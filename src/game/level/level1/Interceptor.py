import random
from pygame import Vector2
from pygame.transform import rotate
from pygame.sprite import Group
from src.game.animation import Effect
from src.helper.sound.sound_loader import play_sound
from src.game.enemy import EnemyIII, EnemyBullet
from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.helper.image import get_image
from src.util.angle import cal_angle
from src.util.type import Pos, Size


class EnemyInterceptor(EnemyIII):

    MAX_HEALTH = 500
    SCORE = 500

    MAX_SPEED_Y = 10
    ACC_Y = 0.5

    ATTACK_CHANCE = 0.5
    DROP_SUPPLY_CHANCE = 0.1

    # Bumping into one hurts (same as its laser) instead of destroying the player
    COLLIDE_DAMAGE = 35

    HITBOX = (20, 20)

    MOVE_RAD = 300

    MOVE_BOTTOM_LIMIT = int(SCREEN_HEIGHT * 3 / 4)
    MOVE_LEFT_LIMIT = int(SCREEN_WIDTH / 10)
    MOVE_RIGHT_LIMIT = int(SCREEN_WIDTH * 9 / 10)
    MOVE_UP_LIMIT = int(SCREEN_HEIGHT / 5)

    GROUP = Group()

    def __init__(self, pos, path):
        super().__init__(pos,
                         frames={
                             "BASE": get_image("Enemy/Interceptor/InterceptorBase.png"),
                             "IDLE": get_image("Enemy/Interceptor/InterceptorIdle.png"),
                             "MOVE": get_image("Enemy/Interceptor/InterceptorMove.png"),
                             "DESTROY": get_image("Enemy/Interceptor/InterceptorDestroy.png"),
                             "HIT": get_image("Enemy/Interceptor/InterceptorHit.png"),
                             "ATTACK": get_image("Enemy/Interceptor/InterceptorAttack.png")
                         },
                         frame_size=None,
                         path=path)
        self.GROUP.add(self)
        play_sound("INTERCEPTOR_CREATE")

    # --------------- Override Methods --------------- #
    def enter_action_move_phase(self):
        self._find_new_path()
        self.set_anime_state("MOVE")
        super().enter_action_move_phase()

    def enter_action_idle_phase(self):
        self.set_anime_state("IDLE")
        return super().enter_action_idle_phase()

    def shoot(self, target):
        if random.random() < self.ATTACK_CHANCE:
            play_sound("INTERCEPTOR_LASER")
            self_pos = Pos(self.rect.center)
            angle = cal_angle(self_pos, Pos(target.rect.center))
            BulletInterceptor(self_pos, angle)

    def _find_new_path(self):
        x = random.randint(max(self.MOVE_LEFT_LIMIT, self.rect.center[0] - self.MOVE_RAD),
                           min(self.MOVE_RIGHT_LIMIT, self.rect.center[0] + self.MOVE_RAD))
        y = random.randint(max(self.MOVE_UP_LIMIT, self.rect.center[1] - self.MOVE_RAD),
                           min(self.MOVE_BOTTOM_LIMIT, self.rect.center[1] + self.MOVE_RAD))
        self.path.append([x, y])

    def destroy(self, drop_supply=True) -> None:
        play_sound("ENEMY_DESTROY")
        return super().destroy(drop_supply)


class BulletInterceptor(EnemyBullet):

    DAMAGE = 35
    SPEED = 8

    def __init__(self, pos: Pos, angle):
        super().__init__(
            pos,
            speed=Vector2([0, self.SPEED]),
            damage=self.DAMAGE,
            image=get_image("Enemy/Laser2.png")
        )
        self._rotate(angle)

    def _rotate(self, angle: int) -> None:
        temp = self.rect.center
        self.image = rotate(self.image, angle)
        self.rect = self.image.get_rect(center=temp)
        self.speed = self.speed.rotate(-angle)

    def hit(self, target=None):
        Effect(
            Pos(self.rect.center).random_offset(5),
            frames={
                "IDLE": get_image("Enemy/LaserHit.png"),
            },
            frame_size=Size([19, 19])
        )
        return super().hit()
