#!/bin/sh
# Photograph farm fields, fences and the grass regrowth stages: the TerrainTest
# game script funds farms and clears a row of land every eight days around the
# map centre (where the view starts); after the third one-minute autosave (about
# 80 game days, so the first rows have grown back) load that save and take the
# 4x screenshot.
# Usage: [SEED=n] [SAVES=3] terrain_shot.sh <name> [keep]
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"
SHOT=normal SIZE="64 64" tools/ingame_shot.sh terrain terrain_build keep >/dev/null
i=0
while [ "$(ls "$T/save/autosave" 2>/dev/null | wc -l)" -lt "${SAVES:-3}" ] && [ $i -lt 600 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/terrain.cfg" || true
save="$(ls -t "$T"/save/autosave/* | head -1)"
LOAD="$save" SIZE="${SIZE:-3600 1800}" tools/ingame_shot.sh modern "$1" $2
