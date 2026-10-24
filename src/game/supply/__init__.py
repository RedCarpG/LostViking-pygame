import random
from .Supply import Supply
from .SupplyLife import SupplyLife
from .SupplyBomb import SupplyBomb
from .SupplyLevel import SupplyLevel
from .supply_event import supply_event_config, update_supply_timer, supply_events_handler, drop_supply_event
from .SUPPLY_TYPE import SUPPLY_TYPE
from .util import get_supply_type


def load_asset_supply():
    from src.helper.sound import load_sound
    from src.setting import MAIN_VOLUME
    load_sound("Supply/Life.ogg", MAIN_VOLUME - 0.3, "SUPPLY_LIFE")
    load_sound("Supply/Upgrade.ogg", MAIN_VOLUME - 0.3, "SUPPLY_LEVEL")
    load_sound("Supply/NucReady.ogg", MAIN_VOLUME - 0.3, "SUPPLY_BOMB")
    from src.helper.image import load_image
    supply_event_config()
    load_image("Supply/SupplyBase.png")
    load_image("Supply/SupplyLife.png")
    load_image("Supply/SupplyBomb.png")
    load_image("Supply/SupplyLevel.png")
    load_image("Supply/SupplyDrop.png")
    load_image("Supply/SupplyGetBomb.png")
    load_image("Supply/SupplyGetLevel.png")
    load_image("Supply/SupplyGetLife.png")
