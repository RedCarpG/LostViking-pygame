""" Generate the pixel-art nebula background (src/asset/image/Nebula.png)

Development tool (needs numpy, not used by the game itself). It takes the smooth
nebula drawn by Background, and turns it into pixel art:
- 2x2 screen pixels per art pixel (500x500 image, drawn at 1000x1000)
- a strict palette: the dark sky color + 4 nebula hues x 4 brightness bands
- hard band edges, no gradients; it still tiles vertically so it can scroll

Run from the project root:  python tools/pixel_art/make_nebula.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.getcwd())

import numpy as np
import pygame

PIXEL = 2
BANDS = 4
# How bright the strongest band is, compared with the smooth nebula
BOOST = 1.35
OUT = "src/asset/image/Nebula.png"


def main():
    pygame.init()
    pygame.display.set_mode((10, 10))
    from src.game.ui.Background import Background, _smooth_base

    smooth = _smooth_base()
    size = smooth.get_width() // PIXEL
    small = pygame.surfarray.array3d(pygame.transform.smoothscale(smooth, (size, size))).astype(float)

    dark = np.array(Background.BASE_COLOR, dtype=float)
    hues = np.array(Background.NEBULA_COLORS, dtype=float)
    strength = small - dark
    max_strength = np.sqrt((strength ** 2).sum(axis=2)).max()

    # Palette: dark sky + each hue at each band brightness
    palette = [dark]
    for hue in hues:
        direction = hue / np.linalg.norm(hue)
        for band in range(1, BANDS + 1):
            palette.append(dark + direction * max_strength * BOOST * band / BANDS)
    palette = np.array(palette).clip(0, 255)

    # Each art pixel takes the nearest palette color (the boosted smooth color decides)
    target = dark + strength * BOOST
    distance = ((target[:, :, None, :] - palette[None, None, :, :]) ** 2).sum(axis=3)
    pixels = palette[distance.argmin(axis=2)].astype(np.uint8)

    image = pygame.surfarray.make_surface(pixels)
    pygame.image.save(image, OUT)
    used = len(np.unique(pixels.reshape(-1, 3), axis=0))
    print(f"saved {OUT}: {size}x{size}, {used} colors (palette {len(palette)})")


if __name__ == "__main__":
    main()
