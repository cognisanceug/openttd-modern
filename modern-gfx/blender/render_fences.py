"""Render the eight track fence sprites (1301-1308) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_fences.py -- <outdir>

The game draws each fence sprite at a point inside the tile (see fence_offsets
in rail_cmd.cpp), so every fence is modelled relative to that point, which the
render puts on the usual sprite origin (the tile's north corner):
  1301 FLAT_X     along OpenTTD x (N -> W), drawn at (0, 1) or (0, 15)
  1302 FLAT_Y     along OpenTTD y (N -> E), drawn at (1, 0) or (15, 0)
  1303 FLAT_VERT  along the N-S diagonal, centred on the tile centre
  1304 FLAT_HORZ  along the W-E diagonal, centred on the tile centre
  1305-1308       along x or y on the slopes SW, SE, NE, NW (rising with the slope)
Low-poly post-and-rail fence in weathered wood.
Output: <outdir>/z<zoom>/fence<sprite>_overlay.png
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ottd_camera as oc  # noqa: E402
import style as st  # noqa: E402

ZOOMS = (1, 2, 4)
POST_RGB = (124, 100, 78)
RAIL_RGB = (156, 130, 100)
HEIGHT = 0.13
POSTS_PER_TILE = 4

N = oc.CORNERS["N"]
X_DIR = Vector((0, -1, 0))  # OpenTTD +x
Y_DIR = Vector((1, 0, 0))   # OpenTTD +y
L = oc.LEVEL

# sprite: (start relative to N corner, direction vector incl. rise, posts)
FENCES = {
    1301: (Vector((0, 0, 0)), X_DIR, POSTS_PER_TILE),
    1302: (Vector((0, 0, 0)), Y_DIR, POSTS_PER_TILE),
    # Diagonals: centred on the anchor (the tile centre in game).
    1303: (-(oc.CORNERS["S"] - N) / 2, oc.CORNERS["S"] - N, 6),
    1304: (-(oc.CORNERS["E"] - oc.CORNERS["W"]) / 2, oc.CORNERS["E"] - oc.CORNERS["W"], 6),
    1305: (Vector((0, 0, 0)), X_DIR + Vector((0, 0, L)), POSTS_PER_TILE),   # SLOPE_SW: W raised
    1306: (Vector((0, 0, 0)), Y_DIR + Vector((0, 0, L)), POSTS_PER_TILE),   # SLOPE_SE: E raised
    1307: (Vector((0, 0, L)), X_DIR + Vector((0, 0, -L)), POSTS_PER_TILE),  # SLOPE_NE: N raised
    1308: (Vector((0, 0, L)), Y_DIR + Vector((0, 0, -L)), POSTS_PER_TILE),  # SLOPE_NW: N raised
}


def add_box(name, centre, size, rot, material):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.transform(Matrix.Translation(centre) @ rot @ Matrix.Diagonal((*size, 1)))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)


def build(start, direction, posts):
    post_mat = st.toon_material("post", POST_RGB)
    rail_mat = st.toon_material("rail", RAIL_RGB)
    a = N + start
    flat = Vector((direction.x, direction.y, 0))
    yaw = math.atan2(flat.y, flat.x)
    for i in range(posts + 1):
        p = a + direction * (i / posts)
        add_box(f"post{i}", p + Vector((0, 0, HEIGHT / 2)), (0.022, 0.022, HEIGHT),
                Matrix.Rotation(yaw, 4, "Z"), post_mat)
    length = direction.length
    pitch = math.atan2(direction.z, flat.length)
    rot = Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(-pitch, 4, "Y")
    for h in (0.55, 0.9):
        mid = a + direction / 2 + Vector((0, 0, HEIGHT * h))
        add_box(f"rail{h}", mid, (length, 0.012, 0.016), rot, rail_mat)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "fences")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    for sprite, (start, direction, posts) in FENCES.items():
        for zoom in ZOOMS:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            scene = bpy.context.scene
            st.configure_render(scene)
            oc.setup_camera(scene, zoom, 64 * zoom, 64 * zoom)
            build(start, direction, posts)
            scene.render.filepath = os.path.join(outdir, f"z{zoom}", f"fence{sprite}_overlay.png")
            bpy.ops.render.render(write_still=True)
        print(f"rendered fence {sprite}", flush=True)


if __name__ == "__main__":
    main()
