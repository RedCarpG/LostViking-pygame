""" The main loop runs the game logic 60 times per second of real time, whatever the frame rate """
import asyncio

import pygame


def _run_with_fake_clock(game, monkeypatch, slow_frames, loops=300):
    """ Run the main loop for `loops` frames. Each takes 1000/60 ms, except `slow_frames`
    ({loop index: duration in ms}). :return: (updates, drawn frames, elapsed ms)
    """
    clock = {"now": 0.0, "loop": 0}
    stats = {"updates": 0, "draws": 0}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: int(clock["now"]))

    def counting_step(draw=True):
        stats["updates"] += 1
        stats["draws"] += draw

    class FakeClock:
        def tick(self, fps):
            clock["now"] += slow_frames.get(clock["loop"], 1000 / 60)
            clock["loop"] += 1
            if clock["loop"] >= loops:
                game.running = False

    monkeypatch.setattr(game, "step", counting_step)
    monkeypatch.setattr(game, "clock", FakeClock())
    monkeypatch.setattr(game, "running", True)
    asyncio.run(game.run())
    return stats["updates"], stats["draws"], clock["now"]


def test_one_update_per_frame_at_60_fps(game, monkeypatch):
    updates, draws, _ = _run_with_fake_clock(game, monkeypatch, {})
    assert updates == draws == 300


def test_slow_frames_are_caught_up_and_a_freeze_is_skipped(game, monkeypatch):
    # Two 50 ms frames, a 120 ms frame and a one second freeze (a hidden browser tab)
    updates, draws, elapsed = _run_with_fake_clock(game, monkeypatch, {50: 50, 51: 50, 120: 120, 200: 1000})
    assert draws == 300, "one drawn frame per loop"
    assert updates > draws, "the missed updates run without drawing"
    # After the freeze only MAX_UPDATES run, the rest of the time runs at 60 updates per second
    expected = (elapsed - 1000) / game.UPDATE_MS + game.MAX_UPDATES
    assert abs(updates - expected) <= 3
