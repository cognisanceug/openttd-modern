"""Render airports, docks, buoys and the oil rig at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_airports.py -- <outdir> [--only a,b] [--part k/n]
(--only takes name prefixes, e.g. --only g2645,b2651,rig)

Draw data comes from table/station_land.h and table/industry_land.h. Building
sprites are anchored at the bounding box origin of their draw-table entry and
carry their cast shadow (see build_kit.py); ground sprites are flat tiles with a
tile-space texture from tools/make_airport_textures.py and the low parts standing
on them. Company colour (recolour mask) goes on fascias, fences, jetways, hangar
doors, the windsock and the dock cranes, as the draw table recolours all of them.

Ground sprites (g<name>):
  2635-2649        aircraft stand, taxiway pieces, runway (exits A-D) and runway end, with edge lights
  2665-2667        small airfield building grounds (buildings drawn in the ground sprite, as in the original)
  2669-2675        small airfield grass and grass runway with edge markers
  x0-x5            Action 5 AIRPORTS: tarmac, runway along y and its end
  x13, x14         grass halves over the apron (overlays, alpha from the texture)
Building sprites (b<name>):
  2633 heliport tower with roof helideck (helicopters land at z 60), 2650/2653/2654
  terminals, 2651 control tower, 2652 round concourse, 2655/2656 hangar front/rear
  (door SE), 2657/2658 small airfield hangar, 2659-2661 jetways, 2662 passenger
  bridge, 2663/2664 fences (Y/X), 2668 small airfield terminal, 2676-2679 windsock
  frames, 2680-2691 radar frames (30 degrees apart), x6-x11 Action 5 hangars (S, W
  with their rear walls, N, E), x12 raised helipad, gui86 helipad marking (OTTD_GUI 86)
  2727-2732 docks: quay deck at land height on piles, on the slope and on the water
  tile, crane and containers on the water part; 693 buoy
  2096-2105 oil rig: the rig is modelled once over its 2x3 tiles and cut into
  three screen-column slices (x - y >= 16, 0..16, < 0), one per tile of the x=1 row,
  as the original draws it; stages: legs (2103-2105), deck and crane (2100-2102), complete
Outputs: see build_kit.py.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_kit as bk  # noqa: E402
import render_ground as rg  # noqa: E402
import style as st  # noqa: E402

W, O, G, F = st.WALL, st.OBJECT, st.GROUND, st.FLAT
bk.PALETTE.update({
    "rig_yellow": ((236, 188, 52), W), "rig_red": ((196, 64, 52), W), "deck_green": ((84, 104, 96), W),
    "orange": ((236, 128, 52), W), "container_blue": ((64, 112, 168), W), "container_green": ((86, 140, 96), W),
    "fender": ((48, 50, 54), W), "pile": ((120, 116, 108), W), "light_green": ((150, 230, 170), F),
})
CC = {"cc", "cc_light", "cc_flat"}


# --- helpers ---------------------------------------------------------------------------

def ring(k, cx, cy, r0, r1, z0, z1, mat, n=24):
    """Flat annulus (no inner disc), as prisms per segment."""
    for i in range(n):
        a0, a1 = i * math.tau / n, (i + 1) * math.tau / n
        k.prism([(cx + r0 * math.cos(a0), cy + r0 * math.sin(a0)), (cx + r1 * math.cos(a0), cy + r1 * math.sin(a0)),
                 (cx + r1 * math.cos(a1), cy + r1 * math.sin(a1)), (cx + r0 * math.cos(a1), cy + r0 * math.sin(a1))],
                z0, z1, mat)


def letter_h(k, cx, cy, s, z0, z1, mat, axis="x"):
    """A helipad 'H' of size s, its bars along axis."""
    if axis == "x":
        k.cbox(cx, cy - s * 0.35, s, s * 0.18, z0, z1, mat)
        k.cbox(cx, cy + s * 0.35, s, s * 0.18, z0, z1, mat)
        k.cbox(cx, cy, s * 0.18, s * 0.7, z0, z1, mat)
    else:
        k.cbox(cx - s * 0.35, cy, s * 0.18, s, z0, z1, mat)
        k.cbox(cx + s * 0.35, cy, s * 0.18, s, z0, z1, mat)
        k.cbox(cx, cy, s * 0.7, s * 0.18, z0, z1, mat)


def rbox(k, cx, cy, lx, ly, ang, z0, z1, mat):
    """Box rotated by ang (radians) about its vertical centre line."""
    c, s = math.cos(ang), math.sin(ang)
    pts = [(cx + c * a - s * b, cy + s * a + c * b) for a, b in ((-lx / 2, -ly / 2), (lx / 2, -ly / 2),
                                                               (lx / 2, ly / 2), (-lx / 2, ly / 2))]
    k.prism(pts, z0, z1, mat)


def transform(parts, fn):
    """Apply fn(x, y, z) -> (x, y, z) to every vertex and fix the normals (mirrors flip them)."""
    for _, bm in parts:
        for v in bm.verts:
            v.co = fn(*v.co)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return parts


def clip_plane(parts, co, no):
    """Keep the side of the plane through co (x, y, z) that the normal no points to."""
    out = []
    for mat, bm in parts:
        bm = bm.copy()
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_inner=True, dist=1e-5)
        if bm.faces:
            out.append((mat, bm))
    return out


def lattice(k, p0, p1, w, mat, r=0.1, step=3.0):
    """Square lattice girder from p0 to p1 (4 chords, zig-zag bracing on every face), width w in x/y units."""
    kz = bk.Z * 16  # length of a z unit in x/y units
    a = Vector((p0[0], p0[1], p0[2] * kz))
    b = Vector((p1[0], p1[1], p1[2] * kz))
    axis = (b - a).normalized()
    ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
    u = axis.cross(ref).normalized()
    v = axis.cross(u).normalized()
    offs = [(-u - v) * w / 2, (u - v) * w / 2, (u + v) * w / 2, (-u + v) * w / 2]
    back = lambda P: (P.x, P.y, P.z / kz)  # noqa: E731
    n = max(1, round((b - a).length / step))
    for o in offs:
        k.rod(back(a + o), back(b + o), r, mat, n=4)
    for i in range(n):
        pa, pb = a.lerp(b, i / n), a.lerp(b, (i + 1) / n)
        for j in range(4):
            k.rod(back(pa + offs[j]), back(pb + offs[(j + 1) % 4]), r * 0.7, mat, n=3)


def band(k, x0, x1, y0, y1, z0, z1, mat, t=0.4, out=0.2):
    """Perimeter band (fascia) around a block, leaving the roof free."""
    x0, x1, y0, y1 = x0 - out, x1 + out, y0 - out, y1 + out
    k.box(x0, x1, y0, y0 + t, z0, z1, mat)
    k.box(x0, x1, y1 - t, y1, z0, z1, mat)
    k.box(x0, x0 + t, y0 + t, y1 - t, z0, z1, mat)
    k.box(x1 - t, x1, y0 + t, y1 - t, z0, z1, mat)


def office_block(k, x0, x1, y0, y1, floors, fh=7.5, wall="white", fascia="cc", glass="glass_light", ribbon=True):
    top = floors * fh
    k.box(x0, x1, y0, y1, 0, top, wall)
    k.windows(x0, x1, y0, y1, 0, top, floor=fh, ribbon=ribbon, sill=1.8, wh=3.8, glass=glass, frame="frame")
    band(k, x0, x1, y0, y1, top - 1.2, top + 0.6, fascia)
    k.flat_roof(x0, x1, y0, y1, top, wall, parapet=0.0)
    return top


# --- airport buildings ---------------------------------------------------------------------

def heliport(k):
    """2633: office tower with a helideck on the roof; deck top at z 60 (helicopters land there)."""
    x0, x1, y0, y1 = 1.5, 14.5, 1.5, 14.5
    k.box(x0, x1, y0, y1, 0, 56, "white")
    k.windows(x0, x1, y0, y1, 0, 56, floor=7.0, ribbon=True, sill=1.6, wh=4.0, glass="glass_light", frame="frame")
    for z in (14.0, 28.0, 42.0):
        k.box(x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, z - 0.8, z, "cc")
    band(k, x0, x1, y0, y1, 54, 56.3, "cc")
    # Entrance canopy.
    k.box(x1, x1 + 1.6, 5.5, 10.5, 6.0, 6.8, "cc")
    k.door("x", x1, y1, 8.0, w=3.5, h=5.5, mat="glass")
    # Deck on posts above the roof, safety net rim, marking.
    for x, y in ((3, 3), (3, 13), (13, 3), (13, 13)):
        k.cyl(x, y, 0.35, 56, 58.2, "steel_dark", n=6)
    k.box(0.4, 15.6, 0.4, 15.6, 58.2, 60.0, "deck_green")
    for a, b, c, d in ((0.0, 16.0, 0.0, 0.4), (0.0, 16.0, 15.6, 16.0), (0.0, 0.4, 0.4, 15.6), (15.6, 16.0, 0.4, 15.6)):
        k.box(a, b, c, d, 58.5, 59.6, "steel")
    ring(k, 8, 8, 5.2, 5.8, 60.0, 60.08, "yellow")
    letter_h(k, 8, 8, 5.0, 60.0, 60.1, "white", axis="x")
    for x, y in ((0.8, 0.8), (0.8, 15.2), (15.2, 0.8), (15.2, 15.2)):
        k.cyl(x, y, 0.3, 59.6, 60.4, "lamp", n=6)


def terminal_a(k):
    """2650 (box 2,0 11x16x40): main terminal hall spanning the tile in y, glazed front, roof lantern."""
    x0, x1 = 2.5, 13.0
    k.box(x0, x1, 0, 16, 0, 20, "white")
    k.box(x1 - 0.05, x1 + 0.12, 0.6, 15.4, 2.0, 18.0, "glass_light")
    for y in (0.6, 4.3, 8.0, 11.7, 15.4):
        k.box(x1, x1 + 0.3, y - 0.2, y + 0.2, 2.0, 18.0, "frame")
    k.box(x1 - 0.1, x1 + 0.35, 0, 16, 9.6, 10.4, "frame")
    k.box(x1 - 0.2, x1 + 0.4, -0.05, 16.05, 18.6, 21.0, "cc")
    k.box(x0 - 0.2, x0 + 0.2, -0.05, 16.05, 18.6, 21.0, "cc")
    k.flat_roof(x0, x1, 0, 16, 20, "white", parapet=0.0)
    # Roof lantern along the hall and a small upper office block with the company sign.
    k.extrude([(5.0, 20.2), (7.75, 25.0), (10.5, 20.2)], "x", 1.5, 14.5, "glass_light")
    k.box(3.5, 9.0, 1.0, 6.0, 20.2, 32.0, "white")
    k.windows(3.5, 9.0, 1.0, 6.0, 20.2, 32.0, floor=6.0, ribbon=True, sill=1.4, wh=3.2, glass="glass_light")
    band(k, 3.5, 9.0, 1.0, 6.0, 31.0, 32.6, "cc")
    k.box(3.8, 8.7, 1.3, 5.7, 32.6, 33.0, "roof_flat")
    k.cyl(5.0, 2.5, 0.12, 33, 39, "steel", n=4)
    # Canopy over the landside kerb (NE side faces the town).
    k.box(x1, x1 + 2.0, 3.0, 13.0, 7.0, 7.6, "cc")


def tower(k):
    """2651 (box 3,3 10x10x60): control tower, glazed cab at the top."""
    k.box(3.5, 12.5, 3.5, 12.5, 0, 9.0, "white")
    k.windows(3.5, 12.5, 3.5, 12.5, 0, 9.0, floor=9.0, ribbon=True, sill=2.0, wh=4.0, glass="glass_light")
    band(k, 3.5, 12.5, 3.5, 12.5, 8.4, 9.6, "cc")
    k.flat_roof(3.5, 12.5, 3.5, 12.5, 9.0, "white", parapet=0.0)
    k.lathe(8, 8, [(2.4, 9.6), (2.1, 40.0), (2.6, 42.0), (3.6, 43.5)], "white", n=10)
    k.lathe(8, 8, [(3.7, 43.5), (3.9, 44.6)], "cc", n=10)
    k.lathe(8, 8, [(3.6, 44.6), (4.3, 50.5), (4.4, 50.9)], "glass", n=10)
    for i in range(10):
        a = i * math.tau / 10 + math.pi / 10
        k.rod((8 + 3.62 * math.cos(a), 8 + 3.62 * math.sin(a), 44.6), (8 + 4.33 * math.cos(a), 8 + 4.33 * math.sin(a), 50.6),
              0.07, "frame", n=3)
    k.lathe(8, 8, [(4.6, 50.9), (4.6, 52.0), (3.0, 53.0)], "cc", n=10)
    k.cyl(8, 8, 0.6, 53, 54.5, "steel_dark", n=6)
    k.rod((8, 8, 54.5), (8, 8, 60.0), 0.08, "steel", n=4)
    k.rod((7, 7.5, 53), (6.5, 7, 58.5), 0.06, "steel", n=3)
    k.blob(8, 8, 60.2, 0.25, 0.25, 0.5, "glow", subdiv=1)


def concourse(k):
    """2652 (box 0,1 14x14x30): round concourse with glass walls, stepped drum and roof."""
    cx, cy = 7.5, 8.0
    k.cyl(cx, cy, 6.6, 0, 1.2, "concrete", n=20)
    k.cyl(cx, cy, 6.3, 1.2, 13.0, "glass_light", n=20)
    for i in range(20):
        a = i * math.tau / 20
        k.rod((cx + 6.35 * math.cos(a), cy + 6.35 * math.sin(a), 1.2), (cx + 6.35 * math.cos(a), cy + 6.35 * math.sin(a), 13),
              0.08, "frame", n=3)
    k.cyl(cx, cy, 6.8, 13.0, 15.0, "cc", n=20)
    k.cyl(cx, cy, 6.5, 15.0, 15.4, "roof_flat", n=20)
    k.cyl(cx, cy, 4.0, 15.4, 22.0, "white", n=16)
    k.cyl(cx, cy, 3.9, 17.0, 20.5, "glass", n=16)
    k.lathe(cx, cy, [(4.3, 22.0), (4.3, 22.8), (2.0, 25.5), (0.3, 26.0)], "roof_metal", n=16)
    k.cyl(cx, cy, 0.1, 26, 30, "steel", n=4)


def terminal_b(k):
    """2653 (box 3,3 10x11x35): four-storey terminal office block."""
    office_block(k, 3.5, 12.8, 3.5, 13.8, 4, fh=7.5)
    k.box(5.0, 8.0, 5.0, 8.0, 30.25, 32.5, "steel")
    k.box(9.0, 11.0, 9.0, 12.0, 30.25, 31.6, "steel_dark")
    k.box(12.8, 14.5, 6.5, 11.0, 6.0, 6.6, "cc")
    k.door("x", 12.8, 13.8, 8.7, w=3.0, h=5.5, mat="glass")


def terminal_c(k):
    """2654 (box 0,3 16x11x40): check-in hall with a curved roof, spanning the tile in x."""
    y0, y1 = 3.5, 13.8
    k.box(0, 16, y0, y1, 0, 16, "white")
    k.box(0.6, 15.4, y1 - 0.05, y1 + 0.12, 1.5, 14.5, "glass_light")
    for x in (0.6, 4.3, 8.0, 11.7, 15.4):
        k.box(x - 0.2, x + 0.2, y1, y1 + 0.3, 1.5, 14.5, "frame")
    # Barrel roof along x.
    prof = [(bk.lerp(y0 - 0.6, y1 + 0.6, i / 10), 16 + 9 * math.sin(math.pi * i / 10)) for i in range(11)]
    inner = [(a, z - 0.7) for a, z in reversed(prof)]
    k.extrude(prof + inner, "x", -0.05, 16.05, "roof_metal")
    k.extrude([(y0, 16), (y1, 16)] + [(a, z - 0.8) for a, z in reversed(prof[1:-1])], "x", 0.05, 15.95, "white")
    k.box(-0.05, 16.05, y1 + 0.1, y1 + 0.5, 14.5, 16.4, "cc")
    k.box(5.5, 10.5, y1, y1 + 2.4, 6.5, 7.1, "cc")


def hangar_model(door, cladding="steel", roof="roof_metal", eave=16.0, ridge=26.0, arched=True):
    """(rear kit, front kit) of a hangar on one tile in the canonical frame: door to SE (+y).

    The rear kit holds the NE side wall (x 0..0.7), the front kit all the rest.
    door: 'open' (aircraft door, company-colour lintel) or 'closed' (the door side faces away).
    """
    rear, front = bk.Kit(), bk.Kit()
    front.box(15.3, 16, 0, 16, 0, eave, cladding)
    rear.box(0, 0.7, 0, 16, 0, eave, cladding)
    rear.box(0.7, 0.9, 0.7, 15.3, 0, eave, "dark")  # inner lining, seen through the open door
    # Back wall with the gable infill.
    if arched:
        prof = [(bk.lerp(0, 16, i / 12), eave + (ridge - eave) * math.sin(math.pi * i / 12)) for i in range(13)]
    else:
        prof = [(0, eave), (8, ridge), (16, eave)]
    front.extrude([(0, 0)] + prof + [(16, 0)], "y", 0, 0.7, cladding)
    # Ribs on the side wall.
    for y in (4, 8, 12):
        front.box(16, 16.25, y - 0.2, y + 0.2, 0, eave, "steel_dark")
    # Roof slab.
    over = 0.5
    outer = [(a, z + 0.6) for a, z in prof]
    outer = [(-over, eave + 0.3)] + outer + [(16 + over, eave + 0.3)]
    inner = [(a, z - 0.1) for a, z in reversed(prof)]
    front.extrude(outer + inner, "y", -0.3, 16.4, roof)
    # Skylight strips across the roof.
    for i in (3, 6, 9) if arched else ():
        a0, z0 = prof[i]
        a1, z1 = prof[i + 1]
        front.extrude([(a0, z0 + 0.62), (a1, z1 + 0.62), (a1, z1 + 0.75), (a0, z0 + 0.75)], "y", 1.0, 15.0, "glass_light")
    if door == "open":
        # Open door: dark interior, the door leaves pushed to the sides, company-colour lintel.
        front.box(0.7, 15.3, 0.7, 1.0, 0, eave, "dark")
        front.extrude([(0.7, eave)] + [(a, z - 0.2) for a, z in prof[1:-1]] + [(15.3, eave)], "y", 0.7, 1.0, "dark")
        front.box(0.7, 2.6, 15.5, 16.0, 0, eave - 1.6, "cc_light")
        front.box(13.4, 15.3, 15.5, 16.0, 0, eave - 1.6, "cc_light")
        front.box(-0.1, 16.1, 15.4, 16.1, eave - 1.6, eave + 0.3, "cc")
        front.extrude([(0, eave + 0.3)] + [(a, z + 0.6) for a, z in prof[1:-1]] + [(16, eave + 0.3)], "y", 15.6, 16.1,
                      cladding)
    else:
        front.extrude([(0, 0)] + prof + [(16, 0)], "y", 15.3, 16.0, cladding)
        front.box(0, 16, 15.9, 16.05, eave - 1.6, eave - 0.6, "cc")
        front.door("y", 16, 16, 12.5, w=1.6, h=5.0, mat="door")
        front.windows(0.7, 15.3, 0.7, 16.0, 0, eave, floor=eave, faces="y", sill=8.0, wh=3.2, pitch=3.2)
    return rear, front


def airfield_hangar():
    """Small airfield hangar (2657/2658): timber walls, gable roof, open to SE."""
    rear, front = bk.Kit(), bk.Kit()
    rear.box(0, 0.7, 0.5, 15.5, 0, 12, "wood")
    front.box(15.3, 16, 0.5, 15.5, 0, 12, "wood")
    front.box(0, 16, 0.5, 1.2, 0, 12, "wood")
    front.gable(0, 16, 0.5, 15.5, 12, 22, "y", "roof_slate", "wood", over=0.7)
    front.box(0.7, 15.3, 1.2, 1.5, 0, 12, "dark")
    front.extrude([(0.7, 12), (8, 21.3), (15.3, 12)], "y", 1.2, 1.5, "dark")
    for x in (1.5, 14.5):
        front.box(x - 0.6, x + 0.6, 15.3, 15.8, 0, 12, "wood_dark")
    front.box(0.2, 15.8, 15.2, 15.8, 10.5, 12.2, "cc")
    for y in (4.0, 8.0, 12.0):
        front.box(16, 16.2, y - 0.9, y + 0.9, 5.5, 8.0, "glass")
    return rear, front


def jetway(k, pts, z=6.5):
    """Jetway: rotunda at the terminal end pts[0], glazed tube along the polyline, cab on a drive column at the end."""
    x, y = pts[0]
    k.cyl(x, y, 1.1, 0, z + 4.4, "steel", n=10)
    k.cyl(x, y, 1.2, z + 4.0, z + 4.6, "cc", n=10)
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        lo_x, hi_x = (min(xa, xb), max(xa, xb)) if xa != xb else (xa - 0.75, xa + 0.75)
        lo_y, hi_y = (min(ya, yb), max(ya, yb)) if ya != yb else (ya - 0.75, ya + 0.75)
        k.box(lo_x, hi_x, lo_y, hi_y, z, z + 3.6, "steel")
        gx = 0.05 if xa == xb else 0.0
        gy = 0.05 if ya == yb else 0.0
        k.box(lo_x - gx, hi_x + gx, lo_y - gy, hi_y + gy, z + 1.4, z + 2.8, "glass_light")
        k.box(lo_x - gx * 2, hi_x + gx * 2, lo_y - gy * 2, hi_y + gy * 2, z + 3.6, z + 4.1, "cc")
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    dx, dy = (xb > xa) - (xb < xa), (yb > ya) - (yb < ya)
    cx, cy = xb + dx * 0.9, yb + dy * 0.9
    k.cbox(cx, cy, 2.0, 2.0, z - 0.3, z + 4.0, "white")
    k.cbox(cx + dx * 1.1, cy + dy * 1.1, 0.6 if dx else 2.2, 2.2 if dx else 0.6, z - 0.2, z + 3.8, "dark")
    k.cyl(xb, yb, 0.3, 1.2, z, "steel_dark", n=6)
    k.box(xb - 1.0, xb + 1.0, yb - 0.6, yb + 0.6, 0.3, 1.2, "steel_dark")
    for ox in (-0.8, 0.8):
        k.cyl(xb + ox, yb, 0.35, 0, 0.7, "dark", n=6)


def fence(k, axis):
    """Airport fence along y (axis 'y', at x 0.5) or x (axis 'x', at y 0.5): posts and company-colour mesh rails."""
    for t in (0.6, 4.4, 8.2, 12.0, 15.6):
        x, y = (0.5, t) if axis == "y" else (t, 0.5)
        k.cbox(x, y, 0.25, 0.25, 0, 6.2, "steel")
    a, b = ((0.5, 0.0), (0.5, 16.0)) if axis == "y" else ((0.0, 0.5), (16.0, 0.5))
    for z in (1.2, 2.6, 4.0, 5.4):
        k.rod((a[0], a[1], z), (b[0], b[1], z), 0.06, "cc", n=3)
    k.rod((a[0], a[1], 6.1), (b[0], b[1], 6.1), 0.1, "steel", n=4)


def windsock(k, frame):
    """2676-2679 (box 4,11 1x1x20): pole and a striped sock swinging in the wind."""
    x, y = 4.5, 11.5
    k.cyl(x, y, 0.5, 0, 0.6, "concrete", n=6)
    k.cyl(x, y, 0.12, 0, 17.5, "steel", n=5)
    ang = math.radians((215, 230, 245, 230)[frame])
    droop = (2.5, 1.2, 0.6, 1.6)[frame]
    L = 5.5
    segs = 5
    k.rod((x, y, 17.0), (x + math.cos(ang) * 0.3, y + math.sin(ang) * 0.3, 17.0), 0.62, "steel", n=8)
    for i in range(segs):
        t0, t1 = i / segs, (i + 1) / segs
        r0, r1 = bk.lerp(0.6, 0.28, t0), bk.lerp(0.6, 0.28, t1)
        p0 = (x + math.cos(ang) * L * t0, y + math.sin(ang) * L * t0, 17.0 - droop * t0 * t0 * 2)
        p1 = (x + math.cos(ang) * L * t1, y + math.sin(ang) * L * t1, 17.0 - droop * t1 * t1 * 2)
        k.rod(p0, p1, (r0 + r1) / 2, "cc_flat" if i % 2 == 0 else "white", n=8)


def radar(k, frame):
    """2680-2691 (box 7,7 2x2x8): surveillance radar on a lattice mast, turning 30 degrees per frame."""
    cx, cy = 8.0, 8.0
    k.cbox(cx, cy, 2.0, 2.0, 0, 0.6, "concrete")
    lattice(k, (cx, cy, 0.6), (cx, cy, 11.0), 1.0, "steel", r=0.07, step=1.6)
    k.cyl(cx, cy, 0.8, 11.0, 11.8, "steel_dark", n=8)
    k.cyl(cx, cy, 0.3, 11.8, 12.8, "steel_dark", n=6)
    ang = frame * math.tau / 12
    # Curved reflector (five slats bent around the turning axis), white with a red rim.
    n = 5
    for i in range(n):
        off = (i - (n - 1) / 2) * 1.0
        bend = 0.18 * off * off
        px = cx + math.cos(ang) * off - math.sin(ang) * bend
        py = cy + math.sin(ang) * off + math.cos(ang) * bend
        rbox(k, px, py, 1.05, 0.2, ang + math.atan(0.36 * off), 12.6, 16.4, "white")
        rbox(k, px, py, 1.05, 0.22, ang + math.atan(0.36 * off), 16.4, 17.0, "red")
    k.rod((cx, cy, 12.8), (cx - math.sin(ang) * 1.6, cy + math.cos(ang) * 1.6, 14.5), 0.08, "steel_dark", n=3)
    k.blob(cx, cy, 11.4, 0.15, 0.15, 0.3, "glow")


def helipad_marking(k, cx, cy, r, z=0.0):
    ring(k, cx, cy, r - 0.6, r, z, z + 0.08, "yellow")
    letter_h(k, cx, cy, r * 0.9, z, z + 0.1, "white", axis="x")


def raised_helipad(k):
    """Action 5 AIRPORTS 12 (drawn at 0,1,2): an octagonal pad two units high, model z shifted by -2."""
    k.cyl(8, 8, 6.4, -2, 0, "concrete_dark", n=8, rot=math.pi / 8)
    k.cyl(8, 8, 6.6, -0.4, 0, "deck_green", n=8, rot=math.pi / 8)
    helipad_marking(k, 8, 8, 5.4)
    for i in range(8):
        a = i * math.tau / 8 + math.pi / 8
        k.cyl(8 + 6.2 * math.cos(a), 8 + 6.2 * math.sin(a), 0.22, 0, 0.5, "lamp", n=5)


def airfield_terminal(k):
    """2668 (box 0,0 15x15x30): small airfield terminal with a control cab."""
    k.box(1.5, 10.5, 2.0, 12.0, 0, 9.0, "brick")
    k.windows(1.5, 10.5, 2.0, 12.0, 0, 9.0, floor=9.0, sill=2.4, wh=3.6, pitch=2.8)
    k.door("x", 10.5, 12.0, 7.0, w=2.2, h=5.5)
    k.box(1.3, 10.7, 1.8, 12.2, 8.4, 9.4, "cc")
    k.flat_roof(1.5, 10.5, 2.0, 12.0, 9.4, "brick", parapet=0.6)
    k.box(2.5, 7.5, 3.0, 8.0, 9.6, 16.0, "white")
    k.lathe(5.0, 5.5, [(3.2, 16.0), (3.6, 21.0)], "glass", n=8)
    k.lathe(5.0, 5.5, [(3.9, 21.0), (3.9, 21.8), (1.0, 23.0)], "cc", n=8)
    k.rod((5.0, 5.5, 23), (5.0, 5.5, 28), 0.07, "steel", n=3)
    # Lean-to waiting room to the SE with a canopy.
    k.box(10.5, 14.0, 3.0, 9.0, 0, 6.0, "white")
    k.windows(10.5, 14.0, 3.0, 9.0, 0, 6.0, floor=6.0, sill=1.6, wh=3.0, glass="glass_light")
    k.extrude([(2.6, 6.0), (9.4, 6.0), (9.4, 6.8)], "y", 10.3, 14.6, "roof_slate")


# --- ground props -----------------------------------------------------------------------

def runway_lights(k, along="x", end=False):
    pos = (2.0, 6.0, 10.0, 14.0)
    for t in pos:
        for c in (0.45, 15.55):
            x, y = (t, c) if along == "x" else (c, t)
            k.cyl(x, y, 0.28, 0, 0.35, "steel_dark", n=6)
            k.cyl(x, y, 0.18, 0.35, 0.65, "lamp", n=6)
    if end:
        for c in (3.0, 5.5, 10.5, 13.0):
            for t in (0.45, 15.55):
                x, y = (t, c) if along == "x" else (c, t)
                k.cyl(x, y, 0.22, 0, 0.55, "light_green", n=6)


def airfield_markers(k):
    for x in (2.0, 6.0, 10.0, 14.0):
        for y in (3.0, 13.0):
            k.cbox(x, y, 0.9, 0.5, 0, 0.6, "white")


def airfield_ground_props(sprite):
    k = bk.Kit()
    if sprite == 2665:
        # Flying club house: timber cabin with a gable roof, bench and a fuel pump.
        k.box(4.0, 10.5, 4.5, 11.5, 0, 7.5, "wood")
        k.windows(4.0, 10.5, 4.5, 11.5, 0, 7.5, floor=7.5, sill=2.4, wh=3.0, pitch=2.8, glass="glass")
        k.door("x", 10.5, 11.5, 8.0, w=1.8, h=5.0)
        k.gable(4.0, 10.5, 4.5, 11.5, 7.5, 12.5, "x", "roof_tile", "wood", over=0.5)
        k.box(11.5, 12.3, 5.0, 8.0, 0, 1.6, "wood_dark")
        k.cbox(12.5, 12.5, 1.2, 0.9, 0, 3.2, "red")
        k.tree(2.5, 14.0, 0.55)
    elif sprite == 2666:
        # Small passenger shed with a flat roof and a parked car.
        k.box(2.5, 10.0, 2.5, 10.5, 0, 8.0, "cream")
        k.windows(2.5, 10.0, 2.5, 10.5, 0, 8.0, floor=8.0, sill=2.2, wh=3.4, pitch=2.6, glass="glass")
        k.door("x", 10.0, 10.5, 6.5, w=2.0, h=5.2)
        k.flat_roof(2.5, 10.0, 2.5, 10.5, 8.0, "cream", roof="roof_slate", parapet=0.5)
        k.box(10.0, 12.0, 3.5, 9.5, 5.6, 6.2, "roof_slate")
        k.cbox(13.5, 14.0, 3.0, 1.5, 0.4, 2.0, "blue")
        k.cbox(13.5, 14.0, 1.8, 1.3, 2.0, 3.0, "glass")
    elif sprite == 2667:
        # Forecourt of the terminal: parking, a flag in company colour, a bench.
        k.cbox(13.5, 4.0, 1.5, 3.0, 0.4, 2.0, "white")
        k.cbox(13.5, 4.0, 1.3, 1.8, 2.0, 3.0, "glass")
        k.cyl(13.5, 13.5, 0.12, 0, 14, "steel", n=5)
        k.box(13.4, 13.6, 10.5, 13.5, 10.0, 13.6, "cc_flat")
        k.box(12.0, 12.8, 8.0, 11.0, 0, 1.5, "wood_dark")
    return k


# --- docks and buoy --------------------------------------------------------------------------

def dock_deck(k, x0, x1, y0, y1, ground_z):
    """Quay deck at z 6.6..8 over x0..x1, y0..y1 on piles reaching down to ground_z(x, y)."""
    k.box(x0, x1, y0, y1, 6.6, 8.0, "concrete")
    k.box(x0, x1, y0 - 0.25, y0 + 0.2, 5.6, 8.2, "concrete_dark")
    k.box(x0, x1, y1 - 0.2, y1 + 0.25, 5.6, 8.2, "concrete_dark")
    for x in bk.frange(x0 + 1.0, x1 - 1.0, 4.5):
        for y in (y0 + 0.8, y1 - 0.8):
            zg = ground_z(x, y)
            if zg < 6.4:
                k.cyl(x, y, 0.5, zg - 2.0, 6.6, "pile", n=6)


def dock_slope(k, slope_dir):
    """Slope part in the canonical frame: water to -x (low edge x 0, high edge x 16), deck along x."""
    dock_deck(k, 0, 16, 1.0, 15.0, lambda x, y: x / 2)
    for y in (1.4, 14.6):
        k.box(0.5, 15.5, y - 0.15, y + 0.15, 8.0, 8.35, "white")
    k.cyl(10.0, 13.6, 0.12, 8, 18, "steel", n=4)
    k.box(9.4, 10.6, 13.5, 13.7, 17.6, 18.0, "steel")
    k.blob(9.6, 13.6, 17.6, 0.3, 0.2, 0.3, "lamp")
    k.box(5.0, 7.5, 3.0, 5.5, 8.0, 10.2, "plank")
    k.box(5.4, 7.1, 3.4, 5.1, 10.2, 11.8, "plank")
    k.cyl(2.0, 2.0, 0.35, 8.0, 9.0, "dark", n=6)
    k.cyl(2.0, 14.0, 0.35, 8.0, 9.0, "dark", n=6)


def dock_flat(k):
    """Water part in the canonical frame: deck along x on piles, crane and containers."""
    dock_deck(k, 0, 16, 1.0, 15.0, lambda x, y: 0.0)
    for x in (2.5, 8.0, 13.5):
        for y in (1.4, 14.6):
            k.cyl(x, y, 0.35, 8.0, 9.0, "dark", n=6)
    for y in (0.85, 15.15):
        for x in (4.5, 11.5):
            k.box(x - 0.9, x + 0.9, y - 0.2, y + 0.2, 3.5, 7.0, "fender")
    # Containers.
    for (x, y, z, mat) in ((3.0, 10.5, 8.0, "red"), (3.0, 10.5, 11.0, "container_blue"), (6.2, 10.5, 8.0, "container_green"),
                           (6.2, 12.6, 8.0, "yellow"), (3.0, 12.6, 8.0, "container_blue")):
        k.box(x - 1.5, x + 1.5, y - 0.95, y + 0.95, z, z + 3.0, mat)
    # Luffing crane in company colour on a portal base.
    cx, cy = 11.0, 6.0
    for dx in (-1.6, 1.6):
        for dy in (-1.6, 1.6):
            k.rod((cx + dx, cy + dy, 8.0), (cx + dx * 0.5, cy + dy * 0.5, 15.0), 0.2, "cc", n=4)
    k.cyl(cx, cy, 1.4, 15.0, 16.0, "cc", n=8)
    k.box(cx - 1.4, cx + 1.0, cy - 1.0, cy + 1.2, 16.0, 20.0, "cc_light")
    k.box(cx + 1.0, cx + 1.1, cy - 0.7, cy + 0.7, 17.0, 19.2, "glass")
    k.box(cx - 2.6, cx - 1.4, cy - 0.8, cy + 0.8, 16.0, 18.2, "steel_dark")
    tip = (cx - 3.0, cy + 9.0, 32.0)
    lattice(k, (cx, cy + 0.5, 19.0), tip, 0.9, "cc", r=0.1, step=2.0)
    k.rod(tip, (tip[0], tip[1], 14.0), 0.03, "dark", n=3)
    k.box(tip[0] - 0.5, tip[0] + 0.5, tip[1] - 0.5, tip[1] + 0.5, 13.0, 14.0, "dark")
    k.rod((cx, cy, 20.0), (cx - 0.2, cy, 24.0), 0.12, "cc", n=4)
    k.rod((cx - 0.2, cy, 24.0), tip, 0.03, "dark", n=3)


def buoy(k):
    """693: red can buoy with a white band and a light, centred on the tile."""
    cx, cy = 8.5, 8.5
    ring(k, cx, cy, 1.5, 2.3, 0.0, 0.05, "white", n=12)
    k.lathe(cx, cy, [(1.1, -0.5), (1.45, 0.4), (1.45, 2.2)], "red", n=10)
    k.lathe(cx, cy, [(1.45, 2.2), (1.45, 2.9)], "white", n=10)
    k.lathe(cx, cy, [(1.45, 2.9), (1.3, 3.6), (0.4, 4.0)], "red", n=10)
    for a in (0.6, 2.7, 4.8):
        k.rod((cx + 0.5 * math.cos(a), cy + 0.5 * math.sin(a), 3.9), (cx, cy, 8.0), 0.09, "red", n=3)
    k.cyl(cx, cy, 0.35, 8.0, 8.6, "dark", n=6)
    k.blob(cx, cy, 9.0, 0.35, 0.35, 0.6, "glow", subdiv=1)


# --- oil rig ------------------------------------------------------------------------------

def oil_rig(k, stage):
    """The whole rig in rig coordinates (tile (0,0) north corner at 0,0); stage 0 legs, 1 deck, 2 complete."""
    legs = [(19.0, 6.0), (29.0, 6.0), (19.0, 24.0), (29.0, 24.0), (19.0, 42.0), (29.0, 42.0)]
    leg_top = 30.0 if stage else 18.0
    for x, y in legs:
        k.cyl(x, y, 1.7, 0.0, leg_top, "concrete", n=10, r_top=1.4)
        k.cyl(x, y, 1.75, 0.0, 0.8, "concrete_dark", n=10)
    if stage == 0:
        for x, y in legs:
            k.cyl(x, y, 1.45, leg_top, leg_top + 0.6, "rig_yellow", n=10)
        return
    # Cellar deck truss and main deck.
    k.box(16.5, 31.5, 1.0, 47.0, 30.0, 31.0, "rig_yellow")
    for y in (1.0, 47.0):
        for x0, x1 in ((16.5, 31.5),):
            k.box(x0, x1, y - 0.3, y + 0.3, 31.0, 36.0, "rig_yellow")
    for x in (16.5, 31.5):
        k.box(x - 0.3, x + 0.3, 1.0, 47.0, 31.0, 31.6, "rig_yellow")
        k.box(x - 0.3, x + 0.3, 1.0, 47.0, 35.4, 36.0, "rig_yellow")
        for y in bk.frange(1.0, 47.0, 4.0):
            k.box(x - 0.25, x + 0.25, y - 0.25, y + 0.25, 31.0, 36.0, "rig_yellow")
        for ya, yb in zip(bk.frange(1.0, 47.0, 4.0), bk.frange(1.0, 47.0, 4.0)[1:]):
            k.rod((x, ya, 31.3), (x, yb, 35.7), 0.1, "rig_yellow", n=3)
    k.box(16.0, 32.0, 0.5, 47.5, 36.0, 37.2, "deck_green")
    if stage == 1:
        # Construction: crane and a few modules being placed.
        k.box(19.0, 27.0, 20.0, 28.0, 37.2, 44.0, "white")
        crane(k, (20.0, 40.0), 37.2, 2.2)
        return
    # Accommodation block (middle tile) with the lifeboat davits.
    k.box(18.0, 30.5, 15.0, 30.0, 37.2, 55.0, "white")
    k.windows(18.0, 30.5, 15.0, 30.0, 37.2, 55.0, floor=6.0, sill=1.6, wh=2.4, pitch=2.2)
    band(k, 18.0, 30.5, 15.0, 30.0, 54.4, 55.6, "orange")
    k.flat_roof(18.0, 30.5, 15.0, 30.0, 55.0, "white", parapet=0.6)
    for y in (18.0, 23.0):
        k.box(30.5, 32.0, y, y + 3.6, 40.0, 42.2, "orange")
    # Process modules and flare boom on the south part.
    k.box(18.0, 26.0, 31.5, 38.0, 37.2, 46.0, "steel")
    k.cyl(28.5, 34.0, 1.6, 37.2, 49.0, "tank", n=10)
    k.cyl(28.5, 37.5, 1.2, 37.2, 45.0, "steel", n=8)
    k.box(26.0, 31.0, 40.0, 46.5, 37.2, 41.0, "rig_red")
    # Drilling derrick over the south-east legs.
    base = (22.5, 43.0)
    k.box(base[0] - 3.0, base[0] + 3.0, base[1] - 3.0, base[1] + 3.0, 37.2, 41.0, "rig_red")
    w0, w1, z0, z1 = 2.6, 0.6, 41.0, 96.0
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for dx, dy in corners:
        k.rod((base[0] + dx * w0, base[1] + dy * w0, z0), (base[0] + dx * w1, base[1] + dy * w1, z1), 0.18, "white", n=4)
    levels = 9
    for i in range(levels):
        za, zb = bk.lerp(z0, z1, i / levels), bk.lerp(z0, z1, (i + 1) / levels)
        wa, wb = bk.lerp(w0, w1, i / levels), bk.lerp(w0, w1, (i + 1) / levels)
        for j in range(4):
            dx, dy = corners[j]
            ex, ey = corners[(j + 1) % 4]
            k.rod((base[0] + dx * wa, base[1] + dy * wa, za), (base[0] + ex * wb, base[1] + ey * wb, zb), 0.08,
                  "white", n=3)
            k.rod((base[0] + dx * wb, base[1] + dy * wb, zb), (base[0] + ex * wb, base[1] + ey * wb, zb), 0.08,
                  "rig_red" if i % 2 else "white", n=3)
    k.box(base[0] - 0.9, base[0] + 0.9, base[1] - 0.9, base[1] + 0.9, z1, z1 + 2.5, "rig_red")
    k.blob(base[0], base[1], z1 + 3.0, 0.3, 0.3, 0.5, "glow")
    crane(k, (19.5, 9.5), 37.2, 2.0)
    # Flare boom reaching out over the water to the south-west, with the flame.
    lattice(k, (30.5, 31.0, 40.0), (38.0, 23.5, 80.0), 1.0, "rig_yellow", r=0.12, step=2.6)
    k.cyl(38.0, 23.5, 0.6, 80.0, 81.5, "steel_dark", n=6)
    k.blob(38.0, 23.5, 83.0, 1.0, 1.0, 2.0, "fire", subdiv=1)
    k.cyl(38.0, 23.5, 1.0, 83.0, 92.0, "fire", n=7, r_top=0.0)
    k.cyl(38.0, 23.6, 0.55, 82.0, 87.0, "lamp", n=6, r_top=0.0)
    # Helideck on the north tile, cantilevered to the south-west; helicopters land at (31, 9, 54).
    hx, hy = 31.0, 9.0
    for dy in (-3.5, 3.5):
        k.rod((24.0, hy + dy, 37.0), (hx, hy + dy, 50.5), 0.25, "rig_yellow", n=4)
        k.rod((hx - 6.0, hy + dy, 37.2), (hx - 6.0, hy + dy, 52.0), 0.3, "rig_yellow", n=4)
    k.cyl(hx, hy, 6.2, 52.0, 54.0, "deck_green", n=8, rot=math.pi / 8)
    k.cyl(hx, hy, 6.5, 51.0, 52.0, "rig_yellow", n=8, rot=math.pi / 8)
    helipad_marking(k, hx, hy, 5.2, z=54.0)
    for i in range(8):
        a = i * math.tau / 8 + math.pi / 8
        k.cyl(hx + 6.1 * math.cos(a), hy + 6.1 * math.sin(a), 0.22, 54.0, 54.5, "lamp", n=5)


def crane(k, pos, z, s):
    x, y = pos
    k.cyl(x, y, 1.0 * s / 2, z, z + 10, "rig_red", n=8)
    k.box(x - 1.2, x + 1.2, y - 1.0, y + 1.0, z + 10, z + 13, "rig_red")
    k.box(x + 1.2, x + 1.3, y - 0.7, y + 0.7, z + 11, z + 12.5, "glass")
    tip = (x + 9.0, y - 4.0, z + 24)
    lattice(k, (x + 0.8, y, z + 12), tip, 0.6, "rig_red", r=0.08, step=2.2)
    k.rod(tip, (tip[0], tip[1], z + 4), 0.03, "dark", n=3)


RIG_SLICES = {  # sprite tile (x, y) -> keep x - y in [lo, hi)
    (1, 0): (16.0, None), (1, 1): (0.0, 16.0), (1, 2): (None, 0.0),
}
RIG_SPRITES = {  # sprite -> (tile, stage)
    2096: ((1, 0), 2), 2097: ((1, 1), 2), 2098: ((1, 2), 2),
    2100: ((1, 0), 1), 2101: ((1, 1), 1), 2102: ((1, 2), 1),
    2103: ((1, 0), 0), 2104: ((1, 1), 0), 2105: ((1, 2), 0),
}


def rig_slice(sprite):
    (tx, ty), stage = RIG_SPRITES[sprite]
    k = bk.Kit()
    oil_rig(k, stage)
    lo, hi = RIG_SLICES[tx, ty]
    parts = k.parts
    if lo is not None:
        parts = clip_plane(parts, (lo, 0, 0), (1, -1, 0))
    if hi is not None:
        parts = clip_plane(parts, (hi, 0, 0), (-1, 1, 0))
    return parts, (tx * 16, ty * 16)


# --- jobs -------------------------------------------------------------------------------

def canon_to(direction):
    """Vertex map from the canonical hangar frame (door +y) to a door facing direction."""
    return {
        "SE": lambda x, y, z: (x, y, z),
        "SW": lambda x, y, z: (y, x, z),
        "NW": lambda x, y, z: (x, 16 - y, z),
        "NE": lambda x, y, z: (16 - y, x, z),
    }[direction]


def hangar_parts(direction, door):
    rear, front = hangar_model(door)
    fn = canon_to(direction)
    transform(rear.parts, fn)
    transform(front.parts, fn)
    if direction == "SW":
        # Door to the SW: the rear sprite (box at x 0..2) is the back wall, now at x 0..0.7.
        back = [p for p in front.parts if max(v.co.x for v in p[1].verts) <= 0.71]
        front.parts = [p for p in front.parts if p not in back] + rear.parts
        rear.parts = back
    return rear.parts, front.parts


def building_jobs():
    """name -> (builder returning parts, shift, shadow parts or None)."""
    jobs = {}

    def simple(fn, shift, shadow=True):
        def build():
            k = bk.Kit()
            fn(k)
            return k.parts, shift, k.parts if shadow else None
        return build
    jobs["b2633"] = simple(heliport, (0, 0))
    jobs["b2650"] = simple(terminal_a, (2, 0))
    jobs["b2651"] = simple(tower, (3, 3))
    jobs["b2652"] = simple(concourse, (0, 1))
    jobs["b2653"] = simple(terminal_b, (3, 3))
    jobs["b2654"] = simple(terminal_c, (0, 3))
    jobs["b2668"] = simple(airfield_terminal, (0, 0))

    # Hangar fronts are drawn with their bounding box at (14, 0) but reach back to x = 0, which
    # lies beyond the building canvas when the box origin is at the canvas origin. They are
    # rendered from the tile's north corner instead; pack_airport.BOX_ORIGIN moves the offsets.
    def hangar(direction, which, door="open"):
        def build():
            rear, front = hangar_parts(direction, door)
            if door == "closed":
                return rear + front, (0, 0), rear + front
            if which == "rear":
                return rear, (0, 0), None
            return front, (0, 0), rear + front
        return build
    jobs["b2655"] = hangar("SE", "front")
    jobs["b2656"] = hangar("SE", "rear")
    jobs["bx6"] = hangar("SE", "front")
    jobs["bx7"] = hangar("SE", "rear")
    jobs["bx8"] = hangar("SW", "front")
    jobs["bx9"] = hangar("SW", "rear")
    jobs["bx10"] = hangar("NW", "front", door="closed")
    jobs["bx11"] = hangar("NE", "front", door="closed")

    def small_hangar(which):
        def build():
            rear, front = airfield_hangar()
            if which == "rear":
                return rear.parts, (0, 0), None
            return front.parts, (0, 0), rear.parts + front.parts
        return build
    jobs["b2657"] = small_hangar("front")
    jobs["b2658"] = small_hangar("rear")
    jobs["b2659"] = simple(lambda k: jetway(k, [(8.5, 16.0), (8.5, 11.5)]), (7, 11))
    jobs["b2660"] = simple(lambda k: jetway(k, [(0.5, 8.5), (5.0, 8.5)]), (2, 7))
    jobs["b2661"] = simple(lambda k: jetway(k, [(4.5, 0.5), (4.5, 4.0), (1.5, 4.0)]), (3, 2))

    def tunnel(k):
        k.box(0, 16, 8.6, 10.4, 7.0, 11.6, "white")
        k.box(0, 16, 8.5, 10.5, 8.4, 10.4, "glass_light")
        k.box(0, 16, 8.4, 10.6, 11.6, 12.2, "cc")
        for x in (4.0, 12.0):
            k.cyl(x, 9.5, 0.4, 0, 7.0, "steel_dark", n=6)
    jobs["b2662"] = simple(tunnel, (0, 8))
    jobs["b2663"] = simple(lambda k: fence(k, "y"), (0, 0), shadow=False)
    jobs["b2664"] = simple(lambda k: fence(k, "x"), (0, 0), shadow=False)
    for f in range(4):
        jobs[f"b{2676 + f}"] = simple(lambda k, f=f: windsock(k, f), (4, 11))
    for f in range(12):
        jobs[f"b{2680 + f}"] = simple(lambda k, f=f: radar(k, f), (7, 7))
    jobs["bx12"] = simple(raised_helipad, (0, 1), shadow=False)
    jobs["bgui86"] = simple(lambda k: helipad_marking(k, 8, 8, 6.0), (10, 6), shadow=False)

    # Docks: the slope sprite's ground slope (table _station_display_datas_dock) puts the water
    # to NE (2727), SE (2728), SW (2729), NW (2730).
    to_water = {2727: "NE", 2728: "SE", 2729: "SW", 2730: "NW"}
    dock_map = {  # canonical frame: water to -x, deck along x
        "NE": lambda x, y, z: (x, y, z),
        "SW": lambda x, y, z: (16 - x, y, z),
        "NW": lambda x, y, z: (y, x, z),
        "SE": lambda x, y, z: (y, 16 - x, z),
    }
    for sprite, water in to_water.items():
        def build(water=water):
            k = bk.Kit()
            dock_slope(k, water)
            parts = transform(k.parts, dock_map[water])
            shift = (0, 4) if water in ("NE", "SW") else (4, 0)
            return parts, shift, None  # a flat shadow catcher would not follow the slope
        jobs[f"b{sprite}"] = build

    def flat(axis):
        def build():
            k = bk.Kit()
            dock_flat(k)
            parts = k.parts if axis == "x" else transform(k.parts, lambda x, y, z: (y, x, z))
            return parts, (0, 4) if axis == "x" else (4, 0), parts
        return build
    jobs["b2731"] = flat("x")
    jobs["b2732"] = flat("y")
    jobs["b693"] = simple(buoy, (4, -1), shadow=False)
    for sprite in RIG_SPRITES:
        def build(sprite=sprite):
            parts, shift = rig_slice(sprite)
            return parts, shift, None
        jobs[f"rig{sprite}"] = build
    return jobs


# Ground sprites: name -> (texture, props builder or None)
def ground_jobs():
    def lights(along, end=False):
        def build():
            k = bk.Kit()
            runway_lights(k, along, end)
            return k
        return build

    def markers():
        k = bk.Kit()
        airfield_markers(k)
        return k
    jobs = {"g2635": ("stand2635", None)}
    jobs.update({f"g{s}": (f"taxi{s}", None) for s in range(2636, 2645)})
    jobs.update({f"g{s}": (f"rwy{s}", lights("x")) for s in range(2645, 2649)})
    jobs["g2649"] = ("rwyend2649", lights("x", end=True))
    for s in (2665, 2666, 2667):
        jobs[f"g{s}"] = (f"afterm{s}", lambda s=s: airfield_ground_props(s))
    jobs.update({f"g{s}": (f"afgrass{s}", None) for s in range(2669, 2673)})
    jobs.update({f"g{s}": (f"afrwy{s}", markers) for s in range(2673, 2676)})
    jobs["gx0"] = ("x_tarmac", None)
    jobs.update({f"gx{k}": (f"x_rwy{k}", lights("y")) for k in range(1, 5)})
    jobs["gx5"] = ("x_rwyend", lights("y", end=True))
    return jobs


OVERLAY_GROUNDS = {"gx13": "x_grass_right", "gx14": "x_grass_left"}


def render_overlay_ground(outdir, name, tex):
    """Grass half drawn over the apron: texture alpha, cut to the tile by the mask pass."""
    for zoom in bk.ZOOMS:
        zdir = os.path.join(outdir, f"z{zoom}")
        os.makedirs(zdir, exist_ok=True)
        scene = bk.new_scene(zoom, bk.GROUND_SIZE, bk.GROUND_SIZE, bk.GROUND_ANCHOR)
        rg.build_tile(0, 1.0).data.materials.append(st.bank_material(st.texture(f"airport/{tex}")))
        bk.render(scene, os.path.join(zdir, f"{name}_color.png"))
        scene = bk.new_scene(zoom, bk.GROUND_SIZE, bk.GROUND_SIZE, bk.GROUND_ANCHOR, samples=16)
        scene.cycles.filter_width = 0.01
        rg.build_tile(0, 1.0).data.materials.append(rg.mask_material())
        bk.render(scene, os.path.join(zdir, f"{name}_mask.png"))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv and not argv[0].startswith("--") else os.path.join(os.getcwd(), "render", "airports")
    only = tuple(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    part, parts = map(int, argv[argv.index("--part") + 1].split("/")) if "--part" in argv else (0, 1)
    work = [("b", n, fn) for n, fn in building_jobs().items()]
    work += [("g", n, job) for n, job in ground_jobs().items()]
    work += [("o", n, tex) for n, tex in OVERLAY_GROUNDS.items()]
    for i, (what, name, job) in enumerate(work):
        if i % parts != part or (only and not name.startswith(only)):
            continue
        if what == "b":
            p, shift, shadow = job()
            bk.render_building(outdir, name, p, shift, cc=CC, shadow_parts=shadow,
                               shadow_tiles=[(0, 0)] if shadow else ())
        elif what == "g":
            tex, props = job
            pk = props() if props else None
            bk.render_ground(outdir, name, f"airport/{tex}", (), (0, 0), pk.parts if pk else (), cc=CC)
        else:
            render_overlay_ground(outdir, name, job)
        print(f"rendered {name}", flush=True)


if __name__ == "__main__":
    main()
