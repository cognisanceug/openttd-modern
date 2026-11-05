"""Render the foundation sprites (retaining walls under raised tiles) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_foundations.py -- <outdir>

A foundation sprite shows only the walls between the terrain and the
foundation's top; the top itself stays transparent because the game draws the
track, road or building ground on it afterwards. Front walls (SW and SE edges)
are full stone walls; on the back edges (NW, NE) only a thin coping strip is
drawn, and only when the sprite block asks for it (see GetFoundationSpriteBlock).

Sprites (file names in <outdir>/z<zoom>/<name>_overlay.png):
  found_base<tileh>   990-1003: leveled foundation, block 0 (both back edges), tileh 1-14
  found<k>            Action 5 FOUNDATIONS block, k = 0-89:
                        22b + i       inclined, block b 0-3, i = corner * 2 + (axis Y)
                        22b - 15 + t  leveled, block b 1-3, tileh t 1-14
                        74 + 4b + c   halftile, block b 0-3, corner c (W, S, E, N)
Blocks: 0 back walls NW and NE, 1 NE only, 2 NW only, 3 none.
Heights follow ApplyFoundationToSlope(): leveled tops are flat one level above
the tile, inclined tops become SLOPE_SW/NE (X) or SLOPE_SE/NW (Y), halftile
tops level the triangle at the corner; terrain under inclined and halftile
foundations is the slope with that one corner raised.
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
TEXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render", "textures")
CORNER_ORDER = ("W", "S", "E", "N")  # OpenTTD Corner enum order
COPING_RGB = (214, 206, 186)
COPING_WIDTH = 0.035
COPING_HEIGHT = 0.012


def levels(slope):
    return {c: (1 if slope & bit else 0) for c, bit in (("W", 1), ("S", 2), ("E", 4), ("N", 8))}


SLOPE_SW, SLOPE_NE, SLOPE_SE, SLOPE_NW = 0x03, 0x0C, 0x06, 0x09


def specs():
    """(name, terrain corner levels, top corner levels, region corners, back edges with coping)."""
    out = []
    all_corners = ("N", "E", "S", "W")

    def back(block):
        return {"NW": block in (0, 2), "NE": block in (0, 1)}

    for t in range(1, 15):
        out.append((f"found_base{t}", levels(t), {c: 1 for c in all_corners}, all_corners, back(0)))
    for k in range(90):
        if k >= 74:
            b, ci = divmod(k - 74, 4)
            c = CORNER_ORDER[ci]
            terrain = levels(1 << ci)
            top = {x: 1 for x in all_corners}
            nb = {"W": ("S", "N"), "S": ("W", "E"), "E": ("S", "N"), "N": ("W", "E")}[c]
            out.append((f"found{k}", terrain, top, (c,) + nb, back(b)))
            continue
        b, i = divmod(k, 22)
        if i < 8:
            ci, axis_y = divmod(i, 2)
            c = CORNER_ORDER[ci]
            if axis_y:
                top = SLOPE_SE if c in ("S", "E") else SLOPE_NW
            else:
                top = SLOPE_SW if c in ("W", "S") else SLOPE_NE
            out.append((f"found{k}", levels(1 << ci), levels(top), all_corners, back(b)))
        else:
            # Leveled sprites of the next block: k = 22(b+1) - 15 + t.
            t = i - 7
            out.append((f"found{k}", levels(t), {c: 1 for c in all_corners}, all_corners, back(b + 1)))
    return out


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    st.configure_render(scene)
    return scene


def pos(corner, level):
    v = oc.CORNERS[corner].copy()
    v.z = level * oc.LEVEL
    return v


def edge_kind(a, b, region):
    """'front', 'back' or 'side' for the edge a-b of a region, by its outward normal."""
    pa, pb = oc.CORNERS[a], oc.CORNERS[b]
    centre = sum((oc.CORNERS[c] for c in region), Vector()) / len(region)
    d = pb - pa
    n = Vector((d.y, -d.x, 0))
    if n.dot((pa + pb) / 2 - centre) < 0:
        n = -n
    facing = n.x - n.y  # towards the camera, which looks along (-1, 1)
    if facing > 1e-6:
        return "front", n
    if facing < -1e-6:
        return "back", n
    return "side", n


def add_wall(name, a, b, terrain, top, outward, material):
    ga, gb, ta, tb = terrain[a], terrain[b], top[a], top[b]
    if ta <= ga and tb <= gb:
        return
    verts = [pos(a, ga), pos(b, gb)]
    verts += [pos(b, tb)] if tb > gb else []
    verts += [pos(a, ta)] if ta > ga else []
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in verts]
    face = bm.faces.new(vs)
    bm.normal_update()
    if face.normal.dot(outward) < 0:
        face.normal_flip()
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)


def add_coping(name, a, b, top, inward, material):
    """Thin strip along a back edge at the foundation's top, inside the tile."""
    pa, pb = pos(a, top[a]), pos(b, top[b])
    off = inward.normalized() * COPING_WIDTH
    up = Vector((0, 0, COPING_HEIGHT))
    bm = bmesh.new()
    quad = [pa, pb, pb + off, pa + off]
    bottom = [bm.verts.new(v) for v in quad]
    topv = [bm.verts.new(v + up) for v in quad]
    bm.faces.new(topv)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((bottom[i], bottom[j], topv[j], topv[i]))
    bm.normal_update()
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)


def build(terrain, top, region, back_edges):
    wall = st.wall_material(os.path.join(TEXTURES, "stone.png"))
    coping = st.toon_material("coping", COPING_RGB)
    ring = list(region)
    if len(ring) == 4:
        ring = ["N", "E", "S", "W"]
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        kind, n = edge_kind(a, b, ring)
        tile_edge = {frozenset("NW"): "NW", frozenset("NE"): "NE"}.get(frozenset((a, b)))
        if kind in ("front", "side"):
            add_wall(f"wall_{a}{b}", a, b, terrain, top, n, wall)
        elif tile_edge is None or back_edges[tile_edge]:
            # Back edge: coping strip (tile back edges only when the block shows them).
            add_coping(f"coping_{a}{b}", a, b, top, -n, coping)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "foundations")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    for name, terrain, top, region, back_edges in specs():
        for zoom in ZOOMS:
            scene = reset_scene()
            size = 64 * zoom
            oc.setup_camera(scene, zoom, size, size)
            build(terrain, top, region, back_edges)
            scene.render.filepath = os.path.join(outdir, f"z{zoom}", f"{name}_overlay.png")
            bpy.ops.render.render(write_still=True)
        print(f"rendered {name}", flush=True)


if __name__ == "__main__":
    main()
