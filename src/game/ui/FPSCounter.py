from src.setting import COLOR
from src.helper.font import FontEntity, get_font


class FPSCounter:

    def __init__(self, surface, clock, pos):

        self.surface = surface
        self.clock = clock
        self._fps = int(self.clock.get_fps())
        self.fps_text = FontEntity(surface, get_font("Scoreboard"),
                                   f"FPS: {self._fps}", (10, 30), color=COLOR.WHITE)
        self.fps_text.move_center(pos)

    def blit(self):
        self.fps_text.blit()

    def update(self):
        # Render the text again only when the value changes
        fps = int(self.clock.get_fps())
        if fps != self._fps:
            self._fps = fps
            self.fps_text.change_text(f"FPS: {fps}")
