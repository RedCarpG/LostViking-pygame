import pygame
from pygame.locals import *
from src.helper.font import get_font, render_text
from src.helper.sound import play_sound
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR
from src.game.custom_events import EVENT_CLOSE_SETTINGS
from src.game.GameSettings import GameSettings
from .Button import text_button_frames


class UISettings:
    """ Settings screen: W/S choose a row, A/D (or arrows) change the value,
    Enter toggles or goes back, Esc goes back. Every change is saved right away.
    """

    GLOW = (60, 150, 255)
    IDLE_COLOR = (120, 132, 170)

    ROW_TOP = SCREEN_HEIGHT / 2 - 110
    ROW_SPACING = 64
    LABEL_X = SCREEN_WIDTH / 2 - 250
    VALUE_X = SCREEN_WIDTH / 2 + 50

    BOX_SIZE = 14
    BOX_GAP = 5

    # (label, setting name, kind)
    ROWS = [
        ("MUSIC", "music_volume", "volume"),
        ("SOUND", "sound_volume", "volume"),
        ("SCREEN SHAKE", "screen_shake", "toggle"),
        ("SHOW FPS", "show_fps", "toggle"),
        ("BACK", None, "back"),
    ]

    def __init__(self, surface) -> None:
        self.surface = surface
        font = get_font("MenuText")

        self.title = render_text(get_font("MenuTitle"), "SETTINGS", COLOR.WHITE,
                                 spacing=10, glow_color=self.GLOW, glow_size=10)
        self.title_rect = self.title.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 230))

        # Labels pre-rendered in both states: (idle, chosen)
        self.labels = []
        for label, name, kind in self.ROWS:
            if kind == "back":
                frames = text_button_frames(label)
                self.labels.append((frames["IDLE"], frames["CHOSEN"]))
            else:
                self.labels.append((
                    render_text(font, label, self.IDLE_COLOR, spacing=6),
                    render_text(font, label, COLOR.WHITE, spacing=6, glow_color=self.GLOW, glow_size=8)))
        self.on_off = {
            (value, chosen): render_text(font, "ON" if value else "OFF",
                                         COLOR.WHITE if chosen else self.IDLE_COLOR, spacing=6)
            for value in [True, False] for chosen in [True, False]}

        self.chosen = 0

    def reset(self):
        self.chosen = 0

    # ------------------ Input ------------------

    # ------------------ Layout (shared by drawing and mouse input) ------------------

    def _row_y(self, index):
        return self.ROW_TOP + index * self.ROW_SPACING

    def _volume_width(self):
        return GameSettings.VOLUME_LEVELS * (self.BOX_SIZE + self.BOX_GAP) - self.BOX_GAP

    def _value_width(self, index):
        label, name, kind = self.ROWS[index]
        if kind == "volume":
            return self._volume_width()
        return self.on_off[(getattr(GameSettings, name), True)].get_width()

    def _row_rect(self, index):
        label, name, kind = self.ROWS[index]
        y = self._row_y(index)
        if kind == "back":
            return self.labels[index][0].get_rect(center=(SCREEN_WIDTH / 2, y + 24))
        right = self.VALUE_X + self._volume_width() + 40
        return pygame.Rect(self.LABEL_X - 20, y - self.ROW_SPACING // 2, right - self.LABEL_X + 20, self.ROW_SPACING)

    def _box_rect(self, index, box):
        y = self._row_y(index)
        x = self.VALUE_X + box * (self.BOX_SIZE + self.BOX_GAP)
        # A bit taller than the box so it is easy to click
        return pygame.Rect(x, y - self.BOX_SIZE, self.BOX_SIZE + self.BOX_GAP, self.BOX_SIZE * 2)

    def _arrow_rects(self, index):
        y = self._row_y(index)
        width = self._value_width(index)
        left = pygame.Rect(0, 0, 26, 26)
        left.center = (self.VALUE_X - 26, y)
        right = pygame.Rect(0, 0, 26, 26)
        right.center = (self.VALUE_X + width + 26, y)
        return left, right

    # ------------------ Mouse ------------------

    def _row_at(self, pos):
        for i in range(len(self.ROWS)):
            if self._row_rect(i).collidepoint(pos):
                return i
        return None

    def _click(self, index, pos):
        label, name, kind = self.ROWS[index]
        if kind == "back":
            self._close()
        elif kind == "toggle":
            self._change(name, not getattr(GameSettings, name))
        elif kind == "volume":
            left, right = self._arrow_rects(index)
            level = getattr(GameSettings, name)
            if left.collidepoint(pos):
                level -= 1
            elif right.collidepoint(pos):
                level += 1
            else:
                for box in range(GameSettings.VOLUME_LEVELS):
                    if self._box_rect(index, box).collidepoint(pos):
                        # Clicking the only filled box turns the volume off
                        level = 0 if (box == 0 and level == 1) else box + 1
                        break
            level = max(0, min(GameSettings.VOLUME_LEVELS, level))
            if level != getattr(GameSettings, name):
                self._change(name, level)

    # ------------------ Input ------------------

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            index = self._row_at(event.pos)
            if index is not None:
                self.chosen = index
            return index is not None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self._row_at(event.pos)
            if index is None:
                return False
            self.chosen = index
            self._click(index, event.pos)
            return True
        if event.type != pygame.KEYUP:
            return False
        label, name, kind = self.ROWS[self.chosen]
        if event.key in [K_s, K_DOWN]:
            self.chosen = (self.chosen + 1) % len(self.ROWS)
        elif event.key in [K_w, K_UP]:
            self.chosen = (self.chosen - 1) % len(self.ROWS)
        elif event.key in [K_a, K_LEFT, K_d, K_RIGHT]:
            step = 1 if event.key in [K_d, K_RIGHT] else -1
            if kind == "volume":
                self._change(name, max(0, min(GameSettings.VOLUME_LEVELS,
                                              getattr(GameSettings, name) + step)))
            elif kind == "toggle":
                self._change(name, not getattr(GameSettings, name))
        elif event.key in [K_RETURN, K_SPACE]:
            if kind == "toggle":
                self._change(name, not getattr(GameSettings, name))
            elif kind == "back":
                self._close()
        elif event.key == K_ESCAPE:
            self._close()
        else:
            return False
        return True

    def _change(self, name, value):
        setattr(GameSettings, name, value)
        GameSettings.apply()
        GameSettings.save()
        if name == "sound_volume":
            # Preview the new sound volume
            play_sound("PLAYER_SHOOT")

    def _close(self):
        self.chosen = 0
        pygame.event.post(pygame.event.Event(EVENT_CLOSE_SETTINGS))

    # ------------------ Draw ------------------

    def blit(self):
        self.surface.blit(self.title, self.title_rect)
        for i, (label, name, kind) in enumerate(self.ROWS):
            chosen = i == self.chosen
            y = self.ROW_TOP + i * self.ROW_SPACING
            image = self.labels[i][1 if chosen else 0]
            if kind == "back":
                self.surface.blit(image, image.get_rect(center=(SCREEN_WIDTH / 2, y + 24)))
                continue
            self.surface.blit(image, image.get_rect(midleft=(self.LABEL_X, y)))
            if kind == "volume":
                width = self._blit_volume(getattr(GameSettings, name), y, chosen)
            else:
                value = self.on_off[(getattr(GameSettings, name), chosen)]
                self.surface.blit(value, value.get_rect(midleft=(self.VALUE_X, y)))
                width = value.get_width()
            if chosen:
                self._blit_arrows(y, width)

    def _blit_volume(self, level, y, chosen) -> int:
        color = self.GLOW if chosen else self.IDLE_COLOR
        x = self.VALUE_X
        for i in range(GameSettings.VOLUME_LEVELS):
            box = pygame.Rect(x, y - self.BOX_SIZE // 2, self.BOX_SIZE, self.BOX_SIZE)
            if i < level:
                self.surface.fill(color, box)
            else:
                pygame.draw.rect(self.surface, color, box, 1)
            x += self.BOX_SIZE + self.BOX_GAP
        return x - self.BOX_GAP - self.VALUE_X

    def _blit_arrows(self, y, width):
        left = self.VALUE_X - 22
        right = self.VALUE_X + width + 22
        pygame.draw.polygon(self.surface, self.GLOW, [(left, y - 6), (left - 9, y), (left, y + 6)])
        pygame.draw.polygon(self.surface, self.GLOW, [(right, y - 6), (right + 9, y), (right, y + 6)])
