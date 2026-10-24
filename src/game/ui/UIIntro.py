import pygame
from pygame.locals import *
from src.helper.image import get_image
from src.helper.font import load_font, get_font, FontEntity, del_font
from src.util.type import Pos
from src.setting import SCREEN_HEIGHT, SCREEN_WIDTH, COLOR
from src.game.custom_events import EVENT_START


class UIIntro:

    def __init__(self, surface) -> None:
        load_font("arialbd.ttf", 150, "Title")
        load_font("arialbd.ttf", 30, "Intro")
        self.surface = surface

        self.title_text = FontEntity(self.surface, get_font("Title"),
                                     ("Lost Viking"), color=COLOR.WHITE)
        self.title_text.move_center((SCREEN_WIDTH/2, SCREEN_HEIGHT/5 * 2))

        self.intro_text = FontEntity(self.surface, get_font("Intro"),
                                     ("Press any key to start"), color=COLOR.WHITE)
        self.intro_text.move_center((SCREEN_WIDTH/2, SCREEN_HEIGHT/5 * 3))

        self.count_flash = 0

    def blit(self):
        self.title_text.blit()
        if self.count_flash < 50:
            self.intro_text.blit()
        self.count_flash = (self.count_flash + 1) % 100

    def handle_event(self, event):

        if event.type == pygame.KEYUP:
            if event.key == K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            else:
                pygame.event.post(pygame.event.Event(EVENT_START))

            return True

        return False

    def __del__(self):
        del_font("Title")
        del_font("Intro")
