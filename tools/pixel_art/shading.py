""" Shared helpers of the sprite generators (make_oracle.py, make_asteroids.py, make_structures.py)

Parts are masks (sets of (x, y) art pixels) made from polygons, rectangles or ellipses.
`shade` lights a part as a bevel seen from above: each pixel's height grows with its
distance to the edge of the part, the light comes from the upper left, and the result is
cut into the few colors of a ramp with an ordered dither. `outline` and `seam` draw the
dark lines around and between parts.
"""
import os

import pygame

LIGHT = (-0.55, -0.75)
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
_SIDES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def dither(x, y) -> float:
    """ Ordered dither offset at (x, y), in [-0.5, 0.5) """
    return BAYER[y & 3][x & 3] / 16 - 0.5


def mask_of(polygons, size) -> set:
    s = pygame.Surface(size, pygame.SRCALPHA)
    for poly in polygons:
        pygame.draw.polygon(s, (255, 255, 255), poly)
    m = pygame.mask.from_surface(s)
    return {(x, y) for y in range(size[1]) for x in range(size[0]) if m.get_at((x, y))}


def rect_mask(x0, y0, w, h) -> set:
    return {(x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h)}


def ellipse_mask(cx, cy, rx, ry) -> set:
    return {(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0}


def distance(mask) -> dict:
    """ Steps to the outside of the mask (4 neighbours) """
    d = {}
    frontier = [p for p in mask if any((p[0] + dx, p[1] + dy) not in mask for dx, dy in _SIDES)]
    for p in frontier:
        d[p] = 1
    level = 1
    while frontier:
        nxt = []
        for x, y in frontier:
            for dx, dy in _SIDES:
                q = (x + dx, y + dy)
                if q in mask and q not in d:
                    d[q] = level + 1
                    nxt.append(q)
        frontier = nxt
        level += 1
    return d


def shade(canvas, mask, ramp, bevel=3.0, gradient=0.25, bias=0.0, contrast=1.6, dither=0.12):
    """ Paint `mask` with the colors of `ramp` (dark to light) as a bevel lit from the upper left.
    :param gradient: darker toward the bottom of the canvas by this much
    """
    d = distance(mask)
    height = canvas.get_height()

    def h(p):
        return min(d.get(p, 0), bevel) / bevel

    for (x, y) in mask:
        nx = -(h((x + 1, y)) - h((x - 1, y))) / 2
        ny = -(h((x, y + 1)) - h((x, y - 1))) / 2
        light = nx * LIGHT[0] + ny * LIGHT[1]
        value = 0.55 + light * contrast + bias - gradient * (y / height - 0.4)
        value += (BAYER[y & 3][x & 3] / 16 - 0.5) * dither
        index = max(0, min(len(ramp) - 1, int(value * len(ramp))))
        canvas.set_at((x, y), ramp[index])


def outline(canvas, mask, color):
    """ A line of `color` around the mask (8 neighbours) """
    width, height = canvas.get_size()
    for y in range(height):
        for x in range(width):
            if (x, y) in mask:
                continue
            if any((x + dx, y + dy) in mask for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                canvas.set_at((x, y), color)


def seam(canvas, mask_a, mask_b, color):
    """ Dark line where part a touches part b """
    for (x, y) in mask_a:
        if any((x + dx, y + dy) in mask_b for dx, dy in _SIDES):
            canvas.set_at((x, y), color)


def silhouette(surface, color, alpha) -> pygame.Surface:
    mask = pygame.mask.from_surface(surface)
    return mask.to_surface(setcolor=(*color, alpha), unsetcolor=(0, 0, 0, 0))


def darken(surface, index, frames=6) -> pygame.Surface:
    """ Destroy frame `index`: darker every frame, the last two are dark silhouettes """
    levels = (255, 200, 150, 105, 60, 0)
    step = index * 6 // frames
    if step >= 4:
        return silhouette(surface, (12, 8, 16) if step == 5 else (34, 24, 30), 255)
    c = surface.copy()
    v = levels[step]
    c.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
    return c


def save_sheet(frames, path):
    """ Save the frames side by side """
    width = frames[0].get_width()
    sheet = pygame.Surface((width * len(frames), frames[0].get_height()), pygame.SRCALPHA)
    for i, f in enumerate(frames):
        sheet.blit(f, (i * width, 0))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(sheet, path)
    print(f"saved {path} {sheet.get_size()}")
