""" Generate the supplies in the chibi style (src/asset/image/Supply/...)

Development tool. Drawn at art size (the game shows them at 2x). A supply is a round badge
with an icon and a white rim; a shine sweeps across it. Sheets of 6 frames:
    SupplyLevel   weapon upgrade: blue chevrons      SupplyGetLevel   picked up: a burst in its color
    SupplyLife    repair / life: a red cross         SupplyGetLife
    SupplyBomb    nuclear bomb: a radiation sign     SupplyGetBomb
    SupplyBase    the first frame of the bomb badge  SupplyDrop       a supply appears: a ring opening

Run from the project root:  python tools/pixel_art/make_supplies.py [preview.png]
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from chibi import Art, RED, YELLOW, GLASS, FRAMES, finish, save, preview

OUT = "src/asset/image/Supply"
SIZE = 17
EFFECT = 25
OUTLINE = (40, 20, 50)
# (badge ramp: shadow, base, light, highlight), icon color, burst color
KINDS = {
    "Level": ([(30, 60, 140), (60, 120, 220), (120, 190, 255), (220, 240, 255)], (255, 255, 255), (120, 200, 255)),
    "Life": ([(160, 30, 60), (226, 70, 90), (255, 140, 150), (255, 220, 224)], (255, 255, 255), (255, 120, 140)),
    "Bomb": ([(180, 90, 20), (240, 160, 40), (255, 210, 100), (255, 245, 210)], (60, 30, 40), (255, 210, 90)),
}


def icon(art, kind, color):
    c = (SIZE - 1) / 2
    if kind == "Level":
        for dy in (-2, 1):
            for i in range(-2, 3):
                art.px(c + i, c + dy + abs(i), color)
                art.px(c + i, c + dy + abs(i) - 1, color)
    elif kind == "Life":
        art.fill(art.rect(round(c) - 1, round(c) - 4, 3, 9), color)
        art.fill(art.rect(round(c) - 4, round(c) - 1, 9, 3), color)
    else:
        # Radiation sign: a dot and three blades
        art.fill(art.ellipse(c, c, 1.1, 1.1), color)
        for k in range(3):
            a0 = math.radians(-90 + k * 120 - 30)
            for r in (2.5, 3.5, 4.5):
                for t in range(-3, 4):
                    a = a0 + t * 0.15
                    art.px(round(c + math.cos(a) * r), round(c + math.sin(a) * r), color)


def badge(kind, frame):
    ramp, color, _ = KINDS[kind]
    art = Art(SIZE, SIZE)
    c = (SIZE - 1) / 2
    disc = art.ellipse(c, c, 6.4, 6.4)
    art.dome(disc, c, c, 6.4, 6.4, ramp)
    icon(art, kind, color)
    # A shine sweeping across from the upper left
    sweep = -8 + frame * 4
    for (x, y) in disc:
        if abs((x - c) + (y - c) - sweep) < 1:
            art.c.set_at((x, y), ramp[3])
    return finish(art.c, disc, OUTLINE)


def burst(kind, frame):
    """ Picked up: a ring opening in the supply's color, with sparks flying out """
    color = KINDS[kind][2]
    art = Art(EFFECT, EFFECT)
    c = (EFFECT - 1) / 2
    t = (frame + 1) / FRAMES
    r = 3 + t * 8
    ring_px = {(x, y) for x, y in art.ellipse(c, c, r + 1, r + 1) if (x, y) not in art.ellipse(c, c, r, r)}
    fade = (255, 255, 255) if frame < 2 else color
    if frame < 5:
        art.fill(ring_px, fade)
    for k in range(8):
        a = k / 8 * math.tau + frame * 0.2
        d = r + 1.5 + t * 2
        if frame < 5 or k % 2 == 0:
            art.px(c + math.cos(a) * d, c + math.sin(a) * d, (255, 255, 255) if k % 2 else color)
    return art.c


def drop(frame):
    """ A supply appears: a white ring closing in, then a flash """
    art = Art(EFFECT, EFFECT)
    c = (EFFECT - 1) / 2
    r = (11, 9, 7, 5, 3, 0)[frame]
    if r:
        art.fill({(x, y) for x, y in art.ellipse(c, c, r + 1, r + 1) if (x, y) not in art.ellipse(c, c, r, r)},
                 (255, 255, 255))
    else:
        art.fill(art.ellipse(c, c, 3, 3), (255, 255, 255))
    for k in range(4):
        a = k / 4 * math.tau + frame * 0.5
        art.px(c + math.cos(a) * (r + 3), c + math.sin(a) * (r + 3), GLASS[2])
    return art.c


def main():
    pygame.init()
    sheets = {}
    for kind in KINDS:
        sheets[f"Supply{kind}"] = [badge(kind, i) for i in range(FRAMES)]
        sheets[f"SupplyGet{kind}"] = [burst(kind, i) for i in range(FRAMES)]
    sheets["SupplyBase"] = [sheets["SupplyBomb"][0]]
    sheets["SupplyDrop"] = [drop(i) for i in range(FRAMES)]
    if len(sys.argv) > 1:
        preview(sys.argv[1], [f for frames in sheets.values() for f in frames], scale=5)
        return
    for name, frames in sheets.items():
        save(frames, os.path.join(OUT, f"{name}.png"))


if __name__ == "__main__":
    main()
