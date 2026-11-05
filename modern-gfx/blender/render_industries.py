"""Render the industries of all climates at zoom 1x, 2x and 4x.

Run:  Blender -b --factory-startup -P render_industries.py -- <outdir> [--only 2011,2023] [--part k/n]
      Blender -b --factory-startup -P render_industries.py -- <outdir> --climate arctic|tropic|toyland

The draw data comes from ref/industries/industries.json (tools/industry_table.py).
For every tile gfx of the units in industry_models.py and every construction
stage (or animation frame), the building sprite is rendered from the unit's
model cut to the gfx's tile, anchored at the bounding box origin of
_industry_draw_tile_data; ground sprites are flat tiles with decals and the
low parts standing on them. A building sprite's kind follows the stages that
use it: only at stage 0 'found', used at stage 3 (or animated) 'final',
otherwise 'partial'. Ground sprites of the base set's terrain (3924 bare land)
and of the town (1420 pavement) are not ours.

The power station's transformer sparks (2055-2060, child sprites of 2054)
are rendered alone in the transformer's frame, as s<sprite>_overlay.png.
The iron ore mine (gfx 100-115, ground sprites only) is one 4x4 open pit,
see render_iron_mine().
Models: industry_models.py (temperate), industry_climates.py (sub-arctic and
sub-tropical), industry_toyland.py; the gold and diamond mines are open pits
like the iron ore mine (pit_mines.py). Toyland child sprites (toy factory,
toffee quarry, sugar mine, bubble generator) render in their parent's frame as
c<sprite>_overlay.png, see industry_toyland.CHILDREN.

--climate renders the variants of sprites a climate shares with temperate
(forest 2072-2077 in sub-arctic and toyland, oil well ground 2173 in
sub-tropical, see CLIMATE_SPRITES) into <outdir> instead; pack them inside
if (climate == ...) blocks.
Outputs: b<sprite>_* building sprites and g<sprite>_* grounds, see build_kit.py.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_kit as bk  # noqa: E402
import industry_models as im  # noqa: E402
import industry_climates as ic  # noqa: E402
import industry_toyland as it  # noqa: E402
import iron_mine  # noqa: E402
import pit_mines  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "..", "ref", "industries", "industries.json")
# Base set terrain (3924 bare land, 3981 toyland rough), town pavement, the desert
# under the water tower (4550) and the toyland house grounds (4675, 4676) are not ours.
EXTERNAL_GROUNDS = {3924, 1420, 3962, 3981, 4550, 4675, 4676}
UNITS = {**im.UNITS, **ic.UNITS, **it.UNITS}
CLIMATE_UNITS = {**ic.CLIMATE_UNITS, **it.CLIMATE_UNITS}
CLIMATE_SPRITES = {"arctic": set(range(2072, 2078)), "toyland": set(range(2072, 2078)), "tropic": {2173}}
GENERIC_GROUND = 2022
SPARKS = range(2055, 2061)


def jobs(table, units=None):
    """(building jobs, ground jobs): sprite -> dict(unit, gfx, tile, kind, box)."""
    builds, grounds = {}, {}
    anim = set(table["anim_state"])
    for name, unit in (units or UNITS).items():
        for gfx, tile in unit["tiles"].items():
            ents = table["ents"][gfx * 4:gfx * 4 + 4]
            for which, out in (("build", builds), ("ground", grounds)):
                if unit[which] is None:
                    continue  # drawn elsewhere (pits) or not at all
                seq = [e[which] for e in ents]
                for s, e in enumerate(ents):
                    sprite = seq[s]
                    if not sprite or sprite in out or sprite in EXTERNAL_GROUNDS or sprite in it.ALIASES:
                        continue
                    stages = [i for i, v in enumerate(seq) if v == sprite]
                    if gfx in anim or stages[-1] == 3:
                        kind = "final"
                    elif stages[0] == 0:
                        kind = "found"
                    else:
                        kind = "partial"
                    out[sprite] = dict(unit=name, gfx=gfx, tile=tile, kind=kind, recolour=e["bcol"],
                                       box=(e["dx"], e["dy"], e["sx"], e["sy"], e["sz"]))
    return builds, grounds


def tile_clip(parts, tile):
    tx, ty = tile
    return bk.clip_parts(parts, tx * 16, tx * 16 + 16, ty * 16, ty * 16 + 16)


def render_build(outdir, sprite, job, units):
    unit = units[job["unit"]]
    k = bk.Kit()
    unit["build"](k, job["kind"], sprite)
    tx, ty = job["tile"]
    dx, dy = job["box"][:2]
    shift = (tx * 16 + dx, ty * 16 + dy)
    rc = job["recolour"]
    bk.render_building(outdir, f"b{sprite}", tile_clip(k.parts, job["tile"]), shift, cc=im.CC if rc else (),
                       shadow_parts=k.parts, shadow_tiles=[job["tile"]], fixed=not rc)
    print(f"rendered industry building {sprite} ({job['unit']} {job['kind']})", flush=True)


def render_sparks(outdir, sprite):
    k = bk.Kit()
    im.transformer(k, "final", sprite)
    bk.render_building(outdir, f"s{sprite}", k.parts, (1, 2), shadow_tiles=(), fixed=True)
    print(f"rendered spark {sprite}", flush=True)


def render_child(outdir, sprite, parent_job):
    """Toyland child sprite in the frame of its parent's building sprite."""
    _, _, build = it.CHILDREN[sprite]
    k = bk.Kit()
    build(k, sprite)
    tx, ty = parent_job["tile"]
    dx, dy = parent_job["box"][:2]
    bk.render_building(outdir, f"c{sprite}", k.parts, (tx * 16 + dx, ty * 16 + dy), shadow_tiles=(), fixed=True)
    print(f"rendered child sprite {sprite}", flush=True)


def render_ground(outdir, sprite, job, units):
    tx, ty = job["tile"] if job else (0, 0)
    if (sprite == GENERIC_GROUND and units is UNITS) or job is None:
        base, d, g = "industry/yard", bk.Kit(), bk.Kit()
    else:
        base, d, g = units[job["unit"]]["ground"](sprite, job["kind"])
    decals = bk.clip_parts(d.parts, tx * 16 - 1, tx * 16 + 17, ty * 16 - 1, ty * 16 + 17)
    # Industry grounds are drawn without the industry's colour.
    bk.render_ground(outdir, f"g{sprite}", base, decals, (tx * 16, ty * 16), tile_clip(g.parts, (tx, ty)), fixed=True)
    print(f"rendered industry ground {sprite}", flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv and not argv[0].startswith("--") else os.path.join(os.getcwd(), "render", "industries")
    only = {int(s) for s in argv[argv.index("--only") + 1].split(",")} if "--only" in argv else None
    part, parts = map(int, argv[argv.index("--part") + 1].split("/")) if "--part" in argv else (0, 1)
    climate = argv[argv.index("--climate") + 1] if "--climate" in argv else None
    table = json.load(open(TABLE))
    units = CLIMATE_UNITS[climate] if climate else UNITS
    builds, grounds = jobs(table, units)
    work = [("b", s, j) for s, j in sorted(builds.items())]
    work += [("g", s, j) for s, j in sorted(grounds.items())]
    if climate:
        work = [w for w in work if w[1] in CLIMATE_SPRITES[climate]]
    else:
        work += [("s", s, None) for s in SPARKS]
        work += [("c", s, builds[p]) for s, (p, _, _) in sorted(it.CHILDREN.items())]
        work += [("i", s, None) for s in iron_mine.SPRITES]
        work += [("p", s, None) for s in sorted(pit_mines.SPRITES)]
    for i, (what, sprite, job) in enumerate(work):
        if i % parts != part or (only and sprite not in only):
            continue
        if what == "b":
            render_build(outdir, sprite, job, units)
        elif what == "s":
            render_sparks(outdir, sprite)
        elif what == "c":
            render_child(outdir, sprite, job)
        elif what == "g":
            render_ground(outdir, sprite, job, units)
        elif what == "p":
            pit_mines.render(outdir, sprite)
        else:
            iron_mine.render(outdir, sprite)


if __name__ == "__main__":
    main()
