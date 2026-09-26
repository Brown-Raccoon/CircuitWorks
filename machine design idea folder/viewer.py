# viewer.py - Simplest marker system
# Miner SITS ON resource node, does NOT draw node
# Node is drawn by resource system, miner draws over it with open center
import pygame
import json
from pathlib import Path
import random

JSON_PATH = Path(__file__).with_name("Machines.json")

def load():
    with JSON_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)["miner"]

miner_data = load()
COLORS = {k: tuple(v) for k,v in miner_data["colors"].items()}
CALLS = sorted(miner_data["draw_calls"], key=lambda c: c.get("layer", 0))

def draw_miner_at_marker(screen, screen_x, screen_y, pixel_size):
    """Call this when tile (x,y) is marked as having miner. Sits ON node."""
    scale = pixel_size / 64
    def col(n):
        return COLORS.get(n, (255,0,255))
    for call in CALLS:
        func = call.get("func")
        c = col(call.get("color"))
        x, y = call.get("x", 0)*scale + screen_x, call.get("y", 0)*scale + screen_y
        if func == "rect":
            w, h = call.get("w",0)*scale, call.get("h",0)*scale
            r = pygame.Rect(x, y, w, h)
            rad = int(call.get("radius",0)*scale)
            pygame.draw.rect(screen, c, r, border_radius=rad)
            if call.get("outline"):
                oc = col(call["outline"])
                pygame.draw.rect(screen, oc, r, int(call.get("outline_width",1)*scale), border_radius=rad)
        elif func == "circle":
            r = call.get("r",0)*scale
            pygame.draw.circle(screen, c, (int(x), int(y)), int(r))
            if call.get("outline"):
                oc = col(call["outline"])
                pygame.draw.circle(screen, oc, (int(x), int(y)), int(r), int(call.get("outline_width",1)*scale))
        elif func == "ellipse":
            w, h = call.get("w",0)*scale, call.get("h",0)*scale
            if len(c)==4:
                s = pygame.Surface((int(w),int(h)), pygame.SRCALPHA)
                pygame.draw.ellipse(s, c, (0,0,w,h))
                screen.blit(s, (x-w/2, y-h/2))
            else:
                pygame.draw.ellipse(screen, c, (x-w/2, y-h/2, w, h))
        elif func == "line":
            x2 = call.get("x2",0)*scale + screen_x
            y2 = call.get("y2",0)*scale + screen_y
            pygame.draw.line(screen, c, (x,y), (x2,y2), max(1,int(call.get("width",1)*scale)))
        elif func == "polygon":
            pts = [(p[0]*scale+screen_x, p[1]*scale+screen_y) for p in call["points"]]
            pygame.draw.polygon(screen, c, pts)

# Demo
pygame.init()
TILE = 54
R = 3
W, H = 640, 640
screen = pygame.display.set_mode((W,H))
clock = pygame.time.Clock()
pygame.display.set_caption("miner sits ON node - click node | R reload | ESC")

random.seed(42)
nodes = {}
for _ in range(12):
    nodes[(random.randint(-R,R), random.randint(-R,R))] = True
placed = set()

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            if e.key == pygame.K_r:
                try:
                    miner_data = load()
                    COLORS = {k: tuple(v) for k,v in miner_data["colors"].items()}
                    CALLS = sorted(miner_data["draw_calls"], key=lambda c: c.get("layer",0))
                    print(f"Reloaded {len(CALLS)} calls")
                except Exception as ex:
                    print(ex)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button==1:
            mx,my = e.pos
            cx,cy = W//2, H//2
            wx = round((mx-cx)/TILE)
            wy = round((my-cy)/TILE)
            if (wx,wy) in nodes:
                if (wx,wy) in placed:
                    placed.remove((wx,wy))
                else:
                    placed.add((wx,wy))

    screen.fill((32,32,38))
    for x in range(-R,R+1):
        for y in range(-R,R+1):
            sx, sy = W//2 + x*TILE, H//2 + y*TILE
            pygame.draw.rect(screen, (60,60,68), (sx,sy,TILE,TILE), 1)
            if (x,y) in nodes:
                # Node drawn FIRST (by resource system)
                pygame.draw.circle(screen, (130,130,130), (sx+TILE//2, sy+TILE//2), 12)
                pygame.draw.circle(screen, (90,90,90), (sx+TILE//2, sy+TILE//2), 6)
            if (x,y) in placed:
                # Miner sits ON node - open center lets node show through
                draw_miner_at_marker(screen, sx, sy, TILE)

    font = pygame.font.SysFont("arial", 14)
    screen.blit(font.render("Click gray nodes to place miner - miner sits ON node, open pit shows node | R reload", True, (220,220,220)), (10,10))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
