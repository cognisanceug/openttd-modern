#!/bin/sh
# Photograph ships: the ShipTest game script digs a canal pond with a ship depot and five
# buoys and buys every buildable ship twice (start year 1990, vehicles never expire), each on
# a round trip between the buoys. The third autosave, with the ships under way, is loaded
# and photographed at 4x. CLIMATE=toyland shows the toyland ships.
# Usage: [SEED=n] [SIZE="w h"] [CLIMATE=toyland] ship_shot.sh <name> [keep]
set -e
cd "$(dirname "$0")/.."
T="$PWD/test-home/Documents/OpenTTD"
rm -rf "$T/save/autosave"
SHOT=normal SIZE="64 64" tools/ingame_shot.sh ship ship_build keep >/dev/null
i=0
while [ "$(ls "$T/save/autosave" 2>/dev/null | wc -l)" -lt 3 ] && [ $i -lt 600 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,2)'
pkill -f "$T/ship.cfg" || true
save="$(ls -t "$T"/save/autosave/* | head -1)"
LOAD="$save" SIZE="${SIZE:-10000 5000}" tools/ingame_shot.sh modern "$1" $2
