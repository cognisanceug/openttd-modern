#!/bin/sh
# Screenshot the text of the interface: town and station labels, news items and the status bar ticker.
# Usage: [SEED=n] [SCALE=percent] [ZOOM=level] [SHOT=no_con|big] [CFG=config lines] [BIN=path/to/openttd]
#        text_shot.sh <classic|modern> <name> [window ...]
#   Starts a new game (town config), opens the windows with the show_window console command a few
#   seconds after the start (default: station, which builds a station with a sign next to the largest
#   town and scrolls there; news_thin, news_small, news_normal, news_vehicle and news_company show a
#   news item) and shoots the screen a few seconds later, while the news item is still shown.
#   SCALE sets the GUI scale (default 200 from the config), ZOOM the zoom level of the main view
#   (0 is 4x zoomed in, 2 normal, 4 is 4x zoomed out with the small labels), SHOT=big shoots the visible map at the
#   closest zoom without windows, CFG adds config lines, \n separated (e.g. CFG='[news_display]\neconomy = summary'
#   puts the news_normal item in the status bar ticker).
# Uses the isolated test home like gui_shot.sh; result in shots/<name>.png.
set -e
cd "$(dirname "$0")/.."
H="$PWD/test-home"
T="$H/Documents/OpenTTD"
BIN="${BIN:-../build/openttd}"
mkdir -p "$T/baseset" "$T/newgrf" "$T/scripts" "$T/screenshot"
[ -f "$T/baseset/opengfx-8.0.tar" ] || cp "$HOME/Documents/OpenTTD/baseset/opengfx-8.0.tar" "$T/baseset/"
ln -sf "$PWD/nml/modern_terrain.grf" "$T/newgrf/modern_terrain.grf"
ln -sf "$PWD/nml/modern_gui.grf" "$T/newgrf/modern_gui.grf"
rm -f "$T/baseset/opntitle.dat" "$T/baseset/opntitle_modern.dat"
cfg="$T/text_$1.cfg"
if [ -n "$SCALE" ]; then
	sed "s/^gui_scale = .*/gui_scale = $SCALE/" test-config/gui_$1.cfg > "$cfg"
else
	cp test-config/gui_$1.cfg "$cfg"
fi
[ -n "$CFG" ] && printf '%b\n' "$CFG" >> "$cfg"
name="$2"
shift 2
rm -f "$T/scripts/autoexec.scr"
printf 'schedule in-5-seconds scripts/text_shot.scr\n' > "$T/scripts/game_start.scr"
{
	[ -n "$ZOOM" ] && echo "zoomto $ZOOM"
	for w in ${*:-station}; do echo "show_window $w"; done
	echo "schedule in-5-seconds scripts/text_shot2.scr"
} > "$T/scripts/text_shot.scr"
if [ "${SHOT:-no_con}" = big ]; then
	printf 'screenshot big %s\n' "$name" > "$T/scripts/text_shot2.scr"
else
	printf 'screenshot no_con %s\n' "$name" > "$T/scripts/text_shot2.scr"
fi
rm -f "$T/screenshot/$name.png"
HOME="$H" "$BIN" -c "$cfg" -g -G "${SEED:-2}" -s null -m null >/dev/null 2>&1 &
pid=$!
i=0
while [ ! -s "$T/screenshot/$name.png" ] && [ $i -lt 240 ]; do perl -e 'select(undef,undef,undef,0.5)'; i=$((i+1)); done
perl -e 'select(undef,undef,undef,1)'
kill $pid
mkdir -p shots && cp "$T/screenshot/$name.png" shots/
