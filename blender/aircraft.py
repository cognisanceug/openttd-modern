"""Aircraft models for render_vehicles.py: the 20 original aircraft sprite sets, toyland's 6 and the rotors.

Same conventions as the ships: local +a is the nose, b the right wing, z height units up from the
vehicle's z_pos. On the ground z_pos is the ground + 1 (aircraft_cmd.cpp), so wheels touch z = -1.
One x/y unit is K = 2.449 z units in true proportions; radii are x/y units, heights z units.

Sprite sets (_aircraft_sprite in aircraft_cmd.cpp, base + Direction):
  liner4hi   0xE9D  image 6   Bakewell Luckett LB-8, Yate Aerospace YAe46 (high wing, four small jets)
  jumbo      0xEA5  image 7   Darwin 300
  concorde   0xEAD  image 8   Yate Haugan (supersonic)
  prop4tri   0xEB5  image 0   Coleman Count (four props, triple fin)
  trimotor   0xEBD  image 1   Sampson U52
  jet_t      0xEC5  image 2   FFP Dart, Bakewell Luckett LB-9 / LB80, YAC 1-11, Darwin 100, Dinger 100
  trijet     0xECD  image 3   Bakewell Luckett LB-10 / LB-11, Guru Galaxy
  twinjet    0xED5  image 4   Darwin 200 / 400 / 500 / 600, Airtaxi A21 / A31 / A32 / A33
  prop4      0xEDD  image 5   Bakewell Cotswald LB-3
  heli       0xEE5  image 9   Tricario Helicopter
  hyperdart  0xEED  image 16  FFP Hyperdart 2
  bwb        0xEF5  image 17  Dinger 200 (blended wing body)
  hypersonic 0xEFD  image 18  Dinger 1000
  zshuttle   0xF05  image 10  Yate Z-Shuttle (ducted pusher fans)
  flywing    0xF0D  image 11  AirTaxi A34-1000
  canard     0xF15  image 12  Kelling K6
  boxwing    0xF1D  image 13  Kelling K7
  truss      0xF25  image 14  Darwin 700
  eprop      0xF2D  image 15  Kelling K1 (distributed electric props)
  heli2      0xF35  image 19  Guru X2 Helicopter
  rotor0-3   3901-3904        rotor stopped, moving 1-3 (with rotor_disc, composited by the packer)
Toyland (its base graphics replace 0xE9D-0xECC and the rotors):
  toybiplane 0xE9D  Ploddyphut 100      toyhiwing  0xEA5  Ploddyphut 500
  toyjet     0xEAD  Flashbang X1        toyjumbo   0xEB5  Juggerplane M1
  toyrocket  0xEBD  Flashbang Wizzer    toyheli    0xEC5  Powernaut Helicopter
  toyrotor0-3, toyrotor_disc
"""

import math

import build_kit as bk
import style as st

W = st.WALL
K = 2.449  # z units per x/y unit
bk.PALETTE.update({
    "skin": ((236, 238, 240), W), "belly": ((196, 202, 208), W), "wing": ((198, 204, 210), W),
    "wing_dark": ((150, 158, 168), W), "window": ((54, 66, 84), W), "cockpit": ((40, 52, 70), W),
    "nacelle": ((214, 218, 222), W), "intake": ((60, 64, 72), W), "tyre": ((44, 46, 50), W),
    "silver": ((182, 188, 194), W), "prop": ((70, 72, 78), W), "blade": ((60, 62, 66), W),
    "rotor_disc": ((150, 154, 160), W), "hub": ((90, 94, 100), W), "exhaust": ((88, 90, 96), W),
    "nav_red": ((220, 60, 56), W), "nav_green": ((70, 190, 100), W),
})
TOY = ["toy_red", "toy_yellow", "toy_blue", "toy_green", "toy_pink", "toy_purple", "toy_orange", "toy_mint"]

GEAR_Z = -1.0  # wheel bottom
HM = 7.2       # helicopter rotor plane (body frame); the rotor sprite sits 5 units higher (ROTOR_Z_OFFSET)


# --- geometry helpers --------------------------------------------------------------------------

def tube(k, rings, mat, cap=True):
    """Closed solid through closed polygon rings [[(a, b, z)]] of equal length."""
    n, m = len(rings[0]), len(rings)
    v = [p for r in rings for p in r]
    f = []
    for j in range(m - 1):
        for i in range(n):
            a, b = j * n + i, j * n + (i + 1) % n
            f.append((a, b, b + n, a + n))
    if cap:
        f += [tuple(range(n)), tuple(range((m - 1) * n, m * n))]
    k._solid(v, f, mat)


def stations(L, R, zc, nose=0.16, tail=0.3, rise=0.7, droop=0.15, tip=0.15, n=5, nose_r=0.1):
    """Fuselage stations [(a, r, zc)] from tail to nose: tail cone sweeps up by rise * R."""
    a0, a1 = -L / 2, L / 2
    lt, ln = tail * L, nose * L
    out = []
    for i in range(n + 1):
        t = i / n
        out.append((a0 + t * lt, R * (tip + (1 - tip) * t ** 0.6), zc + (1 - t) ** 1.6 * rise * R * K))
    for i in range(1, n + 1):
        t = i / n
        r = R * max(nose_r, math.sqrt(max(0.0, 1 - t ** 2.2)))
        out.append((a1 - ln + t * ln, r, zc - droop * R * K * t ** 2))
    return out


def ring(a, r, zc, th0, th1, m=7, scale=1.0, chord=True):
    """Arc from angle th0 to th1 (degrees, 0 = right side, 90 = top) around (a, 0, zc)."""
    pts = []
    for i in range(m + 1):
        th = math.radians(th0 + (th1 - th0) * i / m)
        pts.append((a, r * scale * math.cos(th), zc + r * scale * K * math.sin(th)))
    return pts


def fuselage(k, st_, top, bottom=None, split=-15):
    """Fuselage through stations; with bottom, the part below the split angle is a second colour."""
    if bottom is None:
        tube(k, [ring(a, r, zc, 0, 360, 12)[:-1] for a, r, zc in st_], top)
        return
    tube(k, [ring(a, r, zc, split, 180 - split, 8) for a, r, zc in st_], top)
    tube(k, [ring(a, r, zc, 180 - split, 360 + split, 6, 0.995) for a, r, zc in st_], bottom)


def interp(st_, a):
    """(r, zc) of the fuselage at a."""
    for (a0, r0, z0), (a1, r1, z1) in zip(st_, st_[1:]):
        if a0 <= a <= a1:
            t = (a - a0) / (a1 - a0) if a1 > a0 else 0
            return r0 + (r1 - r0) * t, z0 + (z1 - z0) * t
    return st_[-1][1], st_[-1][2]


def band(k, st_, a0, a1, th0, th1, mat, out=1.04, steps=6):
    """Thin shell on the fuselage between a0 and a1 at angles th0-th1 (both sides mirrored)."""
    for s0, s1 in ((th0, th1), (180 - th1, 180 - th0)):
        rings = []
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            r, zc = interp(st_, a)
            outer = ring(a, r, zc, s0, s1, 3, out, False)
            inner = ring(a, r, zc, s1, s0, 3, 0.92, False)
            rings.append(outer + inner)
        tube(k, rings, mat)


def cockpit(k, st_, L, nose=0.16, t0=0.25, t1=0.62, th0=18, th1=162, mat="cockpit"):
    a1 = L / 2
    ln = nose * L
    rings = []
    for i in range(5):
        a = a1 - ln + ln * (t0 + (t1 - t0) * i / 4)
        r, zc = interp(st_, a)
        rings.append(ring(a, r, zc, th0, th1, 6, 1.04, False) + ring(a, r, zc, th1, th0, 6, 0.9, False))
    tube(k, rings, mat)


def section(a_le, chord, b, z, th, ridge=0.32):
    """Airfoil section at span b: leading edge, top ridge, trailing edge, bottom."""
    return [(a_le, b, z + th * 0.35), (a_le - ridge * chord, b, z + th), (a_le - chord, b, z + th * 0.15),
            (a_le - ridge * chord, b, z)]


def wing(k, a_le, chord, span, tip_chord, sweep, z, mat, b0=0.0, dihedral=0.0, th=0.9, tip_th=None, both=True,
         mid=None):
    """Tapered wing from b0 to b0 + span; sweep moves the tip leading edge aft (negative a)."""
    tip_th = th * 0.45 if tip_th is None else tip_th
    secs = [(a_le, chord, b0, z, th)]
    if mid:  # (fraction of span, a_le, chord) for a cranked planform
        f, ma, mc = mid
        secs.append((ma, mc, b0 + f * span, z + dihedral * f, th + (tip_th - th) * f))
    secs.append((a_le + sweep, tip_chord, b0 + span, z + dihedral, tip_th))
    for s in ((1, -1) if both else (1,)):
        tube(k, [[(p[0], s * p[1], p[2]) for p in section(*sec)] for sec in secs], mat)


def fin(k, a_le, chord, height, tip_chord, sweep, z0, mat, b=0.0, th=0.14, cant=0.0):
    """Vertical fin: root section at z0, tip at z0 + height (z units); cant leans it out by b units."""
    def sec(a, c, bb, z):
        return [(a, bb, z), (a - 0.32 * c, bb + th, z), (a - c, bb, z), (a - 0.32 * c, bb - th, z)]
    tube(k, [sec(a_le, chord, b, z0), sec(a_le + sweep, tip_chord, b + cant, z0 + height)], mat)


def nacelle(k, a_front, length, r, b, z, mat="nacelle", intake="intake", pylon=None, cone=True):
    """Engine pod along a; pylon=(z_top, mat) hangs it under a wing."""
    k.rod((a_front - length, b, z), (a_front, b, z), r, mat, n=8)
    k.rod((a_front, b, z), (a_front + 0.06, b, z), r * 0.78, intake, n=8)
    if cone:
        k.rod((a_front - length - 0.4, b, z), (a_front - length, b, z), r * 0.5, "exhaust", n=6)
    if pylon:
        zt, pm = pylon
        k.box(a_front - length * 0.8, a_front - length * 0.15, b - 0.08, b + 0.08, z, zt, pm)


def propeller(k, a, b, z, R, blades=3, spin=0.0, mat="blade", hub="prop"):
    """Spinner and blades in the b/z plane at a."""
    k.rod((a - 0.3, b, z), (a + 0.35, b, z), R * 0.18, hub, n=6)
    for i in range(blades):
        th = spin + i * math.tau / blades
        k.rod((a, b, z), (a, b + R * math.cos(th), z + R * K * math.sin(th)), 0.07, mat, n=4)


def gear(k, a, b, z_top, r=0.28, twin=True, leg="silver"):
    """Leg from z_top down to a wheel (pair) touching GEAR_Z."""
    axle = GEAR_Z + r * K
    k.rod((a, b, z_top), (a, b, axle), 0.07, leg, n=4)
    for s in ((-1, 1) if twin else (0,)):
        bb = b + s * 0.16
        k.rod((a, bb - 0.09, axle), (a, bb + 0.09, axle), r, "tyre", n=8)


def gear_set(k, st_, a_nose, a_main, b_main, z_wing=None, r=0.28, twin=True):
    r_n, z_n = interp(st_, a_nose)
    gear(k, a_nose, 0, z_n - r_n * K * 0.8, r * 0.8, twin)
    for s in (-1, 1):
        rr, zz = interp(st_, a_main)
        gear(k, a_main, s * b_main, z_wing if z_wing is not None else zz - rr * K * 0.6, r, twin)


def nav_lights(k, a, b, z):
    k.blob(a, b, z, 0.12, 0.12, 0.3, "nav_green")
    k.blob(a, -b, z, 0.12, 0.12, 0.3, "nav_red")


# --- classic aircraft -----------------------------------------------------------------------

def jumbo(k):
    """Four-engined wide-body with the upper-deck hump: white, company-colour cheatline, belly and tail."""
    L, R = 20.0, 0.95
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.14, tail=0.3, rise=0.75)
    fuselage(k, s, "skin", "cc", split=-28)
    hump = stations(8.5, 0.62, zc + 1.1, nose=0.4, tail=0.45, rise=-0.4, droop=0.4, tip=0.3)
    fuselage(k, [(a + 5.2, r, z) for a, r, z in hump], "skin")
    band(k, s, -6.8, 7.4, 16, 24, "window")
    cockpit(k, [(a + 5.2, r, z) for a, r, z in hump], 8.5, nose=0.4, t0=0.55, t1=0.85, th0=25, th1=155)
    zw = zc - R * K * 0.55
    wing(k, 2.6, 5.2, 9.6, 1.1, -5.6, zw, "wing", b0=0.5, dihedral=1.6, th=1.1, mid=(0.3, 1.3, 3.2))
    for b, a in ((3.4, 2.1), (6.4, 0.2)):
        for sgn in (-1, 1):
            nacelle(k, a + 0.4, 2.4, 0.42, sgn * b, zw - 1.0 + b * 0.12, "cc", pylon=(zw + 0.2, "wing_dark"))
    wing(k, -6.6, 2.6, 3.8, 0.9, -2.4, zc + 0.6, "wing", b0=0.3, dihedral=0.5, th=0.5)
    fin(k, -6.4, 3.6, 8.5, 1.4, -2.9, zc + 1.0, "cc", th=0.16)
    gear_set(k, s, 7.4, 0.2, 1.4)
    nav_lights(k, -3.1, 10.1, zw + 1.6)


def twinjet(k):
    """Twin-engined wide-body: big turbofans, white top over a company-colour belly and tail."""
    L, R = 16.5, 0.85
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.14, tail=0.3, rise=0.75)
    fuselage(k, s, "skin", "cc", split=-25)
    band(k, s, -4.8, 5.9, 18, 26, "window")
    cockpit(k, s, L)
    zw = zc - R * K * 0.55
    wing(k, 2.0, 4.4, 8.0, 0.9, -4.6, zw, "wing", b0=0.4, dihedral=1.4, th=1.0, mid=(0.3, 0.9, 2.6))
    for sgn in (-1, 1):
        nacelle(k, 1.8, 2.4, 0.55, sgn * 3.0, zw - 1.2, "skin", pylon=(zw + 0.2, "wing_dark"))
        k.rod((0.1, sgn * 3.0, zw - 1.2), (0.9, sgn * 3.0, zw - 1.2), 0.57, "cc", n=8)
    wing(k, -5.4, 2.2, 3.2, 0.8, -2.0, zc + 0.5, "wing", b0=0.3, dihedral=0.4, th=0.45)
    fin(k, -5.2, 3.2, 7.2, 1.3, -2.6, zc + 0.9, "cc")
    gear_set(k, s, 6.2, 0.1, 1.3)


def trijet(k):
    """Wide-body trijet: two wing engines and the third through the base of the fin."""
    L, R = 17.0, 0.88
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.14, tail=0.26, rise=0.5)
    fuselage(k, s, "skin", "belly", split=-18)
    band(k, s, -5.6, 6.0, 18, 25, "window")
    band(k, s, -6.6, 7.0, 6, 13, "cc")
    cockpit(k, s, L)
    zw = zc - R * K * 0.55
    wing(k, 2.2, 4.4, 8.2, 0.9, -4.6, zw, "wing", b0=0.4, dihedral=1.4, th=1.0, mid=(0.3, 1.0, 2.7))
    for sgn in (-1, 1):
        nacelle(k, 2.9, 2.2, 0.48, sgn * 3.3, zw - 1.3, "nacelle", pylon=(zw + 0.2, "wing_dark"))
    # Tail engine: a pod on the fin root, the fin above it.
    zt = zc + R * K + 1.0
    nacelle(k, -5.2, 3.2, 0.5, 0, zt, "cc")
    k.box(-8.0, -5.6, -0.15, 0.15, zc + 0.8, zt, "cc")
    fin(k, -6.4, 2.8, 6.2, 1.2, -2.2, zt + 0.8, "cc")
    wing(k, -6.6, 2.0, 3.2, 0.8, -1.9, zc + 0.4, "wing", b0=0.3, dihedral=0.4, th=0.45)
    gear_set(k, s, 6.6, 0.0, 1.3)


def jet_t(k):
    """Short-haul jet: engines on the rear fuselage, T-tail; company-colour fuselage under a white roof."""
    L, R = 12.5, 0.62
    zc = GEAR_Z + 0.8 + R * K
    s = stations(L, R, zc, nose=0.15, tail=0.28, rise=0.6)
    fuselage(k, s, "skin", "cc", split=5)
    band(k, s, -2.6, 4.6, 20, 30, "window")
    cockpit(k, s, L)
    zw = zc - R * K * 0.6
    wing(k, 1.6, 3.0, 5.6, 0.8, -3.0, zw, "wing", b0=0.3, dihedral=1.0, th=0.8)
    for sgn in (-1, 1):
        nacelle(k, -2.4, 2.2, 0.42, sgn * 1.25, zc + 0.6, "nacelle")
        k.box(-4.0, -3.0, min(sgn * 0.4, sgn * 0.9), max(sgn * 0.4, sgn * 0.9), zc + 0.4, zc + 0.8, "wing_dark")
    fin(k, -4.3, 2.6, 5.6, 1.6, -2.4, zc + 0.8, "cc")
    wing(k, -6.2, 1.5, 2.4, 0.8, -1.2, zc + 6.3, "cc", b0=0.0, dihedral=0.2, th=0.4)
    gear_set(k, s, 4.9, 0.0, 1.1, twin=False)


def liner4hi(k):
    """High-wing four-jet regional airliner with a T-tail."""
    L, R = 12.5, 0.7
    zc = GEAR_Z + 0.8 + R * K
    s = stations(L, R, zc, nose=0.14, tail=0.3, rise=0.75)
    fuselage(k, s, "skin", "belly", split=-12)
    band(k, s, -3.2, 4.4, 14, 24, "window")
    band(k, s, -4.4, 5.2, 2, 10, "cc")
    cockpit(k, s, L)
    zw = zc + R * K * 0.85
    k.box(-0.6, 1.6, -0.6, 0.6, zc, zw + 0.5, "skin")  # wing root fairing
    wing(k, 1.8, 2.8, 6.2, 1.0, -1.6, zw, "wing", b0=0.2, dihedral=-0.6, th=0.8)
    for b in (1.8, 3.2):
        for sgn in (-1, 1):
            nacelle(k, 2.2 - b * 0.18, 1.7, 0.36, sgn * b, zw - 1.0, "cc", pylon=(zw + 0.2, "wing_dark"))
    fin(k, -4.6, 2.6, 6.0, 1.6, -2.2, zc + 1.0, "cc")
    wing(k, -6.7, 1.5, 2.8, 0.9, -0.8, zc + 6.6, "wing", dihedral=0.0, th=0.4)
    # Main gear in fuselage blisters.
    for sgn in (-1, 1):
        k.blob(0.4, sgn * 0.62, zc - R * K * 0.6, 1.3, 0.3, 0.8, "belly")
    gear_set(k, s, 4.8, 0.4, 0.8, twin=False)


def concorde(k):
    """Supersonic airliner: needle fuselage, ogival delta, paired engines, drooped nose."""
    L, R = 19.0, 0.52
    zc = GEAR_Z + 1.9 + R * K
    s = stations(L, R, zc, nose=0.2, tail=0.18, rise=0.25, droop=0.5, nose_r=0.05)
    fuselage(k, s, "skin")
    band(k, s, -5.0, 5.4, 12, 22, "window")
    band(k, s, -7.4, 7.4, 2, 7, "cc")
    cockpit(k, s, L, nose=0.2, t0=0.15, t1=0.4, th0=30, th1=150)
    zw = zc - R * K * 0.5
    secs = [(4.6, 13.4, 0.3, zw, 1.0), (-1.4, 7.6, 2.4, zw, 0.7), (-4.6, 4.2, 4.1, zw, 0.4),
            (-6.2, 2.4, 4.6, zw + 0.2, 0.25)]
    for sgn in (1, -1):
        tube(k, [[(p[0], sgn * p[1], p[2]) for p in section(*sec, ridge=0.45)] for sec in secs], "skin")
        for b in (1.3, 2.1):
            k.box(-7.8, -3.0, sgn * b - 0.38, sgn * b + 0.38, zw - 1.6, zw + 0.1, "nacelle")
            k.box(-3.0, -2.8, sgn * b - 0.3, sgn * b + 0.3, zw - 1.4, zw - 0.2, "intake")
    fin(k, -5.2, 4.0, 7.0, 1.2, -3.6, zc + 0.6, "cc", th=0.14)
    gear_set(k, s, 5.8, -2.6, 1.7, z_wing=zw, r=0.26)


def prop4tri(k):
    """Four-engined piston airliner with a curved fuselage and triple fins."""
    L, R = 13.0, 0.62
    zc = GEAR_Z + 1.4 + R * K
    s = stations(L, R, zc, nose=0.18, tail=0.32, rise=0.4, droop=0.1)
    fuselage(k, s, "skin", "silver", split=-5)
    band(k, s, -3.6, 4.0, 16, 26, "window")
    band(k, s, -5.0, 4.8, 3, 11, "cc")
    cockpit(k, s, L, nose=0.18)
    zw = zc - R * K * 0.5
    wing(k, 1.8, 2.6, 7.4, 1.0, -0.8, zw, "silver", b0=0.3, dihedral=1.2, th=0.75)
    for b in (2.0, 4.0):
        for sgn in (-1, 1):
            nacelle(k, 2.4, 2.4, 0.38, sgn * b, zw + 0.1 + b * 0.16, "silver", "cc", cone=False)
            propeller(k, 2.5, sgn * b, zw + 0.1 + b * 0.16, 0.95, 3, spin=0.5 + b)
    wing(k, -5.2, 1.6, 3.0, 1.0, -0.4, zc + 0.8, "silver", dihedral=0.6, th=0.4)
    for b in (0, 1.6, -1.6):
        fin(k, -5.0, 1.8 if b else 2.0, 3.4 if b else 4.2, 1.2, -0.6, zc + 0.9 + (0.25 if b else 0), "cc",
            b=b, th=0.1)
    gear_set(k, s, 5.0, 1.4, 2.0, z_wing=zw, twin=False, r=0.3)


def prop4(k):
    """Post-war four-propeller airliner, low wing, single fin."""
    L, R = 11.0, 0.58
    zc = GEAR_Z + 1.3 + R * K
    s = stations(L, R, zc, nose=0.15, tail=0.33, rise=0.5, droop=0.05)
    fuselage(k, s, "silver", "cc", split=-8)
    band(k, s, -2.8, 3.6, 16, 26, "window")
    cockpit(k, s, L)
    zw = zc - R * K * 0.6
    wing(k, 1.6, 2.4, 6.4, 0.9, -0.6, zw, "silver", b0=0.3, dihedral=1.0, th=0.7)
    for b in (1.8, 3.5):
        for sgn in (-1, 1):
            nacelle(k, 2.0, 2.2, 0.34, sgn * b, zw + 0.2 + b * 0.15, "silver", "cc", cone=False)
            propeller(k, 2.1, sgn * b, zw + 0.2 + b * 0.15, 0.85, 3, spin=b)
    wing(k, -4.4, 1.4, 2.6, 0.8, -0.5, zc + 0.6, "silver", dihedral=0.4, th=0.4)
    fin(k, -4.0, 2.2, 4.6, 1.1, -1.5, zc + 0.8, "cc")
    gear_set(k, s, 4.2, 1.2, 1.8, z_wing=zw, twin=False, r=0.28)


def trimotor(k):
    """Early corrugated trimotor: square-ish fuselage, thick straight wing, three radials, spatted wheels."""
    L, R = 9.5, 0.6
    zc = GEAR_Z + 1.6 + R * K
    s = stations(L, R, zc, nose=0.1, tail=0.4, rise=0.5, droop=0.0, nose_r=0.55)
    fuselage(k, s, "silver")
    for a in bk.frange(-2.5, 3.6, 0.7):  # corrugation ribs
        r, z = interp(s, a)
        k.rod((a, 0, z), (a + 0.05, 0, z), r * 1.02, "steel", n=10)
    band(k, s, -1.4, 2.6, 18, 34, "window")
    band(k, s, -3.6, 3.6, 2, 10, "cc")
    cockpit(k, s, L, nose=0.1, t0=-1.6, t1=-0.2, th0=30, th1=150)
    zw = zc - R * K * 0.7
    wing(k, 1.8, 2.8, 6.6, 1.4, -0.3, zw, "silver", b0=0.3, dihedral=0.8, th=1.0)
    nacelle(k, 5.3, 0.8, 0.5, 0, zc, "cc", cone=False)
    propeller(k, 5.4, 0, zc, 0.95, 2, spin=0.6)
    for sgn in (-1, 1):
        nacelle(k, 2.8, 1.6, 0.42, sgn * 2.0, zw + 0.2, "cc", cone=False)
        propeller(k, 2.9, sgn * 2.0, zw + 0.2, 0.85, 2, spin=1.3)
        k.blob(1.0, sgn * 2.0, GEAR_Z + 0.75, 0.5, 0.2, 0.7, "cc")  # wheel spat
        k.rod((1.0, sgn * 2.0, GEAR_Z + 1.0), (1.0, sgn * 2.0, zw), 0.08, "silver", n=4)
        k.rod((1.0, sgn * 2.0, GEAR_Z + 1.0), (1.0, sgn * 0.4, zc - R * K * 0.8), 0.06, "silver", n=4)
    wing(k, -3.6, 1.4, 2.4, 1.0, -0.2, zc + 0.6, "silver", th=0.4)
    fin(k, -3.4, 1.8, 3.8, 1.3, -0.8, zc + 0.8, "cc")
    k.rod((-4.4, 0, GEAR_Z + 0.4), (-4.4, 0, zc - 0.8), 0.06, "silver", n=4)
    k.rod((-4.45, -0.08, GEAR_Z + 0.4), (-4.45, 0.08, GEAR_Z + 0.4), 0.17, "tyre", n=6)


# --- helicopters ----------------------------------------------------------------------------

def mast(k, z0):
    k.cyl(0, 0, 0.18, z0, HM, "hub", n=6)


def heli(k):
    """Light utility helicopter: glazed cabin, slim tail boom, skids; rotor hub over the origin."""
    cab = [(-1.8, 0.35, 2.6), (-1.0, 0.75, 2.4), (0.2, 0.85, 2.4), (1.2, 0.8, 2.3), (2.0, 0.55, 2.0),
           (2.5, 0.2, 1.8)]
    fuselage(k, cab, "cc", "skin", split=-30)
    cockpit(k, cab, 4.3, nose=0.45, t0=0.0, t1=0.95, th0=-10, th1=190)
    k.box(-1.6, 0.6, -0.45, 0.45, 4.0, 5.0, "skin")  # engine cowling
    mast(k, 4.8)
    boom = [(-5.8, 0.12, 4.0), (-1.6, 0.26, 3.2)]
    fuselage(k, boom, "cc")
    fin(k, -5.0, 1.0, 3.2, 0.6, -0.7, 3.6, "cc", th=0.06)
    wing(k, -4.6, 0.7, 0.9, 0.5, -0.1, 3.4, "skin", th=0.2)
    k.rod((-5.6, 0.2, 4.6), (-5.6, 0.25, 4.6), 0.55, "blade", n=10)  # tail rotor
    for sgn in (-1, 1):
        k.rod((-1.8, sgn * 0.95, GEAR_Z + 0.15), (2.0, sgn * 0.95, GEAR_Z + 0.15), 0.07, "steel_dark", n=4)
        for a in (-1.0, 1.0):
            k.rod((a, sgn * 0.95, GEAR_Z + 0.15), (a, sgn * 0.5, 0.8), 0.06, "steel_dark", n=4)


def heli2(k):
    """Twin-engined helicopter: longer cabin, wheels, shrouded tail rotor."""
    cab = [(-2.6, 0.45, 2.6), (-1.6, 0.9, 2.2), (0.6, 0.95, 2.2), (1.8, 0.85, 2.0), (2.8, 0.5, 1.6),
           (3.2, 0.15, 1.4)]
    fuselage(k, cab, "skin", "cc", split=-5)
    band(k, cab, -1.4, 1.2, 12, 30, "window")
    cockpit(k, cab, 5.8, nose=0.35, t0=0.15, t1=0.8, th0=5, th1=175)
    k.box(-2.0, 0.8, -0.6, 0.6, 4.2, 5.2, "skin")
    for sgn in (-1, 1):
        k.rod((-1.6, sgn * 0.62, 4.7), (0.6, sgn * 0.62, 4.7), 0.24, "cc", n=6)
    mast(k, 5.0)
    boom = [(-6.6, 0.16, 4.2), (-2.4, 0.32, 3.4)]
    fuselage(k, boom, "cc")
    k.rod((-6.4, -0.22, 4.4), (-6.4, 0.22, 4.4), 0.62, "cc", n=12)  # fenestron shroud
    k.rod((-6.4, -0.24, 4.4), (-6.4, 0.24, 4.4), 0.42, "dark", n=12)
    fin(k, -6.4, 1.2, 3.0, 0.8, -0.8, 5.6, "cc", th=0.08)
    wing(k, -5.6, 0.8, 1.2, 0.6, -0.1, 3.8, "skin", th=0.2)
    for sgn in (-1, 1):
        k.box(-0.8, 0.8, sgn * 0.9 - 0.25, sgn * 0.9 + 0.25, 0.4, 1.4, "cc")  # sponsons
        gear(k, 0.0, sgn * 1.0, 0.6, 0.26, twin=False)
    gear(k, 2.4, 0, 0.8, 0.2, twin=False)


def rotor_blades(k, n=4, spin=0.0, R=4.4, mat="blade", w=0.14):
    for i in range(n):
        th = spin + i * math.tau / n
        c, s = math.cos(th), math.sin(th)
        p = [(0.3 * c - w * s, 0.3 * s + w * c), (R * c - w * s, R * s + w * c), (R * c + w * s, R * s - w * c),
             (0.3 * c + w * s, 0.3 * s - w * c)]
        k.prism(p, HM, HM + 0.18, mat)


def rotor_hub(k, mat="hub"):
    k.cyl(0, 0, 0.42, HM - 0.1, HM + 0.5, mat, n=8)
    k.cyl(0, 0, 0.18, HM + 0.5, HM + 0.9, mat, n=6)


def rotor_model(frame, toy=False):
    def build(k):
        R = 4.4
        if frame == "disc":
            k.cyl(0, 0, R, HM + 0.02, HM + 0.12, "toy_white" if toy else "rotor_disc", n=24)
            return
        if frame == "hub":
            rotor_hub(k, "toy_red" if toy else "hub")
            return
        spin = (0.0, 0.0, math.radians(30), math.radians(60))[frame]
        if toy:
            for i, m in enumerate(("toy_red", "toy_yellow", "toy_blue")):
                rotor_blades(k, 1, spin + i * math.tau / 3, R, m, 0.22)
        else:
            rotor_blades(k, 4, spin + math.radians(15), R)
        if frame == 0:
            rotor_hub(k, "toy_red" if toy else "hub")
    return build


# --- futuristic aircraft --------------------------------------------------------------------

def hyperdart(k):
    """Small supersonic transport: sharp delta, canards, two canted fins, engines in the wing roots."""
    L, R = 13.5, 0.55
    zc = GEAR_Z + 1.6 + R * K
    s = stations(L, R, zc, nose=0.26, tail=0.12, rise=0.1, droop=0.1, nose_r=0.04)
    fuselage(k, s, "cc", "skin", split=-10)
    cockpit(k, s, L, nose=0.26, t0=0.2, t1=0.45, th0=25, th1=155)
    band(k, s, -2.0, 2.6, 14, 24, "window")
    zw = zc - R * K * 0.4
    for sgn in (1, -1):
        secs = [(2.4, 8.6, 0.3, zw, 1.1), (-3.0, 3.6, 3.6, zw + 0.3, 0.4), (-4.6, 2.0, 4.4, zw + 0.5, 0.25)]
        tube(k, [[(p[0], sgn * p[1], p[2]) for p in section(*sec, ridge=0.5)] for sec in secs], "skin")
        k.box(-6.8, -1.0, sgn * 1.0 - 0.45, sgn * 1.0 + 0.45, zw - 1.2, zw + 0.3, "skin")
        k.box(-1.0, -0.8, sgn * 1.0 - 0.38, sgn * 1.0 + 0.38, zw - 1.0, zw + 0.1, "intake")
        fin(k, -3.6, 2.8, 4.6, 1.0, -2.2, zw + 0.8, "cc", b=sgn * 1.2, cant=sgn * 0.9, th=0.1)
    wing(k, 4.6, 1.2, 1.6, 0.5, -0.8, zc - 0.2, "cc", b0=0.3, th=0.3)
    gear_set(k, s, 4.0, -1.6, 1.5, z_wing=zw, r=0.24)


def bwb(k):
    """Blended wing body: a wide lifting centre body flowing into the wings, two fins, three engines on top."""
    zb = GEAR_Z + 1.6
    secs = [(6.4, 14.0, 0.0, zb, 4.6), (5.6, 12.4, 2.4, zb + 0.1, 4.0), (3.2, 8.4, 4.4, zb + 0.4, 2.4),
            (0.2, 4.2, 6.0, zb + 0.9, 1.0), (-4.0, 1.8, 11.0, zb + 2.0, 0.4)]
    for sgn in (1, -1):
        tube(k, [[(p[0], sgn * p[1], p[2]) for p in section(*sec, ridge=0.3)] for sec in secs[:3]], "cc")
        tube(k, [[(p[0], sgn * p[1], p[2]) for p in section(*sec, ridge=0.3)] for sec in secs[2:]], "skin")
        fin(k, -3.8, 3.2, 5.0, 1.4, -1.8, zb + 2.0, "cc", b=sgn * 4.3, cant=sgn * 0.5, th=0.14)
    # Cockpit band on the nose, a row of windows along the sides of the centre body.
    k.box(5.4, 6.3, -1.2, 1.2, zb + 2.6, zb + 3.2, "cockpit")
    for sgn in (1, -1):
        k.box(-2.0, 4.4, sgn * 3.5 - 0.06, sgn * 3.5 + 0.06, zb + 1.8, zb + 2.3, "window")
    for b in (-1.8, 0.0, 1.8):
        nacelle(k, -3.0, 2.8, 0.62, b, zb + 5.6, "skin")
        k.box(-5.2, -3.6, b - 0.12, b + 0.12, zb + 3.6, zb + 5.6, "wing_dark")
    for b, a in ((0.0, 4.8), (-2.6, -0.4), (2.6, -0.4)):
        gear(k, a, b, zb + 0.5, 0.3)


def hypersonic(k):
    """Hypersonic airliner: long needle fuselage, small aft delta, canards, engine pods under the wing."""
    L, R = 21.0, 0.55
    zc = GEAR_Z + 1.9 + R * K
    s = stations(L, R, zc, nose=0.3, tail=0.12, rise=0.15, droop=0.05, nose_r=0.03)
    fuselage(k, s, "skin", "cc", split=-20)
    cockpit(k, s, L, nose=0.3, t0=0.15, t1=0.32, th0=30, th1=150)
    band(k, s, -3.6, 3.2, 14, 22, "window")
    zw = zc - R * K * 0.5
    for sgn in (1, -1):
        secs = [(0.0, 10.0, 0.3, zw, 0.9), (-6.6, 3.6, 4.0, zw + 0.2, 0.3)]
        tube(k, [[(p[0], sgn * p[1], p[2]) for p in section(*sec, ridge=0.5)] for sec in secs], "skin")
        k.rod((-9.0, sgn * 1.8, zw - 0.8), (-3.0, sgn * 1.8, zw - 0.8), 0.48, "cc", n=8)
        k.rod((-3.0, sgn * 1.8, zw - 0.8), (-2.2, sgn * 1.8, zw - 0.8), 0.22, "intake", n=6)
        k.rod((-9.6, sgn * 1.8, zw - 0.8), (-9.0, sgn * 1.8, zw - 0.8), 0.3, "exhaust", n=6)
    wing(k, 6.0, 1.4, 1.8, 0.5, -1.0, zc - 0.2, "skin", b0=0.3, th=0.3)
    fin(k, -6.6, 3.8, 5.6, 1.0, -3.0, zc + 0.6, "cc")
    gear_set(k, s, 6.4, -4.2, 1.6, z_wing=zw, r=0.24)


def zshuttle(k):
    """Short-haul shuttle: high straight wing, two big ducted pusher fans on the tail, H-tail."""
    L, R = 11.5, 0.75
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.2, tail=0.3, rise=0.5, droop=0.2)
    fuselage(k, s, "skin", "cc", split=-5)
    band(k, s, -2.6, 3.0, 16, 30, "window")
    cockpit(k, s, L, nose=0.2)
    zw = zc + R * K * 0.8
    wing(k, 1.6, 2.4, 6.4, 1.2, -0.4, zw, "skin", b0=0.2, th=0.7)
    for sgn in (-1, 1):
        k.blob(1.0, sgn * 6.5, zw + 0.3, 0.9, 0.12, 0.6, "cc")  # winglet tips
        k.rod((-3.4, sgn * 1.6, zc + 1.8), (-2.0, sgn * 1.6, zc + 1.8), 0.95, "cc", n=12)
        k.rod((-3.5, sgn * 1.6, zc + 1.8), (-1.9, sgn * 1.6, zc + 1.8), 0.72, "dark", n=12)
        k.box(-3.2, -2.2, min(sgn * 0.5, sgn * 0.9), max(sgn * 0.5, sgn * 0.9), zc + 0.6, zc + 1.6, "skin")
        fin(k, -4.8, 1.4, 3.2, 1.0, -0.5, zc + 1.2, "cc", b=sgn * 2.4, th=0.08)
    wing(k, -4.6, 1.2, 2.5, 1.0, -0.2, zc + 1.2, "skin", th=0.35)
    k.box(-1.0, 1.2, -1.0, 1.0, zc - R * K * 0.9, zc - R * K * 0.4, "belly")
    gear_set(k, s, 4.2, 0.2, 0.9, twin=False)


def flywing(k):
    """Small flying-wing air taxi: a swept wing with a central pod, two ducted fans on top, winglets."""
    zb = GEAR_Z + 1.4
    secs = [(3.6, 6.4, 0.0, zb, 2.6), (2.8, 5.0, 1.6, zb + 0.1, 2.0), (0.6, 2.4, 3.6, zb + 0.5, 0.8),
            (-1.8, 1.2, 6.2, zb + 1.1, 0.4)]
    for sgn in (1, -1):
        tube(k, [[(p[0], sgn * p[1], p[2]) for p in section(*sec, ridge=0.32)] for sec in secs[:2]], "cc")
        tube(k, [[(p[0], sgn * p[1], p[2]) for p in section(*sec, ridge=0.32)] for sec in secs[1:]], "skin")
        fin(k, -1.4, 1.1, 2.4, 0.7, -0.6, zb + 1.3, "cc", b=sgn * 6.2, th=0.08)
        k.rod((-2.2, sgn * 1.1, zb + 3.2), (-0.8, sgn * 1.1, zb + 3.2), 0.62, "skin", n=10)
        k.rod((-2.3, sgn * 1.1, zb + 3.2), (-0.7, sgn * 1.1, zb + 3.2), 0.45, "dark", n=10)
    k.blob(1.6, 0, zb + 2.6, 1.6, 0.75, 1.3, "cockpit")
    for b, a in ((0.0, 2.6), (-1.4, -0.4), (1.4, -0.4)):
        gear(k, a, b, zb + 0.4, 0.22, twin=False)


def canard(k):
    """Canard jet: forward-swept main wing aft, small foreplanes, engines on the tail, V-tail."""
    L, R = 14.0, 0.7
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.2, tail=0.25, rise=0.5, droop=0.2, nose_r=0.06)
    fuselage(k, s, "cc", "skin", split=5)
    band(k, s, -2.8, 4.2, 18, 28, "window")
    cockpit(k, s, L, nose=0.2)
    zw = zc - R * K * 0.5
    wing(k, -0.6, 2.8, 6.2, 1.2, 1.4, zw, "skin", b0=0.3, dihedral=1.0, th=0.8)
    wing(k, 4.8, 1.2, 2.0, 0.6, -0.4, zc, "cc", b0=0.3, th=0.35)
    for sgn in (-1, 1):
        nacelle(k, -3.0, 2.4, 0.46, sgn * 1.4, zc + 1.4, "skin")
        fin(k, -5.4, 1.8, 4.0, 1.0, -1.2, zc + 1.0, "cc", b=sgn * 0.3, cant=sgn * 1.8, th=0.08)
    gear_set(k, s, 5.0, -1.0, 1.2, twin=False)


def boxwing(k):
    """Box-wing airliner: a low forward wing joined at the tips to a high aft wing on the fin."""
    L, R = 16.0, 0.85
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.15, tail=0.3, rise=0.7)
    fuselage(k, s, "skin", "cc", split=-15)
    band(k, s, -4.6, 5.2, 18, 26, "window")
    cockpit(k, s, L)
    zw = zc - R * K * 0.55
    zt = zc + 7.6
    wing(k, 3.2, 3.2, 7.0, 1.4, -4.6, zw, "skin", b0=0.4, dihedral=2.0, th=0.9)
    fin(k, -4.8, 3.6, 7.2, 2.0, -1.4, zc + 0.8, "cc", th=0.16)
    wing(k, -6.0, 2.0, 7.0, 1.4, 4.2, zt - 0.3, "skin", b0=0.0, dihedral=-0.6, th=0.6)
    for sgn in (-1, 1):
        fin(k, -1.6, 1.4, zt - zw - 2.3, 1.4, -0.2, zw + 2.0, "cc", b=sgn * 7.3, th=0.1)
        nacelle(k, -3.4, 2.6, 0.55, sgn * 1.5, zc + 1.6, "cc")
    gear_set(k, s, 6.0, 0.0, 1.3)


def truss(k):
    """Truss-braced airliner: very long thin high wing on struts, engines under the wing, T-tail."""
    L, R = 15.5, 0.8
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.15, tail=0.3, rise=0.7)
    fuselage(k, s, "cc", "skin", split=10)
    band(k, s, -4.0, 5.0, 18, 26, "window")
    cockpit(k, s, L)
    zw = zc + R * K * 0.85
    wing(k, 1.8, 2.4, 10.4, 0.8, -1.8, zw, "skin", b0=0.2, dihedral=-0.4, th=0.6)
    for sgn in (-1, 1):
        k.rod((0.6, sgn * 0.7, zc - 0.8), (0.4, sgn * 5.6, zw - 0.2), 0.12, "skin", n=4)
        nacelle(k, 2.6, 2.6, 0.55, sgn * 2.8, zw - 1.6, "skin", pylon=(zw + 0.2, "wing_dark"))
        k.rod((0.6, sgn * 2.8, zw - 1.6), (1.4, sgn * 2.8, zw - 1.6), 0.57, "cc", n=8)
    fin(k, -5.4, 2.8, 6.6, 1.8, -2.0, zc + 1.0, "cc")
    wing(k, -7.2, 1.6, 3.0, 0.9, -0.6, zc + 7.4, "skin", th=0.4)
    for sgn in (-1, 1):
        k.blob(0.5, sgn * 0.7, zc - R * K * 0.6, 1.4, 0.32, 0.8, "skin")
    gear_set(k, s, 5.8, 0.5, 0.9)


def eprop(k):
    """Electric commuter: blended fuselage, straight wing with six distributed props, T-tail."""
    L, R = 10.5, 0.72
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.22, tail=0.3, rise=0.6, droop=0.25)
    fuselage(k, s, "skin", "cc", split=0)
    band(k, s, -2.0, 2.6, 18, 30, "window")
    cockpit(k, s, L, nose=0.22)
    zw = zc + R * K * 0.7
    wing(k, 1.4, 2.0, 6.6, 1.2, -0.3, zw, "skin", b0=0.2, th=0.6)
    for b in (1.6, 3.3, 5.0):
        for sgn in (-1, 1):
            nacelle(k, 2.0 - b * 0.04, 1.2, 0.26, sgn * b, zw + 0.2, "cc", "cc", cone=False)
            propeller(k, 2.1, sgn * b, zw + 0.2, 0.7, 5, spin=b)
    fin(k, -3.6, 2.2, 5.2, 1.4, -1.6, zc + 0.8, "cc")
    wing(k, -5.6, 1.2, 2.4, 0.8, -0.4, zc + 5.9, "skin", th=0.35)
    gear_set(k, s, 3.6, 0.4, 0.9, twin=False)


# --- toyland --------------------------------------------------------------------------------

def toy_wheels(k, a, b, z_top, r=0.42, mat="toy_red"):
    axle = GEAR_Z + r * K
    k.rod((a, b, z_top), (a, b, axle), 0.08, "toy_white", n=4)
    k.rod((a, b - 0.16, axle), (a, b + 0.16, axle), r, "tyre", n=10)
    k.rod((a, b - 0.18, axle), (a, b + 0.18, axle), r * 0.45, mat, n=8)


def toybiplane(k):
    """Toy biplane: fat round body, two yellow wings with struts, a big red propeller."""
    L, R = 8.0, 0.8
    zc = GEAR_Z + 1.6 + R * K
    s = stations(L, R, zc, nose=0.2, tail=0.4, rise=0.4, droop=0.0, nose_r=0.55)
    fuselage(k, s, "cc")
    band(k, s, -1.4, 1.6, 30, 50, "toy_white")
    k.blob(0.4, 0, zc + R * K * 0.9, 0.5, 0.45, 1.0, "toy_blue")  # pilot's helmet
    k.cyl(-0.2, 0, 0.65, zc + R * K * 0.7, zc + R * K * 1.0, "toy_white", n=10)
    zl, zu = zc - R * K * 0.6, zc + R * K * 1.3
    for z in (zl, zu):
        wing(k, 1.8, 1.8, 4.2, 1.6, 0.0, z, "toy_yellow", th=0.6, tip_th=0.5)
    for sgn in (-1, 1):
        for a in (1.6, 0.4):
            k.rod((a, sgn * 3.2, zl + 0.4), (a, sgn * 3.2, zu), 0.08, "toy_white", n=4)
    k.blob(L / 2, 0, zc, 0.3, 0.3, 0.8, "toy_red")
    propeller(k, L / 2 + 0.2, 0, zc, 1.4, 2, spin=0.4, mat="toy_red", hub="toy_red")
    wing(k, -3.0, 1.2, 1.8, 1.0, 0.0, zc + 0.6, "toy_yellow", th=0.4)
    fin(k, -2.8, 1.4, 3.2, 1.1, -0.4, zc + 0.8, "toy_red", th=0.12)
    for sgn in (-1, 1):
        toy_wheels(k, 1.4, sgn * 1.1, zl)
    k.blob(-3.6, 0, GEAR_Z + 0.4, 0.2, 0.2, 0.5, "tyre")


def toyhiwing(k):
    """Toy twin-prop with a chubby body, a high mint wing and two round-nosed engines."""
    L, R = 10.0, 0.95
    zc = GEAR_Z + 1.0 + R * K
    s = stations(L, R, zc, nose=0.25, tail=0.38, rise=0.5, droop=0.1, nose_r=0.4)
    fuselage(k, s, "cc", "toy_white", split=-10)
    for a in bk.frange(-2.0, 2.6, 1.15):  # round windows
        r, z = interp(s, a)
        for sgn in (-1, 1):
            k.rod((a, sgn * (r - 0.1), z + 0.5), (a, sgn * (r + 0.07), z + 0.5), 0.3, "toy_white", n=10)
            k.rod((a, sgn * (r - 0.05), z + 0.5), (a, sgn * (r + 0.1), z + 0.5), 0.2, "toy_blue", n=8)
    cockpit(k, s, L, nose=0.25, t0=0.1, t1=0.5, th0=30, th1=150, mat="toy_blue")
    zw = zc + R * K * 0.9
    wing(k, 1.4, 2.2, 5.6, 1.8, 0.0, zw, "toy_mint", th=0.9, tip_th=0.7)
    for sgn in (-1, 1):
        nacelle(k, 2.4, 2.2, 0.48, sgn * 2.4, zw - 0.3, "toy_yellow", "toy_red", cone=False)
        k.blob(2.5, sgn * 2.4, zw - 0.3, 0.28, 0.28, 0.7, "toy_red")
        propeller(k, 2.6, sgn * 2.4, zw - 0.3, 1.1, 3, spin=sgn, mat="toy_red", hub="toy_red")
        toy_wheels(k, 0.2, sgn * 1.1, zc - R * K * 0.6)
    fin(k, -4.0, 2.0, 4.0, 1.4, -0.8, zc + 1.0, "toy_yellow", th=0.14)
    wing(k, -4.2, 1.3, 2.2, 1.0, 0.0, zc + 1.4, "toy_mint", th=0.45)
    toy_wheels(k, 3.6, 0, zc - R * K * 0.7, 0.3)


def toyjet(k):
    """Toy jet: round nose with a big windscreen, two fat engines on the back, stubby swept wings."""
    L, R = 11.0, 0.95
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.22, tail=0.3, rise=0.5, droop=0.1, nose_r=0.35)
    fuselage(k, s, "cc", "toy_white", split=0)
    cockpit(k, s, L, nose=0.22, t0=0.1, t1=0.6, th0=25, th1=155, mat="toy_blue")
    band(k, s, -3.2, 2.8, 10, 20, "toy_yellow")
    zw = zc - R * K * 0.5
    wing(k, 1.6, 2.6, 4.4, 1.6, -1.4, zw, "toy_white", b0=0.4, dihedral=1.0, th=0.9, tip_th=0.7)
    for sgn in (-1, 1):
        k.blob(-0.4 - 1.4, sgn * 4.7, zw + 1.0, 0.5, 0.3, 0.8, "toy_red")
        nacelle(k, -1.6, 2.8, 0.62, sgn * 0.9, zc + R * K + 0.6, "toy_purple", "toy_yellow", cone=False)
        toy_wheels(k, 0.0, sgn * 1.2, zw)
    fin(k, -3.6, 2.2, 4.0, 1.6, -1.0, zc + 1.0, "toy_yellow", th=0.16)
    wing(k, -4.0, 1.4, 2.4, 1.0, -0.4, zc + 1.0, "toy_white", th=0.45)
    toy_wheels(k, 3.6, 0, zc - R * K * 0.7, 0.32)


def toyjumbo(k):
    """Toy jumbo: a fat round body with rainbow tail stripes and four drum engines."""
    L, R = 16.0, 1.3
    zc = GEAR_Z + 0.9 + R * K
    s = stations(L, R, zc, nose=0.2, tail=0.3, rise=0.6, droop=0.1, nose_r=0.3)
    fuselage(k, s, "cc", "toy_white", split=-15)
    for a in bk.frange(-3.6, 4.6, 1.15):
        r, z = interp(s, a)
        for sgn in (-1, 1):
            k.rod((a, sgn * (r - 0.1), z + 1.0), (a, sgn * (r + 0.07), z + 1.0), 0.3, "toy_white", n=10)
            k.rod((a, sgn * (r - 0.05), z + 1.0), (a, sgn * (r + 0.1), z + 1.0), 0.2, "toy_blue", n=8)
    cockpit(k, s, L, nose=0.2, t0=0.2, t1=0.55, th0=25, th1=155, mat="toy_blue")
    zw = zc - R * K * 0.55
    wing(k, 2.0, 4.0, 7.2, 1.8, -3.4, zw, "toy_white", b0=0.6, dihedral=1.4, th=1.1, tip_th=0.8)
    cols = ["toy_red", "toy_yellow", "toy_green", "toy_blue"]
    for i, b in enumerate((2.8, 5.2)):
        for sgn in (-1, 1):
            nacelle(k, 2.0 - i * 1.4, 2.0, 0.6, sgn * b, zw - 1.4, cols[i * 2 + (sgn > 0)], "toy_white",
                    pylon=(zw + 0.2, "toy_white"), cone=False)
    stripes = ["toy_red", "toy_orange", "toy_yellow", "toy_green", "toy_blue", "toy_purple"]
    for i, m in enumerate(stripes):  # fin in rainbow layers
        h0 = zc + 1.0 + i * 1.3
        fin(k, -5.4 - i * 0.42, 3.4 - i * 0.28, 1.3, 3.4 - (i + 1) * 0.28, -0.42, h0, m, th=0.2)
    wing(k, -5.2, 2.0, 3.0, 1.2, -1.0, zc + 0.8, "toy_white", th=0.5)
    for sgn in (-1, 1):
        toy_wheels(k, 0.0, sgn * 1.5, zw, 0.42)
    toy_wheels(k, 5.6, 0, zc - R * K * 0.7, 0.34)


def toyrocket(k):
    """Toy rocket plane: striped needle body with a red cone, delta wings, three fins, a flame nozzle."""
    L, R = 14.0, 0.8
    zc = GEAR_Z + 1.4 + R * K
    s = stations(L, R, zc, nose=0.25, tail=0.1, rise=0.05, droop=0.0, nose_r=0.04)
    fuselage(k, s, "cc")
    for a in (-3.0, -0.6, 1.8):
        band(k, s, a, a + 0.7, -40, 220, "toy_white", out=1.03, steps=1)
    a1 = L / 2
    nose = [(a, r * 1.02, z) for a, r, z in s if a > a1 - 0.25 * L * 0.6]
    fuselage(k, nose, "toy_red")
    cockpit(k, s, L, nose=0.25, t0=0.0, t1=0.25, th0=30, th1=150, mat="toy_blue")
    zw = zc - R * K * 0.3
    for sgn in (1, -1):
        secs = [(1.6, 7.0, 0.3, zw, 0.8), (-4.2, 2.0, 4.0, zw + 0.3, 0.4)]
        tube(k, [[(p[0], sgn * p[1], p[2]) for p in section(*sec, ridge=0.5)] for sec in secs], "toy_yellow")
        k.blob(-5.2, sgn * 4.0, zw + 0.4, 0.9, 0.3, 0.6, "toy_red")
    fin(k, -4.4, 2.6, 4.4, 1.2, -1.4, zc + 1.0, "toy_yellow", th=0.14)
    k.rod((-L / 2 - 0.6, 0, zc), (-L / 2 + 0.2, 0, zc), R * 0.5, "toy_purple", n=10)
    k.rod((-L / 2 - 1.6, 0, zc), (-L / 2 - 0.6, 0, zc), R * 0.42, "fire", n=8)
    for b, a in ((0, 4.0), (-1.6, -2.4), (1.6, -2.4)):
        toy_wheels(k, a, b, zw, 0.36)


def toyheli(k):
    """Toy helicopter: round bubble cabin, striped tail boom with a ball end, skids with round feet."""
    cab = [(-1.6, 0.4, 2.8), (-1.0, 1.0, 2.8), (0.4, 1.15, 2.8), (1.4, 0.95, 2.8), (2.1, 0.5, 2.8),
           (2.4, 0.15, 2.8)]
    fuselage(k, cab, "cc", "toy_white", split=-20)
    cockpit(k, cab, 4.0, nose=0.45, t0=0.0, t1=0.95, th0=-5, th1=185, mat="toy_blue")
    mast(k, 4.8)
    boom = [(-5.6, 0.2, 4.0), (-1.4, 0.34, 3.4)]
    fuselage(k, boom, "toy_yellow")
    for a in (-4.6, -3.4, -2.2):
        band(k, boom, a, a + 0.5, 0, 360, "toy_red", out=1.08, steps=1)
    k.blob(-5.7, 0, 4.1, 0.45, 0.45, 1.1, "toy_red")
    k.rod((-5.7, 0.4, 4.6), (-5.7, 0.5, 4.6), 0.7, "toy_blue", n=10)
    fin(k, -5.0, 1.0, 2.4, 0.7, -0.4, 4.2, "toy_purple", th=0.08)
    for sgn in (-1, 1):
        k.rod((-1.6, sgn * 1.1, GEAR_Z + 0.2), (1.8, sgn * 1.1, GEAR_Z + 0.2), 0.12, "toy_red", n=6)
        for a in (-1.0, 1.0):
            k.rod((a, sgn * 1.1, GEAR_Z + 0.2), (a, sgn * 0.6, 1.0), 0.08, "toy_white", n=4)
        k.blob(1.9, sgn * 1.1, GEAR_Z + 0.3, 0.22, 0.22, 0.5, "toy_yellow")


# name: (kind, builder, first sprite)
AIRCRAFT = {
    "liner4hi": ("aircraft", liner4hi), "jumbo": ("aircraft", jumbo), "concorde": ("aircraft", concorde),
    "prop4tri": ("aircraft", prop4tri), "trimotor": ("aircraft", trimotor), "jet_t": ("aircraft", jet_t),
    "trijet": ("aircraft", trijet), "twinjet": ("aircraft", twinjet), "prop4": ("aircraft", prop4),
    "heli": ("aircraft", heli), "hyperdart": ("aircraft", hyperdart), "bwb": ("aircraft", bwb),
    "hypersonic": ("aircraft", hypersonic), "zshuttle": ("aircraft", zshuttle), "flywing": ("aircraft", flywing),
    "canard": ("aircraft", canard), "boxwing": ("aircraft", boxwing), "truss": ("aircraft", truss),
    "eprop": ("aircraft", eprop), "heli2": ("aircraft", heli2),
    "toybiplane": ("aircraft", toybiplane), "toyhiwing": ("aircraft", toyhiwing), "toyjet": ("aircraft", toyjet),
    "toyjumbo": ("aircraft", toyjumbo), "toyrocket": ("aircraft", toyrocket), "toyheli": ("aircraft", toyheli),
}
for _f in (0, 1, 2, 3, "disc", "hub"):
    AIRCRAFT[f"rotor{'_' if isinstance(_f, str) else ''}{_f}"] = ("rotor", rotor_model(_f))
    AIRCRAFT[f"toyrotor{'_' if isinstance(_f, str) else ''}{_f}"] = ("rotor", rotor_model(_f, toy=True))
