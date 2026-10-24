
import random

from pygame.math import Vector2
from pygame.sprite import Group
from src.game.animation import Effect
from src.helper.sound.sound_loader import play_sound
from src.setting import SCREEN_WIDTH
from src.game.enemy import EnemyI, EnemyBullet
from src.helper.image import get_image
from src.util.type import Pos, Size


class EnemyScout(EnemyI):

    MAX_HEALTH = 500
    SCORE = 500

    GROUP = Group()

    def __init__(self, pos: Pos):
        super().__init__(
            pos=pos,
            frames={
                "BASE": get_image("Enemy/Scout/ScoutBase.png"),
                "IDLE": get_image("Enemy/Scout/ScoutNormal.png"),
                "DESTROY": get_image("Enemy/Scout/ScoutDestroy.png"),
                "HIT": get_image("Enemy/Scout/ScoutHit.png"),
                "ATTACK": get_image("Enemy/Scout/ScoutAttack.png")
            },
            frame_size=None)
        self.GROUP.add(self)

    # --------------- Create function --------------- #

    @classmethod
    def add_enemy_scout(cls, num) -> bool:
        if len(cls.GROUP.sprites()) < 25:
            for i in range(num):
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = - 100

                EnemyScout(Pos([x, y]))
            return True
        return False

    def shoot(self, target):
        BulletScout(Pos(self.rect.center))

    def destroy(self, drop_supply=True) -> None:
        play_sound("SCOUT_DESTROY")
        return super().destroy(drop_supply)


class BulletScout(EnemyBullet):

    DAMAGE = 30
    SPEED = 5

    def __init__(self, pos: Pos):
        super().__init__(
            pos,
            speed=Vector2([0, self.SPEED]),
            damage=self.DAMAGE,
            image=get_image("Enemy/Laser2.png")
        )

    def hit(self, target=None):
        Effect(
            Pos(self.rect.center).random_offset(5),
            frames={
                "IDLE": get_image("Enemy/LaserHit.png"),
            },
            frame_size=Size([19, 19])
        )
        return super().hit()
