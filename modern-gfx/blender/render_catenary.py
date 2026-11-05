"""Render rail catenary (CATENARY 0-35) and tram overhead wires (TRAMWAY 56-75, 84-94).

Run:  Blender -b --factory-startup -P render_catenary.py -- <outdir>

Rail (see table/elrail_data.h and elrail.cpp):
  wires 0-27   drawn at their bounding-box origin: X wires at (0, 7, 10), Y at (7, 0, 10),
               left/right (N-S) pieces at (8, 0) / (0, 8), upper/lower (E-W) at (7, 0) / (15, 8);
               "up" pieces are anchored 9 units higher and rise one level along the track,
               "down" pieces 1 unit lower and fall; depot entrances are half wires.
               The contact wire hangs 13 units above the track.
  pylons 28-35 drawn at their foot beside the track; the arm reaches the wire (4 units,
               or 2 + 2 units for diagonal track).
Tram (see DrawRoadTypeCatenary): per road shape a back sprite with the poles at the
W, N and E corners and a front sprite with the S pole and all wires, both drawn at the
tile origin; sloped variants follow the slope. Poles carry a company-colour band.

Outputs <outdir>/z<zoom>/cat<name>_overlay.png and cat<name>_cc.png,
canvas 96z x 112z with the sprite origin at (47z, 72z).
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ottd_camera as oc  # noqa: E402
import style as st  # noqa: E402

ZOOMS = (1, 2, 4)
CANVAS_W, CANVAS_H, ANCHOR_Y = 96, 112, 72
UNIT = oc.LEVEL / 8
STEEL = (130, 136, 144)
WIRE = (58, 62, 68)
CC = (128, 128, 128)
WIRE_Z = 13.0


class G:
    def __init__(self, anchor, cc_pass, z_at=None):
        self.anchor = anchor
        self.cc = cc_pass
        self.z_at = z_at or (lambda x, y: 0.0)
        self.mats = {}

    def p(self, x, y, z):
        return oc.CORNERS["N"] + Vector(((y - self.anchor[1]) / 16, -(x - self.anchor[0]) / 16,
                                         (z - self.anchor[2]) * UNIT))

    def mat(self, rgb, cc):
        key = (rgb, cc)
        if key not in self.mats:
            if self.cc:
                self.mats[key] = st.toon_material("m", (255, 255, 255) if cc else (0, 0, 0), params=st.FLAT)
            else:
                self.mats[key] = st.toon_material(str(rgb), rgb, params=st.OBJECT)
        return self.mats[key]

    def strut(self, name, a, b, w, rgb, cc=False):
        """Square bar from a to b (tile units, z absolute), w thick."""
        pa, pb = self.p(*a), self.p(*b)
        d = (pb - pa)
        if d.length < 1e-6:
            return
        up = Vector((0, 0, 1)) if abs(d.normalized().z) < 0.9 else Vector((1, 0, 0))
        s1 = d.cross(up).normalized() * (w / 16 / 2)
        s2 = d.cross(s1).normalized() * (w / 16 / 2)
        corners = [s1 + s2, s1 - s2, -s1 - s2, -s1 + s2]
        bm = bmesh.new()
        va = [bm.verts.new(pa + c) for c in corners]
        vb = [bm.verts.new(pb + c) for c in corners]
        bm.faces.new(va)
        bm.faces.new(list(reversed(vb)))
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((va[i], va[j], vb[j], vb[i]))
        bm.normal_update()
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for poly in mesh.polygons:
            poly.use_smooth = False
        mesh.materials.append(self.mat(rgb, cc))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)

    def wire(self, name, pts, rgb=WIRE, w=0.22):
        for i in range(len(pts) - 1):
            self.strut(f"{name}{i}", pts[i], pts[i + 1], w, rgb)


# --- rail catenary -------------------------------------------------------------

def rail_wire(g, start, end, z0, z1, along_steps=8):
    """Contact wire with a messenger wire above it and droppers, from start to end (x, y)."""
    pts, mess = [], []
    for i in range(along_steps + 1):
        t = i / along_steps
        x = start[0] + (end[0] - start[0]) * t
        y = start[1] + (end[1] - start[1]) * t
        z = z0 + (z1 - z0) * t
        pts.append((x, y, z))
        mess.append((x, y, z + 2.2 - 1.2 * math.sin(math.pi * t)))
    g.wire("contact", pts)
    g.wire("messenger", mess, w=0.18)
    for i in (2, 4, 6):
        g.strut(f"dropper{i}", pts[i], mess[i], 0.12, WIRE)


# (anchor, wire start, wire end) in tile units; the left/right and upper/lower pieces share a sprite.
_X = ((0, 7), (0, 8), (16, 8))
_Y = ((7, 0), (8, 0), (8, 16))
_NS = ((8, 0), (8, 0), (16, 8))
_EW = ((7, 0), (8, 0), (0, 8))


def rail_wire_spec(k):
    """Wire geometry for catenary offset k (0-27): anchor (x, y, z), start, end, z at start/end."""
    kind = ["X", "Y", "EW", "NS", "X_DOWN", "Y_UP", "X_UP", "Y_DOWN"]
    if k >= 24:
        side = ["SW", "NW", "NE", "SE"][k - 24]
        (ax, ay), s, e = _X if side in ("SW", "NE") else _Y
        mid = ((s[0] + e[0]) / 2, (s[1] + e[1]) / 2)
        s, e = ((mid, e) if side in ("SW", "SE") else (s, mid))
        return (ax, ay, 10), s, e, WIRE_Z, WIRE_Z
    t = kind[k % 8]
    geo = {"X": _X, "Y": _Y, "EW": _EW, "NS": _NS}[t.split("_")[0]]
    (ax, ay), s, e = geo
    if t.endswith("_UP"):
        return (ax, ay, 19), s, e, WIRE_Z, WIRE_Z + 8
    if t.endswith("_DOWN"):
        return (ax, ay, 9), s, e, WIRE_Z, WIRE_Z - 8
    return (ax, ay, 10), s, e, WIRE_Z, WIRE_Z


# Pylon offset (28 + i): arm direction from the foot towards the wire, in tile units.
PYLON_ARMS = [(4, 0), (-4, 0), (0, 4), (0, -4), (2, 2), (-2, -2), (-2, 2), (2, -2)]


def rail_pylon(g, arm):
    top = 16.0
    g.strut("mast", (0, 0, 0), (0, 0, top), 0.7, STEEL)
    g.strut("arm", (0, 0, WIRE_Z + 1.6), (arm[0], arm[1], WIRE_Z + 1.6), 0.4, STEEL)
    g.strut("brace", (0, 0, WIRE_Z - 1.2), (arm[0] * 0.8, arm[1] * 0.8, WIRE_Z + 1.4), 0.25, STEEL)
    g.strut("hanger", (arm[0], arm[1], WIRE_Z + 1.6), (arm[0], arm[1], WIRE_Z), 0.2, STEEL)


# --- tram wires -----------------------------------------------------------------

CORNER = {"N": (1.4, 1.4), "E": (1.4, 14.6), "S": (14.6, 14.6), "W": (14.6, 1.4)}
ARM_POLES = {"NW": ("N", "W"), "NE": ("N", "E"), "SE": ("E", "S"), "SW": ("W", "S")}
MID = {"NE": (0, 8), "SE": (8, 16), "SW": (16, 8), "NW": (8, 0)}
SHAPES = {  # TRAMWAY offset -> arms (front wires 56-67, back poles 84-94)
    56: ("NW", "SE"), 57: ("SW", "NE"), 58: ("NW", "SW", "SE", "NE"), 59: ("NW", "SE", "NE"),
    60: ("NW", "SW", "NE"), 61: ("SW", "SE", "NE"), 62: ("NW", "SW", "SE"), 64: ("NW", "SW"),
    65: ("NW", "NE"), 66: ("SE", "NE"), 67: ("SW", "SE"),
}
BACK = {84: 56, 85: 57, 86: 58, 87: 59, 88: 60, 89: 61, 90: 62, 91: 64, 92: 65, 93: 66, 94: 67}
SLOPED = {0: (12, ("SW", "NE")), 1: (6, ("NW", "SE")), 2: (3, ("SW", "NE")), 3: (9, ("NW", "SE"))}  # NE, SE, SW, NW


def slope_z(slope):
    h = oc.slope_corner_levels(slope)
    # Planar slopes only (inclined roads): bilinear over the corners is exact.
    def z(x, y):
        u, v = x / 16, y / 16  # u towards W/S (OpenTTD x), v towards E/S (OpenTTD y)
        n, w, e, s = h["N"], h["W"], h["E"], h["S"]
        return 8 * ((1 - u) * (1 - v) * n + u * (1 - v) * w + (1 - u) * v * e + u * v * s)
    return z


def tram_poles(g, arms, which):
    poles = sorted({c for a in arms for c in ARM_POLES[a]})
    for c in poles:
        if c not in which:
            continue
        x, y = CORNER[c]
        base = g.z_at(x, y)
        g.strut(f"pole{c}", (x, y, base), (x, y, base + 16), 0.6, STEEL)
        g.strut(f"band{c}", (x, y, base + 12.5), (x, y, base + 14), 0.75, CC, cc=True)


def tram_wires(g, arms):
    for a in arms:
        c1, c2 = (CORNER[c] for c in ARM_POLES[a])
        g.wire(f"span{a}", [(c1[0], c1[1], g.z_at(*c1) + 15), (c2[0], c2[1], g.z_at(*c2) + 15)], w=0.18)
        m = MID[a]
        steps = 6
        pts = [(8 + (m[0] - 8) * i / steps, 8 + (m[1] - 8) * i / steps) for i in range(steps + 1)]
        g.wire(f"contact{a}", [(x, y, g.z_at(x, y) + WIRE_Z) for x, y in pts])


def build(name, cc_pass):
    kind, k = name.split("_")
    k = int(k)
    if kind == "rail":
        if k < 28:
            anchor, s, e, z0, z1 = rail_wire_spec(k)
            g = G(anchor, cc_pass)
            rail_wire(g, s, e, z0, z1)
        else:
            g = G((0, 0, 0), cc_pass)
            rail_pylon(g, PYLON_ARMS[k - 28])
        return
    # Tram: front 56-67 (+ sloped 72-75), back 84-94 (+ sloped 68-71).
    if 68 <= k <= 75:
        slope, arms = SLOPED[(k - 68) % 4]
        g = G((0, 0, 0), cc_pass, slope_z(slope))
        front = k >= 72
    else:
        front = k in SHAPES
        arms = SHAPES[k] if front else SHAPES[BACK[k]]
        g = G((0, 0, 0), cc_pass)
    if front:
        tram_poles(g, arms, ("S",))
        tram_wires(g, arms)
    else:
        tram_poles(g, arms, ("W", "N", "E"))


def names():
    out = [f"rail_{k}" for k in range(36)]
    out += [f"tram_{k}" for k in list(SHAPES) + list(BACK) + list(range(68, 76))]
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "catenary")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    for name in names():
        for zoom in ZOOMS:
            for cc_pass in (False, True):
                bpy.ops.wm.read_factory_settings(use_empty=True)
                scene = bpy.context.scene
                st.configure_render(scene, samples=16 if cc_pass else 32)
                if cc_pass:
                    scene.cycles.filter_width = 0.01
                oc.setup_camera(scene, zoom, CANVAS_W * zoom, CANVAS_H * zoom, anchor_y=ANCHOR_Y)
                build(name, cc_pass)
                suffix = "cc" if cc_pass else "overlay"
                scene.render.filepath = os.path.join(outdir, f"z{zoom}", f"cat{name}_{suffix}.png")
                bpy.ops.render.render(write_still=True)
        print(f"rendered {name}", flush=True)


if __name__ == "__main__":
    main()
