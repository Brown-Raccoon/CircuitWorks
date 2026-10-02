#imports
import pygame
import world_generation
#variables/Constants
#world information
world_name = ""
world_seed = ""

#text box identification
#if world name is being typed in
name_active = False
#if seed box is being typed in
seed_active = False

#main code
def start(screen):
    #makes variables global
    global world_name, world_seed, name_active, seed_active

    #gets screen size and sets up center x direction
    screen_width, screen_height = screen.get_size()
    center_x = screen_width // 2

    #font for setting screen
    title_font = pygame.font.SysFont("arial", 48, bold=True)
    button_font = pygame.font.SysFont("arial", 32)

    #creates rectangles
    name_rect = pygame.Rect(center_x -200, 250, 400, 50)

    #world seed box
    seed_rect = pygame.Rect(center_x - 200, 350, 400, 50)

    #resource amount settings
    resource_low_rect = pygame.Rect(center_x - 300, 475, 180, 50)

    resource_medium_rect = pygame.Rect(center_x - 90, 475, 180, 50)

    resource_high_rect = pygame.Rect(center_x + 120, 475, 180, 50)

    #stores current selected resource amount
    resource_amount = "Medium"

    #difficulty settings
    difficulty_low_rect = pygame.Rect(center_x - 300, 600, 180, 50)

    difficulty_medium_rect = pygame.Rect(center_x - 90, 600, 180, 50)

    difficulty_high_rect = pygame.Rect(center_x + 120, 600, 180, 50)

    #stores the currently selected difficulty
    difficulty = "Medium"

    #Main Menu button
    return_rect = pygame.Rect(50, screen_height -80, 220, 50)
    #next step button
    next_rect = pygame.Rect(center_x -110, screen_height - 80, 220, 50)

    #main loop
    running = True

    while running == True:
        #listen for event/input
        for event in pygame.event.get():

            #allows window to close
            if event.type == pygame.QUIT:
                running = False

            #listen for keyboard inputs
            elif event.type == pygame.KEYDOWN:

                #world name input
                if name_active == True:

                #backspace removes last character
                    if event.key == pygame.K_BACKSPACE:
                        world_name = world_name[:-1]

                #enter stops typing in the name box
                    elif event.key == pygame.K_RETURN:
                        name_active = False

                #adds typed character to the text box
                    else:
                        world_name += event.unicode


                #world name input
                elif seed_active == True:

                #backspace removes last character
                    if event.key == pygame.K_BACKSPACE:
                        world_seed = world_seed[:-1]

                #enter stops typing in the name box
                    elif event.key == pygame.K_RETURN:
                        seed_active = False

                #adds typed character to the text box
                    else:
                        world_seed += event.unicode
                
            #mouse input
            #listen to mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:

                #only respond to left mouse button
                if event.button == 1:
                    #click world name box
                    if name_rect.collidepoint(event.pos):
                        name_active = True
                        seed_active = False

                    #click seed box
                    elif seed_rect.collidepoint(event.pos):
                        seed_active = True
                        name_active = False


                    #click resource settings box
                    #click resource LOW
                    elif resource_low_rect.collidepoint(event.pos):
                        resource_amount = "Low"

                    #click resource MEDIUM
                    elif resource_medium_rect.collidepoint(event.pos):
                        resource_amount = "Medium"

                    #click resource HIGH
                    elif resource_high_rect.collidepoint(event.pos):
                        resource_amount = "High"


                    #click difficulty settings
                    #click difficulty LOW
                    elif difficulty_low_rect.collidepoint(event.pos):
                        difficulty = "Low"

                    #click difficulty MEDIUM
                    elif difficulty_medium_rect.collidepoint(event.pos):
                        difficulty = "Medium"

                    #click difficulty HIGH
                    elif difficulty_high_rect.collidepoint(event.pos):
                        difficulty = "High"

                    #click on return to main menu button
                    elif return_rect.collidepoint(event.pos):
                        running = False

                    #click to move onto next step
                    elif next_rect.collidepoint(event.pos):
                        #call next step here
                        world_generation.start(screen, world_seed, world_name)

                    #click somewhere else deactive boxes 
                    else:
                        name_active = False
                        seed_active = False


        #drawing section
        #draw background
        screen.fill((30, 30, 35))

        #title
        title_text = title_font.render("World Gen Settings", True, (255,255,255))
        screen.blit(title_text, title_text.get_rect(center=(center_x, 100)))

        # world settings
        # world name
        name_label = button_font.render("World Name:", True, (255,255,255))
        screen.blit(name_label, name_label.get_rect(center=(center_x, 220)))

        #world name box
        pygame.draw.rect(screen, (255, 255, 255), name_rect)

        #typed text into box
        name_text = button_font.render(world_name, True, (0, 0, 0))
        screen.blit(name_text, (name_rect.x + 10, name_rect.y + 8))

        #world name cursor
        if name_active == True and (pygame.time.get_ticks()// 750) % 2 == 0:
            cursor_x = name_rect.x + 10 + name_text.get_width()
            pygame.draw.line(screen, (0, 0, 0), (cursor_x, name_rect.y + 8), (cursor_x, name_rect.y + 42), 2)

        #world seed
        #name text
        seed_label = button_font.render("World Seed:", True, (255, 255, 255))
        screen.blit(seed_label, seed_label.get_rect(center = (center_x, 320)))

        #seed box
        pygame.draw.rect(screen, (255, 255, 255), seed_rect)

        #typed text into box
        seed_text = button_font.render(world_seed, True, (0, 0, 0))
        screen.blit(seed_text, (seed_rect.x + 10, seed_rect.y + 8))

        #seed cursor
        if seed_active == True and (pygame.time.get_ticks()// 750) % 2 == 0:
            cursor_x = seed_rect.x + 10 + seed_text.get_width()
            pygame.draw.line(screen, (0, 0, 0), (cursor_x, seed_rect.y + 8), (cursor_x, seed_rect.y + 42), 2)


        #resource amount label
        resource_label = button_font.render("Resource Amount", True, (255, 255, 255))
        screen.blit(resource_label, resource_label.get_rect(center = (center_x, 440)))

        #resource buttons
        #low
        if resource_amount == "Low":
            pygame.draw.rect(screen, (128, 128, 128), resource_low_rect)
        else:
            pygame.draw.rect(screen, (64, 64, 64), resource_low_rect)
        resource_low_text = button_font.render("Low", True, (255, 255, 255))
        screen.blit(resource_low_text, resource_low_text.get_rect(center=resource_low_rect.center))

        #medium
        if resource_amount == "Medium":
            pygame.draw.rect(screen, (128, 128, 128), resource_medium_rect)
        else:
            pygame.draw.rect(screen, (64, 64, 64), resource_medium_rect)
        resource_medium_text = button_font.render("Medium", True, (255, 255, 255))
        screen.blit(resource_medium_text, resource_medium_text.get_rect(center=resource_medium_rect.center))

        #High
        if resource_amount == "High":
            pygame.draw.rect(screen, (128, 128, 128), resource_high_rect)
        else:
            pygame.draw.rect(screen, (64, 64, 64), resource_high_rect)
        resource_high_text = button_font.render("High", True, (255, 255, 255))
        screen.blit(resource_high_text, resource_high_text.get_rect(center=resource_high_rect.center))


        #difficulty label
        difficulty_label = button_font.render("Difficulty", True, (255, 255, 255))
        screen.blit(difficulty_label, difficulty_label.get_rect(center=(center_x, 565)))

        #difficulty buttons
        #low
        if difficulty == "Low":
            pygame.draw.rect(screen, (128, 128, 128), difficulty_low_rect)
        else:
            pygame.draw.rect(screen, (64, 64, 64), difficulty_low_rect)
        difficulty_low_text = button_font.render("Low", True, (255, 255, 255))
        screen.blit(difficulty_low_text, difficulty_low_text.get_rect(center = difficulty_low_rect.center))

        #medium
        if difficulty == "Medium":
            pygame.draw.rect(screen, (128, 128, 128), difficulty_medium_rect)
        else:
            pygame.draw.rect(screen, (64, 64, 64), difficulty_medium_rect)
        difficulty_medium_text = button_font.render("Medium", True, (255, 255, 255))
        screen.blit(difficulty_medium_text, difficulty_medium_text.get_rect(center=difficulty_medium_rect.center))

        #high
        if difficulty == "High":
            pygame.draw.rect(screen, (128, 128, 128), difficulty_high_rect)
        else:
            pygame.draw.rect(screen, (64, 64, 64), difficulty_high_rect)
        difficulty_high_text = button_font.render("High", True, (255, 255, 255))
        screen.blit(difficulty_high_text, difficulty_high_text.get_rect(center = difficulty_high_rect.center))


        #draw return button
        pygame.draw.rect(screen, (64, 64, 64), return_rect)
        return_text = button_font.render("Menu", True, (255, 255, 255))
        screen.blit(return_text, return_text.get_rect(center = return_rect.center))

        #draw next button
        pygame.draw.rect(screen, (64, 64, 64), next_rect)
        next_text = button_font.render("Next", True, (255, 255, 255))
        screen.blit(next_text, next_text.get_rect(center = next_rect.center))

        pygame.display.flip()

pygame.quit()