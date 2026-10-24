""" Helpers to render pixel-art styled text (letter spacing, hard outline glow, drop shadow) to a Surface """
import pygame


def _render_spaced(font, text, color, spacing):
    """ Render text (no antialiasing, pixel style) with extra space between letters """
    if spacing == 0:
        return font.render(text, False, color)
    letters = [font.render(c, False, color) for c in text]
    width = sum(each.get_width() for each in letters) + spacing * (len(letters) - 1)
    surface = pygame.Surface((max(width, 1), font.get_height()), pygame.SRCALPHA)
    x = 0
    for each in letters:
        surface.blit(each, (x, 0))
        x += each.get_width() + spacing
    return surface


def _outline(surface, text_surface, offset, radius, color, alpha):
    """ Draw the shape of text_surface in `color`, grown by `radius` pixels (square), with one alpha """
    silhouette = pygame.mask.from_surface(text_surface).to_surface(
        setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
    layer = pygame.Surface((text_surface.get_width() + radius * 2, text_surface.get_height() + radius * 2),
                           pygame.SRCALPHA)
    for dx in range(radius * 2 + 1):
        for dy in range(radius * 2 + 1):
            layer.blit(silhouette, (dx, dy))
    # One alpha for the whole layer (overlapping stamps must not add up)
    layer.set_alpha(alpha)
    surface.blit(layer, (offset - radius, offset - radius))


def font_pixel(font) -> int:
    """ Size in screen pixels of one pixel of a pixel font (Silkscreen: font height / ~10) """
    return max(1, round(font.get_height() / 10.25))


def render_text(font, text, color, spacing=0, glow_color=None, shadow=False):
    """ Render pixel-art text to a new Surface. Sizes are in font pixels so nothing mixes pixel sizes
    :param spacing: Extra space between letters, in font pixels
    :param glow_color: Color of a glow around the letters (a hard outline in two steps), none if None
    :param shadow: Draw a dark drop shadow under the text (keeps it readable on any background)
    """
    px = font_pixel(font)
    text_surface = _render_spaced(font, text, color, spacing * px)
    if glow_color is None and not shadow:
        return text_surface

    pad = (px * 2 if glow_color is not None else 0) + (px if shadow else 0)
    result = pygame.Surface((text_surface.get_width() + pad * 2, text_surface.get_height() + pad * 2),
                            pygame.SRCALPHA)

    if shadow:
        _outline(result, text_surface, pad + px, 0, (0, 0, 0), 255)
    if glow_color is not None:
        # Outer ring faint, inner ring solid: a glow made of hard pixel steps
        _outline(result, text_surface, pad, px * 2, glow_color, 70)
        _outline(result, text_surface, pad, px, glow_color, 220)

    result.blit(text_surface, (pad, pad))
    return result
