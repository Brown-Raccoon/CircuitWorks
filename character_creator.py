import pygame
import colorsys
import character



#will build the hue bar as a offscreen image,
def build_hue_bar_surface(width, height):

    surface = pygame.Surface((width, height))

    for x in range(width):
        hue = x / width
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = (int(r * 255), int(g * 255), int(b * 255))
        pygame.draw.line(surface, color, (x, 0), (x, height))

    return surface

#will convert the cursor pos into the hue based on where it is on the bar
def get_hue_from_pos(pos, bar_rect):

    relative_x = pos[0] - bar_rect.left
    hue = relative_x / bar_rect.width

    return max(0.0, min(1.0, hue))



#will turn a (r, g, b) into a 6 character hex
def rgb_to_hex(rgb):
    return "{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2])

#will convery hex into a (r, g, b) or none.
def hex_to_rgb(hex_string):
    if len(hex_string) != 6:
        return None
    try:
        r = int(hex_string[0:2], 16)
        g = int(hex_string[2:4], 16)
        b = int(hex_string[4:6], 16)
        return (r, g, b)
    except ValueError:
        return None



#will open the character creator panel.
def start(screen, anchor_rect):

    #this will take a screenshot of the main menu as a background so that we dont need to make a seperate window
    background = screen.copy()

    #font
    label_font = pygame.font.SysFont("arial", 22)
    button_font = pygame.font.SysFont("arial", 26)

    #panel pos
    panel_rect = pygame.Rect(anchor_rect.right + 20, anchor_rect.top, 280, 320)

    #preview window
    preview_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 20, 70, 70)

    #hue bar
    bar_rect = pygame.Rect(panel_rect.x + 20, preview_rect.bottom + 30, 240, 35)
    hue_bar_surface = build_hue_bar_surface(bar_rect.width, bar_rect.height)

    #hex input
    hex_rect = pygame.Rect(panel_rect.x + 20, bar_rect.bottom + 25, 160, 40)

    #cancel and confrim buttons
    cancel_rect = pygame.Rect(panel_rect.x + 20, panel_rect.bottom - 60, 110, 45)
    confirm_rect = pygame.Rect(panel_rect.x + 150, panel_rect.bottom - 60, 110, 45)

        
    #start from whatever color is saved
    starting_color = character.get_color()
    hue, _, _ = colorsys.rgb_to_hsv(starting_color[0] / 255, starting_color[1] / 255, starting_color[2] / 255)


    #hex textbox state
    hex_text = rgb_to_hex(starting_color)
    hex_active = False

    #dragging
    dragging_bar = False

    #currently selcted color updated each frame from hue
    current_color = starting_color


    running = True
    confirmed = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    #clicked the hue bar
                    if bar_rect.collidepoint(event.pos):
                        dragging_bar = True
                        hue = get_hue_from_pos(event.pos, bar_rect)
                        hex_active = False


                    #clicked on hex box
                    elif hex_rect.collidepoint(event.pos):
                        hex_active = True

                    #clicked cancel
                    elif cancel_rect.collidepoint(event.pos):
                        running = False

                    #clicked confirm
                    elif confirm_rect.collidepoint(event.pos):
                        confirmed = True
                        running = False

                    #clicked somewhere else
                    else:
                        hex_active = False

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging_bar = False

            elif event.type == pygame.MOUSEMOTION:
                #should keep updating the hue while the mouse is held down
                if dragging_bar:
                    hue = get_hue_from_pos(event.pos, bar_rect)

            elif event.type == pygame.KEYDOWN and hex_active:
                #backspace the last typed character
                if event.key == pygame.K_BACKSPACE:
                    hex_text = hex_text[:-1]

                #if enter is pressed, it confirms hex value
                elif event.key == pygame.K_RETURN:
                    parsed = hex_to_rgb(hex_text)
                    if parsed is not None: 
                        hue, _, _ = colorsys.rgb_to_hsv(parsed[0] / 255, parsed [1] / 255, parsed[2] / 255)
                    hex_active = False

                #needs to be valid hex format
                else:
                    typed_char = event.unicode.upper()

                    if typed_char in "0123456789ABCDEF" and len(hex_text) < 6:
                        hex_text += typed_char

        #compute color from hue every frame
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        current_color = (int(r * 255), int(g * 255), int(b * 255))


        #keep sync between hex box and bar
        if not hex_active:
            hex_text = rgb_to_hex(current_color)

        #draw frozen menu snapshot
        screen.blit(background, (0, 0))

        #panel background
        pygame.draw.rect(screen, (45, 45, 50), panel_rect)
        pygame.draw.rect(screen, (255, 255, 255), panel_rect, 2)


        #preview box
        pygame.draw.rect(screen, (20, 20, 20), preview_rect)
        character.draw(screen, preview_rect.x, preview_rect.y, preview_rect.width, current_color)

        preview_label = label_font.render("Preview", True, (255, 255, 255))
        screen.blit(preview_label, (preview_rect.right + 10, preview_rect.centery - 10))

        #hue bar
        screen.blit(hue_bar_surface, bar_rect)
        pygame.draw.rect(screen, (255, 255, 255), bar_rect, 2)

        #marker that shows current hue position
        marker_x = bar_rect.left + int(hue * bar_rect.width)
        pygame.draw.line (screen, (255, 255, 255), (marker_x, bar_rect.top - 5), (marker_x, bar_rect.bottom + 5), 3)


        #hex input box
        pygame.draw.rect(screen, (255, 255, 255), hex_rect)
        hex_display_text = button_font.render("#" + hex_text, True, (0, 0, 0))
        screen.blit(hex_display_text, (hex_rect.x + 10, hex_rect.y + 8))

        #cancel button
        pygame.draw.rect(screen, (200, 40, 40), cancel_rect)
        cancel_text = button_font.render("Cancel", True, (255, 255, 255))
        screen.blit(cancel_text, cancel_text.get_rect(center=cancel_rect.center))

        #confirm button
        pygame.draw.rect(screen, (40, 180, 40), confirm_rect)
        confirm_text = button_font.render("Confirm", True, (255, 255, 255))
        screen.blit(confirm_text, confirm_text.get_rect(center=confirm_rect.center))

        pygame.display.flip()

    if confirmed:
        character.set_color(current_color)



    return

    
                    

