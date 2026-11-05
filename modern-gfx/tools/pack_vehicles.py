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
needs no sprites of its own. The helicopter rotor is one sprite for every
direction, 3901 stopped and 3902-3904 turning; the turning frames are the
blades over a faint disc. Toyland's base graphics replace 0xE9D-0xECC (its six
aircraft) and the rotors, so a climate block replaces those again.
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

# (name, first sprite, sprites) as in blender/trains.py ENGINES / WAGONS / TOYLAND.
TRAIN_ENGINES = [
    ("jubilee", 0xB59, 8), ("a4", 0xB61, 8), ("tank", 0xB69, 8), ("d25", 0xB71, 4), ("d37", 0xB75, 4),
    ("e30", 0xB79, 4), ("hst", 0xB7D, 8), ("dmu", 0xB85, 8), ("dash", 0xB8D, 8), ("asiastar", 0xB95, 8),
    ("tim", 0xB9D, 8), ("x2001", 0xBA5, 4), ("z1", 0xBA9, 8), ("lev3", 0xBB1, 8), ("lev4", 0xBB9, 8),
    ("lev1", 0xBC1, 4), ("lev2", 0xBC5, 4), ("cs2400", 0xBC9, 8), ("centennial", 0xBD1, 8), ("cs4000", 0xBD9, 8),
    ("wills", 0xBE1, 8), ("kelling", 0xBE9, 4), ("turbo", 0xBED, 8), ("mjs1000", 0xBF5, 4), ("mjs250", 0xBF9, 8)]
_RAIL_WAGONS = ["pass", "coal", "mail", "oil", "livestock", "goods", "food", "grain", "wood", "flat", "hopper",
                "armoured", "coal_full", "grain_full", "wood_full", "steel_full", "iron_full", "paper_full",
                "copper_full", "water", "fruit", "fruit_full", "rubber", "rubber_full"]
TRAIN_WAGONS = [(f"w_{n}", 0xAAD + 4 * i, 4) for i, n in enumerate(_RAIL_WAGONS)] + \
    [(f"m_{n}", 0xB0D + 4 * i, 4) for i, n in enumerate(_RAIL_WAGONS[:19])]
TOYLAND_TRAINS = [
    ("toy_powernaut", 0xB59, 8), ("toy_mightymover", 0xB61, 8), ("toy_ploddy", 0xB69, 8), ("toy_pdiesel", 0xBC9, 8),
    ("toy_ndiesel", 0xBD9, 8), ("toy_z99", 0xBA9, 8), ("toy_rocketeer", 0xBC1, 4), ("t_pass", 0xAAD, 4)] + \
    [(f"t_{n}", 0xAB5 + 4 * i, 4) for i, n in enumerate(
        ["mail", "sugar", "sugar_full", "floss", "floss_full", "toffee", "toffee_full", "bubble", "bubble_full", "cola",
         "cola_full", "sweet", "toy", "battery", "battery_full", "fizzy", "fizzy_full", "plastic", "plastic_full"])]
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


def train_blocks(render_dir, gfx_dir, sheet_block):
    veh_dir = os.path.join(render_dir, "vehicles")
    meta = json.load(open(os.path.join(veh_dir, "meta.json")))

    def block(sets):
        out = []
        for name, first, n in sets:
            sprites = {z: [vehicle_sprite(veh_dir, name, d, z, meta) for d in range(n)] for z in ZOOMS}
            out.append(sheet_block(f"train_{name}", "replace {name}(%d, {file})" % first,
                                   [f"{name} dir {d}" for d in range(n)], sprites, gfx_dir, mask_index=COMPANY_INDEX))
        return out
    return block(TRAIN_ENGINES + TRAIN_WAGONS) + [
        "if (climate == CLIMATE_TOYLAND) {\n" + "\n".join(block(TOYLAND_TRAINS)) + "}\n"]
