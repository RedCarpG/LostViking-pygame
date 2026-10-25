""" Asteroids: the rock field between the Terran Starport and the Protoss outposts

Spinning rocks in three sizes drifting down. A large rock breaks into two medium rocks,
a medium rock into two small ones. Large and medium rocks are armored: the Lanzer Torpedoes
crack them faster, the gatling is better against the small ones. Flying into a rock hurts
and breaks it. Rocks are cover: enemy shots stop at them and chip them (beams go through),
and a rock broken by enemy fire gives no points. The sheets (SPIN_FRAMES frames of a turn, lit from a fixed light) are made by
tools/pixel_art/make_asteroids.py.
"""
import random

from pygame import Vector2
from pygame.sprite import Group

from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.game.enemy import EnemyI, EnemyBullet
from src.game.groups import G_Enemy_Bullets
from src.game.animation import Spark
from src.game.animation.pixel_fx import PIXEL
from src.helper.image import get_image
from src.util.type import Pos, Size

# Debris colors, from the first to the last frame of a piece
DEBRIS_COLORS = {
    0: ((188, 164, 134), (120, 98, 86), (60, 48, 54)),
    1: ((182, 188, 198), (112, 118, 132), (52, 56, 72)),
}
VARIANTS = (0, 1)


def _sheet(size, variant):
    return get_image(f"Enemy/Asteroid/Asteroid{size}{variant}.png")


def images():
    """ Image files of every rock (for the asset manifest) """
    return [f"Enemy/Asteroid/Asteroid{size}{variant}.png" for size in ("Large", "Medium", "Small")
            for variant in VARIANTS]


class Asteroid(EnemyI):
    # Frames of a turn in the sheets (see make_asteroids.py)
    SPIN_FRAMES = 16

    # Set by each size
    SIZE = None
    # Rocks it breaks into
    PIECES = ()
    # Pixels per frame it drifts down, and at most this fast sideways
    SPEED = (1.0, 2.0)
    DRIFT = 0.6
    # Spin frames per game frame
    SPIN = (0.06, 0.14)
    DEBRIS = 8

    DROP_SUPPLY_CHANCE = 0
    DESTROY_SOUND = "ENEMY_DESTROY"
    # Removed once this far out of the screen
    MARGIN = 120

    GROUP = Group()

    def __init__(self, pos: Pos, velocity=None, variant=None):
        """ :param velocity: pixels per frame, random (drifting down) if None """
        self.variant = random.choice(VARIANTS) if variant is None else variant
        sheet = _sheet(self.SIZE, self.variant)
        size = sheet.get_height()
        super().__init__(
            pos=pos,
            frames={"BASE": sheet, "IDLE": sheet, "DESTROY": sheet},
            frame_size=Size([size, size]))
        self.GROUP.add(self)
        if velocity is None:
            velocity = Vector2(random.uniform(-self.DRIFT, self.DRIFT), random.uniform(*self.SPEED))
        self._speed = Vector2(velocity)
        # Turns either way, from a random frame
        self._spin = float(random.randrange(self.SPIN_FRAMES))
        self._spin_speed = random.uniform(*self.SPIN) * random.choice((-1, 1))

    @classmethod
    def spawn(cls, rock=None, x=None) -> "Asteroid":
        """ A rock (one of the size classes) coming in from the top: a random size if None """
        rock = rock or random.choices((AsteroidLarge, AsteroidMedium, AsteroidSmall), weights=(2, 4, 3))[0]
        if x is None:
            x = random.randint(60, SCREEN_WIDTH - 60)
        return rock(Pos([x, -rock.HITBOX[1]]))

    # --------------- Spin --------------- #
    def anime(self, anime_freq=5):
        self._spin = (self._spin + self._spin_speed) % self.SPIN_FRAMES
        index = int(self._spin)
        if index != self._current_frame_index:
            self._current_frame_index = index
            self._render_frame()

    # --------------- Behavior --------------- #
    def action(self, *args, **kwargs) -> None:
        if self.rect.top > SCREEN_HEIGHT + self.MARGIN or self.rect.right < -self.MARGIN \
                or self.rect.left > SCREEN_WIDTH + self.MARGIN:
            self.kill()
            return
        self._block_shots()

    def _block_shots(self) -> None:
        """ Enemy shots that reach the rock stop there and chip it (the beams go through) """
        box = self.hitbox
        for shot in G_Enemy_Bullets.sprites():
            if isinstance(shot, EnemyBullet) and box.colliderect(shot.rect):
                shot.hit(target=self)
                self._chip(shot.damage)
                if not self.is_active:
                    return

    def _chip(self, damage) -> None:
        """ Damage from enemy fire: a flash only (no hit sound), and a rock it breaks drops nothing """
        self._health -= damage
        if self._health > 0:
            self._count_flash = self.FLASH_DURATION
        else:
            self.destroy(drop_supply=False)

    def shoot(self, target):
        pass

    def _damage_hull(self, damage) -> None:
        # Only a white flash: there is no hit sheet for each spin frame
        self._health -= damage
        if self._health > 0:
            self.hit_feedback()
        else:
            self.destroy()

    def destroy(self, drop_supply=True) -> None:
        if not self.is_active:
            return
        super().destroy(drop_supply)
        center = self.rect.center
        Spark.shards(center, self.DEBRIS, DEBRIS_COLORS[self.variant], speed=(2, 5), life=22,
                     size=PIXEL * 2)
        # The pieces fly apart, keeping some of the rock's speed
        for i, piece in enumerate(self.PIECES):
            side = -1 if i % 2 == 0 else 1
            offset = Vector2(side * self.HITBOX[0] / 4, random.uniform(-6, 6))
            velocity = self._speed * 1.6 + Vector2(side * random.uniform(0.8, 1.6), random.uniform(-0.2, 0.6))
            piece(Pos([center[0] + offset.x, center[1] + offset.y]), velocity, self.variant)
        self.kill()


class AsteroidSmall(Asteroid):
    SIZE = "Small"
    MAX_HEALTH = 100
    SCORE = 50
    COLLIDE_DAMAGE = 20
    HITBOX = (28, 28)
    SPEED = (2.0, 3.2)
    SPIN = (0.12, 0.25)
    DEBRIS = 5
    EXPLOSION = "small"
    SHAKE_DESTROY = 0.1
    KNOCKBACK = 2


class AsteroidMedium(Asteroid):
    SIZE = "Medium"
    MAX_HEALTH = 360
    SCORE = 150
    ARMORED = True
    COLLIDE_DAMAGE = 35
    HITBOX = (44, 44)
    SPEED = (1.5, 2.4)
    SPIN = (0.08, 0.16)
    PIECES = (AsteroidSmall, AsteroidSmall)
    DEBRIS = 9
    EXPLOSION = "small"
    SHAKE_DESTROY = 0.2
    KNOCKBACK = 1
    DROP_SUPPLY_CHANCE = 0.03


class AsteroidLarge(Asteroid):
    SIZE = "Large"
    MAX_HEALTH = 1000
    SCORE = 300
    ARMORED = True
    COLLIDE_DAMAGE = 60
    HITBOX = (68, 68)
    SPEED = (1.0, 1.7)
    SPIN = (0.05, 0.1)
    PIECES = (AsteroidMedium, AsteroidMedium)
    DEBRIS = 14
    EXPLOSION = "medium"
    SHAKE_DESTROY = 0.35
    KNOCKBACK = 0
    DROP_SUPPLY_CHANCE = 0.08
