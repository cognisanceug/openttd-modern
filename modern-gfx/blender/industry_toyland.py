"""Low-poly models of the toyland industries, for render_industries.py.

Same conventions as industry_models.py. Toyland is drawn in bright candy and
toy colours, glossy shapes and toy bricks with studs, like the toyland trees
(render_trees.py: blue sticks, pink candyfloss).

Child sprites: four toyland draw procs (industry_cmd.cpp) add child sprites at
screen offsets from the parent sprite's top-left corner; the animated ones move
by the offsets (toy factory clay, robot and stamp; toffee quarry shovel; sugar
mine sieve; bubble). CHILDREN[sprite] = (parent sprite, reference offset, builder):
the child is modelled where it is at the reference offset, in the parent's
frame, and packed so that it lands there (tools/pack_industry.py). A step of
the offsets moves it the way the original does: (-2, +1) px is one unit
along x, (0, -1) px one unit up.

The plastic fountain's eight grounds (4721-4728, one per animation gfx) are
one render (ALIASES).
"""

import math
import random

import build_kit as bk

STAGE = {"found": 0, "partial": 1, "final": 2}


def candy_ground(sprite, kind):
    return "industry/candy", bk.Kit(), bk.Kit()


def no_ground(sprite, kind):
    return "industry/candy", bk.Kit(), bk.Kit()


def studs(k, x0, x1, y0, y1, z, mat, pitch=2.0):
    """Toy brick studs on a top face."""
    for x in bk.frange(x0 + pitch / 2, x1 - pitch / 2, pitch):
        for y in bk.frange(y0 + pitch / 2, y1 - pitch / 2, pitch):
            k.cyl(x, y, pitch * 0.28, z, z + 0.9, mat, n=8)


def brick_block(k, x0, x1, y0, y1, z0, z1, mat, course=3.0):
    """Stack of toy bricks: courses with a slight groove, studs on top."""
    z = z0
    while z < z1 - 0.01:
        top = min(z1, z + course)
        k.box(x0, x1, y0, y1, z, top - 0.15, mat)
        k.box(x0 + 0.15, x1 - 0.15, y0 + 0.15, y1 - 0.15, top - 0.15, top, mat)
        z = top
    studs(k, x0, x1, y0, y1, z1, mat)


def candy_cane(k, x, y, z0, z1, r=0.35):
    n = max(2, int((z1 - z0) / 1.6))
    for i in range(n):
        za, zb = bk.lerp(z0, z1, i / n), bk.lerp(z0, z1, (i + 1) / n)
        k.cyl(x, y, r, za, zb, "toy_red" if i % 2 else "toy_white", n=8)


# --- candyfloss forest -------------------------------------------------------------------------

FLOSS_SCALE = {2072: 0.4, 2073: 0.62, 2074: 0.86, 2075: 1.1}


def candyfloss(k, kind, frame):
    rng = random.Random(29)
    s = FLOSS_SCALE.get(frame, 1.1)
    for x, y in ((4, 4.5), (11.5, 3.5), (4.5, 12), (12, 11.5)):
        x, y = x + rng.uniform(-0.6, 0.6), y + rng.uniform(-0.6, 0.6)
        ss = s * rng.uniform(0.9, 1.05)
        top = 6 + 16 * ss
        k.cyl(x, y, 0.35, 0, top, "stick", n=8)
        if frame == 2076:
            continue
        r = 1.0 + 2.6 * ss
        k.blob(x, y, top + r * 1.6, r, r, r * 2.3, "floss", subdiv=2)


# --- candy factory (2x2, north tile empty) -------------------------------------------------------

def candy_factory(k, kind, frame):
    m = bk.Kit()
    if kind == "found":
        # Building material arrives gift-wrapped.
        for cx, cy, s in ((8, 24, 9), (24, 8, 9), (24, 24, 12)):
            m.cbox(cx, cy, s, s, 0, s * 1.4, "cc")
            m.cbox(cx, cy, s + 0.1, 1.2, 0, s * 1.4 + 0.05, "toy_white")
            m.cbox(cx, cy, 1.2, s + 0.1, 0, s * 1.4 + 0.05, "toy_white")
            m.blob(cx, cy, s * 1.4 + 0.9, 1.4, 1.4, 1.6, "toy_white", subdiv=1)
        k.parts += m.parts
        return
    # Peppermint tent on the S tile, striped annexes on the W and E tiles.
    cx, cy, r = 23.5, 23.5, 8.2
    wall = 14.0
    n = 16
    for i in range(n):
        a0, a1 = i * math.tau / n, (i + 1) * math.tau / n
        pts = [(cx, cy)] + [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in (a0, a1)]
        m.prism(pts, 0, wall, "cc" if i % 2 else "toy_white")
    # Swirled roof: wedges that twist as they rise.
    rings = [(r + 0.6, wall), (r * 0.75, wall + 6), (r * 0.42, wall + 11), (0.01, wall + 14)]
    for i in range(n):
        for j in range(len(rings) - 1):
            (ra, za), (rb, zb) = rings[j], rings[j + 1]
            tw = 0.35
            a0, a1 = i * math.tau / n + j * tw, (i + 1) * math.tau / n + j * tw
            b0, b1 = a0 + tw, a1 + tw
            v = [(cx + ra * math.cos(a0), cy + ra * math.sin(a0), za), (cx + ra * math.cos(a1), cy + ra * math.sin(a1), za),
                 (cx + rb * math.cos(b1), cy + rb * math.sin(b1), zb), (cx + rb * math.cos(b0), cy + rb * math.sin(b0), zb),
                 (cx, cy, za)]
            m._solid(v, [(0, 1, 2, 3), (0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)],
                     "toy_white" if i % 2 else "cc_light")
    m.blob(cx, cy, wall + 15, 1.0, 1.0, 1.4, "toy_red", subdiv=1)
    m.box(cx + r - 0.3, cx + r + 0.4, cy - 1.8, cy + 1.8, 0, 7, "toy_blue")
    candy_cane(m, cx + r + 0.6, cy - 2.6, 0, 11)
    candy_cane(m, cx + r + 0.6, cy + 2.6, 0, 11)
    for x0, x1, y0, y1 in ((2, 14, 18, 29), (18, 29, 2, 14)):
        along_y = x1 - x0 > y1 - y0
        steps = bk.frange(x0, x1, 2.4) if along_y else bk.frange(y0, y1, 2.4)
        for i, (a, b) in enumerate(zip(steps, steps[1:])):
            box = (a, b, y0, y1) if along_y else (x0, x1, a, b)
            m.box(*box, 0, 9, "cc" if i % 2 else "toy_white")
        m.gable(x0, x1, y0, y1, 9, 13, "x" if along_y else "y", "cc_light", "toy_white", over=0.5, thick=0.4)
        m.windows(x0, x1, y0, y1, 0, 9, floor=9, ww=1.2, wh=2.6, pitch=2.4, sill=3.4, glass="toy_cyan")
    if kind == "partial":
        m.parts = bk.clip_parts(m.parts, ztop=8, close_top=False)
        bk.scaffold(m, [(2, 18, 14, 29), (18, 2, 29, 14), (16, 16, 31, 31)], 8)
    k.parts += m.parts


# --- battery farm ------------------------------------------------------------------------------

BATTERY_H = {4686: 1.6, 4687: 3.4, 4688: 5.6, 4689: 7.8}


def battery_farm(k, kind, frame):
    k.box(1, 15, 1, 15, 0, 0.8, "toy_purple")
    for c in (5.5, 10.5):
        k.box(1.3, 14.7, c - 0.15, c + 0.15, 0.8, 1.0, "toy_white")
        k.box(c - 0.15, c + 0.15, 1.3, 14.7, 0.8, 1.0, "toy_white")
    h = BATTERY_H.get(frame)
    if h is None:
        return
    for x in (3.25, 8, 12.75):
        for y in (3.25, 8, 12.75):
            if (x, y) == (8, 8):
                continue
            k.cyl(x, y, 1.4, 0.8, 0.8 + h, "toy_yellow", n=12)
            k.cyl(x, y, 1.42, 0.8, 0.8 + h * 0.45, "dark", n=12)
            k.cyl(x, y, 0.5, 0.8 + h, 1.4 + h, "steel", n=8)


# --- cola wells --------------------------------------------------------------------------------

def ellipse(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(i * math.tau / n), cy + ry * math.sin(i * math.tau / n)) for i in range(n)]


def cola_wells(k, kind, frame):
    k.prism(ellipse(8, 8, 7.2, 6.2), 0, 0.4, "toy_green")
    k.prism(ellipse(8, 8, 6.2, 5.2), 0.4, 1.6, "toy_yellow")
    surface = {"found": ("soil_dark", 0.9), "partial": ("cola", 1.2), "final": ("cola", 1.62)}[kind]
    k.prism(ellipse(8, 8, 5.2, 4.2), 0.4, surface[1], surface[0])
    if kind == "found":
        return
    # Candy-cane pump arch over the well.
    pts = [(12.5, 8 + 4.2 * math.cos(i * math.pi / 10), 2 + 9 * math.sin(i * math.pi / 10)) for i in range(11)]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        k.rod(a, b, 0.4, "toy_red" if i % 2 else "toy_white", n=8)
    if kind == "final":
        k.cyl(12.5, 8, 0.6, 9.5, 11.5, "toy_red", n=8)
        for x, y in ((6, 6), (9, 10)):
            k.blob(x, y, 1.75, 0.6, 0.6, 0.5, "caramel", subdiv=1)


# --- toy shop (2x2 toy brick castle, north tile empty) -------------------------------------------

def flag(k, x, y, z, mat):
    k.cyl(x, y, 0.12, z, z + 7, "toy_white", n=6)
    k.box(x - 0.1, x + 0.1, y, y + 2.6, z + 4.6, z + 6.8, mat)


def toy_shop(k, kind, frame):
    m = bk.Kit()
    m.box(1, 15, 17, 31, 0, 0.8, "toy_blue")
    m.box(17, 31, 1, 15, 0, 0.8, "toy_blue")
    m.box(17, 31, 17, 31, 0, 0.8, "toy_blue")
    towers = [(4, 20, 4, "toy_blue", 30), (20, 4, 4, "toy_red", 30), (20, 20, 4, "toy_green", 42), (25, 26, 4, "toy_yellow", 28)]
    if kind == "found":
        studs(m, 17, 31, 17, 31, 0.8, "toy_blue")
        for x, y, s, mat, h in towers:
            brick_block(m, x, x + s, y, y + s, 0.8, 3.8, mat)
        k.parts += m.parts
        return
    # Curtain walls with crenellations between the towers.
    for x0, x1, y0, y1 in ((8, 16, 21, 23), (21, 23, 8, 16), (24, 30, 18, 20), (18, 20, 24, 30)):
        m.box(x0, x1, y0, y1, 0.8, 14, "toy_cyan")
        along = x1 - x0 > y1 - y0
        cells = bk.frange(x0 if along else y0, x1 if along else y1, 2.0)
        for i, (a, b) in enumerate(zip(cells, cells[1:])):
            if i % 2 == 0:
                m.box(a, b, y0, y1, 14, 16, "toy_cyan") if along else m.box(x0, x1, a, b, 14, 16, "toy_cyan")
    m.box(28.5, 29.0, 22, 26, 0.8, 7, "dark")  # gate
    for x, y, s, mat, h in towers:
        brick_block(m, x, x + s, y, y + s, 0.8, h, mat)
        if kind == "final":
            flag(m, x + s / 2, y + s / 2, h + 0.9, {"toy_blue": "toy_yellow", "toy_red": "toy_green"}.get(mat, "toy_red"))
    if kind == "partial":
        m.parts = bk.clip_parts(m.parts, ztop=12, close_top=False)
    k.parts += m.parts


# --- toy factory (4x2: hall along x on the y = 1 row, a giant hoop on (3, 0)) ---------------------

PRESS_X, PRESS_Y, TABLE_Z = 26.0, 29.0, 10.0


def toy_factory(k, kind, frame):
    m = bk.Kit()
    if frame == 4716:
        # Giant toy hoop leaning on a stand (3, 0).
        cx, cy, r = 56, 8, 5.5
        pts = [(cx, cy + r * math.cos(i * math.tau / 20), 1 + (r + r * math.sin(i * math.tau / 20)) * 2.45 * 0.8)
               for i in range(21)]
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            m.rod(a, b, 0.6, "toy_red" if (i // 2) % 2 else "toy_yellow", n=6)
        m.box(cx - 1.5, cx + 1.5, cy - 4, cy + 4, 0, 1.2, "toy_blue")
        k.parts += m.parts
        return
    # Tower with a hopper of clay balls (0, 1).
    m.box(3, 13, 19, 27, 0, 26, "brick")
    m.windows(3, 13, 19, 27, 0, 26, floor=7, ww=1.0, wh=2.6, pitch=2.4, sill=2.0)
    m.extrude([(18.5, 26), (27.5, 26), (25, 31), (21, 31)], "x", 2.5, 13.5, "toy_red")
    m.box(5, 11, 20.5, 25.5, 31, 33, "toy_red")
    for x, y in ((6.5, 22), (8.5, 23.5), (7, 24.5), (9.5, 21.8)):
        m.blob(x, y, 33.6, 1.0, 1.0, 1.8, "toffee", subdiv=1)
    # Press hall (1, 1): open towards the front, conveyor table in front of it.
    m.box(16, 32, 18, 26, 0, 20, "brick")
    m.windows(16, 32, 18, 26, 6, 20, floor=7, ww=1.0, wh=2.6, pitch=2.4, sill=2.0, faces="y")
    m.extrude([(17.5, 20), (26.5, 20), (24, 24), (20, 24)], "x", 15.5, 32.5, "toy_blue")
    m.box(4, 40, PRESS_Y - 1.2, PRESS_Y + 1.2, TABLE_Z - 0.8, TABLE_Z, "toy_white")
    m.box(4, 40, PRESS_Y - 1.25, PRESS_Y + 1.25, TABLE_Z - 1.6, TABLE_Z - 0.8, "toy_blue")
    for x in bk.frange(6, 38, 8):
        m.cbox(x, PRESS_Y, 0.6, 1.8, 0, TABLE_Z - 1.6, "steel_dark")
    # Blocks with blue mansard roofs (2, 1) and (3, 1), a flagpole on the last.
    for x0, x1, h in ((33, 47, 16), (49, 63, 22)):
        m.box(x0, x1, 18, 30, 0, h, "brick")
        m.windows(x0, x1, 18, 30, 0, h, floor=7, ww=1.0, wh=2.6, pitch=2.4, sill=2.0)
        m.extrude([(17.5, h), (30.5, h), (28, h + 5), (20, h + 5)], "x", x0 - 0.5, x1 + 0.5, "toy_blue")
        m.box(x0 + 1, x1 - 1, 20, 28, h + 5, h + 5.4, "toy_cyan")
    flag(m, 61, 20, 27.4, "toy_yellow")
    if kind == "partial":
        m.parts = bk.clip_parts(m.parts, ztop=10, close_top=False)
        bk.scaffold(m, [(3, 19, 13, 27), (16, 18, 32, 26), (33, 18, 47, 30), (49, 18, 63, 30)], 10)
    k.parts += m.parts


def press_holder(k, frame):
    for y in (PRESS_Y - 2.0, PRESS_Y + 2.0):
        k.box(PRESS_X - 0.5, PRESS_X + 0.5, y - 0.5, y + 0.5, 0, 52, "toy_red")
    k.box(PRESS_X - 1.2, PRESS_X + 1.2, PRESS_Y - 2.8, PRESS_Y + 2.8, 50, 53, "toy_red")
    k.cyl(PRESS_X, PRESS_Y, 1.3, 53, 57, "toy_yellow", n=12)


def press_stamp(k, frame):
    """The stamp at the top of its stroke (offset 0); 29 px lower it presses on the table."""
    bottom = TABLE_Z + 29 + 0.3
    k.box(PRESS_X - 1.5, PRESS_X + 1.5, PRESS_Y - 1.4, PRESS_Y + 1.4, bottom, bottom + 3, "steel")
    k.box(PRESS_X - 1.6, PRESS_X + 1.6, PRESS_Y - 1.5, PRESS_Y + 1.5, bottom + 2.2, bottom + 3.0, "toy_yellow")
    k.cyl(PRESS_X, PRESS_Y, 0.45, bottom + 3, 50, "steel", n=8)


def clay(k, frame):
    """Clay ball on the table at offset img 0, 18 units before the press."""
    k.blob(PRESS_X - 18, PRESS_Y, TABLE_Z + 1.9, 0.9, 0.9, 2.0, "toffee", subdiv=1)


def duck(k, frame):
    """Rubber duck where the stamp left it (robot offset 0), moving on along x."""
    x, y, z = PRESS_X, PRESS_Y, TABLE_Z
    k.blob(x, y, z + 1.8, 1.3, 1.0, 1.9, "toy_yellow", subdiv=2)
    k.blob(x - 0.7, y, z + 4.3, 0.75, 0.75, 1.7, "toy_yellow", subdiv=2)
    k.cbox(x - 1.55, y, 0.6, 0.5, z + 3.8, z + 4.4, "toy_orange")


# --- plastic fountain ---------------------------------------------------------------------------

def plastic_ground(sprite, kind):
    d, g = bk.Kit(), bk.Kit()
    d.box(2, 14, 2, 14, 0.02, 0.06, "toy_pink")
    for x0, x1, y0, y1 in ((1, 15, 1, 2), (1, 15, 14, 15), (1, 2, 1, 15), (14, 15, 1, 15)):
        g.box(x0, x1, y0, y1, 0, 1.6, "toy_blue")
    for x, y in ((1.5, 1.5), (14.5, 1.5), (1.5, 14.5), (14.5, 14.5)):
        g.cyl(x, y, 0.55, 0, 7, "toy_blue", n=8)
        g.cyl(x, y, 0.7, 7, 7.6, "dark", n=8)
    g.cyl(8, 8, 1.6, 0, 1.4, "toy_cyan", n=12)
    g.cyl(8, 8, 0.7, 1.4, 2.4, "dark", n=8)
    return "industry/candy", d, g


PLASTIC_COLOURS = ("toy_pink", "toy_cyan", "toy_yellow", "toy_green", "toy_orange")


def plastic_spurt(k, kind, frame):
    """Eight frames: a jet of plastic grows, bursts into blobs that fall back into the basin."""
    f = frame - 4729
    rng = random.Random(90)
    height = (9, 18, 27, 33, 33, 27, 18, 9)[f]
    spread = (0, 0, 0.6, 1.8, 3.4, 4.6, 5.4, 5.8)[f]
    if f < 4:
        k.cyl(8, 8, 1.0, 2.4, 2.4 + height, PLASTIC_COLOURS[f % 5], n=10, r_top=0.6)
    for i in range(10):
        a = i * math.tau / 10 + rng.uniform(-0.2, 0.2)
        r = spread * rng.uniform(0.7, 1.1)
        z = 2.4 + height * rng.uniform(0.75, 1.0)
        s = rng.uniform(0.7, 1.1)
        k.blob(8 + r * math.cos(a), 8 + r * math.sin(a), z, s, s, s * 2.2, PLASTIC_COLOURS[i % 5], subdiv=1)


# --- fizzy drink factory (2x2, north tile empty) -------------------------------------------------

CAN_X, CAN_Y, CAN_R, CAN_H = 24, 24, 6.0, 28


def fizzy_tap(m):
    """Tap from the can over the glass; its parts lie on both tiles (4741 and 4742)."""
    m.rod((CAN_X, CAN_Y - CAN_R + 0.5, 18), (CAN_X, 9, 18), 0.7, "steel", n=8)
    m.cyl(24, 9, 0.9, 14.5, 18, "steel", n=8)
    m.cyl(24, 9, 0.35, 19, 21.5, "steel_dark", n=6)
    m.cbox(24, 9, 2.6, 0.5, 21.3, 22, "toy_red")


def fizzy(k, kind, frame):
    m = bk.Kit()
    if frame == 4740:
        # Signpost on (0, 1), pointing to the can.
        m.cyl(8, 24, 0.35, 0, 14, "steel", n=6)
        m.extrude([(22, 10), (27, 10), (28.5, 12), (27, 14), (22, 14)], "y", 7.7, 8.3, "cc")
        m.box(7.6, 8.4, 23, 26, 11.4, 12.6, "toy_white")
        k.parts += m.parts
        return
    if frame in (4739, 4742):
        # Glass under the tap on (1, 0).
        gx, gy = 24, 9
        m.box(gx - 3.5, gx + 3.5, gy - 3.5, gy + 3.5, 0, 0.6, "toy_white")
        m.lathe(gx, gy, [(1.8, 0.6), (2.3, 10), (2.0, 10), (1.5, 1.2)], "bubble", n=16)
        if frame == 4742:
            m.cyl(gx, gy, 2.0, 1.2, 8.5, "cola", n=16)
            m.cyl(gx, gy, 2.05, 8.5, 9.6, "toy_white", n=16)
            m.cyl(gx, gy, 0.45, 9.6, 14.6, "cola", n=8)
            fizzy_tap(m)
        k.parts += m.parts
        return
    m.cyl(CAN_X, CAN_Y, CAN_R + 1.5, 0, 0.8, "toy_white", n=24)
    if frame == 4737:
        m.cyl(CAN_X, CAN_Y, CAN_R, 0.8, 2.0, "can", n=24)
        k.parts += m.parts
        return
    m.cyl(CAN_X, CAN_Y, CAN_R * 0.88, 0.8, 1.8, "can", n=24)
    m.cyl(CAN_X, CAN_Y, CAN_R, 1.8, CAN_H - 1.5, "cc", n=24)
    m.cyl(CAN_X, CAN_Y, CAN_R + 0.03, CAN_H * 0.45, CAN_H * 0.6, "toy_white", n=24)
    m.lathe(CAN_X, CAN_Y, [(CAN_R, CAN_H - 1.5), (CAN_R * 0.85, CAN_H), (CAN_R * 0.85, CAN_H + 0.4),
                            (CAN_R * 0.7, CAN_H + 0.4), (CAN_R * 0.7, CAN_H - 0.2)], "can", n=24)
    m.cyl(CAN_X, CAN_Y, CAN_R * 0.7, CAN_H - 0.3, CAN_H - 0.1, "can", n=24)
    m.cbox(CAN_X + 1.5, CAN_Y, 2.4, 1.2, CAN_H - 0.1, CAN_H + 0.2, "steel")
    if frame == 4741:
        fizzy_tap(m)
    k.parts += m.parts


# --- bubble generator (3x4, rows of three tiles along x) -----------------------------------------

def bubble_tank(k, kind, frame):
    k.box(3, 13, 4, 12, 0, 0.6, "toy_white")
    k.cyl(8, 8, 3.2, 0.6, 9, "cc", n=16)
    k.lathe(8, 8, [(3.2, 9), (1.4, 10.5), (0.01, 11)], "toy_white", n=16)
    k.rod((11, 8, 4), (16, 8, 4), 0.5, "steel", n=8)


def bubble_columns(k, kind, frame):
    k.box(2, 14, 3, 13, 0, 0.6, "toy_white")
    for x, y, h in ((5.5, 6, 26), (10.5, 10, 20)):
        for dx, dy in ((-1.3, -1.3), (1.3, -1.3), (-1.3, 1.3), (1.3, 1.3)):
            k.cyl(x + dx, y + dy, 0.45, 0.6, 3, "steel_dark", n=6)
        k.cyl(x, y, 2.0, 3, h, "cc", n=14)
        k.lathe(x, y, [(2.0, h), (2.4, h + 0.8), (2.4, h + 1.4), (1.6, h + 1.4)], "steel", n=14)
    k.rod((0, 8, 4), (16, 8, 4), 0.5, "steel", n=8)


HORN_X, HORN_Y, HORN_TOP = 6.0, 6.5, 32.0


def bubble_horn(k, kind, frame):
    bubble_columns(k, kind, frame)
    k.cyl(HORN_X, HORN_Y, 1.4, 0, 14, "bubble", n=12)
    k.cyl(HORN_X, HORN_Y, 1.2, 1, 9, "toy_cyan", n=12)
    k.cyl(HORN_X, HORN_Y, 1.5, 14, 15, "steel", n=12)
    k.lathe(HORN_X, HORN_Y, [(0.9, 15), (1.2, 24), (2.2, 29), (3.6, HORN_TOP), (3.3, HORN_TOP), (2.0, 29.5)],
            "copper", n=16)


def bubble(k, frame):
    """Soap bubble resting in the horn's mouth (offset 86); smaller offsets lift it out."""
    r = 2.8
    k.blob(HORN_X, HORN_Y, HORN_TOP + r * 2.45 * 0.9, r, r, r * 2.45, "bubble", subdiv=2)
    k.blob(HORN_X + 0.6, HORN_Y + 1.2, HORN_TOP + r * 2.45 * 1.3, 0.5, 0.5, 1.0, "toy_white", subdiv=1)


# --- toffee quarry (3x1 along x) --------------------------------------------------------------

def toffee_roller(k, kind, frame):
    """Caramel roller: a striped drum on a stand, and slabs of toffee (0, 0)."""
    for x in (3, 13):
        k.box(x - 0.6, x + 0.6, 4, 12, 0, 6, "steel_dark")
    k.rod((2.5, 8, 9), (13.5, 8, 9), 3.0, "toy_white", n=16)
    for x in (4.5, 8, 11.5):
        k.rod((x - 0.9, 8, 9), (x + 0.9, 8, 9), 3.05, "toy_red", n=16)
    for i, (x, y) in enumerate(((4, 13.5), (7.5, 13.8), (11, 13.4))):
        k.cbox(x, y, 2.8, 2.0, 0, 1.0 + 0.4 * i, "toffee")


def toffee_face(k, kind, frame):
    """Quarry face of layered toffee towards the north (1, 0)."""
    layers = (("toffee", 0, 6), ("caramel", 6, 10), ("toffee", 10, 16), ("caramel", 16, 19))
    for i, (mat, z0, z1) in enumerate(layers):
        x1 = 6.5 - i * 1.2
        k.box(0.5, x1, 0.5, 15.5, z0, z1, mat)
    k.box(0.5, 2.5, 0.5, 15.5, 19, 23, "toffee")


def toffee_hopper(k, frame):
    """Red tipper with toffee lumps (child at (6, 14))."""
    k.box(9.5, 14.5, 9, 14.5, 0, 3, "toy_red")
    k.box(9.8, 14.2, 9.3, 14.2, 3, 3.3, "dark")
    rng = random.Random(77)
    for _ in range(7):
        x, y = rng.uniform(10.5, 13.5), rng.uniform(10, 13.6)
        k.cbox(x, y, 1.2, 1.2, 3.0, 3.0 + rng.uniform(1.0, 2.2), rng.choice(("toffee", "caramel")))


def toffee_shovel(k, frame):
    """Shovel at the face at offset 0; each step takes it half a unit out and down."""
    x, y, z = 7.0, 7.0, 14.0
    k.rod((x - 4.5, y, z + 14), (x, y, z + 3), 0.3, "steel", n=6)
    k.box(x - 0.6, x + 1.8, y - 1.4, y + 1.4, z, z + 3.0, "toy_red")
    k.box(x + 1.6, x + 2.0, y - 1.4, y + 1.4, z - 0.6, z + 0.6, "steel_dark")


def toffee_heap(k, kind, frame):
    rng = random.Random(78)
    k.heap(8, 8, 6, 5.5, 8, "toffee", seed=79)
    for _ in range(9):
        x, y = rng.uniform(3, 13), rng.uniform(3, 13)
        k.cbox(x, y, 1.6, 1.6, 0, rng.uniform(1.2, 2.6), "caramel")


# --- sugar mine (4x2: heaps on the west 2x2, the sieve rig on the east tiles) --------------------

def sugar_ground(sprite, kind):
    d, g = bk.Kit(), bk.Kit()
    for x, y, rx, ry, h, s in ((10, 10, 7, 6, 9, 1), (22, 9, 6, 5, 7, 2), (9, 22, 5.5, 6, 8, 3), (23, 23, 7, 7, 11, 4)):
        g.heap(x, y, rx, ry, h, "sugar", seed=90 + s)
    return "industry/toyfloor", d, g


SIEVE_X, SIEVE_Y, SIEVE_Z = 56.0, 24.0, 22.0


def sugar_pole(k, kind, frame):
    """4772 pole (2, 1), 4774 pole with a beam (3, 0), 4773 the portal frame the sieve hangs from (3, 1)."""
    if frame == 4772:
        k.cyl(40, 24, 0.7, 0, 34, "cc", n=10)
        k.cyl(40, 24, 1.2, 0, 1.2, "steel", n=10)
        k.cyl(40, 24, 0.9, 34, 35.5, "steel", n=10)
        return
    if frame == 4774:
        k.cyl(56, 8, 0.7, 0, 34, "cc", n=10)
        k.cyl(56, 8, 1.2, 0, 1.2, "steel", n=10)
        k.box(55.5, 56.5, 8, 16, 33, 34.5, "cc")
        return
    for y in (19, 29):
        k.cyl(SIEVE_X, y, 0.7, 0, 34, "cc", n=10)
        k.cyl(SIEVE_X, y, 1.2, 0, 1.2, "steel", n=10)
    k.box(SIEVE_X - 0.6, SIEVE_X + 0.6, 16, 32, 33, 34.5, "cc")
    k.box(SIEVE_X - 0.6, SIEVE_X + 0.6, SIEVE_Y - 8, SIEVE_Y - 0.0, 33, 34.5, "cc")
    k.box(42, 56, 23.4, 24.6, 33, 34.5, "cc")


def sieve(k, frame):
    """Sieve pan on ropes; 4775 full of sugar, 4779 empty."""
    fill = 4779 - frame
    for dy in (-3.4, 3.4):
        k.rod((SIEVE_X, SIEVE_Y + dy, SIEVE_Z + 2), (SIEVE_X, SIEVE_Y, 33), 0.06, "dark", n=3)
    k.lathe(SIEVE_X, SIEVE_Y, [(4.2, SIEVE_Z), (4.5, SIEVE_Z + 2.4), (4.2, SIEVE_Z + 2.4), (3.9, SIEVE_Z + 0.5)],
            "steel", n=20)
    k.cyl(SIEVE_X, SIEVE_Y, 3.95, SIEVE_Z + 0.2, SIEVE_Z + 0.4, "steel_dark", n=20)
    if fill:
        k.heap(SIEVE_X, SIEVE_Y, 3.5, 3.5, 0.6 * fill, "sugar", seed=95)
        k.parts[-1] = (k.parts[-1][0], _lift(k.parts[-1][1], SIEVE_Z + 0.4))


def _lift(bm, z):
    for v in bm.verts:
        v.co.z += z
    return bm


PILE = {4780: (1.6, 1.2), 4781: (2.4, 2.0), 4782: (3.2, 2.8), 4783: (4.2, 3.8)}


def sugar_pile(k, frame):
    r, h = PILE[frame]
    k.heap(SIEVE_X, SIEVE_Y, r, r * 0.9, h, "sugar", seed=frame)


def sugar_dust(k, frame):
    rng = random.Random(frame)
    for _ in range(18):
        a, r = rng.uniform(0, math.tau), rng.uniform(0, 3.5)
        k.blob(SIEVE_X + r * math.cos(a), SIEVE_Y + r * math.sin(a), rng.uniform(4, SIEVE_Z - 0.5),
               0.18, 0.18, 0.45, "sugar", subdiv=0)


UNITS = {
    "candy_factory": dict(tiles={132: (0, 1), 133: (1, 0), 134: (1, 1)}, build=candy_factory, ground=no_ground),
    "battery_farm": dict(tiles={135: (0, 0), 136: (0, 0)}, build=battery_farm, ground=no_ground),
    "cola_wells": dict(tiles={137: (0, 0)}, build=cola_wells, ground=no_ground),
    "toy_shop": dict(tiles={139: (0, 1), 140: (1, 0), 141: (1, 1)}, build=toy_shop, ground=no_ground),
    "toy_factory": dict(tiles={142: (0, 1), 143: (1, 1), 144: (2, 1), 145: (3, 1), 146: (3, 0)}, build=toy_factory,
                        ground=no_ground),
    "plastic": dict(tiles={g: (0, 0) for g in range(148, 156)}, build=plastic_spurt, ground=plastic_ground),
    "fizzy": dict(tiles={157: (0, 1), 158: (1, 0), 159: (1, 1)}, build=fizzy, ground=no_ground),
    "bubble_tank": dict(tiles={160: (0, 0)}, build=bubble_tank, ground=no_ground),
    "bubble_columns": dict(tiles={161: (0, 0)}, build=bubble_columns, ground=no_ground),
    "bubble_horn": dict(tiles={162: (0, 0)}, build=bubble_horn, ground=no_ground),
    "toffee_roller": dict(tiles={164: (0, 0)}, build=toffee_roller, ground=no_ground),
    "toffee_face": dict(tiles={165: (0, 0)}, build=toffee_face, ground=no_ground),
    "toffee_heap": dict(tiles={166: (0, 0)}, build=toffee_heap, ground=no_ground),
    "sugar_heaps": dict(tiles={167: (0, 0), 168: (0, 1), 169: (1, 0), 170: (1, 1)}, build=None, ground=sugar_ground),
    "sugar_rig": dict(tiles={172: (2, 1), 173: (3, 0), 174: (3, 1)}, build=sugar_pole, ground=no_ground),
}

# child sprite: (parent sprite, reference offset (x, y) in 1x px, builder(k, sprite))
CHILDREN = {
    4717: (4713, (0, 42), press_holder),
    4718: (4713, (7, 0), press_stamp),
    4719: (4713, (50, 96), clay),
    4720: (4713, (16, 100), duck),
    4747: (4745, (5, 86), bubble),
    4766: (4764, (6, 14), toffee_hopper),
    4767: (4764, (22, 24), toffee_shovel),
    **{s: (4773, (8, 0), sieve) for s in range(4775, 4780)},
    **{s: (4773, xy, sugar_pile) for s, xy in zip(range(4780, 4784), ((22, 73), (17, 70), (14, 69), (10, 66)))},
    **{s: (4773, (8, 41), sugar_dust) for s in range(4784, 4790)},
}

ALIASES = {s: 4721 for s in range(4722, 4729)}

CLIMATE_UNITS = {
    "toyland": {
        "candyfloss": dict(tiles={129: (0, 0), 130: (0, 0)}, build=candyfloss, ground=candy_ground),
    },
}
