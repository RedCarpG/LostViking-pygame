from src.helper.image import load_image
from src.setting import *

import pygame


class _SoundBuffer(object):

    BUFFER = {}

    def __getitem__(self, key):
        if key not in self.BUFFER:
            return "Not here " + key
        return self.BUFFER[key]

    def __setitem__(self, key, item):
        self.BUFFER[key] = item

    def __delitem__(self, key):
        del self.BUFFER[key]


def test_func():

    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    x = {"a": "b"}
    sound = _SoundBuffer()
    print(f'----- {sound["X"]}')
    if "b" in x:
        print(f'----- a in x')
