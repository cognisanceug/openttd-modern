"""Render the temperate ground tiles (sprites 3924-4060) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_ground.py -- <outdir> [--style calibration|modern] [--kinds a,b]

Kinds (each covers the 19 slope shapes in OpenTTD's order, see SPRITE_SLOPES):
  bare     3924  cleared soil
  grass13  3943  soil, 1/3 grass
  grass23  3962  soil, 2/3 grass
  grass    3981  meadow
  rough    4000  rough land; plus 4019-4022, four flat variants
  rocky1   4023  rocky land
  rocky2   4042  rocky land, second set (different boulder layout)

Styles: "calibration" is a lit 8x8 checker for checking geometry and seams;
"modern" uses the textures from tools/make_ground_textures.py (render/textures)
with the shared style shader from style.py, plus low-poly scatter objects
(tufts on rough land, boulders on rocky land) standing on the slope surface.

For every sprite and zoom two images are written:
  <outdir>/z<zoom>/<sprite>_color.png  surface rendered slightly enlarged, so edge
                                       pixels carry real surface colour
  <outdir>/z<zoom>/<sprite>_mask.png   exact footprint, sampled at pixel centres
The packer combines them: colour from the first, alpha from the second.
Scatter objects are cut off at the tile outline by that mask.
"""

import math
import os
import random
import shutil
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ottd_camera as oc  # noqa: E402
import style as st  # noqa: E402

ZOOMS = (1, 2, 4)
COLOR_OVERSCAN = 1.06  # surface enlargement for the colour pass
TEXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render", "textures")

# name: (first sprite, texture, scatter)
KINDS = {
    "bare": (3924, "bare", None),
    "grass13": (3943, "grass13", None),
    "grass23": (3962, "grass23", None),
    "grass": (3981, "grass", None),
    "rough": (4000, "rough", "tufts"),
    "rocky1": (4023, "rocky", "rocks"),
    "rocky2": (4042, "rocky", "rocks"),
}
ROUGH_FLAT_VARIANTS = (4019, 4020, 4021, 4022)

TUFT_COLORS = ((90, 150, 76), (116, 178, 82), (104, 164, 78), (186, 196, 104))
SHRUB_COLOR = (78, 140, 92)
ROCK_COLORS = ((138, 134, 126), (120, 118, 112), (156, 150, 140))


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "ground")
    style = argv[argv.index("--style") + 1] if "--style" in argv else "modern"
    kinds = argv[argv.index("--kinds") + 1].split(",") if "--kinds" in argv else list(KINDS)
    return outdir, style, kinds


def jobs(kinds):
    """(sprite, slope, kind, seed) for every sprite to render."""
    out = []
    for kind in kinds:
        first = KINDS[kind][0]
        out += [(first + k, slope, kind, first + k) for k, slope in enumerate(oc.SPRITE_SLOPES)]
        if kind == "rough":
            out += [(s, 0, kind, s) for s in ROUGH_FLAT_VARIANTS]
    return out


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    st.configure_render(scene)
    return scene


def tile_geometry(slope):
    """Corner heights (levels), fold diagonal and the two surface triangles as corner names."""
    h = oc.slope_corner_levels(slope)
    fold = oc.slope_fold(h)
    a, b = ("W", "E") if fold == "WE" else ("N", "S")
    others = [c for c in "NESW" if c not in (a, b)]
    return h, (a, b), [(a, b, o) for o in others]


def surface_z(slope, x, y):
    """Height of the tile surface at world (x, y), matching the rendered triangles."""
    h, _, tris = tile_geometry(slope)
    for tri in tris:
        p = [oc.CORNERS[c] for c in tri]
        det = (p[1].y - p[2].y) * (p[0].x - p[2].x) + (p[2].x - p[1].x) * (p[0].y - p[2].y)
        l0 = ((p[1].y - p[2].y) * (x - p[2].x) + (p[2].x - p[1].x) * (y - p[2].y)) / det
        l1 = ((p[2].y - p[0].y) * (x - p[2].x) + (p[0].x - p[2].x) * (y - p[2].y)) / det
        l2 = 1 - l0 - l1
        if min(l0, l1, l2) >= -1e-9:
            return (l0 * h[tri[0]] + l1 * h[tri[1]] + l2 * h[tri[2]]) * oc.LEVEL
    raise ValueError("point outside tile")


def build_tile(slope, scale=1.0):
    """Two-triangle tile surface for a slope, uniformly scaled about the fold midpoint.

    Scaling about the fold midpoint extends both triangle planes outwards, so an
    enlarged tile still has exactly the original surface inside the tile area.
    """
    h, (a, b), _ = tile_geometry(slope)
    mid_z = (h[a] + h[b]) / 2.0 * oc.LEVEL

    order = ["N", "E", "S", "W"]
    verts = []
    for c in order:
        v = oc.CORNERS[c].copy()
        v.z = h[c] * oc.LEVEL
        v.x *= scale
        v.y *= scale
        v.z = mid_z + (v.z - mid_z) * scale
        verts.append(v)
    idx = {c: i for i, c in enumerate(order)}
    if (a, b) == ("W", "E"):
        faces = [(idx["W"], idx["E"], idx["N"]), (idx["E"], idx["W"], idx["S"])]
    else:
        faces = [(idx["N"], idx["S"], idx["E"]), (idx["S"], idx["N"], idx["W"])]
    # Counter-clockwise seen from above so normals point up.
    faces = [f if _ccw(verts, f) else tuple(reversed(f)) for f in faces]

    mesh = bpy.data.meshes.new(f"tile_{slope}")
    mesh.from_pydata([tuple(v) for v in verts], [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"tile_{slope}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _ccw(verts, f):
    a, b, c = (verts[i] for i in f)
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x) > 0


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


def scatter_points(rng, count, margin):
    """Random points inside the tile, keeping `margin` from the edges."""
    lim = 0.5 - margin
    return [(rng.uniform(-lim, lim), rng.uniform(-lim, lim)) for _ in range(count)]


def add_tufts(slope, rng, count, materials):
    for i, (x, y) in enumerate(scatter_points(rng, count, 0.09)):
        r = rng.uniform(0.022, 0.04)
        hgt = rng.uniform(0.035, 0.07)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=r, radius2=0.0, depth=hgt)
        bm.transform(Matrix.Translation((0, 0, hgt / 2 - 0.004)))
        m = Matrix.Translation((x, y, surface_z(slope, x, y))) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z")
        add_mesh(f"tuft{i}", bm, rng.choice(materials), m)


def add_shrubs(slope, rng, count, material):
    for i, (x, y) in enumerate(scatter_points(rng, count, 0.14)):
        r = rng.uniform(0.04, 0.06)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        m = (Matrix.Translation((x, y, surface_z(slope, x, y) + r * 0.45))
             @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z") @ Matrix.Diagonal((1, 1, 0.8, 1)))
        add_mesh(f"shrub{i}", bm, material, m)


def add_rocks(slope, rng, count, materials):
    placed = []
    for i in range(count * 4):
        if len(placed) >= count:
            break
        r = rng.uniform(0.045, 0.11)
        (x, y), = scatter_points(rng, 1, 0.08 + r)
        if any((x - px) ** 2 + (y - py) ** 2 < (r + pr) ** 2 for px, py, pr in placed):
            continue
        placed.append((x, y, r))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        rot = (Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z") @ Matrix.Rotation(rng.uniform(-0.4, 0.4), 4, "X"))
        m = (Matrix.Translation((x, y, surface_z(slope, x, y) - r * 0.25)) @ rot
             @ Matrix.Diagonal((r * rng.uniform(1.0, 1.4), r, r * rng.uniform(0.55, 0.8), 1)))
        add_mesh(f"rock{i}", bm, rng.choice(materials), m)


def add_scatter(kind, slope, seed):
    scatter = KINDS[kind][2]
    rng = random.Random(seed)
    if scatter == "tufts":
        mats = [st.toon_material(f"tuft{i}", c) for i, c in enumerate(TUFT_COLORS)]
        add_tufts(slope, rng, 34, mats)
        add_shrubs(slope, rng, 3, st.toon_material("shrub", SHRUB_COLOR))
    elif scatter == "rocks":
        mats = [st.toon_material(f"rock{i}", c) for i, c in enumerate(ROCK_COLORS)]
        add_rocks(slope, rng, rng.randint(6, 9), mats)
        add_tufts(slope, rng, 10, [st.toon_material("tuft", TUFT_COLORS[0])])


def calibration_material():
    """8x8 checker per tile in world XY (continuous across tiles), lit by a sun."""
    mat = bpy.data.materials.new("calibration")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Location"].default_value = (0.5, 0.5, 0.0)
    mapping.inputs["Scale"].default_value = (8.0, 8.0, 0.0)
    checker = nt.nodes.new("ShaderNodeTexChecker")
    checker.inputs["Scale"].default_value = 1.0
    checker.inputs["Color1"].default_value = (0.16, 0.32, 0.08, 1.0)
    checker.inputs["Color2"].default_value = (0.11, 0.24, 0.05, 1.0)
    nt.links.new(geo.outputs["Position"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], checker.inputs["Vector"])
    nt.links.new(checker.outputs["Color"], bsdf.inputs["Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def add_calibration_lighting(scene):
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.6, 0.7, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.15
    sun_data = bpy.data.lights.new("sun", "SUN")
    sun_data.energy = 4.0
    sun_data.angle = math.radians(10)
    sun = bpy.data.objects.new("sun", sun_data)
    # Light from the screen's left (from Blender -X-Y), 30 deg above the horizon.
    sun.rotation_euler = (math.radians(60), 0.0, math.radians(-45))
    scene.collection.objects.link(sun)


def mask_material():
    mat = bpy.data.materials.new("mask")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    outdir, style, kinds = parse_args()
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)

    masks = {}  # (slope, zoom) -> first rendered mask path; masks only depend on the slope
    for sprite, slope, kind, seed in jobs(kinds):
        for zoom in ZOOMS:
            size = 64 * zoom
            zdir = os.path.join(outdir, f"z{zoom}")

            # Colour pass: enlarged surface, normal anti-aliasing.
            scene = reset_scene()
            oc.setup_camera(scene, zoom, size, size)
            obj = build_tile(slope, COLOR_OVERSCAN)
            if style == "modern":
                tex = os.path.join(TEXTURES, KINDS[kind][1] + ".png")
                obj.data.materials.append(st.toon_material("ground", image_path=tex, params=st.GROUND))
                add_scatter(kind, slope, seed)
            else:
                add_calibration_lighting(scene)
                obj.data.materials.append(calibration_material())
            render(scene, os.path.join(zdir, f"{sprite}_color.png"))

            # Mask pass: exact surface, point sampling at pixel centres.
            mask_path = os.path.join(zdir, f"{sprite}_mask.png")
            if (slope, zoom) in masks:
                shutil.copyfile(masks[slope, zoom], mask_path)
            else:
                scene = reset_scene()
                oc.setup_camera(scene, zoom, size, size)
                obj = build_tile(slope, 1.0)
                obj.data.materials.append(mask_material())
                scene.cycles.samples = 16
                scene.cycles.filter_width = 0.01
                render(scene, mask_path)
                masks[slope, zoom] = mask_path
        print(f"rendered {kind} sprite {sprite} slope {slope:#04x}", flush=True)


if __name__ == "__main__":
    main()
