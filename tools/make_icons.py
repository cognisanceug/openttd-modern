"""Draw the interface icons as flat symbols in the colours of the graphics set.

Each icon is drawn on a 100 x 100 canvas with simple shapes, supersampled and
scaled to the 20 x 20 px toolbar box at 1x (40 and 80 px at 2x and 4x), with a
soft shadow so it reads on the slate toolbar of the modern window style.

Usage: python make_icons.py <out_dir>   writes <out_dir>/z{1,2,4}/<name>.png
"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

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


class Canvas:
    """Drawing in 0..100 icon units on a supersampled RGBA image."""

    def __init__(self, px):
        self.k = px / 100
        self.im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
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

    def punch(self, draw):
        """Cut a hole: draw() paints the hole on a mask with this canvas' methods."""
        hole = Canvas(self.im.width)
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


ICONS = {
    "pause": pause,
    "fastforward": fastforward,
    "settings": settings,
    "save": save,
    "smallmap": smallmap,
    "town": town,
    "buildrail": buildrail,
    "buildroad": buildroad,
}


def render(draw, zoom):
    px = BOX * zoom
    c = Canvas(px * SS)
    draw(c)
    glyph = c.im.resize((px, px), Image.LANCZOS)
    shadow = Image.new("RGBA", (px, px), SHADOW[:3] + (0,))
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
            render(draw, zoom).save(os.path.join(d, f"{name}.png"))


if __name__ == "__main__":
    main()
