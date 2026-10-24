import random

import pygame

from conftest import run
from src.game.Game import GameState
from src.game.GameSettings import GameSettings
from src.game.groups import G_Enemys, G_Enemy_Bullets, G_Effects, G_Texts, G_Supplies, G_Player_Bullets
from src.game.player.player_control import PLAYER1_CONTROL as C


def _play(game, keys, frames, rng):
    """ A simple bot: shoots all the time and wanders left and right """
    for frame in range(frames):
        if game.state != GameState.PLAYING:
            return frame
        if frame % 30 == 0:
            keys.down = {C.SHOOT[0], rng.choice((C.MOVE_LEFT[0], C.MOVE_RIGHT[0], C.MOVE_UP[0], C.MOVE_DOWN[0]))}
        game.step(draw=frame % 4 == 0)
    return frames


def test_normal_round_runs(game, keys):
    """ A normal round (enemies spawn, the player can be destroyed) for a while, drawing too """
    if game.state != GameState.INTRO:
        game.to_main_menu()
    game.start_round(test_mode=False)
    game.level.SPAWN_SPEED_CARRIER = 1500
    try:
        _play(game, keys, 2400, random.Random(3))
    finally:
        del game.level.SPAWN_SPEED_CARRIER
    assert game.state in (GameState.PLAYING, GameState.GAME_OVER)


def test_restart_starts_clean(round_game, keys):
    from src.game.level.level1 import EnemyScout
    from src.util.type import Pos
    for i in range(3):
        EnemyScout(Pos([200 + i * 200, 200]))
    keys.down = {C.SHOOT[0]}
    run(round_game, 30)
    round_game.restart()
    for group in (G_Enemys, G_Enemy_Bullets, G_Effects, G_Texts, G_Supplies, G_Player_Bullets):
        assert len(group) == 0
    assert round_game.player.score == 0 and round_game.player.kills == 0


def test_pause_draws_the_frozen_game_once(round_game, monkeypatch):
    run(round_game, 5)
    round_game.pause()
    calls = []
    original = round_game._draw_world
    monkeypatch.setattr(round_game, "_draw_world", lambda: (calls.append(1), original()))
    for _ in range(5):
        round_game.step()
    assert len(calls) == 1
    round_game.resume()
    round_game.step()
    assert len(calls) == 2


def test_result_saves_the_best_score(round_game):
    from src.game.TestMode import TestMode
    TestMode.enabled = False
    GameSettings.best_score = 100
    round_game.player.add_score(5000)
    round_game._show_result(GameState.GAME_OVER)
    assert GameSettings.best_score == 5000
    best = GameSettings.best_score
    GameSettings.best_score = 0
    GameSettings.load()
    assert GameSettings.best_score == best


def test_test_mode_scores_do_not_count(round_game):
    GameSettings.best_score = 100
    round_game.player.add_score(5000)
    round_game._show_result(GameState.GAME_OVER)
    assert GameSettings.best_score == 100


def test_p_pauses_and_resumes(round_game):
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_p, mod=0, unicode="", scancode=0))
    round_game.step(draw=False)
    assert round_game.state == GameState.PAUSED
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_p, mod=0, unicode="", scancode=0))
    round_game.step(draw=False)
    round_game.step(draw=False)
    assert round_game.state == GameState.PLAYING


def test_settings_survive_a_restart_of_the_game():
    GameSettings.screen_flash = False
    GameSettings.music_volume = 3
    GameSettings.save()
    GameSettings.screen_flash = True
    GameSettings.music_volume = 5
    GameSettings.load()
    assert GameSettings.screen_flash is False and GameSettings.music_volume == 3
    GameSettings.screen_flash = True
    GameSettings.music_volume = GameSettings.DEFAULT_VOLUME
    GameSettings.save()
