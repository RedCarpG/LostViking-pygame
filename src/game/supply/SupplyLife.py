from src.game.animation.FloatingText import LIFE_COLOR, MAX_COLOR
from src.game.player import PlayerPlane
from .SUPPLY_TYPE import SUPPLY_TYPE
from .Supply import Supply


class SupplyLife(Supply):
    """ Repairs the plane, or gives one more life when it is not damaged """
    TYPE = SUPPLY_TYPE.Life
    IMAGE = "Supply/SupplyLife.png"
    GET_EFFECT = "Supply/SupplyGetLife.png"
    GET_SOUND = "SUPPLY_LIFE"

    def apply(self, player: PlayerPlane):
        if player.add_health():
            return "REPAIRED", LIFE_COLOR
        if player.add_life():
            return "+1 LIFE", LIFE_COLOR
        return "LIVES MAX", MAX_COLOR
