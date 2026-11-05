"""Render the temperate trees, low-poly, in all 7 OpenTTD growth stages.

Run:  Blender -b --factory-startup -P render_trees.py -- <outdir> [--only 1576,1583] [--zoom 2]

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
The canvas is 64z x 112z px with the drawing origin at pixel (31z, 80z); the tallest
trees (rainforest 0x74E, palm 0x76A) reach 76 px above it.

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
ANCHOR_Y = 80
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
    1660: ("column", dict(trunk=0.08, slim=0.72, lumps=6, shape="flame"), (54, 102, 76), (112, 98, 62), "spire",
           (112, 84, 58), TRUNK, {}),
    1667: ("column", dict(trunk=0.12, slim=0.7, lumps=7, shape="spindle"), (62, 112, 90), (80, 110, 84), "broom",
           (104, 96, 66), TRUNK, {}),
    1674: ("crown", dict(trunk=0.3, lumps=5, lump=0.5), (60, 112, 78), (214, 130, 48), "branches", (90, 70, 56), TRUNK, {}),
    1681: ("crown", dict(trunk=0.25, lumps=5, lump=0.55), (72, 114, 68), (212, 142, 62), "branches", (130, 70, 50), TRUNK, {}),
    1688: ("crown", dict(trunk=0.3, lumps=4, lump=0.5), (122, 172, 78), (208, 150, 72), "branches", (150, 146, 140), TRUNK,
           {"fruit": (206, 62, 48)}),
    1695: ("column", dict(trunk=0.18, round=True), (128, 182, 86), (186, 182, 92), "branches", (150, 146, 140), TRUNK, {}),
    1702: ("crown", dict(trunk=0.3, lumps=6, lump=0.45), (74, 132, 120), (118, 128, 96), "branches", (150, 92, 60), TRUNK, {}),
}

# Sub-arctic 0x6AD-0x6DE. The same eight species come again with snow at 0x6E5-0x716
# (above the snow line), built identically plus snow on the upward faces.
ARCTIC = {
    1709: ("tiers", dict(trunk=0.1, tiers=3, segments=7), (52, 104, 66), (122, 116, 58), "brown", (126, 100, 62),
           TRUNK_CONIFER, {}),
    1716: ("crown", dict(trunk=0.22, lumps=4, lump=0.45, stack=True), (78, 118, 74), (140, 132, 70), "branches",
           (150, 146, 140), TRUNK, {}),
    1723: ("crown", dict(trunk=0.28, lumps=5, lump=0.5), (164, 70, 56), (138, 92, 54), "branches", None, TRUNK, {}),
    1730: ("layers", dict(trunk=0.3, layers=4), (56, 116, 62), (170, 156, 70), "branches", None, TRUNK, {}),
    1737: ("spindle", dict(trunk=0.3, lumps=9), (62, 112, 84), (132, 112, 64), "brown", (140, 84, 52), TRUNK, {}),
    1744: ("tiers", dict(trunk=0.12, tiers=4, segments=7, gap=1.25), (44, 92, 66), (54, 96, 66), "brown",
           (78, 92, 64), TRUNK_CONIFER, {}),
    1751: ("column", dict(trunk=0.08, slim=0.8, lumps=6, shape="flame"), (58, 110, 58), (96, 112, 60), "spire",
           (112, 84, 58), TRUNK_CONIFER, {}),
    1758: ("tiers", dict(trunk=0.2, tiers=7, segments=6, gap=1.0, top=0.35), (54, 104, 70), (90, 104, 66), "brown",
           (110, 96, 64), PINE_BARK, {}),
}
SNOW = (236, 242, 246)
SNOWY = {b + 56: spec[:7] + ({**spec[7], "snow": True},) for b, spec in ARCTIC.items()}

PALM_TAN = (176, 128, 94)
PALM_DARK = (104, 66, 44)
PALE_BARK = (206, 204, 196)
FROND_DEAD = (128, 90, 48)
# Sub-tropical 0x71D-0x794: palms, rainforest, ferns and two cacti.
TROPIC = {
    1821: ("palm", dict(fronds=8, lean=0.08), (84, 150, 112), (140, 132, 62), "fronds", FROND_DEAD, PALM_TAN, {}),
    1828: ("palm", dict(fronds=9, lean=0.05), (48, 106, 66), (130, 122, 52), "fronds", FROND_DEAD, PALM_DARK, {}),
    1835: ("crown", dict(trunk=0.3, lumps=6, lump=0.48), (128, 166, 92), (178, 170, 98), "branches", (196, 164, 116),
           (168, 128, 82), {}),
    1842: ("crown", dict(trunk=0.3, lumps=6, lump=0.5), (82, 142, 40), (118, 150, 52), "branches", PALE_BARK,
           PALE_BARK, {"vines": (64, 120, 36)}),
    1849: ("fan", dict(fronds=9, rise=0.85, droop=-0.35, width=0.32), (44, 98, 56), (120, 116, 52), "fronds",
           FROND_DEAD, PALM_DARK, {}),
    1856: ("fan", dict(fronds=11, rise=1.05, droop=0.35, width=0.16), (120, 176, 64), (150, 146, 62), "fronds",
           FROND_DEAD, PALM_DARK, {}),
    1863: ("crown", dict(trunk=0.36, lumps=5, lump=0.5, stack=True), (60, 128, 72), (92, 140, 70), "branches",
           PALE_BARK, PALE_BARK, {}),
    1870: ("crown", dict(trunk=0.6, lumps=5, lump=0.6), (56, 112, 78), (96, 132, 70), "branches", PALE_BARK,
           PALE_BARK, {}),
    1877: ("crown", dict(trunk=0.3, lumps=5, lump=0.5), (72, 138, 44), (110, 150, 52), "branches", PALE_BARK,
           PALE_BARK, {}),
    1884: ("palm", dict(fronds=8, lean=0.0, bulb=True), (76, 146, 120), (140, 132, 62), "fronds", FROND_DEAD,
           (36, 82, 50), {}),
    1891: ("palm", dict(fronds=9, lean=0.04), (52, 112, 60), (130, 122, 52), "fronds", FROND_DEAD, PALM_DARK, {}),
    1898: ("palm", dict(fronds=8, lean=0.1), (50, 104, 62), (130, 122, 52), "fronds", FROND_DEAD, PALE_BARK, {}),
    1905: ("palm", dict(fronds=9, lean=0.03), (128, 182, 60), (150, 140, 60), "fronds", FROND_DEAD, PALM_TAN, {}),
    1912: ("cactus", dict(arms=2), (76, 116, 64), (104, 120, 60), "brown", (92, 112, 60), TRUNK, {}),
    1919: ("barrel", dict(), (84, 128, 70), (112, 126, 64), "brown", (110, 116, 64), TRUNK, {"flower": (232, 96, 132)}),
    1926: ("palm", dict(fronds=8, lean=0.16), (60, 124, 72), (136, 126, 56), "fronds", FROND_DEAD, PALM_TAN, {}),
    1933: ("crown", dict(trunk=0.25, lumps=6, lump=0.5), (88, 150, 128), (120, 150, 110), "branches", (142, 140, 136),
           (142, 140, 136), {}),
    1940: ("crown", dict(trunk=0.25, lumps=6, lump=0.5), (164, 114, 50), (176, 140, 70), "branches", PALE_BARK,
           TRUNK, {}),
}
SPECIES.update(ARCTIC)
SPECIES.update(SNOWY)
SPECIES.update(TROPIC)

# Toyland 0x79B-0x7D3: every base has its own builder (build_toy).
TOYS = {1947: "top", 1954: "candyfloss", 1961: "balloon", 1968: "tyres", 1975: "curl", 1982: "mushroom",
        1989: "cone", 1996: "lollipop", 2003: "pole"}

TREES = {1597: "spruce", 1604: "broadleaf", **{b: "species" for b in SPECIES}, **{b: "toy" for b in TOYS}}


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    st.configure_render(scene, samples=64)
    return scene


def add_mesh(name, bm, material, matrix):
    """material is one material, or a list indexed by the faces' material_index."""
    mesh = bpy.data.meshes.new(name)
    bm.transform(matrix)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False
    for m in (material if isinstance(material, list) else [material]):
        mesh.materials.append(m)
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


def segment(name, p0, p1, r0, r1, segments, material):
    """Cone from p0 to p1 (foot-relative points), radius r0 at p0 and r1 at p1."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    return cone(name, r0, r1, d.length, segments, material, place(1.0, p0) @ rot)


def frond(name, origin, azimuth, length, width, rise, droop, materials, steps=4):
    """A leaf blade with a raised midrib, arching from elevation angle rise to droop (radians).

    materials: one material, or [blade, midrib] for a two-coloured leaf.
    """
    out = Vector((math.cos(azimuth), math.sin(azimuth), 0))
    side = Vector((-math.sin(azimuth), math.cos(azimuth), 0))
    up = Vector((0, 0, 1))
    bm = bmesh.new()
    p = Vector(origin)
    rows = []
    for k in range(steps + 1):
        t = k / steps
        w = width * min(1.0, 0.35 + 2.5 * t) * (1.0 - t) ** 0.7
        rows.append([bm.verts.new(p + side * w - up * w * 0.3), bm.verts.new(p + up * w * 0.2),
                     bm.verts.new(p - side * w - up * w * 0.3)])
        e = rise + (droop - rise) * t
        p = p + (out * math.cos(e) + up * math.sin(e)) * (length / steps)
    two = isinstance(materials, list)
    for a, b in zip(rows, rows[1:]):
        for i in range(2):
            f = bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
            f.material_index = 0
    if two:
        # Midrib: a thin raised strip over the centre line.
        for a, b in zip(rows, rows[1:]):
            ca, cb = a[1].co, b[1].co
            wa = (a[0].co - ca).length * 0.35
            wb = (b[0].co - cb).length * 0.35
            vs = [bm.verts.new(ca + side * wa + up * 0.004), bm.verts.new(cb + side * wb + up * 0.004),
                  bm.verts.new(cb - side * wb + up * 0.004), bm.verts.new(ca - side * wa + up * 0.004)]
            bm.faces.new(vs).material_index = 1
    return add_mesh(name, bm, materials, place(1.0))


def torus(name, major, minor, material, matrix, segments=16, sides=6):
    bm = bmesh.new()
    rings = []
    for i in range(segments):
        a = i * math.tau / segments
        c = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c * (major + minor * math.cos(b)) + Vector((0, 0, minor * math.sin(b))))
                      for b in (j * math.tau / sides for j in range(sides))])
    for i in range(segments):
        r0, r1 = rings[i], rings[(i + 1) % segments]
        for j in range(sides):
            bm.faces.new((r0[j], r1[j], r1[(j + 1) % sides], r0[(j + 1) % sides]))
    return add_mesh(name, bm, material, matrix)


def apply_snow(rng):
    """Lay snow on every upward-facing facet; the steeper the facet, the patchier the snow."""
    snow = st.toon_material("snow", SNOW)
    for obj in list(bpy.context.scene.collection.objects):
        if obj.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
        bm.normal_update()
        idx = len(obj.data.materials)
        for f in bm.faces:
            if f.normal.z > -0.1 + 0.6 * rng.random():
                f.material_index = idx
        bm.to_mesh(obj.data)
        bm.free()
        for poly in obj.data.polygons:
            poly.use_smooth = False
        obj.data.materials.append(snow)


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


def bare_branches(height, radius, rng, material, count=5, lo=0.4):
    for i in range(count):
        a = i * math.tau / count + rng.uniform(-0.3, 0.3)
        tilt = Matrix.Rotation(rng.uniform(0.45, 0.8), 4, Vector((-math.sin(a), math.cos(a), 0)))
        length = rng.uniform(0.75, 1.0) * max(radius * 1.3, height * 0.3)
        cone(f"branch{i}", 0.018, 0.005, length, 5, material,
             place(1.0, (0, 0, height * rng.uniform(lo, lo + 0.15)), tilt=tilt))


def snag(height, radius, rng, material):
    for i in range(4):
        a = rng.uniform(0, math.tau)
        tilt = Matrix.Rotation(math.radians(80), 4, Vector((-math.sin(a), math.cos(a), 0)))
        cone(f"stub{i}", 0.014, 0.004, radius * 0.45, 4, material,
             place(1.0, (0, 0, height * rng.uniform(0.55, 0.9)), tilt=tilt))


def spire(height, radius, rng, material, remnant, upright=False):
    """Dead conifer or poplar: the bare stem with whorls of twigs that shorten towards the top.

    upright (poplar) keeps the twigs close to the stem, otherwise they stand out
    and only slightly up. A few clumps of dead needles cling to the twig ends.
    """
    levels = 8
    for k in range(levels):
        t = k / (levels - 1)
        z = height * (0.18 + 0.72 * t)
        for j in range(3):
            a = rng.uniform(0, math.tau)
            out = Vector((math.cos(a), math.sin(a), 0))
            lean = rng.uniform(0.25, 0.4) if upright else rng.uniform(0.9, 1.15)
            d = out * math.sin(lean) + Vector((0, 0, math.cos(lean)))
            length = radius * (1.25 - 0.9 * t) * rng.uniform(0.75, 1.05) * (1.6 if upright else 1.0)
            if upright:
                length = max(length, height * 0.12)
            tip = Vector((0, 0, z)) + d * length
            segment(f"twig{k}_{j}", (0, 0, z), tip, 0.011, 0.003, 4, material)
            if rng.random() < 0.4:
                c = radius * 0.3
                ico(f"needles{k}_{j}", 1.0, remnant, place(1.0, tip - d * length * 0.35)
                    @ Matrix.Rotation(a, 4, "Z") @ Matrix.Diagonal((c, c * 0.7, c * 0.45, 1)), subdiv=0)


SCREEN_LEFT = math.radians(225)  # world azimuth that points left on screen


def palm(spec, stage, height, radius, colour, rng):
    """Curved, slightly tapering trunk with a crown of arching fronds; dead fronds hang down."""
    params, trunk_rgb = spec[1], spec[6]
    trunk = st.toon_material("trunk", trunk_rgb)
    leaf = st.toon_material("leaf", colour)
    length = radius * 1.6
    top = height - length * 0.3
    lean = Vector((math.cos(SCREEN_LEFT), math.sin(SCREEN_LEFT), 0)) * params["lean"] * height
    r0 = max(0.024, radius * 0.12)
    if params.get("bulb"):
        ico("bulb", 1.0, trunk, place(1.0, (0, 0, top * 0.32)) @ Matrix.Diagonal((radius * 0.42, radius * 0.42, top * 0.34, 1)))
        r0 *= 0.75
    pts = [lean * (k / 6) ** 1.6 + Vector((0, 0, top * k / 6)) for k in range(7)]
    for k in range(6):
        segment(f"trunk{k}", pts[k], pts[k + 1], r0 * (1 - 0.06 * k), r0 * (0.94 - 0.06 * k), 6, trunk)
    crown = pts[-1]
    dead = stage == 6
    n = params["fronds"] - (3 if dead else 0)
    for i in range(n):
        a = i * math.tau / n + rng.uniform(-0.25, 0.25)
        rise = rng.uniform(-0.1, 0.2) if dead else rng.uniform(0.35, 0.7)
        droop = rng.uniform(-1.4, -1.1) if dead else rng.uniform(-0.7, -0.3)
        frond(f"frond{i}", crown, a, length * rng.uniform(0.85, 1.05) * (0.8 if dead else 1.0), length * 0.17,
              rise, droop, leaf)
    if not dead:
        for i in range(3):
            frond(f"shoot{i}", crown, i * math.tau / 3 + rng.uniform(0, 1), length * 0.55, length * 0.12, 1.25, 0.7, leaf)
    ico("heart", r0 * 1.5, st.toon_material("heart", mix(colour, (52, 40, 26), 0.6)), place(1.0, crown), subdiv=0)


def fan(spec, stage, height, radius, colour, rng):
    """Ground-level fronds: ferns (broad, arching) and agave-like grasses (narrow, stiff)."""
    params = spec[1]
    leaf = st.toon_material("leaf", colour)
    dead = stage == 6
    n = params["fronds"]
    for i in range(n):
        a = i * math.tau / n + rng.uniform(-0.2, 0.2)
        length = radius * rng.uniform(1.5, 1.8)
        rise = params["rise"] * (0.6 if dead else 1.0) + rng.uniform(-0.1, 0.1)
        droop = params["droop"] - (0.5 if dead else 0.0)
        frond(f"frond{i}", (0, 0, 0.01), a, length, length * params["width"], rise, droop, leaf)


def cactus(spec, stage, height, radius, colour, rng):
    """Saguaro: ribbed column with arms that grow in as it ages."""
    green = st.toon_material("cactus", colour)
    r = max(0.03, radius * 0.4)
    top = height - r * 1.155
    segment("column", (0, 0, 0), (0, 0, top), r, r * 0.92, 8, green)
    ico("cap", r * 0.92, green, place(1.0, (0, 0, top)))
    arms = {0: 0, 1: 1}.get(stage, spec[1]["arms"])
    for i in range(arms):
        a = SCREEN_LEFT + math.pi * i + rng.uniform(-0.25, 0.25)
        out = Vector((math.cos(a), math.sin(a), 0))
        z0 = top * (0.4 + 0.15 * i)
        ra = r * 0.65
        elbow = out * radius * 0.85 + Vector((0, 0, z0 + ra))
        segment(f"arm{i}", (0, 0, z0), elbow, ra, ra, 8, green)
        ico(f"elbow{i}", ra, green, place(1.0, elbow))
        tip = elbow + Vector((0, 0, (top - z0) * (0.45 if stage > 1 else 0.25)))
        segment(f"armup{i}", elbow, tip, ra, ra * 0.92, 8, green)
        ico(f"armcap{i}", ra * 0.92, green, place(1.0, tip))


def barrel(spec, stage, height, radius, colour, rng):
    """Small barrel cactus that flowers when grown."""
    green = st.toon_material("cactus", colour)
    r = radius * 0.85
    h = height - r * 0.5
    ico("body", 1.0, green, place(1.0, (0, 0, h * 0.5)) @ Matrix.Diagonal((r, r, h * 0.5, 1)), subdiv=1)
    if stage in (2, 3, 4):
        flower = st.toon_material("flower", spec[7]["flower"])
        for i in range(3 if stage != 2 else 1):
            a = i * math.tau / 3
            ico(f"flower{i}", r * 0.3, flower, place(1.0, (math.cos(a) * r * 0.3, math.sin(a) * r * 0.3, h * 0.98)),
                subdiv=0)


TOY_GREEN = (86, 156, 58)
TOY_BLUE = (58, 112, 204)
TOY_RED = (150, 44, 48)
TOY_BROWN = (84, 54, 36)


def ref_box(base, stage):
    """Height above the foot and own crown radius of a toyland sprite (no growth scaling)."""
    e = json.load(open(REF_META))[str(base + stage)]
    return (6 - e["y"]) / PX_PER_UNIT_Z, e["w"] / PX_PER_UNIT_XY / 2 * 0.9, e


def striped_cone(name, r1, r2, depth, segments, materials, matrix):
    """Cone whose side faces alternate between two materials, like a spinning top."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r1, radius2=r2, depth=depth)
    bm.transform(Matrix.Translation((0, 0, depth / 2)))
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        f.material_index = 0 if abs(f.normal.z) > 0.99 else int((math.atan2(c.y, c.x) % math.tau) / (math.tau / segments)) % 2
    return add_mesh(name, bm, materials, matrix)


def build_toy(base, stage, rng):
    kind = TOYS[base]
    h, r, e = ref_box(base, stage)
    mat = st.toon_material
    if kind in ("top", "cone"):
        first = {4: mix(TOY_GREEN, TOY_RED, 0.5), 5: TOY_RED, 6: mix(TOY_RED, TOY_BROWN, 0.4)}.get(stage, TOY_GREEN)
        second = TOY_BLUE if stage < 6 else mix(TOY_BLUE, TOY_BROWN, 0.4)
        stripes = [mat("stripe_a", first), mat("stripe_b", second)]
        foot = h * (0.18 if kind == "top" else 0.1)
        segment("trunk", (0, 0, 0), (0, 0, foot + 0.02), 0.03, 0.025, 6, mat("trunk", TOY_BROWN))
        if kind == "top":
            body = h - foot - r * 0.35
            striped_cone("body", r * 0.08, r, body, 16, stripes, place(1.0, (0, 0, foot)))
            striped_cone("lid", r, 0.0, r * 0.3, 16, stripes, place(1.0, (0, 0, foot + body)))
        else:
            striped_cone("body", r, 0.0, h - foot, 16, stripes, place(1.0, (0, 0, foot)))
    elif kind == "candyfloss":
        stick = mat("stick", (70, 136, 214))
        if stage < 2:
            segment("stick", (0, 0, 0), (0, 0, h), 0.022, 0.02, 6, stick)
            return
        zc = h - r * 1.1
        segment("stick", (0, 0, 0), (0, 0, zc), 0.022, 0.02, 6, stick)
        floss = {5: (240, 150, 140), 6: (206, 206, 206)}.get(stage, (246, 188, 180))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        for v in bm.verts:
            v.co *= rng.uniform(0.9, 1.06)
        add_mesh("floss", bm, mat("floss", floss), place(1.0, (0, 0, zc)))
    elif kind == "balloon":
        if stage == 6:
            return  # burst: nothing left
        rb = r * 0.95
        zc = (6 - e["y"] - rb * 1.15 * PX_PER_UNIT_XY) / PX_PER_UNIT_Z
        colour = {4: (52, 104, 190), 5: (46, 90, 166)}.get(stage, (66, 130, 220))
        squash = 0.85 if stage == 5 else 1.15
        ico("balloon", 1.0, mat("balloon", colour), place(1.0, (0, 0, zc)) @ Matrix.Diagonal((rb, rb, rb * squash, 1)),
            subdiv=2)
        knot = zc - rb * squash
        cone("knot", 0.012, 0.0, 0.03, 5, mat("knot", colour), place(1.0, (0, 0, knot - 0.03)))
        string = mat("string", (150, 128, 82))
        bottom = max(0.0, (6 - e["y"] - e["h"]) / PX_PER_UNIT_Z)
        pts = [Vector((0.015 * math.sin(k * 1.7), 0.015 * math.cos(k * 1.3), knot - 0.03 - (knot - 0.03 - bottom) * k / 5))
               for k in range(6)]
        if stage == 5:
            pts += [Vector((0.06, -0.04, 0.005)), Vector((0.1, 0.03, 0.005))]
        for k in range(len(pts) - 1):
            segment(f"string{k}", pts[k], pts[k + 1], 0.005, 0.005, 4, string)
    elif kind == "tyres":
        post = mat("post", (164, 164, 160))
        rp = r * 0.45
        segment("post", (0, 0, 0), (0, 0, h - rp * 0.6), rp, rp, 10, post)
        ico("post_top", 1.0, mat("post_top", (214, 214, 210)), place(1.0, (0, 0, h - rp * 0.6))
            @ Matrix.Diagonal((rp, rp, rp * 0.15, 1)), subdiv=1)
        rubber = mat("tyre", (34, 34, 38))
        minor = r * 0.28
        heights = {0: (0.62,), 4: (0.3, 0.52), 5: (0.0, 0.3), 6: ()}.get(stage, (0.42, 0.66))
        for i, f in enumerate(heights):
            torus(f"tyre{i}", r - minor, minor, rubber, place(1.0, (0, 0, max(minor, h * f))))
    elif kind == "curl":
        wire_c = (140, 84, 40)
        grey = (164, 164, 164)
        n = 28
        hw = h - (0.05 if stage in (3, 4) else 0.0)
        pts = [Vector((0.045 * math.cos(k * 0.6), 0.045 * math.sin(k * 0.6), hw * k / n)) for k in range(n + 1)]
        for k in range(n):
            greyed = stage == 6 or (stage == 5 and k > n // 2)
            segment(f"wire{k}", pts[k], pts[k + 1], 0.016, 0.016, 5, mat(f"wire{k}", grey if greyed else wire_c))
        if stage in (3, 4):
            halo = (90, 160, 236) if stage == 3 else (214, 214, 214)
            torus("halo", 0.075, 0.012, mat("halo", halo), place(1.0, (0, 0, h - 0.02)))
        elif stage == 5:
            torus("halo", 0.075, 0.012, mat("halo", (200, 200, 200)),
                  place(1.0, (0, 0, h * 0.45)) @ Matrix.Rotation(0.9, 4, "X"))
    elif kind == "mushroom":
        stem_c = (226, 226, 220) if stage < 4 else (214, 168, 78)
        cap_c = TOY_BLUE if stage < 4 else (40, 72, 156)
        cap_h = h * 0.32
        zc = h - cap_h - r * 0.35
        segment("stem", (0, 0, 0), (0, 0, zc + cap_h * 0.2), r * 0.3, r * 0.2, 8, mat("stem", stem_c))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_inner=True)
        bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)
        if stage == 6:
            for v in bm.verts:
                v.co *= rng.uniform(0.8, 1.05)
        add_mesh("cap", bm, mat("cap", cap_c), place(1.0, (0, 0, zc)) @ Matrix.Diagonal((r, r, cap_h, 1)))
        if stage < 6:
            spot = mat("spot", (236, 238, 244))
            for i in range(7):
                a, el = rng.uniform(0, math.tau), rng.uniform(0.25, 1.0)
                p = Vector((r * math.cos(el) * math.cos(a), r * math.cos(el) * math.sin(a), zc + cap_h * math.sin(el)))
                ico(f"spot{i}", 1.0, spot, place(1.0, p) @ Matrix.Diagonal((r * 0.13, r * 0.13, r * 0.06, 1)), subdiv=0)
    elif kind == "lollipop":
        trunk = mat("trunk", (72, 50, 34))
        if stage == 6:
            segment("trunk", (0, 0, 0), (0, 0, h), 0.05, 0.05, 8, trunk)
            return
        zc = h - r * 1.155
        segment("trunk", (0, 0, 0), (0, 0, zc), 0.045, 0.04, 8, trunk)
        ball = {4: (84, 134, 50), 5: (106, 128, 54)}.get(stage, (74, 142, 46))
        ico("ball", r, mat("ball", ball), place(1.0, (0, 0, zc)), subdiv=2)
    elif kind == "pole":
        segment("pole", (0, 0, 0), (0, 0, h - 0.02), 0.045, 0.045, 8, mat("pole", (150, 72, 52)))
        ico("pole_top", 1.0, mat("pole_top", (176, 96, 72)), place(1.0, (0, 0, h - 0.02))
            @ Matrix.Diagonal((0.045, 0.045, 0.01, 1)), subdiv=1)
        _, rg, _ = ref_box(base, 3)
        leaf_c = {5: (128, 128, 58), 6: (120, 92, 48)}.get(stage, (84, 150, 52))
        mats = [mat("leaf", leaf_c), mat("rib", TOY_BLUE if stage < 6 else (100, 80, 60))]
        pairs = (0, 1, 2, 3, 3, 2, 1)[stage]
        for k in range(pairs):
            z = h * (0.8 - 0.26 * k) if stage < 5 else h * (0.25 + 0.2 * k)
            for side in (0, 1):
                a = SCREEN_LEFT + math.pi * side + rng.uniform(-0.15, 0.15)
                rise, droop = (0.1, -0.9) if stage == 6 else (0.3, -0.25)
                frond(f"leaf{k}_{side}", (0, 0, z), a, rg * 1.3, rg * 0.3, rise, droop, mats)
        if stage in (3, 4):
            for side in (0, 1):
                frond(f"sprig{side}", (0, 0, h * 0.84), SCREEN_LEFT + math.pi / 2 + math.pi * side, rg * 0.5,
                      rg * 0.12, 0.9, 0.3, mats)


def build_species(base, stage, rng):
    species_body(base, stage, rng)
    if SPECIES[base][7].get("snow"):
        apply_snow(rng)


def species_body(base, stage, rng):
    spec = SPECIES[base]
    form, params, _, _, dead_style, _, trunk_rgb, extras = spec
    height, radius = ref_size(base, stage)
    colour = stage_colour(spec, stage)
    if form in ("palm", "fan", "cactus", "barrel"):
        {"palm": palm, "fan": fan, "cactus": cactus, "barrel": barrel}[form](spec, stage, height, radius, colour, rng)
        return
    dead = stage == 6 and dead_style in ("branches", "snag", "spire", "broom")
    dead_wood = spec[5] or BARE_WOOD
    bare = dead_style == "branches" or (dead and dead_style in ("spire", "broom"))
    trunk_mat = st.toon_material("trunk", (BARE_WOOD if dead_style in ("spire", "broom") else dead_wood)
                                 if stage == 6 and bare else trunk_rgb)
    lo = max(0.4, params["trunk"])
    trunk_h = height * (params["trunk"] + (0.25 if form == "crown" else 0.1))
    if form in ("layers", "spindle"):
        trunk_h = height * 0.9
    if dead:
        trunk_h = height * (0.95 if dead_style in ("snag", "spire", "broom") else lo + 0.2)
    cone("trunk", max(0.03, radius * 0.12), 0.022 if dead_style != "spire" or not dead else 0.008, trunk_h, 6,
         trunk_mat, place(1.0))
    if dead:
        if dead_style == "branches":
            bare_branches(height, radius, rng, trunk_mat, lo=lo)
        elif dead_style == "snag":
            snag(height, radius, rng, trunk_mat)
        else:
            spire(height, radius, rng, trunk_mat, st.toon_material("remnant", dead_wood), upright=dead_style == "broom")
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
        if "vines" in extras:
            vine = st.toon_material("vine", mix(extras["vines"], colour, 0.3 if stage < 4 else 0.7))
            for i in range(9):
                a = i * math.tau / 9 + rng.uniform(-0.2, 0.2)
                p = centre + Vector((math.cos(a) * radius * 0.7, math.sin(a) * radius * 0.7, -rv * 0.35))
                cone(f"vine{i}", 0.018, 0.004, rv * rng.uniform(0.5, 0.8), 4, vine,
                     place(1.0, p) @ Matrix.Rotation(math.pi, 4, "X"))
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
            h = span / n * params.get("gap", 1.9)
            r = radius * (1.0 - (1.0 - params.get("top", 0.4)) * i / max(1, n - 1))
            cone(f"tier{i}", r, 0.0, min(h, height - z), params["segments"], leaf,
                 place(1.0, (0, 0, z), rot_z=rng.uniform(0, math.tau)))
    elif form == "column" and params.get("round"):
        rv = (height - bottom) / 2
        ico("column", 1.0, leaf, place(1.0, (0, 0, bottom + rv)) @ Matrix.Diagonal((radius, radius, rv, 1)), subdiv=2)
    elif form == "column":
        # Cypress / poplar: a slim column of overlapping foliage lumps and a pointed tip.
        # flame: widest low down, tapering to the tip; spindle: widest in the middle.
        r_max = radius * params["slim"]
        n = params["lumps"]
        tip_h = (height - bottom) * 0.2
        top = height - tip_h * 0.6
        rz = (top - bottom) / n * 0.95
        for i in range(n):
            t = i / (n - 1)
            if params["shape"] == "flame":
                f = 0.8 + 0.2 * t / 0.3 if t < 0.3 else 1.0 - 0.6 * ((t - 0.3) / 0.7) ** 1.5
            else:
                f = 0.6 + 0.4 * math.sin(math.pi * (0.2 + 0.75 * t))
            r = r_max * f
            p = Vector((rng.uniform(-0.12, 0.12) * r_max, rng.uniform(-0.12, 0.12) * r_max,
                        bottom + rz + t * (top - bottom - 2 * rz)))
            rot = Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z")
            ico(f"lump{i}", 1.0, leaf, place(1.0, p) @ rot @ Matrix.Diagonal((r, r * 0.85, rz * 1.25, 1)))
        cone("tip", r_max * 0.4, 0.0, tip_h, 6, leaf, place(1.0, (0, 0, height - tip_h)))
    elif form == "layers":
        # Cloud pine: flat foliage pads on short side branches.
        n = params["layers"]
        for i in range(n):
            t = i / (n - 1)
            z = bottom + (height - bottom) * (0.08 + 0.8 * t)
            r = radius * (1.0 - 0.55 * t)
            a = i * 2.4 + rng.uniform(-0.3, 0.3)
            off = Vector((math.cos(a), math.sin(a), 0)) * radius * 0.4 * (1 - 0.5 * t)
            segment(f"limb{i}", (0, 0, z - 0.03), off + Vector((0, 0, z)), 0.014, 0.008, 4, trunk_mat)
            ico(f"pad{i}", 1.0, leaf, place(1.0, off + Vector((0, 0, z))) @ Matrix.Rotation(a, 4, "Z")
                @ Matrix.Diagonal((r * 0.85, r * 0.7, (height - bottom) / n * 0.32, 1)))
    elif form == "spindle":
        # Tall thin tree with small leaf clumps up the whole stem.
        n = params["lumps"]
        for i in range(n):
            t = i / (n - 1)
            a = i * 2.2 + rng.uniform(-0.4, 0.4)
            r = radius * (0.9 - 0.4 * t)
            p = Vector((math.cos(a) * radius * 0.25, math.sin(a) * radius * 0.25,
                        bottom + (height - bottom - r) * t + r * 0.5))
            ico(f"lump{i}", 1.0, leaf, place(1.0, p) @ Matrix.Diagonal((r, r, r * 0.9, 1)))
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
    zooms = ZOOMS
    if "--zoom" in argv:  # previews: render only these zoom levels
        zooms = tuple(int(z) for z in argv[argv.index("--zoom") + 1].split(","))
    for zoom in zooms:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)

    only = None
    if "--only" in argv:
        only = {int(b) for b in argv[argv.index("--only") + 1].split(",")}
    for base, kind in TREES.items():
        if only and base not in only:
            continue
        build = {"spruce": build_conifer, "broadleaf": build_deciduous,
                 "toy": lambda stage, rng, base=base: build_toy(base, stage, rng)}.get(
            kind, lambda stage, rng, base=base: build_species(base, stage, rng))
        for stage in range(7):
            sprite = base + stage
            for zoom in zooms:
                # Tree pass.
                scene = reset_scene()
                oc.setup_camera(scene, zoom, 64 * zoom, 112 * zoom, anchor_y=ANCHOR_Y)
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
