"""sklib - shared Blender 5.2 library for the Skylark Exim v4 scenes (headless, EEVEE).

    import sys; sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib'); import sklib

Conventions: metres, Z up, every builder puts the origin at the base centre. Materials map with a metric box-projected
UV ('UVMap', written by mat_to/box_uv), so always assign library materials with sklib.mat_to(obj, mat).
Textures: CC0 only (Poly Haven, ambientCG), cached in assets-src/tex/<slug>/, credited in assets-src/tex/LICENSES.tsv.
"""
import io
import json
import math
import os
import random
import re
import subprocess
import urllib.request
import zipfile

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

REPO = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4'
SRC = REPO + '/assets-src'
TEX = SRC + '/tex'
LIB = SRC + '/blender/lib'
UA = {'User-Agent': 'skylark-exim-v4-sklib/1.0 (CC0 texture cache)'}
D2R = math.pi / 180


# ----------------------------------------------------------------------------------------------------------------- scene
def reset():
    """Factory-empty file, metric units, EEVEE. Returns the scene."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    u = s.unit_settings
    u.system, u.scale_length, u.length_unit = 'METRIC', 1.0, 'METERS'
    s.render.engine = 'BLENDER_EEVEE'
    return s


def link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def new_obj(name, data=None, coll=None, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob = bpy.data.objects.new(name, data)
    ob.location, ob.rotation_euler = loc, rot
    if parent:
        ob.parent = parent
    return link(ob, coll) if coll is not False else ob


def collection(name, parent=None):
    """Get/create a collection. parent=None -> linked to the scene; parent=False -> unlinked (instancing source)."""
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if parent is not False:
        p = parent or bpy.context.scene.collection
        if c.name not in p.children:
            p.children.link(c)
    return c


def instance(coll, loc=(0, 0, 0), rot_z=0.0, name=None, parent_coll=None, scale=1.0):
    """Collection instance empty (cheap copies of containers, pallets, crates)."""
    e = bpy.data.objects.new(name or ('I_' + coll.name), None)
    e.instance_type, e.instance_collection = 'COLLECTION', coll
    e.location, e.rotation_euler, e.scale = loc, (0, 0, rot_z), (scale,) * 3
    return link(e, parent_coll)


def _mesh_obj(name, bm, coll=None, parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return new_obj(name, me, coll, parent)


def apply_mods(ob):
    """Bake the modifier stack into the mesh (keeps materials)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


def join(obs, name):
    """Join mesh objects (world transforms baked) into one new object; the inputs are removed."""
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    mats = []
    for o in obs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(o.matrix_world)
        remap = []
        for sl in o.material_slots:
            if sl.material not in mats:
                mats.append(sl.material)
            remap.append(mats.index(sl.material))
        for p in me.polygons:
            p.material_index = remap[p.material_index] if remap else 0
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in obs:
        bpy.data.objects.remove(o)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return me


# -------------------------------------------------------------------------------------------------------- texture cache
def _get(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
        data = r.read()
    with open(dest + '.part', 'wb') as f:
        f.write(data)
    os.replace(dest + '.part', dest)
    return dest


def _json(url, cache):
    return json.load(open(_get(url, cache)))


def _license(slug, url, authors, lic='CC0'):
    p = TEX + '/LICENSES.tsv'
    rows = open(p).read() if os.path.exists(p) else 'slug\turl\tauthors\tlicense\n'
    if not any(r.split('\t')[0] == slug for r in rows.splitlines()):
        os.makedirs(TEX, exist_ok=True)
        open(p, 'w').write(rows + '%s\t%s\t%s\t%s\n' % (slug, url, authors, lic))


_PH = {'diff': 'Diffuse', 'rough': 'Rough', 'nor': 'nor_gl', 'disp': 'Displacement', 'arm': 'arm'}


def ph_tex(slug, res='1k', maps=('diff', 'rough', 'nor')):
    """Download Poly Haven CC0 maps (jpg) into assets-src/tex/<slug>/ (cached) and credit them.
    Returns {'diff': path, 'rough': path, 'nor': path, ..., 'size_m': real-world tile width in metres}."""
    d = '%s/%s' % (TEX, slug)
    files = _json('https://api.polyhaven.com/files/' + slug, d + '/files.json')
    info = _json('https://api.polyhaven.com/info/' + slug, d + '/info.json')
    out = {}
    for m in maps:
        f = files[_PH[m]][res]
        url = (f.get('jpg') or f.get('png'))['url']
        out[m] = _get(url, '%s/%s' % (d, os.path.basename(url)))
    out['size_m'] = (info.get('dimensions') or [1000])[0] / 1000.0
    _license(slug, 'https://polyhaven.com/a/' + slug, '; '.join(info.get('authors', {})))
    return out


_ACG_SIZE = {'Cardboard004': 0.30}   # metres per tile (ambientCG has no dimension metadata; measured by eye)


def acg_tex(asset, res='1K'):
    """ambientCG CC0 material (1K/2K-JPG zip) -> same dict as ph_tex. Only the jpg maps are extracted."""
    d = '%s/acg_%s' % (TEX, asset)
    want = {'diff': '_Color.jpg', 'rough': '_Roughness.jpg', 'nor': '_NormalGL.jpg', 'disp': '_Displacement.jpg'}
    out = {k: '%s/%s_%s-JPG%s' % (d, asset, res, v) for k, v in want.items()}
    if not all(os.path.exists(p) for p in out.values()):
        os.makedirs(d, exist_ok=True)
        req = urllib.request.Request('https://ambientcg.com/get?file=%s_%s-JPG.zip' % (asset, res), headers=UA)
        with urllib.request.urlopen(req, timeout=180) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
        for k, p in out.items():
            name = [n for n in z.namelist() if n.endswith(want[k])][0]
            open(p, 'wb').write(z.read(name))
    out['size_m'] = _ACG_SIZE.get(asset, 1.0)
    _license('acg:' + asset, 'https://ambientcg.com/view?id=' + asset, 'ambientCG (Lennart Demes)')
    return out


def tex(slug, res='1k'):
    """'concrete_floor_02' -> Poly Haven; 'acg:Cardboard004' -> ambientCG."""
    if slug.startswith('acg:'):
        return acg_tex(slug[4:], res.upper())
    return ph_tex(slug, res)


# ------------------------------------------------------------------------------------------------------ node utilities
def _new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    m.node_tree.nodes.clear()
    return m, m.node_tree


def _n(nt, t, x=0, y=0, **kw):
    n = nt.nodes.new(t)
    n.location = (x, y)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _s(sockets, key):
    for s in sockets:
        if s.identifier == key and s.enabled:
            return s
    for s in sockets:
        if s.name == key and s.enabled:
            return s
    return sockets[key]


def _l(nt, a, b):
    nt.links.new(a, b)


def _math(nt, op, a, b=None, clamp=False, x=0, y=0, c=None):
    m = _n(nt, 'ShaderNodeMath', x, y, operation=op, use_clamp=clamp)
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            _l(nt, v, m.inputs[i])
    return m.outputs[0]


def _mix(nt, fac, a, b, blend='MIX', x=0, y=0):
    m = _n(nt, 'ShaderNodeMix', x, y, data_type='RGBA', blend_type=blend)
    for key, v in (('Factor_Float', fac), ('A_Color', a), ('B_Color', b)):
        sk = _s(m.inputs, key)
        if isinstance(v, (int, float)):
            sk.default_value = v
        elif isinstance(v, tuple):
            sk.default_value = v if len(v) == 4 else tuple(v) + (1,)
        else:
            _l(nt, v, sk)
    return _s(m.outputs, 'Result_Color')


def _maprange(nt, v, a, b, c=0.0, d=1.0, x=0, y=0):
    m = _n(nt, 'ShaderNodeMapRange', x, y)
    _l(nt, v, m.inputs['Value'])
    m.inputs['From Min'].default_value, m.inputs['From Max'].default_value = a, b
    m.inputs['To Min'].default_value, m.inputs['To Max'].default_value = c, d
    return m.outputs['Result']


def _noise(nt, vec, scale=4.0, detail=6.0, rough=0.6, x=0, y=0, dims='3D'):
    n = _n(nt, 'ShaderNodeTexNoise', x, y, noise_dimensions=dims)
    n.inputs['Scale'].default_value, n.inputs['Detail'].default_value = scale, detail
    n.inputs['Roughness'].default_value = rough
    if vec is not None:
        _l(nt, vec, n.inputs['Vector'])
    return n


def _vscale(nt, vec, sx, sy, sz, x=0, y=0):
    mp = _n(nt, 'ShaderNodeMapping', x, y)
    mp.inputs['Scale'].default_value = (sx, sy, sz)
    _l(nt, vec, mp.inputs['Vector'])
    return mp.outputs[0]


def _img(nt, path, color, vec, x=0, y=0):
    n = _n(nt, 'ShaderNodeTexImage', x, y)
    n.image = bpy.data.images.load(path, check_existing=True)
    if not color:
        n.image.colorspace_settings.name = 'Non-Color'
    if vec is not None:
        _l(nt, vec, n.inputs['Vector'])
    return n


def _avg_lum(img):
    a = np.empty(len(img.pixels), np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(-1, 4)[::7]
    return float((a[:, 0] * 0.2126 + a[:, 1] * 0.7152 + a[:, 2] * 0.0722).mean()) or 0.5


def _dirt_mask(nt, wear, ao_dist, x=-600, y=-500):
    """(1-AO) cavities x large noise blotches x wear -> 0..1 grime mask socket."""
    ao = _n(nt, 'ShaderNodeAmbientOcclusion', x, y, samples=8, only_local=True)
    ao.inputs['Distance'].default_value = ao_dist
    cav = _maprange(nt, ao.outputs['AO'], 1.0, 0.45, 0.0, 1.0, x + 200, y)
    tc = _n(nt, 'ShaderNodeTexCoord', x - 200, y - 250)
    n2 = _noise(nt, tc.outputs['Object'], 3.0, 8.0, 0.62, x, y - 250)
    nb = _maprange(nt, n2.outputs['Fac'], 0.46, 0.7, 0.0, 1.0, x + 200, y - 250)
    m = _math(nt, 'MULTIPLY_ADD', cav, 0.8, x=x + 400, y=y)
    _l(nt, nb, m.node.inputs[2])
    m = _math(nt, 'SUBTRACT', m, 0.25, True, x + 550, y)
    return _math(nt, 'MULTIPLY', m, wear, True, x + 700, y)


# ----------------------------------------------------------------------------------------------------------- materials
def pbr(name, slug, scale=1.0, tint=None, wear=0.3, wear_color=(0.19, 0.16, 0.12), rough=(0.0, 1.0), metal=0.0,
        nor=1.0, res='1k', streaks=0.0, ao_dist=0.25, var=0.10, sat=None, contrast=1.0):
    """Photo PBR material: albedo + roughness + normal from a CC0 scan, mapped at real-world size on the metric
    box UV (scale>1 = bigger pattern), tint = recolour (desaturated albedo x tint, brightness preserved),
    contrast (<1 flattens the scan's value variation when tinting), macro colour variation, AO+noise grime mask (wear 0..1) mixing in wear_color, optional rust streaks (0..1)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    t = tex(slug, res)
    m, nt = _new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 1400, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 1100, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -1400, 0)
    k = 1.0 / (t['size_m'] * scale)
    uv = _vscale(nt, tc.outputs['UV'], k, k, k, -1200, 0)
    di = _img(nt, t['diff'], True, uv, -950, 300)
    col = di.outputs['Color']
    if tint is not None:
        g = 1.0 / _avg_lum(di.image)
        bw = _n(nt, 'ShaderNodeRGBToBW', -650, 350)
        _l(nt, col, bw.inputs[0])
        vm = _n(nt, 'ShaderNodeVectorMath', -450, 350, operation='SCALE')
        vm.inputs[0].default_value = tuple(tint[:3])
        _l(nt, _math(nt, 'MULTIPLY_ADD', bw.outputs[0], g * contrast, x=-550, y=500, c=1.0 - contrast), vm.inputs['Scale'])
        col = vm.outputs[0]
        if sat is not None:      # keep some of the original hue
            col = _mix(nt, sat, col, di.outputs['Color'], 'COLOR', -300, 350)
    # macro variation (breaks tiling)
    nv = _noise(nt, tc.outputs['Object'], 0.35, 3.0, 0.5, -650, 600)
    vv = _maprange(nt, nv.outputs['Fac'], 0.3, 0.7, 1 - var, 1 + var, -450, 600)
    vm = _n(nt, 'ShaderNodeVectorMath', -200, 450, operation='SCALE')
    _l(nt, col, vm.inputs[0])
    _l(nt, vv, vm.inputs['Scale'])
    col = vm.outputs[0]
    mask = _dirt_mask(nt, wear, ao_dist) if wear > 0 else None
    if streaks > 0:
        ns = _noise(nt, _vscale(nt, tc.outputs['Object'], 7, 7, 0.25, -850, 900), 4.0, 6.0, 0.55, -650, 900)
        sm = _maprange(nt, ns.outputs['Fac'], 0.56, 0.72, 0.0, 0.75 * streaks, -450, 900)
        col = _mix(nt, sm, col, (0.30, 0.13, 0.05), 'MIX', 0, 700)
    if mask is not None:
        col = _mix(nt, mask, col, tuple(wear_color), 'MIX', 300, 400)
    _l(nt, col, b.inputs['Base Color'])
    ri = _img(nt, t['rough'], False, uv, -950, 0)
    r = _maprange(nt, ri.outputs['Color'], 0.0, 1.0, rough[0], rough[1], -650, 0)
    if mask is not None:
        r = _math(nt, 'MULTIPLY_ADD', mask, 0.25, True, 500, 0, c=r)
    _l(nt, r, b.inputs['Roughness'])
    ni = _img(nt, t['nor'], False, uv, -950, -300)
    nm = _n(nt, 'ShaderNodeNormalMap', -650, -300)
    nm.inputs['Strength'].default_value = nor
    _l(nt, ni.outputs['Color'], nm.inputs['Color'])
    _l(nt, nm.outputs[0], b.inputs['Normal'])
    if metal:
        if mask is not None:
            _l(nt, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, mask, x=600, y=-150), metal, x=800, y=-150),
               b.inputs['Metallic'])
        else:
            b.inputs['Metallic'].default_value = metal
    return m


def flat(name, color, rough=0.5, metal=0.0, var=0.08, scale=40.0, bump=0.0, **principled):
    """Simple procedural material (colour + micro noise variation [+ bump]) for ink, tape, rubber, film, etc."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = _new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 800, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 500, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -600, 0)
    nz = _noise(nt, tc.outputs['Object'], scale, 8.0, 0.6, -400, 0)
    v = _maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 1 - var, 1 + var, -200, 100)
    vm = _n(nt, 'ShaderNodeVectorMath', 100, 150, operation='SCALE')
    vm.inputs[0].default_value = tuple(color[:3])
    _l(nt, v, vm.inputs['Scale'])
    _l(nt, vm.outputs[0], b.inputs['Base Color'])
    rr = _maprange(nt, nz.outputs['Fac'], 0.3, 0.7, rough * 0.85, min(1, rough * 1.15), -200, -100)
    _l(nt, rr, b.inputs['Roughness'])
    b.inputs['Metallic'].default_value = metal
    if bump:
        bp = _n(nt, 'ShaderNodeBump', 200, -300)
        bp.inputs['Strength'].default_value = bump
        _l(nt, nz.outputs['Fac'], bp.inputs['Height'])
        _l(nt, bp.outputs[0], b.inputs['Normal'])
    for k, val in principled.items():
        b.inputs[k].default_value = val
    return m


def _hex(c):
    return ''.join('%02x' % int(max(0, min(1, v)) * 255) for v in c[:3])


# presets (cached by name) -- every one is a photo-scan texture set + grime mask
def concrete_floor(wear=0.35):
    return pbr('concrete_floor', 'concrete_floor_02', wear=wear, ao_dist=0.4)


def concrete_quay(wear=0.4):
    return pbr('concrete_quay', 'concrete_floor_worn_001', wear=wear, ao_dist=0.5)


def asphalt(wear=0.3):
    return pbr('asphalt', 'asphalt_02', wear=wear, ao_dist=0.5)


def painted_metal(color=(0.5, 0.06, 0.04), wear=0.3, streaks=0.0, contrast=0.6):
    return pbr('painted_metal_%s_w%02d_s%02d_c%02d' % (_hex(color), wear * 99, streaks * 99, contrast * 99),
               'blue_metal_plate', tint=color, wear=wear, wear_color=(0.16, 0.10, 0.06), rough=(0.32, 0.75),
               streaks=streaks, ao_dist=0.35, contrast=contrast)


def rusty_metal(wear=0.3):
    return pbr('rusty_metal', 'rusty_metal_02', wear=wear, metal=0.0)


def stainless(wear=0.1):
    """Brushed stainless: metal_plate_02 roughness/normal, neutral tint, metallic."""
    return pbr('stainless', 'blue_metal_plate', tint=(0.62, 0.63, 0.64), rough=(0.12, 0.38), metal=1.0, nor=0.3,
               wear=wear, wear_color=(0.35, 0.33, 0.30), var=0.04, scale=0.5, contrast=0.3)


def aluminium(wear=0.12):
    return pbr('aluminium', 'blue_metal_plate', tint=(0.78, 0.79, 0.8), rough=(0.3, 0.55), metal=1.0, nor=0.3,
               wear=wear, wear_color=(0.4, 0.38, 0.35), var=0.05, contrast=0.35)


def galvanised(wear=0.25):
    return pbr('galvanised', 'blue_metal_plate', tint=(0.45, 0.46, 0.47), rough=(0.35, 0.7), metal=0.85, nor=0.6,
               wear=wear, wear_color=(0.2, 0.15, 0.1), contrast=0.5)


def corrugated_steel(color=(0.55, 0.56, 0.58), wear=0.3):
    return pbr('corrugated_steel_' + _hex(color), 'corrugated_iron_02', tint=color, wear=wear, metal=0.6,
               rough=(0.3, 0.8))


def wood_planks(wear=0.25):
    return pbr('wood_planks', 'wood_planks', wear=wear, ao_dist=0.2)


def oak_table(wear=0.08):
    return pbr('oak_table', 'kitchen_wood', wear=wear, rough=(0.25, 0.55), ao_dist=0.1)


def linen_fabric(color=(0.86, 0.84, 0.79), wear=0.05):
    return pbr('linen_' + _hex(color), 'rough_linen', tint=color, wear=wear, ao_dist=0.05, rough=(0.75, 1.0))


def plastic(color=(0.08, 0.25, 0.55), wear=0.25, name=None):
    """Moulded HDPE/PP: scuff/scratch roughness + normal borrowed from a scratched painted-steel scan."""
    return pbr(name or 'plastic_' + _hex(color), 'blue_metal_plate', tint=color, wear=wear, rough=(0.38, 0.62),
               nor=0.25, wear_color=(0.22, 0.2, 0.17), ao_dist=0.08, var=0.04, scale=0.6)


def cardboard_kraft(wear=0.15, tint=(0.50, 0.34, 0.19)):
    return pbr('cardboard_kraft', 'acg:Cardboard004', tint=tint, sat=0.25, wear=wear, wear_color=(0.22, 0.15, 0.09),
               rough=(0.75, 0.95), ao_dist=0.04, nor=0.6, var=0.06)


def white_wall(wear=0.15):
    return pbr('white_wall', 'white_plaster_02', wear=wear, ao_dist=0.4)


def white_tiles(wear=0.12):
    return pbr('white_tiles', 'long_white_tiles', wear=wear, ao_dist=0.2)


def epoxy_floor(color=(0.32, 0.38, 0.36), wear=0.2):
    return pbr('epoxy_' + _hex(color), 'smooth_concrete_floor', tint=color, sat=0.1, rough=(0.08, 0.35), nor=0.4,
               wear=wear, ao_dist=0.3)


def mud(wear=0.0):
    return pbr('mud', 'brown_mud_03', wear=wear)


def grass(wear=0.0):
    return pbr('grass', 'sparse_grass', wear=wear)


def sand(wear=0.0):
    return pbr('sand', 'damp_sand', wear=wear)


# ------------------------------------------------------------------------------------------------- UVs, bevel, assign
def box_uv(ob, size=1.0):
    """Metric box-projection UV ('UVMap') from object-space coordinates x object scale. size = metres per UV unit."""
    me = ob.data
    if not len(me.polygons):
        return
    uvl = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3) * np.array(ob.scale, np.float32) / size
    lv = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get('vertex_index', lv)
    pn = np.empty(len(me.polygons) * 3, np.float32)
    me.polygons.foreach_get('normal', pn)
    pn = pn.reshape(-1, 3)
    lt = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get('loop_total', lt)
    n = pn[np.repeat(np.arange(len(lt)), lt)]
    c = co[lv]
    ax = np.abs(n).argmax(1)
    sg = np.sign(n[np.arange(len(n)), ax])
    u = np.where(ax == 0, c[:, 1] * sg, np.where(ax == 1, -c[:, 0] * sg, c[:, 0]))
    v = np.where(ax == 2, c[:, 1] * sg, c[:, 2])
    uvl.data.foreach_set('uv', np.stack([u, v], 1).ravel())


def mat_to(ob, *mats, uv=True):
    """Assign material(s) (slot order = material_index) and write the metric box UV."""
    if ob.type == 'MESH':
        ob.data.materials.clear()
        for m in mats:
            ob.data.materials.append(m)
        if uv:
            box_uv(ob)
    return ob


def bevel(ob, width=0.01, seg=2, angle=35.0, smooth=True):
    """Bevel (angle-limited) + weighted normals + smooth-by-angle: kills razor CG edges."""
    if smooth:
        ob.data.shade_smooth()
        ob.data.set_sharp_from_angle(angle=angle * D2R)
    bv = ob.modifiers.new('Bevel', 'BEVEL')
    bv.width, bv.segments, bv.limit_method, bv.angle_limit = width, seg, 'ANGLE', angle * D2R
    bv.use_clamp_overlap = True
    bv.miter_outer = 'MITER_ARC'
    wn = ob.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL')
    wn.keep_sharp = True
    return ob


# ------------------------------------------------------------------------------------------------------------ world/sky
def kelvin_rgb(k):
    """Approximate blackbody colour (normalised to max 1) for light colours."""
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    c = [x ** 2.2 for x in c]
    mx = max(c)
    return tuple(x / mx for x in c)


def sun_color(elev_deg):
    """Warmer sun near the horizon: ~2600 K at 0 deg -> ~5600 K above 45 deg."""
    f = max(0.0, min(1.0, elev_deg / 45.0))
    f = f * f * (3 - 2 * f)
    return kelvin_rgb(2600 + (5600 - 2600) * f)


def _world(name):
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    try:
        w.use_nodes = True
    except Exception:
        pass
    w.node_tree.nodes.clear()
    bpy.context.scene.world = w
    return w, w.node_tree


def sky_world(sun_elev_deg=35.0, sun_az_deg=135.0, strength=1.0, sun_strength=None, sun_angle_deg=1.2,
              air=1.0, dust=1.0, ozone=1.0):
    """Physical sky (MULTIPLE_SCATTERING, the 5.x Nishita) without its own sun disc + a matching Sun light that
    casts the shadows. Azimuth: 0 = sun in +Y (north), 90 = +X (east). Returns (world, sun_object)."""
    w, nt = _world('SK_Sky')
    sky = _n(nt, 'ShaderNodeTexSky', -300, 0)
    kinds = [e.identifier for e in sky.bl_rna.properties['sky_type'].enum_items]
    sky.sky_type = 'MULTIPLE_SCATTERING' if 'MULTIPLE_SCATTERING' in kinds else 'NISHITA'
    sky.sun_disc = False
    sky.sun_elevation = sun_elev_deg * D2R
    sky.sun_rotation = sun_az_deg * D2R
    sky.air_density, sky.aerosol_density, sky.ozone_density = air, dust, ozone
    bg = _n(nt, 'ShaderNodeBackground', 0, 0)
    bg.inputs['Strength'].default_value = 0.3 * strength
    out = _n(nt, 'ShaderNodeOutputWorld', 250, 0)
    _l(nt, sky.outputs[0], bg.inputs[0])
    _l(nt, bg.outputs[0], out.inputs[0])
    sun = bpy.data.objects.get('SK_Sun')
    if not sun:
        sun = new_obj('SK_Sun', bpy.data.lights.new('SK_Sun', 'SUN'))
    el, az = sun_elev_deg * D2R, sun_az_deg * D2R
    d = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))   # towards the sun
    sun.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    L = sun.data
    L.color = sun_color(sun_elev_deg)
    # sky brightness falls with elevation much more slowly than the direct sun; keep both plausible for AgX
    L.energy = sun_strength if sun_strength is not None else 6.0 * strength * max(0.15, math.sin(el)) ** 0.5
    L.angle = sun_angle_deg * D2R
    return w, sun


def hdri(slug, res='2k', strength=1.0, rot_deg=0.0):
    """Poly Haven CC0 HDRI as the world (cached in assets-src/tex/hdri/)."""
    d = TEX + '/hdri'
    files = _json('https://api.polyhaven.com/files/' + slug, '%s/%s.files.json' % (d, slug))
    info = _json('https://api.polyhaven.com/info/' + slug, '%s/%s.info.json' % (d, slug))
    url = files['hdri'][res]['hdr']['url']
    path = _get(url, '%s/%s' % (d, os.path.basename(url)))
    _license(slug, 'https://polyhaven.com/a/' + slug, '; '.join(info.get('authors', {})))
    w, nt = _world('SK_HDRI_' + slug)
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    mp = _n(nt, 'ShaderNodeMapping', -700, 0)
    mp.inputs['Rotation'].default_value[2] = rot_deg * D2R
    _l(nt, tc.outputs['Generated'], mp.inputs['Vector'])
    env = _n(nt, 'ShaderNodeTexEnvironment', -450, 0)
    env.image = bpy.data.images.load(path, check_existing=True)
    _l(nt, mp.outputs[0], env.inputs['Vector'])
    bg = _n(nt, 'ShaderNodeBackground', -150, 0)
    bg.inputs['Strength'].default_value = strength
    out = _n(nt, 'ShaderNodeOutputWorld', 100, 0)
    _l(nt, env.outputs[0], bg.inputs[0])
    _l(nt, bg.outputs[0], out.inputs[0])
    return w


# ------------------------------------------------------------------------------------------------------- bmesh helpers
def _bm_box(bm, c, size, mi=0):
    r = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal(Vector(size).to_4d()))
    fs = {f for v in r['verts'] for f in v.link_faces}
    for f in fs:
        f.material_index = mi
    return r['verts']


def _bm_cyl(bm, c, r, h, axis='Z', seg=12, mi=0, r2=None):
    rot = {'Z': Matrix(), 'X': Matrix.Rotation(math.pi / 2, 4, 'Y'), 'Y': Matrix.Rotation(math.pi / 2, 4, 'X')}[axis]
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h,
                                matrix=Matrix.Translation(c) @ rot)
    for f in {f for v in res['verts'] for f in v.link_faces}:
        f.material_index = mi
    return res['verts']


def _bm_strip(bm, pts, v0, v1, mapper, mi=0, flip=False):
    """Extrude a 2D profile [(u,d)...] between v0..v1; mapper(u,d,v)->xyz. Returns faces."""
    a = [bm.verts.new(mapper(u, d, v0)) for u, d in pts]
    b = [bm.verts.new(mapper(u, d, v1)) for u, d in pts]
    fs = []
    for i in range(len(pts) - 1):
        q = (a[i], a[i + 1], b[i + 1], b[i]) if not flip else (a[i], b[i], b[i + 1], a[i + 1])
        f = bm.faces.new(q)
        f.material_index = mi
        fs.append(f)
    return fs


def _corr(length, pitch, depth, of, inf):
    """Trapezoid corrugation profile along [0,length]: list of (u, d) with d=0 outer face, d=depth inner face."""
    n = int(length // pitch)
    u = (length - n * pitch) / 2
    run = (pitch - of - inf) / 2
    pts = [(0.0, 0.0)]
    if u > 1e-4:
        pts.append((u, 0.0))
    for _ in range(n):
        pts += [(u + of, 0.0), (u + of + run, depth), (u + of + run + inf, depth), (u + pitch, 0.0)]
        u += pitch
    if length - u > 1e-4:
        pts.append((length, 0.0))
    return pts


# ------------------------------------------------------------------------------------------------- hero carton (A-HERO)
CW, CD, CH, CT = 0.50, 0.35, 0.25, 0.007     # carton outer W(x) D(y) H(z), double-wall board thickness


def _carton_mats(lite=False):
    if lite:
        return _lite_carton_mats()
    kraft = cardboard_kraft()
    edge = bpy.data.materials.get('carton_edge')
    if not edge:     # cut edge of double-wall board: two rows of flute arches (procedural) on kraft
        edge, nt = _new_mat('carton_edge')
        out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
        b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
        _l(nt, b.outputs[0], out.inputs['Surface'])
        tc = _n(nt, 'ShaderNodeTexCoord', -800, 0)
        sep = _n(nt, 'ShaderNodeSeparateXYZ', -600, 0)
        _l(nt, tc.outputs['UV'], sep.inputs[0])
        s = _math(nt, 'ADD', sep.outputs[0], sep.outputs[1], x=-450, y=0)
        wv = _math(nt, 'SINE', _math(nt, 'MULTIPLY', s, 2 * math.pi / 0.0045, x=-300), x=-150)
        fl = _maprange(nt, wv, -1.0, 1.0, 0.0, 1.0, 0, 0)
        nz = _noise(nt, tc.outputs['Object'], 300.0, 4.0, 0.5, -300, -300)
        col = _mix(nt, fl, (0.16, 0.10, 0.05), (0.42, 0.29, 0.16), 'MIX', 250, 150)
        col = _mix(nt, _maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 0, 0.3, 100, -300), col, (0.3, 0.2, 0.1), 'MIX', 400, 150)
        _l(nt, col, b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.9
        bp = _n(nt, 'ShaderNodeBump', 400, -200)
        bp.inputs['Strength'].default_value = 0.6
        bp.inputs['Distance'].default_value = 0.001
        _l(nt, fl, bp.inputs['Height'])
        _l(nt, bp.outputs[0], b.inputs['Normal'])
    white = pbr('carton_white_print', 'acg:Cardboard004', tint=(0.86, 0.85, 0.82), wear=0.12,
                wear_color=(0.45, 0.4, 0.33), rough=(0.6, 0.85), ao_dist=0.04, nor=0.35, var=0.03)
    ink = flat('carton_ink', (0.025, 0.05, 0.13), rough=0.55, var=0.12, scale=180)
    tape = flat('carton_tape', (0.42, 0.27, 0.12), rough=0.12, var=0.06, scale=60, bump=0.05, **{'Coat Weight': 0.6})
    return dict(kraft=kraft, edge=edge, white=white, ink=ink, tape=tape)


def _lite_carton_mats():
    """glTF-safe materials (image textures straight into Principled; UVs pre-scaled per texture size)."""
    d = {}
    t = acg_tex('Cardboard004')
    for key, tint in (('kraft', (1.0, 0.78, 0.6)), ('white', None)):
        nm = 'glb_carton_' + key
        m = bpy.data.materials.get(nm)
        if not m:
            m, nt = _new_mat(nm)
            out = _n(nt, 'ShaderNodeOutputMaterial', 600, 0)
            b = _n(nt, 'ShaderNodeBsdfPrincipled', 300, 0)
            _l(nt, b.outputs[0], out.inputs['Surface'])
            if key == 'kraft':
                di = _img(nt, _kraft_albedo(t['diff']), True, None, -300, 300)
                _l(nt, di.outputs['Color'], b.inputs['Base Color'])
            else:
                b.inputs['Base Color'].default_value = (0.8, 0.79, 0.76, 1)
            ri = _img(nt, t['rough'], False, None, -300, 0)
            _l(nt, ri.outputs['Color'], b.inputs['Roughness'])
            ni = _img(nt, t['nor'], False, None, -300, -300)
            nm_ = _n(nt, 'ShaderNodeNormalMap', 0, -300)
            nm_.inputs['Strength'].default_value = 0.5
            _l(nt, ni.outputs['Color'], nm_.inputs['Color'])
            _l(nt, nm_.outputs[0], b.inputs['Normal'])
        d[key] = m
    for key, col, r in (('edge', (0.30, 0.20, 0.11), 0.9), ('ink', (0.025, 0.05, 0.13), 0.55),
                        ('tape', (0.42, 0.27, 0.12), 0.15)):
        nm = 'glb_carton_' + key
        m = bpy.data.materials.get(nm)
        if not m:
            m, nt = _new_mat(nm)
            b = _n(nt, 'ShaderNodeBsdfPrincipled', 0, 0)
            _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 300, 0).inputs['Surface'])
            b.inputs['Base Color'].default_value = col + (1,)
            b.inputs['Roughness'].default_value = r
        d[key] = m
    return d


def _kraft_albedo(src):
    """Recoloured (kraft-brown) copy of the ambientCG albedo for the web GLB."""
    dst = TEX + '/gen/kraft_albedo_1k.png'
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im = bpy.data.images.load(src)
        a = np.empty(len(im.pixels), np.float32)
        im.pixels.foreach_get(a)
        a = a.reshape(-1, 4)
        lum = (a[:, :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32))
        lum = lum / lum.mean()
        a[:, :3] = lum[:, None] * np.array([0.50, 0.34, 0.19], np.float32)
        out = bpy.data.images.new('kraft_albedo', im.size[0], im.size[1])
        out.pixels.foreach_set(a.ravel())
        out.filepath_raw, out.file_format = dst, 'PNG'
        out.save()
        bpy.data.images.remove(out)
        bpy.data.images.remove(im)
    return dst


def _text_mesh(name, body, size, mat, parent, loc, face_yaw, coll=None, extrude=0.0):
    """Text -> mesh object placed flat on a face whose outward normal has yaw face_yaw (0 = -Y, 180 = +Y, 90 = +X)."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body, cu.size, cu.align_x, cu.align_y = body, size, 'CENTER', 'CENTER'
    cu.extrude = extrude
    tmp = new_obj(name + '_tmp', cu, coll)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg), depsgraph=dg)
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.name = name
    ob = new_obj(name, me, coll, parent, loc, (math.pi / 2, 0, face_yaw * D2R))
    mat_to(ob, mat)
    return ob


def _quad_on_face(bm, center, w, h, face_yaw, mi=0):
    """Flat rectangle (w x h) on a vertical face; same orientation convention as _text_mesh."""
    R = Euler((math.pi / 2, 0, face_yaw * D2R)).to_matrix()
    c = Vector(center)
    vs = [bm.verts.new(c + R @ Vector((x, y, 0))) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    f = bm.faces.new(vs)
    f.material_index = mi
    return f


def _carton_body(name, mats, coll, parent, lite):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, CH / 2)) @ Matrix.Diagonal((CW, CD, CH, 1)))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3 if lite else 6, use_grid_fill=True)
    top = [f for f in bm.faces if f.normal.z > 0.9 and f.calc_center_median().z > CH - 1e-4]
    bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
    for v in bm.verts:     # slight outward bulge of the walls (filled carton), corners stay put
        x, y, z = v.co
        sv = math.sin(math.pi * min(1, max(0, z / CH)))
        if abs(abs(x) - CW / 2) < 1e-4:
            v.co.x += math.copysign(0.003, x) * math.sin(math.pi * (y / CD + 0.5)) * sv
        elif abs(abs(y) - CD / 2) < 1e-4:
            v.co.y += math.copysign(0.004, y) * math.sin(math.pi * (x / CW + 0.5)) * sv
    ob = _mesh_obj(name, bm, coll, parent)
    mat_to(ob, mats['kraft'], mats['edge'])
    if lite:
        box_uv(ob, 0.30)
    so = ob.modifiers.new('Solidify', 'SOLIDIFY')
    so.thickness, so.offset, so.use_rim, so.material_offset_rim = CT, -1.0, True, 1
    if not lite:
        bevel(ob, 0.0025, 2, 50)
    return ob


def _flap(name, L, F, mats, coll, hinge, lite, up=False):
    """Flap mesh in hinge space: x along hinge, z away from hinge, thickness toward -y (or +y for major flaps)."""
    bm = bmesh.new()
    y0, y1 = (0.0, CT) if up else (-CT, 0.0)
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, (y0 + y1) / 2, F / 2)) @ Matrix.Diagonal((L, CT, F, 1)))
    for f in bm.faces:      # the four thin sides are cut board
        f.material_index = 0 if abs(f.normal.y) > 0.9 else 1
    ob = _mesh_obj(name, bm, coll, hinge)
    mat_to(ob, mats['kraft'], mats['edge'])
    if lite:
        box_uv(ob, 0.30)
    else:
        bevel(ob, 0.0015, 2, 50)
    return ob


def _flap_angle_expr(major):
    # closed = +90 deg (folded in), open = -35/-25 deg (leaning outward); majors open first, minors follow
    return ('radians(90) - radians(125)*min(max(o/0.6, 0), 1)' if major else
            'radians(90) - radians(115)*min(max((o - 0.35)/0.65, 0), 1)')


def _flap_angle(major, o):
    if major:
        return (90 - 125 * min(max(o / 0.6, 0), 1)) * D2R
    return (90 - 115 * min(max((o - 0.35) / 0.65, 0), 1)) * D2R


def _shrimp_bm(bm, M, rng, mi=0):
    """One headless shrimp: tapered, segmented curled tube + tail fan, transformed by M."""
    R0, sweep, n_seg, n_ring = 0.016 * rng.uniform(0.9, 1.1), rng.uniform(3.4, 4.2), 12, 6
    rings = []
    for i in range(n_seg + 1):
        t = i / n_seg
        a = sweep * t
        p = Vector((R0 * math.cos(a), R0 * math.sin(a), 0))
        rad = Vector((math.cos(a), math.sin(a), 0))
        r = (0.0082 * (1 - t) ** 0.8 + 0.0024) * (1 + 0.14 * abs(math.sin(t * math.pi * 6)))
        ring = []
        for j in range(n_ring):
            ph = 2 * math.pi * j / n_ring
            off = rad * (math.cos(ph) * r * 0.9) + Vector((0, 0, math.sin(ph) * r * 1.1))
            ring.append(bm.verts.new(M @ (p + off)))
        rings.append(ring)
    for i in range(n_seg):
        for j in range(n_ring):
            f = bm.faces.new((rings[i][j], rings[i][(j + 1) % n_ring], rings[i + 1][(j + 1) % n_ring], rings[i + 1][j]))
            f.material_index = mi
    for ring in (rings[0], rings[-1][::-1]):
        f = bm.faces.new(ring[::-1])
        f.material_index = mi
    a = sweep
    tip = Vector((R0 * math.cos(a), R0 * math.sin(a), 0))
    tan = Vector((-math.sin(a), math.cos(a), 0))
    for s in (-1, 1):      # tail fan
        vs = [bm.verts.new(M @ q) for q in (tip, tip + tan * 0.012 + Vector((0, 0, s * 0.006)),
                                             tip + tan * 0.016 + Vector((0, 0, s * 0.001)))]
        f = bm.faces.new(vs)
        f.material_index = mi


def _ice_mats():
    glaze = bpy.data.materials.get('ice_glaze')
    if not glaze:     # thin clear glaze shell: glossy coat, see-through, frost patches whiter/rougher/more opaque
        glaze, nt = _new_mat('ice_glaze')
        out = _n(nt, 'ShaderNodeOutputMaterial', 1000, 0)
        b = _n(nt, 'ShaderNodeBsdfPrincipled', 700, 0)
        _l(nt, b.outputs[0], out.inputs['Surface'])
        tc = _n(nt, 'ShaderNodeTexCoord', -800, 0)
        fr = _noise(nt, tc.outputs['Object'], 22.0, 10.0, 0.72, -600, 0)
        fm = _maprange(nt, fr.outputs['Fac'], 0.56, 0.78, 0.0, 1.0, -350, 0)
        _l(nt, _maprange(nt, fm, 0, 1, 0.03, 0.5, -100, 0), b.inputs['Roughness'])
        _l(nt, _mix(nt, fm, (0.82, 0.86, 0.88), (0.95, 0.96, 0.97), 'MIX', -100, 250), b.inputs['Base Color'])
        _l(nt, _maprange(nt, fm, 0, 1, 0.06, 0.7, -100, -150), b.inputs['Alpha'])
        b.inputs['IOR'].default_value = 1.31
        b.inputs['Coat Weight'].default_value = 0.6
        b.inputs['Coat Roughness'].default_value = 0.03
        bn = _noise(nt, tc.outputs['Object'], 70.0, 4.0, 0.5, -600, -400)
        bp = _n(nt, 'ShaderNodeBump', 300, -350)
        bp.inputs['Strength'].default_value = 0.35
        bp.inputs['Distance'].default_value = 0.0015
        _l(nt, bn.outputs['Fac'], bp.inputs['Height'])
        _l(nt, bp.outputs[0], b.inputs['Normal'])
        _l(nt, bp.outputs[0], b.inputs['Coat Normal'])
        glaze.use_transparent_shadow = True
    core = flat('ice_core', (0.22, 0.26, 0.29), rough=0.3, var=0.2, scale=35, bump=0.15,
                **{'Subsurface Weight': 0.25, 'Subsurface Radius': (0.05, 0.07, 0.1), 'Subsurface Scale': 0.01,
                   'Coat Weight': 0.4})
    shrimp = flat('shrimp_raw_frozen', (0.47, 0.31, 0.27), rough=0.3, var=0.3, scale=140, bump=0.25,
                  **{'Subsurface Weight': 0.35, 'Subsurface Radius': (0.08, 0.03, 0.02), 'Subsurface Scale': 0.01})
    bag = flat('poly_bag_frosted', (0.88, 0.9, 0.92), rough=0.3, var=0.05, scale=60, bump=0.2,
               **{'Alpha': 0.72, 'Subsurface Weight': 0.3, 'Coat Weight': 0.5})
    bag.use_transparent_shadow = True
    return glaze, shrimp, bag, core


def _shrimp_block(name, size, c, coll, parent, rng, lite):
    """Glazed 2 kg block: clear/frosty glaze box with ~18 curled shrimp frozen inside."""
    sx, sy, sz = size
    bm = bmesh.new()
    _bm_box(bm, Vector((0, 0, sz / 2)), (sx, sy, sz))
    ob = _mesh_obj(name, bm, coll, parent)
    ob.location = c
    glaze, shrimp, _, core = _ice_mats()
    if lite:
        mat_to(ob, _lite_block_mat(), uv=False)
        box_uv(ob, max(sx, sy))
        bevel(ob, 0.006, 2, 50)
        return ob
    mat_to(ob, glaze)
    bevel(ob, 0.008, 3, 50)
    bm = bmesh.new()       # frozen-water core between the shrimp (top layer of shrimp half-embedded in it)
    _bm_box(bm, Vector((0, 0, (0.004 + sz - 0.009) / 2)), (sx - 0.012, sy - 0.012, sz - 0.013))
    co = _mesh_obj(name + '_core', bm, coll, ob)
    mat_to(co, core)
    bevel(co, 0.006, 2, 50)
    bm = bmesh.new()
    for n, z in ((3, sz * 0.35), (4, sz - 0.016), (5, sz - 0.0115)):     # hidden lower layer + dense top layers
        for i in range(n):
            for j in range(n):
                k = 0.78 / n
                p = Vector(((i - (n - 1) / 2) * sx * k + rng.uniform(-0.006, 0.006),
                            (j - (n - 1) / 2) * sy * k + rng.uniform(-0.006, 0.006), z + rng.uniform(-0.002, 0.002)))
                M = Matrix.Translation(p) @ Euler((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15),
                                                    rng.uniform(0, 6.28))).to_matrix().to_4x4()
                _shrimp_bm(bm, M, rng)
    sh = _mesh_obj(name + '_shrimp', bm, coll, ob)
    mat_to(sh, shrimp)
    sh.data.shade_smooth()
    return ob


def _lite_block_mat():
    """Web block material: generated texture of shrimp curls under frosty glaze (numpy-painted, no AI)."""
    m = bpy.data.materials.get('glb_shrimp_block')
    if m:
        return m
    path = TEX + '/gen/shrimp_block_512.png'
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        N = 512
        rng = np.random.default_rng(41)
        yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
        img = np.zeros((N, N, 3), np.float32) + np.array([0.70, 0.74, 0.78], np.float32)
        for _ in range(26):
            cx, cy = rng.uniform(0, N, 2)
            R = rng.uniform(26, 40)
            a0 = rng.uniform(0, 2 * np.pi)
            dx, dy = xx - cx, yy - cy
            dx, dy = (dx + N / 2) % N - N / 2, (dy + N / 2) % N - N / 2     # tileable
            d = np.sqrt(dx * dx + dy * dy)
            ang = (np.arctan2(dy, dx) - a0) % (2 * np.pi)
            t = ang / 4.0
            w = (11 * (1 - np.clip(t, 0, 1)) ** 0.8 + 3) * (1 + 0.12 * np.abs(np.sin(t * np.pi * 6)))
            body = (np.abs(d - R) < w) & (t < 1.0)
            shade = np.clip(1 - np.abs(d - R) / np.maximum(w, 1), 0, 1) ** 0.5
            col = np.array([0.66, 0.50, 0.46], np.float32) * (0.75 + 0.35 * shade[..., None])
            img = np.where(body[..., None], col, img)
        frost = rng.random((N // 8, N // 8)).repeat(8, 0).repeat(8, 1)[..., None].astype(np.float32)
        img = img * 0.62 + np.array([0.86, 0.9, 0.94], np.float32) * (0.30 + 0.08 * frost)
        im = bpy.data.images.new('shrimp_block', N, N)
        im.pixels.foreach_set(np.concatenate([img, np.ones((N, N, 1))], 2)[::-1].astype(np.float32).ravel())
        im.filepath_raw, im.file_format = path, 'PNG'
        im.save()
        bpy.data.images.remove(im)
    m, nt = _new_mat('glb_shrimp_block')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 0, 0)
    _l(nt, b.outputs[0], _n(nt, 'ShaderNodeOutputMaterial', 300, 0).inputs['Surface'])
    _l(nt, _img(nt, path, True, None, -300, 0).outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.18
    b.inputs['Coat Weight'].default_value = 1.0
    return m


def hero_carton(open_amount=0.0, name='A-HERO-CARTON', coll=None, interior=True, lite=False, loc=(0, 0, 0), rot_z=0.0,
                seed=7):
    """A-HERO-CARTON: 0.50 x 0.35 x 0.25 m double-wall kraft export carton, origin at base centre.
    Root empty carries custom property 'open' (0 closed .. 1 open) that drives the 4 hinged flaps (simple-expression
    drivers, render-safe). White print panels with 'SKYLARK EXIM' / 'VISAKHAPATNAM · INDIA', end panels 'VANNAMEI',
    cut tape halves on the major flaps, corrugated cut edges, frosted inner poly bag, 6 glazed shrimp blocks.
    Animate with carton_key_open(root, f0, f1). Returns the root empty."""
    coll = coll or bpy.context.scene.collection
    rng = random.Random(seed)
    mats = _carton_mats(lite)
    root = new_obj(name, None, coll, loc=loc, rot=(0, 0, rot_z))
    root.empty_display_size = 0.3
    root['open'] = float(open_amount)
    _carton_body(name + '.body', mats, coll, root, lite)
    hinges = []
    for side, (pos, yaw, L, major) in {
        'N': ((0, CD / 2, CH), 180, CW, True), 'S': ((0, -CD / 2, CH), 0, CW, True),
        'E': ((CW / 2, 0, CH), 90, CD - 2 * CT - 0.002, False), 'W': ((-CW / 2, 0, CH), -90, CD - 2 * CT - 0.002, False)}.items():
        # hinge frame: local +y = outward, local x along the edge
        h = new_obj('%s.hinge_%s' % (name, side), None, coll, root, pos)
        h.empty_display_size = 0.05
        # euler XYZ: the X fold is applied first, then the side yaw about Z
        h.rotation_euler = (_flap_angle(major, open_amount), 0, (yaw + 180) * D2R)
        h['major'] = major
        F = CD / 2 - 0.0015 if major else CD / 2 - 0.006
        fl = _flap('%s.flap_%s' % (name, side), L, F, mats, coll, h, lite, up=major)
        if major:        # cut tape half on the free edge of each major flap
            bm = bmesh.new()
            _bm_box(bm, Vector((0, CT + 0.00025, F - 0.024)), (L + 0.0004, 0.0004, 0.048))
            tp = _mesh_obj('%s.tape_%s' % (name, side), bm, coll, fl)
            mat_to(tp, mats['tape'])
        if not lite:
            fc = h.driver_add('rotation_euler', 0).driver
            fc.type = 'SCRIPTED'
            v = fc.variables.new()
            v.name, v.type = 'o', 'SINGLE_PROP'
            v.targets[0].id, v.targets[0].data_path = root, '["open"]'
            fc.expression = _flap_angle_expr(major)
        hinges.append(h)
    root['hinges'] = [h.name for h in hinges]
    # tape tabs left on the end walls after the tape was cut
    bm = bmesh.new()
    for s in (-1, 1):
        _bm_box(bm, Vector((s * (CW / 2 + 0.0003), 0, CH - 0.03)), (0.0004, 0.048, 0.06))
    tp = _mesh_obj(name + '.tape_tabs', bm, coll, root)
    mat_to(tp, mats['tape'])
    # print: white panels on the long sides + blue flexo ink; VANNAMEI on the ends
    bm = bmesh.new()
    for s, yaw in ((1, 180), (-1, 0)):
        _quad_on_face(bm, (0, s * (CD / 2 + 0.0045), 0.125), 0.42, 0.15, yaw)
    for s, yaw in ((1, 90), (-1, -90)):
        _quad_on_face(bm, (s * (CW / 2 + 0.0035), 0, 0.105), 0.26, 0.085, yaw)
    pn = _mesh_obj(name + '.print_panels', bm, coll, root)
    mat_to(pn, mats['white'])
    if lite:
        box_uv(pn, 0.30)
    ink = mats['ink']
    for s, yaw in ((1, 180), (-1, 0)):
        y = s * (CD / 2 + 0.0050)
        _text_mesh('%s.txt_brand_%d' % (name, s), 'SKYLARK EXIM', 0.048, ink, root, (0, y, 0.150), yaw, coll)
        _text_mesh('%s.txt_city_%d' % (name, s), 'VISAKHAPATNAM · INDIA', 0.022, ink, root, (0, y, 0.088), yaw, coll)
        bm = bmesh.new()      # printed rule lines (no text, no logo)
        _quad_on_face(bm, (0, y, 0.115), 0.36, 0.003, yaw)
        _quad_on_face(bm, (0, y, 0.0585), 0.36, 0.003, yaw)
        ru = _mesh_obj('%s.rules_%d' % (name, s), bm, coll, root)
        mat_to(ru, ink)
    for s, yaw in ((1, 90), (-1, -90)):
        x = s * (CW / 2 + 0.0040)
        _text_mesh('%s.txt_species_%d' % (name, s), 'VANNAMEI', 0.04, ink, root, (x, 0, 0.105), yaw, coll)
    if interior:
        _carton_interior(name, coll, root, rng, lite)
    return root


def _carton_interior(name, coll, root, rng, lite):
    bagm = _ice_mats()[2]
    iw, idp = CW - 2 * CT - 0.004, CD - 2 * CT - 0.004
    top = CH - 0.016
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, (top + CT) / 2)) @
                          Matrix.Diagonal((iw, idp, top - CT, 1)))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=14 if lite else 26, use_grid_fill=True)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9 and f.calc_center_median().z > top - 1e-4],
                     context='FACES_ONLY')
    for v in bm.verts:      # loose film: random inward sag, rim wavy and slightly rolled
        x, y, z = v.co
        k = (z - CT) / (top - CT)
        n = Vector((x / (iw / 2), y / (idp / 2), 0))
        sag = 0.004 * k * (0.5 + 0.5 * math.sin(x * 61 + y * 47 + z * 83))
        if abs(abs(x) - iw / 2) < 1e-4:
            v.co.x -= math.copysign(sag, x)
        if abs(abs(y) - idp / 2) < 1e-4:
            v.co.y -= math.copysign(sag, y)
        v.co.z += 0.006 * k ** 4 * math.sin(x * 37 + y * 53)
    bag = _mesh_obj(name + '.bag', bm, coll, root)
    mat_to(bag, bagm)
    bag.data.shade_smooth()
    if not lite:
        for nm, sc, st in (('sk_bag_folds', 0.06, 0.012), ('sk_bag_creases', 0.012, 0.003)):
            tx = bpy.data.textures.get(nm) or bpy.data.textures.new(nm, 'CLOUDS')
            tx.noise_scale, tx.noise_depth, tx.noise_basis = sc, 2, 'VORONOI_F2_F1' if sc < 0.03 else 'ORIGINAL_PERLIN'
            dm = bag.modifiers.new(nm, 'DISPLACE')
            dm.texture, dm.strength, dm.mid_level, dm.texture_coords = tx, st, 0.5, 'OBJECT'
    # 6 blocks, 3 x 2, top layer near the rim (a hidden fibre pad underneath fills the depth)
    bx, by, bz = 0.152, 0.152, 0.085
    z0 = top - 0.028 - bz
    for i in range(3):
        for j in range(2):
            c = ((i - 1) * (bx + 0.004) + rng.uniform(-0.002, 0.002), (j - 0.5) * (by + 0.006) + rng.uniform(-0.002, 0.002), z0)
            b = _shrimp_block('%s.block_%d%d' % (name, i, j), (bx, by, bz), c, coll, root, rng, lite)
            b.rotation_euler.z = rng.uniform(-0.03, 0.03)
    if not lite:
        bm = bmesh.new()
        _bm_box(bm, Vector((0, 0, (z0 + CT) / 2)), (iw - 0.012, idp - 0.012, z0 - CT - 0.001))
        pad = _mesh_obj(name + '.pad', bm, coll, root)
        mat_to(pad, cardboard_kraft())


def carton_set_open(root, amount):
    root['open'] = float(amount)
    for h in root.get('hinges', []):
        o = bpy.data.objects[h]
        o.rotation_euler.x = _flap_angle(bool(o['major']), amount)


def carton_key_open(root, f0, f1, a0=0.0, a1=1.0):
    """Keyframe the lid opening (root['open'] a0 at f0 -> a1 at f1, Bezier ease)."""
    for f, a in ((f0, a0), (f1, a1)):
        root['open'] = float(a)
        root.keyframe_insert('["open"]', frame=f)


def carton_closed(name='A-CARTON-CLOSED'):
    """Sealed carton (tape over the seam, 2 PP straps) joined into ONE mesh inside an unlinked collection for
    instancing (stacks/pallets). Returns the collection (origin = base centre)."""
    c = bpy.data.collections.get(name)
    if c:
        return c
    c = collection(name)            # build linked (needs depsgraph evaluation), unlink at the end
    root = hero_carton(0.0, name + '_tmp', coll=c, interior=False)
    mats = _carton_mats()
    bm = bmesh.new()
    _bm_box(bm, Vector((0, 0, CH + CT + 0.0003)), (CW + 0.0006, 0.048, 0.0005))
    for x in (-0.13, 0.13):      # straps
        _bm_box(bm, Vector((x, 0, CH / 2 + 0.0035)), (0.012, CD + 0.003, CH + CT + 0.004))
    ex = _mesh_obj(name + '_extra', bm, c, root)
    mat_to(ex, mats['tape'], plastic((0.75, 0.75, 0.72), 0.2, name='strap_pp'))
    for p in ex.data.polygons:
        p.material_index = 0 if abs(p.center.x) > 0.2 or p.center.z > CH + 0.005 and abs(p.center.x) < 0.12 else 1
    bpy.context.view_layer.update()
    obs = [o for o in c.objects if o.type == 'MESH']
    me = join(obs, name)
    for o in list(c.objects):
        bpy.data.objects.remove(o)
    ob = new_obj(name, me, c)
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=50 * D2R)
    bpy.context.scene.collection.children.unlink(c)
    return c


def pallet_mesh(name='A-PALLET'):
    """1.2 x 1.0 x 0.144 m block pallet (9 blocks, 3 stringer boards, 7 top boards), rough sawn wood."""
    bm = bmesh.new()
    for x in (-0.55, 0, 0.55):
        for y in (-0.45, 0, 0.45):
            _bm_box(bm, Vector((x, y, 0.022 + 0.039)), (0.1, 0.1, 0.078))
        _bm_box(bm, Vector((x, 0, 0.011)), (0.1, 1.0, 0.022))
    for y in (-0.45, 0, 0.45):
        _bm_box(bm, Vector((0, y, 0.1 + 0.011)), (1.2, 0.1, 0.022))
    for i in range(7):
        _bm_box(bm, Vector((-0.5225 + i * 0.17417, 0, 0.122 + 0.011)), (0.145, 1.0, 0.022))
    ob = _mesh_obj(name, bm, False)
    mat_to(ob, pbr('pallet_wood', 'wood_planks_grey', wear=0.4, ao_dist=0.1))
    bevel(ob, 0.003, 1, 40)
    return ob


def carton_pallet(name='A-CARTON-PALLET', layers=6):
    """Pallet + 6 layers x 6 closed cartons (3 x 2 per layer, 1.05 x 1.0 m footprint) + stretch-wrap film.
    Returns an unlinked collection for instancing."""
    c = bpy.data.collections.get(name)
    if c:
        return c
    c = collection(name, False)
    cc = carton_closed()
    pal = pallet_mesh(name + '.pallet')
    c.objects.link(pal)
    z0 = 0.144
    for k in range(layers):
        for i in range(3):
            for j in range(2):
                e = instance(cc, (-0.35 + i * 0.35, -0.25 + j * 0.5, z0 + k * (CH + CT + 0.001)), math.pi / 2,
                             '%s.carton_%d%d%d' % (name, k, i, j), c)
    top = z0 + layers * (CH + CT + 0.001)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, (z0 + 0.05 + top - 0.12) / 2 + 0.0)) @
                          Matrix.Diagonal((1.065, 1.015, top - 0.12 - z0 + 0.05, 1)))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.9], context='FACES_ONLY')
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=10, use_grid_fill=False)
    rng = random.Random(3)
    for v in bm.verts:
        v.co.x *= 1 + rng.uniform(0, 0.004)
        v.co.y *= 1 + rng.uniform(0, 0.004)
    wrap = _mesh_obj(name + '.wrap', bm, c)
    film = flat('stretch_film', (0.9, 0.92, 0.93), rough=0.06, var=0.03, scale=8, bump=0.3,
                **{'Alpha': 0.16, 'Coat Weight': 1.0})
    film.use_transparent_shadow = True
    mat_to(wrap, film)
    wrap.data.shade_smooth()
    return c


# ------------------------------------------------------------------------------------------------------------ containers
CONT_COLORS = {      # muted shipping-line-like paints, no logos
    'maroon': (0.30, 0.05, 0.04), 'blue': (0.04, 0.12, 0.30), 'green': (0.06, 0.20, 0.10), 'grey': (0.30, 0.31, 0.31),
    'orange': (0.62, 0.20, 0.04), 'white': (0.75, 0.75, 0.72), 'teal': (0.03, 0.22, 0.24), 'yellow': (0.62, 0.45, 0.06)}
_CONT_MESH = {}


def _container_mesh(kind, length):
    key = (kind, round(length, 3))
    if key in _CONT_MESH and _CONT_MESH[key].name in bpy.data.meshes:
        return _CONT_MESH[key]
    reefer = kind == 'reefer'
    L, W = length, 2.438
    H = 2.896 if reefer else 2.591
    P, M, R, G = 0, 1, 2, 3          # material slots: paint, steel (bars/hardware), black rubber/holes, machinery
    bm = bmesh.new()
    cs = (0.178, 0.162, 0.118)        # corner casting
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (cs[2] / 2, H - cs[2] / 2):
                c = Vector((sx * (L / 2 - cs[0] / 2), sy * (W / 2 - cs[1] / 2), z))
                _bm_box(bm, c, cs, P)
                # oval apertures (side, end, top/bottom) as dark insets
                _bm_box(bm, c + Vector((0, sy * cs[1] / 2, 0)), (0.075, 0.003, 0.045), R)
                _bm_box(bm, c + Vector((sx * cs[0] / 2, 0, 0)), (0.003, 0.06, 0.045), R)
                _bm_box(bm, c + Vector((0, 0, (1 if z > H / 2 else -1) * cs[2] / 2)), (0.11, 0.06, 0.003), R)
            # corner posts
            _bm_box(bm, Vector((sx * (L / 2 - 0.08), sy * (W / 2 - 0.075), H / 2)), (0.15, 0.14, H - 2 * cs[2]), P)
    in_x = L / 2 - 0.16
    for sy in (-1, 1):      # bottom + top side rails
        _bm_box(bm, Vector((0, sy * (W / 2 - 0.05), 0.08)), (L - 2 * cs[0], 0.1, 0.16), P)
        _bm_box(bm, Vector((0, sy * (W / 2 - 0.035), H - 0.045)), (L - 2 * cs[0], 0.07, 0.09), P)
    # side walls (trapezoid corrugation, vertical ribs); reefer = shallow fine fluting
    prof = _corr(2 * in_x, 0.10, 0.008, 0.05, 0.03) if reefer else _corr(2 * in_x, 0.278, 0.036, 0.072, 0.068)
    for sy in (-1, 1):
        y0 = sy * (W / 2 - 0.012)
        _bm_strip(bm, prof, 0.16, H - 0.09, lambda u, d, v, y0=y0, sy=sy: (u - in_x, y0 - sy * d, v), P, flip=sy < 0)
    # roof (shallow transverse pressings on dry boxes)
    rp = [(0.0, 0.0), (2 * in_x, 0.0)] if reefer else _corr(2 * in_x, 0.30, 0.015, 0.15, 0.1)
    _bm_strip(bm, rp, -(W / 2 - 0.07), W / 2 - 0.07, lambda u, d, v: (u - in_x, v, H - 0.012 - d), P, flip=True)
    # floor plate underneath
    _bm_box(bm, Vector((0, 0, 0.13)), (2 * in_x, W - 0.2, 0.02), R)
    # front end (-X)
    fx = -L / 2 + 0.014
    if reefer:
        _bm_box(bm, Vector((-L / 2 + 0.05, 0, H / 2)), (0.02, W - 0.28, H - 0.24), G)      # unit back plate
        _bm_box(bm, Vector((-L / 2 + 0.02, 0, H - 0.6)), (0.06, W - 0.3, 0.06), P)         # frame cross members
        _bm_box(bm, Vector((-L / 2 + 0.02, 0, 0.9)), (0.06, W - 0.3, 0.06), P)
        for yc, zc, wv, hv in ((-0.52, H - 0.33, 0.9, 0.42), (0.52, H - 0.33, 0.9, 0.42)):     # evaporator hatches
            _bm_box(bm, Vector((-L / 2 + 0.035, yc, zc)), (0.02, wv, hv), G)
            for dz in (-0.12, 0.12):
                _bm_box(bm, Vector((-L / 2 + 0.022, yc + wv * 0.38, zc + dz)), (0.02, 0.05, 0.03), M)
        gc = Vector((-L / 2 + 0.03, -0.42, 1.4))     # condenser fan grille: ring + spokes + guard rings
        _bm_cyl(bm, gc, 0.40, 0.04, 'X', 32, G)
        _bm_cyl(bm, gc + Vector((-0.021, 0, 0)), 0.37, 0.004, 'X', 32, R)
        for k in range(4):
            a = k * math.pi / 4
            _bm_box(bm, gc + Vector((-0.03, 0, 0)), (0.012, 0.74 * abs(math.cos(a)) + 0.012, 0.74 * abs(math.sin(a)) + 0.012), M)
        for rr in (0.1, 0.2, 0.29, 0.355):
            for k in range(14):
                a0 = 2 * math.pi * k / 14
                p = gc + Vector((-0.035, rr * math.cos(a0), rr * math.sin(a0)))
                _bm_box(bm, p, (0.008, 0.008 + abs(math.sin(a0)) * rr * 0.46, 0.008 + abs(math.cos(a0)) * rr * 0.46), M)
        _bm_box(bm, Vector((-L / 2 + 0.06, 0.55, 1.35)), (0.16, 0.6, 0.7), P)                    # control box
        _bm_box(bm, Vector((-L / 2 - 0.022, 0.55, 1.35)), (0.004, 0.5, 0.6), G)                  # its door
        _bm_box(bm, Vector((-L / 2 + 0.04, 0.0, 0.5)), (0.06, W - 0.4, 0.5), G)                  # compressor bay louvre
        for z in np.linspace(0.3, 0.7, 7):
            _bm_box(bm, Vector((-L / 2 + 0.005, 0.0, z)), (0.012, W - 0.42, 0.018), M)
        _bm_cyl(bm, Vector((-L / 2 + 0.03, 0.95, 0.35)), 0.05, 0.08, 'X', 12, R)               # power plug socket
    else:
        fp = _corr(W - 0.3, 0.27, 0.045, 0.07, 0.06)
        _bm_strip(bm, fp, 0.16, H - 0.09, lambda u, d, v: (fx + d, u - (W - 0.3) / 2, v), P)
        _bm_box(bm, Vector((-L / 2 + 0.08, 0, H - 0.06)), (0.16, W - 0.3, 0.12), P)
        _bm_box(bm, Vector((-L / 2 + 0.08, 0, 0.08)), (0.16, W - 0.3, 0.16), P)
    # door end (+X): header, sill, 2 leaves, 4 locking bars + cam keepers, guides, handles, hinges, gasket
    dx = L / 2 - 0.07
    _bm_box(bm, Vector((L / 2 - 0.1, 0, H - 0.1)), (0.1, W - 2 * cs[1], 0.2), P)
    _bm_box(bm, Vector((L / 2 - 0.1, 0, 0.1)), (0.1, W - 2 * cs[1], 0.2), P)
    dz0, dz1 = 0.2, H - 0.2
    lw = (W - 0.3) / 2 - 0.006
    for s in (-1, 1):
        yc = s * (lw / 2 + 0.006)
        if reefer:
            _bm_box(bm, Vector((dx, yc, (dz0 + dz1) / 2)), (0.03, lw, dz1 - dz0), P)
        else:
            dp = _corr(lw, lw / 4, 0.035, 0.11, 0.1)
            _bm_strip(bm, dp, dz0, dz1, lambda u, d, v, yc=yc: (dx - d, yc - lw / 2 + u, v), P, flip=True)
            _bm_box(bm, Vector((dx - 0.02, yc, dz0 + 0.04)), (0.05, lw, 0.08), P)
            _bm_box(bm, Vector((dx - 0.02, yc, dz1 - 0.04)), (0.05, lw, 0.08), P)
        for k in range(4):         # hinges on the outer edge
            _bm_cyl(bm, Vector((dx + 0.03, s * (W / 2 - 0.15), dz0 + 0.25 + k * (dz1 - dz0 - 0.5) / 3)), 0.025, 0.12, 'Z', 10, M)
        for f in (0.22, 0.72):    # locking bars
            by = s * (0.006 + lw * f)
            bxp = dx + 0.045
            _bm_cyl(bm, Vector((bxp, by, (0.06 + H - 0.06) / 2)), 0.0135, H - 0.14, 'Z', 10, M)
            for zc in (0.11, H - 0.11):     # cam + keeper
                _bm_box(bm, Vector((bxp, by, zc)), (0.05, 0.05, 0.07), M)
                _bm_box(bm, Vector((bxp - 0.015, by, zc + (0.045 if zc < 1 else -0.045))), (0.09, 0.09, 0.02), M)
            for zc in (0.6, 1.7, H - 0.6):      # guides
                _bm_box(bm, Vector((bxp - 0.01, by, zc)), (0.05, 0.05, 0.04), M)
            hz = 1.15 if f > 0.5 else 1.05      # handle
            _bm_box(bm, Vector((bxp + 0.025, by - s * 0.17, hz)), (0.025, 0.34, 0.03), M)
            _bm_box(bm, Vector((bxp + 0.012, by, hz)), (0.04, 0.06, 0.07), M)
    _bm_box(bm, Vector((dx, 0, (dz0 + dz1) / 2)), (0.02, 0.016, dz1 - dz0), R)     # centre gasket
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    me = bpy.data.meshes.new('MESH_CONT_%s_%dft' % (kind, round(length / 0.3048)))
    bm.to_mesh(me)
    bm.free()
    for _ in range(4):
        me.materials.append(None)
    tmp = bpy.data.objects.new('tmp_cont', me)
    bpy.context.scene.collection.objects.link(tmp)
    box_uv(tmp)
    bevel(tmp, 0.01, 1, 40)
    apply_mods(tmp)
    me = tmp.data
    me.name = 'MESH_CONT_%s_%dft' % (kind, round(length / 0.3048))
    bpy.data.objects.remove(tmp)
    _CONT_MESH[key] = me
    return me


def _container(kind, length, color, weather, name, coll):
    if isinstance(color, str):
        color = CONT_COLORS[color]
    me = _container_mesh(kind, length)
    ob = bpy.data.objects.new(name, me)
    if coll is not False:
        link(ob, coll)
    w = round(weather, 2)
    rf = kind == 'reefer'
    mats = (painted_metal(color, (0.1 + 0.4 * w) if rf else (0.12 + 0.6 * w), (0.5 if rf else 0.8) * w,
                          0.35 if rf else 0.6), galvanised(0.2 + 0.5 * w),
            plastic((0.02, 0.02, 0.02), 0.2, name='rubber_black'),
            painted_metal((0.55, 0.57, 0.58), 0.1 + 0.3 * w, 0.2 * w, 0.4) if rf else galvanised())
    for i, m in enumerate(mats):
        ob.material_slots[i].link = 'OBJECT'
        ob.material_slots[i].material = m
    return ob


def container_40(kind='dry', color='maroon', weather=0.3, name=None, coll=None):
    """ISO 40-ft box, 12.192 x 2.438 x 2.591 m (reefer = 40HC 2.896 m), origin at base centre, doors at +X.
    Real trapezoid corrugation, corner castings with apertures, door end with 4 locking bars + cam keepers;
    reefer: fine-fluted white walls + machinery front (fan grille, control box, louvres). Mesh is shared per kind
    (materials are per object) so hundreds of copies stay cheap. color: name in CONT_COLORS or RGB."""
    if kind == 'reefer' and color == 'maroon':
        color = 'white'
    return _container(kind, 12.192, color, weather, name or ('A-CONT-40RF' if kind == 'reefer' else 'A-CONT-40DRY'), coll)


def container_20(kind='dry', color='blue', weather=0.3, name=None, coll=None):
    """ISO 20-ft box 6.058 x 2.438 x 2.591 m (same construction as container_40)."""
    return _container(kind, 6.058, color, weather, name or 'A-CONT-20DRY', coll)


def container_collection_variants(weathers=(0.15, 0.6), with_20=False):
    """Unlinked collections for collection-instancing: 8 colours x weathering levels of the 40-ft dry box, plus white
    reefers at the same weathering levels (and 20-ft dry boxes if with_20). Use sklib.instance(coll, loc, rot_z)."""
    out = []
    for cname in CONT_COLORS:
        for w in weathers:
            for length, fn in ((40, container_40),) + (((20, container_20),) if with_20 else ()):
                nm = 'A-CONT-%dDRY_%s_w%02d' % (length, cname, w * 100)
                c = bpy.data.collections.get(nm)
                if not c:
                    c = collection(nm, False)
                    fn('dry', cname, w, nm + '.obj', c)
                out.append(c)
    for w in weathers:
        nm = 'A-CONT-40RF_white_w%02d' % (w * 100)
        c = bpy.data.collections.get(nm)
        if not c:
            c = collection(nm, False)
            container_40('reefer', 'white', w, nm + '.obj', c)
        out.append(c)
    return out


# ------------------------------------------------------------------------------------------------------- crates and ice
def crate(color=(0.05, 0.22, 0.55), name='A-CRATE-FISH', coll=None, wear=0.3):
    """Perforated, slightly tapered HDPE fish crate 0.60 x 0.40 x 0.25 m with slot holes, hand holes and a rolled
    rim. Origin base centre. Returns the object (~6k tris)."""
    Lx, Ly, Hz, t = 0.60, 0.40, 0.25, 0.005
    bm = bmesh.new()

    def wall(Lu, mapper, hand):
        us = [0.0]
        for i in range(int((Lu - 0.06) / 0.03)):
            u0 = 0.03 + 0.0075 + i * 0.03
            us += [u0, u0 + 0.015]
        us.append(Lu)
        vs = [0.0, 0.03, 0.08, 0.095, 0.145, 0.16, 0.2, Hz]
        grid = [[bm.verts.new(mapper(u, v)) for v in vs] for u in us]
        for i in range(len(us) - 1):
            for j in range(len(vs) - 1):
                uc, vc = (us[i] + us[i + 1]) / 2, (vs[j] + vs[j + 1]) / 2
                hole = (i % 2 == 1) and j in (1, 3, 5) and 0.03 < us[i] < Lu - 0.035
                if hand and j == 5 and Lu / 2 - 0.07 < uc < Lu / 2 + 0.07:
                    hole = False
                if hand and j == 6 and Lu / 2 - 0.06 < uc < Lu / 2 + 0.06:
                    hole = True          # hand hole
                if hole:
                    continue
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))

    tap = lambda z: 1 - 0.035 * (1 - z / Hz)
    wall(Lx, lambda u, v: Vector(((u - Lx / 2) * tap(v), -Ly / 2 * tap(v), v)), False)
    wall(Lx, lambda u, v: Vector((-(u - Lx / 2) * tap(v), Ly / 2 * tap(v), v)), False)
    wall(Ly, lambda u, v: Vector((Lx / 2 * tap(v), (u - Ly / 2) * tap(v), v)), True)
    wall(Ly, lambda u, v: Vector((-Lx / 2 * tap(v), -(u - Ly / 2) * tap(v), v)), True)
    # perforated floor
    xs = np.linspace(-Lx / 2 * tap(0), Lx / 2 * tap(0), 25)
    ys = np.linspace(-Ly / 2 * tap(0), Ly / 2 * tap(0), 17)
    g = [[bm.verts.new((x, y, 0.0)) for y in ys] for x in xs]
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if i % 3 == 1 and j % 3 == 1 and 0 < i < len(xs) - 2 and 0 < j < len(ys) - 2:
                continue
            bm.faces.new((g[i][j], g[i + 1][j], g[i + 1][j + 1], g[i][j + 1]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # rolled rim and base skid ring
    for z, h, o in ((Hz - 0.012, 0.024, 0.012), (0.008, 0.016, 0.004)):
        tz = tap(z)
        for sx in (-1, 1):
            _bm_box(bm, Vector((sx * (Lx / 2 * tz + o / 2), 0, z)), (o + t, Ly * tz + 2 * o, h))
        for sy in (-1, 1):
            _bm_box(bm, Vector((0, sy * (Ly / 2 * tz + o / 2), z)), (Lx * tz + 2 * o, o + t, h))
    ob = _mesh_obj(name, bm, coll)
    mat_to(ob, plastic(color, wear))
    so = ob.modifiers.new('Solidify', 'SOLIDIFY')
    so.thickness, so.offset = t, 0
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=50 * D2R)
    ob.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL').keep_sharp = True
    return ob


def _ice_chunk_mat():
    m = bpy.data.materials.get('ice_crushed')
    if m:
        return m
    m, nt = _new_mat('ice_crushed')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -700, 0)
    fr = _noise(nt, tc.outputs['Object'], 60.0, 8.0, 0.7, -500, 0)
    fm = _maprange(nt, fr.outputs['Fac'], 0.42, 0.66, 0.0, 1.0, -300, 0)
    _l(nt, _maprange(nt, fm, 0, 1, 0.03, 0.3, -100, 0), b.inputs['Roughness'])
    _l(nt, _mix(nt, fm, (0.82, 0.9, 0.96), (0.95, 0.97, 1.0), 'MIX', -100, 250), b.inputs['Base Color'])
    _l(nt, _maprange(nt, fm, 0, 1, 0.9, 0.45, -100, -150), b.inputs['Transmission Weight'])
    b.inputs['Coat Weight'].default_value = 0.6
    b.inputs['IOR'].default_value = 1.31
    b.inputs['Subsurface Weight'].default_value = 0.3
    b.inputs['Subsurface Radius'].default_value = (0.02, 0.03, 0.05)
    b.inputs['Subsurface Scale'].default_value = 0.02
    bp = _n(nt, 'ShaderNodeBump', 300, -350)
    bp.inputs['Strength'].default_value = 0.3
    _l(nt, fr.outputs['Fac'], bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    return m


def crushed_ice_fill(target, density=1.0, name='A-ICE-CRUSHED', coll=None, seed=1, chunk=0.022, mound=0.025,
                     max_chunks=2500, depth=0.07):
    """Crushed ice chunks as ONE mesh. target = object (fills the inside of its local bounding box up to just below
    the rim, following its rotation; the ice object is parented to it) or world bounds (x0, x1, y0, y1, z0, z1).
    density 1 ~ a dense pile 'depth' thick with a low mound in the middle; chunk = typical chunk radius (m)."""
    W = Matrix()
    if isinstance(target, bpy.types.Object):
        bb = [Vector(c) for c in target.bound_box]
        x0, x1 = min(v.x for v in bb) + 0.035, max(v.x for v in bb) - 0.035
        y0, y1 = min(v.y for v in bb) + 0.035, max(v.y for v in bb) - 0.035
        z1 = max(v.z for v in bb) - 0.035
        z0 = z1 - depth
    else:
        x0, x1, y0, y1, z0, z1 = target
    rng = random.Random(seed)
    vol = (x1 - x0) * (y1 - y0) * max(z1 - z0, chunk)
    n = min(max_chunks, int(density * vol / (1.4 * chunk) ** 3))
    protos = []
    for k in range(6):     # irregular, faceted chunk prototypes
        b = bmesh.new()
        bmesh.ops.create_icosphere(b, subdivisions=1, radius=1.0)
        for v in b.verts:
            v.co *= rng.uniform(0.7, 1.15)
        bmesh.ops.scale(b, vec=(rng.uniform(0.9, 1.4), rng.uniform(0.7, 1.1), rng.uniform(0.45, 0.8)), verts=b.verts[:])
        protos.append(([v.co.copy() for v in b.verts], [[v.index for v in f.verts] for f in b.faces]))
        b.free()
    bm = bmesh.new()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r2 = ((x - cx) / ((x1 - x0) / 2)) ** 2 + ((y - cy) / ((y1 - y0) / 2)) ** 2
        z = rng.uniform(z0, z1) + mound * max(0.0, 1 - r2)
        s = chunk * rng.uniform(0.5, 1.3)
        M = Matrix.Translation((x, y, z)) @ Euler([rng.uniform(0, 6.3) for _ in range(3)]).to_matrix().to_4x4() @ \
            Matrix.Diagonal((s, s, s, 1))
        vs, fs = protos[i % len(protos)]
        nv = [bm.verts.new(M @ c) for c in vs]
        for f in fs:
            bm.faces.new([nv[j] for j in f])
    ob = _mesh_obj(name, bm, coll)
    if isinstance(target, bpy.types.Object):
        ob.parent = target
    mat_to(ob, _ice_chunk_mat(), uv=False)
    return ob


# ------------------------------------------------------------------------------------------------------------- ocean
def ocean(size=200.0, seed=41, time=0.0, choppy=1.2, foam=True, wave_scale=1.0, wind=12.0, res=12, animate=False,
          name='A-ENV-SEA', coll=None, deep=(0.006, 0.030, 0.034), shallow=(0.02, 0.11, 0.10)):
    """Ocean modifier (seed 41) plane of ~size metres centred on the origin. Shader: Fresnel glossy reflection of the
    sky over a dark blue-green body (emission-based scattering, so the sea catches no diffuse 'floor' shadow),
    lighter green in wave crests, foam from the modifier foam layer. animate=True drives time with frame/24."""
    me = bpy.data.meshes.new(name)
    ob = new_obj(name, me, coll)
    m = ob.modifiers.new('Ocean', 'OCEAN')
    m.geometry_mode = 'GENERATE'
    m.spatial_size = 50
    m.repeat_x = m.repeat_y = max(1, int(round(size / 50)))
    m.resolution, m.viewport_resolution = res, 6
    m.random_seed, m.time, m.choppiness, m.wave_scale, m.wind_velocity = seed, time, choppy, wave_scale, wind
    m.use_normals = True
    if foam:
        m.use_foam, m.foam_layer_name, m.foam_coverage = True, 'foam', 0.25
    if animate:
        d = m.driver_add('time').driver
        d.type, d.expression = 'SCRIPTED', 'frame/24 + %g' % time
    ob.location = (-size / 2, -size / 2, 0)
    mat, nt = _new_mat(name + '_water')
    out = _n(nt, 'ShaderNodeOutputMaterial', 1200, 0)
    gl = _n(nt, 'ShaderNodeBsdfGlossy', 300, 200)
    gl.inputs['Roughness'].default_value = 0.035
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    rn = _noise(nt, tc.outputs['Object'], 0.15, 4.0, 0.5, -700, 300)    # patchy wind roughness
    _l(nt, _maprange(nt, rn.outputs['Fac'], 0.35, 0.65, 0.02, 0.07, -400, 300), gl.inputs['Roughness'])
    geo = _n(nt, 'ShaderNodeNewGeometry', -900, -300)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -700, -300)
    _l(nt, geo.outputs['Position'], sep.inputs[0])
    crest = _maprange(nt, sep.outputs['Z'], -0.2, 1.0 * wave_scale, 0.0, 1.0, -500, -300)
    body = _mix(nt, crest, tuple(deep), tuple(shallow), 'MIX', -250, -200)
    em = _n(nt, 'ShaderNodeEmission', 0, -200)
    em.inputs['Strength'].default_value = 1.0
    _l(nt, body, em.inputs['Color'])
    fr = _n(nt, 'ShaderNodeFresnel', 0, 300)
    fr.inputs['IOR'].default_value = 1.333
    water = _n(nt, 'ShaderNodeMixShader', 550, 0)
    _l(nt, fr.outputs[0], water.inputs[0])
    _l(nt, em.outputs[0], water.inputs[1])
    _l(nt, gl.outputs[0], water.inputs[2])
    sh = water.outputs[0]
    if foam:
        at = _n(nt, 'ShaderNodeAttribute', -500, -600, attribute_name='foam')
        fn = _noise(nt, tc.outputs['Object'], 3.0, 6.0, 0.6, -500, -800)
        fm = _math(nt, 'MULTIPLY', at.outputs['Fac'], _maprange(nt, fn.outputs['Fac'], 0.4, 0.65, 0.0, 1.5, -300, -800),
                   x=-100, y=-600)
        fm = _maprange(nt, fm, 0.15, 0.7, 0.0, 0.95, 100, -600)
        fb = _n(nt, 'ShaderNodeBsdfPrincipled', 550, -500)
        fb.inputs['Base Color'].default_value = (0.85, 0.88, 0.88, 1)
        fb.inputs['Roughness'].default_value = 0.6
        mx = _n(nt, 'ShaderNodeMixShader', 900, 0)
        _l(nt, fm, mx.inputs[0])
        _l(nt, sh, mx.inputs[1])
        _l(nt, fb.outputs[0], mx.inputs[2])
        sh = mx.outputs[0]
    _l(nt, sh, out.inputs['Surface'])
    mat_to(ob, mat, uv=False)
    ob.visible_shadow = False
    return ob


# ------------------------------------------------------------------------------------------------------------- camera
def camera(name='CAM', lens=35.0, loc=(0, -5, 1.6), look_at=(0, 0, 1), sensor=36.0):
    cam = bpy.data.objects.get(name) or new_obj(name, bpy.data.cameras.new(name))
    cam.data.lens, cam.data.sensor_width = lens, sensor
    cam.data.clip_start, cam.data.clip_end = 0.02, 3000
    cam.location = loc
    cam.rotation_euler = (Vector(look_at) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    return cam


def _fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, 'fcurves') and not hasattr(act, 'layers'):
        return list(act.fcurves)
    from bpy_extras import anim_utils
    cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
    return list(cb.fcurves) if cb else []


def ease_keys(*idbs):
    """Bezier + auto-clamped handles on every key of the given datablocks (smooth starts/stops, no overshoot)."""
    for idb in idbs:
        for fc in _fcurves(idb):
            for k in fc.keyframe_points:
                k.interpolation = 'BEZIER'
                k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
            fc.update()


def camera_path(cam, keys):
    """keys = [(frame, location, aim, lens), ...]; aim = a look-at point (3-tuple/Vector) -> camera tracks an animated
    target empty '<cam>_aim' (exact framing between keys), or a mathutils.Euler -> rotation keys.
    lens None = keep. All keys Bezier with auto-clamped handles."""
    use_target = not any(isinstance(k[2], Euler) for k in keys)
    tgt = None
    if use_target:
        tgt = bpy.data.objects.get(cam.name + '_aim') or new_obj(cam.name + '_aim', None)
        tgt.empty_display_size = 0.2
        if not any(c.type == 'TRACK_TO' for c in cam.constraints):
            c = cam.constraints.new('TRACK_TO')
            c.target, c.track_axis, c.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
    prev = None
    for f, loc, aim, lens in keys:
        cam.location = loc
        cam.keyframe_insert('location', frame=f)
        if use_target:
            tgt.location = aim
            tgt.keyframe_insert('location', frame=f)
        else:
            e = aim.copy()
            if prev is not None:
                e.make_compatible(prev)
            cam.rotation_euler = e
            cam.keyframe_insert('rotation_euler', frame=f)
            prev = e
        if lens:
            cam.data.lens = lens
            cam.data.keyframe_insert('lens', frame=f)
    ease_keys(cam, cam.data, *([tgt] if tgt else []))
    return cam


def dof(cam, focus=None, fstop=2.8):
    """Depth of field: focus = object or distance (m)."""
    d = cam.data.dof
    d.use_dof, d.aperture_fstop = True, fstop
    if isinstance(focus, bpy.types.Object):
        d.focus_object = focus
    elif focus is not None:
        d.focus_distance = float(focus)
    return d


# ------------------------------------------------------------------------------------------------------------- finish
LOOKS = {'ext': 'AgX - Medium High Contrast', 'int': 'AgX - Base Contrast', 'cold': 'AgX - Base Contrast',
         'dawn': 'AgX - Medium Low Contrast'}


def scenes_sh(blend):
    """(first, last, light kind, render dir) for a .blend from scripts/scenes.sh (single source of truth)."""
    lo = hi = k = d = None
    for line in open(REPO + '/scripts/scenes.sh'):
        m = re.match(r'\s*"([^|"]+)\|([^|"]+)\|(\d+)\|(\d+)\|([^|"]+)\|([^|"]+)"', line)
        if m and m.group(2) == blend:
            f, l = int(m.group(3)), int(m.group(4))
            lo, hi = (f, l) if lo is None else (min(lo, f), max(hi, l))
            k, d = k or m.group(6), d or m.group(5)
    return lo, hi, k, d or blend


def render_settings(kind='ext', scene=None):
    s = scene or bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    r = s.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
    r.fps, r.fps_base = 24, 1.0
    r.use_motion_blur = True
    if hasattr(r, 'motion_blur_shutter'):
        r.motion_blur_shutter = 0.5
    r.film_transparent = False
    r.use_overwrite, r.use_placeholder = False, False
    im = r.image_settings
    im.file_format, im.color_mode, im.color_depth, im.compression = 'PNG', 'RGB', '8', 15
    e = s.eevee
    e.taa_render_samples = 64
    e.use_raytracing, e.use_shadows, e.use_fast_gi = True, True, True
    e.ray_tracing_options.resolution_scale = '2'
    e.shadow_ray_count, e.shadow_step_count = 1, 6
    vs = s.view_settings
    vs.view_transform = 'AgX'
    try:                     # dynamic enum: enum_items does not list the AgX looks, so just try
        vs.look = LOOKS.get(kind, 'None')
    except TypeError:
        vs.look = 'None'
    vs.exposure, vs.gamma = 0.0, 1.0
    s.display_settings.display_device = 'sRGB'
    if hasattr(s, 'compositing_node_group'):
        s.compositing_node_group = None
    try:
        s.use_nodes = False
    except Exception:
        pass
    return s


def finish(blend, kind=None):
    """Standard Skylark render settings (EEVEE 1920x1080 24 fps 64 spp, motion blur, AgX look per kind, frame range +
    output dir from scripts/scenes.sh, no compositor) and save to assets-src/blender/<blend>.blend."""
    s = bpy.context.scene
    lo, hi, k, d = scenes_sh(blend)
    kind = kind or k or 'ext'
    render_settings(kind, s)
    if lo is not None:
        s.frame_start, s.frame_end = lo, hi
    s.render.filepath = '//../render/%s/' % d
    path = '%s/blender/%s.blend' % (SRC, blend)
    bpy.ops.wm.save_as_mainfile(filepath=path, relative_remap=True, compress=True)
    print('sklib.finish:', blend, kind, s.view_settings.look, s.frame_start, s.frame_end, '->', path)
    return path


def render_still(path, frame=None, res=(960, 540), samples=None):
    """Test still (use only inside assets-src/tools/render-lock.sh). Returns seconds."""
    import time
    s = bpy.context.scene
    if frame is not None:
        s.frame_set(frame)
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = res[0], res[1], 100
    if samples:
        s.eevee.taa_render_samples = samples
    s.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    print('sklib.render_still %s %.1fs' % (path, dt))
    return dt


# --------------------------------------------------------------------------------------------------------- web GLB
def _export_glb_here(path):
    """Runs in a fresh Blender: lite carton (UV-mapped image PBR, numpy-painted block texture), lid opening keyed
    on the hinge nodes over 48 frames (2 s), exported as one glTF animation 'lid_open'."""
    reset()
    s = bpy.context.scene
    s.name = 'lid_open'
    root = hero_carton(0.0, 'A-HERO-CARTON', lite=True)
    s.frame_start, s.frame_end, s.render.fps = 1, 48, 24
    for hn in root['hinges']:
        h = bpy.data.objects[hn]
        for f in range(1, 49, 3):
            o = (f - 1) / 47.0
            o = o * o * (3 - 2 * o)
            h.rotation_euler.x = _flap_angle(bool(h['major']), o)
            h.keyframe_insert('rotation_euler', index=0, frame=f)
        h.rotation_euler.x = _flap_angle(bool(h['major']), 1.0)
        h.keyframe_insert('rotation_euler', index=0, frame=48)
    tris = sum(sum(len(p.vertices) - 2 for p in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.polygons)
               for o in s.objects if o.type == 'MESH')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_animations=True,
                              export_animation_mode='SCENE', export_anim_scene_split_object=False, export_image_format='WEBP', export_image_quality=80,
                              export_yup=True, export_texcoords=True, export_normals=True)
    print('GLB_TRIS %d SIZE %d %s' % (tris, os.path.getsize(path), path))


def export_carton_glb(path=SRC + '/models/hero-carton.glb'):
    """Web hero carton (<= 15k tris, 1K WebP textures, 2 s lid-open animation) via a separate headless Blender,
    so the current scene is untouched. Returns (path, bytes)."""
    code = 'import sys; sys.path.insert(0, %r); import sklib; sklib._export_glb_here(%r)' % (LIB, path)
    r = subprocess.run([bpy.app.binary_path, '-b', '--factory-startup', '--python-expr', code],
                       capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith('GLB_TRIS')]
    print(line[0] if line else r.stdout[-3000:] + r.stderr[-3000:])
    return path, (os.path.getsize(path) if os.path.exists(path) else 0)
