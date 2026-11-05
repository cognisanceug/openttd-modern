#!/usr/bin/env python3
"""Extract the original town house drawing data from table/town_land.h.

_town_draw_tile_data holds 16 entries per house id, indexed
house << 4 | TileHash2Bit << 2 | construction stage. Each entry has a ground
sprite, a building sprite (with palettes), the building's bounding box
(dx, dy, sx, sy, sz) and a draw proc (1 = the lift of house 4).
_original_house_specs gives name, size and climates per house id; parts of
multi-tile houses follow their base id with empty flags.

Writes {"houses": [{id, name, size, temperate, arctic, snow, tropic, toyland, tiles}], "ents": [...]};
arctic marks sub-arctic houses (snow: the variant above the snow line), "tiles"
lists the house ids drawn for a base house (one per tile).

Usage: house_table.py <src/table> <out.json>
"""

import json
import re
import sys


def main():
    table_dir, out = sys.argv[1], sys.argv[2]
    src = open(f"{table_dir}/town_land.h").read()
    sprites = open(f"{table_dir}/sprites.h").read()
    consts = {m.group(1): int(m.group(2), 0)
              for m in re.finditer(r"static const SpriteID (\w+)\s*=\s*(0x[0-9A-Fa-f]+|\d+);", sprites)}

    def sprite(tok):
        return consts[tok] if tok in consts else int(tok, 0)

    ents = []
    body = re.search(r"_town_draw_tile_data\[\] = \{(.*?)\n\};", src, re.S).group(1)
    for m in re.finditer(r"^\s*M\(([^)]*)\)", body, re.M):
        a = [t.strip() for t in m.group(1).split(",")]
        ents.append(dict(ground=sprite(a[0]), gpal=a[1], build=sprite(a[2]), bpal=a[3],
                         dx=int(a[4]), dy=int(a[5]), sx=int(a[6]), sy=int(a[7]), sz=int(a[8]), proc=a[9]))

    specs = re.search(r"_original_house_specs\[\] = \{(.*?)\n\};", src, re.S).group(1)
    houses = []
    for i, block in enumerate(re.split(r"\n\tMS\(", specs)[1:]):
        name = re.search(r"STR_TOWN_BUILDING_NAME_(\w+)", block).group(1)
        size = re.search(r"Size(\dx\d)", block)
        houses.append(dict(id=i, name=name, size=size.group(1) if size else None,
                           temperate="ClimateTemperate" in block, toyland="ClimateToyland" in block,
                           arctic="ClimateSubarctic" in block, snow="ClimateSubarcticAboveSnow" in block,
                           tropic="ClimateSubtropic" in block))
    tiles_for = {"1x1": 1, "2x1": 2, "1x2": 2, "2x2": 4}
    for h in houses:
        if h["size"]:
            h["tiles"] = list(range(h["id"], h["id"] + tiles_for[h["size"]]))
    assert len(ents) == 16 * len(houses), (len(ents), len(houses))
    json.dump(dict(houses=houses, ents=ents), open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
