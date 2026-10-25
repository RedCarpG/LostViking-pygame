""" Record the GIFs and the screenshot shown in the README (docs/media)

Development tool. The game runs headless with scripted scenes (a normal round at a chosen
stage of the route, the player flown by the script and kept alive); one game frame out of
FRAME_STEP is kept. Frames are saved at half size with a 2x2 box
filter, so the 2x pixel art stays exact, and every GIF uses one palette (no flicker).

Needs Pillow:  pip install pillow
Run from the project root:  python tools/record_gifs.py
"""
import math
import os
import random
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.getcwd())

import logging

import pygame
from PIL import Image

OUT = Path("docs/media")
SCALE = 2
# Keep one game frame out of FRAME_STEP (60 / 3 = 20 frames per second)
FRAME_STEP = 3


class Recorder:
    def __init__(self, game):
        self.game = game
        self.frames = []
        self._count = 0

    def run(self, n=1, record=True, each_frame=None):
        for _ in range(n):
            if each_frame:
                each_frame()
            self.game.step()
            if record:
                if self._count % FRAME_STEP == 0:
                    self.frames.append(snapshot(self.game.screen))
                self._count += 1

    def save(self, name):
        save_gif(self.frames, OUT / name)
        self.frames = []
        self._count = 0


def snapshot(surface) -> Image.Image:
    image = Image.frombytes("RGB", surface.get_size(), pygame.image.tostring(surface, "RGB"))
    return image.resize((image.width // SCALE, image.height // SCALE), Image.Resampling.BOX)


def save_gif(frames, path):
    # One palette for the whole GIF, made from a sample of its frames
    sample_frames = frames[::max(1, len(frames) // 12)]
    width, height = frames[0].size
    sample = Image.new("RGB", (width, height * len(sample_frames)))
    for i, frame in enumerate(sample_frames):
        sample.paste(frame, (0, i * height))
    palette = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    paletted = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    paletted[0].save(path, save_all=True, append_images=paletted[1:], duration=1000 * FRAME_STEP // 60,
                     loop=0, optimize=True, disposal=1)
    print(f"saved {path} ({len(frames)} frames, {path.stat().st_size / 1e6:.1f} MB)")


def show_planet(game, kind, radius, seed, x, y):
    from src.game.ui.Planets import make_planet
    job = make_planet(random.Random(seed), kind, radius)
    try:
        while True:
            next(job)
    except StopIteration as done:
        image = done.value
    planets = game.background.planets
    planets._show(image)
    planets._x, planets._y = x, y


def new_game(stage=None):
    """ A normal round, at `stage` of the route (None: no enemies but the scripted ones) """
    from src.game import groups
    from src.game.Game import Game
    for value in vars(groups).values():
        if isinstance(value, pygame.sprite.AbstractGroup):
            value.empty()
    pygame.event.clear()
    game = Game()
    game.start_round(test_mode=False)
    if stage is None:
        game.level.auto_spawn = False
    else:
        game.level.go_to(stage)
    return game


def fly(game, t, target_x=None, speed=60, width=260, y=820, shoot=True):
    """ Move the player smoothly (side to side, or toward `target_x`) and shoot.
    Its health is kept full so the scene does not end
    """
    player = game.player
    if target_x is None:
        x = 500 + width * math.sin(t[0] / speed)
    else:
        x = player.rect.centerx + max(-6, min(6, (target_x - player.rect.centerx) * 0.08))
    player.set_pos((x, y))
    player._health = player.MAX_HEALTH
    if shoot:
        player.attack()
    t[0] += 1


def nearest_enemy_x(game):
    from src.game import groups as G
    enemies = [e for e in G.G_Enemys if e.is_active and 0 < e.rect.centery < 700]
    if not enemies:
        return 500
    return max(enemies, key=lambda e: e.rect.centery).rect.centerx


def title_screen():
    from src.game.Game import Game
    from src.game import groups
    for value in vars(groups).values():
        if isinstance(value, pygame.sprite.AbstractGroup):
            value.empty()
    game = Game()
    show_planet(game, "ocean", 34, 21, 700, 520)
    for _ in range(3):
        game.step()
    snapshot(game.screen).save(OUT / "title.png")
    print(f"saved {OUT / 'title.png'}")


def patrol_scene():
    """ Protoss patrol: Scout formations, Phoenixes, an Oracle """
    game = new_game("patrol")
    rec = Recorder(game)
    for _ in range(3):
        game.player.level_up()
    show_planet(game, "gas", 42, 4, 40, -60)
    t = [0]
    rec.run(450, record=False, each_frame=lambda: fly(game, t, nearest_enemy_x(game)))
    rec.run(330, each_frame=lambda: fly(game, t, nearest_enemy_x(game)))
    rec.save("patrol.gif")


def outposts_scene():
    """ Protoss outposts: platforms with a Pylon and Photon Cannons, Lanzer Torpedoes """
    game = new_game("outposts")
    rec = Recorder(game)
    for _ in range(2):
        game.player.level_up()
    game.player.switch_weapon()
    t = [0]
    # Hold fire while the first outpost comes down, then torpedo it
    rec.run(40, record=False, each_frame=lambda: fly(game, t, 500, y=860, shoot=False))
    rec.run(90, each_frame=lambda: fly(game, t, nearest_enemy_x(game), y=860, shoot=False))
    rec.run(270, each_frame=lambda: fly(game, t, nearest_enemy_x(game), y=860))
    rec.save("outposts.gif")


def boss_scenes():
    from src.game import groups as G
    game = new_game()
    rec = Recorder(game)
    for _ in range(4):
        game.player.level_up()
    show_planet(game, "lava", 30, 9, 760, 380)
    game.level.spawn_carrier()
    boss = G.G_BOSS.sprite
    t = [0]
    for _ in range(600):
        if boss.state.name != "MoveDown":
            break
        rec.run(1, record=False, each_frame=lambda: fly(game, t))
    boss._count_attack_interval = 10 ** 6
    # Let the stage title and the boss warning fade
    rec.run(180, record=False, each_frame=lambda: fly(game, t))

    boss._attack_ring()
    rec.run(75, each_frame=lambda: fly(game, t))
    boss._attack_laser()
    rec.run(200, each_frame=lambda: fly(game, t, speed=90, width=220))
    rec.save("boss.gif")

    if boss.laser_active():
        boss.laser.kill()
    for sprite in G.G_Enemy_Bullets.sprites():
        sprite.kill()
    boss.hit(10 ** 6)
    rec.run(boss.DEATH_DURATION + 45, each_frame=lambda: fly(game, t))
    rec.save("boss_death.gif")


def main():
    logging.disable(logging.CRITICAL)
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()
    # Default settings, whatever the local settings.json says
    sys.modules.setdefault("src.game.GameSettings", __import__("src.game.GameSettings", fromlist=["x"]))
    sys.modules["src.game.GameSettings"]._FILE = Path(tempfile.gettempdir()) / "lostviking-record-settings.json"
    random.seed(2)
    OUT.mkdir(parents=True, exist_ok=True)
    title_screen()
    patrol_scene()
    outposts_scene()
    boss_scenes()


if __name__ == "__main__":
    main()
