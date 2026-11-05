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
  bay2692-bay2695, bay2708-bay2711  bus and truck bay floors (entrance NE, SE, SW, NW)
  tram<4-22>         tram track overlay on roads (grooved rails), 19 road shapes (TRAMWAY 4 + offset)
  tram<27-45>        tram-only track on a grassed bed with sleepers (TRAMWAY 27 + offset)

Usage: make_infra_textures.py <render/textures> <outdir> [size] [--grass <name>]
  --grass toy_grass  draw over render/textures/<name>.png instead of grass.png and write only
                     the textures that show grass (the toyland variants, into render/textures/toyland/infra)
"""

import os
import sys
from concurrent.futures import ProcessPoolExecutor
from functools import partial

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
BAY_YELLOW = np.array([236, 196, 52.0])
CONCRETE_JOINT = np.array([150, 150, 146.0])

BALLAST_HALF = 0.21
SLEEPER_HALF = 0.17
GAUGE_HALF = 0.1
RAIL_HALF = 0.013
RAIL_EDGE = 0.022
ROAD_HALF = 0.23
KERB_W = 0.022
LOOP_R = 0.12  # tram turning loop: outer rail edge 0.12 + 0.085 + 0.018 stays within ROAD_HALF


def grid(n):
    c = (np.arange(n) + 0.5) / n - 0.5
    x = np.tile(c, (n, 1))
    y = -np.tile(c[:, None], (1, n))
    return x, y


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def blend(img, colour, alpha):
    # Only the bounding box of the non-zero alpha changes, so work on that alone.
    rows, cols = np.flatnonzero(alpha.any(axis=1)), np.flatnonzero(alpha.any(axis=0))
    if rows.size == 0:
        return
    box = np.s_[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    if np.ndim(colour) == 3:
        colour = colour[box]
    alpha = alpha[box]
    a = alpha[..., None]
    sub = img[box]
    sub[..., :3] = sub[..., :3] * (1 - a) + colour * a
    sub[..., 3] = np.maximum(sub[..., 3], alpha)


def segment_coords(x, y, track):
    """Along-track t (0 at first end) and signed offset s for a track piece; also its length.

    On the short corner pieces s is measured along the tile edge they cross (the perpendicular
    offset times sqrt 2), so rails, sleepers and ballast meet a straight piece or another corner
    piece at the same points of the shared edge.
    """
    a, b = (np.array(MID[k]) for k in TRACKS[track])
    d = b - a
    length = float(np.hypot(*d))
    u = d / length
    n = np.array([-u[1], u[0]])
    px, py = x - a[0], y - a[1]
    s = px * n[0] + py * n[1]
    if length < 0.9:
        s = s * np.sqrt(2)
    return px * u[0] + py * u[1], s, length


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


def junction_region(n, open_edge):
    """Ballast of a junction ground: the beds of every track that does not reach open_edge (None: all six)."""
    x, y = grid(n)
    region = np.zeros((n, n))
    for track, ends in TRACKS.items():
        if open_edge in ends:
            continue
        t, s, length = segment_coords(x, y, track)
        inside = (t > -0.25) & (t < length + 0.25)
        region = np.maximum(region, (1 - smooth(BALLAST_HALF - 0.02, BALLAST_HALF + 0.01, np.abs(s))) * inside)
    return region


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


def grass_args(argv):
    """argv without an optional '--grass <name>', and that name (default 'grass')."""
    if "--grass" not in argv:
        return argv, "grass"
    i = argv.index("--grass")
    return argv[:i] + argv[i + 2:], argv[i + 1]


def save(img, path):
    """img holds RGB in 0-255 and alpha in 0-1."""
    rgba = np.concatenate([np.clip(img[..., :3], 0, 255), np.clip(img[..., 3:] * 255, 0, 255)], axis=2)
    Image.fromarray(rgba.astype(np.uint8), "RGBA").save(path)


# --- tram tracks ---------------------------------------------------------------

def tram_paths(arms):
    """Track centre lines for a road shape: straights, quarter arcs, loops.

    Each path is (points, index): a point array and a function giving, for grid
    coordinates, the (fractional) index of the polyline segment nearest to them.
    """
    mid = {k: np.array(v) for k, v in MID.items()}
    corner = {frozenset(("NW", "NE")): (-0.5, 0.5), frozenset(("NE", "SE")): (0.5, 0.5),
              frozenset(("SE", "SW")): (0.5, -0.5), frozenset(("SW", "NW")): (-0.5, -0.5)}
    opposite = {"NE": "SW", "SW": "NE", "NW": "SE", "SE": "NW"}

    def straight(a, b, n=64):
        d = b - a
        L2 = d @ d
        return np.linspace(a, b, n), lambda x, y: ((x - a[0]) * d[0] + (y - a[1]) * d[1]) / L2 * (n - 1)

    def arc(c, r, a0, a1, n):
        ang = np.linspace(a0, a1, n)
        path = np.stack([c[0] + r * np.cos(ang), c[1] + r * np.sin(ang)], axis=1)

        def index(x, y):
            rel = np.mod(np.arctan2(y - c[1], x - c[0]) - a0 + np.pi, 2 * np.pi) - np.pi
            if a1 - a0 >= 2 * np.pi - 1e-9:  # full loop: angles 0..2pi
                rel = np.mod(rel, 2 * np.pi)
            return rel / (a1 - a0) * (n - 1)
        return path, index

    paths = []
    arms = list(arms)
    done = set()
    for a in arms:
        if opposite[a] in arms and frozenset((a, opposite[a])) not in done:
            paths.append(straight(mid[a], mid[opposite[a]]))
            done.add(frozenset((a, opposite[a])))
    for i, a in enumerate(arms):
        for b in arms[i + 1:]:
            key = frozenset((a, b))
            if key in corner and not (len(arms) == 4):
                c = np.array(corner[key])
                a0 = np.arctan2(*(mid[a] - c)[::-1])
                a1 = np.arctan2(*(mid[b] - c)[::-1])
                if abs(a1 - a0) > np.pi:
                    a1 += 2 * np.pi * (1 if a1 < a0 else -1)
                paths.append(arc(c, 0.5, a0, a1, 64))
    if len(arms) == 1:
        # Dead end: run to a balloon loop around the tile centre, inside the road stub's round end.
        m = mid[arms[0]]
        d = -m / np.linalg.norm(m)
        centre = m + d * 0.5
        paths.append(straight(m, m + d * (0.5 - LOOP_R)))
        paths.append(arc(centre, LOOP_R, 0, 2 * np.pi, 96))
    return paths


REACH = 0.2  # beyond the tram bed (0.18), where distances no longer matter


def path_fields(x, y, path, index, window=2):
    """Distance to a polyline and the arc length of the nearest point, on the grid.

    Only the segments around index(x, y) are tested; within reach of the track
    (where the fields are used) the nearest segment is always among them.
    """
    seg_len = np.hypot(*np.diff(path, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg_len)])
    segs = len(path) - 1
    p0 = path[:-1]
    d = np.diff(path, axis=0)
    L2 = np.array([max(v @ v, 1e-12) for v in d])
    closed = np.allclose(path[0], path[-1])
    best_full = np.full(x.shape, 1e9)
    along_full = np.zeros(x.shape)
    # Pixels further than REACH from every path point are left at "far away".
    lo, hi = path.min(axis=0) - REACH, path.max(axis=0) + REACH
    cols = np.flatnonzero((x[0] >= lo[0]) & (x[0] <= hi[0]))
    rows = np.flatnonzero((y[:, 0] >= lo[1]) & (y[:, 0] <= hi[1]))
    if rows.size == 0 or cols.size == 0:
        return best_full, along_full
    box = np.s_[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    x, y = x[box], y[box]
    k0 = np.floor(index(x, y)).astype(int)
    best = np.full(x.shape, 1e9)
    best_k = np.full(x.shape, segs)
    along = np.zeros(x.shape)
    for off in range(-window, window + 1):
        k = np.mod(k0 + off, segs) if closed else np.clip(k0 + off, 0, segs - 1)
        px, py, dx, dy = p0[k, 0], p0[k, 1], d[k, 0], d[k, 1]
        t = np.clip(((x - px) * dx + (y - py) * dy) / L2[k], 0, 1)
        dist = np.hypot(x - (px + t * dx), y - (py + t * dy))
        # Same tie-break as testing every segment in order: the lowest index wins.
        better = (dist < best) | ((dist == best) & (k < best_k))
        best = np.where(better, dist, best)
        best_k = np.where(better, k, best_k)
        along = np.where(better, cum[k] + t * seg_len[k], along)
    best_full[box], along_full[box] = best, along
    return best_full, along_full


TRAM_GAUGE = 0.085
GROOVE = np.array([46, 48, 54.0])
TRAM_BED = np.array([96, 132, 72.0])


def tram_texture(n, ground, arms, overlay, noise):
    x, y = grid(n)
    img = np.zeros((n, n, 4))
    if not overlay:
        img[..., :3] = ground
        img[..., 3] = 1.0
    fields = [path_fields(x, y, p, index) for p, index in tram_paths(arms)]
    if not overlay:
        for dist, along in fields:
            bed = 1 - smooth(0.15, 0.18, dist)
            blend(img, TRAM_BED * (1 + (noise[..., None] - 0.5) * 0.15), bed)
        for dist, along in fields:
            sleeper = (dist < 0.13) & (np.abs(np.mod(along / 0.0625, 1) - 0.5) < 0.2)
            blend(img, SLEEPER, sleeper.astype(float))
    for dist, along in fields:
        for side_dist in (np.abs(dist - TRAM_GAUGE),):
            blend(img, GROOVE, (side_dist < 0.018).astype(float))
            blend(img, RAIL_TOP, (side_dist < 0.009).astype(float) * 0.9)
    return img


def apron_texture(n, noise):
    x, y = grid(n)
    img = np.zeros((n, n, 4))
    img[..., :3] = CONCRETE * (1 + (noise[..., None] - 0.5) * 0.06)
    img[..., 3] = 1.0
    joint = (np.mod((x + 0.5) * 4, 1) < 0.012) | (np.mod((y + 0.5) * 4, 1) < 0.012)
    blend(img, CONCRETE_JOINT, joint.astype(float))
    return img


def deck_ground(n, axis, wood, noise):
    x, y = grid(n)
    if wood:
        plank = np.zeros((n, n, 3)) + PLANK * (1 + (noise[..., None] - 0.5) * 0.08)
        along = y if axis == "X" else x
        joints = (np.mod((along + 0.5) * 16, 1) < 0.08)[..., None]
        return plank * (1 - joints) + PLANK_JOINT * joints
    return np.zeros((n, n, 3)) + DECK * (1 + (noise[..., None] - 0.5) * 0.05)


def bay_texture(n, entrance, truck, noise):
    """Road stop bay: asphalt, kerb on the three closed sides, bay markings."""
    x, y = grid(n)
    edge_d = {"NE": 0.5 - y, "SE": 0.5 - x, "SW": y + 0.5, "NW": x + 0.5}
    opposite = {"NE": "SW", "SE": "NW", "SW": "NE", "NW": "SE"}
    img = np.zeros((n, n, 4))
    img[..., :3] = PAVING * (1 + (noise[..., None] - 0.5) * 0.05)
    img[..., 3] = 1.0
    closed = [e for e in edge_d if e != entrance]
    inner = np.min([edge_d[e] for e in closed], axis=0)
    blend(img, KERB, (inner > 0.06).astype(float))
    blend(img, ASPHALT * (1 + (noise[..., None] - 0.5) * 0.06), (inner > 0.085).astype(float))
    far = edge_d[opposite[entrance]]
    side = np.min([edge_d[e] for e in closed if e != opposite[entrance]], axis=0)
    if truck:
        # Two parking bays separated by a white line along the bay.
        along_mid = np.abs(side - 0.5) < 0.01
        blend(img, MARKING, (along_mid & (far > 0.12)).astype(float))
        blend(img, MARKING, ((np.abs(far - 0.12) < 0.01) & (side > 0.1)).astype(float))
    else:
        box = (inner > 0.13) & (inner < 0.15)
        blend(img, BAY_YELLOW, box.astype(float))
    return img


def jobs(tex_dir, n, grass_name="grass"):
    """Every texture as (file name, function drawing it), slowest first; with another grass only those on grass."""
    grass = load_tiled(os.path.join(tex_dir, grass_name + ".png"), n)
    rng = np.random.default_rng(1005)
    speck = rng.random((n // 4, n // 4))
    noise = np.asarray(Image.fromarray((speck * 255).astype(np.uint8)).resize((n, n), Image.NEAREST), dtype=float) / 255
    out = []

    # Tram tracks: grooved rails on roads (overlay) and grassed track on their own.
    for k, arms in enumerate(ROAD_SHAPES):
        out.append((f"tram{27 + k}.png", partial(tram_texture, n, grass, arms, False, noise)))
        out.append((f"tram{4 + k}.png", partial(tram_texture, n, None, arms, True, noise)))

    overlays = {1005: "X", 1006: "Y", 1007: "U", 1008: "L", 1009: "R", 1010: "W"}
    for sprite, tr in overlays.items():
        out.append((f"rail{sprite}.png", partial(rail_texture, n, None, [tr], noise)))
    with_ground = {1011: ["Y"], 1012: ["X"], 1013: ["U"], 1014: ["L"], 1015: ["R"], 1016: ["W"], 1017: ["X", "Y"],
                   1035: ["U", "L"], 1036: ["R", "W"]}
    sloped = {12: "L", 13: "W", 14: "R", 15: "U", 16: "R", 17: "L", 18: "W", 19: "U", 20: "X", 21: "Y", 22: "X", 23: "Y"}
    for off, tr in sloped.items():
        with_ground[1011 + off] = [tr]
    for sprite, trs in with_ground.items():
        out.append((f"rail{sprite}.png", partial(rail_texture, n, grass, trs, noise)))
    # Junction grounds: the ballast beds of all tracks that may lie there (none reach the open edge).
    x, y = grid(n)
    edge_dist = {"NE": 0.5 - y, "SW": y + 0.5, "NW": x + 0.5, "SE": 0.5 - x}
    for k, edge in enumerate(("NE", "SW", "NW", "SE", None)):
        region = junction_region(n, edge)
        out.append((f"rail{1018 + k}.png", partial(rail_texture, n, grass, [], noise, ballast_region=region)))

    for k, arms in enumerate(ROAD_SHAPES):
        out.append((f"road{1313 + k}.png", partial(road_texture, n, grass, arms, True, noise)))
        out.append((f"road{1332 + k}.png", partial(road_texture, n, grass, arms, False, noise)))

    for k in range(12):
        # The sprite is chosen by the rail axis (GetCrossingRailAxis): even = rail X, so road Y.
        axis = "Y" if k % 2 == 0 else "X"
        barred = (k // 2) % 2 == 1
        paved = 4 <= k < 8
        out.append((f"cross{1370 + k}.png", partial(crossing_texture, n, grass, axis, barred, paved, noise)))
    out.append(("apron2634.png", partial(apron_texture, n, noise)))

    # Bridge decks: concrete or timber planks across the deck, with track or road along it.
    for wood in (False, True):
        for axis in ("X", "Y"):
            ground = deck_ground(n, axis, wood, noise)
            suffix = "_wood" if wood else ""
            out.append((f"deck_rail_{axis}{suffix}.png", partial(rail_texture, n, ground, [axis], noise)))
            arms = ("SW", "NE") if axis == "X" else ("NW", "SE")
            out.append((f"deck_road_{axis}{suffix}.png", partial(road_texture, n, ground, arms, False, noise)))

    for base, truck in ((2692, False), (2708, True)):
        for k, entrance in enumerate(("NE", "SE", "SW", "NW")):
            out.append((f"bay{base + k}.png", partial(bay_texture, n, entrance, truck, noise)))
    if grass_name != "grass":
        out = [job for job in out if any(a is grass for a in job[1].args)]
    return out


_JOBS = None


def _init_worker(tex_dir, n, grass_name):
    global _JOBS
    _JOBS = jobs(tex_dir, n, grass_name)


def _run_job(i, outdir):
    name, draw = _JOBS[i]
    save(draw(), os.path.join(outdir, name))


def main():
    argv, grass_name = grass_args(sys.argv)
    tex_dir, outdir = argv[1], argv[2]
    n = int(argv[3]) if len(argv) > 3 else 1024
    os.makedirs(outdir, exist_ok=True)
    count = len(jobs(tex_dir, 8, grass_name))  # each worker builds the full-size job list itself
    workers = min(8, os.cpu_count() or 1)
    with ProcessPoolExecutor(workers, initializer=_init_worker, initargs=(tex_dir, n, grass_name)) as pool:
        list(pool.map(partial(_run_job, outdir=outdir), range(count)))
    print(f"wrote infrastructure textures to {outdir}")


if __name__ == "__main__":
    main()
