import math
import pygame
from pygame.locals import *
from src.helper.font import load_font, get_font, render_text
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR, IS_WEB
from src.game.custom_events import EVENT_START, EVENT_START_TEST, EVENT_OPEN_SETTINGS
from src.game.GameSettings import GameSettings
from .Button import Menu
from .UIPause import post_event


class UIIntro:
    """ Title screen with the main menu """

    TITLE_GLOW = (60, 150, 255)
    HINT_COLOR = (130, 145, 185)

    def __init__(self, surface) -> None:
        load_font("Silkscreen-Bold.ttf", 64, "Title")
        load_font("Silkscreen-Regular.ttf", 16, "IntroHint")
        self.surface = surface

        self.title = render_text(get_font("Title"), "LOST VIKING", COLOR.WHITE,
                                 spacing=1, glow_color=self.TITLE_GLOW)
        self.title_rect = self.title.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.3))

        # Thin line under the title, fading out on both sides
        line_width = 560
        self.line = pygame.Surface((line_width, 2), pygame.SRCALPHA)
        # Brighter in the middle, in hard steps (pixel style)
        for x in range(0, line_width, 8):
            alpha = (60, 130, 220)[min(2, int(3 * math.sin(math.pi * x / line_width)))]
            self.line.fill((*self.TITLE_GLOW, alpha), (x, 0, 8, 2))
        self.line_rect = self.line.get_rect(
            center=(SCREEN_WIDTH / 2, self.title_rect.bottom - 8))

        items = [
            ("START", post_event(EVENT_START)),
            ("SETTINGS", post_event(EVENT_OPEN_SETTINGS)),
            ("TEST MODE", post_event(EVENT_START_TEST)),
        ]
        # A browser page can not be closed by the game
        if not IS_WEB:
            items.append(("EXIT", post_event(pygame.QUIT)))
        self.menu = Menu(self.surface, items, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.48)

        self.hint_text = render_text(
            get_font("IntroHint"),
            "WASD / ARROWS  MOVE     SPACE  SHOOT     Q  BOMB     P  PAUSE",
            self.HINT_COLOR, spacing=0)
        self.hint_rect = self.hint_text.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.76))

        self.best_text = None
        self._render_best()

    def _render_best(self):
        """ Best score under the title (none before the first round) """
        best = GameSettings.best_score
        self.best_text = render_text(get_font("IntroHint"), f"BEST  {best:,}", self.HINT_COLOR,
                                     spacing=1) if best > 0 else None

    def blit(self):
        self.surface.blit(self.title, self.title_rect)
        self.surface.blit(self.line, self.line_rect)
        if self.best_text is not None:
            self.surface.blit(self.best_text, self.best_text.get_rect(
                center=(SCREEN_WIDTH / 2, self.line_rect.bottom + 30)))
        self.menu.blit()
        self.surface.blit(self.hint_text, self.hint_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYUP and event.key == K_ESCAPE and not IS_WEB:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return True
        return self.menu.handle_event(event)

    def reset(self):
        self.menu.reset()
        self._render_best()
