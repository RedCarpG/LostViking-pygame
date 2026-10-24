""" Pixel-art rotation (RotSprite), snapped to a fixed number of directions and cached

RotSprite: scale the sprite up 4x with Scale2x (which keeps pixel-art edges), rotate,
then scale back down. Lines and outlines stay clean, unlike a plain rotation.
It is slow, so only the angles of the first quarter are computed (once per frame
of a sheet); the other directions are exact 90 degree turns of them. The work is
queued while loading and done a little each frame on the main menu.
"""
import time
import pygame

DIRECTIONS = 32
STEP = 360 / DIRECTIONS
_QUARTER = DIRECTIONS // 4

# Scale2x passes: 2 = 4x (looks the same as 8x for these sprites, 4 times faster)
UPSCALE_PASSES = 2

_cache = {}
_jobs = []


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
        frame = sheet.subsurface(rect)
        base = frame if step == 0 else _rotsprite(frame, step * STEP)
        _cache[key] = base
    return pygame.transform.rotate(base, quarter * 90) if quarter else base


def queue(sheet, frame_width) -> None:
    """ Plan the rotations of every frame of a horizontal sheet (done later by work / finish) """
    for x in range(0, sheet.get_width() - frame_width + 1, frame_width):
        rect = pygame.Rect(x, 0, frame_width, sheet.get_height())
        for step in range(1, _QUARTER):
            _jobs.append((sheet, rect, step))


def work(budget_ms) -> None:
    """ Compute queued rotations for at most about `budget_ms` milliseconds """
    end = time.perf_counter() + budget_ms / 1000
    while _jobs and time.perf_counter() < end:
        sheet, rect, step = _jobs.pop()
        rotated_frame(sheet, rect, step * STEP)


def finish() -> None:
    """ Compute every queued rotation now """
    while _jobs:
        sheet, rect, step = _jobs.pop()
        rotated_frame(sheet, rect, step * STEP)


def pending() -> int:
    return len(_jobs)
