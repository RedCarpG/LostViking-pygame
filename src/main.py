import asyncio
import logging
import os
import sys
import pygame
from src.game.Game import Game


def setup_logging():
    """ Warnings only by default: the browser console is slow and every message costs a frame.
    Set LOSTVIKING_DEBUG=1 to see every loaded asset and spawned enemy
    """
    level = logging.DEBUG if os.environ.get("LOSTVIKING_DEBUG") else logging.WARNING
    logging.basicConfig(stream=sys.stdout, level=level, format="%(levelname)s %(name)s: %(message)s")


async def main():
    setup_logging()

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
