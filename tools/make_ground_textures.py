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


if __name__ == "__main__":
    main()
