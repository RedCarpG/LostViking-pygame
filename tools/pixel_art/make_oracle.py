""" Generate the Oracle sprite sheets (src/asset/image/Enemy/Oracle/...)

Development tool. The Oracle is the Protoss harasser of StarCraft II: a copper hull with a
big crystal, violet claw blades in front and two rear fins. It is drawn at 1x like the other
enemies (no art existed for it), with their palette: every part is shaded from its distance to
the edge (a bevel lit from the upper left) in a few hard steps, with a dark outline.
Faces down, engines at the top. Each sheet has 6 frames side by side:
    OracleNormal   flickering engine flames, the crystal pulsing
    OracleHit      red silhouette fading (drawn over the ship when it is hit)
    OracleAttack   cyan glints gathering at the crystal and the claw tips (charging its beam)
    OracleDestroy  the ship darkening to a black silhouette
    OracleBase     the first frame

Run from the project root:  python tools/pixel_art/make_oracle.py
"""
import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

OUT = "src/asset/image/Enemy/Oracle"
FRAMES = 6

W, H = 64, 78
CX = (W - 1) / 2
# Room above the ship for the engine flames
TOP = 10

OUTLINE = (64, 21, 21)
COPPER = [(147, 42, 42), (186, 69, 41), (212, 102, 33), (223, 118, 53), (235, 145, 89), (245, 183, 102), (255, 230, 198)]
VIOLET = [(48, 30, 110), (75, 44, 155), (72, 59, 176), (80, 90, 186), (79, 121, 190), (91, 138, 200), (159, 194, 239)]
CYAN = [(24, 133, 138), (97, 225, 231), (4, 244, 255), (146, 250, 255), (235, 254, 255)]
WHITE = (246, 246, 246)
LIGHT = (-0.55, -0.75)
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def mirror(points):
    """ Left half outline -> full polygon """
    return points + [(W - 1 - x, y) for x, y in reversed(points)]


def mirror_part(points):
    return [points, [(W - 1 - x, y) for x, y in points]]


def mask_of(polygons):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    for poly in polygons:
        pygame.draw.polygon(s, (255, 255, 255), poly)
    m = pygame.mask.from_surface(s)
    return {(x, y) for y in range(H) for x in range(W) if m.get_at((x, y))}


def distance(mask):
    """ Steps to the outside of the mask (4 neighbours) """
    d = {}
    frontier = [p for p in mask if any((p[0] + dx, p[1] + dy) not in mask
                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for p in frontier:
        d[p] = 1
    level = 1
    while frontier:
        nxt = []
        for x, y in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in mask and q not in d:
                    d[q] = level + 1
                    nxt.append(q)
        frontier = nxt
        level += 1
    return d


def shade(canvas, mask, ramp, bevel=3.0, gradient=0.25, bias=0.0, contrast=1.6, dither=0.12):
    d = distance(mask)

    def h(p):
        return min(d.get(p, 0), bevel) / bevel

    for (x, y) in mask:
        nx = -(h((x + 1, y)) - h((x - 1, y))) / 2
        ny = -(h((x, y + 1)) - h((x, y - 1))) / 2
        light = nx * LIGHT[0] + ny * LIGHT[1]
        value = 0.55 + light * contrast + bias - gradient * (y / H - 0.4)
        value += (BAYER[y & 3][x & 3] / 16 - 0.5) * dither
        index = max(0, min(len(ramp) - 1, int(value * len(ramp))))
        canvas.set_at((x, y), ramp[index])


def outline(canvas, mask):
    for y in range(H):
        for x in range(W):
            if (x, y) in mask:
                continue
            if any((x + dx, y + dy) in mask for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                canvas.set_at((x, y), OUTLINE)


def seam(canvas, mask_a, mask_b, color=OUTLINE):
    """ Dark line where part a touches part b """
    for (x, y) in mask_a:
        if any((x + dx, y + dy) in mask_b for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            canvas.set_at((x, y), color)


# ------------------ Parts ------------------
HULL = mirror([(28, 8), (25, 13), (22, 22), (21, 32), (23, 43), (27, 52), (30, 58)])
CLAW_L = [(22, 25), (14, 29), (8, 37), (6, 47), (8, 57), (13, 65), (20, 72), (25, 75), (22, 68), (18, 60),
          (15, 51), (15, 43), (18, 37), (23, 33)]
FIN_L = [(25, 12), (14, 3), (10, 4), (15, 12), (22, 20)]
CRYSTAL = (CX, 33, 5.5, 7.5)
NOZZLES = [(26, 5, 4, 5), (34, 5, 4, 5)]


def base_ship():
    canvas = pygame.Surface((W, H), pygame.SRCALPHA)
    hull = mask_of([HULL])
    claws = mask_of(mirror_part(CLAW_L)) - hull
    fins = mask_of(mirror_part(FIN_L)) - hull
    nozzles = set()
    for x0, y0, w, h in NOZZLES:
        nozzles |= {(x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h)}
    nozzles -= hull
    everything = hull | claws | fins | nozzles

    shade(canvas, claws, VIOLET, bevel=2.5, gradient=0.3)
    shade(canvas, fins, VIOLET, bevel=2.0, bias=0.1)
    # Copper rim on the outer edge of the claws and fins
    for part in (claws, fins):
        d = distance(part)
        for (x, y) in part:
            outer = (x < CX and (x - 1, y) not in part) or (x > CX and (x + 1, y) not in part)
            if d[(x, y)] == 1 and outer:
                canvas.set_at((x, y), COPPER[5] if y < 50 else COPPER[3])
    shade(canvas, hull, COPPER, bevel=4.0, contrast=2.2, dither=0.05)
    shade(canvas, nozzles, COPPER, bevel=1.5, bias=-0.2)
    seam(canvas, claws, hull)
    seam(canvas, fins, hull)

    # Ridge along the hull, panel lines
    for y in range(11, 25):
        canvas.set_at((int(CX), y), COPPER[6] if y < 18 else COPPER[5])
        canvas.set_at((int(CX) + 1, y), COPPER[3])
    for y in range(42, 55):
        canvas.set_at((int(CX), y), COPPER[5])
        canvas.set_at((int(CX) + 1, y), COPPER[2])
    for x in range(24, 40):
        if (x, 40) in hull:
            canvas.set_at((x, 40), COPPER[0])
    # Gold bands across the claws, cyan lights on the hull beside the crystal
    for band_y in (34, 50):
        for x in range(W // 2):
            if (x, band_y) in claws:
                canvas.set_at((x, band_y), COPPER[5])
                canvas.set_at((W - 1 - x, band_y), COPPER[5])
    for x, y in ((23, 29), (23, 37)):
        canvas.set_at((x, y), CYAN[2])
        canvas.set_at((W - 1 - x, y), CYAN[2])

    outline(canvas, everything)
    return canvas, everything


def crystal(canvas, glow=0.0):
    cx, cy, rx, ry = CRYSTAL
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            r = math.hypot((x - cx) / rx, (y - cy) / ry)
            if r <= 1.0:
                # Brighter toward the upper left
                v = 1 - r + 0.25 * (-(x - cx) / rx - (y - cy) / ry) * 0.5 + glow * 0.35
                v += (BAYER[y & 3][x & 3] / 16 - 0.5) * 0.15
                canvas.set_at((x, y), CYAN[max(0, min(len(CYAN) - 1, int(v * len(CYAN) + 0.6)))])
            elif r <= 1.18:
                canvas.set_at((x, y), OUTLINE if r > 1.1 else COPPER[0])
    # Specular
    canvas.set_at((int(cx) - 2, int(cy) - 4), WHITE)
    canvas.set_at((int(cx) - 1, int(cy) - 4), WHITE)
    canvas.set_at((int(cx) - 2, int(cy) - 3), WHITE)


def flames(canvas, frame):
    """ Feathery cyan flames over the two nozzles, flickering from frame to frame """
    heights = (7, 9, 8, 10, 7, 9)
    for i, (x0, y0, w, h) in enumerate(NOZZLES):
        y0 += TOP
        height = heights[(frame + i * 3) % 6]
        top = y0 - height
        for y in range(max(0, top), y0):
            t = (y0 - y) / height
            # Narrows toward the tip, wobbling
            half = (w / 2 + 0.6) * (1 - t * 0.75) + 0.4 * math.sin((y + frame * 2 + i) * 1.3)
            cx = x0 + (w - 1) / 2
            for x in range(x0 - 1, x0 + w + 1):
                dist = abs(x - cx)
                if dist > half:
                    continue
                if dist < half * 0.4 and t < 0.45:
                    color = CYAN[4]
                elif t < 0.75:
                    color = CYAN[3] if dist < half * 0.7 else CYAN[2]
                else:
                    color = CYAN[1]
                canvas.set_at((x, y), color)
        # A spark above the flame
        spark_y = top - 1 - (frame % 3)
        if spark_y >= 0:
            canvas.set_at((x0 + (frame + i) % w, spark_y), CYAN[3])


def frame(index):
    ship, mask = base_ship()
    crystal(ship, glow=0.5 + 0.5 * math.sin(index / 6 * math.tau))
    # Lights at the claw tips
    on = index % 3 != 2
    for x, y in ((22, 70), (W - 23, 70)):
        ship.set_at((x, y), CYAN[3] if on else CYAN[0])
    canvas = pygame.Surface((W, H + TOP), pygame.SRCALPHA)
    canvas.blit(ship, (0, TOP))
    flames(canvas, index)
    return canvas


# ------------------ Sheets ------------------

def silhouette(surface, color, alpha):
    mask = pygame.mask.from_surface(surface)
    return mask.to_surface(setcolor=(*color, alpha), unsetcolor=(0, 0, 0, 0))


def attack_frame(ship, index):
    """ Glints gathering at the crystal and the claw tips, brighter every frame """
    c = pygame.Surface(ship.get_size(), pygame.SRCALPHA)
    t = (index + 1) / FRAMES
    cx, cy = CX, CRYSTAL[1] + TOP
    reach = 4 + 8 * t
    for k in range(8):
        angle = k / 8 * math.tau + index * 0.4
        for r in range(int(reach * 0.5), int(reach)):
            x, y = round(cx + math.cos(angle) * (r + 6)), round(cy + math.sin(angle) * (r + 8))
            c.set_at((x, y), CYAN[3] if r < reach * 0.8 else CYAN[2])
    for x, y in ((22, 70 + TOP), (W - 23, 70 + TOP)):
        size = 1 + index // 2
        pygame.draw.line(c, CYAN[3], (x - size, y), (x + size, y))
        pygame.draw.line(c, CYAN[3], (x, y - size), (x, y + size))
        c.set_at((x, y), CYAN[4])
    return c


def destroy_frame(ship, index):
    """ Darkens step by step, the last frames are dark silhouettes """
    levels = (255, 200, 150, 105, 60, 0)
    c = ship.copy()
    v = levels[index]
    c.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
    if index >= 4:
        c = silhouette(ship, (12, 8, 16) if index == 5 else (34, 24, 30), 255)
    return c


def save_sheet(frames, name):
    sheet = pygame.Surface((W * len(frames), frames[0].get_height()), pygame.SRCALPHA)
    for i, f in enumerate(frames):
        sheet.blit(f, (i * W, 0))
    path = os.path.join(OUT, f"Oracle{name}.png")
    pygame.image.save(sheet, path)
    print(f"saved {path} {sheet.get_size()}")


def main():
    pygame.init()
    os.makedirs(OUT, exist_ok=True)
    normal = [frame(i) for i in range(FRAMES)]
    save_sheet(normal, "Normal")
    save_sheet([normal[0]] * FRAMES, "Base")
    save_sheet([silhouette(normal[0], (190, 24, 24), a) for a in (150, 200, 160, 120, 80, 40)], "Hit")
    save_sheet([attack_frame(normal[0], i) for i in range(FRAMES)], "Attack")
    save_sheet([destroy_frame(normal[0], i) for i in range(FRAMES)], "Destroy")


if __name__ == "__main__":
    main()
