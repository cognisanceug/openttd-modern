"""Render the rail, monorail, maglev and road tunnel portals (2365-2396) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_tunnels.py -- <outdir> [--only rail,mono,mglv,road]

Per direction (NE, SE, SW, NW = the way the tunnel leads into the hill) the game
draws a ground sprite (base + 2 * dir) and a front sprite (base + 2 * dir + 1)
anchored at (15, 15) in tile units, drawn over vehicles. The tunnel tile is the
slope rising towards the hill (SLOPE_NE, SE, SW, NW).

Design: stone portal with a round arch and a dark mouth, a grassy low-poly
mound over the tunnel. When the hill lies behind the portal (NE, NW) the front
sprite holds only the arch frame; when it lies in front (SE, SW) it holds the
whole portal and mound.

Outputs per sprite (canvas 96z x 96z, origin at (47z, 56z)):
  tun<sprite>_ground_color/_ground_mask  ground tile with track/road (ground sprites)
  tun<sprite>_overlay                     3D parts (both sprites)
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
import render_ground as rg  # noqa: E402

ZOOMS = (1, 2, 4)
CANVAS, ANCHOR_Y = 96, 56
STONE = (176, 168, 150)
MOUTH = (28, 30, 34)
MOUND = (113, 183, 88) if st.GRASS == "toy" else (122, 176, 84)  # toy: scaled like toy_grass to grass

DIRS = ("NE", "SE", "SW", "NW")
SLOPE = {"NE": 12, "SE": 6, "SW": 3, "NW": 9}
# Unit vectors in OpenTTD tile units: u into the hill, v across.
INTO = {"NE": (-1, 0), "SE": (0, 1), "SW": (1, 0), "NW": (0, -1)}
SPRITES = {"rail": 2365, "mono": 2373, "mglv": 2381, "road": 2389}
GROUND_TEX = {("rail", "X"): "infra/rail1012", ("rail", "Y"): "infra/rail1011",
              ("mono", "X"): "infra/mono1094", ("mono", "Y"): "infra/mono1093",
              ("mglv", "X"): "infra/mglv1176", ("mglv", "Y"): "infra/mglv1175",
              ("road", "X"): "infra/road1333", ("road", "Y"): "infra/road1332"}


def ottd(x, y, z=0.0):
    """OpenTTD tile units (x, y, z in levels) -> Blender."""
    return oc.CORNERS["N"] + Vector((y / 16, -x / 16, z * oc.LEVEL))


class Tunnel:
    def __init__(self, direction, anchor=(0, 0)):
        self.d = direction
        self.anchor = anchor
        ux, uy = INTO[direction]
        self.u = Vector((ux, uy))
        self.v = Vector((-uy, ux))
        self.mats = {}

    def p(self, u, v, z):
        """u along the tunnel from the tile centre (+ into the hill), v across, z in levels."""
        c = Vector((8, 8)) + self.u * u + self.v * v
        return ottd(c.x - self.anchor[0], c.y - self.anchor[1], z)

    def ground_z(self, u):
        """Tile surface height (levels) along u: 0 at the outer edge, 1 at the hill edge."""
        return (u + 8) / 16

    def mat(self, rgb, params=st.OBJECT):
        if rgb not in self.mats:
            self.mats[rgb] = st.toon_material(str(rgb), rgb, params=params)
        return self.mats[rgb]

    def solid(self, name, profile, u0, u1, rgb, params=st.OBJECT):
        """Extrude a (v, z) polygon from u0 to u1."""
        bm = bmesh.new()
        a = [bm.verts.new(self.p(u0, v, z)) for v, z in profile]
        b = [bm.verts.new(self.p(u1, v, z)) for v, z in profile]
        bm.faces.new(a)
        bm.faces.new(list(reversed(b)))
        n = len(profile)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for poly in mesh.polygons:
            poly.use_smooth = False
        mesh.materials.append(self.mat(rgb, params))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)


PORTAL_U = 0.0     # portal plane: tile centre
ARCH_HALF = 4.2    # half width of the opening (tile units)
ARCH_SPRING = 0.55  # opening wall height above the track (levels)
ARCH_RISE = 0.35
FRAME = 1.4
TOP = 1.75         # portal top above the track at the portal (levels)


def arch_profile(half, spring, rise, base, steps=8):
    pts = [(-half, base), (half, base), (half, base + spring)]
    for i in range(1, steps):
        a = math.pi * i / steps
        pts.append((half * math.cos(a), base + spring + rise * math.sin(a)))
    pts.append((-half, base + spring))
    return pts


def build_portal(t, frame_only):
    base = t.ground_z(PORTAL_U)
    hw = 7.5
    # Portal wall: outer rectangle minus arch, built from pieces around the arch.
    outer_top = base + TOP
    arch = arch_profile(ARCH_HALF, ARCH_SPRING, ARCH_RISE, base)
    # Left and right pillars of the frame.
    for side, sgn in (("l", -1), ("r", 1)):
        prof = [(sgn * ARCH_HALF, base), (sgn * (ARCH_HALF + FRAME), base),
                (sgn * (ARCH_HALF + FRAME), outer_top), (sgn * ARCH_HALF, outer_top)]
        t.solid(f"pillar_{side}", prof if sgn > 0 else list(reversed(prof)), PORTAL_U - 0.6, PORTAL_U + 0.8, STONE,
                params=st.WALL)
    # Spandrel above the arch (polygon between arch curve and top).
    spandrel = [(ARCH_HALF, outer_top)] + [(-ARCH_HALF, outer_top)] + [(-ARCH_HALF, base + ARCH_SPRING)] + \
        [pt for pt in reversed(arch[3:-1])] + [(ARCH_HALF, base + ARCH_SPRING)]
    t.solid("spandrel", spandrel, PORTAL_U - 0.6, PORTAL_U + 0.8, STONE, params=st.WALL)
    # Coping on top of the portal.
    t.solid("coping", [(-ARCH_HALF - FRAME - 0.3, outer_top), (ARCH_HALF + FRAME + 0.3, outer_top),
                       (ARCH_HALF + FRAME + 0.3, outer_top + 0.12), (-ARCH_HALF - FRAME - 0.3, outer_top + 0.12)],
            PORTAL_U - 0.8, PORTAL_U + 1.0, (196, 188, 170), params=st.WALL)
    if frame_only:
        return
    # Wing walls down the slope on both sides, and the dark mouth.
    t.solid("mouth", arch, PORTAL_U + 0.7, PORTAL_U + 4, MOUTH, params=st.FLAT)
    for side, sgn in (("l", -1), ("r", 1)):
        prof = [(sgn * (ARCH_HALF + FRAME), base), (sgn * hw, base), (sgn * hw, base + 0.9),
                (sgn * (ARCH_HALF + FRAME), outer_top)]
        t.solid(f"wing_{side}", prof if sgn > 0 else list(reversed(prof)), PORTAL_U - 0.2, PORTAL_U + 0.6, STONE,
                params=st.WALL)


def build_mound(t):
    """Grassy hill over the tunnel: highest above the portal, running out into the slope at the hill edge."""
    rows = []
    for k in range(6):
        u = PORTAL_U + 0.6 + (8.0 - PORTAL_U - 0.6) * k / 5
        g = t.ground_z(u)
        f = 1 - ((u - PORTAL_U) / (8.0 - PORTAL_U)) ** 2
        h = g + (TOP + 0.12) * max(f, 0.0)
        rows.append([(u, -8.0, g), (u, -6.5, g + 0.55 * (h - g)), (u, -3.5, h - 0.04 * (h - g)), (u, 0, h),
                     (u, 3.5, h - 0.04 * (h - g)), (u, 6.5, g + 0.55 * (h - g)), (u, 8.0, g)])
    bm = bmesh.new()
    vs = [[bm.verts.new(t.p(u, v, z)) for u, v, z in row] for row in rows]
    for i in range(len(vs) - 1):
        for j in range(len(vs[i]) - 1):
            bm.faces.new((vs[i][j], vs[i][j + 1], vs[i + 1][j + 1], vs[i + 1][j]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    mesh = bpy.data.meshes.new("mound")
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False
    mesh.materials.append(t.mat(MOUND, st.GROUND))
    obj = bpy.data.objects.new("mound", mesh)
    bpy.context.scene.collection.objects.link(obj)


def render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def new_scene(zoom):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    st.configure_render(scene)
    oc.setup_camera(scene, zoom, CANVAS * zoom, CANVAS * zoom, anchor_y=ANCHOR_Y)
    return scene


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "tunnels")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else list(SPRITES)
    for kind, base in SPRITES.items():
        if kind not in only:
            continue
        for di, d in enumerate(DIRS):
            ground_id, front_id = base + 2 * di, base + 2 * di + 1
            axis = "X" if d in ("NE", "SW") else "Y"
            hill_behind = d in ("NE", "NW")
            for zoom in ZOOMS:
                zdir = os.path.join(outdir, f"z{zoom}")
                # Ground tile with track or road (colour with overscan, exact mask).
                scene = new_scene(zoom)
                obj = rg.build_tile(SLOPE[d], rg.COLOR_OVERSCAN)
                obj.data.materials.append(st.toon_material(
                    "g", image_path=st.texture(GROUND_TEX[kind, axis]), params=st.GROUND,
                    extension="EXTEND"))
                render(scene, os.path.join(zdir, f"tun{ground_id}_ground_color.png"))
                scene = new_scene(zoom)
                obj = rg.build_tile(SLOPE[d], 1.0)
                obj.data.materials.append(rg.mask_material())
                scene.cycles.samples = 16
                scene.cycles.filter_width = 0.01
                render(scene, os.path.join(zdir, f"tun{ground_id}_ground_mask.png"))
                # 3D parts of the ground sprite: behind-the-portal parts when the hill is behind.
                scene = new_scene(zoom)
                rg.build_tile(SLOPE[d], 1.0).data.materials.append(rg.holdout_material())
                if hill_behind:
                    t = Tunnel(d)
                    build_mound(t)
                    build_portal(t, frame_only=False)
                else:
                    t = Tunnel(d)
                    t.solid("mouth", arch_profile(ARCH_HALF, ARCH_SPRING, ARCH_RISE, t.ground_z(PORTAL_U)),
                            PORTAL_U + 0.7, PORTAL_U + 4, MOUTH, params=st.FLAT)
                render(scene, os.path.join(zdir, f"tun{ground_id}_overlay.png"))
                # Front sprite, anchored at (15, 15).
                scene = new_scene(zoom)
                t = Tunnel(d, anchor=(15, 15))
                if hill_behind:
                    build_portal(t, frame_only=True)
                else:
                    build_mound(t)
                    build_portal(t, frame_only=False)
                render(scene, os.path.join(zdir, f"tun{front_id}_overlay.png"))
            print(f"rendered tunnel {kind} {d}", flush=True)



if __name__ == "__main__":
    main()
