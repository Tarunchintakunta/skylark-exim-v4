"""S4 sea.blend -> clip v-sea (frames 1-264, 11 s, kind dawn).  docs/SCENES.md S4, docs/STORYBOARD.md 01 v-sea.

Dawn sea off the Vizag coast: a Vizag-style mechanised fishing boat (painted wooden hull in blue/white/red bands,
wheelhouse, mast with plain flags, net drum, tyre fenders, stern A-frame, ice-hold hatch) rocking on the swell,
cod-end hauled up the A-frame and dripping, catch on crushed ice in crates (CC0 ffish.asia scans), 6 MPFB crew,
2 fishing boats + 1 small boat on the horizon, headland silhouette, 8 gulls.

f1    = BRIDGE_HORIZON (sunrise sea horizon at 46 % height, lens 35, camera 3 m up, sun 4 deg at az 95, ocean seed 41)
f1-80 fly low toward the boat  | f80-160 circle the stern while the net comes up | f160-210 deck beat (crates,
gloved hands) | f210-264 pull back to the crew portrait at the starboard rail, backlit by the sun (poster frame).

World: X east, Y north. Boat local frame: +Y bow, +X starboard; the boat sits at BOAT_XY heading south (rot 180),
so its starboard side faces west (camera side at the end, sun behind the crew).
Run: Blender --factory-startup -b --python sea.py     (needs assets-src/models/sea-scans.blend from sea_scans.py)
"""
import math
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

REPO = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4'
sys.path.insert(0, REPO + '/assets-src/blender/lib')
import sklib  # noqa: E402
from sklib import _n, _l, _math, _mix, _maprange, _noise, _vscale, _img, _dirt_mask, D2R  # noqa: E402

sklib.reset()
import people  # noqa: E402  (enables MPFB)

S = bpy.context.scene
BOAT_XY = Vector((42.0, -42.0))
L, BM = 15.0, 2.25            # hull length, max half beam (m)
BULW = 0.75                   # bulwark height above deck
rng = random.Random(41)


def W(lx, ly, lz):
    """boat-local (rest) -> world (boat heading south)"""
    return Vector((BOAT_XY.x - lx, BOAT_XY.y - ly, lz))


# ===================================================================================================== hull shape
def _t(y):
    return min(1.0, max(0.0, (y + L / 2) / L))


def half_beam(t):
    if t < 0.62:
        return BM * (1 - 0.16 * ((0.62 - t) / 0.62) ** 2)
    u = (t - 0.62) / 0.38
    return BM * max(0.0, 1 - u ** 1.8) ** 0.75


def sheer(t):
    return 1.22 + 0.10 * (1 - t / 0.5) ** 2 if t < 0.5 else 1.22 + 0.85 * ((t - 0.5) / 0.5) ** 2


def keel(t):
    if t < 0.2:
        return 0.9 + 0.4 * (t / 0.2)
    if t > 0.7:
        return 1.3 - 1.0 * ((t - 0.7) / 0.3) ** 1.5
    return 1.3


def pexp(t):
    return 3.0 - 1.4 * t


def sec(t, v):
    """section point (x>=0, z) at station t, v 0 = gunwale .. 1 = keel"""
    zs, d, b, p = sheer(t), keel(t), half_beam(t), pexp(t)
    return b * (1 - v ** p) * (1 + 0.03 * (1 - v)), zs - (zs + d) * v


def deck_z(y):
    return sheer(_t(y)) - BULW


def deck_half(y, inset=0.07):
    t = _t(y)
    zs, d = sheer(t), keel(t)
    v = BULW / (zs + d)
    return max(0.0, half_beam(t) * (1 - v ** pexp(t)) * (1 + 0.03 * (1 - v)) - inset)


def hull_x_at(y, z):
    """outer hull half-width at height z (bisection on v)"""
    t = _t(y)
    lo, hi = 0.0, 1.0
    for _ in range(30):
        m = (lo + hi) / 2
        if sec(t, m)[1] > z:
            lo = m
        else:
            hi = m
    return sec(t, lo)[0]


# ===================================================================================================== materials
def hull_paint():
    """Painted planked wooden hull: bands by height (red antifouling, white boot-top, blue topsides, red stripe, white
    sheer band), plank seams, chipped paint showing grey wood, rust streaks from fittings, waterline grime."""
    m = bpy.data.materials.get('sea_hull_paint')
    if m:
        return m
    t = sklib.tex('wood_planks_grey')
    m, nt = sklib._new_mat('sea_hull_paint')
    out = _n(nt, 'ShaderNodeOutputMaterial', 1600, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 1300, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -1600, 0)
    k = 1.0 / t['size_m']
    uv = _vscale(nt, tc.outputs['UV'], k, k, k, -1400, 0)
    wood = _img(nt, t['diff'], True, uv, -1100, 400)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -1400, -400)
    _l(nt, tc.outputs['Object'], sep.inputs[0])
    z = sep.outputs['Z']
    ramp = _n(nt, 'ShaderNodeValToRGB', -900, -300)
    _l(nt, _maprange(nt, z, -1.5, 2.5, 0, 1, -1100, -300), ramp.inputs[0])
    cr = ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    zs = lambda zz: (zz + 1.5) / 4.0
    stops = [(0.0, (0.30, 0.05, 0.035)), (zs(0.02), (0.78, 0.78, 0.74)), (zs(0.2), (0.025, 0.16, 0.42)),
             (zs(0.98), (0.55, 0.05, 0.035)), (zs(1.06), (0.80, 0.80, 0.76)), (zs(1.95), (0.035, 0.18, 0.46))]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], stops[0][1] + (1,)
    cr.elements[1].position, cr.elements[1].color = stops[1][0], stops[1][1] + (1,)
    for pos, c in stops[2:]:
        e = cr.elements.new(pos)
        e.color = c + (1,)
    paint = ramp.outputs['Color']
    # brush/fade variation on the paint
    nv = _noise(nt, tc.outputs['Object'], 1.2, 6.0, 0.55, -900, 0)
    paint = _mix(nt, _maprange(nt, nv.outputs['Fac'], 0.35, 0.7, 0.0, 0.35, -700, 0), paint,
                 (0.55, 0.55, 0.52), 'MULTIPLY', -500, -100)
    # chipped paint -> wood
    chip_n = _noise(nt, tc.outputs['Object'], 9.0, 10.0, 0.7, -900, 600)
    chip = _maprange(nt, chip_n.outputs['Fac'], 0.63, 0.67, 0.0, 1.0, -700, 600)
    woodc = _mix(nt, 0.4, wood.outputs['Color'], (0.25, 0.22, 0.18), 'MULTIPLY', -700, 450)
    col = _mix(nt, chip, paint, woodc, 'MIX', -300, 200)
    # rust streaks running down from the gunwale fittings
    ns = _noise(nt, _vscale(nt, tc.outputs['Object'], 9, 9, 0.35, -1100, 900), 3.5, 6.0, 0.55, -900, 900)
    zfade = _maprange(nt, z, 0.2, 1.3, 0.0, 1.0, -700, 1050)
    sm = _math(nt, 'MULTIPLY', _maprange(nt, ns.outputs['Fac'], 0.58, 0.74, 0.0, 0.7, -700, 900), zfade, x=-500, y=900)
    col = _mix(nt, sm, col, (0.28, 0.12, 0.05), 'MIX', -100, 400)
    # waterline grime (algae/oil) band
    wl = _math(nt, 'MULTIPLY', _maprange(nt, z, -0.1, 0.05, 0.0, 1.0, -700, -700),
               _maprange(nt, z, 0.35, 0.08, 0.0, 1.0, -700, -850), x=-500, y=-750)
    gn = _noise(nt, tc.outputs['Object'], 5.0, 8.0, 0.6, -700, -1000)
    wl = _math(nt, 'MULTIPLY', wl, _maprange(nt, gn.outputs['Fac'], 0.35, 0.6, 0.25, 0.9, -500, -1000), x=-300, y=-800)
    col = _mix(nt, wl, col, (0.10, 0.11, 0.06), 'MIX', 100, 300)
    mask = _dirt_mask(nt, 0.7, 0.3, -900, -1300)
    col = _mix(nt, mask, col, (0.17, 0.14, 0.10), 'MIX', 300, 300)
    _l(nt, col, b.inputs['Base Color'])
    ri = _img(nt, t['rough'], False, uv, -1100, 100)
    r = _maprange(nt, ri.outputs['Color'], 0, 1, 0.32, 0.6, -800, 100)
    r = _math(nt, 'MAXIMUM', r, _math(nt, 'MULTIPLY', chip, 0.85, x=300, y=-100), x=500, y=0)
    _l(nt, r, b.inputs['Roughness'])
    # plank seams every 0.19 m (horizontal planking) + wood normal
    wv = _n(nt, 'ShaderNodeTexWave', -900, -500, wave_type='BANDS', bands_direction='Z', wave_profile='SAW')
    wv.inputs['Scale'].default_value = 1.0 / 0.19 / 1.0
    wv.inputs['Distortion'].default_value = 0.4
    _l(nt, tc.outputs['Object'], wv.inputs['Vector'])
    seam = _maprange(nt, wv.outputs['Fac'], 0.0, 0.06, 0.0, 1.0, -700, -500)
    ni = _img(nt, t['nor'], False, uv, -1100, -150)
    nm = _n(nt, 'ShaderNodeNormalMap', -500, -300)
    nm.inputs['Strength'].default_value = 0.5
    _l(nt, ni.outputs['Color'], nm.inputs['Color'])
    bp = _n(nt, 'ShaderNodeBump', 900, -400)
    bp.inputs['Strength'].default_value = 0.6
    bp.inputs['Distance'].default_value = 0.004
    _l(nt, _math(nt, 'ADD', seam, _math(nt, 'MULTIPLY', chip, -0.6, x=500, y=-650), x=700, y=-500), bp.inputs['Height'])
    _l(nt, nm.outputs[0], bp.inputs['Normal'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    return m


def wet_deck():
    """Worn grey working-deck planks (not teak), soaked: puddles with mirror-like roughness + darker wet wood."""
    m = bpy.data.materials.get('sea_wet_deck')
    if m:
        return m
    t = sklib.tex('wood_planks_grey')
    m, nt = sklib._new_mat('sea_wet_deck')
    out = _n(nt, 'ShaderNodeOutputMaterial', 1400, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 1100, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -1400, 0)
    k = 1.0 / t['size_m']
    uv = _vscale(nt, tc.outputs['UV'], k, k, k, -1200, 0)
    di = _img(nt, t['diff'], True, uv, -900, 300)
    pn = _noise(nt, tc.outputs['Object'], 0.9, 4.0, 0.5, -900, -600)
    pud = _maprange(nt, pn.outputs['Fac'], 0.5, 0.56, 0.0, 1.0, -700, -600)
    col = _mix(nt, 0.35, di.outputs['Color'], (0.42, 0.40, 0.36), 'MULTIPLY', -600, 300)
    mask = _dirt_mask(nt, 0.5, 0.25, -900, -900)
    col = _mix(nt, mask, col, (0.12, 0.10, 0.08), 'MIX', -400, 300)
    col = _mix(nt, _maprange(nt, pud, 0, 1, 0.45, 0.75, -400, 100), col, (0.0, 0.0, 0.0), 'MIX', -200, 300)
    _l(nt, col, b.inputs['Base Color'])
    ri = _img(nt, t['rough'], False, uv, -900, 0)
    r = _maprange(nt, ri.outputs['Color'], 0, 1, 0.22, 0.45, -600, 0)
    r = _math(nt, 'MULTIPLY', r, _maprange(nt, pud, 0, 1, 1.0, 0.0, -200, -100), x=0, y=0)
    r = _math(nt, 'MULTIPLY_ADD', pud, 0.02, x=200, y=0, c=r)
    _l(nt, r, b.inputs['Roughness'])
    b.inputs['Coat Weight'].default_value = 0.6
    b.inputs['Coat Roughness'].default_value = 0.08
    ni = _img(nt, t['nor'], False, uv, -900, -300)
    nm = _n(nt, 'ShaderNodeNormalMap', -600, -300)
    _l(nt, ni.outputs['Color'], nm.inputs['Color'])
    _l(nt, _maprange(nt, pud, 0, 1, 1.0, 0.1, -400, -400), nm.inputs['Strength'])
    _l(nt, nm.outputs[0], b.inputs['Normal'])
    return m


def net_mat(color=(0.06, 0.30, 0.22), cell=0.06, twine=0.075, name='sea_net'):
    """Diamond-mesh netting: opacity map from the UVs (metres) -> twine lines; transparent in the meshes."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 1400, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 900, 100)
    b.inputs['Base Color'].default_value = color + (1,)
    b.inputs['Roughness'].default_value = 0.45
    b.inputs['Coat Weight'].default_value = 0.5        # wet twine
    b.inputs['Sheen Weight'].default_value = 0.3
    tc = _n(nt, 'ShaderNodeTexCoord', -1200, 0)
    sp = _n(nt, 'ShaderNodeSeparateXYZ', -1000, 0)
    _l(nt, tc.outputs['UV'], sp.inputs[0])
    u, v = sp.outputs['X'], sp.outputs['Y']
    a = _math(nt, 'MULTIPLY', _math(nt, 'ADD', u, v, x=-800, y=100), 1.0 / cell, x=-600, y=100)
    c = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', u, v, x=-800, y=-100), 1.0 / cell, x=-600, y=-100)

    def line(s, y):
        f = _math(nt, 'FRACT', s, x=-400, y=y)
        d = _math(nt, 'MINIMUM', f, _math(nt, 'SUBTRACT', 1.0, f, x=-250, y=y - 60), x=-100, y=y)
        return _maprange(nt, d, twine * 0.5, twine * 0.5 + 0.04, 1.0, 0.0, 100, y)
    alpha = _math(nt, 'MAXIMUM', line(a, 100), line(c, -150), x=300, y=0)
    tr = _n(nt, 'ShaderNodeBsdfTransparent', 900, -200)
    mx = _n(nt, 'ShaderNodeMixShader', 1150, 0)
    _l(nt, alpha, mx.inputs[0])
    _l(nt, tr.outputs[0], mx.inputs[1])
    _l(nt, b.outputs[0], mx.inputs[2])
    _l(nt, mx.outputs[0], out.inputs['Surface'])
    bp = _n(nt, 'ShaderNodeBump', 600, -300)
    bp.inputs['Strength'].default_value = 0.7
    _l(nt, alpha, bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        pass
    return m


def rope_mat(color, name):
    return sklib.flat(name, color, rough=0.75, var=0.15, scale=300.0, bump=0.4, **{'Sheen Weight': 0.3})


def tyre_mat():
    return sklib.pbr('sea_tyre', 'asphalt_02', tint=(0.035, 0.035, 0.035), rough=(0.55, 0.9), wear=0.35,
                     wear_color=(0.18, 0.16, 0.13), nor=0.8, scale=0.3, contrast=0.4)


def glass_mat():
    m = sklib.flat('sea_glass', (0.025, 0.03, 0.035), rough=0.06, var=0.02, scale=8.0)
    m.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.6 if 'Principled BSDF' in m.node_tree.nodes else 0
    return m


def flag_mat(color, name):
    return sklib.flat(name, color, rough=0.7, var=0.12, scale=60.0, bump=0.2, **{'Sheen Weight': 0.5})


# ===================================================================================================== builders
BOAT_PARTS = []          # objects instanced for the distant boats


def obj_from_bm(name, bm, mat=None, coll=None, parent=None):
    ob = sklib._mesh_obj(name, bm, coll)
    if mat:
        sklib.mat_to(ob, mat)
    if parent:
        ob.parent = parent
    return ob


def build_hull(coll, root, scale=1.0, mat=None, deck_mat=None, name='A-VESSEL-FISHING-A'):
    NS, NV = 64, 18
    bm = bmesh.new()
    rows = []
    for i in range(NS + 1):
        t = i / NS
        y = -L / 2 + t * L
        ring = []
        pts = [sec(t, j / NV) for j in range(NV + 1)]
        for x, z in pts:                       # starboard gunwale -> keel
            ring.append(bm.verts.new((x, y, z)))
        for x, z in reversed(pts[:-1]):        # keel -> port gunwale
            ring.append(bm.verts.new((-x, y, z)))
        rows.append(ring)
    for i in range(NS):
        a, c = rows[i], rows[i + 1]
        for j in range(len(a) - 1):
            try:
                bm.faces.new((a[j], c[j], c[j + 1], a[j + 1]))
            except ValueError:
                pass
    # transom
    try:
        bm.faces.new(list(reversed(rows[0])))
    except ValueError:
        pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    hull = obj_from_bm(name + '-HULL', bm, mat or hull_paint(), coll, root)
    so = hull.modifiers.new('Solidify', 'SOLIDIFY')
    so.thickness, so.offset = 0.06, -1
    hull.data.shade_smooth()
    hull.data.set_sharp_from_angle(angle=40 * D2R)
    hull.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL').keep_sharp = True
    # deck
    bm = bmesh.new()
    NY, NX = 60, 10
    grid = []
    for i in range(NY + 1):
        y = -L / 2 + 0.06 + (L - 0.4) * i / NY
        hw = deck_half(y)
        z0 = deck_z(y)
        grid.append([bm.verts.new((hw * (2 * j / NX - 1), y, z0 + 0.03 * (1 - (2 * j / NX - 1) ** 2)))
                     for j in range(NX + 1)])
    for i in range(NY):
        for j in range(NX):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    deck = obj_from_bm(name + '-DECK', bm, deck_mat or wet_deck(), coll, root)
    so = deck.modifiers.new('Solidify', 'SOLIDIFY')
    so.thickness, so.offset = 0.06, -1
    # gunwale caps + rubbing strakes (tubes along the sheer)
    caps = []
    for side in (1, -1):
        for dz, r in ((0.0, 0.06), (-0.42, 0.045), (-0.95, 0.04)):
            pts = []
            for i in range(0, 61):
                t = 0.003 + 0.992 * i / 60
                y = -L / 2 + t * L
                z = sheer(t) + dz
                x = hull_x_at(y, z) + (0.0 if dz == 0 else r * 0.6)
                pts.append((side * x, y, z))
            caps.append(tube(name + '-STRAKE', pts, r, hull_paint() if dz else sklib.painted_metal((0.55, 0.05, 0.035), 0.5, 0.3), coll, root, sides=8))
    return hull, deck, caps


def tube(name, pts, r, mat, coll, parent, sides=10, cap=True):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth, cu.bevel_resolution = r, max(1, sides // 4 - 1)
    cu.use_fill_caps = cap
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (c[0], c[1], c[2], 1)
    ob = bpy.data.objects.new(name, cu)
    (coll or S.collection).objects.link(ob)
    ob.parent = parent
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob2 = bpy.data.objects.new(name, me)
    (coll or S.collection).objects.link(ob2)
    ob2.parent = parent
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    me.shade_smooth()
    sklib.mat_to(ob2, mat)
    return ob2


def box(name, c, size, mat, coll, parent, bev=0.015, rot=(0, 0, 0)):
    bm = bmesh.new()
    sklib._bm_box(bm, Vector((0, 0, 0)), size)
    ob = obj_from_bm(name, bm, None, coll, parent)
    ob.location, ob.rotation_euler = c, rot
    sklib.mat_to(ob, mat)
    sklib.bevel(ob, bev, 2)
    return ob


def cyl(name, c, r, h, mat, coll, parent, axis='Z', seg=24, r2=None, bev=0.01):
    bm = bmesh.new()
    sklib._bm_cyl(bm, Vector((0, 0, 0)), r, h, axis=axis, seg=seg, r2=r2)
    ob = obj_from_bm(name, bm, None, coll, parent)
    ob.location = c
    sklib.mat_to(ob, mat)
    sklib.bevel(ob, bev, 2)
    return ob


def build_superstructure(coll, root, name='A-VESSEL-FISHING-A'):
    white = sklib.painted_metal((0.80, 0.80, 0.76), wear=0.45, streaks=0.45)
    blue = sklib.painted_metal((0.03, 0.17, 0.45), wear=0.5, streaks=0.3)
    red = sklib.painted_metal((0.50, 0.05, 0.035), wear=0.55, streaks=0.4)
    yel = sklib.painted_metal((0.75, 0.55, 0.12), wear=0.55, streaks=0.5)
    rust = sklib.rusty_metal(0.4)
    gl = glass_mat()
    out = []
    # ---- wheelhouse (y 1.8 .. 4.6)
    y0, y1, hw, h = 1.8, 4.6, 1.25, 2.15
    zb = deck_z(y1) - 0.05
    zc = deck_z(y0)
    out.append(box(name + '-WHEELHOUSE', (0, (y0 + y1) / 2, zb + h / 2 - (zb - zc) / 2 - 0.15),
                   (2 * hw, y1 - y0, h + (zb - zc) + 0.3), white, coll, root, 0.03))
    top = zb + h - 0.15
    out.append(box(name + '-WH-ROOF', (0, (y0 + y1) / 2 + 0.05, top + 0.05), (2 * hw + 0.3, y1 - y0 + 0.45, 0.1), blue, coll, root, 0.02))
    out.append(box(name + '-WH-BAND', (0, (y0 + y1) / 2, top - 0.12), (2 * hw + 0.02, y1 - y0 + 0.02, 0.14), blue, coll, root, 0.01))
    # windows: front (+y), sides, rear door
    wz = top - 0.65
    for k in range(3):
        x = (k - 1) * 0.78
        out.append(box(name + '-WIN', (x, y1 + 0.005, wz), (0.62, 0.03, 0.62), gl, coll, root, 0.008))
        out.append(box(name + '-WINF', (x, y1 + 0.012, wz), (0.7, 0.02, 0.7), blue, coll, root, 0.008))
    for s in (1, -1):
        for k in range(2):
            y = y0 + 0.75 + k * 1.15
            out.append(box(name + '-WIN', (s * (hw + 0.005), y, wz), (0.03, 0.75, 0.55), gl, coll, root, 0.008))
            out.append(box(name + '-WINF', (s * (hw + 0.012), y, wz), (0.02, 0.83, 0.63), blue, coll, root, 0.008))
    out.append(box(name + '-WH-DOOR', (0.5, y0 - 0.01, zc + 0.95), (0.7, 0.04, 1.75), blue, coll, root, 0.01))
    out.append(box(name + '-WH-DOORWIN', (0.5, y0 - 0.03, zc + 1.45), (0.4, 0.02, 0.4), gl, coll, root, 0.005))
    # roof rail + searchlight + horn box
    rail = []
    for s in (1, -1):
        rail.append(tube(name + '-ROOFRAIL', [(s * hw, y0 + 0.1, top + 0.1), (s * hw, y0 + 0.1, top + 0.55),
                                              (s * hw, y1, top + 0.55), (s * hw, y1, top + 0.1)], 0.02, yel, coll, root, 6))
    out += rail
    out.append(cyl(name + '-LAMP', (0.6, y1 - 0.4, top + 0.25), 0.12, 0.25, sklib.stainless(0.3), coll, root))
    # ---- mast (y 5.3) + crosstree + stays + flags
    my = 5.3
    mz = deck_z(my)
    out.append(cyl(name + '-MAST', (0, my, mz + 3.4), 0.085, 6.8, yel, coll, root, r2=0.055, seg=16))
    out.append(cyl(name + '-CROSSTREE', (0, my, mz + 5.0), 0.04, 1.6, yel, coll, root, axis='X', seg=10))
    mtop = Vector((0, my, mz + 6.8))
    wire = rope_mat((0.12, 0.11, 0.1), 'sea_wire')
    for p in [(0, 7.45, sheer(1.0) - 0.05), (-1.6, 3.0, sheer(_t(3.0)) - 0.05), (1.6, 3.0, sheer(_t(3.0)) - 0.05)]:
        out.append(tube(name + '-STAY', [tuple(mtop), p], 0.008, wire, coll, root, 4, cap=False))
    # bunting: plain coloured flags from the mast top to the stern A-frame top (no symbols, no text)
    a = mtop
    bpt = Vector((0.9, 4.75, deck_z(4.6) + 2.15))
    cols = [(0.75, 0.05, 0.03), (0.85, 0.55, 0.02), (0.05, 0.4, 0.12), (0.7, 0.7, 0.68), (0.85, 0.25, 0.02),
            (0.05, 0.2, 0.6)]
    nflags = 7
    for i in range(1, nflags):
        f = i / nflags
        p = a.lerp(bpt, f) + Vector((0, 0, -0.5 * math.sin(math.pi * f)))
        out.append(flag(name + '-FLAG', p, 0.32, 0.22, flag_mat(cols[i % len(cols)], 'sea_flag_%d' % (i % len(cols))),
                        coll, root, phase=i * 0.7))
    out.append(flag(name + '-MASTFLAG', mtop + Vector((0, 0, -0.3)), 0.9, 0.55, flag_mat((0.75, 0.05, 0.03), 'sea_flag_0'),
                    coll, root, phase=0.0, big=True))
    # ---- net drum (y 0.7) on red stands
    dy, dz = 0.75, deck_z(0.75) + 0.8
    out.append(cyl(name + '-DRUM-CORE', (0, dy, dz), 0.22, 2.0, rust, coll, root, axis='X'))
    netwound = sklib.flat('sea_net_wound', (0.05, 0.26, 0.19), rough=0.8, var=0.25, scale=180.0, bump=0.9,
                          **{'Sheen Weight': 0.4})
    out.append(cyl(name + '-DRUM-NET', (0, dy, dz), 0.5, 1.7, netwound, coll, root, axis='X', seg=32, bev=0.08))
    for s in (1, -1):
        out.append(cyl(name + '-DRUM-FLANGE', (s * 0.92, dy, dz), 0.62, 0.05, red, coll, root, axis='X', seg=32))
        out.append(box(name + '-DRUM-STAND', (s * 1.02, dy, (dz + deck_z(dy)) / 2), (0.1, 0.5, dz - deck_z(dy) + 0.1),
                       red, coll, root, 0.01))
    out.append(cyl(name + '-DRUM-MOTOR', (1.15, dy, dz), 0.17, 0.3, sklib.painted_metal((0.08, 0.3, 0.12), 0.5, 0.4),
                   coll, root, axis='X'))
    # ---- stern A-frame (legs at y -7.2 leaning aft to the head at y -8.4)
    az0, ah = deck_z(-7.2), 3.0
    for s in (1, -1):
        out.append(tube(name + '-AFRAME', [(s * 1.6, -7.15, az0 - 0.05), (s * 1.45, -8.4, az0 + ah)], 0.07, red, coll, root, 10))
    out.append(tube(name + '-AFRAME', [(-1.45, -8.4, az0 + ah), (1.45, -8.4, az0 + ah)], 0.075, red, coll, root, 10))
    out.append(cyl(name + '-BLOCK', (0, -8.4, az0 + ah - 0.18), 0.16, 0.12, rust, coll, root, axis='X'))
    out.append(cyl(name + '-ROLLER', (0, -7.55, sheer(0.0) + 0.05), 0.11, 1.4, rust, coll, root, axis='X'))
    # ---- ice-hold hatch (port side)
    hz = deck_z(-3.0)
    out.append(box(name + '-HATCH-COAMING', (-0.75, -3.0, hz + 0.15), (1.0, 1.0, 0.32), blue, coll, root, 0.02))
    out.append(box(name + '-HATCH-LID', (-0.75, -3.0, hz + 0.33), (1.08, 1.08, 0.06), white, coll, root, 0.015))
    # ---- tyre fenders (starboard + port) hung from the gunwale
    tm = tyre_mat()
    rope = rope_mat((0.75, 0.6, 0.1), 'sea_rope_yellow')
    for s in (1, -1):
        for y in (-5.2, -2.6, 0.0, 2.6, 4.4):
            z = sheer(_t(y)) - 0.55
            x = hull_x_at(y, z) + 0.1
            bm = bmesh.new()
            bmesh.ops.create_circle(bm, segments=1, radius=0.1)
            bm.free()
            bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.1, major_segments=28, minor_segments=10)
            ty = bpy.context.object
            ty.name = name + '-TYRE'
            for c in ty.users_collection:
                c.objects.unlink(ty)
            coll.objects.link(ty)
            ty.parent = root
            ty.location = (s * x, y, z)
            ty.rotation_euler = (0, math.pi / 2 + s * 0.12, 0)
            ty.scale = (1, 1, 1.15)
            sklib.mat_to(ty, tm)
            ty.data.shade_smooth()
            out.append(ty)
            out.append(tube(name + '-TYRE-ROPE', [(s * x, y, z + 0.3), (s * (hull_x_at(y, sheer(_t(y))) - 0.02), y, sheer(_t(y)) + 0.04)],
                            0.012, rope, coll, root, 5))
    # ---- deck clutter: plastic drum, rope coil, fish baskets
    out.append(cyl(name + '-BARREL', (-1.2, -1.2, deck_z(-1.2) + 0.45), 0.29, 0.9, sklib.plastic((0.04, 0.2, 0.55), 0.4), coll, root, seg=24))
    for k in range(5):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.32 - k * 0.025, minor_radius=0.025, major_segments=24, minor_segments=6,
                                         location=(-1.0, 0.0 + 0.0, deck_z(0) + 0.03 + k * 0.045))
        rc = bpy.context.object
        rc.name = name + '-ROPECOIL'
        for c in rc.users_collection:
            c.objects.unlink(rc)
        coll.objects.link(rc)
        rc.parent = root
        rc.location.y = -1.95
        sklib.mat_to(rc, rope_mat((0.08, 0.25, 0.5), 'sea_rope_blue'))
        rc.data.shade_smooth()
        out.append(rc)
    return out


def flag(name, p, w, h, mat, coll, parent, phase=0.0, big=False):
    bm = bmesh.new()
    nx, ny = (10, 6)
    g = [[bm.verts.new((0, -x / nx * w, -y / ny * h)) for x in range(nx + 1)] for y in range(ny + 1)]
    for y in range(ny):
        for x in range(nx):
            bm.faces.new((g[y][x], g[y][x + 1], g[y + 1][x + 1], g[y + 1][x]))
    ob = obj_from_bm(name, bm, None, coll, parent)
    ob.location = p
    ob.rotation_euler = (0, 0, rng.uniform(-0.25, 0.25) + (math.pi if not big else 0))
    sklib.mat_to(ob, mat)
    wv = ob.modifiers.new('Wave', 'WAVE')
    wv.use_x, wv.use_y = False, True
    wv.use_normal = False
    wv.height, wv.width, wv.speed = 0.03 if not big else 0.06, 0.18 if not big else 0.4, 0.12
    wv.time_offset = -phase * 10
    wv.start_position_y = 0.0
    wv.falloff_radius = 0
    so = ob.modifiers.new('Solidify', 'SOLIDIFY')
    so.thickness = 0.003
    ob.data.shade_smooth()
    return ob


# ===================================================================================================== scans / catch
SCANS = {}


def load_scans():
    with bpy.data.libraries.load(REPO + '/assets-src/models/sea-scans.blend') as (a, b):
        b.objects = [n for n in a.objects if n.startswith('SCAN_')]
    for o in b.objects:
        SCANS[o.name[5:]] = o
        for ms in o.material_slots:     # wet, glossy catch
            mt = ms.material
            if mt and mt.node_tree:
                bs = next((n for n in mt.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
                if bs:
                    bs.inputs['Coat Weight'].default_value = 0.7
                    bs.inputs['Coat Roughness'].default_value = 0.08
    return SCANS


def place_scan(kind, loc, rz, coll, parent, flip=False, s=1.0, tilt=0.0):
    src = SCANS[kind]
    ob = bpy.data.objects.new('CATCH-' + kind, src.data)
    coll.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = (math.pi if flip else 0.0) + tilt, 0, rz
    ob.scale = (s, s, s)
    if flip:
        ob.location.z += src.dimensions.z * s
    return ob


def fill_crate_fish(cr, kind, n, coll, parent, seed):
    """fish lying on their side on the ice, packed across the crate (head/tail alternating), 2 layers"""
    r = random.Random(seed)
    src = SCANS[kind]
    Lf, Wf, Hf = src.dimensions
    base = cr.matrix_basis
    zt = 0.25 - 0.045          # top of ice in the crate
    per = max(1, int(0.36 / (Wf * 0.85)))
    out = []
    for i in range(n):
        layer, k = divmod(i, per)
        y = -0.18 + (k + 0.5) * 0.36 / per + r.uniform(-0.01, 0.01)
        x = r.uniform(-0.02, 0.02)
        s = r.uniform(0.92, 1.04) * min(1.0, 0.56 / Lf)
        rz = (0 if (i % 2) else math.pi) + r.uniform(-0.08, 0.08)
        lp = Vector((x, y - Wf * s / 2 * 0, zt + layer * Hf * s * 0.85))
        o = place_scan(kind, base @ lp, cr.rotation_euler.z + rz, coll, parent, flip=bool(r.random() < 0.5), s=s,
                       tilt=r.uniform(-0.12, 0.12))
        out.append(o)
    return out


def fill_crate_shrimp(cr, kind, n, coll, parent, seed):
    r = random.Random(seed)
    src = SCANS[kind]
    base = cr.matrix_basis
    zt = 0.25 - 0.06
    out = []
    for i in range(n):
        layer = i * 3 // n
        x, y = r.uniform(-0.24, 0.24), r.uniform(-0.14, 0.14)
        mound = 0.03 * (1 - (x / 0.26) ** 2) * (1 - (y / 0.16) ** 2)
        lp = Vector((x, y, zt + mound + layer * 0.03))
        out.append(place_scan(kind, base @ lp, r.uniform(0, 6.28), coll, parent, flip=r.random() < 0.5,
                              s=r.uniform(0.85, 1.1), tilt=r.uniform(-0.3, 0.3)))
    return out


# ===================================================================================================== people
def gloves(rig, color=(0.85, 0.32, 0.04)):
    """rubber work gloves: hand region of the MPFB body, pushed out 3 mm (same weights -> follows the rig)"""
    body = max((o for o in rig.children if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
    gl = body.copy()
    gl.data = body.data.copy()
    gl.name = rig.name + '.workgloves'
    for c in body.users_collection:
        c.objects.link(gl)
    for m in list(gl.modifiers):
        if m.type not in ('ARMATURE',):
            gl.modifiers.remove(m)
    if gl.data.shape_keys:
        gl.shape_key_clear()
    hand = {g.index for g in gl.vertex_groups if people._part(g.name) == 'hand' and g.name.startswith(
        ('hand', 'index', 'middle', 'ring', 'pinky', 'thumb'))}
    wrist = {g.index for g in gl.vertex_groups if g.name.startswith('lowerarm')}
    bm = bmesh.new()
    bm.from_mesh(gl.data)
    dl = bm.verts.layers.deform.active
    kill = []
    for v in bm.verts:
        w = sum(wt for gi, wt in v[dl].items() if gi in hand)
        w2 = sum(wt for gi, wt in v[dl].items() if gi in wrist)
        if w < 0.35 and not (w > 0.08 and w2 > 0):
            kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(gl.data)
    bm.free()
    gl.data.materials.clear()
    gl.data.materials.append(sklib.flat('sea_glove_%s' % sklib._hex(color), color, rough=0.35, var=0.15, scale=90, bump=0.3))
    d = gl.modifiers.new('push', 'DISPLACE')
    d.strength, d.mid_level = 0.004, 0.0
    so = gl.modifiers.new('Solidify', 'SOLIDIFY')
    so.thickness = 0.002
    return gl


# ===================================================================================================== gulls
def gull(name, coll, cx, cy, cz, r, w, ph, dz, flap):
    root = sklib.new_obj(name, None, coll)
    body_m = sklib.flat('sea_gull_body', (0.85, 0.85, 0.83), rough=0.6, var=0.05, scale=50, **{'Sheen Weight': 0.4})
    wing_m = sklib.flat('sea_gull_wing', (0.52, 0.54, 0.56), rough=0.6, var=0.08, scale=50, **{'Sheen Weight': 0.4})
    tip_m = sklib.flat('sea_gull_tip', (0.04, 0.04, 0.045), rough=0.6, var=0.05, scale=50)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
    bmesh.ops.scale(bm, vec=(0.06, 0.22, 0.065), verts=bm.verts[:])
    for v in bm.verts:
        if v.co.y < 0:
            v.co.x *= 1 + v.co.y * 2.5
            v.co.z *= 1 + v.co.y * 2.5
    b = obj_from_bm(name + '-body', bm, body_m, coll, root)
    b.data.shade_smooth()
    for s in (1, -1):
        bm = bmesh.new()
        pts = [(0, 0.06), (0.30, 0.07), (0.55, 0.0), (0.62, -0.05), (0.32, -0.04), (0, -0.07)]
        vs = [bm.verts.new((s * x, y, 0)) for x, y in pts]
        bm.faces.new(vs if s > 0 else list(reversed(vs)))
        wg = obj_from_bm(name + '-wing', bm, None, coll, root)
        wg.data.materials.append(wing_m)
        wg.data.materials.append(tip_m)
        for p in wg.data.polygons:
            p.material_index = 0
        sd = wg.modifiers.new('Solidify', 'SOLIDIFY')
        sd.thickness = 0.01
        wg.location = (s * 0.04, 0.02, 0.02)
        d = wg.driver_add('rotation_euler', 1).driver
        d.type, d.expression = 'SCRIPTED', '%d*(0.15+0.55*sin(frame*%.3f+%.2f))' % (-s, flap, ph)
    # orbit
    for i, ex in enumerate(('%g+%g*cos(frame*%g+%g)' % (cx, r, w, ph), '%g+%g*sin(frame*%g+%g)' % (cy, r, w, ph),
                            '%g+%g*sin(frame*%g+%g)' % (cz, dz, w * 1.7, ph))):
        d = root.driver_add('location', i).driver
        d.type, d.expression = 'SCRIPTED', ex
    d = root.driver_add('rotation_euler', 2).driver
    d.type, d.expression = 'SCRIPTED', 'frame*%g+%g' % (w, ph) + ('' if w > 0 else '+3.14159')
    d = root.driver_add('rotation_euler', 1).driver
    d.type, d.expression = 'SCRIPTED', '%g' % (0.35 if w > 0 else -0.35)
    return root


# ===================================================================================================== build
col_env = sklib.collection('SEA_ENV')
col_ship = sklib.collection('SEA_BOAT_SHIP')
col_crew = sklib.collection('SEA_CREW')
col_catch = sklib.collection('SEA_CATCH')
col_far = sklib.collection('SEA_FAR')

# ---- sky: sunrise, sun 4 deg at az 95 at f1 rising to 6 deg by f264, sun disc visible
SUN0, SUN1, AZ = 4.0, 6.0, 95.0
world, sun = sklib.sky_world(sun_elev_deg=SUN0, sun_az_deg=AZ, strength=2.6, sun_strength=4.5, air=1.2, dust=4.0)
sky = next(n for n in world.node_tree.nodes if n.bl_idname == 'ShaderNodeTexSky')
sky.sun_disc = True
if hasattr(sky, 'sun_intensity'):
    sky.sun_intensity = 1.0
try:
    world.sun_threshold = 1e6       # the Sun light casts the shadows; don't extract a 2nd sun from the sky
except Exception:
    pass
for f, el in ((1, SUN0), (264, SUN1)):
    sky.sun_elevation = el * D2R
    sky.keyframe_insert('sun_elevation', frame=f)
    e, a = el * D2R, AZ * D2R
    d = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    sun.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    sun.keyframe_insert('rotation_euler', frame=f)
sun.data.angle = 0.6 * D2R

# ---- sea (seed 41, calm swell), t=0 at f1; flat far-sea skirt with the same shader to the horizon
OC = 600.0
sea = sklib.ocean(size=OC, seed=41, time=-1 / 24, choppy=0.9, wave_scale=0.55, wind=9.0, res=12, animate=True, foam=False,
                  coll=col_env, deep=(0.010, 0.040, 0.050), shallow=(0.03, 0.12, 0.12))
cx, cy = 0.0, 0.0
sea.location = (cx - OC / 2, cy - OC / 2, 0)
bm = bmesh.new()
R, h = 9000.0, OC / 2 - 4
outer = [bm.verts.new((cx + x, cy + y, -0.04)) for x, y in ((-R, -R), (R, -R), (R, R), (-R, R))]
inner = [bm.verts.new((cx + x, cy + y, -0.04)) for x, y in ((-h, -h), (h, -h), (h, h), (-h, h))]
for i in range(4):
    j = (i + 1) % 4
    bm.faces.new((outer[i], outer[j], inner[j], inner[i]))
far_m = sea.data.materials[0].copy()
far_m.name = 'A-ENV-SEA-FAR_water'
fnt = far_m.node_tree
ftc = _n(fnt, 'ShaderNodeTexCoord', -1200, -1200)
fno = _noise(fnt, _vscale(fnt, ftc.outputs['Object'], 1.0, 1.6, 1.0, -1000, -1200), 0.12, 6.0, 0.6, -800, -1200)
fbp = _n(fnt, 'ShaderNodeBump', -500, -1200)
fbp.inputs['Strength'].default_value = 1.0
_l(fnt, fno.outputs['Fac'], fbp.inputs['Height'])
for nd in fnt.nodes:
    if nd.bl_idname in ('ShaderNodeBsdfGlossy', 'ShaderNodeFresnel'):
        _l(fnt, fbp.outputs[0], nd.inputs['Normal'])
far = obj_from_bm('A-ENV-SEA-FAR', bm, far_m, col_env)
far.visible_shadow = False

# ---- coast / headland silhouette (NNE, 3.5-4.5 km): ridge az 12..65 deg ending in a headland point
bm = bmesh.new()
hr = random.Random(7)
N = 90
front, back = [], []
for i in range(N + 1):
    a = (12 + (65.5 - 12) * i / N) * D2R
    u = i / N
    dist = 4200 - 700 * u + hr.uniform(-40, 40)
    hgt = (90 + 140 * math.sin(math.pi * min(1, u * 1.15)) ** 0.8 + 35 * math.sin(u * 23) + hr.uniform(-8, 8))
    if u > 0.86:
        hgt *= max(0.0, (1 - u) / 0.14) ** 0.7
    hgt = max(hgt, 0.0) + 2
    front.append(bm.verts.new((math.sin(a) * dist, math.cos(a) * dist, -3)))
    back.append(bm.verts.new((math.sin(a) * (dist + 120), math.cos(a) * (dist + 120), hgt)))
for i in range(N):
    bm.faces.new((front[i], front[i + 1], back[i + 1], back[i]))
land_m = sklib.pbr('sea_headland', 'sparse_grass', tint=(0.07, 0.075, 0.08), scale=40, wear=0.0, contrast=0.3)
land = obj_from_bm('A-ENV-COAST', bm, land_m, col_env)
land.visible_shadow = False

# ---- hero boat
BOAT = sklib.new_obj('BOAT', None, col_ship)
hull, deck, caps = build_hull(col_ship, BOAT)
sup = build_superstructure(col_ship, BOAT)

# ---- catch: crates on crushed ice (aft deck, starboard), tuna tub
load_scans()
crates = []
cols_c = [(0.05, 0.22, 0.55), (0.06, 0.24, 0.58), (0.55, 0.08, 0.05), (0.75, 0.55, 0.06)]
k = 0
for x in (0.55, -0.12):
    for y in (-6.25, -5.82, -5.39, -4.96):
        cr = sklib.crate(color=cols_c[k % 4] if k % 3 else cols_c[0], name='A-CRATE-FISH', coll=col_catch, wear=0.4)
        cr.parent = BOAT
        cr.location = (x + rng.uniform(-0.02, 0.02), y + rng.uniform(-0.015, 0.015), deck_z(y) + 0.03)
        cr.rotation_euler.z = rng.uniform(-0.03, 0.03)
        ice = sklib.crushed_ice_fill(cr, density=1.0, coll=col_catch, seed=k + 3, chunk=0.018, depth=0.06, max_chunks=900)
        crates.append(cr)
        k += 1
# contents: 4 skipjack, 2 shrimp (green tiger prawn), 1 greasyback, 1 iced only (being filled by the sorter)
plan = ['skipjack', 'green-tiger-prawn', 'skipjack', 'skipjack', 'greasyback-shrimp', 'skipjack', 'green-tiger-prawn', None]
for i, (cr, kind) in enumerate(zip(crates, plan)):
    if kind == 'skipjack':
        fill_crate_fish(cr, kind, rng.choice([3, 4, 5]), col_catch, BOAT, 100 + i)
    elif kind:
        fill_crate_shrimp(cr, kind, 34 if kind == 'green-tiger-prawn' else 45, col_catch, BOAT, 200 + i)
tub = sklib.crate(color=(0.05, 0.22, 0.55), name='A-CRATE-TUNA', coll=col_catch, wear=0.45)
tub.parent = BOAT
tub.scale = (1.55, 1.45, 1.2)
tub.location = (0.35, -4.15, deck_z(-4.15) + 0.03)
sklib.crushed_ice_fill(tub, density=0.9, coll=col_catch, seed=91, chunk=0.02, depth=0.08, max_chunks=1400)
for i in range(3):
    place_scan('yellowfin-tuna', Vector((0.35 + (0.02 if i % 2 else -0.02), -4.15 - 0.19 + i * 0.19, deck_z(-4.15) + 0.03 + 0.30 - 0.07)),
               (0 if i % 2 else math.pi) + rng.uniform(-0.05, 0.05), col_catch, BOAT, flip=i == 1, s=0.95)

# ---- cod-end net: bag hauled from the water astern up the A-frame (rigid, origin = top of the extension)
NET = sklib.new_obj('NET-HAUL', None, col_catch)
NET.parent = BOAT
bm = bmesh.new()
NLen, NA, NL = 2.75, 28, 36
uvl = bm.loops.layers.uv.new('UVMap')
rings = []
prof = []
for i in range(NL + 1):
    t = i / NL
    if t < 0.3:
        rr = 0.07 + 0.25 * (t / 0.3) ** 1.3
    else:
        u = (t - 0.3) / 0.7
        rr = 0.32 + 0.33 * math.sin(math.pi * min(1, u * 0.9 + 0.05)) ** 0.7
        rr *= (1 - u ** 6) ** 0.5
    prof.append(max(rr, 0.004))
for i in range(NL + 1):
    t = i / NL
    z = -t * NLen
    ring = []
    for j in range(NA):
        a = 2 * math.pi * j / NA
        lump = 0.10 * math.sin(3 * a + t * 9) * math.sin(5 * a - t * 4) * min(1, t * 2.5)
        sag = 1.0 + lump + 0.06 * math.sin(7 * a + t * 13)
        rr_ = prof[i] * sag * (1 + 0.25 * t)            # heavier at the bottom
        ring.append(bm.verts.new((rr_ * math.cos(a), rr_ * math.sin(a) * 0.85, z + 0.05 * math.sin(2 * a + 1.3) * t)))
    rings.append(ring)
circ = [2 * math.pi * p for p in prof]
for i in range(NL):
    for j in range(NA):
        jn = (j + 1) % NA
        f = bm.faces.new((rings[i][j], rings[i][jn], rings[i + 1][jn], rings[i + 1][j]))
        for lp, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
            lp[uvl].uv = (jj / NA * (circ[i] + circ[min(NL, ii)]) / 2 * 1.0, ii / NL * NLen)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
netbag = sklib._mesh_obj('A-NET-HAUL', bm, col_catch)
netbag.parent = NET
netbag.data.materials.append(net_mat())
netbag.data.shade_smooth()
so = netbag.modifiers.new('Solidify', 'SOLIDIFY')
so.thickness = 0.008
# catch in the bag (skipjack + tuna, compact so nothing pokes through the netting)
for i in range(16):
    t = rng.uniform(0.5, 0.9)
    rr = prof[int(t * NL)] * 0.55
    a = rng.uniform(0, 6.28)
    o = place_scan('skipjack', Vector((rr * math.cos(a), rr * math.sin(a) * 0.8, -t * NLen)), rng.uniform(0, 6.28),
                   col_catch, NET, s=0.8)
    o.rotation_euler = (rng.uniform(1.2, 1.9), rng.uniform(-0.4, 0.4), rng.uniform(0, 6.28))
    o.location -= o.matrix_basis.to_3x3() @ Vector((0, SCANS['skipjack'].dimensions.y * 0.4, SCANS['skipjack'].dimensions.z * 0.4))
# haul keys: f80 lying in the water astern -> f150 hanging from the A-frame block
az0 = deck_z(-7.2)
NET_KEYS = [(1, (0, -12.6, 0.05), (-1.45, 0, 0)), (80, (0, -12.2, 0.05), (-1.43, 0, 0)),
            (112, (0, -10.4, 1.15), (-1.0, 0, 0)), (150, (0, -8.4, az0 + 2.75), (-0.05, 0, 0)),
            (264, (0, -8.4, az0 + 2.75), (0.0, 0, 0))]
for f, loc, rot in NET_KEYS:
    NET.location, NET.rotation_euler = loc, rot
    NET.keyframe_insert('location', frame=f)
    NET.keyframe_insert('rotation_euler', frame=f)
sklib.ease_keys(NET)
# warp from the block to the net (hooked poly curve -> follows the haul)
wire = rope_mat((0.12, 0.11, 0.1), 'sea_wire')
hk0 = sklib.new_obj('NET-HOOK-BLOCK', None, col_catch, parent=BOAT, loc=(0, -8.4, az0 + 2.82))
hk1 = sklib.new_obj('NET-HOOK-NET', None, col_catch, parent=NET, loc=(0, 0, 0.0))
hk2 = sklib.new_obj('NET-HOOK-DRUM', None, col_catch, parent=BOAT, loc=(0, 0.75, deck_z(0.75) + 1.3))
for nm_, a_, b_ in (('A-NET-WARP', hk0, hk1), ('A-NET-WARP2', hk2, hk0)):
    cu = bpy.data.curves.new(nm_, 'CURVE')
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = '3D', 0.012, 2
    sp = cu.splines.new('POLY')
    sp.points.add(1)
    wo = bpy.data.objects.new(nm_, cu)
    col_catch.objects.link(wo)
    wo.data.materials.append(wire)
    for idx, hko in enumerate((a_, b_)):
        hm = wo.modifiers.new('Hook%d' % idx, 'HOOK')
        hm.object = hko
        hm.vertex_indices_set([idx])
# droplets draining from the bag (particles, rendered as instanced drops, motion-blurred)
drop = sklib.new_obj('DROPLET', bpy.data.meshes.new('DROPLET'), sklib.collection('SEA_PROTO', parent=False))
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.006)
bmesh.ops.scale(bm, vec=(1, 1, 1.7), verts=bm.verts[:])
bm.to_mesh(drop.data)
bm.free()
wm = bpy.data.materials.new('sea_droplet')
wm.use_nodes = True
pb = wm.node_tree.nodes['Principled BSDF']
pb.inputs['Base Color'].default_value = (0.8, 0.9, 0.9, 1)
pb.inputs['Transmission Weight'].default_value = 1.0
pb.inputs['Roughness'].default_value = 0.03
pb.inputs['IOR'].default_value = 1.33
drop.data.materials.append(wm)
drop.data.shade_smooth()
vg = netbag.vertex_groups.new(name='drip')
for v in netbag.data.vertices:
    if v.co.z < -NLen * 0.35:
        vg.add([v.index], 1.0, 'REPLACE')
ps_mod = netbag.modifiers.new('drip', 'PARTICLE_SYSTEM')
psys = netbag.particle_systems[0]
pset = psys.settings
pset.count, pset.frame_start, pset.frame_end, pset.lifetime = 4200, 100, 264, 22
pset.emit_from, pset.use_emit_random = 'FACE', True
pset.normal_factor, pset.factor_random, pset.object_factor = 0.05, 0.25, 0.0
pset.render_type, pset.instance_object = 'OBJECT', drop
pset.particle_size, pset.size_random = 1.0, 0.6
pset.use_rotations, pset.rotation_mode = True, 'VEL'
pset.physics_type = 'NEWTON'
psys.vertex_group_density = 'drip'
pset.display_method = 'DOT'

# ---- crew (6): sorter crouched at the crates (oilskins, gloves) + 5 at the starboard rail (one waving)
def gunwale(y, dx=-0.06, dz=0.02):
    t = _t(y)
    return Vector((sec(t, 0.0)[0] + dx, y, sheer(t) + dz))


def reach(rig, side, world_pt, pole, hand_dir):
    bpy.context.view_layer.update()
    T = rig.matrix_world.inverted() @ Vector(world_pt)
    people._arm(rig, side, ('reach', T, Vector(pole), Vector(hand_dir)))


def rebase(rig):
    bpy.context.view_layer.update()
    for pb in rig.pose.bones:
        pb['sk_base'] = list(pb.rotation_quaternion)


dzc = deck_z(-5.5)
CREW = [
    # name, sex, age, skin, body, outfit, pose, (x, y), rot_z deg, cycle, amount, phase, extra
    ('crew-sorter', 'male', 0.38, 0.75, {'weight': 0.5, 'muscle': 0.65}, 'oilskins', 'crouch', (1.36, -5.58), -90, 'work', 0.55, 0.1, 'sort'),
    ('crew-hauler', 'male', 0.55, 0.85, {'weight': 0.62, 'muscle': 0.7}, 'tshirt_shorts', 'pull_rope', (1.2, -3.5), 0, 'pull', 0.8, 0.3, 'haul'),
    ('crew-leaner', 'male', 0.22, 0.5, {'weight': 0.35, 'muscle': 0.5, 'height': 0.4}, 'tshirt_shorts', 'stand', (1.5, -2.75), 90, 'work', 0.08, 0.6, 'lean'),
    ('crew-coiler', 'male', 0.72, 0.95, {'weight': 0.4, 'muscle': 0.4, 'height': 0.35}, 'tshirt_lungi', 'work_table', (1.05, -2.0), 90 - 40, 'work', 0.35, 0.85, 'coil'),
    ('crew-carrier', 'male', 0.42, 0.62, {'weight': 0.6, 'muscle': 0.75, 'height': 0.7}, 'oilskins', 'carry', (1.38, -1.3), 90 - 14, 'work', 0.06, 0.15, 'carry'),
    ('crew-waver', 'male', 0.3, 0.7, {'weight': 0.45, 'muscle': 0.6, 'height': 0.55}, 'tshirt_lungi', 'wave', (1.55, -0.55), -57, 'wave', 1.0, 0.0, None),
]
crew = []
for i, (nm_, sx, age, tone, body, outfit, pose, (x, y), rz, cyc, amt, ph, extra) in enumerate(CREW):
    rig = people.make_person(nm_, sex=sx, age=age, body=body, skin_tone=tone, outfit=outfit, pose=pose,
                             location=(x, y, deck_z(y) + 0.03), rotation_z=rz * D2R, seed=410 + i * 13)
    for o in [rig] + list(rig.children_recursive):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col_crew.objects.link(o)
    if extra == 'sort':        # both hands into the crates in front of him (left hand = aft side)
        reach(rig, 'l', (0.80, -5.78, dzc + 0.30), (0.6, 0.3, -0.5), (0.0, -1, -1.2))
        reach(rig, 'r', (0.78, -5.36, dzc + 0.33), (-0.6, 0.3, -0.5), (0.0, -1, -1.2))
    elif extra == 'lean':      # forearms on the gunwale
        reach(rig, 'l', gunwale(y - 0.24), (0.7, 0.5, -0.4), (0.0, -1, -0.3))
        reach(rig, 'r', gunwale(y + 0.24), (-0.7, 0.5, -0.4), (0.0, -1, -0.3))
    rebase(rig)
    if extra in ('haul', 'coil'):
        bpy.context.view_layer.update()
        hl = rig.matrix_world @ rig.pose.bones['hand_l'].head
        hr = rig.matrix_world @ rig.pose.bones['hand_r'].head
    if extra == 'haul':        # hand-hauling the cod-end lifting line that runs up to the A-frame block
        tube('A-ROPE-HAUL', [tuple(hr + Vector((0, 0.35, -0.05))), tuple(hr), tuple(hl), (0.15, -8.35, az0 + 2.6)], 0.014,
             rope_mat((0.75, 0.6, 0.1), 'sea_rope_yellow'), col_catch, BOAT, 6)
    if extra == 'coil':        # coiling a rope: loops hanging from both hands
        mid = (hl + hr) / 2
        for kk in range(4):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.2 + 0.015 * kk, minor_radius=0.013, major_segments=24,
                                             minor_segments=6, location=mid + Vector((0, 0, -0.17 - 0.01 * kk)),
                                             rotation=(math.pi / 2, 0, rig.rotation_euler.z + 0.2 * kk))
            rc = bpy.context.object
            rc.name = 'A-ROPECOIL-HAND'
            for c in rc.users_collection:
                c.objects.unlink(rc)
            col_catch.objects.link(rc)
            rc.parent = BOAT
            sklib.mat_to(rc, rope_mat((0.08, 0.25, 0.5), 'sea_rope_blue'))
            rc.data.shade_smooth()
    if extra == 'carry':       # a fish basket held in front, between the hands
        bpy.context.view_layer.update()
        hl = rig.matrix_world @ rig.pose.bones['hand_l'].head
        hr = rig.matrix_world @ rig.pose.bones['hand_r'].head
        bk = sklib.crate(color=(0.55, 0.08, 0.05), name='A-CRATE-CARRIED', coll=col_catch, wear=0.45)
        bk.scale = (abs((hl - hr).length) / 0.62, 0.85, 0.8)
        mid = (hl + hr) / 2
        bk.location = mid + Vector((0, 0, -0.16))
        bk.rotation_euler.z = math.atan2(hl.y - hr.y, hl.x - hr.x)
        bk.parent = BOAT
        fill_crate_fish(bk, 'skipjack', 2, col_catch, BOAT, 777)
    rig.parent = BOAT
    people.animate_cycle(rig, cyc, 1, 264, phase=ph, amount=amt)
    if outfit == 'oilskins':
        gloves(rig, (0.85, 0.32, 0.04) if i == 0 else (0.1, 0.12, 0.35))
    crew.append(rig)

# ---- boat motion on the swell (drivers; sea is seed 41 calm)
BOAT.location = (BOAT_XY.x, BOAT_XY.y, 0.0)
BOAT.rotation_euler = (0, 0, math.pi)
for i, ex in ((2, '0.06*sin(frame*0.0494+0.6)+0.02*sin(frame*0.113)'),):
    d = BOAT.driver_add('location', i).driver
    d.type, d.expression = 'SCRIPTED', ex
for i, ex in ((0, '0.012*sin(frame*0.0429+1.0)'), (1, '0.026*sin(frame*0.0556)+0.006*sin(frame*0.131+2.0)')):
    d = BOAT.driver_add('rotation_euler', i).driver
    d.type, d.expression = 'SCRIPTED', ex

# ---- distant boats: instances of the hero ship collection (no crew/catch), + a small boat
col_ship.instance_offset = (BOAT_XY.x, BOAT_XY.y, 0)
for nm_, az, dist, rot, sc, ph in (('A-VESSEL-FISHING-B1', 65.0, 360.0, 1.2, 1.0, 1.3), ('A-VESSEL-FISHING-B2', 61.5, 720.0, -0.6, 0.9, 2.1)):
    e = sklib.instance(col_ship, loc=(math.sin(az * D2R) * dist, math.cos(az * D2R) * dist, 0), rot_z=rot,
                       name=nm_, parent_coll=col_far, scale=sc)
    d = e.driver_add('rotation_euler', 1).driver
    d.type, d.expression = 'SCRIPTED', '0.03*sin(frame*0.05+%g)' % ph
cb = sklib.new_obj('A-VESSEL-COUNTRY', None, col_far, loc=(math.sin(131 * D2R) * 160, math.cos(131 * D2R) * 160, 0), rot=(0, 0, 0.5))
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.55, depth=7.5, rotation=(math.pi / 2, 0, 0))
ch = bpy.context.object
for c in ch.users_collection:
    c.objects.unlink(ch)
col_far.objects.link(ch)
ch.name = 'A-VESSEL-COUNTRY-HULL'
ch.parent = cb
ch.scale = (1.0, 1.0, 0.6)
ch.location = (0, 0, 0.05)
sklib.mat_to(ch, hull_paint())
cyl('A-VESSEL-COUNTRY-MAST', (0, 1.2, 2.2), 0.05, 4.0, sklib.wood_planks(0.4), col_far, cb)
d = cb.driver_add('rotation_euler', 1).driver
d.type, d.expression = 'SCRIPTED', '0.05*sin(frame*0.07)'

# ---- gulls x8 around the boat (orbit radius <= 10 m so none is in the f1 horizon frame)
col_gull = sklib.collection('SEA_GULLS')
for i in range(8):
    r = rng.uniform(5, 10)
    gull('A-GULL-%d' % i, col_gull, BOAT_XY.x + rng.uniform(-3, 3), BOAT_XY.y + rng.uniform(-6, 2), rng.uniform(5.5, 10.5),
         r, rng.choice([1, -1]) * rng.uniform(0.018, 0.03), rng.uniform(0, 6.28), rng.uniform(0.3, 1.0), rng.uniform(0.55, 0.75))

# ===================================================================================================== camera
cam = sklib.camera('CAM', lens=35.0, loc=(0, 0, 3))
cam.data.clip_start, cam.data.clip_end = 0.05, 9500
pitch = math.atan(0.08 * (36 * 9 / 16 / 2) / 35)          # horizon at 46 % from the bottom
far_aim = Vector((math.sin(AZ * D2R), math.cos(AZ * D2R), 0)) * 1000 + Vector((0, 0, 3 + 1000 * math.tan(pitch)))
dz = deck_z(-5.0)
KEYS = [
    (1, (0, 0, 3.0), far_aim, 35.0),                                   # BRIDGE_HORIZON
    (40, (17.0, -15.5, 2.7), W(-2.0, -6.0, 4.0), None),
    (80, tuple(W(7.5, -5.5, 2.6)), W(0, -8.0, 1.0), 35.0),           # starboard beam aft, net in the water astern
    (120, tuple(W(5.8, -13.5, 3.3)), W(0, -9.0, 1.2), None),         # starboard quarter
    (160, tuple(W(0.8, -16.0, 4.1)), W(0, -8.6, 1.5), 35.0),         # astern, the bag up and dripping
    (178, tuple(W(2.3, -11.8, 3.4)), W(0.6, -6.0, 0.9), None),
    (196, tuple(W(1.55, -9.15, dz + 2.3)), W(0.55, -6.0, dz + 0.2), 55.0),   # deck beat: gloved hands sorting on ice
    (210, tuple(W(1.6, -9.05, dz + 2.35)), W(0.6, -5.9, dz + 0.22), 55.0),
    (226, tuple(W(4.3, -8.3, 4.5)), W(1.0, -2.6, 1.3), None),              # rise up and out behind the sorter
    (264, tuple(W(11.0, -1.6, 2.35)), None, 32.0),                   # crew portrait, backlit
]
aim_end = W(11.0, -1.6, 2.35) + Vector((math.sin(84 * D2R), math.cos(84 * D2R), 0)) * 10 + Vector((0, 0, -0.35))
KEYS[-1] = (264, KEYS[-1][1], aim_end, 32.0)
sklib.camera_path(cam, [(f, Vector(l), Vector(a), le) for f, l, a, le in KEYS])

# ===================================================================================================== finish
S.frame_start, S.frame_end = 1, 264
S.frame_set(1)
try:
    bpy.ops.ptcache.bake_all(bake=True)       # droplets: baked into the .blend so any frame renders correctly
    print('SEA_PTCACHE baked')
except Exception as ex:
    print('SEA_PTCACHE bake failed', ex)
S.frame_set(1)
S.eevee.use_raytracing = True
path = sklib.finish('sea', 'dawn')
S.render.motion_blur_shutter = 0.3
S.frame_start, S.frame_end = 1, 264
bpy.ops.wm.save_mainfile()
print('SEA_BUILD_DONE', path)
