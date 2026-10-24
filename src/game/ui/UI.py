
from enum import Enum

from .UIPause import UIPause
from .UIPlayer import UIPlayer
from .UIBoss import UIBoss
from .UIEquip import UIEquip
from src.game.custom_events import EVENT_PLAYER_SHOOT, EVENT_PLAYER_BOMB


class UIType(Enum):
    Player = 0
    Equip = 1
    Boss = 2


class UI:

    def __init__(self, surface) -> None:
        load_asset_ui()
        self.ui_player = UIPlayer(surface)
        self.ui_boss = UIBoss(surface)
        self.ui_equip = UIEquip(surface)

    def update(self):
        self.ui_player.update()
        self.ui_boss.update()
        self.ui_equip.update()

    def blit(self):
        self.ui_player.blit()
        self.ui_boss.blit()
        self.ui_equip.blit()

    def toggle_hidden(self, ui_type: UIType = None):
        if ui_type == None:
            self.ui_equip.toggle_hidden()
        elif ui_type == UIType.Equip:
            self.ui_equip.toggle_hidden()

    def handle_event(self, event):
        if event.type == EVENT_PLAYER_SHOOT:
            self.ui_equip.toggle_green_light(1)
        elif event.type == EVENT_PLAYER_BOMB:
            self.ui_equip.toggle_green_light(2)


def load_asset_ui():
    from src.helper.image import load_image
    from src.helper.font import load_font

    load_font("arialbd.ttf", 15, "HealthBar")
    load_font("arial.ttf", 15, "Equip")
    load_font("Raleway-Regular.ttf", 20, "Scoreboard")
    load_font("Raleway-Regular.ttf", 15, "ScoreLabel")
    load_font("arialbd.ttf", 30, "ScoreValue")
    load_font("Raleway-Light.ttf", 72, "MenuTitle")
    load_font("Raleway-Regular.ttf", 26, "MenuText")

    load_image("UI/Player/HealthBar.png")
    load_image("UI/Player/LifeLight.png")
    load_image("UI/Player/LifeLightEmpty.png")
    load_image("UI/Player/LifeLightBlink.png")
    load_image("UI/Player/BottomLeft.png")
    load_image("UI/Player/Viking30.png")
    load_image("UI/Player/Viking50.png")
    load_image("UI/Player/Viking70.png")
    load_image("UI/Player/Viking100.png")

    load_image("UI/Equip/Left.png")
    load_image("UI/Equip/Left_LightRed.png")
    load_image("UI/Equip/Left_LightYellow.png")
    load_image("UI/Equip/Left_LightGreen.png")
    load_image("UI/Equip/Weapon0.png")
    load_image("UI/Equip/Bomb0.png")

    load_image("UI/Boss/MidTop.png")
    load_image("UI/Boss/MidTop_HealthBar.png")

