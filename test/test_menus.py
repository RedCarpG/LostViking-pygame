""" Menus with the keyboard and the mouse, the settings screen, and the music when the window
loses focus
"""
import json
import sys

import pygame
import pytest
from pygame.locals import (KEYUP, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP, K_DOWN, K_UP, K_LEFT, K_RIGHT,
                           K_RETURN, K_ESCAPE, WINDOWFOCUSLOST, WINDOWFOCUSGAINED, WINDOWMINIMIZED, WINDOWRESTORED)

from conftest import run
from src.game.Game import GameState
from src.game.GameSettings import GameSettings

music = pygame.mixer.music


def keyup(game, *keys):
    for key in keys:
        pygame.event.post(pygame.event.Event(KEYUP, key=key))
    run(game, 2)


def post(game, event_type, **attributes):
    pygame.event.post(pygame.event.Event(event_type, **attributes))
    run(game, 2)


def move(game, pos):
    post(game, MOUSEMOTION, pos=pos, rel=(1, 1), buttons=(0, 0, 0))


def click(game, pos):
    move(game, pos)
    pygame.event.post(pygame.event.Event(MOUSEBUTTONDOWN, pos=pos, button=1))
    post(game, MOUSEBUTTONUP, pos=pos, button=1)


@pytest.fixture
def menu_game(game):
    """ The main menu; the settings are put back after the test """
    saved = {name: getattr(GameSettings, name) for name in GameSettings._SAVED}
    game.to_main_menu()
    pygame.event.clear()
    run(game, 2)
    yield game
    for name, value in saved.items():
        setattr(GameSettings, name, value)
    GameSettings.apply()
    GameSettings.save()
    game.to_main_menu()


def test_settings_with_the_keyboard(menu_game):
    game = menu_game
    GameSettings.music_volume = GameSettings.sound_volume = 5
    GameSettings.screen_shake, GameSettings.show_fps = True, False
    keyup(game, K_DOWN, K_RETURN)
    assert game.state == GameState.SETTINGS
    keyup(game, K_RIGHT)
    assert GameSettings.music_volume == 6
    keyup(game, K_DOWN, K_LEFT, K_LEFT, K_LEFT)
    assert GameSettings.sound_volume == 2
    keyup(game, K_DOWN, K_RETURN)
    assert GameSettings.screen_shake is False
    keyup(game, K_DOWN, K_DOWN, K_RIGHT)
    assert GameSettings.show_fps is True
    saved = json.loads(sys.modules["src.game.GameSettings"]._FILE.read_text())
    assert (saved["music_volume"], saved["sound_volume"], saved["screen_shake"], saved["show_fps"]) == (6, 2, False, True)
    keyup(game, K_ESCAPE)
    assert game.state == GameState.INTRO


def test_main_menu_and_settings_with_the_mouse(menu_game):
    game = menu_game
    menu = game.ui_intro.menu
    move(game, menu.buttons[2].rect.center)
    assert menu.chosen == 2, "hovering chooses a button"
    move(game, (30, 30))
    assert menu.chosen == 2, "moving off the buttons keeps the choice"
    keyup(game, K_UP)
    assert menu.chosen == 1, "the keyboard still works after the mouse"
    click(game, menu.buttons[1].rect.center)
    assert game.state == GameState.SETTINGS

    ui = game.ui_settings
    click(game, ui._box_rect(0, 7).center)
    assert GameSettings.music_volume == 8
    left, right = ui._arrow_rects(0)
    click(game, left.center)
    assert GameSettings.music_volume == 7
    for _ in range(5):
        click(game, right.center)
    assert GameSettings.music_volume == GameSettings.VOLUME_LEVELS
    click(game, ui._box_rect(1, 0).center)
    click(game, ui._box_rect(1, 0).center)
    assert GameSettings.sound_volume == 0, "clicking the first box twice mutes"
    shake = GameSettings.screen_shake
    click(game, ui._row_rect(2).center)
    assert GameSettings.screen_shake == (not shake)
    click(game, ui._row_rect(len(ui.ROWS) - 1).center)
    assert game.state == GameState.INTRO, "BACK"


def test_pause_menu_with_the_mouse(menu_game):
    game = menu_game
    click(game, game.ui_intro.menu.buttons[0].rect.center)
    assert game.state == GameState.PLAYING
    pause = game.ui_pause.menu
    keyup(game, K_ESCAPE)
    click(game, pause.buttons[0].rect.center)
    assert game.state == GameState.PLAYING, "RESUME"
    keyup(game, K_ESCAPE)
    click(game, pause.buttons[2].rect.center)
    assert game.state == GameState.SETTINGS
    click(game, game.ui_settings._row_rect(len(game.ui_settings.ROWS) - 1).center)
    assert game.state == GameState.PAUSED, "BACK returns to the pause menu"
    click(game, pause.buttons[3].rect.center)
    assert game.state == GameState.INTRO, "MAIN MENU"


def test_no_music_while_the_window_is_in_the_background(menu_game):
    game = menu_game
    assert music.get_busy()
    post(game, WINDOWFOCUSLOST)
    assert not music.get_busy()
    post(game, WINDOWFOCUSGAINED)
    assert music.get_busy()
    post(game, WINDOWMINIMIZED)
    assert not music.get_busy()
    post(game, WINDOWRESTORED)
    assert music.get_busy()

    keyup(game, K_RETURN)
    assert game.state == GameState.PLAYING and music.get_busy()
    post(game, WINDOWFOCUSLOST)
    assert game.state == GameState.PAUSED and not music.get_busy(), "a round pauses"
    post(game, WINDOWFOCUSGAINED)
    assert game.state == GameState.PAUSED and not music.get_busy(), "and stays paused and silent"
    keyup(game, K_ESCAPE)
    assert game.state == GameState.PLAYING and music.get_busy(), "until RESUME"


def test_start_waits_for_the_warm_up_without_freezing(menu_game):
    from src.game.animation import warmup
    game = menu_game

    def slow_job():
        import time
        for _ in range(30):
            time.sleep(0.005)
            yield
    warmup.add(slow_job())
    keyup(game, K_RETURN)
    assert game.state == GameState.INTRO and game.ui_intro.loading, "LOADING while images are made"
    for _ in range(60):
        if game.state == GameState.PLAYING:
            break
        run(game, 1)
    assert game.state == GameState.PLAYING and warmup.pending() == 0 and not game.ui_intro.loading
