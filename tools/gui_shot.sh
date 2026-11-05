#!/bin/sh
# Screenshot the interface (title screen or in-game windows) in the classic or modern style.
# Usage: [SEED=n] [TITLE=savegame] [BIN=path/to/openttd] gui_shot.sh <classic|modern> <title|game> <name> [keep]
#   title  waits about ten seconds for the title game, then shoots the screen with the main menu
#   game   starts a new game (town config) and opens the rail toolbar, a town and the finances
#          (or WINDOWS="...", see the show_window console command) before shooting
#   classic  modern_ui off, sprite font          modern  modern_ui on, TrueType font
# Uses the isolated test home like ingame_shot.sh; result in shots/<name>.png.
set -e
cd "$(dirname "$0")/.."
. tools/openttd_dir.sh
H="$PWD/test-home"
T="$H/Documents/OpenTTD"
BIN="${BIN:-$OPENTTD/build/openttd}"
mkdir -p "$T/baseset" "$T/newgrf" "$T/scripts" "$T/screenshot"
[ -f "$T/baseset/opengfx-8.0.tar" ] || cp "$HOME/Documents/OpenTTD/baseset/opengfx-8.0.tar" "$T/baseset/"
ln -sf "$PWD/nml/moderngfx.grf" "$T/newgrf/moderngfx.grf"
ln -sf "$PWD/nml/moderngfx_gui.grf" "$T/newgrf/moderngfx_gui.grf"
cfg="$T/gui_$1.cfg"
cp test-config/gui_$1.cfg "$cfg"
# The title game: TITLE=<savegame> uses it as opntitle_modern.dat, otherwise the game's own one.
rm -f "$T/baseset/opntitle.dat" "$T/baseset/opntitle_modern.dat"
[ -n "$TITLE" ] && cp "$TITLE" "$T/baseset/opntitle_modern.dat"
if [ "$2" = title ]; then
	printf 'schedule in-5-seconds scripts/title_wait.scr\n' > "$T/scripts/autoexec.scr"
	printf 'schedule in-5-seconds scripts/title_shot.scr\n' > "$T/scripts/title_wait.scr"
	printf 'screenshot no_con %s\n' "$3" > "$T/scripts/title_shot.scr"
	rm -f "$T/scripts/game_start.scr"
	start=""
else
	rm -f "$T/scripts/autoexec.scr"
	printf 'schedule on-next-calendar-month scripts/game_shot.scr\n' > "$T/scripts/game_start.scr"
	cat > "$T/scripts/game_shot.scr" <<SCR
show_window goto_town
$(for w in ${WINDOWS:-build_rail town finances}; do echo "show_window $w"; done)
schedule on-next-calendar-month scripts/game_shot2.scr
SCR
	printf 'screenshot no_con %s\n' "$3" > "$T/scripts/game_shot2.scr"
	start="-g -G ${SEED:-2}"
fi
rm -f "$T/screenshot/$3.png"
HOME="$H" "$BIN" -c "$cfg" $start -s null -m null >/dev/null 2>&1 &
pid=$!
i=0
while [ ! -s "$T/screenshot/$3.png" ] && [ $i -lt 480 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,1)'
mkdir -p shots && cp "$T/screenshot/$3.png" shots/
if [ "$4" = keep ]; then echo "game left running (pid $pid)"; else kill $pid; fi
