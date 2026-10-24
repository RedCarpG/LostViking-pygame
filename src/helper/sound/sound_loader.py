import os
import logging
import pygame

log = logging.getLogger(__name__)

_sound_dir = os.path.join(os.path.split(
    os.path.abspath(__file__))[0], '../../asset/sound')


class NoneSound:
    """ Stands for a sound that could not be loaded: playing it does nothing """

    def __init__(self, sound_label):
        self.label = sound_label

    def play(self):
        pass

    def stop(self):
        pass


class _SoundBuffer(object):

    BUFFER = {}

    def __getitem__(self, key):
        if key not in self.BUFFER:
            # Warn once, then keep the silent stand-in
            log.warning("Sound [%s] not loaded", key)
            self.BUFFER[key] = NoneSound(key)
        return self.BUFFER[key]

    def __setitem__(self, key, item):
        self.BUFFER[key] = item

    def __delitem__(self, key):
        del self.BUFFER[key]

    def pop(self, key, default=None):
        return self.BUFFER.pop(key, default)


_SOUND = _SoundBuffer()
_MUSIC = pygame.mixer.music

# Volumes given when loading, scaled by the player's volume settings
_sound_base_volume = {}
_music_base_volume = 0.0
_volume_scale = {"sound": 1.0, "music": 1.0}


def play_sound(label):
    """ Play sound from _SOUND dictionary which is previously loaded
    :param label: Name tag of the sound effect
    """
    sound = _SOUND[label]
    sound.stop()
    sound.play()


def del_sound(label):
    """ Delete a key label from _SOUND which is not needed
    :param label: Name tag of the sound effect
    """
    _SOUND.pop(label, None)


def load_sound(filename, volume, label):
    """ Load a sound file from filename, and add label in the dictionary
    :param filename: Filename, in the sound_dir
    :param volume: Volume to be set for the sound effect
    :param label: Label tag in the dictionary
    """
    if not pygame.mixer or not pygame.mixer.get_init():
        log.warning("Mixer not initialized, sound [%s] not loaded", filename)
        _SOUND[label] = NoneSound(label)
        return

    full_path = os.path.join(_sound_dir, filename)

    try:
        sound = pygame.mixer.Sound(full_path)
        log.debug("Sound [%s] loaded", filename)
    except pygame.error:
        log.error("Can not find audio file: %s", full_path)
        raise SystemExit(str(pygame.get_error()))

    _sound_base_volume[label] = volume
    sound.set_volume(min(1.0, volume * _volume_scale["sound"]))
    _SOUND[label] = sound


def load_sounds(table) -> None:
    """ Load every sound of a table (an asset manifest) of (filename, volume, label), see load_sound """
    for filename, volume, label in table:
        load_sound(filename, volume, label)


def load_music(filename, volume):
    """ Load a sound file from filename to be played as music
    :param filename: Filename, in the sound_dir
    :param volume: Volume to be set for the music
    """
    if not pygame.mixer or not pygame.mixer.get_init():
        log.warning("Mixer not initialized, music [%s] not loaded", filename)
        return

    full_path = os.path.join(_sound_dir, filename)
    try:
        _MUSIC.load(full_path)
        log.debug("Music [%s] loaded", filename)
    except pygame.error:
        log.error("Can not find audio file: %s", full_path)
        raise SystemExit(str(pygame.get_error()))
    global _music_base_volume
    _music_base_volume = volume
    _MUSIC.set_volume(min(1.0, volume * _volume_scale["music"]))


def play_music(fade_ms=0):
    if pygame.mixer.get_init():
        _MUSIC.play(loops=-1, fade_ms=fade_ms)


def set_sound_volume_scale(scale):
    """ Scale every sound effect volume (1.0 keeps the volume given when loading) """
    _volume_scale["sound"] = scale
    for label, sound in _SOUND.BUFFER.items():
        if label in _sound_base_volume:
            sound.set_volume(min(1.0, _sound_base_volume[label] * scale))


def set_music_volume_scale(scale):
    """ Scale the music volume (1.0 keeps the volume given when loading) """
    _volume_scale["music"] = scale
    if pygame.mixer.get_init():
        _MUSIC.set_volume(min(1.0, _music_base_volume * scale))
