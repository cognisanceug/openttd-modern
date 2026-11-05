"""Render the temperate ground tiles (sprites 3924-4060) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_ground.py -- <outdir> [--style calibration|modern] [--kinds a,b]

Kinds (each covers the 19 slope shapes in OpenTTD's order, see SPRITE_SLOPES):
  bare     3924  cleared soil
  grass13  3943  soil, 1/3 grass
  grass23  3962  soil, 2/3 grass
  grass    3981  meadow
  rough    4000  rough land; plus 4019-4022, four flat variants with their own texture (rough1-4)
  rocky1   4023  rocky land
  rocky2   4042  rocky land, second set (own texture rocky2 and boulder layout)
  farm0-8  4126+19k farm field stages (bare, sown ... golden, stubble, hay bales)
  snow1-4, desert1-4  4493+19(k-1) snow / desert densities; only on request, into
           their own outdir (the sprite numbers are shared by both climates)
  toybare, toygrass13, toygrass23, toygrass, toyrough, toyrocky1, toyrocky2, toyshore
           toyland ground: the same sprites as bare ... rocky2 (and the shores), from the toy_*
           textures, with pompoms on rough land and toy blocks and marbles on rocky land;
           only on request, into their own outdir (render/toyland)
Water kinds (output files are named after the sprite slot, not a base sprite):
  water    4061      open water (sea, lakes, flat river), unshaded
  shore    shore0-17 Action 5 COAST block; index -> slope as in DrawShoreTile()
  river    river0-3  first four sprites of the Action 5 CANAL block: river slopes
  coastrocks coastrock0-18  overlay rocks on water and coast (Action 5 OVERLAY_ROCKS,
           offset 95), in slope order; rendered without the tile, which only occludes
  infra    rail1005-1036, road1313-1350, cross1370-1381, apron2634, bay2692-2711, tram4-45: rails, roads, level
           crossings and concrete from tools/make_infra_textures.py (render/textures/infra),
           on the flat tile or the slope the sprite is drawn on; 1005-1010 are
           overlays without ground
  riverbank bank0-59 river edges for our own canal-feature definition: 12 pieces
           (sides NE, SE, SW, NW; outer and inner corners E, S, W, N) for flat
           river tiles and for the slopes SE, NE, SW, NW (offsets 0/12/24/36/48)
  canaldike dike0-11 canal edges (stone quay) for our own canal-feature definition,
           same 12 pieces as the river banks, flat only

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

# name: (first sprite, texture, scatter)
KINDS = {
    "bare": (3924, "bare", None),
    "grass13": (3943, "grass13", None),
    "grass23": (3962, "grass23", None),
    "grass": (3981, "grass", None),
    "rough": (4000, "rough", "tufts"),
    "rocky1": (4023, "rocky", "rocks"),
    "rocky2": (4042, "rocky2", "rocks"),
}
# Farm fields 4126-4296: nine stages in _clear_land_sprites_farmland order (textures
# field0-8 from make_fields()); the last stage carries hay bales.
FIELD_KINDS = {f"farm{k}": (4126 + 19 * k, f"field{k}", "bales" if k == 8 else None) for k in range(9)}
KINDS.update(FIELD_KINDS)
# Snow (arctic) and desert (tropic) both use 4493-4568, four densities x 19 slopes. They
# are never in the default kind list; render each into its own outdir (render/snow,
# render/desert), as the sprite numbers collide.
CLIMATE_KINDS = {f"{c}{k}": (4493 + 19 * (k - 1), f"{c}{k}", None) for c in ("snow", "desert") for k in range(1, 5)}
# Toyland: same sprite numbers as the temperate kinds, so render into render/toyland.
TOY_KINDS = {"toybare": (3924, "toy_bare", None), "toygrass13": (3943, "toy_grass13", None),
             "toygrass23": (3962, "toy_grass23", None), "toygrass": (3981, "toy_grass", None),
             "toyrough": (4000, "toy_rough", "pompoms"), "toyrocky1": (4023, "toy_rocky", "blocks"),
             "toyrocky2": (4042, "toy_rocky2", "blocks")}
CLIMATE_KINDS.update(TOY_KINDS)
ROUGH_FLAT_VARIANTS = (4019, 4020, 4021, 4022)
WATER_KINDS = ("water", "shore", "river", "coastrocks", "riverbank", "canaldike", "infra")
# Sloped track sprites 1023-1034 (offset from 1011 -> slope), see _track_sloped_sprites.
RAIL_SLOPES = {12: 8, 13: 4, 14: 1, 15: 2, 16: 14, 17: 7, 18: 11, 19: 13, 20: 12, 21: 6, 22: 3, 23: 9}
ROAD_SLOPES = {11: 12, 12: 6, 13: 3, 14: 9}  # road sprite offset -> slope NE, SE, SW, NW


def infra_jobs():
    """(name, slope, overlay) for every rail, road and level-crossing sprite."""
    out = [(f"rail{s}", 0, True) for s in range(1005, 1011)]
    out += [(f"rail{s}", RAIL_SLOPES.get(s - 1011, 0), False) for s in range(1011, 1037)]
    for base in (1313, 1332):
        out += [(f"road{base + k}", ROAD_SLOPES.get(k, 0), False) for k in range(19)]
    out += [(f"cross{s}", 0, False) for s in range(1370, 1382)]
    out += [("apron2634", 0, False)]
    out += [(f"bay{s}", 0, False) for s in list(range(2692, 2696)) + list(range(2708, 2712))]
    # Tram tracks: overlays on roads (TRAMWAY 4-22) and tram-only ground (27-45).
    out += [(f"tram{4 + k}", ROAD_SLOPES.get(k, 0), True) for k in range(19)]
    out += [(f"tram{27 + k}", ROAD_SLOPES.get(k, 0), False) for k in range(19)]
    return out
BANK_SLOPES = (0, 6, 12, 3, 9)  # flat, SE, NE, SW, NW as in DrawRiverWater()
WET_ROCK_COLORS = ((112, 112, 108), (128, 126, 120), (100, 104, 104))
# Shore sprite index -> slope (inverse of tileh_to_shoresprite in water_cmd.cpp).
SHORE_SLOPES = (0x17, 1, 2, 3, 4, 0x1B, 6, 7, 8, 9, 0x1D, 11, 12, 13, 14, 0x1E, 5, 10)
# Canal block 0-3: water flowing to -Y (SLOPE_SE), +X (SLOPE_NE), -X (SLOPE_SW), +Y (SLOPE_NW).
RIVER_SLOPES = (6, 12, 3, 9)

TUFT_COLORS = ((90, 150, 76), (116, 178, 82), (104, 164, 78), (186, 196, 104))
SHRUB_COLOR = (78, 140, 92)
ROCK_COLORS = ((138, 134, 126), (120, 118, 112), (156, 150, 140))
# Toyland scatter: grass tufts in the felt greens, candy pompoms, toy blocks, pink pebbles.
TOY_TUFT_COLORS = ((92, 168, 84), (112, 194, 104), (104, 182, 90))
CANDY_COLORS = ((240, 136, 166), (248, 208, 92), (122, 182, 234), (186, 150, 222))
BLOCK_COLORS = ((222, 92, 98), (246, 200, 84), (90, 150, 224), (238, 236, 228), (120, 196, 120))
PEBBLE_COLORS = ((212, 118, 140), (232, 156, 170), (186, 96, 118))


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "ground")
    style = argv[argv.index("--style") + 1] if "--style" in argv else "modern"
    kinds = argv[argv.index("--kinds") + 1].split(",") if "--kinds" in argv else list(KINDS) + list(WATER_KINDS)
    # --only a,b: render only sprites whose name starts with one of these prefixes
    only = tuple(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    return outdir, style, kinds, only


def jobs(kinds):
    """(sprite, slope, kind, seed) for every sprite to render."""
    out = []
    for kind in kinds:
        if kind == "water":
            out.append((4061, 0, kind, 4061))
            continue
        if kind in ("shore", "toyshore"):
            out += [(f"shore{i}", slope, kind, 5000 + i) for i, slope in enumerate(SHORE_SLOPES)]
            continue
        if kind == "river":
            out += [(f"river{i}", slope, kind, 6000 + i) for i, slope in enumerate(RIVER_SLOPES)]
            continue
        if kind == "coastrocks":
            out += [(f"coastrock{i}", slope, kind, 7000 + i) for i, slope in enumerate(oc.SPRITE_SLOPES)]
            continue
        if kind == "riverbank":
            out += [(f"bank{v * 12 + k}", slope, kind, k) for v, slope in enumerate(BANK_SLOPES) for k in range(12)]
            continue
        if kind == "canaldike":
            out += [(f"dike{k}", 0, kind, k) for k in range(12)]
            continue
        if kind == "infra":
            out += [(name, slope, kind, name) for name, slope, _ in infra_jobs()]
            continue
        first = {**KINDS, **CLIMATE_KINDS}[kind][0]
        out += [(first + k, slope, kind, first + k) for k, slope in enumerate(oc.SPRITE_SLOPES)]
        if kind in ("rough", "toyrough"):
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


def add_foam_ring(x, y, z, r, material):
    """Flat foam ring on the water surface around a rock."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=r * 1.35)
    add_mesh("foam", bm, material, Matrix.Translation((x, y, z + 0.002)))


def add_rocks(slope, rng, count, materials, foam=None, spread=False):
    """Boulders; with spread, mostly small stones that may come close to the tile edges."""
    placed = []
    for i in range(count * 4):
        if len(placed) >= count:
            break
        if spread:
            # A few big boulders, many small stones; small ones get near the edges,
            # so the boulders of neighbouring tiles do not line up in a grid.
            r = rng.uniform(0.07, 0.11) if len(placed) < 2 else rng.uniform(0.025, 0.06)
            (x, y), = scatter_points(rng, 1, 0.015 + 1.25 * r)
        else:
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


HAY_COLOR = (214, 184, 108)


def add_bales(slope, rng, count, material):
    """Round hay bales lying on the field, axis along the furrows (world X)."""
    placed = []
    for i in range(count * 6):
        if len(placed) >= count:
            break
        r, depth = 0.05, 0.075
        (x, y), = scatter_points(rng, 1, 0.1)
        if any((x - px) ** 2 + (y - py) ** 2 < (2.6 * r) ** 2 for px, py in placed):
            continue
        placed.append((x, y))
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r, depth=depth)
        m = (Matrix.Translation((x, y, surface_z(slope, x, y) + r * 0.9))
             @ Matrix.Rotation(rng.uniform(-0.3, 0.3), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y"))
        add_mesh(f"bale{i}", bm, material, m)


def holdout_material():
    mat = bpy.data.materials.new("holdout")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(nt.nodes.new("ShaderNodeHoldout").outputs[0], out.inputs["Surface"])
    return mat


def foam_material():
    """Half-transparent foam, after the map study's shoreline foam."""
    mat = bpy.data.materials.new("foam")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = st.lin(st.FOAM_RGB)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.5
    nt.links.new(nt.nodes.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


def render_coast_rocks(outdir, name, slope, seed, zoom):
    """Overlay: rocks only; the tile surface is a holdout so sunk parts stay hidden."""
    size = 64 * zoom
    scene = reset_scene()
    oc.setup_camera(scene, zoom, size, size)
    build_tile(slope, 1.0).data.materials.append(holdout_material())
    rng = random.Random(seed)
    mats = [st.toon_material(f"wetrock{i}", c) for i, c in enumerate(WET_ROCK_COLORS)]
    add_rocks(slope, rng, rng.randint(3, 5), mats, foam=foam_material())
    render(scene, os.path.join(outdir, f"z{zoom}", f"{name}_overlay.png"))


def ground_material(kind, piece=None):
    tex = st.texture
    if kind == "water":
        return st.toon_material("water", image_path=tex("water"), params=st.FLAT)
    if kind == "river":
        return st.toon_material("river", image_path=tex("water"), params=st.GROUND)
    if kind == "shore":
        return st.shore_material(tex("water"), tex("sand"), tex("grass"))
    if kind == "toyshore":
        return st.shore_material(tex("water"), tex("sand"), tex("toy_grass"))
    if kind == "riverbank":
        return st.bank_material(tex(f"riverbank{piece}"))
    if kind == "canaldike":
        return st.bank_material(tex(f"canaldike{piece}"))
    if kind == "infra":
        path = tex(f"infra/{piece}")
        if piece in {n for n, _, overlay in infra_jobs() if overlay}:
            return st.bank_material(path)
        return st.toon_material("infra", image_path=path, params=st.GROUND, extension="EXTEND")
    name = {**KINDS, **CLIMATE_KINDS}[kind][1]
    if kind in ("rough", "toyrough") and piece in ROUGH_FLAT_VARIANTS:
        name = f"{name}{ROUGH_FLAT_VARIANTS.index(piece) + 1}"  # own texture variant, see make_rough_rocky()
    return st.toon_material("ground", image_path=tex(name), params=st.GROUND)


def add_blocks(slope, rng, count, materials):
    """Toy building blocks: cubes and a few long bricks, turned and slightly sunk into the ground."""
    placed = []
    for i in range(count * 6):
        if len(placed) >= count:
            break
        r = rng.uniform(0.03, 0.045)
        (x, y), = scatter_points(rng, 1, 0.04 + 1.5 * r)
        if any((x - px) ** 2 + (y - py) ** 2 < (1.6 * (r + pr)) ** 2 for px, py, pr in placed):
            continue
        placed.append((x, y, r))
        sx = r * (2.0 if rng.random() < 0.3 else 1.0)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0)
        m = (Matrix.Translation((x, y, surface_z(slope, x, y) + r * 0.8))
             @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z") @ Matrix.Diagonal((sx, r, r, 1)))
        add_mesh(f"block{i}", bm, rng.choice(materials), m)


def add_marbles(slope, rng, count, materials):
    for i, (x, y) in enumerate(scatter_points(rng, count, 0.06)):
        r = rng.uniform(0.02, 0.03)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        add_mesh(f"marble{i}", bm, rng.choice(materials), Matrix.Translation((x, y, surface_z(slope, x, y) + r * 0.8)))


def add_scatter(kind, slope, seed):
    scatter = {**KINDS, **TOY_KINDS}[kind][2] if kind in KINDS or kind in TOY_KINDS else None
    rng = random.Random(seed)
    if scatter == "tufts":
        mats = [st.toon_material(f"tuft{i}", c) for i, c in enumerate(TUFT_COLORS)]
        add_tufts(slope, rng, 34, mats)
        add_shrubs(slope, rng, 3, st.toon_material("shrub", SHRUB_COLOR))
    elif scatter == "bales":
        add_bales(slope, rng, rng.randint(3, 5), st.toon_material("hay", HAY_COLOR))
    elif scatter == "rocks":
        mats = [st.toon_material(f"rock{i}", c) for i, c in enumerate(ROCK_COLORS)]
        add_rocks(slope, rng, rng.randint(7, 11), mats, spread=True)
        add_tufts(slope, rng, 10, [st.toon_material("tuft", TUFT_COLORS[0])])
    elif scatter == "pompoms":
        add_tufts(slope, rng, 30, [st.toon_material(f"tuft{i}", c) for i, c in enumerate(TOY_TUFT_COLORS)])
        candy = [st.toon_material(f"candy{i}", c) for i, c in enumerate(CANDY_COLORS)]
        for i, (x, y) in enumerate(scatter_points(rng, rng.randint(2, 4), 0.12)):
            r = rng.uniform(0.035, 0.05)
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
            m = (Matrix.Translation((x, y, surface_z(slope, x, y) + r * 0.6))
                 @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z"))
            add_mesh(f"pompom{i}", bm, rng.choice(candy), m)
    elif scatter == "blocks":
        pebbles = [st.toon_material(f"pebble{i}", c) for i, c in enumerate(PEBBLE_COLORS)]
        add_rocks(slope, rng, rng.randint(5, 8), pebbles, spread=True)
        add_blocks(slope, rng, rng.randint(2, 4), [st.toon_material(f"block{i}", c) for i, c in enumerate(BLOCK_COLORS)])
        add_marbles(slope, rng, rng.randint(1, 3), [st.toon_material(f"marble{i}", c) for i, c in enumerate(CANDY_COLORS)])


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
    outdir, style, kinds, only = parse_args()
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)

    masks = {}  # (slope, zoom) -> first rendered mask path; masks only depend on the slope
    for sprite, slope, kind, seed in jobs(kinds):
        if only and not str(sprite).startswith(only):
            continue
        if kind == "coastrocks":
            for zoom in ZOOMS:
                render_coast_rocks(outdir, sprite, slope, seed, zoom)
            print(f"rendered {kind} {sprite} slope {slope:#04x}", flush=True)
            continue
        for zoom in ZOOMS:
            size = 64 * zoom
            zdir = os.path.join(outdir, f"z{zoom}")

            # Colour pass: enlarged surface, normal anti-aliasing.
            scene = reset_scene()
            oc.setup_camera(scene, zoom, size, size)
            obj = build_tile(slope, COLOR_OVERSCAN)
            if style == "modern":
                obj.data.materials.append(ground_material(kind, seed))
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
        print(f"rendered {kind} {sprite} slope {slope:#04x}", flush=True)


if __name__ == "__main__":
    main()
