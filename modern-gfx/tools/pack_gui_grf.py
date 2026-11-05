"""Pack the interface graphics into nml/moderngfx_gui.grf.

A separate NewGRF from moderngfx.grf, so the interface can be built and
enabled on its own. It holds the title screen logo, one sprite per letter
(tools/make_logo.py): T 4836, n 4839, p 4841, O 4842 in the base set, e and D
in the OpenTTD GUI block (OTTD_GUI 12, 13); the main toolbar and build menu
icons (tools/make_icons.py), 20 x 20 px at 1x (station, bridge and airport
40 x 20), see ICON_BLOCKS; and the other interface sprites
(tools/make_gui_icons.py: monorail and maglev build icons, cursors, vehicle
and depot buttons, window glyphs, cargo and status icons) in the sizes and
offsets of the originals, grouped into runs of consecutive sprites, see
gui_blocks().
Every block gets an 8bpp fallback plus 32bpp sprites at 1x, 2x, 4x.

Usage: pack_gui_grf.py <render-dir> <nml-dir>   (render-dir holds logo/, icons/ and gui_icons/)
"""

import os
import subprocess
import sys

from PIL import Image

from make_gui_icons import SPRITES
from pack_grf import ZOOMS, sheet_block

LOGO_BLOCKS = (
    ("logo_t", "replace {name}(4836, {file})", "T"),
    ("logo_n", "replace {name}(4839, {file})", "n"),
    ("logo_p", "replace {name}(4841, {file})", "p"),
    ("logo_o", "replace {name}(4842, {file})", "O"),
    ("logo_ed", "replacenew {name}(OTTD_GUI, {file}, 12)", "eD"),
)

# (block name, NML block header, icon names in sprite order)
ICON_BLOCKS = (
    ("icon_subsidies_messages", "replace {name}(679, {file})", ["subsidies", "messages"]),
    ("icon_league", "replace {name}(684, {file})", ["league"]),
    ("icon_smallmap", "replace {name}(708, {file})", ["smallmap"]),
    ("icon_music", "replace {name}(713, {file})", ["music"]),
    ("icon_query", "replace {name}(723, {file})", ["query"]),
    ("icon_save", "replace {name}(724, {file})", ["save"]),
    ("icon_toolbar", "replace {name}(726, {file})",
     ["pause", "buildrail", "buildroad", "buildwater", "buildair", "trainlist", "trucklist", "shiplist",
      "planelist", "zoomin", "zoomout", "finance", "contours", "vehicles", "routes", "industry", "planttrees",
      "company"]),
    ("icon_graphs", "replace {name}(745, {file})", ["graphs"]),
    ("icon_settings", "replace {name}(751, {file})", ["settings"]),
    ("icon_companylist", "replace {name}(1299, {file})", ["companylist"]),
    ("icon_town", "replace {name}(4077, {file})", ["town"]),
    ("icon_sign_landscaping", "replace {name}(4082, {file})", ["sign", "landscaping"]),
    ("icon_transmitter", "replace {name}(4086, {file})", ["transmitter"]),
    ("icon_fastforward", "replacenew {name}(OTTD_GUI, {file}, 90)", ["fastforward"]),
    ("icon_switchtoolbar", "replacenew {name}(OTTD_GUI, {file}, 144)", ["switchtoolbar"]),
    ("icon_storybook", "replacenew {name}(OTTD_GUI, {file}, 169)", ["storybook"]),
    ("icon_goal", "replacenew {name}(OTTD_GUI, {file}, 171)", ["goal"]),
    ("icon_buildtrams", "replacenew {name}(OTTD_GUI, {file}, 179)", ["buildtrams"]),
    # Build menus: rail, road, tram, water, airport, landscaping.
    ("icon_buoy_terraform", "replace {name}(693, {file})", ["buoy", "terraform_up", "terraform_down"]),
    ("icon_dynamite", "replace {name}(703, {file})", ["dynamite"]),
    ("icon_remove", "replace {name}(714, {file})", ["remove"]),
    ("icon_airport", "replace {name}(744, {file})", ["airport"]),
    ("icon_ship_dock", "replace {name}(746, {file})", ["ship_dock"]),
    ("icon_depot_stops", "replace {name}(748, {file})", ["ship_depot", "bus_station", "truck_bay"]),
    ("icon_rail_tracks", "replace {name}(1251, {file})", ["rail_ns", "rail_x", "rail_ew", "rail_y"]),
    ("icon_signals", "replace {name}(1291, {file})", ["signals"]),
    ("icon_depots", "replace {name}(1294, {file})", ["depot_rail", "road_depot"]),
    ("icon_railstation", "replace {name}(1298, {file})", ["railstation"]),
    ("icon_roads", "replace {name}(1309, {file})", ["road_y", "road_x"]),
    ("icon_tunnels", "replace {name}(2429, {file})", ["road_tunnel", "tunnel_rail"]),
    ("icon_bridge", "replace {name}(2594, {file})", ["bridge"]),
    ("icon_rocks_desert", "replace {name}(4084, {file})", ["rocks", "desert"]),
    ("icon_buy_land", "replace {name}(4791, {file})", ["buy_land"]),
    ("icon_autorail", "replacenew {name}(OTTD_GUI, {file}, 53)", ["autorail"]),
    ("icon_convert_rail", "replacenew {name}(OTTD_GUI, {file}, 55)", ["convert_rail"]),
    ("icon_autoelrail", "replacenew {name}(OTTD_GUI, {file}, 57)", ["autoelrail"]),
    ("icon_convert_elrail", "replacenew {name}(OTTD_GUI, {file}, 59)", ["convert_elrail"]),
    ("icon_depot_elrail", "replacenew {name}(OTTD_GUI, {file}, 61)", ["depot_elrail"]),
    ("icon_waypoint", "replacenew {name}(OTTD_GUI, {file}, 76)", ["waypoint"]),
    ("icon_autoroad", "replacenew {name}(OTTD_GUI, {file}, 82)", ["autoroad"]),
    ("icon_autotram", "replacenew {name}(OTTD_GUI, {file}, 84)", ["autotram"]),
    ("icon_canal", "replacenew {name}(OTTD_GUI, {file}, 88)", ["canal"]),
    ("icon_level_land", "replacenew {name}(OTTD_GUI, {file}, 91)", ["level_land"]),
    ("icon_one_way_signal_convert_river", "replacenew {name}(OTTD_GUI, {file}, 134)",
     ["one_way", "signal_convert", "river"]),
    ("icon_aqueduct", "replacenew {name}(OTTD_GUI, {file}, 145)", ["aqueduct"]),
    ("icon_convert_road", "replacenew {name}(OTTD_GUI, {file}, 180)", ["convert_road"]),
    ("icon_elrail_tracks", "replacenew {name}(CATENARY, {file}, 36)", ["elrail_ns", "elrail_x", "elrail_ew", "elrail_y"]),
    ("icon_tunnel_elrail", "replacenew {name}(CATENARY, {file}, 44)", ["tunnel_elrail"]),
    ("icon_tram_tracks", "replacenew {name}(TRAMWAY, {file}, 0)", ["tram_y", "tram_x"]),
    ("icon_lock", "replacenew {name}(CANALS, {file}, 64)", ["lock"]),
)


# make_gui_icons block -> NML block header; "base" sprites are replaced by number.
GUI_HEADERS = {
    "base": "replace {name}({index}, {file})",
    "gui": "replacenew {name}(OTTD_GUI, {file}, {index})",
    "catenary": "replacenew {name}(CATENARY, {file}, {index})",
    "tramway": "replacenew {name}(TRAMWAY, {file}, {index})",
    "canals": "replacenew {name}(CANALS, {file}, {index})",
}


def gui_blocks():
    """Runs of consecutive sprites of make_gui_icons: (block name, header, keys in sprite order)."""
    by_index = sorted(SPRITES, key=lambda k: (SPRITES[k][0], SPRITES[k][1]))
    runs = []
    for key in by_index:
        block, index = SPRITES[key][:2]
        if runs and runs[-1][0] == block and runs[-1][2] + 1 == index:
            runs[-1][2] = index
            runs[-1][3].append(key)
        else:
            runs.append([block, index, index, [key]])
    return [(f"gui_{block}_{first}", GUI_HEADERS[block].replace("{index}", str(first)), keys)
            for block, first, _, keys in runs]


def gui_sprite(gui_dir, key, zoom):
    _, _, (_, _, xo, yo), _, _ = SPRITES[key]
    return Image.open(os.path.join(gui_dir, f"z{zoom}", f"{key}.png")).convert("RGBA"), xo * zoom, yo * zoom


def icon_sprite(icon_dir, name, zoom):
    return Image.open(os.path.join(icon_dir, f"z{zoom}", f"{name}.png")).convert("RGBA"), 0, 0


def logo_sprite(logo_dir, ch, zoom):
    # The letters are set in their full advance box; the game places them side by side.
    return Image.open(os.path.join(logo_dir, f"z{zoom}", f"{ch}.png")).convert("RGBA"), 0, 0


def main():
    render_dir, nml_dir = sys.argv[1:3]
    logo_dir = os.path.join(render_dir, "logo")
    gfx_dir = os.path.join(nml_dir, "gfx")
    os.makedirs(gfx_dir, exist_ok=True)

    nml = [
        "// Generated by tools/pack_gui_grf.py - do not edit.",
        "grf {",
        '    grfid: "RV\\4D\\02";',
        "    name: string(STR_GUI_GRF_NAME);",
        "    desc: string(STR_GUI_GRF_DESC);",
        "    version: 1;",
        "    min_compatible_version: 1;",
        "}",
        "",
    ]
    for name, header, chars in LOGO_BLOCKS:
        nml.append(sheet_block(name, header, [f"logo {c}" for c in chars],
                               {z: [logo_sprite(logo_dir, c, z) for c in chars] for z in ZOOMS}, gfx_dir))
    icon_dir = os.path.join(render_dir, "icons")
    for name, header, icons in ICON_BLOCKS:
        nml.append(sheet_block(name, header, icons, {z: [icon_sprite(icon_dir, i, z) for i in icons] for z in ZOOMS},
                               gfx_dir))
    gui_dir = os.path.join(render_dir, "gui_icons")
    for name, header, keys in gui_blocks():
        nml.append(sheet_block(name, header, keys, {z: [gui_sprite(gui_dir, k, z) for k in keys] for z in ZOOMS},
                               gfx_dir))
    open(os.path.join(nml_dir, "moderngfx_gui.nml"), "w").write("\n".join(nml))

    lang_dir = os.path.join(nml_dir, "lang_gui")
    os.makedirs(lang_dir, exist_ok=True)
    open(os.path.join(lang_dir, "english.lng"), "w").write(
        "##grflangid 0x01\n"
        "STR_GUI_GRF_NAME :ModernGFX Interface\n"
        "STR_GUI_GRF_DESC :Interface graphics matching ModernGFX: the title screen logo, toolbar, build menu and window icons and cursors. Licence: GPL v2.\n"
    )
    nmlc = os.path.join(os.path.dirname(sys.executable), "nmlc")
    subprocess.run([nmlc, "-c", "--lang-dir", "lang_gui", "--grf", "moderngfx_gui.grf", "moderngfx_gui.nml"],
                   cwd=nml_dir, check=True)


if __name__ == "__main__":
    main()
