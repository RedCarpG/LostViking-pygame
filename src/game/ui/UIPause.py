import pygame
from pygame.locals import *
from src.helper.image import get_image
from src.helper.font import load_font, get_font, FontEntity
from src.util.type import Pos
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR, IS_WEB
from src.game.custom_events import EVENT_RESUME, EVENT_RESTART
from .Button import Button


class UIPause:

    def __init__(self, surface) -> None:
        load_font("arialbd.ttf", 30, "Pause")
        self.surface = surface

        self.pause_text = FontEntity(self.surface, get_font("Pause"),
                                     ("PAUSE"), color=COLOR.WHITE)
        self.pause_text.move_center((SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 100))

        def resume_game(button):
            pygame.event.post(pygame.event.Event(EVENT_RESUME))

        self.button_resume = Button(
            self.surface,
            function=resume_game,
            frames={
                "IDLE": get_image("UI/Pause/Resume0.png"),
                "CHOSEN": get_image("UI/Pause/Resume1.png")
            },
            center=Pos([SCREEN_WIDTH/2, SCREEN_HEIGHT/2])
        )
        self.button_resume.toggle_choose()

        def restart_game(button):
            pygame.event.post(pygame.event.Event(EVENT_RESTART))
        self.button_restart = Button(
            self.surface,
            function=restart_game,
            frames={
                "IDLE": get_image("UI/Pause/Restart0.png"),
                "CHOSEN": get_image("UI/Pause/Restart1.png")
            },
            center=Pos([SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 100])
        )

        def end_game(button):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.button_exit = Button(
            self.surface,
            function=end_game,
            frames={
                "IDLE": get_image("UI/Pause/Exit0.png"),
                "CHOSEN": get_image("UI/Pause/Exit1.png")
            },
            center=Pos([SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 200])
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
        self.pause_text.blit()

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
