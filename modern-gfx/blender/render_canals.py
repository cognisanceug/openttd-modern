"""Render canal locks (24 wall sprites) and ship depots (4070-4075) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_canals.py -- <outdir> [--only locks|depots]

Locks: the game draws each of the three lock tiles (lower, middle, upper) as
water ground plus two wall sprites, a rear one anchored at (0, 0) and a front
one at (0, 15) (X axis) or (15, 0) (Y axis), see table/water_land.h. With our
own canal-feature definition (WF_LOCKS) the 24 sprites are indexed
  part * 8 + side * 4 + direction    part: middle 0, lower 1, upper 2
                                     side: rear 0, front 1
                                     direction: SE 0, NE 1, SW 2, NW 3
and drawn at the tile's base height. The lock rises towards its direction (the
upper tile lies on that side). Model: stone quay walls with light coping, the
chamber walls one level higher than the upper water, the lower walls stepping
down from the lower gate; mitre gates stand open in recesses of the walls with
black-and-white balance beams on the coping.

Ship depots: a boathouse over two water tiles (DepotPart north and south along
the axis). North tile: one sprite at the front (4072 X, 4073 Y) with both walls
and its half of the roof; south tile: the rear wall (4074, 4075) and the front
part with its half of the roof (4070, 4071). 4070-4073 carry a company-colour
eaves band (cc pass).

Output: <outdir>/z<zoom>/lock<k>_overlay.png, depot<sprite>_overlay.png and _cc.png
Canvas 192z x 144z px with the sprite origin at (95z, 80z), as for the rail depots.
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
Z_UNIT = oc.LEVEL / 8  # one OpenTTD height unit (8 per level)

STONE = (184, 174, 152)
STONE_DARK = (150, 142, 124)
COPING = (214, 208, 194)
TIMBER = (92, 76, 60)
BEAM = (52, 54, 58)
BEAM_TIP = (232, 232, 228)
BOLLARD = (60, 62, 66)

WALL = (222, 214, 196)
ROOF = (96, 104, 112)
TRIM = (128, 128, 128)  # company colour, see the cc pass
OPENING = (40, 46, 52)
WINDOW = (110, 140, 160)

LOCK_DIRS = ("SE", "NE", "SW", "NW")
WALL_T = 1.5      # wall thickness (units, 16 per tile)
TOP_LOW = 3       # wall top above the water on the upper and lower tiles' far ends
TOP_HIGH = 8 + 3  # chamber wall top: one level plus the coping height


def lock_xy(direction, a, c):
    """Lock frame (a along the lock from its high end, c across from the rear side) -> tile x, y."""
    return {"NE": (a, c), "SW": (16 - a, c), "NW": (c, a), "SE": (c, 16 - a)}[direction]


class Builder:
    """Low-poly boxes in OpenTTD units (x, y 0-16 per tile, z 8 per level) around a sprite anchor."""

    def __init__(self, anchor, cc_pass, to_xy):
        self.anchor = anchor
        self.cc_pass = cc_pass
        self.to_xy = to_xy
        self.materials = {}

    def mat(self, rgb, cc=False, params=None):
        key = (rgb, cc)
        if key not in self.materials:
            if self.cc_pass:
                self.materials[key] = st.toon_material("cc" if cc else "black", (255, 255, 255) if cc else (0, 0, 0),
                                                       params=st.FLAT)
            elif rgb is None:
                self.materials[key] = holdout_material()
            else:
                self.materials[key] = st.toon_material(str(rgb), rgb, params=params or st.OBJECT)
        return self.materials[key]

    def point(self, a, c, z):
        x, y = self.to_xy(a, c)
        x -= self.anchor[0]
        y -= self.anchor[1]
        return oc.CORNERS["N"] + Vector((y / 16, -x / 16, z * Z_UNIT))

    def poly_mesh(self, name, faces, rgb, cc=False, params=None):
        bm = bmesh.new()
        for face in faces:
            bm.faces.new([bm.verts.new(p) for p in face])
        bm.normal_update()
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for p in mesh.polygons:
            p.use_smooth = False
        mesh.materials.append(self.mat(rgb, cc, params))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)

    def prism(self, name, a0, a1, c0, c1, bottom, top, rgb, cc=False, params=None):
        """Box between a0..a1 and c0..c1 whose bottom and top heights may vary linearly along a.

        bottom/top: number or (z at a0, z at a1).
        """
        lo = bottom if isinstance(bottom, tuple) else (bottom, bottom)
        hi = top if isinstance(top, tuple) else (top, top)
        p = lambda a, c, k, zz: self.point(a, c, zz[k])  # noqa: E731
        v = {(i, j, k): p((a0, a1)[i], (c0, c1)[j], i, (lo, hi)[k]) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
        faces = [
            [v[0, 0, 0], v[1, 0, 0], v[1, 1, 0], v[0, 1, 0]], [v[0, 0, 1], v[0, 1, 1], v[1, 1, 1], v[1, 0, 1]],
            [v[0, 0, 0], v[0, 0, 1], v[1, 0, 1], v[1, 0, 0]], [v[0, 1, 0], v[1, 1, 0], v[1, 1, 1], v[0, 1, 1]],
            [v[0, 0, 0], v[0, 1, 0], v[0, 1, 1], v[0, 0, 1]], [v[1, 0, 0], v[1, 0, 1], v[1, 1, 1], v[1, 1, 0]],
        ]
        self.poly_mesh(name, faces, rgb, cc, params)


def holdout_material():
    mat = bpy.data.materials.new("holdout")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(nt.nodes.new("ShaderNodeHoldout").outputs[0], out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------- locks

def lock_profile(part, a):
    """(water z, wall top z) at position a along the lock part."""
    if part == "middle":
        return 8 - a / 2, TOP_HIGH
    if part == "upper":
        return 0, TOP_LOW
    # Lower tile: chamber height up to the gate, then the wing walls step down.
    t = min(1.0, max(0.0, (a - 8.5) / 5.5))
    return 0, TOP_HIGH + (TOP_LOW - TOP_HIGH) * t


def build_lock(part, side, direction):
    rear = side == "rear"
    anchor = (0, 0) if rear else ((0, 15) if direction in ("NE", "SW") else (15, 0))
    b = Builder(anchor, False, lambda a, c: lock_xy(direction, a, c))
    c0, c1 = (0, WALL_T) if rear else (16 - WALL_T, 16)
    inner = c1 if rear else c0  # the wall face towards the water
    out = 1 if rear else -1     # direction across from the water towards the wall

    # Water surface as holdout, so wall parts below the water are cut.
    w0, w1 = lock_profile(part, 0)[0], lock_profile(part, 16)[0]
    b.prism("water", 0, 16, WALL_T, 16 - WALL_T, (w0 - 0.2, w1 - 0.2), (w0, w1), None)

    # Wall in segments along a, so sloped tops and bottoms follow the profile.
    steps = [0, 4, 6, 8.5, 10, 12, 14, 16]
    for i in range(len(steps) - 1):
        a0, a1 = steps[i], steps[i + 1]
        (wa0, ta0), (wa1, ta1) = lock_profile(part, a0), lock_profile(part, a1)
        bottom = (min(wa0, 0) - 2, min(wa1, 0) - 2)
        b.prism(f"wall{i}", a0, a1, c0, c1, bottom, (ta0 - 0.8, ta1 - 0.8), STONE, params=st.WALL)
        # Coping, slightly wider than the wall towards the water.
        cc0, cc1 = (c0, c1 + 0.25) if rear else (c0 - 0.25, c1)
        b.prism(f"coping{i}", a0, a1, cc0, cc1, (ta0 - 0.8, ta1 - 0.8), (ta0, ta1), COPING)
        # Dark wet band just above the water line.
        band0, band1 = (inner - 0.05, inner + 0.01) if rear else (inner - 0.01, inner + 0.05)
        b.prism(f"wet{i}", a0, a1, band0, band1, (wa0 - 0.5, wa1 - 0.5), (wa0 + 1.2, wa1 + 1.2), STONE_DARK,
                params=st.WALL)

    # Gates: open mitre leaves along the wall, balance beam on the coping.
    gate_a = {"upper": 13.0, "lower": 1.5}.get(part)
    if gate_a is not None:
        water, top = lock_profile(part, gate_a)
        leaf_c0, leaf_c1 = (inner, inner + 0.6) if rear else (inner - 0.6, inner)
        gate_bottom = 0 if part == "upper" else -1
        # The open leaves fold towards the chamber's far side: upstream on the upper, downstream on the lower tile.
        la0, la1 = (gate_a - 6.5, gate_a) if part == "upper" else (gate_a, gate_a + 6.5)
        b.prism("leaf", la0, la1, leaf_c0, leaf_c1, gate_bottom, top - 1.0, TIMBER)
        b.prism("leaf_cap", la0, la1, leaf_c0, leaf_c1, top - 1.0, top - 0.6, BEAM)
        # Beam from the gate post outwards over the coping, white tip.
        bc = (c0, c1) if rear else (c0, c1)
        mid = (bc[0] + bc[1]) / 2
        b.prism("beam", gate_a - 0.4, gate_a + 0.4, mid - out * 0.3 - 0.35, mid - out * 0.3 + 0.35, top + 0.3,
                top + 1.1, BEAM)
        tip_c = mid + out * 3.2
        lo_c, hi_c = sorted((mid + out * 0.4, tip_c))
        b.prism("beam_arm", gate_a - 0.35, gate_a + 0.35, lo_c, hi_c, top + 0.6, top + 1.2, BEAM)
        lo_t, hi_t = sorted((tip_c - out * 1.0, tip_c))
        b.prism("beam_tip", gate_a - 0.36, gate_a + 0.36, lo_t, hi_t, top + 0.59, top + 1.21, BEAM_TIP)
    # Bollards on the coping.
    for a in ((4.5, 11.5) if part == "middle" else (8.0,)):
        top = lock_profile(part, a)[1]
        mid = (c0 + c1) / 2
        b.prism(f"bollard{a}", a - 0.35, a + 0.35, mid - 0.35, mid + 0.35, top, top + 1.4, BOLLARD)


def lock_sprites():
    """(index, part, side, direction) for all 24 WF_LOCKS sprites."""
    out = []
    for p, part in enumerate(("middle", "lower", "upper")):
        for s, side in enumerate(("rear", "front")):
            for d, direction in enumerate(LOCK_DIRS):
                out.append((p * 8 + s * 4 + d, part, side, direction))
    return out


# ---------------------------------------------------------------- ship depots

DEPOTS = {
    # sprite: (axis, tile 0 north / 1 south, part, anchor in tile units, company colour)
    4072: ("X", 0, "all", (0, 15), True),
    4074: ("X", 1, "rear", (0, 0), False),
    4070: ("X", 1, "front", (0, 15), True),
    4073: ("Y", 0, "all", (15, 0), True),
    4075: ("Y", 1, "rear", (0, 0), False),
    4071: ("Y", 1, "front", (15, 0), True),
}
EAVES, RIDGE = 13, 22  # heights in units
SHED_T = 1.0


def build_depot(axis, tile, part, anchor, cc_pass):
    # a runs along the axis over both tiles (0-32), c across (0 rear .. 16 front).
    def to_xy(a, c):
        a -= 16 * tile
        return (a, c) if axis == "X" else (c, a)

    b = Builder(anchor, cc_pass, to_xy)
    a0, a1 = 16 * tile, 16 * tile + 16
    first, last = tile == 0, tile == 1
    rear = part in ("all", "rear")
    front = part in ("all", "front")
    roof = part in ("all", "front")
    win = [(a, a + 2.4) for a in range(a0 + 2, a1 - 1, 4)]

    def side_wall(name, c0, c1, outer):
        b.prism(name, a0, a1, c0, c1, -1, EAVES, WALL, params=st.WALL)
        for i, (wa, wb) in enumerate(win):
            oc0, oc1 = (c0 - 0.05, c0 + 0.1) if outer < 0 else (c1 - 0.1, c1 + 0.05)
            b.prism(f"{name}_win{i}", wa, wb, oc0, oc1, EAVES - 6, EAVES - 2.5, WINDOW)
        oc0, oc1 = (c0 - 0.15, c0 + 0.1) if outer < 0 else (c1 - 0.1, c1 + 0.15)
        b.prism(f"{name}_band", a0, a1, oc0, oc1, EAVES - 1.2, EAVES, TRIM, cc=True)

    if rear:
        side_wall("rear", 0.5, 0.5 + SHED_T, -1)
    if front:
        side_wall("front", 15.5 - SHED_T, 15.5, 1)
    if roof:
        ov = 0.8
        ra0 = a0 - (0.6 if first else 0)
        ra1 = a1 + (0.6 if last else 0)
        for name, ca, cb in (("roof_r", 0.5 - ov, 8.0), ("roof_f", 15.5 + ov, 8.0)):
            b.poly_mesh(name, [[b.point(ra0, ca, EAVES - 0.6), b.point(ra1, ca, EAVES - 0.6),
                                b.point(ra1, cb, RIDGE), b.point(ra0, cb, RIDGE)]], ROOF)
        # Gable ends above the open water gates, with a dark opening below the lintel.
        for name, a, on in (("gable_n", a0, first), ("gable_s", a1, last)):
            if not on:
                continue
            b.poly_mesh(name, [[b.point(a, 0.5, EAVES), b.point(a, 15.5, EAVES), b.point(a, 8.0, RIDGE - 0.3)]],
                        WALL, params=st.WALL)
            b.prism(f"{name}_lintel", a - 0.4, a + 0.4, 0.5, 15.5, EAVES - 3, EAVES, WALL, params=st.WALL)
            b.prism(f"{name}_trim", a - 0.5, a + 0.5, 0.3, 15.7, EAVES - 3.4, EAVES - 2.8, TRIM, cc=True)
    if part == "all" or part == "front":
        # Dark interior behind the open gates so the inside does not show the background.
        inside0, inside1 = (0.5 + SHED_T, 15.5 - SHED_T)
        if part == "all":
            b.prism("inside", a0 + 0.6, a1, inside0, inside1, EAVES - 3, EAVES - 0.5, OPENING)


def render_sprite(path_base, build, cc):
    for zoom in ZOOMS:
        for cc_pass in ((False, True) if cc else (False,)):
            bpy.ops.wm.read_factory_settings(use_empty=True)
            scene = bpy.context.scene
            st.configure_render(scene, samples=16 if cc_pass else 64)
            if cc_pass:
                scene.cycles.filter_width = 0.01
            oc.setup_camera(scene, zoom, CANVAS_W * zoom, CANVAS_H * zoom, anchor_y=ANCHOR_Y)
            build(cc_pass)
            suffix = "cc" if cc_pass else "overlay"
            d, name = os.path.split(path_base)
            scene.render.filepath = os.path.join(d, f"z{zoom}", f"{name}_{suffix}.png")
            bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "canals")
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    if only in (None, "locks"):
        for k, part, side, direction in lock_sprites():
            render_sprite(os.path.join(outdir, f"lock{k}"),
                          lambda cc_pass, p=part, s=side, d=direction: build_lock(p, s, d), cc=False)
            print(f"rendered lock {k} {part} {side} {direction}", flush=True)
    if only in (None, "depots"):
        for sprite, (axis, tile, part, anchor, cc) in DEPOTS.items():
            render_sprite(os.path.join(outdir, f"depot{sprite}"),
                          lambda cc_pass, a=axis, t=tile, p=part, an=anchor: build_depot(a, t, p, an, cc_pass), cc=cc)
            print(f"rendered ship depot {sprite}", flush=True)


if __name__ == "__main__":
    main()
