#imports
#pygame
import pygame
#world generation
import world_generation_settings
#character creator
import character_creator

#variables
#main game running variable
running = True

#color constants
BLACK = (0, 0, 0)
RED = (255, 0, 0)
LIGHT_RED = (255, 102, 102)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BLUE = (0, 0, 255)
CHARCOAL = (30, 30, 35)

#start screen
pygame.init()

#set screen to full screen and get size
screen = pygame.display.set_mode((0,0),pygame.NOFRAME)
screen_width, screen_height = screen.get_size()

#set up display screen
#fontsizes
title_font = pygame.font.SysFont("arial", 64, bold=True)
button_font = pygame.font.SysFont("arial", 32)

#create Buttons
btn_w, btn_h = 240,50
#center buttons horizontally
btn_x = (screen_width - btn_w)//2

#vertical spaceing of buttons
start_y = 300
load_y = 380
settings_y = 460
quit_y = 540

#create button interactions
start_rect = pygame.Rect(btn_x, start_y, btn_w, btn_h)
load_rect = pygame.Rect(btn_x, load_y, btn_w, btn_h)
settings_rect = pygame.Rect(btn_x, settings_y, btn_w, btn_h)
quit_rect = pygame.Rect(btn_x, quit_y, btn_w, btn_h)

#create character button wider than the others so the label fits
cc_w, cc_h = 280, 50
cc_x = (screen_width - cc_w)//2
cc_y = quit_y + 80
create_character_rect = pygame.Rect(cc_x, cc_y, cc_w, cc_h)


#mainloop
while running == True:
    #track mouse
    mouse_pos = pygame.mouse.get_pos()

    #listens for input
    for event in pygame.event.get():
        #if click x end loop
        if event.type == pygame.QUIT:
            running = False
        #if click any button
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                #if click start button
                if start_rect.collidepoint(mouse_pos):
                    world_generation_settings.start(screen)

                #if click quit button
                if quit_rect.collidepoint(mouse_pos):
                    running = False

                #if click create character button
                if create_character_rect.collidepoint(mouse_pos):
                    character_creator.start(screen, create_character_rect)

    #game logic

    #draw screen
    screen.fill(CHARCOAL)

    #draw title
    title_surface = title_font.render("CircuitWorks", True, WHITE)
    title_rect = title_surface.get_rect(center = (screen_width //2, 150))
    screen.blit(title_surface, title_rect)

    #draw buttons
    #start
    #if hover over start
    if start_rect.collidepoint(mouse_pos):
        # Brighter when hovered
        pygame.draw.rect(screen, BLUE, start_rect)
        # Change text color to White
        start_text = button_font.render("Start", True, WHITE)
    #otherwise normal color
    else:
        pygame.draw.rect(screen, DARK_GRAY, start_rect)
        start_text = button_font.render("Start", True, GRAY)
    screen.blit(start_text, start_text.get_rect(center=start_rect.center))

    #load
    pygame.draw.rect(screen, DARK_GRAY, load_rect)
    load_text = button_font.render("Load", True, GRAY)
    screen.blit(load_text, load_text.get_rect(center=load_rect.center))

    #settings
    pygame.draw.rect(screen, DARK_GRAY, settings_rect)
    settings_text = button_font.render("Settings", True, GRAY)
    screen.blit(settings_text, settings_text.get_rect(center=settings_rect.center))

    #Quit
    #if hover over quit button
    if quit_rect.collidepoint(mouse_pos):
        # Brighter when hovered
        pygame.draw.rect(screen, LIGHT_RED, quit_rect)
    #otherwise normal color
    else:
        pygame.draw.rect(screen, RED, quit_rect)
    #button display
    quit_text = button_font.render("Quit Game", True, WHITE)
    screen.blit(quit_text, quit_text.get_rect(center=quit_rect.center))

    #Create Character
    #if hover over create character button
    if create_character_rect.collidepoint(mouse_pos):
        # Brighter when hovered
        pygame.draw.rect(screen, BLUE, create_character_rect)
        create_character_text = button_font.render("Create Character", True, WHITE)
    #otherwise normal color
    else:
        pygame.draw.rect(screen, DARK_GRAY, create_character_rect)
        create_character_text = button_font.render("Create Character", True, GRAY)
    screen.blit(create_character_text, create_character_text.get_rect(center=create_character_rect.center))

    #update display
    pygame.display.flip()