""" Short texts rising from a point and fading out: points won, what a pickup gave """
import pygame
from pygame.sprite import Sprite

from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.game.groups import G_Texts
from src.helper.font import get_font, render_text
from .pixel_fx import PIXEL

# Colors by meaning
SCORE_COLOR = (255, 232, 140)
LIFE_COLOR = (120, 235, 150)
BOMB_COLOR = (255, 186, 90)
WEAPON_COLOR = (120, 205, 255)
MAX_COLOR = (170, 180, 210)
WARNING_COLOR = (255, 100, 90)
# Dark outline: the text stays readable over explosions
OUTLINE_COLOR = (16, 12, 28)

_SCREEN = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)


class FloatingText(Sprite):

    FONT = "FloatText"
    DURATION = 48
    # The last frames fade out
    FADE = 16
    # Rises fast, then slows down
    RISE = 1.6
    DRAG = 0.94
    # Starts this far above the given point
    OFFSET = 18

    # Rendered texts, by (text, color)
    _cache = {}

    def __init__(self, pos, text, color=SCORE_COLOR, duration=DURATION) -> None:
        super().__init__(G_Texts)
        key = (text, color)
        image = self._cache.get(key)
        if image is None:
            image = render_text(get_font(self.FONT), text, color, spacing=0, glow_color=OUTLINE_COLOR)
            self._cache[key] = image
        # Own copy: its alpha changes while it fades
        self.image = image.copy()
        self.rect = self.image.get_rect(center=(round(pos[0]), round(pos[1]) - self.OFFSET))
        self.rect.clamp_ip(_SCREEN)
        self._y = float(self.rect.y)
        self._speed = self.RISE
        self._duration = duration
        self._age = 0

    def update(self) -> None:
        self._age += 1
        if self._age >= self._duration:
            self.kill()
            return
        self._y -= self._speed
        self._speed *= self.DRAG
        # Snap to the pixel grid of the art
        self.rect.y = int(self._y) // PIXEL * PIXEL
        left = self._duration - self._age
        if left < self.FADE:
            self.image.set_alpha(255 * left // self.FADE)
