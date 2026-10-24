from src.game.animation import AnimeSprite
from src.util.type import Pos, Size
from src.game.groups import G_Effects


class Effect(AnimeSprite):

    def __init__(self, pos: Pos, frames, frame_size: Size) -> None:
        super().__init__(frames, frame_size)

        self.rect.center = pos.to_list()
        G_Effects.add(self)

    def anime_end_loop_hook(self):
        self.kill()

    def update(self):
        self.anime()


class AttachEffect(AnimeSprite):

    def __init__(self, ref, frames, frame_size: Size, enable_rotate=True, angle=0, offset=None, cb_func=None, break_cb_func=None, loop: bool = False) -> None:
        super().__init__(frames, frame_size, enable_rotate=enable_rotate, angle=angle)

        if offset is not None:
            self.offset = offset
        else:
            self.offset = [0, 0]
        self.rect.center = ref.rect.center
        self.rect = self.rect.move(self.offset)
        self.ref = ref
        G_Effects.add(self)
        self.angle = ref.angle
        self.cb_func = cb_func
        self.break_cb_func = break_cb_func
        self.loop = loop

    def anime_end_loop_hook(self):
        if self.cb_func:
            self.cb_func()
        if not self.loop:
            self.kill()

    def update(self):
        if self.break_cb_func is not None and self.break_cb_func():
            self.kill()
        self.anime()
        self.rect.center = self.ref.rect.center
        self.rect = self.rect.move(self.offset)
        self.angle = self.ref.angle


class UIEffect(AnimeSprite):

    def __init__(self, surface, frames, frame_size: Size, offset=[0, 0], cb_func=None, loop: bool = False, group=None) -> None:
        super().__init__(frames, frame_size)

        self.cb_func = cb_func
        self.surface = surface
        self.rect.move_ip(offset[0], offset[1])
        if group is not None:
            group.add(self)
        self.loop = loop

    def anime_end_loop_hook(self):
        if self.cb_func:
            self.cb_func()
        if not self.loop:
            self.kill()

    def update(self):
        self.anime()

    def blit(self):
        self.surface.blit(self.image, self.rect)
