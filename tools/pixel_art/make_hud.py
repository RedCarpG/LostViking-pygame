""" Generate the pixel-art HUD images (src/asset/image/UI/...)

Development tool. Every image is drawn on a half size canvas with a small palette,
then scaled 2x (same pixel size as the background and the 16px pixel font).
Panels get a 1 pixel outline, a light top/left edge and a dark bottom/right edge.

Run from the project root:  python tools/pixel_art/make_hud.py
Editable copies for Aseprite:  see README in this folder.
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

SCALE = 2
OUT = "src/asset/image/UI"

# Palette
OUTLINE = (34, 12, 28)
DARK = (62, 28, 60)
BODY = (98, 52, 96)
LIGHT = (140, 86, 136)
HIGH = (196, 156, 196)
SHINE = (236, 214, 236)
SCREEN_0 = (6, 14, 40)
SCREEN_1 = (12, 32, 82)
SCREEN_2 = (22, 58, 128)
GLASS = (70, 130, 210)
CYAN = (80, 200, 255)
CYAN_LIGHT = (170, 236, 255)
RED = (225, 54, 54)
RED_DARK = (110, 20, 32)
GREEN = (70, 225, 125)
GREEN_DIM = (26, 96, 60)
YELLOW = (250, 196, 64)
YELLOW_DIM = (112, 80, 22)
SOCKET = (26, 12, 26)


def canvas(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def save(surface, path, scale=SCALE):
    big = pygame.transform.scale(surface, (surface.get_width() * scale, surface.get_height() * scale))
    full = os.path.join(OUT, path)
    pygame.image.save(big, full)
    print(f"saved {full} {big.get_size()}")


def panel(c, points):
    """ Metal panel: flat body, 1px outline, light top/left edge, dark bottom/right edge """
    shape = canvas(*c.get_size())
    pygame.draw.polygon(shape, BODY, points)
    mask = pygame.mask.from_surface(shape)
    w, h = c.get_size()

    def inside(x, y):
        return 0 <= x < w and 0 <= y < h and mask.get_at((x, y))

    for y in range(h):
        for x in range(w):
            if not mask.get_at((x, y)):
                continue
            if not (inside(x - 1, y) and inside(x + 1, y) and inside(x, y - 1) and inside(x, y + 1)):
                color = OUTLINE
            elif not inside(x, y - 2) or not inside(x - 2, y):
                color = HIGH
            elif not inside(x, y + 2) or not inside(x + 2, y):
                color = DARK
            elif not inside(x, y - 3):
                color = LIGHT
            else:
                color = BODY
            c.set_at((x, y), color)


def recess(c, rect, fill=SOCKET):
    """ Sunken area: dark top/left inner edge, light bottom/right edge """
    x, y, w, h = rect
    c.fill(fill, rect)
    c.fill(OUTLINE, (x, y, w, 1))
    c.fill(OUTLINE, (x, y, 1, h))
    c.fill(LIGHT, (x, y + h - 1, w, 1))
    c.fill(LIGHT, (x + w - 1, y, 1, h))


def screen(c, rect):
    """ Blue display: dark background with scanlines and a glint in the corner """
    x, y, w, h = rect
    for row in range(h):
        c.fill(SCREEN_1 if row % 2 else SCREEN_0, (x, y + row, w, 1))
    c.fill(SCREEN_2, (x + 1, y + 1, 2, 1))
    c.fill(SCREEN_2, (x + 1, y + 2, 1, 1))


def rivet(c, x, y):
    c.set_at((x, y), SHINE)
    c.set_at((x, y + 1), DARK)


def bitmap(c, x, y, rows, color):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "#":
                c.set_at((x + i, y + j), color)


def outline_of(filled):
    """ Keep only the edge pixels of a filled shape (line-art look) """
    out = canvas(*filled.get_size())
    m = pygame.mask.from_surface(filled)
    w, h = filled.get_size()
    for y in range(h):
        for x in range(w):
            if m.get_at((x, y)) and not all(
                    0 <= x + dx < w and 0 <= y + dy < h and m.get_at((x + dx, y + dy))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.set_at((x, y), filled.get_at((x, y)))
    return out


def bar_frame(w, h):
    """ Frame drawn over a health bar: 2px border, transparent middle with a glass shine """
    c = canvas(w, h)
    pygame.draw.rect(c, OUTLINE, (0, 0, w, h), 1)
    pygame.draw.rect(c, DARK, (1, 1, w - 2, h - 2), 1)
    c.fill((255, 255, 255, 70), (2, 2, w - 4, 1))
    c.fill((255, 255, 255, 120), (3, 2, 6, 1))
    # Ticks every 10%
    for i in range(1, 10):
        c.fill((0, 0, 0, 90), (2 + (w - 4) * i // 10, h - 4, 1, 2))
    return c


# ------------------ Player panel (bottom left) ------------------

def player_panel():
    c = canvas(125, 46)
    panel(c, [(0, 0), (34, 0), (41, 7), (112, 7), (116, 11), (116, 17), (121, 17), (124, 20), (124, 45), (0, 45)])
    # Portrait display (the ship portrait is drawn by the game, centered at (36, 32) full size)
    recess(c, (3, 3, 30, 26))
    screen(c, (4, 4, 28, 24))
    # Life lights strip (the lights are drawn by the game at (92 + 24i, 22), 20x6)
    recess(c, (44, 10, 61, 5))
    # Health bar slot (frame at (10, 56), bar (14, 60, 214, 18))
    recess(c, (5, 28, 111, 13))
    # Vents and rivets
    for i in range(4):
        c.fill(DARK, (118, 25 + i * 4, 4, 1))
    for x, y in ((2, 42), (121, 42), (37, 3), (109, 9)):
        rivet(c, x, y)
    save(c, "Player/BottomLeft.png")
    save(bar_frame(111, 13), "Player/HealthBar.png")


def life_lights():
    lit = canvas(60, 3)
    blink = canvas(60, 3)
    for f in range(6):
        x = f * 10
        lit.fill(CYAN, (x, 0, 10, 3))
        lit.fill(CYAN_LIGHT, (x, 0, 10, 1))
        # Glint running along the light
        lit.fill((255, 255, 255), (x + f * 2, 0, 2, 2))
        if f < 3:
            blink.fill(RED, (x, 0, 10, 3))
            blink.fill((255, 140, 140), (x, 0, 10, 1))
    empty = canvas(10, 3)
    empty.fill((44, 22, 44), (0, 0, 10, 3))
    empty.fill((70, 40, 70), (0, 0, 10, 1))
    save(lit, "Player/LifeLight.png")
    save(blink, "Player/LifeLightBlink.png")
    save(empty, "Player/LifeLightEmpty.png")


# ------------------ Equipment panel (left) ------------------

WEAPON = [
    "........#........",
    ".......###.......",
    ".......#.#.......",
    "......##.##......",
    "......#...#......",
    "......#.#.#......",
    "......#...#......",
    ".....##...##.....",
    "....#.#.#.#.#....",
    "...#..#...#..#...",
    "..#...#...#...#..",
    ".#....#####....#.",
    ".#...##...##...#.",
    "..###.#...#.###..",
    "......#.#.#......",
    ".....##...##.....",
    ".....#.....#.....",
]


# A pair of Lanzer Torpedoes, fins and flames
TORPEDO = [
    ".................",
    ".....#.....#.....",
    "....#.#...#.#....",
    "....#.#...#.#....",
    "....###...###....",
    "....#.#...#.#....",
    "....#.#...#.#....",
    "....#.#...#.#....",
    "....#.#...#.#....",
    "...##.##.##.##...",
    "..#.#.#.#.#.#.#..",
    "..#.###...###.#..",
    "..##...#.#...##..",
    ".....#.....#.....",
    "....#.#...#.#....",
    ".....#.....#.....",
    ".................",
]


def radiation_icon(size=17):
    filled = canvas(size, size)
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            dx, dy = x - c, y - c
            r = math.hypot(dx, dy)
            angle = (math.degrees(math.atan2(-dy, dx)) + 360) % 360
            wedge = any(abs((angle - a + 180) % 360 - 180) < 30 for a in (90, 210, 330))
            if r <= 1.5 or (3.5 <= r <= 8.2 and wedge):
                filled.set_at((x, y), YELLOW)
    return outline_of(filled)


def equip_icon(draw, path):
    c = canvas(21, 21)
    screen(c, (0, 0, 21, 21))
    draw(c)
    save(c, path)


def equip_panel():
    c = canvas(50, 99)
    panel(c, [(0, 0), (40, 0), (46, 6), (46, 26), (49, 29), (49, 62), (46, 65), (46, 92), (39, 98), (0, 98)])
    # Three display slots (icons drawn by the game at (16, 24), (16, 76) and (16, 128), 42x42)
    for y in (11, 37, 63):
        recess(c, (7, y, 23, 23))
        screen(c, (8, y + 1, 21, 21))
    # Red "X" indicator
    recess(c, (40, 7, 5, 11), RED_DARK)
    bitmap(c, 41, 9, ["#.#", ".#.", "#.#", ".#.", "#.#"], RED)
    # Light sockets (lights drawn by the game at (84, 82 / 94 / 106), 6x10)
    for y in (40, 46, 52):
        recess(c, (41, y, 5, 7))
    for x, y in ((2, 95), (37, 2), (2, 2)):
        rivet(c, x, y)
    save(c, "Equip/Left.png")
    equip_icon(lambda s: bitmap(s, 2, 2, WEAPON, GREEN), "Equip/Weapon0.png")
    equip_icon(lambda s: s.blit(radiation_icon(), (2, 2)), "Equip/Bomb0.png")
    equip_icon(lambda s: bitmap(s, 2, 2, TORPEDO, CYAN), "Equip/Torpedo0.png")


def equip_lights():
    for name, bright, dim in (("Green", GREEN, GREEN_DIM), ("Red", RED, RED_DARK), ("Yellow", YELLOW, YELLOW_DIM)):
        c = canvas(18, 5)
        for f, level in enumerate((0.0, 0.5, 1.0, 1.0, 0.5, 0.0)):
            color = tuple(int(d + (b - d) * (0.45 + 0.55 * level)) for b, d in zip(bright, dim))
            c.fill(color, (f * 3, 0, 3, 5))
            c.set_at((f * 3, 0), (255, 255, 255) if level > 0.6 else color)
        save(c, f"Equip/Left_Light{name}.png")


# ------------------ Boss bar (top middle) ------------------

def boss_panel():
    c = canvas(266, 24)
    panel(c, [(0, 0), (265, 0), (265, 14), (256, 23), (9, 23), (0, 14)])
    # Health bar slot (frame at (32, 12), bar (36, 16, 470, 18))
    recess(c, (15, 5, 241, 15))
    # Warning lights on both ends
    for x in (4, 259):
        recess(c, (x, 4, 4, 4), RED_DARK)
        c.fill(RED, (x + 1, 5, 2, 2))
    for x in (6, 258):
        rivet(c, x, 15)
    save(c, "Boss/MidTop.png")
    save(bar_frame(239, 13), "Boss/MidTop_HealthBar.png")


def main():
    pygame.init()
    pygame.display.set_mode((10, 10))
    player_panel()
    life_lights()
    equip_panel()
    equip_lights()
    boss_panel()


if __name__ == "__main__":
    main()
