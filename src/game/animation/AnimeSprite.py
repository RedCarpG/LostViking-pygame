from pygame import Rect
from pygame.sprite import Sprite, AbstractGroup
from src.util.type import Size
from .rotsprite import rotated_frame, direction


class AnimeSprite(Sprite):
    def __init__(self, frames: dict, frame_size: Size = None, enable_rotate=False, angle=0, *groups: AbstractGroup):
        # Init Sprite
        super().__init__(*groups)

        # Set Image properties
        self.frames = frames
        self.current_state = None
        self.current_frame = None

        self._max_frame_index = 0
        self._max_frame_width = None
        self._current_frame_index = 0
        self._anime_interval = 0
        self.enable_rotate = enable_rotate
        self.angle = angle
        self._rendered_angle = angle

        if frame_size is not None:
            self._img_w = frame_size.width
            self._img_h = frame_size.height
            self._chop_rect = Rect(0, 0, self._img_w, self._img_h)
        else:
            rect = self.frames["IDLE"].get_rect()
            self._img_w = rect.width / 6
            self._img_h = rect.height
            self._chop_rect = Rect(0, 0, self._img_w, self._img_h)

        self.rect = Rect(0, 0, self._img_w, self._img_h)
        self.set_anime_state("IDLE")

    def update(self):
        self.anime()

    def anime_end_loop_hook(self):
        pass

    def anime(self, anime_freq=5):
        """
        Switch image function should be called per frame
        :param switch_rate: switch rate between each change
        :return: True if loop finished, False if loop not finished
        """
        if self._anime_interval >= anime_freq:
            self._next_image()
            self._anime_interval = 0
        else:
            self._anime_interval += 1
            # Turn between two animation frames when the angle reaches another direction
            if self.enable_rotate and direction(self.angle) != direction(self._rendered_angle):
                self._render_frame()

    def _render_frame(self) -> None:
        """ Set self.image to the current frame, rotated if enabled """
        # Read the sheet from self.frames each time: some UI code swaps it at runtime
        sheet = self.frames[self.current_state]
        rect = self._chop_rect.move(self._current_frame_index * self._img_w, 0)
        if self.enable_rotate:
            # Pixel-art rotation (RotSprite), snapped to 32 directions and cached
            self.image = rotated_frame(sheet, rect, self.angle)
            _temp = self.rect.center
            self.rect = self.image.get_rect(center=_temp)
        else:
            self.image = sheet.subsurface(rect)
        self._rendered_angle = self.angle

    def _next_image(self) -> None:
        self._current_frame_index = (
            self._current_frame_index + 1) % self._max_frame_index
        self._render_frame()
        if self._current_frame_index == 0:
            self.anime_end_loop_hook()

    @property
    def frame_size(self):
        return Size([self._img_w, self._img_h])

    def set_anime_state(self, state) -> None:
        """
        Change main loop image
        :param image_type: Name of the type of image to put into loop
        """
        self._current_frame_index = 0
        self._anime_interval = 0
        self.current_state = state
        self.current_frame = self.frames[state]
        self._max_frame_width = self.current_frame.get_width()
        self._max_frame_index = int(self._max_frame_width / self._img_w)

        self._render_frame()
