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
| 1087–1118, 1169–1200, 1382–1405 | monorail (one steel rail on a concrete beam with ties) and maglev (wide concrete guideway, two guide rails, reaction rail) in the rail layout, and their level crossings |
| 1145–1168, 1227–1250 | monorail and maglev depots and stations: the rail renders (they hold no track) |
| 2373–2388, 2581–2592, 4324–4403 | monorail and maglev tunnel portals and the bridge sprites only they use (decks with their guideway) |
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
| 1566–1569, 4418–4492, 4569–4625, 4627–4676, 4694–4698 | the town houses of the other climates with their grounds and construction stages: sub-arctic (steep roofs, timber, falu red and ochre; every house also above the snow line with its roofs and garden under snow), sub-tropical (white and ochre walls, flat or low tiled roofs, arcades, roof water tanks, palms; they bring their own sand garden or sandstone paving), toyland (toy houses, a boot, igloo, tepees, teapot, piggy bank and a toy soldier; built in a gift box that is unwrapped) |
| Action 5 `ONE_WAY_ROAD` | one-way markers: a white arrow in each lane (no-entry bars when both directions are closed), flat and on inclined roads |
| 1576–1708 | temperate trees: 19 bases × 7 growth stages (cypress and poplar as slim columns of foliage lumps, dead cypress as a bare spire) |
| 1709–1820 | sub-arctic trees: 8 species, and the same 8 with snow on every upward facet for above the snow line |
| 1821–1946 | sub-tropical trees: 7 palms, 7 rainforest trees (pale bark, lianas), fern, agave, saguaro and barrel cactus |
| 1947–2009 | toyland trees: spinning top, candyfloss, balloon, tyre stack, curly wire, mushroom, striped cone, lollipop, leaf pole |
| 2601–2632, 4790 | objects: transmitter, lighthouse, company statue, owned-land flag, company HQ in all 5 sizes (see *Objects and industries*) |
| 2633, 2635–2691, Action 5 `AIRPORTS`, `OTTD_GUI` 86 | all original airports: aircraft stand, taxiway pieces (apron and grass split as in the original, yellow edge line), runways with edge and threshold lights (exits A–D, end with piano keys; along y for NewGRFs), terminals, round concourse, jetways and passenger bridge, control tower, heliport tower with roof helideck, hangars in four directions (rear wall split off as in the original), fences, radar (12 frames) and windsock (4 frames); small airfield with grass runway and timber buildings; helipads (see *Airports, docks and the oil rig*) |
| 2727–2732, 693 | docks (quay deck at land height on piles, crane and containers on the water part) and the buoy (also the build-buoy toolbar icon, as in the original) |
| 2096–2105 | oil rig: one model cut into three screen-column slices, with its construction stages |
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
.venv/bin/python tools/industry_table.py ../src/table ref/industries/industries.json
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 2011 2340 ref/industries   # reference sizes only
.venv/bin/python tools/make_industry_textures.py render/textures/industry   # needs numpy
$B -b --factory-startup -P blender/render_industries.py -- render/industries   # [--only 2013,2150] [--part k/n]
.venv/bin/python tools/make_airport_textures.py render/textures render/textures/airport 512   # needs numpy
$B -b --factory-startup -P blender/render_airports.py -- render/airports   # [--only b2651,g2645,rig] [--part k/n]
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
SEED=1 SIZE="4800 3200" CFG=infra_future tools/infra_shot.sh guideway_4x   # 2090: also monorail and maglev
SEED=1 SIZE="4800 3200" tools/infra_shot.sh infra_4x   # InfraTest builds rails, roads, one-way roads, crossings, signals, depots, bridges, tunnels, stations, electrifies (start year 2000)
SEED=5 tools/ingame_shot.sh arctic arctic_4x      # sub-arctic: snow ground, trees with and without snow
SEED=5 tools/ingame_shot.sh tropic tropic_4x      # sub-tropical: desert ground, palms, rainforest, cacti
SEED=5 tools/ingame_shot.sh toyland toyland_4x    # toyland trees
SEED=4 SIZE="2400 1600" tools/ingame_shot.sh arctic_town arctic_town_4x    # sub-arctic town above the snow line (SEED=1: below it)
SEED=1 SIZE="2400 1600" tools/ingame_shot.sh tropic_town tropic_town_4x    # sub-tropical houses (SEED=6: the tall ones)
SEED=5 SIZE="2400 1600" tools/ingame_shot.sh toyland_town toyland_town_4x  # toyland houses
LOAD="$PWD/test-home/terrain_test.sav" ZOOM=2 tools/ingame_shot.sh modern terrain_2x   # 2x sprites
SEED=5 tools/terrain_shot.sh terrain_4x   # TerrainTest funds farms and clears a row of land every 8 days: fields, fences, bare soil -> grass (~3 min)
tools/industry_shot.sh industry_4x   # IndustryTest builds HQ, statue, owned land and every industry (two waves: complete and under construction)
tools/airport_shot.sh airport_4x     # AirportTest builds every airport type, docks in four directions, buoys and an oil rig
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
rendered colour's brightness; the rest keeps the rendered RGB. The palette's
water shades are bluer than our teal, so the pattern is a checkerboard: every
other pattern pixel stays static in the complement colour (2 x water minus
its animated neighbour's mean), each pair averages to the teal, and only the
cycle's brightness change shows, moving along the crests. The pattern is
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

The houses of the other climates use the same kit; their models are in
blender/house_climates.py. Sub-arctic houses above the snow line are the same
model with every roof under snow (model name "…@snow"), on snowy grounds made
from the set's snow texture. Finished houses whose original ground is the bare
land (all sub-tropical houses, the sub-arctic hotel and brick block) draw their
own ground inside the building sprite, under the cast shadow. Toyland houses
are built in a gift box: closed at stage 0, unwrapped with the house standing
in it later. All these sprite numbers are only used in their climate, so they
are replaced without climate checks; the one sprite pair a climate base set
replaces (statue and fountain 1454/1455 in sub-tropical) keeps the temperate
drawing, which fits there too.

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

## Airports, docks and the oil rig

`blender/render_airports.py` follows the objects and industries: buildings from the
kit, anchored at the bounding box origin of `table/station_land.h` with their cast
shadow, grounds as tile-space textures (`tools/make_airport_textures.py`) from the
apron and meadow textures, so airport tiles join the apron and the grass around
them. The taxiway pieces 2636–2644 keep the original's split of apron and grass
along screen-vertical or -horizontal lines; runway pieces carry one centre dash per
tile so the line continues. Everything the draw table recolours (fascias, fences,
jetways, hangar doors, windsock, dock crane) carries the company-colour mask.

Hangars are drawn as two sprites, the rear wall behind the aircraft (box at x 0–2)
and the rest in front (box at x 14–16); the four Action 5 hangars are one model
mirrored. Radar (2680–2691) turns 30° per frame, the windsock (2676–2679) swings.
The heliport's roof deck is at z 60, where helicopters land; the old helipad marking
(`OTTD_GUI` 86) is flat, the helistation's (`AIRPORTS` 12) a pad two units high, as
it is drawn at z 2. 2095, the helidepot office, is shared with the oil refinery
and stays the industry render.

Docks: the slope part (2727–2730, one per water direction) is a quay deck at land
height on piles over the slope, the water part (2731/2732, shared by both docks of
an axis) the same deck over the water with crane and containers. The buoy is drawn
from sprite 693, which is also the toolbar icon. The oil rig is modelled once over
its 2×3 tiles; as in the original only the three tiles of the x = 1 row draw it,
each the screen-column slice x − y ≥ 16, 0–16 or < 0 of the model, so the slices
meet without overlap. The helideck sits where helicopters land (31, 9, z 54).

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

## Interface

The fork draws windows in a flat modern style (Game Options › Interface,
"Modern window style", on by default; off gives the classic bevels): even
1 px outlines instead of bevels, flat title bars, and the grey, brown, dark
green, orange, mauve and yellow window colours mapped to slate, sand, sage,
steel blue, lavender and ochre ramps of the palette (`GetWindowColour()` in `src/widget.cpp`). A TrueType
font completes the look, e.g. in `openttd.cfg` under `[misc]`:
`small_font = AvenirNext-Medium`, `medium_font = AvenirNext-Medium`,
`large_font = AvenirNext-DemiBold`, `prefer_sprite_font = false`.

`nml/modern_gui.grf` is a separate NewGRF for interface graphics; it holds the
title screen logo, set by `tools/make_logo.py`, and the 36 main toolbar icons
plus the minimap buttons, flat symbols in the colours of the set drawn by
`tools/make_icons.py`. In the modern style the toolbar's red separators are
dark slate. The title game tries
`baseset/opntitle_modern.dat` first, a town scene that needs Modern Terrain
and Modern Interface enabled for new games; without them the default
`opntitle.dat` is shown.

```sh
.venv/bin/python tools/make_logo.py render/logo
.venv/bin/python tools/make_icons.py render/icons
.venv/bin/python tools/pack_gui_grf.py render nml           # -> nml/modern_gui.grf
SEED=3 tools/title_save.sh title                           # -> shots/title.sav, copy to ../media/baseset/opntitle_modern.dat
tools/gui_shot.sh classic game game_classic                # rail toolbar, town and finance windows
TITLE=shots/title.sav tools/gui_shot.sh modern title title_modern
.venv/bin/python tools/gui_compare.py shots/game_classic.png shots/game_modern.png shots/cmp_game.png
```

The shots use two console commands of the fork: `show_window <name>` opens a
window from a script, and `schedule in-5-seconds <script>` runs a script after
a few seconds of real time, also on the title screen.
