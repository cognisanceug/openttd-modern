"""Town house catalogue of all climates, shared by render_houses.py and tools/make_house_textures.py.

Coordinates are OpenTTD units: x, y 0-16 across a tile (x runs to the lower
left of the screen, y to the lower right; the visible walls face +x and +y),
z in height units (8 per level, 1 px at 1x). A multi-tile house uses one frame
for all its tiles: tile (tx, ty) covers x tx*16..tx*16+16, y ty*16..ty*16+16.

The draw data (ref/houses/houses.json from tools/house_table.py) holds four
construction stages per tile and four variants picked by the tile hash. Every
variant chain (tile, hash) ends in a finished building sprite (stage 3); its
model is looked up in FINAL, or MULTI for multi-tile houses. Earlier stages
show the same model under construction: "found" (foundations, first used at
stage 0) or "partial" (walls going up with scaffolding); toyland houses are
delivered in a gift box instead (closed at stage 0, unwrapped later).

Sub-arctic houses come in pairs below and above the snow line. The snowy one
shares the construction stages and differs in its finished sprite (and mostly
its ground): its model is the plain one with "@snow" appended, which renders
every roof under snow. Finished houses that keep the bare land (3924) as
their ground (all sub-tropical houses, a few sub-arctic ones) carry their own
ground in the building sprite: a tile-space texture of kind "base" drawn
under the house and its shadow.
"""

GRASS_GROUNDS = {3924, 3981}  # bare and grass land, already part of the terrain set
EMPTY_SPRITES = {4407}        # 1x1 px placeholders in the original set

MULTI = {7: "hotel", 20: "stadium1", 32: "stadium2", 40: "mall", 66: "arc_hotel", 68: "arc_hotel@snow",
         74: "arc_twin", 76: "arc_twin@snow", 87: "trop_twin", 99: "toy_boot"}
TILE_OFFSET, BASE = {}, {}
for _base in MULTI:
    _tiles = (((0, 0), (0, 1), (1, 0), (1, 1)) if _base in (20, 32, 40) else
              ((0, 0), (1, 0)) if _base in (74, 76, 87) else ((0, 0), (0, 1)))  # 2x1 along x, 1x2 along y
    for _k, _off in enumerate(_tiles):
        TILE_OFFSET[_base + _k], BASE[_base + _k] = _off, _base

FINAL = {
    1423: "office_tall_a", 1425: "office_tall_b", 1428: "office_gable", 1432: "flats_small", 1436: "church",
    1442: "office_lift", 1446: "house_a", 1506: "bungalow", 1454: "statue", 1455: "fountain",
    1456: "park_pond", 1457: "park_hill", 1460: "office_cube", 1463: "shops_mansard", 1466: "shops_gable",
    1469: "shops_tall", 1472: "modern_tower", 1475: "warehouse", 1478: "office_two",
    1488: "old_house_a", 1490: "old_house_b", 1492: "old_house_c", 1494: "old_house_d", 1496: "cottage",
    1500: "house_b", 1512: "house_c", 1518: "house_d", 1575: "house_e", 1523: "flats_a", 1529: "flats_b",
    1535: "glass_tower", 1551: "band_tower", 1537: "shops_hip", 1539: "shops_two", 1545: "gold_tower",
    1553: "theatre", 1565: "round_tower", 4405: "cinema",
    # Sub-arctic (snowy finals map to the same model with "@snow").
    4569: "office_lift@snow",
    1567: "arc_brick", 1569: "arc_cream", 4571: "arc_brick@snow", 4573: "arc_cream@snow",
    4422: "arc_cottage", 4423: "arc_cottage@snow", 4426: "arc_long", 4427: "arc_long@snow",
    4432: "arc_thatch", 4433: "arc_thatch@snow", 4437: "arc_office_a", 4574: "arc_office_a@snow",
    4441: "arc_office_b", 4575: "arc_office_b@snow", 4445: "arc_office_c", 4576: "arc_office_c@snow",
    4450: "arc_house_c", 4451: "arc_house_c@snow", 4456: "arc_house_d", 4457: "arc_house_d@snow",
    4461: "arc_hall", 4578: "arc_hall@snow", 4465: "arc_church", 4579: "arc_church@snow",
    4469: "arc_house_e", 4581: "arc_house_e@snow", 4470: "arc_tall_brick", 4582: "arc_tall_brick@snow",
    4479: "arc_shops", 4577: "arc_shops@snow", 4484: "arc_office_d", 4585: "arc_office_d@snow",
    # Sub-tropical.
    4590: "trop_villa_a", 4593: "trop_villa_b", 4596: "trop_villa_c", 4597: "trop_huts_a", 4598: "trop_huts_b",
    4599: "trop_huts_c", 4600: "trop_huts_d", 4603: "trop_flats_tall", 4604: "trop_mission", 4607: "trop_villa_d",
    4610: "trop_flats_a", 4613: "trop_flats_b", 4622: "trop_flats_c", 4625: "trop_tower",
    # Toyland.
    4629: "toy_church", 4632: "toy_pavilion", 4635: "toy_cabin", 4638: "toy_dome", 4641: "toy_house_a",
    4644: "toy_flats", 4647: "toy_house_b", 4650: "toy_office", 4659: "toy_tower", 4662: "toy_igloo",
    4665: "toy_tepees", 4668: "toy_cola", 4671: "toy_bar", 4674: "toy_pink", 4694: "toy_statue",
    4697: "toy_teapot", 4698: "toy_piggy",
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
    # Sub-arctic.
    "arc_brick": dict(foot=[(4, 4, 11, 12)], door="x", ground="garden"),
    "arc_cream": dict(foot=[(4, 4, 11, 11)], door="x", ground="garden"),
    "arc_cottage": dict(foot=[(4, 3, 11, 12)], door="x", ground="garden"),
    "arc_long": dict(foot=[(2, 5, 14, 10)], door="x", ground="garden"),
    "arc_thatch": dict(foot=[(3, 3, 11, 9), (3, 9, 8, 13)], door="x", ground="garden_wall"),
    "arc_office_a": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "arc_office_b": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "arc_office_c": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "arc_house_c": dict(foot=[(4, 4, 11, 12)], door="x", ground="garden"),
    "arc_house_d": dict(foot=[(5, 4, 11, 11)], door="x", ground="garden_wall"),
    "arc_hall": dict(foot=[(1, 1, 15, 15)], ground="yard"),
    "arc_church": dict(foot=[(3, 4, 13, 12)], ground="yard"),
    "arc_house_e": dict(foot=[(3, 3, 13, 10)], door="x", ground="garden"),
    "arc_tall_brick": dict(foot=[(1, 1, 15, 15)], ground="paving", base="paving"),
    "arc_hotel": dict(foot=[(2, 4, 14, 30)], ground="paving", base="paving"),
    "arc_shops": dict(foot=[(1, 1, 15, 15)], ground="paving"),
    "arc_office_d": dict(foot=[(2, 2, 14, 14)], ground="paving"),
    "arc_twin": dict(foot=[(6, 3, 28, 13)], ground="paving"),
    # Sub-tropical: the finished houses carry their ground (base).
    "trop_villa_a": dict(foot=[(4, 4, 11, 12)], door="x", ground="desert_garden", base="desert_garden"),
    "trop_villa_b": dict(foot=[(3, 5, 10, 12)], door="x", ground="desert_garden", base="desert_garden"),
    "trop_villa_c": dict(foot=[(4, 5, 10, 11)], door="x", ground="desert_garden", base="desert_garden"),
    "trop_huts_a": dict(foot=[(3, 3, 7, 7), (8, 9, 12, 13)], ground="desert_yard", base="desert_yard"),
    "trop_huts_b": dict(foot=[(2, 3, 6, 7), (7, 2, 11, 6), (8, 9, 13, 13)], ground="desert_yard", base="desert_yard"),
    "trop_huts_c": dict(foot=[(3, 4, 10, 10), (10, 10, 13, 13)], ground="desert_yard", base="desert_yard"),
    "trop_huts_d": dict(foot=[(2, 3, 7, 9), (9, 8, 14, 13)], ground="desert_yard", base="desert_yard"),
    "trop_flats_tall": dict(foot=[(2, 2, 14, 14)], ground="desert_paving", base="desert_paving"),
    "trop_mission": dict(foot=[(2, 3, 14, 12)], ground="desert_paving", base="desert_paving"),
    "trop_villa_d": dict(foot=[(3, 4, 11, 12)], door="x", ground="desert_garden", base="desert_garden"),
    "trop_flats_a": dict(foot=[(2, 2, 14, 14)], ground="desert_paving", base="desert_paving"),
    "trop_flats_b": dict(foot=[(1, 1, 15, 15)], ground="desert_paving", base="desert_paving"),
    "trop_flats_c": dict(foot=[(2, 2, 14, 14)], ground="desert_paving", base="desert_paving"),
    "trop_tower": dict(foot=[(2, 2, 14, 14)], ground="desert_paving", base="desert_paving"),
    "trop_twin": dict(foot=[(2, 2, 30, 14)], ground="desert_paving", base="desert_paving"),
    # Toyland.
    "toy_church": dict(foot=[(4, 5, 12, 11)], ground="toy_lawn"),
    "toy_pavilion": dict(foot=[(3, 3, 13, 13)], ground="toy_lawn"),
    "toy_cabin": dict(foot=[(3, 4, 13, 12)], ground="toy_lawn"),
    "toy_dome": dict(foot=[(3, 3, 13, 13)], ground="toy_lawn"),
    "toy_house_a": dict(foot=[(3, 3, 13, 12)], ground="toy_lawn"),
    "toy_flats": dict(foot=[(3, 3, 13, 13)], ground="toy_lawn"),
    "toy_house_b": dict(foot=[(4, 3, 12, 12)], ground="toy_lawn"),
    "toy_office": dict(foot=[(2, 2, 14, 14)], ground="toy_lawn"),
    "toy_boot": dict(foot=[(4, 5, 12, 12), (5, 12, 12, 28)], ground="toy_lawn"),
    "toy_tower": dict(foot=[(3, 3, 13, 13)], ground="toy_lawn"),
    "toy_igloo": dict(foot=[(3, 3, 13, 13)], ground="toy_lawn"),
    "toy_tepees": dict(foot=[(3, 3, 9, 9), (8, 8, 14, 14)], ground="toy_lawn"),
    "toy_cola": dict(foot=[(3, 3, 13, 13)], ground="toy_lawn"),
    "toy_bar": dict(foot=[(3, 3, 13, 13)], ground="toy_lawn"),
    "toy_pink": dict(foot=[(3, 3, 13, 13)], ground="toy_lawn"),
    "toy_statue": dict(foot=[(5, 5, 11, 11)], ground="toy_lawn"),
    "toy_teapot": dict(foot=[(4, 4, 12, 12)], ground="toy_lawn"),
    "toy_piggy": dict(foot=[(4, 4, 12, 12)], ground="toy_lawn"),
}

# Grounds shared by many houses, by sprite (toyland houses all stand on one of two).
GROUND_KIND = {4675: "toy_lawn", 4676: "toy_paving"}


def spec(model):
    """MODELS entry of a model; a snowy model ("x@snow") has snowy grounds."""
    name, _, snow = model.partition("@")
    s = dict(MODELS[name])
    if snow:
        s["ground"] = s["ground"] + "_snow"
        if "base" in s:
            s["base"] = s["base"] + "_snow"
    return s

PARTIAL_LEVEL = {1: 0.45, 2: 0.75}  # share of the building height standing in a partial stage
LIFT_SPRITE = 1443


def model_of(tile, final_build):
    base = BASE.get(tile, tile)
    return MULTI[base] if base in MULTI else FINAL[final_build]


def chains(data, toy=False):
    """(tile, hash, model, [entry per stage]) for every variant chain (of the toyland houses with toy)."""
    ents = data["ents"]
    out = []
    for h in data["houses"]:
        if "tiles" not in h or (toy is not None and h["toyland"] != toy):
            continue
        for t in h["tiles"]:
            for v in range(4):
                stages = [ents[t * 16 + v * 4 + s] for s in range(4)]
                out.append((t, v, model_of(t, stages[3]["build"]), stages))
    return out


def all_chains(data):
    """(chain, toy) for the houses of every climate, temperate first."""
    return [(c, False) for c in chains(data)] + [(c, True) for c in chains(data, True)]


def building_jobs(data):
    """{sprite: dict(model, tile, stage_kind, level, rc, anchor)} for every building sprite."""
    """toy: a toyland house (gift-box construction stages); base: ground kind drawn in the building sprite."""
    finals = {e["build"] for (_, _, _, st), _ in all_chains(data) for e in st[3:]}
    jobs = {}
    for (t, v, model, stages), toy in all_chains(data):
        for s, e in enumerate(stages):
            b = e["build"]
            if not b or b in EMPTY_SPRITES:
                continue
            kind = "final" if b in finals else "found" if s == 0 else "partial"
            base = spec(model).get("base") if kind == "final" and stages[3]["ground"] in GRASS_GROUNDS else None
            job = jobs.setdefault(b, dict(model=model, tile=t, anchor=(e["dx"], e["dy"]), rc=False, kind=kind,
                                          level=PARTIAL_LEVEL.get(s, 1.0), toy=toy, base=base))
            job["rc"] |= e["bpal"] != "PAL_NONE"
    return jobs


def ground_jobs(data):
    """{sprite: dict(model, tile, kind, props)}; props: the house itself stands in the ground sprite."""
    jobs = {}
    users = {}
    for (t, v, model, stages), toy in all_chains(data):
        for s, e in enumerate(stages):
            g = e["ground"]
            if g in GRASS_GROUNDS:
                continue
            users.setdefault(g, set()).add(model)
            final = g == stages[3]["ground"]
            kind = GROUND_KIND.get(g) or (spec(model)["ground"] if final else "construction")
            jobs.setdefault(g, dict(model=model, tile=t, kind=kind,
                                    props=final and stages[3]["build"] == 0))
    for g, models in users.items():
        if len(models) > 1:
            jobs[g]["model"] = None  # shared plain ground (pavement) without a footprint
    return jobs
