import sys

# Running in a browser (pygbag build)
IS_WEB = sys.platform == "emscripten"


# Color values
class COLOR:
    GRAY = (128, 128, 128)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (246, 38, 39)
    GREEN = (24, 138, 70)
    BLUE = (0, 0, 255)
    BROWN = (216, 158, 120)


# 主音量
MAIN_VOLUME = 0.5
# 屏幕震动的默认值 (受击、爆炸时), 玩家可在设置里修改
SCREEN_SHAKE = True

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
