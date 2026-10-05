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
    small_label_font = pygame.font.SysFont("arial", 16)
    button_font = pygame.font.SysFont("arial", 26)

    #panel pos - wider/taller than before to fit the sprite selection row
    panel_rect = pygame.Rect(anchor_rect.right + 20, anchor_rect.top, 340, 490)

    #preview window
    preview_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 20, 70, 70)

    #hue bar (only used when no sprite is selected - see the "Default" button below)
    bar_rect = pygame.Rect(panel_rect.x + 20, preview_rect.bottom + 30, 240, 35)
    hue_bar_surface = build_hue_bar_surface(bar_rect.width, bar_rect.height)

    #hex input
    hex_rect = pygame.Rect(panel_rect.x + 20, bar_rect.bottom + 25, 160, 40)

    #sprite selection thumbnails - one small button per sprite set (1-7)
    sprite_label_y = hex_rect.bottom + 20
    sprite_row_y = sprite_label_y + 25
    sprite_size = 36
    sprite_gap = 6
    sprite_rects = {}
    for sprite_id in range(1, 8):
        x = panel_rect.x + 20 + (sprite_id - 1) * (sprite_size + sprite_gap)
        sprite_rects[sprite_id] = pygame.Rect(x, sprite_row_y, sprite_size, sprite_size)

    #"Default" button, goes back to the plain colored smiley instead of a sprite
    default_rect = pygame.Rect(panel_rect.x + 20, sprite_row_y + sprite_size + 15, 110, 36)

    #cancel and confrim buttons
    cancel_rect = pygame.Rect(panel_rect.x + 20, panel_rect.bottom - 60, 110, 45)
    confirm_rect = pygame.Rect(panel_rect.x + 150, panel_rect.bottom - 60, 110, 45)


    #start from whatever color/sprite is already saved
    starting_color = character.get_color()
    hue, _, _ = colorsys.rgb_to_hsv(starting_color[0] / 255, starting_color[1] / 255, starting_color[2] / 255)

    #the sprite the player currently has selected in THIS panel (not yet saved to character.py)
    selected_sprite_id = character.get_sprite()

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
                        #picking a color switches back to the smiley
                        selected_sprite_id = None


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

                    #clicked the "Default" (smiley) button
                    elif default_rect.collidepoint(event.pos):
                        selected_sprite_id = None
                        hex_active = False

                    #clicked one of the sprite thumbnails
                    else:
                        clicked_sprite = False
                        for sprite_id, rect in sprite_rects.items():
                            if rect.collidepoint(event.pos):
                                selected_sprite_id = sprite_id
                                hex_active = False
                                clicked_sprite = True
                                break

                        #clicked somewhere else entirely
                        if not clicked_sprite:
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
                        #typing a hex color also switches back to the smiley
                        selected_sprite_id = None
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


        #preview box - shows the pending sprite OR color selection, whichever is active
        pygame.draw.rect(screen, (20, 20, 20), preview_rect)
        #clip so a tall sprite can't spill outside the preview box
        screen.set_clip(preview_rect)
        character.draw(screen, preview_rect.x, preview_rect.y, preview_rect.width, current_color, selected_sprite_id)
        screen.set_clip(None)

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

        #sprite selection label + thumbnails
        sprite_label = small_label_font.render("Or pick a character:", True, (255, 255, 255))
        screen.blit(sprite_label, (panel_rect.x + 20, sprite_label_y))

        for sprite_id, rect in sprite_rects.items():
            #highlight the currently selected sprite's thumbnail
            if selected_sprite_id == sprite_id:
                pygame.draw.rect(screen, (255, 255, 0), rect.inflate(4, 4), 2)

            pygame.draw.rect(screen, (20, 20, 20), rect)
            thumbnail = character.get_idle_frame(sprite_id)
            thumbnail = pygame.transform.scale(thumbnail, (rect.width - 4, rect.height - 4))
            screen.blit(thumbnail, (rect.x + 2, rect.y + 2))

        #"Default" (smiley) button
        if selected_sprite_id is None:
            pygame.draw.rect(screen, (100, 100, 220), default_rect)
        else:
            pygame.draw.rect(screen, (64, 64, 64), default_rect)
        default_text = small_label_font.render("Default", True, (255, 255, 255))
        screen.blit(default_text, default_text.get_rect(center=default_rect.center))

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
        character.set_sprite(selected_sprite_id)
        #only save the color if we're actually staying on the smiley
        if selected_sprite_id is None:
            character.set_color(current_color)



    return