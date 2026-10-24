"""
Enemy Basic abstract classes, which defines its general behaviors,
Initialization should be made in the implementation of the class
"""
import math
from enum import Enum
from pygame import Vector2

from src.util.type import Pos, Size
from src.util.angle import cal_angle, angle_diff, turn_toward
from .EnemyI import EnemyI


class EnemyIIIActionPhase(Enum):
    Move = 0
    Idle = 1


class EnemyIII(EnemyI):
    """ Third type of Enemy: flies from point to point along `path`,
    stops at each point and attacks the player
    """

    MAX_SPEED_Y = 5
    ACC_Y = 0.2

    # Steering: max turn per frame (degrees) and distance where it starts to slow down
    TURN_SPEED = 6
    ARRIVE_RADIUS = 120

    ATTACK_SPEED = 0

    STAY_DURATION = 100

    DROP_SUPPLY_CHANCE = 0.3

    def __init__(
            self,
            pos: Pos,
            frames,
            frame_size: Size = None,
            path: list = None):

        self.angle = 0

        super().__init__(pos, frames, frame_size,
                         **{"enable_rotate": True, "angle": self.angle})

        self.path = path
        # Speed along the current heading, starts fast (launched from its carrier)
        self._move_speed = self.MAX_SPEED_Y

        self.state = EnemyIIIActionPhase.Move
        self._count_action_idle = self.STAY_DURATION
        self.enter_action_move_phase()

    # --------------- Main action status --------------- #

    def action(self, *args, **kwargs):
        if self.state == EnemyIIIActionPhase.Move:
            self._action_move()
        else:
            self._action_idle()

    # --------------- Sub action status --------------- #
    def enter_action_move_phase(self):
        self.state = EnemyIIIActionPhase.Move

    def _action_move(self):
        target = Vector2(self.path[0])
        to_target = target - self._pos
        distance = to_target.length()

        if distance <= max(3, self._move_speed):
            # Arrived
            self._move_speed = 0
            self._speed.update(0, 0)
            self.path.pop(0)
            if len(self.path) > 0:
                self.enter_action_idle_phase()
            else:
                self.kill()
            return

        # Turn smoothly toward the target
        target_angle = cal_angle(Pos(list(self._pos)), Pos(list(target)))
        self.angle = turn_toward(self.angle, target_angle, self.TURN_SPEED)

        # Slow down when close to the target, or while still facing away from it
        desired_speed = self.MAX_SPEED_Y * min(1, distance / self.ARRIVE_RADIUS)
        facing = math.cos(math.radians(angle_diff(self.angle, target_angle)))
        desired_speed = max(0.5, desired_speed * max(0.25, facing))
        # Accelerate gently, brake a bit faster
        change = desired_speed - self._move_speed
        self._move_speed += max(-self.ACC_Y * 2, min(self.ACC_Y, change))

        if distance < 20:
            # Final approach: head straight to the point so it can not circle around it
            self._speed = to_target.normalize() * min(self._move_speed, distance)
        else:
            self._speed = Vector2(0, self._move_speed).rotate(-self.angle)

    def enter_action_idle_phase(self):
        self._count_action_idle = self.STAY_DURATION
        self.state = EnemyIIIActionPhase.Idle

    def _action_idle(self, *args, **kwargs):
        from src.game.groups import G_Player1
        player = G_Player1.sprite
        # Turn to face the player while waiting
        self.angle = turn_toward(
            self.angle, cal_angle(Pos(list(self._pos)), Pos(player.rect.center)), self.TURN_SPEED / 2)
        if not self._count_action_idle:
            self.attack(player)
            self.enter_action_move_phase()
        else:
            self._count_action_idle -= 1
