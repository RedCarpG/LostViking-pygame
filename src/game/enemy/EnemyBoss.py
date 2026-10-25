from enum import Enum
import random
import pygame
from src.util.type import Pos, Size
from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.util.inertial import decelerate, accelerate
from src.game.groups import G_BOSS, G_Player1
from src.game.animation import Explosion, Spark, ScreenShake, HitStop, ScreenFX, FloatingText
from src.game.animation.FloatingText import WARNING_COLOR
from src.helper.sound import play_sound
from .EnemyI import EnemyI
from .BossShield import BossShield


class BossActionPhase(Enum):
    MoveDown = 0
    Stay = 1
    MoveX = 2


class EnemyBoss(EnemyI):
    # Shown under its health bar, None: no name
    NAME = None
    MAX_HEALTH = 30000
    SCORE = 15000

    ATTACK_SPEED = 100

    MAX_SPEED_X = 2
    MAX_SPEED_Y = 5
    ACC_X = 0.1
    ACC_Y = 0.1

    IDLE_DURATION = 200
    MOVE_X_DURATION = 200

    # Height of the top edge where the boss stops after coming in (can be above the screen)
    STOP_TOP = 0

    DROP_SUPPLY_CHANCE = 0

    SHAKE_DESTROY = 1.0

    # Death: explosions all over the ship for DEATH_DURATION frames, then a last big blast
    DEATH_DURATION = 120
    DEATH_BLAST_INTERVAL = 8
    SHAKE_DEATH_BLAST = 0.3

    # The last blast: frames the world freezes, white flash strength
    HITSTOP_FINAL_BLAST = 10
    FLASH_FINAL_BLAST = 0.6

    # Flying into the boss destroys the player, the boss only takes some damage
    COLLIDE_SELF_DAMAGE = 500
    KNOCKBACK = 0
    # A boss is hit all the time: a soft flash, and the red overlay only when a burst starts,
    # so its art still shows
    FLASH_COLOR = (56, 56, 56)
    HIT_OVERLAY_QUIET = 30

    # Energy shield (0: none). It takes the hits first and recharges after SHIELD_REGEN_DELAY
    # frames without a hit, SHIELD_REGEN points per frame; once broken (0) it is gone for good
    MAX_SHIELD = 0
    SHIELD_REGEN = 0
    SHIELD_REGEN_DELAY = 120
    SHAKE_SHIELD_BREAK = 0.5

    def __init__(self, frames, frame_size: Size, **kwargs):
        super().__init__(pos=Pos([0, 0]), frames=frames,
                         frame_size=frame_size, **kwargs)
        self.add(G_BOSS)

        self.state = BossActionPhase.MoveDown

        self._move_x_direction = None
        self._count_action_idle = self.IDLE_DURATION
        self._count_action_move_x = self.MOVE_X_DURATION

        self.set_pos(Pos([SCREEN_WIDTH // 2, -self.rect.height]))
        self.enter_action_move_down_phase()
        self._count_dying = 0

        self.shield = self.MAX_SHIELD
        self._count_shield_regen = 0
        self.shield_effect = BossShield(self) if self.MAX_SHIELD else None

    # -------------------- Shield --------------------
    def hit(self, damage=100, target=None, **kwargs) -> bool:
        """ The shield takes the hits while it lasts (a nuke goes through: `ignore_shield`) """
        if not self.is_active:
            return False
        if self.shield > 0 and not kwargs.get("ignore_shield"):
            self._hit_shield(damage, kwargs.get("hit_pos"))
            return True
        return super().hit(damage, target=target, **kwargs)

    def shield_contains(self, point) -> bool:
        """ True if `point` is inside the shield (wider than the hull: shots stop at its edge) """
        if self.shield <= 0 or self.shield_effect is None:
            return False
        a, b = self.shield_effect.semi_axes
        dx = (point[0] - self.rect.centerx) / a
        dy = (point[1] - self.rect.centery) / b
        return dx * dx + dy * dy <= 1

    def _hit_shield(self, damage, hit_pos) -> None:
        self._count_shield_regen = self.SHIELD_REGEN_DELAY
        self.shield = max(0, self.shield - damage)
        play_sound("SHIELD")
        self.shield_effect.impact(hit_pos)
        if self.shield == 0:
            self._break_shield()

    def _break_shield(self) -> None:
        self.shield_effect.burst()
        ScreenShake.add(self.SHAKE_SHIELD_BREAK)
        play_sound("POWER_DOWN")
        FloatingText((self.rect.centerx, self.rect.bottom + 30), "SHIELD DOWN", WARNING_COLOR, duration=90)

    def _regenerate_shield(self) -> None:
        """ Recharges after a while without a hit, unless it was broken """
        recharging = 0 < self.shield < self.MAX_SHIELD and self._count_shield_regen == 0
        if self._count_shield_regen > 0:
            self._count_shield_regen -= 1
        elif recharging:
            self.shield = min(self.MAX_SHIELD, self.shield + self.SHIELD_REGEN)
        if self.shield_effect is not None:
            self.shield_effect.recharging = recharging

    # -------------------- Main action states --------------------
    def action(self):
        if self.MAX_SHIELD:
            self._regenerate_shield()
        if self.state == BossActionPhase.MoveDown:
            self._action_move_down()
        else:
            self._action_stay()
            player = G_Player1.sprites()[0]
            self.attack(target=player)

    # -------------------- Sub action states --------------------
    def enter_action_move_down_phase(self):
        self.state = BossActionPhase.MoveDown

    def _action_move_down(self):
        # Start braking just in time to stop at STOP_TOP
        braking_distance = self._speed.y ** 2 / (2 * self.ACC_Y)
        if self.STOP_TOP - self.rect.top <= braking_distance:
            self._speed.y = decelerate(self._speed.y, self.ACC_Y)
            if self._speed.y == 0:
                self.enter_action_stay_phase()

    def enter_action_stay_phase(self):
        self._count_action_idle = self.IDLE_DURATION
        self.state = BossActionPhase.Stay
        self._move_x_direction = random.choice([1, -1])

    def _action_stay(self):
        if self._count_action_idle > 0:
            self._count_action_idle -= 1
        else:

            if self._count_action_move_x > 0:
                # Accelerate (if not max) and count down
                self._speed.x = accelerate(self._speed.x,
                                           self.MAX_SPEED_X,
                                           self._move_x_direction,
                                           self.ACC_X)
                self._count_action_move_x -= 1
            else:
                # Decelerate in X direction and enter idle phase
                self._speed.x = decelerate(self._speed.x, self.ACC_X)
                if self._speed.x == 0:
                    self._count_action_move_x = self.MOVE_X_DURATION
                    self._count_action_idle = self.IDLE_DURATION

    # -------------------- Behaviors --------------------
    def _move(self) -> None:
        super()._move()
        # Bounce on the screen edges (only when moving outwards, so it does not get stuck flipping)
        if (self.rect.left < 0 and self._speed.x < 0) or (self.rect.right > SCREEN_WIDTH and self._speed.x > 0):
            self._move_x_direction = -self._move_x_direction
            self._speed.x = -self._speed.x

    def collide_player(self) -> None:
        self.hit(self.COLLIDE_SELF_DAMAGE)

    # -------------------- Death --------------------
    @property
    def dying(self) -> bool:
        return self._count_dying > 0

    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        if self._count_dying > 0 and self.alive():
            self._update_dying()

    def anime_end_loop_hook(self):
        # While dying, the ship stays until the last blast
        if self._count_dying == 0:
            super().anime_end_loop_hook()

    def destroy(self, drop_supply=True) -> None:
        """ Start the death: explosions all over the ship, then a last big blast (see final_blast) """
        if self._count_dying > 0 or not self.is_active:
            return
        self._health = 0
        self.is_active = False
        self._speed *= 0
        self._count_dying = self.DEATH_DURATION
        play_sound("ENEMY_DESTROY")

    def _update_dying(self):
        self._count_dying -= 1
        if self._count_dying == 0:
            self.final_blast()
        elif self._count_dying % self.DEATH_BLAST_INTERVAL == 0:
            # Somewhere on the part of the ship that is on screen
            area = self.rect.inflate(-self.rect.width // 4, -self.rect.height // 4)
            area = area.clip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pos = (random.randint(area.left, area.right), random.randint(area.top, area.bottom))
            Explosion(pos, random.choice(("medium", "medium", "large")))
            ScreenShake.add(self.SHAKE_DEATH_BLAST)
            self._count_flash = self.FLASH_DURATION
            if self._count_dying % (self.DEATH_BLAST_INTERVAL * 2) == 0:
                play_sound("ENEMY_DESTROY")

    def final_blast(self):
        """ The last big explosion: the ship breaks apart (destroy animation) """
        visible = self.rect.clip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        x, y = visible.center
        for i, (dx, dy) in enumerate(((0, 0), (-70, -40), (70, -30), (-30, 60), (40, 70))):
            Explosion((x + dx, y + dy), "large", delay=i * 4)
        Spark.burst((x, y), 30, 120)
        ScreenShake.add(self.SHAKE_DESTROY)
        HitStop.add(self.HITSTOP_FINAL_BLAST)
        ScreenFX.flash(strength=self.FLASH_FINAL_BLAST, duration=45)
        self.set_anime_state("DESTROY")
