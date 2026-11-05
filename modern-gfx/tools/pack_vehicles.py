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

Aircraft: the 20 original sprite sets are 0xE9D-0xF3C, base + Direction
(_aircraft_sprite in aircraft_cmd.cpp, several engines share a set). The
shadow in flight is the same sprite drawn with the transparent palette, so it
needs no sprites of its own (the same holds for the disaster vehicles). The helicopter rotor is one sprite for every
direction, 3901 stopped and 3902-3904 turning; the turning frames are the
blades over a faint disc. Toyland's base graphics replace 0xE9D-0xECC (its six
aircraft) and the rotors, so a climate block replaces those again.

Disasters and effects: the disaster vehicles 3905-3923 and the road-works bulldozer
(blender/disasters.py) are packed like the aircraft; the animated effects (smoke, steam,
sparks, explosions, toyland bubbles; blender/render_effects.py) are drawn at the effect
position, so their offset is the crop box minus that point. No climate replaces them.
"""

import json
import os

from PIL import Image

COMPANY_INDEX = 202
ZOOMS = (1, 2, 4)

SHIPS = [("tanker", 0xE55), ("cargo", 0xE5D), ("ferry", 0xE65), ("hover", 0xE6D)]
TOYLAND_SHIPS = [("toycargo", 0xE5D), ("toyferry", 0xE65)]

AIRCRAFT = [("liner4hi", 0xE9D), ("jumbo", 0xEA5), ("concorde", 0xEAD), ("prop4tri", 0xEB5), ("trimotor", 0xEBD),
            ("jet_t", 0xEC5), ("trijet", 0xECD), ("twinjet", 0xED5), ("prop4", 0xEDD), ("heli", 0xEE5),
            ("hyperdart", 0xEED), ("bwb", 0xEF5), ("hypersonic", 0xEFD), ("zshuttle", 0xF05), ("flywing", 0xF0D),
            ("canard", 0xF15), ("boxwing", 0xF1D), ("truss", 0xF25), ("eprop", 0xF2D), ("heli2", 0xF35)]
TOYLAND_AIRCRAFT = [("toybiplane", 0xE9D), ("toyhiwing", 0xEA5), ("toyjet", 0xEAD), ("toyjumbo", 0xEB5),
                    ("toyrocket", 0xEBD), ("toyheli", 0xEC5)]
SPR_ROTOR_STOPPED = 3901
ROTOR_DISC_ALPHA, ROTOR_BLADE_ALPHA = 0.28, 0.55


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


def fade(im, f):
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: round(v * f)))
    return im


def rotor_sprite(veh_dir, prefix, frame, zoom, meta):
    """(im, x, y) of rotor frame 0 (stopped) to 3: frames 1-3 are faded blades over a faint disc, then the hub."""
    zdir = os.path.join(veh_dir, f"z{zoom}")

    def load(part):
        return Image.open(os.path.join(zdir, f"{prefix}{part}_d0.png")).convert("RGBA")
    if frame == 0:
        im = load("0")
    else:
        im = fade(load("_disc"), ROTOR_DISC_ALPHA)
        im.alpha_composite(fade(load(str(frame)), ROTOR_BLADE_ALPHA))
        im.alpha_composite(load("_hub"))
    im.putalpha(im.getchannel("A").point(lambda v: v if v >= 4 else 0))
    box = im.getbbox()
    ox, oy = meta[f"{prefix}0_d0_z{zoom}"]
    return im.crop(box), box[0] - ox, box[1] - oy


def aircraft_blocks(render_dir, gfx_dir, sheet_block):
    veh_dir = os.path.join(render_dir, "vehicles")
    meta = json.load(open(os.path.join(veh_dir, "meta.json")))

    def block(planes, rotor):
        out = []
        for name, first in planes:
            sprites = {z: [vehicle_sprite(veh_dir, name, d, z, meta) for d in range(8)] for z in ZOOMS}
            out.append(sheet_block(f"aircraft_{name}", "replace {name}(%d, {file})" % first,
                                   [f"{name} dir {d}" for d in range(8)], sprites, gfx_dir, mask_index=COMPANY_INDEX))
        sprites = {z: [rotor_sprite(veh_dir, rotor, f, z, meta) for f in range(4)] for z in ZOOMS}
        out.append(sheet_block(f"aircraft_{rotor}", "replace {name}(%d, {file})" % SPR_ROTOR_STOPPED,
                               ["rotor stopped", "rotor moving 1", "rotor moving 2", "rotor moving 3"], sprites,
                               gfx_dir))
        return out
    return block(AIRCRAFT, "rotor") + [
        "if (climate == CLIMATE_TOYLAND) {\n" + "\n".join(block(TOYLAND_AIRCRAFT, "toyrotor")) + "}\n"]


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


# Disaster vehicles (blender/disasters.py): one sprite each in the direction the game flies them,
# the submarines in four directions; 3905-3923 in this order. The road-works bulldozer 1416-1419.
DISASTERS = [("blimp", 3), ("blimp_crashing", 3), ("blimp_crashed", 3), ("ufo", 0), ("ufo_dark", 0)] + \
    [("sub_small", d) for d in (1, 3, 5, 7)] + [("sub_large", d) for d in (1, 3, 5, 7)] + \
    [("f15", 1), ("f15_fire", 1), ("ufo_big", 0), ("skyranger", 5), ("ah64", 5), ("ah64_fire", 5)]
SPR_DISASTERS, SPR_BULLDOZER = 3905, 1416

# Animated effects (blender/render_effects.py): name, first sprite, frames.
EFFECTS = [("smoke", 2040, 5), ("diesel", 3073, 6), ("steam", 3079, 5), ("spark", 3084, 6), ("chimney", 3701, 8),
           ("explosion", 3709, 16), ("explosion_small", 3725, 12), ("breakdown", 3737, 4), ("bubble", 4748, 15)]


def effect_sprite(fx_dir, name, f, zoom, meta):
    """(im, x, y) of one effect frame; its origin is the effect position."""
    im = Image.open(os.path.join(fx_dir, f"z{zoom}", f"{name}_{f}.png")).convert("RGBA")
    im.putalpha(im.getchannel("A").point(lambda v: v if v >= 4 else 0))
    box = im.getbbox() or (0, 0, 1, 1)
    ox, oy = meta[f"{name}_{f}_z{zoom}"]
    return im.crop(box), box[0] - ox, box[1] - oy


def effect_blocks(render_dir, gfx_dir, sheet_block):
    veh_dir = os.path.join(render_dir, "vehicles")
    meta = json.load(open(os.path.join(veh_dir, "meta.json")))
    out = []
    sprites = {z: [vehicle_sprite(veh_dir, name, d, z, meta)[:3] for name, d in DISASTERS] for z in ZOOMS}
    out.append(sheet_block("disasters", "replace {name}(%d, {file})" % SPR_DISASTERS,
                           [f"{name} dir {d}" for name, d in DISASTERS], sprites, gfx_dir))
    sprites = {z: [vehicle_sprite(veh_dir, "bulldozer", d, z, meta)[:3] for d in (1, 3, 5, 7)] for z in ZOOMS}
    out.append(sheet_block("bulldozer", "replace {name}(%d, {file})" % SPR_BULLDOZER,
                           [f"bulldozer dir {d}" for d in (1, 3, 5, 7)], sprites, gfx_dir))
    fx_dir = os.path.join(render_dir, "effects")
    fx_meta = json.load(open(os.path.join(fx_dir, "meta.json")))
    for name, first, frames in EFFECTS:
        sprites = {z: [effect_sprite(fx_dir, name, f, z, fx_meta) for f in range(frames)] for z in ZOOMS}
        out.append(sheet_block(f"effect_{name}", "replace {name}(%d, {file})" % first,
                               [f"{name} frame {f}" for f in range(frames)], sprites, gfx_dir))
    return out
