""" Protoss warp-in: the Oracle arriving, the ships coming out of the Stargate, the Carrier """
import pygame
from pygame.sprite import Sprite, Group

from src.game.groups import G_Effects
from src.helper.sound import play_sound
from src.game.animation.pixel_fx import PIXEL, canvas

WHITE = (235, 254, 255)
CYAN_LIGHT = (146, 250, 255)
CYAN = (4, 244, 255)


class WarpIn(Sprite):
    """ A ring of light closes in, the ship's shape fills from the top in bright cyan,
    then `spawn` is called and the ship is there
    """

    DURATION = 40
    # Part of the warp the ring takes
    RING_PART = 0.45
    # Room around the ship for the ring
    MARGIN = 38

    GROUP = Group()
    # Cyan silhouettes, by ship image; first frames, by sheet
    _shapes = {}
    _frames = {}

    @classmethod
    def first_frame(cls, sheet, frames=6) -> pygame.Surface:
        """ The first frame of a sprite sheet, the same Surface every time (its shape is cached) """
        frame = cls._frames.get(sheet)
        if frame is None:
            frame = sheet.subsurface((0, 0, sheet.get_width() // frames, sheet.get_height()))
            cls._frames[sheet] = frame
        return frame

    @classmethod
    def shape(cls, ship) -> pygame.Surface:
        """ The cyan silhouette of `ship` (made once: call it while loading for the big ships) """
        shape = cls._shapes.get(ship)
        if shape is None:
            shape = pygame.mask.from_surface(ship).to_surface(setcolor=(*CYAN_LIGHT, 255), unsetcolor=(0, 0, 0, 0))
            cls._shapes[ship] = shape
        return shape

    def __init__(self, pos, spawn, ship: pygame.Surface, duration=DURATION, sound="PHOENIX_ARRIVE") -> None:
        """ :param ship: the image whose shape fills in (a frame of the ship, see first_frame) """
        super().__init__(G_Effects, self.GROUP)
        self._shape = shape = self.shape(ship)
        self._spawn = spawn
        self._duration = duration
        self._center = (round(pos[0]), round(pos[1]))
        self._age = 0
        size = max(shape.get_size()) + self.MARGIN * 2
        self.image = canvas(size, size)
        self.rect = self.image.get_rect(center=self._center)
        if sound:
            play_sound(sound)
        self._render()

    def update(self) -> None:
        self._age += 1
        if self._age >= self._duration:
            self._spawn()
            self.kill()
            return
        self._render()

    def _render(self):
        t = self._age / self._duration
        c = self.image
        c.fill((0, 0, 0, 0))
        middle = c.get_width() // 2
        if t < self.RING_PART:
            r = t / self.RING_PART
            radius = int((middle - 4) * (1 - r)) // PIXEL * PIXEL + PIXEL * 2
            pygame.draw.circle(c, WHITE if r > 0.6 else CYAN, (middle, middle), radius, PIXEL)
        # The shape fills from the top, the filled part fading toward the end
        shape = self._shape
        reveal = int(shape.get_height() * min(1.0, max(0.0, (t - 0.25) / 0.6)))
        if reveal > 0:
            top_left = (middle - shape.get_width() // 2, middle - shape.get_height() // 2)
            part = shape.subsurface((0, 0, shape.get_width(), reveal)).copy()
            part.set_alpha(int(220 * (1 - max(0.0, t - 0.75) * 3)))
            c.blit(part, top_left)
            # The bright line where it fills
            inset = shape.get_width() // 8
            c.fill(WHITE, (top_left[0] + inset, top_left[1] + reveal - PIXEL, shape.get_width() - 2 * inset, PIXEL))
