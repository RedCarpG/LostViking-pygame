import pygame
from src.helper.font import FontEntity, get_font
from src.setting import COLOR
import math


class HealthBar:

    DROP_SPEED = 0.05

    def __init__(self, surface, rect, max_value) -> None:
        self.surface = surface
        self.max_health = max_value
        self.max_rect = rect
        self._max_length = rect.width

        self._current_health = max_value
        self._current_health_rect = rect.copy()
        self._drop_health = max_value
        self._drop_health_rect = rect.copy()
        self._health_diff = 0

        self.health_text = FontEntity(surface, get_font("HealthBar"),
                                      (f"{max_value}/{max_value}"), color=COLOR.WHITE)
        # Centered in the bar (the text stays centered when it changes)
        self.health_text.move_center(rect.center)

    def update(self, health):

        if self._current_health != health:
            if self._current_health < health:
                self._health_diff = 0
                self._health_diff = health
                self._drop_health = health
            elif self._current_health > health:
                self._health_diff = self._current_health - health
                self._drop_health = self._current_health
            self._current_health = health
            self._current_health_rect.width = health/self.max_health*self._max_length
            self.health_text.change_text(f"{health}/{self.max_health}")

        if self._drop_health > health:
            self._drop_health -= math.ceil(self._health_diff * self.DROP_SPEED)
            self._drop_health_rect.width = self._drop_health/self.max_health*self._max_length
        elif self._drop_health < health:
            self._drop_health = health

    def blit(self):
        pygame.draw.rect(self.surface, COLOR.RED,
                         self.max_rect)
        pygame.draw.rect(self.surface, COLOR.BROWN,
                         self._drop_health_rect)
        pygame.draw.rect(self.surface, COLOR.GREEN, self._current_health_rect)
        self.health_text.blit()
