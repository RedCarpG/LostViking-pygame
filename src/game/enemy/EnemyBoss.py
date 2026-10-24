
from enum import Enum
import random
import pygame
from src.game.groups import G_BOSS
from src.util.type import Pos, Size
from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.util.inertial import decelerate, accelerate
from src.game.groups import G_BOSS, G_Player1
from src.game.animation import Explosion, Spark, ScreenShake
from src.helper.sound import play_sound
from .EnemyI import EnemyI
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class BossActionPhase(Enum):
    MoveDown = 0
    Stay = 1
    MoveX = 2


class EnemyBoss(EnemyI):
    MAX_HEALTH = 30000
    SCORE = 15000

    ATTACK_SPEED = 100

    MAX_SPEED_X = 2
    MAX_SPEED_Y = 5
    ACC_X = 0.1
    ACC_Y = 0.1

    IDLE_DURATION = 200
    MOVE_X_DURATION = 200

    # Height of the top edge where the boss stops after coming in (can be above the screen)
    STOP_TOP = 0

    DROP_SUPPLY_CHANCE = 0

    SHAKE_DESTROY = 1.0

    # Death: explosions all over the ship for DEATH_DURATION frames, then a last big blast
    DEATH_DURATION = 120
    DEATH_BLAST_INTERVAL = 8
    SHAKE_DEATH_BLAST = 0.3

    # Flying into the boss destroys the player, the boss only takes some damage
    COLLIDE_SELF_DAMAGE = 500
    KNOCKBACK = 0

    def __init__(self, frames, frame_size: Size, **kwargs):
        super().__init__(pos=Pos([0, 0]), frames=frames,
                         frame_size=frame_size, **kwargs)
        self.add(G_BOSS)

        self.state = BossActionPhase.MoveDown

        self._move_x_direction = None
        self._count_action_idle = self.IDLE_DURATION
        self._count_action_move_x = self.MOVE_X_DURATION

        self.set_pos(Pos([SCREEN_WIDTH // 2, -self.rect.height]))
        self.enter_action_move_down_phase()
        self._count_dying = 0

    # -------------------- Main action states --------------------
    def action(self):
        if self.state == BossActionPhase.MoveDown:
            self._action_move_down()
        else:
            self._action_stay()
            player = G_Player1.sprites()[0]
            self.attack(target=player)

    # -------------------- Sub action states --------------------
    def enter_action_move_down_phase(self):
        self.state = BossActionPhase.MoveDown

    def _action_move_down(self):
        # Start braking just in time to stop at STOP_TOP
        braking_distance = self._speed.y ** 2 / (2 * self.ACC_Y)
        if self.STOP_TOP - self.rect.top <= braking_distance:
            self._speed.y = decelerate(self._speed.y, self.ACC_Y)
            if self._speed.y == 0:
                self.enter_action_stay_phase()

    def enter_action_stay_phase(self):
        self._count_action_idle = self.IDLE_DURATION
        self.state = BossActionPhase.Stay
        self._move_x_direction = random.choice([1, -1])

    def _action_stay(self):
        if self._count_action_idle > 0:
            self._count_action_idle -= 1
        else:

            if self._count_action_move_x > 0:
                # Accelerate (if not max) and count down
                self._speed.x = accelerate(self._speed.x,
                                           self.MAX_SPEED_X,
                                           self._move_x_direction,
                                           self.ACC_X)
                self._count_action_move_x -= 1
            else:
                # Decelerate in X direction and enter idle phase
                self._speed.x = decelerate(self._speed.x, self.ACC_X)
                if self._speed.x == 0:
                    self._count_action_move_x = self.MOVE_X_DURATION
                    self._count_action_idle = self.IDLE_DURATION

    # -------------------- Behaviors --------------------
    def _move(self) -> None:
        super()._move()
        # Bounce on the screen edges (only when moving outwards, so it does not get stuck flipping)
        if (self.rect.left < 0 and self._speed.x < 0) or (self.rect.right > SCREEN_WIDTH and self._speed.x > 0):
            self._move_x_direction = -self._move_x_direction
            self._speed.x = -self._speed.x

    def collide_player(self) -> None:
        self.hit(self.COLLIDE_SELF_DAMAGE)

    # -------------------- Death --------------------
    @property
    def dying(self) -> bool:
        return self._count_dying > 0

    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        if self._count_dying > 0 and self.alive():
            self._update_dying()

    def anime_end_loop_hook(self):
        # While dying, the ship stays until the last blast
        if self._count_dying == 0:
            super().anime_end_loop_hook()

    def destroy(self, drop_supply=True) -> None:
        """ Start the death: explosions all over the ship, then a last big blast (see final_blast) """
        if self._count_dying > 0 or not self.is_active:
            return
        self._health = 0
        self.is_active = False
        self._speed *= 0
        self._count_dying = self.DEATH_DURATION
        play_sound("ENEMY_DESTROY")

    def _update_dying(self):
        self._count_dying -= 1
        if self._count_dying == 0:
            self.final_blast()
        elif self._count_dying % self.DEATH_BLAST_INTERVAL == 0:
            # Somewhere on the part of the ship that is on screen
            area = self.rect.inflate(-self.rect.width // 4, -self.rect.height // 4)
            area = area.clip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pos = (random.randint(area.left, area.right), random.randint(area.top, area.bottom))
            Explosion(pos, random.choice(("medium", "medium", "large")))
            ScreenShake.add(self.SHAKE_DEATH_BLAST)
            self._count_flash = self.FLASH_DURATION
            if self._count_dying % (self.DEATH_BLAST_INTERVAL * 2) == 0:
                play_sound("ENEMY_DESTROY")

    def final_blast(self):
        """ The last big explosion: the ship breaks apart (destroy animation) """
        visible = self.rect.clip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        x, y = visible.center
        for i, (dx, dy) in enumerate(((0, 0), (-70, -40), (70, -30), (-30, 60), (40, 70))):
            Explosion((x + dx, y + dy), "large", delay=i * 4)
        Spark.burst((x, y), 30, 120)
        ScreenShake.add(self.SHAKE_DESTROY)
        self.set_anime_state("DESTROY")
