class HitStop:
    """ Freezes the world for a few frames on a big impact (a large ship destroyed, the nuke),
    so the hit feels heavy. The screen keeps shaking and the controls still answer
    """

    _frames = 0

    @classmethod
    def add(cls, frames: int) -> None:
        # The longest freeze wins, freezes do not add up
        cls._frames = max(cls._frames, frames)

    @classmethod
    def update(cls) -> bool:
        """ Called once per game frame, :return: True if the world is frozen this frame """
        if cls._frames > 0:
            cls._frames -= 1
            return True
        return False

    @classmethod
    def reset(cls) -> None:
        cls._frames = 0
