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
        # Both titles made now: the glow takes a while to draw, the round has just ended
        self._titles = {
            is_victory: render_text(get_font("MenuTitle"), title, COLOR.WHITE, spacing=1, glow_color=glow)
            for is_victory, title, glow in ((True, "MISSION COMPLETE", self.VICTORY_GLOW),
                                            (False, "GAME OVER", self.GAME_OVER_GLOW))}
        self.score_label = render_text(get_font("ScoreLabel"), "SCORE",
                                       self.LABEL_COLOR, spacing=0)
        self.score_text = None
        self.stats_text = None
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

    def show(self, is_victory: bool, score: int, best_score: int, new_best=False, seconds=0, kills=0):
        """ :param new_best: the score beat the saved best score
        :param seconds: length of the round, kills: enemies destroyed by the player
        """
        self.title = "MISSION COMPLETE" if is_victory else "GAME OVER"
        self.title_text = self._titles[is_victory]
        self.score_text = render_text(get_font("ResultScore"), f"{score:,}",
                                      COLOR.WHITE, spacing=0)
        minutes, seconds = divmod(seconds, 60)
        self.stats_text = render_text(get_font("ScoreLabel"), f"TIME {minutes}:{seconds:02}      KILLS {kills}",
                                      self.LABEL_COLOR, spacing=0)
        if new_best:
            self.best_text = render_text(get_font("MenuText"), "NEW BEST!",
                                         self.VICTORY_GLOW, spacing=0, glow_color=(120, 70, 10))
        else:
            self.best_text = render_text(get_font("MenuText"), f"BEST  {best_score:,}",
                                         self.LABEL_COLOR, spacing=0)
        self.menu.reset()

    def blit(self):
        center_x = SCREEN_WIDTH / 2
        self.surface.blit(self.title_text, self.title_text.get_rect(
            center=(center_x, SCREEN_HEIGHT / 2 - 230)))
        self.surface.blit(self.score_label, self.score_label.get_rect(
            center=(center_x, SCREEN_HEIGHT / 2 - 140)))
        self.surface.blit(self.score_text, self.score_text.get_rect(
            center=(center_x, SCREEN_HEIGHT / 2 - 100)))
        self.surface.blit(self.stats_text, self.stats_text.get_rect(
            center=(center_x, SCREEN_HEIGHT / 2 - 52)))
        self.surface.blit(self.best_text, self.best_text.get_rect(
            center=(center_x, SCREEN_HEIGHT / 2 - 10)))
        self.menu.blit()

    def handle_event(self, event):
        return self.menu.handle_event(event)
