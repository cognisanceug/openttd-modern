"""Render the animated effect sprites (effect vehicles, effectvehicle.cpp) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_effects.py -- <outdir> [--only steam,spark] [--zooms 4]

An effect vehicle has the bounds origin 0 (EffectVehicle::UpdateDeltaXY), so its sprite origin is the
effect position itself; the renders put that point at the canvas pixel (W/2 - 1, ANCHOR) like the
vehicles, and meta.json stores it per frame and zoom. Frames are low-poly clusters (puffs of smoke
and steam, fire lobes, shards, sparks, soap bubbles) whose materials may be translucent: the toon
emission of style.py mixed with a transparent shader, so smoke thins out as it fades.

Sequences and the game's timing (ticks per frame; the game also lifts some effects each tick):
  steam      3079-3083  5 frames, 16 ticks, rises 1 unit / 8 ticks   steam engine chimney (z_pos + 10)
  diesel     3073-3078  6 frames, 8 ticks, rises 1 unit / 4 ticks    diesel exhaust
  spark      3084-3089  6 frames, 3 ticks                            electric spark, drawn 3 units up at
                                                                     the contact wire (z_pos + 13)
  smoke      2040-2044  5 frames, 16 ticks, rises 1 unit / 4 ticks   crash smoke, aircraft breakdown, copper mine
  breakdown  3737-3740  4 frames looped, 8 ticks                     broken-down vehicle
  chimney    3701-3708  8 frames looped, 8 ticks                     power station chimney (tile + 15, 14, 59)
  explosion  3709-3724  16 frames, 4 ticks                           crashes, disasters, demolition
  explosion_small 3725-3736  12 frames, 4 ticks
  bubble     4748-4762  toyland bubble generator: float 0-2, generate 0-3, burst 0-2, absorb 0-4
Looped sequences move every puff one step along a fixed path per frame, so the last frame leads into
the first.

Outputs (in <outdir>/z<zoom>/): <name>_<frame>.png, plus <outdir>/meta.json.
"""

import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_kit as bk  # noqa: E402
import style as st  # noqa: E402

K = 2.449  # z units per x/y unit
O, F = st.OBJECT, st.FLAT

# Materials are registered on the fly: key -> (sRGB, shading, alpha).
MATS = {}


def mat(rgb, params=O, alpha=1.0):
    rgb = tuple(int(round(c)) for c in rgb)
    key = f"fx{rgb}{sorted(params.items())}{alpha:.3f}"
    MATS[key] = (rgb, params, max(0.0, min(1.0, alpha)))
    return key


def mix(c0, c1, t):
    t = max(0.0, min(1.0, t))
    return tuple(a + (b - a) * t for a, b in zip(c0, c1))


class FxMaterials:
    """Toon emission like bk.Materials, mixed with a transparent shader by the material's alpha."""

    def __init__(self):
        self.cache = {}

    def get(self, key):
        if key not in self.cache:
            rgb, params, alpha = MATS[key]
            m = st.toon_material(key, rgb, params=params)
            if alpha < 1.0:
                nt = m.node_tree
                out = nt.nodes["Material Output"]
                em = out.inputs["Surface"].links[0].from_node
                mixer = nt.nodes.new("ShaderNodeMixShader")
                clear = nt.nodes.new("ShaderNodeBsdfTransparent")
                mixer.inputs["Fac"].default_value = alpha
                nt.links.new(clear.outputs[0], mixer.inputs[1])
                nt.links.new(em.outputs[0], mixer.inputs[2])
                nt.links.new(mixer.outputs[0], out.inputs["Surface"])
                m.blend_method = "BLEND"
            self.cache[key] = m
        return self.cache[key]


def unit_dirs(n, seed, up=0.0):
    """n fixed pseudo-random unit vectors (x, y, z), biased upwards by up."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        z = rng.uniform(-1 + up, 1)
        t = rng.uniform(0, math.tau)
        r = math.sqrt(max(0.0, 1 - z * z))
        out.append((r * math.cos(t), r * math.sin(t), z))
    return out


def puff(k, c, R, m, lobes=5, seed=1, spin=0.0, flat=1.0):
    """Cloud of low-poly lobes around c = (x, y, z), overall radius about R (x/y units)."""
    x, y, z = c
    k.blob(x, y, z, R * 0.72, R * 0.72, R * 0.72 * K * flat, m, subdiv=2)
    cs, sn = math.cos(spin), math.sin(spin)
    for i, (dx, dy, dz) in enumerate(unit_dirs(lobes - 1, seed, up=0.3)):
        dx, dy = dx * cs - dy * sn, dx * sn + dy * cs
        r = R * (0.5 + 0.12 * ((i * 7 + seed) % 3))
        k.blob(x + dx * R * 0.55, y + dy * R * 0.55, z + dz * R * 0.5 * K * flat, r, r, r * K * flat, m, subdiv=2)


# --- smoke and steam ----------------------------------------------------------------------------

def steam(k, f, n):
    t = f / (n - 1)
    R = 1.0 + 1.35 * t
    a = (0.95, 0.9, 0.78, 0.58, 0.36)[f]
    puff(k, (0, 0, 0.35 * R * K), R, mat(mix((250, 251, 252), (236, 240, 244), t), O, a), lobes=5, seed=3,
         spin=0.5 * f)


def diesel(k, f, n):
    t = f / (n - 1)
    R = 0.65 + 1.1 * t
    puff(k, (0, 0, 0.3 * R * K), R, mat(mix((96, 100, 108), (156, 160, 166), t), O, 0.88 - 0.55 * t), lobes=3,
         seed=5, spin=0.7 * f)


def smoke(k, f, n):
    t = f / (n - 1)
    R = 1.5 + 1.5 * t
    puff(k, (0, 0, 0.3 * R * K), R, mat(mix((72, 72, 78), (132, 132, 138), t), O, 0.92 - 0.55 * t), lobes=5,
         seed=7, spin=0.6 * f)


def plume(k, f, n, count, path, r0, r1, c0, c1, a0, lobes=3, seed=9):
    """Looped plume: count puffs along path(s), s in [0, 1), each moving 1/count per loop of n frames."""
    for i in range(count):
        s = (i + f / n) / count
        x, y, z = path(s)
        a = a0 * min(1.0, s * count * 1.4 + 0.25) * (1 - s ** 1.6)
        if a < 0.03:
            continue
        puff(k, (x, y, z), r0 + (r1 - r0) * s, mat(mix(c0, c1, s), O, a), lobes=lobes, seed=seed, spin=s * 4.0)


def breakdown(k, f, n):
    plume(k, f, n, 5, lambda s: (-3.0 * s, 4.0 * s, 3.0 + 28.0 * s), 0.8, 2.7, (56, 56, 62), (118, 118, 124), 0.95)


def chimney(k, f, n):
    plume(k, f, n, 8, lambda s: (-5.0 * s, 11.0 * s, 2.5 + 44.0 * s), 0.8, 3.2, (242, 243, 244), (212, 216, 220),
          0.92, lobes=4, seed=11)


# --- electric sparks -------------------------------------------------------------------------------

SPARK_Z = 3.0  # the effect is spawned at z_pos + 10, our pantographs touch the wire at z_pos + 13


def spark(k, f, n):
    c = (0.0, 0.0, SPARK_Z)
    core, glow, ga, rays, ray_len, flying, fly_d, fall = (
        (0.22, 0.6, 0.35, 0, 0.0, 0, 0.0, 0.0),
        (0.34, 1.0, 0.42, 4, 1.3, 0, 0.0, 0.0),
        (0.44, 1.4, 0.45, 6, 2.1, 0, 0.0, 0.0),
        (0.32, 1.2, 0.3, 6, 2.5, 5, 1.8, 0.3),
        (0.18, 0.8, 0.18, 0, 0.0, 5, 2.7, 1.2),
        (0.0, 0.0, 0.0, 0, 0.0, 5, 3.3, 2.6),
    )[f]
    core, glow, ray_len, fly_d = core * 1.3, glow * 1.3, ray_len * 1.3, fly_d * 1.3
    if core:
        k.blob(*c, core, core, core * K, mat((244, 250, 255), F), subdiv=2)
    if glow:
        k.blob(*c, glow, glow, glow * K, mat((140, 186, 255), F, ga), subdiv=2)
    for dx, dy, dz in unit_dirs(rays, 21)[:rays]:
        k.rod(c, (dx * ray_len, dy * ray_len, SPARK_Z + dz * ray_len * K), 0.05, mat((206, 228, 255), F), n=4)
    for i, (dx, dy, dz) in enumerate(unit_dirs(flying, 23)):
        p = (dx * fly_d, dy * fly_d, SPARK_Z + dz * fly_d * K * 0.6 - fall * K)
        r = 0.14 if f < 5 else 0.1
        k.blob(*p, r, r, r * K, mat((255, 236, 170) if i % 2 else (220, 236, 255), F, 1.0 if f < 5 else 0.7))


# --- explosions ------------------------------------------------------------------------------------

FIRE = [(255, 250, 226), (255, 220, 110), (252, 168, 64), (232, 104, 52), (170, 70, 48)]


def explosion(k, f, n, scale=1.0, seed=31):
    """Fireball that flares up and burns out, shards flying out and falling, then rising dark smoke."""
    t = f / (n - 1)
    grow = min(1.0, (f + 1) / (0.28 * n))
    burn = 1.0 if t < 0.18 else max(0.0, 1 - (t - 0.18) / 0.45)  # fire intensity
    Rf = scale * (1.3 + 2.7 * grow)
    if burn > 0:
        # Hot core, yellow and orange lobes; as the fire burns out the lobes shrink and redden.
        heat = 1 - burn
        if t < 0.25:
            k.blob(0, 0, 0, Rf * 0.55, Rf * 0.55, Rf * 0.55 * K, mat(FIRE[0], F), subdiv=2)
        for i, (dx, dy, dz) in enumerate(unit_dirs(9, seed, up=-0.2)):
            ring = 0.45 + 0.25 * (i % 3) / 2
            r = Rf * (0.32 + 0.16 * ((i * 5) % 3) / 2) * (0.45 + 0.55 * burn)
            col = FIRE[min(4, 1 + (i % 2) + int(heat * 3))]
            k.blob(dx * Rf * ring, dy * Rf * ring, (dz * ring + 0.15 * heat) * Rf * K, r, r, r * K,
                   mat(col, F, 0.95 if burn > 0.3 else 0.75), subdiv=2)
    # Smoke takes over from the fire and rises (the effect itself does not move).
    u = (t - 0.22) / 0.78
    if u > 0:
        for i, (dx, dy, dz) in enumerate(unit_dirs(6, seed + 1, up=0.5)):
            uu = max(0.0, u - 0.06 * (i % 3))
            if uu <= 0:
                continue
            R = scale * (1.3 + 2.2 * uu)
            p = (dx * scale * 2.4 * (0.5 + uu), dy * scale * 2.4 * (0.5 + uu), (dz * 1.2 + 4.5 * uu) * scale * K)
            a = 0.95 * (1 - uu) ** 1.3
            if a > 0.04:
                puff(k, p, R * 0.7, mat(mix((60, 58, 58), (126, 124, 124), uu), O, a), lobes=3, seed=seed + i,
                     spin=uu * 3)
    # Shards on ballistic paths, glowing at first.
    if 0 < t < 0.75:
        for i, (dx, dy, dz) in enumerate(unit_dirs(11, seed + 2, up=0.1)):
            d = scale * (1.5 + 5.0 * t)
            z = (dz * d * 0.8 + scale * 8.0 * t - scale * 16.0 * t * t) * K * 0.5
            s = scale * (0.2 if i % 3 else 0.28)
            m = mat((255, 150, 60), F) if (t < 0.3 and i % 2) else mat((66, 62, 60), st.WALL)
            k.cyl(dx * d, dy * d, s, z - s * K * 0.5, z + s * K * 0.5, m, n=3, r_top=0.0, rot=i)


def explosion_large(k, f, n):
    explosion(k, f, n, 2.2, 31)


def explosion_small(k, f, n):
    explosion(k, f, n, 1.2, 37)


# --- toyland bubbles -------------------------------------------------------------------------------

RB = 2.4
BUBBLE = ((188, 226, 250), O, 0.5)


def bubble_ball(k, rx, rz, cz, flat_bottom=False):
    k.blob(0, 0, cz, rx, rx, rz, mat(*BUBBLE), subdiv=2)
    if flat_bottom:
        for v in k.parts[-1][1].verts:
            v.co.z = max(v.co.z, 0.0)
    # Highlights towards the light, a faint pink rim reflection on the far side.
    if rz > 0.4 * RB * K:
        h = min(rx, rz / K)
        k.blob(0.35 * rx, -0.42 * rx, cz + 0.45 * rz, 0.26 * h, 0.26 * h, 0.26 * h * K, mat((255, 255, 255), F),
               subdiv=2)
        k.blob(-0.5 * rx, 0.45 * rx, cz - 0.3 * rz, 0.14 * h, 0.14 * h, 0.14 * h * K, mat((250, 200, 236), F, 0.8))


def bubble(k, f, n):
    if f < 3:  # floating, wobbling
        sx, sz = ((1.0, 1.0), (1.07, 0.92), (0.94, 1.08))[f]
        bubble_ball(k, RB * sx, RB * K * sz, RB * K * sz)
    elif f < 7:  # coming out of the spring
        frac = (0.25, 0.5, 0.75, 0.95)[f - 3]
        rz = RB * K
        bubble_ball(k, RB * (0.75 + 0.25 * frac), rz, (2 * frac - 1) * rz, flat_bottom=True)
    elif f < 10:  # burst: a ring of droplets flying apart
        g = f - 7
        for i, (dx, dy, dz) in enumerate(unit_dirs(14, 41)):
            d = RB * (1.05 + 0.45 * g)
            r = 0.3 - 0.06 * g
            k.blob(dx * d, dy * d, RB * K + dz * d * K, r, r, r * K, mat(BUBBLE[0], O, 0.9 - 0.25 * g))
    else:  # absorbed: drawn down into the catcher
        rx, rz, cz = ((1.0, 1.0, 1.0), (0.9, 1.15, 0.9), (0.72, 1.35, 0.6), (0.52, 1.5, -0.2), (0.32, 1.6, -1.6))[
            f - 10]
        bubble_ball(k, RB * rx, RB * K * rz, RB * K * cz)


# name: (first sprite, frames, canvas (w, h, anchor) at 1x, builder)
EFFECTS = {
    "steam": (3079, 5, (40, 40, 26), steam),
    "diesel": (3073, 6, (32, 32, 20), diesel),
    "spark": (3084, 6, (48, 48, 30), spark),
    "smoke": (2040, 5, (56, 56, 32), smoke),
    "breakdown": (3737, 4, (96, 80, 68), breakdown),
    "chimney": (3701, 8, (112, 96, 84), chimney),
    "explosion": (3709, 16, (136, 136, 84), explosion_large),
    "explosion_small": (3725, 12, (80, 80, 50), explosion_small),
    "bubble": (4748, 15, (56, 96, 52), bubble),
}


def render_effect(outdir, name, meta, zooms=bk.ZOOMS):
    first, frames, (w, h, anchor), build = EFFECTS[name]
    for f in range(frames):
        k = bk.Kit()
        build(k, f, frames)
        for zoom in zooms:
            zdir = os.path.join(outdir, f"z{zoom}")
            os.makedirs(zdir, exist_ok=True)
            scene = bk.new_scene(zoom, w, h, anchor, samples=32)
            bk.link_parts(k.parts, (0, 0), FxMaterials())
            bk.render(scene, os.path.join(zdir, f"{name}_{f}.png"))
            meta[f"{name}_{f}_z{zoom}"] = [(w // 2 - 1) * zoom, anchor * zoom]
        print(f"rendered {name} {f}", flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv and not argv[0].startswith("--") else os.path.join(os.getcwd(), "render", "effects")
    only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    zooms = [int(z) for z in argv[argv.index("--zooms") + 1].split(",")] if "--zooms" in argv else bk.ZOOMS
    os.makedirs(outdir, exist_ok=True)
    meta_path = os.path.join(outdir, "meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for name in EFFECTS:
        if only and name not in only:
            continue
        render_effect(outdir, name, meta, zooms)
        json.dump(meta, open(meta_path, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
