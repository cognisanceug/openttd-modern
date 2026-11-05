"""OpenTTD-calibrated orthographic camera and scene helpers for Blender.

World conventions (Blender units):
  * One tile is 1 x 1, centred on the origin.
  * Tile corners: N = (-0.5, 0.5), E = (0.5, 0.5), S = (0.5, -0.5), W = (-0.5, -0.5).
    OpenTTD's x axis (N -> W) is Blender -Y, OpenTTD's y axis (N -> E) is Blender +X.
  * One OpenTTD height level (TILE_HEIGHT = 8 px at 1x) is LEVEL = 1 / (2 * sqrt(6)) units.

Projection: true orthographic camera, 30 degrees elevation, 45 degrees azimuth.
That squashes the tile diagonal by exactly 2:1 and maps one height level to
8 px * zoom. At zoom z (1, 2, 4) the tile diamond is 64z x 32z px; sampled at
pixel centres it covers 32z - 1 rows (31 / 63 / 127), matching OpenTTD.

Canvas: every tile sprite is rendered on a square canvas of 64z x 64z px
(larger canvases for tall objects use the same anchor). The north corner of
the tile at height 0 lands on pixel position (32z, ANCHOR_Y * z - 0.5),
where pixel rows are counted from the top. Sprite offsets are the 1x OpenTTD
offsets multiplied by the zoom factor (flat tile: -31z, 0).
"""

import math

import bpy
from mathutils import Euler, Vector

LEVEL = 1.0 / (2.0 * math.sqrt(6.0))
ELEVATION = math.radians(30.0)
AZIMUTH = math.radians(45.0)
ANCHOR_Y = 24  # 1x canvas row of the flat tile's north corner (+0.5 px above it)

CORNERS = {
    "N": Vector((-0.5, 0.5, 0.0)),
    "E": Vector((0.5, 0.5, 0.0)),
    "S": Vector((0.5, -0.5, 0.0)),
    "W": Vector((-0.5, -0.5, 0.0)),
}

CAM_ROT = Euler((math.pi / 2 - ELEVATION, 0.0, AZIMUTH), "XYZ")
CAM_FORWARD = CAM_ROT.to_matrix() @ Vector((0.0, 0.0, -1.0))
CAM_UP = CAM_ROT.to_matrix() @ Vector((0.0, 1.0, 0.0))
CAM_RIGHT = CAM_ROT.to_matrix() @ Vector((1.0, 0.0, 0.0))


def pixel_size(zoom):
    """World units per pixel along the screen axes at the given zoom (1, 2, 4)."""
    return math.sqrt(2.0) / (64.0 * zoom)


def project(point, zoom, width, height, anchor_y=ANCHOR_Y):
    """Analytic projection of a world point to continuous canvas pixel coords (x right, y down)."""
    p = pixel_size(zoom)
    rel = Vector(point) - CORNERS["N"]
    u = width / 2.0 + rel.dot(CAM_RIGHT) / p
    v = (anchor_y * zoom - 0.5) - rel.dot(CAM_UP) / p
    return u, v


def setup_camera(scene, zoom, width, height, anchor_y=ANCHOR_Y):
    """Create/position the orthographic camera so the canvas follows the OpenTTD grid."""
    cam_data = bpy.data.cameras.get("OTTD_Camera") or bpy.data.cameras.new("OTTD_Camera")
    cam_data.type = "ORTHO"
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.ortho_scale = width * pixel_size(zoom)
    cam_data.clip_start = 0.01
    cam_data.clip_end = 100.0
    cam_data.shift_x = 0.0
    cam_data.shift_y = 0.0

    cam = bpy.data.objects.get("OTTD_Camera") or bpy.data.objects.new("OTTD_Camera", cam_data)
    if cam.name not in scene.collection.objects:
        scene.collection.objects.link(cam)
    cam.rotation_mode = "XYZ"
    cam.rotation_euler = CAM_ROT

    # The north corner sits (height/2 - anchor) px above the image centre.
    p = pixel_size(zoom)
    above_centre = height / 2.0 - (anchor_y * zoom - 0.5)
    centre = CORNERS["N"] - CAM_UP * (above_centre * p)
    cam.location = centre - CAM_FORWARD * 20.0
    scene.camera = cam

    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0
    return cam


def slope_corner_levels(slope):
    """Corner heights (in levels) for an OpenTTD Slope value (bits W=1, S=2, E=4, N=8, STEEP=16)."""
    w, s, e, n = (1 if slope & bit else 0 for bit in (1, 2, 4, 8))
    h = {"W": w, "S": s, "E": e, "N": n}
    if slope & 16:
        # Steep: the corner opposite the low one is at 2 levels.
        low = [c for c, v in h.items() if v == 0][0]
        top = {"N": "S", "S": "N", "E": "W", "W": "E"}[low]
        h[top] = 2
    return h


def slope_fold(h):
    """Diagonal the two surface triangles share: the one whose endpoints are level ('NS' or 'WE')."""
    return "WE" if h["W"] == h["E"] else "NS"


# Slope value for each of the 19 ground sprites (base sprite + offset), see _slope_to_sprite_offset.
SPRITE_SLOPES = list(range(15)) + [0x1D, 0x17, 0x1B, 0x1E]
