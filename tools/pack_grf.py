#!/usr/bin/env python3
"""Pack rendered sprites into sprite sheets and an NML file, then compile the GRF.

Ground tiles (3924-4060: bare, 1/3 and 2/3 grass, grass, rough land with its
four flat variants, two rocky sets): colour from <sprite>_color.png, alpha from the
binary <sprite>_mask.png so neighbouring tiles meet without seams; crop box
and offsets are the OpenTTD 1x values times the zoom factor.

Water (same treatment as ground): open water 4061 and the 18 shore shapes as
an Action 5 COAST_TILES_DIAGONAL block (all 18, so OpenTTD uses only ours);
their crop box comes from the grass sprite with the same slope.
Rivers are defined as our own canal-feature items, because OpenGFX draws them
that way and a definition takes precedence over plain sprites: WF_RIVER_SLOPE
(flat water + slopes SE, NE, SW, NW) and WF_RIVERBANKS (60 bank pieces, alpha
from the rendered bank times the tile mask, cropped like overlays). Coast rocks are an overlay
(Action 5 OVERLAY_ROCKS from offset 95, 19 slopes) cropped to their visible
pixels, with the same drawing origin as the ground tiles.

Infrastructure: rails 1005-1036 (1005-1010 are overlays without ground, cut
like river banks), roads 1313-1350 and level crossings 1370-1381, all packed
like ground tiles with the crop box of the grass sprite on the same slope.
Track fences 1301-1308 are cropped like overlays.

Foundations: the 14 leveled foundations 990-1003 and the 90-sprite Action 5
FOUNDATIONS_SLOPES_HALFTILES block, cropped like overlays (fully empty
variants become a 1x1 transparent sprite).

Trees (all temperate bases 1576-1715, 0x6AD packed from the 0x63D renders): the cast shadow (<sprite>_shadow.png, shadow-catcher alpha)
is tinted and faded to the map study's soft shadow, the tree
(<sprite>_tree.png) is laid over it, and the result is cropped to its
bounding box. The drawing origin sits at canvas pixel (31z, 64z).

Each block gets an 8bpp fallback (DOS palette) plus 32bpp sprites at 1x, 2x, 4x.

Usage: pack_grf.py <ground-render-dir> <ref/ground> <trees-render-dir> <foundations-render-dir> <fences-render-dir> <nml-dir>
"""

import json
import os
import subprocess
import sys

from nml.palette import raw_palette_data
from PIL import Image

ZOOMS = (1, 2, 4)
GAP = 8
GROUND_ANCHOR_Y = 24
# (block name, first sprite, count); rough land includes its four flat variants 4019-4022.
GROUND_BLOCKS = (
    ("ground_bare", 3924, 19),
    ("ground_grass13", 3943, 19),
    ("ground_grass23", 3962, 19),
    ("ground_grass", 3981, 19),
    ("ground_rough", 4000, 23),
    ("ground_rocky", 4023, 38),
)
SPRITE_SLOPES = list(range(15)) + [0x1D, 0x17, 0x1B, 0x1E]
SHORE_SLOPES = (0x17, 1, 2, 3, 4, 0x1B, 6, 7, 8, 9, 0x1D, 11, 12, 13, 14, 0x1E, 5, 10)
RIVER_SLOPES = (6, 12, 3, 9)
# (block name, NML block header with {file}, [(rendered name, slope)])
WATER_BLOCKS = (
    ("water_flat", "replace {name}(4061, {file})", [(4061, 0)]),
    ("water_shore", "replacenew {name}(COAST_TILES_DIAGONAL, {file})", [(f"shore{i}", s) for i, s in enumerate(SHORE_SLOPES)]),
)
BANK_SLOPES = (0, 6, 12, 3, 9)  # bank variants: flat, SE, NE, SW, NW
RAIL_SLOPES = {12: 8, 13: 4, 14: 1, 15: 2, 16: 14, 17: 7, 18: 11, 19: 13, 20: 12, 21: 6, 22: 3, 23: 9}
ROAD_SLOPES = {11: 12, 12: 6, 13: 3, 14: 9}
COAST_ROCKS_OFFSET = 95  # SPR_OVERLAY_ROCKS_WATER_COAST - SPR_OVERLAY_ROCKS_BASE
# (block name, first sprite, first rendered sprite)
TREE_BLOCKS = tuple((f"tree_{b:x}", b, 1597 if b == 0x6AD else b) for b in range(0x628, 0x6AD + 1, 7))
TREE_ANCHOR_Y = 64
SHADOW_RGB = (24, 40, 34)
SHADOW_ALPHA = 0.22
# DOS palette indices safe for plain colour: no transparency (0), company colours
# (198-205) or animated/special colours (215-255).
SAFE_INDICES = [i for i in range(1, 215) if not 198 <= i <= 205]


def to_8bpp(rgba):
    """Quantize an RGBA sheet to the DOS palette (no dithering); alpha < 128 -> index 0."""
    dos = raw_palette_data[0]
    lookup = Image.new("P", (1, 1))
    flat = []
    for i in SAFE_INDICES:
        flat += dos[i * 3:i * 3 + 3]
    lookup.putpalette(flat + flat[:3] * (256 - len(SAFE_INDICES)))
    q = rgba.convert("RGB").quantize(palette=lookup, dither=Image.Dither.NONE)
    alpha = rgba.getchannel("A").load()
    src = q.load()
    out = Image.new("P", rgba.size, 0)
    out.putpalette(dos)
    dst = out.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            if alpha[x, y] >= 128:
                dst[x, y] = SAFE_INDICES[src[x, y]]
    return out


def ground_sprite(render_dir, sprite, zoom, ref):
    size = 64 * zoom
    color = Image.open(os.path.join(render_dir, f"z{zoom}", f"{sprite}_color.png")).convert("RGBA")
    mask = Image.open(os.path.join(render_dir, f"z{zoom}", f"{sprite}_mask.png")).convert("RGBA").getchannel("A")
    alpha = mask.point(lambda a: 255 if a >= 128 else 0)
    color.putalpha(alpha)
    top = GROUND_ANCHOR_Y * zoom + zoom * ref["y"]
    h = zoom * (ref["h"] + 1) - 1
    box = (0, top, size, top + h)
    assert alpha.getbbox() == box, (sprite, zoom, alpha.getbbox(), box)
    return color.crop(box), zoom * ref["x"], zoom * ref["y"]


def overlay_sprite(render_dir, name, zoom):
    im = Image.open(os.path.join(render_dir, f"z{zoom}", f"{name}_overlay.png")).convert("RGBA")
    a = im.getchannel("A").point(lambda v: v if v >= 4 else 0)
    im.putalpha(a)
    box = a.getbbox()
    if box is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0
    left, top, right, bottom = box
    return im.crop(box), left - 31 * zoom, top - GROUND_ANCHOR_Y * zoom


def bank_sprite(render_dir, name, slope, zoom):
    """River bank piece: rendered alpha cut by the binary tile mask, cropped to visible pixels."""
    im = Image.open(os.path.join(render_dir, f"z{zoom}", f"{name}_color.png")).convert("RGBA")
    mask = Image.open(os.path.join(render_dir, f"z{zoom}", f"{name}_mask.png")).convert("RGBA").getchannel("A")
    cut = Image.eval(mask, lambda a: 255 if a >= 128 else 0)
    alpha = Image.composite(im.getchannel("A"), Image.new("L", im.size, 0), cut)
    im.putalpha(alpha.point(lambda v: v if v >= 4 else 0))
    box = im.getchannel("A").getbbox()
    if box is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0
    return im.crop(box), box[0] - 31 * zoom, box[1] - GROUND_ANCHOR_Y * zoom


def tree_sprite(render_dir, sprite, zoom):
    tree = Image.open(os.path.join(render_dir, f"z{zoom}", f"{sprite}_tree.png")).convert("RGBA")
    catcher = Image.open(os.path.join(render_dir, f"z{zoom}", f"{sprite}_shadow.png")).convert("RGBA")
    shade = catcher.getchannel("A").point(lambda a: round(a * SHADOW_ALPHA))
    out = Image.new("RGBA", tree.size, SHADOW_RGB + (0,))
    out.putalpha(shade)
    out.alpha_composite(tree)
    # Drop near-invisible fringe so the crop stays tight.
    a = out.getchannel("A").point(lambda v: v if v >= 4 else 0)
    out.putalpha(a)
    left, top, right, bottom = a.getbbox()
    return out.crop((left, top, right, bottom)), left - 31 * zoom, top - TREE_ANCHOR_Y * zoom


def sheet_block(name, header, labels, sprites_by_zoom, gfx_dir):
    """Write sheets for one replace block; returns NML text.

    header is the NML block head with {name} and {file} placeholders, labels
    the comment per sprite.
    """
    zoom_const = {1: "ZOOM_LEVEL_NORMAL", 2: "ZOOM_LEVEL_IN_2X", 4: "ZOOM_LEVEL_IN_4X"}
    parts = []
    for zoom in ZOOMS:
        sprites = sprites_by_zoom[zoom]
        cell = max(im.width for im, _, _ in sprites) + GAP
        sheet = Image.new("RGBA", (cell * len(sprites), max(im.height for im, _, _ in sprites)), (0, 0, 0, 0))
        lines = []
        for k, (im, xo, yo) in enumerate(sprites):
            sheet.paste(im, (k * cell, 0))
            lines.append(f"    [{k * cell:5d}, 0, {im.width:3d}, {im.height:3d}, {xo:4d}, {yo:4d}]  // {labels[k]}")
        sheet.save(os.path.join(gfx_dir, f"{name}_z{zoom}.png"))
        if zoom == 1:
            to_8bpp(sheet).save(os.path.join(gfx_dir, f"{name}_z1_8bpp.png"))
            head = header.format(name=name, file=f'"gfx/{name}_z1_8bpp.png"')
            parts += [head + " {", *lines, "}", ""]
        parts += [f'alternative_sprites({name}, {zoom_const[zoom]}, BIT_DEPTH_32BPP, "gfx/{name}_z{zoom}.png") {{',
                  *lines, "}", ""]
    return "\n".join(parts)


def main():
    ground_dir, ref_dir, trees_dir, found_dir, fence_dir, nml_dir = sys.argv[1:7]
    meta = json.load(open(os.path.join(ref_dir, "meta.json")))
    gfx_dir = os.path.join(nml_dir, "gfx")
    os.makedirs(gfx_dir, exist_ok=True)

    nml = [
        "// Generated by tools/pack_grf.py - do not edit.",
        "grf {",
        '    grfid: "RV\\4D\\01";',
        "    name: string(STR_GRF_NAME);",
        "    desc: string(STR_GRF_DESC);",
        "    version: 2;",
        "    min_compatible_version: 1;",
        "}",
        "",
    ]
    for name, first, count in GROUND_BLOCKS:
        tiles = {z: [ground_sprite(ground_dir, first + k, z, meta[str(first + k)]) for k in range(count)]
                 for z in ZOOMS}
        nml.append(sheet_block(name, f"replace {{name}}({first}, {{file}})",
                               [first + k for k in range(count)], tiles, gfx_dir))
    for name, header, items in WATER_BLOCKS:
        refs = [meta[str(3981 + SPRITE_SLOPES.index(slope))] for _, slope in items]
        tiles = {z: [ground_sprite(ground_dir, n, z, ref) for (n, _), ref in zip(items, refs)] for z in ZOOMS}
        nml.append(sheet_block(name, header, [n for n, _ in items], tiles, gfx_dir))
    # Rivers: our own canal-feature definitions replace OpenGFX's.
    slope_items = [(4061, 0)] + [(f"river{i}", sl) for i, sl in enumerate(RIVER_SLOPES)]
    tiles = {z: [ground_sprite(ground_dir, n, z, meta[str(3981 + SPRITE_SLOPES.index(sl))]) for n, sl in slope_items]
             for z in ZOOMS}
    nml.append(sheet_block("river_slopes", "spriteset({name}, {file})", [n for n, _ in slope_items], tiles, gfx_dir))
    nml.append("item(FEAT_CANALS, river_slope_item, WF_RIVER_SLOPE) {\n"
               "    property { graphic_flags: 1; }  // first sprite is flat water\n"
               "    graphics { river_slopes; }\n}\n")
    banks = [(f"bank{v * 12 + k}", sl) for v, sl in enumerate(BANK_SLOPES) for k in range(12)]
    pieces = {z: [bank_sprite(ground_dir, n, sl, z) for n, sl in banks] for z in ZOOMS}
    nml.append(sheet_block("river_banks", "spriteset({name}, {file})", [n for n, _ in banks], pieces, gfx_dir))
    nml.append("item(FEAT_CANALS, river_bank_item, WF_RIVERBANKS) {\n"
               "    graphics { river_banks; }\n}\n")
    names = [f"coastrock{k}" for k in range(len(SPRITE_SLOPES))]
    rocks = {z: [overlay_sprite(ground_dir, n, z) for n in names] for z in ZOOMS}
    nml.append(sheet_block("water_coast_rocks", f"replacenew {{name}}(OVERLAY_ROCKS, {{file}}, {COAST_ROCKS_OFFSET})",
                           names, rocks, gfx_dir))
    grass_meta = lambda slope: meta[str(3981 + SPRITE_SLOPES.index(slope))]  # noqa: E731
    rails = {z: [bank_sprite(ground_dir, f"rail{n}", 0, z) for n in range(1005, 1011)]
             + [ground_sprite(ground_dir, f"rail{n}", z, grass_meta(RAIL_SLOPES.get(n - 1011, 0)))
                for n in range(1011, 1037)] for z in ZOOMS}
    nml.append(sheet_block("rails", "replace {name}(1005, {file})", list(range(1005, 1037)), rails, gfx_dir))
    roads = {z: [ground_sprite(ground_dir, f"road{base + k}", z, grass_meta(ROAD_SLOPES.get(k, 0)))
                 for base in (1313, 1332) for k in range(19)] for z in ZOOMS}
    nml.append(sheet_block("roads", "replace {name}(1313, {file})", list(range(1313, 1351)), roads, gfx_dir))
    crossings = {z: [ground_sprite(ground_dir, f"cross{n}", z, grass_meta(0)) for n in range(1370, 1382)]
                 for z in ZOOMS}
    nml.append(sheet_block("level_crossings", "replace {name}(1370, {file})", list(range(1370, 1382)),
                           crossings, gfx_dir))
    fences = {z: [overlay_sprite(fence_dir, f"fence{n}", z) for n in range(1301, 1309)] for z in ZOOMS}
    nml.append(sheet_block("track_fences", "replace {name}(1301, {file})", list(range(1301, 1309)), fences, gfx_dir))
    for name, header, names in (
        ("foundations_base", "replace {name}(990, {file})", [f"found_base{t}" for t in range(1, 15)]),
        ("foundations", "replacenew {name}(FOUNDATIONS_SLOPES_HALFTILES, {file})", [f"found{k}" for k in range(90)]),
    ):
        found = {z: [overlay_sprite(found_dir, n, z) for n in names] for z in ZOOMS}
        nml.append(sheet_block(name, header, names, found, gfx_dir))
    for name, first, rendered in TREE_BLOCKS:
        trees = {z: [tree_sprite(trees_dir, rendered + g, z) for g in range(7)] for z in ZOOMS}
        nml.append(sheet_block(name, f"replace {{name}}({first}, {{file}})",
                               [first + g for g in range(7)], trees, gfx_dir))
    open(os.path.join(nml_dir, "modern_terrain.nml"), "w").write("\n".join(nml))

    os.makedirs(os.path.join(nml_dir, "lang"), exist_ok=True)
    open(os.path.join(nml_dir, "lang", "english.lng"), "w").write(
        "##grflangid 0x01\n"
        "STR_GRF_NAME :Modern Terrain\n"
        "STR_GRF_DESC :32bpp temperate ground, water and shores, foundations, trees, rails and roads rendered in Blender. Licence: GPL v2.\n"
    )
    nmlc = os.path.join(os.path.dirname(sys.executable), "nmlc")
    subprocess.run([nmlc, "-c", "--grf", "modern_terrain.grf", "modern_terrain.nml"], cwd=nml_dir, check=True)


if __name__ == "__main__":
    main()
