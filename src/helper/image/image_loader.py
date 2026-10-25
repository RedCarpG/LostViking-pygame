""" Contains functions to load image to a pygame.surface.Surface object.
Some methods to modify a Surface:
    Surface.set_colorkey() -> None
    Surface.set_alpha() -> None
    pygame.transform.smoothscale(Surface) -> Surface
"""
import os
import logging
import pygame
from pygame.display import get_init
from dataclasses import dataclass

log = logging.getLogger(__name__)

_image_dir = os.path.join(os.path.split(os.path.abspath(__file__))[
                          0], '../../asset/image')

# The sprites (ships, bullets, supplies, structures) are drawn at art size and shown at ART_SCALE,
# like the background: one art pixel is a 2x2 block of screen pixels. Images in these folders are
# scaled when they are loaded; the art-size image is kept for the pixel-art rotations (art_source)
ART_SCALE = 2
_ART_FOLDERS = ("PlayerPlane/", "Enemy/", "Supply/", "Structure/", "Bomb/")
# Scaled image -> (art-size image, scale)
_ART = {}


def art_scale(filename: str) -> int:
    """ Screen pixels per art pixel of an image file """
    return ART_SCALE if filename.replace("\\", "/").startswith(_ART_FOLDERS) else 1


def art_source(image: pygame.Surface):
    """ (art-size image, scale) of an image scaled when loaded, None for the others """
    return _ART.get(image)


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
        log.debug("Image [%s] loaded", filename)
    except pygame.error:
        log.error("Image [%s] not found", filename)
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

    scale = art_scale(filename)
    if scale > 1:
        art = image
        image = pygame.transform.scale(art, (art.get_width() * scale, art.get_height() * scale))
        _ART[image] = (art, scale)

    _IMAGE[filename] = image
    return image


def load_images(filenames) -> None:
    """ Load every image of a list (an asset manifest) that is not loaded yet, see load_image """
    for filename in filenames:
        if filename not in _IMAGE.BUFFER:
            load_image(filename)


def get_image(label: str, **kwargs: ImageType) -> pygame.surface.Surface:
    _transparency = kwargs.get("transparency", True)
    _scale = kwargs.get("scale", None)
    _color_key = kwargs.get("color_key", None)
    _alpha = kwargs.get("alpha", None)

    image = _IMAGE[label]
    if not kwargs:
        # Already converted when loaded: share it instead of copying it on every call
        # (copying the big sprite sheets froze the game for a moment, mostly on the web).
        # Code that draws onto an image must copy it first
        return image

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


_ROTATED = {}


def get_rotated_image(image: pygame.Surface, angle: float) -> pygame.surface.Surface:
    """ `image` turned by `angle` degrees (counterclockwise), cached by whole degree.
    Bullets are turned on every shot: the same few angles come back all the time.
    A sprite is turned at art size, then scaled: its pixels stay on the art grid
    """
    angle = round(angle) % 360
    if angle == 0:
        return image
    key = (image, angle)
    rotated = _ROTATED.get(key)
    if rotated is None:
        source = art_source(image)
        if source is None:
            rotated = pygame.transform.rotate(image, angle)
        else:
            art, scale = source
            turned = pygame.transform.rotate(art, angle)
            rotated = pygame.transform.scale(turned, (turned.get_width() * scale, turned.get_height() * scale))
        _ROTATED[key] = rotated
    return rotated
