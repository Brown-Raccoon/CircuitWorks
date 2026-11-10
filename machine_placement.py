import json
from pathlib import Path

import pygame


# MACHINE DEFINITIONS
MACHINE_FILE = Path(__file__).parent / "machine design idea folder" / "Machines.json"


def load_all_machines():
    """Load every machine definition from Machines.json."""
    with MACHINE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


# Load definitions once when this module is imported.
MACHINES = load_all_machines()


def reload_machines():
    """
    Reload Machines.json.

    Mostly useful while testing so changes to the JSON can be picked up
    without changing the rest of the placement code.
    """
    global MACHINES
    MACHINES = load_all_machines()
    return MACHINES


def get_machine(machine_id):
    """Return one machine definition, or None if it does not exist."""
    return MACHINES.get(machine_id)


# ORIENTATION

# The base machine drawing faces east
# Rotating clockwise gives south, west, then north.
ORIENTATION_NAMES = {
    0: "east",
    1: "south",
    2: "west",
    3: "north",
}


def normalize_orientation(orientation):
    """Keep orientation inside the range 0-3."""
    return orientation % 4


def rotate_orientation(orientation):
    """Rotate one step clockwise."""
    return (orientation + 1) % 4


def get_orientation_name(orientation):
    """
    Return the display name for an orientation.

    If Machines.json contains orientation names for a machine, those can still
    be used when placement data is created. This function provides a safe
    default.
    """
    return ORIENTATION_NAMES[normalize_orientation(orientation)]


# PLACEMENT MODE STATE
class MachinePlacementState:
    """
    Small object that tracks what the player is currently trying to place.

    Example:
        placement_state = MachinePlacementState()
        placement_state.start("miner")
        placement_state.rotate()
        placement_state.cancel()
    """

    def __init__(self):
        self.active = False
        self.selected_machine_id = None
        self.orientation = 0

    def start(self, machine_id):
        """Begin placement mode for a valid machine."""
        if get_machine(machine_id) is None:
            return False

        self.active = True
        self.selected_machine_id = machine_id
        self.orientation = 0
        return True

    def cancel(self):
        """Leave placement mode."""
        self.active = False
        self.selected_machine_id = None
        self.orientation = 0

    def rotate(self):
        """Rotate the selected machine clockwise."""
        if not self.active:
            return self.orientation

        self.orientation = rotate_orientation(self.orientation)
        return self.orientation


# COORDINATE HELPERS

def screen_to_world(
    mouse_x,
    mouse_y,
    camera_x,
    camera_y,
    screen_width,
    screen_height,
    pixel_size,
):
    """
    Convert a mouse position on the screen into a world-grid coordinate.

    This matches world_generation.py's current camera system, where the
    camera tile begins at the center of the screen.
    """
    center_x = screen_width // 2
    center_y = screen_height // 2

    grid_x = camera_x + ((mouse_x - center_x) // pixel_size)
    grid_y = camera_y + ((mouse_y - center_y) // pixel_size)

    return int(grid_x), int(grid_y)


def world_to_screen(
    grid_x,
    grid_y,
    camera_x,
    camera_y,
    screen_width,
    screen_height,
    pixel_size,
):
    """Convert a world-grid coordinate into the tile's screen position."""
    screen_x = (
        screen_width // 2
        + (grid_x - camera_x) * pixel_size
    )

    screen_y = (
        screen_height // 2
        + (grid_y - camera_y) * pixel_size
    )

    return int(screen_x), int(screen_y)


# PLACEMENT VALIDATION
def can_place_machine(
    machine_id,
    grid_x,
    grid_y,
    resource_nodes,
    placed_machines,
    world_radius=None,
):
    """
    Check whether a machine can be placed on a world tile.

    Returns:
        (True, "OK")
    or:
        (False, reason)

    Current rules:
    - machine must exist
    - tile must be inside the world, if world_radius is supplied
    - tile cannot already contain another machine
    - miners must be placed on a resource node

    Future machines can add more placement rules later.
    """
    machine = get_machine(machine_id)

    if machine is None:
        return False, f"Unknown machine '{machine_id}'"

    if world_radius is not None:
        if not (
            -world_radius <= grid_x <= world_radius
            and -world_radius <= grid_y <= world_radius
        ):
            return False, "Outside world"

    position = (grid_x, grid_y)

    if position in placed_machines:
        return False, "Tile already occupied"

    # Support placement metadata if it is added to Machines.json later.
    placement_info = machine.get("placement", {})
    requirement = placement_info.get("requires")

    # For now, miner always requires a resource node.
    if machine_id == "miner" or requirement in ("ore_node", "resource_node"):
        if position not in resource_nodes:
            return False, "Miner requires a resource node"

    return True, "OK"


# CREATE PLACED MACHINE DATA

def handle_build_click(
    selected_machine_id,
    grid_x,
    grid_y,
    orientation,
    resource_nodes,
    placed_machines,
    world_radius=None,
):
    """
    Attempt to create data for a newly placed machine.

    IMPORTANT:
    This function does NOT remove anything from inventory.
    world_generation.py should remove one machine only after success=True.

    Returns:
        success, message, placed_data
    """
    if not selected_machine_id:
        return False, "No machine selected", None

    machine = get_machine(selected_machine_id)

    if machine is None:
        return False, f"Machine '{selected_machine_id}' not found", None

    can_place, reason = can_place_machine(
        selected_machine_id,
        grid_x,
        grid_y,
        resource_nodes,
        placed_machines,
        world_radius,
    )

    if not can_place:
        return False, reason, None

    orientation = normalize_orientation(orientation)

    # Use optional names from Machines.json if they exist.
    orientation_values = (
        machine.get("orientation", {})
        .get("values", {})
    )

    orientation_name = orientation_values.get(
        str(orientation),
        get_orientation_name(orientation),
    )

    placed_data = {
        "machine_id": selected_machine_id,
        "x": grid_x,
        "y": grid_y,
        "orientation": orientation,
        "orientation_name": orientation_name,
    }

    message = (
        f"Placed {selected_machine_id} at "
        f"({grid_x}, {grid_y}) facing {orientation_name}"
    )

    return True, message, placed_data


# MACHINE DRAWING / ROTATION

def rotate_point(px, py, center_x, center_y, orientation):
    """Rotate a point around a center in 90-degree clockwise steps."""
    dx = px - center_x
    dy = py - center_y

    orientation = normalize_orientation(orientation)

    if orientation == 0:      # east
        rotated_x, rotated_y = dx, dy

    elif orientation == 1:    # south - 90 degrees clockwise
        rotated_x, rotated_y = -dy, dx

    elif orientation == 2:    # west - 180 degrees
        rotated_x, rotated_y = -dx, -dy

    else:                     # north - 270 degrees clockwise
        rotated_x, rotated_y = dy, -dx

    return center_x + rotated_x, center_y + rotated_y


def draw_machine_at_marker(
    screen,
    machine_id,
    screen_x,
    screen_y,
    pixel_size,
    orientation=0,
):
    """
    Draw one machine using the drawing instructions in Machines.json.

    screen_x and screen_y are the top-left corner of the world tile.
    """
    machine = get_machine(machine_id)

    if machine is None:
        return False

    colors = {
        name: tuple(value)
        for name, value in machine["colors"].items()
    }

    draw_calls = sorted(
        machine["draw_calls"],
        key=lambda call: call.get("layer", 0),
    )

    canvas_size = machine.get("canvas_size", 64)
    scale = pixel_size / canvas_size

    center_x = canvas_size / 2
    center_y = canvas_size / 2

    orientation = normalize_orientation(orientation)

    def get_color(color_name):
        # Magenta makes missing colors obvious during testing.
        return colors.get(color_name, (255, 0, 255, 255))

    for call in draw_calls:
        function_name = call.get("func")
        color = get_color(call.get("color"))

        outline_color = None
        if call.get("outline"):
            outline_color = get_color(call["outline"])

        outline_width = 0
        if outline_color is not None:
            outline_width = max(
                1,
                int(call.get("outline_width", 1) * scale),
            )

        # RECTANGLE
        if function_name == "rect":
            x = call["x"]
            y = call["y"]
            width = call["w"]
            height = call["h"]

            rect_center_x = x + width / 2
            rect_center_y = y + height / 2

            new_center_x, new_center_y = rotate_point(
                rect_center_x,
                rect_center_y,
                center_x,
                center_y,
                orientation,
            )

            # A 90/270 degree rotation swaps width and height.
            if orientation % 2 == 1:
                width, height = height, width

            new_x = new_center_x - width / 2
            new_y = new_center_y - height / 2

            scaled_x = new_x * scale + screen_x
            scaled_y = new_y * scale + screen_y
            scaled_width = width * scale
            scaled_height = height * scale

            rect = pygame.Rect(
                scaled_x,
                scaled_y,
                scaled_width,
                scaled_height,
            )

            radius = int(call.get("radius", 0) * scale)

            pygame.draw.rect(
                screen,
                color,
                rect,
                border_radius=radius,
            )

            if outline_color is not None:
                pygame.draw.rect(
                    screen,
                    outline_color,
                    rect,
                    outline_width,
                    border_radius=radius,
                )

        # CIRCLE
        elif function_name == "circle":
            x = call["x"]
            y = call["y"]
            radius = call["r"]

            new_x, new_y = rotate_point(
                x,
                y,
                center_x,
                center_y,
                orientation,
            )

            scaled_x = new_x * scale + screen_x
            scaled_y = new_y * scale + screen_y
            scaled_radius = radius * scale

            pygame.draw.circle(
                screen,
                color,
                (int(scaled_x), int(scaled_y)),
                max(1, int(scaled_radius)),
            )

            if outline_color is not None:
                pygame.draw.circle(
                    screen,
                    outline_color,
                    (int(scaled_x), int(scaled_y)),
                    max(1, int(scaled_radius)),
                    outline_width,
                )

        # ELLIPSE
        elif function_name == "ellipse":
            x = call["x"]
            y = call["y"]
            width = call["w"]
            height = call["h"]

            new_x, new_y = rotate_point(
                x,
                y,
                center_x,
                center_y,
                orientation,
            )

            if orientation % 2 == 1:
                width, height = height, width

            scaled_x = new_x * scale + screen_x
            scaled_y = new_y * scale + screen_y
            scaled_width = width * scale
            scaled_height = height * scale

            ellipse_rect = pygame.Rect(
                scaled_x - scaled_width / 2,
                scaled_y - scaled_height / 2,
                scaled_width,
                scaled_height,
            )

            # Handle RGBA colors (for shadows) using a temporary surface.
            if len(color) == 4:
                ellipse_surface = pygame.Surface(
                    (
                        max(1, int(scaled_width)),
                        max(1, int(scaled_height)),
                    ),
                    pygame.SRCALPHA,
                )

                pygame.draw.ellipse(
                    ellipse_surface,
                    color,
                    ellipse_surface.get_rect(),
                )

                screen.blit(
                    ellipse_surface,
                    ellipse_rect.topleft,
                )

            else:
                pygame.draw.ellipse(
                    screen,
                    color,
                    ellipse_rect,
                )

        # POLYGON
        elif function_name == "polygon":
            points = []

            for point_x, point_y in call["points"]:
                new_x, new_y = rotate_point(
                    point_x,
                    point_y,
                    center_x,
                    center_y,
                    orientation,
                )

                points.append(
                    (
                        new_x * scale + screen_x,
                        new_y * scale + screen_y,
                    )
                )

            pygame.draw.polygon(
                screen,
                color,
                points,
            )

    return True


# PREVIEW + PLACED MACHINE DRAWING

def draw_placement_preview(
    screen,
    machine_id,
    grid_x,
    grid_y,
    orientation,
    can_place,
    camera_x,
    camera_y,
    screen_width,
    screen_height,
    pixel_size,
):
    """
    Draw the machine ghost on the tile under the mouse.

    Green tint = valid placement
    Red tint   = invalid placement
    """
    screen_x, screen_y = world_to_screen(
        grid_x,
        grid_y,
        camera_x,
        camera_y,
        screen_width,
        screen_height,
        pixel_size,
    )

    tint = pygame.Surface(
        (pixel_size, pixel_size),
        pygame.SRCALPHA,
    )

    if can_place:
        tint.fill((100, 255, 100, 45))
    else:
        tint.fill((255, 80, 80, 60))

    screen.blit(tint, (screen_x, screen_y))

    draw_machine_at_marker(
        screen,
        machine_id,
        screen_x,
        screen_y,
        pixel_size,
        orientation,
    )


def draw_placed_machines(
    screen,
    placed_machines,
    camera_x,
    camera_y,
    screen_width,
    screen_height,
    pixel_size,
):
    """Draw every placed machine using the current camera position."""
    for (grid_x, grid_y), placed_data in placed_machines.items():
        screen_x, screen_y = world_to_screen(
            grid_x,
            grid_y,
            camera_x,
            camera_y,
            screen_width,
            screen_height,
            pixel_size,
        )

        draw_machine_at_marker(
            screen,
            placed_data["machine_id"],
            screen_x,
            screen_y,
            pixel_size,
            placed_data.get("orientation", 0),
        )
