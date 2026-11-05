#!/usr/bin/env python3
"""Tile-space textures for airport grounds (render_airports.py lays them on the flat tile).

Like the rail and road textures (make_infra_textures.py), each texture covers one
tile: row r is OpenTTD x = 16 (r + 0.5) / n (row 0 at the NE edge), column c is
OpenTTD y (column 0 at the NW edge). Apron and grass come from the existing
textures (infra/apron2634, grass), so airport tiles join the apron and meadow
around them without a seam.

Written to <outdir>/<name>.png:
  stand2635            apron with an aircraft stand: white box, yellow lead-in line, stop bar
  taxi2636-taxi2644    taxiway pieces: grass islands on apron with edges along the tile axes,
                       kerb and yellow edge line on the apron side
  rwy2645-rwy2648      runway along x (exits A-D): asphalt, edge stripes, centre dash; A and D
                       also carry touchdown-zone bars
  rwyend2649           runway end: threshold piano keys
  afgrass2669-2672     small airfield grass (aprons A-D): mown stripes along the runway
  afrwy2673-2675       small airfield grass runway: near end (threshold at the SW edge),
                       middle, far end (threshold at the NE edge); short-mown strip
  afterm2665-2667      small airfield building grounds: grass with a gravel yard and path
  x_tarmac, x_rwy1-4, x_rwyend   Action 5 AIRPORTS 0-5: tarmac, runway along y and its end
  x_grass_right, x_grass_left    Action 5 AIRPORTS 13/14: grass halves over the apron (RGBA)

Usage: make_airport_textures.py <render/textures> <outdir> [size] [--grass <name>]
  --grass toy_grass  draw over <name>.png and write only the textures that show grass
"""

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_infra_textures as mi  # noqa: E402

ASPHALT = np.array([86, 92, 100.0])
TARMAC = np.array([112, 116, 120.0])
MARKING = np.array([246, 244, 232.0])
YELLOW = np.array([236, 196, 52.0])
GRAVEL = np.array([182, 172, 150.0])
PATH = np.array([206, 196, 170.0])


def grid(n):
    """OpenTTD tile coordinates (x down the rows, y along the columns), 0..16."""
    c = (np.arange(n) + 0.5) / n * 16
    return np.tile(c[:, None], (1, n)), np.tile(c, (n, 1))


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def band(v, lo, hi, aa):
    """1 inside lo..hi with anti-aliased edges of width aa."""
    return smooth(lo - aa, lo + aa, v) * (1 - smooth(hi - aa, hi + aa, v))


def blend(img, colour, alpha):
    a = np.clip(alpha, 0, 1)[..., None]
    img[..., :3] = img[..., :3] * (1 - a) + colour * a


def load(path, n):
    return np.asarray(Image.open(path).convert("RGB").resize((n, n), Image.BICUBIC), dtype=float)


def noise(n, seed, cells=24):
    """Periodic speckle noise 0..1, one repeat per tile."""
    rng = np.random.default_rng(seed)
    g = rng.random((cells, cells))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC), dtype=float) / 255


def with_alpha(rgb):
    out = np.ones(rgb.shape[:2] + (4,))
    out[..., :3] = rgb
    return out


# Taxiway pieces as grass islands (x0, x1, y0, y1) on apron, edges along the tile axes so
# they read as straight lines and continue into the neighbouring pieces. A side open to the
# tile edge (-I / I) merges with the neighbour's island; a side at 4 or 12 leaves a 4-unit
# apron margin that joins the neighbour's margin to an 8-unit taxiway. Laid out for the city
# airport (rows x 1-5, columns y 2-4), and the S, H, N column of the metropolitan airport:
#   x1: W  S            x3: S  HE VN        x5: N  (tower, radar)
#   x2: VS HW           x4: H  N  E
I = 99
TAXI = {
    2636: [(-I, 12, 4, 12)],             # APRON_W: island cut off from the stands and the S piece
    2637: [(4, I, 4, 12)],               # APRON_S: island running on to the SW
    2638: [],                            # VER_CROSSING_S: all apron, the junction off the pier
    2639: [(-I, 12, 4, 12)],             # HOR_CROSSING_W: end of the S island beside the runway
    2640: [(4, I, 4, 12)],               # VER_CROSSING_N: island running on to the SW
    2641: [(4, I, 4, 12)],               # HOR_CROSSING_E: island running on to the SW
    2642: [(-I, I, 4, 12)],              # APRON_E: island through to the radar grass
    2643: [(-I, I, 4, 12)],              # ARPON_N: island through to the tower grass
    2644: [(-I, 4, 4, 12), (12, I, 4, 12)],  # APRON_HOR: taxiway across the island along y
}


def island_distance(x, y, rects, r=1.2):
    """Signed distance outside the grass islands (negative inside), corners rounded by r."""
    d = np.full(x.shape, 1e9)
    for x0, x1, y0, y1 in rects:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hx, hy = (x1 - x0) / 2 - r, (y1 - y0) / 2 - r
        qx, qy = np.abs(x - cx) - hx, np.abs(y - cy) - hy
        d = np.minimum(d, np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r)
    return d


def taxi_texture(n, apron, grass, sprite):
    x, y = grid(n)
    d = island_distance(x, y, TAXI[sprite])
    img = with_alpha(apron.copy())
    blend(img, grass, 1 - smooth(-0.04, 0.04, d))
    # Light kerb at the edge, then a yellow taxiway edge line just inside the apron.
    blend(img, MARKING * 0.92, band(d, 0.0, 0.16, 0.03))
    blend(img, YELLOW, band(d, 0.45, 0.7, 0.03))
    return img


def runway_texture(n, asphalt, along, touchdown=False, end=False):
    """Runway along x ('x') or y ('y'): asphalt over the whole tile with markings."""
    x, y = grid(n)
    a, c = (x, y) if along == "x" else (y, x)  # a: along the runway, c: across
    img = with_alpha(asphalt.copy())
    aa = 0.03
    # Edge stripes along both sides.
    blend(img, MARKING, band(c, 1.0, 1.45, aa) + band(c, 14.55, 15.0, aa))
    if end:
        # Threshold piano keys: six bars on either side of the centre line.
        keys = np.zeros_like(a)
        for k in range(6):
            lo = 2.2 + k * 1.0 if k < 3 else 2.2 + (k + 3) * 1.0 + 0.6
            keys += band(c, lo, lo + 0.55, aa)
        blend(img, MARKING, keys * band(a, 3.0, 13.0, aa))
        return img
    blend(img, MARKING, band(c, 7.8, 8.2, aa) * band(a, 4.0, 12.0, aa))
    if touchdown:
        bars = band(c, 4.3, 5.8, aa) + band(c, 10.2, 11.7, aa)
        blend(img, MARKING, bars * (band(a, 1.5, 6.0, aa) + band(a, 10.0, 14.5, aa)))
    return img


def mown(n, grass, along, phase=0.0, strength=0.07):
    """Mowing stripes along the runway direction: four light/dark bands per tile across it."""
    x, y = grid(n)
    c = y if along == "x" else x
    s = np.sign(np.sin((c / 16 * 4 + phase) * np.pi))
    soft = np.clip(np.sin((c / 16 * 4 + phase) * np.pi) * 6, -1, 1)
    del s
    return grass * (1 + strength * soft[..., None])


def airfield_runway(n, grass, end=None):
    """Grass strip along x: short-mown band y 3..13 (lighter), threshold bars at an end edge."""
    x, y = grid(n)
    g = mown(n, grass, "x", strength=0.05)
    strip = band(y, 3.0, 13.0, 0.25)
    light = g * 1.12 + np.array([10, 12, 0.0])
    img = with_alpha(g)
    blend(img, light, strip)
    if end is not None:
        a = x if end == 0 else 16 - x
        bars = np.zeros_like(a)
        for k in range(5):
            lo = 3.6 + k * 1.9
            bars += band(y, lo, lo + 0.9, 0.03)
        blend(img, MARKING, bars * band(a, 0.8, 2.6, 0.03))
    return img


def airfield_ground(n, grass, gravel_noise, yard, path):
    """Grass with a gravel yard (x0, x1, y0, y1) and a path strip (x0, x1, y0, y1)."""
    x, y = grid(n)
    img = with_alpha(grass.copy())
    gravel = GRAVEL * (0.92 + 0.16 * gravel_noise[..., None])
    for (x0, x1, y0, y1), colour in ((yard, gravel), (path, PATH * (0.96 + 0.08 * gravel_noise[..., None]))):
        m = band(x, x0, x1, 0.08) * band(y, y0, y1, 0.08)
        blend(img, colour, m)
    return img


def grass_half(n, grass, side):
    """Grass over the right (east, y > x) or left (west) half of the tile, with a kerb."""
    x, y = grid(n)
    d = (y - x if side == "right" else x - y) / np.sqrt(2)
    img = with_alpha(grass.copy())
    img[..., 3] = smooth(-0.04, 0.04, d)
    blend(img, MARKING * 0.92, band(d, 0.0, 0.16, 0.03))
    return img


def save(img, path):
    img = np.clip(img, 0, 255) if img.shape[-1] == 3 else img
    out = img.copy()
    if out.shape[-1] == 4:
        out[..., 3] *= 255
    mode = "RGBA" if out.shape[-1] == 4 else "RGB"
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode).save(path)


def main():
    argv, grass_name = mi.grass_args(sys.argv)
    tex_dir, outdir = argv[1], argv[2]
    n = int(argv[3]) if len(argv) > 3 else 1024
    os.makedirs(outdir, exist_ok=True)
    apron = load(os.path.join(tex_dir, "infra", "apron2634.png"), n)
    grass = load(os.path.join(tex_dir, grass_name + ".png"), n)
    nz = noise(n, 3)
    asphalt = ASPHALT * (0.96 + 0.08 * nz[..., None])
    tarmac = TARMAC * (0.96 + 0.08 * noise(n, 4)[..., None])
    x, y = grid(n)
    out = {}

    stand = with_alpha(apron.copy())
    box = band(np.minimum(np.minimum(x, 16 - x), np.minimum(y, 16 - y)), 1.3, 1.65, 0.03)
    blend(stand, MARKING, box)
    blend(stand, YELLOW, band(y, 7.85, 8.15, 0.03) * band(x, 1.65, 13.5, 0.03))
    blend(stand, MARKING, band(x, 12.6, 13.0, 0.03) * band(y, 6.6, 9.4, 0.03))
    out["stand2635"] = stand
    for sprite in TAXI:
        out[f"taxi{sprite}"] = taxi_texture(n, apron, grass, sprite)
    for sprite, td in ((2645, True), (2646, False), (2647, False), (2648, True)):
        out[f"rwy{sprite}"] = runway_texture(n, asphalt, "x", touchdown=td)
    out["rwyend2649"] = runway_texture(n, asphalt, "x", end=True)
    for k, sprite in enumerate(range(2669, 2673)):
        out[f"afgrass{sprite}"] = with_alpha(mown(n, grass, "x"))
    out["afrwy2673"] = airfield_runway(n, grass, end=16)
    out["afrwy2674"] = airfield_runway(n, grass)
    out["afrwy2675"] = airfield_runway(n, grass, end=0)
    out["afterm2665"] = airfield_ground(n, grass, nz, (2, 14, 3, 13), (14, 16, 6.5, 9.5))
    out["afterm2666"] = airfield_ground(n, grass, nz, (1, 15, 1, 12), (12, 16, 12, 16))
    out["afterm2667"] = airfield_ground(n, grass, nz, (0, 16, 0, 16), (0, 0, 0, 0))
    joints = (np.mod(x, 4) < 0.05) | (np.mod(y, 4) < 0.05)
    tarmac_img = with_alpha(tarmac)
    blend(tarmac_img, tarmac * 0.85, joints.astype(float))
    out["x_tarmac"] = tarmac_img
    for k in range(1, 5):
        out[f"x_rwy{k}"] = runway_texture(n, asphalt, "y", touchdown=k in (1, 4))
    out["x_rwyend"] = runway_texture(n, asphalt, "y", end=True)
    out["x_grass_right"] = grass_half(n, grass, "right")
    out["x_grass_left"] = grass_half(n, grass, "left")
    on_grass = ("taxi", "afgrass", "afrwy", "afterm", "x_grass")
    for name, img in out.items():
        if grass_name != "grass" and not name.startswith(on_grass):
            continue
        save(img, os.path.join(outdir, f"{name}.png"))
        print("wrote", name, flush=True)


if __name__ == "__main__":
    main()
