import pygame
from pygame.sprite import Sprite
from src.game.groups import G_Effects
from src.game.TestMode import TestMode


class EnemyStatusBar(Sprite):
    """ Small shield / health bars shown above an enemy for a while after it is hit """

    WIDTH = 64
    BAR_HEIGHT = 4
    SHOW_DURATION = 180
    FADE_DURATION = 30

    SHIELD_COLOR = (90, 200, 255)
    HEALTH_COLOR = (235, 70, 60)
    BACK_COLOR = (0, 0, 0, 170)

    def __init__(self, owner, has_shield: bool) -> None:
        super().__init__(G_Effects)
        self.owner = owner
        self.has_shield = has_shield
        bars = 2 if has_shield else 1
        self.image = pygame.Surface((self.WIDTH, bars * (self.BAR_HEIGHT + 1) + 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self._count_show = 0
        self._drawn_values = None

    def show(self) -> None:
        # Only a test mode tool, hidden in the normal game
        if TestMode.enabled:
            self._count_show = self.SHOW_DURATION

    def update(self) -> None:
        if not self.owner.alive() or not self.owner.is_active:
            self.kill()
            return
        self.rect.midbottom = (self.owner.rect.centerx, self.owner.rect.top - 2)
        if self._count_show > 0:
            self._count_show -= 1

        alpha = 255 if self._count_show > self.FADE_DURATION else int(
            255 * self._count_show / self.FADE_DURATION)
        shield = self.owner.shield if self.has_shield else 0
        values = (shield, self.owner.health, alpha)
        if values != self._drawn_values:
            self._drawn_values = values
            self._redraw(shield, alpha)

    def _redraw(self, shield, alpha) -> None:
        self.image.fill((0, 0, 0, 0))
        if alpha == 0:
            return
        self.image.fill(self.BACK_COLOR)
        y = 1
        bars = []
        if self.has_shield:
            bars.append((shield / self.owner.MAX_SHIELD, self.SHIELD_COLOR))
        bars.append((self.owner.health / self.owner.MAX_HEALTH, self.HEALTH_COLOR))
        for ratio, color in bars:
            width = int((self.WIDTH - 2) * max(0, min(1, ratio)))
            if width > 0:
                self.image.fill(color, (1, y, width, self.BAR_HEIGHT))
            y += self.BAR_HEIGHT + 1
        self.image.set_alpha(alpha)
