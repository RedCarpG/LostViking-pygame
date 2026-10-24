import pygame
from src.game.groups import G_Player1
from src.game.animation.Effect import UIEffect
from src.game.animation.AnimeSprite import AnimeSprite
from src.helper.image.image_loader import get_image
from src.setting import COLOR, SCREEN_HEIGHT
from src.util.type import Size
from src.helper.font import FontEntity, get_font
from .UIState import UIState


class UIEquip:

    MOVE_SPEED = 3

    def __init__(self, surface) -> None:
        self.surface = surface
        self.player_g = G_Player1

        self.state = UIState.Entry

        # Main Surface
        # Copy: icons and texts are drawn onto it
        self.ui_equip = get_image("UI/Equip/Left.png").copy()
        self.ui_equip_rect = self.ui_equip.get_rect(
            bottom=SCREEN_HEIGHT-87, right=0)

        self.weapon_img = get_image("UI/Equip/Weapon0.png")
        self.wepon_rect = pygame.Rect(16, 24, 42, 42)
        self.bomb_img = get_image("UI/Equip/Bomb0.png")
        self.bomb_rect = pygame.Rect(16, 76, 42, 42)
        self._player_level = self.player_g.sprite.level
        self._player_bomb_count = self.player_g.sprite.bomb_count
        self.weapon_text = FontEntity(self.ui_equip, get_font("Equip"),
                                      (f"{self._player_level}/5"), color=COLOR.WHITE)
        self.weapon_text.rect.bottomright = (self.wepon_rect.right, self.wepon_rect.bottom + 2)
        self.bomb_text = FontEntity(self.ui_equip, get_font("Equip"),
                                    (f"{self._player_bomb_count}/3"), color=COLOR.WHITE)
        self.bomb_text.rect.bottomright = (self.bomb_rect.right, self.bomb_rect.bottom + 2)

        self.light1 = AnimeSprite(
            frames={
                "IDLE": get_image("UI/Equip/Left_LightYellow.png")
            },
            frame_size=Size([6, 10])
        )
        self.light1.rect.move_ip(84, 82)
        self.light1_effect = None
        self.light2 = AnimeSprite(
            frames={
                "IDLE": get_image("UI/Equip/Left_LightYellow.png")
            },
            frame_size=Size([6, 10])
        )
        self.light2.rect.move_ip(84, 94)
        self.light3 = AnimeSprite(
            frames={
                "IDLE": get_image("UI/Equip/Left_LightRed.png")
            },
            frame_size=Size([6, 10])
        )
        self.light3.rect.move_ip(84, 106)

        self.group_light = pygame.sprite.Group()
        self.group_light.add(self.light1)
        self.group_light.add(self.light2)
        self.group_light.add(self.light3)

    def update(self):
        self.group_light.update()
        if self.player_g.sprite.level != self._player_level:
            self._player_level = self.player_g.sprite.level
            self.weapon_text.change_text(f"{self._player_level}/5")
        if self.player_g.sprite.bomb_count != self._player_bomb_count:
            self._player_bomb_count = self.player_g.sprite.bomb_count
            if self._player_bomb_count == 0:
                self.light2.frames["IDLE"] = get_image(
                    "UI/Equip/Left_LightRed.png")
                self.bomb_text.change_color(COLOR.RED)
            else:
                self.light2.frames["IDLE"] = get_image(
                    "UI/Equip/Left_LightYellow.png")
                self.bomb_text.change_color(COLOR.WHITE)
            self.bomb_text.change_text(f"{self._player_bomb_count}/3")
        if self.state == UIState.Entry:
            self.ui_equip_rect.right += self.MOVE_SPEED
            if self.ui_equip_rect.left >= 0:
                self.ui_equip_rect.left = 0
                self.state = UIState.Idle
        elif self.state == UIState.Exit:
            self.ui_equip_rect.right -= self.MOVE_SPEED
            if self.ui_equip_rect.right <= 19:
                self.ui_equip_rect.right = 19
                self.state = UIState.Hidden

    def blit(self):
        self.surface.blit(self.ui_equip, self.ui_equip_rect)
        self.ui_equip.blit(self.weapon_img, self.wepon_rect)
        self.ui_equip.blit(self.bomb_img, self.bomb_rect)
        self.group_light.draw(self.ui_equip)
        self.weapon_text.blit()
        self.bomb_text.blit()

    def toggle_hidden(self):
        if self.state == UIState.Idle:
            self.state = UIState.Exit
        elif self.state == UIState.Hidden:
            self.state = UIState.Entry

    def toggle_green_light(self, id):
        if id == 1:
            if self.light1_effect is None:
                def cb_func():
                    self.light1_effect = None
                self.light1_effect = UIEffect(
                    self.ui_equip,
                    frames={
                        "IDLE": get_image("UI/Equip/Left_LightGreen.png")
                    },
                    frame_size=Size([6, 10]),
                    group=self.group_light,
                    offset=[self.light1.rect.x, self.light1.rect.y],
                    cb_func=cb_func
                )
        elif id == 2:
            UIEffect(
                self.ui_equip,
                frames={
                    "IDLE": get_image("UI/Equip/Left_LightGreen.png")
                },
                frame_size=Size([6, 10]),
                group=self.group_light,
                offset=[self.light2.rect.x, self.light2.rect.y]
            )
        else:
            UIEffect(
                self.ui_equip,
                frames={
                    "IDLE": get_image("UI/Equip/Left_LightGreen.png")
                },
                frame_size=Size([6, 10]),
                group=self.group_light,
                offset=[self.light3.rect.x, self.light3.rect.y]
            )
