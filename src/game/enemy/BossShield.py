""" The energy shield around a boss, drawn in code as pixel art

An ellipse around the ship: a bright rim, a dithered band inside it and a faint mesh. It is
invisible at rest, lights up when it is hit (sparks fly off where the shot struck), glows
faintly while it recharges, and bursts into shards when it breaks. The image is made once per
ship size (see `prepare`).
"""
import math

import pygame
from pygame import Vector2
from pygame.sprite import Sprite

from src.game.groups import G_Effects
from src.game.animation import Spark, ScreenFX, warmup
from src.game.animation.pixel_fx import PIXEL, canvas, upscale, dither

RIM = (210, 246, 255)
LIGHT = (120, 212, 255)
MID = (70, 160, 250)
MESH = (60, 140, 240)
SHARD_COLORS = [(235, 252, 255), RIM, LIGHT, MID, (44, 90, 200)]

# Screen pixels between the hull and the shield
MARGIN = (30, 24)

_images = {}


def _semi_axes(ship_size):
    """ Half width and half height of the ellipse, in screen pixels """
    return ship_size[0] / 2 + MARGIN[0], ship_size[1] / 2 + MARGIN[1]


def prepare(ship_size) -> None:
    """ Make the shield image of a ship of `ship_size` ahead of time (see warmup) """
    if ship_size not in _images:
        warmup.add(_build(ship_size))


def image(ship_size) -> pygame.Surface:
    if ship_size not in _images:
        for _ in _build(ship_size):
            pass
    return _images[ship_size]


def _build(ship_size):
    """ Generator: draws a few rows per step (see warmup) """
    if ship_size in _images:
        return
    a, b = (axis / PIXEL for axis in _semi_axes(ship_size))
    width, height = int(2 * a) + 2, int(2 * b) + 2
    cx, cy = width / 2, height / 2
    c = canvas(width, height)
    for y in range(height):
        ny = (y + 0.5 - cy) / b
        for x in range(width):
            nx = (x + 0.5 - cx) / a
            r = math.sqrt(nx * nx + ny * ny)
            if r > 1:
                continue
            if r >= 0.965:
                c.set_at((x, y), (*RIM, 235))
            elif r >= 0.92:
                c.set_at((x, y), (*LIGHT, 175))
            elif r >= 0.8:
                # Fades into the inside with an ordered dither
                if dither(x, y) < (r - 0.8) / 0.12:
                    c.set_at((x, y), (*MID, 120))
            elif (x + y) % 8 == 0 or (x - y) % 8 == 0:
                # Faint diamond mesh
                c.set_at((x, y), (*MESH, 40))
        if y % 8 == 0:
            yield
    _images[ship_size] = upscale(c)


class BossShield(Sprite):
    """ Follows `ship` (a boss with `shield` and MAX_SHIELD) """

    FADE = 0.9
    RECHARGE_GLOW = 0.3
    # Frames between two impact sparks (continuous fire hits every frame)
    IMPACT_INTERVAL = 4
    BREAK_FADE = 0.8

    def __init__(self, ship) -> None:
        super().__init__(G_Effects)
        self.ship = ship
        self._image = image(tuple(ship.rect.size))
        self.image = self._image
        self.rect = self.image.get_rect(center=ship.rect.center)
        self._glow = 0.0
        self._time = 0
        self._count_impact = 0
        self._broken = False
        self.recharging = False

    @property
    def semi_axes(self):
        return self._image.get_width() / 2, self._image.get_height() / 2

    def edge_point(self, toward) -> Vector2:
        """ The point of the ellipse in the direction of `toward` from the ship center """
        center = Vector2(self.ship.rect.center)
        direction = Vector2(toward) - center
        if direction.length() == 0:
            direction = Vector2(0, 1)
        a, b = self.semi_axes
        scale = 1 / math.sqrt((direction.x / a) ** 2 + (direction.y / b) ** 2)
        return center + direction * scale

    def impact(self, hit_pos=None) -> None:
        """ A shot struck the shield at `hit_pos` (None: below the ship) """
        self._glow = 1.0
        if self._count_impact == 0:
            self._count_impact = self.IMPACT_INTERVAL
            point = self.edge_point(hit_pos if hit_pos is not None else
                                    (self.ship.rect.centerx, self.ship.rect.bottom + 100))
            Spark.shards(point, 5, SHARD_COLORS, speed=(2, 4.5), life=12, size=PIXEL)

    def burst(self) -> None:
        """ The shield breaks: shards all around the ellipse and a ring """
        self._broken = True
        self._glow = 1.0
        a, b = self.semi_axes
        center = Vector2(self.ship.rect.center)
        for k in range(28):
            angle = k / 28 * math.tau
            point = center + Vector2(math.cos(angle) * a, math.sin(angle) * b)
            if 0 <= point.y <= 1000:
                Spark.shards(point, 2, SHARD_COLORS, speed=(2, 6), life=22, size=PIXEL * 2)
        ScreenFX.ring((round(center.x), round(center.y)), int(max(a, b) * 1.3), duration=30,
                      colors=(RIM, LIGHT, MID))

    def restore(self) -> None:
        """ Back online after it broke: a flash, then it recharges """
        self._broken = False
        self._glow = 1.0

    def update(self) -> None:
        ship = self.ship
        if not ship.alive() or not ship.is_active:
            self.kill()
            return
        self._time += 1
        if self._count_impact > 0:
            self._count_impact -= 1
        self._glow *= self.BREAK_FADE if self._broken else self.FADE
        glow = self._glow
        if self.recharging and not self._broken:
            # A slow shimmer while it builds up again
            glow = max(glow, self.RECHARGE_GLOW * (0.7 + 0.3 * math.sin(self._time / 8)))
        self.rect = self._image.get_rect(center=ship.rect.center)
        if glow < 0.02:
            self.image = _empty_image()
            return
        self._image.set_alpha(int(255 * min(1.0, glow)))
        self.image = self._image


_empty = None


def _empty_image() -> pygame.Surface:
    """ Shown while the shield is invisible, made once """
    global _empty
    if _empty is None:
        _empty = pygame.Surface((1, 1), pygame.SRCALPHA)
    return _empty
