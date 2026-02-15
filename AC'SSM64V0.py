import pygame
import math
import sys
from random import randint

# ============================================================
#  AC'S SM64 PY PORT 1.X - program.py
#  Title Menu (SM64-ish) -> Peach's Castle gameplay
# ============================================================

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 500
VIEW_DISTANCE = 5000

DEFAULT_ROTATION_SPEED = 0.05
DEFAULT_MOVE_SPEED = 12
JUMP_FORCE = 18
GRAVITY = 0.9
COIN_ROTATION_SPEED = 0.1

# --- COLORS ---
DD_SKY = (20, 20, 60)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)
BLUE = (0, 0, 205)
SKIN = (255, 204, 153)
BROWN = (139, 69, 19)
MUSTACHE_BLACK = (20, 20, 20)
BUTTON_GOLD = (255, 215, 0)
EYE_BLUE = (0, 128, 255)
YELLOW = (255, 255, 0)
METAL_GREY = (160, 170, 180)
CHECKER_LIGHT = (50, 200, 50)
CHECKER_DARK = (30, 140, 30)
GOOMBA_BROWN = (139, 90, 43)
GOOMBA_EYE = (255, 255, 255)
GOOMBA_PUPIL = (0, 0, 0)
COIN_COLOR = (255, 215, 0)
HEALTH_BAR = (220, 20, 60)

# --- 3D MATH UTILITIES ---

class Vector3:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Face:
    __slots__ = ('indices', 'color', 'avg_z', 'normal')
    def __init__(self, indices, color):
        self.indices = indices
        self.color = color
        self.avg_z = 0
        self.normal = None

def normalize(vx, vy, vz):
    length = math.sqrt(vx*vx + vy*vy + vz*vz)
    if length == 0:
        return (0, 0, 1)
    return (vx/length, vy/length, vz/length)

def cross(ax, ay, az, bx, by, bz):
    return (ay*bz - az*by, az*bx - ax*bz, ax*by - ay*bx)

# --- BASE MESH CLASS ---

class Mesh:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = 0
        self.vertices = []
        self.faces = []
        self.active = True

    def add_cube(self, w, h, d, offset_x, offset_y, offset_z, color):
        """Add a cube to the mesh at local offset."""
        start_idx = len(self.vertices)
        hw, hh, hd = w/2, h/2, d/2
        corners = [
            (-hw, -hh, -hd), ( hw, -hh, -hd), ( hw,  hh, -hd), (-hw,  hh, -hd), # back
            (-hw, -hh,  hd), ( hw, -hh,  hd), ( hw,  hh,  hd), (-hw,  hh,  hd)  # front
        ]
        for cx, cy, cz in corners:
            self.vertices.append(Vector3(cx + offset_x, cy + offset_y, cz + offset_z))

        # Face definitions (indices relative to start_idx)
        cube_faces = [
            ([0,1,2,3], color), # back
            ([5,4,7,6], color), # front
            ([4,0,3,7], color), # left
            ([1,5,6,2], color), # right
            ([3,2,6,7], color), # top
            ([4,5,1,0], color)  # bottom
        ]
        for idx_list, col in cube_faces:
            shifted = [i + start_idx for i in idx_list]
            face = Face(shifted, col)
            # Precompute face normal (not used directly, but kept for future)
            v0 = self.vertices[shifted[0]]
            v1 = self.vertices[shifted[1]]
            v2 = self.vertices[shifted[2]]
            ax, ay, az = v1.x - v0.x, v1.y - v0.y, v1.z - v0.z
            bx, by, bz = v2.x - v0.x, v2.y - v0.y, v2.z - v0.z
            nx, ny, nz = cross(ax, ay, az, bx, by, bz)
            face.normal = normalize(nx, ny, nz)
            self.faces.append(face)

# --- SPECIFIC GAME OBJECTS ---

class Mario(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.dy = 0
        self.health = 100
        self.coins = 0
        self.build_model()

    def build_model(self):
        # Feet
        self.add_cube(10, 8, 14, -6, -25, -2, BROWN)
        self.add_cube(10, 8, 14,  6, -25, -2, BROWN)
        # Legs
        self.add_cube(8, 12, 8, -6, -15, 0, BLUE)
        self.add_cube(8, 12, 8,  6, -15, 0, BLUE)
        # Body
        self.add_cube(20, 10, 14, 0, -4, 0, BLUE)
        self.add_cube(22, 14, 14, 0,  8, 0, RED)
        self.add_cube(2, 2, 1, -5, 4, -8, BUTTON_GOLD)
        self.add_cube(2, 2, 1,  5, 4, -8, BUTTON_GOLD)
        # Arms
        self.add_cube(8, 8, 8, -16, 12, 0, RED)
        self.add_cube(6, 12, 6, -16, 2, 0, RED)
        self.add_cube(7, 7, 7, -16, -8, 0, WHITE)
        self.add_cube(8, 8, 8,  16, 12, 0, RED)
        self.add_cube(6, 12, 6,  16, 2, 0, RED)
        self.add_cube(7, 7, 7,  16, -8, 0, WHITE)
        # Head
        self.add_cube(18, 16, 18, 0, 22, 0, SKIN)
        self.add_cube(20, 6, 20, 0, 32, 0, RED)
        self.add_cube(24, 2, 24, 0, 29, -4, RED)
        # Face features
        self.add_cube(4, 4, 4, 0, 22, -10, SKIN)
        self.add_cube(10, 3, 2, 0, 18, -10, MUSTACHE_BLACK)
        self.add_cube(4, 8, 4, -9, 22, -2, BROWN)
        self.add_cube(4, 8, 4,  9, 22, -2, BROWN)
        self.add_cube(18, 10, 6, 0, 22, 8, BROWN)
        # Eyes
        self.add_cube(4, 4, 1, -6, 24, -9, WHITE)
        self.add_cube(2, 2, 1, -5, 24, -10, EYE_BLUE)
        self.add_cube(4, 4, 1,  6, 24, -9, WHITE)
        self.add_cube(2, 2, 1,  5, 24, -10, EYE_BLUE)

    def update(self, dt):
        self.dy -= GRAVITY * (dt / 16.67)
        self.y += self.dy
        if self.y < 0:
            self.y = 0
            self.dy = 0
        if self.y == 0 and self.dy <= 0:
            self.dy = 0

    def jump(self):
        if self.y == 0:
            self.dy = JUMP_FORCE

    def move(self, dx, dz):
        self.x += dx
        self.z += dz

class Coin(Mesh):
    """Simple rotating coin."""
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.angle = 0
        self.collected = False
        self.build_coin()

    def build_coin(self):
        self.add_cube(12, 2, 12, 0, 0, 0, YELLOW)
        self.add_cube(10, 2, 10, 0, 2, 0, YELLOW)
        self.add_cube(8, 2, 8, 0, 4, 0, YELLOW)

    def update(self):
        self.angle += COIN_ROTATION_SPEED
        if self.angle > 2*math.pi:
            self.angle -= 2*math.pi
        self.yaw = self.angle

class Goomba(Mesh):
    """Simple enemy that walks back and forth."""
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.direction = 1
        self.speed = 2
        self.health = 1
        self.build_goomba()

    def build_goomba(self):
        self.add_cube(20, 15, 20, 0, 10, 0, GOOMBA_BROWN)
        self.add_cube(24, 10, 24, 0, 20, 0, (160, 82, 45))
        self.add_cube(4, 4, 4, -6, 22, 12, WHITE)
        self.add_cube(4, 4, 4,  6, 22, 12, WHITE)
        self.add_cube(2, 2, 2, -6, 22, 14, BLACK)
        self.add_cube(2, 2, 2,  6, 22, 14, BLACK)
        self.add_cube(8, 4, 12, -8, 0, 0, BROWN)
        self.add_cube(8, 4, 12,  8, 0, 0, BROWN)

    def update(self, dt):
        self.x += self.direction * self.speed * (dt / 16.67)
        if self.x > 600:
            self.direction = -1
        elif self.x < -600:
            self.direction = 1

class Level(Mesh):
    def __init__(self):
        super().__init__(0, 0, 0)
        self.build_castle()

    def build_castle(self):
        """Construct Peach's Castle using cubes."""
        ground_size = 2000
        self.add_cube(ground_size, 20, ground_size, 0, -10, 0, (30, 60, 30))

        # Main Keep
        self.add_cube(400, 200, 300, 0, 90, 0, (200, 180, 150))
        self.add_cube(420, 40, 320, 0, 180, 0, (150, 120, 100))

        for i in range(4):
            size = 300 - i*40
            y = 200 + i*20
            self.add_cube(size, 20, size, 0, y, 0, (180, 120, 80))

        self.add_cube(40, 80, 40, 0, 280, 0, (220, 180, 140))
        self.add_cube(20, 40, 20, 0, 340, 0, YELLOW)

        # Towers
        tower_positions = [(-500, -400), (500, -400), (-500, 400), (500, 400)]
        for tx, tz in tower_positions:
            self.add_cube(150, 180, 150, tx, 70, tz, (200, 180, 150))
            for i in range(3):
                size = 130 - i*20
                y = 160 + i*15
                self.add_cube(size, 15, size, tx, y, tz, (150, 120, 100))
            self.add_cube(30, 60, 30, tx, 210, tz, (220, 180, 140))
            self.add_cube(15, 30, 15, tx, 250, tz, YELLOW)

        # Walls
        self.add_cube(1000, 120, 50, 0, 50, 600, (180, 160, 130))
        self.add_cube(800, 80, 40, 0, 20, 620, (150, 120, 100))
        self.add_cube(50, 200, 50, -150, 100, 620, (100, 80, 60))
        self.add_cube(50, 200, 50,  150, 100, 620, (100, 80, 60))
        self.add_cube(350, 30, 30, 0, 180, 620, (120, 90, 70))

        self.add_cube(1000, 120, 50, 0, 50, -600, (180, 160, 130))
        self.add_cube(50, 120, 1200, 600, 50, 0, (180, 160, 130))
        self.add_cube(50, 120, 1200, -600, 50, 0, (180, 160, 130))

        # Windows
        for y in [30, 90, 150]:
            self.add_cube(60, 10, 10, -120, y, 160, (255, 255, 200))
            self.add_cube(60, 10, 10,  120, y, 160, (255, 255, 200))

        # Flags
        for tx, tz in tower_positions:
            self.add_cube(10, 40, 5, tx+30, 220, tz+30, RED)
            self.add_cube(5, 10, 10, tx+30, 260, tz+30, YELLOW)

        # Floating star
        self.add_cube(40, 40, 10, 0, 400, 0, YELLOW)
        self.add_cube(10, 60, 10, 0, 400, 0, YELLOW)
        self.add_cube(60, 10, 10, 0, 400, 0, YELLOW)

# --- MAIN RENDERER ---

def render_mesh(mesh, cam, render_list):
    if not mesh.active:
        return

    world_x, world_y, world_z = mesh.x, mesh.y, mesh.z
    yaw = mesh.yaw

    c_yaw = math.cos(yaw)
    s_yaw = math.sin(yaw)

    cx, cy = cam['cx'], cam['cy']
    cam_x, cam_y, cam_z = cam['x'], cam['y'], cam['z']
    cam_yaw = cam['yaw']

    c_cam = math.cos(-cam_yaw)
    s_cam = math.sin(-cam_yaw)

    for face in mesh.faces:
        cam_verts = []
        valid = True
        for idx in face.indices:
            v = mesh.vertices[idx]

            # Object rotation
            rx = v.x * c_yaw - v.z * s_yaw
            rz = v.x * s_yaw + v.z * c_yaw
            ry = v.y

            # World
            wx = rx + world_x
            wy = ry + world_y
            wz = rz + world_z

            # Camera translate
            tx = wx - cam_x
            ty = wy - cam_y
            tz = wz - cam_z

            # Camera yaw rotate
            dx = tx * c_cam - tz * s_cam
            dz = tx * s_cam + tz * c_cam
            dy = ty

            if dz < 1:
                valid = False
                break
            cam_verts.append((dx, dy, dz))

        if not valid or len(cam_verts) < 3:
            continue

        screen_pts = []
        avg_z = 0
        for dx, dy, dz in cam_verts:
            scale = FOV / dz
            sx = int(dx * scale + cx)
            sy = int(-dy * scale + cy)
            screen_pts.append((sx, sy))
            avg_z += dz
        avg_z /= len(cam_verts)

        # Backface cull (signed area in screen space)
        area = 0
        n = len(screen_pts)
        for i in range(n):
            x1, y1 = screen_pts[i]
            x2, y2 = screen_pts[(i+1) % n]
            area += (x2 - x1) * (y2 + y1)
        if area <= 0:
            continue

        # Simple frustum-ish: skip if fully offscreen
        off_screen = True
        for sx, sy in screen_pts:
            if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                off_screen = False
                break
        if off_screen:
            continue

        render_list.append({
            'poly': screen_pts,
            'depth': avg_z,
            'color': face.color
        })

# ============================================================
#  GAME LOOP (your original main loop) wrapped in a function
# ============================================================

def run_game(screen, clock, settings):
    """Runs the Peach's Castle gameplay. Returns 'menu' to go back, or 'quit'."""
    # Create game objects
    mario = Mario(0, 20, 0)
    level = Level()
    coins = [Coin(randint(-500, 500), 50, randint(-500, 500)) for _ in range(5)]
    goombas = [Goomba(randint(-400, 400), 0, randint(-400, 400)) for _ in range(3)]

    # Camera
    camera = {
        'x': 0, 'y': 300, 'z': 800,
        'yaw': 0, 'pitch': 0.2,
        'cx': WIDTH // 2, 'cy': HEIGHT // 2
    }

    small_font = pygame.font.SysFont('Arial', 18)

    coins_collected = 0
    mario_health = 100

    running = True
    while running:
        dt = clock.tick(FPS)
        if dt > 50:
            dt = 16

        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    mario.jump()
                if event.key == pygame.K_ESCAPE:
                    # ESC returns to menu instead of hard quitting
                    return "menu"

        keys = pygame.key.get_pressed()

        # --- CAMERA ROTATION ---
        if keys[pygame.K_a]:
            camera['yaw'] -= settings['rotation_speed']
        if keys[pygame.K_d]:
            camera['yaw'] += settings['rotation_speed']

        # --- MARIO MOVEMENT ---
        move_x, move_z = 0, 0
        if keys[pygame.K_w]:
            move_z -= settings['move_speed']
        if keys[pygame.K_s]:
            move_z += settings['move_speed']
        if keys[pygame.K_q]:
            move_x -= settings['move_speed']
        if keys[pygame.K_e]:
            move_x += settings['move_speed']

        if move_x != 0 or move_z != 0:
            world_dx = move_x * math.cos(camera['yaw']) - move_z * math.sin(camera['yaw'])
            world_dz = move_x * math.sin(camera['yaw']) + move_z * math.cos(camera['yaw'])
            mario.move(world_dx, world_dz)
            mario.yaw = math.atan2(world_dx, world_dz)

        # --- PHYSICS UPDATE ---
        mario.update(dt)
        for coin in coins:
            coin.update()
        for goomba in goombas:
            goomba.update(dt)

        # --- COLLISIONS (distance-based) ---
        for coin in coins[:]:
            if not coin.collected:
                dx = mario.x - coin.x
                dz = mario.z - coin.z
                dy = mario.y - coin.y
                dist = math.sqrt(dx*dx + dz*dz + dy*dy)
                if dist < 40:
                    coin.collected = True
                    coins_collected += 1
                    mario.coins += 1
        coins = [c for c in coins if not c.collected]

        for goomba in goombas[:]:
            dx = mario.x - goomba.x
            dz = mario.z - goomba.z
            dy = mario.y - goomba.y
            dist = math.sqrt(dx*dx + dz*dz + dy*dy)
            if dist < 40:
                mario_health -= 10
                if mario_health <= 0:
                    # game over -> back to menu
                    return "menu"
                mario.x += dx * 2
                mario.z += dz * 2
                goomba.health -= 1
                if goomba.health <= 0:
                    goombas.remove(goomba)

        # Keep bounds
        if mario.x > 900: mario.x = 900
        if mario.x < -900: mario.x = -900
        if mario.z > 900: mario.z = 900
        if mario.z < -900: mario.z = -900

        # --- CAMERA FOLLOW ---
        target_cam_x = mario.x - math.sin(camera['yaw']) * 500
        target_cam_z = mario.z - math.cos(camera['yaw']) * 500
        target_cam_y = mario.y + 200

        camera['x'] += (target_cam_x - camera['x']) * 0.08
        camera['y'] += (target_cam_y - camera['y']) * 0.08
        camera['z'] += (target_cam_z - camera['z']) * 0.08

        # --- RENDER ---
        screen.fill(DD_SKY)
        render_list = []

        render_mesh(level, camera, render_list)
        render_mesh(mario, camera, render_list)
        for coin in coins:
            render_mesh(coin, camera, render_list)
        for goomba in goombas:
            render_mesh(goomba, camera, render_list)

        render_list.sort(key=lambda x: x['depth'], reverse=True)

        for item in render_list:
            depth = item['depth']
            fog = min(1.0, depth / VIEW_DISTANCE)
            r, g, b = item['color']
            sr, sg, sb = DD_SKY
            fr = int(r + (sr - r) * fog)
            fg = int(g + (sg - g) * fog)
            fb = int(b + (sb - b) * fog)
            pygame.draw.polygon(screen, (fr, fg, fb), item['poly'])

        # --- HUD ---
        hud_surf = pygame.Surface((WIDTH, 60))
        hud_surf.set_alpha(180)
        hud_surf.fill((0, 0, 0))
        screen.blit(hud_surf, (0, HEIGHT - 60))

        coin_text = small_font.render(f"Coins: {coins_collected}", True, YELLOW)
        screen.blit(coin_text, (20, HEIGHT - 50))

        pygame.draw.rect(screen, (100, 0, 0), (20, HEIGHT - 30, 200, 20))
        pygame.draw.rect(screen, HEALTH_BAR, (20, HEIGHT - 30, int(200 * mario_health / 100), 20))

        if settings['show_fps']:
            fps_text = small_font.render(f"FPS: {int(clock.get_fps())}", True, CHECKER_LIGHT)
            screen.blit(fps_text, (WIDTH - 110, HEIGHT - 50))

        castle_text = small_font.render("Peach's Castle", True, (255, 200, 200))
        screen.blit(castle_text, (WIDTH - 250, HEIGHT - 30))

        pygame.display.flip()

    return "menu"


# ============================================================
#  MAIN MENU (SM64-ish)
# ============================================================

def draw_centered_text(surface, text, font, y, color=WHITE):
    s = font.render(text, True, color)
    rect = s.get_rect(center=(WIDTH // 2, y))
    surface.blit(s, rect)

def menu_loop(screen, clock, settings):
    """Returns 'start' to run game, or 'quit'."""
    title_font = pygame.font.SysFont('Arial', 44, bold=True)
    big_font = pygame.font.SysFont('Arial', 28, bold=True)
    small_font = pygame.font.SysFont('Arial', 18)

    state = "title"   # 'title' -> 'main' -> 'options'
    selected = 0
    main_items = ["START GAME", "OPTIONS", "QUIT"]
    opt_selected = 0

    pulse_t = 0.0

    while True:
        dt = clock.tick(FPS)
        pulse_t += dt / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if state == "title":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        state = "main"
                        selected = 0
                    if event.key == pygame.K_ESCAPE:
                        return "quit"

                elif state == "main":
                    if event.key == pygame.K_ESCAPE:
                        state = "title"
                    elif event.key == pygame.K_UP:
                        selected = (selected - 1) % len(main_items)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(main_items)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        choice = main_items[selected]
                        if choice == "START GAME":
                            return "start"
                        elif choice == "OPTIONS":
                            state = "options"
                            opt_selected = 0
                        elif choice == "QUIT":
                            return "quit"

                elif state == "options":
                    if event.key == pygame.K_ESCAPE:
                        state = "main"
                    elif event.key == pygame.K_UP:
                        opt_selected = (opt_selected - 1) % 5
                    elif event.key == pygame.K_DOWN:
                        opt_selected = (opt_selected + 1) % 5
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
                        # Options list:
                        # 0: Show FPS toggle
                        # 1: Rotation speed
                        # 2: Move speed
                        # 3: Reset defaults
                        # 4: Back
                        if opt_selected == 0:
                            settings['show_fps'] = not settings['show_fps']
                        elif opt_selected == 1:
                            delta = 0.01 if event.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE) else -0.01
                            settings['rotation_speed'] = max(0.01, min(0.20, settings['rotation_speed'] + delta))
                        elif opt_selected == 2:
                            delta = 1 if event.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE) else -1
                            settings['move_speed'] = max(4, min(30, settings['move_speed'] + delta))
                        elif opt_selected == 3:
                            settings['show_fps'] = True
                            settings['rotation_speed'] = DEFAULT_ROTATION_SPEED
                            settings['move_speed'] = DEFAULT_MOVE_SPEED
                        elif opt_selected == 4:
                            state = "main"

        # --- DRAW ---
        screen.fill(DD_SKY)

        # A subtle "checker" floor band for vibe
        for x in range(0, WIDTH, 40):
            col = CHECKER_LIGHT if (x // 40) % 2 == 0 else CHECKER_DARK
            pygame.draw.rect(screen, col, (x, HEIGHT - 120, 40, 120))

        # Title text
        draw_centered_text(screen, "AC'S SM64 PY PORT 1.X", title_font, 110, (255, 210, 210))
        draw_centered_text(screen, "PEACH'S CASTLE", big_font, 165, (255, 240, 200))

        if state == "title":
            # pulsating prompt
            pulse = 0.5 + 0.5 * math.sin(pulse_t * 4.0)
            c = int(180 + 75 * pulse)
            draw_centered_text(screen, "PRESS START", big_font, 320, (c, c, 255))
            draw_centered_text(screen, "ENTER / SPACE = Start   |   ESC = Quit", small_font, 520, (220, 220, 220))

        elif state == "main":
            y0 = 280
            for i, item in enumerate(main_items):
                is_sel = (i == selected)
                col = (255, 255, 0) if is_sel else (230, 230, 230)
                prefix = "▶ " if is_sel else "  "
                draw_centered_text(screen, prefix + item, big_font, y0 + i * 45, col)

            draw_centered_text(screen, "UP/DOWN to select   |   ENTER to confirm   |   ESC to title", small_font, 520, (220, 220, 220))

        elif state == "options":
            opts = [
                f"SHOW FPS: {'ON' if settings['show_fps'] else 'OFF'}",
                f"ROTATION SPEED: {settings['rotation_speed']:.2f}",
                f"MOVE SPEED: {settings['move_speed']}",
                "RESET DEFAULTS",
                "BACK"
            ]
            y0 = 250
            for i, item in enumerate(opts):
                is_sel = (i == opt_selected)
                col = (255, 255, 0) if is_sel else (230, 230, 230)
                prefix = "▶ " if is_sel else "  "
                draw_centered_text(screen, prefix + item, big_font, y0 + i * 45, col)

            draw_centered_text(screen, "LEFT/RIGHT or ENTER to change   |   ESC to return", small_font, 520, (220, 220, 220))

        pygame.display.flip()


# ============================================================
#  PROGRAM ENTRYPOINT
# ============================================================

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AC'S SM64 PY PORT 1.X")
    clock = pygame.time.Clock()

    settings = {
        'show_fps': True,
        'rotation_speed': DEFAULT_ROTATION_SPEED,
        'move_speed': DEFAULT_MOVE_SPEED,
    }

    while True:
        action = menu_loop(screen, clock, settings)
        if action == "quit":
            break
        if action == "start":
            result = run_game(screen, clock, settings)
            if result == "quit":
                break
            # else goes back to menu

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
