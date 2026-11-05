#!/usr/bin/env python3
"""Map every bridge sprite to how the game uses it, from table/bridge_land.h.

For each sprite id: the bridge types (table names) using it, the transport
(rail, road, mono, maglev), and the role: a head (direction the bridge leaves
it, ramp or flat) or a middle element (section, axis, back/front/pillar).
See the comment at the top of bridge_land.h for the table layout.

Usage: bridge_usage.py <src/table> <out.json>
"""

import json
import re
import sys


def main():
    table_dir, out = sys.argv[1], sys.argv[2]
    src = open(f"{table_dir}/bridge_land.h").read()
    sprites = open(f"{table_dir}/sprites.h").read()
    consts = {m.group(1): int(m.group(2), 0)
              for m in re.finditer(r"static const SpriteID (\w+)\s*=\s*(0x[0-9A-Fa-f]+|\d+);", sprites)}
    tables = {}
    for m in re.finditer(r"static const PalSpriteID (_bridge_sprite_table_\w+)\[\] = \{(.*?)\};", src, re.S):
        entries = re.findall(r"\{\s*(\w+)\s*,\s*(\w+)\s*\}", m.group(2))
        tables[m.group(1)] = [(consts.get(a, int(a, 0) if a[0].isdigit() else None), p) for a, p in entries]
    sets = {m.group(1): re.findall(r"(_bridge_sprite_table_\w+)", m.group(2))
            for m in re.finditer(r"static const std::span<const PalSpriteID> (_bridge_sprite_table_\w+)\[\] = \{(.*?)\};",
                                 src, re.S)}
    order = re.search(r"_bridge_sprite_table\[MAX_BRIDGES\] = \{(.*?)\};", src, re.S).group(1)
    types = re.findall(r"(_bridge_sprite_table_\w+)", order)
    pieces = ["north", "south", "inner_north", "inner_south", "middle_odd", "middle_even", "heads"]
    transports = ["rail", "road", "mono", "maglev"]
    usage = {}
    for ti, tname in enumerate(types):
        for pi, table in enumerate(sets[tname]):
            for k, (sid, pal) in enumerate(tables[table]):
                if not sid:
                    continue
                if pieces[pi] == "heads":
                    idx = k % 8
                    role = dict(kind="head", dir=["SW", "SE", "NE", "NW"][idx % 4], ramp=idx >= 4)
                    transport = transports[k // 8]
                else:
                    group, element = divmod(k, 4)
                    if element == 3:
                        continue
                    transport = transports[group // 2]
                    role = dict(kind="middle", piece=pieces[pi], axis="XY"[group % 2],
                                element=["back", "front", "pillar"][element])
                usage.setdefault(sid, []).append(dict(type=ti, tname=tname.replace("_bridge_sprite_table_", ""),
                                                      table=table.replace("_bridge_sprite_table_", ""),
                                                      transport=transport, pal=pal, **role))
    json.dump({str(k): v for k, v in sorted(usage.items())}, open(out, "w"), indent=0)
    print(f"{len(usage)} bridge sprites")


if __name__ == "__main__":
    main()
