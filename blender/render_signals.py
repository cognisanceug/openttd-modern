"""Render all rail signals at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_signals.py -- <outdir>

One sprite per (variant, type, direction, state), see DrawSingleSignal():
  variant  0 light signal, 1 semaphore
  type     0 block, 1 entry, 2 exit, 3 combo, 4 path, 5 path one-way
  image    the direction the signal faces: SW, NE, SE, NW, E, W, S, N
  state    0 red, 1 green
Type markers follow the OpenGFX convention: entry yellow plate, exit white
plate, combo yellow and white, path blue plate, one-way path additionally a
red no-entry disc. The foot stands on the sprite origin; the canvas keeps
room above it (origin at canvas pixel (31z, 40z)).
Output: <outdir>/z<zoom>/sig_<variant>_<type>_<image>_<state>_overlay.png
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

ZOOMS = (1, 2, 4)
ANCHOR_Y = 40
FOOT = oc.CORNERS["N"]

# Facing directions in Blender axes (OpenTTD x = Blender -Y, y = Blender +X).
D = 1 / math.sqrt(2)
FACING = [Vector(v) for v in ((0, -1, 0), (0, 1, 0), (1, 0, 0), (-1, 0, 0),
                              (D, D, 0), (-D, -D, 0), (D, -D, 0), (-D, D, 0))]

POST = (150, 154, 160)
HEAD = (40, 44, 50)
HEAD_BACK = (96, 100, 108)
RED_ON, RED_OFF = (255, 70, 58), (70, 34, 32)
GREEN_ON, GREEN_OFF = (90, 255, 130), (30, 60, 40)
YELLOW, WHITE, BLUE = (240, 196, 40), (236, 236, 230), (70, 110, 205)
ARM_RED = (200, 40, 36)


def flat(name, rgb):
    """Unshaded emission material (lit lamps)."""
    return st.toon_material(name, rgb, params=st.FLAT)


def box(name, centre, size, frame, material):
    """Box in the signal's local frame (x = sideways, y = facing, z = up)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.transform(frame @ Matrix.Translation(centre) @ Matrix.Diagonal((*size, 1)))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = False
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def disc(name, centre, radius, frame, material):
    """Lamp: a flat disc facing local +y."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=radius)
    bm.transform(frame @ Matrix.Translation(centre) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)


def markers(signal_type, frame, z):
    """Type plates on the post below the head (facing the same way)."""
    plates = {1: [YELLOW], 2: [WHITE], 3: [YELLOW, WHITE], 4: [BLUE], 5: [BLUE]}.get(signal_type, [])
    for i, rgb in enumerate(plates):
        box(f"plate{i}", (0, 0.012, z - i * 0.045), (0.05, 0.008, 0.038), frame, st.toon_material(f"p{i}", rgb))
    if signal_type == 5:
        disc("noentry", (0, 0.018, z - 0.095), 0.024, frame, st.toon_material("ne", ARM_RED))
        box("noentry_bar", (0, 0.022, z - 0.095), (0.032, 0.004, 0.008), frame, st.toon_material("nw", WHITE))


def build(variant, signal_type, image, state):
    face = FACING[image]
    side = Vector((face.y, -face.x, 0))
    frame = Matrix.Translation(FOOT) @ Matrix(((side.x, face.x, 0, 0), (side.y, face.y, 0, 0),
                                                (0, 0, 1, 0), (0, 0, 0, 1)))
    post = st.toon_material("post", POST)
    box("foot", (0, 0, 0.01), (0.05, 0.05, 0.02), frame, post)
    if variant == 0:
        box("post", (0, 0, 0.17), (0.018, 0.018, 0.34), frame, post)
        box("head", (0, 0, 0.36), (0.05, 0.034, 0.12), frame, st.toon_material("head", HEAD))
        box("head_back", (0, -0.018, 0.36), (0.046, 0.002, 0.112), frame, st.toon_material("back", HEAD_BACK))
        disc("red", (0, 0.018, 0.39), 0.016, frame, flat("r", RED_ON if state == 0 else RED_OFF))
        disc("green", (0, 0.018, 0.335), 0.016, frame, flat("g", GREEN_ON if state == 1 else GREEN_OFF))
        markers(signal_type, frame, 0.26)
    else:
        box("post", (0, 0, 0.22), (0.016, 0.016, 0.44), frame, post)
        box("cap", (0, 0, 0.445), (0.026, 0.026, 0.01), frame, post)
        angle = 0.0 if state == 0 else math.radians(45)
        arm = frame @ Matrix.Translation((0, 0.014, 0.4)) @ Matrix.Rotation(angle, 4, "Y")
        box("arm", (-0.07, 0, 0), (0.12, 0.008, 0.026), arm, st.toon_material("arm", ARM_RED))
        box("stripe", (-0.1, 0.005, 0), (0.016, 0.002, 0.026), arm, st.toon_material("stripe", WHITE))
        disc("lamp", (0, 0.02, 0.37), 0.011, frame, flat("l", RED_ON if state == 0 else GREEN_ON))
        markers(signal_type, frame, 0.3)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "signals")
    for zoom in ZOOMS:
        os.makedirs(os.path.join(outdir, f"z{zoom}"), exist_ok=True)
    for variant in (0, 1):
        for signal_type in range(6):
            for image in range(8):
                for state in (0, 1):
                    name = f"sig_{variant}_{signal_type}_{image}_{state}"
                    for zoom in ZOOMS:
                        bpy.ops.wm.read_factory_settings(use_empty=True)
                        scene = bpy.context.scene
                        st.configure_render(scene, samples=32)
                        oc.setup_camera(scene, zoom, 64 * zoom, 64 * zoom, anchor_y=ANCHOR_Y)
                        build(variant, signal_type, image, state)
                        scene.render.filepath = os.path.join(outdir, f"z{zoom}", f"{name}_overlay.png")
                        bpy.ops.render.render(write_still=True)
            print(f"rendered variant {variant} type {signal_type}", flush=True)


if __name__ == "__main__":
    main()
