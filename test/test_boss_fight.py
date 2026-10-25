""" The Carrier fight: choice of attacks, bullet patterns, the laser, continuous fire and death """
import random

import pytest

from conftest import run
from src.game.animation import AttachEffect, Explosion
from src.game.groups import G_BOSS, G_Enemys, G_Enemy_Bullets, G_Effects
from src.util.collide_detect import collide_detect


@pytest.fixture
def carrier(round_game):
    """ The Carrier in place at the top, attacking only when a test asks """
    round_game.level.spawn_carrier()
    boss = G_BOSS.sprite
    for _ in range(600):
        if boss.state.name != "MoveDown":
            break
        run(round_game, 1)
    boss._count_attack_interval = 10 ** 6
    for sprite in G_Enemys.sprites() + G_Enemy_Bullets.sprites():
        if sprite is not boss:
            sprite.kill()
    round_game.player.set_pos((500, 820))
    yield boss
    round_game.level.clear_enemies()
    G_Enemy_Bullets.empty()


def _attack(game, boss, name, frames):
    """ Start an attack: the number of enemy bullets on screen at each frame """
    G_Enemy_Bullets.empty()
    getattr(boss, f"_attack_{name}")()
    counts = []
    for _ in range(frames):
        run(game, 1)
        counts.append(len(G_Enemy_Bullets))
    return counts


def test_the_carrier_varies_its_attacks(round_game, carrier):
    # The attacks are drawn at random: the same draws on every run
    random.seed(4)
    picked = []
    real_shoot = carrier.shoot

    def spy(target):
        real_shoot(target)
        picked.append(carrier._last_attack)
    carrier.shoot = spy
    carrier._count_attack_interval = 0
    for _ in range(2200):
        round_game.player.set_pos((carrier.rect.centerx + 150, 820))
        run(round_game, 1)
    assert set(picked) == {"interceptors", "laser", "fan", "ring", "volley"}
    assert all(a != b for a, b in zip(picked, picked[1:])), "never the same attack twice in a row"


def test_bullet_patterns(round_game, carrier):
    assert max(_attack(round_game, carrier, "fan", 60)) == carrier.FAN_BULLETS
    assert max(_attack(round_game, carrier, "ring", 60)) == carrier.RING_BULLETS
    assert max(_attack(round_game, carrier, "volley", 90)) >= 7


def test_the_laser_charges_fires_and_sweeps(round_game, carrier):
    game = round_game
    carrier._speed.x = 0
    game.player.set_pos((carrier.rect.centerx + 300, 820))
    carrier._attack_laser()
    laser = carrier.laser
    assert not laser.firing and laser.hitbox.width == 0, "charging: an aiming line, no damage"
    x = carrier.rect.centerx
    frames = 0
    while not laser.firing and frames < 200:
        run(game, 1)
        frames += 1
    assert abs(carrier.rect.centerx - x) <= 2, "the Carrier holds still while it charges"
    while laser.hitbox.width == 0 and frames < 200:
        run(game, 1)
        frames += 1
    assert 55 <= frames <= 75, "the beam hurts about a second after the charge starts"

    box = laser.hitbox
    assert box.top <= carrier.rect.bottom and box.bottom >= 1000, "from the nose to the bottom of the screen"
    player = game.player
    player.set_pos((laser.rect.centerx, carrier.rect.bottom + 30))
    player.rect.top = carrier.rect.bottom + 4
    assert collide_detect(0.6)(player, laser), "no gap under the nose"
    player.set_pos((laser.rect.centerx + 70, 600))
    assert not collide_detect(0.6)(player, laser)

    x = carrier.rect.centerx
    for _ in range(60):
        player.set_pos((x + 250, 820))
        run(game, 1)
    assert carrier.rect.centerx > x + 20, "it sweeps toward the plane"
    for _ in range(400):
        if not laser.alive():
            break
        run(game, 1)
    assert not laser.alive() and not laser.emitter.alive(), "it closes and goes away with its glow"


def test_continuous_fire_does_not_paint_the_carrier_red(round_game, carrier):
    """ Hit every frame: the red hit overlay shows when the burst starts, then the art shows
    (with a soft flash); a hit after a pause shows the overlay again
    """
    def overlay():
        return any(isinstance(s, AttachEffect) and s.ref is carrier and s.frames["IDLE"] is carrier.frames["HIT"]
                   for s in G_Effects)
    carrier.shield = 0      # already broken: the hits reach the hull
    red = 0
    for _ in range(180):
        carrier.hit(10)
        run(round_game, 1)
        red += overlay()
    assert red <= 30
    run(round_game, carrier.HIT_OVERLAY_QUIET)
    carrier.hit(10)
    assert overlay()


def test_the_carrier_explodes_all_over_before_it_falls(round_game, carrier):
    round_game.player.set_pos((800, 900))
    carrier.shield = 0      # already broken: the hits reach the hull
    carrier.hit(carrier.MAX_HEALTH)
    assert carrier.dying and carrier.alive()
    explosions = set()
    for _ in range(carrier.DEATH_DURATION - 1):
        run(round_game, 1)
        explosions.update(s for s in G_Effects if isinstance(s, Explosion))
    assert carrier.alive() and len(explosions) >= 12
    run(round_game, 1 + carrier.HITSTOP_FINAL_BLAST)
    assert carrier.current_state == "DESTROY", "then the last blast"


# --------------- The Carrier's shield --------------- #
def test_the_shield_takes_the_hits_first(round_game, carrier):
    from src.game.animation import Spark
    carrier.hit(500, hit_pos=(carrier.rect.centerx, carrier.rect.bottom))
    assert carrier.shield == carrier.MAX_SHIELD - 500 and carrier.health == carrier.MAX_HEALTH
    assert any(isinstance(s, Spark) for s in G_Effects), "sparks fly off the shield"
    run(round_game, 1)
    assert carrier.shield_effect.image.get_width() > carrier.rect.width, "the shield shows around the hull"


def test_the_shield_recharges_after_a_pause(round_game, carrier):
    carrier.hit(3000)
    run(round_game, carrier.SHIELD_REGEN_DELAY - 5)
    assert carrier.shield == carrier.MAX_SHIELD - 3000, "not while it is under fire"
    run(round_game, 30)
    assert carrier.shield > carrier.MAX_SHIELD - 3000 and carrier.shield_effect.recharging
    run(round_game, 600)
    assert carrier.shield == carrier.MAX_SHIELD


def test_a_broken_shield_comes_back_later(round_game, carrier, monkeypatch):
    import sys
    texts = []
    boss_module = sys.modules["src.game.enemy.EnemyBoss"]
    real_text = boss_module.FloatingText
    monkeypatch.setattr(boss_module, "FloatingText", lambda pos, text, *a, **k: (texts.append(text), real_text(pos, text, *a, **k)))
    carrier.hit(carrier.MAX_SHIELD)
    assert carrier.shield == 0 and carrier.health == carrier.MAX_HEALTH
    assert texts == ["SHIELD DOWN"]
    carrier.hit(100)
    assert carrier.health == carrier.MAX_HEALTH - 100, "while it is down, the hull takes the hits"
    run(round_game, carrier.SHIELD_BREAK_DELAY - 5)
    assert carrier.shield == 0, "it stays down a while"
    run(round_game, 30)
    assert carrier.shield > 0 and carrier.shield_effect.alive(), "then it comes back and recharges"
    run(round_game, 600)
    assert carrier.shield == carrier.MAX_SHIELD

def test_the_shield_bar_stays_while_the_shield_is_down(round_game, carrier):
    ui = round_game.ui.ui_boss
    run(round_game, 1)
    assert ui._blit_shield(carrier) > 0
    carrier.hit(carrier.MAX_SHIELD)
    assert ui._blit_shield(carrier) > 0, "an empty bar while it is down: it comes back"


def test_torpedoes_get_no_armor_bonus_on_a_shield(carrier):
    from types import SimpleNamespace
    from src.game.player.LanzerTorpedo import LanzerTorpedo
    torpedo = SimpleNamespace(damage=110, ARMOR_BONUS=LanzerTorpedo.ARMOR_BONUS)
    assert LanzerTorpedo.damage_to(torpedo, carrier) == 110
    carrier.shield = 0
    assert LanzerTorpedo.damage_to(torpedo, carrier) == 110 + LanzerTorpedo.ARMOR_BONUS


def test_the_nuke_goes_through_shields(round_game, carrier):
    import pygame
    from src.game.custom_events import EVENT_BOMB_EXPLODE
    from src.game.level.level1 import EnemyPhoenix
    from src.util.type import Pos
    phoenix = EnemyPhoenix(Pos([200, 400]), is_left=True)
    assert phoenix.shield == phoenix.MAX_SHIELD
    pygame.event.post(pygame.event.Event(EVENT_BOMB_EXPLODE, {"player": round_game.player}))
    run(round_game, 1)
    assert not phoenix.is_active, "a shielded Phoenix does not survive a nuke"
    assert carrier.shield == carrier.MAX_SHIELD and carrier.health == carrier.MAX_HEALTH - 1000


def test_shots_stop_at_the_edge_of_the_shield(round_game, carrier):
    from pygame import Vector2
    from src.game.player.PlayerViking import PlayerBulletViking
    from src.util.type import Pos
    edge = carrier.shield_effect.edge_point((carrier.rect.centerx, 2000))
    # Just inside the shield, below the hull
    bullet = PlayerBulletViking(Pos([round(edge.x), round(edge.y) - 4]), Vector2(0, -17), 80,
                                player=round_game.player)
    assert bullet.rect.top > carrier.rect.bottom
    bullet.collide_enemy(G_Enemys)
    assert not bullet.alive() and carrier.shield == carrier.MAX_SHIELD - 80
    # Once the shield is down, the same place is empty space
    carrier.shield = 0
    bullet = PlayerBulletViking(Pos([round(edge.x), round(edge.y) - 4]), Vector2(0, -17), 80,
                                player=round_game.player)
    bullet.collide_enemy(G_Enemys)
    assert bullet.alive()
    bullet.kill()
