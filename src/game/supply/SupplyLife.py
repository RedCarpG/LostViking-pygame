from src.util.type import Size, Pos
from src.game.animation.Effect import Effect
from src.helper.image import get_image
from src.game.player import PlayerPlane
from src.helper.sound import play_sound
from .Supply import Supply
from .SUPPLY_TYPE import SUPPLY_TYPE


class SupplyLife(Supply):
    TYPE = SUPPLY_TYPE.Life

    def __init__(self, pos: Pos = None):
        super().__init__(pos,
                         frames={
                             "BASE": get_image("Supply/SupplyBase.png"),
                             "IDLE": get_image("Supply/SupplyLife.png")
                         },
                         frame_size=None
                         )

    def get_by_player(self, player: PlayerPlane):
        if not player.add_health():
            player.add_life()
        play_sound("SUPPLY_LIFE")
        Effect(
            pos=Pos(self.rect.center),
            frames={
                "IDLE": get_image("Supply/SupplyGetLife.png")
            },
            frame_size=Size([50, 50])
        )
        return super().get_by_player(player)
