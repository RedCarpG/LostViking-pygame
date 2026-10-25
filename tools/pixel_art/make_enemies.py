""" Generate the Protoss ship sheets in the chibi style (src/asset/image/Enemy/...)

Development tool. Copper hulls, violet plates and cyan energy crystals, faces down (engines at
the top), drawn at art size (the game shows them at 2x). Each ship has sheets of 6 frames:
    <Ship>Normal / Idle   engines flickering          <Ship>Attack   glints gathering (drawn over the ship)
    <Ship>Hit             red flash (3 frames)         <Ship>Destroy  darkening
    <Ship>Base            the first frame
Ships: Scout, Interceptor (also Move: engine at full thrust), Phoenix (also Fast: flying in, and
Shield: its shield bubble), Carrier.

Run from the project root:  python tools/pixel_art/make_enemies.py [ship ...] [--preview file.png]
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from chibi import Art, COPPER, GOLD, VIOLET, CYAN, P_OUTLINE, FRAMES, finish, hit_frames, destroy_frames, save, \
    flame, preview

OUT = "src/asset/image/Enemy"
HIT_ALPHAS = (170, 120, 70)
CYAN_FLAME = (CYAN[0], CYAN[1], CYAN[2], CYAN[3])


def sparkle(c, x, y, size, color, core=(255, 255, 255)):
    """ A 4-pointed glint """
    x, y = round(x), round(y)
    for i in range(-size, size + 1):
        for px, py in ((x + i, y), (x, y + i)):
            if 0 <= px < c.get_width() and 0 <= py < c.get_height():
                c.set_at((px, py), color)
    c.set_at((x, y), core)


# ------------------ Scout ------------------
SCOUT = (28, 32)


def scout(frame, lengths=(3, 4, 3, 4, 3, 3)):
    art = Art(*SCOUT)
    cx = 13.5
    body = art.ellipse(cx, 16.5, 4.6, 8) | art.poly([(10.5, 21), (16.5, 21), (cx, 28.5)])
    gem = art.ellipse(cx, 17, 2.4, 2.8)
    wings = art.both(art.poly([(9.5, 12), (3, 15), (1.5, 21), (4, 22.5), (9.5, 18)])) - body
    trim = {(x, y) for x, y in wings if x <= 3 or x >= SCOUT[0] - 4}
    engines = art.ellipse(10.5, 9, 1.7, 2.2) | art.ellipse(16.5, 9, 1.7, 2.2)
    art.cel(wings, VIOLET, bevel=2)
    art.cel(trim, GOLD, bevel=1.5)
    art.cel(engines, COPPER, bevel=1.5)
    art.cel(body, COPPER, bevel=3.5)
    art.cel(gem, CYAN, bevel=2)
    art.px(cx - 1, 15.5, CYAN[3])
    art.seam(gem, body - gem, P_OUTLINE)
    art.seam(wings, body, P_OUTLINE)
    # Copper ridge down the nose
    for y in range(21, 27):
        art.px(cx, y, COPPER[2] if y < 24 else COPPER[1])
    flames = set()
    for x in (10.5, 16.5):
        flames |= flame(art.c, x + 0.5, 6, lengths[frame % len(lengths)], 2.6, CYAN_FLAME, down=False)
    return finish(art.c, body | wings | engines, P_OUTLINE, extra=flames)


def scout_attack(frame):
    """ Glints gathering at the nose (it fires from there) """
    c = pygame.Surface(SCOUT, pygame.SRCALPHA)
    t = (frame + 1) / FRAMES
    sparkle(c, 13.5, 27, 1 + round(t * 2), CYAN[2])
    for i, (dx, dy) in enumerate(((-4, -3), (4, -3), (-3, 2), (3, 2))):
        if (frame + i) % 2 == 0:
            r = 1 - t
            c.set_at((round(13.5 + dx * r), round(27 + dy * r)), CYAN[3])
    return c


# ------------------ Interceptor ------------------
INTERCEPTOR = (18, 14)


def interceptor(frame, lengths=(2, 3, 2, 3, 2, 2)):
    art = Art(*INTERCEPTOR)
    cx = 8.5
    body = art.ellipse(cx, 6.5, 3.4, 3.2)
    blades = art.both(art.poly([(5.5, 4), (2, 7), (2.5, 10), (5.5, 8)])) - body
    eye = art.ellipse(cx, 7.5, 1.4, 1.2)
    art.cel(blades, VIOLET, bevel=1.5)
    art.cel(body, COPPER, bevel=2.5)
    blink = frame % 6 == 5
    art.fill(eye, CYAN[0] if blink else CYAN[1])
    if not blink:
        art.px(cx - 0.5, 7, CYAN[3])
    flames = flame(art.c, cx + 0.5, 3, lengths[frame % len(lengths)], 2.2, CYAN_FLAME, down=False)
    return finish(art.c, body | blades, P_OUTLINE, extra=flames)


def interceptor_attack(frame):
    c = pygame.Surface(INTERCEPTOR, pygame.SRCALPHA)
    sparkle(c, 8.5, 8, 1 + frame // 2, CYAN[2])
    return c


# ------------------ Phoenix ------------------
PHOENIX = (50, 48)


def phoenix_parts(art):
    cx = 24.5
    body = art.ellipse(cx, 19, 5.6, 8.5) | art.poly([(20.5, 24), (28.5, 24), (cx, 33)])
    crystal = art.ellipse(cx, 21, 2.8, 3.4)
    # Crescent blades: a band between two ellipses, curving down on both sides
    outer = art.ellipse(cx, 21, 21.5, 19)
    inner = art.ellipse(cx, 25.5, 16.5, 18)
    blades = {(x, y) for x, y in outer - inner if y >= 13 * art.k and abs(x - art._p(cx)) > 7 * art.k}
    trim = {(x, y) for x, y in blades if (x, y) not in art.ellipse(cx, 21, 19.8, 17.4)}
    arms = art.both(art.poly([(19.5, 15), (9, 15.5), (8, 19.5), (19.5, 21)])) - body
    engines = art.ellipse(cx - 3.5, 10.5, 1.8, 2.2) | art.ellipse(cx + 3.5, 10.5, 1.8, 2.2)
    return dict(body=body, crystal=crystal, blades=blades - trim, trim=trim, arms=arms, engines=engines)


def phoenix(frame, lengths=(3, 4, 3, 4, 3, 3)):
    art = Art(*PHOENIX)
    p = phoenix_parts(art)
    cx = 24.5
    art.cel(p["blades"], VIOLET, bevel=2.5)
    art.cel(p["trim"], GOLD, bevel=1.2)
    art.cel(p["arms"], COPPER, bevel=1.8)
    art.cel(p["engines"], COPPER, bevel=1.5)
    art.cel(p["body"], COPPER, bevel=4)
    art.cel(p["crystal"], CYAN, bevel=2.2)
    art.px(cx - 1, 19.5, CYAN[3])
    art.seam(p["crystal"], p["body"] - p["crystal"], P_OUTLINE)
    art.seam(p["arms"], p["blades"] | p["trim"], P_OUTLINE)
    # Lights on the blades
    for x, y in ((6, 27), (43, 27)):
        art.px(x, y, CYAN[2] if frame % 3 else CYAN[3])
    hull = set().union(*p.values())
    flames = set()
    for x in (cx - 3.5, cx + 3.5):
        flames |= flame(art.c, x + 0.5, 8, lengths[frame % len(lengths)], 2.6, CYAN_FLAME, down=False)
    return finish(art.c, hull, P_OUTLINE, extra=flames)


def phoenix_attack(frame):
    """ Glints at the crystal and the blade tips: the laser charges """
    c = pygame.Surface(PHOENIX, pygame.SRCALPHA)
    t = (frame + 1) / FRAMES
    sparkle(c, 24.5, 33, 1 + round(t * 2), CYAN[2])
    for x, y in ((10, 36), (39, 36)):
        if frame % 2 == 0:
            sparkle(c, x, y, 1, CYAN[2])
    return c


SHIELD = 63


def phoenix_shield(frame):
    """ The shield bubble: see-through cyan with a bright edge and a shine turning around """
    c = pygame.Surface((SHIELD, SHIELD), pygame.SRCALPHA)
    m = (SHIELD - 1) / 2
    r = SHIELD / 2 - 1.5
    turn = frame / FRAMES * math.tau
    for y in range(SHIELD):
        for x in range(SHIELD):
            d = math.hypot(x - m, y - m) / r
            if d > 1:
                continue
            if d > 0.92:
                color = (*CYAN[2], 230)
            elif d > 0.84:
                color = (*CYAN[1], 120)
            else:
                # Soft dither toward the middle
                color = (*CYAN[1], 44 if (x + y) % 2 else 26)
            c.set_at((x, y), color)
    # Shine: an arc on the upper left and sparkles going around
    for i in range(14):
        a = math.radians(200 + i * 4)
        c.set_at((round(m + math.cos(a) * r * 0.75), round(m + math.sin(a) * r * 0.75)), (255, 255, 255, 220))
    for k in range(3):
        a = turn + k * math.tau / 3
        sparkle(c, m + math.cos(a) * r * 0.92, m + math.sin(a) * r * 0.92, 1, (*CYAN[3], 255), (255, 255, 255, 255))
    return c


# ------------------ Carrier ------------------
CARRIER = (140, 194)


def carrier_parts(art):
    cx = 69.5
    hull = art.ellipse(cx, 92, 31, 66)
    front = art.ellipse(cx, 150, 21, 34) - hull
    pods = art.both(art.ellipse(44, 140, 10, 13))
    arms = art.both(art.poly([(40, 40), (15, 70), (8, 118), (15, 166), (27, 190), (33, 168), (25, 120),
                              (31, 84), (46, 60)])) - hull - pods - art.ellipse(cx, 150, 21, 34)
    inner = art.both(art.poly([(41, 47), (19, 73), (12, 118), (18, 160), (27, 178), (29, 166), (22, 120),
                               (28, 86), (45, 63)]))
    arm_trim = {(x, y) for x, y in arms if (x, y) not in inner}
    struts = art.both(art.rect(30, 72, 9, 5) | art.rect(27, 128, 8, 5)) - hull - pods - art.ellipse(cx, 150, 21, 34)
    plates = art.both(art.ellipse(50, 98, 6, 24)) & hull
    window = art.ellipse(cx, 98, 8, 12)
    frame = art.ellipse(cx, 98, 11, 15) - window
    bay = art.ellipse(cx, 172, 10, 7)
    engines = art.ellipse(cx - 15, 27, 6, 6) | art.ellipse(cx + 15, 27, 6, 6) | art.ellipse(cx, 23, 7.5, 7.5)
    return dict(hull=hull, front=front, pods=pods, arms=arms - arm_trim, arm_trim=arm_trim, struts=struts,
                plates=plates, frame=frame, window=window, bay=bay, engines=engines)


def carrier(frame, lengths=(6, 8, 7, 9, 7, 8)):
    art = Art(*CARRIER)
    p = carrier_parts(art)
    cx = 69.5
    art.cel(p["arms"], VIOLET, bevel=4)
    art.cel(p["arm_trim"], GOLD, bevel=2)
    art.cel(p["struts"], COPPER, bevel=2)
    art.cel(p["engines"], COPPER, bevel=3)
    # A long hull: lit like a cylinder (the dome stretched far beyond the hull), the light side on
    # the left all along, so the front that shows on the screen is lit too
    art.dome(p["hull"], cx, 70, 31, 180, COPPER)
    art.dome(p["front"], cx, 120, 21, 120, COPPER)
    for side in (-1, 1):
        x = cx + side * 25.5
        art.dome({q for q in p["pods"] if (q[0] < art.size[0] / 2) == (side < 0)}, x, 140, 10, 13, COPPER)
    art.dome(p["plates"], cx, 98, 30, 30, VIOLET)
    art.cel(p["frame"], GOLD, bevel=2)
    art.dome(p["window"], cx, 98, 8, 12, CYAN)
    art.fill(p["bay"], VIOLET[0])
    # Gold bands around the hull, a ridge down the middle
    for band in (58, 124):
        for x in range(art.size[0]):
            for y in (band, band + 1):
                if (x, y) in (p["hull"] | p["front"]) - p["plates"] - p["frame"] - p["window"]:
                    art.c.set_at((x, y), GOLD[2] if y == band else GOLD[0])
    for y in list(range(32, 56)) + list(range(116, 122)) + list(range(128, 160)):
        art.px(cx, y, GOLD[2])
        art.px(cx + 1, y, COPPER[0])
    # Shine on the window, lights on the pods, around the bay and along the arms
    for x, y in ((cx - 4, 90), (cx - 3, 89), (cx - 4, 91)):
        art.px(x, y, CYAN[3])
    for i, (x, y) in enumerate(((cx - 7, 172), (cx - 3, 176), (cx + 3, 176), (cx + 7, 172))):
        art.px(x, y, CYAN[3] if (i + frame) % 3 == 0 else CYAN[1])
    for x in (40, 99):
        art.px(x, 143, CYAN[3] if frame % 2 else CYAN[1])
    for i, y in enumerate(range(84, 170, 14)):
        on = (i + frame) % 3 == 0
        art.px(13, y, CYAN[3] if on else CYAN[0])
        art.px(126, y, CYAN[3] if on else CYAN[0])
    art.seam(p["plates"], p["hull"] - p["plates"], P_OUTLINE)
    art.seam(p["frame"], p["hull"] - p["frame"] - p["window"], P_OUTLINE)
    art.seam(p["pods"], p["hull"] | p["front"], P_OUTLINE)
    art.seam(p["front"], p["hull"], COPPER[0])
    art.seam(p["arms"] | p["arm_trim"], p["hull"] | p["front"] | p["struts"] | p["pods"], P_OUTLINE)
    hull = set().union(*p.values())
    flames = set()
    for x, w in ((cx - 15, 6), (cx, 7), (cx + 15, 6)):
        flames |= flame(art.c, x + 0.5, 15, lengths[frame % len(lengths)], w, CYAN_FLAME, down=False)
    return finish(art.c, hull, P_OUTLINE, extra=flames)


def carrier_attack(frame):
    """ The bay and the window light up (launching interceptors, charging) """
    c = pygame.Surface(CARRIER, pygame.SRCALPHA)
    t = (frame + 1) / FRAMES
    sparkle(c, 69.5, 172, 2 + round(t * 4), CYAN[2])
    for i in range(6):
        a = i / 6 * math.tau + frame * 0.4
        r = 16 * (1 - t) + 4
        sparkle(c, 69.5 + math.cos(a) * r, 100 + math.sin(a) * r * 1.4, 1, CYAN[3])
    return c


# ------------------ Sheets ------------------
def ship_sheets(name, normal, attack, extra=None):
    sheets = {
        f"{name}Normal" if name != "Interceptor" else f"{name}Idle": normal,
        f"{name}Base": [normal[0]],
        f"{name}Attack": attack,
        f"{name}Hit": hit_frames(normal[0], HIT_ALPHAS),
        f"{name}Destroy": destroy_frames(normal[0]),
    }
    sheets.update(extra or {})
    return sheets


def all_sheets(names):
    out = {}
    if "Scout" in names:
        out["Scout"] = ship_sheets("Scout", [scout(i) for i in range(FRAMES)], [scout_attack(i) for i in range(FRAMES)])
    if "Interceptor" in names:
        out["Interceptor"] = ship_sheets(
            "Interceptor", [interceptor(i) for i in range(FRAMES)], [interceptor_attack(i) for i in range(FRAMES)],
            {"InterceptorMove": [interceptor(i, (4, 5, 4, 5, 4, 4)) for i in range(FRAMES)]})
    if "Phoenix" in names:
        out["Phoenix"] = ship_sheets(
            "Phoenix", [phoenix(i) for i in range(FRAMES)], [phoenix_attack(i) for i in range(FRAMES)],
            {"PhoenixFast": [phoenix(i, (6, 7, 6, 7, 6, 6)) for i in range(FRAMES)],
             "PhoenixShield": [phoenix_shield(i) for i in range(FRAMES)]})
    if "Carrier" in names:
        normal = [carrier(i) for i in range(FRAMES)]
        # A faint flash: the boss is big and hit all the time
        out["Carrier"] = ship_sheets("Carrier", normal, [carrier_attack(i) for i in range(FRAMES)],
                                     {"CarrierHit": hit_frames(normal[0], (70, 45, 20))})
    return out


SHIPS = ("Scout", "Interceptor", "Phoenix", "Carrier")


def main():
    pygame.init()
    args = sys.argv[1:]
    preview_path = None
    if "--preview" in args:
        preview_path = args[args.index("--preview") + 1]
        args = [a for a in args if a not in ("--preview", preview_path)]
    sheets = all_sheets(args or SHIPS)
    if preview_path:
        preview(preview_path, [f for ship in sheets.values() for frames in ship.values() for f in frames])
        return
    for ship, ship_sheets_ in sheets.items():
        for name, frames in ship_sheets_.items():
            save(frames, os.path.join(OUT, ship, f"{name}.png"))


if __name__ == "__main__":
    main()
