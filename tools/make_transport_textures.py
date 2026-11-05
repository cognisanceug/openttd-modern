#!/usr/bin/env python3
"""Tile-space textures for the transport parts added after make_infra_textures.py.

Same conventions as make_infra_textures.py (x, y in -0.5..0.5, Blender axes,
row 0 is y = +0.5; RGB 0-255, alpha 0-1) and its helpers. Overlays are
transparent off the drawn parts.

Written to <outdir>/<name>.png:
  tramdeck<107-112>  tram track on a bridge deck without road (TRAMWAY 107-112): asphalt band
                     covering the deck's lane markings, grooved rails; axis Y, X, then the ramps
  oneway<0-17>       one-way road markers (Action 5 ONE_WAY_ROAD): per slope set (flat, rising to the
                     north, rising to the south) road X then Y, each with one-way traffic one way, the other,
                     or none (no-entry bars); a white arrow in each lane

Usage: make_transport_textures.py <render/textures> <outdir> [size]
"""

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_infra_textures as mi  # noqa: E402

# Bridge road-bits offset (0 = axis Y, 1 = axis X, 2-5 = flat head ramps NE, SE, SW, NW) -> arms.
DECK_ARMS = (("NW", "SE"), ("SW", "NE"), ("SW", "NE"), ("NW", "SE"), ("SW", "NE"), ("NW", "SE"))


def tram_deck_texture(n, arms, noise):
    x, y = mi.grid(n)
    img = np.zeros((n, n, 4))
    _, _, s = mi.arm_distance(x, y, arms[0])
    band = 1 - mi.smooth(mi.ROAD_HALF - 0.03, mi.ROAD_HALF - 0.02, np.abs(s))
    mi.blend(img, mi.ASPHALT * (1 + (noise[..., None] - 0.5) * 0.06), band)
    rails = mi.tram_texture(n, None, arms, True, noise)
    mi.blend(img, rails[..., :3], rails[..., 3])
    return img


def oneway_texture(n, axis, flow):
    """White arrows in both lanes; flow = disallowed directions - 1 (0, 1, 2 = both: no-entry bars).

    Flow 0 (DisallowedRoadDirection::Southbound) leaves the trackdirs X_SW and Y_NW
    (drd_to_multiplier in road_cmd.cpp), so its arrows point SW resp. NW; flow 1 the other way.
    """
    x, y = mi.grid(n)
    _, t, s = mi.arm_distance(x, y, "SW" if axis == "X" else "NW")  # t grows in the flow-0 direction
    if flow == 1:
        t, s = -t, -s
    img = np.zeros((n, n, 4))
    shape = np.zeros((n, n))
    for lane in (-0.11, 0.11):
        d = s - lane
        if flow == 2:
            shape = np.maximum(shape, ((np.abs(d) < 0.055) & (np.abs(t) < 0.018)).astype(float))
            continue
        shaft = (np.abs(d) < 0.013) & (t > -0.13) & (t < 0.03)
        head = (t >= 0.03) & (t < 0.12) & (np.abs(d) < 0.05 * (0.12 - t) / 0.09)
        shape = np.maximum(shape, (shaft | head).astype(float))
    mi.blend(img, mi.MARKING, shape)
    return img


def main():
    outdir = sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    os.makedirs(outdir, exist_ok=True)
    rng = np.random.default_rng(1005)
    speck = rng.random((n // 4, n // 4))
    noise = np.asarray(Image.fromarray((speck * 255).astype(np.uint8)).resize((n, n), Image.NEAREST), dtype=float) / 255
    for k, arms in enumerate(DECK_ARMS):
        mi.save(tram_deck_texture(n, arms, noise), os.path.join(outdir, f"tramdeck{107 + k}.png"))
    for k in range(18):
        mi.save(oneway_texture(n, "XY"[k % 6 // 3], k % 3), os.path.join(outdir, f"oneway{k}.png"))
    print(f"wrote transport textures to {outdir}")


if __name__ == "__main__":
    main()
