""" Ring closing onto the plane while it transforms (switches weapons), drawn in code as pixel art """
import math

import pygame
from pygame.sprite import Sprite

from src.game.groups import G_Effects
from .pixel_fx import canvas, upscale

# Color of each weapon: twin gatling (green, like its HUD icon), Lanzer Torpedoes (cyan)
SWITCH_COLORS = [(110, 235, 150), (110, 210, 255)]
WHITE = (240, 250, 255)

SIZE = 64           # art pixels
FRAMES = 10
FRAME_TIME = 2      # game frames per animation frame
TICKS = 8

_frames = {}


def _make_frames(color):
    frames = []
    center = SIZE // 2
    light = tuple(min(255, c + 80) for c in color)
    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        c = canvas(SIZE, SIZE)
        radius = 4 + 26 * (1 - t) ** 1.3
        pygame.draw.circle(c, color if t < 0.6 else light, (center, center), round(radius), 2 if t < 0.5 else 1)
        # Panel ticks folding in, turning a little every frame
        for k in range(TICKS):
            angle = k / TICKS * math.tau + t * 1.2
            for d in (radius + 3, radius + 4):
                c.set_at((round(center + math.cos(angle) * d), round(center + math.sin(angle) * d)), light)
        if f == FRAMES - 1:
            pygame.draw.circle(c, WHITE, (center, center), 3)
        frames.append(upscale(c))
    return frames


class TransformRing(Sprite):
    """ Follows `owner` (a plane), `weapon_index` picks the color """

    def __init__(self, owner, weapon_index) -> None:
        super().__init__(G_Effects)
        color = SWITCH_COLORS[weapon_index % len(SWITCH_COLORS)]
        if color not in _frames:
            _frames[color] = _make_frames(color)
        self._frames = _frames[color]
        self.owner = owner
        self._age = 0
        self.image = self._frames[0]
        self.rect = self.image.get_rect(center=owner.rect.center)

    def update(self) -> None:
        self._age += 1
        index = self._age // FRAME_TIME
        if index >= len(self._frames) or not self.owner.is_active:
            self.kill()
            return
        self.image = self._frames[index]
        self.rect = self.image.get_rect(center=self.owner.rect.center)
