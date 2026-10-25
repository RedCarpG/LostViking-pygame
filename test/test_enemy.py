from pygame import Vector2

from conftest import run
from src.game.groups import G_Effects, G_Enemy_Bullets
from src.game.animation import AttachEffect
from src.util.type import Pos


def test_bolt_flies_the_way_it_was_aimed(round_game):
    from src.game.level.level1.Carrier import BulletCarrierBolt
    for velocity in (Vector2(3, 8), Vector2(-5, 2), Vector2(0, 9), Vector2(4, -6)):
        bolt = BulletCarrierBolt(Vector2(500, 300), velocity)
        assert (bolt.speed - velocity).length() < 1e-6


def test_aimed_bullet_turns_image_and_speed(round_game):
    from src.game.level.level1.Interceptor import BulletInterceptor
    bullet = BulletInterceptor(Pos([500, 300]), 90)
    assert round(bullet.speed.x, 6) == BulletInterceptor.SPEED and round(bullet.speed.y, 6) == 0
    # The rotated images are cached
    again = BulletInterceptor(Pos([500, 300]), 90)
    assert again.image is bullet.image


def test_bullet_hit_leaves_a_spark(round_game):
    from src.game.level.level1.Scout import BulletScout
    bullet = BulletScout(Pos([500, 300]))
    effects = len(G_Effects)
    bullet.hit()
    assert not bullet.alive()
    assert len(G_Effects) == effects + 1


def test_repeated_hits_reuse_one_hit_overlay(round_game):
    from src.game.level.level1 import EnemyScout
    scout = EnemyScout(Pos([500, 200]))
    for _ in range(4):
        scout.hit(10)
    overlays = [each for each in G_Effects if isinstance(each, AttachEffect) and each.ref is scout
                and each.frames["IDLE"] is scout.frames["HIT"]]
    assert len(overlays) == 1


def test_phoenix_shield_takes_the_hits_first(round_game):
    from src.game.level.level1 import EnemyPhoenix
    phoenix = EnemyPhoenix(Pos([500, 200]), is_left=True)
    phoenix.hit(100, hit_pos=(500, 260))
    assert phoenix.shield == phoenix.MAX_SHIELD - 100
    assert phoenix.health == phoenix.MAX_HEALTH
    phoenix.hit(phoenix.MAX_SHIELD)
    assert phoenix.shield == 0
    phoenix.hit(100)
    assert phoenix.health == phoenix.MAX_HEALTH - 100


def test_boss_arrival_and_enrage(round_game):
    from src.game.groups import G_BOSS
    from src.game.animation import ScreenFX
    round_game.level.spawn_carrier()
    boss = G_BOSS.sprite
    assert boss is not None
    assert ScreenFX._banner is not None
    assert round_game.level._count_boss_music > 0
    run(round_game, 200)
    assert round_game.level._count_boss_music == 0
    boss.shield = 0     # already broken: the hits reach the hull
    boss.hit(boss.MAX_HEALTH // 2 + 1)
    run(round_game, 1)
    assert boss.enraged and boss._enrage_shown
    assert round_game.ui.ui_boss.health_bar.fill_color != round_game.ui.ui_boss.BAR_COLOR


def test_boss_death_ends_the_round_in_victory(round_game):
    from src.game.groups import G_BOSS
    from src.game.Game import GameState
    round_game.level.spawn_carrier()
    run(round_game, 100)
    boss = G_BOSS.sprite
    boss.shield = 0     # already broken: the hits reach the hull
    boss.hit(boss.MAX_HEALTH)
    for _ in range(boss.DEATH_DURATION + 200 + round_game.END_DELAY):
        run(round_game, 1)
        if round_game.state != GameState.PLAYING:
            break
    assert round_game.state == GameState.VICTORY
    G_Enemy_Bullets.empty()


def _phoenix_above_player(game, attack=False):
    """ A Phoenix staying right above the plane, which can be hit (no god mode) """
    from src.game.level.level1 import EnemyPhoenix
    from src.game.TestMode import TestMode
    TestMode.god_mode = False
    game.apply_god_mode()
    x = game.player.rect.centerx
    phoenix = EnemyPhoenix(Pos([x, 200]), is_left=True)
    phoenix.enter_action_stay_phase()
    phoenix.set_pos(Pos([x, 200]))
    phoenix.angle = 0
    phoenix._count_attack_interval = 0 if attack else 10 ** 6
    phoenix._count_graviton = 0
    return phoenix


def _until(game, condition, frames):
    for _ in range(frames):
        if condition():
            return True
        run(game, 1)
    return condition()


def test_graviton_beam_catches_and_pulls_the_plane(round_game):
    from src.game.level.level1.Phoenix import BulletPhoenix
    from src.game.level.level1.GravitonBeam import GravitonBeam
    player = round_game.player
    phoenix = _phoenix_above_player(round_game, attack=True)
    run(round_game, 1)
    assert phoenix.graviton is not None and phoenix.graviton.phase == GravitonBeam.AIM
    assert _until(round_game, lambda: player.lifted, GravitonBeam.AIM_FRAMES + GravitonBeam.LOCK_FRAMES + 5)
    y = player.rect.centery
    run(round_game, 40)
    assert player.rect.centery < y - 30
    # No laser while the beam is on
    assert not any(isinstance(each, BulletPhoenix) for each in G_Enemy_Bullets)
    # The beam lets go in the end
    assert _until(round_game, lambda: not player.lifted, GravitonBeam.LIFT_FRAMES)


def test_breaking_the_shield_frees_the_plane(round_game):
    from src.game.groups import G_Texts
    player = round_game.player
    phoenix = _phoenix_above_player(round_game)
    assert _until(round_game, lambda: player.lifted, 100)
    phoenix.hit(phoenix.MAX_SHIELD)
    run(round_game, 1)
    assert not player.lifted and not phoenix.graviton.alive()
    assert any(each.image.get_width() > 0 for each in G_Texts)


def test_moving_out_of_the_locked_beam_dodges_it(round_game):
    from src.game.level.level1.GravitonBeam import GravitonBeam
    player = round_game.player
    phoenix = _phoenix_above_player(round_game)
    assert _until(round_game, lambda: phoenix.graviton is not None and phoenix.graviton.phase == GravitonBeam.LOCK, 80)
    player.rect.centerx += 250
    run(round_game, GravitonBeam.LOCK_FRAMES + GravitonBeam.FIRE_FRAMES + 2)
    assert not player.lifted
    assert phoenix.graviton is None


def test_an_invincible_plane_is_not_caught(round_game):
    from src.game.TestMode import TestMode
    player = round_game.player
    _phoenix_above_player(round_game)
    TestMode.god_mode = True
    round_game.apply_god_mode()
    run(round_game, 100)
    assert not player.lifted
