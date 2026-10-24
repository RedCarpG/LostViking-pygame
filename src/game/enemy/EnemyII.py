from enum import Enum

from src.util.type import Pos, Size
from src.game.groups import G_Player1
from src.util.inertial import accelerate, decelerate
from src.setting import SCREEN_HEIGHT
from src.util.angle import follow_angle
from .EnemyI import EnemyI


class EnemyIIActionPhase(Enum):
    Entrance = 0
    Stay = 1
    Leave = 2


class EnemyII(EnemyI):
    """ Enemy II has several different states and will target the player when shooting """

    STAY_DURATION = 1000

    MAX_SPEED_X = 10
    MAX_SPEED_Y = 1
    ACC_X = 0.2
    ACC_LEAVE = 0.02

    DROP_SUPPLY_CHANCE = 0.5

    SHAKE_DESTROY = 0.45

    def __init__(
            self,
            pos: Pos,
            frames,
            frame_size: Size = None,
            is_left=True):

        self.is_left = is_left
        if is_left:
            self.angle = 90
        else:
            self.angle = -90

        super().__init__(pos, frames, frame_size,
                         **{"enable_rotate": True, "angle": self.angle})

        self._count_action_stay = self.STAY_DURATION
        self._speed.y = 0

        self.state = EnemyIIActionPhase.Entrance

        self.enter_action_entrance_phase()

    # --------------- Main action status --------------- #

    def action(self, *args, **kwargs):
        if self.state == EnemyIIActionPhase.Entrance:
            self._action_entrance()
        else:
            if self.state == EnemyIIActionPhase.Stay:
                self._action_stay()
            else:
                self._action_leave()
            player = G_Player1.sprites()[0]
            self.aim(Pos(player.rect.center))
            self.attack(player)

    # --------------- Sub action status --------------- #

    def enter_action_entrance_phase(self):
        if self.is_left:
            self._speed.x = self.MAX_SPEED_X
        else:
            self._speed.x = -self.MAX_SPEED_X

        self._speed.y = 0
        self.state = EnemyIIActionPhase.Entrance
        self.set_anime_state("MOVE")

    def _action_entrance(self):
        self._speed.x = decelerate(self._speed.x, self.ACC_X)
        if self._speed.x == 0:
            self.enter_action_stay_phase()

    def enter_action_stay_phase(self):
        self.state = EnemyIIActionPhase.Stay
        self._speed.x = self._speed.y = 0
        self._count_action_stay = self.STAY_DURATION
        self.set_anime_state("IDLE")

    def _action_stay(self):
        self._count_action_stay -= 1
        if not self._count_action_stay:
            self.enter_action_leave_phase()

    def enter_action_leave_phase(self):
        self.state = EnemyIIActionPhase.Leave
        self._speed.x = 0
        self._speed.y = 0

    def _action_leave(self):
        # Ease into the leaving speed instead of starting at full speed
        self._speed.y = accelerate(self._speed.y, self.MAX_SPEED_Y, 1, self.ACC_LEAVE)
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    # --------------- Aim --------------- #

    def aim(self, point: Pos):
        self.angle = follow_angle(
            Pos(self.rect.center), point, self.angle, rotation_speed=2)
