from pygame import Vector2
from src.game.enemy import EnemyII, EnemyBullet
from src.helper.image import get_image
from src.setting import SCREEN_WIDTH
from src.util.type import Pos, Size
from pygame.transform import rotate
from src.game.animation import AttachEffect, Effect
from src.helper.sound import play_sound


class EnemyPhoenix(EnemyII):

    MAX_HEALTH = 400
    SCORE = 2000

    MAX_SHIELD = 600

    def __init__(self, pos, is_left):
        super().__init__(
            pos=pos,
            frames={
                "BASE": get_image("Enemy/Phoenix/PhoenixBase.png"),
                "IDLE": get_image("Enemy/Phoenix/PhoenixNormal.png"),
                "MOVE": get_image("Enemy/Phoenix/PhoenixFast.png"),
                "DESTROY": get_image("Enemy/Phoenix/PhoenixDestroy.png"),
                "HIT": get_image("Enemy/Phoenix/PhoenixHit.png"),
                "ATTACK": get_image("Enemy/Phoenix/PhoenixAttack.png"),

                "SHIELD": get_image("Enemy/Phoenix/PhoenixShield.png")
            },
            frame_size=None,
            is_left=is_left
        )
        self.shield = self.MAX_SHIELD
        play_sound("PHOENIX_ARRIVE")
    # ---------- Override Methods

    def shoot(self, target):
        # --- Correct the release point of the bullet from attack animation
        correction = Vector2(0, 100)
        correction = correction.rotate(-self.angle)
        BulletPhoenix(Pos(correction + self.rect.center), self.angle)
        play_sound("PHOENIX_LASER")

    # Rewrite hit to add Shield
    def hit(self, damage=100, **kwargs):
        if self.is_active:
            if self.shield > 0:
                self.shield -= damage
                AttachEffect(
                    self,
                    frames={
                        "IDLE": self.frames["SHIELD"]
                    },
                    frame_size=None,
                    enable_rotate=False
                )
                play_sound("SHIELD")
            else:
                self._health -= damage
                if self._health > 0:
                    # Get Hit effect
                    AttachEffect(
                        self,
                        frames={
                            "IDLE": self.frames["HIT"]
                        },
                        frame_size=self.frame_size,
                        angle=self.angle
                    )
                else:
                    # HP below 0
                    self.destroy()
            return True
        else:
            return False

    def action(self, *args, **kwargs):
        super().action()
        if self.shield < self.MAX_SHIELD:
            self.shield += 3
        else:
            self.shield = self.MAX_SHIELD

    def destroy(self, drop_supply=True) -> None:
        play_sound("PHOENIX_DESTROY")
        return super().destroy(drop_supply)

    @classmethod
    def add_enemy_phoenix(cls, side=None) -> bool:
        x1 = SCREEN_WIDTH + 100
        x2 = - 100
        y = 200
        if side == "left":
            EnemyPhoenix(Pos([x2, y]), is_left=True)
        elif side == "right":
            EnemyPhoenix(Pos([x1, y]), is_left=False)
        else:
            EnemyPhoenix(Pos([x1, y]), is_left=False)
            EnemyPhoenix(Pos([x2, y]), is_left=True)

        return True


class BulletPhoenix(EnemyBullet):

    DAMAGE = 50
    SPEED = 15

    def __init__(self, pos: Pos, angle):
        super().__init__(
            pos,
            speed=Vector2([0, self.SPEED]),
            damage=self.DAMAGE,
            image=get_image("Enemy/laser.png")
        )
        self._rotate(angle)

    def _rotate(self, angle: int) -> None:
        temp = self.rect.center
        self.image = rotate(self.image, angle)
        self.rect = self.image.get_rect(center=temp)
        self.speed = self.speed.rotate(-angle)

    def hit(self, target=None):
        Effect(
            Pos(self.rect.center).random_offset(5),
            frames={
                "IDLE": get_image("Enemy/LaserHit.png"),
            },
            frame_size=Size([19, 19])
        )
        return super().hit()
