import pygame
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
