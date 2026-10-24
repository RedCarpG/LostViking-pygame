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
