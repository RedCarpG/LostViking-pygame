import math
import random
import pygame
from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT


def _make_glow(radius, color, max_alpha) -> pygame.Surface:
    """ Soft radial gradient used for the nebula clouds """
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    steps = 40
    for i in range(steps):
        alpha = int(max_alpha * (i / steps) ** 2)
        pygame.draw.circle(glow, (*color, alpha), (radius, radius),
                           int(radius * (1 - i / steps)))
    return glow


class Background:
    """ Scrolling space background made of a nebula layer and two star layers
    moving at different speeds (parallax)
    """

    BASE_COLOR = (6, 7, 18)
    NEBULA_COLORS = [(70, 30, 120), (25, 50, 125), (110, 25, 80), (15, 80, 100)]
    NEBULA_NUMBER = 8
    DUST_NUMBER = 260
    BASE_SPEED = 0.3

    # (number, size, speed, brightness range)
    STAR_LAYERS = [
        (45, 2, 1.0, (110, 190)),
        (14, 3, 2.6, (200, 255)),
    ]

    def __init__(self) -> None:
        # Fixed seed so the background looks the same on every run
        self._random = random.Random(7)
        self._base = self._create_base()
        self._base_y = 0.0
        self._time = 0

        self._layers = []
        for number, size, speed, brightness in self.STAR_LAYERS:
            stars = []
            for _ in range(number):
                stars.append([
                    self._random.uniform(0, SCREEN_WIDTH),
                    self._random.uniform(0, SCREEN_HEIGHT),
                    self._random.randint(*brightness),
                    self._random.uniform(0, math.tau)
                ])
            self._layers.append((stars, size, speed))

    def _create_base(self) -> pygame.Surface:
        """ Pre-render the slowest layer: dark sky, nebula clouds and dim dust stars.
        It tiles vertically so it can scroll forever.
        """
        base = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        base.fill(self.BASE_COLOR)

        for _ in range(self.NEBULA_NUMBER):
            radius = self._random.randint(160, 340)
            glow = _make_glow(radius, self._random.choice(self.NEBULA_COLORS),
                              self._random.randint(55, 95))
            # Stretch into an ellipse
            size = (int(radius * 2 * self._random.uniform(0.8, 1.6)),
                    int(radius * 2 * self._random.uniform(0.6, 1.2)))
            glow = pygame.transform.smoothscale(glow, size)
            x = self._random.randint(-size[0] // 2, SCREEN_WIDTH - size[0] // 2)
            y = self._random.randint(0, SCREEN_HEIGHT)
            # Draw again one screen above and below so the edges tile
            for offset in [-SCREEN_HEIGHT, 0, SCREEN_HEIGHT]:
                base.blit(glow, (x, y - size[1] // 2 + offset))

        for _ in range(self.DUST_NUMBER):
            value = self._random.randint(35, 95)
            base.set_at((self._random.randrange(SCREEN_WIDTH),
                         self._random.randrange(SCREEN_HEIGHT)),
                        (value, value, min(255, value + 25)))
        return base.convert()

    def update(self) -> None:
        self._time += 1
        self._base_y = (self._base_y + self.BASE_SPEED) % SCREEN_HEIGHT
        for stars, size, speed in self._layers:
            for star in stars:
                star[1] += speed
                if star[1] > SCREEN_HEIGHT:
                    star[1] -= SCREEN_HEIGHT + size
                    star[0] = self._random.uniform(0, SCREEN_WIDTH)

    def draw(self, surface) -> None:
        y = int(self._base_y)
        surface.blit(self._base, (0, y))
        surface.blit(self._base, (0, y - SCREEN_HEIGHT))

        for stars, size, speed in self._layers:
            for x, y, brightness, phase in stars:
                # Slow twinkle
                value = int(brightness * (0.8 + 0.2 * math.sin(self._time * 0.05 + phase)))
                surface.fill((value, value, min(255, value + 30)),
                             (int(x), int(y), size, size))
