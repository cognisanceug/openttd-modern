#!/bin/sh
# Photograph airports, docks, buoys and the oil rig: the AirportTest game script builds
# every original airport type, a pond with docks in all four directions, buoys and an oil
# rig around the map centre. The rig needs about two months to finish its construction
# stages, so the third autosave is loaded and photographed at 4x.
# Usage: [SEED=n] [SIZE="w h"] airport_shot.sh <name> [keep]
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"
SHOT=normal SIZE="64 64" tools/ingame_shot.sh airport airport_build keep >/dev/null
i=0
while [ "$(ls "$T/save/autosave" 2>/dev/null | wc -l)" -lt 3 ] && [ $i -lt 600 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/airport.cfg" || true
save="$(ls -t "$T"/save/autosave/* | head -1)"
LOAD="$save" SIZE="${SIZE:-10000 5000}" tools/ingame_shot.sh modern "$1" $2
