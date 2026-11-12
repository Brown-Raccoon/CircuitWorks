#imports
#pygame
import pygame
from sympy import false
#world generation
import world_generation_settings
#character creator
import character_creator
import world_load_settings

#variables
#main game running variable
running = True

#color constants

STEEL = (55, 59, 64)
BLACK = (0,0,0)
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
title_font = pygame.font.SysFont("arial", 192, bold=True)
button_font = pygame.font.SysFont("arial", 64)


#create Buttons
btn_w, btn_h = 280,80
#center buttons to the right side of the screen
btn_x = (screen_width - btn_w) - 100

#vertical spaceing of buttons
start_y = 440
load_y = 630
settings_y = 740
quit_y = 850

#create button interactions
start_rect = pygame.Rect(btn_x, start_y, btn_w, btn_h)
load_rect = pygame.Rect(btn_x, load_y, btn_w, btn_h)
settings_rect = pygame.Rect(btn_x, settings_y, btn_w, btn_h)
quit_rect = pygame.Rect(btn_x, quit_y, btn_w, btn_h)

background_image = pygame.image.load("G-Sugar_Beet.jpg").convert()
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
#create character button wider than the others so the label fits
cc_w, cc_h = 440, 60
cc_x = (screen_width - btn_w) - 200
cc_y = 550
create_character_rect = pygame.Rect(cc_x, cc_y, cc_w, cc_h)

#track hover state of buttons
start_hover = False
load_hover = False
settings_hover = False
quit_hover = False

def draw_start():
    #draw screen
    screen.blit(background_image, (0, 0))

    #draw buttons 
    pygame.draw.rect(screen, DARK_GRAY, start_rect)
    start_text = button_font.render("Start", True, GRAY)
    pygame.draw.rect(screen, DARK_GRAY, load_rect)
    load_text = button_font.render("Load", True, GRAY)
    pygame.draw.rect(screen, DARK_GRAY, settings_rect)
    settings_text = button_font.render("Settings", True, GRAY)
    pygame.draw.rect(screen, RED, quit_rect)
    quit_text = button_font.render("Quit Game", True, GRAY)

    #draw title
    title_surface = title_font.render("CircuitWorks", True, STEEL)
    title_rect = title_surface.get_rect(center = (screen_width //2, 150))
    screen.blit(title_surface, title_rect)

#draw screen
screen.blit(background_image, (0, 0))

#draw buttons 
pygame.draw.rect(screen, DARK_GRAY, start_rect)
start_text = button_font.render("Start", True, GRAY)
pygame.draw.rect(screen, DARK_GRAY, load_rect)
load_text = button_font.render("Load", True, GRAY)
pygame.draw.rect(screen, DARK_GRAY, settings_rect)
settings_text = button_font.render("Settings", True, GRAY)
pygame.draw.rect(screen, RED, quit_rect)
quit_text = button_font.render("Quit Game", True, GRAY)

#draw title
title_surface = title_font.render("CircuitWorks", True, STEEL)
title_rect = title_surface.get_rect(center = (screen_width //2, 150))
screen.blit(title_surface, title_rect)


## Component Placement UI
placement_ui = False
writing_ui = False

#Define dimensions of the main placement portion
placement_ui_dimensions = pygame.Rect(300, 130, 1500, 900)

#Define dimensions of the location of components to be presented
placement_ui_items_dimensions = pygame.Rect(120, 130, 300, 900)

#Define the dimenstions of the programming ui 
programming_ui_dimensions = pygame.Rect(120, 130, 1680, 900)

#Define the dimensions of the text box the user can click
programming_ui_text = pygame.Rect(140, 180, 1640, 800)

#Define color for the main placement portion
PLACE_COLOR = (237, 255, 217)

#Define color for the location of components
PLACE_ITEMS_COLOR = (145, 145, 144)

#Define color for the writing_ui
PROGRAM_COLOR = (69, 63, 63)

#Define color of the text that shows up when 
#User types
PROGRAM_TEXT_COLOR = (255, 255, 255)

#Define the font of the text that shows up when
#The user types
base_font = pygame.font.Font(None, 32)

#Holds the users text
program_text = ""

#Defines the current level if the user has clicked 
#The programming_ui_text to allow user input
active_text_input = False


#mainloop
while running == True:

    #track mouse
    mouse_pos = pygame.mouse.get_pos()

    #listens for input
    for event in pygame.event.get():
        #if click x end loop
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            #This listens if the Tab key is pressed
            #Then brings up the placement_ui 
            if event.key == pygame.K_TAB:
                placement_ui = not placement_ui

            #This will check if the key 1 is pressed
            #Then brings up the writing_ui only when the
            #Placement_ui is already open
            if placement_ui:
                if event.key == pygame.K_1:
                    writing_ui = True
                
                #elif writing_ui == True and pygame.K_ESCAPE:
                    #writing_ui = False

        #if click any button
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                #if click start button
                if start_rect.collidepoint(mouse_pos):
                    world_generation_settings.start(screen)
                    draw_start()

                if load_rect.collidepoint(mouse_pos):
                    world_load_settings.start(screen)
                    draw_start()

                #if click quit button
                if quit_rect.collidepoint(mouse_pos):
                    running = False

                #if click create character button
                if create_character_rect.collidepoint(mouse_pos):
                    character_creator.start(screen, create_character_rect)
                    draw_start()

            #This will check if the user has enabled text input by
            #looking to see if the user clicked anywhere in the programming_ui_text
            if programming_ui_text.collidepoint(event.pos):
                active_text_input = True

        #This will track the inputs made by the user and add them
        if event.type == pygame.KEYDOWN and active_text_input:
            program_text += event.unicode


    #game logic


    #draw buttons
    #start
    #if hover over start
    if start_rect.collidepoint(mouse_pos):
        # Brighter when hovered
        pygame.draw.rect(screen, BLUE, start_rect)
        # Change text color to White
        start_text = button_font.render("Start", True, WHITE)
        start_hover = True
    #otherwise normal color
    elif start_hover:
        pygame.draw.rect(screen, DARK_GRAY, start_rect)
        start_text = button_font.render("Start", True, GRAY)
        start_hover = False
    screen.blit(start_text, start_text.get_rect(center=start_rect.center))



    #load
    if load_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, BLUE, load_rect)
        load_text = button_font.render("Load", True, WHITE)
        load_hover = True
    elif load_hover:
        pygame.draw.rect(screen, DARK_GRAY, load_rect)
        load_text = button_font.render("Load", True, GRAY)
        load_hover = False
    screen.blit(load_text, load_text.get_rect(center=load_rect.center))

    #settings
    if settings_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, BLUE, settings_rect)
        settings_text = button_font.render("Settings", True, WHITE)
        settings_hover = True
    elif settings_hover:
        pygame.draw.rect(screen, DARK_GRAY, settings_rect)
        settings_text = button_font.render("Settings", True, GRAY)
        settings_hover = False
    screen.blit(settings_text, settings_text.get_rect(center=settings_rect.center))

    #Quit
    #if hover over quit button
    if quit_rect.collidepoint(mouse_pos):
            # Brighter when hovered
            pygame.draw.rect(screen, LIGHT_RED, quit_rect)
            # Change text color to White
            quit_text = button_font.render("Quit Game", True, WHITE)
            quit_hover = True
            
        #otherwise normal color
    elif quit_hover:
            pygame.draw.rect(screen, RED, quit_rect)
            quit_text = button_font.render("Quit Game", True, GRAY)
            quit_hover = False
            
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


    #Checks if the placement_ui is set to true
    #Then draws the rectangles for it
    if placement_ui:
        pygame.draw.rect(screen, PLACE_COLOR, placement_ui_dimensions, border_radius = 10)
        pygame.draw.rect(screen, PLACE_ITEMS_COLOR, placement_ui_items_dimensions, border_top_left_radius = 10, border_bottom_left_radius = 10)

    #Checks if the writing_ui is set to true
    #Then draws the rectangle for it
    if writing_ui:
        pygame.draw.rect(screen, PROGRAM_COLOR, programming_ui_dimensions, border_radius = 10)
        pygame.draw.rect(screen, PROGRAM_COLOR, programming_ui_text)

    #Checks if user has clicked on the active_text_input
    #Then renders the keys pressed onto the screen
    if active_text_input:
        text_surface = base_font.render(program_text, True, PROGRAM_TEXT_COLOR)
        screen.blit(text_surface, (0, 0))

    #update display
    pygame.display.flip()