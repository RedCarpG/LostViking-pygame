
import pygame

from collections.abc import Sequence
from src.game.animation.Effect import Effect
from src.util.type import Pos, Size
from src.helper.image import get_image
from .PlayerPlane import PlayerPlane
from .PlayerWeapon import PlayerWeapon, PlayerBullet


class PlayerViking(PlayerPlane):
    def __init__(self, pos):
        super().__init__(
            weapon=PlayerWeaponViking(self),
            pos=pos,
            frames={
                "BASE": get_image("PlayerPlane/VikingBase.png"),
                "IDLE": get_image("PlayerPlane/VikingMoveNormal.png"),

                "MOVE_UP": get_image("PlayerPlane/VikingMoveUp.png"),
                "MOVE_DOWN": get_image("PlayerPlane/VikingMoveNormal.png"),
                "DESTROY": get_image("PlayerPlane/VikingDestroy.png"),

                "HIT": get_image("PlayerPlane/VikingHit.png"),
                "INVINCIBLE": get_image("PlayerPlane/VikingInvincible.png")
            },
            frame_size=None)


class PlayerWeaponViking(PlayerWeapon):

    BASIC_DMG = 80
    INC_DMG = 5

    def __init__(self, player: PlayerPlane):
        super().__init__(player)
        self._bullet_type = PlayerBulletViking

    def shoot(self, pos: Pos):
        position1 = pos.move_x(-10)
        position2 = pos.move_x(10)
        self._bullet_type(position1, pygame.Vector2(0, -17),
                          self._damage, player=self.player)
        self._bullet_type(position2, pygame.Vector2(0, -17),
                          self._damage, player=self.player)

        if self._level >= 2:
            position1 = pos.move_x(-10)
            position2 = pos.move_x(10)
            self._bullet_type(
                position1, pygame.Vector2(-5, -17), self._damage, angle=20, player=self.player)
            self._bullet_type(position2, pygame.Vector2(
                5, -17), self._damage, angle=-20,  player=self.player)

        if self._level >= 3:
            self._bullet_type(
                position1, pygame.Vector2(-10, -17), self._damage, angle=30, player=self.player)
            self._bullet_type(position2, pygame.Vector2(
                10, -17), self._damage, angle=-30, player=self.player)


class PlayerBulletViking(PlayerBullet):

    def __init__(self, pos: Pos,
                 speed: Sequence[int, int],
                 damage,
                 player: PlayerPlane,
                 angle=None):
        super().__init__(pos=pos, speed=speed,
                         image=get_image("PlayerPlane/bullet.png"), player=player)
        self.damage = damage
        if angle:
            self._rotate(angle)

    def _rotate(self, angle: int) -> None:
        temp = self.rect.center
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=temp)

    def hit(self):
        Effect(
            Pos(self.rect.center).random_offset(5),
            frames={
                "IDLE": get_image("PlayerPlane/BulletHit.png"),
            },
            frame_size=Size([35, 19])
        )
        return super().hit()
