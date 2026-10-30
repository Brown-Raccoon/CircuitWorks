#imports
import pygame
import random
import json
from pathlib import Path
import save_handler
import resource_nodes
from inventory import Inventory
import inventory_ui
import character
import machine_placement

# set constants and variables
# size of each tile in pixels
PIXEL_SIZE = 32
#number of tiles from center in a direction
WORLD_RADIUS = 20
#total number of tiles in world
WORLD_SIZE = (WORLD_RADIUS ** 2)* 4 + 1

# json file pathing
tile_file = Path(__file__).with_name("tile_type_assignment.json")

# load tile types from json file
def load_tile_types():
    #open tile type json file
    with tile_file.open("r", encoding="utf-8") as file:
        #turn json data into python data
        data = json.load(file)
    #return tile info
    return data["tiles"]

# define tile_types variable to hold the loaded tile types
tile_types = load_tile_types()

# check world seed and generate world
def generate_world(world_seed):
    # check if user input a world seed, if not generate new seed
    if world_seed == "":
        # generate a new world seed
        world_seed = str(random.randint(1000000000, 9999999999))

    #makes sure same world comes from same seed
    random_generator = random.Random(world_seed)

    #hold world data
    world = {}

    for x in range(-WORLD_RADIUS, WORLD_RADIUS + 1):
        for y in range(-WORLD_RADIUS, WORLD_RADIUS + 1):

            #chooses random number
            tile_number = random_generator.randint(0, 99)

            #grass
            if tile_number < 60:
                tile_id = "2"
            #dirt
            elif tile_number < 75:
                tile_id = "3"
            #stone
            elif tile_number < 90:
                tile_id = "4"
            #sand
            elif tile_number < 96:
                tile_id = "6"
            #water
            elif tile_number < 99:
                tile_id = "1"
            #snow
            else:
                tile_id = "7"

            #store the tiles
            world[(x, y)] = tile_id

    #return the generated world and seed
    return world, world_seed

def start(screen, world_seed, world_name, load):

    #place character at center of world
    character.spawn_at_center()

    #create player inventory
    player_inventory = Inventory()

    #temporary test items
    player_inventory.add_item("copper_wire", 10)
    player_inventory.add_item("resistor", 5)
    player_inventory.add_item("circuit_board", 3)
    player_inventory.add_item("miner", 3)
    player_inventory.add_item("assembler", 1)
    player_inventory.add_item("conveyor", 30)  # temporary test belts

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

        placed_machines = save_handler.load_entity(save_path)

        #update character position from save data
        character.grid_x = character_data["Pos"][0]
        character.grid_y = character_data["Pos"][1]

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
                
                #Save world and resource nodes to save file before exiting

                inv_temp = player_inventory.to_dict()
                character_data = {
                    "Pos" : [character.grid_x, character.grid_y],
                    "inventory" : inv_temp
                }


                save_handler.save_world(
                    save_path, 
                    world,
                    resource_nodes_data, 
                    WORLD_RADIUS, 
                    WORLD_SIZE)
                save_handler.save_nodes(save_path, resource_nodes_data)
                save_handler.save_character(save_path, character_data)
                save_handler.save_entitys(save_path, placed_machines)



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
                        #Save world and resource nodes to save file before exiting
                        inv_temp = player_inventory.to_dict()
                        character_data = {
                            "Pos" : [character.grid_x, character.grid_y],
                            "inventory" : inv_temp
                        }
                        
                        save_handler.save_world(
                            save_path, 
                            world, 
                            resource_nodes_data, 
                            WORLD_RADIUS, 
                            WORLD_SIZE)
                        
                        save_handler.save_nodes(save_path, resource_nodes_data)
                        save_handler.save_character(save_path, character_data)

                        print("entities saved: ", placed_machines)

                        save_handler.save_entitys(save_path, placed_machines)

                        running = False

                #movement only works while inventory is closed
                elif not inventory_open:

                    #up
                    if event.key in (pygame.K_w, pygame.K_UP):
                        character.move(0, -1, WORLD_RADIUS)

                    #down
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        character.move(0, 1, WORLD_RADIUS)

                    #left
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        character.move(-1, 0, WORLD_RADIUS)

                    #right
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        character.move(1, 0, WORLD_RADIUS)

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
                                    WORLD_RADIUS
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

        #find visible tiles(those on the screen currently)
        tiles_x = screen_width // PIXEL_SIZE + 2
        tiles_y = screen_height // PIXEL_SIZE + 2

        #half visable tiles
        half_tiles_x = tiles_x // 2
        half_tiles_y = tiles_y // 2

        #draw the tiles
        for x in range(camera_x - half_tiles_x, camera_x + half_tiles_x + 1):
            for y in range(camera_y - half_tiles_y, camera_y + half_tiles_y + 1):

                #make sure coordinates exist in world
                if (
                    -WORLD_RADIUS <= x <= WORLD_RADIUS
                    and -WORLD_RADIUS <= y <= WORLD_RADIUS
                ):
                    #get tile id
                    tile_id = world[(x, y)]

                    #get tile info from json
                    tile_info = tile_types[tile_id]

                    #get tile color
                    tile_color = tuple(tile_info["color"])

                    #convert world coordinates to screen coordinates
                    screen_x = (
                        screen_width // 2
                        + (x - camera_x) * PIXEL_SIZE
                    )

                    screen_y = (
                        screen_height // 2
                        + (y - camera_y) * PIXEL_SIZE
                    )

                    #draw tile
                    pygame.draw.rect(
                        screen,
                        tile_color,
                        (screen_x, screen_y, PIXEL_SIZE, PIXEL_SIZE)
                    )

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
                        WORLD_RADIUS
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