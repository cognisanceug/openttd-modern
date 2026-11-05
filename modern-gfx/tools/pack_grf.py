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

Farm fields 4126-4296 (nine stages, 19 slopes each) are packed like ground
tiles; their fences 4090-4125 (six types) like overlays. The GRF also sets
second_rocky_tileset, so rocky land alternates between the sets 4023 and 4042.
Snow (arctic) and desert (tropic) densities 4493-4568 come from render/snow and
render/desert and are replaced only in their climate. Toyland loads its own
ground into the same sprites 3924-4060 (table/landscape_sprite.h), so in toyland
an if-block replaces them again from render/toyland, together with the shores,
whose meadow band is the toyland grass. Everything else that shows grass and is drawn
in toyland too has a toyland variant (render/toyland, rendered with GFX_GRASS=toy), packed
in a second toyland if-block at the end so it wins over the temperate replacements:
see toyland_grass_blocks().

Signals: 1275-1290 (electric block signals) and the 240-sprite Action 5
PRE_SIGNAL_SEMAPHORE_PBS block, indexed like DrawSingleSignal(); slots the game
never uses get a 1x1 transparent sprite. Depots 1063-1068 and 1408-1413 carry a
company-colour mask: masked pixels get palette index 202 in the 32bpp mask
sheet (brightness comes from the rendered grey) and company colours in the
8bpp fallback. Concrete 2634 is packed like ground.

Foundations: the 14 leveled foundations 990-1003 and the 90-sprite Action 5
FOUNDATIONS_SLOPES_HALFTILES block, cropped like overlays (fully empty
variants become a 1x1 transparent sprite).

Trees (all 62 tree bases of all climates, 1576-2009): the cast shadow (<sprite>_shadow.png, shadow-catcher alpha)
is tinted and faded to the map study's soft shadow, the tree
(<sprite>_tree.png) is laid over it, and the result is cropped to its
bounding box. The drawing origin sits at canvas pixel (31z, 80z).

Water animation (tools/water_anim.py): open water, shores and river slopes
carry a mask of animated palette indices (dark water 245-249, glitter
250-254) on a ripple pattern, so the 32bpp-anim blitters keep OpenTTD's
palette animation; the rest of the water keeps its rendered colour.

Canals, locks, aqueducts and ship depots: see canal_blocks().

Each block gets an 8bpp fallback (DOS palette) plus 32bpp sprites at 1x, 2x, 4x.

Bridges 2437-2580 (rail and road) carry a structure recolour mask (index 75 in
the 70-79 range PALETTE_TO_STRUCT_* remaps) so every bridge type keeps its
colour. Tunnels 2365-2372 and 2389-2396: ground sprites are the slope tile with
the portal laid over it, front sprites are cropped overlays.

Stations: rail station parts 1069-1086, road stop bays 2692-2723 (floors
packed like ground, parts as overlays), drive-through stops (ROAD_STOPS),
road waypoints (ROAD_WAYPOINTS) and rail waypoints (OTTD_GUI 78-81), all with
company-colour masks.

Catenary: rail wires and pylons (CATENARY 0-35); trams: track overlays
(TRAMWAY 4-22), tram-only track (27-45), overhead wires front 56-75 and back
poles 84-94 with a company-colour band; tram stops 23-26, depots 49-54 and 113-118,
tunnel wires 80-83, bridge wires 95-106 and tram-only bridge decks 107-112 (tram_extra_blocks).

One-way road markers: Action 5 ONE_WAY_ROAD, drawn at the tile centre (oneway_block).

Town houses of all climates, 1420-1575, 4404-4492, 4569-4625, 4627-4676 and
4694-4698 (render_houses.py): buildings are the rendered house with its cast
shadow under it (and under that the house's own ground where it has one),
recolourable facades carry a structure recolour mask; grounds are the flat tile, with house parts laid over
it where the original draws the house in the ground sprite. The lift (1443) is
a child sprite placed relative to the top-left corner of the office block
sprite (1442), so its offsets are taken from that sprite's crop. 1438 and 1439 are
the church recolour sprites and are left out.

Monorail and maglev (guideway_blocks): tracks 1087-1118 / 1169-1200, crossings 1382-1405,
depots and stations 1145-1168 / 1227-1250 from the rail renders, tunnels 2373-2388 and
the bridge sprites only they use (2581-2592, 4324-4403).

Airports (heliport 2633, grounds and buildings 2635-2691, Action 5 AIRPORTS and the
OTTD_GUI helipad), docks 2727-2732, the buoy 693 and the oil rig 2096-2105: see
tools/pack_airport.py.

Usage: pack_grf.py <render-dir> <ref/ground> <nml-dir>
  (render-dir holds ground/, snow/, desert/, toyland/, trees/, foundations/, fences/, signals/, depots/, bridges/,
   tunnels/, stations/, catenary/, houses/, objects/, industries/, airports/, vehicles/)
"""

import json
import os
import subprocess
import sys

from nml.palette import raw_palette_data
from PIL import Image

import water_anim

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
# All tree bases of all climates: temperate 0x628-0x6A6, sub-arctic 0x6AD-0x716 (with snow from 0x6E5),
# sub-tropical 0x71D-0x794, toyland 0x79B-0x7D3.
TREE_BLOCKS = tuple((f"tree_{b:x}", b, b) for b in range(0x628, 0x7D3 + 1, 7))
TREE_ANCHOR_Y = 80
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


def overlay_sprite(render_dir, name, zoom, origin=(31, GROUND_ANCHOR_Y), cc=False):
    """Crop a rendered overlay to its visible pixels; origin is the sprite origin at 1x canvas scale.

    With cc, also returns the company-colour mask (L, 255 = recolour) cropped alike.
    """
    im = Image.open(os.path.join(render_dir, f"z{zoom}", f"{name}_overlay.png")).convert("RGBA")
    a = im.getchannel("A").point(lambda v: v if v >= 4 else 0)
    im.putalpha(a)
    box = a.getbbox()
    if box is None:
        empty = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        return (empty, 0, 0, Image.new("L", (1, 1), 0)) if cc else (empty, 0, 0)
    left, top = box[0], box[1]
    out = (im.crop(box), left - origin[0] * zoom, top - origin[1] * zoom)
    if not cc:
        return out
    mask = Image.open(os.path.join(render_dir, f"z{zoom}", f"{name}_cc.png")).convert("RGB").convert("L")
    mask = mask.point(lambda v: 255 if v >= 128 else 0)
    return out + (Image.composite(mask, Image.new("L", mask.size, 0), a.point(lambda v: 255 if v >= 128 else 0)).crop(box),)


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


def tunnel_ground_sprite(render_dir, sprite, zoom):
    """Tunnel ground sprite: the slope tile (cut by its mask) with the 3D portal parts laid over it."""
    d = os.path.join(render_dir, f"z{zoom}")
    tile = Image.open(os.path.join(d, f"tun{sprite}_ground_color.png")).convert("RGBA")
    mask = Image.open(os.path.join(d, f"tun{sprite}_ground_mask.png")).convert("RGBA").getchannel("A")
    tile.putalpha(mask.point(lambda a: 255 if a >= 128 else 0))
    tile.alpha_composite(Image.open(os.path.join(d, f"tun{sprite}_overlay.png")).convert("RGBA"))
    box = tile.getchannel("A").getbbox()
    return tile.crop(box), box[0] - 47 * zoom, box[1] - 56 * zoom


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
    if a.getbbox() is None:  # nothing left (the burst toyland balloon)
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0
    left, top, right, bottom = a.getbbox()
    return out.crop((left, top, right, bottom)), left - 31 * zoom, top - TREE_ANCHOR_Y * zoom


def house_sprite(render_dir, sprite, zoom, cc, base=False):
    """Building with its shadow under it, cropped; origin (47z, 136z). Returns (im, x, y, recolour mask).

    base: the house brings its own ground (b<sprite>_base.png), drawn under the shadow."""
    d = os.path.join(render_dir, f"z{zoom}")
    building = Image.open(os.path.join(d, f"b{sprite}_overlay.png")).convert("RGBA")
    catcher = Image.open(os.path.join(d, f"b{sprite}_shadow.png")).convert("RGBA")
    shadow = Image.new("RGBA", building.size, SHADOW_RGB + (0,))
    shadow.putalpha(catcher.getchannel("A").point(lambda a: round(a * SHADOW_ALPHA)))
    if base:
        out = Image.open(os.path.join(d, f"b{sprite}_base.png")).convert("RGBA")
        mask = Image.open(os.path.join(d, f"b{sprite}_basemask.png")).convert("RGBA").getchannel("A")
        out.putalpha(mask.point(lambda a: 255 if a >= 128 else 0))
        out.alpha_composite(shadow)
    else:
        out = shadow
    out.alpha_composite(building)
    a = out.getchannel("A").point(lambda v: v if v >= 4 else 0)
    out.putalpha(a)
    box = a.getbbox()
    mask = Image.new("L", building.size, 0)
    if cc:
        m = Image.open(os.path.join(d, f"b{sprite}_cc.png")).convert("RGB").convert("L").point(lambda v: 255 if v >= 128 else 0)
        solid = building.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
        mask = Image.composite(m, mask, solid)
    return out.crop(box), box[0] - 47 * zoom, box[1] - 136 * zoom, mask.crop(box)


def house_ground_sprite(render_dir, sprite, zoom):
    """Flat tile cut by its mask, with house parts standing in the ground laid over it; origin (47z, 56z)."""
    d = os.path.join(render_dir, f"z{zoom}")
    tile = Image.open(os.path.join(d, f"g{sprite}_color.png")).convert("RGBA")
    mask = Image.open(os.path.join(d, f"g{sprite}_mask.png")).convert("RGBA").getchannel("A")
    tile.putalpha(mask.point(lambda a: 255 if a >= 128 else 0))
    props = os.path.join(d, f"g{sprite}_overlay.png")
    if os.path.exists(props):
        tile.alpha_composite(Image.open(props).convert("RGBA"))
    box = tile.getchannel("A").getbbox()
    return tile.crop(box), box[0] - 47 * zoom, box[1] - 56 * zoom, Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)


def house_lift_sprite(render_dir, zoom, parent):
    """The lift cabin at the ground floor, offset from the parent sprite's top-left as AddChildSpriteScreen does."""
    im, x, y = overlay_sprite(render_dir, "l1443", zoom, origin=(47, 136))
    return im, x - parent[1] - 14 * zoom, y - parent[2] - 60 * zoom, Image.new("L", im.size, 0)


def house_blocks(house_dir, table, gfx_dir):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
    import house_specs as hs
    data = json.load(open(table))
    buildings, grounds = hs.building_jobs(data), hs.ground_jobs(data)
    empty = (Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0, Image.new("L", (1, 1), 0))
    out = []
    # Temperate and sub-arctic (1566-1569), then the houses of the other climates, which have sprite
    # numbers of their own (between them only the snow and desert grounds 4493-4568). 1438 and 1439
    # are the recolour sprites PALETTE_CHURCH_RED and _CREAM, so they stay as they are.
    for name, first, last in (("houses", 1420, 1437), ("houses_b", 1440, 1575), ("houses_late", 4404, 4492), ("houses_snow", 4569, 4625),
                              ("houses_toyland", 4627, 4676), ("houses_toyland2", 4694, 4698)):
        sprites = {}
        for z in ZOOMS:
            row = []
            for n in range(first, last + 1):
                if n in buildings:
                    row.append(house_sprite(house_dir, n, z, buildings[n]["rc"], bool(buildings[n]["base"])))
                elif n in grounds:
                    row.append(house_ground_sprite(house_dir, n, z))
                else:
                    row.append(empty)
            if first <= hs.LIFT_SPRITE <= last:
                row[hs.LIFT_SPRITE - first] = house_lift_sprite(house_dir, z, row[1442 - first])
            sprites[z] = row
        out.append(sheet_block(name, f"replace {{name}}({first}, {{file}})", list(range(first, last + 1)), sprites,
                               gfx_dir, mask_index=STRUCT_INDEX))
    return out


COMPANY_INDEX = 202  # middle of the company-colour range 198-205


STRUCT_INDEX = 75  # middle of the structure colour range 70-79 that PALETTE_TO_STRUCT_* recolour


def sheet_block(name, header, labels, sprites_by_zoom, gfx_dir, mask_index=COMPANY_INDEX):
    """Write sheets for one replace block; returns NML text.

    header is the NML block head with {name} and {file} placeholders, labels
    the comment per sprite. Sprites with a fourth element carry a mask: masked
    pixels get mask_index, or with mask_index=None the mask's own value
    (palette indices, e.g. the animated water colours).
    """
    zoom_const = {1: "ZOOM_LEVEL_NORMAL", 2: "ZOOM_LEVEL_IN_2X", 4: "ZOOM_LEVEL_IN_4X"}
    parts = []
    for zoom in ZOOMS:
        sprites = sprites_by_zoom[zoom]
        has_mask = len(sprites[0]) == 4
        cell = max(sp[0].width for sp in sprites) + GAP
        size = (cell * len(sprites), max(sp[0].height for sp in sprites))
        sheet = Image.new("RGBA", size, (0, 0, 0, 0))
        mask_sheet = Image.new("L", size, 0)
        lines = []
        for k, sp in enumerate(sprites):
            im, xo, yo = sp[:3]
            sheet.paste(im, (k * cell, 0))
            if has_mask:
                mask_sheet.paste(sp[3], (k * cell, 0))
            flags = ", ANIM" if mask_index is None else ""  # animated palette colours are intended
            lines.append(f"    [{k * cell:5d}, 0, {im.width:3d}, {im.height:3d}, {xo:4d}, {yo:4d}{flags}]  // {labels[k]}")
        sheet.save(os.path.join(gfx_dir, f"{name}_z{zoom}.png"))
        mask_arg = ""
        if has_mask:
            pal = Image.new("P", size, 0)
            pal.putpalette(raw_palette_data[0])
            if mask_index is None:
                pal.paste(mask_sheet)  # the mask holds the palette indices themselves
            else:
                pal.paste(mask_index, mask=mask_sheet)
            pal.save(os.path.join(gfx_dir, f"{name}_z{zoom}_mask.png"))
            mask_arg = f', "gfx/{name}_z{zoom}_mask.png"'
        if zoom == 1:
            eight = to_8bpp(sheet)
            if has_mask and mask_index is None:
                eight.paste(mask_sheet, mask=mask_sheet.point(lambda v: 255 if v else 0))
            elif has_mask:
                # Company colours in the 8bpp fallback, shaded by the rendered grey.
                grey = sheet.convert("L").load()
                m, e = mask_sheet.load(), eight.load()
                for yy in range(size[1]):
                    for xx in range(size[0]):
                        if m[xx, yy]:
                            first = mask_index - 4  # shade within the 8 colours around the index
                            e[xx, yy] = first + max(0, min(7, round(grey[xx, yy] / 128 * 4)))
            eight.save(os.path.join(gfx_dir, f"{name}_z1_8bpp.png"))
            head = header.format(name=name, file=f'"gfx/{name}_z1_8bpp.png"')
            parts += [head + " {", *lines, "}", ""]
        parts += [f'alternative_sprites({name}, {zoom_const[zoom]}, BIT_DEPTH_32BPP, "gfx/{name}_z{zoom}.png"{mask_arg}) {{',
                  *lines, "}", ""]
    return "\n".join(parts)


def canal_blocks(render_dir, ground_dir, gfx_dir):
    """Canals, locks and ship depots; returns NML text.

    OpenGFX defines canal water, locks and dikes as canal-feature items, so ours
    are items too: WF_WATERCLIFFS reuses the animated river slopes (flat water
    first), WF_DIKES the 12 canal edge pieces (cut like river banks), WF_LOCKS
    the 24 lock wall sprites (render/canals, origin (95, 80)). Ship depots
    4070-4075 replace the base sprites; 4070-4073 carry a company-colour mask.
    Aqueducts (render/aqueducts, origin (47, 72) like the bridges) replace the
    Action 5 AQUEDUCTS block, with the water animation in the trough.
    """
    canal_dir = os.path.join(render_dir, "canals")
    nml = ["item(FEAT_CANALS, canal_water_item, WF_WATERCLIFFS) {\n"
           "    property { graphic_flags: 1; }  // first sprite is flat water\n"
           "    graphics { river_slopes; }\n}\n"]
    dikes = {z: [bank_sprite(ground_dir, f"dike{k}", 0, z) for k in range(12)] for z in ZOOMS}
    nml.append(sheet_block("canal_dikes", "spriteset({name}, {file})", [f"dike{k}" for k in range(12)], dikes, gfx_dir))
    nml.append("item(FEAT_CANALS, canal_dike_item, WF_DIKES) {\n    graphics { canal_dikes; }\n}\n")
    locks = {z: [overlay_sprite(canal_dir, f"lock{k}", z, origin=(95, 80)) for k in range(24)] for z in ZOOMS}
    nml.append(sheet_block("canal_locks", "spriteset({name}, {file})", [f"lock{k}" for k in range(24)], locks, gfx_dir))
    nml.append("item(FEAT_CANALS, canal_lock_item, WF_LOCKS) {\n    graphics { canal_locks; }\n}\n")

    def depot(n, z):
        if n in (4074, 4075):
            sp = overlay_sprite(canal_dir, f"depot{n}", z, origin=(95, 80))
            return sp + (Image.new("L", sp[0].size, 0),)
        return overlay_sprite(canal_dir, f"depot{n}", z, origin=(95, 80), cc=True)

    nml.append(sheet_block("ship_depots", "replace {name}(4070, {file})", list(range(4070, 4076)),
                           {z: [depot(n, z) for n in range(4070, 4076)] for z in ZOOMS}, gfx_dir))
    aq_dir = os.path.join(render_dir, "aqueducts")
    aqueducts = {z: [water_anim.animate(overlay_sprite(aq_dir, f"aq{k}", z, origin=(47, 72)), z) for k in range(8)]
                 for z in ZOOMS}
    nml.append(sheet_block("aqueducts", "replacenew {name}(AQUEDUCTS, {file})", [f"aq{k}" for k in range(8)],
                           aqueducts, gfx_dir, mask_index=None))
    return "\n".join(nml)


def tram_extra_blocks(render_dir, gfx_dir):
    """Tram stops, depots, tunnel and bridge wires and tram-only bridge decks; returns NML text.

    TRAMWAY 23-26 (drive-through tram stops, kept for old GRFs) reuse the ROAD_STOPS parts;
    depots 49-54 (with track) and 113-118 (without, the ones the game uses with our tram overlay)
    are the same tram hall; bridge wires 95-106 are the straight and sloped ground wires, which
    the game draws at the same anchor and deck height; 107-112 are tram track on the deck.
    """
    ground_dir = os.path.join(render_dir, "ground")
    st_part = lambda n, z: overlay_sprite(os.path.join(render_dir, "stations"), f"st{n}", z, origin=(63, 72), cc=True)  # noqa: E731
    cat = lambda n, z: overlay_sprite(os.path.join(render_dir, "catenary"), f"cattram_{n}", z, origin=(47, 72), cc=True)  # noqa: E731
    depot = lambda n, z: overlay_sprite(os.path.join(render_dir, "depots"), f"depottram{n}", z, origin=(95, 80), cc=True)  # noqa: E731
    no_mask = lambda sp: sp + (Image.new("L", sp[0].size, 0),)  # noqa: E731
    stops = ["rs1", "rs2", "rs0", "rs3"]  # BUS_STOP_DT Y_E, X_W, Y_W, X_E
    # Bridge road-bits offsets 0-5 (flat Y, flat X, ramps NE, SE, SW, NW) as in GetBridgeRoadCatenary().
    bridge = [84, 85, 56, 57, 68, 70, 71, 69, 72, 74, 75, 73]  # back 95,96, front 97,98, back 99-102, front 103-106
    out = [sheet_block("tram_stops", "replacenew {name}(TRAMWAY, {file}, 23)", stops,
                       {z: [st_part(n, z) for n in stops] for z in ZOOMS}, gfx_dir)]
    for name, first in (("tram_depots_track", 49), ("tram_depots", 113)):
        out.append(sheet_block(name, f"replacenew {{name}}(TRAMWAY, {{file}}, {first})", list(range(113, 119)),
                               {z: [depot(n, z) for n in range(113, 119)] for z in ZOOMS}, gfx_dir))
    out.append(sheet_block("tram_tunnel_wires", "replacenew {name}(TRAMWAY, {file}, 80)", list(range(80, 84)),
                           {z: [cat(n, z) for n in range(80, 84)] for z in ZOOMS}, gfx_dir))
    out.append(sheet_block("tram_bridges", "replacenew {name}(TRAMWAY, {file}, 95)",
                           [f"wire {n}" for n in bridge] + [f"tramdeck{n}" for n in range(107, 113)],
                           {z: [cat(n, z) for n in bridge]
                            + [no_mask(bank_sprite(ground_dir, f"tramdeck{n}", 0, z)) for n in range(107, 113)]
                            for z in ZOOMS}, gfx_dir))
    return "\n".join(out)


def oneway_block(render_dir, gfx_dir):
    """One-way road markers (Action 5 ONE_WAY_ROAD, 18 sprites); returns NML text.

    The game draws them at the tile centre at the height of the surface there
    (DrawGroundSpriteAt(.., 8, 8, GetPartialPixelZ(8, 8))): 0 on flat tiles,
    half a level (4 px) on the inclined road slopes of the second and third sets.
    """
    ground_dir = os.path.join(render_dir, "ground")

    def marker(k, zoom):
        im, xo, yo = bank_sprite(ground_dir, f"oneway{k}", 0, zoom)
        return im, xo, yo - (16 - (0 if k < 6 else 4)) * zoom
    return sheet_block("oneway_roads", "replacenew {name}(ONE_WAY_ROAD, {file})", [f"oneway{k}" for k in range(18)],
                       {z: [marker(k, z) for k in range(18)] for z in ZOOMS}, gfx_dir)


def guideway_blocks(render_dir, grass_meta, gfx_dir):
    """Monorail and maglev: tracks, crossings, depots, stations, tunnels and bridges; returns NML text.

    Tracks 1087-1118 and 1169-1200 follow the rail layout 1005-1036 (single pieces without
    ground first), crossings 1382-1405 that of 1370-1381. Depots and stations have no track
    of their own, so 1145-1168 and 1227-1250 (rail sprite + 82 resp. 164) reuse the rail
    renders. Tunnels 2373-2388 and the bridge sprites only these two use (2581-2592,
    4324-4403) have their own renders.
    """
    ground_dir = os.path.join(render_dir, "ground")
    out = []
    for kind, first in (("mono", 1087), ("mglv", 1169)):
        tracks = {z: [bank_sprite(ground_dir, f"{kind}{first + k}", 0, z) for k in range(6)]
                  + [ground_sprite(ground_dir, f"{kind}{first + k}", z, grass_meta(RAIL_SLOPES.get(k - 6, 0)))
                     for k in range(6, 32)] for z in ZOOMS}
        out.append(sheet_block(f"{kind}_tracks", f"replace {{name}}({first}, {{file}})",
                               list(range(first, first + 32)), tracks, gfx_dir))
    out.append(sheet_block("guideway_crossings", "replace {name}(1382, {file})", list(range(1382, 1406)),
                           {z: [ground_sprite(ground_dir, f"cross{n}", z, grass_meta(0)) for n in range(1382, 1406)]
                            for z in ZOOMS}, gfx_dir))
    depot = lambda n, z: overlay_sprite(os.path.join(render_dir, "depots"), f"depot{n}", z, origin=(95, 80), cc=True)  # noqa: E731
    station = lambda n, z: overlay_sprite(os.path.join(render_dir, "stations"), f"st{n}", z, origin=(63, 72), cc=True)  # noqa: E731
    for kind, offset in (("mono", 82), ("mglv", 164)):
        out.append(sheet_block(f"{kind}_depots_stations", f"replace {{name}}({1063 + offset}, {{file}})",
                               [f"{n} as {n + offset}" for n in range(1063, 1087)],
                               {z: [depot(n, z) if n < 1069 else station(n, z) for n in range(1063, 1087)]
                                for z in ZOOMS}, gfx_dir))
    tunnel_dir = os.path.join(render_dir, "tunnels")
    out.append(sheet_block("guideway_tunnels", "replace {name}(2373, {file})", list(range(2373, 2389)),
                           {z: [tunnel_ground_sprite(tunnel_dir, n, z) if (n - 2373) % 2 == 0
                                else overlay_sprite(tunnel_dir, f"tun{n}", z, origin=(47, 56)) for n in range(2373, 2389)]
                            for z in ZOOMS}, gfx_dir))
    bridge_dir = os.path.join(render_dir, "bridges")
    for name, first, count in (("guideway_bridges_a", 2581, 12), ("guideway_bridges_b", 4324, 80)):
        out.append(sheet_block(name, f"replace {{name}}({first}, {{file}})", list(range(first, first + count)),
                               {z: [overlay_sprite(bridge_dir, f"br{n}", z, origin=(47, 72), cc=True)
                                    for n in range(first, first + count)] for z in ZOOMS},
                               gfx_dir, mask_index=STRUCT_INDEX))
    return "\n".join(out)


def runs(numbers):
    """Consecutive runs [(first, count)] of sorted sprite numbers."""
    out = []
    for n in numbers:
        if out and n == out[-1][0] + out[-1][1]:
            out[-1] = (out[-1][0], out[-1][1] + 1)
        else:
            out.append((n, 1))
    return out


def toyland_grass_blocks(render_dir, grass_meta, gfx_dir):
    """Toyland variants of the sprites with grass in them, from render/toyland; returns NML text.

    Only sprites the game draws in toyland and that show grass: rails, roads with verges,
    the level crossings without pavement (1370-1377 hold the toyland ones, the snow slot
    is never used), monorail and maglev, tunnels (verges and the mound), river banks and
    canal dikes (as canal-feature items again) and the airport grass pieces. Town roads, paved
    crossings, the gravel airfield yard (2667) and the company HQ grounds (paved) show no grass;
    the toyland town houses stand on their own lawn (4675, drawn from toy_grass) and need no variant.
    """
    import pack_airport
    import pack_industry
    toy_dir = os.path.join(render_dir, "toyland")
    out = []

    def tiles(name, numbers, sprite):
        for first, count in runs(numbers):
            label = f"{name}_{first}"
            out.append(sheet_block(label, f"replace {{name}}({first}, {{file}})", list(range(first, first + count)),
                                   {z: [sprite(n, z) for n in range(first, first + count)] for z in ZOOMS}, gfx_dir,
                                   mask_index=COMPANY_INDEX))

    tiles("toy_rails", range(1011, 1037),
          lambda n, z: ground_sprite(toy_dir, f"rail{n}", z, grass_meta(RAIL_SLOPES.get(n - 1011, 0))))
    tiles("toy_roads", range(1332, 1351),
          lambda n, z: ground_sprite(toy_dir, f"road{n}", z, grass_meta(ROAD_SLOPES.get(n - 1332, 0))))
    tiles("toy_crossings", range(1370, 1374), lambda n, z: ground_sprite(toy_dir, f"cross{n}", z, grass_meta(0)))
    for kind, first in (("mono", 1087), ("mglv", 1169)):
        tiles(f"toy_{kind}", range(first + 6, first + 32),
              lambda n, z, kind=kind, first=first: ground_sprite(toy_dir, f"{kind}{n}", z,
                                                                 grass_meta(RAIL_SLOPES.get(n - first - 6, 0))))
    tiles("toy_guideway_crossings", [*range(1382, 1386), *range(1394, 1398)],
          lambda n, z: ground_sprite(toy_dir, f"cross{n}", z, grass_meta(0)))
    tunnel_dir = os.path.join(toy_dir, "tunnels")
    tiles("toy_tunnels", range(2365, 2397),
          lambda n, z: tunnel_ground_sprite(tunnel_dir, n, z) if (n - 2365) % 2 == 0
          else overlay_sprite(tunnel_dir, f"tun{n}", z, origin=(47, 56)))
    air_dir = os.path.join(toy_dir, "airports")
    tiles("toy_airport", [*range(2636, 2645), 2665, 2666, *range(2669, 2676)],
          lambda n, z: pack_industry.ground_sprite(air_dir, f"g{n}", z))
    out.append(sheet_block("toy_airport_grass", "replacenew {name}(AIRPORTS, {file}, 13)", ["gx13", "gx14"],
                           {z: [pack_airport.overlay_ground_sprite(air_dir, n, z) for n in ("gx13", "gx14")]
                            for z in ZOOMS}, gfx_dir))

    # Spritesets may not stand in a conditional block, only the items using them.
    banks = [(f"bank{v * 12 + k}", sl) for v, sl in enumerate(BANK_SLOPES) for k in range(12)]
    sets = [sheet_block("toy_river_banks", "spriteset({name}, {file})", [n for n, _ in banks],
                        {z: [bank_sprite(toy_dir, n, sl, z) for n, sl in banks] for z in ZOOMS}, gfx_dir),
            sheet_block("toy_canal_dikes", "spriteset({name}, {file})", [f"dike{k}" for k in range(12)],
                        {z: [bank_sprite(toy_dir, f"dike{k}", 0, z) for k in range(12)] for z in ZOOMS}, gfx_dir)]
    out.append("item(FEAT_CANALS, toy_river_bank_item, WF_RIVERBANKS) {\n    graphics { toy_river_banks; }\n}\n")
    out.append("item(FEAT_CANALS, toy_canal_dike_item, WF_DIKES) {\n    graphics { toy_canal_dikes; }\n}\n")
    return "\n".join(sets) + "if (climate == CLIMATE_TOYLAND) {\n" + "\n".join(out) + "}\n"


def main():
    render_dir, ref_dir, nml_dir = sys.argv[1:4]
    ground_dir, trees_dir, found_dir, fence_dir, signal_dir, depot_dir = (
        os.path.join(render_dir, d) for d in ("ground", "trees", "foundations", "fences", "signals", "depots"))
    bridge_dir, tunnel_dir = os.path.join(render_dir, "bridges"), os.path.join(render_dir, "tunnels")
    station_dir = os.path.join(render_dir, "stations")
    catenary_dir = os.path.join(render_dir, "catenary")
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
        "// Rocky land: let the game also use the second set (4042), picked per tile by TileHash.",
        "second_rocky_tileset = 1;",
        "",
    ]
    for name, first, count in GROUND_BLOCKS:
        tiles = {z: [ground_sprite(ground_dir, first + k, z, meta[str(first + k)]) for k in range(count)]
                 for z in ZOOMS}
        nml.append(sheet_block(name, f"replace {{name}}({first}, {{file}})",
                               [first + k for k in range(count)], tiles, gfx_dir))
    for name, header, items in WATER_BLOCKS:
        refs = [meta[str(3981 + SPRITE_SLOPES.index(slope))] for _, slope in items]
        tiles = {z: [water_anim.animate(ground_sprite(ground_dir, n, z, ref), z) for (n, _), ref in zip(items, refs)]
                 for z in ZOOMS}
        nml.append(sheet_block(name, header, [n for n, _ in items], tiles, gfx_dir, mask_index=None))
    # Rivers: our own canal-feature definitions replace OpenGFX's.
    slope_items = [(4061, 0)] + [(f"river{i}", sl) for i, sl in enumerate(RIVER_SLOPES)]
    tiles = {z: [water_anim.animate(ground_sprite(ground_dir, n, z, meta[str(3981 + SPRITE_SLOPES.index(sl))]), z)
                 for n, sl in slope_items] for z in ZOOMS}
    nml.append(sheet_block("river_slopes", "spriteset({name}, {file})", [n for n, _ in slope_items], tiles, gfx_dir,
                           mask_index=None))
    nml.append("item(FEAT_CANALS, river_slope_item, WF_RIVER_SLOPE) {\n"
               "    property { graphic_flags: 1; }  // first sprite is flat water\n"
               "    graphics { river_slopes; }\n}\n")
    banks = [(f"bank{v * 12 + k}", sl) for v, sl in enumerate(BANK_SLOPES) for k in range(12)]
    pieces = {z: [bank_sprite(ground_dir, n, sl, z) for n, sl in banks] for z in ZOOMS}
    nml.append(sheet_block("river_banks", "spriteset({name}, {file})", [n for n, _ in banks], pieces, gfx_dir))
    nml.append("item(FEAT_CANALS, river_bank_item, WF_RIVERBANKS) {\n"
               "    graphics { river_banks; }\n}\n")
    nml.append(canal_blocks(render_dir, ground_dir, gfx_dir))
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
    # Signals: electric block signals in the base set, everything else in the Action 5 block.
    sig = lambda v, t, i, c, z: overlay_sprite(signal_dir, f"sig_{v}_{t}_{i}_{c}", z, origin=(31, 40))  # noqa: E731
    base_sig = {z: [sig(0, 0, k // 2, k % 2, z) for k in range(16)] for z in ZOOMS}
    nml.append(sheet_block("signals_base", "replace {name}(1275, {file})", list(range(1275, 1291)), base_sig, gfx_dir))
    slots = {}
    for v in (0, 1):
        for t in range(6):
            if v == 0 and t == 0:
                continue
            for i in range(8):
                for c in (0, 1):
                    slots[t * 16 + v * 64 + i * 2 + c + (64 if t >= 4 else 0) - 16] = (v, t, i, c)
    blank = lambda z: (Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0)  # noqa: E731
    sigs = {z: [sig(*slots[k], z) if k in slots else blank(z) for k in range(240)] for z in ZOOMS}
    nml.append(sheet_block("signals", "replacenew {name}(PRE_SIGNAL_SEMAPHORE_PBS, {file})",
                           [f"sig {slots.get(k, 'unused')}" for k in range(240)], sigs, gfx_dir))
    depots = {z: [overlay_sprite(depot_dir, f"depot{n}", z, origin=(95, 80), cc=True)
                  for n in list(range(1063, 1069))] for z in ZOOMS}
    nml.append(sheet_block("rail_depots", "replace {name}(1063, {file})", list(range(1063, 1069)), depots, gfx_dir))
    depots = {z: [overlay_sprite(depot_dir, f"depot{n}", z, origin=(95, 80), cc=True)
                  for n in list(range(1408, 1414))] for z in ZOOMS}
    nml.append(sheet_block("road_depots", "replace {name}(1408, {file})", list(range(1408, 1414)), depots, gfx_dir))
    apron = {z: [ground_sprite(ground_dir, "apron2634", z, grass_meta(0))] for z in ZOOMS}
    nml.append(sheet_block("concrete", "replace {name}(2634, {file})", [2634], apron, gfx_dir))
    # Bridges: rail and road sprites 2437-2580 with the structure recolour mask.
    bridges = {z: [overlay_sprite(bridge_dir, f"br{n}", z, origin=(47, 72), cc=True) for n in range(2437, 2581)]
               for z in ZOOMS}
    nml.append(sheet_block("bridges", "replace {name}(2437, {file})", list(range(2437, 2581)), bridges, gfx_dir,
                           mask_index=STRUCT_INDEX))
    # Tunnels: per direction a ground sprite (tile + portal) and a front sprite.
    for name, first in (("tunnels_rail", 2365), ("tunnels_road", 2389)):
        tun = {z: [tunnel_ground_sprite(tunnel_dir, first + k, z) if k % 2 == 0
                   else overlay_sprite(tunnel_dir, f"tun{first + k}", z, origin=(47, 56)) for k in range(8)]
               for z in ZOOMS}
        nml.append(sheet_block(name, f"replace {{name}}({first}, {{file}})", list(range(first, first + 8)), tun, gfx_dir))
    # Stations and stops.
    st_part = lambda n, z: overlay_sprite(station_dir, f"st{n}", z, origin=(63, 72), cc=True)  # noqa: E731
    no_mask = lambda sp: sp + (Image.new("L", sp[0].size, 0),)  # noqa: E731
    nml.append(sheet_block("rail_station", "replace {name}(1069, {file})", list(range(1069, 1087)),
                           {z: [st_part(n, z) for n in range(1069, 1087)] for z in ZOOMS}, gfx_dir))
    bay_floor = set(range(2692, 2696)) | set(range(2708, 2712))
    nml.append(sheet_block("road_stops", "replace {name}(2692, {file})", list(range(2692, 2724)),
                           {z: [no_mask(ground_sprite(ground_dir, f"bay{n}", z, grass_meta(0))) if n in bay_floor
                                else st_part(n, z) for n in range(2692, 2724)] for z in ZOOMS}, gfx_dir))
    for name, header, parts in (
        ("drive_through_stops", "replacenew {name}(ROAD_STOPS, {file})", [f"rs{k}" for k in range(8)]),
        ("road_waypoints", "replacenew {name}(ROAD_WAYPOINTS, {file})", [f"rw{k}" for k in range(4)]),
        ("rail_waypoints", "replacenew {name}(OTTD_GUI, {file}, 78)", [f"wp{k}" for k in range(4)]),
    ):
        nml.append(sheet_block(name, header, parts, {z: [st_part(n, z) for n in parts] for z in ZOOMS}, gfx_dir))
    # Rail catenary and trams.
    cat = lambda n, z: overlay_sprite(catenary_dir, f"cat{n}", z, origin=(47, 72), cc=True)  # noqa: E731
    nml.append(sheet_block("catenary", "replacenew {name}(CATENARY, {file}, 0)", list(range(36)),
                           {z: [cat(f"rail_{k}", z) for k in range(36)] for z in ZOOMS}, gfx_dir))
    road_slopes = {11: 12, 12: 6, 13: 3, 14: 9}
    nml.append(sheet_block("tram_overlay", "replacenew {name}(TRAMWAY, {file}, 4)", list(range(4, 23)),
                           {z: [bank_sprite(ground_dir, f"tram{4 + k}", 0, z) for k in range(19)] for z in ZOOMS},
                           gfx_dir))
    nml.append(sheet_block("tram_track", "replacenew {name}(TRAMWAY, {file}, 27)", list(range(27, 46)),
                           {z: [ground_sprite(ground_dir, f"tram{27 + k}", z, grass_meta(road_slopes.get(k, 0)))
                                for k in range(19)] for z in ZOOMS}, gfx_dir))
    blank4 = lambda z: (Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0, Image.new("L", (1, 1), 0))  # noqa: E731
    nml.append(sheet_block("tram_wires_front", "replacenew {name}(TRAMWAY, {file}, 56)", list(range(56, 76)),
                           {z: [blank4(z) if k == 63 else cat(f"tram_{k}", z) for k in range(56, 76)] for z in ZOOMS},
                           gfx_dir))
    nml.append(sheet_block("tram_wires_back", "replacenew {name}(TRAMWAY, {file}, 84)", list(range(84, 95)),
                           {z: [cat(f"tram_{k}", z) for k in range(84, 95)] for z in ZOOMS}, gfx_dir))
    # Farm fields 4126-4296 (nine stages x 19 slopes, packed like ground) and their fences 4090-4125.
    for k in range(9):
        first = 4126 + 19 * k
        fields = {z: [ground_sprite(ground_dir, first + i, z, grass_meta(SPRITE_SLOPES[i])) for i in range(19)]
                  for z in ZOOMS}
        nml.append(sheet_block(f"farm_field{k}", f"replace {{name}}({first}, {{file}})",
                               list(range(first, first + 19)), fields, gfx_dir))
    farm_fences = {z: [overlay_sprite(fence_dir, f"ffence{n}", z) for n in range(4090, 4126)] for z in ZOOMS}
    nml.append(sheet_block("farm_fences", "replace {name}(4090, {file})", list(range(4090, 4126)),
                           farm_fences, gfx_dir))
    # Snow (arctic) and desert (tropic) densities share 4493-4568; replace them per climate.
    for climate, cdir in (("CLIMATE_ARCTIC", "snow"), ("CLIMATE_TROPICAL", "desert")):
        parts = []
        for k in range(4):
            first = 4493 + 19 * k
            tiles = {z: [ground_sprite(os.path.join(render_dir, cdir), first + i, z, grass_meta(SPRITE_SLOPES[i]))
                         for i in range(19)] for z in ZOOMS}
            parts.append(sheet_block(f"{cdir}{k + 1}", f"replace {{name}}({first}, {{file}})",
                                     list(range(first, first + 19)), tiles, gfx_dir))
        nml.append(f"if (climate == {climate}) {{\n" + "\n".join(parts) + "}\n")
    # Toyland: its own ground in 3924-4060 and shores with the toyland meadow.
    toy_dir = os.path.join(render_dir, "toyland")
    parts = []
    for name, first, count in GROUND_BLOCKS:
        tiles = {z: [ground_sprite(toy_dir, first + k, z, meta[str(first + k)]) for k in range(count)] for z in ZOOMS}
        parts.append(sheet_block(f"toy_{name}", f"replace {{name}}({first}, {{file}})",
                                 [first + k for k in range(count)], tiles, gfx_dir))
    shores = WATER_BLOCKS[1][2]
    tiles = {z: [water_anim.animate(ground_sprite(toy_dir, n, z, grass_meta(slope)), z) for n, slope in shores]
             for z in ZOOMS}
    parts.append(sheet_block("toy_water_shore", WATER_BLOCKS[1][1], [n for n, _ in shores], tiles, gfx_dir,
                             mask_index=None))
    nml.append("if (climate == CLIMATE_TOYLAND) {\n" + "\n".join(parts) + "}\n")
    nml.append(tram_extra_blocks(render_dir, gfx_dir))
    nml.append(oneway_block(render_dir, gfx_dir))
    nml.append(guideway_blocks(render_dir, grass_meta, gfx_dir))
    fences = {z: [overlay_sprite(fence_dir, f"fence{n}", z) for n in range(1301, 1309)] for z in ZOOMS}
    nml.append(sheet_block("track_fences", "replace {name}(1301, {file})", list(range(1301, 1309)), fences, gfx_dir))
    for name, header, names in (
        ("foundations_base", "replace {name}(990, {file})", [f"found_base{t}" for t in range(1, 15)]),
        ("foundations", "replacenew {name}(FOUNDATIONS_SLOPES_HALFTILES, {file})", [f"found{k}" for k in range(90)]),
    ):
        found = {z: [overlay_sprite(found_dir, n, z) for n in names] for z in ZOOMS}
        nml.append(sheet_block(name, header, names, found, gfx_dir))
    nml += house_blocks(os.path.join(render_dir, "houses"), os.path.join(ref_dir, "..", "houses", "houses.json"),
                        gfx_dir)
    for name, first, rendered in TREE_BLOCKS:
        trees = {z: [tree_sprite(trees_dir, rendered + g, z) for g in range(7)] for z in ZOOMS}
        nml.append(sheet_block(name, f"replace {{name}}({first}, {{file}})",
                               [first + g for g in range(7)], trees, gfx_dir))
    # Objects and industries, see tools/pack_industry.py.
    import pack_industry
    nml += pack_industry.object_blocks(render_dir, gfx_dir, sheet_block)
    nml += pack_industry.industry_blocks(render_dir, gfx_dir, sheet_block)
    # Airports, docks, buoys and the oil rig, see tools/pack_airport.py.
    import pack_airport
    nml += pack_airport.airport_blocks(render_dir, gfx_dir, sheet_block)
    # Ships, aircraft, trains and road vehicles (toyland has its own), disasters and effects, see tools/pack_vehicles.py.
    import pack_vehicles
    nml += pack_vehicles.ship_blocks(render_dir, gfx_dir, sheet_block)
    nml += pack_vehicles.aircraft_blocks(render_dir, gfx_dir, sheet_block)
    nml += pack_vehicles.train_blocks(render_dir, gfx_dir, sheet_block)
    nml += pack_vehicles.road_vehicle_blocks(render_dir, gfx_dir, sheet_block)
    nml += pack_vehicles.effect_blocks(render_dir, gfx_dir, sheet_block)
    nml.append(toyland_grass_blocks(render_dir, grass_meta, gfx_dir))
    open(os.path.join(nml_dir, "moderngfx.nml"), "w").write("\n".join(nml))

    os.makedirs(os.path.join(nml_dir, "lang"), exist_ok=True)
    open(os.path.join(nml_dir, "lang", "english.lng"), "w").write(
        "##grflangid 0x01\n"
        "STR_GRF_NAME :ModernGFX\n"
        "STR_GRF_DESC :Modern low-poly 32bpp graphics rendered in Blender, in every climate: terrain, water, trees, transport infrastructure, airports and docks, towns, industries and vehicles. Licence: GPL v2.\n"
    )
    nmlc = os.path.join(os.path.dirname(sys.executable), "nmlc")
    subprocess.run([nmlc, "-c", "--grf", "moderngfx.grf", "moderngfx.nml"], cwd=nml_dir, check=True)


if __name__ == "__main__":
    main()
