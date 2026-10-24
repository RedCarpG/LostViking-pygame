import random
import pygame
import logging
import sys
from src.setting import MAIN_VOLUME
from src.helper.sound.sound_loader import load_sound, play_music
from src.helper.image import load_image, get_image, del_image
from src.game.animation.rotsprite import queue as queue_rotations
from src.helper.sound import load_music
from src.game.groups import G_BOSS, G_Enemys, G_Enemy_Bullets
from .Scout import EnemyScout
from .Phoenix import EnemyPhoenix
from .Carrier import EnemyCarrier

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class Level1:
    SPAWN_SPEED_SCOUT = 100
    SPAWN_SPEED_SCOUT_MAX = 30
    SPAWN_SPEED_SCOUT_INCREASE = 0.01
    SPAWN_SPEED_PHOENIX = 2000
    SPAWN_SPEED_CARRIER = 8200

    def __init__(self, enable_event=True) -> None:
        self.start_time = 0
        load_image("Enemy/laser.png")
        load_image("Enemy/Laser2.png")
        load_image("Enemy/LaserHit.png")
        load_image("Enemy/Scout/ScoutBase.png")
        load_image("Enemy/Scout/ScoutNormal.png")
        load_image("Enemy/Scout/ScoutDestroy.png")
        load_image("Enemy/Scout/ScoutHit.png")
        load_image("Enemy/Scout/ScoutAttack.png")
        load_image("Enemy/Phoenix/PhoenixBase.png")
        load_image("Enemy/Phoenix/PhoenixNormal.png")
        load_image("Enemy/Phoenix/PhoenixFast.png")
        load_image("Enemy/Phoenix/PhoenixDestroy.png")
        load_image("Enemy/Phoenix/PhoenixHit.png")
        load_image("Enemy/Phoenix/PhoenixAttack.png")
        load_image("Enemy/Phoenix/PhoenixShield.png")
        load_image("Enemy/Carrier/CarrierBase.png"),
        load_image("Enemy/Carrier/CarrierNormal.png"),
        load_image("Enemy/Carrier/CarrierDestroy.png"),
        load_image("Enemy/Carrier/CarrierHit.png"),
        load_image("Enemy/Carrier/CarrierAttack.png")
        load_image("Enemy/Carrier/OrbCyan.png")
        load_image("Enemy/Carrier/OrbPink.png")
        # The boss is drawn at 2x: scale its images now, not when it arrives
        EnemyCarrier.prepare_images()
        load_image("Enemy/Interceptor/InterceptorBase.png"),
        load_image("Enemy/Interceptor/InterceptorIdle.png"),
        load_image("Enemy/Interceptor/InterceptorMove.png"),
        load_image("Enemy/Interceptor/InterceptorDestroy.png"),
        load_image("Enemy/Interceptor/InterceptorHit.png"),
        load_image("Enemy/Interceptor/InterceptorAttack.png")

        # Pixel-art rotations of the enemies that turn, prepared before play so turning costs
        # nothing in a round (the Phoenix "Fast" frames only fly at 90 degrees: no rotation needed)
        for name in ["Normal", "Destroy", "Hit", "Attack"]:
            queue_rotations(get_image(f"Enemy/Phoenix/Phoenix{name}.png"), 100)
        for name in ["Idle", "Move", "Destroy", "Hit", "Attack"]:
            queue_rotations(get_image(f"Enemy/Interceptor/Interceptor{name}.png"), 30)

        load_sound("Enemy/Shield.ogg", MAIN_VOLUME - 0.4, "SHIELD")
        load_sound("Enemy/Destroy.ogg", MAIN_VOLUME - 0.4, "ENEMY_DESTROY")
        load_sound("Enemy/PhoenixArrive.ogg",
                   MAIN_VOLUME - 0.4, "PHOENIX_ARRIVE")
        load_sound("Enemy/PhoenixLaser.ogg",
                   MAIN_VOLUME - 0.3, "PHOENIX_LASER")
        load_sound("Enemy/PhoenixDestroy.ogg",
                   MAIN_VOLUME - 0.3, "PHOENIX_DESTROY")
        load_sound("Enemy/ScoutDestroy.ogg",
                   MAIN_VOLUME - 0.4, "SCOUT_DESTROY")
        load_sound("Enemy/CarrierDestroy.ogg",
                   MAIN_VOLUME - 0.1, "CARRIER_DESTROY")
        load_sound("Enemy/CarrierLaserStart.ogg",
                   MAIN_VOLUME - 0.4, "CARRIER_LASER_START")
        load_sound("Enemy/CarrierLaser.ogg",
                   MAIN_VOLUME - 0.3, "CARRIER_LASER")
        load_sound("Enemy/CarrierArrive.ogg",
                   MAIN_VOLUME - 0.2, "CARRIER_ARRIVE")
        load_sound("Enemy/InterceptorLaser.ogg",
                   MAIN_VOLUME - 0.4, "INTERCEPTOR_LASER")
        load_sound("Enemy/InterceptorCreate.ogg",
                   MAIN_VOLUME - 0.4, "INTERCEPTOR_CREATE")
        load_sound("Enemy/Hit.ogg",
                   MAIN_VOLUME - 0.4, "ENEMY_HIT")

        self.spwan_speed_scout = self.SPAWN_SPEED_SCOUT
        self.spwan_speed_phoenix = self.SPAWN_SPEED_PHOENIX
        self._count_create_scout = 0
        self._count_create_phoenix = 0
        self._phoenix_created_times = 0
        self._count_create_carrier = 0
        self._carrier_created = False
        # Spawn enemies over time, can be turned off in test mode
        self.auto_spawn = True

    def start(self):
        self.start_time = pygame.time.get_ticks()

        self.spwan_speed_scout = self.SPAWN_SPEED_SCOUT
        self._count_create_scout = 0
        self._count_create_phoenix = 0
        self._phoenix_created_times = 0
        self._count_create_carrier = 0
        self._carrier_created = False

        load_music("music/bgm1.ogg", MAIN_VOLUME - 0.4)
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
            logging.info('Create Carrier')

    def clear_enemies(self):
        """ Remove every enemy and enemy bullet (test mode), a removed boss does not count as a victory """
        for sprite in G_Enemys.sprites() + G_Enemy_Bullets.sprites():
            sprite.kill()
        self._carrier_created = False

    def update(self):
        if self.is_completed or not self.auto_spawn:
            return

        self._count_create_phoenix += 1

        if self.spwan_speed_scout > self.SPAWN_SPEED_SCOUT_MAX:
            self.spwan_speed_scout -= self.SPAWN_SPEED_SCOUT_INCREASE

        if not self._carrier_created:
            self._count_create_scout += 1
            self._count_create_carrier += 1

            if self._count_create_scout > self.spwan_speed_scout:
                self._count_create_scout = 0
                if EnemyScout.add_enemy_scout(1):
                    logging.info('Create Scout')
            if self._count_create_phoenix > self.spwan_speed_phoenix:
                self._phoenix_created_times += 1
                self._count_create_phoenix = 0
                if self._phoenix_created_times >= 3:
                    EnemyPhoenix.add_enemy_phoenix()
                else:
                    EnemyPhoenix.add_enemy_phoenix(
                        side=random.choice(["left", "right"]))
                logging.info('Create Phoenix')
            if self._count_create_carrier > self.SPAWN_SPEED_CARRIER:
                self.spawn_carrier()
        else:
            if self._count_create_phoenix > self.spwan_speed_phoenix * 1.5:
                self._count_create_phoenix = 0
                EnemyPhoenix.add_enemy_phoenix(
                    side=random.choice(["left", "right"]))
                logging.info('Create Phoenix')

    def __del__(self) -> None:
        del_image("Enemy/Scout/ScoutBase.png")
        del_image("Enemy/Scout/ScoutNormal.png")
        del_image("Enemy/Scout/ScoutDestroy.png")
        del_image("Enemy/Scout/ScoutHit.png")
        del_image("Enemy/Scout/ScoutAttack.png")
        del_image("Enemy/Phoenix/PhoenixBase.png")
        del_image("Enemy/Phoenix/PhoenixNormal.png")
        del_image("Enemy/Phoenix/PhoenixFast.png")
        del_image("Enemy/Phoenix/PhoenixDestroy.png")
        del_image("Enemy/Phoenix/PhoenixHit.png")
        del_image("Enemy/Phoenix/PhoenixAttack.png")
        del_image("Enemy/Phoenix/PhoenixShield.png")
        del_image("Enemy/Carrier/CarrierBase.png"),
        del_image("Enemy/Carrier/CarrierNormal.png"),
        del_image("Enemy/Carrier/CarrierDestroy.png"),
        del_image("Enemy/Carrier/CarrierHit.png"),
        del_image("Enemy/Carrier/CarrierAttack.png")
        del_image("Enemy/Interceptor/InterceptorBase.png"),
        del_image("Enemy/Interceptor/InterceptorIdle.png"),
        del_image("Enemy/Interceptor/InterceptorMove.png"),
        del_image("Enemy/Interceptor/InterceptorDestroy.png"),
        del_image("Enemy/Interceptor/InterceptorHit.png"),
        del_image("Enemy/Interceptor/InterceptorAttack.png")
