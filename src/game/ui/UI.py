from enum import Enum

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
        if ui_type is None:
            self.ui_equip.toggle_hidden()
        elif ui_type == UIType.Equip:
            self.ui_equip.toggle_hidden()

    def handle_event(self, event):
        if event.type == EVENT_PLAYER_SHOOT:
            self.ui_equip.toggle_green_light(1)
        elif event.type == EVENT_PLAYER_BOMB:
            self.ui_equip.toggle_green_light(2)


# Silkscreen pixel font (SIL Open Font License, see Silkscreen-OFL.txt): (file, size, label).
# Sizes are multiples of 8 so every font pixel is a whole number of screen pixels
FONTS = [
    ("Silkscreen-Regular.ttf", 16, "HealthBar"),
    ("Silkscreen-Regular.ttf", 16, "Equip"),
    ("Silkscreen-Regular.ttf", 16, "Scoreboard"),
    ("Silkscreen-Regular.ttf", 16, "ScoreLabel"),
    ("Silkscreen-Bold.ttf", 32, "ScoreValue"),
    ("Silkscreen-Bold.ttf", 32, "MenuTitle"),
    ("Silkscreen-Regular.ttf", 24, "MenuText"),
    ("Silkscreen-Bold.ttf", 16, "FloatText"),
]

IMAGES = [
    "UI/Player/HealthBar.png",
    "UI/Player/LifeLight.png",
    "UI/Player/LifeLightEmpty.png",
    "UI/Player/LifeLightBlink.png",
    "UI/Player/BottomLeft.png",
    "UI/Player/Viking30.png",
    "UI/Player/Viking50.png",
    "UI/Player/Viking70.png",
    "UI/Player/Viking100.png",

    "UI/Equip/Left.png",
    "UI/Equip/Left_LightRed.png",
    "UI/Equip/Left_LightYellow.png",
    "UI/Equip/Left_LightGreen.png",
    "UI/Equip/Weapon0.png",
    "UI/Equip/Bomb0.png",

    "UI/Boss/MidTop.png",
    "UI/Boss/MidTop_HealthBar.png",
]


def load_asset_ui():
    from src.helper.image import load_images
    from src.helper.font import load_font
    for filename, size, label in FONTS:
        load_font(filename, size, label)
    load_images(IMAGES)

