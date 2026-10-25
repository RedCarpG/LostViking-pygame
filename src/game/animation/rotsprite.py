""" Pixel-art rotation (RotSprite), snapped to a fixed number of directions and cached

RotSprite: scale the sprite up 4x with Scale2x (which keeps pixel-art edges), rotate,
then scale back down. Lines and outlines stay clean, unlike a plain rotation.
It is slow, so only the angles of the first quarter are computed (once per frame
of a sheet); the other directions are exact 90 degree turns of them. The work is
queued while loading and done a little each frame on the main menu (see warmup).
Sprites shown bigger than their art (see art_source) are turned at art size, then
scaled: their pixels stay on the art grid.
"""
import pygame
from src.helper.image import art_source
from . import warmup

DIRECTIONS = 32
STEP = 360 / DIRECTIONS
_QUARTER = DIRECTIONS // 4

# Scale2x passes: 2 = 4x (looks the same as 8x for these sprites, 4 times faster)
UPSCALE_PASSES = 2

_cache = {}


def direction(angle) -> int:
    """ Index (0 to DIRECTIONS - 1) of the direction nearest to `angle` """
    return round(angle / STEP) % DIRECTIONS


def _rotsprite(image, angle) -> pygame.Surface:
    big = image
    for _ in range(UPSCALE_PASSES):
        big = pygame.transform.scale2x(big)
    rotated = pygame.transform.rotate(big, angle)
    factor = 2 ** UPSCALE_PASSES
    return pygame.transform.scale(rotated, (max(1, rotated.get_width() // factor),
                                            max(1, rotated.get_height() // factor)))


def rotated_frame(sheet, rect, angle) -> pygame.Surface:
    """ The frame `rect` of `sheet`, rotated by `angle` snapped to the nearest direction """
    quarter, step = divmod(direction(angle), _QUARTER)
    key = (id(sheet), tuple(rect), step)
    base = _cache.get(key)
    if base is None:
        source = art_source(sheet)
        if step == 0:
            base = sheet.subsurface(rect)
        elif source is None:
            base = _rotsprite(sheet.subsurface(rect), step * STEP)
        else:
            art, scale = source
            art_rect = pygame.Rect(rect.x // scale, rect.y // scale, rect.width // scale, rect.height // scale)
            turned = _rotsprite(art.subsurface(art_rect), step * STEP)
            base = pygame.transform.scale(turned, (turned.get_width() * scale, turned.get_height() * scale))
        _cache[key] = base
    return pygame.transform.rotate(base, quarter * 90) if quarter else base


def queue(sheet, frame_width) -> None:
    """ Plan the rotations of every frame of a horizontal sheet (done later, see warmup) """
    for x in range(0, sheet.get_width() - frame_width + 1, frame_width):
        rect = pygame.Rect(x, 0, frame_width, sheet.get_height())
        for step in range(1, _QUARTER):
            warmup.add(lambda rect=rect, step=step: rotated_frame(sheet, rect, step * STEP))
