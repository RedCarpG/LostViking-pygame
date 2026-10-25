# Pixel art tools

The game uses a pixel-art style: hard edges, small palettes, no smooth gradients.

| What | How it is made |
| --- | --- |
| Ships and enemies (`src/asset/image/Enemy`, `PlayerPlane`, ...) | Original pixel art, drawn at 1x |
| Oracle (`src/asset/image/Enemy/Oracle`) | `make_oracle.py`, 1x, 6 frames per sheet |
| Asteroids (`src/asset/image/Enemy/Asteroid`) | `make_asteroids.py`, 16 frames of a turn, lit again in every frame, drawn at 2x |
| Structures (`src/asset/image/Structure`): Terran Starport, outpost platforms, Pylon, Photon Cannon, Stargate | `make_structures.py`, drawn at 2x |
| HUD panels, lights and icons (`src/asset/image/UI`) | `make_hud.py`, drawn at half size and scaled 2x |
| Background nebula (`src/asset/image/Nebula.png`) | `make_nebula.py`, 500x500, drawn at 2x by the game |
| Text | Silkscreen pixel font (`src/asset/font`, SIL Open Font License), sizes in multiples of 8 |
| Turning enemies | RotSprite rotation in 32 directions (`src/game/animation/rotsprite.py`) |
| Explosions | Drawn by the game at 2x (`src/game/animation/Explosion.py`) |
| Carrier laser | Drawn by the game at 2x (`src/game/level/level1/CarrierLaser.py`) |
| Planets | Random on every run, drawn by the game at 2x (`src/game/ui/Planets.py`) |
| Red screen edges, WARNING banner | Drawn by the game at 2x (`src/game/animation/ScreenFX.py`) |
| Muzzle flashes, transform ring | Drawn by the game at 2x (`src/game/animation/MuzzleFlash.py`, `TransformRing.py`) |
| Lanzer Torpedoes and their smoke | Drawn by the game at 2x, turned with RotSprite (`src/game/player/LanzerTorpedo.py`) |
| Phoenix Graviton Beam | Drawn by the game on the 2x grid (`src/game/level/level1/GravitonBeam.py`) |
| Oracle Pulsar Beam, Stasis Ward and crystal | Drawn by the game at 2x (`src/game/level/level1/Oracle.py`) |
| Protoss warp-in | Drawn by the game from the ship's shape (`src/game/level/level1/WarpIn.py`) |
| Route on the left edge, stage titles | Drawn by the game at 2x (`src/game/ui/UIRoute.py`, `ScreenFX.py`) |

The effects drawn by the game share the helpers in `src/game/animation/pixel_fx.py`
(ordered dither, value noise, nearest-neighbour 2x scaling). Explosions, the laser and the
screen effects are drawn while the main menu shows (`src/game/animation/warmup.py`); planets are drawn a
little each frame while the sky waits for the next one.

## Generate the images

Run from the project root (needs `numpy` for the nebula):

```bash
python tools/pixel_art/make_hud.py
python tools/pixel_art/make_nebula.py
python tools/pixel_art/make_oracle.py
python tools/pixel_art/make_asteroids.py
python tools/pixel_art/make_structures.py
```

The sprite generators share their shading helpers (`shading.py`). The synthesized sounds (stasis,
pylon power-down, Stargate warp surge) are made by `python tools/sound/make_sounds.py`
(needs `numpy` and `ffmpeg`).

## Edit them in Aseprite

`art/` holds Aseprite copies at their drawing size (HUD: half size, so one pixel is one art pixel).
After editing, export back to the game at 2x (nearest neighbor, pixels stay sharp), for example:

```bash
Aseprite -b art/UI/Player/BottomLeft.aseprite --scale 2 --save-as src/asset/image/UI/Player/BottomLeft.png
Aseprite -b art/Nebula.aseprite --save-as src/asset/image/Nebula.png
```

Keep the same image sizes: the game draws bars, lights and icons at fixed positions
(see the comments in `make_hud.py`). Running the generators again overwrites hand edits.
