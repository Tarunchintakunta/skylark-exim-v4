"""S3 reefer.blend -> v-reefer (f1-192, kind ext).
f1 BRIDGE_FROST (frost macro on the hero carton inside a 40-ft reefer on a feeder ship) -> pull out, track back
through the open (cut-away) doors into the lashing-bridge gap, rise past the reefer unit above, sweep out to a high
aerial of the feeder underway at 12 kn, tilt down to BRIDGE_SEA (open sea, cam 60 m, lens 35, ocean seed 41 t=0).
   $B -b --factory-startup --python assets-src/blender/build/reefer.py
Ship space S: origin midship on the waterline, +Y forward, +X starboard. The ship sails +Y in world.
"""
import math
import random
import sys

sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

import sklib  # noqa: E402

D2R = math.pi / 180
F0, F1 = 1, 192
V = 6.17                       # 12 kn in m/s
SHIP_X, SHIP_Y192 = -58.0, 5.0  # ship midship (world) at f192; hull stays > 15 m outside the BRIDGE_SEA frame
rng = random.Random(3)

s = sklib.reset()
sklib.sky_world(sun_elev_deg=52, sun_az_deg=135)


def ship_y(f):
    return SHIP_Y192 + V * (f - F1) / 24.0


def motion(f, w=1.0):
    """(heave, pitch, roll) of the hull, scaled by w."""
    t = f / 24.0
    return (w * 0.12 * math.sin(2 * math.pi * t / 6.5),
            w * 0.5 * D2R * math.sin(2 * math.pi * t / 7.0 + 1.0),
            w * 1.2 * D2R * math.sin(2 * math.pi * t / 9.0 + 0.4))


def motion_m(f, w=1.0):
    h, p, r = motion(f, w)
    return Matrix.Translation((0, 0, h)) @ Euler((p, r, 0), 'XYZ').to_matrix().to_4x4()


def root_m(f):
    return Matrix.Translation((SHIP_X, ship_y(f), 0))


# ------------------------------------------------------------------------------------------------ ship rig
ROOT = sklib.new_obj('SHIP_ROOT', None)
MOT = sklib.new_obj('SHIP_MOTION', None, parent=ROOT)
for f in range(F0 - 2, F1 + 3):
    ROOT.location = root_m(f).to_translation()
    ROOT.keyframe_insert('location', frame=f)
    h, p, r = motion(f)
    MOT.location, MOT.rotation_euler = (0, 0, h), (p, r, 0)
    MOT.keyframe_insert('location', frame=f)
    MOT.keyframe_insert('rotation_euler', frame=f)
for ob in (ROOT, MOT):
    for fc in sklib._fcurves(ob):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'

SHIP = sklib.collection('SHIP')


def mesh(name, bm, mats, parent=MOT, coll=SHIP, bev=0.0, seg=2):
    ob = sklib._mesh_obj(name, bm, coll, parent)
    sklib.mat_to(ob, *mats)
    if bev:
        sklib.bevel(ob, bev, seg)
    return ob


def box(bm, c, size, mi=0):
    sklib._bm_box(bm, Vector(c), size, mi)


# ------------------------------------------------------------------------------------------------ hull
L2, B = 75.0, 11.5
DECK = 4.5


def sq(u):
    return math.sqrt(max(0.0, 1 - u * u))


def b_deck(y):
    if y > 45:
        return B * sq((y - 45) / 30)
    if y < -60:
        return 9.6 + 1.9 * (y + 75) / 15
    return B


def b_wl(y):
    if y > 30:
        return B * sq((y - 30) / 42)
    if y < -58:
        return max(0.0, 8.5 + 3.0 * (y + 75) / 17)
    return B


def b_bot(y):
    if y > 22:
        return B * sq((y - 22) / 44)
    if y < -55:
        return max(0.0, B * sq((y + 55) / 15))
    return B


def deck_z(y):
    t = min(1, max(0, (y - 54) / 8))
    return DECK + 2.6 * t * t * (3 - 2 * t)


def keel_z(y):
    return -8.0 if y > -58 else -8.0 + 8.6 * min(1, (-58 - y) / 17)


HULL_PAINT = sklib.painted_metal((0.27, 0.075, 0.045), 0.55, 0.85, 0.6)
BOOT = sklib.painted_metal((0.045, 0.04, 0.035), 0.6, 0.35, 0.5)
ANTIF = sklib.painted_metal((0.22, 0.05, 0.035), 0.5, 0.2, 0.5)
DECK_M = sklib.painted_metal((0.13, 0.17, 0.14), 0.6, 0.3, 0.6)
WHITE = sklib.painted_metal((0.80, 0.80, 0.77), 0.35, 0.55, 0.5)
GREY = sklib.painted_metal((0.33, 0.35, 0.36), 0.45, 0.4, 0.5)
HATCH = sklib.painted_metal((0.24, 0.08, 0.05), 0.5, 0.5, 0.6)
GALV = sklib.galvanised(0.35)
GLASS = sklib.flat('bridge_glass', (0.015, 0.022, 0.026), rough=0.04, var=0.03, **{'Coat Weight': 0.6})
RUBBER = sklib.plastic((0.02, 0.02, 0.02), 0.2, name='rubber_black')


def hull():
    bm = bmesh.new()
    ys = list(np.arange(-L2, L2 + 0.01, 1.5))
    rings = []
    for y in ys:
        bd, bw, bb, dz, kz = b_deck(y), b_wl(y), b_bot(y), deck_z(y), keel_z(y)
        bh = 1.25 if y > 48 else 0.0
        side = []
        for z in (dz, 3.0, 1.6, 0.6, -0.5):
            t = max(0.0, min(1.0, z / dz))
            side.append((bw + (bd - bw) * t, max(z, kz)))
        for x, z in ((bb, -3.0), (bb, -6.2), (max(0, bb - 0.6), -7.4), (max(0, bb - 2.0), -8.0)):
            side.append((min(x, bw), max(z, kz)))
        top = [(max(0, bd - 0.25), dz), (max(0, bd - 0.25), dz + bh), (bd, dz + bh)]
        half = top + side                  # starboard, from inner bulwark foot down to the keel
        pts = [(x, z) for x, z in half] + [(0.0, max(-8.0, kz))] + [(-x, z) for x, z in reversed(half)]
        rings.append([bm.verts.new((x, y, z)) for x, z in pts])
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n - 1):
            f = bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
        bm.faces.new((a[-1], b[-1], b[0], a[0]))      # deck strip between the bulwark feet
    bm.faces.new(list(reversed(rings[0])))           # transom
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        c = f.calc_center_median()
        if abs(f.normal.z) > 0.9 and c.z > DECK - 0.1 and abs(c.x) < b_deck(c.y) - 0.2:
            f.material_index = 3
        elif c.z < -0.5:
            f.material_index = 2
        elif c.z < 0.6:
            f.material_index = 1
        else:
            f.material_index = 0
    ob = mesh('A-VESSEL-FEEDER.hull', bm, (HULL_PAINT, BOOT, ANTIF, DECK_M))
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=40 * D2R)
    ob.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL').keep_sharp = True
    return ob


hull()

# ------------------------------------------------------------------------------------------------ cargo layout
BAY_Y = [-46.0 + 15.19 * k for k in range(7)]
ROW_X = [(i - 4) * 2.465 for i in range(9)]
HATCH_TOP = 6.0
HD, HR = 2.591, 2.896
TL = 0.03                       # twistlock gap
OUR_BAY, OUR_ROW = 4, 7

bm = bmesh.new()
for y in BAY_Y:                 # hatch coamings + covers (with cover-panel seams)
    box(bm, (0, y, (DECK + HATCH_TOP) / 2 - 0.05), (21.8, 12.7, HATCH_TOP - DECK - 0.1))
    for k in range(4):
        box(bm, (0, y - 4.8 + k * 3.2, HATCH_TOP - 0.05), (21.6, 3.12, 0.1))
mesh('hatch_covers', bm, (HATCH,), bev=0.03)

variants = sklib.container_collection_variants(weathers=(0.15, 0.6))
dry_v = [c for c in variants if 'DRY' in c.name]
rf_v = [c for c in variants if '40RF' in c.name]
CARGO = sklib.collection('CARGO', SHIP)
stacks = {}                     # (bay,row) -> list of (z0, h, kind)
tw = bmesh.new()


def corners(x, y, z):
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(tw, (x + sx * 1.13, y + sy * 6.0, z - TL / 2), (0.11, 0.17, TL))


for bi, y in enumerate(BAY_Y):
    for ri, x in enumerate(ROW_X):
        tiers = 4
        if (bi, ri) != (OUR_BAY, OUR_ROW) and not (bi in (3, 4) and ri >= 5):
            tiers = rng.choice((3, 4, 4, 4, 5)) if 1 <= ri <= 7 else rng.choice((3, 4))
        if bi == 0:
            tiers = min(tiers, 4)  # keep the view from the bridge
        z = HATCH_TOP + TL
        col = []
        for t in range(tiers):
            if (bi, ri) == (OUR_BAY, OUR_ROW):
                kind = ('dry', 'dry', 'hero', 'fan')[t]
            else:
                kind = 'rf' if t >= 2 and rng.random() < 0.25 else 'dry'
            h = HD if kind == 'dry' else HR
            corners(x, y, z)
            if kind in ('dry', 'rf'):
                c = rng.choice(dry_v if kind == 'dry' else rf_v)
                e = sklib.instance(c, (x, y, z), -math.pi / 2, 'I_%d_%d_%d' % (bi, ri, t), CARGO)
                e.parent = MOT
            col.append((z, h, kind))
            z += h + TL
        stacks[(bi, ri)] = col
mesh('twistlocks', tw, (GALV,))

# our column: hero reefer (doors aft, cut-away) on tier 3, a reversed reefer with its unit facing the gap on tier 4
OX, OY = ROW_X[OUR_ROW], BAY_Y[OUR_BAY]
OZ = stacks[(OUR_BAY, OUR_ROW)][2][0]
FZ = stacks[(OUR_BAY, OUR_ROW)][3][0]
L, W = 12.192, 2.438


def own_reefer(name, loc, rot, cut):
    ob = sklib.container_40('reefer', 'white', 0.15, name, SHIP)
    ob.data = ob.data.copy()
    ob.data.name = name
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = [f for f in bm.faces if cut(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(ob.data)
    bm.free()
    ob.parent, ob.location, ob.rotation_euler = MOT, loc, (0, 0, rot)
    return ob


HERO_C = own_reefer('A-CONT-40RF-HERO', (OX, OY, OZ), -math.pi / 2,
                    lambda c: (c.x > L / 2 - 0.13 and abs(c.y) < 1.072 and 0.2 < c.z < HR - 0.2) or
                              (c.x > L / 2 - 0.07 and abs(c.y) < 1.10 and 0.2 < c.z < HR - 0.2))
GC = Vector((-L / 2 + 0.03, -0.42, 1.4))
FAN_C = own_reefer('A-CONT-40RF-FAN', (OX, OY, FZ), math.pi / 2,
                   lambda c: abs(c.x - (-L / 2 + 0.009)) < 0.004 and (Vector((0, c.y, c.z)) - Vector((0, GC.y, GC.z))).length < 0.375)

# condenser fan (5 pitched blades + hub) behind the grille, spinning
bm = bmesh.new()
sklib._bm_cyl(bm, Vector((0, 0, 0)), 0.075, 0.03, 'X', 16)
for k in range(5):
    a = 2 * math.pi * k / 5
    vs = []
    for r, da, dx in ((0.07, -0.16, -0.010), (0.07, 0.16, 0.010), (0.335, 0.22, 0.008), (0.335, -0.22, -0.008)):
        vs.append(bm.verts.new((dx, r * math.cos(a + da), r * math.sin(a + da))))
    bm.faces.new(vs)
fan = mesh('A-REEFER-FAN', bm, (sklib.plastic((0.05, 0.055, 0.06), 0.4, name='fan_plastic'),), parent=FAN_C)
fan.location = (-L / 2 + 0.026, GC.y, GC.z)
so = fan.modifiers.new('Solidify', 'SOLIDIFY')
so.thickness = 0.003
for f, a in ((F0 - 2, 0.0), (F1 + 2, (F1 + 4 - F0) * 15 * D2R)):
    fan.rotation_euler.x = a
    fan.keyframe_insert('rotation_euler', index=0, frame=f)
for fc in sklib._fcurves(fan):
    for k in fc.keyframe_points:
        k.interpolation = 'LINEAR'
# status lamp (green) on the control box
bm = bmesh.new()
sklib._bm_cyl(bm, Vector((-L / 2 - 0.03, 0.30, 1.78)), 0.022, 0.02, 'X', 12)
mesh('reefer_status_lamp', bm, (sklib.flat('lamp_green', (0.1, 0.9, 0.2), 0.3, **{'Emission Color': (0.1, 1.0, 0.25, 1), 'Emission Strength': 9.0}),),
     parent=FAN_C)


def s_of_fan(lx, ly, lz):      # FAN_C local -> ship space (rot +90)
    return Vector((OX - ly, OY + lx, FZ + lz))


# plug cable from the unit socket down to the socket box on the lashing bridge
GAP_Y0, GAP_Y1 = BAY_Y[OUR_BAY - 1] + L / 2, OY - L / 2      # 5.70 .. 8.70
GAP_C = (GAP_Y0 + GAP_Y1) / 2
BR_Z = stacks[(OUR_BAY, OUR_ROW)][1][0] + HD                  # upper walkway level (top of tier 2)
p0 = s_of_fan(-L / 2 - 0.05, 0.95, 0.35)
cu = bpy.data.curves.new('plug_cable', 'CURVE')
cu.dimensions, cu.bevel_depth, cu.bevel_resolution = '3D', 0.013, 3
sp = cu.splines.new('BEZIER')
pts = [p0, p0 + Vector((-0.15, -0.25, -0.2)), Vector((OX - 1.55, GAP_Y1 - 0.75, BR_Z + 1.9)),
       Vector((OX - 1.95, GAP_C + 0.45, BR_Z + 1.25))]
sp.bezier_points.add(len(pts) - 1)
for bp, p in zip(sp.bezier_points, pts):
    bp.co, bp.handle_left_type, bp.handle_right_type = p, 'AUTO', 'AUTO'
cab = sklib.new_obj('A-REEFER-PLUG-CABLE', cu, SHIP, MOT)
cab.data.materials.append(RUBBER)

# ------------------------------------------------------------------------------------------------ lashing bridges + rods
lb, rods, sock = bmesh.new(), bmesh.new(), bmesh.new()
for k in range(len(BAY_Y) - 1):
    y0, y1 = BAY_Y[k] + L / 2, BAY_Y[k + 1] - L / 2
    yc = (y0 + y1) / 2
    for zt in (HATCH_TOP + TL + HD, HATCH_TOP + 2 * (TL + HD)):
        box(lb, (0, yc, zt - 0.03), (22.0, 0.95, 0.06))                       # grating walkway
        for yy in (yc - 0.47, yc + 0.47):
            box(lb, (0, yy, zt + 1.05), (22.0, 0.045, 0.045))                 # hand rail
            box(lb, (0, yy, zt + 0.55), (22.0, 0.03, 0.03))                   # knee rail
        for x in np.arange(-11.0, 11.01, 2.465):
            for yy in (yc - 0.47, yc + 0.47):
                box(lb, (x, yy, zt + 0.53), (0.045, 0.045, 1.06))
    for x in (-11.0, -6.1, -1.2, 3.7, 8.6, 11.0):                              # columns from the hatch
        for yy in (yc - 0.4, yc + 0.4):
            box(lb, (x, yy, (HATCH_TOP + HATCH_TOP + 2 * (TL + HD)) / 2), (0.2, 0.2, 2 * (TL + HD)))
    # rods: X-lashing on every container end facing this gap, tiers 2-3, except our door end + the fan unit above it
    zt = HATCH_TOP + 2 * (TL + HD)
    for ri, x in enumerate(ROW_X):
        for yf, sgn, bi in ((y0, 1, k), (y1, -1, k + 1)):
            if bi == OUR_BAY and ri == OUR_ROW:
                continue
            col = stacks[(bi, ri)]
            if len(col) < 3:
                continue
            ztop = col[2][0] + col[2][1] - 0.06
            for sx in (-1, 1):
                a = Vector((x + sx * 0.9, yf + sgn * 0.35, zt + 0.05))
                b = Vector((x - sx * 1.13, yf + sgn * 0.05, ztop + 0.06))
                d = b - a
                bmesh.ops.create_cone(rods, cap_ends=True, segments=8, radius1=0.014, radius2=0.014, depth=d.length,
                                      matrix=Matrix.Translation((a + b) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4())
                tb = a + d.normalized() * 0.45                                       # turnbuckle
                bmesh.ops.create_cone(rods, cap_ends=True, segments=8, radius1=0.03, radius2=0.03, depth=0.5,
                                      matrix=Matrix.Translation(tb) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4())
    if k == OUR_BAY - 1:
        box(sock, (OX - 1.95, yc + 0.47, zt + 0.95), (0.42, 0.18, 0.55))         # reefer socket box on the rail
mesh('lashing_bridges', lb, (GALV,), bev=0.006, seg=1)
mesh('lashing_rods', rods, (GALV,))
mesh('reefer_socket_box', sock, (GREY,), bev=0.01)

# ------------------------------------------------------------------------------------------------ accommodation, funnel
acc, gl, fun = bmesh.new(), bmesh.new(), bmesh.new()
for d in range(5):
    z0 = DECK + 2.8 * d
    box(acc, (0, -62, z0 + 1.4), (18.0 - 0.0 * d, 12.0, 2.8))
    for fy in (-56.0, -68.0):
        for wx in np.arange(-7.5, 7.6, 1.5):
            box(gl, (wx, fy + (0.03 if fy > -60 else -0.03), z0 + 1.55), (1.0, 0.04, 0.9))
    for sx in (-1, 1):
        for wy in np.arange(-66.5, -57.4, 1.8):
            box(gl, (sx * 9.03, wy, z0 + 1.55), (0.04, 1.0, 0.9))
zb = DECK + 14.0
box(acc, (0, -58.5, zb + 1.5), (23.2, 5.0, 3.0))                                     # wheelhouse + bridge wings
for wx in np.arange(-10.8, 10.9, 1.2):
    box(gl, (wx, -55.97, zb + 1.85), (1.0, 0.04, 1.3))
box(acc, (0, -58.5, zb + 3.1), (23.6, 5.4, 0.2))
box(acc, (0, -60.5, zb + 6.5), (0.5, 0.5, 6.6))                                      # mast
box(acc, (0, -60.5, zb + 8.0), (5.0, 0.3, 0.3))
box(fun, (0, -66.5, zb + 3.2), (5.0, 4.0, 8.6))                                      # funnel
box(fun, (0, -66.5, zb + 7.75), (5.06, 4.06, 0.5), 1)
mesh('accommodation', acc, (WHITE,), bev=0.05)
mesh('bridge_windows', gl, (GLASS,))
mesh('funnel', fun, (GREY, RUBBER), bev=0.06)
bm = bmesh.new()                                                                      # free-fall lifeboat
box(bm, (0, 0, 0), (2.6, 7.5, 2.4))
lb_ob = mesh('lifeboat', bm, (sklib.plastic((0.85, 0.32, 0.04), 0.35, name='lifeboat_orange'),), bev=0.5, seg=4)
lb_ob.rotation_euler.x = 30 * D2R
lb_ob.location = (0, -70.5, DECK + 3.4)
bm = bmesh.new()                                                                      # forecastle winches
for sx in (-1, 1):
    sklib._bm_cyl(bm, Vector((sx * 3.5, 64, deck_z(64) + 0.8)), 0.7, 1.6, 'X', 20)
    box(bm, (sx * 3.5, 64, deck_z(64) + 0.3), (2.2, 1.6, 0.6))
mesh('mooring_winches', bm, (GREY,), bev=0.02)

# ------------------------------------------------------------------------------------------------ reefer interior (A-CONT-40RF-INT), local to HERO_C
FZL, CZL = 0.22, 2.77           # T-floor top, ceiling
XU, XD = -L / 2 + 0.5, L / 2 - 0.12
YI = 1.145
INT = sklib.collection('REEFER_INT', SHIP)


def imesh(name, bm, mats, bev=0.0, seg=2):
    return mesh(name, bm, mats, parent=HERO_C, coll=INT, bev=bev, seg=seg)


ALU = sklib.aluminium(0.25)
LINER = sklib.painted_metal((0.82, 0.83, 0.82), 0.25, 0.15, 0.35)
bm = bmesh.new()
box(bm, ((XU + XD) / 2, 0, FZL - 0.03), (XD - XU, 2 * YI, 0.02), 1)
n = int(2 * YI / 0.05)
for i in range(n):
    y = -YI + 0.025 + i * 0.05
    box(bm, ((XU + XD) / 2, y, FZL - 0.015), (XD - XU, 0.008, 0.026))
    box(bm, ((XU + XD) / 2, y, FZL - 0.004), (XD - XU, 0.034, 0.008))
imesh('reefer_T_floor', bm, (ALU, RUBBER))
bm = bmesh.new()
for sy in (-1, 1):
    box(bm, ((XU + XD) / 2, sy * (YI + 0.01), (FZL + CZL) / 2), (XD - XU, 0.02, CZL - FZL + 0.04))
    for x in np.arange(XU + 0.6, XD, 1.2):                                   # panel joints / scuff rails
        box(bm, (x, sy * (YI - 0.003), (FZL + CZL) / 2), (0.03, 0.01, CZL - FZL))
    box(bm, ((XU + XD) / 2, sy * (YI - 0.01), FZL + 0.18), (XD - XU, 0.03, 0.12), 1)
box(bm, ((XU + XD) / 2, 0, CZL + 0.01), (XD - XU, 2 * YI + 0.04, 0.02))
box(bm, (XU - 0.01, 0, (FZL + CZL) / 2), (0.02, 2 * YI, CZL - FZL))
for sy in (-1, 1):                                                          # door frame lips
    box(bm, (XD - 0.02, sy * 1.11, (FZL + CZL) / 2), (0.05, 0.08, CZL - FZL), 1)
imesh('reefer_liner', bm, (LINER, ALU), bev=0.004, seg=1)
bm = bmesh.new()                                                            # evaporator return grille on the bulkhead
box(bm, (XU + 0.02, 0, CZL - 0.35), (0.04, 2.0, 0.55))
for z in np.arange(CZL - 0.58, CZL - 0.1, 0.05):
    box(bm, (XU + 0.045, 0, z), (0.015, 1.96, 0.022), 1)
imesh('reefer_evaporator_grille', bm, (GREY, ALU), bev=0.004, seg=1)
# air chute (vinyl) along the ceiling, offset to starboard of the centre
bm = bmesh.new()
prof = [(0.0, 0.0), (0.03, -0.08), (0.12, -0.12), (0.22, -0.12), (0.31, -0.08), (0.34, 0.0)]
CY0 = 0.12
rows = []
for x in np.arange(XU + 0.1, XD - 1.2, 0.25):
    sag = 0.01 * math.sin(x * 2.3)
    rows.append([bm.verts.new((x, CY0 + py, CZL + pz * (1 + sag * 3) - 0.002)) for py, pz in prof])
for a, b in zip(rows[:-1], rows[1:]):
    for i in range(len(prof) - 1):
        bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
ch = imesh('reefer_air_chute', bm, (sklib.plastic((0.82, 0.84, 0.85), 0.2, name='vinyl_chute'),))
ch.data.shade_smooth()
# LED strips + their lights (cool 6500 K)
LED = sklib.flat('led_strip', (0.9, 0.95, 1.0), 0.3, **{'Emission Color': (0.85, 0.92, 1.0, 1), 'Emission Strength': 9.0})
bm = bmesh.new()
for sy in (-0.75, 0.75):
    box(bm, ((XU + XD) / 2 - 0.3, sy, CZL - 0.012), (XD - XU - 1.2, 0.05, 0.02))
imesh('reefer_led_strips', bm, (LED,))
K65 = sklib.kelvin_rgb(6500)
for sy in (-0.75, 0.75):
    for x in (-2.8, 2.8):
        ld = bpy.data.lights.new('reefer_led', 'AREA')
        ld.shape, ld.size, ld.size_y, ld.energy, ld.color = 'RECTANGLE', 5.4, 0.12, 50.0, K65
        ld.use_shadow = False
        lo = sklib.new_obj('reefer_led_light', ld, INT, HERO_C, (x, sy, CZL - 0.03))
# cold mist volume (faint, denser low)
bm = bmesh.new()
box(bm, ((XU + XD) / 2, 0, (FZL + CZL) / 2), (XD - XU - 0.02, 2 * YI - 0.02, CZL - FZL - 0.02))
mist = imesh('reefer_cold_mist', bm, ())
mm, nt = sklib._new_mat('cold_mist')
out = sklib._n(nt, 'ShaderNodeOutputMaterial', 600, 0)
pv = sklib._n(nt, 'ShaderNodeVolumePrincipled', 300, 0)
pv.inputs['Color'].default_value = (0.86, 0.92, 1.0, 1)
tc = sklib._n(nt, 'ShaderNodeTexCoord', -600, 0)
nz = sklib._noise(nt, tc.outputs['Object'], 0.9, 3.0, 0.55, -400, 0)
den = sklib._maprange(nt, nz.outputs['Fac'], 0.35, 0.75, 0.004, 0.035, -200, 0)
sklib._l(nt, den, pv.inputs['Density'])
sklib._l(nt, pv.outputs[0], out.inputs['Volume'])
mist.data.materials.append(mm)

# pallets: 2 columns x 9 rows = 18 (front rows 4 layers, hero pallet 4 + partial layer, the rest 5 = flush load line)
P5 = sklib.carton_pallet('A-CARTON-PALLET-5', 5)
P4 = sklib.carton_pallet('A-CARTON-PALLET-4', 4)
CC = sklib.carton_closed()
HERO_ROW = 3
for k in range(9):
    x = 5.03 - 1.22 * k
    for j, y in enumerate((-0.56, 0.56)):
        c = P4 if k <= HERO_ROW else P5
        e = sklib.instance(c, (x + rng.uniform(-0.02, 0.02), y + rng.uniform(-0.015, 0.015), FZL), rng.uniform(-0.01, 0.01),
                           'I_pallet_%d_%d' % (k, j), INT)
        e.parent = HERO_C
HPX, HPY = 5.03 - 1.22 * HERO_ROW, -0.56
Z5 = FZL + 0.144 + 4 * 0.258
for (cx, cy) in ((-0.35, -0.25), (0.0, -0.25), (0.0, 0.25)):
    e = sklib.instance(CC, (HPX + cx, HPY + cy, Z5), math.pi / 2 + rng.uniform(-0.02, 0.02), 'I_top_carton', INT)
    e.parent = HERO_C
HX, HY = HPX + 0.35, HPY + 0.25
hero = sklib.hero_carton(0.0, 'A-HERO-CARTON', coll=INT, interior=False, loc=(HX, HY, Z5), rot_z=math.pi / 2 + 0.015)
hero.parent = HERO_C

# BRIDGE_FROST: frosted white poly sheet on the hero lid + soft 6500 K area light 1 m above
BF = sklib.collection('BRIDGE_FROST', SHIP)
TOPZ = sklib.CH + sklib.CT + 0.002
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=60, y_segments=44, size=0.5)
r2 = random.Random(11)
for v in bm.verts:
    x, y = v.co.x * 0.44, v.co.y * 0.30          # grid size 0.5 -> spans +-0.5
    v.co = Vector((x, y, 0.0004 + 0.00025 * math.sin(x * 37 + y * 23) * math.sin(y * 41 - x * 19)))
frost_m, nt = sklib._new_mat('frost_poly')
out = sklib._n(nt, 'ShaderNodeOutputMaterial', 1200, 0)
pb = sklib._n(nt, 'ShaderNodeBsdfPrincipled', 900, 0)
sklib._l(nt, pb.outputs[0], out.inputs['Surface'])
tc = sklib._n(nt, 'ShaderNodeTexCoord', -1100, 0)
geo = sklib._n(nt, 'ShaderNodeNewGeometry', -300, -600)
nzc = sklib._noise(nt, tc.outputs['Object'], 45.0, 6.0, 0.65, -900, 400)          # frost coverage
cov = sklib._maprange(nt, nzc.outputs['Fac'], 0.44, 0.56, 0.0, 1.0, -650, 400)
facets = []
for i, sc in enumerate((380.0, 1500.0)):                                             # plates + fine needles
    vo = sklib._n(nt, 'ShaderNodeTexVoronoi', -900, -100 - 300 * i)
    vo.inputs['Scale'].default_value = sc
    vo.inputs['Randomness'].default_value = 1.0
    sklib._l(nt, tc.outputs['Object'], vo.inputs['Vector'])
    facets.append(vo)
d0 = sklib._n(nt, 'ShaderNodeVectorMath', -600, -100, operation='SUBTRACT')
sklib._l(nt, facets[0].outputs['Color'], d0.inputs[0])
d0.inputs[1].default_value = (0.5, 0.5, 0.5)
d1 = sklib._n(nt, 'ShaderNodeVectorMath', -600, -400, operation='SUBTRACT')
sklib._l(nt, facets[1].outputs['Color'], d1.inputs[0])
d1.inputs[1].default_value = (0.5, 0.5, 0.5)
ad = sklib._n(nt, 'ShaderNodeVectorMath', -400, -250, operation='ADD')
sklib._l(nt, d0.outputs[0], ad.inputs[0])
sklib._l(nt, d1.outputs[0], ad.inputs[1])
sc_ = sklib._n(nt, 'ShaderNodeVectorMath', -200, -250, operation='SCALE')
sklib._l(nt, ad.outputs[0], sc_.inputs[0])
sklib._l(nt, sklib._maprange(nt, cov, 0, 1, 0.1, 2.4, -400, 100), sc_.inputs['Scale'])
nn = sklib._n(nt, 'ShaderNodeVectorMath', 0, -400, operation='ADD')
sklib._l(nt, sc_.outputs[0], nn.inputs[0])
sklib._l(nt, geo.outputs['Normal'], nn.inputs[1])
nrm = sklib._n(nt, 'ShaderNodeVectorMath', 200, -400, operation='NORMALIZE')
sklib._l(nt, nn.outputs[0], nrm.inputs[0])
sklib._l(nt, nrm.outputs[0], pb.inputs['Normal'])
grain = sklib._maprange(nt, facets[1].outputs['Distance'], 0.0, 0.5, 1.0, 0.45, -400, 650)
col = sklib._mix(nt, cov, (0.07, 0.085, 0.10), (0.78, 0.82, 0.86), 'MIX', -150, 450)
cm = sklib._n(nt, 'ShaderNodeVectorMath', 100, 450, operation='SCALE')
sklib._l(nt, col, cm.inputs[0])
sklib._l(nt, grain, cm.inputs['Scale'])
sklib._l(nt, cm.outputs[0], pb.inputs['Base Color'])
sklib._l(nt, sklib._maprange(nt, cov, 0, 1, 0.12, 0.35, 300, 150), pb.inputs['Roughness'])
pb.inputs['Subsurface Weight'].default_value = 0.2
pb.inputs['Subsurface Radius'].default_value = (0.002, 0.002, 0.003)
pb.inputs['Coat Weight'].default_value = 0.0
frost = sklib._mesh_obj('BRIDGE_FROST.sheet', bm, BF, hero)
frost.data.materials.append(frost_m)
frost.location = (0, 0, TOPZ)
frost.rotation_euler.z = 0.03
frost.data.shade_smooth()
fl = bpy.data.lights.new('BRIDGE_FROST.light', 'AREA')
fl.shape, fl.size, fl.energy, fl.color = 'SQUARE', 0.35, 3.0, K65
sklib.new_obj('BRIDGE_FROST.light', fl, BF, hero, (0, 0, TOPZ + 1.0))
bpy.context.view_layer.update()


def hero_S():
    """frost-sheet centre in ship space."""
    p = Vector((HX, HY, Z5 + TOPZ))
    return Vector((OX + p.y, OY - p.x, OZ + p.z))     # rot -90: local (x,y) -> S (y, -x)


# ------------------------------------------------------------------------------------------------ sea, far sea, wake foam
sea = sklib.ocean(size=20000, seed=41, time=0.0)    # 6x6 displaced 100 m tiles (+-300 m) + flat far plane, same water
om = sea.modifiers['Ocean']
for f in (F0 - 2, F1):
    om.time = (F1 - f) / 24.0                        # time = 0 at f192 (hard min 0 -> runs down to 0, constant after)
    sea.keyframe_insert('modifiers["Ocean"].time', frame=f)
for fc in sklib._fcurves(sea):
    for k in fc.keyframe_points:
        k.interpolation = 'LINEAR'
om.time = 0.0

# wake mask (ship space, painted with numpy, packed)
WX0, WX1, WY0, WY1 = -100.0, 100.0, -420.0, 140.0
IW, IH = 512, 1434
xs = np.linspace(WX0, WX1, IW)[None, :]
ys = np.linspace(WY0, WY1, IH)[:, None]
bwv = np.vectorize(b_wl)(ys)
d = np.abs(xs) - bwv
inhull = (ys > -75) & (ys < 72.5)
bowness = np.clip((ys - 35) / 35, 0, 1)
aft = np.clip((-20 - ys) / 55, 0, 1)
ws = 1.4 + 2.6 * aft + 3.0 * bowness
side = np.where(inhull & (d > -0.5), np.exp(-np.maximum(d, 0) / ws), 0) * (0.55 + 0.6 * bowness + 0.45 * aft)
r = np.sqrt(xs ** 2 + (ys - 72.0) ** 2)
cush = np.exp(-r / 6.0) * 1.0
m = np.maximum(side, cush)
SA, CA = math.sin(19.5 * D2R), math.cos(19.5 * D2R)
for sx in (-1, 1):
    for (ox, oy, w0, gw, fade, tmax, amp) in ((6.5, 66.0, 0.9, 0.06, 18.0, 50.0, 0.95), (9.0, -74.0, 1.6, 0.04, 90.0, 300.0, 0.45)):
        dx, dy = sx * SA, -CA
        px, py = xs - sx * ox, ys - oy
        t = px * dx + py * dy
        perp = np.abs(px * dy - py * dx)
        arm = np.exp(-(perp / (w0 + gw * np.maximum(t, 0))) ** 2) * np.exp(-np.maximum(t, 0) / fade) * amp
        m = np.maximum(m, np.where((t > 0) & (t < tmax), arm, 0))
tt = -75 - ys
wk = np.where(tt > -2, np.exp(-2 * (xs / (10.0 + 0.1 * np.maximum(tt, 0))) ** 2) * np.exp(-np.maximum(tt, 0) / 260) *
              np.clip((tt + 2) / 4, 0, 1), 0)
m = np.clip(np.maximum(m, wk), 0, 1).astype(np.float32)
# BRIDGE_SEA frame (ship space x 27..89, y -22..12 at f192) must be foam-free
assert m[(np.broadcast_to(ys, m.shape) > -26) & (np.broadcast_to(ys, m.shape) < 16) & (np.broadcast_to(xs, m.shape) > 24)].max() < 0.02
img = bpy.data.images.new('wake_mask', IW, IH, alpha=False, float_buffer=False)
px = np.zeros((IH, IW, 4), np.float32)
px[..., 0] = px[..., 1] = px[..., 2] = m
px[..., 3] = 1
img.pixels.foreach_set(px.ravel())
img.filepath_raw = sklib.SRC + '/blender/tex_reefer_wake_mask.png'
img.file_format = 'PNG'
img.save()
img.source = 'FILE'
img.reload()
img.colorspace_settings.name = 'Non-Color'
img.pack()

wm = sea.active_material
nt = wm.node_tree
mo = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
mx = mo.inputs['Surface'].links[0].from_node                  # foam mix (fac = foam)
foam_src = mx.inputs[0].links[0].from_socket
tc = sklib._n(nt, 'ShaderNodeTexCoord', -1500, -1100)
tc.object = ROOT
vm = sklib._n(nt, 'ShaderNodeMapping', -1300, -1100)
vm.vector_type = 'POINT'
vm.inputs['Location'].default_value = (-WX0 / (WX1 - WX0), -WY0 / (WY1 - WY0), 0)
vm.inputs['Scale'].default_value = (1 / (WX1 - WX0), 1 / (WY1 - WY0), 1)
sklib._l(nt, tc.outputs['Object'], vm.inputs['Vector'])
ti = sklib._n(nt, 'ShaderNodeTexImage', -1100, -1100)
ti.image, ti.extension, ti.interpolation = img, 'CLIP', 'Cubic'
sklib._l(nt, vm.outputs[0], ti.inputs['Vector'])
gtc = sklib._n(nt, 'ShaderNodeTexCoord', -1300, -1400)
n1 = sklib._noise(nt, gtc.outputs['Object'], 0.35, 6.0, 0.62, -1100, -1400)
n2 = sklib._noise(nt, gtc.outputs['Object'], 2.2, 4.0, 0.6, -1100, -1600)
brk = sklib._math(nt, 'MULTIPLY', sklib._maprange(nt, n1.outputs['Fac'], 0.3, 0.65, 0.55, 1.4, -900, -1400),
                  sklib._maprange(nt, n2.outputs['Fac'], 0.3, 0.7, 0.7, 1.25, -900, -1600), x=-700, y=-1500)
wake = sklib._maprange(nt, sklib._math(nt, 'MULTIPLY', ti.outputs['Color'], brk, x=-500, y=-1200), 0.08, 0.45, 0.0, 1.0, -300, -1200)
fac = sklib._math(nt, 'MAXIMUM', foam_src, wake, x=700, y=-400)
sklib._l(nt, fac, mx.inputs[0])
# distance blend (beyond ~150 m): geometric wave normals/crest colour -> shared bump normal, so the 600 m simulated
# patch and the flat far ring shade identically at the join (no effect near the camera, e.g. BRIDGE_SEA at 60 m)
cdn = sklib._n(nt, 'ShaderNodeCameraData', -1500, -1900)
dfac = sklib._maprange(nt, cdn.outputs['View Distance'], 150.0, 270.0, 0.0, 1.0, -1300, -1900)
bpn = sklib._noise(nt, sklib._vscale(nt, gtc.outputs['Object'], 0.12, 0.2, 1, -1300, -2100), 1.0, 6.0, 0.6, -1100, -2100)
bmp = sklib._n(nt, 'ShaderNodeBump', -900, -2100)
bmp.inputs['Strength'].default_value = 0.3
sklib._l(nt, bpn.outputs['Fac'], bmp.inputs['Height'])
geo2 = sklib._n(nt, 'ShaderNodeNewGeometry', -1100, -2300)
vmx = sklib._n(nt, 'ShaderNodeMix', -700, -2100)
vmx.data_type = 'VECTOR'
sklib._l(nt, dfac, vmx.inputs[0])
sklib._l(nt, geo2.outputs['Normal'], vmx.inputs[4])
sklib._l(nt, bmp.outputs[0], vmx.inputs[5])
nrz = sklib._n(nt, 'ShaderNodeVectorMath', -500, -2100, operation='NORMALIZE')
sklib._l(nt, vmx.outputs[1], nrz.inputs[0])
for n in nt.nodes:
    if n.type in ('BSDF_GLOSSY', 'FRESNEL'):
        sklib._l(nt, nrz.outputs[0], n.inputs['Normal'])


# bow spray particles (both sides, gravity, motion-blurred droplets)
drop_m = sklib.flat('spray_water', (0.85, 0.9, 0.92), 0.15, **{'Alpha': 0.6})
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
drop = sklib._mesh_obj('spray_drop', bm, False)
drop.data.materials.append(drop_m)
for sx in (-1, 1):
    bm = bmesh.new()
    box(bm, (0, 0, 0), (0.3, 14.0, 0.4))
    em = sklib._mesh_obj('bow_spray_emitter_%d' % sx, bm, SHIP, ROOT)
    em.location = (sx * 5.0, 63.0, 0.6)
    em.rotation_euler.z = -sx * 12 * D2R
    em.hide_render = False
    em.show_instancer_for_render = False
    md = em.modifiers.new('spray', 'PARTICLE_SYSTEM')
    ps = em.particle_systems[0].settings
    ps.count, ps.frame_start, ps.frame_end, ps.lifetime, ps.lifetime_random = 6000, F0 - 40, F1, 26, 0.5
    ps.emit_from, ps.use_emit_random = 'VOLUME', True
    ps.normal_factor, ps.object_align_factor = 0.0, (sx * 3.2, 0.0, 3.0)
    ps.object_factor, ps.factor_random = 0.75, 1.6
    ps.render_type, ps.instance_object = 'OBJECT', drop
    ps.particle_size, ps.size_random = 0.05, 0.7
    ps.effector_weights.gravity = 1.0
    em.data.materials.append(drop_m)

# ------------------------------------------------------------------------------------------------ gulls x4
GULL_W = sklib.flat('gull_white', (0.86, 0.86, 0.84), 0.6, var=0.05)
GULL_G = sklib.flat('gull_grey', (0.42, 0.44, 0.46), 0.6, var=0.08)
GULL_K = sklib.flat('gull_black', (0.03, 0.03, 0.03), 0.6)


def gull(name, loc, phase, drift):
    g = sklib.new_obj(name, None, SHIP, ROOT, loc)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
    bmesh.ops.scale(bm, vec=(0.075, 0.24, 0.075), verts=bm.verts[:])
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.055,
                              matrix=Matrix.Translation((0, 0.22, 0.03)))
    body = sklib._mesh_obj(name + '.body', bm, SHIP, g)
    body.data.materials.append(GULL_W)
    body.data.shade_smooth()
    for sx in (-1, 1):
        bm = bmesh.new()
        sec = [(0.0, 0.07, -0.08), (0.28, 0.06, -0.06), (0.52, 0.0, -0.02), (0.62, -0.06, 0.0)]
        vs = [(bm.verts.new((sx * x, yf, 0)), bm.verts.new((sx * x, yb, 0))) for x, yf, yb in sec]
        for (a, b), (c, dd) in zip(vs[:-1], vs[1:]):
            f = bm.faces.new((a, c, dd, b) if sx > 0 else (a, b, dd, c))
            f.material_index = 1 if abs(a.co.x) > 0.45 else 0
        wg = sklib._mesh_obj(name + '.wing', bm, SHIP, g)
        wg.data.materials.append(GULL_G)
        wg.data.materials.append(GULL_K)
        wg.modifiers.new('Solidify', 'SOLIDIFY').thickness = 0.01
        for f in range(F0 - 2, F1 + 3, 2):
            wg.rotation_euler.y = sx * 0.55 * math.sin(2 * math.pi * f / 9.0 + phase) * (0.35 if (f // 40) % 2 else 1.0)
            wg.keyframe_insert('rotation_euler', index=1, frame=f)
    for f in range(F0 - 2, F1 + 3, 6):
        a = 2 * math.pi * f / 240 + phase
        g.location = Vector(loc) + Vector((drift * math.sin(a), drift * 0.6 * math.cos(a), 0.8 * math.sin(a * 1.7)))
        g.rotation_euler = (0, -0.25 * math.cos(a), 0.15 * math.sin(a))
        g.keyframe_insert('location', frame=f)
        g.keyframe_insert('rotation_euler', frame=f)
    sklib.ease_keys(g)
    return g


for i, (p, ph, dr) in enumerate((((70.0, -66.0, 50.0), 0.0, 3.0), ((60.0, -52.0, 44.0), 1.7, 4.0),
                                 ((80.0, -58.0, 54.0), 3.1, 2.5), ((64.0, -76.0, 47.0), 4.4, 3.5))):
    gull('A-FX-GULL.%d' % i, p, ph, dr)

# ------------------------------------------------------------------------------------------------ camera (baked)
H = hero_S()
# (frame, ship-space pos, pitch deg (0 = down, 90 = level), yaw deg (0 = +Y, + = to port), lens, focus, fstop)
KEYS = [
    (1, H + Vector((0, 0, 0.12)), 0.0, 0.0, 100.0, 0.12, 2.8),
    (14, H + Vector((0, 0, 0.13)), 0.0, 0.0, 100.0, 0.17, 4.0),
    (45, Vector((H.x + 0.06, H.y - 2.05, H.z + 0.68)), 71.0, 0.0, 32.0, 2.2, 2.8),
    (75, Vector((OX - 0.10, GAP_Y1 - 0.15, OZ + FZL + 1.95)), 80.0, 0.0, 26.0, 4.6, 4.0),
    (95, Vector((OX - 0.05, GAP_C + 0.1, OZ + FZL + 2.15)), 82.0, 0.0, 24.0, 1.7, 4.0),
    (118, Vector((OX + 0.3, GAP_C - 0.8, FZ + HR + 4.5)), 72.0, 0.0, 24.0, 14.0, 8.0),
    (150, Vector((95.0, -95.0, 65.0)), 77.0, 47.0, 24.0, 140.0, 11.0),
    (192, None, 0.0, 0.0, 35.0, 60.0, 11.0),
]
WEND = Vector((0.0, 0.0, 60.0))
KEYS[-1] = (192, WEND - root_m(192).to_translation(), 0.0, 0.0, 35.0, 60.0, 11.0)


def pchip(xk, yk, x):
    """Monotone cubic (Fritsch-Carlson/Butland), zero end slopes -> eased, no overshoot."""
    xk, yk = np.asarray(xk, float), np.asarray(yk, float)
    h = np.diff(xk)
    dk = np.diff(yk) / h
    m = np.zeros_like(yk)
    for i in range(1, len(xk) - 1):
        if dk[i - 1] * dk[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dk[i - 1] + w2 / dk[i])
    x = min(max(x, xk[0]), xk[-1])
    i = min(np.searchsorted(xk, x, side='right') - 1, len(xk) - 2)
    t = (x - xk[i]) / h[i]
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * yk[i] + h10 * h[i] * m[i] + h01 * yk[i + 1] + h11 * h[i] * m[i + 1]


assert abs(pchip([0, 1, 3], [0, 2, 1], 1.0) - 2) < 1e-9 and 0 <= pchip([0, 1, 3], [0, 2, 1], 2.0) <= 2

kf = [k[0] for k in KEYS]


def chan(i, f, world=False):
    if world:
        vals = [(root_m(k[0]) @ k[1])[i] for k in KEYS]
    else:
        vals = [k[1][i] for k in KEYS]
    return pchip(kf, vals, f)


cd = bpy.data.cameras.new('CAM')
cam = sklib.new_obj('CAM', cd)
s.camera = cam
cd.sensor_width, cd.dof.use_dof = 36.0, True
prev = None
for f in range(F0 - 1, F1 + 2):
    fc_ = min(max(f, F0), F1)
    pS = Vector([chan(i, fc_) for i in range(3)])
    pW = Vector([chan(i, fc_, True) for i in range(3)])
    w = 1.0 - min(1, max(0, (fc_ - 100) / 30.0))
    w = w * w * (3 - 2 * w)
    Mm = motion_m(fc_, w)
    a = min(1, max(0, (fc_ - 105) / 20.0))
    a = a * a * (3 - 2 * a)
    pitch = pchip(kf, [k[2] for k in KEYS], fc_) * D2R
    yaw = pchip(kf, [k[3] for k in KEYS], fc_) * D2R
    R = Euler((pitch, 0, yaw), 'XYZ').to_matrix().to_4x4()
    Mw_S = root_m(fc_) @ Mm @ Matrix.Translation(pS) @ R
    loc = Mw_S.to_translation().lerp(pW, a)
    rot = Mw_S.to_euler('XYZ', prev) if prev else Mw_S.to_euler('XYZ')
    prev = rot
    cam.location, cam.rotation_euler = loc, rot
    cam.keyframe_insert('location', frame=f)
    cam.keyframe_insert('rotation_euler', frame=f)
    cd.lens = pchip(kf, [k[4] for k in KEYS], fc_)
    cd.dof.focus_distance = math.exp(pchip(kf, [math.log(k[5]) for k in KEYS], fc_))
    cd.dof.aperture_fstop = pchip(kf, [k[6] for k in KEYS], fc_)
    cd.clip_start = 0.01 if fc_ < 90 else 0.3
    cd.clip_end = 25000.0
    for p in ('lens', 'dof.focus_distance', 'dof.aperture_fstop', 'clip_start', 'clip_end'):
        cd.keyframe_insert(p, frame=f)
    # clearance check against the stacked boxes (ship space, while the camera is on the ship)
    if fc_ < 125:
        for (bi, ri), col in stacks.items():
            for z0, hh, kind in col:
                if kind == 'hero':
                    continue
                if abs(pS.x - ROW_X[ri]) < 1.3 and abs(pS.y - BAY_Y[bi]) < 6.2 and z0 - 0.1 < pS.z < z0 + hh + 0.1:
                    print('WARN camera inside container', f, bi, ri, z0)
for idb in (cam, cd):
    for fc in sklib._fcurves(idb):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
# exactness of the bridges
s.frame_set(F1)
assert (cam.matrix_world.to_translation() - WEND).length < 1e-3, cam.matrix_world.to_translation()

# ------------------------------------------------------------------------------------------------ render settings
sklib.finish('reefer', 'ext')
e = s.eevee
e.volumetric_tile_size, e.volumetric_samples, e.volumetric_end = '16', 32, 30.0
e.use_volumetric_shadows = True
s.frame_set(F0)
sklib.finish('reefer', 'ext')
