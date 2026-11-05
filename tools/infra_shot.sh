#!/bin/sh
# Photograph rails, roads and level crossings: let the InfraTest game script build
# them around the map centre (where the view starts), wait for the one-minute
# autosave, then load that save and take the 4x screenshot.
# Usage: [SEED=n] [CFG=infra_future] infra_shot.sh <name> [keep]
#   CFG=infra_future starts in 2090, so the script also builds monorail and maglev.
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"
SHOT=normal SIZE="64 64" tools/ingame_shot.sh ${CFG:-infra} infra_build keep >/dev/null
i=0
while [ -z "$(ls "$T/save/autosave" 2>/dev/null)" ] && [ $i -lt 240 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/${CFG:-infra}.cfg" || true
save="$(ls -t "$T"/save/autosave/* | head -1)"
# "big" screenshots start at the view's top-left corner; a wide shot covers the map centre.
LOAD="$save" SIZE="${SIZE:-3600 1800}" tools/ingame_shot.sh modern "$1" $2
