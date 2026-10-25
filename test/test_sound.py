""" Sounds that come in bursts (hits, explosions) do not pile up """
import pygame
import pytest

from src.helper.sound import sound_loader
from src.helper.sound.sound_loader import play_sound, SOUND_GROUPS


class FakeSound:
    """ Counts its starts; `playing` copies are heard at a time """

    def __init__(self):
        self.starts = 0
        self.stops = 0
        self.playing = 0

    def play(self):
        self.starts += 1
        self.playing += 1

    def stop(self):
        self.stops += 1
        self.playing = 0

    def get_num_channels(self):
        return self.playing


@pytest.fixture
def sounds(monkeypatch):
    """ Fake sounds for every label of the groups (and one other), and a clock to set """
    clock = {"now": 10000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: clock["now"])
    monkeypatch.setattr(sound_loader, "_last_start", {})
    fakes = {}
    for labels, _, _ in SOUND_GROUPS.values():
        for label in labels:
            fakes[label] = FakeSound()
    fakes["PLAYER_SHOOT"] = FakeSound()
    for label, fake in fakes.items():
        monkeypatch.setitem(sound_loader._SOUND.BUFFER, label, fake)
    return fakes, clock


def test_many_hits_in_one_frame_start_one_sound(sounds):
    fakes, clock = sounds
    for _ in range(10):
        play_sound("ENEMY_HIT")
    assert fakes["ENEMY_HIT"].starts == 1


def test_hits_play_again_after_a_short_while_without_cutting_the_last_one(sounds):
    fakes, clock = sounds
    labels, limit, interval = SOUND_GROUPS["hit"]
    play_sound("ENEMY_HIT")
    clock["now"] += interval
    play_sound("ENEMY_HIT")
    assert fakes["ENEMY_HIT"].starts == 2 and fakes["ENEMY_HIT"].stops == 0
    # The group limit: no third copy while two are heard
    clock["now"] += interval
    play_sound("SHIELD")
    assert fakes["SHIELD"].starts == 0
    fakes["ENEMY_HIT"].playing = 0
    play_sound("SHIELD")
    assert fakes["SHIELD"].starts == 1


def test_a_nuke_does_not_play_every_explosion(sounds):
    fakes, clock = sounds
    labels, limit, interval = SOUND_GROUPS["destroy"]
    for frame in range(10):
        for label in labels:
            play_sound(label)
        clock["now"] += 16
    started = sum(fakes[label].starts for label in labels)
    assert started <= limit


def test_other_sounds_restart_as_before(sounds):
    fakes, clock = sounds
    play_sound("PLAYER_SHOOT")
    play_sound("PLAYER_SHOOT")
    assert fakes["PLAYER_SHOOT"].starts == 2 and fakes["PLAYER_SHOOT"].stops == 2
