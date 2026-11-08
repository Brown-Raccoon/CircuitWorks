#imports
import bisect
import json
import math
import random
from pathlib import Path
import pygame
import character
import inventory_ui
import machine_placement
import resource_nodes
import save_handler
from inventory import Inventory

PIXEL_SIZE = 32
WORLD_RADIUS = 20
WORLD_SIZE = (WORLD_RADIUS * 2 + 1) ** 2  # Number of tiles, not side length

BASE_PATH = Path(__file__).resolve().parent
TILE_FILE = BASE_PATH / "tile_type_assignment.json"
BIOME_FILE = BASE_PATH / "biome_generation.json"


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


def weighted_choice(rng, values, weights):
    """Pick one item using nonnegative relative weights."""
    return rng.choices(values, weights=weights, k=1)[0]


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


def create_player_inventory():
    """Provide temporary starter items until character inventory is loaded."""
    inventory = Inventory()
    for item, amount in (
        ("copper_wire", 10), ("resistor", 5), ("circuit_board", 3),
        ("miner", 3), ("assembler", 1), ("conveyor", 30),
        ("power_pole", 5), ("wind_turbine", 5)
    ):
        inventory.add_item(item, amount)
    return inventory


def save_game(save_path, world, nodes, inventory, machines):
    """Persist the whole game consistently on ESC and window close."""
    character_data = {
        "Pos": [character.grid_x, character.grid_y],
        "inventory": inventory.to_dict(),
    }
    save_handler.save_world(save_path, world, nodes, WORLD_RADIUS, WORLD_SIZE)
    save_handler.save_nodes(save_path, nodes)
    # save_handler.load_character currently reads a list of records.
    save_handler.save_character(save_path, [character_data])
    save_handler.save_entitys(save_path, machines)


def remove_placed_machine(position, placed_machines, player_inventory):
    """Remove one machine and refund its inventory item, if the item is valid.

    Saved conveyor segments have shape-specific IDs, but all refund a single
    'conveyor' inventory item. The world is only changed after the refund works.
    """
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


def draw_terrain(screen, world, camera_x, camera_y, width, height):
    """Only draw visible tiles, caching each tile's RGB lookup."""
    half_x = (width // PIXEL_SIZE + 2) // 2
    half_y = (height // PIXEL_SIZE + 2) // 2
    min_x = max(-WORLD_RADIUS, camera_x - half_x)
    max_x = min(WORLD_RADIUS, camera_x + half_x)
    min_y = max(-WORLD_RADIUS, camera_y - half_y)
    max_y = min(WORLD_RADIUS, camera_y + half_y)
    for x in range(min_x, max_x + 1):
        sx = width // 2 + (x - camera_x) * PIXEL_SIZE
        for y in range(min_y, max_y + 1):
            sy = height // 2 + (y - camera_y) * PIXEL_SIZE
            pygame.draw.rect(screen, TILE_COLORS[world[(x, y)]],
                             (sx, sy, PIXEL_SIZE, PIXEL_SIZE))


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

    #tracks if inventory is open
    inventory_open = False
    if load:
        #load world from save
        save_path = world_name

        #load world and resource nodes from save
        world = save_handler.get_world(save_path, WORLD_RADIUS)
        resource_nodes_data = save_handler.load_nodes(save_path)

        #load character data from save
        character_data = save_handler.load_character(save_path)

        try:
            placed_machines = save_handler.load_entity(save_path)
        except FileNotFoundError:
            placed_machines = {}

        # Existing save_handler.load_character returns a list of records.
        if isinstance(character_data, list):
            character_data = character_data[0]
        character.grid_x, character.grid_y = character_data["Pos"]
        # Restore saved quantities, including items refunded by machine removal.
        if "inventory" in character_data:
            player_inventory.load_dict(character_data["inventory"])

    else:
        #create save file
        save_path = save_handler.create_save_file(world_name)

        #create character save file
        save_handler.create_character_file(save_path, 
            character.grid_x, 
            character.grid_y, 
            player_inventory)
        
        #send to generate world
        world, resource_nodes_data, world_seed = save_handler.create_world_file(
            save_path, 
            world_seed, 
            WORLD_SIZE, 
            WORLD_RADIUS)
    
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

    while running:
        #detect events/inputs
        for event in pygame.event.get():
            #allow window to close
            if event.type == pygame.QUIT:
                
                save_game(save_path, world, resource_nodes_data,
                          player_inventory, placed_machines)
                running = False

            #keybord input
            elif event.type == pygame.KEYDOWN:

                #rotate the selected machine while placement mode is active
                if event.key == pygame.K_r and placement_state.active:
                    placement_state.rotate()
                    print(
                        "Machine orientation:",
                        machine_placement.get_orientation_name(
                            placement_state.orientation
                        )
                    )

                #open/close inventory
                elif event.key == pygame.K_i and not placement_state.active:
                    inventory_open = not inventory_open

                #ESC cancels placement first, then closes inventory, then leaves world
                elif event.key == pygame.K_ESCAPE:
                    if placement_state.active:
                        placement_state.cancel()
                        belt_dragging = False
                        belt_drag_tiles = []
                        belt_drag_anchor = None
                        print("Machine placement cancelled.")
                    elif inventory_open:
                        inventory_open = False
                    else:
                        save_game(save_path, world, resource_nodes_data,
                                  player_inventory, placed_machines)
                        running = False

                #movement only works while inventory is closed
                elif not inventory_open:

                    #up
                    if event.key in (pygame.K_w, pygame.K_UP):
                        character.move(0, -1, WORLD_RADIUS, placed_machines)

                    #down
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        character.move(0, 1, WORLD_RADIUS, placed_machines)

                    #left
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        character.move(-1, 0, WORLD_RADIUS, placed_machines)

                    #right
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        character.move(1, 0, WORLD_RADIUS, placed_machines)

            #mouse input
            elif event.type == pygame.MOUSEBUTTONDOWN:

                #inventory clicks
                if inventory_open and not placement_state.active:

                    #only left click can press inventory buttons
                    if event.button == 1:
                        selected_machine = inventory_ui.handle_click(
                            screen,
                            event.pos,
                            player_inventory
                        )

                        #a machine Place button was clicked
                        if selected_machine is not None:

                            #make sure the player still owns at least one
                            if not player_inventory.has_item(
                                selected_machine,
                                1
                            ):
                                print(
                                    f"No {selected_machine} available in inventory."
                                )

                            #start placement only if that machine has a
                            #definition in Machines.json
                            elif placement_state.start(
                                selected_machine
                            ):
                                inventory_open = False

                                if selected_machine == "conveyor":
                                    print("Conveyor mode: left-drag to build, "
                                          "R rotates a single piece, "
                                          "ESC/right click cancels.")
                                else:
                                    print(
                                        f"{selected_machine} placement mode started. "
                                        "R rotates, left click places, "
                                        "ESC/right click cancels."
                                    )

                            else:
                                print(
                                    f"Machine '{selected_machine}' does not "
                                    "have a placement definition yet."
                                )

                #world clicks while placing a machine
                elif placement_state.active:

                    #right click cancels placement
                    if event.button == 3:
                        placement_state.cancel()
                        belt_dragging = False
                        belt_drag_tiles = []
                        belt_drag_anchor = None
                        print("Machine placement cancelled.")

                    #left click attempts to place the selected machine
                    elif event.button == 1 and placement_state.selected_machine_id == "conveyor":
                        # Begin a connected belt path. We commit it on mouse release.
                        if not player_inventory.has_item("conveyor", 1):
                            placement_state.cancel()
                        else:
                            gx, gy = machine_placement.screen_to_world(
                                *event.pos, camera_x, camera_y,
                                screen_width, screen_height, PIXEL_SIZE
                            )
                            belt_drag_tiles = []
                            belt_drag_anchor = None
                            if (gx, gy) in placed_machines:
                                # Click an existing open belt end to continue its path.
                                if machine_placement.is_open_belt_endpoint(
                                    (gx, gy), placed_machines
                                ):
                                    belt_drag_anchor = (gx, gy)
                                    belt_dragging = True
                                else:
                                    belt_dragging = False
                            else:
                                belt_dragging = machine_placement.extend_belt_drag(
                                    belt_drag_tiles, (gx, gy), placed_machines, WORLD_RADIUS
                                )

                    elif event.button == 1:
                        mouse_x, mouse_y = event.pos

                        grid_x, grid_y = machine_placement.screen_to_world(
                            mouse_x,
                            mouse_y,
                            camera_x,
                            camera_y,
                            screen_width,
                            screen_height,
                            PIXEL_SIZE
                        )

                        selected_machine = (
                            placement_state.selected_machine_id
                        )

                        #make sure the player still owns the selected machine
                        if not player_inventory.has_item(
                            selected_machine,
                            1
                        ):
                            print(
                                f"No {selected_machine} available in inventory."
                            )
                            placement_state.cancel()

                        else:
                            success, message, placed_data = (
                                machine_placement.handle_build_click(
                                    selected_machine,
                                    grid_x,
                                    grid_y,
                                    placement_state.orientation,
                                    resource_nodes_data,
                                    placed_machines,
                                    WORLD_RADIUS,
                                    world,
                                    tile_types
                                )
                            )

                            print(message)

                            if success:
                                #store the placed machine in the world
                                placed_machines[
                                    (grid_x, grid_y)
                                ] = placed_data

                                #remove exactly one machine from inventory
                                player_inventory.remove_item(
                                    selected_machine,
                                    1
                                )

                                #if no more of this machine remain,
                                #exit placement mode
                                if not player_inventory.has_item(
                                    selected_machine,
                                    1
                                ):
                                    placement_state.cancel()

                #right click in normal gameplay removes a placed building
                elif not inventory_open and event.button == 3:
                    gx, gy = machine_placement.screen_to_world(
                        *event.pos, camera_x, camera_y,
                        screen_width, screen_height, PIXEL_SIZE
                    )
                    if (gx, gy) in placed_machines:
                        success, message = remove_placed_machine(
                            (gx, gy), placed_machines, player_inventory
                        )
                        print(message)

            # Track conveyor path while holding the left mouse button.
            elif event.type == pygame.MOUSEMOTION and belt_dragging:
                gx, gy = machine_placement.screen_to_world(
                    *event.pos, camera_x, camera_y,
                    screen_width, screen_height, PIXEL_SIZE
                )
                machine_placement.extend_belt_drag(
                    belt_drag_tiles, (gx, gy), placed_machines, WORLD_RADIUS,
                    start_anchor=belt_drag_anchor
                )

            # Release commits only valid belt tiles, limited by inventory.
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and belt_dragging:
                gx, gy = machine_placement.screen_to_world(
                    *event.pos, camera_x, camera_y,
                    screen_width, screen_height, PIXEL_SIZE
                )
                machine_placement.extend_belt_drag(
                    belt_drag_tiles, (gx, gy), placed_machines, WORLD_RADIUS,
                    start_anchor=belt_drag_anchor
                )

                available = player_inventory.get_quantity("conveyor")
                usable_tiles = belt_drag_tiles[:available]
                placements = machine_placement.build_belt_path(
                    usable_tiles, placed_machines, WORLD_RADIUS,
                    placement_state.orientation, start_anchor=belt_drag_anchor
                )

                # Reserve the quantity first, so no belt appears for free.
                if placements and player_inventory.remove_item("conveyor", len(placements)):
                    # Update the old end piece only after the placement succeeds.
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

        #camera follows character
        camera_x = character.grid_x
        camera_y = character.grid_y

        #draw screen
        #background
        screen.fill((0, 0, 0))

        draw_terrain(screen, world, camera_x, camera_y,
                     screen_width, screen_height)

        #draw resource nodes
        resource_nodes.draw_resource_nodes(
            screen,
            resource_nodes_data,
            camera_x,
            camera_y,
            screen_width,
            screen_height,
            PIXEL_SIZE
        )

        #draw machines that have already been placed
        machine_placement.draw_placed_machines(
            screen,
            placed_machines,
            camera_x,
            camera_y,
            screen_width,
            screen_height,
            PIXEL_SIZE
        )

        #draw character on top of world
        character_screen_x = screen_width // 2
        character_screen_y = screen_height // 2

        character.draw(
            screen,
            character_screen_x,
            character_screen_y,
            PIXEL_SIZE
        )

        #draw placement preview under the mouse while placement mode is active
        if placement_state.active and placement_state.selected_machine_id == "conveyor":
            if belt_dragging and belt_drag_tiles:
                usable_tiles = belt_drag_tiles[:player_inventory.get_quantity("conveyor")]
                belt_preview = machine_placement.build_belt_path(
                    usable_tiles, placed_machines, WORLD_RADIUS,
                    placement_state.orientation, start_anchor=belt_drag_anchor
                )
                if belt_drag_anchor is not None and belt_preview:
                    # Preview the updated end piece as well as the new belts.
                    endpoint = machine_placement.get_extended_endpoint_placement(
                        placed_machines, belt_drag_anchor,
                        (belt_preview[0][0], belt_preview[0][1])
                    )
                    if endpoint is not None:
                        machine_placement.draw_belt_path_preview(
                            screen, [endpoint], camera_x, camera_y,
                            screen_width, screen_height, PIXEL_SIZE
                        )
                machine_placement.draw_belt_path_preview(
                    screen, belt_preview, camera_x, camera_y,
                    screen_width, screen_height, PIXEL_SIZE
                )
            else:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                gx, gy = machine_placement.screen_to_world(
                    mouse_x, mouse_y, camera_x, camera_y,
                    screen_width, screen_height, PIXEL_SIZE
                )
                valid, reason = machine_placement.can_place_machine(
                    "conveyor", gx, gy, resource_nodes_data,
                    placed_machines, WORLD_RADIUS
                )
                if machine_placement.is_open_belt_endpoint((gx, gy), placed_machines):
                    # Existing endpoints are valid drag starts, not new placements.
                    sx, sy = machine_placement.world_to_screen(
                        gx, gy, camera_x, camera_y,
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
                        screen, "conveyor", gx, gy, placement_state.orientation,
                        valid, camera_x, camera_y,
                        screen_width, screen_height, PIXEL_SIZE
                    )
                    if not valid:
                        screen.blit(placement_font.render(
                            reason, True, (255, 120, 120)
                        ), (15, 40))

            belt_message = (
                f"Conveyor | x{player_inventory.get_quantity('conveyor')} | "
                "Drag empty tiles or from an existing belt end | "
                "R rotates single piece | ESC/right click cancels"
            )
            screen.blit(placement_font.render(belt_message, True, (255, 255, 255)), (15, 15))

        elif placement_state.active:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                preview_grid_x, preview_grid_y = (
                    machine_placement.screen_to_world(
                        mouse_x,
                        mouse_y,
                        camera_x,
                        camera_y,
                        screen_width,
                        screen_height,
                        PIXEL_SIZE
                    )
                )

                can_place, placement_reason = (
                    machine_placement.can_place_machine(
                        placement_state.selected_machine_id,
                        preview_grid_x,
                        preview_grid_y,
                        resource_nodes_data,
                        placed_machines,
                        WORLD_RADIUS,
                        world,
                        tile_types
                    )
                )

                machine_placement.draw_placement_preview(
                    screen,
                    placement_state.selected_machine_id,
                    preview_grid_x,
                    preview_grid_y,
                    placement_state.orientation,
                    can_place,
                    camera_x,
                    camera_y,
                    screen_width,
                    screen_height,
                    PIXEL_SIZE
                )

                #temporary placement instructions
                placement_text = (
                    f"Placing: {placement_state.selected_machine_id} | "
                    f"Facing: {machine_placement.get_orientation_name(placement_state.orientation)} | "
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
        if inventory_open:
            inventory_ui.draw(screen, player_inventory)

        #display world
        pygame.display.flip()

    #return to previous screen
    return