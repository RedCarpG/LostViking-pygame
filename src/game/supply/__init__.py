from .Supply import Supply
from .SupplyLife import SupplyLife
from .SupplyBomb import SupplyBomb
from .SupplyLevel import SupplyLevel
from .supply_event import supply_event_config, update_supply_timer, supply_events_handler, drop_supply_event
from .SUPPLY_TYPE import SUPPLY_TYPE
from .util import get_supply_type

# Asset manifest of the supplies
IMAGES = [
    "Supply/SupplyBase.png",
    "Supply/SupplyLife.png",
    "Supply/SupplyBomb.png",
    "Supply/SupplyLevel.png",
    "Supply/SupplyDrop.png",
    "Supply/SupplyGetBomb.png",
    "Supply/SupplyGetLevel.png",
    "Supply/SupplyGetLife.png",
]


def load_asset_supply():
    from src.helper.image import load_images
    from src.helper.sound import load_sounds
    from src.setting import MAIN_VOLUME
    load_sounds([
        ("Supply/Life.ogg", MAIN_VOLUME - 0.3, "SUPPLY_LIFE"),
        ("Supply/Upgrade.ogg", MAIN_VOLUME - 0.3, "SUPPLY_LEVEL"),
        ("Supply/NucReady.ogg", MAIN_VOLUME - 0.3, "SUPPLY_BOMB"),
    ])
    supply_event_config()
    load_images(IMAGES)
