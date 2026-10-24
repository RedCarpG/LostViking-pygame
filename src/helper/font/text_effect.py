""" Helpers to render styled text (letter spacing, glow, drop shadow) to a Surface """
import pygame


def _render_spaced(font, text, color, spacing):
    """ Render text with extra space between letters """
    if spacing == 0:
        return font.render(text, True, color)
    letters = [font.render(c, True, color) for c in text]
    width = sum(each.get_width() for each in letters) + spacing * (len(letters) - 1)
    surface = pygame.Surface((max(width, 1), font.get_height()), pygame.SRCALPHA)
    x = 0
    for each in letters:
        surface.blit(each, (x, 0))
        x += each.get_width() + spacing
    return surface


def render_text(font, text, color, spacing=0, glow_color=None, glow_size=8, shadow=False):
    """ Render text to a new Surface
    :param spacing: Extra pixels between letters
    :param glow_color: Color of a soft glow around the letters, no glow if None
    :param glow_size: Blur radius of the glow
    :param shadow: Draw a dark drop shadow under the text (keeps it readable on any background)
    """
    text_surface = _render_spaced(font, text, color, spacing)
    if glow_color is None and not shadow:
        return text_surface

    pad = glow_size * 2 if glow_color is not None else 3
    width = text_surface.get_width() + pad * 2
    height = text_surface.get_height() + pad * 2
    result = pygame.Surface((width, height), pygame.SRCALPHA)

    if glow_color is not None:
        glow = pygame.Surface((width, height), pygame.SRCALPHA)
        glow.blit(_render_spaced(font, text, glow_color, spacing), (pad, pad))
        # Blur: scale down then back up
        small = pygame.transform.smoothscale(
            glow, (max(1, width // glow_size), max(1, height // glow_size)))
        glow = pygame.transform.smoothscale(small, (width, height))
        result.blit(glow, (0, 0))
        result.blit(glow, (0, 0))

    if shadow:
        result.blit(_render_spaced(font, text, (0, 0, 0), spacing), (pad + 2, pad + 2))

    result.blit(text_surface, (pad, pad))
    return result
