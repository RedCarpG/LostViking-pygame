import os
import logging
import pygame

log = logging.getLogger(__name__)

_font_dir = os.path.join(os.path.split(
    os.path.abspath(__file__))[0], '../../asset/font')


class _FontBuffer(object):

    BUFFER = {}

    def __getitem__(self, key):
        if key not in self.BUFFER:
            raise KeyError(f"Font [{key}] not loaded")
        return self.BUFFER[key]

    def __setitem__(self, key, item):
        self.BUFFER[key] = item

    def __delitem__(self, key):
        del self.BUFFER[key]


_FONT = _FontBuffer()


def load_font(filename, size, label):
    """ Load from a font file ".ttf" to a Font object
    :param filename [Name of the file, from a default directory "_font_dir"]
    :param size
    :return pygame.font.Font object
    """
    if label in _FONT.BUFFER:
        return _FONT[label]
    fullname = os.path.join(_font_dir, filename)
    try:
        font = pygame.font.Font(fullname, size)
        log.debug("Font [%s] loaded", filename)
    except (pygame.error, FileNotFoundError):
        log.error("Font [%s] not found", filename)
        raise SystemExit(str(pygame.get_error()))
    _FONT[label] = font
    return font


def get_font(label):
    return _FONT[label]


def del_font(label):
    del _FONT[label]
