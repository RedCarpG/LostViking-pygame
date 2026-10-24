""" Generate the pixel-art energy orbs fired by the Carrier boss (src/asset/image/Enemy/Carrier/Orb*.png)

Development tool. 7x7 drawing scaled 2x, like the boss itself.
Run from the project root:  python tools/pixel_art/make_bullets.py
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

SCALE = 2
ORB = [
    "..###..",
    ".#ooo#.",
    "#oowoo#",
    "#owwwo#",
    "#oowoo#",
    ".#ooo#.",
    "..###..",
]
COLORS = {
    "Cyan": {"#": (20, 90, 140), "o": (80, 200, 255), "w": (232, 250, 255)},
    "Pink": {"#": (110, 20, 80), "o": (255, 90, 190), "w": (255, 232, 246)},
}


def main():
    pygame.init()
    pygame.display.set_mode((10, 10))
    for name, palette in COLORS.items():
        image = pygame.Surface((7, 7), pygame.SRCALPHA)
        for y, row in enumerate(ORB):
            for x, ch in enumerate(row):
                if ch in palette:
                    image.set_at((x, y), palette[ch])
        path = f"src/asset/image/Enemy/Carrier/Orb{name}.png"
        pygame.image.save(pygame.transform.scale(image, (7 * SCALE, 7 * SCALE)), path)
        print("saved", path)


if __name__ == "__main__":
    main()
