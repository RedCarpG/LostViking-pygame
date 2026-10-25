""" Generate the asteroid sprite sheets (src/asset/image/Enemy/Asteroid/...)

Development tool. Each rock is a lumpy dome (a random outline made of a few waves) with
craters and a few bumps. It spins: every frame turns the rock, then lights it again from
the upper left, so the light stays where it is while the rock turns. Chibi style like the ships
(see chibi.py): the light is cut into four flat bands, with a dark outline and the white rim.
The grey rocks carry blue mineral crystals (the Minerals of StarCraft).

Drawn at art size and scaled 2x by the game. Each sheet holds SPIN_FRAMES frames side by side:
    Asteroid<Size><Variant>.png   Size: Large, Medium, Small   Variant: 0 (brown), 1 (grey)

Run from the project root:  python tools/pixel_art/make_asteroids.py
"""
import math
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from shading import save_sheet
from chibi import N_OUTLINE, finish, opaque

OUT = "src/asset/image/Enemy/Asteroid"
# Frames per turn (keep in sync with Asteroid.SPIN_FRAMES)
SPIN_FRAMES = 16

# Art pixels: (radius, canvas size, room left for the outline and the rim)
SIZES = {"Large": (19, 48), "Medium": (12, 34), "Small": (7, 22)}

# Shadow, base, light, highlight
BROWN = [(78, 60, 66), (134, 106, 92), (180, 150, 120), (224, 204, 170)]
GREY = [(64, 68, 90), (112, 118, 136), (158, 164, 180), (208, 214, 224)]
MINERAL = [(30, 120, 180), (70, 200, 245), (190, 245, 255)]
BANDS = (0.36, 0.64, 0.86)

_L = (-0.55, -0.6, 0.58)
_n = math.sqrt(sum(v * v for v in _L))
LIGHT = tuple(v / _n for v in _L)


class Rock:
    """ A rock in its own coordinates (it turns, its features turn with it) """

    def __init__(self, rng, radius, minerals):
        self.radius = radius
        # Outline: radius * (1 + sum of waves)
        self.waves = [(k, rng.uniform(0, 0.16) / math.sqrt(k), rng.uniform(0, math.tau)) for k in range(2, 7)]
        self.craters = []
        for _ in range(max(2, radius // 4)):
            angle, dist = rng.uniform(0, math.tau), rng.uniform(0, 0.7) * radius
            self.craters.append((math.cos(angle) * dist, math.sin(angle) * dist,
                                 rng.uniform(0.18, 0.34) * radius, rng.uniform(0.25, 0.45)))
        # Small bumps and pits all over
        self.bumps = [(rng.uniform(-1, 1) * radius, rng.uniform(-1, 1) * radius,
                       rng.uniform(1.8, 3.2), rng.uniform(-0.9, 1.0)) for _ in range(radius // 2)]
        self.minerals = []
        if minerals:
            for _ in range(max(2, radius // 5)):
                angle, dist = rng.uniform(0, math.tau), rng.uniform(0.2, 0.6) * radius
                self.minerals.append((math.cos(angle) * dist, math.sin(angle) * dist, rng.choice((2.2, 2.8, 3.4))))

    def edge(self, phi) -> float:
        return self.radius * (1 + sum(a * math.cos(k * phi + p) for k, a, p in self.waves))

    def height(self, x, y):
        """ Height of the surface at (x, y), None outside the rock """
        s = math.hypot(x, y) / self.edge(math.atan2(y, x))
        if s >= 1:
            return None
        h = math.sqrt(1 - s * s) * self.radius * 0.85
        for cx, cy, cr, depth in self.craters:
            d = math.hypot(x - cx, y - cy)
            if d < cr:
                h -= depth * cr * (1 - (d / cr) ** 2)
            # Raised rim
            h += 0.3 * depth * cr * math.exp(-((d - cr) / (0.3 * cr)) ** 2)
        for bx, by, br, bh in self.bumps:
            d = math.hypot(x - bx, y - by)
            if d < br:
                h += bh * (1 - d / br)
        return h

    def mineral(self, x, y) -> float:
        """ 0 outside the crystals, up to 1 at their middle """
        best = 0.0
        for mx, my, size in self.minerals:
            # Diamond shaped crystals
            d = (abs(x - mx) * 1.3 + abs(y - my)) / size
            best = max(best, 1 - d)
        return best


def render(rock, angle, ramp, size):
    c = pygame.Surface((size, size), pygame.SRCALPHA)
    middle = (size - 1) / 2
    cos_a, sin_a = math.cos(-angle), math.sin(-angle)

    def local(x, y):
        dx, dy = x - middle, y - middle
        return dx * cos_a - dy * sin_a, dx * sin_a + dy * cos_a

    def height(x, y):
        return rock.height(*local(x, y))

    for y in range(size):
        for x in range(size):
            h = height(x, y)
            if h is None:
                continue
            # Normal from the slope of the surface (in screen space: the light does not turn)
            hx0, hx1 = height(x - 0.5, y), height(x + 0.5, y)
            hy0, hy1 = height(x, y - 0.5), height(x, y + 0.5)
            gx = (hx1 if hx1 is not None else h - 1.5) - (hx0 if hx0 is not None else h - 1.5)
            gy = (hy1 if hy1 is not None else h - 1.5) - (hy0 if hy0 is not None else h - 1.5)
            n = (-gx, -gy, 1.0)
            norm = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
            light = max(0.0, sum(a * b for a, b in zip(n, LIGHT)) / norm)
            # Four flat bands: a lit top, a dark side toward the lower right
            color = ramp[sum(light > band for band in BANDS)]
            crystal = rock.mineral(*local(x, y))
            if crystal > 0:
                color = MINERAL[2 if crystal > 0.55 else 1 if light > 0.5 else 0]
            c.set_at((x, y), color)
    return finish(c, opaque(c), N_OUTLINE)


def main():
    pygame.init()
    for name, (radius, size) in SIZES.items():
        for variant, (ramp, minerals) in enumerate(((BROWN, False), (GREY, name != "Small"))):
            rng = random.Random(f"{name}{variant}")
            rock = Rock(rng, radius, minerals)
            frames = [render(rock, k * math.tau / SPIN_FRAMES, ramp, size) for k in range(SPIN_FRAMES)]
            save_sheet(frames, os.path.join(OUT, f"Asteroid{name}{variant}.png"))


if __name__ == "__main__":
    main()
