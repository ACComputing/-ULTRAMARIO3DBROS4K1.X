"""
Super Mario 64 Pygame Port – Expanded Peach's Castle
----------------------------------------------------
Features:
- Detailed castle hub with exterior (moat, bridge, courtyard) and interior (main hall,
  upper floors, library, tower).
- Secret stars hidden in the castle.
- Five classic courses accessible via paintings.
- Star and coin collection, portal system, camera follow.
"""

import pygame
import math
import sys
from random import randint

# ============================================================
# CONFIG
# ============================================================

WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 500
VIEW_DISTANCE = 5000

MOVE_SPEED = 12
JUMP_FORCE = 18
GRAVITY = 0.9

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SM64 PY PORT – EXPANDED CASTLE")
clock = pygame.time.Clock()

# ============================================================
# COLORS
# ============================================================

DD_SKY = (20, 20, 60)
INDOOR_SKY = (12, 10, 18)

WHITE = (255, 255, 255)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)
GOLD = (255, 200, 0)
BLUE = (0, 0, 205)
BROWN = (139, 69, 19)
GREEN = (30, 140, 30)
LIGHT_GREEN = (50, 200, 50)
STONE_GRAY = (120, 120, 120)
WATER_BLUE = (64, 164, 223)
LAVA_ORANGE = (255, 100, 0)
SNOW_WHITE = (240, 240, 255)
DARK_BROWN = (101, 67, 33)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

PARCHMENT = (245, 235, 205)
PARCHMENT_BORDER = (190, 150, 100)
INK = (70, 40, 25)

# ============================================================
# 3D CORE CLASSES
# ============================================================

class Vec3:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

class Face:
    def __init__(self, idx, col):
        self.idx = idx
        self.col = col

class Mesh:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z
        self.yaw = 0
        self.verts = []
        self.faces = []

    def cube(self, w, h, d, ox, oy, oz, col):
        """Add a cube centered at (ox, oy, oz) relative to the mesh's origin."""
        s = len(self.verts)
        hw, hh, hd = w/2, h/2, d/2
        pts = [(-hw, -hh, -hd), ( hw, -hh, -hd), ( hw,  hh, -hd), (-hw,  hh, -hd),
               (-hw, -hh,  hd), ( hw, -hh,  hd), ( hw,  hh,  hd), (-hw,  hh,  hd)]
        for px, py, pz in pts:
            self.verts.append(Vec3(px + ox, py + oy, pz + oz))

        faces = [[0,1,2,3], [5,4,7,6], [4,0,3,7],
                 [1,5,6,2], [3,2,6,7], [4,5,1,0]]
        for f in faces:
            self.faces.append(Face([i + s for i in f], col))

def render(mesh, cam, polys):
    """Collect visible polygons from mesh, transformed and projected."""
    cy = math.cos(mesh.yaw)
    sy = math.sin(mesh.yaw)

    for face in mesh.faces:
        pts = []
        avgz = 0
        for i in face.idx:
            v = mesh.verts[i]
            # rotate around Y
            rx = v.x * cy - v.z * sy
            rz = v.x * sy + v.z * cy
            ry = v.y

            # translate to world
            wx = rx + mesh.x - cam["x"]
            wy = ry + mesh.y - cam["y"]
            wz = rz + mesh.z - cam["z"]

            if wz <= 1:
                break   # behind camera

            scale = FOV / wz
            sx = wx * scale + WIDTH // 2
            syy = -wy * scale + HEIGHT // 2
            pts.append((sx, syy))
            avgz += wz
        else:
            avgz /= len(pts)
            polys.append((avgz, pts, face.col))

# ============================================================
# GAME OBJECTS
# ============================================================

class Mario(Mesh):
    def __init__(self):
        super().__init__(0, 0, 400)
        self.dy = 0
        self.health = 100
        self.coins = 0
        self.stars = 0
        self.cube(30, 40, 20, 0, 20, 0, RED)

    def update(self):
        self.dy -= GRAVITY
        self.y += self.dy
        if self.y < 0:
            self.y = 0
            self.dy = 0

    def jump(self):
        if self.y == 0:
            self.dy = JUMP_FORCE

class Coin(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.cube(20, 5, 20, 0, 0, 0, YELLOW)

class Star(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.cube(15, 15, 15, 0, 7.5, 0, GOLD)

# ============================================================
# LEVEL CLASS
# ============================================================

class Level:
    def __init__(self, name, terrain, stars, coins, entry_point=(0,0,400)):
        self.name = name
        self.terrain = terrain
        self.stars = stars
        self.coins = coins
        self.entry_point = entry_point
        self.portals = []

    def add_portal(self, x1, x2, z1, z2, target_level, spawn):
        self.portals.append({
            "rect": (x1, x2, z1, z2),
            "target": target_level,
            "spawn": spawn
        })

# ============================================================
# ENHANCED CASTLE BUILDER
# ============================================================

def make_castle():
    """Build a more detailed Peach's Castle with exterior and interior."""
    terrain = Mesh()

    # --- EXTERIOR GROUND (grass) ---
    terrain.cube(2000, 10, 2000, 0, -5, 0, LIGHT_GREEN)   # large grass plane

    # --- MOAT (water around the castle) ---
    # Using four long cubes to form a rectangular moat
    moat_y = -3
    terrain.cube(1400, 5, 200, 0, moat_y, -650, WATER_BLUE)   # front
    terrain.cube(1400, 5, 200, 0, moat_y, 650, WATER_BLUE)    # back
    terrain.cube(200, 5, 1400, -650, moat_y, 0, WATER_BLUE)   # left
    terrain.cube(200, 5, 1400, 650, moat_y, 0, WATER_BLUE)    # right

    # --- BRIDGE (wooden planks) over front moat ---
    terrain.cube(200, 10, 80, 0, 5, -600, DARK_BROWN)   # bridge deck
    terrain.cube(20, 40, 20, -90, 20, -600, DARK_BROWN) # left pillar
    terrain.cube(20, 40, 20, 90, 20, -600, DARK_BROWN)  # right pillar

    # --- CASTLE OUTER WALLS (stone) ---
    # Front wall (with opening for bridge)
    terrain.cube(800, 150, 50, 0, 75, -400, STONE_GRAY)  # main front wall
    # Gap for bridge entrance – we'll add side walls later

    # Left and right wings
    terrain.cube(200, 200, 600, -400, 100, 0, STONE_GRAY)
    terrain.cube(200, 200, 600, 400, 100, 0, STONE_GRAY)

    # Back wall
    terrain.cube(800, 200, 50, 0, 100, 400, STONE_GRAY)

    # --- MAIN CASTLE BUILDING (central keep) ---
    # Base
    terrain.cube(500, 150, 500, 0, 75, 0, (210, 180, 140))  # beige stone
    # Towers on corners (simplified)
    for dx, dz in [(-200, -200), (200, -200), (-200, 200), (200, 200)]:
        terrain.cube(100, 250, 100, dx, 125, dz, STONE_GRAY)

    # --- INTERIOR: MAIN HALL (hollow space) ---
    # Floor (inside)
    terrain.cube(400, 10, 400, 0, 10, 0, (150, 150, 150))
    # Walls (thin cubes around the inside perimeter)
    # These will be added after we create the hollow space; for simplicity we'll
    # add them as separate meshes later? Actually, we need a way to have empty space.
    # In this simple engine, we just place walls where they should be.
    # Let's add interior walls as separate cubes to define rooms.

    # Main hall walls (stone)
    terrain.cube(20, 150, 400, -200, 85, 0, STONE_GRAY)   # left wall
    terrain.cube(20, 150, 400, 200, 85, 0, STONE_GRAY)    # right wall
    terrain.cube(400, 150, 20, 0, 85, -200, STONE_GRAY)   # back wall (towards entrance)
    terrain.cube(400, 150, 20, 0, 85, 200, STONE_GRAY)    # front wall (towards staircase)

    # Grand staircase (steps) leading up
    for i in range(5):
        step_y = 15 + i*20
        terrain.cube(300, 10, 50, 0, step_y, 150 + i*30, (200,180,150))

    # Upper floor (above main hall)
    terrain.cube(300, 10, 300, 0, 150, 50, (150,150,150))  # upper floor platform

    # Upper hallways
    terrain.cube(20, 100, 200, -150, 200, 50, STONE_GRAY)  # left hallway wall
    terrain.cube(20, 100, 200, 150, 200, 50, STONE_GRAY)   # right hallway wall

    # Library (room on left side)
    terrain.cube(150, 100, 150, -300, 70, -100, (139,69,19))  # bookshelves (brown)
    terrain.cube(150, 100, 150, -300, 70, 100, (139,69,19))

    # Tower (cylindrical look using stacked cubes)
    for y in range(0, 300, 40):
        terrain.cube(80, 40, 80, 300, 20 + y, -200, (180,160,130))

    # --- PAINTINGS (portals to courses) ---
    # Back wall of main hall
    terrain.cube(120, 100, 10, -120, 90, -195, GREEN)      # Bob-omb
    terrain.cube(120, 100, 10, 120, 90, -195, WATER_BLUE)  # Jolly Roger
    # Side walls
    terrain.cube(10, 100, 120, -195, 90, -100, STONE_GRAY) # Whomp's (gray)
    terrain.cube(10, 100, 120, -195, 90, 100, SNOW_WHITE)  # Cool Cool
    terrain.cube(10, 100, 120, 195, 90, 0, LAVA_ORANGE)    # Lethal Lava

    # --- CASTLE ROOF (simple pyramid) ---
    # Using multiple cubes to simulate a sloped roof
    for i in range(1, 6):
        size = 500 - i*40
        y = 150 + i*20
        terrain.cube(size, 10, size, 0, y, 0, (150,0,0))  # red roof tiles

    # --- SECRET STARS hidden in the castle ---
    stars = [
        Star(300, 280, -200),   # top of tower
        Star(0, 50, -550),      # under bridge (in moat) – need to jump?
        Star(-300, 90, -100),   # library
        Star(150, 220, 50),     # upper hallway
        Star(-150, 40, 150),    # behind a painting? We'll just place it.
    ]

    # Coins scattered around
    coins = [Coin(randint(-400,400), 20, randint(-400,400)) for _ in range(15)]

    level = Level("Peach's Castle", terrain, stars, coins, entry_point=(0, 0, 400))

    # --- PORTALS (painting areas) to courses ---
    # Bob-omb Battlefield (green painting)
    level.add_portal(-180, -60, -200, -190, "Bob-omb Battlefield", (0, 0, 200))
    # Jolly Roger Bay (blue painting)
    level.add_portal(60, 180, -200, -190, "Jolly Roger Bay", (0, 0, 300))
    # Whomp's Fortress (gray painting on left wall)
    level.add_portal(-200, -190, -160, -40, "Whomp's Fortress", (0, 0, 300))
    # Cool Cool Mountain (white painting)
    level.add_portal(-200, -190, 40, 160, "Cool Cool Mountain", (0, 0, 400))
    # Lethal Lava Land (orange painting on right wall)
    level.add_portal(190, 200, -60, 60, "Lethal Lava Land", (0, 0, 400))

    return level

# ============================================================
# COURSE BUILDERS (unchanged from previous version)
# ============================================================

def make_bobomb_battlefield():
    terrain = Mesh()
    terrain.cube(2000, 20, 2000, 0, -10, 0, LIGHT_GREEN)
    terrain.cube(400, 200, 400, 0, 100, 0, BROWN)
    terrain.cube(300, 100, 300, 0, 200, 0, BROWN)
    terrain.cube(200, 100, 200, 0, 300, 0, BROWN)
    terrain.cube(100, 20, 300, 300, 50, -200, DARK_BROWN)
    terrain.cube(100, 20, 300, 300, 50, 200, DARK_BROWN)
    terrain.cube(150, 20, 150, -200, 150, 300, (200, 180, 150))

    stars = [
        Star(0, 350, 0), Star(300, 80, -200), Star(-200, 180, 300),
        Star(500, 50, 500), Star(-400, 30, -400), Star(200, 20, -600)
    ]
    coins = [Coin(randint(-800,800), 20, randint(-800,800)) for _ in range(8)]
    level = Level("Bob-omb Battlefield", terrain, stars, coins, entry_point=(0, 0, 400))
    level.add_portal(-100, 100, 350, 400, "Peach's Castle", (0, 0, 400))
    return level

def make_whomps_fortress():
    terrain = Mesh()
    terrain.cube(1500, 20, 1500, 0, -10, 0, STONE_GRAY)
    terrain.cube(300, 200, 300, 0, 100, 0, (150,140,130))
    terrain.cube(250, 150, 250, 0, 200, 0, (140,130,120))
    terrain.cube(200, 100, 200, 0, 300, 0, (130,120,110))
    for x in (-400, 400):
        terrain.cube(50, 100, 800, x, 50, 0, STONE_GRAY)
    for z in (-400, 400):
        terrain.cube(800, 100, 50, 0, 50, z, STONE_GRAY)
    terrain.cube(150, 20, 150, 300, 80, 300, (200,180,150))
    terrain.cube(150, 20, 150, -300, 80, -300, (200,180,150))

    stars = [
        Star(0, 350, 0), Star(300, 100, 300), Star(-300, 100, -300),
        Star(400, 30, 0), Star(-400, 30, 0), Star(0, 30, 400)
    ]
    coins = [Coin(randint(-600,600), 20, randint(-600,600)) for _ in range(6)]
    level = Level("Whomp's Fortress", terrain, stars, coins, entry_point=(0, 0, 300))
    level.add_portal(-100, 100, 250, 300, "Peach's Castle", (0, 0, 400))
    return level

def make_jolly_roger_bay():
    terrain = Mesh()
    terrain.cube(1500, 5, 1500, 0, -5, 0, WATER_BLUE)
    terrain.cube(300, 100, 100, -100, 30, -100, DARK_BROWN)
    terrain.cube(150, 50, 150, 50, 80, 0, (210,180,140))
    terrain.cube(800, 200, 50, 0, 100, -500, STONE_GRAY)
    terrain.cube(50, 200, 800, -500, 100, 0, STONE_GRAY)
    terrain.cube(50, 200, 800, 500, 100, 0, STONE_GRAY)
    terrain.cube(200, 20, 200, 300, 30, 300, (200,180,150))

    stars = [
        Star(-100, 80, -100), Star(300, 50, 300), Star(0, 20, -400),
        Star(-400, 20, 0), Star(400, 20, 0), Star(0, 20, 400)
    ]
    coins = [Coin(randint(-600,600), 10, randint(-600,600)) for _ in range(8)]
    level = Level("Jolly Roger Bay", terrain, stars, coins, entry_point=(0, 0, 300))
    level.add_portal(-100, 100, 250, 300, "Peach's Castle", (0, 0, 400))
    return level

def make_cool_cool_mountain():
    terrain = Mesh()
    terrain.cube(1500, 20, 1500, 0, -10, 0, SNOW_WHITE)
    terrain.cube(400, 80, 400, -200, 40, -200, (220,220,240))
    terrain.cube(300, 80, 300, -250, 100, -250, (240,240,255))
    terrain.cube(200, 80, 200, -300, 160, -300, WHITE)
    terrain.cube(200, 10, 800, 200, 30, 0, (200,220,255))
    terrain.cube(150, 100, 150, 400, 50, 300, WHITE)
    terrain.cube(120, 80, 120, 400, 100, 300, WHITE)

    stars = [
        Star(-300, 200, -300), Star(200, 50, 0), Star(400, 120, 300),
        Star(-400, 30, 400), Star(0, 30, -500), Star(500, 30, -200)
    ]
    coins = [Coin(randint(-600,600), 20, randint(-600,600)) for _ in range(6)]
    level = Level("Cool Cool Mountain", terrain, stars, coins, entry_point=(0, 0, 400))
    level.add_portal(-100, 100, 350, 400, "Peach's Castle", (0, 0, 400))
    return level

def make_lethal_lava_land():
    terrain = Mesh()
    terrain.cube(1500, 5, 1500, 0, -5, 0, LAVA_ORANGE)
    terrain.cube(400, 150, 400, 0, 75, 0, (100,50,20))
    terrain.cube(300, 100, 300, 0, 150, 0, (120,60,30))
    terrain.cube(200, 80, 200, 0, 220, 0, (140,70,40))
    terrain.cube(200, 30, 200, 400, 15, 400, STONE_GRAY)
    terrain.cube(200, 30, 200, -400, 15, -400, STONE_GRAY)
    terrain.cube(200, 30, 200, 400, 15, -400, STONE_GRAY)
    terrain.cube(200, 30, 200, -400, 15, 400, STONE_GRAY)

    stars = [
        Star(0, 260, 0), Star(400, 45, 400), Star(-400, 45, -400),
        Star(400, 45, -400), Star(-400, 45, 400), Star(200, 30, 200)
    ]
    coins = [Coin(randint(-600,600), 10, randint(-600,600)) for _ in range(8)]
    level = Level("Lethal Lava Land", terrain, stars, coins, entry_point=(0, 0, 400))
    level.add_portal(-100, 100, 350, 400, "Peach's Castle", (0, 0, 400))
    return level

# ============================================================
# UI: Dear Mario card
# ============================================================

def dear_card():
    title = pygame.font.SysFont("Times New Roman", 34, bold=True)
    body = pygame.font.SysFont("Times New Roman", 26)

    fade = 0
    while True:
        dt = clock.tick(FPS)
        fade = min(255, fade + dt * 0.7)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return

        screen.fill(DD_SKY)

        card = pygame.Surface((560, 360), pygame.SRCALPHA)
        card.fill(PARCHMENT)
        pygame.draw.rect(card, PARCHMENT_BORDER, card.get_rect(), 6)

        card.blit(title.render("Dear Mario,", True, INK), (40, 40))
        card.blit(body.render("You're invited to Peach's Castle.", True, INK), (40, 100))
        card.blit(body.render("Please come right away!", True, INK), (40, 140))

        card.set_alpha(fade)
        screen.blit(card, (120, 120))
        pygame.display.flip()

# ============================================================
# MENU
# ============================================================

def menu():
    font = pygame.font.SysFont("Arial", 40, bold=True)
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return
        screen.fill(DD_SKY)
        screen.blit(font.render("PRESS START", True, WHITE), (260, 260))
        pygame.display.flip()

# ============================================================
# GAME LOOP
# ============================================================

def game():
    # Build all levels
    levels = {
        "Peach's Castle": make_castle(),
        "Bob-omb Battlefield": make_bobomb_battlefield(),
        "Whomp's Fortress": make_whomps_fortress(),
        "Jolly Roger Bay": make_jolly_roger_bay(),
        "Cool Cool Mountain": make_cool_cool_mountain(),
        "Lethal Lava Land": make_lethal_lava_land(),
    }

    current_level = levels["Peach's Castle"]
    mario = Mario()
    mario.x, mario.y, mario.z = current_level.entry_point

    cam = {"x": mario.x, "y": mario.y + 200, "z": mario.z + 400}

    font = pygame.font.SysFont("Arial", 24)

    running = True
    while running:
        clock.tick(FPS)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    mario.jump()
                if e.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: mario.z -= MOVE_SPEED
        if keys[pygame.K_s]: mario.z += MOVE_SPEED
        if keys[pygame.K_a]: mario.x -= MOVE_SPEED
        if keys[pygame.K_d]: mario.x += MOVE_SPEED

        mario.update()

        # Collectibles
        for coin in current_level.coins[:]:
            if math.dist((mario.x, mario.z), (coin.x, coin.z)) < 40 and abs(mario.y - coin.y) < 40:
                current_level.coins.remove(coin)
                mario.coins += 1
        for star in current_level.stars[:]:
            if math.dist((mario.x, mario.z), (star.x, star.z)) < 40 and abs(mario.y - star.y) < 40:
                current_level.stars.remove(star)
                mario.stars += 1

        # Portal checks
        for portal in current_level.portals:
            x1, x2, z1, z2 = portal["rect"]
            if x1 <= mario.x <= x2 and z1 <= mario.z <= z2:
                target = levels[portal["target"]]
                current_level = target
                mario.x, mario.y, mario.z = portal["spawn"]
                break

        # Camera follow
        cam["x"] = mario.x
        cam["y"] = mario.y + 200
        cam["z"] = mario.z + 400

        # Sky color based on level
        if "Lava" in current_level.name:
            sky = (80, 20, 20)
        elif "Bay" in current_level.name:
            sky = (100, 150, 200)
        elif "Mountain" in current_level.name:
            sky = (200, 220, 240)
        elif "Castle" in current_level.name:
            sky = DD_SKY
        else:
            sky = INDOOR_SKY

        screen.fill(sky)

        polys = []
        render(current_level.terrain, cam, polys)
        render(mario, cam, polys)
        for coin in current_level.coins:
            render(coin, cam, polys)
        for star in current_level.stars:
            render(star, cam, polys)

        polys.sort(reverse=True)
        for _, pts, col in polys:
            if len(pts) == 4:
                pygame.draw.polygon(screen, col, pts)

        # HUD
        hud_text = font.render(f"Stars: {mario.stars}   Coins: {mario.coins}", True, WHITE)
        screen.blit(hud_text, (20, 20))
        level_name = font.render(current_level.name, True, WHITE)
        screen.blit(level_name, (20, 50))

        pygame.display.flip()

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    while True:
        menu()
        dear_card()
        game()
