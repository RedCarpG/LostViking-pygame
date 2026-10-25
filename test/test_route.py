""" The route of level 1: stages, the Terran Starport, asteroids, outposts, the Stargate """
import pygame
from pygame import Vector2

from conftest import run
from src.game.Game import GameState
from src.game.groups import G_BOSS, G_Enemys, G_Enemy_Bullets, G_Player_Bullets, G_Scenery
from src.game.level.level1 import Asteroid, AsteroidLarge, AsteroidMedium, AsteroidSmall, OutpostPlatform, \
    PhotonCannon, Pylon, EnemyStargate, EnemyCarrier, EnemyScout, TerranStarport
from src.game.level.level1.Outpost import BulletPhoton
from src.game.level.level1.WarpIn import WarpIn
from src.game.animation import ScreenFX
from src.game.player.player_control import PLAYER1_CONTROL as C
from src.game.TestMode import TestMode
from src.util.type import Pos


def _vulnerable(game):
    TestMode.god_mode = False
    game.apply_god_mode()
    return game.player


def _clear(game):
    for sprite in G_Enemys.sprites() + G_Enemy_Bullets.sprites() + G_Scenery.sprites():
        sprite.kill()
    game.level.auto_spawn = False
    pygame.event.clear()


# --------------- Stages --------------- #
def test_the_route_goes_through_its_stages(round_game):
    level = round_game.level
    assert level.stage == "launch" and level.route_progress == 0
    level.auto_spawn = True
    run(round_game, level.STAGES[0][1])
    assert level.stage == "asteroids"
    # Each stage of the route shows its name
    assert ScreenFX._title is not None and ScreenFX._title.images
    assert 0 < level.route_progress < 0.1
    level.go_to("outposts")
    assert level.stage == "outposts" and len(OutpostPlatform.GROUP) == 0
    run(round_game, max(frame for frame, layouts in level.OUTPOSTS[:1]) + 1)
    assert len(OutpostPlatform.GROUP) == 1
    level.go_to("stargate")
    assert level.route_progress == 1 and isinstance(G_BOSS.sprite, EnemyStargate)
    assert ScreenFX._banner is not None
    _clear(round_game)


def test_the_route_marks_start_at_the_starport(round_game):
    marks = round_game.level.route_marks()
    assert marks[0] == 0 and marks == sorted(marks) and len(marks) == 4
    round_game.step()   # draws the route on the left edge


def test_the_plane_takes_off_from_the_terran_starport(round_game):
    starport = next(each for each in G_Scenery if isinstance(each, TerranStarport))
    pad = (starport.rect.left + starport.PAD[0], starport.rect.top + starport.PAD[1])
    assert Vector2(pad).distance_to(round_game.player.rect.center) < 2
    run(round_game, TerranStarport.HOLD - 2)
    assert starport.rect.left + starport.PAD[0] == pad[0] and starport.rect.top + starport.PAD[1] == pad[1]
    run(round_game, 200)
    assert not starport.alive()


# --------------- Asteroids --------------- #
def test_asteroids_break_into_smaller_rocks(round_game, keys):
    _clear(round_game)
    rock = AsteroidLarge(Pos([500, 300]), Vector2(0, 0))
    assert rock.ARMORED and not AsteroidSmall.ARMORED
    rock.hit(rock.MAX_HEALTH)
    pieces = list(Asteroid.GROUP)
    assert not rock.alive() and [type(each) for each in pieces] == [AsteroidMedium, AsteroidMedium]
    # They fly apart
    assert pieces[0]._speed.x < 0 < pieces[1]._speed.x
    pieces[0].hit(AsteroidMedium.MAX_HEALTH)
    assert sorted(type(each).__name__ for each in Asteroid.GROUP) == ["AsteroidMedium", "AsteroidSmall",
                                                                      "AsteroidSmall"]
    small = next(each for each in Asteroid.GROUP if isinstance(each, AsteroidSmall))
    small.hit(AsteroidSmall.MAX_HEALTH)
    assert not small.alive() and len(Asteroid.GROUP) == 2
    _clear(round_game)


def test_shooting_a_rock_scores(round_game, keys):
    _clear(round_game)
    player = round_game.player
    AsteroidSmall(Pos([player.rect.centerx, player.rect.top - 200]), Vector2(0, 0))
    keys.down = {C.SHOOT[0]}
    run(round_game, 60)
    assert player.kills == 1 and player.score == AsteroidSmall.SCORE
    _clear(round_game)


def test_flying_into_a_rock_hurts_and_breaks_it(round_game):
    _clear(round_game)
    player = _vulnerable(round_game)
    rock = AsteroidMedium(Pos(list(player.rect.center)), Vector2(0, 0))
    run(round_game, 1)
    assert player.health == player.MAX_HEALTH - AsteroidMedium.COLLIDE_DAMAGE
    assert not rock.alive()
    _clear(round_game)


def test_rocks_stop_enemy_shots(round_game):
    from src.game.level.level1.Scout import BulletScout
    _clear(round_game)
    player = _vulnerable(round_game)
    x = player.rect.centerx
    rock = AsteroidLarge(Pos([x, player.rect.top - 160]), Vector2(0, 0))
    BulletScout(Pos([x, player.rect.top - 320]))
    run(round_game, 100)
    # The plane hides behind the rock: the shot stopped there and chipped it
    assert player.health == player.MAX_HEALTH
    assert rock.health == AsteroidLarge.MAX_HEALTH - BulletScout.DAMAGE
    assert not any(isinstance(each, BulletScout) for each in G_Enemy_Bullets)
    _clear(round_game)


def test_enemy_fire_breaks_rocks_for_no_points(round_game):
    from src.game.level.level1.Scout import BulletScout
    _clear(round_game)
    player = round_game.player
    rock = AsteroidSmall(Pos([300, 400]), Vector2(0, 0))
    for i in range(4):
        BulletScout(Pos([300, 300 - i * 40]))
    run(round_game, 120)
    assert not rock.alive() and not rock.is_active
    assert player.score == 0 and player.kills == 0
    _clear(round_game)


def test_rocks_spin(round_game):
    _clear(round_game)
    rock = AsteroidSmall(Pos([500, 300]), Vector2(0, 0))
    frames = set()
    for _ in range(60):
        run(round_game, 1)
        frames.add(rock._current_frame_index)
    assert len(frames) > 3
    _clear(round_game)


# --------------- Outposts --------------- #
def _outpost(game, layout="large", y=200):
    _clear(game)
    platform = OutpostPlatform(layout, 500)
    platform._y = float(y)
    platform.rect.top = y
    run(game, 1)
    return platform


def test_structures_ride_their_platform(round_game):
    platform = _outpost(round_game)
    cannons = [each for each in platform.structures if isinstance(each, PhotonCannon)]
    pylon = next(each for each in platform.structures if isinstance(each, Pylon))
    assert len(cannons) == 2 and pylon.cannons == cannons
    offsets = [(each.rect.centerx - platform.rect.left, each.rect.centery - platform.rect.top)
               for each in platform.structures]
    run(round_game, 50)
    assert platform.rect.top > 200
    assert offsets == [(each.rect.centerx - platform.rect.left, each.rect.centery - platform.rect.top)
                       for each in platform.structures]
    # They go away with it
    platform.kill()
    run(round_game, 1)
    assert not any(each.alive() for each in platform.structures)


def test_cannons_fire_at_the_plane(round_game):
    platform = _outpost(round_game)
    cannon = platform.structures[0]
    cannon._count_attack_interval = 0
    run(round_game, 40)
    shots = [each for each in G_Enemy_Bullets if isinstance(each, BulletPhoton)]
    assert shots
    to_player = Vector2(round_game.player.rect.center) - Vector2(cannon.rect.center)
    assert shots[0].speed.angle_to(to_player) % 360 < 8 or shots[0].speed.angle_to(to_player) % 360 > 352
    _clear(round_game)


def test_a_destroyed_pylon_cuts_the_cannons(round_game):
    platform = _outpost(round_game)
    pylon = next(each for each in platform.structures if isinstance(each, Pylon))
    pylon.hit(Pylon.MAX_HEALTH)
    assert not platform.powered
    for cannon in pylon.cannons:
        assert not cannon.powered
        cannon._count_attack_interval = 0
    run(round_game, 200)
    assert not any(isinstance(each, BulletPhoton) for each in G_Enemy_Bullets)
    _clear(round_game)


def test_destroying_an_outpost_gives_a_bonus(round_game):
    platform = _outpost(round_game, "left")
    player = round_game.player
    for each in platform.structures:
        each.hit(each.MAX_HEALTH)
        player.credit_kill(each)
    # (the pylon's hit stop freezes the world for a moment)
    run(round_game, 10)
    assert player.score == sum(each.SCORE for each in platform.structures) + OutpostPlatform.BONUS
    _clear(round_game)


def test_the_plane_flies_over_structures(round_game):
    platform = _outpost(round_game)
    player = _vulnerable(round_game)
    cannon = platform.structures[0]
    cannon._count_attack_interval = 10 ** 6
    player.rect.center = cannon.rect.center
    player._count_attack_interval = 0
    # A Scout over the same spot still rams the plane
    run(round_game, 1)
    assert player.health == player.MAX_HEALTH and cannon.is_active
    scout = EnemyScout(Pos(list(player.rect.center)))
    scout._count_attack_interval = 10 ** 6
    run(round_game, 1)
    assert player.health == player.MAX_HEALTH - EnemyScout.COLLIDE_DAMAGE
    _clear(round_game)


# --------------- Stargate --------------- #
def _stargate(game):
    _clear(game)
    game.level.go_to("stargate")
    gate = G_BOSS.sprite
    gate._count_attack_interval = 10 ** 6
    run(game, 900)
    return gate


def test_the_stargate_comes_in_and_stays(round_game):
    gate = _stargate(round_game)
    top = gate.rect.top
    assert abs(top - gate.STOP_TOP) <= 2
    assert gate.GROUND and len(gate.cannons) == 2
    run(round_game, 60)
    assert gate.rect.top == top
    _clear(round_game)


def test_the_stargate_warps_out_scouts(round_game):
    gate = _stargate(round_game)
    gate._attack_scouts()
    run(round_game, 60)
    # They come out of the portal
    warps = list(WarpIn.GROUP)
    assert len(warps) == 2 and all(abs(each.rect.centerx - gate.portal.x) < 60 for each in warps)
    run(round_game, gate.SCOUT_WARP + 2)
    assert len(EnemyScout.GROUP) == 2
    _clear(round_game)


def test_the_stargate_warps_out_the_carrier_before_it_falls(round_game):
    gate = _stargate(round_game)
    level = round_game.level
    player = round_game.player
    gate.hit(gate.MAX_HEALTH)
    # Its health is gone, but it stands while the Carrier comes through
    assert gate.warping and gate.is_active and player.score == gate.SCORE
    gate.hit(1000)
    assert gate.health == 0 and gate.is_active
    run(round_game, gate.WARP_OUT - 5)
    assert G_BOSS.sprite is gate and level.stage == "stargate"
    run(round_game, 10)
    carrier = G_BOSS.sprite
    assert isinstance(carrier, EnemyCarrier) and level.stage == "carrier"
    assert carrier.rect.center == EnemyCarrier.warp_center()
    assert not gate.is_active and gate.dying and not any(each.is_active for each in gate.cannons)
    # The boss bar now shows the Carrier
    run(round_game, 1)
    assert round_game.ui.ui_boss.health_bar.max_health == EnemyCarrier.MAX_HEALTH
    # Destroying the Carrier wins the level (its shield already broken)
    carrier.shield = 0
    carrier.hit(carrier.MAX_HEALTH)
    for _ in range(carrier.DEATH_DURATION + 200 + round_game.END_DELAY):
        run(round_game, 1)
        if round_game.state != GameState.PLAYING:
            break
    assert round_game.state == GameState.VICTORY
    G_Enemy_Bullets.empty()


def test_the_bomb_hits_structures(round_game):
    platform = _outpost(round_game)
    from src.game.player.player_event_handler import _handle_player_bomb_explode_event
    _handle_player_bomb_explode_event(round_game.player)
    assert all(each.health == each.MAX_HEALTH - 1000 or not each.is_active for each in platform.structures)
    G_Player_Bullets.empty()
    _clear(round_game)


def test_shots_reach_the_stargate_cannons(round_game):
    from pygame import Vector2
    from src.game.player.PlayerViking import PlayerBulletViking
    gate = _stargate(round_game)
    for cannon in gate.cannons:
        health = cannon.health
        bullet = PlayerBulletViking(Pos(list(cannon.rect.center)), Vector2(0, -17), 80, player=round_game.player)
        bullet.collide_enemy(G_Enemys)
        assert cannon.health < health and gate.health == gate.MAX_HEALTH, "the cannon is hit, not the gate"
    bullet = PlayerBulletViking(Pos(list(gate.portal)), Vector2(0, -17), 80, player=round_game.player)
    bullet.collide_enemy(G_Enemys)
    assert gate.health < gate.MAX_HEALTH, "the portal is still the gate's"
    _clear(round_game)
