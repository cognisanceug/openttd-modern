"""Low-poly modelling kit and render helpers for objects and industries.

Models are built in OpenTTD units: x and y run 0-16 per tile (x from the
north corner towards west, y towards east), z is in OpenTTD height units
(8 per height level, 1 px at 1x). In true proportions one x/y unit is about
2.45 z units, so a storey of ~3 m is ~7 z units.

A Kit collects closed solids as (material name, bmesh). Materials come from
PALETTE (base colour sRGB, shading parameters); materials listed in a CC set
are rendered white in the recolour-mask pass. Construction stages follow the
town houses: stage 0 shows foundations, stage 1 the lower part of the
building in scaffolding.

Render outputs (per sprite name and zoom, in <outdir>/z<zoom>/):
  <name>_overlay.png   building colour, canvas 96z x 176z, sprite origin (47z, 136z)
  <name>_cc.png        recolour mask (white = recolour) when the sprite has one
  <name>_shadow.png    cast shadow on the tiles under the building (shadow catcher alpha)
  <name>_color.png / <name>_mask.png   ground tile, canvas 96z x 96z, origin (47z, 56z)
  <name>_gprops.png    parts standing in a ground sprite, tile held out
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ottd_camera as oc  # noqa: E402
import render_ground as rg  # noqa: E402
import style as st  # noqa: E402

ZOOMS = (1, 2, 4)
BUILD_W, BUILD_H, BUILD_ANCHOR = 96, 176, 136
GROUND_SIZE, GROUND_ANCHOR = 96, 56
Z = oc.LEVEL / 8  # one OpenTTD height unit in Blender units
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render", "textures")

W, O, G, F = st.WALL, st.OBJECT, st.GROUND, st.FLAT
PALETTE = {
    # walls and roofs
    "brick": ((178, 98, 76), W), "brick_dark": ((128, 78, 64), W), "cream": ((232, 220, 190), W),
    "white": ((238, 236, 230), W), "grey": ((190, 192, 192), W), "concrete": ((176, 176, 170), W),
    "concrete_dark": ((132, 134, 132), W), "stone": ((204, 196, 178), W), "plinth": ((168, 162, 150), W),
    "glass": ((78, 104, 132), W), "glass_light": ((140, 172, 196), W), "frame": ((244, 242, 236), W),
    "roof_slate": ((92, 100, 114), W), "roof_flat": ((150, 148, 142), W), "roof_tile": ((176, 90, 68), W),
    "roof_metal": ((118, 128, 136), W), "roof_green": ((96, 136, 118), W),
    "wood": ((150, 112, 80), W), "wood_dark": ((104, 78, 58), W), "plank": ((206, 170, 116), O),
    "door": ((92, 76, 64), W), "dark": ((52, 56, 62), W),
    # metal and machinery
    "steel": ((150, 156, 164), W), "steel_dark": ((96, 102, 110), W), "rust": ((156, 88, 62), W),
    "red": ((200, 70, 60), W), "white_band": ((240, 240, 236), W), "yellow": ((236, 196, 64), W),
    "blue": ((76, 128, 196), W), "tank": ((224, 226, 222), W), "pipe": ((188, 190, 186), W),
    "copper": ((186, 120, 76), W), "bronze": ((128, 100, 66), O), "gold": ((214, 174, 92), W),
    # lights and emissive parts
    "lamp": ((255, 238, 170), F), "fire": ((255, 170, 60), F), "glow": ((255, 120, 40), F),
    "spark": ((236, 248, 255), F),
    # nature and loose material
    "leaf": ((96, 158, 72), O), "leaf_dark": ((66, 126, 80), O), "conifer": ((58, 112, 78), O),
    "trunk": ((98, 76, 58), O), "lawn": ((128, 182, 88), G), "hedge": ((84, 140, 70), O),
    "coal": ((66, 66, 72), O), "ore": ((150, 92, 70), O), "gravel": ((150, 146, 136), O),
    "soil": ((150, 114, 80), G), "soil_dark": ((112, 86, 62), G), "sand": ((214, 196, 146), O),
    "log": ((150, 108, 72), O), "log_end": ((222, 186, 132), O), "hay": ((222, 196, 112), O),
    "water": ((86, 150, 190), O), "paper": ((240, 238, 230), O),
    # ground decals
    "paving": ((202, 198, 188), G), "asphalt": ((104, 108, 112), G), "marking": ((236, 234, 226), G),
    "path": ((212, 200, 176), G), "yard": ((170, 160, 144), G), "yard_dark": ((136, 128, 116), G),
    # recolour parts (rendered neutral grey; the mask makes them company / industry colour)
    "cc": ((150, 150, 150), W), "cc_light": ((190, 190, 190), W), "cc_flat": ((160, 160, 160), O),
}


def lerp(a, b, t):
    return a + (b - a) * t


def frange(a, b, step):
    n = max(1, round((b - a) / step))
    return [a + (b - a) * i / n for i in range(n + 1)]


class Kit:
    """Collects closed solids as (material, bmesh) in OpenTTD units."""

    def __init__(self):
        self.parts = []

    def _solid(self, verts, faces, mat):
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in verts]
        for f in faces:
            try:
                bm.faces.new([vs[i] for i in f])
            except ValueError:
                pass
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self.parts.append((mat, bm))

    def box(self, x0, x1, y0, y1, z0, z1, mat):
        if x1 <= x0 or y1 <= y0 or z1 <= z0:
            return
        v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        self._solid(v, f, mat)

    def cbox(self, cx, cy, sx, sy, z0, z1, mat):
        self.box(cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, z0, z1, mat)

    def prism(self, poly, z0, z1, mat):
        """Vertical extrusion of a horizontal polygon [(x, y)]."""
        n = len(poly)
        v = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
        f = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self._solid(v, f, mat)

    def extrude(self, profile, axis, b0, b1, mat):
        """Horizontal extrusion of a vertical profile [(a, z)]; a is y for axis 'x', x for axis 'y'."""
        n = len(profile)

        def p(a, z, b):
            return (b, a, z) if axis == "x" else (a, b, z)
        v = [p(a, z, b0) for a, z in profile] + [p(a, z, b1) for a, z in profile]
        f = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self._solid(v, f, mat)

    def cyl(self, cx, cy, r, z0, z1, mat, n=12, r_top=None, rot=0.0):
        r_top = r if r_top is None else r_top
        ring = [(math.cos(rot + i * math.tau / n), math.sin(rot + i * math.tau / n)) for i in range(n)]
        if r_top <= 0:
            v = [(cx + r * c, cy + r * s, z0) for c, s in ring] + [(cx, cy, z1)]
            f = [tuple(range(n))] + [(i, (i + 1) % n, n) for i in range(n)]
        else:
            v = [(cx + r * c, cy + r * s, z0) for c, s in ring] + [(cx + r_top * c, cy + r_top * s, z1) for c, s in ring]
            f = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self._solid(v, f, mat)

    def lathe(self, cx, cy, profile, mat, n=14):
        """Solid of revolution from a profile [(r, z)] running bottom to top."""
        ring = [(math.cos(i * math.tau / n), math.sin(i * math.tau / n)) for i in range(n)]
        v, f = [], []
        for r, z in profile:
            v += [(cx + max(r, 1e-3) * c, cy + max(r, 1e-3) * s, z) for c, s in ring]
        m = len(profile)
        for j in range(m - 1):
            for i in range(n):
                a, b = j * n + i, j * n + (i + 1) % n
                f.append((a, b, b + n, a + n))
        f += [tuple(range(n)), tuple(range((m - 1) * n, m * n))]
        self._solid(v, f, mat)

    def rod(self, p0, p1, r, mat, n=6):
        """Cylinder between two points (x, y, z) with radius r in x/y units (z scaled to match)."""
        a, b = Vector(p0), Vector(p1)
        # Work in true proportions so the rod is round: z units are 1 / 2.449 of x/y units.
        k = Z * 16  # length of a z unit in x/y units
        A, B = Vector((a.x, a.y, a.z * k)), Vector((b.x, b.y, b.z * k))
        axis = (B - A).normalized()
        ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
        u = axis.cross(ref).normalized()
        w = axis.cross(u).normalized()
        ring = [u * math.cos(i * math.tau / n) * r + w * math.sin(i * math.tau / n) * r for i in range(n)]
        v = [(P.x, P.y, P.z / k) for P in [A + d for d in ring] + [B + d for d in ring]]
        f = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self._solid(v, f, mat)

    def blob(self, cx, cy, cz, rx, ry, rz, mat, subdiv=1):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
        for v in bm.verts:
            v.co = Vector((cx + v.co.x * rx, cy + v.co.y * ry, cz + v.co.z * rz))
        self.parts.append((mat, bm))

    def heap(self, cx, cy, rx, ry, h, mat, seed=0, n=9):
        """Low-poly pile: a ring of jittered base points under a ridge, for coal, ore, gravel."""
        import random
        rng = random.Random(seed)
        ring = []
        for i in range(n):
            t = i * math.tau / n + rng.uniform(-0.15, 0.15)
            s = rng.uniform(0.85, 1.1)
            ring.append((cx + rx * s * math.cos(t), cy + ry * s * math.sin(t)))
        mid = [(cx + rx * 0.45 * s * math.cos(t), cy + ry * 0.45 * s * math.sin(t))
               for t, s in ((i * math.tau / n + 0.3, rng.uniform(0.8, 1.1)) for i in range(n))]
        v = [(x, y, 0) for x, y in ring] + [(x, y, h * rng.uniform(0.55, 0.75)) for x, y in mid] + [(cx, cy, h)]
        f = [tuple(range(n))]
        for i in range(n):
            j = (i + 1) % n
            f.append((i, j, n + j, n + i))
            f.append((n + i, n + j, 2 * n))
        self._solid(v, f, mat)

    # --- building parts -----------------------------------------------------------------

    def gable(self, x0, x1, y0, y1, ze, zr, axis, roof, wall, over=0.6, thick=0.5):
        """Pitched roof with the ridge along axis, gable walls filled with wall."""
        a0, a1, b0, b1 = (y0, y1, x0, x1) if axis == "x" else (x0, x1, y0, y1)
        am = (a0 + a1) / 2
        slope = (zr - ze) / (am - a0)
        # The gable wall stays below the roof's top surface (coplanar faces would flicker).
        self.extrude([(a0, ze - 0.05), (am, zr - thick * 0.8), (a1, ze - 0.05)], axis, b0, b1, wall)
        lo = ze - slope * over
        self.extrude([(a0 - over, lo), (am, zr), (a1 + over, lo), (a1 + over, lo - thick),
                      (am, zr - thick), (a0 - over, lo - thick)], axis, b0 - over * 0.6, b1 + over * 0.6, roof)

    def sawtooth(self, x0, x1, y0, y1, ze, h, n, axis, roof, glass):
        """Factory sawtooth roof: n teeth across axis, glazed steep faces."""
        a0, a1, b0, b1 = (y0, y1, x0, x1) if axis == "x" else (x0, x1, y0, y1)
        step = (a1 - a0) / n
        for i in range(n):
            s = a0 + i * step
            self.extrude([(s, ze), (s + step, ze), (s + step, ze + h)], axis, b0, b1, roof)
            self.extrude([(s + step - 0.25, ze + 0.3), (s + step - 0.05, ze + 0.3), (s + step - 0.05, ze + h - 0.3),
                          (s + step - 0.25, ze + h - 0.4)], axis, b0 + 0.4, b1 - 0.4, glass)

    def flat_roof(self, x0, x1, y0, y1, z, wall, roof="roof_flat", parapet=0.9, t=0.45):
        self.box(x0 + t, x1 - t, y0 + t, y1 - t, z, z + 0.25, roof)
        if parapet:
            self.box(x0, x1, y0, y0 + t, z, z + parapet, wall)
            self.box(x0, x1, y1 - t, y1, z, z + parapet, wall)
            self.box(x0, x0 + t, y0, y1, z, z + parapet, wall)
            self.box(x1 - t, x1, y0, y1, z, z + parapet, wall)

    def windows(self, x0, x1, y0, y1, z0, z1, floor=7.0, ww=1.4, wh=3.2, pitch=2.6, sill=1.6,
                faces="xy", glass="glass", frame="frame", ribbon=False):
        """Windows on the +x and/or +y walls of the box x0-x1, y0-y1, one row per floor from z0."""
        for face in faces:
            lo, hi = (y0, y1) if face == "x" else (x0, x1)
            length = hi - lo
            n = max(1, int((length - 0.8) // pitch))
            first = lo + (length - (n - 1) * pitch) / 2
            z = z0
            while z + sill + wh <= z1 + 0.01:
                cols = [((lo + hi) / 2, length - 1.2)] if ribbon else [(first + i * pitch, ww) for i in range(n)]
                for c, w in cols:
                    for mat, grow, out in ((frame, 0.22, 0.07), (glass, 0.0, 0.12)):
                        a0, a1 = c - w / 2 - grow, c + w / 2 + grow
                        zz0, zz1 = z + sill - grow, z + sill + wh + grow
                        if face == "x":
                            self.box(x1 - 0.05, x1 + out, a0, a1, zz0, zz1, mat)
                        else:
                            self.box(a0, a1, y1 - 0.05, y1 + out, zz0, zz1, mat)
                z += floor

    def door(self, face, x1, y1, pos, w=2.0, h=5.0, mat="door"):
        if face == "x":
            self.box(x1 - 0.05, x1 + 0.15, pos - w / 2, pos + w / 2, 0, h, mat)
        else:
            self.box(pos - w / 2, pos + w / 2, y1 - 0.05, y1 + 0.15, 0, h, mat)

    def roller_door(self, face, x1, y1, pos, w=4.0, h=7.0, mat="steel_dark"):
        self.door(face, x1, y1, pos, w, h, mat)
        for i in range(1, 6):
            z = h * i / 6
            if face == "x":
                self.box(x1 + 0.1, x1 + 0.2, pos - w / 2, pos + w / 2, z - 0.12, z + 0.12, "steel")
            else:
                self.box(pos - w / 2, pos + w / 2, y1 + 0.1, y1 + 0.2, z - 0.12, z + 0.12, "steel")

    def tree(self, x, y, s=1.0, kind="round"):
        self.cyl(x, y, 0.35 * s, 0, 6 * s, "trunk", n=6, r_top=0.25 * s)
        if kind == "round":
            self.blob(x, y, 11 * s, 2.6 * s, 2.6 * s, 6 * s, "leaf")
            self.blob(x - 1.1 * s, y + 0.8 * s, 8.5 * s, 1.8 * s, 1.8 * s, 4 * s, "leaf")
        else:
            for r, z0, z1 in ((2.6, 4, 15), (2.0, 10, 21), (1.3, 16, 27)):
                self.cyl(x, y, r * s, z0 * s, z1 * s, "conifer", n=7, r_top=0)

    def bush(self, x, y, r, mat="hedge"):
        self.blob(x, y, r * 0.9, r, r, r * 1.5, mat, subdiv=1)

    def fence(self, pts, h=3.0, mat="steel", post=2.0):
        """Simple fence along a polyline [(x, y)]: posts and two rails."""
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            L = math.hypot(xb - xa, yb - ya)
            for i in range(int(L // post) + 1):
                t = i * post / L if L else 0
                x, y = lerp(xa, xb, t), lerp(ya, yb, t)
                self.cbox(x, y, 0.2, 0.2, 0, h, mat)
            for z in (h * 0.45, h * 0.95):
                self.rod((xa, ya, z), (xb, yb, z), 0.06, mat, n=4)

    def top(self):
        return max(v.co.z for _, bm in self.parts for v in bm.verts)


# --- construction stages (as for the town houses) -------------------------------------------

def foundations(k, foot):
    for x0, y0, x1, y1 in foot:
        k.box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 0, 1.0, "concrete")
        for a, b, c, d in ((x0, x1, y0, y0 + 0.5), (x0, x1, y1 - 0.5, y1), (x0, x0 + 0.5, y0, y1), (x1 - 0.5, x1, y0, y1)):
            k.box(a, b, c, d, 1.0, 3.0, "concrete")
    x0, y0, x1, y1 = foot[0]
    if x1 - x0 > 4 and y1 - y0 > 4:
        k.box(x0 + 1.0, x0 + 2.6, y0 + 1.0, y0 + 2.6, 1.0, 2.6, "brick")


def scaffold(k, foot, top):
    for x0, y0, x1, y1 in foot:
        x0, y0, x1, y1 = x0 - 0.6, y0 - 0.6, x1 + 0.6, y1 + 0.6
        posts = [(x1, y) for y in frange(y0, y1, 3)] + [(x, y1) for x in frange(x0, x1, 3)]
        for x, y in posts:
            k.box(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0, top + 2.5, "steel")
        z = 5.5
        while z < top + 2:
            k.box(x1 - 0.5, x1 + 0.4, y0, y1 + 0.4, z, z + 0.3, "wood")
            k.box(x0, x1 + 0.4, y1 - 0.5, y1 + 0.4, z, z + 0.3, "wood")
            k.box(x1 + 0.25, x1 + 0.4, y0, y1 + 0.4, z + 1.8, z + 2.0, "steel")
            k.box(x0, x1 + 0.4, y1 + 0.25, y1 + 0.4, z + 1.8, z + 2.0, "steel")
            z += 6


def clip_parts(parts, x0=None, x1=None, y0=None, y1=None, ztop=None, close_top=True):
    """Cut every solid at the given planes, dropping what lies outside; a cut top is closed unless close_top is False."""
    planes = []
    if x0 is not None:
        planes.append(((x0, 0, 0), (1, 0, 0), False))
    if x1 is not None:
        planes.append(((x1, 0, 0), (-1, 0, 0), False))
    if y0 is not None:
        planes.append(((0, y0, 0), (0, 1, 0), False))
    if y1 is not None:
        planes.append(((0, y1, 0), (0, -1, 0), False))
    if ztop is not None:
        planes.append(((0, 0, ztop), (0, 0, -1), close_top))
    out = []
    for mat, bm in parts:
        bm = bm.copy()
        for co, no, fill in planes:
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_inner=True, dist=1e-5)
            if fill:
                edges = [e for e in bm.edges if e.is_boundary]
                if edges:
                    bmesh.ops.holes_fill(bm, edges=edges, sides=0)
        if bm.faces:
            out.append((mat, bm))
    return out


def staged(k, model, stage, foot, final_stage=2):
    """Build model(k) for a construction stage: 0 foundations, 1 lower part in scaffolding."""
    if stage == 0:
        foundations(k, foot)
        return
    model(k)
    if stage < final_stage:
        top = k.top() * 0.45
        k.parts = clip_parts(k.parts, ztop=top, close_top=False)  # open shells read as unfinished walls
        for x0, y0, x1, y1 in foot:
            k.box(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, 0, 0.6, "concrete")
        scaffold(k, foot, top)


# --- scene ---------------------------------------------------------------------------------

def to_blender(x, y, z, shift):
    return oc.CORNERS["N"] + Vector(((y - shift[1]) / 16, -(x - shift[0]) / 16, z * Z))


# Colours of the recolour materials on sprites the game draws without a recolour palette.
CC_FALLBACK = {"cc": "red", "cc_light": "roof_tile", "cc_flat": "red"}


class Materials:
    """mode 'color' (palette), 'cc' (white for recolour materials, black otherwise).

    With fixed=True the recolour materials get the CC_FALLBACK colours.
    """

    def __init__(self, mode, cc=(), fixed=False):
        self.mode, self.cc, self.fixed, self.cache = mode, set(cc), fixed, {}

    def get(self, name):
        if name not in self.cache:
            if self.mode == "cc":
                white = name in self.cc
                self.cache[name] = st.toon_material("cc", (255, 255, 255) if white else (0, 0, 0), params=st.FLAT)
            else:
                rgb, params = PALETTE[CC_FALLBACK.get(name, name) if self.fixed else name]
                self.cache[name] = st.toon_material(name, rgb, params=params)
        return self.cache[name]


def link_parts(parts, shift, mats, camera_visible=True):
    for i, (mat, bm) in enumerate(parts):
        mesh = bpy.data.meshes.new(f"p{i}")
        bm2 = bm.copy()
        for v in bm2.verts:
            v.co = to_blender(v.co.x, v.co.y, v.co.z, shift)
        bm2.to_mesh(mesh)
        bm2.free()
        for poly in mesh.polygons:
            poly.use_smooth = False
        mesh.materials.append(mats.get(mat))
        obj = bpy.data.objects.new(f"p{i}", mesh)
        obj.visible_camera = camera_visible
        bpy.context.scene.collection.objects.link(obj)


def new_scene(zoom, w, h, anchor, samples=24):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    st.configure_render(scene, samples=samples)
    oc.setup_camera(scene, zoom, w * zoom, h * zoom, anchor_y=anchor)
    return scene


def render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def shadow_catcher(shift, tiles):
    """Shadow catcher over the given tiles [(tx, ty)] (tile units relative to the model origin)."""
    for tx, ty in tiles:
        verts = [to_blender(tx * 16 + x, ty * 16 + y, 0, shift) for x, y in ((0, 0), (16, 0), (16, 16), (0, 16))]
        mesh = bpy.data.meshes.new("catcher")
        mesh.from_pydata([tuple(v) for v in verts], [], [(0, 3, 2, 1)])
        obj = bpy.data.objects.new("catcher", mesh)
        obj.is_shadow_catcher = True
        bpy.context.scene.collection.objects.link(obj)


def render_building(outdir, name, parts, shift, cc=(), shadow_parts=None, shadow_tiles=((0, 0),), fixed=False):
    """Colour, recolour mask (if cc) and shadow passes of a building sprite.

    shift is the model point (x, y) that is the sprite's bounding box origin.
    shadow_parts (default: parts) cast the shadow onto shadow_tiles.
    fixed gives the recolour materials fixed colours (sprites drawn without recolouring).
    """
    for zoom in ZOOMS:
        zdir = os.path.join(outdir, f"z{zoom}")
        os.makedirs(zdir, exist_ok=True)
        scene = new_scene(zoom, BUILD_W, BUILD_H, BUILD_ANCHOR)
        link_parts(parts, shift, Materials("color", fixed=fixed))
        render(scene, os.path.join(zdir, f"{name}_overlay.png"))
        if cc:
            scene = new_scene(zoom, BUILD_W, BUILD_H, BUILD_ANCHOR, samples=8)
            scene.cycles.filter_width = 0.01
            link_parts(parts, shift, Materials("cc", cc))
            render(scene, os.path.join(zdir, f"{name}_cc.png"))
        if shadow_tiles:
            scene = new_scene(zoom, BUILD_W, BUILD_H, BUILD_ANCHOR, samples=16)
            link_parts(parts if shadow_parts is None else shadow_parts, shift, Materials("color"), camera_visible=False)
            shadow_catcher(shift, shadow_tiles)
            st.add_shadow_sun(scene, angle_deg=8.0)
            render(scene, os.path.join(zdir, f"{name}_shadow.png"))


def ground_material(base):
    """base: texture name in render/textures (with '/' for subfolders) or a palette name."""
    if base in PALETTE:
        rgb, params = PALETTE[base]
        return st.toon_material(base, rgb, params=G)
    return st.toon_material(base, image_path=os.path.join(TEX, base + ".png"), params=G)


def render_ground(outdir, name, base, decals=(), shift=(0, 0), props=(), cc=(), fixed=False):
    """Flat ground tile: base surface plus flat decal solids, and props standing on it.

    decals and props are Kit parts in model units; shift is the model point at the tile's north corner.
    Decals are drawn into the tile colour (they should only rise a fraction of a unit);
    props go to <name>_gprops.png with the tile held out.
    """
    for zoom in ZOOMS:
        zdir = os.path.join(outdir, f"z{zoom}")
        os.makedirs(zdir, exist_ok=True)
        scene = new_scene(zoom, GROUND_SIZE, GROUND_SIZE, GROUND_ANCHOR)
        rg.build_tile(0, rg.COLOR_OVERSCAN).data.materials.append(ground_material(base))
        link_parts(decals, shift, Materials("color", fixed=fixed))
        render(scene, os.path.join(zdir, f"{name}_color.png"))
        scene = new_scene(zoom, GROUND_SIZE, GROUND_SIZE, GROUND_ANCHOR, samples=16)
        scene.cycles.filter_width = 0.01
        rg.build_tile(0, 1.0).data.materials.append(rg.mask_material())
        render(scene, os.path.join(zdir, f"{name}_mask.png"))
        if props:
            scene = new_scene(zoom, GROUND_SIZE, GROUND_SIZE, GROUND_ANCHOR)
            rg.build_tile(0, 1.0).data.materials.append(rg.holdout_material())
            link_parts(props, shift, Materials("color", fixed=fixed))
            render(scene, os.path.join(zdir, f"{name}_gprops.png"))
            if cc:
                scene = new_scene(zoom, GROUND_SIZE, GROUND_SIZE, GROUND_ANCHOR, samples=8)
                scene.cycles.filter_width = 0.01
                rg.build_tile(0, 1.0).data.materials.append(rg.holdout_material())
                link_parts(props, shift, Materials("cc", cc))
                render(scene, os.path.join(zdir, f"{name}_gcc.png"))
