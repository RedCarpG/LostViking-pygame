""" Lanzer Torpedoes: the fighter mode weapon of the StarCraft II Viking

A salvo drops from the wing pods; each torpedo then ignites, turns toward the nearest
enemy (armored ships first, see ARMORED in the enemy classes) and speeds up, leaving a
trail of smoke. Armored ships take extra damage.
The torpedo and the smoke are drawn in code as pixel art; the torpedo is turned with
RotSprite (its rotations are made during the menu warm-up).
"""
import random

from pygame import Rect, Vector2
from pygame.sprite import Sprite, Group

from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.util.type import Pos
from src.game.groups import G_Enemys, G_Effects
from src.game.animation import Explosion
from src.game.animation.pixel_fx import PIXEL, canvas, upscale
from src.game.animation.rotsprite import rotated_frame, queue as queue_rotations
from .PlayerWeapon import PlayerBullet

# Palette
WHITE = (240, 244, 255)
LIGHT = (188, 198, 216)
GREY = (128, 138, 160)
DARK = (68, 76, 100)
BAND = (220, 62, 62)
FIN = (98, 106, 130)
FLAME_HOT = (255, 242, 176)
FLAME = (255, 168, 60)
FLAME_COOL = (222, 84, 34)
# Smoke, from fresh to old (it darkens into the sky instead of fading)
SMOKE = [(196, 196, 212), (156, 156, 178), (118, 118, 144), (86, 86, 114), (60, 60, 88)]

# The torpedo points up: rows of art pixels, "." is empty
BODY = [
    "..W..",
    ".WLW.",
    ".LGL.",
    ".GDG.",
    ".GDG.",
    ".BBB.",
    ".GDG.",
    "FGDGF",
    "F.D.F",
]
FLAMES = [
    [],
    ["..H..", ".FHF.", "..F..", "..C.."],
    ["..H..", "..F..", ".C.C."],
]
COLORS = {"W": WHITE, "L": LIGHT, "G": GREY, "D": DARK, "B": BAND, "F": FIN}
FLAME_COLORS = {"H": FLAME_HOT, "F": FLAME, "C": FLAME_COOL}
ART_W, ART_H = 5, len(BODY) + 4
FRAME_W, FRAME_H = ART_W * PIXEL, ART_H * PIXEL

_sheet = None


def sheet():
    """ 3 frames side by side: unlit, then two flickering flames """
    global _sheet
    if _sheet is None:
        art = canvas(ART_W * len(FLAMES), ART_H)
        for f, flame in enumerate(FLAMES):
            x0 = f * ART_W
            for y, row in enumerate(BODY):
                for x, ch in enumerate(row):
                    if ch in COLORS:
                        art.set_at((x0 + x, y), COLORS[ch])
            for y, row in enumerate(flame):
                for x, ch in enumerate(row):
                    if ch in FLAME_COLORS:
                        art.set_at((x0 + x, len(BODY) + y), FLAME_COLORS[ch])
        _sheet = upscale(art)
    return _sheet


def prepare() -> None:
    """ Make the image and queue its rotations (done while the menu shows, see warmup) """
    queue_rotations(sheet(), FRAME_W)


_smoke_images = {}


def _smoke_image(shade, size):
    key = (shade, size)
    image = _smoke_images.get(key)
    if image is None:
        image = canvas(size, size)
        image.fill(SMOKE[shade])
        _smoke_images[key] = image
    return image


class TorpedoSmoke(Sprite):
    """ A puff of the trail: grows a little and darkens into the sky """

    LIFE = 12
    # At most this many puffs at a time (a full salvo makes a lot of smoke)
    MAX_NUMBER = 120
    GROUP = Group()

    @classmethod
    def puff(cls, pos) -> None:
        if len(cls.GROUP) < cls.MAX_NUMBER:
            cls(pos)

    def __init__(self, pos) -> None:
        super().__init__(G_Effects, self.GROUP)
        self._pos = Vector2(pos) + Vector2(random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5))
        self._drift = Vector2(random.uniform(-0.3, 0.3), random.uniform(0.2, 0.6))
        self._age = 0
        self.image = _smoke_image(0, PIXEL * 2)
        self.rect = self.image.get_rect(center=pos)

    def update(self) -> None:
        self._age += 1
        if self._age >= self.LIFE:
            self.kill()
            return
        self._pos += self._drift
        t = self._age / self.LIFE
        size = PIXEL * (2 if t < 0.3 else 3)
        self.image = _smoke_image(min(len(SMOKE) - 1, int(t * len(SMOKE))), size)
        # Snap to the pixel grid of the art
        self.rect = self.image.get_rect()
        self.rect.topleft = (int(self._pos.x) // PIXEL * PIXEL, int(self._pos.y) // PIXEL * PIXEL)


class LanzerTorpedo(PlayerBullet):

    # Speed while it drops from the pod is lost by this factor per frame
    EJECT_DRAG = 0.86
    # After ignition: speed gain per frame and top speed (pixels per frame)
    ACCELERATION = 0.9
    MAX_SPEED = 13
    # Turn rate (degrees per frame) at ignition; it grows so a torpedo can not circle a target
    TURN_RATE = 4
    TURN_GROWTH = 0.35
    TURN_RATE_MAX = 16
    # Extra damage to armored ships: at level 1 a pair destroys a Scout (500)
    ARMOR_BONUS = 140
    LIFETIME = 110
    SMOKE_INTERVAL = 2
    # Enemies below the torpedo are less likely to be chosen (it would have to turn around)
    BEHIND_PENALTY = 1.6
    ARMORED_PREFERENCE = 0.6

    _SCREEN = Rect(-60, -80, SCREEN_WIDTH + 120, SCREEN_HEIGHT + 140)

    def __init__(self, pos, eject: Vector2, ignite: int, damage: int, player, rank: int = 0):
        """ :param eject: speed when it leaves the pod, :param ignite: frames before ignition,
        :param rank: pair of the salvo: the first pair goes for the best target, the next pairs for
        the next best ones
        """
        self._sheet = sheet()
        image = rotated_frame(self._sheet, Rect(0, 0, FRAME_W, FRAME_H), 0)
        super().__init__(pos=Pos(pos), speed=Vector2(eject), image=image, player=player)
        self.damage = damage
        self._pos = Vector2(pos)
        self._heading = Vector2(0, -1)
        self._ignite_at = ignite
        self._rank = rank
        self._age = 0
        self._target = None

    # --------------- Flight --------------- #
    def update(self):
        self._age += 1
        if self._age > self.LIFETIME or not self._SCREEN.collidepoint(self._pos):
            self.kill()
            return
        if self._age < self._ignite_at:
            self.speed *= self.EJECT_DRAG
            frame = 0
        else:
            self._fly()
            frame = 1 + (self._age // 2) % 2
            if self._age % self.SMOKE_INTERVAL == 0:
                tail = self._pos - self._heading * (FRAME_H // 2)
                TorpedoSmoke.puff(tail)
                # A second puff half a step back: the trail stays unbroken at top speed
                TorpedoSmoke.puff(tail - self.speed * 0.5)
        self._pos += self.speed
        angle = -Vector2(0, -1).angle_to(self._heading)
        self.image = rotated_frame(self._sheet, Rect(frame * FRAME_W, 0, FRAME_W, FRAME_H), angle)
        self.rect = self.image.get_rect(center=(round(self._pos.x), round(self._pos.y)))
        self.collide_enemy(enemy_group=G_Enemys)

    def _fly(self):
        if self._target is None or not self._target.alive() or not self._target.is_active:
            self._target = self._choose_target()
        if self._target is not None:
            # Aim at the part of the ship that is on screen (the boss sticks out of the top)
            x, y = self._target.rect.center
            wanted = Vector2(x, max(y, 20)) - self._pos
            if wanted.length() > 0:
                turn = min(self.TURN_RATE_MAX, self.TURN_RATE + (self._age - self._ignite_at) * self.TURN_GROWTH)
                angle = (self._heading.angle_to(wanted) + 180) % 360 - 180
                self._heading.rotate_ip(max(-turn, min(turn, angle)))
        speed = min(self.MAX_SPEED, self.speed.length() + self.ACCELERATION)
        self.speed = self._heading * speed

    def _choose_target(self):
        candidates = []
        for enemy in G_Enemys:
            if not enemy.is_active or enemy.rect.bottom < 0 or enemy.rect.top > SCREEN_HEIGHT:
                continue
            score = self._pos.distance_to(enemy.rect.center)
            if getattr(enemy, "ARMORED", False):
                score *= self.ARMORED_PREFERENCE
            if enemy.rect.centery > self._pos.y + 60:
                score *= self.BEHIND_PENALTY
            candidates.append((score, id(enemy), enemy))
        if not candidates:
            return None
        candidates.sort()
        return candidates[min(self._rank, len(candidates) - 1)][2]

    # --------------- Hits --------------- #
    def damage_to(self, enemy) -> int:
        return self.damage + (self.ARMOR_BONUS if getattr(enemy, "ARMORED", False) else 0)

    def collide_enemy(self, enemy_group):
        # Still in the pod's drop: it can not hit yet
        if self._age >= self._ignite_at:
            super().collide_enemy(enemy_group)

    def hit(self):
        Explosion(self.rect.center, "small", sparks=False)
        self.kill()

    def hit_shield(self):
        self.hit()
