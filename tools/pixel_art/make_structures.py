""" Generate the structure sprite sheets (src/asset/image/Structure/...)

Development tool. The structures of the route, seen from above like the ships:
    Terran Starport      where the Viking takes off (scenery)
    Protoss outposts     platforms carrying a Pylon and Photon Cannons (the platforms are scenery)
    Photon Cannon        fixed turret: an energy orb held by four copper claws
    Pylon                a floating crystal in a copper frame; it powers the cannons near it
    Stargate             the Protoss gate at the end of the route (the boss)
Protoss parts use the palette of the Protoss ships (copper, violet, cyan, dark red outline),
the Terran Starport the steel, white and red of the Viking. Drawn at art size; the game draws
them at 2x like the background. Sheets have 6 frames side by side where they are animated.

Run from the project root:  python tools/pixel_art/make_structures.py [preview.png]
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from shading import dither, mask_of, rect_mask, ellipse_mask, distance, shade, outline, seam, \
    silhouette, darken, save_sheet

OUT = "src/asset/image/Structure"
FRAMES = 6

OUTLINE = (64, 21, 21)
COPPER = [(147, 42, 42), (186, 69, 41), (212, 102, 33), (223, 118, 53), (235, 145, 89), (245, 183, 102),
          (255, 230, 198)]
VIOLET = [(48, 30, 110), (75, 44, 155), (72, 59, 176), (80, 90, 186), (79, 121, 190), (91, 138, 200),
          (159, 194, 239)]
CYAN = [(24, 133, 138), (97, 225, 231), (4, 244, 255), (146, 250, 255), (235, 254, 255)]
WHITE = (246, 246, 246)
# Protoss stone of the platforms: pale violet grey
STONE = [(28, 24, 48), (42, 38, 66), (58, 54, 86), (78, 76, 108), (102, 102, 134), (132, 134, 164)]
# Energy lines without power
DEAD = [(34, 30, 52), (52, 50, 74), (70, 70, 96)]
# Terran
STEEL = [(26, 28, 38), (44, 48, 62), (66, 72, 88), (94, 100, 116), (126, 132, 146), (162, 168, 180),
         (204, 208, 218)]
T_OUTLINE = (16, 16, 24)
RED = [(110, 10, 16), (184, 0, 0), (232, 40, 40)]
YELLOW = [(120, 84, 10), (214, 160, 30), (250, 210, 80)]
GREEN = (80, 230, 120)


def canvas(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def glow_disc(c, cx, cy, radius, ramp, strength=1.0, core=None):
    """ Round glow: bright middle, dithered steps toward the edge """
    for y in range(int(cy - radius) - 1, int(cy + radius) + 2):
        for x in range(int(cx - radius) - 1, int(cx + radius) + 2):
            d = math.hypot(x - cx, y - cy) / radius
            if d > 1:
                continue
            # Brighter toward the upper left
            v = (1 - d) * strength + 0.2 * (-(x - cx) - (y - cy)) / radius + dither(x, y) * 0.25
            c.set_at((x, y), ramp[max(0, min(len(ramp) - 1, int(v * len(ramp) + 0.3)))])
    if core:
        c.set_at((round(cx - radius * 0.35), round(cy - radius * 0.35)), core)


def sheet_frames(make, count=FRAMES):
    return [make(i) for i in range(count)]


# ------------------ Photon Cannon ------------------
CANNON = 22


def cannon(frame, powered=True, charge=0.0):
    """ :param charge: 0 to 1, the orb fills with light before a shot """
    size = CANNON
    m = (size - 1) / 2
    c = canvas(size, size)
    base = ellipse_mask(m, m, 10, 10)
    groove = ellipse_mask(m, m, 7, 7)
    claws = set()
    for k in range(4):
        a = math.radians(45 + k * 90)
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux
        tip = (m + ux * 4.5, m + uy * 4.5)
        root = (m + ux * 10.5, m + uy * 10.5)
        claws |= mask_of([[(root[0] + px * 3.2, root[1] + py * 3.2), (tip[0] + px * 1.0, tip[1] + py * 1.0),
                           (tip[0] - px * 1.0, tip[1] - py * 1.0), (root[0] - px * 3.2, root[1] - py * 3.2)]],
                         (size, size))
    shade(c, base - groove, COPPER, bevel=2.5, contrast=2.0)
    shade(c, groove, VIOLET[:4], bevel=2.0, bias=-0.15)
    glow = 0.5 + 0.5 * math.sin(frame / FRAMES * math.tau)
    if powered:
        strength = 1.0 + 0.25 * glow + charge * 0.9
        glow_disc(c, m, m, 5.2 + charge * 0.8, CYAN, strength, core=WHITE)
    else:
        glow_disc(c, m, m, 5.2, DEAD, 0.8)
    shade(c, claws, COPPER, bevel=1.5, bias=0.12, contrast=2.2)
    seam(c, claws, base - claws, OUTLINE)
    outline(c, base | claws, OUTLINE)
    if powered and charge > 0:
        # Glints gathering at the orb
        for k in range(8):
            a = k / 8 * math.tau + frame * 0.5
            r = 9 - charge * 4
            c.set_at((round(m + math.cos(a) * r), round(m + math.sin(a) * r)), CYAN[3] if k % 2 else WHITE)
    return c


# ------------------ Pylon ------------------
PYLON_W, PYLON_H = 24, 30


def pylon(frame):
    w, h = PYLON_W, PYLON_H
    c = canvas(w, h)
    m = (w - 1) / 2
    bob = (0, 0, -1, -1, 0, 0)[frame]
    # Copper frame: two arcs left and right of the crystal
    frame_l = mask_of([[(m - 4, 4), (m - 9, 7), (m - 11, 14), (m - 9, 22), (m - 4, 26),
                        (m - 6, 21), (m - 8, 14), (m - 6, 8)]], (w, h))
    frame_r = {(round(2 * m) - x, y) for x, y in frame_l}
    base = ellipse_mask(m, 24, 7, 3.5)
    shade(c, base, STONE, bevel=2.0, bias=-0.1)
    outline(c, base, OUTLINE)
    # Crystal: a tall diamond with a lit and a dark facet
    top, bottom, left, right = (m, 3 + bob), (m, 25 + bob), (m - 5, 13 + bob), (m + 5, 13 + bob)
    crystal = mask_of([[top, right, bottom, left]], (w, h))
    pulse = 0.5 + 0.5 * math.sin(frame / FRAMES * math.tau)
    lit_ramp = [VIOLET[5], CYAN[0], CYAN[1], CYAN[2], CYAN[3]]
    dark_ramp = [VIOLET[0], VIOLET[1], VIOLET[2], VIOLET[3], VIOLET[5]]
    for x, y in crystal:
        lit = x <= m
        v = 0.45 + (0.2 if y < 13 + bob else 0) + pulse * 0.15 + dither(x, y) * 0.2
        ramp = lit_ramp if lit else dark_ramp
        c.set_at((x, y), ramp[max(0, min(len(ramp) - 1, int(v * len(ramp))))])
    # Middle edge of the facets
    for y in range(int(top[1]) + 2, int(bottom[1]) - 1):
        c.set_at((round(m), y), CYAN[4] if (y + frame) % 5 else WHITE)
    outline(c, crystal, (30, 24, 70))
    for part in (frame_l, frame_r):
        shade(c, part, COPPER, bevel=1.5, contrast=2.2)
    outline(c, frame_l | frame_r, OUTLINE)
    return c


# ------------------ Outpost platforms ------------------
# (name, size, outline polygon, pads: (x, y, radius, part), conduits: (x0, x1, y))
# Keep the pad places in sync with src/game/level/level1/Outpost.py (LAYOUTS)
PLATFORMS = {
    "Large": ((150, 60), [(14, 6), (135, 6), (149, 20), (149, 39), (135, 53), (14, 53), (0, 39), (0, 20)],
              [(26, 30, 12, "cannon"), (75, 30, 13, "pylon"), (123, 30, 12, "cannon")],
              [(38, 61, 30), (89, 111, 30)]),
    "SmallL": ((80, 52), [(10, 4), (69, 4), (79, 16), (79, 35), (69, 47), (10, 47), (0, 35), (0, 16)],
               [(22, 26, 13, "pylon"), (57, 26, 12, "cannon")],
               [(35, 45, 26)]),
    "SmallR": ((80, 52), [(10, 4), (69, 4), (79, 16), (79, 35), (69, 47), (10, 47), (0, 35), (0, 16)],
               [(22, 26, 12, "cannon"), (57, 26, 13, "pylon")],
               [(34, 45, 26)]),
}


def platform(name, frame, powered=True):
    (w, h), polygon, pads, conduits = PLATFORMS[name]
    c = canvas(w, h)
    body = mask_of([polygon], (w, h))
    d = distance(body)
    trim = {p for p in body if d[p] <= 2}
    shade(c, body - trim, STONE, bevel=5.0, contrast=1.4, gradient=0.3, dither=0.15)
    shade(c, trim, COPPER, bevel=2.0, contrast=2.0, bias=0.05)
    seam(c, trim, body - trim, OUTLINE)
    # Copper plates in the four corners
    for cx, cy, sx, sy in ((0, 0, 1, 1), (w - 1, 0, -1, 1), (0, h - 1, 1, -1), (w - 1, h - 1, -1, -1)):
        plate = mask_of([[(cx + sx * 6, cy + sy * 10), (cx + sx * 18, cy + sy * 4), (cx + sx * 22, cy + sy * 8),
                          (cx + sx * 9, cy + sy * 15)]], (w, h)) & (body - trim)
        shade(c, plate, COPPER, bevel=1.5, contrast=2.0, bias=-0.05)
        outline(c, plate, OUTLINE)
    # Panel lines across the stone, between the pads
    for x0, x1, y in conduits:
        for x in (x0 - 4, x1 + 4):
            for yy in range(8, h - 8):
                if (x, yy) in body and (x, yy) not in trim:
                    c.set_at((x, yy), STONE[1])
    lights = CYAN if powered else DEAD + [DEAD[-1], DEAD[-1]]
    # Pads: a copper ring around a dark violet socket
    for x, y, r, part in pads:
        ring = ellipse_mask(x, y, r, r * 0.8)
        socket = ellipse_mask(x, y, r - 3, r * 0.8 - 3)
        shade(c, ring - socket, COPPER, bevel=1.5, contrast=2.0, bias=-0.1)
        shade(c, socket, VIOLET[:3] if part == "cannon" else VIOLET[:4], bevel=2.0, bias=-0.2)
        outline(c, ring, OUTLINE)
        # Four lights on the ring
        for k in range(4):
            a = k / 4 * math.tau + math.pi / 4
            c.set_at((round(x + math.cos(a) * (r - 1.5)), round(y + math.sin(a) * (r * 0.8 - 1.5))),
                     lights[3] if (k + frame) % 4 else lights[4])
    # Energy conduits: dashes flowing from the pylon to the cannons
    pylon_x = next(x for x, y, r, part in pads if part == "pylon")
    for x0, x1, y in conduits:
        for x in range(x0, x1 + 1):
            c.set_at((x, y - 2), OUTLINE)
            c.set_at((x, y + 2), OUTLINE)
            away = abs(x - pylon_x)
            for dy in (-1, 0, 1):
                if not powered:
                    color = DEAD[1] if dy else DEAD[2]
                elif (away - frame * 2) % 8 < 3:
                    color = CYAN[4] if dy == 0 else CYAN[3]
                else:
                    color = CYAN[2] if dy == 0 else CYAN[0]
                c.set_at((x, y + dy), color)
    # Running lights along the long edges
    for x in range(14, w - 14, 10):
        for y in (3, h - 4):
            if (x, y) in body:
                on = powered and (x // 10 + frame) % 3 == 0
                c.set_at((x, y), lights[4] if on else lights[1])
    outline(c, body, OUTLINE)
    return c


# ------------------ Stargate ------------------
# Keep in sync with src/game/level/level1/Stargate.py (PORTAL, CANNON_PADS)
GATE_W, GATE_H = 156, 118
GATE_PORTAL = (77.5, 50, 27, 22)
GATE_PADS = [(17, 74), (138, 74)]


def _portal(c, frame, flare=0.0):
    """ Swirling energy; `flare` (0 - 1) fills it with white light from the middle """
    cx, cy, rx, ry = GATE_PORTAL
    ramp = [VIOLET[0], VIOLET[1], VIOLET[3], VIOLET[5], CYAN[0], CYAN[1], CYAN[2], CYAN[3], CYAN[4]]
    turn = frame / FRAMES * math.tau
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            dx, dy = (x - cx) / rx, (y - cy) / ry
            r = math.hypot(dx, dy)
            if r > 1:
                continue
            arms = 0.5 + 0.5 * math.sin(math.atan2(dy, dx) * 3 + r * 9 - turn)
            v = 0.15 + (1 - r) * 0.65 + arms * 0.35 + dither(x, y) * 0.2 + flare * (1.2 - r)
            if r < flare * 0.7:
                c.set_at((x, y), WHITE)
            else:
                c.set_at((x, y), ramp[max(0, min(len(ramp) - 1, int(v * len(ramp) * 0.85)))])


def stargate(frame, flare=0.0):
    w, h = GATE_W, GATE_H
    c = canvas(w, h)
    cx, cy, rx, ry = GATE_PORTAL
    # Platform: wide in the middle, wings on the sides for the cannons
    body = mask_of([[(30, 8), (126, 8), (140, 22), (155, 58), (155, 90), (140, 100), (108, 100), (96, 117),
                     (60, 117), (48, 100), (16, 100), (0, 90), (0, 58), (16, 22)]], (w, h))
    d = distance(body)
    trim = {p for p in body if d[p] <= 2}
    shade(c, body - trim, STONE, bevel=6.0, contrast=1.4, gradient=0.3, dither=0.15)
    shade(c, trim, COPPER, bevel=2.0, contrast=2.0, bias=0.05)
    seam(c, trim, body - trim, OUTLINE)
    # Launch lane: from the portal to the front edge, with chevrons pointing out
    lane = rect_mask(63, 70, 30, 46) & body
    shade(c, lane - trim, VIOLET[:4], bevel=2.0, bias=-0.1)
    for k in range(4):
        y0 = 80 + k * 9
        on = (k - frame) % 4 == 0
        for i in range(7):
            for x in (round(cx) - i, round(cx) + i):
                c.set_at((x, y0 + 6 - i), CYAN[4] if on else CYAN[1])
    # Cannon pads on the wings
    for x, y in GATE_PADS:
        ring = ellipse_mask(x, y, 12, 10)
        socket = ellipse_mask(x, y, 9, 7)
        shade(c, ring - socket, COPPER, bevel=1.5, contrast=2.0, bias=-0.1)
        shade(c, socket, VIOLET[:3], bevel=2.0, bias=-0.2)
        outline(c, ring, OUTLINE)
    # Power crystal at the back, its line to the portal
    for y in range(10, int(cy - ry) + 1):
        c.set_at((round(cx) - 1, y), CYAN[2] if (y + frame * 2) % 6 < 3 else CYAN[0])
        c.set_at((round(cx), y), CYAN[3] if (y + frame * 2) % 6 < 3 else CYAN[1])
    crystal = mask_of([[(cx, 2), (cx + 6, 11), (cx, 22), (cx - 6, 11)]], (w, h))
    for x, y in crystal:
        lit = x <= cx
        v = 0.5 + (0.2 if y < 11 else 0) + dither(x, y) * 0.2
        ramp = [VIOLET[5], CYAN[0], CYAN[1], CYAN[2], CYAN[3]] if lit else [VIOLET[0], VIOLET[1], VIOLET[2], VIOLET[3]]
        c.set_at((x, y), ramp[max(0, min(len(ramp) - 1, int(v * len(ramp))))])
    outline(c, crystal, (30, 24, 70))
    # Portal in a copper ring
    ring = ellipse_mask(cx, cy, rx + 4, ry + 4)
    shade(c, ring, COPPER, bevel=2.5, contrast=2.2)
    outline(c, ring, OUTLINE)
    _portal(c, frame, flare)
    # The two arches of the gate, around the portal
    arch_l = mask_of([[(cx - 22, 12), (cx - 34, 18), (cx - 44, 34), (cx - 47, 52), (cx - 43, 70), (cx - 33, 84),
                       (cx - 24, 88), (cx - 31, 72), (cx - 35, 52), (cx - 32, 34), (cx - 24, 22), (cx - 14, 16)]], (w, h))
    arch_r = {(round(2 * cx) - x, y) for x, y in arch_l}
    for arch in (arch_l, arch_r):
        inner = {p for p in arch if distance(arch)[p] >= 3}
        shade(c, arch, COPPER, bevel=3.0, contrast=2.2)
        shade(c, {p for p in inner if p[1] % 7 < 4}, VIOLET[2:6], bevel=1.5, bias=0.1)
    outline(c, arch_l | arch_r, OUTLINE)
    # Lights on the arches
    for x, y in ((cx - 44, 40), (cx - 44, 62), (cx + 44, 40), (cx + 44, 62)):
        c.set_at((round(x), y), CYAN[4] if frame % 3 else CYAN[2])
    outline(c, body, OUTLINE)
    return c


# ------------------ Terran Starport ------------------
# Keep in sync with src/game/level/level1/Starport.py (PAD)
PORT_W, PORT_H = 200, 124
PORT_PAD = (100, 40)


def octagon(cx, cy, r):
    k = r * 0.41
    return [(cx - k, cy - r), (cx + k, cy - r), (cx + r, cy - k), (cx + r, cy + k), (cx + k, cy + r),
            (cx - k, cy + r), (cx - r, cy + k), (cx - r, cy - k)]


def starport(frame):
    w, h = PORT_W, PORT_H
    c = canvas(w, h)
    px, py = PORT_PAD
    hull = mask_of([[(22, 26), (178, 26), (198, 44), (199, h - 1), (0, h - 1), (1, 44)]], (w, h))
    pad = mask_of([octagon(px, py, 24)], (w, h))
    hull -= pad
    shade(c, hull, STEEL, bevel=5.0, contrast=1.5, gradient=0.35, bias=-0.15, dither=0.1)
    # Plates: panel lines and rivets
    for y in (62, 86, 108):
        for x in range(2, w - 2):
            if (x, y) in hull:
                c.set_at((x, y), STEEL[1])
                if (x, y + 1) in hull:
                    c.set_at((x, y + 1), STEEL[4])
    for x in (30, 70, 130, 170):
        for y in range(46, h):
            if (x, y) in hull:
                c.set_at((x, y), STEEL[1])
    for x in range(10, w - 10, 12):
        for y in (50, 96):
            if (x, y) in hull:
                c.set_at((x, y), STEEL[5])
    # Rows of lit windows
    for x0, y in ((84, 96), (84, 100), (12, 100), (150, 104)):
        for i in range(0, 34, 3):
            if (x0 + i, y) in hull and (x0 + i + 1, y) in hull:
                lit = (x0 * 7 + i * 13 + y) % 5 != 0
                c.set_at((x0 + i, y), (250, 220, 140) if lit else STEEL[0])
                c.set_at((x0 + i + 1, y), (200, 160, 90) if lit else STEEL[0])
    # Exhaust vents
    for x0 in (60, 128):
        for i in range(4):
            for x in range(x0, x0 + 12):
                c.set_at((x, 72 + i * 3), STEEL[0])
    # Control tower (left): a dome ringed with lit windows
    tower = ellipse_mask(36, 76, 16, 15)
    shade(c, tower, STEEL, bevel=4.0, contrast=2.0, bias=0.08)
    outline(c, tower, T_OUTLINE)
    for k in range(12):
        a = k / 12 * math.tau
        x, y = round(36 + math.cos(a) * 11), round(76 + math.sin(a) * 10)
        c.set_at((x, y), (120, 200, 255) if (k + frame) % 6 else (230, 250, 255))
    c.set_at((32, 71), WHITE)
    # Hangar (right): a block with the red stripes of the Terran fleet
    hangar = rect_mask(140, 52, 44, 44)
    shade(c, hangar, STEEL, bevel=3.0, contrast=1.8, bias=0.05)
    for y in range(56, 92, 8):
        for x in range(144, 180):
            c.set_at((x, y), RED[1])
            c.set_at((x, y + 1), RED[0])
    outline(c, hangar, T_OUTLINE)
    # Launch pad: dark deck, a hazard ring, a white circle and a cross
    deck = pad
    shade(c, deck, STEEL[:4], bevel=3.0, contrast=1.4, bias=-0.1)
    d = distance(deck)
    for x, y in deck:
        if d[(x, y)] <= 3:
            stripe = ((x + y) // 4) % 2 == 0
            c.set_at((x, y), YELLOW[1] if stripe else STEEL[0])
    for k in range(48):
        a = k / 48 * math.tau
        c.set_at((round(px + math.cos(a) * 13), round(py + math.sin(a) * 13)), STEEL[6])
    for i in range(-6, 7):
        c.set_at((px + i, py), STEEL[5])
        c.set_at((px, py + i), STEEL[5])
    # Landing lights around the pad, running around it
    for k in range(8):
        a = k / 8 * math.tau + math.pi / 8
        on = (k + frame) % 4 == 0
        c.set_at((round(px + math.cos(a) * 19), round(py + math.sin(a) * 19)), GREEN if on else (40, 90, 60))
    outline(c, deck, T_OUTLINE)
    # Warning lights on the front corners, blinking
    for x in (24, 176):
        c.set_at((x, 30), RED[2] if frame % 2 == 0 else RED[0])
    outline(c, hull | deck, T_OUTLINE)
    return c


def preview(path, images):
    """ Every image at 4x on a dark background """
    scale = 4
    width = 1600
    x = y = 10
    row = 0
    placed = []
    for image in images:
        w, h = image.get_width() * scale, image.get_height() * scale
        if x + w > width:
            x, y = 10, y + row + 10
            row = 0
        placed.append((image, (x, y)))
        x += w + 10
        row = max(row, h)
    out = pygame.Surface((width, y + row + 10))
    out.fill((6, 7, 18))
    for image, pos in placed:
        out.blit(pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale)), pos)
    pygame.image.save(out, path)


def main():
    pygame.init()
    sheets = {
        "PhotonCannon/CannonIdle": sheet_frames(cannon),
        "PhotonCannon/CannonAttack": sheet_frames(lambda i: cannon(i, charge=(i + 1) / FRAMES)),
        "PhotonCannon/CannonUnpowered": sheet_frames(lambda i: cannon(i, powered=False)),
        "Pylon/PylonIdle": sheet_frames(pylon),
    }
    for name in PLATFORMS:
        sheets[f"Outpost/Platform{name}"] = sheet_frames(lambda i: platform(name, i))
        sheets[f"Outpost/Platform{name}Unpowered"] = [platform(name, 0, powered=False)]
    sheets["Starport/Starport"] = sheet_frames(starport)
    sheets["Stargate/StargateIdle"] = sheet_frames(stargate)
    sheets["Stargate/StargateAttack"] = sheet_frames(lambda i: stargate(i, flare=(i + 1) / FRAMES))
    sheets["Stargate/StargateBase"] = [sheets["Stargate/StargateIdle"][0]] * FRAMES
    # Faint: the gate is big and hit all the time, a strong flash would hide it
    sheets["Stargate/StargateHit"] = [silhouette(sheets["Stargate/StargateIdle"][0], (190, 24, 24), a)
                                      for a in (60, 80, 60, 45, 30, 15)]
    sheets["Stargate/StargateDestroy"] = [darken(sheets["Stargate/StargateIdle"][0], i) for i in range(FRAMES)]
    sheets["PhotonCannon/CannonHit"] = [silhouette(sheets["PhotonCannon/CannonIdle"][0], (190, 24, 24), a)
                                        for a in (150, 200, 160, 120, 80, 40)]
    sheets["PhotonCannon/CannonDestroy"] = [darken(sheets["PhotonCannon/CannonIdle"][0], i) for i in range(FRAMES)]
    sheets["Pylon/PylonHit"] = [silhouette(sheets["Pylon/PylonIdle"][0], (190, 24, 24), a)
                                for a in (150, 200, 160, 120, 80, 40)]
    sheets["Pylon/PylonDestroy"] = [darken(sheets["Pylon/PylonIdle"][0], i) for i in range(FRAMES)]
    if len(sys.argv) > 1:
        preview(sys.argv[1], [f for frames in sheets.values() for f in frames])
        return
    for name, frames in sheets.items():
        save_sheet(frames, os.path.join(OUT, f"{name}.png"))


if __name__ == "__main__":
    main()
