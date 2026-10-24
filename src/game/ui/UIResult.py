import pygame
from pygame.locals import *
from src.helper.image import get_image
from src.helper.font import load_font, get_font, FontEntity
from src.util.type import Pos
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR, IS_WEB
from src.game.custom_events import EVENT_RESTART
from .Button import Button


class UIResult:
    """ Result screen shown at the end of a round (game over or victory) """

    def __init__(self, surface) -> None:
        load_font("arialbd.ttf", 80, "ResultTitle")
        load_font("arialbd.ttf", 30, "ResultText")
        self.surface = surface

        self.title_text = FontEntity(self.surface, get_font("ResultTitle"),
                                     "", color=COLOR.WHITE)
        self.score_text = FontEntity(self.surface, get_font("ResultText"),
                                     "", color=COLOR.WHITE)
        self.best_text = FontEntity(self.surface, get_font("ResultText"),
                                    "", color=COLOR.GRAY)

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

        self.buttons = [self.button_restart]
        # A browser page can not be closed by the game
        if not IS_WEB:
            self.buttons.append(self.button_exit)
        self.button_choosed = 0

    def show(self, is_victory: bool, score: int, best_score: int):
        if is_victory:
            self.title_text.change_text("MISSION COMPLETE")
            self.title_text.change_color(COLOR.WHITE)
        else:
            self.title_text.change_text("GAME OVER")
            self.title_text.change_color(COLOR.RED)
        self.score_text.change_text(f"Score: {score}")
        self.best_text.change_text(f"Best: {best_score}")

        self.title_text.move_center((SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 200))
        self.score_text.move_center((SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 80))
        self.best_text.move_center((SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30))
        self._reset_chosen()

    def blit(self):
        self.title_text.blit()
        self.score_text.blit()
        self.best_text.blit()
        for each in self.buttons:
            each.blit()

    def handle_event(self, event):
        # Use KEYDOWN so releasing a key held during the game (e.g. shoot) does not click a button
        if event.type == pygame.KEYDOWN:
            if event.key in [K_s, K_DOWN, K_w, K_UP]:
                self.buttons[self.button_choosed].toggle_choose()
                self.button_choosed = (
                    self.button_choosed + 1) % len(self.buttons)
                self.buttons[self.button_choosed].toggle_choose()
            elif event.key in [K_RETURN, K_SPACE]:
                self.buttons[self.button_choosed].clicked()
            else:
                return False

            return True

        return False

    def _reset_chosen(self):
        self.button_choosed = 0
        for each in self.buttons:
            each.toggle_choose(False)
        self.buttons[0].toggle_choose(True)
