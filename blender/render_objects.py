"""Render the original objects (table/object_land.h) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_objects.py -- <outdir> [--only 2601,2632]

  2601        transmitter: guyed lattice mast, red and white, with dishes; box (7, 7) 2x2x70
  2602        lighthouse: tapered white tower with red bands and a lit lantern; box (4, 4) 7x7x61
  2632        company statue on a stone plinth, figure in company colour; box 0x0 16x16x25
  4790        owned land: flag pole with a company-colour flag; box (8, 8) 1x1x6
  2603-2631   company headquarters, 5 sizes on 2x2 tiles. _object_hq is indexed
              size << 2 | TileY << 1 | TileX: per size the N, E, W, S tiles. Tiny and
              small HQs are drawn entirely in the tiles' ground sprites (kept low);
              medium, large and huge HQs draw the building on N, E and W in full-tile
              boxes (sz 20, 50, 60) above paved ground, the S tile is a forecourt.
              Company colour on fascias, window frames and flags.
Outputs: see build_kit.py (o<sprite>_* building sprites, o<sprite>_color/_mask/_gprops grounds).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_kit as bk  # noqa: E402

CC = {"cc", "cc_light", "cc_flat"}

# HQ sprites per size: tile (tx, ty) -> (ground sprite, building sprite or None)
HQ_SPRITES = {
    0: {(0, 0): (2603, None), (0, 1): (2604, None), (1, 0): (2605, None), (1, 1): (2606, None)},
    1: {(0, 0): (2607, None), (0, 1): (2608, None), (1, 0): (2609, None), (1, 1): (2610, None)},
    2: {(0, 0): (2611, 2612), (0, 1): (2613, 2614), (1, 0): (2615, 2616), (1, 1): (2617, None)},
    3: {(0, 0): (2618, 2619), (0, 1): (2620, 2621), (1, 0): (2622, 2623), (1, 1): (2624, None)},
    4: {(0, 0): (2625, 2626), (0, 1): (2627, 2628), (1, 0): (2629, 2630), (1, 1): (2631, None)},
}


# --- single objects ----------------------------------------------------------------------------

def transmitter(k):
    cx, cy, top = 8.0, 8.0, 72.0
    legs = [(cx + 1.1 * math.cos(a), cy + 1.1 * math.sin(a)) for a in (0.5, 0.5 + math.tau / 3, 0.5 + 2 * math.tau / 3)]

    def leg_at(i, z):
        x, y = legs[i]
        t = z / top
        return (bk.lerp(x, cx, t * 0.55), bk.lerp(y, cy, t * 0.55), z)
    seg = 8.0
    z = 0.0
    n = 0
    while z < top - 0.1:
        z1 = min(top, z + seg)
        mat = "red" if n % 2 == 0 else "white_band"
        for i in range(3):
            k.rod(leg_at(i, z), leg_at(i, z1), 0.16, mat, n=4)
            k.rod(leg_at(i, z), leg_at((i + 1) % 3, z1), 0.07, mat, n=4)
            k.rod(leg_at(i, z1), leg_at((i + 1) % 3, z1), 0.07, mat, n=4)
        z, n = z1, n + 1
    k.cyl(cx, cy, 1.5, 0, 1.2, "concrete", n=6)
    # Platforms, dishes and the antenna on top.
    for zp in (44.0, 60.0):
        k.cyl(cx, cy, 1.5, zp, zp + 0.6, "steel", n=8)
    for ang, zp in ((0.9, 46.5), (2.6, 46.5), (4.4, 62.5)):
        dx, dy = math.cos(ang), math.sin(ang)
        k.rod((cx + dx * 0.9, cy + dy * 0.9, zp), (cx + dx * 1.6, cy + dy * 1.6, zp), 0.12, "steel", n=4)
        k.lathe(cx + dx * 1.9, cy + dy * 1.9, [(0.05, zp - 1.6), (1.0, zp - 1.0), (1.3, zp), (1.0, zp + 1.0), (0.05, zp + 1.6)],
                "white", n=8)
    k.rod((cx, cy, top), (cx, cy, top + 6), 0.1, "steel", n=4)
    k.blob(cx, cy, top + 6.2, 0.3, 0.3, 0.7, "glow", subdiv=1)
    # Guy wires to three anchors on the tile.
    for ax, ay in ((1.5, 9.5), (13.5, 2.5), (12.5, 14.5)):
        for zw in (30.0, 56.0):
            k.rod((bk.lerp(cx, ax, 0.04), bk.lerp(cy, ay, 0.04), zw), (ax, ay, 0.4), 0.05, "steel_dark", n=3)
        k.cbox(ax, ay, 1.0, 1.0, 0, 0.8, "concrete")


def lighthouse(k):
    cx, cy = 7.5, 7.5
    bands = [(0, 9, "white"), (9, 17, "red"), (17, 26, "white"), (26, 34, "red"), (34, 44, "white")]
    r = lambda z: bk.lerp(3.1, 2.1, z / 44)  # noqa: E731
    for z0, z1, mat in bands:
        k.lathe(cx, cy, [(r(z0), z0), (r(z1), z1)], mat, n=14)
    k.lathe(cx, cy, [(3.4, 0), (3.4, 1.4), (3.2, 1.4)], "stone", n=14)
    # Gallery, railing, lantern, roof.
    k.cyl(cx, cy, 3.1, 44, 45.3, "dark", n=14)
    for i in range(14):
        a = i * math.tau / 14
        k.rod((cx + 2.9 * math.cos(a), cy + 2.9 * math.sin(a), 45.3), (cx + 2.9 * math.cos(a), cy + 2.9 * math.sin(a), 48), 0.07,
              "dark", n=3)
    k.lathe(cx, cy, [(2.95, 47.6), (2.95, 48.1)], "dark", n=14)
    k.cyl(cx, cy, 1.9, 45.3, 46.2, "red", n=12)
    k.cyl(cx, cy, 1.7, 46.2, 52.5, "lamp", n=12)
    for i in range(6):
        a = i * math.tau / 6 + 0.2
        k.rod((cx + 1.75 * math.cos(a), cy + 1.75 * math.sin(a), 46.2), (cx + 1.75 * math.cos(a), cy + 1.75 * math.sin(a), 52.5),
              0.08, "dark", n=3)
    k.lathe(cx, cy, [(2.2, 52.5), (2.2, 53.2), (0.4, 58.5), (0.15, 60)], "red", n=12)
    # Door and two small windows facing the viewer.
    k.box(cx + 2.6, cx + 3.2, cy - 0.8, cy + 0.8, 1.4, 6.5, "door")
    for z in (20.0, 30.0):
        k.box(cx - 0.5, cx + 0.5, cy + r(z) - 0.25, cy + r(z) + 0.3, z, z + 3, "glass")


def statue(k):
    cx, cy = 8.0, 8.0
    k.cbox(cx, cy, 9.0, 9.0, 0, 1.4, "plinth")
    k.cbox(cx, cy, 7.0, 7.0, 1.4, 2.8, "stone")
    k.cbox(cx, cy, 4.2, 4.2, 2.8, 11.5, "plinth")
    k.cbox(cx, cy, 4.8, 4.8, 11.5, 12.5, "stone")
    k.cbox(cx + 2.15, cy, 0.2, 2.4, 6, 8.5, "gold")  # name plate
    base = 12.5
    # Figure in a long coat, one arm raised towards the viewer.
    for side in (-1, 1):
        k.cbox(cx, cy + side * 0.75, 1.1, 1.0, base, base + 7.5, "cc")
    k.prism([(cx - 1.0, cy - 1.6), (cx + 0.9, cy - 1.6), (cx + 1.1, cy + 1.6), (cx - 1.0, cy + 1.6)], base + 5.5, base + 15.5,
            "cc")
    k.prism([(cx - 0.8, cy - 1.9), (cx + 0.8, cy - 1.9), (cx + 0.8, cy + 1.9), (cx - 0.8, cy + 1.9)], base + 14.0, base + 15.8,
            "cc")
    k.cyl(cx, cy, 0.45, base + 15.8, base + 16.8, "cc", n=6)
    k.blob(cx, cy, base + 18.6, 0.85, 0.85, 2.1, "cc_light")
    k.rod((cx, cy + 1.6, base + 15), (cx + 0.9, cy + 3.0, base + 22.5), 0.42, "cc", n=6)
    k.rod((cx, cy - 1.6, base + 15), (cx + 0.5, cy - 2.0, base + 8.5), 0.4, "cc", n=6)
    # Planters at the corners of the square.
    for x, y in ((2.5, 2.5), (13.5, 2.5), (2.5, 13.5), (13.5, 13.5)):
        k.cbox(x, y, 2.4, 2.4, 0, 1.6, "stone")
        k.blob(x, y, 2.6, 1.1, 1.1, 2.0, "hedge")


def flag(k):
    k.cyl(8.5, 8.5, 0.12, 0, 14, "steel", n=5)
    k.blob(8.5, 8.5, 14.1, 0.2, 0.2, 0.4, "gold")
    k.box(8.4, 8.6, 6.0, 8.4, 9.6, 13.6, "cc_flat")
    k.cyl(8.5, 8.5, 0.5, 0, 0.5, "concrete", n=6)


# --- company headquarters ---------------------------------------------------------------------

def office(k, x0, x1, y0, y1, floors, floor_h=7.0, base="white", band="cc", roof="roof_flat", ribbon=True):
    """Office block with ribbon windows and a company-colour fascia on every floor."""
    top = floors * floor_h
    k.box(x0, x1, y0, y1, 0, top, base)
    k.windows(x0, x1, y0, y1, 0, top, floor=floor_h, ribbon=ribbon, sill=1.8, wh=3.6, frame="frame")
    for f in range(1, floors + 1):
        z = f * floor_h
        k.box(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, z - 0.9, z - 0.2 if f < floors else z + 0.6, band)
    k.flat_roof(x0, x1, y0, y1, top, base, roof=roof, parapet=0.0)
    # Roof plant: two air handlers and a skylight.
    k.box(x0 + 1.5, x0 + 4.5, y0 + 1.5, y0 + 3.5, top + 0.25, top + 2.6, "steel")
    k.box(x0 + 1.5, x0 + 3.5, y1 - 4.5, y1 - 1.5, top + 0.25, top + 2.0, "steel_dark")
    k.box((x0 + x1) / 2 - 1, (x0 + x1) / 2 + 1.2, y0 + 5, y1 - 5, top + 0.25, top + 1.0, "glass_light")
    return top


def entrance(k, face, x1, y1, pos, w=4.0, h=5.0):
    k.door(face, x1, y1, pos, w=w, h=h, mat="glass_light")
    if face == "x":
        k.box(x1, x1 + 2.2, pos - w / 2 - 0.8, pos + w / 2 + 0.8, h + 0.2, h + 0.9, "cc")
    else:
        k.box(pos - w / 2 - 0.8, pos + w / 2 + 0.8, y1, y1 + 2.2, h + 0.2, h + 0.9, "cc")


def flagpole(k, x, y, h=16.0):
    k.cyl(x, y, 0.12, 0, h, "steel", n=5)
    k.box(x - 0.1, x + 0.1, y - 3.0, y, h - 4.0, h - 0.4, "cc_flat")


def parking(decals, x0, x1, y0, y1, axis="x", n=4):
    """Asphalt with white bay lines (decals)."""
    decals.box(x0, x1, y0, y1, 0, 0.05, "asphalt")
    if axis == "x":
        for x in bk.frange(x0 + 0.6, x1 - 0.6, (x1 - x0 - 1.2) / n):
            decals.box(x - 0.15, x + 0.15, y0 + 0.5, y0 + (y1 - y0) * 0.4, 0.05, 0.08, "marking")
            decals.box(x - 0.15, x + 0.15, y1 - (y1 - y0) * 0.4, y1 - 0.5, 0.05, 0.08, "marking")
    else:
        for y in bk.frange(y0 + 0.6, y1 - 0.6, (y1 - y0 - 1.2) / n):
            decals.box(x0 + 0.5, x0 + (x1 - x0) * 0.4, y - 0.15, y + 0.15, 0.05, 0.08, "marking")
            decals.box(x1 - (x1 - x0) * 0.4, x1 - 0.5, y - 0.15, y + 0.15, 0.05, 0.08, "marking")


def cars(k, spots, seed=0):
    import random
    rng = random.Random(seed)
    colours = ["red", "blue", "white", "steel_dark", "yellow", "grey"]
    for x, y, axis in spots:
        c = rng.choice(colours)
        lx, ly = (3.0, 1.5) if axis == "x" else (1.5, 3.0)
        k.cbox(x, y, lx, ly, 0.4, 2.0, c)
        k.cbox(x, y, lx * 0.6, ly * 0.85 if axis == "x" else ly * 0.6, 2.0, 3.0, "glass" if axis else c)


def hq_model(size):
    """(building kit, decals kit, ground props kit) of the whole 2x2 HQ in model units 0-32."""
    b, d, g = bk.Kit(), bk.Kit(), bk.Kit()
    # Common campus ground: paving with lawn strips, paths and hedges.
    d.box(-1, 33, -1, 33, 0, 0.03, "paving")
    if size == 0:
        d.box(16.5, 33, -1, 15.5, 0.03, 0.06, "lawn")
        d.box(-1, 15.5, 16.5, 33, 0.03, 0.06, "lawn")
        d.box(19, 23, -1, 15.5, 0.06, 0.08, "path")
        parking(d, 17, 31, 17, 31, "x", 4)
        g.box(3, 13, 3, 12, 0, 9.5, "white")
        g.windows(3, 13, 3, 12, 0, 9.5, floor=9.5, ribbon=True, sill=1.6, wh=5.0)
        g.box(2.8, 13.2, 2.8, 12.2, 8.3, 10.0, "cc")
        g.box(3.4, 12.6, 3.4, 11.6, 10.0, 10.3, "roof_flat")
        g.door("x", 13, 12, 7.5, w=3.0, h=6.0, mat="glass_light")
        flagpole(g, 14.5, 14.5, 14)
        for x, y in ((24, 4), (27, 11), (6, 24), (11, 28)):
            g.tree(x, y, 0.6)
        cars(g, [(20.5, 19.5, "y"), (26.5, 19.5, "y"), (23.5, 28.5, "y")], seed=1)
        return b, d, g
    if size == 1:
        d.box(-1, 15.5, 16.5, 33, 0.03, 0.06, "lawn")
        parking(d, 17, 31, 1, 15, "x", 4)
        d.box(17, 31, 17, 31, 0.03, 0.06, "lawn")
        d.box(22, 26, 17, 33, 0.06, 0.08, "path")
        g.box(2, 14, 2, 14, 0, 9.5, "white")
        g.box(2, 9, 14, 24, 0, 9.5, "white")
        for x0, x1, y0, y1 in ((2, 14, 2, 14), (2, 9, 14, 24)):
            g.windows(x0, x1, y0, y1, 0, 9.5, floor=9.5, ribbon=True, sill=1.6, wh=5.0)
            g.box(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, 8.3, 10.0, "cc")
            g.box(x0 + 0.4, x1 - 0.4, y0 + 0.4, y1 - 0.4, 10.0, 10.3, "roof_flat")
        g.door("x", 14, 14, 8, w=3.0, h=6.0, mat="glass_light")
        g.box(14, 16, 5.5, 10.5, 6.2, 6.8, "cc")
        flagpole(g, 15.2, 15.2, 15)
        for x, y in ((12, 19), (12, 28), (26, 21), (28, 28)):
            g.tree(x, y, 0.65)
        cars(g, [(20.5, 4.5, "y"), (23.5, 11.5, "y"), (29, 4.5, "y")], seed=2)
        return b, d, g
    # Medium, large, huge: U-shaped block over N, E and W tiles, forecourt on S.
    floors, tower = {2: (2, 0), 3: (5, 0), 4: (5, 3)}[size]
    fh = 7.5 if size == 2 else 7.6
    office(b, 2, 14.5, 2, 14.5, floors + tower, fh)
    office(b, 2, 14.5, 16, 30, floors, fh)
    office(b, 16, 30, 2, 14.5, floors, fh)
    # Glazed links across the tile edges.
    b.box(4, 13, 14.5, 16, 0, floors * fh - 1.2, "glass_light")
    b.box(14.5, 16, 4, 13, 0, floors * fh - 1.2, "glass_light")
    entrance(b, "x", 30, 14.5, 8.0)
    entrance(b, "y", 14.5, 30, 8.0)
    if size == 4:
        # Roof top of the tower: helipad and the company sign.
        t = (floors + tower) * fh
        b.cyl(8.25, 8.25, 5.0, t + 0.3, t + 1.0, "concrete_dark", n=12)
        b.cyl(8.25, 8.25, 3.6, t + 1.0, t + 1.1, "cc_flat", n=12)
        b.box(13.8, 14.6, 4, 12.5, t - 5, t - 1, "cc")
    elif size == 3:
        b.box(13.8, 14.6, 4, 12.5, floors * fh - 5, floors * fh - 1, "cc")
    d.box(16.2, 33, 16.2, 33, 0.03, 0.06, "lawn")
    d.box(16.2, 33, 21.5, 24.5, 0.06, 0.09, "path")
    d.box(21.5, 24.5, 16.2, 33, 0.06, 0.09, "path")
    g.cyl(23, 23, 3.0, 0, 1.2, "stone", n=12)
    g.cyl(23, 23, 2.5, 1.0, 1.25, "water", n=12)
    g.cyl(23, 23, 0.4, 1.0, 3.5, "white", n=6)
    for x, y in ((18.5, 18.5), (28, 18.5), (18.5, 28)):
        g.tree(x, y, 0.6)
    flagpole(g, 30, 30, 16)
    flagpole(g, 30, 27, 16)
    return b, d, g


def tile_parts(parts, tx, ty):
    return bk.clip_parts(parts, tx * 16, tx * 16 + 16, ty * 16, ty * 16 + 16)


def render_hq(outdir, size, only):
    b, d, g = hq_model(size)
    for (tx, ty), (ground, build) in HQ_SPRITES[size].items():
        shift = (tx * 16, ty * 16)
        if not only or ground in only:
            # Decals overlap the tile edges so the colour pass covers the overscan margin.
            decals = bk.clip_parts(d.parts, tx * 16 - 1, tx * 16 + 17, ty * 16 - 1, ty * 16 + 17)
            bk.render_ground(outdir, f"o{ground}", "grass", decals, shift, tile_parts(g.parts, tx, ty), cc=CC)
            print(f"rendered hq ground {ground}", flush=True)
        if build and (not only or build in only):
            parts = tile_parts(b.parts, tx, ty)
            bk.render_building(outdir, f"o{build}", parts, shift, cc=CC, shadow_parts=b.parts,
                               shadow_tiles=[(tx, ty)])
            print(f"rendered hq building {build}", flush=True)


OBJECTS = {2601: (transmitter, (7, 7)), 2602: (lighthouse, (4, 4)), 2632: (statue, (0, 0)), 4790: (flag, (8, 8))}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv and not argv[0].startswith("--") else os.path.join(os.getcwd(), "render", "objects")
    only = {int(s) for s in argv[argv.index("--only") + 1].split(",")} if "--only" in argv else None
    for sprite, (fn, shift) in OBJECTS.items():
        if only and sprite not in only:
            continue
        k = bk.Kit()
        fn(k)
        bk.render_building(outdir, f"o{sprite}", k.parts, shift, cc=CC)
        print(f"rendered object {sprite}", flush=True)
    for size in HQ_SPRITES:
        render_hq(outdir, size, only)


if __name__ == "__main__":
    main()
