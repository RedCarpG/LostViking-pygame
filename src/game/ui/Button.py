import pygame
from src.game.animation import AnimeSprite
from src.util.type import Pos, Size
from src.helper.font import get_font, render_text
from pygame.sprite import AbstractGroup


def text_button_frames(text) -> dict:
    """ Create the IDLE / CHOSEN frames of a text menu button (both frames have the same size) """
    font = get_font("MenuText")
    glow = (60, 150, 255)
    chosen_text = render_text(font, text, (255, 255, 255), spacing=6,
                              glow_color=glow, glow_size=8)
    idle_text = render_text(font, text, (120, 132, 170), spacing=6)

    marker_space = 34
    width = chosen_text.get_width() + marker_space * 2
    height = chosen_text.get_height()
    center = (width // 2, height // 2)

    idle = pygame.Surface((width, height), pygame.SRCALPHA)
    idle.blit(idle_text, idle_text.get_rect(center=center))

    chosen = pygame.Surface((width, height), pygame.SRCALPHA)
    chosen.blit(chosen_text, chosen_text.get_rect(center=center))
    # Small arrow markers on both sides of the chosen button
    left, right, y = 12, width - 12, center[1]
    pygame.draw.polygon(chosen, glow, [(left, y - 6), (left + 9, y), (left, y + 6)])
    pygame.draw.polygon(chosen, glow, [(right, y - 6), (right - 9, y), (right, y + 6)])

    return {"IDLE": idle, "CHOSEN": chosen}


class Button:

    def __init__(self, surface, function, frames: dict, *groups: AbstractGroup, **kwargs):
        self.surface = surface
        self.frames = frames
        self.image = frames["IDLE"]
        self.rect = self.image.get_rect()

        if "pos" in kwargs:
            self.rect.move_ip(kwargs["pos"].x, kwargs["pos"].y)
        elif "center" in kwargs:
            self.rect.center = (kwargs["center"].x, kwargs["center"].y)

        self.function = function
        self.is_hidden = False
        self.is_chosen = False

    def toggle_hide(self):
        self.is_hidden = not self.is_hidden

    def clicked(self):
        self.function(self)

    def toggle_choose(self, is_chosen=None):
        if is_chosen is not None:
            self.is_chosen = is_chosen
        else:
            self.is_chosen = not self.is_chosen
        if self.is_chosen:
            self.image = self.frames["CHOSEN"]
        else:
            self.image = self.frames["IDLE"]

    def blit(self):
        self.surface.blit(self.image, self.rect)
