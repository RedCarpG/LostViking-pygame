""" Headless test setup: no window, no sound card, settings saved in a temporary file

Run from the project root:  python -m pytest
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import pytest


class Keys:
    """ Stands for pygame.key.get_pressed(): the keys in `down` are held """

    def __init__(self):
        self.down = set()

    def __getitem__(self, key):
        return key in self.down


@pytest.fixture(scope="session")
def game(tmp_path_factory):
    """ One game for the whole session (loading every asset takes a while) """
    import src.game.GameSettings as settings_module
    settings_module._FILE = tmp_path_factory.mktemp("settings") / "settings.json"

    pygame.init()
    pygame.mixer.init()
    pygame.font.init()
    from src.game.Game import Game
    from src.game.animation import warmup
    game = Game()
    warmup.finish()
    yield game
    pygame.quit()


@pytest.fixture
def keys(monkeypatch):
    keys = Keys()
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: keys)
    return keys


@pytest.fixture
def round_game(game, keys):
    """ A fresh test mode round: nothing spawns on its own, the player can not be hit """
    from src.game.Game import GameState
    if game.state != GameState.INTRO:
        game.to_main_menu()
    game.start_round(test_mode=True)
    game.level.auto_spawn = False
    pygame.event.clear()
    return game


def run(game, frames):
    for _ in range(frames):
        game.step(draw=False)
