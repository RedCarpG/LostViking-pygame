import pygame
from src.helper.font import load_font, get_font, render_text
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR, IS_WEB
from src.game.custom_events import EVENT_RESTART, EVENT_MAIN_MENU
from .Button import Menu
from .UIPause import post_event


class UIResult:
    """ Result screen shown at the end of a round (game over or victory) """

    LABEL_COLOR = (130, 145, 185)
    VICTORY_GLOW = (255, 180, 50)
    GAME_OVER_GLOW = (255, 40, 40)

    def __init__(self, surface) -> None:
        load_font("Silkscreen-Bold.ttf", 48, "ResultScore")
        self.surface = surface

        self.title = ""
        self.title_text = None
        self.score_label = render_text(get_font("ScoreLabel"), "SCORE",
                                       self.LABEL_COLOR, spacing=0)
        self.score_text = None
        self.best_text = None

        items = [
            ("RESTART", post_event(EVENT_RESTART)),
            ("MAIN MENU", post_event(EVENT_MAIN_MENU)),
        ]
        # A browser page can not be closed by the game
        if not IS_WEB:
            items.append(("EXIT", post_event(pygame.QUIT)))
        # Use KEYDOWN so releasing a key held during the game (e.g. shoot) does not click a button
        self.menu = Menu(self.surface, items, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 70,
                         key_event=pygame.KEYDOWN)

    def show(self, is_victory: bool, score: int, best_score: int):
        if is_victory:
            self.title = "MISSION COMPLETE"
            glow_color = self.VICTORY_GLOW
        else:
            self.title = "GAME OVER"
            glow_color = self.GAME_OVER_GLOW
        self.title_text = render_text(get_font("MenuTitle"), self.title, COLOR.WHITE,
                                      spacing=1, glow_color=glow_color)
        self.score_text = render_text(get_font("ResultScore"), f"{score:,}",
                                      COLOR.WHITE, spacing=0)
        if score > 0 and score >= best_score:
            self.best_text = render_text(get_font("MenuText"), "NEW BEST!",
                                         self.VICTORY_GLOW, spacing=0)
        else:
            self.best_text = render_text(get_font("MenuText"), f"BEST  {best_score:,}",
                                         self.LABEL_COLOR, spacing=0)
        self.menu.reset()

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
        self.menu.blit()

    def handle_event(self, event):
        return self.menu.handle_event(event)
