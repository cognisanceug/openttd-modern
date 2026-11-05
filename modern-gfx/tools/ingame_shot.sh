#!/bin/sh
# Start OpenTTD in an isolated test home, take one screenshot and quit.
# Usage: [SEED=n | LOAD=savegame] [SHOT=big|normal] [ZOOM=4|2] [SIZE="w h"] ingame_shot.sh <config> <name> [keep]
#   modern  OpenGFX plus nml/modern_terrain.grf      base  OpenGFX only
#   water   like modern, with a high sea level so coasts and rivers show up
#   town    like modern, with many towns: houses and roads on slopes show foundations
#   arctic, tropic, toyland   like modern in that climate (snow, desert, the climate's trees)
#   arctic_town, tropic_town, toyland_town   the same with many towns, from the year 2000
#   terrain like infra, runs the TerrainTest game script (see tools/terrain_shot.sh)
#   infra   like modern, runs the InfraTest game script and autosaves every minute
#           (see tools/infra_shot.sh)
#   LOAD    load this savegame instead of generating a map
#   CLIMATE=toyland (or arctic, tropic) generates the map in that climate; it passes through
#               infra_shot.sh, water_shot.sh and airport_shot.sh, so their test scripts build there.
#   SHOT=big renders at the max zoom-in (4x), SHOT=normal always at 1x.
#   ZOOM=2 caps the zoom-in at 2x, so SHOT=big shows the 2x sprites.
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
cp test-config/*.cfg "$T/"
[ -n "$CLIMATE" ] && perl -0pi -e "s/\\[game_creation\\]\\n/[game_creation]\\nlandscape = $CLIMATE\\n/" "$T/$1.cfg"
[ "${ZOOM:-4}" = 2 ] && sed -i '' 's/^zoom_min = 0/zoom_min = 1/' "$T/$1.cfg"
rm -rf "$T/game" && cp -R test-config/game "$T/game"
[ -f "$T/baseset/opengfx-8.0.tar" ] || cp "$HOME/Documents/OpenTTD/baseset/opengfx-8.0.tar" "$T/baseset/"
ln -sf "$PWD/nml/modern_terrain.grf" "$T/newgrf/modern_terrain.grf"
cat > "$T/scripts/game_start.scr" <<SCR
screenshot ${SHOT:-big} size ${SIZE:-1600 1000} $2
SCR
rm -f "$T/screenshot/$2.png"
if [ -n "$LOAD" ]; then start="-g $LOAD"; else start="-g -G ${SEED:-12345}"; fi
HOME="$H" ../build/openttd -c "$T/$1.cfg" $start -s null -m null >/dev/null 2>&1 &
pid=$!
i=0
while [ ! -s "$T/screenshot/$2.png" ] && [ $i -lt 120 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
# Large shots take a while to write: wait until the file stops growing.
size=-1
while [ "$(wc -c < "$T/screenshot/$2.png")" != "$size" ]; do size="$(wc -c < "$T/screenshot/$2.png")"; perl -e 'select(undef,undef,undef,1)'; done
mkdir -p shots && cp "$T/screenshot/$2.png" shots/
if [ "$3" = keep ]; then echo "game left running (pid $pid)"; else kill $pid; fi
