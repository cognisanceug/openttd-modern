#!/usr/bin/env python3
"""Generate tile-space textures for rails, roads and level crossings.

Rails and roads are flat patterns on the terrain, as in the map study, so each
sprite is first drawn as a texture covering one tile (x, y in -0.5..0.5,
Blender axes; row 0 is y = +0.5), then Blender lays it on the flat or sloped
tile with the usual shading (render_ground.py, kind "infra").

Track and road pieces run between tile edge midpoints: NE (0, 0.5),
SE (0.5, 0), SW (0, -0.5), NW (-0.5, 0). Sleeper spacing and lane-marking
period divide every piece length, so patterns continue across tiles.

Written to <outdir>/<name>.png (RGBA; overlays are transparent off the track):
  rail1005-rail1010  single track pieces without ground (junction overlays)
  rail1011-rail1036  track with ground: straight, short pieces, cross, junction
                     grounds 1018-1022, sloped 1023-1034, double pieces 1035/1036
  road1313-road1331  roads with pavements (towns), 19 shapes
  road1332-road1350  roads with grass verges, 19 shapes
  cross1370-cross1381 level crossings (rail X/Y, open/barred, grass/paved/snow slot)
  apron2634          concrete slabs (road depot floor, airport apron)
  deck_<rail|road>_<X|Y>[_wood]  bridge deck surfaces: concrete or timber planks with track or road

Usage: make_infra_textures.py <render/textures> <outdir> [size]
"""

import os
import sys

import numpy as np
from PIL import Image

MID = {"NE": (0.0, 0.5), "SE": (0.5, 0.0), "SW": (0.0, -0.5), "NW": (-0.5, 0.0)}
TRACKS = {"X": ("NE", "SW"), "Y": ("NW", "SE"), "U": ("NW", "NE"), "L": ("SW", "SE"),
          "R": ("NE", "SE"), "W": ("NW", "SW")}

BALLAST = np.array([150, 140, 126.0])
BALLAST_DARK = np.array([128, 118, 106.0])
SLEEPER = np.array([96, 78, 64.0])
RAIL_DARK = np.array([70, 72, 78.0])
RAIL_TOP = np.array([214, 218, 224.0])
ASPHALT = np.array([84, 90, 98.0])
KERB = np.array([210, 208, 198.0])
PAVING = np.array([192, 190, 180.0])
PAVING_JOINT = np.array([174, 172, 162.0])
MARKING = np.array([250, 246, 226.0])
BARRIER_RED = np.array([214, 58, 52.0])
POST = np.array([236, 236, 230.0])
CONCRETE = np.array([180, 180, 174.0])
DECK = np.array([160, 158, 150.0])
PLANK = np.array([138, 104, 72.0])
PLANK_JOINT = np.array([104, 78, 54.0])
CONCRETE_JOINT = np.array([150, 150, 146.0])

BALLAST_HALF = 0.21
SLEEPER_HALF = 0.17
GAUGE_HALF = 0.1
RAIL_HALF = 0.013
RAIL_EDGE = 0.022
ROAD_HALF = 0.23
KERB_W = 0.022


def grid(n):
    c = (np.arange(n) + 0.5) / n - 0.5
    x = np.tile(c, (n, 1))
    y = -np.tile(c[:, None], (1, n))
    return x, y


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def blend(img, colour, alpha):
    a = alpha[..., None]
    img[..., :3] = img[..., :3] * (1 - a) + colour * a
    img[..., 3] = np.maximum(img[..., 3], alpha)


def segment_coords(x, y, track):
    """Along-track t (0 at first end) and signed offset s for a track piece; also its length."""
    a, b = (np.array(MID[k]) for k in TRACKS[track])
    d = b - a
    length = float(np.hypot(*d))
    u = d / length
    n = np.array([-u[1], u[0]])
    px, py = x - a[0], y - a[1]
    return px * u[0] + py * u[1], px * n[0] + py * n[1], length


def draw_ballast(img, x, y, track, noise):
    t, s, length = segment_coords(x, y, track)
    m = 0.25  # run past the piece ends so joints between pieces are filled
    inside = (t > -m) & (t < length + m)
    a = (1 - smooth(BALLAST_HALF - 0.02, BALLAST_HALF + 0.01, np.abs(s))) * inside
    col = BALLAST + (BALLAST_DARK - BALLAST) * noise[..., None]
    img[..., :3] = img[..., :3] * (1 - a[..., None]) + col * a[..., None]
    img[..., 3] = np.maximum(img[..., 3], a)


def draw_rails(img, x, y, track):
    t, s, length = segment_coords(x, y, track)
    count = 8 if length > 0.9 else 6
    spacing = length / count
    inside = (t > -0.2) & (t < length + 0.2)
    phase = np.mod(t / spacing, 1.0)
    sleeper = (np.abs(s) < SLEEPER_HALF) & (np.abs(phase - 0.5) < 0.19) & inside
    blend(img, SLEEPER, sleeper.astype(float))
    for side in (-1, 1):
        d = np.abs(s - side * GAUGE_HALF)
        blend(img, RAIL_DARK, ((d < RAIL_EDGE) & inside).astype(float))
        blend(img, RAIL_TOP, ((d < RAIL_HALF) & inside).astype(float) * 0.95)


def rail_texture(n, ground, tracks, noise, ballast_region=None):
    img = np.zeros((n, n, 4))
    x, y = grid(n)
    if ground is not None:
        img[..., :3] = ground
        img[..., 3] = 1.0
    if ballast_region is not None:
        col = BALLAST + (BALLAST_DARK - BALLAST) * noise[..., None]
        blend(img, col, ballast_region)
    else:
        for tr in tracks:
            draw_ballast(img, x, y, tr, noise)
    if ground is None and ballast_region is None:
        img[..., 3] = 0  # overlays: rails and sleepers only
    for tr in tracks:
        draw_rails(img, x, y, tr)
    return img


# Road shapes in OpenTTD's sprite order (see GetRoadSpriteOffset): arms per shape.
ROAD_SHAPES = [
    ("NW", "SE"), ("SW", "NE"), ("NW", "SW", "SE", "NE"),
    ("NW", "SE", "NE"), ("NW", "SW", "NE"), ("NW", "SW", "SE"), ("SW", "SE", "NE"),
    ("NW", "SW"), ("NW", "NE"), ("SE", "NE"), ("SW", "SE"),
    ("SW", "NE"), ("NW", "SE"), ("SW", "NE"), ("NW", "SE"),  # slopes NE, SE, SW, NW
    ("NE",), ("SE",), ("SW",), ("NW",),
]


def arm_distance(x, y, arm):
    """Distance to the segment from the tile centre to an edge midpoint, plus along/across coords."""
    ex, ey = MID[arm]
    length = 0.5
    ux, uy = ex / length, ey / length
    t = x * ux + y * uy
    s = -x * uy + y * ux
    tc = np.clip(t, 0, length + 0.3)
    return np.hypot(x - tc * ux, y - tc * uy), t, s


def road_texture(n, ground, arms, paved, noise):
    img = np.zeros((n, n, 4))
    x, y = grid(n)
    img[..., :3] = ground
    img[..., 3] = 1.0
    if paved:
        slab = (np.mod((x + 0.5) * 8, 1) < 0.04) | (np.mod((y + 0.5) * 8, 1) < 0.04)
        img[..., :3] = PAVING * (1 + (noise[..., None] - 0.5) * 0.05)
        blend(img, PAVING_JOINT, slab.astype(float))
    dist = np.min([arm_distance(x, y, a)[0] for a in arms], axis=0)
    kerb = 1 - smooth(ROAD_HALF + KERB_W - 0.004, ROAD_HALF + KERB_W + 0.004, dist)
    blend(img, KERB, kerb)
    road = 1 - smooth(ROAD_HALF - 0.004, ROAD_HALF + 0.004, dist)
    blend(img, ASPHALT * (1 + (noise[..., None] - 0.5) * 0.06), road)
    centre = np.hypot(x, y)
    straight = len(arms) == 2 and {MID[arms[0]], MID[arms[1]]} in (
        {MID["NW"], MID["SE"]}, {MID["SW"], MID["NE"]})
    for a in arms:
        _, t, s = arm_distance(x, y, a)
        dash = (np.abs(s) < 0.009) & (np.abs(np.mod(t, 0.25) - 0.125) < 0.055) & (t > -0.01) & (t < 0.5)
        if not straight:
            dash &= centre > (0.26 if len(arms) > 2 else 0.12)
        blend(img, MARKING, dash.astype(float))
    return img


def crossing_texture(n, ground, road_axis, barred, paved, noise):
    """Road straight along road_axis ('X' or 'Y') with rails across, posts and booms at the four corners."""
    arms = ("SW", "NE") if road_axis == "X" else ("NW", "SE")
    img = road_texture(n, ground, arms, paved, noise)
    x, y = grid(n)
    rail = "Y" if road_axis == "X" else "X"
    t, s, _ = segment_coords(x, y, rail)
    for side in (-1, 1):
        d = np.abs(s - side * GAUGE_HALF)
        blend(img, RAIL_DARK, (d < RAIL_EDGE).astype(float))
        blend(img, RAIL_TOP, (d < RAIL_HALF).astype(float) * 0.95)
    # Posts beside the road, one on each side of the track, and booms across the road when barred.
    _, ta, sa = arm_distance(x, y, arms[1])
    for along in (-0.24, 0.24):
        for across in (-1, 1):
            post = np.hypot(ta - along, sa - across * (ROAD_HALF + 0.05)) < 0.03
            blend(img, POST, post.astype(float))
            blend(img, BARRIER_RED, (np.hypot(ta - along, sa - across * (ROAD_HALF + 0.05)) < 0.014).astype(float))
            if barred:
                boom_s = sa * across
                boom = (np.abs(ta - along) < 0.012) & (boom_s > 0) & (boom_s < ROAD_HALF + 0.05)
                stripe = np.mod(boom_s * 14, 1) < 0.5
                blend(img, BARRIER_RED, (boom & stripe).astype(float))
                blend(img, POST, (boom & ~stripe).astype(float))
    return img


def load_tiled(path, n):
    """A world-XY texture (one repeat per tile) resampled to n x n in the same orientation."""
    return np.asarray(Image.open(path).convert("RGB").resize((n, n), Image.BICUBIC), dtype=float)


def save(img, path):
    """img holds RGB in 0-255 and alpha in 0-1."""
    rgba = np.concatenate([np.clip(img[..., :3], 0, 255), np.clip(img[..., 3:] * 255, 0, 255)], axis=2)
    Image.fromarray(rgba.astype(np.uint8), "RGBA").save(path)


def main():
    tex_dir, outdir = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    os.makedirs(outdir, exist_ok=True)
    grass = load_tiled(os.path.join(tex_dir, "grass.png"), n)
    rng = np.random.default_rng(1005)
    speck = rng.random((n // 4, n // 4))
    noise = np.asarray(Image.fromarray((speck * 255).astype(np.uint8)).resize((n, n), Image.NEAREST), dtype=float) / 255

    overlays = {1005: "X", 1006: "Y", 1007: "U", 1008: "L", 1009: "R", 1010: "W"}
    for sprite, tr in overlays.items():
        save(rail_texture(n, None, [tr], noise), os.path.join(outdir, f"rail{sprite}.png"))
    with_ground = {1011: ["Y"], 1012: ["X"], 1013: ["U"], 1014: ["L"], 1015: ["R"], 1016: ["W"], 1017: ["X", "Y"],
                   1035: ["U", "L"], 1036: ["R", "W"]}
    sloped = {12: "L", 13: "W", 14: "R", 15: "U", 16: "R", 17: "L", 18: "W", 19: "U", 20: "X", 21: "Y", 22: "X", 23: "Y"}
    for off, tr in sloped.items():
        with_ground[1011 + off] = [tr]
    for sprite, trs in with_ground.items():
        save(rail_texture(n, grass, trs, noise), os.path.join(outdir, f"rail{sprite}.png"))
    # Junction grounds: ballast everywhere except a grass strip along the edge no track reaches.
    x, y = grid(n)
    edge_dist = {"NE": 0.5 - y, "SW": y + 0.5, "NW": x + 0.5, "SE": 0.5 - x}
    for k, edge in enumerate(("NE", "SW", "NW", "SE", None)):
        region = np.ones((n, n)) if edge is None else smooth(0.2, 0.24, edge_dist[edge])
        save(rail_texture(n, grass, [], noise, ballast_region=region), os.path.join(outdir, f"rail{1018 + k}.png"))

    for k, arms in enumerate(ROAD_SHAPES):
        save(road_texture(n, grass, arms, True, noise), os.path.join(outdir, f"road{1313 + k}.png"))
        save(road_texture(n, grass, arms, False, noise), os.path.join(outdir, f"road{1332 + k}.png"))

    for k in range(12):
        # The sprite is chosen by the rail axis (GetCrossingRailAxis): even = rail X, so road Y.
        axis = "Y" if k % 2 == 0 else "X"
        barred = (k // 2) % 2 == 1
        paved = 4 <= k < 8
        save(crossing_texture(n, grass, axis, barred, paved, noise), os.path.join(outdir, f"cross{1370 + k}.png"))
    img = np.zeros((n, n, 4))
    img[..., :3] = CONCRETE * (1 + (noise[..., None] - 0.5) * 0.06)
    img[..., 3] = 1.0
    joint = (np.mod((x + 0.5) * 4, 1) < 0.012) | (np.mod((y + 0.5) * 4, 1) < 0.012)
    blend(img, CONCRETE_JOINT, joint.astype(float))
    save(img, os.path.join(outdir, "apron2634.png"))

    # Bridge decks: concrete or timber planks across the deck, with track or road along it.
    for wood in (False, True):
        if wood:
            plank = np.zeros((n, n, 3)) + PLANK * (1 + (noise[..., None] - 0.5) * 0.08)
        for axis in ("X", "Y"):
            if wood:
                along = y if axis == "X" else x
                ground = plank.copy()
                joints = (np.mod((along + 0.5) * 16, 1) < 0.08)[..., None]
                ground = ground * (1 - joints) + PLANK_JOINT * joints
            else:
                ground = np.zeros((n, n, 3)) + DECK * (1 + (noise[..., None] - 0.5) * 0.05)
            suffix = "_wood" if wood else ""
            img = rail_texture(n, ground, [axis], noise)
            save(img, os.path.join(outdir, f"deck_rail_{axis}{suffix}.png"))
            arms = ("SW", "NE") if axis == "X" else ("NW", "SE")
            save(road_texture(n, ground, arms, False, noise), os.path.join(outdir, f"deck_road_{axis}{suffix}.png"))
    print(f"wrote infrastructure textures to {outdir}")


if __name__ == "__main__":
    main()
