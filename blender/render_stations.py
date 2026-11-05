"""Render rail stations, road stops and waypoints at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_stations.py -- <outdir>

Every sprite is a part the game draws at the origin of its bounding box (see
table/station_land.h); geometry is modelled in tile units (x, y 0-16, z in
height units, 8 per level) inside that box and the box origin becomes the
sprite origin.

  1069-1086  rail station: platforms (rear y 0-5 / front y 11-16 for the X
             axis, swapped for Y), building, roof pillars, roof frame at z 16
             and roof glass (drawn by the game with the transparency palette)
  2696-2707  bus bay parts A, B, C per entrance NE, SE, SW, NW
  2712-2723  truck bay parts
  rs0-rs7    drive-through stops (Action 5 ROAD_STOPS): bus Y W/E, X W/E, truck alike
  rw0-rw3    road waypoints (Action 5 ROAD_WAYPOINTS): Y W/E, X W/E
  wp0-wp3    rail waypoints (OTTD_GUI 78-81): X 1/2, Y 1/2

Two passes per sprite: <name>_overlay.png (colour) and <name>_cc.png
(company-colour mask). Canvas 128z x 128z, sprite origin at (63z, 72z).
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
CANVAS, ANCHOR_Y = 128, 72
UNIT = oc.LEVEL / 8

PLATFORM_SIDE = (170, 166, 158)
PLATFORM_TOP = (208, 204, 194)
SAFETY = (236, 200, 60)
WALL = (222, 214, 196)
WINDOW = (120, 150, 172)
ROOF = (96, 104, 112)
STEEL = (130, 136, 144)
CC = (128, 128, 128)
GLASS = (176, 206, 224)
WOOD = (150, 118, 84)
WHITE = (236, 236, 230)
RED = (210, 56, 48)
CRATE = (176, 142, 96)
DOOR = (64, 70, 78)


class Part:
    """Geometry in tile units relative to an anchor (the bounding box origin)."""

    def __init__(self, anchor, cc_pass, swap=False):
        """anchor and geometry are given in the X-axis frame; swap mirrors both onto the Y axis."""
        self.anchor = (anchor[1], anchor[0], anchor[2]) if swap else anchor
        self.cc = cc_pass
        self.swap = swap
        self.mats = {}

    def p(self, x, y, z):
        if self.swap:
            x, y = y, x
        x -= self.anchor[0]
        y -= self.anchor[1]
        return oc.CORNERS["N"] + Vector((y / 16, -x / 16, (z - self.anchor[2]) * UNIT))

    def mat(self, rgb, cc=False, glass=False):
        key = (rgb, cc, glass)
        if key not in self.mats:
            if self.cc:
                m = st.toon_material("m", (255, 255, 255) if cc else (0, 0, 0), params=st.FLAT)
            elif glass:
                m = glass_material(rgb)
            else:
                m = st.toon_material(str(rgb), rgb, params=st.WALL if rgb == WALL else st.OBJECT)
            self.mats[key] = m
        return self.mats[key]

    def faces(self, name, faces, rgb, cc=False, glass=False):
        bm = bmesh.new()
        for f in faces:
            bm.faces.new([bm.verts.new(self.p(*v)) for v in f])
        bm.normal_update()
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for poly in mesh.polygons:
            poly.use_smooth = False
        mesh.materials.append(self.mat(rgb, cc, glass))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)

    def box(self, name, x0, x1, y0, y1, z0, z1, rgb, cc=False):
        c = [[[(x, y, z) for z in (z0, z1)] for y in (y0, y1)] for x in (x0, x1)]
        f = [[c[0][0][0], c[1][0][0], c[1][1][0], c[0][1][0]], [c[0][0][1], c[0][1][1], c[1][1][1], c[1][0][1]],
             [c[0][0][0], c[0][0][1], c[1][0][1], c[1][0][0]], [c[0][1][0], c[1][1][0], c[1][1][1], c[0][1][1]],
             [c[0][0][0], c[0][1][0], c[0][1][1], c[0][0][1]], [c[1][0][0], c[1][0][1], c[1][1][1], c[1][1][0]]]
        self.faces(name, f, rgb, cc)


def glass_material(rgb):
    mat = bpy.data.materials.new("glass")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = st.lin(rgb)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.55
    nt.links.new(nt.nodes.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


# --- rail station (modelled for the X axis; Y swaps x and y) -------------------

def platform(p, y0, y1, edge):
    p.box("slab", 0, 16, y0, y1, 0, 1.9, PLATFORM_SIDE)
    p.box("top", 0, 16, y0, y1, 1.9, 2.1, PLATFORM_TOP)
    e0, e1 = (edge - 0.5, edge - 0.2) if edge > y0 + 1 else (edge + 0.2, edge + 0.5)
    p.box("safety", 0, 16, e0, e1, 2.1, 2.15, SAFETY)


def platform_props(p, y_outer):
    p.box("bench_seat", 5.5, 9, y_outer - 0.4, y_outer + 0.4, 2.9, 3.2, WOOD)
    p.box("bench_back", 5.5, 9, y_outer + (0.3 if y_outer < 8 else -0.5), y_outer + (0.5 if y_outer < 8 else -0.3),
          3.2, 4.3, CC, cc=True)
    for x in (6, 8.5):
        p.box(f"bench_leg{x}", x, x + 0.3, y_outer - 0.3, y_outer + 0.3, 2.1, 2.9, STEEL)
    p.box("lamp_post", 12.3, 12.6, y_outer - 0.15, y_outer + 0.15, 2.1, 9.5, STEEL)
    p.box("lamp_head", 11.9, 13.0, y_outer - 0.4, y_outer + 0.4, 9.5, 10.0, STEEL)


def station_part(sprite, cc_pass):
    rear_sprites = {1070: ("X", "platform"), 1071: ("Y", "platform"), 1073: ("X", "building"),
                    1074: ("Y", "building"), 1076: ("X", "pillars"), 1077: ("Y", "pillars")}
    front_sprites = {1072: ("X", "platform"), 1069: ("Y", "platform"), 1078: ("X", "pillars"),
                     1075: ("Y", "pillars")}
    roofs = {1079: "X", 1080: "Y", 1081: "X", 1082: "Y"}
    glasses = {1083: "X", 1084: "Y", 1085: "X", 1086: "Y"}
    if sprite in rear_sprites or sprite in front_sprites:
        axis, kind = rear_sprites.get(sprite) or front_sprites[sprite]
        rear = sprite in rear_sprites
        p = Part((0, 0 if rear else 11, 0), cc_pass, swap=axis == "Y")
        y0, y1, edge, outer = (0, 5, 5, 1.6) if rear else (11, 16, 11, 14.4)
        platform(p, y0, y1, edge)
        if kind == "platform":
            platform_props(p, outer)
        elif kind == "pillars":
            for x in (3, 13):
                p.box(f"pillar{x}", x - 0.35, x + 0.35, (y0 + y1) / 2 - 0.35, (y0 + y1) / 2 + 0.35, 2, 16, STEEL)
            p.box("bench_seat", 6.5, 9.5, outer - 0.4, outer + 0.4, 2.9, 3.2, WOOD)
        else:
            p.box("building", 1.5, 14.5, 0.6, 4.4, 2, 11, WALL)
            p.box("windows", 2.5, 13.5, 4.4, 4.5, 5, 8.5, WINDOW)
            p.box("door", 7, 9, 4.4, 4.55, 2, 7.5, DOOR)
            p.box("band", 1.3, 14.7, 0.4, 4.6, 10.3, 11, CC, cc=True)
            p.box("roof", 1.0, 15.0, 0.1, 4.9, 11, 11.6, ROOF)
        return
    if sprite in roofs or sprite in glasses:
        axis = roofs.get(sprite) or glasses[sprite]
        p = Part((0, 0, 16), cc_pass, swap=axis == "Y")
        ridge = 20.5
        if sprite in roofs:
            for y in (1.0, 15.0):
                p.box(f"eave{y}", 0, 16, y - 0.3, y + 0.3, 15.6, 16.2, CC, cc=True)
            p.box("ridge", 0, 16, 7.7, 8.3, ridge - 0.4, ridge, STEEL)
            for x in (0.4, 4.2, 8, 11.8, 15.6):
                for ya, yb in ((1.0, 8.0), (8.0, 15.0)):
                    za, zb = (16.0, ridge) if ya < yb and ya == 1.0 else (ridge, 16.0)
                    p.faces(f"rafter{x}{ya}", [[(x - 0.2, ya, za), (x + 0.2, ya, za), (x + 0.2, yb, zb), (x - 0.2, yb, zb)],
                                               [(x - 0.2, ya, za - 0.4), (x - 0.2, yb, zb - 0.4),
                                                (x + 0.2, yb, zb - 0.4), (x + 0.2, ya, za - 0.4)]], STEEL)
        else:
            p.faces("panes", [[(0, 1.0, 16.1), (16, 1.0, 16.1), (16, 8.0, ridge + 0.05), (0, 8.0, ridge + 0.05)],
                              [(0, 8.0, ridge + 0.05), (16, 8.0, ridge + 0.05), (16, 15.0, 16.1), (0, 15.0, 16.1)]],
                    GLASS, glass=True)


# --- road stops ----------------------------------------------------------------

def inward(rect):
    """Unit direction from a part's box towards the tile centre (axis aligned)."""
    (x0, x1, y0, y1) = rect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if (x1 - x0) < (y1 - y0):
        return (1 if cx < 8 else -1, 0)
    return (0, 1 if cy < 8 else -1)


def line_posts(p, rect, spacing, height, rgb, top_rgb=None):
    x0, x1, y0, y1 = rect
    long_x = (x1 - x0) >= (y1 - y0)
    length = (x1 - x0) if long_x else (y1 - y0)
    n = max(2, int(length / spacing) + 1)
    for i in range(n):
        t = 0.5 + (length - 1) * i / (n - 1)
        x, y = ((x0 + t, (y0 + y1) / 2) if long_x else ((x0 + x1) / 2, y0 + t))
        p.box(f"post{i}", x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0, height, rgb)
        if top_rgb:
            p.box(f"cap{i}", x - 0.22, x + 0.22, y - 0.22, y + 0.22, height * 0.6, height * 0.8, top_rgb)
    return long_x


def fence(p, rect):
    x0, x1, y0, y1 = rect
    long_x = line_posts(p, rect, 2.5, 3.5, STEEL)
    for h in (1.6, 3.2):
        if long_x:
            p.box(f"rail{h}", x0 + 0.3, x1 - 0.3, (y0 + y1) / 2 - 0.08, (y0 + y1) / 2 + 0.08, h, h + 0.2, STEEL)
        else:
            p.box(f"rail{h}", (x0 + x1) / 2 - 0.08, (x0 + x1) / 2 + 0.08, y0 + 0.3, y1 - 0.3, h, h + 0.2, STEEL)


def shelter(p, rect):
    """Bus shelter: glass back wall on the outer side, roof with company-colour edge, bench."""
    x0, x1, y0, y1 = rect
    ix, iy = inward(rect)
    long_x = (x1 - x0) >= (y1 - y0)
    if long_x:
        ob = y0 if iy > 0 else y1
        back = (x0 + 1, x1 - 1, ob - 0.1 if iy < 0 else ob, ob + 0.1 if iy > 0 else ob)
        p.box("back", back[0], back[1], min(back[2], back[3]) - 0.05, max(back[2], back[3]) + 0.05, 0.4, 6.5, GLASS)
        p.box("roof", x0 + 0.6, x1 - 0.6, y0, y1, 6.5, 7.1, ROOF)
        p.box("edge", x0 + 0.5, x1 - 0.5, (y1 - 0.25) if iy > 0 else y0, y1 if iy > 0 else (y0 + 0.25), 6.4, 7.2, CC,
              cc=True)
        for x in (x0 + 1, x1 - 1.3):
            p.box(f"post{x}", x, x + 0.3, y0 + 0.2, y1 - 0.2, 0, 6.5, STEEL)
        p.box("bench", x0 + 3, x1 - 3, y0 + 0.8, y1 - 0.8, 1.4, 1.8, WOOD)
    else:
        ob = x0 if ix > 0 else x1
        p.box("back", ob - 0.05, ob + 0.15, y0 + 1, y1 - 1, 0.4, 6.5, GLASS)
        p.box("roof", x0, x1, y0 + 0.6, y1 - 0.6, 6.5, 7.1, ROOF)
        p.box("edge", (x1 - 0.25) if ix > 0 else x0, x1 if ix > 0 else (x0 + 0.25), y0 + 0.5, y1 - 0.5, 6.4, 7.2, CC,
              cc=True)
        for y in (y0 + 1, y1 - 1.3):
            p.box(f"post{y}", x0 + 0.2, x1 - 0.2, y, y + 0.3, 0, 6.5, STEEL)
        p.box("bench", x0 + 0.8, x1 - 0.8, y0 + 3, y1 - 3, 1.4, 1.8, WOOD)


def bus_end(p, rect):
    """Closed end of a bus bay: kerb, bollards and the stop sign."""
    x0, x1, y0, y1 = rect
    line_posts(p, rect, 3.0, 2.4, WHITE, RED)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    p.box("sign_pole", cx - 0.15, cx + 0.15, cy - 0.15, cy + 0.15, 0, 8.5, STEEL)
    p.box("sign", cx - 0.9, cx + 0.9, cy - 0.9, cy + 0.9, 7.0, 9.0, CC, cc=True)


def warehouse(p, rect):
    x0, x1, y0, y1 = rect
    ix, iy = inward(rect)
    p.box("hall", x0 + 0.2, x1 - 0.2, y0 + 0.2, y1 - 0.2, 0, 9, WALL)
    p.box("roof", x0, x1, y0, y1, 9, 9.6, ROOF)
    p.box("band", x0 + 0.1, x1 - 0.1, y0 + 0.1, y1 - 0.1, 8.2, 9, CC, cc=True)
    if iy:
        y = y1 - 0.1 if iy > 0 else y0 - 0.05
        for i, (a, b) in enumerate(((x0 + 2, x0 + 7), (x1 - 7, x1 - 2))):
            p.box(f"door{i}", a, b, y, y + 0.15, 0, 6, DOOR)
    else:
        x = x1 - 0.1 if ix > 0 else x0 - 0.05
        for i, (a, b) in enumerate(((y0 + 2, y0 + 7), (y1 - 7, y1 - 2))):
            p.box(f"door{i}", x, x + 0.15, a, b, 0, 6, DOOR)


def crates_fence(p, rect):
    fence(p, rect)
    x0, x1, y0, y1 = rect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    p.box("crate", cx - 0.8, cx + 0.8, cy - 0.8, cy + 0.8, 0, 1.6, CRATE)


def loading(p, rect):
    """Drive-through truck stop side: low kiosk with company colour and crates."""
    x0, x1, y0, y1 = rect
    long_x = (x1 - x0) >= (y1 - y0)
    if long_x:
        p.box("kiosk", x0 + 5, x0 + 11, y0 + 0.3, y1 - 0.3, 0, 6, WALL)
        p.box("band", x0 + 4.9, x0 + 11.1, y0 + 0.2, y1 - 0.2, 5.4, 6.3, CC, cc=True)
        p.box("crate", x0 + 1.5, x0 + 3.2, y0 + 0.6, y1 - 0.6, 0, 1.7, CRATE)
        p.box("crate2", x1 - 3.2, x1 - 1.5, y0 + 0.6, y1 - 0.6, 0, 1.7, CRATE)
    else:
        p.box("kiosk", x0 + 0.3, x1 - 0.3, y0 + 5, y0 + 11, 0, 6, WALL)
        p.box("band", x0 + 0.2, x1 - 0.2, y0 + 4.9, y0 + 11.1, 5.4, 6.3, CC, cc=True)
        p.box("crate", x0 + 0.6, x1 - 0.6, y0 + 1.5, y0 + 3.2, 0, 1.7, CRATE)
        p.box("crate2", x0 + 0.6, x1 - 0.6, y1 - 3.2, y1 - 1.5, 0, 1.7, CRATE)


def waypoint_markers(p, rect):
    x0, x1, y0, y1 = rect
    line_posts(p, rect, 7.0, 3.0, WHITE, RED)


def rail_waypoint(p, rect, edge):
    x0, x1, y0, y1 = rect
    for x in (3, 13):
        p.box(f"post{x}", x - 0.2, x + 0.2, edge - 0.2, edge + 0.2, 0, 6, STEEL)
    p.box("board", 2.6, 13.4, edge - 0.15, edge + 0.15, 4.5, 6.2, CC, cc=True)


def road_parts():
    """sprite or name -> (anchor (x, y), box size (sx, sy), builder)."""
    parts = {}
    bus = {  # entrance: A, B, C as (origin, size)
        "NE": [((2, 0), (11, 1)), ((13, 0), (3, 16)), ((0, 13), (13, 3))],
        "SE": [((0, 3), (1, 11)), ((0, 0), (16, 3)), ((13, 3), (3, 13))],
        "SW": [((3, 15), (11, 1)), ((0, 0), (3, 16)), ((3, 0), (13, 3))],
        "NW": [((15, 2), (1, 11)), ((0, 13), (16, 3)), ((0, 0), (3, 13))],
    }
    truck = {
        "NE": [((0, 15), (13, 1)), ((13, 0), (3, 16)), ((2, 0), (11, 1))],
        "SE": [((15, 3), (1, 13)), ((0, 0), (16, 3)), ((0, 3), (1, 11))],
        "SW": [((3, 0), (13, 1)), ((0, 0), (3, 16)), ((3, 15), (11, 1))],
        "NW": [((0, 0), (1, 13)), ((0, 13), (16, 3)), ((15, 2), (1, 11))],
    }
    for di, d in enumerate(("NE", "SE", "SW", "NW")):
        for k, (builder, base) in enumerate(((fence_or_posts, 2696), (bus_end, 2700), (shelter, 2704))):
            o, s = bus[d][k]
            parts[base + di] = (o, s, builder)
        for k, (builder, base) in enumerate(((fence, 2712), (warehouse, 2716), (crates_fence, 2720))):
            o, s = truck[d][k]
            parts[base + di] = (o, s, builder)
    dt = [((13, 0), (3, 16)), ((0, 0), (3, 16)), ((0, 0), (16, 3)), ((0, 13), (16, 3))]  # Y W, Y E, X W, X E
    for k, (o, s) in enumerate(dt):
        parts[f"rs{k}"] = (o, s, shelter)
        parts[f"rs{k + 4}"] = (o, s, loading)
        parts[f"rw{k}"] = (o, s, waypoint_markers)
    return parts


def fence_or_posts(p, rect):
    line_posts(p, rect, 3.0, 2.4, WHITE, RED)


def build(name, cc_pass):
    if isinstance(name, int) and 1069 <= name <= 1086:
        station_part(name, cc_pass)
        return
    if isinstance(name, str) and name.startswith("wp"):
        k = int(name[2:])
        axis, rear = ("X" if k < 2 else "Y"), k % 2 == 0
        p = Part((0, 0 if rear else 11, 0), cc_pass, swap=axis == "Y")
        rail_waypoint(p, (0, 16, 0, 5) if rear else (0, 16, 11, 16), 1.5 if rear else 14.5)
        return
    o, s, builder = road_parts()[name]
    p = Part((o[0], o[1], 0), cc_pass)
    builder(p, (o[0], o[0] + s[0], o[1], o[1] + s[1]))


def names():
    out = list(range(1069, 1087)) + list(range(2696, 2708)) + list(range(2712, 2724))
    out += [f"rs{k}" for k in range(8)] + [f"rw{k}" for k in range(4)] + [f"wp{k}" for k in range(4)]
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "stations")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    for name in names():
        for zoom in ZOOMS:
            for cc_pass in (False, True):
                bpy.ops.wm.read_factory_settings(use_empty=True)
                scene = bpy.context.scene
                st.configure_render(scene, samples=16 if cc_pass else 48)
                if cc_pass:
                    scene.cycles.filter_width = 0.01
                oc.setup_camera(scene, zoom, CANVAS * zoom, CANVAS * zoom, anchor_y=ANCHOR_Y)
                build(name, cc_pass)
                suffix = "cc" if cc_pass else "overlay"
                scene.render.filepath = os.path.join(outdir, f"z{zoom}", f"st{name}_{suffix}.png")
                bpy.ops.render.render(write_still=True)
        print(f"rendered station part {name}", flush=True)


if __name__ == "__main__":
    main()
