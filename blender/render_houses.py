"""Render the temperate town houses (1420-1575, 4404-4417) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_houses.py -- <outdir> [--only 1423,1442] [--part k/n]

The draw data comes from ref/houses/houses.json (tools/house_table.py); which
sprite shows which model at which construction stage is worked out in
house_specs.py. Models are built from a small kit of boxes, prisms, roofs and
window grids in OpenTTD units (see house_specs.py). A multi-tile house is
modelled once and cut along the tile edges for each tile's sprite.

Building sprites are drawn anchored at their bounding box origin (dx, dy) of
_town_draw_tile_data. Per sprite and zoom:
  b<sprite>_overlay.png  colour (canvas 96z x 176z, origin (47z, 136z))
  b<sprite>_cc.png       recolour mask (white = facade parts PALETTE_TO_STRUCT_* recolours), rc sprites only
  b<sprite>_shadow.png   cast shadow on the tile (shadow catcher alpha)
Ground sprites (canvas 96z x 96z, origin (47z, 56z), like the tunnel grounds):
  g<sprite>_color.png / g<sprite>_mask.png  flat tile with the texture from make_house_textures.py
  g<sprite>_overlay.png  parts of the house standing in the ground sprite (only where the
                         original draws no building sprite), with the tile held out
The lift of the large office block (1443) is rendered on its own as l1443_overlay.png,
at the ground floor; the packer places it relative to the building sprite.
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import house_specs as hs  # noqa: E402
import ottd_camera as oc  # noqa: E402
import render_ground as rg  # noqa: E402
import style as st  # noqa: E402

ZOOMS = (1, 2, 4)
BUILD_W, BUILD_H, BUILD_ANCHOR = 96, 176, 136
GROUND_SIZE, GROUND_ANCHOR = 96, 56
Z = oc.LEVEL / 8  # one OpenTTD height unit in Blender units
HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "..", "ref", "houses", "houses.json")
TEX = os.path.join(HERE, "..", "render", "textures", "houses")

W, O, G = st.WALL, st.OBJECT, st.GROUND
PALETTE = {
    "brick": ((186, 104, 80), W), "brick_dark": ((132, 82, 70), W), "cream": ((234, 220, 186), W),
    "sand": ((214, 190, 146), W), "white": ((236, 234, 226), W), "grey": ((192, 194, 194), W),
    "concrete": ((170, 170, 164), W), "stone": ((204, 196, 178), W),
    "glass": ((74, 100, 128), W), "glass_light": ((136, 168, 194), W), "frame": ((244, 242, 236), W),
    "roof_tile": ((176, 90, 68), W), "roof_slate": ((92, 100, 114), W), "roof_flat": ((150, 148, 142), W),
    "thatch": ((198, 166, 104), W), "wood": ((150, 112, 80), W), "door": ((96, 74, 60), W),
    "metal": ((150, 156, 164), W), "gold": ((214, 174, 92), W), "yellow": ((236, 198, 64), W),
    "bronze": ((128, 100, 66), O), "red": ((196, 72, 62), W), "blue": ((76, 128, 196), W),
    "seat": ((70, 116, 196), W), "seat2": ((226, 208, 92), W), "sign": ((214, 64, 60), W),
    "lamp": ((255, 240, 186), st.FLAT), "water": ((96, 160, 200), O), "jet": ((214, 236, 246), O),
    "leaf": ((96, 158, 72), O), "leaf_dark": ((66, 126, 80), O), "trunk": ((98, 76, 58), O),
    "lawn": ((122, 176, 84), G), "path": ((206, 196, 176), G), "flower": ((236, 120, 120), O),
    "rc": ((128, 128, 128), W),
}
RC = {"rc"}  # materials PALETTE_TO_STRUCT_* recolours

def lerp(a, b, t):
    return a + (b - a) * t


class Kit:
    """Collects closed solids as (material, bmesh) in OpenTTD units."""

    def __init__(self):
        self.parts = []

    # --- primitives -----------------------------------------------------------------

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

    def cyl(self, cx, cy, r, z0, z1, mat, n=12, r_top=None):
        r_top = r if r_top is None else r_top
        ring = [(math.cos(i * math.tau / n), math.sin(i * math.tau / n)) for i in range(n)]
        if r_top <= 0:
            v = [(cx + r * c, cy + r * s, z0) for c, s in ring] + [(cx, cy, z1)]
            f = [tuple(range(n))] + [(i, (i + 1) % n, n) for i in range(n)]
        else:
            v = [(cx + r * c, cy + r * s, z0) for c, s in ring] + [(cx + r_top * c, cy + r_top * s, z1) for c, s in ring]
            f = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self._solid(v, f, mat)

    def blob(self, cx, cy, cz, rx, ry, rz, mat, subdiv=1):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
        for v in bm.verts:
            v.co = Vector((cx + v.co.x * rx, cy + v.co.y * ry, cz + v.co.z * rz))
        self.parts.append((mat, bm))

    # --- building parts ---------------------------------------------------------------

    def gable(self, x0, x1, y0, y1, ze, zr, axis, roof, wall, over=0.6, thick=0.5):
        """Pitched roof with the ridge along axis, gable walls filled with wall."""
        a0, a1, b0, b1 = (y0, y1, x0, x1) if axis == "x" else (x0, x1, y0, y1)
        am = (a0 + a1) / 2
        slope = (zr - ze) / (am - a0)
        # Gable wall kept just under the roof surface so the two never share a plane.
        self.extrude([(a0, ze - 0.02), (am, zr - thick * 0.8), (a1, ze - 0.02)], axis, b0, b1, wall)
        lo = ze - slope * over
        self.extrude([(a0 - over, lo), (am, zr), (a1 + over, lo), (a1 + over, lo - thick),
                      (am, zr - thick), (a0 - over, lo - thick)], axis, b0 - over * 0.6, b1 + over * 0.6, roof)

    def hip(self, x0, x1, y0, y1, ze, zr, roof, over=0.6, steep=None):
        """Hipped roof over a rectangle; steep gives a mansard-like break (share of the rise)."""
        x0, x1, y0, y1 = x0 - over, x1 + over, y0 - over, y1 + over
        lx, ly = x1 - x0, y1 - y0
        half = min(lx, ly) / 2
        slope = (zr - ze) / half
        ze -= slope * over * 0.5
        if lx >= ly:
            r0, r1 = (x0 + half, (y0 + y1) / 2), (x1 - half, (y0 + y1) / 2)
        else:
            r0, r1 = ((x0 + x1) / 2, y0 + half), ((x0 + x1) / 2, y1 - half)
        v = [(x0, y0, ze), (x1, y0, ze), (x1, y1, ze), (x0, y1, ze), (*r0, zr), (*r1, zr)]
        if lx >= ly:
            f = [(0, 1, 2, 3), (0, 4, 5, 1), (2, 5, 4, 3), (0, 3, 4), (1, 5, 2)]
        else:
            f = [(0, 1, 2, 3), (1, 4, 5, 2), (3, 5, 4, 0), (0, 4, 1), (2, 5, 3)]
        self._solid(v, f, roof)

    def flat_roof(self, x0, x1, y0, y1, z, wall, roof="roof_flat", parapet=0.9, t=0.45):
        self.box(x0 + t, x1 - t, y0 + t, y1 - t, z, z + 0.25, roof)
        if parapet:
            self.box(x0, x1, y0, y0 + t, z, z + parapet, wall)
            self.box(x0, x1, y1 - t, y1, z, z + parapet, wall)
            self.box(x0, x0 + t, y0, y1, z, z + parapet, wall)
            self.box(x1 - t, x1, y0, y1, z, z + parapet, wall)

    def windows(self, x0, x1, y0, y1, z0, z1, floor=6.0, ww=1.5, wh=3.0, pitch=2.6, sill=1.4,
                faces="xy", glass="glass", frame="frame", ribbon=False, skip=()):
        """Windows on the +x and/or +y walls of the box x0-x1, y0-y1, one row per floor from z0."""
        for face in faces:
            lo, hi = (y0, y1) if face == "x" else (x0, x1)
            length = hi - lo
            n = max(1, int((length - 0.8) // pitch))
            first = lo + (length - (n - 1) * pitch) / 2
            z = z0
            while z + sill + wh <= z1 + 0.01:
                if ribbon:
                    cols = [((lo + hi) / 2, length - 1.2)]
                else:
                    cols = [(first + i * pitch, ww) for i in range(n) if i not in skip]
                for c, w in cols:
                    for mat, grow, out in ((frame, 0.25, 0.07), (glass, 0.0, 0.12)):
                        a0, a1 = c - w / 2 - grow, c + w / 2 + grow
                        zz0, zz1 = z + sill - grow, z + sill + wh + grow
                        if face == "x":
                            self.box(x1 - 0.05, x1 + out, a0, a1, zz0, zz1, mat)
                        else:
                            self.box(a0, a1, y1 - 0.05, y1 + out, zz0, zz1, mat)
                z += floor

    def door(self, face, x0, x1, y0, y1, pos, w=2.0, h=4.0, mat="door", canopy=None):
        if face == "x":
            self.box(x1 - 0.05, x1 + 0.15, pos - w / 2, pos + w / 2, 0, h, mat)
            if canopy:
                self.box(x1, x1 + 1.4, pos - w / 2 - 0.6, pos + w / 2 + 0.6, h + 0.2, h + 0.6, canopy)
        else:
            self.box(pos - w / 2, pos + w / 2, y1 - 0.05, y1 + 0.15, 0, h, mat)
            if canopy:
                self.box(pos - w / 2 - 0.6, pos + w / 2 + 0.6, y1, y1 + 1.4, h + 0.2, h + 0.6, canopy)

    def shopfront(self, x0, x1, y0, y1, h=4.5, awning="red", faces="xy"):
        for face in faces:
            if face == "x":
                self.box(x1 - 0.05, x1 + 0.1, y0 + 0.6, y1 - 0.6, 0.4, h - 0.6, "glass_light")
                if awning:
                    self._awning("x", x1, y0 + 0.4, y1 - 0.4, h, awning)
            else:
                self.box(x0 + 0.6, x1 - 0.6, y1 - 0.05, y1 + 0.1, 0.4, h - 0.6, "glass_light")
                if awning:
                    self._awning("y", y1, x0 + 0.4, x1 - 0.4, h, awning)

    def _awning(self, face, at, a0, a1, h, mat):
        """Sloping awning off the wall at x = at (face 'x') or y = at (face 'y'), from a0 to a1 along it."""
        prof = [(at, h), (at + 1.6, h - 1.0), (at + 1.6, h - 1.3), (at, h - 0.3)]
        if face == "x":
            verts = [(x, a, z) for a in (a0, a1) for x, z in prof]
        else:
            verts = [(a, y, z) for a in (a0, a1) for y, z in prof]
        self._solid(verts, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], mat)

    def chimney(self, x, y, z0, z1, mat="brick_dark"):
        self.box(x - 0.6, x + 0.6, y - 0.6, y + 0.6, z0, z1, mat)
        self.box(x - 0.75, x + 0.75, y - 0.75, y + 0.75, z1, z1 + 0.4, "concrete")

    def tree(self, x, y, s=1.0, kind="round"):
        self.cyl(x, y, 0.35 * s, 0, 5 * s, "trunk", n=6, r_top=0.25 * s)
        if kind == "round":
            self.blob(x, y, 8.5 * s, 2.6 * s, 2.6 * s, 3.4 * s, "leaf")
            self.blob(x - 1.2 * s, y + 0.8 * s, 6.8 * s, 1.8 * s, 1.8 * s, 2.2 * s, "leaf")
            self.blob(x + 1.0 * s, y - 0.9 * s, 10.5 * s, 1.6 * s, 1.6 * s, 2.0 * s, "leaf")
        else:
            for k, (r, z0, z1) in enumerate(((2.6, 3, 9), (2.0, 7, 13), (1.4, 11, 17))):
                self.cyl(x, y, r * s, z0 * s, z1 * s, "leaf_dark", n=7, r_top=0)

    def bush(self, x, y, r, mat="leaf"):
        self.blob(x, y, r * 0.55, r, r, r * 0.75, mat, subdiv=1)

    # --- height of all geometry ------------------------------------------------------

    def top(self):
        return max(v.co.z for _, bm in self.parts for v in bm.verts)


# --- the models (see house_specs.py for the coordinate frame) -------------------------------

def tall_office_a(k):
    k.box(1, 14, 1, 14, 0, 54, "brick")
    k.box(1.6, 14.3, 1.6, 14.3, 0, 5, "glass_light")
    k.windows(1, 14, 1, 14, 6, 54, pitch=2.2, ww=1.3)
    k.flat_roof(1, 14, 1, 14, 54, "brick")
    k.box(5, 10, 4, 9, 54, 57.5, "metal")
    k.door("x", 1, 14, 1, 14, 7.5, w=3, h=4.5, mat="glass", canopy="concrete")


def tall_office_b(k):
    k.box(1, 14, 1, 8.5, 0, 60, "rc")
    k.box(1, 14, 8.5, 14, 0, 36, "rc")
    k.windows(1, 14, 1, 8.5, 6, 60, faces="x", pitch=2.2, ww=1.3)
    k.windows(1, 14, 1, 8.5, 36, 60, faces="y", pitch=2.2, ww=1.3)
    k.windows(1, 14, 8.5, 14, 6, 36, pitch=2.2, ww=1.3)
    k.box(1.6, 14.3, 1.6, 14.3, 0, 5, "glass_light")
    k.flat_roof(1, 14, 1, 8.5, 60, "rc")
    k.flat_roof(1, 14, 8.5, 14, 36, "rc")
    k.box(4, 8, 10, 13, 36, 38.5, "metal")


def office_gable(k):
    k.box(1, 8, 1, 15, 0, 34, "rc")
    k.windows(1, 8, 1, 15, 4, 34, faces="y", pitch=2.4)
    k.flat_roof(1, 8, 1, 15, 34, "rc")
    k.box(8, 14, 1, 15, 0, 18, "brick")
    k.windows(8, 14, 1, 15, 4, 18, pitch=2.4)
    k.windows(1, 8.2, 1, 15, 22, 34, faces="x", pitch=2.4)
    k.gable(8, 14, 1, 15, 18, 27, "y", "roof_slate", "brick")
    for y in (4, 8, 12):
        k.box(12.6, 14.4, y - 0.9, y + 0.9, 19, 22, "brick")
        k.box(14.3, 14.5, y - 0.6, y + 0.6, 19.5, 21.5, "glass")
    k.door("x", 8, 14, 1, 15, 8, w=2.4, mat="door", canopy="roof_slate")


def flats_small(k):
    k.box(3, 12, 3, 12, 0, 11, "cream")
    k.windows(3, 12, 3, 12, 0, 11, floor=5.5, wh=2.6, pitch=2.4, sill=1.3)
    k.hip(3, 12, 3, 12, 11, 18, "roof_tile")
    k.door("x", 3, 12, 3, 12, 7.5, w=1.8, h=3.5, canopy="white")
    k.chimney(6, 5, 14, 19.5)


def church(k):
    k.box(3, 12, 4, 12, 0, 12, "rc")
    k.gable(3, 12, 4, 12, 12, 21, "x", "roof_slate", "rc")
    for x in (5, 7.5, 10):
        k.box(x - 0.6, x + 0.6, 12 - 0.05, 12.12, 3, 9.5, "glass")
    k.cyl(3, 8, 3.0, 0, 10, "rc", n=10)
    k.cyl(3, 8, 3.3, 10, 15, "roof_slate", n=10, r_top=0)
    k.box(12, 15, 5.5, 10.5, 0, 30, "rc")
    k.box(14.9, 15.1, 7.2, 8.8, 0, 5, "door")
    k.box(14.9, 15.12, 7.4, 8.6, 20, 26, "glass")
    k.box(15.0, 15.2, 7.0, 9.0, 14, 16.4, "white")  # clock
    k.box(11.8, 15.2, 5.3, 10.7, 30, 31, "stone")
    k.hip(12, 15, 5.5, 10.5, 31, 46, "roof_slate", over=0.2)


def office_lift(k):
    k.box(2, 13, 2, 13, 0, 12, "glass")
    for x in (1.2, 13.4):
        for y in (1.2, 13.4):
            k.box(x, x + 0.6, y, y + 0.6, 0, 12, "concrete")
    k.box(1, 14, 1, 14, 12, 50, "concrete")
    for z in range(12, 50, 6):
        for face in "xy":
            if face == "x":
                k.box(13.95, 14.12, 1.6, 14 - 0.6, z + 1.8, z + 4.8, "glass")
            else:
                k.box(1.6, 13.4, 13.95, 14.12, z + 1.8, z + 4.8, "glass")
    k.box(14, 14.3, 6.6, 9.6, 0, 52, "frame")
    k.box(14.1, 14.5, 6.9, 9.3, 0, 51.5, "glass_light")
    k.flat_roof(1, 14, 1, 14, 50, "concrete")
    k.box(4, 10, 3, 9, 50, 55, "concrete")


def lift_cabin(k):
    k.box(14.3, 15.3, 7.2, 9.0, 0.2, 7.0, "white")
    k.box(15.25, 15.4, 7.5, 8.7, 2.0, 6.0, "glass")


def house_a(k):
    k.box(3, 10, 3, 11, 0, 8, "cream")
    k.windows(3, 10, 3, 11, 0, 8, floor=8, wh=2.6, pitch=2.6, sill=2.4, skip=(1,))
    k.gable(3, 10, 3, 11, 8, 15, "x", "roof_tile", "cream")
    k.door("x", 3, 10, 3, 11, 7, w=1.6, h=3.6)
    k.box(4, 9, 11, 14, 0, 5, "white")
    k.box(4.2, 8.8, 11, 14.2, 0, 4, "metal")
    k.flat_roof(4, 9, 11, 14, 5, "white", parapet=0.4)
    k.chimney(5, 5, 11, 16.5)


def bungalow(k):
    k.box(2, 9, 2, 12, 0, 6, "brick")
    k.box(9, 13, 2, 7, 0, 6, "brick")
    k.windows(2, 9, 2, 12, 0, 6, floor=6, wh=2.4, pitch=2.8, sill=1.8)
    k.windows(9, 13, 2, 7, 0, 6, floor=6, wh=2.4, pitch=2.6, sill=1.8, faces="x")
    k.hip(2, 9, 2, 12, 6, 11, "roof_slate")
    k.hip(9, 13, 2, 7, 6, 10, "roof_slate")
    k.door("x", 9, 13, 2, 7, 4.5, w=1.6, h=3.6)


def hotel(k):
    k.box(1, 8, 1, 31, 0, 44, "white")
    k.box(1.4, 8.4, 1.4, 30.6, 0, 5, "glass_light")
    for z in range(6, 44, 5):
        k.box(8, 9, 2, 30, z, z + 0.5, "white")
        k.box(8.6, 9, 2, 30, z + 0.5, z + 1.6, "frame")
    k.windows(1, 8, 1, 31, 6, 44, floor=5, wh=3.0, sill=1.2, pitch=2.0, ww=1.4, faces="x")
    k.windows(1, 8, 1, 24, 6, 44, floor=5, wh=3.0, sill=1.2, pitch=2.0, ww=1.4, faces="y")
    k.flat_roof(1, 8, 1, 31, 44, "white")
    k.box(2.5, 6.5, 12, 20, 44, 48, "sand")
    k.box(6.5, 6.7, 13, 19, 45, 47.2, "sign")
    k.box(8, 15, 24, 31, 0, 30, "white")
    k.windows(8, 15, 24, 31, 6, 30, floor=5, wh=3.0, sill=1.2, pitch=2.2, ww=1.4)
    k.flat_roof(8, 15, 24, 31, 30, "white")
    k.door("x", 8, 15, 24, 31, 27.5, w=3, h=4.5, mat="glass", canopy="sign")
    # Pool deck in the courtyard.
    k.box(9.5, 15, 3, 22, 0, 0.5, "stone")
    k.box(10.5, 14, 4.5, 20, 0, 0.62, "water")
    for y in (6, 9, 12, 15):
        k.box(9.6, 10.3, y, y + 1.6, 0.5, 1.0, "white")
    k.bush(9.8, 21.5, 1.0)
    k.bush(14.5, 2.5, 1.1)


def statue(k):
    k.box(6.2, 8.8, 5.4, 10.6, 0, 1.2, "stone")
    k.box(6.8, 8.2, 7.0, 9.0, 1.2, 6.0, "stone")
    k.box(6.6, 8.4, 6.8, 9.2, 5.6, 6.2, "stone")
    k.cyl(7.5, 8.0, 0.55, 6.2, 9.6, "bronze", n=8, r_top=0.45)
    k.blob(7.5, 8.0, 10.3, 0.5, 0.5, 0.55, "bronze")
    k.box(7.3, 7.7, 8.2, 8.6, 8.4, 11.6, "bronze")
    k.bush(6.4, 5.8, 0.7)
    k.bush(8.6, 10.2, 0.7)


def fountain(k):
    k.cyl(7.5, 7.5, 4.3, 0, 1.4, "stone", n=20)
    k.cyl(7.5, 7.5, 3.8, 0, 1.5, "water", n=20)
    k.cyl(7.5, 7.5, 0.6, 1.5, 4.2, "stone", n=8)
    k.cyl(7.5, 7.5, 1.6, 4.2, 4.8, "stone", n=12, r_top=1.8)
    k.cyl(7.5, 7.5, 1.3, 4.8, 4.9, "water", n=12)
    k.cyl(7.5, 7.5, 0.3, 4.9, 9.0, "jet", n=6, r_top=0.08)
    for i in range(6):
        a = i * math.tau / 6
        k.cyl(7.5 + 1.7 * math.cos(a), 7.5 + 1.7 * math.sin(a), 0.2, 1.5, 3.2, "jet", n=5, r_top=0)


def park_pond(k):
    pond = [(9 + 3.4 * math.cos(a) * (1 + 0.15 * math.sin(3 * a)), 9.5 + 2.6 * math.sin(a))
            for a in (i * math.tau / 16 for i in range(16))]
    k.prism([(x + (x - 9) * 0.12, y + (y - 9.5) * 0.12) for x, y in pond], 0, 0.3, "stone")
    k.prism(pond, 0, 0.36, "water")
    k.box(13.5, 16, 3.6, 5.0, 0, 0.12, "path")
    k.box(3.5, 4.9, 0, 16, 0, 0.12, "path")
    k.tree(4.5, 11, 1.25)
    k.tree(11.5, 3.5, 0.95)
    k.tree(2.5, 4, 1.4, "conifer")
    k.box(13.8, 14.5, 7.2, 9.8, 0, 1.4, "wood")
    k.bush(14, 14, 1.2)
    k.bush(7, 14.6, 1.0, "leaf_dark")


def park_hill(k):
    k.blob(7.5, 7.5, 0, 6.2, 6.2, 4.0, "lawn", subdiv=2)
    k.tree(6.5, 6.5, 1.3)
    k.tree(10.5, 4.5, 1.0, "conifer")
    k.tree(3.5, 11.5, 0.9)
    for i, (x, y) in enumerate(((13, 12), (14, 9.5), (11.5, 14))):
        k.bush(x, y, 0.9, "flower" if i == 1 else "leaf")
    k.box(13.5, 16, 1.0, 2.4, 0, 0.12, "path")


def office_cube(k):
    k.box(1, 15, 1, 15, 0, 38, "rc")
    k.box(1.4, 15.2, 1.4, 15.2, 0, 5, "glass_light")
    k.windows(1, 15, 1, 15, 6, 38, pitch=2.6, ww=1.8, wh=3.2, sill=1.2)
    k.flat_roof(1, 15, 1, 15, 38, "rc")
    k.box(4, 11, 4, 11, 38, 42, "glass")
    k.flat_roof(4, 11, 4, 11, 42, "white", parapet=0.4)


def shops_mansard(k):
    k.box(1.5, 14.5, 3.5, 13.5, 0, 42, "brick")
    k.shopfront(1.5, 14.5, 3.5, 13.5, awning="red")
    k.windows(1.5, 14.5, 3.5, 13.5, 6, 42, pitch=2.4, wh=3.4)
    k.box(1.3, 14.7, 3.3, 13.7, 42, 43, "stone")
    k.hip(1.5, 14.5, 3.5, 13.5, 43, 53, "roof_slate", over=-0.6)
    for y in (6, 8.5, 11):
        k.box(12.8, 14.6, y - 0.8, y + 0.8, 44, 47, "stone")
        k.box(14.5, 14.7, y - 0.5, y + 0.5, 44.5, 46.5, "glass")


def shops_gable(k):
    k.box(3.5, 13.5, 1.5, 14.5, 0, 20, "sand")
    k.shopfront(3.5, 13.5, 1.5, 14.5, awning="blue")
    k.windows(3.5, 13.5, 1.5, 14.5, 6, 20, floor=7, pitch=2.6, wh=3.6)
    k.gable(3.5, 13.5, 1.5, 14.5, 20, 28, "y", "roof_tile", "sand")
    k.chimney(6, 4, 24, 30)


def shops_tall(k):
    k.box(2.5, 14.5, 0.5, 15.5, 0, 38, "rc")
    k.shopfront(2.5, 14.5, 0.5, 15.5, awning="red")
    k.windows(2.5, 14.5, 0.5, 15.5, 6, 38, pitch=2.5, wh=3.3)
    k.gable(2.5, 14.5, 0.5, 15.5, 38, 46, "x", "roof_tile", "rc")


# Stacked office cubes (centre x, y, base z, accent on the +x side), two per storey, alternating.
MODERN_CUBES = tuple(c for i, z in enumerate(range(13, 82, 6))
                     for c in (((5.6, 5.2, z, i % 2), (10.4, 10.6, z, 1 - i % 2)) if i % 2 == 0 else
                               ((10.2, 5.4, z, i % 2), (5.8, 10.4, z, 1 - i % 2))))


def modern_tower(k):
    k.box(3.5, 13.5, 1.5, 14.5, 0, 10, "glass")
    for x in (2.6, 8.2, 13.8):
        for y in (0.6, 5.4, 10.2, 14.9):
            k.box(x - 0.1, x + 0.6, y - 0.1, y + 0.6, 0, 10, "white")
    k.box(2.5, 14.5, 0.5, 15.5, 10, 13, "white")
    for cx, cy, z, accent in MODERN_CUBES:
        k.box(cx - 3.0, cx + 3.0, cy - 3.0, cy + 3.0, z, z + 5.7, "white")
        k.box(cx + 2.95, cx + 3.1, cy - 2.2, cy + 2.2, z + 1.4, z + 4.3, "rc" if accent else "glass")
        k.box(cx - 2.2, cx + 2.2, cy + 2.95, cy + 3.1, z + 1.4, z + 4.3, "glass" if accent else "rc")
    for cx, cy, top in ((5, 3.5, 104), (11.5, 12.5, 96)):
        k.cyl(cx, cy, 1.8, 13, top, "white", n=12)
        for z in range(24, int(top), 14):
            k.cyl(cx, cy, 1.9, z, z + 4, "rc", n=12)
        k.cyl(cx, cy, 2.0, top, top + 1, "metal", n=12)


def warehouse(k):
    k.box(1.5, 15.5, 2.5, 13.5, 0, 18, "brick_dark")
    for y0, y1 in ((2.5, 8), (8, 13.5)):
        k.gable(1.5, 15.5, y0, y1, 18, 26, "x", "roof_slate", "brick_dark", over=0.3)
    for y in (5.2, 10.8):
        k.box(15.45, 15.6, y - 1.8, y + 1.8, 0, 8, "metal")
    k.windows(1.5, 15.5, 2.5, 13.5, 10, 18, floor=8, wh=3, pitch=2.4, ww=1.2, sill=2)


def office_two(k):
    k.box(1, 8, 0.5, 14.5, 0, 32, "brick")
    k.windows(1, 8, 0.5, 14.5, 4, 32, faces="y", pitch=2.3)
    k.windows(1, 8.2, 0.5, 14.5, 26, 32, faces="x", pitch=2.3)
    k.gable(1, 8, 0.5, 14.5, 32, 42, "y", "roof_tile", "brick")
    k.box(8, 15, 0.5, 14.5, 0, 24, "white")
    k.box(8.4, 15.2, 0.9, 14.7, 0, 4.5, "glass_light")
    k.windows(8, 15, 0.5, 14.5, 6, 24, pitch=2.3, wh=3.4)
    k.box(7.8, 15.4, 0.3, 14.9, 24, 25, "stone")
    k.flat_roof(8, 15, 0.5, 14.5, 25, "white", parapet=0.5)


def old_house_a(k):
    k.box(4, 11, 4, 12, 0, 8, "stone")
    k.windows(4, 11, 4, 12, 0, 8, floor=8, wh=2.4, pitch=2.5, sill=2.6, skip=(1,))
    k.gable(4, 11, 4, 12, 8, 16, "x", "roof_tile", "stone")
    k.door("x", 4, 11, 4, 12, 8, w=1.5, h=3.4)
    k.chimney(7.5, 5.5, 12, 17.5)


def old_house_b(k):
    k.box(4, 12, 3, 10, 0, 8, "cream")
    k.windows(4, 12, 3, 10, 0, 8, floor=8, wh=2.4, pitch=2.4, sill=2.6)
    k.gable(4, 12, 3, 10, 8, 15, "y", "roof_slate", "cream")
    k.door("y", 4, 12, 3, 10, 8, w=1.5, h=3.4)
    k.chimney(9, 6.5, 12, 16.5)


def old_house_c(k):
    k.box(3, 11, 4, 12, 0, 9, "brick")
    k.windows(3, 11, 4, 12, 0, 9, floor=9, wh=2.6, pitch=2.6, sill=3)
    k.hip(3, 11, 4, 12, 9, 16, "roof_tile")
    k.door("x", 3, 11, 4, 12, 8, w=1.5, h=3.4, mat="wood")


def old_house_d(k):
    k.box(4, 10, 4, 13, 0, 8, "white")
    k.windows(4, 10, 4, 13, 0, 8, floor=8, wh=2.4, pitch=2.6, sill=2.6)
    k.gable(4, 10, 4, 13, 8, 15, "y", "roof_slate", "white")
    k.box(10, 13, 7, 11, 0, 5.5, "white")
    k.gable(10, 13, 7, 11, 5.5, 9, "x", "roof_slate", "white", over=0.4)
    k.door("x", 10, 13, 7, 11, 9, w=1.4, h=3.4)
    k.chimney(7, 5, 11, 16)


def cottage(k):
    k.box(4, 12, 4, 11, 0, 7, "cream")
    k.windows(4, 12, 4, 11, 0, 7, floor=7, wh=2.3, pitch=2.4, sill=2.2, skip=(1,))
    k.hip(4, 12, 4, 11, 7, 16, "thatch", over=1.0)
    k.door("x", 4, 12, 4, 11, 7.5, w=1.4, h=3.4, mat="wood")
    k.chimney(5.5, 9, 12, 17.5, "stone")


def house_b(k):
    k.box(3, 9, 3, 12, 0, 9, "brick")
    k.box(9, 13, 3, 8, 0, 9, "brick")
    k.windows(3, 9, 3, 12, 0, 9, floor=9, wh=2.6, pitch=2.6, sill=3)
    k.windows(9, 13, 3, 8, 0, 9, floor=9, wh=2.6, pitch=2.4, sill=3, faces="x")
    k.gable(3, 9, 3, 12, 9, 16, "y", "roof_tile", "brick")
    k.gable(9, 13, 3, 8, 9, 15, "x", "roof_tile", "brick")
    k.door("y", 9, 13, 3, 8, 11, w=1.5, h=3.4)


def house_c(k):
    k.box(3, 11, 4, 11, 0, 9, "sand")
    k.windows(3, 11, 4, 11, 0, 9, floor=9, wh=2.6, pitch=2.6, sill=3)
    k.gable(3, 11, 4, 11, 9, 16, "x", "roof_slate", "sand")
    k.door("x", 3, 11, 4, 11, 6, w=1.5, h=3.4)
    k.box(5, 10, 11, 14, 0, 5, "white")
    k.box(5.4, 9.6, 13.95, 14.15, 0, 4, "metal")
    k.flat_roof(5, 10, 11, 14, 5, "white", parapet=0.4)


def house_d(k):
    k.box(3, 12, 3, 9, 0, 9, "cream")
    k.box(3, 8, 9, 13, 0, 9, "cream")
    k.windows(3, 12, 3, 9, 0, 9, floor=9, wh=2.6, pitch=2.6, sill=3, faces="x")
    k.windows(3, 8, 9, 13, 0, 9, floor=9, wh=2.6, pitch=2.6, sill=3)
    k.gable(3, 12, 3, 9, 9, 16, "x", "roof_tile", "cream")
    k.gable(3, 8, 9, 13, 9, 15, "y", "roof_tile", "cream")
    k.door("y", 3, 12, 3, 9, 10, w=1.5, h=3.4)


def house_e(k):
    k.box(4, 11, 3, 12, 0, 14, "brick")
    k.windows(4, 11, 3, 12, 0, 14, floor=7, wh=2.6, pitch=2.6, sill=2.4)
    k.hip(4, 11, 3, 12, 14, 21, "roof_slate")
    k.door("x", 4, 11, 3, 12, 7.5, w=1.5, h=3.6, canopy="white")
    k.chimney(6, 10, 17, 22)


def flats_a(k):
    k.box(2, 13, 2, 12, 0, 18, "brick")
    k.windows(2, 13, 2, 12, 0, 18, wh=2.8, pitch=2.6, sill=1.6)
    for z in (6, 12):
        k.box(13, 14.3, 4, 10, z, z + 0.4, "concrete")
        k.box(14.1, 14.3, 4, 10, z + 0.4, z + 1.8, "frame")
    k.flat_roof(2, 13, 2, 12, 18, "brick")
    k.door("x", 2, 13, 2, 12, 7, w=2, h=3.8, canopy="concrete")


def flats_b(k):
    k.box(2, 13, 2, 8, 0, 16, "sand")
    k.box(2, 8, 8, 14, 0, 16, "sand")
    k.windows(2, 13, 2, 8, 0, 16, floor=5.5, wh=2.6, pitch=2.4, sill=1.4, faces="x")
    k.windows(2, 8, 8, 14, 0, 16, floor=5.5, wh=2.6, pitch=2.4, sill=1.4)
    k.windows(8, 13, 2, 8, 0, 16, floor=5.5, wh=2.6, pitch=2.4, sill=1.4, faces="y")
    k.hip(2, 13, 2, 8, 16, 22, "roof_tile")
    k.hip(2, 8, 8, 14, 16, 22, "roof_tile")
    k.door("x", 2, 13, 2, 8, 5, w=1.8, h=3.6, canopy="white")


def glass_tower(k):
    k.box(2, 14, 2, 14, 0, 82, "glass")
    for i in range(7):
        a = 2.2 + i * 1.95
        k.box(13.95, 14.1, a - 0.08, a + 0.08, 0, 82, "frame")
        k.box(a - 0.08, a + 0.08, 13.95, 14.1, 0, 82, "frame")
    for z in range(6, 82, 6):
        k.box(13.95, 14.12, 2, 14, z - 0.15, z + 0.15, "frame")
        k.box(2, 14, 13.95, 14.12, z - 0.15, z + 0.15, "frame")
    for y in (2.4, 13.6):
        k.box(14.1, 15.2, y - 0.6, y + 0.6, 0, 86, "red")
    for z in range(10, 86, 12):
        k.box(14.1, 15.0, 2.4, 13.6, z, z + 1.0, "red")
    k.flat_roof(2, 14, 2, 14, 82, "concrete")
    k.box(5, 11, 5, 11, 82, 86, "concrete")


def band_tower(k):
    k.box(1, 15, 1, 15, 0, 10, "white")
    k.box(1.4, 15.2, 1.4, 15.2, 0, 7, "glass_light")
    k.box(3, 13, 3, 13, 10, 82, "red")
    for z in range(10, 82, 6):
        k.box(3, 13.12, 3, 13.12, z + 2.2, z + 5.2, "glass")
        k.box(3, 13.16, 3, 13.16, z + 5.2, z + 6.0, "white")
    for x, y in ((12.4, 12.4), (12.4, 3), (3, 12.4)):
        k.box(x, x + 0.8, y, y + 0.8, 10, 84, "white")
    k.flat_roof(3, 13, 3, 13, 82, "white")
    k.flat_roof(1, 15, 1, 15, 10, "white", parapet=0.6)


def shops_hip(k):
    k.box(1, 15, 1, 15, 0, 38, "rc")
    k.shopfront(1, 15, 1, 15, awning="red")
    k.windows(1, 15, 1, 15, 6, 38, pitch=2.5, wh=3.4)
    k.box(0.8, 15.2, 0.8, 15.2, 38, 39, "stone")
    k.hip(1, 15, 1, 15, 39, 52, "roof_slate")


def shops_two(k):
    k.box(1, 8, 1, 15, 0, 44, "rc")
    k.windows(1, 8, 1, 15, 6, 44, faces="y", pitch=2.5, wh=3.4)
    k.windows(1, 8.2, 1, 15, 32, 44, faces="x", pitch=2.5, wh=3.4)
    k.gable(1, 8, 1, 15, 44, 54, "y", "roof_slate", "rc")
    k.box(8, 15, 1, 15, 0, 28, "rc")
    k.shopfront(8, 15, 1, 15, awning="blue")
    k.windows(8, 15, 1, 15, 6, 28, pitch=2.5, wh=3.4)
    k.gable(8, 15, 1, 15, 28, 37, "y", "roof_tile", "rc")


def gold_tower(k):
    n, cx, cy = 8, 8, 8
    rot = math.pi / 8
    for z in range(0, 84, 6):
        r = 4.6 + 1.4 * math.sin(math.pi * (z + 3) / 86)
        poly = [(cx + r * math.cos(rot + i * math.tau / n), cy + r * math.sin(rot + i * math.tau / n)) for i in range(n)]
        k.prism(poly, z, z + 6, "glass")
        k.prism([(cx + (x - cx) * 1.03, cy + (y - cy) * 1.03) for x, y in poly], z + 5.4, z + 6, "gold")
        for x, y in poly:
            k.box(x - 0.35, x + 0.35, y - 0.35, y + 0.35, z, z + 6, "gold")
    r = 4.6
    poly = [(cx + r * math.cos(rot + i * math.tau / n), cy + r * math.sin(rot + i * math.tau / n)) for i in range(n)]
    k.prism(poly, 84, 87, "gold")


def theatre(k):
    k.box(1, 15, 1, 15, 0, 28, "brick")
    k.box(1, 7, 1, 15, 28, 40, "brick")
    k.flat_roof(1, 7, 1, 15, 40, "brick", parapet=0.5)
    k.flat_roof(1, 15, 1, 15, 28, "stone", parapet=0.6)
    k.box(14.9, 15.1, 4, 12, 0, 8, "glass_light")
    k.box(15, 17, 2.5, 13.5, 8.5, 9.6, "white")
    for y in range(3, 14, 2):
        k.box(16.7, 17.1, y - 0.25, y + 0.25, 8.0, 8.5, "lamp")
    k.box(15, 15.3, 4.5, 11.5, 11, 15, "sign")
    k.windows(1, 15, 1, 15, 16, 28, floor=12, wh=7, pitch=3, ww=1.4, sill=1.5)


def round_tower(k):
    k.cyl(8, 8, 5.4, 0, 92, "glass", n=16)
    for z in range(0, 92, 6):
        k.cyl(8, 8, 5.6, z, z + 1.0, "white", n=16)
    k.cyl(8, 8, 5.8, 92, 94, "white", n=16)
    k.cyl(8, 8, 0.5, 94, 106, "metal", n=6, r_top=0.1)
    for x, y in ((14.2, 1.8), (1.8, 14.2)):
        for dx, dy in ((-0.5, -0.5), (0.5, 0.5)):
            k.box(x + dx - 0.25, x + dx + 0.25, y + dy - 0.25, y + dy + 0.25, 0, 100, "yellow")
        for z in range(4, 100, 6):
            k.box(x - 0.8, x + 0.8, y - 0.8, y + 0.8, z, z + 0.4, "yellow")
        k.box(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 100, 108, "metal")


def cinema(k):
    k.box(1, 15, 1, 15, 0, 24, "white")
    for z in (8, 16):
        k.box(1, 15.15, 1, 15.15, z, z + 0.8, "cream")
    k.flat_roof(1, 15, 1, 15, 24, "white", parapet=0.7)
    k.box(11, 15, 11, 15, 24, 32, "white")
    k.box(12, 15, 12, 15, 32, 38, "white")
    k.box(15, 15.6, 12.4, 13.6, 18, 37, "sign")
    k.box(12.4, 13.6, 15, 15.6, 18, 37, "sign")
    k.box(14.9, 15.1, 4, 11, 0, 6.5, "glass_light")
    k.box(15, 16.8, 3, 12, 6.8, 7.8, "red")
    for y in range(4, 12, 2):
        k.box(16.5, 16.9, y - 0.2, y + 0.2, 6.4, 6.8, "lamp")
    k.windows(1, 15, 1, 11, 9, 16, floor=8, wh=4, pitch=3, faces="y")


def stand(k, axis, a0, a1, b_back, b_front, h, steps, roof_h=None, seat="seat"):
    """Seating rising from the pitch (b_front) to the back (b_back), running along axis from a0 to a1."""
    sgn = 1 if b_back > b_front else -1
    depth = abs(b_back - b_front)
    step = depth / steps
    for i in range(steps):
        b0 = b_front + sgn * i * step
        b1 = b_back
        z = h * (i + 1) / steps
        lo, hi = sorted((b0, b1))
        if axis == "y":
            k.box(lo, hi, a0, a1, 0, z - 0.4, "concrete")
            k.box(lo, hi, a0, a1, z - 0.4, z, seat if i % 2 == 0 else "seat2")
        else:
            k.box(a0, a1, lo, hi, 0, z - 0.4, "concrete")
            k.box(a0, a1, lo, hi, z - 0.4, z, seat if i % 2 == 0 else "seat2")
    if roof_h:
        back_lo, back_hi = sorted((b_back - sgn * 0.5, b_back))
        front = b_front - sgn * 0.5
        lo, hi = sorted((front, b_back))
        if axis == "y":
            k.box(back_lo, back_hi, a0, a1, h, roof_h, "concrete")
            k.box(lo, hi, a0, a1, roof_h, roof_h + 0.6, "metal")
            for a in (a0 + 0.5, (a0 + a1) / 2, a1 - 0.5):
                k.box(back_lo, back_hi, a - 0.3, a + 0.3, roof_h - 1, roof_h + 2.5, "white")
        else:
            k.box(a0, a1, back_lo, back_hi, h, roof_h, "concrete")
            k.box(a0, a1, lo, hi, roof_h, roof_h + 0.6, "metal")
            for a in (a0 + 0.5, (a0 + a1) / 2, a1 - 0.5):
                k.box(a - 0.3, a + 0.3, back_lo, back_hi, roof_h - 1, roof_h + 2.5, "white")


def floodlight(k, x, y, top=46):
    k.cyl(x, y, 0.45, 0, top, "metal", n=6, r_top=0.3)
    k.box(x - 1.4, x + 1.4, y - 1.4, y + 1.4, top, top + 2.2, "metal")
    k.box(x - 1.2, x + 1.2, y - 1.2, y + 1.2, top + 0.2, top + 2.0, "lamp")


def stadium1(k):
    stand(k, "y", 1, 31, 0.5, 5.5, 14, 5, roof_h=20)
    stand(k, "x", 6, 31, 0.5, 4.5, 12, 4, roof_h=18, seat="seat2")
    stand(k, "y", 5, 28, 31.5, 28.5, 6, 3)
    stand(k, "x", 5, 28, 31.5, 27.5, 6, 3, seat="seat2")
    for x, y in ((2, 2), (2, 30), (30, 2), (30, 30)):
        floodlight(k, x, y)


def goalposts(k, gx, gy):
    for dx in (-1.4, 1.4):
        k.box(gx + dx - 0.15, gx + dx + 0.15, gy - 0.15, gy + 0.15, 0, 20, "white")
    k.box(gx - 1.4, gx + 1.4, gy - 0.15, gy + 0.15, 6, 6.35, "white")


def stadium2(k):
    stand(k, "y", 1, 31, 0.5, 7, 16, 6, roof_h=24)
    stand(k, "y", 4, 28, 31.5, 27, 7, 3, seat="seat2")
    goalposts(k, 17, 4.5)
    goalposts(k, 17, 27.5)
    for x, y in ((29.5, 2), (29.5, 30)):
        floodlight(k, x, y, top=40)


def mall(k):
    k.box(2, 30, 2, 30, 0, 14, "cream")
    k.box(2.4, 30.15, 2.4, 30.15, 0.4, 5, "glass_light")
    k.flat_roof(2, 30, 2, 30, 14, "cream", parapet=0.8)
    # Glass barrel vaults along y.
    for x0, x1 in ((6, 13), (19, 26)):
        xm, r = (x0 + x1) / 2, (x1 - x0) / 2
        prof = [(xm + r * math.cos(a), 14.2 + r * 0.7 * math.sin(a)) for a in (i * math.pi / 8 for i in range(9))]
        k.extrude(prof, "y", 4, 28, "glass_light")
        for y in range(4, 29, 3):
            k.extrude([(xm + (r + 0.1) * math.cos(a), 14.2 + (r + 0.1) * 0.7 * math.sin(a)) for a in
                       (i * math.pi / 8 for i in range(9))], "y", y - 0.15, y + 0.15, "frame")
    # Tent roof over the atrium and the main entrance at the front corner.
    k.cyl(8, 24, 5.5, 14.5, 26, "white", n=12, r_top=0.4)
    k.box(26, 31.5, 26, 31.5, 9, 10, "white")
    k.box(30, 30.2, 20, 28, 9.5, 12.5, "sign")
    k.box(20, 28, 30, 30.2, 9.5, 12.5, "sign")
    for x, y in ((31, 26.4), (26.4, 31), (31, 31)):
        k.box(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0, 9, "white")


MODEL_FUNCS = {
    "office_tall_a": tall_office_a, "office_tall_b": tall_office_b, "office_gable": office_gable,
    "flats_small": flats_small, "church": church, "office_lift": office_lift, "house_a": house_a,
    "bungalow": bungalow, "hotel": hotel, "statue": statue, "fountain": fountain, "park_pond": park_pond,
    "park_hill": park_hill, "office_cube": office_cube, "shops_mansard": shops_mansard, "shops_gable": shops_gable,
    "shops_tall": shops_tall, "modern_tower": modern_tower, "warehouse": warehouse, "office_two": office_two,
    "old_house_a": old_house_a, "old_house_b": old_house_b, "old_house_c": old_house_c, "old_house_d": old_house_d,
    "cottage": cottage, "house_b": house_b, "house_c": house_c, "house_d": house_d, "house_e": house_e,
    "flats_a": flats_a, "flats_b": flats_b, "glass_tower": glass_tower, "band_tower": band_tower,
    "shops_hip": shops_hip, "shops_two": shops_two, "gold_tower": gold_tower, "theatre": theatre,
    "round_tower": round_tower, "cinema": cinema, "stadium1": stadium1, "stadium2": stadium2, "mall": mall,
}


# --- construction stages ----------------------------------------------------------------

def foundations(k, foot):
    for x0, y0, x1, y1 in foot:
        k.box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 0, 1.0, "concrete")
        for a, b, c, d in ((x0, x1, y0, y0 + 0.5), (x0, x1, y1 - 0.5, y1), (x0, x0 + 0.5, y0, y1), (x1 - 0.5, x1, y0, y1)):
            k.box(a, b, c, d, 1.0, 3.0, "concrete")
    x0, y0, x1, y1 = foot[0]
    k.box(x1 + 0.6, x1 + 2.0, y0 + 0.5, y0 + 2.0, 0, 1.4, "brick")
    k.box(x1 + 0.6, x1 + 2.0, y0 + 0.5, y0 + 2.0, 0, 0.3, "wood")


def scaffold(k, foot, top):
    for x0, y0, x1, y1 in foot:
        x0, y0, x1, y1 = x0 - 0.8, y0 - 0.8, x1 + 0.8, y1 + 0.8
        posts = [(x1, y) for y in frange(y0, y1, 3)] + [(x, y1) for x in frange(x0, x1, 3)]
        for x, y in posts:
            k.box(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0, top + 2.5, "metal")
        z = 5.5
        while z < top + 2:
            k.box(x1 - 0.5, x1 + 0.4, y0, y1 + 0.4, z, z + 0.3, "wood")
            k.box(x0, x1 + 0.4, y1 - 0.5, y1 + 0.4, z, z + 0.3, "wood")
            k.box(x1 + 0.25, x1 + 0.4, y0, y1 + 0.4, z + 1.8, z + 2.0, "metal")
            k.box(x0, x1 + 0.4, y1 + 0.25, y1 + 0.4, z + 1.8, z + 2.0, "metal")
            z += 6


def frange(a, b, step):
    n = max(1, round((b - a) / step))
    return [a + (b - a) * i / n for i in range(n + 1)]


def clip_parts(parts, x0=None, x1=None, y0=None, y1=None, ztop=None):
    """Cut every solid at the given planes, dropping what lies outside; a cut top is closed."""
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
        planes.append(((0, 0, ztop), (0, 0, -1), True))
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


# --- scene ---------------------------------------------------------------------------------

def to_blender(x, y, z, shift):
    return oc.CORNERS["N"] + Vector(((y - shift[1]) / 16, -(x - shift[0]) / 16, z * Z))


class Materials:
    def __init__(self, mode, rc):
        self.mode, self.rc, self.cache = mode, rc, {}

    def get(self, name):
        if name not in self.cache:
            if self.mode == "cc":
                white = self.rc and name in RC
                self.cache[name] = st.toon_material("cc", (255, 255, 255) if white else (0, 0, 0), params=st.FLAT)
            else:
                rgb, params = PALETTE[name]
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


def model_parts(model, tile_part=None, kind="final", level=1.0):
    """Solids of a model in house coordinates; tile_part (tx, ty) cuts out one tile of a multi-tile house."""
    k = Kit()
    if model == "lift":
        lift_cabin(k)
        return k.parts
    foot = hs.MODELS[model]["foot"]
    if kind == "found":
        foundations(k, foot)
    else:
        MODEL_FUNCS[model](k)
        if kind == "partial":
            top = k.top() * level
            k.parts = clip_parts(k.parts, ztop=top)
            for x0, y0, x1, y1 in foot:
                k.box(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, 0, 0.6, "concrete")
                k.box(x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, top - 0.5, top + 0.15, "concrete")
            scaffold(k, foot, top)
    if tile_part is not None:
        tx, ty = tile_part
        k.parts = clip_parts(k.parts, tx * 16, tx * 16 + 16, ty * 16, ty * 16 + 16)
    return k.parts


def shadow_catcher(shift, tile):
    tx, ty = tile
    verts = [to_blender(tx * 16 + x, ty * 16 + y, 0, shift) for x, y in ((0, 0), (16, 0), (16, 16), (0, 16))]
    mesh = bpy.data.meshes.new("catcher")
    mesh.from_pydata([tuple(v) for v in verts], [], [(0, 3, 2, 1)])
    obj = bpy.data.objects.new("catcher", mesh)
    obj.is_shadow_catcher = True
    bpy.context.scene.collection.objects.link(obj)


def render_building(outdir, sprite, job):
    tile = hs.TILE_OFFSET.get(job["tile"], (0, 0)) if job["model"] in hs.MULTI.values() else None
    t = tile or (0, 0)
    shift = (t[0] * 16 + job["anchor"][0], t[1] * 16 + job["anchor"][1])
    parts = model_parts(job["model"], tile, job["kind"], job["level"])
    whole = model_parts(job["model"], None, job["kind"], job["level"]) if tile else parts
    for zoom in ZOOMS:
        zdir = os.path.join(outdir, f"z{zoom}")
        scene = new_scene(zoom, BUILD_W, BUILD_H, BUILD_ANCHOR)
        link_parts(parts, shift, Materials("color", job["rc"]))
        render(scene, os.path.join(zdir, f"b{sprite}_overlay.png"))
        if job["rc"]:
            scene = new_scene(zoom, BUILD_W, BUILD_H, BUILD_ANCHOR, samples=8)
            scene.cycles.filter_width = 0.01
            link_parts(parts, shift, Materials("cc", True))
            render(scene, os.path.join(zdir, f"b{sprite}_cc.png"))
        scene = new_scene(zoom, BUILD_W, BUILD_H, BUILD_ANCHOR, samples=16)
        link_parts(whole, shift, Materials("color", False), camera_visible=False)
        shadow_catcher(shift, t)
        st.add_shadow_sun(scene, angle_deg=8.0)
        render(scene, os.path.join(zdir, f"b{sprite}_shadow.png"))
    print(f"rendered house sprite {sprite} ({job['model']} {job['kind']})", flush=True)


def render_lift(outdir):
    parts = model_parts("lift")
    for zoom in ZOOMS:
        scene = new_scene(zoom, BUILD_W, BUILD_H, BUILD_ANCHOR)
        link_parts(parts, (0, 0), Materials("color", False))
        render(scene, os.path.join(outdir, f"z{zoom}", f"l{hs.LIFT_SPRITE}_overlay.png"))
    print("rendered lift", flush=True)


def render_ground(outdir, sprite, job):
    tile = hs.TILE_OFFSET.get(job["tile"], (0, 0))
    tex = os.path.join(TEX, f"g{sprite}.png")
    for zoom in ZOOMS:
        zdir = os.path.join(outdir, f"z{zoom}")
        scene = new_scene(zoom, GROUND_SIZE, GROUND_SIZE, GROUND_ANCHOR)
        obj = rg.build_tile(0, rg.COLOR_OVERSCAN)
        obj.data.materials.append(st.toon_material("g", image_path=tex, params=st.GROUND, extension="EXTEND"))
        render(scene, os.path.join(zdir, f"g{sprite}_color.png"))
        scene = new_scene(zoom, GROUND_SIZE, GROUND_SIZE, GROUND_ANCHOR, samples=16)
        scene.cycles.filter_width = 0.01
        rg.build_tile(0, 1.0).data.materials.append(rg.mask_material())
        render(scene, os.path.join(zdir, f"g{sprite}_mask.png"))
        if job["props"]:
            scene = new_scene(zoom, GROUND_SIZE, GROUND_SIZE, GROUND_ANCHOR)
            rg.build_tile(0, 1.0).data.materials.append(rg.holdout_material())
            link_parts(model_parts(job["model"], tile), (tile[0] * 16, tile[1] * 16), Materials("color", False))
            render(scene, os.path.join(zdir, f"g{sprite}_overlay.png"))
    print(f"rendered house ground {sprite} ({job['kind']})", flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv and not argv[0].startswith("--") else os.path.join(os.getcwd(), "render", "houses")
    only = {int(s) for s in argv[argv.index("--only") + 1].split(",")} if "--only" in argv else None
    part, parts = map(int, argv[argv.index("--part") + 1].split("/")) if "--part" in argv else (0, 1)
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    data = json.load(open(TABLE))
    work = [("b", s, j) for s, j in sorted(hs.building_jobs(data).items())]
    work += [("g", s, j) for s, j in sorted(hs.ground_jobs(data).items())]
    work.append(("l", hs.LIFT_SPRITE, None))
    for i, (what, sprite, job) in enumerate(work):
        if i % parts != part or (only and sprite not in only):
            continue
        if what == "b":
            render_building(outdir, sprite, job)
        elif what == "g":
            render_ground(outdir, sprite, job)
        else:
            render_lift(outdir)


if __name__ == "__main__":
    main()
