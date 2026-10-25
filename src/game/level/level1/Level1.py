import random
import logging
import pygame
from src.setting import MAIN_VOLUME
from src.helper.sound import load_sounds, load_music, play_music
from src.helper.image import load_images, get_image
from src.game.animation.rotsprite import queue as queue_rotations
from src.game.animation import ScreenFX
from src.game.groups import G_BOSS, G_Enemys, G_Enemy_Bullets
from .Scout import EnemyScout
from .Phoenix import EnemyPhoenix
from .Carrier import EnemyCarrier

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
]

MUSIC = ("music/bgm1.ogg", MAIN_VOLUME - 0.4)
BOSS_MUSIC = ("music/bgm2.ogg", MAIN_VOLUME - 0.4)


class Level1:
    SPAWN_SPEED_SCOUT = 100
    SPAWN_SPEED_SCOUT_MAX = 30
    SPAWN_SPEED_SCOUT_INCREASE = 0.01
    SPAWN_SPEED_PHOENIX = 2000
    SPAWN_SPEED_CARRIER = 8200

    # Scout formations (see EnemyScout.spawn_wave): weight at the start of the level and when
    # the boss comes. Formations become more common as the level goes on
    WAVE_WEIGHTS = {
        "single": (6, 3),
        "v": (1, 2),
        "line": (1, 2),
        "column": (0.5, 2),
        "pincer": (0.5, 1.5),
    }
    # After a formation of n Scouts the next one waits (n - 1) * FORMATION_PAUSE spawn intervals,
    # so about as many Scouts come as before
    FORMATION_PAUSE = 0.9

    # When the boss comes the level music fades out, and the boss music starts this many frames later
    MUSIC_FADE_MS = 1200
    BOSS_MUSIC_DELAY = 75
    BOSS_MUSIC_FADE_IN_MS = 1500

    def __init__(self) -> None:
        self.start_time = 0
        load_images(IMAGES)
        # The boss is drawn at 2x: scale its images now, not when it arrives
        EnemyCarrier.prepare_images()

        # Pixel-art rotations of the enemies that turn, prepared before play so turning costs
        # nothing in a round (the Phoenix "Fast" frames only fly at 90 degrees: no rotation needed)
        for name in ["Normal", "Destroy", "Hit", "Attack"]:
            queue_rotations(get_image(f"Enemy/Phoenix/Phoenix{name}.png"), 100)
            queue_rotations(get_image(f"Enemy/Scout/Scout{name}.png"), 53)
        for name in ["Idle", "Move", "Destroy", "Hit", "Attack"]:
            queue_rotations(get_image(f"Enemy/Interceptor/Interceptor{name}.png"), 30)

        load_sounds(SOUNDS)

        self.spawn_speed_scout = self.SPAWN_SPEED_SCOUT
        self.spawn_speed_phoenix = self.SPAWN_SPEED_PHOENIX
        self._count_create_scout = 0
        self._count_create_phoenix = 0
        self._phoenix_created_times = 0
        self._count_create_carrier = 0
        self._carrier_created = False
        self._count_boss_music = 0
        # Spawn enemies over time, can be turned off in test mode
        self.auto_spawn = True

    def start(self):
        self.start_time = pygame.time.get_ticks()

        self.spawn_speed_scout = self.SPAWN_SPEED_SCOUT
        self._count_create_scout = 0
        self._count_create_phoenix = 0
        self._phoenix_created_times = 0
        self._count_create_carrier = 0
        self._carrier_created = False
        self._count_boss_music = 0

        load_music(*MUSIC)
        play_music()

    @property
    def is_completed(self) -> bool:
        """ The level is completed once the Carrier has appeared and been destroyed """
        return self._carrier_created and G_BOSS.sprite is None

    def spawn_carrier(self):
        """ Bring in the boss now (the level then waits for it to be destroyed) """
        if G_BOSS.sprite is None:
            self._count_create_carrier = 0
            self._carrier_created = True
            EnemyCarrier()
            ScreenFX.boss_warning()
            if pygame.mixer.get_init():
                pygame.mixer.music.fadeout(self.MUSIC_FADE_MS)
            self._count_boss_music = self.BOSS_MUSIC_DELAY
            log.debug('Create Carrier')

    def _choose_wave(self) -> str:
        progress = min(1.0, self._count_create_carrier / self.SPAWN_SPEED_CARRIER)
        names = list(self.WAVE_WEIGHTS)
        weights = [start + (end - start) * progress for start, end in self.WAVE_WEIGHTS.values()]
        return random.choices(names, weights=weights)[0]

    def clear_enemies(self):
        """ Remove every enemy and enemy bullet (test mode), a removed boss does not count as a victory """
        for sprite in G_Enemys.sprites() + G_Enemy_Bullets.sprites():
            sprite.kill()
        self._carrier_created = False

    def update(self):
        if self._count_boss_music > 0:
            self._count_boss_music -= 1
            if self._count_boss_music == 0 and not self.is_completed:
                # The level music again if the boss is already gone (removed in test mode)
                load_music(*(BOSS_MUSIC if G_BOSS.sprite is not None else MUSIC))
                play_music(fade_ms=self.BOSS_MUSIC_FADE_IN_MS)

        if self.is_completed or not self.auto_spawn:
            return

        self._count_create_phoenix += 1

        if self.spawn_speed_scout > self.SPAWN_SPEED_SCOUT_MAX:
            self.spawn_speed_scout -= self.SPAWN_SPEED_SCOUT_INCREASE

        if not self._carrier_created:
            self._count_create_scout += 1
            self._count_create_carrier += 1

            if self._count_create_scout > self.spawn_speed_scout:
                self._count_create_scout = 0
                wave = self._choose_wave()
                count = EnemyScout.spawn_wave(wave)
                if count > 1:
                    self._count_create_scout = -self.spawn_speed_scout * (count - 1) * self.FORMATION_PAUSE
                log.debug('Create Scouts: %s (%d)', wave, count)
            if self._count_create_phoenix > self.spawn_speed_phoenix:
                self._phoenix_created_times += 1
                self._count_create_phoenix = 0
                if self._phoenix_created_times >= 3:
                    EnemyPhoenix.add_enemy_phoenix()
                else:
                    EnemyPhoenix.add_enemy_phoenix(
                        side=random.choice(["left", "right"]))
                log.debug('Create Phoenix')
            if self._count_create_carrier > self.SPAWN_SPEED_CARRIER:
                self.spawn_carrier()
        else:
            if self._count_create_phoenix > self.spawn_speed_phoenix * 1.5:
                self._count_create_phoenix = 0
                EnemyPhoenix.add_enemy_phoenix(
                    side=random.choice(["left", "right"]))
                log.debug('Create Phoenix')
