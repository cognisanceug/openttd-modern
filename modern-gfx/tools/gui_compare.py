"""Put two interface screenshots side by side (before | after) with a label above each.

Usage: python gui_compare.py <before.png> <after.png> <out.png> [width]
Each shot is scaled to <width> pixels (default 1200) so the pair fits on one screen.
"""
import sys

from PIL import Image, ImageDraw, ImageFont


def main():
    before, after, out = sys.argv[1:4]
    width = int(sys.argv[4]) if len(sys.argv) > 4 else 1200
    shots = []
    for path in (before, after):
        im = Image.open(path).convert("RGB")
        shots.append(im.resize((width, round(im.height * width / im.width)), Image.LANCZOS))
    label_h, gap = 44, 16
    height = max(s.height for s in shots)
    sheet = Image.new("RGB", (2 * width + gap, height + label_h), (238, 238, 232))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", 26)
    except OSError:
        font = ImageFont.load_default()
    for i, (shot, label) in enumerate(zip(shots, ("Klassisch (vorher)", "Modern (nachher)"))):
        x = i * (width + gap)
        draw.text((x + 8, 8), label, fill=(40, 44, 52), font=font)
        sheet.paste(shot, (x, label_h))
    sheet.save(out)


if __name__ == "__main__":
    main()
