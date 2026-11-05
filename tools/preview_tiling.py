#!/usr/bin/env python3
"""Lay flat ground sprites out as a large isometric field, the way the game picks them.

Repetition across many tiles only shows on a big area, which test maps rarely
have, so this mosaic stands in for it. Variants are chosen like OpenTTD does:
rocky land by TileHash bit 0 (with the second rocky set enabled), rough land
by TileHash bits 0-2 through _landscape_clear_sprites_rough, farm fields by a
per-field stage.

Usage: preview_tiling.py <render/ground> <ref/ground> <out.png> <layout> [zoom] [tiles]
  layout: rocky | rough | bare | grass13 | grass23 | grass | mixed | fields
  zoom 1, 2 or 4 (default 4); tiles per side (default 12)
"""

import json
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pack_grf import ground_sprite  # noqa: E402

ROUGH_TABLE = (4000, 4019, 4020, 4021, 4022, 4000, 4019, 4020)
FIRST = {"bare": 3924, "grass13": 3943, "grass23": 3962, "grass": 3981}


def tile_hash(tx, ty):
    """TileHash() from tile_map.h, called with pixel coordinates (tile * 16)."""
    x, y = tx * 16, ty * 16
    h = x >> 4
    h ^= x >> 6
    h ^= y >> 4
    h -= y >> 6
    return h & 0xFFFFFFFF


def pick(layout, tx, ty, n):
    if layout == "rocky":
        return 4042 if tile_hash(tx, ty) & 1 else 4023
    if layout == "rough":
        return ROUGH_TABLE[tile_hash(tx, ty) & 7]
    if layout in FIRST:
        return FIRST[layout]
    if layout == "fields":
        # 3x3 fields, each with its own growth stage.
        return 4126 + 19 * (((tx // 4) * 5 + (ty // 4) * 3) % 9)
    # mixed: bands of grass, rough, rocky
    band = (tx + ty) * 3 // (2 * n)
    return [3981, ROUGH_TABLE[tile_hash(tx, ty) & 7], 4042 if tile_hash(tx, ty) & 1 else 4023][band % 3]


def main():
    ground_dir, ref_dir, out = sys.argv[1:4]
    layout = sys.argv[4]
    zoom = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    n = int(sys.argv[6]) if len(sys.argv) > 6 else 12
    meta = json.load(open(os.path.join(ref_dir, "meta.json")))
    cache = {}
    w, h = n * 64 * zoom, n * 32 * zoom + 32 * zoom
    img = Image.new("RGBA", (w, h), (40, 40, 40, 255))
    for tx in range(n):
        for ty in range(n):
            s = pick(layout, tx, ty, n)
            if s not in cache:
                cache[s] = ground_sprite(ground_dir, s, zoom, meta[str(s)])
            im, xo, yo = cache[s]
            sx = w // 2 + (ty - tx) * 32 * zoom
            sy = (tx + ty) * 16 * zoom
            img.alpha_composite(im, (sx + xo, sy + yo))
    img.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
