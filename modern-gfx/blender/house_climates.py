"""Town house models of the sub-arctic, sub-tropical and toyland climates, for render_houses.py.

Same frame and kit as the temperate models there (see house_specs.py): x, y
0-16 per tile, the visible walls face +x and +y, z in height units. Each
function builds one finished house into the Kit k; snowy sub-arctic variants
are the same function on a kit that puts every roof under snow.

Sub-arctic: steep roofs, timber and brick, falu red and ochre walls.
Sub-tropical: flat roofs or low tiled roofs, white and ochre walls, arches,
roof water tanks and palms. Toyland: toy shapes in bright colours.
"""

import math


# --- sub-arctic ----------------------------------------------------------------------------

def steep_house(k, x0, x1, y0, y1, wall_h, ridge, axis, wall, roof, door=None, chimney=None,
                floors=1, trim="white"):
    """A house with a steep gable roof; door: (face, pos)."""
    k.box(x0, x1, y0, y1, 0, wall_h, wall)
    fl = wall_h / floors
    k.windows(x0, x1, y0, y1, 0, wall_h, floor=fl, wh=min(2.4, fl - 2.2), pitch=2.5, sill=fl - min(2.4, fl - 2.2) - 1.0,
              frame=trim, skip=(1,) if door else ())
    k.gable(x0, x1, y0, y1, wall_h, ridge, axis, roof, wall)
    if door:
        k.door(door[0], x0, x1, y0, y1, door[1], w=1.4, h=3.4, mat="door")
    if chimney:
        k.chimney(chimney[0], chimney[1], ridge - 3, ridge + 1.5)


def arc_brick(k):
    steep_house(k, 4, 11, 4, 12, 7, 18, "x", "rc", "roof_red", door=("x", 8), chimney=(6, 6))
    k.box(11, 12.6, 6.6, 9.4, 0, 0.5, "stone")
    k.box(11, 12.6, 6.4, 9.6, 3.8, 4.2, "roof_red")


def arc_cream(k):
    steep_house(k, 4, 11, 4, 11, 7, 17, "y", "cream", "roof_slate", door=("y", 7.5), chimney=(7.5, 5.5))
    for x in (5.6, 9.4):  # recoloured shutters
        k.box(x - 1.2, x - 0.8, 11, 11.15, 2.2, 4.8, "rc")
        k.box(x + 0.8, x + 1.2, 11, 11.15, 2.2, 4.8, "rc")


def arc_cottage(k):
    k.box(4, 11, 3, 12, 0, 6, "stone")
    k.windows(4, 11, 3, 12, 0, 6, floor=6, wh=2.0, pitch=2.6, sill=2.2, skip=(1,))
    k.gable(4, 11, 3, 12, 6, 15, "y", "turf", "timber", over=0.9)
    k.door("x", 4, 11, 3, 12, 7.5, w=1.4, h=3.2, mat="wood")
    k.chimney(7.5, 10, 11, 16.5, "stone")
    k.box(11, 13.5, 3.5, 6, 0, 2.2, "wood")  # wood pile
    k.box(11, 13.5, 3.5, 6, 2.2, 2.6, "roof_brown")


def arc_long(k):
    k.box(2, 14, 5, 10, 0, 6, "falu")
    k.windows(2, 14, 5, 10, 0, 6, floor=6, wh=2.2, pitch=2.4, sill=2.0, frame="white", skip=(2,))
    k.gable(2, 14, 5, 10, 6, 13, "x", "roof_slate", "falu")
    k.door("y", 2, 14, 5, 10, 8, w=1.4, h=3.4, mat="white")
    k.chimney(6, 7.5, 10, 14.5)
    k.chimney(11, 7.5, 10, 14.5)


def arc_thatch(k):
    k.box(3, 11, 3, 9, 0, 6.5, "rc")
    k.box(3, 8, 9, 13, 0, 6.5, "rc")
    k.windows(3, 11, 3, 9, 0, 6.5, floor=6.5, wh=2.2, pitch=2.5, sill=2.4, faces="x")
    k.windows(3, 8, 9, 13, 0, 6.5, floor=6.5, wh=2.2, pitch=2.5, sill=2.4)
    k.gable(3, 11, 3, 9, 6.5, 15, "x", "thatch", "rc", over=0.8)
    k.gable(3, 8, 9, 13, 6.5, 14, "y", "thatch", "rc", over=0.8)
    k.door("x", 3, 11, 3, 9, 6, w=1.4, h=3.4, mat="wood")
    k.chimney(6, 5, 11, 16, "stone")


def arc_office_a(k):
    k.box(1, 15, 1, 15, 0, 6, "glass_light")
    k.box(1.5, 14.5, 1.5, 14.5, 0, 6.2, "concrete")
    k.box(1, 15, 1, 15, 6, 62, "white")
    k.windows(1, 15, 1, 15, 6, 62, floor=5, pitch=2.2, ww=1.4, wh=3.0, sill=1.0)
    for z in (6, 34):
        k.box(1, 15.15, 1, 15.15, z, z + 1.2, "rc")
    k.flat_roof(1, 15, 1, 15, 62, "white")
    k.box(5, 11, 5, 10, 62, 65, "concrete")
    k.door("x", 1, 15, 1, 15, 8, w=3, h=4.5, mat="glass", canopy="concrete")


def arc_office_b(k):
    k.box(1, 10, 1, 10, 0, 64, "blue_band")
    k.windows(1, 10, 1, 10, 4, 64, floor=4, pitch=1.8, ww=1.0, wh=2.4, sill=0.8, frame="white")
    k.flat_roof(1, 10, 1, 10, 64, "white")
    k.box(3, 8, 3, 7, 64, 67, "concrete")
    k.box(10, 15, 2, 9, 0, 30, "rc")
    k.windows(10, 15, 2, 9, 4, 30, floor=4, pitch=1.8, ww=1.0, wh=2.4, sill=0.8)
    k.flat_roof(10, 15, 2, 9, 30, "rc")
    k.box(2, 9, 10, 15, 0, 24, "rc")
    k.windows(2, 9, 10, 15, 4, 24, floor=4, pitch=1.8, ww=1.0, wh=2.4, sill=0.8)
    k.flat_roof(2, 9, 10, 15, 24, "rc")
    k.box(10.5, 15.5, 10.5, 15.5, 0, 0.4, "stone")
    k.bush(13, 13, 1.2)


def arc_office_c(k):
    poly = []
    for cx, cy, a0 in ((12, 12, 0), (4, 12, 90), (4, 4, 180), (12, 4, 270)):  # rounded corners
        for j in range(4):
            a = math.radians(a0 + j * 30)
            poly.append((cx + 3 * math.cos(a), cy + 3 * math.sin(a)))
    k.prism(poly, 0, 6, "glass_light")
    for z in range(6, 78, 5):
        k.prism(poly, z, z + 3.4, "glass")
        k.prism([(8 + (x - 8) * 1.02, 8 + (y - 8) * 1.02) for x, y in poly], z + 3.4, z + 5, "rc")
    k.prism(poly, 78, 80, "white")
    k.box(5, 11, 5, 11, 80, 86, "rc")
    k.flat_roof(5, 11, 5, 11, 86, "white", parapet=0.4)
    k.cyl(8, 8, 0.25, 86, 94, "metal", n=6, r_top=0.1)
    k.box(14.5, 16, 5, 11, 4.5, 5, "white")


def arc_house_c(k):
    steep_house(k, 4, 11, 4, 10, 8, 17, "y", "ochre", "roof_brown", door=("x", 6.5), floors=1)
    k.box(4, 9, 10, 13, 0, 8, "ochre")
    k.windows(4, 9, 10, 13, 0, 8, floor=8, wh=2.4, sill=2.8, faces="y")
    k.gable(4, 9, 10, 13, 8, 14, "x", "roof_brown", "ochre", over=0.4)
    k.chimney(7, 6, 13, 18.5)


def arc_house_d(k):
    k.box(5, 11, 4, 11, 0, 8, "brick")
    k.windows(5, 11, 4, 11, 0, 8, floor=8, wh=2.4, pitch=2.5, sill=2.8, skip=(1,), faces="x")
    k.windows(5, 11, 4, 11, 0, 8, floor=8, wh=2.4, pitch=2.5, sill=2.8, faces="y")
    k.gable(5, 11, 4, 11, 8, 15.5, "x", "roof_slate", "brick")
    k.door("x", 5, 11, 4, 11, 7.5, w=1.4, h=3.4)
    k.chimney(7, 6, 12, 16.5)


def arc_hall(k):
    k.box(1, 15, 1, 15, 0, 20, "brick")
    k.box(1.4, 15.15, 1.4, 15.15, 0.4, 4.6, "glass_light")
    k.windows(1, 15, 1, 15, 6, 20, floor=7, pitch=2.4, wh=3.4, sill=1.6)
    k.hip(1, 15, 1, 15, 20, 34, "roof_red", over=0.4)
    for c in (4.5, 11.5):  # stepped gables on both street sides
        for face in "xy":
            if face == "x":
                k.box(13, 15, c - 2.5, c + 2.5, 20, 24, "brick")
                k.gable(9, 15, c - 2.5, c + 2.5, 24, 30, "x", "roof_red", "brick", over=0.3)
                k.box(14.9, 15.1, c - 0.7, c + 0.7, 21, 24.5, "glass")
            else:
                k.box(c - 2.5, c + 2.5, 13, 15, 20, 24, "brick")
                k.gable(c - 2.5, c + 2.5, 9, 15, 24, 30, "y", "roof_red", "brick", over=0.3)
                k.box(c - 0.7, c + 0.7, 14.9, 15.1, 21, 24.5, "glass")
    k.door("x", 1, 15, 1, 15, 8, w=2.6, h=4.4, mat="wood", canopy="roof_slate")


def arc_church(k):
    k.box(3, 13, 4, 12, 0, 10, "brick")
    k.gable(3, 13, 4, 12, 10, 24, "x", "roof_slate", "brick", over=0.5)
    for x in (5, 8, 11):
        k.box(x - 0.6, x + 0.6, 11.95, 12.12, 3, 8, "glass")
    k.box(12.95, 13.12, 6.6, 9.4, 0, 4.4, "wood")
    k.box(12.95, 13.15, 7.4, 8.6, 9, 16, "glass")  # tall window with a cross
    k.box(13.1, 13.25, 7.85, 8.15, 9, 16, "white")
    k.box(13.1, 13.25, 7.0, 9.0, 13.2, 13.6, "white")
    k.box(5, 7, 7, 9, 22, 27, "timber")  # belfry on the ridge
    k.hip(5, 7, 7, 9, 27, 33, "roof_slate", over=0.3)


def arc_house_e(k):
    k.box(3, 13, 3, 10, 0, 8, "rc")
    k.windows(3, 13, 3, 10, 0, 8, floor=8, wh=2.4, pitch=2.5, sill=2.8, skip=(1,), faces="x")
    k.windows(3, 13, 3, 10, 0, 8, floor=8, wh=2.4, pitch=2.5, sill=2.8, faces="y")
    k.gable(3, 13, 3, 10, 8, 17, "x", "roof_red", "rc")
    for x in (5.5, 10.5):
        k.dormer("y", 9.4, x, 10, wall="white", roof="roof_red")
    k.door("x", 3, 13, 3, 10, 6.5, w=1.4, h=3.4)
    k.chimney(8, 5.5, 13, 18.5)


def arc_tall_brick(k):
    k.box(1, 15, 1, 15, 0, 26, "rc")
    k.shopfront(1, 15, 1, 15, awning="roof_red")
    k.windows(1, 15, 1, 15, 6, 26, floor=6.5, pitch=2.4, wh=3.4)
    k.box(0.8, 15.2, 0.8, 15.2, 26, 27, "stone")
    k.hip(1, 15, 1, 15, 27, 40, "roof_slate", over=-0.4)
    for a in (4, 8, 12):
        k.dormer("x", 14.2, a, 28, wall="stone")
        k.dormer("y", 14.2, a, 28, wall="stone")


def arc_hotel(k):
    k.box(2, 14, 12, 30, 0, 22, "brick")
    k.box(2.4, 14.15, 12.4, 30.15, 0, 4.6, "glass_light")
    k.windows(2, 14, 12, 30, 6, 22, floor=5.3, pitch=2.3, wh=3.0, sill=1.2)
    k.hip(2, 14, 12, 30, 22, 33, "roof_slate")
    k.box(12, 14.6, 18, 24, 0, 30, "stone")  # entrance tower
    k.hip(12, 14.6, 18, 24, 30, 38, "roof_slate", over=0.2)
    k.door("x", 2, 14.6, 18, 24, 21, w=3, h=4.4, mat="wood", canopy="roof_red")
    k.box(4, 12, 4, 12, 0, 12, "brick")  # garden wing
    k.windows(4, 12, 4, 12, 0, 12, floor=6, pitch=2.4, wh=3.0, sill=1.6)
    k.gable(4, 12, 4, 12, 12, 20, "x", "roof_slate", "brick")
    k.tree(13.5, 6, 0.8, "conifer")
    k.tree(10, 2.5, 0.7, "conifer")


def arc_shops(k):
    k.box(1, 8, 1, 15, 0, 40, "rc")
    k.windows(1, 8, 1, 15, 6, 40, faces="y", pitch=2.4, wh=3.4)
    k.flat_roof(1, 8, 1, 15, 40, "rc")
    k.box(8, 15, 1, 15, 0, 32, "stone")
    k.shopfront(8, 15, 1, 15, awning="roof_red")
    k.windows(8, 15, 1, 15, 6, 32, pitch=2.4, wh=3.4)
    k.windows(1, 8.2, 1, 15, 32, 40, faces="x", pitch=2.4, wh=3.4)
    k.flat_roof(8, 15, 1, 15, 32, "stone")


def arc_office_d(k):
    k.box(2, 14, 2, 14, 0, 5, "glass")
    for x in (2.2, 8, 13.6):
        for y in (2.2, 13.6):
            k.box(x - 0.2, x + 0.4, y - 0.2, y + 0.4, 0, 5, "concrete")
    k.box(2, 14, 2, 14, 5, 58, "grey")
    k.windows(2, 14, 2, 14, 5, 58, floor=4.4, pitch=2.0, ww=1.3, wh=2.6, sill=0.9)
    for z in range(5, 58, 9):
        k.box(2, 14.12, 2, 14.12, z, z + 0.5, "rc")
    k.flat_roof(2, 14, 2, 14, 58, "grey")
    k.box(5, 10, 5, 10, 58, 61, "concrete")


def arc_twin(k):
    k.box(6, 28, 3, 13, 0, 6, "glass_light")
    k.box(6, 28, 3, 13, 6, 80, "ochre")
    k.windows(6, 28, 3, 13, 6, 80, floor=5, pitch=2.2, ww=1.3, wh=3.2, sill=1.0)
    for x in (12, 22):  # vertical service strips
        k.box(x - 0.8, x + 0.8, 13, 13.3, 6, 80, "concrete")
    k.flat_roof(6, 28, 3, 13, 80, "ochre")
    k.box(14, 20, 5, 11, 80, 84, "concrete")
    k.box(8, 26, 13, 15, 0, 0.3, "stone")
    k.door("y", 6, 28, 3, 13, 17, w=4, h=4.8, mat="glass", canopy="concrete")


# --- sub-tropical -------------------------------------------------------------------------

def garden_wall(k, gate=("x", 8), h=1.3, mat="plaster"):
    """Low wall along the street sides of the plot, open at the gate (face, position)."""
    for face in "xy":
        lo, hi = 0.3, 15.7
        gaps = [(gate[1] - 1.2, gate[1] + 1.2)] if gate and gate[0] == face else []
        cuts = [lo] + [c for g in gaps for c in g] + [hi]
        for a0, a1 in zip(cuts[::2], cuts[1::2]):
            if face == "x":
                k.box(15.3, 15.8, a0, a1, 0, h, mat)
            else:
                k.box(a0, a1, 15.3, 15.8, 0, h, mat)


def trop_villa_a(k):
    k.box(4, 11, 4, 12, 0, 12, "plaster")
    k.windows(4, 11, 4, 12, 0, 12, floor=6, wh=2.4, pitch=2.6, sill=1.8, frame="blue_band", skip=(1,))
    k.hip(4, 11, 4, 12, 12, 16, "roof_tile", over=0.8)
    k.door("x", 4, 11, 4, 12, 8, w=1.6, h=3.6, mat="wood")
    garden_wall(k, ("x", 8))
    k.palm(13, 3.5, 13, 0.9)
    k.bush(13.5, 13.5, 1.0, "flower")


def trop_villa_b(k):
    k.box(3, 10, 5, 12, 0, 7, "plaster")
    k.windows(3, 10, 5, 12, 0, 7, floor=7, wh=2.4, pitch=2.6, sill=2.4, frame="blue_band", skip=(1,))
    k.gable(3, 10, 5, 12, 7, 11, "y", "roof_tile", "plaster")
    k.door("x", 3, 10, 5, 12, 8.5, w=1.6, h=3.6, mat="wood")
    k.box(10, 13, 5, 9, 0, 5, "plaster")  # terrace with a pergola
    k.box(10, 13.2, 5, 9.2, 5, 5.4, "wood")
    garden_wall(k, ("x", 8.5))
    k.bush(13.5, 12, 1.1)


def trop_villa_c(k):
    k.box(4, 10, 5, 11, 0, 6.5, "plaster")
    k.windows(4, 10, 5, 11, 0, 6.5, floor=6.5, wh=2.2, pitch=2.5, sill=2.2, frame="blue_band", skip=(1,))
    k.hip(4, 10, 5, 11, 6.5, 10, "roof_tile", over=0.7)
    k.door("x", 4, 10, 5, 11, 8, w=1.4, h=3.4, mat="wood")
    for y in (2, 4.5, 14):
        k.bush(14.2, y, 0.9, "leaf_dark")
    k.palm(2.5, 13, 11, 0.8, lean=(0.4, 0.7))


def adobe_hut(k, x0, x1, y0, y1, h, roof="tin", door=None):
    k.box(x0, x1, y0, y1, 0, h, "adobe")
    k.box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, h, h + 0.4, roof)
    k.box(x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, h + 0.4, h + 0.7, "adobe")
    if door:
        face, pos = door
        k.door(face, x0, x1, y0, y1, pos, w=1.2, h=min(3.2, h - 0.6), mat="shade")
    k.windows(x0, x1, y0, y1, 0, h, floor=h, wh=1.2, ww=1.0, sill=h - 2.4, pitch=2.6, glass="shade", frame="adobe",
              skip=(0,) if door else ())


def trop_huts_a(k):
    adobe_hut(k, 3, 7, 3, 7, 5, door=("x", 5))
    adobe_hut(k, 8, 12, 9, 13, 4.5, roof="roof_tile", door=("y", 10))
    k.palm(12.5, 4, 12, 0.85)


def trop_huts_b(k):
    adobe_hut(k, 2, 6, 3, 7, 4.5, door=("x", 5))
    adobe_hut(k, 7, 11, 2, 6, 5, roof="roof_tile")
    adobe_hut(k, 8, 13, 9, 13, 4.5, door=("y", 10.5))
    k.cyl(4.5, 11, 1.1, 0, 1.2, "terracotta", n=10, r_top=1.3)  # water jar


def trop_huts_c(k):
    k.box(3, 10, 4, 10, 0, 7, "plaster")
    k.windows(3, 10, 4, 10, 0, 7, floor=7, wh=2.2, pitch=2.4, sill=2.4, frame="blue_band", skip=(1,))
    k.hip(3, 10, 4, 10, 7, 10.5, "roof_tile", over=0.6)
    k.door("x", 3, 10, 4, 10, 7, w=1.4, h=3.4, mat="wood")
    adobe_hut(k, 10, 13, 10, 13, 4)
    k.palm(4, 13, 10, 0.75)


def trop_huts_d(k):
    adobe_hut(k, 2, 7, 3, 9, 5, roof="roof_tile", door=("x", 6))
    adobe_hut(k, 9, 14, 8, 13, 5, door=("y", 11.5))
    k.palm(12, 3.5, 12, 0.85, lean=(0.5, -0.3))
    k.bush(5, 12.5, 1.0, "leaf_dark")


def trop_flats_tall(k):
    k.box(2, 14, 2, 14, 0, 70, "terracotta")
    for z in range(4, 70, 6):  # white floor slabs and deep balconies on the street sides
        k.box(2, 14.9, 2, 14.9, z, z + 0.6, "plaster")
        k.box(14, 14.9, 2.5, 13.5, z + 0.6, z + 1.6, "plaster")
        k.box(2.5, 13.5, 14, 14.9, z + 0.6, z + 1.6, "plaster")
    k.windows(2, 14, 2, 14, 4, 70, floor=6, pitch=2.4, ww=1.5, wh=3.4, sill=1.2, frame="plaster")
    k.flat_roof(2, 14, 2, 14, 70, "plaster")
    k.water_tank(6, 6, 70.2, r=1.5, legs=2.5)


def trop_mission(k):
    k.box(2, 12, 3, 12, 0, 14, "adobe")
    k.box(2.4, 11.6, 3.4, 11.6, 14, 14.3, "roof_flat")
    k.box(2, 12, 3, 12, 14, 15, "adobe")
    k.arches("y", 12, 3, 11, 0, 5, 3, mat="shade")
    k.box(12, 14.5, 3, 12, 0, 6, "adobe")  # arcade along the front
    k.arches("x", 14.5, 3.5, 11.5, 0, 4.6, 4, mat="shade")
    k.box(11.8, 14.7, 2.8, 12.2, 6, 6.6, "terracotta")
    # Bell gable over the entrance with two openings.
    k.extrude([(4.5, 14), (11.5, 14), (11.5, 18), (9.6, 18), (8.8, 21.5), (7.2, 21.5), (6.4, 18), (4.5, 18)],
              "x", 11.4, 12.4, "adobe")
    k.arches("x", 12.4, 5.5, 10.5, 15.2, 4.2, 2, mat="shade")
    k.box(12.3, 12.6, 7.8, 8.2, 19.6, 21.6, "wood")
    k.box(12.3, 12.6, 7.2, 8.8, 20.6, 21.0, "wood")
    k.palm(14.5, 14, 13, 0.85)
    k.palm(4, 14.3, 11, 0.75, lean=(0.3, 0.6))


def trop_villa_d(k):
    k.box(3, 11, 4, 12, 0, 13, "plaster")
    k.windows(3, 11, 4, 12, 0, 13, floor=6.5, wh=2.4, pitch=2.6, sill=2.0, frame="blue_band", skip=(1,))
    k.box(11, 12.6, 5, 11, 6.2, 6.6, "plaster")  # balcony
    k.box(12.4, 12.6, 5, 11, 6.6, 7.8, "blue_band")
    k.hip(3, 11, 4, 12, 13, 17, "roof_tile", over=0.8)
    k.door("x", 3, 11, 4, 12, 8, w=1.6, h=3.6, mat="wood")
    garden_wall(k, ("x", 8))
    k.palm(13.5, 13.5, 12, 0.85)


def trop_flats_a(k):
    k.box(2, 14, 2, 14, 0, 40, "plaster")
    k.windows(2, 14, 2, 14, 0, 40, floor=6.6, pitch=2.8, ww=1.6, wh=3.2, sill=1.6, frame="plaster")
    z = 6.6
    while z < 40:  # balconies with recoloured rails
        for a in (4.5, 10.5):
            k.box(14, 15.2, a - 1.6, a + 1.6, z, z + 0.4, "plaster")
            k.box(15.0, 15.2, a - 1.6, a + 1.6, z + 0.4, z + 1.6, "rc")
            k.box(a - 1.6, a + 1.6, 14, 15.2, z, z + 0.4, "plaster")
            k.box(a - 1.6, a + 1.6, 15.0, 15.2, z + 0.4, z + 1.6, "rc")
        z += 6.6
    k.flat_roof(2, 14, 2, 14, 40, "plaster")
    k.water_tank(5, 5, 40.2, r=1.4, legs=2.5)


def trop_flats_b(k):
    k.box(1, 15, 1, 15, 0, 32, "plaster")
    for z in (1, 11.5, 22):
        k.box(1, 15.12, 1, 15.12, z + 6.2, z + 7.4, "rc")
    k.windows(1, 15, 1, 15, 0, 32, floor=10.5, pitch=2.8, ww=1.8, wh=3.6, sill=2.2, frame="plaster")
    k.flat_roof(1, 15, 1, 15, 32, "plaster")
    k.box(4, 8, 4, 8, 32, 35, "plaster")
    k.door("x", 1, 15, 1, 15, 8, w=2.4, h=4.0, mat="shade")


def trop_flats_c(k):
    k.box(2, 14, 2, 14, 0, 30, "ochre")
    k.arches("x", 14, 2.5, 13.5, 0, 5.5, 4, mat="shade")
    k.arches("y", 14, 2.5, 13.5, 0, 5.5, 4, mat="shade")
    k.windows(2, 14, 2, 14, 7, 30, floor=7.5, pitch=2.8, ww=1.6, wh=3.6, sill=1.8, frame="plaster")
    k.flat_roof(2, 14, 2, 14, 30, "ochre")
    k.water_tank(6, 6, 30.2, r=2.0, legs=4.0, h=3.6)
    k.box(9, 12, 8, 11, 30, 32.5, "plaster")


def trop_tower(k):
    k.box(2, 14, 2, 14, 0, 8, "glass")
    k.box(2, 14.1, 2, 14.1, 8, 9, "plaster")
    k.box(2, 9, 2, 9, 9, 80, "plaster")
    k.windows(2, 9, 2, 9, 9, 80, floor=4.4, pitch=1.8, ww=1.2, wh=3.0, sill=0.7, frame="plaster")
    k.flat_roof(2, 9, 2, 9, 80, "plaster")
    k.box(4, 7, 4, 7, 80, 84, "plaster")
    k.cyl(5.5, 5.5, 0.3, 84, 96, "metal", n=6, r_top=0.08)
    k.box(9, 14, 2, 8, 9, 40, "glass")
    k.flat_roof(9, 14, 2, 8, 40, "plaster")
    k.box(10.5, 14, 10.5, 14, 9, 9.3, "lawn")  # roof garden with a palm on the podium
    k.palm(12, 12, 9, 0.7)


def trop_twin(k):
    k.box(2, 30, 2, 14, 0, 10, "plaster")
    k.box(2.4, 30.15, 2.4, 14.15, 0, 5, "glass_light")
    k.box(13, 18, 3, 13, 10, 10.3, "pool")
    for x0, x1, top in ((4, 12, 86), (20, 28, 100)):
        k.box(x0, x1, 4, 12, 10, top, "glass")
        for z in range(10, top, 6):
            k.box(x0, x1 + 0.12, 4, 12.12, z, z + 0.4, "plaster")
        k.flat_roof(x0, x1, 4, 12, top, "plaster")
        k.box(x0 + 2, x1 - 2, 6, 10, top, top + 3, "plaster")
        k.cyl((x0 + x1) / 2, 8, 0.25, top + 3, top + 12, "metal", n=6, r_top=0.08)
    k.palm(15, 1.5, 10, 0.7)


# --- toyland ------------------------------------------------------------------------------

def grow(k, n0, f, cx=8.0, cy=8.0):
    """Scale the solids added since part n0 by f about (cx, cy) on the ground."""
    for _, bm in k.parts[n0:]:
        for v in bm.verts:
            v.co.x, v.co.y, v.co.z = cx + (v.co.x - cx) * f, cy + (v.co.y - cy) * f, v.co.z * f


def toy_church(k):
    k.box(4, 12, 5, 11, 0, 14, "toy_cream")
    k.windows(4, 12, 5, 11, 0, 14, floor=14, wh=6, ww=1.4, pitch=2.6, sill=4, glass="toy_blue", frame="toy_yellow")
    k.gable(4, 12, 5, 11, 14, 20, "x", "roof_red", "toy_cream")
    k.box(10, 14, 6, 10, 0, 34, "rc")  # clock tower with a pointed spire
    k.box(13.95, 14.15, 7, 9, 0, 4.4, "toy_brown")
    k.cyl(14.1, 8, 1.4, 24, 24.2, "white", n=12)
    k.box(14.15, 14.3, 7.95, 8.05, 24.2, 25.3, "toy_black")
    k.box(13.9, 14.3, 7.8, 8.9, 24.2, 24.4, "toy_black")
    k.box(9.6, 14.4, 5.6, 10.4, 34, 35, "toy_yellow")
    k.cyl(12, 8, 3.0, 35, 54, "roof_red", n=4, r_top=0)
    k.blob(12, 8, 54.6, 0.6, 0.6, 0.6, "toy_yellow")


def toy_pavilion(k):
    for x in (3.6, 12.4):
        for y in (3.6, 12.4):
            k.cyl(x, y, 0.7, 0, 30, "white", n=8)
    k.box(5, 11, 5, 11, 0, 8, "toy_pink")
    k.box(4, 12, 4, 12, 14, 26, "white")
    k.windows(4, 12, 4, 12, 14, 26, floor=6, wh=3, ww=1.4, pitch=2.4, sill=1.5, glass="toy_blue", frame="white")
    k.box(2.6, 13.4, 2.6, 13.4, 30, 31, "toy_pink")
    k.hip(2.6, 13.4, 2.6, 13.4, 31, 38, "toy_pink", over=0.8, )
    k.box(6.5, 9.5, 6.5, 9.5, 37, 40, "white")


def toy_cabin(k):
    k.box(3, 13, 4, 12, 0, 7, "toy_brown")
    for z in (1.5, 3.5, 5.5):  # log ends
        k.box(3, 13.2, 4, 12.2, z, z + 0.3, "wood")
    k.windows(3, 13, 4, 12, 0, 7, floor=7, wh=2.4, pitch=3, sill=2.4, glass="toy_yellow", frame="toy_red", skip=(1,))
    k.gable(3, 13, 4, 12, 7, 13, "x", "roof_green", "toy_brown", over=0.8)
    k.door("x", 3, 13, 4, 12, 8, w=1.6, h=3.6, mat="toy_red")
    k.chimney(6, 6, 9, 15, "toy_red")


def toy_dome(k):
    for x in (3.6, 12.4):
        for y in (3.6, 12.4):
            k.cyl(x, y, 0.8, 0, 20, "white", n=8)
    k.box(5, 11, 5, 11, 0, 9, "toy_pink")
    k.box(3, 13, 3, 13, 20, 22, "toy_cream")
    k.blob(8, 8, 22, 5.6, 5.6, 9, "roof_green", subdiv=2)
    k.cyl(8, 8, 1.4, 30, 34, "toy_cream", n=8)
    k.cyl(8, 8, 1.8, 34, 37, "roof_green", n=8, r_top=0)


def toy_house_a(k):
    k.box(3, 13, 3, 12, 0, 13, "rc")
    k.box(3, 13.1, 3, 12.1, 6.2, 6.8, "toy_yellow")
    k.windows(3, 13, 3, 12, 0, 13, floor=6.5, wh=2.6, pitch=2.8, sill=2, glass="toy_blue", frame="white", skip=(1,))
    k.hip(3, 13, 3, 12, 13, 19, "toy_blue", over=0.8)
    k.door("x", 3, 13, 3, 12, 7.5, w=1.6, h=3.8, mat="toy_red")
    k.cyl(9, 5, 0.12, 18, 22, "metal", n=4)  # aerial
    k.box(8, 10, 4.9, 5.1, 21, 21.2, "metal")


def toy_flats(k):
    k.box(3, 13, 3, 13, 0, 32, "rc")
    k.windows(3, 13, 3, 13, 0, 32, floor=6.4, wh=3, pitch=2.8, sill=1.6, glass="toy_teal", frame="toy_cream")
    k.box(2.6, 13.4, 2.6, 13.4, 32, 33.6, "toy_blue")
    k.flat_roof(3, 13, 3, 13, 33.6, "toy_blue", roof="roof_flat")
    k.cyl(5, 5, 0.5, 33, 40, "toy_yellow", n=8)  # chimney pipe
    k.door("x", 3, 13, 3, 13, 8, w=2, h=4, mat="toy_brown")


def toy_house_b(k):
    k.box(4, 12, 3, 12, 0, 8, "rc")
    k.windows(4, 12, 3, 12, 0, 8, floor=8, wh=2.8, pitch=2.8, sill=2.4, glass="toy_green", frame="white", skip=(1,))
    k.gable(4, 12, 3, 12, 8, 14, "y", "toy_blue", "rc", over=0.7)
    k.door("x", 4, 12, 3, 12, 7.5, w=1.6, h=3.6, mat="toy_yellow")
    for x in (6, 10):
        k.cyl(x, 7.5, 0.2, 11, 16, "toy_green", n=6)
        k.blob(x, 7.5, 16.4, 0.5, 0.5, 0.5, "toy_red")


def toy_office(k):
    k.box(2, 14, 2, 14, 0, 58, "white")
    k.windows(2, 14, 2, 14, 4, 58, floor=5, pitch=2.2, ww=1.3, wh=3.2, sill=1.0, glass="toy_blue", frame="white")
    k.box(2.4, 14.15, 2.4, 14.15, 0, 4, "toy_yellow")
    k.box(1.8, 14.2, 1.8, 14.2, 58, 60, "toy_orange")
    k.hip(2, 14, 2, 14, 60, 66, "roof_brown", over=0.3)
    k.box(6, 10, 6, 10, 64, 68, "toy_teal")


def toy_boot(k):
    # The leg of an old boot standing on tile 0 (y 0-16), its foot reaching over tile 1.
    leg = [(8 + 4.2 * math.cos(a), 8.5 + 3.8 * math.sin(a)) for a in (i * math.tau / 12 for i in range(12))]
    k.prism(leg, 0, 46, "toy_brown")
    for z in (12, 26, 38):
        k.prism([(8 + (x - 8) * 1.04, 8.5 + (y - 8.5) * 1.04) for x, y in leg], z, z + 0.8, "toy_black")
    k.prism([(8 + (x - 8) * 1.12, 8.5 + (y - 8.5) * 1.12) for x, y in leg], 46, 49, "toy_cream")  # cuff
    k.cyl(8, 8.5, 4.4, 49, 56, "roof_green", n=12, r_top=1.0)
    k.cyl(9.5, 7.5, 0.6, 52, 60, "toy_red", n=6)
    foot = [(5, 10), (12, 10), (12.6, 18), (12.4, 24), (11, 27.4), (8.4, 28), (5.8, 27.2), (4.8, 24), (4.6, 16)]
    k.prism(foot, 0, 10, "toy_brown")
    k.prism([(8.5 + (x - 8.5) * 0.92, y * 0.98 + 0.2) for x, y in foot], 10, 13, "toy_brown")
    k.prism([(8.5 + (x - 8.5) * 1.03, y) for x, y in foot], 0, 1.2, "toy_black")  # sole
    for y in (15, 19.5, 24):
        k.box(12.3, 12.75, y - 0.9, y + 0.9, 4, 7, "toy_yellow")
    for z in (16, 30):
        k.box(12.0, 12.4, 7.3, 9.7, z, z + 3.4, "toy_yellow")
    k.box(11.9, 12.5, 11, 13, 0.8, 5.6, "toy_red")
    for y in (12, 13.6, 15.2):  # laces
        k.beam((5.6, y, 10.4), (11.4, y + 0.8, 10.4), 0.3, 0.3, "toy_cream")


def toy_tower(k):
    k.box(3, 13, 3, 13, 0, 56, "terracotta")
    k.windows(3, 13, 3, 13, 0, 56, floor=7, wh=3.4, pitch=2.8, sill=1.8, glass="toy_green", frame="toy_cream")
    k.flat_roof(3, 13, 3, 13, 56, "terracotta", parapet=1.0)
    k.box(3.6, 12.4, 3.6, 12.4, 56, 56.5, "lawn")
    k.bush(6, 6, 1.6)
    k.bush(10, 9, 1.2, "flower")
    k.box(8, 11, 4, 6, 56, 58.5, "toy_cream")


def toy_igloo(k):
    k.blob(8, 8, 0, 5.2, 5.2, 6.4, "toy_ice", subdiv=2)
    k.extrude([(6.6, 0), (9.4, 0), (9.4, 2.6), (8, 3.8), (6.6, 2.6)], "x", 11, 14.2, "toy_ice")
    k.box(14.15, 14.3, 7.1, 8.9, 0, 2.6, "toy_blue")
    for z in (2.2, 4.4):  # block joints
        k.cyl(8, 8, 5.2 * math.sqrt(1 - (z / 6.4) ** 2) + 0.05, z, z + 0.15, "white", n=16)
    k.cyl(13.5, 3.5, 1.2, 0, 0.15, "toy_blue", n=10)  # fishing hole


def toy_tepees(k):
    n0 = len(k.parts)
    for x, y, s, mat in ((6, 6, 1.0, "toy_cream"), (11, 11, 0.9, "toy_yellow")):
        k.cyl(x, y, 3.2 * s, 0, 12 * s, mat, n=9, r_top=0.3)
        k.cyl(x, y, 3.25 * s - 0.6, 3 * s, 3.8 * s, "toy_red", n=9, r_top=3.25 * s - 0.9)
        for i in range(3):
            a = i * math.tau / 3
            k.beam((x, y, 10 * s), (x + 0.9 * math.cos(a), y + 0.9 * math.sin(a), 15 * s), 0.25, 0.25, "toy_brown")
        k.box(x + 2.3 * s, x + 2.9 * s, y - 0.7, y + 0.7, 0, 3.0 * s, "toy_black")
    grow(k, n0, 1.2)


def toy_cola(k):
    k.box(3, 13, 3, 13, 0, 36, "white")
    k.windows(3, 13, 3, 13, 8, 36, floor=6.5, wh=3, pitch=2.6, sill=1.6, glass="toy_blue", frame="white")
    k.shopfront(3, 13, 3, 13, h=6, awning="toy_red")
    k.box(13, 13.4, 5, 11, 6.4, 8.2, "toy_red")  # shop sign
    for i, (x, y) in enumerate((a, b) for a in range(3, 13, 2) for b in range(3, 13, 2)):
        k.box(x, x + 2, y, y + 2, 36, 37.2 + 0.1 * (i % 2), "toy_red" if (x + y) % 4 == 2 else "white")
    k.chimney(5, 5, 36, 41, "toy_red")


def toy_bar(k):
    k.box(3, 13, 3, 11, 0, 30, "toy_cream")
    k.windows(3, 13, 3, 11, 0, 30, floor=7.5, wh=3, pitch=2.6, sill=2, glass="toy_green", frame="toy_brown")
    k.gable(3, 13, 3, 11, 30, 38, "x", "roof_brown", "toy_cream")
    k.box(3, 13, 11, 14, 0, 6, "toy_cream")  # bar annex with a striped roof
    k.shopfront(3, 13, 11, 14, h=5.5, awning=None, faces="y")
    for i, x in enumerate(range(3, 13)):
        k.box(x, x + 1, 10.6, 14.6, 6, 6.5, "toy_green" if i % 2 else "toy_cream")
    k.box(13, 13.4, 11.5, 13.5, 2, 6, "toy_yellow")
    k.chimney(7, 5.5, 34, 40, "toy_red")


def toy_pink(k):
    k.box(3, 13, 3, 13, 0, 58, "toy_pink")
    k.windows(3, 13, 3, 13, 5, 58, floor=5.3, pitch=2.4, ww=1.4, wh=3.2, sill=1.0, glass="toy_purple", frame="white")
    k.box(3.4, 13.15, 3.4, 13.15, 0, 4.4, "toy_red")
    k.hip(3, 13, 3, 13, 58, 66, "roof_slate", over=0.4)


def toy_statue(k):
    n0 = len(k.parts)
    # A toy soldier on a red plinth.
    k.box(5, 11, 5, 11, 0, 8, "rc")
    k.box(4.6, 11.4, 4.6, 11.4, 8, 9, "toy_yellow")
    k.box(11, 11.2, 6.5, 9.5, 2, 5.6, "toy_yellow")
    for y in (7.2, 8.8):  # legs
        k.cyl(8, y, 0.75, 9, 17, "toy_blue", n=8)
    k.cyl(8, 8, 1.8, 17, 26, "toy_red", n=10)
    k.box(9.6, 9.95, 7.5, 8.5, 18, 25, "toy_yellow")  # buttons strip
    k.cyl(8, 8, 1.9, 17, 17.8, "white", n=10)
    for y in (5.8, 10.2):  # arms
        k.cyl(8, y, 0.55, 19, 26, "toy_red", n=6)
        k.blob(8, y, 18.8, 0.6, 0.6, 0.6, "toy_skin")
    k.blob(8, 8, 28.6, 1.6, 1.6, 1.8, "toy_skin")
    k.blob(9.5, 8, 28.3, 0.35, 0.35, 0.35, "toy_red")
    k.cyl(8, 8, 1.7, 29.6, 35, "toy_black", n=10, r_top=1.9)
    k.box(9.5, 9.9, 7.4, 8.6, 30.8, 32.2, "toy_yellow")
    grow(k, n0, 1.3)


def toy_teapot(k):
    n0 = len(k.parts)
    k.blob(8, 8, 6.2, 5.0, 5.0, 5.8, "toy_blue", subdiv=2)
    k.cyl(8, 8, 3.2, 10.6, 12.2, "toy_blue", n=14, r_top=2.6)
    k.blob(8, 8, 12.2, 2.8, 2.8, 1.8, "toy_green", subdiv=2)
    k.blob(8, 8, 14.2, 0.7, 0.7, 0.7, "toy_green")
    k.beam((11.6, 11.6, 6), (13.6, 13.6, 10.2), 1.1, 1.1, "toy_blue")  # spout to the front corner
    k.beam((3.2, 3.2, 9.6), (1.6, 1.6, 6.4), 0.8, 1.6, "toy_blue")  # handle at the back
    k.box(12.0, 13.2, 7, 9, 0, 3.6, "toy_yellow")  # door
    k.box(7, 9, 12.4, 13.4, 5, 7.4, "toy_yellow")  # window
    k.box(7.3, 8.7, 13.3, 13.5, 5.3, 7.1, "glass")
    grow(k, n0, 1.35)


def toy_piggy(k):
    n0 = len(k.parts)
    k.blob(8, 8, 6.2, 4.8, 3.8, 3.8, "toy_pink", subdiv=2)
    for x in (5.4, 10.6):
        for y in (6.2, 9.8):
            k.cyl(x, y, 0.9, 0, 3.2, "toy_pink", n=8)
    k.cyl(12.6, 8, 1.4, 6, 6.1, "toy_pink", n=10)
    k.extrude([(8 + 1.2 * math.cos(a), 5.9 + 1.2 * math.sin(a)) for a in (i * math.tau / 10 for i in range(10))],
              "x", 12.2, 13.4, "flower")  # snout
    for y in (6.0, 10.0):
        k.cyl(11.2, y, 0.9, 9.0, 11.4, "toy_pink", n=4, r_top=0.1)  # ears
        k.blob(12.4, y * 0.9 + 0.8, 7.9, 0.3, 0.3, 0.3, "toy_black")  # eyes
    k.box(6.4, 9.6, 7.7, 8.3, 9.9, 10.15, "toy_black")  # coin slot
    k.box(3.0, 3.4, 7.8, 8.2, 6.0, 7.4, "toy_pink")  # tail
    k.box(9.4, 10.6, 11.7, 11.95, 1.8, 4.8, "toy_yellow")  # door in the side
    grow(k, n0, 1.4)


MODEL_FUNCS = {f.__name__: f for f in (
    arc_brick, arc_cream, arc_cottage, arc_long, arc_thatch, arc_office_a, arc_office_b, arc_office_c,
    arc_house_c, arc_house_d, arc_hall, arc_church, arc_house_e, arc_tall_brick, arc_hotel, arc_shops,
    arc_office_d, arc_twin,
    trop_villa_a, trop_villa_b, trop_villa_c, trop_huts_a, trop_huts_b, trop_huts_c, trop_huts_d,
    trop_flats_tall, trop_mission, trop_villa_d, trop_flats_a, trop_flats_b, trop_flats_c, trop_tower, trop_twin,
    toy_church, toy_pavilion, toy_cabin, toy_dome, toy_house_a, toy_flats, toy_house_b, toy_office, toy_boot,
    toy_tower, toy_igloo, toy_tepees, toy_cola, toy_bar, toy_pink, toy_statue, toy_teapot, toy_piggy)}
