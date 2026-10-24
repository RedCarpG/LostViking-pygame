import math
import random
import pygame
from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.helper.image import load_image


def _make_glow(radius, color, max_alpha) -> pygame.Surface:
    """ Soft radial gradient used for the nebula clouds """
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    steps = 40
    for i in range(steps):
        alpha = int(max_alpha * (i / steps) ** 2)
        pygame.draw.circle(glow, (*color, alpha), (radius, radius),
                           int(radius * (1 - i / steps)))
    return glow


def _smooth_base() -> pygame.Surface:
    """ Smooth nebula (dark sky and soft clouds), tiling vertically.
    It is the source of the pixel-art nebula made by tools/pixel_art/make_nebula.py
    """
    rand = random.Random(7)
    base = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    base.fill(Background.BASE_COLOR)
    for _ in range(Background.NEBULA_NUMBER):
        radius = rand.randint(160, 340)
        glow = _make_glow(radius, rand.choice(Background.NEBULA_COLORS), rand.randint(55, 95))
        # Stretch into an ellipse
        size = (int(radius * 2 * rand.uniform(0.8, 1.6)),
                int(radius * 2 * rand.uniform(0.6, 1.2)))
        glow = pygame.transform.smoothscale(glow, size)
        x = rand.randint(-size[0] // 2, SCREEN_WIDTH - size[0] // 2)
        y = rand.randint(0, SCREEN_HEIGHT)
        # Draw again one screen above and below so the edges tile
        for offset in [-SCREEN_HEIGHT, 0, SCREEN_HEIGHT]:
            base.blit(glow, (x, y - size[1] // 2 + offset))
    return base


class Background:
    """ Scrolling pixel-art space background: a nebula layer and two star layers
    moving at different speeds (parallax). Everything sits on a 2x2 pixel grid.
    """

    # Size in screen pixels of one background art pixel
    PIXEL = 2

    BASE_COLOR = (6, 7, 18)
    NEBULA_COLORS = [(70, 30, 120), (25, 50, 125), (110, 25, 80), (15, 80, 100)]
    NEBULA_NUMBER = 8
    DUST_NUMBER = 260
    BASE_SPEED = 0.3

    # (number, size, speed, brightness steps)
    STAR_LAYERS = [
        (45, 2, 1.0, (120, 160, 200)),
        (14, 4, 2.6, (190, 225, 255)),
    ]

    def __init__(self) -> None:
        # Fixed seed so the background looks the same on every run
        self._random = random.Random(7)
        self._base = self._create_base()
        self._base_y = 0.0
        self._time = 0

        self._layers = []
        for number, size, speed, steps in self.STAR_LAYERS:
            stars = []
            for _ in range(number):
                stars.append([
                    self._random.uniform(0, SCREEN_WIDTH),
                    self._random.uniform(0, SCREEN_HEIGHT),
                    self._random.randrange(len(steps)),
                    self._random.uniform(0, math.tau)
                ])
            self._layers.append((stars, size, speed, steps))

    def _create_base(self) -> pygame.Surface:
        """ The slowest layer: the pixel-art nebula (made by tools/pixel_art/make_nebula.py)
        drawn at 2x, with dim dust stars. It tiles vertically so it can scroll forever.
        """
        nebula = load_image("Nebula.png", transparency=False)
        base = pygame.transform.scale(nebula, (SCREEN_WIDTH, SCREEN_HEIGHT))
        for _ in range(self.DUST_NUMBER):
            value = self._random.choice((45, 65, 90))
            x = self._random.randrange(SCREEN_WIDTH // self.PIXEL) * self.PIXEL
            y = self._random.randrange(SCREEN_HEIGHT // self.PIXEL) * self.PIXEL
            base.fill((value, value, min(255, value + 25)), (x, y, self.PIXEL, self.PIXEL))
        return base.convert()

    def update(self) -> None:
        self._time += 1
        self._base_y = (self._base_y + self.BASE_SPEED) % SCREEN_HEIGHT
        for stars, size, speed, steps in self._layers:
            for star in stars:
                star[1] += speed
                if star[1] > SCREEN_HEIGHT:
                    star[1] -= SCREEN_HEIGHT + size
                    star[0] = self._random.uniform(0, SCREEN_WIDTH)

    def draw(self, surface) -> None:
        # Scroll on the pixel grid
        y = int(self._base_y) // self.PIXEL * self.PIXEL
        surface.blit(self._base, (0, y))
        surface.blit(self._base, (0, y - SCREEN_HEIGHT))

        grid = self.PIXEL
        for stars, size, speed, steps in self._layers:
            for x, y, step, phase in stars:
                # Twinkle between a few hard brightness steps
                level = (step + int(1.5 + 1.5 * math.sin(self._time * 0.05 + phase))) % len(steps)
                value = steps[level]
                surface.fill((value, value, min(255, value + 30)),
                             (int(x) // grid * grid, int(y) // grid * grid, size, size))
