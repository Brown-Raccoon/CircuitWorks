import pygame

#varibles and constants


#some default options for now
character_color = (255, 200, 100)
character_shape = "Smiley"

#characters pos using the world grid coords
grid_x = 0
grid_y = 0

#called by the character creator when color is confirmed
def set_color(color):
    global character_color
    character_color = color


#returns the character color for creator preview window
def get_color():
    return character_color


#will reset the character back to the origin
def spawn_at_center():
    global grid_x, grid_y
    grid_x = 0
    grid_y = 0



#will move the player a single tile in a given direction
#dy and dx needs to be 1, 0 or -1 (eg. dx = 1 for right or dy = -1 for up)
def move(dx, dy, world_radius):
    global grid_x, grid_y


    new_x = grid_x + dx
    new_y = grid_y + dy


    if -world_radius <= new_x <= world_radius:
        grid_x = new_x

    if -world_radius <= new_y <= world_radius:
        grid_y = new_y





#will draw the character at screen pos
def draw(screen, screen_x, screen_y, pixel_size, color=None):

    draw_color = character_color if color is None else color

    #the center point of the tile
    center_x = screen_x + pixel_size // 2
    center_y = screen_y + pixel_size // 2


    #radius of the character circle
    radius = pixel_size // 2 - 2

    #body circle
    pygame.draw.circle(screen, draw_color, (center_x, center_y), radius)


    #body outline
    pygame.draw.circle(screen, (0, 0, 0), (center_x, center_y), radius, 2)


    #custom offset so the eyes fit for any pixel
    eye_radius = max(1, pixel_size // 12)
    eye_offset_x = pixel_size // 6
    eye_offset_y = pixel_size // 8


    #left eye
    pygame.draw.circle(screen, (0, 0, 0), (center_x - eye_offset_x, center_y - eye_offset_y), eye_radius)

    #right eye
    pygame.draw.circle(screen, (0, 0, 0), (center_x + eye_offset_x, center_y - eye_offset_y), eye_radius)

    #mouth
    mouth_rect = pygame.Rect(center_x - pixel_size // 4, center_y - pixel_size // 8, pixel_size // 2, pixel_size // 2)
    pygame.draw.arc(screen, (0, 0, 0), mouth_rect, 3.4, 6.0, 2)

