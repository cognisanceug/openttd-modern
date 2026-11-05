"""Iron ore mine: one 4x4 open pit drawn entirely in ground sprites.

gfx 100 + 4x + y sits at layout tile (x, y). Ground sprites per stage:
stage 0 2293 + i (topsoil stripped, fence), stages 1-2 2309 + i (two benches),
stage 3 2325 + i (four benches, haul ramp, water on the floor, crusher plant on
the north tile, excavator and dump truck in the pit).

The whole pit is one height field in unit coordinates (x, y 0-64). Each tile's
sprite is the render of the whole pit seen through that tile's diamond at
height 0: a pixel of the pit belongs to the tile whose diamond it lies in, so
the 16 sprites join without seams, and walls further down show through the
tiles in front of them. Parts standing above the ground (fence, plant,
machines) are cut to the tile and rendered with the pit held out.
"""

import math
import os

import bmesh
import bpy

import build_kit as bk
import render_ground as rg
import style as st

SPRITES = list(range(2293, 2341))
DEPTH = {0: 1, 1: 2, 3: 4}  # benches per stage
BENCH = 4.0  # z units per bench
MARGIN = 3.5


def stage_of(sprite):
    return 0 if sprite < 2309 else 1 if sprite < 2325 else 3


def tile_of(sprite):
    i = (sprite - 2293) % 16
    return i // 4, i % 4


def rim(x, y):
    """Distance inside the pit outline (negative outside); the north tile keeps the plant."""
    p = 5.0
    ax, ay = abs(x - 34) / 30, abs(y - 34) / 30
    d = (1 - (ax ** p + ay ** p) ** (1 / p)) * 30 - MARGIN + 2.5
    plant = min(18 - x, 18 - y)  # the north corner stays at ground level
    return min(d, -plant + 0.0) if plant > 0 else d


def height(x, y, benches):
    d = rim(x, y)
    if d <= 0:
        return 0.0
    if benches == 1:
        return -0.6 * min(1.0, d / 1.5)
    z = 0.0
    step = 4.2  # x/y distance per bench (face + berm)
    for b in range(benches):
        t = d - b * step
        if t <= 0:
            break
        z -= BENCH * min(1.0, t / 1.4)
    # Haul ramp along the south-east side, from the rim near the east corner down to the floor.
    if benches > 2 and 46 <= y <= 51.5:
        ramp = -BENCH * benches * min(1.0, max(0.0, (x - 12) / 38))
        z = max(z, ramp)
    return z


def terrain(benches):
    """Height-field mesh with per-face material index: 0 grass, 1 ore, 2 berm/ramp gravel."""
    n = 128
    step = 64 / n
    bm = bmesh.new()
    verts = {}
    for i in range(n + 1):
        for j in range(n + 1):
            x, y = i * step, j * step
            verts[i, j] = bm.verts.new(bk.to_blender(x, y, height(x, y, benches), (0, 0)))
    for i in range(n):
        for j in range(n):
            q = [verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]]
            f = bm.faces.new(q)
            cx, cy = (i + 0.5) * step, (j + 0.5) * step
            zs = [height(cx, cy, benches)]
            d = rim(cx, cy)
            if d <= -0.3:
                f.material_index = 0
            elif benches > 2 and 46 <= cy <= 51.5 and abs(zs[0] - (-BENCH * benches * min(1.0, max(0.0, (cx - 12) / 38)))) < 0.3:
                f.material_index = 2
            else:
                f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def props(stage):
    k = bk.Kit()
    # Fence along the outline (on grass).
    pts = []
    for a in range(0, 361, 12):
        t = math.radians(a)
        c, s = math.cos(t), math.sin(t)
        # Walk outwards until outside the pit.
        r = 10.0
        while rim(34 + r * c, 34 + r * s) > -1.2 and r < 40:
            r += 0.25
        x, y = 34 + r * c, 34 + r * s
        if 0.8 < x < 63.2 and 0.8 < y < 63.2 and not (x < 19 and y < 19):
            pts.append((x, y))
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if math.hypot(xb - xa, yb - ya) < 10:
            k.fence([(xa, ya), (xb, yb)], h=2.4, mat="steel", post=3.0)
    if stage == 0:
        k.heap(8, 9, 4.5, 4.0, 5, "soil", seed=21)
        k.heap(40, 20, 3.0, 4.0, 3, "soil", seed=22)
        tractor_like(k, 32, 30)
        return k
    # Crusher plant on the north tile, conveyor into the pit, ore heap.
    k.box(3, 11, 3, 10, 0, 14, "concrete")
    k.box(3, 11, 3, 10, 14, 20, "roof_metal")
    k.box(2.8, 11.2, 2.8, 10.2, 13, 14, "cc")
    k.gable(3, 11, 3, 10, 20, 23, "y", "steel_dark", "roof_metal", over=0.3, thick=0.3)
    k.roller_door("x", 11, 10, 6.5, w=3.5, h=6)
    k.heap(12.5, 14.5, 3.5, 3.0, 7, "ore", seed=23)
    bk_conv(k, (10, 9.5, 18), (16, 16, 8))
    k.cbox(14, 4, 2.4, 2.4, 0, 9, "steel")
    k.cbox(14, 4, 2.8, 2.8, 9, 10, "cc")
    if stage == 3:
        excavator(k, 30, 26, -8)
        dumper(k, 44, 49, -9)
        k.box(4, 9, 13, 16, 0, 5, "white")
        k.box(3.8, 9.2, 12.8, 16.2, 4.2, 5.0, "cc")
    else:
        excavator(k, 36, 30, -4)
    return k


def bk_conv(k, p0, p1):
    k.rod(p0, p1, 0.6, "steel_dark", n=4)
    k.rod((p0[0], p0[1], p0[2] + 0.6), (p1[0], p1[1], p1[2] + 0.6), 0.4, "ore", n=4)
    mx, my, mz = [(a + b) / 2 for a, b in zip(p0, p1)]
    k.rod((mx, my, 0), (mx, my, mz), 0.2, "steel", n=4)


def excavator(k, x, y, z):
    k.box(x - 2.0, x + 2.0, y - 1.6, y + 1.6, z, z + 1.4, "dark")
    k.box(x - 1.6, x + 1.4, y - 1.3, y + 1.3, z + 1.4, z + 4.4, "yellow")
    k.box(x + 0.2, x + 1.4, y - 1.3, y - 0.1, z + 4.4, z + 6.4, "glass")
    k.rod((x + 1.4, y + 0.5, z + 4), (x + 4.5, y + 0.5, z + 9), 0.35, "yellow", n=4)
    k.rod((x + 4.5, y + 0.5, z + 9), (x + 6.0, y + 0.5, z + 2.5), 0.3, "yellow", n=4)
    k.cbox(x + 6.0, y + 0.5, 1.2, 1.4, z + 1.5, z + 3.0, "steel_dark")


def dumper(k, x, y, z):
    k.box(x - 2.6, x + 2.6, y - 1.5, y + 1.5, z + 1.6, z + 4.6, "yellow")
    k.box(x + 1.6, x + 2.6, y - 1.5, y + 0.2, z + 4.6, z + 6.6, "glass")
    k.heap(x - 0.6, y, 1.6, 1.0, 1.6, "ore", seed=5)
    for dx in (-1.8, 1.8):
        for dy in (-1.4, 1.4):
            k.rod((x + dx, y + dy - 0.3, z + 1.1 * 2.45), (x + dx, y + dy + 0.3, z + 1.1 * 2.45), 1.1, "dark", n=8)


def tractor_like(k, x, y):
    k.box(x - 1.8, x + 1.8, y - 1.2, y + 1.2, 0.2, 2.6, "yellow")
    k.box(x - 1.0, x + 0.6, y - 1.0, y + 1.0, 2.6, 4.6, "glass")
    k.box(x + 1.8, x + 2.4, y - 1.8, y + 1.8, 0.2, 2.0, "steel_dark")


def link_bm(bm, mats, shift, holdout=False):
    mesh = bpy.data.meshes.new("pit")
    bm2 = bm.copy()
    # The mesh was built for shift (0, 0); move it so the sprite's tile sits at the camera anchor.
    off = bk.to_blender(0, 0, 0, shift) - bk.to_blender(0, 0, 0, (0, 0))
    for v in bm2.verts:
        v.co += off
    bm2.to_mesh(mesh)
    bm2.free()
    for p in mesh.polygons:
        p.use_smooth = False
    if holdout:
        mesh.materials.append(rg.holdout_material())
        for p in mesh.polygons:
            p.material_index = 0
    else:
        for m in mats:
            mesh.materials.append(m)
    obj = bpy.data.objects.new("pit", mesh)
    bpy.context.scene.collection.objects.link(obj)


def render(outdir, sprite):
    stage = stage_of(sprite)
    tx, ty = tile_of(sprite)
    shift = (tx * 16, ty * 16)
    bm = terrain(DEPTH[stage])
    p = props(stage)
    tile_props = bk.clip_parts(p.parts, tx * 16, tx * 16 + 16, ty * 16, ty * 16 + 16)
    name = f"g{sprite}"
    for zoom in bk.ZOOMS:
        zdir = os.path.join(outdir, f"z{zoom}")
        os.makedirs(zdir, exist_ok=True)
        scene = bk.new_scene(zoom, bk.GROUND_SIZE, bk.GROUND_SIZE, bk.GROUND_ANCHOR)
        mats = [bk.ground_material("grass"), bk.ground_material("industry/ore" if stage else "industry/yard"),
                bk.ground_material("industry/yard")]
        link_bm(bm, mats, shift)
        if stage == 3:
            water = bk.Kit()
            water.cyl(30, 40, 4.5, -BENCH * 4 - 0.6, -BENCH * 4 + 0.15, "water", n=12)
            bk.link_parts(water.parts, shift, bk.Materials("color"))
        bk.render(scene, os.path.join(zdir, f"{name}_color.png"))
        scene = bk.new_scene(zoom, bk.GROUND_SIZE, bk.GROUND_SIZE, bk.GROUND_ANCHOR, samples=16)
        scene.cycles.filter_width = 0.01
        rg.build_tile(0, 1.0).data.materials.append(rg.mask_material())
        bk.render(scene, os.path.join(zdir, f"{name}_mask.png"))
        if tile_props:
            scene = bk.new_scene(zoom, bk.GROUND_SIZE, bk.GROUND_SIZE, bk.GROUND_ANCHOR)
            link_bm(bm, None, shift, holdout=True)
            bk.link_parts(tile_props, shift, bk.Materials("color", fixed=True))
            bk.render(scene, os.path.join(zdir, f"{name}_gprops.png"))
    bm.free()
    print(f"rendered iron mine ground {sprite}", flush=True)
