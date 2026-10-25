""" The Terran Starport the Viking takes off from at the start of the route (scenery)

The plane starts on its launch pad; after a moment the Starport falls behind, faster and
faster, and leaves the screen. The sheet (6 frames: blinking lights) is made by
tools/pixel_art/make_structures.py and drawn at 2x.
"""
from pygame.sprite import Sprite

from src.setting import SCREEN_HEIGHT
from src.game.groups import G_Scenery
from src.helper.image import get_image, ART_SCALE
from src.helper.sound import play_sound

IMAGE = "Structure/Starport/Starport.png"


class TerranStarport(Sprite):

    # Middle of the launch pad in the image (art pixels (100, 40), see make_structures.py)
    PAD = (100 * ART_SCALE + 1, 40 * ART_SCALE + 1)
    # Frames it waits before the plane takes off, then it speeds up to MAX_SPEED
    HOLD = 60
    ACCELERATION = 0.05
    MAX_SPEED = 7
    FRAME_TIME = 8

    def __init__(self, pad_center) -> None:
        """ :param pad_center: where the plane stands """
        super().__init__(G_Scenery)
        sheet = get_image(IMAGE)
        width = sheet.get_width() // 6
        self._frames = [sheet.subsurface((i * width, 0, width, sheet.get_height())) for i in range(6)]
        self.image = self._frames[0]
        self.rect = self.image.get_rect(topleft=(pad_center[0] - self.PAD[0], pad_center[1] - self.PAD[1]))
        self._y = float(self.rect.top)
        self._speed = 0.0
        self._time = 0

    @property
    def launched(self) -> bool:
        return self._time >= self.HOLD

    def update(self) -> None:
        self._time += 1
        if self._time == self.HOLD:
            play_sound("TRANSFORM_FIGHTER")
        if self.launched:
            self._speed = min(self.MAX_SPEED, self._speed + self.ACCELERATION)
            self._y += self._speed
            self.rect.top = round(self._y)
            if self.rect.top > SCREEN_HEIGHT:
                self.kill()
                return
        self.image = self._frames[(self._time // self.FRAME_TIME) % len(self._frames)]
