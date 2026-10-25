# Pygame-LostViking

A StarCraft II themed vertical shooter: fly a Terran Viking from a Terran Starport, through an
asteroid field and the Protoss outposts, to the Protoss Stargate and its Carrier. See the
[game intro](https://github.com/RedCarpG/DOCS/blob/main/lost_viking/README.md) for more screenshots.

<p>
<img src="https://github.com/RedCarpG/DOCS/blob/main/lost_viking/route_2_asteroids.png?raw=true" width="49%" alt="Asteroid field">
<img src="https://github.com/RedCarpG/DOCS/blob/main/lost_viking/route_4_outposts.png?raw=true" width="49%" alt="Protoss outposts">
<img src="https://github.com/RedCarpG/DOCS/blob/main/lost_viking/route_5_stargate.png?raw=true" width="49%" alt="Stargate">
<img src="https://github.com/RedCarpG/DOCS/blob/main/lost_viking/route_6_carrier.png?raw=true" width="49%" alt="Carrier">
</p>

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

The Viking flies from a Terran Starport to a Protoss Stargate. The route, shown on the left edge
of the screen, has stages, each announced by its name:

1. **Launch**: the Viking takes off from the launch pad of the Terran Starport.
2. **Asteroid field**: spinning rocks drift down, a large rock breaks into two medium rocks, a medium
   rock into two small ones. Flying into a rock hurts. Large and medium rocks are armored.
   Rocks are cover: enemy shots stop at them (beams go through), and enemy fire chips them too.
3. **Protoss patrol**: Scout formations, Phoenixes, an Oracle.
4. **Protoss outposts**: floating platforms with a **Pylon** and **Photon Cannons** (fixed turrets
   firing at you). The Pylon powers the cannons of its platform: destroy it and they go dark.
   Destroy everything on a platform for a bonus. You fly over the structures (they do not ram you).
5. **Stargate** (WARNING): it builds ships (Scouts warp out of its portal, an Oracle, Phoenixes),
   releases rings of photon orbs, and two cannons stand on its wings. Before it falls it warps out
   the **Carrier**, then blows up.
6. **Carrier**: destroy it to win.

- Two weapons, as the StarCraft II Viking, switched with E (no shot while the Viking transforms):
  - **Twin gatling**: fast straight shots, the best against light ships (Interceptors, Phoenixes) and shields.
    From weapon level 4 its shots turn green and go through ships: one ship at level 4, two at level 5,
    30% less damage after each. A shield stops them.
  - **Lanzer Torpedoes**: homing torpedoes in salvos of pairs, extra damage against armored targets
    (Scouts, Oracles, large and medium rocks, structures, the Carrier).
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
    Touching an armed ward freezes you in a crystal for almost a second: no move, no shot, no bomb,
    but no damage either. Shoot the wards down.
- The Carrier gets angry below half health: its attacks come faster.

## Test mode

Choose **Test Mode** in the main menu to play with a test panel (press `` ` `` to show / hide it).
Each action has a key and can also be clicked: spawn any enemy or the boss, damage the boss,
level up the weapon, add bombs and lives, god mode, turn automatic spawning off and show hitboxes.
"Scout wave" brings a random Scout formation, "Oracle" warps one in, "Asteroid" and "Outpost" bring
a rock or a platform, "Stargate" starts the boss fight, "Next stage" jumps along the route.
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

The Viking, the Scouts, Interceptors, Phoenixes and the Carrier, the bullets and the nuke keep
their original art, drawn in Aseprite: the sources are in
[LostViking-pixel_art](https://github.com/RedCarpG/LostViking-pixel_art). The Oracle, the asteroids, the structures (Terran Starport, outposts, Stargate)
and the supplies are chibi pixel art (round shapes, cel shading, big 2x pixels, a white rim around
ships and targets), made by the generators in `tools/pixel_art` (see its README).
