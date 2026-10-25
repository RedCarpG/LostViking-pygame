# Pygame-LostViking

![img](https://github.com/RedCarpG/DOCS/blob/main/lost_viking/LostViking.png?raw=true)

![img](https://github.com/RedCarpG/DOCS/blob/main/lost_viking/LostViking2.png?raw=true)

![img](https://github.com/RedCarpG/DOCS/blob/main/lost_viking/LostViking_pixel.png?raw=true)

## Run

Desktop (Python 3.9+ with pygame):

```bash
python LostViking.py
```

Web (with [pygbag](https://pypi.org/project/pygbag/)), then open http://localhost:8000:

```bash
python -m pygbag --template static/lostviking.tmpl --icon static/favicon.png .
```

Add `--build` to only build `build/web` without starting the test server.

## Controls

| Key | Action |
| --- | --- |
| WASD or arrow keys | Move |
| Space | Shoot |
| E | Switch weapon (the Viking transforms) |
| Q | Nuclear bomb |
| Esc or P | Pause |
| Tab | Show / hide equipment panel |
| F3 | Show / hide FPS |

Volume, screen shake, screen flashes and the FPS counter can be changed in **Settings** (main menu or pause menu).
They are saved with the best score in `settings.json` (desktop) or the browser storage (web).

## Gameplay

- Survive the waves of Scouts, Phoenixes and Oracles until the Carrier comes (a WARNING tells you), then destroy it.
- Two weapons, as the StarCraft II Viking, switched with E (no shot while the Viking transforms):
  - **Twin gatling**: fast straight shots, the best against light ships (Interceptors, Phoenixes) and shields.
    From weapon level 4 its shots turn green and go through ships: one ship at level 4, two at level 5,
    30% less damage after each. A shield stops them.
  - **Lanzer Torpedoes**: homing torpedoes in salvos of pairs, extra damage against armored ships
    (Scouts, the Carrier).
- Supplies: weapon upgrade (5 levels, for both weapons), nuclear bomb, repair (or one more life when not damaged).
  They blink before they leave and fly to you once you are close.
- Losing a life costs the weapon upgrades: they drop from the wreck, pick them up again.
- Scouts weave, dive at you, strafe across the screen or stop to fire aimed bursts, alone or in formations.
- Phoenixes use a **Graviton Beam**: a dashed line shows where they aim, it locks and blinks, then fires.
  If it catches you, you are pulled toward the Phoenix and hard to steer: break its shield to get free.
- Oracles warp in and stay a while:
  - **Pulsar Beam**: the Oracle stops above you, a dashed line shows the beam charging, then it burns
    and follows you slowly. Move sideways.
  - **Stasis Ward**: dropped ahead of you, faint at first; once armed a dashed ring turns around it.
    Touching an armed ward freezes you in a crystal for over a second: no move, no shot, no bomb,
    but no damage either. Shoot the wards down.
- The Carrier gets angry below half health: its attacks come faster.

## Test mode

Choose **Test Mode** in the main menu to play with a test panel (press `` ` `` to show / hide it).
Each action has a key and can also be clicked: spawn any enemy or the boss, damage the boss,
level up the weapon, add bombs and lives, god mode, turn automatic spawning off and show hitboxes.
"Scout wave" brings a random Scout formation, "Oracle" warps one in.
Test mode scores do not count as best score.

## Development

Tests run without a window or a sound card:

```bash
pip install pytest
python -m pytest
```

`python tools/bench.py [frames] [--boss-at FRAME] [--god]` lets a bot play a round headless and prints the
time of the update and draw of each frame (mean, 95th percentile, worst). Set `LOSTVIKING_DEBUG=1` to log every
loaded asset and spawned enemy.
