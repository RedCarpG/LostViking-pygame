""" The Carrier's laser, drawn in code as pixel art

It has three phases:
- charge: energy gathers at the nose of the ship and a thin blinking line shows
  where the beam will hit (no damage yet)
- fire: the beam opens from a thin line to its full width and its energy flows down
- close: the beam narrows to nothing
The images are made once (see `prepare`). The beam is a short tile repeated down the
screen, shown a few pixels lower every frame so the energy flows, with two edge shapes
swapped to make the edges flicker.
"""
import math
import random

import pygame
from pygame.sprite import Sprite

from src.setting import SCREEN_HEIGHT
from src.helper.sound import play_sound
from src.helper.image import get_image
from src.util.type import Pos, Size
from src.game.groups import G_Enemy_Bullets, G_Effects
from src.game.animation import Effect, warmup
from src.game.animation.pixel_fx import PIXEL, canvas, upscale, dither

# Palette
WHITE = (250, 255, 255)
CYAN_LIGHT = (176, 244, 255)
CYAN = (84, 212, 255)
BLUE = (52, 136, 240)
DEEP_BLUE = (44, 72, 204)
VIOLET = (58, 36, 150)

# Bands of the full beam, from the center: (half width in art pixels, color)
BANDS = [(3.5, WHITE), (6.5, CYAN_LIGHT), (10.5, CYAN), (13.5, BLUE), (16, DEEP_BLUE)]
# Sparse flickering pixels around the beam, up to this distance from the center
GLOW = 19.5
# The beam hurts inside this half width (art pixels): the bright part, without the glow
HITBOX_HALF_WIDTH = 16

HALF_WIDTH = 20         # art pixels, from the center to the side of the image
TILE = 32               # art pixels: the pattern of the beam repeats every TILE rows
WIDTH_STEPS = 6         # widths from a thin line to the full beam
VARIANTS = 2            # edge shapes, swapped to make the edges flicker
LENGTH = SCREEN_HEIGHT  # screen pixels below the nose of the ship
EMITTER_SIZE = 40       # art pixels

CHARGE_FRAMES = 18
FIRE_FRAMES = 4
CLOSE_FRAMES = 6

_images = None


def prepare() -> None:
    """ Make the images ahead of time (see warmup) """
    if _images is None:
        warmup.add(_build())


def images() -> dict:
    global _images
    if _images is None:
        for _ in _build():
            pass
    return _images


def _build():
    """ Generator: makes one image set per step (see warmup) """
    global _images
    if _images is not None:
        return
    rng = random.Random(7)
    streaks = _streaks(rng)
    beams = {}
    for step in range(1, WIDTH_STEPS + 1):
        beams[step] = [_long(_beam_tile(step, variant, streaks, rng)) for variant in range(VARIANTS)]
        yield
    warning = [_long(_warning_tile(color)) for color in (DEEP_BLUE, CYAN)]
    yield
    charge = [upscale(_charge_frame(i / (CHARGE_FRAMES - 1))) for i in range(CHARGE_FRAMES)]
    yield
    fire = [upscale(_fire_frame(i, rng)) for i in range(FIRE_FRAMES)]
    close = [upscale(_close_frame(i / (CLOSE_FRAMES - 1))) for i in range(CLOSE_FRAMES)]
    if _images is None:
        _images = {"beam": beams, "warning": warning, "charge": charge, "fire": fire, "close": close,
                   "empty": canvas(1, 1)}


# --------------- Drawing --------------- #
def _streaks(rng):
    """ Brighter dashes flowing down the beam: (distance from the center, side, top row, length) """
    result = []
    for _ in range(9):
        result.append((rng.uniform(7, 13), rng.choice((-1, 1)), rng.randrange(TILE), rng.randint(4, 10)))
    return result


def _beam_tile(step, variant, streaks, rng) -> pygame.Surface:
    scale = step / WIDTH_STEPS
    tile = canvas(HALF_WIDTH * 2, TILE)
    for y in range(TILE):
        # Wavy edges, two waves per tile so the tile repeats without a seam
        wave = math.sin((y / TILE * 2 + variant * 0.5) * math.tau) * 0.8 * scale
        for x in range(HALF_WIDTH * 2):
            d = abs(x + 0.5 - HALF_WIDTH)
            # Dithered steps between the bands
            dd = d - wave + (dither(x, y) - 0.5) * 0.9
            color = None
            for half_width, band_color in BANDS:
                if dd < half_width * scale:
                    color = band_color
                    break
            if color is None:
                edge = BANDS[-1][0] * scale
                glow = GLOW * scale
                if d < glow and rng.random() < 0.4 * (1 - (d - edge) / max(0.1, glow - edge)):
                    color = VIOLET
            if color is not None:
                tile.set_at((x, y), color)
    # Energy streaks in the cyan and blue bands
    for dist, side, top, length in streaks:
        d = dist * scale
        if d < 2:
            continue
        x = int(HALF_WIDTH + side * d - (1 if side < 0 else 0))
        color = CYAN_LIGHT if dist < 10.5 else CYAN
        for i in range(length):
            tile.set_at((x, (top + i) % TILE), WHITE if i == length - 1 else color)
    return tile


def _warning_tile(color) -> pygame.Surface:
    """ Thin dashed aiming line """
    tile = canvas(HALF_WIDTH * 2, TILE)
    for y in range(TILE):
        if y % 8 < 5:
            tile.fill(color, (HALF_WIDTH - 1, y, 2, 1))
    return tile


def _long(tile) -> pygame.Surface:
    """ The tile, scaled up and repeated down the whole length (plus one tile to scroll) """
    tile = upscale(tile)
    height = tile.get_height()
    surface = canvas(tile.get_width(), LENGTH + height)
    for y in range(0, surface.get_height(), height):
        surface.blit(tile, (0, y))
    return surface


def _orb(surface, center, radius, colors):
    """ Pixel disc with rings: `colors` from the outside to the center """
    count = len(colors)
    for i, color in enumerate(colors):
        r = radius * (count - i) / count
        if r >= 0.5:
            pygame.draw.circle(surface, color, center, round(r))


def _charge_frame(t) -> pygame.Surface:
    """ Energy gathering: a growing orb and particles falling into it """
    c = canvas(EMITTER_SIZE, EMITTER_SIZE)
    center = (EMITTER_SIZE // 2, EMITTER_SIZE // 2)
    # The same particles in every frame
    state = random.Random(11)
    for k in range(12):
        angle = state.uniform(0, math.tau)
        phase = state.random()
        # Each particle falls in, then starts again from the outside
        progress = (t * 3 + phase) % 1
        dist = 18 * (1 - progress) + 2
        for trail in (0, 2):
            r = dist + trail
            x = round(center[0] + math.cos(angle) * r)
            y = round(center[1] + math.sin(angle) * r)
            color = (CYAN_LIGHT if progress > 0.6 else CYAN) if trail == 0 else DEEP_BLUE
            if 0 <= x < EMITTER_SIZE and 0 <= y < EMITTER_SIZE:
                c.set_at((x, y), color)
    radius = 2 + 8 * t
    # Pulses faster as the charge ends
    radius += math.sin(t * math.tau * (2 + 4 * t)) * 0.8
    _orb(c, center, radius + 1.5, [DEEP_BLUE, BLUE, CYAN, CYAN_LIGHT, WHITE])
    return c


def _fire_frame(i, rng) -> pygame.Surface:
    """ Flare at the nose while the beam fires: a bright orb with flickering rays """
    c = canvas(EMITTER_SIZE, EMITTER_SIZE)
    cx = cy = EMITTER_SIZE // 2
    _orb(c, (cx, cy), 12 + (i % 2), [DEEP_BLUE, BLUE, CYAN, CYAN_LIGHT, WHITE, WHITE])
    rays = (18, 15, 19, 16)[i]
    for side in (-1, 1):
        for d in range(8, rays):
            color = WHITE if d < rays * 0.6 else (CYAN_LIGHT if d < rays * 0.8 else CYAN)
            x = cx + side * d - (1 if side < 0 else 0)
            c.set_at((x, cy), color)
            if d < rays * 0.7:
                c.set_at((x, cy - 1), CYAN_LIGHT)
    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        for d in range(7, 10 + (i % 2) * 2):
            c.set_at((cx + dx * d - (dx < 0), cy + dy * d - (dy < 0)), CYAN_LIGHT if d < 9 else CYAN)
    for _ in range(5):
        angle = rng.uniform(0, math.tau)
        r = rng.uniform(13, 18)
        c.set_at((round(cx + math.cos(angle) * r), round(cy + math.sin(angle) * r)), CYAN_LIGHT)
    return c


def _close_frame(t) -> pygame.Surface:
    c = canvas(EMITTER_SIZE, EMITTER_SIZE)
    colors = [DEEP_BLUE, BLUE, CYAN, CYAN_LIGHT, WHITE][:max(2, round(5 * (1 - t)) + 1)]
    _orb(c, (EMITTER_SIZE // 2, EMITTER_SIZE // 2), 12 * (1 - t) + 1, colors)
    return c


# --------------- Sprites --------------- #
class LaserCarrier(Sprite):
    """ The laser beam of the Carrier (an enemy bullet that follows the ship) """

    CHARGE_DURATION = 54
    DURATION = 200
    # Frames per width step when the beam opens and closes
    STEP_FRAMES = 2
    # Screen pixels the energy flows down per frame (a multiple of the pixel size)
    SCROLL = 6
    # Frames between two edge shapes
    FLICKER = 3
    HIT_EFFECT_INTERVAL = 4
    DAMAGE = 8
    # The beam starts under the nose of the ship, this far above its bottom
    NOSE = 12

    CHARGE, OPEN, FIRE, CLOSE = "CHARGE", "OPEN", "FIRE", "CLOSE"

    def __init__(self, carrier) -> None:
        super().__init__(G_Enemy_Bullets)
        self._images = images()
        self.carrier = carrier
        self.damage = self.DAMAGE
        self.phase = self.CHARGE
        self._count = 0
        self._time = 0
        self._step = 0
        self._count_hit_effect = 0
        self.image = self._images["empty"]
        self.rect = pygame.Rect(0, 0, HALF_WIDTH * 2 * PIXEL, LENGTH)
        self.emitter = LaserEmitter(self)
        play_sound("CARRIER_LASER_START")
        self._follow()
        self._render()

    @property
    def firing(self) -> bool:
        return self.phase != self.CHARGE

    @property
    def nose(self):
        return self.carrier.rect.centerx, self.carrier.rect.bottom - self.NOSE

    @property
    def hitbox(self) -> pygame.Rect:
        """ The bright part of the beam, from the nose to the bottom (see collide_detect).
        Empty while charging and while the beam is still thin
        """
        if self._step < WIDTH_STEPS - 1:
            return pygame.Rect(self.rect.centerx, self.rect.top, 0, 0)
        box = pygame.Rect(0, 0, HITBOX_HALF_WIDTH * 2 * PIXEL, self.rect.height)
        box.midtop = self.rect.midtop
        return box

    def kill(self) -> None:
        super().kill()
        self.emitter.kill()

    def update(self):
        self._time += 1
        self._count += 1
        if self.phase == self.CHARGE:
            if self._count >= self.CHARGE_DURATION:
                self._set_phase(self.OPEN)
                play_sound("CARRIER_LASER")
        elif self.phase == self.OPEN:
            self._step = min(WIDTH_STEPS, 1 + self._count // self.STEP_FRAMES)
            if self._count >= WIDTH_STEPS * self.STEP_FRAMES:
                self._set_phase(self.FIRE)
        elif self.phase == self.FIRE:
            if self._count >= self.DURATION:
                self._set_phase(self.CLOSE)
        else:
            self._step = WIDTH_STEPS - self._count // self.STEP_FRAMES
            if self._step <= 0:
                self.kill()
                return
        self._follow()
        self._render()

    def _set_phase(self, phase):
        self.phase = phase
        self._count = 0
        if phase == self.OPEN:
            self._step = 1

    def _follow(self):
        self.rect.midtop = self.nose

    def _render(self):
        tile = TILE * PIXEL
        top = tile - (self._time * self.SCROLL) % tile
        if self.phase == self.CHARGE:
            # Blinks faster and brighter as the charge ends
            progress = self._count / self.CHARGE_DURATION
            blink = 8 if progress < 0.5 else (4 if progress < 0.8 else 2)
            if (self._count // blink) % 2:
                self.image = self._images["empty"]
                return
            sheet = self._images["warning"][0 if progress < 0.5 else 1]
        else:
            variant = (self._time // self.FLICKER) % VARIANTS
            sheet = self._images["beam"][self._step][variant]
        self.image = sheet.subsurface((0, top, sheet.get_width(), LENGTH))

    def hit(self, target=None):
        # The laser touches every frame: a spark every few frames is enough
        self._count_hit_effect = (self._count_hit_effect + 1) % self.HIT_EFFECT_INTERVAL
        if target is not None and self._count_hit_effect == 1:
            Effect(
                Pos(target.rect.midtop).random_offset(15),
                frames={
                    "IDLE": get_image("Enemy/LaserHit.png"),
                },
                frame_size=Size([19, 19])
            )


class LaserEmitter(Sprite):
    """ Glow at the nose of the ship: the charge, then the flare of the beam """

    def __init__(self, laser: LaserCarrier) -> None:
        super().__init__(G_Effects)
        self.laser = laser
        self._images = laser._images
        self.image = self._images["charge"][0]
        self.rect = self.image.get_rect(center=laser.nose)

    def update(self):
        laser = self.laser
        if laser.phase == laser.CHARGE:
            index = min(CHARGE_FRAMES - 1, laser._count * CHARGE_FRAMES // laser.CHARGE_DURATION)
            self.image = self._images["charge"][index]
        elif laser.phase == laser.CLOSE:
            index = min(CLOSE_FRAMES - 1, laser._count * CLOSE_FRAMES // (WIDTH_STEPS * laser.STEP_FRAMES))
            self.image = self._images["close"][index]
        else:
            self.image = self._images["fire"][(laser._time // 2) % FIRE_FRAMES]
        self.rect = self.image.get_rect(center=laser.nose)
