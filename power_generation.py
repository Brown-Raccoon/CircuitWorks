import json
import math
from pathlib import Path
from collections import deque

# Files that hold machine power numbers
POWER_FILE = Path(__file__).with_name("MachinePower.json")
# Machines.json can also hold a power block per machine
MACHINES_FILE = Path(__file__).parent / "machine design idea folder" / "Machines.json"

# Tuning for the whole power system
TURBINE_VOLTAGE = 120.0
TURBINE_MAX_POWER = 600.0
WIRE_RESISTANCE_PER_TILE = 0.20
WIRE_MAX_LENGTH = 7
MIN_RUN_VOLTAGE = 90.0
MIN_OFF_VOLTAGE = 60.0
CABLE_ITEM_KEY = "power_cable"

# How close the mouse has to be to a wire to show its tooltip
HOVER_DIST = 8

# Load MachinePower.json once at startup
def _load_power_file():
    try:
        with POWER_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

MACHINE_POWER = _load_power_file()

# Load any power blocks from Machines.json
def _load_machines_power():
    try:
        with MACHINES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        out = {}
        for mid, mdata in data.items():
            if isinstance(mdata, dict) and "power" in mdata:
                out[mid] = mdata["power"]
        return out
    except Exception:
        return {}

MACHINES_POWER = _load_machines_power()

# ============================================================
# MACHINE OHMS - this is what the future interface will use
# ============================================================

# Get full power info for one machine_id - for interface / circuit panel
# Returns dict with ohms, watts, volts, type
# Checks Machines.json first, then MachinePower.json, then fallbacks
def get_machine_power_info(machine_id):
    # 1. Check Machines.json power block first
    if machine_id in MACHINES_POWER:
        info = MACHINES_POWER[machine_id]
        # Fill missing ohms from watts if needed
        if "ohms" not in info and "watts" in info and info["watts"] > 0:
            info = dict(info)
            # Ohms from watts: R = V^2 / P
            info["ohms"] = (TURBINE_VOLTAGE * TURBINE_VOLTAGE) / info["watts"]
        return info
    # 2. Check MachinePower.json
    if machine_id in MACHINE_POWER:
        return MACHINE_POWER[machine_id]
    # 3. Belt fallback - all conveyor_... are 5W / 2880 ohms
    if machine_id.startswith("conveyor"):
        return MACHINE_POWER.get("conveyor", {"type": "load", "rated_volts": 120, "watts": 5, "ohms": 2880})
    # 4. Unknown - default 50W
    return {"type": "load", "rated_volts": 120, "watts": 50, "ohms": 288}

# Get ohms for one machine_id - use this everywhere, never hardcode ohms
def get_machine_ohms(machine_id):
    info = get_machine_power_info(machine_id)
    # Source / passthrough have no load ohms
    if info.get("type") in ("source", "passthrough"):
        return None
    # Return ohms
    return info.get("ohms")

# Get watts for one machine_id
def get_machine_watts(machine_id):
    info = get_machine_power_info(machine_id)
    return info.get("watts", 0)

# ============================================================
# HELPERS - use machine_placement.py: placed_machines format
# placed_machines = {(x, y): {"machine_id": ..., "x": ..., "y": ...}}
# ============================================================

# Get the machine_id at a grid pos, or None if empty
def get_machine_id(placed_machines, pos):
    data = placed_machines.get(pos)
    if not isinstance(data, dict):
        return None
    return data.get("machine_id")

# True if there is any machine at this pos that can take a wire
def is_power_node(placed_machines, pos):
    return get_machine_id(placed_machines, pos) is not None

# True if the machine at pos is a wind turbine
def is_turbine(placed_machines, pos):
    mid = get_machine_id(placed_machines, pos)
    if mid is None:
        return False
    mid = mid.lower()
    return "turbine" in mid or "wind" in mid

# True if the machine at pos is a power pole
def is_pole(placed_machines, pos):
    mid = get_machine_id(placed_machines, pos)
    if mid is None:
        return False
    return "pole" in mid.lower()

# Get the load ohms for the machine at pos
def get_load_resistance(placed_machines, pos):
    mid = get_machine_id(placed_machines, pos)
    if mid is None:
        return None
    # Use ohms from MachinePower.json / Machines.json
    return get_machine_ohms(mid)

# Straight-line distance between two grid positions, in tiles
def wire_length(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])

# Wire resistance grows with length
def wire_resistance(a, b):
    return wire_length(a, b) * WIRE_RESISTANCE_PER_TILE

# Always store a wire the same way so (a,b) and (b,a) count as one wire
def normalize_wire(a, b):
    return (a, b) if a < b else (b, a)

# Try to add a wire, checking all the rules first
def try_connect_wire(start_pos, end_pos, placed_machines, power_wires, max_length=WIRE_MAX_LENGTH):
    if start_pos == end_pos:
        return False, "Cannot connect to itself"
    cable = normalize_wire(start_pos, end_pos)
    if cable in power_wires:
        return False, "Already connected"
    if not is_power_node(placed_machines, start_pos):
        return False, "No machine at start"
    if not is_power_node(placed_machines, end_pos):
        return False, "No machine at end"
    if max_length is not None and wire_length(start_pos, end_pos) > max_length:
        return False, f"Too far - max {max_length} tiles"
    power_wires.add(cable)
    return True, "Connected"

# Remove one wire between two positions
def remove_wire(start_pos, end_pos, power_wires):
    cable = normalize_wire(start_pos, end_pos)
    if cable not in power_wires:
        return False
    power_wires.remove(cable)
    return True

# Remove every wire touching this position, return how many were removed
def remove_all_wires_at(pos, power_wires):
    to_remove = [c for c in power_wires if c[0] == pos or c[1] == pos]
    for c in to_remove:
        power_wires.remove(c)
    return len(to_remove)

# Convert wires to a list that can be saved to JSON
def wires_to_save(power_wires):
    return [{"x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1]} for a, b in sorted(power_wires)]

# Convert saved wires back to a set
def wires_from_save(saved_list):
    wires = set()
    for w in saved_list or []:
        wires.add(normalize_wire((w["x1"], w["y1"]), (w["x2"], w["y2"])))
    return wires

# ============================================================
# OHM'S LAW SOLVER
# Wire: I = (V_a - V_b) / R_wire, V_drop = I * R
# Load: I = V / R_load, P = V * I
# ============================================================

# Solve A * x = b with Gaussian elimination
def solve_linear_system(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        # Pick the biggest pivot so small numbers do not blow up
        pivot = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[pivot][col]) < 1e-9:
            return [0.0] * n
        M[col], M[pivot] = M[pivot], M[col]
        # Eliminate this column from rows below
        for row in range(col + 1, n):
            factor = M[row][col] / M[col][col]
            for k in range(col, n + 1):
                M[row][k] -= factor * M[col][k]
    # Work backwards to get each voltage
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = sum(M[i][j] * x[j] for j in range(i + 1, n))
        x[i] = (M[i][n] - s) / M[i][i] if abs(M[i][i]) > 1e-9 else 0.0
    return x

# Run Ohm's law for the whole network and return volts / amps / watts per node and per wire
def calculate_power_network(placed_machines, power_wires):
    turbines = [pos for pos in placed_machines if is_turbine(placed_machines, pos)]
    # Build neighbour list for every wired machine
    adj = {}
    for a, b in power_wires:
        if a not in placed_machines or b not in placed_machines:
            continue
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    # Find every machine connected to a turbine through wires
    connected = set()
    queue = deque(turbines)
    connected.update(turbines)
    while queue:
        cur = queue.popleft()
        for nb in adj.get(cur, []):
            if nb not in connected:
                connected.add(nb)
                queue.append(nb)
    unknown_nodes = [pos for pos in connected if pos not in turbines]
    index = {pos: i for i, pos in enumerate(unknown_nodes)}
    n = len(unknown_nodes)
    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n
    # Build one equation per unknown node: current in = current out
    for pos in unknown_nodes:
        i = index[pos]
        r_load = get_load_resistance(placed_machines, pos)
        diag = (1.0 / r_load) if r_load else 0.0
        for nb in adj.get(pos, []):
            r_wire = wire_resistance(pos, nb)
            if r_wire < 1e-6:
                r_wire = 1e-6
            g = 1.0 / r_wire
            diag += g
            if nb in index:
                A[i][index[nb]] -= g
            elif nb in turbines:
                b[i] += g * TURBINE_VOLTAGE
        A[i][i] = diag
    voltages = {t: TURBINE_VOLTAGE for t in turbines}
    if n > 0:
        solved = solve_linear_system(A, b)
        for pos, v in zip(unknown_nodes, solved):
            voltages[pos] = v
    for pos in placed_machines:
        if pos not in voltages:
            voltages[pos] = 0.0

    # Per-node results - includes ohms for interface
    nodes = {}
    for pos in placed_machines:
        v = voltages.get(pos, 0.0)
        mid = get_machine_id(placed_machines, pos)
        info = get_machine_power_info(mid) if mid else {}
        ohms = info.get("ohms")
        if is_turbine(placed_machines, pos):
            nodes[pos] = {"machine_id": mid, "volts": v, "amps": 0.0, "watts": 0.0, "ohms": ohms, "rated_watts": 0.0, "status": "SOURCE", "connected": pos in connected, "power_info": info}
        elif is_pole(placed_machines, pos):
            nodes[pos] = {"machine_id": mid, "volts": v, "amps": 0.0, "watts": 0.0, "ohms": ohms, "rated_watts": 0.0, "status": "POLE", "connected": pos in connected, "power_info": info}
        else:
            # Load machine: amps and watts from its volts and ohms
            r_load = get_load_resistance(placed_machines, pos)
            amps = (v / r_load) if r_load else 0.0
            watts = v * amps
            rated = info.get("watts", 0)
            if pos not in connected:
                status = "NO_POWER"
            elif v >= MIN_RUN_VOLTAGE:
                status = "ON"
            elif v >= MIN_OFF_VOLTAGE:
                status = "UNDERPOWERED"
            else:
                status = "OFF"
            nodes[pos] = {"machine_id": mid, "volts": v, "amps": amps, "watts": watts, "ohms": ohms, "rated_watts": rated, "status": status, "connected": pos in connected, "power_info": info}

    # Per-wire results: voltage drop, current, and power lost as heat
    wires = []
    for a, b in sorted(power_wires):
        if a not in placed_machines or b not in placed_machines:
            continue
        r = wire_resistance(a, b)
        v_a = voltages.get(a, 0.0)
        v_b = voltages.get(b, 0.0)
        v_drop = abs(v_a - v_b)
        amps = (v_drop / r) if r > 1e-6 else 0.0
        loss = (amps * amps) * r
        wires.append({"a": a, "b": b, "length_tiles": wire_length(a, b), "resistance_ohms": r, "volts_a": v_a, "volts_b": v_b, "volts_drop": v_drop, "amps": amps, "power_loss_watts": loss})

    # Total power made by turbines, from the current leaving each turbine
    total_generated = 0.0
    total_loss = sum(w["power_loss_watts"] for w in wires)
    for t in turbines:
        t_current = 0.0
        for w in wires:
            if w["a"] == t:
                t_current += w["amps"] if w["volts_a"] >= w["volts_b"] else -w["amps"]
            elif w["b"] == t:
                t_current += w["amps"] if w["volts_b"] >= w["volts_a"] else -w["amps"]
        t_power = TURBINE_VOLTAGE * max(0.0, t_current)
        nodes[t]["amps"] = t_current
        nodes[t]["watts"] = t_power
        nodes[t]["status"] = "OVERLOADED" if t_power > TURBINE_MAX_POWER else "SOURCE"
        total_generated += t_power
    total_consumed = sum(n["watts"] for n in nodes.values() if n["status"] in ("ON", "UNDERPOWERED", "OFF"))

    return {"source_volts": TURBINE_VOLTAGE, "nodes": nodes, "wires": wires, "total_generated_watts": total_generated, "total_consumed_watts": total_consumed, "total_loss_watts": total_loss, "turbines": turbines}

# ============================================================
# WIRE TOOL - logic only, no button drawing here
# Button lives in inventory_ui.py: handle_click()
# This tool is started from world_generation.py after inventory returns power_cable
# ============================================================

# Tracks wire mode: off, one endpoint picked, or connecting
class PowerWireTool:
    def __init__(self):
        self.active = False
        self.selected_pos = None
        self.wires = set()

    # Start wire mode - call after inventory_ui.py returns power_cable
    def start(self, player_inventory):
        if player_inventory is None:
            self.active = True
            self.selected_pos = None
            return True
        if player_inventory.get_quantity(CABLE_ITEM_KEY) < 1:
            return False
        self.active = True
        self.selected_pos = None
        return True

    # Exit wire mode and clear any picked endpoint
    def cancel(self):
        self.active = False
        self.selected_pos = None

    # ESC - call this from world_generation.py on K_ESCAPE
    # First ESC cancels just the first click, second ESC exits wire mode
    def handle_escape(self):
        if self.selected_pos is not None:
            self.selected_pos = None
            return "cancelled_selection"
        if self.active:
            self.cancel()
            return "exited"
        return None

    # Handle one click - grid_pos from machine_placement.py: screen_to_world()
    # Access inventory.py: player_inventory.remove_item() to consume 1 cable
    # Left click picks first machine, then second machine to connect
    # Right click cancels pick, or exits wire mode if nothing picked
    def handle_click(self, grid_pos, placed_machines, player_inventory=None, button=1):
        if not self.active:
            return (None, None)
        # Right-click - this is the fix
        if button == 3:
            # If you already picked a first machine, just cancel that pick
            if self.selected_pos is not None:
                self.selected_pos = None
                return ("cancelled_selection", None)
            # If no pick yet, exit wire mode completely
            self.cancel()
            return ("exited", None)
        if button != 1:
            return (None, None)
        if not is_power_node(placed_machines, grid_pos):
            self.selected_pos = None
            return ("cancelled_selection", None)
        if self.selected_pos is None:
            self.selected_pos = grid_pos
            return ("selected", grid_pos)
        if grid_pos == self.selected_pos:
            self.selected_pos = None
            return ("cancelled_selection", None)
        # Second click: try to connect, then spend 1 cable if it worked
        start = self.selected_pos
        success, msg = try_connect_wire(start, grid_pos, placed_machines, self.wires)
        self.selected_pos = None
        if not success:
            return ("failed", msg)
        if player_inventory is not None:
            removed = player_inventory.remove_item(CABLE_ITEM_KEY, 1)
            if not removed:
                remove_wire(start, grid_pos, self.wires)
                self.cancel()
                return ("failed", "No cable in inventory")
            if player_inventory.get_quantity(CABLE_ITEM_KEY) < 1:
                self.cancel()
                return ("connected_out", normalize_wire(start, grid_pos))
        return ("connected", normalize_wire(start, grid_pos))

# Drawing - use machine_placement.py: world_to_screen() math
# Convert grid pos to screen pixels using camera and screen centre
def world_to_screen(grid_x, grid_y, camera_x, camera_y, screen_width, screen_height, pixel_size):
    sx = screen_width // 2 + (grid_x - camera_x) * pixel_size
    sy = screen_height // 2 + (grid_y - camera_y) * pixel_size
    return int(sx), int(sy)

# Distance from a point to a line segment - for wire hover
def _point_to_segment_dist(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5

# Draw a small dark box next to the mouse with info lines
def _draw_tooltip(screen, mouse_x, mouse_y, lines, font):
    # Small dark box next to mouse, not in the middle of the wire
    import pygame
    line_height = 15
    padding_x = 8
    padding_y = 6
    width = 0
    rendered = []
    for text, color, bold in lines:
        f = pygame.font.SysFont("arial", 12, bold=bold)
        surf = f.render(text, True, color)
        rendered.append(surf)
        width = max(width, surf.get_width())
    height = len(rendered) * line_height + padding_y * 2
    # Keep tooltip on screen
    box_x = mouse_x + 14
    box_y = mouse_y + 14
    if box_x + width + padding_x * 2 > screen.get_width():
        box_x = mouse_x - width - padding_x * 2 - 14
    if box_y + height > screen.get_height():
        box_y = mouse_y - height - 14
    bg = pygame.Surface((width + padding_x * 2, height), pygame.SRCALPHA)
    bg.fill((15, 15, 18, 215))
    screen.blit(bg, (box_x, box_y))
    pygame.draw.rect(screen, (90, 90, 100), (box_x, box_y, width + padding_x * 2, height), 1, border_radius=5)
    for i, surf in enumerate(rendered):
        screen.blit(surf, (box_x + padding_x, box_y + padding_y + i * line_height))

# Draw all wires + hover tooltips. Machine hover beats wire hover.
def draw_power_wires(screen, power_wires, placed_machines, power_result, camera_x, camera_y, screen_width, screen_height, pixel_size, font=None, mouse_pos=None):
    import pygame
    wire_info = {}
    if power_result:
        for w in power_result.get("wires", []):
            wire_info[normalize_wire(w["a"], w["b"])] = w
    nodes = power_result.get("nodes", {}) if power_result else {}

    # 1. Machine hover has priority - check ANY machine first
    hovered_machine = None
    if mouse_pos is not None:
        mx, my = mouse_pos
        for pos in placed_machines:
            sx, sy = world_to_screen(pos[0], pos[1], camera_x, camera_y, screen_width, screen_height, pixel_size)
            if sx <= mx < sx + pixel_size and sy <= my < sy + pixel_size:
                hovered_machine = pos
                break

    # 2. Draw wires - thin, muted
    for a, b in sorted(power_wires):
        if a not in placed_machines or b not in placed_machines:
            continue
        ax, ay = world_to_screen(a[0], a[1], camera_x, camera_y, screen_width, screen_height, pixel_size)
        bx, by = world_to_screen(b[0], b[1], camera_x, camera_y, screen_width, screen_height, pixel_size)
        ax += pixel_size // 2
        ay += pixel_size // 2
        bx += pixel_size // 2
        by += pixel_size // 2
        info = wire_info.get(normalize_wire(a, b))
        color = (110, 200, 130) if info and info["amps"] > 0.01 else (110, 110, 115)
        pygame.draw.line(screen, (30, 45, 35), (ax, ay), (bx, by), 3)
        pygame.draw.line(screen, color, (ax, ay), (bx, by), 1)
        pygame.draw.circle(screen, (25, 25, 25), (ax, ay), 3)
        pygame.draw.circle(screen, color, (ax, ay), 2)
        pygame.draw.circle(screen, (25, 25, 25), (bx, by), 3)
        pygame.draw.circle(screen, color, (bx, by), 2)

        # Only show wire tooltip if NOT hovering a machine
        if hovered_machine is None and mouse_pos is not None and info is not None:
            dist = _point_to_segment_dist(mouse_pos[0], mouse_pos[1], ax, ay, bx, by)
            if dist <= HOVER_DIST:
                lines = [
                    (f"{info['volts_a']:.1f}V  ->  {info['volts_b']:.1f}V", (255, 255, 255), True),
                    (f"drop {info['volts_drop']:.2f}V  |  {info['amps']:.2f}A  |  R {info['resistance_ohms']:.2f} ohm", (180, 200, 180), False),
                ]
                _draw_tooltip(screen, mouse_pos[0], mouse_pos[1], lines, font)

    # 3. If hovering a machine, show ONLY machine tooltip
    if hovered_machine is not None:
        mx, my = mouse_pos
        node = nodes.get(hovered_machine, {})
        mid = get_machine_id(placed_machines, hovered_machine) or "machine"
        title = mid.replace("_", " ").title()
        volts = node.get("volts", 0.0)
        amps = node.get("amps", 0.0)
        watts = node.get("watts", 0.0)
        ohms = node.get("ohms")
        status = node.get("status", "")
        info = node.get("power_info", {})

        if is_turbine(placed_machines, hovered_machine):
            lines = [
                ("Wind Turbine", (255, 255, 255), True),
                (f"{volts:.1f}V  |  {watts:.0f}W generated", (180, 200, 180), False),
                (f"{status}", (160, 160, 170), False),
            ]
        elif is_pole(placed_machines, hovered_machine):
            connected = sum(1 for w in power_wires if hovered_machine in w)
            contact = info.get("contact_ohms", 0.05)
            lines = [
                ("Power Pole", (255, 255, 255), True),
                (f"{volts:.1f}V  |  {connected} wire(s)", (180, 200, 180), False),
                (f"R {contact:.2f} ohm contact", (160, 160, 170), False),
            ]
        else:
            # Any other machine - miner, smelter, etc.
            ohms_text = f"R {ohms:.0f} ohm" if ohms is not None else "R -"
            lines = [
                (title, (255, 255, 255), True),
                (f"{volts:.1f}V  |  {amps:.2f}A  |  {watts:.0f}W", (180, 200, 180), False),
                (f"{ohms_text}  |  {status}", (160, 160, 170), False),
            ]
        _draw_tooltip(screen, mx, my, lines, font)

# Draw yellow box on the picked start machine while placing a wire
def draw_wire_selection(screen, selected_pos, camera_x, camera_y, screen_width, screen_height, pixel_size):
    import pygame
    if selected_pos is None:
        return
    sx, sy = world_to_screen(selected_pos[0], selected_pos[1], camera_x, camera_y, screen_width, screen_height, pixel_size)
    pygame.draw.rect(screen, (255, 255, 100), (sx, sy, pixel_size, pixel_size), 3)