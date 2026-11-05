"""Temperate town house catalogue, shared by render_houses.py and tools/make_house_textures.py.

Coordinates are OpenTTD units: x, y 0-16 across a tile (x runs to the lower
left of the screen, y to the lower right; the visible walls face +x and +y),
z in height units (8 per level, 1 px at 1x). A multi-tile house uses one frame
for all its tiles: tile (tx, ty) covers x tx*16..tx*16+16, y ty*16..ty*16+16.

The draw data (ref/houses/houses.json from tools/house_table.py) holds four
construction stages per tile and four variants picked by the tile hash. Every
variant chain (tile, hash) ends in a finished building sprite (stage 3); its
model is looked up in FINAL, or MULTI for multi-tile houses. Earlier stages
show the same model under construction: "found" (foundations, first used at
stage 0) or "partial" (walls going up with scaffolding).
"""

GRASS_GROUNDS = {3924, 3981}  # bare and grass land, already part of the terrain set
EMPTY_SPRITES = {4407}        # 1x1 px placeholders in the original set

MULTI = {7: "hotel", 20: "stadium1", 32: "stadium2", 40: "mall"}
TILE_OFFSET = {7: (0, 0), 8: (0, 1)}
for _base in (20, 32, 40):
    TILE_OFFSET.update({_base: (0, 0), _base + 1: (0, 1), _base + 2: (1, 0), _base + 3: (1, 1)})
BASE = {t: b for b in (7, 20, 32, 40) for t in range(b, b + 4) if t in TILE_OFFSET}

FINAL = {
    1423: "office_tall_a", 1425: "office_tall_b", 1428: "office_gable", 1432: "flats_small", 1436: "church",
    1442: "office_lift", 1446: "house_a", 1506: "bungalow", 1454: "statue", 1455: "fountain",
    1456: "park_pond", 1457: "park_hill", 1460: "office_cube", 1463: "shops_mansard", 1466: "shops_gable",
    1469: "shops_tall", 1472: "modern_tower", 1475: "warehouse", 1478: "office_two",
    1488: "old_house_a", 1490: "old_house_b", 1492: "old_house_c", 1494: "old_house_d", 1496: "cottage",
    1500: "house_b", 1512: "house_c", 1518: "house_d", 1575: "house_e", 1523: "flats_a", 1529: "flats_b",
    1535: "glass_tower", 1551: "band_tower", 1537: "shops_hip", 1539: "shops_two", 1545: "gold_tower",
    1553: "theatre", 1565: "round_tower", 4405: "cinema",
}

# foot: building footprints (x0, y0, x1, y1) for the ground textures; door: the wall
# ("x" = the +x wall, "y" = the +y wall) a garden path leads to; ground: final ground kind.
MODELS = {
    "office_tall_a": dict(foot=[(1, 1, 14, 14)], ground="yard"),
    "office_tall_b": dict(foot=[(1, 1, 14, 14)], ground="yard"),
    "office_gable": dict(foot=[(1, 1, 14, 15)], ground="yard"),
    "flats_small": dict(foot=[(3, 3, 12, 12)], door="x", ground="garden"),
    "church": dict(foot=[(3, 4, 12, 12), (12, 5.5, 15, 10.5)], door="x", ground="garden"),
    "office_lift": dict(foot=[(1, 1, 14, 14)], ground="paving"),
    "house_a": dict(foot=[(3, 3, 10, 11), (4, 11, 9, 14)], door="x", ground="garden"),
    "bungalow": dict(foot=[(2, 2, 9, 12), (9, 2, 13, 7)], door="x", ground="garden"),
    "hotel": dict(foot=[(1, 1, 8, 31), (8, 24, 15, 31)], ground="paving"),
    "statue": dict(foot=[], ground="paving"),
    "fountain": dict(foot=[], ground="paving"),
    "park_pond": dict(foot=[], ground="grass"),
    "park_hill": dict(foot=[], ground="grass"),
    "office_cube": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "shops_mansard": dict(foot=[(1.5, 3.5, 14.5, 13.5)], ground="paving"),
    "shops_gable": dict(foot=[(3.5, 1.5, 13.5, 14.5)], ground="paving"),
    "shops_tall": dict(foot=[(2.5, 0.5, 14.5, 15.5)], ground="paving"),
    "modern_tower": dict(foot=[(2.5, 0.5, 14.5, 15.5)], ground="paving"),
    "warehouse": dict(foot=[(1.5, 2.5, 15.5, 13.5)], ground="paving"),
    "office_two": dict(foot=[(1, 0.5, 15, 14.5)], ground="paving"),
    "old_house_a": dict(foot=[(4, 4, 11, 12)], door="x", ground="garden"),
    "old_house_b": dict(foot=[(4, 3, 12, 10)], door="y", ground="garden"),
    "old_house_c": dict(foot=[(3, 4, 11, 12)], door="x", ground="garden"),
    "old_house_d": dict(foot=[(4, 4, 10, 13), (10, 7, 13, 11)], door="x", ground="garden"),
    "cottage": dict(foot=[(4, 4, 12, 11)], door="x", ground="garden"),
    "house_b": dict(foot=[(3, 3, 9, 12), (9, 3, 13, 8)], door="x", ground="garden"),
    "house_c": dict(foot=[(3, 4, 11, 11), (5, 11, 10, 14)], door="x", ground="garden"),
    "house_d": dict(foot=[(3, 3, 12, 9), (3, 9, 8, 13)], door="y", ground="garden"),
    "house_e": dict(foot=[(4, 3, 11, 12)], door="x", ground="garden"),
    "flats_a": dict(foot=[(2, 2, 13, 12)], door="x", ground="garden"),
    "flats_b": dict(foot=[(2, 2, 13, 8), (2, 8, 8, 14)], door="x", ground="garden"),
    "glass_tower": dict(foot=[(2, 2, 14, 14)], ground="paving"),
    "band_tower": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "shops_hip": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "shops_two": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "gold_tower": dict(foot=[(2, 2, 14, 14)], ground="paving"),
    "theatre": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "round_tower": dict(foot=[(2, 2, 14, 14)], ground="paving"),
    "cinema": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "stadium1": dict(foot=[], ground="pitch1"),
    "stadium2": dict(foot=[], ground="pitch2"),
    "mall": dict(foot=[(2, 2, 30, 30)], ground="plaza"),
}

PARTIAL_LEVEL = {1: 0.45, 2: 0.75}  # share of the building height standing in a partial stage
LIFT_SPRITE = 1443


def model_of(tile, final_build):
    base = BASE.get(tile, tile)
    return MULTI[base] if base in MULTI else FINAL[final_build]


def chains(data):
    """(tile, hash, model, [entry per stage]) for every temperate variant chain."""
    ents = data["ents"]
    out = []
    for h in data["houses"]:
        if not h["temperate"]:
            continue
        for t in h["tiles"]:
            for v in range(4):
                stages = [ents[t * 16 + v * 4 + s] for s in range(4)]
                out.append((t, v, model_of(t, stages[3]["build"]), stages))
    return out


def building_jobs(data):
    """{sprite: dict(model, tile, stage_kind, level, rc, anchor)} for every building sprite."""
    finals = {e["build"] for _, _, _, st in chains(data) for e in st[3:]}
    jobs = {}
    for t, v, model, stages in chains(data):
        for s, e in enumerate(stages):
            b = e["build"]
            if not b or b in EMPTY_SPRITES:
                continue
            job = jobs.setdefault(b, dict(model=model, tile=t, anchor=(e["dx"], e["dy"]), rc=False,
                                          kind="final" if b in finals else "found" if s == 0 else "partial",
                                          level=PARTIAL_LEVEL.get(s, 1.0)))
            job["rc"] |= e["bpal"] != "PAL_NONE"
    return jobs


def ground_jobs(data):
    """{sprite: dict(model, tile, kind, props)}; props: the house itself stands in the ground sprite."""
    jobs = {}
    users = {}
    for t, v, model, stages in chains(data):
        for s, e in enumerate(stages):
            g = e["ground"]
            if g in GRASS_GROUNDS:
                continue
            users.setdefault(g, set()).add(model)
            final = g == stages[3]["ground"]
            kind = MODELS[model]["ground"] if final else "construction"
            jobs.setdefault(g, dict(model=model, tile=t, kind=kind,
                                    props=final and stages[3]["build"] == 0))
    for g, models in users.items():
        if len(models) > 1:
            jobs[g]["model"] = None  # shared plain ground (pavement) without a footprint
    return jobs
