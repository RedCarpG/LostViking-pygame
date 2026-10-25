import pygame
from src.setting import SCREEN_WIDTH
from src.game.groups import G_BOSS
from src.helper.image import get_image
from src.helper.font import get_font, render_text
from .UIState import UIState
from .HealthBar import HealthBar


class UIBoss:

    MOVE_SPEED = 2
    # Health bar colors: normal, and once the boss is enraged (blinking with the second one)
    BAR_COLOR = (24, 138, 70)
    ENRAGED_COLORS = ((236, 110, 36), (255, 170, 80))
    NAME_COLOR = (214, 226, 255)
    BAR_RECT = pygame.Rect(36, 16, 470, 18)

    def __init__(self, surface) -> None:

        self.surface = surface
        self.boss_g = G_BOSS
        self.state = UIState.Hidden
        self._count_blink = 0

        # Main Surface
        # Copy: the health bar is drawn onto it
        self.ui_boss = get_image("UI/Boss/MidTop.png").copy()
        self.ui_boss_rect = self.ui_boss.get_rect(
            midtop=(SCREEN_WIDTH/2, -100))

        # Health Bar
        self.health_bar_img = get_image("UI/Boss/MidTop_HealthBar.png")
        self.health_bar_img_rect = self.health_bar_img.get_rect().move(32, 12)
        self.health_bar = HealthBar(self.ui_boss, self.BAR_RECT, 100)
        # The boss shown, its name under the bar
        self._boss = None
        self._name = None

    def _show_boss(self, boss):
        """ A new bar for `boss` (the Stargate hands over to the Carrier it warps out) """
        self._boss = boss
        self.health_bar = HealthBar(self.ui_boss, self.BAR_RECT, boss.MAX_HEALTH)
        self._name = render_text(get_font("Equip"), boss.NAME, self.NAME_COLOR, spacing=1, shadow=True) \
            if boss.NAME else None

    def update(self):
        if self.state == UIState.Hidden and self.boss_g.sprite is not None:
            self.state = UIState.Entry
            self._show_boss(self.boss_g.sprite)
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
                boss = self.boss_g.sprite
                if boss is not self._boss:
                    self._show_boss(boss)
                self.health_bar.update(boss.health)
                if getattr(boss, "enraged", False):
                    self._count_blink += 1
                    self.health_bar.fill_color = self.ENRAGED_COLORS[(self._count_blink // 20) % 2]
                else:
                    self.health_bar.fill_color = self.BAR_COLOR
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
            if self._name is not None:
                self.surface.blit(self._name, self._name.get_rect(midtop=(SCREEN_WIDTH // 2, self.ui_boss_rect.bottom + 4)))
