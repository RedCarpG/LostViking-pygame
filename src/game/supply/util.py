import random
from .SUPPLY_TYPE import SUPPLY_TYPE
from .SupplyLife import SupplyLife
from .SupplyBomb import SupplyBomb
from .SupplyLevel import SupplyLevel
from .Supply import Supply

SUPPLIES = {each.TYPE: each for each in (SupplyLife, SupplyBomb, SupplyLevel)}


def get_supply_type(supply_type: SUPPLY_TYPE = None) -> type[Supply]:
    """ Supply class of `supply_type`, a random one if None """
    if supply_type is None:
        supply_type = random.choice(SUPPLY_TYPE.get_types())
    return SUPPLIES[supply_type]
