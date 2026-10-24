import pygame

from src.game.animation.Effect import Effect
from src.util.type import Pos, Size
from src.helper.image import get_image, get_rotated_image
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
    """ Level 1: two guns. 2: two angled shots. 3: two wider shots.
    4: shoots faster. 5: two more guns on the wings
    """

    BASIC_DMG = 80
    INC_DMG = 5
    FIRE_INTERVALS = (20, 20, 20, 16)

    SPEED = 17

    def __init__(self, player: PlayerPlane):
        super().__init__(player)
        self._bullet_type = PlayerBulletViking

    def _fire(self, pos: Pos, dx, angle=None):
        self._bullet_type(pos, pygame.Vector2(dx, -self.SPEED), self._damage, angle=angle, player=self.player)

    def shoot(self, pos: Pos):
        left = pos.move_x(-10)
        right = pos.move_x(10)
        self._fire(left, 0)
        self._fire(right, 0)

        if self._level >= 2:
            self._fire(left, -5, angle=20)
            self._fire(right, 5, angle=-20)

        if self._level >= 3:
            self._fire(left, -10, angle=30)
            self._fire(right, 10, angle=-30)

        if self._level >= 5:
            self._fire(pos.move([-22, 8]), 0)
            self._fire(pos.move([22, 8]), 0)


class PlayerBulletViking(PlayerBullet):

    def __init__(self, pos: Pos,
                 speed: pygame.Vector2,
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
        self.image = get_rotated_image(self.image, angle)
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
