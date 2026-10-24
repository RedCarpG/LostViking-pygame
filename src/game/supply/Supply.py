from enum import Enum
import abc
import math
import random

import pygame
from pygame import Vector2
from pygame.sprite import spritecollideany

from src.game.animation import AnimeSprite, Effect, FloatingText
from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.game.groups import G_Supplies, G_Players
from src.helper.image import get_image
from src.helper.sound import play_sound
from src.util.type import Pos, Size
from src.game.player import PlayerPlane


class SupplyStatus(Enum):
    Enter = 0
    Pop = 1
    Move = 2
    Leave = 3


class Supply(AnimeSprite, abc.ABC):
    """ A supply floats on smooth curves: it steers toward a target point that changes
    from time to time (inside the play area), then glides down and leaves the screen
    """

    MOVE_PHASE_DURATION = 1500
    # Frames before choosing another target point, when it was not reached
    TARGET_DURATION = 240

    MAX_SPEED = 1.6
    ENTER_SPEED = 2.5
    LEAVE_SPEED = 2.2
    # Steering: at most TURN_RATE degrees and ACC pixels/frame of speed change per frame,
    # so every turn is a wide arc (even a U-turn)
    TURN_RATE = 2.0
    ACC = 0.03
    # Slow down after popping out of a destroyed ship
    POP_DRAG = 0.93

    # Area where the target points are chosen
    AREA = pygame.Rect(70, 130, SCREEN_WIDTH - 140, int(SCREEN_HEIGHT * 0.62) - 130)

    # Gentle up and down bobbing (pixels, frames per cycle)
    BOB_HEIGHT = 3
    BOB_PERIOD = 90

    # Blinks during the last frames before it leaves, and while leaving
    BLINK_BEFORE_LEAVE = 180
    BLINK_PERIOD = 12

    # Drawn to the player once this close (pixels), at up to MAGNET_SPEED pixels per frame
    MAGNET_RADIUS = 110
    MAGNET_SPEED = 7

    SCORE = 1000

    # Set by each kind of supply: its SUPPLY_TYPE, its image, the effect and the
    # sound when it is picked up
    TYPE = None
    IMAGE = None
    GET_EFFECT = None
    GET_SOUND = None

    def __init__(self, pos: Pos = None):
        """ :param pos: where it appears, None: comes in from the top of the screen """
        super().__init__(frames={
            "BASE": get_image("Supply/SupplyBase.png"),
            "IDLE": get_image(self.IMAGE)
        }, frame_size=None)

        self.is_active = True

        self.add(G_Supplies)

        self._pos = Vector2(0, 0)
        self._velocity = Vector2(0, 0)
        self._target = Vector2(self.AREA.center)
        self._count_target = 0
        self._count_status_duration = self.MOVE_PHASE_DURATION
        self._time = random.uniform(0, self.BOB_PERIOD)

        self.set_pos(pos)
        if pos is None:
            self.enter_action_enter_phase()
        else:
            self.enter_action_move_phase()

    def update(self):
        self.anime()
        if self.is_active:
            if self.status == SupplyStatus.Pop:
                self._action_pop()
            elif self._action_magnet():
                pass
            elif self.status == SupplyStatus.Enter:
                self._action_enter()
            elif self.status == SupplyStatus.Move:
                self._action_move()
            else:
                self._action_leave()
            self._move()
            self._blink()
            self.collide_player(G_Players)
        else:
            self.kill()

    # Image while hidden by the blinking, made once
    _EMPTY = None
    _hidden = False

    def _blink(self):
        """ Warn that it is about to leave: hidden every other half period """
        leaving = self.status == SupplyStatus.Leave or (
            self.status == SupplyStatus.Move and self._count_status_duration < self.BLINK_BEFORE_LEAVE)
        hidden = leaving and int(self._time // (self.BLINK_PERIOD // 2)) % 2 == 1
        if hidden != self._hidden:
            self._hidden = hidden
            self._render_frame()

    def _render_frame(self) -> None:
        super()._render_frame()
        if self._hidden:
            if Supply._EMPTY is None:
                Supply._EMPTY = pygame.Surface((1, 1), pygame.SRCALPHA)
            self.image = Supply._EMPTY

    def get_by_player(self, player: PlayerPlane):
        text, color = self.apply(player)
        play_sound(self.GET_SOUND)
        Effect(
            pos=Pos(self.rect.center),
            frames={
                "IDLE": get_image(self.GET_EFFECT)
            },
            frame_size=Size([50, 50])
        )
        self.show_label(text, color)
        self.kill()

    @abc.abstractmethod
    def apply(self, player: PlayerPlane) -> tuple:
        """ Give the supply to the player
        :return: (text, color) of the label telling what it gave
        """

    # --------------- Phases --------------- #
    def enter_action_enter_phase(self):
        """ Come in from the top of the screen """
        self.status = SupplyStatus.Enter
        self._velocity = Vector2(0, self.ENTER_SPEED)

    def pop(self, direction: Vector2, speed=4.0):
        """ Burst out (from a destroyed ship), slow down, then float around """
        self.status = SupplyStatus.Pop
        self._velocity = Vector2(direction).normalize() * speed if direction.length() > 0 else Vector2(0, -speed)

    def enter_action_move_phase(self):
        self.status = SupplyStatus.Move
        self._count_status_duration = self.MOVE_PHASE_DURATION
        self._new_target()

    def enter_action_leave_phase(self):
        self.status = SupplyStatus.Leave

    def set_pos(self, point: Pos):
        if point is None:
            x = random.randint(self.rect.width, SCREEN_WIDTH - self.rect.width)
            self._pos = Vector2(x, -self.rect.height)
        else:
            self._pos = Vector2(point.to_list())
        self.rect.center = (round(self._pos.x), round(self._pos.y))

    def _new_target(self):
        self._target = Vector2(random.uniform(self.AREA.left, self.AREA.right),
                               random.uniform(self.AREA.top, self.AREA.bottom))
        self._count_target = self.TARGET_DURATION

    def _steer(self, wanted: Vector2):
        """ Turn the velocity smoothly toward `wanted` """
        speed = self._velocity.length()
        wanted_speed = wanted.length()
        if speed < 0.05:
            # Standing still: start moving toward `wanted`
            if wanted_speed > 0:
                self._velocity = wanted.normalize() * min(wanted_speed, self.ACC)
            return
        if wanted_speed > 0:
            angle = (self._velocity.angle_to(wanted) + 180) % 360 - 180
            self._velocity.rotate_ip(max(-self.TURN_RATE, min(self.TURN_RATE, angle)))
        speed += max(-self.ACC, min(self.ACC, wanted_speed - speed))
        self._velocity.scale_to_length(max(0.0, speed))

    def _action_enter(self):
        if self._pos.y > self.AREA.top:
            self.enter_action_move_phase()

    def _action_pop(self):
        self._velocity *= self.POP_DRAG
        if self._velocity.length() < self.MAX_SPEED * 0.5:
            self.enter_action_move_phase()

    def _action_move(self):
        to_target = self._target - self._pos
        self._count_target -= 1
        if to_target.length() < 40 or self._count_target <= 0:
            self._new_target()
            to_target = self._target - self._pos
        # Slow down a little near the target point
        speed = self.MAX_SPEED * min(1.0, 0.4 + to_target.length() / 200)
        self._steer(to_target.normalize() * speed if to_target.length() > 0 else Vector2(0, 0))

        self._count_status_duration -= 1
        if self._count_status_duration <= 0:
            self.enter_action_leave_phase()

    def _action_leave(self):
        self._steer(Vector2(0, self.LEAVE_SPEED))
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def _action_magnet(self) -> bool:
        """ Fly to the player when it is close, :return: True if it does """
        from src.game.groups import G_Player1
        player = G_Player1.sprite
        if player is None or not player.is_active:
            return False
        to_player = Vector2(player.rect.center) - self._pos
        distance = to_player.length()
        if distance > self.MAGNET_RADIUS or distance == 0:
            return False
        # Faster as it gets closer
        speed = self.MAGNET_SPEED * (1.2 - distance / self.MAGNET_RADIUS)
        self._velocity = to_player.normalize() * min(distance, max(self.MAX_SPEED, speed))
        return True

    def _move(self):
        self._pos += self._velocity
        # Keep it on screen (a drop near an edge must not get lost)
        if self.status != SupplyStatus.Leave:
            half_w, half_h = self.rect.width / 2, self.rect.height / 2
            self._pos.x = max(half_w, min(SCREEN_WIDTH - half_w, self._pos.x))
            if self.status != SupplyStatus.Enter:
                self._pos.y = max(half_h, min(SCREEN_HEIGHT - half_h, self._pos.y))
        self._time += 1
        bob = self.BOB_HEIGHT * math.sin(self._time * math.tau / self.BOB_PERIOD)
        self.rect.center = (round(self._pos.x), round(self._pos.y + bob))

    def collide_player(self, player_group):
        player = spritecollideany(self, player_group)
        # A destroyed plane (still exploding) can't pick up its own dropped upgrades
        if player and player.is_active:
            player.add_score(self.SCORE)
            self.get_by_player(player)

    def show_label(self, text, color) -> None:
        """ Tell the player what the supply gave """
        FloatingText((self.rect.centerx, self.rect.top - 6), text, color)
