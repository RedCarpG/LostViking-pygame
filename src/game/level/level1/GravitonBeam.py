""" Graviton Beam: the ability of the StarCraft II Phoenix, it lifts a unit and holds it helpless

1. AIM: a thin dashed line shows where the Phoenix is facing (it keeps turning to the plane)
2. LOCK: the line stops turning, turns bright and blinks fast: the last moment to move away
3. FIRE: the beam shoots along the line; if it touches the plane, the plane is caught
4. LIFT: the beam holds the plane: it is pulled toward the Phoenix and answers its controls
   badly. It ends after LIFT_FRAMES, or at once when the Phoenix's shield breaks or the
   Phoenix is destroyed: shoot it to break free
The Phoenix does not fire its laser while it channels the beam.
The beam is drawn in code as pixel art, straight onto the screen (see draw).
"""
import math

import pygame
from pygame import Vector2
from pygame.sprite import Sprite

from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.helper.sound import play_sound
from src.game.groups import G_Beams, G_Player1
from src.game.animation import FloatingText, ScreenShake, ScreenFX
from src.game.animation.FloatingText import WARNING_COLOR, WEAPON_COLOR
from src.game.animation.pixel_fx import PIXEL

# Palette (Protoss energy)
WHITE = (236, 246, 255)
CYAN = (110, 220, 255)
VIOLET = (156, 104, 255)
VIOLET_DIM = (96, 64, 180)

_SCREEN = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)


def _pixel_line(surface, start, end, color, size, wave=0.0, phase=0.0, wave_length=48.0, dash=0):
    """ A line of size x size squares on the pixel grid, from `start` to `end`.
    :param wave: amplitude of a sideways wave (pixels), :param dash: dash length (0: solid)
    """
    start = Vector2(start)
    delta = Vector2(end) - start
    length = delta.length()
    if length < 1:
        return
    along = delta / length
    side = Vector2(-along.y, along.x)
    step = max(PIXEL, size // 2)
    for s in range(0, int(length), step):
        if dash and (s // dash) % 2:
            continue
        point = start + along * s
        if wave:
            point += side * (wave * math.sin(s / wave_length * math.tau + phase))
        surface.fill(color, (int(point.x) // PIXEL * PIXEL - size // 2,
                             int(point.y) // PIXEL * PIXEL - size // 2, size, size))


def _pixel_ring(surface, center, radius, color, size, dots, turn):
    for k in range(dots):
        angle = k / dots * math.tau + turn
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        surface.fill(color, (int(x) // PIXEL * PIXEL - size // 2, int(y) // PIXEL * PIXEL - size // 2, size, size))


def _distance_to_segment(point, start, end) -> float:
    point, start, end = Vector2(point), Vector2(start), Vector2(end)
    delta = end - start
    if delta.length_squared() == 0:
        return point.distance_to(start)
    t = max(0.0, min(1.0, (point - start).dot(delta) / delta.length_squared()))
    return point.distance_to(start + delta * t)


class GravitonBeam(Sprite):

    AIM, LOCK, FIRE, LIFT = "AIM", "LOCK", "FIRE", "LIFT"

    AIM_FRAMES = 50
    LOCK_FRAMES = 16
    FIRE_FRAMES = 22
    LIFT_FRAMES = 110
    # The plane is caught if its center comes this close to the beam (pixels)
    CATCH_DISTANCE = 26
    # The beam starts this far in front of the Phoenix center
    NOSE = 24
    # While lifted: the plane's own speed is scaled by CONTROL, and it is pulled toward the
    # Phoenix at PULL pixels per frame, but not closer than MIN_DISTANCE
    CONTROL = 0.3
    PULL = 1.8
    MIN_DISTANCE = 230

    def __init__(self, phoenix) -> None:
        super().__init__(G_Beams)
        self.phoenix = phoenix
        self.phase = self.AIM
        self.target = None
        self._count = 0
        self._time = 0
        # Nothing to blit: the beam is drawn by draw()
        self.image = pygame.Surface((0, 0))
        self.rect = pygame.Rect(0, 0, 0, 0)
        play_sound("CARRIER_LASER_START")

    @property
    def locks_aim(self) -> bool:
        """ The Phoenix must not turn: the beam is locked or firing """
        return self.phase in (self.LOCK, self.FIRE)

    # --------------- Geometry --------------- #
    def _direction(self) -> Vector2:
        if self.phase == self.LIFT and self.target is not None:
            to_target = Vector2(self.target.rect.center) - self.phoenix.rect.center
            if to_target.length() > 0:
                return to_target.normalize()
        return Vector2(0, 1).rotate(-self.phoenix.angle)

    def _origin(self) -> Vector2:
        return Vector2(self.phoenix.rect.center) + self._direction() * self.NOSE

    def _end(self) -> Vector2:
        """ Where the line leaves the screen (or the caught plane) """
        if self.phase == self.LIFT and self.target is not None:
            return Vector2(self.target.rect.center)
        origin = self._origin()
        clipped = _SCREEN.clipline(origin, origin + self._direction() * (SCREEN_WIDTH + SCREEN_HEIGHT))
        return Vector2(clipped[1]) if clipped else origin

    def pull(self, pos) -> Vector2:
        """ How much the beam moves a lifted plane at `pos` this frame """
        to_phoenix = Vector2(self.phoenix.rect.center) - Vector2(pos)
        distance = to_phoenix.length()
        if distance <= self.MIN_DISTANCE:
            return Vector2(0, 0)
        return to_phoenix.normalize() * min(self.PULL, distance - self.MIN_DISTANCE)

    # --------------- Phases --------------- #
    def update(self) -> None:
        self._time += 1
        self._count += 1
        phoenix = self.phoenix
        if not phoenix.alive() or not phoenix.is_active or phoenix.shield <= 0:
            self._break()
            return
        if self.phase == self.AIM:
            if self._count >= self.AIM_FRAMES:
                self._set_phase(self.LOCK)
        elif self.phase == self.LOCK:
            if self._count >= self.LOCK_FRAMES:
                self._set_phase(self.FIRE)
                play_sound("PHOENIX_LASER")
        elif self.phase == self.FIRE:
            player = G_Player1.sprite
            if player is not None and _distance_to_segment(
                    player.rect.center, self._origin(), self._end()) <= self.CATCH_DISTANCE and player.lift(self):
                self._catch(player)
            elif self._count >= self.FIRE_FRAMES:
                self.kill()
        elif self._count >= self.LIFT_FRAMES or not self.target.is_active:
            self.kill()

    def _set_phase(self, phase):
        self.phase = phase
        self._count = 0

    def _catch(self, player):
        self.target = player
        self._set_phase(self.LIFT)
        play_sound("SHIELD")
        ScreenShake.add(0.25)
        ScreenFX.hurt(0.5)
        FloatingText((player.rect.centerx, player.rect.top - 10), "GRAVITON BEAM", WARNING_COLOR)

    def _break(self):
        """ The Phoenix lost its shield or was destroyed: the plane is free """
        if self.phase == self.LIFT and self.target is not None and self.target.is_active:
            FloatingText((self.target.rect.centerx, self.target.rect.top - 10), "BEAM BROKEN", WEAPON_COLOR)
        self.kill()

    def kill(self) -> None:
        if self.target is not None:
            self.target.release(self)
            self.target = None
        super().kill()

    # --------------- Drawing --------------- #
    def draw(self, surface) -> None:
        origin, end = self._origin(), self._end()
        t = self._time
        if self.phase == self.AIM:
            progress = self._count / self.AIM_FRAMES
            blink = 8 if progress < 0.6 else 4
            if (self._count // blink) % 2 == 0:
                _pixel_line(surface, origin, end, VIOLET_DIM, PIXEL, dash=8)
            self._draw_charge(surface, origin, 2 + 4 * progress, VIOLET)
        elif self.phase == self.LOCK:
            if (self._count // 3) % 2 == 0:
                _pixel_line(surface, origin, end, VIOLET, PIXEL)
            self._draw_charge(surface, origin, 7, CYAN)
        else:
            # Three strands, the outer ones waving and flowing along the beam
            lifted = self.phase == self.LIFT
            _pixel_line(surface, origin, end, VIOLET, PIXEL * 2, wave=6 if lifted else 8, phase=-t * 0.5)
            _pixel_line(surface, origin, end, CYAN, PIXEL * 2, wave=3 if lifted else 4, phase=math.pi - t * 0.5)
            _pixel_line(surface, origin, end, WHITE, PIXEL)
            self._draw_charge(surface, origin, 6 + (t % 4) // 2, WHITE)
            if lifted:
                # Rings turning around the lifted plane
                center = self.target.rect.center
                radius = 34 + 3 * math.sin(t * 0.3)
                _pixel_ring(surface, center, radius, VIOLET, PIXEL * 2, 14, t * 0.08)
                _pixel_ring(surface, center, radius - 8, CYAN, PIXEL, 10, -t * 0.12)

    @staticmethod
    def _draw_charge(surface, center, radius, color):
        """ Glow at the Phoenix's nose """
        x, y = int(center.x) // PIXEL * PIXEL, int(center.y) // PIXEL * PIXEL
        radius = int(radius) // PIXEL * PIXEL
        pygame.draw.circle(surface, VIOLET_DIM, (x, y), radius + PIXEL)
        pygame.draw.circle(surface, color, (x, y), radius)
        pygame.draw.circle(surface, WHITE, (x, y), max(PIXEL, radius // 2))
