import random
from src.setting import SCREEN_SHAKE


class ScreenShake:
    """ Camera shake based on "trauma":
    events add trauma (0 to 1), the shake offset grows with trauma squared
    (small hits barely move, big explosions shake hard) and trauma decays every frame
    """

    MAX_OFFSET = 14
    DECAY = 0.025

    _trauma = 0.0
    offset = (0, 0)

    @classmethod
    def add(cls, trauma: float) -> None:
        if SCREEN_SHAKE:
            cls._trauma = min(1.0, cls._trauma + trauma)

    @classmethod
    def update(cls) -> None:
        """ Called once per game frame """
        if cls._trauma > 0:
            cls._trauma = max(0.0, cls._trauma - cls.DECAY)
            power = cls.MAX_OFFSET * cls._trauma ** 2
            cls.offset = (round(random.uniform(-power, power)),
                          round(random.uniform(-power, power)))
        else:
            cls.offset = (0, 0)

    @classmethod
    def is_shaking(cls) -> bool:
        return cls.offset != (0, 0)

    @classmethod
    def reset(cls) -> None:
        cls._trauma = 0.0
        cls.offset = (0, 0)
