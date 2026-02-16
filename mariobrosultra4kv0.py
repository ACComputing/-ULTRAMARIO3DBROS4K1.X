import pygame
import sys
import math

pygame.init()

# =====================================================
# CONFIG
# =====================================================

WIDTH, HEIGHT = 900, 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultra Mario 3D Bros")
clock = pygame.time.Clock()

# =====================================================
# COLORS
# =====================================================

SKY = (20, 20, 60)
WHITE = (255, 255, 255)
RED = (220, 20, 60)
BLUE = (0, 0, 205)
YELLOW = (255, 215, 0)
PARCHMENT = (245, 235, 205)
PARCHMENT_BORDER = (190, 150, 100)
INK = (70, 40, 25)

# =====================================================
# FADE SYSTEM
# =====================================================

def fade(mode="out", duration=300):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))

    t = 0
    while t < duration:
        dt = clock.tick(FPS)
        t += dt
        p = min(1, t/duration)

        alpha = int(255*p) if mode == "out" else int(255*(1-p))
        overlay.set_alpha(alpha)

        screen.blit(overlay, (0,0))
        pygame.display.flip()

# =====================================================
# TITLE SCREEN
# =====================================================

def title_screen():
    title_font = pygame.font.SysFont("Arial", 64, bold=True)
    small_font = pygame.font.SysFont("Arial", 20)
    pulse = 0

    while True:
        dt = clock.tick(FPS)
        pulse += dt/1000

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "start"

        screen.fill(SKY)

        # Big title
        screen.blit(
            title_font.render("ULTRA MARIO", True, RED),
            (WIDTH//2 - 240, 200)
        )
        screen.blit(
            title_font.render("3D BROS", True, BLUE),
            (WIDTH//2 - 160, 280)
        )

        # Pulsing prompt
        glow = 150 + int(100 * math.sin(pulse * 4))
        prompt = title_font.render("PRESS START", True, (glow, glow, 255))
        screen.blit(prompt, (WIDTH//2 - 220, 400))

        hint = small_font.render("ENTER / SPACE", True, WHITE)
        screen.blit(hint, (WIDTH//2 - 70, 500))

        pygame.display.flip()

# =====================================================
# DEAR MARIO LETTER
# =====================================================

def dear_mario():
    title_font = pygame.font.SysFont("Times New Roman", 36, bold=True)
    body_font = pygame.font.SysFont("Times New Roman", 26)
    small_font = pygame.font.SysFont("Arial", 18)

    lines = [
        "Dear Mario,",
        "",
        "Please come to Peach's Castle.",
        "I have baked a cake for you.",
        "",
        "Yours truly,",
        "Princess Toadstool"
    ]

    fade_val = 0

    while True:
        dt = clock.tick(FPS)
        fade_val = min(255, fade_val + dt*0.8)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "continue"

        screen.fill(SKY)

        card = pygame.Surface((600, 380), pygame.SRCALPHA)
        card.fill(PARCHMENT)
        pygame.draw.rect(card, PARCHMENT_BORDER, card.get_rect(), 6)

        y = 50
        for i, line in enumerate(lines):
            if i == 0:
                text = title_font.render(line, True, INK)
                card.blit(text, (50, y))
                y += 60
            else:
                text = body_font.render(line, True, INK)
                card.blit(text, (50, y))
                y += 35

        hint = small_font.render("PRESS START TO CONTINUE", True, INK)
        card.blit(hint, (150, 330))

        card.set_alpha(fade_val)
        screen.blit(card, (WIDTH//2 - 300, HEIGHT//2 - 190))

        pygame.display.flip()

# =====================================================
# MAIN LOOP
# =====================================================

while True:

    result = title_screen()
    if result == "quit":
        break

    fade("out")
    fade("in")

    letter = dear_mario()
    if letter == "quit":
        break

    fade("out")

    # Placeholder for game start
    screen.fill((0,0,0))
    pygame.display.flip()
    pygame.time.wait(800)

    fade("in")

pygame.quit()
sys.exit()
