#imports
import bisect
import json
import math
from queue import Empty, Queue
import random
from pathlib import Path
from threading import Event, Lock, Thread
import time
import pygame
import character
import inventory_ui
import machine_placement
import resource_nodes
import power_generation
import save_handler
from inventory import Inventory

PIXEL_SIZE = 32
WORLD_RADIUS = 1000
WORLD_SIZE = (WORLD_RADIUS * 2 + 1) ** 2  # Number of tiles, not side length
LOGIC_TPS = 500
RENDER_FPS = 60
Acceleration = 2.5 / LOGIC_TPS  # tiles per logic frame

BASE_PATH = Path(__file__).resolve().parent
TILE_FILE = BASE_PATH / "tile_type_assignment.json"
BIOME_FILE = BASE_PATH / "biome_generation.json"

### load tile and biome definitions
def load_tile_types():
    """Read tile definitions from JSON (numeric keys remain strings)."""
    with TILE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)["tiles"]


def load_biomes():
    """Read the primary biomes and future feature definitions."""
    with BIOME_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


tile_types = load_tile_types()
biome_config = load_biomes()
TILE_COLORS = {tile_id: tuple(info["color"]) for tile_id, info in tile_types.items()}

### validation helpers
def validate_biomes(config, tiles):
    """Catch mismatched IDs and empty weights before world creation."""
    biomes = config.get("biomes", {})
    if not biomes:
        raise ValueError("biome_generation.json defines no biomes")
    for biome_id, info in biomes.items():
        if float(info.get("generation_weight", 0)) < 0:
            raise ValueError(f"Negative generation_weight in {biome_id}")
        weights = info.get("tile_weights", {})
        if not weights or sum(weights.values()) <= 0:
            raise ValueError(f"No positive tile weights in {biome_id}")
        for tile_id, weight in weights.items():
            if tile_id not in tiles:
                raise ValueError(f"Missing tile {tile_id} used by {biome_id}")
            if weight < 0:
                raise ValueError(f"Negative tile weight {tile_id} in {biome_id}")

### weighted random selection
def weighted_choice(rng, values, weights):
    """Pick one item using nonnegative relative weights."""
    return rng.choices(values, weights=weights, k=1)[0]

### biome map generation helpers
def make_biome_centers(rng, radius, biomes):
    """Place a handful of region origins, including a safe spawn and water.

    Using regions instead of rolling a biome for each tile keeps forests,
    deserts, lakes, and other environments geographically clustered.
    """
    names = list(biomes)
    weights = [biomes[name]["generation_weight"] for name in names]
    centers = [(0, 0, "plains" if "plains" in biomes else names[0])]

    # A lake and an ocean are useful landmarks on this small starter world.
    if "lake" in biomes:
        centers.append((rng.randint(-radius, radius),
                        rng.randint(-radius, radius), "lake"))
    if "ocean" in biomes:
        side = rng.choice((0, 1, 2, 3))
        edge = rng.randint(-radius, radius)
        x, y = ((-radius, edge), (radius, edge),
                (edge, -radius), (edge, radius))[side]
        centers.append((x, y, "ocean"))

    # Scale region count modestly for larger worlds; do not build one per tile.
    region_count = max(12, min(80, round((2 * radius + 1) ** 2 / 95)))
    for _ in range(max(0, region_count - len(centers))):
        biome = weighted_choice(rng, names, weights)
        x = rng.randint(-radius, radius)
        y = rng.randint(-radius, radius)
        if biome == "ocean":
            if rng.choice((True, False)):
                x = rng.choice((-radius, radius))
            else:
                y = rng.choice((-radius, radius))
        centers.append((x, y, biome))
    return centers

### biome map generation
def generate_biome_map(seed, radius=WORLD_RADIUS, config=None):
    """Return biome IDs keyed by (x, y) with softly irregular region edges."""
    config = biome_config if config is None else config
    biomes = config["biomes"]
    rng = random.Random(f"{seed}_biome_regions")
    centers = make_biome_centers(rng, radius, biomes)

    # Warp coordinates smoothly, rather than producing a grid of rigid circles.
    phases = [rng.uniform(0, 2 * math.pi) for _ in range(4)]
    result = {}
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            warped_x = x + 2.8 * math.sin(y * 0.23 + phases[0]) + 1.5 * math.sin(x * 0.17 + phases[1])
            warped_y = y + 2.8 * math.sin(x * 0.23 + phases[2]) + 1.5 * math.sin(y * 0.17 + phases[3])
            closest = min(centers,
                          key=lambda center: (warped_x - center[0]) ** 2
                          + (warped_y - center[1]) ** 2)
            # Keep the spawn clear of lakes, lava, and other hazards.
            result[(x, y)] = ("plains" if "plains" in biomes
                               and abs(x) <= 1 and abs(y) <= 1
                               else closest[2])
    return result

### terrain generation helpers
def prepare_tile_tables(config):
    """Prepare cumulative weights once per biome, not once per map tile."""
    tables = {}
    for name, info in config["biomes"].items():
        ids = []
        cumulative = []
        total = 0
        for tile_id, weight in info["tile_weights"].items():
            if weight > 0:
                total += weight
                ids.append(tile_id)
                cumulative.append(total)
        tables[name] = (ids, cumulative, total)
    return tables

### terrain generation
def generate_terrain_tiles(seed, biomes, config=None):
    """Use biome-specific tile weights with an independent deterministic RNG."""
    config = biome_config if config is None else config
    rng = random.Random(f"{seed}_biome_tiles")
    tables = prepare_tile_tables(config)
    world = {}
    for position, biome in biomes.items():
        ids, cumulative, total = tables[biome]
        roll = rng.random() * total
        world[position] = ids[bisect.bisect_right(cumulative, roll)]
    return world

### world generation entry point
def generate_world(world_seed, radius=WORLD_RADIUS):
    """Create a seeded world; return (tile_map, actual_seed) for save_handler.

    Existing callers still receive the original two-value return signature.
    The biome map is computed during generation but is not saved separately;
    future features needing persistent biome metadata can add a sidecar file.
    """
    if world_seed is None or str(world_seed) == "":
        world_seed = str(random.SystemRandom().randint(1_000_000_000, 9_999_999_999))
    world_seed = str(world_seed)
    validate_biomes(biome_config, tile_types)
    biome_map = generate_biome_map(world_seed, radius)
    world = generate_terrain_tiles(world_seed, biome_map)
    return world, world_seed

### temporary inventory for new characters
def create_player_inventory():
    """Provide temporary starter items until character inventory is loaded."""
    inventory = Inventory()
    for item, amount in (
        ("copper_wire", 10), ("resistor", 5), ("circuit_board", 3),
        ("miner", 3), ("assembler", 1), ("conveyor", 30),
        ("power_pole", 5), ("wind_turbine", 5), ("power_cable", 20)
    ):
        inventory.add_item(item, amount)
    return inventory

### save/load helpers
def save_game(save_path, world, nodes, inventory, machines, world_seed,
              power_wires=None,
              progress_callback=None):
    """Persist a snapshot through the save handler's complete-save API."""
    character_data = {
        "Pos": [character.grid_x, character.grid_y],
        "inventory": inventory.to_dict(),
        "last_saved": time.time(),
    }
    save_handler.save_data(
        save_path,
        world,
        nodes,
        world_seed,
        [character_data],
        machines,
        radius=WORLD_RADIUS,
        progress_callback=progress_callback,
    )
    if power_wires is not None:
        wires_path = Path(save_path) / "wires.json"
        wires_path.parent.mkdir(parents=True, exist_ok=True)
        with wires_path.open("w", encoding="utf-8") as file:
            json.dump(power_generation.wires_to_save(power_wires), file)


def remove_placed_machine(position, placed_machines, player_inventory):
    """Remove a machine and refund the item used to place it."""
    placed_data = placed_machines.get(position)
    if placed_data is None:
        return False, "No placed machine on this tile."

    machine_id = placed_data.get("machine_id")
    item_id = (
        "conveyor" if machine_placement.get_belt_type(machine_id) is not None
        else machine_id
    )
    if not player_inventory.add_item(item_id, 1):
        return False, f"Cannot return unknown item '{item_id}' to inventory."

    del placed_machines[position]
    return True, f"Removed {item_id} at {position}."

### I/O thread with progress display
def run_io_task(screen, title, operation):
    """Run save I/O in a worker while keeping status drawing on the Pygame thread."""
    updates = Queue()
    result_queue = Queue()
    close_requested = False

    def report(message, progress):
        updates.put((message, progress))

    def worker():
        try:
            result_queue.put((True, operation(report)))
        except Exception as error:
            result_queue.put((False, error))

    thread = Thread(target=worker, name="save-io")
    started_at = time.perf_counter()
    thread.start()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 26)
    small_font = pygame.font.SysFont("arial", 18)
    message = "Preparing..."
    progress = 0.0
    screen_width, screen_height = screen.get_size()
    panel = pygame.Rect(0, 0, max(1, min(520, screen_width - 40)), 170)
    panel.center = (screen_width // 2, screen_height // 2)

    while thread.is_alive() or time.perf_counter() - started_at < 0.2:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close_requested = True

        while True:
            try:
                message, progress = updates.get_nowait()
            except Empty:
                break

        screen.fill((18, 22, 28))
        pygame.draw.rect(screen, (45, 52, 62), panel, border_radius=8)
        title_surface = font.render(title, True, (245, 245, 245))
        message_surface = small_font.render(message, True, (200, 210, 220))
        screen.blit(title_surface, title_surface.get_rect(
            center=(panel.centerx, panel.y + 42)
        ))
        screen.blit(message_surface, message_surface.get_rect(
            center=(panel.centerx, panel.y + 86)
        ))
        bar_rect = pygame.Rect(panel.x + 30, panel.bottom - 42, panel.width - 60, 16)
        pygame.draw.rect(screen, (25, 30, 36), bar_rect, border_radius=8)
        fill_width = int(bar_rect.width * max(0.0, min(progress, 1.0)))
        if fill_width:
            pygame.draw.rect(
                screen,
                (70, 165, 235),
                (bar_rect.x, bar_rect.y, fill_width, bar_rect.height),
                border_radius=8,
            )
        pygame.display.flip()
        clock.tick(RENDER_FPS)

    thread.join()
    succeeded, result = result_queue.get()
    if not succeeded:
        raise result
    return result, close_requested

### transient rendering functions, not part of the save system or world generation
def draw_terrain(screen, world, camera_x, camera_y, width, height):
    """Only draw visible tiles, caching each tile's RGB lookup."""
    half_x = (width // PIXEL_SIZE + 2) // 2
    half_y = (height // PIXEL_SIZE + 2) // 2
    min_x = max(-WORLD_RADIUS, math.floor(camera_x - half_x))
    max_x = min(WORLD_RADIUS, math.ceil(camera_x + half_x))
    min_y = max(-WORLD_RADIUS, math.floor(camera_y - half_y))
    max_y = min(WORLD_RADIUS, math.ceil(camera_y + half_y))
    for x in range(min_x, max_x + 1):
        sx = round(width // 2 + (x - camera_x) * PIXEL_SIZE)
        for y in range(min_y, max_y + 1):
            sy = round(height // 2 + (y - camera_y) * PIXEL_SIZE)
            pygame.draw.rect(screen, TILE_COLORS[world[(x, y)]],
                             (sx, sy, PIXEL_SIZE, PIXEL_SIZE))

### external exceleration handler
def handle_acceleration():
    sprinting=pygame.key.get_mods() & pygame.KMOD_SHIFT
    character.accelerate(0, 0, WORLD_RADIUS,.1, sprinting)

def start(screen, world_seed, world_name, load):

    #place character at center of world
    character.spawn_at_center()

    player_inventory = create_player_inventory()

    #temporary machine placement data
    #later this can be loaded/saved through the save system
    placed_machines = {}

    #tracks the machine currently being placed and its orientation
    placement_state = machine_placement.MachinePlacementState()
    belt_dragging = False
    belt_drag_tiles = []
    belt_drag_anchor = None  # existing belt end when extending a line
    wire_tool = power_generation.PowerWireTool()
    power_result = None

    #tracks if inventory is open
    inventory_open = False

    #Track if the placement UI is open
    placement_ui = False

    #Track if the writing UI is open
    writing_ui = False

    #Define dimensions of placement
    placement_ui_dimensions = pygame.Rect(300, 130, 1500, 900)
    placement_ui_items_dimensions = pygame.Rect(120, 130, 300, 900)

    #Define dimensions of writing UI
    writing_ui_dimensions = pygame.Rect(120, 130, 1680, 900)
    writing_ui_text_dimensions = pygame.Rect(140, 180, 1640, 800)

    #Define colors for placement, writing UI
    PLACE_COLOR = (237, 255, 217)
    PLACE_ITEMS_COLOR = (145, 145, 144)
    WRITING_UI_COLOR = (69, 63, 63)
    WRITING_UI_TEXT_COLOR = (255, 255, 255)

    #Define font of text that user types
    base_font = pygame.font.Font(None, 32)

    #Holds the users text
    program_text = ""

    #Defines current level if the user has clicked the writing_ui_text_dimensions
    active_text_input = False


    if load:
        operation = lambda report: save_handler.load_data(
            world_name,
            radius=WORLD_RADIUS,
            progress_callback=report,
        )
        load_title = "Loading world"
    else:
        operation = lambda report: save_handler.create_data(
            world_name,
            inventory=player_inventory.to_dict(),
            radius=WORLD_RADIUS,
            progress_callback=report,
            seed=world_seed,
        )
        load_title = "Creating world"

    ### run the I/O operation in a separate thread while showing a progress screen
    io_result, close_requested = run_io_task(screen, load_title, operation)
    if close_requested:
        return

    save_path, world, resource_nodes_data, world_seed, character_data, placed_machines = io_result

    if load:
        try:
            with (Path(save_path) / "wires.json").open("r", encoding="utf-8") as file:
                wire_tool.wires = power_generation.wires_from_save(json.load(file))
        except FileNotFoundError:
            pass

    if isinstance(character_data, list):
        if not character_data:
            raise ValueError(f"No character data found in save {save_path}")
        character_data = character_data[0]
    character.grid_x, character.grid_y = character_data["Pos"]
    if load and "inventory" in character_data:
        player_inventory.load_dict(character_data["inventory"])

    #get screen size
    screen_width, screen_height = screen.get_size()

    #temporary placement instruction font
    placement_font = pygame.font.SysFont("arial", 18)

    #"camera"
    #camera follows character
    camera_x = character.grid_x
    camera_y = character.grid_y

    #main world loop
    running = True
    save_requested = False

    event_queue = Queue()
    logic_errors = Queue()
    stop_event = Event()
    state_lock = Lock()
    logic_interval = 1.0 / LOGIC_TPS

    ### on logic tick, process all events in the queue and update the game state
    def process_event(event):
        nonlocal running, save_requested, inventory_open, belt_dragging
        nonlocal belt_drag_tiles, belt_drag_anchor

        nonlocal placement_ui, writing_ui, active_text_input

        def quit_game():
            nonlocal running, save_requested
            save_requested = True
            running = False

        def rotate_placement():
            placement_state.rotate()
            print(
                "Machine orientation:",
                machine_placement.get_orientation_name(placement_state.orientation)
            )

        def toggle_inventory():
            nonlocal inventory_open
            if wire_tool.active:
                wire_tool.cancel()
            inventory_open = not inventory_open

        def toggle_placement_ui():
            nonlocal placement_ui
            placement_ui = not placement_ui

        def toggle_writing_ui():
            nonlocal writing_ui
            writing_ui = not writing_ui
        
        def cancel_placement():
            nonlocal belt_dragging, belt_drag_tiles, belt_drag_anchor
            placement_state.cancel()
            belt_dragging = False
            belt_drag_tiles = []
            belt_drag_anchor = None
            print("Machine placement cancelled.")

        def escape_action():
            nonlocal running, save_requested, inventory_open
            if wire_tool.active:
                if wire_tool.selected_pos is not None:
                    wire_tool.selected_pos = None
                    print("Wire start cancelled.")
                else:
                    wire_tool.cancel()
                    print("Wire placement cancelled.")
            elif placement_state.active:
                cancel_placement()
            elif inventory_open:
                inventory_open = False
            else:
                save_requested = True
                running = False

        def move_player(key):
            x = 0
            y = 0
            if key in (pygame.K_w, pygame.K_UP):
                y+=-1
            if key in (pygame.K_s, pygame.K_DOWN):
                y+=1
            if key in (pygame.K_a, pygame.K_LEFT):
                x+=-1
            if key in (pygame.K_d, pygame.K_RIGHT):
                x+=1

            ## normalize diagonal movement
            length = math.sqrt(x**2 + y**2)

            x /= length 
            y /= length

            x*= Acceleration
            y*= Acceleration

            ### apply sprint multiplier if shift is held
            sprinting = pygame.key.get_mods() & pygame.KMOD_SHIFT
            character.accelerate(x, y, WORLD_RADIUS, sprinting=sprinting)

        def handle_key(keys_pressed):
            if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
                move_player(pygame.K_w)
            if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
                move_player(pygame.K_s)
            if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
                move_player(pygame.K_a)
            if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
                move_player(pygame.K_d)

        
        def handle_keydown(key):
            if key == pygame.K_r and placement_state.active:
                rotate_placement()
            elif key == pygame.K_i and not placement_state.active:
                toggle_inventory()
            elif key == pygame.K_1:
                toggle_placement_ui()
            elif key == pygame.K_2:
                toggle_writing_ui()
            elif key == pygame.K_ESCAPE:
                escape_action()

        def select_inventory_machine(position):
            nonlocal inventory_open
            selected_machine = inventory_ui.handle_click(
                (screen_width, screen_height),
                position,
                player_inventory
            )
            if selected_machine is None:
                return
            if selected_machine == "power_cable":
                if wire_tool.start(player_inventory):
                    inventory_open = False
                    print(
                        "Wire mode: left-click two machines to connect; "
                        "right-click/ESC cancels."
                    )
                else:
                    print("No power_cable in inventory.")
                return
            if not player_inventory.has_item(selected_machine, 1):
                print(f"No {selected_machine} available in inventory.")
            elif placement_state.start(selected_machine):
                inventory_open = False
                if selected_machine == "conveyor":
                    print(
                        "Conveyor mode: left-drag to build, "
                        "R rotates a single piece, ESC/right click cancels."
                    )
                else:
                    print(
                        f"{selected_machine} placement mode started. "
                        "R rotates, left click places, ESC/right click cancels."
                    )
            else:
                print(
                    f"Machine '{selected_machine}' does not "
                    "have a placement definition yet."
                )

        def begin_belt_drag(position):
            nonlocal belt_dragging, belt_drag_tiles, belt_drag_anchor
            if not player_inventory.has_item("conveyor", 1):
                placement_state.cancel()
                return

            gx, gy = machine_placement.screen_to_world(
                *position, camera_x, camera_y,
                screen_width, screen_height, PIXEL_SIZE
            )
            belt_drag_tiles = []
            belt_drag_anchor = None
            if (gx, gy) in placed_machines:
                if machine_placement.is_open_belt_endpoint((gx, gy), placed_machines):
                    belt_drag_anchor = (gx, gy)
                    belt_dragging = True
                else:
                    belt_dragging = False
            else:
                belt_dragging = machine_placement.extend_belt_drag(
                    belt_drag_tiles, (gx, gy), placed_machines, WORLD_RADIUS
                )

        def place_machine(position):
            gx, gy = machine_placement.screen_to_world(
                *position, camera_x, camera_y,
                screen_width, screen_height, PIXEL_SIZE
            )
            selected_machine = placement_state.selected_machine_id

            if not player_inventory.has_item(selected_machine, 1):
                print(f"No {selected_machine} available in inventory.")
                placement_state.cancel()
                return

            success, message, placed_data = machine_placement.handle_build_click(
                selected_machine,
                gx,
                gy,
                placement_state.orientation,
                resource_nodes_data,
                placed_machines,
                WORLD_RADIUS
            )
            print(message)
            if success:
                placed_machines[(gx, gy)] = placed_data
                player_inventory.remove_item(selected_machine, 1)
                if not player_inventory.has_item(selected_machine, 1):
                    placement_state.cancel()

        def track_belt_drag(position):
            gx, gy = machine_placement.screen_to_world(
                *position, camera_x, camera_y,
                screen_width, screen_height, PIXEL_SIZE
            )
            machine_placement.extend_belt_drag(
                belt_drag_tiles, (gx, gy), placed_machines, WORLD_RADIUS,
                start_anchor=belt_drag_anchor
            )

        def commit_belt_drag(position):
            nonlocal belt_dragging, belt_drag_tiles, belt_drag_anchor
            track_belt_drag(position)

            available = player_inventory.get_quantity("conveyor")
            usable_tiles = belt_drag_tiles[:available]
            placements = machine_placement.build_belt_path(
                usable_tiles, placed_machines, WORLD_RADIUS,
                placement_state.orientation, start_anchor=belt_drag_anchor
            )

            if placements and player_inventory.remove_item("conveyor", len(placements)):
                if belt_drag_anchor is not None:
                    anchor_update = machine_placement.get_extended_endpoint_placement(
                        placed_machines, belt_drag_anchor,
                        (placements[0][0], placements[0][1])
                    )
                    if anchor_update is not None:
                        ax, ay, anchor_type, anchor_orientation = anchor_update
                        placed_machines[(ax, ay)] = {
                            **placed_machines[(ax, ay)],
                            **machine_placement.create_belt_placement(
                                ax, ay, anchor_type, anchor_orientation
                            )
                        }
                for gx, gy, belt_type, orientation in placements:
                    placed_machines[(gx, gy)] = machine_placement.create_belt_placement(
                        gx, gy, belt_type, orientation
                    )
                print(f"Placed {len(placements)} conveyor belt(s).")
                if not player_inventory.has_item("conveyor", 1):
                    placement_state.cancel()

            belt_dragging = False
            belt_drag_tiles = []
            belt_drag_anchor = None

        def handle_mouse_button_down(button, position):
            if inventory_open and not placement_state.active:
                if button == 1:
                    select_inventory_machine(position)
            elif wire_tool.active:
                if button == 3:
                    if wire_tool.selected_pos is not None:
                        wire_tool.selected_pos = None
                        print("Wire start cancelled.")
                    else:
                        wire_tool.cancel()
                        print("Wire placement cancelled.")
                elif button == 1:
                    gx, gy = machine_placement.screen_to_world(
                        *position, camera_x, camera_y,
                        screen_width, screen_height, PIXEL_SIZE
                    )
                    action, data = wire_tool.handle_click(
                        (gx, gy), placed_machines, player_inventory, button=button
                    )
                    print(action, data)
                    if action == "connected_out":
                        print("Out of power_cable - wire mode exited.")
            elif placement_state.active:
                if button == 3:
                    cancel_placement()
                elif button == 1 and placement_state.selected_machine_id == "conveyor":
                    begin_belt_drag(position)
                elif button == 1:
                    place_machine(position)
            elif button == 3:
                gx, gy = machine_placement.screen_to_world(
                    *position, camera_x, camera_y,
                    screen_width, screen_height, PIXEL_SIZE
                )
                if (gx, gy) in placed_machines:
                    success, message = remove_placed_machine(
                        (gx, gy), placed_machines, player_inventory
                    )
                    print(message)
                    if success:
                        removed = power_generation.remove_all_wires_at(
                            (gx, gy), wire_tool.wires
                        )
                        if removed:
                            player_inventory.add_item("power_cable", removed)
                            print(f"Returned {removed} power_cable(s).")
                else:
                    closest_wire = None
                    closest_dist = power_generation.HOVER_DIST + 1
                    mouse_x, mouse_y = position
                    for start, end in list(wire_tool.wires):
                        ax, ay = power_generation.world_to_screen(
                            start[0], start[1], camera_x, camera_y,
                            screen_width, screen_height, PIXEL_SIZE
                        )
                        bx, by = power_generation.world_to_screen(
                            end[0], end[1], camera_x, camera_y,
                            screen_width, screen_height, PIXEL_SIZE
                        )
                        dist = power_generation._point_to_segment_dist(
                            mouse_x, mouse_y, ax, ay, bx, by
                        )
                        if dist < closest_dist:
                            closest_dist = dist
                            closest_wire = (start, end)
                    if closest_wire is not None:
                        power_generation.remove_wire(
                            closest_wire[0], closest_wire[1], wire_tool.wires
                        )
                        player_inventory.add_item("power_cable", 1)
                        print("Removed wire - returned 1 power_cable.")

        def handle_writing(position):
            nonlocal active_text_input
            if writing_ui:
                if writing_ui_text_dimensions.collidepoint(position):
                    active_text_input = True
                else:
                    active_text_input = False
                

            if (active_text_input == True) and (writing_ui_dimensions.collidepoint(position) == False): 
                active_text_input = False

        def handle_writes(key):
            nonlocal program_text, active_text_input
            if active_text_input:
                if event.key == pygame.K_BACKSPACE:
                    program_text = program_text[:-1]
                elif event.key == pygame.K_RETURN:
                    program_text += "\n"
                elif hasattr(key, "unicode") and key.unicode:
                    program_text += event.unicode
                
        keys_pressed = pygame.key.get_pressed()
        if not inventory_open and not placement_state.active:
            handle_key(keys_pressed)

        if event is None:
            return
        if event.type == pygame.QUIT:
            quit_game()
        elif event.type == pygame.KEYDOWN:
            handle_keydown(event.key)
            handle_writes(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            handle_mouse_button_down(event.button, event.pos)
            handle_writing(event.pos)
        elif event.type == pygame.MOUSEMOTION and belt_dragging:
            track_belt_drag(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and belt_dragging:
            commit_belt_drag(event.pos)

    ### logice thread worker function, runs at LOGIC_TPS and updates the game state
    def logic_worker():
        nonlocal camera_x, camera_y, power_result
        next_tick = time.perf_counter()
        try:
            while not stop_event.is_set() and running:
                next_tick += logic_interval
                try:
                    event = event_queue.get_nowait()
                except Empty:
                    event = None

                process_event(event)

                ## handle acceleration even if no keydown event is received
                handle_acceleration()
                power_result = power_generation.calculate_power_network(
                    placed_machines, wire_tool.wires
                )
                camera_x = character.grid_x
                camera_y = character.grid_y

                delay = next_tick - time.perf_counter()
                if delay > 0:
                    stop_event.wait(delay)
                else:
                    next_tick = time.perf_counter()
        except Exception as error:
            logic_errors.put(error)
            stop_event.set()

    ### main loop
    logic_thread = Thread(target=logic_worker, name="world-logic")
    logic_thread.start()
    render_clock = pygame.time.Clock()

    ### main render loop, runs at RENDER_FPS and draws the game state
    try:
        while running:
            for event in pygame.event.get():
                event_queue.put(event)

            if not logic_errors.empty():
                raise logic_errors.get()
            if not running:
                break

            with state_lock:
                render_world = world
                render_camera_x = camera_x
                render_camera_y = camera_y
                render_resource_nodes_data = resource_nodes_data.copy()
                render_placed_machines = placed_machines.copy()
                render_belt_dragging = belt_dragging
                render_belt_drag_tiles = list(belt_drag_tiles)
                render_belt_drag_anchor = belt_drag_anchor
                render_power_wires = wire_tool.wires.copy()
                render_power_result = power_result
                render_inventory = Inventory()
                render_inventory.load_dict(player_inventory.to_dict())
                render_inventory_open = inventory_open
                render_placement_active = placement_state.active
                render_selected_machine_id = placement_state.selected_machine_id
                render_orientation = placement_state.orientation

            #draw screen
            #background
            screen.fill((0, 0, 0))

            draw_terrain(screen, render_world, render_camera_x, render_camera_y,
                         screen_width, screen_height)

            #draw resource nodes
            resource_nodes.draw_resource_nodes(
                screen,
                render_resource_nodes_data,
                render_camera_x,
                render_camera_y,
                screen_width,
                screen_height,
                PIXEL_SIZE
            )

            #draw machines that have already been placed
            machine_placement.draw_placed_machines(
                screen,
                render_placed_machines,
                render_camera_x,
                render_camera_y,
                screen_width,
                screen_height,
                PIXEL_SIZE
            )

            power_generation.draw_power_wires(
                screen,
                render_power_wires,
                render_placed_machines,
                render_power_result,
                render_camera_x,
                render_camera_y,
                screen_width,
                screen_height,
                PIXEL_SIZE,
                mouse_pos=pygame.mouse.get_pos()
            )
            power_generation.draw_wire_selection(
                screen,
                wire_tool.selected_pos,
                render_camera_x,
                render_camera_y,
                screen_width,
                screen_height,
                PIXEL_SIZE
            )

            if wire_tool.active:
                wire_hint = placement_font.render(
                    f"Placing Wire | Cables: x{render_inventory.get_quantity('power_cable')} "
                    "| Left-click = connect | Right-click/ESC = exit",
                    True,
                    (255, 255, 255)
                )
                screen.blit(wire_hint, (15, 15))

            #draw character on top of world
            character_screen_x = screen_width // 2
            character_screen_y = screen_height // 2

            with state_lock:
                character.draw(
                    screen,
                    character_screen_x,
                    character_screen_y,
                    PIXEL_SIZE
                )

            #draw placement preview under the mouse while placement mode is active
            if render_placement_active and render_selected_machine_id == "conveyor":
                if render_belt_dragging and render_belt_drag_tiles:
                    usable_tiles = render_belt_drag_tiles[:render_inventory.get_quantity("conveyor")]
                    belt_preview = machine_placement.build_belt_path(
                        usable_tiles, render_placed_machines, WORLD_RADIUS,
                        render_orientation, start_anchor=render_belt_drag_anchor
                    )
                    if render_belt_drag_anchor is not None and belt_preview:
                        # Preview the updated end piece as well as the new belts.
                        endpoint = machine_placement.get_extended_endpoint_placement(
                            render_placed_machines, render_belt_drag_anchor,
                            (belt_preview[0][0], belt_preview[0][1])
                        )
                        if endpoint is not None:
                            machine_placement.draw_belt_path_preview(
                                screen, [endpoint], render_camera_x, render_camera_y,
                                screen_width, screen_height, PIXEL_SIZE
                            )
                    machine_placement.draw_belt_path_preview(
                        screen, belt_preview, render_camera_x, render_camera_y,
                        screen_width, screen_height, PIXEL_SIZE
                    )
                else:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    gx, gy = machine_placement.screen_to_world(
                        mouse_x, mouse_y, render_camera_x, render_camera_y,
                        screen_width, screen_height, PIXEL_SIZE
                    )
                    valid, reason = machine_placement.can_place_machine(
                        "conveyor", gx, gy, render_resource_nodes_data,
                        render_placed_machines, WORLD_RADIUS
                    )
                    if machine_placement.is_open_belt_endpoint((gx, gy), render_placed_machines):
                        # Existing endpoints are valid drag starts, not new placements.
                        sx, sy = machine_placement.world_to_screen(
                            gx, gy, render_camera_x, render_camera_y,
                            screen_width, screen_height, PIXEL_SIZE
                        )
                        pygame.draw.rect(
                            screen, (110, 255, 110), (sx, sy, PIXEL_SIZE, PIXEL_SIZE), 2
                        )
                        screen.blit(placement_font.render(
                            "Drag from this belt end to extend it.",
                            True, (110, 255, 110)
                        ), (15, 40))
                    else:
                        machine_placement.draw_placement_preview(
                            screen, "conveyor", gx, gy, render_orientation,
                            valid, render_camera_x, render_camera_y,
                            screen_width, screen_height, PIXEL_SIZE
                        )
                        if not valid:
                            screen.blit(placement_font.render(
                                reason, True, (255, 120, 120)
                            ), (15, 40))

                belt_message = (
                    f"Conveyor | x{render_inventory.get_quantity('conveyor')} | "
                    "Drag empty tiles or from an existing belt end | "
                    "R rotates single piece | ESC/right click cancels"
                )
                screen.blit(placement_font.render(belt_message, True, (255, 255, 255)), (15, 15))

            elif render_placement_active:
                    mouse_x, mouse_y = pygame.mouse.get_pos()

                    preview_grid_x, preview_grid_y = (
                        machine_placement.screen_to_world(
                            mouse_x,
                            mouse_y,
                            render_camera_x,
                            render_camera_y,
                            screen_width,
                            screen_height,
                            PIXEL_SIZE
                        )
                    )

                    can_place, placement_reason = (
                        machine_placement.can_place_machine(
                            render_selected_machine_id,
                            preview_grid_x,
                            preview_grid_y,
                            render_resource_nodes_data,
                            render_placed_machines,
                            WORLD_RADIUS
                        )
                    )

                    machine_placement.draw_placement_preview(
                        screen,
                        render_selected_machine_id,
                        preview_grid_x,
                        preview_grid_y,
                        render_orientation,
                        can_place,
                        render_camera_x,
                        render_camera_y,
                        screen_width,
                        screen_height,
                        PIXEL_SIZE
                    )

                    #temporary placement instructions
                    placement_text = (
                        f"Placing: {render_selected_machine_id} | "
                        f"Facing: {machine_placement.get_orientation_name(render_orientation)} | "
                        f"R = rotate | Left click = place | ESC/right click = cancel"
                    )

                    placement_surface = placement_font.render(
                        placement_text,
                        True,
                        (255, 255, 255)
                    )

                    screen.blit(
                        placement_surface,
                        (15, 15)
                    )

                    #show why the current tile is invalid
                    if not can_place:
                        reason_surface = placement_font.render(
                            placement_reason,
                            True,
                            (255, 120, 120)
                        )

                        screen.blit(
                            reason_surface,
                            (15, 40)
                        )

            #draw inventory if open
            if render_inventory_open:
                inventory_ui.draw(screen, render_inventory)

            if placement_ui:
                pygame.draw.rect(screen, PLACE_COLOR, placement_ui_dimensions, border_radius = 10)
                pygame.draw.rect(screen, PLACE_ITEMS_COLOR, placement_ui_items_dimensions, border_top_left_radius = 10, border_bottom_left_radius = 10)


            if writing_ui:
                pygame.draw.rect(screen, WRITING_UI_COLOR, writing_ui_dimensions, border_radius = 10)
                pygame.draw.rect(screen, WRITING_UI_COLOR, writing_ui_text_dimensions, border_radius = 10)
            
            if active_text_input and writing_ui:
                lines = program_text.split("\n")
                lines_height = base_font.get_linesize()

                start_x = writing_ui_dimensions.x + 15
                start_y = writing_ui_dimensions.y + 15

                for i, line in enumerate(lines):
                    text_surface = base_font.render(line, True, WRITING_UI_TEXT_COLOR)
                    screen.blit(text_surface, (start_x, start_y + (i * lines_height)))                
            
            #display world
            pygame.display.flip()

            render_clock.tick(RENDER_FPS)
    #################
    ### thread cleanup
    finally:
        stop_event.set()
        logic_thread.join()

    if not logic_errors.empty():
        raise logic_errors.get()

    ### save game if requested
    if save_requested:
        run_io_task(
            screen,
            "Saving game",
            lambda report: save_game(
                save_path,
                world,
                resource_nodes_data,
                player_inventory,
                placed_machines,
                world_seed,
                power_wires=wire_tool.wires,
                progress_callback=report,
            ),
        )

    #return to previous screen
    return
