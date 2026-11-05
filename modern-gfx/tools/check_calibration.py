#!/usr/bin/env python3
"""Verify the Blender camera calibration against OpenTTD's tile raster.

For every ground sprite that was rendered (3924-4060, see render_ground.py)
and every zoom level the rendered footprint mask is checked
  1. against the analytic projection (point-in-triangle at pixel centres),
  2. for its crop box: width 64z, height z*(h1+1)-1, top row = anchor + z*yoffs1x,
  3. at 1x, pixel-for-pixel against the OpenGFX reference sprite.

Usage: check_calibration.py <render/ground> <ref/ground>
"""

import json
import math
import os
import sys

from PIL import Image

LEVEL = 1.0 / (2.0 * math.sqrt(6.0))
ANCHOR_Y = 24
S2 = math.sqrt(0.5)
RIGHT = (S2, S2, 0.0)
UP = (-S2 * 0.5, S2 * 0.5, math.sqrt(3) / 2)
CORNERS = {"N": (-0.5, 0.5), "E": (0.5, 0.5), "S": (0.5, -0.5), "W": (-0.5, -0.5)}
SPRITE_SLOPES = list(range(15)) + [0x1D, 0x17, 0x1B, 0x1E]
GROUND_BASES = (3924, 3943, 3962, 3981, 4000, 4023, 4042)
ROUGH_FLAT_VARIANTS = (4019, 4020, 4021, 4022)


def ground_sprites():
    """(sprite, slope) for all temperate ground sprites."""
    out = [(b + k, s) for b in GROUND_BASES for k, s in enumerate(SPRITE_SLOPES)]
    return sorted(out + [(s, 0) for s in ROUGH_FLAT_VARIANTS])


def corner_levels(slope):
    h = {c: (1 if slope & bit else 0) for c, bit in (("W", 1), ("S", 2), ("E", 4), ("N", 8))}
    if slope & 16:
        low = [c for c, v in h.items() if v == 0][0]
        h[{"N": "S", "S": "N", "E": "W", "W": "E"}[low]] = 2
    return h


def project(x, y, z, zoom, width):
    p = math.sqrt(2.0) / (64.0 * zoom)
    rx, ry, rz = x - CORNERS["N"][0], y - CORNERS["N"][1], z
    u = width / 2.0 + (rx * RIGHT[0] + ry * RIGHT[1]) / p
    v = (ANCHOR_Y * zoom - 0.5) - (rx * UP[0] + ry * UP[1] + rz * UP[2]) / p
    return u, v


def analytic_mask(slope, zoom):
    size = 64 * zoom
    h = corner_levels(slope)
    pts = {c: project(*CORNERS[c], h[c] * LEVEL, zoom, size) for c in CORNERS}
    fold = ("W", "E") if h["W"] == h["E"] else ("N", "S")
    others = [c for c in "NESW" if c not in fold]
    tris = [(pts[fold[0]], pts[fold[1]], pts[o]) for o in others]

    def inside(px, py, t):
        (ax, ay), (bx, by), (cx, cy) = t
        d1 = (px - bx) * (ay - by) - (ax - bx) * (py - by)
        d2 = (px - cx) * (by - cy) - (bx - cx) * (py - cy)
        d3 = (px - ax) * (cy - ay) - (cx - ax) * (py - ay)
        neg = d1 < 0 or d2 < 0 or d3 < 0
        pos = d1 > 0 or d2 > 0 or d3 > 0
        return not (neg and pos)

    return [[any(inside(x + 0.5, y + 0.5, t) for t in tris) for x in range(size)] for y in range(size)]


def load_mask(path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    a = im.getchannel("A").load()
    return [[a[x, y] >= 128 for x in range(w)] for y in range(h)]


def bbox(mask):
    ys = [y for y, row in enumerate(mask) if any(row)]
    xs = [x for row in mask for x, v in enumerate(row) if v]
    return min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def main():
    render_dir, ref_dir = sys.argv[1], sys.argv[2]
    ref_meta = json.load(open(os.path.join(ref_dir, "meta.json")))
    failures = 0
    report = {}
    analytic = {}
    for sprite, slope in ground_sprites():
        if not os.path.exists(os.path.join(render_dir, "z1", f"{sprite}_mask.png")):
            continue
        ref = ref_meta[str(sprite)]
        for zoom in (1, 2, 4):
            mask = load_mask(os.path.join(render_dir, f"z{zoom}", f"{sprite}_mask.png"))
            if (slope, zoom) not in analytic:
                analytic[slope, zoom] = analytic_mask(slope, zoom)
            ana = analytic[slope, zoom]
            diff_ana = sum(m != a for mr, ar in zip(mask, ana) for m, a in zip(mr, ar))
            left, top, w, h = bbox(mask)
            exp = (0, ANCHOR_Y * zoom + zoom * ref["y"], 64 * zoom, zoom * (ref["h"] + 1) - 1)
            box_ok = (left, top, w, h) == exp
            diff_ref = None
            if zoom == 1:
                rim = Image.open(os.path.join(ref_dir, f"{sprite}_mask.png")).load()
                diff_ref = sum(
                    mask[top + y][left + x] != (rim[x, y] > 0)
                    for y in range(ref["h"]) for x in range(ref["w"])
                ) if box_ok else -1
            ok = diff_ana == 0 and box_ok and diff_ref in (None, 0)
            failures += not ok
            report[f"{sprite}@{zoom}x"] = dict(
                slope=hex(slope), box=(left, top, w, h), expected=exp,
                diff_analytic=diff_ana, diff_opengfx=diff_ref, ok=ok)
            print(f"{sprite} slope {slope:#04x} {zoom}x  box {w}x{h}@({left},{top}) "
                  f"{'=' if box_ok else '!='} {exp[2]}x{exp[3]}@({exp[0]},{exp[1]})  "
                  f"analytic diff {diff_ana}" + (f"  OpenGFX diff {diff_ref}" if zoom == 1 else "")
                  + ("" if ok else "  <-- FAIL"))
    json.dump(report, open(os.path.join(render_dir, "calibration_report.json"), "w"), indent=1)
    print(f"\n{len(report) - failures}/{len(report)} checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
