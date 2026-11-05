#!/usr/bin/env python3
"""Compose rendered sprites into a preview sheet, for parts the game cannot show (trams).

Each tile is a list of layers "kind:name"; kinds and where they live:
  ground   render/ground/z<zoom>/<name>_color.png cut by <name>_mask.png (N corner at 32z, 24z)
  overlay  render/ground/z<zoom>/<name>_color.png, alpha as rendered (N corner at 32z, 24z)
  cat      render/catenary/z<zoom>/cat<name>_overlay.png (N corner at 48z, 72z)
  <dir>    render/<dir>/z<zoom>/<name>_overlay.png with the N corner given as  <dir>@x,y:name (1x px)
Tiles are separated by ";" on the command line, layers by "+".

Usage: preview_tiles.py <render-dir> <out.png> <zoom> "ground:tram27+cat:tram_84+cat:tram_56;..."
"""

import os
import sys

from PIL import Image

ANCHORS = {"ground": (32, 24), "overlay": (32, 24), "cat": (48, 72)}
BG = (122, 170, 92, 255)


def layer(render_dir, spec, zoom):
    kind, name = spec.split(":", 1)
    if "@" in kind:
        kind, at = kind.split("@")
        anchor = tuple(float(v) for v in at.split(","))
    else:
        anchor = ANCHORS[kind]
    if kind in ("ground", "overlay"):
        d = os.path.join(render_dir, "ground", f"z{zoom}")
        im = Image.open(os.path.join(d, f"{name}_color.png")).convert("RGBA")
        if kind == "ground":
            mask = Image.open(os.path.join(d, f"{name}_mask.png")).convert("RGBA").getchannel("A")
            im.putalpha(mask.point(lambda a: 255 if a >= 128 else 0))
    elif kind == "cat":
        im = Image.open(os.path.join(render_dir, "catenary", f"z{zoom}", f"cat{name}_overlay.png")).convert("RGBA")
    else:
        fname = name if name.endswith(".png") else f"{name}_overlay.png"
        im = Image.open(os.path.join(render_dir, kind, f"z{zoom}", fname)).convert("RGBA")
    return im, (round(anchor[0] * zoom), round(anchor[1] * zoom))


def main():
    render_dir, out, zoom, tiles = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4].split(";")
    cell_w, cell_h = 96 * zoom, 112 * zoom
    sheet = Image.new("RGBA", (cell_w * len(tiles), cell_h), BG)
    for i, tile in enumerate(tiles):
        corner = (i * cell_w + cell_w // 2, 72 * zoom)
        for spec in tile.split("+"):
            im, anchor = layer(render_dir, spec, zoom)
            top = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
            top.paste(im, (corner[0] - anchor[0], corner[1] - anchor[1]))
            sheet.alpha_composite(top)
    sheet.save(out)


if __name__ == "__main__":
    main()
