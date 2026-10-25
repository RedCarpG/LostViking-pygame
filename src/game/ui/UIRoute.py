""" The route on the left edge of the screen: from the Terran Starport (bottom) to the Protoss
Stargate (top), a tick where each stage starts, the part already flown lit, the Viking on it.
Pixel art on the 2x grid, drawn once; only the lit part and the marker change.
"""
import pygame

from src.game.animation.pixel_fx import PIXEL, canvas, upscale

TRACK = (44, 52, 92)
TRACK_EDGE = (10, 12, 26)
LIT = (70, 200, 240)
LIT_EDGE = (30, 110, 160)
TICK = (130, 150, 200)
STEEL = (126, 132, 146)
STEEL_DARK = (66, 72, 88)
RED = (184, 0, 0)
COPPER = (223, 118, 53)
COPPER_DARK = (147, 42, 42)
CYAN = (146, 250, 255)
WHITE = (246, 246, 246)
VIKING_RED = (207, 18, 18)


class UIRoute:

    X = 22
    TOP = 160
    BOTTOM = 660
    # Art pixels
    WIDTH = 16
    TRACK_WIDTH = 2
    BLINK = 30

    def __init__(self, surface, level) -> None:
        self.surface = surface
        self.level = level
        self._time = 0
        self._back = self._draw_back()
        self._marker = self._draw_marker()

    @property
    def _length(self):
        return self.BOTTOM - self.TOP

    def _draw_back(self) -> pygame.Surface:
        w, h = self.WIDTH, self._length // PIXEL + 16
        c = canvas(w, h)
        middle = w // 2
        top, bottom = 8, h - 8
        # Track with a dark edge
        c.fill(TRACK_EDGE, (middle - self.TRACK_WIDTH // 2 - 1, top, self.TRACK_WIDTH + 2, bottom - top))
        c.fill(TRACK, (middle - self.TRACK_WIDTH // 2, top, self.TRACK_WIDTH, bottom - top))
        # Ticks where the stages start
        for mark in self.level.route_marks()[1:]:
            y = round(bottom - mark * (bottom - top))
            c.fill(TICK, (middle - 3, y, 6, 1))
        # Terran Starport: a steel block with a red stripe
        c.fill(STEEL_DARK, (middle - 4, bottom - 1, 8, 7))
        c.fill(STEEL, (middle - 3, bottom, 6, 5))
        c.fill(RED, (middle - 3, bottom + 2, 6, 1))
        # Protoss Stargate: a copper diamond around a cyan portal
        for i in range(5):
            c.fill(COPPER_DARK, (middle - i - 1, top - 8 + i, 2 * i + 2, 1))
            c.fill(COPPER_DARK, (middle - i - 1, top + 1 - i, 2 * i + 2, 1))
        for i in range(4):
            c.fill(COPPER, (middle - i, top - 7 + i, 2 * i, 1))
            c.fill(COPPER, (middle - i, top - i, 2 * i, 1))
        c.fill(CYAN, (middle - 1, top - 5, 2, 3))
        return upscale(c)

    @staticmethod
    def _draw_marker() -> pygame.Surface:
        """ The Viking: a small white arrow with red wing tips, pointing up """
        c = canvas(7, 6)
        for row in range(5):
            c.fill(WHITE, (3 - row // 2, row, 1 + (row // 2) * 2, 1))
        c.set_at((0, 4), VIKING_RED)
        c.set_at((6, 4), VIKING_RED)
        c.fill(TRACK_EDGE, (2, 5, 3, 1))
        return upscale(c)

    def update(self) -> None:
        self._time += 1

    def blit(self) -> None:
        back = self._back
        left = self.X - back.get_width() // 2
        top = self.TOP - 8 * PIXEL
        self.surface.blit(back, (left, top))
        progress = self.level.route_progress
        # The part flown, lit
        flown = int(progress * self._length) // PIXEL * PIXEL
        if flown > 0:
            x = self.X - self.TRACK_WIDTH * PIXEL // 2
            self.surface.fill(LIT_EDGE, (x - PIXEL, self.BOTTOM - flown, (self.TRACK_WIDTH + 2) * PIXEL, flown))
            self.surface.fill(LIT, (x, self.BOTTOM - flown, self.TRACK_WIDTH * PIXEL, flown))
        if progress >= 1 and (self._time // self.BLINK) % 2:
            # At the Stargate: the marker blinks
            return
        marker = self._marker
        self.surface.blit(marker, marker.get_rect(center=(self.X, self.BOTTOM - flown)))
