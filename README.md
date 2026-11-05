# Modern Terrain – 32bpp graphics for OpenTTD

A NewGRF that replaces OpenGFX sprites with 32bpp graphics rendered in Blender,
in the style of the "Schienenwerk" map study: isometric low-poly look, soft
light without hard shadows. Gameplay is unchanged. Licence: GPL v2.

Currently covered (temperate; trees in all climates):

| Sprites   | Content |
|-----------|---------|
| 3924–4060 | ground: bare soil, 1/3 and 2/3 grass, grass, rough land (+4 flat variants with their own texture), two rocky sets (own texture and boulders each; the GRF switches the second set on) |
| 4126–4296 | farm fields: 9 stages (ploughed, sown, young, green, turning, ripening, golden, stubble, stubble with round hay bales), 19 slopes each |
| 4493–4568 | snow (sub-arctic) and desert (sub-tropical): 4 densities over the meadow, 19 slopes each; replaced only in their climate (the rest of those climates is still temperate or OpenGFX) |
| 4090–4125 | farm field fences: hedge, hedge with gate, post-and-rail fence, yellow and red flowering hedge, dry stone wall; flat and both slope directions on the SW/SE edge shapes |
| 4061      | open water (sea, lakes, canals) |
| Action 5 `COAST_TILES_DIAGONAL` | all 18 shore shapes: water, foam line, beach, meadow by height |
| `FEAT_CANALS` `WF_RIVER_SLOPE`, `WF_RIVERBANKS` | rivers: flat water + 4 slopes, and 60 bank pieces (sides, outer/inner corners, flat and sloped); our own definitions replace OpenGFX's |
| Action 5 `OVERLAY_ROCKS` 95–113 | rocks on water and coast |
| `FEAT_CANALS` `WF_WATERCLIFFS`, `WF_DIKES`, `WF_LOCKS` | canals: water (the river slopes, flat first), 12 quay edge pieces (meadow, light coping, wall face on the far sides), 24 lock walls (chamber one level above the upper water, mitre gates open in the walls, balance beams, bollards); our own definitions replace OpenGFX's |
| Action 5 `AQUEDUCTS` | aqueducts: stone trough with water on arched spandrels, abutments on the slope, piers |
| 4070–4075 | ship depot: boathouse over two water tiles with gable roof, windows, company-colour eaves band |
| 990–1003, Action 5 `FOUNDATIONS_SLOPES_HALFTILES` | all foundations: leveled, inclined, halftile; stone walls, coping on back edges |
| 1005–1036 | rails: straight, short pieces, cross, junction grounds (ballast beds of the tracks a junction can hold, grass in the corners) and single overlays, 12 slopes, double pieces |
| 1063–1068, 1408–1413 | rail and road depots (shed with gable roof, garage with roller door); company-colour eaves band via recolour mask |
| 1275–1290, Action 5 `PRE_SIGNAL_SEMAPHORE_PBS` | all signals: light and semaphore; block, entry, exit, combo, path, one-way path; 8 directions, red/green |
| 2634      | concrete (road depot floor, airport apron) |
| 2437–2580 | rail and road bridges of all 13 types: heads, decks, superstructures per section, pillars; steel recolour mask keeps the per-type colours |
| 1069–1086 | rail station: platforms with benches and lamps, station building, roof pillars, gable roof frame and glass |
| 2692–2723 | bus and truck bays: floors, bus shelter, stop sign, warehouse with roller doors, fences |
| Action 5 `ROAD_STOPS`, `ROAD_WAYPOINTS`, `OTTD_GUI` 78–81 | drive-through stops, road waypoints, rail waypoints |
| Action 5 `CATENARY` 0–35 | electrified rail: wires (flat, up, down, depot entrances) and pylons |
| Action 5 `TRAMWAY` 4–45, 56–75, 84–94 | tram tracks on roads and on their own (grassed track), overhead wires and poles with company colour; contact wires follow curves, the dead-end loop fits inside the road stub |
| Action 5 `TRAMWAY` 23–26, 49–54, 80–83, 95–118 | tram stops (drive-through parts), tram depot (hall with gable roof and open gate; the track overlay runs inside), wires into tunnels, wires on bridges, tram track on bridge decks without road. Vanilla OpenTTD has no trams, so these are checked with `tools/preview_tiles.py` only |
| 2365–2372, 2389–2396 | rail and road tunnel portals: stone portal with round arch under a grassy mound |
| 1301–1308 | track fences: low-poly post-and-rail, flat, diagonal and sloped |
| 1313–1350 | roads with pavements (towns) and with grass verges: 19 shapes each incl. slopes and dead ends |
| 1370–1381 | level crossings, open and barred |
| 1420–1575, 4404–4417 | all 31 temperate town houses (52 variants incl. the 2×2 stadiums and shopping mall and the 1×2 hotel), with their grounds (lawn with hedge and path, paving, construction site, pitches) and construction stages (foundations, walls with scaffolding); recolourable facades keep their `PALETTE_TO_STRUCT_*` variants via a structure recolour mask; the office block lift (1443) |
| Action 5 `ONE_WAY_ROAD` | one-way markers: a white arrow in each lane (no-entry bars when both directions are closed), flat and on inclined roads |
| 1576–1708 | temperate trees: 19 bases × 7 growth stages (cypress and poplar as slim columns of foliage lumps, dead cypress as a bare spire) |
| 1709–1820 | sub-arctic trees: 8 species, and the same 8 with snow on every upward facet for above the snow line |
| 1821–1946 | sub-tropical trees: 7 palms, 7 rainforest trees (pale bark, lianas), fern, agave, saguaro and barrel cactus |
| 1947–2009 | toyland trees: spinning top, candyfloss, balloon, tyre stack, curly wire, mushroom, striped cone, lollipop, leaf pole |
| 2601–2632, 4790 | objects: transmitter, lighthouse, company statue, owned-land flag, company HQ in all 5 sizes (see *Objects and industries*) |

Every sprite ships as 8bpp fallback plus 32bpp at 1x, 2x and 4x.

## Camera calibration

`blender/ottd_camera.py` holds the projection: orthographic, 30° elevation,
45° azimuth, one tile = 1 Blender unit, one height level = 1/(2√6) ≈ 0.2041.
A flat tile is then 64z × 32z px and, sampled at pixel centres, covers
31/63/127 rows – 256×127 at 4x. Slope triangulation follows
`GetPartialPixelZ()`: the fold runs along the diagonal whose corners are level.

`tools/check_calibration.py` verifies every rendered footprint against the
analytic projection (must be 0 px off) and the OpenGFX sprite boxes. At 1x a
few edge pixels differ from OpenGFX, where the original was rounded by hand.

## Pipeline

Requires Blender 4.5 (`brew install --cask blender`) and NML in a venv:

```sh
python3 -m venv .venv && .venv/bin/pip install nml numpy
B=/Applications/Blender.app/Contents/MacOS/Blender

# reference data from OpenGFX (offsets, sizes, masks) and the bridge sprite usage map
.venv/bin/python tools/bridge_usage.py ../src/table ref/bridges/usage.json
tar -xf ~/Documents/OpenTTD/baseset/opengfx-8.0.tar -C ref
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 3924 4060 ref/ground
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 1576 2009 ref/trees
.venv/bin/python tools/house_table.py ../src/table ref/houses/houses.json
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 4090 4296 ref/fields   # only to compare, not needed to pack

# textures, renders, checks, GRF
.venv/bin/python tools/make_ground_textures.py render/textures
.venv/bin/python tools/make_infra_textures.py render/textures render/textures/infra   # needs numpy
.venv/bin/python tools/make_house_textures.py render/textures ref/houses/houses.json render/textures/houses
$B -b --factory-startup -P blender/render_ground.py -- render/ground
$B -b --factory-startup -P blender/render_ground.py -- render/snow --kinds snow1,snow2,snow3,snow4
$B -b --factory-startup -P blender/render_ground.py -- render/desert --kinds desert1,desert2,desert3,desert4
$B -b --factory-startup -P blender/render_trees.py -- render/trees
$B -b --factory-startup -P blender/render_foundations.py -- render/foundations
$B -b --factory-startup -P blender/render_fences.py -- render/fences
$B -b --factory-startup -P blender/render_farm_fences.py -- render/fences
$B -b --factory-startup -P blender/render_signals.py -- render/signals
$B -b --factory-startup -P blender/render_depots.py -- render/depots
$B -b --factory-startup -P blender/render_tunnels.py -- render/tunnels
$B -b --factory-startup -P blender/render_stations.py -- render/stations
$B -b --factory-startup -P blender/render_catenary.py -- render/catenary
$B -b --factory-startup -P blender/render_bridges.py -- render/bridges   # needs ref/bridges/usage.json
$B -b --factory-startup -P blender/render_houses.py -- render/houses     # --part k/n splits it over processes
$B -b --factory-startup -P blender/render_canals.py -- render/canals     # locks and ship depots
$B -b --factory-startup -P blender/render_aqueducts.py -- render/aqueducts
.venv/bin/python tools/make_transport_textures.py render/textures render/textures/infra   # tram decks, ...
$B -b --factory-startup -P blender/render_infra_extra.py -- render/ground   # sprites from those textures
$B -b --factory-startup -P blender/render_objects.py -- render/objects
.venv/bin/python tools/check_calibration.py render/ground ref/ground
.venv/bin/python tools/preview_tiling.py render/ground ref/ground render/preview_rocky_area.png rocky 2 12   # big area, variants as in game
.venv/bin/python tools/pack_grf.py render ref/ground nml
```

The result is `nml/modern_terrain.grf`. To check it in game without touching
your own OpenTTD config (needs the game built in `../build`):

```sh
SEED=5 tools/ingame_shot.sh modern trees_4x       # -> shots/trees_4x.png
SEED=1 tools/ingame_shot.sh modern rocks_4x keep  # leaves the window open
SEED=2 tools/ingame_shot.sh water coast_4x        # high sea level: coast and coast rocks
SEED=2 tools/ingame_shot.sh town town_4x          # many towns (start year 2000): houses, foundations, and a river
SEED=1 tools/water_shot.sh canals_4x            # WaterTest builds a canal ring, two ship depots, four locks and an aqueduct
SEED=1 SIZE="4800 3200" tools/infra_shot.sh infra_4x   # InfraTest builds rails, roads, one-way roads, crossings, signals, depots, bridges, tunnels, stations, electrifies (start year 2000)
SEED=5 tools/ingame_shot.sh arctic arctic_4x      # sub-arctic: snow ground, trees with and without snow
SEED=5 tools/ingame_shot.sh tropic tropic_4x      # sub-tropical: desert ground, palms, rainforest, cacti
SEED=5 tools/ingame_shot.sh toyland toyland_4x    # toyland trees
LOAD="$PWD/test-home/terrain_test.sav" ZOOM=2 tools/ingame_shot.sh modern terrain_2x   # 2x sprites
SEED=5 tools/terrain_shot.sh terrain_4x   # TerrainTest funds farms and clears a row of land every 8 days: fields, fences, bare soil -> grass (~3 min)
tools/industry_shot.sh objects_4x    # IndustryTest builds HQ, statue, owned land and every industry (two waves: complete and under construction)
```

Most render scripts take `--only prefix,prefix` to re-render a subset.
Parts the game cannot show (trams) are checked by composing renders:

```sh
.venv/bin/python tools/preview_tiles.py render /tmp/trams.png 4 "ground:road1321+overlay:tram12+cat:tram_92+cat:tram_65"
```

## Style

`blender/style.py` reproduces the map study's lighting: base colour times
`clamp(1 + gain·(N·L/L.z − 1), lo, hi)`, light from the study's direction.
Ground textures repeat exactly once per tile so neighbouring tiles join
seamlessly. Where the game has several sprites for one ground type (rocky
land: two sets picked by TileHash bit 0; rough land: four extra flat
variants), each gets its own texture: the variants share a narrow band
along the tile edges and differ inside it, so any two of them meet without a
seam while a large area no longer repeats one pattern. The noise for these
is band-passed white noise on the tile torus (isotropic, no blocky lattice).
Boulders on rocky land are mostly small stones that may come near the tile
edges, so they do not bunch in the tile centres. Farm field furrows repeat a
whole number of times per tile, so the rows of a field continue across tiles. Shore tiles are coloured by height on the tile (water below 0.05
levels, then foam, wet sand, beach, meadow), so they meet open water and grass
without a seam.

Water keeps OpenTTD's palette animation (tools/water_anim.py). A 32bpp sprite
can carry an 8bpp mask; where the mask holds an animated palette index, the
32bpp-anim blitters draw that palette colour, scaled by the pixel's brightness
max(r, g, b) / 128, and the colour cycles with the palette (dark water
245–249, glittery water 250–254). Only the brightness is ours, the hue is the
palette's, so not the whole surface is animated: a ripple pattern of short
wave crests in dark-water indices (their phase falls across each crest, so the
light band travels) and a sprinkle of glitter pixels, each fitted to the
rendered colour's brightness; the rest keeps the rendered RGB. The pattern is
periodic in tile coordinates, so seas, shores, rivers, canals and aqueduct
troughs join without seams. `water_anim.py <render/ground> <ref/ground> out.gif`
simulates the cycle for a patch of sea. Desert and snow shores do not exist in
OpenTTD: DrawShoreTile() uses the one COAST block in every climate, so for the
other climates the meadow on our shores would need a climate switch.
Scatter objects (tufts, boulders) are real geometry placed on the slope
surface and cut to the tile outline by the footprint mask. Rails and roads
are drawn as tile-space textures (tools/make_infra_textures.py: ballast,
sleepers, rails; asphalt, kerbs, lane markings) and laid on the flat or
sloped tile in Blender, so slopes and tile joins stay exact.

Bridges are built from the map tools/bridge_usage.py makes of of how table/bridge_land.h
uses each sprite (head, or back/front/pillar of a section of a bridge family).
The concrete bridge's middle sprites (2493-2498) double as the suspension
bridges' even middle tiles (table/bridge_land.h), so they carry a kerb and a
plain steel railing that suits both, and the suspension cable lands on its top
rail at the neighbouring tiles. Steel parts carry palette index 75 in a mask, inside the 70-79 range that the
game's PALETTE_TO_STRUCT_* recolours remap, so shared sprites still appear
oxide, yellow, red, brown, white or concrete-grey per bridge type.

Town houses come from the original draw table (tools/house_table.py reads
table/town_land.h); blender/house_specs.py maps every sprite to a model and a
construction stage: the finished house, its foundations, or its walls cut at
45 % / 75 % height with scaffolding. Models are built in OpenTTD units from a
small kit (boxes, prisms, gable and hipped roofs, window grids) in
blender/render_houses.py; multi-tile houses are modelled once and cut along
the tile edges. Facades that the game recolours per tile hash carry the same
structure recolour mask as the bridges (index 75 is a brick red, so the plain
variant keeps a brick facade). Grounds are tile-space textures
(tools/make_house_textures.py) laid on the flat tile; buildings cast a soft
shadow onto their own tile.

## Objects

Objects (`blender/render_objects.py`) are built from the low-poly kit in
`blender/build_kit.py`: boxes, prisms, lathes, rods, roofs and window rows in
OpenTTD units (x, y 0–16 per tile, z in height units, 8 per level). Building
sprites are anchored at the bounding box origin of `table/object_land.h` and
carry their cast shadow like the town houses; ground sprites are the flat
tile with decals and the low parts standing on it. The HQ (all of its
sprites, grounds included), the statue and the owned-land flag carry a
company-colour mask on fascias, flags and the statue's figure.

The tiny and small HQs live entirely in ground sprites (as in the original) and
stay low; medium to huge HQs put the building into the N, E and W tiles' full-tile
boxes, the S tile is a forecourt.

## Trees

`blender/render_trees.py` builds every tree base of every climate from a few
low-poly forms (crown, tiers, column, umbrella, layers, spindle, palm, fan,
cactus, barrel; toyland objects have their own builders). The `SPECIES` table
names form, colours per growth stage, dead style and bark for each base.
Height and width of every growth stage come from the OpenGFX sprite it
replaces (`ref/trees/meta.json`), so forests keep their density and skyline.
The snowy sub-arctic set (0x6E5-0x716) is the plain set (0x6AD-0x6DE) plus
snow: after the tree is built, its facets are subdivided once and every facet
turns white with a probability that rises with how far it faces up. Palms and
the toyland leaf pole use arching leaf blades with a raised midrib; leaning
trunks lean to the screen's left as in OpenGFX. The burst toyland balloon
(last stage of 0x7A9) is an empty sprite.
Tree canvases are 64z × 112z px with the drawing origin at (31z, 80z), tall
enough for the 76 px rainforest tree and palm. Toyland ground is not covered yet: there the set's temperate ground
replaces OpenGFX's.
