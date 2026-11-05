"""Low-poly models of the temperate industries, for render_industries.py.

Every industry tile gfx belongs to a unit: a single tile or a group of tiles
the layouts in table/build_industry.h always place together (factory 2x2,
coal mine head frame + winding house, bank 2x1, ...). A unit is modelled
once in unit coordinates (tile (tx, ty) covers x 16tx..16tx+16, y 16ty..16ty+16,
OpenTTD units, see build_kit.py) and cut per tile.

UNITS[name] = dict(
    tiles={gfx: (tx, ty)},
    build=fn(k, kind, frame) -> fills Kit k with the buildings for a construction
        kind ('found', 'partial', 'final') or animation frame,
    ground=fn(sprite, kind) -> (base texture, decals Kit, props Kit) for a ground sprite,
    foot={gfx: [(x0, y0, x1, y1)]} footprint of the building per tile for construction stages,
)
Recolour (industry random colour) materials are the build_kit 'cc*' materials.
"""

import math

import build_kit as bk

CC = {"cc", "cc_light", "cc_flat"}


# --- shared building parts ---------------------------------------------------------------------

def hall(k, x0, x1, y0, y1, h, wall="brick", roof="roof_metal", kind="gable", axis="x", ridge=None, windows=True,
         glass="glass", band=None):
    """Industrial hall: walls, optional windows on the visible walls, gable / flat / sawtooth roof."""
    k.box(x0, x1, y0, y1, 0, h, wall)
    if windows:
        k.windows(x0, x1, y0, y1, 0, h, floor=max(h, 7.0), ww=1.2, wh=min(4.0, h - 3.0), pitch=2.4, sill=2.2,
                  glass=glass, frame="frame" if wall != "brick" else "cream")
    if band:
        k.box(x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, h - 1.2, h - 0.2, band)
    if kind == "gable":
        k.gable(x0, x1, y0, y1, h, h + (ridge if ridge else 4.0), axis, roof, wall, over=0.5, thick=0.4)
    elif kind == "saw":
        n = max(2, round(((x1 - x0) if axis == "y" else (y1 - y0)) / 4))
        k.sawtooth(x0, x1, y0, y1, h, 3.5, n, axis, roof, "glass_light")
    else:
        k.flat_roof(x0, x1, y0, y1, h, wall, roof="roof_flat", parapet=0.8)


def chimney(k, x, y, top, r=1.0, mat="brick", band="white_band"):
    k.cyl(x, y, r * 1.25, 0, 3, mat, n=10)
    k.cyl(x, y, r, 3, top, mat, n=10, r_top=r * 0.8)
    k.cyl(x, y, r * 0.95, top - 4.5, top - 3.0, band, n=10)
    k.cyl(x, y, r * 0.95, top - 0.6, top, "dark", n=10)


def tank(k, x, y, r, h, mat="tank", band="cc", roof="steel"):
    k.cyl(x, y, r, 0, h, mat, n=16)
    if band:
        k.cyl(x, y, r + 0.05, h * 0.55, h * 0.75, band, n=16)
    k.lathe(x, y, [(r + 0.05, h), (r * 0.6, h + r * 0.25), (0.01, h + r * 0.32)], roof, n=16)


def conveyor(k, p0, p1, w=1.2, mat="steel_dark", belt="coal"):
    """Inclined conveyor gallery between two points with a support at the low end."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    k.rod((x0, y0, z0), (x1, y1, z1), w * 0.5, mat, n=4)
    k.rod((x0, y0, z0 + 0.8), (x1, y1, z1 + 0.8), w * 0.35, belt, n=4)
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) // 5))
    for i in range(1, n + 1):
        t = i / (n + 1)
        x, y, z = bk.lerp(x0, x1, t), bk.lerp(y0, y1, t), bk.lerp(z0, z1, t)
        k.rod((x, y, 0), (x, y, z), 0.15, "steel", n=4)


def pipe_run(k, pts, r=0.35, mat="pipe"):
    for a, b in zip(pts, pts[1:]):
        k.rod(a, b, r, mat, n=6)


def stairs_tower(k, x, y, h, mat="steel"):
    for c in ((x - 0.6, y - 0.6), (x + 0.6, y - 0.6), (x - 0.6, y + 0.6), (x + 0.6, y + 0.6)):
        k.rod((c[0], c[1], 0), (c[0], c[1], h), 0.07, mat, n=3)
    z = 4.0
    while z < h:
        k.cbox(x, y, 1.4, 1.4, z, z + 0.2, mat)
        z += 4.0


def truck(k, x, y, axis="x", body="cc", load=None):
    """Small lorry, length along axis, cab towards +axis."""
    if axis == "x":
        k.cbox(x, y, 4.2, 1.7, 0.6, 3.6, body)
        k.cbox(x + 2.9, y, 1.6, 1.7, 0.6, 4.2, "white")
        k.cbox(x + 3.5, y, 0.4, 1.4, 2.2, 3.9, "glass")
    else:
        k.cbox(x, y, 1.7, 4.2, 0.6, 3.6, body)
        k.cbox(x, y + 2.9, 1.7, 1.6, 0.6, 4.2, "white")
        k.cbox(x, y + 3.5, 1.4, 0.4, 2.2, 3.9, "glass")
    if load:
        k.heap(x if axis == "y" else x - 0.3, y if axis == "x" else y - 0.3, 1.6 if axis == "x" else 0.6,
               0.6 if axis == "x" else 1.6, 1.4, load, seed=int(x * 7 + y))


def rails(d, x0, x1, y, mat="steel_dark"):
    """Siding along x (decals): ballast and two rails."""
    d.box(x0, x1, y - 1.4, y + 1.4, 0.03, 0.06, "gravel")
    for off in (-0.6, 0.6):
        d.box(x0, x1, y + off - 0.1, y + off + 0.1, 0.06, 0.2, mat)


def pallets(k, x, y, n=3, mat="wood", load="cc_flat", seed=0):
    import random
    rng = random.Random(seed)
    for i in range(n):
        xx, yy = x + (i % 2) * 2.2, y + (i // 2) * 2.2
        k.cbox(xx, yy, 1.8, 1.8, 0, 0.4, mat)
        k.cbox(xx, yy, 1.6, 1.6, 0.4, 0.4 + rng.uniform(1.5, 3.0), load)


def no_ground(sprite, kind):
    return "industry/yard", bk.Kit(), bk.Kit()


# --- coal mine ---------------------------------------------------------------------------------

def sheave(k, cx, cy, cz, r, angle, mat="cc"):
    """Head frame sheave wheel in the y-z plane, spokes rotated by angle."""
    n = 14
    pts = [(cx, cy + r * math.cos(i * math.tau / n), cz + r * math.sin(i * math.tau / n) * 2.45) for i in range(n)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        k.rod(a, b, 0.22, mat, n=4)
    for i in range(3):
        t = angle + i * math.tau / 6
        dy, dz = r * math.cos(t), r * math.sin(t) * 2.45
        k.rod((cx, cy - dy, cz - dz), (cx, cy + dy, cz + dz), 0.12, mat, n=4)
    k.rod((cx - 0.4, cy, cz), (cx + 0.4, cy, cz), 0.35, "steel_dark", n=6)


def coal_head(k, kind, frame):
    """Head frame over the shaft (tile 0, 0) and the winding engine house (tile 0, 1)."""
    if kind == "found":
        bk.foundations(k, [(8, 1, 15, 8)])
        bk.foundations(k, [(3, 19, 15, 26)])
        return
    top = 36.0
    legs = [(8.5, 1.5), (14.5, 1.5), (8.5, 7.5), (14.5, 7.5)]
    parts = bk.Kit()
    for x, y in legs:
        parts.rod((x, y, 0), (bk.lerp(x, 11.5, 0.3), bk.lerp(y, 4.5, 0.3), top), 0.35, "steel_dark", n=4)
    for z in (9.0, 18.0, 27.0):
        t = z / top * 0.3
        c = [(bk.lerp(x, 11.5, t), bk.lerp(y, 4.5, t), z) for x, y in legs]
        for a, b in ((0, 1), (1, 3), (3, 2), (2, 0)):
            parts.rod(c[a], c[b], 0.18, "steel_dark", n=4)
    # Back legs leaning towards the winding house.
    for x in (9.5, 13.5):
        parts.rod((x, 14.5, 0), (x, 6.0, top - 2), 0.4, "steel_dark", n=4)
    parts.cbox(11.5, 4.5, 6.5, 6.5, top - 1, top, "steel")
    angle = {2014: 1, 2015: 2}.get(frame, 0) * math.tau / 18  # animation frames turn the sheaves
    for x in (10.2, 12.8):
        sheave(parts, x, 4.5, top + 3.2, 2.6, angle)
    parts.cbox(11.5, 4.5, 4.0, 4.0, 0, 4.5, "concrete")
    # Winding engine house with ropes up to the sheaves.
    hall(parts, 3, 15, 19, 26, 14, wall="brick", roof="roof_slate", axis="y", ridge=5)
    parts.cbox(9, 26.4, 3.0, 0.4, 0, 6, "door")
    chimney(parts, 4.5, 20.5, 26, r=0.8)
    for x in (10.2, 12.8):
        parts.rod((x, 2.0 + 4.5, top + 3.2 + 2.6 * 2.45 * 0.3), (x, 19.0, 11.0), 0.08, "dark", n=3)
    if kind == "partial":
        parts.parts = bk.clip_parts(parts.parts, ztop=top * 0.45, close_top=False)
        bk.scaffold(parts, [(8, 1, 15, 8)], top * 0.45)
        bk.scaffold(parts, [(3, 19, 15, 26)], 7)
    k.parts += parts.parts


def coal_bunker(k, kind, frame):
    def model(k):
        for x, y in ((5, 5), (11.5, 5), (5, 11.5), (11.5, 11.5)):
            k.box(x - 0.4, x + 0.4, y - 0.4, y + 0.4, 0, 12, "concrete")
        k.prism([(4.5, 4.5), (12, 4.5), (12, 12), (4.5, 12)], 12, 14, "concrete")
        k.box(4, 12.5, 4, 12.5, 14, 26, "roof_metal")
        k.box(3.8, 12.7, 3.8, 12.7, 23.5, 24.5, "cc")
        k.gable(4, 12.5, 4, 12.5, 26, 29, "x", "steel_dark", "roof_metal", over=0.3, thick=0.3)
        k.cbox(8.25, 8.25, 2.0, 2.0, 9.5, 12, "steel_dark")
        conveyor(k, (8.25, -2.0, 6.0), (8.25, 4.0, 22.0))
        k.box(12.5, 12.8, 6, 10, 15, 22, "glass")
    bk.staged(k, model, {"found": 0, "partial": 1, "final": 2}[kind], [(4, 4, 12.5, 12.5)])


def coal_ground(sprite, kind):
    d, g = bk.Kit(), bk.Kit()
    if sprite == 2022:
        return "industry/yard", d, g
    seed = sprite - 2022
    if sprite == 2023:
        g.heap(6, 7, 5.5, 5.0, 9.0, "coal", seed=1)
        g.heap(12, 12, 3.5, 3.0, 5.0, "coal", seed=2)
    elif sprite == 2024:
        g.heap(8, 8, 6.5, 6.0, 11.0, "coal", seed=3)
        truck(g, 13.5, 3, "y", body="cc", load="coal")
    else:
        g.heap(5, 10, 4.0, 4.5, 7.0, "coal", seed=4)
        g.heap(11, 5, 4.0, 3.5, 6.0, "coal", seed=5)
        g.heap(12, 12.5, 2.5, 2.5, 3.0, "coal", seed=6)
    return "industry/coalyard", d, g


# --- power station -----------------------------------------------------------------------------

def cooling_tower(k, kind, frame):
    cx, cy = 8, 8
    if kind == "found":
        k.cyl(cx, cy, 6.8, 0, 1.0, "concrete", n=20)
        k.cyl(cx, cy, 5.6, 1.0, 1.2, "dark", n=20)
        return
    k.cyl(cx, cy, 6.5, 0, 0.6, "concrete", n=20)
    for i in range(16):
        a = i * math.tau / 16
        x, y = cx + 6.1 * math.cos(a), cy + 6.1 * math.sin(a)
        k.rod((x, y, 0.6), (cx + 6.4 * math.cos(a + 0.2), cy + 6.4 * math.sin(a + 0.2), 4), 0.25, "concrete_dark", n=4)
    prof = [(6.4, 4), (5.6, 14), (5.0, 26), (4.8, 34), (4.95, 40), (5.2, 44)]
    if kind == "partial":
        prof = [p for p in prof if p[1] <= 26]
    k.lathe(cx, cy, prof, "concrete", n=20)
    top = prof[-1]
    k.lathe(cx, cy, [(top[0] - 0.05, top[1] - 0.1), (top[0] - 0.6, top[1] - 0.1), (top[0] - 0.6, top[1] - 6)],
            "concrete_dark", n=20)
    k.cyl(cx, cy, top[0] - 0.7, top[1] - 6, top[1] - 5.6, "dark", n=20)
    if kind == "partial":
        k.lathe(cx, cy, [(top[0] + 0.6, top[1]), (top[0] + 0.6, top[1] + 1.2)], "wood", n=20)
    else:
        k.cyl(cx, cy, top[0] + 0.03, 36, 38, "red", n=20)


def turbine_hall(k, kind, frame):
    def model(k):
        hall(k, 0.5, 15.5, 2.5, 9.5, 18, wall="concrete", roof="roof_metal", axis="x", ridge=3, band="cc")
        k.box(1, 9, 9.5, 13.5, 0, 26, "brick")
        k.windows(1, 9, 9.5, 13.5, 0, 26, floor=8, ww=1.0, wh=4.5, pitch=2.2, sill=2.0)
        k.flat_roof(1, 9, 9.5, 13.5, 26, "brick", parapet=0.6)
        k.box(0.8, 9.2, 9.3, 13.7, 24, 25, "cc")
        chimney(k, 14.0, 12.6, 60, r=1.4)  # the game emits the smoke at (15, 14, 59)
        k.box(9, 12, 10, 12.5, 0, 9, "concrete_dark")
    bk.staged(k, model, {"found": 0, "partial": 1, "final": 2}[kind], [(0.5, 2.5, 15.5, 13.5)])


def boiler_house(k, kind, frame):
    def model(k):
        hall(k, 1.5, 9.5, 0.5, 14.5, 14, wall="brick", roof="roof_slate", axis="y", ridge=4)
        k.box(9.5, 14.5, 4, 14.5, 0, 9, "concrete")
        k.flat_roof(9.5, 14.5, 4, 14.5, 9, "concrete", parapet=0.5)
        k.roller_door("x", 14.5, 14.5, 9.25, w=4.0, h=6.5)
        conveyor(k, (12, 0.5, 9), (5.5, 7, 18))
        k.cbox(12, 1.5, 3.0, 3.0, 0, 9.5, "steel_dark")
    bk.staged(k, model, {"found": 0, "partial": 1, "final": 2}[kind], [(1.5, 0.5, 14.5, 14.5)])


TRANSFORMER_INSULATORS = [(4.0, 4.0), (4.0, 8.0), (4.0, 12.0), (10.0, 4.0), (10.0, 8.0), (10.0, 12.0)]


def transformer(k, kind, frame):
    """Switchyard: transformers, insulators and a gantry; frames 2055-2060 are the sparks alone."""
    if frame in range(2055, 2061):
        x, y = TRANSFORMER_INSULATORS[frame - 2055]
        z = 13.5
        import random
        rng = random.Random(frame)
        pts = [(x, y, z)]
        for _ in range(4):
            px, py, pz = pts[-1]
            pts.append((px + rng.uniform(-0.8, 0.8), py + rng.uniform(-0.8, 0.8), pz + rng.uniform(1.0, 2.5)))
        for a, b in zip(pts, pts[1:]):
            k.rod(a, b, 0.12, "spark", n=3)
        k.blob(x, y, z + 0.5, 0.7, 0.7, 1.6, "spark", subdiv=1)
        return
    for x0 in (2.0, 8.0):
        k.box(x0, x0 + 4.0, 2.0, 14.0, 0, 0.6, "concrete")
        k.box(x0 + 0.5, x0 + 3.5, 2.5, 13.5, 0.6, 7.0, "steel_dark")
        for y in (3.5, 6.5, 9.5, 12.5):
            k.box(x0 + 3.5, x0 + 3.9, y - 0.5, y + 0.5, 1.0, 6.0, "steel")
    for x, y in TRANSFORMER_INSULATORS:
        k.cyl(x, y, 0.35, 7.0, 13.0, "white", n=6)
        for z in (8.5, 10.0, 11.5):
            k.cyl(x, y, 0.65, z, z + 0.4, "white", n=6)
    for y in (1.0, 15.0):
        k.rod((14.5, y, 0), (14.5, y, 30), 0.3, "steel", n=4)
        k.rod((1.5, y, 0), (1.5, y, 30), 0.3, "steel", n=4)
        k.rod((1.5, y, 30), (14.5, y, 30), 0.25, "steel", n=4)
    for x in (1.5, 14.5):
        k.rod((x, 1.0, 30), (x, 15.0, 30), 0.25, "steel", n=4)
    for x, y in TRANSFORMER_INSULATORS:
        k.rod((x, y, 13), (x, 1.0 if y < 8 else 15.0, 29.5), 0.05, "dark", n=3)


# --- sawmill -----------------------------------------------------------------------------------

def logs(k, x0, x1, y, z, r=0.7, axis="x", mat="log"):
    if axis == "x":
        k.rod((x0, y, z + r), (x1, y, z + r), r, mat, n=7)
        k.cyl(x1 + 0.01, y, r * 0.95, 0, 0.01, "log_end")
    else:
        k.rod((y, x0, z + r), (y, x1, z + r), r, mat, n=7)


def log_stack(k, x0, x1, y0, y1, rows=3, r=0.7, axis="x"):
    w = y1 - y0 if axis == "x" else x1 - x0
    n = int(w // (2 * r))
    for row in range(rows):
        m = n - row
        start = (w - m * 2 * r) / 2 + r
        for i in range(m):
            c = (y0 if axis == "x" else x0) + start + i * 2 * r
            z = row * r * 1.75 * 2.45
            if axis == "x":
                k.rod((x0, c, z + r * 2.45), (x1, c, z + r * 2.45), r, "log", n=7)
            else:
                k.rod((c, y0, z + r * 2.45), (c, y1, z + r * 2.45), r, "log", n=7)


def plank_stack(k, x0, x1, y0, y1, h, mat="plank"):
    z = 0.0
    k.box(x0, x1, y0, y1, 0, 0.8, "wood_dark")
    z = 0.8
    while z < h:
        k.box(x0, x1, y0, y1, z, z + 1.6, mat)
        k.box(x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, z + 1.6, z + 2.0, "wood_dark")
        z += 2.0


def saw_shed(k, kind, frame):
    def model(k):
        for x in (1.5, 13.5):
            for y in bk.frange(0.5, 15.5, 5):
                k.cbox(x, y, 0.5, 0.5, 0, 12, "wood_dark")
        k.gable(1.5, 13.5, 0.5, 15.5, 12, 17, "y", "roof_metal", "wood", over=0.6, thick=0.4)
        plank_stack(k, 3, 7, 2, 14, 8)
        plank_stack(k, 8, 12, 2, 9, 6)
    bk.staged(k, model, {"found": 0, "partial": 1, "final": 2}[kind], [(1.5, 0.5, 13.5, 15.5)])


def saw_hall(k, kind, frame):
    def model(k):
        hall(k, 0.5, 15.5, 2, 10, 13, wall="wood", roof="roof_metal", axis="x", ridge=5, band=None)
        k.roller_door("y", 15.5, 10, 4, w=4.0, h=8.0)
        k.box(0.5, 15.5, 10, 14.5, 0, 0.8, "concrete")
        log_stack(k, 9, 15.5, 11, 14.5, rows=2, r=0.6, axis="x")
        k.cbox(6, 12.5, 2.0, 2.0, 0, 9, "cc")
        conveyor(k, (2, 12.5, 2), (2, 9.5, 8), belt="log")
    bk.staged(k, model, {"found": 0, "partial": 1, "final": 2}[kind], [(0.5, 2, 15.5, 14.5)])


def saw_office(k, kind, frame):
    def model(k):
        hall(k, 1.5, 9.5, 1.5, 14.5, 10, wall="cream", roof="roof_tile", axis="y", ridge=5)
        k.door("x", 9.5, 14.5, 4, w=1.6, h=5)
        k.box(9.5, 14.5, 6.5, 14.5, 0, 14, "wood")
        k.box(9.3, 14.7, 6.3, 14.7, 12.5, 14, "cc")
        k.flat_roof(9.5, 14.5, 6.5, 14.5, 14, "wood", parapet=0.0)
        chimney(k, 12, 9, 22, r=0.7, mat="steel")
    bk.staged(k, model, {"found": 0, "partial": 1, "final": 2}[kind], [(1.5, 1.5, 14.5, 14.5)])


def saw_logs(k, kind, frame):
    log_stack(k, 1, 15, 1, 7, rows=3, r=0.75, axis="x")
    log_stack(k, 1, 12, 8, 13, rows=2, r=0.7, axis="x")
    k.cbox(14, 11, 2.0, 3.6, 0, 4, "yellow")
    k.cbox(14, 11, 1.6, 2.0, 4, 6.5, "glass")
    k.rod((14, 9.5, 5), (14, 7, 10), 0.25, "steel_dark", n=4)


def saw_planks(k, kind, frame):
    for i, (x0, y0) in enumerate(((1, 1.5), (6, 1.5), (11, 1.5), (1, 8), (6, 8))):
        plank_stack(k, x0, x0 + 4, y0, y0 + 5, 6 + 4 * (i % 2))
    k.cbox(13, 11, 3, 2.6, 0, 2.5, "cc")
    k.cbox(13, 11, 1.4, 2.0, 2.5, 4.6, "glass")


# --- forest ------------------------------------------------------------------------------------

FOREST_SCALE = {2072: 0.35, 2073: 0.55, 2074: 0.85, 2075: 1.15}


def forest(k, kind, frame):
    import random
    s = FOREST_SCALE.get(frame, 1.15)
    rng = random.Random(16)
    for i, x in enumerate((2.7, 8.0, 13.3)):
        for j, y in enumerate((2.7, 8.0, 13.3)):
            jx, jy = rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8)
            ss = s * rng.uniform(0.85, 1.05)
            k.cyl(x + jx, y + jy, 0.3 * ss + 0.1, 0, 5 * ss, "trunk", n=5)
            for r, z0, z1 in ((2.4, 3, 14), (1.9, 9, 20), (1.3, 15, 27)):
                k.cyl(x + jx, y + jy, r * ss, z0 * ss, z1 * ss, "conifer", n=7, r_top=0, rot=rng.uniform(0, 1))


def forest_felled(k, kind, frame):
    log_stack(k, 2, 14, 2, 8, rows=2, r=0.6, axis="x")
    for x, y in ((3, 11), (7, 13), (12, 10.5), (13, 14), (9.5, 10)):
        k.cyl(x, y, 0.55, 0, 1.0, "log", n=7)
        k.cyl(x, y, 0.5, 1.0, 1.05, "log_end", n=7)


def forest_ground(sprite, kind):
    return "industry/forest", bk.Kit(), bk.Kit()


# --- oil refinery ------------------------------------------------------------------------------

def ref_tank(k, kind, frame):
    cx, cy = 8, 8
    if kind == "found":
        k.cyl(cx, cy, 6.8, 0, 1.2, "concrete", n=20)
        return
    h = 22 if kind == "final" else 10
    k.cyl(cx, cy, 6.6, 0, 1.0, "concrete", n=20)
    k.cyl(cx, cy, 6.3, 1.0, 1.0 + h, "tank", n=20)
    k.cyl(cx, cy, 6.35, 1.0 + h * 0.62, 1.0 + h * 0.82, "cc", n=20)
    if kind == "final":
        k.lathe(cx, cy, [(6.35, 23), (5.0, 24.6), (0.01, 25.6)], "steel", n=20)
        for i in range(9):
            a = 0.2 + i * 0.16
            z = 1 + i * 2.4
            k.cbox(cx + 6.6 * math.cos(a), cy + 6.6 * math.sin(a), 0.8, 0.8, z, z + 0.25, "steel_dark")
    else:
        bk.scaffold(k, [(1.7, 1.7, 14.3, 14.3)], h)


def ref_columns(k, kind, frame):
    def model(k):
        for x, y, r, h in ((6, 6.5, 1.8, 58), (10.5, 9.5, 1.3, 44)):
            k.cyl(x, y, r + 0.5, 0, 2, "concrete", n=10)
            k.cyl(x, y, r, 2, h, "tank", n=12)
            k.lathe(x, y, [(r, h), (r * 0.5, h + 1.2), (0.01, h + 1.6)], "tank", n=12)
            for z in bk.frange(10, h - 4, 12):
                k.cyl(x, y, r + 0.7, z, z + 0.4, "cc", n=12)
            k.cyl(x, y, r + 0.03, h - 8, h - 6, "cc", n=12)
        pipe_run(k, [(6, 8.3, 40), (6, 11, 40), (10.5, 11, 40)], r=0.3)
        pipe_run(k, [(7.8, 6.5, 50), (12, 6.5, 50), (12, 6.5, 0)], r=0.35)
        stairs_tower(k, 4, 10, 56)
    bk.staged(k, model, {"found": 0, "partial": 1, "final": 2}[kind], [(3, 3, 13, 12)])


def ref_flare(k, kind, frame):
    cx, cy = 7.5, 7.5
    if kind == "found":
        k.cbox(cx, cy, 6, 6, 0, 1.2, "concrete")
        return
    k.cbox(cx, cy, 5.5, 5.5, 0, 1.0, "concrete")
    top = 74.0 if kind == "final" else 30.0
    for x, y in ((cx - 2, cy - 2), (cx + 2, cy - 2), (cx - 2, cy + 2), (cx + 2, cy + 2)):
        k.rod((x, y, 1), (bk.lerp(x, cx, 0.7), bk.lerp(y, cy, 0.7), top * 0.6), 0.2, "steel", n=4)
    k.cyl(cx, cy, 0.7, 1, top, "white_band", n=8)
    for z in bk.frange(8, top - 6, 10):
        k.cyl(cx, cy, 0.75, z, z + 4, "red", n=8)
    k.cyl(cx, cy, 1.0, top, top + 1.5, "dark", n=8)
    if kind == "partial":
        bk.scaffold(k, [(cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5)], top - 4)
    if frame == 2086:
        k.blob(cx, cy, top + 5, 1.3, 1.3, 4.0, "fire", subdiv=1)
        k.blob(cx + 0.3, cy - 0.3, top + 9, 0.7, 0.7, 2.6, "glow", subdiv=1)


def ref_frame(k, kind, frame):
    """Process unit: a steel frame with vessels and pipes (frame only at the foundation stage)."""
    x0, x1, y0, y1 = 3, 13, 1, 15
    levels = (0, 13, 26, 39, 50)
    cols = [(x, y) for x in (x0, x1) for y in (y0, 8, y1)]
    k.box(x0 - 0.5, x1 + 0.5, y0 - 0.5, y1 + 0.5, 0, 0.6, "concrete")
    top = {"found": 13, "partial": 39, "final": 50}[kind]
    for x, y in cols:
        k.cbox(x, y, 0.6, 0.6, 0, top, "rust")
    for z in levels[1:]:
        if z > top:
            break
        for (xa, ya), (xb, yb) in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1)),
                                   ((x0, 8), (x1, 8))):
            k.rod((xa, ya, z), (xb, yb, z), 0.3, "rust", n=4)
        k.box(x0, x1, y0, y1, z - 0.3, z, "steel_dark")
    if kind == "found":
        return
    k.rod((5.5, 3, 4), (5.5, 13, 4), 1.6, "tank", n=10)
    k.rod((10.5, 3, 17), (10.5, 13, 17), 1.8, "cc", n=10)
    k.cyl(6, 5, 1.4, 26, 36, "tank", n=10)
    k.cyl(10, 11, 1.6, 26, 37, "cc", n=10)
    if kind == "final":
        k.cyl(8, 8, 1.2, 39, 49, "tank", n=10)
        pipe_run(k, [(13.6, 2, 6), (13.6, 14, 6), (13.6, 14, 30), (8, 14, 30)], r=0.3)
        pipe_run(k, [(2.4, 3, 20), (2.4, 13, 20)], r=0.35, mat="yellow")
        pipe_run(k, [(6, 5, 36), (8, 8, 44)], r=0.25)


def ref_cracker(k, kind, frame):
    def model(k):
        k.box(0.5, 15.5, 0.5, 15.5, 0, 0.6, "concrete")
        k.cyl(5, 5, 2.4, 0.6, 30, "tank", n=14)
        k.lathe(5, 5, [(2.4, 30), (1.2, 32), (0.01, 32.5)], "tank", n=14)
        k.cyl(5, 5, 2.45, 22, 26, "cc", n=14)
        for x, y, r in ((11, 4.5, 2.6), (11.5, 11, 2.2)):
            k.cyl(x, y, 0.6, 0.6, 5, "steel", n=6)
            k.blob(x, y, 5 + r * 2.45, r, r, r * 2.45, "tank", subdiv=2)
        k.box(2, 8, 9, 15, 0.6, 14, "steel_dark")
        k.box(1.8, 8.2, 8.8, 15.2, 11, 12, "cc")
        chimney(k, 5, 12, 44, r=0.9, mat="steel", band="red")
        pipe_run(k, [(5, 7.4, 26), (5, 11, 26)], r=0.4)
        pipe_run(k, [(7.4, 5, 20), (11, 5, 20), (11, 5, 10)], r=0.35)
        pipe_run(k, [(8.2, 12, 8), (11.5, 12, 8), (11.5, 11, 8)], r=0.35, mat="yellow")
    bk.staged(k, model, {"found": 0, "partial": 1, "final": 2}[kind], [(0.5, 0.5, 15.5, 15.5)])


def ref_office(k, kind, frame):
    def model(k):
        k.box(3.5, 12.5, 1.5, 13.5, 0, 9, "white")
        k.windows(3.5, 12.5, 1.5, 13.5, 0, 9, floor=9, ribbon=True, sill=2.4, wh=3.6)
        k.box(3.3, 12.7, 1.3, 13.7, 8, 9.6, "steel_dark")
        k.flat_roof(3.5, 12.5, 1.5, 13.5, 9.6, "white", parapet=0.0)
        k.door("x", 12.5, 13.5, 7.5, w=2.2, h=5, mat="glass_light")
        k.cbox(5.5, 4, 2.0, 2.0, 9.8, 11.5, "steel")
    bk.staged(k, model, {"found": 0, "partial": 1, "final": 2}[kind], [(3.5, 1.5, 12.5, 13.5)])


# --- factory (2x2) -----------------------------------------------------------------------------

def factory(k, kind, frame):
    if kind == "found":
        bk.foundations(k, [(1, 1, 15, 15), (1, 17, 15, 31), (17, 1, 31, 15)])
        k.box(19, 30, 19, 30, 0, 0.5, "concrete")
        k.heap(24, 24, 2.5, 2.0, 3.0, "sand", seed=9)
        return
    m = bk.Kit()
    # N: boiler house with two chimneys; E: office tower; W: production hall with a sawtooth roof.
    hall(m, 1.5, 15.5, 1.5, 15.5, 16, wall="brick", roof="cc", kind="gable", axis="x", ridge=5)
    chimney(m, 4, 4, 46, r=1.2)
    chimney(m, 4, 9, 40, r=1.0)
    m.box(1.5, 14.5, 16.5, 30.5, 0, 30, "brick")
    m.windows(1.5, 14.5, 16.5, 30.5, 0, 30, floor=7.5, ww=1.3, wh=4.0, pitch=2.4, sill=2.0, frame="cream")
    m.flat_roof(1.5, 14.5, 16.5, 30.5, 30, "brick", parapet=0.8)
    m.box(1.3, 14.7, 16.3, 30.7, 27.5, 28.5, "cc")
    m.box(5, 9, 22, 26, 30.8, 36, "cc_light")
    m.box(16.5, 30.5, 1.5, 15.5, 0, 14, "brick")
    m.windows(16.5, 30.5, 1.5, 15.5, 0, 14, floor=14, ww=1.2, wh=6.0, pitch=2.4, sill=3.0, frame="cream")
    m.sawtooth(16.5, 30.5, 1.5, 15.5, 14, 4.0, 4, "y", "cc", "glass_light")
    m.roller_door("x", 30.5, 15.5, 8, w=4.5, h=8)
    m.box(14.5, 16.5, 4, 12, 7, 11, "glass_light")
    if kind == "partial":
        m.parts = bk.clip_parts(m.parts, ztop=12, close_top=False)
        bk.scaffold(m, [(1.5, 1.5, 15.5, 15.5), (1.5, 16.5, 14.5, 30.5), (16.5, 1.5, 30.5, 15.5)], 12)
        # Crane on the yard tile.
        m.cbox(24, 24, 3, 6, 0.5, 4, "yellow")
        m.rod((24, 24, 4), (19, 18, 48), 0.4, "yellow", n=4)
        m.rod((19, 18, 48), (19, 18, 30), 0.06, "dark", n=3)
        m.cbox(19, 18, 2.5, 0.6, 26, 30, "steel_dark")
    k.parts += m.parts


def factory_ground(sprite, kind):
    d, g = bk.Kit(), bk.Kit()
    if sprite == 2149:
        # Yard: lorry bay and pallets of goods.
        d.box(15, 33, 15, 33, 0.03, 0.06, "asphalt")
        for y in (20, 25):
            d.box(17, 31, y - 0.1, y + 0.1, 0.06, 0.08, "marking")
        truck(g, 24, 22.5, "x", body="cc")
        pallets(g, 18, 27, n=4, seed=3)
        pallets(g, 27, 27.5, n=2, seed=4)
    return "industry/concrete", d, g


# --- printing works (2x2) ----------------------------------------------------------------------

def printing(k, kind, frame):
    if kind == "found":
        bk.foundations(k, [(1, 1, 15, 15), (1, 17, 15, 30), (17, 1, 30, 15), (17, 17, 26, 26)])
        return
    m = bk.Kit()
    m.box(1, 31, 1, 15, 0, 16, "white")
    m.box(1, 15, 15, 31, 0, 16, "white")
    for x0, x1, y0, y1 in ((1, 31, 1, 15), (1, 15, 15, 31)):
        m.windows(x0, x1, y0, y1, 0, 16, floor=16, ribbon=True, sill=9, wh=4.0)
        m.box(x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, 13.5, 16.2, "cc")
        m.flat_roof(x0, x1, y0, y1, 16.2, "white", parapet=0.0)
    for x in (6, 22):
        m.box(x, x + 5, 3, 7, 16.4, 19, "steel")
    m.box(3, 11, 3, 11, 16.4, 30, "white")
    m.windows(3, 11, 3, 11, 16.4, 30, floor=7, ribbon=True, sill=1.6, wh=3.6)
    m.box(2.8, 11.2, 2.8, 11.2, 28.5, 30.2, "cc")
    m.flat_roof(3, 11, 3, 11, 30.2, "white", parapet=0.0)
    for y in (19, 25):
        m.roller_door("x", 31, 31, y, w=4.0, h=8) if False else m.roller_door("x", 15, 31, y, w=4.0, h=8)
    m.roller_door("y", 31, 15, 22, w=4.0, h=8)
    # Loading dock with paper rolls on the S tile.
    m.box(17, 31, 17, 23, 0, 3, "concrete")
    m.box(17, 31, 17, 23, 3, 9, "steel")
    m.box(16.8, 31.2, 16.8, 23.4, 8.5, 9.2, "cc")
    for i, (x, y) in enumerate(((19, 26), (22, 26), (25, 26), (19, 29), (22, 29))):
        m.cyl(x, y, 1.2, 0, 5 if i % 2 else 3.5, "paper", n=10)
    if kind == "partial":
        m.parts = bk.clip_parts(m.parts, ztop=9, close_top=False)
        bk.scaffold(m, [(1, 1, 15, 15), (1, 15, 15, 31), (15, 1, 31, 15)], 9)
    k.parts += m.parts


# --- steel mill (2x2 furnace block, 2x1 rolling mill) -----------------------------------------

def steel_block(k, kind, frame):
    """N: blast furnace, E: casting house, W: hot blast stoves, S: ore yard (ground only)."""
    if kind == "found":
        bk.foundations(k, [(3, 3, 13, 13)])
        bk.foundations(k, [(1, 17, 15, 30)])
        bk.foundations(k, [(18, 2, 27, 12)])
        k.box(18, 30, 18, 30, 0, 0.6, "concrete")
        return
    m = bk.Kit()
    if kind == "final":
        m.cyl(8, 8, 4.5, 0, 6, "steel_dark", n=14)
        m.lathe(8, 8, [(4.2, 6), (5.0, 22), (3.4, 40), (2.6, 46)], "rust", n=14)
        m.cyl(8, 8, 2.8, 46, 52, "steel_dark", n=10)
        for a in (0.4, 2.0, 3.6, 5.2):
            m.rod((8 + 3 * math.cos(a), 8 + 3 * math.sin(a), 50), (8 + 3.5 * math.cos(a), 8 + 3.5 * math.sin(a), 64), 0.6,
                  "steel_dark", n=6)
        stairs_tower(m, 13.5, 3, 44)
        conveyor(m, (14, 1, 2), (9, 6, 46), belt="ore")
        m.box(1, 15, 17, 30, 0, 14, "brick")
        m.windows(1, 15, 17, 30, 0, 14, floor=14, ww=1.2, wh=6, pitch=2.6, sill=4, frame="cream")
        m.gable(1, 15, 17, 30, 14, 20, "y", "cc", "brick", over=0.5, thick=0.4)
        m.box(6, 10, 30, 30.4, 0, 8, "glow")
        for x, y in ((20, 4), (25, 4), (20, 10), (25, 10)):
            m.cyl(x, y, 2.3, 0, 30, "steel", n=12)
            m.lathe(x, y, [(2.3, 30), (1.4, 32), (0.01, 33)], "steel", n=12)
            m.cyl(x, y, 2.35, 24, 26, "cc", n=12)
        pipe_run(m, [(20, 4, 28), (10, 6, 28)], r=0.9, mat="rust")
        chimney(m, 29, 13, 44, r=1.0, mat="steel", band="red")
    else:
        m.cyl(8, 8, 4.5, 0, 6, "steel_dark", n=14)
        m.lathe(8, 8, [(4.2, 6), (5.0, 16)], "rust", n=14)
        bk.scaffold(m, [(3, 3, 13, 13)], 16)
        m.box(1, 15, 17, 30, 0, 8, "brick")
        bk.scaffold(m, [(1, 17, 15, 30)], 8)
        for x, y in ((20, 4), (25, 4), (20, 10), (25, 10)):
            m.cyl(x, y, 2.3, 0, 12, "steel", n=12)
    k.parts += m.parts


def rolling_mill(k, kind, frame):
    if kind == "found":
        bk.foundations(k, [(1, 2, 31, 14)])
        return
    m = bk.Kit()
    if kind == "final":
        hall(m, 1, 31, 2, 14, 18, wall="brick", roof="cc", kind="gable", axis="x", ridge=5, band=None)
        m.roller_door("x", 31, 14, 8, w=5, h=10)
        m.box(31, 31.3, 6, 10, 2, 6, "glow")
        for x in (6, 16, 26):
            m.box(x - 1.2, x + 1.2, 5, 11, 23, 25, "glass_light")
        chimney(m, 4, 13, 40, r=0.9, mat="brick")
    else:
        m.box(1, 31, 2, 14, 0, 7, "brick")
        bk.scaffold(m, [(1, 2, 31, 14)], 7)
    k.parts += m.parts


def steel_ground(sprite, kind):
    d, g = bk.Kit(), bk.Kit()
    yard = {2124, 2135}
    if sprite in yard:
        # Ore and coke yard of the furnace block (S tile).
        rails(d, 15, 33, 27)
        if sprite == 2124:
            g.heap(21, 21, 4.5, 4.0, 8, "ore", seed=11)
            g.heap(27, 20.5, 3.0, 3.0, 5, "coal", seed=12)
            g.cbox(28, 27, 6, 1.7, 0.4, 3.5, "rust")
        else:
            g.heap(22, 21, 3.0, 3.0, 4, "ore", seed=13)
    return "industry/concrete" if sprite not in yard else "industry/yard", d, g


# --- farm --------------------------------------------------------------------------------------

def farmhouse(k, kind, frame):
    """Farmhouse with a garden (tile 0, 0) and a barn (tile 0, 1)."""
    m = bk.Kit()
    m.box(3, 11, 3, 12, 0, 11, "cream")
    m.windows(3, 11, 3, 12, 0, 11, floor=6, ww=1.3, wh=2.6, pitch=2.8, sill=1.4)
    m.gable(3, 11, 3, 12, 11, 17, "y", "cc", "cream", over=0.6)
    m.door("x", 11, 12, 7.5, w=1.6, h=4.8)
    chimney(m, 6, 5, 20, r=0.6, mat="brick", band="brick")
    m.tree(13, 3.5, 0.75)
    for y in bk.frange(2, 14, 3):
        m.bush(14.5, y, 0.7)
    m.box(17.5, 30, 3, 13, 0, 10, "cc")
    m.box(17.5, 30, 3, 13, 0, 1.2, "stone")
    m.gable(17.5, 30, 3, 13, 10, 17, "y", "roof_slate", "cc", over=0.6)
    m.box(30, 30.2, 5.5, 10.5, 0, 7.5, "wood_dark")
    m.box(30.1, 30.3, 5.6, 10.4, 3.6, 3.9, "white")
    m.cbox(24, 15.5, 3, 2, 0, 1.6, "hay")
    m.cbox(27, 15.5, 2, 2, 0, 1.6, "hay")
    k.parts += m.parts


def farm_barn(k, kind, frame):
    if kind == "found":
        return
    k.box(2, 14, 2, 10, 0, 9, "cc")
    k.gable(2, 14, 2, 10, 9, 15, "x", "roof_slate", "cc", over=0.6)
    k.box(14, 14.2, 3.5, 8.5, 0, 7, "wood_dark")
    k.cbox(8, 12.5, 4, 2.2, 0, 2.2, "hay")
    k.cbox(8, 12.5, 2.4, 2.0, 2.2, 4.0, "hay")
    tractor(k, 12, 13)


def tractor(k, x, y):
    k.cbox(x, y, 2.6, 1.4, 1.0, 2.6, "red")
    k.cbox(x - 0.5, y, 1.2, 1.2, 2.6, 4.4, "glass")
    for dx, r in ((-0.8, 1.0), (1.0, 0.6)):
        for dy in (-0.9, 0.9):
            k.rod((x + dx, y + dy - 0.25, r * 2.45), (x + dx, y + dy + 0.25, r * 2.45), r, "dark", n=8)


def farm_shed(k, kind, frame):
    if kind == "found":
        return
    for x in (2, 14):
        for y in bk.frange(2, 14, 4):
            k.cbox(x, y, 0.5, 0.5, 0, 9, "wood_dark")
    k.gable(2, 14, 2, 14, 9, 13, "x", "roof_metal", "wood", over=0.4, thick=0.3)
    for x in (4, 7, 10):
        k.rod((x, 4, 1.2 * 2.45), (x, 12, 1.2 * 2.45), 1.2, "hay", n=10)
    k.cbox(10, 8.5, 3, 4, 0, 3.5, "cc")


def farm_silos(k, kind, frame):
    if kind == "found":
        return
    for x, y in ((5, 5), (5, 11), (11, 8)):
        k.cyl(x, y, 2.4, 0, 26, "steel", n=14)
        k.lathe(x, y, [(2.4, 26), (1.0, 28.5), (0.01, 29)], "cc", n=14)
        for z in (8, 16):
            k.cyl(x, y, 2.45, z, z + 0.4, "steel_dark", n=14)
    k.rod((5, 5, 29), (11, 8, 29), 0.25, "steel_dark", n=4)
    k.rod((11, 8, 29), (5, 11, 29), 0.25, "steel_dark", n=4)
    k.cbox(13.5, 13.5, 2.2, 2.2, 0, 6, "steel_dark")


def farm_stable(k, kind, frame):
    if kind == "found":
        return
    k.box(1.5, 14.5, 1.5, 7.5, 0, 7, "white")
    k.windows(1.5, 14.5, 1.5, 7.5, 0, 7, floor=7, ww=1.0, wh=1.2, pitch=2.4, sill=4.5)
    k.gable(1.5, 14.5, 1.5, 7.5, 7, 11, "x", "cc", "white", over=0.5)
    k.fence([(1.5, 9), (1.5, 15), (14.5, 15), (14.5, 9)], h=2.5, mat="wood", post=2.5)
    for x, y in ((5, 11.5), (9.5, 12.5), (12, 10.5)):
        cow(k, x, y)


def cow(k, x, y):
    k.cbox(x, y, 2.2, 1.0, 1.4, 3.2, "white")
    k.cbox(x + 1.4, y, 0.8, 0.7, 2.4, 3.6, "dark")
    k.cbox(x - 0.3, y + 0.05, 0.9, 1.05, 2.0, 3.0, "dark")
    for dx in (-0.8, 0.8):
        for dy in (-0.35, 0.35):
            k.cbox(x + dx, y + dy, 0.3, 0.3, 0, 1.5, "white")


def farm_ground(sprite, kind):
    d, g = bk.Kit(), bk.Kit()
    if sprite in (2106, 2107):
        d.box(-1, 17, -1, 33, 0.02, 0.04, "lawn")
        d.box(1.5, 13, 1.5, 14, 0.04, 0.06, "path") if sprite == 2106 else None
        d.box(15, 33, 1.5, 15, 0.04, 0.06, "yard")
        if sprite == 2106:
            for x in (2.5, 4.5, 6.5):
                g.box(x, x + 1.2, 13, 15.5, 0, 0.6, "soil_dark")
        return "grass", d, g
    d.box(-1, 17, -1, 17, 0.02, 0.04, "yard")
    return "grass", d, g


# --- oil wells ---------------------------------------------------------------------------------

PUMP_ANGLES = {2174: -16, 2175: -9, 2176: -2, 2177: 5, 2178: 12, 2179: 19}


def pump_jack(k, kind, frame):
    """Pump jack along x; frame is the sprite (2174-2179) whose beam angle to draw."""
    ang = math.radians(PUMP_ANGLES.get(frame, -16))
    k.box(3, 13, 6, 10, 0, 1.0, "concrete")
    for y in (6.6, 9.4):
        k.rod((5, y, 1), (8, 8, 12), 0.25, "cc", n=4)
        k.rod((11, y, 1), (8, 8, 12), 0.25, "cc", n=4)
    piv = (8, 8, 12.5)
    L1, L2 = 5.5, 4.0
    head = (piv[0] - L1 * math.cos(ang), 8, piv[2] - L1 * math.sin(ang) * 2.45)
    tail = (piv[0] + L2 * math.cos(ang), 8, piv[2] + L2 * math.sin(ang) * 2.45)
    k.rod(head, tail, 0.45, "cc", n=4)
    k.box(head[0] - 0.9, head[0] + 0.3, 7.4, 8.6, head[2] - 3.5, head[2] + 1.5, "cc_light")
    k.rod((head[0] - 0.7, 8, head[2] - 3.5), (3.6, 8, 1.0), 0.06, "dark", n=3)
    k.cyl(3.6, 8, 0.4, 0, 2.5, "steel_dark", n=6)
    k.box(11, 13.5, 6.8, 9.2, 1, 5, "steel_dark")
    crank = (12.0, 8, 4.5)
    arm = (crank[0] + 1.6 * math.cos(-ang * 4), 8, crank[2] + 1.6 * math.sin(-ang * 4) * 2.45)
    for y in (6.4, 9.6):
        k.rod((crank[0], y, crank[2]), (arm[0], y, arm[2]), 0.45, "steel", n=4)
        k.rod((arm[0], y, arm[2]), (tail[0], y, tail[2]), 0.1, "steel_dark", n=3)
    k.cbox(arm[0], 6.2, 1.8, 0.4, arm[2] - 1.5, arm[2] + 1.5, "dark")
    k.cbox(arm[0], 9.8, 1.8, 0.4, arm[2] - 1.5, arm[2] + 1.5, "dark")


def oil_ground(sprite, kind):
    d, g = bk.Kit(), bk.Kit()
    if sprite == 2022:
        return "industry/yard", d, g
    d.box(2, 14, 4, 12, 0.02, 0.05, "gravel")
    g.cyl(12.5, 13.5, 1.6, 0, 5, "tank", n=10)
    g.cyl(12.5, 13.5, 1.65, 3, 4, "cc", n=10)
    pipe_run(g, [(12.5, 11.9, 1.0), (12.5, 8, 1.0), (4, 8, 1.0)], r=0.2)
    return "grass", d, g


# --- bank (2x1 along x) ------------------------------------------------------------------------

def bank(k, kind, frame):
    m = bk.Kit()
    x0, x1, y0, y1 = 2, 30, 2, 14
    m.box(x0 - 1, x1 + 1, y0 - 1, y1 + 1, 0, 1.4, "stone")
    m.box(x0 - 0.5, x1 + 0.5, y0 - 0.5, y1 + 0.5, 1.4, 2.4, "stone")
    m.box(x0, x1, y0, y1 - 3, 2.4, 20, "stone")
    m.windows(x0, x1, y0, y1 - 3, 2.4, 20, floor=8.5, ww=1.4, wh=4.0, pitch=3.4, sill=2.0, faces="x", frame="white")
    # Portico with columns towards SE (+y), pediment above.
    for x in bk.frange(x0 + 2, x1 - 2, 3.4):
        m.cyl(x, y1 - 1.2, 0.75, 2.4, 17, "white", n=10)
        m.cbox(x, y1 - 1.2, 1.9, 1.9, 2.4, 3.0, "white")
        m.cbox(x, y1 - 1.2, 1.9, 1.9, 16.4, 17, "white")
    m.box(x0, x1, y1 - 2.4, y1, 17, 19.5, "white")
    m.extrude([(y0, 19.5), (y1, 19.5), ((y0 + y1) / 2, 24)], "x", x0, x1, "roof_green")
    m.extrude([(y1 - 3, 19.5), (y1, 19.5), (y1, 19.8)], "x", x0, x1, "white")
    m.door("y", x1, y1 - 3, 16, w=3.0, h=8, mat="door")
    m.box(14, 18, y1 - 0.3, y1 + 0.1, 17.5, 19.0, "gold")
    k.parts += m.parts


def bank_ground(sprite, kind):
    d = bk.Kit()
    d.box(-1, 33, -1, 17, 0.02, 0.05, "paving")
    return "grass", d, bk.Kit()


UNITS = {
    "coal_head": dict(tiles={0: (0, 0), 1: (0, 0), 2: (0, 1)}, build=coal_head, ground=coal_ground),
    "coal_bunker": dict(tiles={3: (0, 0)}, build=coal_bunker, ground=coal_ground),
    "coal_heap": dict(tiles={4: (0, 0), 5: (0, 0), 6: (0, 0)}, build=None, ground=coal_ground),
    "cooling_tower": dict(tiles={7: (0, 0)}, build=cooling_tower, ground=no_ground),
    "turbine_hall": dict(tiles={8: (0, 0)}, build=turbine_hall, ground=no_ground),
    "boiler_house": dict(tiles={9: (0, 0)}, build=boiler_house, ground=no_ground),
    "transformer": dict(tiles={10: (0, 0)}, build=transformer, ground=no_ground),
    "saw_shed": dict(tiles={11: (0, 0)}, build=saw_shed, ground=no_ground),
    "saw_hall": dict(tiles={12: (0, 0)}, build=saw_hall, ground=no_ground),
    "saw_office": dict(tiles={13: (0, 0)}, build=saw_office, ground=no_ground),
    "saw_logs": dict(tiles={14: (0, 0)}, build=saw_logs, ground=no_ground),
    "saw_planks": dict(tiles={15: (0, 0)}, build=saw_planks, ground=no_ground),
    "forest": dict(tiles={16: (0, 0)}, build=forest, ground=forest_ground),
    "forest_felled": dict(tiles={17: (0, 0)}, build=forest_felled, ground=forest_ground),
    "ref_tank": dict(tiles={18: (0, 0)}, build=ref_tank, ground=no_ground),
    "ref_columns": dict(tiles={19: (0, 0)}, build=ref_columns, ground=no_ground),
    "ref_flare": dict(tiles={20: (0, 0)}, build=ref_flare, ground=no_ground),
    "ref_frame": dict(tiles={21: (0, 0)}, build=ref_frame, ground=no_ground),
    "ref_cracker": dict(tiles={22: (0, 0)}, build=ref_cracker, ground=no_ground),
    "ref_office": dict(tiles={23: (0, 0)}, build=ref_office, ground=no_ground),
    "factory": dict(tiles={39: (0, 0), 40: (0, 1), 41: (1, 0), 42: (1, 1)}, build=factory, ground=factory_ground),
    "printing": dict(tiles={43: (0, 0), 44: (0, 1), 45: (1, 0), 46: (1, 1)}, build=printing, ground=no_ground),
    "steel_block": dict(tiles={52: (0, 0), 53: (0, 1), 54: (1, 0), 55: (1, 1)}, build=steel_block, ground=steel_ground),
    "rolling_mill": dict(tiles={56: (0, 0), 57: (1, 0)}, build=rolling_mill, ground=steel_ground),
    "farmhouse": dict(tiles={33: (0, 0), 34: (0, 1)}, build=farmhouse, ground=farm_ground),
    "farm_barn": dict(tiles={35: (0, 0)}, build=farm_barn, ground=farm_ground),
    "farm_shed": dict(tiles={36: (0, 0)}, build=farm_shed, ground=farm_ground),
    "farm_silos": dict(tiles={37: (0, 0)}, build=farm_silos, ground=farm_ground),
    "farm_stable": dict(tiles={38: (0, 0)}, build=farm_stable, ground=farm_ground),
    "oil_well": dict(tiles={29: (0, 0), 30: (0, 0), 31: (0, 0), 32: (0, 0)}, build=pump_jack, ground=oil_ground),
    "bank": dict(tiles={58: (0, 0), 59: (1, 0)}, build=bank, ground=bank_ground),
}
