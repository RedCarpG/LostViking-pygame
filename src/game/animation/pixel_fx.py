""" Helpers to draw pixel art in code (generated effects, planets)

Images are drawn at art size (one pixel is one art pixel), then scaled up with
nearest neighbour to the pixel size of the rest of the art (2x). Shades change
in steps, with an ordered (Bayer) dither where two shades meet.
"""
import math
import random
import pygame

PIXEL = 2

# 4x4 ordered dither matrix, values in [0, 1)
_BAYER4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
BAYER = [[v / 16 + 1 / 32 for v in row] for row in _BAYER4]


def dither(x, y) -> float:
    """ Threshold of the ordered dither at (x, y), in (0, 1) """
    return BAYER[y & 3][x & 3]


def upscale(surface, factor=PIXEL) -> pygame.Surface:
    """ Scale up with nearest neighbour: every art pixel becomes a square block """
    return pygame.transform.scale(surface, (surface.get_width() * factor, surface.get_height() * factor))


def canvas(width, height) -> pygame.Surface:
    return pygame.Surface((width, height), pygame.SRCALPHA)


def ramp(colors, value):
    """ Color of `value` (0 - 1) in a list of colors from dark to light """
    index = int(value * len(colors))
    return colors[max(0, min(len(colors) - 1, index))]


class ValueNoise:
    """ Smooth random 2D noise, values about 0 - 1. It tiles every `period` cells """

    def __init__(self, rng: random.Random, period=32):
        self.period = period
        self._grid = [[rng.random() for _ in range(period)] for _ in range(period)]

    def at(self, x, y) -> float:
        p = self.period
        x0, y0 = math.floor(x), math.floor(y)
        fx, fy = x - x0, y - y0
        # Smoothstep between the grid values
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        row0 = self._grid[y0 % p]
        row1 = self._grid[(y0 + 1) % p]
        a = row0[x0 % p] + (row0[(x0 + 1) % p] - row0[x0 % p]) * fx
        b = row1[x0 % p] + (row1[(x0 + 1) % p] - row1[x0 % p]) * fx
        return a + (b - a) * fy

    def fbm(self, x, y, octaves=3) -> float:
        """ Sum of several octaves: large shapes with smaller details """
        total, amplitude, norm = 0.0, 1.0, 0.0
        for i in range(octaves):
            total += self.at(x, y) * amplitude
            norm += amplitude
            amplitude *= 0.5
            x, y = x * 2 + 17.3, y * 2 + 5.1
        return total / norm
