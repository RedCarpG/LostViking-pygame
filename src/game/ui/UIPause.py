import pygame
from pygame.locals import *
from src.helper.font import get_font, render_text
from src.util.type import Pos
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR, IS_WEB
from src.game.custom_events import EVENT_RESUME, EVENT_RESTART
from .Button import Button, text_button_frames


class UIPause:

    def __init__(self, surface) -> None:
        self.surface = surface

        self.pause_text = render_text(get_font("MenuTitle"), "PAUSED", COLOR.WHITE,
                                      spacing=10, glow_color=(60, 150, 255), glow_size=10)
        self.pause_rect = self.pause_text.get_rect(
            center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 120))

        def resume_game(button):
            pygame.event.post(pygame.event.Event(EVENT_RESUME))

        self.button_resume = Button(
            self.surface,
            function=resume_game,
            frames=text_button_frames("RESUME"),
            center=Pos([SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 10])
        )
        self.button_resume.toggle_choose()

        def restart_game(button):
            pygame.event.post(pygame.event.Event(EVENT_RESTART))
        self.button_restart = Button(
            self.surface,
            function=restart_game,
            frames=text_button_frames("RESTART"),
            center=Pos([SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 60])
        )

        def end_game(button):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.button_exit = Button(
            self.surface,
            function=end_game,
            frames=text_button_frames("EXIT"),
            center=Pos([SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 130])
        )

        self.buttons = []
        self.buttons.append(self.button_resume)
        self.buttons.append(self.button_restart)
        # A browser page can not be closed by the game
        if not IS_WEB:
            self.buttons.append(self.button_exit)

        self.button_choosed = 0

    def blit(self):
        for each in self.buttons:
            each.blit()
        self.surface.blit(self.pause_text, self.pause_rect)

    def handle_event(self, event):

        if event.type == pygame.KEYUP:
            if event.key in [K_s, K_DOWN]:
                self.buttons[self.button_choosed].toggle_choose()
                self.button_choosed = (
                    self.button_choosed + 1) % len(self.buttons)
                self.buttons[self.button_choosed].toggle_choose()
            elif event.key in [K_w, K_UP]:
                self.buttons[self.button_choosed].toggle_choose()
                self.button_choosed = (
                    self.button_choosed - 1) % len(self.buttons)
                self.buttons[self.button_choosed].toggle_choose()
            elif event.key in [K_RETURN, K_SPACE]:
                self.buttons[self.button_choosed].clicked()
                self._reset_chosen()
            elif event.key == K_ESCAPE:
                pygame.event.post(pygame.event.Event(EVENT_RESUME))
            else:
                return False

            return True

        return False

    def _reset_chosen(self):
        self.button_choosed = 0
        for each in self.buttons:
            each.toggle_choose(False)
        self.buttons[0].toggle_choose(True)
