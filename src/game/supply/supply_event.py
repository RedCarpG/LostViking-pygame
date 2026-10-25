import random
import pygame
from src.game.animation.Effect import Effect
from src.helper.image import get_image
from src.util.type import Pos, Size
from src.setting import SCREEN_WIDTH
from src.game.groups import G_Supplies
from .SUPPLY_TYPE import SUPPLY_TYPE
from .util import get_supply_type


EVENT_ADD_SUPPLY = pygame.event.custom_type()
EVENT_DROP_SUPPLY = pygame.event.custom_type()

# Frames between two random supplies (35s at 60 FPS)
ADD_SUPPLY_INTERVAL = 35 * 60
# Frames after a drop before an enemy can drop another one (10s at 60 FPS).
# Counted in game frames, so time on the pause menu does not count
DROP_COOLDOWN = 10 * 60
# No drop while this many supplies are already on screen
DROP_MAX_ON_SCREEN = 2

_count_add_supply = 0
_count_drop_cooldown = 0


def supply_event_config():
    """ Reset the supply timers, called when a round starts """
    global _count_add_supply, _count_drop_cooldown
    _count_add_supply = 0
    _count_drop_cooldown = 0


def update_supply_timer():
    """ Called every frame while playing, posts EVENT_ADD_SUPPLY periodically
    (pygame.time.set_timer is not available on WASM)
    """
    global _count_add_supply, _count_drop_cooldown
    _count_add_supply += 1
    if _count_add_supply >= ADD_SUPPLY_INTERVAL:
        _count_add_supply = 0
        pygame.event.post(pygame.event.Event(EVENT_ADD_SUPPLY))
    if _count_drop_cooldown > 0:
        _count_drop_cooldown -= 1


def supply_events_handler(event):
    global _count_drop_cooldown
    if event.type == EVENT_ADD_SUPPLY:
        pos = Pos(
            [random.randint(int(SCREEN_WIDTH/3), int(2 * SCREEN_WIDTH/3)), -50])
        get_supply_type()(pos)

    elif event.type == EVENT_DROP_SUPPLY:
        if _count_drop_cooldown > 0 or len(G_Supplies) >= DROP_MAX_ON_SCREEN:
            return
        Effect(
            pos=event.pos,
            frames={
                "IDLE": get_image("Supply/SupplyDrop.png")
            },
            frame_size=Size([50, 50]))
        _count_drop_cooldown = DROP_COOLDOWN
        get_supply_type(event.supply_type)(event.pos)


def drop_supply_event(pos: Pos, supply_type: SUPPLY_TYPE = None):

    pygame.event.post(pygame.event.Event(
        EVENT_DROP_SUPPLY, {"pos": pos, "supply_type": supply_type}))
