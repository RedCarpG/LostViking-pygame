""" Generate the stasis sound (src/asset/sound/Enemy/Stasis.ogg): the plane frozen by an Oracle's
Stasis Ward. A crystal chime (bell-like partials, slightly detuned and trembling) over a short
falling whoosh, about 0.9 s.

Development tool, needs numpy and ffmpeg. Run from the project root:
    python tools/sound/make_stasis.py
"""
import subprocess

import numpy as np

RATE = 22050
DURATION = 0.9
OUT = "src/asset/sound/Enemy/Stasis.ogg"


def chime(t):
    sound = np.zeros_like(t)
    # (frequency, loudness): C6, G6, C7, G7, each with a slightly detuned twin (shimmer)
    for freq, amp in ((1047, 1.0), (1568, 0.7), (2093, 0.5), (3136, 0.3)):
        for detune in (1.0, 1.006):
            sound += amp * np.sin(2 * np.pi * freq * detune * t)
    tremolo = 1 - 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * 12 * t))
    return sound * tremolo * np.exp(-t / 0.35)


def whoosh(t, rng):
    noise = rng.uniform(-1, 1, t.size)
    out = np.zeros_like(noise)
    # One-pole low-pass whose cut-off falls from 6 kHz to 800 Hz
    cutoff = 6000 * (800 / 6000) ** np.clip(t / 0.4, 0, 1)
    alpha = 1 - np.exp(-2 * np.pi * cutoff / RATE)
    value = 0.0
    for i in range(t.size):
        value += alpha[i] * (noise[i] - value)
        out[i] = value
    return out * np.minimum(1, t / 0.02) * np.exp(-t / 0.15)


def main():
    t = np.arange(int(RATE * DURATION)) / RATE
    sound = chime(t) * 0.6 + whoosh(t, np.random.default_rng(7)) * 0.9
    sound *= np.minimum(1, (DURATION - t) / 0.05)
    sound = sound / np.abs(sound).max() * 0.7
    pcm = (sound * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(RATE), "-ac", "1", "-i", "-",
                    "-c:a", "libvorbis", "-q:a", "4", OUT], input=pcm, check=True)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
