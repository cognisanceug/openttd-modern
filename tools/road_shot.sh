#!/bin/sh
# Photograph road vehicles: the RoadTest game script builds a main road with three depots,
# bus stops and a town, one line per raw cargo from its industry (truck bay, full load) to an
# industry accepting it (drive-through stop), and buys every buildable road vehicle twice
# (start year 1985, vehicles never expire, so earlier generations are there too). Lorries for
# the secondary cargo of a line's far end (steel, paper, fizzy drinks) load there once the raw
# cargo has been delivered. The AUTOSAVES-th autosave (default 4), with lorries loaded and
# empty on the road, at the stops and leaving the depots, is loaded and photographed at 4x.
# CLIMATE=arctic|tropic|toyland builds there, YEAR=n another start year.
# Usage: [SEED=n] [SIZE="w h"] [CLIMATE=...] [YEAR=n] [AUTOSAVES=n] road_shot.sh <name> [keep]
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"; mkdir -p shots
LOG="$PWD/shots/road_build.log" SHOT=normal SIZE="64 64" tools/ingame_shot.sh road road_build keep >/dev/null
i=0
while [ "$(ls "$T/save/autosave" 2>/dev/null | wc -l)" -lt ${AUTOSAVES:-4} ] && [ $i -lt 1200 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/road.cfg" || true
save="$(ls -t "$T"/save/autosave/* | head -1)"
LOAD="$save" SIZE="${SIZE:-10000 5000}" tools/ingame_shot.sh modern "$1" $2
