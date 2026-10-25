from src.game.animation.FloatingText import WEAPON_COLOR, MAX_COLOR
from src.game.player import PlayerPlane
from .SUPPLY_TYPE import SUPPLY_TYPE
from .Supply import Supply


class SupplyLevel(Supply):
    """ Weapon upgrade """
    TYPE = SUPPLY_TYPE.Level
    IMAGE = "Supply/SupplyLevel.png"
    GET_EFFECT = "Supply/SupplyGetLevel.png"
    GET_SOUND = "SUPPLY_LEVEL"

    def apply(self, player: PlayerPlane):
        if player.level_up():
            return f"WEAPON LV {player.level}", WEAPON_COLOR
        return "WEAPON MAX", MAX_COLOR
