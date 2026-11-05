#!/bin/sh
# Start OpenTTD in an isolated test home, take one screenshot and quit.
# Usage: [SEED=n] [SHOT=big|normal] [SIZE="w h"] ingame_shot.sh <modern|base> <name> [keep]
#   modern  OpenGFX plus nml/modern_terrain.grf      base  OpenGFX only
#   SHOT=big renders at the max zoom-in (4x), SHOT=normal always at 1x.
#   The view cannot be scrolled from the start script (the viewport is placed
#   afterwards), so pick the map with SEED instead (5: trees, 1: rocks).
#   keep: leave the game window open instead of quitting.
# The test home (test-home/) is rebuilt from test-config/ on every run; OpenGFX
# is copied from ~/Documents/OpenTTD/baseset, so the user's own config is never touched.
set -e
cd "$(dirname "$0")/.."
H="$PWD/test-home"
T="$H/Documents/OpenTTD"
mkdir -p "$T/baseset" "$T/newgrf" "$T/scripts" "$T/screenshot"
cp test-config/modern.cfg test-config/base.cfg "$T/"
[ -f "$T/baseset/opengfx-8.0.tar" ] || cp "$HOME/Documents/OpenTTD/baseset/opengfx-8.0.tar" "$T/baseset/"
ln -sf "$PWD/nml/modern_terrain.grf" "$T/newgrf/modern_terrain.grf"
cat > "$T/scripts/game_start.scr" <<SCR
screenshot ${SHOT:-big} size ${SIZE:-1600 1000} $2
SCR
rm -f "$T/screenshot/$2.png"
HOME="$H" ../build/openttd -c "$T/$1.cfg" -g -G ${SEED:-12345} -s null -m null >/dev/null 2>&1 &
pid=$!
i=0
while [ ! -s "$T/screenshot/$2.png" ] && [ $i -lt 120 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,1)'
mkdir -p shots && cp "$T/screenshot/$2.png" shots/
if [ "$3" = keep ]; then echo "game left running (pid $pid)"; else kill $pid; fi
