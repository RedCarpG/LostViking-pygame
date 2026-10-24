""" Player adjustable settings, saved between runs
(settings.json on desktop, the browser localStorage on the web)
"""
import json
import logging
from pathlib import Path
from src.setting import IS_WEB, SCREEN_SHAKE

_FILE = Path(__file__).resolve().parents[2] / "settings.json"
_STORAGE_KEY = "lostviking.settings"


class GameSettings:

    VOLUME_LEVELS = 10
    # Volume level matching the original sound mix
    DEFAULT_VOLUME = 5

    music_volume = DEFAULT_VOLUME
    sound_volume = DEFAULT_VOLUME
    screen_shake = SCREEN_SHAKE
    show_fps = False
    # Best score of a normal round (test mode rounds do not count)
    best_score = 0

    _SAVED = ["music_volume", "sound_volume", "screen_shake", "show_fps", "best_score"]

    @classmethod
    def music_scale(cls) -> float:
        return cls.music_volume / cls.DEFAULT_VOLUME

    @classmethod
    def sound_scale(cls) -> float:
        return cls.sound_volume / cls.DEFAULT_VOLUME

    @classmethod
    def apply(cls) -> None:
        """ Apply the volume settings to the loaded sounds and the music """
        from src.helper.sound import set_music_volume_scale, set_sound_volume_scale
        set_music_volume_scale(cls.music_scale())
        set_sound_volume_scale(cls.sound_scale())

    # ------------------ Persistence ------------------

    @classmethod
    def load(cls) -> None:
        try:
            if IS_WEB:
                import platform
                text = platform.window.localStorage.getItem(_STORAGE_KEY)
            else:
                text = _FILE.read_text(encoding="utf-8") if _FILE.is_file() else None
            if text:
                data = json.loads(str(text))
                for name in cls._SAVED:
                    if name in data:
                        setattr(cls, name, type(getattr(cls, name))(data[name]))
        except Exception as e:
            logging.warning(f"<WARNING> Settings not loaded: {e}")
        cls.music_volume = max(0, min(cls.VOLUME_LEVELS, cls.music_volume))
        cls.sound_volume = max(0, min(cls.VOLUME_LEVELS, cls.sound_volume))
        cls.best_score = max(0, cls.best_score)

    @classmethod
    def save(cls) -> None:
        text = json.dumps({name: getattr(cls, name) for name in cls._SAVED})
        try:
            if IS_WEB:
                import platform
                platform.window.localStorage.setItem(_STORAGE_KEY, text)
            else:
                _FILE.write_text(text, encoding="utf-8")
        except Exception as e:
            logging.warning(f"<WARNING> Settings not saved: {e}")
