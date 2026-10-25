import math
import random

import pygame
from pygame.math import Vector2
from pygame.sprite import Group
from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.game.enemy import EnemyI, EnemyBullet
from src.game.groups import G_Player1
from src.helper.image import get_image
from src.util.angle import turn_toward
from src.util.type import Pos

_SCREEN = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)


def _angle_of(velocity: Vector2) -> float:
    """ Facing angle of a ship flying along `velocity` (0: facing down) """
    return -Vector2(0, 1).angle_to(velocity) if velocity.length() > 0 else 0


class EnemyScout(EnemyI):
    """ Protoss Scout. It flies one of several flight patterns (FLIGHTS), alone or in a
    formation (see spawn_wave), and turns to face where it flies
    """

    MAX_HEALTH = 500
    SCORE = 500

    DESTROY_SOUND = "SCOUT_DESTROY"

    # Ramming a Scout hurts (half the health) instead of destroying the plane at once
    COLLIDE_DAMAGE = 50
    ARMORED = True

    # At most this many Scouts at a time
    MAX_NUMBER = 25

    GROUP = Group()

    # Collision box once it has turned (the rect of a turned image is bigger)
    TURNED_HITBOX = (42, 48)

    # ------ Flight patterns
    STRAIGHT, WEAVE, DIVE, STRAFE, HOVER = "straight", "weave", "dive", "strafe", "hover"
    FLIGHTS = (STRAIGHT, WEAVE, DIVE, STRAFE, HOVER)

    SPEED = 3
    # Degrees per frame it turns to its flight direction
    TURN_RATE = 4
    # Weave: snakes down, WEAVE_WIDTH pixels to each side every WEAVE_PERIOD frames
    WEAVE_WIDTH = 110
    WEAVE_PERIOD = 160
    WEAVE_SPEED = 2.4
    # Dive: comes down to its dive height, then swoops toward where the plane was
    DIVE_HEIGHT = (200, 320)
    DIVE_SPEED = 6.5
    DIVE_ACCELERATION = 0.12
    DIVE_TURN = 2.2
    # Strafe: crosses the screen from a side, dropping shots straight down
    STRAFE_SPEED = 4
    STRAFE_BANK = 14
    # Hover: comes down to its hover height and stops, turns to the plane, fires a burst of
    # aimed shots, then leaves
    HOVER_HEIGHT = (140, 300)
    HOVER_DURATION = 130
    HOVER_AIM_TIME = 35
    BURST = 3
    BURST_INTERVAL = 10

    # Removed once it has left the screen by this many pixels, or after this many frames
    LEAVE_MARGIN = 120
    MAX_LIFE = 2400

    def __init__(self, pos: Pos, flight=STRAIGHT, **params):
        """ :param flight: one of FLIGHTS
        :param params: settings of the flight: `phase` (weave), `height` (dive, hover)
        """
        super().__init__(
            pos=pos,
            frames={
                "BASE": get_image("Enemy/Scout/ScoutBase.png"),
                "IDLE": get_image("Enemy/Scout/ScoutNormal.png"),
                "DESTROY": get_image("Enemy/Scout/ScoutDestroy.png"),
                "HIT": get_image("Enemy/Scout/ScoutHit.png"),
                "ATTACK": get_image("Enemy/Scout/ScoutAttack.png")
            },
            frame_size=None,
            enable_rotate=True)
        self.GROUP.add(self)
        self.flight = flight
        self._time = 0
        self._entered = False
        self._phase = params.get("phase", 0.0)
        self._height = params.get("height", random.uniform(*(
            self.DIVE_HEIGHT if flight == self.DIVE else self.HOVER_HEIGHT)))
        # Stage of the dive and hover flights
        self._stage = "in"
        self._count_stage = 0
        self._burst_left = 0
        self._dive_target = None
        self._direction = 1 if self._pos.x < SCREEN_WIDTH / 2 else -1
        if flight == self.STRAFE:
            self._speed.update(self._direction * self.STRAFE_SPEED, 0.4)
        self.angle = self._wanted_angle()
        self._render_frame()

    # --------------- Create functions --------------- #

    @classmethod
    def add_enemy_scout(cls, num, flight=STRAIGHT) -> bool:
        if len(cls.GROUP.sprites()) < cls.MAX_NUMBER:
            for i in range(num):
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = - 100

                EnemyScout(Pos([x, y]), flight)
            return True
        return False

    # Formations: each gives a list of (x, y, flight, flight settings)
    @staticmethod
    def _wave_single(rng):
        flight = rng.choice((EnemyScout.STRAIGHT, EnemyScout.WEAVE, EnemyScout.DIVE, EnemyScout.HOVER))
        return [(rng.randint(80, SCREEN_WIDTH - 80), -100, flight, {})]

    @staticmethod
    def _wave_v(rng):
        """ Five in a V, weaving together (same phase) or flying straight """
        flight = rng.choice((EnemyScout.STRAIGHT, EnemyScout.WEAVE))
        x = rng.randint(270, SCREEN_WIDTH - 270)
        phase = rng.uniform(0, math.tau)
        return [(x + dx, -100 + dy, flight, {"phase": phase})
                for dx, dy in ((0, 0), (-75, -65), (75, -65), (-150, -130), (150, -130))]

    @staticmethod
    def _wave_line(rng):
        """ Four strafing in a row from one side, at the same height """
        side = rng.choice((-1, 1))
        y = rng.randint(130, 360)
        start = -70 if side > 0 else SCREEN_WIDTH + 70
        return [(start - side * i * 95, y, EnemyScout.STRAFE, {}) for i in range(4)]

    @staticmethod
    def _wave_column(rng):
        """ Three one above the other: they dive at the plane one after the other """
        x = rng.randint(150, SCREEN_WIDTH - 150)
        height = rng.uniform(*EnemyScout.DIVE_HEIGHT)
        return [(x, -100 - i * 110, EnemyScout.DIVE, {"height": height}) for i in range(3)]

    @staticmethod
    def _wave_pincer(rng):
        """ Two hovering on both sides of the screen """
        height = rng.uniform(*EnemyScout.HOVER_HEIGHT)
        return [(x, -100, EnemyScout.HOVER, {"height": height})
                for x in (SCREEN_WIDTH // 4, SCREEN_WIDTH * 3 // 4)]

    WAVES = ("single", "v", "line", "column", "pincer")

    @classmethod
    def spawn_wave(cls, wave=None, rng=random) -> int:
        """ Bring in a formation (one of WAVES, a random one if None)
        :return: number of Scouts that came (0 if there are too many already)
        """
        wave = wave or rng.choice(cls.WAVES)
        ships = getattr(cls, f"_wave_{wave}")(rng)
        if len(cls.GROUP) + len(ships) > cls.MAX_NUMBER:
            return 0
        for x, y, flight, params in ships:
            EnemyScout(Pos([x, y]), flight, **params)
        return len(ships)

    # --------------- Flight --------------- #

    @property
    def hitbox(self):
        if self.angle == 0:
            # Not turned: the rect, as for the other enemies
            return None
        box = pygame.Rect(0, 0, *self.TURNED_HITBOX)
        box.center = self.rect.center
        return box

    def action(self, *args, **kwargs) -> None:
        self._time += 1
        getattr(self, f"_fly_{self.flight}")()
        self.angle = turn_toward(self.angle, self._wanted_angle(), self.TURN_RATE)

        on_screen = self.rect.colliderect(_SCREEN)
        self._entered = self._entered or on_screen
        margin = self.LEAVE_MARGIN * 2
        if (self._entered and not self.rect.colliderect(_SCREEN.inflate(margin, margin))) \
                or self._time > self.MAX_LIFE:
            self.kill()
            return
        # Only shoots from inside the screen; a hovering Scout fires its own bursts
        if on_screen and self.rect.top > 0 and self.flight != self.HOVER:
            self.attack(None)

    def _wanted_angle(self) -> float:
        if self.flight == self.STRAFE:
            # Faces down, its nose turned a little toward where it flies
            return self._direction * self.STRAFE_BANK
        if self.flight == self.HOVER and self._stage == "hold":
            player = G_Player1.sprite
            if player is not None:
                return _angle_of(Vector2(player.rect.center) - self._pos)
        if self.flight == self.WEAVE:
            # Banks half way into the weave
            return _angle_of(self._speed) * 0.5
        return _angle_of(self._speed)

    def _fly_straight(self):
        self._speed.update(0, self.SPEED)

    def _fly_weave(self):
        omega = math.tau / self.WEAVE_PERIOD
        # Speed of x = x0 + WIDTH * sin(omega * t + phase)
        self._speed.update(self.WEAVE_WIDTH * omega * math.cos(omega * self._time + self._phase), self.WEAVE_SPEED)

    def _fly_strafe(self):
        pass

    def _fly_dive(self):
        if self._stage == "in":
            self._speed.update(0, self.SPEED)
            if self._pos.y >= self._height:
                self._stage = "dive"
                player = G_Player1.sprite
                x = player.rect.centerx if player is not None else self._pos.x
                # Aims below the plane: it swoops through, then off the bottom of the screen
                self._dive_target = Vector2(x, SCREEN_HEIGHT + 200)
        else:
            wanted = self._dive_target - self._pos
            angle = (self._speed.angle_to(wanted) + 180) % 360 - 180
            self._speed.rotate_ip(max(-self.DIVE_TURN, min(self.DIVE_TURN, angle)))
            self._speed.scale_to_length(min(self.DIVE_SPEED, self._speed.length() + self.DIVE_ACCELERATION))

    def _fly_hover(self):
        if self._stage == "in":
            # Slows down on the way to its height
            left = self._height - self._pos.y
            self._speed.update(0, max(0.4, min(self.SPEED, left * 0.08)))
            if left <= 1:
                self._stage = "hold"
                self._count_stage = 0
                self._speed.update(0, 0)
        elif self._stage == "hold":
            self._count_stage += 1
            if self._count_stage == self.HOVER_AIM_TIME:
                self._burst_left = self.BURST
            if self._burst_left and (self._count_stage - self.HOVER_AIM_TIME) % self.BURST_INTERVAL == 0:
                self._burst_left -= 1
                self.shoot(None)
            if self._count_stage >= self.HOVER_DURATION:
                self._stage = "leave"
        else:
            self._speed.update(0, min(self.SPEED * 1.5, self._speed.y + 0.08))

    def shoot(self, target):
        # Fires where it faces, from its nose
        nose = Vector2(0, 38).rotate(-self.angle) + self.rect.center
        BulletScout(Pos([nose.x, nose.y]), self.angle)


class BulletScout(EnemyBullet):

    DAMAGE = 30
    SPEED = 5

    def __init__(self, pos: Pos, angle=0):
        super().__init__(
            pos,
            speed=Vector2([0, self.SPEED]),
            damage=self.DAMAGE,
            image=get_image("Enemy/Laser2.png"),
            angle=angle
        )
