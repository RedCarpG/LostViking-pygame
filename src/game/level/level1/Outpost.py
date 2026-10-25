""" Protoss outposts: floating platforms carrying a Pylon and Photon Cannons

The platform is scenery that drifts down with the stars; the structures on it are enemies.
The plane flies over structures (no collision); bullets, torpedoes and bombs hit them, and
they are armored (the Lanzer Torpedoes hurt them more).
- Photon Cannon: a fixed turret, it charges its orb and fires a photon shot at the plane
- Pylon: powers the cannons of its platform, as in StarCraft. Destroy it and the cannons go
  dark and stop firing (the platform's energy lines go dark too)
Destroying every structure of a platform gives a bonus. The sheets are made by
tools/pixel_art/make_structures.py and drawn at 2x.
"""
import random

from pygame import Vector2
from pygame.sprite import Sprite, Group

from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.game.enemy import EnemyI, EnemyBullet
from src.game.groups import G_Scenery, G_Player1
from src.game.animation import FloatingText, Spark
from src.game.animation.FloatingText import MAX_COLOR, SCORE_COLOR
from src.helper.image import get_image, get_scaled_image
from src.helper.sound import play_sound
from src.util.type import Pos

SCALE = 2
# Pixels per frame the platforms drift down
SCROLL = 1.2

# Sparks of a cannon losing its power
POWER_DOWN_COLORS = ((146, 250, 255), (4, 244, 255), (24, 133, 138))


def _sheet(name):
    return get_scaled_image(f"Structure/{name}.png", SCALE)


# Image files (for the asset manifest)
IMAGES = [f"Structure/{name}.png" for name in (
    "PhotonCannon/CannonIdle", "PhotonCannon/CannonAttack", "PhotonCannon/CannonUnpowered",
    "PhotonCannon/CannonHit", "PhotonCannon/CannonDestroy",
    "Pylon/PylonIdle", "Pylon/PylonHit", "Pylon/PylonDestroy",
    "Outpost/PlatformLarge", "Outpost/PlatformLargeUnpowered",
    "Outpost/PlatformSmallL", "Outpost/PlatformSmallLUnpowered",
    "Outpost/PlatformSmallR", "Outpost/PlatformSmallRUnpowered",
)]


def prepare_images():
    """ Scale the images now (while loading) instead of when the first outpost comes """
    for name in IMAGES:
        _sheet(name[len("Structure/"):-len(".png")])


class Structure(EnemyI):
    """ A structure standing on something that carries it (`anchor`: a platform, the Stargate),
    at `offset` pixels from its top left; it goes away with it
    """

    GROUND = True
    ARMORED = True
    COLLIDE_DAMAGE = 0
    KNOCKBACK = 0
    EXPLOSION = "medium"
    SHAKE_DESTROY = 0.35

    def __init__(self, anchor, offset, frames):
        self.anchor = anchor
        self.offset = offset
        super().__init__(pos=Pos(list(self._anchored_center())), frames=frames, frame_size=None)
        self._speed.update(0, 0)

    def _anchored_center(self):
        return self.anchor.rect.left + self.offset[0], self.anchor.rect.top + self.offset[1]

    def update(self, *args, **kwargs) -> None:
        if not self.anchor.alive():
            self.kill()
            return
        super().update(*args, **kwargs)

    def _move(self) -> None:
        self.set_pos(Pos(list(self._anchored_center())))

    def action(self, *args, **kwargs) -> None:
        pass

    def shoot(self, target):
        pass

    def collide_player(self) -> None:
        pass


class PhotonCannon(Structure):
    MAX_HEALTH = 700
    SCORE = 400
    DROP_SUPPLY_CHANCE = 0.12
    DESTROY_SOUND = "ENEMY_DESTROY"

    # Frames between two shots, the first one comes sooner
    ATTACK_SPEED = 120
    FIRST_SHOT = (30, 100)
    # Fires only from this part of the screen (not from the very top, not next to the plane)
    FIRE_AREA = (20, SCREEN_HEIGHT - 160)

    def __init__(self, anchor, offset):
        super().__init__(anchor, offset, frames={
            "BASE": _sheet("PhotonCannon/CannonIdle"),
            "IDLE": _sheet("PhotonCannon/CannonIdle"),
            "ATTACK": _sheet("PhotonCannon/CannonAttack"),
            "UNPOWERED": _sheet("PhotonCannon/CannonUnpowered"),
            "HIT": _sheet("PhotonCannon/CannonHit"),
            "DESTROY": _sheet("PhotonCannon/CannonDestroy"),
        })
        self.powered = True
        self._count_attack_interval = random.randint(*self.FIRST_SHOT)

    def action(self, *args, **kwargs) -> None:
        if self.powered and self.FIRE_AREA[0] < self.rect.top and self.rect.bottom < self.FIRE_AREA[1]:
            self.attack(None)

    def shoot(self, target):
        player = G_Player1.sprite
        if not self.powered or player is None:
            return
        aim = Vector2(player.rect.center) - Vector2(self.rect.center)
        aim = aim.normalize() if aim.length() > 0 else Vector2(0, 1)
        BulletPhoton(Pos(list(self.rect.center)), aim * BulletPhoton.SPEED)
        play_sound("PHOTON_SHOT")

    def power_off(self) -> None:
        """ Its pylon is gone: the orb goes dark, no more shots """
        if not self.powered or not self.is_active:
            return
        self.powered = False
        self.frames = dict(self.frames, IDLE=self.frames["UNPOWERED"])
        self.set_anime_state("IDLE")
        Spark.shards(self.rect.center, 8, POWER_DOWN_COLORS, speed=(1, 3))
        FloatingText((self.rect.centerx, self.rect.top), "UNPOWERED", MAX_COLOR, duration=60)


class Pylon(Structure):
    MAX_HEALTH = 900
    SCORE = 500
    DROP_SUPPLY_CHANCE = 0.25
    DESTROY_SOUND = "PHOENIX_DESTROY"
    HITSTOP_DESTROY = 2
    SHAKE_DESTROY = 0.5

    def __init__(self, anchor, offset):
        super().__init__(anchor, offset, frames={
            "BASE": _sheet("Pylon/PylonIdle"),
            "IDLE": _sheet("Pylon/PylonIdle"),
            "HIT": _sheet("Pylon/PylonHit"),
            "DESTROY": _sheet("Pylon/PylonDestroy"),
        })
        # The cannons it powers
        self.cannons = []

    def destroy(self, drop_supply=True) -> None:
        if not self.is_active:
            return
        super().destroy(drop_supply)
        play_sound("POWER_DOWN")
        for cannon in self.cannons:
            cannon.power_off()
        if hasattr(self.anchor, "power_off"):
            self.anchor.power_off()


class BulletPhoton(EnemyBullet):
    """ The photon shot of a cannon: an energy orb flying at the plane """

    DAMAGE = 20
    SPEED = 5
    HIT_SPREAD = 4

    def __init__(self, pos: Pos, velocity: Vector2):
        super().__init__(pos, speed=velocity, damage=self.DAMAGE, image=get_image("Enemy/Carrier/OrbCyan.png"))


class OutpostPlatform(Sprite):
    """ The floating platform of an outpost (scenery): it drifts down and carries its structures """

    # name: (sheet, structures: (kind, pad center in art pixels)).
    # Keep the pads in sync with tools/pixel_art/make_structures.py (PLATFORMS)
    LAYOUTS = {
        "large": ("Large", [("cannon", (26, 30)), ("pylon", (75, 30)), ("cannon", (123, 30))]),
        "left": ("SmallL", [("pylon", (22, 26)), ("cannon", (57, 26))]),
        "right": ("SmallR", [("cannon", (22, 26)), ("pylon", (57, 26))]),
    }
    # The pylon floats a little above its pad
    PYLON_RISE = 8
    FRAME_TIME = 5
    # Points for destroying every structure of the platform
    BONUS = 1000

    GROUP = Group()

    def __init__(self, layout, x) -> None:
        """ :param x: where its middle comes in, from above the screen """
        super().__init__(G_Scenery, self.GROUP)
        name, structures = self.LAYOUTS[layout]
        sheet = _sheet(f"Outpost/Platform{name}")
        width = sheet.get_width() // 6
        self._frames = [sheet.subsurface((i * width, 0, width, sheet.get_height())) for i in range(6)]
        self._unpowered = _sheet(f"Outpost/Platform{name}Unpowered")
        self.image = self._frames[0]
        self.rect = self.image.get_rect(midbottom=(x, 0))
        self._y = float(self.rect.top)
        self._time = 0
        self.powered = True
        self._cleared = False

        self.structures = []
        pylon, cannons = None, []
        for kind, (ax, ay) in structures:
            offset = (ax * SCALE + 1, ay * SCALE + 1)
            if kind == "pylon":
                pylon = Pylon(self, (offset[0], offset[1] - self.PYLON_RISE))
                self.structures.append(pylon)
            else:
                cannon = PhotonCannon(self, offset)
                cannons.append(cannon)
                self.structures.append(cannon)
        pylon.cannons = cannons

    @classmethod
    def spawn(cls, layout=None) -> "OutpostPlatform":
        """ An outpost coming in from the top: the large one in the middle part of the screen,
        a small one against its side
        """
        layout = layout or random.choice(list(cls.LAYOUTS))
        width = _sheet(f"Outpost/Platform{cls.LAYOUTS[layout][0]}").get_width() // 6
        if layout == "large":
            x = random.randint(width // 2 + 60, SCREEN_WIDTH - width // 2 - 60)
        elif layout == "left":
            x = width // 2 + random.randint(10, 60)
        else:
            x = SCREEN_WIDTH - width // 2 - random.randint(10, 60)
        return cls(layout, x)

    def power_off(self) -> None:
        self.powered = False
        self.image = self._unpowered

    def update(self) -> None:
        self._time += 1
        self._y += SCROLL
        self.rect.top = round(self._y)
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
            return
        if self.powered:
            self.image = self._frames[(self._time // self.FRAME_TIME) % len(self._frames)]
        if not self._cleared and all(not each.is_active for each in self.structures):
            self._cleared = True
            player = G_Player1.sprite
            if player is not None:
                player.add_score(self.BONUS)
                FloatingText(self.rect.center, f"OUTPOST DOWN +{self.BONUS:,}", SCORE_COLOR, duration=90)
