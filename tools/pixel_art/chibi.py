""" The chibi pixel-art style of the game, shared by the sprite generators

Sprites are drawn at art size; the game shows them at 2x, like the background. The style:
- round, chunky shapes with few details, big canopies and crystals
- cel shading: each part has a base color, a shadow band toward the lower right, a light band
  toward the upper left and a highlight on its brightest edge (ramps of 4 colors)
- a dark outline around the sprite, then a white rim around everything: the sprites stand out
  of the dark space like stickers
Shapes are given on a design grid and drawn `k` times bigger (Art), so one design can be drawn
at another size (the HUD portrait of the Viking).
"""
import math

import pygame

from shading import mask_of, distance, darken, silhouette, save_sheet

LIGHT = (-0.55, -0.75)
FRAMES = 6

# White rim around every sprite
RIM = (240, 244, 255)

# Ramps: shadow, base, light, highlight
# Terran (the Viking): white hull, red paint, blue glass, steel
WHITE = [(126, 118, 158), (196, 196, 222), (238, 240, 250), (255, 255, 255)]
RED = [(150, 20, 40), (214, 40, 50), (250, 100, 84), (255, 178, 156)]
GLASS = [(26, 54, 120), (52, 124, 214), (124, 206, 255), (236, 252, 255)]
STEEL = [(70, 70, 98), (110, 112, 140), (160, 162, 186), (210, 212, 230)]
YELLOW = [(176, 110, 20), (240, 184, 40), (255, 226, 110), (255, 250, 210)]
FLAME = [(250, 110, 40), (255, 196, 70), (255, 248, 210)]
T_OUTLINE = (34, 16, 40)
# Protoss: copper hulls, violet plates, cyan energy
COPPER = [(160, 54, 40), (218, 110, 44), (248, 172, 92), (255, 232, 196)]
GOLD = [(176, 96, 30), (236, 160, 52), (255, 214, 110), (255, 246, 214)]
VIOLET = [(58, 40, 130), (92, 92, 196), (138, 158, 236), (210, 222, 255)]
CYAN = [(18, 128, 140), (40, 218, 238), (160, 250, 255), (244, 255, 255)]
P_OUTLINE = (52, 18, 26)
# Rocks and other things
ROCK = [(70, 56, 64), (128, 104, 92), (176, 148, 120), (220, 200, 168)]
N_OUTLINE = (36, 26, 34)


class Art:
    """ A canvas with shapes given on a design grid of `w` x `h`, drawn `k` times bigger """

    def __init__(self, w, h, k=1):
        self.k = k
        self.size = (round(w * k), round(h * k))
        self.c = pygame.Surface(self.size, pygame.SRCALPHA)

    def _p(self, v):
        """ Design coordinate -> canvas coordinate (the middle of the design pixel) """
        return v * self.k + (self.k - 1) / 2

    # --------------- Shapes (sets of canvas pixels) --------------- #
    def poly(self, pts):
        return mask_of([[(self._p(x), self._p(y)) for x, y in pts]], self.size)

    def ellipse(self, cx, cy, rx, ry):
        cx, cy, rx, ry = self._p(cx), self._p(cy), rx * self.k, ry * self.k
        w, h = self.size
        return {(x, y) for y in range(max(0, int(cy - ry) - 1), min(h, int(cy + ry) + 2))
                for x in range(max(0, int(cx - rx) - 1), min(w, int(cx + rx) + 2))
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0}

    def rect(self, x, y, w, h):
        k = self.k
        return {(i, j) for i in range(round(x * k), round((x + w) * k)) for j in range(round(y * k), round((y + h) * k))}

    def mirror(self, shape):
        w = self.size[0]
        return {(w - 1 - x, y) for x, y in shape}

    def both(self, shape):
        """ The shape and its mirror image """
        return shape | self.mirror(shape)

    # --------------- Painting --------------- #
    def cel(self, mask, ramp, bevel=3.0, high=0.22, low=-0.3):
        """ Cel shading lit from the upper left; `bevel`: how far in from the edge it curves """
        cel(self.c, mask, ramp, bevel * self.k, high, low, self.k)

    def dome(self, mask, cx, cy, rx, ry, ramp, high=0.62, low=0.3, top=0.88):
        """ Cel shading of a rounded part, lit as the dome over the ellipse (cx, cy, rx, ry):
        big parts get a lit side and a shadow side instead of a flat middle
        """
        lx, ly, lz = LIGHT[0], LIGHT[1], 0.75
        n = math.sqrt(lx * lx + ly * ly + lz * lz)
        lx, ly, lz = lx / n, ly / n, lz / n
        cx, cy, rx, ry = self._p(cx), self._p(cy), rx * self.k, ry * self.k
        for (x, y) in mask:
            dx, dy = (x - cx) / rx, (y - cy) / ry
            dz = math.sqrt(max(0.0, 1 - dx * dx - dy * dy))
            light = dx * lx + dy * ly + dz * lz
            # Ordered dither where two bands meet
            light += ((x * 3 + y * 5) % 4 - 1.5) * 0.015
            if light > top:
                color = ramp[3]
            elif light > high:
                color = ramp[2]
            elif light > low:
                color = ramp[1]
            else:
                color = ramp[0]
            self.c.set_at((x, y), color)

    def fill(self, mask, color):
        for p in mask:
            self.c.set_at(p, color)

    def px(self, x, y, color):
        """ One design pixel """
        k = self.k
        self.c.fill(color, (round(x * k), round(y * k), max(1, round(k)), max(1, round(k))))

    def seam(self, a, b, color):
        """ Dark line on the pixels of `a` that touch `b` """
        for (x, y) in a:
            if any((x + dx, y + dy) in b for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                self.c.set_at((x, y), color)


def cel(c, mask, ramp, bevel=3.0, high=0.22, low=-0.3, k=1):
    """ Cel shading of `mask` on the surface `c`, lit from the upper left: the shadow, base, light and
    highlight colors of `ramp` in bands; `bevel`: how far in from the edge the part curves
    """
    d = distance(mask)

    def h(p):
        return min(d.get(p, 0), bevel) / bevel

    for (x, y) in mask:
        nx = -(h((x + 1, y)) - h((x - 1, y))) / 2 * k
        ny = -(h((x, y + 1)) - h((x, y - 1))) / 2 * k
        light = nx * LIGHT[0] + ny * LIGHT[1]
        if light > high * 1.8 and d[(x, y)] <= k:
            color = ramp[3]
        elif light > high:
            color = ramp[2]
        elif light < low:
            color = ramp[0]
        else:
            color = ramp[1]
        c.set_at((x, y), color)


def ring(c, mask, color):
    """ The pixels around `mask` (8 neighbours), painted `color`; returns them """
    w, h = c.get_size()
    out = set()
    for (x, y) in mask:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q not in mask and 0 <= q[0] < w and 0 <= q[1] < h:
                    out.add(q)
    for p in out:
        c.set_at(p, color)
    return out


def finish(c, mask, outline, extra=frozenset(), rim=RIM):
    """ Dark outline around `mask`, then the white rim around everything (`extra`: parts with no
    dark outline, like flames, that the rim goes around too)
    """
    edge = ring(c, mask, outline)
    if rim is not None:
        ring(c, mask | edge | set(extra), rim)
    return c


def opaque(surface) -> set:
    m = pygame.mask.from_surface(surface)
    w, h = surface.get_size()
    return {(x, y) for y in range(h) for x in range(w) if m.get_at((x, y))}


# --------------- Overlay sheets made from a finished sprite --------------- #
def hit_frames(sprite, alphas=(150, 220, 160, 120, 80, 40)):
    """ Red flash drawn over the sprite when it is hit """
    return [silhouette(sprite, (230, 40, 40), a) for a in alphas]


def blink_frames(sprite, pattern=(1, 1, 0, 1, 1, 0)):
    """ White blinking silhouette (invincible) """
    empty = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
    return [silhouette(sprite, (255, 255, 255), 230) if on else empty for on in pattern]


def destroy_frames(sprite):
    return [darken(sprite, i) for i in range(FRAMES)]


def save(frames, path):
    save_sheet(frames, path)


def flame(c, x, top, length, width, colors, k=1, down=True):
    """ A rounded flame from (x, top), `length` pixels long; returns its pixels """
    out = set()
    for i in range(int(length)):
        y = top + i if down else top - i
        t = i / max(1, length)
        half = width / 2 * (1 - t * 0.7)
        for px in range(int(x - width), int(x + width) + 1):
            dist = abs(px + 0.5 - x)
            if dist <= half + 0.01:
                if t < 0.3 and dist < half * 0.6:
                    color = colors[-1]
                elif t < 0.7:
                    color = colors[-2]
                else:
                    color = colors[0]
                c.set_at((px, y), color)
                out.add((px, y))
    return out


def preview(path, images, scale=4, background=(6, 7, 18)):
    """ The images side by side, `scale` times bigger """
    width = 1600
    x = y = 10
    row = 0
    placed = []
    for image in images:
        w, h = image.get_width() * scale, image.get_height() * scale
        if x + w > width:
            x, y = 10, y + row + 10
            row = 0
        placed.append((image, (x, y)))
        x += w + 10
        row = max(row, h)
    out = pygame.Surface((width, y + row + 10))
    out.fill(background)
    for image, pos in placed:
        out.blit(pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale)), pos)
    pygame.image.save(out, path)


def angle_mask(art, cx, cy, r0, r1, a0, a1):
    """ Ring sector between radius r0 and r1, angles a0 to a1 (degrees, 0: right, clockwise) """
    out = set()
    k = art.k
    cx, cy = art._p(cx), art._p(cy)
    for y in range(art.size[1]):
        for x in range(art.size[0]):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy) / k
            a = math.degrees(math.atan2(dy, dx)) % 360
            if r0 <= r <= r1 and (a0 <= a <= a1 if a0 <= a1 else (a >= a0 or a <= a1)):
                out.add((x, y))
    return out

