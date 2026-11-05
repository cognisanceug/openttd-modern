#!/usr/bin/env python3
"""Generate the seamless ground textures used on the ground tiles.

Every texture repeats exactly once per tile (1 Blender unit), so a sprite
meets its neighbours without a seam. Colours follow the map study:
  grass    meadow #8EC65E, lush patches #74B252, dry patches #BAC468, fine grain
  bare     soil (map study's earth tones, a little lighter for ground tiles)
  grass13  bare soil with grass on ~1/3 of the area
  grass23  bare soil with grass on ~2/3 of the area
  rough    darker, patchier meadow (low-poly tufts are added in Blender)
  rocky    meadow with gravel patches (low-poly boulders are added in Blender)
  water    the study's mid-depth water blue, nearly uniform
  sand     beach sand #E2D098 for the shores
  stone    dressed stone courses for foundation walls (U per tile, V per height level)
  riverbank0-11  RGBA river bank pieces (sides, outer and inner corners), see make_river_banks()
  canaldike0-11  RGBA canal edge pieces in the same order: stone quay with coping, see make_canal_dikes()
The grass-growth stages share one coverage field, so grass regrows in place.
Low-frequency variation stays gentle because one sprite repeats on every tile.

Usage: make_ground_textures.py <outdir> [size]
"""

import os
import random
import sys

from PIL import Image

MEADOW = (142, 198, 94)
LUSH = (116, 178, 82)
DRY = (186, 196, 104)
DEEP = (90, 150, 76)
SOIL = (150, 114, 80)
SOIL_DARK = (122, 90, 62)
SOIL_LIGHT = (172, 138, 100)
GRAVEL = (156, 152, 140)
WATER = (64, 142, 174)
WATER_DEEP = (48, 118, 156)
SAND = (226, 208, 152)
SAND_DARK = (208, 188, 134)
STONE = (190, 178, 154)
MORTAR = (146, 136, 116)


def periodic_noise(size, freq, rng):
    """Smooth value noise on a torus: freq x freq lattice, wraps at the texture edge."""
    lattice = [[rng.random() for _ in range(freq)] for _ in range(freq)]
    out = [[0.0] * size for _ in range(size)]
    for y in range(size):
        fy = y * freq / size
        y0 = int(fy)
        ty = fy - y0
        ty = ty * ty * (3 - 2 * ty)
        for x in range(size):
            fx = x * freq / size
            x0 = int(fx)
            tx = fx - x0
            tx = tx * tx * (3 - 2 * tx)
            a = lattice[y0 % freq][x0 % freq]
            b = lattice[y0 % freq][(x0 + 1) % freq]
            c = lattice[(y0 + 1) % freq][x0 % freq]
            d = lattice[(y0 + 1) % freq][(x0 + 1) % freq]
            out[y][x] = (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty
    return out


def smoothstep(e0, e1, v):
    t = min(1.0, max(0.0, (v - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


def quantile(field, q):
    vals = sorted(v for row in field for v in row[::4])
    return vals[int(q * (len(vals) - 1))]


def save(img_fn, size, path):
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            px[x, y] = tuple(max(0, min(255, int(round(v)))) for v in img_fn(x, y))
    img.save(path)
    print(f"wrote {path}")


def main():
    outdir = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 512
    os.makedirs(outdir, exist_ok=True)

    # Grass: same seed and draw order as the first version, so grass.png stays identical.
    rng = random.Random(19870314)
    octaves = [(periodic_noise(size, f, rng), w) for f, w in ((3, 0.5), (6, 0.3), (12, 0.2))]
    dry = periodic_noise(size, 4, rng)
    grain = periodic_noise(size, 96, rng)

    def grass(x, y):
        n = sum(o[y][x] * w for o, w in octaves)
        c = mix(MEADOW, LUSH, smoothstep(0.42, 0.62, n) * 0.45)
        c = mix(c, DRY, smoothstep(0.55, 0.75, dry[y][x]) * 0.35)
        g = 1.0 + (grain[y][x] - 0.5) * 0.07
        return [v * g for v in c]

    save(grass, size, os.path.join(outdir, "grass.png"))

    rng2 = random.Random(4242)
    soil_n = periodic_noise(size, 5, rng2)
    soil_fine = periodic_noise(size, 24, rng2)
    pebbles = periodic_noise(size, 128, rng2)
    cover = [[0.65 * a + 0.35 * b for a, b in zip(ra, rb)]
             for ra, rb in zip(periodic_noise(size, 6, rng2), periodic_noise(size, 16, rng2))]

    def bare(x, y):
        c = mix(SOIL, SOIL_DARK, smoothstep(0.45, 0.7, soil_n[y][x]) * 0.6)
        c = mix(c, SOIL_LIGHT, smoothstep(0.55, 0.8, soil_fine[y][x]) * 0.35)
        p = pebbles[y][x]
        g = 1.0 + (p - 0.5) * 0.16
        return [v * g for v in c]

    save(bare, size, os.path.join(outdir, "bare.png"))

    for name, share in (("grass13", 1 / 3), ("grass23", 2 / 3)):
        t = quantile(cover, 1 - share)

        def growth(x, y, t=t):
            k = smoothstep(t - 0.025, t + 0.025, cover[y][x])
            return mix(bare(x, y), grass(x, y), k)

        save(growth, size, os.path.join(outdir, f"{name}.png"))

    rng3 = random.Random(777)
    clumps = periodic_noise(size, 10, rng3)
    clumps2 = periodic_noise(size, 20, rng3)
    gravel = periodic_noise(size, 7, rng3)
    grit = periodic_noise(size, 160, rng3)

    def rough(x, y):
        c = mix(grass(x, y), LUSH, 0.45)
        c = mix(c, DEEP, smoothstep(0.5, 0.7, 0.6 * clumps[y][x] + 0.4 * clumps2[y][x]) * 0.7)
        c = mix(c, DRY, smoothstep(0.62, 0.8, dry[y][x]) * 0.3)
        return c

    save(rough, size, os.path.join(outdir, "rough.png"))

    def rocky(x, y):
        c = mix(grass(x, y), LUSH, 0.2)
        k = smoothstep(0.5, 0.68, gravel[y][x]) * 0.75
        g = mix(GRAVEL, [v * 0.82 for v in GRAVEL], grit[y][x])
        return mix(c, g, k)

    save(rocky, size, os.path.join(outdir, "rocky.png"))

    # Water: the map study's mid-depth blue, kept almost uniform because the
    # same tile repeats over whole seas.
    rng4 = random.Random(2468)
    swell = periodic_noise(size, 3, rng4)
    swell2 = periodic_noise(size, 7, rng4)
    ripple = periodic_noise(size, 40, rng4)

    def water(x, y):
        c = mix(WATER, WATER_DEEP, smoothstep(0.35, 0.75, 0.6 * swell[y][x] + 0.4 * swell2[y][x]) * 0.12)
        g = 1.0 + (ripple[y][x] - 0.5) * 0.03
        return [v * g for v in c]

    save(water, size, os.path.join(outdir, "water.png"))

    sand_n = periodic_noise(size, 9, rng4)
    sand_grain = periodic_noise(size, 140, rng4)

    def sand(x, y):
        c = mix(SAND, SAND_DARK, smoothstep(0.5, 0.75, sand_n[y][x]) * 0.5)
        g = 1.0 + (sand_grain[y][x] - 0.5) * 0.1
        return [v * g for v in c]

    save(sand, size, os.path.join(outdir, "sand.png"))

    # Foundation walls: dressed stone courses. U repeats once per tile along the
    # wall, V once per height level (three courses), see style.wall_material().
    rng5 = random.Random(1357)
    stone_n = periodic_noise(size, 30, rng5)
    courses, blocks = 3, 5
    shades = [[rng5.uniform(-0.07, 0.07) for _ in range(blocks)] for _ in range(courses)]

    def stone(x, y):
        v = y / size * courses
        row = int(v)
        u = x / size * blocks + (0.5 if row % 2 else 0.0)
        col = int(u) % blocks
        fv, fu = v - row, u - int(u)
        mortar = fv < 0.07 or fu < 0.035
        if mortar:
            return list(MORTAR)
        c = [s * (1 + shades[row][col]) for s in STONE]
        g = 1.0 + (stone_n[y][x] - 0.5) * 0.08
        edge = 1.0 - 0.08 * smoothstep(0.75, 1.0, fv)
        return [v_ * g * edge for v_ in c]

    save(stone, size, os.path.join(outdir, "stone.png"))

    make_river_banks(outdir, size, grass, sand)
    make_canal_dikes(outdir, size, grass, stone)


# River bank pieces in OpenTTD's RiverEdge order: sides NE, SE, SW, NW; outer
# corners E, S, W, N (both neighbouring sides land); inner corners E, S, W, N
# (only the diagonal neighbour is land). Distances in tile units, tile -0.5..0.5.
def _bank_distance(piece, x, y):
    side = {"NE": 0.5 - y, "SE": 0.5 - x, "SW": y + 0.5, "NW": x + 0.5}
    pairs = {"E": ("NE", "SE"), "S": ("SE", "SW"), "W": ("SW", "NW"), "N": ("NW", "NE")}
    points = {"E": (0.5, 0.5), "S": (0.5, -0.5), "W": (-0.5, -0.5), "N": (-0.5, 0.5)}
    kind, name = piece
    if kind == "side":
        return side[name]
    if kind == "outer":
        # Only the corner square where both sides' banks overlap; coloured by the nearer side.
        a, b = pairs[name]
        return BANK_WIDTH if max(side[a], side[b]) >= BANK_WIDTH else min(side[a], side[b])
    px, py = points[name]
    return ((x - px) ** 2 + (y - py) ** 2) ** 0.5


BANK_PIECES = ([("side", s) for s in ("NE", "SE", "SW", "NW")]
               + [("outer", c) for c in ("E", "S", "W", "N")]
               + [("inner", c) for c in ("E", "S", "W", "N")])
BANK_WIDTH = 0.19
FOAM = (240, 252, 250)
WET_SAND = (196, 176, 126)


def _bank_rgba(d, grass_c, sand_c):
    """Bank profile from the land edge (d = 0) towards the water: meadow, sand, wet sand, foam."""
    if d >= BANK_WIDTH:
        return None
    c = mix(grass_c, sand_c, smoothstep(0.03, 0.07, d))
    c = mix(c, WET_SAND, smoothstep(0.10, 0.14, d))
    c = mix(c, FOAM, smoothstep(0.14, 0.155, d) * 0.6)
    a = 1.0 - smoothstep(0.15, BANK_WIDTH, d) * 1.0
    return [*c, a]


def make_river_banks(outdir, size, grass, sand):
    """RGBA bank pieces in tile space; same pixel mapping as the world-XY textures."""
    for k, piece in enumerate(BANK_PIECES):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        px = img.load()
        for j in range(size):
            y = 0.5 - (j + 0.5) / size
            for i in range(size):
                x = (i + 0.5) / size - 0.5
                d = _bank_distance(piece, x, y)
                rgba = _bank_rgba(d, grass(i, j), sand(i, j))
                if rgba:
                    px[i, j] = tuple(max(0, min(255, int(round(v)))) for v in rgba[:3]) + (int(round(rgba[3] * 255)),)
        img.save(os.path.join(outdir, f"riverbank{k}.png"))
    print(f"wrote {len(BANK_PIECES)} river bank pieces")


# Canal edges: a stone quay instead of a sandy bank. From the land edge: meadow,
# light coping, then (only where the wall faces the camera, i.e. on the far NE
# and NW sides) the quay wall's face down to a dark waterline.
DIKE_WIDTH = 0.17
COPING = (214, 208, 194)
COPING_EDGE = (176, 168, 150)
WATERLINE = (40, 62, 70)
TO_CAMERA = (2 ** -0.5, -(2 ** -0.5))  # tile-space direction towards the viewer (S corner)


def _dike_profile(piece, x, y):
    """(distance from the land edge, how much the quay wall faces the camera 0..1) for a canal edge piece."""
    side = {"NE": 0.5 - y, "SE": 0.5 - x, "SW": y + 0.5, "NW": x + 0.5}
    normal = {"NE": (0, -1), "SE": (-1, 0), "SW": (0, 1), "NW": (1, 0)}  # land -> water
    kind, name = piece
    d = _bank_distance(piece, x, y)
    if kind == "inner":
        px, py = {"E": (0.5, 0.5), "S": (0.5, -0.5), "W": (-0.5, -0.5), "N": (-0.5, 0.5)}[name]
        r = max(d, 1e-6)
        n = ((x - px) / r, (y - py) / r)
    else:
        near = name if kind == "side" else min({"E": ("NE", "SE"), "S": ("SE", "SW"), "W": ("SW", "NW"),
                                                 "N": ("NW", "NE")}[name], key=lambda s_: side[s_])
        n = normal[near]
    facing = n[0] * TO_CAMERA[0] + n[1] * TO_CAMERA[1]
    return d, smoothstep(-0.1, 0.4, facing)


def _dike_rgba(d, facing, grass_c, stone_c):
    if d >= DIKE_WIDTH:
        return None
    if d < 0.05:
        return [*grass_c, 1.0]
    if d < 0.058:
        return [*COPING_EDGE, 1.0]
    if d < 0.09:
        return [*COPING, 1.0]
    wall_end = 0.09 + 0.065 * facing
    if d < wall_end:
        c = mix([v * 0.82 for v in stone_c], WATERLINE, smoothstep(wall_end - 0.02, wall_end, d) * 0.7)
        return [*c, 1.0]
    # Shadow of the quay on the water, fading out.
    a = 0.45 * (1.0 - smoothstep(wall_end, wall_end + 0.03, d))
    return [*WATERLINE, a] if a > 0.01 else None


def make_canal_dikes(outdir, size, grass, stone):
    """RGBA canal edge pieces in tile space, same order and mapping as the river banks."""
    for k, piece in enumerate(BANK_PIECES):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        px = img.load()
        for j in range(size):
            y = 0.5 - (j + 0.5) / size
            for i in range(size):
                x = (i + 0.5) / size - 0.5
                d, facing = _dike_profile(piece, x, y)
                if piece[0] == "outer" and d >= BANK_WIDTH:
                    d = DIKE_WIDTH
                rgba = _dike_rgba(d, facing, grass(i, j), stone(i, j * 3 % size))
                if rgba:
                    px[i, j] = tuple(max(0, min(255, int(round(v)))) for v in rgba[:3]) + (int(round(rgba[3] * 255)),)
        img.save(os.path.join(outdir, f"canaldike{k}.png"))
    print(f"wrote {len(BANK_PIECES)} canal dike pieces")


if __name__ == "__main__":
    main()
