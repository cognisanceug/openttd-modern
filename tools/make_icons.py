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
