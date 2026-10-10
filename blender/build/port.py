"""S2 port.blend -> v-port (f1-264, ext). Visakhapatnam container terminal, clear day.
Run:  $B --factory-startup -b --python assets-src/blender/build/port.py          (re-runnable, saves port.blend)
      add '-- nopeople' for a fast layout build without MPFB people.

World layout (metres, Z up, sea level z=0): quay edge along x=0 (land x>0, top z=3), feeder ship berthed along the
quay with its bow to the south (-Y), 3 STS cranes on rails x=10/x=40, yard of straddle stacks x>70, breakwater
along y=-165 (south) and x=-400 (west), headland (Dolphin's Nose-like) south-east of the channel.
Camera: f1 BRIDGE_SEA (top-down sea) -> rise/fly north to the bow -> glide along the ship side on the quay apron ->
3/4 on the middle crane landing the white reefer (contact f204) -> pull back past the canopy desk -> push onto the
rear doors of the truck reefer = BRIDGE_DOOR at f264 (camera looking -X, sun behind camera-left).
"""
import math
import random
import sys
import time

sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector, noise  # noqa: E402

import sklib  # noqa: E402
from sklib import _bm_box as bbox, _bm_cyl as bcyl  # noqa: E402

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
T0 = time.time()
R = random.Random(41)
D2R = math.pi / 180
s = sklib.reset()
s.frame_start, s.frame_end = 1, 264
QZ = 3.0            # quay / yard top
F_END = 264


def log(*a):
    print('[port %5.1fs]' % (time.time() - T0), *a, flush=True)


C = {k: sklib.collection('PORT_' + k) for k in ('ENV', 'QUAY', 'SHIP', 'CRANES', 'YARD', 'VEH', 'PEOPLE')}
C['DOOR'] = sklib.collection('BRIDGE_DOOR')


def mk(name, bm, mats, coll, bev=0.0, seg=2, angle=35):
    ob = sklib._mesh_obj(name, bm, coll)
    mi = [p.material_index for p in ob.data.polygons]
    sklib.mat_to(ob, *mats)
    ob.data.polygons.foreach_set('material_index', mi)     # materials.clear() drops the index attribute
    ob.data.update()
    if bev:
        sklib.bevel(ob, bev, seg, angle)
    else:
        ob.data.shade_smooth()
        ob.data.set_sharp_from_angle(angle=angle * D2R)
    return ob


def obox(bm, p0, p1, w, h, mi=0):
    """Box beam from p0 to p1, cross-section w (horizontal) x h."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    q = d.to_track_quat('X', 'Z') if abs(d.normalized().z) < 0.999 else d.to_track_quat('X', 'Y')
    M = Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((d.length, w, h, 1))
    r = bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    for f in {f for v in r['verts'] for f in v.link_faces}:
        f.material_index = mi


def rod(bm, p0, p1, r, mi=0, seg=8):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    q = d.to_track_quat('Z', 'X' if abs(d.normalized().x) < 0.9 else 'Y')
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length,
                                matrix=Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4())
    for f in {f for v in res['verts'] for f in v.link_faces}:
        f.material_index = mi


def key_loc(ob, f, loc):
    ob.location = loc
    ob.keyframe_insert('location', frame=f)


def linear(*idbs):
    for idb in idbs:
        for fc in sklib._fcurves(idb):
            for k in fc.keyframe_points:
                k.interpolation = 'LINEAR'


def catenary(p0, p1, sag, n=14):
    p0, p1 = Vector(p0), Vector(p1)
    return [p0.lerp(p1, i / (n - 1)) - Vector((0, 0, sag * 4 * (i / (n - 1)) * (1 - i / (n - 1)))) for i in range(n)]


def curve_obj(name, splines, radius, mat, coll):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = '3D', radius, 2
    for pts in splines:
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for p, q in zip(sp.points, pts):
            p.co = (q.x, q.y, q.z, 1)
    ob = sklib.new_obj(name, cu, coll)
    cu.materials.append(mat)
    return ob


# ------------------------------------------------------------------------------------------------ materials
M = dict(
    conc=sklib.concrete_quay(0.45), asph=sklib.asphalt(0.35), galv=sklib.galvanised(0.35), rust=sklib.rusty_metal(0.3),
    rubber=sklib.plastic((0.02, 0.02, 0.02), 0.2, name='rubber_black'),
    hull=sklib.painted_metal((0.27, 0.075, 0.05), 0.55, 0.75, 0.6),
    af=sklib.painted_metal((0.17, 0.035, 0.03), 0.45, 0.4, 0.5),
    deck=sklib.painted_metal((0.10, 0.15, 0.11), 0.55, 0.3, 0.6),
    white=sklib.painted_metal((0.70, 0.70, 0.67), 0.35, 0.5, 0.45),
    crane=sklib.painted_metal((0.14, 0.21, 0.26), 0.55, 0.95, 0.65),
    crane_l=sklib.painted_metal((0.56, 0.58, 0.58), 0.3, 0.45, 0.5),
    yellow=sklib.painted_metal((0.62, 0.44, 0.05), 0.4, 0.35, 0.5),
    black=sklib.painted_metal((0.035, 0.035, 0.035), 0.4, 0.3, 0.5),
    orange=sklib.painted_metal((0.65, 0.18, 0.03), 0.35, 0.3, 0.5),
    red=sklib.painted_metal((0.45, 0.06, 0.04), 0.35, 0.3, 0.5),
    tt=sklib.painted_metal((0.60, 0.40, 0.05), 0.45, 0.35, 0.55),
    cab=sklib.painted_metal((0.74, 0.72, 0.66), 0.35, 0.3, 0.45),
    cabstripe=sklib.painted_metal((0.06, 0.16, 0.42), 0.3, 0.2, 0.5),
    tetra=sklib.pbr('tetrapod_conc', 'concrete_floor_worn_001', tint=(0.66, 0.64, 0.60), wear=0.55, contrast=0.7,
                    wear_color=(0.22, 0.24, 0.2), ao_dist=0.6, scale=0.6),
    rock=sklib.pbr('rock_aerial', 'aerial_rocks_02', wear=0.0, scale=0.25),
    grass=sklib.pbr('grass_scrub', 'sparse_grass', tint=(0.13, 0.20, 0.07), sat=0.35, wear=0.0, scale=4.0, var=0.35),
    wood=sklib.oak_table(0.15), corr=sklib.corrugated_steel((0.62, 0.63, 0.64), 0.35),
    corr_b=sklib.corrugated_steel((0.32, 0.42, 0.5), 0.35),
    rope=sklib.flat('rope_poly', (0.62, 0.52, 0.30), rough=0.85, var=0.15, scale=60, bump=0.4),
    glass=sklib.flat('glass_dark', (0.012, 0.016, 0.02), rough=0.04, var=0.05, scale=5,
                     **{'Specular IOR Level': 0.7, 'Coat Weight': 0.5}),
    foliage=sklib.flat('foliage', (0.07, 0.13, 0.04), rough=0.7, var=0.35, scale=0.6, bump=0.6),
    lamp=sklib.flat('lamp_lens', (0.85, 0.85, 0.8), rough=0.15),
)


def hazed(mat, dist=4500.0, color=(0.62, 0.72, 0.86), strength=1.1):
    """Copy of a material with aerial perspective: mixes toward a sky-haze emission with camera distance."""
    nm = mat.name + '_haze'
    m = bpy.data.materials.get(nm)
    if m:
        return m
    m = mat.copy()
    m.name = nm
    nt = m.node_tree
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    src = out.inputs['Surface'].links[0].from_socket
    cd = nt.nodes.new('ShaderNodeCameraData')
    f = sklib._math(nt, 'MULTIPLY', cd.outputs['View Distance'], -1.0 / dist)
    f = sklib._math(nt, 'EXPONENT', f)
    f = sklib._math(nt, 'SUBTRACT', 1.0, f, True)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = tuple(color) + (1,)
    em.inputs['Strength'].default_value = strength
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(f, mx.inputs[0])
    nt.links.new(src, mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m


# ---- merged instancing: thousands of far copies (tetrapods, trees, far-yard LOD boxes) become one mesh per source,
# which renders far faster in EEVEE than thousands of collection-instance empties.
import numpy as np  # noqa: E402
BATCH = {}


def batch(src_coll, loc, rot, scale=1.0, key=None):
    M4 = Matrix.LocRotScale(Vector(loc), Euler(rot), Vector((scale,) * 3))
    BATCH.setdefault((src_coll.name, key or src_coll.name), []).append(M4)


def realize(name, src, mats, coll):
    me0 = src.data
    n, nl, npl = len(me0.vertices), len(me0.loops), len(me0.polygons)
    V = np.empty(n * 3, np.float32); me0.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    LV = np.empty(nl, np.int32); me0.loops.foreach_get('vertex_index', LV)
    LS = np.empty(npl, np.int32); me0.polygons.foreach_get('loop_start', LS)
    MI = np.empty(npl, np.int32); me0.polygons.foreach_get('material_index', MI)
    uvl = me0.uv_layers.get('UVMap')
    UV = np.zeros(nl * 2, np.float32)
    if uvl:
        uvl.data.foreach_get('uv', UV)
    k = len(mats)
    A = np.array([np.array(m) for m in mats], np.float32)           # k x 4 x 4
    W = np.einsum('kij,nj->kni', A[:, :3, :3], V) + A[:, None, :3, 3]
    me = bpy.data.meshes.new(name)
    me.vertices.add(k * n)
    me.vertices.foreach_set('co', W.reshape(-1))
    me.loops.add(k * nl)
    me.loops.foreach_set('vertex_index', (LV[None, :] + (np.arange(k) * n)[:, None]).reshape(-1))
    me.polygons.add(k * npl)
    me.polygons.foreach_set('loop_start', (LS[None, :] + (np.arange(k) * nl)[:, None]).reshape(-1))
    me.update(calc_edges=True)
    for m in src.material_slots:
        me.materials.append(m.material)
    me.polygons.foreach_set('material_index', np.tile(MI, k))
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', np.tile(UV, k))
    me.validate()
    me.shade_smooth()
    me.set_sharp_from_angle(angle=40 * D2R)
    return sklib.new_obj(name, me, coll)


def realize_all():
    for (cname, key), mats in BATCH.items():
        src = bpy.data.collections[cname].objects[0]
        coll = C['YARD'] if cname.startswith('A-CONT') else C['ENV']
        realize('MERGED.' + key, src, mats, coll)
    BATCH.clear()


def paper_mat():
    m = bpy.data.materials.get('paper_lines')
    if m:
        return m
    m, nt = sklib._new_mat('paper_lines')
    n = sklib._n
    out = n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    tc = n(nt, 'ShaderNodeTexCoord', -900, 0)
    wv = n(nt, 'ShaderNodeTexWave', -600, 0, wave_type='BANDS', bands_direction='Y')
    wv.inputs['Scale'].default_value, wv.inputs['Distortion'].default_value = 140.0, 0.0
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    nz = sklib._noise(nt, tc.outputs['Object'], 90.0, 2.0, 0.5, -600, -250)      # broken 'words'
    ln = sklib._math(nt, 'MULTIPLY', sklib._maprange(nt, wv.outputs['Fac'], 0.82, 0.95, 0, 1, -350, 0),
                     sklib._maprange(nt, nz.outputs['Fac'], 0.45, 0.55, 0, 1, -350, -250), x=-150)
    nt.links.new(sklib._mix(nt, ln, (0.86, 0.86, 0.84), (0.25, 0.27, 0.32), 'MIX', 100, 0), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.8
    return m


def water_flat():
    m = bpy.data.materials.get('puddle')
    if m:
        return m
    m = sklib.flat('puddle', (0.03, 0.03, 0.03), rough=0.03, var=0.1, scale=2)
    return m


# ------------------------------------------------------------------------------------------------ world + sea
sklib.sky_world(sun_elev_deg=52, sun_az_deg=135, sun_angle_deg=3.0)
SUN = bpy.data.objects['SK_Sun']
sky = [n for n in bpy.data.worlds['SK_Sky'].node_tree.nodes if n.type == 'TEX_SKY'][0]


# sun 52 deg (BRIDGE_SEA) -> 40 deg (BRIDGE_DOOR), azimuth fixed 135: rebuild-free keying of node + light
for f, el in ((1, 52.0), (F_END, 40.0)):
    e, a = el * D2R, 135 * D2R
    d = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    SUN.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    SUN.keyframe_insert('rotation_euler', frame=f)
    SUN.data.color = sklib.sun_color(el)
    SUN.data.energy = 6.0 * max(0.15, math.sin(e)) ** 0.5
    SUN.data.keyframe_insert('color', frame=f)
    SUN.data.keyframe_insert('energy', frame=f)
    sky.sun_elevation = e
    sky.keyframe_insert('sun_elevation', frame=f)
linear(SUN, SUN.data, bpy.data.worlds['SK_Sky'].node_tree)

# one Ocean (seed 41, sklib defaults = BRIDGE_SEA); time 0 at f1
# sklib.ocean = 6x6 displaced 100 m tiles around its origin; origin = the BRIDGE_SEA point under the f1 camera
OC = (-90.0, -150.0)
sea = sklib.ocean(size=600.0, seed=41, time=-1 / 24.0, animate=True, res=10, coll=C['ENV'])
sea.location = (OC[0] + sea.location.x, OC[1] + sea.location.y, 0)
far = bpy.data.meshes.new('A-ENV-SEA-FAR')
_h, _o = 7000.0, 299.0
_v = [(-_h, -_h), (_h, -_h), (_h, _h), (-_h, _h),
      (OC[0] - _o, OC[1] - _o), (OC[0] + _o, OC[1] - _o), (OC[0] + _o, OC[1] + _o), (OC[0] - _o, OC[1] + _o)]
far.from_pydata([(x, y, 0) for x, y in _v], [], [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
farob = sklib.new_obj('A-ENV-SEA-FAR', far, C['ENV'], loc=(0, 0, -0.15))
farob.data.materials.append(sea.data.materials[0] if sea.data.materials else bpy.data.materials['A-ENV-SEA_water'])
farob.visible_shadow = False
log('sea')

# ------------------------------------------------------------------------------------------------ land + quay
def slab(name, x0, x1, y0, y1, mat, z0=-12.0, z1=QZ, coll=None, bev=0.25):
    bm = bmesh.new()
    bbox(bm, Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), (x1 - x0, y1 - y0, z1 - z0))
    return mk(name, bm, (mat,), coll or C['QUAY'], bev, 2)


slab('A-PORT-QUAY', 0, 70, -140, 420, M['conc'])
slab('A-PORT-YARD', 70, 520, -140, 420, M['asph'])
slab('A-ENV-LAND-N', -400, 0, 280, 420, M['asph'], coll=C['ENV'])
slab('A-ENV-LAND-FAR', -1500, 2500, 420, 1300, hazed(M['grass']), z1=QZ, coll=C['ENV'], bev=0)
slab('A-ENV-LAND-E', 520, 2500, -140, 420, hazed(M['grass']), coll=C['ENV'], bev=0)

# quay details: capping beam, rails, fenders, bollards, lane markings, puddles
bm = bmesh.new()
bbox(bm, Vector((0.35, 140, QZ + 0.12)), (0.7, 560, 0.24))
for x in (10.0, 40.0):           # crane rails (2 heads per rail)
    for dx in (-0.06, 0.06):
        bbox(bm, Vector((x + dx, 140, QZ + 0.04)), (0.08, 560, 0.08), 1)
mk('A-PORT-QUAYEDGE', bm, (M['conc'], M['galv']), C['QUAY'], 0.02)
bm = bmesh.new()
for y in range(-130, 412, 16):
    bcyl(bm, Vector((-0.8, y, 1.4)), 0.85, 1.6, 'X', 16)
mk('A-PORT-FENDERS', bm, (M['rubber'],), C['QUAY'], 0.04)
bm = bmesh.new()
BOLL = [(1.3, y) for y in range(-128, 412, 15)]
for x, y in BOLL:
    bcyl(bm, Vector((x, y, QZ + 0.3)), 0.32, 0.6, 'Z', 14)
    bcyl(bm, Vector((x - 0.08, y, QZ + 0.66)), 0.44, 0.14, 'Z', 14)
    bcyl(bm, Vector((x, y, QZ + 0.03)), 0.55, 0.06, 'Z', 14)
mk('A-PORT-BOLLARDS', bm, (M['black'],), C['QUAY'], 0.02)
bm = bmesh.new()
for x in (13.6, 36.4, 69.0):
    for y in range(-136, 416, 6):
        bbox(bm, Vector((x, y + 2, QZ + 0.002)), (0.15, 4.0, 0.004))
for y in (15.4, 20.6):            # truck bay box
    bbox(bm, Vector((48, y, QZ + 0.002)), (18, 0.15, 0.004))
mk('A-PORT-MARKINGS', bm, (sklib.pbr('lane_paint', 'asphalt_02', tint=(0.72, 0.55, 0.12), contrast=0.4, wear=0.5),),
   C['QUAY'])
bm = bmesh.new()
rp = random.Random(7)
for i in range(26):               # puddles + oil stains (flat irregular polygons)
    cx, cy = rp.uniform(3, 66), rp.uniform(-90, 30)
    r0 = rp.uniform(0.6, 2.4)
    vs = []
    for k in range(14):
        a = 2 * math.pi * k / 14
        rr = r0 * rp.uniform(0.55, 1.0)
        vs.append(bm.verts.new((cx + rr * math.cos(a) * 1.4, cy + rr * math.sin(a), QZ + 0.004)))
    bm.faces.new(vs)
mk('A-PORT-PUDDLES', bm, (water_flat(),), C['QUAY'])
log('quay')

# ------------------------------------------------------------------------------------------------ breakwater + headland
def tetrapod_coll():
    c = sklib.collection('A-ENV-TETRAPOD', False)
    if c.objects:
        return c
    bm = bmesh.new()
    dirs = [Vector((0, 0, 1)), Vector((0.943, 0, -0.333)), Vector((-0.471, 0.816, -0.333)), Vector((-0.471, -0.816, -0.333))]
    for d in dirs:
        q = d.to_track_quat('Z', 'X' if abs(d.x) < 0.9 else 'Y')
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.62, radius2=0.40, depth=1.7,
                                  matrix=Matrix.Translation(d * 0.85) @ q.to_matrix().to_4x4())
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.01)
    ob = mk('A-ENV-TETRAPOD.mesh', bm, (M['tetra'],), c, 0.05, 1, 40)
    sklib.apply_mods(ob)
    return c


TP = tetrapod_coll()
BW = [((-400, -205), (-55, -205), (0, -1)), ((-400, 280), (-400, -205), (-1, 0))]   # (start, end, seaward normal)
bm = bmesh.new()
nt_ = 0
for (a, b, nrm) in BW:
    a, b, n = Vector((*a, 0)), Vector((*b, 0)), Vector((*nrm, 0))
    t = (b - a).normalized()
    L = (b - a).length
    prof = [(-26, -10), (-4.5, 5.2), (4, 5.2), (20, -10)]      # (offset seaward(-)->harbour(+), z) ; seaward = -n
    steps = int(L / 6) + 1
    rows = []
    for i in range(steps + 1):
        p = a + t * (L * i / steps)
        rows.append([bm.verts.new(p - n * o + Vector((0, 0, z))) for o, z in prof])
    for i in range(steps):
        for j in range(len(prof) - 1):
            bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
    bm.faces.new(rows[0])
    bm.faces.new(rows[-1][::-1])
    # parapet wall on the seaward crest edge
    obox(bm, a + n * 3.6 + Vector((0, 0, 6.2)), b + n * 3.6 + Vector((0, 0, 6.2)), 1.2, 2.2, 0)
    # tetrapods on the seaward slope
    for i in range(int(L / 2.4)):
        for k, (o, z) in enumerate(((5.5, 4.0), (8.3, 2.0), (11.0, 0.3), (13.8, -1.5), (16.5, -3.2))):
            p = a + t * (i * 2.4 + (1.2 if k % 2 else 0) + R.uniform(-0.4, 0.4)) + n * (o + R.uniform(-0.5, 0.5))
            batch(TP, (p.x, p.y, z + R.uniform(-0.3, 0.3)), (R.uniform(-0.6, 0.6), R.uniform(-0.6, 0.6), R.uniform(0, 6.28)),
                  R.uniform(0.95, 1.15), 'A-ENV-TETRAPODS')
            nt_ += 1
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
mk('A-ENV-BREAKWATER', bm, (hazed(M['rock']),), C['ENV'])
bm = bmesh.new()                         # lighthouse at the breakwater head
bcyl(bm, Vector((-58, -205, 9)), 1.6, 8, 'Z', 20, 0, 1.3)
bcyl(bm, Vector((-58, -205, 14)), 1.32, 2.0, 'Z', 20, 1)
bcyl(bm, Vector((-58, -205, 16)), 0.9, 2.0, 'Z', 16, 2)
bcyl(bm, Vector((-58, -205, 17.3)), 1.1, 0.6, 'Z', 16, 1)
mk('A-ENV-LIGHTHOUSE', bm, (M['white'], M['red'], M['glass']), C['ENV'], 0.04)
log('breakwater %d tetrapods' % nt_)


def terrain(name, x0, x1, y0, y1, nx, ny, hfun, coll, rock_slope=0.82):
    bm = bmesh.new()
    vs = [[bm.verts.new((x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, 0)) for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(ny + 1):
            v = vs[i][j]
            v.co.z = hfun(v.co.x, v.co.y)
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        f.material_index = 0 if (f.normal.z > rock_slope and c.z > 2.5) else 1
    ob = mk(name, bm, (hazed(M['grass']), hazed(M['rock'])), coll)
    return ob


def fbm(x, y, s=90.0, o=4):
    v, a, f = 0.0, 1.0, 1.0
    for _ in range(o):
        v += a * noise.noise(Vector((x * f / s, y * f / s, 0.37)))
        a *= 0.5
        f *= 2.1
    return v


def head_h(x, y):
    g = math.exp(-(((x - 270) / 150) ** 2 + ((y + 275) / 105) ** 2))
    h = 135 * g ** 0.8 + 14 * fbm(x, y) * (0.3 + g) - 9
    if y > -165 and x > 30:                     # merge into the terminal land at z=3 toward the north
        k = min(1.0, (y + 165) / 30)
        h = h * (1 - k) + (QZ - 0.4) * k
    return h


HEAD = terrain('A-ENV-HEADLAND', 20, 580, -480, -130, 112, 70, head_h, C['ENV'])
RIDGE = terrain('A-ENV-HILLS-N', -1500, 2500, 1250, 2600, 200, 70,
                lambda x, y: 40 + 230 * max(0, noise.noise(Vector((x / 900, y / 700, 0.2))) + 0.35) + 55 * fbm(x, y, 220, 6)
                * (0.4 + max(0, noise.noise(Vector((x / 900, y / 700, 0.2))) + 0.35)), C['ENV'], 0.7)


def tree_coll():
    c = sklib.collection('A-ENV-TREE', False)
    if c.objects:
        return c
    bm = bmesh.new()
    bcyl(bm, Vector((0, 0, 1.6)), 0.18, 3.2, 'Z', 6, 0)
    rt = random.Random(3)
    for k in range(4):
        r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0,
                                       matrix=Matrix.Translation((rt.uniform(-1, 1), rt.uniform(-1, 1), 3.6 + rt.uniform(0, 1.6)))
                                       @ Matrix.Diagonal((2.1, 2.1, 1.5, 1)))
        for v in r['verts']:
            v.co += Vector((rt.uniform(-.3, .3), rt.uniform(-.3, .3), rt.uniform(-.3, .3)))
            for f in v.link_faces:
                f.material_index = 1
    mk('A-ENV-TREE.mesh', bm, (hazed(M['wood']), hazed(M['foliage'])), c)
    return c


TREE = tree_coll()
nt_ = 0
for i in range(2600):
    x, y = R.uniform(60, 560), R.uniform(-460, -150)
    z = head_h(x, y)
    if z > 6 and noise.noise(Vector((x / 60, y / 60, 3))) > -0.15:
        batch(TREE, (x, y, z - 0.4), (0, 0, R.uniform(0, 6.3)), R.uniform(0.7, 1.5), 'A-ENV-TREES')
        nt_ += 1
log('headland trees %d' % nt_)

# warehouses / sheds east + north (corrugated)
bm = bmesh.new()
for (cx, cy, lx, ly, h) in ((340, -60, 110, 46, 13), (340, 40, 110, 46, 13), (340, 150, 110, 46, 13),
                            (-250, 330, 120, 50, 12), (-100, 340, 80, 40, 10), (420, 300, 90, 60, 15)):
    bbox(bm, Vector((cx, cy, QZ + h / 2)), (lx, ly, h), 0)
    obox(bm, (cx - lx / 2, cy, QZ + h + 1.2), (cx + lx / 2, cy, QZ + h + 1.2), ly * 0.55, 2.4, 1)
mk('A-PORT-SHEDS', bm, (hazed(M['corr']), hazed(M['corr_b'])), C['ENV'], 0.2)
log('sheds')

# ------------------------------------------------------------------------------------------------ containers
VAR = sklib.container_collection_variants((0.15, 0.6))
DRY = [c for c in VAR if 'DRY' in c.name]
REEF = [c for c in VAR if '40RF' in c.name]
CW_, CH_, CL_ = 2.438, 2.591, 12.192


def lod_variant(c):
    """Far-yard LOD: bevelled box with the variant's paint (instanced beyond ~120 m from the camera path)."""
    nm = c.name + '_LOD'
    lc = bpy.data.collections.get(nm)
    if lc:
        return lc
    lc = sklib.collection(nm, False)
    src = c.objects[0]
    h = 2.896 if 'RF' in c.name else CH_
    bm = bmesh.new()
    bbox(bm, Vector((0, 0, h / 2)), (CL_, CW_, h))
    for sx in (-1, 1):                       # door/front frames
        bbox(bm, Vector((sx * (CL_ / 2 - 0.08), 0, h / 2)), (0.16, CW_ + 0.02, h + 0.01))
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.03, segments=1, affect='EDGES', clamp_overlap=True)
    ob = sklib._mesh_obj(nm + '.obj', bm, lc)
    sklib.mat_to(ob, hazed(src.material_slots[0].material))
    return lc


LOD = {c.name: lod_variant(c) for c in VAR}


def pick(rng, reefer_p=0.12):
    return rng.choice(REEF) if rng.random() < reefer_p else rng.choice(DRY)


NCONT = {'ship': 0, 'yard': 0, 'yard_full': 0}

# yard: straddle-carrier rows (containers along Y) with 1.6 m straddle gaps, blocks with cross lanes
YARD_ROWS = [72.0 + i * 4.05 for i in range(40)]
BLOCKS = [-112 + k * 90.8 for k in range(5)]
ry = random.Random(11)
for i, x in enumerate(YARD_ROWS):
    for b0 in BLOCKS:
        for j in range(6):
            y = b0 + 6.4 + j * 12.8
            if y > 405:
                continue
            u = ry.random()
            tiers = 0 if u < 0.12 else (1 if u < 0.3 else (2 if u < 0.58 else (3 if u < 0.86 else 4)))
            full = i < 5 and y < 130
            z = QZ
            for t in range(tiers):
                c = pick(ry)
                loc_ = (x + ry.uniform(-0.03, 0.03), y + ry.uniform(-0.05, 0.05), z)
                rz_ = math.pi / 2 + (math.pi if ry.random() < 0.5 else 0) + ry.uniform(-0.004, 0.004)
                if full:
                    sklib.instance(c, loc_, rz_, 'A-CONT-Y.%d.%d.%d.%d' % (i, int(b0), j, t), C['YARD'])
                else:
                    batch(LOD[c.name], loc_, (0, 0, rz_))
                z += 2.896 if 'RF' in c.name else CH_
                NCONT['yard'] += 1
                NCONT['yard_full'] += full
realize_all()
log('yard containers', NCONT)

# light towers + yard light poles
bm = bmesh.new()
for (x, y) in ((67, -95), (67, -5), (67, 125), (67, 235), (236, -60), (236, 60), (236, 180), (236, 300),
               (74, BLOCKS[0] + 83.8), (74, BLOCKS[2] + 83.8), (74, BLOCKS[3] + 83.8), (150, BLOCKS[1] + 83.8)):
    bcyl(bm, Vector((x, y, QZ + 17)), 0.45, 34, 'Z', 12, 0, 0.28)
    bcyl(bm, Vector((x, y, QZ + 0.4)), 0.9, 0.8, 'Z', 12, 0)
    bbox(bm, Vector((x, y, QZ + 34.3)), (4.4, 1.6, 0.25), 0)
    for k in range(6):
        bbox(bm, Vector((x - 1.8 + k * 0.72, y - 0.5, QZ + 35.0)), (0.6, 0.35, 0.5), 1)
        bbox(bm, Vector((x - 1.8 + k * 0.72, y - 0.69, QZ + 35.0)), (0.5, 0.02, 0.4), 2)
    bbox(bm, Vector((x, y + 0.6, QZ + 34.9)), (4.4, 0.04, 1.0), 0)
mk('A-PORT-LIGHTTOWERS', bm, (M['galv'], M['black'], M['lamp']), C['QUAY'], 0.03)
log('towers')

# ------------------------------------------------------------------------------------------------ feeder ship
SX = -13.5                  # ship centreline x
SL, SB, SD, ST = 150.0, 23.0, 8.5, 7.0


def hull_halfbeam(y, z, L, B, D, T, bow_len, stern_len, rake=0.35):
    yb = -L / 2 + max(0.0, D - z) * rake
    u = (y - yb) / bow_len
    if u <= 0:
        return 0.0
    f = 1.0 if u >= 1 else 1 - (1 - u) ** 2
    if u < 1:
        f = f ** (1 + 0.7 * max(0.0, -z) / T)
    v = (L / 2 - y) / stern_len
    if v < 1:
        f *= 0.8 + 0.2 * math.sqrt(max(v, 0.0))
    return B / 2 * f


def hull_bm(L, B, D, T, bow_len, stern_len, sheer=2.2, Rb=2.2, nst=96):
    bm = bmesh.new()
    rings = []

    def Dz(y):
        return D + sheer * max(0.0, (-L / 2 + 16 - y) / 16)

    for i in range(nst + 1):
        y = -L / 2 + L * i / nst
        d = Dz(y)
        pts = []
        for k in range(9):
            z = d - (d - (-T + Rb)) * k / 8
            pts.append((hull_halfbeam(y, z, L, B, D, T, bow_len, stern_len), z))
        hb = hull_halfbeam(y, -T + Rb, L, B, D, T, bow_len, stern_len)
        r = min(Rb, hb)
        for k in range(1, 6):
            a = math.pi / 2 * k / 5
            pts.append((max(0.0, hb - r + r * math.cos(a)), -T + Rb - r * math.sin(a) if r > 0 else -T))
        for k in range(1, 4):
            pts.append(((hb - r) * (1 - k / 3), -T))
        ring_r = [bm.verts.new((x, y, z)) for x, z in pts]
        ring_l = [bm.verts.new((-x, y, z)) for x, z in pts]
        rings.append((ring_r, ring_l))
    for i in range(nst):
        (ar, al), (br, bl) = rings[i], rings[i + 1]
        for j in range(len(ar) - 1):
            bm.faces.new((ar[j], br[j], br[j + 1], ar[j + 1]))
            bm.faces.new((al[j], al[j + 1], bl[j + 1], bl[j]))
        bm.faces.new((ar[0], al[0], bl[0], br[0]))          # deck strip
    sr, sl = rings[-1]
    bm.faces.new(sr + sl[::-1])     # transom
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.002)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=0.002)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        c = f.calc_center_median()
        f.material_index = 2 if f.normal.z > 0.95 and c.z > D - 0.5 else (1 if c.z < 0.35 else 0)
    return bm, Dz


bm, SDz = hull_bm(SL, SB, SD, ST, 32.0, 14.0)
hull = mk('A-VESSEL-FEEDER.hull', bm, (M['hull'], M['af'], M['deck']), C['SHIP'], 0, angle=40)
hull.location = (SX, 0, 0)

BAYS = [-52.8 + k * 13.2 for k in range(8)]
ROWS = [SX + (k - 3.5) * 2.55 for k in range(8)]
ROWS_Q = sorted(ROWS, reverse=True)      # quay side first
SLOT = (ROWS_Q[2], 0.0)
HZ = SD + 1.0                            # hatch-cover top = container base on deck
SLOT_Z = HZ + 2 * CH_                    # reefer base when landed (on top of tier 2)
rs = random.Random(5)
bm = bmesh.new()          # hatch covers, coamings, lashing bridges, cell guides, rails, rods
STACK = {}
for by in BAYS:
    hb_end = min(hull_halfbeam(by - 6.6, SD, SL, SB, SD, ST, 32, 14), hull_halfbeam(by + 6.6, SD, SL, SB, SD, ST, 32, 14))
    rows = [x for x in ROWS if abs(x - SX) + 1.22 < hb_end - 0.7]
    if not rows:
        continue
    w = max(rows) - min(rows) + CW_ + 0.6
    bbox(bm, Vector(((max(rows) + min(rows)) / 2, by, SD + 0.5)), (w, 12.7, 1.0), 0)        # hatch cover
    for x in rows:
        if by == 0.0 and x >= SLOT[0] - 0.01:
            tiers = 2
        elif by == -13.2 and x > SLOT[0] - 3:
            tiers = 1
        elif by == BAYS[0]:
            tiers = rs.choice([1, 2, 2])
        else:
            tiers = rs.choice([2, 3, 3, 3])
        STACK[(by, x)] = tiers
for by in BAYS[:-1]:
    yg = by + 6.6
    xs = [x for (b, x) in STACK if b == by] + [x for (b, x) in STACK if b == by + 13.2]
    if not xs:
        continue
    x0, x1 = min(xs) - 1.5, max(xs) + 1.5
    z = HZ + CH_
    bbox(bm, Vector(((x0 + x1) / 2, yg, z - 0.03)), (x1 - x0, 0.8, 0.06), 1)          # walkway grating
    for x in [x0 + k * 2.55 for k in range(int((x1 - x0) / 2.55) + 1)]:
        bbox(bm, Vector((x, yg, (SD + z) / 2)), (0.16, 0.16, z - SD), 1)              # support posts
        for sy in (-1, 1):
            bbox(bm, Vector((x, yg + sy * 0.37, z + 0.55)), (0.04, 0.04, 1.1), 1)    # rail stanchions
    for sy in (-1, 1):
        for zz in (z + 0.55, z + 1.1):
            bbox(bm, Vector(((x0 + x1) / 2, yg + sy * 0.37, zz)), (x1 - x0, 0.035, 0.035), 1)
    for (b, x), t in STACK.items():                                               # lashing rods to tier 3
        for side, b_ in ((-1, by + 13.2), (1, by)):
            if b_ == b and t >= 3:
                ye = yg + side * 0.47
                for sx in (-1, 1):
                    rod(bm, (x + sx * 0.75, yg + side * 0.3, z + 0.05), (x + sx * 1.12, ye, HZ + 2 * CH_ + 0.05), 0.016, 1, 6)
                    rod(bm, (x + sx * 0.75, yg + side * 0.3, z + 0.05), (x + sx * 1.12, ye, HZ + CH_ + 0.05), 0.016, 1, 6)
for (by, x), t in STACK.items():           # cell-guide angles at bay ends (hatch top -> tier-1 top)
    for sy in (-1, 1):
        for sx in (-1, 1):
            bbox(bm, Vector((x + sx * 1.18, by + sy * 6.16, HZ + CH_ / 2)), (0.10, 0.012, CH_ - 0.1), 1)
# deck-edge railing + forecastle winches + mast + bow
for side in (-1, 1):
    pts = [(SX + side * (hull_halfbeam(y, SD, SL, SB, SD, ST, 32, 14) - 0.25), y) for y in range(-70, 74, 3)]
    for (x, y) in pts:
        bbox(bm, Vector((x, y, SDz(y) + 0.55)), (0.05, 0.05, 1.1), 1)
    for a, b in zip(pts, pts[1:]):
        obox(bm, (a[0], a[1], SDz(a[1]) + 1.1), (b[0], b[1], SDz(b[1]) + 1.1), 0.045, 0.045, 1)
for x in (SX - 4, SX + 4):
    bcyl(bm, Vector((x, -64, SDz(-64) + 0.7)), 0.6, 1.6, 'X', 14, 3)
bcyl(bm, Vector((SX, -68.5, SDz(-68.5) + 6)), 0.25, 12, 'Z', 10, 1)
bbox(bm, Vector((SX, -68.5, SDz(-68.5) + 9)), (3.0, 0.2, 0.2), 1)
ship_gear = mk('A-VESSEL-FEEDER.gear', bm, (M['deck'], M['galv'], M['white'], M['red']), C['SHIP'], 0.015)

# accommodation block aft (white) + bridge + funnel + lifeboat
bm = bmesh.new()
AX0, AX1, AY0, AY1 = SX - 9.0, SX + 9.0, 50.0, 64.0
for lv in range(4):
    z0 = SD + lv * 2.8
    bbox(bm, Vector((SX, (AY0 + AY1) / 2, z0 + 1.4)), (AX1 - AX0, AY1 - AY0, 2.8), 0)
    bbox(bm, Vector((SX, AY0 - 0.6, z0 + 2.75)), (AX1 - AX0 + 0.6, 1.2, 0.1), 0)                 # deck overhang
    for k in range(7):
        bbox(bm, Vector((AX0 + 1.4 + k * 2.55, AY0 - 0.03, z0 + 1.55)), (1.2, 0.1, 0.95), 1)       # windows fwd
    for sx in (AX0, AX1):
        for k in range(5):
            bbox(bm, Vector((sx + (0.03 if sx > SX else -0.03), AY0 + 1.8 + k * 2.6, z0 + 1.55)), (0.1, 1.1, 0.9), 1)
zb = SD + 4 * 2.8
bbox(bm, Vector((SX, 54.5, zb + 1.5)), (SB - 0.8, 7.0, 3.0), 0)                                   # bridge + wings
bbox(bm, Vector((SX, 50.95, zb + 1.9)), (SB - 1.6, 0.1, 1.2), 1)                                  # bridge windows
bbox(bm, Vector((SX, 54.5, zb + 3.08)), (SB - 0.4, 7.4, 0.16), 0)
bcyl(bm, Vector((SX, 55.0, zb + 6.0)), 0.18, 6.0, 'Z', 8, 2)                                       # radar mast
bbox(bm, Vector((SX, 55.0, zb + 7.6)), (3.4, 0.25, 0.12), 2)
bbox(bm, Vector((SX, 62.4, zb + 3.2)), (3.6, 3.4, 6.4), 3)                                         # funnel
bbox(bm, Vector((SX, 62.4, zb + 6.7)), (3.7, 3.5, 0.7), 2)
obox(bm, (SX - 1.3, 68.0, SD + 5.0), (SX - 1.3, 72.5, SD + 2.4), 2.6, 2.4, 4)                      # freefall lifeboat
for lv in range(5):
    z = SD + lv * 2.8 + 2.8
    for sx in (AX0 - 0.55, AX1 + 0.55):
        bbox(bm, Vector((sx, (AY0 + AY1) / 2, z + 1.0)), (0.04, AY1 - AY0, 0.04), 5)
mk('A-VESSEL-FEEDER.accom', bm, (M['white'], M['glass'], M['galv'], M['red'], M['orange'], M['galv']), C['SHIP'], 0.03)

ns = 0
rc = random.Random(9)
for (by, x), t in STACK.items():
    z = HZ
    for k in range(t):
        c = pick(rc, 0.18)
        if (by, x) == (0.0, SLOT[0]):
            c = rc.choice([d for d in DRY if 'white' not in d.name and 'w60' in d.name])
        sklib.instance(c, (x, by, z), math.pi / 2 + (math.pi if rc.random() < 0.5 else 0), 'A-CONT-S.%d.%d.%d' % (by, x * 10, k),
                       C['SHIP'])
        z += 2.896 if 'RF' in c.name else CH_
        ns += 1
NCONT['ship'] = ns
log('ship containers', ns)

# mooring lines (ship fairleads -> bollards)
lines = []
for (yf, yb_) in ((-66, -88), (-62, -73), (-30, -13), (40, 22), (66, 82), (70, 97)):
    xb = 1.3
    bx = min(BOLL, key=lambda p: abs(p[1] - yb_))
    hbx = SX + hull_halfbeam(yf, SD, SL, SB, SD, ST, 32, 14) - 0.3
    lines.append(catenary((hbx, yf, SDz(yf) + 0.6), (bx[0], bx[1], QZ + 0.62), 0.9, 16))
curve_obj('A-VESSEL-FEEDER.mooring', lines, 0.035, M['rope'], C['SHIP'])

# tugs + pilot boat
def vessel(name, L, B, D, T, hull_mat, sup_mat, coll):
    bm, Dz = hull_bm(L, B, D, T, L * 0.36, L * 0.15, sheer=0.8, Rb=1.0, nst=40)
    ob = mk(name, bm, (hull_mat, M['af'], M['deck']), coll, 0, angle=40)
    bm = bmesh.new()
    bbox(bm, Vector((0, L * 0.05, D + 1.2)), (B * 0.62, L * 0.32, 2.4), 0)
    bbox(bm, Vector((0, -L * 0.02, D + 3.4)), (B * 0.55, L * 0.16, 2.0), 0)
    bbox(bm, Vector((0, -L * 0.02 - L * 0.08, D + 3.6)), (B * 0.5, 0.08, 1.0), 1)
    for sx in (-1, 1):
        bbox(bm, Vector((sx * B * 0.275, -L * 0.02, D + 3.6)), (0.08, L * 0.12, 0.9), 1)
    bcyl(bm, Vector((0, L * 0.1, D + 5.6)), 0.12, 3.5, 'Z', 8, 2)
    for k in range(int(L / 2.2)):             # tyre fenders along the sides
        y = -L / 2 + 3 + k * 2.2
        if y > L / 2 - 2:
            break
        hb = hull_halfbeam(y, D - 0.6, L, B, D, T, L * 0.36, L * 0.15)
        for sx in (-1, 1):
            bcyl(bm, Vector((sx * (hb + 0.2), y, D - 0.7)), 0.45, 0.3, 'X', 12, 3)
    bcyl(bm, Vector((0, -L / 2 + 0.2, D - 0.2)), 0.9, B * 0.5, 'X', 14, 3)       # bow pudding fender
    sup = mk(name + '.sup', bm, (sup_mat, M['glass'], M['galv'], M['rubber']), coll, 0.03)
    sup.parent = ob
    return ob


TUGS = []
for k, (pos, rz, anim) in enumerate((((SX - hull_halfbeam(-58, 3.4, SL, SB, SD, ST, 32, 14) - 13.85, -58.0, 0), math.pi / 2, 0.15),
                                     ((SX - hull_halfbeam(-30, 3.4, SL, SB, SD, ST, 32, 14) - 13.85, -30.0, 0), math.pi / 2, 0.12))):
    t = vessel('A-VESSEL-TUG.%d' % (k + 1), 26.0, 9.6, 3.6, 3.4, M['black'], M['white'], C['SHIP'])
    t.rotation_euler.z = rz
    t.location = pos
    # bow pressed into the hull: small push oscillation (keyed), stern wash patch
    for f in (1, 90, 180, 264):
        key_loc(t, f, Vector(pos) - Vector((anim * (0.5 + 0.5 * math.sin(f * 0.07 + k)), 0, 0)))
    TUGS.append(t)
pilot = vessel('A-VESSEL-PILOT', 13.0, 4.4, 2.2, 1.4, M['orange'], M['white'], C['SHIP'])
pilot.rotation_euler.z = -0.6
key_loc(pilot, 1, (-150, -110, 0))
key_loc(pilot, F_END, (-128, -80, 0))
linear(pilot)


def foam_mat():
    m = bpy.data.materials.get('prop_wash')
    if m:
        return m
    m, nt = sklib._new_mat('prop_wash')
    n = sklib._n
    out = n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = n(nt, 'ShaderNodeBsdfPrincipled', 500, 0)
    b.inputs['Base Color'].default_value = (0.85, 0.89, 0.88, 1)
    b.inputs['Roughness'].default_value = 0.55
    tc = n(nt, 'ShaderNodeTexCoord', -900, 0)
    nz = sklib._noise(nt, tc.outputs['Object'], 0.6, 8.0, 0.65, -600, 0)
    gr = n(nt, 'ShaderNodeTexGradient', -600, -300, gradient_type='SPHERICAL')
    nt.links.new(tc.outputs['Object'], gr.inputs['Vector'])
    a = sklib._math(nt, 'MULTIPLY', sklib._maprange(nt, nz.outputs['Fac'], 0.45, 0.7, 0, 1, -350, 0),
                    sklib._maprange(nt, gr.outputs['Fac'], 0.0, 0.6, 0, 1, -350, -300), x=-100)
    nt.links.new(a, b.inputs['Alpha'])
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return m


for k, t in enumerate(TUGS):           # prop wash astern (sits on the water, follows the tug)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=1.0)
    w = mk('A-VESSEL-TUG.%d.wash' % (k + 1), bm, (foam_mat(),), C['SHIP'])
    w.parent = t
    w.location, w.scale = (0, 13.0 + 7.0, 0.12), (6.0, 11.0, 1)
    w.visible_shadow = False
log('ship done')

# ------------------------------------------------------------------------------------------------ STS cranes
LEG_S, LEG_L, HALF = 10.0, 40.0, 9.0
ZP, ZG = 44.0, 47.5                    # portal top, boom girder top
TROLLEY_Z = ZG
APEX = (24.0, 78.0)


def crane_static():
    c = sklib.collection('A-PORT-STS', False)
    if c.objects:
        return c
    bm = bmesh.new()
    for x in (LEG_S, LEG_L):
        for sy in (-1, 1):
            y = sy * HALF
            bbox(bm, Vector((x, y, (5.0 + ZP) / 2)), (1.7, 1.7, ZP - 5.0), 0)                  # legs
            bbox(bm, Vector((x, y, QZ + 1.25)), (1.3, 7.0, 1.3), 2)                            # bogie beam
            for k in range(4):
                bcyl(bm, Vector((x, y - 2.7 + k * 1.8, QZ + 0.5)), 0.48, 0.5, 'X', 14, 3)      # wheels
            bbox(bm, Vector((x, y, QZ + 3.2)), (1.9, 2.6, 2.6), 0)                             # equaliser
    for sy in (-1, 1):
        y = sy * HALF
        bbox(bm, Vector(((LEG_S + LEG_L) / 2, y, 16.5)), (LEG_L - LEG_S, 1.3, 1.8), 0)         # sill beams
        bbox(bm, Vector(((LEG_S + LEG_L) / 2, y, ZP - 1.1)), (LEG_L - LEG_S + 1.7, 1.8, 2.2), 0)   # upper portal
        obox(bm, (LEG_S, y, ZP - 2.2), (LEG_L, y, 17.4), 0.7, 0.9, 0)                          # diagonal brace
    for x in (LEG_S, LEG_L):
        bbox(bm, Vector((x, 0, ZP - 1.1)), (1.8, 2 * HALF + 1.7, 2.2), 0)                      # portal cross beams
    bbox(bm, Vector((LEG_L, 0, 16.5)), (1.2, 2 * HALF, 1.6), 0)
    # boom + girders (2 box girders, cross ties), boom tip, backreach
    for sy in (-1, 1):
        bbox(bm, Vector(((-47 + 66) / 2, sy * 4.1, ZG - 1.6)), (113, 1.3, 3.2), 0)
        bbox(bm, Vector(((-47 + 66) / 2, sy * 4.95, ZG - 1.75)), (113, 0.5, 0.08), 1)          # walkway
        for xx in range(-46, 66, 2):
            bbox(bm, Vector((xx, sy * 5.18, ZG - 1.2)), (0.04, 0.04, 1.1), 1)
        bbox(bm, Vector(((-47 + 66) / 2, sy * 5.18, ZG - 0.65)), (113, 0.04, 0.04), 1)
        # A-frame legs, forestays, backstays
        obox(bm, (LEG_S, sy * 7.0, ZG), (APEX[0], sy * 5.0, APEX[1]), 1.2, 1.2, 0)
        obox(bm, (LEG_L, sy * 7.0, ZG), (APEX[0], sy * 5.0, APEX[1]), 1.2, 1.2, 0)
        for xb in (-12.0, -44.0):
            obox(bm, (APEX[0], sy * 5.0, APEX[1]), (xb, sy * 5.25, ZG - 0.2), 0.45, 0.45, 0)
        obox(bm, (APEX[0], sy * 5.0, APEX[1]), (64.0, sy * 5.25, ZG - 0.2), 0.55, 0.55, 0)
        bbox(bm, Vector((LEG_S, sy * 6.6, ZG - 0.6)), (1.6, 3.2, 1.6), 0)
        bbox(bm, Vector((LEG_L, sy * 6.6, ZG - 0.6)), (1.6, 3.2, 1.6), 0)
    for xx in (-44, -20, 4, 30, 56):
        bbox(bm, Vector((xx, 0, ZG - 3.05)), (0.6, 8.2, 0.4), 0)                              # bottom ties
    bbox(bm, Vector((APEX[0], 0, APEX[1])), (1.6, 11.0, 1.6), 0)
    bbox(bm, Vector((APEX[0], 0, APEX[1] + 1.6)), (2.6, 2.6, 1.6), 4)                        # apex sheave house
    bbox(bm, Vector((-47.5, 0, ZG - 1.6)), (1.0, 9.4, 3.4), 0)                                # boom tip
    bbox(bm, Vector((55.0, 0, ZG + 3.0)), (16.0, 10.0, 6.0), 4)                               # machinery house
    bbox(bm, Vector((55.0, 0, ZG + 6.1)), (16.4, 10.4, 0.25), 1)
    bbox(bm, Vector((LEG_L + 0.2, 0, 21.0)), (6.0, 9.0, 5.0), 4)                              # e-house
    # stair tower beside the land leg (zig-zag flights + landings + handrails)
    sx0, sy0 = LEG_L + 1.6, -HALF
    for k in range(13):
        z0 = 5.0 + k * 3.0
        d = 1 if k % 2 == 0 else -1
        obox(bm, (sx0, sy0 - d * 1.6, z0), (sx0, sy0 + d * 1.6, z0 + 3.0), 0.9, 0.12, 1)
        bbox(bm, Vector((sx0, sy0 + d * 2.0, z0 + 3.0)), (0.9, 1.0, 0.08), 1)
        obox(bm, (sx0 + 0.45, sy0 - d * 1.6, z0 + 1.0), (sx0 + 0.45, sy0 + d * 1.6, z0 + 4.0), 0.04, 0.04, 1)
        bbox(bm, Vector((sx0 + 0.45, sy0 + d * 2.0, z0 + 3.5)), (0.04, 0.04, 1.0), 1)
    # boom-tip lights, festoon track
    for sy in (-1, 1):
        bbox(bm, Vector((-46.0, sy * 3.0, ZG - 3.6)), (0.5, 0.8, 0.4), 5)
    bbox(bm, Vector((22.0, -5.6, ZG - 3.4)), (86.0, 0.2, 0.2), 1)
    ob = mk('A-PORT-STS.mesh', bm, (M['crane'], M['galv'], M['black'], M['galv'], M['crane_l'], M['lamp']), c, 0.06, 2, 40)
    sklib.apply_mods(ob)
    # festoon cable loops (static, parked on the land side of the track)
    loops = []
    for k in range(9):
        x0 = 26 + k * 4.0
        loops.append(catenary((x0, -5.6, ZG - 3.5), (x0 + 3.7, -5.6, ZG - 3.5), 1.6, 10))
        loops.append(catenary((x0 + 0.1, -5.5, ZG - 3.5), (x0 + 3.6, -5.5, ZG - 3.5), 1.45, 10))
    fo = curve_obj('A-PORT-STS.festoon', loops, 0.045, M['rubber'], False)
    c.objects.link(fo)
    return c


def trolley_parts(name, coll):
    bm = bmesh.new()
    bbox(bm, Vector((0, 0, 1.3)), (7.0, 10.6, 2.4), 0)            # trolley frame on the girders
    for sx in (-1, 1):
        for sy in (-1, 1):
            bcyl(bm, Vector((sx * 2.8, sy * 4.1, 0.2)), 0.4, 0.4, 'Y', 12, 1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bcyl(bm, Vector((sx * 1.0, sy * 1.6, -0.2)), 0.45, 0.25, 'X', 14, 1)    # rope sheaves
    # operator cabin hanging under the girder (sea side of the trolley)
    bbox(bm, Vector((-1.8, 5.6, -0.4)), (1.0, 1.0, 1.4), 0)
    bbox(bm, Vector((-2.4, 5.6, -2.6)), (2.6, 2.4, 2.6), 2)
    bbox(bm, Vector((-3.72, 5.6, -2.4)), (0.06, 2.1, 1.6), 3)
    bbox(bm, Vector((-2.4, 6.82, -2.4)), (2.2, 0.06, 1.6), 3)
    bbox(bm, Vector((-2.4, 5.6, -3.92)), (2.1, 2.0, 0.06), 3)
    ob = mk(name, bm, (M['crane_l'], M['galv'], M['white'], M['glass']), coll, 0.04)
    return ob


def spreader(name, coll):
    bm = bmesh.new()
    bbox(bm, Vector((0, 0, 0.55)), (0.7, 11.6, 0.6), 0)                        # main telescopic beam (along Y)
    for sy in (-1, 1):
        bbox(bm, Vector((0, sy * 5.85, 0.45)), (2.44, 0.5, 0.5), 0)              # end beams
        bbox(bm, Vector((0, sy * 3.0, 0.62)), (0.9, 0.4, 0.5), 0)
        for sx in (-1, 1):
            bbox(bm, Vector((sx * 1.0, sy * 5.85, 0.32)), (0.42, 0.5, 0.64), 0)  # corner housings
            bcyl(bm, Vector((sx * 1.0, sy * 5.85, 0.0)), 0.07, 0.12, 'Z', 8, 1)  # twistlock cones (into castings)
            bbox(bm, Vector((sx * 1.2, sy * 5.9, 0.85)), (0.08, 0.08, 0.35), 2)  # indicator light
    bbox(bm, Vector((0, 0, 1.25)), (2.2, 3.4, 0.9), 0)                          # headblock
    for sx in (-1, 1):
        for sy in (-1, 1):
            bcyl(bm, Vector((sx * 1.0, sy * 1.6, 1.75)), 0.35, 0.22, 'X', 14, 1)
    bcyl(bm, Vector((0.6, -0.9, 1.0)), 0.18, 1.2, 'Y', 10, 3)                   # hydraulic pack / cable basket
    ob = mk(name, bm, (M['yellow'], M['galv'], M['orange'], M['black']), coll, 0.03)
    return ob


STS = crane_static()
CRANES_Y = [-52.8, 0.0, 39.6]
CRANE_ANIM = {}
for k, cy in enumerate(CRANES_Y):
    sklib.instance(STS, (0, cy, 0), 0.0, 'A-PORT-STS.%d' % (k + 1), C['CRANES'])
    tr = trolley_parts('A-PORT-STS.%d.trolley' % (k + 1), C['CRANES'])
    sp = spreader('A-PORT-SPREADER.%d' % (k + 1), C['CRANES'])
    ropes = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm = bmesh.new()
            bcyl(bm, Vector((0, 0, -0.5)), 0.022, 1.0, 'Z', 6)
            rp_ = mk('A-PORT-STS.%d.rope%d%d' % (k + 1, sx, sy), bm, (M['galv'],), C['CRANES'])
            rp_.parent = tr
            rp_.location = (sx * 1.0, cy * 0 + sy * 1.6, -0.2)
            fc = rp_.driver_add('scale', 2)
            d = fc.driver
            d.type = 'SCRIPTED'
            v = d.variables.new()
            v.name, v.type = 'z', 'TRANSFORMS'
            v.targets[0].id = sp
            v.targets[0].transform_type, v.targets[0].transform_space = 'LOC_Z', 'WORLD_SPACE'
            d.expression = '%.4f - (z + 1.75)' % (TROLLEY_Z - 0.2)
            ropes.append(rp_)
    CRANE_ANIM[k] = (tr, sp, cy)

# middle crane: trolley travels out to the slot, then lowers the white reefer (hover 1.5 m, contact f204)
tr, sp, cy = CRANE_ANIM[1]
REEFER_H = 2.896
hero = sklib.container_40('reefer', 'white', 0.15, 'A-CONT-40RF.hero', C['CRANES'])
hero.parent = sp
hero.location, hero.rotation_euler = (0, 0, -REEFER_H), (0, 0, math.pi / 2)
for f, x, zb in ((1, 24.0, 33.0), (40, 24.0, 33.0), (118, SLOT[0], 33.0), (130, SLOT[0], 33.0), (186, SLOT[0], SLOT_Z + 1.5),
                 (194, SLOT[0], SLOT_Z + 1.5), (204, SLOT[0], SLOT_Z), (F_END, SLOT[0], SLOT_Z)):
    key_loc(tr, f, (x, cy, TROLLEY_Z))
    key_loc(sp, f, (x, cy + SLOT[1], zb + REEFER_H))
sklib.ease_keys(tr, sp)
# crane 1: holding a box at 30 m over the ship; crane 3: spreader parked high over the backreach
for k, (x, zb, box) in ((0, (ROWS_Q[5], 29.0, True)), (2, (30.0, 26.0, False))):
    tr, sp, cy = CRANE_ANIM[k]
    tr.location = (x, cy, TROLLEY_Z)
    sp.location = (x, cy, zb + (CH_ if box else 0))
    if box:
        sklib.instance(DRY[3], (0, 0, -CH_), math.pi / 2, 'A-CONT-S.crane1', C['CRANES']).parent = sp
log('cranes')

# ------------------------------------------------------------------------------------------------ vehicles
def wheel(bm, c, r, w, mi_t, mi_h):
    bcyl(bm, c, r, w, 'Y', 18, mi_t)
    bcyl(bm, c, r * 0.55, w + 0.02, 'Y', 12, mi_h)


def tractor_coll():
    """Terminal tractor (front +X): offset single-seat cab with pillars + glass, side hood, rear deck + fifth wheel."""
    c = sklib.collection('A-PORT-TT', False)
    if c.objects:
        return c
    bm = bmesh.new()
    for sy in (-0.45, 0.45):
        bbox(bm, Vector((0, sy, 0.78)), (5.6, 0.16, 0.3), 2)                       # frame rails
    bbox(bm, Vector((-1.1, 0, 0.98)), (3.4, 2.3, 0.08), 3)                         # rear deck plate
    bbox(bm, Vector((-1.5, 0, 1.07)), (1.5, 1.5, 0.1), 3)                          # fifth wheel
    for sy in (-0.6, 0.6):
        obox(bm, (-0.6, sy, 1.0), (-1.4, sy, 1.02), 0.12, 0.2, 2)                  # lift arms
    bbox(bm, Vector((1.75, 0.68, 1.22)), (2.3, 1.05, 0.85), 0)                     # hood (right of cab)
    bbox(bm, Vector((2.92, 0.68, 1.2)), (0.04, 0.9, 0.6), 2)                       # grille
    bbox(bm, Vector((1.4, -0.55, 1.35)), (1.6, 1.4, 0.75), 0)                      # cab lower body
    for x in (0.62, 2.18):
        for y in (-1.23, 0.13):
            bbox(bm, Vector((x, y, 2.27)), (0.08, 0.08, 1.15), 0)                  # pillars
    bbox(bm, Vector((1.4, -0.55, 2.9)), (1.75, 1.55, 0.12), 0)                     # roof
    bbox(bm, Vector((2.17, -0.55, 2.27)), (0.02, 1.25, 1.1), 1)                    # glass front/back/sides
    bbox(bm, Vector((0.63, -0.55, 2.27)), (0.02, 1.25, 1.1), 1)
    bbox(bm, Vector((1.4, -1.225, 2.27)), (1.45, 0.02, 1.1), 1)
    bbox(bm, Vector((1.4, 0.125, 2.27)), (1.45, 0.02, 1.1), 1)
    bcyl(bm, Vector((1.4, -0.55, 3.03)), 0.09, 0.14, 'Z', 10, 5)                   # beacon
    bbox(bm, Vector((1.0, -1.35, 0.75)), (0.5, 0.25, 0.06), 3)                     # step
    bcyl(bm, Vector((0.45, 0.95, 2.1)), 0.07, 1.8, 'Z', 8, 3)                      # exhaust
    bbox(bm, Vector((3.0, 0, 0.72)), (0.18, 2.4, 0.3), 2)                          # bumper
    for x in (2.0, -1.3):
        for sy in (-1, 1):
            bbox(bm, Vector((x, sy * 1.0, 1.15)), (1.3, 0.4 if x > 0 else 0.65, 0.05), 2)   # mudguards
            wheel(bm, Vector((x, sy * 1.0, 0.55)), 0.55, 0.36 if x > 0 else 0.6, 4, 3)
    mk('A-PORT-TT.mesh', bm, (M['tt'], M['glass'], M['black'], M['galv'], M['rubber'], M['orange']), c, 0.03)
    return c


def chassis_coll(name='A-PORT-CHASSIS', axles=2):
    c = sklib.collection(name, False)
    if c.objects:
        return c
    bm = bmesh.new()
    for sy in (-0.5, 0.5):
        bbox(bm, Vector((0, sy, 1.18)), (12.2, 0.16, 0.36), 0)                     # I-beams (centred, front -X)
    for x in [-5.9 + k * 1.475 for k in range(9)]:
        bbox(bm, Vector((x, 0, 1.32)), (0.12, 2.44, 0.12), 0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bbox(bm, Vector((sx * 6.0, sy * 1.1, 1.33)), (0.2, 0.2, 0.14), 1)      # twistlock pads
    bbox(bm, Vector((-4.3, 0, 0.8)), (0.12, 2.2, 0.9), 1)                          # landing legs
    for k in range(axles):
        x = 4.0 + k * 1.35
        bbox(bm, Vector((x, 0, 0.55)), (0.18, 2.0, 0.18), 1)
        for sy in (-1, 1):
            wheel(bm, Vector((x, sy * 1.0, 0.52)), 0.52, 0.62, 2, 1)
    bbox(bm, Vector((6.15, 0, 0.75)), (0.12, 2.3, 0.25), 3)                         # rear bumper / lamp bar
    mk(name + '.mesh', bm, (M['black'], M['galv'], M['rubber'], M['red']), c, 0.03)
    return c


TT, CHS = tractor_coll(), chassis_coll()


def rig_vehicle(name, parts, coll):
    e = sklib.new_obj(name, None, coll)
    for (src, loc, rz) in parts:
        sklib.instance(src, loc, rz, name + '.' + src.name, coll).parent = e
    return e


NVEH = 0
for k, (x, y0, y1, box) in enumerate(((16.0, -112, -58, True), (21.0, 14, -46, True), (26.0, -90, -36, False),
                                      (31.0, 40, -12, True))):
    heading = math.pi / 2 if y1 > y0 else -math.pi / 2
    parts = [(TT, (0, 0, 0), 0.0), (CHS, (-6.4, 0, 0), math.pi)]
    if box:
        parts.append((pick(R, 0.25), (-6.4, 0, 1.40), 0.0))
    v = rig_vehicle('A-PORT-TT.%d' % (k + 1), parts, C['VEH'])
    v.rotation_euler.z = heading
    key_loc(v, 1, (x, y0, QZ))
    key_loc(v, F_END, (x, y1, QZ))
    linear(v)
    NVEH += 1


def reach_stacker(coll):
    bm = bmesh.new()
    bbox(bm, Vector((0, 0, 1.6)), (9.0, 3.6, 1.6), 0)                              # body (front +X)
    bbox(bm, Vector((-4.2, 0, 2.6)), (1.4, 3.4, 2.0), 0)                           # counterweight
    bbox(bm, Vector((0.6, -1.1, 3.6)), (2.0, 1.4, 2.2), 0)                         # cab
    bbox(bm, Vector((1.62, -1.1, 3.8)), (0.04, 1.2, 1.4), 1)
    bbox(bm, Vector((0.6, -1.82, 3.8)), (1.7, 0.04, 1.4), 1)
    obox(bm, (-3.0, 0.4, 3.4), (6.0, 0.4, 9.0), 1.2, 1.1, 0)                       # boom
    obox(bm, (1.2, 0.4, 2.4), (2.6, 0.4, 5.2), 0.5, 0.5, 2)                        # lift cylinder
    for x, r in ((3.2, 0.9), (-2.8, 0.8)):
        for sy in (-1, 1):
            wheel(bm, Vector((x, sy * 1.55, r)), r, 0.7, 3, 2)
    ob = mk('A-PORT-RS.mesh', bm, (M['red'], M['glass'], M['galv'], M['rubber']), coll, 0.05)
    bm = bmesh.new()                                                                 # its spreader (along Y)
    bbox(bm, Vector((0, 0, 0.3)), (0.6, 11.6, 0.5))
    for sy in (-1, 1):
        bbox(bm, Vector((0, sy * 5.85, 0.25)), (2.44, 0.5, 0.5))
    sp_ = mk('A-PORT-RS.spreader', bm, (M['yellow'],), coll, 0.03)
    sp_.parent = ob
    sp_.location = (6.6, 0.4, 9.0 - 0.9 - CH_ + CH_)
    box_ = sklib.instance(pick(R), (6.6, 0.4, 9.0 - 0.9 - CH_ - 0.0), math.pi / 2, 'A-PORT-RS.box', coll)
    box_.parent = ob
    sp_.location.z = 9.0 - 0.9
    box_.location.z = 9.0 - 0.9 - CH_
    return ob


# parked empty chassis along the apron back lane + cone lines (quay never bare)
for k, y in enumerate([-118 + i * 15.5 for i in range(15)]):
    if 6 < y < 40:
        continue
    sklib.instance(CHS, (61.0, y, QZ), math.pi / 2 + R.uniform(-0.03, 0.03), 'A-PORT-CHASSIS.park%02d' % k, C['VEH'])
    if R.random() < 0.5:
        sklib.instance(pick(R, 0.3), (61.0, y, QZ + 1.40), math.pi / 2, 'A-CONT-P.%02d' % k, C['VEH'])
bm = bmesh.new()
for y in range(-110, 120, 9):
    for dx in (0, 0.0):
        bcyl(bm, Vector((14.5, y + 0.5, QZ + 0.35)), 0.16, 0.7, 'Z', 10, 0, 0.03)
        bbox(bm, Vector((14.5, y + 0.5, QZ + 0.02)), (0.42, 0.42, 0.04), 1)
mk('A-PORT-CONES', bm, (M['orange'], M['black']), C['QUAY'], 0.01)

def straddle_carrier(name, coll):
    """Straddle carrier (long axis Y, travels X): 4 legs in the stack gaps, top frame, cab, carried box."""
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            bbox(bm, Vector((sx * 2.1, sy * 6.3, 5.6)), (0.55, 0.7, 9.6), 0)
            bcyl(bm, Vector((sx * 2.1, sy * 6.3, 0.55)), 0.55, 0.5, 'X', 14, 2)
        bbox(bm, Vector((sx * 2.1, 0, 10.6)), (0.7, 13.4, 0.9), 0)               # top beams
        bbox(bm, Vector((sx * 2.1, 0, 1.4)), (0.6, 13.4, 0.5), 0)                # bottom rails
    for sy in (-1, 1):
        bbox(bm, Vector((0, sy * 6.3, 10.6)), (4.8, 0.7, 0.9), 0)
    bbox(bm, Vector((2.9, -5.6, 9.7)), (1.4, 1.6, 2.0), 0)                       # cab
    bbox(bm, Vector((3.61, -5.6, 9.9)), (0.02, 1.4, 1.2), 1)
    bbox(bm, Vector((0, 0, 9.9)), (2.0, 11.8, 0.5), 3)                           # spreader
    ob = mk(name, bm, (M['orange'], M['glass'], M['rubber'], M['yellow']), coll, 0.04)
    box_ = sklib.instance(pick(R), (0, 0, 9.65 - CH_ - 0.05), math.pi / 2, name + '.box', coll)
    box_.parent = ob
    return ob


for k, (yl, x0, x1) in enumerate(((BLOCKS[0] + 83.8, 80.0, 150.0), (BLOCKS[2] + 83.8, 210.0, 120.0))):
    sc = straddle_carrier('A-PORT-SC.%d' % (k + 1), C['VEH'])
    key_loc(sc, 1, (x0, yl, QZ))
    key_loc(sc, F_END, (x1, yl, QZ))
    linear(sc)
    NVEH += 1

rs_ = reach_stacker(C['VEH'])
rs_.rotation_euler.z = 0.0
key_loc(rs_, 1, (78.0, BLOCKS[2] - 7.0, QZ))
key_loc(rs_, F_END, (132.0, BLOCKS[2] - 7.0, QZ))
linear(rs_)
NVEH += 1


def truck_cab(coll):
    """Indian tipper-style tractor cab (Tata/Ashok Leyland-like proportions, no badges), front -X."""
    bm = bmesh.new()
    bbox(bm, Vector((0, 0, 0.75)), (6.2, 1.0, 0.32), 2)                            # frame
    bbox(bm, Vector((-2.0, 0, 2.3)), (2.0, 2.45, 2.2), 0)                          # cab box
    bbox(bm, Vector((-2.15, 0, 3.55)), (1.7, 2.3, 0.35), 0)                        # roof cap
    bbox(bm, Vector((-3.02, 0, 2.75)), (0.05, 2.15, 1.05), 1)                      # windscreen
    for sy in (-1, 1):
        bbox(bm, Vector((-2.2, sy * 1.235, 2.75)), (1.1, 0.04, 0.85), 1)           # side windows
        bbox(bm, Vector((-3.25, sy * 1.45, 2.6)), (0.08, 0.06, 0.55), 2)           # mirrors
        bbox(bm, Vector((-3.03, sy * 0.85, 1.55)), (0.05, 0.4, 0.22), 4)           # headlamps
    bbox(bm, Vector((-3.03, 0, 1.7)), (0.05, 1.1, 0.6), 2)                         # grille
    bbox(bm, Vector((-3.1, 0, 1.05)), (0.25, 2.45, 0.35), 2)                       # bumper
    bbox(bm, Vector((-3.0, 0, 2.05)), (0.04, 2.46, 0.18), 3)                       # stripe
    bbox(bm, Vector((1.2, 0, 0.95)), (1.6, 1.8, 0.1), 2)                           # fifth wheel
    for x in (-2.1, 0.9, 2.3):
        for sy in (-1, 1):
            wheel(bm, Vector((x, sy * 1.0, 0.52)), 0.52, 0.32 if x < 0 else 0.6, 5, 2)
    return mk('A-TRUCK-REEFER.cab', bm, (M['cab'], M['glass'], M['black'], M['cabstripe'], M['lamp'], M['rubber']), coll, 0.04)


TRUCK_Y, TRUCK_X = 18.0, 46.0          # reefer centre; doors at +X
cab = truck_cab(C['VEH'])
cab.location = (TRUCK_X - 6.3, TRUCK_Y, QZ)
sklib.instance(chassis_coll('A-TRUCK-CHASSIS', 3), (TRUCK_X, TRUCK_Y, QZ), 0.0, 'A-TRUCK-REEFER.chassis', C['VEH'])
DOOR = sklib.container_40('reefer', 'white', 0.15, 'A-CONT-40RF.door', C['DOOR'])
DOOR_BASE = QZ + 1.40
DOOR.location = (TRUCK_X, TRUCK_Y, DOOR_BASE)
NVEH += 1
log('vehicles')

# ------------------------------------------------------------------------------------------------ canopy desk + office
DX, DY = 52.0, 28.0
bm = bmesh.new()
for sx in (-3, 3):
    for sy in (-2.5, 2.5):
        bbox(bm, Vector((DX + sx, DY + sy, QZ + 1.5)), (0.1, 0.1, 3.0), 0)
for sx in (-3, 3):
    obox(bm, (DX + sx, DY - 2.6, QZ + 2.9), (DX + sx, DY + 2.6, QZ + 3.15), 0.12, 0.16, 0)
obox(bm, (DX - 3.3, DY - 2.8, QZ + 3.0), (DX + 3.3, DY - 2.8, QZ + 3.0), 0.1, 0.12, 0)
canopy_frame = mk('A-PORT-DOCDESK.canopy', bm, (M['galv'],), C['QUAY'], 0.01)
bm = bmesh.new()                                         # corrugated roof sheet, slight slope
prof = sklib._corr(6.8, 0.2, 0.025, 0.06, 0.06)
sklib._bm_strip(bm, prof, -2.9, 2.9, lambda u, d, v: (DX - 3.4 + u, DY + v, QZ + 3.08 + (v + 2.9) * 0.05 + d), 0, flip=True)
roof = sklib._mesh_obj('A-PORT-DOCDESK.roof', bm, C['QUAY'])
sklib.mat_to(roof, M['corr'])
so = roof.modifiers.new('Solidify', 'SOLIDIFY')
so.thickness = 0.004
bm = bmesh.new()                                         # table
bbox(bm, Vector((DX, DY, QZ + 0.88)), (2.2, 0.85, 0.04), 0)
for sx in (-1, 1):
    for sy in (-1, 1):
        bbox(bm, Vector((DX + sx * 1.0, DY + sy * 0.36, QZ + 0.43)), (0.05, 0.05, 0.86), 1)
bbox(bm, Vector((DX, DY + 0.36, QZ + 0.6)), (2.0, 0.02, 0.4), 0)
mk('A-PORT-DOCDESK.table', bm, (M['wood'], M['galv']), C['QUAY'], 0.005)
TZ = QZ + 0.90
bm = bmesh.new()                                         # papers, clipboard, folders, stamp, laptop
pap = []
for k, (x, y, rz) in enumerate(((-0.55, -0.05, 0.08), (-0.52, -0.03, -0.05), (0.15, -0.12, 0.2), (0.05, 0.1, -0.12))):
    pap.append((x, y, rz, k))
for (x, y, rz, k) in pap:
    Mx = Matrix.Translation((DX + x, DY + y, TZ + 0.001 + k * 0.002)) @ Matrix.Rotation(rz, 4, 'Z')
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, matrix=Mx @ Matrix.Diagonal((0.21, 0.297, 1, 1)))
mk('A-PORT-DOCDESK.papers', bm, (paper_mat(),), C['QUAY'])
bm = bmesh.new()
bbox(bm, Vector((DX + 0.62, DY - 0.08, TZ + 0.006)), (0.24, 0.33, 0.012), 0)             # clipboard
bbox(bm, Vector((DX + 0.62, DY + 0.07, TZ + 0.016)), (0.08, 0.02, 0.012), 1)
bbox(bm, Vector((DX - 0.95, DY + 0.1, TZ + 0.03)), (0.24, 0.32, 0.06), 2)               # file folders
bbox(bm, Vector((DX - 0.95, DY + 0.1, TZ + 0.075)), (0.235, 0.31, 0.03), 3)
bcyl(bm, Vector((DX - 0.2, DY + 0.25, TZ + 0.012)), 0.035, 0.024, 'Z', 12, 4)            # stamp + pad
bcyl(bm, Vector((DX - 0.2, DY + 0.25, TZ + 0.065)), 0.016, 0.085, 'Z', 10, 4)
bbox(bm, Vector((DX - 0.32, DY + 0.25, TZ + 0.006)), (0.12, 0.08, 0.012), 4)
bbox(bm, Vector((DX + 0.0, DY + 0.18, TZ + 0.011)), (0.34, 0.24, 0.022), 5)              # laptop base
obox(bm, (DX + 0.0, DY + 0.30, TZ + 0.022), (DX + 0.0, DY + 0.36, TZ + 0.24), 0.34, 0.012, 5)
obox(bm, (DX + 0.0, DY + 0.296, TZ + 0.035), (DX + 0.0, DY + 0.352, TZ + 0.225), 0.30, 0.004, 6)
mk('A-PORT-DOCDESK.props', bm, (sklib.plastic((0.12, 0.12, 0.13), 0.2, name='clip_board_brown'), M['galv'],
                                sklib.plastic((0.08, 0.22, 0.45), 0.2), sklib.plastic((0.6, 0.12, 0.08), 0.2),
                                M['black'], sklib.aluminium(), sklib.flat('screen', (0.05, 0.07, 0.09), rough=0.1,
                                                                         **{'Emission Color': (0.35, 0.42, 0.5, 1),
                                                                            'Emission Strength': 0.6})),
   C['QUAY'], 0.002)
bm = bmesh.new()                                         # quay office cabin behind the desk
bbox(bm, Vector((DX + 1.0, DY + 6.0, QZ + 1.4)), (6.0, 2.6, 2.8), 0)
bbox(bm, Vector((DX + 1.0, DY + 6.0, QZ + 2.86)), (6.2, 2.8, 0.12), 2)
bbox(bm, Vector((DX - 0.6, DY + 4.68, QZ + 1.6)), (1.4, 0.05, 0.9), 1)
bbox(bm, Vector((DX + 2.4, DY + 4.68, QZ + 1.05)), (0.9, 0.05, 2.0), 2)
bbox(bm, Vector((DX + 3.6, DY + 4.68, QZ + 2.3)), (0.9, 0.5, 0.45), 2)                  # split AC unit
mk('A-PORT-OFFICE', bm, (M['white'], M['glass'], M['galv']), C['QUAY'], 0.02)
log('desk')

# ------------------------------------------------------------------------------------------------ people
NPEOPLE = 0
if 'nopeople' not in ARGV:
    import people

    def person(name, outfit, pose, loc, rz, seed, sex='male', age=0.4, tone=0.6, cycle=None, phase=0.0, path=None,
               lod='L0', body=None):
        global NPEOPLE
        p = people.make_person(name, sex=sex, age=age, skin_tone=tone, outfit=outfit, pose=pose, location=loc,
                               rotation_z=rz, seed=seed, lod=lod, body=body)
        for o in [p] + list(p.children_recursive):
            for c in list(o.users_collection):
                c.objects.unlink(o)
            C['PEOPLE'].objects.link(o)
        if cycle:
            people.animate_cycle(p, cycle, 1, F_END, phase=phase)
        if path:
            pz = p.location.z
            for f, xy in path:
                key_loc(p, f, (xy[0], xy[1], pz))
            linear(p)
        NPEOPLE += 1
        return p

    LZ = HZ + CH_ + 0.0
    # documentation staff under the canopy (behind the table, facing south / the camera side)
    person('P-PORT-DOC-1', 'formal_shirt_lanyard', 'work_table', (DX - 0.45, DY + 0.78, QZ), 0.1, 21, 'female', 0.35, 0.55,
           'work', 0.2)
    person('P-PORT-DOC-2', 'formal_shirt_lanyard', 'work_table', (DX + 0.6, DY + 0.8, QZ), -0.15, 22, 'male', 0.55, 0.7,
           'work', 0.6)
    # lashing crew stepping in on the lashing bridge next to the slot
    yg = -6.6
    person('P-PORT-LASH-1', 'hivis_helmet', 'walk', (SLOT[0] + 3.2, yg, LZ), -math.pi / 2, 31, 'male', 0.3, 0.75, 'walk',
           0.0, [(1, (SLOT[0] + 4.6, yg)), (190, (SLOT[0] + 3.2, yg)), (F_END, (SLOT[0] + 1.6, yg))])
    person('P-PORT-LASH-2', 'hivis_helmet', 'stand', (SLOT[0] - 2.3, yg, LZ), math.pi / 2, 32, 'male', 0.5, 0.5, 'work', 0.4)
    # quay: lashing foreman at the edge, a walker under crane 2, a signalman by the truck, crew on the forecastle
    person('P-PORT-QUAY-1', 'hivis_helmet', 'stand', (6.5, -20.0, QZ), -math.pi / 2 - 0.4, 41, 'male', 0.6, 0.65, 'work', 0.1)
    person('P-PORT-QUAY-2', 'hivis_helmet', 'walk', (12.8, -30.0, QZ), 0.0 + math.pi, 42, 'male', 0.25, 0.8, 'walk', 0.3,
           [(1, (12.8, -40.0)), (F_END, (12.8, -12.0))])
    person('P-PORT-QUAY-3', 'hivis_helmet', 'wave', (34.0, TRUCK_Y - 4.2, QZ), math.pi / 2 + 0.3, 43, 'male', 0.45, 0.6, 'wave', 0.0)
    person('P-PORT-SHIP-1', 'hivis_helmet', 'stand', (SX + 2.0, -70.0, SDz(-70.0)), 0.3, 44, 'male', 0.4, 0.7, 'work', 0.7,
           lod='L1')
    for k, (x, y0, y1) in enumerate(((18.5, -80, -60), (24.0, 30, 48), (34.5, -30, -50), (8.0, 60, 40))):
        person('P-PORT-QUAY-W%d' % k, 'hivis_helmet', 'walk', (x, y0, QZ), 0.0 if y1 < y0 else math.pi, 50 + k, 'male',
               0.3 + 0.1 * k, 0.5 + 0.1 * k, 'walk', 0.25 * k, [(1, (x, y0)), (F_END, (x, y0 + (y1 - y0) * 0.45))], lod='L1')
    log('people', NPEOPLE)

# ------------------------------------------------------------------------------------------------ camera
cam = sklib.camera('CAM', 35, (OC[0], OC[1], 60), (OC[0], OC[1] + 0.01, 0))
DOOR_FACE = TRUCK_X + CL_ / 2 - 0.055
CAMZ_DOOR = DOOR_BASE + 1.45
AIMS = [
    (1, (OC[0], OC[1], 60.0), None, 35),
    (30, (-70.0, -150.0, 92.0), (110.0, -60.0, 0.0), 35),
    (70, (3.0, -112.0, 11.0), (-8.0, -52.0, 9.0), 30),
    (110, (3.0, -62.0, 13.0), (-9.0, -12.0, 15.0), 29),
    (150, (3.5, -14.0, 19.0), (SLOT[0], 0.0, 21.0), 28),
    (168, (11.0, 1.0, 21.5), (SLOT[0], 0.0, 21.0), 28),
    (185, (16.5, 21.0, 23.5), (SLOT[0], 0.0, 18.0), 28),
    (204, (19.0, 23.0, 24.0), (SLOT[0], 0.0, 16.6), 28),
    (215, (19.5, 23.5, 24.0), (SLOT[0], 0.4, 16.3), 28),
    (240, (64.0, 24.0, 5.5), (10.0, 23.0, 10.0), 35),
    (F_END, (DOOR_FACE + 1.2, TRUCK_Y, CAMZ_DOOR), (DOOR_FACE - 20.0, TRUCK_Y, CAMZ_DOOR), 50),
]
KEYS = []
for f, loc, aim, lens in AIMS:
    e = Euler((0, 0, 0)) if aim is None else (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    KEYS.append((f, loc, e, lens))
sklib.camera_path(cam, KEYS)
log('camera')

s.render.use_simplify = False
sklib.finish('port', 'ext')
log('DONE containers', NCONT, 'vehicles', NVEH, 'people', NPEOPLE)
