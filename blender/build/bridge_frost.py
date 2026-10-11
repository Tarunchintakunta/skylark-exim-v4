"""BRIDGE_FROST (table f216 -> reefer f1): shared builder.

    sys.path.insert(0, REPO + '/assets-src/blender/build'); import bridge_frost
    coll = bridge_frost.build()          # unlinked collection 'BRIDGE_FROST' (patch + crystals + light), origin = patch centre
    sklib.instance(coll, loc, 0.0, 'BRIDGE_FROST_inst')   # camera: loc + (0,0,0.12), rotation (0,0,0), lens 100, f/2.8

Frost = real geometry: ~26k hoar-frost crystals (hexagonal plates + needle columns, 0.15-1.6 mm) standing on a
frosted white poly film, clumped by a density field, so the 100 mm macro shows crystal facets that sparkle under the
single soft 6500 K area light 1 m above (spec). No cell/crack pattern in the film shader.
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector, noise

import sklib
from sklib import _n, _l, _math, _mix, _maprange, _noise

LIGHT_ELEV_DEG = 90.0      # spec: single soft area light 1 m above the patch
LIGHT_AZ_DEG = 200.0


def material(p=None):
    """M-FROST-BRIDGE: white poly film under a fine frost bloom (no cellular pattern): mottled white fuzz over a
    greyer translucent film, fine bump. The 3D crystals on top carry the macro texture."""
    p = dict(dict(fuzz=900.0, clump=55.0, bump=0.0012), **(p or {}))
    old = bpy.data.materials.get('M-FROST-BRIDGE')
    if old:
        old.name = 'M-FROST-BRIDGE.old'
    m, nt = sklib._new_mat('M-FROST-BRIDGE')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 1200, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 1500, 0).inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -1500, 0)
    co = tc.outputs['Object']
    fz = _noise(nt, co, p['fuzz'], 14.0, 0.85, -950, -250)                  # frost bloom grain
    fuzz = _maprange(nt, fz.outputs['Fac'], 0.42, 0.68, 0.0, 1.0, -750, -250)
    cl = _noise(nt, co, p['clump'], 6.0, 0.65, -950, -500)                  # thicker / thinner frost
    dens = _maprange(nt, cl.outputs['Fac'], 0.32, 0.66, 0.1, 1.0, -750, -500)
    mask = _math(nt, 'MULTIPLY', fuzz, dens, True, -450, 100)
    col = _mix(nt, mask, (0.30, 0.33, 0.37), (0.88, 0.92, 0.98), 'MIX', 0, 400)
    _l(nt, col, b.inputs['Base Color'])
    _l(nt, _maprange(nt, mask, 0.0, 1.0, 0.3, 0.6, 0, -100), b.inputs['Roughness'])
    b.inputs['Specular IOR Level'].default_value = 0.6
    b.inputs['Subsurface Weight'].default_value = 0.2
    b.inputs['Subsurface Radius'].default_value = (0.4, 0.5, 0.7)
    b.inputs['Subsurface Scale'].default_value = 0.001
    bp = _n(nt, 'ShaderNodeBump', 900, -300)
    bp.inputs['Strength'].default_value = 0.8
    bp.inputs['Distance'].default_value = p['bump']
    _l(nt, mask, bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    if old:
        for ob in bpy.data.objects:
            if ob.type == 'MESH':
                for i, ms in enumerate(ob.data.materials):
                    if ms == old:
                        ob.data.materials[i] = m
    return m


def crystal_material():
    """Clear ice: glossy, faintly blue, subsurface for the milky interior (no refraction: thousands of tiny
    refractive shards are noisy in EEVEE and read grey). Per-object random -> slight brightness variation."""
    m = bpy.data.materials.get('M-FROST-CRYSTAL')
    if m:
        return m
    m, nt = sklib._new_mat('M-FROST-CRYSTAL')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 900, 0).inputs['Surface'])
    at = _n(nt, 'ShaderNodeAttribute', -400, 100, attribute_name='cv')
    _l(nt, _mix(nt, at.outputs['Fac'], (0.62, 0.68, 0.76), (0.97, 0.98, 1.0), 'MIX', 200, 100), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.07
    b.inputs['IOR'].default_value = 1.31
    b.inputs['Specular IOR Level'].default_value = 0.9
    b.inputs['Subsurface Weight'].default_value = 0.35
    b.inputs['Subsurface Radius'].default_value = (0.5, 0.65, 0.9)
    b.inputs['Subsurface Scale'].default_value = 0.0004
    return m


def crystals(name='BRIDGE_FROST_crystals', W=0.11, H=0.08, n=26000, seed=216):
    """Hoar-frost crystals in a W x H area around the origin (the macro view at 0.12 m / 100 mm is ~43 x 24 mm)."""
    r = random.Random(seed)
    vs, fs, cv = [], [], []
    hexr = [(math.cos(k * math.pi / 3), math.sin(k * math.pi / 3)) for k in range(6)]
    k = 0
    while k < n:
        x, y = r.uniform(-W / 2, W / 2), r.uniform(-H / 2, H / 2)
        d = noise.noise(Vector((x * 60, y * 60, 3.1))) * 0.5 + noise.noise(Vector((x * 220, y * 220, 7.7))) * 0.25
        edge = max(abs(x) / (W / 2), abs(y) / (H / 2))
        if r.random() > min(1.0, max(0.0, 0.55 + d * 1.4)) * (1.0 - edge ** 6):
            continue
        k += 1
        big = r.random() ** 2.2
        tilt = r.uniform(0.25, 1.35)
        zc = 0.00025 * math.sin(x * 210 + 1.3) * math.sin(y * 170) - 0.00008   # root in the film
        M = Matrix.Translation((x, y, zc)) @ Euler((tilt, 0, r.uniform(0, 2 * math.pi)), 'XZY').to_matrix().to_4x4()
        base = len(vs)
        c = r.random()
        if r.random() < 0.62:                        # hexagonal plate standing on an edge
            R_ = 0.00015 + 0.0006 * big
            t = R_ * r.uniform(0.06, 0.12)
            M = M @ Matrix.Translation((0, 0, R_ * 0.7)) @ Matrix.Rotation(math.pi / 2, 4, 'X')
            sq = r.uniform(0.75, 1.0)
            for z in (-t, t):
                for (cx, cy) in hexr:
                    vs.append(M @ Vector((cx * R_, cy * R_ * sq, z)))
            fs.append(tuple(base + i for i in range(6)))
            fs.append(tuple(base + 6 + i for i in range(5, -1, -1)))
            for i in range(6):
                j = (i + 1) % 6
                fs.append((base + i, base + 6 + i, base + 6 + j, base + j))
            cv += [c] * 12
        else:                                        # needle / column, 4-sided with a pointed tip
            L = 0.0003 + 0.0013 * big
            w = L * r.uniform(0.05, 0.1)
            for z in (0.0, L * 0.85):
                for (cx, cy) in ((w, 0), (0, w), (-w, 0), (0, -w)):
                    vs.append(M @ Vector((cx, cy, z)))
            vs.append(M @ Vector((0, 0, L)))
            fs.append((base + 3, base + 2, base + 1, base + 0))
            for i in range(4):
                j = (i + 1) % 4
                fs.append((base + i, base + j, base + 4 + j, base + 4 + i))
                fs.append((base + 4 + i, base + 4 + j, base + 8))
            cv += [c] * 9
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in vs], [], fs)
    me.update()
    a = me.attributes.new('cv', 'FLOAT', 'POINT')
    a.data.foreach_set('value', cv)
    me.materials.append(crystal_material())
    print('BRIDGE_FROST crystals', n, 'verts', len(vs))
    return bpy.data.objects.new(name, me)


def light_object(lo):
    el, az = math.radians(LIGHT_ELEV_DEG), math.radians(LIGHT_AZ_DEG)
    d = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    lo.location = d * 1.0                               # 1 m from the patch centre
    lo.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    L = lo.data
    L.shape, L.size, L.size_y = 'RECTANGLE', 0.25, 0.25
    L.color = sklib.kelvin_rgb(6500)
    L.energy = 22.0
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
            z = -0.003 * e * e + 0.004 * e * (math.sin(x * 130 + y * 70) * math.sin(y * 150 - x * 40)) \
                + 0.00025 * math.sin(x * 210 + 1.3) * math.sin(y * 170)           # soft film creases under the frost
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
    patch = bpy.data.objects.new('BRIDGE_FROST_patch', me)
    bc.objects.link(patch)
    cr = crystals()
    bc.objects.link(cr)
    lo = bpy.data.objects.new('BRIDGE_FROST_light', bpy.data.lights.new('BRIDGE_FROST_light', 'AREA'))
    light_object(lo)
    bc.objects.link(lo)
    return bc
