import pygame
from src.game.groups import G_Player1
from src.game.animation.Effect import UIEffect
from src.game.animation.AnimeSprite import AnimeSprite
from src.helper.image.image_loader import get_image
from src.setting import COLOR, SCREEN_HEIGHT
from src.util.type import Size
from src.helper.font import FontEntity, get_font
from src.game.player import PlayerPlane
from src.game.animation.TransformRing import SWITCH_COLORS
from .UIState import UIState


class UIEquip:

    MOVE_SPEED = 3
    # Icon and display slot of each weapon of the plane (the bomb is in the middle slot)
    WEAPON_ICONS = ["UI/Equip/Weapon0.png", "UI/Equip/Torpedo0.png"]
    WEAPON_SLOTS = [(16, 24), (16, 128)]
    # The weapon not in use is dimmed
    DIM = (100, 100, 120)

    def __init__(self, surface) -> None:
        self.surface = surface
        self.player_g = G_Player1

        self.state = UIState.Entry

        # Main Surface
        # Copy: drawn again from the empty panel every frame, then icons and texts on it
        self._panel = get_image("UI/Equip/Left.png")
        self.ui_equip = self._panel.copy()
        self.ui_equip_rect = self.ui_equip.get_rect(
            bottom=SCREEN_HEIGHT-87, right=0)

        # Weapons: (icon, dimmed icon, slot) each, the level is shared
        self.weapons = []
        for name, pos in zip(self.WEAPON_ICONS, self.WEAPON_SLOTS):
            icon = get_image(name)
            dim = icon.copy()
            dim.fill(self.DIM, special_flags=pygame.BLEND_RGB_MULT)
            self.weapons.append((icon, dim, pygame.Rect(pos, (42, 42))))
        self.bomb_img = get_image("UI/Equip/Bomb0.png")
        self.bomb_rect = pygame.Rect(16, 76, 42, 42)
        self._player_level = self.player_g.sprite.level
        self._player_bomb_count = self.player_g.sprite.bomb_count
        self._level_max = self.player_g.sprite.weapon.LEVEL_MAX
        self.weapon_texts = []
        for icon, dim, slot in self.weapons:
            text = FontEntity(self.ui_equip, get_font("Equip"),
                              (f"{self._player_level}/{self._level_max}"), color=COLOR.WHITE)
            text.rect.bottomright = (slot.right, slot.bottom + 2)
            self.weapon_texts.append(text)
        self._time = 0
        self.bomb_text = FontEntity(self.ui_equip, get_font("Equip"),
                                    (f"{self._player_bomb_count}/{PlayerPlane.BOMB_COUNT_MAX}"), color=COLOR.WHITE)
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
        self._time += 1
        self.group_light.update()
        if self.player_g.sprite.level != self._player_level:
            self._player_level = self.player_g.sprite.level
            for text in self.weapon_texts:
                text.change_text(f"{self._player_level}/{self._level_max}")
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
            self.bomb_text.change_text(f"{self._player_bomb_count}/{PlayerPlane.BOMB_COUNT_MAX}")
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
        # Draw the icons, lights and texts on the panel first, then the panel on the screen
        self.ui_equip.blit(self._panel, (0, 0))
        player = self.player_g.sprite
        for index, ((icon, dim, slot), text) in enumerate(zip(self.weapons, self.weapon_texts)):
            active = index == player.weapon_index
            self.ui_equip.blit(icon if active else dim, slot)
            text.blit()
            # Frame around the weapon in use, blinking while the plane transforms
            if active and not (player.transforming and (self._time // 4) % 2):
                pygame.draw.rect(self.ui_equip, SWITCH_COLORS[index % len(SWITCH_COLORS)], slot.inflate(2, 2), 2)
        self.ui_equip.blit(self.bomb_img, self.bomb_rect)
        self.group_light.draw(self.ui_equip)
        self.bomb_text.blit()
        self.surface.blit(self.ui_equip, self.ui_equip_rect)

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
