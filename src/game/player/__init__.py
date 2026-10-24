
from .player_event_handler import detect_custom_event, stop_player_shoot, reset_player_events
from .PlayerWeapon import PlayerWeapon
from .PlayerPlane import PlayerPlane
from .PlayerBomb import PlayerNucBomb
from .PlayerViking import PlayerViking, PlayerWeaponViking, PlayerBulletViking


def load_asset_player():
    from src.helper.image import load_image
    load_image("PlayerPlane/bullet.png")
    load_image("PlayerPlane/Bomb.png")
    load_image("PlayerPlane/BulletHit.png")

    load_image("PlayerPlane/VikingBase.png")
    load_image("PlayerPlane/VikingMoveNormal.png")
    load_image("PlayerPlane/VikingMoveUp.png")
    load_image("PlayerPlane/VikingMoveNormal.png")
    load_image("PlayerPlane/VikingDestroy.png")
    load_image("PlayerPlane/VikingHit.png")
    load_image("PlayerPlane/VikingInvincible.png")
    # Init sound
    from src.helper.sound import load_sound
    from src.setting import MAIN_VOLUME
    # Player
    load_sound("Player/Shoot.wav", MAIN_VOLUME - 0.3, "PLAYER_SHOOT")
    load_sound("Player/Explode.wav", MAIN_VOLUME - 0.3, "PLAYER_DESTROY")
    # Nuc bomb
    load_sound("Bomb/Bomb.wav", MAIN_VOLUME - 0.2, "BOMB_LAUNCH")
    load_sound("Bomb/BombExplode.wav", MAIN_VOLUME, "BOMB_EXPLODE")
    load_sound("Error.wav", MAIN_VOLUME - 0.2, "BOMB_ERROR")
