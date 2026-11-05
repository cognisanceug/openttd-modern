# Modern Terrain – 32bpp graphics for OpenTTD

A NewGRF that replaces OpenGFX sprites with 32bpp graphics rendered in Blender,
in the style of the "Schienenwerk" map study: isometric low-poly look, soft
light without hard shadows. Gameplay is unchanged. Licence: GPL v2.

Currently covered (temperate):

| Sprites   | Content |
|-----------|---------|
| 3924–4060 | ground: bare soil, 1/3 and 2/3 grass, grass, rough land (+4 flat variants), two rocky sets |
| 4061      | open water (sea, lakes, canals) |
| Action 5 `COAST_TILES_DIAGONAL` | all 18 shore shapes: water, foam line, beach, meadow by height |
| `FEAT_CANALS` `WF_RIVER_SLOPE`, `WF_RIVERBANKS` | rivers: flat water + 4 slopes, and 60 bank pieces (sides, outer/inner corners, flat and sloped); our own definitions replace OpenGFX's |
| Action 5 `OVERLAY_ROCKS` 95–113 | rocks on water and coast |
| 990–1003, Action 5 `FOUNDATIONS_SLOPES_HALFTILES` | all foundations: leveled, inclined, halftile; stone walls, coping on back edges |
| 1005–1036 | rails: straight, short pieces, cross, junction grounds and single overlays, 12 slopes, double pieces |
| 1063–1068, 1408–1413 | rail and road depots (shed with gable roof, garage with roller door); company-colour eaves band via recolour mask |
| 1275–1290, Action 5 `PRE_SIGNAL_SEMAPHORE_PBS` | all signals: light and semaphore; block, entry, exit, combo, path, one-way path; 8 directions, red/green |
| 2634      | concrete (road depot floor, airport apron) |
| 2437–2580 | rail and road bridges of all 13 types: heads, decks, superstructures per section, pillars; steel recolour mask keeps the per-type colours |
| 1069–1086 | rail station: platforms with benches and lamps, station building, roof pillars, gable roof frame and glass |
| 2692–2723 | bus and truck bays: floors, bus shelter, stop sign, warehouse with roller doors, fences |
| Action 5 `ROAD_STOPS`, `ROAD_WAYPOINTS`, `OTTD_GUI` 78–81 | drive-through stops, road waypoints, rail waypoints |
| Action 5 `CATENARY` 0–35 | electrified rail: wires (flat, up, down, depot entrances) and pylons |
| Action 5 `TRAMWAY` 4–45, 56–75, 84–94 | tram tracks on roads and on their own (grassed track), overhead wires and poles with company colour |
| 2365–2372, 2389–2396 | rail and road tunnel portals: stone portal with round arch under a grassy mound |
| 1301–1308 | track fences: low-poly post-and-rail, flat, diagonal and sloped |
| 1313–1350 | roads with pavements (towns) and with grass verges: 19 shapes each incl. slopes and dead ends |
| 1370–1381 | level crossings, open and barred |
| 1576–1715 | all 20 temperate tree bases × 7 growth stages (17 species; 0x6AD repeats the spruce like OpenGFX) |
| 2601–2632, 4790 | objects: transmitter, lighthouse, company statue, owned-land flag, company HQ in all 5 sizes (see *Objects and industries*) |
| 2011–2183, 2293–2340 | temperate industries: coal mine, power station, sawmill, forest, oil refinery, factory, printing works, steel mill, farm, oil wells, bank, iron ore mine; all construction stages and animation frames |

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
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 1576 1715 ref/trees

# textures, renders, checks, GRF
.venv/bin/python tools/make_ground_textures.py render/textures
.venv/bin/python tools/make_infra_textures.py render/textures render/textures/infra   # needs numpy
$B -b --factory-startup -P blender/render_ground.py -- render/ground
$B -b --factory-startup -P blender/render_trees.py -- render/trees
$B -b --factory-startup -P blender/render_foundations.py -- render/foundations
$B -b --factory-startup -P blender/render_fences.py -- render/fences
$B -b --factory-startup -P blender/render_signals.py -- render/signals
$B -b --factory-startup -P blender/render_depots.py -- render/depots
$B -b --factory-startup -P blender/render_tunnels.py -- render/tunnels
$B -b --factory-startup -P blender/render_stations.py -- render/stations
$B -b --factory-startup -P blender/render_catenary.py -- render/catenary
$B -b --factory-startup -P blender/render_bridges.py -- render/bridges   # needs ref/bridges/usage.json
$B -b --factory-startup -P blender/render_objects.py -- render/objects
.venv/bin/python tools/industry_table.py ../src/table ref/industries/industries.json
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 2011 2340 ref/industries   # reference sizes only
.venv/bin/python tools/make_industry_textures.py render/textures/industry   # needs numpy
$B -b --factory-startup -P blender/render_industries.py -- render/industries   # [--only 2013,2150] [--part k/n]
.venv/bin/python tools/check_calibration.py render/ground ref/ground
.venv/bin/python tools/pack_grf.py render ref/ground nml
```

The result is `nml/modern_terrain.grf`. To check it in game without touching
your own OpenTTD config (needs the game built in `../build`):

```sh
SEED=5 tools/ingame_shot.sh modern trees_4x       # -> shots/trees_4x.png
SEED=1 tools/ingame_shot.sh modern rocks_4x keep  # leaves the window open
SEED=2 tools/ingame_shot.sh water coast_4x        # high sea level: coast and coast rocks
SEED=2 tools/ingame_shot.sh town town_4x          # many towns: foundations, and a river
SEED=1 SIZE="4800 3200" tools/infra_shot.sh infra_4x   # InfraTest builds rails, roads, crossings, signals, depots, bridges, tunnels, stations, electrifies (start year 2000)
tools/industry_shot.sh industry_4x   # IndustryTest builds HQ, statue, owned land and every industry (two waves: complete and under construction)
```

## Style

`blender/style.py` reproduces the map study's lighting: base colour times
`clamp(1 + gain·(N·L/L.z − 1), lo, hi)`, light from the study's direction.
Ground textures repeat exactly once per tile so neighbouring tiles join
seamlessly. Shore tiles are coloured by height on the tile (water below 0.05
levels, then foam, wet sand, beach, meadow), so they meet open water and grass
without a seam. Water is static; OpenTTD's palette animation is not used.
Scatter objects (tufts, boulders) are real geometry placed on the slope
surface and cut to the tile outline by the footprint mask. Rails and roads
are drawn as tile-space textures (tools/make_infra_textures.py: ballast,
sleepers, rails; asphalt, kerbs, lane markings) and laid on the flat or
sloped tile in Blender, so slopes and tile joins stay exact.

Bridges are built from the map tools/bridge_usage.py makes of of how table/bridge_land.h
uses each sprite (head, or back/front/pillar of a section of a bridge family).
Steel parts carry palette index 75 in a mask, inside the 70-79 range that the
game's PALETTE_TO_STRUCT_* recolours remap, so shared sprites still appear
oxide, yellow, red, brown, white or concrete-grey per bridge type.

## Objects and industries

Objects (`blender/render_objects.py`) and industries (`blender/render_industries.py`,
models in `blender/industry_models.py`, the open pit in `blender/iron_mine.py`) are
built from the low-poly kit in `blender/build_kit.py`: boxes, prisms, lathes,
rods, roofs and window rows in OpenTTD units (x, y 0–16 per tile, z in height
units, 8 per level). Building sprites are anchored at the bounding box origin
of the draw tables (`table/object_land.h`, `_industry_draw_tile_data`) and carry
their cast shadow like the town houses; ground sprites are the flat tile with
decals and the low parts standing on it.

Industry tiles that the layouts in `table/build_industry.h` always place
together form one unit (factory, printing works and the steel mill's furnace
block 2×2, rolling mill and bank 2×1, coal mine head frame with its winding
house, farmhouse with its barn). A unit is modelled once and cut along the
tile edges for each tile's sprite. `tools/industry_table.py` reads the draw
table; a building sprite used only at stage 0 shows foundations, one used
before stage 3 the lower part in scaffolding, the rest is complete. Animation
frames are separate renders: the head frame's sheaves turn (2013–2015), the
pump jack's beam tilts (2174–2179), the refinery flare burns at stage 3 (2086),
and the six transformer sparks (2055–2060) are rendered alone in the
transformer's frame and packed as child sprites relative to 2054.

Recolouring: sprites the game draws with the industry's random colour
(refinery, factory, printing works, steel mill, farmhouse and barn) or with the
company colour (HQ, statue, owned-land flag; HQ grounds too) carry a recolour
mask on roofs, bands and flags. On all other industry sprites those parts get
fixed colours. The iron ore mine is one 4×4 open pit: every tile renders the
whole pit seen through its own diamond, so the 16 ground sprites join without
seams and the far walls show through the tiles in front of them.

The tiny and small HQs live entirely in ground sprites (as in the original) and
stay low; medium to huge HQs put the building into the N, E and W tiles' full-tile
boxes, the S tile is a forecourt.
