""" Short flash at a gun when it fires, drawn in code as pixel art """
from pygame.sprite import Sprite

from src.game.groups import G_Effects
from .pixel_fx import canvas, upscale

WHITE = (255, 255, 232)
YELLOW = (255, 216, 92)
ORANGE = (248, 136, 36)

# Each frame: (x offset from the middle column, top row, color) of the vertical lines of the
# flame, on a 7x9 art pixel canvas with the gun at the bottom middle. Hot at the start
SHAPES = [
    [(0, 1, YELLOW), (0, 4, WHITE), (-1, 5, YELLOW), (1, 5, YELLOW), (-2, 7, ORANGE), (2, 7, ORANGE)],
    [(0, 4, YELLOW), (0, 6, WHITE), (-1, 7, ORANGE), (1, 7, ORANGE)],
    [(0, 7, ORANGE)],
]
WIDTH, HEIGHT = 7, 9
# Game frames per animation frame
FRAME_TIME = 2

_frames = None


def _get_frames():
    global _frames
    if _frames is None:
        _frames = []
        for shape in SHAPES:
            c = canvas(WIDTH, HEIGHT)
            for dx, top, color in shape:
                c.fill(color, (WIDTH // 2 + dx, top, 1, HEIGHT - top))
            _frames.append(upscale(c))
    return _frames


class MuzzleFlash(Sprite):
    """ Follows `owner`: the gun is at `offset` (x from its center, y from its top) """

    def __init__(self, owner, offset) -> None:
        super().__init__(G_Effects)
        self.owner = owner
        self.offset = offset
        self._frames = _get_frames()
        self._age = 0
        self.image = self._frames[0]
        self.rect = self.image.get_rect()
        self._follow()

    def _follow(self):
        self.rect.midbottom = (self.owner.rect.centerx + self.offset[0], self.owner.rect.top + self.offset[1])

    def update(self) -> None:
        self._age += 1
        index = self._age // FRAME_TIME
        if index >= len(self._frames) or not self.owner.is_active:
            self.kill()
            return
        self.image = self._frames[index]
        self._follow()
