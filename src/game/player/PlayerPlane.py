""" Player controllable object
Includes:
    -> PlayerPlane
"""
import random
import pygame
from pygame import Vector2
from pygame.sprite import spritecollide, spritecollideany
from pygame.locals import KEYDOWN, KEYUP

from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT

from src.util.collide_detect import collide_detect
from src.util.type import Pos
from src.util.inertial import accelerate, decelerate

from src.helper.sound import play_sound

from src.game.groups import G_Enemys, G_Enemy_Bullets, G_Players
from src.game.animation import AnimeSprite, ScreenShake, HitStop, ScreenFX, Explosion, FloatingText, TransformRing
from src.game.animation.TransformRing import SWITCH_COLORS
from src.game.animation.Effect import AttachEffect
from src.game.custom_events import EVENT_PLAYER_SHOOT, EVENT_PLAYER_BOMB
from .player_control import PLAYER1_CONTROL, PLAYER2_CONTROL
from .PlayerWeapon import PlayerWeapon


class PlayerPlane(AnimeSprite):
    """ Basic Player Abstract class
    """
    BOMB_COUNT_MAX = 3
    BOMB_COUNT_DEFAULT = 1

    LIFE_MAX = 5
    LIFE_DEFAULT = 3

    MAX_SPEED_X = 8
    MAX_SPEED_UP = 10
    MAX_SPEED_DOWN = 5
    ACC_X = 0.8
    ACC_UP = 1
    ACC_DOWN = 0.6
    MAX_HEALTH = 100

    INVINCIBLE_DURATION = 100

    LIMIT_BOTTOM = 100

    # Screen shake trauma (see ScreenShake)
    SHAKE_HIT = 0.5
    SHAKE_DESTROY = 0.8
    # Chance of a second upgrade orb when more than one upgrade is lost on death
    EXTRA_DROP_CHANCE = 0.5
    # Frames of the destroy animation shown under the explosion (then the plane is
    # hidden until it comes back)
    DESTROY_FRAMES_SHOWN = 2
    # Hits with less damage shake less, and continuous damage (e.g. a laser)
    # only shakes again after a short cooldown
    SHAKE_FULL_DAMAGE = 30
    SHAKE_HIT_COOLDOWN = 12
    # The screen edges pulse red at this health or below
    LOW_HEALTH = 30
    # Frames the world freezes when the plane is destroyed (see HitStop)
    HITSTOP_DESTROY = 6
    # Frames to switch weapons (the Viking transforms), no shot meanwhile
    TRANSFORM_FRAMES = 24

    def __init__(self, weapons: list, pos, frames, frame_size, id=1):
        """ :param weapons: the weapons the plane switches between (they share the level) """
        # Init
        super().__init__(frames=frames, frame_size=frame_size)

        self.id = id
        if id == 1:
            self.controller = PLAYER1_CONTROL
        else:
            self.controller = PLAYER2_CONTROL

        if pos:
            self.start_position = pos
        else:
            self.start_position = (int(pygame.display.get_surface().get_width() // 2),
                                   int(pygame.display.get_surface().get_height() - self.rect.height - self.LIMIT_BOTTOM))

        self._weapons = weapons
        self._weapon_index = 0
        self._count_transform = 0
        # Graviton beam holding the plane (see lift), and the part of a pixel not moved yet
        self._lifted_by = None
        self._lift_carry = Vector2(0, 0)
        # Frames left frozen in stasis (see stasis)
        self._count_stasis = 0

        self._score = 0
        # Enemies destroyed by this player
        self.kills = 0
        self._life = self.LIFE_DEFAULT
        self._bomb_count = self.BOMB_COUNT_DEFAULT
        self._level = 1

        self._speed = pygame.Vector2(0, 0)
        self._health = self.MAX_HEALTH

        self._count_attack_interval = 0
        self._count_invincible = 0
        self._count_shake_cooldown = 0
        self._hit_effect = None

        ''' States '''
        self.state = None
        self.is_invincible = False
        self.is_active = True
        # Set when the last life is lost and the destroy animation has finished
        self.is_dead = False
        self._is_moving_x = False
        self._is_moving_y = False

        # Set init position
        self.set_pos(pos)

    # --------------- Super Methods Override --------------- #
    def update(self) -> None:
        """ Update method from Sprite, is called per frame """
        if self._count_stasis > 0:
            # Frozen: no animation, no move, nothing touches it
            self._count_stasis -= 1
            return
        super().update()
        if not self.is_active and self.current_state == "DESTROY" \
                and self._current_frame_index >= self.DESTROY_FRAMES_SHOWN:
            self.image = self._hidden_image()
        self._reload()
        if self._count_shake_cooldown > 0:
            self._count_shake_cooldown -= 1
        if self.is_active:
            if self.is_invincible:
                if self._count_invincible > 0:
                    self._count_invincible -= 1
                elif self._count_invincible == 0:
                    self.is_invincible = False
            self._move()
            self.collide_enemy(G_Enemys)
            self.collide_enemy_bullet(G_Enemy_Bullets)

    def anime_end_loop_hook(self):
        if not self.is_active and not self.is_dead:
            if self._life > 0:
                self.reset()
            else:
                # No life left: hide the plane, the game will show the result screen
                self.is_dead = True
                self.remove(G_Players)

    # --------------------- Behaviors ---------------------

    def _move(self) -> None:
        beam = self._lifted_by
        if self._speed.y != 0 or self._speed.x != 0 or beam is not None:
            # Move this object
            # (Note: this is the only place when the object is really moving)
            if beam is not None:
                # Held by a graviton beam: weak controls, pulled toward the beam's ship
                delta = self._speed * beam.CONTROL + beam.pull(self.rect.center) + self._lift_carry
                step = (int(delta.x), int(delta.y))
                self._lift_carry = delta - Vector2(step)
                self.rect.move_ip(step)
            else:
                self.rect.move_ip(self._speed)

            # Speed down if there's no movement command on X or Y
            # (Note: Only values of _speed_x/_speed_y will be changed here)
            if not self._is_moving_x:
                self._speed.x = decelerate(self._speed.x, self.ACC_X)
            if not self._is_moving_y:
                self._speed.y = decelerate(self._speed.y, self.ACC_DOWN)

            # Restrict the plane inside the screen
            if self.rect.bottom > SCREEN_HEIGHT - self.LIMIT_BOTTOM:
                self.rect.bottom = SCREEN_HEIGHT - self.LIMIT_BOTTOM
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
            if self.rect.top < 0:
                self.rect.top = 0

    def _reload(self):
        if self._count_attack_interval > 0:
            self._count_attack_interval -= 1
        if self._count_transform > 0:
            self._count_transform -= 1

    def destroy(self) -> None:
        self._health = 0
        self.dec_life()
        self.is_active = False
        self._is_moving_y = False
        self._is_moving_x = False
        self.set_anime_state("DESTROY")
        play_sound("PLAYER_DESTROY")
        ScreenShake.add(self.SHAKE_DESTROY)
        HitStop.add(self.HITSTOP_DESTROY)
        ScreenFX.hurt(1.0)
        Explosion(self.rect.center, "large")
        self._drop_upgrades()

    def _hidden_image(self) -> pygame.Surface:
        if getattr(self, "_hidden", None) is None or self._hidden.get_size() != self.rect.size:
            self._hidden = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        return self._hidden

    def _drop_upgrades(self):
        """ The lost weapon upgrades: one upgrade orb pops out of the wreck,
        a second one (by chance) when more than one upgrade was lost
        """
        # Imported here: the supplies import this module
        from src.game.supply import SupplyLevel
        lost = self.level - 1
        drops = 0
        if lost >= 1:
            drops = 1
        if lost >= 2 and random.random() < self.EXTRA_DROP_CHANCE:
            drops = 2
        angles = [0] if drops == 1 else [-35, 35]
        for angle in angles[:drops]:
            supply = SupplyLevel(Pos(self.rect.center))
            supply.pop(Vector2(0, -1).rotate(angle + random.uniform(-15, 15)), speed=5)

    # ------------------ Battle
    def hit(self, damage=100, **kwargs) -> bool:
        """
        This function is called in collision detection
        """
        if not self.is_invincible and self.is_active and not self.in_stasis:
            # Take damage
            self._health -= damage
            # Red screen edges, stronger for a bigger hit
            ScreenFX.hurt(min(1.0, 0.25 + damage / 50))
            if self._health > 0:
                # Get Hit effect (restarted by continuous damage, e.g. a laser)
                if self._hit_effect is not None and self._hit_effect.alive():
                    self._hit_effect.set_anime_state("IDLE")
                else:
                    self._hit_effect = AttachEffect(
                        self,
                        frames={
                            "IDLE": self.frames["HIT"]
                        },
                        frame_size=self.frame_size
                    )
                if self._count_shake_cooldown == 0:
                    ScreenShake.add(self.SHAKE_HIT * min(1.0, damage / self.SHAKE_FULL_DAMAGE))
                    self._count_shake_cooldown = self.SHAKE_HIT_COOLDOWN
            else:
                # HP below 0
                self.destroy()
            return True
        else:
            return False

    # ------------------ Graviton beam (Phoenix)
    @property
    def lifted(self) -> bool:
        return self._lifted_by is not None

    def lift(self, beam) -> bool:
        """ Caught by a graviton beam (see GravitonBeam)
        :return: False if it can not be caught (destroyed, invincible or already held)
        """
        if not self.is_active or self.is_invincible or self._lifted_by is not None or self.in_stasis:
            return False
        self._lifted_by = beam
        self._lift_carry = Vector2(0, 0)
        return True

    def release(self, beam) -> None:
        if self._lifted_by is beam:
            self._lifted_by = None

    # ------------------ Stasis (Oracle's Stasis Ward)
    @property
    def in_stasis(self) -> bool:
        return self._count_stasis > 0

    def stasis(self, frames) -> bool:
        """ Frozen for `frames`: it can not move or shoot, and nothing can hurt it (as in StarCraft II)
        :return: False if it can not be frozen (destroyed, invincible or already frozen)
        """
        if not self.is_active or self.is_invincible or self.in_stasis:
            return False
        self._count_stasis = frames
        self._speed.update(0, 0)
        self._is_moving_x = self._is_moving_y = False
        if self._lifted_by is not None:
            self._lifted_by.kill()
        return True

    def invincible(self, duration: int = None, continuous: bool = False):
        if continuous:
            self._count_invincible = -1
        elif duration is not None:
            self._count_invincible = duration
        else:
            self._count_invincible = self.INVINCIBLE_DURATION
        self.is_invincible = True

    def remove_invincible(self):
        self._count_invincible = 0
        self.is_invincible = False

    def attack(self) -> None:
        """
        This method is called from a user attack event
        """
        if self.is_active and self._count_transform == 0 and not self.in_stasis:
            if self._count_attack_interval == 0:
                weapon = self.weapon
                play_sound(weapon.SHOOT_SOUND)
                weapon.shoot(pos=Pos(self.rect.center))
                self._count_attack_interval = weapon.fire_interval

    def collide_enemy(self, enemy_group):
        # The plane flies over ground structures: only ships (and wards, rocks) are in its way
        enemy = next((each for each in spritecollide(self, enemy_group, False, collide_detect(0.5))
                      if each.is_active and not each.GROUND), None)
        if enemy and not self.is_invincible:
            # Each enemy decides how much a collision hurts (see EnemyI.COLLIDE_DAMAGE)
            if enemy.COLLIDE_DAMAGE is None:
                self.destroy()
            elif enemy.COLLIDE_DAMAGE:
                self.hit(enemy.COLLIDE_DAMAGE)
            enemy.collide_player()
            if not enemy.is_active:
                self.credit_kill(enemy)

    def collide_enemy_bullet(self, enemy_bullet_group):
        bullet = spritecollideany(
            self, enemy_bullet_group, collide_detect(0.6))
        if bullet:
            self.hit(bullet.damage)
            bullet.hit(target=self)

    # ------------------ Trigger-Movement-Commands ------------------
    # ------------------ (Instant trigger method called by events) --
    # Trigger Move Up

    def trigger_move_up(self) -> None:
        """ Trigger this object to move Up (with acceleration)
        Called by event (e.g. Button press)
        """
        if not self.is_active:
            return
        # If the plane starts to move, switch frame to "MOVE_UP"
        if not self._is_moving_y:
            self._is_moving_y = True
            self.set_anime_state("MOVE_UP")
        # If not outside the screen
        if self.rect.top > 0:
            self._speed.y = accelerate(
                self._speed.y, self.MAX_SPEED_UP, -1, self.ACC_UP)
        else:
            self._speed.y = 0
            self.rect.top = 0

    # Trigger Move Down
    def trigger_move_back(self) -> None:
        """ Trigger this object to move Down (with acceleration)
        Called by event (e.g. Button press)
        (Note: This method only change the value of _speed_x / _speed_y)
        """
        if not self.is_active:
            return
        # If it was not moving before, change image
        if not self._is_moving_y:
            self._is_moving_y = True
            self.set_anime_state("MOVE_DOWN")
        # If not outside the screen
        if self.rect.bottom < SCREEN_HEIGHT - self.LIMIT_BOTTOM:
            self._speed.y = accelerate(
                self._speed.y, self.MAX_SPEED_DOWN, 1, self.ACC_DOWN)
        else:
            self._speed.y = 0
            self.rect.bottom = SCREEN_HEIGHT - self.LIMIT_BOTTOM

    # Trigger Move Left
    def trigger_move_left(self) -> None:
        """ Trigger this object to move Left (with acceleration)
        Called by event (e.g. Button press)
        (Note: This method only change the value of _speed_x / _speed_y)
        """
        if not self.is_active:
            return
        # If not outside the screen
        if self.rect.left > 0:
            self._is_moving_x = True
            self._speed.x = accelerate(
                self._speed.x, self.MAX_SPEED_X, -1, self.ACC_X)
        else:
            self._speed.x = 0
            self.rect.left = 0

    # Trigger Move Right
    def trigger_move_right(self) -> None:
        """ Trigger this object to move Right (with acceleration)
        Called by event (e.g. Button press)
        (Note: This method only change the value of _speed_x / _speed_y)
        """
        if not self.is_active:
            return
        # If not outside the screen
        if self.rect.right < SCREEN_WIDTH:
            self._is_moving_x = True
            self._speed.x = accelerate(
                self._speed.x, self.MAX_SPEED_X, 1, self.ACC_X)
        else:
            self._speed.x = 0
            self.rect.right = SCREEN_WIDTH

    # Trigger Brake y, only triggered when lease the button
    def trigger_stop_y(self) -> None:
        """ Trigger this object to stop in y axis (with acceleration)
        Triggered by event (e.g. Button release)
        (Note: This only sets the flag, the deceleration will be done
        by _inertial_deceleration automatically in update)
        """
        self._is_moving_y = False
        if self.is_active:
            self.set_anime_state("IDLE")

    # Trigger Brake x
    def trigger_stop_x(self) -> None:
        """ Trigger this object to stop in x axis (with acceleration)
        Triggered by event (e.g. Button release)
        (Note: This only sets the flag, the deceleration will be done
        by _inertial_deceleration automatically in update)
        """
        self._is_moving_x = False

    # ------------------ Attributes -----------------

    # ----- Life
    @property
    def life(self) -> int:
        return self._life

    def add_life(self) -> bool:
        if self._life >= self.LIFE_MAX:
            return False
        self._life += 1
        return True

    def dec_life(self) -> bool:
        if self._life <= 0:
            return False
        self._life -= 1
        return True

    # ----- Weapon & Level

    @property
    def weapon(self) -> PlayerWeapon:
        """ The weapon in use """
        return self._weapons[self._weapon_index]

    @property
    def weapons(self) -> list:
        return self._weapons

    @property
    def weapon_index(self) -> int:
        return self._weapon_index

    @property
    def transforming(self) -> bool:
        return self._count_transform > 0

    def switch_weapon(self) -> bool:
        """ Change to the next weapon (the plane can not shoot while it transforms)
        :return: False if it can not switch now
        """
        if not self.is_active or self._count_transform > 0 or len(self._weapons) < 2 or self.in_stasis:
            return False
        self._weapon_index = (self._weapon_index + 1) % len(self._weapons)
        self._count_transform = self.TRANSFORM_FRAMES
        weapon = self.weapon
        if weapon.SWITCH_SOUND:
            play_sound(weapon.SWITCH_SOUND)
        TransformRing(self, self._weapon_index)
        FloatingText((self.rect.centerx, self.rect.top - 8), weapon.NAME, SWITCH_COLORS[self._weapon_index])
        return True

    @property
    def level(self) -> int:
        return self.weapon.level

    def level_up(self) -> bool:
        """ Every weapon goes up a level
        :return: False if the weapons were already at their highest level
        """
        return all([each.level_up() for each in self._weapons])

    def level_down(self) -> None:
        for each in self._weapons:
            each.level_down()

    def reset_level(self) -> None:
        for each in self._weapons:
            each.reset_level()

    # ----- Score
    @property
    def score(self) -> int:
        return self._score

    def add_score(self, score) -> None:
        self._score += score

    def credit_kill(self, enemy) -> None:
        """ Points for an enemy destroyed by this player, shown where it was """
        self._score += enemy.score
        self.kills += 1
        FloatingText(enemy.rect.center, f"{enemy.score:,}")

    # ----- Position
    @property
    def pos(self) -> tuple[int, int]:
        return self.rect.center

    def set_pos(self, point=None) -> None:
        if point is None:
            self.rect.center = self.start_position
        else:
            # Move its rect to a point, or a default position
            self.rect.center = point

    # ----- Speed
    @property
    def speed(self) -> pygame.Vector2:
        return self._speed

    # ----- Health
    @property
    def health(self) -> int:
        return self._health

    def add_health(self) -> bool:
        if self.health < self.MAX_HEALTH:
            self._health = self.MAX_HEALTH
            return True
        return False

    # ----- Bomb
    @property
    def bomb_count(self) -> int:
        return self._bomb_count

    def add_bomb(self) -> bool:
        if self._bomb_count >= self.BOMB_COUNT_MAX:
            return False
        self._bomb_count += 1
        return True

    def dec_bomb(self) -> bool:
        if self._bomb_count <= 0:
            return False
        self._bomb_count -= 1
        return True

    # ----------------- Reset method -----------------
    # Reset
    def reset(self, point=None) -> None:
        self.is_active = True
        self.is_invincible = True
        self._count_invincible = self.INVINCIBLE_DURATION
        self.set_anime_state("IDLE")
        self.set_pos(point)

        def break_cb_func():
            return not self.is_invincible
        AttachEffect(
            self,
            frames={
                "IDLE": self.frames["INVINCIBLE"]
            },
            frame_size=self.frame_size,
            break_cb_func=break_cb_func,
            loop=True
        )
        self.reset_level()
        self._count_transform = 0
        self._count_stasis = 0
        self._health = self.MAX_HEALTH

    # ----------------- Event -----------------

    @staticmethod
    def _held(key_pressed, keys) -> bool:
        return any(key_pressed[key] for key in keys)

    def detect_key_pressed(self):
        # If Key Pressed
        key_pressed = pygame.key.get_pressed()
        control = self.controller
        if self.in_stasis:
            return
        # Vertical and horizontal axes are checked separately to allow diagonal movement
        if self._held(key_pressed, control.MOVE_UP):
            self.trigger_move_up()
        elif self._held(key_pressed, control.MOVE_DOWN):
            self.trigger_move_back()
        if self._held(key_pressed, control.MOVE_LEFT):
            self.trigger_move_left()
        elif self._held(key_pressed, control.MOVE_RIGHT):
            self.trigger_move_right()
        # Keep shooting while the key is held (attack() limits the fire rate).
        # Polled here because pygame.time.set_timer is not available on WASM
        if self._held(key_pressed, control.SHOOT):
            pygame.event.post(pygame.event.Event(
                EVENT_PLAYER_SHOOT, {"player": self, "id": self.id}))

    def handle_event(self, e):
        control = self.controller
        if e.type == KEYDOWN:
            if e.key in control.SWITCH:
                self.switch_weapon()
                return True
            # Shooting is handled in detect_key_pressed()
            return e.key in control.SHOOT
        # --------------- Key Up Events ---------------
        elif e.type == KEYUP:
            vertical = control.MOVE_UP + control.MOVE_DOWN
            horizontal = control.MOVE_LEFT + control.MOVE_RIGHT
            if e.key in vertical:
                # Two keys can move the same way (WASD and arrows): stop when none is held
                if not self._held(pygame.key.get_pressed(), vertical):
                    self.trigger_stop_y()
            elif e.key in horizontal:
                if not self._held(pygame.key.get_pressed(), horizontal):
                    self.trigger_stop_x()
            elif e.key in control.BOMB:
                pygame.event.post(pygame.event.Event(
                    EVENT_PLAYER_BOMB, {"player": self, "id": self.id}))
            elif e.key in control.SHOOT or e.key in control.SWITCH:
                pass
            else:
                return False
            return True
        return False
