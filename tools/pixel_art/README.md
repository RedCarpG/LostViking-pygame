# Pixel art tools

The game uses a chibi pixel-art style: round, chunky shapes, cel shading (a base color, a shadow
band, a light band and a highlight, no smooth gradients), and big pixels: one art pixel is a 2x2
block of screen pixels everywhere (sprites, background, effects). Ships, rocks and the structures
that can be shot have a dark outline and a white rim around it, so they stand out of the dark
space like stickers. Bullets have the dark outline only; scenery (platforms, the Terran Starport)
has no rim.

## Sprites are stored at art size

The images in `src/asset/image/PlayerPlane`, `Enemy`, `Supply`, `Structure` and `Bomb` are at
art size (one file pixel is one art pixel). The game scales them 2x when it loads them
(`ART_SCALE` in `src/helper/image/image_loader.py`) and keeps the art-size image: turning sprites
(RotSprite, bullets) are turned at art size, then scaled, so their pixels stay on the art grid.
Edit them at art size; offsets in the code (guns, noses, pads) are in screen pixels.

| What | How it is made |
| --- | --- |
| The Viking, its bullet and bomb, the nuke blast, the HUD portraits | `make_player.py` |
| Scout, Interceptor, Phoenix (with its shield bubble), Carrier | `make_enemies.py` |
| Oracle | `make_oracle.py` |
| Enemy bullets and their hit spark, the Carrier orbs | `make_bullets.py` |
| Supplies and their pickup effects | `make_supplies.py` |
| Asteroids (16 frames of a turn, lit again in every frame) | `make_asteroids.py` |
| Structures: Terran Starport, outpost platforms, Pylon, Photon Cannon, Stargate | `make_structures.py` |
| HUD panels, lights and icons (`src/asset/image/UI`, stored at screen size) | `make_hud.py`, drawn at half size and scaled 2x |
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

The sprite generators share the chibi style in `chibi.py` (palettes, shapes on a design grid,
cel and dome shading, the outline and the white rim, hit / blink / destroy overlay sheets) and
the shape helpers in `shading.py`. The effects drawn by the game share the helpers in
`src/game/animation/pixel_fx.py` (ordered dither, value noise, nearest-neighbour 2x scaling).
Explosions, the laser and the screen effects are drawn while the main menu shows
(`src/game/animation/warmup.py`); planets are drawn a little each frame while the sky waits for
the next one.

## Generate the images

Run from the project root (needs `numpy` for the nebula). Each sprite generator takes a file name
to write a preview of everything it draws instead of saving the sheets
(`make_enemies.py` takes the ship names, and `--preview file.png`):

```bash
python tools/pixel_art/make_player.py
python tools/pixel_art/make_enemies.py
python tools/pixel_art/make_oracle.py
python tools/pixel_art/make_bullets.py
python tools/pixel_art/make_supplies.py
python tools/pixel_art/make_asteroids.py
python tools/pixel_art/make_structures.py
python tools/pixel_art/make_hud.py
python tools/pixel_art/make_nebula.py
```

The synthesized sounds (stasis, pylon power-down, Stargate warp surge) are made by
`python tools/sound/make_sounds.py` (needs `numpy` and `ffmpeg`).

## Edit them in Aseprite

The sprite sheets can be opened and edited as they are (they are at art size). Keep the frame
sizes: the code places guns, noses and pads in them (see the comments in the generators).

`art/` holds Aseprite copies of the HUD and the nebula at their drawing size (HUD: half size, so one
pixel is one art pixel). After editing, export back to the game at 2x (nearest neighbor, pixels
stay sharp), for example:

```bash
Aseprite -b art/UI/Player/BottomLeft.aseprite --scale 2 --save-as src/asset/image/UI/Player/BottomLeft.png
Aseprite -b art/Nebula.aseprite --save-as src/asset/image/Nebula.png
```

Keep the same image sizes: the game draws bars, lights and icons at fixed positions
(see the comments in `make_hud.py`). Running the generators again overwrites hand edits.
