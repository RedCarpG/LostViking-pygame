import pygame
from pygame import Vector2
from pygame.locals import KEYUP

from conftest import run
from src.game.groups import G_Player_Bullets, G_Texts, G_Enemys
from src.game.player.player_control import PLAYER1_CONTROL as C
from src.game.animation import HitStop
from src.util.type import Pos


def test_weapon_has_five_levels(round_game):
    player = round_game.player
    weapon = player.weapon
    assert weapon.LEVEL_MAX == 5
    assert [player.level_up() for _ in range(5)] == [True, True, True, True, False]
    assert player.level == 5


def test_weapon_patterns_by_level(round_game):
    player = round_game.player
    counts = {}
    for level in range(1, 6):
        G_Player_Bullets.empty()
        player.weapon.shoot(pos=Pos(player.pos))
        counts[level] = (len(G_Player_Bullets), player.weapon.fire_interval)
        player.level_up()
    assert counts == {1: (2, 20), 2: (4, 20), 3: (6, 20), 4: (6, 16), 5: (8, 16)}


def test_shooting_shows_muzzle_flashes(round_game, keys):
    from src.game.animation.MuzzleFlash import MuzzleFlash
    from src.game.groups import G_Effects
    keys.down = {C.SHOOT[0]}
    run(round_game, 3)
    assert any(isinstance(each, MuzzleFlash) for each in G_Effects)


def test_arrow_keys_move_the_plane(round_game, keys):
    player = round_game.player
    x = player.rect.centerx
    keys.down = {pygame.K_LEFT}
    run(round_game, 10)
    assert player.rect.centerx < x


def test_releasing_one_of_two_held_keys_keeps_moving(round_game, keys):
    player = round_game.player
    keys.down = {pygame.K_a, pygame.K_LEFT}
    run(round_game, 10)
    # A is released, the left arrow is still held
    keys.down = {pygame.K_LEFT}
    pygame.event.post(pygame.event.Event(KEYUP, key=pygame.K_a, mod=0, unicode="", scancode=0))
    run(round_game, 1)
    assert player._is_moving_x
    keys.down = set()
    pygame.event.post(pygame.event.Event(KEYUP, key=pygame.K_LEFT, mod=0, unicode="", scancode=0))
    run(round_game, 1)
    assert not player._is_moving_x


def test_kill_gives_points_and_a_floating_text(round_game):
    from src.game.level.level1 import EnemyScout
    player = round_game.player
    scout = EnemyScout(Pos([500, 300]))
    scout.hit(10 ** 6)
    player.credit_kill(scout)
    assert player.score == scout.score
    assert player.kills == 1
    assert len(G_Texts) == 1


def test_bomb_without_bombs_says_so(round_game):
    player = round_game.player
    while player.bomb_count:
        player.dec_bomb()
    pygame.event.post(pygame.event.Event(KEYUP, key=C.BOMB[0], mod=0, unicode="", scancode=0))
    run(round_game, 2)
    texts = list(G_Texts)
    assert len(texts) == 1


def test_nuke_clears_the_screen_with_a_hit_stop(round_game):
    from src.game.level.level1 import EnemyScout
    from src.game.groups import G_Bomb
    for i in range(4):
        EnemyScout(Pos([200 + i * 150, 200]))
    pygame.event.post(pygame.event.Event(KEYUP, key=C.BOMB[0], mod=0, unicode="", scancode=0))
    run(round_game, 2)
    assert G_Bomb.sprite is not None
    frozen = False
    for _ in range(120):
        run(round_game, 1)
        frozen = frozen or HitStop._frames > 0
        if not any(each.is_active for each in G_Enemys):
            break
    assert not any(each.is_active for each in G_Enemys)
    assert frozen
    assert round_game.player.kills == 4


def test_hit_stop_freezes_the_world_but_not_the_keys(round_game, keys):
    from src.game.level.level1 import EnemyScout
    player = round_game.player
    scout = EnemyScout(Pos([300, 200]))
    keys.down = {pygame.K_RIGHT}
    run(round_game, 10)
    HitStop.add(5)
    y = scout.rect.centery
    keys.down = set()
    pygame.event.post(pygame.event.Event(KEYUP, key=pygame.K_RIGHT, mod=0, unicode="", scancode=0))
    run(round_game, 3)
    assert scout.rect.centery == y
    assert not player._is_moving_x
    run(round_game, 5)
    assert scout.rect.centery > y


def test_scout_ram_hurts_instead_of_destroying(round_game):
    from src.game.level.level1 import EnemyScout
    from src.game.TestMode import TestMode
    player = round_game.player
    TestMode.god_mode = False
    round_game.apply_god_mode()
    lives = player.life
    EnemyScout(Pos(player.rect.center))
    run(round_game, 1)
    assert player.life == lives
    assert player.health == player.MAX_HEALTH - 50


def _switch(game):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=C.SWITCH[0], mod=0, unicode="e", scancode=0))
    run(game, 1)


def test_e_switches_weapons_and_transforming_blocks_shots(round_game, keys):
    from src.game.player import PlayerTorpedoViking, PlayerWeaponViking
    player = round_game.player
    assert isinstance(player.weapon, PlayerWeaponViking)
    _switch(round_game)
    assert isinstance(player.weapon, PlayerTorpedoViking) and player.transforming
    # No shot while transforming, then torpedoes
    keys.down = {C.SHOOT[0]}
    run(round_game, player.TRANSFORM_FRAMES - 3)
    assert len(G_Player_Bullets) == 0
    run(round_game, 4)
    assert len(G_Player_Bullets) == 2
    # Switching again is refused until the transform is over, then goes back
    keys.down = set()
    run(round_game, player.TRANSFORM_FRAMES)
    _switch(round_game)
    assert isinstance(player.weapon, PlayerWeaponViking)


def test_weapons_share_the_level(round_game):
    player = round_game.player
    player.level_up()
    player.level_up()
    assert [each.level for each in player.weapons] == [3, 3]
    player.reset_level()
    assert [each.level for each in player.weapons] == [1, 1]


def test_torpedo_salvo_by_level(round_game):
    from src.game.player import PlayerTorpedoViking
    player = round_game.player
    weapon = next(each for each in player.weapons if isinstance(each, PlayerTorpedoViking))
    counts = []
    for level in range(1, 6):
        G_Player_Bullets.empty()
        weapon.shoot(Pos(player.pos))
        counts.append(len(G_Player_Bullets))
        player.level_up()
    assert counts == [2, 2, 4, 4, 6]


def test_torpedoes_home_onto_an_enemy_off_to_the_side(round_game):
    from src.game.level.level1 import EnemyScout
    from src.game.player import PlayerTorpedoViking
    player = round_game.player
    # Far to the side and above: straight shots would miss it
    scout = EnemyScout(Pos([player.rect.centerx + 350, 250]))
    scout._speed.update(0, 0)
    scout._count_attack_interval = 10 ** 6
    weapon = next(each for each in player.weapons if isinstance(each, PlayerTorpedoViking))
    weapon.shoot(Pos(player.pos))
    for _ in range(120):
        scout._speed.update(0, 0)
        run(round_game, 1)
        if not scout.is_active:
            break
    assert not scout.is_active
    assert player.kills == 1


def test_torpedoes_hurt_armored_ships_more(round_game):
    from src.game.level.level1 import EnemyScout, EnemyInterceptor
    from src.game.player.LanzerTorpedo import LanzerTorpedo
    torpedo = LanzerTorpedo(round_game.player.rect.center, Vector2(0, 0), 5, 100, round_game.player)
    assert EnemyScout.ARMORED and not EnemyInterceptor.ARMORED
    scout = EnemyScout(Pos([100, 100]))
    interceptor = EnemyInterceptor(Pos([300, 100]), [[300, 200]])
    assert torpedo.damage_to(scout) == 100 + LanzerTorpedo.ARMOR_BONUS
    assert torpedo.damage_to(interceptor) == 100


def _gatling_shot(player, x, y, level):
    from src.game.player import PlayerBulletViking, PlayerWeaponViking
    weapon = next(each for each in player.weapons if isinstance(each, PlayerWeaponViking))
    return PlayerBulletViking(Pos([x, y]), Vector2(0, -17), 100, player=player,
                              pierce=weapon.PIERCE[level - 1])


def _sitting_scouts(xs_ys):
    from src.game.level.level1 import EnemyScout
    scouts = []
    for x, y in xs_ys:
        scout = EnemyScout(Pos([x, y]))
        scout._speed.update(0, 0)
        scout._count_attack_interval = 10 ** 6
        scouts.append(scout)
    return scouts


def test_gatling_pierces_from_level_4(round_game):
    from src.game.player import PlayerWeaponViking
    assert PlayerWeaponViking.PIERCE == (0, 0, 0, 1, 2)
    player = round_game.player
    scouts = _sitting_scouts([(300, 500), (300, 380), (300, 260), (300, 140)])
    bullet = _gatling_shot(player, 300, 640, level=5)
    for _ in range(40):
        for each in scouts:
            each._speed.update(0, 0)
        run(round_game, 1)
    damaged = [each.MAX_HEALTH - each.health for each in scouts]
    # Through two Scouts, stopped by the third, each hit 30% weaker; the fourth untouched
    assert damaged == [100, 70, 49, 0]
    assert not bullet.alive()


def test_level_1_shots_stop_at_the_first_enemy(round_game):
    player = round_game.player
    scouts = _sitting_scouts([(600, 500), (600, 380)])
    _gatling_shot(player, 600, 640, level=1)
    run(round_game, 20)
    assert [each.MAX_HEALTH - each.health for each in scouts] == [100, 0]


def test_a_shield_stops_a_piercing_shot(round_game):
    from src.game.level.level1 import EnemyPhoenix
    player = round_game.player
    phoenix = EnemyPhoenix(Pos([450, 300]), is_left=True)
    phoenix.enter_action_stay_phase()
    phoenix.set_pos(Pos([450, 300]))
    phoenix._count_attack_interval = 10 ** 6
    phoenix._count_graviton = 10 ** 6
    behind = _sitting_scouts([(450, 120)])[0]
    bullet = _gatling_shot(player, 450, 600, level=5)
    run(round_game, 30)
    assert phoenix.shield == phoenix.MAX_SHIELD - 100
    assert behind.health == behind.MAX_HEALTH
    assert not bullet.alive()
