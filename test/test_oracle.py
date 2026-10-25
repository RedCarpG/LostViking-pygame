import pygame

from conftest import run
from src.game.groups import G_Enemys, G_Player_Bullets
from src.game.level.level1 import EnemyOracle
from src.game.level.level1.Oracle import PulsarBeam, StasisWard, StasisShell, WarpIn
from src.game.player.player_control import PLAYER1_CONTROL as C
from src.game.TestMode import TestMode
from src.util.type import Pos


def _vulnerable(game):
    TestMode.god_mode = False
    game.apply_god_mode()
    return game.player


def _oracle_above_player(game):
    """ An Oracle ready to fire its beam right above the plane """
    player = game.player
    # Where it goes to fire (see EnemyOracle._decide)
    oracle = EnemyOracle(Pos([player.rect.centerx, min(560, player.rect.centery - PulsarBeam.LENGTH + 40)]))
    oracle._count_ward = 10 ** 6
    oracle._count_beam = 0
    oracle._count_hold = 0
    return oracle


def test_warp_in_brings_the_oracle_after_the_effect(round_game):
    EnemyOracle.warp_in((500, 250))
    assert len(EnemyOracle.GROUP) == 0 and len(WarpIn.GROUP) == 1
    run(round_game, WarpIn.DURATION - 2)
    assert len(EnemyOracle.GROUP) == 0
    run(round_game, 3)
    assert len(EnemyOracle.GROUP) == 1 and len(WarpIn.GROUP) == 0
    assert EnemyOracle.ARMORED


def test_pulsar_beam_charges_then_burns(round_game):
    player = _vulnerable(round_game)
    oracle = _oracle_above_player(round_game)
    run(round_game, 3)
    beam = oracle.beam
    assert beam is not None and beam.phase == PulsarBeam.CHARGE
    run(round_game, PulsarBeam.CHARGE_FRAMES - 5)
    # The charge only shows where the beam will be
    assert player.health == player.MAX_HEALTH
    run(round_game, 30)
    assert beam.phase == PulsarBeam.FIRE
    assert player.health < player.MAX_HEALTH
    # Done after its time, the Oracle waits before the next one
    run(round_game, PulsarBeam.FIRE_FRAMES + 20)
    assert not beam.alive() and oracle.beam is None and oracle._count_beam > 0


def test_the_beam_follows_the_plane_slowly(round_game):
    player = round_game.player
    oracle = _oracle_above_player(round_game)
    run(round_game, PulsarBeam.CHARGE_FRAMES + 10)
    x = oracle.rect.centerx
    player.rect.centerx += 200
    run(round_game, 20)
    moved = oracle.rect.centerx - x
    assert 0 < moved <= EnemyOracle.BEAM_SWEEP * 20 + 2


def _armed_ward_on(player):
    ward = StasisWard(Pos(player.rect.center))
    ward._speed.update(0, 0)
    ward._age = StasisWard.ARM_FRAMES
    return ward


def test_a_ward_does_nothing_while_arming(round_game):
    player = _vulnerable(round_game)
    ward = StasisWard(Pos(player.rect.center))
    ward._speed.update(0, 0)
    run(round_game, 5)
    assert not player.in_stasis and ward.alive()


def test_an_armed_ward_freezes_the_plane(round_game, keys):
    player = _vulnerable(round_game)
    ward = _armed_ward_on(player)
    run(round_game, 1)
    assert player.in_stasis and not ward.alive()
    assert player.score == 0
    from src.game.groups import G_Effects
    assert any(isinstance(each, StasisShell) for each in G_Effects)
    # Frozen: does not move, does not shoot, is not hurt
    pos = player.rect.center
    keys.down = {C.MOVE_LEFT[0], C.SHOOT[0]}
    run(round_game, 20)
    assert player.rect.center == pos and len(G_Player_Bullets) == 0
    assert player.hit(100) is False and player.health == player.MAX_HEALTH
    # Free again
    run(round_game, StasisWard.STASIS_FRAMES)
    assert not player.in_stasis
    run(round_game, 10)
    assert player.rect.centerx < pos[0] and len(G_Player_Bullets) > 0


def test_wards_can_be_shot_down(round_game, keys):
    player = round_game.player
    ward = StasisWard(Pos([player.rect.centerx - 10, player.rect.centery - 300]))
    ward._speed.update(0, 0)
    keys.down = {C.SHOOT[0]}
    run(round_game, 40)
    assert not ward.is_active
    assert player.score == StasisWard.SCORE and player.kills == 1


def test_an_invincible_plane_passes_through_wards(round_game):
    player = round_game.player
    assert player.is_invincible
    _armed_ward_on(player)
    run(round_game, 3)
    assert not player.in_stasis


def test_the_oracle_drops_wards_in_front_of_the_plane(round_game):
    player = round_game.player
    oracle = EnemyOracle(Pos([300, 200]))
    oracle._count_beam = 10 ** 6
    oracle._count_ward = 0
    oracle._count_hold = 0
    run(round_game, 150)
    wards = list(StasisWard.GROUP)
    assert len(wards) == 1
    assert wards[0].rect.centery < player.rect.centery


def test_the_patrol_brings_an_oracle(round_game):
    level = round_game.level
    level.auto_spawn = True
    level._enter_stage(level.STAGE_NAMES.index("patrol"))
    level._stage_time = level.PATROL_ORACLE - 1
    run(round_game, 2)
    assert len(WarpIn.GROUP) == 1
    run(round_game, WarpIn.DURATION + 2)
    assert len(EnemyOracle.GROUP) == 1
    level.auto_spawn = False
    for each in G_Enemys.sprites():
        each.kill()
    pygame.event.clear()


def test_the_oracle_leaves_after_its_stay(round_game):
    oracle = EnemyOracle(Pos([500, 200]))
    oracle._count_beam = oracle._count_ward = 10 ** 6
    oracle._time = EnemyOracle.STAY
    run(round_game, 200)
    assert not oracle.alive()
