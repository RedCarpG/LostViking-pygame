from abc import abstractmethod
import random
import pygame
from pygame import Vector2

from src.game.animation import AnimeSprite, AttachEffect, ScreenShake, HitStop, Explosion
from src.game.groups import G_Enemys
from src.util.type import Pos, Size
from src.helper.sound import play_sound
from src.setting import SCREEN_HEIGHT
from .BasicEnemy import BasicEnemy


class EnemyI(AnimeSprite, BasicEnemy):

    MAX_HEALTH = 100
    SCORE = 100

    ATTACK_SPEED = 100
    MAX_SPEED_X = 0
    MAX_SPEED_Y = 3

    DROP_SUPPLY_CHANCE = 0.1

    # Screen shake trauma added when destroyed (see ScreenShake)
    SHAKE_DESTROY = 0.3

    # Damage dealt to the player when they collide, None destroys the player
    COLLIDE_DAMAGE = None

    # Armored ships take extra damage from the Lanzer Torpedoes (as in StarCraft II)
    ARMORED = False

    # Ground structures (cannons, pylons, the Stargate): the plane flies over them
    GROUND = False

    # Fixed (width, height) collision box, for sprites that rotate: the rect of a
    # rotated image grows with the angle. None uses the rect (see collide_detect)
    HITBOX = None

    # Hit feedback: frames of white flash (light added to the image) and pixels pushed back per hit
    FLASH_DURATION = 3
    FLASH_COLOR = (190, 190, 190)
    KNOCKBACK = 2

    # Explosion when destroyed (see Explosion.SIZES)
    EXPLOSION = "medium"
    # Sound played when destroyed, None: no sound
    DESTROY_SOUND = None
    # Frames the world freezes when destroyed, for the big ships (see HitStop)
    HITSTOP_DESTROY = 0
    # Frames of the destroy animation shown under the explosion (the last ones are
    # dark silhouettes)
    DESTROY_FRAMES_SHOWN = 3

    def __init__(self, pos: Pos, frames, frame_size: Size = None, *groups, **kwargs):
        BasicEnemy.__init__(self)
        AnimeSprite.__init__(self, frames, frame_size,
                             enable_rotate=kwargs.setdefault(
                                 "enable_rotate", False),
                             angle=kwargs.setdefault("angle", 0),
                             *groups)
        # Exact position, the rect only holds whole pixels
        self._pos = Vector2(0, 0)
        self.set_pos(pos)
        self.add(G_Enemys)

        self.attack_speed = self.ATTACK_SPEED
        self._count_attack_interval = random.randint(0, self.ATTACK_SPEED)
        self._speed.y = self.MAX_SPEED_Y
        self.drop_supply_chance = self.DROP_SUPPLY_CHANCE

        self._count_flash = 0
        self._normal_image = None
        self._flash_image = None
        self._hit_effect = None

    # --------------- Super Methods Override --------------- #

    def update(self, *args, **kwargs) -> None:
        """ Update method from Sprite, is called per frame """
        super().update()
        self._move()
        if self.is_active:
            self.action(*args, **kwargs)
        elif self.current_state == "DESTROY" and self._current_frame_index >= self.DESTROY_FRAMES_SHOWN:
            self.kill()
            return
        self._update_flash()

    def anime_end_loop_hook(self):
        if not self.is_active:
            self.kill()

    # --------------- Behaviors --------------- #

    def action(self, *args, **kwargs) -> None:
        """ Main method to be called in `self.update()`
        """
        if self.rect.top > SCREEN_HEIGHT + 100:
            self.kill()
        elif self.rect.top > 0:
            self.attack(None)

    def _move(self) -> None:
        self._pos += self._speed
        self.rect.center = (round(self._pos.x), round(self._pos.y))

    def hit(self, damage=100, target=None, **kwargs) -> bool:
        """ This function is called in collision detection
        :param kwargs: hit_pos, where the bullet hit (used by shields)
        :return: False if this enemy can not be hit any more (already destroyed)
        """
        if not self.is_active:
            return False
        self._damage_hull(damage)
        return True

    def _damage_hull(self, damage) -> None:
        """ Take damage on the health, destroyed when it reaches 0 """
        self._health -= damage
        if self._health > 0:
            # Get Hit effect (restarted by the next hits: stacking copies of a big ship
            # sheet cost a lot of drawing and looked no different)
            if self._hit_effect is not None and self._hit_effect.alive():
                self._hit_effect.set_anime_state("IDLE")
            else:
                self._hit_effect = AttachEffect(
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

    def hit_feedback(self) -> None:
        """ Make a hit feel solid: white flash, small push back and a hit sound """
        self._count_flash = self.FLASH_DURATION
        self._pos.y -= self.KNOCKBACK
        play_sound("ENEMY_HIT")

    def _update_flash(self) -> None:
        if self._count_flash > 0:
            if self.image is not self._flash_image:
                # New animation frame (or first flash frame): make a white copy of it
                self._normal_image = self.image
                self._flash_image = self.image.copy()
                self._flash_image.fill(self.FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD)
                self.image = self._flash_image
            self._count_flash -= 1
        elif self._flash_image is not None:
            if self.image is self._flash_image:
                self.image = self._normal_image
            self._flash_image = None

    def collide_player(self) -> None:
        """ Called when the player flies into this enemy """
        self.destroy()

    def destroy(self, drop_supply=True) -> None:
        """ This method is called when the sprite's health decrease to 0
        The animation state will be set to `DESTROY` and the `self.anime_end_loop_hook()` can be called
        to kill the sprite after destroy animation
        """
        self._health = 0
        self.is_active = False
        self._speed *= 0.5
        self.set_anime_state("DESTROY")
        if self.DESTROY_SOUND is not None:
            play_sound(self.DESTROY_SOUND)
        Explosion(self.rect.center, self.EXPLOSION)
        ScreenShake.add(self.SHAKE_DESTROY)
        if self.HITSTOP_DESTROY:
            HitStop.add(self.HITSTOP_DESTROY)
        from src.game.supply import drop_supply_event
        if drop_supply and random.random() < self.drop_supply_chance:
            drop_supply_event(Pos(self.pos))

    def attack(self, target):
        """ The method is called continuously to perfom a attack in the `self.update()` method
            It counts down the attack interval and will call create a AttachEffect which
            will activate a callback function to call `self.shoot()` after its animation will be finished
        """
        if self._count_attack_interval > 0:
            self._count_attack_interval -= 1
        else:
            self._count_attack_interval = self.attack_speed

            def _attack_cb():
                if self.is_active:
                    self.shoot(target)

            AttachEffect(
                self,
                frames={
                    "IDLE": self.frames["ATTACK"]
                },
                frame_size=None,
                angle=self.angle,
                cb_func=_attack_cb
            )

    @abstractmethod
    def shoot(self, target):
        """ This method will be called after an attack animation is finished """
        pass

    # --------------- Attributes --------------- #
    # ----- Position

    @property
    def pos(self) -> tuple:
        return self.rect.center

    @property
    def hitbox(self):
        if self.HITBOX is None:
            return None
        box = pygame.Rect(0, 0, *self.HITBOX)
        box.center = self.rect.center
        return box

    def set_pos(self, point: Pos) -> None:
        self._pos = Vector2(point.to_list())
        self.rect.center = (round(self._pos.x), round(self._pos.y))
