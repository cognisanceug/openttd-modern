"""Shared look of the modern set, after the map study artifact.

Lighting is not physically simulated. Like the map study, every surface gets
its base colour multiplied by a brightness derived from its normal:
    lum = clamp(1 + gain * (dot(N, L) / L.z - 1), lo, hi)
so a flat surface shows exactly its base colour and slopes or facets facing
the light get brighter, those facing away darker, without hard shadows.
The multiplication happens in sRGB space as in the study (lum ** 2.2 in linear).
"""

import math

import bpy
from mathutils import Vector

# Map study LIGHT = (-0.2, 0.45, 0.87) in its map coordinates; its map x is
# Blender +X and its map y is Blender -Y.
LIGHT = Vector((-0.2, -0.45, 0.87)).normalized()

GROUND = dict(gain=1.5, lo=0.62, hi=1.22)   # terrain: a bit more contrast than the study for readability
OBJECT = dict(gain=1.0, lo=0.60, hi=1.30)   # trees and other objects
FLAT = dict(gain=0.0, lo=1.0, hi=1.0)       # unshaded: open water

SHADOW_RGB = (24, 40, 34)
SHADOW_ALPHA = 0.22


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(rgb):
    return tuple(srgb_to_linear(v) for v in rgb) + (1.0,)


def _lum_strength(nt, gain, lo, hi):
    """Node chain computing lum ** 2.2 from the shading normal; returns the output socket."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = tuple(LIGHT)
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])

    def math_node(op, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        nt.links.new(a, n.inputs[0])
        if b is not None:
            n.inputs[1].default_value = b
        return n.outputs[0]

    v = math_node("DIVIDE", dot.outputs["Value"], LIGHT.z)
    v = math_node("SUBTRACT", v, 1.0)
    v = math_node("MULTIPLY", v, gain)
    v = math_node("ADD", v, 1.0)
    v = math_node("MAXIMUM", v, lo)
    v = math_node("MINIMUM", v, hi)
    return math_node("POWER", v, 2.2)


def toon_material(name, color_rgb=None, image_path=None, params=OBJECT):
    """Emission material: base colour (sRGB tuple or world-XY image, 1 repeat per tile) times lum."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    nt.links.new(_lum_strength(nt, **params), em.inputs["Strength"])

    if image_path:
        nt.links.new(_world_xy_texture(nt, image_path), em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = lin(color_rgb)
    return mat


def _world_xy_texture(nt, image_path):
    """Image texture repeating once per tile in world XY; returns the colour socket.

    The tile spans -0.5..0.5, so the texture is shifted to put its wrap lines on tile edges.
    """
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Location"].default_value = (0.5, 0.5, 0.0)
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 0.0)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image_path, check_existing=True)
    tex.image.colorspace_settings.name = "sRGB"
    tex.extension = "REPEAT"
    tex.interpolation = "Cubic"
    nt.links.new(geo.outputs["Position"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    return tex.outputs["Color"]


def _mix_rgb(nt, factor, a, b):
    """Linear mix of two colour sockets (a at factor 0, b at 1); factor is a socket."""
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    nt.links.new(factor, m.inputs["Factor"])
    for socket, src in ((m.inputs[6], a), (m.inputs[7], b)):
        if isinstance(src, tuple):
            socket.default_value = src
        else:
            nt.links.new(src, socket)
    return m.outputs[2]


def _band(nt, z_socket, lo_level, hi_level, peak=1.0):
    """Smooth 0 -> peak ramp of world height between two height levels."""
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    nt.links.new(z_socket, mr.inputs["Value"])
    mr.inputs["From Min"].default_value = lo_level * SHORE_LEVEL
    mr.inputs["From Max"].default_value = hi_level * SHORE_LEVEL
    mr.inputs["To Max"].default_value = peak
    return mr.outputs["Result"]


SHORE_LEVEL = 1.0 / (2.0 * math.sqrt(6.0))  # one OpenTTD height level, see ottd_camera.LEVEL
FOAM_RGB = (240, 252, 250)
WET_SAND_RGB = (196, 176, 126)


def shore_material(water_path, sand_path, grass_path):
    """Shore tile: colour by height on the tile, after the map study's coastline.

    Below 0.05 levels the surface shows water (unshaded, identical to the open
    water tile), then a foam line, wet sand, beach and finally the regular
    meadow. Land parts get the usual ground shading.
    """
    mat = bpy.data.materials.new("shore")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    z = sep.outputs["Z"]

    water = _world_xy_texture(nt, water_path)
    sand = _world_xy_texture(nt, sand_path)
    grass = _world_xy_texture(nt, grass_path)

    land = _mix_rgb(nt, _band(nt, z, 0.10, 0.22), lin(WET_SAND_RGB), sand)
    land = _mix_rgb(nt, _band(nt, z, 0.40, 0.56), land, grass)
    lum = nt.nodes.new("ShaderNodeVectorMath")
    lum.operation = "SCALE"
    nt.links.new(land, lum.inputs[0])
    nt.links.new(_lum_strength(nt, **GROUND), lum.inputs["Scale"])
    shaded_land = lum.outputs["Vector"]

    foam = _mix_rgb(nt, _band(nt, z, 0.035, 0.06, peak=0.6), water, lin(FOAM_RGB))
    surface = _mix_rgb(nt, _band(nt, z, 0.08, 0.11), foam, shaded_land)
    nt.links.new(surface, em.inputs["Color"])
    return mat


def configure_render(scene, samples=64):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.use_denoising = False
    scene.cycles.samples = samples
    scene.cycles.filter_width = 1.5
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.dither_intensity = 0.0
    world = bpy.data.worlds.new("black")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    scene.world = world


def add_shadow_sun(scene, angle_deg=6.0):
    """Sun used only for cast shadows onto a shadow catcher, from the study's light direction."""
    sun_data = bpy.data.lights.new("shadow_sun", "SUN")
    sun_data.energy = 3.0
    sun_data.angle = math.radians(angle_deg)
    sun = bpy.data.objects.new("shadow_sun", sun_data)
    sun.rotation_euler = LIGHT.to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(sun)
    return sun
