#!/bin/sh
# Photograph aircraft: the AircraftTest game script builds an intercontinental and an
# international airport, a helistation and a heliport and buys every buildable aircraft
# (start year 2060, vehicles never expire, so every generation is there) on round trips
# between them; some wait parked for a full load. The third autosave, with aircraft parked,
# taxiing and circling, is loaded and photographed at 4x. CLIMATE=toyland shows the toyland
# aircraft, YEAR=n another start year.
# Usage: [SEED=n] [SIZE="w h"] [CLIMATE=toyland] [YEAR=n] [AUTOSAVES=n (default 3)] aircraft_shot.sh <name> [keep]
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"
SHOT=normal SIZE="64 64" tools/ingame_shot.sh aircraft aircraft_build keep >/dev/null
i=0
while [ "$(ls "$T/save/autosave" 2>/dev/null | wc -l)" -lt ${AUTOSAVES:-3} ] && [ $i -lt 600 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/aircraft.cfg" || true
save="$(ls -t "$T"/save/autosave/* | head -1)"
LOAD="$save" SIZE="${SIZE:-10000 5000}" tools/ingame_shot.sh modern "$1" $2
