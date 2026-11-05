#!/bin/sh
# Photograph trains: the TrainTest game script builds loops of rail, electrified rail,
# monorail and maglev (each with two stations, a depot, a hill and diagonal corners) and
# buys every engine available that year with four wagons each, cycling through the wagons;
# primary industries round the first station load the freight trains that wait for a full
# load, so loaded and empty wagons run together. A later autosave is loaded and photographed
# at 4x. YEAR=n another start year (default 2060), CLIMATE=arctic|tropic|toyland.
# Usage: [SEED=n] [SIZE="w h"] [CLIMATE=c] [YEAR=n] [AUTOSAVES=n (default 4)] train_shot.sh <name> [keep]
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"
LOG="$PWD/shots/train_build.log" SHOT=normal SIZE="64 64" tools/ingame_shot.sh train train_build keep >/dev/null
i=0
while [ "$(ls "$T/save/autosave" 2>/dev/null | wc -l)" -lt ${AUTOSAVES:-4} ] && [ $i -lt 900 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/train.cfg" || true
save="$(ls -t "$T"/save/autosave/* | head -1)"
LOAD="$save" SIZE="${SIZE:-10000 5000}" tools/ingame_shot.sh modern "$1" $2
