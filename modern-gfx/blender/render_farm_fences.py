"""Render the farm field fences (sprites 4090-4125) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_farm_fences.py -- <outdir>

Six fence types in _clear_land_fence_sprites order, six sprites each:
  4090 hedge   4096 hedge with gate   4102 wooden fence
  4108 hedge with yellow blossom   4114 hedge with red blossom   4120 dry stone wall
Within a type (see DrawClearLandFence() and _fence_mod_by_tileh_*):
  even offsets lie along the tile's SW edge (W -> S), odd ones along the SE edge (S -> E);
  0/1 flat, 2/3 the far end (W or E) one level higher, 4/5 one level lower.
The game draws every piece with its origin on the tile's north corner at the
height of the S end (for the NE and NW edges it shifts the origin by one tile,
which maps the SW and SE edge shapes onto them), so the S end stays at height 0.
Output: <outdir>/z<zoom>/ffence<sprite>_overlay.png
"""

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ottd_camera as oc  # noqa: E402
import style as st  # noqa: E402

ZOOMS = (1, 2, 4)
FIRST = 4090
TYPES = ("hedge", "gate", "fence", "bloom_yellow", "bloom_red", "stone")
HEDGE_RGB = ((70, 128, 62), (82, 142, 66), (62, 116, 58))
BLOOM_RGB = {"bloom_yellow": (238, 206, 72), "bloom_red": (206, 72, 66)}
WOOD_RGB = (132, 104, 76)
RAIL_RGB = (162, 134, 100)
STONE_RGB = ((166, 160, 148), (146, 142, 134), (182, 176, 162))


def edge(offset):
    """Start (S corner, height 0) and end of the fence line for a sprite offset 0-5."""
    s = oc.CORNERS["S"].copy()
    end = (oc.CORNERS["W"] if offset % 2 == 0 else oc.CORNERS["E"]).copy()
    end.z = (0.0, oc.LEVEL, -oc.LEVEL)[offset // 2]
    return s, end


def add_mesh(name, bm, material, matrix):
    mesh = bpy.data.meshes.new(name)
    bm.transform(matrix)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)


def box(name, centre, size, yaw, pitch, material):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    rot = Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(-pitch, 4, "Y")
    add_mesh(name, bm, material, Matrix.Translation(centre) @ rot @ Matrix.Diagonal((*size, 1)))


def blob(name, centre, r, squash, rng, material):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    m = (Matrix.Translation(centre) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z")
         @ Matrix.Diagonal((1.0, 1.0, squash, 1)))
    add_mesh(name, bm, material, m)


def build_hedge(a, b, rng, bloom=None, gate=False):
    mats = [st.toon_material(f"hedge{i}", c) for i, c in enumerate(HEDGE_RGB)]
    bloom_mat = st.toon_material("bloom", BLOOM_RGB[bloom]) if bloom else None
    n = 12
    for i in range(n):
        f = (i + 0.5) / n
        if gate and abs(f - 0.5) < 0.12:
            continue
        r = rng.uniform(0.052, 0.066)
        p = a.lerp(b, f) + Vector((0, 0, r * 0.75))
        blob(f"bush{i}", p, r, 0.95, rng, rng.choice(mats))
        if bloom_mat:
            for k in range(3):
                q = p + Vector((rng.uniform(-r, r) * 0.7, rng.uniform(-r, r) * 0.7, r * rng.uniform(0.35, 0.8)))
                blob(f"bloom{i}_{k}", q, 0.012, 1.0, rng, bloom_mat)
    if gate:
        build_gate(a, b)


def build_gate(a, b):
    """Five-bar wooden gate in the middle of the hedge, with its two posts."""
    wood = st.toon_material("gatewood", WOOD_RGB)
    d = b - a
    flat = Vector((d.x, d.y, 0))
    yaw = math.atan2(flat.y, flat.x)
    pitch = math.atan2(d.z, flat.length)
    h = 0.075
    for f in (0.38, 0.62):
        p = a.lerp(b, f)
        box("gatepost", p + Vector((0, 0, h * 0.6)), (0.018, 0.018, h * 1.2), yaw, 0.0, wood)
    for k in range(3):
        mid = a.lerp(b, 0.5) + Vector((0, 0, h * (0.3 + 0.32 * k)))
        box("gatebar", mid, (d.length * 0.24, 0.008, 0.01), yaw, pitch, wood)


def build_fence(a, b):
    post = st.toon_material("post", WOOD_RGB)
    rail = st.toon_material("rail", RAIL_RGB)
    d = b - a
    flat = Vector((d.x, d.y, 0))
    yaw = math.atan2(flat.y, flat.x)
    pitch = math.atan2(d.z, flat.length)
    h = 0.085
    posts = 4
    for i in range(posts + 1):
        p = a.lerp(b, i / posts)
        box(f"post{i}", p + Vector((0, 0, h / 2)), (0.02, 0.02, h), yaw, 0.0, post)
    for frac in (0.5, 0.88):
        box(f"rail{frac}", a.lerp(b, 0.5) + Vector((0, 0, h * frac)), (d.length, 0.01, 0.014), yaw, pitch, rail)


def build_wall(a, b, rng):
    """Dry stone wall: a low course of irregular stones with a capping row."""
    mats = [st.toon_material(f"stone{i}", c) for i, c in enumerate(STONE_RGB)]
    d = b - a
    flat = Vector((d.x, d.y, 0))
    yaw = math.atan2(flat.y, flat.x)
    pitch = math.atan2(d.z, flat.length)
    n = 12
    for row, (hz, size) in enumerate(((0.022, 0.044), (0.055, 0.03))):
        for i in range(n + row):
            # The capping row sits half a stone off the course below.
            f = min(max((i + 0.5 * (1 - row) + rng.uniform(-0.1, 0.1)) / n, 0.03), 0.97)
            p = a.lerp(b, f) + Vector((0, 0, hz))
            s = d.length / n * rng.uniform(0.85, 1.05)
            box(f"stone{row}_{i}", p, (s, size * rng.uniform(0.9, 1.1) + 0.012, size), yaw + rng.uniform(-0.06, 0.06),
                pitch, rng.choice(mats))


def build(kind, offset):
    a, b = edge(offset)
    rng = random.Random(FIRST + TYPES.index(kind) * 6 + offset)
    if kind == "fence":
        build_fence(a, b)
    elif kind == "stone":
        build_wall(a, b, rng)
    else:
        build_hedge(a, b, rng, bloom=kind if kind.startswith("bloom") else None, gate=kind == "gate")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "fences")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    for t, kind in enumerate(TYPES):
        for offset in range(6):
            sprite = FIRST + t * 6 + offset
            for zoom in ZOOMS:
                bpy.ops.wm.read_factory_settings(use_empty=True)
                scene = bpy.context.scene
                st.configure_render(scene)
                oc.setup_camera(scene, zoom, 64 * zoom, 64 * zoom)
                build(kind, offset)
                scene.render.filepath = os.path.join(outdir, f"z{zoom}", f"ffence{sprite}_overlay.png")
                bpy.ops.render.render(write_still=True)
            print(f"rendered farm fence {sprite} ({kind} {offset})", flush=True)


if __name__ == "__main__":
    main()
