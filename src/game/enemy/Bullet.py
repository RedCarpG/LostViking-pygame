
from collections.abc import Sequence
from abc import ABC, abstractmethod
import pygame
from pygame import Surface, Vector2

from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH
from src.util import if_in_screen
from src.util.type import Pos

from src.game.groups import G_Enemy_Bullets


class EnemyBullet(pygame.sprite.Sprite, ABC):
    """ Basic Bullet Class
    """

    def __init__(self,
                 pos: Pos,
                 speed: Vector2,
                 damage: int,
                 image: pygame.Surface, **kwargs):
        super().__init__(G_Enemy_Bullets)

        self.image = image
        self.rect = self.image.get_rect(center=pos.to_list())
        # Exact position: slow or diagonal bullets would stall with whole pixels only
        self._pos = Vector2(self.rect.center)
        self.speed = speed
        self.damage = damage

    def update(self):
        # General update method for bullets
        if if_in_screen(self.rect):
            self._move()
        else:
            self.kill()

    def hit(self, target=None):
        # General get hit method for bullets
        self.kill()

    def _move(self):
        self._pos += self.speed
        self.rect.center = (round(self._pos.x), round(self._pos.y))
