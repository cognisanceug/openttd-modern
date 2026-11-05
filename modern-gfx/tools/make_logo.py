"""Set the letters of the title screen logo "OpenTTD" in a modern typeface.

The game draws the logo from one sprite per letter (O, p, e, n, T, T, D). Each
letter is set here in its full advance box, all with the same height and
baseline, so the game only has to place them side by side. "Open" is white,
"TTD" warm amber, both with a soft shadow so they read on any map.

Usage: python make_logo.py <out_dir>   writes <out_dir>/z{1,2,4}/{O,p,e,n,T,D}.png
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/System/Library/Fonts/Avenir Next.ttc"
FONT_INDEX = 8  # Avenir Next Heavy
SIZE = 52  # font size at 1x; capitals are then about 36 px high
LETTERS = {"O": "Open", "p": "Open", "e": "Open", "n": "Open", "T": "TTD", "D": "TTD"}
COLOURS = {"Open": (250, 250, 246, 255), "TTD": (242, 184, 75, 255)}
SHADOW = (24, 32, 40, 150)
PAD = 4  # room above and below for the shadow at 1x


def font(zoom):
    f = ImageFont.truetype(FONT, SIZE * zoom, index=FONT_INDEX)
    assert "Heavy" in " ".join(f.getname()), f.getname()
    return f


def letter(ch, word, zoom):
    f = font(zoom)
    ascent, descent = f.getmetrics()
    # The box is exactly the advance wide, so the letters join with normal spacing;
    # only the height has room for the shadow.
    pad = PAD * zoom
    w = round(f.getlength(ch))
    h = ascent + descent + 2 * pad
    ink = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ink).text((0, pad), ch, font=f, fill=COLOURS[word])
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((zoom, pad + 2 * zoom), ch, font=f, fill=SHADOW)
    shadow = shadow.filter(ImageFilter.GaussianBlur(1.5 * zoom))
    return Image.alpha_composite(shadow, ink)


def main():
    out = sys.argv[1]
    for zoom in (1, 2, 4):
        d = os.path.join(out, f"z{zoom}")
        os.makedirs(d, exist_ok=True)
        for ch, word in LETTERS.items():
            letter(ch, word, zoom).save(os.path.join(d, f"{ch}.png"))


if __name__ == "__main__":
    main()
