"""Draw the interface icons as flat symbols in the colours of the graphics set.

Each icon is drawn on a 100 x 100 canvas with simple shapes, supersampled and
scaled to the 20 x 20 px toolbar box at 1x (40 and 80 px at 2x and 4x), with a
soft shadow so it reads on the slate toolbar of the modern window style.

Usage: python make_icons.py <out_dir>   writes <out_dir>/z{1,2,4}/<name>.png
"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

BOX = 20  # icon box at 1x
SS = 4  # supersampling

CREAM = (244, 240, 230, 255)
AMBER = (242, 184, 75, 255)
BRICK = (196, 84, 60, 255)
SAGE = (134, 176, 118, 255)
SAGE_LIGHT = (184, 214, 160, 255)
STEEL = (86, 140, 178, 255)
ASPHALT = (66, 72, 84, 255)
WOOD = (176, 134, 92, 255)
RAIL = (214, 218, 224, 255)
SLATE = (52, 60, 72, 255)
SHADOW = (20, 26, 34, 120)
GLYPH_FONT = ("/System/Library/Fonts/Avenir Next.ttc", 8)  # Avenir Next Heavy, for glyphs such as "?"


class Canvas:
    """Drawing in 0..100 icon units on a supersampled RGBA image."""

    def __init__(self, px, units_wide=100):
        self.k = px / 100
        self.units_wide = units_wide
        self.im = Image.new("RGBA", (round(px * units_wide / 100), px), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def p(self, pts):
        return [(x * self.k, y * self.k) for x, y in pts]

    def poly(self, pts, fill):
        self.d.polygon(self.p(pts), fill=fill)

    def rect(self, x0, y0, x1, y1, fill, r=0):
        self.d.rounded_rectangle([x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k], r * self.k, fill=fill)

    def circle(self, cx, cy, r, fill):
        self.d.ellipse([(cx - r) * self.k, (cy - r) * self.k, (cx + r) * self.k, (cy + r) * self.k], fill=fill)

    def line(self, pts, fill, w):
        self.d.line(self.p(pts), fill=fill, width=max(1, round(w * self.k)), joint="curve")

    def ellipse(self, x0, y0, x1, y1, fill=None, outline=None, w=0):
        self.d.ellipse([x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k], fill=fill, outline=outline,
                       width=max(1, round(w * self.k)) if outline else 0)

    def ring(self, cx, cy, r, fill, w):
        self.ellipse(cx - r, cy - r, cx + r, cy + r, outline=fill, w=w)

    def glyph(self, text, cx, cy, size, fill):
        font = ImageFont.truetype(GLYPH_FONT[0], round(size * self.k), index=GLYPH_FONT[1])
        self.d.text((cx * self.k, cy * self.k), text, font=font, fill=fill, anchor="mm")

    def punch(self, draw):
        """Cut a hole: draw() paints the hole on a mask with this canvas' methods."""
        hole = Canvas(self.im.height, self.units_wide)
        draw(hole)
        alpha = ImageChops.subtract(self.im.getchannel("A"), hole.im.getchannel("A"))
        self.im.putalpha(alpha)


def pause(c):
    c.rect(26, 20, 43, 80, CREAM, 5)
    c.rect(57, 20, 74, 80, CREAM, 5)


def fastforward(c):
    c.poly([(14, 22), (50, 50), (14, 78)], CREAM)
    c.poly([(48, 22), (84, 50), (48, 78)], AMBER)


def settings(c):
    teeth, r_out, r_in = 8, 42, 31
    pts = []
    for i in range(teeth * 4):
        a = (i / (teeth * 4)) * 2 * math.pi
        r = r_out if i % 4 in (0, 1) else r_in
        pts.append((50 + r * math.cos(a + math.pi / 16), 50 + r * math.sin(a + math.pi / 16)))
    c.poly(pts, CREAM)
    c.punch(lambda h: h.circle(50, 50, 13, CREAM))


def save(c):
    c.poly([(16, 20), (72, 20), (84, 32), (84, 84), (16, 84)], STEEL)
    c.rect(30, 20, 66, 42, CREAM, 2)
    c.rect(54, 24, 62, 38, STEEL, 1)
    c.rect(26, 54, 74, 84, CREAM, 3)
    c.rect(32, 62, 68, 65, RAIL)
    c.rect(32, 71, 60, 74, RAIL)


def smallmap(c):
    c.poly([(12, 24), (37, 15), (37, 77), (12, 86)], SAGE)
    c.poly([(37, 15), (63, 24), (63, 86), (37, 77)], SAGE_LIGHT)
    c.poly([(63, 24), (88, 15), (88, 77), (63, 86)], SAGE)
    c.line([(20, 70), (32, 52), (48, 58), (60, 40), (78, 34)], STEEL, 5)
    c.circle(78, 34, 7, BRICK)


def town(c):
    c.rect(24, 48, 76, 86, CREAM, 2)
    c.poly([(14, 52), (50, 16), (86, 52)], BRICK)
    c.rect(44, 62, 56, 86, SLATE, 2)
    c.rect(30, 58, 39, 67, STEEL, 1)
    c.rect(61, 58, 70, 67, STEEL, 1)


def buildrail(c):
    for k in range(5):
        t = k / 4
        y = 18 + t * 64
        half = 20 + t * 14
        c.rect(50 - half, y - 3 - t * 2, 50 + half, y + 3 + t * 2, WOOD, 1.5)
    c.poly([(34, 12), (39, 12), (31, 90), (24, 90)], RAIL)
    c.poly([(61, 12), (66, 12), (76, 90), (69, 90)], RAIL)


def buildroad(c):
    c.poly([(38, 12), (62, 12), (88, 90), (12, 90)], ASPHALT)
    for y0, y1 in ((16, 26), (36, 50), (60, 80)):
        w0, w1 = 1.5 + y0 / 40, 1.5 + y1 / 40
        c.poly([(50 - w0, y0), (50 + w0, y0), (50 + w1, y1), (50 - w1, y1)], CREAM)


def subsidies(c):
    c.rect(18, 14, 72, 80, CREAM, 3)
    for y in (26, 36, 46):
        c.rect(26, y, 64, y + 4, RAIL)
    c.poly([(58, 66), (66, 92), (72, 82), (80, 90), (76, 64)], BRICK)
    c.circle(68, 64, 14, AMBER)
    c.circle(68, 64, 7, CREAM)


def messages(c):
    c.rect(14, 18, 86, 82, CREAM, 3)
    c.rect(22, 26, 78, 38, SLATE, 1)
    c.rect(22, 46, 46, 72, STEEL, 1)
    for y in (46, 56, 66):
        c.rect(52, y, 78, y + 5, RAIL)


def league(c):
    c.ring(24, 36, 11, AMBER, 6)
    c.ring(76, 36, 11, AMBER, 6)
    c.poly([(24, 16), (76, 16), (72, 44), (60, 60), (40, 60), (28, 44)], AMBER)
    c.rect(44, 58, 56, 74, AMBER)
    c.rect(30, 74, 70, 86, WOOD, 2)


def music(c):
    c.poly([(36, 20), (80, 10), (80, 22), (36, 32)], CREAM)
    c.rect(36, 22, 43, 74, CREAM)
    c.rect(73, 12, 80, 64, CREAM)
    c.ellipse(16, 64, 44, 84, fill=CREAM)
    c.ellipse(53, 54, 81, 74, fill=CREAM)


def query(c):
    c.circle(50, 50, 40, STEEL)
    c.glyph("?", 50, 50, 62, CREAM)


def buildwater(c):
    c.poly([(16, 56), (84, 56), (72, 72), (28, 72)], BRICK)
    c.rect(47, 14, 52, 58, WOOD)
    c.poly([(54, 16), (78, 50), (54, 50)], CREAM)
    c.poly([(45, 24), (45, 50), (26, 50)], CREAM)
    c.line([(8, 82), (22, 76), (36, 82), (50, 76), (64, 82), (78, 76), (92, 82)], STEEL, 6)


def plane(c, body):
    c.poly([(47, 8), (53, 8), (56, 20), (56, 84), (50, 92), (44, 84), (44, 20)], body)
    c.poly([(44, 38), (8, 58), (8, 64), (44, 54)], body)
    c.poly([(56, 38), (92, 58), (92, 64), (56, 54)], body)
    c.poly([(44, 76), (30, 86), (30, 90), (46, 86)], body)
    c.poly([(56, 76), (70, 86), (70, 90), (54, 86)], body)


def buildair(c):
    plane(c, CREAM)


def trainlist(c):
    c.rect(22, 12, 78, 78, STEEL, 12)
    c.rect(30, 22, 70, 44, CREAM, 4)
    c.circle(34, 62, 5, AMBER)
    c.circle(66, 62, 5, AMBER)
    c.poly([(30, 78), (38, 78), (28, 92), (20, 92)], SLATE)
    c.poly([(62, 78), (70, 78), (80, 92), (72, 92)], SLATE)


def trucklist(c):
    c.rect(8, 22, 60, 70, CREAM, 3)
    c.poly([(62, 34), (80, 34), (92, 50), (92, 70), (62, 70)], AMBER)
    c.poly([(68, 40), (78, 40), (86, 52), (68, 52)], STEEL)
    c.circle(26, 74, 10, SLATE)
    c.circle(76, 74, 10, SLATE)
    c.circle(26, 74, 4, RAIL)
    c.circle(76, 74, 4, RAIL)


def shiplist(c):
    c.poly([(6, 54), (94, 54), (82, 74), (16, 74)], BRICK)
    c.rect(28, 36, 70, 54, CREAM, 2)
    c.rect(52, 16, 64, 38, AMBER, 1)
    for x in (34, 46):
        c.rect(x, 42, x + 7, 48, STEEL)
    c.line([(4, 84), (20, 78), (36, 84), (52, 78), (68, 84), (84, 78), (98, 84)], STEEL, 6)


def planelist(c):
    plane(c, STEEL)


def magnifier(c):
    c.line([(60, 60), (86, 86)], WOOD, 14)
    c.circle(40, 40, 30, CREAM)
    c.circle(40, 40, 22, STEEL)


def zoomin(c):
    magnifier(c)
    c.rect(26, 36, 54, 44, CREAM, 2)
    c.rect(36, 26, 44, 54, CREAM, 2)


def zoomout(c):
    magnifier(c)
    c.rect(26, 36, 54, 44, CREAM, 2)


def finance(c):
    c.rect(10, 24, 74, 62, SAGE, 3)
    c.circle(42, 43, 10, SAGE_LIGHT)
    for y in (78, 68, 58):
        c.ellipse(46, y - 8, 90, y + 8, fill=(196, 140, 48, 255))
        c.ellipse(46, y - 12, 90, y + 4, fill=AMBER)


def industry(c):
    c.rect(64, 10, 76, 50, BRICK)
    c.poly([(10, 48), (30, 34), (30, 48), (50, 34), (50, 48), (70, 34), (90, 48), (90, 86), (10, 86)], SLATE)
    for x in (18, 40, 62):
        c.rect(x, 60, x + 14, 72, AMBER, 1)
    c.circle(76, 8, 6, CREAM)
    c.circle(86, 4, 4, CREAM)


def planttrees(c):
    c.rect(46, 64, 54, 90, WOOD)
    c.poly([(50, 8), (78, 40), (70, 70), (30, 70), (22, 40)], SAGE)
    c.poly([(50, 8), (78, 40), (50, 48)], SAGE_LIGHT)


def person(c, cx, body, scale=1.0):
    c.circle(cx, 34 * scale + (1 - scale) * 60, 16 * scale, CREAM)
    top = 56 * scale + (1 - scale) * 70
    c.rect(cx - 30 * scale, top, cx + 30 * scale, 90, body, 14 * scale)


def company(c):
    person(c, 50, STEEL)
    c.poly([(46, 60), (54, 60), (56, 82), (50, 88), (44, 82)], BRICK)


def graphs(c):
    c.rect(12, 12, 18, 86, CREAM)
    c.rect(12, 80, 88, 86, CREAM)
    c.line([(22, 68), (40, 50), (56, 58), (84, 24)], AMBER, 7)
    c.line([(22, 74), (42, 66), (60, 70), (84, 52)], SAGE_LIGHT, 6)


def companylist(c):
    person(c, 32, SAGE, 0.8)
    person(c, 64, STEEL)


def sign(c):
    c.rect(46, 30, 54, 92, WOOD)
    c.rect(12, 14, 88, 46, CREAM, 4)
    c.rect(20, 24, 70, 29, SLATE)
    c.rect(20, 33, 56, 37, RAIL)


def landscaping(c):
    c.poly([(4, 84), (34, 40), (52, 58), (66, 44), (96, 84)], SAGE)
    c.poly([(34, 40), (44, 54), (34, 84), (24, 84)], SAGE_LIGHT)
    c.line([(60, 14), (82, 52)], WOOD, 7)
    c.poly([(76, 46), (92, 38), (98, 58), (86, 66)], RAIL)


def transmitter(c):
    # Radio waves first, cut to arcs above the mast, then the mast on top.
    c.ring(50, 28, 34, CREAM, 6)
    c.ring(50, 28, 20, CREAM, 6)
    c.punch(lambda h: h.poly([(50, 28), (0, 100), (0, 46), (100, 46), (100, 100)], CREAM))
    c.poly([(46, 28), (54, 28), (70, 92), (30, 92)], SLATE)
    c.poly([(48, 46), (52, 46), (60, 84), (40, 84)], RAIL)
    c.circle(50, 28, 8, BRICK)


def switchtoolbar(c):
    for x in (24, 50, 76):
        c.circle(x, 50, 10, CREAM)


def storybook(c):
    c.poly([(8, 22), (48, 30), (48, 86), (8, 78)], CREAM)
    c.poly([(92, 22), (52, 30), (52, 86), (92, 78)], CREAM)
    c.poly([(6, 78), (48, 86), (52, 86), (94, 78), (94, 84), (52, 92), (48, 92), (6, 84)], STEEL)
    for y in (40, 50, 60):
        c.line([(16, y - 6), (40, y)], RAIL, 3)
        c.line([(60, y), (84, y - 6)], RAIL, 3)


def goal(c):
    c.circle(50, 50, 40, CREAM)
    c.circle(50, 50, 30, BRICK)
    c.circle(50, 50, 20, CREAM)
    c.circle(50, 50, 10, BRICK)


def buildtrams(c):
    c.line([(50, 4), (50, 16)], SLATE, 4)
    c.line([(36, 4), (64, 4)], SLATE, 4)
    c.rect(20, 16, 80, 80, SAGE, 10)
    c.rect(28, 26, 72, 48, CREAM, 4)
    c.circle(34, 64, 5, AMBER)
    c.circle(66, 64, 5, AMBER)
    c.rect(30, 80, 70, 88, SLATE, 2)


def contours(c):
    c.ellipse(6, 14, 94, 86, fill=SAGE)
    c.ellipse(18, 22, 82, 74, outline=SAGE_LIGHT, w=5)
    c.ellipse(30, 32, 70, 64, outline=SAGE_LIGHT, w=5)
    c.ellipse(42, 42, 58, 54, fill=CREAM)


def vehicles(c):
    c.rect(8, 16, 56, 56, STEEL, 8)
    c.rect(14, 22, 50, 36, CREAM, 3)
    c.circle(18, 48, 3, AMBER)
    c.circle(46, 48, 3, AMBER)
    c.rect(40, 50, 76, 80, CREAM, 3)
    c.poly([(78, 58), (88, 58), (96, 68), (96, 80), (78, 80)], AMBER)
    c.circle(52, 82, 7, SLATE)
    c.circle(86, 82, 7, SLATE)


def routes(c):
    c.line([(20, 78), (34, 58), (56, 62), (70, 40), (80, 22)], CREAM, 6)
    c.circle(20, 78, 11, BRICK)
    c.circle(80, 22, 11, AMBER)
    c.circle(20, 78, 4, CREAM)
    c.circle(80, 22, 4, CREAM)


# Build menus. Tracks and roads follow the map's isometric axes: X runs "/" and
# Y runs "\\" at 2:1, NS is vertical and EW horizontal on screen.
WATER = (92, 150, 196, 255)
STONE = (168, 160, 150, 255)
SAND = (226, 200, 140, 255)
RED = (214, 64, 56, 255)
GREEN = (96, 196, 110, 255)
ISO_X = (2 / math.sqrt(5), -1 / math.sqrt(5))  # screen direction of the X axis, towards NE
ISO_Y = (2 / math.sqrt(5), 1 / math.sqrt(5))  # screen direction of the Y axis, towards SE
TRACK_DIRS = {  # direction of travel, direction across the track
    "ns": ((0, 1), (1, 0)),
    "x": (ISO_X, ISO_Y),
    "ew": ((1, 0), (0, 1)),
    "y": (ISO_Y, ISO_X),
}


def track(c, cx, cy, d, length=84, gauge=13, sleepers=6):
    (dx, dy), (sx, sy) = TRACK_DIRS[d]
    for k in range(sleepers):
        t = (k / (sleepers - 1) - 0.5) * length * 0.9
        x, y = cx + dx * t, cy + dy * t
        c.line([(x - sx * gauge * 1.4, y - sy * gauge * 1.4), (x + sx * gauge * 1.4, y + sy * gauge * 1.4)], WOOD, 7)
    for side in (-1, 1):
        ox, oy = sx * gauge * side, sy * gauge * side
        c.line([(cx - dx * length / 2 + ox, cy - dy * length / 2 + oy),
                (cx + dx * length / 2 + ox, cy + dy * length / 2 + oy)], RAIL, 5)


def wire(c, cx, cy, d, length=84):
    (dx, dy), (sx, sy) = TRACK_DIRS[d]
    lift = 30
    c.line([(cx - dx * length / 2, cy - dy * length / 2 - lift), (cx + dx * length / 2, cy + dy * length / 2 - lift)],
           SLATE, 3)
    mx, my = cx - dx * length * 0.3 + sx * 20, cy - dy * length * 0.3 + sy * 20
    c.line([(mx, my), (mx, my - lift - 4)], SLATE, 5)
    c.line([(mx, my - lift), (cx - dx * length * 0.3, cy - dy * length * 0.3 - lift)], SLATE, 3)


def road(c, cx, cy, d, length=88, half=20, colour=ASPHALT, dashes=True):
    (dx, dy), (sx, sy) = TRACK_DIRS[d]
    e = [(cx - dx * length / 2, cy - dy * length / 2), (cx + dx * length / 2, cy + dy * length / 2)]
    c.poly([(e[0][0] - sx * half, e[0][1] - sy * half), (e[1][0] - sx * half, e[1][1] - sy * half),
            (e[1][0] + sx * half, e[1][1] + sy * half), (e[0][0] + sx * half, e[0][1] + sy * half)], colour)
    if dashes:
        for k in range(3):
            t0, t1 = -0.4 + k * 0.3, -0.27 + k * 0.3
            c.line([(cx + dx * length * t0, cy + dy * length * t0), (cx + dx * length * t1, cy + dy * length * t1)],
                   CREAM, 4)


def tramtrack(c, cx, cy, d):
    road(c, cx, cy, d, half=20, colour=STONE, dashes=False)
    (dx, dy), (sx, sy) = TRACK_DIRS[d]
    for side in (-1, 1):
        ox, oy = sx * 9 * side, sy * 9 * side
        c.line([(cx - dx * 44 + ox, cy - dy * 44 + oy), (cx + dx * 44 + ox, cy + dy * 44 + oy)], SLATE, 4)


def sparkle(c, cx, cy, r=13):
    c.poly([(cx, cy - r), (cx + r * 0.3, cy - r * 0.3), (cx + r, cy), (cx + r * 0.3, cy + r * 0.3),
            (cx, cy + r), (cx - r * 0.3, cy + r * 0.3), (cx - r, cy), (cx - r * 0.3, cy - r * 0.3)], AMBER)


def cycle(c, cx, cy, r=15):
    """Two curved arrows: convert."""
    c.ring(cx, cy, r, AMBER, 6)
    c.punch(lambda h: (h.poly([(cx - r - 8, cy - 3), (cx + r + 8, cy - 3), (cx + r + 8, cy + 3), (cx - r - 8, cy + 3)],
                              CREAM)))
    c.poly([(cx + r - 9, cy - 4), (cx + r + 9, cy - 4), (cx + r, cy + 8)], AMBER)
    c.poly([(cx - r - 9, cy + 4), (cx - r + 9, cy + 4), (cx - r, cy - 8)], AMBER)


def shed(c, door=SLATE):
    c.rect(18, 40, 82, 88, CREAM, 2)
    c.poly([(10, 44), (50, 12), (90, 44)], BRICK)
    c.rect(32, 52, 68, 88, door, 2)


def portal(c):
    c.poly([(2, 92), (24, 30), (50, 14), (76, 30), (98, 92)], SAGE)
    c.poly([(24, 30), (50, 14), (52, 40), (30, 50)], SAGE_LIGHT)
    c.rect(26, 50, 74, 92, STONE, 24)
    c.rect(36, 60, 64, 92, SLATE, 14)


def rail_ns(c):
    track(c, 50, 50, "ns")


def rail_x(c):
    track(c, 50, 50, "x")


def rail_ew(c):
    track(c, 50, 50, "ew")


def rail_y(c):
    track(c, 50, 50, "y")


def autorail(c):
    track(c, 46, 54, "x", length=74)
    sparkle(c, 76, 22)


def depot_rail(c):
    shed(c)
    c.line([(42, 66), (36, 92)], RAIL, 4)
    c.line([(58, 66), (64, 92)], RAIL, 4)


def tunnel_rail(c):
    portal(c)
    c.line([(44, 70), (38, 92)], RAIL, 4)
    c.line([(56, 70), (62, 92)], RAIL, 4)


def convert_rail(c):
    track(c, 40, 60, "x", length=64)
    cycle(c, 72, 30)


def elrail(d):
    def draw(c):
        track(c, 50, 58, d, length=80)
        wire(c, 50, 58, d, length=80)
    return draw


def autoelrail(c):
    track(c, 46, 58, "x", length=74)
    wire(c, 46, 58, "x", length=74)
    sparkle(c, 80, 20, 11)


def depot_elrail(c):
    depot_rail(c)
    c.line([(36, 34), (64, 34)], SLATE, 3)


def tunnel_elrail(c):
    tunnel_rail(c)
    c.line([(50, 62), (50, 72)], SLATE, 3)


def convert_elrail(c):
    track(c, 40, 62, "x", length=64)
    wire(c, 40, 62, "x", length=64)
    cycle(c, 74, 26, 13)


def railstation(c):
    # 200 units wide
    track(c, 100, 80, "ew", length=190, gauge=8, sleepers=10)
    c.rect(20, 50, 180, 66, STONE, 2)
    c.rect(40, 18, 160, 26, STEEL, 2)
    for x in (52, 100, 148):
        c.rect(x - 3, 24, x + 3, 52, SLATE)
    c.rect(150, 26, 196, 52, CREAM, 2)
    c.poly([(144, 30), (173, 10), (200, 30)], BRICK)


def signals(c):
    c.rect(46, 44, 54, 92, SLATE)
    c.rect(34, 6, 66, 52, SLATE, 8)
    c.circle(50, 18, 8, RED)
    c.circle(50, 38, 8, GREEN)


def signal_convert(c):
    c.rect(26, 44, 32, 92, SLATE)
    c.rect(16, 10, 42, 48, SLATE, 7)
    c.circle(29, 20, 6, RED)
    c.circle(29, 37, 6, GREEN)
    cycle(c, 72, 58, 15)


def bridge(c):
    # 200 units wide
    c.rect(0, 80, 200, 100, WATER)
    c.ellipse(30, 20, 170, 150, outline=STEEL, w=8)
    c.punch(lambda h: h.rect(0, 64, 200, 100, CREAM))
    c.rect(0, 80, 200, 100, WATER)
    c.rect(0, 56, 200, 66, ASPHALT)
    for x in (58, 80, 100, 120, 142):
        c.rect(x - 2, 30 if x == 100 else 36, x + 2, 58, STEEL)
    c.rect(28, 56, 40, 96, STONE)
    c.rect(160, 56, 172, 96, STONE)


def waypoint(c):
    track(c, 50, 62, "ew", length=88)
    c.rect(47, 12, 53, 60, SLATE)
    c.poly([(50, 8), (66, 20), (50, 32), (34, 20)], AMBER)


def dynamite(c):
    for k, x in enumerate((26, 44, 62)):
        c.rect(x, 40, x + 16, 90, RED, 4)
        c.rect(x, 56, x + 16, 62, CREAM)
    c.line([(52, 40), (58, 26), (70, 20)], SLATE, 4)
    sparkle(c, 76, 16, 12)


def remove(c):
    c.rect(14, 64, 74, 86, SLATE, 10)
    for x in (24, 44, 64):
        c.circle(x, 75, 5, STONE)
    c.rect(22, 38, 64, 64, AMBER, 3)
    c.rect(40, 22, 62, 40, AMBER, 2)
    c.rect(44, 26, 58, 36, STEEL, 1)
    c.poly([(74, 52), (92, 46), (94, 86), (76, 86)], STONE)


def road_x(c):
    road(c, 50, 50, "x")


def road_y(c):
    road(c, 50, 50, "y")


def autoroad(c):
    road(c, 46, 56, "x", length=76)
    sparkle(c, 78, 20)


def road_depot(c):
    c.rect(14, 34, 86, 88, CREAM, 3)
    c.rect(8, 26, 92, 38, BRICK, 2)
    c.rect(26, 48, 74, 88, STONE, 2)
    for y in (56, 66, 76):
        c.rect(28, y, 72, y + 3, SLATE)


def bus_station(c):
    c.rect(18, 10, 82, 80, AMBER, 12)
    c.rect(26, 20, 74, 46, STEEL, 4)
    c.circle(32, 64, 5, CREAM)
    c.circle(68, 64, 5, CREAM)
    c.rect(26, 80, 38, 90, SLATE, 2)
    c.rect(62, 80, 74, 90, SLATE, 2)


def truck_bay(c):
    trucklist(c)


def one_way(c):
    road(c, 50, 50, "x", dashes=False)
    (dx, dy), (sx, sy) = TRACK_DIRS["x"]
    c.line([(50 - dx * 24, 50 - dy * 24), (50 + dx * 14, 50 + dy * 14)], CREAM, 7)
    tip = (50 + dx * 28, 50 + dy * 28)
    c.poly([tip, (50 + dx * 10 + sx * 12, 50 + dy * 10 + sy * 12), (50 + dx * 10 - sx * 12, 50 + dy * 10 - sy * 12)],
           AMBER)


def road_tunnel(c):
    portal(c)
    c.poly([(42, 64), (58, 64), (68, 92), (32, 92)], ASPHALT)


def convert_road(c):
    road(c, 40, 60, "x", length=64)
    cycle(c, 72, 30)


def tram_x(c):
    tramtrack(c, 50, 50, "x")


def tram_y(c):
    tramtrack(c, 50, 50, "y")


def autotram(c):
    tramtrack(c, 46, 56, "x")
    sparkle(c, 80, 18)


def canal(c):
    road(c, 50, 50, "x", half=26, colour=STONE, dashes=False)
    road(c, 50, 50, "x", half=18, colour=WATER, dashes=False)




def lock(c):
    road(c, 50, 50, "x", half=26, colour=STONE, dashes=False)
    road(c, 50, 50, "x", half=18, colour=WATER, dashes=False)
    (dx, dy), (sx, sy) = TRACK_DIRS["x"]
    for t in (-16, 16):
        x, y = 50 + dx * t, 50 + dy * t
        c.line([(x - sx * 24, y - sy * 24), (x + sx * 24, y + sy * 24)], WOOD, 8)
def river(c):
    c.line([(4, 84), (26, 66), (46, 74), (64, 46), (80, 40), (96, 16)], WATER, 16)
    c.line([(22, 70), (32, 64)], CREAM, 3)
    c.line([(66, 48), (74, 44)], CREAM, 3)


def aqueduct(c):
    c.rect(4, 30, 96, 46, STONE)
    c.rect(4, 22, 96, 32, WATER)
    for x in (4, 50):
        c.rect(x, 46, x + 46, 92, STONE)
    c.punch(lambda h: (h.ellipse(12, 56, 42, 120, fill=CREAM), h.ellipse(58, 56, 88, 120, fill=CREAM)))


def buoy(c):
    c.rect(4, 74, 96, 92, WATER, 4)
    c.poly([(30, 76), (70, 76), (60, 30), (40, 30)], RED)
    c.poly([(36, 56), (64, 56), (62, 46), (38, 46)], CREAM)
    c.rect(46, 12, 54, 30, SLATE)
    c.circle(50, 12, 7, AMBER)


def ship_depot(c):
    c.rect(4, 70, 96, 92, WATER, 4)
    c.rect(18, 36, 82, 74, CREAM, 2)
    c.poly([(10, 40), (50, 10), (90, 40)], BRICK)
    c.rect(32, 48, 68, 74, WATER, 2)


def ship_dock(c):
    c.rect(4, 72, 96, 92, WATER, 4)
    c.rect(4, 58, 60, 72, STONE)
    c.rect(10, 16, 18, 60, AMBER)
    c.line([(14, 18), (80, 30)], AMBER, 6)
    c.line([(70, 30), (70, 52)], SLATE, 2)
    c.rect(62, 52, 80, 62, BRICK, 1)


def airport(c):
    # 200 units wide
    c.rect(4, 70, 196, 90, ASPHALT, 3)
    for x in range(20, 190, 34):
        c.rect(x, 78, x + 18, 82, CREAM)
    c.rect(154, 24, 170, 70, CREAM)
    c.rect(146, 12, 178, 28, STEEL, 3)
    c.d.polygon([(px * c.k, py * c.k) for px, py in
                 [(30, 46), (110, 46), (124, 40), (130, 46), (130, 52), (110, 56), (30, 56)]], fill=CREAM)
    c.poly([(60, 50), (84, 22), (94, 22), (82, 50)], CREAM)
    c.poly([(60, 52), (84, 66), (92, 66), (82, 52)], CREAM)
    c.poly([(30, 46), (22, 30), (30, 30), (40, 46)], BRICK)


def terraform(up):
    def draw(c):
        c.poly([(2, 92), (40, 46), (60, 60), (98, 92)], SAGE)
        c.poly([(40, 46), (50, 92), (2, 92)], SAGE_LIGHT)
        x, top, bottom = 70, 8, 48
        c.rect(x - 5, top + 10 if up else top, x + 5, bottom - 10 if not up else bottom, AMBER)
        if up:
            c.poly([(x - 15, top + 16), (x, top - 2), (x + 15, top + 16)], AMBER)
        else:
            c.poly([(x - 15, bottom - 16), (x, bottom + 2), (x + 15, bottom - 16)], AMBER)
    return draw


def level_land(c):
    c.poly([(2, 66), (50, 42), (98, 66), (50, 90)], SAGE)
    c.poly([(2, 66), (50, 90), (50, 96), (2, 72)], SAGE_LIGHT)
    c.rect(18, 14, 82, 30, AMBER, 4)
    c.rect(44, 18, 56, 26, CREAM, 3)


def buy_land(c):
    c.poly([(2, 70), (50, 46), (98, 70), (50, 94)], SAGE)
    c.rect(46, 12, 52, 72, WOOD)
    c.poly([(52, 12), (84, 22), (52, 32)], BRICK)


def rocks(c):
    c.poly([(8, 86), (20, 54), (44, 46), (56, 70), (52, 86)], STONE)
    c.poly([(20, 54), (44, 46), (34, 64)], (200, 194, 186, 255))
    c.poly([(46, 86), (60, 40), (84, 30), (96, 66), (92, 86)], (140, 134, 126, 255))
    c.poly([(60, 40), (84, 30), (74, 54)], STONE)


def desert(c):
    c.poly([(2, 86), (30, 52), (58, 70), (78, 46), (98, 86)], SAND)
    c.poly([(30, 52), (40, 86), (2, 86)], (240, 222, 176, 255))
    c.circle(76, 20, 12, AMBER)


ICONS = {
    "pause": pause,
    "fastforward": fastforward,
    "settings": settings,
    "save": save,
    "smallmap": smallmap,
    "town": town,
    "buildrail": buildrail,
    "buildroad": buildroad,
    "subsidies": subsidies,
    "messages": messages,
    "league": league,
    "music": music,
    "query": query,
    "buildwater": buildwater,
    "buildair": buildair,
    "trainlist": trainlist,
    "trucklist": trucklist,
    "shiplist": shiplist,
    "planelist": planelist,
    "zoomin": zoomin,
    "zoomout": zoomout,
    "finance": finance,
    "industry": industry,
    "planttrees": planttrees,
    "company": company,
    "graphs": graphs,
    "companylist": companylist,
    "sign": sign,
    "landscaping": landscaping,
    "transmitter": transmitter,
    "switchtoolbar": switchtoolbar,
    "storybook": storybook,
    "goal": goal,
    "buildtrams": buildtrams,
    "contours": contours,
    "vehicles": vehicles,
    "routes": routes,
    "rail_ns": rail_ns,
    "rail_x": rail_x,
    "rail_ew": rail_ew,
    "rail_y": rail_y,
    "autorail": autorail,
    "depot_rail": depot_rail,
    "tunnel_rail": tunnel_rail,
    "convert_rail": convert_rail,
    "elrail_ns": elrail("ns"),
    "elrail_x": elrail("x"),
    "elrail_ew": elrail("ew"),
    "elrail_y": elrail("y"),
    "autoelrail": autoelrail,
    "depot_elrail": depot_elrail,
    "tunnel_elrail": tunnel_elrail,
    "convert_elrail": convert_elrail,
    "railstation": railstation,
    "signals": signals,
    "signal_convert": signal_convert,
    "bridge": bridge,
    "waypoint": waypoint,
    "dynamite": dynamite,
    "remove": remove,
    "road_x": road_x,
    "road_y": road_y,
    "autoroad": autoroad,
    "road_depot": road_depot,
    "bus_station": bus_station,
    "truck_bay": truck_bay,
    "one_way": one_way,
    "road_tunnel": road_tunnel,
    "convert_road": convert_road,
    "tram_x": tram_x,
    "tram_y": tram_y,
    "autotram": autotram,
    "canal": canal,
    "lock": lock,
    "river": river,
    "aqueduct": aqueduct,
    "buoy": buoy,
    "ship_depot": ship_depot,
    "ship_dock": ship_dock,
    "airport": airport,
    "terraform_up": terraform(True),
    "terraform_down": terraform(False),
    "level_land": level_land,
    "buy_land": buy_land,
    "rocks": rocks,
    "desert": desert,
}
WIDE = {"railstation": 40, "bridge": 40, "airport": 40}  # 1x width of the wide build menu buttons


def render(draw, zoom, width=BOX):
    """Draw at 1x box size BOX high and width wide (100 units = BOX px)."""
    px, pw = BOX * zoom, width * zoom
    c = Canvas(px * SS, 100 * width / BOX)
    draw(c)
    glyph = c.im.resize((pw, px), Image.LANCZOS)
    shadow = Image.new("RGBA", (pw, px), SHADOW[:3] + (0,))
    shadow.putalpha(glyph.getchannel("A").point(lambda a: a * SHADOW[3] // 255))
    shadow = shadow.transform(shadow.size, Image.AFFINE, (1, 0, -0.5 * zoom, 0, 1, -zoom))
    shadow = shadow.filter(ImageFilter.GaussianBlur(0.6 * zoom))
    return Image.alpha_composite(shadow, glyph)


def main():
    out = sys.argv[1]
    for zoom in (1, 2, 4):
        d = os.path.join(out, f"z{zoom}")
        os.makedirs(d, exist_ok=True)
        for name, draw in ICONS.items():
            render(draw, zoom, WIDE.get(name, BOX)).save(os.path.join(d, f"{name}.png"))


if __name__ == "__main__":
    main()
