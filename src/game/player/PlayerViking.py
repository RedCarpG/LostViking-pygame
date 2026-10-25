import pygame
from pygame import Vector2

from src.game.animation import Effect, MuzzleFlash
from src.util.type import Pos, Size
from src.helper.image import get_image, get_rotated_image
from .PlayerPlane import PlayerPlane
from .PlayerWeapon import PlayerWeapon, PlayerBullet
from .LanzerTorpedo import LanzerTorpedo


class PlayerViking(PlayerPlane):
    """ The Viking switches between its two weapons, as it transforms in StarCraft II:
    twin gatling cannons (many fast shots, best against swarms and shields) and
    Lanzer Torpedoes (homing, best against armored ships)
    """

    def __init__(self, pos):
        super().__init__(
            weapons=[PlayerWeaponViking(self), PlayerTorpedoViking(self)],
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
    """ Twin gatling cannons. Level 1: two guns. 2: two angled shots. 3: two wider shots.
    4: shoots faster, the shots go through an enemy. 5: two more guns on the wings, the shots
    go through two enemies (they lose 30% of their damage each time, a shield stops them)
    """

    NAME = "TWIN GATLING"
    SWITCH_SOUND = "TRANSFORM_ASSAULT"

    BASIC_DMG = 80
    INC_DMG = 5
    FIRE_INTERVALS = (20, 20, 20, 16)
    # Enemies a shot goes through, by level
    PIERCE = (0, 0, 0, 1, 2)

    SPEED = 17
    # Guns, from the plane center (x) and top (y): the wing pods, and the wing tips (level 5)
    GUNS = ((-11, 10), (11, 10))
    WING_GUNS = ((-23, 13), (23, 13))

    def __init__(self, player: PlayerPlane):
        super().__init__(player)
        self._bullet_type = PlayerBulletViking

    def _fire(self, pos: Pos, dx, angle=None):
        self._bullet_type(pos, pygame.Vector2(dx, -self.SPEED), self._damage, angle=angle, player=self.player,
                          pierce=self.PIERCE[self._level - 1])

    def shoot(self, pos: Pos):
        left = pos.move_x(-10)
        right = pos.move_x(10)
        self._fire(left, 0)
        self._fire(right, 0)
        for gun in self.GUNS:
            MuzzleFlash(self.player, gun)

        if self._level >= 2:
            self._fire(left, -5, angle=20)
            self._fire(right, 5, angle=-20)

        if self._level >= 3:
            self._fire(left, -10, angle=30)
            self._fire(right, 10, angle=-30)

        if self._level >= 5:
            self._fire(pos.move([-22, 8]), 0)
            self._fire(pos.move([22, 8]), 0)
            for gun in self.WING_GUNS:
                MuzzleFlash(self.player, gun)


class PlayerTorpedoViking(PlayerWeapon):
    """ Lanzer Torpedoes, fired in salvos of pairs. Level 1: one pair. 2: faster.
    3: two pairs. 4: faster. 5: three pairs. Armored ships take extra damage (see LanzerTorpedo).
    Against light ships and shields the twin gatling does more damage
    """

    NAME = "LANZER TORPEDOES"
    SHOOT_SOUND = "TORPEDO_LAUNCH"
    SWITCH_SOUND = "TRANSFORM_FIGHTER"

    BASIC_DMG = 110
    INC_DMG = 20
    FIRE_INTERVALS = (40, 34, 40, 34, 30)
    # Torpedoes per salvo, by level
    SALVOS = (2, 2, 4, 4, 6)
    # Wing pods, from the plane center (x) and top (y)
    POD_X = 12
    POD_Y = 16

    def shoot(self, pos: Pos):
        plane = self.player.rect
        for i in range(self.SALVOS[self._level - 1]):
            side = -1 if i % 2 == 0 else 1
            pair = i // 2
            # Each pair drops a little further out and ignites a little later: a ripple
            LanzerTorpedo((plane.centerx + side * self.POD_X, plane.top + self.POD_Y),
                          eject=Vector2(side * (1.6 + pair * 1.4), 1.0 + pair * 0.5),
                          ignite=5 + pair * 5, damage=self._damage, player=self.player, rank=pair)


class PlayerBulletViking(PlayerBullet):

    # Piercing shots glow green, the color of the gatling: (multiply, then add)
    PIERCE_TINT = ((150, 255, 170), (40, 90, 40))
    _pierce_image = None

    def __init__(self, pos: Pos,
                 speed: pygame.Vector2,
                 damage,
                 player: PlayerPlane,
                 angle=None,
                 pierce=0):
        image = get_image("PlayerPlane/bullet.png")
        if pierce:
            image = self._piercing_image(image)
        super().__init__(pos=pos, speed=speed, image=image, player=player)
        self.damage = damage
        self.pierce = pierce
        if angle:
            self._rotate(angle)

    @classmethod
    def _piercing_image(cls, image):
        if cls._pierce_image is None:
            multiply, add = cls.PIERCE_TINT
            cls._pierce_image = image.copy()
            cls._pierce_image.fill(multiply, special_flags=pygame.BLEND_RGB_MULT)
            cls._pierce_image.fill(add, special_flags=pygame.BLEND_RGB_ADD)
        return cls._pierce_image

    def _rotate(self, angle: int) -> None:
        temp = self.rect.center
        self.image = get_rotated_image(self.image, angle)
        self.rect = self.image.get_rect(center=temp)

    def _spark(self):
        Effect(
            Pos(self.rect.center).random_offset(5),
            frames={
                "IDLE": get_image("PlayerPlane/BulletHit.png"),
            },
            frame_size=Size([35, 19])
        )

    def hit(self):
        self._spark()
        return super().hit()

    def pass_through(self):
        self._spark()
