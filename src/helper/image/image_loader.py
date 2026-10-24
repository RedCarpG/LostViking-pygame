""" Contains functions to load image to a pygame.surface.Surface object.
Some methods to modify a Surface:
    Surface.set_colorkey() -> None
    Surface.set_alpha() -> None
    pygame.transform.smoothscale(Surface) -> Surface
"""
import os
import sys
import pygame
from pygame.display import get_init
from dataclasses import dataclass
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

_image_dir = os.path.join(os.path.split(os.path.abspath(__file__))[
                          0], '../../asset/image')


class _ImageBuffer(object):

    BUFFER = {}

    def __getitem__(self, key):
        if key not in self.BUFFER:
            self.BUFFER[key] = load_image(key)
        return self.BUFFER[key]

    def __setitem__(self, key, item):
        self.BUFFER[key] = item

    def __delitem__(self, key):
        del self.BUFFER[key]

    def pop(self, key, default=None):
        return self.BUFFER.pop(key, default)


_IMAGE = _ImageBuffer()


@dataclass
class ImageType:
    transparency: bool
    color_key: int
    alpha: int
    scale: list


def load_image(filename: str, **kwargs: ImageType) -> pygame.surface.Surface:
    """ Load an image file to a Surface object.
    :param transparency: If a file has transparent pixels
    :param filename: File name, from a default directory "_image_dir"
    :param color_key: A color value which make certain color transparent if not None
    :param alpha: A value from 0-255 which controls full image alpha(transparency) if not None
    :param scale: Transform the image with scale if not None
    :return pygame.surface.Surface object
    """
    if not get_init():
        raise RuntimeError("<ERROR> Pygame display not init.")
    fullname = os.path.join(_image_dir, filename)
    _transparency = kwargs.get("transparency", True)
    _scale = kwargs.get("scale", None)
    _color_key = kwargs.get("color_key", None)
    _alpha = kwargs.get("alpha", None)

    try:
        image = pygame.image.load(fullname)
        logging.info("<SUCCESS> Image [{}] loaded !".format(filename))
    except pygame.error:
        logging.error("<ERROR> Image [{}] not found".format(filename))
        raise SystemExit(str(pygame.get_error()))

    # Convert the Surface for better performance(convert_alpha() if with transparent pixels)
    image = image.convert_alpha() if _transparency else image.convert()

    if _color_key:
        # Set color key for transparency
        if _color_key == -1:
            _color_key = image.get_at((0, 0))
        image.set_colorkey(_color_key, pygame.RLEACCEL)
    if _alpha:
        # Set image alpha value
        image.set_alpha(_alpha, pygame.RLEACCEL)

    if _scale:
        # Scale image
        image = pygame.transform.scale(image,
                                       [int(image.get_width() * _scale[0]),
                                        int(image.get_height() * _scale[1])])

    _IMAGE[filename] = image
    return image


def get_image(label: str, **kwargs: ImageType) -> pygame.surface.Surface:
    _transparency = kwargs.get("transparency", True)
    _scale = kwargs.get("scale", None)
    _color_key = kwargs.get("color_key", None)
    _alpha = kwargs.get("alpha", None)

    image = _IMAGE[label]

    # Convert the Surface for better performance(convert_alpha() if with transparent pixels)
    image = image.convert_alpha() if _transparency else image.convert()

    if _color_key:
        # Set color key for transparency
        if _color_key == -1:
            _color_key = image.get_at((0, 0))
        image.set_colorkey(_color_key, pygame.RLEACCEL)
    if _alpha:
        # Set image alpha value
        image.set_alpha(_alpha, pygame.RLEACCEL)

    if _scale:
        # Scale image
        image = pygame.transform.smoothscale(image,
                                             (int(image.get_width() * _scale[0]),
                                              int(image.get_height() * _scale[1])))

    return image


def del_image(label: str):
    _IMAGE.pop(label, None)
