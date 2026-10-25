""" Generate the synthesized sounds (src/asset/sound/Enemy/...)

    Stasis      the plane frozen by an Oracle's Stasis Ward: a crystal chime (bell-like partials,
                slightly detuned and trembling) over a short falling whoosh, about 0.9 s
    PowerDown   a Pylon destroyed, its cannons going dark: a falling whine with crackles, 0.8 s
    WarpSurge   the Stargate warping out the Carrier: a deep tone rising and trembling faster,
                a swelling rush of noise and a chime at the top, 3.4 s

Development tool, needs numpy and ffmpeg. Run from the project root:
    python tools/sound/make_sounds.py [Stasis PowerDown WarpSurge]   (all of them by default)
"""
import subprocess
import sys

import numpy as np

RATE = 22050
OUT = "src/asset/sound/Enemy/{}.ogg"


def chime(t, freqs=((1047, 1.0), (1568, 0.7), (2093, 0.5), (3136, 0.3)), decay=0.35):
    sound = np.zeros_like(t)
    # (frequency, loudness), each with a slightly detuned twin (shimmer)
    for freq, amp in freqs:
        for detune in (1.0, 1.006):
            sound += amp * np.sin(2 * np.pi * freq * detune * t)
    tremolo = 1 - 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * 12 * t))
    return sound * tremolo * np.exp(-t / decay)


def low_pass(noise, cutoff):
    """ One-pole low-pass, `cutoff` (Hz) can change over time """
    out = np.zeros_like(noise)
    alpha = 1 - np.exp(-2 * np.pi * cutoff / RATE)
    value = 0.0
    for i in range(noise.size):
        value += alpha[i] * (noise[i] - value)
        out[i] = value
    return out


def whoosh(t, rng):
    # Cut-off falling from 6 kHz to 800 Hz
    cutoff = 6000 * (800 / 6000) ** np.clip(t / 0.4, 0, 1)
    return low_pass(rng.uniform(-1, 1, t.size), cutoff) * np.minimum(1, t / 0.02) * np.exp(-t / 0.15)


def sweep(t, start, end, duration):
    """ Phase of a tone gliding from `start` to `end` Hz (exponential glide) """
    freq = start * (end / start) ** np.clip(t / duration, 0, 1)
    return 2 * np.pi * np.cumsum(freq) / RATE


def stasis():
    duration = 0.9
    t = np.arange(int(RATE * duration)) / RATE
    sound = chime(t) * 0.6 + whoosh(t, np.random.default_rng(7)) * 0.9
    return sound * np.minimum(1, (duration - t) / 0.05)


def power_down():
    duration = 0.8
    t = np.arange(int(RATE * duration)) / RATE
    rng = np.random.default_rng(11)
    phase = sweep(t, 900, 110, duration)
    whine = np.sin(phase) + 0.4 * np.sin(2 * phase) + 0.25 * np.sign(np.sin(0.5 * phase))
    # Crackles: short noise bursts, rarer toward the end
    crackle = rng.uniform(-1, 1, t.size) * (rng.random(t.size) < 0.02 * (1 - t / duration))
    crackle = low_pass(crackle * 6, np.full(t.size, 3000.0))
    envelope = np.minimum(1, t / 0.01) * (1 - t / duration) ** 1.5
    return (whine * 0.5 + crackle) * envelope


def warp_surge():
    duration = 3.4
    t = np.arange(int(RATE * duration)) / RATE
    rng = np.random.default_rng(5)
    rise = 2.8
    phase = sweep(t, 70, 560, rise)
    tone = np.sin(phase) + 0.5 * np.sin(1.5 * phase) + 0.3 * np.sin(2 * phase)
    # Trembles faster and faster
    tremolo = 1 - 0.45 * (0.5 + 0.5 * np.sin(sweep(t, 4, 28, rise)))
    cutoff = 300 * (5000 / 300) ** np.clip(t / rise, 0, 1)
    rush = low_pass(rng.uniform(-1, 1, t.size), cutoff)
    swell = np.clip(t / rise, 0, 1) ** 2
    sound = (tone * tremolo * 0.5 + rush * 1.2) * swell
    # The chime when the Carrier comes through
    top = t >= rise
    sound[top] += chime(t[top] - rise, decay=0.25) * 0.5
    fade = np.clip((duration - t) / (duration - rise), 0, 1)
    return sound * np.where(t < rise, 1, fade)


SOUNDS = {"Stasis": stasis, "PowerDown": power_down, "WarpSurge": warp_surge}


def save(name, sound):
    sound = sound / np.abs(sound).max() * 0.7
    pcm = (sound * 32767).astype("<i2").tobytes()
    path = OUT.format(name)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(RATE), "-ac", "1", "-i", "-",
                    "-c:a", "libvorbis", "-q:a", "4", path], input=pcm, check=True)
    print(f"saved {path}")


def main():
    for name in sys.argv[1:] or SOUNDS:
        save(name, SOUNDS[name]())


if __name__ == "__main__":
    main()
