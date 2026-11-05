#!/bin/sh
# Photograph objects and industries: the IndustryTest game script builds a company
# HQ, a statue, owned land and every buildable industry around the map centre, a
# second wave of industries shortly before the third autosave shows construction
# stages. The third autosave is then loaded and photographed at 4x.
# CLIMATE=arctic|tropic|toyland builds that climate's industries (test-config/industry_<climate>.cfg).
# Usage: [SEED=n] [SIZE="w h"] [CLIMATE=...] industry_shot.sh <name> [keep]
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"
CFG=industry${CLIMATE:+_$CLIMATE}
SHOT=normal SIZE="64 64" tools/ingame_shot.sh $CFG industry_build keep >/dev/null
i=0
while [ "$(ls "$T/save/autosave" 2>/dev/null | wc -l)" -lt 3 ] && [ $i -lt 600 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/$CFG.cfg" || true
save="$(ls -t "$T"/save/autosave/* | head -1)"
LOAD="$save" SIZE="${SIZE:-10000 5000}" tools/ingame_shot.sh modern "$1" $2
