
from pygame import Rect
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH

# General method to detect whether in screen


def if_in_screen(rect: Rect):
    if rect.top > SCREEN_HEIGHT \
            or rect.bottom < 0 \
            or rect.right < 0 \
            or rect.left > SCREEN_WIDTH:
        return False
    return True
