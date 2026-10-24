import asyncio
import pygame
from src.game.Game import Game


async def main():

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

    import sys
    sys.exit()
