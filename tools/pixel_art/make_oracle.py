""" Generate the Oracle sprite sheets in the chibi style (src/asset/image/Enemy/Oracle/...)

Development tool. The Oracle is the Protoss harasser of StarCraft II: a copper hull with a big
crystal, violet claw blades in front, two rear fins and two engines. Faces down, engines at the
top, drawn at art size (the game shows it at 2x). Each sheet has 6 frames side by side:
    OracleNormal   flickering engine flames, the crystal pulsing
    OracleHit      red flash (drawn over the ship when it is hit)
    OracleAttack   cyan glints gathering at the crystal and the claw tips (charging its beam)
    OracleDestroy  the ship darkening to a black silhouette
    OracleBase     the first frame

Run from the project root:  python tools/pixel_art/make_oracle.py [preview.png]
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from chibi import Art, COPPER, GOLD, VIOLET, CYAN, P_OUTLINE, FRAMES, finish, hit_frames, destroy_frames, \
    save, flame, preview

OUT = "src/asset/image/Enemy/Oracle"
W, H = 34, 46
CX = 16.5
CYAN_FLAME = (CYAN[0], CYAN[1], CYAN[2], CYAN[3])


def parts(art):
    hull = art.ellipse(CX, 19, 5.6, 9.5) | art.poly([(13, 24), (20, 24), (CX, 32)])
    crystal = art.ellipse(CX, 20.5, 3.2, 4.2)
    claws = art.both(art.poly([(11.5, 15), (5.5, 20), (3.5, 28), (5.5, 36), (10.5, 41), (13.5, 42), (11.5, 36),
                               (8.5, 29), (9.5, 22), (12.5, 20)])) - hull
    inner = art.both(art.poly([(11.5, 16.5), (7, 21), (5.5, 28), (7.2, 35), (11, 39.5), (11, 36),
                               (9.5, 29), (10.3, 22.5), (12.5, 21)]))
    rims = {p for p in claws if p not in inner}
    fins = art.both(art.poly([(13, 12), (7, 6), (5, 7), (8, 12), (12, 15)])) - hull
    engines = art.ellipse(CX - 2.5, 10, 1.6, 2) | art.ellipse(CX + 2.5, 10, 1.6, 2)
    return dict(hull=hull, crystal=crystal, claws=claws - rims, rims=rims, fins=fins, engines=engines)


def oracle(frame):
    art = Art(W, H)
    p = parts(art)
    art.cel(p["fins"], VIOLET, bevel=1.5)
    art.cel(p["claws"], VIOLET, bevel=2)
    art.cel(p["rims"], GOLD, bevel=1.2)
    art.cel(p["engines"], COPPER, bevel=1.5)
    art.dome(p["hull"], CX, 21, 7, 12, COPPER)
    # The crystal pulses
    glow = 0.5 + 0.5 * math.sin(frame / FRAMES * math.tau)
    art.dome(p["crystal"], CX, 20.5, 3.2, 4.2, CYAN, high=0.55 - glow * 0.15, low=0.2 - glow * 0.1)
    art.px(CX - 1.5, 18, CYAN[3])
    art.px(CX - 0.5, 17, CYAN[3])
    art.seam(p["crystal"], p["hull"] - p["crystal"], P_OUTLINE)
    art.seam(p["claws"] | p["rims"], p["hull"], P_OUTLINE)
    # Lights at the claw tips
    for x in (11.5, 21.5):
        art.px(x, 40, CYAN[3] if frame % 3 != 2 else CYAN[0])
    hull = set().union(*p.values())
    flames = set()
    for i, x in enumerate((CX - 2.5, CX + 2.5)):
        flames |= flame(art.c, x + 0.5, 7, (3, 4, 3, 4, 3, 4)[(frame + i) % FRAMES], 2.4, CYAN_FLAME, down=False)
    return finish(art.c, hull, P_OUTLINE, extra=flames)


def attack(frame):
    """ Glints gathering at the crystal and the claw tips """
    c = pygame.Surface((W, H), pygame.SRCALPHA)
    t = (frame + 1) / FRAMES
    for k in range(8):
        a = k / 8 * math.tau + frame * 0.4
        r = 9 * (1 - t) + 4
        x, y = round(CX + math.cos(a) * r), round(20.5 + math.sin(a) * r)
        c.set_at((x, y), CYAN[3] if k % 2 else (255, 255, 255))
    size = 1 + frame // 2
    for x in (11.5, 21.5):
        for i in range(-size, size + 1):
            c.set_at((round(x + i), 40), CYAN[2])
            c.set_at((round(x), 40 + i), CYAN[2])
    return c


def main():
    pygame.init()
    normal = [oracle(i) for i in range(FRAMES)]
    sheets = {
        "Normal": normal,
        "Base": [normal[0]] * FRAMES,
        "Hit": hit_frames(normal[0], (170, 120, 70)),
        "Attack": [attack(i) for i in range(FRAMES)],
        "Destroy": destroy_frames(normal[0]),
    }
    if len(sys.argv) > 1:
        preview(sys.argv[1], [f for frames in sheets.values() for f in frames])
        return
    for name, frames in sheets.items():
        save(frames, os.path.join(OUT, f"Oracle{name}.png"))


if __name__ == "__main__":
    main()
