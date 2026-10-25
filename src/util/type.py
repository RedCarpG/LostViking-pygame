
import random


class Size:

    def __init__(self, size: list[int, int]) -> None:
        self._width = size[0]
        self._height = size[1]

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def to_list(self):
        return [self._width, self._height]


class Pos(object):

    def __init__(self, pos: list[int, int]) -> None:
        super().__init__()
        self._x = pos[0]
        self._y = pos[1]

    def random_offset(self, offset):
        x = self._x + random.randint(-offset, offset)
        y = self._y + random.randint(-offset, offset)
        return Pos([x, y])

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def move_x(self, x):
        return Pos([self._x + x, self._y])

    def move_y(self, y):
        return Pos([self._x, self._y + y])

    def move(self, pos: list[int, int]):
        return Pos([self._x + pos[0], self._y + pos[1]])

    def to_list(self):
        return [self._x, self._y]
