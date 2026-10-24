import math

from pygame import Vector2

from src.util.type import Pos


def cal_angle(base_point: Pos, target_point: Pos) -> int:
    """ Calculate angle between two points
    :param base_point
    :param target_point
    :return int angle degree value
    """
    vec = Vector2(0, 1)

    if base_point.y == target_point.y:
        if target_point.x > base_point.x:
            angle = 90
        else:
            angle = -90
    elif base_point.x == target_point.x:
        if target_point.y > base_point.y:
            angle = 0
        else:
            angle = 180
    else:
        angle = math.atan(
            (target_point.y - base_point.y) / (target_point.x - base_point.x))
        angle = 90 - angle * 360 / 2 / math.pi
        if base_point.x > target_point.x:
            angle -= 180

    return angle


def angle_diff(current_angle, target_angle) -> float:
    """ Shortest signed rotation (degrees, -180 to 180) from current_angle to target_angle """
    return (target_angle - current_angle + 180) % 360 - 180


def turn_toward(current_angle, target_angle, rotation_speed) -> float:
    """ Rotate current_angle toward target_angle by at most rotation_speed degrees """
    diff = angle_diff(current_angle, target_angle)
    result = current_angle + max(-rotation_speed, min(rotation_speed, diff))
    return (result + 180) % 360 - 180


def follow_angle(base_point: Pos, target_point: Pos, current_angle, rotation_speed) -> int:
    """ Rotate current_angle to face target_point, by at most rotation_speed degrees
    (the step is clamped so it does not overshoot and jitter around the target)
    """
    return turn_toward(current_angle, cal_angle(base_point, target_point), rotation_speed)
