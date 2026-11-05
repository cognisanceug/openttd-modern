#!/usr/bin/env python3
"""Preview vehicle sprites placed as the game draws them, next to the OpenGFX originals.

Usage: preview_vehicles.py <render-dir> <out.png> <zoom> [name:ref_dir:first_sprite ...]

Per vehicle two rows of 8 directions over a sea of tiles: our sprite (packed as
pack_vehicles.py does) and the OpenGFX sprite scaled to the zoom. The vehicle
sits on a tile centre, the red line is its path, the cross its position.
"""

import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack_vehicles as pv  # noqa: E402

SHIP_ORIGIN = [(-3, -3), (-16, -3), (-3, -3), (-3, -16), (-3, -3), (-16, -3), (-3, -3), (-3, -16)]
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


def cell(zoom, draw_sprite, d):
    w, h = 150 * zoom, 96 * zoom
    im = Image.new("RGBA", (w, h), WATER)
    dr = ImageDraw.Draw(im)
    vx, vy = w // 2, 52 * zoom
    for t in range(-3, 4):
        for a, b in (((t * 16 - 8, -56), (t * 16 - 8, 40)), ((-56, t * 16 - 8), (40, t * 16 - 8))):
            p, q = remap(*a), remap(*b)
            dr.line([(vx + p[0] * zoom, vy + p[1] * zoom), (vx + q[0] * zoom, vy + q[1] * zoom)], fill=GRID, width=zoom)
    dx, dy = DIRS[d]
    p, q = remap(-dx * 24, -dy * 24), remap(dx * 24, dy * 24)
    dr.line([(vx + p[0] * zoom, vy + p[1] * zoom), (vx + q[0] * zoom, vy + q[1] * zoom)], fill=(200, 60, 60, 255), width=zoom)
    sp, xo, yo = draw_sprite(d)
    ox, oy = remap(*SHIP_ORIGIN[d])
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
        name, ref_dir, first = spec.split(":")
        if f"{name}_d0_z{zoom}" not in meta:
            continue

        def ours(d):
            im, x, y, cc = pv.vehicle_sprite(veh_dir, name, d, zoom, meta)
            return tint(im, cc), x, y

        ref_meta = json.load(open(os.path.join(ref_dir, "meta.json")))

        def ref(d):
            n = str(int(first) + d)
            im = Image.open(os.path.join(ref_dir, f"{n}.png")).convert("RGBA")
            im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
            return im, ref_meta[n]["x"] * zoom, ref_meta[n]["y"] * zoom
        rows.append([cell(zoom, ours, d) for d in range(8)])
        rows.append([cell(zoom, ref, d) for d in range(8)])
    cw, ch = rows[0][0].size
    sheet = Image.new("RGBA", (cw * 8, ch * len(rows)))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            sheet.paste(im, (c * cw, r * ch))
    sheet.save(out)


if __name__ == "__main__":
    main()
