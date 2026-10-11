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
import look  # noqa: E402  (art pass, issue #75: COLOR_SCRIPT row 10 v-truck)

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


HAZE_COL = tuple(0.85 * c for c in look.hex_rgb('#e8d2b0'))   # morning haze (was cool grey-blue 0.55/0.63/0.72)


def haze(m, color=HAZE_COL, dist=4500.0, maxf=0.45):
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
M['white_box'] = grimed(sklib.painted_metal((0.80, 0.80, 0.77), wear=0.3, streaks=0.4, contrast=0.4), 'truck_box_white',
                        0.9, 2.6, amount=0.85, streaks=0.8)
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
M['puf'] = grimed(sklib.painted_metal((0.64, 0.72, 0.82), wear=0.12, contrast=0.3), 'puf_panel', 0.0, 1.8,
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
    sepn = _n(nt, 'ShaderNodeSeparateXYZ', -150, 750)
    _l(nt, geo.outputs['Normal'], sepn.inputs[0])
    und = _maprange(nt, sepn.outputs['Z'], -0.7, 0.6, 0.35, 1.0, 0, 750)
    vmu = _n(nt, 'ShaderNodeVectorMath', 250, 500, operation='SCALE')
    _l(nt, col, vmu.inputs[0])
    _l(nt, und, vmu.inputs['Scale'])
    _l(nt, vmu.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6 if cut else 0.85
    b.inputs['Subsurface Weight'].default_value = 0.0
    if not cut:
        b.inputs['Specular IOR Level'].default_value = 0.3   # solid crowns: break the surface into leaf clumps (dark gaps between clumps, bumped clumps)
        vc = _n(nt, 'ShaderNodeTexVoronoi', -650, 900, feature='F1')
        vc.inputs['Scale'].default_value = 1.6
        _l(nt, geo.outputs['Position'], vc.inputs['Vector'])
        ve = _n(nt, 'ShaderNodeTexVoronoi', -650, 1100, feature='DISTANCE_TO_EDGE')
        ve.inputs['Scale'].default_value = 1.6
        _l(nt, geo.outputs['Position'], ve.inputs['Vector'])
        gap = _maprange(nt, ve.outputs['Distance'], 0.0, 0.12, 0.25, 1.0, -400, 1100)
        vm2 = _n(nt, 'ShaderNodeVectorMath', 450, 650, operation='SCALE')
        _l(nt, vmu.outputs[0], vm2.inputs[0])
        _l(nt, gap, vm2.inputs['Scale'])
        _l(nt, vm2.outputs[0], b.inputs['Base Color'])
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
    if cut:
        _l(nt, nz2.outputs['Fac'], bp.inputs['Height'])
    else:
        bp.inputs['Strength'].default_value = 0.9
        _l(nt, _math(nt, 'MULTIPLY_ADD', nz2.outputs['Fac'], 0.3, x=100, y=-500,
                     c=_maprange(nt, vc.outputs['Distance'], 0.0, 0.8, 1.0, 0.0, -100, -600)), bp.inputs['Height'])
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
    """Farmland seen from 10-300 m: irregular (domain-warped) fields - paddy greens, fallow, red laterite, olive scrub -
    with bund lines, broad dry/green zones, shader tree-canopy groves (bumped crowns), grass scan detail up close, haze."""
    m = bpy.data.materials.get('land')
    if m:
        return m
    t = sklib.tex('sparse_grass')
    m, nt = sklib._new_mat('land')
    out = _n(nt, 'ShaderNodeOutputMaterial', 1600, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 1300, 0)
    geo = _n(nt, 'ShaderNodeNewGeometry', -2000, 0)
    pos = geo.outputs['Position']
    # domain warp so field edges wander like real parcels
    wn = _n(nt, 'ShaderNodeTexNoise', -1800, 300)
    wn.inputs['Scale'].default_value = 1 / 160.0
    wn.inputs['Detail'].default_value = 2.0
    _l(nt, pos, wn.inputs['Vector'])
    wv = _n(nt, 'ShaderNodeVectorMath', -1600, 300, operation='MULTIPLY_ADD')
    _l(nt, wn.outputs['Color'], wv.inputs[0])
    wv.inputs[1].default_value = (55.0, 55.0, 0.0)
    _l(nt, pos, wv.inputs[2])
    wpos = wv.outputs[0]
    # land-holding zones (warped voronoi ~150 m), each with its own plot orientation and plot size
    zv = _n(nt, 'ShaderNodeTexVoronoi', -1400, 500, feature='F1')
    zv.inputs['Scale'].default_value = 1 / 150.0
    _l(nt, wpos, zv.inputs['Vector'])
    zs = _n(nt, 'ShaderNodeSeparateColor', -1250, 500)
    _l(nt, zv.outputs['Color'], zs.inputs[0])
    rot = _n(nt, 'ShaderNodeVectorRotate', -1100, 350, rotation_type='Z_AXIS')
    _l(nt, pos, rot.inputs['Vector'])
    _l(nt, _math(nt, 'MULTIPLY', zs.outputs[0], 3.1416, x=-1250, y=350), rot.inputs['Angle'])
    # plots: brick pattern = rows of rectangular fields (~25-45 m x 12-20 m) with earth bunds as mortar
    br = _n(nt, 'ShaderNodeTexBrick', -900, 350)
    br.offset, br.squash = 0.37, 1.0
    br.inputs['Color1'].default_value = (0, 0, 0, 1)
    br.inputs['Color2'].default_value = (1, 1, 1, 1)
    br.inputs['Mortar'].default_value = (0, 0, 0, 1)
    _l(nt, _maprange(nt, zs.outputs[1], 0.0, 1.0, 1 / 30.0, 1 / 55.0, -1100, 150), br.inputs['Scale'])
    br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Mortar Smooth'].default_value = 0.3
    br.inputs['Bias'].default_value = 0.0
    br.inputs['Brick Width'].default_value = 0.9
    br.inputs['Row Height'].default_value = 0.35
    _l(nt, rot.outputs[0], br.inputs['Vector'])
    pr = _n(nt, 'ShaderNodeSeparateColor', -700, 450)
    _l(nt, br.outputs['Color'], pr.inputs[0])
    ramp = _n(nt, 'ShaderNodeValToRGB', -500, 450)
    cr = ramp.color_ramp
    pal = [(0.0, (0.045, 0.11, 0.018)), (0.14, (0.10, 0.17, 0.03)), (0.26, (0.065, 0.13, 0.025)), (0.38, (0.17, 0.12, 0.06)),
           (0.48, (0.11, 0.15, 0.035)), (0.58, (0.19, 0.09, 0.045)), (0.68, (0.075, 0.095, 0.03)), (0.78, (0.14, 0.16, 0.05)),
           (0.88, (0.21, 0.16, 0.08)), (0.96, (0.05, 0.10, 0.02))]
    cr.interpolation = 'CONSTANT'
    cr.elements[0].position, cr.elements[0].color = pal[0][0], pal[0][1] + (1,)
    cr.elements[1].position, cr.elements[1].color = pal[1][0], pal[1][1] + (1,)
    for p_, c_ in pal[2:]:
        cr.elements.new(p_).color = c_ + (1,)
    _l(nt, _math(nt, 'FRACT', _math(nt, 'MULTIPLY_ADD', zs.outputs[2], 0.37, x=-650, y=600, c=pr.outputs[0]), x=-600, y=550), ramp.inputs['Fac'])
    col = ramp.outputs['Color']
    # some zones are scrub / fallow without plots (dry olive-brown, mottled)
    sn = _noise(nt, pos, 1 / 18.0, 6.0, 0.7, -900, 700)
    scrub = _mix(nt, _maprange(nt, sn.outputs['Fac'], 0.35, 0.65, 0, 1, -700, 700), (0.10, 0.10, 0.04), (0.20, 0.15, 0.08), 'MIX', -500, 700)
    zone = _maprange(nt, zs.outputs[1], 0.72, 0.78, 0.0, 1.0, -700, 850)
    col = _mix(nt, zone, col, scrub, 'MIX', -300, 500)
    # broad moisture zones
    zn = _noise(nt, pos, 1 / 700.0, 3.0, 0.5, -1400, 650)
    col = _mix(nt, _maprange(nt, zn.outputs['Fac'], 0.42, 0.62, 0.0, 0.4, -1200, 650), col, (0.16, 0.14, 0.07), 'MIX', -200, 450)
    # bunds (brick mortar) between plots, only where there are plots
    edge = _math(nt, 'MULTIPLY', br.outputs['Fac'], _math(nt, 'SUBTRACT', 1.0, zone, x=-700, y=100), x=-550, y=150)
    edge = _math(nt, 'MULTIPLY', edge, 0.8, x=-400, y=150)
    col = _mix(nt, edge, col, (0.20, 0.17, 0.10), 'MIX', -100, 300)
    # in-field streaks (crop rows / mottling)
    nz = _noise(nt, pos, 0.09, 8.0, 0.7, -1400, -250)
    v = _maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 0.62, 1.38, -1200, -250)
    nzb = _noise(nt, pos, 0.025, 4.0, 0.6, -1400, -400)          # 20-40 m patches inside plots (uneven growth, wet/dry)
    v = _math(nt, 'MULTIPLY', v, _maprange(nt, nzb.outputs['Fac'], 0.35, 0.65, 0.8, 1.2, -1200, -400), x=-1000, y=-300)
    # furrows (2.5 m) along the plot direction in some plots
    sepr = _n(nt, 'ShaderNodeSeparateXYZ', -900, -500)
    _l(nt, rot.outputs[0], sepr.inputs[0])
    fur = _math(nt, 'SINE', _math(nt, 'MULTIPLY', sepr.outputs['Y'], 2 * math.pi / 2.5, x=-750, y=-500), x=-650, y=-500)
    plough = _math(nt, 'GREATER_THAN', _math(nt, 'FRACT', _math(nt, 'MULTIPLY', pr.outputs[0], 7.0, x=-750, y=-650), x=-650, y=-650), 0.6, x=-550, y=-650)
    v = _math(nt, 'MULTIPLY', v, _math(nt, 'MULTIPLY_ADD', _math(nt, 'MULTIPLY', fur, plough, x=-500, y=-550), 0.12, x=-400, y=-550, c=1.0),
              x=-300, y=-400)
    vm = _n(nt, 'ShaderNodeVectorMath', -500, 150, operation='SCALE')
    _l(nt, col, vm.inputs[0])
    _l(nt, v, vm.inputs['Scale'])
    col = vm.outputs[0]
    # tree-canopy groves: patch mask x small crown cells (dark, bumped, AO between crowns)
    gm = _noise(nt, pos, 1 / 230.0, 4.0, 0.55, -1400, -500)
    grove = _maprange(nt, gm.outputs['Fac'], 0.56, 0.60, 0.0, 1.0, -1200, -500)
    gm2 = _noise(nt, pos, 1 / 60.0, 3.0, 0.5, -1400, -700)
    grove = _math(nt, 'MAXIMUM', grove, _maprange(nt, gm2.outputs['Fac'], 0.70, 0.73, 0.0, 1.0, -1200, -700), x=-1050, y=-600)
    cv = _n(nt, 'ShaderNodeTexVoronoi', -1400, -900, feature='F1')
    cv.inputs['Scale'].default_value = 1 / 4.2
    _l(nt, pos, cv.inputs['Vector'])
    crown = _maprange(nt, cv.outputs['Distance'], 0.95, 0.15, 0.0, 1.0, -1200, -900)
    ccol = _mix(nt, crown, (0.008, 0.02, 0.006), (0.05, 0.10, 0.025), 'MIX', -900, -900)
    cvc = _n(nt, 'ShaderNodeSeparateColor', -1200, -1050)
    _l(nt, cv.outputs['Color'], cvc.inputs[0])
    ccol = _mix(nt, _math(nt, 'MULTIPLY', cvc.outputs[0], 0.5, x=-1000, y=-1050), ccol, (0.09, 0.12, 0.03), 'MIX', -750, -950)
    col = _mix(nt, grove, col, ccol, 'MIX', -350, 100)
    # grass scan detail (multiplied, normalised) close to the camera
    uvm = _n(nt, 'ShaderNodeMapping', -1400, -1300)
    uvm.inputs['Scale'].default_value = (1 / t['size_m'],) * 3
    _l(nt, pos, uvm.inputs['Vector'])
    di = sklib._img(nt, t['diff'], True, uvm.outputs[0], -1150, -1300)
    g = 1.0 / sklib._avg_lum(di.image)
    bw = _n(nt, 'ShaderNodeRGBToBW', -900, -1300)
    _l(nt, di.outputs['Color'], bw.inputs[0])
    cd = _n(nt, 'ShaderNodeCameraData', -1150, -1500)
    near = _maprange(nt, cd.outputs['View Distance'], 40.0, 150.0, 1.0, 0.0, -900, -1500)
    det = _math(nt, 'MULTIPLY_ADD', _math(nt, 'SUBTRACT', _math(nt, 'MULTIPLY', bw.outputs[0], g, x=-750, y=-1300), 1.0, x=-650, y=-1300),
                near, x=-550, y=-1400, c=1.0)
    vm2 = _n(nt, 'ShaderNodeVectorMath', -150, 50, operation='SCALE')
    _l(nt, col, vm2.inputs[0])
    _l(nt, det, vm2.inputs['Scale'])
    _l(nt, vm2.outputs[0], b.inputs['Base Color'])
    # normals: grass scan up close + crown bumps in the groves
    ni = sklib._img(nt, t['nor'], False, uvm.outputs[0], -1150, -1700)
    nm = _n(nt, 'ShaderNodeNormalMap', -850, -1700)
    _l(nt, ni.outputs['Color'], nm.inputs['Color'])
    bp = _n(nt, 'ShaderNodeBump', 600, -600)
    bp.inputs['Distance'].default_value = 0.5
    _l(nt, _math(nt, 'MULTIPLY', crown, grove, x=300, y=-600), bp.inputs['Height'])
    _l(nt, nm.outputs[0], bp.inputs['Normal'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    _l(nt, _maprange(nt, grove, 0.0, 1.0, 0.92, 0.75, 600, -300), b.inputs['Roughness'])
    _l(nt, b.outputs[0], out.inputs['Surface'])
    haze(m, dist=3800.0, maxf=0.5)
    return m


M['land'] = land_mat()


def water_mat(name, deep, shallow, rough=0.28, spec=0.2):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    geo = _n(nt, 'ShaderNodeNewGeometry', -900, 0)
    nz = _noise(nt, geo.outputs['Position'], 0.03, 4.0, 0.6, -650, 200)
    _l(nt, _mix(nt, _maprange(nt, nz.outputs['Fac'], 0.35, 0.65, 0, 1, -400, 200), deep, shallow, 'MIX', -150, 200),
       b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
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
    haze(m, maxf=0.5)
    return m


# aquaculture pond water: green / olive / teal / turbid, never mirror-like
PONDW = [water_mat('pond_water_a', (0.012, 0.040, 0.026), (0.035, 0.085, 0.045)),
         water_mat('pond_water_b', (0.030, 0.045, 0.020), (0.075, 0.090, 0.040)),
         water_mat('pond_water_c', (0.008, 0.040, 0.040), (0.025, 0.090, 0.075)),
         water_mat('pond_water_d', (0.050, 0.060, 0.035), (0.100, 0.105, 0.060), rough=0.14)]


def coast_d(nt, pos, x=-1200, y=0):
    """Signed distance (m, + = seaward) from the NE-SW coastline x = COAST0 + 0.5 y, in a node tree."""
    sep = _n(nt, 'ShaderNodeSeparateXYZ', x, y)
    _l(nt, pos, sep.inputs[0])
    d = _math(nt, 'MULTIPLY_ADD', sep.outputs['Y'], -0.5, x=x + 150, y=y, c=sep.outputs['X'])
    return _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', d, COAST0, x=x + 300, y=y), 0.894, x=x + 450, y=y)


def sea_mat():
    """Bay of Bengal from the air: turquoise shallows -> deep blue, long swell normals, breaking surf lines parallel to
    the beach (foam broken up by noise), rough enough that the low sun spreads into a sheen, not a pillar."""
    m, nt = sklib._new_mat('sea_water')
    out = _n(nt, 'ShaderNodeOutputMaterial', 1300, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 1000, 0)
    geo = _n(nt, 'ShaderNodeNewGeometry', -1600, 0)
    pos = geo.outputs['Position']
    d = coast_d(nt, pos, -1500, 300)
    depth = _maprange(nt, d, 10.0, 260.0, 0.0, 1.0, -900, 300)
    nzc = _noise(nt, pos, 1 / 90.0, 4.0, 0.6, -1200, 500)
    depth = _math(nt, 'MULTIPLY_ADD', _math(nt, 'SUBTRACT', nzc.outputs['Fac'], 0.5, x=-1000, y=500), 0.35, True, -800, 450, c=depth)
    col = _mix(nt, depth, (0.016, 0.16, 0.19), (0.006, 0.04, 0.075), 'MIX', -600, 300)
    # surf: 3-4 bands of foam near the beach, each broken into streaks
    s = _math(nt, 'SINE', _math(nt, 'MULTIPLY', d, 2 * math.pi / 22.0, x=-1100, y=0), x=-950, y=0)
    band = _maprange(nt, s, 0.55, 0.95, 0.0, 1.0, -800, 0)
    fn = _noise(nt, pos, 0.12, 6.0, 0.65, -1100, -200)
    brk = _maprange(nt, fn.outputs['Fac'], 0.42, 0.62, 0.0, 1.0, -900, -200)
    near = _maprange(nt, d, 95.0, 4.0, 0.0, 1.0, -900, -350)
    shore = _maprange(nt, d, 9.0, 1.0, 0.0, 1.0, -900, -500)        # wash line on the beach edge
    foam = _math(nt, 'MAXIMUM', _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', band, brk, x=-650, y=-100), near, x=-500, y=-150),
                 _math(nt, 'MULTIPLY', shore, brk, x=-650, y=-500), x=-350, y=-200)
    col = _mix(nt, foam, col, (0.80, 0.83, 0.84), 'MIX', -200, 200)
    _l(nt, col, b.inputs['Base Color'])
    _l(nt, _maprange(nt, foam, 0.0, 1.0, 0.16, 0.8, 500, -100), b.inputs['Roughness'])
    b.inputs['Specular IOR Level'].default_value = 0.42
    # swell normals: long crests parallel to the coast + chop
    mp = _n(nt, 'ShaderNodeMapping', -1300, -800)
    mp.inputs['Rotation'].default_value = (0, 0, math.atan2(1.0, -0.5))
    _l(nt, pos, mp.inputs['Vector'])
    w = _n(nt, 'ShaderNodeTexWave', -1100, -800, wave_type='BANDS')
    w.inputs['Scale'].default_value = 1 / 40.0
    w.inputs['Distortion'].default_value = 4.0
    w.inputs['Detail'].default_value = 4.0
    _l(nt, mp.outputs[0], w.inputs['Vector'])
    ch = _noise(nt, pos, 0.35, 6.0, 0.6, -1100, -1000)
    bp = _n(nt, 'ShaderNodeBump', 700, -600)
    bp.inputs['Strength'].default_value = 0.35
    bp.inputs['Distance'].default_value = 0.6
    _l(nt, _math(nt, 'MULTIPLY_ADD', ch.outputs['Fac'], 0.5, x=-800, y=-900, c=w.outputs['Fac']), bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    _l(nt, b.outputs[0], out.inputs['Surface'])
    haze(m, dist=5000.0, maxf=0.32)
    return m


def beach_mat():
    m, nt = sklib._new_mat('beach_sand')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    geo = _n(nt, 'ShaderNodeNewGeometry', -1300, 0)
    d = coast_d(nt, geo.outputs['Position'], -1200, 200)
    wet = _maprange(nt, d, -14.0, -2.0, 0.0, 1.0, -600, 200)
    nz = _noise(nt, geo.outputs['Position'], 0.08, 5.0, 0.6, -700, -100)
    dry = _mix(nt, _maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 0, 1, -450, -100), (0.42, 0.35, 0.25), (0.52, 0.45, 0.33), 'MIX', -250, 0)
    _l(nt, _mix(nt, wet, dry, (0.20, 0.17, 0.12), 'MIX', 0, 100), b.inputs['Base Color'])
    _l(nt, _maprange(nt, wet, 0.0, 1.0, 0.9, 0.25, 200, -200), b.inputs['Roughness'])
    _l(nt, b.outputs[0], out.inputs['Surface'])
    haze(m, dist=5000.0, maxf=0.35)
    return m


COAST0 = 900.0
M['sea'] = sea_mat()
M['beach'] = beach_mat()
M['bund'] = haze(sklib.pbr('bund_mud', 'brown_mud_03', tint=(0.27, 0.20, 0.12), contrast=0.7, wear=0.0, scale=3.0))
M['pond_mud'] = haze(sklib.pbr('pond_mud', 'mud_cracked_dry_03', tint=(0.40, 0.33, 0.24), contrast=0.6, wear=0.0, scale=4.0))
M['track'] = haze(sklib.pbr('laterite_track', 'muddy_tracks', tint=(0.55, 0.32, 0.20), contrast=0.6, wear=0.0, scale=2.0))


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
    SUN.data.color = look.hex_rgb('#ffb870')      # art r6 (lead): warmer than row 10's #ffc98a so sunlit surfaces read morning gold
    SUN.data.keyframe_insert('color', frame=f)


set_sun(20, 100, 1)
set_sun(20, 100, 120)
set_sun(15, 90, 216)
SUN.data.energy = 7.5   # art r5: brighter sun pools on the yard


def tint_sky(horizon='#ffd7a0', zenith='#5f93c8', amount=0.7, strength=1.0):
    """Morning world: multiply the physical sky by a horizon->zenith gradient (hues normalised, so it tints, not darkens)."""
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    bg.inputs['Strength'].default_value *= strength
    tc = _n(nt, 'ShaderNodeTexCoord', -700, -300)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -500, -300)
    _l(nt, tc.outputs['Generated'], sep.inputs[0])
    ramp = _n(nt, 'ShaderNodeValToRGB', -300, -300)
    _l(nt, sep.outputs['Z'], ramp.inputs[0])
    norm = lambda h: (*(c / max(look.hex_rgb(h)) for c in look.hex_rgb(h)), 1.0)
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, norm(horizon)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.45, norm(zenith)
    mx = _mix(nt, amount, sky_node.outputs[0], ramp.outputs[0], 'MULTIPLY', -100, -100)
    _l(nt, mx, bg.inputs['Color'])


tint_sky()
# cool sky fill (no shadow) from the west and a warm low rim from behind the yard (north-east), COLOR_SCRIPT row 10
FILL = look.add_light(S, 'SK_Fill', 'SUN', '#8fb8e0', 0.45, (0, 0, 50), (math.radians(55), 0, math.radians(-100)), shadow=False)   # from az 280 (rz = 180 - az)
RIM = look.add_light(S, 'SK_Rim', 'SUN', '#ffd59a', 1.6, (0, 0, 50), (math.radians(72), 0, math.radians(160)), shadow=True)


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
    la.energy, la.size, la.color = 400.0, 3.0, sklib.kelvin_rgb(5500)   # BRIDGE_DOCK interior 5500 K
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
    ground_plane('yard_concrete', -34, 34, -46, 0.2, 0.0, YARD, sklib.pbr('yard_conc', 'concrete_floor_worn_001', tint=(0.64, 0.55, 0.43),
                                                                          wear=0.55, scale=2.0), cuts=1)
    # saw-cut joints every 6 m (dark, dirt-filled)
    bmj = bmesh.new()
    for x in range(-30, 31, 6):
        bbox_bm(bmj, x - 0.012, x + 0.012, -45.8, -0.1, 0.0, 0.0012)
    for y in range(-42, -1, 6):
        bbox_bm(bmj, -33.8, 33.8, y - 0.012, y + 0.012, 0.0, 0.0012)
    bm_obj('yard_joints', bmj, YARD, [sklib.flat('joint_dirt', (0.035, 0.03, 0.025), rough=0.9, var=0.3, scale=3.0)])
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
    # tyre: revolved section with real tread (staggered lugs either side of a centre rib, lateral grooves)
    W, R, r_in = 0.28, WR, 0.29
    xs = [-W / 2, -W / 2, -W / 2 + 0.025, -W / 2 + 0.055, -0.04, -0.03, -0.012, 0.012, 0.03, 0.04, W / 2 - 0.055, W / 2 - 0.025, W / 2, W / 2]
    bm = bmesh.new()
    seg = 96
    rings = []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        lugL = (k % 6) < 3
        lugR = ((k + 3) % 6) < 3
        rr = []
        for j, x in enumerate(xs):
            if j == 0 or j == len(xs) - 1:
                r = r_in
            elif j in (1, len(xs) - 2):
                r = R - 0.085
            elif j in (2, len(xs) - 3):
                r = R - 0.02
            elif j in (5, 6, 7, 8):        # centre rib with a groove either side
                r = R - 0.002 if j in (6, 7) else R - 0.016
            else:
                r = R if (lugL if x < 0 else lugR) else R - 0.016
            rr.append(bm.verts.new((x, r * math.cos(a), r * math.sin(a))))
        rings.append(rr)
    for k in range(seg):
        A, B = rings[k], rings[(k + 1) % seg]
        for j in range(len(xs) - 1):
            bm.faces.new((A[j], A[j + 1], B[j + 1], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ty = bm_obj('tyre', bm, c, [M['tyre']])
    ty.data.shade_smooth()
    ty.data.set_sharp_from_angle(angle=50 * D2R)
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
    # FRP panel joint strips, side reflective tape (red/white), amber side markers
    bmj = bmesh.new()
    for sx in (-1, 1):
        y = BOX_Y0 + 1.2
        while y < -0.3:
            bbox_bm(bmj, sx * BW - 0.006 if sx > 0 else -BW - 0.006, sx * BW + 0.006 if sx > 0 else -BW + 0.006, y - 0.025, y + 0.025,
                    BOX_Z0 + 0.12, BOX_Z1 - 0.08)
            y += 1.2
    bm_obj('box_joints', bmj, T, [M['alu']], 0.003)
    for sx in (-1, 1):
        box('box_sidetape_%d' % sx, T, M['tape'], (sx * (BW + 0.008), BOX_Y0 / 2, BOX_Z0 + 0.22), (0.006, -BOX_Y0 - 0.3, 0.05), 0.0)
        for k in range(4):
            box('box_marker_%d_%d' % (sx, k), T, M['lamp_amber'], (sx * (BW + 0.03), -0.6 - k * 2.1, BOX_Z0 + 0.06), (0.03, 0.08, 0.05), 0.008)
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
    # ---- cab (Tata Ultra / Ashok Leyland Ecomet-like cab-over): lofted rounded shell with raked, wrap-around
    # windscreen, tumblehome, rounded roof; black lower fascia, grille with a chrome bar, swept corner headlamps.
    CY0, CY1 = -9.58, -7.47
    PROF = [(1.10, 0.04, 1.215, 0.17), (1.35, 0.0, 1.225, 0.21), (1.70, 0.02, 1.222, 0.24), (1.94, 0.06, 1.212, 0.27),
            (2.02, 0.11, 1.200, 0.29), (2.40, 0.25, 1.175, 0.31), (2.80, 0.40, 1.150, 0.33), (2.90, 0.47, 1.135, 0.36),
            (2.98, 0.57, 1.105, 0.40), (3.04, 0.72, 1.050, 0.46), (3.07, 0.90, 0.960, 0.50)]
    NS, NC, NF, NB = 9, 9, 14, 6
    N = 2 * NS + 2 * NC + NF + NB

    def prof(z):
        z = min(max(z, PROF[0][0]), PROF[-1][0])
        for a, b in zip(PROF, PROF[1:]):
            if a[0] <= z <= b[0]:
                t = (z - a[0]) / (b[0] - a[0])
                return tuple(a[i] + (b[i] - a[i]) * t for i in (1, 2, 3))
        return PROF[-1][1:]

    def ring(z, grow=0.0):
        """Outline points (x, y) + outward normals at height z (fixed count N, index = same feature on every ring)."""
        f, hw, r = prof(z)
        yf = CY0 + f
        hw += grow
        r += grow
        yf -= grow
        pts = []
        for k in range(NS):                                        # right side, back -> front
            t = k / NS
            pts.append(((hw, CY1 + (yf + r - CY1) * t), (1, 0)))
        for k in range(NC):                                        # front-right corner
            a = -math.pi / 2 * k / NC
            pts.append(((hw - r + r * math.cos(a), yf + r + r * math.sin(a)), (math.cos(a), math.sin(a))))
        for k in range(NF):                                        # front, right -> left
            t = k / NF
            pts.append(((hw - r - 2 * (hw - r) * t, yf), (0, -1)))
        for k in range(NC):                                        # front-left corner
            a = -math.pi / 2 - math.pi / 2 * k / NC
            pts.append(((-(hw - r) + r * math.cos(a), yf + r + r * math.sin(a)), (math.cos(a), math.sin(a))))
        for k in range(NS):                                        # left side, front -> back
            t = k / NS
            pts.append(((-hw, yf + r + (CY1 - yf - r) * t), (-1, 0)))
        for k in range(NB):                                        # back, left -> right
            t = k / NB
            pts.append(((-hw + 2 * hw * t, CY1), (0, 1)))
        return pts

    ZS = [1.10, 1.22, 1.35, 1.52, 1.70, 1.84, 1.94, 2.02, 2.21, 2.40, 2.60, 2.80, 2.90, 2.98, 3.04, 3.07]
    bmc = bmesh.new()
    rings = [[bmc.verts.new((p[0], p[1], z)) for p, n in ring(z)] for z in ZS]
    for A, B in zip(rings, rings[1:]):
        for k in range(N):
            bmc.faces.new((A[k], A[(k + 1) % N], B[(k + 1) % N], B[k]))
    bmc.faces.new(rings[-1])
    bmc.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bmc, faces=bmc.faces[:])
    cabo = bm_obj('cab_shell', bmc, T, [M['cab']])
    cabo.data.shade_smooth()
    cabo.data.set_sharp_from_angle(angle=38 * D2R)

    def patch(name, i0, i1, z0, z1, off, mat, nz=5, bev=None, solid=0.0):
        """Panel following the shell surface: outline indices i0..i1, heights z0..z1, pushed out by off."""
        bm = bmesh.new()
        rows = []
        for j in range(nz + 1):
            z = z0 + (z1 - z0) * j / nz
            rp = ring(z, off)
            rows.append([bm.verts.new((rp[i][0][0], rp[i][0][1], z)) for i in range(i0, i1 + 1)])
        for A, B in zip(rows, rows[1:]):
            for k in range(len(A) - 1):
                bm.faces.new((A[k], A[k + 1], B[k + 1], B[k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        o = bm_obj(name, bm, T, [mat], bev)
        o.data.shade_smooth()
        if solid:
            o.modifiers.new('sol', 'SOLIDIFY').thickness = solid
        return o

    F0 = NS                    # first front-right corner index
    FL = NS + NC + NF          # first front-left corner index
    # wrap-around windscreen: gasket, glass; black lower fascia; grille + chrome bar; corner headlamps; indicators
    patch('cab_ws_gasket', F0 + 3, FL + NC - 4, 2.05, 2.86, 0.006, M['rubber'], 6)
    patch('cab_windscreen', F0 + 4, FL + NC - 5, 2.08, 2.83, 0.011, M['glass'], 6)
    patch('cab_fascia', F0 + 2, FL + NC - 3, 1.12, 1.88, 0.008, M['cab_dark'], 6, solid=0.01)
    yf = lambda z: CY0 + prof(z)[0]
    bmg = bmesh.new()
    for k in range(7):
        z = 1.32 + k * 0.064
        bbox_bm(bmg, -0.68, 0.68, -0.025, 0.0, z, z + 0.028)
    for xx in (-0.69, -0.23, 0.23, 0.69):
        bbox_bm(bmg, xx - 0.015, xx + 0.015, -0.025, 0.0, 1.30, 1.78)
    go = bm_obj('cab_grille', bmg, T, [sklib.painted_metal((0.03, 0.03, 0.032), 0.3, contrast=0.4)], 0.004)
    go.location = (0, yf(1.55) - 0.012, 0)
    box('cab_chrome_bar', T, M['stainless'], (0, yf(1.80) - 0.03, 1.80), (1.62, 0.03, 0.07), 0.012)
    box('cab_chrome_bar2', T, M['stainless'], (0, yf(1.27) - 0.03, 1.27), (1.30, 0.025, 0.035), 0.008)
    for sx in (-1, 1):
        a, b = (F0 + 1, F0 + NC + 2) if sx > 0 else (FL - 3, FL + NC - 2)
        patch('cab_headlamp_%d' % sx, a, b, 1.52, 1.74, 0.02, M['lamp'], 3)
        patch('cab_headlamp_bezel_%d' % sx, a - 1, b + 1, 1.49, 1.77, 0.014, M['stainless'], 3)
        patch('cab_indicator_%d' % sx, a, b, 1.42, 1.49, 0.02, M['lamp_amber'], 1)
        # side repeater + door shut lines, handle, grab rail, side window with vent split
        side_x = lambda z: sx * (prof(z)[1] + 0.004)
        box('cab_doorline_f%d' % sx, T, M['rubber'], (side_x(1.9), -9.18, 1.92), (0.008, 0.012, 1.55), 0.0)
        box('cab_doorline_r%d' % sx, T, M['rubber'], (side_x(1.9), -7.92, 1.92), (0.008, 0.012, 1.55), 0.0)
        box('cab_handle_%d' % sx, T, M['cab_dark'], (side_x(1.95) + sx * 0.01, -8.05, 1.95), (0.02, 0.2, 0.05), 0.008)
        box('cab_grab_%d' % sx, T, M['stainless'], (side_x(1.7) + sx * 0.03, -7.86, 1.75), (0.025, 0.025, 0.7), 0.008)
        bmw = bmesh.new()
        rows = []
        for j in range(4):
            z = 2.06 + 0.68 * j / 3
            xw = sx * (prof(z)[1] + 0.008)
            rows.append([bmw.verts.new((xw, y, z)) for y in (-9.12, -8.05)])
        for A, B in zip(rows, rows[1:]):
            bmw.faces.new((A[0], A[1], B[1], B[0]))
        bmesh.ops.recalc_face_normals(bmw, faces=bmw.faces[:])
        bm_obj('cab_sidewin_%d' % sx, bmw, T, [M['glass']], None)
        box('cab_vent_%d' % sx, T, M['rubber'], (sx * (prof(2.4)[1] + 0.012), -8.85, 2.4), (0.012, 0.025, 0.7), 0.0)
        box('cab_repeater_%d' % sx, T, M['lamp_amber'], (side_x(1.6) + sx * 0.01, -9.3, 1.6), (0.02, 0.1, 0.05), 0.01)
        for k, z in enumerate((0.48, 0.86)):
            box('cab_step_%d_%d' % (sx, k), T, M['alu'], (sx * 1.10, -7.75, z), (0.26, 0.38, 0.04), 0.008)
        box('cab_step_brk_%d' % sx, T, M['chassis'], (sx * 1.0, -7.75, 0.75), (0.04, 0.3, 0.6), 0.008)
        # mirrors on tubular arms (main + kerb)
        bmm = bmesh.new()
        cyl_bm(bmm, (0, 0, 0), 0.016, 0.36, 'X', 8)
        mo = bm_obj('cab_mirror_arm_%d' % sx, bmm, T, [M['cab_dark']], None)
        mo.location = (sx * 1.30, -9.05, 2.80)
        bmm2 = bmesh.new()
        cyl_bm(bmm2, (0, 0, 0), 0.016, 0.42, 'Z', 8)
        mo2 = bm_obj('cab_mirror_stay_%d' % sx, bmm2, T, [M['cab_dark']], None)
        mo2.location = (sx * 1.47, -9.05, 2.62)
        box('cab_mirror_head_%d' % sx, T, M['cab_dark'], (sx * 1.49, -9.08, 2.30), (0.07, 0.26, 0.44), 0.03)
        box('cab_mirror_glass_%d' % sx, T, M['mirror'], (sx * 1.49, -8.947, 2.30), (0.05, 0.005, 0.40), 0.0)
        box('cab_mirror_kerb_%d' % sx, T, M['cab_dark'], (sx * 1.46, -9.10, 1.98), (0.06, 0.2, 0.2), 0.025)
        # front wheel arch liners (black)
        bma2 = bmesh.new()
        n = 12
        vv = []
        for k in range(n + 1):
            a = math.pi * k / n
            y, z = FRONT_AX + 0.64 * math.cos(a), WR + 0.64 * math.sin(a) * 0.95
            vv.append((bma2.verts.new((sx * 0.84, y, z)), bma2.verts.new((sx * 1.235, y, z))))
        for k in range(n):
            bma2.faces.new((vv[k][0], vv[k + 1][0], vv[k + 1][1], vv[k][1]))
        o = bm_obj('cab_arch_%d' % sx, bma2, T, [M['rubber']])
        o.modifiers.new('sol', 'SOLIDIFY').thickness = 0.012
    # bumper (grey, bevelled, wraps the corners) with fog lamps, tow eye, blank yellow plate, corner steps
    bmb = bmesh.new()
    bbox_bm(bmb, -1.18, 1.18, CY0 - 0.16, CY0 + 0.12, 0.70, 1.10)
    for sx in (-1, 1):
        bbox_bm(bmb, sx * 1.04 - 0.14, sx * 1.04 + 0.14, CY0 - 0.10, CY0 + 0.35, 0.70, 1.10)
    bm_obj('cab_bumper', bmb, T, [grimed(sklib.painted_metal((0.20, 0.205, 0.21), 0.35, 0.3), 'bumper_grey', 0.3, 1.1)], 0.05)
    for sx in (-1, 1):
        cy = bmesh.new()
        cyl_bm(cy, (sx * 0.86, CY0 - 0.165, 0.86), 0.065, 0.03, 'Y', 20)
        bm_obj('cab_foglamp_%d' % sx, cy, T, [M['lamp']], 0.005)
        box('cab_bstep_%d' % sx, T, M['rubber'], (sx * 0.98, CY0 - 0.06, 0.995), (0.32, 0.2, 0.03), 0.006)
    box('cab_plate', T, M['plate'], (0, CY0 - 0.172, 0.88), (0.52, 0.012, 0.13), 0.004)
    box('cab_tow', T, M['chassis'], (0, CY0 - 0.17, 0.75), (0.18, 0.04, 0.07), 0.01)
    # sun visor, roof marker lamps, wipers
    box('cab_visor', T, M['cab_dark'], (0, yf(2.95) - 0.14, 2.95), (2.0, 0.30, 0.03), 0.01, rot=(-8 * D2R, 0, 0))
    for xx in (-0.35, 0.0, 0.35):
        box('cab_marker_%g' % xx, T, M['lamp_amber'], (xx, yf(3.06) + 0.05, 3.08), (0.12, 0.05, 0.04), 0.01)
    rake = math.atan2(0.29, 0.78)
    for sx in (-0.52, 0.34):
        o = box('cab_wiper_%g' % sx, T, M['rubber'], (sx, yf(2.13) - 0.03, 2.13), (0.80, 0.015, 0.02), 0.003)
        o.rotation_euler = (-rake, 0.10, 0)
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
DOCK2 = sklib.new_obj('TRUCK_DOCK2', None, None, loc=(-9.0, -0.45, 0))       # second reefer waiting at the west dock
sklib.instance(TRUCK, (0, 0, 0), 0.0, 'A-TRUCK-REEFER.dock2', None).parent = DOCK2
box_roof('truck_dock2_roof', S.collection, DOCK2)
rear_doors('dock2', S.collection, DOCK2, False)

# cut-away roof: hidden while the camera flies through the body, back once the camera is out over the cab
for f, h in ((1, True), (60, True), (61, False)):
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


# ======================================================================================================== yard life
def build_yard_extras():
    Y = C('A-YARD-LIFE')
    crate1 = C('A-CRATE-1', False)
    sklib.crate((0.05, 0.22, 0.55), 'crate1', crate1, 0.4)
    pal = sklib.pallet_mesh('A-PALLET.mesh')
    palc = C('A-PALLET', False)
    palc.objects.link(pal)
    # pallet loaded with 2x2x3 crates
    cp = C('A-CRATE-PALLET', False)
    sklib.instance(palc, (0, 0, 0), 0.0, 'cp_pallet', cp)
    for i, x in enumerate((-0.3, 0.3)):
        for j, y in enumerate((-0.21, 0.21)):
            for k in range(3):
                sklib.instance(crate1, (x, y, 0.145 + k * 0.245), 0.0, 'cp_c%d%d%d' % (i, j, k), cp)
    # empty pallet stacks + loaded pallets near the west docks
    rng = random.Random(12)
    for n, (x, y, h) in enumerate([(-24.0, -3.0, 7), (-24.0, -4.4, 5), (-22.4, -3.1, 9)]):
        for k in range(h):
            sklib.instance(palc, (x + rng.uniform(-0.03, 0.03), y, k * 0.145), rng.uniform(-0.03, 0.03), 'pstack_%d_%d' % (n, k), Y)
    for n, (x, y, r) in enumerate([(-12.0, -3.2, 0.02), (-12.0, -4.6, -0.04), (11.8, -3.0, 0.03), (13.3, -3.1, 0.0)]):
        sklib.instance(cp, (x, y, 0), r, 'cpal_%d' % n, Y)
    # forklift (LPG counterbalance) carrying a loaded pallet toward the west dock
    fk = C('A-FORKLIFT', False)
    body = grimed(sklib.painted_metal((0.75, 0.40, 0.03), 0.4, 0.3), 'forklift_paint', 0.0, 0.7)
    bm = bmesh.new()
    bbox_bm(bm, -0.55, 0.55, -0.55, 1.0, 0.25, 1.05, 0)
    bbox_bm(bm, -0.6, 0.6, 0.95, 1.5, 0.2, 1.2, 0)            # counterweight
    bbox_bm(bm, -0.25, 0.25, 0.35, 0.75, 1.05, 1.15, 1)        # seat base
    bbox_bm(bm, -0.24, 0.24, 0.62, 0.72, 1.15, 1.6, 1)         # seat back
    for x in (-0.5, 0.5):
        for y in (-0.45, 0.95):
            bbox_bm(bm, x - 0.03, x + 0.03, y - 0.03, y + 0.03, 1.05, 2.15, 2)
    for x in (-0.5, 0.0, 0.5):
        bbox_bm(bm, x - 0.03, x + 0.03, -0.48, 0.98, 2.12, 2.18, 2)
    bbox_bm(bm, -0.53, 0.53, -0.48, -0.42, 2.12, 2.18, 2)
    bbox_bm(bm, -0.53, 0.53, 0.92, 0.98, 2.12, 2.18, 2)
    cyl_bm(bm, (0, -0.25, 1.45), 0.16, 0.03, 'Z', 16, 1)
    for x in (-0.36, 0.36):
        bbox_bm(bm, x - 0.05, x + 0.05, -0.82, -0.66, 0.08, 2.35, 3)   # mast channels
    bbox_bm(bm, -0.45, 0.45, -0.9, -0.82, 0.1, 0.75, 3)              # carriage
    for x in (-0.3, 0.3):
        bbox_bm(bm, x - 0.06, x + 0.06, -2.05, -0.9, 0.06, 0.11, 3)    # forks
        bbox_bm(bm, x - 0.06, x + 0.06, -0.96, -0.9, 0.06, 0.7, 3)
    for x in (-0.5, 0.5):
        cyl_bm(bm, (x, -0.4, 0.3), 0.3, 0.22, 'X', 20, 4)
        cyl_bm(bm, (x, 1.15, 0.24), 0.24, 0.18, 'X', 20, 4)
    cyl_bm(bm, (0, 1.2, 1.75), 0.15, 0.7, 'Z', 16, 2)                 # LPG bottle
    bm_obj('forklift.mesh', bm, fk, [body, M['rubber'], M['chassis'], M['galv'], M['tyre']], 0.012)
    sklib.instance(cp, (0, -1.45, 0.115), 0.0, 'fk_load', fk)
    # (forklift removed in r4: read as a toy; the yard uses pallet jacks and hand-carried crates)
    # pallet jack with a loaded pallet, pulled by a worker
    pj = C('A-PALLETJACK', False)
    bm = bmesh.new()
    for y in (-0.28, 0.28):
        bbox_bm(bm, 0.0, 1.15, y - 0.08, y + 0.08, 0.03, 0.08, 0)
    bbox_bm(bm, -0.25, 0.02, -0.3, 0.3, 0.03, 0.35, 0)
    cyl_bm(bm, (-0.12, 0, 0.09), 0.09, 0.12, 'Y', 16, 1)
    bm_obj('palletjack.mesh', bm, pj, [sklib.painted_metal((0.55, 0.06, 0.04), 0.4, 0.3), M['tyre']], 0.006)
    bmh = bmesh.new()
    cyl_bm(bmh, (0, 0, 0.6), 0.02, 1.2, 'Z', 8)
    bbox_bm(bmh, -0.02, 0.02, -0.18, 0.18, 1.18, 1.22)
    ho = bm_obj('palletjack.handle', bmh, pj, [M['chassis']], None)
    ho.location = (-0.15, 0, 0.3)
    ho.rotation_euler.y = -0.75
    sklib.instance(cp, (0.6, 0, 0.09), 0.0, 'pj_load', pj)
    sklib.instance(pj, (8.6, -5.75, 0), 0.0, 'A-PALLETJACK.inst', Y)
    # parked mini-truck (Tata Ace-like) and a hatchback by the west wall
    mt = C('A-VEH-MINITRUCK', False)
    bm = bmesh.new()
    bbox_bm(bm, -0.75, 0.75, -1.9, -0.6, 0.45, 1.85, 0)
    bbox_bm(bm, -0.7, 0.7, -1.95, -1.6, 1.15, 1.75, 1)
    bbox_bm(bm, -0.8, 0.8, -0.55, 1.75, 0.6, 0.7, 2)
    for sx in (-1, 1):
        bbox_bm(bm, sx * 0.8 - 0.03, sx * 0.8 + 0.03, -0.55, 1.75, 0.7, 1.05, 2)
    bbox_bm(bm, -0.8, 0.8, 1.72, 1.78, 0.7, 1.05, 2)
    bbox_bm(bm, -0.8, 0.8, -0.58, -0.52, 0.7, 1.6, 2)
    for sx in (-0.68, 0.68):
        for y in (-1.3, 1.1):
            cyl_bm(bm, (sx, y, 0.27), 0.27, 0.17, 'X', 18, 3)
    bm_obj('minitruck.mesh', bm, mt, [grimed(sklib.painted_metal((0.80, 0.80, 0.78), 0.3, 0.2), 'mt_white', 0.1, 0.9),
                                       M['glass'], M['galv'], M['tyre']], 0.03)
    car = C('A-VEH-CAR', False)
    bm = bmesh.new()
    bbox_bm(bm, -0.85, 0.85, -1.9, 1.9, 0.3, 0.95, 0)
    bbox_bm(bm, -0.78, 0.78, -0.9, 1.2, 0.95, 1.45, 1)
    for sx in (-0.76, 0.76):
        for y in (-1.25, 1.25):
            cyl_bm(bm, (sx, y, 0.3), 0.3, 0.2, 'X', 18, 2)
    bm_obj('car.mesh', bm, car, [grimed(sklib.painted_metal((0.45, 0.46, 0.48), 0.25, 0.2), 'car_silver', 0.1, 0.7), M['glass'], M['tyre']], 0.12)
    sklib.instance(mt, (-28.0, -38.0, 0), 0.08, 'minitruck_parked', Y)
    sklib.instance(car, (-24.5, -40.5, 0), 0.03, 'car_parked', Y)
    sklib.instance(car, (-21.0, -40.3, 0), -0.05, 'car_parked2', Y)
    # puddles (wet, reflective patches) around the drains and the dock apron
    pm = decal_mat('puddle', (0.02, 0.02, 0.02), 0.95, 0.9, 0.45, 0.55, rough=0.03)
    for n, (x, y, sx, sy) in enumerate([(-6.0, -6.5, 2.4, 1.6), (6.8, -7.2, 3.0, 1.8), (-13.6, -29.5, 2.2, 1.5), (3.0, -15.3, 4.0, 1.2),
                                        (14.5, -44.0, 3.5, 2.0)]):
        decal('puddle_%d' % n, Y, pm, (x, y, 0.0035), (sx, sy), rng.uniform(0, 3))
    oil = bpy.data.materials['oil_stain']
    for n in range(10):
        decal('oil_x%d' % n, Y, oil, (rng.uniform(-28, 28), rng.uniform(-42, -6), 0.0025), (rng.uniform(0.5, 1.6), rng.uniform(0.4, 1.2)),
              rng.uniform(0, 3))


build_yard_extras()


# ======================================================================================================== lived-in yard
def grass_tuft_coll():
    c = C('A-GRASS-TUFT', False)
    rng = random.Random(5)
    verts, faces, uvs = [], [], []
    for k in range(16):
        a = rng.uniform(0, 6.28)
        L = rng.uniform(0.12, 0.38)
        lean = rng.uniform(0.15, 0.7)
        w = rng.uniform(0.008, 0.016)
        base = Vector((rng.gauss(0, 0.05), rng.gauss(0, 0.05), 0))
        d = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-d.y, d.x, 0))
        b0 = len(verts)
        for i in range(4):
            t = i / 3
            p = base + d * L * lean * t * t + Vector((0, 0, L * t * (1 - 0.35 * lean * t)))
            ww = w * (1 - t) + 0.001
            verts += [tuple(p - side * ww), tuple(p + side * ww)]
            uvs += [(0, t), (1, t)]
            if i:
                k2 = b0 + 2 * i
                faces.append((k2 - 2, k2 - 1, k2 + 1, k2))
    uv_strip_obj('grass_tuft', verts, faces, uvs, c, leaf_mat('grass_blade', (0.10, 0.16, 0.03), (0.30, 0.28, 0.09), cut=False))
    return c


def build_yard_life2():
    Y = bpy.data.collections['A-YARD-LIFE']
    rng = random.Random(81)
    stack = bpy.data.collections['A-CRATE-STACK']
    cp = bpy.data.collections['A-CRATE-PALLET']
    # crate staging area west of the hero truck: stacks of empty crates, a loaded pallet, white insulated fish boxes
    for i, (x, y, r) in enumerate([(-5.3, -8.9, 0.08), (-6.1, -8.95, -0.05), (-5.35, -9.65, 0.25), (-6.15, -9.75, 0.02),
                                   (-4.55, -9.2, -0.15), (-6.9, -9.3, 0.4)]):
        sklib.instance(stack, (x, y, 0), r, 'stage_stack_%d' % i, Y)
    sklib.instance(cp, (-6.0, -12.6, 0), 0.12, 'stage_pallet', Y)
    ib = C('A-ICEBOX', False)
    bm = bmesh.new()
    bbox_bm(bm, -0.55, 0.55, -0.38, 0.38, 0.0, 0.62)
    bbox_bm(bm, -0.57, 0.57, -0.40, 0.40, 0.62, 0.70, 1)
    bm_obj('icebox', bm, ib, [grimed(sklib.plastic((0.04, 0.17, 0.45), 0.35, name='icebox_blue'), 'icebox_g', 0.0, 0.5,
                                       (0.30, 0.27, 0.22), 0.6), sklib.plastic((0.80, 0.80, 0.77), 0.35, name='icebox_lid')], 0.035)
    for i, (x, y, r, z) in enumerate([(-3.2, -10.3, 0.1, 0.0), (-3.25, -10.32, 0.14, 0.70), (-2.0, -10.6, -0.2, 0.0),
                                      (10.2, -3.2, 0.05, 0.0), (10.25, -3.2, 0.0, 0.70)]):
        sklib.instance(ib, (x, y, z), r, 'icebox_%d' % i, Y)
    # loose crates on the ground (one tipped on its side)
    for i, (x, y, r) in enumerate([(-4.5, -12.3, 0.6), (2.6, -12.4, 1.2), (12.4, -8.6, 0.3)]):
        sklib.instance(bpy.data.collections['A-CRATE-1'], (x, y, 0), r, 'loose_crate_%d' % i, Y)
    e = sklib.instance(bpy.data.collections['A-CRATE-1'], (-2.6, -12.9, 0.2), 0.4, 'tipped_crate', Y)
    e.rotation_euler.x = math.pi / 2
    # water hose from the dock wall tap to the drain
    cu = bpy.data.curves.new('hose', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth, cu.bevel_resolution = 0.022, 2
    sp = cu.splines.new('NURBS')
    pts = [(3.45, -0.12, 1.0), (3.45, -0.25, 0.3), (3.5, -0.6, 0.024), (4.3, -1.9, 0.024), (3.7, -3.4, 0.024), (4.6, -4.6, 0.024),
           (5.6, -5.4, 0.024), (6.3, -6.2, 0.024), (6.45, -6.45, 0.024)]
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = co + (1,)
    sp.use_endpoint_u, sp.order_u = True, 3
    ho = sklib.new_obj('hose', cu, Y)
    cu.materials.append(grimed(sklib.plastic((0.05, 0.28, 0.08), 0.3, name='hose_green'), 'hose_g', 0.0, 0.05, (0.25, 0.2, 0.15), 0.5))
    box('tap', Y, M['galv'], (3.45, -0.06, 1.05), (0.06, 0.12, 0.06), 0.01)
    wet = decal_mat('wet_concrete', (0.05, 0.045, 0.04), 0.7, 1.3, 0.40, 0.62, rough=0.12)
    for i, (x, y, sx, sy, r) in enumerate([(0.9, -3.0, 1.6, 5.0, 0.1), (5.2, -5.4, 2.6, 1.6, 0.7), (-1.0, -1.6, 2.2, 1.4, 0.0)]):
        decal('wet_%d' % i, Y, wet, (x, y, 0.0032 + i * 1e-4), (sx, sy), r)
    # dust / sand drifts: along the walls and the plinth, plus broad scuffed patches in the traffic lanes
    dust = decal_mat('dust_drift', (0.40, 0.31, 0.20), 0.85, 1.1, 0.36, 0.60, rough=0.9)
    grime = decal_mat('yard_grime', (0.13, 0.115, 0.09), 0.55, 0.45, 0.33, 0.66, rough=0.8)
    for i in range(26):
        if i < 10:
            x, y, sx, sy, r = rng.uniform(-32, 32), rng.uniform(-45.5, -43.5), rng.uniform(4, 9), rng.uniform(1.5, 3), 0.0
        elif i < 16:
            x, y, sx, sy, r = rng.choice((-33, 33)) * 0.97, rng.uniform(-42, -4), rng.uniform(1.5, 3), rng.uniform(4, 9), 0.0
        else:
            x, y, sx, sy, r = rng.uniform(-28, 28), rng.uniform(-1.6, -0.9), rng.uniform(3, 6), rng.uniform(0.8, 1.4), 0.0
        decal('dust_%d' % i, Y, dust, (x, y, 0.0026 + i * 2e-5), (sx, sy), r)
    for i in range(30):
        decal('grime_%d' % i, Y, grime, (rng.uniform(-30, 30), rng.uniform(-44, -4), 0.0024 + i * 1e-5),
              (rng.uniform(5, 14), rng.uniform(4, 9)), rng.uniform(0, 3))
    # weeds in the wall base, plinth base and the yard edge
    gt = grass_tuft_coll()
    k = 0
    for (x0, y0, x1, y1, n) in ((-33.7, -45.7, 11.6, -45.7, 70), (20.4, -45.7, 33.7, -45.7, 25), (-33.7, -45.5, -33.7, -1.0, 55),
                                (33.7, -45.5, 33.7, -1.0, 55), (-29.5, -0.12, -12.0, -0.12, 22), (12.0, -0.12, 29.5, -0.12, 22)):
        for i in range(n):
            t = rng.random()
            x = x0 + (x1 - x0) * t + rng.gauss(0, 0.06)
            y = y0 + (y1 - y0) * t + rng.gauss(0, 0.06)
            sklib.instance(gt, (x, y, 0), rng.uniform(0, 6.28), 'weed_%d' % k, Y, rng.uniform(0.6, 1.5))
            k += 1
    # scraps: flattened cardboard, a torn tarp, a broom against the wall
    for i, (x, y, r) in enumerate([(14.8, -9.5, 0.4), (-9.6, -14.2, 1.1), (21.0, -20.0, 2.0)]):
        box('cardboard_%d' % i, Y, sklib.cardboard_kraft(0.5), (x, y, 0.004), (0.9, 0.6, 0.006), 0.0, rot=(0, 0, r))
    box('tarp_scrap', Y, M['tarp_blue'], (-14.6, -6.0, 0.004), (1.6, 1.1, 0.004), 0.0, rot=(0, 0, 0.5))
    bmb = bmesh.new()
    cyl_bm(bmb, (0, 0, 0.7), 0.014, 1.4, seg=8)
    bbox_bm(bmb, -0.18, 0.18, -0.03, 0.03, 0.0, 0.16, 1)
    br = bm_obj('broom', bmb, Y, [M['wood'], sklib.plastic((0.55, 0.45, 0.25), 0.5, name='broom_bristle')], 0.003)
    br.location, br.rotation_euler = (5.7, -0.3, 0.0), (0.22, 0, 0.3)


build_yard_life2()


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


def tree_low(name, seed, height=7.0, wide=1.0, mat='leaf_blob'):
    """Mid/far broadleaf (mango/neem/tamarind): short trunk + 3 limbs, 9-12 noise-displaced crown clumps forming one
    irregular canopy (not a ball on a stick)."""
    c = C(name, False)
    rng = random.Random(seed)
    bm = bmesh.new()
    th = height * 0.30
    cyl_bm(bm, (0, 0, th / 2), 0.20 * height / 7, th, seg=7, r2=0.13 * height / 7)
    for k in range(3):
        a = k * 2.1 + rng.uniform(-0.4, 0.4)
        L = height * 0.3
        d = Vector((math.cos(a) * 0.7 * wide, math.sin(a) * 0.7 * wide, 0.75)).normalized()
        q = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.09 * height / 7, radius2=0.04, depth=L,
                              matrix=Matrix.Translation(Vector((0, 0, th * 0.92)) + d * L / 2) @ q)
    bm_obj(name + '.trunk', bm, c, [M['bark']], None)
    bmc = bmesh.new()
    nclump = rng.randint(9, 12)
    for k in range(nclump):
        a = rng.uniform(0, 6.28)
        rr = rng.uniform(0.0, 0.33) * height * wide
        cc = Vector((math.cos(a) * rr, math.sin(a) * rr, height * rng.uniform(0.42, 0.74)))
        r = height * rng.uniform(0.17, 0.26) * (wide ** 0.4)
        bmesh.ops.create_icosphere(bmc, subdivisions=2, radius=r, matrix=Matrix.Translation(cc) @ Matrix.Diagonal((1, 1, 0.72, 1)))
    off = Vector((seed * 3.1, seed * 1.7, 0.0))
    for v in bmc.verts:
        p = v.co / height * 2.6 + off
        v.co += Vector((mnoise.noise(p), mnoise.noise(p + Vector((5.2, 1.3, 0))), mnoise.noise(p + Vector((2.1, 7.7, 0))))) * height * 0.09
    cr = bm_obj(name + '.crown', bmc, c, [M[mat]], None, uv=False)
    cr.data.shade_smooth()
    return c


def tree_casuarina(name, seed, height=14.0):
    """Coastal casuarina: straight thin trunk, narrow ragged conical crown in lumps (shelter belts behind the beach)."""
    c = C(name, False)
    rng = random.Random(seed)
    bm = bmesh.new()
    cyl_bm(bm, (0, 0, height * 0.45), 0.13, height * 0.9, seg=6, r2=0.05)
    bm_obj(name + '.trunk', bm, c, [M['bark']], None)
    bmc = bmesh.new()
    for k in range(9):
        t = k / 8
        z = height * (0.28 + 0.66 * t)
        r = height * (0.16 * (1 - t) + 0.04) * rng.uniform(0.8, 1.2)
        cc = Vector((rng.gauss(0, 0.25), rng.gauss(0, 0.25), z))
        bmesh.ops.create_icosphere(bmc, subdivisions=1, radius=r, matrix=Matrix.Translation(cc) @ Matrix.Diagonal((1, 1, 1.5, 1)))
    for v in bmc.verts:
        p = v.co * 0.5 + Vector((seed, 0, 0))
        v.co += Vector((mnoise.noise(p), mnoise.noise(p + Vector((4, 0, 0))), 0)) * height * 0.04
    cr = bm_obj(name + '.crown', bmc, c, [M['leaf_casuarina']], None, uv=False)
    cr.data.shade_smooth()
    return c


M['leaf_mango_blob'] = leaf_mat('leaf_mango_blob', (0.014, 0.042, 0.012), (0.035, 0.08, 0.022), cut=False)
M['leaf_casuarina'] = leaf_mat('leaf_casuarina', (0.035, 0.06, 0.03), (0.07, 0.10, 0.05), cut=False)
from mathutils import noise as mnoise  # noqa: E402
TREES_HI = [tree_neem('A-VEG-TREE-neem%d' % i, 10 + i, height=h) for i, h in enumerate((6.5, 8.5, 7.5))]
PALMS = [tree_palm('A-VEG-PALM-%d' % i, 40 + i, height=h) for i, h in enumerate((10.0, 12.5, 8.5, 14.0))]
TREES_LO = [tree_low('A-VEG-TREE-low%d' % i, 70 + i, height=h, wide=w) for i, (h, w) in enumerate(((6.0, 1.0), (8.0, 1.15), (9.5, 0.9)))]
MANGO = [tree_low('A-VEG-TREE-mango%d' % i, 90 + i, height=h, wide=1.35, mat='leaf_mango_blob') for i, h in enumerate((7.0, 8.5, 9.5))]
CASUA = [tree_casuarina('A-VEG-CASUARINA-%d' % i, 120 + i, height=h) for i, h in enumerate((13.0, 15.5, 17.0))]


# ======================================================================================================== landscape
ENV = C('A-ENV')
COAST = C('BRIDGE_COAST')
ROAD_Y = -60.0


def coast_x(y):
    return COAST0 + 0.5 * y


def coast_dist(x, y):
    return (x - coast_x(y)) * 0.894


def land_h(x, y):
    """Rolling inland relief (0-35 m), flat along the road, around the plant and on the coastal pond plain."""
    m = min(1.0, max(0.0, (abs(y - ROAD_Y) - 25.0) / 120.0))
    m *= min(1.0, max(0.0, (math.hypot(x, y + 20.0) - 90.0) / 150.0))
    m *= min(1.0, max(0.0, (coast_x(y) - 860.0 - x) / 350.0))
    h = (mnoise.fractal(Vector((x / 550.0, y / 550.0, 2.1)), 0.7, 2.0, 4) * 0.5 + 0.5) * 26.0
    h += 10.0 * mnoise.noise(Vector((x / 170.0, y / 170.0, 4.2)))
    return max(0.0, h) * m


def tree_at(src, x, y, rz, name, coll, s, rng, lean=0.05):
    e = sklib.instance(src, (x, y, land_h(x, y) - 0.15), rz, name, coll, s)
    e.rotation_euler.x, e.rotation_euler.y = rng.gauss(0, lean), rng.gauss(0, lean)
    return e


def sway(e, rng, amount=0.018):
    """Wind sway on a tree instance (noise on its tilt, own phase)."""
    for i in (0, 1):
        e.keyframe_insert('rotation_euler', index=i, frame=1)
    for fc in sklib._fcurves(e):
        if fc.data_path == 'rotation_euler' and fc.array_index in (0, 1):
            m = fc.modifiers.new('NOISE')
            m.strength, m.scale, m.phase = amount, rng.uniform(28, 45), rng.uniform(0, 100)


POND_BLOCKS = []      # (cx, cy, half_x, half_y, angle) for scatter exclusion


def in_ponds(x, y, pad=8.0):
    for cx, cy, hx, hy, a in POND_BLOCKS:
        dx, dy = x - cx, y - cy
        u = dx * math.cos(a) + dy * math.sin(a)
        v = -dx * math.sin(a) + dy * math.cos(a)
        if abs(u) < hx + pad and abs(v) < hy + pad:
            return True
    return False


def strip(name, coll, mat, d0, d1, z0, z1, y0=-4000.0, y1=6000.0, n=60):
    """Ribbon parallel to the coast between signed coast distances d0..d1 (m) at heights z0..z1."""
    verts, faces = [], []
    for i in range(n + 1):
        y = y0 + (y1 - y0) * i / n
        for d, z in ((d0, z0), (d1, z1)):
            verts.append((coast_x(y) + d / 0.894, y, z))
        if i:
            k = 2 * i
            faces.append((k - 2, k - 1, k + 1, k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    ob = sklib.new_obj(name, me, coll)
    me.materials.append(mat)
    return ob


def boat_coll(name, hull_col, seed):
    """Vizag beach fishing boat (FRP, ~8 m): pointed hull with sheer, painted band, small deck house aft."""
    c = C(name, False)
    rng = random.Random(seed)
    bm = bmesh.new()
    L, Wd, H = 8.0, 1.6, 0.9
    secs = []
    for i in range(9):
        t = i / 8
        w = Wd / 2 * (math.sin(math.pi * min(1.0, 0.15 + t * 0.95)) ** 0.6) if t < 0.95 else 0.02
        zt = H + 0.25 * (t ** 3)
        y = -L / 2 + L * t
        secs.append([bm.verts.new(p) for p in ((-w, y, zt), (-w * 0.55, y, 0.15), (0, y, 0.0), (w * 0.55, y, 0.15), (w, y, zt))])
    for A, B in zip(secs, secs[1:]):
        for j in range(4):
            bm.faces.new((A[j], A[j + 1], B[j + 1], B[j]))
    bm.faces.new([secs[0][j] for j in range(5)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm_obj(name + '.hull', bm, c, [grimed(sklib.painted_metal(hull_col, 0.4, 0.4), name + '_paint', 0.0, 0.6, (0.3, 0.27, 0.2), 0.6)])
    box(name + '.house', c, M['wall'], (0, -L * 0.28, H + 0.5), (1.1, 1.3, 1.0), 0.03)
    box(name + '.tarp', c, M['tarp_blue'] if rng.random() < 0.5 else M['tarp_black'], (0, L * 0.05, H + 0.05), (1.3, 2.6, 0.1), 0.02)
    return c


def build_land():
    # land with rolling relief (flat at the road, plant and pond plain), slightly below yard level
    bm = bmesh.new()
    grid_bm(bm, -4000, 4500, -4000, 6000, 220, 260, -0.03)
    for v in bm.verts:
        v.co.z = land_h(v.co.x, v.co.y) - 0.03
    lo = bm_obj('land', bm, COAST, [M['land']], uv=False)
    lo.data.shade_smooth()
    # sea (z 0.1) east of the NE-SW coastline; sloping beach strip (waterline ~ d = +4 m)
    verts = [(coast_x(-4000) - 30, -4000, 0.1), (9000, -4000, 0.1), (9000, 6000, 0.1), (coast_x(6000) - 30, 6000, 0.1)]
    me = bpy.data.meshes.new('sea')
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    sklib.new_obj('A-ENV-SEA', me, COAST)
    me.materials.append(M['sea'])
    strip('A-ENV-BEACH', COAST, M['beach'], -72.0, 15.0, 0.30, 0.07)
    # hills north + west (displaced grid)
    for name, (x0, x1, y0, y1, hmax) in {'hills_n': (-4000, 2600, 1600, 5600, 380), 'hills_w': (-4000, -1200, -3000, 1800, 260)}.items():
        nx, ny = 90, 60
        bm = bmesh.new()
        grid_bm(bm, x0, x1, y0, y1, nx, ny)
        for v in bm.verts:
            x, y = v.co.x, v.co.y
            edge = min(1.0, max(0.0, (y - y0) / 900.0)) if name == 'hills_n' else min(1.0, max(0.0, (x1 - x) / 700.0))
            h = mnoise.fractal(Vector((x / 1400.0, y / 1400.0, 0.3)), 0.6, 2.1, 5) * 0.5 + 0.55
            h += 0.5 * abs(mnoise.noise(Vector((x / 700.0, y / 700.0, 1.7))))
            v.co.z = max(0.0, h) * hmax * edge - 2.0
        ob = bm_obj(name, bm, COAST, [M['hill']], uv=False)
        ob.data.shade_smooth()
    # pond variants (4 water colours + drained), 60 x 40 m water, 2.5-4.7 m earthen bunds
    PV = []
    for i, wm in enumerate(PONDW + [M['pond_mud']]):
        cc = C('A-POND-%d' % i, False)
        bm = bmesh.new()
        grid_bm(bm, -30.0, 30.0, -20.0, 20.0)
        w = bm_obj(cc.name + '.water', bm, cc, [wm], uv=(i == 4))
        w.location.z = 0.12 if i < 4 else -0.15
        bmb = bmesh.new()
        for (xa, xb, ya, yb) in ((-33.2, 33.2, -23.2, -18.5), (-33.2, 33.2, 18.5, 23.2), (-33.2, -28.5, -18.5, 18.5), (28.5, 33.2, -18.5, 18.5)):
            bbox_bm(bmb, xa, xb, ya, yb, -0.05, 0.9)
        bm_obj(cc.name + '.bund', bmb, cc, [M['bund']], 0.6, smooth_angle=60)
        PV.append(cc)
    # pond blocks: each farm block has its own pond size and orientation; tracks/canals between blocks
    rng = random.Random(9)
    k = 0
    for j in range(7):
        for i in range(3):
            if rng.random() < 0.12:
                continue
            cy = 45.0 + j * 235.0 + rng.uniform(-25, 25)
            cx = coast_x(cy) - (255.0 + i * 235.0) / 0.894 + rng.uniform(-20, 20)
            a = rng.uniform(-0.18, 0.18)
            sx, sy = rng.uniform(0.62, 1.05), rng.uniform(0.7, 1.15)
            px, py = 66.4 * sx, 46.4 * sy
            nx, ny = max(1, int(200 / px)), max(1, int(200 / py))
            ca, sa = math.cos(a), math.sin(a)
            Rb = max(nx * px, ny * py) * 0.62
            if cy - Rb < ROAD_Y + 25.0:                    # keep clear of the road: slide the block north
                cy = ROAD_Y + 25.0 + Rb
                cx = coast_x(cy) - (255.0 + i * 235.0) / 0.894
            if cx - Rb < 90.0 and cy - Rb < 70.0:          # and of the plant yard: slide it east
                cx = 90.0 + Rb
            if any(math.hypot(cx - q[0], cy - q[1]) < Rb + max(q[2], q[3]) * 1.24 for q in POND_BLOCKS):
                continue
            POND_BLOCKS.append((cx, cy, nx * px / 2, ny * py / 2, a))
            for u in range(nx):
                for v in range(ny):
                    if rng.random() < 0.07:
                        continue
                    lx, ly = (u - (nx - 1) / 2) * px, (v - (ny - 1) / 2) * py
                    e = sklib.instance(PV[4] if rng.random() < 0.08 else PV[rng.randrange(4)],
                                       (cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, 0), a, 'pond_%d' % k, COAST)
                    e.scale = (sx, sy, 1.0)
                    k += 1
    print('ponds', k)
    # casuarina shelter belt behind the beach, fishing boats drawn up on the sand and out at sea
    rng = random.Random(14)
    n = 0
    y = -1800.0
    while y < 2600:
        for row in range(5):
            d = -78.0 - row * 9.0 + rng.uniform(-3, 3)
            if rng.random() < 0.12:
                continue
            yy = y + rng.uniform(-3, 3)
            sklib.instance(CASUA[rng.randrange(3)], (coast_x(yy) + d / 0.894, yy, 0.0), rng.uniform(0, 6.28), 'casua_%d' % n, COAST,
                           rng.uniform(0.8, 1.2))
            n += 1
        y += rng.uniform(6.0, 9.0)
    print('casuarinas', n)
    boats = [boat_coll('A-BOAT-%d' % i, c, i) for i, c in enumerate([(0.05, 0.20, 0.50), (0.55, 0.06, 0.04), (0.75, 0.75, 0.72),
                                                                       (0.06, 0.35, 0.30)])]
    for i in range(40):
        yy = rng.uniform(-1500, 1500)
        d = rng.uniform(-48, -22)
        e = sklib.instance(boats[i % 4], (coast_x(yy) + d / 0.894, yy, 0.30 - (d + 72.0) / 87.0 * 0.23), math.atan2(-0.5, 1.0) + math.pi / 2 + rng.uniform(-0.3, 0.3),
                           'beach_boat_%d' % i, COAST)
        e.rotation_euler.y = rng.uniform(-0.1, 0.1)
    wake = decal_mat('wake_foam', (0.85, 0.87, 0.87), 0.9, 0.6, 0.35, 0.6, stretch=(1, 0.3, 1), rough=0.6)
    for i, (yy, d, hd) in enumerate([(-300, 260, 0.4), (-60, 520, 2.6), (240, 380, 1.2), (-520, 820, -0.6), (90, 1150, 3.0),
                                     (420, 700, 0.1), (-150, 1500, 1.9)]):
        x = coast_x(yy) + d / 0.894
        sklib.instance(boats[i % 4], (x, yy, -0.3), hd, 'sea_boat_%d' % i, COAST)
        dv = Vector((-math.sin(hd), math.cos(hd), 0))      # boats face -Y locally; wake trails behind (+Y local)
        decal('sea_wake_%d' % i, COAST, wake, (x + dv.x * 22, yy + dv.y * 22, 0.12), (5.0, 40.0), hd)


build_land()


def house_coll(name, wall_col, roof, seed):
    c = C(name, False)
    rng = random.Random(seed)
    w, d, h = rng.uniform(6, 9), rng.uniform(5, 8), rng.uniform(3.0, 3.4)
    bm = bmesh.new()
    bbox_bm(bm, -w / 2, w / 2, -d / 2, d / 2, 0, h)
    if rng.random() < 0.5:      # second floor on part of it
        bbox_bm(bm, -w / 2, 0.5, -d / 2, d / 2, h, 2 * h)
    hw = bm_obj(name + '.walls', bm, c, [grimed(sklib.pbr('house_' + name, 'painted_plaster_wall', tint=wall_col, wear=0.4), 'house_g_' + name, 0, 1.2,
                                                  (0.35, 0.28, 0.2), 0.6)], 0.03)
    if roof == 'tile':
        bmr = bmesh.new()
        vs = [bmr.verts.new(p) for p in [(-w / 2 - 0.4, -d / 2 - 0.4, h), (w / 2 + 0.4, -d / 2 - 0.4, h), (w / 2 + 0.4, d / 2 + 0.4, h),
                                          (-w / 2 - 0.4, d / 2 + 0.4, h), (-w / 2 - 0.4, 0, h + 1.6), (w / 2 + 0.4, 0, h + 1.6)]]
        for f in ((0, 1, 5, 4), (3, 4, 5, 2), (0, 4, 3), (1, 2, 5)):
            bmr.faces.new([vs[i] for i in f])
        bm_obj(name + '.roof', bmr, c, [sklib.pbr('roof_tile', 'red_brick_03', tint=(0.45, 0.16, 0.08), wear=0.4, scale=0.5)])
    else:
        top = 2 * h if False else h
        box(name + '.parapet', c, M['concrete'], (0, 0, h + 0.1), (w + 0.1, d + 0.1, 0.2), 0.02)
    return c


def build_villages():
    V = C('A-VILLAGES')
    cols = [(0.86, 0.84, 0.78), (0.82, 0.74, 0.52), (0.78, 0.62, 0.62), (0.62, 0.72, 0.78), (0.70, 0.78, 0.62)]
    houses = [house_coll('A-HOUSE-%d' % i, cols[i % 5], 'tile' if i % 3 == 0 else 'flat', 50 + i) for i in range(8)]
    rng = random.Random(61)
    centres = [(-380, 260), (300, 470), (-220, -520), (420, -380), (-900, 700), (120, -900), (-1300, -200), (-60, -1350), (-600, 1300), (420, 1500)]
    n = 0
    for cx, cy in centres:
        ang = rng.uniform(0, 1.57)
        for k in range(rng.randint(25, 45)):
            x = cx + rng.gauss(0, 55)
            y = cy + rng.gauss(0, 55)
            if abs(y - ROAD_Y) < 14 or x > coast_x(y) - 150 or in_ponds(x, y, 12.0):
                continue
            e = sklib.instance(houses[rng.randrange(8)], (x, y, land_h(x, y) - 0.1), ang + rng.choice((0, 1.5708)) + rng.uniform(-0.08, 0.08),
                               'house_%d' % n, V)
            n += 1
        for k in range(30):     # village palms / mango trees
            x, y = cx + rng.gauss(0, 80), cy + rng.gauss(0, 80)
            if abs(y - ROAD_Y) < 9 or x > coast_x(y) - 140 or in_ponds(x, y):
                continue
            tree_at((PALMS + TREES_LO)[rng.randrange(6)], x, y, rng.uniform(0, 6.28), 'vtree_%d_%d' % (n, k), V, rng.uniform(0.8, 1.3), rng, 0.06)
    print('houses', n)


build_villages()


def build_road():
    R = C('A-ENV-ROAD')
    x0, x1 = -3000.0, coast_x(ROAD_Y) - 60.0
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
                if -36 < x < 110 and y > -80:     # clear of the yard and of the camera climb
                    continue
                if x > coast_x(y) - 140 or in_ponds(x, y):
                    continue
                kind = PALMS if rng.random() < 0.35 else TREES_HI
                e = tree_at(kind[rng.randrange(3)], x + rng.uniform(-3, 3), y, rng.uniform(0, 6.28), 'rtree_%d' % k, T,
                            rng.uniform(0.7, 1.35), rng, 0.07 if kind is PALMS else 0.03)
                if -150 < x < 350:
                    sway(e, rng)
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
    px = list(range(-480, int(coast_x(ROAD_Y)) - 100, 42))
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
    # far vegetation: orchards in rows (mango / coconut), natural clumps, singles along field edges
    rng3 = random.Random(77)
    FT = C('FAR_TREES')
    nfar = 0

    def ok(x, y):
        if x > coast_x(y) - 140 or (-45 < x < 45 and -55 < y < 45) or abs(y - ROAD_Y) < 8:
            return False
        if min(math.hypot(x - a_, y - b_) for a_, b_ in ((17, -30), (40, -62), (70, -78), (95, -90))) < 60:   # no trees under the low climb
            return False
        return not in_ponds(x, y)

    for g in range(330):
        cx, cy = rng3.uniform(-1700, coast_x(0) - 150), rng3.uniform(-1700, 2300)
        if not ok(cx, cy):
            continue
        kind = rng3.random()
        R = rng3.uniform(25, 75)
        near_path = min(math.hypot(cx - px_, cy - py_) for px_, py_ in ((40, -62), (95, -90), (140, -100), (190, -106), (260, -110))) < 280
        if near_path:
            kind = 0.5
        if kind < 0.65:          # planted orchard: rows
            sp = rng3.uniform(7.5, 10.5)
            a = rng3.uniform(0, 3.14)
            src = MANGO if kind < 0.35 else PALMS
            n = int(R / sp)
            for i in range(-n, n + 1):
                for j in range(-n, n + 1):
                    lx, ly = i * sp, j * sp
                    if lx * lx + ly * ly > R * R * (0.8 + 0.4 * mnoise.noise(Vector((i * 0.3, j * 0.3, g)))) or rng3.random() < 0.08:
                        continue
                    x = cx + lx * math.cos(a) - ly * math.sin(a) + rng3.gauss(0, 0.5)
                    y = cy + lx * math.sin(a) + ly * math.cos(a) + rng3.gauss(0, 0.5)
                    if ok(x, y):
                        tree_at(src[rng3.randrange(len(src))], x, y, rng3.uniform(0, 6.28), 'grove_%d' % nfar, FT, rng3.uniform(0.85, 1.15), rng3,
                                0.05 if src is PALMS else 0.02)
                        nfar += 1
        else:                    # natural clump of mixed trees
            for i in range(int(R * 0.9)):
                x, y = cx + rng3.gauss(0, R / 2.2), cy + rng3.gauss(0, R / 2.2)
                if ok(x, y):
                    src = (TREES_LO + MANGO + PALMS)[rng3.randrange(10)]
                    tree_at(src, x, y, rng3.uniform(0, 6.28), 'grove_%d' % nfar, FT, rng3.uniform(0.7, 1.3), rng3, 0.05)
                    nfar += 1
    for i in range(5000):        # singles and pairs along bunds/fields
        x, y = rng3.uniform(-1700, coast_x(0)), rng3.uniform(-1700, 2300)
        if ok(x, y) and mnoise.noise(Vector((x / 260.0, y / 260.0, 0.5))) > -0.25:
            near_path = min(math.hypot(x - px_, y - py_) for px_, py_ in ((40, -62), (95, -90), (140, -100), (190, -106), (260, -110))) < 220
            src = PALMS[rng3.randrange(4)] if near_path else (TREES_LO + PALMS + MANGO)[rng3.randrange(10)]
            tree_at(src, x, y, rng3.uniform(0, 6.28), 'single_%d' % i, FT, rng3.uniform(0.7, 1.35), rng3, 0.05)
            nfar += 1
    print('far trees', nfar)
    # yard trees along the walls
    for i, (xx, yy) in enumerate([(-31.5, -30.0), (-31.5, -14.0), (-20.0, -43.5)]):     # clear of the camera climb (SE corner)
        sway(tree_at(TREES_HI[i % 3], xx, yy, i * 1.3, 'ytree_%d' % i, T, 0.9 + 0.1 * (i % 3), rng, 0.04), rng)


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


def two_wheeler(name, paint, shirt, scooter=False, with_rider=True):
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
    if with_rider:
        rider(bm, 0.25, 0.82, 5, 6, 7, 8)
    else:   # parked: side stand lean handled by the instance tilt
        bbox_bm(bm, -0.1, 0.1, 0.62, 0.72, 0.84, 0.9, 2)
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
# staff two-wheelers parked under the canopy east of the hero dock (on side stands)
PARKED_2W = [two_wheeler('A-VEH-2W-park-%d' % i, (M['bike_red'], M['bike_blue'], M['bike_black'], M['bike_black'])[i], SHIRTS[0],
                         i == 1, with_rider=False) for i in range(4)]
for i, x in enumerate((16.2, 17.1, 18.0, 18.9, 22.4, 23.3)):
    e = sklib.instance(PARKED_2W[i % 4], (x, -2.6, 0), 0.25 + 0.06 * (i % 3), 'parked_2w_%d' % i, YARD)
    e.rotation_euler.y = -0.12
BUS = bus()
# left-hand traffic: eastbound (+X) keeps to the north lane (y > road centre), westbound to the south lane.
# vehicle meshes face -Y; rot_z = +90 deg -> facing +X (east), -90 -> facing -X (west).
LANE_E, LANE_W = ROAD_Y + 1.75, ROAD_Y - 1.75
movers = [(BIKES[0], LANE_E + 0.9, math.pi / 2, -30.0, 0.55), (BIKES[1], LANE_E + 0.7, math.pi / 2, -62.0, 0.45),
          (BIKES[2], LANE_W - 0.8, -math.pi / 2, 175.0, -0.5), (AUTO, LANE_E, math.pi / 2, 5.0, 0.36),
          (BUS, LANE_W, -math.pi / 2, 420.0, -0.6), (TRUCK, LANE_E - 0.1, math.pi / 2, 250.0, 0.42),
          (AUTO, LANE_W, -math.pi / 2, 640.0, -0.35), (BIKES[0], LANE_W - 0.8, -math.pi / 2, 470.0, -0.5),
          (BUS, LANE_E, math.pi / 2, 560.0, 0.5), (BIKES[2], LANE_E + 0.9, math.pi / 2, 760.0, 0.5),
          (AUTO, LANE_E, math.pi / 2, 880.0, 0.32), (BIKES[1], LANE_W - 0.7, -math.pi / 2, 950.0, -0.45)]
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
people.animate_cycle(sig, 'wave', 1, 216, phase=0.2, amount=1.8)
dock = people.make_person('P-YARD-2-dockhand', sex='male', age=0.25, skin_tone=0.8, body={'weight': 0.45},
                          outfit='tshirt_shorts', pose='pull_rope', location=(2.0, -1.3, 0), rotation_z=-90 * D2R, seed=8)
people.animate_cycle(dock, 'pull', 1, 216, phase=0.6)
guard = people.make_person('P-YARD-3-guard', sex='male', age=0.6, skin_tone=0.55, outfit='formal_shirt_lanyard',
                           pose='stand', location=(26.6, -44.2, 0), rotation_z=200 * D2R, seed=12)
people.animate_cycle(guard, 'work', 1, 216, phase=0.4, amount=0.4)
porter = people.make_person('P-YARD-4-porter', sex='male', age=0.45, skin_tone=0.9, body={'weight': 0.4},
                            outfit='tshirt_lungi', pose='carry', location=(27.2, -6.4, 0), rotation_z=120 * D2R, seed=21)
people.animate_cycle(porter, 'work', 1, 216, phase=0.7, amount=0.5)
fl_op = people.make_person('P-YARD-5-checker', sex='female', age=0.3, skin_tone=0.6, outfit='hivis_helmet', pose='stand',
                           location=(-3.6, -11.2, 0), rotation_z=200 * D2R, seed=31)
people.animate_cycle(fl_op, 'work', 1, 216, phase=0.1, amount=0.6)
jack_w = people.make_person('P-YARD-6-jack', sex='male', age=0.5, skin_tone=0.75, body={'weight': 0.6}, outfit='tshirt_lungi',
                            pose='pull_rope', location=(7.05, -5.75, 0), rotation_z=90 * D2R, seed=44)
people.animate_cycle(jack_w, 'pull', 1, 216, phase=0.35)
carrier = people.make_person('P-YARD-7-carrier', sex='male', age=0.3, skin_tone=0.85, body={'weight': 0.35}, outfit='tshirt_shorts',
                             pose='carry', location=(-3.9, -8.3, 0), rotation_z=95 * D2R, seed=52)
people.animate_cycle(carrier, 'work', 1, 216, phase=0.55, amount=0.5)
stacker = people.make_person('P-YARD-8-stacker', sex='male', age=0.4, skin_tone=0.7, body={'weight': 0.5}, outfit='cotton_shirt_lungi_towel',
                             pose='crouch', location=(-5.75, -11.0, 0), rotation_z=170 * D2R, seed=63)
people.animate_cycle(stacker, 'work', 1, 216, phase=0.85, amount=0.6)
superv = people.make_person('P-YARD-9-supervisor', sex='male', age=0.55, skin_tone=0.5, body={'weight': 0.65}, outfit='formal_shirt_lanyard',
                            pose='stand', location=(11.2, -11.2, 0), rotation_z=145 * D2R, seed=74)
people.animate_cycle(superv, 'work', 1, 216, phase=0.25, amount=0.4)
for p in (sig, dock, guard, porter, fl_op, jack_w, carrier, stacker, superv):
    for o in [p] + list(p.children_recursive):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        PEOPLE.objects.link(o)


# ======================================================================================================== per-shot visibility
def hide_keys(obs, keys):
    """keys: [(frame, hidden)] -> constant-interpolated hide_render/hide_viewport keys on every object."""
    for o in obs:
        for f, h in keys:
            o.hide_render = o.hide_viewport = h
            o.keyframe_insert('hide_render', frame=f)
            o.keyframe_insert('hide_viewport', frame=f)
        for fc in sklib._fcurves(o):
            if fc.data_path in ('hide_render', 'hide_viewport'):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'CONSTANT'


# aerial-only content (far groves, villages) lives in one nested collection instance: off while the camera is in the yard
AER = C('AERIAL', False)
for cn in ('FAR_TREES', 'A-VILLAGES'):
    cc = bpy.data.collections[cn]
    S.collection.children.unlink(cc)
    AER.children.link(cc)
AER_I = sklib.instance(AER, (0, 0, 0), 0.0, 'AERIAL_INST', None)
hide_keys([AER_I], [(1, True), (97, False)])
# yard-only content off once the camera has climbed away: cargo, dock bay interior, people
hide_keys(list(bpy.data.collections['CARGO'].all_objects), [(1, False), (62, True)])
hide_keys([o for o in bpy.data.collections['A-PLANT-EXT'].objects if o.name.startswith(('bay_', 'leveller'))], [(1, False), (70, True)])
hide_keys(list(PEOPLE.all_objects), [(1, False), (178, True)])


# ======================================================================================================== camera
cam = sklib.camera('CAM', 28.0, (0, 3.0, 2.75), (0, -10, 2.35))
cam.data.clip_end = 12000.0
keys = [
    (1, (0.0, 3.0, 2.75), (0.0, -10.0, 2.35), 28.0),          # BRIDGE_DOCK
    (24, (0.0, -1.6, 2.9), (0.0, -10.0, 1.7), None),
    (44, (0.0, -5.4, 3.95), (0.2, -10.5, 1.3), None),
    (58, (0.3, -7.0, 6.4), (0.3, -10.8, 1.6), None),       # risen out of the cut-away roof, cab below/ahead
    (66, (3.4, -9.4, 6.3), (0.3, -10.6, 1.7), None),       # orbit to the right around the cab front
    (76, (5.8, -13.4, 6.2), (0.2, -8.8, 1.9), None),
    (90, (8.5, -18.5, 6.2), (0.5, -5.5, 1.9), None),
    (120, (17.0, -30.0, 11.0), (0.0, -5.5, 1.8), 28.0),
    (150, (40.0, -62.0, 30.0), (18.0, -2.0, 0.0), None),
    (175, (95.0, -90.0, 85.0), (145.0, 48.0, 0.0), None),
    (200, (190.0, -106.0, 190.0), (443.0, 40.0, 0.0), None),
    (216, (260.0, -110.0, 300.0), (260.0 + 300.0 / math.tan(35 * D2R), -110.0, 0.0), 24.0),   # BRIDGE_COAST
]
sklib.camera_path(cam, keys)
# art r4: yard/aerial +0.2 EV (the warm grade reads ~10 luma darker); f1 keeps BRIDGE_DOCK -0.3
EXPO_KEYS = ((1, -0.3), (18, 0.6), (60, 0.35), (110, 0.35), (190, 0.3), (216, 0.2))   # f1 stays BRIDGE_DOCK -0.3; r5 brighter (mean >= 95)
for f, v in ((1, 0.03), (100, 0.03), (130, 0.5)):
    cam.data.clip_start = v
    cam.data.keyframe_insert('clip_start', frame=f)
for f, v in EXPO_KEYS:
    S.view_settings.exposure = v
    S.view_settings.keyframe_insert('exposure', frame=f)

# keep the final aerial clean: the yard/plant are behind the camera at f216; nothing else needed.
sklib.finish('truck', 'ext')
# finish() resets exposure to 0; the keyframes above still drive it (re-key to be explicit after finish)
for f, v in EXPO_KEYS:
    S.view_settings.exposure = v
    S.view_settings.keyframe_insert('exposure', frame=f)
# art pass (issue #75): AgX Punchy + morning haze + grade (lift field green, gain sun gold); finish() reset the view/compositor
# look.apply's world-volume fog absorbs the whole sky + sun in EEVEE (art r1: frames black, same as sea r1), so the morning
# haze #e8d2b0 comes from the per-material distance haze (HAZE_COL in haze()) and only the view + grade come from look.
look.view(S, 'AgX - Punchy')
# art r5 (COLOR_SCRIPT §3 updated): complementary grade, cool teal-blue shadows vs warm key highlights (r4 gold lift read as a sepia wash)
look.grade(S, lift='#2f6f8a', gain='#ffc98a', sat=1.14, contrast=2.0, bloom=0.15, vignette=0.10, lift_amt=0.012, gain_amt=0.06)   # r5b: 0.025 lift went teal over the whole frame; r6: lead raised the gain cap to 0.06 for the gold
for f, v in EXPO_KEYS:
    S.view_settings.exposure = v
    S.view_settings.keyframe_insert('exposure', frame=f)
# fast flight (dock -> 300 m aerial in 9 s): a 108 deg shutter keeps the yard and the coast readable
S.render.motion_blur_shutter = 0.3
for f, v in ((1, 0.3), (150, 0.3), (172, 0.15), (216, 0.15)):   # shorter shutter on the fast climb to the aerial
    S.render.motion_blur_shutter = v
    S.render.keyframe_insert('motion_blur_shutter', frame=f)
S.eevee.taa_render_samples = 32      # 16 vs 64 samples measured identical on the blurred flight frames; 32 for margin
S.eevee.shadow_resolution_scale = 0.5   # A/B at f90: no visible change, ~-30 % frame time on the shared GPU
bpy.ops.wm.save_mainfile()
print('TRUCK BUILD OK')
