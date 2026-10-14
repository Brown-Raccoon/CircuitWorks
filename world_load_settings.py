#imports
import world_generation
import save_handler
import pygame
from sympy import false

#set Pixel size
PIXEL_SIZE = 32

#number of tiles from center in a direction
WORLD_RADIUS = 20

#total number of tiles in world
WORLD_SIZE = WORLD_RADIUS * 2 + 1

#main code
def start(screen):

    running = True

    #draw screen

    #background
    screen.fill((0, 0, 0))

    #get screen size
    screen_width, screen_height = screen.get_size()

    #find visible tiles(those on the screen currently)
    tiles_x = screen_width // PIXEL_SIZE + 2
    tiles_y = screen_height // PIXEL_SIZE + 2

    #half visable tiles
    half_tiles_x = tiles_x // 2
    half_tiles_y = tiles_y // 2

    #setup save list
    world_list = save_handler.list_saves()
    world_rectangles = []
    world_names = []
    worlds = []

    #Main Menu button
    return_rect = pygame.Rect(50, screen_height -80, 220, 50)

    hight_index = 0
    i = 0

    

    #create world rectangles and names
    for world in world_list:
        world_rect = pygame.Rect(100, 100 + (hight_index * 50), 700, 40)
        world_name = world.name
        world_tuple = (i,world_name, world_rect, world)

        worlds.append(world_tuple)
        world_names.append(world_name)
        world_rectangles.append(world_rect)

        i+=1
        hight_index += 1

    #create exit button
    pygame.draw.rect(screen, (200, 0, 0), return_rect)
    exit_text = pygame.font.SysFont(None, 30).render("Main Menu", True, (255, 255, 255))
    screen.blit(exit_text, (return_rect.x + 10, return_rect.y + 5))

    #main loop
    while running:

        #track mouse
        mouse_pos = pygame.mouse.get_pos()

        #listens for input
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:

                    #if click return button
                    if return_rect.collidepoint(mouse_pos):
                        running = False

                    #if click any world
                    for world in worlds:
                        world_index, world_name, world_rect, world_save = world
                        if world_rect.collidepoint(mouse_pos):

                            #load world
                            world_generation.start(screen, 0, world_save ,True)
                            running = False

            if event.type == pygame.QUIT:
                running = False

        

        #draw save list
        for world in worlds:
            world_index, world_name, world_rect, world_save = world
            if world_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (100, 100, 100), world_rect)
            else:
                pygame.draw.rect(screen, (50, 50, 50), world_rect)

            world_text = pygame.font.SysFont(None, 30).render(world_name, True, (255, 255, 255))

            screen.blit(world_text, (world_rect.x + 10, world_rect.y + 5))

        if return_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (150, 0, 0), return_rect)
        else:
            pygame.draw.rect(screen, (200, 0, 0), return_rect)
        exit_text = pygame.font.SysFont(None, 30).render("Main Menu", True, (255, 255, 255))
        screen.blit(exit_text, (return_rect.x + 10, return_rect.y + 5))

        pygame.display.flip()