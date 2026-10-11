"""S1 table.blend -> v-table (1-216, kind int). Re-runnable: factory reset -> build -> sklib.finish('table', 'int').
Run: $B --factory-startup -b --python assets-src/blender/build/table.py

Layout (metres, Z up): dining table centred at origin (top z=0.75, long axis X), diner A at -X (plate A, macro), diner B
at +X; back wall y=1.9 with floor-to-ceiling window (left, x<0.5) and the kitchen (right, x>1.35): dark pantry cabinet +
counter with the opened hero carton. BRIDGE_FROST collection (frosted bag patch + area light, origin at the patch)
is instanced lying on a glazed block inside the carton; the camera ends 0.12 m above it at f216.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

REPO = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4'
sys.path.insert(0, REPO + '/assets-src/blender/lib')
import sklib  # noqa: E402
import look  # noqa: E402  (art pass #75: COLOR_SCRIPT row 00)
from sklib import _n, _l, _math, _mix, _maprange, _noise  # noqa: E402
sys.path.insert(0, REPO + '/assets-src/blender/build')
import bridge_frost as bridge_frost_mod  # noqa: E402

PRAWN_SCAN = REPO + '/assets-src/models/prawn.glb'   # A-PROD-PRAWN: the CC0 ffish.asia green tiger prawn scan, cleaned (remeshed body + baked albedo) by products.py
D2R = math.pi / 180
TOP = 0.75                       # table top height
CARTON_LOC = Vector((2.86, 1.58, 0.92))
rng = random.Random(216)

s = sklib.reset()
import people  # noqa: E402  (after the factory reset: it re-enables MPFB)

C_SET = sklib.collection('SET')
C_TABLE = sklib.collection('TABLE')
C_FOOD = sklib.collection('FOOD')
C_KITCHEN = sklib.collection('KITCHEN')
C_LIGHT = sklib.collection('LIGHTS')
C_PEOPLE = sklib.collection('PEOPLE')


# ------------------------------------------------------------------------------------------------ geometry helpers
def mesh(name, bm, coll, mats=(), loc=(0, 0, 0), rot=(0, 0, 0), uv=True, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = sklib.new_obj(name, me, coll, loc=loc, rot=rot)
    if mats:
        sklib.mat_to(ob, *mats, uv=uv)
    if smooth:
        me.shade_smooth()
    return ob


def box(name, center, size, mat, coll, bev=0.004, seg=2, rot=(0, 0, 0)):
    bm = bmesh.new()
    sklib._bm_box(bm, Vector((0, 0, 0)), size)
    ob = mesh(name, bm, coll, (mat,), loc=center, rot=rot)
    if bev:
        sklib.bevel(ob, bev, seg)
    return ob


def lathe(name, prof, coll, mat, seg=64, loc=(0, 0, 0), smooth=True):
    """Solid of revolution about local Z from a profile [(r, z), ...] (axis points r=0 are merged)."""
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((max(r, 1e-6) * math.cos(2 * math.pi * k / seg),
                                    max(r, 1e-6) * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            try:
                bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = mesh(name, bm, coll, (mat,) if mat else (), loc=loc)
    if smooth:
        ob.data.shade_smooth()
        ob.data.set_sharp_from_angle(angle=50 * D2R)
    return ob


def parent_keep(ob, par):
    mw = ob.matrix_world.copy()
    ob.parent = par
    ob.matrix_world = mw


# ------------------------------------------------------------------------------------------------------- materials
def principled(name, color, rough=0.5, **kw):
    m = bpy.data.materials.get(name)
    if m:
        return m, None, None
    m, nt = sklib._new_mat(name)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 900, 0).inputs['Surface'])
    b.inputs['Base Color'].default_value = tuple(color[:3]) + (1,)
    b.inputs['Roughness'].default_value = rough
    for k, v in kw.items():
        b.inputs[k].default_value = v
    return m, nt, b


def refractive(m, thick='SLAB'):
    for a, v in (('surface_render_method', 'DITHERED'), ('use_raytrace_refraction', True),
                 ('thickness_mode', thick), ('use_transparent_shadow', True)):
        if hasattr(m, a):
            setattr(m, a, v)
    return m


def glass_mat():
    """Thin soda-lime glass, BLENDED (no screen-space refraction: the wine/water inside stays visible, nothing turns
    black): glossy Principled whose alpha follows Fresnel, so the rims and silhouettes read and the body stays clear."""
    m = bpy.data.materials.get('glass_clear')
    if m:
        return m
    m, nt, b = principled('glass_clear', (0.97, 0.99, 0.98), 0.02, **{'IOR': 1.5})
    lw = _n(nt, 'ShaderNodeLayerWeight', 0, -300)
    lw.inputs['Blend'].default_value = 0.12
    _l(nt, _maprange(nt, lw.outputs['Fresnel'], 0.0, 1.0, 0.07, 0.7, 250, -300), b.inputs['Alpha'])
    m.surface_render_method = 'BLENDED'
    for a_, v in (('use_transparent_shadow', True), ('show_transparent_back', False)):
        if hasattr(m, a_):
            setattr(m, a_, v)
    return m


def liquid_mat(name, color, ior=1.333):
    m, nt, b = principled(name, color, 0.02, **{'Transmission Weight': 1.0, 'IOR': ior})
    return refractive(m, 'SPHERE' if 'wine' in name else 'SLAB')


def ceramic():
    m = sklib.pbr('ceramic_stoneware', 'white_plaster_02', tint=(0.07, 0.062, 0.058), rough=(0.05, 0.16), nor=0.03,
                  wear=0.05, wear_color=(0.30, 0.27, 0.25), contrast=0.3, var=0.08)   # art #75: charcoal stoneware glaze, not white/peach
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Coat Weight'].default_value = 1.0
    b.inputs['Coat Roughness'].default_value = 0.02
    b.inputs['Subsurface Weight'].default_value = 0.08
    return m


def food_mat(name, base, sss_rad, rough=0.4, coat=0.5, sss=0.4, bump=0.3, scale=200.0, var=0.15):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = sklib.flat(name, base, rough=rough, var=var, scale=scale, bump=bump,
                   **{'Subsurface Weight': sss, 'Subsurface Radius': sss_rad, 'Subsurface Scale': 0.004,
                      'Coat Weight': coat, 'Coat Roughness': 0.12})
    return m


def prawn_cooked(img):
    """Cooked vannamei: the scan albedo's light/dark pattern remapped to a cooked orange-pink ramp, grill char bars
    (object-space stripes x noise), oily coat, subsurface."""
    m = bpy.data.materials.get('prawn_grilled')
    if m:
        return m
    m, nt = sklib._new_mat('prawn_grilled')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 900, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 1200, 0).inputs['Surface'])
    uv = _n(nt, 'ShaderNodeUVMap', -1200, 300, uv_map='UVMap_scan')
    ti = _n(nt, 'ShaderNodeTexImage', -1000, 300)
    ti.image = img
    _l(nt, uv.outputs[0], ti.inputs[0])
    bw = _n(nt, 'ShaderNodeRGBToBW', -750, 300)
    _l(nt, ti.outputs['Color'], bw.inputs[0])
    tcp = _n(nt, 'ShaderNodeTexCoord', -1200, 600)
    sp = _n(nt, 'ShaderNodeSeparateXYZ', -1000, 600)
    _l(nt, tcp.outputs['Object'], sp.inputs[0])
    belly = _maprange(nt, sp.outputs['Z'], 0.006, -0.009, 0.0, 1.0, -800, 650)          # pale underside
    band = _math(nt, 'SINE', _math(nt, 'MULTIPLY', sp.outputs['X'], 520.0, x=-800, y=500), x=-650, y=500)
    band = _maprange(nt, band, 0.55, 1.0, 0.0, 0.25, -500, 500)                         # paler segment joints
    det = _maprange(nt, bw.outputs[0], 0.2, 0.8, -0.12, 0.12, -550, 300)                 # scan detail, toned down
    fac = _math(nt, 'ADD', _math(nt, 'ADD', belly, band, x=-350, y=550), det, x=-200, y=450)
    rp = _n(nt, 'ShaderNodeValToRGB', -50, 300)
    els = rp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.62, 0.11, 0.03, 1)
    els[1].position, els[1].color = 1.0, (0.96, 0.58, 0.36, 1)   # art #75: cooked orange, not candy pink
    e = els.new(0.35)
    e.color = (0.78, 0.26, 0.08, 1)
    _l(nt, fac, rp.inputs[0])
    tc = _n(nt, 'ShaderNodeTexCoord', -1200, -200)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -1000, -200)
    _l(nt, tc.outputs['Object'], sep.inputs[0])
    st = _math(nt, 'MULTIPLY_ADD', sep.outputs['Z'], 0.35, x=-800, y=-200, c=sep.outputs['X'])   # bars across
    st = _math(nt, 'MULTIPLY', st, 210.0, x=-650, y=-200)
    st = _math(nt, 'SINE', st, x=-500, y=-200)
    nz = _noise(nt, tc.outputs['Object'], 180.0, 6.0, 0.65, -650, -420)
    ch = _math(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 0.5, x=-350, y=-300, c=st)
    ch = _maprange(nt, ch, 0.88, 1.12, 0.0, 0.8, -200, -300)
    col = _mix(nt, ch, rp.outputs['Color'], (0.09, 0.035, 0.015), 'MIX', 200, 200)
    _l(nt, col, b.inputs['Base Color'])
    _l(nt, _maprange(nt, ch, 0, 1, 0.32, 0.6, 200, -50), b.inputs['Roughness'])
    b.inputs['Subsurface Weight'].default_value = 0.35
    b.inputs['Subsurface Radius'].default_value = (0.9, 0.35, 0.2)
    b.inputs['Subsurface Scale'].default_value = 0.004
    b.inputs['Coat Weight'].default_value = 0.7
    b.inputs['Coat Roughness'].default_value = 0.08
    bp = _n(nt, 'ShaderNodeBump', 500, -300)
    bp.inputs['Strength'].default_value = 0.25
    bp.inputs['Distance'].default_value = 0.0006
    _l(nt, nz.outputs['Fac'], bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    return m


def tuna_mat():
    """Seared tuna slice: ruby interior with faint myosepta arcs, a 2-3 mm grey-brown seared rim with pepper flecks.
    Uses object coords of a slice whose local y = steak width (+-0.035), z = steak thickness (+-0.0125)."""
    m = bpy.data.materials.get('tuna_seared')
    if m:
        return m
    m, nt = sklib._new_mat('tuna_seared')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 900, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 1200, 0).inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -1300, 0)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -1100, 0)
    _l(nt, tc.outputs['Object'], sep.inputs[0])
    ay = _math(nt, 'DIVIDE', _math(nt, 'ABSOLUTE', sep.outputs['Y'], x=-950, y=100), 0.035, x=-800, y=100)
    az = _math(nt, 'DIVIDE', _math(nt, 'ABSOLUTE', sep.outputs['Z'], x=-950, y=-50), 0.0125, x=-800, y=-50)
    dz = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, az, x=-650, y=-50), 0.0125, x=-500, y=-50)
    dy = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, ay, x=-650, y=100), 0.035, x=-500, y=100)
    d = _math(nt, 'MINIMUM', dy, dz, x=-350, y=50)                       # metres to the outer seared surface
    nz = _noise(nt, tc.outputs['Object'], 300.0, 4.0, 0.6, -650, -250)
    d = _math(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 0.0012, x=-200, y=0, c=d)
    crust = _maprange(nt, d, 0.0055, 0.0038, 0.0, 1.0, -50, 0)
    wv = _n(nt, 'ShaderNodeTexWave', -650, 350)
    wv.wave_type, wv.bands_direction = 'RINGS', 'Z'
    wv.inputs['Scale'].default_value = 90.0
    wv.inputs['Distortion'].default_value = 6.0
    wv.inputs['Detail'].default_value = 3.0
    _l(nt, tc.outputs['Object'], wv.inputs['Vector'])
    my = _maprange(nt, wv.outputs['Fac'], 0.9, 1.0, 0.0, 0.14, -450, 350)
    nv = _noise(nt, tc.outputs['Object'], 60.0, 4.0, 0.6, -650, 200)
    flesh = _mix(nt, _maprange(nt, nv.outputs['Fac'], 0.3, 0.7, 0, 1, -450, 200), (0.085, 0.006, 0.012), (0.155, 0.014, 0.022), 'MIX', -350, 300)   # deep ruby
    flesh = _mix(nt, my, flesh, (0.28, 0.09, 0.10), 'MIX', -250, 350)
    fl = _noise(nt, tc.outputs['Object'], 900.0, 2.0, 0.5, -650, 600)            # pepper/sesame flecks
    fk = _maprange(nt, fl.outputs['Fac'], 0.62, 0.68, 0.0, 1.0, -450, 600)
    seared = _mix(nt, fk, (0.17, 0.09, 0.05), (0.02, 0.015, 0.01), 'MIX', -250, 600)
    col = _mix(nt, crust, flesh, seared, 'MIX', 200, 300)
    _l(nt, col, b.inputs['Base Color'])
    _l(nt, _maprange(nt, crust, 0, 1, 0.22, 0.55, 200, 0), b.inputs['Roughness'])
    _l(nt, _maprange(nt, crust, 0, 1, 0.12, 0.02, 200, -150), b.inputs['Subsurface Weight'])
    b.inputs['Subsurface Radius'].default_value = (1.0, 0.25, 0.2)
    b.inputs['Subsurface Scale'].default_value = 0.004
    b.inputs['Coat Weight'].default_value = 0.35
    b.inputs['Coat Roughness'].default_value = 0.15
    bp = _n(nt, 'ShaderNodeBump', 600, -300)
    bp.inputs['Strength'].default_value = 0.3
    bp.inputs['Distance'].default_value = 0.0005
    _l(nt, _math(nt, 'MULTIPLY', nz.outputs['Fac'], crust, x=400, y=-350), bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    return m


def frost_bridge_mat():
    """M-FROST-BRIDGE: white poly film under hoar frost. Crystal facets = voronoi cells with random heights (bump) and
    low roughness -> sparkle under the area light; frost density clumps (noise) over a smoother translucent film."""
    m = bpy.data.materials.get('M-FROST-BRIDGE')
    if m:
        return m
    m, nt = sklib._new_mat('M-FROST-BRIDGE')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 1100, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 1400, 0).inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -1400, 0)
    v1 = _n(nt, 'ShaderNodeTexVoronoi', -1100, 300)          # crystal facets ~0.3 mm, random tilt per cell
    v1.inputs['Scale'].default_value = 650.0
    _l(nt, tc.outputs['Object'], v1.inputs['Vector'])
    fz = _noise(nt, tc.outputs['Object'], 260.0, 10.0, 0.75, -1100, 0)        # feathery frost fuzz
    dn = _noise(nt, tc.outputs['Object'], 45.0, 6.0, 0.65, -1100, -300)        # density clumps
    dens = _maprange(nt, dn.outputs['Fac'], 0.35, 0.65, 0.35, 1.0, -850, -300)
    h1 = _n(nt, 'ShaderNodeRGBToBW', -850, 300)
    _l(nt, v1.outputs['Color'], h1.inputs[0])
    h = _math(nt, 'MULTIPLY_ADD', h1.outputs[0], 0.35, x=-650, y=150, c=fz.outputs['Fac'])
    h = _math(nt, 'MULTIPLY', h, dens, x=-450, y=150)
    col = _mix(nt, _maprange(nt, h, 0.25, 0.75, 0, 1, -450, 450), (0.5, 0.56, 0.64), (0.99, 0.99, 0.995), 'MIX', -200, 450)
    _l(nt, col, b.inputs['Base Color'])
    _l(nt, _maprange(nt, h1.outputs[0], 0.0, 1.0, 0.03, 0.5, -350, -150), b.inputs['Roughness'])
    b.inputs['Subsurface Weight'].default_value = 0.5
    b.inputs['Subsurface Radius'].default_value = (0.35, 0.4, 0.5)
    b.inputs['Subsurface Scale'].default_value = 0.002
    b.inputs['Specular IOR Level'].default_value = 0.6
    bp = _n(nt, 'ShaderNodeBump', 800, -300)
    bp.inputs['Strength'].default_value = 1.0
    bp.inputs['Distance'].default_value = 0.002
    _l(nt, h, bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    return m


def walnut():
    """Art #75: walnut-dusk table/chairs (#3a1f14 dominant) instead of pale oak; same CC0 wood scan, recoloured."""
    return sklib.pbr('walnut', 'kitchen_wood', tint=(0.14, 0.10, 0.042), contrast=1.1, wear=0.1, rough=(0.22, 0.5),
                     ao_dist=0.1, var=0.12)


def leaf_mat(name, col):
    return food_mat(name, col, (0.2, 0.6, 0.1), rough=0.5, coat=0.04, sss=0.3, bump=0.15, scale=400, var=0.25)


# ----------------------------------------------------------------------------------------------------------- room
def build_room():
    floor = sklib.pbr('floor_parquet', 'herringbone_parquet', scale=1.0, wear=0.12, rough=(0.3, 0.7), ao_dist=0.3)
    wallm = sklib.pbr('wall_warm', 'white_plaster_02', tint=(0.46, 0.38, 0.31), wear=0.06, contrast=0.4, ao_dist=0.4)
    box('floor', (0.8, -0.575, -0.025), (8.4, 4.95, 0.05), floor, C_SET, 0)
    box('ceiling', (0.8, -0.575, 2.725), (8.4, 4.95, 0.05), wallm, C_SET, 0)
    box('wall_L', (-3.25, -0.05, 1.35), (0.1, 6.1, 2.7), wallm, C_SET, 0)
    box('wall_R', (4.85, -0.05, 1.35), (0.1, 6.1, 2.7), wallm, C_SET, 0)
    box('wall_F', (0.8, -3.05, 1.35), (8.4, 0.1, 2.7), wallm, C_SET, 0)
    # back wall with a floor-to-ceiling window opening x in [-2.8, 0.5]
    box('wall_B_left', (-3.025, 1.95, 1.35), (0.35, 0.1, 2.7), wallm, C_SET, 0)
    box('wall_B_right', (2.675, 1.95, 1.35), (4.35, 0.1, 2.7), wallm, C_SET, 0)
    box('wall_B_head', (-1.15, 1.95, 2.65), (3.3, 0.1, 0.1), wallm, C_SET, 0)
    frame = sklib.painted_metal((0.03, 0.03, 0.032), wear=0.1, contrast=0.3)
    for x in (-2.78, -1.7, -0.6, 0.48):
        box('mullion_%.1f' % x, (x, 1.93, 1.3), (0.05, 0.08, 2.6), frame, C_SET, 0.004)
    box('transom_b', (-1.15, 1.93, 0.04), (3.3, 0.08, 0.06), frame, C_SET, 0.004)
    box('transom_t', (-1.15, 1.93, 2.57), (3.3, 0.08, 0.06), frame, C_SET, 0.004)
    # glass: thin reflective film (no refraction needed: faint reflection, see-through)
    gm, nt, b = principled('window_glass', (0.9, 0.93, 0.95), 0.03, **{'Alpha': 0.12})
    if nt:
        gm.surface_render_method = 'BLENDED'
    box('window_glass', (-1.15, 1.92, 1.3), (3.3, 0.006, 2.5), gm, C_SET, 0)
    skirt = sklib.pbr('skirting', 'white_plaster_02', tint=(0.9, 0.88, 0.84), wear=0.05, contrast=0.2)
    box('skirting_L', (-3.19, -0.6, 0.04), (0.02, 4.8, 0.08), skirt, C_SET, 0.002)
    # sheer linen curtain bunched at the window's left edge (sine folds)
    bm = bmesh.new()
    nx, nz = 60, 30
    vs = [[bm.verts.new((-2.72 + 0.55 * i / nx, 1.8 + 0.035 * math.sin(i / nx * 2 * math.pi * 7 + j * 0.02)
                         + 0.01 * math.sin(i * 1.3), 0.02 + 2.5 * j / nz)) for i in range(nx + 1)] for j in range(nz + 1)]
    for j in range(nz):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    cm = sklib.linen_fabric((0.93, 0.9, 0.84))
    cur = mesh('curtain', bm, C_SET, (cm,), smooth=True)
    sol = cur.modifiers.new('sol', 'SOLIDIFY')
    sol.thickness = 0.002
    # out-of-focus city at dusk: dark-blue sky gradient + lit windows of generic blocks (no landmarks)
    city()


def city():
    """Dusk sky gradient + soft round bokeh discs of lit windows far behind the glass (generic, no landmarks)."""
    m, nt = sklib._new_mat('city_sky')
    em = _n(nt, 'ShaderNodeEmission', 400, 0)
    _l(nt, em.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 700, 0).inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -400, 0)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -200, 0)
    _l(nt, tc.outputs['Generated'], sep.inputs[0])
    rp = _n(nt, 'ShaderNodeValToRGB', 0, 0)
    rp.color_ramp.elements[0].color = (0.16, 0.12, 0.13, 1)       # city haze low
    rp.color_ramp.elements[1].color = (0.05, 0.08, 0.19, 1)       # blue hour above
    rp.color_ramp.elements[0].position = 0.3
    e = rp.color_ramp.elements.new(0.42)
    e.color = (0.5, 0.3, 0.2, 1)                                  # warm afterglow band
    _l(nt, sep.outputs['Z'], rp.inputs[0])
    _l(nt, rp.outputs[0], em.inputs['Color'])
    em.inputs['Strength'].default_value = 1.4
    bm = bmesh.new()
    sklib._bm_box(bm, Vector((0, 0, 0)), (40, 0.1, 22))
    mesh('city_sky', bm, C_SET, (m,), loc=(-1, 24, 4), uv=False)
    lm, nt = sklib._new_mat('city_bokeh')
    uv = _n(nt, 'ShaderNodeUVMap', -900, 0, uv_map='UVMap')
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -700, 0)
    _l(nt, uv.outputs[0], sep.inputs[0])
    cx = _math(nt, 'SUBTRACT', sep.outputs['X'], 0.5, x=-550, y=50)
    cy = _math(nt, 'SUBTRACT', sep.outputs['Y'], 0.5, x=-550, y=-50)
    r = _math(nt, 'SQRT', _math(nt, 'ADD', _math(nt, 'MULTIPLY', cx, cx, x=-400, y=50),
                                _math(nt, 'MULTIPLY', cy, cy, x=-400, y=-50), x=-250, y=0), x=-100, y=0)
    disc = _maprange(nt, r, 0.5, 0.44, 0.0, 1.0, 50, 0)
    rim = _maprange(nt, r, 0.3, 0.47, 0.75, 1.0, 50, -150)
    at = _n(nt, 'ShaderNodeAttribute', -100, 300, attribute_name='Col')
    em = _n(nt, 'ShaderNodeEmission', 400, 200)
    _l(nt, at.outputs['Color'], em.inputs['Color'])
    _l(nt, _math(nt, 'MULTIPLY', rim, 5.0, x=250, y=-150), em.inputs['Strength'])
    tr = _n(nt, 'ShaderNodeBsdfTransparent', 400, 0)
    mx = _n(nt, 'ShaderNodeMixShader', 650, 100)
    _l(nt, disc, mx.inputs[0])
    _l(nt, tr.outputs[0], mx.inputs[1])
    _l(nt, em.outputs[0], mx.inputs[2])
    _l(nt, mx.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 900, 100).inputs['Surface'])
    lm.surface_render_method = 'BLENDED'
    bm = bmesh.new()
    cols = bm.verts.layers.float_color.new('Col')
    uvl = bm.loops.layers.uv.new('UVMap')
    for k in range(150):
        x, z = rng.uniform(-9, 7), rng.uniform(-2.5, 6.5) * rng.random() ** 0.6
        y = rng.uniform(14, 21)
        r_ = rng.random()
        c = sklib.kelvin_rgb(2600 + 2400 * r_) if r_ < 0.85 else (0.7, 0.82, 1.0)
        c = tuple(v * rng.uniform(0.35, 1.0) for v in c) + (1,)
        d = rng.uniform(0.35, 0.8)
        vs = [bm.verts.new((x + dx * d, y, z + dz * d)) for dx, dz in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))]
        f = bm.faces.new(vs)
        for lp, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[uvl].uv = uvv
        for v in vs:
            v[cols] = c
    me = bpy.data.meshes.new('city_bokeh')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(lm)
    sklib.new_obj('city_bokeh', me, C_SET)


# ---------------------------------------------------------------------------------------------- table & chairs
def build_table():
    oak = walnut()
    box('table_top', (0, 0, TOP - 0.02), (1.4, 0.85, 0.04), oak, C_TABLE, 0.006, 3)
    box('table_apron_N', (0, 0.36, TOP - 0.065), (1.1, 0.025, 0.05), oak, C_TABLE, 0.003)
    box('table_apron_S', (0, -0.36, TOP - 0.065), (1.1, 0.025, 0.05), oak, C_TABLE, 0.003)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm = bmesh.new()
            r = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.018, radius2=0.026, depth=TOP - 0.04)
            ob = mesh('table_leg', bm, C_TABLE, (oak,), loc=(sx * 0.6, sy * 0.33, (TOP - 0.04) / 2), smooth=True)
            sklib.bevel(ob, 0.003, 2)


def chair(name, x, rot, seat_z):
    oak = walnut()
    root = sklib.new_obj(name, None, C_TABLE)
    parts = [box(name + '.seat', (0, 0, seat_z - 0.018), (0.44, 0.44, 0.036), oak, C_TABLE, 0.008, 3)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = seat_z - 0.036
            parts.append(box(name + '.leg', (sx * 0.19, sy * 0.19, h / 2), (0.035, 0.035, h), oak, C_TABLE, 0.004))
    for sx in (-1, 1):      # back posts behind the sitter (+y local = behind)
        parts.append(box(name + '.post', (sx * 0.19, 0.205, seat_z + 0.22), (0.032, 0.03, 0.44), oak, C_TABLE, 0.004,
                         rot=(-8 * D2R, 0, 0)))
    for z in (0.20, 0.36):
        parts.append(box(name + '.slat', (0, 0.215 + z * 0.14, seat_z + z), (0.38, 0.022, 0.07), oak, C_TABLE, 0.004,
                         rot=(-8 * D2R, 0, 0)))
    for p in parts:
        parent_keep(p, root)
    root.location, root.rotation_euler = (x, 0, 0), (0, 0, rot)
    return root


# -------------------------------------------------------------------------------------------------- tableware
PLATE_PROF = [(0, 0.004), (0.085, 0.004), (0.09, 0.0), (0.098, 0.0), (0.104, 0.006), (0.118, 0.015), (0.148, 0.021),
              (0.152, 0.024), (0.149, 0.026), (0.12, 0.019), (0.104, 0.010), (0, 0.010)]


def plate(name, loc):
    return lathe(name, PLATE_PROF, C_TABLE, ceramic(), 72, loc)


def wine_glass(name, loc, fill=0.4):
    g = glass_mat()
    t = 0.0012
    outer = [(0, 0), (0.036, 0.0), (0.037, 0.002), (0.012, 0.005), (0.004, 0.012), (0.0035, 0.085), (0.008, 0.094),
             (0.03, 0.11), (0.043, 0.14), (0.044, 0.165), (0.039, 0.2), (0.037, 0.21)]
    inner = [(0.037 - t, 0.21), (0.039 - t, 0.2), (0.044 - t, 0.165), (0.043 - t, 0.14), (0.03 - t, 0.112),
             (0.008, 0.098), (0, 0.097)]
    ob = lathe(name, outer + inner, C_TABLE, g, 64, loc)
    zt = 0.098 + fill * 0.07
    w = [(0, 0.0975), (0.008, 0.0985), (0.03 - t - 0.0003, 0.1125), (0.0415, 0.14)]
    prof = [p for p in w if p[1] <= zt] + [(_r_at(w, zt), zt), (0, zt)]
    lathe(name + '.wine', prof, C_TABLE, liquid_mat('red_wine', (0.36, 0.015, 0.035), 1.34), 64, loc)
    return ob


def _r_at(prof, z):
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / max(z1 - z0, 1e-6)
    return prof[-1][0]


def tumbler(name, loc, fill=0.65):
    t = 0.0022
    prof = [(0, 0), (0.033, 0), (0.034, 0.003), (0.037, 0.095), (0.037 - t, 0.095), (0.034 - t, 0.012), (0, 0.012)]
    ob = lathe(name, prof, C_TABLE, glass_mat(), 64, loc)
    zt = 0.012 + fill * 0.08
    lathe(name + '.water', [(0, 0.0122), (0.0315, 0.0122), (0.0318 + 0.03 * (zt - 0.012) / 0.083, zt), (0, zt)],
          C_TABLE, liquid_mat('water', (0.95, 0.98, 1.0)), 64, loc)
    return ob


def cutlery(name, kind):
    """Fork / knife along local +X (tip at +X, handle end at x=0), ~0.2 m, polished stainless. Every station is a
    rounded (elliptic) section, so highlights roll across the handle like real flatware; fork tines are tapered
    rounded rods, the knife blade thins to an edge."""
    bm = bmesh.new()
    seg = 12
    if kind == 'fork':
        prof = [(0.0, 0.0085, 0.0034), (0.012, 0.0105, 0.0036), (0.06, 0.0115, 0.0032), (0.095, 0.0068, 0.0028),
                (0.118, 0.0042, 0.0034), (0.13, 0.0058, 0.0026), (0.145, 0.0105, 0.0022), (0.153, 0.0118, 0.002)]
    else:
        prof = [(0.0, 0.0085, 0.0062), (0.012, 0.0098, 0.0068), (0.085, 0.0095, 0.0058), (0.1, 0.0062, 0.0042),
                (0.108, 0.0072, 0.0016), (0.15, 0.0098, 0.0012), (0.19, 0.0088, 0.001), (0.208, 0.004, 0.0008)]
    zc = lambda x: (0.006 * math.sin(min(x / 0.155, 1.0) * math.pi) - 0.0035 * min(max(x - 0.13, 0) / 0.04, 1)) \
        if kind == 'fork' else 0.0025 * math.sin(min(x / 0.1, 1.0) * math.pi)
    rows = []
    for x, w, th in prof:
        z = zc(x)
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            ca, sa = math.cos(a), math.sin(a)
            yy = w * math.copysign(abs(ca) ** 0.6, ca)              # superellipse: flat top, rounded sides
            zz = th / 2 * math.copysign(abs(sa) ** 0.8, sa)
            if kind == 'knife' and x > 0.105:
                zz *= (1 - 0.85 * max(0.0, -ca))                      # blade thins to the cutting edge (-y side)
            ring.append(bm.verts.new((x, yy, z + zz)))
        rows.append(ring)
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(seg):
            bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])
    if kind == 'fork':
        x0, L = 0.152, 0.042
        for i in range(4):
            y0 = -0.0118 + 0.0016 + i * (0.0236 - 0.0032) / 3
            trows = []
            for t in (0.0, 0.5, 0.85, 1.0):
                x = x0 + t * L
                r_ = 0.0013 * (1 - 0.55 * t ** 2)
                z = zc(0.153) - 0.0035 * t * t * 0.4 - 0.001 * t
                trows.append([bm.verts.new((x, y0 + r_ * math.cos(2 * math.pi * k / 8),
                                            z + r_ * 0.8 * math.sin(2 * math.pi * k / 8))) for k in range(8)])
            for r0, r1 in zip(trows, trows[1:]):
                for k in range(8):
                    bm.faces.new((r0[k], r0[(k + 1) % 8], r1[(k + 1) % 8], r1[k]))
            bm.faces.new(trows[-1])
    ob = mesh(name, bm, C_TABLE, (cutlery_mat(),))
    ob.data.shade_smooth()
    return ob


def cutlery_mat():
    """Polished 18/10 stainless flatware: bright metal, low roughness with fine wipe streaks + fingerprint smudges."""
    m = bpy.data.materials.get('flatware')
    if m:
        return m
    m, nt = sklib._new_mat('flatware')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 700, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 1000, 0).inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -700, 0)
    mp = _n(nt, 'ShaderNodeMapping', -500, 0)
    mp.inputs['Scale'].default_value = (40.0, 1500.0, 1500.0)           # streaks along the handle
    _l(nt, tc.outputs['Object'], mp.inputs['Vector'])
    st = _noise(nt, mp.outputs[0], 1.0, 4.0, 0.5, -300, 0)
    sm = _noise(nt, tc.outputs['Object'], 160.0, 3.0, 0.6, -300, -250)    # smudges
    r = _math(nt, 'MULTIPLY_ADD', _maprange(nt, sm.outputs['Fac'], 0.5, 0.7, 0.0, 0.12, -100, -250), 1.0,
              x=100, y=-100, c=_maprange(nt, st.outputs['Fac'], 0.3, 0.7, 0.05, 0.12, -100, 0))
    _l(nt, r, b.inputs['Roughness'])
    b.inputs['Base Color'].default_value = (0.78, 0.77, 0.75, 1)
    b.inputs['Metallic'].default_value = 1.0
    return m


def napkin(name, loc, rot, size=(0.2, 0.14)):
    bm = bmesh.new()
    nx, ny = 40, 28
    vs = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x, y = (u - 0.5) * size[0], (v - 0.5) * size[1]
            z = 0.006 * (1 - abs(2 * v - 1)) ** 0.5 + 0.0025 * math.sin(u * 4.1 + v * 2.3) \
                + 0.0012 * math.sin(u * 9.0 - v * 5.0) * u
            row.append(bm.verts.new((x, y, z)))
        vs.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    ob = mesh(name, bm, C_TABLE, (sklib.pbr('napkin_linen', 'rough_linen', scale=0.3, tint=(0.863, 0.791, 0.672), contrast=0.5, wear=0.04, ao_dist=0.05, rough=(0.75, 1.0)),), loc=loc, rot=(0, 0, rot), smooth=True)
    sol = ob.modifiers.new('sol', 'SOLIDIFY')
    sol.thickness, sol.offset = 0.0025, 1
    return ob


def candle(loc):
    holder = lathe('candle_holder', [(0, 0), (0.04, 0), (0.042, 0.004), (0.036, 0.05), (0.033, 0.05),
                                     (0.035, 0.006), (0, 0.006)], C_TABLE, glass_mat(), 48, loc)
    wax = food_mat('candle_wax', (0.9, 0.87, 0.8), (0.3, 0.25, 0.18), rough=0.35, coat=0.0, sss=0.8, bump=0.05)
    lathe('candle', [(0, 0.006), (0.024, 0.006), (0.024, 0.075), (0.02, 0.079), (0.003, 0.076), (0, 0.077)],
          C_TABLE, wax, 32, loc)
    fm, nt = sklib._new_mat('flame')
    em = _n(nt, 'ShaderNodeEmission', 0, 0)
    em.inputs['Color'].default_value = sklib.kelvin_rgb(1900) + (1,)
    em.inputs['Strength'].default_value = 60.0
    _l(nt, em.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 300, 0).inputs['Surface'])
    fl = lathe('candle_flame', [(0, 0.082), (0.0035, 0.087), (0.0028, 0.094), (0, 0.104)], C_TABLE, fm, 16, loc)
    L = bpy.data.lights.new('candle', 'POINT')
    L.energy, L.color, L.shadow_soft_size = 2.7, amber('#ffb46b'), 0.006
    L.use_shadow = False
    lo = sklib.new_obj('L_candle', L, C_LIGHT, loc=Vector(loc) + Vector((0, 0, 0.092)))
    L.keyframe_insert('energy', frame=1)
    fc = L.animation_data.action
    for c in sklib._fcurves(L):
        md = c.modifiers.new('NOISE')
        md.scale, md.strength, md.phase = 3.0, 0.5, 7.0
    return lo


def phone(loc, rot):
    bm = bmesh.new()
    sklib._bm_box(bm, Vector((0, 0, 0.004)), (0.147, 0.072, 0.0078))
    ob = mesh('phone', bm, C_TABLE, (sklib.plastic((0.035, 0.037, 0.04), 0.1, 'phone_back'),), loc=loc,
              rot=(0, 0, rot))
    sklib.bevel(ob, 0.006, 4, 40)
    bm = bmesh.new()
    sklib._bm_box(bm, Vector((0.045, 0.018, 0.0085)), (0.04, 0.03, 0.0016))
    cb = mesh('phone_cambump', bm, C_TABLE, (sklib.plastic((0.02, 0.02, 0.022), 0.05, 'phone_bump'),))
    sklib.bevel(cb, 0.004, 3, 40)
    cb.parent = ob
    return ob


def bread(loc):
    oak = sklib.oak_table(0.2)
    lathe('bread_board', [(0, 0), (0.12, 0), (0.125, 0.004), (0.125, 0.014), (0.12, 0.018), (0, 0.018)], C_TABLE,
          oak, 48, loc)
    crumb, nt = sklib._new_mat('bread_crumb')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 700, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 1000, 0).inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    vo = _n(nt, 'ShaderNodeTexVoronoi', -650, 0)
    vo.inputs['Scale'].default_value = 260.0
    _l(nt, tc.outputs['Object'], vo.inputs['Vector'])
    holes = _maprange(nt, vo.outputs['Distance'], 0.04, 0.3, 1.0, 0.0, -450, 0)
    rad = _n(nt, 'ShaderNodeVectorMath', -650, 300, operation='LENGTH')
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -850, 300)
    _l(nt, tc.outputs['Object'], sep.inputs[0])
    cmb = _n(nt, 'ShaderNodeCombineXYZ', -750, 300)
    _l(nt, sep.outputs['X'], cmb.inputs['X'])
    _l(nt, _math(nt, 'MULTIPLY', sep.outputs['Y'], 1.35, x=-850, y=420), cmb.inputs['Y'])
    _l(nt, cmb.outputs[0], rad.inputs[0])
    crust = _maprange(nt, rad.outputs['Value'], 0.043, 0.051, 0.0, 1.0, -450, 300)
    col = _mix(nt, holes, (0.8, 0.7, 0.52), (0.38, 0.28, 0.17), 'MIX', -200, 150)
    col = _mix(nt, crust, col, (0.2, 0.09, 0.03), 'MIX', 100, 200)
    _l(nt, col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    b.inputs['Subsurface Weight'].default_value = 0.15
    b.inputs['Subsurface Radius'].default_value = (0.4, 0.3, 0.2)
    b.inputs['Subsurface Scale'].default_value = 0.003
    bp = _n(nt, 'ShaderNodeBump', 400, -250)
    bp.inputs['Strength'].default_value = 0.7
    bp.inputs['Distance'].default_value = 0.0015
    _l(nt, holes, bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    for i in range(3):      # sourdough slices shingled on the board
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=8, radius=1.0)
        for v in bm.verts:
            ang = math.atan2(v.co.y, v.co.x)
            wob = 1 + 0.06 * math.sin(3 * ang + i * 2.1) + 0.025 * math.sin(7 * ang + i) + 0.04 * math.cos(ang)
            v.co = Vector((v.co.x * 0.058 * wob, v.co.y * 0.043 * wob, max(-1, min(1, v.co.z * 3)) * 0.0065))
        ob = mesh('bread_slice_%d' % i, bm, C_TABLE, (crumb,), uv=False, smooth=True,
                  loc=Vector(loc) + Vector((-0.04 + i * 0.035, 0.0 + i * 0.008, 0.026 + i * 0.006)),
                  rot=(0, -14 * D2R, (10 + i * 7) * D2R))
    crumbs(Vector(loc) + Vector((0.0, -0.13, -0.0)), 26, 0.07, 'crumbs_bread', crumb)


def crumbs(center, n, spread, name, mat, z=0.0, size=0.0025):
    bm = bmesh.new()
    for i in range(n):
        p = Vector((center.x + rng.gauss(0, spread), center.y + rng.gauss(0, spread * 0.6), 0))
        r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size * rng.uniform(0.4, 1.2))
        for v in r['verts']:
            v.co = Vector((v.co.x * rng.uniform(0.6, 1.4), v.co.y * rng.uniform(0.6, 1.4), v.co.z * 0.6)) + p
            v.co.z += size * 0.3
    return mesh(name, bm, C_TABLE, (mat,), loc=(0, 0, TOP + z), uv=False)


# ----------------------------------------------------------------------------------------------------------- food
_PRAWN = {}


def prawn_source():
    """CC0 green tiger prawn scan (raw, antennae + colour checker removed), decimated, ~0.12 m long, length = +X
    (head at -X), dorsal +Z, origin at the underside centre. Kept unlinked as the shared mesh."""
    if 'me' in _PRAWN:
        return _PRAWN['me'], _PRAWN['mat']
    before = set(o.name for o in bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=PRAWN_SCAN)
    new = [o for o in bpy.data.objects if o.name not in before]
    new_names = [o.name for o in new]
    ms = [o for o in new if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(ms) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    for nm in new_names:
        o = bpy.data.objects.get(nm)
        if o is not None and o != ob:
            bpy.data.objects.remove(o, do_unlink=True)
    me = ob.data
    body_mi = [i for i, m in enumerate(me.materials) if m and (m.name.startswith('Q11545') or m.name.startswith('PRAWN_SHELL'))]
    img = None
    for n in me.materials[body_mi[0]].node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image:
            img = n.image
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in body_mi], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for f in bm.faces:
        f.material_index = 0
    bm.to_mesh(me)
    bm.free()
    if me.uv_layers:
        me.uv_layers[0].name = 'UVMap_scan'
    ob.data.materials.clear()
    dm = ob.modifiers.new('dec', 'DECIMATE')
    dm.ratio = min(1.0, 30000.0 / max(1, len(me.polygons)))
    sklib.apply_mods(ob)
    me = ob.data
    me.use_fake_user = True
    co = [v.co for v in me.vertices]
    mn = Vector([min(c[i] for c in co) for i in range(3)])
    mx = Vector([max(c[i] for c in co) for i in range(3)])
    k = 0.10 / (mx.x - mn.x)
    cx = (mn.x + mx.x) / 2
    ztop = max(c.z for c in co if abs(c.x - cx) < 0.05 * (mx.x - mn.x))
    zc = ztop - 0.0105 / k                      # body centre line ~10 mm under the back at mid-length
    me.transform(Matrix.Diagonal((k, k, k, 1)) @ Matrix.Translation(-Vector((cx, (mn.y + mx.y) / 2, zc))))
    # cooked + skewered: walking legs / swimmerets are trimmed (they read as a hairy fringe at macro distance)
    bm = bmesh.new()
    bm.from_mesh(me)
    cut = [v for v in bm.verts if v.co.z < -0.0105 and -0.04 < v.co.x < 0.035]
    bmesh.ops.delete(bm, geom=cut, context='VERTS')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    mat = prawn_cooked(img)
    me.materials.append(mat)
    bpy.data.objects.remove(ob, do_unlink=True)
    me.name = 'A-PROD-PRAWN_cooked'
    me.use_fake_user = True
    _PRAWN['me'], _PRAWN['mat'] = me, mat
    print('PRAWN tris', len(me.polygons), 'dims', (mx - mn) * k)
    return me, mat


def skewer(name, origin, yaw, n=3, seed=0):
    """n grilled prawns threaded lengthwise head-to-tail on a bamboo stick (root local X), lying on their sides;
    root z = the stick / body centre line."""
    me, _ = prawn_source()
    r = random.Random(seed)
    root = sklib.new_obj(name, None, C_FOOD, loc=origin, rot=(0, 0, yaw))
    root.empty_display_size = 0.05
    gap = 0.091
    for i in range(n):
        sklib.new_obj('%s.prawn_%d' % (name, i), me, C_FOOD, root,
                      loc=((i - (n - 1) / 2) * gap + r.uniform(-0.003, 0.003), 0, 0),
                      rot=(math.pi / 2 + r.uniform(-0.25, 0.25), r.uniform(-0.04, 0.04), r.uniform(-0.05, 0.05)))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.0022, radius2=0.0008, depth=0.34,
                          matrix=Matrix.Rotation(math.pi / 2, 4, 'Y'))
    stick = mesh(name + '.stick', bm, C_FOOD, (bamboo_mat(),), smooth=True)
    stick.parent = root
    return root


def bamboo_mat():
    m = bpy.data.materials.get('bamboo_skewer')
    if m:
        return m
    m = sklib.pbr('bamboo_skewer', 'kitchen_wood', tint=(0.78, 0.62, 0.42), scale=0.15, wear=0.5,
                  wear_color=(0.08, 0.05, 0.03), rough=(0.5, 0.8), contrast=0.4)
    return m


def tuna_slices(name, origin, yaw, n=5):
    """Slices cut from one seared loin and fanned: each slice is a rounded, slightly wedge-shaped section whose
    outline wobbles (knife + muscle flakes), sizes taper toward the loin ends."""
    m = tuna_mat()
    root = sklib.new_obj(name, None, C_FOOD, loc=origin, rot=(0, 0, yaw))
    r = random.Random(len(name))
    for i in range(n):
        t = i / max(1, n - 1)
        k = 0.82 + 0.18 * math.sin(math.pi * (0.15 + 0.7 * t))          # loin tapers toward both ends
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
        ph = r.uniform(0, 6)
        for v in bm.verts:
            x, y, z = v.co
            wob = 1 + 0.05 * math.sin(z * 9 + ph) + 0.03 * math.sin(y * 13 + ph * 2) + r.uniform(-0.006, 0.006)
            v.co = Vector((x * (0.0085 + 0.0025 * (z + 0.5)),                  # slightly wedge-cut
                           y * 0.064 * k * (1 - 0.18 * (2 * z) ** 2) * wob,
                           z * 0.025 * k * (1 - 0.22 * (2 * y) ** 4) * wob))
        ob = mesh('%s.slice_%d' % (name, i), bm, C_FOOD, (m,), uv=False, smooth=True)
        sklib.bevel(ob, 0.0022, 3, 30)
        ob.parent = root     # fanned row: cut faces up, each slice resting on the previous one
        ob.location = (-i * 0.0158, 0.003 * math.sin(i * 1.7) + r.uniform(-0.002, 0.002), 0.0105 + i * 0.0021)
        ob.rotation_euler = (r.uniform(-0.05, 0.05), -76 * D2R + r.uniform(-0.05, 0.05), i * 0.04 + r.uniform(-0.04, 0.04))
    return root


def leaves(name, center, radius, count, seed=3):
    """Loose salad: wild rocket (long, few rounded lobes) + baby spinach (ovate, cupped), each leaf cupped, arched
    and twisted, heaped low in the middle."""
    r = random.Random(seed)
    mats = [leaf_mat('leaf_rocket', (0.035, 0.1, 0.018)), leaf_mat('leaf_dark', (0.018, 0.065, 0.012)),
            leaf_mat('leaf_frisee', (0.12, 0.24, 0.04))]
    bm = bmesh.new()
    for k in range(count):
        spin = r.random() < 0.4
        L = r.uniform(0.032, 0.048) if spin else r.uniform(0.045, 0.075)
        W = r.uniform(0.011, 0.016) if spin else r.uniform(0.005, 0.008)
        nu, nv = 12, 6
        a = r.uniform(0, 2 * math.pi)
        d = radius * math.sqrt(r.random())
        h = (1 - (d / radius) ** 2) * 0.022
        M = Matrix.Translation(center + Vector((d * math.cos(a), d * math.sin(a), h + 0.002))) @ \
            Euler((r.uniform(-0.7, 0.7), r.uniform(-0.5, 0.5), r.uniform(0, 6.28))).to_matrix().to_4x4()
        lob, nl, ph = r.uniform(0.3, 0.8), r.choice((3.5, 4.5, 5.5)), r.uniform(0, 1)
        cup, arch, tw = r.uniform(0.25, 0.6), r.uniform(-0.004, 0.008), r.uniform(-0.6, 0.6)
        grid = []
        for i in range(nu + 1):
            u = i / nu
            if spin:
                w = W * math.sin(math.pi * min(1.0, u ** 0.8 * 1.02)) ** 0.75
            else:
                w = W * math.sin(math.pi * min(u * 1.05, 1)) ** 0.6 * (1 + lob * max(0.0, math.sin((u + ph) * math.pi * nl)) * (1 - u))
            row = []
            for j in range(nv + 1):
                t = j / nv * 2 - 1
                z = cup * W * t * t + arch * u * u + 0.0015 * math.sin(u * 11 + k + t * 3)
                y = t * w
                c, s_ = math.cos(tw * u), math.sin(tw * u)
                row.append(bm.verts.new(M @ Vector((u * L - L / 2, y * c - z * s_, y * s_ + z * c))))
            grid.append(row)
        mi = 1 if spin else (2 if r.random() < 0.12 else 0)
        for i in range(nu):
            for j in range(nv):
                f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
                f.material_index = mi
    ob = mesh(name, bm, C_FOOD, mats, uv=False, smooth=True)
    sol = ob.modifiers.new('sol', 'SOLIDIFY')
    sol.thickness = 0.0005
    return ob


def lemon_wedge(name, loc, rot):
    peel = food_mat('lemon_peel', (0.85, 0.62, 0.05), (0.6, 0.5, 0.1), rough=0.35, coat=0.3, sss=0.2, bump=0.5,
                    scale=900)
    flesh = lemon_flesh_mat()
    bm = bmesh.new()
    nu, nf = 20, 10
    A, R, phi = 0.038, 0.026, 62 * D2R
    rows = []
    for i in range(nu + 1):
        u = -1 + 2 * i / nu
        rr = R * math.sqrt(max(0.0, 1 - u * u)) ** 0.9
        rows.append([bm.verts.new((A * u, rr * math.cos(phi * (j / nf - 0.5)), rr * math.sin(phi * (j / nf - 0.5))))
                     for j in range(nf + 1)])
    axis = [bm.verts.new((A * (-1 + 2 * i / nu) * 0.92, 0, 0)) for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nf):
            bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1])).material_index = 0
        for side in (0, nf):       # two cut faces
            f = bm.faces.new((axis[i], axis[i + 1], rows[i + 1][side], rows[i][side]))
            f.material_index = 1
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = mesh(name, bm, C_FOOD, (peel, flesh), loc=loc, rot=rot, uv=False, smooth=True)
    ob.data.set_sharp_from_angle(angle=40 * D2R)
    return ob


def lemon_flesh_mat():
    m = bpy.data.materials.get('lemon_flesh')
    if m:
        return m
    m, nt = sklib._new_mat('lemon_flesh')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 900, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 1200, 0).inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -1200, 0)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -1000, 0)
    _l(nt, tc.outputs['Object'], sep.inputs[0])
    cy = _n(nt, 'ShaderNodeCombineXYZ', -850, 0)
    _l(nt, sep.outputs['Y'], cy.inputs['Y'])
    _l(nt, sep.outputs['Z'], cy.inputs['Z'])
    ln = _n(nt, 'ShaderNodeVectorMath', -700, 0, operation='LENGTH')
    _l(nt, cy.outputs[0], ln.inputs[0])
    xr = _math(nt, 'DIVIDE', sep.outputs['X'], 0.038, x=-850, y=-200)
    rr = _math(nt, 'SQRT', _math(nt, 'MAXIMUM', _math(nt, 'SUBTRACT', 1.0, _math(nt, 'POWER', xr, 2.0, x=-700, y=-200),
                                                      x=-550, y=-200), 0.02, x=-400, y=-200), x=-250, y=-200)
    ratio = _math(nt, 'DIVIDE', ln.outputs['Value'], _math(nt, 'MULTIPLY', rr, 0.026, x=-100, y=-200), x=50, y=-100)
    pith = _maprange(nt, ratio, 0.8, 0.86, 0.0, 1.0, 200, -100)
    vo = _n(nt, 'ShaderNodeTexVoronoi', -700, 300)
    vo.inputs['Scale'].default_value = 450.0
    _l(nt, tc.outputs['Object'], vo.inputs['Vector'])
    ves = _maprange(nt, vo.outputs['Distance'], 0.0, 0.5, 0.0, 1.0, -450, 300)
    col = _mix(nt, ves, (1.0, 0.86, 0.32), (0.92, 0.72, 0.14), 'MIX', 200, 250)
    col = _mix(nt, pith, col, (0.96, 0.93, 0.78), 'MIX', 450, 200)
    _l(nt, col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.12
    b.inputs['Coat Weight'].default_value = 0.8
    b.inputs['Subsurface Weight'].default_value = 0.7
    b.inputs['Subsurface Radius'].default_value = (0.9, 0.8, 0.3)
    b.inputs['Subsurface Scale'].default_value = 0.004
    bp = _n(nt, 'ShaderNodeBump', 600, -300)
    bp.inputs['Strength'].default_value = 0.6
    bp.inputs['Distance'].default_value = 0.0006
    _l(nt, ves, bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    return m


def sauce_smear(name, center, r0, a0, a1, width=0.016):
    sm = food_mat('sauce_chili_butter', (0.22, 0.05, 0.012), (0.6, 0.2, 0.05), rough=0.12, coat=1.0, sss=0.5,
                  bump=0.2, scale=150)
    bm = bmesh.new()
    n = 40
    rows = []
    for i in range(n + 1):
        t = i / n
        a = a0 + (a1 - a0) * t
        w = width * math.sin(math.pi * t) ** 0.6 * (1 - 0.6 * t) + 0.0015
        rr = r0 + 0.004 * math.sin(t * 9)
        c = Vector((math.cos(a), math.sin(a), 0))
        rows.append([bm.verts.new(c * (rr + w * (j / 4 - 0.5)) + Vector((0, 0, 0.0008 * math.sin(math.pi * j / 4))))
                     for j in range(5)])
    for a, b in zip(rows, rows[1:]):
        for j in range(4):
            bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
    ob = mesh(name, bm, C_FOOD, (sm,), loc=center, uv=False, smooth=True)
    sol = ob.modifiers.new('sol', 'SOLIDIFY')
    sol.thickness, sol.offset = 0.0012, 1
    return ob


def herb_flecks(name, center, n, spread, z):
    m = leaf_mat('parsley', (0.07, 0.22, 0.03))
    bm = bmesh.new()
    for i in range(n):
        p = center + Vector((rng.gauss(0, spread), rng.gauss(0, spread), z))
        s_ = rng.uniform(0.0012, 0.0028)
        vs = [bm.verts.new(p + Vector((s_ * math.cos(a + i), s_ * math.sin(a + i) * 0.7, rng.uniform(-0.0005, 0.0005))))
              for a in (0, 2.1, 4.2)]
        bm.faces.new(vs)
    ob = mesh(name, bm, C_FOOD, (m,), uv=False)
    return ob


def dish(prefix, c, yaw, flip=1):
    """One dinner plate of grilled skewers + seared tuna on greens + lemon + chili-butter smear. c = plate centre."""
    pl = plate(prefix + '.plate', c)
    zp = c.z + 0.010
    R = Matrix.Rotation(yaw, 3, 'Z')
    P = lambda x, y, z=0.0: c + R @ Vector((x, y, zp - c.z + z))
    leaves(prefix + '.greens', P(0.045, 0.0), 0.062, 70, seed=len(prefix))
    tuna_slices(prefix + '.tuna', P(-0.06, -0.05 * flip, -0.003), yaw - math.pi / 2 + 0.12, 6)
    skewer(prefix + '.skewer_a', P(0.025, 0.0, 0.019), yaw + math.pi / 2 + 0.06, 3, seed=1 + len(prefix))
    skewer(prefix + '.skewer_b', P(0.072, 0.008, 0.019), yaw + math.pi / 2 - 0.05, 3, seed=7 + len(prefix))
    lemon_wedge(prefix + '.lemon', P(-0.07, 0.075 * flip, 0.02), (-0.9, 0, yaw + 0.7))
    sauce_smear(prefix + '.smear', P(0, 0, 0.0002), 0.093, yaw + 3.5, yaw + 4.6)
    return pl


# ---------------------------------------------------------------------------------------------------- kitchen
def build_kitchen():
    dark = sklib.pbr('cabinet_dark', 'kitchen_wood', tint=(0.055, 0.06, 0.058), contrast=0.25, rough=(0.3, 0.6),
                     wear=0.06, ao_dist=0.1, var=0.04)
    stone = sklib.pbr('counter_stone', 'marble_01', scale=1.0, wear=0.05, rough=(0.08, 0.3), ao_dist=0.1)
    tiles = sklib.pbr('splash_tiles', 'long_white_tiles', scale=2.2, wear=0.06, ao_dist=0.2)
    brass = sklib.pbr('brass', 'blue_metal_plate', tint=(0.75, 0.55, 0.25), rough=(0.25, 0.45), metal=1.0, nor=0.2,
                      wear=0.1, contrast=0.3)
    # tall pantry cabinet (left of the counter): the dark type-zone block for f130-216
    box('pantry', (1.9, 1.6, 1.15), (1.1, 0.6, 2.3), dark, C_KITCHEN, 0.004)
    for x in (1.625, 2.175):
        box('pantry_door_gap', (x + 0.27 * (1 if x < 2 else -1), 1.297, 1.15), (0.004, 0.006, 2.2), stone, C_KITCHEN, 0)
        box('pantry_handle', (1.9 + (0.03 if x > 2 else -0.03), 1.28, 1.05), (0.012, 0.02, 0.35), brass, C_KITCHEN,
            0.004)
    # base cabinets + stone top
    box('base_cab', (3.6, 1.6, 0.44), (2.3, 0.6, 0.86), dark, C_KITCHEN, 0.004)
    box('plinth', (3.6, 1.62, 0.04), (2.3, 0.56, 0.08), dark, C_KITCHEN, 0.002)
    for i in range(4):
        x = 2.55 + 0.575 * i
        box('base_gap_%d' % i, (x, 1.297, 0.47), (0.004, 0.006, 0.78), stone, C_KITCHEN, 0)
        box('base_handle_%d' % i, (x + 0.3, 1.285, 0.8), (0.18, 0.016, 0.012), brass, C_KITCHEN, 0.003)
    box('countertop', (3.6, 1.58, 0.90), (2.32, 0.66, 0.04), stone, C_KITCHEN, 0.004, 3)
    box('backsplash', (3.6, 1.895, 1.18), (2.3, 0.01, 0.52), tiles, C_KITCHEN, 0)
    box('upper_cab', (4.1, 1.725, 1.82), (1.3, 0.35, 0.72), dark, C_KITCHEN, 0.004)
    # kettle, bowl of lemons, cutting board, plant
    st = sklib.stainless(0.08)
    k = lathe('kettle', [(0, 0), (0.08, 0), (0.088, 0.01), (0.092, 0.06), (0.085, 0.13), (0.05, 0.175), (0.02, 0.185),
                         (0.022, 0.195), (0, 0.197)], C_KITCHEN, st, 48, (4.25, 1.72, 0.92))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.012, radius2=0.006, depth=0.12,
                          matrix=Matrix.Translation((4.25 - 0.12, 1.72, 0.92 + 0.11)) @ Matrix.Rotation(-0.8, 4, 'Y'))
    mesh('kettle_spout', bm, C_KITCHEN, (st,), smooth=True)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, segments=24, radius=0.07)
    bm.free()
    cu = bpy.data.curves.new('kettle_handle', 'CURVE')
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = '3D', 0.009, 4
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(2)
    for bp_, co in zip(sp.bezier_points, ((4.19, 1.72, 1.1), (4.25, 1.72, 1.19), (4.31, 1.72, 1.1))):
        bp_.co = co
        bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
    cu.materials.append(sklib.plastic((0.03, 0.03, 0.03), 0.1, 'handle_black'))
    sklib.new_obj('kettle_handle', cu, C_KITCHEN)
    bowl = lathe('fruit_bowl', [(0, 0), (0.05, 0), (0.06, 0.005), (0.12, 0.06), (0.125, 0.07), (0.118, 0.07),
                                (0.055, 0.012), (0, 0.012)], C_KITCHEN, ceramic(), 64, (4.0, 1.75, 0.92))
    peel = food_mat('lemon_peel', (0.85, 0.62, 0.05), (0.6, 0.5, 0.1))
    for i, (dx, dy, dz) in enumerate([(0, 0, 0.04), (0.05, 0.03, 0.045), (-0.045, 0.025, 0.045), (0.01, -0.05, 0.05)]):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=0.032)
        for v in bm.verts:
            v.co.x *= 1.25
            v.co.x += 0.006 * (abs(v.co.x) / 0.04) ** 6 * (1 if v.co.x > 0 else -1)
        mesh('lemon_%d' % i, bm, C_KITCHEN, (peel,), loc=(4.0 + dx, 1.75 + dy, 0.92 + dz),
             rot=(0, 0.3 * i, 1.1 * i), uv=False, smooth=True)
    box('cutting_board', (3.62, 1.62, 0.932), (0.42, 0.28, 0.024), sklib.oak_table(0.25), C_KITCHEN, 0.006, 3)
    crumbs(Vector((3.65, 1.6, 0)), 12, 0.05, 'crumbs_board', sklib.oak_table(0.25), z=0.944 - TOP, size=0.0018)
    pot = sklib.pbr('terracotta', 'white_plaster_02', tint=(0.55, 0.28, 0.17), contrast=0.6, wear=0.3,
                    wear_color=(0.6, 0.55, 0.48), rough=(0.7, 0.95))
    lathe('plant_pot', [(0, 0), (0.07, 0), (0.09, 0.16), (0.095, 0.17), (0.085, 0.17), (0, 0.16)], C_KITCHEN, pot,
          40, (4.55, 1.7, 0.92))
    pl = leaves('plant_leaves', Vector((0, 0, 0)), 0.04, 30, seed=11)
    pl.scale = (3.0, 3.0, 3.0)
    pl.location = (4.55, 1.7, 1.08)
    # the opened hero carton
    root = sklib.hero_carton(open_amount=1.0, coll=C_KITCHEN, loc=CARTON_LOC, rot_z=0.04)
    return root


# -------------------------------------------------------------------------------------------------- BRIDGE_FROST
def bridge_frost():
    return bridge_frost_mod.build()


# ------------------------------------------------------------------------------------------------------- lights
def amber(h):
    """r6: a warm hex used as the light's *seen* colour (not linearised). look.hex_rgb linearises #ffb46b to
    (1, 0.46, 0.15) -- a deep orange-red light (#ffb46b here -> (1, 0.57, 0.25)) that, with the cool lift, turned the walnut magenta (crop R/G 2.6)."""
    return tuple((a * b) ** 0.5 for a, b in zip(look.hex_rgb(h), look.hex_rgb(h, linear=False)))   # amber, midway


def build_lights():
    def area(name, loc, rot, size, k, energy, sy=None):
        L = bpy.data.lights.new(name, 'AREA')
        L.shape = 'RECTANGLE'
        L.size, L.size_y = size, sy or size
        L.color, L.energy = sklib.kelvin_rgb(k), energy
        return sklib.new_obj(name, L, C_LIGHT, loc=loc, rot=rot)

    def aimed(o, loc, tgt):
        o.location = Vector(loc)
        o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o
    out = {}
    # art #75 (COLOR_SCRIPT 00): cool window fill #5b7da6 ~0.25x the warm key; warm 2900 K key camera-left high; warm
    # candle rim #ff8a3d behind the plates; ceiling/front fills cut back so the room falls into walnut dusk.
    out['window'] = area('L_window', (-1.15, 1.75, 1.35), (math.pi / 2, 0, math.pi), 3.2, 7200, 200, 2.4)
    out['window'].data.color = look.hex_rgb('#5b7da6')
    out['key'] = aimed(area('L_key', (0, 0, 0), (0, 0, 0), 0.9, 2900, 190), (-1.7, -0.5, 2.35), (-0.1, 0.0, TOP))
    out['key'].data.color = amber('#ffb46b')
    for nm, x in (('L_rim_A', -0.42), ('L_rim_B', 0.42)):
        out[nm] = aimed(area(nm, (0, 0, 0), (0, 0, 0), 0.35, 2000, 20), (x, 0.62, 0.98), (x, -0.05, TOP))
        out[nm].data.color = amber('#ffc27a')   # r6: amber rim (orange-red #ff8a3d read pink)
    out['ceil_table'] = area('L_ceil_table', (-0.6, -0.8, 2.66), (0, 0, 0), 1.6, 3200, 28, 1.2)
    out['ceil_kitchen'] = area('L_ceil_kitchen', (3.3, 0.6, 2.66), (0, 0, 0), 1.6, 3200, 40, 1.0)
    out['under_cab'] = area('L_undercab', (4.1, 1.68, 1.44), (0, 0, 0), 1.2, 2900, 45, 0.12)
    out['front_fill'] = area('L_front_fill', (0.6, -2.9, 1.6), (-math.pi / 2, 0, 0), 2.5, 3400, 22, 1.4)
    out['under_cab'].data.color = look.hex_rgb('#ffb46b')
    for k in ('ceil_table', 'ceil_kitchen', 'front_fill'):           # neutral-warm bounce, so amber stays in the pools
        out[k].data.color = (1.0, 0.86, 0.72)
    # pendant over the table: black dome shade, warm bulb, spot down + soft point for the shade glow
    shade = sklib.painted_metal((0.025, 0.025, 0.027), wear=0.05, contrast=0.3)
    lathe('pendant_shade', [(0.0, 1.78), (0.025, 1.78), (0.03, 1.765), (0.12, 1.70), (0.19, 1.60), (0.2, 1.585),
                            (0.195, 1.582), (0.185, 1.596), (0.115, 1.69), (0.028, 1.755), (0, 1.758)],
          C_LIGHT, shade, 64, (0, 0, 0))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.003, radius2=0.003, depth=0.92,
                          matrix=Matrix.Translation((0, 0, 1.78 + 0.46)))
    mesh('pendant_cord', bm, C_LIGHT, (sklib.plastic((0.02, 0.02, 0.02), 0.05, 'cord_black'),), smooth=True)
    bm_, nt = sklib._new_mat('bulb_glow')
    em = _n(nt, 'ShaderNodeEmission', 0, 0)
    em.inputs['Color'].default_value = sklib.kelvin_rgb(2600) + (1,)
    em.inputs['Strength'].default_value = 25.0
    _l(nt, em.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 300, 0).inputs['Surface'])
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.045)
    mesh('pendant_bulb', bm, C_LIGHT, (bm_,), loc=(0, 0, 1.69), uv=False, smooth=True)
    L = bpy.data.lights.new('L_pendant', 'SPOT')
    L.energy, L.color, L.spot_size, L.spot_blend, L.shadow_soft_size = 145, amber('#ffb46b'), 110 * D2R, 0.5, 0.05
    out['pendant'] = sklib.new_obj('L_pendant', L, C_LIGHT, loc=(0, 0, 1.66))
    for k in ('ceil_table', 'ceil_kitchen', 'under_cab', 'front_fill', 'L_rim_A', 'L_rim_B'):   # soft fills: no shadow maps (~40 % faster,
        out[k].data.use_shadow = False                                     # no visible change; window + pendant shade)
    return out


def world():
    """Warm interior ambient mixed (keyed, f200->216) into the studio_small_09 HDRI @0.3 used by BRIDGE_FROST."""
    sklib.hdri('studio_small_09', '1k', 0.3)
    img = next(i for i in bpy.data.images if 'studio_small_09' in i.name)
    w, nt = sklib._world('SK_Table')
    env = _n(nt, 'ShaderNodeTexEnvironment', -400, -100)
    env.image = img
    bg1 = _n(nt, 'ShaderNodeBackground', -100, 150)
    bg1.inputs['Color'].default_value = (*look.hex_rgb('#1d2433'), 1)   # art #75: evening world
    bg1.inputs['Strength'].default_value = 2.5
    bg2 = _n(nt, 'ShaderNodeBackground', -100, -100)
    _l(nt, env.outputs[0], bg2.inputs['Color'])
    bg2.inputs['Strength'].default_value = 0.3
    mx = _n(nt, 'ShaderNodeMixShader', 150, 0)
    _l(nt, bg1.outputs[0], mx.inputs[1])
    _l(nt, bg2.outputs[0], mx.inputs[2])
    _l(nt, mx.outputs[0], _n(nt, 'ShaderNodeOutputWorld', 400, 0).inputs[0])
    for f, v in ((200, 0.0), (214, 1.0)):
        mx.inputs[0].default_value = v
        mx.inputs[0].keyframe_insert('default_value', frame=f)
    return w


# -------------------------------------------------------------------------------------------------------- diners
def seat_height(rig):
    """Lowest body vertex near the hips (buttocks) -> chair seat top."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hip = rig.matrix_world @ rig.pose.bones['thigh_l'].head
    mz = hip.z - 0.1
    for o in rig.children:
        if o.type != 'MESH' or o.hide_render:
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            if (w.xy - hip.xy).length < 0.16 and w.z < hip.z:
                mz = min(mz, w.z)
        ev.to_mesh_clear()
    print('SEAT', rig.name, 'hip', hip, 'seat', mz)
    return mz, hip


def hand_frame(rig, s_):
    bpy.context.view_layer.update()
    pb = rig.pose.bones['hand_' + s_]
    return rig.matrix_world @ pb.head, rig.matrix_world @ pb.tail


def build_diners(plateA, plateB):
    """Two diners mid-conversation: seated upright, hands resting in the lap under the table edge (MPFB hands read
    mannequin-like up close, so they stay out of view), heads slightly bowed toward the table. Cutlery is laid on the
    table beside each plate (fork left, knife right of the diner)."""
    out = {}
    specs = [('DinerA', 'male', 0.3, 0.32, 'diner_shirt', -1.02, math.pi / 2, 5, plateA, (4, 3, 2, 6, 12, 0)),
             ('DinerB', 'female', 0.28, 0.68, 'diner_sweater', 1.02, -math.pi / 2, 9, plateB, (6, 4, 3, 4, 16, 8))]
    for name, sex, age, tone, outfit, x, rz, seed, pc, lean in specs:
        rig = people.make_person(name, sex=sex, age=age, skin_tone=tone, outfit=outfit, pose='sit',
                                 location=(x, 0, 0), rotation_z=rz, seed=seed)
        for o in [rig] + list(rig.children):
            for c in o.users_collection:
                c.objects.unlink(o)
            C_PEOPLE.objects.link(o)
        sgn = 1 if x < 0 else -1                       # +1: diner faces +X
        people._set_rot(rig, 'spine_01', lean[0], 0, 0)
        people._set_rot(rig, 'spine_02', lean[1], 0, 0)
        people._set_rot(rig, 'spine_03', lean[2], 0, 0)
        people._set_rot(rig, 'neck_01', lean[3], 0, 0)
        people._set_rot(rig, 'head', lean[4], 0, lean[5])
        for s_, sx in (('l', 1), ('r', -1)):          # forearms on the thighs, hands well under the table top
            people._arm(rig, s_, ('aim', Vector((sx * 0.08, -0.28, -1)), Vector((sx * 0.02, -1, -0.75)),
                                  Vector((sx * 0.01, -1, -0.9))))
        bpy.context.view_layer.update()
        for pb in rig.pose.bones:
            pb['sk_base'] = list(pb.rotation_quaternion)
        sz, hip = seat_height(rig)
        chair(name + '.chair', hip.x - sgn * 0.02, rz, max(0.38, sz - 0.004))
        for s_ in ('l', 'r'):
            h, t = hand_frame(rig, s_)
            print('HAND', name, s_, tuple(round(v, 3) for v in t), 'under table' if t.z < TOP - 0.06 else 'CHECK')
        # cutlery laid flat beside the plate: diner's left = +Y*sgn
        pcv = Vector(pc)
        fork = cutlery(name + '.fork', 'fork')
        knife = cutlery(name + '.knife', 'knife')
        yaw = 0.0 if sgn > 0 else math.pi
        fork.location = pcv + Vector((-sgn * 0.09, sgn * 0.185, 0.0016))
        fork.rotation_euler = (0, 0, yaw + 0.03 * sgn)
        knife.location = pcv + Vector((-sgn * 0.1, -sgn * 0.185, 0.0029))
        knife.rotation_euler = (0, 0, yaw - 0.02 * sgn)
        for ob in (fork, knife):                       # rest on the lowest point
            ob.location.z = pcv.z - min(v.co.z for v in ob.data.vertices) + 0.0002
        out[name] = dict(rig=rig, sgn=sgn, fork=fork, knife=knife, pc=pcv)
    return out


# -------------------------------------------------------------------------------------------------------- camera
def cam_rot(pos, target):
    v = Vector(target) - Vector(pos)
    tilt = math.atan2(v.xy.length, -v.z)
    yaw = math.atan2(-v.x, v.y)
    return Euler((tilt, 0, yaw))


def build_camera(bridge_loc, focus_targets):
    cam = sklib.camera('CAM', 50, (-0.4, 0.09, 1.5), (-0.4, 0.09, 0))
    cam.data.sensor_width = 36
    keys = []
    pA = Vector((-0.40, 0.0, TOP))
    # opening: high-angle food macro over plate A (65 mm, f/2, ~0.5 m) -- prawn skewers sharp, tuna/greens/table
    # falling off in focus; diners' hands rest in their laps, outside this frame
    tgt = Vector((-0.40, -0.03, TOP + 0.02))
    p = Vector((-0.47, -0.40, 1.24))
    keys.append((1, p, cam_rot(p, tgt), 58))
    p = Vector((-0.45, -0.45, 1.31))
    keys.append((45, p, cam_rot(p, tgt + Vector((0.01, 0.01, 0))), 55))
    p = Vector((-0.25, -0.95, 1.95))
    keys.append((90, p, cam_rot(p, (0.0, 0.0, TOP)), 40))
    p = Vector((0.05, -1.6, 1.8))
    keys.append((130, p, cam_rot(p, (0.3, 0.05, TOP)), 35))
    p = Vector((1.2, -2.0, 1.75))
    keys.append((160, p, cam_rot(p, (2.3, 1.2, 1.0)), 35))
    p190 = Vector((3.22, 0.62, 1.78))
    aim190 = Vector((2.70, 1.62, 1.0))
    r190 = cam_rot(p190, aim190)
    keys.append((190, p190, r190, 35))
    # push-in onto the frost patch (BRIDGE_FROST): position eases to 0.12 m above it, lens 35 -> 100, yaw -> 0
    end = bridge_loc + Vector((0, 0, 0.12))
    for f in range(194, 217, 2):
        t = min(1.0, (f - 190) / 22.0)                 # lands at f212, holds still to f216 (no zoom streaks)
        e = t * t * (3 - 2 * t)
        pos = p190.lerp(end, e) + Vector((0, 0, 0.12 * math.sin(math.pi * e) * (1 - e)))
        aim = aim190.lerp(bridge_loc, min(1.0, e * 1.6))
        tilt = cam_rot(pos, aim).x * (1 - e ** 3)
        rot = Euler((tilt, 0, r190.z * (1 - e)))
        lens = 35 * (100 / 35) ** (e ** 1.5)
        if f == 216:
            pos, rot, lens = end, Euler((0, 0, 0)), 100
        keys.append((f, pos, rot, lens))
    sklib.camera_path(cam, keys)
    # DOF: animated focus empty
    fe = sklib.new_obj('CAM_focus', None, C_LIGHT)
    for f, loc in focus_targets:
        fe.location = loc
        fe.keyframe_insert('location', frame=f)
    sklib.ease_keys(fe)
    sklib.dof(cam, fe, 2.0)
    for f, v in ((1, 2.0), (55, 2.0), (100, 2.8)):           # wide open for the macro, f/2.8 from the crane on
        cam.data.dof.aperture_fstop = v
        cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
    sklib.ease_keys(cam.data)
    return cam


# --------------------------------------------------------------------------------------------------------- build
def TABLE_GRADE(s):
    """Per-scene grade (COLOR_SCRIPT §3, complementary): cool window-blue lift under warm 2900 K gain; bounded warm
    haze over the dining area only (no world fog: lead note, a world volume swallows the window/sky)."""
    look.grade(s, lift='#5b7da6', gain='#ffb46b', sat=1.08, contrast=2.0, bloom=0.2, vignette=0.1,
               lift_amt=0.025, gain_amt=0.015)
    gl = next(n for n in s.compositing_node_group.nodes if n.bl_idname == 'CompositorNodeGlare')
    gl.inputs['Size'].default_value = GLARE_SIZE      # the default (0.5) spreads the warm highlights into a full-frame
    gl.inputs['Threshold'].default_value = 1.5        # orange wash; keep bloom on the flame/bulb/glass glints only
    m, nt = sklib._new_mat('table_haze')
    v = _n(nt, 'ShaderNodeVolumePrincipled', 0, 0)
    v.inputs['Color'].default_value = (*look.hex_rgb('#ffcf9a'), 1)
    v.inputs['Density'].default_value = HAZE_DENSITY
    v.inputs['Anisotropy'].default_value = 0.45          # forward scatter: glow around pendant/candle
    _l(nt, v.outputs['Volume'], _n(nt, 'ShaderNodeOutputMaterial', 300, 0).inputs['Volume'])
    hz = box('table_haze', (-0.4, -0.3, 1.33), (4.6, 4.2, 2.62), m, C_SET, 0)   # x<=1.9: kitchen/carton/frost clear
    hz.visible_shadow = False
    e = s.eevee
    e.volumetric_end, e.volumetric_tile_size, e.volumetric_samples = 8.0, '8', 24


HAZE_DENSITY = 0.008
GLARE_SIZE = 0.15


def main():
    build_room()
    build_table()
    lights = build_lights()
    world()
    pA = Vector((-0.40, 0.0, TOP))
    pB = Vector((0.40, 0.0, TOP))
    plA = dish('DishA', pA, -math.pi / 2, 1)
    plB = dish('DishB', pB, math.pi, 1)
    wine_glass('glassA_wine', (-0.16, -0.27, TOP), 0.45)
    tumbler('glassA_water', (-0.27, -0.33, TOP), 0.7)
    wine_glass('glassB_wine', (0.16, 0.27, TOP), 0.35)
    tumbler('glassB_water', (0.27, 0.33, TOP), 0.6)
    napkin('napkinA', (-0.42, 0.29, TOP), 0.08)
    napkin('napkinB', (0.42, -0.29, TOP), math.pi - 0.1)
    candle((0.02, -0.06, TOP))
    phone((0.13, -0.30, TOP), 0.35)
    bread((-0.02, 0.2, TOP))
    crumbs(Vector((-0.25, 0.08, 0)), 10, 0.03, 'crumbs_plateA', bpy.data.materials['bread_crumb'], size=0.002)
    carton = build_kitchen()
    # BRIDGE_FROST: a frosted fold of the inner bag lying flat on the front-left block of the carton
    bc = bridge_frost()
    blk = bpy.data.objects['A-HERO-CARTON.block_01']
    bpy.context.view_layer.update()
    bl = blk.matrix_world.translation
    bridge_loc = Vector((bl.x + 0.02, bl.y - 0.004, bl.z + 0.085 + 0.0045))
    inst = sklib.instance(bc, bridge_loc, 0.0, 'BRIDGE_FROST_inst', C_KITCHEN)
    bpy.data.lights['BRIDGE_FROST_light'].color = look.hex_rgb('#e6f2ff')     # COLOR_SCRIPT §2 BRIDGE_FROST
    kd = bpy.data.lights.new('L_frost_kick', 'AREA')
    kd.size, kd.color, kd.energy, kd.use_shadow = 0.3, look.hex_rgb('#ffb46b'), 2.5, False
    kp = bridge_loc + Vector((-0.45, -0.55, 0.35))                            # from the table side, low
    sklib.new_obj('L_frost_kick', kd, C_LIGHT, loc=kp,
                  rot=(bridge_loc - kp).to_track_quat('-Z', 'Y').to_euler())
    diners = build_diners(pA, pB)
    # room lights fade out as the frost fills the frame (BRIDGE_FROST is lit by its own area light only)
    for nm, o in lights.items():
        if o.type != 'LIGHT':
            continue
        e = o.data.energy
        o.data.keyframe_insert('energy', frame=198)
        o.data.energy = e * 0.02
        o.data.keyframe_insert('energy', frame=214)
        sklib.ease_keys(o.data)
    cam = build_camera(bridge_loc, [(1, pA + Vector((0.0, -0.07, 0.03))), (45, pA + Vector((0.0, -0.065, 0.03))),
                                    (130, Vector((0.05, 0.0, TOP + 0.02))), (165, CARTON_LOC + Vector((0, 0, 0.2))),
                                    (190, CARTON_LOC + Vector((0, 0, 0.2))), (206, bridge_loc + Vector((0, 0, 0.01))),
                                    (216, bridge_loc)])
    s.eevee.use_shadows = True
    path = sklib.finish('table', 'int')
    s.eevee.taa_render_samples = 32          # 32 spp is visually identical here (checked on f100), halves frame time
    look.apply(s, 'table')                   # art #75: AgX MHC, warm haze, grade (after finish: it resets view/compositing)
    TABLE_GRADE(s)
    bpy.ops.wm.save_as_mainfile(filepath=path, relative_remap=True, compress=True)


main()
