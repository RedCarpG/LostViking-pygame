from src.game.animation.Effect import Effect
from src.util.type import Size, Pos
from src.helper.image import get_image
from src.game.player import PlayerPlane
from src.helper.sound import play_sound
from .Supply import Supply
from .SUPPLY_TYPE import SUPPLY_TYPE


class SupplyLevel(Supply):
    TYPE = SUPPLY_TYPE.Level

    def __init__(self, pos: Pos = None):
        super().__init__(pos,
                         frames={
                             "BASE": get_image("Supply/SupplyBase.png"),
                             "IDLE": get_image("Supply/SupplyLevel.png")
                         },
                         frame_size=None
                         )

    def get_by_player(self, player: PlayerPlane):
        Effect(
            pos=Pos(self.rect.center),
            frames={
                "IDLE": get_image("Supply/SupplyGetLevel.png")
            },
            frame_size=Size([50, 50])
        )
        player.level_up()
        play_sound("SUPPLY_LEVEL")
        return super().get_by_player(player)
