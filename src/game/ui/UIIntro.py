import math
import pygame
from pygame.locals import *
from src.helper.font import load_font, get_font, del_font, render_text
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR
from src.game.custom_events import EVENT_START


class UIIntro:

    TITLE_GLOW = (60, 150, 255)
    HINT_COLOR = (130, 145, 185)

    def __init__(self, surface) -> None:
        load_font("Raleway-Light.ttf", 104, "Title")
        load_font("Raleway-Regular.ttf", 24, "Intro")
        load_font("Raleway-Regular.ttf", 17, "IntroHint")
        self.surface = surface

        self.title = render_text(get_font("Title"), "LOST VIKING", COLOR.WHITE,
                                 spacing=10, glow_color=self.TITLE_GLOW, glow_size=12)
        self.title_rect = self.title.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.34))

        # Thin line under the title, fading out on both sides
        line_width = 560
        self.line = pygame.Surface((line_width, 2), pygame.SRCALPHA)
        for x in range(line_width):
            alpha = int(200 * math.sin(math.pi * x / line_width))
            self.line.fill((*self.TITLE_GLOW, alpha), (x, 0, 1, 2))
        self.line_rect = self.line.get_rect(
            center=(SCREEN_WIDTH / 2, self.title_rect.bottom - 8))

        self.intro_text = render_text(get_font("Intro"), "PRESS ANY KEY TO START",
                                      COLOR.WHITE, spacing=6)
        self.intro_rect = self.intro_text.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.55))

        self.hint_text = render_text(
            get_font("IntroHint"),
            "WASD  MOVE      SPACE  SHOOT      Q  BOMB      ESC  PAUSE",
            self.HINT_COLOR, spacing=2)
        self.hint_rect = self.hint_text.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.62))

        self.count_flash = 0

    def blit(self):
        self.surface.blit(self.title, self.title_rect)
        self.surface.blit(self.line, self.line_rect)

        # Smooth pulse instead of on/off blinking
        self.count_flash += 1
        alpha = int(255 * (0.55 + 0.45 * math.sin(self.count_flash * 0.06)))
        self.intro_text.set_alpha(alpha)
        self.surface.blit(self.intro_text, self.intro_rect)
        self.surface.blit(self.hint_text, self.hint_rect)

    def handle_event(self, event):

        if event.type == pygame.KEYUP:
            if event.key == K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            else:
                pygame.event.post(pygame.event.Event(EVENT_START))

            return True

        return False

    def __del__(self):
        del_font("Title")
        del_font("Intro")
        del_font("IntroHint")
