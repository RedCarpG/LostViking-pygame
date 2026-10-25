import random

import pygame
from pygame.sprite import Sprite

from src.util.angle import angle_diff, turn_toward, cal_angle
from src.util.inertial import accelerate, decelerate
from src.util.collide_detect import collide_detect, hit_rect
from src.util.type import Pos


def test_angle_diff_takes_the_short_way():
    assert angle_diff(170, -170) == 20
    assert angle_diff(-170, 170) == -20
    assert angle_diff(10, 10) == 0


def test_turn_toward_does_not_overshoot():
    assert turn_toward(0, 5, 10) == 5
    assert turn_toward(0, 90, 10) == 10
    assert turn_toward(175, -175, 6) == -179


def test_cal_angle_points_down_at_zero():
    assert cal_angle(Pos([0, 0]), Pos([0, 10])) == 0
    assert cal_angle(Pos([0, 0]), Pos([10, 0])) == 90
    assert cal_angle(Pos([0, 0]), Pos([-10, 0])) == -90


def test_accelerate_and_decelerate_stop_at_the_limits():
    assert accelerate(9.5, 10, 1, 1) == 10.5
    assert accelerate(10, 10, 1, 1) == 10
    assert decelerate(0.5, 1) == 0
    assert decelerate(-0.5, 1) == 0


class _Box(Sprite):
    def __init__(self, rect, hitbox=None):
        super().__init__()
        self.rect = pygame.Rect(rect)
        if hitbox is not None:
            self.hitbox = pygame.Rect(0, 0, *hitbox)
            self.hitbox.center = self.rect.center


def test_collide_quick_rect_test_gives_the_same_result():
    """ The rect pre-test must never change the answer: hit areas lie inside the rects """
    rng = random.Random(1)
    func = collide_detect(0.8)
    for _ in range(2000):
        a = _Box((rng.randint(0, 200), rng.randint(0, 200), rng.randint(4, 80), rng.randint(4, 80)))
        b = _Box((rng.randint(0, 200), rng.randint(0, 200), 60, 60),
                 hitbox=(rng.randint(2, 60), rng.randint(2, 60)) if rng.random() < 0.5 else None)
        expected = hit_rect(a, 0.8).colliderect(hit_rect(b, 0.8))
        assert func(a, b) == expected


def test_collide_functions_are_cached():
    assert collide_detect(0.6) is collide_detect(0.6)
