"""Render the temperate trees, low-poly, in all 7 OpenTTD growth stages.

Run:  Blender -b --factory-startup -P render_trees.py -- <outdir> [--only 1576,1583]

Every OpenGFX temperate tree sprite base (0x628-0x6AD, 7 sprites each) gets its
own species. The first two, spruce (0x63D) and broadleaf (0x644), have
hand-tuned builders; the others come from the SPECIES table and one of five
generic forms (crown, tiers, column, umbrella) with a dead style. Height and
width of the grown tree, and the size of every growth stage relative to it,
come from the OpenGFX sprites (ref/trees/meta.json), so forests keep their
proportions. 0x6AD repeats 0x63D in OpenGFX and is packed from the spruce.
Stages: 0-2 growing, 3 grown, 4-5 dying, 6 dead.

The tree's foot stands where OpenGFX trees have their trunk: 2.5/16 tile east
and 3.5/16 tile south-west of the drawing origin (sprite pixel (-2, +6) at 1x).
The canvas is 64z x 96z px with the drawing origin at pixel (31z, 64z).

For every sprite and zoom two images are written:
  <outdir>/z<zoom>/<sprite>_tree.png    the tree itself
  <outdir>/z<zoom>/<sprite>_shadow.png  its cast shadow on flat ground (shadow catcher alpha)
"""

import json
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

REF_META = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ref", "trees", "meta.json")
PX_PER_UNIT_Z = 39.19     # 1x screen px per world unit of height (cos 30 deg / pixel size)
PX_PER_UNIT_XY = 45.25    # 1x screen px per world unit across the screen
TRUNK = (98, 76, 58)
BIRCH_BARK = (220, 216, 204)
PINE_BARK = (150, 96, 66)

# base sprite: (form, form params, leaf, dying colour, dead style, dead colour, trunk, extras)
SPECIES = {
    1576: ("crown", dict(trunk=0.2, lumps=3, lump=0.5), (150, 198, 92), (226, 198, 74), "branches", (222, 218, 206), BIRCH_BARK, {}),
    1583: ("crown", dict(trunk=0.18, lumps=5, lump=0.55), (78, 132, 62), (170, 138, 64), "brown", (132, 100, 60), TRUNK, {}),
    1590: ("umbrella", dict(trunk=0.62), (62, 110, 86), (110, 112, 72), "snag", None, PINE_BARK, {}),
    1611: ("crown", dict(trunk=0.2, lumps=4, lump=0.45, stack=True), (112, 170, 82), (192, 178, 92), "branches", None, TRUNK, {}),
    1618: ("crown", dict(trunk=0.3, lumps=6, lump=0.5), (84, 134, 62), (164, 132, 62), "branches", None, TRUNK, {}),
    1625: ("tiers", dict(trunk=0.1, tiers=4, segments=8), (60, 114, 84), (100, 112, 72), "brown", (120, 96, 66), TRUNK, {}),
    1632: ("crown", dict(trunk=0.3, lumps=3, lump=0.5), (170, 78, 60), (150, 92, 62), "branches", None, TRUNK, {}),
    1639: ("tiers", dict(trunk=0.12, tiers=5, segments=7), (58, 106, 84), (70, 108, 80), "brown", (96, 98, 72), TRUNK, {}),
    1646: ("crown", dict(trunk=0.3, lumps=4, lump=0.5), (170, 162, 82), (196, 126, 70), "branches", None, TRUNK, {}),
    1653: ("crown", dict(trunk=0.3, lumps=3, lump=0.5), (218, 176, 62), (222, 146, 50), "branches", (124, 82, 58), TRUNK, {}),
    1660: ("column", dict(trunk=0.1), (54, 102, 76), (112, 98, 62), "brown", (134, 82, 52), TRUNK, {}),
    1667: ("column", dict(trunk=0.15), (62, 112, 90), (80, 110, 84), "snag", None, TRUNK, {}),
    1674: ("crown", dict(trunk=0.3, lumps=5, lump=0.5), (60, 112, 78), (214, 130, 48), "branches", (90, 70, 56), TRUNK, {}),
    1681: ("crown", dict(trunk=0.25, lumps=5, lump=0.55), (72, 114, 68), (212, 142, 62), "branches", (130, 70, 50), TRUNK, {}),
    1688: ("crown", dict(trunk=0.3, lumps=4, lump=0.5), (122, 172, 78), (208, 150, 72), "branches", (150, 146, 140), TRUNK,
           {"fruit": (206, 62, 48)}),
    1695: ("column", dict(trunk=0.18, round=True), (128, 182, 86), (186, 182, 92), "branches", (150, 146, 140), TRUNK, {}),
    1702: ("crown", dict(trunk=0.3, lumps=6, lump=0.45), (74, 132, 120), (118, 128, 96), "branches", (150, 92, 60), TRUNK, {}),
}
TREES = {1597: "spruce", 1604: "broadleaf", **{b: "species" for b in SPECIES}}


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


def ref_size(base, stage):
    """World height and crown radius of a stage, from the OpenGFX sprite it replaces.

    OpenGFX trees stand 6 px below the sprite origin at 1x, so height = 6 - y_offs.
    """
    meta = json.load(open(REF_META))
    e = meta[str(base + stage)]
    grown = meta[str(base + 3)]
    height = (6 - e["y"]) / PX_PER_UNIT_Z
    radius = grown["w"] / PX_PER_UNIT_XY / 2 * 0.9 * height / ((6 - grown["y"]) / PX_PER_UNIT_Z)
    return height, radius


def stage_colour(spec, stage):
    _, _, leaf, dying, dead_style, dead, _, _ = spec
    if stage <= 3:
        return leaf
    if stage == 4:
        return mix(leaf, dying, 0.4)
    if stage == 5:
        return mix(leaf, dying, 0.85)
    return dead or dying


def bare_branches(height, radius, rng, material, count=5):
    for i in range(count):
        a = i * math.tau / count + rng.uniform(-0.3, 0.3)
        tilt = Matrix.Rotation(rng.uniform(0.45, 0.8), 4, Vector((-math.sin(a), math.cos(a), 0)))
        length = rng.uniform(0.75, 1.0) * max(radius * 1.3, height * 0.3)
        cone(f"branch{i}", 0.018, 0.005, length, 5, material,
             place(1.0, (0, 0, height * rng.uniform(0.4, 0.55)), tilt=tilt))


def snag(height, radius, rng, material):
    for i in range(4):
        a = rng.uniform(0, math.tau)
        tilt = Matrix.Rotation(math.radians(80), 4, Vector((-math.sin(a), math.cos(a), 0)))
        cone(f"stub{i}", 0.014, 0.004, radius * 0.45, 4, material,
             place(1.0, (0, 0, height * rng.uniform(0.55, 0.9)), tilt=tilt))


def build_species(base, stage, rng):
    spec = SPECIES[base]
    form, params, _, _, dead_style, _, trunk_rgb, extras = spec
    height, radius = ref_size(base, stage)
    colour = stage_colour(spec, stage)
    dead = stage == 6 and dead_style in ("branches", "snag")
    dead_wood = spec[5] or BARE_WOOD
    trunk_mat = st.toon_material("trunk", dead_wood if stage == 6 and dead_style == "branches" else trunk_rgb)
    trunk_h = height * (params["trunk"] + (0.25 if form == "crown" else 0.1))
    if dead:
        trunk_h = height * (0.95 if dead_style == "snag" else 0.6)
    cone("trunk", max(0.03, radius * 0.12), 0.022, trunk_h, 6, trunk_mat, place(1.0))
    if dead:
        (bare_branches if dead_style == "branches" else snag)(height, radius, rng, trunk_mat)
        return
    leaf = st.toon_material("leaf", colour)
    bottom = height * params["trunk"]
    if form == "crown":
        rv = (height - bottom) / 2
        centre = Vector((0, 0, bottom + rv))
        ico("crown", 1.0, leaf, place(1.0, centre) @ Matrix.Diagonal((radius * 0.8, radius * 0.8, rv * 0.85, 1)))
        for i in range(params["lumps"]):
            if params.get("stack"):
                t = (i + 0.5) / params["lumps"]
                p = Vector((rng.uniform(-0.2, 0.2) * radius, rng.uniform(-0.2, 0.2) * radius, bottom + t * 2 * rv))
                r = params["lump"] * radius * (1.1 - 0.4 * t)
            else:
                a, e = rng.uniform(0, math.tau), rng.uniform(-0.2, 0.9)
                p = centre + Vector((math.cos(a) * math.cos(e) * radius * 0.5,
                                     math.sin(a) * math.cos(e) * radius * 0.5, math.sin(e) * rv * 0.5))
                r = params["lump"] * radius * rng.uniform(0.85, 1.1)
            rot = Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z") @ Matrix.Rotation(rng.uniform(0, 1), 4, "X")
            ico(f"lump{i}", r, leaf, place(1.0, p) @ rot)
        if "fruit" in extras and stage in (3, 4):
            fruit = st.toon_material("fruit", extras["fruit"])
            for i in range(9):
                a, e = rng.uniform(0, math.tau), rng.uniform(-0.3, 0.6)
                p = centre + Vector((math.cos(a) * math.cos(e) * radius * 0.85,
                                     math.sin(a) * math.cos(e) * radius * 0.85, math.sin(e) * rv * 0.9))
                ico(f"fruit{i}", 0.022, fruit, place(1.0, p), subdiv=0)
    elif form == "tiers":
        n = params["tiers"]
        span = height - bottom
        for i in range(n):
            z = bottom + span * i / n * 0.85
            h = span / n * 1.9
            r = radius * (1.0 - 0.6 * i / max(1, n - 1))
            cone(f"tier{i}", r, 0.0, min(h, height - z), params["segments"], leaf,
                 place(1.0, (0, 0, z), rot_z=rng.uniform(0, math.tau)))
    elif form == "column":
        rv = (height - bottom) / 2
        sub = 2 if params.get("round") else 1
        ico("column", 1.0, leaf, place(1.0, (0, 0, bottom + rv)) @ Matrix.Diagonal((radius, radius, rv, 1)), subdiv=sub)
    elif form == "umbrella":
        top = height * 0.82
        for i in range(4):
            a = i * math.tau / 4 + rng.uniform(-0.4, 0.4)
            p = Vector((math.cos(a) * radius * 0.45, math.sin(a) * radius * 0.45, top + rng.uniform(-0.05, 0.05) * height))
            r = radius * rng.uniform(0.45, 0.6)
            ico(f"cloud{i}", 1.0, leaf, place(1.0, p) @ Matrix.Diagonal((r, r, r * 0.5, 1)))
        ico("cloudtop", 1.0, leaf, place(1.0, (0, 0, height * 0.9)) @ Matrix.Diagonal((radius * 0.5, radius * 0.5, radius * 0.3, 1)))


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

    only = None
    if "--only" in argv:
        only = {int(b) for b in argv[argv.index("--only") + 1].split(",")}
    for base, kind in TREES.items():
        if only and base not in only:
            continue
        build = {"spruce": build_conifer, "broadleaf": build_deciduous}.get(
            kind, lambda stage, rng, base=base: build_species(base, stage, rng))
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
