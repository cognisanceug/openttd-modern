#!/usr/bin/env python3
"""Palette animation for the 32bpp water sprites.

OpenTTD animates water by cycling palette colours (DoPaletteAnimations() in
palette.cpp): indices 245-249 run through five shades of dark blue ("dark
water"), 250-254 through a 15-step sparkle ("glittery water"). A 32bpp sprite
keeps that animation when its mask (the 8bpp companion of the RGBA sheet)
carries such an index: the 32bpp-anim blitters then draw the animated palette
colour, scaled by the pixel's brightness max(r, g, b) / 128.

Only the colour's brightness is ours, its hue is the palette's: the dark-water
shades are a saturated blue (LCh hue ~276) where our water is a soft teal
(~241), and no brightness turns one into the other. So most water pixels keep
their rendered RGB, and only a ripple pattern is animated: wave crests in
dark-water indices whose phase advances across the crest (so the light band
travels like OpenGFX's waves), plus a sparse sprinkle of glitter pixels. The
pattern is dithered: every other pattern pixel (a checkerboard in screen
pixels) stays static and takes the complement 2 * water - animated of its
neighbour's colour (cycle mean for crests, resting shade for glitter). Each
pair averages to the rendered teal, so the blue does not show as streaks, and
what remains visible is the cycle's change of brightness moving along the
crests.

The pattern is a function of the tile coordinates (u, v) in [0, 1), periodic
in both, so neighbouring water tiles, shores and rivers join without seams.

Usage (preview): water_anim.py <render/ground> <ref/ground> <out.gif>
  packs a 4x4 patch of open water at 4x and writes the animation as a GIF.
"""

import math
import random
import sys

from PIL import Image

DARK_WATER = ((32, 68, 112), (36, 72, 116), (40, 76, 120), (44, 80, 124), (48, 84, 128))
GLITTER = ((216, 244, 252), (172, 208, 224), (132, 172, 196), (100, 132, 168), (72, 100, 144),
           (72, 100, 144), (72, 100, 144), (72, 100, 144), (72, 100, 144), (72, 100, 144),
           (72, 100, 144), (72, 100, 144), (100, 132, 168), (132, 172, 196), (172, 208, 224))
DARK_FIRST, GLITTER_FIRST = 245, 250
DARK_MEAN = DARK_WATER[2]
GLITTER_REST = GLITTER[4]

CREST_WIDTH = 0.16     # share of a wave period that is an animated crest
CREST_GAIN = 1.15      # animated crest pixels are this much lighter than the water (their
                       # static partners as much darker); the cycle's swing grows with it
DASH_SHARE = 0.55      # share of a crest that is drawn (crests break into dashes)
GLITTER_SHARE = 0.006  # share of water pixels that sparkle
WAVES = (3, 2)         # wave fronts per tile along u and v
DASHES = (-2, 3)       # dash period along the fronts
_rng = random.Random(4242)
_WOBBLE = [(_rng.randint(1, 3), _rng.randint(-3, 3), _rng.random(), 0.05 + 0.05 * _rng.random()) for _ in range(3)]


def is_water(r, g, b):
    """Rendered water (flat, shaded slope, or shore below the foam line); foam, sand and grass are not."""
    return b >= g and b > 2.3 * r and g > 1.9 * r


def fit_brightness(target, base):
    """Brightness v (1-255) for which base * v / 128 is closest to the target colour."""
    v = 128 * sum(t * c for t, c in zip(target, base)) / sum(c * c for c in base)
    return max(1, min(255, round(v)))


def tile_uv(x, y):
    """Screen offset from the tile's north corner (1x pixels, height 0) -> tile coordinates."""
    return (y - x / 2) / 32, (y + x / 2) / 32


def pattern(u, v, cells):
    """(kind, index offset) for a point on the tile: ('dark', 0-4), ('glitter', 0-4) or None."""
    w = sum(a * math.sin(2 * math.pi * (i * u + j * v + p)) for i, j, p, a in _WOBBLE)
    s = (WAVES[0] * u + WAVES[1] * v + w) % 1.0
    d = (DASHES[0] * u + DASHES[1] * v + 0.7 * w) % 1.0
    cu, cv = int(u % 1.0 * cells), int(v % 1.0 * cells)
    h = random.Random(cu * 1000 + cv).random()
    if h < GLITTER_SHARE:
        return "glitter", int(h / GLITTER_SHARE * 5)
    if s < CREST_WIDTH and d < DASH_SHARE:
        # Phase falls across the crest, so the bright shade moves in wave direction.
        return "dark", 4 - int(s / CREST_WIDTH * 5)
    return None


def animate(sprite, zoom):
    """Add the water animation to a packed sprite (image, xoffs, yoffs[, mask]).

    Returns (image, xoffs, yoffs, mask) with mask an L image of palette indices
    (0 = plain 32bpp pixel). An existing mask is kept where it is set.
    """
    im, xo, yo = sprite[:3]
    im = im.copy()
    old = sprite[3] if len(sprite) > 3 else None
    mask = Image.new("L", im.size, 0)
    px, mp = im.load(), mask.load()
    om = old.load() if old is not None else None
    cells = 32 * zoom  # glitter cells: about one screen pixel each
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 128 or (om is not None and om[x, y]) or not is_water(r, g, b):
                continue
            u, v = tile_uv((x + xo + 0.5) / zoom, (y + yo + 0.5) / zoom)
            hit = pattern(u, v, cells)
            if hit is None:
                continue
            kind, k = hit
            if kind == "dark":
                index, vb = DARK_FIRST + k, min(255, round(CREST_GAIN * fit_brightness((r, g, b), DARK_MEAN)))
                ref = [sum(c) / 5 for c in zip(*(adjust_brightness(d, vb) for d in DARK_WATER))]
            else:
                index, vb = GLITTER_FIRST + k, fit_brightness((r, g, b), GLITTER_REST)
                ref = adjust_brightness(GLITTER_REST, vb)
            if (x + xo + y + yo) % 2:
                # The palette sets the hue of an animated pixel, and its blue is
                # not our teal. So every other pattern pixel stays static and
                # takes the complement of its animated neighbour's colour (the
                # cycle mean for crests, the resting shade for glitter): the
                # pair averages to the rendered water, and only the cycle shows.
                px[x, y] = tuple(max(0, min(255, round(2 * t - c))) for t, c in zip((r, g, b), ref)) + (a,)
                continue
            mp[x, y] = index
            px[x, y] = (vb, vb, vb, a)
    if om is not None:
        mask.paste(old, mask=old.point(lambda m: 255 if m else 0))
    return im, xo, yo, mask


def adjust_brightness(c, v):
    """ReallyAdjustBrightness() from palette.cpp."""
    r, g, b = (ch * v // 128 for ch in c)
    if max(r, g, b) <= 255:
        return r, g, b
    ob = sum(max(0, ch - 255) for ch in (r, g, b)) // 2
    return tuple(255 if ch >= 255 else min(ch + ob * (255 - ch) // 256, 255) for ch in (r, g, b))


def palette_at(step):
    """Animated palette entries 245-254 at a step of the dark-water cycle (glitter runs 3x per 5 steps)."""
    pal = {DARK_FIRST + i: DARK_WATER[(step + i) % 5] for i in range(5)}
    pal.update({GLITTER_FIRST + i: GLITTER[(step + 3 * i) % 15] for i in range(5)})
    return pal


def resolve(im, mask, step):
    """Draw an animated sprite like the 32bpp-anim blitter at one animation step."""
    out = im.copy()
    px, mp = out.load(), mask.load()
    pal = palette_at(step)
    for y in range(out.height):
        for x in range(out.width):
            m = mp[x, y]
            if m:
                r, g, b, a = px[x, y]
                px[x, y] = adjust_brightness(pal[m], max(r, g, b) or 128) + (a,)
    return out


def main():
    import json
    import os
    from pack_grf import ground_sprite
    render_dir, ref_dir, out = sys.argv[1:4]
    meta = json.load(open(os.path.join(ref_dir, "meta.json")))
    zoom = 4
    im, xo, yo, mask = animate(ground_sprite(render_dir, 4061, zoom, meta["3981"]), zoom)
    w, h = 32 * zoom * 5, 16 * zoom * 5
    frames = []
    for step in range(15):
        tile = resolve(im, mask, step)
        canvas = Image.new("RGB", (w, h), (0, 0, 0))
        for i in range(-2, 8):
            for j in range(-2, 8):
                x0, y0 = w // 2 + (j - i) * 32 * zoom, (i + j - 4) * 16 * zoom
                canvas.paste(tile, (x0 + xo, y0 + yo), tile)
        frames.append(canvas)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=150, loop=0)
    frames[0].save(out.rsplit(".", 1)[0] + "_f0.png")


if __name__ == "__main__":
    main()
