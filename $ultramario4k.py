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

ROT_SPEED = 0.05
MOVE_SPEED = 12
JUMP_FORCE = 18
GRAVITY = 0.9

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SM64 PY PORT – COMPLETE")
clock = pygame.time.Clock()

# ============================================================
# COLORS
# ============================================================

DD_SKY = (20, 20, 60)
INDOOR_SKY = (12, 10, 18)

WHITE = (255, 255, 255)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)
BLUE = (0, 0, 205)
BROWN = (139, 69, 19)
GREEN = (30, 140, 30)
LIGHT_GREEN = (50, 200, 50)

PARCHMENT = (245, 235, 205)
PARCHMENT_BORDER = (190, 150, 100)
INK = (70, 40, 25)

# ============================================================
# 3D CORE
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
        s = len(self.verts)
        hw, hh, hd = w/2, h/2, d/2
        pts = [(-hw,-hh,-hd),(hw,-hh,-hd),(hw,hh,-hd),(-hw,hh,-hd),
               (-hw,-hh,hd),(hw,-hh,hd),(hw,hh,hd),(-hw,hh,hd)]
        for px,py,pz in pts:
            self.verts.append(Vec3(px+ox,py+oy,pz+oz))

        faces = [[0,1,2,3],[5,4,7,6],[4,0,3,7],[1,5,6,2],[3,2,6,7],[4,5,1,0]]
        for f in faces:
            self.faces.append(Face([i+s for i in f], col))

def render(mesh, cam, polys, bg):
    cy = math.cos(mesh.yaw)
    sy = math.sin(mesh.yaw)

    for face in mesh.faces:
        pts = []
        avgz = 0

        for i in face.idx:
            v = mesh.verts[i]

            rx = v.x*cy - v.z*sy
            rz = v.x*sy + v.z*cy
            ry = v.y

            wx = rx + mesh.x - cam["x"]
            wy = ry + mesh.y - cam["y"]
            wz = rz + mesh.z - cam["z"]

            cz = wz
            if cz <= 1:
                break

            scale = FOV/cz
            sx = wx*scale + WIDTH//2
            syy = -wy*scale + HEIGHT//2

            pts.append((sx,syy))
            avgz += cz
        else:
            avgz/=len(pts)
            polys.append((avgz, pts, face.col))

# ============================================================
# OBJECTS
# ============================================================

class Mario(Mesh):
    def __init__(self):
        super().__init__(0,0,400)
        self.dy = 0
        self.health = 100
        self.coins = 0
        self.cube(30,40,20,0,20,0,RED)

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
    def __init__(self,x,z):
        super().__init__(x,40,z)
        self.cube(20,5,20,0,0,0,YELLOW)

# ============================================================
# SCENES
# ============================================================

def make_outside():
    level = Mesh()
    level.cube(2000,20,2000,0,-10,0,GREEN)
    level.cube(400,200,300,0,100,0,(200,180,150))
    level.cube(200,180,20,0,90,250,(90,60,40))
    return level

def make_inside():
    level = Mesh()
    level.cube(700,10,700,0,-5,0,(200,200,200))
    level.cube(700,200,30,0,100,-350,(180,160,130))
    level.cube(700,200,30,0,100,350,(180,160,130))
    return level

# ============================================================
# UI
# ============================================================

def dear_card():
    title = pygame.font.SysFont("Times New Roman",34,bold=True)
    body = pygame.font.SysFont("Times New Roman",26)

    fade = 0
    while True:
        dt = clock.tick(FPS)
        fade = min(255, fade+dt*0.7)

        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                pygame.quit();sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN,pygame.K_SPACE):
                    return

        screen.fill(DD_SKY)

        card = pygame.Surface((560,360),pygame.SRCALPHA)
        card.fill(PARCHMENT)
        pygame.draw.rect(card,PARCHMENT_BORDER,card.get_rect(),6)

        card.blit(title.render("Dear Mario,",True,INK),(40,40))
        card.blit(body.render("You're invited to Peach's Castle.",True,INK),(40,100))
        card.blit(body.render("Please come right away!",True,INK),(40,140))

        card.set_alpha(fade)
        screen.blit(card,(120,120))
        pygame.display.flip()

# ============================================================
# GAME LOOP
# ============================================================

def game():
    mario = Mario()
    cam = {"x":0,"y":200,"z":800}

    scene = "outside"
    level = make_outside()
    coins = [Coin(randint(-300,300),randint(-200,400)) for _ in range(5)]

    font = pygame.font.SysFont("Arial",18)

    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                return
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_SPACE:
                    mario.jump()
                if e.key==pygame.K_ESCAPE:
                    return

        keys=pygame.key.get_pressed()
        if keys[pygame.K_w]: mario.z-=MOVE_SPEED
        if keys[pygame.K_s]: mario.z+=MOVE_SPEED
        if keys[pygame.K_a]: mario.x-=MOVE_SPEED
        if keys[pygame.K_d]: mario.x+=MOVE_SPEED

        mario.update()

        # coin pickup
        for c in coins[:]:
            if math.dist((mario.x,mario.z),(c.x,c.z))<40:
                coins.remove(c)
                mario.coins+=1

        screen.fill(DD_SKY if scene=="outside" else INDOOR_SKY)

        polys=[]
        render(level,cam,polys,DD_SKY)
        render(mario,cam,polys,DD_SKY)
        for c in coins:
            render(c,cam,polys,DD_SKY)

        polys.sort(reverse=True)
        for _,pts,col in polys:
            pygame.draw.polygon(screen,col,pts)

        hud = font.render(f"Coins: {mario.coins}",True,WHITE)
        screen.blit(hud,(20,20))

        pygame.display.flip()

# ============================================================
# MENU
# ============================================================

def menu():
    font = pygame.font.SysFont("Arial",40,bold=True)
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                pygame.quit();sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN,pygame.K_SPACE):
                    return
        screen.fill(DD_SKY)
        screen.blit(font.render("PRESS START",True,WHITE),(260,260))
        pygame.display.flip()

# ============================================================
# MAIN
# ============================================================

while True:
    menu()
    dear_card()
    game()
