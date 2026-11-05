"""Low-poly models of the sub-arctic and sub-tropical industries, for render_industries.py.

Same conventions as industry_models.py (UNITS, unit coordinates, kinds). Where
a gfx's sprites differ per stage beyond foundations / scaffolding (paper mill,
food processing plant), the builder picks by sprite number (frame).
The gold and diamond mines are open pits drawn like the iron ore mine, see pit_mines.py;
here is only the gold mine's head frame (2263-2265).

CLIMATE_UNITS holds the variants of sprites the climates share with temperate
(table/landscape_sprite.h): the snowy forest (2072-2077) in sub-arctic and the
oil wells' sandy ground (2173) in sub-tropical. They render to their own folders
and are packed inside if (climate == ...) blocks.
"""

import math
import random

import build_kit as bk
import industry_models as im
from industry_models import chimney, hall, pallets, pipe_run, truck

STAGE = {"found": 0, "partial": 1, "final": 2}


def concrete_ground(sprite, kind):
    return "industry/concrete", bk.Kit(), bk.Kit()


# --- copper ore mine (sub-tropical) ------------------------------------------------------------

def copper_head(k, kind, frame):
    """Winding house with a head frame and its big sheave; box x 3-11, y 2-10."""
    def model(k):
        hall(k, 3.5, 11, 5, 10, 12, wall="brick", roof="roof_slate", axis="x", ridge=3)
        k.door("y", 11, 10, 9, w=2, h=5)
        for x, y in ((4, 2.5), (10, 2.5), (4, 7.5), (10, 7.5)):
            k.rod((x, y, 0), (bk.lerp(x, 7, 0.55), bk.lerp(y, 5, 0.55), 38), 0.35, "steel_dark", n=4)
        for z in (14, 26):
            t = z / 38 * 0.55
            c = [(bk.lerp(x, 7, t), bk.lerp(y, 5, t), z) for x, y in ((4, 2.5), (10, 2.5), (10, 7.5), (4, 7.5))]
            for a, b in zip(c, c[1:] + c[:1]):
                k.rod(a, b, 0.16, "steel_dark", n=4)
        k.cbox(7, 5, 3.5, 3.5, 37, 38.5, "steel")
        angle = {2029: 1, 2030: 2}.get(frame, 0) * math.tau / 18
        im.sheave(k, 7, 5, 43, 3.6, angle, mat="copper")
        k.rod((7, 8.6, 43), (7, 12.5, 6), 0.2, "steel_dark", n=4)
    bk.staged(k, model, STAGE[kind], [(3.5, 2.5, 11, 10)])


def copper_mill(k, kind, frame):
    """Ore dressing house with three chimneys; box x 3-13, y 2-9."""
    def model(k):
        hall(k, 3, 13, 2.5, 9, 16, wall="brick", roof="roof_slate", axis="x", ridge=4)
        k.box(3, 7, 2.5, 9, 0, 22, "brick")
        k.windows(3, 7, 2.5, 9, 0, 22, floor=7, ww=1.0, wh=3.2, pitch=2.2, sill=2.0, frame="cream")
        k.flat_roof(3, 7, 2.5, 9, 22, "brick", parapet=0.5)
        for x in (4.2, 5.8):
            chimney(k, x, 4.0, 38, r=0.7, band="brick_dark")
        chimney(k, 5.0, 7.5, 34, r=0.7, band="brick_dark")
        k.roller_door("y", 13, 9, 10, w=3, h=6)
    bk.staged(k, model, STAGE[kind], [(3, 2.5, 13, 9)])


def copper_shed(k, kind, frame):
    def model(k):
        hall(k, 4, 11, 4.5, 12, 10, wall="brick", roof="roof_slate", axis="y", ridge=4, windows=False)
        k.roller_door("x", 11, 12, 8.25, w=3.5, h=6)
        k.heap(12.8, 13.5, 2.0, 1.8, 3.5, "copper_ore", seed=31)
    bk.staged(k, model, STAGE[kind], [(4, 4.5, 11, 12)])


def copper_store(k, kind, frame):
    """Two long ore sheds and a heap of copper ore between them; box x 2-13, y 1-14."""
    def model(k):
        for y0 in (1.5, 9.0):
            hall(k, 2, 13, y0, y0 + 4.5, 6, wall="brick", roof="roof_slate", axis="x", ridge=2.5, windows=False)
            k.door("x", 13, y0 + 4.5, y0 + 2.25, w=2, h=4.5)
        k.heap(7.5, 7.2, 4.5, 1.4, 3.0, "copper_ore", seed=32)
    bk.staged(k, model, STAGE[kind], [(2, 1.5, 13, 13.5)])


# --- food processing plant (sub-arctic and sub-tropical, industry colour) ----------------------

def food_hall(k, kind, frame):
    def model(k):
        hall(k, 1, 15, 2, 14, 13, wall="brick", roof="cc", axis="x", ridge=5, band="white_band")
        k.roller_door("x", 15, 14, 5, w=4, h=7)
        k.roller_door("x", 15, 14, 11, w=4, h=7)
    bk.staged(k, model, STAGE[kind], [(1, 2, 15, 14)])


def food_boiler(k, kind, frame):
    def model(k):
        k.box(2, 9, 2, 14, 0, 18, "brick")
        k.windows(2, 9, 2, 14, 0, 18, floor=6, ww=1.1, wh=2.8, pitch=2.4, sill=1.8, frame="cream")
        k.box(1.8, 9.2, 1.8, 14.2, 15.5, 16.5, "cc")
        k.flat_roof(2, 9, 2, 14, 18, "brick", parapet=0.6)
        k.box(9, 14.5, 6, 14, 0, 9, "brick")
        k.flat_roof(9, 14.5, 6, 14, 9, "brick", parapet=0.5)
        k.door("x", 14.5, 14, 10, w=2, h=5, mat="cc")
        chimney(k, 12, 3.5, 40, r=1.0)
    bk.staged(k, model, STAGE[kind], [(2, 2, 14.5, 14)])


def food_silo(k, kind, frame):
    if kind == "found":
        k.cyl(8, 8, 5.4, 0, 1.0, "concrete", n=20)
        return
    h = 26 if kind == "final" else 12
    k.cyl(8, 8, 5.2, 0, 1.0, "concrete", n=20)
    k.cyl(8, 8, 4.8, 1, 1 + h, "tank", n=20)
    for z in (0.25, 0.65):
        k.cyl(8, 8, 4.85, 1 + h * z, 1 + h * z + 3, "cc", n=20)
    if kind == "final":
        k.lathe(8, 8, [(4.85, 27), (2.0, 29.5), (0.01, 30)], "steel", n=20)
        k.rod((11.5, 11.5, 0), (11.5, 11.5, 27), 0.18, "steel_dark", n=4)
        pipe_run(k, [(12.8, 8, 1), (12.8, 8, 22), (11.6, 8, 24)], r=0.3)
    else:
        bk.scaffold(k, [(3.2, 3.2, 12.8, 12.8)], h)


def food_yard(k, kind, frame):
    """Walled delivery yard: slab, then the walls, then crates and a lorry."""
    k.box(1, 15, 1, 15, 0, 0.5, "concrete")
    if kind == "found":
        return
    for x0, x1, y0, y1 in ((1, 15, 1, 2), (1, 2, 1, 15), (1, 10, 14, 15), (14, 15, 1, 10)):
        k.box(x0, x1, y0, y1, 0.5, 3.0, "brick")
        k.box(x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, 3.0, 3.4, "cc")
    if kind == "final":
        pallets(k, 4, 4, n=4, mat="wood", load="hay", seed=41)
        pallets(k, 9, 4, n=2, mat="wood", load="cc_flat", seed=42)
        truck(k, 8, 10, "x", body="cc")


# --- paper mill (sub-arctic) -------------------------------------------------------------------

def paper_main(k, kind, frame):
    def model(k):
        k.box(1, 15, 1, 9, 0, 17, "brick")
        k.windows(1, 15, 1, 9, 0, 17, floor=8, ww=1.2, wh=3.4, pitch=2.6, sill=2.0, frame="cream")
        k.flat_roof(1, 15, 1, 9, 17, "brick", parapet=0.6)
        hall(k, 1, 15, 9, 15, 10, wall="brick", roof="roof_slate", axis="x", ridge=4)
        k.roller_door("y", 15, 15, 12, w=3.5, h=7)
        k.box(4, 8, 3, 6, 17.2, 19.5, "steel")
    bk.staged(k, model, STAGE[kind], [(1, 1, 15, 15)])


def paper_shed(k, kind, frame):
    """Open log shed on posts (only at stage 3)."""
    for x in (2, 14):
        for y in bk.frange(2, 14, 4):
            k.cbox(x, y, 0.5, 0.5, 0, 10, "steel_dark")
    k.gable(2, 14, 2, 14, 10, 14, "y", "roof_slate", "steel_dark", over=0.5, thick=0.3)
    im.log_stack(k, 3.5, 12.5, 3, 13, rows=3, r=0.7, axis="y")


def paper_house(k, kind, frame, rolls=False):
    def model(k):
        hall(k, 2, 10, 2, 14, 20, wall="brick", roof="roof_slate", axis="y", ridge=5)
        hall(k, 10, 15, 6, 14, 11, wall="brick", roof="roof_slate", axis="x", ridge=3)
        k.door("x", 15, 14, 10, w=2, h=5)
        if rolls:
            k.box(10.5, 14.5, 2, 5.6, 0, 0.4, "wood")
            for x, y in ((11.5, 3), (13.5, 3), (12.5, 4.6)):
                k.rod((x, y, 1.2 * 2.45 * 0.5 + 0.4), (x, y + 0.01, 1.2 * 2.45 * 0.5 + 0.4), 1.0, "paper", n=10)
                k.cyl(x, y, 0.95, 0.4, 3.6, "paper", n=10)
    bk.staged(k, model, STAGE[kind], [(2, 2, 15, 14)])


def paper_stacks(k, kind, frame):
    """Two chimneys of the boiler house and a walled yard (2207 short, 2208 tall, 2209 with paper rolls)."""
    tall = frame != 2207
    k.box(1, 15, 1, 15, 0, 0.4, "concrete")
    for x0, x1, y0, y1 in ((8, 15, 14, 15), (14, 15, 6, 15), (8, 9, 6, 15)):
        k.box(x0, x1, y0, y1, 0.4, 3.0, "brick")
    for x, y, top in ((4, 4, 62), (4, 10, 46)):
        top = top if tall else 16
        chimney(k, x, y, top, r=1.6 if top > 50 else 1.3, band="brick_dark")
    if frame == 2209:
        for x, y in ((10.5, 8), (12.5, 8), (10.5, 10.5), (12.5, 10.5), (11.5, 12.8)):
            k.cyl(x, y, 1.0, 0.4, 3.8, "paper", n=10)


def paper_hut(k, kind, frame):
    """2210 bare yard, 2211 hut walls, 2212 the hut, 2213 the hut with logs."""
    k.box(1, 15, 1, 15, 0, 0.3, "concrete")
    if frame == 2210:
        return
    k.box(2, 8, 2, 8, 0, 7, "brick")
    if frame == 2211:
        return
    k.gable(2, 8, 2, 8, 7, 10, "x", "roof_slate", "brick", over=0.4)
    k.door("x", 8, 8, 5, w=1.6, h=4.5)
    if frame == 2213:
        im.log_stack(k, 9, 15, 2, 14, rows=4, r=0.75, axis="x")


# --- bank (sub-arctic and sub-tropical, 2x1 along x) ---------------------------------------------

def bank2(k, kind, frame):
    m = bk.Kit()
    x0, x1, y0, y1 = 2, 30, 2, 13
    m.box(x0, x1, y0, y1, 0, 1.2, "plinth")
    m.box(x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, 1.2, 22, "stone")
    m.windows(x0, x1, y0, y1, 9, 22, floor=6.5, ww=1.2, wh=3.4, pitch=2.8, sill=1.6, frame="white")
    # Arcade on the ground floor towards both visible sides.
    for x in bk.frange(x0 + 1.5, x1 - 1.5, 3.5):
        m.cbox(x, y1 + 0.4, 1.0, 1.0, 1.2, 8.6, "white")
    for y in bk.frange(y0 + 1.5, y1 - 1.5, 3.2):
        m.cbox(x1 + 0.4, y, 1.0, 1.0, 1.2, 8.6, "white")
    m.box(x0, x1 + 0.9, y0, y1 + 0.9, 8.6, 9.6, "white")
    m.box(x0 + 1, x1 - 1, y1 - 0.4, y1 - 0.2, 1.2, 7, "glass")
    m.box(x1 - 0.4, x1 - 0.2, y0 + 1, y1 - 1, 1.2, 7, "glass")
    m.box(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, 22, 23.2, "white")
    m.flat_roof(x0, x1, y0, y1, 23.2, "white", parapet=0.6)
    m.box(12, 20, y1 - 0.2, y1 + 0.2, 18.5, 20.5, "gold")
    m.box(6, 10, 5, 9, 23.4, 26, "steel")
    k.parts += m.parts


def bank2_ground(sprite, kind):
    d, g = bk.Kit(), bk.Kit()
    off = 16 if sprite == 2185 else 0
    d.box(-1 + off, 17 + off, -1, 17, 0.02, 0.05, "paving")
    if sprite in (2184, 2185):
        g.box(off + 11, off + 15, 13.5, 15.5, 0, 1.2, "plinth")
        g.box(off + 11.3, off + 14.7, 13.8, 15.2, 1.2, 1.4, "soil_dark")
        for x in (off + 12, off + 14):
            g.bush(x, 14.5, 0.9)
    return "grass", d, g


# --- plantations (sub-tropical) ---------------------------------------------------------------

GRID = [(x, y) for x in (3, 8, 13) for y in (3, 8, 13)]


def fruit_trees(k, kind, frame):
    rng = random.Random(51)
    for x, y in GRID:
        x, y = x + rng.uniform(-0.6, 0.6), y + rng.uniform(-0.6, 0.6)
        s = rng.uniform(0.85, 1.05)
        k.cyl(x, y, 0.3, 0, 5 * s, "trunk", n=6, r_top=0.22)
        k.blob(x, y, 9 * s, 2.3 * s, 2.3 * s, 4.8 * s, "leaf", subdiv=1)
        for i in range(5):
            a = rng.uniform(0, math.tau)
            k.blob(x + 2.1 * s * math.cos(a), y + 2.1 * s * math.sin(a), (8 + rng.uniform(-1.5, 2.5)) * s,
                   0.42, 0.42, 1.0, "fruit", subdiv=1)


def rubber_trees(k, kind, frame):
    rng = random.Random(52)
    for x, y in GRID:
        x, y = x + rng.uniform(-0.5, 0.5), y + rng.uniform(-0.5, 0.5)
        s = rng.uniform(0.9, 1.1)
        k.cyl(x, y, 0.35, 0, 13 * s, "trunk", n=6, r_top=0.25)
        k.cyl(x + 0.36, y, 0.25, 3.0, 4.2, "latex", n=6)  # tapping cup
        k.blob(x, y, 19 * s, 2.5 * s, 2.5 * s, 6.5 * s, "leaf_dark", subdiv=1)
        k.blob(x + 0.8, y - 0.6, 16 * s, 1.8 * s, 1.8 * s, 4.5 * s, "leaf_dark", subdiv=1)


def plantation_ground(sprite, kind):
    return "industry/plantation", bk.Kit(), bk.Kit()


# --- water supply and water tower (sub-tropical, industry colour) --------------------------------

def water_tower(k, kind, frame):
    cx, cy, r = 8, 8, 5.6
    legs = [(cx + 4.6 * math.cos(a), cy + 4.6 * math.sin(a)) for a in (0.4, 2.0, 3.6, 5.2)]
    k.cyl(cx, cy, 6.5, 0, 0.6, "concrete", n=20)
    top = {"found": 6, "partial": 20, "final": 20}[kind]
    for x, y in legs:
        k.cyl(x, y, 0.45, 0.6, top, "steel_dark", n=6)
    if kind == "found":
        return
    for a, b in zip(legs, legs[1:] + legs[:1]):
        k.rod((a[0], a[1], 4), (b[0], b[1], 14), 0.1, "steel", n=3)
    k.cyl(cx, cy, r, 20, 21, "steel_dark", n=24)
    h = 34 if kind == "final" else 26
    k.cyl(cx, cy, r, 21, h, "tank", n=24)
    for z in bk.frange(23, h - 3, 5):
        k.cyl(cx, cy, r + 0.05, z, z + 2, "cc", n=24)
    k.lathe(cx, cy, [(r - 0.5, h - 0.4), (r - 0.5, h - 0.8)], "steel", n=24)
    k.cyl(cx, cy, r - 0.5, h - 1.2, h - 0.9, "water", n=24)
    k.cyl(cx, cy, r + 0.2, h - 0.3, h + 0.3, "steel", n=24)
    k.lathe(cx, cy, [(r + 0.2, h + 0.3), (r - 0.4, h + 0.3)], "steel", n=24)
    if kind == "partial":
        bk.scaffold(k, [(cx - r, cy - r, cx + r, cy + r)], h - 4)


def water_pumps(k, kind, frame):
    """Bore-hole pumps: blue (industry colour) motors over the wells, pipes to the treatment tile."""
    k.box(1, 15, 2, 14, 0, 0.5, "concrete")
    cols = (3.5, 8, 12.5)
    for i, x in enumerate(cols):
        k.cyl(x, 5, 0.5, 0.5, 9 if kind != "found" else 4, "pipe", n=8)
    if kind == "found":
        return
    for x in cols:
        k.cbox(x, 5, 2.4, 2.4, 9, 12, "cc")
        k.cbox(x, 5, 1.2, 1.2, 12, 13, "steel_dark")
        if kind == "final":
            k.cyl(x, 11, 1.7, 0.5, 8, "cc", n=12)
            k.lathe(x, 11, [(1.7, 8), (0.8, 9), (0.01, 9.3)], "cc_light", n=12)
            pipe_run(k, [(x, 5, 3), (x, 9.4, 3)], r=0.35)
    if kind == "final":
        pipe_run(k, [(1, 13.5, 2), (15, 13.5, 2)], r=0.45)


def water_treat(k, kind, frame):
    """Settling tanks, a pipe rack and a filter frame."""
    k.box(1, 15, 1, 15, 0, 0.5, "concrete")
    for x, y in ((3.5, 4), (3.5, 10)):
        k.cyl(x, y, 2.2, 0.5, 7 if kind != "found" else 2, "tank", n=14)
        if kind != "found":
            k.lathe(x, y, [(2.2, 7), (1.0, 8), (0.01, 8.3)], "tank", n=14)
    if kind == "found":
        return
    for y in (6.5, 8.5, 10.5, 12.5):
        pipe_run(k, [(6, y, 2.2), (15, y, 2.2)], r=0.4)
    for x in (7, 11, 14.5):
        k.box(x - 0.15, x + 0.15, 5.5, 13.5, 0.5, 2.0, "steel")
    if kind == "final":
        for x in (9, 13):
            for y in (2.5, 4.5):
                k.rod((x, y, 0.5), (x, y, 14), 0.25, "pipe", n=6)
            k.rod((x, 2.5, 14), (x, 4.5, 14), 0.25, "pipe", n=6)
        k.box(9.5, 12.5, 2, 5, 0.5, 9, "steel_dark")
        k.box(9.4, 12.6, 1.9, 5.1, 6, 7.5, "cc")
        k.cbox(11, 3.5, 2.4, 2.4, 9, 11, "cc_light")
        pipe_run(k, [(5.7, 4, 5), (9.5, 4, 5)], r=0.35)


# --- lumber mill (sub-tropical rainforest, 2x2) -----------------------------------------------

LUMBER_FOOT = [(2, 18, 15, 30), (18, 18, 28, 29)]


def lumber_mill(k, kind, frame):
    m = bk.Kit()
    m.box(0, 32, 0, 32, 0, 0.12, "mud")
    if kind == "found":
        for f in LUMBER_FOOT:
            bk.foundations(m, [f])
        for x, y in ((5, 5), (11, 9), (22, 4), (27, 10), (8, 12)):
            m.cyl(x, y, 0.6, 0, 1.2, "log", n=7)
            m.cyl(x, y, 0.55, 1.2, 1.25, "log_end", n=7)
        k.parts += m.parts
        return
    # Saw hall (W tile) and drying shed (S tile).
    hall(m, 2, 15, 18, 30, 12, wall="white", roof="roof_red", axis="y", ridge=5)
    m.roller_door("x", 15, 30, 24, w=4, h=7)
    for x in (18, 28):
        for y in bk.frange(18, 29, 5.5):
            m.cbox(x, y, 0.5, 0.5, 0, 9, "wood_dark")
    m.gable(18, 28, 18, 29, 9, 13, "x", "roof_red", "wood", over=0.5, thick=0.3)
    im.plank_stack(m, 19.5, 26.5, 20, 24, 5)
    im.plank_stack(m, 19.5, 26.5, 25, 28, 3)
    # Log yard (E tile) and rainforest trees on the N tile.
    im.log_stack(m, 18, 30, 3, 9, rows=3, r=0.75, axis="x")
    im.log_stack(m, 18, 27, 10.5, 14, rows=2, r=0.7, axis="x")
    m.cbox(29, 12.5, 2.0, 3.0, 0, 3.4, "yellow")
    m.cbox(29, 12.5, 1.6, 1.6, 3.4, 5.6, "glass")
    rng = random.Random(61)
    for x, y in ((4, 4), (10, 3), (6, 10), (12, 11)):
        s = rng.uniform(0.95, 1.15)
        m.cyl(x, y, 0.35, 0, 12 * s, "trunk", n=6, r_top=0.25)
        m.blob(x, y, 17 * s, 3.0 * s, 3.0 * s, 6.0 * s, "leaf_dark", subdiv=1)
        m.blob(x - 0.8, y + 0.9, 14 * s, 2.2 * s, 2.2 * s, 4.5 * s, "leaf", subdiv=1)
    for x, y in ((3, 13.5), (13.5, 6)):
        m.cyl(x, y, 0.55, 0, 1.0, "log", n=7)
    if kind == "partial":
        m.parts = bk.clip_parts(m.parts, ztop=7, close_top=False)
        bk.scaffold(m, [LUMBER_FOOT[0]], 7)
    k.parts += m.parts


# --- gold mine head frame (sub-arctic) ---------------------------------------------------------

def gold_head(k, kind, frame):
    """Steel head frame over the shaft on gfx 79; 2263-2265 turn the sheave."""
    top = 30.0
    for x, y in ((4, 4), (10, 4), (4, 10), (10, 10)):
        k.rod((x, y, 0), (bk.lerp(x, 7, 0.35), bk.lerp(y, 7, 0.35), top), 0.32, "steel_dark", n=4)
    for x in (5.5, 8.5):
        k.rod((x, 14.5, 0), (x, 8.5, top - 2), 0.35, "steel_dark", n=4)
    k.cbox(7, 7, 4.5, 4.5, top - 1, top, "steel")
    angle = {2264: 1, 2265: 2}.get(frame, 0) * math.tau / 18
    im.sheave(k, 7, 7, top + 3, 2.6, angle, mat="red")
    k.cbox(7, 7, 4.0, 4.0, 0, 3, "concrete")
    k.box(11.5, 15, 1, 6, 0, 7, "wood")
    k.gable(11.5, 15, 1, 6, 7, 9, "y", "roof_slate", "wood", over=0.3)


# --- sub-arctic forest with snow ------------------------------------------------------------

def snowy_forest(k, kind, frame):
    rng = random.Random(16)
    s = im.FOREST_SCALE.get(frame, 1.15)
    for x in (2.7, 8.0, 13.3):
        for y in (2.7, 8.0, 13.3):
            jx, jy = rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8)
            ss = s * rng.uniform(0.85, 1.05)
            k.cyl(x + jx, y + jy, 0.3 * ss + 0.1, 0, 5 * ss, "trunk", n=5)
            for r, z0, z1 in ((2.4, 3, 14), (1.9, 9, 20), (1.3, 15, 27)):
                rot = rng.uniform(0, 1)
                k.cyl(x + jx, y + jy, r * ss, z0 * ss, z1 * ss, "conifer", n=7, r_top=0, rot=rot)
                # Snow caps the upper part of every tier.
                t = 0.3
                zc = z0 + (z1 - z0) * t
                k.cyl(x + jx, y + jy, r * ss * (1 - t) + 0.18, zc * ss, z1 * ss + 0.3, "snow", n=7, r_top=0, rot=rot)


def snowy_felled(k, kind, frame):
    im.forest_felled(k, kind, frame)
    for x, y in ((3, 11), (7, 13), (12, 10.5), (13, 14), (9.5, 10)):
        k.cyl(x, y, 0.5, 1.05, 1.35, "snow", n=7)
    k.box(2.2, 13.8, 2.2, 7.8, 5.6, 5.9, "snow")


def snowy_ground(sprite, kind):
    return "snow4", bk.Kit(), bk.Kit()


def desert_oil_ground(sprite, kind):
    _, d, g = im.oil_ground(sprite, kind)
    return "desert4", d, g


UNITS = {
    "copper_head": dict(tiles={47: (0, 0), 48: (0, 0)}, build=copper_head, ground=im.no_ground),
    "copper_mill": dict(tiles={49: (0, 0)}, build=copper_mill, ground=im.no_ground),
    "copper_shed": dict(tiles={50: (0, 0)}, build=copper_shed, ground=im.no_ground),
    "copper_store": dict(tiles={51: (0, 0)}, build=copper_store, ground=im.no_ground),
    "food_hall": dict(tiles={60: (0, 0)}, build=food_hall, ground=im.no_ground),
    "food_boiler": dict(tiles={61: (0, 0)}, build=food_boiler, ground=im.no_ground),
    "food_silo": dict(tiles={62: (0, 0)}, build=food_silo, ground=im.no_ground),
    "food_yard": dict(tiles={63: (0, 0)}, build=food_yard, ground=im.no_ground),
    "paper_main": dict(tiles={64: (0, 0)}, build=paper_main, ground=im.no_ground),
    "paper_shed": dict(tiles={65: (0, 0)}, build=paper_shed, ground=im.no_ground),
    "paper_house": dict(tiles={66: (0, 0)}, build=paper_house, ground=im.no_ground),
    "paper_rolls": dict(tiles={67: (0, 0)}, build=lambda k, kind, f: paper_house(k, kind, f, rolls=True),
                        ground=im.no_ground),
    "paper_stacks": dict(tiles={68: (0, 0), 69: (0, 0)}, build=paper_stacks, ground=im.no_ground),
    "paper_hut": dict(tiles={70: (0, 0), 71: (0, 0)}, build=paper_hut, ground=im.no_ground),
    "gold_head": dict(tiles={79: (0, 0), 88: (0, 0)}, build=gold_head, ground=None),
    "bank2": dict(tiles={89: (0, 0), 90: (1, 0)}, build=bank2, ground=bank2_ground),
    "fruit": dict(tiles={116: (0, 0)}, build=fruit_trees, ground=plantation_ground),
    "rubber": dict(tiles={117: (0, 0)}, build=rubber_trees, ground=plantation_ground),
    "water_pumps": dict(tiles={118: (0, 0)}, build=water_pumps, ground=im.no_ground),
    "water_treat": dict(tiles={119: (0, 0)}, build=water_treat, ground=im.no_ground),
    "water_tower": dict(tiles={120: (0, 0)}, build=water_tower, ground=im.no_ground),
    "lumber_mill": dict(tiles={125: (0, 0), 126: (0, 1), 127: (1, 0), 128: (1, 1)}, build=lumber_mill,
                        ground=im.no_ground),
}

CLIMATE_UNITS = {
    "arctic": {
        "forest": dict(tiles={16: (0, 0)}, build=snowy_forest, ground=snowy_ground),
        "forest_felled": dict(tiles={17: (0, 0)}, build=snowy_felled, ground=snowy_ground),
    },
    "tropic": {
        "oil_well": dict(tiles={29: (0, 0)}, build=None, ground=desert_oil_ground),
    },
}
