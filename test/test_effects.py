""" Generated effects: explosions, lost upgrades, smooth supply flight, planets, screen shake """
import random

import pygame
import pytest
from pygame import Vector2

from conftest import run
from src.game.TestMode import TestMode
from src.game.animation import Explosion, Spark, ScreenShake
from src.game.groups import G_Effects, G_Players, G_Supplies
from src.game.supply import SupplyLevel, SupplyLife
from src.game.supply.Supply import SupplyStatus
from src.game.ui.Planets import PlanetLayer, make_planet, TYPES
from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.util.type import Pos


def _mortal(game):
    """ The plane can be destroyed (god mode off), with lives to spare """
    TestMode.god_mode = False
    game.apply_god_mode()
    game.player._life = 50


def _respawn(game):
    for _ in range(300):
        if game.player.is_active:
            return
        run(game, 1)
    raise AssertionError("the plane did not come back")


def test_a_destroyed_ship_explodes_without_dark_frames(round_game):
    from src.game.level.level1 import EnemyScout
    G_Effects.empty()
    scout = EnemyScout(Pos([300, 300]))
    run(round_game, 1)
    scout.hit(scout.MAX_HEALTH * 10)
    explosions = [s for s in G_Effects if isinstance(s, Explosion)]
    assert len(explosions) == 1 and any(isinstance(s, Spark) for s in G_Effects)
    shown = 0
    for _ in range(60):
        run(round_game, 1)
        shown += scout.alive()
    assert shown <= 3 * 6, "removed under the explosion, before its dark silhouette frames"
    assert not any(isinstance(s, Explosion) for s in G_Effects), "the explosion ends"


def test_explosions_are_turned_and_flipped_at_random():
    looks = {id(Explosion((0, 0), "medium").frames[3]) for _ in range(40)}
    G_Effects.empty()
    assert len(looks) >= 5


def test_the_destroyed_plane_hides_under_its_explosion(round_game):
    _mortal(round_game)
    player = round_game.player
    player.set_pos((500, 700))
    run(round_game, 1)
    player.destroy()
    assert any(isinstance(s, Explosion) and s.size == "large" for s in G_Effects)
    run(round_game, 20)
    assert pygame.mask.from_surface(player.image).count() == 0
    _respawn(round_game)
    assert pygame.mask.from_surface(player.image).count() > 0


def _die_with_level(game, level):
    """ Destroy the plane at weapon `level`: the upgrade orbs it dropped """
    G_Supplies.empty()
    while game.player.level < level:
        game.player.level_up()
    game.player.set_pos((500, 700))
    run(game, 1)
    game.player.destroy()
    orbs = [s for s in G_Supplies if isinstance(s, SupplyLevel)]
    _respawn(game)
    return orbs


def test_lost_upgrades_drop_from_the_wreck(round_game):
    _mortal(round_game)
    random.seed(2)
    assert _die_with_level(round_game, 1) == []
    assert len(_die_with_level(round_game, 2)) == 1
    counts = [len(_die_with_level(round_game, 4)) for _ in range(30)]
    assert set(counts) <= {1, 2} and 7 <= counts.count(2) <= 23, "a second orb half of the time"
    G_Supplies.empty()


def test_a_dropped_orb_pops_out_and_can_be_won_back(round_game):
    _mortal(round_game)
    player = round_game.player
    G_Supplies.empty()
    player.level_up()
    player.set_pos((500, 700))
    run(round_game, 1)
    player.destroy()
    orb = [s for s in G_Supplies if isinstance(s, SupplyLevel)][0]
    assert orb.status == SupplyStatus.Pop and orb._velocity.y < -2
    run(round_game, 3)
    assert orb.alive(), "the wreck does not pick it up"
    _respawn(round_game)
    level = player.level
    player.set_pos(orb.rect.center)
    run(round_game, 2)
    assert not orb.alive() and player.level == level + 1


def test_a_supply_flies_along_smooth_curves(round_game, monkeypatch):
    player = round_game.player
    G_Players.remove(player)        # nobody picks it up
    try:
        supply = SupplyLife()
        # Its free flight, without the pull toward a close plane
        monkeypatch.setattr(supply, "_action_magnet", lambda: False)
        turns, speed_changes, path = [], [], []
        previous = None
        for _ in range(supply.MOVE_PHASE_DURATION + 800):
            before = Vector2(supply._pos)
            run(round_game, 1)
            if not supply.alive():
                break
            velocity = Vector2(supply._pos) - before
            path.append(supply._pos.xy)
            if previous is not None and velocity.length() > 0.3 and previous.length() > 0.3:
                turns.append(abs((previous.angle_to(velocity) + 180) % 360 - 180))
                speed_changes.append(abs(velocity.length() - previous.length()))
            previous = velocity
    finally:
        G_Players.add(player)
    assert max(turns) <= supply.TURN_RATE + 0.1, "no sharp turns"
    assert max(speed_changes) <= supply.ACC + 0.01, "no sudden speed changes"
    floating = path[60:supply.MOVE_PHASE_DURATION]
    assert all(0 <= x <= SCREEN_WIDTH and 0 <= y <= SCREEN_HEIGHT for x, y in floating), "stays on screen"
    assert not supply.alive(), "leaves at the bottom after its time"


@pytest.mark.parametrize("kind", TYPES)
def test_every_planet_type_is_drawn_in_small_steps(kind):
    job = make_planet(random.Random(5), kind, radius=30)
    steps = 0
    while True:
        try:
            next(job)
            steps += 1
        except StopIteration as done:
            image = done.value
            break
    assert steps >= 60, "half a row at a time, a little each frame"
    assert image.get_width() >= 62 * 2 and pygame.mask.from_surface(image).count() > 0


def test_planets_drift_by_one_after_another():
    layer = PlanetLayer(random.Random(3))
    shown, visible = 0, False
    for _ in range(9000):
        layer.update()
        shown += layer.visible and not visible
        visible = layer.visible
    assert shown >= 4


def test_screen_shake_fills_the_uncovered_edge(round_game):
    run(round_game, 1)
    try:
        ScreenShake._trauma = 1.0
        ScreenShake.offset = (10, -8)
        round_game._draw_world()
        assert round_game.screen.get_at((3, 500))[:3] == round_game.background.BASE_COLOR
    finally:
        ScreenShake.reset()
