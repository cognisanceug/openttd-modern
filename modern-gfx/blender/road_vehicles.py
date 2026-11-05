"""Road vehicle models for render_vehicles.py: the 72 original sprite sets and toyland's 20.

Same conventions as the ships: local +a is the front, b across, z height units up from the
vehicle's z_pos (the road surface). One x/y unit is K = 2.449 z units in true proportions, a
storey (~3 m) is ~7 z units, so a lorry is ~8 z units high and 2.6 units wide in a lane of
~3.7 units (ROAD_HALF in make_infra_textures.py). Every model is 7.8 units long, centred on 0
(VEHICLE_LENGTH 8); render_vehicles.py moves it to the lane (type "road").

Bodies are lofts through rounded-rectangle sections (shell), so cabs and buses get rounded or
raked fronts and roofs; window bands follow the same sections (band). Three generations share
a cab per era: 1 a 1930s bonneted cab with round fenders, 2 a boxy 1970s cab-over, 3 a modern
raked cab with roof deflector and side skirts. The cab carries the company colour.

Sprite sets (_roadveh_images in roadveh_cmd.cpp, base + Direction; loaded = base + full adder,
used when the vehicle is at least half full):
  gen 1 (1929-1935)  gen 2 (1964-1986)  gen 3 (2004-2022)
  bus1      0xCD4    bus2      0xC14    bus3      0xD94    MPS Regal / Hereford Leopard, Foster / Foster MkII
  coal1_e/l 0xCDC/D34 coal2_e/l 0xC1C/C74 coal3_e/l 0xD9C/DF4  Balogh, Uhl, DW coal trucks
  mail1     0xCE4    mail2     0xC24    mail3     0xDA4    MPS, Reynard, Perry mail trucks
  oil1      0xCEC    oil2      0xC2C    oil3      0xDAC    Witcombe, Foster, Perry oil tankers
  live1     0xCF4    live2     0xC34    live3     0xDB4    Talbott, Uhl, Foster livestock vans
  goods1    0xCFC    goods2    0xC3C    goods3    0xDBC    Balogh, Craighead, Goss goods trucks
  food1     0xD04    food2     0xC44    food3     0xDC4    Foster, Perry, Chippy food vans
  grain1_e/l 0xD0C/D3C grain2_e/l 0xC4C/C7C grain3_e/l 0xDCC/DFC  Hereford, Thomas, Goss grain
  wood1_e/l 0xD14/D44 wood2_e/l 0xC54/C84 wood3_e/l 0xDD4/E04  Witcombe, Foster, Moreland wood
  flat1_e   0xD1C    flat2_e   0xC5C    flat3_e   0xDDC    empty steel (temperate) and paper (arctic)
  steel1_l  0xD4C    steel2_l  0xC8C    steel3_l  0xE0C    Balogh, Uhl, Kelling steel trucks
  paper1_l  0xD5C    paper2_l  0xC9C    paper3_l  0xE1C    Uhl, Balogh, MPS paper trucks
  ore1_e    0xD24    ore2_e    0xC64    ore3_e    0xDE4    empty iron ore (temperate), copper ore (tropic)
  iron1_l   0xD54    iron2_l   0xC94    iron3_l   0xE14    MPS, Uhl, Chippy iron ore trucks
  copper1_l 0xD64    copper2_l 0xCA4    copper3_l 0xE24    MPS, Uhl, Goss copper ore trucks
  armour1   0xD2C    armour2   0xC6C    armour3   0xDEC    Balogh, Uhl, Foster armoured trucks
  water1    0xD6C    water2    0xCAC    water3    0xE2C    Uhl, Balogh, MPS water tankers
  fruit1_e/l 0xD74/D84 fruit2_e/l 0xCB4/CC4 fruit3_e/l 0xE34/E44  Balogh, Uhl, Kelling fruit
  rubber1_e/l 0xD7C/D8C rubber2_e/l 0xCBC/CCC rubber3_e/l 0xE3C/E4C  Balogh, Uhl, RMT rubber
Toyland (its base graphics replace 0xC14-0xCB3; MkI-III / MightyMover-Wizzowow share a set):
  toybus 0xC14, toysugar_e/l 0xC1C/C24, toycola_e/l 0xC2C/C34, toyfloss_e/l 0xC3C/C44,
  toytoffee_e/l 0xC4C/C54, toyvan 0xC5C, toymail 0xC64, toysweets 0xC6C, toybattery_e/l 0xC74/C7C,
  toyfizzy_e/l 0xC84/C8C, toyplastic_e/l 0xC94/C9C, toybubble_e/l 0xCA4/CAC
"""

import math
import random
from functools import partial

import build_kit as bk
import style as st

W, O, F = st.WALL, st.OBJECT, st.FLAT
K = 2.449  # z units per x/y unit
bk.PALETTE.update({
    "tyre": ((44, 46, 50), W), "hub": ((178, 182, 188), W), "chrome": ((210, 214, 218), W),
    "headlamp": ((252, 246, 222), F), "tail": ((206, 62, 52), W), "grille": ((58, 62, 68), W),
    "bumper": ((72, 76, 82), W), "chassis": ((54, 56, 62), W), "bed_dark": ((70, 66, 62), W),
    "plank_w": ((178, 132, 88), W), "plank_dark": ((128, 94, 66), W), "alu": ((212, 216, 220), W),
    "alu_dark": ((164, 170, 176), W), "body_white": ((240, 240, 236), W), "tarp": ((92, 118, 96), W),
    "grain": ((228, 190, 88), O), "coil": ((172, 178, 186), W), "coil_dark": ((96, 102, 110), W),
    "paper_roll": ((244, 242, 236), W), "drum": ((222, 218, 204), W), "drum_band": ((120, 124, 130), W),
    "crate": ((194, 158, 106), W), "cow": ((246, 244, 238), O), "cow_dark": ((72, 62, 56), O),
    "tank_red": ((158, 70, 60), W), "tank_water": ((128, 176, 210), W), "armour": ((132, 140, 144), W),
    "fridge": ((176, 182, 188), W), "mail_yellow": ((246, 204, 60), W), "dest": ((44, 46, 52), W),
    "stall_dark": ((60, 54, 48), W),
    "toy_brown": ((160, 104, 64), W), "battery": ((52, 56, 66), W), "bubble_hi": ((246, 252, 255), F),
    "lolly": ((250, 246, 240), W),
})

HB = 1.3                 # half width of cabs and buses
BH = 1.25                # half width of cargo bodies
FRONT, BACK = 3.9, -3.9  # model length 7.8, centred


# --- geometry helpers --------------------------------------------------------------------------

def rrect(a0, a1, hb, rf=0.0, rb=0.0, n=3):
    """Rounded-rectangle outline: the +b side from back to front, then mirrored (loft order)."""
    lim = min(hb * 0.95, (a1 - a0) * 0.45)
    rf, rb = min(max(rf, 0.02), lim), min(max(rb, 0.02), lim)
    side = []
    for i in range(n + 1):
        t = math.pi / 2 * i / n
        side.append((a0 + rb - rb * math.cos(t), hb - rb + rb * math.sin(t)))
    for i in range(n + 1):
        t = math.pi / 2 * i / n
        side.append((a1 - rf + rf * math.sin(t), hb - rf + rf * math.cos(t)))
    return side + [(a, -b) for a, b in reversed(side)]


def loft(k, rings, mat):
    """Closed solid through mirror-symmetric rings [[(a, b, z)]] (as render_vehicles.loft)."""
    n, m = len(rings[0]), len(rings)
    v = [p for r in rings for p in r]
    f = []
    for base in (0, (m - 1) * n):
        f += [(base + j, base + j + 1, base + n - 2 - j, base + n - 1 - j) for j in range(n // 2 - 1)]
    for j in range(m - 1):
        for i in range(n):
            a, b = j * n + i, j * n + (i + 1) % n
            f.append((a, b, b + n, a + n))
    k._solid(v, f, mat)


def shell(k, secs, mat, n=3):
    """Solid through sections [(z, a0, a1, hb, r_front, r_back)] from bottom to top."""
    loft(k, [[(a, b, s[0]) for a, b in rrect(*s[1:], n=n)] for s in secs], mat)


def section_at(secs, z):
    for s0, s1 in zip(secs, secs[1:]):
        if s0[0] <= z <= s1[0]:
            t = (z - s0[0]) / (s1[0] - s0[0]) if s1[0] > s0[0] else 0.0
            return tuple(p + (q - p) * t for p, q in zip(s0, s1))
    return secs[0] if z < secs[0][0] else secs[-1]


def band(k, secs, z0, z1, mat, out=0.05, n=3, a_min=None):
    """Shell around the sections between z0 and z1, grown by out: window bands and stripes.

    With a_min the band only covers the part in front of a_min (a windscreen and the front
    side windows)."""
    zs = [z0] + [s[0] for s in secs if z0 < s[0] < z1] + [z1]
    rings = []
    for z in zs:
        _, a0, a1, hb, rf, rb = section_at(secs, z)
        if a_min is not None:
            a0, rb = a_min, 0.0
        rings.append([(a, b, z) for a, b in rrect(a0 - out, a1 + out, hb + out, rf + out, rb, n)])
    loft(k, rings, mat)


def pillars(k, secs, z0, z1, places, mat, w=0.14):
    """Window pillars on both sides at the given a positions."""
    hb = section_at(secs, (z0 + z1) / 2)[3] + 0.08
    for a in places:
        for s in (-1, 1):
            k.box(a - w / 2, a + w / 2, *sorted((s * (hb - 0.1), s * hb)), z0, z1, mat)


def wheel(k, a, r=0.5, hb=HB, w=0.42, hub="hub", rim=None):
    zc = r * K
    for s in (-1, 1):
        k.rod((a, s * (hb - w), zc), (a, s * (hb + 0.03), zc), r, "tyre", n=12)
        k.rod((a, s * (hb + 0.02), zc), (a, s * (hb + 0.06), zc), r * 0.56, hub, n=10)
        if rim:
            k.rod((a, s * (hb + 0.05), zc), (a, s * (hb + 0.08), zc), r * 0.24, rim, n=8)


def arch(k, a, r, hb=HB, mat="chassis", grow=0.14):
    """Dark wheel arch on both body sides behind a wheel (upper half disc)."""
    zc, R = r * K, r + grow
    prof = [(a + R * math.cos(math.pi * i / 8), max(0.0, zc + R * K * math.sin(math.pi * i / 8))) for i in range(9)]
    for s in (-1, 1):
        k.extrude(prof, "y", *sorted((s * (hb + 0.004), s * (hb + 0.018))), mat)


def pile(k, a0, a1, hb, z0, h, mat, seed=0):
    """Low-poly heap of loose cargo filling a body from z0, h high, with a lumpy ridge."""
    rng = random.Random(seed)
    L = a1 - a0
    rings = []
    for z, ia, ib, r in ((z0, 0.0, 0.0, 0.1), (z0 + h * 0.55, L * 0.08, hb * 0.18, 0.4),
                         (z0 + h * 0.88, L * 0.2, hb * 0.55, 0.5), (z0 + h, L * 0.3, hb * 0.82, 0.3)):
        pts = rrect(a0 + ia, a1 - ia, hb - ib, r, r, n=2)
        jit = 0 if z == z0 else 0.35
        rings.append([(a, b, z + rng.uniform(-jit, jit) * h / 3) for a, b in pts])
    loft(k, rings, mat)
    for i in range(3):  # a few lumps on the ridge
        a = a0 + L * (0.25 + 0.25 * i) + rng.uniform(-0.3, 0.3)
        k.blob(a, rng.uniform(-0.3, 0.3), z0 + h * 0.85, 0.5, 0.42, h * 0.3, mat, subdiv=1)


# --- cabs and chassis ---------------------------------------------------------------------------

GEN = {
    1: dict(wheels=(2.75, -2.35), r=0.5, bed=2.75, cab_back=0.25),
    2: dict(wheels=(2.95, -2.3), r=0.52, bed=2.85, cab_back=2.0),
    3: dict(wheels=(2.95, -1.75, -2.95), r=0.5, bed=2.75, cab_back=1.75),
}


def chassis(k, g, a1=None):
    G = GEN[g]
    a1 = G["cab_back"] + 0.5 if a1 is None else a1
    zc = G["r"] * K
    k.box(-3.75, a1, -0.8, 0.8, zc - 0.3, G["bed"] - 0.35, "chassis")
    for a in G["wheels"]:
        wheel(k, a, G["r"], hb=BH if a < G["cab_back"] else HB, rim="chassis" if g == 1 else None)
    # Mudguards over the rear wheels, under the body edge.
    for a in G["wheels"][1:]:
        for s in (-1, 1):
            k.box(a - 0.62, a + 0.62, *sorted((s * 0.85, s * (BH + 0.02))), G["bed"] - 0.55, G["bed"] - 0.35, "chassis")


def cab1(k):
    """1930s bonneted cab: rounded hood with a chrome grille, round fenders and lamps, round roof."""
    r, zc = 0.5, 0.5 * K
    chassis(k, 1)
    shell(k, [(1.6, 2.0, 3.85, 0.74, 0.3, 0.05), (4.0, 2.0, 3.85, 0.74, 0.3, 0.05),
              (4.75, 2.0, 3.72, 0.5, 0.32, 0.05)], "cc")
    k.box(3.78, 3.93, -0.52, 0.52, 1.7, 4.3, "chrome")
    k.box(3.84, 3.96, -0.38, 0.38, 1.9, 4.1, "grille")
    for s in (-1, 1):
        k.blob(2.78, s * 1.0, zc + 0.85, 0.85, 0.36, 0.95, "cc")  # fender
        k.box(0.3, 2.1, *sorted((s * 0.9, s * 1.32)), 1.45, 1.75, "chassis")  # running board
        k.blob(3.6, s * 0.95, 3.75, 0.24, 0.22, 0.55, "chrome")  # headlamp
        k.blob(3.78, s * 0.95, 3.75, 0.08, 0.17, 0.42, "headlamp")
    k.box(3.88, 4.05, -1.05, 1.05, 1.3, 1.8, "chrome")  # bumper
    secs = [(1.6, 0.25, 2.1, 1.2, 0.12, 0.08), (6.1, 0.25, 2.1, 1.2, 0.12, 0.08), (7.1, 0.42, 1.95, 0.98, 0.4, 0.3)]
    shell(k, secs, "cc")
    band(k, secs, 4.55, 6.0, "glass", out=0.04)
    pillars(k, secs, 4.55, 6.0, (1.25,), "cc")


def cab2(k):
    """1970s cab-over: flat front, big windscreen, black grille, square lamps, white roof cap."""
    chassis(k, 2)
    secs = [(1.5, 2.05, 3.92, HB, 0.14, 0.05), (7.25, 2.05, 3.92, HB, 0.14, 0.05),
            (7.8, 2.1, 3.84, 1.23, 0.18, 0.06)]
    shell(k, secs, "cc")
    band(k, secs, 7.45, 7.83, "body_white", out=0.015)
    band(k, secs, 4.55, 6.85, "glass", out=0.04)
    pillars(k, secs, 4.55, 6.85, (2.95,), "cc")
    k.box(3.9, 4.0, -0.82, 0.82, 2.55, 3.75, "grille")
    for s in (-1, 1):
        k.box(3.9, 4.0, *sorted((s * 0.92, s * 1.2)), 2.6, 3.35, "headlamp")
        k.box(3.62, 3.76, *sorted((s * 1.3, s * 1.56)), 5.0, 6.5, "dark")  # mirror
        k.box(0.4, 1.7, *sorted((s * 0.8, s * 1.18)), 1.25, 2.25, "chrome")  # fuel tank
    k.box(3.85, 4.06, -1.34, 1.34, 1.35, 2.3, "bumper")
    arch(k, GEN[2]["wheels"][0], GEN[2]["r"])


def cab3(k):
    """Modern cab: raked windscreen, light strips, roof deflector, side skirts."""
    chassis(k, 3)
    secs = [(1.2, 1.75, 3.95, HB, 0.35, 0.05), (3.9, 1.75, 3.98, HB, 0.42, 0.05),
            (6.9, 1.75, 3.62, 1.28, 0.55, 0.05), (8.2, 1.75, 3.0, 1.17, 0.62, 0.05),
            (8.75, 1.85, 2.2, 1.0, 0.5, 0.1)]
    shell(k, secs, "cc")
    band(k, secs, 4.6, 6.9, "glass", out=0.04)
    k.box(3.86, 4.02, -0.62, 0.62, 2.0, 3.45, "grille")
    for s in (-1, 1):
        k.box(3.84, 4.02, *sorted((s * 0.72, s * 1.16)), 3.1, 3.5, "headlamp")
        k.box(3.42, 3.54, *sorted((s * 1.28, s * 1.5)), 5.6, 6.6, "dark")  # camera mirror
    k.box(3.82, 4.04, -1.3, 1.3, 1.15, 2.0, "bumper")
    k.box(-1.1, 2.3, -1.24, 1.24, 1.1, 2.4, "alu_dark")  # side skirts
    arch(k, GEN[3]["wheels"][0], GEN[3]["r"])


CABS = {1: cab1, 2: cab2, 3: cab3}

# Body materials per generation: wall, rail/rib, accent.
BODY = {1: ("plank_w", "plank_dark"), 2: ("alu", "alu_dark"), 3: ("body_white", "alu_dark")}


def span(g):
    return BACK + 0.05, GEN[g]["cab_back"] - 0.14


def tail_lights(k, a0, z):
    for s in (-1, 1):
        k.box(a0 - 0.04, a0 + 0.02, *sorted((s * 0.85, s * 1.15)), z - 0.4, z, "tail")


def platform(k, g, mat=None):
    a0, a1 = span(g)
    z = GEN[g]["bed"]
    k.box(a0, a1, -BH, BH, z - 0.4, z, mat or BODY[g][1])
    tail_lights(k, a0, z - 0.05)
    return a0, a1, z


def ribs(k, a0, a1, z0, z1, mat, pitch=0.9, hb=BH):
    for a in bk.frange(a0 + 0.35, a1 - 0.3, pitch):
        for s in (-1, 1):
            k.box(a - 0.06, a + 0.06, *sorted((s * hb, s * (hb + 0.07))), z0, z1, mat)


# --- cargo bodies -------------------------------------------------------------------------------

def tipper(k, g, h, load=None, seed=0, slope=False, hoops=False):
    """Open tipping body; with load a heap rising over the sides. slope: rock-dump sides falling
    towards the open-ish rear (ore); hoops: tarpaulin bows (grain)."""
    wall, rib = BODY[g]
    if g == 2:
        wall = "steel"
    a0, a1, z = platform(k, g)
    t = 0.13
    k.box(a0 + t, a1 - t, -BH + t, BH - t, z, z + 0.12, "bed_dark")
    if slope:
        prof = [(a0, z), (a1, z), (a1, z + h + 0.5), (a0 + 1.4, z + h), (a0, z + h * 0.55)]
    else:
        prof = [(a0, z), (a1, z), (a1, z + h + 0.6), (a1 - 0.3, z + h), (a0, z + h)]
    for s in (-1, 1):
        k.extrude(prof, "y", *sorted((s * (BH - t), s * BH)), wall)
        top = prof[2:]
        for (pa, pz), (qa, qz) in zip(top, top[1:]):
            k.rod((pa, s * (BH + 0.02), pz - 0.08), (qa, s * (BH + 0.02), qz - 0.08), 0.07, rib, n=4)
    k.box(a1 - t, a1, -BH, BH, z, z + h + 0.6, wall)
    k.box(a0, a0 + t, -BH, BH, z, z + (h * 0.55 if slope else h), wall)
    if g != 3:
        ribs(k, a0, a1, z, z + h * (0.55 if slope else 1.0) - 0.05, rib, pitch=1.0)
    else:
        for s in (-1, 1):  # company-colour stripe on the smooth body
            k.box(a0 + 0.1, a1 - 0.1, *sorted((s * BH, s * (BH + 0.03))), z + h * 0.35, z + h * 0.55, "cc")
    if hoops:
        for a in bk.frange(a0 + 0.5, a1 - 0.4, 1.25):
            pts = [(a, BH * math.cos(math.pi * i / 6), z + h + 0.15 + 1.4 * math.sin(math.pi * i / 6)) for i in range(7)]
            for p, q in zip(pts, pts[1:]):
                k.rod(p, q, 0.05, "chassis", n=3)
    if load:
        top_z = z + (h * 0.55 if slope else h)
        pile(k, a0 + t, a1 - t - (0.2 if not slope else 0.0), BH - t, z + 0.4, top_z - z + 0.9, load, seed)


def stakes(k, g, logs=False):
    """Stake body with a headboard; loaded with stacked logs."""
    wall, rib = BODY[g]
    a0, a1, z = platform(k, g, "plank_w" if g == 1 else "chassis")
    k.box(a1 - 0.15, a1, -BH, BH, z, z + 3.6, rib)
    for a in bk.frange(a0 + 0.12, a1 - 0.5, 1.2):
        for s in (-1, 1):
            k.box(a - 0.08, a + 0.08, *sorted((s * (BH - 0.14), s * BH)), z, z + 3.1, "chassis" if g > 1 else "plank_dark")
    if g == 3:
        for s in (-1, 1):
            k.box(a0, a1, *sorted((s * BH, s * (BH + 0.03))), z - 0.4, z, "cc")
    if logs:
        rng = random.Random(g)
        r = 0.36
        dz = r * math.sqrt(3) * K
        rows = [((-0.82, 0.0, 0.82), 0), ((-0.41, 0.41), 1), ((0.0,), 2)]
        for bs, lvl in rows:
            for b in bs:
                zc = z + r * K + lvl * dz
                a_end = a0 - rng.uniform(0.0, 0.25)
                a_head = a1 - 0.2 - rng.uniform(0.0, 0.3)
                k.rod((a_end + 0.06, b, zc), (a_head, b, zc), r, "log", n=8)
                k.rod((a_end, b, zc), (a_end + 0.07, b, zc), r * 0.9, "log_end", n=8)


def flatbed(k, g, load=None):
    """Flat body with headboard and low rails; loads: steel coils, paper rolls."""
    wall, rib = BODY[g]
    a0, a1, z = platform(k, g, "plank_w" if g == 1 else "chassis")
    k.box(a1 - 0.18, a1, -BH, BH, z, z + 3.0, rib)
    for s in (-1, 1):
        k.box(a0, a1, *sorted((s * (BH - 0.1), s * (BH + 0.02))), z, z + 0.45, wall if g != 3 else "cc")
    L = a1 - 0.3 - a0
    if load == "steel":
        n = max(2, int(L // 1.75))
        R = 0.78
        for i in range(n):
            a = a0 + 0.2 + L * (i + 0.5) / n
            zc = z + 0.2 + R * K
            k.box(a - 0.7, a + 0.7, -0.75, 0.75, z, z + 0.6, "chassis")  # cradle
            k.rod((a - 0.6, 0, zc), (a + 0.6, 0, zc), R, "coil", n=14)
            k.rod((a - 0.63, 0, zc), (a + 0.63, 0, zc), R * 0.36, "coil_dark", n=10)
    elif load == "paper":
        n = max(3, int(L // 1.15))
        for i in range(n):
            a = a0 + 0.15 + L * (i + 0.5) / n
            for b in (-0.62, 0.62):
                k.cyl(a, b, 0.56, z, z + 3.3, "paper_roll", n=12)
                k.cyl(a, b, 0.2, z + 3.3, z + 3.34, "alu_dark", n=8)


def box_body(k, g, top, wall, stripe=None, stripe_z=None, r_top=0.12, ribbed=False, base=None):
    """Closed box body from the bed to top; optional company-colour stripe and ribs."""
    a0, a1 = span(g)
    z = GEN[g]["bed"]
    secs = [(z - 0.4, a0, a1, BH, 0.06, 0.06), (top - r_top * K, a0, a1, BH, 0.06, 0.06),
            (top, a0 + r_top, a1 - r_top, BH - r_top, 0.1, 0.1)]
    shell(k, secs, wall)
    if base:
        band(k, secs, z - 0.4, z + 0.15, base, out=0.02)
    if stripe:
        z0, z1 = stripe_z
        band(k, secs, z0, z1, stripe, out=0.02)
    if ribbed:
        ribs(k, a0, a1, z - 0.3, top - 0.25, "alu_dark", pitch=0.75)
    k.box(a0 - 0.03, a0 + 0.02, -0.03, 0.03, z, top - 0.3, "grille")  # rear door split
    tail_lights(k, a0 - 0.02, z - 0.05)
    return a0, a1, z, secs


def van(k, g, kind):
    """Box vans: goods, mail, food (refrigerated), armoured."""
    z = GEN[g]["bed"]
    if kind == "goods":
        if g == 1:
            box_body(k, g, z + 4.9, "cream", "cc", (z + 1.0, z + 1.7), r_top=0.4, base="plank_dark")
        elif g == 2:
            box_body(k, g, z + 5.1, "alu", "cc", (z + 3.6, z + 4.3), ribbed=True)
        else:
            a0, a1, _, _ = box_body(k, g, z + 5.5, "body_white", "cc", (z + 0.2, z + 1.1))
            for s in (-1, 1):  # curtain-side straps
                for a in bk.frange(a0 + 0.5, a1 - 0.3, 0.7):
                    k.box(a - 0.04, a + 0.04, *sorted((s * BH, s * (BH + 0.04))), z + 1.2, z + 5.2, "alu_dark")
    elif kind == "mail":
        if g == 1:
            box_body(k, g, z + 4.6, "cc", "mail_yellow", (z + 2.2, z + 2.6), r_top=0.5)
        elif g == 2:
            box_body(k, g, z + 5.0, "cc", "mail_yellow", (z + 2.6, z + 3.1), ribbed=True)
            band(k, [(z + 4.6, *span(g), BH, 0.06, 0.06), (z + 5.03, *span(g), BH, 0.06, 0.06)], z + 4.6, z + 5.03,
                 "body_white", out=0.025)
        else:
            box_body(k, g, z + 5.3, "body_white", "cc", (z + 0.6, z + 2.4))
            a0, a1 = span(g)
            for s in (-1, 1):
                k.box(a0 + 0.1, a1 - 0.1, *sorted((s * BH, s * (BH + 0.05))), z + 2.5, z + 2.9, "mail_yellow")
    elif kind == "food":
        top = z + (4.7 if g == 1 else 5.2 if g == 2 else 5.5)
        a0, a1, _, _ = box_body(k, g, top, "body_white", "cc", (top - 1.2, top - 0.6), r_top=0.35 if g == 1 else 0.12)
        u0 = a1 - (1.0 if g < 3 else 1.3)
        k.box(u0, a1 - 0.15, -0.8, 0.8, top - 0.05, top + 0.9, "fridge")  # refrigeration unit
        k.box(u0 + 0.15, a1 - 0.3, -0.82, 0.82, top + 0.2, top + 0.7, "grille")
    elif kind == "armour":
        top = z + (4.2 if g < 3 else 4.6)
        a0, a1, _, secs = box_body(k, g, top, "armour", "cc", (z + 1.4, z + 1.9), r_top=0.4 if g == 1 else 0.15)
        for s in (-1, 1):
            for a in (a1 - 0.7, a0 + 1.2):  # slit windows
                k.box(a - 0.35, a + 0.35, *sorted((s * BH, s * (BH + 0.04))), top - 1.6, top - 1.1, "glass")
        k.box(-1.2, -0.2, -0.45, 0.45, top - 0.05, top + 0.35, "armour")  # roof hatch
        if g == 1:
            for a in bk.frange(a0 + 0.3, a1 - 0.2, 0.6):  # rivet lines
                for s in (-1, 1):
                    k.box(a - 0.04, a + 0.04, *sorted((s * BH, s * (BH + 0.04))), top - 0.75, top - 0.65, "dark")


def tank(k, g, kind):
    """Tank body: horizontal tank with company-colour rings, catwalk and domes."""
    a0, a1 = span(g)
    z = GEN[g]["bed"]
    R = (0.98, 1.08, 1.12)[g - 1]
    mat = {("oil", 1): "tank_red", ("oil", 2): "tank", ("oil", 3): "chrome",
           ("water", 1): "tank_water", ("water", 2): "tank_water", ("water", 3): "chrome"}[(kind, g)]
    zc = z - 0.15 + R * K
    for a in (a0 + 0.6, a1 - 0.6):
        k.box(a - 0.25, a + 0.25, -0.9, 0.9, z - 0.4, zc - R * K * 0.5, "chassis")  # cradles
    k.box(a0, a1, -0.75, 0.75, z - 0.4, z, "chassis")
    tail_lights(k, a0, z - 0.05)
    k.rod((a0 + 0.25, 0, zc), (a1 - 0.25, 0, zc), R, mat, n=16)
    for a, d in ((a0 + 0.25, -1), (a1 - 0.25, 1)):  # rounded ends
        k.rod((a, 0, zc), (a + d * 0.22, 0, zc), R * 0.86, mat, n=16)
    rings = (a0 + 0.5, a1 - 0.5) if g == 1 else (a0 + 0.45, (a0 + a1) / 2, a1 - 0.45)
    for a in rings:
        k.rod((a - 0.12, 0, zc), (a + 0.12, 0, zc), R + 0.03, "cc", n=16)
    if kind == "water" and g == 3:
        k.rod((a0 + 0.9, 0, zc), ((a0 + a1) / 2 - 0.3, 0, zc), R + 0.02, "tank_water", n=16)
    zt = zc + R * K
    k.box(a0 + 0.5, a1 - 0.5, -0.28, 0.28, zt - 0.2, zt + 0.12, "steel_dark")  # catwalk
    for a in bk.frange(a0 + 1.0, a1 - 0.6, 1.6):
        k.cyl(a, 0, 0.32, zt - 0.2, zt + 0.55, "chrome" if g > 1 else "steel", n=10)
    if g > 1:
        k.rod((a0 + 0.3, 0.0, z + 0.4), (a0 + 0.3, 0.0, zc), 0.12, "steel_dark", n=6)  # outlet pipe


def livestock(k, g):
    """Slatted body with a dark stall; cattle show between the slats."""
    wall, rib = BODY[g]
    if g == 3:
        wall = "body_white"
    a0, a1, z = platform(k, g)
    top = z + (4.3 if g == 1 else 5.0)
    k.box(a0 + 0.1, a1 - 0.1, -BH + 0.12, BH - 0.12, z, top - 0.2, "stall_dark")
    rng = random.Random(g)
    for a in bk.frange(a0 + 0.8, a1 - 0.6, 1.4):  # cattle backs and heads
        for s in (-1, 1):
            b = s * 0.62
            c = "cow" if rng.random() < 0.6 else "cow_dark"
            k.blob(a, b, top - 1.9, 0.7, 0.62, 1.1, c, subdiv=1)
    pitch = 0.82
    for zz in bk.frange(z + 0.1, top - 0.35, pitch):
        for s in (-1, 1):
            k.box(a0, a1, *sorted((s * (BH - 0.1), s * BH)), zz, zz + pitch * 0.55, wall)
    for a in bk.frange(a0, a1 + 0.01, (a1 - a0) / 4):
        for s in (-1, 1):
            k.box(a - 0.08, a + 0.08, *sorted((s * (BH - 0.1), s * (BH + 0.05))), z, top, rib)
    k.box(a0, a0 + 0.12, -BH, BH, z, top, wall)
    k.box(a1 - 0.12, a1, -BH, BH, z, top, wall)
    if g > 1:
        k.box(a0 - 0.02, a1 + 0.02, -BH - 0.02, BH + 0.02, top - 0.2, top + 0.1, rib if g == 2 else "cc")
    else:
        for s in (-1, 1):
            k.box(a0, a1, *sorted((s * (BH - 0.1), s * (BH + 0.03))), top - 0.2, top, "cc")


def open_body(k, g, h, slatted=False):
    """Low open body (fruit, rubber); returns the inner box (a0, a1, hb, z)."""
    wall, rib = BODY[g]
    a0, a1, z = platform(k, g)
    t = 0.12
    k.box(a0 + t, a1 - t, -BH + t, BH - t, z, z + 0.1, "bed_dark")
    for s in (-1, 1):
        if slatted:
            for zz in (z, z + h * 0.5):
                k.box(a0, a1, *sorted((s * (BH - t), s * BH)), zz, zz + h * 0.36, "crate" if g == 1 else wall)
        else:
            k.box(a0, a1, *sorted((s * (BH - t), s * BH)), z, z + h, wall)
    k.box(a0, a0 + t, -BH, BH, z, z + h, wall)
    k.box(a1 - t, a1, -BH, BH, z, z + h + 0.8, rib)
    ribs(k, a0, a1, z, z + h, rib if g != 3 else "cc", pitch=1.1)
    return a0 + t, a1 - t, BH - t, z


def fruit(k, g, loaded):
    a0, a1, hb, z = open_body(k, g, 2.0, slatted=True)
    if not loaded:
        return
    n = max(3, int((a1 - a0) // 0.95))
    rng = random.Random(g)
    w = (a1 - a0) / n
    for i in range(n):
        for j, b in enumerate((-hb / 2, hb / 2)):
            a = a0 + w * (i + 0.5)
            for lvl in range(2 if (i + j) % 3 else 1):
                z0 = z + 0.1 + lvl * 1.75
                k.box(a - w / 2 + 0.05, a + w / 2 - 0.05, b - hb / 2 + 0.05, b + hb / 2 - 0.05, z0, z0 + 1.55, "crate")
                for (da, db) in ((-0.2, -0.2), (0.2, 0.2), (0.2, -0.2), (-0.2, 0.2)):
                    k.blob(a + da * w, b + db * hb, z0 + 1.65, 0.24, 0.24, 0.5, "fruit" if rng.random() < 0.7 else "banana")


def rubber(k, g, loaded):
    a0, a1, hb, z = open_body(k, g, 1.3)
    if not loaded:
        return
    n = max(3, int((a1 - a0) // 1.0))
    for i in range(n):
        a = a0 + (a1 - a0) * (i + 0.5) / n
        for b in (-0.6, 0.6):
            k.cyl(a, b, 0.47, z + 0.1, z + 3.0, "drum", n=12)
            for zz in (z + 0.9, z + 2.1):
                k.cyl(a, b, 0.49, zz, zz + 0.2, "drum_band", n=12)
            k.cyl(a, b, 0.4, z + 3.0, z + 3.08, "latex", n=10)


# --- buses --------------------------------------------------------------------------------------

def bus1(k):
    """1929 bonneted bus: company-colour lower body, cream upper and rounded roof, many windows."""
    r, zc = 0.5, 0.5 * K
    for a in (3.05, -2.35):
        wheel(k, a, r, rim="chassis")
    k.box(-3.6, 3.4, -0.8, 0.8, zc - 0.2, 1.6, "chassis")
    shell(k, [(1.6, 2.5, 3.85, 0.72, 0.3, 0.05), (4.0, 2.5, 3.85, 0.72, 0.3, 0.05),
              (4.7, 2.5, 3.72, 0.5, 0.3, 0.05)], "cc")
    k.box(3.78, 3.93, -0.52, 0.52, 1.7, 4.2, "chrome")
    k.box(3.84, 3.96, -0.38, 0.38, 1.9, 4.0, "grille")
    for s in (-1, 1):
        k.blob(3.05, s * 0.98, zc + 0.85, 0.8, 0.36, 0.95, "cc")
        k.blob(3.62, s * 0.92, 3.7, 0.22, 0.2, 0.5, "chrome")
        k.blob(3.78, s * 0.92, 3.7, 0.07, 0.15, 0.4, "headlamp")
    k.box(3.88, 4.05, -1.0, 1.0, 1.3, 1.8, "chrome")
    secs = [(1.3, -3.9, 2.55, 1.25, 0.15, 0.45), (6.5, -3.9, 2.55, 1.25, 0.15, 0.45),
            (7.5, -3.6, 2.35, 0.95, 0.55, 0.75)]
    shell(k, secs, "cream")
    band(k, secs, 1.3, 4.1, "cc", out=0.02)
    band(k, secs, 4.1, 4.3, "chrome", out=0.03)
    band(k, secs, 4.6, 6.2, "glass", out=0.04)
    pillars(k, secs, 4.6, 6.2, bk.frange(-3.1, 2.0, 0.95), "cream")
    arch(k, -2.35, r, hb=1.25)
    tail_lights(k, -3.9, 2.6)


def bus2(k):
    """1970s/80s city bus: boxy, flat front with a deep windscreen, cc skirt, white upper body."""
    r = 0.52
    for a in (2.75, -2.25):
        wheel(k, a, r)
    secs = [(0.95, -3.95, 3.95, HB, 0.22, 0.18), (7.35, -3.95, 3.95, HB, 0.22, 0.18),
            (7.85, -3.86, 3.86, 1.22, 0.28, 0.24)]
    shell(k, secs, "body_white")
    band(k, secs, 0.95, 3.5, "cc", out=0.02)
    band(k, secs, 3.95, 6.6, "glass", out=0.04)
    pillars(k, secs, 3.95, 6.6, bk.frange(-3.3, 2.6, 1.25), "body_white")
    band(k, secs, 2.6, 6.85, "glass", out=0.05, a_min=3.55)
    k.box(3.9, 4.01, -0.8, 0.8, 6.95, 7.5, "dest")
    k.box(3.95, 4.03, -0.5, 0.5, 7.08, 7.36, "lamp")
    for s in (-1, 1):
        k.box(3.92, 4.02, *sorted((s * 0.85, s * 1.18)), 1.6, 2.2, "headlamp")
    k.box(3.88, 4.07, -1.32, 1.32, 0.9, 1.55, "bumper")
    k.box(-3.4, 1.2, -0.9, 0.9, 7.8, 8.25, "body_white")  # roof vent box
    for a in (2.75, -2.25):
        arch(k, a, r)
    tail_lights(k, -3.95, 2.2)


def bus3(k):
    """Modern low-floor bus: large glazing to the floor at the front, raked nose, roof pods."""
    r = 0.5
    for a in (2.7, -2.3):
        wheel(k, a, r)
    secs = [(0.7, -3.95, 3.9, HB, 0.5, 0.22), (3.0, -3.95, 3.97, HB, 0.55, 0.22),
            (7.3, -3.95, 3.82, HB, 0.5, 0.22), (8.0, -3.88, 3.62, 1.23, 0.5, 0.3)]
    shell(k, secs, "body_white")
    band(k, secs, 0.7, 2.5, "cc", out=0.02)
    band(k, secs, 3.1, 7.1, "glass", out=0.04)
    pillars(k, secs, 3.1, 7.1, bk.frange(-3.4, 2.8, 1.55), "body_white", w=0.1)
    band(k, secs, 2.2, 7.3, "glass", out=0.05, a_min=3.0)
    band(k, secs, 7.35, 7.75, "cc", out=0.02)
    k.box(3.62, 3.8, -0.75, 0.75, 7.38, 7.75, "dest")
    for s in (-1, 1):
        k.box(3.84, 3.98, *sorted((s * 0.75, s * 1.15)), 1.75, 2.05, "headlamp")
    shell(k, [(7.9, -2.8, 1.6, 0.95, 0.4, 0.4), (8.7, -2.6, 1.4, 0.85, 0.5, 0.5)], "roof_metal")
    for a in (2.7, -2.3):
        arch(k, a, r)
    tail_lights(k, -3.95, 2.2)


# --- toyland ------------------------------------------------------------------------------------

TOY_R, TOY_BED = 0.62, 2.7
TOY_CAB = 1.35  # back of the toy cab


def toy_chassis(k, cab=True):
    zc = TOY_R * K
    k.box(-3.7, 3.4, -0.85, 0.85, zc - 0.4, 2.2, "toy_white")
    for a in (2.65, -2.3):
        wheel(k, a, TOY_R, hb=HB, w=0.5, hub="toy_yellow", rim="toy_red")
    k.rod((4.0, -1.15, 1.9), (4.0, 1.15, 1.9), 0.3, "toy_white", n=8)  # round bumper
    if not cab:
        return
    secs = [(1.6, TOY_CAB, 3.95, HB, 0.85, 0.3), (5.0, TOY_CAB, 3.98, HB, 0.95, 0.3),
            (7.6, TOY_CAB + 0.1, 3.45, 1.15, 0.95, 0.5), (8.6, TOY_CAB + 0.45, 2.9, 0.8, 0.6, 0.4)]
    shell(k, secs, "cc", n=4)
    band(k, secs, 5.2, 7.2, "glass_light", out=0.04, n=4)
    for s in (-1, 1):
        k.blob(3.84, s * 0.72, 3.9, 0.22, 0.34, 0.8, "toy_white")  # big round lamps
        k.blob(3.98, s * 0.72, 3.9, 0.1, 0.2, 0.48, "toy_yellow")
    k.cyl(2.3, 0, 0.26, 8.4, 9.3, "toy_red", n=8)  # roof beacon
    arch(k, 2.65, TOY_R, mat="toy_white", grow=0.16)


def toy_bed(k, rail="toy_red", h=0.8):
    a0, a1, z = BACK + 0.05, TOY_CAB - 0.12, TOY_BED
    k.box(a0, a1, -BH, BH, z - 0.45, z, "toy_wood")
    k.box(a1 - 0.2, a1, -BH, BH, z, z + 2.4, rail)
    for s in (-1, 1):
        k.box(a0, a1, *sorted((s * (BH - 0.12), s * (BH + 0.02))), z, z + h, rail)
        for a in (a0 + 0.3, (a0 + a1) / 2, a1 - 0.5):
            k.cyl(a, s * BH, 0.16, z + h, z + h + 0.35, "toy_yellow", n=8)  # rail knobs
    tail_lights(k, a0, z - 0.05)
    return a0 + 0.12, a1 - 0.2, BH - 0.12, z


def toy_tub(k, wall, rim, h=2.4):
    """Open toy tipper tub with a rounded rim."""
    a0, a1, z = BACK + 0.05, TOY_CAB - 0.12, TOY_BED
    k.box(a0, a1, -BH, BH, z - 0.45, z, "toy_wood")
    t = 0.14
    k.box(a0 + t, a1 - t, -BH + t, BH - t, z, z + 0.1, "bed_dark")
    for s in (-1, 1):
        k.box(a0, a1, *sorted((s * (BH - t), s * BH)), z, z + h, wall)
        k.rod((a0, s * BH, z + h), (a1, s * BH, z + h), 0.14, rim, n=8)
    k.box(a0, a0 + t, -BH, BH, z, z + h, wall)
    k.box(a1 - t, a1, -BH, BH, z, z + h + 0.6, rim)
    for a in (a0 + 1.0, a1 - 1.2):  # painted dots on the sides
        for s in (-1, 1):
            k.rod((a, s * (BH - 0.02), z + h * 0.5), (a, s * (BH + 0.04), z + h * 0.5), 0.4, rim, n=10)
    tail_lights(k, a0, z - 0.05)
    return a0 + t, a1 - t, BH - t, z, h


def toytipper(k, wall, rim, load):
    toy_chassis(k)
    a0, a1, hb, z, h = toy_tub(k, wall, rim)
    if load is None:
        return
    rng = random.Random(len(wall))
    if load == "sugar":
        pile(k, a0, a1 - 0.1, hb, z + 0.3, h + 0.4, "sugar", seed=3)
        for _ in range(9):
            a, b = rng.uniform(a0 + 0.4, a1 - 0.5), rng.uniform(-hb + 0.4, hb - 0.4)
            zz = z + h + rng.uniform(-0.1, 0.9)
            k.box(a - 0.32, a + 0.32, b - 0.32, b + 0.32, zz, zz + 0.75 * K * 0.5, "sugar")
    elif load == "toffee":
        cols = ["toffee", "caramel", "toffee", "toy_brown"]
        i = 0
        for lvl, zz in enumerate((z + 0.9, z + 2.05, z + 3.2)):
            for a in bk.frange(a0 + 0.45 + lvl * 0.3, a1 - 0.4, 0.95):
                for b in (-0.55, 0.55) if lvl < 2 else (0.0,):
                    k.box(a - 0.4, a + 0.4, b - 0.42, b + 0.42, zz, zz + 1.1, cols[i % 4])
                    for d in (-1, 1):  # wrapper twists
                        k.cyl(a, b + d * 0.5, 0.18, zz + 0.45, zz + 0.65, "toy_yellow", n=6)
                    i += 1
    elif load == "floss":
        for a in bk.frange(a0 + 0.6, a1 - 0.4, 0.95):
            for b in (-0.5, 0.5):
                zz = z + h + rng.uniform(-0.3, 0.4)
                k.blob(a, b, zz, 0.75, 0.7, 1.7, "floss", subdiv=2)


def toyflat(k, rail, load):
    toy_chassis(k)
    a0, a1, hb, z = toy_bed(k, rail)
    if load is None:
        return
    L = a1 - a0
    if load == "battery":
        n = max(3, int(L // 1.0))
        for i in range(n):
            a = a0 + L * (i + 0.5) / n
            for b in (-0.55, 0.55):
                k.cyl(a, b, 0.46, z, z + 2.6, "battery", n=12)
                k.cyl(a, b, 0.47, z + 1.9, z + 2.6, "copper", n=12)
                k.cyl(a, b, 0.17, z + 2.6, z + 2.95, "chrome", n=8)
    elif load == "fizzy":
        n = max(4, int(L // 0.8))
        for i in range(n):
            a = a0 + L * (i + 0.5) / n
            for b, c in ((-0.6, "toy_red"), (0.0, "toy_green"), (0.6, "toy_red")):
                k.cyl(a, b, 0.32, z, z + 2.3, c, n=10)
                k.cyl(a, b, 0.33, z + 0.9, z + 1.4, "toy_white", n=10)
                k.cyl(a, b, 0.26, z + 2.3, z + 2.45, "can", n=10)
    elif load == "plastic":
        cols = ["toy_green", "toy_blue", "toy_purple", "toy_orange"]
        n = max(3, int(L // 1.05))
        for i in range(n):
            a = a0 + L * (i + 0.5) / n
            for j, b in enumerate((-0.58, 0.58)):
                c = cols[(i + j) % 4]
                k.cyl(a, b, 0.5, z, z + 2.8, c, n=12)
                k.cyl(a, b, 0.52, z + 0.7, z + 0.9, "toy_white", n=12)
                k.cyl(a, b, 0.52, z + 1.9, z + 2.1, "toy_white", n=12)
                k.cyl(a + 0.2, b, 0.12, z + 2.8, z + 3.1, c, n=6)
    elif load == "bubble":
        rng = random.Random(7)
        for a in bk.frange(a0 + 0.6, a1 - 0.3, 1.1):
            for b in (-0.5, 0.5):
                rr = rng.uniform(0.55, 0.72)
                zz = z + rr * K + rng.uniform(0.0, 0.8)
                k.blob(a, b, zz, rr, rr, rr * K, "bubble", subdiv=2)
                k.blob(a + rr * 0.35, b - rr * 0.35, zz + rr * K * 0.45, rr * 0.22, rr * 0.22, rr * K * 0.2,
                       "bubble_hi", subdiv=1)
    elif load == "cola":
        for b in (-0.62, 0.62):  # two big bottles lying, necks forward... and backwards
            d = 1 if b < 0 else -1
            zc = z + 0.62 * K
            c0 = a0 + 0.2 if d > 0 else a1 - 0.2
            pts = [(0.0, 0.6, "cola"), (2.4, 0.6, "cola"), (2.9, 0.42, "cola"), (3.3, 0.22, "cola"), (3.6, 0.26, "toy_red")]
            for (s0, r0, m0), (s1, _, _) in zip(pts, pts[1:]):
                k.rod((c0 + d * s0, b, zc), (c0 + d * s1, b, zc), r0, m0, n=10)
            k.rod((c0 + d * 0.8, b, zc), (c0 + d * 1.6, b, zc), 0.62, "toy_red", n=10)  # label


def toybox(k, colours, roof=None):
    """Toy box van body with coloured panels."""
    a0, a1, z = BACK + 0.05, TOY_CAB - 0.12, TOY_BED
    top = z + 5.2
    secs = [(z - 0.45, a0, a1, BH, 0.2, 0.35), (top - 0.6, a0, a1, BH, 0.2, 0.35), (top, a0 + 0.3, a1 - 0.2, BH - 0.25, 0.3, 0.4)]
    shell(k, secs, colours[0], n=4)
    L = a1 - a0
    for i, c in enumerate(colours[1:]):  # panels on the sides
        a = a0 + L * (i + 0.5) / (len(colours) - 1)
        for s in (-1, 1):
            k.box(a - 0.62, a + 0.62, *sorted((s * BH, s * (BH + 0.05))), z + 1.2, z + 3.7, c)
    tail_lights(k, a0 + 0.1, z - 0.05)
    return a0, a1, z, top


def toyvan(k):
    toy_chassis(k)
    a0, a1, z, top = toybox(k, ["toy_yellow", "toy_blue", "toy_red", "toy_green"])
    k.blob(-1.4, 0, top + 1.0, 0.75, 0.75, 1.9, "toy_brown")  # teddy on the roof
    k.blob(-1.4, 0, top + 2.9, 0.55, 0.55, 1.35, "toy_brown")
    for s in (-1, 1):
        k.blob(-1.4, s * 0.42, top + 3.9, 0.2, 0.2, 0.5, "toy_brown")
    k.blob(-0.9, 0, top + 2.7, 0.18, 0.2, 0.35, "toy_white")


def toymail(k):
    toy_chassis(k)
    a0, a1, z, top = toybox(k, ["toy_white", "cc", "cc"])
    for s in (-1, 1):  # envelope
        k.box(-2.5, -0.3, *sorted((s * (BH + 0.04), s * (BH + 0.08))), z + 2.0, z + 3.6, "toy_white")
        k.extrude([(-2.5, z + 3.6), (-0.3, z + 3.6), (-1.4, z + 2.6)], "y", *sorted((s * (BH + 0.07), s * (BH + 0.1))), "toy_red")
    k.box(-3.0, 0.6, -0.9, 0.9, top - 0.05, top + 0.25, "toy_yellow")


def toysweets(k):
    toy_chassis(k)
    a0, a1, z, top = toybox(k, ["toy_pink", "toy_mint", "toy_yellow", "toy_mint"])
    a = -1.3
    k.rod((a, 0, top), (a, 0, top + 2.6), 0.1, "lolly", n=6)  # lollipop
    zc = top + 2.6 + 1.25 * K * 0.7
    for i, (r, c) in enumerate(((1.25, "toy_red"), (0.95, "lolly"), (0.68, "toy_red"), (0.4, "lolly"), (0.18, "toy_red"))):
        k.rod((a, -0.1 - i * 0.02, zc), (a, 0.1 + i * 0.02, zc), r, c, n=16)


def toybus(k):
    """Toy bus: rounded loaf in company colour, yellow roof, round windows."""
    k.box(-3.6, 3.5, -0.85, 0.85, TOY_R * K - 0.4, 1.6, "toy_white")
    for a in (2.65, -2.35):
        wheel(k, a, TOY_R, hb=HB, w=0.5, hub="toy_yellow", rim="toy_red")
    secs = [(1.2, -3.95, 3.95, HB, 0.9, 0.7), (6.4, -3.95, 3.98, HB, 1.0, 0.75),
            (7.6, -3.8, 3.7, 1.2, 1.0, 0.8), (8.4, -3.4, 3.2, 0.9, 0.8, 0.7)]
    shell(k, secs, "cc", n=4)
    band(k, secs, 7.2, 8.43, "toy_yellow", out=0.02, n=4)
    band(k, secs, 4.6, 6.6, "glass_light", out=0.03, n=4, a_min=2.6)
    for a in bk.frange(-3.0, 2.2, 1.25):
        for s in (-1, 1):
            k.rod((a, s * (HB - 0.05), 5.6), (a, s * (HB + 0.06), 5.6), 0.5, "toy_white", n=12)
            k.rod((a, s * (HB + 0.02), 5.6), (a, s * (HB + 0.09), 5.6), 0.38, "glass_light", n=12)
    for s in (-1, 1):
        k.blob(3.84, s * 0.72, 3.4, 0.22, 0.34, 0.8, "toy_white")
        k.blob(3.98, s * 0.72, 3.4, 0.1, 0.2, 0.48, "toy_yellow")
    k.rod((4.0, -1.15, 1.7), (4.0, 1.15, 1.7), 0.3, "toy_white", n=8)
    for a in (2.65, -2.35):
        arch(k, a, TOY_R, mat="toy_white", grow=0.16)
    tail_lights(k, -3.92, 2.6)


# --- registry -----------------------------------------------------------------------------------

def truck(g, body, *args, **kw):
    def build(k):
        CABS[g](k)
        body(k, g, *args, **kw)
    return build


ROAD = {}
for _g in (1, 2, 3):
    ROAD[f"bus{_g}"] = ("road", (bus1, bus2, bus3)[_g - 1])
    _h = 2.6 if _g == 1 else 2.9
    for _n, _f, _a in (
            ("coal{}_e", tipper, dict(h=_h)), ("coal{}_l", tipper, dict(h=_h, load="coal", seed=_g)),
            ("grain{}_e", tipper, dict(h=_h - 0.4, hoops=True)),
            ("grain{}_l", tipper, dict(h=_h - 0.4, hoops=True, load="grain", seed=_g + 3)),
            ("ore{}_e", tipper, dict(h=_h - 0.2, slope=True)),
            ("iron{}_l", tipper, dict(h=_h - 0.2, slope=True, load="ore", seed=_g + 6)),
            ("copper{}_l", tipper, dict(h=_h - 0.2, slope=True, load="copper_ore", seed=_g + 9)),
            ("wood{}_e", stakes, {}), ("wood{}_l", stakes, dict(logs=True)),
            ("flat{}_e", flatbed, {}), ("steel{}_l", flatbed, dict(load="steel")),
            ("paper{}_l", flatbed, dict(load="paper")),
            ("mail{}", van, dict(kind="mail")), ("goods{}", van, dict(kind="goods")),
            ("food{}", van, dict(kind="food")), ("armour{}", van, dict(kind="armour")),
            ("oil{}", tank, dict(kind="oil")), ("water{}", tank, dict(kind="water")),
            ("live{}", livestock, {}),
            ("fruit{}_e", fruit, dict(loaded=False)), ("fruit{}_l", fruit, dict(loaded=True)),
            ("rubber{}_e", rubber, dict(loaded=False)), ("rubber{}_l", rubber, dict(loaded=True))):
        ROAD[_n.format(_g)] = ("road", truck(_g, _f, **_a))

ROAD.update({
    "toybus": ("road", toybus),
    "toysugar_e": ("road", partial(toytipper, wall="toy_pink", rim="toy_white", load=None)),
    "toysugar_l": ("road", partial(toytipper, wall="toy_pink", rim="toy_white", load="sugar")),
    "toycola_e": ("road", partial(toyflat, rail="toy_red", load=None)),
    "toycola_l": ("road", partial(toyflat, rail="toy_red", load="cola")),
    "toyfloss_e": ("road", partial(toytipper, wall="toy_cyan", rim="toy_pink", load=None)),
    "toyfloss_l": ("road", partial(toytipper, wall="toy_cyan", rim="toy_pink", load="floss")),
    "toytoffee_e": ("road", partial(toytipper, wall="toy_orange", rim="toy_yellow", load=None)),
    "toytoffee_l": ("road", partial(toytipper, wall="toy_orange", rim="toy_yellow", load="toffee")),
    "toyvan": ("road", toyvan), "toymail": ("road", toymail), "toysweets": ("road", toysweets),
    "toybattery_e": ("road", partial(toyflat, rail="toy_blue", load=None)),
    "toybattery_l": ("road", partial(toyflat, rail="toy_blue", load="battery")),
    "toyfizzy_e": ("road", partial(toyflat, rail="toy_green", load=None)),
    "toyfizzy_l": ("road", partial(toyflat, rail="toy_green", load="fizzy")),
    "toyplastic_e": ("road", partial(toyflat, rail="toy_purple", load=None)),
    "toyplastic_l": ("road", partial(toyflat, rail="toy_purple", load="plastic")),
    "toybubble_e": ("road", partial(toyflat, rail="toy_mint", load=None)),
    "toybubble_l": ("road", partial(toyflat, rail="toy_mint", load="bubble")),
})
