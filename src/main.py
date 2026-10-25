import asyncio
import logging
import os
import sys
import pygame
from src.game.Game import Game
from src.setting import IS_WEB


def setup_logging():
    """ Warnings only by default: the browser console is slow and every message costs a frame.
    Set LOSTVIKING_DEBUG=1 to see every loaded asset and spawned enemy
    """
    level = logging.DEBUG if os.environ.get("LOSTVIKING_DEBUG") else logging.WARNING
    logging.basicConfig(stream=sys.stdout, level=level, format="%(levelname)s %(name)s: %(message)s")


async def main():
    setup_logging()

    # The web build mixes the sound on the same thread as the game: a bigger buffer (46 ms)
    # rides over a slow frame instead of breaking the music up (pygame's default is 11 ms)
    pygame.mixer.pre_init(44100, -16, 2, 2048 if IS_WEB else 512)
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()
    pygame.display.set_caption("Lost Viking")

    game = Game()
    await game.run()

    pygame.font.quit()
    pygame.mixer.quit()
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())

    sys.exit()
