#imports
import pygame
import random
import json
from  pathlib import Path

# set constants and variables
# size of each tile in pixels
PIXEL_SIZE = 32
#number of tiles from center in a direction
WORLD_RADIUS = 20
#total number of tiles in world
WORLD_SIZE = WORLD_RADIUS * 2 + 1

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

def start(screen, world_seed):

    #send to generate world
    world, world_seed = generate_world(world_seed)

    #get screen size
    screen_width, screen_height = screen.get_size()


    #"camera"
    #sets "camera position"
    camera_x = 0
    camera_y = 0

    #main world loop
    running = True

    while running:
        #detect events/inputs
        for event in pygame.event.get():
            #allow window to close
            if event.type == pygame.quit:
                running = False

            #keybord input
            elif event.type == pygame.KEYDOWN:
                #esc to leave world(temporary)
                if event.key == pygame.K_ESCAPE:
                    running = False

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
                if(-WORLD_RADIUS <= x <= WORLD_RADIUS and -WORLD_RADIUS <= y <= WORLD_RADIUS):
                    #get tile id
                    tile_id = world[(x, y)]

                    #get tile info from json
                    tile_info = tile_types[tile_id]

                    #get tile color
                    tile_color = tuple(tile_info["color"])

                    #convert world coordinates to screen coordinates
                    screen_x = (screen_width // 2 + (x - camera_x) * PIXEL_SIZE)
                    screen_y = (screen_height // 2 + (y - camera_y) * PIXEL_SIZE)

                    #draw tile
                    pygame.draw.rect(screen, tile_color, (screen_x, screen_y, PIXEL_SIZE, PIXEL_SIZE))

        #display world
        pygame.display.flip()

    #return to previous screen
    return