""" Generate the player's sprite sheets in the chibi style (src/asset/image/PlayerPlane/...,
and the HUD portraits src/asset/image/UI/Player/Viking*.png)

Development tool. The Viking of StarCraft II as a chibi fighter: a round white hull with a red
nose, a big glass canopy, stubby wings carrying the two red gun pods, red tail fins and two
engines. Faces up. Sheets (6 frames side by side unless said):
    VikingMoveNormal   engines flickering          VikingMoveUp      engines at full thrust
    VikingBase         the first frame              VikingHit         red flash (3 frames)
    VikingInvincible   white blink                  VikingDestroy     darkening
    bullet             gatling shot (1 frame)       BulletHit         where a shot hits
    Bomb               the nuclear missile (1 frame)
HUD portraits (drawn at 2x like the HUD): the Viking's outline in green, and its damaged parts
in red at 70%, 50% and 30% health (6 blinking frames).

Run from the project root:  python tools/pixel_art/make_player.py [preview.png]
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from chibi import Art, WHITE, RED, GLASS, STEEL, YELLOW, FLAME, T_OUTLINE, RIM, FRAMES, finish, ring, \
    hit_frames, blink_frames, destroy_frames, save, flame, preview, opaque
from shading import save_sheet

OUT = "src/asset/image/PlayerPlane"
UI_OUT = "src/asset/image/UI/Player"

W, H = 28, 33
CX = 13.5
# Flame lengths, frame by frame: cruising, full thrust
CRUISE = (3, 4, 3, 4, 3, 3)
THRUST = (5, 6, 5, 6, 5, 5)
NOZZLES = (11.5, 15.5)


def viking_parts(art):
    """ The parts of the Viking (sets of pixels), drawn on `art` """
    body = art.ellipse(CX, 14, 4.8, 10.5)
    nose = art.ellipse(CX, 6, 3.2, 3) & body
    canopy = art.ellipse(CX, 11.5, 2.8, 3.8)
    pods = art.both(art.ellipse(6.5, 14.5, 1.8, 3.4))
    barrels = art.both(art.rect(6, 9.5, 1, 2.5))
    wings = art.both(art.poly([(9, 12), (2, 18.5), (1.5, 21.5), (4, 22.5), (9, 21)])) - body - pods
    tips = {(x, y) for x, y in wings if x <= 3.5 * art.k or x >= art.size[0] - 1 - 3.5 * art.k}
    fins = art.both(art.poly([(10, 19), (7.5, 25), (9.5, 26), (11.5, 23)])) - body
    nozzles = art.ellipse(NOZZLES[0], 24.5, 1.6, 1.6) | art.ellipse(NOZZLES[1], 24.5, 1.6, 1.6)
    return dict(body=body, nose=nose, canopy=canopy, pods=pods, barrels=barrels, wings=wings - tips,
                tips=tips, fins=fins, nozzles=nozzles)


def viking(frame=0, lengths=CRUISE):
    art = Art(W, H)
    p = viking_parts(art)
    art.cel(p["wings"] | p["tips"], WHITE, bevel=2)
    art.cel(p["tips"], RED, bevel=1.5)
    art.cel(p["fins"], RED, bevel=1.5)
    art.cel(p["nozzles"], STEEL, bevel=1.5)
    art.cel(p["body"], WHITE, bevel=4)
    art.cel(p["nose"], RED, bevel=3)
    art.cel(p["barrels"], STEEL, bevel=1)
    art.cel(p["pods"], RED, bevel=2)
    art.cel(p["canopy"], GLASS, bevel=3)
    # Shine on the canopy, a red chevron on the hull
    art.px(CX - 1.5, 9, GLASS[3])
    art.px(CX - 1.5, 10, GLASS[3])
    art.px(CX - 0.5, 8, GLASS[3])
    for i in range(3):
        art.px(CX - 1.5 + i, 18 + (1 if i == 1 else 0), RED[1])
    art.seam(p["canopy"], p["body"] - p["canopy"], T_OUTLINE)
    art.seam(p["wings"] | p["tips"], p["pods"] | p["body"], T_OUTLINE)
    art.seam(p["nose"], p["body"] - p["nose"] - p["canopy"], RED[0])
    hull = set().union(*p.values())
    flames = set()
    for x in NOZZLES:
        flames |= flame(art.c, x + 0.5, 26, lengths[frame % len(lengths)], 3, FLAME)
    return finish(art.c, hull, T_OUTLINE, extra=flames)


def portrait(damage=None, frame=0):
    """ HUD portrait: the Viking's outline (green), with the damaged parts in red. 48x37 at 2x """
    k = 0.62
    art = Art(W, H, k)
    p = viking_parts(art)
    hull = set().union(*p.values())
    green = (40, 190, 110)
    red = (240, 60, 60) if frame % 3 != 2 else (150, 30, 40)
    lines = set()
    for part in ("body", "pods", "wings", "tips", "fins", "canopy"):
        shape = p[part]
        lines |= {(x, y) for x, y in shape
                  if any((x + dx, y + dy) not in shape for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    damaged = {"70": ("pods",), "50": ("pods", "wings", "tips"),
               "30": ("pods", "wings", "tips", "fins", "body")}.get(damage, ())
    for x, y in lines:
        part = next((name for name in ("pods", "wings", "tips", "fins", "canopy", "body") if (x, y) in p[name]),
                    "body")
        if damage is None:
            art.c.set_at((x, y), green)
        elif part in damaged:
            art.c.set_at((x, y), red)
    out = pygame.Surface((24, 18), pygame.SRCALPHA)
    out.blit(art.c, ((24 - art.size[0]) // 2, (18 - art.size[1]) // 2))
    big = pygame.Surface((48, 37), pygame.SRCALPHA)
    big.blit(pygame.transform.scale(out, (48, 36)), (0, 0))
    return big


def bullet():
    """ Gatling shot: a yellow bolt with a white core and an orange tail """
    art = Art(5, 14)
    body = art.ellipse(2, 4, 1.6, 3.4)
    tail = art.poly([(1, 6), (3, 6), (2, 12)])
    art.fill(tail, FLAME[0])
    art.fill(body, YELLOW[2])
    art.fill(art.ellipse(2, 3.5, 0.8, 2.2), YELLOW[3])
    return art.c


def bullet_hit(frame):
    """ A star burst growing then breaking into sparks """
    art = Art(18, 10)
    cx, cy = 8.5, 4.5
    sizes = (2, 4, 5, 5, 4, 3)
    size = sizes[frame]
    colors = (YELLOW[3], YELLOW[2], FLAME[1], FLAME[0], FLAME[0], RED[1])
    color = colors[frame]
    if frame < 3:
        art.fill(art.ellipse(cx, cy, size * 0.6 + 0.6, size * 0.45 + 0.5), color)
        if frame < 2:
            art.fill(art.ellipse(cx, cy, size * 0.3 + 0.3, size * 0.2 + 0.3), (255, 255, 255))
    for dx, dy in ((1, 0), (-1, 0), (0.7, -0.7), (-0.7, -0.7), (0.7, 0.7), (-0.7, 0.7)):
        x, y = cx + dx * (size + 1), cy + dy * (size * 0.6 + 1)
        if frame >= 1:
            art.px(x, y, color)
    return art.c


def bomb():
    """ The nuclear missile: a round yellow body with black hazard bands, red fins and a flame """
    art = Art(10, 22)
    cx = 4.5
    body = art.ellipse(cx, 8, 2.8, 6.5)
    nose = art.ellipse(cx, 3.5, 2.3, 2.3) & body
    fins = art.both(art.poly([(2, 11), (0.5, 15.5), (3, 14)]))
    art.cel(fins, RED, bevel=1.2)
    art.cel(body, YELLOW, bevel=2.5)
    art.cel(nose, RED, bevel=2)
    for y in (8, 11):
        for x in range(10):
            if (x, y) in body:
                art.c.set_at((x, y), T_OUTLINE if x % 2 == 0 else YELLOW[0])
    hull = body | fins
    flames = flame(art.c, cx + 0.5, 15, 5, 3, FLAME)
    return finish(art.c, hull, T_OUTLINE, extra=flames)


NUKE = 200


def nuke(frame):
    """ The nuclear blast: a white flash swelling into a puffy fireball that cools into smoke """
    import random
    rng = random.Random(11)
    c = pygame.Surface((NUKE, NUKE), pygame.SRCALPHA)
    m = (NUKE - 1) / 2
    radius = (26, 52, 70, 82, 90, 95, 98, 99)[frame]
    # Puffs around a core: (angle, distance, size), the same in every frame
    puffs = [(rng.uniform(0, math.tau), rng.uniform(0.35, 0.8), rng.uniform(0.28, 0.42)) for _ in range(16)]
    ramps = [
        [(255, 240, 180), (255, 255, 230), (255, 255, 255), (255, 255, 255)],
        [(255, 170, 60), (255, 220, 110), (255, 248, 200), (255, 255, 255)],
        [(236, 96, 40), (255, 160, 60), (255, 216, 110), (255, 246, 210)],
        [(200, 60, 40), (240, 110, 50), (255, 170, 80), (255, 220, 150)],
        [(150, 50, 50), (200, 80, 50), (236, 130, 70), (255, 190, 120)],
        [(96, 70, 80), (140, 100, 96), (180, 140, 120), (220, 190, 160)],
        [(70, 62, 80), (104, 94, 110), (140, 130, 146), (180, 172, 186)],
        [(60, 56, 74), (86, 80, 100), (112, 106, 128), (150, 146, 164)],
    ]
    ramp = ramps[frame]
    light = (-0.5, -0.6, 0.62)
    shapes = [(m, m, radius * 0.62)] + [(m + math.cos(a) * d * radius, m + math.sin(a) * d * radius, s * radius)
                                        for a, d, s in puffs]
    # Thinning smoke: holes in the last frames
    holes = (0, 0, 0, 0, 0, 0.15, 0.4, 0.7)[frame]
    for y in range(NUKE):
        for x in range(NUKE):
            best = None
            for px, py, r in shapes:
                dx, dy = (x - px) / r, (y - py) / r
                d2 = dx * dx + dy * dy
                if d2 <= 1 and (best is None or d2 < best[0]):
                    best = (d2, dx, dy)
            if best is None:
                continue
            if holes and ((x * 7 + y * 13) % 17) / 17 < holes * (0.3 + best[0]):
                continue
            d2, dx, dy = best
            dz = math.sqrt(1 - d2)
            v = dx * light[0] + dy * light[1] + dz * light[2]
            color = ramp[0] if v < 0.25 else ramp[1] if v < 0.6 else ramp[2] if v < 0.85 else ramp[3]
            c.set_at((x, y), color)
    return c


def main():
    pygame.init()
    normal = [viking(i, CRUISE) for i in range(FRAMES)]
    up = [viking(i, THRUST) for i in range(FRAMES)]
    sheets = {
        "VikingMoveNormal": normal,
        "VikingMoveUp": up,
        "VikingBase": [normal[0]],
        "VikingHit": hit_frames(normal[0], (150, 220, 150)),
        "VikingInvincible": blink_frames(normal[0]),
        "VikingDestroy": destroy_frames(normal[0]),
        "bullet": [bullet()],
        "BulletHit": [bullet_hit(i) for i in range(FRAMES)],
        "Bomb": [bomb()],
    }
    nukes = [nuke(i) for i in range(8)]
    portraits = {
        "Viking100": [portrait()],
        "Viking70": [portrait("70", i) for i in range(FRAMES)],
        "Viking50": [portrait("50", i) for i in range(FRAMES)],
        "Viking30": [portrait("30", i) for i in range(FRAMES)],
    }
    if len(sys.argv) > 1:
        preview(sys.argv[1], [f for frames in list(sheets.values()) + list(portraits.values()) for f in frames])
        preview(sys.argv[1].replace(".png", "_nuke.png"), nukes, scale=1)
        return
    for name, frames in sheets.items():
        save(frames, os.path.join(OUT, f"{name}.png"))
    save(nukes, "src/asset/image/Bomb/NucExplosion.png")
    for name, frames in portraits.items():
        save_sheet(frames, os.path.join(UI_OUT, f"{name}.png"))


if __name__ == "__main__":
    main()
