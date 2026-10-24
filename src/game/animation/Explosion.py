""" Pixel-art explosions, generated in code

An explosion is a fireball (a white flash that grows and cools from yellow to red,
then smoke that breaks up with a dither), a shockwave ring for the bigger ones, and
sparks flying out. The fireball frames are made ahead of time (see `prepare`) and
turned or flipped at random, so two explosions rarely look the same.
"""
import math
import random

import pygame
from pygame import Vector2
from pygame.sprite import Sprite

from src.game.groups import G_Effects
from . import warmup
from .pixel_fx import PIXEL, canvas, upscale, dither, ValueNoise

# Palette, from hot to cold
WHITE = (255, 255, 232)
LIGHT_YELLOW = (255, 238, 140)
YELLOW = (255, 200, 64)
ORANGE = (248, 136, 36)
RED_ORANGE = (220, 74, 30)
RED = (158, 34, 38)
DARK_RED = (96, 24, 42)
SMOKE_LIGHT = (84, 68, 92)
SMOKE = (58, 46, 68)
SMOKE_DARK = (38, 32, 50)

# (lowest heat, color) of the fireball
FIRE = [(1.0, WHITE), (0.82, LIGHT_YELLOW), (0.66, YELLOW), (0.5, ORANGE),
        (0.36, RED_ORANGE), (0.24, RED), (0.12, DARK_RED)]
SPARK_COLORS = [WHITE, LIGHT_YELLOW, YELLOW, ORANGE, RED_ORANGE, RED, DARK_RED]

# name: (fireball radius in art pixels, animation frames, shockwave radius (0: none), sparks)
SIZES = {
    "small": (11, 9, 0, 6),
    "medium": (19, 11, 30, 10),
    "large": (28, 13, 44, 16),
}
# Game frames per animation frame
FRAME_TIME = 3
# Rows drawn per warm-up step (see warmup)
ROWS_PER_STEP = 8

_frames = {}
_variants = {}


def prepare() -> None:
    """ Make the fireballs and their turned / flipped variants ahead of time (see warmup):
    a variant made on its first use cost a few milliseconds in the middle of a fight
    """
    for name in SIZES:
        if name not in _frames:
            warmup.add(_build(name))
        for index in range(1, 8):
            if (name, index) not in _variants:
                warmup.add(lambda name=name, index=index: _variant(name, index))


def _get_frames(name):
    if name not in _frames:
        for _ in _build(name):
            pass
    return _frames[name]


def _variant(name, index):
    """ The frames turned by a multiple of 90 degrees and/or flipped (8 variants) """
    key = (name, index)
    frames = _variants.get(key)
    if frames is None:
        frames = []
        for frame in _get_frames(name):
            if index >= 4:
                frame = pygame.transform.flip(frame, True, False)
            frames.append(pygame.transform.rotate(frame, 90 * (index % 4)) if index % 4 else frame)
        _variants[key] = frames
    return frames


# --------------- Drawing --------------- #
def _fire_color(heat):
    for lowest, color in FIRE:
        if heat >= lowest:
            return color
    return None


def _build(name):
    """ Generator: draws one frame per step (see warmup) """
    if name in _frames:
        return
    radius, count, ring, _ = SIZES[name]
    rng = random.Random(name)
    noise = ValueNoise(rng, 16)
    size = int(2 * max(radius * 1.3, ring + 2)) + 2
    center = size / 2
    # Noise sampled once for the whole canvas: (large shapes, small details)
    big, fine = [], []
    for y in range(size):
        big.append([noise.fbm(x / 5, y / 5, 2) for x in range(size)])
        fine.append([noise.at(x / 2.2 + 40, y / 2.2 + 40) for x in range(size)])
        if y % ROWS_PER_STEP == 0:
            yield
    frames = []
    for f in range(count):
        t = f / (count - 1)
        c = canvas(size, size)
        # Grows fast, then slowly
        grow = 1 - (1 - min(1.0, t / 0.4)) ** 2
        fire_radius = radius * (0.4 + 0.6 * grow)
        rough = 0.25 + 0.3 * t
        # Breaks up into holes in the second half
        dissolve = max(0.0, (t - 0.45) / 0.55)
        reach = int(fire_radius * (1 + rough)) + 1
        low, high = max(0, int(center) - reach), min(size, int(center) + reach + 1)
        for y in range(low, high):
            big_row, fine_row = big[y], fine[y]
            dy = y + 0.5 - center
            for x in range(low, high):
                dx = x + 0.5 - center
                n1, n2 = big_row[x], fine_row[x]
                edge = math.sqrt(dx * dx + dy * dy) / fire_radius + (n1 - 0.5) * rough * 2
                if edge >= 1:
                    continue
                threshold = dither(x, y)
                if dissolve > 0 and n2 * 0.6 + n1 * 0.4 + (threshold - 0.5) * 0.3 < dissolve * 1.1:
                    continue
                heat = (1 - edge) * 1.3 + 0.45 - t * 1.6 + (n2 - 0.5) * 0.4 + (threshold - 0.5) * 0.12
                if t < 0.15:
                    # First frames: a white flash with a yellow rim
                    heat += 0.3
                color = _fire_color(heat)
                if color is None:
                    smoke = n1 + (threshold - 0.5) * 0.2
                    color = SMOKE_LIGHT if smoke > 0.6 else (SMOKE if smoke > 0.42 else SMOKE_DARK)
                c.set_at((x, y), color)
            if y % ROWS_PER_STEP == 0:
                yield
        if ring and t < 0.5:
            _draw_ring(c, center, ring, t / 0.5, noise)
        frames.append(upscale(c))
        yield
    _frames[name] = frames


def _draw_ring(c, center, ring, progress, noise):
    """ Shockwave: a thin ring that grows and breaks up """
    r = ring * (0.3 + 0.7 * (1 - (1 - progress) ** 2))
    color = WHITE if progress < 0.3 else (LIGHT_YELLOW if progress < 0.6 else ORANGE)
    points = int(math.tau * r * 1.5) + 1
    for k in range(points):
        angle = k / points * math.tau
        ca, sa = math.cos(angle), math.sin(angle)
        for width in ((0, 1) if progress < 0.4 else (0,)):
            x = int(center + ca * (r - width))
            y = int(center + sa * (r - width))
            if noise.at(ca * 3 + 9, sa * 3 + 9) + (dither(x, y) - 0.5) * 0.5 < progress * 0.9:
                continue
            c.set_at((x, y), color)


_spark_images = {}


def _spark_image(color, size):
    key = (color, size)
    image = _spark_images.get(key)
    if image is None:
        image = pygame.Surface((size, size))
        image.fill(color)
        _spark_images[key] = image
    return image


# --------------- Sprites --------------- #
class Explosion(Sprite):
    """ A fireball with sparks, centered on `pos`. `delay`: frames before it starts """

    def __init__(self, pos, size="medium", delay=0, sparks=True) -> None:
        super().__init__(G_Effects)
        self.size = size
        self.frames = _variant(size, random.randrange(8))
        self._center = (round(pos[0]), round(pos[1]))
        self._index = 0
        self._count = 0
        self._delay = delay
        self._sparks = sparks
        self.image = pygame.Surface((0, 0))
        self.rect = pygame.Rect(self._center, (0, 0))
        if delay <= 0:
            self._start()

    def _start(self):
        self._delay = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=self._center)
        if self._sparks:
            Spark.burst(self._center, SIZES[self.size][3], SIZES[self.size][0] * PIXEL)

    def update(self):
        if self._delay > 0:
            self._delay -= 1
            if self._delay == 0:
                self._start()
            return
        self._count += 1
        if self._count >= FRAME_TIME:
            self._count = 0
            self._index += 1
            if self._index >= len(self.frames):
                self.kill()
                return
            self.image = self.frames[self._index]


class Spark(Sprite):
    """ A hot pixel flying out of an explosion: it slows down and cools from white to red """

    DRAG = 0.9

    def __init__(self, pos, velocity, life, size=PIXEL) -> None:
        super().__init__(G_Effects)
        self._pos = Vector2(pos)
        self._velocity = Vector2(velocity)
        self._life = life
        self._age = 0
        self._size = size
        self.image = _spark_image(SPARK_COLORS[0], size)
        self.rect = self.image.get_rect(center=pos)

    @classmethod
    def burst(cls, pos, count, radius):
        for _ in range(count):
            velocity = Vector2(0, 1).rotate(random.uniform(0, 360)) * random.uniform(2, 3 + radius / 10)
            size = PIXEL * 2 if random.random() < 0.3 else PIXEL
            cls(pos, velocity, random.randint(12, 26), size)

    def update(self):
        self._age += 1
        if self._age >= self._life:
            self.kill()
            return
        self._pos += self._velocity
        self._velocity *= self.DRAG
        color = SPARK_COLORS[self._age * len(SPARK_COLORS) // self._life]
        self.image = _spark_image(color, self._size)
        # Snap to the pixel grid of the art
        self.rect.topleft = (int(self._pos.x) // PIXEL * PIXEL, int(self._pos.y) // PIXEL * PIXEL)
