#imports
#pygame
import pygame

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

#start screen
pygame.init()

#set screen to full screen and get size
screen = pygame.display.set_mode((0,0),pygame.NOFRAME)
screen_width, screen_height = screen.get_size()

#screen_width = 1280
#screen_height = 720

#set up display screen
#fontsizes
title_font = pygame.font.SysFont("arial", 192, bold=True)
button_font = pygame.font.SysFont("arial", 64)

#######Custom Font
#custom_font = pygame.font.Font("determination.ttf", 45)
#title_font = pygame.font.SysFont(custom_font, 192, bold=True)

#create Buttons
btn_w, btn_h = 280,80
#center buttons to the right side of the screen
btn_x = (screen_width - btn_w) - 100

#vertical spaceing of buttons
start_y = 440
load_y = 550
settings_y = 660
quit_y = 770

#create button interactions
start_rect = pygame.Rect(btn_x, start_y, btn_w, btn_h)
load_rect = pygame.Rect(btn_x, load_y, btn_w, btn_h)
settings_rect = pygame.Rect(btn_x, settings_y, btn_w, btn_h)
quit_rect = pygame.Rect(btn_x, quit_y, btn_w, btn_h)

background_image = pygame.image.load("G-Sugar_Beet.jpg").convert()
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))


#mainloop
while running == True:
    #track mouse
    mouse_pos = pygame.mouse.get_pos()

    #listens for input
    for event in pygame.event.get():
        #if click x end loop
        if event.type == pygame.QUIT:
            running = False
        #if click quit button end loop
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if quit_rect.collidepoint(mouse_pos):
                    running = False

    #game logic

    #draw screen
    #screen.fill(BLACK)
    screen.blit(background_image, (0, 0))

    #draw title
    title_surface = title_font.render("CircuitWorks", True, STEEL)
    title_rect = title_surface.get_rect(center = (screen_width //2, 150))
    screen.blit(title_surface, title_rect)

    #draw buttons
    #start
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


    pygame.draw.rect(screen, RED, quit_rect)


    #Quit
    #if hover over quit button
    if quit_rect.collidepoint(mouse_pos):
        # Brighter when hovered
        pygame.draw.rect(screen, LIGHT_RED, quit_rect)
    #otherwise normal color
    #else:
    #    pygame.draw.rect(screen, RED, quit_rect)
    #button display

    quit_text = button_font.render("Quit Game", True, WHITE)
    screen.blit(quit_text, quit_text.get_rect(center=quit_rect.center))

    #update display
    pygame.display.flip()
#end game
pygame.quit()
