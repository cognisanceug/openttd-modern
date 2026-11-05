#!/usr/bin/env python3
"""Tile-space textures for the transport parts added after make_infra_textures.py.

Same conventions as make_infra_textures.py (x, y in -0.5..0.5, Blender axes,
row 0 is y = +0.5; RGB 0-255, alpha 0-1) and its helpers. Overlays are
transparent off the drawn parts.

Written to <outdir>/<name>.png:
  tramdeck<107-112>  tram track on a bridge deck without road (TRAMWAY 107-112): asphalt band
                     covering the deck's lane markings, grooved rails; axis Y, X, then the ramps
  oneway<0-17>       one-way road markers (Action 5 ONE_WAY_ROAD): per slope set (flat, rising to the
                     north, rising to the south) road X then Y, each with one-way traffic one way, the other,
                     or none (no-entry bars); a white arrow in each lane
  mono<1087-1118>, mglv<1169-1200>  monorail and maglev in the rail layout (1005-1036 shifted by 82
                     resp. 164): single pieces without ground, track with ground, slopes, junction
                     grounds; monorail is one steel rail on a concrete beam with ties, maglev a wide
                     concrete guideway with two guide rails and a reaction rail
  cross<1382-1405>   level crossings for monorail (1382-1393) and maglev (1394-1405), as 1370-1381
  deck_<mono|mglv>_<X|Y>[_wood]  bridge deck surfaces for them

Usage: make_transport_textures.py <render/textures> <outdir> [size] [--grass <name>]
  --grass toy_grass  draw over <name>.png and write only the guideway grounds and crossings, which show grass
"""

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_infra_textures as mi  # noqa: E402

# Bridge road-bits offset (0 = axis Y, 1 = axis X, 2-5 = flat head ramps NE, SE, SW, NW) -> arms.
DECK_ARMS = (("NW", "SE"), ("SW", "NE"), ("SW", "NE"), ("NW", "SE"), ("SW", "NE"), ("NW", "SE"))


def tram_deck_texture(n, arms, noise):
    x, y = mi.grid(n)
    img = np.zeros((n, n, 4))
    _, _, s = mi.arm_distance(x, y, arms[0])
    band = 1 - mi.smooth(mi.ROAD_HALF - 0.03, mi.ROAD_HALF - 0.02, np.abs(s))
    mi.blend(img, mi.ASPHALT * (1 + (noise[..., None] - 0.5) * 0.06), band)
    rails = mi.tram_texture(n, None, arms, True, noise)
    mi.blend(img, rails[..., :3], rails[..., 3])
    return img


def oneway_texture(n, axis, flow):
    """White arrows in both lanes; flow = disallowed directions - 1 (0, 1, 2 = both: no-entry bars).

    Flow 0 (DisallowedRoadDirection::Southbound) leaves the trackdirs X_SW and Y_NW
    (drd_to_multiplier in road_cmd.cpp), so its arrows point SW resp. NW; flow 1 the other way.
    """
    x, y = mi.grid(n)
    _, t, s = mi.arm_distance(x, y, "SW" if axis == "X" else "NW")  # t grows in the flow-0 direction
    if flow == 1:
        t, s = -t, -s
    img = np.zeros((n, n, 4))
    shape = np.zeros((n, n))
    for lane in (-0.11, 0.11):
        d = s - lane
        if flow == 2:
            shape = np.maximum(shape, ((np.abs(d) < 0.055) & (np.abs(t) < 0.018)).astype(float))
            continue
        shaft = (np.abs(d) < 0.013) & (t > -0.13) & (t < 0.03)
        head = (t >= 0.03) & (t < 0.12) & (np.abs(d) < 0.05 * (0.12 - t) / 0.09)
        shape = np.maximum(shape, (shaft | head).astype(float))
    mi.blend(img, mi.MARKING, shape)
    return img


def deck_ground(n, axis, wood, noise):
    """Bridge deck surface as in make_infra_textures.py (which gains its own deck_ground in a later version)."""
    x, y = mi.grid(n)
    if wood:
        plank = np.zeros((n, n, 3)) + mi.PLANK * (1 + (noise[..., None] - 0.5) * 0.08)
        along = y if axis == "X" else x
        joints = (np.mod((along + 0.5) * 16, 1) < 0.08)[..., None]
        return plank * (1 - joints) + mi.PLANK_JOINT * joints
    return np.zeros((n, n, 3)) + mi.DECK * (1 + (noise[..., None] - 0.5) * 0.05)


# --- monorail and maglev ---------------------------------------------------------

BEAM = np.array([186, 184, 176.0])
BEAM_EDGE = np.array([150, 148, 140.0])
GUIDEWAY = np.array([196, 196, 190.0])
REACTION = np.array([92, 104, 120.0])
GUIDEWAYS = {
    # kind: bed half width, bed colour, edge colour
    "mono": (0.12, BEAM, BEAM_EDGE),
    "mglv": (0.17, GUIDEWAY, BEAM_EDGE),
}


def guideway_bed(img, x, y, track, kind, noise):
    half, colour, edge = GUIDEWAYS[kind]
    t, s, length = mi.segment_coords(x, y, track)
    inside = (t > -0.25) & (t < length + 0.25)
    col = colour * (1 + (noise[..., None] - 0.5) * 0.05)
    mi.blend(img, edge, (1 - mi.smooth(half - 0.005, half + 0.005, np.abs(s))) * inside)
    mi.blend(img, col, (1 - mi.smooth(half - 0.025, half - 0.015, np.abs(s))) * inside)


def guideway_rails(img, x, y, track, kind):
    t, s, length = mi.segment_coords(x, y, track)
    inside = ((t > -0.2) & (t < length + 0.2)).astype(float)
    count = 8 if length > 0.9 else 6
    phase = np.mod(t / (length / count), 1.0)
    if kind == "mono":
        tie = (np.abs(s) < 0.1) & (np.abs(phase - 0.5) < 0.12)
        mi.blend(img, mi.SLEEPER * 0.9, tie * inside)
        mi.blend(img, mi.RAIL_DARK, (np.abs(s) < 0.03) * inside)
        mi.blend(img, mi.RAIL_TOP, (np.abs(s) < 0.016) * inside * 0.95)
    else:
        joint = np.abs(phase - 0.5) > 0.49
        mi.blend(img, mi.CONCRETE_JOINT, (joint & (np.abs(s) < 0.15)) * inside)
        mi.blend(img, REACTION, (np.abs(s) < 0.045) * inside)
        for side in (-1, 1):
            d = np.abs(s - side * 0.12)
            mi.blend(img, mi.RAIL_DARK, (d < 0.02) * inside)
            mi.blend(img, mi.RAIL_TOP, (d < 0.009) * inside * 0.9)


def guideway_texture(n, ground, tracks, kind, noise, region=None):
    """Like make_infra_textures.rail_texture: with ground (None: overlay with rails only) and junction region."""
    x, y = mi.grid(n)
    img = np.zeros((n, n, 4))
    if ground is not None:
        img[..., :3] = ground
        img[..., 3] = 1.0
    if region is not None:
        mi.blend(img, GUIDEWAYS[kind][1] * (1 + (noise[..., None] - 0.5) * 0.05), region)
    elif ground is not None:
        for tr in tracks:
            guideway_bed(img, x, y, tr, kind, noise)
    for tr in tracks:
        if ground is None:
            guideway_bed(img, x, y, tr, kind, noise)  # single pieces carry their bed, as the rail ones their sleepers
        guideway_rails(img, x, y, tr, kind)
    return img


def guideway_region(n, kind, open_edge):
    """Junction ground: the beds of every track not reaching open_edge (None: all six)."""
    x, y = mi.grid(n)
    half = GUIDEWAYS[kind][0]
    region = np.zeros((n, n))
    for track, ends in mi.TRACKS.items():
        if open_edge in ends:
            continue
        t, s, length = mi.segment_coords(x, y, track)
        inside = (t > -0.25) & (t < length + 0.25)
        region = np.maximum(region, (1 - mi.smooth(half - 0.005, half + 0.005, np.abs(s))) * inside)
    return region


def guideway_set(n, kind, first, grass, noise, outdir, on_grass_only=False):
    """The 32 sprites of the rail layout (1005-1036) for monorail or maglev, starting at first."""
    singles = () if on_grass_only else ("X", "Y", "U", "L", "R", "W")
    for k, tr in enumerate(singles):
        mi.save(guideway_texture(n, None, [tr], kind, noise), os.path.join(outdir, f"{kind}{first + k}.png"))
    with_ground = {6: ["Y"], 7: ["X"], 8: ["U"], 9: ["L"], 10: ["R"], 11: ["W"], 12: ["X", "Y"],
                   30: ["U", "L"], 31: ["R", "W"]}
    sloped = {12: "L", 13: "W", 14: "R", 15: "U", 16: "R", 17: "L", 18: "W", 19: "U", 20: "X", 21: "Y", 22: "X", 23: "Y"}
    for off, tr in sloped.items():
        with_ground[6 + off] = [tr]
    for k, trs in with_ground.items():
        mi.save(guideway_texture(n, grass, trs, kind, noise), os.path.join(outdir, f"{kind}{first + k}.png"))
    for k, edge in enumerate(("NE", "SW", "NW", "SE", None)):
        mi.save(guideway_texture(n, grass, [], kind, noise, guideway_region(n, kind, edge)),
                os.path.join(outdir, f"{kind}{first + 13 + k}.png"))


def guideway_crossing(n, grass, kind, road_axis, barred, paved, noise):
    """Level crossing as make_infra_textures.crossing_texture, with the guideway's rails across the road."""
    img = mi.crossing_texture(n, grass, road_axis, barred, paved, noise)
    x, y = mi.grid(n)
    rail = "Y" if road_axis == "X" else "X"
    _, s, _ = mi.segment_coords(x, y, rail)
    # Cover the plain rails the crossing texture drew, then lay the guideway's.
    road = mi.road_texture(n, grass, ("SW", "NE") if road_axis == "X" else ("NW", "SE"), paved, noise)
    band = (np.abs(s) < mi.GAUGE_HALF + mi.RAIL_EDGE + 0.01).astype(float)
    mi.blend(img, road[..., :3], band * (np.abs(mi.arm_distance(x, y, "NE" if road_axis == "X" else "NW")[2])
                                         < mi.ROAD_HALF))
    guideway_rails(img, x, y, rail, kind)
    return img


def main():
    argv, grass_name = mi.grass_args(sys.argv)
    outdir = argv[2]
    n = int(argv[3]) if len(argv) > 3 else 1024
    os.makedirs(outdir, exist_ok=True)
    rng = np.random.default_rng(1005)
    speck = rng.random((n // 4, n // 4))
    noise = np.asarray(Image.fromarray((speck * 255).astype(np.uint8)).resize((n, n), Image.NEAREST), dtype=float) / 255
    on_grass_only = grass_name != "grass"
    for k, arms in enumerate(() if on_grass_only else DECK_ARMS):
        mi.save(tram_deck_texture(n, arms, noise), os.path.join(outdir, f"tramdeck{107 + k}.png"))
    for k in range(0 if on_grass_only else 18):
        mi.save(oneway_texture(n, "XY"[k % 6 // 3], k % 3), os.path.join(outdir, f"oneway{k}.png"))
    grass = mi.load_tiled(os.path.join(argv[1], grass_name + ".png"), n)
    for kind, first, cross in (("mono", 1087, 1382), ("mglv", 1169, 1394)):
        guideway_set(n, kind, first, grass, noise, outdir, on_grass_only)
        for k in range(12):
            axis = "Y" if k % 2 == 0 else "X"
            mi.save(guideway_crossing(n, grass, kind, axis, (k // 2) % 2 == 1, 4 <= k < 8, noise),
                    os.path.join(outdir, f"cross{cross + k}.png"))
        for wood in () if on_grass_only else (False, True):
            for axis in ("X", "Y"):
                ground = deck_ground(n, axis, wood, noise)
                mi.save(guideway_texture(n, ground, [axis], kind, noise),
                        os.path.join(outdir, f"deck_{kind}_{axis}{'_wood' if wood else ''}.png"))
    print(f"wrote transport textures to {outdir}")


if __name__ == "__main__":
    main()
