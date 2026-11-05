"""Render the ground-level sprites from tools/make_transport_textures.py at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_infra_extra.py -- <render/ground> [--only prefix,prefix]

Like the "infra" kind of render_ground.py: each texture is laid on the flat
tile or the slope it is drawn on, overlays (transparent off the drawn parts)
with the bank material, full tiles with the ground material. Output names
and files are the same (<name>_color.png, <name>_mask.png), so the packer
treats them alike.
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ottd_camera as oc  # noqa: E402
import render_ground as rg  # noqa: E402
import style as st  # noqa: E402

INFRA_TEX = os.path.join(rg.TEXTURES, "infra")
# Bridge road-bits offset -> slope: flat Y, flat X, ramps NE, SE, SW, NW.
DECK_SLOPES = (0, 0, 12, 6, 3, 9)
# One-way markers: slope set (flat, ONEWAY_SLOPE_N, ONEWAY_SLOPE_S) -> slope for road X, road Y.
ONEWAY_SLOPES = ((0, 0), (12, 9), (3, 6))


def jobs():
    """(name, slope, overlay) for every sprite."""
    out = [(f"tramdeck{107 + k}", s, True) for k, s in enumerate(DECK_SLOPES)]
    out += [(f"oneway{k}", ONEWAY_SLOPES[k // 6][k % 6 // 3], True) for k in range(18)]
    # Monorail and maglev in the rail layout: 6 single pieces without ground, then 26 with ground.
    for kind, first in (("mono", 1087), ("mglv", 1169)):
        out += [(f"{kind}{first + k}", 0, True) for k in range(6)]
        out += [(f"{kind}{first + 6 + k}", rg.RAIL_SLOPES.get(k, 0), False) for k in range(26)]
    out += [(f"cross{s}", 0, False) for s in range(1382, 1406)]
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv else os.path.join(os.getcwd(), "render", "ground")
    only = tuple(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    masks = {}
    for name, slope, overlay in jobs():
        if only and not name.startswith(only):
            continue
        path = os.path.join(INFRA_TEX, f"{name}.png")
        for zoom in rg.ZOOMS:
            size = 64 * zoom
            zdir = os.path.join(outdir, f"z{zoom}")
            os.makedirs(zdir, exist_ok=True)
            scene = rg.reset_scene()
            oc.setup_camera(scene, zoom, size, size)
            obj = rg.build_tile(slope, rg.COLOR_OVERSCAN)
            obj.data.materials.append(st.bank_material(path) if overlay else
                                      st.toon_material("infra", image_path=path, params=st.GROUND, extension="EXTEND"))
            rg.render(scene, os.path.join(zdir, f"{name}_color.png"))
            mask_path = os.path.join(zdir, f"{name}_mask.png")
            if (slope, zoom) in masks:
                shutil.copyfile(masks[slope, zoom], mask_path)
                continue
            scene = rg.reset_scene()
            oc.setup_camera(scene, zoom, size, size)
            rg.build_tile(slope, 1.0).data.materials.append(rg.mask_material())
            scene.cycles.samples = 16
            scene.cycles.filter_width = 0.01
            rg.render(scene, mask_path)
            masks[slope, zoom] = mask_path
        print(f"rendered {name} slope {slope:#04x}", flush=True)


if __name__ == "__main__":
    main()
