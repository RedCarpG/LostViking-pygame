""" Generate the enemy bullets in the chibi style (src/asset/image/Enemy/...)

Development tool. Drawn at art size (the game shows them at 2x). Bullets have a white core,
a bright body and a dark outline, but no white rim: only ships and objects have it, so a bullet
never looks like a ship.
    laser.png         the Phoenix laser: a long cyan bolt
    Laser2.png        the bolt of the Scouts, Interceptors and the Carrier
    LaserHit.png      where a bolt hits (6 frames)
    Carrier/Orb*.png  energy orbs (Cyan, Pink)

Run from the project root:  python tools/pixel_art/make_bullets.py [preview.png]
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from chibi import Art, CYAN, VIOLET, ring, save, preview

OUT = "src/asset/image/Enemy"
DARK = (20, 24, 60)
ORBS = {
    "Cyan": ((20, 90, 150), (70, 200, 255), (180, 240, 255)),
    "Pink": ((110, 20, 90), (255, 90, 190), (255, 200, 236)),
}


def bolt(length, width=2.0):
    """ A bolt pointing down: cyan body, a white line down the middle, rounded ends """
    art = Art(2 * int(width) + 3, length + 2)
    cx = (art.size[0] - 1) / 2
    body = art.ellipse(cx, length / 2 + 0.5, width, length / 2)
    art.fill(body, CYAN[1])
    art.fill({(round(cx), y) for y in range(3, length - 1)}, (255, 255, 255))
    ring(art.c, body, DARK)
    return art.c


def hit(frame):
    """ A cyan spark burst: a flash, then four sparks flying out and fading """
    art = Art(10, 10)
    c = 4.5
    if frame == 0:
        art.fill(art.ellipse(c, c, 1.6, 1.6), (255, 255, 255))
    elif frame == 1:
        art.fill(art.ellipse(c, c, 2.6, 2.6), CYAN[2])
        art.fill(art.ellipse(c, c, 1.2, 1.2), (255, 255, 255))
    reach = (0, 2, 3, 3.6, 4, 4.2)[frame]
    colors = ((255, 255, 255), CYAN[3], CYAN[2], CYAN[1], VIOLET[2], VIOLET[1])
    if frame >= 1:
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            art.px(c + dx * reach * 0.8, c + dy * reach * 0.8, colors[frame])
    return art.c


def orb(colors):
    art = Art(8, 8)
    c = 3.5
    body = art.ellipse(c, c, 2.9, 2.9)
    art.fill(body, colors[1])
    art.fill(art.ellipse(c - 0.5, c - 0.5, 1.4, 1.4), colors[2])
    art.px(c - 1, c - 1, (255, 255, 255))
    ring(art.c, body, colors[0])
    return art.c


def main():
    pygame.init()
    images = {
        "laser": [bolt(22, 2.0)],
        "Laser2": [bolt(14, 1.5)],
        "LaserHit": [hit(i) for i in range(6)],
        "Carrier/OrbCyan": [orb(ORBS["Cyan"])],
        "Carrier/OrbPink": [orb(ORBS["Pink"])],
    }
    if len(sys.argv) > 1:
        preview(sys.argv[1], [f for frames in images.values() for f in frames], scale=6)
        return
    for name, frames in images.items():
        save(frames, os.path.join(OUT, f"{name}.png"))


if __name__ == "__main__":
    main()
