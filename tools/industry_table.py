#!/usr/bin/env python3
"""Extract the original industry drawing data from table/industry_land.h and build_industry.h.

_industry_draw_tile_data holds 4 entries per industry tile gfx, indexed
gfx << 2 | construction stage (or animation frame for tiles with anim_state).
Each entry has a ground sprite, a building sprite (with palettes), the
building's bounding box (dx, dy, sx, sy, sz) and a draw proc.
build_industry.h gives the tile layouts per industry type; this tool records
for every gfx which industries use it and at which layout positions.

Writes {"ents": [...], "industries": {name: [[[x, y, gfx], ...], ...]},
        "gfx_users": {gfx: [industry names]}, "anim_state": [gfx, ...]}.

Usage: industry_table.py <src/table> <out.json>
"""

import json
import re
import sys


def main():
    table_dir, out = sys.argv[1], sys.argv[2]
    land = open(f"{table_dir}/industry_land.h").read()
    build = open(f"{table_dir}/build_industry.h").read()

    def num(tok):
        tok = tok.split("|")[0].strip()
        return int(tok, 0)

    body = re.search(r"_industry_draw_tile_data\[[^]]*\] = \{(.*?)\n\};", land, re.S).group(1)
    ents = []
    for line in re.findall(r"^\s*M\((.*)\),\s*$", body, re.M):
        raw = [t.strip() for t in line.split(",")]
        ents.append(dict(ground=num(raw[0]), gpal=raw[1], build=num(raw[2]),
                         bcol="PALETTE_MODIFIER_COLOUR" in raw[2], bpal=raw[3],
                         dx=int(raw[4]), dy=int(raw[5]), sx=int(raw[6]), sy=int(raw[7]), sz=int(raw[8]),
                         proc=int(raw[9])))
    assert len(ents) % 4 == 0, len(ents)

    layouts = {}
    for m in re.finditer(r"static const IndustryTileLayout _tile_table_(\w+?)_(\d+) \{(.*?)\n\};", build, re.S):
        tiles = [[int(x), int(y), int(g)] for x, y, g in
                 re.findall(r"\{\{(-?\d+), (-?\d+)\}, (\d+)\}", m.group(3))]
        layouts.setdefault(m.group(1), []).append(tiles)
    users = {}
    for name, lays in layouts.items():
        for lay in lays:
            for _, _, g in lay:
                users.setdefault(g, [])
                if name not in users[g]:
                    users[g].append(name)

    specs = re.search(r"_origin_industry_tile_specs\[[^]]*\] = \{(.*?)\n\};", build, re.S).group(1)
    anim = [i for i, s in enumerate(re.findall(r"^\s*\{(.*)\},", specs, re.M)) if s.rstrip().endswith("true")]
    json.dump(dict(ents=ents, industries=layouts, gfx_users=users, anim_state=anim), open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
