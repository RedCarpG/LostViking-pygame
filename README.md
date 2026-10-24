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
| Q | Nuclear bomb |
| Esc or P | Pause |
| Tab | Show / hide equipment panel |
| F3 | Show / hide FPS |

Volume, screen shake, screen flashes and the FPS counter can be changed in **Settings** (main menu or pause menu).
They are saved with the best score in `settings.json` (desktop) or the browser storage (web).

## Gameplay

- Survive the waves of Scouts and Phoenixes until the Carrier comes (a WARNING tells you), then destroy it.
- Supplies: weapon upgrade (5 levels), nuclear bomb, repair (or one more life when not damaged).
  They blink before they leave and fly to you once you are close.
- Losing a life costs the weapon upgrades: they drop from the wreck, pick them up again.
- The Carrier gets angry below half health: its attacks come faster.

## Test mode

Choose **Test Mode** in the main menu to play with a test panel (press `` ` `` to show / hide it).
Each action has a key and can also be clicked: spawn any enemy or the boss, damage the boss,
level up the weapon, add bombs and lives, god mode, turn automatic spawning off and show hitboxes.
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
