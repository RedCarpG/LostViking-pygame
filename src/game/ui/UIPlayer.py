
import pygame
from src.game.groups import G_Player1
from src.game.animation.Effect import AttachEffect, UIEffect
from src.game.animation.AnimeSprite import AnimeSprite
from src.helper.image.image_loader import get_image
from src.setting import COLOR, SCREEN_HEIGHT
from src.util.type import Size
from .UIState import UIState
from .HealthBar import HealthBar


class UIPlayer:

    MOVE_SPEED = 3

    def __init__(self, surface) -> None:
        self.surface = surface
        self.player_g = G_Player1

        self.state = UIState.Entry

        # Main Surface
        self.ui_player = get_image("UI/Player/BottomLeft.png")
        self.ui_player_rect = self.ui_player.get_rect(
            top=SCREEN_HEIGHT, left=0)

        # Health Bar
        self.health_bar_img = get_image("UI/Player/HealthBar.png")
        self.health_bar_img_rect = self.health_bar_img.get_rect().move(12, 58)
        self.health_bar = HealthBar(
            self.ui_player, pygame.Rect(15, 61, 215, 20), 100)

        # Life Light image
        self.lifelight_img = AnimeSprite(
            frames={
                "IDLE": get_image("UI/Player/LifeLight.png")
            },
            frame_size=Size([19, 6]))
        self.lifelight_img.rect.move_ip(99, 23)
        self.lifelight_empty_img = get_image("UI/Player/LifeLightEmpty.png")
        self.lifelight_blink = UIEffect(
            self.ui_player,
            frames={
                "IDLE": get_image("UI/Player/LifeLightBlink.png")
            },
            frame_size=Size([19, 6]),
            loop=True,
            offset=[self.lifelight_img.rect.x, self.lifelight_img.rect.y]
        )

        # Player image
        self.player_img = get_image("UI/Player/Viking100.png")
        self.player_img_rect = self.player_img.get_rect()
        self.player_img_rect.center = (36, 30)
        self.player_dmg = UIEffect(
            self.ui_player,
            frames={
                "IDLE": get_image("UI/Player/Viking70.png")
            },
            frame_size=Size([48, 37]),
            loop=True,
            offset=[self.player_img_rect.x, self.player_img_rect.y]
        )
        self.player_health = self.player_g.sprite.health

    def update(self):
        if self.state == UIState.Entry:
            self.ui_player_rect.top -= self.MOVE_SPEED
            if self.ui_player_rect.bottom <= SCREEN_HEIGHT:
                self.ui_player_rect.bottom = SCREEN_HEIGHT
                self.state = UIState.Idle
        self.lifelight_img.update()
        self.lifelight_blink.update()
        self.player_dmg.update()
        self.health_bar.update(self.player_g.sprite.health)
        if self.player_health != self.player_g.sprite.health:
            self.player_health = self.player_g.sprite.health
            if self.player_health <= 30:
                self.player_dmg.frames["IDLE"] = get_image(
                    "UI/Player/Viking30.png")
            elif self.player_health <= 50:
                self.player_dmg.frames["IDLE"] = get_image(
                    "UI/Player/Viking50.png")
            elif self.player_health <= 70:
                self.player_dmg.frames["IDLE"] = get_image(
                    "UI/Player/Viking70.png")

    def blit(self):
        for i in range(5):
            if i < self.player_g.sprite.life:
                self.ui_player.blit(
                    self.lifelight_img.image, self.lifelight_img.rect.move(i*23, 0))
            else:
                self.ui_player.blit(
                    self.lifelight_empty_img, self.lifelight_img.rect.move(i*23, 0))

        if self.player_g.sprite.life <= 1:
            self.lifelight_blink.blit()
        self.health_bar.blit()
        self.ui_player.blit(self.health_bar_img, self.health_bar_img_rect)
        self.ui_player.blit(self.player_img, self.player_img_rect)
        if self.player_g.sprite.health <= 70:
            self.player_dmg.blit()
        self.surface.blit(self.ui_player, self.ui_player_rect)
