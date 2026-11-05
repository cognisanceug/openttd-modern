#!/bin/sh
# Put together a playable OpenTTD Modern with ModernGFX in one folder, apart from any other
# OpenTTD installation: the built game, the NewGRFs and a config of its own.
# Usage: install_local.sh [target]   (default: ~/Games/OpenTTD Modern)
#   <target>/game/                  the game (copied from $OPENTTD/build) with its base sets and languages
#   <target>/data/                  personal dir: openttd.cfg, newgrf/, baseset/ (OpenGFX), saves
#   <target>/OpenTTD Modern.command  double-click to start
# Running it again updates game and NewGRFs and keeps the config and savegames.
set -e
cd "$(dirname "$0")/.."
. tools/openttd_dir.sh
SRC="$PWD"
BUILD="$OPENTTD/build"
DST="${1:-$HOME/Games/OpenTTD Modern}"
# Only install into a new or empty folder or a previous install (the file system may ignore case,
# so ~/OpenTTD-Modern could be this very checkout).
if [ -d "$DST" ] && [ -n "$(ls -A "$DST")" ] && [ ! -f "$DST/data/openttd.cfg" ]; then
	echo "$DST exists and is not an OpenTTD Modern install, choose another target" >&2; exit 1
fi
[ -x "$BUILD/openttd" ] || { echo "no game build in $BUILD" >&2; exit 1; }
for g in nml/moderngfx.grf nml/moderngfx_gui.grf; do
	[ -f "$g" ] || { echo "missing $g, run pack_grf.py and pack_gui_grf.py first" >&2; exit 1; }
done

mkdir -p "$DST/game" "$DST/data/newgrf" "$DST/data/baseset"
for d in baseset lang ai game; do
	rm -rf "$DST/game/$d"
	cp -R "$BUILD/$d" "$DST/game/$d"
done
cp "$BUILD/openttd" "$DST/game/openttd"
cp nml/moderngfx.grf nml/moderngfx_gui.grf "$DST/data/newgrf/"
# Earlier installs used the file names modern_terrain.grf and modern_gui.grf.
rm -f "$DST/data/newgrf/modern_terrain.grf" "$DST/data/newgrf/modern_gui.grf"
[ ! -f "$DST/data/openttd.cfg" ] || perl -pi -e 's/^modern_terrain\.grf/moderngfx.grf/; s/^modern_gui\.grf/moderngfx_gui.grf/' "$DST/data/openttd.cfg"
[ -f "$DST/data/baseset/opengfx-8.0.tar" ] || cp "$HOME/Documents/OpenTTD/baseset/opengfx-8.0.tar" "$DST/data/baseset/"

if [ ! -f "$DST/data/openttd.cfg" ]; then
	cat > "$DST/data/openttd.cfg" <<'CFG'
[gui]
zoom_min = 0
sprite_zoom_min = 0
modern_ui = true
[graphicsset]
name = OpenGFX
[newgrf]
moderngfx.grf =
moderngfx_gui.grf =
[misc]
resolution = 1600,1000
fullscreen = false
gui_scale = 200
global_aa = true
[network]
participate_survey = no
CFG
fi

cat > "$DST/OpenTTD Modern.command" <<'RUN'
#!/bin/sh
cd "$(dirname "$0")/game" && exec ./openttd -c "../data/openttd.cfg"
RUN
chmod +x "$DST/OpenTTD Modern.command"
echo "installed to $DST"
