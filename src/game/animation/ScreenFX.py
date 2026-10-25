""" Effects over the whole screen, drawn in screen space (they do not shake)

- flash: the screen lights up (the nuke, the boss blast, the boss getting angry)
- vignette: red edges when the plane is hit, pulsing while its health is low
- rings: shockwaves growing from a point (the nuke, a warp)
- banner: the WARNING shown when a boss comes
- stage title: the name of the part of the route the plane enters

Pixel style like the other generated effects: hard dithered steps on the 2x2 grid.
The images are made ahead of time (see `prepare` and warmup).
"""
import math
import pygame

from src.setting import SCREEN_WIDTH, SCREEN_HEIGHT
from src.helper.font import load_font, get_font, render_text
from src.game.GameSettings import GameSettings
from . import warmup
from .pixel_fx import PIXEL, canvas, upscale, dither

# Red edges: color, strongest alpha (at the screen edge), width (art pixels), shade steps
VIGNETTE_COLOR = (214, 24, 40)
VIGNETTE_ALPHA = 190
VIGNETTE_WIDTH = 56
VIGNETTE_STEPS = 5

# Shockwave colors, from the start to the end of a ring: fire, and the light of a warp
RING_COLORS = [(255, 255, 232), (255, 238, 140), (255, 200, 64), (248, 136, 36), (220, 74, 30)]
WARP_RING_COLORS = [(235, 254, 255), (146, 250, 255), (4, 244, 255), (91, 138, 200), (75, 44, 155)]

# Warning banner
BANNER_RED = (220, 40, 48)
BANNER_DARK = (44, 10, 18)
BANNER_BACK = (8, 4, 12, 180)
BANNER_Y = int(SCREEN_HEIGHT * 0.42)
BANNER_HEIGHT = 120
STRIPE_HEIGHT = 10      # art pixels
STRIPE_PERIOD = 16      # art pixels
# Texts under the WARNING, drawn ahead of time
BANNER_SUBTITLES = ("CARRIER APPROACHING", "PROTOSS STARGATE AHEAD", "CARRIER WARPED IN")

# Stage title
TITLE_COLOR = (214, 236, 255)
TITLE_GLOW = (30, 70, 150)
SUBTITLE_COLOR = (140, 170, 220)
LINE_COLOR = (90, 140, 220)
TITLE_Y = int(SCREEN_HEIGHT * 0.3)

_images = None


def prepare() -> None:
    """ Make the images ahead of time (see warmup) """
    if _images is None:
        warmup.add(_build())


def _get_images() -> dict:
    if _images is None:
        for _ in _build():
            pass
    return _images


def _build():
    """ Generator: one image per step (see warmup) """
    global _images
    if _images is not None:
        return
    result = {}
    vignette = None
    for vignette in _make_vignette():
        if vignette is None:
            yield
    result["vignette"] = vignette
    yield
    result["stripes"] = _make_stripes()
    yield
    # The font is drawn small and scaled 2x: same pixel look, and the glow is much faster to draw
    load_font("Silkscreen-Bold.ttf", 32, "MenuTitle")
    load_font("Silkscreen-Regular.ttf", 24, "MenuText")
    title = render_text(get_font("MenuTitle"), "WARNING", (255, 236, 236), spacing=1, glow_color=BANNER_RED)
    result["title"] = upscale(title, 2)
    yield
    result["subtitles"] = {}
    for text in BANNER_SUBTITLES:
        result["subtitles"][text] = _render_subtitle(text)
        yield
    back = pygame.Surface((SCREEN_WIDTH, BANNER_HEIGHT), pygame.SRCALPHA)
    back.fill(BANNER_BACK)
    result["back"] = back
    if _images is None:
        _images = result


def _render_subtitle(text):
    return render_text(get_font("MenuText"), text, (255, 170, 170), spacing=1, shadow=True)


# Stage titles, by (title, subtitle)
_titles = {}


def prepare_titles(titles) -> None:
    """ Draw the (title, subtitle) texts of stage titles ahead of time (see warmup) """
    for title in titles:
        if title not in _titles:
            warmup.add(_draw_title(title))


def _draw_title(title):
    """ Generator: the title, then the subtitle (two warm-up steps) """
    text, subtitle = title
    big = render_text(get_font("MenuTitle"), text, TITLE_COLOR, spacing=1, glow_color=TITLE_GLOW)
    yield
    small = render_text(get_font("MenuText"), subtitle, SUBTITLE_COLOR, spacing=1, shadow=True)
    _titles.setdefault(title, (big, small))


def _title_images(title):
    if title not in _titles:
        for _ in _draw_title(title):
            pass
    return _titles[title]


def _make_vignette():
    """ Generator: yields None while drawing (a few rows per step), then the 4 edge strips
    (top, bottom, left, right): only the edges are blended, not the whole screen
    """
    w, h = SCREEN_WIDTH // PIXEL, SCREEN_HEIGHT // PIXEL
    band = VIGNETTE_WIDTH
    art = canvas(w, h)
    for y in range(h):
        dy = max(0, band - min(y, h - 1 - y))
        if dy == 0:
            # Middle rows: only the left and right bands
            columns = list(range(band)) + list(range(w - band, w))
        else:
            columns = range(w)
        for x in columns:
            dx = max(0, band - min(x, w - 1 - x))
            # 1 at the edge, 0 at the inner side of the band (rounded inner corners)
            t = min(1.0, math.sqrt(dx * dx + dy * dy) / band)
            if t <= 0:
                continue
            level = int(t ** 1.7 * VIGNETTE_STEPS + dither(x, y) - 0.5)
            if level > 0:
                art.set_at((x, y), (*VIGNETTE_COLOR, VIGNETTE_ALPHA * min(level, VIGNETTE_STEPS) // VIGNETTE_STEPS))
        if y % 6 == 0:
            yield None
    full = upscale(art)
    edge = band * PIXEL
    yield [
        (full.subsurface((0, 0, SCREEN_WIDTH, edge)).copy(), (0, 0)),
        (full.subsurface((0, SCREEN_HEIGHT - edge, SCREEN_WIDTH, edge)).copy(), (0, SCREEN_HEIGHT - edge)),
        (full.subsurface((0, edge, edge, SCREEN_HEIGHT - 2 * edge)).copy(), (0, edge)),
        (full.subsurface((SCREEN_WIDTH - edge, edge, edge, SCREEN_HEIGHT - 2 * edge)).copy(),
         (SCREEN_WIDTH - edge, edge)),
    ]


def _make_stripes() -> pygame.Surface:
    """ Hazard stripes, one period wider than the screen so they can scroll """
    w = SCREEN_WIDTH // PIXEL + STRIPE_PERIOD
    art = canvas(w, STRIPE_HEIGHT)
    for y in range(STRIPE_HEIGHT):
        for x in range(w):
            if y in (0, STRIPE_HEIGHT - 1):
                color = BANNER_DARK
            else:
                color = BANNER_RED if ((x + y) // (STRIPE_PERIOD // 2)) % 2 == 0 else BANNER_DARK
            art.set_at((x, y), color)
    return upscale(art)


class Banner:
    """ Hazard stripes slide in, the title blinks, then everything fades out """

    DURATION = 170
    SLIDE = 14
    FADE = 20
    # The title is shown BLINK_ON frames, hidden BLINK_OFF frames
    BLINK_ON = 22
    BLINK_OFF = 8
    SCROLL = 2

    def __init__(self, subtitle) -> None:
        self.age = 0
        self.subtitle = subtitle

    @property
    def done(self) -> bool:
        return self.age >= self.DURATION

    def update(self) -> None:
        self.age += 1

    def draw(self, surface, images) -> None:
        age = self.age
        left = self.DURATION - age
        alpha = 255 if left > self.FADE else 255 * left // self.FADE
        # Opens from the middle of the screen
        width = SCREEN_WIDTH * min(1.0, (age + 1) / self.SLIDE)
        width = int(width) // (PIXEL * 2) * PIXEL * 2
        x = (SCREEN_WIDTH - width) // 2
        top = BANNER_Y - BANNER_HEIGHT // 2

        back = images["back"]
        back.set_alpha(alpha)
        surface.blit(back, (x, top), (0, 0, width, BANNER_HEIGHT))

        stripes = images["stripes"]
        stripes.set_alpha(alpha)
        period = STRIPE_PERIOD * PIXEL
        scroll = (age * self.SCROLL) % period
        height = stripes.get_height()
        # The two bands scroll in opposite directions
        surface.blit(stripes, (x, top - height), (scroll + x, 0, width, height))
        surface.blit(stripes, (x, top + BANNER_HEIGHT), (period - scroll + x, 0, width, height))

        if age >= self.SLIDE and (age - self.SLIDE) % (self.BLINK_ON + self.BLINK_OFF) < self.BLINK_ON:
            subtitles = images["subtitles"]
            if self.subtitle not in subtitles:
                subtitles[self.subtitle] = _render_subtitle(self.subtitle)
            for image, y in ((images["title"], BANNER_Y - 18), (subtitles[self.subtitle], BANNER_Y + 38)):
                image.set_alpha(alpha)
                surface.blit(image, image.get_rect(center=(SCREEN_WIDTH // 2, y)))


class StageTitle:
    """ The name of a part of the route: fades in, a line grows under it, then it fades out """

    DURATION = 210
    FADE_IN = 16
    FADE_OUT = 40
    LINE_FRAMES = 28
    LINE_WIDTH = 380

    def __init__(self, title) -> None:
        self.age = 0
        self.images = _title_images(title)

    @property
    def done(self) -> bool:
        return self.age >= self.DURATION

    def update(self) -> None:
        self.age += 1

    def draw(self, surface) -> None:
        left = self.DURATION - self.age
        alpha = 255 * min(self.age, self.FADE_IN) // self.FADE_IN
        if left < self.FADE_OUT:
            alpha = 255 * left // self.FADE_OUT
        title, subtitle = self.images
        title.set_alpha(alpha)
        surface.blit(title, title.get_rect(midbottom=(SCREEN_WIDTH // 2, TITLE_Y)))
        # The line grows from the middle, on the pixel grid
        width = int(self.LINE_WIDTH * min(1.0, self.age / self.LINE_FRAMES)) // (PIXEL * 2) * PIXEL * 2
        if width > 0 and alpha > 0:
            r, g, b = LINE_COLOR
            k = alpha / 255
            surface.fill((int(r * k), int(g * k), int(b * k)),
                         ((SCREEN_WIDTH - width) // 2, TITLE_Y + PIXEL * 3, width, PIXEL),
                         special_flags=pygame.BLEND_RGB_ADD)
        subtitle.set_alpha(alpha)
        surface.blit(subtitle, subtitle.get_rect(midtop=(SCREEN_WIDTH // 2, TITLE_Y + PIXEL * 7)))


class ScreenFX:

    # Hurt vignette: fades by this much per frame
    HURT_DECAY = 0.06
    # Low health pulse: strength range and frames per pulse
    LOW_HEALTH_MIN = 0.3
    LOW_HEALTH_MAX = 0.65
    LOW_HEALTH_PERIOD = 50

    # Flash: strength at the start, frames since the start, length
    _flash = 0.0
    _flash_age = 0
    _flash_duration = 1
    _flash_color = (255, 255, 255)
    _hurt = 0.0
    _low_health = False
    _time = 0
    # [center, max radius, age, duration]
    _rings = []
    _banner = None
    _title = None

    # ------------------ Triggers ------------------

    @classmethod
    def flash(cls, color=(255, 255, 255), strength=1.0, duration=24) -> None:
        """ Light the screen up with `color`, fading out over `duration` frames """
        if GameSettings.screen_flash and strength >= cls._flash_strength():
            cls._flash = strength
            cls._flash_age = 0
            cls._flash_duration = duration
            cls._flash_color = color

    @classmethod
    def _flash_strength(cls) -> float:
        """ Bright at once, then fades fast (squared) """
        if cls._flash_age >= cls._flash_duration:
            return 0.0
        return cls._flash * (1 - cls._flash_age / cls._flash_duration) ** 2

    @classmethod
    def hurt(cls, strength) -> None:
        """ Red edges for a moment, `strength` 0 to 1 """
        cls._hurt = min(1.0, max(cls._hurt, strength))

    @classmethod
    def set_low_health(cls, low: bool) -> None:
        cls._low_health = low

    @classmethod
    def ring(cls, center, radius, duration=30, colors=RING_COLORS) -> None:
        cls._rings.append([center, radius, 0, duration, colors])

    @classmethod
    def boss_warning(cls, subtitle=BANNER_SUBTITLES[0]) -> None:
        cls._banner = Banner(subtitle)

    @classmethod
    def stage_title(cls, title, subtitle) -> None:
        """ Show the name of the part of the route the plane enters (see prepare_titles) """
        cls._title = StageTitle((title, subtitle))

    # ------------------ Frame ------------------

    @classmethod
    def update(cls) -> None:
        """ Called once per game frame """
        cls._time += 1
        if cls._flash_age < cls._flash_duration:
            cls._flash_age += 1
        if cls._hurt > 0:
            cls._hurt = max(0.0, cls._hurt - cls.HURT_DECAY)
        for ring in cls._rings:
            ring[2] += 1
        cls._rings = [ring for ring in cls._rings if ring[2] < ring[3]]
        if cls._banner is not None:
            cls._banner.update()
            if cls._banner.done:
                cls._banner = None
        if cls._title is not None:
            cls._title.update()
            if cls._title.done:
                cls._title = None

    @classmethod
    def draw(cls, surface) -> None:
        """ Rings, vignette and flash: over the world, under the HUD """
        for center, radius, age, duration, colors in cls._rings:
            t = age / duration
            r = int(radius * (1 - (1 - t) ** 2)) // PIXEL * PIXEL
            width = max(PIXEL, int(12 * (1 - t)) // PIXEL * PIXEL)
            if r > width:
                color = colors[min(len(colors) - 1, int(t * len(colors)))]
                pygame.draw.circle(surface, color, center, r, width)

        strength = cls._hurt
        if cls._low_health:
            pulse = 0.5 + 0.5 * math.sin(cls._time * math.tau / cls.LOW_HEALTH_PERIOD)
            strength = max(strength, cls.LOW_HEALTH_MIN + (cls.LOW_HEALTH_MAX - cls.LOW_HEALTH_MIN) * pulse)
        if strength > 0.02:
            alpha = int(255 * strength)
            for image, pos in _get_images()["vignette"]:
                image.set_alpha(alpha)
                surface.blit(image, pos)

        k = cls._flash_strength()
        if k > 0.01:
            # Additive fill: brightens the whole screen without an alpha layer
            r, g, b = cls._flash_color
            surface.fill((int(r * k), int(g * k), int(b * k)), special_flags=pygame.BLEND_RGB_ADD)

    @classmethod
    def draw_overlay(cls, surface) -> None:
        """ The stage title and the banner: over the HUD """
        if cls._title is not None:
            cls._title.draw(surface)
        if cls._banner is not None:
            cls._banner.draw(surface, _get_images())

    @classmethod
    def reset(cls) -> None:
        cls._flash = 0.0
        cls._flash_age = 0
        cls._flash_duration = 1
        cls._hurt = 0.0
        cls._low_health = False
        cls._rings = []
        cls._banner = None
        cls._title = None
