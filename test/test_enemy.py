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
    boss.hit(boss.MAX_HEALTH)
    for _ in range(boss.DEATH_DURATION + 200 + round_game.END_DELAY):
        run(round_game, 1)
        if round_game.state != GameState.PLAYING:
            break
    assert round_game.state == GameState.VICTORY
    G_Enemy_Bullets.empty()
