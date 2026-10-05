# imports
import pygame
import inventory


# UI colors
BACKGROUND = (30, 30, 35)
PANEL_COLOR = (45, 45, 50)
SECTION_COLOR = (60, 60, 68)
ROW_COLOR = (72, 72, 82)
BORDER_COLOR = (185, 185, 195)

WHITE = (255, 255, 255)
LIGHT_GRAY = (205, 205, 215)
MUTED_GRAY = (145, 145, 155)


# item helpers

# returns all owned inventory items that match a category
def get_items_by_category(player_inventory, category):
    category_items = []

    for item_key, quantity in player_inventory.get_all_items().items():

        # ignore anything that no longer exists in the definition file
        if item_key not in inventory.item_definitions:
            continue

        item_info = inventory.item_definitions[item_key]

        if item_info["category"] == category:
            category_items.append((item_key, quantity, item_info))

    return category_items

# draw item row
def draw_item_row(
    screen,
    row_rect,
    item_info,
    quantity,
    name_font,
    quantity_font
):
    # row background
    pygame.draw.rect(screen, ROW_COLOR, row_rect, border_radius=6)

    # item name
    name_text = name_font.render(
        item_info["name"],
        True,
        WHITE
    )

    screen.blit(
        name_text,
        (row_rect.x + 12, row_rect.y + 10)
    )

    # item quantity
    quantity_text = quantity_font.render(
        f"x{quantity}",
        True,
        LIGHT_GRAY
    )

    quantity_rect = quantity_text.get_rect(
        midright=(row_rect.right - 12, row_rect.centery)
    )

    screen.blit(quantity_text, quantity_rect)


#draw category sections

def draw_category_section(
    screen,
    section_rect,
    title,
    category,
    player_inventory,
    title_font,
    item_font,
    quantity_font,
    small_font
):
    # section background
    pygame.draw.rect(
        screen,
        SECTION_COLOR,
        section_rect,
        border_radius=8
    )

    pygame.draw.rect(
        screen,
        BORDER_COLOR,
        section_rect,
        2,
        border_radius=8
    )

    # category title
    title_text = title_font.render(
        title,
        True,
        WHITE
    )

    title_rect = title_text.get_rect(
        midtop=(section_rect.centerx, section_rect.y + 12)
    )

    screen.blit(title_text, title_rect)

    # get all owned items in this category
    category_items = get_items_by_category(
        player_inventory,
        category
    )

    # if the category is empty, show a message
    if len(category_items) == 0:
        empty_text = small_font.render(
            "No items",
            True,
            MUTED_GRAY
        )

        empty_rect = empty_text.get_rect(
            center=(section_rect.centerx, section_rect.y + 90)
        )

        screen.blit(empty_text, empty_rect)
        return

    # item row settings
    row_height = 50
    row_gap = 8
    row_x = section_rect.x + 12
    row_width = section_rect.width - 24
    row_y = section_rect.y + 55

    # draw each item in the category
    for item_key, quantity, item_info in category_items:

        # stop drawing if we run out of room
        if row_y + row_height > section_rect.bottom - 12:
            break

        row_rect = pygame.Rect(
            row_x,
            row_y,
            row_width,
            row_height
        )

        draw_item_row(
            screen,
            row_rect,
            item_info,
            quantity,
            item_font,
            quantity_font
        )

        row_y += row_height + row_gap



#main inventory drawing system
def draw(screen, player_inventory):
    screen_width, screen_height = screen.get_size()

    # dark transparent overlay over the game world
    overlay = pygame.Surface(
        (screen_width, screen_height),
        pygame.SRCALPHA
    )

    overlay.fill((0, 0, 0, 145))
    screen.blit(overlay, (0, 0))

    # panel size
    panel_width = min(900, screen_width - 120)
    panel_height = min(650, screen_height - 120)

    panel_x = (screen_width - panel_width) // 2
    panel_y = (screen_height - panel_height) // 2

    panel_rect = pygame.Rect(
        panel_x,
        panel_y,
        panel_width,
        panel_height
    )

    # main panel
    pygame.draw.rect(
        screen,
        PANEL_COLOR,
        panel_rect,
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        BORDER_COLOR,
        panel_rect,
        2,
        border_radius=10
    )

    # fonts
    title_font = pygame.font.SysFont(
        "arial",
        38,
        bold=True
    )

    section_title_font = pygame.font.SysFont(
        "arial",
        26,
        bold=True
    )

    item_font = pygame.font.SysFont(
        "arial",
        20
    )

    quantity_font = pygame.font.SysFont(
        "arial",
        20,
        bold=True
    )

    small_font = pygame.font.SysFont(
        "arial",
        17
    )

    # inventory title
    inventory_title = title_font.render(
        "Inventory",
        True,
        WHITE
    )

    inventory_title_rect = inventory_title.get_rect(
        midtop=(panel_rect.centerx, panel_rect.y + 18)
    )

    screen.blit(
        inventory_title,
        inventory_title_rect
    )

  
    # catagory layout
    section_top = panel_rect.y + 85
    section_bottom_margin = 25
    section_gap = 20

    section_height = (
        panel_rect.bottom
        - section_top
        - section_bottom_margin
    )

    section_width = (
        panel_width
        - 60
        - section_gap
    ) // 2

    # components on left
    components_rect = pygame.Rect(
        panel_rect.x + 30,
        section_top,
        section_width,
        section_height
    )

    # machines on right
    machines_rect = pygame.Rect(
        components_rect.right + section_gap,
        section_top,
        section_width,
        section_height
    )

    # draw components section
    draw_category_section(
        screen,
        components_rect,
        "Components",
        "component",
        player_inventory,
        section_title_font,
        item_font,
        quantity_font,
        small_font
    )

    # draw machines section
    draw_category_section(
        screen,
        machines_rect,
        "Machines",
        "machine",
        player_inventory,
        section_title_font,
        item_font,
        quantity_font,
        small_font
    )
