""" The Protoss Stargate at the end of the route

It drifts in from the top and stays there. Its portal builds the ships of the Protoss fleet:
Scouts warp out of it and dive at the plane, an Oracle warps in, Phoenixes come to defend it,
and the portal releases rings of photon orbs. Two Photon Cannons stand on its wings.
Before it is destroyed it warps out the Carrier: its health gone, the portal surges, the Carrier
warps in over it, then the Stargate blows up. It is a structure: the plane flies over it.
The sheets are made by tools/pixel_art/make_structures.py and drawn at 2x.
"""
import random

from pygame import Vector2

from src.game.enemy import EnemyBoss
from src.game.groups import G_Player1
from src.game.animation import AttachEffect, ScreenShake, ScreenFX, FloatingText
from src.game.animation.FloatingText import WARNING_COLOR
from src.game.animation.ScreenFX import WARP_RING_COLORS
from src.helper.image import get_image, ART_SCALE
from src.helper.sound import play_sound
from src.util.type import Pos
from .Carrier import EnemyCarrier
from .Outpost import PhotonCannon, BulletPhoton
from .Oracle import EnemyOracle
from .Phoenix import EnemyPhoenix
from .Scout import EnemyScout
from .WarpIn import WarpIn

SHEETS = ("Idle", "Attack", "Base", "Hit", "Destroy")
IMAGES = [f"Structure/Stargate/Stargate{name}.png" for name in SHEETS]


def _sheet(name):
    return get_image(f"Structure/Stargate/Stargate{name}.png")


class EnemyStargate(EnemyBoss):
    NAME = "STARGATE"

    MAX_HEALTH = 14000
    SCORE = 10000
    ARMORED = True
    GROUND = True
    COLLIDE_DAMAGE = 0
    # The portal and its arches only: the cannons on the wings must stay in reach of the shots
    HITBOX = (180, 200)

    # Comes in slowly, like the outposts
    MAX_SPEED_Y = 1.2
    ACC_Y = 0.012
    STOP_TOP = 20

    # Middle of the portal and of the cannon pads in the image, in art pixels (see make_structures.py:
    # the rim adds one pixel all around)
    PORTAL = ((77.5 + 1) * ART_SCALE + 1, (50 + 1) * ART_SCALE + 1)
    CANNON_PADS = [((17 + 1) * ART_SCALE + 1, (74 + 1) * ART_SCALE + 1),
                   ((138 + 1) * ART_SCALE + 1, (74 + 1) * ART_SCALE + 1)]

    ATTACK_SPEED = 170
    FIRST_ATTACK_DELAY = 90
    # (attack, weight); the same attack is never used twice in a row
    ATTACKS = [("scouts", 4), ("surge", 3), ("oracle", 1), ("phoenix", 1)]
    MAX_SCOUTS = 8
    SURGE_BULLETS = 18
    SURGE_SPEED = 3.2
    SCOUT_WARP = 30

    # Warp-out of the Carrier: frames of the whole warp, frame its warp-in starts, rings
    WARP_OUT = 210
    CARRIER_WARP_AT = 70
    RING_INTERVAL = 22
    WARP_FLASH = (120, 230, 255)

    def __init__(self):
        super().__init__(
            frames={
                "BASE": _sheet("Base"),
                "IDLE": _sheet("Idle"),
                "ATTACK": _sheet("Attack"),
                "HIT": _sheet("Hit"),
                "DESTROY": _sheet("Destroy"),
            },
            frame_size=None)
        self._speed.y = self.MAX_SPEED_Y
        self._count_attack_interval = self.FIRST_ATTACK_DELAY
        self._last_attack = None
        self.cannons = [PhotonCannon(self, pad) for pad in self.CANNON_PADS]
        self.warping = False
        self._warp_time = 0

    @property
    def portal(self) -> Vector2:
        return Vector2(self.rect.left + self.PORTAL[0], self.rect.top + self.PORTAL[1])

    # --------------- Behavior --------------- #
    def action(self):
        if self.warping:
            self._update_warp_out()
        else:
            super().action()

    def _action_stay(self):
        # A structure: it does not move
        pass

    def attack(self, target):
        if self._count_attack_interval > 0:
            self._count_attack_interval -= 1
        else:
            self.shoot(target)
            self._count_attack_interval = self.ATTACK_SPEED

    def shoot(self, target):
        """ Pick the next attack """
        choices = []
        for name, weight in self.ATTACKS:
            if name == self._last_attack:
                continue
            if name == "scouts" and len(EnemyScout.GROUP) > self.MAX_SCOUTS - 2:
                continue
            if name == "oracle" and (len(EnemyOracle.GROUP) or len(WarpIn.GROUP)):
                continue
            choices.append((name, weight))
        name = random.choices([c[0] for c in choices], weights=[c[1] for c in choices])[0]
        self._last_attack = name
        getattr(self, f"_attack_{name}")()

    def _flare(self, callback):
        """ The portal lights up (a warning), then `callback` """
        def fire():
            if self.is_active and not self.warping:
                callback()
        AttachEffect(self, frames={"IDLE": self.frames["ATTACK"]}, frame_size=None, enable_rotate=False, cb_func=fire)

    def _attack_scouts(self):
        def warp():
            portal = self.portal
            flight = random.choice((EnemyScout.DIVE, EnemyScout.HOVER, EnemyScout.WEAVE))
            height = portal.y + random.uniform(160, 260)
            frame = WarpIn.first_frame(get_image("Enemy/Scout/ScoutNormal.png"))
            for side in (-1, 1):
                pos = (portal.x + side * 46, portal.y + 40)
                WarpIn(pos, lambda pos=pos: EnemyScout(Pos(list(pos)), flight, height=height, phase=0.0),
                       frame, duration=self.SCOUT_WARP, sound=None)
            play_sound("PHOENIX_ARRIVE")
        self._flare(warp)

    def _attack_surge(self):
        def fire():
            portal = self.portal
            offset = random.uniform(0, 360 / self.SURGE_BULLETS)
            for i in range(self.SURGE_BULLETS):
                direction = Vector2(0, 1).rotate(offset + i * 360 / self.SURGE_BULLETS)
                BulletPhoton(Pos([portal.x, portal.y]), direction * self.SURGE_SPEED)
            ScreenFX.ring((round(portal.x), round(portal.y)), 120, duration=24, colors=WARP_RING_COLORS)
            play_sound("PHOENIX_LASER")
        self._flare(fire)

    def _attack_oracle(self):
        portal = self.portal
        self._flare(lambda: EnemyOracle.warp_in((round(portal.x), round(portal.y) + 170)))

    def _attack_phoenix(self):
        EnemyPhoenix.add_enemy_phoenix(side=random.choice(["left", "right"]))

    # --------------- The Carrier warps out --------------- #
    def _damage_hull(self, damage) -> None:
        if self.warping:
            # Nothing hurts it any more while the Carrier comes through (and no flash: the
            # portal surge shows)
            return
        if self._health - damage > 0:
            super()._damage_hull(damage)
            return
        self._health = 0
        self._start_warp_out()

    def _start_warp_out(self):
        self.warping = True
        self._warp_time = 0
        self._speed.update(0, 0)
        player = G_Player1.sprite
        if player is not None:
            player.credit_kill(self)
        # The portal surges until the end
        self.frames = dict(self.frames, IDLE=self.frames["ATTACK"])
        self.set_anime_state("IDLE")
        FloatingText((self.portal.x, self.rect.bottom + 40), "WARP SIGNATURE", WARNING_COLOR, duration=120)
        play_sound("WARP_SURGE")

    def _update_warp_out(self):
        self._warp_time += 1
        portal = (round(self.portal.x), round(self.portal.y))
        if self._warp_time % self.RING_INTERVAL == 1:
            ScreenFX.ring(portal, 300, duration=40, colors=WARP_RING_COLORS)
            ScreenShake.add(0.15)
        if self._warp_time == self.CARRIER_WARP_AT:
            WarpIn(EnemyCarrier.warp_center(), self._release_carrier, EnemyCarrier.warp_frame(),
                   duration=self.WARP_OUT - self.CARRIER_WARP_AT)

    def _release_carrier(self):
        carrier = EnemyCarrier()
        carrier.warp_to(EnemyCarrier.warp_center())
        ScreenFX.flash(self.WARP_FLASH, strength=0.5, duration=40)
        ScreenFX.boss_warning("CARRIER WARPED IN")
        self.warping = False
        self.destroy()

    def destroy(self, drop_supply=True) -> None:
        if not self.is_active:
            return
        for cannon in self.cannons:
            if cannon.is_active:
                cannon.destroy(False)
        super().destroy(drop_supply)

    def final_blast(self):
        play_sound("CARRIER_DESTROY")
        super().final_blast()
