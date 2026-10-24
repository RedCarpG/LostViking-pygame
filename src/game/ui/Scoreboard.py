import pygame
from src.helper.font import get_font, render_text
from src.game.groups import G_Player1


class Scoreboard:

    POS = (24, 16)
    LABEL_COLOR = (130, 145, 185)
    VALUE_COLOR = (255, 255, 255)

    def __init__(self, surface) -> None:

        self.surface = surface
        self.player_g = G_Player1

        self.label = render_text(get_font("ScoreLabel"), "SCORE",
                                 self.LABEL_COLOR, spacing=4, shadow=True)
        self._score = None
        self.value = None
        self.update()

    def update(self):
        score = self.player_g.sprite.score
        if score != self._score:
            self._score = score
            self.value = render_text(get_font("ScoreValue"), f"{score:,}",
                                     self.VALUE_COLOR, spacing=2, shadow=True)

    def blit(self):
        self.surface.blit(self.label, self.POS)
        self.surface.blit(self.value, (self.POS[0], self.POS[1] + self.label.get_height() - 6))
