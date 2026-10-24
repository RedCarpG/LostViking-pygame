import os
import sys

import pygame
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

_sound_dir = os.path.join(os.path.split(
    os.path.abspath(__file__))[0], '../../asset/sound')


class NoneSound:
    def __init__(self, sound_label):
        self.label = sound_label

    def play(self):
        logging.warning("-- No sound played for {}".format(self.label))

    def stop(self):
        pass


class _SoundBuffer(object):

    BUFFER = {}

    def __getitem__(self, key):
        if key not in self.BUFFER:
            logging.warning(
                f"<WARNING> Sound [{key}] not loaded")
            return NoneSound(key)
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
    _SOUND[label].stop()
    _SOUND[label].play()


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

        logging.warning(
            "<WARNING> Mixer hasn't initialized, failed loading sound ！")
        _SOUND[label] = NoneSound(label)
        return

    full_path = os.path.join(_sound_dir, filename)

    try:
        sound = pygame.mixer.Sound(full_path)
        logging.info(f"<SUCCESS> Sound [{filename}] loaded ！")
    except pygame.error:
        logging.error(
            f'<ERROR> !!! Can not find audio file : {full_path}')
        raise SystemExit(str(pygame.get_error()))

    _sound_base_volume[label] = volume
    sound.set_volume(min(1.0, volume * _volume_scale["sound"]))
    _SOUND[label] = sound


def load_music(filename, volume):
    """ Load a sound file from filename to be played as music
    :param filename: Filename, in the sound_dir
    :param volume: Volume to be set for the music
    """

    if not pygame.mixer or not pygame.mixer.get_init():
        class NoneMusic:
            @classmethod
            def play(cls):
                logging.warning("-- No music played to play")

        logging.warning(
            "<WARNING> Mixer hasn't initialized, failed loading music！")
        return NoneMusic()

    if isinstance(filename, (list, tuple)):
        try:
            _MUSIC.load(os.path.join(_sound_dir, filename[0]))
        except pygame.error:
            logging.error('<ERROR> !!! Can not find audio file in: [{}]'.format(
                filename[0]))
            raise SystemExit(str(pygame.get_error()))

        for each_filename in filename[1:]:
            each_path = os.path.join(_sound_dir, each_filename)
            try:
                _MUSIC.queue(os.path.join(_sound_dir, each_path))
            except pygame.error:
                logging.error('<ERROR> !!! Can not find audio file in: [{}]'.format(
                    each_path))
                raise SystemExit(str(pygame.get_error()))
            logging.info("<SUCCESS> Music [{}] loaded !".format(each_path))
    else:
        full_path = os.path.join(_sound_dir, filename)
        try:
            _MUSIC.load(full_path)
            logging.info("<SUCCESS> Music [{}] loaded !".format(filename))
        except pygame.error:
            logging.error('<ERROR> !!! Can not find audio file in: [{}]'.format(
                full_path))
            raise SystemExit(str(pygame.get_error()))
    global _music_base_volume
    _music_base_volume = volume
    _MUSIC.set_volume(min(1.0, volume * _volume_scale["music"]))


def play_music():
    _MUSIC.play(loops=-1)


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
