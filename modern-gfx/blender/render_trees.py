"""Render a low-poly conifer and a deciduous tree in all 7 OpenTTD growth stages.

Run:  Blender -b --factory-startup -P render_trees.py -- <outdir>

Replaced sprites (temperate):
  1597-1603  conifer   (OpenGFX base 0x63D, classic spruce)
  1604-1610  deciduous (OpenGFX base 0x644, broad leafy tree)
Stages: 0-2 growing, 3 grown, 4-5 dying, 6 dead.

The tree's foot stands where OpenGFX trees have their trunk: 2.5/16 tile east
and 3.5/16 tile south-west of the drawing origin (sprite pixel (-2, +6) at 1x).
The canvas is 64z x 96z px with the drawing origin at pixel (31z, 64z).

For every sprite and zoom two images are written:
  <outdir>/z<zoom>/<sprite>_tree.png    the tree itself
  <outdir>/z<zoom>/<sprite>_shadow.png  its cast shadow on flat ground (shadow catcher alpha)
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
ANCHOR_Y = 64
FOOT = Vector((-0.5 + 2.5 / 16, 0.5 - 3.5 / 16, 0.0))
STAGE_SCALE = (0.45, 0.65, 0.85, 1.0, 1.0, 1.0, 1.0)

TRUNK_CONIFER = (92, 70, 52)
TRUNK_DECIDUOUS = (98, 76, 58)
NEEDLES = (62, 120, 84)
NEEDLES_BROWN = (128, 116, 70)
NEEDLES_DEAD = (122, 92, 62)
LEAVES = (96, 158, 72)
LEAVES_AUTUMN = (214, 160, 62)
BARE_WOOD = (112, 94, 80)

TREES = {
    "conifer": 1597,
    "deciduous": 1604,
}


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    st.configure_render(scene, samples=64)
    return scene


def add_mesh(name, bm, material, matrix):
    mesh = bpy.data.meshes.new(name)
    bm.transform(matrix)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def cone(name, r1, r2, depth, segments, material, matrix):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r1, radius2=r2, depth=depth)
    # create_cone is centred on the origin; move its base to z = 0.
    bm.transform(Matrix.Translation((0, 0, depth / 2)))
    return add_mesh(name, bm, material, matrix)


def ico(name, radius, material, matrix, subdiv=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    return add_mesh(name, bm, material, matrix)


def place(scale, offset=(0, 0, 0), rot_z=0.0, tilt=None):
    m = Matrix.Translation(FOOT + Vector(offset) * scale) @ Matrix.Rotation(rot_z, 4, "Z")
    if tilt:
        m = m @ tilt
    return m @ Matrix.Scale(scale, 4)


def build_conifer(stage, rng):
    s = STAGE_SCALE[stage]
    needles = {4: mix(NEEDLES, NEEDLES_BROWN, 0.35), 5: mix(NEEDLES, NEEDLES_BROWN, 0.75), 6: NEEDLES_DEAD}.get(stage, NEEDLES)
    trunk = st.toon_material("trunk", TRUNK_CONIFER)
    leaf = st.toon_material("needles", needles)
    cone("trunk", 0.035, 0.03, 0.2, 6, trunk, place(s))
    thin = 0.85 if stage == 6 else 1.0
    tiers = ((0.24, 0.12, 0.36), (0.19, 0.33, 0.32), (0.13, 0.53, 0.30))
    for i, (r, z, h) in enumerate(tiers):
        cone(f"tier{i}", r * thin, 0.0, h, 7, leaf, place(s, (0, 0, z), rot_z=rng.uniform(0, math.tau)))


def build_deciduous(stage, rng):
    s = STAGE_SCALE[stage]
    trunk = st.toon_material("trunk", TRUNK_DECIDUOUS if stage < 6 else BARE_WOOD)
    cone("trunk", 0.045, 0.03, 0.42, 6, trunk, place(s))
    if stage == 6:
        # Dead: bare branches only.
        for i in range(5):
            a = i * math.tau / 5 + rng.uniform(-0.3, 0.3)
            tilt = Matrix.Rotation(rng.uniform(0.5, 0.8), 4, Vector((-math.sin(a), math.cos(a), 0)))
            cone(f"branch{i}", 0.02, 0.006, rng.uniform(0.22, 0.32), 5, trunk,
                 place(s, (0, 0, rng.uniform(0.28, 0.4)), tilt=tilt))
        return
    leaves = {4: mix(LEAVES, LEAVES_AUTUMN, 0.4), 5: mix(LEAVES, LEAVES_AUTUMN, 0.85)}.get(stage, LEAVES)
    leaf = st.toon_material("leaves", leaves)
    lumps = ((0.0, 0.0, 0.56, 0.30), (-0.13, 0.06, 0.70, 0.21), (0.15, -0.07, 0.50, 0.22), (0.05, 0.15, 0.64, 0.20))
    for i, (x, y, z, r) in enumerate(lumps):
        rot = Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z") @ Matrix.Rotation(rng.uniform(0, 1), 4, "X")
        ico(f"crown{i}", r, leaf, place(s, (x, y, z)) @ rot)


def shadow_catcher(scene):
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.is_shadow_catcher = True
    return plane


def render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "trees")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)

    for kind, base in TREES.items():
        build = build_conifer if kind == "conifer" else build_deciduous
        for stage in range(7):
            sprite = base + stage
            for zoom in ZOOMS:
                # Tree pass.
                scene = reset_scene()
                oc.setup_camera(scene, zoom, 64 * zoom, 96 * zoom, anchor_y=ANCHOR_Y)
                build(stage, random.Random(sprite))
                render(scene, os.path.join(outdir, f"z{zoom}", f"{sprite}_tree.png"))

                # Shadow pass: same tree, invisible to the camera, casting onto a catcher.
                for obj in scene.collection.objects:
                    if obj.type == "MESH":
                        obj.visible_camera = False
                shadow_catcher(scene)
                st.add_shadow_sun(scene, angle_deg=14.0)
                render(scene, os.path.join(outdir, f"z{zoom}", f"{sprite}_shadow.png"))
                print(f"rendered {kind} sprite {sprite} stage {stage} zoom {zoom}x", flush=True)


if __name__ == "__main__":
    main()
