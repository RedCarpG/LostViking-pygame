""" Headless benchmark: a bot plays a round, the time of every frame is measured

Development tool, run from the project root:
    python tools/bench.py [frames] [--boss-at FRAME] [--god] [--seed N]

--boss-at brings the Carrier in at that frame, --god makes the player invincible.
Prints the mean, 95th percentile and worst update / draw times, and the frames above 6 ms.
"""
import os
import sys
import time
import random
import logging
import argparse
import statistics

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame


class Keys:
    """ Stands for pygame.key.get_pressed(): the keys in `down` are held """
    down = set()

    def __getitem__(self, key):
        return key in self.down


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("frames", type=int, nargs="?", default=3000)
    parser.add_argument("--boss-at", type=int, default=None)
    parser.add_argument("--god", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    logging.disable(logging.CRITICAL)
    random.seed(args.seed)
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()
    keys = Keys()
    pygame.key.get_pressed = lambda: keys

    import src.game.GameSettings as settings_module
    # Do not touch the player's settings (best score)
    settings_module.GameSettings.save = classmethod(lambda cls: None)
    from src.game.Game import Game, GameState
    from src.game.TestMode import TestMode
    from src.game.animation import warmup
    from src.game.groups import G_Enemys, G_Enemy_Bullets
    from src.game.player.player_control import PLAYER1_CONTROL as C

    game = Game()
    warmup.finish()
    game.start_round(test_mode=False)

    def god_mode():
        if args.god:
            TestMode.god_mode = True
            game.apply_god_mode()

    def bot():
        """ Shoots all the time, dodges the closest bullet, else goes under the nearest enemy """
        keys.down = {C.SHOOT[0]}
        px, py = game.player.rect.center
        danger = next((b.rect.centerx - px for b in G_Enemy_Bullets
                       if -220 < b.rect.centery - py < 40 and abs(b.rect.centerx - px) < 60), None)
        targets = [e for e in G_Enemys if e.is_active and e.rect.bottom > 0]
        if danger is not None:
            keys.down.add(C.MOVE_LEFT[0] if danger > 0 else C.MOVE_RIGHT[0])
        elif targets:
            tx = min(targets, key=lambda e: abs(e.rect.centerx - px)).rect.centerx
            if abs(tx - px) > 10:
                keys.down.add(C.MOVE_RIGHT[0] if tx > px else C.MOVE_LEFT[0])
        if py < 700:
            keys.down.add(C.MOVE_DOWN[0])

    god_mode()
    updates, draws, slow, rounds = [], [], [], []
    for frame in range(args.frames):
        if frame == args.boss_at:
            game.level.spawn_carrier()
        if game.state == GameState.PLAYING:
            bot()
        else:
            rounds.append(game.state.name)
            game.restart()
            god_mode()
        start = time.perf_counter()
        game.step(draw=False)
        middle = time.perf_counter()
        game._draw()
        end = time.perf_counter()
        updates.append((middle - start) * 1000)
        draws.append((end - middle) * 1000)
        if end - start > 0.006:
            slow.append((frame, round((end - start) * 1000, 1)))

    def line(name, values):
        values = sorted(values)
        print(f"{name:7s} mean {statistics.mean(values):6.2f} ms   "
              f"p95 {values[int(len(values) * 0.95)]:6.2f} ms   max {values[-1]:7.2f} ms")

    print(f"{args.frames} frames")
    line("update", updates)
    line("draw", draws)
    line("total", [a + b for a, b in zip(updates, draws)])
    print("frames above 6 ms:", slow[:20])
    print("rounds ended:", rounds)


if __name__ == "__main__":
    main()
