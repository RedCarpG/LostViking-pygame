
from .player_event_handler import detect_custom_event, reset_player_events
from .PlayerWeapon import PlayerWeapon
from .PlayerPlane import PlayerPlane
from .PlayerBomb import PlayerNucBomb
from .PlayerViking import PlayerViking, PlayerWeaponViking, PlayerTorpedoViking, PlayerBulletViking
from . import LanzerTorpedo

# Asset manifest of the player
IMAGES = [
    "PlayerPlane/bullet.png",
    "PlayerPlane/Bomb.png",
    # Preloaded: decoding this big sheet during the explosion froze the game
    "Bomb/NucExplosion.png",
    "PlayerPlane/BulletHit.png",
    "PlayerPlane/VikingBase.png",
    "PlayerPlane/VikingMoveNormal.png",
    "PlayerPlane/VikingMoveUp.png",
    "PlayerPlane/VikingDestroy.png",
    "PlayerPlane/VikingHit.png",
    "PlayerPlane/VikingInvincible.png",
]


def load_asset_player():
    from src.helper.image import load_images
    from src.helper.sound import load_sounds
    from src.setting import MAIN_VOLUME
    load_images(IMAGES)
    # (file, volume, label)
    load_sounds([
        ("Player/Shoot.ogg", MAIN_VOLUME - 0.3, "PLAYER_SHOOT"),
        ("Player/Explode.ogg", MAIN_VOLUME - 0.3, "PLAYER_DESTROY"),
        # Nuc bomb
        ("Bomb/Bomb.ogg", MAIN_VOLUME - 0.2, "BOMB_LAUNCH"),
        ("Bomb/BombExplode.ogg", MAIN_VOLUME, "BOMB_EXPLODE"),
        ("Error.ogg", MAIN_VOLUME - 0.2, "BOMB_ERROR"),
        # Lanzer Torpedoes, and the Viking transforming to each weapon
        ("Player/Torpedo.ogg", MAIN_VOLUME - 0.3, "TORPEDO_LAUNCH"),
        ("Player/TransformFighter.ogg", MAIN_VOLUME - 0.25, "TRANSFORM_FIGHTER"),
        ("Player/TransformAssault.ogg", MAIN_VOLUME - 0.25, "TRANSFORM_ASSAULT"),
    ])
    LanzerTorpedo.prepare()
