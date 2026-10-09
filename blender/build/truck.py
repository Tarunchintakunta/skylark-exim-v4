"""S6 truck.blend -> v-truck (1-216, 9 s, ext).
Anandapuram plant dock + Indian reefer truck -> Anandapuram-Pendurthi road -> coastal aerial (BRIDGE_COAST).
f1 = BRIDGE_DOCK (inside the dock, 1.5 m, 28 mm, exposure -0.3, sun elev 20 az 100), f216 = BRIDGE_COAST.
World: +Y north, +X east. Plant facade on y=0 facing south; truck backed against the dock seal, cab pointing south.
Road runs E-W at y=-60; pond belt north-east; coastline NE-SW ~2 km east; sea east.
Run: Blender -b --factory-startup --python truck.py
"""
import math
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

REPO = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4'
sys.path.insert(0, REPO + '/assets-src/blender/lib')
import sklib  # noqa: E402

sklib.reset()
import people  # noqa: E402  (enables MPFB after the factory reset)

D2R = math.pi / 180
S = bpy.context.scene
_n, _l, _mix, _math, _maprange, _noise = sklib._n, sklib._l, sklib._mix, sklib._math, sklib._maprange, sklib._noise


# ======================================================================================================== helpers
def C(name, parent=None):
    return sklib.collection(name, parent)


def bm_obj(name, bm, coll, mats, bev=None, uv=True, smooth_angle=35.0, loc=(0, 0, 0), parent=None):
    ob = sklib._mesh_obj(name, bm, coll)
    ob.location = loc
    if parent:
        ob.parent = parent
    sklib.mat_to(ob, *mats, uv=uv)
    if bev:
        sklib.bevel(ob, bev, 2, smooth_angle)
    return ob


def box(name, coll, mat, c, size, bev=0.01, parent=None, rot=None):
    bm = bmesh.new()
    sklib._bm_box(bm, Vector((0, 0, 0)), size)
    ob = bm_obj(name, bm, coll, [mat], bev if bev else None, parent=parent)
    ob.location = c
    if rot:
        ob.rotation_euler = rot
    return ob


def grid_bm(bm, x0, x1, y0, y1, nx=1, ny=1, z=0.0):
    rows = [[bm.verts.new((x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, z)) for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]))
    return rows


def bbox_bm(bm, x0, x1, y0, y1, z0, z1, mi=0):
    sklib._bm_box(bm, Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), (x1 - x0, y1 - y0, z1 - z0), mi)


def cyl_bm(bm, c, r, h, axis='Z', seg=16, mi=0, r2=None):
    sklib._bm_cyl(bm, Vector(c), r, h, axis, seg, mi, r2)


def grimed(base, name, z0=0.3, z1=1.9, color=(0.23, 0.18, 0.12), amount=0.85, streaks=0.5, world=True):
    """Copy of a material with road grime rising from the bottom (world/object z below z1 gets dirtier toward z0),
    broken by noise and vertical drip streaks. Lower = muddier."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = base.copy()
    m.name = name
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    inp = b.inputs['Base Color']
    src = inp.links[0].from_socket if inp.links else tuple(inp.default_value)
    if world:
        geo = _n(nt, 'ShaderNodeNewGeometry', -1500, -900)
        pos = geo.outputs['Position']
    else:
        tc = _n(nt, 'ShaderNodeTexCoord', -1500, -900)
        pos = tc.outputs['Object']
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -1300, -900)
    _l(nt, pos, sep.inputs[0])
    h = _maprange(nt, sep.outputs['Z'], z1, z0, 0.0, 1.0, -1100, -900)
    h = _math(nt, 'POWER', h, 1.6, True, -950, -900)
    nz = _noise(nt, pos, 2.2, 6.0, 0.62, -1100, -1100)
    nm = _maprange(nt, nz.outputs['Fac'], 0.35, 0.65, 0.45, 1.0, -950, -1100)
    mp = _n(nt, 'ShaderNodeMapping', -1250, -1300)
    mp.inputs['Scale'].default_value = (9.0, 9.0, 0.35)
    _l(nt, pos, mp.inputs['Vector'])
    st = _noise(nt, mp.outputs[0], 3.0, 4.0, 0.5, -1100, -1300)
    sm = _maprange(nt, st.outputs['Fac'], 0.5, 0.75, 0.0, streaks, -950, -1300)
    fac = _math(nt, 'MULTIPLY', h, nm, False, -800, -950)
    fac = _math(nt, 'MULTIPLY_ADD', sm, _math(nt, 'MINIMUM', 1.0, _math(nt, 'MULTIPLY', h, 2.5, x=-800, y=-1250), x=-700, y=-1250), True, -600, -1050, c=fac)
    fac = _math(nt, 'MULTIPLY', fac, amount, True, -450, -1000)
    col = _mix(nt, fac, src, color, 'MIX', -250, -800)
    _l(nt, col, inp)
    r = b.inputs['Roughness']
    if r.links:
        rr = _math(nt, 'MULTIPLY_ADD', fac, 0.35, True, -250, -1100, c=r.links[0].from_socket)
        _l(nt, rr, r)
    return m


def haze(m, color=(0.55, 0.63, 0.72), dist=4500.0, maxf=0.45):
    """Aerial perspective: blend the base colour toward a haze colour with camera distance (cheap, no volumes)."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    inp = b.inputs['Base Color']
    src = inp.links[0].from_socket if inp.links else tuple(inp.default_value)
    cd = _n(nt, 'ShaderNodeCameraData', -900, -1600)
    f = _math(nt, 'DIVIDE', cd.outputs['View Distance'], -dist, x=-700, y=-1600)
    f = _math(nt, 'EXPONENT', f, x=-550, y=-1600)
    f = _math(nt, 'SUBTRACT', 1.0, f, x=-400, y=-1600)
    f = _math(nt, 'MULTIPLY', f, maxf, True, -250, -1600)
    _l(nt, _mix(nt, f, src, color, 'MIX', -100, -1500), inp)
    return m


def uv_strip_obj(name, verts, faces, uvs, coll, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        for li in p.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    ob = sklib.new_obj(name, me, coll)
    me.materials.append(mat)
    return ob


# ======================================================================================================== materials
M = {}
M['white_box'] = grimed(sklib.painted_metal((0.84, 0.84, 0.82), wear=0.22, streaks=0.0, contrast=0.35), 'truck_box_white',
                        0.9, 2.3, amount=0.75)
M['cab'] = grimed(sklib.painted_metal((0.80, 0.80, 0.78), wear=0.2, streaks=0.0, contrast=0.35), 'truck_cab_white',
                  0.6, 1.8, amount=0.8)
M['cab_dark'] = grimed(sklib.painted_metal((0.06, 0.065, 0.07), wear=0.3, contrast=0.5), 'truck_cab_dark', 0.4, 1.3)
M['chassis'] = sklib.painted_metal((0.035, 0.035, 0.035), wear=0.55, streaks=0.9, contrast=0.6)
M['rust'] = sklib.rusty_metal(0.3)
M['alu'] = sklib.aluminium(0.2)
M['galv'] = sklib.galvanised(0.35)
M['stainless'] = sklib.stainless(0.1)
M['rubber'] = sklib.plastic((0.022, 0.022, 0.022), 0.45, name='rubber_dusty')
M['tyre'] = grimed(sklib.plastic((0.028, 0.027, 0.026), 0.6, name='tyre_rubber'), 'tyre_rubber_mud', 0.0, 0.7,
                   color=(0.25, 0.20, 0.15), amount=0.6, streaks=0.2)
M['plastic_grey'] = sklib.plastic((0.12, 0.125, 0.13), 0.3, name='plastic_grey')
M['reefer'] = grimed(sklib.plastic((0.70, 0.71, 0.70), 0.25, name='reefer_shroud'), 'reefer_shroud_g', 2.9, 3.4, amount=0.4)
M['yellow'] = grimed(sklib.painted_metal((0.70, 0.52, 0.04), wear=0.45, streaks=0.3), 'guard_yellow', 0.2, 0.8)
M['plate'] = sklib.painted_metal((0.85, 0.72, 0.12), wear=0.25, contrast=0.3)   # Indian commercial plate, blank
M['rim'] = sklib.painted_metal((0.55, 0.55, 0.53), wear=0.5, streaks=0.4)
M['ice'] = sklib._ice_chunk_mat()
M['concrete'] = sklib.concrete_quay(0.45)
M['concrete_fl'] = sklib.concrete_floor(0.3)
M['puf'] = grimed(sklib.painted_metal((0.80, 0.82, 0.82), wear=0.12, contrast=0.3), 'puf_panel', 0.0, 1.8,
                  color=(0.42, 0.38, 0.33), amount=0.5)
M['puf_blue'] = sklib.painted_metal((0.08, 0.22, 0.45), wear=0.15, contrast=0.4)
M['shutter'] = sklib.corrugated_steel((0.62, 0.64, 0.66), 0.35)
M['wall'] = grimed(sklib.pbr('yard_wall', 'painted_plaster_wall', tint=(0.86, 0.82, 0.72), wear=0.35, ao_dist=0.3),
                   'yard_wall_g', 0.0, 1.0, color=(0.36, 0.30, 0.24), amount=0.7)
M['int_wall'] = sklib.white_wall(0.2)
M['epoxy'] = sklib.epoxy_floor((0.35, 0.40, 0.38), 0.3)
M['wood'] = sklib.wood_planks(0.3)
M['bark'] = sklib.pbr('bark', 'bark_brown_02', wear=0.0, scale=0.6)
M['gravel'] = sklib.pbr('gravel', 'gravel_road', wear=0.0)
M['asphalt'] = sklib.asphalt(0.35)
M['mud'] = sklib.mud()
M['brick'] = sklib.pbr('brick', 'red_brick_03', wear=0.3)
M['tarp_blue'] = sklib.plastic((0.04, 0.16, 0.42), 0.3, name='tarp_blue')
M['tarp_black'] = sklib.linen_fabric((0.05, 0.05, 0.05), 0.2)
M['auto_yellow'] = grimed(sklib.painted_metal((0.75, 0.55, 0.03), wear=0.3, contrast=0.4), 'auto_yellow_g', 0.0, 0.5)
M['auto_green'] = grimed(sklib.painted_metal((0.06, 0.30, 0.10), wear=0.3, contrast=0.4), 'auto_green_g', 0.0, 0.5)
M['bus_white'] = grimed(sklib.painted_metal((0.78, 0.78, 0.74), wear=0.3, contrast=0.4), 'bus_white_g', 0.0, 1.0)
M['bus_green'] = sklib.painted_metal((0.10, 0.36, 0.14), wear=0.3, contrast=0.4)
M['bike_red'] = sklib.painted_metal((0.45, 0.03, 0.03), wear=0.25, contrast=0.4)
M['bike_blue'] = sklib.painted_metal((0.03, 0.10, 0.35), wear=0.25, contrast=0.4)
M['bike_black'] = sklib.painted_metal((0.02, 0.02, 0.02), wear=0.25, contrast=0.4)
M['sign_blue'] = sklib.painted_metal((0.05, 0.16, 0.40), wear=0.25, contrast=0.5)
M['sign_white'] = sklib.painted_metal((0.85, 0.85, 0.83), wear=0.2, contrast=0.3)
M['pole_conc'] = sklib.pbr('pole_concrete', 'concrete_floor_02', tint=(0.62, 0.61, 0.58), wear=0.4, contrast=0.6)


def glass_mat(name='glass_tinted', color=(0.05, 0.07, 0.07), rough=0.04):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 600, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 300, 0)
    b.inputs['Base Color'].default_value = color + (1,)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = 0.0
    tc = _n(nt, 'ShaderNodeTexCoord', -600, -200)
    nz = _noise(nt, tc.outputs['Object'], 5.0, 6.0, 0.6, -400, -200)
    _l(nt, _maprange(nt, nz.outputs['Fac'], 0.4, 0.75, rough, rough + 0.25, -200, -200), b.inputs['Roughness'])
    _l(nt, b.outputs[0], out.inputs['Surface'])
    return m


M['glass'] = glass_mat()
M['lamp'] = glass_mat('lamp_clear', (0.55, 0.56, 0.55), 0.08)
M['lamp_red'] = glass_mat('lamp_red', (0.45, 0.02, 0.01), 0.1)
M['lamp_amber'] = glass_mat('lamp_amber', (0.6, 0.25, 0.01), 0.1)
M['mirror'] = glass_mat('mirror_glass', (0.6, 0.62, 0.62), 0.02)
M['mirror'].node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 1.0


def reflect_tape():
    """Indian rear reflective tape: alternating red / white blocks (no text)."""
    m = bpy.data.materials.get('reflect_tape')
    if m:
        return m
    m, nt = sklib._new_mat('reflect_tape')
    out = _n(nt, 'ShaderNodeOutputMaterial', 600, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 300, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -700, 0)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -500, 0)
    _l(nt, tc.outputs['Object'], sep.inputs[0])
    s = _math(nt, 'ADD', sep.outputs['X'], sep.outputs['Z'], x=-350)
    s = _math(nt, 'MULTIPLY', _math(nt, 'ADD', s, sep.outputs['Y'], x=-300), 3.3, x=-250)
    w = _math(nt, 'FRACT', s, x=-150)
    w = _math(nt, 'GREATER_THAN', w, 0.5, x=-50)
    _l(nt, _mix(nt, w, (0.55, 0.02, 0.02), (0.85, 0.85, 0.82), 'MIX', 100, 100), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.25
    _l(nt, b.outputs[0], out.inputs['Surface'])
    return m


M['tape'] = reflect_tape()


def decal_mat(name, color, alpha=0.8, scale=1.5, lo=0.42, hi=0.62, stretch=(1, 1, 1), rough=0.35):
    """Transparent ground stain (oil / tyre rubber / damp) with a noisy edge."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 700, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 400, 0)
    b.inputs['Base Color'].default_value = color + (1,)
    b.inputs['Roughness'].default_value = rough
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    mp = _n(nt, 'ShaderNodeMapping', -700, 0)
    mp.inputs['Scale'].default_value = stretch
    _l(nt, tc.outputs['Object'], mp.inputs['Vector'])
    nz = _noise(nt, mp.outputs[0], scale, 8.0, 0.65, -500, 0)
    a = _maprange(nt, nz.outputs['Fac'], lo, hi, 0.0, alpha, -300, 0)
    # radial fade from the UV centre (planes are UV'd 0..1)
    gr = _n(nt, 'ShaderNodeTexGradient', -500, -250, gradient_type='SPHERICAL')
    mp2 = _n(nt, 'ShaderNodeMapping', -700, -250)
    mp2.inputs['Location'].default_value = (-1.0, -1.0, 0)
    mp2.inputs['Scale'].default_value = (2.0, 2.0, 1)
    _l(nt, tc.outputs['UV'], mp2.inputs['Vector'])
    _l(nt, mp2.outputs[0], gr.inputs['Vector'])
    a = _math(nt, 'MULTIPLY', a, _maprange(nt, gr.outputs['Fac'], 0.0, 0.5, 0.0, 1.0, -300, -250), x=-100)
    _l(nt, a, b.inputs['Alpha'])
    _l(nt, b.outputs[0], out.inputs['Surface'])
    return m


def leaf_mat(name, c1, c2, cut=True):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    geo = _n(nt, 'ShaderNodeNewGeometry', -900, -300)
    nz = _noise(nt, geo.outputs['Position'], 0.6, 4.0, 0.6, -650, 200)
    oi = _n(nt, 'ShaderNodeObjectInfo', -900, 400)
    f = _math(nt, 'ADD', nz.outputs['Fac'], _math(nt, 'MULTIPLY', oi.outputs['Random'], 0.35, x=-650, y=400), x=-450, y=300)
    col = _mix(nt, _maprange(nt, f, 0.5, 1.2, 0, 1, -300, 300), c1, c2, 'MIX', -100, 300)
    # darker toward the inside of the crown (AO)
    ao = _n(nt, 'ShaderNodeAmbientOcclusion', -400, 600, samples=8)
    ao.inputs['Distance'].default_value = 1.2
    col = _mix(nt, _maprange(nt, ao.outputs['AO'], 0.3, 1.0, 0.55, 0.0, -150, 600), col, (0.01, 0.025, 0.008), 'MIX', 100, 400)
    _l(nt, col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    b.inputs['Subsurface Weight'].default_value = 0.0
    if cut:   # leaf clusters on cards: voronoi blobs
        vo = _n(nt, 'ShaderNodeTexVoronoi', -650, -100, feature='F1')
        vo.inputs['Scale'].default_value = 7.0
        _l(nt, tc.outputs['UV'], vo.inputs['Vector'])
        a = _maprange(nt, vo.outputs['Distance'], 0.42, 0.36, 0.0, 1.0, -400, -100)
        gr = _n(nt, 'ShaderNodeTexGradient', -650, -400, gradient_type='SPHERICAL')
        mp2 = _n(nt, 'ShaderNodeMapping', -800, -400)
        mp2.inputs['Location'].default_value = (-1.0, -1.0, 0)
        mp2.inputs['Scale'].default_value = (2.0, 2.0, 1)
        _l(nt, tc.outputs['UV'], mp2.inputs['Vector'])
        _l(nt, mp2.outputs[0], gr.inputs['Vector'])
        a = _math(nt, 'MULTIPLY', a, _maprange(nt, gr.outputs['Fac'], 0.0, 0.25, 0, 1, -400, -400), x=-200, y=-200)
        _l(nt, a, b.inputs['Alpha'])
    bp = _n(nt, 'ShaderNodeBump', 300, -300)
    bp.inputs['Strength'].default_value = 0.5
    nz2 = _noise(nt, geo.outputs['Position'], 18.0, 4.0, 0.6, 0, -400)
    _l(nt, nz2.outputs['Fac'], bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    _l(nt, b.outputs[0], out.inputs['Surface'])
    return m


M['leaf_neem'] = leaf_mat('leaf_neem', (0.05, 0.13, 0.025), (0.12, 0.20, 0.04))
M['leaf_mango'] = leaf_mat('leaf_mango', (0.03, 0.09, 0.025), (0.07, 0.15, 0.04))
M['leaf_blob'] = leaf_mat('leaf_blob', (0.04, 0.11, 0.025), (0.10, 0.18, 0.04), cut=False)


def frond_mat():
    m = bpy.data.materials.get('palm_frond')
    if m:
        return m
    m, nt = sklib._new_mat('palm_frond')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -700, 0)
    _l(nt, tc.outputs['UV'], sep.inputs[0])
    # leaflets: thin stripes across the frond (u along rachis), slanted, gaps between them; rachis in the middle (v=0.5)
    vv = _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', sep.outputs['Y'], 0.5, x=-550, y=-100), x=-450, y=-100)
    s = _math(nt, 'MULTIPLY_ADD', vv, 0.9, x=-350, y=0, c=sep.outputs['X'])
    s = _math(nt, 'FRACT', _math(nt, 'MULTIPLY', s, 55.0, x=-250, y=0), x=-150, y=0)
    leaflet = _math(nt, 'LESS_THAN', _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', s, 0.5, x=-50), x=0), 0.28, x=80)
    rach = _math(nt, 'LESS_THAN', vv, 0.03, x=80, y=-150)
    # leaflet length tapers toward tip; ragged ends
    tip = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, sep.outputs['X'], x=-450, y=-300), 0.5, x=-350, y=-300)
    nz = _noise(nt, tc.outputs['UV'], 30.0, 2.0, 0.5, -450, -450)
    lim = _math(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 0.12, x=-250, y=-350, c=_math(nt, 'ADD', tip, 0.0, x=-300, y=-250))
    inside = _math(nt, 'LESS_THAN', vv, lim, x=-100, y=-300)
    a = _math(nt, 'MAXIMUM', _math(nt, 'MULTIPLY', leaflet, inside, x=200, y=-100), rach, x=320, y=-100)
    _l(nt, a, b.inputs['Alpha'])
    oi = _n(nt, 'ShaderNodeObjectInfo', -700, 400)
    col = _mix(nt, _maprange(nt, _math(nt, 'ADD', oi.outputs['Random'], sep.outputs['X'], x=-450, y=400), 0.2, 1.8, 0, 1, -300, 400),
               (0.06, 0.14, 0.03), (0.22, 0.26, 0.07), 'MIX', -100, 400)
    _l(nt, col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.5
    _l(nt, b.outputs[0], out.inputs['Surface'])
    return m


M['frond'] = frond_mat()


def land_mat():
    """Patchwork farmland seen from 10-300 m: voronoi fields (paddy greens, scrub, a few ploughed plots), darker field
    bunds, grass scan detail up close, aerial haze."""
    m = bpy.data.materials.get('land')
    if m:
        return m
    t = sklib.tex('sparse_grass')
    m, nt = sklib._new_mat('land')
    out = _n(nt, 'ShaderNodeOutputMaterial', 1400, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 1100, 0)
    geo = _n(nt, 'ShaderNodeNewGeometry', -1500, 0)
    pos = geo.outputs['Position']
    vo = _n(nt, 'ShaderNodeTexVoronoi', -1200, 300, feature='F1', distance='CHEBYCHEV')
    vo.inputs['Scale'].default_value = 1 / 32.0
    vo.inputs['Randomness'].default_value = 0.8
    _l(nt, pos, vo.inputs['Vector'])
    ramp = _n(nt, 'ShaderNodeValToRGB', -950, 300)
    cr = ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    pal = [(0.0, (0.07, 0.17, 0.025)), (0.16, (0.13, 0.22, 0.035)), (0.32, (0.05, 0.12, 0.025)), (0.48, (0.15, 0.21, 0.05)),
           (0.62, (0.10, 0.19, 0.03)), (0.74, (0.21, 0.16, 0.08)), (0.84, (0.09, 0.15, 0.04)), (0.93, (0.17, 0.14, 0.08))]
    cr.elements[0].position, cr.elements[0].color = pal[0][0], pal[0][1] + (1,)
    cr.elements[1].position, cr.elements[1].color = pal[1][0], pal[1][1] + (1,)
    for p, c in pal[2:]:
        e = cr.elements.new(p)
        e.color = c + (1,)
    sepc = _n(nt, 'ShaderNodeSeparateColor', -1100, 450)
    _l(nt, vo.outputs['Color'], sepc.inputs[0])
    _l(nt, sepc.outputs[0], ramp.inputs['Fac'])
    col = ramp.outputs['Color']
    # field edge bunds (distance to cell edge)
    ve = _n(nt, 'ShaderNodeTexVoronoi', -1200, 0, feature='F1', distance='CHEBYCHEV')
    ve.inputs['Scale'].default_value = 1 / 32.0
    ve.inputs['Randomness'].default_value = 0.8
    _l(nt, pos, ve.inputs['Vector'])
    v2 = _n(nt, 'ShaderNodeTexVoronoi', -1200, -150, feature='F2', distance='CHEBYCHEV')
    v2.inputs['Scale'].default_value = 1 / 32.0
    v2.inputs['Randomness'].default_value = 0.8
    _l(nt, pos, v2.inputs['Vector'])
    edge = _maprange(nt, _math(nt, 'SUBTRACT', v2.outputs['Distance'], ve.outputs['Distance'], x=-1050, y=-50), 0.05, 0.015, 0.0, 0.8, -950, 0)
    col = _mix(nt, edge, col, (0.18, 0.15, 0.08), 'MIX', -700, 200)
    # in-field variation
    nz = _noise(nt, pos, 0.12, 8.0, 0.7, -1200, -300)
    v = _maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 0.6, 1.35, -950, -300)
    vm = _n(nt, 'ShaderNodeVectorMath', -500, 100, operation='SCALE')
    _l(nt, col, vm.inputs[0])
    _l(nt, v, vm.inputs['Scale'])
    col = vm.outputs[0]
    # grass scan detail (multiplied, normalised)
    uvm = _n(nt, 'ShaderNodeMapping', -1200, -600)
    uvm.inputs['Scale'].default_value = (1 / t['size_m'],) * 3
    _l(nt, pos, uvm.inputs['Vector'])
    di = sklib._img(nt, t['diff'], True, uvm.outputs[0], -950, -600)
    g = 1.0 / sklib._avg_lum(di.image)
    bw = _n(nt, 'ShaderNodeRGBToBW', -700, -600)
    _l(nt, di.outputs['Color'], bw.inputs[0])
    cd = _n(nt, 'ShaderNodeCameraData', -950, -850)
    near = _maprange(nt, cd.outputs['View Distance'], 40.0, 150.0, 1.0, 0.0, -700, -850)
    det = _math(nt, 'MULTIPLY_ADD', _math(nt, 'SUBTRACT', _math(nt, 'MULTIPLY', bw.outputs[0], g, x=-550, y=-600), 1.0, x=-450, y=-600),
                near, x=-350, y=-700, c=1.0)
    vm2 = _n(nt, 'ShaderNodeVectorMath', -250, 50, operation='SCALE')
    _l(nt, col, vm2.inputs[0])
    _l(nt, det, vm2.inputs['Scale'])
    _l(nt, vm2.outputs[0], b.inputs['Base Color'])
    ni = sklib._img(nt, t['nor'], False, uvm.outputs[0], -950, -1000)
    nm = _n(nt, 'ShaderNodeNormalMap', -650, -1000)
    _l(nt, ni.outputs['Color'], nm.inputs['Color'])
    _l(nt, nm.outputs[0], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.9
    _l(nt, b.outputs[0], out.inputs['Surface'])
    haze(m)
    return m


M['land'] = land_mat()


def water_mat(name, deep, shallow, rough=0.06):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    geo = _n(nt, 'ShaderNodeNewGeometry', -900, 0)
    nz = _noise(nt, geo.outputs['Position'], 0.02, 4.0, 0.6, -650, 200)
    _l(nt, _mix(nt, _maprange(nt, nz.outputs['Fac'], 0.35, 0.65, 0, 1, -400, 200), deep, shallow, 'MIX', -150, 200),
       b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.12 if rough > 0.3 else 0.3
    w = _n(nt, 'ShaderNodeTexWave', -650, -200, wave_type='BANDS')
    w.inputs['Scale'].default_value = 0.08
    w.inputs['Distortion'].default_value = 6.0
    w.inputs['Detail'].default_value = 3.0
    _l(nt, geo.outputs['Position'], w.inputs['Vector'])
    nz2 = _noise(nt, geo.outputs['Position'], 0.6, 6.0, 0.6, -650, -450)
    bp = _n(nt, 'ShaderNodeBump', 300, -300)
    bp.inputs['Strength'].default_value = 0.12
    _l(nt, _math(nt, 'ADD', w.outputs['Fac'], nz2.outputs['Fac'], x=-300, y=-300), bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    _l(nt, b.outputs[0], out.inputs['Surface'])
    haze(m, maxf=0.55)
    return m


M['pond'] = water_mat('pond_water', (0.03, 0.07, 0.035), (0.06, 0.12, 0.045), 0.5)
M['pond2'] = water_mat('pond_water_b', (0.05, 0.08, 0.035), (0.09, 0.12, 0.045), 0.55)
M['sea'] = water_mat('sea_water', (0.008, 0.04, 0.07), (0.02, 0.09, 0.12), 0.18)
M['sand'] = haze(sklib.sand().copy())
M['sand'].name = 'sand_hazed'
M['bund'] = haze(sklib.pbr('bund_mud', 'brown_mud_03', tint=(0.36, 0.30, 0.20), contrast=0.6, wear=0.0, scale=3.0))


def hill_mat():
    m = bpy.data.materials.get('hill')
    if m:
        return m
    m, nt = sklib._new_mat('hill')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    geo = _n(nt, 'ShaderNodeNewGeometry', -900, 0)
    nz = _noise(nt, geo.outputs['Position'], 0.004, 8.0, 0.65, -650, 200)
    slope = _n(nt, 'ShaderNodeSeparateXYZ', -650, -100)
    _l(nt, geo.outputs['Normal'], slope.inputs[0])
    f = _math(nt, 'ADD', nz.outputs['Fac'], _maprange(nt, slope.outputs['Z'], 0.75, 0.95, 0.35, 0.0, -450, -100), x=-300)
    _l(nt, _mix(nt, _maprange(nt, f, 0.4, 0.9, 0, 1, -150, 100), (0.05, 0.11, 0.03), (0.22, 0.20, 0.11), 'MIX', 100, 100),
       b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.95
    _l(nt, b.outputs[0], out.inputs['Surface'])
    haze(m, dist=3500, maxf=0.75)
    return m


M['hill'] = hill_mat()


# ======================================================================================================== world / sun
world, SUN = sklib.sky_world(20.0, 100.0)
sky_node = next(n for n in world.node_tree.nodes if n.type == 'TEX_SKY')


def set_sun(elev, az, f):
    sky_node.sun_elevation, sky_node.sun_rotation = elev * D2R, az * D2R
    sky_node.keyframe_insert('sun_elevation', frame=f)
    sky_node.keyframe_insert('sun_rotation', frame=f)
    el, a = elev * D2R, az * D2R
    d = Vector((math.sin(a) * math.cos(el), math.cos(a) * math.cos(el), math.sin(el)))
    SUN.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    SUN.keyframe_insert('rotation_euler', frame=f)
    SUN.data.color = sklib.sun_color(elev)
    SUN.data.keyframe_insert('color', frame=f)


set_sun(20, 100, 1)
set_sun(20, 100, 120)
set_sun(15, 90, 216)
SUN.data.energy = 4.2


# ======================================================================================================== plant
PLANT = C('A-PLANT-EXT')
DOCK_Z = 1.25
DOORS = [-9.0, 0.0, 9.0]       # dock door centres (x); hero truck at 0
DW, DH = 3.0, 3.0              # door opening
BX0, BX1, BH, BD = -30.0, 30.0, 9.0, 34.0


def ribbed_wall(name, x0, x1, z0, z1, y, coll, mat, pitch=0.333, depth=0.018, face=-1):
    """PUF sandwich panel face: flat sheet with trapezoid ribs (pitch m), facing -Y (face=-1) or +Y."""
    pts = []
    n = max(1, int(round((x1 - x0) / pitch)))
    p = (x1 - x0) / n
    for i in range(n):
        u = x0 + i * p
        pts += [(u, 0.0), (u + p * 0.40, 0.0), (u + p * 0.46, depth), (u + p * 0.54, depth), (u + p * 0.60, 0.0)]
    pts.append((x1, 0.0))
    bm = bmesh.new()
    sklib._bm_strip(bm, pts, z0, z1, lambda u, d, v: Vector((u, y + face * d, v)), flip=(face > 0))
    ob = bm_obj(name, bm, coll, [mat])
    return ob


def build_plant():
    # facade: PUF panels above the dock plinth, gaps for the dock doors
    xs = [BX0]
    for d in DOORS:
        xs += [d - DW / 2, d + DW / 2]
    xs.append(BX1)
    for i in range(0, len(xs), 2):
        ribbed_wall('facade_%d' % i, xs[i], xs[i + 1], DOCK_Z, BH, 0.0, PLANT, M['puf'])
    for d in DOORS:
        ribbed_wall('facade_hdr_%g' % d, d - DW / 2, d + DW / 2, DOCK_Z + DH, BH, 0.0, PLANT, M['puf'])
    # blue accent band and clerestory window strip
    box('facade_band', PLANT, M['puf_blue'], (0, -0.03, BH - 0.45), (BX1 - BX0 + 0.1, 0.06, 0.5), 0.01)
    box('facade_win', PLANT, M['glass'], (0, -0.025, BH - 1.6), (BX1 - BX0 - 6, 0.04, 0.7), 0.005)
    for x in range(int(BX0) + 3, int(BX1) - 2, 3):
        box('facade_mull_%d' % x, PLANT, M['alu'], (x, -0.05, BH - 1.6), (0.06, 0.06, 0.74), 0.005)
    # side and back walls (simple panels), roof
    for sx in (BX0, BX1):
        w = ribbed_wall('side_%g' % sx, 0.0, BD, 0.0, BH, 0.0, PLANT, M['puf'], face=1 if sx < 0 else -1)
        w.rotation_euler.z = math.pi / 2
        w.location.x = sx
    ribbed_wall('back', BX0, BX1, 0.0, BH, BD, PLANT, M['puf'], face=1)
    roof = box('roof', PLANT, M['shutter'], (0, BD / 2, BH + 0.25), (BX1 - BX0 + 0.6, BD + 0.6, 0.5), 0.02)
    # concrete dock plinth (raised dock floor edge), scuffed
    box('plinth', PLANT, M['concrete'], (0, 0.5, DOCK_Z / 2), (BX1 - BX0, 1.0, DOCK_Z), 0.02)
    box('plinth_cap', PLANT, M['galv'], (0, -0.02, DOCK_Z - 0.04), (BX1 - BX0, 0.06, 0.08), 0.005)
    # canopy over the docks
    box('canopy', PLANT, M['shutter'], (0, -1.6, 5.6), (30.0, 3.4, 0.12), 0.01, rot=(-4 * D2R, 0, 0))
    box('canopy_fascia', PLANT, M['puf_blue'], (0, -3.3, 5.55), (30.0, 0.08, 0.35), 0.01)
    for x in (-14.5, -4.5, 4.5, 14.5):
        bmx = bmesh.new()
        bbox_bm(bmx, -0.06, 0.06, -3.25, 0.0, 5.35, 5.5)
        bbox_bm(bmx, -0.05, 0.05, -0.1, 0.0, 4.6, 5.45)
        bm_obj('canopy_brk_%g' % x, bmx, PLANT, [M['galv']], 0.005, loc=(x, 0, 0))
    for d in DOORS:
        hero = d == 0.0
        # door frame (galvanised channel)
        bmf = bmesh.new()
        for sx in (-1, 1):
            bbox_bm(bmf, sx * DW / 2 - 0.08, sx * DW / 2 + 0.08, -0.08, 0.25, DOCK_Z, DOCK_Z + DH + 0.08)
        bbox_bm(bmf, -DW / 2 - 0.08, DW / 2 + 0.08, -0.08, 0.25, DOCK_Z + DH, DOCK_Z + DH + 0.12)
        bm_obj('dock_frame_%g' % d, bmf, PLANT, [M['galv']], 0.01, loc=(d, 0, 0))
        # dock seal: side pads + head pad (black foam with fabric), slightly scuffed
        bms = bmesh.new()
        for sx in (-1, 1):
            bbox_bm(bms, sx * 1.34 if sx > 0 else -1.70, 1.70 if sx > 0 else -1.34, -0.30, 0.0, DOCK_Z + 0.05, DOCK_Z + DH)
        bbox_bm(bms, -1.70, 1.70, -0.30, 0.0, 3.99, DOCK_Z + DH + 0.35)
        bm_obj('dock_seal_%g' % d, bms, PLANT, [M['tarp_black']], 0.04, loc=(d, 0, 0))
        # yellow guide stripes on the seal pads
        for sx in (-1, 1):
            box('seal_stripe_%g_%d' % (d, sx), PLANT, M['yellow'], (d + sx * 1.52, -0.305, 2.8), (0.12, 0.012, 2.6), 0.003)
        # bumpers (scuffed rubber blocks)
        for sx in (-1, 1):
            box('dock_bumper_%g_%d' % (d, sx), PLANT, grimed(M['rubber'], 'bumper_scuffed', 0.8, 1.3,
                (0.35, 0.33, 0.30), 0.6, 0.0), (d + sx * 1.05, -0.07, 1.0), (0.25, 0.14, 0.45), 0.02)
        # leveller plate + lip; interior bay floor
        if hero:
            box('leveller', PLANT, M['galv'], (d, 1.3, 1.33), (2.2, 2.6, 0.04), 0.006, rot=(-2.6 * D2R, 0, 0))
            box('leveller_lip', PLANT, M['galv'], (d, -0.45, 1.41), (2.0, 0.95, 0.03), 0.004)
            for sx in (-1, 1):
                box('leveller_stripe_%d' % sx, PLANT, M['yellow'], (d + sx * 1.05, 1.35, DOCK_Z + 0.005), (0.08, 2.6, 0.01), 0.002)
        else:
            # closed roll-up shutter
            sh = ribbed_wall('shutter_%g' % d, d - DW / 2, d + DW / 2, DOCK_Z, DOCK_Z + DH, 0.08, PLANT, M['shutter'],
                             pitch=0.08, depth=0.02)
    # dock bay interior (seen from f1): floor, walls, ceiling, a lamp
    box('bay_floor', PLANT, M['epoxy'], (0, 7.5, DOCK_Z - 0.1), (12.0, 15.0, 0.2), 0.0)
    box('bay_inner_l', PLANT, M['int_wall'], (-DW / 2 - 2.0, 0.2, 4.6), (4.0, 0.1, 6.8), 0.0)
    box('bay_inner_r', PLANT, M['int_wall'], (DW / 2 + 2.0, 0.2, 4.6), (4.0, 0.1, 6.8), 0.0)
    box('bay_inner_t', PLANT, M['int_wall'], (0, 0.2, (DOCK_Z + DH + 8.0) / 2 + 0.05), (DW, 0.1, 8.0 - DOCK_Z - DH), 0.0)
    for sx in (-1, 1):
        box('bay_side_%d' % sx, PLANT, M['int_wall'], (sx * 6.0, 7.5, 4.6), (0.1, 15.0, 6.8), 0.0)
    box('bay_ceiling', PLANT, M['int_wall'], (0, 7.5, 8.0), (12.0, 15.0, 0.1), 0.0)
    pal = sklib.carton_pallet()
    for i, (x, y) in enumerate([(-4.2, 2.5), (-4.2, 3.8), (4.2, 2.8), (4.2, 5.5), (-2.5, 8.0)]):
        sklib.instance(pal, (x, y, DOCK_Z), random.Random(i).uniform(-0.05, 0.05), 'bay_pallet_%d' % i, PLANT)
    la = bpy.data.lights.new('bay_light', 'AREA')
    la.energy, la.size, la.color = 400.0, 3.0, sklib.kelvin_rgb(5000)
    sklib.new_obj('bay_light', la, PLANT, loc=(0, 5.0, 7.8))


build_plant()


# ======================================================================================================== yard
YARD = C('A-YARD')


def ground_plane(name, x0, x1, y0, y1, z, coll, mat, cuts=1):
    bm = bmesh.new()
    grid_bm(bm, x0, x1, y0, y1, cuts, cuts, z)
    return bm_obj(name, bm, coll, [mat])


def decal(name, coll, mat, loc, size, rot=0.0):
    bm = bmesh.new()
    grid_bm(bm, -size[0] / 2, size[0] / 2, -size[1] / 2, size[1] / 2)
    ob = sklib._mesh_obj(name, bm, coll)
    ob.location, ob.rotation_euler.z = loc, rot
    uvl = ob.data.uv_layers.new(name='UVMap')
    for p in ob.data.polygons:
        for li in p.loop_indices:
            co = ob.data.vertices[ob.data.loops[li].vertex_index].co
            uvl.data[li].uv = (co.x / size[0] + 0.5, co.y / size[1] + 0.5)
    ob.data.materials.append(mat)
    return ob


def tyre_track(name, pts, coll, mat, width=0.30, gap=1.8):
    """Pair of rubber tracks along a polyline (world XY), as a UV'd ribbon at z=0.004."""
    verts, faces, uvs = [], [], []
    L = 0.0
    for side in (-1, 1):
        base = len(verts)
        acc = 0.0
        for i, p in enumerate(pts):
            p = Vector(p)
            q = Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])
            t = q.normalized()
            nrm = Vector((-t.y, t.x))
            if i:
                acc += (Vector(pts[i]) - Vector(pts[i - 1])).length
            for e in (-1, 1):
                c = p + nrm * (side * gap / 2 + e * width / 2)
                verts.append((c.x, c.y, 0.004))
                uvs.append((acc / 6.0, 0.5 + e * 0.5))
            if i:
                k = base + 2 * i
                faces.append((k - 2, k, k + 1, k - 1))
        L = acc
    return uv_strip_obj(name, verts, faces, uvs, coll, mat)


def track_mat():
    m = bpy.data.materials.get('tyre_track')
    if m:
        return m
    m, nt = sklib._new_mat('tyre_track')
    out = _n(nt, 'ShaderNodeOutputMaterial', 700, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 400, 0)
    b.inputs['Base Color'].default_value = (0.03, 0.028, 0.025, 1)
    b.inputs['Roughness'].default_value = 0.7
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -700, 0)
    _l(nt, tc.outputs['UV'], sep.inputs[0])
    tread = _math(nt, 'GREATER_THAN', _math(nt, 'FRACT', _math(nt, 'MULTIPLY', sep.outputs['X'], 60.0, x=-550), x=-450), 0.45, x=-350)
    nz = _noise(nt, tc.outputs['Object'], 0.8, 6.0, 0.6, -550, -250)
    a = _maprange(nt, nz.outputs['Fac'], 0.38, 0.62, 0.0, 0.75, -350, -250)
    edge = _maprange(nt, _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', sep.outputs['Y'], 0.5, x=-550, y=-450), x=-450, y=-450),
                     0.5, 0.3, 0.0, 1.0, -350, -450)
    a = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', a, edge, x=-150, y=-300), _math(nt, 'MULTIPLY_ADD', tread, 0.4, x=-150, y=-100, c=0.6), x=0, y=-200)
    _l(nt, a, b.inputs['Alpha'])
    _l(nt, b.outputs[0], out.inputs['Surface'])
    return m


def build_yard():
    ground_plane('yard_concrete', -34, 34, -46, 0.2, 0.0, YARD, M['concrete'], cuts=1)
    # yard boundary wall (plastered brick, pillars, coping) with a gate opening on the south side (x 12..20)
    def wall_run(name, p0, p1):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        ang = math.atan2(d.y, d.x)
        bm = bmesh.new()
        bbox_bm(bm, 0, L, -0.115, 0.115, 0, 2.2)
        bbox_bm(bm, -0.02, L + 0.02, -0.15, 0.15, 2.2, 2.3)
        n = int(L / 3.0)
        for i in range(n + 1):
            u = i * L / max(n, 1)
            bbox_bm(bm, u - 0.17, u + 0.17, -0.17, 0.17, 0.0, 2.45)
        ob = bm_obj(name, bm, YARD, [M['wall']], 0.012)
        ob.location = (p0.x, p0.y, 0)
        ob.rotation_euler.z = ang
        sklib.box_uv(ob)
    wall_run('ywall_s1', (-34, -46), (12, -46))
    wall_run('ywall_s2', (20, -46), (34, -46))
    wall_run('ywall_w', (-34, -46), (-34, 0))
    wall_run('ywall_e', (34, -46), (34, 0))
    # gate posts + open sliding gate leaf parked behind the wall
    for x in (12, 20):
        box('gate_post_%d' % x, YARD, M['wall'], (x, -46, 1.4), (0.5, 0.5, 2.8), 0.02)
    bmg = bmesh.new()
    bbox_bm(bmg, 0, 8.0, -0.03, 0.03, 0.15, 0.22)
    bbox_bm(bmg, 0, 8.0, -0.03, 0.03, 1.9, 1.97)
    for i in range(41):
        cyl_bm(bmg, (i * 0.2, 0, 1.06), 0.012, 1.8, seg=6)
    bm_obj('gate_leaf', bmg, YARD, [sklib.painted_metal((0.10, 0.22, 0.12), 0.45, 0.4)], None, loc=(3.0, -45.6, 0.0))
    # security cabin by the gate
    cab = C('A-SECURITY-CABIN', YARD)
    cx, cy = 24.0, -42.5
    bmc = bmesh.new()
    bbox_bm(bmc, -1.4, 1.4, -1.4, 1.4, 0.0, 2.7)
    bm_obj('cabin_body', bmc, cab, [M['wall']], 0.02, loc=(cx, cy, 0))
    box('cabin_roof', cab, M['concrete'], (cx, cy, 2.8), (3.3, 3.3, 0.18), 0.02)
    box('cabin_win_s', cab, M['glass'], (cx - 0.2, cy - 1.41, 1.6), (1.4, 0.03, 0.9), 0.005)
    box('cabin_win_w', cab, M['glass'], (cx - 1.41, cy, 1.6), (0.03, 1.4, 0.9), 0.005)
    box('cabin_door', cab, sklib.painted_metal((0.12, 0.2, 0.32), 0.35, 0.2), (cx + 1.41, cy - 0.3, 1.0), (0.04, 0.85, 2.0), 0.005)
    box('cabin_step', cab, M['concrete'], (cx + 1.7, cy - 0.3, 0.08), (0.6, 1.2, 0.16), 0.02)
    # boom barrier
    box('boom_post', YARD, M['yellow'], (21.0, -45.2, 0.55), (0.3, 0.3, 1.1), 0.02)
    box('boom_arm', YARD, M['tape'], (21.0, -45.2, 3.5), (0.08, 0.08, 4.8), 0.01)
    # blank signboard (no text) outside the gate
    for x in (22.5, 25.5):
        cyl_bmo = bmesh.new()
        cyl_bm(cyl_bmo, (0, 0, 1.6), 0.05, 3.2, seg=10)
        bm_obj('sign_post_%g' % x, cyl_bmo, YARD, [M['galv']], None, loc=(x, -47.6, 0))
    box('sign_face', YARD, M['sign_blue'], (24.0, -47.66, 2.7), (3.4, 0.05, 1.5), 0.01)
    box('sign_border', YARD, M['sign_white'], (24.0, -47.63, 2.7), (3.6, 0.03, 1.7), 0.01)
    # drains: channel drain across the yard + square covers
    box('drain_channel', YARD, sklib.pbr('grate_dark', 'metal_grate_rusty', tint=(0.12, 0.12, 0.12), contrast=0.5, wear=0.3, scale=0.3), (0, -16.0, 0.004), (60.0, 0.25, 0.012), 0.002)
    for i, (x, y) in enumerate([(-6.5, -6.0), (6.5, -6.5), (-14.0, -30.0), (10.0, -36.0)]):
        box('drain_cover_%d' % i, YARD, sklib.pbr('grate', 'metal_grate_rusty', wear=0.2, scale=0.3), (x, y, 0.005), (0.6, 0.6, 0.014), 0.002)
        decal('drain_damp_%d' % i, YARD, decal_mat('damp_stain', (0.13, 0.12, 0.1), 0.6, 2.0), (x, y, 0.003), (1.6, 1.4))
    # oil stains + tyre tracks
    oil = decal_mat('oil_stain', (0.015, 0.014, 0.012), 0.85, 1.8, rough=0.15)
    rng = random.Random(4)
    for i, (x, y) in enumerate([(0.3, -6.5), (-0.4, -9.8), (-9.2, -5.0), (-8.8, -9.3), (9.1, -6.0), (4.0, -20.0),
                                (-13.0, -24.0), (14.0, -28.0), (2.0, -32.0)]):
        decal('oil_%d' % i, YARD, oil, (x, y, 0.002 + i * 1e-4), (rng.uniform(0.8, 2.2), rng.uniform(0.6, 1.6)), rng.uniform(0, 3))
    tm = track_mat()
    # reverse-in arcs from the gate to the docks
    for i, (dx, sx) in enumerate([(0.0, 1), (-9.0, 1), (9.0, 1), (0.6, 1)]):
        pts = []
        for k in range(25):
            t = k / 24.0
            y = -2.0 - t * 42.0
            x = dx + (16.0 - dx) * (t ** 2.2)
            pts.append((x + 0.3 * math.sin(t * 7 + i), y))
        tyre_track('track_%d' % i, pts, YARD, tm, 0.32, 1.95)
    # stacked empty crates, drums near the east wall
    cr = C('A-CRATE-STACK', False)
    for k in range(5):
        c = sklib.crate((0.05, 0.22, 0.55) if k % 2 else (0.55, 0.38, 0.05), 'stack_crate_%d' % k, cr, 0.45)
        c.location = (0, 0, k * 0.245)
    for i, (x, y, r) in enumerate([(28.5, -3.0, 0.1), (29.2, -3.0, 0.0), (28.5, -3.6, 0.05), (29.3, -3.65, -0.1), (28.9, -4.4, 0.3)]):
        sklib.instance(cr, (x, y, 0), r, 'crate_stack_%d' % i, YARD)
    drum = C('A-DRUM', False)
    bmd = bmesh.new()
    cyl_bm(bmd, (0, 0, 0.44), 0.29, 0.88, seg=24)
    for z in (0.3, 0.6):
        cyl_bm(bmd, (0, 0, z), 0.295, 0.03, seg=24)
    d_ = bm_obj('drum_mesh', bmd, drum, [sklib.painted_metal((0.08, 0.2, 0.42), 0.5, 0.5)], 0.01)
    for i, (x, y) in enumerate([(31.0, -6.0), (31.65, -6.1), (31.3, -6.65)]):
        sklib.instance(drum, (x, y, 0), i * 0.7, 'drum_%d' % i, YARD)
    # yellow bollards between the docks, painted lane/parking lines
    bmb = bmesh.new()
    for x in (-13.5, -4.5, 4.5, 13.5, -20.0, 20.0):
        cyl_bm(bmb, (x, -0.9, 0.55), 0.11, 1.1, seg=16)
    bm_obj('dock_bollards', bmb, YARD, [M['yellow']], 0.01)
    paint = sklib.flat('yard_paint', (0.62, 0.48, 0.06), rough=0.7, var=0.3, scale=2.0)
    bml = bmesh.new()
    for x in (-4.5, 4.5, -13.5, 13.5):
        bbox_bm(bml, x - 0.06, x + 0.06, -14.0, -1.2, 0.0, 0.006)
    bbox_bm(bml, -28.0, 28.0, -14.06, -13.94, 0.0, 0.006)
    for k in range(6):
        x = -27.0 + k * 3.2
        bbox_bm(bml, x - 0.06, x + 0.06, -44.5, -38.0, 0.0, 0.006)
    bm_obj('yard_lines', bml, YARD, [paint])
    return


build_yard()


# ======================================================================================================== truck
TRUCK = C('A-TRUCK-REEFER', False)        # shared body (instanced twice); roof + doors per instance
BOX_Y0, BOX_Y1 = -7.30, 0.0
BOX_Z0, BOX_Z1 = 1.20, 3.95
BW = 1.25
IN_Z0, IN_Z1 = 1.35, 3.65
FRONT_AX, REAR_AX = -8.65, -3.0
WR = 0.515


def wheel_coll():
    c = bpy.data.collections.get('A-WHEEL')
    if c:
        return c
    c = C('A-WHEEL', False)
    # tyre: revolve a rounded section around X
    prof = []
    W, R, r_in = 0.28, WR, 0.29
    for i in range(13):
        a = -math.pi / 2 + math.pi * i / 12
        prof.append((W / 2 * 0.86 * math.sin(a) * 1.0 + 0.0, R - 0.05 + 0.05 * math.cos(a), a))
    sec = [(x, rr) for x, rr, a in prof]
    sec = [(-W / 2, r_in)] + [(x if abs(x) < W / 2 else math.copysign(W / 2, x), rr) for x, rr in sec] + [(W / 2, r_in)]
    sec = sorted(set(sec), key=lambda p: (p[0] if p[1] > R - 0.06 else p[0]))
    sec = [(-W / 2, r_in), (-W / 2, R - 0.08), (-W / 2 + 0.03, R - 0.015), (-W / 2 + 0.07, R), (W / 2 - 0.07, R),
           (W / 2 - 0.03, R - 0.015), (W / 2, R - 0.08), (W / 2, r_in)]
    bm = bmesh.new()
    seg = 40
    rings = []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        rings.append([bm.verts.new((x, rr * math.cos(a), rr * math.sin(a))) for x, rr in sec])
    for k in range(seg):
        A, B = rings[k], rings[(k + 1) % seg]
        for j in range(len(sec) - 1):
            bm.faces.new((A[j], A[j + 1], B[j + 1], B[j]))
    # tread grooves: offset alternate ring vertices inward on the crown
    for k in range(seg):
        if k % 2:
            for j in (3, 4):
                v = rings[k][j]
                v.co.y *= 0.985
                v.co.z *= 0.985
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ty = bm_obj('tyre', bm, c, [M['tyre']])
    ty.data.shade_smooth()
    # steel rim disc + hub + nuts
    bmr = bmesh.new()
    cyl_bm(bmr, (0, 0, 0), r_in + 0.005, 0.22, 'X', 32)
    cyl_bm(bmr, (0.115, 0, 0), 0.20, 0.03, 'X', 24)
    cyl_bm(bmr, (0.14, 0, 0), 0.10, 0.06, 'X', 16)
    for k in range(8):
        a = 2 * math.pi * k / 8
        cyl_bm(bmr, (0.17, 0.15 * math.cos(a), 0.15 * math.sin(a)), 0.018, 0.04, 'X', 6)
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        bbox_bm(bmr, 0.11, 0.135, 0.22 * math.cos(a) - 0.035, 0.22 * math.cos(a) + 0.035, 0.22 * math.sin(a) - 0.035, 0.22 * math.sin(a) + 0.035)
    bm_obj('rim', bmr, c, [M['rim']], 0.004)
    return c


def truck_body():
    W = wheel_coll()
    rng = random.Random(7)
    T = TRUCK
    # ---- insulated box (walls, floor, front wall, rear portal); roof is separate
    bm = bmesh.new()
    for sx in (-1, 1):
        bbox_bm(bm, sx * BW - (0.08 if sx > 0 else 0), sx * BW + (0.08 if sx < 0 else 0), BOX_Y0, -0.12, BOX_Z0, BOX_Z1 - 0.06)
    bbox_bm(bm, -BW, BW, BOX_Y0, -0.12, BOX_Z0, IN_Z0)                     # floor slab
    bbox_bm(bm, -BW, BW, BOX_Y0, BOX_Y0 + 0.1, BOX_Z0, BOX_Z1)              # front wall
    sh = bm_obj('box_shell', bm, T, [M['white_box']], 0.03)
    # rear portal frame (stainless) with corner posts, header and sill
    bmp = bmesh.new()
    for sx in (-1, 1):
        bbox_bm(bmp, sx * BW - 0.12 if sx > 0 else -BW, BW if sx > 0 else -BW + 0.12, -0.14, 0.0, BOX_Z0, BOX_Z1)
    bbox_bm(bmp, -BW, BW, -0.14, 0.0, IN_Z1, BOX_Z1)
    bbox_bm(bmp, -BW, BW, -0.14, 0.0, BOX_Z0, IN_Z0)
    bm_obj('box_portal', bmp, T, [M['stainless']], 0.012)
    box('box_tape', T, M['tape'], (0, 0.004, IN_Z1 + 0.15), (2.3, 0.01, 0.06), 0.0)
    for sx in (-1, 1):
        box('box_tape_v%d' % sx, T, M['tape'], (sx * (BW - 0.06), 0.004, 2.5), (0.05, 0.01, 1.8), 0.0)
    # aluminium cap rails along edges + rub rail
    bmc = bmesh.new()
    for sx in (-1, 1):
        bbox_bm(bmc, sx * BW - 0.03, sx * BW + 0.03, BOX_Y0, 0.0, BOX_Z1 - 0.08, BOX_Z1 + 0.01)
        bbox_bm(bmc, sx * BW - 0.035, sx * BW + 0.035, BOX_Y0, 0.0, BOX_Z0 - 0.02, BOX_Z0 + 0.12)
        bbox_bm(bmc, sx * BW - 0.03, sx * BW + 0.03, BOX_Y0 - 0.03, BOX_Y0 + 0.06, BOX_Z0, BOX_Z1)
    bbox_bm(bmc, -BW, BW, BOX_Y0 - 0.03, BOX_Y0 + 0.03, BOX_Z1 - 0.08, BOX_Z1 + 0.01)
    bm_obj('box_caprails', bmc, T, [M['alu']], 0.01)
    # interior lining: aluminium ribbed walls, T-section floor ridges
    bmi = bmesh.new()
    for sx in (-1, 1):
        bbox_bm(bmi, sx * (BW - 0.081) - 0.004, sx * (BW - 0.081) + 0.004, BOX_Y0 + 0.1, -0.14, IN_Z0, IN_Z1)
        for k in range(14):
            y = BOX_Y0 + 0.4 + k * 0.5
            bbox_bm(bmi, sx * (BW - 0.081) - 0.02, sx * (BW - 0.081) + 0.02, y - 0.02, y + 0.02, IN_Z0, IN_Z1)
    bbox_bm(bmi, -BW + 0.08, BW - 0.08, BOX_Y0 + 0.1, BOX_Y0 + 0.108, IN_Z0, IN_Z1)
    for k in range(22):
        x = -1.05 + k * 0.1
        bbox_bm(bmi, x - 0.015, x + 0.015, BOX_Y0 + 0.1, -0.14, IN_Z0, IN_Z0 + 0.03)
    bm_obj('box_lining', bmi, T, [M['alu']], 0.003)
    # ---- reefer unit on the front wall, above the cab
    bmr = bmesh.new()
    bbox_bm(bmr, -0.95, 0.95, BOX_Y0 - 0.46, BOX_Y0, 3.12, 3.92)
    ru = bm_obj('reefer_unit', bmr, T, [M['reefer']], 0.07)
    bmg = bmesh.new()
    for sx in (-0.45, 0.45):
        cyl_bm(bmg, (sx, BOX_Y0 - 0.465, 3.55), 0.27, 0.02, 'Y', 32, mi=0)
        for rr in (0.08, 0.15, 0.22):
            cyl_bm(bmg, (sx, BOX_Y0 - 0.48, 3.55), rr, 0.012, 'Y', 32, mi=1, r2=rr)
        bbox_bm(bmg, sx - 0.25, sx + 0.25, BOX_Y0 - 0.485, BOX_Y0 - 0.47, 3.545, 3.555, mi=1)
        bbox_bm(bmg, sx - 0.005, sx + 0.005, BOX_Y0 - 0.485, BOX_Y0 - 0.47, 3.30, 3.80, mi=1)
    for k in range(6):
        z = 3.18 + k * 0.022
        bbox_bm(bmg, -0.8, 0.8, BOX_Y0 - 0.47, BOX_Y0 - 0.455, z, z + 0.01, mi=1)
    bm_obj('reefer_grille', bmg, T, [M['plastic_grey'], M['galv']], None)
    # ---- chassis (rusty black C-rails + cross members), rear underride bar, lights
    bmch = bmesh.new()
    for sx in (-1, 1):
        bbox_bm(bmch, sx * 0.43 - 0.045, sx * 0.43 + 0.045, -9.35, -0.55, 0.80, 1.08)
        bbox_bm(bmch, sx * 0.43 - 0.06, sx * 0.43 + 0.06, BOX_Y0 + 0.2, -0.55, 1.08, 1.20)    # subframe
    for y in (-0.8, -2.2, -3.8, -5.4, -7.0, -8.2, -9.2):
        bbox_bm(bmch, -0.43, 0.43, y - 0.05, y + 0.05, 0.85, 1.03)
    for k in range(10):     # box cross-bearers
        y = BOX_Y0 + 0.3 + k * 0.75
        bbox_bm(bmch, -BW + 0.05, BW - 0.05, y - 0.04, y + 0.04, 1.12, 1.20)
    bm_obj('chassis', bmch, T, [M['chassis']], 0.008)
    bmu = bmesh.new()
    bbox_bm(bmu, -1.12, 1.12, -0.22, -0.10, 0.48, 0.63)
    for sx in (-0.55, 0.55):
        bbox_bm(bmu, sx - 0.04, sx + 0.04, -0.6, -0.12, 0.6, 1.0)
    bm_obj('rear_underride', bmu, T, [M['chassis']], 0.008)
    box('rear_underride_tape', T, M['tape'], (0, -0.095, 0.555), (2.2, 0.01, 0.1), 0.0)
    for sx in (-1, 1):
        box('rear_lamp_r%d' % sx, T, M['lamp_red'], (sx * 0.95, -0.09, 0.72), (0.22, 0.05, 0.1), 0.01)
        box('rear_lamp_a%d' % sx, T, M['lamp_amber'], (sx * 0.72, -0.09, 0.72), (0.12, 0.05, 0.1), 0.01)
        box('rear_lamp_bkt%d' % sx, T, M['chassis'], (sx * 0.85, -0.16, 0.72), (0.5, 0.1, 0.14), 0.01)
    # ---- wheels: front singles, rear duals
    for sx in (-1, 1):
        e = sklib.instance(W, (sx * 1.03, FRONT_AX, WR - 0.006), 0.0 if sx > 0 else math.pi, 'wheel_f%d' % sx, T)
        for k, off in enumerate((0.84, 1.13)):
            e = sklib.instance(W, (sx * off, REAR_AX, WR - 0.006), 0.0 if sx > 0 else math.pi, 'wheel_r%d%d' % (sx, k), T)
    # axles/hubs
    bma = bmesh.new()
    cyl_bm(bma, (0, REAR_AX, WR), 0.07, 1.8, 'X', 16)
    cyl_bm(bma, (0, REAR_AX, WR), 0.22, 0.35, 'X', 16)
    cyl_bm(bma, (0, FRONT_AX, WR), 0.06, 1.85, 'X', 12)
    for sx in (-1, 1):   # leaf springs
        bbox_bm(bma, sx * 0.43 - 0.04, sx * 0.43 + 0.04, REAR_AX - 0.65, REAR_AX + 0.65, WR + 0.08, WR + 0.2)
        bbox_bm(bma, sx * 0.43 - 0.04, sx * 0.43 + 0.04, FRONT_AX - 0.6, FRONT_AX + 0.6, WR + 0.06, WR + 0.16)
    bm_obj('axles', bma, T, [M['rust']], 0.01)
    # rear mudguards (black arches) and mud flaps
    for sx in (-1, 1):
        bmm = bmesh.new()
        n = 10
        prof = []
        for k in range(n + 1):
            a = math.pi * k / n
            prof.append((REAR_AX + 0.66 * math.cos(a), WR + 0.66 * math.sin(a) * 0.62))
        for k in range(n):
            (y0, z0), (y1, z1) = prof[k], prof[k + 1]
        verts = []
        for k in range(n + 1):
            y, z = prof[k]
            verts.append((bmm.verts.new((sx * 0.68, y, max(z, WR + 0.25))), bmm.verts.new((sx * 1.30, y, max(z, WR + 0.25)))))
        for k in range(n):
            bmm.faces.new((verts[k][0], verts[k + 1][0], verts[k + 1][1], verts[k][1]))
        o = bm_obj('mudguard_%d' % sx, bmm, T, [M['rubber']])
        o.modifiers.new('sol', 'SOLIDIFY').thickness = 0.008
        box('mudflap_r%d' % sx, T, grimed(M['rubber'], 'mudflap_mud', 0.1, 0.8, (0.26, 0.21, 0.15), 0.8), (sx * 0.99, REAR_AX + 0.68, 0.53),
            (0.62, 0.012, 0.66), 0.005)
        box('mudflap_f%d' % sx, T, grimed(M['rubber'], 'mudflap_mud', 0.1, 0.8, (0.26, 0.21, 0.15), 0.8), (sx * 1.03, FRONT_AX + 0.60, 0.62),
            (0.36, 0.012, 0.5), 0.005)
    # side underrun guards (two yellow rails + brackets) between the axles
    for sx in (-1, 1):
        bmg2 = bmesh.new()
        for z in (0.48, 0.80):
            bbox_bm(bmg2, sx * 1.17 - 0.025, sx * 1.17 + 0.025, -7.45, REAR_AX - 0.72, z - 0.05, z + 0.05)
        for y in (-7.4, -5.4, REAR_AX - 0.9):
            bbox_bm(bmg2, min(sx * 0.48, sx * 1.15), max(sx * 0.48, sx * 1.15), y - 0.03, y + 0.03, 0.82, 0.88)
            bbox_bm(bmg2, sx * 1.15 - 0.025, sx * 1.15 + 0.025, y - 0.03, y + 0.03, 0.43, 0.88)
        bm_obj('side_guard_%d' % sx, bmg2, T, [M['yellow']], 0.008)
    # fuel tank (left), battery box (right), air tanks
    bmf = bmesh.new()
    bbox_bm(bmf, -1.08, -0.52, -7.0, -5.9, 0.62, 1.12)
    bm_obj('fuel_tank', bmf, T, [M['alu']], 0.05)
    box('fuel_cap', T, M['galv'], (-0.8, -6.2, 1.15), (0.12, 0.12, 0.05), 0.01)
    box('battery_box', T, M['chassis'], (0.8, -6.3, 0.85), (0.55, 0.7, 0.42), 0.02)
    bmt = bmesh.new()
    cyl_bm(bmt, (-0.75, -4.6, 0.9), 0.14, 0.9, 'Y', 16)
    bm_obj('air_tank', bmt, T, [M['chassis']], 0.01)
    # ---- cab (Tata Signa-like cab-over): rounded shell, raked windscreen, tumblehome
    CY0, CY1, CZ0, CZ1 = -9.58, -7.47, 1.12, 3.06
    bmc = bmesh.new()
    rr = bmesh.ops.create_cube(bmc, size=1.0)
    for v in bmc.verts:
        x, y, z = v.co
        X = x * 2 * BW * 0.995
        Y = (CY0 + CY1) / 2 + y * (CY1 - CY0)
        Z = (CZ0 + CZ1) / 2 + z * (CZ1 - CZ0)
        if z > 0:
            X *= 0.94
            if y < 0:
                Y += 0.30      # raked front, top set back
        v.co = (X, Y, Z)
    bmesh.ops.subdivide_edges(bmc, edges=bmc.edges[:], cuts=2, use_grid_fill=True)
    cabo = bm_obj('cab_shell', bmc, T, [M['cab']])
    bv = cabo.modifiers.new('Bevel', 'BEVEL')
    bv.width, bv.segments, bv.limit_method, bv.angle_limit = 0.16, 5, 'ANGLE', 30 * D2R
    bv.use_clamp_overlap = True
    cabo.data.shade_smooth()
    cabo.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL').keep_sharp = True
    sklib.apply_mods(cabo)
    sklib.box_uv(cabo)
    rake = math.atan2(0.30, CZ1 - CZ0)

    def front_y(z):   # y of the raked front face at height z
        t = (z - CZ0) / (CZ1 - CZ0)
        return CY0 + 0.30 * t

    # windscreen (glass, proud of the face) with black gasket, split by a thin centre pillar
    for name, z0, z1, w, mat, prot in (('cab_ws_gasket', 2.02, 2.88, 2.22, M['rubber'], 0.008), ('cab_windscreen', 2.05, 2.85, 2.16, M['glass'], 0.016)):
        zc = (z0 + z1) / 2
        o = box(name, T, mat, (0, front_y(zc) - prot, zc), (w, 0.02, z1 - z0), 0.01, rot=(-rake, 0, 0))
    # lower fascia, grille with slats, headlamps, indicators
    zc = 1.62
    box('cab_fascia', T, M['cab_dark'], (0, front_y(zc) - 0.012, zc), (2.12, 0.03, 0.75), 0.015, rot=(-rake, 0, 0))
    bmg = bmesh.new()
    for k in range(6):
        z = 1.40 + k * 0.085
        bbox_bm(bmg, -0.80, 0.80, -0.03, 0.03, z, z + 0.035)
    for sx in (-0.81, 0.81):
        bbox_bm(bmg, sx - 0.02, sx + 0.02, -0.03, 0.03, 1.37, 1.88)
    go = bm_obj('cab_grille', bmg, T, [sklib.painted_metal((0.16, 0.16, 0.17), 0.25, contrast=0.4)], 0.006)
    go.location = (0, front_y(1.62) - 0.045, 0)
    go.rotation_euler.x = rake * 0.0
    for sx in (-1, 1):
        box('cab_headlamp_%d' % sx, T, M['lamp'], (sx * 0.9, front_y(1.55) - 0.04, 1.55), (0.30, 0.05, 0.2), 0.02, rot=(-rake, 0, 0))
        box('cab_headlamp_bezel_%d' % sx, T, M['stainless'], (sx * 0.9, front_y(1.55) - 0.03, 1.55), (0.34, 0.04, 0.24), 0.015, rot=(-rake, 0, 0))
        box('cab_indicator_%d' % sx, T, M['lamp_amber'], (sx * 0.9, front_y(1.78) - 0.035, 1.78), (0.30, 0.04, 0.07), 0.015, rot=(-rake, 0, 0))
    # bumper with fog lamps + blank plate
    bmb = bmesh.new()
    bbox_bm(bmb, -1.22, 1.22, CY0 - 0.20, CY0 + 0.05, 0.72, 1.12)
    bm_obj('cab_bumper', bmb, T, [grimed(sklib.painted_metal((0.22, 0.23, 0.24), 0.35, 0.3), 'bumper_grey', 0.3, 1.1)], 0.04)
    for sx in (-1, 1):
        cy = bmesh.new()
        cyl_bm(cy, (sx * 0.9, CY0 - 0.205, 0.9), 0.07, 0.03, 'Y', 20)
        bm_obj('cab_foglamp_%d' % sx, cy, T, [M['lamp']], 0.005)
    box('cab_plate', T, M['plate'], (0, CY0 - 0.215, 0.92), (0.52, 0.012, 0.13), 0.004)
    box('cab_tow', T, M['chassis'], (0, CY0 - 0.21, 0.76), (0.18, 0.04, 0.08), 0.01)
    # sun visor over the windscreen
    box('cab_visor', T, M['cab_dark'], (0, front_y(3.0) - 0.16, 2.97), (2.26, 0.34, 0.03), 0.01, rot=(-8 * D2R, 0, 0))
    # wipers
    for sx in (-0.55, 0.35):
        o = box('cab_wiper_%g' % sx, T, M['rubber'], (sx, front_y(2.18) - 0.035, 2.2), (0.85, 0.015, 0.02), 0.003)
        o.rotation_euler = (-rake, 0.18, 0)
    # side windows, door handles, steps
    for sx in (-1, 1):
        box('cab_sidewin_%d' % sx, T, M['glass'], (sx * (BW * (0.995 - 0.055 * (2.40 - CZ0) / (CZ1 - CZ0)) + 0.006), -8.55, 2.40), (0.02, 1.15, 0.62), 0.01)
        box('cab_doorline_%d' % sx, T, M['rubber'], (sx * (BW * 0.995 + 0.002), -7.95, 1.9), (0.006, 0.012, 1.4), 0.0)
        box('cab_handle_%d' % sx, T, M['cab_dark'], (sx * (BW * 0.995 + 0.012), -8.1, 1.95), (0.02, 0.2, 0.05), 0.008)
        for k, z in enumerate((0.48, 0.86)):
            box('cab_step_%d_%d' % (sx, k), T, M['alu'], (sx * 1.12, -7.75, z), (0.24, 0.36, 0.04), 0.008)
        box('cab_step_brk_%d' % sx, T, M['chassis'], (sx * 1.0, -7.75, 0.75), (0.04, 0.3, 0.6), 0.008)
        # mirrors on arms
        bmm = bmesh.new()
        cyl_bm(bmm, (0, 0, 0), 0.016, 0.42, 'X', 8)
        mo = bm_obj('cab_mirror_arm_%d' % sx, bmm, T, [M['cab_dark']], None)
        mo.location = (sx * 1.40, -9.25, 2.82)
        bmm2 = bmesh.new()
        cyl_bm(bmm2, (0, 0, 0), 0.016, 0.36, 'Z', 8)
        mo2 = bm_obj('cab_mirror_stay_%d' % sx, bmm2, T, [M['cab_dark']], None)
        mo2.location = (sx * 1.60, -9.25, 2.66)
        box('cab_mirror_head_%d' % sx, T, M['cab_dark'], (sx * 1.62, -9.22, 2.32), (0.07, 0.24, 0.42), 0.025)
        box('cab_mirror_glass_%d' % sx, T, M['mirror'], (sx * 1.62, -9.105, 2.32), (0.05, 0.005, 0.38), 0.0)
        box('cab_mirror_kerb_%d' % sx, T, M['cab_dark'], (sx * 1.58, -9.22, 2.02), (0.06, 0.18, 0.18), 0.02)
        # front wheel arches
        bma2 = bmesh.new()
        n = 10
        vv = []
        for k in range(n + 1):
            a = math.pi * k / n
            y, z = FRONT_AX + 0.62 * math.cos(a), WR + 0.62 * math.sin(a) * 0.95
            vv.append((bma2.verts.new((sx * 0.86, y, z)), bma2.verts.new((sx * 1.22, y, z))))
        for k in range(n):
            bma2.faces.new((vv[k][0], vv[k + 1][0], vv[k + 1][1], vv[k][1]))
        o = bm_obj('cab_arch_%d' % sx, bma2, T, [M['rubber']])
        o.modifiers.new('sol', 'SOLIDIFY').thickness = 0.01
    # cab rear wall shadow gap filler (between cab and box) + exhaust stack
    box('cab_backwall', T, M['chassis'], (0, CY1 + 0.02, 2.0), (2.2, 0.04, 1.6), 0.01)
    bme = bmesh.new()
    cyl_bm(bme, (0.95, -7.42, 2.2), 0.05, 1.7, 'Z', 12)
    bm_obj('exhaust', bme, T, [M['rust']], None)
    return TRUCK


truck_body()


def box_roof(name, coll, parent):
    bm = bmesh.new()
    bbox_bm(bm, -BW, BW, BOX_Y0, -0.14, BOX_Z1 - 0.07, BOX_Z1)
    ob = bm_obj(name, bm, coll, [M['white_box']], 0.02)
    ob.parent = parent
    return ob


def rear_doors(prefix, coll, parent, open_=True):
    """Two insulated rear doors (locking bars, hinges, rubber seals), hinged 0.13 m outboard of the rear corners.
    open_: folded 270 deg flat against the box sides (as when docked against a seal)."""
    OFF = 0.13
    L = BW + OFF
    obs = []
    for sx in (-1, 1):
        g = -sx                                   # leaf extends from its hinge toward the centre
        X = lambda u: g * u
        lo = lambda a, b: (min(X(a), X(b)), max(X(a), X(b)))
        bm = bmesh.new()
        bbox_bm(bm, *lo(0.0, L), 0.0, 0.06, BOX_Z0 + 0.12, BOX_Z1 - 0.06)
        leaf = bm_obj('%s_door_%d' % (prefix, sx), bm, coll, [M['white_box']], 0.02)
        bmh = bmesh.new()
        for z in (BOX_Z0 + 0.12, BOX_Z1 - 0.085):
            bbox_bm(bmh, *lo(0.02, L - 0.02), -0.012, 0.0, z, z + 0.025)
        bbox_bm(bmh, *lo(L - 0.025, L), -0.012, 0.0, BOX_Z0 + 0.12, BOX_Z1 - 0.06)
        seals = bm_obj('%s_seal_%d' % (prefix, sx), bmh, coll, [M['rubber']], None)
        bml = bmesh.new()
        for u in (0.45, 1.05):
            cyl_bm(bml, (X(u), 0.09, (BOX_Z0 + BOX_Z1) / 2 + 0.03), 0.016, BOX_Z1 - BOX_Z0 - 0.1, 'Z', 10)
            for z in (BOX_Z0 + 0.4, BOX_Z1 - 0.35):
                bbox_bm(bml, *lo(u - 0.04, u + 0.04), 0.06, 0.1, z - 0.04, z + 0.04)
            bbox_bm(bml, *lo(u, u + 0.3), 0.09, 0.12, 2.0, 2.05)
        for z in (BOX_Z0 + 0.35, 2.15, 2.95, BOX_Z1 - 0.3):
            bbox_bm(bml, *lo(0.0, 0.18), 0.06, 0.09, z - 0.05, z + 0.05)
        bars = bm_obj('%s_bars_%d' % (prefix, sx), bml, coll, [M['stainless']], 0.004)
        hinge = sklib.new_obj('%s_hinge_%d' % (prefix, sx), None, coll, parent)
        hinge.location = (sx * L, 0.0, 0.0)
        for o in (leaf, seals, bars):
            o.parent = hinge
        hinge.rotation_euler.z = (-sx * 270 * D2R) if open_ else 0.0
        obs.append(hinge)
    return obs


HERO = sklib.new_obj('TRUCK_HERO', None, None, loc=(0, -0.31, 0))
sklib.instance(TRUCK, (0, 0, 0), 0.0, 'A-TRUCK-REEFER.hero', None).parent = HERO
HERO_ROOF = box_roof('truck_hero_roof', S.collection, HERO)
rear_doors('hero', S.collection, HERO, True)
VAR = sklib.new_obj('TRUCK_PARKED', None, None, loc=(-17.0, -21.0, 0), rot=(0, 0, 28 * D2R))
sklib.instance(TRUCK, (0, 0, 0), 0.0, 'A-TRUCK-REEFER.parked', None).parent = VAR
box_roof('truck_parked_roof', S.collection, VAR)
rear_doors('parked', S.collection, VAR, False)

# cut-away roof: hidden while the camera flies through the body, back once the camera is out over the cab
for f, h in ((1, True), (64, True), (65, False)):
    HERO_ROOF.hide_render = HERO_ROOF.hide_viewport = h
    HERO_ROOF.keyframe_insert('hide_render', frame=f)
    HERO_ROOF.keyframe_insert('hide_viewport', frame=f)

# wheel chock at the right rear wheel (cab side of the tyre)
bmk = bmesh.new()
vs = [bmk.verts.new(p) for p in [(-0.12, 0.0, 0.0), (0.12, 0.0, 0.0), (0.12, -0.24, 0.0), (-0.12, -0.24, 0.0),
                                  (-0.12, -0.24, 0.2), (0.12, -0.24, 0.2)]]
for f in ((0, 1, 2, 3), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2), (0, 4, 5, 1)):
    bmk.faces.new([vs[i] for i in f])
bmesh.ops.recalc_face_normals(bmk, faces=bmk.faces[:])
chock = bm_obj('wheel_chock', bmk, YARD, [grimed(sklib.plastic((0.75, 0.55, 0.03), 0.5, name='chock_yellow'), 'chock_g', 0.0, 0.25)], 0.01)
chock.location = (1.13, -0.31 + REAR_AX - 0.205, 0.0)


# ======================================================================================================== cargo
def cargo():
    """Crates of shrimp on crushed ice stacked inside the hero box (instanced variants)."""
    CG = C('CARGO')
    base = C('A-CRATE-STACK3', False)
    for k in range(2):
        c = sklib.crate((0.05, 0.22, 0.55), 'cargo_crate_low_%d' % k, base, 0.35)
        c.location = (0, 0, k * 0.245)
    top_vars = []
    prawn = None
    try:
        bpy.ops.import_scene.gltf(filepath=REPO + '/assets-src/models/table-prawn-gtp.glb')
        prawn = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
        me = prawn.data
        bb = [Vector(c) for c in prawn.bound_box]
        ctr = sum(bb, Vector()) / 8
        me.transform(Matrix.Translation(-ctr))
        s = 0.15 / prawn.dimensions.x
        me.transform(Matrix.Rotation(math.pi / 2, 4, 'X') @ Matrix.Diagonal((s, s, s, 1)))
        for c in prawn.users_collection:
            c.objects.unlink(prawn)
        prawn.location = (0, 0, 0)
        prawn.rotation_euler = (0, 0, 0)
        prawn.scale = (1, 1, 1)
    except Exception as e:  # keep building without shrimp if the scan is missing
        print('prawn import failed', e)
    for v in range(3):
        cv = C('A-CRATE-ICE-%d' % v, False)
        cr = sklib.crate((0.05, 0.22, 0.55), 'cargo_crate_top_%d' % v, cv, 0.35)
        cr.location = (0, 0, 0.49)
        ice = sklib.crushed_ice_fill(cr, density=1.0, name='cargo_ice_%d' % v, coll=cv, seed=11 + v, depth=0.06)
        if prawn:
            rng = random.Random(30 + v)
            for i in range(7):
                p = bpy.data.objects.new('cargo_prawn_%d_%d' % (v, i), prawn.data)
                cv.objects.link(p)
                p.location = (rng.uniform(-0.2, 0.2), rng.uniform(-0.12, 0.12), 0.49 + 0.225 + rng.uniform(-0.01, 0.012))
                p.rotation_euler = (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), rng.uniform(0, 6.28))
        top_vars.append(cv)
    rng = random.Random(5)
    y0 = -0.31 - 0.75
    k = 0
    for row in range(16):
        y = y0 - row * 0.405
        if y < -0.31 + BOX_Y0 + 0.35:
            break
        for col in range(3):
            x = -0.68 + col * 0.68 + rng.uniform(-0.02, 0.02)
            rz = math.pi / 2 * 0 + rng.uniform(-0.02, 0.02)
            loc = (x, y, IN_Z0 + 0.03)
            sklib.instance(base, loc, rz, 'cargo_low_%d' % k, CG)
            sklib.instance(top_vars[rng.randrange(3)], loc, rz + (math.pi if rng.random() < 0.5 else 0), 'cargo_top_%d' % k, CG)
            k += 1


cargo()


# ======================================================================================================== vegetation
VEG = C('A-VEG', False)


def tree_neem(name, seed, cards=True, height=7.0):
    """Neem/mango-like broadleaf: tapered trunk + limbs, lumpy crown clumps (+ leaf-cluster cards on the surface)."""
    c = C(name, False)
    rng = random.Random(seed)
    bm = bmesh.new()
    th = height * 0.45
    cyl_bm(bm, (0, 0, th / 2), 0.22 * height / 7, th, seg=10, r2=0.14 * height / 7)
    tips = []
    for k in range(4):
        a = k * 1.57 + rng.uniform(-0.4, 0.4)
        L = height * 0.32
        d = Vector((math.cos(a) * 0.6, math.sin(a) * 0.6, 0.8)).normalized()
        base = Vector((0, 0, th * 0.9))
        q = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.10 * height / 7, radius2=0.04, depth=L,
                              matrix=Matrix.Translation(base + d * L / 2) @ q)
        tips.append(base + d * L)
    tr = bm_obj(name + '.trunk', bm, c, [M['bark']], None)
    bmc = bmesh.new()
    centers = []
    for k in range(9):
        t = tips[k % 4]
        cc = t + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.8))) * height * 0.12
        r = height * rng.uniform(0.17, 0.25)
        bmesh.ops.create_icosphere(bmc, subdivisions=2, radius=r, matrix=Matrix.Translation(cc) @ Matrix.Diagonal((1, 1, 0.75, 1)))
        centers.append((cc, r))
    nz = random.Random(seed + 1)
    for v in bmc.verts:
        v.co += v.co.normalized() * 0.0 + Vector((nz.uniform(-1, 1), nz.uniform(-1, 1), nz.uniform(-1, 1))) * height * 0.025
    crown = bm_obj(name + '.crown', bmc, c, [M['leaf_blob']], None, uv=False)
    crown.data.shade_smooth()
    if cards:
        verts, faces, uvs = [], [], []
        dg = None
        for k in range(260):
            cc, r = centers[rng.randrange(len(centers))]
            d = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) * 0.75 + 0.15)).normalized()
            p = cc + Vector((d.x, d.y, d.z * 0.75)) * r * rng.uniform(0.85, 1.12)
            s = height * rng.uniform(0.07, 0.11)
            q = (d + Vector((rng.uniform(-.5, .5), rng.uniform(-.5, .5), rng.uniform(-.5, .5)))).normalized().to_track_quat('Z', 'Y').to_matrix()
            b0 = len(verts)
            for (u, w) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                verts.append(tuple(p + q @ Vector((u * s, w * s, 0))))
                uvs.append(((u + 1) / 2, (w + 1) / 2))
            faces.append((b0, b0 + 1, b0 + 2, b0 + 3))
        uv_strip_obj(name + '.cards', verts, faces, uvs, c, M['leaf_neem'])
    return c


def tree_palm(name, seed, height=11.0):
    c = C(name, False)
    rng = random.Random(seed)
    lean = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized() * rng.uniform(0.6, 1.6)
    bm = bmesh.new()
    n, seg = 14, 10
    rings = []
    for i in range(n + 1):
        t = i / n
        ctr = Vector((0, 0, t * height)) + lean * (t ** 1.8)
        r = 0.24 - 0.09 * t + (0.04 if i % 2 else 0)
        rings.append([bm.verts.new(ctr + Vector((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), 0))) for k in range(seg)])
    for i in range(n):
        for k in range(seg):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]))
    top = Vector((0, 0, height)) + lean
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.42, matrix=Matrix.Translation(top))
    tr = bm_obj(name + '.trunk', bm, c, [M['bark']], None)
    tr.data.shade_smooth()
    verts, faces, uvs = [], [], []
    nf = 18
    for f in range(nf):
        a = 2 * math.pi * f / nf + rng.uniform(-0.15, 0.15)
        up = rng.uniform(0.15, 0.75)
        L = rng.uniform(3.6, 4.6)
        dirv = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-math.sin(a), math.cos(a), 0))
        m = 10
        b0 = len(verts)
        for i in range(m + 1):
            t = i / m
            pos = top + dirv * L * t + Vector((0, 0, L * (up * t - 0.9 * t * t)))
            w = 0.95 * math.sin(math.pi * min(1.0, t * 1.15 + 0.05)) * (1 - 0.3 * t) + 0.05
            droop = Vector((0, 0, -0.25 * w))
            for e in (-1, 1):
                verts.append(tuple(pos + side * w * e + droop))
                uvs.append((t, 0.5 + 0.5 * e))
            if i:
                k = b0 + 2 * i
                faces.append((k - 2, k, k + 1, k - 1))
    uv_strip_obj(name + '.fronds', verts, faces, uvs, c, M['frond'])
    return c


def tree_low(name, seed, height=7.0):
    """Far-field tree: trunk + 3 lumpy clumps (for the aerial)."""
    c = C(name, False)
    rng = random.Random(seed)
    bm = bmesh.new()
    cyl_bm(bm, (0, 0, height * 0.25), 0.18, height * 0.5, seg=6, r2=0.1)
    bm_obj(name + '.trunk', bm, c, [M['bark']], None)
    bmc = bmesh.new()
    for k in range(3):
        cc = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.3))) * height * 0.15 + Vector((0, 0, height * 0.68))
        bmesh.ops.create_icosphere(bmc, subdivisions=1, radius=height * rng.uniform(0.22, 0.3),
                                   matrix=Matrix.Translation(cc) @ Matrix.Diagonal((1, 1, 0.8, 1)))
    cr = bm_obj(name + '.crown', bmc, c, [M['leaf_blob']], None, uv=False)
    return c


TREES_HI = [tree_neem('A-VEG-TREE-neem%d' % i, 10 + i, height=h) for i, h in enumerate((6.5, 8.5, 7.5))]
PALMS = [tree_palm('A-VEG-PALM-%d' % i, 40 + i, height=h) for i, h in enumerate((10.0, 12.5, 8.5))]
TREES_LO = [tree_low('A-VEG-TREE-low%d' % i, 70 + i, height=h) for i, h in enumerate((6.0, 8.0, 9.5))]


# ======================================================================================================== landscape
ENV = C('A-ENV')
COAST = C('BRIDGE_COAST')
ROAD_Y = -60.0


def coast_x(y):
    return 1450.0 + 0.45 * y


def build_land():
    # big land plane (outside the yard), slightly below yard level
    ground_plane('land', -4000, 4500, -4000, 6000, -0.03, COAST, M['land'], cuts=1)
    # sea east of the NE-SW coastline + beach band
    verts = [(coast_x(-4000), -4000, 0.25), (9000, -4000, 0.25), (9000, 6000, 0.25), (coast_x(6000), 6000, 0.25)]
    me = bpy.data.meshes.new('sea')
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    sea = sklib.new_obj('A-ENV-SEA', me, COAST)
    me.materials.append(M['sea'])
    bv = [(coast_x(-4000) - 70, -4000, 0.02), (coast_x(-4000) + 15, -4000, 0.3), (coast_x(6000) + 15, 6000, 0.3), (coast_x(6000) - 70, 6000, 0.02)]
    me2 = bpy.data.meshes.new('beach')
    me2.from_pydata(bv, [], [(0, 1, 2, 3)])
    beach = sklib.new_obj('A-ENV-BEACH', me2, COAST)
    sklib.mat_to(beach, M['sand'])
    # surf line (thin white foam strip just off the beach)
    fv = [(coast_x(-4000) + 4, -4000, 0.27), (coast_x(-4000) + 14, -4000, 0.27), (coast_x(6000) + 14, 6000, 0.27), (coast_x(6000) + 4, 6000, 0.27)]
    me3 = bpy.data.meshes.new('surf')
    me3.from_pydata(fv, [], [(0, 1, 2, 3)])
    surf = sklib.new_obj('A-ENV-SURF', me3, COAST)
    me3.materials.append(haze(sklib.flat('surf_foam', (0.85, 0.88, 0.88), rough=0.6, var=0.2, scale=0.05).copy()))
    # hills north + west (displaced grid)
    for name, (x0, x1, y0, y1, hmax) in {'hills_n': (-4000, 2600, 1600, 5600, 380), 'hills_w': (-4000, -1200, -3000, 1800, 260)}.items():
        nx, ny = 90, 60
        bm = bmesh.new()
        grid_bm(bm, x0, x1, y0, y1, nx, ny)
        from mathutils import noise
        for v in bm.verts:
            x, y = v.co.x, v.co.y
            if name == 'hills_n':
                edge = min(1.0, max(0.0, (y - y0) / 900.0))
            else:
                edge = min(1.0, max(0.0, (x1 - x) / 700.0))
            h = noise.fractal(Vector((x / 1400.0, y / 1400.0, 0.3)), 0.6, 2.1, 5) * 0.5 + 0.55
            h += 0.5 * abs(noise.noise(Vector((x / 700.0, y / 700.0, 1.7))))
            v.co.z = max(0.0, h) * hmax * edge - 2.0
        ob = bm_obj(name, bm, COAST, [M['hill']], uv=False)
        ob.data.shade_smooth()
    # pond belt: grid of rectangular ponds with earthen bunds (north of the road, west of the coast)
    pond = C('A-POND', False)
    pond2 = C('A-POND-B', False)
    for cc, wm in ((pond, M['pond']), (pond2, M['pond2'])):
        bm = bmesh.new()
        grid_bm(bm, -30.0, 30.0, -20.0, 20.0)
        w = bm_obj(cc.name + '.water', bm, cc, [wm], uv=False)
        w.location.z = 0.12
        bmb = bmesh.new()
        for (xa, xb, ya, yb) in ((-33.2, 33.2, -23.2, -18.5), (-33.2, 33.2, 18.5, 23.2), (-33.2, -28.5, -18.5, 18.5), (28.5, 33.2, -18.5, 18.5)):
            bbox_bm(bmb, xa, xb, ya, yb, -0.05, 0.9)
        b = bm_obj(cc.name + '.bund', bmb, cc, [M['bund']], 0.6, smooth_angle=60)
    rng = random.Random(9)
    k = 0
    for i in range(22):
        for j in range(26):
            x = 620 + i * 66.5
            y = -15 + j * 46.5
            if x + 40 > coast_x(y) - 90 or (x < 900 and y < 120):
                continue
            if rng.random() < 0.08:
                continue
            sklib.instance(pond if rng.random() < 0.7 else pond2, (x, y, 0), 0.0, 'pond_%d' % k, COAST)
            k += 1
    print('ponds', k)


build_land()


def build_road():
    R = C('A-ENV-ROAD')
    x0, x1 = -3000.0, 1500.0
    rng = random.Random(21)
    # gravel shoulders (wide strip) then asphalt with ragged worn edges on top
    ground_plane('road_shoulder', x0, x1, ROAD_Y - 5.2, ROAD_Y + 5.2, -0.01, R, M['gravel'], cuts=1)
    n = 900
    bm = bmesh.new()
    rows = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        e1 = rng.uniform(-0.25, 0.08) + 0.12 * math.sin(x * 0.05)
        e2 = rng.uniform(-0.25, 0.08) + 0.12 * math.sin(x * 0.043 + 1)
        rows.append([bm.verts.new((x, ROAD_Y - 3.5 - e1, 0.0)), bm.verts.new((x, ROAD_Y, 0.005)), bm.verts.new((x, ROAD_Y + 3.5 + e2, 0.0))])
    for i in range(n):
        for j in range(2):
            bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]))
    road = bm_obj('road_asphalt', bm, R, [M['asphalt']])
    # markings: faded dashed centre line, edge lines
    mk = bpy.data.materials.get('road_paint') or sklib.flat('road_paint', (0.72, 0.72, 0.68), rough=0.6, var=0.25, scale=3.0)
    bmd = bmesh.new()
    x = x0
    while x < x1:
        bbox_bm(bmd, x, x + 3.0, ROAD_Y - 0.06, ROAD_Y + 0.06, 0.0, 0.012)
        x += 7.5
    for sy in (-1, 1):
        bbox_bm(bmd, x0, x1, ROAD_Y + sy * 3.05 - 0.05, ROAD_Y + sy * 3.05 + 0.05, 0.0, 0.01)
    bm_obj('road_markings', bmd, R, [mk])
    # yard access apron: concrete from the gate to the road
    ground_plane('gate_apron', 12.0, 20.0, ROAD_Y + 3.4, -46.0, 0.003, R, M['concrete'], cuts=1)
    # trees, palms, stalls, poles along the road; scatter on the land
    T = C('ROAD_SCATTER')
    k = 0
    x = -500.0
    while x < 1400:
        for side in (-1, 1):
            if rng.random() < 0.65:
                off = rng.uniform(7.0, 16.0)
                y = ROAD_Y + side * off
                if -36 < x < 36 and y > -48:
                    continue
                kind = PALMS if rng.random() < 0.35 else TREES_HI
                sklib.instance(kind[rng.randrange(3)], (x + rng.uniform(-3, 3), y, 0), rng.uniform(0, 6.28), 'rtree_%d' % k, T,
                               rng.uniform(0.8, 1.2))
                k += 1
        x += rng.uniform(9.0, 18.0)
    # power poles along the south shoulder with sagging wires
    pole = C('A-POLE', False)
    bmp = bmesh.new()
    cyl_bm(bmp, (0, 0, 4.5), 0.13, 9.0, seg=8, r2=0.08)
    bm_obj('pole_shaft', bmp, pole, [M['pole_conc']], None)
    bmx = bmesh.new()
    bbox_bm(bmx, -0.04, 0.04, -0.9, 0.9, 8.4, 8.5)
    for yy in (-0.8, 0.0, 0.8):
        cyl_bm(bmx, (0, yy, 8.6), 0.035, 0.16, seg=8)
    bm_obj('pole_arm', bmx, pole, [M['galv']], None)
    px = list(range(-480, 1400, 42))
    for i, xx in enumerate(px):
        sklib.instance(pole, (xx, ROAD_Y - 6.0, 0), 0.0, 'pole_%d' % i, T)
    wm = sklib.flat('wire', (0.02, 0.02, 0.02), rough=0.4)
    for yy in (-0.8, 0.0, 0.8):
        cu = bpy.data.curves.new('wire_%g' % yy, 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = 0.012
        cu.bevel_resolution = 1
        sp = cu.splines.new('POLY')
        pts = []
        for i in range(len(px) - 1):
            for t in (0, 0.25, 0.5, 0.75):
                xx = px[i] + 42 * t
                pts.append((xx, ROAD_Y - 6.0 + yy, 8.68 - 0.9 * 4 * t * (1 - t)))
        sp.points.add(len(pts) - 1)
        for p, co in zip(sp.points, pts):
            p.co = co + (1,)
        o = sklib.new_obj('wire_%g' % yy, cu, R)
        cu.materials.append(wm)
    # roadside stalls (bamboo posts, tarp roof, counter with produce crates)
    st = C('A-STALL', False)
    bms = bmesh.new()
    for (sx, sy, h) in ((-1.6, -1.1, 2.3), (1.6, -1.1, 2.3), (-1.6, 1.1, 2.0), (1.6, 1.1, 2.0)):
        cyl_bm(bms, (sx, sy, h / 2), 0.05, h, seg=8)
    bm_obj('stall_posts', bms, st, [M['bark']], None)
    rt = box('stall_tarp', st, M['tarp_blue'], (0, 0, 2.2), (3.6, 2.6, 0.02), 0.005, rot=(math.atan2(0.3, 2.2), 0, 0))
    box('stall_counter', st, M['wood'], (0, -0.6, 0.45), (3.0, 0.8, 0.9), 0.01)
    fruit = [sklib.flat('fruit_%d' % i, c, rough=0.45, var=0.15) for i, c in enumerate([(0.65, 0.35, 0.03), (0.25, 0.45, 0.05), (0.55, 0.06, 0.03), (0.7, 0.55, 0.1)])]
    rng2 = random.Random(3)
    for i in range(4):
        cr = sklib.crate((0.55, 0.38, 0.05) if i % 2 else (0.05, 0.3, 0.1), 'stall_crate_%d' % i, st, 0.5)
        cr.location = (-1.1 + i * 0.72, -0.6, 0.9)
        cr.rotation_euler.z = math.pi / 2 + rng2.uniform(-0.1, 0.1)
        bmfr = bmesh.new()
        for q in range(28):
            p = Vector((rng2.uniform(-0.15, 0.15), rng2.uniform(-0.25, 0.25), 0.2 + rng2.uniform(0, 0.08)))
            bmesh.ops.create_icosphere(bmfr, subdivisions=2, radius=rng2.uniform(0.035, 0.05), matrix=Matrix.Translation(p))
        fo = bm_obj('stall_fruit_%d' % i, bmfr, st, [fruit[i]], None, uv=False)
        fo.data.shade_smooth()
        fo.location = cr.location
        fo.rotation_euler.z = cr.rotation_euler.z
    box('stall_bench', st, M['wood'], (0, 0.7, 0.25), (1.6, 0.35, 0.5), 0.01)
    for i, (xx, side, rz) in enumerate([(52.0, 1, 0.0), (118.0, -1, math.pi), (170.0, 1, 0.05), (236.0, -1, math.pi + 0.08)]):
        sklib.instance(st, (xx, ROAD_Y + side * 6.4, 0), rz, 'stall_%d' % i, T)
    # far scatter: trees and palms on the land (outside ponds/sea/road/yard), more low-poly further out
    rng3 = random.Random(77)
    nfar = 0
    for i in range(15000):
        x = rng3.uniform(-2500, 2200)
        y = rng3.uniform(-2500, 2600)
        if x > coast_x(y) - 80:
            continue
        if -40 < x < 40 and -50 < y < 40:
            continue
        if abs(y - ROAD_Y) < 7:
            continue
        inpond = (600 < x < 2100 and -40 < y < 1200)
        if inpond and rng3.random() < 0.85:
            continue
        # clustered villages/groves: keep trees where a low-frequency pattern is high
        from mathutils import noise
        if noise.noise(Vector((x / 300.0, y / 300.0, 0.5))) < -0.1 and rng3.random() < 0.8:
            continue
        d = math.hypot(x - 150, y + 80)
        palm = rng3.random() < 0.45
        if d < 350:
            src = (PALMS if palm else TREES_HI)[rng3.randrange(3)]
        else:
            src = (PALMS[rng3.randrange(3)]) if (palm and d < 900) else TREES_LO[rng3.randrange(3)]
        sklib.instance(src, (x, y, 0), rng3.uniform(0, 6.28), 'ftree_%d' % i, T, rng3.uniform(0.8, 1.3))
        nfar += 1
    print('far trees', nfar)
    # yard trees along the walls
    for i, (xx, yy) in enumerate([(-31.5, -43.5), (-31.5, -30.0), (31.5, -40.0), (-31.5, -14.0), (30.5, -18.0), (8.0, -43.5)]):
        sklib.instance((PALMS + TREES_HI)[i % 6], (xx, yy, 0), i * 1.3, 'ytree_%d' % i, T, 0.9)


build_road()


# ======================================================================================================== traffic
TRAFFIC = C('A-TRAFFIC')


def wheel_small(bm, c, r, w, mi=0):
    cyl_bm(bm, c, r, w, 'X', 20, mi)


def rider(bm, x_hip, z_seat, mi_shirt, mi_skin, mi_pants, mi_helmet, lean=0.2):
    """Simple seated rider proxy (mid-distance only): torso, thighs, shins, arms, head + helmet."""
    def mark(vs, mi):
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = mi

    def seg(p0, p1, r, mi):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        q = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r * 0.9, depth=d.length,
                                    matrix=Matrix.Translation((p0 + p1) / 2) @ q)
        mark(res['verts'], mi)
    hip = Vector((0, x_hip, z_seat + 0.08))
    sh = hip + Vector((0, -0.18 - lean * 0.3, 0.52))
    seg(hip, sh, 0.15, mi_shirt)
    for sx in (-0.11, 0.11):
        knee = Vector((sx * 1.6, x_hip - 0.42, z_seat + 0.12))
        seg(hip + Vector((sx, 0, 0)), knee, 0.075, mi_pants)
        seg(knee, Vector((sx * 1.6, x_hip - 0.38, 0.32)), 0.055, mi_pants)
        hand = Vector((sx * 3.2, x_hip - 0.62, z_seat + 0.42))
        el = (sh + hand) / 2 + Vector((sx * 0.8, 0.05, -0.12))
        seg(sh + Vector((sx * 1.5, 0, -0.03)), el, 0.05, mi_shirt)
        seg(el, hand, 0.04, mi_skin)
    head = sh + Vector((0, -0.04, 0.2))
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.115, matrix=Matrix.Translation(head))
    mark(res['verts'], mi_helmet)


SKIN = sklib.flat('rider_skin', (0.30, 0.17, 0.10), rough=0.5, var=0.1)
SHIRTS = [sklib.linen_fabric(c, 0.1) for c in [(0.75, 0.75, 0.72), (0.12, 0.2, 0.45), (0.45, 0.1, 0.08), (0.2, 0.32, 0.18)]]
PANTS = sklib.linen_fabric((0.07, 0.07, 0.09), 0.1)
HELM = sklib.plastic((0.04, 0.04, 0.05), 0.2, name='helmet_black')


def two_wheeler(name, paint, shirt, scooter=False):
    c = C(name, False)
    bm = bmesh.new()
    wheel_small(bm, (0, 0.65, 0.29), 0.29, 0.09, 1)
    wheel_small(bm, (0, -0.65, 0.29), 0.29, 0.09, 1)
    if scooter:
        bbox_bm(bm, -0.18, 0.18, -0.1, 0.65, 0.35, 0.72, 0)     # rear body
        bbox_bm(bm, -0.16, 0.16, -0.55, -0.1, 0.22, 0.32, 0)    # floorboard
        bbox_bm(bm, -0.2, 0.2, -0.75, -0.55, 0.3, 1.0, 0)       # front shield
    else:
        bbox_bm(bm, -0.13, 0.13, -0.35, 0.1, 0.62, 0.86, 0)     # tank
        bbox_bm(bm, -0.12, 0.12, -0.15, 0.25, 0.32, 0.6, 2)     # engine
        bbox_bm(bm, -0.04, 0.04, -0.7, -0.55, 0.3, 0.95, 2)     # fork
        bbox_bm(bm, -0.06, 0.06, 0.6, 0.75, 0.55, 0.62, 2)      # rear mudguard
    bbox_bm(bm, -0.13, 0.13, 0.05, 0.6, 0.76, 0.84, 3)          # seat
    bbox_bm(bm, -0.36, 0.36, -0.68, -0.64, 1.0, 1.03, 2)        # handlebar
    bbox_bm(bm, -0.08, 0.08, -0.78, -0.7, 0.88, 1.0, 4)         # headlamp
    rider(bm, 0.25, 0.82, 5, 6, 7, 8)
    o = bm_obj(name + '.mesh', bm, c, [paint, M['tyre'], M['chassis'], M['rubber'], M['lamp'], shirt, SKIN, PANTS, HELM], 0.01)
    return c


def auto_rickshaw():
    c = C('A-VEH-AUTO', False)
    bm = bmesh.new()
    wheel_small(bm, (0, -1.0, 0.2), 0.2, 0.1, 1)
    for sx in (-0.58, 0.58):
        wheel_small(bm, (sx, 0.65, 0.2), 0.2, 0.11, 1)
    bbox_bm(bm, -0.65, 0.65, -0.35, 1.0, 0.25, 0.85, 0)        # rear tub (yellow)
    bbox_bm(bm, -0.42, 0.42, -1.2, -0.35, 0.3, 0.75, 0)        # front cowl
    bbox_bm(bm, -0.5, 0.5, -0.85, -0.7, 0.75, 1.35, 2)         # windscreen
    bbox_bm(bm, -0.7, 0.7, -0.9, 1.05, 1.62, 1.72, 3)          # canvas roof (black)
    for sx in (-0.66, 0.66):
        bbox_bm(bm, sx - 0.02, sx + 0.02, -0.85, -0.81, 0.75, 1.65, 4)
        bbox_bm(bm, sx - 0.02, sx + 0.02, 0.98, 1.02, 0.85, 1.65, 3)
    bbox_bm(bm, -0.62, 0.62, 0.95, 1.05, 0.85, 1.62, 3)        # rear canvas
    bbox_bm(bm, -0.55, 0.55, 0.2, 0.75, 0.85, 1.0, 5)          # rear seat
    bbox_bm(bm, -0.07, 0.07, -1.22, -1.18, 0.55, 0.68, 6)      # headlamp
    rider(bm, -0.25, 0.9, 7, 8, 9, 10, lean=0.0)
    bm_obj('A-VEH-AUTO.mesh', bm, c, [M['auto_yellow'], M['tyre'], M['glass'], M['tarp_black'], M['chassis'],
                                       M['rubber'], M['lamp'], SHIRTS[3], SKIN, PANTS, sklib.flat('hair_black', (0.02, 0.02, 0.02), 0.5)], 0.02)
    return c


def bus():
    c = C('A-VEH-BUS', False)
    bm = bmesh.new()
    bbox_bm(bm, -1.25, 1.25, -5.5, 5.5, 0.45, 2.15, 0)
    bbox_bm(bm, -1.25, 1.25, -5.5, 5.5, 2.95, 3.15, 0)
    bbox_bm(bm, -1.24, 1.24, -5.45, 5.45, 2.15, 2.95, 2)         # window band
    bbox_bm(bm, -1.27, 1.27, -5.52, 5.52, 1.2, 1.45, 1)          # green stripe
    for sx in (-1.0, 1.0):
        for yy in (-3.6, 3.4):
            wheel_small(bm, (sx, yy, 0.5), 0.5, 0.28, 3)
    bm_obj('A-VEH-BUS.mesh', bm, c, [M['bus_white'], M['bus_green'], M['glass'], M['tyre']], 0.05)
    return c


BIKES = [two_wheeler('A-VEH-2W-a', M['bike_red'], SHIRTS[0]), two_wheeler('A-VEH-2W-b', M['bike_blue'], SHIRTS[1], True),
         two_wheeler('A-VEH-2W-c', M['bike_black'], SHIRTS[2])]
AUTO = auto_rickshaw()
BUS = bus()
# left-hand traffic: eastbound (+X) keeps to the north lane (y > road centre), westbound to the south lane.
# vehicle meshes face -Y; rot_z = +90 deg -> facing +X (east), -90 -> facing -X (west).
LANE_E, LANE_W = ROAD_Y + 1.75, ROAD_Y - 1.75
movers = [(BIKES[0], LANE_E + 0.9, math.pi / 2, -30.0, 0.55), (BIKES[1], LANE_E + 0.7, math.pi / 2, -62.0, 0.45),
          (BIKES[2], LANE_W - 0.8, -math.pi / 2, 175.0, -0.5), (AUTO, LANE_E, math.pi / 2, 5.0, 0.36),
          (BUS, LANE_W, -math.pi / 2, 420.0, -0.6)]
for i, (src, y, rz, x_at_1, v) in enumerate(movers):
    e = sklib.instance(src, (x_at_1, y, 0), rz, 'traffic_%d' % i, TRAFFIC)
    e.location.x = x_at_1
    e.keyframe_insert('location', index=0, frame=1)
    e.location.x = x_at_1 + v * 215
    e.keyframe_insert('location', index=0, frame=216)
    for fc in sklib._fcurves(e):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'


# ======================================================================================================== people
PEOPLE = C('PEOPLE')
sig = people.make_person('P-YARD-1-signaller', sex='male', age=0.35, skin_tone=0.65, outfit='hivis_helmet', pose='wave',
                         location=(4.1, -7.2, 0), rotation_z=-60 * D2R, seed=3)
people.animate_cycle(sig, 'wave', 1, 216, phase=0.2)
dock = people.make_person('P-YARD-2-dockhand', sex='male', age=0.25, skin_tone=0.8, body={'weight': 0.45},
                          outfit='tshirt_shorts', pose='pull_rope', location=(2.0, -1.3, 0), rotation_z=-90 * D2R, seed=8)
people.animate_cycle(dock, 'pull', 1, 216, phase=0.6)
guard = people.make_person('P-YARD-3-guard', sex='male', age=0.6, skin_tone=0.55, outfit='formal_shirt_lanyard',
                           pose='stand', location=(26.6, -44.2, 0), rotation_z=200 * D2R, seed=12)
people.animate_cycle(guard, 'work', 1, 216, phase=0.4, amount=0.4)
porter = people.make_person('P-YARD-4-porter', sex='male', age=0.45, skin_tone=0.9, body={'weight': 0.4},
                            outfit='tshirt_lungi', pose='carry', location=(27.2, -6.4, 0), rotation_z=120 * D2R, seed=21)
people.animate_cycle(porter, 'work', 1, 216, phase=0.7, amount=0.5)
for p in (sig, dock, guard, porter):
    for o in [p] + list(p.children_recursive):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        PEOPLE.objects.link(o)


# ======================================================================================================== camera
cam = sklib.camera('CAM', 28.0, (0, 3.0, 2.75), (0, -10, 2.35))
cam.data.clip_end = 12000.0
keys = [
    (1, (0.0, 3.0, 2.75), (0.0, -10.0, 2.35), 28.0),          # BRIDGE_DOCK
    (24, (0.0, -1.6, 2.9), (0.0, -10.0, 1.7), None),
    (44, (0.0, -5.4, 3.95), (0.2, -10.5, 1.3), None),
    (58, (0.4, -9.6, 4.85), (0.3, -12.5, 1.4), None),
    (74, (4.2, -14.6, 5.6), (0.2, -9.0, 1.8), None),
    (90, (8.5, -18.5, 6.2), (0.5, -5.5, 1.9), None),
    (120, (17.0, -30.0, 11.0), (0.0, -5.5, 1.8), 28.0),
    (150, (46.0, -66.0, 28.0), (14.0, -6.0, 0.0), None),
    (175, (100.0, -86.0, 72.0), (175.0, 60.0, 0.0), None),
    (200, (192.0, -105.0, 185.0), (560.0, -45.0, 0.0), None),
    (216, (260.0, -110.0, 300.0), (260.0 + 300.0 / math.tan(35 * D2R), -110.0, 0.0), 24.0),   # BRIDGE_COAST
]
sklib.camera_path(cam, keys)
for f, v in ((1, 0.03), (100, 0.03), (130, 0.5)):
    cam.data.clip_start = v
    cam.data.keyframe_insert('clip_start', frame=f)
for f, v in ((1, -0.3), (70, -0.3), (110, 0.0), (216, 0.0)):
    S.view_settings.exposure = v
    S.view_settings.keyframe_insert('exposure', frame=f)

# keep the final aerial clean: the yard/plant are behind the camera at f216; nothing else needed.
sklib.finish('truck', 'ext')
# finish() resets exposure to 0; the keyframes above still drive it (re-key to be explicit after finish)
for f, v in ((1, -0.3), (70, -0.3), (110, 0.0), (216, 0.0)):
    S.view_settings.exposure = v
    S.view_settings.keyframe_insert('exposure', frame=f)
bpy.ops.wm.save_mainfile()
print('TRUCK BUILD OK')
