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
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        mapping = nt.nodes.new("ShaderNodeMapping")
        # Tile spans -0.5..0.5; shift so the texture's wrap lines fall on tile edges.
        mapping.inputs["Location"].default_value = (0.5, 0.5, 0.0)
        mapping.inputs["Scale"].default_value = (1.0, 1.0, 0.0)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image_path, check_existing=True)
        tex.image.colorspace_settings.name = "sRGB"
        tex.extension = "REPEAT"
        tex.interpolation = "Cubic"
        nt.links.new(geo.outputs["Position"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = lin(color_rgb)
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
