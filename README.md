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
| WASD | Move |
| Space | Shoot |
| Q | Nuclear bomb |
| Esc | Pause |
| Tab | Show / hide equipment panel |
| F3 | Show / hide FPS |

Volume, screen shake and the FPS counter can be changed in **Settings** (main menu or pause menu).
They are saved in `settings.json` (desktop) or the browser storage (web).

## Test mode

Choose **Test Mode** in the main menu to play with a test panel (press `` ` `` to show / hide it).
Each action has a key and can also be clicked: spawn any enemy or the boss, damage the boss,
level up the weapon, add bombs and lives, god mode, turn automatic spawning off and show hitboxes.
Test mode scores do not count as best score.
