import pygame
from pygame.locals import *
from src.helper.font import get_font, render_text
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR, IS_WEB
from src.game.custom_events import EVENT_RESUME, EVENT_RESTART, EVENT_OPEN_SETTINGS, EVENT_MAIN_MENU
from .Button import Menu


def post_event(event_type):
    """ Return a function posting a pygame event, used as a menu button action """
    return lambda: pygame.event.post(pygame.event.Event(event_type))


class UIPause:

    def __init__(self, surface) -> None:
        self.surface = surface

        self.pause_text = render_text(get_font("MenuTitle"), "PAUSED", COLOR.WHITE,
                                      spacing=1, glow_color=(60, 150, 255))
        self.pause_rect = self.pause_text.get_rect(
            center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 150))

        items = [
            ("RESUME", post_event(EVENT_RESUME)),
            ("RESTART", post_event(EVENT_RESTART)),
            ("SETTINGS", post_event(EVENT_OPEN_SETTINGS)),
            ("MAIN MENU", post_event(EVENT_MAIN_MENU)),
        ]
        # A browser page can not be closed by the game
        if not IS_WEB:
            items.append(("EXIT", post_event(pygame.QUIT)))
        self.menu = Menu(self.surface, items, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 40)

    def blit(self):
        self.menu.blit()
        self.surface.blit(self.pause_text, self.pause_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYUP and event.key == K_ESCAPE:
            pygame.event.post(pygame.event.Event(EVENT_RESUME))
            return True
        return self.menu.handle_event(event)

    def reset(self):
        self.menu.reset()
