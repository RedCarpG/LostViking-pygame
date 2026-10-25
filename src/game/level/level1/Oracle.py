""" Oracle: the Protoss harasser of StarCraft II

It warps in, darts around the top of the screen and uses its two abilities:
- Pulsar Beam: it moves above the plane, charges (two dashed lines show where the beam will
  be), then fires a short beam straight down for a while, slowly following the plane
- Stasis Ward: it darts down, drops a faint ward in the plane's way and darts back up. Flying
  into an armed ward freezes the plane in stasis: it can not move or shoot, but nothing can
  hurt it either (as in StarCraft II). Wards can be shot down. The Oracle likes to aim its beam
  where a frozen plane will be when the stasis ends
It is armored, as in StarCraft II: the Lanzer Torpedoes hurt it more.
The ship sheets are made by tools/pixel_art/make_oracle.py; the beam, the ward, the stasis
crystal and the warp-in are drawn here in code as pixel art (see prepare).
"""
import math
import random

import pygame
from pygame import Vector2
from pygame.sprite import Sprite, Group

from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.game.enemy import EnemyI
from src.game.groups import G_Enemy_Bullets, G_Effects, G_Player1
from src.helper.image import get_image
from src.helper.sound import play_sound
from src.game.animation import AttachEffect, Effect, FloatingText, warmup
from src.game.animation.FloatingText import WEAPON_COLOR
from src.game.animation.pixel_fx import PIXEL, canvas, upscale, dither
from src.util.angle import turn_toward
from src.util.type import Pos, Size

# Palette (the Protoss energy of the other ships)
WHITE = (235, 254, 255)
CYAN_LIGHT = (146, 250, 255)
CYAN = (4, 244, 255)
CYAN_DARK = (24, 133, 138)
LAVENDER = (159, 194, 239)
BLUE = (91, 138, 200)
VIOLET = (75, 44, 155)

_images = None


def prepare() -> None:
    """ Make the images ahead of time (see warmup) """
    if _images is None:
        warmup.add(_build())


def images() -> dict:
    if _images is None:
        for _ in _build():
            pass
    return _images


def _build():
    """ Generator: one image set per step (see warmup) """
    global _images
    if _images is not None:
        return
    result = {"empty": canvas(1, 1)}
    result["preview"] = _beam_preview()
    yield
    result["beam"] = {step: [_beam(step, f) for f in range(PulsarBeam.FLOW_FRAMES)]
                      for step in range(1, PulsarBeam.WIDTH_STEPS + 1)}
    yield
    result["ward"] = _ward_sheets()
    yield
    result["shell"] = [_shell(f) for f in range(StasisShell.FRAMES)]
    if _images is None:
        _images = result


# --------------- Drawing --------------- #
BEAM_HALF = 8           # art pixels, from the center to the side of the beam image
BEAM_ART_LENGTH = 150   # art pixels (the beam is PulsarBeam.LENGTH screen pixels long)


def _beam_preview():
    """ Two thin dashed lines along the sides of the hit area """
    c = canvas(BEAM_HALF * 2, BEAM_ART_LENGTH)
    edge = PulsarBeam.HIT_WIDTH // (2 * PIXEL)
    for y in range(BEAM_ART_LENGTH):
        if y % 6 < 4:
            c.set_at((BEAM_HALF - edge - 1, y), LAVENDER)
            c.set_at((BEAM_HALF + edge, y), LAVENDER)
    return upscale(c)


def _beam(step, frame):
    """ The beam at width `step` (1 to WIDTH_STEPS), `frame` makes its energy flow down """
    rng = random.Random(step * 31 + frame)
    c = canvas(BEAM_HALF * 2, BEAM_ART_LENGTH)
    scale = step / PulsarBeam.WIDTH_STEPS
    bands = [(1.5, WHITE), (3.0, CYAN_LIGHT), (5.0, CYAN), (6.5, BLUE)]
    for y in range(BEAM_ART_LENGTH):
        # Wider at the far end: the beam splashes
        splash = max(0.0, (y - (BEAM_ART_LENGTH - 12)) / 12) * 1.5
        wobble = math.sin((y + frame * 3) * 0.7) * 0.6
        streak = (y - frame * 4) % 14 < 2
        for x in range(BEAM_HALF * 2):
            d = abs(x + 0.5 - BEAM_HALF) - wobble * scale + (dither(x, y) - 0.5) * 0.8
            for half, color in bands:
                if d < (half + splash) * scale:
                    if streak and color in (CYAN, BLUE):
                        color = CYAN_LIGHT
                    c.set_at((x, y), color)
                    break
    # Sparks around the splash
    for _ in range(4):
        x = rng.randrange(BEAM_HALF * 2)
        y = BEAM_ART_LENGTH - 1 - rng.randrange(10)
        if c.get_at((x, y)).a == 0:
            c.set_at((x, y), CYAN_LIGHT)
    return upscale(c)


def _ward_sheets():
    """ The ward: a faint Protoss glyph; armed, a dotted ring shows where it catches.
    Sheets of 6 frames: ARMING (dim, no ring), IDLE (armed), HIT, DESTROY
    """
    size = StasisWard.SIZE // PIXEL
    center = (size - 1) / 2
    arming, armed, hit, destroy = [], [], [], []
    for f in range(6):
        pulse = 0.5 + 0.5 * math.sin(f / 6 * math.tau)
        glyph = canvas(size, size)
        mid = round(center)
        # Crystal diamond with a bright core, and four rays
        diamond = [(mid, mid - 6), (mid + 5, mid), (mid, mid + 6), (mid - 5, mid)]
        pygame.draw.polygon(glyph, VIOLET, diamond)
        pygame.draw.polygon(glyph, LAVENDER, diamond, 1)
        pygame.draw.polygon(glyph, BLUE, [(mid, mid - 3), (mid + 2, mid), (mid, mid + 3), (mid - 2, mid)])
        glyph.set_at((mid, mid), WHITE if pulse > 0.5 else CYAN_LIGHT)
        ray = CYAN if pulse > 0.5 else CYAN_DARK
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            pygame.draw.line(glyph, ray, (mid + dx * 8, mid + dy * 8), (mid + dx * 11, mid + dy * 11))
        ring = glyph.copy()
        # Dashed ring where it catches, turning
        radius = size // 2 - 1
        for k in range(120):
            angle = k / 120 * math.tau + f * math.tau / 36
            if (k // 5) % 2 == 0:
                ring.set_at((round(center + math.cos(angle) * radius), round(center + math.sin(angle) * radius)),
                            CYAN if k % 40 < 10 else BLUE)
        dim = glyph.copy()
        dim.fill((255, 255, 255, 110), special_flags=pygame.BLEND_RGBA_MULT)
        # Cloaked: armed wards are see-through too
        ring.fill((255, 255, 255, 190 + int(50 * pulse)), special_flags=pygame.BLEND_RGBA_MULT)
        arming.append(dim)
        armed.append(ring)
        white = pygame.mask.from_surface(glyph).to_surface(setcolor=(255, 255, 255, 220 - f * 35),
                                                            unsetcolor=(0, 0, 0, 0))
        hit.append(white)
        fading = glyph.copy()
        fading.fill((255, 255, 255, max(0, 220 - f * 50)), special_flags=pygame.BLEND_RGBA_MULT)
        destroy.append(fading)

    def sheet(frames):
        s = canvas(size * len(frames), size)
        for i, each in enumerate(frames):
            s.blit(each, (i * size, 0))
        return upscale(s)

    return {"ARMING": sheet(arming), "IDLE": sheet(armed), "HIT": sheet(hit), "DESTROY": sheet(destroy),
            "BASE": sheet(armed)}


def _shell(frame):
    """ Stasis crystal around the plane: a see-through faceted diamond """
    size = StasisShell.SIZE // PIXEL
    c = canvas(size, size)
    m = size // 2
    top, bottom, left, right = (m, 1), (m, size - 2), (2, m), (size - 3, m)
    pygame.draw.polygon(c, (*LAVENDER, 90), [top, right, bottom, left])
    # Facets: lighter on the upper left
    pygame.draw.polygon(c, (*WHITE, 70), [top, (m, m), left])
    pygame.draw.polygon(c, (*BLUE, 70), [bottom, (m, m), right])
    for a, b in ((top, right), (right, bottom), (bottom, left), (left, top), (top, bottom), (left, right)):
        pygame.draw.line(c, (*CYAN_LIGHT, 200), a, b)
    # A glint running along the edge
    t = frame / StasisShell.FRAMES
    gx = round(left[0] + (top[0] - left[0]) * t)
    gy = round(left[1] + (top[1] - left[1]) * t)
    c.fill(WHITE, (gx - 1, gy - 1, 2, 2))
    return upscale(c)


# --------------- Ship --------------- #
class EnemyOracle(EnemyI):

    MAX_HEALTH = 900
    SCORE = 2500
    ARMORED = True
    COLLIDE_DAMAGE = 50
    DROP_SUPPLY_CHANCE = 0.5

    HITBOX = (44, 56)
    EXPLOSION = "medium"
    DESTROY_SOUND = "PHOENIX_DESTROY"
    HITSTOP_DESTROY = 3
    SHAKE_DESTROY = 0.4
    KNOCKBACK = 1

    # Darts at up to MAX_SPEED pixels per frame, speed changes by at most ACCELERATION per frame
    MAX_SPEED = 9
    ACCELERATION = 0.9
    # Frames it waits between two moves
    HOLD = (20, 45)
    # Where it roams and warps in
    AREA = pygame.Rect(90, 90, SCREEN_WIDTH - 180, 300)
    # It leaves after this many frames
    STAY = 1500
    # Banks toward its flight: degrees per pixel per frame of sideways speed, at most BANK_MAX
    BANK = 4
    BANK_MAX = 30
    TURN_RATE = 5

    # Pulsar Beam: frames before the first one and between two
    BEAM_FIRST = 150
    BEAM_COOLDOWN = (300, 420)
    # Pixels per frame it follows the plane while firing (the plane is much faster)
    BEAM_SWEEP = 2.0
    # Stasis Ward: frames before the first one and between two, wards at a time
    WARD_FIRST = 60
    WARD_COOLDOWN = (360, 480)
    MAX_WARDS = 2
    # The ward is dropped this far ahead of the plane, and up to WARD_SIDE pixels to a side
    WARD_AHEAD = (150, 260)
    WARD_SIDE = 140

    HOLDING, MOVING, CHARGING, FIRING, LEAVING = "holding", "moving", "charging", "firing", "leaving"

    GROUP = Group()

    def __init__(self, pos: Pos):
        super().__init__(
            pos=pos,
            frames={
                "BASE": get_image("Enemy/Oracle/OracleBase.png"),
                "IDLE": get_image("Enemy/Oracle/OracleNormal.png"),
                "DESTROY": get_image("Enemy/Oracle/OracleDestroy.png"),
                "HIT": get_image("Enemy/Oracle/OracleHit.png"),
                "ATTACK": get_image("Enemy/Oracle/OracleAttack.png")
            },
            frame_size=None,
            enable_rotate=True)
        self.GROUP.add(self)
        self._speed.update(0, 0)
        self._time = 0
        self._count_beam = self.BEAM_FIRST
        self._count_ward = self.WARD_FIRST
        self._count_hold = 0
        self._target = Vector2(self._pos)
        self._then = None
        self.beam = None
        self._hold()

    @classmethod
    def warp_in(cls, pos=None) -> None:
        """ Bring an Oracle in with a warp-in effect, at `pos` or a random place away from the plane """
        if pos is None:
            player = G_Player1.sprite
            for _ in range(10):
                pos = (random.randint(cls.AREA.left, cls.AREA.right), random.randint(cls.AREA.top, cls.AREA.bottom))
                if player is None or abs(pos[0] - player.rect.centerx) > 200:
                    break
        WarpIn(pos, lambda: cls(Pos(pos)))

    # --------------- Behavior --------------- #
    def action(self, *args, **kwargs) -> None:
        self._time += 1
        if self._count_beam > 0:
            self._count_beam -= 1
        if self._count_ward > 0:
            self._count_ward -= 1
        if self._time > self.STAY and self.state in (self.HOLDING, self.MOVING):
            self.state = self.LEAVING
        getattr(self, f"_{self.state}")()
        if self.state in (self.CHARGING, self.FIRING):
            wanted = 0
        else:
            wanted = max(-self.BANK_MAX, min(self.BANK_MAX, self._speed.x * self.BANK))
        self.angle = turn_toward(self.angle, wanted, self.TURN_RATE)

    def _hold(self):
        self.state = self.HOLDING
        self._count_hold = random.randint(*self.HOLD)

    def _go(self, target, then):
        self.state = self.MOVING
        self._target = Vector2(target)
        self._then = then

    def _holding(self):
        self._speed *= 0.85
        self._count_hold -= 1
        if self._count_hold <= 0:
            self._decide()

    def _decide(self):
        player = G_Player1.sprite
        if player is None or not player.is_active:
            self._roam()
        elif self._count_beam == 0 and (player.in_stasis or self._count_ward > 0 or random.random() < 0.6):
            # Above the plane, the far end of the beam just below it
            x = max(60, min(SCREEN_WIDTH - 60, player.rect.centerx))
            y = max(100, min(560, player.rect.centery - PulsarBeam.LENGTH + 40))
            self._go((x, y), self._start_beam)
        elif self._count_ward == 0 and len(StasisWard.GROUP) < self.MAX_WARDS:
            x = player.rect.centerx + random.uniform(-self.WARD_SIDE, self.WARD_SIDE)
            y = player.rect.centery - random.uniform(*self.WARD_AHEAD)
            self._go((max(80, min(SCREEN_WIDTH - 80, x)), max(140, min(SCREEN_HEIGHT - 220, y))), self._drop_ward)
        else:
            self._roam()

    def _roam(self):
        self._go((random.randint(self.AREA.left, self.AREA.right),
                  random.randint(self.AREA.top, self.AREA.bottom)), self._hold)

    def _moving(self):
        to_target = self._target - self._pos
        distance = to_target.length()
        if distance < 4 and self._speed.length() < 1.5:
            self._speed.update(0, 0)
            self._then()
            return
        # Fast, then brakes on arrival
        wanted = to_target.normalize() * min(self.MAX_SPEED, distance * 0.18) if distance > 0 else Vector2()
        change = wanted - self._speed
        if change.length() > self.ACCELERATION:
            change.scale_to_length(self.ACCELERATION)
        self._speed += change

    def _start_beam(self):
        self.state = self.CHARGING
        self.beam = PulsarBeam(self)
        AttachEffect(self, frames={"IDLE": self.frames["ATTACK"]}, frame_size=None, angle=self.angle)

    def _charging(self):
        self._speed *= 0.8
        if not self.beam.alive():
            self._end_beam()
        elif self.beam.firing:
            self.state = self.FIRING

    def _firing(self):
        if not self.beam.alive():
            self._end_beam()
            return
        player = G_Player1.sprite
        dx = player.rect.centerx - self._pos.x if player is not None else 0
        self._speed.update(max(-self.BEAM_SWEEP, min(self.BEAM_SWEEP, dx * 0.1)), 0)

    def _end_beam(self):
        self.beam = None
        self._count_beam = random.randint(*self.BEAM_COOLDOWN)
        self._hold()

    def _drop_ward(self):
        StasisWard(Pos([self._pos.x, self._pos.y + 30]))
        play_sound("STASIS_WARD")
        self._count_ward = random.randint(*self.WARD_COOLDOWN)
        # Darts back up at once
        self._roam()

    def _leaving(self):
        self._speed.x *= 0.9
        self._speed.y = max(-self.MAX_SPEED, self._speed.y - self.ACCELERATION)
        if self.rect.bottom < -20:
            self.kill()

    def shoot(self, target):
        # No plain gun: see the Pulsar Beam
        pass

    def attack(self, target):
        pass

    def destroy(self, drop_supply=True) -> None:
        if self.beam is not None and self.beam.alive():
            self.beam.kill()
        super().destroy(drop_supply)


# --------------- Pulsar Beam --------------- #
class PulsarBeam(Sprite):
    """ Short beam straight down from the Oracle (an enemy bullet that follows it) """

    CHARGE, OPEN, FIRE, CLOSE = "CHARGE", "OPEN", "FIRE", "CLOSE"

    CHARGE_FRAMES = 36
    FIRE_FRAMES = 90
    # Frames per width step when it opens and closes
    STEP_FRAMES = 2
    WIDTH_STEPS = 3
    FLOW_FRAMES = 4
    # Screen pixels below the Oracle's nose, and width that hurts
    LENGTH = BEAM_ART_LENGTH * PIXEL
    HIT_WIDTH = 20
    DAMAGE = 5
    # The beam starts this far below the Oracle center
    NOSE = 34
    HIT_EFFECT_INTERVAL = 4

    def __init__(self, oracle) -> None:
        super().__init__(G_Enemy_Bullets)
        self._images = images()
        self.oracle = oracle
        self.damage = self.DAMAGE
        self.phase = self.CHARGE
        self._count = 0
        self._time = 0
        self._step = 0
        self._count_hit_effect = 0
        self.image = self._images["empty"]
        self.rect = pygame.Rect(0, 0, BEAM_HALF * 2 * PIXEL, self.LENGTH)
        play_sound("CARRIER_LASER_START")
        self._follow()

    @property
    def firing(self) -> bool:
        return self.phase != self.CHARGE

    @property
    def hitbox(self) -> pygame.Rect:
        """ The middle of the beam, once it is open (see collide_detect) """
        if self.phase not in (self.FIRE, self.OPEN) or self._step < self.WIDTH_STEPS:
            return pygame.Rect(self.rect.centerx, self.rect.top, 0, 0)
        box = pygame.Rect(0, 0, self.HIT_WIDTH, self.LENGTH)
        box.midtop = self.rect.midtop
        return box

    def _follow(self):
        self.rect.midtop = (self.oracle.rect.centerx, self.oracle.rect.centery + self.NOSE)

    def update(self):
        if not self.oracle.alive() or not self.oracle.is_active:
            self.kill()
            return
        self._time += 1
        self._count += 1
        if self.phase == self.CHARGE:
            if self._count >= self.CHARGE_FRAMES:
                self._set_phase(self.OPEN)
                play_sound("ORACLE_BEAM")
        elif self.phase == self.OPEN:
            self._step = min(self.WIDTH_STEPS, 1 + self._count // self.STEP_FRAMES)
            if self._count >= self.WIDTH_STEPS * self.STEP_FRAMES:
                self._set_phase(self.FIRE)
        elif self.phase == self.FIRE:
            if self._count >= self.FIRE_FRAMES:
                self._set_phase(self.CLOSE)
        else:
            self._step = self.WIDTH_STEPS - self._count // self.STEP_FRAMES
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

    def _render(self):
        if self.phase == self.CHARGE:
            # The preview blinks faster as the charge ends
            blink = 6 if self._count < self.CHARGE_FRAMES * 0.6 else 3
            self.image = self._images["preview"] if (self._count // blink) % 2 == 0 else self._images["empty"]
        else:
            self.image = self._images["beam"][max(1, self._step)][(self._time // 2) % self.FLOW_FRAMES]

    def hit(self, target=None):
        # Touches every frame: a spark every few frames is enough
        self._count_hit_effect = (self._count_hit_effect + 1) % self.HIT_EFFECT_INTERVAL
        if target is not None and self._count_hit_effect == 1:
            Effect(
                Pos(target.rect.midtop).random_offset(12),
                frames={
                    "IDLE": get_image("Enemy/LaserHit.png"),
                },
                frame_size=Size([19, 19])
            )


# --------------- Stasis Ward --------------- #
class StasisWard(EnemyI):
    """ Faint trap: flying into it once it is armed freezes the plane in stasis """

    MAX_HEALTH = 160
    SCORE = 200
    # No damage: it freezes the plane instead (see collide_player)
    COLLIDE_DAMAGE = 0
    DROP_SUPPLY_CHANCE = 0
    EXPLOSION = "small"
    SHAKE_DESTROY = 0.1
    KNOCKBACK = 0
    # Image size, and the area that catches the plane
    SIZE = 72
    HITBOX = (64, 64)

    ARM_FRAMES = 45
    LIFETIME = 720
    # Pixels per frame it drifts down
    DRIFT = 0.3
    STASIS_FRAMES = 80

    GROUP = Group()

    def __init__(self, pos: Pos):
        frames = images()["ward"]
        super().__init__(pos=pos, frames=dict(frames), frame_size=Size([self.SIZE, self.SIZE]))
        self.GROUP.add(self)
        self._speed.update(0, self.DRIFT)
        self._count_attack_interval = 10 ** 9
        self._age = 0
        self.set_anime_state("ARMING")

    @property
    def armed(self) -> bool:
        return self._age >= self.ARM_FRAMES

    def action(self, *args, **kwargs) -> None:
        self._age += 1
        if self._age == self.ARM_FRAMES:
            self.set_anime_state("IDLE")
        if self._age >= self.LIFETIME or self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def shoot(self, target):
        pass

    def collide_player(self) -> None:
        player = G_Player1.sprite
        if not self.armed or player is None:
            return
        if player.stasis(self.STASIS_FRAMES):
            StasisShell(player, self.STASIS_FRAMES)
            play_sound("STASIS")
            FloatingText((player.rect.centerx, player.rect.top - 10), "STASIS", WEAPON_COLOR)
        # Used up (no points: the player did not destroy it)
        self.kill()


class StasisShell(Sprite):
    """ The crystal around the frozen plane; it shatters when the stasis ends """

    SIZE = 76
    FRAMES = 6
    FRAME_TIME = 4
    SHARDS = 12

    def __init__(self, player, duration) -> None:
        super().__init__(G_Effects)
        self._frames = images()["shell"]
        self.player = player
        self._duration = duration
        self._age = 0
        self.image = self._frames[0]
        self.rect = self.image.get_rect(center=player.rect.center)

    def update(self) -> None:
        self._age += 1
        if self._age >= self._duration or not self.player.in_stasis:
            for k in range(self.SHARDS):
                CrystalShard(self.rect.center, Vector2(0, 1).rotate(k * 360 / self.SHARDS + random.uniform(-10, 10))
                             * random.uniform(3, 6))
            self.kill()
            return
        self.image = self._frames[(self._age // self.FRAME_TIME) % len(self._frames)]
        self.rect = self.image.get_rect(center=self.player.rect.center)


_shard_images = {}


class CrystalShard(Sprite):
    """ A piece of the shattered stasis crystal """

    LIFE = 16
    COLORS = (WHITE, LAVENDER, BLUE)

    def __init__(self, pos, velocity) -> None:
        super().__init__(G_Effects)
        self._pos = Vector2(pos)
        self._velocity = Vector2(velocity)
        self._age = 0
        self.image = self._image(0)
        self.rect = self.image.get_rect(center=pos)

    @staticmethod
    def _image(index):
        image = _shard_images.get(index)
        if image is None:
            image = canvas(PIXEL * 2, PIXEL * 2)
            image.fill(CrystalShard.COLORS[index])
            _shard_images[index] = image
        return image

    def update(self) -> None:
        self._age += 1
        if self._age >= self.LIFE:
            self.kill()
            return
        self._pos += self._velocity
        self._velocity *= 0.88
        self.image = self._image(min(len(self.COLORS) - 1, self._age * len(self.COLORS) // self.LIFE))
        self.rect.topleft = (int(self._pos.x) // PIXEL * PIXEL, int(self._pos.y) // PIXEL * PIXEL)


# --------------- Warp-in --------------- #
class WarpIn(Sprite):
    """ Protoss warp-in: a ring of light closes in, the ship's shape fills from the top in
    bright cyan, then `spawn` is called and the ship is there
    """

    DURATION = 40
    RING_FRAMES = 18
    SIZE = 140

    GROUP = Group()
    # Cyan silhouette of the Oracle, made once
    _shape = None

    def __init__(self, pos, spawn) -> None:
        super().__init__(G_Effects, self.GROUP)
        if WarpIn._shape is None:
            ship = get_image("Enemy/Oracle/OracleNormal.png").subsurface((0, 0, 64, 88))
            WarpIn._shape = pygame.mask.from_surface(ship).to_surface(setcolor=(*CYAN_LIGHT, 255),
                                                                      unsetcolor=(0, 0, 0, 0))
        self._spawn = spawn
        self._center = (round(pos[0]), round(pos[1]))
        self._age = 0
        self.image = canvas(self.SIZE, self.SIZE)
        self.rect = self.image.get_rect(center=self._center)
        play_sound("PHOENIX_ARRIVE")
        self._render()

    def update(self) -> None:
        self._age += 1
        if self._age >= self.DURATION:
            self._spawn()
            self.kill()
            return
        self._render()

    def _render(self):
        t = self._age / self.DURATION
        c = self.image
        c.fill((0, 0, 0, 0))
        middle = self.SIZE // 2
        if self._age < self.RING_FRAMES:
            r = self._age / self.RING_FRAMES
            radius = int((self.SIZE // 2 - 4) * (1 - r)) // PIXEL * PIXEL + PIXEL * 2
            pygame.draw.circle(c, WHITE if r > 0.6 else CYAN, (middle, middle), radius, PIXEL)
        # The shape fills from the top, the filled part fading toward the end
        shape = self._shape
        reveal = int(shape.get_height() * min(1.0, max(0.0, (t - 0.25) / 0.6)))
        if reveal > 0:
            top_left = (middle - shape.get_width() // 2, middle - shape.get_height() // 2)
            part = shape.subsurface((0, 0, shape.get_width(), reveal)).copy()
            part.set_alpha(int(220 * (1 - max(0.0, t - 0.75) * 3)))
            c.blit(part, top_left)
            c.fill(WHITE, (top_left[0] + 8, top_left[1] + reveal - PIXEL, shape.get_width() - 16, PIXEL))
