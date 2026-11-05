#!/usr/bin/env python3
"""Generate the seamless ground textures used on the ground tiles.

Every texture repeats exactly once per tile (1 Blender unit), so a sprite
meets its neighbours without a seam. Colours follow the map study:
  grass    meadow #8EC65E, lush patches #74B252, dry patches #BAC468, fine grain
  bare     soil (map study's earth tones, a little lighter for ground tiles)
  grass13  bare soil with grass on ~1/3 of the area
  grass23  bare soil with grass on ~2/3 of the area
  rough    darker, patchier meadow (low-poly tufts are added in Blender); rough1-4 are
           variants for the flat sprites 4019-4022, see make_rough_rocky()
  rocky    meadow with scree patches (low-poly boulders are added in Blender); rocky2
           is the variant for the second rocky set
  field0-8 farm field stages, see make_fields()
  snow1-4, desert1-4  snow (arctic) and desert (tropic) densities, see make_snow_desert()
  water    the study's mid-depth water blue, nearly uniform
  sand     beach sand #E2D098 for the shores
  stone    dressed stone courses for foundation walls (U per tile, V per height level)
  riverbank0-11  RGBA river bank pieces (sides, outer and inner corners), see make_river_banks()
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

    make_rough_rocky(outdir, size)
    make_fields(outdir, size)
    make_snow_desert(outdir, size)

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


# Rough and rocky land come in variants that the game picks per tile (rocky
# sets 4023/4042 by TileHash bit 0, rough land 4000/4019-4022 by bits 0-2), so a
# large area does not repeat the same tile. All variants share one band along
# the tile edges and differ only inside it, so any two of them join seamlessly.
# The noise is band-passed white noise on the torus: periodic per tile like
# periodic_noise(), but isotropic, so patches have no blocky lattice shapes.
ROUGH_VARIANTS = 5    # rough.png (slopes and 4000), rough1-4.png (flat 4019-4022)
ROCKY_VARIANTS = 2    # rocky.png (set 1, 4023), rocky2.png (set 2, 4042)
EDGE_BAND = (0.02, 0.1)  # tile units from the edge: common below, own pattern above
SCREE = (128, 124, 114)
SCREE_LIGHT = (176, 170, 156)
SCREE_DARK = (98, 94, 88)


def _np_smoothstep(e0, e1, v):
    import numpy as np
    t = np.clip((v - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def spectral_noise(size, freq, seed, width=0.4):
    """Periodic isotropic noise: white noise band-passed around `freq` cycles per tile; mean 0, std 1."""
    import numpy as np
    white = np.random.default_rng(seed).standard_normal((size, size))
    f = np.fft.fftfreq(size) * size
    k = np.hypot(*np.meshgrid(f, f))
    band = np.exp(-np.log(np.maximum(k, 1e-6) / freq) ** 2 / (2 * width ** 2))
    band[0, 0] = 0.0
    out = np.real(np.fft.ifft2(np.fft.fft2(white) * band))
    return out / out.std()


class VariantNoise:
    """Noise fields for tile variants: variant 0 is the common field; others keep it near the edges."""

    def __init__(self, size, seed):
        import numpy as np
        self.size, self.seed = size, seed
        u = (np.arange(size) + 0.5) / size
        d = np.minimum(np.minimum(u, 1 - u)[None, :], np.minimum(u, 1 - u)[:, None])
        self.w = _np_smoothstep(EDGE_BAND[0], EDGE_BAND[1], d)

    def field(self, freq, variant, octave_id):
        import numpy as np
        common = spectral_noise(self.size, freq, self.seed * 1000 + octave_id)
        if variant == 0:
            return common
        own = spectral_noise(self.size, freq, self.seed * 1000 + octave_id + 100 * variant)
        w = self.w
        # Renormalise so the blend keeps unit variance across the band.
        return (common * (1 - w) + own * w) / np.sqrt((1 - w) ** 2 + w ** 2)

    def fbm(self, octaves, variant, octave_id):
        """Weighted sum of fields [(freq, weight)], renormalised to std 1."""
        import numpy as np
        total = sum(self.field(f, variant, octave_id + i) * wt for i, (f, wt) in enumerate(octaves))
        return total / np.sqrt(sum(wt * wt for _, wt in octaves))


def _np_mix(a, b, t):
    import numpy as np
    a, b = np.asarray(a, float), np.asarray(b, float)
    return a + (b - a) * np.asarray(t)[..., None]


def _save_np(rgb, path):
    import numpy as np
    Image.fromarray(np.clip(np.round(rgb), 0, 255).astype(np.uint8), "RGB").save(path)
    print(f"wrote {path}")


def _meadow(vn, v, lushness):
    """Meadow base for rough and rocky land, gentler than grass.png and varied per variant."""
    base = vn.fbm([(3, 0.6), (7, 0.4)], v, 0)
    c = _np_mix(MEADOW, LUSH, lushness + _np_smoothstep(-0.2, 1.4, base) * 0.35)
    c = _np_mix(c, DRY, _np_smoothstep(0.6, 1.8, vn.fbm([(5, 1.0)], v, 10)) * 0.3)
    return c * (1.0 + vn.field(110, v, 20) * 0.018)[..., None]


def make_rough_rocky(outdir, size):
    rough_vn = VariantNoise(size, 31)
    for v in range(ROUGH_VARIANTS):
        c = _meadow(rough_vn, v, 0.4)
        # Darker tussock clumps: soft-edged, irregular, at two scales.
        clumps = rough_vn.fbm([(4, 0.5), (9, 0.45), (20, 0.3)], v, 30)
        c = _np_mix(c, DEEP, _np_smoothstep(-0.2, 1.6, clumps) * 0.7)
        # Straw-coloured dry tufts and a fine grain of blades.
        straw = rough_vn.fbm([(18, 0.6), (40, 0.4)], v, 40)
        c = _np_mix(c, DRY, _np_smoothstep(1.0, 2.2, straw) * 0.45)
        c = c * (1.0 + rough_vn.fbm([(70, 0.5), (140, 0.5)], v, 50) * 0.035)[..., None]
        _save_np(c, os.path.join(outdir, "rough.png" if v == 0 else f"rough{v}.png"))

    rocky_vn = VariantNoise(size, 47)
    for v in range(ROCKY_VARIANTS):
        c = _meadow(rocky_vn, v, 0.2)
        # Scree patches: about 25 % cover, ragged at the rim.
        scree = rocky_vn.fbm([(3.5, 0.6), (8, 0.4), (18, 0.18)], v, 30)
        # Thinner along the shared edge band, where every variant looks the same.
        k = _np_smoothstep(0.55, 1.0, scree) * (0.4 + 0.6 * rocky_vn.w)
        # Brown soil fringe where grass gives way to gravel.
        fringe = _np_smoothstep(0.0, 0.45, scree) * (1 - k)
        c = _np_mix(c, SOIL, fringe * 0.45)
        # Gravel: mid grey with light stones and dark gaps at pebble size.
        peb = rocky_vn.fbm([(48, 0.6), (96, 0.4)], v, 40)
        g = _np_mix(SCREE, SCREE_LIGHT, _np_smoothstep(0.4, 1.8, peb) * 0.6)
        g = _np_mix(g, SCREE_DARK, _np_smoothstep(0.6, 1.8, -peb) * 0.45)
        c = _np_mix(c, g, k * 0.9)
        # Lone stones in the grass around the patches.
        stones = rocky_vn.field(64, v, 50)
        c = _np_mix(c, SCREE_LIGHT, _np_smoothstep(2.3, 2.8, stones) * (1 - k) * 0.8)
        _save_np(c, os.path.join(outdir, "rocky.png" if v == 0 else f"rocky{v + 1}.png"))


# Farm fields (sprites 4126-4296): nine stages in _clear_land_sprites_farmland
# order, ploughed soil -> sown -> green -> ripening -> golden -> stubble -> hay.
# Rows run along world X (OpenTTD y) and repeat a whole number of times per
# tile, so the furrows of a field continue from tile to tile.
FIELD_ROWS = 8
FIELD_STAGES = (
    # (crop colour, row cover 0..1, along-row gaps 0..1)
    (None, 0.0, 0.0),                # 0 bare ploughed soil
    ((132, 176, 84), 0.22, 0.65),    # 1 seedlings
    ((108, 164, 72), 0.45, 0.35),    # 2 young crop
    ((88, 150, 64), 0.78, 0.1),      # 3 full green
    ((132, 162, 70), 0.85, 0.08),    # 4 turning
    ((184, 180, 86), 0.88, 0.06),    # 5 ripening
    ((218, 186, 98), 0.9, 0.05),     # 6 golden, ready to harvest
    ((212, 190, 128), 0.75, 0.45),   # 7 stubble
    ((212, 190, 128), 0.75, 0.45),   # 8 stubble with hay bales (bales are geometry)
)
FIELD_SOIL = (138, 102, 70)
FIELD_SOIL_DARK = (104, 76, 54)
FIELD_SOIL_LIGHT = (164, 128, 92)


def make_fields(outdir, size):
    import numpy as np
    vn = VariantNoise(size, 63)
    j = (np.arange(size) + 0.5) / size
    t = (j * FIELD_ROWS) % 1.0
    # 0 in the furrow, 1 on the ridge; image rows run along world -Y.
    ridge = np.broadcast_to((0.5 - 0.5 * np.cos(2 * np.pi * t))[:, None], (size, size))
    d = np.broadcast_to(np.abs(t - 0.5)[:, None] * 2, (size, size))  # 0 at the row centre
    clods = vn.fbm([(30, 0.5), (70, 0.5)], 0, 0)
    patch = vn.fbm([(2, 0.6), (4, 0.4)], 0, 10)  # gentle unevenness across the field
    plants = vn.field(48, 0, 20)
    for k, (crop, cover, gaps) in enumerate(FIELD_STAGES):
        soil = _np_mix(FIELD_SOIL_DARK, FIELD_SOIL, ridge)
        soil = _np_mix(soil, FIELD_SOIL_LIGHT, _np_smoothstep(0.8, 2.0, clods) * 0.5)
        if k >= 7:  # harvested: dry, pale soil
            soil = _np_mix(soil, FIELD_SOIL_LIGHT, 0.45)
        c = soil
        if crop:
            # Leaf cover around the row centre, broken into plants along the row.
            gap = _np_smoothstep(-0.2, 1.2, -plants) * gaps
            leaf = _np_smoothstep(cover, cover * 0.55, d) * (1 - gap)
            col = _np_mix(crop, [v * 0.8 for v in crop], d / max(cover, 1e-3))
            col = col * (1.0 + clods * 0.03)[..., None]
            c = _np_mix(c, col, np.clip(leaf, 0, 1))
        c = c * (1.0 + patch * 0.035)[..., None]
        _save_np(c, os.path.join(outdir, f"field{k}.png"))


# Snow (arctic) and desert (tropic) share the sprites 4493-4568: four densities
# (_clear_land_sprites_snow_desert), each over 19 slopes. Both grow over the
# meadow of grass.png on one coverage field, so a tile thickens in place.
SNOW = (240, 245, 248)
SNOW_SHADE = (208, 222, 234)
DESERT = (228, 206, 148)
DESERT_DARK = (206, 178, 120)


def make_snow_desert(outdir, size):
    import numpy as np
    grass = np.asarray(Image.open(os.path.join(outdir, "grass.png")).convert("RGB"), float)
    vn = VariantNoise(size, 79)
    cover = vn.fbm([(3, 0.5), (7, 0.35), (16, 0.2)], 0, 0)
    drift = vn.fbm([(5, 0.6), (12, 0.4)], 0, 10)
    ripple = vn.fbm([(20, 0.5), (36, 0.5)], 0, 20)
    grain = vn.field(120, 0, 30)
    snow = _np_mix(SNOW, SNOW_SHADE, _np_smoothstep(0.2, 1.6, drift) * 0.5) * (1 + grain * 0.012)[..., None]
    sand = _np_mix(DESERT, DESERT_DARK, _np_smoothstep(-0.2, 1.4, ripple) * 0.45) * (1 + grain * 0.03)[..., None]
    # Dry, sparse grass where the desert starts.
    dry_grass = _np_mix(grass, DRY, 0.35)
    for k in range(1, 5):
        if k == 4:
            snow_k, sand_k = snow, sand
        else:
            t = np.quantile(cover, 1 - k / 4)
            m = _np_smoothstep(t - 0.22, t + 0.22, cover)
            snow_k = _np_mix(grass, snow, m)
            sand_k = _np_mix(dry_grass, sand, m)
        _save_np(snow_k, os.path.join(outdir, f"snow{k}.png"))
        _save_np(sand_k, os.path.join(outdir, f"desert{k}.png"))


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


if __name__ == "__main__":
    main()
