#!/bin/sh
# Photograph canals, locks, ship depots and aqueducts: let the WaterTest game script
# build them around the map centre (where the view starts), wait for the one-minute
# autosave, then load that save and take the 4x screenshot (like infra_shot.sh).
# Usage: [SEED=n] water_shot.sh <name> [keep]
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"
SHOT=normal SIZE="64 64" tools/ingame_shot.sh waterbuild water_build keep >/dev/null
i=0
while [ -z "$(ls "$T/save/autosave" 2>/dev/null)" ] && [ $i -lt 240 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/waterbuild.cfg" || true
save="$(ls -t "$T"/save/autosave/* | head -1)"
LOAD="$save" SIZE="${SIZE:-3600 1800}" tools/ingame_shot.sh modern "$1" $2
