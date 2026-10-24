import pygame
from src.setting import SCREEN_WIDTH
from src.game.groups import G_BOSS
from src.helper.image import get_image
from .UIState import UIState
from .HealthBar import HealthBar


class UIBoss:

    MOVE_SPEED = 2

    def __init__(self, surface) -> None:

        self.surface = surface
        self.boss_g = G_BOSS
        self.state = UIState.Hidden

        # Main Surface
        # Copy: the health bar is drawn onto it
        self.ui_boss = get_image("UI/Boss/MidTop.png").copy()
        self.ui_boss_rect = self.ui_boss.get_rect(
            midtop=(SCREEN_WIDTH/2, -100))

        # Health Bar
        self.health_bar_img = get_image("UI/Boss/MidTop_HealthBar.png")
        self.health_bar_img_rect = self.health_bar_img.get_rect().move(32, 12)
        self.health_bar = HealthBar(
            self.ui_boss, pygame.Rect(36, 16, 470, 18), 100)

    def update(self):
        if self.state == UIState.Hidden and self.boss_g.sprite is not None:
            self.state = UIState.Entry
            self.health_bar.max_health = self.boss_g.sprite.MAX_HEALTH
        elif self.state in [UIState.Entry, UIState.Idle]:
            if self.state == UIState.Entry:
                if self.ui_boss_rect.top < 0:
                    self.ui_boss_rect.move_ip([0, self.MOVE_SPEED])
                else:
                    self.ui_boss_rect.top = 0
                    self.state = UIState.Idle

            if self.boss_g.sprite is None:
                self.state = UIState.Exit
                self.health_bar.max_health = 100
            else:
                self.health_bar.update(self.boss_g.sprite.health)
        elif self.state == UIState.Exit:
            if self.ui_boss_rect.bottom > 0:
                self.ui_boss_rect.move_ip([0, -self.MOVE_SPEED])
            else:
                self.state = UIState.Hidden

    def blit(self):
        if self.boss_g.sprite is not None:
            self.health_bar.blit()
            self.ui_boss.blit(self.health_bar_img, self.health_bar_img_rect)
            self.surface.blit(self.ui_boss, self.ui_boss_rect)
