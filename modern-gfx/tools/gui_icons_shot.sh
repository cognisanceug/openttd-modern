#!/bin/sh
# Screenshot several sets of windows in one game, for checking the interface icons.
# Usage: [SEED=n] [BIN=path/to/openttd] gui_icons_shot.sh <classic|modern> <prefix> [set ...]
#   A set is <name>:<window>[,<window>...] with the window names of the show_window console command,
#   e.g. rail:build_rail,build_signals depot:depot,vehicle. Each set gets shots/<prefix>_<name>.png;
#   the windows of a set are closed before the next one opens.
# Uses the isolated test home and the configs of gui_shot.sh.
set -e
cd "$(dirname "$0")/.."
H="$PWD/test-home"
T="$H/Documents/OpenTTD"
BIN="${BIN:-../build/openttd}"
style=$1 prefix=$2
shift 2
mkdir -p "$T/baseset" "$T/newgrf" "$T/scripts" "$T/screenshot" shots
[ -f "$T/baseset/opengfx-8.0.tar" ] || cp "$HOME/Documents/OpenTTD/baseset/opengfx-8.0.tar" "$T/baseset/"
ln -sf "$PWD/nml/modern_terrain.grf" "$T/newgrf/modern_terrain.grf"
ln -sf "$PWD/nml/modern_gui.grf" "$T/newgrf/modern_gui.grf"
cfg="$T/gui_$style.cfg"
cp test-config/gui_$style.cfg "$cfg"
rm -f "$T/scripts/autoexec.scr" "$T"/scripts/icons_*.scr
printf 'schedule in-5-seconds scripts/icons_0.scr\n' > "$T/scripts/game_start.scr"
k=0 last=""
for set in "$@"; do
	name=${set%%:*}
	{
		echo "show_window close_all"
		echo "show_window goto_town"
		for w in $(echo "${set#*:}" | tr ',' ' '); do echo "show_window $w"; done
		echo "schedule in-5-seconds scripts/icons_${k}s.scr"
	} > "$T/scripts/icons_$k.scr"
	printf 'screenshot no_con %s_%s\nschedule in-5-seconds scripts/icons_%d.scr\n' "$prefix" "$name" $((k + 1)) > "$T/scripts/icons_${k}s.scr"
	rm -f "$T/screenshot/${prefix}_$name.png"
	last="${prefix}_$name"
	k=$((k + 1))
done
HOME="$H" "$BIN" -c "$cfg" -g -G "${SEED:-2}" -s null -m null >/dev/null 2>&1 &
pid=$!
i=0
while [ ! -s "$T/screenshot/$last.png" ] && [ $i -lt 600 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,1)'
kill $pid
for set in "$@"; do cp "$T/screenshot/${prefix}_${set%%:*}.png" shots/; done
