import math
import random
import pygame
from pygame import Vector2
from pygame.sprite import Sprite
from src.game.enemy import EnemyII, EnemyBullet, EnemyStatusBar
from src.game.groups import G_Effects
from src.helper.image import get_image
from src.setting import SCREEN_WIDTH
from src.util.type import Pos
from src.game.animation import AnimeSprite, ScreenShake
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

    # Body and wing roots, the same at every angle
    HITBOX = (60, 60)
    EXPLOSION = "large"
    DESTROY_SOUND = "PHOENIX_DESTROY"
    HITSTOP_DESTROY = 3

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

    # The shield takes the hits while it lasts
    def hit(self, damage=100, **kwargs) -> bool:
        if not self.is_active:
            return False
        self._count_regen_delay = self.SHIELD_REGEN_DELAY
        self.status_bar.show()
        if self.shield > 0:
            self.shield -= damage
            play_sound("SHIELD")
            if self.shield <= 0:
                self.shield = 0
                self._break_shield()
            else:
                hit_pos = kwargs.get("hit_pos")
                self.shield_bubble.pulse(hit_pos)
                ShieldImpactEffect(self, hit_pos)
        else:
            self._damage_hull(damage)
        return True

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
            image=get_image("Enemy/laser.png"),
            angle=angle
        )


class PhoenixShieldBubble(AnimeSprite):
    """ Shield bubble around a Phoenix. On each hit it flashes, swells and springs back,
    and its edge lights up where the bullet struck. It gets fainter as the shield
    drops and turns red when the shield is about to break.
    """

    LOW_SHIELD = 0.35
    # Distance from the Phoenix center to the bubble edge
    RADIUS = 58

    FADE = 0.92
    FLASH_FRAMES = 3
    POP_SCALE = 0.14
    POP_FADE = 0.7
    IMPACT_FADE = 0.85

    IMPACT_COLOR = (225, 250, 255)
    LOW_IMPACT_COLOR = (255, 170, 160)

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
        self._pop = 0.0
        self._impact = 0.0
        self._impact_angle = None
        self._count_flash = 0
        self.rect.center = phoenix.rect.center
        self.image = self._EMPTY
        G_Effects.add(self)

    def pulse(self, hit_pos=None) -> None:
        """ Light the bubble up, hit_pos is where the bullet struck (None: no impact arc) """
        self._glow = 1.0
        self._pop = 1.0
        self._count_flash = self.FLASH_FRAMES
        if hit_pos is not None:
            dx = hit_pos[0] - self.phoenix.rect.centerx
            dy = hit_pos[1] - self.phoenix.rect.centery
            # pygame.draw.arc angles go counterclockwise with y up
            self._impact_angle = math.atan2(-dy, dx)
            self._impact = 1.0

    def update(self) -> None:
        if not self.phoenix.alive() or not self.phoenix.is_active:
            self.kill()
            return
        self.anime()
        self._glow *= self.FADE
        self._pop *= self.POP_FADE
        self._impact *= self.IMPACT_FADE

        ratio = self.phoenix.shield / self.phoenix.MAX_SHIELD
        alpha = int(255 * self._glow * (0.6 + 0.4 * ratio))
        if alpha < 4:
            self.image = self._EMPTY
            self.rect = self.image.get_rect(center=self.phoenix.rect.center)
            return

        low = ratio < self.LOW_SHIELD
        sheet = self._LOW_SHEET if low else self._normal_sheet
        frame = sheet.subsurface(
            self._chop_rect.move(self._current_frame_index * self._img_w, 0)).copy()

        if self._count_flash > 0:
            # Bright flash right after the hit
            self._count_flash -= 1
            frame.fill((160, 160, 160), special_flags=pygame.BLEND_RGB_ADD)

        if self._impact > 0.05 and self._impact_angle is not None:
            # Light the edge up where the bullet struck
            color = self.LOW_IMPACT_COLOR if low else self.IMPACT_COLOR
            edge = frame.get_rect().inflate(-6, -6)
            for width, spread, strength in [(4, 0.9, 0.55), (9, 0.45, 1.0)]:
                pygame.draw.arc(frame, (*color, int(255 * self._impact * strength)), edge,
                                self._impact_angle - spread, self._impact_angle + spread, width)

        scale = 1 + self.POP_SCALE * self._pop
        if scale > 1.005:
            # Swell on the hit and spring back (pixel scaling, sizes kept even)
            frame = pygame.transform.scale(
                frame, (int(frame.get_width() * scale) // 2 * 2, int(frame.get_height() * scale) // 2 * 2))

        frame.set_alpha(alpha)
        self.image = frame
        self.rect = self.image.get_rect(center=self.phoenix.rect.center)


class ShieldImpactEffect(Sprite):
    """ Where a bullet hits a shield: a flash, a small ring and sparks
    bouncing off the shield, so the bullet looks deflected
    """

    DURATION = 12
    SIZE = 130
    COLOR = (150, 230, 255)
    SPARK_COLOR = (235, 252, 255)
    SPARKS = 12

    # Soft glow image, made once
    _GLOW = None

    def __init__(self, phoenix, hit_pos=None) -> None:
        super().__init__(G_Effects)
        if ShieldImpactEffect._GLOW is None:
            # Glow in three hard steps (pixel style, no smooth gradient)
            glow = pygame.Surface((76, 76), pygame.SRCALPHA)
            for radius, alpha in ((38, 60), (26, 130), (14, 230)):
                pygame.draw.circle(glow, (*self.COLOR, alpha), (38, 38), radius)
            ShieldImpactEffect._GLOW = glow

        center = Vector2(phoenix.rect.center)
        direction = Vector2(hit_pos) - center if hit_pos is not None else Vector2(random.uniform(-1, 1), 1)
        if direction.length() == 0:
            direction = Vector2(0, 1)
        direction = direction.normalize()

        self.image = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center + direction * PhoenixShieldBubble.RADIUS)
        # Sparks fly outwards from the shield surface
        self._sparks = [[Vector2(0, 0), direction.rotate(random.uniform(-70, 70)) * random.uniform(4, 8.5)]
                        for _ in range(self.SPARKS)]
        self._count = 0
        self._render()

    def update(self) -> None:
        self._count += 1
        if self._count >= self.DURATION:
            self.kill()
            return
        for spark in self._sparks:
            spark[0] += spark[1]
            spark[1] *= 0.88
        self._render()

    def _render(self) -> None:
        t = self._count / self.DURATION
        alpha = int(255 * (1 - t))
        center = Vector2(self.SIZE // 2, self.SIZE // 2)
        self.image.fill((0, 0, 0, 0))

        self._GLOW.set_alpha(int(255 * (1 - t) ** 2))
        self.image.blit(self._GLOW, self._GLOW.get_rect(center=center))

        # Small quick ring
        radius = 3 + 14 * (1 - (1 - t) ** 3)
        ring_alpha = int(255 * (1 - t) ** 1.5)
        pygame.draw.circle(self.image, (*self.COLOR, ring_alpha), center, int(radius), max(1, int(3 * (1 - t))))

        for position, velocity in self._sparks:
            start = center + position
            pygame.draw.line(self.image, (*self.SPARK_COLOR, alpha), start, start - velocity * 2.2, 2)


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
