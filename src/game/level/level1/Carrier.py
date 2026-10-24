from src.game.animation.AnimeSprite import AnimeSprite
from src.game.enemy import EnemyBoss
from src.game.animation import AttachEffect, Effect
from src.helper.image import get_image
from src.helper.sound import play_sound
from src.util.type import Pos, Size
from .Interceptor import EnemyInterceptor
from src.game.groups import G_Enemy_Bullets


class EnemyCarrier(EnemyBoss):
    MAX_INTERCEPTOR_NUMBER = 9

    ATTACK_SPEED = 700

    def __init__(self):
        EnemyBoss.__init__(
            self,
            frames={
                "BASE": get_image("Enemy/Carrier/CarrierBase.png"),
                "IDLE": get_image("Enemy/Carrier/CarrierNormal.png"),
                "DESTROY": get_image("Enemy/Carrier/CarrierDestroy.png"),
                "HIT": get_image("Enemy/Carrier/CarrierHit.png"),
                "ATTACK_INTERCEPTOR": get_image("Enemy/Carrier/CarrierAttack.png")
            },
            frame_size=None
        )
        play_sound("CARRIER_ARRIVE")
        self._count_attack_interval = 100

    # --------------- Override Methods --------------- #
    def shoot(self, target):

        num_interceptor = len(EnemyInterceptor.GROUP.sprites())
        if num_interceptor > self.MAX_INTERCEPTOR_NUMBER / 2:
            self._shoot_laser()

        else:
            self._shoot_interceptor()

    def _shoot_interceptor(self):
        def _attack_cb():
            if self.is_active and len(EnemyInterceptor.GROUP.sprites()) < self.MAX_INTERCEPTOR_NUMBER:
                pos = self.rect.center
                EnemyInterceptor(Pos(pos),  [[pos[0], pos[1] + 300]])
                # Launch the next one after another attack animation, until the limit is reached
                self._shoot_interceptor()
        AttachEffect(
            self,
            frames={
                "IDLE": self.frames["ATTACK_INTERCEPTOR"]
            },
            frame_size=None,
            enable_rotate=False,
            cb_func=_attack_cb
        )

    def _shoot_laser(self):
        play_sound("CARRIER_LASER_START")

        def _attack_laser():
            LaserCarrier(self)
        AttachEffect(
            self,
            frames={
                "IDLE": get_image("Enemy/Carrier/LaserCarrierStart.png")
            },
            frame_size=Size([133, 696]),
            enable_rotate=False,
            cb_func=_attack_laser,
            offset=[0, (696 + self.rect.height)/2]
        )

    def destroy(self) -> None:
        for each in EnemyInterceptor.GROUP:
            each.destroy(False)
        play_sound("CARRIER_DESTROY")
        return super().destroy()

    def attack(self, target):
        if self._count_attack_interval > 0:
            self._count_attack_interval -= 1
        else:
            self.shoot(target)
            self._count_attack_interval = self.ATTACK_SPEED

    @classmethod
    def add_enemy_carrier(cls):
        EnemyCarrier()


class LaserCarrier(AnimeSprite):
    DURATION = 200
    DAMAGE = 15

    def __init__(self, carrier) -> None:
        play_sound("CARRIER_LASER")
        super().__init__(
            frames={
                "IDLE": get_image("Enemy/Carrier/LaserCarrierIdle.png")
            },
            frame_size=Size([133, 696]))
        self.add(G_Enemy_Bullets)
        self.carrier = carrier
        self.damage = self.DAMAGE
        self.duration = self.DURATION
        self.rect.midtop = self.carrier.rect.midbottom

    def update(self):
        super().update()
        # General update method for bullets
        self.rect.midtop = self.carrier.rect.midbottom
        if self.duration > 0:
            self.duration -= 1
        else:
            AttachEffect(
                self.carrier,
                frames={
                    "IDLE": get_image("Enemy/Carrier/LaserCarrierEnd.png")
                },
                frame_size=Size([133, 696]),
                enable_rotate=False,
                offset=[0, (696 + self.carrier.rect.height)/2]
            )
            self.kill()

    def hit(self, target=None):
        if target is not None:
            Effect(
                Pos(target.rect.midtop).random_offset(15),
                frames={
                    "IDLE": get_image("Enemy/LaserHit.png"),
                },
                frame_size=Size([19, 19])
            )
