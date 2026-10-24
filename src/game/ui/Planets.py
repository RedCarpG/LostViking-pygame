""" Random pixel-art planets drifting behind the action

Every planet is made in code: a type (rocky, gas giant, ice, lava, ocean), a size,
one of the type's palettes, surface noise wrapped around a sphere, light from the upper
left with dithered shading, sometimes a ring. One planet is on screen at a time; the
next one is drawn a little each frame while the sky waits for it (see PlanetLayer).
"""
import math
import random
import time

import pygame

from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.game.animation.pixel_fx import PIXEL, canvas, upscale, dither, ValueNoise

# Color of the night side, close to the sky
NIGHT = (10, 11, 26)
# The finished planet is darkened (with a little blue, as if far away) so it stays
# behind the bullets and ships
DIM = (200, 200, 214)
# Direction of the light (upper left, toward the viewer)
_L = (-0.55, -0.6, 0.58)
_n = math.sqrt(sum(v * v for v in _L))
LIGHT = tuple(v / _n for v in _L)

# Ramps from shadow to highlight. Kept dim: planets are scenery, not targets
ROCK = [
    [(34, 28, 38), (62, 50, 54), (98, 80, 74), (136, 114, 96), (166, 144, 118)],
    [(26, 28, 40), (48, 52, 68), (78, 84, 100), (112, 118, 132), (144, 150, 162)],
    [(36, 24, 30), (68, 40, 42), (106, 62, 54), (144, 90, 68), (174, 120, 88)],
]
ROCK_DARK = [
    [(26, 22, 32), (44, 36, 44), (68, 56, 58), (94, 80, 76), (120, 104, 94)],
    [(20, 22, 34), (36, 40, 56), (58, 64, 82), (84, 90, 108), (110, 116, 132)],
    [(26, 18, 26), (48, 30, 34), (76, 46, 44), (104, 66, 56), (130, 88, 70)],
]
GAS = [
    [[(40, 26, 30), (82, 52, 46), (126, 86, 62), (166, 124, 84), (194, 158, 110)],
     [(34, 24, 32), (66, 42, 46), (104, 64, 56), (140, 92, 68), (168, 120, 86)],
     [(44, 34, 40), (90, 74, 70), (134, 116, 98), (172, 156, 128), (200, 188, 156)]],
    [[(26, 24, 48), (52, 46, 90), (84, 74, 130), (120, 108, 166), (154, 144, 194)],
     [(22, 30, 52), (40, 58, 94), (64, 92, 134), (94, 128, 168), (128, 162, 196)],
     [(36, 30, 56), (70, 60, 100), (108, 96, 140), (146, 136, 176), (180, 172, 204)]],
]
ICE = [(30, 40, 60), (60, 84, 110), (100, 132, 160), (146, 178, 198), (188, 214, 226)]
ICE_DARK = [(24, 32, 52), (42, 58, 86), (66, 92, 124), (94, 128, 160), (122, 160, 188)]
CRUST = [(22, 16, 22), (40, 28, 32), (60, 42, 44), (82, 58, 56), (104, 76, 68)]
LAVA = [(150, 44, 26), (214, 96, 34), (246, 170, 74)]
WATER = [(16, 24, 52), (26, 46, 92), (40, 72, 128), (64, 104, 158), (94, 140, 186)]
LAND = [(22, 32, 26), (40, 60, 40), (66, 90, 54), (98, 118, 72), (132, 146, 98)]
CLOUD = [(40, 46, 70), (88, 96, 122), (136, 144, 164), (172, 178, 194), (196, 200, 212)]

TYPES = ("rocky", "gas", "ice", "lava", "ocean")


def make_planet(rng: random.Random, kind=None, radius=None):
    """ Generator drawing a planet half a row at a time; its return value is the image """
    kind = kind or rng.choice(TYPES)
    radius = radius or rng.randint(14, 50)
    noise = ValueNoise(rng, 32)
    detail = ValueNoise(rng, 32)
    ringed = (kind == "gas" and rng.random() < 0.6) or (kind in ("ice", "rocky") and rng.random() < 0.2)
    extent = math.ceil(radius * (1.95 if ringed else 1.0)) + 1
    size = extent * 2
    center = size / 2
    c = canvas(size, size)

    # Palettes and features of this planet
    choice = rng.randrange(3)
    gas_bands = rng.choice(GAS)
    band_count = rng.randint(5, 9)
    craters = []
    if kind == "rocky":
        for _ in range(max(2, radius // 4)):
            angle, dist = rng.uniform(0, math.tau), rng.uniform(0, 0.85) * radius
            craters.append((math.cos(angle) * dist, math.sin(angle) * dist, rng.uniform(1.5, max(2.0, radius / 6))))
    storm = None
    if kind == "gas" and rng.random() < 0.6:
        storm = (rng.uniform(-0.4, 0.4) * radius, rng.uniform(-0.5, 0.5) * radius, rng.uniform(0.12, 0.2) * radius)
    tilt = rng.uniform(-0.35, 0.35)
    squash = rng.uniform(0.22, 0.38)
    ring_ramp = gas_bands[2] if kind == "gas" else (ICE if kind == "ice" else ROCK[choice])
    feature = radius / rng.uniform(2.5, 4.0)
    rim_color = {"ocean": (104, 150, 200), "ice": (176, 210, 228), "gas": gas_bands[2][4]}.get(kind)
    rim = 1 - 1.3 / radius

    lx, ly, lz = LIGHT
    half = size // 2
    for y in range(size):
        dy = y + 0.5 - center
        ny = dy / radius
        for x in range(size):
            if x == half:
                # Half a row per step (see PlanetLayer)
                yield
            dx = x + 0.5 - center
            nx = dx / radius
            r2 = nx * nx + ny * ny
            threshold = dither(x, y)

            ring_color = None
            ring_front = False
            if ringed:
                rx = dx * math.cos(tilt) + dy * math.sin(tilt)
                ry = (-dx * math.sin(tilt) + dy * math.cos(tilt)) / squash
                rr = math.sqrt(rx * rx + ry * ry) / radius
                if 1.35 < rr < 1.9:
                    gap = math.sin(rr * 26) + (threshold - 0.5) * 0.6
                    if gap > -0.55:
                        shade = 3 if gap > 0.4 else 2
                        ring_front = ry > 0
                        if not ring_front:
                            shade -= 1
                        ring_color = ring_ramp[shade]

            if r2 > 1:
                if ring_color is not None:
                    c.set_at((x, y), ring_color)
                continue
            if ring_color is not None and ring_front:
                c.set_at((x, y), ring_color)
                continue

            nz = math.sqrt(1 - r2)
            light = nx * lx + ny * ly + nz * lz
            # Surface coordinates wrapped around the sphere (features shrink at the edge)
            lat = math.asin(max(-1.0, min(1.0, ny)))
            cos_lat = math.sqrt(max(1e-6, 1 - ny * ny))
            lon = math.asin(max(-1.0, min(1.0, nx / cos_lat)))
            u, v = lon * radius / feature, lat * radius / feature
            n = noise.fbm(u, v, 3)

            emissive = None
            if kind == "rocky":
                ramp = ROCK_DARK[choice] if n < 0.42 else ROCK[choice]
                bump = 0
                for cx, cy, cr in craters:
                    ox, oy = dx - cx, dy - cy
                    d = math.sqrt(ox * ox + oy * oy)
                    if d < cr:
                        # Inside a crater: its wall facing the light is lit, the other in shadow
                        side = (ox * lx + oy * ly) / cr
                        bump = -1 if side > -0.2 else 1
                        break
            elif kind == "gas":
                turbulence = (detail.fbm(u * 0.5, v * 3, 2) - 0.5) * 1.4
                band = int((lat / math.pi + 0.5) * band_count + turbulence) % 3
                ramp = gas_bands[band]
                bump = 0
                if storm is not None:
                    sx, sy, sr = storm
                    if ((dx - sx) / (sr * 1.6)) ** 2 + ((dy - sy) / sr) ** 2 < 1:
                        ramp = gas_bands[(band + 1) % 3]
                        bump = 1
            elif kind == "ice":
                ramp = ICE_DARK if detail.fbm(u, v, 2) < 0.38 or abs(n - 0.5) < 0.025 else ICE
                bump = 0
            elif kind == "lava":
                ramp = CRUST
                bump = 0
                vein = abs(n - 0.5)
                if vein < 0.045:
                    # Glowing cracks, bright even on the night side
                    emissive = LAVA[2] if vein < 0.012 else (LAVA[1] if vein < 0.028 else LAVA[0])
            else:
                ramp = LAND if n > 0.54 else WATER
                bump = 0
                if abs(ny) > 0.86 + (n - 0.5) * 0.2:
                    ramp = ICE
                elif detail.fbm(u * 1.4, v * 2.2, 2) > 0.6:
                    ramp = CLOUD

            if emissive is not None:
                c.set_at((x, y), emissive)
                continue
            if light < -0.12 + (threshold - 0.5) * 0.12:
                c.set_at((x, y), NIGHT)
                continue
            level = (light + 0.12) / 1.12
            index = int(level * (len(ramp) - 1) + threshold) + bump
            index = max(0, min(len(ramp) - 1, index))
            color = ramp[index]
            if rim_color is not None and r2 > rim * rim and light > 0.15:
                color = rim_color
            c.set_at((x, y), color)
        yield
    c.fill(DIM, special_flags=pygame.BLEND_RGB_MULT)
    image = upscale(c)
    if pygame.display.get_surface() is not None:
        image = image.convert_alpha()
    return image


class PlanetLayer:
    """ One planet at a time drifts down the screen, then the sky stays empty for a while """

    # Frames before the first planet and between two planets
    FIRST_DELAY = (60, 240)
    DELAY = (500, 1300)
    # Screen pixels per frame: between the far stars (1.0, behind the planet) and the
    # near stars (2.6, in front of it). Small planets are farther away and slower
    SPEED = (1.05, 1.5)
    # Time per frame spent drawing the next planet
    WORK_MS = 1.0

    def __init__(self, rng: random.Random = None):
        self._random = rng or random.Random()
        self._image = None
        self._x = 0
        self._y = 0.0
        self._speed = 0.0
        self._ready = None
        self._job = None
        self._count_delay = self._random.randint(*self.FIRST_DELAY)
        self._start_next()

    @property
    def visible(self) -> bool:
        return self._image is not None

    def _start_next(self):
        self._ready = None
        self._job = make_planet(self._random)

    def _work(self):
        end = time.perf_counter() + self.WORK_MS / 1000
        while self._job is not None and time.perf_counter() < end:
            try:
                next(self._job)
            except StopIteration as done:
                self._ready = done.value
                self._job = None

    def update(self) -> None:
        if self._job is not None:
            self._work()
        if self._image is not None:
            self._y += self._speed
            if self._y > SCREEN_HEIGHT:
                self._image = None
                self._count_delay = self._random.randint(*self.DELAY)
        elif self._count_delay > 0:
            self._count_delay -= 1
        elif self._ready is not None:
            self._show(self._ready)
            self._start_next()

    def _show(self, image):
        self._image = image
        width, height = image.get_size()
        # Off to one side, sometimes partly off the screen, so it does not sit behind the player
        side = self._random.choice((self._random.uniform(-0.1, 0.35), self._random.uniform(0.65, 1.1)))
        self._x = int(side * SCREEN_WIDTH - width / 2) // PIXEL * PIXEL
        self._y = float(-height)
        size = min(1.0, height / 200)
        self._speed = self.SPEED[0] + (self.SPEED[1] - self.SPEED[0]) * size

    def draw(self, surface) -> None:
        if self._image is not None:
            surface.blit(self._image, (self._x, int(self._y) // PIXEL * PIXEL))
