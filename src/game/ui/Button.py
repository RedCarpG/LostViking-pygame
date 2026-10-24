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


class Menu:
    """ Vertical list of text buttons, chosen with W/S or the arrow keys and
    confirmed with Enter or Space
    """

    def __init__(self, surface, items: list, center_x, top, spacing=60, key_event=pygame.KEYUP):
        """
        :param items: list of (label, function) for each button, the function is called when clicked
        :param key_event: pygame.KEYUP or pygame.KEYDOWN, the key event that controls the menu
        """
        self.key_event = key_event
        self.buttons = []
        for i, (label, function) in enumerate(items):
            self.buttons.append(Button(
                surface,
                function=lambda button, function=function: function(),
                frames=text_button_frames(label),
                center=Pos([center_x, top + i * spacing])
            ))
        self.chosen = 0
        self.reset()

    def reset(self):
        self.chosen = 0
        for each in self.buttons:
            each.toggle_choose(False)
        self.buttons[0].toggle_choose(True)

    def _choose(self, index):
        self.buttons[self.chosen].toggle_choose(False)
        self.chosen = index
        self.buttons[self.chosen].toggle_choose(True)

    def _button_at(self, pos):
        for i, each in enumerate(self.buttons):
            if each.rect.collidepoint(pos):
                return i
        return None

    def handle_event(self, event) -> bool:
        # Mouse: hovering chooses a button, a left click activates it
        if event.type == pygame.MOUSEMOTION:
            index = self._button_at(event.pos)
            if index is not None and index != self.chosen:
                self._choose(index)
            return index is not None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self._button_at(event.pos)
            if index is None:
                return False
            self._choose(index)
            self.buttons[index].clicked()
            return True
        if event.type != self.key_event:
            return False
        if event.key in [pygame.K_s, pygame.K_DOWN, pygame.K_w, pygame.K_UP]:
            step = 1 if event.key in [pygame.K_s, pygame.K_DOWN] else -1
            self._choose((self.chosen + step) % len(self.buttons))
        elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
            self.buttons[self.chosen].clicked()
        else:
            return False
        return True

    def blit(self):
        for each in self.buttons:
            each.blit()
