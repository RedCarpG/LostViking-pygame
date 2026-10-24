import random
import pygame
from pygame import Vector2
from src.game.enemy import EnemyBoss, EnemyBullet
from src.game.animation import AttachEffect, Effect
from src.helper.image import get_image, get_scaled_image
from src.helper.sound import play_sound
from src.util.type import Pos, Size
from src.util.inertial import accelerate, decelerate
from .Interceptor import EnemyInterceptor
from . import CarrierLaser
from .CarrierLaser import LaserCarrier
from src.game.groups import G_Player1


def _sheet(name):
    return get_scaled_image(f"Enemy/Carrier/{name}.png", EnemyCarrier.SCALE)


class EnemyCarrier(EnemyBoss):
    # Drawn at 2x (an integer scale keeps the pixel art sharp)
    SCALE = 2

    # The top half of the ship stays above the screen
    STOP_TOP = -150

    MAX_INTERCEPTOR_NUMBER = 9

    # Frames between two attacks, faster below half health
    ATTACK_SPEED = 200
    ENRAGED_ATTACK_SPEED = 130
    FIRST_ATTACK_DELAY = 60

    # (attack, weight); the same attack is never used twice in a row
    ATTACKS = [("interceptors", 3), ("laser", 2), ("fan", 3), ("ring", 2), ("volley", 3)]

    FAN_BULLETS = 7
    FAN_SPREAD = 14         # degrees between two bullets
    FAN_SPEED = 5
    RING_BULLETS = 20
    RING_SPEED = 3.5
    SECOND_RING_DELAY = 24  # enraged: a second ring
    VOLLEY_BURSTS = 3
    VOLLEY_INTERVAL = 12
    VOLLEY_SPREAD = 8
    VOLLEY_SPEED = 9
    LASER_SWEEP_SPEED = 1.2

    def __init__(self):
        EnemyBoss.__init__(
            self,
            frames={
                "BASE": _sheet("CarrierBase"),
                "IDLE": _sheet("CarrierNormal"),
                "DESTROY": _sheet("CarrierDestroy"),
                "HIT": _sheet("CarrierHit"),
                "ATTACK_INTERCEPTOR": _sheet("CarrierAttack")
            },
            frame_size=None
        )
        play_sound("CARRIER_ARRIVE")
        self._count_attack_interval = self.FIRST_ATTACK_DELAY
        self._last_attack = None
        self._ring_offset = 0
        self._count_second_ring = 0
        self._volley_left = 0
        self._count_volley = 0
        self.laser = None

    @classmethod
    def prepare_images(cls):
        """ Scale the boss images now (while loading) instead of when it arrives """
        for name in ("CarrierBase", "CarrierNormal", "CarrierDestroy", "CarrierHit", "CarrierAttack"):
            _sheet(name)
        CarrierLaser.prepare()

    @property
    def enraged(self) -> bool:
        return self._health < self.MAX_HEALTH / 2

    @property
    def emitter(self) -> Vector2:
        """ Where bullets come out: the nose of the ship """
        return Vector2(self.rect.centerx, self.rect.bottom - 40)

    def laser_active(self) -> bool:
        return self.laser is not None and self.laser.alive()

    # --------------- Override Methods --------------- #
    def action(self):
        super().action()
        # Bullet patterns that last a few frames
        if self._volley_left > 0:
            if self._count_volley > 0:
                self._count_volley -= 1
            else:
                self._fire_volley()
                self._volley_left -= 1
                self._count_volley = self.VOLLEY_INTERVAL
        if self._count_second_ring > 0:
            self._count_second_ring -= 1
            if self._count_second_ring == 0:
                self._fire_ring()

    def _action_stay(self):
        if self.laser_active() and not self.laser.firing:
            # Hold still while the laser charges: the aiming line shows where it will hit
            self._speed.x = decelerate(self._speed.x, self.ACC_X)
        elif self.laser_active():
            # Sweep the laser slowly toward the player
            target_x = G_Player1.sprite.rect.centerx
            if abs(target_x - self.rect.centerx) < 8:
                self._speed.x = decelerate(self._speed.x, self.ACC_X)
            else:
                self._move_x_direction = 1 if target_x > self.rect.centerx else -1
                self._speed.x = accelerate(self._speed.x, self.LASER_SWEEP_SPEED,
                                           self._move_x_direction, self.ACC_X)
        else:
            super()._action_stay()

    def attack(self, target):
        if self._count_attack_interval > 0:
            self._count_attack_interval -= 1
        else:
            self.shoot(target)
            self._count_attack_interval = self.ENRAGED_ATTACK_SPEED if self.enraged else self.ATTACK_SPEED

    def shoot(self, target):
        """ Pick the next attack """
        choices = []
        for name, weight in self.ATTACKS:
            if name == self._last_attack:
                continue
            if name == "interceptors" and len(EnemyInterceptor.GROUP) >= self.MAX_INTERCEPTOR_NUMBER // 2:
                continue
            if name == "laser" and self.laser_active():
                continue
            choices.append((name, weight))
        if not choices:
            choices = [("fan", 1)]
        name = random.choices([c[0] for c in choices], weights=[c[1] for c in choices])[0]
        self._last_attack = name
        getattr(self, f"_attack_{name}")()

    def destroy(self) -> None:
        if not self.is_active:
            return
        for each in EnemyInterceptor.GROUP:
            each.destroy(False)
        if self.laser_active():
            self.laser.kill()
        self._volley_left = 0
        self._count_second_ring = 0
        return super().destroy()

    def final_blast(self):
        play_sound("CARRIER_DESTROY")
        super().final_blast()

    # --------------- Attacks --------------- #
    def _wind_up(self, callback):
        """ Play the attack animation (a warning), then call `callback` """
        def fire():
            if self.is_active:
                callback()
        AttachEffect(
            self,
            frames={
                "IDLE": self.frames["ATTACK_INTERCEPTOR"]
            },
            frame_size=None,
            enable_rotate=False,
            cb_func=fire
        )

    def _aim(self, origin) -> Vector2:
        """ Unit vector from `origin` toward the player """
        direction = Vector2(G_Player1.sprite.rect.center) - origin
        return direction.normalize() if direction.length() > 0 else Vector2(0, 1)

    def _attack_interceptors(self):
        def launch():
            if len(EnemyInterceptor.GROUP.sprites()) < self.MAX_INTERCEPTOR_NUMBER:
                pos = self.rect.center
                EnemyInterceptor(Pos(pos), [[pos[0], pos[1] + 300]])
                # Launch the next one after another attack animation, until the limit is reached
                self._wind_up(launch)
        self._wind_up(launch)

    def _attack_laser(self):
        # Charges, then fires (see CarrierLaser)
        self.laser = LaserCarrier(self)

    def _attack_fan(self):
        def fire():
            origin = self.emitter
            aim = self._aim(origin)
            for i in range(self.FAN_BULLETS):
                angle = (i - (self.FAN_BULLETS - 1) / 2) * self.FAN_SPREAD
                BulletCarrierOrb(origin, aim.rotate(angle) * self.FAN_SPEED, "Cyan")
            play_sound("PHOENIX_LASER")
        self._wind_up(fire)

    def _attack_ring(self):
        def fire():
            self._fire_ring()
            if self.enraged:
                self._count_second_ring = self.SECOND_RING_DELAY
        self._wind_up(fire)

    def _fire_ring(self):
        origin = self.emitter
        step = 360 / self.RING_BULLETS
        for i in range(self.RING_BULLETS):
            BulletCarrierOrb(origin, Vector2(0, 1).rotate(self._ring_offset + i * step) * self.RING_SPEED, "Pink")
        # Turn the next ring by half a step
        self._ring_offset += step / 2
        play_sound("PHOENIX_LASER")

    def _attack_volley(self):
        def fire():
            self._volley_left = self.VOLLEY_BURSTS
            self._count_volley = 0
        self._wind_up(fire)

    def _fire_volley(self):
        origin = self.emitter
        aim = self._aim(origin)
        for angle in (-self.VOLLEY_SPREAD, 0, self.VOLLEY_SPREAD):
            BulletCarrierBolt(origin, aim.rotate(angle) * self.VOLLEY_SPEED)
        play_sound("INTERCEPTOR_LASER")

    @classmethod
    def add_enemy_carrier(cls):
        EnemyCarrier()


class BulletCarrierOrb(EnemyBullet):
    """ Energy orb of the fan and ring attacks """

    DAMAGE = 25

    def __init__(self, pos: Vector2, velocity: Vector2, color: str):
        super().__init__(
            Pos([pos.x, pos.y]),
            speed=velocity,
            damage=self.DAMAGE,
            image=get_image(f"Enemy/Carrier/Orb{color}.png")
        )

    def hit(self, target=None):
        Effect(
            Pos(self.rect.center).random_offset(4),
            frames={
                "IDLE": get_image("Enemy/LaserHit.png"),
            },
            frame_size=Size([19, 19])
        )
        return super().hit()


class BulletCarrierBolt(EnemyBullet):
    """ Fast aimed bolt of the volley attack """

    DAMAGE = 30

    def __init__(self, pos: Vector2, velocity: Vector2):
        # The art points down: turn it to the direction it flies
        angle = -Vector2(0, 1).angle_to(velocity)
        super().__init__(
            Pos([pos.x, pos.y]),
            speed=velocity,
            damage=self.DAMAGE,
            image=pygame.transform.rotate(get_image("Enemy/Laser2.png"), angle)
        )

    def hit(self, target=None):
        Effect(
            Pos(self.rect.center).random_offset(4),
            frames={
                "IDLE": get_image("Enemy/LaserHit.png"),
            },
            frame_size=Size([19, 19])
        )
        return super().hit()

