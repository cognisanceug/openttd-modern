#!/bin/sh
# Photograph effects and disasters: the FxTest game script builds a loop of steam and diesel trains,
# a loop of electric trains, buses, a small airport and the industries the disasters go for (power
# station, refinery, factory, coal mine; the bubble generator in toyland), then drives two pairs of
# engines into each other. Vehicles are old (start year 2060, engines never expire), so they break
# down. Disasters need the test hook of tools/disaster_test.patch: build OpenTTD with it and pass the
# binary as OTTD; the game then starts the disasters of FX_DISASTERS (default all, in turn) every
# FX_DAYS days. Each of the first AUTOSAVES autosaves is loaded and photographed at 4x as <name>_<n>.
# Usage: OTTD=<patched openttd> [CLIMATE=toyland] [SIZE="w h"] [AUTOSAVES=n] fx_shot.sh <name>
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"
export OTTD_FX_DISASTERS="${FX_DISASTERS-0,1,4,2,3,7,5,6}" OTTD_FX_DISASTER_DAYS="${FX_DAYS:-5}"
LOG="$PWD/shots/fx_build.log" SHOT=normal SIZE="64 64" tools/ingame_shot.sh fx fx_build keep >/dev/null
i=0
while [ "$(ls "$T/save/autosave" 2>/dev/null | wc -l)" -lt ${AUTOSAVES:-4} ] && [ $i -lt 900 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/fx.cfg" || true
mkdir -p shots/fx_saves
n=0
for save in $(ls -tr "$T"/save/autosave/*); do
	n=$((n+1))
	cp "$save" "shots/fx_saves/$1_$n.sav"
	LOAD="$save" SIZE="${SIZE:-10000 5000}" tools/ingame_shot.sh modern "$1_$n"
done
