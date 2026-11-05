#!/usr/bin/env python3
"""Seamless ground textures for industry tiles (one repeat per tile, like the ground set).

  yard        compacted gravel and soil of industry grounds (2022 and the yards)
  forest      forest floor: needles, moss and dark soil under the plantation
  concrete    plain industrial concrete slabs with joints every quarter tile
  ore         reddish-brown ore soil for the iron ore mine pit
  coalyard    yard dusted with coal

Usage: make_industry_textures.py <outdir> [size]
"""

import os
import sys

import numpy as np
from PIL import Image


def noise(size, cells, rng, octaves=4):
    """Periodic value noise in 0..1 that tiles seamlessly."""
    out = np.zeros((size, size))
    amp, total = 1.0, 0.0
    for o in range(octaves):
        n = cells * 2 ** o
        grid = rng.random((n, n))
        t = np.arange(size) * n / size
        i0 = np.floor(t).astype(int) % n
        i1 = (i0 + 1) % n
        f = t - np.floor(t)
        f = f * f * (3 - 2 * f)
        rows = grid[i0][:, :] * (1 - f)[:, None] + grid[i1] * f[:, None]
        layer = rows[:, i0] * (1 - f)[None, :] + rows[:, i1] * f[None, :]
        out += amp * layer
        total += amp
        amp *= 0.5
    return out / total


def colorize(field, stops):
    """Map 0..1 to colours by linear interpolation between (pos, rgb) stops."""
    pos = np.array([p for p, _ in stops])
    rgb = np.array([c for _, c in stops], dtype=float)
    out = np.zeros(field.shape + (3,))
    for ch in range(3):
        out[..., ch] = np.interp(field, pos, rgb[:, ch])
    return out


def speckle(img, rng, density, rgb, size=1):
    h, w, _ = img.shape
    n = int(h * w * density)
    ys, xs = rng.integers(0, h, n), rng.integers(0, w, n)
    for dy in range(size):
        for dx in range(size):
            img[(ys + dy) % h, (xs + dx) % w] = rgb
    return img


def save(img, outdir, name):
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(outdir, f"{name}.png"))


def main():
    outdir = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 512
    os.makedirs(outdir, exist_ok=True)
    rng = np.random.default_rng(7)

    f = noise(size, 4, rng)
    yard = colorize(f, [(0.0, (138, 124, 106)), (0.5, (160, 148, 128)), (1.0, (176, 166, 146))])
    yard = speckle(yard, rng, 0.02, (120, 112, 100), 2)
    yard = speckle(yard, rng, 0.01, (190, 182, 166), 2)
    save(yard, outdir, "yard")

    coal = yard.copy()
    c = noise(size, 3, rng)
    dark = (c > 0.55)[..., None]
    coal = np.where(dark, coal * 0.45 + 18, coal)
    coal = speckle(coal, rng, 0.02, (48, 48, 52), 2)
    save(coal, outdir, "coalyard")

    f = noise(size, 5, rng)
    forest = colorize(f, [(0.0, (92, 84, 58)), (0.45, (108, 112, 66)), (0.7, (96, 132, 70)), (1.0, (112, 146, 78))])
    forest = speckle(forest, rng, 0.03, (132, 104, 70), 2)
    forest = speckle(forest, rng, 0.01, (70, 64, 48), 3)
    save(forest, outdir, "forest")

    f = noise(size, 6, rng, octaves=3)
    conc = colorize(f, [(0.0, (172, 172, 166)), (1.0, (196, 196, 190))])
    q = size // 4
    conc[::q, :] = conc[::q, :] * 0.8
    conc[:, ::q] = conc[:, ::q] * 0.8
    save(conc, outdir, "concrete")

    f = noise(size, 4, rng)
    ore = colorize(f, [(0.0, (128, 74, 54)), (0.5, (156, 96, 68)), (1.0, (178, 120, 86))])
    ore = speckle(ore, rng, 0.02, (104, 62, 48), 2)
    save(ore, outdir, "ore")


if __name__ == "__main__":
    main()
