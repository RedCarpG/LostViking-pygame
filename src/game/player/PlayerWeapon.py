"""
Player controllable object
"""
import pygame
from pygame.sprite import spritecollideany
from abc import ABC, abstractmethod
from src.util.type import Pos
from src.util import if_in_screen, collide_detect
from src.game.groups import G_Enemys, G_Player_Bullets
from src.game.player import PlayerPlane


class PlayerWeapon(ABC):
    LEVEL_MAX = 10

    BASIC_DMG = 80
    INC_DMG = 10

    def __init__(self, player: PlayerPlane):
        self.player = player
        self._damage = self.BASIC_DMG
        self._inc_dmg = self.INC_DMG
        self._level = 1
        self._bullet_type = None

    @property
    def level(self) -> int:
        return self._level

    def level_up(self) -> None:
        if self._level >= self.LEVEL_MAX:
            return
        self._level += 1
        self._damage += self._inc_dmg

    def level_down(self) -> None:
        if self._level <= 1:
            return
        self._level -= 1
        self._damage -= self._inc_dmg

    def reset_level(self) -> None:
        self._level = 1
        self._damage = self.BASIC_DMG

    @property
    def bullet(self):
        return self._bullet_type

    def set_bullet_type(self, bullet_type):
        self._bullet_type = bullet_type

    @abstractmethod
    def shoot(self, pos: Pos):
        return None


class PlayerBullet(pygame.sprite.Sprite, ABC):
    """ Basic Bullet Class
    """

    def __init__(self,
                 pos: Pos,
                 speed: pygame.Vector2,
                 image: pygame.Surface,
                 player: PlayerPlane):
        super().__init__(G_Player_Bullets)
        self.player = player
        self.image = image
        self.rect = self.image.get_rect(center=pos.to_list())
        self.speed = speed
        self.damage = 0

    def update(self):
        # General update method for bullets
        if if_in_screen(self.rect):
            self._move()
            self.collide_enemy(enemy_group=G_Enemys)
        else:
            self.kill()

    def hit(self):
        # General get hit method for bullets
        self.kill()

    def _move(self):
        self.rect.move_ip(self.speed.x, self.speed.y)

    def collide_enemy(self, enemy_group):
        enemy = spritecollideany(self, enemy_group, collide_detect(0.8))
        if enemy and enemy.is_active:
            # A shield absorbs the bullet and shows its own impact effect
            shielded = getattr(enemy, "shield", 0) > 0
            enemy.hit(self.damage, hit_pos=self.rect.center)
            if not enemy.is_active:
                self.player.add_score(enemy.score)
            if shielded:
                self.kill()
            else:
                self.hit()
