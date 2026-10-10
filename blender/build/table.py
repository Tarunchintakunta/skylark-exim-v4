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
from sklib import _n, _l, _math, _mix, _maprange, _noise  # noqa: E402
sys.path.insert(0, REPO + '/assets-src/blender/build')
import bridge_frost as bridge_frost_mod  # noqa: E402

PRAWN_SCAN = REPO + '/assets-src/scans/green-tiger-prawn.glb'   # CC0 ffish.asia (docs/ASSETS.md A-PROD-PRAWN)
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
    m, nt, b = principled('glass_clear', (1, 1, 1), 0.02, **{'Transmission Weight': 1.0, 'IOR': 1.45})
    return refractive(m, 'SLAB')


def liquid_mat(name, color, ior=1.333):
    m, nt, b = principled(name, color, 0.02, **{'Transmission Weight': 1.0, 'IOR': ior})
    return refractive(m, 'SPHERE')


def ceramic():
    m = sklib.pbr('ceramic_white', 'white_plaster_02', tint=(0.93, 0.92, 0.89), rough=(0.05, 0.16), nor=0.03,
                  wear=0.03, wear_color=(0.7, 0.68, 0.64), contrast=0.08, var=0.02)
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
    rp = _n(nt, 'ShaderNodeValToRGB', -550, 300)
    els = rp.color_ramp.elements
    els[0].position, els[0].color = 0.08, (0.42, 0.06, 0.02, 1)
    els[1].position, els[1].color = 0.62, (0.98, 0.62, 0.42, 1)
    e = els.new(0.32)
    e.color = (0.86, 0.26, 0.08, 1)
    e = els.new(0.85)
    e.color = (1.0, 0.86, 0.72, 1)
    _l(nt, bw.outputs[0], rp.inputs[0])
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
    flesh = _mix(nt, _maprange(nt, nv.outputs['Fac'], 0.3, 0.7, 0, 1, -450, 200), (0.16, 0.006, 0.018), (0.27, 0.02, 0.035), 'MIX', -350, 300)
    flesh = _mix(nt, my, flesh, (0.38, 0.12, 0.13), 'MIX', -250, 350)
    fl = _noise(nt, tc.outputs['Object'], 900.0, 2.0, 0.5, -650, 600)            # pepper/sesame flecks
    fk = _maprange(nt, fl.outputs['Fac'], 0.62, 0.68, 0.0, 1.0, -450, 600)
    seared = _mix(nt, fk, (0.17, 0.09, 0.05), (0.02, 0.015, 0.01), 'MIX', -250, 600)
    col = _mix(nt, crust, flesh, seared, 'MIX', 200, 300)
    _l(nt, col, b.inputs['Base Color'])
    _l(nt, _maprange(nt, crust, 0, 1, 0.22, 0.55, 200, 0), b.inputs['Roughness'])
    _l(nt, _maprange(nt, crust, 0, 1, 0.22, 0.02, 200, -150), b.inputs['Subsurface Weight'])
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


def leaf_mat(name, col):
    return food_mat(name, col, (0.2, 0.6, 0.1), rough=0.45, coat=0.25, sss=0.3, bump=0.15, scale=400, var=0.25)


# ----------------------------------------------------------------------------------------------------------- room
def build_room():
    floor = sklib.pbr('floor_parquet', 'herringbone_parquet', scale=1.0, wear=0.12, rough=(0.3, 0.7), ao_dist=0.3)
    wallm = sklib.pbr('wall_warm', 'white_plaster_02', tint=(0.86, 0.80, 0.72), wear=0.06, contrast=0.4, ao_dist=0.4)
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
    oak = sklib.oak_table(0.1)
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
    oak = sklib.oak_table(0.15)
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
    """Fork / knife along local +X (tip at +X, handle end at x=0), 0.2 m long, stainless."""
    bm = bmesh.new()
    L = 0.2
    if kind == 'fork':
        prof = [(0.0, 0.010), (0.06, 0.012), (0.105, 0.0065), (0.125, 0.004), (0.14, 0.009), (0.152, 0.0115)]
    else:
        prof = [(0.0, 0.010), (0.09, 0.0105), (0.105, 0.007), (0.112, 0.008), (0.2, 0.009), (0.21, 0.0)]
    rows = []
    for x, w in prof:
        z = 0.004 * math.sin(min(x / 0.15, 1.0) * math.pi) if kind == 'fork' else 0.0
        th = 0.0016 if kind == 'knife' and x > 0.11 else 0.0028
        rows.append([bm.verts.new((x, -w, z - th / 2)), bm.verts.new((x, w, z - th / 2)),
                     bm.verts.new((x, w, z + th / 2)), bm.verts.new((x, -w, z + th / 2))])
    for a, b in zip(rows, rows[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])
    if kind == 'fork':
        for i in range(4):     # tines
            y = -0.0115 + 0.0023 + i * (0.023 - 0.0046) / 3
            sklib._bm_box(bm, Vector((0.152 + 0.019, y, 0.0)), (0.038, 0.0028, 0.0024))
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    ob = mesh(name, bm, C_TABLE, (sklib.stainless(0.05),))
    sklib.bevel(ob, 0.0007, 2, 30)
    return ob


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
    ob = mesh(name, bm, C_TABLE, (sklib.pbr('napkin_linen', 'rough_linen', scale=0.3, tint=(0.84, 0.81, 0.74), contrast=0.5, wear=0.04, ao_dist=0.05, rough=(0.75, 1.0)),), loc=loc, rot=(0, 0, rot), smooth=True)
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
    L.energy, L.color, L.shadow_soft_size = 1.2, sklib.kelvin_rgb(1900), 0.006
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
    parent_keep(cb, ob)
    cb.location = (0.045, 0.018, 0.0)
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
    vo.inputs['Scale'].default_value = 320.0
    _l(nt, tc.outputs['Object'], vo.inputs['Vector'])
    holes = _maprange(nt, vo.outputs['Distance'], 0.05, 0.22, 1.0, 0.0, -450, 0)
    rad = _n(nt, 'ShaderNodeVectorMath', -650, 300, operation='LENGTH')
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -850, 300)
    _l(nt, tc.outputs['Object'], sep.inputs[0])
    cmb = _n(nt, 'ShaderNodeCombineXYZ', -750, 300)
    _l(nt, sep.outputs['X'], cmb.inputs['X'])
    _l(nt, _math(nt, 'MULTIPLY', sep.outputs['Y'], 1.35, x=-850, y=420), cmb.inputs['Y'])
    _l(nt, cmb.outputs[0], rad.inputs[0])
    crust = _maprange(nt, rad.outputs['Value'], 0.046, 0.052, 0.0, 1.0, -450, 300)
    col = _mix(nt, holes, (0.86, 0.76, 0.58), (0.55, 0.43, 0.3), 'MIX', -200, 150)
    col = _mix(nt, crust, col, (0.35, 0.17, 0.06), 'MIX', 100, 200)
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
            v.co = Vector((v.co.x * 0.055, v.co.y * 0.041, max(-1, min(1, v.co.z * 3)) * 0.007))
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
    body_mi = [i for i, m in enumerate(me.materials) if m and m.name.startswith('Q11545')]
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
    m = tuna_mat()
    root = sklib.new_obj(name, None, C_FOOD, loc=origin, rot=(0, 0, yaw))
    for i in range(n):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=4, use_grid_fill=True)
        for v in bm.verts:
            x, y, z = v.co
            v.co = Vector((x * 0.009, y * 0.066 * (1 - 0.1 * (2 * z) ** 2) * (1 + 0.04 * math.sin(z * 7 + i)),
                           z * 0.026 * (1 - 0.12 * (2 * y) ** 4)))
        ob = mesh('%s.slice_%d' % (name, i), bm, C_FOOD, (m,), uv=False, smooth=True)
        sklib.bevel(ob, 0.0018, 3, 30)
        ob.parent = root     # fanned row: cut faces up, each slice resting on the previous one
        ob.location = (-i * 0.0165, 0.004 * math.sin(i * 0.9), 0.0105 + i * 0.0022)
        ob.rotation_euler = (0, -78 * D2R + rng.uniform(-0.03, 0.03), i * 0.035 + rng.uniform(-0.03, 0.03))
    return root


def leaves(name, center, radius, count, seed=3):
    r = random.Random(seed)
    mats = [leaf_mat('leaf_rocket', (0.05, 0.16, 0.025)), leaf_mat('leaf_dark', (0.025, 0.09, 0.02)),
            leaf_mat('leaf_frisee', (0.2, 0.36, 0.06))]
    bm = bmesh.new()
    for k in range(count):
        L, W = r.uniform(0.035, 0.06), r.uniform(0.005, 0.009)
        nu, nv = 10, 4
        a = r.uniform(0, 2 * math.pi)
        d = radius * math.sqrt(r.random())
        h = (1 - (d / radius) ** 2) * 0.028
        M = Matrix.Translation(center + Vector((d * math.cos(a), d * math.sin(a), h + 0.002))) @ \
            Euler((r.uniform(-0.6, 0.6), r.uniform(-0.6, 0.6), r.uniform(0, 6.28))).to_matrix().to_4x4()
        lob = r.uniform(0.35, 0.7)
        grid = []
        for i in range(nu + 1):
            u = i / nu
            w = W * math.sin(math.pi * min(u * 1.1, 1)) ** 0.7 * (1 + lob * math.sin(u * math.pi * 7))
            row = []
            for j in range(nv + 1):
                t = j / nv * 2 - 1
                z = 0.25 * W * t * t + 0.004 * math.sin(u * 9 + k) + 0.006 * u * u
                row.append(bm.verts.new(M @ Vector((u * L - L / 2, t * w, z))))
            grid.append(row)
        mi = k % 3
        for i in range(nu):
            for j in range(nv):
                f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
                f.material_index = mi
    ob = mesh(name, bm, C_FOOD, mats, uv=False, smooth=True)
    sol = ob.modifiers.new('sol', 'SOLIDIFY')
    sol.thickness = 0.0006
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
    leaves(prefix + '.greens', P(0.045, 0.0), 0.065, 95, seed=len(prefix))
    tuna_slices(prefix + '.tuna', P(-0.06, -0.05 * flip, -0.003), yaw - math.pi / 2 + 0.12, 6)
    skewer(prefix + '.skewer_a', P(0.025, 0.0, 0.019), yaw + math.pi / 2 + 0.06, 3, seed=1 + len(prefix))
    skewer(prefix + '.skewer_b', P(0.072, 0.008, 0.019), yaw + math.pi / 2 - 0.05, 3, seed=7 + len(prefix))
    lemon_wedge(prefix + '.lemon', P(-0.07, 0.075 * flip, 0.02), (-0.9, 0, yaw + 0.7))
    sauce_smear(prefix + '.smear', P(0, 0, 0.0002), 0.093, yaw + 3.5, yaw + 4.6)
    herb_flecks(prefix + '.herbs', P(0.0, 0.0), 40, 0.04, 0.004)
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
def build_lights():
    def area(name, loc, rot, size, k, energy, sy=None):
        L = bpy.data.lights.new(name, 'AREA')
        L.shape = 'RECTANGLE'
        L.size, L.size_y = size, sy or size
        L.color, L.energy = sklib.kelvin_rgb(k), energy
        return sklib.new_obj(name, L, C_LIGHT, loc=loc, rot=rot)
    out = {}
    out['window'] = area('L_window', (-1.15, 1.75, 1.35), (math.pi / 2, 0, math.pi), 3.2, 7200, 320, 2.4)
    out['ceil_table'] = area('L_ceil_table', (-0.6, -0.8, 2.66), (0, 0, 0), 1.6, 3200, 110, 1.2)
    out['ceil_kitchen'] = area('L_ceil_kitchen', (3.3, 0.6, 2.66), (0, 0, 0), 1.6, 3200, 110, 1.0)
    out['under_cab'] = area('L_undercab', (4.1, 1.68, 1.44), (0, 0, 0), 1.2, 2900, 30, 0.12)
    out['front_fill'] = area('L_front_fill', (0.6, -2.9, 1.6), (-math.pi / 2, 0, 0), 2.5, 3400, 70, 1.4)
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
    L.energy, L.color, L.spot_size, L.spot_blend, L.shadow_soft_size = 170, sklib.kelvin_rgb(2700), 110 * D2R, 0.5, 0.05
    out['pendant'] = sklib.new_obj('L_pendant', L, C_LIGHT, loc=(0, 0, 1.66))
    return out


def world():
    """Warm interior ambient mixed (keyed, f200->216) into the studio_small_09 HDRI @0.3 used by BRIDGE_FROST."""
    sklib.hdri('studio_small_09', '1k', 0.3)
    img = next(i for i in bpy.data.images if 'studio_small_09' in i.name)
    w, nt = sklib._world('SK_Table')
    env = _n(nt, 'ShaderNodeTexEnvironment', -400, -100)
    env.image = img
    bg1 = _n(nt, 'ShaderNodeBackground', -100, 150)
    bg1.inputs['Color'].default_value = (0.32, 0.26, 0.2, 1)
    bg1.inputs['Strength'].default_value = 0.25
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
def to_local(rig, p):
    return rig.matrix_world.inverted() @ Vector(p)


def dir_local(rig, d):
    return rig.matrix_world.to_3x3().inverted() @ Vector(d)


ARM_BONES = ('upperarm', 'lowerarm', 'hand')


def reset_arm(rig, s_):
    from mathutils import Quaternion
    for b in ARM_BONES:
        pb = rig.pose.bones['%s_%s' % (b, s_)]
        pb.rotation_quaternion = Quaternion(pb['sk_base']) if 'sk_base' in pb else (1, 0, 0, 0)


def reach(rig, s_, wrist_world, pole_world, hand_dir_world):
    reset_arm(rig, s_)
    bpy.context.view_layer.update()
    people._arm(rig, s_, ('reach', to_local(rig, wrist_world), dir_local(rig, pole_world).normalized(),
                          dir_local(rig, hand_dir_world).normalized()))


def key_arm(rig, s_, f):
    for b in ARM_BONES:
        rig.pose.bones['%s_%s' % (b, s_)].keyframe_insert('rotation_quaternion', frame=f)


def grip(rig, s_, curl=(30, 55, 62, 66), thumb=20):
    for f, c in zip(('index', 'middle', 'ring', 'pinky'), curl):
        for k in ('01', '02', '03'):
            people._set_rot(rig, '%s_%s_%s' % (f, k, s_), -(c + rng.uniform(-4, 4)), 0, 0, mirror=False)


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


def attach(ob, rig, bone):
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    pb = rig.pose.bones[bone]
    pm = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
    ob.matrix_parent_inverse = pm.inverted()
    ob.matrix_basis = mw


def place_tool(ob, rig, s_, tip_world):
    """Lay a cutlery piece (local +X = tip) from the palm heel to tip_world; then bone-parent it to the hand."""
    h, t = hand_frame(rig, s_)
    heel = h + (t - h) * 0.35 + Vector((0, 0, -0.022))
    d = (Vector(tip_world) - heel)
    q = d.to_track_quat('X', 'Z')
    L = 0.2 if 'knife' not in ob.name else 0.21
    ob.matrix_world = Matrix.Translation(Vector(tip_world) - d.normalized() * (L - 0.005)) @ q.to_matrix().to_4x4()
    attach(ob, rig, 'hand_' + s_)


def build_diners(plateA, plateB):
    out = {}
    specs = [('DinerA', 'male', 0.3, 0.32, 'diner_shirt', -1.02, math.pi / 2, 5, plateA),
             ('DinerB', 'female', 0.28, 0.68, 'diner_sweater', 1.02, -math.pi / 2, 9, plateB)]
    for name, sex, age, tone, outfit, x, rz, seed, pc in specs:
        rig = people.make_person(name, sex=sex, age=age, skin_tone=tone, outfit=outfit, pose='sit',
                                 location=(x, 0, 0), rotation_z=rz, seed=seed)
        for o in [rig] + list(rig.children):
            for c in o.users_collection:
                c.objects.unlink(o)
            C_PEOPLE.objects.link(o)
        sgn = 1 if x < 0 else -1                       # +1: diner faces +X
        # lean in to eat, head down toward the plate (keeps the face turned away from the 3/4 camera)
        people._set_rot(rig, 'spine_01', 10, 0, 0)
        people._set_rot(rig, 'spine_02', 8, 0, 0)
        people._set_rot(rig, 'spine_03', 6, 0, 0)
        people._set_rot(rig, 'neck_01', 10, 0, 0)
        people._set_rot(rig, 'head', 22, 0, 0)
        bpy.context.view_layer.update()
        for pb in rig.pose.bones:
            pb['sk_base'] = list(pb.rotation_quaternion)
        sz, hip = seat_height(rig)
        ch = chair(name + '.chair', hip.x - sgn * 0.02, rz, max(0.38, sz - 0.004))
        # cutlery: right hand knife, left hand fork (world sides: facing +X -> right = -Y)
        right_y = -sgn
        fork = cutlery(name + '.fork', 'fork')
        knife = cutlery(name + '.knife', 'knife')
        pcv = Vector(pc)
        out[name] = dict(rig=rig, sgn=sgn, fork=fork, knife=knife, pc=pcv, right_y=right_y)
        # hands near the plate (wrist targets); the pole pushes elbows out and back
        fw = lambda dx, dy, dz: pcv + Vector((sgn * dx, dy, dz))
        reach(rig, 'l', fw(-0.24, -right_y * 0.085, 0.085), (sgn * -0.3, -right_y * 1.0, -0.4), (sgn * 1, -right_y * 0.15, -0.55))
        reach(rig, 'r', fw(-0.24, right_y * 0.075, 0.085), (sgn * -0.3, right_y * 1.0, -0.4), (sgn * 1, right_y * 0.15, -0.55))
        bpy.context.view_layer.update()
        place_tool(fork, rig, 'l', fw(-0.05, -right_y * 0.002, 0.03))
        place_tool(knife, rig, 'r', fw(-0.055, right_y * 0.05, 0.026))
    # Diner A cuts the tuna: hands enter f1->20, two sawing strokes, fork lifts a little at the end
    A = out['DinerA']
    rig, sgn, pc, ry = A['rig'], A['sgn'], A['pc'], A['right_y']
    fw = lambda dx, dy, dz: pc + Vector((sgn * dx, dy, dz))
    for f, kx, fz in ((1, -0.34, 0.12), (22, -0.25, 0.09), (32, -0.225, 0.085), (42, -0.255, 0.09), (52, -0.225, 0.085),
                      (70, -0.24, 0.09), (100, -0.25, 0.11)):
        bpy.context.scene.frame_set(f)
        reach(rig, 'r', fw(kx, ry * 0.075, fz), (sgn * -0.3, ry * 1.0, -0.4),
              (sgn * 1, ry * 0.15, -0.55))
        reach(rig, 'l', fw(-0.24 if f > 1 else -0.33, -ry * 0.085, fz + 0.005), (sgn * -0.3, -ry * 1.0, -0.4),
              (sgn * 1, -ry * 0.15, -0.55))
        key_arm(rig, 'r', f)
        key_arm(rig, 'l', f)
    sklib.ease_keys(rig)
    bpy.context.scene.frame_set(1)
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
    keys.append((1, Vector((-0.40, 0.085, 1.42)), Euler((0, 0, -90 * D2R)), 50))
    keys.append((45, Vector((-0.40, 0.075, 1.50)), Euler((0, 0, -89 * D2R)), 48))
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
        t = (f - 190) / 26.0
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
    sklib.dof(cam, fe, 2.8)
    return cam


# --------------------------------------------------------------------------------------------------------- build
def main():
    build_room()
    build_table()
    lights = build_lights()
    world()
    pA = Vector((-0.40, 0.0, TOP))
    pB = Vector((0.40, 0.0, TOP))
    plA = dish('DishA', pA, 0.0, 1)
    plB = dish('DishB', pB, math.pi, 1)
    wine_glass('glassA_wine', (-0.16, -0.27, TOP), 0.45)
    tumbler('glassA_water', (-0.27, -0.33, TOP), 0.7)
    wine_glass('glassB_wine', (0.16, 0.27, TOP), 0.35)
    tumbler('glassB_water', (0.27, 0.33, TOP), 0.6)
    napkin('napkinA', (-0.42, 0.29, TOP), 0.08)
    napkin('napkinB', (0.42, -0.29, TOP), math.pi - 0.1)
    candle((0.02, -0.06, TOP))
    phone((0.3, -0.31, TOP), 0.35)
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
    cam = build_camera(bridge_loc, [(1, pA + Vector((0.0, 0, 0.02))), (45, pA + Vector((0.0, 0, 0.02))),
                                    (130, Vector((0.05, 0.0, TOP + 0.02))), (165, CARTON_LOC + Vector((0, 0, 0.2))),
                                    (190, CARTON_LOC + Vector((0, 0, 0.2))), (206, bridge_loc + Vector((0, 0, 0.01))),
                                    (216, bridge_loc)])
    s.eevee.use_shadows = True
    sklib.finish('table', 'int')


main()
