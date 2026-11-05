"""Render the eight aqueduct sprites (Action 5 AQUEDUCTS) at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_aqueducts.py -- <outdir>

The game draws aqueducts like bridges (tunnelbridge_cmd.cpp), with the
anchors render_bridges.py uses:
  0-3  heads SW, SE, NE, NW (direction towards the bridge), always on an
       inclined slope: the trough runs flat one level up, on a stone abutment
       that stands on the slope; anchored at the tile origin
  4-5  middle X, Y: trough with water, stone side walls with coping and the
       arch spandrels below it, anchored at (0, 0, deck - 3)
  6-7  pillar X, Y: one level of pier, drawn at (0, 12) resp. (12, 0) and
       repeated downwards; the game draws a second copy 9 units further back
Stone masonry like the canal quays (render_canals.py). Water in the trough is
rendered in the open-water colour; the packer adds the water animation.

Output: <outdir>/z<zoom>/aq<k>_overlay.png
Canvas 96z x 128z with the sprite origin at (47z, 72z), as for the bridges.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ottd_camera as oc  # noqa: E402
import style as st  # noqa: E402
from render_bridges import ANCHOR_Y, CANVAS_H, CANVAS_W, B  # noqa: E402

ZOOMS = (1, 2, 4)
STONE = (184, 174, 152)
STONE_DARK = (160, 150, 130)
COPING = (214, 208, 194)
WATER = (64, 142, 174)  # the open-water texture's colour (tools/make_ground_textures.py)

C0, C1 = 2.0, 14.0       # trough outer faces across the bridge
WALL_T = 1.4             # trough wall thickness
DECK = 3.0               # trough floor (water bottom) above the middle anchor
WATER_Z, TOP_Z = 4.6, 6.5  # water surface and wall top above the anchor

HEADS = ("SW", "SE", "NE", "NW")


def trough(b, z0, a0=0.0, a1=16.0):
    """Trough from a0 to a1 with its floor at z0: floor slab, two walls with coping, water."""
    water, top = z0 + WATER_Z - DECK, z0 + TOP_Z - DECK
    b.box("floor", a0, a1, C0, C1, z0 - 2.0, z0, STONE_DARK)
    for name, c0, c1 in (("wall_back", C0, C0 + WALL_T), ("wall_front", C1 - WALL_T, C1)):
        b.box(name, a0, a1, c0, c1, z0, top - 0.7, STONE)
        b.box(name + "_coping", a0, a1, c0 - 0.2, c1 + 0.2, top - 0.7, top, COPING)
    b.box("water", a0, a1, C0 + WALL_T, C1 - WALL_T, z0, water, WATER)


def spandrel(b, c0, c1, z_top, z_spring, crown):
    """Wall from a = 0 to 16 between z_top and an arch soffit: piers at a = 8, crowns at the tile edges."""
    n = 16
    for i in range(n):
        a0, a1 = 16 * i / n, 16 * (i + 1) / n
        soffit = lambda a: crown - (crown - z_spring) * math.cos(math.pi * (a - 8) / 16) ** 0.5  # noqa: E731
        faces = []
        for c in (c0, c1):
            faces.append([b.p(a0, c, soffit(a0)), b.p(a1, c, soffit(a1)), b.p(a1, c, z_top), b.p(a0, c, z_top)])
        faces.append([b.p(a0, c0, soffit(a0)), b.p(a1, c0, soffit(a1)), b.p(a1, c1, soffit(a1)),
                      b.p(a0, c1, soffit(a0))])
        b.mesh(f"spandrel{c0}_{i}", faces, STONE)


def head(b, direction):
    # The ground falls towards the bridge: high at the far end of the tile.
    towards_a = direction in ("SW", "SE")
    ground = (lambda a: 8 * (1 - a / 16)) if towards_a else (lambda a: 8 * a / 16)  # noqa: E731
    trough(b, 8.0)
    n = 8
    faces = []
    for i in range(n):
        a0, a1 = 16 * i / n, 16 * (i + 1) / n
        for c in (C0 + 0.3, C1 - 0.3):
            faces.append([b.p(a0, c, ground(a0) - 0.5), b.p(a1, c, ground(a1) - 0.5), b.p(a1, c, 6.0),
                          b.p(a0, c, 6.0)])
    # End face of the abutment towards the bridge.
    a_end = 16.0 if towards_a else 0.0
    faces.append([b.p(a_end, C0 + 0.3, -0.5), b.p(a_end, C1 - 0.3, -0.5), b.p(a_end, C1 - 0.3, 6.0),
                  b.p(a_end, C0 + 0.3, 6.0)])
    b.mesh("abutment", faces, STONE)


def middle(b):
    trough(b, DECK)
    for c0, c1 in ((C0 + 0.3, C0 + WALL_T), (C1 - WALL_T, C1 - 0.3)):
        spandrel(b, c0, c1, DECK - 1.9, -8.0, -3.0)


def pillar(b):
    """One level of pier at a = 8 under the front spandrel (the game adds the back one 9 units further back)."""
    b.box("pier", 6.6, 9.4, 12.4, 14.6, -8.0, 0.0, STONE)
    b.box("pier_band", 6.4, 9.6, 12.2, 14.8, -1.0, -0.4, STONE_DARK)


def build(k):
    if k < 4:
        direction = HEADS[k]
        head(B("X" if direction in ("NE", "SW") else "Y", (0, 0), False), direction)
    elif k < 6:
        middle(B("X" if k == 4 else "Y", (0, 0), False))
    else:
        pillar(B("X" if k == 6 else "Y", (0, 12), False))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "aqueducts")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    for k in range(8):
        for zoom in ZOOMS:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            scene = bpy.context.scene
            st.configure_render(scene, samples=48)
            oc.setup_camera(scene, zoom, CANVAS_W * zoom, CANVAS_H * zoom, anchor_y=ANCHOR_Y)
            build(k)
            scene.render.filepath = os.path.join(outdir, f"z{zoom}", f"aq{k}_overlay.png")
            bpy.ops.render.render(write_still=True)
        print(f"rendered aqueduct sprite {k}", flush=True)


if __name__ == "__main__":
    main()
