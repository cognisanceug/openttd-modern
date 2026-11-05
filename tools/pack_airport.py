"""Packing of airports, docks, buoys and the oil rig (render_airports.py) for pack_grf.py.

Building sprites (b<name>, rig<sprite>) carry their cast shadow and are cropped
with the bounding box origin at canvas (47z, 136z); ground sprites (g<name>) are
the flat tile with the parts standing on it, origin (47z, 56z) at the north
corner. The grass halves over the apron (Action 5 AIRPORTS 13/14) take their
alpha from the texture, cut to the tile by the mask pass. Recolour masks mark
company colour.

Blocks:
  2633, 2635-2691   heliport, airport grounds and buildings, fences, windsock and radar frames
                    (2634, the apron concrete, is packed with the infrastructure)
  2096-2105         oil rig slices and construction stages (2099 is unused and stays empty)
  2727-2732         docks
  693               buoy (also the build-buoy toolbar icon, as in the original)
  AIRPORTS 0-14     tarmac, runway along y, hangars facing S, W, N, E, raised helipad, grass halves
  OTTD_GUI 86       helipad marking
"""

import os

from PIL import Image

from pack_industry import COMPANY_INDEX, ZOOMS, building_sprite, ground_sprite


# Sprites rendered from the tile's north corner although the game draws them at this bounding
# box origin (the hangar fronts reach 14 units back from it, beyond the building canvas).
BOX_ORIGIN = {name: (14, 0) for name in ("b2655", "b2657", "bx6", "bx8", "bx10", "bx11")}


def blank():
    return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0, Image.new("L", (1, 1), 0)


def overlay_ground_sprite(render_dir, name, zoom):
    """Tile overlay with its own alpha (grass half), cut to the tile, origin at the north corner."""
    d = os.path.join(render_dir, f"z{zoom}")
    im = Image.open(os.path.join(d, f"{name}_color.png")).convert("RGBA")
    cut = Image.open(os.path.join(d, f"{name}_mask.png")).convert("RGBA").getchannel("A").point(
        lambda a: 255 if a >= 128 else 0)
    alpha = Image.composite(im.getchannel("A"), Image.new("L", im.size, 0), cut)
    im.putalpha(alpha.point(lambda v: v if v >= 4 else 0))
    box = im.getchannel("A").getbbox()
    if box is None:
        return blank()
    return im.crop(box), box[0] - 47 * zoom, box[1] - 56 * zoom, Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)


def airport_blocks(render_dir, gfx_dir, sheet_block):
    d = os.path.join(render_dir, "airports")
    have = {n.split("_")[0] for n in os.listdir(os.path.join(d, "z1"))}

    def sprite(name, z):
        if name is None:
            return blank()
        if name in ("gx13", "gx14"):
            return overlay_ground_sprite(d, name, z)
        if os.path.exists(os.path.join(d, f"z{z}", f"{name}_overlay.png")):
            im, x, y, mask = building_sprite(d, name, z)
            ox, oy = BOX_ORIGIN.get(name, (0, 0))
            return im, x - 2 * (oy - ox) * z, y - (ox + oy) * z, mask
        return ground_sprite(d, name, z)

    def named(n):
        for prefix in ("b", "g", "rig"):
            if f"{prefix}{n}" in have:
                return f"{prefix}{n}"
        return None

    blocks = [
        ("airport_heliport", "replace {name}(2633, {file})", [2633], [named(2633)]),
        ("airport", "replace {name}(2635, {file})", list(range(2635, 2692)), [named(n) for n in range(2635, 2692)]),
        ("oil_rig", "replace {name}(2096, {file})", list(range(2096, 2106)), [named(n) for n in range(2096, 2106)]),
        ("docks", "replace {name}(2727, {file})", list(range(2727, 2733)), [named(n) for n in range(2727, 2733)]),
        ("buoy", "replace {name}(693, {file})", [693], [named(693)]),
        ("airport_extra", "replacenew {name}(AIRPORTS, {file})", list(range(15)),
         [f"gx{k}" if k <= 5 or k >= 13 else f"bx{k}" for k in range(15)]),
        ("helipad", "replacenew {name}(OTTD_GUI, {file}, 86)", [86], ["bgui86"]),
    ]
    out = []
    for name, header, labels, names in blocks:
        missing = [lab for lab, n in zip(labels, names) if n is None and lab != 2099]
        assert not missing, (name, missing)
        out.append(sheet_block(name, header, [f"{lab} {n}" for lab, n in zip(labels, names)],
                               {z: [sprite(n, z) for n in names] for z in ZOOMS}, gfx_dir, mask_index=COMPANY_INDEX))
    return out
