"""Packing of objects and industries of all climates (render_objects.py, render_industries.py) for pack_grf.py.

Building sprites are the rendered building with its cast shadow under it,
cropped; origin (47z, 136z) is the bounding box origin. Ground sprites are
the flat tile cut by its mask with the parts standing in the ground laid
over it; origin (47z, 56z) is the tile's north corner. Recolour masks mark
company colour (objects) or the industry's random colour.
"""

import os

from PIL import Image

SHADOW_RGB = (24, 40, 34)
COMPANY_INDEX = 202  # recolour masks mark the company-colour range (company or industry random colour)
SHADOW_ALPHA = 0.22
ZOOMS = (1, 2, 4)


def _solid_mask(path, alpha):
    m = Image.open(path).convert("RGB").convert("L").point(lambda v: 255 if v >= 128 else 0)
    return Image.composite(m, Image.new("L", m.size, 0), alpha.point(lambda v: 255 if v >= 128 else 0))


def building_sprite(render_dir, name, zoom):
    """(im, x, y, recolour mask) of a building sprite with its shadow under it."""
    d = os.path.join(render_dir, f"z{zoom}")
    building = Image.open(os.path.join(d, f"{name}_overlay.png")).convert("RGBA")
    out = Image.new("RGBA", building.size, SHADOW_RGB + (0,))
    shadow = os.path.join(d, f"{name}_shadow.png")
    if os.path.exists(shadow):
        out.putalpha(Image.open(shadow).getchannel("A").point(lambda a: round(a * SHADOW_ALPHA)))
    out.alpha_composite(building)
    a = out.getchannel("A").point(lambda v: v if v >= 4 else 0)
    out.putalpha(a)
    box = a.getbbox()
    if box is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0, Image.new("L", (1, 1), 0)
    cc = os.path.join(d, f"{name}_cc.png")
    mask = _solid_mask(cc, building.getchannel("A")) if os.path.exists(cc) else Image.new("L", building.size, 0)
    return out.crop(box), box[0] - 47 * zoom, box[1] - 136 * zoom, mask.crop(box)


def ground_sprite(render_dir, name, zoom):
    """(im, x, y, recolour mask) of a flat ground tile with the parts standing in it."""
    d = os.path.join(render_dir, f"z{zoom}")
    tile = Image.open(os.path.join(d, f"{name}_color.png")).convert("RGBA")
    tile.putalpha(Image.open(os.path.join(d, f"{name}_mask.png")).convert("RGBA").getchannel("A")
                  .point(lambda a: 255 if a >= 128 else 0))
    mask = Image.new("L", tile.size, 0)
    props = os.path.join(d, f"{name}_gprops.png")
    if os.path.exists(props):
        p = Image.open(props).convert("RGBA")
        tile.alpha_composite(p)
        cc = os.path.join(d, f"{name}_gcc.png")
        if os.path.exists(cc):
            mask = _solid_mask(cc, p.getchannel("A"))
    box = tile.getchannel("A").getbbox()
    return tile.crop(box), box[0] - 47 * zoom, box[1] - 56 * zoom, mask.crop(box)


# Object sprites 2601-2632: 2601/2602/2632 are buildings, of the HQ sprites the
# building parts (rendered as o<sprite>_overlay) and the rest grounds.
OBJECT_BUILDINGS = {2601, 2602, 2612, 2614, 2616, 2619, 2621, 2623, 2626, 2628, 2630, 2632, 4790}


def object_blocks(render_dir, gfx_dir, sheet_block):
    obj_dir = os.path.join(render_dir, "objects")

    def sprite(n, z):
        if n in OBJECT_BUILDINGS:
            return building_sprite(obj_dir, f"o{n}", z)
        return ground_sprite(obj_dir, f"o{n}", z)
    out = [sheet_block("objects", "replace {name}(2601, {file})", list(range(2601, 2633)),
                       {z: [sprite(n, z) for n in range(2601, 2633)] for z in ZOOMS}, gfx_dir,
                       mask_index=COMPANY_INDEX)]
    out.append(sheet_block("owned_land", "replace {name}(4790, {file})", [4790],
                           {z: [sprite(4790, z)] for z in ZOOMS}, gfx_dir, mask_index=COMPANY_INDEX))
    return out


# Child sprites: (parent sprite, offset from the parent's top-left) as the draw procs add them
# (table/industry_land.h, industry_cmd.cpp). The transformer sparks (s<sprite>) are child sprites
# of 2054; the toyland ones (c<sprite>) are modelled at their reference offset (industry_toyland.CHILDREN).
COAL_PLANT_SPARKS = {2055: (11, 23), 2056: (11, 11), 2057: (14, 6), 2058: (13, 3), 2059: (18, 1), 2060: (15, 0)}
CHILDREN = {
    **{n: (2054, xy) for n, xy in COAL_PLANT_SPARKS.items()},
    4717: (4713, (0, 42)), 4718: (4713, (7, 0)), 4719: (4713, (50, 96)), 4720: (4713, (16, 100)),
    4747: (4745, (5, 86)), 4766: (4764, (6, 14)), 4767: (4764, (22, 24)),
    **{n: (4773, (8, 0)) for n in range(4775, 4780)},
    **{n: (4773, xy) for n, xy in zip(range(4780, 4784), ((22, 73), (17, 70), (14, 69), (10, 66)))},
    **{n: (4773, (8, 41)) for n in range(4784, 4790)},
}
# The plastic fountain's eight grounds are one render.
ALIASES = {n: 4721 for n in range(4722, 4729)}
# Variants of sprites a climate shares with temperate (render_industries.py --climate).
CLIMATES = (("arctic", "CLIMATE_ARCTIC"), ("tropic", "CLIMATE_TROPICAL"), ("toyland", "CLIMATE_TOYLAND"))


def _industry_runs(ind_dir, base_dir, gfx_dir, sheet_block, prefix):
    names = os.listdir(os.path.join(ind_dir, "z1"))
    builds = {int(n[1:].split("_")[0]) for n in names if n.startswith("b")}
    grounds = {int(n[1:].split("_")[0]) for n in names if n.startswith("g")}
    children = {int(n[1:].split("_")[0]) for n in names if n[0] in "sc"}
    aliases = {n for n, a in ALIASES.items() if a in grounds}

    def sprite(n, z):
        if n in builds:
            return building_sprite(ind_dir, f"b{n}", z)
        if n in grounds or n in aliases:
            return ground_sprite(ind_dir, f"g{ALIASES.get(n, n)}", z)
        name = f"s{n}" if n in COAL_PLANT_SPARKS else f"c{n}"
        im, x, y, mask = building_sprite(ind_dir, name, z)
        parent, (sx, sy) = CHILDREN[n]
        _, px, py, _ = building_sprite(base_dir, f"b{parent}", z)
        return im, x - px - sx * z, y - py - sy * z, mask

    ids = sorted(builds | grounds | children | aliases)
    runs = []
    for n in ids:
        if runs and n == runs[-1][-1] + 1:
            runs[-1].append(n)
        else:
            runs.append([n])
    return [sheet_block(f"{prefix}_{run[0]}", "replace {name}(%d, {file})" % run[0], run,
                        {z: [sprite(n, z) for n in run] for z in ZOOMS}, gfx_dir, mask_index=COMPANY_INDEX)
            for run in runs]


def industry_blocks(render_dir, gfx_dir, sheet_block):
    """Replace blocks for every run of consecutive industry sprites we rendered.

    The climate variants follow the unconditional blocks inside if (climate == ...),
    so they replace the temperate sprites only in their climate.
    """
    ind_dir = os.path.join(render_dir, "industries")
    out = _industry_runs(ind_dir, ind_dir, gfx_dir, sheet_block, "industry")
    for name, const in CLIMATES:
        cdir = os.path.join(render_dir, f"industries_{name}")
        if os.path.isdir(cdir):
            blocks = _industry_runs(cdir, ind_dir, gfx_dir, sheet_block, f"industry_{name}")
            out.append(f"if (climate == {const}) {{\n" + "\n".join(blocks) + "}\n")
    return out
