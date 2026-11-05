#!/usr/bin/env python3
"""Generate tile-space ground textures for the town house grounds.

Same layout as make_infra_textures.py: one texture covers one tile (Blender
x, y in -0.5..0.5; row 0 is y = +0.5), so texture rows run along OpenTTD x
and columns along OpenTTD y. render_houses.py lays them on the flat tile.

Kinds (blender/house_specs.py decides which ground gets which):
  paving        light concrete slabs (town centre)
  yard          paving with planted beds along the tile edges
  garden        lawn with a hedge round the plot, flower beds and a stone path
                from the door to the street side
  construction  trodden earth, a concrete slab on the building footprint
  pitch1/pitch2 one quarter of a football or rugby pitch with mown stripes,
                concrete under the stands
  plaza         mall forecourt: paving with marked parking bays
  garden_wall   garden behind a low brick wall instead of the hedge
  *_snow        sub-arctic grounds above the snow line: the same under snow, paths swept
  desert_*      sub-tropical: sand garden with a lawn and a tiled path behind a white
                wall, sandy yard with dry grass, sandstone paving
  toy_lawn      toyland: the toyland meadow (toy_grass.png) with confetti-coloured flowers
  toy_paving    toyland: pastel chequered tiles

Written to <outdir>/g<sprite>.png (RGB); grounds drawn inside a building sprite
(the "base" of finished houses on bare land) to <outdir>/b<sprite>.png.

Usage: make_house_textures.py <render/textures> <ref/houses/houses.json> <outdir> [size]
"""

import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
import house_specs as hs  # noqa: E402

PAVING = np.array([196, 194, 184.0])
PAVING_JOINT = np.array([176, 174, 164.0])
HEDGE = np.array([70, 122, 70.0])
HEDGE_DARK = np.array([56, 100, 60.0])
PATH = np.array([206, 196, 176.0])
PATH_JOINT = np.array([170, 160, 142.0])
SOIL = np.array([128, 98, 72.0])
FLOWERS = (np.array([236, 120, 120.0]), np.array([246, 214, 96.0]), np.array([240, 240, 236.0]),
           np.array([170, 130, 214.0]))
SLAB = np.array([178, 178, 172.0])
LINE = np.array([244, 244, 236.0])
STAND_FLOOR = np.array([168, 166, 160.0])
MARKING = np.array([250, 246, 226.0])
ASPHALT = np.array([96, 100, 106.0])
BRICK_WALL = np.array([150, 84, 66.0])
WHITE_WALL = np.array([238, 234, 222.0])
SNOW_HEDGE = np.array([206, 222, 214.0])
SANDSTONE = np.array([222, 196, 150.0])
SANDSTONE_JOINT = np.array([196, 168, 124.0])
TERRACOTTA = np.array([198, 116, 82.0])
DRY_GRASS = np.array([176, 166, 92.0])
TOY_COLOURS = (np.array([226, 70, 64.0]), np.array([66, 120, 214.0]), np.array([244, 202, 60.0]),
               np.array([236, 140, 178.0]), np.array([150, 116, 222.0]))


def grid(n):
    """OpenTTD tile units per pixel: u along x (rows), v along y (columns), 0-16."""
    c = (np.arange(n) + 0.5) / n * 16
    return np.tile(c[:, None], (1, n)), np.tile(c, (n, 1))


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def blend(img, colour, alpha):
    a = np.clip(alpha, 0, 1)[..., None]
    img[:] = img * (1 - a) + colour * a


def rect_alpha(u, v, r, soft=0.08):
    x0, y0, x1, y1 = r
    return (smooth(x0 - soft, x0 + soft, u) * (1 - smooth(x1 - soft, x1 + soft, u)) *
            smooth(y0 - soft, y0 + soft, v) * (1 - smooth(y1 - soft, y1 + soft, v)))


def noise(n, rng, scale=8):
    small = rng.random((scale, scale))
    return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC), float) / 255


def load_tiled(path, n):
    return np.asarray(Image.open(path).convert("RGB").resize((n, n), Image.BICUBIC), dtype=float)


def paving(n, u, v, rng, slab=2.0):
    img = np.empty((n, n, 3))
    img[:] = PAVING * (1 + (noise(n, rng, 16)[..., None] - 0.5) * 0.06)
    joint = (np.mod(u, slab) < 0.12) | (np.mod(v, slab) < 0.12)
    blend(img, PAVING_JOINT, joint.astype(float))
    return img


def footprint(u, v, rects, pad=0.0):
    a = np.zeros_like(u)
    for x0, y0, x1, y1 in rects:
        a = np.maximum(a, rect_alpha(u, v, (x0 - pad, y0 - pad, x1 + pad, y1 + pad)))
    return a


def garden(n, u, v, rng, grass, foot, door, border="hedge", snow=None):
    """snow: the snow texture; the plot then lies under snow with the path swept."""
    img = (snow if snow is not None else grass).copy()
    # Hedge round the plot, open where the path meets the street side.
    edge = np.minimum.reduce([u, v, 16 - u, 16 - v])
    hedge = 1 - smooth(0.8, 1.0, edge)
    if foot:
        fx0 = min(r[0] for r in foot)
        fy0 = min(r[1] for r in foot)
        fx1 = max(r[2] for r in foot)
        fy1 = max(r[3] for r in foot)
    else:
        fx0, fy0, fx1, fy1 = 5, 5, 11, 11
    if door == "x":
        mid = (fy0 + fy1) / 2
        path = rect_alpha(u, v, (fx1 - 0.5, mid - 1.1, 16.5, mid + 1.1))
    elif door == "y":
        mid = (fx0 + fx1) / 2
        path = rect_alpha(u, v, (mid - 1.1, fy1 - 0.5, mid + 1.1, 16.5))
    else:
        path = np.zeros_like(u)
    hedge *= 1 - smooth(0.2, 0.6, path)
    leaf = noise(n, rng, 48)
    if border == "wall":
        hedge = (1 - smooth(0.45, 0.6, edge)) * (1 - smooth(0.2, 0.6, path))
        course = (np.mod(u + v * 0.0, 0.7) < 0.1) | (np.mod(v, 0.7) < 0.1)
        blend(img, BRICK_WALL * (1 - 0.15 * course[..., None]), hedge)
    else:
        blend(img, HEDGE_DARK + (HEDGE - HEDGE_DARK) * leaf[..., None], hedge)
    if snow is not None:
        blend(img, SNOW_HEDGE, hedge * (0.55 + 0.3 * leaf))
        stones = PATH * 0.94 * (1 + (noise(n, rng, 32)[..., None] - 0.5) * 0.08)
        blend(img, stones, path)
        blend(img, snow, path * (noise(n, rng, 20) > 0.6) * 0.7)
        blend(img, PAVING_JOINT, footprint(u, v, foot))
        return img
    # Flower beds along the house walls, dotted with blossoms.
    bed = footprint(u, v, foot, pad=0.9) * (1 - footprint(u, v, foot)) * (1 - path)
    blend(img, SOIL, bed)
    dots = rng.random((n, n))
    for k, colour in enumerate(FLOWERS):
        spot = (dots > 0.985 - 0.004 * k) & (dots <= 0.99 - 0.004 * k)
        blend(img, colour, bed * spot)
    # Loose flowers in the lawn.
    lawn = (1 - hedge) * (1 - bed) * (1 - path) * (1 - footprint(u, v, foot, pad=0.2))
    blossom = noise(n, rng, 6) > 0.62
    blend(img, FLOWERS[1], lawn * blossom * (rng.random((n, n)) > 0.993))
    # Stone path, laid in square stones.
    stones = PATH * (1 + (noise(n, rng, 32)[..., None] - 0.5) * 0.08)
    blend(img, stones, path)
    joints = (np.mod(u, 1.1) < 0.12) | (np.mod(v, 1.1) < 0.12)
    blend(img, PATH_JOINT, path * joints)
    blend(img, PAVING_JOINT, footprint(u, v, foot))
    return img


def yard(n, u, v, rng, grass, foot):
    img = paving(n, u, v, rng)
    edge = np.minimum.reduce([u, v, 16 - u, 16 - v])
    bed = 1 - smooth(1.0, 1.2, edge)
    bed *= (np.mod(u + v, 6) > 1.4).astype(float)  # gaps for the entrances
    blend(img, grass, bed)
    kerb = (1 - smooth(1.2, 1.35, edge)) * smooth(0.95, 1.1, edge)
    blend(img, SLAB, kerb * (np.mod(u + v, 6) > 1.4))
    return img


def snowy(img, n, rng, snow, cover=0.75):
    """Snow over a ground, thinner in patches."""
    blend(img, snow, cover * smooth(0.25, 0.55, noise(n, rng, 10)) + 0.2)
    return img


def desert_garden(n, u, v, rng, sand, grass, foot, door):
    img = sand.copy()
    edge = np.minimum.reduce([u, v, 16 - u, 16 - v])
    lawn = smooth(1.6, 2.4, edge) * smooth(0.35, 0.6, noise(n, rng, 6) + 0.25)
    blend(img, grass * 0.92, lawn)
    if door:
        fx1 = max(r[2] for r in foot)
        fy1 = max(r[3] for r in foot)
        mid = (min(r[1] for r in foot) + fy1) / 2 if door == "x" else (min(r[0] for r in foot) + fx1) / 2
        r = (fx1 - 0.5, mid - 1.0, 16.5, mid + 1.0) if door == "x" else (mid - 1.0, fy1 - 0.5, mid + 1.0, 16.5)
        path = rect_alpha(u, v, r)
        blend(img, TERRACOTTA * (1 + (noise(n, rng, 32)[..., None] - 0.5) * 0.1), path)
        blend(img, TERRACOTTA * 0.8, path * ((np.mod(u, 1.0) < 0.1) | (np.mod(v, 1.0) < 0.1)))
    else:
        path = np.zeros_like(u)
    wall = (1 - smooth(0.4, 0.55, edge)) * (1 - smooth(0.2, 0.6, path))
    blend(img, WHITE_WALL, wall)
    blend(img, SANDSTONE_JOINT, footprint(u, v, foot))
    return img


def desert_yard(n, u, v, rng, sand, foot):
    img = sand * (1 + (noise(n, rng, 12)[..., None] - 0.5) * 0.08)
    tufts = (noise(n, rng, 40) > 0.62) * (rng.random((n, n)) > 0.6)
    blend(img, DRY_GRASS, tufts * 0.8)
    blend(img, SANDSTONE_JOINT, footprint(u, v, foot, pad=0.3) * 0.6)
    return img


def desert_paving(n, u, v, rng, sand):
    img = np.empty((n, n, 3))
    img[:] = SANDSTONE * (1 + (noise(n, rng, 16)[..., None] - 0.5) * 0.06)
    joint = (np.mod(u, 2.6) < 0.12) | (np.mod(v + np.floor(u / 2.6) * 1.3, 2.6) < 0.12)
    blend(img, SANDSTONE_JOINT, joint.astype(float))
    blend(img, sand, (noise(n, rng, 14) > 0.7) * 0.5)
    return img


def toy_lawn(n, u, v, rng, toy_grass):
    img = toy_grass.copy()
    dots = rng.random((n, n))
    for k, colour in enumerate(TOY_COLOURS):
        blend(img, colour, ((dots > 0.996 - 0.0012 * k) & (dots <= 0.9972 - 0.0012 * k)).astype(float))
    return img


def toy_paving(n, u, v, rng):
    img = np.empty((n, n, 3))
    check = (np.floor(u / 2) + np.floor(v / 2)) % 2
    img[:] = np.array([246, 226, 206.0])
    blend(img, np.array([170, 204, 236.0]), check)
    blend(img, np.array([226, 212, 196.0]), ((np.mod(u, 2) < 0.1) | (np.mod(v, 2) < 0.1)).astype(float))
    return img


def construction(n, u, v, rng, bare, foot):
    img = bare.copy()
    blend(img, SOIL, noise(n, rng, 12) * 0.45)
    for r in foot or [(4, 4, 12, 12)]:
        blend(img, SLAB * (1 + (noise(n, rng, 24)[..., None] - 0.5) * 0.08), rect_alpha(u, v, r))
    # Tyre tracks towards the street sides.
    tracks = (np.abs(np.mod(v, 16) - 6) < 0.25) | (np.abs(np.mod(v, 16) - 8.5) < 0.25)
    blend(img, SOIL * 0.82, tracks * smooth(10, 14, u) * 0.6)
    return img


def pitch(n, u, v, rng, grass, tile, kind):
    tx, ty = tile
    gx, gy = u + tx * 16, v + ty * 16  # frame of the whole 2x2 stadium
    img = grass * 1.06
    stripes = np.mod(np.floor(gy / 2.0), 2) == 0
    blend(img, grass * 0.88, stripes.astype(float))
    # Pitch rectangle, lines 0.18 wide; stands round it stand on concrete.
    x0, y0, x1, y1 = (7, 6, 27, 26) if kind == "pitch1" else (8, 5, 26, 27)
    inside = rect_alpha(gx, gy, (x0 - 1.5, y0 - 1.5, x1 + 1.5, y1 + 1.5), 0.05)
    floor = 1 - inside
    blend(img, STAND_FLOOR * (1 + (noise(n, rng, 16)[..., None] - 0.5) * 0.06), floor)
    w = 0.1
    outline = (rect_alpha(gx, gy, (x0 - w, y0 - w, x1 + w, y1 + w), 0.02) -
               rect_alpha(gx, gy, (x0 + w, y0 + w, x1 - w, y1 - w), 0.02))
    my = (y0 + y1) / 2
    half = (np.abs(gy - my) < w) * rect_alpha(gx, gy, (x0, y0, x1, y1), 0.02)
    marks = outline + half
    if kind == "pitch1":
        cx = (x0 + x1) / 2
        r = np.hypot(gx - cx, gy - my)
        marks += (np.abs(r - 2.6) < w) * 1.0
        for yy, d in ((y0, 1), (y1, -1)):  # penalty areas
            box = ((np.abs(gx - cx) < 4.5) * ((gy - yy) * d >= 0) * ((gy - yy) * d < 3.2))
            edge = box * ((np.abs(np.abs(gx - cx) - 4.5) < w * 1.5) | (np.abs((gy - yy) * d - 3.2) < w * 1.5))
            marks += edge
    else:
        for yy in (y0 + 5, y1 - 5, y0 + 1.6, y1 - 1.6):  # 22 m and try lines
            marks += (np.abs(gy - yy) < w) * rect_alpha(gx, gy, (x0, y0, x1, y1), 0.02)
    blend(img, LINE, np.clip(marks, 0, 1))
    return img


def plaza(n, u, v, rng, tile):
    tx, ty = tile
    gx, gy = u + tx * 16, v + ty * 16
    img = paving(n, u, v, rng)
    # Parking along the front sides of the mall.
    lot = np.maximum(rect_alpha(gx, gy, (29.6, 1, 32, 31), 0.05), rect_alpha(gx, gy, (1, 29.6, 31, 32), 0.05))
    blend(img, ASPHALT * (1 + (noise(n, rng, 16)[..., None] - 0.5) * 0.05), lot)
    bays = ((np.mod(gy, 2.2) < 0.12) & (gx > 30.2)) | ((np.mod(gx, 2.2) < 0.12) & (gy > 30.2))
    blend(img, MARKING, lot * bays)
    return img


def main():
    tex_dir, table, outdir = sys.argv[1:4]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 256
    os.makedirs(outdir, exist_ok=True)
    data = json.load(open(table))
    grass = load_tiled(os.path.join(tex_dir, "grass.png"), n)
    toy_grass = load_tiled(os.path.join(tex_dir, "toy_grass.png"), n)
    bare = load_tiled(os.path.join(tex_dir, "bare.png"), n)
    snow = load_tiled(os.path.join(tex_dir, "snow4.png"), n)
    sand = load_tiled(os.path.join(tex_dir, "desert4.png"), n)
    u, v = grid(n)
    work = [("g", s, j) for s, j in sorted(hs.ground_jobs(data).items())]
    work += [("b", s, dict(j, kind=j["base"], props=False)) for s, j in sorted(hs.building_jobs(data).items())
             if j["base"]]
    for prefix, sprite, job in work:
        rng = np.random.default_rng(sprite)
        spec = hs.spec(job["model"]) if job["model"] else {}
        foot, door = spec.get("foot", []), spec.get("door")
        tile = hs.TILE_OFFSET.get(job["tile"], (0, 0))
        if job["model"] in hs.MULTI.values():
            # Multi-tile footprints are in the house frame; shift them into this tile.
            foot = [(x0 - tile[0] * 16, y0 - tile[1] * 16, x1 - tile[0] * 16, y1 - tile[1] * 16)
                    for x0, y0, x1, y1 in foot]
        kind = job["kind"]
        is_snow = kind.endswith("_snow")
        kind = kind.removesuffix("_snow")
        if kind == "paving":
            img = paving(n, u, v, rng)
        elif kind == "yard":
            img = yard(n, u, v, rng, grass, foot)
        elif kind in ("garden", "garden_wall"):
            img = garden(n, u, v, rng, grass, foot, door, "wall" if kind == "garden_wall" else "hedge",
                         snow if is_snow else None)
            is_snow = False
        elif kind == "desert_garden":
            img = desert_garden(n, u, v, rng, sand, grass, foot, door)
        elif kind == "desert_yard":
            img = desert_yard(n, u, v, rng, sand, foot)
        elif kind == "desert_paving":
            img = desert_paving(n, u, v, rng, sand)
        elif kind == "toy_lawn":
            img = toy_lawn(n, u, v, rng, toy_grass)
        elif kind == "toy_paving":
            img = toy_paving(n, u, v, rng)
        elif kind == "construction":
            img = construction(n, u, v, rng, bare, foot)
        elif kind in ("pitch1", "pitch2"):
            img = pitch(n, u, v, rng, grass, tile, kind)
        elif kind == "plaza":
            img = plaza(n, u, v, rng, tile)
        else:
            raise ValueError(kind)
        if is_snow:
            img = snowy(img, n, rng, snow)
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(
            os.path.join(outdir, f"{prefix}{sprite}.png"))


if __name__ == "__main__":
    main()
