""" Level 1: the route of the Viking, from a Terran Starport to a Protoss Stargate

The level is a route of stages (STAGES), one after the other:
    launch      the Viking takes off from the Terran Starport
    asteroids   an asteroid field, a few Scouts
    patrol      Protoss fighters: Scout formations, Phoenixes, an Oracle
    outposts    Protoss outposts: Pylons powering Photon Cannons, fighters around them
    stargate    the Stargate (boss): it builds ships, and warps out the Carrier before it falls
    carrier     the Carrier (boss): the level is won once it is destroyed
The route stages last a fixed time, the boss stages until their boss is gone. Each stage shows
its name when it starts (the bosses: a WARNING banner).
"""
import random
import logging
import pygame
from src.setting import MAIN_VOLUME
from src.helper.sound import load_sounds, load_music, play_music
from src.helper.image import load_images, get_image
from src.game.animation import ScreenFX, warmup
from src.game.animation.rotsprite import queue as queue_rotations
from src.game.animation.ScreenFX import prepare_titles
from src.game.groups import G_BOSS, G_Enemys, G_Enemy_Bullets, G_Player1, G_Scenery
from .Scout import EnemyScout
from .Phoenix import EnemyPhoenix
from .Carrier import EnemyCarrier
from .Oracle import EnemyOracle
from .Asteroid import Asteroid, AsteroidSmall
from .Outpost import OutpostPlatform
from .Stargate import EnemyStargate
from .Starport import TerranStarport
from .WarpIn import WarpIn
from . import Oracle, Asteroid as asteroid, Outpost, Stargate, Starport

log = logging.getLogger(__name__)


def _sheets(ship, names):
    """ Image files of a ship's sprite sheets: Enemy/<ship>/<ship><name>.png """
    return [f"Enemy/{ship}/{ship}{name}.png" for name in names]


# Asset manifest of the level
IMAGES = [
    "Enemy/laser.png", "Enemy/Laser2.png", "Enemy/LaserHit.png",
    "Enemy/Carrier/OrbCyan.png", "Enemy/Carrier/OrbPink.png",
    *_sheets("Scout", ("Base", "Normal", "Destroy", "Hit", "Attack")),
    *_sheets("Phoenix", ("Base", "Normal", "Fast", "Destroy", "Hit", "Attack", "Shield")),
    *_sheets("Carrier", ("Base", "Normal", "Destroy", "Hit", "Attack")),
    *_sheets("Interceptor", ("Base", "Idle", "Move", "Destroy", "Hit", "Attack")),
    *_sheets("Oracle", ("Base", "Normal", "Destroy", "Hit", "Attack")),
    *asteroid.images(),
    *Outpost.IMAGES,
    *Stargate.IMAGES,
    Starport.IMAGE,
]

# (file, volume, label)
SOUNDS = [
    ("Enemy/Shield.ogg", MAIN_VOLUME - 0.4, "SHIELD"),
    ("Enemy/Destroy.ogg", MAIN_VOLUME - 0.4, "ENEMY_DESTROY"),
    ("Enemy/PhoenixArrive.ogg", MAIN_VOLUME - 0.4, "PHOENIX_ARRIVE"),
    ("Enemy/PhoenixLaser.ogg", MAIN_VOLUME - 0.3, "PHOENIX_LASER"),
    ("Enemy/PhoenixDestroy.ogg", MAIN_VOLUME - 0.3, "PHOENIX_DESTROY"),
    ("Enemy/ScoutDestroy.ogg", MAIN_VOLUME - 0.4, "SCOUT_DESTROY"),
    ("Enemy/CarrierDestroy.ogg", MAIN_VOLUME - 0.1, "CARRIER_DESTROY"),
    ("Enemy/CarrierLaserStart.ogg", MAIN_VOLUME - 0.4, "CARRIER_LASER_START"),
    ("Enemy/CarrierLaser.ogg", MAIN_VOLUME - 0.3, "CARRIER_LASER"),
    ("Enemy/CarrierArrive.ogg", MAIN_VOLUME - 0.2, "CARRIER_ARRIVE"),
    ("Enemy/InterceptorLaser.ogg", MAIN_VOLUME - 0.4, "INTERCEPTOR_LASER"),
    ("Enemy/InterceptorCreate.ogg", MAIN_VOLUME - 0.4, "INTERCEPTOR_CREATE"),
    ("Enemy/Hit.ogg", MAIN_VOLUME - 0.4, "ENEMY_HIT"),
    # Oracle: the pulsar beam (the Carrier laser sound, quieter), the stasis ward and the stasis
    ("Enemy/CarrierLaser.ogg", MAIN_VOLUME - 0.38, "ORACLE_BEAM"),
    ("Enemy/StasisWard.ogg", MAIN_VOLUME - 0.3, "STASIS_WARD"),
    ("Enemy/Stasis.ogg", MAIN_VOLUME - 0.2, "STASIS"),
    # Outposts: the photon shot (the Interceptor laser, quieter), a pylon going down
    ("Enemy/InterceptorLaser.ogg", MAIN_VOLUME - 0.44, "PHOTON_SHOT"),
    ("Enemy/PowerDown.ogg", MAIN_VOLUME - 0.25, "POWER_DOWN"),
    # The Stargate warping out the Carrier
    ("Enemy/WarpSurge.ogg", MAIN_VOLUME - 0.15, "WARP_SURGE"),
]

MUSIC = ("music/bgm1.ogg", MAIN_VOLUME - 0.4)
BOSS_MUSIC = ("music/bgm2.ogg", MAIN_VOLUME - 0.4)


class Level1:
    # (name, frames (None: until its boss is gone), title, subtitle (None: no title))
    STAGES = [
        ("launch", 300, "LAUNCH", "LEAVING THE TERRAN STARPORT"),
        ("asteroids", 2100, "ASTEROID FIELD", "TORPEDOES CRACK THE BIG ROCKS"),
        ("patrol", 2400, "PROTOSS PATROL", "FIGHTERS INBOUND"),
        ("outposts", 2700, "PROTOSS OUTPOSTS", "DESTROY A PYLON TO CUT ITS CANNONS"),
        ("stargate", None, None, None),
        ("carrier", None, None, None),
    ]
    STAGE_NAMES = [stage[0] for stage in STAGES]

    # Asteroid field: frames between two rocks at the start and at the end of the field,
    # rocks at a time; a lone Scout now and then
    ASTEROID_INTERVAL = (70, 34)
    MAX_ASTEROIDS = 24
    ASTEROID_SCOUT_FIRST = 600
    ASTEROID_SCOUT_INTERVAL = 280

    # Patrol: frames between two Scout waves at the start and at the end of the stage
    SCOUT_INTERVAL = (100, 55)
    # Scout formations (see EnemyScout.spawn_wave): weight at the start and at the end of the patrol
    WAVE_WEIGHTS = {
        "single": (6, 2),
        "v": (1, 2),
        "line": (1, 2),
        "column": (0.5, 2),
        "pincer": (0.5, 1.5),
    }
    # After a formation of n Scouts the next one waits (n - 1) * FORMATION_PAUSE intervals
    FORMATION_PAUSE = 0.9
    PATROL_PHOENIX = (700, 1700)
    PATROL_ORACLE = 1200
    STRAY_ROCK_INTERVAL = 360

    # Outposts: (frame, layouts) of the platforms coming in
    OUTPOSTS = [(30, ("large",)), (650, ("left", "right")), (1300, ("large",)), (1900, ("left",)),
                (2150, ("right",))]
    OUTPOST_SCOUT_INTERVAL = 140
    OUTPOST_PHOENIX = 1100
    OUTPOST_ORACLE = 1750

    # Carrier stage: Phoenixes now and then
    SPAWN_SPEED_PHOENIX = 3000

    # When a boss comes the level music fades out, and the boss music starts this many frames later
    MUSIC_FADE_MS = 1200
    BOSS_MUSIC_DELAY = 75
    BOSS_MUSIC_FADE_IN_MS = 1500

    def __init__(self) -> None:
        load_images(IMAGES)
        EnemyCarrier.prepare()

        # Pixel-art rotations of the enemies that turn, prepared before play so turning costs
        # nothing in a round (the Phoenix "Fast" frames only fly at 90 degrees: no rotation needed).
        # The frame width is the one of the first sheet (6 frames)
        for ship, names in (("Phoenix", ("Normal", "Destroy", "Hit", "Attack")),
                            ("Scout", ("Normal", "Destroy", "Hit", "Attack")),
                            ("Interceptor", ("Idle", "Move", "Destroy", "Hit", "Attack")),
                            ("Oracle", ("Normal", "Destroy", "Hit", "Attack"))):
            width = get_image(f"Enemy/{ship}/{ship}{names[0]}.png").get_width() // 6
            for name in names:
                queue_rotations(get_image(f"Enemy/{ship}/{ship}{name}.png"), width)
        # Pulsar beam, stasis ward and stasis crystal images
        Oracle.prepare()
        # Shapes of the ships that warp in, stage titles
        for sheet in ("Enemy/Oracle/OracleNormal.png", "Enemy/Scout/ScoutNormal.png"):
            warmup.add(lambda sheet=sheet: WarpIn.shape(WarpIn.first_frame(get_image(sheet))))
        warmup.add(lambda: WarpIn.shape(EnemyCarrier.warp_frame()))
        prepare_titles([(title, subtitle) for name, frames, title, subtitle in self.STAGES if title])

        load_sounds(SOUNDS)

        self.stage_index = 0
        self._stage_time = 0
        self._route_time = 0
        self._count_scout = 0
        self._count_rock = 0
        self._count_phoenix = 0
        self._count_boss_music = 0
        self._carrier_created = False
        # Spawn enemies and go along the route, can be turned off in test mode
        self.auto_spawn = True

    def start(self):
        self._count_boss_music = 0
        self._carrier_created = False
        self._route_time = 0
        player = G_Player1.sprite
        if player is not None:
            TerranStarport(player.rect.center)
        self._enter_stage(0)

        load_music(*MUSIC)
        play_music()

    # --------------- Route --------------- #
    @property
    def stage(self) -> str:
        return self.STAGES[self.stage_index][0]

    @classmethod
    def route_frames(cls) -> int:
        """ Frames from the Terran Starport to the Stargate """
        return sum(frames for name, frames, title, subtitle in cls.STAGES if frames)

    @property
    def route_progress(self) -> float:
        """ 0 at the Terran Starport, 1 at the Stargate """
        return min(1.0, self._route_time / self.route_frames())

    @classmethod
    def route_marks(cls) -> list:
        """ Route progress where each stage of the route starts """
        marks, frames = [], 0
        for name, length, title, subtitle in cls.STAGES:
            if length:
                marks.append(frames / cls.route_frames())
                frames += length
        return marks

    def _enter_stage(self, index):
        self.stage_index = index
        self._stage_time = 0
        self._count_scout = 0
        self._count_rock = 0
        self._count_phoenix = 0
        name, frames, title, subtitle = self.STAGES[index]
        if title:
            ScreenFX.stage_title(title, subtitle)
        if name == "stargate":
            EnemyStargate()
            self._boss_arrives("PROTOSS STARGATE AHEAD")
        log.debug("Stage %s", name)

    def go_to(self, name):
        """ Jump to the stage `name` now (test mode, benchmarks); the route time jumps to its start """
        index = self.STAGE_NAMES.index(name)
        self._route_time = sum(frames for stage, frames, title, subtitle in self.STAGES[:index] if frames)
        self._enter_stage(index)

    def next_stage(self):
        if self.stage_index + 1 < len(self.STAGES):
            self.go_to(self.STAGE_NAMES[self.stage_index + 1])

    def _boss_arrives(self, subtitle):
        ScreenFX.boss_warning(subtitle)
        if pygame.mixer.get_init():
            pygame.mixer.music.fadeout(self.MUSIC_FADE_MS)
        self._count_boss_music = self.BOSS_MUSIC_DELAY

    @property
    def is_completed(self) -> bool:
        """ The level is completed once the Carrier has appeared and been destroyed """
        return self._carrier_created and G_BOSS.sprite is None

    def spawn_carrier(self):
        """ Bring in the Carrier now, without the Stargate (test mode); the level then waits for it """
        if G_BOSS.sprite is None:
            self._carrier_created = True
            self.stage_index = self.STAGE_NAMES.index("carrier")
            self._stage_time = 0
            EnemyCarrier()
            self._boss_arrives("CARRIER APPROACHING")
            log.debug('Create Carrier')

    def clear_enemies(self):
        """ Remove every enemy, enemy bullet and outpost (test mode), a removed boss does not count as a victory """
        for sprite in G_Enemys.sprites() + G_Enemy_Bullets.sprites() + G_Scenery.sprites():
            sprite.kill()
        self._carrier_created = False

    # --------------- Frame --------------- #
    def update(self):
        if self._count_boss_music > 0:
            self._count_boss_music -= 1
            if self._count_boss_music == 0 and not self.is_completed:
                # The level music again if the boss is already gone (removed in test mode)
                load_music(*(BOSS_MUSIC if G_BOSS.sprite is not None else MUSIC))
                play_music(fade_ms=self.BOSS_MUSIC_FADE_IN_MS)

        # The Carrier came out of the Stargate (in test mode too: it ends the level)
        if self.stage == "stargate" and isinstance(G_BOSS.sprite, EnemyCarrier):
            self._carrier_created = True
            self._enter_stage(self.STAGE_NAMES.index("carrier"))

        if self.is_completed or not self.auto_spawn:
            return

        name, frames, title, subtitle = self.STAGES[self.stage_index]
        self._stage_time += 1
        if frames:
            self._route_time += 1
        getattr(self, f"_update_{name}")()
        if frames and self._stage_time >= frames:
            self._enter_stage(self.stage_index + 1)

    def _stage_progress(self) -> float:
        return min(1.0, self._stage_time / self.STAGES[self.stage_index][1])

    def _update_launch(self):
        pass

    def _update_asteroids(self):
        start, end = self.ASTEROID_INTERVAL
        interval = start + (end - start) * self._stage_progress()
        self._count_rock += 1
        if self._count_rock >= interval and len(Asteroid.GROUP) < self.MAX_ASTEROIDS:
            self._count_rock = 0
            Asteroid.spawn()
        t = self._stage_time
        if t >= self.ASTEROID_SCOUT_FIRST and t % self.ASTEROID_SCOUT_INTERVAL == 0:
            EnemyScout.spawn_wave("single")

    def _update_patrol(self):
        progress = self._stage_progress()
        start, end = self.SCOUT_INTERVAL
        self._spawn_scouts(start + (end - start) * progress, self._choose_wave(progress))
        t = self._stage_time
        if t in self.PATROL_PHOENIX:
            EnemyPhoenix.add_enemy_phoenix(side=random.choice(["left", "right"]))
        if t == self.PATROL_ORACLE:
            EnemyOracle.warp_in()
        if t % self.STRAY_ROCK_INTERVAL == 0:
            Asteroid.spawn(AsteroidSmall)

    def _update_outposts(self):
        t = self._stage_time
        for frame, layouts in self.OUTPOSTS:
            if t == frame:
                for layout in layouts:
                    OutpostPlatform.spawn(layout)
        self._spawn_scouts(self.OUTPOST_SCOUT_INTERVAL, random.choice(("single", "single", "v", "column")))
        if t == self.OUTPOST_PHOENIX:
            EnemyPhoenix.add_enemy_phoenix(side=random.choice(["left", "right"]))
        if t == self.OUTPOST_ORACLE:
            EnemyOracle.warp_in()

    def _update_stargate(self):
        # The Stargate builds the ships itself (see update for the Carrier coming out of it)
        pass

    def _update_carrier(self):
        self._count_phoenix += 1
        if self._count_phoenix > self.SPAWN_SPEED_PHOENIX:
            self._count_phoenix = 0
            EnemyPhoenix.add_enemy_phoenix(side=random.choice(["left", "right"]))
            log.debug('Create Phoenix')

    def _spawn_scouts(self, interval, wave):
        self._count_scout += 1
        if self._count_scout > interval:
            count = EnemyScout.spawn_wave(wave)
            # After a formation the next one waits longer: about as many Scouts come
            self._count_scout = -interval * (count - 1) * self.FORMATION_PAUSE if count > 1 else 0
            log.debug('Create Scouts: %s (%d)', wave, count)

    def _choose_wave(self, progress) -> str:
        names = list(self.WAVE_WEIGHTS)
        weights = [start + (end - start) * progress for start, end in self.WAVE_WEIGHTS.values()]
        return random.choices(names, weights=weights)[0]
