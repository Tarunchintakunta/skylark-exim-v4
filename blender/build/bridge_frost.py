"""BRIDGE_FROST (table f216 -> reefer f1): shared builder. See assets-src/blender/BRIDGE_FROST.md.

    sys.path.insert(0, REPO + '/assets-src/blender/build'); import bridge_frost
    coll = bridge_frost.build()          # unlinked collection 'BRIDGE_FROST' (patch + light), origin = patch centre
    sklib.instance(coll, loc, 0.0, 'BRIDGE_FROST_inst')   # camera: loc + (0,0,0.12), rotation (0,0,0), lens 100, f/2.8
"""
import math

import bmesh
import bpy

import sklib
from sklib import _n, _l, _math, _mix, _maprange, _noise

LIGHT_ELEV_DEG = 25.0      # grazing key so crystal facets cast micro-shadows and sparkle
LIGHT_AZ_DEG = 200.0       # light comes from -X/-Y side (azimuth measured like sklib: 0 = +Y, 90 = +X)


def material(p=None):
    """M-FROST-BRIDGE: greyish frosted poly bag + blue-white hoar-frost crystals.
    Crystal mask = feathery voronoi ridges (distance-to-edge) + fine fuzz, clumped by a density noise; bump from the
    mask x per-facet random heights; crystals glossy (sparkle), bag satin."""
    p = dict(dict(ridge=230.0, facet=900.0, fuzz=420.0, clump=40.0, bump=0.0025), **(p or {}))
    old = bpy.data.materials.get('M-FROST-BRIDGE')
    if old:
        old.name = 'M-FROST-BRIDGE.old'
    m, nt = sklib._new_mat('M-FROST-BRIDGE')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 1200, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 1500, 0).inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -1500, 0)
    co = tc.outputs['Object']
    wn = _noise(nt, co, 180.0, 4.0, 0.6, -1350, 400)                    # warp so ridges look grown, not cellular
    wv = _n(nt, 'ShaderNodeVectorMath', -1150, 300, operation='MULTIPLY_ADD')
    _l(nt, wn.outputs['Color'], wv.inputs[0])
    wv.inputs[1].default_value = (0.004, 0.004, 0.004)
    _l(nt, co, wv.inputs[2])
    rg = _n(nt, 'ShaderNodeTexVoronoi', -950, 300, feature='DISTANCE_TO_EDGE')
    rg.inputs['Scale'].default_value = p['ridge']
    _l(nt, wv.outputs[0], rg.inputs['Vector'])
    ridge = _maprange(nt, rg.outputs['Distance'], 0.0, 0.12, 1.0, 0.0, -750, 300)     # bright feather lines
    fv = _n(nt, 'ShaderNodeTexVoronoi', -950, 0)
    fv.inputs['Scale'].default_value = p['facet']
    _l(nt, co, fv.inputs['Vector'])
    fh = _n(nt, 'ShaderNodeRGBToBW', -750, 0)
    _l(nt, fv.outputs['Color'], fh.inputs[0])
    fz = _noise(nt, co, p['fuzz'], 12.0, 0.8, -950, -250)
    fuzz = _maprange(nt, fz.outputs['Fac'], 0.45, 0.7, 0.0, 1.0, -750, -250)
    cl = _noise(nt, co, p['clump'], 5.0, 0.6, -950, -500)
    dens = _maprange(nt, cl.outputs['Fac'], 0.35, 0.62, 0.15, 1.0, -750, -500)
    mask = _math(nt, 'MAXIMUM', ridge, _math(nt, 'MULTIPLY', fuzz, 0.85, x=-550, y=-250), x=-450, y=100)
    mask = _math(nt, 'MULTIPLY', mask, dens, True, -300, 100)
    col = _mix(nt, mask, (0.42, 0.45, 0.5), (0.86, 0.92, 1.0), 'MIX', 0, 400)
    col = _mix(nt, _math(nt, 'MULTIPLY', mask, fh.outputs[0], x=-150, y=600), col, (1.0, 1.0, 1.0), 'MIX', 200, 450)
    _l(nt, col, b.inputs['Base Color'])
    _l(nt, _maprange(nt, mask, 0.0, 1.0, 0.45, 0.08, 0, -100), b.inputs['Roughness'])
    b.inputs['Specular IOR Level'].default_value = 0.7
    b.inputs['Subsurface Weight'].default_value = 0.15
    b.inputs['Subsurface Radius'].default_value = (0.4, 0.5, 0.7)
    b.inputs['Subsurface Scale'].default_value = 0.001
    h = _math(nt, 'MULTIPLY', mask, _math(nt, 'MULTIPLY_ADD', fh.outputs[0], 0.6, x=-300, y=-100, c=0.4), x=0, y=-250)
    bp = _n(nt, 'ShaderNodeBump', 900, -300)
    bp.inputs['Strength'].default_value = 1.0
    bp.inputs['Distance'].default_value = p['bump']
    _l(nt, h, bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    if old:
        for ob in bpy.data.objects:
            if ob.type == 'MESH':
                for i, ms in enumerate(ob.data.materials):
                    if ms == old:
                        ob.data.materials[i] = m
    return m


def light_object(lo):
    el, az = math.radians(LIGHT_ELEV_DEG), math.radians(LIGHT_AZ_DEG)
    from mathutils import Vector
    d = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    lo.location = d * 1.0                               # 1 m from the patch centre
    lo.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    L = lo.data
    L.shape, L.size, L.size_y = 'RECTANGLE', 0.25, 0.25
    L.color = sklib.kelvin_rgb(6500)
    L.energy = 30.0
    return lo


def build(W=0.21, H=0.15):
    bc = sklib.collection('BRIDGE_FROST', parent=False)
    bm = bmesh.new()
    nx, ny = 48, 40
    vs = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x, y = (i / nx - 0.5) * W, (j / ny - 0.5) * H
            e = max(0.0, max(abs(x) / (W / 2), abs(y) / (H / 2)) - 0.45) / 0.55     # flat centre, crumpled rim
            z = -0.003 * e * e + 0.004 * e * (math.sin(x * 130 + y * 70) * math.sin(y * 150 - x * 40))
            row.append(bm.verts.new((x, y, z)))
        vs.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    me = bpy.data.meshes.new('BRIDGE_FROST_patch')
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.materials.append(material())
    bc.objects.link(bpy.data.objects.new('BRIDGE_FROST_patch', me))
    lo = bpy.data.objects.new('BRIDGE_FROST_light', bpy.data.lights.new('BRIDGE_FROST_light', 'AREA'))
    light_object(lo)
    bc.objects.link(lo)
    return bc
