"""Gold mine (sub-arctic, 4x4) and diamond mine (sub-tropical, 3x3): open pits like the iron ore mine.

Both draw every tile as a full-tile picture, at stage 0 in the ground sprite and
later partly as building sprites drawn over 2022 (_industry_draw_tile_data); a
building sprite with the box at the tile's north corner has the same anchor as
a ground sprite, so all of them render the way iron_mine.py does: the whole pit
seen through the tile's diamond, parts standing above the ground cut to the tile.

gfx first + n*tx + ty sits at layout tile (tx, ty). Sprites per stage are
SPRITES[stage] + n*tx + ty for stage 0, 1 (also used at stage 2) and 3.
The gold mine's head frame on gfx 79 is a building (2263-2265, industry_climates.py).
"""

import math
import os

import bmesh

import build_kit as bk
import iron_mine as iron
import render_ground as rg


def rounded_rim(cx, cy, rx, ry, keep=()):
    """Distance inside a rounded-rectangle outline; keep lists (x0, y0, x1, y1) boxes that stay at ground level."""
    def rim(x, y):
        p = 4.0
        ax, ay = abs(x - cx) / rx, abs(y - cy) / ry
        d = (1 - (ax ** p + ay ** p) ** (1 / p)) * min(rx, ry)
        for x0, y0, x1, y1 in keep:
            inside = min(x - x0, x1 - x, y - y0, y1 - y)
            if inside > -3:
                d = min(d, -inside - 1.0)
        return d
    return rim


def make_height(rim, step, bench):
    def height(x, y, benches):
        d = rim(x, y)
        if d <= 0:
            return 0.0
        if benches == 1:
            return -0.6 * min(1.0, d / 1.5)
        z = 0.0
        for b in range(benches):
            t = d - b * step
            if t <= 0:
                break
            z -= bench * min(1.0, t / 1.4)
        return z
    return height


def terrain(size, height, rim, benches):
    n = size * 2
    step = size / n
    bm = bmesh.new()
    verts = {}
    for i in range(n + 1):
        for j in range(n + 1):
            x, y = i * step, j * step
            verts[i, j] = bm.verts.new(bk.to_blender(x, y, height(x, y, benches), (0, 0)))
    for i in range(n):
        for j in range(n):
            f = bm.faces.new([verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]])
            cx, cy = (i + 0.5) * step, (j + 0.5) * step
            f.material_index = 0 if rim(cx, cy) <= -0.3 else 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def fence_around(k, rim, size, centre, skip=()):
    pts = []
    for a in range(0, 361, 10):
        t = math.radians(a)
        c, s = math.cos(t), math.sin(t)
        r = 4.0
        while rim(centre[0] + r * c, centre[1] + r * s) > -1.2 and r < size:
            r += 0.25
        x, y = centre[0] + r * c, centre[1] + r * s
        if 0.8 < x < size - 0.8 and 0.8 < y < size - 0.8 and not any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in skip):
            pts.append((x, y))
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if math.hypot(xb - xa, yb - ya) < 8:
            k.fence([(xa, ya), (xb, yb)], h=2.4, mat="steel", post=3.0)


# --- gold mine ---------------------------------------------------------------------------------

GOLD_RIM = rounded_rim(38, 30, 20, 15, keep=[(0, 0, 17, 17), (16, 48, 32, 64)])


def gold_props(stage):
    k = bk.Kit()
    fence_around(k, GOLD_RIM, 64, (38, 30), skip=[(0, 0, 18, 18), (15, 46, 33, 64)])
    if stage == 0:
        k.heap(8, 9, 4.0, 3.5, 4, "soil", seed=71)
        k.heap(52, 52, 3.5, 3.0, 3, "soil", seed=72)
        iron.tractor_like(k, 40, 28)
        return k
    # Timber hut (later the stamp mill) on the north tile.
    if stage == 1:
        k.box(4, 11, 4, 10, 0, 7, "wood")
        k.gable(4, 11, 4, 10, 7, 10, "x", "roof_slate", "wood", over=0.4)
        iron.excavator(k, 40, 28, -4)
        k.heap(10, 14, 3.0, 2.0, 3, "rock", seed=73)
        return k
    # Stamp mill: stepped timber building down the slope, with an ore bin and a chimney.
    k.box(2, 12, 3, 12, 0, 12, "wood")
    k.gable(2, 12, 3, 12, 12, 16, "y", "roof_slate", "wood", over=0.4)
    k.windows(2, 12, 3, 12, 0, 12, floor=12, ww=1.0, wh=2.4, pitch=2.4, sill=6)
    k.box(12, 15, 4, 11, 0, 7, "wood_dark")
    k.flat_roof(12, 15, 4, 11, 7, "wood_dark", roof="roof_slate", parapet=0.0)
    im_chimney(k, 4, 5, 26)
    k.heap(14, 15, 2.6, 2.0, 4, "rock", seed=74)
    # Rail track from the mill along the pit edge, with a few ore wagons.
    for x in bk.frange(14, 56, 3):
        k.box(x - 0.2, x + 0.2, 45.6, 48.4, 0, 0.25, "wood_dark")
    for off in (-0.6, 0.6):
        k.box(14, 56, 47 + off - 0.1, 47 + off + 0.1, 0.25, 0.45, "steel_dark")
    for x in (40, 44.5):
        k.box(x - 1.8, x + 1.8, 46, 48, 0.5, 2.6, "rust")
        k.heap(x, 47, 1.3, 0.7, 1.0, "rock", seed=int(x))
    iron.excavator(k, 40, 26, -12)
    iron.dumper(k, 30, 34, -8)
    return k


def im_chimney(k, x, y, top):
    k.cyl(x, y, 0.7, 0, top, "steel_dark", n=8)
    k.cyl(x, y, 0.8, top - 1, top, "dark", n=8)


GOLD = dict(name="gold", size=4, sprites={0: 2215, 1: 2231, 3: 2247}, benches={0: 1, 1: 2, 3: 3},
            rim=GOLD_RIM, height=make_height(GOLD_RIM, 4.0, 4.0), props=gold_props,
            outside="grass", pit="industry/dirt", pond=((40, 30), 3.5))


# --- diamond mine ------------------------------------------------------------------------------

DIAMOND_RIM = rounded_rim(28, 28, 17, 17, keep=[(0, 0, 15, 15)])


def diamond_props(stage):
    k = bk.Kit()
    fence_around(k, DIAMOND_RIM, 48, (28, 28), skip=[(0, 0, 16, 16)])
    if stage == 0:
        k.heap(7, 8, 4.0, 3.5, 4, "sand", seed=81)
        iron.tractor_like(k, 26, 28)
        return k
    # Processing plant on the north tile: crusher hall, conveyor into the pit.
    k.box(2, 12, 2, 9, 0, 10, "concrete")
    k.box(1.8, 12.2, 1.8, 9.2, 8.6, 9.6, "cc")
    k.flat_roof(2, 12, 2, 9, 10, "concrete", parapet=0.5)
    if stage == 1:
        iron.excavator(k, 28, 26, -4)
        return k
    k.box(3, 8, 3, 7, 10, 16, "steel")
    k.gable(3, 8, 3, 7, 16, 18, "y", "steel_dark", "steel", over=0.2, thick=0.2)
    iron.bk_conv(k, (8, 8, 14), (17, 17, 6))
    k.heap(12, 13, 2.8, 2.4, 4, "kimberlite", seed=82)
    k.box(3, 10, 11, 14, 0, 5, "white")
    k.box(2.8, 10.2, 10.8, 14.2, 4.2, 5.0, "cc")
    iron.excavator(k, 30, 22, -14)
    iron.dumper(k, 22, 34, -10)
    return k


DIAMOND = dict(name="diamond", size=3, sprites={0: 2266, 1: 2275, 3: 2284}, benches={0: 1, 1: 2, 3: 4},
               rim=DIAMOND_RIM, height=make_height(DIAMOND_RIM, 3.4, 4.5), props=diamond_props,
               outside="desert4", pit="industry/dirt", pond=((30, 30), 3.0))

MINES = (GOLD, DIAMOND)
SPRITES = {s: m for m in MINES for first in m["sprites"].values() for s in range(first, first + m["size"] ** 2)}


def render(outdir, sprite):
    mine = SPRITES[sprite]
    n = mine["size"]
    stage, first = max((st, f) for st, f in mine["sprites"].items() if f <= sprite)
    i = sprite - first
    tx, ty = i // n, i % n
    shift = (tx * 16, ty * 16)
    benches = mine["benches"][stage]
    bm = terrain(n * 16, mine["height"], mine["rim"], benches)
    p = mine["props"](stage)
    tile_props = bk.clip_parts(p.parts, tx * 16, tx * 16 + 16, ty * 16, ty * 16 + 16)
    name = f"g{sprite}"
    for zoom in bk.ZOOMS:
        zdir = os.path.join(outdir, f"z{zoom}")
        os.makedirs(zdir, exist_ok=True)
        scene = bk.new_scene(zoom, bk.GROUND_SIZE, bk.GROUND_SIZE, bk.GROUND_ANCHOR)
        mats = [bk.ground_material(mine["outside"]), bk.ground_material(mine["pit"] if stage else "industry/yard")]
        iron.link_bm(bm, mats, shift)
        if stage == 3:
            (px, py), r = mine["pond"]
            z = mine["height"](px, py, benches)
            water = bk.Kit()
            water.cyl(px, py, r, z - 0.6, z + 0.15, "water", n=12)
            bk.link_parts(water.parts, shift, bk.Materials("color"))
        bk.render(scene, os.path.join(zdir, f"{name}_color.png"))
        scene = bk.new_scene(zoom, bk.GROUND_SIZE, bk.GROUND_SIZE, bk.GROUND_ANCHOR, samples=16)
        scene.cycles.filter_width = 0.01
        rg.build_tile(0, 1.0).data.materials.append(rg.mask_material())
        bk.render(scene, os.path.join(zdir, f"{name}_mask.png"))
        if tile_props:
            scene = bk.new_scene(zoom, bk.GROUND_SIZE, bk.GROUND_SIZE, bk.GROUND_ANCHOR)
            iron.link_bm(bm, None, shift, holdout=True)
            bk.link_parts(tile_props, shift, bk.Materials("color", fixed=True))
            bk.render(scene, os.path.join(zdir, f"{name}_gprops.png"))
    bm.free()
    print(f"rendered {mine['name']} mine tile {sprite}", flush=True)
