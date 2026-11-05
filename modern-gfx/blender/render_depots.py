"""Render rail depots (1063-1068), road depots (1408-1413) and tram depots (TRAMWAY 113-118) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_depots.py -- <outdir> [--only prefix,prefix]

The game draws a depot as one or two building sprites, each anchored at the
origin of its bounding box (see _depot_gfx_* in table/track_land.h and
_road_depot_* in table/road_land.h). Depots facing SE or SW are split: the
side wall behind the vehicle (NE resp. NW side) is a separate sprite so the
vehicle sorts between the parts. Geometry is modelled in OpenTTD tile units
(x, y 0-16) with u running from the door to the back and v across.

Two passes per sprite:
  <name>_overlay.png  colour
  <name>_cc.png       company-colour mask (white where the eaves band and door
                      trim are; the packer turns it into a recolour mask)
Canvas 192z x 144z px with the sprite origin at (95z, 80z).
"""

import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ottd_camera as oc  # noqa: E402
import style as st  # noqa: E402

ZOOMS = (1, 2, 4)
CANVAS_W, CANVAS_H, ANCHOR_Y = 192, 144, 80
Z_UNIT = oc.LEVEL / 8  # one OpenTTD height unit

WALL = (222, 214, 196)
WALL_INSIDE = (54, 58, 64)
ROOF = (96, 104, 112)
TRIM = (128, 128, 128)  # company colour parts are rendered neutral grey, see the cc pass
DOOR = (64, 70, 78)

# sprite: (kind, entrance, part, anchor in OpenTTD units)
SPRITES = {
    1063: ("rail", "SE", "side", (2, 2)), 1064: ("rail", "SE", "rest", (13, 2)),
    1065: ("rail", "SW", "side", (2, 2)), 1066: ("rail", "SW", "rest", (2, 13)),
    1067: ("rail", "NE", "all", (2, 13)), 1068: ("rail", "NW", "all", (13, 2)),
    1408: ("road", "SE", "side", (0, 0)), 1409: ("road", "SE", "rest", (15, 0)),
    1410: ("road", "SW", "side", (0, 0)), 1411: ("road", "SW", "rest", (0, 15)),
    1412: ("road", "NE", "all", (0, 15)), 1413: ("road", "NW", "all", (15, 0)),
}
# Tram depots (TRAMWAY 113-118, laid out like 1408-1413; 49-54 get the same images): a taller hall
# with a gable roof and an open gate, the tram track overlay on the ground runs inside.
SPRITES.update({f"tram{113 + k}": ("tram",) + SPRITES[1408 + k][1:] for k in range(6)})


def uv_to_xy(entrance, u, v):
    return {"NE": (u, v), "SW": (16 - u, v), "NW": (v, u), "SE": (v, 16 - u)}[entrance]


class Builder:
    def __init__(self, entrance, anchor, cc_pass):
        self.entrance = entrance
        self.anchor = anchor
        self.cc_pass = cc_pass
        self.materials = {}

    def mat(self, rgb, cc=False):
        key = (rgb, cc)
        if key not in self.materials:
            if self.cc_pass:
                self.materials[key] = st.toon_material("cc" if cc else "black", (255, 255, 255) if cc else (0, 0, 0),
                                                       params=st.FLAT)
            else:
                self.materials[key] = st.toon_material(str(rgb), rgb, params=st.WALL if rgb == WALL else st.OBJECT)
        return self.materials[key]

    def point(self, u, v, z):
        x, y = uv_to_xy(self.entrance, u, v)
        x -= self.anchor[0]
        y -= self.anchor[1]
        return oc.CORNERS["N"] + Vector((y / 16, -x / 16, z))

    def poly_mesh(self, name, faces, rgb, cc=False):
        bm = bmesh.new()
        for face in faces:
            bm.faces.new([bm.verts.new(p) for p in face])
        bm.normal_update()
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for p in mesh.polygons:
            p.use_smooth = False
        mesh.materials.append(self.mat(rgb, cc))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)

    def box(self, name, u0, u1, v0, v1, z0, z1, rgb, cc=False):
        c = [[[self.point(u, v, z) for z in (z0, z1)] for v in (v0, v1)] for u in (u0, u1)]
        faces = [
            [c[0][0][0], c[1][0][0], c[1][1][0], c[0][1][0]], [c[0][0][1], c[0][1][1], c[1][1][1], c[1][0][1]],
            [c[0][0][0], c[0][0][1], c[1][0][1], c[1][0][0]], [c[0][1][0], c[1][1][0], c[1][1][1], c[0][1][1]],
            [c[0][0][0], c[0][1][0], c[0][1][1], c[0][0][1]], [c[1][0][0], c[1][0][1], c[1][1][1], c[1][1][0]],
        ]
        self.poly_mesh(name, faces, rgb, cc)


def build(kind, entrance, part, anchor, cc_pass):
    b = Builder(entrance, anchor, cc_pass)
    if kind == "rail":
        u0, u1, v0, v1, wall_h, ridge, t = 1.0, 15.0, 2.0, 14.0, 0.36, 0.56, 0.7
        door_lo, door_hi = 4.5, 11.5
    elif kind == "tram":
        u0, u1, v0, v1, wall_h, ridge, t = 0.5, 15.5, 1.0, 15.0, 0.38, 0.6, 0.7
        door_lo, door_hi = 3.5, 12.5
    else:
        u0, u1, v0, v1, wall_h, ridge, t = 0.5, 15.5, 1.0, 15.0, 0.34, None, 0.7
        door_lo, door_hi = 3.0, 13.0
    side = part in ("side", "all")
    rest = part in ("rest", "all")
    if side:
        b.box("wall_lo", u0, u1, v0, v0 + t, 0, wall_h, WALL)
        b.box("wall_lo_in", u0 + t, u1 - t, v0 + t, v0 + t + 0.15, 0, wall_h - 0.02, WALL_INSIDE)
        b.box("band_lo", u0, u1, v0 - 0.1, v0 + t, wall_h - 0.035, wall_h, TRIM, cc=True)
    if not rest:
        return
    b.box("wall_hi", u0, u1, v1 - t, v1, 0, wall_h, WALL)
    b.box("wall_hi_in", u0 + t, u1 - t, v1 - t - 0.15, v1 - t, 0, wall_h - 0.02, WALL_INSIDE)
    b.box("band_hi", u0, u1, v1 - t, v1 + 0.1, wall_h - 0.035, wall_h, TRIM, cc=True)
    b.box("back", u1 - t, u1, v0, v1, 0, wall_h, WALL)
    b.box("back_in", u1 - t - 0.15, u1 - t, v0 + t, v1 - t, 0, wall_h - 0.02, WALL_INSIDE)
    door_top = wall_h * (0.84 if kind == "tram" else 0.78)
    b.box("front_lo", u0, u0 + t, v0, door_lo, 0, wall_h, WALL)
    b.box("front_hi", u0, u0 + t, door_hi, v1, 0, wall_h, WALL)
    b.box("lintel", u0, u0 + t, door_lo, door_hi, door_top, wall_h, WALL)
    b.box("trim", u0 - 0.1, u0 + 0.05, door_lo - 0.4, door_hi + 0.4, door_top - 0.03, door_top + 0.02, TRIM, cc=True)
    if kind == "tram":
        # Open gate: the roller door is rolled up under the lintel.
        b.box("door", u0 + 0.2, u0 + 0.45, door_lo, door_hi, door_top - 0.05, door_top, DOOR)
    if kind in ("rail", "tram"):
        # Gable roof along the track with overhangs, gable ends above the walls.
        ov, vm = 0.6, (v0 + v1) / 2
        eave = wall_h
        for name, va, vb in (("roof_a", v0 - ov, vm), ("roof_b", v1 + ov, vm)):
            b.poly_mesh(name, [[b.point(u0 - ov, va, eave - 0.03), b.point(u1 + ov, va, eave - 0.03),
                                b.point(u1 + ov, vb, ridge), b.point(u0 - ov, vb, ridge)]], ROOF)
        for name, u in (("gable_front", u0), ("gable_back", u1)):
            b.poly_mesh(name, [[b.point(u, v0, eave), b.point(u, v1, eave), b.point(u, vm, ridge - 0.02)]], WALL)
    else:
        # Flat roof with a parapet, and a closed roller door.
        b.box("roof", u0 - 0.2, u1 + 0.2, v0 - 0.2, v1 + 0.2, wall_h, wall_h + 0.03, ROOF)
        b.box("door", u0 + 0.2, u0 + 0.4, door_lo, door_hi, 0, door_top, DOOR)
        for i in range(1, 6):
            z = door_top * i / 6
            b.box(f"slat{i}", u0 + 0.1, u0 + 0.2, door_lo, door_hi, z - 0.004, z + 0.004, WALL_INSIDE)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "depots")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    only = tuple(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    for sprite, (kind, entrance, part, anchor) in SPRITES.items():
        if only and not str(sprite).startswith(only):
            continue
        for zoom in ZOOMS:
            for cc_pass in (False, True):
                bpy.ops.wm.read_factory_settings(use_empty=True)
                scene = bpy.context.scene
                st.configure_render(scene, samples=16 if cc_pass else 64)
                if cc_pass:
                    scene.cycles.filter_width = 0.01
                oc.setup_camera(scene, zoom, CANVAS_W * zoom, CANVAS_H * zoom, anchor_y=ANCHOR_Y)
                build(kind, entrance, part, anchor, cc_pass)
                suffix = "cc" if cc_pass else "overlay"
                scene.render.filepath = os.path.join(outdir, f"z{zoom}", f"depot{sprite}_{suffix}.png")
                bpy.ops.render.render(write_still=True)
        print(f"rendered depot {sprite}", flush=True)


if __name__ == "__main__":
    main()
