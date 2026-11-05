# ModernGFX – 32bpp graphics for OpenTTD

A NewGRF that replaces OpenGFX sprites with 32bpp graphics rendered in Blender,
in the style of the "Schienenwerk" map study: isometric low-poly look, soft
light without hard shadows. Gameplay is unchanged. Licence: GPL v2.

Currently covered (all climates unless noted; effects and disasters still OpenGFX):

| Sprites   | Content |
|-----------|---------|
| 3924–4060 | ground: bare soil, 1/3 and 2/3 grass, grass, rough land (+4 flat variants with their own texture), two rocky sets (own texture and boulders each; the GRF switches the second set on) |
| 4126–4296 | farm fields: 9 stages (ploughed, sown, young, green, turning, ripening, golden, stubble, stubble with round hay bales), 19 slopes each |
| 4493–4568 | snow (sub-arctic) and desert (sub-tropical): 4 densities over the meadow, 19 slopes each; replaced only in their climate (the rest of those climates is still temperate or OpenGFX) |
| 3924–4060 in toyland, `COAST_TILES_DIAGONAL` in toyland | toyland ground: lilac-grey putty for bare soil, felt-green meadow with pastel confetti for the grass stages, rough land with candy pompoms, rocky land with raspberry gravel, toy blocks and marbles; shores with the toyland meadow. Replaced only in toyland, which loads its own ground into the same sprite numbers |
| 1011–1036, 1093–1118, 1175–1200, 1332–1350, 1370–1373, 1382–1385, 1394–1397, 2365–2396, 2636–2644, 2665–2666, 2669–2675, `AIRPORTS` 13–14, `WF_RIVERBANKS`, `WF_DIKES` in toyland | toyland variants of everything else with grass in it: rails, monorail and maglev on their ground, road verges, unpaved level crossings, tunnels (verges and the mound), the airport grass pieces, river banks and canal dikes, all with the toyland meadow. Town roads, paved crossings and the company HQ grounds hold no grass; the toyland houses' lawn (4675) is drawn from the toyland meadow directly |
| 4090–4125 | farm field fences: hedge, hedge with gate, post-and-rail fence, yellow and red flowering hedge, dry stone wall; flat and both slope directions on the SW/SE edge shapes |
| 4061      | open water (sea, lakes, canals) |
| Action 5 `COAST_TILES_DIAGONAL` | all 18 shore shapes: water, foam line, beach, meadow by height |
| `FEAT_CANALS` `WF_RIVER_SLOPE`, `WF_RIVERBANKS` | rivers: flat water + 4 slopes, and 60 bank pieces (sides, outer/inner corners, flat and sloped); our own definitions replace OpenGFX's |
| Action 5 `OVERLAY_ROCKS` 95–113 | rocks on water and coast |
| `FEAT_CANALS` `WF_WATERCLIFFS`, `WF_DIKES`, `WF_LOCKS` | canals: water (the river slopes, flat first), 12 quay edge pieces (meadow, light coping, wall face on the far sides), 24 lock walls (chamber one level above the upper water, mitre gates open in the walls, balance beams, bollards); our own definitions replace OpenGFX's |
| Action 5 `AQUEDUCTS` | aqueducts: stone trough with water on arched spandrels, abutments on the slope, piers |
| 4070–4075 | ship depot: boathouse over two water tiles with gable roof, windows, company-colour eaves band |
| 990–1003, Action 5 `FOUNDATIONS_SLOPES_HALFTILES` | all foundations: leveled, inclined, halftile; stone walls, coping on back edges |
| 1005–1036 | rails: straight, short pieces, cross, junction grounds (ballast beds of the tracks a junction can hold, grass in the corners) and single overlays, 12 slopes, double pieces. The short corner pieces lay their rails, sleepers and ballast at the gauge measured along the tile edge they cross, so they meet straight pieces and each other at the same points |
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
| 2633, 2635–2691, Action 5 `AIRPORTS`, `OTTD_GUI` 86 | all original airports: aircraft stand, taxiway pieces (grass islands with edges along the tile axes, so the yellow edge lines run straight from piece to piece), runways with edge and threshold lights (exits A–D, end with piano keys; along y for NewGRFs), terminals, round concourse, jetways and passenger bridge, control tower, heliport tower with roof helideck, hangars in four directions (rear wall split off as in the original), fences, radar (12 frames) and windsock (4 frames); small airfield with grass runway and timber buildings; helipads (see *Airports, docks and the oil rig*) |
| 2727–2732, 693 | docks (quay deck at land height on piles, crane and containers on the water part) and the buoy (also the build-buoy toolbar icon, as in the original) |
| 2096–2105 | oil rig: one model cut into three screen-column slices, with its construction stages |
| 2011–2183, 2293–2340 | temperate industries: coal mine, power station, sawmill, forest, oil refinery, factory, printing works, steel mill, farm, oil wells, bank, iron ore mine; all construction stages and animation frames |
| 2026–2039, 2184–2292, 2341–2364 | sub-arctic and sub-tropical industries: copper ore mine, food processing plant, paper mill, gold mine, bank, diamond mine, fruit and rubber plantations, water supply, water tower, lumber mill; the snowy forest (2072–2077, sub-arctic only) and the oil wells' sandy ground (2173, sub-tropical only) |
| 4677–4789 | toyland industries: candyfloss forest (2072–2077, toyland only), sweet factory, battery farm, cola wells, toy shop, toy factory, plastic fountains, fizzy drink factory, bubble generator, toffee quarry, sugar mine, with the animated child sprites |
| 3669–3700 | ships: oil tanker, cargo ship, passenger ferry, hovercraft, 8 directions each, company colour on hulls, bands and funnels; in toyland a toy cargo boat loaded with building blocks and a toy paddle steamer replace the cargo ship and ferry (see *Vehicles*) |
| 3741–3900, 3901–3904 | aircraft: all 20 original sprite sets (piston and turboprop airliners, jets of all sizes, supersonic and futuristic types, two helicopters) and the helicopter rotor, 8 directions each, white with company-colour tails, bellies, cheatlines or bodies; in toyland six toy aircraft and a toy rotor replace 3741–3788 and 3901–3904 (see *Vehicles*) |
| 2733–3072 | trains: every original engine (steam with boiler and tender, diesel hoods and boxes, electrics with pantographs, multiple units, high-speed power cars, monorail and maglev) and wagon, 8 directions or 4 for symmetric vehicles, wagons empty and loaded (coal, grain, logs, steel coils, paper reels, iron and copper ore, fruit, rubber); company colour on bodies, bands and tenders; in toyland toy engines and toy cargo wagons replace their sprites (see *Vehicles*) |
| 3092–3667 | road vehicles: all 72 original sprite sets, 8 directions each: buses and lorries in three generations (1930s bonneted, 1970s cab-over, modern raked cab) for every cargo, loaded lorries with their load (coal, grain, ore heaps, logs, steel coils, paper rolls, fruit crates, latex drums), company colour on cabs, bus skirts and body stripes; in toyland 20 toy vehicles replace 3092–3251 (see *Vehicles*) |
| 2040–2044, 3073–3089, 3701–3740, 4748–4762 | effects: crash smoke, diesel exhaust, steam puffs, electric sparks, power station chimney plume (8-frame loop), large and small explosions (fireball, shards, rising smoke), breakdown smoke (4-frame loop), toyland soap bubbles (float, emerge, burst, absorbed) as translucent low-poly puff clusters (see *Effects and disasters*) |
| 3905–3923, 1416–1419 | disasters: zeppelin (flying, crashing in flames, burnt-out wreck), small UFO (lights blinking), large UFO, UFO-destroyer transport, combat jet and attack helicopter (each also firing), small and large submarine in 4 directions; road-works bulldozer in 4 directions |

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
$B -b --factory-startup -P blender/render_ground.py -- render/toyland --kinds toybare,toygrass13,toygrass23,toygrass,toyrough,toyrocky1,toyrocky2,toyshore
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
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 4675 4790 ref/industries/toyland   # reference only (also 2341-2364)
$B -b --factory-startup -P blender/render_industries.py -- render/industries   # [--only 2013,2150] [--part k/n]
for c in arctic tropic toyland; do $B -b --factory-startup -P blender/render_industries.py -- render/industries_$c --climate $c; done
.venv/bin/python tools/make_airport_textures.py render/textures render/textures/airport 512   # needs numpy
$B -b --factory-startup -P blender/render_airports.py -- render/airports   # [--only b2651,g2645,rig] [--part k/n]
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 3669 3700 ref/ships            # reference only
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfxt_toyland.grf 401 416 ref/ships_toyland  # toyland 0xE5D-0xE6C
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 3741 3904 ref/aircraft         # reference only
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfxt_toyland.grf 341 392 ref/aircraft_toyland  # toyland 0xE9D-0xECC, rotors
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 2733 3072 ref/trains          # reference only
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfxt_toyland.grf 761 884 ref/trains_toyland # toyland wagons and engines
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 3092 3667 ref/roadveh          # reference only
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfxt_toyland.grf 601 760 ref/roadveh_toyland  # toyland 0xC14-0xCB3
$B -b --factory-startup -P blender/render_vehicles.py -- render/vehicles   # [--only tanker,jumbo,rotor0 | trains | road] [--zooms 4 --dirs 3,6]
$B -b --factory-startup -P blender/render_effects.py -- render/effects     # [--only steam,explosion] [--zooms 4]
.venv/bin/python tools/grf_extract.py ref/opengfx-8.0/ogfx1_base.grf 3701 3740 ref/effects   # reference only (also 2040-2044, 3073-3089, 3905-3923, 4748-4762)
.venv/bin/python tools/preview_vehicles.py render /tmp/ships.png 4   # placed as in game, next to OpenGFX
.venv/bin/python tools/preview_vehicles.py render /tmp/trains.png 4 jubilee:ref/trains:2905:train w_coal_full:ref/trains:2781:train4   # three in a row on rails
.venv/bin/python tools/preview_vehicles.py render /tmp/rv.png 4 bus1:ref/roadveh:3284:road coal2_l:ref/roadveh:3188:road  # on a lane
.venv/bin/python tools/check_calibration.py render/ground ref/ground
.venv/bin/python tools/preview_tiling.py render/ground ref/ground render/preview_rocky_area.png rocky 2 12   # big area, variants as in game
# toyland variants of the sprites with grass (GFX_GRASS=toy reads render/textures/toyland first, toy_grass for grass)
.venv/bin/python tools/make_infra_textures.py render/textures render/textures/toyland/infra --grass toy_grass
.venv/bin/python tools/make_transport_textures.py render/textures render/textures/toyland/infra --grass toy_grass
.venv/bin/python tools/make_airport_textures.py render/textures render/textures/toyland/airport 512 --grass toy_grass
.venv/bin/python tools/make_ground_textures.py render/textures --toyland   # also the toyland banks and dikes
GFX_GRASS=toy $B -b --factory-startup -P blender/render_ground.py -- render/toyland --kinds infra,riverbank,canaldike --only rail1011,...,rail1036,road1332,...,road1350,cross1370,...,cross1373,bank,dike
GFX_GRASS=toy $B -b --factory-startup -P blender/render_infra_extra.py -- render/toyland --only mono1093,...,mono1118,mglv1175,...,mglv1200,cross1382,...,cross1385,cross1394,...,cross1397
GFX_GRASS=toy $B -b --factory-startup -P blender/render_tunnels.py -- render/toyland/tunnels
GFX_GRASS=toy $B -b --factory-startup -P blender/render_airports.py -- render/toyland/airports --only g2636,...,g2644,g2665,g2666,g2669,...,g2675,gx13,gx14
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
CFG=rail_join SIZE="8000 4400" tools/infra_shot.sh rail_join   # RailJoinTest: zigzags of straight and corner pieces in every orientation, junctions, corner pieces on slopes
SEED=1 SIZE="4800 3200" tools/infra_shot.sh infra_4x   # InfraTest builds rails, roads, one-way roads, crossings, signals, depots, bridges, tunnels, stations, electrifies (start year 2000)
SEED=5 tools/ingame_shot.sh arctic arctic_4x      # sub-arctic: snow ground, trees with and without snow
SEED=5 tools/ingame_shot.sh tropic tropic_4x      # sub-tropical: desert ground, palms, rainforest, cacti
SEED=5 tools/ingame_shot.sh toyland toyland_4x    # toyland trees and ground
SEED=4 SIZE="2400 1600" tools/ingame_shot.sh arctic_town arctic_town_4x    # sub-arctic town above the snow line (SEED=1: below it)
SEED=1 SIZE="2400 1600" tools/ingame_shot.sh tropic_town tropic_town_4x    # sub-tropical houses (SEED=6: the tall ones)
SEED=5 SIZE="2400 1600" tools/ingame_shot.sh toyland_town toyland_town_4x  # toyland houses
LOAD="$PWD/test-home/terrain_test.sav" ZOOM=2 tools/ingame_shot.sh modern terrain_2x   # 2x sprites
SEED=5 tools/terrain_shot.sh terrain_4x   # TerrainTest funds farms and clears a row of land every 8 days: fields, fences, bare soil -> grass (~3 min)
CFG=terrain_toyland SEED=5 tools/terrain_shot.sh toyland_terrain_4x   # the same in toyland (no farms): bare putty -> grass
tools/industry_shot.sh industry_4x   # IndustryTest builds HQ, statue, owned land and every industry (two waves: complete and under construction)
CLIMATE=arctic tools/industry_shot.sh industry_arctic_4x   # the same in sub-arctic (also tropic, toyland)
tools/airport_shot.sh airport_4x     # AirportTest builds every airport type, docks in four directions, buoys and an oil rig
CLIMATE=toyland CFG=infra_future tools/infra_shot.sh toyland_infra_4x   # CLIMATE= generates any of the above in another climate
CLIMATE=toyland tools/airport_shot.sh toyland_airport_4x                # (toyland: rails, roads, tunnels, airports on the toyland meadow)
tools/ship_shot.sh ships_4x          # ShipTest digs a pond with a depot and buoys and buys every ship twice (1990, never expire)
CLIMATE=toyland tools/ship_shot.sh toyland_ships_4x
tools/aircraft_shot.sh aircraft_4x   # AircraftTest: two airports, helistation, heliport, every aircraft (2060, never expire)
CLIMATE=toyland tools/aircraft_shot.sh toyland_aircraft_4x              # YEAR=1960 for an earlier mix
tools/train_shot.sh trains_4x        # TrainTest: rail, electric, monorail and maglev loops, every engine with wagons (2060)
YEAR=1950 tools/train_shot.sh trains_1950_4x                            # CLIMATE=arctic|tropic|toyland for the others
tools/road_shot.sh road_4x           # RoadTest: main road, depots, bus stops, a line per raw cargo, every road vehicle twice (1985)
YEAR=2030 CLIMATE=toyland tools/road_shot.sh toyland_road_4x            # CLIMATE=arctic|tropic|toyland, YEAR=1950 for the first generation
OTTD=<patched build> tools/fx_shot.sh fx_4x   # FxTest: trains, crashes, buses, airport, industries; disasters every 5 days
CLIMATE=toyland OTTD=<patched build> tools/fx_shot.sh toyland_fx_4x     # needs a build with tools/disaster_test.patch
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
simulates the cycle for a patch of sea. Coast tiles never carry snow or
desert: DrawShoreTile() uses the one COAST block in every climate, map
generation keeps desert at least 5 tiles from water, and land sloping down to
the sea is below the snow line. The meadow on our shores matches the set's
grass, which is used in every climate except toyland; toyland gets its own
shores, rendered with the toyland meadow (`toyshore`). The sub-arctic and
sub-tropical grass ground is the temperate meadow, so their verges, banks and
gardens need no variant; in toyland every sprite with grass in it is rendered
again over the toyland meadow (`GFX_GRASS=toy`, see the pipeline above).
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

The other climates follow the same scheme (`blender/industry_climates.py`,
`blender/industry_toyland.py`). The gold mine (4×4) and the diamond mine (3×3)
are open pits like the iron ore mine (`blender/pit_mines.py`); they draw their
tiles partly as building sprites over 2022, which share the ground sprite's
anchor when the box sits at the tile's north corner, so all their sprites are
rendered as whole-pit views through the tile's diamond. Sub-arctic has no snowy
industries in the original: only the forest (above the snow line) gets snow.
Arctic and tropical farms and oil wells keep the temperate sprites, the oil
wells' ground turns to sand in sub-tropical.

Some sprite numbers are shared between climates (`table/landscape_sprite.h`):
2072–2077 are the forest in temperate, the snowy forest in sub-arctic and the
candyfloss forest in toyland; 2173 is the oil wells' ground. `render_industries.py
--climate` renders these variants into `render/industries_<climate>`, and
`tools/pack_industry.py` packs them inside `if (climate == ...)` blocks after the
temperate ones, so temperate stays unchanged.

Toyland is bright: toy bricks with studs, peppermint stripes, candy canes and
candyfloss like the toyland trees. Four draw procs add child sprites that move
by their screen offset (`industry_land.h`): the toy factory's clay ball, stamp and
rubber duck, the toffee quarry's shovel, the sugar mine's shaking sieve with
its growing pile and dust, the bubble generator's bubble. Each child is
modelled where it is at a reference offset, in its parent's frame, and packed
so it lands there; one offset step moves it as in the original ((−2, +1) px is
one unit along x, (0, −1) px one unit up). The eight plastic fountain grounds are
one render.

The tiny and small HQs live entirely in ground sprites (as in the original) and
stay low; medium to huge HQs put the building into the N, E and W tiles' full-tile
boxes, the S tile is a forecourt.

## Airports, docks and the oil rig

`blender/render_airports.py` follows the objects and industries: buildings from the
kit, anchored at the bounding box origin of `table/station_land.h` with their cast
shadow, grounds as tile-space textures (`tools/make_airport_textures.py`) from the
apron and meadow textures, so airport tiles join the apron and the grass around
them. The taxiway pieces 2636–2644 are grass islands on the apron with edges along
the tile axes (the original's screen-vertical and -horizontal splits turn into
sawtooth edges in this style); each piece's islands are chosen for its places in the
city and metropolitan airports, so islands and 8-unit taxiways continue into the
neighbouring pieces. Runway pieces carry one centre dash per tile so the line
continues. Everything the draw table recolours (fascias, fences,
jetways, hangar doors, windsock, dock crane) carries the company-colour mask.

Hangars are drawn as two sprites, the rear wall behind the aircraft (box at x 0–2)
and the rest in front (box at x 14–16); the four Action 5 hangars are one model
mirrored. The fronts reach 14 units back from their box origin, beyond the building
canvas, so they are rendered from the tile's north corner and `pack_airport.py`
moves their offsets to the box origin. Radar (2680–2691) turns 30° per frame, the windsock (2676–2679) swings.
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

## Vehicles

`blender/render_vehicles.py` builds each vehicle once from the kit, in vehicle units
(bow towards +a, z up from the vehicle's z_pos, for ships the water line), and turns it
to the 8 directions of the `Direction` enum (sprite = base + direction). The game draws
a vehicle sprite at `RemapCoords(pos + bounds.origin)`, where `bounds` is set per
direction in `UpdateDeltaXY()` (ships: (-16, -3) along x, (-3, -16) along y, (-3, -3)
diagonally); the renders put the vehicle position at a fixed canvas point and
`render/vehicles/meta.json` stores the canvas pixel of that sprite origin per direction
and zoom, so `tools/pack_vehicles.py` gets the offsets from the crop box. Ships sit on
their path: hull centred on the vehicle position, water line at z_pos (the OpenGFX
sprites along the x axis are a few pixels off their path). Other vehicle types only
need their bounds and canvas in `TYPES` and models in `MODELS`.

Ships use four base sprite sets (`_ship_sprites` in `ship_cmd.cpp`): tanker 0xE55,
cargo ship 0xE5D, ferry 0xE65, hovercraft 0xE6D; the two engines of each kind share
one. Toyland's base graphics load their own cargo ship and ferry into 0xE5D–0xE6C, so a
climate block replaces them again with the toy models (a red tub with building blocks
and a toy wheelhouse; a paddle steamer with striped funnels). Hulls, hull bands and
funnel bands carry the company-colour mask (index 202). Ships have no cast shadow:
the same sprites are drawn in the depot and vehicle windows.

Aircraft (models in `blender/aircraft.py`) have the bounds origin (-1, -1) in every
direction and stand on z_pos = ground + 1, so their wheels touch z = -1. The 20 sprite
sets are 0xE9D–0xF3C (`_aircraft_sprite` in `aircraft_cmd.cpp`); most are shared by
several engines, so each model stands for a type rather than one engine:

| sprite | model | engines |
|---|---|---|
| 0xE9D | high-wing regional jet, four engines, T-tail | Bakewell Luckett LB-8, Yate Aerospace YAe46 |
| 0xEA5 | wide-body with upper-deck hump, four engines | Darwin 300 |
| 0xEAD | supersonic delta with drooped nose | Yate Haugan |
| 0xEB5 | four-propeller airliner, triple fin | Coleman Count |
| 0xEBD | corrugated trimotor with spatted wheels | Sampson U52 |
| 0xEC5 | short-haul jet, rear engines, T-tail | FFP Dart, Bakewell Luckett LB-9 / LB80, YAC 1-11, Darwin 100, Dinger 100 |
| 0xECD | wide-body trijet, third engine in the fin | Bakewell Luckett LB-10 / LB-11, Guru Galaxy |
| 0xED5 | wide-body twinjet | Darwin 200–600, Airtaxi A21–A33 |
| 0xEDD | four-propeller low-wing airliner | Bakewell Cotswald LB-3 |
| 0xEE5 | light helicopter, skids | Tricario Helicopter |
| 0xEED | small supersonic transport, canards, canted fins | FFP Hyperdart 2 |
| 0xEF5 | blended wing body, three engines on top | Dinger 200 |
| 0xEFD | hypersonic needle with aft delta | Dinger 1000 |
| 0xF05 | high-wing shuttle with ducted pusher fans | Yate Z-Shuttle |
| 0xF0D | flying-wing air taxi | AirTaxi A34-1000 |
| 0xF15 | canard jet, forward-swept wing, V-tail | Kelling K6 |
| 0xF1D | box wing | Kelling K7 |
| 0xF25 | truss-braced high wing | Darwin 700 |
| 0xF2D | electric commuter with six props | Kelling K1 |
| 0xF35 | twin-engined helicopter, shrouded tail rotor | Guru X2 Helicopter |

Toyland's base graphics load six toy aircraft into 0xE9D–0xECC and their own rotor, so a
climate block replaces them with a toy biplane (Ploddyphut 100), a chubby high-wing twin
(Ploddyphut 500), a toy jet (Flashbang X1), a fat jumbo with a rainbow fin (Juggerplane
M1), a rocket plane (Flashbang Wizzer) and a bubble helicopter (Powernaut).

The shadow of an aircraft is not a sprite of its own: the game draws the aircraft
sprite again on the ground (bounds origin 0, so 3 px below the parked aircraft) with
the transparent palette, which in 32bpp darkens the ground by a quarter under the
sprite's alpha. It therefore follows the new silhouettes without extra sprites.

The helicopter rotor (3901 stopped, 3902–3904 turning) is a separate vehicle 5 height
units above the body (`ROTOR_Z_OFFSET`), drawn with the same sprite in every direction,
so both helicopters carry their mast on the vehicle position and the rotor plane at the
same height (`HM` in `aircraft.py`). The renderer builds rotors in the body's frame
(type `rotor`, origin (-1, -1, 5), one direction); the packer composes each turning
frame from faded blades over a faint disc (`rotor_disc`) with the hub on top.

### Trains

Trains (models in `blender/trains.py`) use the bounds of `Train::UpdateDeltaXY()` for
the original length of 8 units: the sprite is drawn at `pos + (-1, -1)` in N/E/S/W and
two units further back along the track in NE/SW and SE/NW (type `train`, 8 sprites, or
`train4`, 4 sprites for symmetric vehicles, which the game draws with `direction & 3`).
Each vehicle is centred on its position and 8 units long: bodies end at 3.7, buffers at
3.95, so buffers meet at the vehicle spacing. On the corner-cutting pieces (N/E/S/W) a
vehicle step moves one unit in x and y, so the renderer stretches the length by √2 there,
as the original sprites do; consecutive vehicles then meet on every track piece. Wheels
sit on the rails (gauge ±1.6 units as in `make_infra_textures.py`), bodies stay within
±2.1 of the track centre (platform edges are 3 units away), floors are just above the
platform top (z 2.1) and pantographs reach the contact wire at z 13
(`render_catenary.py`). Monorail and maglev cars hang a skirt down over the beam or
guideway. `tools/preview_vehicles.py` with `:train` / `:train4` draws three vehicles in
a row on rails next to the OpenGFX ones.

The sprite sets are `_engine_sprite_base` + direction (`table/train_sprites.h`); several
engines share a set, multihead rear engines draw the front set turned round, and loaded
wagons add `_wagon_full_adder` (a set of its own per load):

| sprite | model | engines / wagons |
|---|---|---|
| 0xB59 | 4-6-0 tender engine | Chaney 'Jubilee', SH '8P' |
| 0xB61 | streamlined pacific with wedge casing | Ginzu 'A4' |
| 0xB69 | 0-6-0 side-tank engine | Kirby Paul Tank |
| 0xB71 (4) | double-cab diesel | SH/Hendry '25', Floss '47' |
| 0xB75 (4) | double-cab diesel with short noses | UU '37' |
| 0xB79 (4) | box electric, two pantographs | SH '30', SH '40' |
| 0xB7D | high-speed diesel power car | SH '125' (both ends) |
| 0xB85 | 1960s diesel multiple unit car | Manley-Morel DMU |
| 0xB8D | modern DMU car with rounded cab | 'Dash' |
| 0xB95 | long-nosed bullet train power car | 'AsiaStar' |
| 0xB9D | high-speed electric power car | 'T.I.M.' |
| 0xBA5 (4) | symmetric monorail car | 'X2001' |
| 0xBA9 | streamlined monorail cab car | 'Millennium Z1' |
| 0xBB1, 0xBB9 | maglev cab cars, long noses | Lev3 'Pegasus', Lev4 'Chimaera' |
| 0xBC1, 0xBC5 (4) | symmetric maglev cars (company-colour roof; headlight "eye") | Lev1 'Leviathan', Lev2 'Cyclops' |
| 0xBC9, 0xBD1, 0xBD9 | road-switcher hood units, wide-cab ones | CS 2400, Centennial, CS 4000 |
| 0xBE1 | 2-8-0 with cowcatcher, headlamp and bell | Wills 2-8-0 |
| 0xBE9 (4) | centre-cab diesel | Kelling 3100 |
| 0xBED | streamlined cab unit | Turner Turbo (both ends) |
| 0xBF5 (4) | box-cab diesel | MJS 1000 |
| 0xBF9 | small switcher, cab at the rear | MJS 250 |
| 0xAAD–0xB0C | rail wagons: passenger, mail, coal, oil, livestock, goods, food, grain, wood, steel/paper flat, ore hopper, armoured, water, fruit, rubber (+ loaded sets) | all climates |
| 0xB0D–0xB58 | monorail and maglev wagons: the same cargoes with rounded white bodies over a skirt | monorail and maglev |

Some wagons share an empty set: the paper truck uses the steel flat wagon and the copper
ore hopper the iron ore one, each with its own loaded set. The sub-tropic water, fruit and
rubber wagons on monorail and maglev use the rail ones (engine table). Toyland's base
graphics replace the passenger and toy cargo wagons (0xAAD–0xAB0, 0xAB5–0xB00) and seven
engine sets, so a climate block replaces those again: three toy steam engines with fat
boilers and flared funnels (Ploddyphut, Powernaut, Mightymover Choo-Choo), two bubble-cab
toy diesels, a capsule monorail (Wizzowow Z99), a striped rocket maglev (Rocketeer), and
wagons for sugar cubes, candyfloss, toffee, a glass van of bubbles, a cola barrel with
froth, sweets and toys vans, batteries, fizzy drink bottles and plastic. Smoke, steam
and sparks are effects (not drawn here); `trains.EFFECTS` lists the chimney tops,
exhausts and pantograph heads in the model frame for lining them up.

### Road vehicles

Road vehicles (models in `blender/road_vehicles.py`) are drawn at bounds origin + offset
from `RoadVehicle::UpdateDeltaXY`: (-1, -1) for N/E/S/W, (-2, -1) for NE/SW, (-1, -2) for
SE/NW. They drive at 5 and 9 across the tile (`roadveh_movement.h`, mirrored for the other
driving side), while our road texture is centred on 8 with lanes ±1.85 wide (`ROAD_HALF` in
`make_infra_textures.py`), so the renderer moves each model to (x + 1, y + 1): lane centres
6 and 10 on either driving side, inside the bounding box (type `road`, `shift`). Every model
is 7.8 units long (`VEHICLE_LENGTH` 8, no original road vehicle is articulated), 2.6 wide and
about 8 height units high, a little above the depot door and below a two-storey house.

The 72 sprite sets 0xC14–0xE4B are base + direction (`_roadveh_images` in
`roadveh_cmd.cpp`); a lorry at least half full shows base + `_roadveh_full_adder`, so the
loaded lorries are sets of their own. Models are a cab per generation on a cargo body:

| generation | engines | cab |
|---|---|---|
| 1 (1929–1935) | MPS Regal Bus, Balogh, MPS, Witcombe, Talbott, Hereford, Foster, Uhl lorries | bonneted: rounded hood, chrome grille, round fenders and lamps, round roof; wooden bodies |
| 2 (1964–1986) | Hereford Leopard and Foster Bus (one set), Uhl, Reynard, Foster, Craighead, Thomas, Perry lorries | boxy cab-over: flat front, deep windscreen, black grille, white roof cap; ribbed aluminium bodies |
| 3 (2004–2022) | Foster MkII Superbus, DW, Perry, Goss, Moreland, Kelling, Chippy, MPS, RMT lorries | raked cab with light strips, roof deflector, side skirts, tandem rear axle; smooth white bodies with a company-colour stripe |

| body | sets (gen 1 / 2 / 3) | empty → loaded |
|---|---|---|
| bus | 0xCD4 / 0xC14 / 0xD94 | bonneted two-tone bus / city bus with deep windscreen / low-floor bus with roof pods |
| coal tipper | 0xCDC→0xD34 / 0xC1C→0xC74 / 0xD9C→0xDF4 | dark floor → coal heap |
| grain tipper with tarpaulin bows | 0xD0C→0xD3C / 0xC4C→0xC7C / 0xDCC→0xDFC | → golden grain heap (wheat, maize) |
| ore rock-dump body (iron ore and copper ore share the empty set) | 0xD24 / 0xC64 / 0xDE4 | → iron ore 0xD54 / 0xC94 / 0xE14, copper ore 0xD64 / 0xCA4 / 0xE24 |
| stake body | 0xD14→0xD44 / 0xC54→0xC84 / 0xDD4→0xE04 | → stacked logs |
| flatbed (steel and paper share the empty set) | 0xD1C / 0xC5C / 0xDDC | → steel coils 0xD4C / 0xC8C / 0xE0C, paper rolls 0xD5C / 0xC9C / 0xE1C |
| open slatted body | 0xD74→0xD84 / 0xCB4→0xCC4 / 0xE34→0xE44 | → fruit crates |
| low open body | 0xD7C→0xD8C / 0xCBC→0xCCC / 0xE3C→0xE4C | → latex drums (rubber) |
| box vans | mail 0xCE4 / 0xC24 / 0xDA4, goods 0xCFC / 0xC3C / 0xDBC, food 0xD04 / 0xC44 / 0xDC4, armoured 0xD2C / 0xC6C / 0xDEC | one set each: company-colour mail van with a yellow stripe, goods box (curtain-sider in gen 3), refrigerated van with a cooling unit, armoured van with slit windows |
| tankers | oil 0xCEC / 0xC2C / 0xDAC, water 0xD6C / 0xCAC / 0xE2C | one set each: tank with company-colour rings, catwalk and domes |
| livestock | 0xCF4 / 0xC34 / 0xDB4 | one set: slatted body, cattle between the slats |

Toyland's base graphics load its 20 sets into 0xC14–0xCB3 (all three generations of a
toyland lorry share one set), so a climate block replaces them again with toy vehicles: a
round cab with big lamps and a roof beacon, fat wheels with yellow hubs, bright bodies —
a loaf-shaped bus with round windows; tippers loaded with sugar cubes, wrapped toffee and
candyfloss; flatbeds loaded with cola bottles, batteries, fizzy drink cans, plastic drums
and bubbles; a toy van with a teddy on the roof, a mail van with an envelope and a sweet van
with a giant lollipop. Cabs, the toy bus body and the toy mail panels carry the company
colour.

## Effects and disasters

Effect vehicles (`effectvehicle.cpp`) have the bounds origin 0, so their sprite origin is the
effect position itself. `blender/render_effects.py` builds every frame as a cluster of low-poly
lobes with translucent toon materials (the emission of `style.py` mixed with a transparent
shader by the material's alpha) and renders it with that point at the canvas anchor; the
packer crops each frame and offsets it from that point.

| sprites | effect | game timing (ticks per frame) | drawing |
|---|---|---|---|
| 3079–3083 | steam (steam engines) | 16, rising 1 unit / 8 ticks | white puff growing from 5 to 15 px, fading |
| 3073–3078 | diesel exhaust | 8, rising 1 unit / 4 ticks | small grey puff, 3 to 9 px |
| 3084–3089 | electric spark | 3 | blue-white flash with rays, then flying sparks; drawn 3 units above the effect point, at the contact wire |
| 2040–2044 | crash smoke, aircraft breakdown, copper mine | 16, rising 1 unit / 4 ticks | dark puff, lighter and thinner as it grows |
| 3737–3740 | breakdown smoke | 8, looped | column of dark puffs; every frame moves each puff one step up the column, so the loop is seamless |
| 3701–3708 | power station chimney | 8, looped | white plume drifting up and east from the chimney top, 8 puffs, same looping |
| 3709–3724 | large explosion | 4 | fireball flaring up (white core, yellow and orange lobes), burning out red while shards fly out and fall, then dark smoke rising and thinning out |
| 3725–3736 | small explosion | 4 | the same at about half the size |
| 4748–4762 | toyland bubbles | 4 | translucent soap bubble with highlights: floating (3 wobble frames), emerging from the spring (4), bursting into droplets (3), drawn down into the catcher (5) |

The game spawns steam, diesel smoke and sparks at the vehicle centre, 10 units above it
(`ShowVisualEffect`, effect offset 0 for the original engines). A sprite cannot know the
direction, so steam appears a few units behind a chimney near the front of an engine, which
reads as steam trailing the moving engine.

Disaster vehicles (`blender/disasters.py`) have the aircraft bounds origin (-1, -1) and are
rendered with the vehicle renderer (type `disaster`). The game draws one sprite per disaster
vehicle in every direction (`_disaster_images`), so each model is rendered in the direction it
flies: zeppelin SE, combat jet NE, attack helicopter and UFO destroyer SW, the round UFOs
without direction; only the submarines have four sprites (NE, SE, SW, NW). The crashing
zeppelin is pitched nose down with its tail burning, the crashed one is a flattened wreck with
the bare girder rings of the burnt tail on scorched ground. The small UFO alternates with a
darker sprite (lights off), the jet and helicopter with a firing sprite. The attack
helicopter uses the aircraft rotor (3902–3904), so its mast top is at `HM` like the other
helicopters. Disaster shadows are the same sprites drawn with the transparent palette on the
ground, as for aircraft, so they follow the new silhouettes. The road-works bulldozer
(1416–1419, `EV_BULLDOZER`) is an effect vehicle and uses type `effect` (origin 0).

Toyland's base graphics replace none of these sprites, so they need no climate block.

Disasters cannot be started on demand in an unmodified game. `tools/disaster_test.patch` adds
a test hook to `disaster_vehicle.cpp` (environment `OTTD_FX_DISASTERS="0,1,4"` runs these
disasters in turn whatever the year, `OTTD_FX_DISASTER_DAYS=n` the days between them); build
OpenTTD with it in a separate tree and pass that binary to `tools/fx_shot.sh` as `OTTD`. The
patch is for testing only and is not applied to this branch's sources.

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
enough for the 76 px rainforest tree and palm.

## Interface

The fork draws windows in a flat modern style (Game Options › Interface,
"Modern window style", on by default; off gives the classic bevels): even
1 px outlines instead of bevels, flat title bars, and the grey, brown, dark
green, orange, mauve and yellow window colours mapped to slate, sand, sage,
steel blue, lavender and ochre ramps of the palette (`GetWindowColour()` in `src/widget.cpp`).

Text in the modern style:
- Font: the bundled Inter (SIL Open Font License, `media/baseset/Inter-*.ttf`
  with `Inter-LICENSE.txt`) is the default for the small, normal and large
  sizes, without the hard text shadow; the monospace font stays OpenTTD-Mono.
  Fonts set under `[misc]` in `openttd.cfg` (`small_font` etc.) still win,
  `prefer_sprite_font = true` still gives the sprite font, and if Inter is
  missing the classic OpenTTD TrueType fonts are used (`src/fontcache.cpp`).
- Map labels: stations, waypoints and signs are flat rounded labels in the
  company colour with a soft shadow and black or white text, whichever reads
  better; town names and text effects sit on a translucent dark backing
  instead of the pixel shadow; transparent signs keep a light backing
  (`DrawModernViewportString()` in `src/viewport.cpp`).
- News: light cards with a slate header bar holding the close box, the date
  and the town of the news item, a sans-serif headline, and always in
  colour (the "Coloured news appears in" year only applies to the classic
  style); small news is slate like the other windows (`src/news_gui.cpp`).

`nml/modern_gui.grf` is a separate NewGRF for interface graphics; it holds the
title screen logo, set by `tools/make_logo.py`, the 36 main toolbar icons
plus the minimap buttons, and the build menu icons (rail and electric rail,
road, tram, water, airport, landscaping), flat symbols in the colours of the
set drawn by `tools/make_icons.py`; tracks and roads follow the map's
isometric axes. `tools/make_gui_icons.py` draws the other interface sprites
in the same style: the monorail and maglev build icons, the cursors of all
build tools (with the make_icons drawings), the vehicle, depot and group
buttons, the window glyphs (scroll and dropdown arrows, pin, shade, resize,
check boxes), cargo icons and small status icons. Each keeps the size and
offset of its OpenGFX original, so layouts and cursor hotspots stay put.
In the modern style the toolbar's red separators are
dark slate. The title game tries
`baseset/opntitle_modern.dat` first, a town scene that needs ModernGFX
and ModernGFX Interface enabled for new games; without them the default
`opntitle.dat` is shown.

```sh
.venv/bin/python tools/make_logo.py render/logo
.venv/bin/python tools/make_icons.py render/icons
.venv/bin/python tools/make_gui_icons.py render/gui_icons
.venv/bin/python tools/pack_gui_grf.py render nml           # -> nml/modern_gui.grf
SEED=3 tools/title_save.sh title                           # -> shots/title.sav, copy to ../media/baseset/opntitle_modern.dat
tools/gui_shot.sh classic game game_classic                # rail toolbar, town and finance windows
TITLE=shots/title.sav tools/gui_shot.sh modern title title_modern
.venv/bin/python tools/gui_compare.py shots/game_classic.png shots/game_modern.png shots/cmp_game.png
```

`tools/text_shot.sh` shoots the labels, news items and the status bar ticker,
e.g. `ZOOM=4 tools/text_shot.sh modern signs_out station` or
`tools/text_shot.sh classic news station news_thin`; it uses the `show_window`
names `station` (a station and a sign next to the largest town) and
`news_thin`, `news_small`, `news_normal`, `news_vehicle`, `news_company`.

`tools/gui_icons_shot.sh` shoots several window sets in one game, e.g.
`tools/gui_icons_shot.sh modern icons rail:build_rail,build_signals depot:depot,vehicle`.

The shots use two console commands of the fork: `show_window <name>` opens a
window from a script (`WINDOWS="build_water"` picks them for `gui_shot.sh`;
only one build toolbar is open at a time; `depot`, `vehicle` and `orders`
first build a depot with a train next to the largest town; `close_all`
closes the open windows), and `schedule in-5-seconds <script>` runs a script after
a few seconds of real time, also on the title screen.
