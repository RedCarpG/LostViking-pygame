import pygame
from pygame.locals import *
from src.helper.font import load_font, get_font, render_text
from src.util.type import Pos
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR, IS_WEB
from src.game.custom_events import EVENT_RESTART
from .Button import Button, text_button_frames


class UIResult:
    """ Result screen shown at the end of a round (game over or victory) """

    LABEL_COLOR = (130, 145, 185)
    VICTORY_GLOW = (255, 180, 50)
    GAME_OVER_GLOW = (255, 40, 40)

    def __init__(self, surface) -> None:
        load_font("arialbd.ttf", 48, "ResultScore")
        self.surface = surface

        self.title = ""
        self.title_text = None
        self.score_label = render_text(get_font("ScoreLabel"), "SCORE",
                                       self.LABEL_COLOR, spacing=4)
        self.score_text = None
        self.best_text = None

        def restart_game(button):
            pygame.event.post(pygame.event.Event(EVENT_RESTART))
        self.button_restart = Button(
            self.surface,
            function=restart_game,
            frames=text_button_frames("RESTART"),
            center=Pos([SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 70])
        )

        def end_game(button):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.button_exit = Button(
            self.surface,
            function=end_game,
            frames=text_button_frames("EXIT"),
            center=Pos([SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 140])
        )

        self.buttons = [self.button_restart]
        # A browser page can not be closed by the game
        if not IS_WEB:
            self.buttons.append(self.button_exit)
        self.button_choosed = 0

    def show(self, is_victory: bool, score: int, best_score: int):
        if is_victory:
            self.title = "MISSION COMPLETE"
            glow_color = self.VICTORY_GLOW
        else:
            self.title = "GAME OVER"
            glow_color = self.GAME_OVER_GLOW
        self.title_text = render_text(get_font("MenuTitle"), self.title, COLOR.WHITE,
                                      spacing=8, glow_color=glow_color, glow_size=12)
        self.score_text = render_text(get_font("ResultScore"), f"{score:,}",
                                      COLOR.WHITE, spacing=2)
        if score > 0 and score >= best_score:
            self.best_text = render_text(get_font("MenuText"), "NEW BEST!",
                                         self.VICTORY_GLOW, spacing=4)
        else:
            self.best_text = render_text(get_font("MenuText"), f"BEST  {best_score:,}",
                                         self.LABEL_COLOR, spacing=4)
        self._reset_chosen()

    def blit(self):
        center_x = SCREEN_WIDTH / 2
        self.surface.blit(self.title_text, self.title_text.get_rect(
            center=(center_x, SCREEN_HEIGHT / 2 - 210)))
        self.surface.blit(self.score_label, self.score_label.get_rect(
            center=(center_x, SCREEN_HEIGHT / 2 - 120)))
        self.surface.blit(self.score_text, self.score_text.get_rect(
            center=(center_x, SCREEN_HEIGHT / 2 - 80)))
        self.surface.blit(self.best_text, self.best_text.get_rect(
            center=(center_x, SCREEN_HEIGHT / 2 - 25)))
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
