#!/usr/bin/env python3
"""Preview vehicle sprites placed as the game draws them, next to the OpenGFX originals.

Usage: preview_vehicles.py <render-dir> <out.png> <zoom> [name:ref_dir:first_sprite[:kind] ...]

Per vehicle two rows of 8 directions over a sea of tiles: our sprite (packed as
pack_vehicles.py does) and the OpenGFX sprite scaled to the zoom. The vehicle
sits on a tile centre, the red line is its path, the cross its position.
kind train (8 sprites) or train4 (4 sprites, used as direction & 3) draws the
vehicle three times, 8 steps apart along the track as in a train, over the rails.
kind road draws the vehicle on grass in its lane (grey, 3.7 units wide around the
lane centre one unit right and below the position, see TYPES in render_vehicles.py).
A ref_dir of - leaves out the OpenGFX row.
"""

import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack_vehicles as pv  # noqa: E402

SHIP_ORIGIN = [(-3, -3), (-16, -3), (-3, -3), (-3, -16), (-3, -3), (-16, -3), (-3, -3), (-3, -16)]
TRAIN_ORIGIN = [(-1, -1), (-3, -1), (-1, -1), (-1, -3)] * 2
BALLAST, RAIL = (150, 140, 126, 255), (90, 92, 98, 255)
ROAD_ORIGIN = [(-1, -1), (-2, -1), (-1, -1), (-1, -2), (-1, -1), (-2, -1), (-1, -1), (-1, -2)]
GRASS, LANE = (118, 150, 92, 255), (120, 124, 128, 255)
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
WATER, GRID = (70, 140, 170, 255), (96, 162, 190, 255)


def remap(x, y, z=0):
    return (y - x) * 2, x + y - z


def tint(im, cc, rgb=(60, 110, 200)):
    """Company colour (dark blue) on the recolour mask, shaded by the rendered brightness."""
    grey = im.convert("L")
    col = Image.merge("RGB", [grey.point(lambda v, c=c: min(255, round(c * v / 150))) for c in rgb])
    out = im.copy()
    out.paste(col, mask=cc)
    out.putalpha(im.getchannel("A"))
    return out


def cell(zoom, draw_sprite, d, kind="ship"):
    road = kind == "road"
    w, h = (64 * zoom, 44 * zoom) if road else (150 * zoom, 96 * zoom)
    im = Image.new("RGBA", (w, h), GRASS if road else WATER)
    dr = ImageDraw.Draw(im)
    vx, vy = w // 2, (26 if road else 52) * zoom

    def line(a, b, fill, width):
        p, q = remap(*a), remap(*b)
        dr.line([(vx + p[0] * zoom, vy + p[1] * zoom), (vx + q[0] * zoom, vy + q[1] * zoom)], fill=fill, width=width)
    dx, dy = DIRS[d]
    if road:
        n = (-dy, dx) if dx * dy == 0 else (0, 0)
        pts = [remap(1 + dx * s * 30 + n[0] * t, 1 + dy * s * 30 + n[1] * t)
               for s, t in ((-1, -1.85), (1, -1.85), (1, 1.85), (-1, 1.85))]
        if n != (0, 0):
            dr.polygon([(vx + p[0] * zoom, vy + p[1] * zoom) for p in pts], fill=LANE)
    else:
        for t in range(-3, 4):
            line((t * 16 - 8, -56), (t * 16 - 8, 40), GRID, zoom)
            line((-56, t * 16 - 8), (40, t * 16 - 8), GRID, zoom)
    train = kind.startswith("train")
    if train:  # ballast and the two rails (gauge 3.2 units), across the track direction (-dy, dx) normalised
        n = (dx * dx + dy * dy) ** 0.5
        px, py = -dy / n, dx / n
        for off, fill, wd in ((0, BALLAST, 7 * zoom), (1.6, RAIL, max(1, zoom // 2)), (-1.6, RAIL, max(1, zoom // 2))):
            line((-dx * 40 + px * off, -dy * 40 + py * off), (dx * 40 + px * off, dy * 40 + py * off), fill, wd)
    line((-dx * 24, -dy * 24), (dx * 24, dy * 24), (200, 60, 60, 255), zoom)
    origin = TRAIN_ORIGIN if train else ROAD_ORIGIN if road else SHIP_ORIGIN
    sp, xo, yo = draw_sprite(d)
    steps = sorted((8, 0, -8) if train else (0,), key=lambda st: (st * (dx + dy), st * (dx - dy)))
    for st in steps:  # back to front: the vehicle further north first
        ox, oy = remap(origin[d][0] + dx * st, origin[d][1] + dy * st)
        im.alpha_composite(sp, (vx + ox * zoom + xo, vy + oy * zoom + yo))
    dr.line([(vx - 3 * zoom, vy), (vx + 3 * zoom, vy)], fill=(255, 40, 40, 255), width=max(1, zoom // 2))
    dr.line([(vx, vy - 3 * zoom), (vx, vy + 3 * zoom)], fill=(255, 40, 40, 255), width=max(1, zoom // 2))
    return im


def main():
    render_dir, out, zoom = sys.argv[1], sys.argv[2], int(sys.argv[3])
    specs = sys.argv[4:] or ["tanker:ref/ships:3669", "cargo:ref/ships:3677", "ferry:ref/ships:3685",
                             "hover:ref/ships:3693", "toycargo:ref/ships_toyland:401", "toyferry:ref/ships_toyland:409"]
    veh_dir = os.path.join(render_dir, "vehicles")
    meta = json.load(open(os.path.join(veh_dir, "meta.json")))
    rows = []
    for spec in specs:
        name, ref_dir, first, *kind = spec.split(":")
        kind = kind[0] if kind else "ship"
        n_spr = 4 if kind == "train4" else 8
        if f"{name}_d0_z{zoom}" not in meta:
            continue

        def ours(d):
            im, x, y, cc = pv.vehicle_sprite(veh_dir, name, d % n_spr, zoom, meta)
            return tint(im, cc), x, y

        has_ref = ref_dir != "-" and os.path.exists(os.path.join(ref_dir, "meta.json"))
        ref_meta = json.load(open(os.path.join(ref_dir, "meta.json"))) if has_ref else {}

        def ref(d):
            n = str(int(first) + d % n_spr)
            im = Image.open(os.path.join(ref_dir, f"{n}.png")).convert("RGBA")
            im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
            return im, ref_meta[n]["x"] * zoom, ref_meta[n]["y"] * zoom
        rows.append([cell(zoom, ours, d, kind) for d in range(8)])
        if has_ref:
            rows.append([cell(zoom, ref, d, kind) for d in range(8)])
    cw = max(im.width for row in rows for im in row)
    ch = max(im.height for row in rows for im in row)
    sheet = Image.new("RGBA", (cw * 8, ch * len(rows)))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            sheet.paste(im, (c * cw, r * ch))
    sheet.save(out)


if __name__ == "__main__":
    main()
