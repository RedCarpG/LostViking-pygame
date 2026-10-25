import random
import pygame
from pygame.locals import *
from src.helper.font import load_font, get_font, render_text
from src.setting import SCREEN_WIDTH
from src.util.type import Pos
from src.game.groups import G_BOSS
from src.game.TestMode import TestMode


class TestPanel:
    """ Test mode tools: spawn enemies, change the player and the level.
    Every entry has a hotkey and can also be clicked, ` (backquote) shows or hides the panel.
    """

    WIDTH = 286
    LEFT = SCREEN_WIDTH - WIDTH - 14
    TOP = 66
    ROW_HEIGHT = 25
    PADDING = 12

    BACK_COLOR = (6, 9, 22, 240)
    BORDER_COLOR = (60, 150, 255, 150)
    HOVER_COLOR = (60, 150, 255, 70)
    TITLE_COLOR = (90, 175, 255)
    HEADER_COLOR = (130, 145, 185)
    TEXT_COLOR = (225, 232, 255)
    ON_COLOR = (90, 220, 140)
    OFF_COLOR = (120, 132, 170)

    def __init__(self, surface, game) -> None:
        load_font("Silkscreen-Regular.ttf", 16, "Panel")
        load_font("Silkscreen-Bold.ttf", 8, "PanelKey")
        load_font("Silkscreen-Regular.ttf", 8, "PanelHint")
        self.surface = surface
        self.game = game
        self.visible = True

        # Each row: (key, key label, text function, action), a header row has no key
        self.rows = []
        self._build_rows()
        self._text_cache = {}
        self._layout()
        self._rendered_key = None
        self._panel = None

        self.tag = render_text(get_font("PanelKey"), "TEST MODE  -  PRESS ` TO SHOW THE PANEL",
                               self.TITLE_COLOR, spacing=1, shadow=True)

    def _build_rows(self):
        # Imported here: the level modules are only needed once the game is running
        from src.game.level.level1 import EnemyScout, EnemyPhoenix, EnemyInterceptor, EnemyOracle, \
            Asteroid, OutpostPlatform
        from src.game.supply import get_supply_type
        game = self.game

        def header(text):
            self.rows.append((None, None, lambda: (text, None), None))

        def entry(key, key_label, text, action):
            self.rows.append((key, key_label, text, action))

        def spawn_interceptor():
            x = random.randint(150, SCREEN_WIDTH - 150)
            EnemyInterceptor(Pos([x, -30]), [[x, 260]])

        def spawn_stargate():
            if G_BOSS.sprite is None:
                game.level.clear_enemies()
                game.level.go_to("stargate")

        def boss_damage():
            boss = G_BOSS.sprite
            if boss is not None and boss.is_active:
                boss.hit(boss.MAX_HEALTH // 4)

        def boss_value():
            boss = G_BOSS.sprite
            return f"{max(0, boss.health) * 100 // boss.MAX_HEALTH}%" if boss is not None else "-"

        def toggle_god_mode():
            TestMode.god_mode = not TestMode.god_mode
            game.apply_god_mode()

        def toggle_auto_spawn():
            game.level.auto_spawn = not game.level.auto_spawn

        def toggle_hitboxes():
            TestMode.show_hitboxes = not TestMode.show_hitboxes

        header("SPAWN")
        entry(K_1, "1", lambda: ("Scout wave", None), lambda: EnemyScout.spawn_wave())
        entry(K_2, "2", lambda: ("Phoenix", None),
              lambda: EnemyPhoenix.add_enemy_phoenix(side=random.choice(["left", "right"])))
        entry(K_3, "3", lambda: ("Interceptor", None), spawn_interceptor)
        entry(K_o, "O", lambda: ("Oracle", None), lambda: EnemyOracle.warp_in())
        entry(K_r, "R", lambda: ("Asteroid", None), lambda: Asteroid.spawn())
        entry(K_t, "T", lambda: ("Outpost", None), lambda: OutpostPlatform.spawn())
        entry(K_4, "4", lambda: ("Stargate (boss)", None), spawn_stargate)
        entry(K_c, "C", lambda: ("Carrier (boss)", None), lambda: game.level.spawn_carrier())
        header("PLAYER")
        entry(K_5, "5", lambda: ("Weapon level +1", f"Lv {game.player.level}"),
              lambda: game.player.level_up())
        entry(K_6, "6", lambda: ("Bomb +1", str(game.player.bomb_count)),
              lambda: game.player.add_bomb())
        entry(K_7, "7", lambda: ("Heal, life +1", f"{game.player.life} lives"),
              lambda: (game.player.add_health(), game.player.add_life()))
        entry(K_g, "G", lambda: ("God mode", TestMode.god_mode), toggle_god_mode)
        header("LEVEL")
        entry(K_8, "8", lambda: ("Drop supply", None),
              lambda: get_supply_type()(Pos([random.randint(200, SCREEN_WIDTH - 200), 300])))
        entry(K_9, "9", lambda: ("Boss -25% HP", boss_value()), boss_damage)
        entry(K_0, "0", lambda: ("Clear enemies", None), lambda: game.level.clear_enemies())
        entry(K_j, "J", lambda: ("Next stage", game.level.stage), lambda: game.level.next_stage())
        entry(K_n, "N", lambda: ("Auto spawn", game.level.auto_spawn), toggle_auto_spawn)
        entry(K_h, "H", lambda: ("Hitboxes", TestMode.show_hitboxes), toggle_hitboxes)
        entry(K_BACKQUOTE, "`", lambda: ("Hide panel", None), self.toggle_visible)

    def toggle_visible(self):
        self.visible = not self.visible

    # ------------------ Input ------------------

    def handle_event(self, event) -> bool:
        if event.type == KEYDOWN:
            for key, key_label, text, action in self.rows:
                if key is not None and event.key == key:
                    action()
                    return True
        elif event.type == MOUSEBUTTONDOWN and event.button == 1 and self.visible:
            for rect, action in self._row_rects:
                if rect.collidepoint(event.pos):
                    action()
                    return True
        return False

    # ------------------ Draw ------------------

    def _text(self, font_name, text, color):
        key = (font_name, text, color)
        if key not in self._text_cache:
            self._text_cache[key] = get_font(font_name).render(text, False, color)
        return self._text_cache[key]

    TITLE_HEIGHT = 30
    HINT_HEIGHT = 26

    def _layout(self):
        """ Screen rect of every clickable row (the layout never changes) """
        self._row_rects = []
        y = self.PADDING + self.TITLE_HEIGHT
        for key, key_label, text, action in self.rows:
            if key is not None:
                self._row_rects.append(
                    (pygame.Rect(self.LEFT, self.TOP + y, self.WIDTH, self.ROW_HEIGHT), action))
            y += self.ROW_HEIGHT

    def blit(self, target=None, offset=(0, 0)):
        """ Draw the panel on `target` (default: the screen). `offset` is subtracted from
        its position, so it stays still on screen when the world is shaking.
        The panel image is only rendered again when a value or the hovered row changes.
        """
        target = target or self.surface
        ox, oy = offset
        if not self.visible:
            target.blit(self.tag, self.tag.get_rect(topright=(SCREEN_WIDTH - 10 - ox, 62 - oy)))
            return

        texts = tuple(text() for key, key_label, text, action in self.rows)
        mouse = pygame.mouse.get_pos()
        hover = next((i for i, (rect, action) in enumerate(self._row_rects) if rect.collidepoint(mouse)), None)
        if (texts, hover) != self._rendered_key:
            self._rendered_key = (texts, hover)
            self._panel = self._render(texts, hover)
        target.blit(self._panel, (self.LEFT - ox, self.TOP - oy))

    def _render(self, texts, hover):
        height = self.PADDING * 2 + self.TITLE_HEIGHT + len(self.rows) * self.ROW_HEIGHT + self.HINT_HEIGHT
        panel = pygame.Surface((self.WIDTH, height), pygame.SRCALPHA)
        panel.fill(self.BACK_COLOR)
        pygame.draw.rect(panel, self.BORDER_COLOR, panel.get_rect(), 1)

        panel.blit(self._text("MenuText", "TEST PANEL", self.TITLE_COLOR), (self.PADDING, self.PADDING - 4))
        y = self.PADDING + self.TITLE_HEIGHT
        entry = 0
        for (key, key_label, text, action), (label, value) in zip(self.rows, texts):
            middle = y + self.ROW_HEIGHT // 2
            if key is None:
                header = self._text("PanelKey", label, self.HEADER_COLOR)
                panel.blit(header, header.get_rect(midleft=(self.PADDING, middle + 2)))
            else:
                if entry == hover:
                    panel.fill(self.HOVER_COLOR, (1, y, self.WIDTH - 2, self.ROW_HEIGHT))
                entry += 1
                # Key badge
                badge = pygame.Rect(self.PADDING, middle - 9, 22, 18)
                pygame.draw.rect(panel, self.HEADER_COLOR, badge, 1, border_radius=3)
                key_text = self._text("PanelKey", key_label, self.TEXT_COLOR)
                panel.blit(key_text, key_text.get_rect(center=badge.center))
                label_text = self._text("Panel", label, self.TEXT_COLOR)
                panel.blit(label_text, label_text.get_rect(midleft=(self.PADDING + 32, middle)))
                if value is not None:
                    if isinstance(value, bool):
                        value_text = self._text("PanelKey", "ON" if value else "OFF",
                                                self.ON_COLOR if value else self.OFF_COLOR)
                    else:
                        value_text = self._text("Panel", value, self.OFF_COLOR)
                    panel.blit(value_text, value_text.get_rect(midright=(self.WIDTH - self.PADDING, middle)))
            y += self.ROW_HEIGHT

        hint = self._text("PanelHint", "Press the key or click a row", self.HEADER_COLOR)
        panel.blit(hint, hint.get_rect(midleft=(self.PADDING, y + self.HINT_HEIGHT // 2 + 2)))
        return panel
