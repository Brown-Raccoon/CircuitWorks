#imports
import pygame
from pathlib import Path

#varibles and constants

#some default options for now (used when no sprite is selected)
character_color = (255, 200, 100)
character_shape = "Smiley"

#characters pos using the world grid coords
grid_x = 0
grid_y = 0

#sprite support 

#folder + filename-prefix for each selectable sprite set 
#frame 1 is the idle pose and frames 2-4 are the walk cycle
SPRITE_SETS = {
    1: ("character1", "red-robot-man-right"),
    2: ("character2", "white-little-woman-right"),
    3: ("character3", "white-little-man-right"),
    4: ("character4", "green-robot-man-right"),
    5: ("character5", "dark-little-woman-right"),
    6: ("character6", "dark_little-man-right"),
    7: ("character7", "blue-robot-man-right"),
}

#the "assets" folder must sit next to this file (same folder as character.py)
ASSETS_PATH = Path(__file__).with_name("assets")

#currently selected sprite set
#none means "draw plain colored smiley instead"
character_sprite_id = None

#cache of loaded frame images, so each sprite set is only ever loaded from disk once
_loaded_frames = {}

#how many game frames to hold a walk cycle pose before snapping back to idle
WALK_ANIMATION_HOLD = 12

#animation state
animation_frame = 0
_animation_hold_timer = 0
facing_right = True

#a unique marker used as a default value below so draw() can tell the difference
#between "no override passed in" and "override passed in as None"
_NO_OVERRIDE = object()


#loads (and caches) the 4 animation frames for a given sprite set
def _load_frames(sprite_id):
    if sprite_id in _loaded_frames:
        return _loaded_frames[sprite_id]

    folder, base_name = SPRITE_SETS[sprite_id]
    filenames = [
        f"{base_name}-1-idle.png",
        f"{base_name}-2.png",
        f"{base_name}-3.png",
        f"{base_name}-4.png",
    ]

    frames = []
    for filename in filenames:
        image_path = ASSETS_PATH / folder / filename
        frames.append(pygame.image.load(str(image_path)).convert_alpha())

    _loaded_frames[sprite_id] = frames
    return frames


#returns just the idle frame for a sprite set  --used by character_creator.py to draw thumbnail buttons
def get_idle_frame(sprite_id):
    return _load_frames(sprite_id)[0]


#called by the character creator when a sprite is confirmed 
def set_sprite(sprite_id):
    global character_sprite_id
    character_sprite_id = sprite_id
    #load it in this step so the very first draw doesn't stall on disk access
    if sprite_id is not None:
        _load_frames(sprite_id)


#returns the currently selected sprite id or None if using the smiley
def get_sprite():
    return character_sprite_id


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
    global grid_x, grid_y, facing_right, animation_frame, _animation_hold_timer

    new_x = grid_x + dx
    new_y = grid_y + dy

    moved = False

    if -world_radius <= new_x <= world_radius:
        grid_x = new_x
        moved = True

    if -world_radius <= new_y <= world_radius:
        grid_y = new_y
        moved = True

    #only turn/animate if the character actually moved onto a new tile
    if moved:
        #face left/right based on horizontal movement (keeps last facing during vertical-only moves)
        if dx > 0:
            facing_right = True
        elif dx < 0:
            facing_right = False

        #advance to the next walk-cycle frame (cycles 1, 2, 3, 1, 2, 3...) and reset the hold timer
        animation_frame = (animation_frame % 3) + 1
        _animation_hold_timer = WALK_ANIMATION_HOLD


#will draw the character at screen pos
#color/sprite_id let other files (the creator's preview box) show a selection before it's confirmed;
#leave them unset to use whatever is actually saved
def draw(screen, screen_x, screen_y, pixel_size, color=None, sprite_id=_NO_OVERRIDE):
    global animation_frame, _animation_hold_timer

    effective_sprite_id = character_sprite_id if sprite_id is _NO_OVERRIDE else sprite_id

    #--- sprite mode ---
    if effective_sprite_id is not None:
        frames = _load_frames(effective_sprite_id)
        image = frames[animation_frame]

        if not facing_right:
            image = pygame.transform.flip(image, True, False)

        #scale the sprite to fit the tile - sprites are taller than they are wide,
        #so size by height and let width follow the sprite's own aspect ratio
        original_width, original_height = image.get_size()
        display_height = int(pixel_size * 1.4)
        display_width = int(original_width * (display_height / original_height))
        image = pygame.transform.scale(image, (display_width, display_height))

        #anchor the sprite's feet to the bottom-center of the tile
        draw_rect = image.get_rect()
        draw_rect.midbottom = (screen_x + pixel_size // 2, screen_y + pixel_size)
        screen.blit(image, draw_rect)

        #tick down the walk-animation hold timer, snapping back to idle once it runs out
        if _animation_hold_timer > 0:
            _animation_hold_timer -= 1
            if _animation_hold_timer == 0:
                animation_frame = 0

        return

    # we goin smiley mode (fallback / default when no sprite is selected)
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