from abc import ABC
from pygame import Vector2


class BasicEnemy(ABC):

    MAX_HEALTH = 100
    SCORE = 100

    def __init__(self) -> None:

        self.is_active = True
        self.state = None
        self._speed = Vector2(0, 0)

        self._score = self.SCORE

        self._health = self.MAX_HEALTH

    # --------------- Attributes --------------- #
    # ----- Speed
    @property
    def speed(self) -> tuple:
        return self._speed

    # ----- Health
    @property
    def health(self) -> int:
        return self._health

    @property
    def score(self) -> int:
        return self._score
