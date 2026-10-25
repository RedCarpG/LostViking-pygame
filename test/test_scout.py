import random

from pygame import Vector2

from conftest import run
from src.game.groups import G_Enemy_Bullets
from src.game.level.level1 import EnemyScout
from src.game.level.level1.Scout import BulletScout
from src.util.type import Pos


def _calm(scout):
    """ No regular attacks (the tests watch the flight) """
    scout._count_attack_interval = 10 ** 6
    return scout


def test_weave_snakes_down(round_game):
    scout = _calm(EnemyScout(Pos([500, -60]), EnemyScout.WEAVE))
    xs = []
    for _ in range(EnemyScout.WEAVE_PERIOD):
        run(round_game, 1)
        xs.append(scout.rect.centerx)
    assert max(xs) - min(xs) > EnemyScout.WEAVE_WIDTH * 1.5
    assert scout.rect.centery > 200


def test_dive_swoops_toward_the_plane(round_game):
    player = round_game.player
    player.rect.centerx = 800
    scout = _calm(EnemyScout(Pos([200, -60]), EnemyScout.DIVE, height=250))
    run(round_game, 150)
    assert scout._stage == "dive"
    run(round_game, 60)
    assert scout.rect.centerx > 450
    assert scout.angle != 0


def test_strafe_crosses_and_leaves(round_game):
    scout = _calm(EnemyScout(Pos([-70, 300]), EnemyScout.STRAFE))
    run(round_game, 60)
    assert 0 < scout.rect.centerx < 400 and abs(scout.rect.centery - 300) < 40
    run(round_game, 300)
    assert not scout.alive()


def test_hover_stops_and_fires_an_aimed_burst(round_game):
    player = round_game.player
    player.rect.centerx = 800
    scout = EnemyScout(Pos([300, -60]), EnemyScout.HOVER, height=220)
    run(round_game, 140)
    assert scout._stage == "hold" and scout._speed.length() == 0
    run(round_game, EnemyScout.HOVER_AIM_TIME + EnemyScout.BURST * EnemyScout.BURST_INTERVAL)
    bullets = [each for each in G_Enemy_Bullets if isinstance(each, BulletScout)]
    assert len(bullets) == EnemyScout.BURST
    to_player = Vector2(player.rect.center) - scout.rect.center
    for bullet in bullets:
        assert bullet.speed.angle_to(to_player) % 360 < 15 or bullet.speed.angle_to(to_player) % 360 > 345
    run(round_game, EnemyScout.HOVER_DURATION + 200)
    assert not scout.alive()


def test_waves_bring_formations(round_game):
    rng = random.Random(1)
    sizes = {wave: EnemyScout.spawn_wave(wave, rng) for wave in EnemyScout.WAVES}
    assert sizes == {"single": 1, "v": 5, "line": 4, "column": 3, "pincer": 2}


def test_waves_respect_the_scout_limit(round_game):
    while len(EnemyScout.GROUP) < EnemyScout.MAX_NUMBER - 2:
        EnemyScout(Pos([500, -300]))
    assert EnemyScout.spawn_wave("v") == 0
    assert EnemyScout.spawn_wave("pincer") == 2


def test_formations_get_more_common(round_game):
    level = round_game.level
    random.seed(4)
    early = sum(level._choose_wave(0.0) == "single" for _ in range(400))
    late = sum(level._choose_wave(1.0) == "single" for _ in range(400))
    assert early > late + 60
