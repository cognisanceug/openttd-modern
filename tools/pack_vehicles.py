"""Packing of vehicles (blender/render_vehicles.py) for pack_grf.py.

A vehicle sprite is the rendered model cropped to its pixels; its offset is the
crop box minus the canvas pixel of the sprite origin, RemapCoords(pos +
bounds.origin), that render_vehicles.py writes to meta.json per direction and
zoom. The recolour mask marks company colour.

Ships: the four original sprite sets are base sprites 0xE55 + Direction
(table _ship_sprites in ship_cmd.cpp: image 1 tanker 0xE55, 0 cargo ship
0xE5D, 2 ferry 0xE65, 3 hovercraft 0xE6D). Toyland's base graphics replace
0xE5D-0xE6C with its own cargo ship and ferry (table/landscape_sprite.h), so a
climate block replaces those again with the toyland models.
"""

import json
import os

from PIL import Image

COMPANY_INDEX = 202
ZOOMS = (1, 2, 4)

SHIPS = [("tanker", 0xE55), ("cargo", 0xE5D), ("ferry", 0xE65), ("hover", 0xE6D)]
TOYLAND_SHIPS = [("toycargo", 0xE5D), ("toyferry", 0xE65)]


def vehicle_sprite(veh_dir, name, d, zoom, meta=None):
    """(im, x, y, recolour mask) of one direction of a vehicle."""
    if meta is None:
        meta = json.load(open(os.path.join(veh_dir, "meta.json")))
    zdir = os.path.join(veh_dir, f"z{zoom}")
    im = Image.open(os.path.join(zdir, f"{name}_d{d}.png")).convert("RGBA")
    a = im.getchannel("A").point(lambda v: v if v >= 4 else 0)
    im.putalpha(a)
    box = a.getbbox()
    cc = Image.open(os.path.join(zdir, f"{name}_d{d}_cc.png")).convert("L").point(lambda v: 255 if v >= 128 else 0)
    cc = Image.composite(cc, Image.new("L", cc.size, 0), a.point(lambda v: 255 if v >= 128 else 0))
    ox, oy = meta[f"{name}_d{d}_z{zoom}"]
    return im.crop(box), box[0] - ox, box[1] - oy, cc.crop(box)


def ship_blocks(render_dir, gfx_dir, sheet_block):
    veh_dir = os.path.join(render_dir, "vehicles")
    meta = json.load(open(os.path.join(veh_dir, "meta.json")))

    def block(prefix, ships):
        out = []
        for name, first in ships:
            sprites = {z: [vehicle_sprite(veh_dir, name, d, z, meta) for d in range(8)] for z in ZOOMS}
            out.append(sheet_block(f"{prefix}{name}", "replace {name}(%d, {file})" % first,
                                   [f"{name} dir {d}" for d in range(8)], sprites, gfx_dir, mask_index=COMPANY_INDEX))
        return out
    return block("ship_", SHIPS) + ["if (climate == CLIMATE_TOYLAND) {\n" + "\n".join(block("ship_", TOYLAND_SHIPS)) + "}\n"]
