"""Render the rail and road bridge sprites (2437-2580) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_bridges.py -- <outdir> [<ref/bridges/usage.json>] [--families a,b]

usage.json (built from table/bridge_land.h) tells for every sprite how the game
uses it: bridge head (direction, ramp or flat) or middle element (back = deck
plus the far side, front = the near side, pillar) for a section (north, south,
inner, middle) of a bridge family. Geometry is built in tile units with a
running along the bridge (0 = north end of the tile) and c across it.

Families: wood, concrete (kerb and plain steel railing, shared with the suspension
bridges' even middle tiles), archgirder (one arch per tile), girder
(lattice side girders), suspension (pylons and sagging cables), cantilever
(truss rising towards the ends), tubular (tube arch). Steel parts are rendered
neutral grey and flagged in a second pass; the packer gives them palette index
75 so the game's PALETTE_TO_STRUCT_* recolours (indices 70-79) still tint them
per bridge type. Anchors follow DrawBridgeMiddle(): back at (0, 0, deck - 3),
front and pillars at (0, 12) resp. (12, 0), pillars one level per sprite;
heads at the tile origin with the deck one level up.

Outputs: <outdir>/z<zoom>/br<sprite>_overlay.png and br<sprite>_cc.png.
Canvas 96z x 128z with the sprite origin at (47z, 72z).
"""

import json
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
CANVAS_W, CANVAS_H, ANCHOR_Y = 96, 128, 72
HERE = os.path.dirname(os.path.abspath(__file__))
INFRA = os.path.join(HERE, "..", "render", "textures", "infra")
UNIT = oc.LEVEL / 8

CONCRETE = (176, 174, 166)
CONCRETE_DARK = (146, 144, 136)
TIMBER = (132, 98, 66)
TIMBER_DARK = (104, 78, 54)
STEEL = (128, 128, 128)  # recoloured in game through the mask
RAIL_GREY = (150, 154, 160)
RAIL_TOP = 3.4  # top rail of the steel railings above the deck

DECK_C0, DECK_C1, DECK_T = 2.0, 14.0, 3.0
SIDE_BACK, SIDE_FRONT = 2.6, 13.4


def family_of(uses):
    names = {u["tname"] for u in uses}
    if any(n == "wood" for n in names):
        return "wood"
    for fam in ("archgirder", "girder", "suspension", "cantilever", "tubular"):
        if all(n.startswith(fam) for n in names):
            return fam
    return "concrete"


class B:
    def __init__(self, axis, anchor_ac, cc_pass, base_z=0.0):
        self.axis = axis
        self.anchor = anchor_ac
        self.cc = cc_pass
        self.base_z = base_z
        self.mats = {}

    def p(self, a, c, z):
        a -= self.anchor[0]
        c -= self.anchor[1]
        x, y = (a, c) if self.axis == "X" else (c, a)
        return oc.CORNERS["N"] + Vector((y / 16, -x / 16, (z - self.base_z) * UNIT))

    def mat(self, rgb, steel=False, image=None):
        key = (rgb, steel, image)
        if key not in self.mats:
            if self.cc:
                self.mats[key] = st.toon_material("m", (255, 255, 255) if steel else (0, 0, 0), params=st.FLAT)
            elif image:
                self.mats[key] = st.toon_material("deck", image_path=image, params=st.GROUND, extension="EXTEND")
            else:
                self.mats[key] = st.toon_material(str(rgb), rgb, params=st.OBJECT)
        return self.mats[key]

    def mesh(self, name, faces, rgb, steel=False, image=None):
        bm = bmesh.new()
        for f in faces:
            bm.faces.new([bm.verts.new(v) for v in f])
        bm.normal_update()
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for poly in mesh.polygons:
            poly.use_smooth = False
        mesh.materials.append(self.mat(rgb, steel, image))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)

    def box(self, name, a0, a1, c0, c1, z0, z1, rgb, steel=False):
        P = self.p
        v = [[[P(a, c, z) for z in (z0, z1)] for c in (c0, c1)] for a in (a0, a1)]
        faces = [[v[0][0][0], v[1][0][0], v[1][1][0], v[0][1][0]], [v[0][0][1], v[0][1][1], v[1][1][1], v[1][0][1]],
                 [v[0][0][0], v[0][0][1], v[1][0][1], v[1][0][0]], [v[0][1][0], v[1][1][0], v[1][1][1], v[0][1][1]],
                 [v[0][0][0], v[0][1][0], v[0][1][1], v[0][0][1]], [v[1][0][0], v[1][0][1], v[1][1][1], v[1][1][0]]]
        self.mesh(name, faces, rgb, steel)

    def beam(self, name, a0, z0, a1, z1, c, w, rgb, steel=True):
        """Thin member in the side plane c from (a0, z0) to (a1, z1), w tile units thick."""
        da, dz = a1 - a0, (z1 - z0) * UNIT * 16  # compare in tile units
        length = math.hypot(da, dz) or 1
        na, nz = -dz / length * w / 2, da / length * w / 2 / (UNIT * 16)
        q = [(a0 + na, z0 + nz), (a1 + na, z1 + nz), (a1 - na, z1 - nz), (a0 - na, z0 - nz)]
        faces = []
        P = self.p
        f0 = [P(a, c - w / 2, z) for a, z in q]
        f1 = [P(a, c + w / 2, z) for a, z in q]
        faces += [f0, list(reversed(f1))]
        for i in range(4):
            j = (i + 1) % 4
            faces.append([f0[i], f0[j], f1[j], f1[i]])
        self.mesh(name, faces, rgb, steel)


# --- deck and railings ------------------------------------------------------

def deck(b, transport, wood, z_at=lambda a: DECK_T):
    """Deck slab and surface; z_at gives the surface height along a."""
    rgb = TIMBER if wood else CONCRETE_DARK
    tex = os.path.join(INFRA, f"deck_{transport}_{b.axis}{'_wood' if wood else ''}.png")
    n = 8
    top, side_back, side_front, bottom = [], [], [], []
    for i in range(n):
        a0, a1 = 16 * i / n, 16 * (i + 1) / n
        z0, z1 = z_at(a0), z_at(a1)
        top.append([b.p(a0, DECK_C0, z0), b.p(a1, DECK_C0, z1), b.p(a1, DECK_C1, z1), b.p(a0, DECK_C1, z0)])
        for c, lst in ((DECK_C0, side_back), (DECK_C1, side_front)):
            lst.append([b.p(a0, c, z0 - DECK_T), b.p(a1, c, z1 - DECK_T), b.p(a1, c, z1), b.p(a0, c, z0)])
        bottom.append([b.p(a0, DECK_C0, z0 - DECK_T), b.p(a0, DECK_C1, z0 - DECK_T),
                       b.p(a1, DECK_C1, z1 - DECK_T), b.p(a1, DECK_C0, z1 - DECK_T)])
    b.mesh("deck_top", top, rgb, image=tex)
    b.mesh("deck_sides", side_back + side_front + bottom, rgb)


def railing(b, c, style, z_at=lambda a: DECK_T):
    wood = style == "wood"
    rgb, steel = (TIMBER_DARK, False) if wood else (STEEL, True)
    if style == "plain":
        # Unrecoloured steel railing on a concrete kerb: the concrete family's middle sprites
        # are shared with the suspension bridges' even middle tiles (bridge_land.h).
        b.box("kerb", 0, 16, c - 0.5, c + 0.5, z_at(0), z_at(0) + 0.9, CONCRETE)
        rgb, steel = RAIL_GREY, False
    for i in range(5):
        a = 0.6 + 14.8 * i / 4
        b.box(f"post{i}", a - 0.25, a + 0.25, c - 0.25, c + 0.25, z_at(a), z_at(a) + 3.6, rgb, steel)
    for h in (1.8, RAIL_TOP):
        b.beam(f"rail{h}", 0, z_at(0) + h, 16, z_at(16) + h, c, 0.3, rgb, steel)


# --- superstructures ----------------------------------------------------------

def cable_profile(piece):
    """(pylons as a positions, cable height above the deck at a = 0 and a = 16) per section."""
    # The cable falls from the end pylons to railing height and rises again in two-tile waves
    # (inner_north falls, inner_south rises, see CalcBridgePiece); an odd middle tile carries a
    # centre pylon, an even one is plain deck (the concrete bridge's sprites) whose top rail
    # continues the cable where it lands on the railing.
    return {
        "north": ([0.8], (24, 12)), "south": ([15.2], (12, 24)),
        "inner_north": ([], (12, RAIL_TOP)), "inner_south": ([], (RAIL_TOP, 12)),
        "middle_odd": ([8.0], (12, 12)), "middle_even": ([], (RAIL_TOP, RAIL_TOP)),
    }[piece]


def suspension(b, c, piece):
    towers, (h0, h1) = cable_profile(piece)
    top = DECK_T + 24
    for t in towers:
        b.box(f"tower{t}", t - 0.8, t + 0.8, c - 0.8, c + 0.8, 0, top, STEEL, True)
        b.box(f"cap{t}", t - 1.0, t + 1.0, c - 1.0, c + 1.0, top, top + 0.8, STEEL, True)
    # Cable: straight from the ends to the tower top, or between the end heights.
    pts = [(0.0, DECK_T + h0)]
    for t in towers:
        pts.append((t, top))
    pts.append((16.0, DECK_T + h1))
    pts.sort()
    for i in range(len(pts) - 1):
        (a0, z0), (a1, z1) = pts[i], pts[i + 1]
        b.beam(f"cable{i}", a0, z0, a1, z1, c, 0.35, STEEL, True)
    # Hangers every 2 units down to the deck edge.
    for k in range(1, 8):
        a = 2.0 * k
        if any(abs(a - t) < 1.2 for t in towers):
            continue
        for i in range(len(pts) - 1):
            (a0, z0), (a1, z1) = pts[i], pts[i + 1]
            if a0 <= a <= a1:
                z = z0 + (z1 - z0) * (a - a0) / (a1 - a0)
                b.beam(f"hanger{k}", a, DECK_T, a, z, c, 0.15, STEEL, True)
    railing(b, c, "steel")


def truss(b, c, top_at, name="truss", w=0.4):
    """Warren truss in the side plane: bottom chord on the deck, top chord at top_at(a)."""
    b.beam(f"{name}_bottom", 0, DECK_T, 16, DECK_T, c, w, STEEL, True)
    b.beam(f"{name}_top", 0, top_at(0), 16, top_at(16), c, w, STEEL, True)
    for k in range(5):
        a = 4.0 * k
        b.beam(f"{name}_v{k}", a, DECK_T, a, top_at(a), c, w * 0.8, STEEL, True)
        if k < 4:
            if k % 2 == 0:
                b.beam(f"{name}_d{k}", a, DECK_T, a + 4, top_at(a + 4), c, w * 0.7, STEEL, True)
            else:
                b.beam(f"{name}_d{k}", a, top_at(a), a + 4, DECK_T, c, w * 0.7, STEEL, True)


def cantilever(b, c, piece):
    low, high = DECK_T + 7, DECK_T + 15
    if piece == "north":
        f = lambda a: low + (high - low) * a / 16  # noqa: E731
    elif piece == "south":
        f = lambda a: high - (high - low) * a / 16  # noqa: E731
    else:
        f = lambda a: high  # noqa: E731
    truss(b, c, f)


def tubular(b, c, piece):
    rise = DECK_T + 14
    if piece == "north":
        f = lambda a: DECK_T + 2 + (rise - DECK_T - 2) * math.sin(a / 16 * math.pi / 2)  # noqa: E731
    elif piece == "south":
        f = lambda a: DECK_T + 2 + (rise - DECK_T - 2) * math.cos(a / 16 * math.pi / 2)  # noqa: E731
    else:
        f = lambda a: rise  # noqa: E731
    steps = 8
    for i in range(steps):
        a0, a1 = 16 * i / steps, 16 * (i + 1) / steps
        b.beam(f"tube{i}", a0, f(a0), a1, f(a1), c, 0.9, STEEL, True)
    for k in range(1, 4):
        a = 4.0 * k
        b.beam(f"post{k}", a, DECK_T, a, f(a), c, 0.25, STEEL, True)
        b.beam(f"diag{k}", a - 4, DECK_T, a, f(a), c, 0.2, STEEL, True)
    railing(b, c, "steel")


def arch(b, c):
    steps = 10
    f = lambda a: DECK_T + 11 * math.sin(a / 16 * math.pi)  # noqa: E731
    for i in range(steps):
        a0, a1 = 16 * i / steps, 16 * (i + 1) / steps
        b.beam(f"arch{i}", a0, f(a0), a1, f(a1), c, 0.6, STEEL, True)
    for k in range(1, 8):
        a = 2.0 * k
        b.beam(f"hanger{k}", a, DECK_T, a, f(a), c, 0.15, STEEL, True)
    railing(b, c, "steel")


def girder(b, c):
    truss(b, c, lambda a: DECK_T + 5.5, name="girder", w=0.5)
    b.box("web", 0, 16, c - 0.15, c + 0.15, DECK_T, DECK_T + 0.6, STEEL, True)


def superstructure(b, fam, piece, c):
    if fam == "wood":
        railing(b, c, "wood")
    elif fam == "concrete":
        railing(b, c, "plain")
    elif fam == "archgirder":
        arch(b, c)
    elif fam == "girder":
        girder(b, c)
    elif fam == "suspension":
        suspension(b, c, piece)
    elif fam == "cantilever":
        cantilever(b, c, piece)
    elif fam == "tubular":
        tubular(b, c, piece)


def pillar(b, fam):
    """One level of pier below the deck at a = 8, c = 13.4 (the game repeats it downwards and draws a copy 9 units back)."""
    a, c = 8.0, SIDE_FRONT
    if fam == "wood":
        b.box("leg", a - 0.5, a + 0.5, c - 0.5, c + 0.5, -8, 0, TIMBER_DARK)
        b.beam("brace", a - 0.5, -7.5, a + 0.5, -0.5, c, 0.3, TIMBER_DARK, False)
    elif fam in ("suspension", "concrete"):
        b.box("pier", a - 1.6, a + 1.6, c - 1.2, c + 1.2, -8, 0, CONCRETE)
    else:
        b.box("pier", a - 0.9, a + 0.9, c - 0.9, c + 0.9, -8, 0, STEEL, True)


def head(b, transport, fam, direction, ramp):
    """Bridge head: deck from the ground (ramp) or flat one level up, on an abutment, with railings."""
    rises_with_a = direction in ("SW", "SE")  # bridge lies towards larger a
    if ramp:
        z_at = (lambda a: 8 * a / 16) if rises_with_a else (lambda a: 8 * (1 - a / 16))
    else:
        z_at = lambda a: 8.0  # noqa: E731
    wood = fam == "wood"
    deck(b, transport, wood, z_at)
    # Abutment under the deck down to the ground.
    n = 8
    faces = []
    for i in range(n):
        a0, a1 = 16 * i / n, 16 * (i + 1) / n
        z0, z1 = max(0.0, z_at(a0) - DECK_T), max(0.0, z_at(a1) - DECK_T)
        for cc in (DECK_C0 + 0.3, DECK_C1 - 0.3):
            faces.append([b.p(a0, cc, 0), b.p(a1, cc, 0), b.p(a1, cc, z1), b.p(a0, cc, z0)])
    b.mesh("abutment", faces, TIMBER_DARK if wood else CONCRETE)
    style = "wood" if wood else "steel"
    railing(b, SIDE_BACK, style, z_at)
    railing(b, SIDE_FRONT, style, z_at)


def build(sprite, uses, cc_pass):
    fam = family_of(uses)
    u = next((x for x in uses if x["transport"] in ("rail", "road")), uses[0])
    transport = u["transport"] if u["transport"] in ("rail", "road") else "rail"
    if u["kind"] == "head":
        axis = "X" if u["dir"] in ("NE", "SW") else "Y"
        b = B(axis, (0, 0), cc_pass)
        head(b, transport, fam, u["dir"], u["ramp"])
        return
    axis, element, piece = u["axis"], u["element"], u["piece"]
    if element == "back":
        b = B(axis, (0, 0), cc_pass)
        deck(b, transport, fam == "wood")
        superstructure(b, fam, piece, SIDE_BACK)
    elif element == "front":
        b = B(axis, (0, 12), cc_pass)
        superstructure(b, fam, piece, SIDE_FRONT)
    else:
        # DrawBridgePillars() gets the coordinates already moved by 12 for the front part.
        b = B(axis, (0, 12), cc_pass)
        pillar(b, fam)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "bridges")
    usage_path = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else os.path.join(HERE, "..", "ref", "bridges", "usage.json")
    usage = json.load(open(usage_path))
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    families = argv[argv.index("--families") + 1].split(",") if "--families" in argv else None
    for sid, uses in usage.items():
        if not {x["transport"] for x in uses} & {"rail", "road"}:
            continue
        if families and family_of(uses) not in families:
            continue
        for zoom in ZOOMS:
            for cc_pass in (False, True):
                bpy.ops.wm.read_factory_settings(use_empty=True)
                scene = bpy.context.scene
                st.configure_render(scene, samples=16 if cc_pass else 48)
                if cc_pass:
                    scene.cycles.filter_width = 0.01
                oc.setup_camera(scene, zoom, CANVAS_W * zoom, CANVAS_H * zoom, anchor_y=ANCHOR_Y)
                build(int(sid), uses, cc_pass)
                suffix = "cc" if cc_pass else "overlay"
                scene.render.filepath = os.path.join(outdir, f"z{zoom}", f"br{sid}_{suffix}.png")
                bpy.ops.render.render(write_still=True)
        print(f"rendered bridge sprite {sid} ({family_of(uses)})", flush=True)


if __name__ == "__main__":
    main()
