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
pygame.display.set_caption("AC'S SM64")
clock = pygame.time.Clock()

# =====================================================
# COLORS
# =====================================================

SKY = (25, 25, 80)
WHITE = (255, 255, 255)
RED = (220, 30, 30)
BLUE = (40, 90, 255)
YELLOW = (255, 220, 0)

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
        p = min(1, t / duration)

        alpha = int(255 * p) if mode == "out" else int(255 * (1 - p))
        overlay.set_alpha(alpha)

        screen.blit(overlay, (0, 0))
        pygame.display.flip()

# =====================================================
# MAIN MENU
# =====================================================

def main_menu():
    title_font = pygame.font.SysFont("Arial", 70, bold=True)
    press_font = pygame.font.SysFont("Arial", 36, bold=True)
    small_font = pygame.font.SysFont("Arial", 18)

    pulse = 0

    while True:
        dt = clock.tick(FPS)
        pulse += dt / 1000

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "start"

        screen.fill(SKY)

        # Big title
        title = title_font.render("AC'S SM64", True, RED)
        screen.blit(title, title.get_rect(center=(WIDTH//2, 200)))

        # Sub glow
        sub = title_font.render("SUPER MARIO 64", True, BLUE)
        screen.blit(sub, sub.get_rect(center=(WIDTH//2, 290)))

        # Pulsing PRESS START
        glow = 180 + int(70 * math.sin(pulse * 4))
        press = press_font.render("PRESS START", True, (glow, glow, 255))
        screen.blit(press, press.get_rect(center=(WIDTH//2, 420)))

        hint = small_font.render("ENTER / SPACE", True, WHITE)
        screen.blit(hint, hint.get_rect(center=(WIDTH//2, 480)))

        pygame.display.flip()

# =====================================================
# DEAR MARIO LETTER
# =====================================================

def dear_mario():
    title_font = pygame.font.SysFont("Times New Roman", 38, bold=True)
    body_font = pygame.font.SysFont("Times New Roman", 26)
    small_font = pygame.font.SysFont("Arial", 18)

    lines = [
        "Dear Mario,",
        "",
        "Please come to the castle.",
        "I've baked a cake for you.",
        "",
        "Yours truly,",
        "Princess Toadstool"
    ]

    fade_val = 0

    while True:
        dt = clock.tick(FPS)
        fade_val = min(255, fade_val + dt * 0.8)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "continue"

        screen.fill(SKY)

        # Card
        card = pygame.Surface((600, 380), pygame.SRCALPHA)
        card.fill(PARCHMENT)
        pygame.draw.rect(card, PARCHMENT_BORDER, card.get_rect(), 6)

        y = 60
        for i, line in enumerate(lines):
            if i == 0:
                text = title_font.render(line, True, INK)
                card.blit(text, (60, y))
                y += 60
            else:
                text = body_font.render(line, True, INK)
                card.blit(text, (60, y))
                y += 35

        hint = small_font.render("PRESS START TO CONTINUE", True, INK)
        card.blit(hint, (170, 330))

        card.set_alpha(fade_val)
        screen.blit(card, card.get_rect(center=(WIDTH//2, HEIGHT//2)))

        pygame.display.flip()

# =====================================================
# MAIN LOOP
# =====================================================

while True:

    result = main_menu()
    if result == "quit":
        break

    fade("out")
    fade("in")

    letter = dear_mario()
    if letter == "quit":
        break

    fade("out")

    # Placeholder for game start
    screen.fill((0, 0, 0))
    pygame.display.flip()
    pygame.time.wait(800)

    fade("in")

pygame.quit()
sys.exit()
