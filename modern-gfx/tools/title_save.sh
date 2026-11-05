#!/bin/sh
# Make a title screen savegame: generate a town map, centre the view on the largest town
# and save it. The result goes to shots/<name>.sav; copy it to the baseset folder as
# opntitle.dat to use it as the title game.
# Usage: [SEED=n] [BIN=path/to/openttd] title_save.sh <name>
set -e
cd "$(dirname "$0")/.."
H="$PWD/test-home"
T="$H/Documents/OpenTTD"
BIN="${BIN:-../build/openttd}"
mkdir -p "$T/baseset" "$T/newgrf" "$T/scripts" "$T/save"
[ -f "$T/baseset/opengfx-8.0.tar" ] || cp "$HOME/Documents/OpenTTD/baseset/opengfx-8.0.tar" "$T/baseset/"
ln -sf "$PWD/nml/modern_terrain.grf" "$T/newgrf/modern_terrain.grf"
ln -sf "$PWD/nml/modern_gui.grf" "$T/newgrf/modern_gui.grf"
sed -e "s/^map_x = .*/map_x = ${MAPSIZE:-7}/" -e "s/^map_y = .*/map_y = ${MAPSIZE:-7}/" test-config/gui_modern.cfg > "$T/title.cfg"
rm -f "$T/scripts/autoexec.scr"
printf 'schedule on-next-calendar-month scripts/title_save.scr\n' > "$T/scripts/game_start.scr"
cat > "$T/scripts/title_save.scr" <<SCR
show_window title_view
schedule in-5-seconds scripts/title_save2.scr
SCR
printf 'save %s\n' "$1" > "$T/scripts/title_save2.scr"
rm -f "$T/save/$1.sav"
HOME="$H" "$BIN" -c "$T/title.cfg" -g -G "${SEED:-2}" -s null -m null >/dev/null 2>&1 &
pid=$!
i=0
while [ ! -s "$T/save/$1.sav" ] && [ $i -lt 480 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,1)'
kill $pid
mkdir -p shots && cp "$T/save/$1.sav" shots/
