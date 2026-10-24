import pygame
from pygame import Vector2

from conftest import run
from src.game.groups import G_Supplies, G_Texts
from src.game.supply import SupplyLife, SupplyBomb, SupplyLevel, SUPPLY_TYPE, get_supply_type, drop_supply_event
from src.game.supply import supply_event
from src.util.type import Pos


def test_each_supply_has_its_own_type():
    assert get_supply_type(SUPPLY_TYPE.Life) is SupplyLife
    assert get_supply_type(SUPPLY_TYPE.Bomb) is SupplyBomb
    assert get_supply_type(SUPPLY_TYPE.Level) is SupplyLevel
    assert {cls.TYPE for cls in (SupplyLife, SupplyBomb, SupplyLevel)} == set(SUPPLY_TYPE.get_types())


def test_labels_say_what_the_supply_gave(round_game):
    player = round_game.player
    far = Pos([100, 100])
    assert SupplyBomb(far).apply(player)[0] == "+1 BOMB"
    while player.add_bomb():
        pass
    assert SupplyBomb(far).apply(player)[0] == "BOMBS MAX"
    assert SupplyLevel(far).apply(player)[0] == "WEAPON LV 2"
    assert SupplyLife(far).apply(player)[0] == "+1 LIFE"
    player._health = 10
    assert SupplyLife(far).apply(player)[0] == "REPAIRED"
    while player.add_life():
        pass
    assert SupplyLife(far).apply(player)[0] == "LIVES MAX"


def test_pickup_gives_points_and_a_label(round_game):
    player = round_game.player
    SupplyBomb(Pos(player.rect.center))
    run(round_game, 1)
    assert len(G_Supplies) == 0
    assert player.bomb_count == player.BOMB_COUNT_DEFAULT + 1
    assert player.score == SupplyBomb.SCORE
    assert len(G_Texts) == 1


def test_supply_is_drawn_to_a_close_player(round_game):
    player = round_game.player
    x, y = player.rect.center
    supply = SupplyLevel(Pos([x + 80, y - 40]))
    start = Vector2(supply.rect.center).distance_to(player.rect.center)
    run(round_game, 4)
    # Pulled in, faster as it gets closer
    assert Vector2(supply.rect.center).distance_to(player.rect.center) < start - 8
    run(round_game, 12)
    assert not supply.alive()


def test_supply_blinks_before_it_leaves(round_game):
    supply = SupplyBomb(Pos([500, 300]))
    supply._count_status_duration = 100
    sizes = set()
    for _ in range(2 * SupplyBomb.BLINK_PERIOD):
        run(round_game, 1)
        sizes.add(supply.image.get_size())
    assert (1, 1) in sizes and len(sizes) == 2
    # Collisions keep the real size while hidden
    assert supply.rect.width > 1


def test_drop_cooldown_counts_game_frames(round_game):
    G_Supplies.empty()
    supply_event.supply_event_config()
    drop_supply_event(Pos([500, 300]), SUPPLY_TYPE.Level)
    run(round_game, 1)
    assert len(G_Supplies) == 1
    # Within the cooldown: no second drop
    drop_supply_event(Pos([300, 300]), SUPPLY_TYPE.Level)
    run(round_game, 1)
    assert len(G_Supplies) == 1
    # The time on the pause menu does not count
    round_game.pause()
    run(round_game, supply_event.DROP_COOLDOWN + 5)
    round_game.resume()
    drop_supply_event(Pos([300, 300]), SUPPLY_TYPE.Level)
    run(round_game, 1)
    assert len(G_Supplies) == 1
    for each in G_Supplies.sprites():
        each.kill()
    run(round_game, supply_event.DROP_COOLDOWN)
    drop_supply_event(Pos([300, 300]), SUPPLY_TYPE.Level)
    run(round_game, 1)
    assert len(G_Supplies) == 1
    pygame.event.clear()
