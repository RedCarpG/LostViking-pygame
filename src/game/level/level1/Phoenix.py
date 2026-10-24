import math
import random
import pygame
from pygame import Vector2
from pygame.sprite import Sprite
from src.game.enemy import EnemyII, EnemyBullet, EnemyStatusBar
from src.game.groups import G_Effects
from src.helper.image import get_image
from src.setting import SCREEN_WIDTH
from src.util.type import Pos, Size
from pygame.transform import rotate
from src.game.animation import AnimeSprite, AttachEffect, Effect, ScreenShake
from src.helper.sound import play_sound


class EnemyPhoenix(EnemyII):

    MAX_HEALTH = 600
    SCORE = 2000

    MAX_SHIELD = 600
    # The shield regenerates only after some time without being hit
    SHIELD_REGEN = 4
    SHIELD_REGEN_DELAY = 150
    SHAKE_SHIELD_BREAK = 0.25

    KNOCKBACK = 1

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
        self._count_regen_delay = 0
        self.shield_bubble = PhoenixShieldBubble(self)
        self.status_bar = EnemyStatusBar(self, has_shield=True)
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
            self._count_regen_delay = self.SHIELD_REGEN_DELAY
            self.status_bar.show()
            if self.shield > 0:
                self.shield -= damage
                play_sound("SHIELD")
                if self.shield <= 0:
                    self.shield = 0
                    self._break_shield()
                else:
                    self.shield_bubble.pulse()
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
                    self.hit_feedback()
                else:
                    # HP below 0
                    self.destroy()
            return True
        else:
            return False

    def _break_shield(self):
        ShieldBreakEffect(self.rect.center)
        ScreenShake.add(self.SHAKE_SHIELD_BREAK)
        self.hit_feedback()

    def action(self, *args, **kwargs):
        super().action()
        if self._count_regen_delay > 0:
            self._count_regen_delay -= 1
        elif self.shield < self.MAX_SHIELD:
            if self.shield == 0:
                # Shield back online
                play_sound("SHIELD")
                self.shield_bubble.pulse()
            self.shield = min(self.MAX_SHIELD, self.shield + self.SHIELD_REGEN)

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


class PhoenixShieldBubble(AnimeSprite):
    """ Shield bubble around a Phoenix: it lights up when hit, gets fainter
    as the shield drops and turns red when the shield is about to break
    """

    LOW_SHIELD = 0.35
    FADE = 0.9

    # Red tinted copy of the shield sheet, made once
    _LOW_SHEET = None
    _EMPTY = None

    def __init__(self, phoenix) -> None:
        self._normal_sheet = phoenix.frames["SHIELD"]
        super().__init__(frames={"IDLE": self._normal_sheet}, frame_size=None)
        if PhoenixShieldBubble._LOW_SHEET is None:
            low = self._normal_sheet.copy()
            low.fill((140, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
            low.fill((255, 110, 110), special_flags=pygame.BLEND_RGB_MULT)
            PhoenixShieldBubble._LOW_SHEET = low
            PhoenixShieldBubble._EMPTY = pygame.Surface((1, 1), pygame.SRCALPHA)

        self.phoenix = phoenix
        self._glow = 0.0
        self.rect.center = phoenix.rect.center
        self.image = self._EMPTY
        G_Effects.add(self)

    def pulse(self) -> None:
        self._glow = 1.0

    def update(self) -> None:
        if not self.phoenix.alive() or not self.phoenix.is_active:
            self.kill()
            return
        self.anime()
        self._glow *= self.FADE

        ratio = self.phoenix.shield / self.phoenix.MAX_SHIELD
        alpha = int(255 * self._glow * (0.45 + 0.55 * ratio))
        if alpha < 4:
            self.image = self._EMPTY
            self.rect = self.image.get_rect(center=self.phoenix.rect.center)
            return

        sheet = self._LOW_SHEET if ratio < self.LOW_SHIELD else self._normal_sheet
        self.image = sheet.subsurface(
            self._chop_rect.move(self._current_frame_index * self._img_w, 0)).copy()
        self.image.set_alpha(alpha)
        self.rect = self.image.get_rect(center=self.phoenix.rect.center)


class ShieldBreakEffect(Sprite):
    """ Expanding ring with flying shards, shown when a shield breaks """

    DURATION = 20
    SIZE = 260
    COLOR = (120, 220, 255)

    def __init__(self, center) -> None:
        super().__init__(G_Effects)
        self.image = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        self._count = 0
        self._shards = [(random.uniform(0, math.tau), random.uniform(0.8, 1.25))
                        for _ in range(14)]
        self._render()

    def update(self) -> None:
        self._count += 1
        if self._count >= self.DURATION:
            self.kill()
            return
        self._render()

    def _render(self) -> None:
        t = self._count / self.DURATION
        ease = 1 - (1 - t) ** 3
        alpha = int(255 * (1 - t))
        center = self.SIZE // 2
        radius = 50 + 70 * ease

        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (*self.COLOR, alpha), (center, center),
                           int(radius), max(1, int(5 * (1 - t))))
        for angle, speed in self._shards:
            distance = radius * speed
            x = center + math.cos(angle) * distance
            y = center + math.sin(angle) * distance
            self.image.fill((200, 245, 255, alpha), (int(x) - 2, int(y) - 2, 4, 4))
