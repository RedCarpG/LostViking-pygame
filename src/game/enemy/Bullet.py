import pygame
from pygame import Vector2

from src.util import if_in_screen
from src.util.type import Pos, Size
from src.helper.image import get_image, get_rotated_image

from src.game.groups import G_Enemy_Bullets
from src.game.animation.Effect import Effect


class EnemyBullet(pygame.sprite.Sprite):
    """ Basic Bullet Class
    """

    # Spark shown where the bullet hits: (image, frame size), None: no spark
    HIT_EFFECT = ("Enemy/LaserHit.png", (19, 19))
    # The spark lands up to this many pixels away from the bullet
    HIT_SPREAD = 5

    def __init__(self,
                 pos: Pos,
                 speed: Vector2,
                 damage: int,
                 image: pygame.Surface,
                 angle: float = 0):
        """ :param angle: turn the image and the speed by `angle` degrees (counterclockwise) """
        super().__init__(G_Enemy_Bullets)

        self.image = image
        self.rect = self.image.get_rect(center=pos.to_list())
        # Exact position: slow or diagonal bullets would stall with whole pixels only
        self._pos = Vector2(self.rect.center)
        self.speed = speed
        self.damage = damage
        if angle:
            self._rotate(angle)

    def update(self):
        # General update method for bullets
        if if_in_screen(self.rect):
            self._move()
        else:
            self.kill()

    def hit(self, target=None):
        # General get hit method for bullets
        if self.HIT_EFFECT is not None:
            image, size = self.HIT_EFFECT
            Effect(
                Pos(self.rect.center).random_offset(self.HIT_SPREAD),
                frames={
                    "IDLE": get_image(image),
                },
                frame_size=Size(size)
            )
        self.kill()

    def _rotate(self, angle) -> None:
        center = self.rect.center
        self.image = get_rotated_image(self.image, angle)
        self.rect = self.image.get_rect(center=center)
        self.speed = self.speed.rotate(-angle)

    def _move(self):
        self._pos += self.speed
        self.rect.center = (round(self._pos.x), round(self._pos.y))
