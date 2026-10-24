from src.game.animation.FloatingText import BOMB_COLOR, MAX_COLOR
from src.game.player import PlayerPlane
from .SUPPLY_TYPE import SUPPLY_TYPE
from .Supply import Supply


class SupplyBomb(Supply):
    """ One more nuclear bomb """
    TYPE = SUPPLY_TYPE.Bomb
    IMAGE = "Supply/SupplyBomb.png"
    GET_EFFECT = "Supply/SupplyGetBomb.png"
    GET_SOUND = "SUPPLY_BOMB"

    def apply(self, player: PlayerPlane):
        if player.add_bomb():
            return "+1 BOMB", BOMB_COLOR
        return "BOMBS MAX", MAX_COLOR
