import json
from pathlib import Path

import pygame


# MACHINE DEFINITIONS
MACHINE_FILE = Path(__file__).parent / "machine design idea folder" / "Machines.json"

# Conveyor definitions live next to this Python file.
BELT_FILE = Path(__file__).with_name("Belts.json")


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


# BELT DEFINITIONS AND DRAWING

def load_all_belts():
    """Load the conveyor shapes from Belts.json."""
    with BELT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


BELTS = load_all_belts()


def get_belt(belt_type):
    """Return one belt definition, or None if it is unknown."""
    return BELTS.get(belt_type)


def draw_belt(screen, belt_type, screen_x, screen_y, pixel_size, orientation=0):
    """Draw a straight or corner conveyor using Belts.json instructions."""
    belt_data = get_belt(belt_type)
    if belt_data is None:
        return

    colors = {name: tuple(value) for name, value in belt_data["colors"].items()}
    calls = sorted(belt_data["draw_calls"], key=lambda call: call.get("layer", 0))
    canvas_size = belt_data.get("canvas_size", 64)
    scale = pixel_size / canvas_size
    center = canvas_size / 2

    def get_color(name):
        return colors.get(name, (255, 0, 255))

    for call in calls:
        color = get_color(call["color"])
        outline = get_color(call["outline"]) if call.get("outline") else None
        outline_width = max(1, round(call.get("outline_width", 1) * scale))
        shape = call["func"]

        if shape == "rect":
            x, y = call["x"], call["y"]
            width, height = call["w"], call["h"]
            rect_center_x = x + width / 2
            rect_center_y = y + height / 2
            new_x, new_y = rotate_point(
                rect_center_x, rect_center_y, center, center, orientation
            )
            if orientation % 2 == 1:
                width, height = height, width
            rect = pygame.Rect(
                screen_x + (new_x - width / 2) * scale,
                screen_y + (new_y - height / 2) * scale,
                width * scale,
                height * scale,
            )
            radius = round(call.get("radius", 0) * scale)
            pygame.draw.rect(screen, color, rect, border_radius=radius)
            if outline:
                pygame.draw.rect(
                    screen, outline, rect, outline_width, border_radius=radius
                )

        elif shape == "circle":
            x, y = rotate_point(call["x"], call["y"], center, center, orientation)
            pygame.draw.circle(
                screen,
                color,
                (round(screen_x + x * scale), round(screen_y + y * scale)),
                max(1, round(call["r"] * scale)),
            )

        elif shape == "polygon":
            points = []
            for x, y in call["points"]:
                new_x, new_y = rotate_point(x, y, center, center, orientation)
                points.append((screen_x + new_x * scale, screen_y + new_y * scale))
            pygame.draw.polygon(screen, color, points)



# CONVEYOR PATH HELPERS
# Belts are inventory items named "conveyor". Each placed tile stores its
# shape in machine_id so the current save system needs no new fields.
BELT_MACHINE_PREFIX = "conveyor_"
BELT_DIRECTIONS = {0: (1, 0), 1: (0, 1), 2: (-1, 0), 3: (0, -1)}


def get_belt_type(machine_id):
    """Convert a saved conveyor ID to a visual definition key."""
    if not isinstance(machine_id, str):
        return None
    if machine_id == "conveyor":
        return "straight"
    if machine_id.startswith(BELT_MACHINE_PREFIX):
        belt_type = machine_id[len(BELT_MACHINE_PREFIX):]
        if get_belt(belt_type) is not None:
            return belt_type
    return None


def belt_direction(start, end):
    """Get the direction from one adjacent grid tile to another."""
    if start is None or end is None:
        return None
    delta = (end[0] - start[0], end[1] - start[1])
    for direction, movement in BELT_DIRECTIONS.items():
        if delta == movement:
            return direction
    return None


def belt_corner(in_direction, out_direction, single_orientation=0):
    """Use the same straight/corner mapping as the group's Belt Viewer."""
    if in_direction is None and out_direction is None:
        return "straight", normalize_orientation(single_orientation)
    if in_direction is None:
        return "straight", out_direction
    if out_direction is None:
        return "straight", in_direction
    if in_direction == out_direction:
        return "straight", in_direction
    if in_direction == (out_direction + 2) % 4:
        return "straight", in_direction

    right_turns = {(0, 1): 0, (1, 2): 1, (2, 3): 2, (3, 0): 3}
    left_turns = {(0, 3): 0, (3, 2): 3, (2, 1): 2, (1, 0): 1}
    if (in_direction, out_direction) in right_turns:
        return "corner_right", right_turns[(in_direction, out_direction)]
    if (in_direction, out_direction) in left_turns:
        return "corner_left", left_turns[(in_direction, out_direction)]
    return "straight", in_direction


def belt_input_direction(placed_belt):
    """Direction in which a conveyor receives an item (travel direction)."""
    belt_type = get_belt_type(placed_belt.get("machine_id"))
    if belt_type not in ("straight", "corner_right", "corner_left"):
        return None
    return normalize_orientation(placed_belt.get("orientation", 0))


def belt_output_direction(placed_belt):
    """Direction in which a conveyor sends an item."""
    in_direction = belt_input_direction(placed_belt)
    if in_direction is None:
        return None
    belt_type = get_belt_type(placed_belt["machine_id"])
    if belt_type == "corner_right":
        return (in_direction + 1) % 4
    if belt_type == "corner_left":
        return (in_direction - 1) % 4
    return in_direction


def is_open_belt_endpoint(position, placed_machines):
    """True for an existing conveyor whose output tile is not occupied.

    Allows players to start a second drag on the last belt, while preventing
    accidental modification of a belt that already connects to another piece.
    """
    data = placed_machines.get(position)
    if not isinstance(data, dict):
        return False
    output_direction = belt_output_direction(data)
    if output_direction is None:
        return False
    dx, dy = BELT_DIRECTIONS[output_direction]
    output_tile = (position[0] + dx, position[1] + dy)
    return output_tile not in placed_machines


def get_extended_endpoint_placement(placed_machines, anchor, next_tile):
    """Return the new visual for the old end belt when a drag continues it.

    This placement updates an *existing* belt and costs no inventory item.
    """
    if anchor is None or not is_open_belt_endpoint(anchor, placed_machines):
        return None
    new_direction = belt_direction(anchor, next_tile)
    if new_direction is None:
        return None
    old_direction = belt_input_direction(placed_machines[anchor])
    if old_direction is None or new_direction == (old_direction + 2) % 4:
        return None  # no U-turns: a belt cannot feed backward into itself
    belt_type, orientation = belt_corner(old_direction, new_direction)
    return anchor[0], anchor[1], belt_type, orientation


def extend_belt_drag(tiles, target, placed_machines, world_radius=None, start_anchor=None):
    """Extend a drag across empty horizontal/vertical tiles, never diagonally.

    Mutates tiles only if the entire segment can be added. Also fills in any
    tiles skipped by a fast mouse movement along a straight row/column.
    """
    if not tiles and start_anchor is None:
        candidate_tiles = [target]
    else:
        current = tiles[-1] if tiles else start_anchor
        dx, dy = target[0] - current[0], target[1] - current[1]
        if dx == 0 and dy == 0:
            return False
        if dx != 0 and dy != 0:
            return False
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        candidate_tiles = [
            (current[0] + step_x * i, current[1] + step_y * i)
            for i in range(1, abs(dx) + abs(dy) + 1)
        ]

    for position in candidate_tiles:
        if position in placed_machines or position in tiles:
            return False
        if world_radius is not None and not (
            -world_radius <= position[0] <= world_radius
            and -world_radius <= position[1] <= world_radius
        ):
            return False

    tiles.extend(candidate_tiles)
    return True


def build_belt_path(
    tiles, placed_machines=None, world_radius=None, single_orientation=0,
    start_anchor=None
):
    """Return (x, y, belt_type, orientation) for a continuous valid path."""
    if placed_machines is None:
        placed_machines = {}

    cleaned = []
    visited = set()
    for position in tiles:
        if position in visited:
            break
        if position in placed_machines:
            break
        if world_radius is not None and not (
            -world_radius <= position[0] <= world_radius
            and -world_radius <= position[1] <= world_radius
        ):
            break
        if cleaned and belt_direction(cleaned[-1], position) is None:
            break
        cleaned.append(position)
        visited.add(position)

    # A continued path must lead away from the old end belt.
    if start_anchor is not None:
        if not cleaned or get_extended_endpoint_placement(
            placed_machines, start_anchor, cleaned[0]
        ) is None:
            return []

    placements = []
    for index, (x, y) in enumerate(cleaned):
        prev = cleaned[index - 1] if index > 0 else start_anchor
        following = cleaned[index + 1] if index + 1 < len(cleaned) else None
        in_direction = belt_direction(prev, (x, y))
        out_direction = belt_direction((x, y), following)
        belt_type, orientation = belt_corner(
            in_direction, out_direction, single_orientation
        )
        placements.append((x, y, belt_type, orientation))
    return placements


def create_belt_placement(x, y, belt_type, orientation):
    """Make data compatible with save_handler.load_entity/save_entitys."""
    orientation = normalize_orientation(orientation)
    orientation_values = get_belt(belt_type)["orientation"].get("values", {})
    return {
        "machine_id": BELT_MACHINE_PREFIX + belt_type,
        "x": x,
        "y": y,
        "orientation": orientation,
        "orientation_name": orientation_values.get(
            str(orientation), get_orientation_name(orientation)
        ),
    }


def draw_belt_path_preview(
    screen, placements, camera_x, camera_y, screen_width, screen_height, pixel_size
):
    """Draw semitransparent connected belt previews at their world positions."""
    for x, y, belt_type, orientation in placements:
        sx, sy = world_to_screen(
            x, y, camera_x, camera_y, screen_width, screen_height, pixel_size
        )
        ghost = pygame.Surface((pixel_size, pixel_size), pygame.SRCALPHA)
        draw_belt(ghost, belt_type, 0, 0, pixel_size, orientation)
        ghost.set_alpha(175)
        screen.blit(ghost, (sx, sy))
        pygame.draw.rect(
            screen, (110, 255, 110), (sx, sy, pixel_size, pixel_size), 1
        )

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
        if get_machine(machine_id) is None and get_belt_type(machine_id) is None:
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
        belt_type = get_belt_type(machine_id)
        if belt_type is not None:
            machine = get_belt(belt_type)

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
    # Conveyor variants are saved as machine IDs, but drawn from Belts.json.
    belt_type = get_belt_type(machine_id)
    if belt_type is not None:
        draw_belt(screen, belt_type, screen_x, screen_y, pixel_size, orientation)
        return True

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
