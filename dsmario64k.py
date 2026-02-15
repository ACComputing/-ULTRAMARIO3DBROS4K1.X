import pygame
import math
import sys
from random import randint

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 500
VIEW_DISTANCE = 5000
ROTATION_SPEED = 0.05
MOVE_SPEED = 12
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
            # Precompute face normal for backface culling (world space, not rotated yet)
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
        # Simplified Mario model (you can expand)
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
        self.dy -= GRAVITY * (dt / 16.67)  # scale by frame time
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
        # Build a flat octagon to look like a coin
        self.build_coin()

    def build_coin(self):
        # Simplified as a thin cylinder (cube stack)
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
        # Body
        self.add_cube(20, 15, 20, 0, 10, 0, GOOMBA_BROWN)
        # Head (mushroom top)
        self.add_cube(24, 10, 24, 0, 20, 0, (160, 82, 45))
        # Eyes
        self.add_cube(4, 4, 4, -6, 22, 12, WHITE)
        self.add_cube(4, 4, 4,  6, 22, 12, WHITE)
        self.add_cube(2, 2, 2, -6, 22, 14, BLACK)
        self.add_cube(2, 2, 2,  6, 22, 14, BLACK)
        # Feet
        self.add_cube(8, 4, 12, -8, 0, 0, BROWN)
        self.add_cube(8, 4, 12,  8, 0, 0, BROWN)

    def update(self, dt):
        self.x += self.direction * self.speed * (dt / 16.67)
        # Simple patrol boundary
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
        # --- Ground / Courtyard ---
        ground_size = 2000
        self.add_cube(ground_size, 20, ground_size, 0, -10, 0, (30, 60, 30))

        # --- Main Keep ---
        # Base
        self.add_cube(400, 200, 300, 0, 90, 0, (200, 180, 150))  # walls
        self.add_cube(420, 40, 320, 0, 180, 0, (150, 120, 100))  # roof trim
        # Roof (pyramid shape – we'll use stacked cubes)
        for i in range(4):
            size = 300 - i*40
            y = 200 + i*20
            self.add_cube(size, 20, size, 0, y, 0, (180, 120, 80))
        # Spire
        self.add_cube(40, 80, 40, 0, 280, 0, (220, 180, 140))
        self.add_cube(20, 40, 20, 0, 340, 0, YELLOW)  # golden top

        # --- Towers (four corner towers) ---
        tower_positions = [(-500, -400), (500, -400), (-500, 400), (500, 400)]
        for tx, tz in tower_positions:
            # Base
            self.add_cube(150, 180, 150, tx, 70, tz, (200, 180, 150))
            # Roof
            for i in range(3):
                size = 130 - i*20
                y = 160 + i*15
                self.add_cube(size, 15, size, tx, y, tz, (150, 120, 100))
            # Spire
            self.add_cube(30, 60, 30, tx, 210, tz, (220, 180, 140))
            self.add_cube(15, 30, 15, tx, 250, tz, YELLOW)

        # --- Connecting Walls ---
        # Front wall (with gate)
        self.add_cube(1000, 120, 50, 0, 50, 600, (180, 160, 130))
        self.add_cube(800, 80, 40, 0, 20, 620, (150, 120, 100))  # walkway
        # Gate opening (two pillars)
        self.add_cube(50, 200, 50, -150, 100, 620, (100, 80, 60))
        self.add_cube(50, 200, 50,  150, 100, 620, (100, 80, 60))
        # Arch (cube)
        self.add_cube(350, 30, 30, 0, 180, 620, (120, 90, 70))

        # Back wall
        self.add_cube(1000, 120, 50, 0, 50, -600, (180, 160, 130))

        # Side walls
        self.add_cube(50, 120, 1200, 600, 50, 0, (180, 160, 130))
        self.add_cube(50, 120, 1200, -600, 50, 0, (180, 160, 130))

        # --- Details ---
        # Windows on main keep
        for y in [30, 90, 150]:
            self.add_cube(60, 10, 10, -120, y, 160, (255, 255, 200))
            self.add_cube(60, 10, 10,  120, y, 160, (255, 255, 200))
        # Flags on towers
        for tx, tz in tower_positions:
            self.add_cube(10, 40, 5, tx+30, 220, tz+30, RED)
            self.add_cube(5, 10, 10, tx+30, 260, tz+30, YELLOW)

        # --- Floating star (like in SM64) ---
        self.add_cube(40, 40, 10, 0, 400, 0, YELLOW)
        self.add_cube(10, 60, 10, 0, 400, 0, YELLOW)
        self.add_cube(60, 10, 10, 0, 400, 0, YELLOW)

# --- COLLISION DETECTION (simple AABB) ---
def aabb_collide(obj1, obj2, margin=0):
    # Placeholder – actual collision would use bounding boxes
    return False

# --- MAIN RENDERER ---
def project_vertex(vx, vy, vz, cam_x, cam_y, cam_z, cam_yaw, cam_pitch, fov, cx, cy):
    """Transform world vertex to camera space and project to screen."""
    # Translate
    tx = vx - cam_x
    ty = vy - cam_y
    tz = vz - cam_z

    # Rotate around Y (yaw)
    c_y = math.cos(-cam_yaw)
    s_y = math.sin(-cam_yaw)
    rx = tx * c_y - tz * s_y
    rz = tx * s_y + tz * c_y
    ry = ty

    # Rotate around X (pitch) – simplified, we'll skip for clarity
    # For now, keep pitch at 0 for simplicity

    if rz < 1:  # near clip
        return None
    scale = fov / rz
    sx = int(rx * scale + cx)
    sy = int(-ry * scale + cy)
    return (sx, sy, rz)

def render_mesh(mesh, cam, render_list):
    """Process a mesh: transform vertices, cull, and add to render list."""
    if not mesh.active:
        return
    world_x, world_y, world_z = mesh.x, mesh.y, mesh.z
    yaw = mesh.yaw

    # Precompute object rotation
    c_yaw = math.cos(yaw)
    s_yaw = math.sin(yaw)

    # Camera params
    cx, cy = cam['cx'], cam['cy']
    cam_x, cam_y, cam_z = cam['x'], cam['y'], cam['z']
    cam_yaw = cam['yaw']
    # For now, we ignore pitch for simplicity

    # Precompute camera rotation
    c_cam = math.cos(-cam_yaw)
    s_cam = math.sin(-cam_yaw)

    for face in mesh.faces:
        # 1. Transform vertices to camera space
        cam_verts = []
        valid = True
        for idx in face.indices:
            v = mesh.vertices[idx]
            # Object rotation
            rx = v.x * c_yaw - v.z * s_yaw
            rz = v.x * s_yaw + v.z * c_yaw
            ry = v.y
            # World position
            wx = rx + world_x
            wy = ry + world_y
            wz = rz + world_z
            # Camera transform
            tx = wx - cam_x
            ty = wy - cam_y
            tz = wz - cam_z
            # Rotate by camera
            dx = tx * c_cam - tz * s_cam
            dz = tx * s_cam + tz * c_cam
            dy = ty
            if dz < 1:
                valid = False
                break
            cam_verts.append((dx, dy, dz))

        if not valid or len(cam_verts) < 3:
            continue

        # 2. Backface culling in screen space (using projected area sign)
        # Project to screen
        screen_pts = []
        avg_z = 0
        for dx, dy, dz in cam_verts:
            scale = FOV / dz
            sx = int(dx * scale + cx)
            sy = int(-dy * scale + cy)
            screen_pts.append((sx, sy))
            avg_z += dz
        avg_z /= len(cam_verts)

        # Compute signed area
        area = 0
        n = len(screen_pts)
        for i in range(n):
            x1, y1 = screen_pts[i]
            x2, y2 = screen_pts[(i+1)%n]
            area += (x2 - x1) * (y2 + y1)
        if area <= 0:  # backface (clockwise in Pygame's coordinate system)
            continue

        # 3. Frustum culling (simple: check if all points are off-screen)
        off_screen = True
        for sx, sy in screen_pts:
            if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                off_screen = False
                break
        if off_screen:
            continue

        # 4. Add to render list
        render_list.append({
            'poly': screen_pts,
            'depth': avg_z,
            'color': face.color
        })

# --- GAME INITIALIZATION ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SUPER MARIO 64DD - PEACH'S CASTLE")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 24, bold=True)
    small_font = pygame.font.SysFont('Arial', 18)

    # Create game objects
    mario = Mario(0, 20, 0)
    level = Level()
    coins = [Coin(randint(-500,500), 50, randint(-500,500)) for _ in range(5)]
    goombas = [Goomba(randint(-400,400), 0, randint(-400,400)) for _ in range(3)]

    # Camera
    camera = {
        'x': 0, 'y': 300, 'z': 800,
        'yaw': 0, 'pitch': 0.2,
        'cx': WIDTH//2, 'cy': HEIGHT//2
    }

    # Game state
    coins_collected = 0
    mario_health = 100

    running = True
    while running:
        dt = clock.tick(FPS)
        # Cap dt to avoid large jumps
        if dt > 50:
            dt = 16

        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    mario.jump()
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()

        # --- CAMERA ROTATION ---
        if keys[pygame.K_a]:
            camera['yaw'] -= ROTATION_SPEED
        if keys[pygame.K_d]:
            camera['yaw'] += ROTATION_SPEED

        # --- MARIO MOVEMENT ---
        move_x, move_z = 0, 0
        if keys[pygame.K_w]:
            move_z -= MOVE_SPEED
        if keys[pygame.K_s]:
            move_z += MOVE_SPEED
        if keys[pygame.K_q]:
            move_x -= MOVE_SPEED
        if keys[pygame.K_e]:
            move_x += MOVE_SPEED

        if move_x != 0 or move_z != 0:
            # Camera-relative movement
            world_dx = move_x * math.cos(camera['yaw']) - move_z * math.sin(camera['yaw'])
            world_dz = move_x * math.sin(camera['yaw']) + move_z * math.cos(camera['yaw'])
            mario.move(world_dx, world_dz)
            # Rotate Mario to face movement direction
            if move_x != 0 or move_z != 0:
                mario.yaw = math.atan2(world_dx, world_dz)

        # --- PHYSICS UPDATE ---
        mario.update(dt)
        for coin in coins:
            coin.update()
        for goomba in goombas:
            goomba.update(dt)

        # --- COLLISION DETECTION (simple distance-based) ---
        # Mario vs coins
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

        # Mario vs goombas
        for goomba in goombas[:]:
            dx = mario.x - goomba.x
            dz = mario.z - goomba.z
            dy = mario.y - goomba.y
            dist = math.sqrt(dx*dx + dz*dz + dy*dy)
            if dist < 40:
                mario_health -= 10
                if mario_health <= 0:
                    print("Game Over!")
                    running = False
                # knockback
                mario.x += dx * 2
                mario.z += dz * 2
                goomba.health -= 1
                if goomba.health <= 0:
                    goombas.remove(goomba)

        # Keep Mario within castle bounds (approximate)
        margin = 400
        if mario.x > 900:
            mario.x = 900
        if mario.x < -900:
            mario.x = -900
        if mario.z > 900:
            mario.z = 900
        if mario.z < -900:
            mario.z = -900

        # --- CAMERA FOLLOW ---
        target_cam_x = mario.x - math.sin(camera['yaw']) * 500
        target_cam_z = mario.z - math.cos(camera['yaw']) * 500
        target_cam_y = mario.y + 200

        camera['x'] += (target_cam_x - camera['x']) * 0.08
        camera['y'] += (target_cam_y - camera['y']) * 0.08
        camera['z'] += (target_cam_z - camera['z']) * 0.08

        # --- RENDERING ---
        screen.fill(DD_SKY)

        render_list = []

        # Process all meshes
        render_mesh(level, camera, render_list)
        render_mesh(mario, camera, render_list)
        for coin in coins:
            render_mesh(coin, camera, render_list)
        for goomba in goombas:
            render_mesh(goomba, camera, render_list)

        # Sort by depth (far to near)
        render_list.sort(key=lambda x: x['depth'], reverse=True)

        # Draw polygons with fog
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
        hud_surf.fill((0,0,0))
        screen.blit(hud_surf, (0, HEIGHT-60))

        # Coin count
        coin_text = small_font.render(f"Coins: {coins_collected}", True, YELLOW)
        screen.blit(coin_text, (20, HEIGHT-50))

        # Health bar
        pygame.draw.rect(screen, (100,0,0), (20, HEIGHT-30, 200, 20))
        pygame.draw.rect(screen, HEALTH_BAR, (20, HEIGHT-30, int(200 * mario_health/100), 20))

        # FPS
        fps_text = small_font.render(f"FPS: {int(clock.get_fps())}", True, CHECKER_LIGHT)
        screen.blit(fps_text, (WIDTH-100, HEIGHT-50))

        # Castle name
        castle_text = small_font.render("Peach's Castle", True, (255, 200, 200))
        screen.blit(castle_text, (WIDTH-250, HEIGHT-30))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
