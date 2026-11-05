"""Draw the remaining interface sprites in the style of the main toolbar icons.

Covers the construction toolbars (rail, road, tram, water, air, landscaping)
and their cursors, the vehicle, depot and group buttons, the window widget
glyphs and a few small status icons. make_icons.py draws the main toolbar.

Every sprite keeps the size and offset of the OpenGFX original, so layouts
and cursor hotspots do not move. Drawing units are 5 per pixel at 1x, the
same as the 100-unit toolbar icons in their 20 px box, so strokes match.
Sizes in SPRITES are the OpenGFX ones at 1x: (w, h, x offset, y offset).

Usage: python make_gui_icons.py <out_dir>   writes <out_dir>/z{1,2,4}/<key>.png
"""
import math
import os
import sys
from contextlib import contextmanager

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import make_icons as mi
from make_icons import AMBER, ASPHALT, BRICK, CREAM, RAIL, SAGE, SAGE_LIGHT, SLATE, STEEL, WOOD

U = 5  # drawing units per pixel at 1x
SS = 4  # supersampling
INK = (34, 40, 50, 255)  # window glyphs: arrows, pins, boxes
SHADOW = mi.SHADOW
WATER = (96, 160, 196, 255)
WATER_DEEP = (64, 124, 166, 255)
GREEN = (98, 184, 98, 255)
STONE = (168, 160, 150, 255)
ROCK = (132, 122, 112, 255)
CONCRETE = (196, 198, 200, 255)


class Canvas:
    """Drawing in units (5 per pixel at 1x) on a supersampled RGBA image, with nested transforms."""

    def __init__(self, w, h, zoom):
        self.k = zoom * SS / U
        self.size = (w * zoom * SS, h * zoom * SS)
        self.im = Image.new("RGBA", self.size, (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.t = [(0.0, 0.0, 1.0)]
        self.W, self.H = w * U, h * U

    @contextmanager
    def at(self, ox, oy, s=1.0):
        """Draw in a sub-frame: (x, y) -> (ox + s x, oy + s y) in the current frame."""
        tx, ty, ts = self.t[-1]
        self.t.append((tx + ox * ts, ty + oy * ts, ts * s))
        try:
            yield
        finally:
            self.t.pop()

    def xy(self, x, y):
        tx, ty, ts = self.t[-1]
        return ((tx + x * ts) * self.k, (ty + y * ts) * self.k)

    def len(self, v):
        return v * self.t[-1][2] * self.k

    def p(self, pts):
        return [self.xy(x, y) for x, y in pts]

    def poly(self, pts, fill):
        self.d.polygon(self.p(pts), fill=fill)

    def rect(self, x0, y0, x1, y1, fill, r=0):
        a, b = self.xy(x0, y0), self.xy(x1, y1)
        self.d.rounded_rectangle([a, b], self.len(r), fill=fill)

    def ellipse(self, x0, y0, x1, y1, fill=None, outline=None, w=0):
        a, b = self.xy(x0, y0), self.xy(x1, y1)
        self.d.ellipse([a, b], fill=fill, outline=outline, width=max(1, round(self.len(w))) if outline else 0)

    def circle(self, cx, cy, r, fill):
        self.ellipse(cx - r, cy - r, cx + r, cy + r, fill=fill)

    def ring(self, cx, cy, r, fill, w):
        self.ellipse(cx - r, cy - r, cx + r, cy + r, outline=fill, w=w)

    def line(self, pts, fill, w):
        self.d.line(self.p(pts), fill=fill, width=max(1, round(self.len(w))), joint="curve")

    def arc(self, cx, cy, r, a0, a1, fill, w):
        a, b = self.xy(cx - r, cy - r), self.xy(cx + r, cy + r)
        self.d.arc([a, b], a0, a1, fill=fill, width=max(1, round(self.len(w))))

    def glyph(self, text, cx, cy, size, fill):
        font = ImageFont.truetype(mi.GLYPH_FONT[0], max(1, round(self.len(size))), index=mi.GLYPH_FONT[1])
        self.d.text(self.xy(cx, cy), text, font=font, fill=fill, anchor="mm")

    def punch(self, draw):
        """Cut a hole: draw() paints the hole on a mask canvas with the same transform."""
        hole = Canvas.__new__(Canvas)
        hole.__dict__.update(self.__dict__)
        hole.im = Image.new("RGBA", self.size, (0, 0, 0, 0))
        hole.d = ImageDraw.Draw(hole.im)
        hole.t = list(self.t)
        draw(hole)
        self.im.putalpha(ImageChops.subtract(self.im.getchannel("A"), hole.im.getchannel("A")))


# ---------------------------------------------------------------- geometry

def unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1
    return dx / n, dy / n, n


def band(c, a, b, w, fill):
    """A straight strip of width w from a to b."""
    ux, uy, _ = unit(a, b)
    nx, ny = -uy * w / 2, ux * w / 2
    c.poly([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)], fill)


def offset(a, b, d):
    ux, uy, _ = unit(a, b)
    return (a[0] - uy * d, a[1] + ux * d), (b[0] - uy * d, b[1] + ux * d)


def track(c, a, b, kind, s=1.0):
    """A piece of track or road from a to b; s scales the cross-section."""
    ux, uy, n = unit(a, b)
    if kind in ("rail", "elrail"):
        steps = max(2, int(n / (13 * s)))
        for i in range(steps + 1):
            t = (i + 0.5) / (steps + 1) * n
            cx, cy = a[0] + ux * t, a[1] + uy * t
            band(c, (cx - ux * 2.6 * s, cy - uy * 2.6 * s), (cx + ux * 2.6 * s, cy + uy * 2.6 * s), 27 * s, WOOD)
        for d in (-8 * s, 8 * s):
            band(c, *offset(a, b, d), 5 * s, RAIL)
    elif kind == "mono":
        band(c, a, b, 18 * s, SLATE)
        band(c, *offset(a, b, -2 * s), 12 * s, STEEL)
        band(c, *offset(a, b, -5 * s), 4 * s, RAIL)
    elif kind == "maglev":
        band(c, a, b, 28 * s, SLATE)
        band(c, *offset(a, b, -2 * s), 20 * s, (96, 104, 118, 255))
        band(c, a, b, 7 * s, STEEL)
    elif kind == "road":
        band(c, a, b, 32 * s, ASPHALT)
        steps = max(1, int(n / (22 * s)))
        for i in range(steps):
            t0, t1 = (i + 0.3) / steps * n, (i + 0.7) / steps * n
            band(c, (a[0] + ux * t0, a[1] + uy * t0), (a[0] + ux * t1, a[1] + uy * t1), 4 * s, CREAM)
    elif kind == "tram":
        band(c, a, b, 30 * s, ASPHALT)
        for d in (-7 * s, 7 * s):
            band(c, *offset(a, b, d), 4.5 * s, RAIL)


def iso_tile(c, cx, cy, hw, fill, depth=0, side=None):
    """An isometric tile (diamond) centred on (cx, cy), half width hw, optionally with a thickness."""
    hh = hw / 2
    if depth:
        c.poly([(cx - hw, cy), (cx, cy + hh), (cx + hw, cy), (cx + hw, cy + depth), (cx, cy + hh + depth),
                (cx - hw, cy + depth)], side or SLATE)
    c.poly([(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)], fill)


def iso_box(c, cx, cy, hw, h, top, left, right):
    """An isometric block standing on the diamond at (cx, cy) with height h."""
    hh = hw / 2
    c.poly([(cx - hw, cy - h), (cx, cy + hh - h), (cx, cy + hh), (cx - hw, cy)], left)
    c.poly([(cx, cy + hh - h), (cx + hw, cy - h), (cx + hw, cy), (cx, cy + hh)], right)
    c.poly([(cx, cy - hh - h), (cx + hw, cy - h), (cx, cy + hh - h), (cx - hw, cy - h)], top)


def shade(col, f):
    return tuple(min(255, round(v * f)) for v in col[:3]) + (col[3],)


# ---------------------------------------------------------------- badges and small symbols

def badge_x(c, cx, cy, r=13, col=BRICK):
    c.circle(cx, cy, r, col)
    d = r * 0.45
    c.line([(cx - d, cy - d), (cx + d, cy + d)], CREAM, r * 0.32)
    c.line([(cx - d, cy + d), (cx + d, cy - d)], CREAM, r * 0.32)


def badge_plus(c, cx, cy, r=13, col=AMBER):
    c.circle(cx, cy, r, col)
    d = r * 0.55
    c.line([(cx - d, cy), (cx + d, cy)], CREAM, r * 0.32)
    c.line([(cx, cy - d), (cx, cy + d)], CREAM, r * 0.32)


def cycle(c, cx, cy, r, col, w):
    """A circular arrow, clockwise, open at the top left."""
    c.arc(cx, cy, r, 200, 500, col, w)
    a = math.radians(140)
    tx, ty = cx + r * math.cos(a), cy + r * math.sin(a)
    s = w * 1.3
    c.poly([(tx - s, ty - s * 0.2), (tx + s, ty - s * 0.2), (tx, ty + s * 1.1)], col)


def badge_cycle(c, cx, cy, r=13, col=AMBER):
    c.circle(cx, cy, r, col)
    cycle(c, cx, cy, r * 0.5, CREAM, r * 0.22)


def badge_pencil(c, cx, cy, r=13, col=STEEL):
    c.circle(cx, cy, r, col)
    d = r * 0.5
    c.line([(cx - d, cy + d), (cx + d, cy - d)], CREAM, r * 0.32)
    c.poly([(cx - d - 2, cy + d + 2), (cx - d + 2.5, cy + d - 1), (cx - d + 1, cy + d + 2.5)], CREAM)


def bulldozer(c):
    c.poly([(8, 64), (14, 36), (30, 36), (30, 22), (62, 22), (66, 44), (74, 44), (74, 64)], AMBER)
    c.rect(36, 28, 56, 42, STEEL, 2)
    c.rect(10, 62, 76, 84, SLATE, 10)
    for x in (20, 43, 66):
        c.circle(x, 73, 6, RAIL)
    c.poly([(76, 40), (88, 40), (96, 84), (80, 84)], CREAM)


def bomb(c):
    c.circle(44, 60, 30, SLATE)
    c.circle(34, 50, 8, (96, 104, 118, 255))
    c.rect(52, 24, 66, 36, SLATE, 2)
    c.line([(60, 26), (68, 14), (80, 10)], WOOD, 4)
    for a in range(0, 360, 45):
        r = math.radians(a)
        c.line([(84, 8), (84 + 10 * math.cos(r), 8 + 10 * math.sin(r))], AMBER, 3)
    c.circle(84, 8, 4, CREAM)


def signal_post(c, x, y, h, lit, semaphore=False, head=None):
    """A signal at (x, y) bottom, height h; lit is 'red' or 'green'."""
    c.rect(x - 2.5, y - h * 0.55, x + 2.5, y, SLATE)
    if semaphore:
        c.rect(x - 2.5, y - h, x + 2.5, y - h * 0.5, SLATE)
        up = lit == "green"
        arm = [(x, y - h * 0.86), (x + h * 0.42, y - h * (1.05 if up else 0.86))]
        c.line(arm, BRICK, h * 0.12)
        c.circle(x, y - h * 0.86, h * 0.07, CREAM)
        return
    bw = h * 0.44
    c.rect(x - bw / 2, y - h, x + bw / 2, y - h * 0.45, head or SLATE, bw * 0.4)
    c.circle(x, y - h * 0.86, bw * 0.3, BRICK if lit == "red" else (70, 44, 44, 255))
    c.circle(x, y - h * 0.6, bw * 0.3, GREEN if lit == "green" else (40, 64, 44, 255))


def depot_front(c, roof, wall):
    """A depot building in front view with an open gate."""
    c.poly([(8, 44), (50, 14), (92, 44)], roof)
    c.rect(14, 42, 86, 88, wall, 2)
    c.rect(28, 52, 72, 88, SLATE, 4)
    c.rect(34, 58, 66, 88, (78, 86, 100, 255))


# ---------------------------------------------------------------- rail toolbar

def rail_piece(kind, direction, w, h, top=0):
    """Track piece filling a box of w x h px; top leaves room for catenary."""
    W, H = w * U, h * U
    m = 5
    ends = {
        "ns": ((W / 2, m + top), (W / 2, H - m)),
        "x": ((m, H - m), (W - m, m + top)),
        "ew": ((m, (H + top) / 2), (W - m, (H + top) / 2)),
        "y": ((m, m + top), (W - m, H - m)),
    }[direction]
    cross = min(W, H - top) / 38 if direction == "ns" and W < 50 else min(1.0, (H - top) / 38) if direction == "ew" else 1.0

    def draw(c):
        a, b = ends
        track(c, a, b, kind, cross)
        if kind == "elrail":
            for p in (a, b):
                px, py = p[0] + (3 if p[0] < W / 2 else -3), p[1]
                c.rect(px - 2, py - 30, px + 2, py, SLATE)
            c.line([(a[0], a[1] - 26), (b[0], b[1] - 26)], SLATE, 2)
    return draw


def autorail(kind, H=100):
    def draw(c):
        track(c, (6, H - 8), (94, 8), kind, 1.15)
        track(c, (6, 8), (94, H - 8), kind, 1.15)
    return draw


def convert(kind, H=100):
    def draw(c):
        track(c, (6, H - 10), (94, H - 50), kind, 1.15)
        c.circle(62, 30, 29, AMBER)
        cycle(c, 62, 30, 15, CREAM, 6.5)
    return draw


def rail_depot(kind):
    roofs = {"rail": BRICK, "elrail": BRICK, "mono": STEEL, "maglev": SLATE, "road": BRICK, "tram": SAGE}

    def draw(c):
        depot_front(c, roofs[kind], CREAM)
        if kind == "elrail":
            c.line([(10, 8), (90, 8)], SLATE, 3)
    return draw


def tunnel(kind):
    def draw(c):
        c.poly([(4, 86), (4, 46), (30, 20), (70, 20), (96, 46), (96, 86)], SAGE)
        c.poly([(4, 46), (30, 20), (70, 20), (96, 46), (80, 46), (62, 30), (38, 30), (20, 46)], SAGE_LIGHT)
        c.ellipse(24, 38, 76, 96, fill=STONE)
        c.ellipse(32, 46, 68, 100, fill=SLATE)
        c.rect(4, 86, 96, 96, SAGE)
        if kind in ("rail", "elrail"):
            c.line([(40, 96), (44, 72)], RAIL, 3)
            c.line([(60, 96), (56, 72)], RAIL, 3)
        elif kind == "road":
            c.poly([(34, 96), (42, 70), (58, 70), (66, 96)], ASPHALT)
            c.rect(48.5, 76, 51.5, 92, CREAM)
        elif kind == "mono":
            c.poly([(46, 96), (48, 70), (52, 70), (54, 96)], STEEL)
        else:
            c.poly([(40, 96), (45, 70), (55, 70), (60, 96)], STEEL)
        if kind == "elrail":
            c.line([(10, 10), (90, 10)], SLATE, 3)
    return draw


def rail_station(c):
    # Platform with a roof and a train at it, in a 40 x 20 px box.
    c.rect(4, 66, 196, 80, CONCRETE, 2)
    track(c, (2, 90), (198, 90), "rail", 0.55)
    c.rect(20, 40, 24, 66, SLATE)
    c.rect(176, 40, 180, 66, SLATE)
    c.poly([(8, 30), (192, 30), (184, 42), (16, 42)], STEEL)
    c.rect(60, 46, 150, 86, BRICK, 8)
    c.rect(68, 52, 142, 64, CREAM, 2)
    c.circle(78, 86, 5, SLATE)
    c.circle(132, 86, 5, SLATE)


def rail_signals(c):
    # Two light signals, red and green, 19 x 17 px.
    signal_post(c, 26, 84, 82, "red")
    signal_post(c, 70, 84, 82, "green")


def waypoint(c):
    track(c, (6, 64), (84, 64), "rail", 0.8)
    c.rect(38, 10, 46, 56, SLATE)
    c.poly([(46, 10), (80, 18), (46, 28)], AMBER)


def bridge(c):
    # Suspension bridge, 43 x 20 px.
    W = 215
    c.rect(0, 62, W, 70, BRICK)
    for x in (52, 160):
        c.rect(x - 4, 14, x + 4, 92, SLATE)
    c.line([(0, 22), (30, 52), (52, 16)], CREAM, 3)
    c.line([(52, 16), (106, 56), (160, 16)], CREAM, 3)
    c.line([(160, 16), (186, 52), (W, 22)], CREAM, 3)
    for x in range(64, 156, 12):
        y = 16 + 40 * (1 - ((x - 106) / 54) ** 2)
        c.line([(x, y), (x, 62)], CREAM, 1.5)
    c.line([(0, 90), (40, 84), (80, 92), (120, 84), (170, 92), (W, 86)], WATER, 6)


def build_canal(c):
    iso_tile(c, 50, 54, 46, STONE, 10, ROCK)
    iso_tile(c, 50, 54, 34, WATER)
    c.line([(28, 54), (40, 48), (52, 54), (64, 48)], CREAM, 3)


def build_river(c):
    c.poly([(0, 0), (100, 0), (100, 100), (0, 100)], (0, 0, 0, 0))
    pts = [(16, 6), (44, 22), (30, 46), (62, 60), (48, 84), (70, 98)]
    c.line(pts, SAGE, 30)
    c.line(pts, WATER, 18)
    c.line([(40, 26), (32, 40)], CREAM, 3)


def build_lock(c):
    # Side view: a high and a low basin with the gate between them.
    c.rect(4, 26, 96, 94, STONE, 4)
    c.rect(12, 34, 46, 86, WATER)
    c.rect(54, 56, 88, 86, WATER)
    c.rect(12, 34, 46, 40, CREAM)
    c.rect(54, 56, 88, 62, CREAM)
    c.rect(44, 14, 56, 86, WOOD, 2)
    c.rect(40, 10, 60, 18, SLATE, 2)


def aqueduct(c):
    # 20 x 14 px.
    c.rect(4, 18, 96, 34, STONE, 2)
    c.rect(8, 20, 92, 28, WATER)
    for x in (10, 40, 70):
        c.rect(x, 34, x + 20, 70, STONE)
        c.ellipse(x + 20, 38, x + 40, 76, fill=(0, 0, 0, 0))
    c.punch(lambda h: [h.ellipse(x + 2, 40, x + 28, 90, fill=CREAM) for x in (22, 52)])
    c.rect(0, 34, 100, 38, STONE)


def dock(c):
    # 20 x 18 px at +0+2: quay, crane, water.
    iso_tile(c, 50, 64, 46, WATER)
    c.poly([(4, 64), (50, 40), (96, 64), (50, 64)], CONCRETE)
    c.rect(56, 10, 62, 52, AMBER)
    c.line([(59, 12), (90, 22)], AMBER, 4)
    c.line([(88, 22), (88, 40)], SLATE, 2)
    c.rect(20, 40, 44, 56, BRICK, 2)


def ship_depot(c):
    c.rect(0, 72, 100, 100, WATER)
    c.poly([(10, 44), (50, 14), (90, 44)], STEEL)
    c.rect(14, 42, 86, 78, CREAM, 2)
    c.rect(28, 50, 72, 78, WATER_DEEP, 4)
    c.line([(2, 88), (18, 82), (34, 88), (50, 82), (66, 88), (82, 82), (98, 88)], CREAM, 3)


def airport(c):
    # 39 x 20 px at +1+0: terminal with a tower and a runway.
    band(c, (10, 92), (190, 52), 22, ASPHALT)
    for t in range(4):
        x = 40 + t * 36
        band(c, (x, 92 - (x - 10) * 0.222 - 0), (x + 16, 92 - (x + 6) * 0.222), 3, CREAM)
    c.rect(20, 34, 96, 70, CONCRETE, 3)
    c.rect(24, 40, 92, 48, STEEL, 1)
    c.rect(100, 12, 110, 60, CONCRETE)
    c.rect(94, 6, 116, 18, STEEL, 2)
    with c.at(120, 0, 0.6):
        mi.plane(c, CREAM)


def bus_station(c):
    iso_tile(c, 50, 60, 48, CONCRETE, 8, (150, 152, 156, 255))
    c.poly([(16, 50), (50, 32), (84, 50), (50, 68)], ASPHALT)
    c.rect(18, 20, 56, 40, STEEL, 6)
    c.rect(22, 24, 52, 32, CREAM, 2)
    c.rect(64, 14, 68, 56, SLATE)
    c.circle(66, 14, 8, AMBER)


def truck_bay(c):
    iso_tile(c, 50, 60, 48, CONCRETE, 8, (150, 152, 156, 255))
    c.poly([(16, 50), (50, 32), (84, 50), (50, 68)], ASPHALT)
    c.rect(14, 22, 52, 46, CREAM, 3)
    c.poly([(54, 28), (68, 28), (78, 38), (78, 46), (54, 46)], AMBER)
    c.circle(26, 48, 5, SLATE)
    c.circle(68, 48, 5, SLATE)


def one_way(c):
    c.rect(10, 18, 90, 64, STEEL, 8)
    c.poly([(20, 36), (58, 36), (58, 26), (80, 41), (58, 56), (58, 46), (20, 46)], CREAM)
    c.rect(46, 64, 54, 92, SLATE)


def signal_convert(c):
    signal_post(c, 30, 88, 70, "red")
    c.circle(66, 36, 24, AMBER)
    cycle(c, 66, 36, 12, CREAM, 5)


def raise_land(c, up=True):
    # 20 x 14 px at +0+4: a grass slope with an arrow.
    c.poly([(2, 48), (30, 34), (50, 44), (22, 58)], SAGE)
    c.poly([(22, 58), (50, 44), (50, 52), (22, 66)], (96, 128, 80, 255))
    tip, base = (74, 2), (74, 68)
    if not up:
        tip, base = base, tip
    d = 1 if up else -1
    c.line([base, (tip[0], tip[1] + 20 * d)], AMBER, 14)
    c.poly([(tip[0] - 22, tip[1] + 26 * d), (tip[0] + 22, tip[1] + 26 * d), tip], AMBER)


def level_land(c):
    # 20 x 14 px at +0+4.
    iso_tile(c, 50, 44, 46, SAGE, 12, (96, 128, 80, 255))
    c.rect(26, 6, 74, 14, AMBER, 3)
    c.line([(50, 14), (50, 34)], AMBER, 6)


def buy_land(c):
    # 12 x 16 px at +4+2: a flag on a pole.
    c.rect(10, 4, 18, 78, SLATE, 2)
    c.poly([(18, 6), (58, 12), (52, 24), (58, 36), (18, 34)], STEEL)
    c.rect(2, 72, 28, 80, SLATE, 3)


def rocks(c):
    iso_tile(c, 50, 64, 50, SAGE, 10, (96, 128, 80, 255))
    c.poly([(30, 50), (40, 22), (62, 18), (70, 46), (54, 58)], ROCK)
    c.poly([(40, 22), (62, 18), (56, 36)], STONE)
    c.poly([(16, 64), (26, 40), (44, 36), (52, 58), (40, 70)], ROCK)
    c.poly([(26, 40), (44, 36), (40, 52)], STONE)
    c.poly([(52, 66), (62, 44), (82, 48), (86, 68), (70, 74)], ROCK)
    c.poly([(62, 44), (82, 48), (72, 58)], STONE)


def lighthouse(c):
    # 9 x 20 px at +5+0.
    c.poly([(10, 92), (16, 26), (30, 26), (36, 92)], CREAM)
    for y in (40, 62, 84):
        c.poly([(16 - (y - 26) * 0.09 * 0 - 2 + (92 - y) * 0.09, y - 6), (30 + 2 - (92 - y) * 0.09, y - 6),
                (31 - (92 - y) * 0.08, y), (15 + (92 - y) * 0.08, y)], BRICK)
    c.rect(12, 14, 34, 26, AMBER, 2)
    c.poly([(10, 14), (23, 2), (36, 14)], BRICK)


# ---------------------------------------------------------------- vehicle and depot windows

VEHICLES = {"train": mi.trainlist, "road": mi.trucklist, "ship": mi.shiplist, "air": mi.planelist}


def vehicle(c, vt, x=0, y=0, s=1.0):
    with c.at(x, y, s):
        VEHICLES[vt](c)


def sell(vt, all_=False, chain=False):
    def draw(c):
        if all_ or chain:
            vehicle(c, vt, 18, -2, 0.8)
            vehicle(c, vt, -4, 18, 0.84)
        else:
            vehicle(c, vt, -4, 4, 1.0)
        badge_x(c, 76, 22, 22)
    return draw


def replace(vt):
    def draw(c):
        vehicle(c, vt, -4, 4, 1.0)
        badge_cycle(c, 76, 22, 22)
    return draw


def clone(vt):
    def draw(c):
        vehicle(c, vt, 16, -4, 0.86)
        c.im.putalpha(c.im.getchannel("A").point(lambda a: a * 140 // 255))
        vehicle(c, vt, -4, 16, 0.9)
    return draw


def group_badge(vt, badge):
    def draw(c):
        vehicle(c, vt, -4, 6, 0.98)
        badge(c, 76, 22, 22)
    return draw


def badge_cycle_off(c, cx, cy, r):
    badge_cycle(c, cx, cy, r, (150, 150, 150, 255))
    c.line([(cx - r * 0.75, cy + r * 0.75), (cx + r * 0.75, cy - r * 0.75)], BRICK, r * 0.28)


def badge_cycle_on(c, cx, cy, r):
    badge_cycle(c, cx, cy, r, AMBER)


def livery(vt):
    def draw(c):
        vehicle(c, vt, 0, 14, 0.84)
        c.rect(58, 6, 94, 42, CREAM, 6)
        c.rect(62, 10, 76, 38, BRICK, 3)
        c.rect(76, 10, 90, 38, STEEL, 3)
    return draw


def centre_view(c):
    # 16 x 16 px: crosshair.
    c.ring(50, 50, 30, CREAM, 9)
    for a, b in (((50, 4), (50, 30)), ((50, 70), (50, 96)), ((4, 50), (30, 50)), ((70, 50), (96, 50))):
        c.line([a, b], CREAM, 9)
    c.circle(50, 50, 8, AMBER)


def to_depot(vt):
    def draw(c):
        # 16 x 16 px: depot house with an arrow into it.
        c.poly([(28, 34), (64, 4), (100, 34)], BRICK)
        c.rect(34, 32, 94, 96, CREAM, 2)
        c.rect(46, 48, 82, 96, SLATE, 3)
        c.poly([(0, 56), (34, 56), (34, 38), (64, 68), (34, 98), (34, 80), (0, 80)], AMBER)
    return draw


def ignore_signals(c):
    # 12 x 16 px.
    signal_post(c, 34, 98, 96, "red")
    badge_x(c, 66, 70, 30, BRICK)


def show_orders(c):
    # 16 x 11 px: an arrow.
    c.line([(6, 27), (52, 27)], AMBER, 12)
    c.poly([(46, 4), (76, 27), (46, 50)], AMBER)


def vehicle_details(c):
    # 16 x 16 px: a sheet with lines.
    c.rect(14, 6, 86, 94, CREAM, 6)
    for y in (22, 38, 54, 70):
        c.rect(24, y, 76 if y != 70 else 56, y + 6, STEEL, 2)


def refit(c):
    # 16 x 16 px: a wrench.
    c.line([(24, 76), (64, 36)], STEEL, 16)
    c.circle(70, 30, 22, STEEL)
    c.punch(lambda h: h.poly([(66, 4), (96, 4), (96, 34), (78, 30)], CREAM))
    c.circle(24, 76, 12, STEEL)


def turn_around(c):
    # 14 x 16 px: a U-turn arrow.
    c.arc(50, 46, 28, 180, 360, AMBER, 13)
    c.line([(22, 46), (22, 90)], AMBER, 13)
    c.poly([(60, 46), (96, 46), (78, 74)], AMBER)


def flag_stopped(c):
    c.rect(4, 4, 96, 96, BRICK, 22)
    c.rect(28, 28, 72, 72, CREAM, 6)


def flag_running(c):
    c.circle(50, 50, 48, GREEN)
    c.poly([(36, 24), (78, 50), (36, 76)], CREAM)


# ---------------------------------------------------------------- window glyphs (flat ink, no shadow)

def arrow(direction):
    def draw(c):
        W, H = c.W, c.H
        cx, cy = W / 2, H / 2
        pts = {"down": [(0.5, 1), (W - 0.5, 1), (cx, H - 0.5)],
               "up": [(0.5, H - 1), (W - 0.5, H - 1), (cx, 0.5)],
               "left": [(W - 1, 0.5), (W - 1, H - 0.5), (0.5, cy)],
               "right": [(1, 0.5), (1, H - 0.5), (W - 0.5, cy)]}[direction]
        c.poly(pts, INK)
    return draw


def pin(down):
    def draw(c):
        # 7 x 8 px: a drawing pin, upright when stuck.
        if down:
            c.circle(17.5, 12, 11, INK)
            c.rect(11, 12, 24, 22, INK)
            c.rect(6, 22, 29, 27, INK, 2)
            c.rect(16, 27, 19, 40, INK)
        else:
            c.poly([(22, 2), (34, 14), (26, 18), (18, 10)], INK)
            c.line([(16, 10), (26, 22)], INK, 7)
            c.poly([(6, 18), (18, 6), (30, 26), (26, 30)], INK)
            c.line([(14, 26), (2, 38)], INK, 3)
    return draw


def shade_glyph(unshade):
    def draw(c):
        # 7 x 4..5 px: a bar with a triangle.
        W, H = c.W, c.H
        if unshade:
            c.rect(1, H - 5, W - 1, H, INK)
            c.poly([(3, H - 8), (W - 3, H - 8), (W / 2, 0)], INK)
        else:
            c.rect(1, 0, W - 1, 5, INK)
            c.poly([(3, 8), (W - 3, 8), (W / 2, H)], INK)
    return draw


def defsize(c):
    c.rect(2, 2, c.W - 2, c.H - 2, INK, 4)
    c.rect(7, 9, c.W - 7, c.H - 7, (0, 0, 0, 0))
    c.punch(lambda h: h.rect(7, 9, h.W - 7, h.H - 7, CREAM, 1))


def debug_box(c):
    c.ellipse(8, 10, 22, 32, fill=INK)
    c.circle(15, 8, 5, INK)
    for y in (16, 24):
        c.line([(3, y), (27, y)], INK, 2.5)


def resize_grip(left):
    def draw(c):
        W, H = c.W, c.H
        for k in (0, 1, 2):
            d = 6 + k * 11
            if left:
                c.line([(0, H - d), (d, H)], INK, 3.5)
            else:
                c.line([(W, H - d), (W - d, H)], INK, 3.5)
    return draw


def circle_sign(plus):
    def draw(c):
        c.circle(20, 20, 18, STEEL)
        c.rect(9, 17.5, 31, 22.5, CREAM, 1)
        if plus:
            c.rect(17.5, 9, 22.5, 31, CREAM, 1)
    return draw


def box(checked):
    def draw(c):
        c.rect(2, 2, 33, 33, INK, 5)
        c.punch(lambda h: h.rect(6, 6, 29, 29, CREAM, 3))
        if checked:
            c.line([(10, 18), (16, 25), (27, 10)], INK, 5)
    return draw


def lock_icon(c):
    c.ring(17, 16, 9, INK, 4)
    c.rect(4, 18, 30, 44, AMBER, 4)
    c.circle(17, 28, 3.5, INK)


def warning(c):
    c.poly([(25, 2), (48, 42), (2, 42)], AMBER)
    c.rect(22.5, 14, 27.5, 30, INK, 2)
    c.circle(25, 36, 3, INK)


def house_icon(c):
    c.poly([(4, 18), (20, 3), (36, 18)], INK)
    c.rect(8, 16, 32, 37, INK, 1)
    c.punch(lambda h: h.rect(17, 25, 23, 37, CREAM))


def pin_shared(c):
    # Shared orders: two overlapping sheets, 7 x 9 px.
    c.rect(10, 2, 33, 30, INK, 3)
    c.punch(lambda h: h.rect(13, 5, 30, 27, CREAM, 2))
    c.rect(2, 14, 25, 43, INK, 3)
    c.punch(lambda h: h.rect(5, 17, 22, 40, CREAM, 2))
    c.rect(8, 23, 19, 26, INK)
    c.rect(8, 31, 19, 34, INK)


def delete_left(c):
    W, H = c.W, c.H
    c.poly([(2, H / 2), (20, 4), (W - 3, 4), (W - 3, H - 4), (20, H - 4)], INK)
    c.punch(lambda h: (h.line([(30, 13), (48, 27)], CREAM, 4), h.line([(30, 27), (48, 13)], CREAM, 4)))


def delete_right(c):
    W, H = c.W, c.H
    c.poly([(W - 2, H / 2), (W - 20, 4), (3, 4), (3, H - 4), (W - 20, H - 4)], INK)
    c.punch(lambda h: (h.line([(22, 13), (40, 27)], CREAM, 4), h.line([(22, 27), (40, 13)], CREAM, 4)))


def rating(col, mouth):
    def draw(c):
        c.circle(25, 25, 23, col)
        c.circle(17, 20, 3.5, INK)
        c.circle(33, 20, 3.5, INK)
        if mouth > 0:
            c.arc(25, 24, 12, 30, 150, INK, 3.5)
        elif mouth < 0:
            c.arc(25, 42, 12, 210, 330, INK, 3.5)
        else:
            c.line([(15, 34), (35, 34)], INK, 3.5)
    return draw


def profit(col):
    def draw(c):
        c.ellipse(4, 4, c.W - 4, c.H - 4, fill=col)
    return draw


def rename(c):
    c.line([(8, 42), (40, 10)], INK, 8)
    c.poly([(2, 48), (4, 38), (12, 46)], INK)


def goto_location(c):
    c.circle(27, 18, 16, BRICK)
    c.poly([(13, 24), (41, 24), (27, 48)], BRICK)
    c.circle(27, 18, 6, CREAM)


# ---------------------------------------------------------------- cursors

def pointer(c, x, y):
    """The mouse arrow with its tip at (x, y), 12 x 18 px."""
    pts = [(0, 0), (0, 78), (18, 62), (30, 90), (42, 85), (30, 58), (54, 56)]
    with c.at(x, y):
        c.poly(pts, SLATE)
        with c.at(5.5, 10, 0.8):
            c.poly(pts, CREAM)


def tool(c, icon, frac=0.74):
    """Draw a 100-unit tool icon at the lower right of a cursor, frac of its smaller side."""
    s = min(c.W, c.H) * frac / 100
    with c.at(c.W - 100 * s, c.H - 100 * s, s):
        icon(c)


def cursor(icon, frac=0.74):
    """Cursor with the mouse arrow at the hotspot and the tool icon at the lower right."""
    def draw(c):
        tool(c, icon, frac)
        pointer(c, 0, 0)
    return draw


def cursor_box(icon, w, h):
    """Like cursor(), for icons drawn in a box other than 20 x 20 px."""
    def draw(c):
        s = min((c.W - 30) / (w * U), (c.H - 40) / (h * U))
        with c.at(c.W - w * U * s - 2, c.H - h * U * s - 2, s):
            icon(c)
        pointer(c, 0, 0)
    return draw


def track_cursor(kind, direction):
    W = 130
    ends = {"ns": ((90, 64), (90, 140)), "x": ((40, 132), (128, 88)), "ew": ((36, 120), (132, 120)),
            "y": ((40, 92), (128, 136))}[direction]

    def draw(c):
        track(c, *ends[:2], kind, 0.85)
        if kind == "elrail":
            for p in ends:
                c.rect(p[0] - 2, p[1] - 28, p[0] + 2, p[1], SLATE)
            c.line([(ends[0][0], ends[0][1] - 24), (ends[1][0], ends[1][1] - 24)], SLATE, 2)
        pointer(c, 0, 0)
    return draw


def road_cursor(kind, direction, tip=(0, 0)):
    def draw(c):
        bx, by = tip[0] + 30, tip[1] + 64
        a, b = ((bx, by + 50), (c.W - 4, by + 4)) if direction == "x" else ((bx, by + 4), (c.W - 4, by + 50))
        track(c, a, b, kind, 0.9)
        pointer(c, *tip)
    return draw


def demolish_frame(k):
    def draw(c):
        sc = min(c.W, c.H) * 0.78 / 100
        with c.at(c.W - 100 * sc, c.H - 100 * sc, sc):
            bomb(c)
            for a in range(0, 360, 60):
                r = math.radians(a + k * 30)
                c.line([(84, 8), (84 + (8 + k * 3) * math.cos(r), 8 + (8 + k * 3) * math.sin(r))], AMBER, 3)
        pointer(c, 0, 0)
    return draw


def land_frame(up, k):
    def draw(c):
        with c.at(c.W - 104, c.H - 76 - k * 4 * (1 if up else -1) + (8 if not up else 0), 1.04):
            raise_land(c, up)
        pointer(c, 0, 0)
    return draw


def pick_frame(k):
    def draw(c):
        sc = min(c.W, c.H) * 0.8 / 100
        with c.at(c.W - 100 * sc, c.H - 100 * sc, sc):
            c.line([(18, 82), (62, 38)], STEEL, 12)
            c.poly([(52, 30), (78, 4), (96, 22), (70, 48)], AMBER)
            c.circle(18, 82, 10 + k * 3, BRICK)
        pointer(c, 0, 0)
    return draw


def signal_cursor(lit):
    def draw(c):
        signal_post(c, 78, 148, 92, "red" if lit == 0 else "green")
        signal_post(c, 118, 148, 92, "green" if lit == 0 else "red")
        pointer(c, 0, 0)
    return draw


def query_cursor(c):
    tool(c, mi.query)
    pointer(c, 0, 0)


def tram_cursor(direction):
    # 42 x 32 px with the hotspot at (15, 7): wires above, track below.
    def draw(c):
        a, b = ((84, 136), (196, 80)) if direction == "x" else ((84, 84), (196, 140))
        track(c, a, b, "tram", 0.9)
        c.line([(a[0], a[1] - 50), (b[0], b[1] - 50)], SLATE, 2)
        pointer(c, 75, 35)
    return draw


def town_cursor(c):
    tool(c, mi.town)
    pointer(c, 0, 0)


def industry_cursor(c):
    tool(c, mi.industry)
    pointer(c, 0, 0)


def hq(c):
    iso_box(c, 50, 74, 44, 50, CONCRETE, STEEL, shade(STEEL, 0.75))
    for y in (40, 56):
        c.line([(10, y + 6), (46, y + 24)], CREAM, 3)
        c.line([(54, y + 24), (90, y + 6)], CREAM, 3)
    c.rect(47, 4, 53, 30, SLATE)
    c.poly([(53, 4), (76, 10), (53, 16)], AMBER)


def hq_cursor(c):
    tool(c, hq, 0.8)
    pointer(c, 0, 0)


def tree_cursor(c):
    tool(c, mi.planttrees)
    pointer(c, 0, 0)


def sign_cursor(c):
    tool(c, mi.sign)
    pointer(c, 0, 0)


def transmitter_cursor(c):
    tool(c, mi.transmitter)
    pointer(c, 0, 0)


# ---------------------------------------------------------------- cargo icons (small, drawn in their own box)

def heap(col, light):
    def draw(c):
        W, H = c.W, c.H
        c.poly([(1, H - 2), (W * 0.3, H * 0.25), (W * 0.55, H * 0.1), (W * 0.8, H * 0.35), (W - 1, H - 2)], col)
        c.poly([(W * 0.3, H * 0.25), (W * 0.55, H * 0.1), (W * 0.5, H * 0.55)], light)
    return draw


def barrels(col, band_col):
    def draw(c):
        W, H = c.W, c.H
        n = 2 if W > 40 else 1
        bw = W / n
        for k in range(n):
            x = k * bw
            c.rect(x + 1, 2, x + bw - 1, H - 1, col, bw * 0.25)
            c.rect(x + 1, H * 0.3, x + bw - 1, H * 0.3 + 3, band_col)
            c.rect(x + 1, H * 0.7, x + bw - 1, H * 0.7 + 3, band_col)
    return draw


def passengers(c):
    for x, col in ((14, STEEL), (32, BRICK)):
        c.circle(x, 9, 6, CREAM)
        c.rect(x - 8, 16, x + 8, 50, col, 5)


def mail(c):
    c.rect(2, 8, 43, 40, CREAM, 3)
    c.line([(3, 10), (22.5, 26), (42, 10)], STEEL, 3)


def livestock(c):
    c.ellipse(4, 8, 36, 28, fill=CREAM)
    c.circle(38, 12, 7, CREAM)
    for x in (8, 14, 26, 32):
        c.rect(x, 24, x + 3, 34, SLATE)
    c.circle(16, 16, 4, SLATE)


def crate(col, line):
    def draw(c):
        W, H = c.W, c.H
        c.rect(2, 2, W - 2, H - 2, col, 3)
        c.line([(4, 4), (W - 4, H - 4)], line, 3)
        c.rect(2, 2, W - 2, 6, line)
    return draw


def logs(c):
    for y in (8, 26):
        c.rect(4, y, 50, y + 16, WOOD, 8)
        c.circle(46, y + 8, 7, (220, 186, 140, 255))
    c.rect(18, 14, 40, 32, WOOD, 8)


def steel(c):
    c.poly([(2, 12), (24, 2), (34, 8), (12, 18)], RAIL)
    c.poly([(2, 12), (12, 18), (12, 28), (2, 22)], STEEL)
    c.poly([(12, 18), (34, 8), (34, 18), (12, 28)], (150, 170, 190, 255))


def bag(col):
    def draw(c):
        W, H = c.W, c.H
        c.ellipse(4, H * 0.3, W - 4, H - 1, fill=col)
        c.poly([(W * 0.35, H * 0.35), (W * 0.65, H * 0.35), (W * 0.6, 2), (W * 0.4, 2)], col)
        c.rect(W * 0.32, H * 0.25, W * 0.68, H * 0.32, WOOD)
    return draw


def fruit(c):
    c.ellipse(4, 18, 31, 54, fill=AMBER)
    c.poly([(17, 20), (8, 2), (17, 10), (26, 2)], SAGE)


def drop(c):
    W, H = c.W, c.H
    c.poly([(W / 2, 2), (W - 4, H * 0.6), (4, H * 0.6)], WATER)
    c.circle(W / 2, H * 0.62, W / 2 - 4, WATER)


def diamond(c):
    c.poly([(4, 14), (12, 4), (24, 4), (32, 14), (18, 33)], (150, 210, 230, 255))
    c.poly([(4, 14), (32, 14), (18, 33)], (110, 180, 210, 255))


def paper(c):
    for k in range(3):
        c.rect(2 + k * 2, 20 - k * 7, 33 + k * 2, 28 - k * 7, CREAM if k % 2 else RAIL, 1)


def sweets(c):
    c.ellipse(16, 12, 42, 34, fill=BRICK)
    c.poly([(2, 10), (18, 20), (2, 34)], AMBER)
    c.poly([(54, 10), (40, 22), (54, 36)], AMBER)


def sugar(c):
    c.rect(4, 8, 56, 32, CREAM, 3)
    c.rect(4, 8, 56, 14, RAIL)


def toys(c):
    c.rect(4, 14, 44, 46, STEEL, 3)
    c.rect(20, 14, 28, 46, AMBER)
    c.poly([(16, 14), (24, 4), (32, 14)], AMBER)


def candyfloss(c):
    c.ellipse(4, 2, 46, 24, fill=(232, 168, 190, 255))
    c.line([(25, 20), (25, 30)], CREAM, 3)


def can(c):
    c.rect(4, 2, 27, 48, BRICK, 4)
    c.rect(4, 18, 27, 30, CREAM)


def toffee(c):
    c.rect(4, 6, 42, 26, (176, 122, 64, 255), 4)
    c.line([(4, 16), (42, 16)], (210, 160, 100, 255), 2)


def bubbles(c):
    c.ring(18, 26, 15, (160, 200, 230, 255), 3)
    c.ring(40, 12, 8, (160, 200, 230, 255), 3)


def plastic(c):
    c.ellipse(4, 4, 43, 28, fill=(226, 214, 186, 255))
    c.ellipse(12, 8, 30, 18, fill=CREAM)


def battery(c):
    c.rect(4, 6, 27, 48, SLATE, 3)
    c.rect(11, 1, 20, 6, SLATE)
    c.rect(8, 14, 23, 26, AMBER, 1)


def sq(draw):
    """Fit an icon drawn on the 100-unit square into a smaller box, centred."""
    def fitted(c):
        s = min(c.W, c.H) / 100
        with c.at((c.W - 100 * s) / 2, (c.H - 100 * s) / 2, s):
            draw(c)
    return fitted


# ---------------------------------------------------------------- the sprite table

# key: (block, index, (w, h, xoffs, yoffs), draw, shadow)
#   block "base" = sprite number in the base set; "gui" = OTTD_GUI (SPR_OPENTTD_BASE + index);
#   "catenary", "tramway", "canals" = Action 5 blocks.
SPRITES = {}


def add(key, block, index, size, draw, shadow=True):
    SPRITES[key] = (block, index, size, draw, shadow)


RAILS = (("rail", 1251, "rail"), ("mono", 1255, "mono"), ("maglev", 1259, "maglev"))
PIECE_SIZES = {
    1251: (8, 15, 6, 4), 1252: (20, 11, 0, 7), 1253: (20, 7, 0, 9), 1254: (19, 10, 1, 8),
    1255: (5, 15, 7, 4), 1256: (18, 11, 1, 7), 1257: (20, 4, 0, 12), 1258: (18, 11, 1, 7),
    1259: (10, 15, 5, 4), 1260: (19, 12, 0, 6), 1261: (20, 12, 0, 6), 1262: (20, 5, 0, 11),
}
for name, first, kind in RAILS:
    for k, d in enumerate(("ns", "x", "ew", "y")):
        w, h, xo, yo = PIECE_SIZES[first + k]
        add(f"{name}_{d}", "base", first + k, (w, h, xo, yo), rail_piece(kind, d, w, h))
for k, (d, size) in enumerate((("ns", (8, 18, 6, 1)), ("x", (20, 16, 0, 2)), ("ew", (20, 10, 0, 6)),
                               ("y", (19, 14, 1, 4)))):
    add(f"elrail_{d}", "catenary", 36 + k, size, rail_piece("elrail", d, size[0], size[1], top=26))

# Track cursors: arrow plus the piece; NS/X/EW/Y for each railtype.
CURSOR_SIZES = {
    1263: (20, 29), 1264: (26, 28), 1265: (27, 26), 1266: (26, 28),
    1267: (18, 29), 1268: (25, 28), 1269: (30, 26), 1270: (25, 28),
    1271: (21, 29), 1272: (25, 28), 1273: (26, 26), 1274: (26, 28),
}
for name, first, kind in RAILS:
    for k, d in enumerate(("ns", "x", "ew", "y")):
        w, h = CURSOR_SIZES[1263 + (first - 1251) + k]
        add(f"cur_{name}_{d}", "base", 1263 + (first - 1251) + k, (w, h, 0, 0), track_cursor(kind, d))
for k, (d, size) in enumerate((("ns", (20, 29)), ("x", (26, 28)), ("ew", (27, 26)), ("y", (26, 28)))):
    add(f"cur_elrail_{d}", "catenary", 40 + k, size + (0, 0), track_cursor("elrail", d))

for name, auto, depot, conv, sizes in (
        ("rail", 53, 1294, 55, ((20, 11, 0, 7), (20, 20, 0, 0), (20, 20, 0, 0))),
        ("elrail", 57, 61, 59, ((20, 15, 0, 3), (20, 20, 0, 0), (20, 20, 0, 0))),
        ("mono", 63, 67, 65, ((20, 11, 0, 7), (20, 20, 0, 0), (20, 20, 0, 0))),
        ("maglev", 69, 73, 71, ((20, 13, 0, 5), (20, 20, 0, 0), (20, 20, 0, 0)))):
    add(f"auto_{name}", "gui", auto, sizes[0], autorail(name, sizes[0][1] * U))
    add(f"cur_auto_{name}", "gui", auto + 1, (26, 28, 0, 0), cursor_box(autorail(name, sizes[0][1] * U), *sizes[0][:2]))
    add(f"conv_{name}", "gui", conv, (20, 16, 0, 0), convert(name, 80))
    add(f"cur_conv_{name}", "gui", conv + 1, ({"rail": 29, "elrail": 28, "mono": 32, "maglev": 28}[name], 28, 0, 0),
        cursor(convert(name)))
    dep_block = "base" if name == "rail" else "gui"
    add(f"depot_{name}", dep_block, depot, (20, 20, 0, 0), rail_depot(name))
    cur_depot = {"rail": 1296, "elrail": 62, "mono": 68, "maglev": 74}[name]
    add(f"cur_depot_{name}", dep_block, cur_depot, (32, 32, 0, 0), cursor(rail_depot(name)))

for name, img, cur, block in (("rail", 2430, 2434, "base"), ("mono", 2431, 2435, "base"),
                              ("maglev", 2432, 2436, "base"), ("elrail", 44, 45, "catenary"),
                              ("road", 2429, 2433, "base")):
    add(f"tunnel_{name}", block, img, (20, 20, 0, 0), tunnel(name))
    add(f"cur_tunnel_{name}", block, cur, (27, 30, 0, 0), cursor(tunnel(name)))

add("rail_station", "base", 1298, (40, 20, 0, 0), rail_station)
add("cur_rail_station", "base", 1300, (29, 32, 0, 0), cursor_box(rail_station, 40, 20))
add("rail_signals", "base", 1291, (19, 17, 0, 1), rail_signals)
add("cur_signals_0", "base", 1292, (28, 30, 0, 0), signal_cursor(0))
add("cur_signals_1", "base", 1293, (28, 30, 0, 0), signal_cursor(1))
add("signal_convert", "gui", 135, (20, 20, 0, 0), signal_convert)
add("waypoint", "gui", 76, (18, 16, 1, 3), waypoint)
add("cur_waypoint", "gui", 77, (32, 32, 0, 0), cursor_box(waypoint, 18, 16))
add("bridge", "base", 2594, (43, 20, 0, 0), bridge)
add("cur_bridge", "base", 2593, (45, 32, 0, 0), cursor_box(bridge, 43, 20))
add("remove", "base", 714, (20, 18, 0, 1), bulldozer)
add("dynamite", "base", 703, (20, 20, 0, 0), bomb)
for k, sid in enumerate(range(704, 708)):
    add(f"cur_demolish_{k}", "base", sid, ((27, 26, 27, 28)[k], 29, 0, 0), demolish_frame(k))

# Road and tram toolbar.
add("road_y", "base", 1309, (20, 13, 0, 5), rail_piece("road", "y", 20, 13))
add("road_x", "base", 1310, (20, 13, 0, 5), rail_piece("road", "x", 20, 13))
add("cur_road_x", "base", 1311, (27, 28, 0, 0), road_cursor("road", "x"))
add("cur_road_y", "base", 1312, (27, 28, 0, 0), road_cursor("road", "y"))
add("autoroad", "gui", 82, (20, 14, 0, 4), autorail("road", 70))
add("cur_autoroad", "gui", 83, (27, 29, 0, 0), cursor_box(autorail("road", 70), 20, 14))
add("tram_y", "tramway", 0, (20, 13, 0, 4), rail_piece("tram", "y", 20, 13))
add("tram_x", "tramway", 1, (20, 13, 0, 4), rail_piece("tram", "x", 20, 13))
add("cur_tram_x", "tramway", 2, (42, 32, -15, -7), tram_cursor("x"))
add("cur_tram_y", "tramway", 3, (42, 31, -13, -7), tram_cursor("y"))
add("autotram", "gui", 84, (20, 14, 0, 4), autorail("tram", 70))
add("cur_autotram", "gui", 85, (27, 28, 0, 0), cursor_box(autorail("tram", 70), 20, 14))
add("road_depot", "base", 1295, (20, 20, 0, 0), rail_depot("road"))
add("cur_road_depot", "base", 1297, (32, 32, 0, 0), cursor(rail_depot("road")))
add("bus_station", "base", 749, (20, 19, 0, 1), bus_station)
add("truck_bay", "base", 750, (20, 20, 0, 0), truck_bay)
add("cur_bus_station", "base", 2725, (32, 32, 0, 0), cursor(bus_station))
add("cur_truck_bay", "base", 2726, (32, 32, 0, 0), cursor(truck_bay))
add("one_way", "gui", 134, (20, 18, 0, 2), one_way)
add("conv_road", "gui", 180, (20, 18, 0, 0), convert("road", 90))
add("cur_conv_road", "gui", 181, (29, 29, 0, 0), cursor(convert("road")))
add("conv_tram", "gui", 182, (20, 18, 0, 0), convert("tram", 90))
add("cur_conv_tram", "gui", 183, (29, 28, 0, 0), cursor(convert("tram")))

# Waterways and air.
add("canal", "gui", 88, (20, 18, 0, 1), build_canal)
add("cur_canal", "gui", 89, (32, 32, 0, 0), cursor(build_canal))
add("river", "gui", 136, (20, 20, 0, 0), build_river)
add("cur_river", "gui", 137, (27, 32, 0, 0), cursor(build_river))
add("lock", "canals", 64, (20, 20, 0, 0), build_lock)
add("cur_lock", "gui", 87, (32, 32, 0, 0), cursor(build_lock))
add("aqueduct", "gui", 145, (20, 14, 0, 6), aqueduct)
add("cur_aqueduct", "gui", 146, (27, 32, 0, 0), cursor_box(aqueduct, 20, 14))
add("dock", "base", 746, (20, 18, 0, 2), dock)
add("cur_dock", "base", 3668, (32, 32, 0, 0), cursor_box(dock, 20, 18))
add("ship_depot", "base", 748, (20, 20, 0, 0), ship_depot)
add("cur_ship_depot", "base", 721, (32, 32, 0, 0), cursor(ship_depot))
add("airport", "base", 744, (39, 20, 1, 0), airport)
add("cur_airport", "base", 2724, (32, 32, 0, 0), cursor_box(airport, 39, 20))

# Landscaping.
add("terraform_up", "base", 694, (20, 14, 0, 4), lambda c: raise_land(c, True))
add("terraform_down", "base", 695, (20, 14, 0, 4), lambda c: raise_land(c, False))
for k in range(3):
    add(f"cur_raise_{k}", "base", 696 + k, (29, 24, 0, 0), land_frame(True, k))
    add(f"cur_lower_{k}", "base", 699 + k, (29, 24, 0, 0), land_frame(False, k))
add("level_land", "gui", 91, (20, 14, 0, 4), level_land)
add("cur_level_land", "gui", 92, (29, 24, 0, 0), cursor_box(level_land, 20, 14))
add("buy_land", "base", 4791, (12, 16, 4, 2), buy_land)
add("cur_buy_land", "base", 4792, (20, 28, 0, 0), cursor_box(buy_land, 12, 16))
add("rocks", "base", 4084, (20, 20, 0, 0), rocks)
add("cur_rocks", "base", 4087, (26, 32, 0, 0), cursor(rocks))
add("lighthouse", "base", 4085, (9, 20, 5, 0), lighthouse)
add("cur_lighthouse", "base", 4088, (19, 32, 0, 0), cursor_box(lighthouse, 9, 20))
add("cur_transmitter", "base", 4089, (28, 32, 0, 0), transmitter_cursor)
add("cur_query", "base", 719, (26, 31, 0, 0), query_cursor)
add("cur_hq", "base", 720, (32, 32, 0, 0), hq_cursor)
add("cur_sign", "base", 722, (26, 32, 0, 0), sign_cursor)
add("cur_tree", "base", 2010, (23, 32, 0, 0), tree_cursor)
add("cur_town", "base", 4080, (32, 32, 0, 0), town_cursor)
add("cur_industry", "base", 4081, (26, 31, 0, 0), industry_cursor)
for k in range(3):
    add(f"cur_pick_{k}", "base", 716 + k, (24, 27, 0, 0), pick_frame(k))

# Vehicle, depot and group windows.
VT = ("train", "road", "ship", "air")
for k, vt in enumerate(VT):
    add(f"sell_{vt}", "gui", 93 + k, (20, 20, 0, 0), sell(vt))
    add(f"sell_all_{vt}", "gui", 97 + k, (20, 20, 0, 0), sell(vt, all_=True))
    add(f"replace_{vt}", "gui", 101 + k, (20, 20, 0, 0), replace(vt))
    add(f"clone_{vt}", "gui", 106 + k, ((13, 16, 0, 0), (14, 15, 0, 1), (16, 16, 0, 0), (15, 15, 0, 1))[k], sq(clone(vt)))
    add(f"cur_clone_{vt}", "gui", 110 + k, ((22, 29), (23, 29), (25, 29), (24, 29))[k] + (0, 0),
        cursor(clone(vt)))
    odd = (19, 19, 0, 1) if k % 2 else (19, 20, 0, 0)
    add(f"group_create_{vt}", "gui", 114 + k, odd, group_badge(vt, badge_plus))
    add(f"group_delete_{vt}", "gui", 118 + k, (20, 20, 0, 0), group_badge(vt, badge_x))
    add(f"group_rename_{vt}", "gui", 122 + k, odd, group_badge(vt, badge_pencil))
    add(f"group_replace_on_{vt}", "gui", 126 + k, (20, 20, 0, 0), group_badge(vt, badge_cycle_on))
    add(f"group_replace_off_{vt}", "gui", 130 + k, (20, 20, 0, 0), group_badge(vt, badge_cycle_off))
    add(f"livery_{vt}", "gui", 175 + k, ((13, 20, 0, 0), (14, 19, 0, 1), (16, 20, 0, 0), (17, 19, 0, 0))[k],
        sq(livery(vt)))
    add(f"to_depot_{vt}", "base", (685, 686, 688, 687)[k], (16, 10 if vt == "ship" else 16, 0, 0), sq(to_depot(vt)))
add("sell_chain", "gui", 105, (20, 20, 0, 0), sell("train", chain=True))
add("centre_view", "base", 683, (16, 16, 0, 0), sq(centre_view))
add("ignore_signals", "base", 689, (12, 16, 2, 0), sq(ignore_signals))
add("show_orders", "base", 690, (16, 11, 0, 3), show_orders)
add("vehicle_details", "base", 691, (16, 16, 0, 0), sq(vehicle_details))
add("refit", "base", 692, (16, 16, 0, 0), sq(refit))
add("turn_around", "base", 715, (14, 16, 0, 0), sq(turn_around))
add("flag_stopped", "base", 3090, (7, 7, 0, 1), sq(flag_stopped))
add("flag_running", "base", 3091, (7, 7, 0, 1), sq(flag_running))

# Window widget glyphs and small status icons.
add("arrow_down", "gui", 45, (7, 4, 1, 2), arrow("down"), False)
add("arrow_up", "gui", 46, (7, 4, 1, 2), arrow("up"), False)
add("arrow_left", "gui", 47, (4, 7, 1, 1), arrow("left"), False)
add("arrow_right", "gui", 48, (4, 7, 2, 1), arrow("right"), False)
add("house_icon", "gui", 49, (8, 8, 1, 1), house_icon, False)
add("shared_orders", "gui", 50, (9, 9, 1, 0), pin_shared, False)
add("pin_up", "gui", 51, (7, 8, 1, 1), pin(True), False)
add("pin_down", "gui", 52, (8, 8, 1, 1), pin(False), False)
add("box_empty", "gui", 41, (7, 7, 1, 1), box(False), False)
add("box_checked", "gui", 42, (8, 7, 1, 1), box(True), False)
add("lock_icon", "gui", 40, (7, 9, 1, 0), lock_icon, False)
add("warning", "gui", 43, (10, 9, 0, 1), warning, False)
add("resize_right", "gui", 44, (7, 7, 3, 3), resize_grip(False), False)
add("resize_left", "gui", 149, (7, 7, 0, 3), resize_grip(True), False)
add("circle_folded", "gui", 147, (8, 8, 1, 1), circle_sign(True), False)
add("circle_unfolded", "gui", 148, (8, 8, 1, 1), circle_sign(False), False)
add("shade", "gui", 151, (7, 6, 1, 2), shade_glyph(False), False)
add("unshade", "gui", 152, (7, 5, 1, 2), shade_glyph(True), False)
add("debug", "gui", 153, (6, 7, 2, 2), debug_box, False)
add("profit_na", "gui", 154, (8, 9, 0, 0), profit((150, 156, 168, 255)), False)
add("profit_negative", "gui", 155, (9, 6, 0, 3), profit(BRICK), False)
add("profit_some", "gui", 156, (9, 6, 0, 3), profit(AMBER), False)
add("profit_lot", "gui", 157, (9, 9, 0, 0), profit(GREEN), False)
add("rating_appalling", "gui", 163, (10, 10, 0, 0), rating(BRICK, -1), False)
add("rating_mediocre", "gui", 164, (10, 10, 0, 0), rating(AMBER, 0), False)
add("rating_good", "gui", 165, (10, 10, 0, 0), rating(GREEN, 1), False)
add("delete_left", "gui", 166, (14, 8, 0, 1), delete_left, False)
add("delete_right", "gui", 167, (14, 8, 0, 1), delete_right, False)
add("defsize", "gui", 168, (8, 8, 0, 0), defsize, False)
add("rename", "gui", 184, (10, 10, 0, 0), rename, False)
add("goto_location", "gui", 185, (11, 10, 0, 0), goto_location, False)

# Cargo icons, 4297..4323 in the base set.
COAL, ORE, COPPER = (54, 58, 66, 255), (150, 110, 96, 255), (176, 112, 70, 255)
for k, (name, size, draw) in enumerate((
        ("passengers", (9, 10, 0, 0), passengers), ("coal", (11, 6, 1, 3), heap(COAL, (96, 102, 112, 255))),
        ("mail", (9, 9, 0, 1), mail), ("oil", (9, 9, 0, 1), barrels(SLATE, AMBER)),
        ("livestock", (9, 7, 0, 2), livestock), ("goods", (10, 10, 0, 0), crate(WOOD, (140, 100, 64, 255))),
        ("grain", (12, 6, 0, 3), heap(AMBER, (250, 214, 130, 255))), ("wood", (11, 9, 0, 1), logs),
        ("iron_ore", (9, 5, 1, 4), heap(ORE, (184, 150, 134, 255))), ("steel", (7, 6, 1, 3), steel),
        ("valuables", (13, 8, 0, 2), bag(AMBER)), ("fruit", (7, 11, 1, 0), fruit),
        ("copper_ore", (11, 5, 1, 4), heap(COPPER, (214, 150, 104, 255))), ("water", (6, 9, 1, 0), drop),
        ("diamonds", (7, 7, 0, 3), diamond), ("food", (10, 9, 0, 1), crate(SAGE, (96, 140, 84, 255))),
        ("paper", (7, 6, 1, 3), paper), ("rubber", (10, 10, 0, 0), barrels((70, 60, 54, 255), SAGE)),
        ("sweets", (11, 9, 2, 1), sweets), ("sugar", (12, 7, 0, 0), sugar), ("toys", (10, 10, 0, 0), toys),
        ("candyfloss", (10, 6, 0, 3), candyfloss), ("fizzy_drinks", (6, 10, 0, 0), can),
        ("toffee", (9, 6, 0, 3), toffee), ("bubbles", (10, 9, 0, 1), bubbles), ("plastic", (9, 6, 1, 3), plastic),
        ("batteries", (6, 10, 0, 0), battery))):
    add(f"cargo_{name}", "base", 4297 + k, size, draw)

# News, group and network status icons.
add("unread_news", "gui", 158, (8, 10, 1, 0), lambda c: (c.rect(3, 2, 37, 48, CREAM, 3),
    [c.rect(9, y, 31, y + 4, STEEL) for y in (10, 20, 30)], c.circle(32, 40, 8, BRICK)))
add("exclusive", "gui", 159, (13, 10, 0, 0), lambda c: c.poly(
    [(4, 44), (4, 12), (18, 26), (32, 6), (46, 26), (60, 12), (60, 44)], AMBER))
add("replace_protect", "gui", 160, (12, 10, 0, 0), lambda c: badge_cycle_off(c, 30, 25, 22))
add("replace_active", "gui", 161, (12, 10, 0, 0), lambda c: badge_cycle(c, 30, 25, 22))
add("chat", "gui", 186, (11, 9, 1, 1), lambda c: (c.rect(2, 2, 53, 32, CREAM, 8),
    c.poly([(12, 30), (26, 30), (10, 44)], CREAM)), False)
add("admin", "gui", 187, (9, 9, 2, 1), lambda c: (c.line([(8, 38), (30, 16)], CREAM, 7), c.ring(32, 13, 9, CREAM, 6)), False)
add("join", "gui", 188, (12, 9, 0, 1), lambda c: (c.circle(18, 12, 9, CREAM), c.rect(4, 24, 32, 44, CREAM, 8),
    c.rect(38, 19, 58, 25, CREAM), c.rect(45, 12, 51, 32, CREAM)), False)
add("player_self", "gui", 189, (7, 9, 2, 1), lambda c: (c.circle(17.5, 12, 9, CREAM), c.rect(3, 24, 32, 44, CREAM, 8)),
    False)
add("player_host", "gui", 190, (9, 7, 1, 3), lambda c: c.poly(
    [(2, 34), (2, 6), (13, 18), (22.5, 2), (32, 18), (43, 6), (43, 34)], CREAM), False)
add("extra_menu", "gui", 191, (2, 8, 3, 1), lambda c: [c.circle(5, y, 4.2, INK) for y in (6, 20, 34)], False)


def render(key, zoom):
    _, _, (w, h, _, _), draw, shadow = SPRITES[key]
    c = Canvas(w, h, zoom)
    draw(c)
    px = (w * zoom, h * zoom)
    glyph = c.im.resize(px, Image.LANCZOS)
    if not shadow:
        return glyph
    sh = Image.new("RGBA", px, SHADOW[:3] + (0,))
    sh.putalpha(glyph.getchannel("A").point(lambda a: a * SHADOW[3] // 255))
    sh = sh.transform(px, Image.AFFINE, (1, 0, -0.5 * zoom, 0, 1, -zoom))
    sh = sh.filter(ImageFilter.GaussianBlur(0.6 * zoom))
    return Image.alpha_composite(sh, glyph)


def main():
    out = sys.argv[1]
    only = set(sys.argv[2:])
    for zoom in (1, 2, 4):
        d = os.path.join(out, f"z{zoom}")
        os.makedirs(d, exist_ok=True)
        for key in SPRITES:
            if only and key not in only:
                continue
            render(key, zoom).save(os.path.join(d, f"{key}.png"))


if __name__ == "__main__":
    main()
