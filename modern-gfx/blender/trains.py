"""Train models for render_vehicles.py: every original engine and wagon sprite set (0xAAD-0xC00).

Conventions as for the ships: local +a is the front, b across (right side +b), z height units up from
the vehicle's z_pos, which is the top of the ground the track texture lies on, so wheels touch z = 0.
One x/y unit is K = 2.449 z units in true proportions. Every original vehicle is 8 units long
(VEHICLE_LENGTH): bodies end at |a| = 3.7, buffers and couplers reach 3.95, so the next vehicle's
buffers meet at the 8-unit spacing. render_vehicles stretches the length by sqrt(2) in the N, E, S, W
directions (the corner-cutting track pieces), where a vehicle step moves one unit in x and y.

Fit to the infrastructure: wheels on the rails at b = +-1.6 (make_infra_textures.py GAUGE_HALF 0.1 tile),
bodies at most 2.1 wide either side (platform edges are 3 units from the track centre, render_stations.py),
floors at z 2.4 just above the platform top (2.1), roofs at 7-8 and pantographs reaching the contact wire
at z 13 (render_catenary.py WIRE_Z). Monorail and maglev cars hang skirts down to z 0.6 over the beam or
guideway texture.

Effect attachment points (local a, b, z; for the effects session): steam engines puff at the chimney top,
diesels at the exhaust, electrics spark at the pantograph head; EFFECTS lists them per model. The game
spawns all three (Vehicle::ShowVisualEffect, CreateEffectVehicleRel(v, x, y, 10, ...)) 10 units above
z_pos at the vehicle centre (the default effect offset of the original engines is 0), so steam smoke
appears about 3 units behind our chimneys, which sit near the front as on a real engine. Without a NewGRF
engine property the offset cannot move; the smoke sprites could be drawn with their puff shifted instead.

Sprite sets (base + Direction; _engine_sprite_base in table/train_sprites.h, 8 dirs, or 4 for symmetric
vehicles where the game uses direction & 3; wagons with a full load add _wagon_full_adder):
  engines (temperate unless noted; A = sub-arctic, S = sub-tropic; toyland replaces some, see TOYLAND)
  jubilee 0xB59 Chaney 'Jubilee', SH '8P'      a4      0xB61 Ginzu 'A4'          tank   0xB69 Kirby Paul Tank
  d25     0xB71 SH/Hendry '25', Floss '47' (4) d37     0xB75 UU '37' (4)         e30    0xB79 SH '30', SH '40' (4)
  hst     0xB7D SH '125' (multihead)           dmu     0xB85 Manley-Morel DMU    dash   0xB8D 'Dash' DMU
  asiastar 0xB95 'AsiaStar'                    tim     0xB9D 'T.I.M.'            x2001  0xBA5 'X2001' monorail (4)
  z1      0xBA9 'Millennium Z1' monorail       lev3    0xBB1 Lev3 'Pegasus'      lev4   0xBB9 Lev4 'Chimaera'
  lev1    0xBC1 Lev1 'Leviathan' (4)           lev2    0xBC5 Lev2 'Cyclops' (4)  cs2400 0xBC9 CS 2400 (A, S)
  centennial 0xBD1 Centennial (A, S)           cs4000  0xBD9 CS 4000 (A, S)      wills  0xBE1 Wills 2-8-0 (A, S)
  kelling 0xBE9 Kelling 3100 (A, S; 4)         turbo   0xBED Turner Turbo (A, S) mjs1000 0xBF5 MJS 1000 (A, S; 4)
  mjs250  0xBF9 MJS 250 (A, S)
  rail wagons 0xAAD-0xB0C (4 dirs each), monorail/maglev wagons 0xB0D-0xB58 (m_*): see WAGONS
  toyland: its base graphics replace 0xAAD-0xAB0, 0xAB5-0xB00 and the engines above marked in TOYLAND
"""

import math

import build_kit as bk
import style as st

W, O = st.WALL, st.OBJECT
K = 2.449  # z units per x/y unit
GAUGE = 1.6
HALF = 3.7  # body end
BUF = 3.95  # buffer face

bk.PALETTE.update({
    "tr_black": ((52, 54, 60), W), "tr_iron": ((74, 78, 86), W), "tr_wheel": ((58, 60, 66), W),
    "tr_frame": ((64, 66, 72), W), "tr_buffer": ((176, 60, 52), W), "tr_brass": ((210, 168, 88), W),
    "tr_warn": ((240, 196, 60), W), "tr_white": ((236, 238, 238), W), "tr_silver": ((186, 192, 198), W),
    "tr_grey": ((140, 146, 152), W), "tr_roof": ((112, 118, 126), W), "tr_glass": ((52, 66, 86), W),
    "tr_glass_hi": ((96, 128, 160), W), "tr_lamp": ((255, 240, 190), st.FLAT), "tr_red": ((196, 66, 56), W),
    "tr_brown": ((132, 88, 62), W), "tr_wood": ((166, 122, 82), W), "tr_green": ((70, 112, 84), W),
    "tr_maroon": ((128, 54, 56), W), "tr_cream": ((232, 220, 186), W), "tr_tank": ((70, 74, 82), W),
    "tr_water_tank": ((176, 200, 214), W), "tr_rust": ((150, 96, 70), W), "tr_teal": ((70, 150, 160), W),
    "tr_skirt": ((92, 98, 108), W), "tr_cattle": ((140, 96, 70), O), "tr_sheep": ((228, 224, 210), O),
    "tr_crate": ((196, 154, 100), W), "tr_tarp": ((92, 110, 92), W), "tr_coil": ((160, 168, 178), W),
    "tr_paper": ((238, 236, 228), W), "tr_rubber": ((84, 70, 58), O), "tr_orange": ((244, 150, 50), O),
    "tr_wheat": ((226, 190, 98), O), "tr_coal": ((60, 60, 66), O), "tr_ore": ((152, 90, 66), O),
    "tr_copper": ((96, 150, 128), O), "tr_log": ((150, 106, 70), O), "tr_log_end": ((222, 186, 132), O),
    "tr_sugar": ((250, 250, 246), O), "tr_floss": ((248, 170, 206), O), "tr_toffee": ((150, 90, 44), O),
    "tr_bubble": ((176, 220, 246), O), "tr_cola": ((90, 46, 28), O), "tr_plastic": ((120, 210, 200), O),
})

TOY = ["toy_red", "toy_yellow", "toy_blue", "toy_green", "toy_pink", "toy_purple", "toy_orange", "toy_mint"]


# --- geometry helpers --------------------------------------------------------------------------

def tube(k, rings, mat):
    """Closed solid through closed polygon rings [[(a, b, z)]] of equal length, capped."""
    n, m = len(rings[0]), len(rings)
    v = [p for r in rings for p in r]
    f = []
    for j in range(m - 1):
        for i in range(n):
            a, b = j * n + i, j * n + (i + 1) % n
            f.append((a, b, b + n, a + n))
    f += [tuple(range(n)), tuple(range((m - 1) * n, m * n))]
    k._solid(v, f, mat)


def prof(w, z0, z1, r=0.5, rz=None, n=3, wb=None):
    """Body cross-section [(b, z)]: sides from z0 (half width wb at the bottom, w at the shoulder),
    rounded shoulders r across and rz up, flat roof at z1."""
    rz = min(r * K, (z1 - z0) * 0.9) if rz is None else rz
    wb = w if wb is None else wb
    r = min(r, w * 0.95)
    pts = [(-wb, z0), (wb, z0)]
    for i in range(n + 1):
        t = i / n * math.pi / 2
        pts.append((w - r + r * math.cos(t), z1 - rz + rz * math.sin(t)))
    for i in range(n + 1):
        t = math.pi / 2 + i / n * math.pi / 2
        pts.append((-w + r + r * math.cos(t), z1 - rz + rz * math.sin(t)))
    return pts


def body(k, a0, a1, w, z0, z1, mat, r=0.5, rz=None, wb=None):
    """Straight car body from a0 to a1."""
    k.extrude(prof(w, z0, z1, r, rz, wb=wb), "x", a0, a1, mat)


def stations(k, st_, mat, r=0.5, rz=None):
    """Body through stations [(a, w, z0, z1)] (a rising), e.g. a nose."""
    tube(k, [[(a, b, z) for b, z in prof(w, z0, z1, min(r, w * 0.9), None if rz is None else min(rz, (z1 - z0) * 0.9))]
             for a, w, z0, z1 in st_], mat)


def nose_st(a0, a1, w, z0, z1, n=5, tip_w=0.55, tip_z=0.45, power=2.0, drop=0.0):
    """Stations of a streamlined nose from a0 (full section) to the tip at a1: width and roof fall
    off as 1 - t^power; drop lowers the floor towards the tip."""
    out = []
    for i in range(n + 1):
        t = i / n
        f = 1 - t ** power
        out.append((a0 + (a1 - a0) * t, w * (tip_w + (1 - tip_w) * math.sqrt(max(f, 0))),
                    z0 + drop * t, z0 + drop * t + (z1 - z0 - drop * t) * (tip_z + (1 - tip_z) * f)))
    return out


def mirror_a(st_):
    return [(-a, w, z0, z1) for a, w, z0, z1 in reversed(st_)]


def wheel(k, a, r=0.48, mat="tr_wheel", g=GAUGE, t=0.28):
    for s in (-1, 1):
        k.rod((a, s * (g - t / 2), r * K), (a, s * (g + t / 2), r * K), r, mat, n=10)


def bogie(k, a, base=1.5, r=0.42, frame="tr_frame"):
    """Two-axle bogie centred at a: wheels and the side frames outside them."""
    for x in (a - base / 2, a + base / 2):
        wheel(k, x, r)
    for s in (-1, 1):
        k.box(a - base / 2 - 0.55, a + base / 2 + 0.55, s * 1.84 - 0.12, s * 1.84 + 0.12, r * K - 0.5, r * K + 0.6, frame)


def underframe(k, z0=1.3, z1=2.2, w=1.6, half=HALF - 0.1, mat="tr_frame"):
    k.box(-half, half, -w, w, z0, z1, mat)


def buffers(k, z=1.9, ends=(1, -1), mat="tr_iron", beam="tr_frame"):
    for e in ends:
        a0, a1 = sorted((e * (HALF - 0.2), e * (HALF + 0.05)))
        k.box(a0, a1, -1.7, 1.7, z - 0.55, z + 0.45, beam)
        for s in (-1, 1):
            k.rod((e * (HALF - 0.05), s * 1.15, z), (e * BUF, s * 1.15, z), 0.17, mat, n=6)


def band(k, a0, a1, w, z0, z1, mat, out=0.04):
    """Belt round a straight-sided body (sides and both ends)."""
    k.box(a0 - out, a1 + out, -w - out, w + out, z0, z1, mat)


def rim(k, a0, a1, w, z0, z1, mat, out=0.04, t=0.25):
    """Hollow belt round an open wagon: four strips, the inside left open."""
    k.box(a0 - out, a1 + out, -w - out, -w + t, z0, z1, mat)
    k.box(a0 - out, a1 + out, w - t, w + out, z0, z1, mat)
    k.box(a0 - out, a0 + t, -w, w, z0, z1, mat)
    k.box(a1 - t, a1 + out, -w, w, z0, z1, mat)


def side_windows(k, a0, a1, w, z0, z1, pitch=1.0, pane=0.7, mat="tr_glass", out=0.05):
    """Separate window panes on both sides."""
    n = max(1, int(round((a1 - a0) / pitch)))
    step = (a1 - a0) / n
    for i in range(n):
        c = a0 + step * (i + 0.5)
        for s in (-1, 1):
            k.box(c - pane * step / 2, c + pane * step / 2, s * w - out, s * w + out, z0, z1, mat)


def strip_windows(k, a0, a1, w, z0, z1, mat="tr_glass", out=0.05):
    for s in (-1, 1):
        k.box(a0, a1, s * w - out, s * w + out, z0, z1, mat)


def end_windows(k, a, w, z0, z1, mat="tr_glass", split=True, e=1):
    """Two cab windows (or one) on the flat end face at a (e = +1 front, -1 rear)."""
    a0, a1 = (a - 0.04, a + 0.06) if e > 0 else (a - 0.06, a + 0.04)
    if split:
        for s in (-1, 1):
            k.box(a0, a1, min(s * 0.12, s * (w - 0.25)), max(s * 0.12, s * (w - 0.25)), z0, z1, mat)
    else:
        k.box(a0, a1, -(w - 0.25), w - 0.25, z0, z1, mat)


def lamps(k, a, w, z, e=1, mat="tr_lamp", r=0.16):
    for s in (-1, 1):
        k.rod((a, s * w, z), (a + e * 0.08, s * w, z), r, mat, n=6)


def door(k, a, w, z0, z1, mat, width=0.5, out=0.05):
    for s in (-1, 1):
        k.box(a - width / 2, a + width / 2, s * w - out, s * w + out, z0, z1, mat)


def pantograph(k, a, z_roof, z_top=13.0, mat="tr_iron", e=1):
    """Diamond-less single-arm pantograph rising from the roof to the contact wire."""
    k.box(a - 0.35, a + 0.35, -0.5, 0.5, z_roof, z_roof + 0.35, "tr_frame")
    knee = (a - e * 0.9, 0, (z_roof + z_top) / 2 + 0.3)
    k.rod((a + e * 0.25, -0.35, z_roof + 0.35), knee, 0.06, mat, n=4)
    k.rod((a + e * 0.25, 0.35, z_roof + 0.35), knee, 0.06, mat, n=4)
    k.rod(knee, (a, 0, z_top - 0.2), 0.06, mat, n=4)
    k.box(a - 0.12, a + 0.12, -0.75, 0.75, z_top - 0.3, z_top, "tr_grey")


def mound(k, a0, a1, w, z0, h, mat, peaks=2):
    """Bulk load heaped above z0: low ends and sides, ridges along the middle."""
    n = 2 * peaks + 3
    st_ = []
    for i in range(n):
        t = i / (n - 1)
        a = a0 + (a1 - a0) * t
        bump = 0.75 + 0.25 * math.cos(t * math.tau * peaks) if 0 < i < n - 1 else 0.25
        st_.append((a, w * (0.92 if 0 < i < n - 1 else 0.8), z0, z0 + h * bump))
    tube(k, [[(a, b, z) for b, z in [(-ww, z0), (ww, z0), (ww * 0.92, z0 + (zt - z0) * 0.35),
                                       (ww * 0.45, z0 + (zt - z0) * 0.85), (0, zt), (-ww * 0.45, z0 + (zt - z0) * 0.85),
                                       (-ww * 0.92, z0 + (zt - z0) * 0.35)]] for a, ww, z0, zt in st_], mat)


# --- wagon parts -------------------------------------------------------------------------------

def rounded_plan(half, w, r, n=4):
    """Rectangle +-half x +-w with corners rounded by r, counter-clockwise [(a, b)]."""
    pts = []
    for ca, cb, t0 in ((half - r, w - r, 0), (-half + r, w - r, 90), (-half + r, -w + r, 180), (half - r, -w + r, 270)):
        for i in range(n + 1):
            t = math.radians(t0 + 90 * i / n)
            pts.append((ca + r * math.cos(t), cb + r * math.sin(t)))
    return pts


def chassis(k, fut=False, toy=False, z=2.2, bogies=True):
    """Running gear: bogies (or a skirt for monorail/maglev cars, big wheels for toys), frame, buffers."""
    if toy:
        for a in (-2.4, 2.4):
            toy_wheel(k, a)
        k.box(-HALF + 0.1, HALF - 0.1, -1.5, 1.5, 1.2, z, "tr_frame")
        for e in (1, -1):
            k.rod((e * (HALF - 0.1), 0, 1.7), (e * BUF, 0, 1.7), 0.3, "toy_yellow", n=8)
        return
    if fut:
        k.box(-HALF + 0.15, HALF - 0.15, -1.85, 1.85, 0.6, z, "tr_skirt")
        return
    if bogies:
        bogie(k, -2.5)
        bogie(k, 2.5)
    else:
        for a in (-2.2, 2.2):
            wheel(k, a, 0.5)
        for s in (-1, 1):
            for a in (-2.2, 2.2):
                k.box(a - 0.6, a + 0.6, s * 1.86 - 0.1, s * 1.86 + 0.1, 0.9, 1.9, "tr_frame")
    underframe(k, 1.2, z)
    buffers(k, z=1.75)


def toy_wheel(k, a, r=0.62, mat="toy_red", hub="toy_yellow"):
    for s in (-1, 1):
        k.rod((a, s * 1.45, r * K), (a, s * 1.95, r * K), r, mat, n=12)
        k.rod((a, s * 1.9, r * K), (a, s * 2.02, r * K), r * 0.45, hub, n=8)


def box_body(k, w=1.95, z0=2.2, z1=7.0, mat="cc", roof="tr_roof", r=0.45, half=HALF, fut=False):
    if fut:
        st_ = nose_st(half - 0.9, half, w, z0, z1, n=3, tip_w=0.8, tip_z=0.75, power=2.5)
        body(k, -half + 0.9, half - 0.9, w, z0, z1, mat, r=0.8)
        stations(k, st_, mat, r=0.8)
        stations(k, mirror_a(st_), mat, r=0.8)
        return
    body(k, -half, half, w, z0, z1 - 0.3, mat, r=0.2)
    body(k, -half + 0.1, half - 0.1, w - 0.05, z1 - 0.5, z1, roof, r=r)


def open_wagon(k, w=1.95, z0=2.2, z1=4.8, mat="cc", inner="tr_rust", half=HALF, fut=False, ribs=True):
    """Open box (coal, ore, fruit): four walls round a floor."""
    t = 0.18
    if fut:  # a tub with rounded corners
        k.prism(rounded_plan(half, w, 0.9), z0, z1, mat)
        k.prism(rounded_plan(half - t, w - t, 0.75), z1 - 0.05, z1 + 0.02, inner)
        return
    k.box(-half, half, -w, w, z0, z0 + 0.4, mat)
    k.box(-half, half, -w, -w + t, z0, z1, mat)
    k.box(-half, half, w - t, w, z0, z1, mat)
    k.box(-half, -half + t, -w, w, z0, z1, mat)
    k.box(half - t, half, -w, w, z0, z1, mat)
    k.box(-half + t, half - t, -w + t, w - t, z0 + 0.4, z0 + 0.5, inner)
    if ribs:
        for a in (-2.4, -0.8, 0.8, 2.4):
            for s in (-1, 1):
                k.box(a - 0.1, a + 0.1, s * w - 0.06, s * w + 0.06, z0, z1, "tr_iron")


def hopper(k, w=1.95, z0=2.4, z1=5.4, mat="cc", half=HALF, fut=False):
    """Ore / grain hopper: walls with sloped chutes below between the bogies."""
    open_wagon(k, w, z0 + 0.6, z1, mat, "tr_rust", half - 0.2, fut=fut, ribs=not fut)
    if not fut:
        for a in (-1.2, 1.2):
            k.prism([(a - 1.1, -w + 0.2), (a + 1.1, -w + 0.2), (a + 1.1, w - 0.2), (a - 1.1, w - 0.2)], 1.3, z0 + 0.6, mat)
            k.box(a - 0.5, a + 0.5, -0.6, 0.6, 1.0, 1.3, "tr_iron")


def flat_wagon(k, w=1.95, z=2.6, mat="cc", stakes=True, fut=False):
    k.box(-HALF, HALF, -w, w, z - 0.45, z, mat)
    if stakes and not fut:
        for a in (-3.2, -1.1, 1.1, 3.2):
            for s in (-1, 1):
                k.box(a - 0.1, a + 0.1, s * (w - 0.05) - 0.08, s * (w - 0.05) + 0.08, z, z + 2.2, "tr_iron")
    if fut:
        for e in (1, -1):
            k.box(e * HALF - (0.5 if e > 0 else 0), e * HALF + (0 if e > 0 else 0.5), -w, w, z, z + 1.6, mat)


def tank(k, r=1.55, z0=2.4, a0=-3.5, a1=3.5, mat="tr_tank", dome=True, bands=True, cc_band=True):
    """Horizontal tank on the frame: barrel, rounded ends, dome and walkway."""
    zc = z0 + r * K
    k.rod((a0 + 0.3, 0, zc), (a1 - 0.3, 0, zc), r, mat, n=14)
    for e, a in ((-1, a0 + 0.3), (1, a1 - 0.3)):
        k.blob(a, 0, zc, 0.45, r, r * K, mat, subdiv=2)
    if cc_band:
        k.rod((-1.2, 0, zc), (1.2, 0, zc), r + 0.015, "cc", n=14)
    if bands:
        for a in (a0 + 1.0, a1 - 1.0):
            k.rod((a - 0.06, 0, zc), (a + 0.06, 0, zc), r + 0.02, "tr_iron", n=14)
    if dome:
        k.cyl(0, 0, 0.5, zc + r * K - 0.3, zc + r * K + 0.5, "tr_iron", n=10)
    return zc + r * K


# --- loads -------------------------------------------------------------------------------------

def logs(k, a0, a1, z0, w=1.6, rows=2, r=0.38):
    n = int(round(2 * w / (2 * r)))
    for row in range(rows):
        cnt = n - row
        for i in range(cnt):
            b = -w + r + i * 2 * r + row * r
            zc = z0 + r * K + row * 2 * r * K * 0.85
            k.rod((a0, b, zc), (a1, b, zc), r, "tr_log", n=7)
            for a in (a0, a1):
                k.rod((a - 0.03, b, zc), (a + 0.03, b, zc), r * 0.9, "tr_log_end", n=7)


def coils(k, z0, n=3, r=0.75, mat="tr_coil"):
    for i in range(n):
        a = (i - (n - 1) / 2) * 2.2
        k.rod((a - 0.55, 0, z0 + r * K), (a + 0.55, 0, z0 + r * K), r, mat, n=12)
        k.rod((a - 0.57, 0, z0 + r * K), (a + 0.57, 0, z0 + r * K), r * 0.4, "tr_iron", n=8)


def reels(k, z0, mat="tr_paper", r=0.62):
    for a in (-2.4, -0.8, 0.8, 2.4):
        for b in (-0.85, 0.85):
            k.cyl(a, b, r, z0, z0 + 2.8, mat, n=12)
    k.box(-3.3, 3.3, -1.6, 1.6, z0 + 2.8, z0 + 2.9, "tr_crate")


def crates(k, a0, a1, z0, h, mats, w=1.7, n=4):
    step = (a1 - a0) / n
    for i in range(n):
        for j, (b0, b1) in enumerate(((-w, -0.05), (0.05, w))):
            m = mats[(i + j) % len(mats)]
            k.box(a0 + step * i + 0.05, a0 + step * (i + 1) - 0.05, b0, b1, z0, z0 + h * (1 if (i + j) % 3 else 0.8), m)


# --- wagons ------------------------------------------------------------------------------------

def passenger(fut=False):
    def build(k):
        chassis(k, fut)
        if fut:
            box_body(k, 2.0, 1.6, 7.4, "tr_white", fut=True)
            for s in (-1, 1):
                k.box(-2.9, 2.9, s * 2.0 - 0.05, s * 2.0 + 0.05, 2.1, 2.8, "cc")
            strip_windows(k, -2.8, 2.8, 2.0, 4.0, 5.7)
            for a in (-3.1, 3.1):
                door(k, a, 2.0, 2.4, 6.0, "tr_silver", 0.4)
            return
        body(k, -HALF, HALF, 1.95, 2.2, 6.9, "tr_cream", r=0.2)
        k.extrude(prof(1.95, 6.5, 7.6, 0.9, 1.1 * K / 2), "x", -HALF + 0.05, HALF - 0.05, "tr_roof")
        band(k, -HALF, HALF, 1.95, 2.2, 3.7, "cc")
        band(k, -HALF, HALF, 1.95, 6.2, 6.5, "cc")
        side_windows(k, -2.6, 2.6, 1.95, 4.2, 5.9, pitch=1.05, pane=0.78)
        for a in (-3.2, 3.2):
            door(k, a, 1.95, 2.4, 6.0, "tr_roof", 0.5)
    return build


def mail_van(fut=False):
    def build(k):
        chassis(k, fut)
        if fut:
            box_body(k, 2.0, 1.6, 7.4, "tr_white", fut=True)
            band(k, -2.9, 2.9, 2.0, 2.1, 3.0, "cc")
            band(k, -2.9, 2.9, 2.0, 5.5, 6.1, "tr_red")
            strip_windows(k, -1.0, 1.0, 2.0, 4.0, 5.2)
            return
        body(k, -HALF, HALF, 1.95, 2.2, 6.9, "tr_red", r=0.2)
        k.extrude(prof(1.95, 6.5, 7.6, 0.9, 1.1 * K / 2), "x", -HALF + 0.05, HALF - 0.05, "tr_roof")
        band(k, -HALF, HALF, 1.95, 5.6, 6.1, "cc")
        side_windows(k, -1.6, 1.6, 1.95, 4.4, 5.4, pitch=1.6, pane=0.5)
        for a in (-2.6, 2.6):
            door(k, a, 1.95, 2.5, 5.9, "tr_maroon", 0.9)
    return build


def van(colour="cc", stripe=None, slats=False, kind="goods", fut=False):
    """Covered van: goods (company colour), food (white reefer), livestock (slatted), armoured."""
    def build(k):
        chassis(k, fut)
        if fut:
            box_body(k, 2.0, 1.6, 7.0, colour, fut=True)
            band(k, -2.9, 2.9, 2.0, 5.6, 6.0, stripe or "tr_white")
            if kind == "livestock":
                for a in bk.frange(-2.4, 2.5, 0.8):
                    for s in (-1, 1):
                        k.box(a - 0.18, a + 0.18, s * 2.0 - 0.06, s * 2.0 + 0.06, 3.6, 5.2, "tr_black")
            elif kind == "armoured":
                door(k, 0, 2.0, 2.4, 5.2, "tr_iron", 1.0)
            else:
                door(k, 0, 2.0, 2.4, 5.4, "tr_silver", 1.8)
            return
        chassis_top = 2.2
        z1 = 6.4 if kind == "armoured" else 7.0
        if slats:
            body(k, -HALF, HALF, 1.85, chassis_top, z1 - 0.3, "tr_black", r=0.1)
            for z in bk.frange(chassis_top + 0.2, z1 - 0.5, 0.75):
                band(k, -HALF, HALF, 1.85, z, z + 0.45, colour, out=0.1)
            for a in (-HALF + 0.1, -1.2, 1.2, HALF - 0.1):
                for s in (-1, 1):
                    k.box(a - 0.12, a + 0.12, s * 1.95 - 0.06, s * 1.95 + 0.06, chassis_top, z1 - 0.3, "tr_iron")
            k.extrude(prof(1.95, z1 - 0.4, z1 + 0.3, 0.9, 0.7 * K / 2), "x", -HALF, HALF, "tr_roof")
            for a, b, m in ((-1.9, 0.6, "tr_cattle"), (0.2, -0.4, "tr_sheep"), (2.0, 0.5, "tr_cattle")):
                k.blob(a, b, 4.2, 0.9, 1.0, 1.6, m)
            return
        body(k, -HALF, HALF, 1.95, chassis_top, z1 - 0.3, colour, r=0.15)
        k.extrude(prof(1.95, z1 - 0.4, z1 + 0.2, 0.9, 0.6 * K / 2), "x", -HALF, HALF, "tr_roof")
        if stripe:
            band(k, -HALF, HALF, 1.95, z1 - 1.5, z1 - 1.0, stripe)
        if kind == "armoured":
            for a in (-2.6, 2.6):
                for s in (-1, 1):
                    k.box(a - 0.25, a + 0.25, s * 1.95 - 0.05, s * 1.95 + 0.05, 4.6, 5.2, "tr_glass")
            door(k, 0, 1.95, 2.5, 5.5, "tr_iron", 1.2)
            for a in (-3.0, -1.5, 1.5, 3.0):
                for s in (-1, 1):
                    k.box(a - 0.06, a + 0.06, s * 1.95 - 0.07, s * 1.95 + 0.07, 2.3, z1 - 0.4, "tr_iron")
        else:
            door(k, 0, 1.95, 2.4, z1 - 0.6, "tr_iron" if kind == "goods" else "tr_silver", 2.0)
            for a in (-1.0, 1.0):
                door(k, a, 1.97, 2.4, z1 - 0.6, "tr_frame", 0.06)
            for a in bk.frange(-3.3, -1.3, 0.5) + bk.frange(1.6, 3.4, 0.5):
                for s in (-1, 1):
                    k.box(a - 0.04, a + 0.04, s * 1.95 - 0.06, s * 1.95 + 0.06, 2.3, z1 - 0.4, "tr_frame")
    return build


def coal(full=False, fut=False, load="tr_coal"):
    def build(k):
        chassis(k, fut, bogies=False)
        open_wagon(k, z1=5.0, fut=fut, mat="cc")
        if full:
            mound(k, -3.3, 3.3, 1.75, 4.2, 2.0, load, peaks=2)
    return build


def ore_hopper(full=False, load="tr_ore", fut=False, mat="cc"):
    def build(k):
        chassis(k, fut)
        hopper(k, fut=fut, mat=mat)
        if full:
            mound(k, -3.0, 3.0, 1.7, 4.8, 1.9, load, peaks=3)
    return build


def grain(full=False, fut=False):
    """Covered hopper with roof hatches; full shows grain heaped in the open hatches."""
    def build(k):
        chassis(k, fut)
        if fut:
            box_body(k, 1.95, 1.6, 6.6, "tr_wheat" if False else "tr_cream", fut=True)
        else:
            body(k, -HALF + 0.1, HALF - 0.1, 1.95, 3.0, 6.4, "tr_cream", r=0.9, wb=1.5)
            band(k, -HALF + 0.1, HALF - 0.1, 1.97, 5.0, 5.5, "cc", out=0.02)
            for a in (-1.6, 1.6):
                k.prism([(a - 1.3, -1.5), (a + 1.3, -1.5), (a + 1.0, 1.5), (a - 1.0, 1.5)][::1], 1.3, 3.0, "tr_cream")
        top = 6.6 if fut else 6.4
        for a in (-2.2, 0, 2.2):
            k.box(a - 0.75, a + 0.75, -0.7, 0.7, top - 0.1, top + 0.25, "tr_roof" if not full else "tr_frame")
            if full:
                k.cyl(a, 0, 0.62, top + 0.2, top + 0.75, "tr_wheat", n=8, r_top=0.15)
    return build


def wood(full=False, fut=False):
    def build(k):
        chassis(k, fut, bogies=not fut)
        flat_wagon(k, z=2.6, mat="cc", fut=fut)
        if full:
            logs(k, -3.5, 3.5, 2.6, rows=3, r=0.4)
    return build


def flat(load=None, fut=False):
    def build(k):
        chassis(k, fut)
        flat_wagon(k, z=2.6, mat="cc", stakes=load != "steel", fut=fut)
        if load == "steel":
            for a in (-2.2, 0, 2.2):
                k.box(a - 0.75, a + 0.75, -1.2, 1.2, 2.6, 2.75, "tr_wood")
            coils(k, 2.75)
        elif load == "paper":
            reels(k, 2.6)
    return build


def oil(fut=False, mat="tr_tank", band_mat="cc"):
    def build(k):
        chassis(k, fut)
        if fut:
            k.box(-HALF + 0.2, HALF - 0.2, -1.9, 1.9, 1.6, 2.6, "tr_white")
            tank(k, 1.6, 2.2, -3.6, 3.6, mat, dome=False, bands=False)
            return
        k.box(-HALF, HALF, -1.6, 1.6, 2.0, 2.4, "tr_frame")
        top = tank(k, 1.5, 2.4, -3.5, 3.5, mat)
        k.box(-1.0, 1.0, -1.85, 1.85, 2.3, 2.5, "tr_iron")
        k.rod((-0.3, 1.0, 2.4), (-0.3, 1.0, top), 0.05, "tr_iron", n=4)
    return build


def fruit(full=False, fut=False):
    def build(k):
        chassis(k, fut)
        open_wagon(k, z1=4.6, mat="tr_green" if not fut else "tr_white", fut=fut, ribs=not fut)
        if fut:
            rim(k, -3.0, 3.0, 1.95, 3.4, 3.9, "cc")
        else:
            rim(k, -HALF, HALF, 1.95, 4.2, 4.6, "cc", out=0.05)
        if full:
            crates(k, -3.3, 3.3, 2.7, 2.6, ["tr_crate"], n=4)
            for a in (-2.5, -0.8, 0.8, 2.5):
                for b in (-0.85, 0.85):
                    k.blob(a, b, 5.35, 0.65, 0.65, 0.7, "tr_orange")
    return build


def rubber(full=False, fut=False):
    def build(k):
        chassis(k, fut)
        open_wagon(k, z1=4.4, mat="tr_brown" if not fut else "tr_white", fut=fut, ribs=not fut)
        rim(k, -HALF + (0.7 if fut else 0), HALF - (0.7 if fut else 0), 1.95, 3.9, 4.4, "cc", out=0.05)
        if full:
            for a in (-2.5, -0.8, 0.8, 2.5):
                for b in (-0.85, 0.85):
                    k.cyl(a, b, 0.7, 2.6, 5.0, "tr_rubber", n=10)
                    k.cyl(a, b, 0.72, 4.95, 5.05, "tr_paper", n=10)
    return build


def water(fut=False):
    return oil(fut, mat="tr_water_tank", band_mat="cc")


# --- engine parts ------------------------------------------------------------------------------

def drivers(k, xs, r=0.62, rod=True, mat="tr_wheel"):
    for a in xs:
        wheel(k, a, r, mat)
        for s in (-1, 1):
            k.rod((a, s * 1.78, r * K), (a, s * 1.84, r * K), r * 0.35, "tr_buffer", n=6)
    if rod and len(xs) > 1:
        for s in (-1, 1):
            k.box(min(xs) - 0.1, max(xs) + 0.1, s * 1.85, s * 1.92, r * K - 0.15, r * K + 0.1, "tr_silver")


def boiler(k, a0, a1, r, zc, mat="tr_black", box_mat="tr_iron"):
    k.rod((a0, 0, zc), (a1, 0, zc), r, mat, n=14)
    k.rod((a1 - 0.05, 0, zc), (a1 + 0.65, 0, zc), r * 1.04, box_mat, n=14)
    k.rod((a1 + 0.6, 0, zc), (a1 + 0.7, 0, zc), r * 0.9, "tr_frame", n=14)
    return a1 + 0.7


def chimney(k, a, z0, z1, r=0.32, mat="tr_black"):
    k.cyl(a, 0, r, z0, z1, mat, n=10)
    k.cyl(a, 0, r * 1.3, z1 - 0.3, z1, mat, n=10)


def cab(k, a0, a1, w, z0, z1, mat="cc", roof="tr_black", window=True):
    k.box(a0, a1, -w, w, z0, z1, mat)
    k.extrude(prof(w + 0.15, z1, z1 + 0.6, 0.8, 0.5), "x", a0 - 0.2, a1 + 0.15, roof)
    if window:
        for s in (-1, 1):
            k.box(a0 + 0.25, a1 - 0.25, s * w - 0.05, s * w + 0.05, z1 - 2.2, z1 - 0.6, "tr_glass")
        k.box(a1 - 0.03, a1 + 0.05, -w + 0.3, -0.35, z1 - 1.8, z1 - 0.6, "tr_glass")
        k.box(a1 - 0.03, a1 + 0.05, 0.35, w - 0.3, z1 - 1.8, z1 - 0.6, "tr_glass")


def tender(k, a0, a1, w=1.85, z0=2.0, z1=6.0, mat="cc", load="tr_coal", wheels=(-3.2, -2.0)):
    for a in wheels:
        wheel(k, a, 0.42)
    k.box(a0, a1, -1.5, 1.5, 1.0, z0, "tr_frame")
    k.box(a0, a1, -w, w, z0, z1, mat)
    k.box(a0, a1, -w - 0.03, w + 0.03, z0, z0 + 0.3, "tr_black")
    mound(k, a0 + 0.2, a1 - 0.3, w - 0.1, z1 - 0.2, 1.0, load, peaks=1)


def cowcatcher(k, a, z=0.3, w=1.7, mat="tr_iron"):
    k.prism([(a, -w), (a + 0.7, -0.2), (a + 0.7, 0.2), (a, w)], z, z + 1.1, mat)


def hood(k, a0, a1, w, z0, z1, mat, r=0.35):
    body(k, a0, a1, w, z0, z1, mat, r=r)


def warn_end(k, a, w, z0, z1, e=1, mat="tr_warn"):
    a0, a1 = (a - 0.02, a + 0.07) if e > 0 else (a - 0.07, a + 0.02)
    k.box(a0, a1, -w + 0.05, w - 0.05, z0, z1, mat)


# --- steam engines -----------------------------------------------------------------------------

def steam(k, kind):
    """Tender engines (jubilee, wills) and the tank engine."""
    if kind == "tank":
        drivers(k, [-1.6, -0.2, 1.2], 0.55)
        k.box(-3.6, 3.4, -1.45, 1.45, 1.0, 2.2, "tr_frame")
        k.box(-3.6, 3.5, -1.85, 1.85, 2.0, 2.3, "tr_black")
        boiler(k, -1.0, 2.6, 1.05, 4.6)
        k.box(-1.2, 2.2, -1.85, -1.1, 2.3, 5.3, "cc")  # side tanks
        k.box(-1.2, 2.2, 1.1, 1.85, 2.3, 5.3, "cc")
        band(k, -1.2, 2.2, 1.85, 4.6, 4.9, "tr_brass", out=0.02)
        cab(k, -3.4, -1.2, 1.8, 2.3, 7.4)
        k.box(-3.7, -3.4, -1.6, 1.6, 2.3, 5.4, "tr_black")  # bunker back
        chimney(k, 3.0, 6.6, 8.6)
        k.blob(1.0, 0, 7.0, 0.45, 0.45, 1.0, "tr_brass")
        buffers(k, 1.9)
        lamps(k, 3.75, 0.9, 2.6)
        return
    big = kind == "wills"
    drivers(k, [-0.7, 0.4, 1.5, 2.6] if big else [-0.6, 0.7, 2.0], 0.55 if big else 0.62)
    if big:
        wheel(k, 3.5, 0.36)
    else:
        wheel(k, 3.2, 0.38)
    k.box(-1.6, 3.6, -1.45, 1.45, 1.0, 2.2, "tr_frame")
    k.box(-1.5, 3.7, -1.85, 1.85, 2.2, 2.5, "tr_black" if big else "cc")
    zc = 4.9
    front = boiler(k, -0.3, 2.9, 1.15, zc, "tr_black" if big else "cc")
    for s in (-1, 1):
        k.rod((2.7, s * 1.45, 2.4), (3.6, s * 1.45, 2.4), 0.36, "tr_iron", n=8)
    chimney(k, 3.25, zc + 2.4, 9.0 if not big else 9.2)
    k.blob(1.3, 0, zc + 2.6, 0.5, 0.5, 1.1, "tr_brass" if not big else "tr_black")
    cab(k, -1.7, -0.2, 1.85, 2.5, 7.6, "cc")
    tender(k, -3.85, -1.95, mat="cc", wheels=(-3.4, -2.4))
    if big:
        cowcatcher(k, 3.6)
        k.cyl(3.8, 0, 0.32, zc + 1.0, zc + 1.7, "tr_lamp", n=8)
        k.blob(2.0, 0, zc + 2.7, 0.35, 0.35, 0.6, "tr_brass")  # bell
    else:
        k.box(3.6, 3.85, -1.7, 1.7, 1.4, 2.3, "tr_buffer")
        for s in (-1, 1):
            k.rod((3.7, s * 1.15, 1.9), (BUF, s * 1.15, 1.9), 0.17, "tr_iron", n=6)
        lamps(k, 3.85, 0.9, 2.7)
    return front


def jubilee(k):
    steam(k, "jubilee")


def wills(k):
    steam(k, "wills")


def tank_engine(k):
    steam(k, "tank")


def a4(k):
    """Streamlined pacific: wedge casing over the boiler, valances over the wheels, tender."""
    drivers(k, [-0.6, 0.6, 1.8], 0.6, rod=True)
    wheel(k, 3.0, 0.36)
    k.box(-1.6, 3.6, -1.45, 1.45, 1.0, 2.2, "tr_frame")
    st_ = [(-1.7, 1.85, 1.9, 7.6), (0.6, 1.85, 1.9, 7.0), (2.0, 1.8, 1.9, 6.6)] + \
        [(a, w, z0, z1) for a, w, z0, z1 in nose_st(2.0, 3.95, 1.8, 1.9, 6.6, n=5, tip_w=0.5, tip_z=0.35, power=1.6)][1:]
    stations(k, st_, "cc", r=1.0)
    stations(k, [(a, w * 1.01, z0 - 0.02, z0 + 0.7) for a, w, z0, z1 in st_], "tr_black", r=0.05)  # valance skirt
    k.box(-1.6, -0.3, -1.9, 1.9, 5.0, 6.4, "tr_glass")
    chimney(k, 2.6, 6.2, 7.2, 0.3, "tr_black")
    tender(k, -3.85, -1.95, z1=6.4, mat="cc", wheels=(-3.4, -2.4))
    k.box(-3.85, -1.95, -1.88, 1.88, 5.9, 6.4, "tr_black")


# --- diesels -----------------------------------------------------------------------------------

def double_cab(k, mat="cc", z1=7.0, nose=0.0, roof="tr_roof", grille=True, w=1.95, warn=True, panto=False):
    """Box body with a cab at each end (class 25/47 style); nose > 0 gives short sloped noses."""
    chassis_box(k)
    a_end = HALF - nose
    body(k, -a_end, a_end, w, 2.2, z1, mat, r=0.5)
    if nose:
        for e in (1, -1):
            st_ = [(e * a_end, w, 2.2, z1)] + [(e * (a_end + nose * t), w - 0.15 * t, 2.2, z1 - 2.2 * t ** 1.5)
                                                for t in (0.5, 1.0)]
            stations(k, st_ if e > 0 else list(reversed(st_)), mat, r=0.5)
    k.extrude(prof(w - 0.3, z1 - 0.1, z1 + 0.3, 0.6, 0.35), "x", -a_end + 0.8, a_end - 0.8, roof)
    for e in (1, -1):
        ae = e * HALF
        end_windows(k, ae - e * (0.0 if not nose else 0.2), w - (0.2 if nose else 0), z1 - 2.0, z1 - 0.7, e=e)
        if warn:
            warn_end(k, ae, w, 2.3, z1 - 2.2, e)
        lamps(k, ae, 1.2, 2.9, e)
        for s in (-1, 1):
            k.box(e * (HALF - 1.4) - 0.45, e * (HALF - 1.4) + 0.45, s * w - 0.05, s * w + 0.05, z1 - 2.1, z1 - 0.8, "tr_glass")
    if grille:
        for s in (-1, 1):
            for a in (-1.4, 0.2, 1.4):
                k.box(a - 0.45, a + 0.45, s * w - 0.05, s * w + 0.05, 4.5, 5.4, "tr_frame")
    band(k, -a_end, a_end, w, 3.0, 3.35, "tr_white" if mat == "cc" else "cc", out=0.03)
    if panto:
        for e in (1, -1):
            pantograph(k, e * 1.8, z1 + 0.3, e=e)


def chassis_box(k, bogie_a=2.4):
    bogie(k, -bogie_a, 1.7, 0.45)
    bogie(k, bogie_a, 1.7, 0.45)
    underframe(k, 1.3, 2.2)
    k.box(-1.2, 1.2, -1.5, 1.5, 1.0, 1.4, "tr_iron")  # fuel tank
    buffers(k, 1.8)


def d25(k):
    double_cab(k, "cc", 7.0)


def d37(k):
    double_cab(k, "cc", 7.0, nose=0.8)


def e30(k):
    double_cab(k, "cc", 7.0, grille=False, panto=True, roof="tr_grey")
    for s in (-1, 1):
        for a in (-1.0, 0, 1.0):
            k.box(a - 0.35, a + 0.35, s * 1.95 - 0.05, s * 1.95 + 0.05, 4.4, 5.6, "tr_frame")


def hood_unit(k, cab_a, cab_len=1.6, long_hood="cc", wide=False, z_hood=6.0, z_cab=7.5, mat="cc",
              bogie_a=2.5, stripe="tr_warn"):
    """North American road switcher: walkway frame, low hoods, one cab at cab_a (front end +a)."""
    for a in (-bogie_a, bogie_a):
        bogie(k, a, 1.9, 0.42)
        for s in (-1, 1):
            k.box(a - 0.4, a + 0.4, s * 1.3, s * 1.5, 1.3, 1.6, "tr_iron")
    k.box(-HALF, HALF, -1.95, 1.95, 1.9, 2.4, "tr_frame")
    k.box(-HALF - 0.05, HALF + 0.05, -1.97, 1.97, 2.0, 2.3, stripe)
    k.box(-1.3, 1.3, -1.5, 1.5, 1.0, 1.9, "tr_iron")
    c0, c1 = cab_a - cab_len / 2, cab_a + cab_len / 2
    w = 1.45
    rear, front = (-HALF + 0.25, c0), (c1, HALF - 0.25)
    long_ = rear if c0 - rear[0] >= front[1] - c1 else front
    if rear[1] - rear[0] > 0.4:
        hood(k, rear[0], rear[1], w, 2.4, z_hood if long_ is rear else z_hood - 0.8, long_hood)
    if front[1] - front[0] > 0.4:
        if wide:
            stations(k, [(c1, 1.9, 2.4, z_hood), (HALF - 0.1, 1.85, 2.4, z_hood - 0.5)], mat, r=0.3)
        else:
            even = abs((front[1] - front[0]) - (rear[1] - rear[0])) < 0.1  # centre cab: both hoods alike
            hood(k, front[0], front[1], w, 2.4, z_hood if long_ is front or even else z_hood - 0.8, mat)
    cw = 1.9 if wide else 1.75
    k.box(c0, c1, -cw, cw, 2.4, z_cab, mat)
    k.extrude(prof(cw + 0.1, z_cab, z_cab + 0.4, 0.8, 0.35), "x", c0 - 0.1, c1 + 0.1, "tr_roof")
    for s in (-1, 1):
        k.box(c0 + 0.2, c1 - 0.2, s * cw - 0.05, s * cw + 0.05, z_cab - 1.7, z_cab - 0.5, "tr_glass")
    end_windows(k, c1, cw, z_cab - 1.7, z_cab - 0.5, e=1)
    end_windows(k, c0, cw, z_cab - 1.7, z_cab - 0.5, e=-1)
    even = abs((front[1] - front[0]) - (rear[1] - rear[0])) < 0.1
    for h0, h1 in [long_] + ([front] if even and long_ is rear else []):
        for a in bk.frange(h0 + 0.55, h1 - 0.4, 0.9):
            for s in (-1, 1):
                k.box(a - 0.3, a + 0.3, s * w - 0.05, s * w + 0.05, z_hood - 1.6, z_hood - 0.6, "tr_frame")
        for a in bk.frange(h0 + 0.75, h1 - 0.5, 1.6):
            k.cyl(a, 0, 0.55, z_hood + 0.1, z_hood + 0.35, "tr_frame", n=10)  # fans
    ex = c0 - 0.7 if long_ is rear else c1 + 0.7
    k.cyl(ex, 0, 0.18, z_hood, z_hood + 0.6, "tr_black", n=8)  # exhaust stack
    lamps(k, HALF - 0.1, 0.6, 3.0)
    for e in (1, -1):
        for s in (-1, 1):
            k.box(e * HALF - 0.05, e * HALF + 0.05, s * 1.9, s * 1.95, 2.4, 3.8, "tr_warn")
    for e in (1, -1):
        k.box(min(e * HALF, e * BUF), max(e * HALF, e * BUF), -0.25, 0.25, 1.6, 2.0, "tr_iron")


def mjs250(k):
    """Small switcher: cab at the rear, one long hood."""
    hood_unit(k, -2.6, 1.8, z_hood=5.8, z_cab=7.2, bogie_a=2.2)


def cs2400(k):
    hood_unit(k, 1.5, 1.5, z_hood=6.0, z_cab=7.4)


def centennial(k):
    hood_unit(k, 2.25, 1.4, z_hood=6.3, z_cab=7.6, wide=True, bogie_a=2.6)


def cs4000(k):
    hood_unit(k, 2.1, 1.6, z_hood=6.4, z_cab=7.8, wide=True, bogie_a=2.6)
    for a in (-1.5, -0.2):
        k.box(a - 0.5, a + 0.5, -1.2, 1.2, 6.4, 6.9, "tr_frame")


def kelling(k):
    """Centre-cab freight diesel, symmetric (4 directions)."""
    hood_unit(k, 0.0, 1.5, z_hood=5.8, z_cab=7.4)


def mjs1000(k):
    """Box-cab diesel, cabs at both ends (4 directions)."""
    double_cab(k, "cc", 7.2, nose=0.0, warn=False)
    band(k, -HALF, HALF, 1.95, 2.3, 2.9, "tr_warn", out=0.03)


def turbo(k):
    """Streamlined cab unit (bulldog nose); the rear head is the same unit turned round."""
    bogie(k, -2.4, 1.8, 0.45)
    bogie(k, 2.4, 1.8, 0.45)
    k.box(-HALF, HALF - 0.6, -1.6, 1.6, 1.4, 2.3, "tr_frame")
    st_ = nose_st(1.9, 3.95, 1.95, 2.0, 7.4, n=6, tip_w=0.6, tip_z=0.35, power=1.8)
    body(k, -HALF, 1.9, 1.95, 2.0, 7.4, "cc", r=0.8)
    stations(k, st_, "cc", r=0.8)
    stations(k, [(a, w * 1.01, z0 - 0.02, z0 + 1.0) for a, w, z0, z1 in st_] + [], "tr_warn", r=0.05)
    k.box(-HALF, 1.9, -1.98, 1.98, 1.98, 3.0, "tr_warn")
    for s in (-1, 1):
        k.box(1.95, 2.6, s * 1.4, s * 1.0, 6.0, 6.8, "tr_glass")
    stations(k, [(a, w * 1.02, z0 + (z1 - z0) * 0.7, z1 + 0.02) for a, w, z0, z1 in st_[1:3]], "tr_glass", r=0.6)
    for a in (-2.8, -1.6, -0.4, 0.8):
        for s in (-1, 1):
            k.box(a - 0.3, a + 0.3, s * 1.95 - 0.05, s * 1.95 + 0.05, 5.0, 5.8, "tr_frame")
    k.box(-HALF - 0.05, -HALF + 0.05, -1.7, 1.7, 2.2, 7.2, "tr_frame")
    k.cyl(3.2, 0, 0.22, 4.0, 4.5, "tr_lamp", n=8)


# --- multiple units and high speed -------------------------------------------------------------

def mu_car(k, z1=7.2, mat="cc", lower="tr_white", nose=None, panto=False, front_window="split"):
    """Multiple-unit driving car: bogies, body with window band, cab end at +a (nose stations or flat)."""
    chassis_box(k, 2.5)
    a_body = 2.6 if nose else HALF
    body(k, -HALF, a_body, 1.95, 2.2, z1, mat, r=0.6)
    band(k, -HALF, a_body, 1.95, 2.2, 3.6, lower, out=0.03) if lower else None
    side_windows(k, -3.2, a_body - 1.2, 1.95, 4.3, 5.9, pitch=1.0, pane=0.8)
    for a in (-3.4, a_body - 0.9):
        door(k, a, 1.95, 2.5, 6.1, "tr_roof", 0.55)
    if nose:
        st_ = nose(a_body, HALF + 0.2, 1.95, 2.2, z1)
        stations(k, st_, mat, r=0.6)
        stations(k, [(a, w * 1.01, z0 - 0.01, z0 + 1.4) for a, w, z0, z1 in st_], lower or mat, r=0.05)
        stations(k, [(a, w * 1.03, z0 + (z1 - z0) * 0.62, z1 + 0.03) for a, w, z0, z1 in st_[1:4]], "tr_glass", r=0.6)
    else:
        warn_end(k, HALF, 1.95, 2.3, z1 - 2.4)
        end_windows(k, HALF, 1.95, z1 - 2.2, z1 - 0.7, split=front_window == "split")
    lamps(k, HALF + 0.1, 1.2, 3.0)
    k.extrude(prof(1.6, z1 - 0.05, z1 + 0.25, 0.5, 0.3), "x", -HALF + 0.3, a_body - 0.3, "tr_roof")
    if panto:
        pantograph(k, -1.6, z1 + 0.25, e=-1)


def dmu(k):
    mu_car(k, 7.0, "tr_green", lower="cc")
    k.box(-0.6, 0.6, -0.9, 0.9, 7.2, 7.6, "tr_frame")  # exhaust/radiator


def dash(k):
    mu_car(k, 7.2, "tr_white", lower="cc",
           nose=lambda a0, a1, w, z0, z1: nose_st(a0, a1, w, z0, z1, n=4, tip_w=0.8, tip_z=0.6, power=2.2))
    band(k, -HALF, 2.6, 1.95, 6.2, 6.5, "cc", out=0.03)


def power_car(k, mat="tr_white", stripe="cc", z1=7.4, nose_len=2.4, tip_z=0.32, tip_w=0.55, panto=False,
              glass_mat="tr_glass", cab_win=(0.62, 1.0)):
    """High-speed power car: long streamlined nose at +a, flat inner end with gangway at -a."""
    chassis_box(k, 2.5)
    a_body = HALF - nose_len + 0.25
    body(k, -HALF, a_body, 1.95, 2.0, z1, mat, r=0.9)
    st_ = nose_st(a_body, BUF, 1.95, 2.0, z1, n=6, tip_w=tip_w, tip_z=tip_z, power=1.5)
    stations(k, st_, mat, r=0.9)
    k.box(-HALF, a_body, -1.98, 1.98, 2.0, 2.6, "tr_skirt")
    stations(k, [(a, w * 1.012, z0 - 0.01, z0 + 0.6) for a, w, z0, z1 in st_], "tr_skirt", r=0.05)
    stations(k, [(a, w * 1.012, z0 + 0.6, z0 + 1.4) for a, w, z0, z1 in st_[:-1]] +
             [(-HALF, 1.97, 2.6, 3.4)][:0], stripe, r=0.05)
    band(k, -HALF, a_body, 1.95, 2.6, 3.4, stripe, out=0.02)
    lo, hi = cab_win
    stations(k, [(a, w * 1.025, z0 + (z1 - z0) * lo, z1 + 0.04) for a, w, z0, z1 in st_[1:4]], glass_mat, r=0.9)
    for s in (-1, 1):
        k.box(-3.2, -2.0, s * 1.95 - 0.05, s * 1.95 + 0.05, 4.6, 5.8, "tr_frame")  # louvres
    k.box(-HALF - 0.05, -HALF + 0.05, -0.8, 0.8, 2.6, z1 - 0.4, "tr_frame")  # gangway
    lamps(k, st_[-2][0], st_[-2][1] * 0.6, 2.9)
    if panto:
        pantograph(k, -2.2, z1 + 0.05, e=-1)


def hst(k):
    power_car(k, "tr_white", "cc", 7.2, nose_len=2.1, tip_z=0.4, tip_w=0.7)
    k.box(-1.6, 0.4, -1.97, 1.97, 3.6, 6.4, "cc")


def tim(k):
    power_car(k, "tr_silver", "cc", 7.3, nose_len=2.6, tip_z=0.3, tip_w=0.55, panto=True)


def asiastar(k):
    power_car(k, "tr_white", "cc", 7.0, nose_len=3.3, tip_z=0.22, tip_w=0.35, panto=True)
    band(k, -HALF, 0.6, 1.95, 4.0, 4.3, "tr_teal" if False else "cc", out=0.03)


# --- monorail and maglev ------------------------------------------------------------------------

def guided(k, mat="tr_white", stripe="cc", z1=7.0, nose_len=2.4, sym=False, tip_z=0.35, tip_w=0.5, eye=False,
           fins=False, cc_roof=False, skirt="tr_skirt"):
    """Monorail / maglev car: skirt over the beam, smooth body, nose at +a (and at -a when sym)."""
    k.box(-HALF + 0.3, HALF - 0.3, -1.6, 1.6, 0.6, 2.2, skirt)
    a1 = HALF - nose_len + 0.2
    a0 = -a1 if sym else -HALF
    body(k, a0, a1, 2.0, 1.4, z1, mat, r=1.0, wb=1.85)
    st_ = nose_st(a1, BUF - 0.05, 2.0, 1.4, z1, n=6, tip_w=tip_w, tip_z=tip_z, power=1.6)
    st_ = [(a, w, z0, z1_) for a, w, z0, z1_ in st_]
    ends = [st_] + ([mirror_a(st_)] if sym else [])
    for s_ in ends:
        stations(k, s_, mat, r=1.0)
    band(k, a0, a1, 2.0, 2.4, 3.2, stripe, out=0.02)
    for s_ in ends:
        stations(k, [(a, w * 1.012, z0 + 1.0, z0 + 1.8) for a, w, z0, z1_ in s_], stripe, r=0.05)
        rising = s_[0][0] < s_[-1][0]
        part = s_[1:4] if rising else s_[-4:-1]
        stations(k, [(a, w * 1.025, z0 + (z1_ - z0) * 0.6, z1_ + 0.04) for a, w, z0, z1_ in part], "tr_glass", r=1.0)
    strip_windows(k, a0 + 0.4, a1 - 0.4, 2.0, 4.4, 5.7)
    if cc_roof:
        k.extrude(prof(1.4, z1 - 0.05, z1 + 0.2, 0.6, 0.2), "x", a0 + 0.3, a1 - 0.3, stripe)
    if eye:
        k.blob(st_[-1][0] - 0.25, 0, 3.4, 0.25, 0.5, 1.1, "tr_lamp")
    else:
        lamps(k, st_[-2][0], st_[-2][1] * 0.6, 2.8)
    if fins:
        k.prism([(-HALF + 0.4, -0.08), (-HALF + 1.6, -0.08), (-HALF + 1.6, 0.08), (-HALF + 0.4, 0.08)], z1, z1 + 1.3, stripe)


def x2001(k):
    guided(k, "tr_white", "cc", 7.0, nose_len=1.4, sym=True, tip_z=0.5, tip_w=0.7)


def z1(k):
    guided(k, "tr_white", "cc", 7.0, nose_len=2.6, tip_z=0.3)


def lev1(k):
    guided(k, "tr_silver", "cc", 6.6, nose_len=1.3, sym=True, tip_z=0.45, tip_w=0.65, cc_roof=True)


def lev2(k):
    guided(k, "tr_white", "cc", 6.8, nose_len=1.6, sym=True, tip_z=0.35, tip_w=0.55, eye=True)


def lev3(k):
    guided(k, "tr_white", "cc", 6.6, nose_len=2.9, tip_z=0.25, tip_w=0.4, fins=False)


def lev4(k):
    guided(k, "tr_silver", "cc", 6.4, nose_len=3.4, tip_z=0.18, tip_w=0.3, cc_roof=True)


# --- toyland -----------------------------------------------------------------------------------

def toy_chassis(k, wheels=(-2.4, 2.4), mat="toy_blue", z=2.0):
    for a in wheels:
        toy_wheel(k, a)
    k.box(-HALF + 0.1, HALF - 0.1, -1.6, 1.6, 1.0, z, mat)


def toy_steam(k, size=1.0, body_mat="cc", cab_mat="toy_red", funnel="toy_yellow", boiler_mat="toy_green",
              n_wheels=2, roof="toy_yellow"):
    """Chunky toy steam engine: fat boiler, huge funnel with a flared top, cab with a big round roof."""
    xs = [-2.4, 0.0, 2.2][:n_wheels + 1] if n_wheels == 2 else [-2.6, -0.6, 1.4, 3.0]
    for a in xs[:max(2, n_wheels)] if n_wheels > 2 else [-2.2, 1.6]:
        toy_wheel(k, a, 0.7 * size)
    k.box(-HALF, HALF - 0.2, -1.7, 1.7, 1.2, 2.4, "toy_blue")
    r = 1.25 * size
    zc = 2.4 + r * K * 0.95
    k.rod((-0.8, 0, zc), (3.2, 0, zc), r, boiler_mat, n=14)
    k.rod((3.15, 0, zc), (3.6, 0, zc), r * 1.1, "toy_red", n=14)
    k.rod((3.55, 0, zc), (3.75, 0, zc), r * 0.5, "toy_yellow", n=10)
    for a in (0.5, 1.8):
        k.rod((a - 0.15, 0, zc), (a + 0.15, 0, zc), r * 1.06, "toy_yellow", n=14)
    top = zc + r * K
    k.cyl(2.6, 0, 0.42, top - 0.5, top + 1.6, funnel, n=12)
    k.cyl(2.6, 0, 0.42, top + 1.6, top + 2.6, funnel, n=12, r_top=0.8)
    k.blob(1.2, 0, top + 0.1, 0.5, 0.5, 1.1, "toy_red")
    k.box(-3.6, -0.7, -1.8, 1.8, 2.4, 6.4 * min(size, 1.1) + 0.6, cab_mat)
    k.box(-3.62, -0.68, -1.82, 1.82, 3.0, 3.5, body_mat)
    for s in (-1, 1):
        k.rod((-2.15, s * 1.75, 5.4), (-2.15, s * 1.88, 5.4), 0.55, "toy_white", n=12)
    ct = 6.4 * min(size, 1.1) + 0.6
    k.extrude([(b, z) for b, z in prof(2.1, ct, ct + 1.2, 1.2, 1.2)], "x", -3.9, -0.4, roof)
    k.rod((HALF, 0, 1.9), (BUF, 0, 1.9), 0.32, "toy_yellow", n=8)
    k.rod((-HALF, 0, 1.9), (-BUF, 0, 1.9), 0.32, "toy_yellow", n=8)
    k.box(3.3, 3.8, -1.6, 1.6, 0.6, 1.4, "toy_red")  # buffer plank / cowcatcher
    return 2.6, top + 2.6


def toy_ploddy(k):
    toy_steam(k, 0.9, "cc", "toy_red", "toy_yellow", "toy_green")


def toy_powernaut(k):
    toy_steam(k, 1.0, "cc", "toy_blue", "toy_red", "toy_purple", roof="toy_red")


def toy_mightymover(k):
    toy_steam(k, 1.1, "cc", "toy_orange", "toy_blue", "toy_red", n_wheels=3, roof="toy_blue")


def toy_diesel(k, body_mat="toy_yellow", cab="toy_red", roof="toy_blue"):
    """Toy diesel: a rounded block body with a big bubble cab and porthole windows."""
    toy_chassis(k, (-2.3, 2.3))
    body(k, -HALF, 1.0, 1.85, 2.0, 5.8, body_mat, r=0.9)
    k.blob(-1.2, 0, 5.8, 1.6, 1.3, 0.6, roof)
    for a in (-2.6, -1.2, 0.2):
        for s in (-1, 1):
            k.rod((a, s * 1.8, 4.2), (a, s * 1.95, 4.2), 0.42, "toy_white", n=10)
    k.box(1.0, 3.5, -1.85, 1.85, 2.0, 7.0, cab)
    k.extrude(prof(2.05, 7.0, 8.0, 1.0, 1.0), "x", 0.8, 3.7, roof)
    band(k, -HALF, 3.5, 1.85, 2.6, 3.2, "cc")
    for s in (-1, 1):
        k.box(1.4, 3.1, s * 1.85 - 0.05, s * 1.85 + 0.05, 4.8, 6.3, "toy_cyan")
    k.box(3.48, 3.56, -1.4, 1.4, 4.8, 6.3, "toy_cyan")
    k.rod((HALF, 0, 1.6), (BUF, 0, 1.6), 0.32, "toy_yellow", n=8)
    k.rod((-HALF, 0, 1.6), (-BUF, 0, 1.6), 0.32, "toy_yellow", n=8)
    k.cyl(-0.3, 0, 0.3, 5.8, 7.0, "toy_red", n=10)
    k.cyl(-0.3, 0, 0.36, 7.0, 7.3, "toy_yellow", n=10)


def toy_pdiesel(k):
    toy_diesel(k, "toy_yellow", "toy_red", "toy_blue")


def toy_ndiesel(k):
    toy_diesel(k, "toy_mint", "toy_purple", "toy_pink")


def toy_z99(k):
    """Toy monorail: a fat round capsule with a bubble canopy and a stubby fin."""
    k.box(-HALF + 0.3, HALF - 0.3, -1.6, 1.6, 0.6, 2.2, "toy_blue")
    st_ = [(-HALF, 1.4, 1.6, 5.0), (-2.6, 1.95, 1.4, 6.6)] + nose_st(1.6, BUF, 1.95, 1.4, 6.6, n=5, tip_w=0.45,
                                                                          tip_z=0.45, power=2.0)
    stations(k, st_, "cc", r=1.2)
    stations(k, [(a, w * 1.012, z0 - 0.02, z0 + 1.0) for a, w, z0, z1 in st_], "toy_yellow", r=0.1)
    k.blob(1.2, 0, 6.5, 1.5, 1.2, 1.4, "toy_cyan")
    for a in (-2.2, -0.8):
        for s in (-1, 1):
            k.rod((a, s * 1.9, 4.6), (a, s * 2.02, 4.6), 0.45, "toy_white", n=10)
    k.prism([(-3.6, -0.1), (-2.4, -0.1), (-2.4, 0.1), (-3.6, 0.1)], 6.0, 8.2, "toy_red")
    k.blob(BUF - 0.2, 0, 2.6, 0.2, 0.5, 0.8, "toy_yellow")


def toy_rocketeer(k):
    """Toy maglev rocket, symmetric: a striped tube with cone ends and fins at both ends."""
    k.box(-HALF + 0.3, HALF - 0.3, -1.6, 1.6, 0.6, 2.2, "toy_purple")
    zc = 4.4
    k.rod((-2.2, 0, zc), (2.2, 0, zc), 1.7, "cc", n=16)
    for e in (1, -1):
        k.lathe(0, 0, [], "toy_red") if False else None
        k.rod((e * 2.2, 0, zc), (e * 2.4, 0, zc), 1.72, "toy_yellow", n=16)
        cone = [(e * (2.4 + 1.5 * t), 1.7 * (1 - t) + 0.08) for t in (0, 0.35, 0.65, 1.0)]
        rings = []
        for a, r in cone:
            rings.append([(a, r * math.cos(i * math.tau / 16), zc + r * K * math.sin(i * math.tau / 16)) for i in range(16)])
        tube(k, rings if e > 0 else list(reversed(rings)), "toy_red")
        for s in (-1, 1):
            k.prism([(e * 1.0, s * 1.5), (e * 2.4, s * 1.5), (e * 2.4, s * 2.15), (e * 1.4, s * 2.15)], 1.2, 2.2,
                    "toy_yellow") if True else None
    for a in (-1.2, 0.0, 1.2):
        for s in (-1, 1):
            k.rod((a, s * 1.62, zc + 0.6), (a, s * 1.78, zc + 0.6), 0.45, "toy_cyan", n=10)
    k.rod((-0.6, 0, zc), (0.6, 0, zc), 1.74, "toy_yellow", n=16)


def toy_wagon_base(k, mat):
    toy_chassis(k, (-2.4, 2.4), "toy_blue")
    k.box(-HALF, HALF, -1.9, 1.9, 2.0, 2.6, mat)
    k.rod((HALF, 0, 1.6), (BUF, 0, 1.6), 0.3, "toy_yellow", n=8)
    k.rod((-HALF, 0, 1.6), (-BUF, 0, 1.6), 0.3, "toy_yellow", n=8)


def toy_passenger(k):
    toy_wagon_base(k, "cc")
    body(k, -HALF + 0.1, HALF - 0.1, 1.85, 2.6, 6.6, "toy_yellow", r=0.4)
    k.extrude(prof(2.05, 6.6, 7.8, 1.2, 1.2), "x", -HALF - 0.1, HALF + 0.1, "toy_red")
    for a in (-2.4, -0.8, 0.8, 2.4):
        for s in (-1, 1):
            k.rod((a, s * 1.8, 4.9), (a, s * 1.95, 4.9), 0.55, "toy_cyan", n=12)
    band(k, -HALF + 0.1, HALF - 0.1, 1.85, 2.6, 3.4, "cc")


def toy_mail(k):
    toy_wagon_base(k, "cc")
    body(k, -HALF + 0.1, HALF - 0.1, 1.85, 2.6, 6.6, "toy_red", r=0.4)
    k.extrude(prof(2.05, 6.6, 7.6, 1.2, 1.0), "x", -HALF - 0.1, HALF + 0.1, "toy_yellow")
    for s in (-1, 1):  # envelope on the side
        k.box(-1.3, 1.3, s * 1.85 - 0.05, s * 1.85 + 0.05, 3.6, 5.6, "toy_white")
        k.prism([(-1.2, s * 1.9), (1.2, s * 1.9), (0, s * 1.9 + s * 0.02)], 4.5, 5.55, "toy_blue") if False else None
        k.box(-1.25, 1.25, s * 1.9 - 0.03, s * 1.9 + 0.03, 5.2, 5.5, "toy_blue")
    band(k, -HALF + 0.1, HALF - 0.1, 1.85, 2.6, 3.2, "cc")


def toy_open(k, mat, load=None, cols=None):
    toy_wagon_base(k, "cc")
    t = 0.25
    for a0, a1, b0, b1 in ((-HALF, HALF, -1.9, -1.9 + t), (-HALF, HALF, 1.9 - t, 1.9), (-HALF, -HALF + t, -1.9, 1.9),
                           (HALF - t, HALF, -1.9, 1.9)):
        k.box(a0, a1, b0, b1, 2.6, 4.8, mat)
    rim(k, -HALF, HALF, 1.9, 4.5, 4.9, "toy_white", out=0.05, t=0.3)
    k.box(-HALF + t, HALF - t, -1.9 + t, 1.9 - t, 2.6, 2.75, "toy_wood")
    if load:
        load(k)


def toy_tankcar(k, mat, lid="toy_red", full=None):
    toy_wagon_base(k, "cc")
    zc = 2.6 + 1.5 * K
    k.rod((-3.3, 0, zc), (3.3, 0, zc), 1.5, mat, n=14)
    for a in (-3.3, 3.3):
        k.blob(a, 0, zc, 0.5, 1.5, 1.5 * K, mat, subdiv=2)
    for a in (-1.8, 1.8):
        k.rod((a - 0.15, 0, zc), (a + 0.15, 0, zc), 1.56, "toy_white", n=14)
    k.cyl(0, 0, 0.7, zc + 1.5 * K - 0.4, zc + 1.5 * K + 0.6, lid, n=12)
    if full:
        full(k, zc + 1.5 * K + 0.6)


def toy_van(k, mat, roof, deco):
    toy_wagon_base(k, "cc")
    body(k, -HALF + 0.1, HALF - 0.1, 1.85, 2.6, 6.8, mat, r=0.3)
    k.extrude(prof(2.0, 6.8, 7.6, 1.0, 0.8), "x", -HALF - 0.05, HALF + 0.05, roof)
    deco(k)


def sweets_deco(k):
    for a, m in ((-2.0, "toy_pink"), (0, "toy_yellow"), (2.0, "toy_cyan")):
        for s in (-1, 1):
            k.rod((a, s * 1.82, 4.6), (a, s * 1.98, 4.6), 0.7, m, n=12)
            k.rod((a, s * 1.9, 4.6), (a, s * 2.02, 4.6), 0.3, "toy_white", n=8)


def toys_deco(k):
    for s in (-1, 1):
        for a, m in ((-2.2, "toy_red"), (-0.7, "toy_yellow"), (0.8, "toy_green"), (2.3, "toy_blue")):
            k.box(a - 0.55, a + 0.55, s * 1.85 - 0.06, s * 1.85 + 0.06, 3.2 + (a > 0) * 0.5, 4.3 + (a > 0) * 0.5, m)
        k.box(-3.0, 3.0, s * 1.85 - 0.04, s * 1.85 + 0.04, 5.4, 5.9, "toy_white")


def toy_heap(mat, h=2.0):
    def load(k):
        mound(k, -3.2, 3.2, 1.6, 3.8, h, mat, peaks=2)
    return load


def toy_sugar_load(k):
    for i, a in enumerate((-2.6, -1.3, 0, 1.3, 2.6)):
        for j, b in enumerate((-0.8, 0.8)):
            z = 3.4 + ((i + j) % 2) * 0.8
            k.box(a - 0.55, a + 0.55, b - 0.6, b + 0.6, z, z + 1.4, "tr_sugar")
    mound(k, -3.2, 3.2, 1.6, 2.8, 1.4, "tr_sugar", peaks=2)


def toy_floss_load(k):
    for a in (-2.4, -0.8, 0.8, 2.4):
        k.blob(a, 0, 5.2, 0.95, 1.5, 2.2, "tr_floss", subdiv=2)
        k.rod((a, 0, 3.0), (a + 0.3, 0.3, 4.0), 0.07, "stick", n=4)


def toy_toffee_load(k):
    for i, a in enumerate((-2.6, -1.3, 0, 1.3, 2.6)):
        for j, b in enumerate((-0.75, 0.75)):
            z = 3.4 + ((i + j) % 2) * 0.7
            k.box(a - 0.55, a + 0.55, b - 0.6, b + 0.6, z, z + 1.3, "tr_toffee")
            k.box(a - 0.6, a + 0.6, b - 0.2, b + 0.2, z + 0.3, z + 1.0, "toy_yellow")


def toy_bubble_van(full):
    def build(k):
        toy_wagon_base(k, "cc")
        # A glass box of bubbles: frame, clear-blue panes; full shows the bubbles crowding up out of the top.
        k.box(-HALF + 0.1, HALF - 0.1, -1.85, 1.85, 2.6, 6.6, "tr_bubble")
        for a in (-HALF + 0.1, 0, HALF - 0.1):
            for s in (-1, 1):
                k.box(a - 0.12, a + 0.12, s * 1.85 - 0.08, s * 1.85 + 0.08, 2.6, 6.6, "toy_pink")
        k.box(-HALF, HALF, -1.95, 1.95, 6.6, 6.9, "toy_pink")
        if full:
            for a, b, z, r in ((-2.4, -0.6, 7.6, 0.8), (-1.0, 0.7, 8.0, 1.0), (0.6, -0.4, 7.7, 0.9), (2.2, 0.5, 7.9, 0.85),
                               (-0.3, 0.1, 9.0, 0.6), (1.4, -0.2, 9.1, 0.5)):
                k.blob(a, b, z, r, r, r * K, "tr_bubble", subdiv=2)
    return build


def cola_full(k, z):
    k.blob(0, 0, z + 0.4, 0.75, 0.75, 0.9, "tr_sugar", subdiv=2)  # froth over the open lid


def toy_battery_load(k):
    for a in (-2.4, -0.8, 0.8, 2.4):
        for b in (-0.85, 0.85):
            k.cyl(a, b, 0.65, 2.6, 5.4, "toy_red" if (a > 0) == (b > 0) else "toy_blue", n=12)
            k.cyl(a, b, 0.66, 4.6, 5.4, "toy_yellow", n=12)
            k.cyl(a, b, 0.22, 5.4, 5.8, "toy_white", n=8)


def toy_fizzy_load(k):
    for a in (-2.4, -0.8, 0.8, 2.4):
        for b in (-0.85, 0.85):
            m = "toy_green" if (a + b) % 1.6 > 0.4 else "toy_orange"
            k.cyl(a, b, 0.5, 4.0, 6.2, m, n=10)
            k.cyl(a, b, 0.5, 6.2, 7.2, m, n=10, r_top=0.2)
            k.cyl(a, b, 0.24, 7.2, 7.6, "toy_red", n=8)


def toy_plastic_load(k):
    mound(k, -3.2, 3.2, 1.6, 3.6, 1.8, "tr_plastic", peaks=3)
    for a, b, m in ((-2.2, 0.4, "toy_pink"), (-0.4, -0.5, "toy_yellow"), (1.4, 0.5, "toy_purple"), (2.6, -0.4, "toy_red")):
        k.blob(a, b, 5.6, 0.45, 0.45, 1.0, m)


def toy_flat(load):
    def build(k):
        toy_wagon_base(k, "cc")
        for a in (-HALF + 0.2, HALF - 0.2):
            k.box(a - 0.2, a + 0.2, -1.8, 1.8, 2.6, 4.0, "toy_yellow")
        if load:
            load(k)
    return build


# --- registry ----------------------------------------------------------------------------------

ENGINES = [  # name, builder, first sprite, directions
    ("jubilee", jubilee, 0xB59, 8), ("a4", a4, 0xB61, 8), ("tank", tank_engine, 0xB69, 8), ("d25", d25, 0xB71, 4),
    ("d37", d37, 0xB75, 4), ("e30", e30, 0xB79, 4), ("hst", hst, 0xB7D, 8), ("dmu", dmu, 0xB85, 8),
    ("dash", dash, 0xB8D, 8), ("asiastar", asiastar, 0xB95, 8), ("tim", tim, 0xB9D, 8), ("x2001", x2001, 0xBA5, 4),
    ("z1", z1, 0xBA9, 8), ("lev3", lev3, 0xBB1, 8), ("lev4", lev4, 0xBB9, 8), ("lev1", lev1, 0xBC1, 4),
    ("lev2", lev2, 0xBC5, 4), ("cs2400", cs2400, 0xBC9, 8), ("centennial", centennial, 0xBD1, 8),
    ("cs4000", cs4000, 0xBD9, 8), ("wills", wills, 0xBE1, 8), ("kelling", kelling, 0xBE9, 4),
    ("turbo", turbo, 0xBED, 8), ("mjs1000", mjs1000, 0xBF5, 4), ("mjs250", mjs250, 0xBF9, 8),
]


def wagon_set(prefix, first, fut):
    """The 24 rail wagon sets (0xAAD-0xB0C) or the 19 monorail/maglev ones (0xB0D-0xB58)."""
    empty = [("pass", passenger(fut)), ("coal", coal(False, fut)), ("mail", mail_van(fut)), ("oil", oil(fut)),
             ("livestock", van("tr_brown", slats=True, kind="livestock", fut=fut)),
             ("goods", van("cc", "tr_white", kind="goods", fut=fut)),
             ("food", van("tr_white", "cc", kind="food", fut=fut)), ("grain", grain(False, fut)),
             ("wood", wood(False, fut)), ("flat", flat(None, fut)), ("hopper", ore_hopper(False, fut=fut)),
             ("armoured", van("tr_grey", "cc", kind="armoured", fut=fut))]
    full = [("coal_full", coal(True, fut)), ("grain_full", grain(True, fut)), ("wood_full", wood(True, fut)),
            ("steel_full", flat("steel", fut)), ("iron_full", ore_hopper(True, "tr_ore", fut)),
            ("paper_full", flat("paper", fut)), ("copper_full", ore_hopper(True, "tr_copper", fut))]
    tropic = [("water", water(fut)), ("fruit", fruit(False, fut)), ("fruit_full", fruit(True, fut)),
              ("rubber", rubber(False, fut)), ("rubber_full", rubber(True, fut))]
    out = []
    for name, build in empty + full + (tropic if not fut else []):
        out.append((prefix + name, build, first, 4))
        first += 4
    return out


WAGONS = wagon_set("w_", 0xAAD, False) + wagon_set("m_", 0xB0D, True)

TOYLAND = [  # replace in toyland only
    ("toy_powernaut", toy_powernaut, 0xB59, 8), ("toy_mightymover", toy_mightymover, 0xB61, 8),
    ("toy_ploddy", toy_ploddy, 0xB69, 8), ("toy_pdiesel", toy_pdiesel, 0xBC9, 8), ("toy_ndiesel", toy_ndiesel, 0xBD9, 8),
    ("toy_z99", toy_z99, 0xBA9, 8), ("toy_rocketeer", toy_rocketeer, 0xBC1, 4),
    ("t_pass", toy_passenger, 0xAAD, 4), ("t_mail", toy_mail, 0xAB5, 4),
    ("t_sugar", lambda k: toy_open(k, "toy_pink"), 0xAB9, 4),
    ("t_sugar_full", lambda k: toy_open(k, "toy_pink", toy_sugar_load), 0xABD, 4),
    ("t_floss", lambda k: toy_open(k, "toy_cyan"), 0xAC1, 4),
    ("t_floss_full", lambda k: toy_open(k, "toy_cyan", toy_floss_load), 0xAC5, 4),
    ("t_toffee", lambda k: toy_open(k, "toy_orange"), 0xAC9, 4),
    ("t_toffee_full", lambda k: toy_open(k, "toy_orange", toy_toffee_load), 0xACD, 4),
    ("t_bubble", toy_bubble_van(False), 0xAD1, 4), ("t_bubble_full", toy_bubble_van(True), 0xAD5, 4),
    ("t_cola", lambda k: toy_tankcar(k, "tr_cola"), 0xAD9, 4),
    ("t_cola_full", lambda k: toy_tankcar(k, "tr_cola", full=cola_full), 0xADD, 4),
    ("t_sweet", lambda k: toy_van(k, "toy_white", "toy_pink", sweets_deco), 0xAE1, 4),
    ("t_toy", lambda k: toy_van(k, "toy_yellow", "toy_green", toys_deco), 0xAE5, 4),
    ("t_battery", toy_flat(None), 0xAE9, 4), ("t_battery_full", toy_flat(toy_battery_load), 0xAED, 4),
    ("t_fizzy", toy_flat(None), 0xAF1, 4), ("t_fizzy_full", toy_flat(lambda k: (k.box(-3.4, 3.4, -1.8, 1.8, 2.6, 4.0, "toy_red"), toy_fizzy_load(k))), 0xAF5, 4),
    ("t_plastic", lambda k: toy_open(k, "toy_purple"), 0xAF9, 4),
    ("t_plastic_full", lambda k: toy_open(k, "toy_purple", toy_plastic_load), 0xAFD, 4),
]

# Effect attachment points in the model frame (a along the vehicle from its centre, b across, z up);
# see the module docstring. Rear heads of multihead engines are the same model turned round.
EFFECTS = {
    "steam chimney top": {"jubilee": (3.25, 0, 9.0), "wills": (3.25, 0, 9.2), "tank": (3.0, 0, 8.6),
                          "a4": (2.6, 0, 7.2), "toy_ploddy": (2.6, 0, 10.6), "toy_powernaut": (2.6, 0, 11.0),
                          "toy_mightymover": (2.6, 0, 11.6)},
    "diesel exhaust": {"mjs250": (-1.95, 0, 6.4), "cs2400": (0.05, 0, 6.6), "centennial": (0.85, 0, 6.9),
                       "cs4000": (0.6, 0, 7.0), "kelling": (-1.45, 0, 6.4), "dmu": (0, 0, 7.6), "turbo": (-1.0, 0, 7.6),
                       "d25": (0, 0, 7.3), "d37": (0, 0, 7.3), "mjs1000": (0, 0, 7.5), "hst": (-2.6, 0, 7.4),
                       "toy_pdiesel": (-0.3, 0, 7.3), "toy_ndiesel": (-0.3, 0, 7.3)},
    "pantograph head (contact wire z 13)": {"e30": (1.8, 0, 13.0), "tim": (-2.2, 0, 13.0), "asiastar": (-2.2, 0, 13.0)},
}

TRAINS = {name: ("train" if dirs == 8 else "train4", build) for name, build, _, dirs in ENGINES + WAGONS + TOYLAND}
