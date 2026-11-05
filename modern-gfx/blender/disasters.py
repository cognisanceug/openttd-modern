"""Disaster vehicles and the road-works bulldozer for render_vehicles.py.

Same conventions as the aircraft: local +a is the nose, b the right side, z height units up from the
vehicle's z_pos; one x/y unit is K = 2.449 z units. Disaster vehicles have the bounds origin (-1, -1)
of the aircraft (DisasterVehicle::UpdateDeltaXY), so they share the aircraft anchoring.

The game draws one sprite per disaster vehicle in every direction (_disaster_images in
disaster_vehicle.cpp), so each model is rendered only in the direction it flies in:
  blimp          3905  zeppelin, flies SE        blimp_crashing 3906  falling, nose down
  blimp_crashed  3907  wreck on the runway      ufo / ufo_dark 3908-3909  small UFO, lights blinking
  sub_small      3910-3913  NE, SE, SW, NW       sub_large      3914-3917  NE, SE, SW, NW
  f15 / f15_fire 3918-3919  combat jet, flies NE, firing   ufo_big 3920  large UFO (no direction)
  skyranger      3921  UFO destroyer, flies SW   ah64 / ah64_fire 3922-3923  combat helicopter, flies SW
The combat helicopter's rotor is the aircraft rotor 3902-3904 (aircraft.py), ROTOR_Z_OFFSET above
the body, so its mast top sits at aircraft.HM. Shadows are the same sprites drawn with the
transparent palette on the ground below (DisasterVehicle::UpdatePosition), like the aircraft.

  bulldozer      1416-1419  road works (EV_BULLDOZER), NE, SE, SW, NW; an effect vehicle: bounds origin 0
"""

import math
import random

import build_kit as bk
import style as st
from aircraft import K, HM, GEAR_Z, tube, stations, fuselage, cockpit, band, wing, fin, ring

W, O, F = st.WALL, st.OBJECT, st.FLAT
bk.PALETTE.update({
    "zep_skin": ((214, 216, 214), W), "zep_band": ((176, 180, 182), W), "zep_rib": ((120, 124, 128), W),
    "zep_gondola": ((120, 126, 134), W), "soot": ((54, 52, 52), O), "scorch": ((70, 64, 58), O),
    "ember": ((255, 132, 52), F), "flame": ((255, 196, 84), F), "flame_core": ((255, 244, 200), F),
    "ufo_hull": ((176, 184, 192), W), "ufo_rim": ((126, 134, 146), W), "ufo_dome": ((140, 214, 226), F),
    "ufo_dome_dim": ((84, 132, 146), F), "ufo_light": ((255, 234, 140), F), "ufo_light_off": ((112, 108, 92), W),
    "ufo_dark": ((84, 90, 100), W), "ufo_panel": ((112, 226, 150), F), "ufo_core": ((236, 84, 70), F),
    "jet_grey": ((150, 160, 172), W), "jet_dark": ((110, 118, 130), W), "canopy": ((60, 80, 104), W),
    "olive": ((106, 116, 86), W), "olive_dark": ((80, 88, 66), W), "pod": ((70, 74, 66), W),
    "xcom": ((118, 130, 152), W), "xcom_dark": ((84, 94, 112), W),
    "sub": ((70, 76, 86), W), "sub_deck": ((92, 98, 106), W), "foam": ((236, 244, 246), O),
    "dozer": ((236, 180, 54), W), "dozer_dark": ((60, 60, 64), W), "blade_steel": ((150, 150, 146), W),
})


def tilt(k, pitch, a0=0.0, z0=0.0):
    """Pitch every part nose down by pitch radians about (a0, z0), in true proportions."""
    c, s = math.cos(pitch), math.sin(pitch)
    for _, bm in k.parts:
        for v in bm.verts:
            a, z = v.co.x - a0, (v.co.z - z0) / K
            v.co.x, v.co.z = a0 + a * c + z * s, z0 + (-a * s + z * c) * K


# --- zeppelin --------------------------------------------------------------------------------------

ZL, ZR = 30.0, 3.3
ZC = 2.6 + ZR * K  # hull axis above the gondola


def zep_stations(squash=1.0):
    st_ = stations(ZL, ZR, ZC, nose=0.22, tail=0.4, rise=0.0, droop=0.0, tip=0.12, n=6, nose_r=0.12)
    return [(a, r, ZC + (zc - ZC) * squash) for a, r, zc in st_]


def zep_fins(k, mat="zep_skin"):
    a_le = -ZL / 2 + 6.0
    fin(k, a_le, 5.0, ZR * K * 0.6 + 3.5, 2.6, -2.6, ZC + ZR * K * 0.4, mat, th=0.18)
    fin(k, a_le, 5.0, -(ZR * K * 0.6 + 3.5), 2.6, -2.6, ZC - ZR * K * 0.4, mat, th=0.18)
    wing(k, a_le, 5.0, ZR * 0.6 + 2.2, 2.6, -2.6, ZC - 0.4, mat, b0=ZR * 0.5, th=0.5, tip_th=0.35)


def zep_hull(k, squash=1.0):
    st_ = zep_stations(squash)
    fuselage(k, st_, "zep_skin")
    for a in (-8.0, -2.5, 3.0, 8.5):  # gore seams
        tube(k, [ring(aa, _at(st_, aa)[0] * 1.015, _at(st_, aa)[1], 0, 360, 16)[:-1] for aa in (a - 0.25, a + 0.25)],
             "zep_band")
    return st_


def _at(st_, a):
    for (a0, r0, z0), (a1, r1, z1) in zip(st_, st_[1:]):
        if a0 <= a <= a1:
            t = (a - a0) / (a1 - a0) if a1 > a0 else 0
            return r0 + (r1 - r0) * t, z0 + (z1 - z0) * t
    return st_[-1][1], st_[-1][2]


def zep_gondola(k):
    """Control car under the front third, engine cars on struts either side."""
    g = [(5.0, 0.3, 1.6), (6.0, 0.75, 1.4), (9.0, 0.8, 1.4), (10.4, 0.55, 1.6), (11.0, 0.2, 1.9)]
    fuselage(k, g, "zep_gondola")
    band(k, g, 6.2, 10.4, 5, 40, "window")
    for a, b in ((-3.5, 3.6), (-3.5, -3.6), (2.5, 3.4), (2.5, -3.4)):
        k.rod((a - 1.4, b, ZC - 3.2), (a + 1.0, b, ZC - 3.2), 0.42, "zep_gondola", n=8)
        k.rod((a, b * 0.6, ZC - 1.8), (a, b, ZC - 3.2), 0.07, "zep_rib", n=4)
        k.rod((a - 1.6, b, ZC - 3.2), (a - 1.4, b, ZC - 3.2), 0.9, "blade", n=10)  # propeller disc


def blimp(k):
    """Rigid airship: long silver hull with gore seams, cruciform tail, control car and engine cars."""
    zep_hull(k)
    zep_fins(k)
    zep_gondola(k)


def blimp_crashing(k):
    """The airship falling nose down, its tail on fire."""
    zep_hull(k)
    zep_fins(k)
    zep_gondola(k)
    rng = random.Random(7)
    for i in range(9):
        a = -ZL / 2 + 3.0 + rng.uniform(0, 7)
        b = rng.uniform(-1.6, 1.6)
        r = rng.uniform(0.9, 1.6)
        k.blob(a, b, ZC + ZR * K * 0.75 + rng.uniform(0, 2.5), r, r, r * K, "flame" if i % 3 else "ember")
    for i in range(4):
        k.blob(-ZL / 2 + 4 + i * 1.5, 0.3, ZC + ZR * K + 2.5 + i * 0.8, 0.7, 0.7, 1.7, "flame_core")
    tilt(k, math.radians(16), 0.0, ZC)


def blimp_crashed(k):
    """Wreck on the ground: the bare girder frame of the burnt-out tail, the front still clad, embers."""
    squash = 0.62
    zc = ZR * K * squash
    st_ = [(a, r, zc) for a, r, _ in zep_stations()]

    def flat_ring(a, r, f=1.0):  # cross-section squashed onto the ground
        return [(a, r * f * math.cos(t), r * K * squash * (1 + f * math.sin(t))) for t in
                (i * math.tau / 12 for i in range(12))]
    front = [(-0.4, _at(st_, -0.4)[0])] + [(a, r) for a, r, _ in st_ if a >= 1.0]
    tube(k, [flat_ring(a, r) for a, r in front], "zep_skin")
    for a in (3.0, 8.5):
        tube(k, [flat_ring(aa, _at(st_, aa)[0], 1.015) for aa in (a - 0.25, a + 0.25)], "zep_band")
    rng = random.Random(11)
    # Rings of the frame aft of the cladding, sagging more towards the tail, and the keel girders.
    ribs = [a for a in bk.frange(-ZL / 2 + 1.5, 1.0, 2.4)]
    for j, a in enumerate(ribs):
        r = _at(st_, a)[0]
        sag = squash * (1 - 0.45 * (1 - j / len(ribs)))
        pts = [(a, r * math.cos(t), r * K * sag * (1 + math.sin(t))) for t in
               (i * math.tau / 10 for i in range(11))]
        for p, q in zip(pts, pts[1:]):
            if rng.random() < 0.82 and max(p[2], q[2]) > -0.2:
                k.rod((p[0], p[1], max(p[2], 0.1)), (q[0], q[1], max(q[2], 0.1)), 0.09, "zep_rib", n=4)
    for t in (i * math.tau / 8 for i in range(8)):
        if math.sin(t) < -0.5:
            continue
        p0 = [(a, _at(st_, a)[0]) for a in (ribs[0], ribs[-1])]
        k.rod((p0[0][0], p0[0][1] * math.cos(t), max(0.1, p0[0][1] * K * squash * 0.55 * (1 + math.sin(t)))),
              (p0[1][0], p0[1][1] * math.cos(t), max(0.1, p0[1][1] * K * squash * (1 + math.sin(t)))),
              0.08, "zep_rib", n=4)
    # Scorched ground, fallen fin, debris and smouldering embers.
    k.blob(-6.0, 0.0, 0.0, 11.0, 4.6, 0.12, "scorch", subdiv=2)
    fin(k, -ZL / 2 + 1.0, 4.4, 4.0, 2.2, -2.0, 0.2, "zep_band", b=2.6, cant=2.4, th=0.15)
    for i in range(16):
        a, b = rng.uniform(-14, 2), rng.uniform(-4.0, 4.0)
        k.box(a - 0.3, a + 0.3, b - 0.25, b + 0.25, 0.1, 0.6, "soot" if i % 3 else "zep_rib")
    for i in range(7):
        a, b = rng.uniform(-12, -1), rng.uniform(-2.0, 2.0)
        k.blob(a, b, 0.6, 0.45, 0.45, 1.0, "ember" if i % 2 else "flame")
    k.box(5.0, 10.6, -0.9, 0.9, 0.1, 2.0, "zep_gondola")  # control car, flattened under the bow
    k.box(6.0, 10.2, -0.95, 0.95, 1.0, 1.6, "window")


# --- UFOs --------------------------------------------------------------------------------------------

def saucer(k, R, h, hull, rim, dome, light, n=24, lights=10):
    """Lens-shaped saucer centred on the origin: rim at z 0, a dome on top and lights round the rim."""
    k.lathe(0, 0, [(0.05, -h * 0.55), (R * 0.45, -h * 0.5), (R * 0.85, -h * 0.22), (R, 0.0)], rim, n=n)
    k.lathe(0, 0, [(R, 0.0), (R * 0.9, h * 0.22), (R * 0.6, h * 0.5), (R * 0.38, h * 0.62), (0.05, h * 0.66)], hull,
            n=n)
    k.lathe(0, 0, [(R * 0.4, h * 0.6), (R * 0.38, h * 1.05), (R * 0.26, h * 1.45), (0.05, h * 1.62)], dome, n=16)
    for i in range(lights):
        t = i * math.tau / lights + 0.2
        k.blob(R * 0.97 * math.cos(t), R * 0.97 * math.sin(t), 0.05, 0.24, 0.24, 0.5, light)


def ufo_model(dark):
    def build(k):
        saucer(k, 3.0, 2.6, "ufo_hull", "ufo_rim", "ufo_dome_dim" if dark else "ufo_dome",
               "ufo_light_off" if dark else "ufo_light")
        k.cyl(0, 0, 0.7, -1.6, -1.35, "ufo_light_off" if dark else "ufo_light", n=10)  # beam emitter
    return build


def ufo_big(k):
    """Harvester: a big dark saucer with glowing green panels, a red core on top and emitters below."""
    R, h = 6.6, 4.4
    k.lathe(0, 0, [(0.05, -h * 0.5), (R * 0.4, -h * 0.48), (R * 0.82, -h * 0.25), (R, -0.2), (R, 0.3)], "ufo_dark",
            n=32)
    k.lathe(0, 0, [(R, 0.3), (R * 0.88, h * 0.3), (R * 0.55, h * 0.55), (R * 0.42, h * 0.6), (0.05, h * 0.62)],
            "ufo_rim", n=32)
    for i in range(8):  # glowing panels between ribs on the upper hull
        t0 = i * math.tau / 8 + 0.08
        t1 = t0 + math.tau / 8 - 0.16
        rings = []
        for j in range(5):
            t = t0 + (t1 - t0) * j / 4
            c, s = math.cos(t), math.sin(t)
            rings.append([(r * f * c, r * f * s, z) for f, (r, z) in
                          ((1.03, (R * 0.92, h * 0.27)), (1.03, (R * 0.6, h * 0.53)), (0.97, (R * 0.6, h * 0.53)),
                           (0.97, (R * 0.92, h * 0.27)))])
        tube(k, rings, "ufo_panel")
    k.lathe(0, 0, [(R * 0.4, h * 0.58), (R * 0.36, h * 0.85), (R * 0.22, h * 1.08), (0.05, h * 1.15)], "ufo_core",
            n=16)
    k.cyl(0, 0, R * 1.01, -0.2, 0.3, "ufo_rim", n=32)
    for i in range(12):
        t = i * math.tau / 12
        k.blob(R * 1.01 * math.cos(t), R * 1.01 * math.sin(t), 0.05, 0.3, 0.3, 0.6, "ufo_panel")
    for i in range(3):
        t = i * math.tau / 3 + 0.5
        k.cyl(R * 0.45 * math.cos(t), R * 0.45 * math.sin(t), 0.8, -h * 0.5, -h * 0.38, "ufo_core", n=10)


# --- combat aircraft ---------------------------------------------------------------------------------

def f15_model(firing):
    def build(k):
        """Twin-engined fighter: grey, twin fins, wide intakes, bubble canopy."""
        L, R = 12.0, 0.55
        zc = 1.4
        s = stations(L, R, zc, nose=0.3, tail=0.06, rise=0.0, droop=0.08, tip=0.8, nose_r=0.05)
        fuselage(k, s, "jet_grey", "jet_dark", split=-10)
        cockpit(k, s, L, nose=0.3, t0=0.25, t1=0.9, th0=30, th1=150, mat="canopy")
        for sgn in (-1, 1):
            k.box(-5.6, 2.2, min(sgn * 0.55, sgn * 1.25), max(sgn * 0.55, sgn * 1.25), zc - 1.1, zc + 0.6, "jet_grey")
            k.box(1.6, 2.3, sgn * 0.6 - 0.35, sgn * 0.6 + 0.35, zc - 1.0, zc + 0.4, "intake")
            k.rod((-6.4, sgn * 0.85, zc - 0.3), (-5.6, sgn * 0.85, zc - 0.3), 0.42, "exhaust", n=8)
            fin(k, -4.0, 2.0, 3.6, 1.0, -1.2, zc + 0.6, "jet_grey", b=sgn * 0.95, cant=sgn * 0.35, th=0.1)
        wing(k, 1.6, 5.2, 4.6, 1.2, -3.2, zc - 0.2, "jet_grey", b0=1.0, th=0.35, tip_th=0.15)
        wing(k, -4.0, 2.0, 2.0, 0.9, -1.2, zc - 0.3, "jet_dark", b0=1.1, th=0.2, tip_th=0.12)
        for sgn in (-1, 1):  # wing-tip missiles
            k.rod((-1.2, sgn * 5.6, zc - 0.1), (1.6, sgn * 5.6, zc - 0.1), 0.12, "white", n=6)
        if firing:
            for sgn in (-1, 1):
                k.rod((-8.4, sgn * 0.85, zc - 0.3), (-6.4, sgn * 0.85, zc - 0.3), 0.32, "flame", n=8)
                k.rod((-7.4, sgn * 0.85, zc - 0.3), (-6.4, sgn * 0.85, zc - 0.3), 0.22, "flame_core", n=8)
            # A missile ahead under the left wing with its exhaust and the gun's muzzle flash.
            k.rod((5.0, 3.0, zc - 0.8), (8.0, 3.0, zc - 0.8), 0.13, "white", n=6)
            k.rod((3.4, 3.0, zc - 0.8), (5.0, 3.0, zc - 0.8), 0.22, "flame", n=6)
            k.blob(2.4, 3.0, zc - 0.8, 0.9, 0.5, 1.1, "flame", subdiv=1)
            k.blob(6.6, 0.6, zc + 0.1, 0.55, 0.45, 1.0, "flame_core")
    return build


def skyranger(k):
    """Troop transport hunting the big UFO: bulky fuselage, high swept wing with tip engines, twin tail."""
    L, R = 11.0, 0.95
    zc = 1.8
    s = stations(L, R, zc, nose=0.24, tail=0.3, rise=0.4, droop=0.12, tip=0.4, nose_r=0.15)
    fuselage(k, s, "xcom", "xcom_dark", split=-20)
    cockpit(k, s, L, nose=0.24, t0=0.2, t1=0.75, th0=20, th1=160, mat="canopy")
    zw = zc + R * K * 0.7
    wing(k, 1.8, 4.2, 4.6, 1.6, -2.6, zw, "xcom", b0=0.6, dihedral=-0.6, th=0.45, tip_th=0.25)
    for sgn in (-1, 1):
        k.rod((-2.6, sgn * 4.6, zw - 0.6), (0.6, sgn * 4.6, zw - 0.6), 0.5, "xcom_dark", n=8)
        k.rod((-3.2, sgn * 4.6, zw - 0.6), (-2.6, sgn * 4.6, zw - 0.6), 0.3, "exhaust", n=6)
        fin(k, -3.6, 1.8, 3.4, 1.0, -1.0, zc + 0.9, "xcom", b=sgn * 0.8, cant=sgn * 0.6, th=0.12)
    wing(k, -3.2, 1.6, 2.4, 0.9, -0.8, zc + 1.0, "xcom_dark", b0=0.5, th=0.18)


def ah64_model(firing):
    def build(k):
        """Attack helicopter: slim olive body, stepped tandem canopy, stub wings with pods, chin gun."""
        body = [(-2.4, 0.4, 2.6), (-1.4, 0.85, 2.4), (0.4, 0.9, 2.3), (1.6, 0.7, 2.0), (2.6, 0.38, 1.6),
                (3.0, 0.12, 1.4)]
        fuselage(k, body, "olive", "olive_dark", split=-20)
        cockpit(k, body, 5.4, nose=0.5, t0=0.1, t1=0.9, th0=25, th1=155, mat="canopy")
        k.box(-1.0, 0.4, -0.62, 0.62, 4.2, 5.0, "olive")  # engine bay
        for sgn in (-1, 1):
            k.rod((-1.6, sgn * 0.85, 4.5), (0.4, sgn * 0.85, 4.5), 0.34, "olive_dark", n=8)
        k.cyl(0, 0, 0.18, 4.8, HM, "hub", n=6)
        boom = [(-7.2, 0.14, 4.2), (-2.2, 0.34, 3.2)]
        fuselage(k, boom, "olive")
        fin(k, -6.8, 1.2, 3.4, 0.8, -0.6, 4.0, "olive", th=0.08)
        wing(k, -6.6, 0.8, 1.4, 0.6, 0.0, 4.6, "olive_dark", th=0.18)
        k.rod((-6.9, 0.2, 6.6), (-6.9, 0.28, 6.6), 0.75, "blade", n=10)  # tail rotor
        wing(k, 0.2, 1.1, 1.8, 0.9, -0.1, 2.2, "olive_dark", b0=0.8, th=0.28)
        for sgn in (-1, 1):
            k.rod((-0.9, sgn * 1.9, 1.5), (0.9, sgn * 1.9, 1.5), 0.32, "pod", n=8)  # rocket pods
            k.rod((-0.6, sgn * 2.55, 1.6), (0.7, sgn * 2.55, 1.6), 0.15, "pod", n=6)
            k.rod((-0.4, sgn * 0.95, GEAR_Z + 0.4), (-0.2, sgn * 0.95, 1.2), 0.07, "steel_dark", n=4)
            k.rod((-0.3, sgn * 0.95 - 0.1, GEAR_Z + 0.4), (-0.3, sgn * 0.95 + 0.1, GEAR_Z + 0.4), 0.3, "tyre", n=8)
        k.rod((2.0, 0, 0.9), (3.2, 0, 0.7), 0.07, "dark", n=4)  # chin gun
        k.rod((-6.8, 0, 3.0), (-6.8, 0, GEAR_Z + 0.5), 0.05, "steel_dark", n=4)
        if firing:
            k.blob(3.5, 0, 0.7, 0.5, 0.4, 0.9, "flame_core")
            for sgn in (-1, 1):
                k.rod((1.2, sgn * 1.9, 1.5), (4.2, sgn * 1.9, 1.3), 0.1, "white", n=4)
                k.rod((0.9, sgn * 1.9, 1.5), (1.6, sgn * 1.9, 1.5), 0.25, "flame", n=6)
                k.blob(-1.6, sgn * 1.9, 1.5, 0.8, 0.45, 1.0, "flame", subdiv=1)
    return build


# --- submarines -------------------------------------------------------------------------------------

def sub_model(L, B, sail_h, large):
    def build(k):
        """Surfaced submarine at sea level (z 0): a low dark hull awash, the sail, bow wave and wake."""
        import render_vehicles as rv
        rv.loft(k, rv.hull_rings(L, B, -0.1, 0.9, bow=0.3, stern=0.4, point=0.06, flare=0.9), "sub")
        rv.loft(k, [[(a, b, 0.9) for a, b in rv.plan(L * 0.8, B * 0.32, 0.25, 0.3, 0.2)],
                    [(a, b, 1.2) for a, b in rv.plan(L * 0.8, B * 0.32, 0.25, 0.3, 0.2)]], "sub_deck")
        sa = L * 0.12
        sail = [(a + sa, b) for a, b in rv.plan(L * (0.2 if large else 0.18), B * 0.36, 0.45, 0.25, 0.25, n=5)]
        rv.loft(k, [[(a, b, 0.9) for a, b in sail], [(a, b, sail_h) for a, b in sail]], "sub")
        if large:
            wing(k, sa + 0.6, 0.9, 1.4, 0.6, -0.2, sail_h - 1.4, "sub", b0=0.4, th=0.15)
            k.box(sa - L * 0.42, sa - L * 0.08, -0.5, 0.5, 1.2, 1.7, "sub")  # missile deck
            for a in bk.frange(sa - L * 0.4, sa - L * 0.1, 1.2):
                k.cyl(a, 0, 0.32, 1.7, 1.75, "sub_deck", n=8)
            for b in (-0.2, 0.25):
                k.rod((sa - 0.2, b, sail_h), (sa - 0.2, b, sail_h + 1.6), 0.06, "steel_dark", n=4)
            fin(k, -L / 2 + 0.6, 1.2, 1.8, 0.8, -0.4, 0.8, "sub", th=0.1)
        else:
            k.rod((sa - 0.1, 0, sail_h), (sa - 0.1, 0, sail_h + 1.8), 0.06, "steel_dark", n=4)
            k.rod((sa + 0.3, 0, sail_h), (sa + 0.3, 0, sail_h + 1.2), 0.08, "steel_dark", n=4)
            k.rod((sa + 2.6, 0, 1.2), (sa + 3.6, 0, 1.6), 0.08, "steel_dark", n=4)  # deck gun
            k.box(sa + 2.3, sa + 2.9, -0.25, 0.25, 1.2, 1.8, "sub_deck")
        rng = random.Random(5 if large else 3)
        for i in range(7):  # bow wave and wake on the water
            t = i / 6
            for sgn in (-1, 1):
                a = L / 2 - 0.6 - t * 1.6
                k.blob(a, sgn * (0.35 + t * B * 0.45), 0.15, 0.5 - 0.2 * t, 0.3, 0.3, "foam")
        for i in range(8):
            a = -L / 2 - 0.4 - i * 0.8
            k.blob(a, rng.uniform(-0.6, 0.6) * (1 + i * 0.2), 0.12, 0.55, 0.35 + 0.05 * i, 0.25, "foam")
    return build


# --- road works --------------------------------------------------------------------------------------

def bulldozer(k):
    """Small yellow crawler with a blade at the front, cab with roll-over frame and exhaust stack."""
    for sgn in (-1, 1):
        k.box(-1.9, 1.7, sgn * 1.05 - 0.35, sgn * 1.05 + 0.35, 0.0, 1.5, "dozer_dark")
    k.box(-1.6, 1.4, -0.75, 0.75, 1.0, 2.6, "dozer")
    k.box(0.3, 1.5, -0.6, 0.6, 2.6, 3.4, "dozer")  # engine hood
    k.box(-1.5, -0.1, -0.7, 0.7, 2.6, 5.4, "glass")
    k.box(-1.6, 0.0, -0.75, 0.75, 5.4, 5.9, "dozer")
    k.rod((0.9, 0.35, 3.4), (0.9, 0.35, 5.0), 0.1, "dark", n=4)
    k.box(2.2, 2.5, -1.6, 1.6, 0.0, 2.2, "blade_steel")
    for sgn in (-1, 1):
        k.rod((1.2, sgn * 1.0, 1.4), (2.2, sgn * 1.0, 1.0), 0.12, "dozer", n=4)
    k.box(-2.4, -1.9, -0.2, 0.2, 0.2, 1.4, "dozer_dark")  # ripper


# name: (kind, builder, directions rendered)
DISASTERS = {
    "blimp": ("disaster", blimp, [3]), "blimp_crashing": ("disaster", blimp_crashing, [3]),
    "blimp_crashed": ("disaster", blimp_crashed, [3]),
    "ufo": ("disaster", ufo_model(False), [0]), "ufo_dark": ("disaster", ufo_model(True), [0]),
    "sub_small": ("disaster", sub_model(11.0, 1.7, 4.2, False), [1, 3, 5, 7]),
    "sub_large": ("disaster", sub_model(17.0, 2.4, 5.4, True), [1, 3, 5, 7]),
    "f15": ("disaster", f15_model(False), [1]), "f15_fire": ("disaster", f15_model(True), [1]),
    "ufo_big": ("disaster", ufo_big, [0]), "skyranger": ("disaster", skyranger, [5]),
    "ah64": ("disaster", ah64_model(False), [5]), "ah64_fire": ("disaster", ah64_model(True), [5]),
    "bulldozer": ("effect", bulldozer, [1, 3, 5, 7]),
}
