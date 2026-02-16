"""
Super Mario 64 Pygame Port – FULL MAP EDITION
----------------------------------------------
All 15 courses, 3 Bowser stages, secret areas,
expanded Peach's Castle hub with floor-based portals.
Team Flames / CatSDK
"""

import pygame
import math
import sys
from random import randint, seed

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
pygame.display.set_caption("SM64 PY PORT – ALL MAPS")
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
SAND_YELLOW = (210, 180, 80)
DARK_WATER = (20, 60, 120)
CLOCK_BRONZE = (180, 140, 60)
RAINBOW = (255, 120, 200)
GHOST_GREEN = (80, 200, 80)
CAVE_GRAY = (80, 80, 90)
TOXIC_GREEN = (40, 180, 40)
DARK_PURPLE = (60, 20, 80)
ICE_BLUE = (180, 220, 255)
DEEP_BLUE = (10, 30, 80)

PARCHMENT = (245, 235, 205)
PARCHMENT_BORDER = (190, 150, 100)
INK = (70, 40, 25)

# ============================================================
# 3D CORE CLASSES
# ============================================================

class Vec3:
    __slots__ = ("x", "y", "z")
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

class Face:
    __slots__ = ("idx", "col")
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
        s = len(self.verts)
        hw, hh, hd = w / 2, h / 2, d / 2
        pts = [
            (-hw, -hh, -hd), (hw, -hh, -hd), (hw, hh, -hd), (-hw, hh, -hd),
            (-hw, -hh, hd), (hw, -hh, hd), (hw, hh, hd), (-hw, hh, hd),
        ]
        for px, py, pz in pts:
            self.verts.append(Vec3(px + ox, py + oy, pz + oz))
        for f in [
            [0, 1, 2, 3], [5, 4, 7, 6], [4, 0, 3, 7],
            [1, 5, 6, 2], [3, 2, 6, 7], [4, 5, 1, 0],
        ]:
            self.faces.append(Face([i + s for i in f], col))

    def wedge(self, w, h, d, ox, oy, oz, col):
        """Triangular prism for ramps/slopes."""
        s = len(self.verts)
        hw, hd = w / 2, d / 2
        self.verts.append(Vec3(-hw + ox, oy, -hd + oz))       # 0 base front-left
        self.verts.append(Vec3(hw + ox, oy, -hd + oz))        # 1 base front-right
        self.verts.append(Vec3(hw + ox, oy, hd + oz))         # 2 base back-right
        self.verts.append(Vec3(-hw + ox, oy, hd + oz))        # 3 base back-left
        self.verts.append(Vec3(-hw + ox, oy + h, hd + oz))    # 4 top back-left
        self.verts.append(Vec3(hw + ox, oy + h, hd + oz))     # 5 top back-right
        for f in [
            [s, s+1, s+2, s+3],     # bottom
            [s+3, s+2, s+5, s+4],   # back wall
            [s, s+3, s+4, s+4],     # left triangle (degenerate quad)
            [s+1, s+5, s+5, s+2],   # right triangle
            [s, s+1, s+5, s+4],     # slope face
        ]:
            self.faces.append(Face(f, col))


def render(mesh, cam, polys):
    cy = math.cos(mesh.yaw)
    sy = math.sin(mesh.yaw)
    for face in mesh.faces:
        pts = []
        avgz = 0
        for i in face.idx:
            v = mesh.verts[i]
            rx = v.x * cy - v.z * sy
            rz = v.x * sy + v.z * cy
            ry = v.y
            wx = rx + mesh.x - cam["x"]
            wy = ry + mesh.y - cam["y"]
            wz = rz + mesh.z - cam["z"]
            if wz <= 1:
                break
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
        self.health = 8
        self.coins = 0
        self.stars = 0
        # Body
        self.cube(30, 30, 20, 0, 15, 0, RED)
        # Head
        self.cube(22, 20, 18, 0, 40, 0, (255, 200, 150))
        # Hat
        self.cube(26, 8, 22, 0, 54, 0, RED)
        # Legs
        self.cube(12, 15, 12, -8, 0, 0, BLUE)
        self.cube(12, 15, 12, 8, 0, 0, BLUE)

    def update(self, floor_y=0):
        self.dy -= GRAVITY
        self.y += self.dy
        if self.y < floor_y:
            self.y = floor_y
            self.dy = 0

    def jump(self):
        if abs(self.dy) < 0.1:
            self.dy = JUMP_FORCE


class Coin(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.cube(20, 5, 20, 0, 0, 0, YELLOW)
        self.spin = 0

    def animate(self):
        self.spin += 0.05
        self.yaw = self.spin


class Star(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.cube(15, 15, 15, 0, 7.5, 0, GOLD)
        self.bob = 0

    def animate(self):
        self.bob += 0.03
        self.y += math.sin(self.bob) * 0.5


# ============================================================
# LEVEL CLASS
# ============================================================

class Level:
    def __init__(self, name, terrain, stars, coins, entry_point=(0, 0, 400),
                 sky_color=DD_SKY, floor_y=0):
        self.name = name
        self.terrain = terrain
        self.stars = stars
        self.coins = coins
        self.entry_point = entry_point
        self.portals = []
        self.sky_color = sky_color
        self.floor_y = floor_y

    def add_portal(self, x1, x2, z1, z2, target_level, spawn):
        self.portals.append({
            "rect": (x1, x2, z1, z2),
            "target": target_level,
            "spawn": spawn,
        })


# ============================================================
# HELPER: scatter coins with a seed for consistency
# ============================================================

def scatter_coins(n, xr, zr, y=20, s=42):
    seed(s)
    c = [Coin(randint(-xr, xr), y, randint(-zr, zr)) for _ in range(n)]
    seed()
    return c


# ============================================================
# CASTLE HUB (3-floor layout with all portals)
# ============================================================

def make_castle():
    t = Mesh()

    # === EXTERIOR ===
    t.cube(3000, 10, 3000, 0, -5, 0, LIGHT_GREEN)

    # Moat
    for pos in [(-850, 0), (850, 0), (0, -850), (0, 850)]:
        t.cube(1800 if pos[1] == 0 else 200, 8, 200 if pos[1] == 0 else 1800,
               pos[0], -3, pos[1], WATER_BLUE)

    # Bridge
    t.cube(200, 12, 100, 0, 6, -800, DARK_BROWN)
    t.cube(20, 50, 20, -90, 25, -800, DARK_BROWN)
    t.cube(20, 50, 20, 90, 25, -800, DARK_BROWN)

    # Castle outer walls
    t.cube(1000, 200, 50, 0, 100, -500, STONE_GRAY)
    t.cube(200, 250, 800, -500, 125, 0, STONE_GRAY)
    t.cube(200, 250, 800, 500, 125, 0, STONE_GRAY)
    t.cube(1000, 250, 50, 0, 125, 500, STONE_GRAY)

    # Main building
    t.cube(600, 200, 600, 0, 100, 0, (210, 180, 140))

    # Corner towers
    for dx, dz in [(-250, -250), (250, -250), (-250, 250), (250, 250)]:
        t.cube(120, 350, 120, dx, 175, dz, STONE_GRAY)
        t.cube(60, 30, 60, dx, 365, dz, RED)  # tower cap

    # Roof pyramid
    for i in range(1, 8):
        sz = 600 - i * 50
        t.cube(sz, 12, sz, 0, 200 + i * 22, 0, (150, 0, 0))

    # === FLOOR 1 – MAIN HALL ===
    t.cube(500, 10, 500, 0, 10, 0, (160, 160, 160))  # floor
    t.cube(20, 180, 500, -250, 100, 0, STONE_GRAY)    # left wall
    t.cube(20, 180, 500, 250, 100, 0, STONE_GRAY)     # right wall
    t.cube(500, 180, 20, 0, 100, -250, STONE_GRAY)    # back wall
    t.cube(500, 180, 20, 0, 100, 250, STONE_GRAY)     # front wall

    # F1 paintings (courses 1-4 + Bowser 1)
    t.cube(100, 80, 10, -150, 70, -245, GREEN)         # 1 Bob-omb
    t.cube(100, 80, 10, 0, 70, -245, (150, 140, 130))  # 2 Whomp's
    t.cube(100, 80, 10, 150, 70, -245, WATER_BLUE)     # 3 Jolly Roger
    t.cube(10, 80, 100, -245, 70, -100, SNOW_WHITE)    # 4 Cool Cool
    # Bowser 1 trapdoor
    t.cube(80, 5, 80, 0, 11, -100, DARK_PURPLE)

    # Grand staircase to F2
    for i in range(8):
        t.cube(250, 10, 40, 0, 15 + i * 22, 200 + i * 35, (200, 180, 150))

    # === FLOOR 2 – UPPER HALL ===
    f2y = 190
    t.cube(500, 10, 500, 0, f2y, 600, (170, 170, 170))
    t.cube(20, 150, 500, -250, f2y + 75, 600, STONE_GRAY)
    t.cube(20, 150, 500, 250, f2y + 75, 600, STONE_GRAY)
    t.cube(500, 150, 20, 0, f2y + 75, 350, STONE_GRAY)
    t.cube(500, 150, 20, 0, f2y + 75, 850, STONE_GRAY)

    # F2 paintings (courses 5-10 + Bowser 2)
    t.cube(80, 70, 10, -180, f2y + 60, 355, GHOST_GREEN)     # 5 Big Boo
    t.cube(80, 70, 10, -60, f2y + 60, 355, CAVE_GRAY)        # 6 Hazy Maze
    t.cube(80, 70, 10, 60, f2y + 60, 355, LAVA_ORANGE)       # 7 Lethal Lava
    t.cube(80, 70, 10, 180, f2y + 60, 355, SAND_YELLOW)      # 8 Shifting Sand
    t.cube(10, 70, 80, -245, f2y + 60, 550, DEEP_BLUE)       # 9 Dire Dire Docks
    t.cube(10, 70, 80, -245, f2y + 60, 700, ICE_BLUE)        # 10 Snowman's Land
    # Bowser 2 trapdoor
    t.cube(80, 5, 80, 0, f2y + 1, 600, DARK_PURPLE)

    # Staircase to F3
    for i in range(8):
        t.cube(200, 10, 35, 200, f2y + 15 + i * 22, 600 + i * 35, (190, 170, 140))

    # === FLOOR 3 – TOP FLOOR ===
    f3y = 380
    t.cube(400, 10, 400, 0, f3y, 1100, (180, 180, 180))
    t.cube(20, 130, 400, -200, f3y + 65, 1100, STONE_GRAY)
    t.cube(20, 130, 400, 200, f3y + 65, 1100, STONE_GRAY)
    t.cube(400, 130, 20, 0, f3y + 65, 900, STONE_GRAY)
    t.cube(400, 130, 20, 0, f3y + 65, 1300, STONE_GRAY)

    # F3 paintings (courses 11-15 + Bowser 3)
    t.cube(70, 60, 10, -120, f3y + 50, 905, (100, 180, 255))  # 11 Wet-Dry
    t.cube(70, 60, 10, 0, f3y + 50, 905, GREEN)                # 12 Tall Tall Mtn
    t.cube(70, 60, 10, 120, f3y + 50, 905, (200, 150, 200))   # 13 Tiny-Huge
    t.cube(10, 60, 70, -195, f3y + 50, 1050, CLOCK_BRONZE)    # 14 Tick Tock
    t.cube(10, 60, 70, -195, f3y + 50, 1180, RAINBOW)         # 15 Rainbow Ride
    # Bowser 3 – big star door
    t.cube(100, 100, 10, 0, f3y + 60, 1295, DARK_PURPLE)

    # Secret areas entrance (wing/metal/vanish cap + aquarium + slide)
    t.cube(60, 40, 10, -180, 140, 245, (255, 50, 50))    # Wing Cap
    t.cube(60, 40, 10, -60, 140, 245, (180, 180, 180))   # Metal Cap
    t.cube(60, 40, 10, 60, 140, 245, (150, 100, 200))    # Vanish Cap
    t.cube(60, 40, 10, 180, 140, 245, WATER_BLUE)         # Aquarium
    # Slide entrance near staircase
    t.cube(60, 40, 10, -200, f2y + 50, 845, YELLOW)       # Princess Slide

    # Castle stars
    stars = [
        Star(300, 340, -200), Star(0, 50, -700), Star(-300, 90, -100),
        Star(150, 250, 50), Star(-150, 40, 150),
    ]
    coins = scatter_coins(20, 400, 400, 20, 101)
    level = Level("Peach's Castle", t, stars, coins, (0, 0, -700), DD_SKY)

    # ---- FLOOR 1 PORTALS ----
    level.add_portal(-200, -100, -255, -240, "Bob-omb Battlefield", (0, 0, 400))
    level.add_portal(-50, 50, -255, -240, "Whomp's Fortress", (0, 0, 300))
    level.add_portal(100, 200, -255, -240, "Jolly Roger Bay", (0, 0, 300))
    level.add_portal(-255, -240, -150, -50, "Cool Cool Mountain", (0, 0, 400))
    level.add_portal(-40, 40, -140, -60, "Bowser Dark World", (0, 0, 400))

    # ---- FLOOR 2 PORTALS ----
    level.add_portal(-220, -140, 350, 365, "Big Boo's Haunt", (0, 0, 400))
    level.add_portal(-100, -20, 350, 365, "Hazy Maze Cave", (0, 0, 400))
    level.add_portal(20, 100, 350, 365, "Lethal Lava Land", (0, 0, 400))
    level.add_portal(140, 220, 350, 365, "Shifting Sand Land", (0, 0, 400))
    level.add_portal(-255, -240, 510, 590, "Dire Dire Docks", (0, 0, 400))
    level.add_portal(-255, -240, 660, 740, "Snowman's Land", (0, 0, 400))
    level.add_portal(-40, 40, 560, 640, "Bowser Fire Sea", (0, 0, 400))

    # ---- FLOOR 3 PORTALS ----
    level.add_portal(-155, -85, 900, 915, "Wet-Dry World", (0, 0, 400))
    level.add_portal(-35, 35, 900, 915, "Tall Tall Mountain", (0, 0, 400))
    level.add_portal(85, 155, 900, 915, "Tiny-Huge Island", (0, 0, 400))
    level.add_portal(-205, -190, 1015, 1085, "Tick Tock Clock", (0, 0, 400))
    level.add_portal(-205, -190, 1145, 1215, "Rainbow Ride", (0, 0, 400))
    level.add_portal(-50, 50, 1290, 1305, "Bowser in the Sky", (0, 0, 400))

    # ---- SECRET AREA PORTALS ----
    level.add_portal(-210, -150, 240, 255, "Wing Cap Tower", (0, 0, 400))
    level.add_portal(-90, -30, 240, 255, "Metal Cap Cavern", (0, 0, 400))
    level.add_portal(30, 90, 240, 255, "Vanish Cap Ruins", (0, 0, 400))
    level.add_portal(150, 210, 240, 255, "Secret Aquarium", (0, 0, 400))
    level.add_portal(-230, -170, 840, 855, "Princess Slide", (0, 0, 400))

    return level


# ============================================================
# ALL 15 COURSES
# ============================================================

def _return_portal(level, target="Peach's Castle", spawn=(0, 0, -700)):
    """Add a standard return-to-castle portal at the far edge."""
    level.add_portal(-120, 120, 380, 430, target, spawn)


# ---- COURSE 1: Bob-omb Battlefield ----
def make_bobomb_battlefield():
    t = Mesh()
    t.cube(2000, 20, 2000, 0, -10, 0, LIGHT_GREEN)
    # King Bob-omb's mountain
    t.cube(400, 200, 400, 0, 100, 0, BROWN)
    t.cube(300, 100, 300, 0, 250, 0, BROWN)
    t.cube(200, 100, 200, 0, 350, 0, BROWN)
    t.cube(100, 60, 100, 0, 430, 0, BROWN)
    # Bridges
    t.cube(100, 15, 300, 300, 50, -200, DARK_BROWN)
    t.cube(100, 15, 300, -300, 50, 200, DARK_BROWN)
    # Cannon platform
    t.cube(80, 30, 80, -500, 15, -500, STONE_GRAY)
    # Chain Chomp post
    t.cube(20, 60, 20, 400, 30, -300, DARK_BROWN)
    # Fences
    t.cube(600, 40, 10, 0, 20, -600, DARK_BROWN)
    t.cube(10, 40, 400, -600, 20, -400, DARK_BROWN)

    stars = [
        Star(0, 470, 0), Star(300, 80, -200), Star(-300, 80, 200),
        Star(500, 50, 500), Star(-500, 45, -500), Star(200, 20, -600),
    ]
    coins = scatter_coins(12, 800, 800, 20, 1)
    lv = Level("Bob-omb Battlefield", t, stars, coins, (0, 0, 400), (100, 180, 255))
    _return_portal(lv)
    return lv


# ---- COURSE 2: Whomp's Fortress ----
def make_whomps_fortress():
    t = Mesh()
    t.cube(1500, 20, 1500, 0, -10, 0, STONE_GRAY)
    # Fortress tower
    t.cube(300, 200, 300, 0, 100, 0, (150, 140, 130))
    t.cube(250, 150, 250, 0, 275, 0, (140, 130, 120))
    t.cube(200, 100, 200, 0, 375, 0, (130, 120, 110))
    # Perimeter walls
    for x in (-500, 500):
        t.cube(50, 120, 1000, x, 60, 0, STONE_GRAY)
    for z in (-500, 500):
        t.cube(1000, 120, 50, 0, 60, z, STONE_GRAY)
    # Thwomp platform
    t.cube(150, 20, 150, 300, 100, 300, (200, 180, 150))
    t.cube(150, 20, 150, -300, 100, -300, (200, 180, 150))
    # Piranha plant platforms
    t.cube(80, 20, 80, -400, 40, 200, GREEN)
    t.cube(80, 20, 80, 400, 40, -200, GREEN)

    stars = [
        Star(0, 430, 0), Star(300, 120, 300), Star(-300, 120, -300),
        Star(400, 60, -200), Star(-400, 60, 200), Star(0, 30, 500),
    ]
    coins = scatter_coins(8, 600, 600, 20, 2)
    lv = Level("Whomp's Fortress", t, stars, coins, (0, 0, 300), (160, 180, 220))
    _return_portal(lv)
    return lv


# ---- COURSE 3: Jolly Roger Bay ----
def make_jolly_roger_bay():
    t = Mesh()
    # Ocean floor
    t.cube(2000, 5, 2000, 0, -100, 0, (30, 50, 100))
    # Water surface
    t.cube(2000, 3, 2000, 0, 0, 0, WATER_BLUE)
    # Ship wreck
    t.cube(300, 100, 100, -100, -50, -200, DARK_BROWN)
    t.cube(60, 200, 10, -100, 50, -200, DARK_BROWN)  # mast
    # Cave entrance
    t.cube(200, 150, 200, 400, 20, -300, STONE_GRAY)
    # Dock / shore
    t.cube(500, 30, 200, 0, 15, 500, (210, 190, 140))
    # Treasure chests (small cubes)
    for pos in [(-200, -80, 100), (300, -70, -100), (-400, -60, -400)]:
        t.cube(40, 30, 40, *pos, DARK_BROWN)
    # Clam platforms
    t.cube(100, 15, 100, 200, -20, 200, (200, 200, 220))
    # Eel cave
    t.cube(150, 100, 150, -400, -50, -400, CAVE_GRAY)

    stars = [
        Star(-100, 100, -200), Star(400, 60, -300), Star(0, 20, 500),
        Star(-400, -30, -400), Star(300, -20, 200), Star(-200, -60, 100),
    ]
    coins = scatter_coins(10, 600, 600, -10, 3)
    lv = Level("Jolly Roger Bay", t, stars, coins, (0, 30, 500), (80, 140, 200))
    _return_portal(lv)
    return lv


# ---- COURSE 4: Cool Cool Mountain ----
def make_cool_cool_mountain():
    t = Mesh()
    t.cube(2000, 20, 2000, 0, -10, 0, SNOW_WHITE)
    # Mountain peak layers
    t.cube(500, 80, 500, -200, 40, -200, (220, 220, 240))
    t.cube(400, 80, 400, -200, 120, -200, (230, 230, 250))
    t.cube(300, 80, 300, -200, 200, -200, (240, 240, 255))
    t.cube(200, 80, 200, -200, 280, -200, WHITE)
    # Slide ramp
    t.cube(150, 10, 600, 200, 30, 0, ICE_BLUE)
    # Cabin
    t.cube(120, 80, 100, 400, 40, 300, DARK_BROWN)
    t.cube(130, 10, 110, 400, 85, 300, RED)  # roof
    # Snowman
    t.cube(60, 60, 60, -500, 30, 300, WHITE)
    t.cube(40, 40, 40, -500, 80, 300, WHITE)
    # Ice bridge
    t.cube(200, 10, 60, 0, 150, -400, ICE_BLUE)
    # Penguin platform
    t.cube(100, 20, 100, 300, 280, -200, SNOW_WHITE)

    stars = [
        Star(-200, 320, -200), Star(200, 50, 300), Star(400, 60, 300),
        Star(-500, 50, 300), Star(0, 170, -400), Star(300, 300, -200),
    ]
    coins = scatter_coins(8, 600, 600, 20, 4)
    lv = Level("Cool Cool Mountain", t, stars, coins, (0, 0, 400), (200, 220, 240))
    _return_portal(lv)
    return lv


# ---- COURSE 5: Big Boo's Haunt ----
def make_big_boos_haunt():
    t = Mesh()
    # Courtyard
    t.cube(1200, 10, 1200, 0, -5, 0, (40, 50, 40))
    # Haunted mansion
    t.cube(500, 200, 400, 0, 100, 0, (60, 60, 80))
    # Mansion floors
    t.cube(480, 10, 380, 0, 10, 0, (50, 50, 60))    # F1
    t.cube(480, 10, 380, 0, 200, 0, (50, 50, 60))   # F2
    t.cube(400, 10, 300, 0, 380, 0, (50, 50, 60))   # attic
    # Roof
    for i in range(1, 6):
        t.cube(500 - i * 60, 12, 400 - i * 40, 0, 200 + i * 25, 0, (40, 40, 50))
    # Graveyard fence
    for x in range(-500, 600, 200):
        t.cube(10, 50, 10, x, 25, -500, (30, 30, 30))
    # Tombstones
    for x in [-400, -200, 0, 200, 400]:
        t.cube(40, 40, 15, x, 20, -450, STONE_GRAY)
    # Cage area
    t.cube(120, 120, 120, 300, 260, 0, (80, 80, 80))
    # Spooky trees
    for pos in [(-350, 0, 400), (350, 0, 400), (-400, 0, -200), (400, 0, -200)]:
        t.cube(20, 100, 20, pos[0], 50, pos[2], DARK_BROWN)
        t.cube(60, 30, 60, pos[0], 110, pos[2], (30, 60, 30))

    stars = [
        Star(0, 30, 0), Star(300, 280, 0), Star(-200, 220, -100),
        Star(0, 400, 0), Star(-300, 50, -450), Star(200, 120, 200),
    ]
    coins = scatter_coins(8, 400, 400, 20, 5)
    lv = Level("Big Boo's Haunt", t, stars, coins, (0, 0, 500), (15, 10, 25))
    _return_portal(lv)
    return lv


# ---- COURSE 6: Hazy Maze Cave ----
def make_hazy_maze_cave():
    t = Mesh()
    # Cave floor
    t.cube(2000, 20, 2000, 0, -10, 0, CAVE_GRAY)
    # Ceiling
    t.cube(2000, 20, 2000, 0, 350, 0, (50, 50, 55))
    # Maze walls
    for z in range(-600, 700, 300):
        t.cube(1200, 200, 40, 0, 100, z, CAVE_GRAY)
    for x in range(-500, 600, 250):
        t.cube(40, 200, 800, x, 100, 0, (90, 90, 100))
    # Toxic haze pool
    t.cube(400, 5, 400, -400, 2, -400, TOXIC_GREEN)
    # Underground lake (Dorrie's area)
    t.cube(500, 5, 500, 400, -5, 400, DARK_WATER)
    # Metal cap switch platform
    t.cube(100, 30, 100, 400, 15, -400, (180, 180, 180))
    # Elevator shaft
    t.cube(80, 300, 80, -500, 150, 0, STONE_GRAY)
    # Rolling rocks path
    t.cube(150, 10, 600, 0, 5, -200, (100, 80, 60))
    # Black hole (pit)
    t.cube(100, 5, 100, 300, -5, -300, (10, 10, 10))

    stars = [
        Star(-400, 50, -400), Star(400, 30, 400), Star(0, 100, 0),
        Star(-500, 180, 0), Star(400, 45, -400), Star(300, 20, -300),
    ]
    coins = scatter_coins(10, 600, 600, 15, 6)
    lv = Level("Hazy Maze Cave", t, stars, coins, (0, 0, 400), (30, 30, 40))
    _return_portal(lv)
    return lv


# ---- COURSE 7: Lethal Lava Land ----
def make_lethal_lava_land():
    t = Mesh()
    t.cube(2000, 5, 2000, 0, -5, 0, LAVA_ORANGE)
    # Volcano
    t.cube(400, 150, 400, 0, 75, 0, (100, 50, 20))
    t.cube(300, 100, 300, 0, 175, 0, (120, 60, 30))
    t.cube(200, 80, 200, 0, 275, 0, (140, 70, 40))
    t.cube(100, 60, 100, 0, 345, 0, (160, 80, 50))
    # Lava mouth (crater)
    t.cube(80, 10, 80, 0, 380, 0, (255, 50, 0))
    # Stone platforms
    for dx, dz in [(400, 400), (-400, -400), (400, -400), (-400, 400),
                   (600, 0), (-600, 0), (0, 600), (0, -600)]:
        t.cube(200, 30, 200, dx, 15, dz, STONE_GRAY)
    # Bully platform (big)
    t.cube(300, 40, 300, -500, 20, 0, (80, 80, 80))
    # Rolling log bridge
    t.cube(60, 30, 400, 300, 15, -300, DARK_BROWN)
    # Fire pillars
    for pos in [(200, 200), (-200, -200), (200, -200)]:
        t.cube(30, 80, 30, pos[0], 40, pos[1], (255, 150, 0))

    stars = [
        Star(0, 400, 0), Star(400, 45, 400), Star(-400, 45, -400),
        Star(400, 45, -400), Star(-500, 55, 0), Star(0, 30, 600),
    ]
    coins = scatter_coins(10, 600, 600, 10, 7)
    lv = Level("Lethal Lava Land", t, stars, coins, (0, 30, 400), (80, 20, 20))
    _return_portal(lv)
    return lv


# ---- COURSE 8: Shifting Sand Land ----
def make_shifting_sand_land():
    t = Mesh()
    t.cube(2500, 15, 2500, 0, -8, 0, SAND_YELLOW)
    # Pyramid
    for i in range(8):
        sz = 500 - i * 50
        t.cube(sz, 25, sz, 0, i * 25, 0, (190 + i * 5, 170 + i * 3, 60 + i * 5))
    # Quicksand pit
    t.cube(300, 5, 300, 400, -3, 400, (180, 150, 50))
    # Oasis
    t.cube(200, 5, 200, -500, 2, -400, WATER_BLUE)
    t.cube(20, 80, 20, -500, 40, -400, DARK_BROWN)  # palm tree trunk
    t.cube(80, 15, 80, -500, 85, -400, GREEN)        # palm leaves
    # Tox boxes path
    for i in range(5):
        t.cube(100, 80, 100, -300 + i * 150, 40, -200, (200, 190, 160))
    # Klepto's perch
    t.cube(60, 150, 60, 600, 75, -500, STONE_GRAY)
    # Pillars
    for pos in [(300, -400), (-300, 300), (500, 200), (-500, 200)]:
        t.cube(50, 100, 50, pos[0], 50, pos[1], SAND_YELLOW)

    stars = [
        Star(0, 220, 0), Star(-500, 30, -400), Star(600, 170, -500),
        Star(400, 20, 400), Star(-300, 100, -200), Star(0, 50, -600),
    ]
    coins = scatter_coins(10, 800, 800, 15, 8)
    lv = Level("Shifting Sand Land", t, stars, coins, (0, 0, 400), (220, 200, 140))
    _return_portal(lv)
    return lv


# ---- COURSE 9: Dire Dire Docks ----
def make_dire_dire_docks():
    t = Mesh()
    # Deep water
    t.cube(2000, 5, 2000, 0, -200, 0, DEEP_BLUE)
    # Water surface
    t.cube(2000, 3, 2000, 0, 0, 0, DARK_WATER)
    # Dock structure
    t.cube(400, 30, 200, 0, 15, 500, (150, 130, 100))
    t.cube(30, 80, 30, -180, 40, 500, DARK_BROWN)  # pole
    t.cube(30, 80, 30, 180, 40, 500, DARK_BROWN)
    # Submarine pen
    t.cube(300, 100, 200, 0, -50, -200, STONE_GRAY)
    # Bowser's sub (simplified)
    t.cube(200, 60, 80, 0, -30, -200, (40, 40, 50))
    # Water rings (pole markers)
    for x in range(-400, 500, 200):
        t.cube(15, 120, 15, x, -60, 0, (200, 200, 220))
    # Cave tunnels
    t.cube(150, 100, 600, -500, -50, 0, CAVE_GRAY)
    t.cube(150, 100, 600, 500, -50, 0, CAVE_GRAY)
    # Manta ray area
    t.cube(300, 5, 300, -300, -150, -400, (20, 40, 80))

    stars = [
        Star(0, 40, 500), Star(0, -20, -200), Star(-400, -40, 0),
        Star(400, -40, 0), Star(-300, -120, -400), Star(0, -100, 200),
    ]
    coins = scatter_coins(8, 500, 500, -30, 9)
    lv = Level("Dire Dire Docks", t, stars, coins, (0, 30, 500), (20, 40, 80))
    _return_portal(lv)
    return lv


# ---- COURSE 10: Snowman's Land ----
def make_snowmans_land():
    t = Mesh()
    t.cube(2000, 20, 2000, 0, -10, 0, SNOW_WHITE)
    # Giant snowman
    t.cube(300, 200, 300, 0, 100, 0, WHITE)
    t.cube(200, 150, 200, 0, 275, 0, WHITE)
    t.cube(120, 100, 120, 0, 375, 0, WHITE)
    # Snowman hat
    t.cube(150, 20, 150, 0, 435, 0, (20, 20, 20))
    t.cube(100, 40, 100, 0, 460, 0, (20, 20, 20))
    # Ice area
    t.cube(400, 5, 400, -400, 2, -400, ICE_BLUE)
    # Igloo
    t.cube(150, 80, 150, 400, 40, -300, WHITE)
    t.cube(160, 10, 160, 400, 85, -300, ICE_BLUE)
    # Frozen pond
    t.cube(300, 3, 300, 400, 1, 400, (180, 210, 240))
    # Trees
    for pos in [(-300, 200), (300, 200), (-500, -200), (500, -200)]:
        t.cube(20, 80, 20, pos[0], 40, pos[1], DARK_BROWN)
        t.cube(60, 30, 60, pos[0], 90, pos[1], (20, 80, 20))
    # Wind bridge
    t.cube(60, 10, 300, -200, 100, 0, ICE_BLUE)

    stars = [
        Star(0, 480, 0), Star(-400, 30, -400), Star(400, 60, -300),
        Star(400, 30, 400), Star(-200, 120, 0), Star(-300, 50, 200),
    ]
    coins = scatter_coins(8, 600, 600, 20, 10)
    lv = Level("Snowman's Land", t, stars, coins, (0, 0, 400), (180, 200, 230))
    _return_portal(lv)
    return lv


# ---- COURSE 11: Wet-Dry World ----
def make_wet_dry_world():
    t = Mesh()
    # Base floor
    t.cube(1600, 10, 1600, 0, -5, 0, (100, 120, 160))
    # Water (variable height – we set it mid-level)
    t.cube(1600, 3, 1600, 0, 100, 0, (100, 180, 255))
    # City buildings
    for i, (x, z, w, h) in enumerate([
        (-300, -300, 200, 300), (300, -300, 150, 250), (-300, 300, 180, 350),
        (300, 300, 200, 200), (0, 0, 250, 400),
    ]):
        shade = 140 + i * 15
        t.cube(w, h, w, x, h // 2, z, (shade, shade, shade + 20))
    # Crystal switches (color cubes)
    for x, z, col in [(-500, 0, (200, 50, 50)), (500, 0, (50, 50, 200)),
                       (0, -500, (200, 200, 50)), (0, 500, (50, 200, 50))]:
        t.cube(40, 40, 40, x, 20, z, col)
    # Wire mesh platforms
    for y in [50, 150, 250]:
        t.cube(300, 5, 100, 0, y, -400, (160, 160, 180))
    # Downtown area
    t.cube(400, 10, 400, 0, -5, -600, (90, 90, 100))

    stars = [
        Star(0, 420, 0), Star(-300, 320, -300), Star(300, 270, -300),
        Star(-300, 370, 300), Star(0, 120, -400), Star(500, 40, 0),
    ]
    coins = scatter_coins(8, 600, 600, 110, 11)
    lv = Level("Wet-Dry World", t, stars, coins, (0, 0, 400), (140, 170, 210))
    _return_portal(lv)
    return lv


# ---- COURSE 12: Tall Tall Mountain ----
def make_tall_tall_mountain():
    t = Mesh()
    t.cube(2000, 20, 2000, 0, -10, 0, GREEN)
    # Mountain (stacked)
    for i in range(10):
        sz = 600 - i * 50
        shade = 60 + i * 15
        t.cube(sz, 40, sz, 0, i * 40 + 20, 0, (shade, 120 + i * 8, shade))
    # Waterfall
    t.cube(60, 300, 20, -300, 150, -200, WATER_BLUE)
    # Monkey cage
    t.cube(80, 80, 80, 300, 280, -200, (100, 80, 60))
    # Log bridge
    t.cube(40, 20, 300, 200, 200, 100, DARK_BROWN)
    # Slide entrance
    t.cube(80, 60, 80, -200, 360, 0, CAVE_GRAY)
    # Mushrooms (platforms)
    for pos in [(400, 100, 300), (-400, 60, -300), (200, 150, -400)]:
        t.cube(80, 15, 80, *pos, RED)
        t.cube(20, 40, 20, pos[0], pos[1] - 25, pos[2], WHITE)

    stars = [
        Star(0, 420, 0), Star(-300, 180, -200), Star(300, 300, -200),
        Star(200, 220, 100), Star(-200, 380, 0), Star(400, 120, 300),
    ]
    coins = scatter_coins(8, 600, 600, 20, 12)
    lv = Level("Tall Tall Mountain", t, stars, coins, (0, 0, 400), (120, 180, 120))
    _return_portal(lv)
    return lv


# ---- COURSE 13: Tiny-Huge Island ----
def make_tiny_huge_island():
    t = Mesh()
    t.cube(2500, 20, 2500, 0, -10, 0, LIGHT_GREEN)
    # Giant structures (huge island mode)
    t.cube(600, 300, 600, 0, 150, 0, BROWN)
    t.cube(400, 200, 400, 0, 350, 0, BROWN)
    # Tiny village
    for i, (x, z) in enumerate([(-400, -400), (-250, -400), (-400, -250)]):
        t.cube(60, 40, 60, x, 20, z, (180 + i * 15, 150 + i * 10, 100))
    # Giant pipe
    t.cube(100, 150, 100, 500, 75, 0, GREEN)
    # Koopa beach
    t.cube(400, 5, 200, 0, 2, 600, SAND_YELLOW)
    t.cube(400, 3, 300, 0, 0, 750, WATER_BLUE)
    # Wind tower
    t.cube(80, 250, 80, -500, 125, 300, STONE_GRAY)
    # Wiggler cave
    t.cube(200, 100, 200, 0, -30, -400, CAVE_GRAY)
    # Size switch pipe
    t.cube(80, 80, 80, -600, 40, 0, (0, 160, 0))

    stars = [
        Star(0, 400, 0), Star(-400, 40, -400), Star(500, 100, 0),
        Star(0, 20, 600), Star(-500, 160, 300), Star(0, -10, -400),
    ]
    coins = scatter_coins(10, 800, 800, 20, 13)
    lv = Level("Tiny-Huge Island", t, stars, coins, (0, 0, 400), (120, 200, 120))
    _return_portal(lv)
    return lv


# ---- COURSE 14: Tick Tock Clock ----
def make_tick_tock_clock():
    t = Mesh()
    # Clock interior (vertical level)
    t.cube(600, 10, 600, 0, -5, 0, CLOCK_BRONZE)
    # Clock gears (rotating platforms simulated as cubes)
    for y in range(0, 800, 100):
        w = 200 - (y % 200)
        t.cube(w, 15, w, (y % 300) - 150, y, (y % 200) - 100, CLOCK_BRONZE)
    # Pendulum shaft
    t.cube(30, 600, 30, -250, 300, 0, (160, 120, 40))
    # Clock hands
    t.cube(200, 10, 30, 0, 400, 0, (180, 140, 60))
    t.cube(150, 10, 20, 100, 500, 100, (180, 140, 60))
    # Walls (clock tower)
    t.cube(20, 800, 600, -300, 400, 0, (100, 90, 70))
    t.cube(20, 800, 600, 300, 400, 0, (100, 90, 70))
    t.cube(600, 800, 20, 0, 400, -300, (100, 90, 70))
    t.cube(600, 800, 20, 0, 400, 300, (100, 90, 70))
    # Conveyor belt platforms
    for i in range(4):
        t.cube(120, 10, 60, -100, 200 + i * 150, -200 + i * 80, (140, 100, 40))

    stars = [
        Star(0, 100, 0), Star(-100, 300, -100), Star(100, 500, 100),
        Star(0, 700, 0), Star(-200, 450, 150), Star(150, 200, -150),
    ]
    coins = scatter_coins(8, 250, 250, 50, 14)
    lv = Level("Tick Tock Clock", t, stars, coins, (0, 0, 400), (60, 50, 40))
    _return_portal(lv)
    return lv


# ---- COURSE 15: Rainbow Ride ----
def make_rainbow_ride():
    t = Mesh()
    # Sky floor (invisible base far below)
    t.cube(100, 5, 100, 0, -500, 0, (80, 80, 80))
    # Flying carpet path (series of platforms)
    for i in range(12):
        angle = i * 0.5
        px = int(math.cos(angle) * 300)
        pz = int(math.sin(angle) * 300)
        py = 50 + i * 40
        col = (
            int(200 + 55 * math.sin(i * 0.8)),
            int(100 + 100 * math.sin(i * 0.5 + 1)),
            int(150 + 100 * math.cos(i * 0.3)),
        )
        t.cube(120, 10, 120, px, py, pz, col)
    # Rainbow bridge segments
    for i in range(8):
        r = int(255 * (i / 7))
        g = int(255 * ((7 - i) / 7))
        b = int(128 + 127 * math.sin(i))
        t.cube(80, 10, 80, -400 + i * 100, 300 + i * 20, -200, (r, g, b))
    # House in the sky
    t.cube(200, 120, 200, 400, 400, 200, (220, 200, 180))
    t.cube(220, 10, 220, 400, 465, 200, RED)  # roof
    # Ship (airship)
    t.cube(300, 40, 100, -300, 350, 300, DARK_BROWN)
    t.cube(20, 100, 10, -300, 400, 300, DARK_BROWN)  # mast
    # Floating islands
    for pos in [(0, 200, 0), (200, 150, -300), (-200, 250, 200)]:
        t.cube(100, 30, 100, *pos, LIGHT_GREEN)
    # Tricky triangles
    t.cube(80, 8, 80, 100, 500, -100, RAINBOW)
    t.cube(80, 8, 80, -100, 520, 100, RAINBOW)

    stars = [
        Star(400, 480, 200), Star(-300, 400, 300), Star(0, 540, 0),
        Star(200, 180, -300), Star(-200, 280, 200), Star(100, 520, -100),
    ]
    coins = scatter_coins(8, 400, 400, 200, 15)
    lv = Level("Rainbow Ride", t, stars, coins, (0, 60, 0), (120, 140, 220))
    _return_portal(lv)
    return lv


# ============================================================
# BOWSER STAGES
# ============================================================

def make_bowser_dark_world():
    t = Mesh()
    t.cube(1500, 10, 1500, 0, -5, 0, (30, 20, 40))
    # Dark path
    for i in range(10):
        t.cube(150, 15, 150, i * 120 - 600, 10 + i * 8, i * 50 - 250, (50 + i * 10, 30, 50))
    # Lava pits
    t.cube(200, 5, 200, -300, 2, 300, LAVA_ORANGE)
    t.cube(200, 5, 200, 300, 2, -300, LAVA_ORANGE)
    # Crystal pillars
    for x in range(-400, 500, 200):
        t.cube(40, 120, 40, x, 60, 0, DARK_PURPLE)
    # Bowser arena
    t.cube(400, 20, 400, 0, 10, -400, (40, 30, 50))
    # Pipe (exit)
    t.cube(60, 80, 60, 0, 40, -600, GREEN)

    stars = [Star(0, 50, -400)]
    coins = scatter_coins(5, 500, 500, 15, 100)
    lv = Level("Bowser Dark World", t, stars, coins, (0, 0, 400), (10, 5, 20))
    _return_portal(lv)
    return lv


def make_bowser_fire_sea():
    t = Mesh()
    t.cube(1800, 5, 1800, 0, -5, 0, LAVA_ORANGE)
    # Platforms over lava
    for i in range(15):
        px = int(math.cos(i * 0.7) * 400)
        pz = int(math.sin(i * 0.7) * 400)
        t.cube(120, 20, 120, px, 15 + i * 10, pz, STONE_GRAY)
    # Rising/falling platforms
    for y in [30, 80, 130, 180]:
        t.cube(100, 15, 100, 500, y, 0, (80, 80, 90))
    # Fire bars (pillars)
    for pos in [(200, -200), (-200, 200), (0, 400)]:
        t.cube(30, 100, 30, pos[0], 50, pos[1], (200, 100, 0))
    # Bowser arena
    t.cube(500, 25, 500, 0, 12, -400, (60, 40, 30))
    # Pipe
    t.cube(60, 80, 60, 0, 40, -650, GREEN)

    stars = [Star(0, 60, -400)]
    coins = scatter_coins(5, 500, 500, 20, 101)
    lv = Level("Bowser Fire Sea", t, stars, coins, (0, 30, 400), (60, 15, 10))
    _return_portal(lv)
    return lv


def make_bowser_in_the_sky():
    t = Mesh()
    # Sky void – base below
    t.cube(80, 5, 80, 0, -800, 0, (30, 30, 30))
    # Ascending platforms
    for i in range(20):
        angle = i * 0.6
        px = int(math.cos(angle) * 350)
        pz = int(math.sin(angle) * 350)
        py = i * 30
        t.cube(130, 15, 130, px, py, pz, (80 + i * 5, 60 + i * 3, 100 + i * 4))
    # Stairway to Bowser
    for i in range(8):
        t.cube(200, 12, 100, 0, 600 + i * 20, -200 + i * 40, STONE_GRAY)
    # Bowser's final arena
    t.cube(600, 30, 600, 0, 760, 200, (50, 40, 60))
    # Bomb spheres at edge
    for angle in range(0, 360, 45):
        bx = int(math.cos(math.radians(angle)) * 280)
        bz = int(math.sin(math.radians(angle)) * 280) + 200
        t.cube(40, 40, 40, bx, 790, bz, (20, 20, 20))
    # Pipe
    t.cube(60, 80, 60, 0, 800, -200, GREEN)

    stars = [Star(0, 810, 200)]
    coins = scatter_coins(5, 300, 300, 100, 102)
    lv = Level("Bowser in the Sky", t, stars, coins, (0, 30, 400), (80, 60, 120))
    _return_portal(lv)
    return lv


# ============================================================
# SECRET LEVELS
# ============================================================

def make_wing_cap_tower():
    t = Mesh()
    # Tower in the clouds
    t.cube(800, 5, 800, 0, -5, 0, (220, 230, 255))
    # Central tower
    t.cube(200, 300, 200, 0, 150, 0, (200, 180, 160))
    # Wing cap switch
    t.cube(60, 20, 60, 0, 310, 0, RED)
    # Cloud platforms
    for i in range(6):
        angle = i * math.pi / 3
        cx = int(math.cos(angle) * 300)
        cz = int(math.sin(angle) * 300)
        t.cube(100, 15, 100, cx, 20 + i * 30, cz, WHITE)
    # Rainbow ring
    for i in range(8):
        angle = i * math.pi / 4
        t.cube(30, 30, 30, int(math.cos(angle) * 200), 200, int(math.sin(angle) * 200),
               (255, int(200 * abs(math.sin(i))), int(200 * abs(math.cos(i)))))

    stars = [Star(0, 340, 0)]
    coins = scatter_coins(5, 300, 300, 30, 200)
    lv = Level("Wing Cap Tower", t, stars, coins, (0, 0, 400), (180, 200, 255))
    _return_portal(lv)
    return lv


def make_metal_cap_cavern():
    t = Mesh()
    t.cube(1200, 10, 1200, 0, -5, 0, CAVE_GRAY)
    # Waterfall
    t.cube(80, 200, 20, 0, 100, -500, WATER_BLUE)
    # Underground river
    t.cube(1200, 5, 150, 0, 2, 0, DARK_WATER)
    # Metal cap switch
    t.cube(60, 20, 60, 0, 15, -300, (180, 180, 180))
    # Cave walls
    t.cube(20, 200, 1200, -600, 100, 0, CAVE_GRAY)
    t.cube(20, 200, 1200, 600, 100, 0, CAVE_GRAY)
    t.cube(1200, 200, 20, 0, 100, -600, CAVE_GRAY)
    t.cube(1200, 200, 20, 0, 100, 600, CAVE_GRAY)

    stars = [Star(0, 40, -300)]
    coins = scatter_coins(5, 400, 400, 15, 201)
    lv = Level("Metal Cap Cavern", t, stars, coins, (0, 0, 400), (40, 40, 50))
    _return_portal(lv)
    return lv


def make_vanish_cap_ruins():
    t = Mesh()
    t.cube(1000, 10, 1000, 0, -5, 0, (80, 70, 100))
    # Slope (slide down into ruins)
    t.cube(200, 10, 500, 0, 100, -200, (100, 80, 120))
    # Vanish cap switch
    t.cube(60, 20, 60, 0, 15, 300, PURPLE)
    # Disappearing platforms
    for i in range(6):
        t.cube(80, 10, 80, -200 + i * 80, 40 + i * 15, 0, (150, 100, 200))
    # Ancient pillars
    for x in range(-300, 400, 150):
        t.cube(40, 100, 40, x, 50, -300, (110, 100, 130))
    # Walls
    t.cube(20, 150, 1000, -500, 75, 0, (70, 60, 90))
    t.cube(20, 150, 1000, 500, 75, 0, (70, 60, 90))

    stars = [Star(0, 40, 300)]
    coins = scatter_coins(5, 400, 400, 15, 202)
    lv = Level("Vanish Cap Ruins", t, stars, coins, (0, 120, -400), (50, 40, 70))
    _return_portal(lv)
    return lv


def make_secret_aquarium():
    t = Mesh()
    # Glass box underwater
    t.cube(800, 5, 800, 0, -200, 0, (20, 40, 80))
    t.cube(800, 3, 800, 0, 200, 0, (40, 80, 160))  # ceiling water
    # Glass walls
    for x in [-400, 400]:
        t.cube(5, 400, 800, x, 0, 0, (100, 180, 255))
    for z in [-400, 400]:
        t.cube(800, 400, 5, 0, 0, z, (100, 180, 255))
    # Coral formations
    for pos in [(-200, -150, -200), (200, -150, 200), (0, -150, 0),
                (-300, -150, 100), (300, -150, -100)]:
        t.cube(60, 80, 60, *pos, (255, 100, 100))
    # Treasure
    t.cube(40, 30, 40, 0, -180, 0, GOLD)

    stars = [Star(0, -150, 0)]
    coins = scatter_coins(8, 300, 300, -100, 203)
    lv = Level("Secret Aquarium", t, stars, coins, (0, 0, 400), (30, 60, 120))
    _return_portal(lv)
    return lv


def make_princess_slide():
    t = Mesh()
    # Slide track (descending platforms)
    for i in range(20):
        y = 400 - i * 20
        z = -400 + i * 50
        x = int(math.sin(i * 0.5) * 200)
        t.cube(120, 8, 80, x, y, z, (255, 200 + i * 2, 100 + i * 5))
    # Walls along slide
    t.cube(20, 500, 1200, -300, 200, 200, (200, 180, 160))
    t.cube(20, 500, 1200, 300, 200, 200, (200, 180, 160))
    # Start platform
    t.cube(200, 15, 200, 0, 410, -400, GOLD)
    # End platform
    t.cube(200, 15, 200, 0, 10, 600, GOLD)

    stars = [Star(0, 30, 600)]
    coins = scatter_coins(5, 200, 500, 200, 204)
    lv = Level("Princess Slide", t, stars, coins, (0, 420, -400), (220, 180, 160))
    _return_portal(lv, spawn=(0, 0, -700))
    return lv


# ============================================================
# UI: Dear Mario card
# ============================================================

def dear_card():
    title = pygame.font.SysFont("Times New Roman", 34, bold=True)
    body = pygame.font.SysFont("Times New Roman", 24)

    fade = 0
    while True:
        dt = clock.tick(FPS)
        fade = min(255, fade + dt * 0.7)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                return

        screen.fill(DD_SKY)
        card = pygame.Surface((580, 380), pygame.SRCALPHA)
        card.fill(PARCHMENT)
        pygame.draw.rect(card, PARCHMENT_BORDER, card.get_rect(), 6)

        card.blit(title.render("Dear Mario,", True, INK), (40, 30))
        lines = [
            "You're invited to Peach's Castle!",
            "Please come right away!",
            "",
            "There are 90 stars hidden across",
            "15 courses, 3 Bowser stages,",
            "and 5 secret areas.",
            "",
            "  — Peach",
        ]
        for i, line in enumerate(lines):
            card.blit(body.render(line, True, INK), (40, 80 + i * 32))

        card.set_alpha(int(fade))
        screen.blit(card, (110, 110))
        pygame.display.flip()


# ============================================================
# MENU
# ============================================================

def menu():
    title_font = pygame.font.SysFont("Arial", 48, bold=True)
    sub_font = pygame.font.SysFont("Arial", 22)
    prompt_font = pygame.font.SysFont("Arial", 28, bold=True)
    t = 0

    while True:
        clock.tick(FPS)
        t += 1
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                return

        screen.fill(DD_SKY)

        # Animated stars background
        for i in range(30):
            sx = (i * 137 + t) % WIDTH
            sy = (i * 89) % HEIGHT
            brightness = int(150 + 100 * math.sin(t * 0.02 + i))
            pygame.draw.circle(screen, (brightness, brightness, brightness), (sx, sy), 2)

        # Title
        title = title_font.render("SUPER MARIO 64", True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 140))

        sub = sub_font.render("Pygame Port — All Maps Edition", True, WHITE)
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 200))

        credits = sub_font.render("Team Flames / CatSDK", True, (180, 180, 180))
        screen.blit(credits, (WIDTH // 2 - credits.get_width() // 2, 240))

        # Blinking prompt
        if (t // 30) % 2 == 0:
            prompt = prompt_font.render("PRESS START", True, WHITE)
            screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 340))

        pygame.display.flip()


# ============================================================
# HUD
# ============================================================

def draw_hud(mario, level_name, show_map):
    font = pygame.font.SysFont("Arial", 22, bold=True)
    small = pygame.font.SysFont("Arial", 16)

    # Star counter
    star_txt = font.render(f"Stars: {mario.stars}", True, GOLD)
    screen.blit(star_txt, (20, 15))

    # Coin counter
    coin_txt = font.render(f"Coins: {mario.coins}", True, YELLOW)
    screen.blit(coin_txt, (20, 42))

    # Health
    health_txt = font.render(f"HP: {mario.health}", True, RED)
    screen.blit(health_txt, (20, 69))

    # Level name
    name_txt = font.render(level_name, True, WHITE)
    screen.blit(name_txt, (WIDTH - name_txt.get_width() - 20, 15))

    # Controls hint
    hint = small.render("WASD=Move  Space=Jump  M=Map  Esc=Quit", True, (160, 160, 160))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 28))


# ============================================================
# MAP SCREEN
# ============================================================

ALL_LEVEL_NAMES = [
    "Peach's Castle",
    "Bob-omb Battlefield", "Whomp's Fortress", "Jolly Roger Bay",
    "Cool Cool Mountain", "Big Boo's Haunt", "Hazy Maze Cave",
    "Lethal Lava Land", "Shifting Sand Land", "Dire Dire Docks",
    "Snowman's Land", "Wet-Dry World", "Tall Tall Mountain",
    "Tiny-Huge Island", "Tick Tock Clock", "Rainbow Ride",
    "Bowser Dark World", "Bowser Fire Sea", "Bowser in the Sky",
    "Wing Cap Tower", "Metal Cap Cavern", "Vanish Cap Ruins",
    "Secret Aquarium", "Princess Slide",
]


def draw_map_screen(current_name):
    """Full-screen map overlay showing all levels."""
    font = pygame.font.SysFont("Arial", 20, bold=True)
    small = pygame.font.SysFont("Arial", 16)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    title = font.render("=== CASTLE MAP — ALL LEVELS ===", True, GOLD)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

    # Three columns
    col_w = WIDTH // 3
    headers = ["Main Courses", "More Courses", "Bowser & Secrets"]
    groups = [
        ALL_LEVEL_NAMES[0:9],   # castle + courses 1-8
        ALL_LEVEL_NAMES[9:16],  # courses 9-15
        ALL_LEVEL_NAMES[16:],   # bowser + secrets
    ]

    for col, (header, names) in enumerate(zip(headers, groups)):
        x = col * col_w + 20
        h = font.render(header, True, WHITE)
        screen.blit(h, (x, 55))
        for i, name in enumerate(names):
            color = GOLD if name == current_name else (200, 200, 200)
            prefix = "> " if name == current_name else "  "
            txt = small.render(f"{prefix}{name}", True, color)
            screen.blit(txt, (x, 85 + i * 24))

    hint = small.render("Press M to close map", True, (160, 160, 160))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))
    pygame.display.flip()


# ============================================================
# GAME LOOP
# ============================================================

def game():
    # Build ALL levels
    levels = {
        "Peach's Castle": make_castle(),
        # 15 courses
        "Bob-omb Battlefield": make_bobomb_battlefield(),
        "Whomp's Fortress": make_whomps_fortress(),
        "Jolly Roger Bay": make_jolly_roger_bay(),
        "Cool Cool Mountain": make_cool_cool_mountain(),
        "Big Boo's Haunt": make_big_boos_haunt(),
        "Hazy Maze Cave": make_hazy_maze_cave(),
        "Lethal Lava Land": make_lethal_lava_land(),
        "Shifting Sand Land": make_shifting_sand_land(),
        "Dire Dire Docks": make_dire_dire_docks(),
        "Snowman's Land": make_snowmans_land(),
        "Wet-Dry World": make_wet_dry_world(),
        "Tall Tall Mountain": make_tall_tall_mountain(),
        "Tiny-Huge Island": make_tiny_huge_island(),
        "Tick Tock Clock": make_tick_tock_clock(),
        "Rainbow Ride": make_rainbow_ride(),
        # 3 Bowser stages
        "Bowser Dark World": make_bowser_dark_world(),
        "Bowser Fire Sea": make_bowser_fire_sea(),
        "Bowser in the Sky": make_bowser_in_the_sky(),
        # 5 secret areas
        "Wing Cap Tower": make_wing_cap_tower(),
        "Metal Cap Cavern": make_metal_cap_cavern(),
        "Vanish Cap Ruins": make_vanish_cap_ruins(),
        "Secret Aquarium": make_secret_aquarium(),
        "Princess Slide": make_princess_slide(),
    }

    current_level = levels["Peach's Castle"]
    mario = Mario()
    mario.x, mario.y, mario.z = current_level.entry_point

    cam = {"x": mario.x, "y": mario.y + 200, "z": mario.z + 400}
    show_map = False

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
                if e.key == pygame.K_m:
                    show_map = not show_map

        if show_map:
            draw_map_screen(current_level.name)
            continue

        keys = pygame.key.get_pressed()
        dx, dz = 0, 0
        if keys[pygame.K_w]:
            dz -= MOVE_SPEED
        if keys[pygame.K_s]:
            dz += MOVE_SPEED
        if keys[pygame.K_a]:
            dx -= MOVE_SPEED
        if keys[pygame.K_d]:
            dx += MOVE_SPEED

        # Normalize diagonal movement
        if dx and dz:
            factor = 0.707  # 1/sqrt(2)
            dx *= factor
            dz *= factor

        mario.x += dx
        mario.z += dz
        mario.update(current_level.floor_y)

        # Collectibles
        for coin in current_level.coins[:]:
            if math.dist((mario.x, mario.z), (coin.x, coin.z)) < 40 and abs(mario.y - coin.y) < 40:
                current_level.coins.remove(coin)
                mario.coins += 1
        for star in current_level.stars[:]:
            if math.dist((mario.x, mario.z), (star.x, star.z)) < 50 and abs(mario.y - star.y) < 50:
                current_level.stars.remove(star)
                mario.stars += 1

        # Animate collectibles
        for coin in current_level.coins:
            coin.animate()
        for star in current_level.stars:
            star.animate()

        # Portal checks
        for portal in current_level.portals:
            x1, x2, z1, z2 = portal["rect"]
            if x1 <= mario.x <= x2 and z1 <= mario.z <= z2:
                target = levels.get(portal["target"])
                if target:
                    current_level = target
                    mario.x, mario.y, mario.z = portal["spawn"]
                break

        # Camera follow (smooth)
        cam["x"] += (mario.x - cam["x"]) * 0.08
        cam["y"] += (mario.y + 200 - cam["y"]) * 0.06
        cam["z"] += (mario.z + 400 - cam["z"]) * 0.08

        # Render
        screen.fill(current_level.sky_color)

        polys = []
        render(current_level.terrain, cam, polys)
        render(mario, cam, polys)
        for coin in current_level.coins:
            render(coin, cam, polys)
        for star in current_level.stars:
            render(star, cam, polys)

        polys.sort(reverse=True)
        for _, pts, col in polys:
            if len(pts) >= 3:
                pygame.draw.polygon(screen, col, pts)

        draw_hud(mario, current_level.name, show_map)
        pygame.display.flip()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    while True:
        menu()
        dear_card()
        game()
