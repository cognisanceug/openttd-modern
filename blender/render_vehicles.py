"""Render the original vehicles at zoom 1x, 2x and 4x, 8 directions each.

Run:  Blender -b --factory-startup -P render_vehicles.py -- <outdir> [--only tanker,cargo]

Each model is built once in vehicle units, bow towards local +a, beam along b,
z up from the vehicle's z_pos (the water line for ships): a and b are OpenTTD
x/y units, z height units, as in build_kit.py. It is turned to the 8 OpenTTD
directions (sprite = base + Direction: N, NE, E, SE, S, SW, W, NW) and centred
on the vehicle position.

Anchoring: the game draws a vehicle sprite at RemapCoords(pos + bounds.origin)
(Vehicle::bounds, set per direction in UpdateDeltaXY, e.g. ShipVehicle). The
renders put the vehicle position at the canvas point (W/2 - 1, ANCHOR) in 1x
pixels (times zoom), like the building canvases; meta.json stores the canvas
pixel of the sprite origin per direction and zoom, so the packer's offsets are
box - origin. Other vehicle types add their bounds and canvas to TYPES.

Outputs (in <outdir>/z<zoom>/): <name>_d<dir>.png colour, <name>_d<dir>_cc.png
recolour mask (white = company colour), plus <outdir>/meta.json.

  tanker     3669-3676  MPS / CS-Inc. oil tanker (image 1, 0xE55)
  cargo      3677-3684  Yate / Bakewell cargo ship (image 0, 0xE5D)
  ferry      3685-3692  MPS / FFP passenger ferry (image 2, 0xE65)
  hover      3693-3700  Bakewell 300 hovercraft (image 3, 0xE6D)
  toycargo   3677-3684  Mightymover / Powernaut cargo ship (toyland replaces 0xE5D-0xE6C)
  toyferry   3685-3692  Chugger-Chug / Shivershake ferry
  aircraft, helicopters and rotors: see aircraft.py (3741-3904)
  disaster vehicles and the road-works bulldozer: see disasters.py (3905-3923, 1416-1419)
"""

import json
import math
import os
import sys

import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_kit as bk  # noqa: E402
import style as st  # noqa: E402

W, O = st.WALL, st.OBJECT
bk.PALETTE.update({
    "hull_red": ((150, 62, 54), W), "hull_dark": ((58, 64, 74), W), "boot": ((44, 48, 54), W),
    "deck_green": ((104, 128, 104), W), "deck_rust": ((150, 92, 72), W), "deck_wood": ((198, 164, 116), W),
    "deck_grey": ((150, 154, 150), W), "hatch": ((86, 118, 140), W), "crane": ((236, 190, 70), W),
    "lifeboat": ((240, 130, 44), W), "rubber": ((50, 52, 58), W), "funnel_top": ((40, 42, 48), W),
    "rail": ((236, 236, 230), W),
    "toy_red": ((228, 76, 72), W), "toy_yellow": ((248, 206, 76), W), "toy_blue": ((76, 146, 226), W),
    "toy_green": ((98, 190, 112), W), "toy_pink": ((242, 152, 192), W), "toy_purple": ((156, 116, 212), W),
    "toy_orange": ((248, 152, 62), W), "toy_white": ((250, 246, 236), W), "toy_mint": ((150, 222, 196), W),
    "toy_wood": ((222, 182, 124), W),
})
CC = {"cc", "cc_light", "cc_flat"}

# Direction unit vectors in OpenTTD x/y (Direction enum order).
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]

# Per vehicle type: bounding box origin per direction (UpdateDeltaXY, x, y[, z]) and canvas (w, h, anchor row)
# in 1x px; dirs=1 for sprites the game draws in every direction (the helicopter rotor).
TYPES = {
    "ship": dict(origin=[(-3, -3), (-16, -3), (-3, -3), (-3, -16), (-3, -3), (-16, -3), (-3, -3), (-3, -16)],
                 canvas=(128, 96, 60)),
    "aircraft": dict(origin=[(-1, -1)] * 8, canvas=(128, 80, 46)),
    # The rotor vehicle is ROTOR_Z_OFFSET = 5 above the body; models are built in the body's frame.
    "rotor": dict(origin=[(-1, -1, 5)], canvas=(48, 40, 26), dirs=1),
    # Disaster vehicles share the aircraft bounds; the zeppelin and the big UFO need a larger canvas.
    "disaster": dict(origin=[(-1, -1)] * 8, canvas=(176, 128, 80)),
    # Effect vehicles (EffectVehicle::UpdateDeltaXY) are drawn at their position.
    "effect": dict(origin=[(0, 0)] * 8, canvas=(48, 40, 26)),
}


def remap(x, y, z=0):
    """OpenTTD RemapCoords at 1x."""
    return (y - x) * 2, x + y - z


# --- model helpers (local a/b/z) ---------------------------------------------------------------

def loft(k, rings, mat):
    """Closed solid through rings [[(a, b, z)]] of equal length, bottom to top.

    Rings are mirror-symmetric outlines (plan()), so the caps are strips across the beam: a cap
    whose height varies along a (sheer) stays planar per strip and never bulges over a deck.
    """
    n, m = len(rings[0]), len(rings)
    v = [p for r in rings for p in r]
    f = []
    for base in (0, (m - 1) * n):
        f += [(base + j, base + j + 1, base + n - 2 - j, base + n - 1 - j) for j in range(n // 2 - 1)]
    for j in range(len(rings) - 1):
        for i in range(n):
            a, b = j * n + i, j * n + (i + 1) % n
            f.append((a, b, b + n, a + n))
    k._solid(v, f, mat)


def plan(L, B, bow=0.3, stern=0.12, point=0.12, n=7):
    """Hull outline [(a, b)], length L centred on 0, beam B; bow is the share of L that tapers."""
    a_bow = L / 2 - bow * L
    side = []
    side.append((-L / 2, B / 2 * (1 - stern)))
    side.append((-L / 2 + stern * B / 2, B / 2))
    side.append((a_bow, B / 2))
    for i in range(1, n + 1):
        t = i / n
        side.append((a_bow + t * bow * L, B / 2 * max(point, math.sqrt(max(0.0, 1 - t ** 1.8)))))
    return side + [(a, -b) for a, b in reversed(side)]


def hull_rings(L, B, z0, z1, bow=0.3, stern=0.12, point=0.12, flare=0.88, sheer=0.0):
    """Two rings: the narrower hull at z0, the full outline at z1 (raised by sheer towards the bow)."""
    top = plan(L, B, bow, stern, point)
    bot = plan(L * 0.97, B * flare, bow * 1.05, stern, point)
    rings = []
    for pts, z in ((bot, z0), (top, z1)):
        rings.append([(a, b, z + (sheer * max(0.0, a / (L / 2)) ** 2 if z == z1 else 0)) for a, b in pts])
    return rings


def hull(k, L, B, h, mat, boot=0.7, deck="deck_grey", bow=0.3, stern=0.12, point=0.12, sheer=0.0, band=None,
         band_z=None):
    """Hull above the water line: dark boot topping, hull colour, optional band, deck plate."""
    boot_rings = hull_rings(L, B, 0, boot, bow, stern, point, 0.86, 0)
    loft(k, boot_rings, "boot")
    loft(k, [boot_rings[1], hull_rings(L, B, boot, h, bow, stern, point, 1.0, sheer)[1]], mat)
    if band:
        z0, z1 = band_z
        loft(k, [[(a * 1.002, b * 1.01, z0) for a, b in plan(L, B, bow, stern, point)],
                 [(a * 1.002, b * 1.01, z1) for a, b in plan(L, B, bow, stern, point)]], band)
    deck_plate(k, L, B, h, deck, bow, stern, point, sheer)


def deck_plate(k, L, B, h, mat, bow, stern, point, sheer, sa=0.97, sb=0.86, dz=0.15):
    """Deck inside the bulwark, following the sheer of the hull top."""
    rise = lambda a: sheer * max(0.0, a / (L / 2)) ** 2  # noqa: E731
    inner = [(a * sa, b * sb) for a, b in plan(L, B, bow, stern, point)]
    loft(k, [[(a, b, h - 0.3) for a, b in inner], [(a, b, h + dz + rise(a / sa)) for a, b in inner]], mat)


def block(k, a0, a1, b0, b1, z0, z1, mat):
    k.box(a0, a1, b0, b1, z0, z1, mat)


def windows(k, a0, a1, b0, b1, z0, z1, glass="glass", pitch=1.1, frame="frame", out=0.06):
    """Window band all round the block a0-a1 x b0-b1, with mullions."""
    k.box(a0 - out, a1 + out, b0 - out, b1 + out, z0, z1, glass)
    for a in bk.frange(a0 + 0.3, a1 - 0.3, pitch):
        for b in (b0 - out - 0.04, b1 + out - 0.04):
            k.box(a - 0.09, a + 0.09, b, b + 0.08, z0, z1, frame)
    for b in bk.frange(b0 + 0.3, b1 - 0.3, pitch):
        for a in (a0 - out - 0.04, a1 + out - 0.04):
            k.box(a, a + 0.08, b - 0.09, b + 0.09, z0, z1, frame)


def railing(k, pts, z, h=1.6, mat="rail"):
    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
        k.rod((a0, b0, z + h), (a1, b1, z + h), 0.05, mat, n=4)
        L = math.hypot(a1 - a0, b1 - b0)
        for t in bk.frange(0, 1, 1.2 / max(L, 0.1)):
            k.rod((bk.lerp(a0, a1, t), bk.lerp(b0, b1, t), z), (bk.lerp(a0, a1, t), bk.lerp(b0, b1, t), z + h), 0.04, mat, n=3)


def funnel(k, a, b, z0, z1, ra, rb, band="cc", top="funnel_top", body="white"):
    """Oval funnel, slightly raked: body, company band, black top."""
    h = z1 - z0
    k.cyl(a, b, ra, z0, z0 + h * 0.62, body, n=12)
    k.cyl(a, b, ra, z0 + h * 0.62, z0 + h * 0.88, band, n=12)
    k.cyl(a, b, ra, z0 + h * 0.88, z1, top, n=12)
    for part in k.parts[-3:]:
        for v in part[1].verts:  # oval: squeeze across the ship, rake aft with height
            v.co.y = b + (v.co.y - b) * (rb / ra)
            v.co.x -= (v.co.z - z0) * 0.05


def mast(k, a, b, z0, z1, mat="rail"):
    k.rod((a, b, z0), (a, b, z1), 0.09, mat, n=4)
    k.rod((a, b - 0.9, z1 - 2.5), (a, b + 0.9, z1 - 2.5), 0.06, mat, n=4)
    k.blob(a, b, z1 + 0.2, 0.18, 0.18, 0.5, "lamp")


def lifeboat(k, a, b, z, L=2.4, mat="lifeboat"):
    k.blob(a, b, z + 0.6, L / 2, 0.5, 1.0, mat)


# --- models ----------------------------------------------------------------------------------

def tanker(k):
    """Oil tanker: long low hull in company colour, green deck with pipe run, aft accommodation."""
    L, B, h = 25.5, 6.4, 3.4
    hull(k, L, B, h, "cc", deck="deck_green", bow=0.24, stern=0.18, point=0.1, sheer=1.6, band="white_band",
         band_z=(h - 0.55, h - 0.25))
    # Pipe run with manifolds and a catwalk along the middle.
    k.rod((-6.5, 0, h + 0.7), (9.5, 0, h + 0.7), 0.22, "steel", n=6)
    k.rod((-6.5, 0.7, h + 1.6), (10.5, 0.7, h + 1.6), 0.1, "steel_dark", n=4)
    for a in (-3.0, 1.5, 6.0):
        k.box(a - 0.5, a + 0.5, -2.2, 2.2, h, h + 1.0, "red")
        k.cyl(a, 0, 0.75, h, h + 1.2, "tank", n=8)
    for a in bk.frange(-6, 10, 2.0):
        k.box(a - 0.2, a + 0.2, -0.2, 0.2, h, h + 1.6, "steel_dark")
    # Forecastle with a mast.
    k.box(9.8, 11.4, -2.2, 2.2, h, h + 1.6, "white")
    mast(k, 10.6, 0, h + 1.6, h + 8)
    # Aft accommodation, bridge with wings, funnel.
    a0, a1 = -12.2, -7.4
    block(k, a0, a1, -2.9, 2.9, h, h + 6, "white")
    windows(k, a0 + 0.2, a1, -2.9, 2.9, h + 2.0, h + 3.2, glass="glass")
    block(k, a0 + 0.8, a1 + 0.1, -2.8, 2.8, h + 6, h + 9.4, "white")
    windows(k, a0 + 0.8, a1 + 0.1, -2.8, 2.8, h + 7.4, h + 8.9, glass="glass")
    k.box(a1 - 1.6, a1 + 0.2, -3.6, 3.6, h + 8.7, h + 9.2, "white")
    k.box(a0 + 0.7, a1 + 0.2, -2.9, 2.9, h + 9.4, h + 9.8, "roof_flat")
    funnel(k, a0 + 1.6, 0, h + 9.4, h + 15.0, 1.1, 0.8)
    mast(k, a1 - 0.6, 0, h + 9.8, h + 13.5)
    lifeboat(k, a0 + 2.6, 3.0, h + 3.2)
    lifeboat(k, a0 + 2.6, -3.0, h + 3.2)


def cargo(k):
    """General cargo ship: company-colour hull, three hatch covers, yellow deck cranes, aft bridge."""
    L, B, h = 30.0, 6.6, 3.8
    hull(k, L, B, h, "cc", deck="deck_rust", bow=0.25, stern=0.16, point=0.1, sheer=1.8, band="white_band",
         band_z=(h - 0.5, h - 0.2))
    for a0, a1 in ((-7.4, -1.6), (-0.6, 5.2), (6.2, 11.0)):
        k.box(a0, a1, -2.4, 2.4, h, h + 1.6, "hatch")
        for a in bk.frange(a0 + 0.8, a1 - 0.8, 1.6):
            k.box(a - 0.1, a + 0.1, -2.45, 2.45, h + 1.2, h + 1.65, "steel")
    # Cranes between the hatches: pedestal, cab, jib reaching over the next hatch.
    for a, side in ((-1.1, 1), (5.7, -1)):
        k.cyl(a, side * 2.1, 0.55, h, h + 5.5, "crane", n=8)
        k.box(a - 0.8, a + 0.8, side * 2.1 - 0.7, side * 2.1 + 0.7, h + 5.5, h + 7.0, "crane")
        k.rod((a, side * 2.1, h + 6.0), (a + 4.0, side * 0.6, h + 10.5), 0.18, "crane", n=4)
        k.rod((a + 4.0, side * 0.6, h + 10.5), (a + 4.0, side * 0.6, h + 6.0), 0.03, "dark", n=3)
    # Forecastle, mast.
    k.box(11.8, 13.6, -2.4, 2.4, h, h + 1.8, "white")
    mast(k, 12.6, 0, h + 1.8, h + 8.5)
    # Aft accommodation.
    a0, a1 = -14.0, -8.6
    block(k, a0, a1, -3.0, 3.0, h, h + 6.5, "white")
    windows(k, a0 + 0.2, a1, -3.0, 3.0, h + 2.2, h + 3.4)
    block(k, a0 + 0.8, a1 + 0.1, -2.9, 2.9, h + 6.5, h + 10.0, "white")
    windows(k, a0 + 0.8, a1 + 0.1, -2.9, 2.9, h + 7.9, h + 9.4)
    k.box(a1 - 1.6, a1 + 0.2, -3.8, 3.8, h + 9.3, h + 9.8, "white")
    k.box(a0 + 0.7, a1 + 0.2, -3.0, 3.0, h + 10.0, h + 10.4, "roof_flat")
    funnel(k, a0 + 1.6, 0, h + 10.0, h + 15.5, 1.1, 0.8)
    mast(k, a1 - 0.6, 0, h + 10.4, h + 14.0)
    lifeboat(k, a0 + 2.8, 3.1, h + 3.4)
    lifeboat(k, a0 + 2.8, -3.1, h + 3.4)


def ferry(k):
    """Passenger ferry: white hull with a company-colour stripe, two cabin decks, sun deck aft."""
    L, B, h = 17.5, 5.4, 3.2
    hull(k, L, B, h, "white", deck="deck_wood", bow=0.3, stern=0.2, point=0.14, sheer=1.0, band="cc",
         band_z=(1.2, 2.3))
    # Main deck saloon with a long window band, upper deck with the bridge forward.
    a0, a1 = -6.6, 5.4
    block(k, a0, a1, -2.3, 2.3, h, h + 4.4, "white")
    windows(k, a0, a1, -2.3, 2.3, h + 1.4, h + 3.3, glass="glass", pitch=1.2)
    k.box(a0 - 0.2, a1 + 0.2, -2.45, 2.45, h + 4.4, h + 4.8, "cc")
    a2, a3 = -3.0, 4.0
    block(k, a2, a3, -1.9, 1.9, h + 4.8, h + 8.0, "white")
    windows(k, a2, a3, -1.9, 1.9, h + 5.8, h + 7.4, glass="glass", pitch=1.2)
    k.box(a3 - 0.3, a3 + 0.15, -1.95, 1.95, h + 5.7, h + 7.5, "glass_light")  # wide bridge front
    k.box(a2 - 0.1, a3 + 0.1, -2.0, 2.0, h + 8.0, h + 8.3, "roof_flat")
    funnel(k, -1.4, 0, h + 8.3, h + 12.0, 0.9, 0.7)
    mast(k, 2.6, 0, h + 8.3, h + 12.5)
    # Sun deck railing aft, lifeboats on the saloon roof, bow railing.
    railing(k, [(a0 + 0.2, -2.2), (a0 + 0.2, 2.2)], h + 4.8, h=1.0)
    railing(k, [(-8.2, -2.2), (-8.7, 0), (-8.2, 2.2)], h, h=1.2)
    railing(k, [(a1 + 0.4, -2.2), (8.0, 0), (a1 + 0.4, 2.2)], h, h=1.2)
    lifeboat(k, -4.6, 2.0, h + 4.8, L=2.0)
    lifeboat(k, -4.6, -2.0, h + 4.8, L=2.0)


def hover(k):
    """Hovercraft: black skirt, white body with company stripe, cabin, two ducted fans aft."""
    L, B = 18.0, 7.8
    pl = plan(L, B, bow=0.22, stern=0.25, point=0.45, n=6)
    loft(k, [[(a * 0.96, b * 0.94, 0) for a, b in pl], [(a * 1.03, b * 1.04, 1.4) for a, b in pl],
             [(a, b, 2.0) for a, b in pl]], "rubber")
    body = plan(L - 0.8, B - 0.6, bow=0.22, stern=0.25, point=0.45, n=6)
    loft(k, [[(a, b, 2.0) for a, b in body], [(a, b, 4.0) for a, b in body]], "white")
    loft(k, [[(a * 1.005, b * 1.01, 2.5) for a, b in body], [(a * 1.005, b * 1.01, 3.3) for a, b in body]], "cc")
    deck = [(a * 0.97, b * 0.94) for a, b in body]
    loft(k, [[(a, b, 3.8) for a, b in deck], [(a, b, 4.1) for a, b in deck]], "deck_grey")
    # Passenger cabin with rounded front: wall, window band, wall, cambered roof.
    cab = [(a + 1.0, b) for a, b in plan(10.0, 5.0, bow=0.3, stern=0.05, point=0.55, n=5)]
    loft(k, [[(a, b, 4.1) for a, b in cab], [(a, b, 9.6) for a, b in cab]], "white")
    loft(k, [[(1.0 + (a - 1.0) * 1.012, b * 1.03, 6.0) for a, b in cab],
             [(1.0 + (a - 1.0) * 1.012, b * 1.03, 8.2) for a, b in cab]], "glass")
    loft(k, [[(1.0 + (a - 1.0) * 1.014, b * 1.035, 8.9) for a, b in cab],
             [(1.0 + (a - 1.0) * 1.014, b * 1.035, 9.6) for a, b in cab]], "cc")
    loft(k, [[(1.0 + (a - 1.0) * 0.98, b * 0.96, 9.6) for a, b in cab],
             [(1.0 + (a - 1.0) * 0.9, b * 0.7, 10.4) for a, b in cab]], "roof_flat")
    k.box(-4.6, -3.0, -1.0, 1.0, 9.6, 11.0, "steel")  # air intake
    # Two ducted fans on pylons at the stern, rudders in their wake.
    for b in (-1.9, 1.9):
        k.box(-7.6, -6.4, b - 0.25, b + 0.25, 4.0, 7.0, "white")
        k.rod((-7.7, b, 8.2), (-6.5, b, 8.2), 1.5, "white", n=14)
        k.rod((-7.8, b, 8.2), (-6.4, b, 8.2), 1.22, "dark", n=14)
        k.box(-8.6, -8.2, b - 0.1, b + 0.1, 5.0, 11.2, "cc")
    k.box(-8.6, -8.2, -2.0, 2.0, 10.8, 11.2, "cc")


def toycargo(k):
    """Toy cargo boat: round-ended red tub, a load of building blocks, a toy wheelhouse and fat funnel."""
    L, B, h = 25.0, 6.6, 3.6
    rings = hull_rings(L, B, 0, h, bow=0.22, stern=0.22, point=0.55, flare=0.8, sheer=1.4)
    loft(k, rings, "cc")
    band = [(a * 1.004, b * 1.012) for a, b in plan(L, B, 0.22, 0.22, 0.55)]
    loft(k, [[(a, b, h - 0.9) for a, b in band], [(a, b, h - 0.2) for a, b in band]], "toy_yellow")
    deck_plate(k, L, B, h, "toy_wood", 0.22, 0.22, 0.55, 1.4, sa=0.96)
    # Portholes along the hull.
    for a in bk.frange(-9.5, 8.0, 2.5):
        for s in (-1, 1):
            k.rod((a, s * (B / 2 - 0.2), 1.7), (a, s * (B / 2 + 0.08), 1.7), 0.42, "toy_white", n=8)
            k.rod((a, s * (B / 2 - 0.1), 1.7), (a, s * (B / 2 + 0.12), 1.7), 0.26, "toy_blue", n=8)
    # Building blocks: cubes, a cylinder, a pyramid, in bright colours.
    cols = ["toy_blue", "toy_green", "toy_yellow", "toy_purple", "toy_orange", "toy_pink", "toy_red", "toy_mint"]
    i = 0
    for a in (-4.6, -1.6, 1.4, 4.4):
        for b in (-1.5, 1.5):
            k.box(a - 1.3, a + 1.3, b - 1.3, b + 1.3, h + 0.1, h + 3.2, cols[i % len(cols)])
            i += 1
    k.box(-3.1 - 1.3, -3.1 + 1.3, -1.3, 1.3, h + 3.2, h + 6.3, "toy_red")
    k.cyl(2.9, 0, 1.25, h + 3.2, h + 6.4, "toy_yellow", n=12)
    k.cyl(7.4, 0, 1.5, h + 0.1, h + 4.2, "toy_green", n=4, r_top=0.05, rot=math.pi / 4)
    # Wheelhouse like a toy house with a pitched roof, round windows; fat striped funnel.
    a0, a1 = -11.4, -6.8
    block(k, a0, a1, -2.4, 2.4, h, h + 6.0, "toy_white")
    for z in (h + 2.0, h + 4.4):
        for s in (-1, 1):
            k.rod((-9.1, s * 2.35, z), (-9.1, s * 2.55, z), 0.55, "toy_blue", n=10)
        k.rod((a1 - 0.1, 0, z), (a1 + 0.12, 0, z), 0.55, "toy_blue", n=10)
    k.gable(a0 - 0.1, a1 + 0.1, -2.5, 2.5, h + 6.0, h + 9.0, "x", "toy_red", "toy_white", over=0.4, thick=0.4)
    k.cyl(-10.0, 0, 1.25, h + 6.0, h + 13.0, "toy_yellow", n=14)
    k.cyl(-10.0, 0, 1.27, h + 9.0, h + 10.4, "cc", n=14)
    k.cyl(-10.0, 0, 1.5, h + 13.0, h + 13.8, "toy_red", n=14)
    k.blob(-10.6, 0.4, h + 16.0, 1.0, 1.0, 2.0, "toy_white", subdiv=1)  # puff of smoke
    k.blob(-11.6, 0.9, h + 18.4, 0.7, 0.7, 1.4, "toy_white", subdiv=1)


def toyferry(k):
    """Toy paddle steamer: rounded hull, paddle boxes with sunburst, two tall striped funnels, pennants."""
    L, B, h = 17.0, 5.4, 3.2
    rings = hull_rings(L, B, 0, h, bow=0.28, stern=0.25, point=0.4, flare=0.82, sheer=1.2)
    loft(k, rings, "toy_white")
    band = [(a * 1.004, b * 1.012) for a, b in plan(L, B, 0.28, 0.25, 0.4)]
    loft(k, [[(a, b, 1.0) for a, b in band], [(a, b, 2.2) for a, b in band]], "cc")
    deck_plate(k, L, B, h, "toy_wood", 0.28, 0.25, 0.4, 1.2, sa=0.96)
    # Paddle boxes: half discs on both sides with coloured spokes.
    for s in (-1, 1):
        b0, b1 = s * (B / 2 - 0.2), s * (B / 2 + 1.0)
        k.rod((0.0, b0, 3.0), (0.0, b1, 3.0), 2.6, "toy_red", n=16)
        k.rod((0.0, b1, 3.0), (0.0, b1 + s * 0.12, 3.0), 1.9, "toy_yellow", n=16)
        k.rod((0.0, b1, 3.0), (0.0, b1 + s * 0.2, 3.0), 0.5, "toy_red", n=8)
    # Cabin deck with round windows, upper deck with wheelhouse.
    a0, a1 = -6.0, 5.0
    block(k, a0, a1, -2.2, 2.2, h, h + 3.8, "toy_mint")
    for a in bk.frange(a0 + 0.9, a1 - 0.9, 1.6):
        for s in (-1, 1):
            k.rod((a, s * 2.15, h + 2.0), (a, s * 2.32, h + 2.0), 0.55, "toy_white", n=10)
            k.rod((a, s * 2.25, h + 2.0), (a, s * 2.36, h + 2.0), 0.36, "toy_blue", n=10)
    k.box(a0 - 0.3, a1 + 0.3, -2.5, 2.5, h + 3.8, h + 4.3, "toy_pink")
    railing(k, [(a0, -2.4), (a1, -2.4), (a1, 2.4), (a0, 2.4), (a0, -2.4)], h + 4.3, h=1.0, mat="toy_white")
    block(k, 1.4, 4.2, -1.4, 1.4, h + 4.3, h + 7.2, "toy_white")
    windows(k, 1.4, 4.2, -1.4, 1.4, h + 5.3, h + 6.6, glass="toy_blue", frame="toy_white", pitch=0.9)
    k.cyl(2.8, 0, 2.0, h + 7.2, h + 8.2, "toy_red", n=4, r_top=1.0, rot=math.pi / 4)
    for a, top in ((-1.0, 15.5), (-3.6, 14.5)):
        k.cyl(a, 0, 0.85, h + 4.3, h + top, "toy_blue", n=12)
        for z in bk.frange(h + 7.0, h + top - 2.0, 2.4):
            k.cyl(a, 0, 0.87, z, z + 1.0, "toy_white", n=12)
        k.cyl(a, 0, 1.15, h + top, h + top + 0.6, "toy_yellow", n=12, r_top=1.25)
    # Bow mast with pennant.
    k.rod((7.2, 0, h), (7.2, 0, h + 7.0), 0.1, "toy_wood", n=4)
    k.prism([(7.2, 0.0), (7.2, 0.05), (5.6, 0.0)], h + 5.6, h + 6.9, "toy_yellow")


MODELS = {
    "tanker": ("ship", tanker), "cargo": ("ship", cargo), "ferry": ("ship", ferry), "hover": ("ship", hover),
    "toycargo": ("ship", toycargo), "toyferry": ("ship", toyferry),
}
import aircraft  # noqa: E402  (after the palette above: the toy colours are shared)
MODELS.update(aircraft.AIRCRAFT)
import disasters  # noqa: E402
MODELS.update(disasters.DISASTERS)


# --- rendering ---------------------------------------------------------------------------------

def turned(parts, d):
    """Copies of parts with local +a pointing in direction d (proper rotation about z)."""
    dx, dy = DIRS[d]
    th = math.atan2(dy, dx)
    c, s = math.cos(th), math.sin(th)
    out = []
    for mat, bm in parts:
        bm = bm.copy()
        for v in bm.verts:
            a, b = v.co.x, v.co.y
            v.co = Vector((a * c - b * s, a * s + b * c, v.co.z))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        out.append((mat, bm))
    return out


def render_model(outdir, name, kind, build, meta, zooms=bk.ZOOMS, dirs=None):
    k = bk.Kit()
    build(k)
    spec = TYPES[kind]
    w, h, anchor = spec["canvas"]
    for d in range(spec.get("dirs", 8)):
        if dirs is not None and d not in dirs:
            continue
        parts = turned(k.parts, d)
        sx, sy = remap(*spec["origin"][d])
        for zoom in zooms:
            zdir = os.path.join(outdir, f"z{zoom}")
            os.makedirs(zdir, exist_ok=True)
            # Vehicle position = the N-corner point of the camera (canvas column w/2 - 1, row anchor at 1x).
            scene = bk.new_scene(zoom, w, h, anchor)
            bk.link_parts(parts, (0, 0), bk.Materials("color"))
            bk.render(scene, os.path.join(zdir, f"{name}_d{d}.png"))
            scene = bk.new_scene(zoom, w, h, anchor, samples=8)
            scene.cycles.filter_width = 0.01
            bk.link_parts(parts, (0, 0), bk.Materials("cc", CC))
            bk.render(scene, os.path.join(zdir, f"{name}_d{d}_cc.png"))
            meta[f"{name}_d{d}_z{zoom}"] = [(w // 2 - 1 + sx) * zoom, (anchor + sy) * zoom]
        print(f"rendered {name} d{d}", flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    outdir = argv[0] if argv and not argv[0].startswith("--") else os.path.join(os.getcwd(), "render", "vehicles")
    only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    # Previews: --zooms 4 --dirs 2,5 render a subset.
    zooms = [int(z) for z in argv[argv.index("--zooms") + 1].split(",")] if "--zooms" in argv else bk.ZOOMS
    dirs = {int(d) for d in argv[argv.index("--dirs") + 1].split(",")} if "--dirs" in argv else None
    os.makedirs(outdir, exist_ok=True)
    meta_path = os.path.join(outdir, "meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for name, (kind, build, *model_dirs) in MODELS.items():
        if only and name not in only:
            continue
        # Models the game draws in a few directions only list them (disasters.py).
        use = dirs if dirs is not None else (set(model_dirs[0]) if model_dirs else None)
        render_model(outdir, name, kind, build, meta, zooms, use)
        json.dump(meta, open(meta_path, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
