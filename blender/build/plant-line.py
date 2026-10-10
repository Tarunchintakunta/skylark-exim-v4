"""S8 plant-line.blend -- v-qc (1-192), v-grade (192-383), v-peel (383-574), v-wash (574-765), kind int.
One continuous camera flight UPSTREAM through the Anandapuram processing line (the film runs the process backwards):
BRIDGE_BELT top-down -> QC sampling -> lab bench -> roller grader -> peeling hall -> receiving/wash bay -> BRIDGE_DOCK.

    Blender -b --factory-startup --python plant-line.py [-- --stills f1,f2,..] [-- --fast]

World layout (metres, Z up, floor z=0, product flows toward -X, camera travels toward +X):
  belt y=0  x -8..10.5 (into the freezer wall at x=-8)  | QC station x~2.6 y-1.4 | lab x 2.4..9, y -5.4..-3
  grader x 11..21.5 y~0.6 | peel tables x 26..40 at y=+-2.4 | partition x=43 | receiving bay x 43..58 (tiled wall y=4.5)
  dock door east wall x=58, y -1.6..1.6; yard z=-1.2; reefer truck rear at x=60.
"""
import inspect
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
from sklib import _bm_box, _bm_cyl, D2R  # noqa: E402

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
STILLS = [int(x) for x in ARGS[ARGS.index('--stills') + 1].split(',')] if '--stills' in ARGS else []
FAST = '--fast' in ARGS          # no people (layout iterations)
STILL_DIR = REPO + '/assets-src/blender/stills/plant-line/'
TAG = ARGS[ARGS.index('--tag') + 1] if '--tag' in ARGS else 'r1'

scene = sklib.reset()
import people  # noqa: E402  (after reset: re-enables MPFB)

# lab_coat in people.py has no hairnet/mask/gloves; the brief wants them -> runtime patch of _outfit (lib untouched)
_src = inspect.getsource(people._outfit)
_old = "            coat((0.82, 0.82, 0.8), 'lab_coat', length=knee + 0.02)\n"
assert _old in _src
exec(compile(_src.replace(_old, _old + "            gloves((0.25, 0.42, 0.75)); headcover((0.84, 0.84, 0.84), 'hairnet', 'net', 0.018)"
                                         "; mask((0.55, 0.7, 0.8))\n"), people.__file__, 'exec'), people.__dict__)

RNG = random.Random(8)
F_END = 765
LED_K = sklib.kelvin_rgb(5000)


def col(name, parent=None):
    return sklib.collection(name, parent)


C_BUILD = col('PLANT_BUILDING')
C_BELT = col('BRIDGE_BELT')
C_LAB = col('A-PLANT-LAB')
C_GRADE = col('A-GRADER')
C_PEEL = col('A-PEEL')
C_WASH = col('A-WASH')
C_DOCK = col('BRIDGE_DOCK')
C_PEOPLE = col('PEOPLE')
C_LIGHT = col('LIGHTS')

# ------------------------------------------------------------------------------------------------------ materials
M = {}
M['wall'] = sklib.painted_metal((0.86, 0.87, 0.86), wear=0.06, contrast=0.22)       # PUF panel skin
M['floor'] = sklib.epoxy_floor((0.60, 0.65, 0.63), wear=0.12)
M['ss'] = sklib.stainless(0.08)
M['alu'] = sklib.aluminium(0.1)
M['galv'] = sklib.galvanised(0.2)
M['tile'] = sklib.white_tiles(0.08)
M['plaster'] = sklib.white_wall(0.04)
M['rubber'] = sklib.plastic((0.025, 0.025, 0.025), 0.2, name='rubber_black')
M['tray'] = sklib.pbr('plastic_white_clean', 'blue_metal_plate', tint=(0.86, 0.87, 0.87), wear=0.04, rough=(0.35, 0.5), nor=0.12,
                      wear_color=(0.5, 0.5, 0.48), ao_dist=0.08, var=0.03, scale=0.6, contrast=0.2)
M['laminate'] = sklib.pbr('bench_laminate', 'blue_metal_plate', tint=(0.84, 0.85, 0.84), wear=0.03, rough=(0.25, 0.4), nor=0.08,
                          wear_color=(0.5, 0.5, 0.48), ao_dist=0.05, var=0.02, scale=0.8, contrast=0.15)
M['grey_pl'] = sklib.plastic((0.30, 0.33, 0.35), 0.15, name='plastic_grey')
M['yellow'] = sklib.painted_metal((0.62, 0.45, 0.06), wear=0.25, contrast=0.5)
M['truck'] = sklib.painted_metal((0.80, 0.80, 0.78), wear=0.18, streaks=0.15, contrast=0.3)
M['concrete'] = sklib.concrete_quay(0.35)


def glass_mat(name='glass_clear', tint=(0.93, 0.97, 0.97), rough=0.02):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = tint + (1,)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = rough
    b.inputs['IOR'].default_value = 1.45
    for a, v in (('use_raytrace_refraction', True), ('surface_render_method', 'DITHERED')):
        if hasattr(m, a):
            setattr(m, a, v)
    return m


def emit_mat(name, color, strength):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = tuple(color) + (1,)
    e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


M['glass'] = glass_mat()
M['led'] = emit_mat('led_panel', LED_K, 18.0)
M['screen'] = sklib.flat('screen_dim', (0.02, 0.035, 0.03), rough=0.15, var=0.02, scale=200, **{'Coat Weight': 1.0})
M['red_lens'] = sklib.flat('lens_red', (0.35, 0.01, 0.01), rough=0.15, var=0.05, scale=80)


def water_mat(name='water_tank'):
    """Clear treated water: refractive, rippled by an animated 4D noise bump."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.86, 0.96, 0.97, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.015
    b.inputs['IOR'].default_value = 1.333
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.noise_dimensions = '4D'
    nz.inputs['Scale'].default_value = 9.0
    nz.inputs['Detail'].default_value = 4.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    w = nz.inputs['W']
    w.default_value = 0.0
    w.keyframe_insert('default_value', frame=1)
    w.default_value = F_END / 24 * 0.9
    w.keyframe_insert('default_value', frame=F_END)
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.35
    bp.inputs['Distance'].default_value = 0.004
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs[0], b.inputs['Normal'])
    for fc in sklib._fcurves(nt):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    for a, v in (('use_raytrace_refraction', True), ('surface_render_method', 'DITHERED')):
        if hasattr(m, a):
            setattr(m, a, v)
    return m


M['water'] = water_mat()


def belt_mat():
    """Stainless flat-wire mesh belt: cross rods + zig-zag links over dark gaps; UV-offset animated (belt runs -X)."""
    m = bpy.data.materials.get('belt_mesh')
    if m:
        return m
    m = bpy.data.materials.new('belt_mesh')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    loc = mp.inputs['Location']
    loc.default_value = (0, 0, 0)
    loc.keyframe_insert('default_value', frame=1)
    loc.default_value = (BELT_V * (F_END - 1) / 24, 0, 0)      # pattern moves with the shrimp (-X)
    loc.keyframe_insert('default_value', frame=F_END)
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(mp.outputs[0], sep.inputs[0])
    # rods across the belt every 12 mm (along X)
    rx = N.new('ShaderNodeMath'); rx.operation = 'MULTIPLY'; rx.inputs[1].default_value = 2 * math.pi / 0.0075
    L.new(sep.outputs['X'], rx.inputs[0])
    # zig-zag: link wires every 9 mm across, shifted by rod phase
    ly = N.new('ShaderNodeMath'); ly.operation = 'MULTIPLY'; ly.inputs[1].default_value = 2 * math.pi / 0.0125
    L.new(sep.outputs['Y'], ly.inputs[0])
    s1 = N.new('ShaderNodeMath'); s1.operation = 'COSINE'; L.new(rx.outputs[0], s1.inputs[0])
    s2 = N.new('ShaderNodeMath'); s2.operation = 'COSINE'; L.new(ly.outputs[0], s2.inputs[0])
    r1 = N.new('ShaderNodeMapRange'); L.new(s1.outputs[0], r1.inputs['Value'])
    r1.inputs['From Min'].default_value, r1.inputs['From Max'].default_value = 0.2, 0.55
    r2 = N.new('ShaderNodeMapRange'); L.new(s2.outputs[0], r2.inputs['Value'])
    r2.inputs['From Min'].default_value, r2.inputs['From Max'].default_value = 0.72, 0.9
    wire = N.new('ShaderNodeMath'); wire.operation = 'MAXIMUM'; wire.use_clamp = True
    L.new(r1.outputs[0], wire.inputs[0]); L.new(r2.outputs[0], wire.inputs[1])
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    L.new(wire.outputs[0], mix.inputs['Factor'])
    mix.inputs['A'].default_value = (0.015, 0.017, 0.018, 1)
    mix.inputs['B'].default_value = (0.5, 0.51, 0.52, 1)
    L.new(mix.outputs['Result'], b.inputs['Base Color'])
    mt = N.new('ShaderNodeMath'); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = 1.0
    L.new(wire.outputs[0], mt.inputs[0]); L.new(mt.outputs[0], b.inputs['Metallic'])
    rr = N.new('ShaderNodeMapRange'); L.new(wire.outputs[0], rr.inputs['Value'])
    rr.inputs['To Min'].default_value, rr.inputs['To Max'].default_value = 0.6, 0.22
    L.new(rr.outputs[0], b.inputs['Roughness'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.5; bp.inputs['Distance'].default_value = 0.0012
    L.new(wire.outputs[0], bp.inputs['Height']); L.new(bp.outputs[0], b.inputs['Normal'])
    for fc in sklib._fcurves(nt):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    return m


BELT_V = -0.06      # m/s
QC_Z = 0.93         # QC sampling shelf top
M['belt'] = belt_mat()


def grating_mat():
    m = bpy.data.materials.get('drain_grating')
    if m:
        return m
    m = bpy.data.materials.new('drain_grating')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    w = N.new('ShaderNodeMath'); w.operation = 'PINGPONG'; w.inputs[1].default_value = 0.012
    L.new(sep.outputs['X'], w.inputs[0])
    mr = N.new('ShaderNodeMapRange'); L.new(w.outputs[0], mr.inputs['Value'])
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = 0.003, 0.0045
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; L.new(mr.outputs[0], mix.inputs['Factor'])
    mix.inputs['A'].default_value = (0.6, 0.61, 0.62, 1); mix.inputs['B'].default_value = (0.01, 0.012, 0.012, 1)
    L.new(mix.outputs['Result'], b.inputs['Base Color'])
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    L.new(mr.outputs[0], inv.inputs[1]); L.new(inv.outputs[0], b.inputs['Metallic'])
    b.inputs['Roughness'].default_value = 0.3
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 1.0; bp.inputs['Distance'].default_value = 0.004
    L.new(inv.outputs[0], bp.inputs['Height']); L.new(bp.outputs[0], b.inputs['Normal'])
    return m


M['grate'] = grating_mat()


def wet_mat():
    """Wet floor film: glossy clear coat patches (alpha-masked), sits 1 mm above the epoxy."""
    m = bpy.data.materials.get('wet_film')
    if m:
        return m
    m = bpy.data.materials.new('wet_film')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    N, L = nt.nodes, nt.links
    b.inputs['Base Color'].default_value = (0.3, 0.33, 0.33, 1)
    b.inputs['Roughness'].default_value = 0.03
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = N.new('ShaderNodeMapRange'); L.new(nz.outputs['Fac'], mr.inputs['Value'])
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = 0.47, 0.56
    mr.inputs['To Max'].default_value = 0.65
    L.new(mr.outputs[0], b.inputs['Alpha'])
    if hasattr(m, 'surface_render_method'):
        m.surface_render_method = 'DITHERED'
    return m


M['wet'] = wet_mat()


# ---------------------------------------------------------------------------------------------------- mesh helpers
def mk(name, build, mats, coll, loc=(0, 0, 0), rot=(0, 0, 0), bev=0.006, seg=2, uv=True):
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = sklib.new_obj(name, me, coll, loc=loc, rot=rot)
    sklib.mat_to(ob, *mats, uv=uv)
    if bev:
        sklib.bevel(ob, bev, seg, 35)
    return ob


def box(name, c, size, mat, coll, bev=0.006, rot=(0, 0, 0)):
    return mk(name, lambda bm: _bm_box(bm, Vector((0, 0, 0)), size), [mat], coll, loc=c, rot=rot, bev=bev)


def frame_vis(objs, f0, f1):
    """Render-visible only in [f0, f1] (keyed hide_render) -- keeps per-frame cost to one chapter's people."""
    for o in objs:
        for f, h in ((1, f0 > 1), (f0, False), (f1 + 1, True)):
            if f < 1 or f > F_END + 1:
                continue
            o.hide_render = h
            o.keyframe_insert('hide_render', frame=f)


# --------------------------------------------------------------------------------------------- shrimp prototypes
SCANS = REPO + '/assets-src/models/plant-line/'
C_PROTO_HI = sklib.collection('SHRIMP_PROTO_HI', False)
C_PROTO_LO = sklib.collection('SHRIMP_PROTO_LO', False)


def shrimp_mats(img):
    """raw (wet grey-translucent vannamei look from the scan albedo) and peeled (pale pink-grey flesh)."""
    out = {}
    for kind in ('raw', 'peeled'):
        nm = 'shrimp_%s_%s' % (kind, img.name)
        m = bpy.data.materials.new(nm)
        m.use_nodes = True
        nt = m.node_tree
        N, L = nt.nodes, nt.links
        b = N['Principled BSDF']
        ti = N.new('ShaderNodeTexImage'); ti.image = img
        hs = N.new('ShaderNodeHueSaturation')
        L.new(ti.outputs['Color'], hs.inputs['Color'])
        mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        L.new(hs.outputs['Color'], mix.inputs['A'])
        if kind == 'raw':
            hs.inputs['Saturation'].default_value = 0.3
            hs.inputs['Value'].default_value = 0.85
            mix.inputs['B'].default_value = (0.78, 0.84, 0.86, 1)
            b.inputs['Subsurface Weight'].default_value = 0.25
            b.inputs['Roughness'].default_value = 0.32
        else:
            hs.inputs['Saturation'].default_value = 0.0
            hs.inputs['Value'].default_value = 1.25
            mix.inputs['B'].default_value = (0.84, 0.66, 0.6, 1)
            b.inputs['Subsurface Weight'].default_value = 0.5
            b.inputs['Roughness'].default_value = 0.28
        b.inputs['Subsurface Radius'].default_value = (0.006, 0.003, 0.002)
        b.inputs['Coat Weight'].default_value = 0.55
        b.inputs['Coat Roughness'].default_value = 0.12
        L.new(mix.outputs['Result'], b.inputs['Base Color'])
        out[kind] = m
    return out


def _clean_islands(bm):
    """Keep the largest connected island (drops antenna/leg fragments left by a cut)."""
    bm.verts.ensure_lookup_table()
    seen, best = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        st, isl = [v], []
        seen.add(v)
        while st:
            w = st.pop()
            isl.append(w)
            for e in w.link_edges:
                o = e.other_vert(w)
                if o not in seen:
                    seen.add(o)
                    st.append(o)
        if len(isl) > len(best):
            best = isl
    keep = set(best)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v not in keep], context='VERTS')


def make_protos():
    """6 hi + 6 lo prototypes, named so Collection Info 'separate children' order = index:
    0/1 head-on raw (tiger, greasyback), 2/3 headless raw, 4/5 peeled (tail-on). Scan: head at -X, dorsal +Z."""
    specs = [('green-tiger-prawn', 0.0112), ('greasyback-shrimp', 0.0138)]
    base = []
    for fn, s in specs:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=SCANS + fn + '-lo.glb')
        ob = [o for o in bpy.data.objects if o not in before and o.type == 'MESH'][0]
        for o in [o for o in bpy.data.objects if o not in before and o is not ob]:
            bpy.data.objects.remove(o)
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        me = ob.data
        me.transform(Matrix.Diagonal((s, s, s, 1)))
        img = [n.image for n in me.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE'][0]
        base.append((me, shrimp_mats(img)))
        bpy.data.objects.remove(ob)
    def decimated(me0, ratio):
        tmp = bpy.data.objects.new('tmp_dec', me0.copy())
        scene.collection.objects.link(tmp)
        d = tmp.modifiers.new('dec', 'DECIMATE')
        d.ratio = ratio
        bpy.context.view_layer.update()
        sklib.apply_mods(tmp)
        me = tmp.data
        bpy.data.objects.remove(tmp)
        return me      # decimate BEFORE welding: the welded scan is non-manifold and collapse stalls

    def staged(me0, stage, mat):
        me = me0.copy()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2e-5)
        xs = [v.co.x for v in bm.verts]
        zs = [v.co.z for v in bm.verts]
        x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
        if stage != 'head':
            cut = x0 + 0.37 * (x1 - x0)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x < cut], context='VERTS')
        if stage == 'peeled':
            zc = z0 + 0.50 * (z1 - z0)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < zc], context='VERTS')
            bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
        if stage != 'head':
            _clean_islands(bm)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(me)
        bm.free()
        me.materials.clear()
        me.materials.append(mat)
        me.shade_smooth()
        return me

    out = []
    for stage in ('head', 'headless', 'peeled'):
        for i, (me0, mats) in enumerate(base):
            mat = mats['peeled' if stage == 'peeled' else 'raw']
            hme = staged(me0, stage, mat)
            lme = staged(decimated(me0, 0.12), stage, mat)
            # common centre (from the hi mesh) so hi/lo swap in place
            c = sum((v.co for v in hme.vertices), Vector()) / max(1, len(hme.vertices))
            for m_ in (hme, lme):
                m_.transform(Matrix.Translation(-c))
            k = len(out)
            hi = bpy.data.objects.new('SP%d_%s_%d_hi' % (k, stage, i), hme)
            C_PROTO_HI.objects.link(hi)
            lo = bpy.data.objects.new('SP%d_%s_%d_lo' % (k, stage, i), lme)
            C_PROTO_LO.objects.link(lo)
            out.append((hi, lo))
    print('PROTOS', [(h.name, len(h.data.polygons), len(l.data.polygons), tuple(round(x, 3) for x in h.dimensions)) for h, l in out])
    return out


PROTOS = make_protos()
# lying-on-side half-thickness (instance z offset) per proto
HALF = [max(0.008, min(h.dimensions.y, h.dimensions.z) * 0.5) for h, _ in PROTOS]

_SC_GROUPS = {}


def scatter_group(proto_coll):
    if proto_coll.name in _SC_GROUPS:
        return _SC_GROUPS[proto_coll.name]
    ng = bpy.data.node_groups.new('SK_SCATTER_' + proto_coll.name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
    ci = N.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = proto_coll
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    io = N.new('GeometryNodeInstanceOnPoints')
    io.inputs['Pick Instance'].default_value = True
    na = {}
    for nm, t in (('rot', 'FLOAT_VECTOR'), ('scl', 'FLOAT'), ('pid', 'INT')):
        n = N.new('GeometryNodeInputNamedAttribute')
        n.data_type = t
        n.inputs['Name'].default_value = nm
        na[nm] = n.outputs['Attribute']
    e2r = N.new('FunctionNodeEulerToRotation')
    L.new(na['rot'], e2r.inputs['Euler'])
    L.new(gi.outputs[0], io.inputs['Points'])
    L.new(ci.outputs[0], io.inputs['Instance'])
    L.new(na['pid'], io.inputs['Instance Index'])
    L.new(e2r.outputs[0], io.inputs['Rotation'])
    L.new(na['scl'], io.inputs['Scale'])
    L.new(io.outputs[0], go.inputs[0])
    _SC_GROUPS[proto_coll.name] = ng
    return ng


def scatter(name, items, coll, hi=False, parent=None):
    """items: [(x, y, z, rx, ry, rz, scale, proto_index)] in parent/local space -> one GN instancer object."""
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(items))
    me.vertices.foreach_set('co', [c for it in items for c in it[:3]])
    a = me.attributes.new('rot', 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', [c for it in items for c in it[3:6]])
    a = me.attributes.new('scl', 'FLOAT', 'POINT')
    a.data.foreach_set('value', [it[6] for it in items])
    a = me.attributes.new('pid', 'INT', 'POINT')
    a.data.foreach_set('value', [it[7] for it in items])
    ob = sklib.new_obj(name, me, coll, parent=parent)
    gm = ob.modifiers.new('scatter', 'NODES')
    gm.node_group = scatter_group(C_PROTO_HI if hi else C_PROTO_LO)
    return ob


def lying(x, y, z, stage, rng, yaw=None, s=1.0, var=True):
    """One shrimp lying on its side (stage 0 head-on, 1 headless, 2 peeled; species random)."""
    pid = stage * 2 + rng.randrange(2)
    side = rng.choice((-1, 1))
    rz = yaw if yaw is not None else rng.uniform(0, 2 * math.pi)
    if var:
        rz += rng.uniform(-0.25, 0.25)
    sc = s * rng.uniform(0.88, 1.1)
    return (x, y, z + HALF[pid] * sc * 0.85, side * math.pi / 2 + rng.uniform(-0.2, 0.2), rng.uniform(-0.12, 0.12), rz, sc, pid)


def heap(cx, cy, z, rx, ry, n, stage_w, rng, layers=2):
    """Random pile of shrimp on a surface (ellipse rx, ry), 'layers' deep."""
    out = []
    for i in range(n):
        a, r = rng.uniform(0, 2 * math.pi), math.sqrt(rng.random())
        x, y = cx + math.cos(a) * r * rx, cy + math.sin(a) * r * ry
        lz = z + (1 - r * r) * 0.018 * layers * rng.random()
        st = rng.choices((0, 1, 2), stage_w)[0]
        out.append(lying(x, y, lz, st, rng))
    return out


# ============================================================================================ BUILDING SHELL
X0, X1, Y0, Y1, H = -8.0, 58.0, -8.0, 8.0, 6.0


def panel_wall(name, p0, p1, z0, z1, mat, coll, holes=(), pw=1.15, t=0.1, gap=0.004):
    """PUF sandwich-panel wall from p0 to p1 (xy), vertical panels pw wide with seams; holes = [(u0,u1,z0,z1)]
    in wall-local u metres (rectangular openings)."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    d = (p1 - p0).normalized()
    n = Vector((-d.y, d.x))
    yaw = math.atan2(d.y, d.x)

    def build(bm):
        u = 0.0
        while u < L - 1e-4:
            w = min(pw, L - u)
            # cut opening out of this panel column
            pieces = [(u, u + w, z0, z1)]
            for (h0, h1, hz0, hz1) in holes:
                np_ = []
                for (a0, a1, b0, b1) in pieces:
                    if a1 <= h0 or a0 >= h1:
                        np_.append((a0, a1, b0, b1))
                        continue
                    if a0 < h0:
                        np_.append((a0, h0, b0, b1))
                    if a1 > h1:
                        np_.append((h1, a1, b0, b1))
                    m0, m1 = max(a0, h0), min(a1, h1)
                    if b0 < hz0:
                        np_.append((m0, m1, b0, hz0))
                    if b1 > hz1:
                        np_.append((m0, m1, hz1, b1))
                pieces = np_
            for (a0, a1, b0, b1) in pieces:
                if a1 - a0 < 0.01 or b1 - b0 < 0.01:
                    continue
                cu = (a0 + a1) / 2
                _bm_box(bm, Vector((cu, 0, (b0 + b1) / 2)), (a1 - a0 - gap, t, b1 - b0))
            u += w

    ob = mk(name, build, [mat], coll, loc=(p0.x, p0.y, 0), rot=(0, 0, yaw), bev=0.003, seg=2)
    return ob


def shell():
    c = C_BUILD
    # floor (epoxy) incl. coving strip along walls
    box('floor', (25, 0, -0.05), (X1 - X0 + 0.4, Y1 - Y0 + 0.4, 0.1), M['floor'], c, bev=0)
    # walls: south y=-8, north y=+8, west x=-8 (belt opening into the freezer), east x=58 (dock door)
    panel_wall('wall_S', (X0, Y0), (X1, Y0), 0, H, M['wall'], c)
    panel_wall('wall_N', (X1, Y1), (X0, Y1), 0, H, M['wall'], c)
    panel_wall('wall_W', (X0, Y1), (X0, Y0), 0, H, M['wall'], c, holes=[(7.2, 8.8, 0.7, 1.35)])
    # east wall: dock opening u from Y0 -> world y = -8 + u ; opening y -1.6..1.6 -> u 6.4..9.6
    panel_wall('wall_E', (X1, Y0), (X1, Y1), -1.2, H, M['wall'], c, holes=[(6.4, 9.6, -1.3, 3.2)])
    # ceiling panels (seams along Y)

    def ceil(bm):
        x = X0
        while x < X1 - 1e-3:
            w = min(1.15, X1 - x)
            _bm_box(bm, Vector((x + w / 2, 0, H + 0.05)), (w - 0.004, Y1 - Y0, 0.1))
            x += w
    mk('ceiling', ceil, [M['wall']], c, bev=0.003)
    # coving (radiused hygienic floor-wall joint) as a 45-deg chamfer strip
    for nm, a, b in (('cove_S', (X0, Y0 + 0.05), (X1, Y0 + 0.05)), ('cove_N', (X0, Y1 - 0.05), (X1, Y1 - 0.05))):
        box(nm, ((a[0] + b[0]) / 2, a[1], 0.04), (b[0] - a[0], 0.08, 0.08), M['ss'], c, bev=0.03)
    # columns (stainless clad) along y=+-5.6 every 9 m
    for x in range(-4, 58, 9):
        for y in (-5.6, 5.6):
            box('col_%d_%d' % (x, y), (x, y, H / 2), (0.4, 0.4, H), M['ss'], c, bev=0.012)
    # overhead ducts + cable trays
    for y in (-4.2, 4.2):
        o = mk('duct_%d' % y, lambda bm: _bm_cyl(bm, Vector((0, 0, 0)), 0.3, X1 - X0 - 1, 'X', 24), [M['galv']], c,
               loc=((X0 + X1) / 2, y, H - 0.75), bev=0)
        o.data.shade_smooth()
        for x in range(-6, 57, 3):
            box('hanger_%d_%d' % (x, y), (x, y, H - 0.2), (0.04, 0.04, 0.38), M['galv'], c, bev=0.004)
            box('band_%d_%d' % (x, y), (x, y, H - 0.75), (0.05, 0.64, 0.64), M['galv'], c, bev=0.02)
        box('tray_%d' % y, ((X0 + X1) / 2, y * 0.5, H - 0.35), (X1 - X0 - 1, 0.4, 0.06), M['galv'], c, bev=0.004)
    # floor drains (stainless channel gratings)
    for nm, cx, cy, lx, ly in (('drain_belt', 1, -0.95, 18, 0.2), ('drain_grade', 16, -1.9, 10, 0.2),
                               ('drain_peel_a', 33, 0, 15, 0.22), ('drain_wash', 52.3, 0.45, 5, 0.25),
                               ('drain_dock', 55.5, 0, 0.25, 6)):
        o = box(nm, (cx, cy, 0.002), (lx, ly, 0.006), M['grate'], c, bev=0.002)
        if lx < ly:
            o.rotation_euler.z = 0
        box(nm + '_rim', (cx, cy, 0.001), (lx + 0.03, ly + 0.03, 0.002), M['ss'], c, bev=0)


def lights():
    """Ceiling LED battens (emissive) + rectangular area lights (5000 K) -> bright, even, clean interior."""
    c = C_LIGHT

    def area(name, loc, sx, sy, w, coll=c):
        L = bpy.data.lights.new(name, 'AREA')
        L.shape, L.size, L.size_y, L.energy, L.color = 'RECTANGLE', sx, sy, w, LED_K
        return sklib.new_obj(name, L, coll, loc=loc)

    def batten(bm):
        for x in range(-6, 57, 3):
            for y in (-6.0, -2.0, 2.0, 6.0):
                _bm_box(bm, Vector((x, y, H - 0.05)), (1.5, 0.22, 0.06))
    o = mk('led_housings', batten, [M['alu']], c, bev=0.006)

    def diff(bm):
        for x in range(-6, 57, 3):
            for y in (-6.0, -2.0, 2.0, 6.0):
                _bm_box(bm, Vector((x, y, H - 0.085)), (1.42, 0.16, 0.012))
    mk('led_diffusers', diff, [M['led']], c, bev=0)
    for x in range(-5, 58, 6):
        for y in (-4.0, 4.0):
            area('L_hall_%d_%d' % (x, y), (x, y, H - 0.3), 5.5, 3.6, 560)
    # lab ceiling lights
    area('L_lab_a', (4.8, -4.2, 2.9), 1.2, 0.6, 150, C_LAB)
    area('L_lab_b', (7.4, -4.2, 2.9), 1.2, 0.6, 150, C_LAB)
    # task light over the belt bridge (frame-filling BRIDGE_BELT)
    area('L_belt', (0, 0, 3.0), 2.0, 1.2, 70, C_BELT)
    # bounce fill for the dock end (exposure-matched daylight)
    area('L_dock_fill', (54, 0, 4.5), 4, 4, 600)


# ============================================================================================ BELT + QC
def belt():
    c = C_BELT
    bx0, bx1, bw, bz = -8.4, 10.8, 1.2, 0.90
    o = box('belt_surface', ((bx0 + bx1) / 2, 0, bz - 0.004), (bx1 - bx0, bw, 0.008), M['belt'], c, bev=0)
    # frame: side channels, legs, return rollers, side guards
    for s in (-1, 1):
        box('belt_side_%d' % s, ((bx0 + bx1) / 2, s * (bw / 2 + 0.04), bz - 0.05), (bx1 - bx0, 0.06, 0.14), M['ss'], C_GRADE)
        box('belt_guard_%d' % s, ((bx0 + bx1) / 2, s * (bw / 2 + 0.07), bz + 0.05), (bx1 - bx0, 0.012, 0.1), M['ss'], C_GRADE, bev=0.003)
    for x in [x * 1.6 + bx0 + 0.3 for x in range(12)]:
        for s in (-1, 1):
            box('belt_leg_%.1f_%d' % (x, s), (x, s * (bw / 2 + 0.03), bz / 2 - 0.05), (0.05, 0.05, bz - 0.1), M['ss'], C_GRADE, bev=0.005)
        box('belt_cross_%.1f' % x, (x, 0, 0.25), (0.04, bw + 0.06, 0.04), M['ss'], C_GRADE, bev=0.004)
        o = mk('belt_ret_%.1f' % x, lambda bm: _bm_cyl(bm, Vector((0, 0, 0)), 0.03, bw, 'Y', 16), [M['ss']], C_GRADE,
               loc=(x + 0.8, 0, bz - 0.2), bev=0)
        o.data.shade_smooth()
    # shrimp rows on the belt (moving with the belt); hi protos in the bridge area
    root = sklib.new_obj('belt_shrimp_root', None, c)
    root.location = (0, 0, 0)
    root.keyframe_insert('location', frame=1)
    root.location = (BELT_V * (F_END - 1) / 24, 0, 0)
    root.keyframe_insert('location', frame=F_END)
    for fc in sklib._fcurves(root):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    rng = random.Random(41)
    hi, lo = [], []
    nrow = 12
    for r in range(nrow):
        y = -0.49 + r * (0.98 / (nrow - 1))
        x = bx0 + rng.uniform(0, 0.05)
        while x < bx1 + 2.6:
            it = lying(x, y + rng.uniform(-0.012, 0.012), bz, 0, rng, yaw=(0 if r % 2 else math.pi), var=True)
            (hi if -1.3 < x < 1.3 else lo).append(it)
            x += rng.uniform(0.125, 0.15)
    scatter('belt_shrimp_hi', hi, c, hi=True, parent=root)
    scatter('belt_shrimp_lo', lo, C_GRADE, parent=root)
    # QC sampling shelf beside the belt + spare trays
    box('qc_shelf', (2.7, -1.0, QC_Z - 0.015), (1.4, 0.42, 0.03), M['ss'], C_LAB, bev=0.004)
    for x in (2.05, 3.35):
        for y in (-0.82, -1.18):
            box('qc_leg_%.2f_%.2f' % (x, y), (x, y, QC_Z / 2 - 0.015), (0.035, 0.035, QC_Z - 0.03), M['ss'], C_LAB, bev=0.004)
    box('qc_undershelf', (2.7, -1.0, 0.25), (1.35, 0.38, 0.02), M['ss'], C_LAB, bev=0.003)
    for i, x in enumerate((3.25,)):
        t = tray('qc_tray_spare', C_LAB, loc=(x, -1.0, QC_Z))
    # the hand-wash/sanitizer station on the lab wall
    box('handwash', (8.2, -2.85, 1.0), (0.6, 0.3, 0.25), M['ss'], C_LAB, bev=0.01)


def tray(name, coll, loc=(0, 0, 0), size=(0.36, 0.26, 0.05), mat=None, rot_z=0.0, parent=None):
    """Shallow moulded tray with sloped walls (origin = base centre)."""
    sx, sy, h = size

    def build(bm):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r['verts']:
            v.co.x *= sx * (1 if v.co.z > 0 else 0.9)
            v.co.y *= sy * (1 if v.co.z > 0 else 0.88)
            v.co.z = h if v.co.z > 0 else 0
        top = [f for f in bm.faces if f.normal.z > 0.9]
        bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
    ob = mk(name, build, [mat or M['tray']], coll, loc=loc, rot=(0, 0, rot_z), bev=0)
    so = ob.modifiers.new('sol', 'SOLIDIFY')
    so.thickness, so.offset = 0.003, 1.0
    sklib.bevel(ob, 0.004, 2, 40)
    if parent:
        ob.parent = parent
    return ob


# ============================================================================================ LAB
def lab():
    c = C_LAB
    lx0, lx1, ly0, ly1, lh = 2.4, 9.0, -5.4, -3.0, 3.0
    # partition (north, to the line): door u 1.2..2.4 (x 3.6..4.8), window u 2.8..6.2 (x 5.2..8.6)
    panel_wall('lab_N', (lx0, ly1), (lx1, ly1), 0, lh, M['wall'], c, holes=[(1.2, 2.4, 0, 2.25), (2.8, 6.2, 1.0, 2.2)], t=0.08)
    panel_wall('lab_E', (lx1, ly1), (lx1, ly0), 0, lh, M['wall'], c, holes=[(0.4, 2.0, 0, 2.3)], t=0.08)
    panel_wall('lab_W', (lx0, ly0), (lx0, ly1), 0, lh, M['wall'], c, t=0.08)
    panel_wall('lab_back', (lx1, ly0 - 0.04), (lx0, ly0 - 0.04), 0, lh, M['wall'], c, t=0.08)
    box('lab_ceiling', ((lx0 + lx1) / 2, (ly0 + ly1) / 2, lh + 0.03), (lx1 - lx0 + 0.1, ly1 - ly0 + 0.1, 0.06), M['wall'], c, bev=0.004)
    for x in (4.8, 7.4):
        box('lab_led_%.1f' % x, (x, -4.2, lh - 0.012), (1.2, 0.6, 0.02), M['led'], c, bev=0)
    # window glazing + frames, door frame + open door leaf
    box('lab_window', (6.9, ly1, 1.6), (3.4, 0.012, 1.2), M['glass'], c, bev=0)
    for nm, cc, sz in (('win_sill', (6.9, ly1, 0.99), (3.46, 0.12, 0.03)), ('win_head', (6.9, ly1, 2.21), (3.46, 0.1, 0.03)),
                       ('win_l', (5.19, ly1, 1.6), (0.03, 0.1, 1.24)), ('win_r', (8.61, ly1, 1.6), (0.03, 0.1, 1.24)),
                       ('win_mul', (6.9, ly1, 1.6), (0.03, 0.06, 1.2)),
                       ('door_l', (3.59, ly1, 1.13), (0.04, 0.12, 2.26)), ('door_r', (4.81, ly1, 1.13), (0.04, 0.12, 2.26)),
                       ('door_h', (4.2, ly1, 2.27), (1.26, 0.12, 0.04)),
                       ('door2_l', (lx1, -3.39, 1.15), (0.12, 0.04, 2.3)), ('door2_r', (lx1, -5.01, 1.15), (0.12, 0.04, 2.3)),
                       ('door2_h', (lx1, -4.2, 2.31), (0.12, 1.66, 0.04))):
        box(nm, cc, sz, M['alu'], c, bev=0.004)
    # door leaf swung open into the lab (glazed vision panel)
    leaf = box('lab_door_leaf', (3.62, ly1 - 0.6, 1.1), (0.04, 1.15, 2.2), M['wall'], c, bev=0.006)
    box('lab_door_vision', (3.6, ly1 - 0.6, 1.55), (0.05, 0.4, 0.6), M['glass'], c, bev=0)
    box('lab_floor', ((lx0 + lx1) / 2, (ly0 + ly1) / 2, 0.003), (lx1 - lx0, ly1 - ly0, 0.004),
        sklib.epoxy_floor((0.70, 0.72, 0.72), wear=0.08), c, bev=0)
    # bench along the back wall: cabinets + laminate top (z 0.88) + upstand
    bz = 0.88
    bench_y = ly0 + 0.33
    box('bench_top', (5.8, bench_y, bz - 0.02), (6.0, 0.68, 0.04), M['laminate'], c, bev=0.006)
    box('bench_upstand', (5.8, ly0 + 0.01, bz + 0.05), (6.0, 0.02, 0.1), M['laminate'], c, bev=0.003)
    for i in range(6):
        x = 3.3 + i * 1.0
        box('bench_cab_%d' % i, (x, bench_y + 0.02, 0.43), (0.97, 0.6, 0.82), M['tray'], c, bev=0.008)
        box('bench_handle_%d' % i, (x, bench_y - 0.29, 0.75), (0.25, 0.02, 0.015), M['ss'], c, bev=0.003)
        box('bench_kick_%d' % i, (x, bench_y + 0.05, 0.04), (0.97, 0.55, 0.08), M['grey_pl'], c, bev=0.003)
    # sink + gooseneck tap at x 7.9
    box('sink_bowl', (7.9, bench_y, bz - 0.01), (0.5, 0.4, 0.02), M['ss'], c, bev=0.004)
    sink = mk('sink_basin', lambda bm: tray_bm(bm, 0.46, 0.36, 0.2), [M['ss']], c, loc=(7.9, bench_y, bz - 0.2), bev=0)
    sink.modifiers.new('sol', 'SOLIDIFY').thickness = 0.003
    tap = mk('tap', lambda bm: (_bm_cyl(bm, Vector((0, 0, 0.15)), 0.012, 0.3, 'Z', 12),
                               _bm_cyl(bm, Vector((0, 0.08, 0.3)), 0.011, 0.17, 'Y', 12),
                               _bm_cyl(bm, Vector((0, 0.16, 0.26)), 0.011, 0.09, 'Z', 12)),
             [M['ss']], c, loc=(7.9, ly0 + 0.08, bz), bev=0)
    tap.data.shade_smooth()
    # wall shelf + reagent bottles + glassware (left part only: upper right of the frame stays plain wall)
    box('wall_shelf', (7.3, ly0 + 0.15, 1.75), (2.4, 0.26, 0.025), M['laminate'], c, bev=0.004)
    box('wall_cab', (7.3, ly0 + 0.17, 2.3), (2.4, 0.32, 0.7), M['tray'], c, bev=0.008)
    rng = random.Random(5)
    for i in range(9):
        x = 6.25 + i * 0.24
        h = rng.choice((0.16, 0.2, 0.24))
        g = mk('bottle_%d' % i, lambda bm, h=h: _bm_cyl(bm, Vector((0, 0, h / 2)), 0.04, h, 'Z', 16), [M['glass']], c,
               loc=(x, ly0 + 0.15, 1.765), bev=0.006)
        g.data.shade_smooth()
        mk('bottle_cap_%d' % i, lambda bm, h=h: _bm_cyl(bm, Vector((0, 0, h + 0.015)), 0.022, 0.03, 'Z', 12),
           [M['grey_pl'] if i % 2 else M['tray']], c, loc=(x, ly0 + 0.15, 1.765), bev=0.003)
    # glassware on the bench (beakers, cylinders), sample bags, rack
    for i, (x, r, h) in enumerate(((6.55, 0.045, 0.12), (6.7, 0.035, 0.09), (6.42, 0.025, 0.24), (7.15, 0.05, 0.14))):
        g = mk('beaker_%d' % i, lambda bm, r=r, h=h: tray_bm(bm, r * 2, r * 2, h, round_=True), [M['glass']], c,
               loc=(x, bench_y + 0.12, bz), bev=0)
        g.modifiers.new('sol', 'SOLIDIFY').thickness = 0.002
        g.data.shade_smooth()
    for i in range(4):
        box('sample_bag_%d' % i, (3.35 + i * 0.17, bench_y + 0.12 + (i % 2) * 0.03, bz + 0.012), (0.15, 0.22, 0.022),
            M['glass'], c, bev=0.008, rot=(0, 0, 0.1 * (i - 1.5)))
    # balance (precision bench scale, blank dim display) at the tray spot; lamp; probe; filled at runtime by tech()
    return bench_y, bz


def tray_bm(bm, sx, sy, h, round_=False):
    if round_:
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=sx / 2, radius2=sx / 2, depth=h,
                                  matrix=Matrix.Translation((0, 0, h / 2)))
    else:
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r['verts']:
            v.co.x *= sx
            v.co.y *= sy
            v.co.z = h if v.co.z > 0 else 0
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')


def balance(c, loc):
    x, y, z = loc
    box('balance_base', (x, y, z + 0.035), (0.34, 0.4, 0.07), M['tray'], c, bev=0.012)
    box('balance_pan', (x, y + 0.03, z + 0.078), (0.3, 0.3, 0.012), M['ss'], c, bev=0.004)
    box('balance_head', (x, y - 0.17, z + 0.1), (0.2, 0.06, 0.07), M['tray'], c, bev=0.01, rot=(0.5, 0, 0))
    box('balance_display', (x, y - 0.2, z + 0.105), (0.13, 0.004, 0.035), M['screen'], c, bev=0, rot=(0.5, 0, 0))
    return z + 0.084


def lamp(c, base, target):
    """Bench magnifier lamp: clamp, two arms, ring head with LED ring above the sample."""
    b, t = Vector(base), Vector(target)
    elbow = Vector(((b.x + t.x) / 2, b.y + 0.05, max(b.z, t.z) + 0.42))
    head = t + Vector((0.08, -0.2, 0.4))
    box('lamp_clamp', b + Vector((0, 0, 0.03)), (0.06, 0.08, 0.06), M['grey_pl'], c, bev=0.006)
    for nm, p, q in (('lamp_arm1', b + Vector((0, 0, 0.05)), elbow), ('lamp_arm2', elbow, head + Vector((0, 0.12, 0.02)))):
        d = q - p
        o = mk(nm, lambda bm, d=d: _bm_cyl(bm, Vector((0, 0, d.length / 2)), 0.009, d.length, 'Z', 10), [M['alu']], c,
               loc=p, bev=0)
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        o.data.shade_smooth()
    ring = mk('lamp_head', lambda bm: _bm_cyl(bm, Vector((0, 0, 0)), 0.11, 0.035, 'Z', 32), [M['tray']], c, loc=head, bev=0.006)
    ring.data.shade_smooth()
    mk('lamp_lens', lambda bm: _bm_cyl(bm, Vector((0, 0, -0.019)), 0.075, 0.004, 'Z', 32), [M['glass']], c, loc=head, bev=0)
    mk('lamp_ring_led', lambda bm: _bm_cyl(bm, Vector((0, 0, -0.019)), 0.095, 0.003, 'Z', 32),
       [emit_mat('lamp_led', LED_K, 6.0)], c, loc=head, bev=0)
    L = bpy.data.lights.new('L_lamp', 'SPOT')
    L.energy, L.spot_size, L.color, L.shadow_soft_size = 25, 1.3, LED_K, 0.09
    sklib.new_obj('L_lamp', L, c, loc=head - Vector((0, 0, 0.03)), rot=(0, 0, 0))


# ============================================================================================ GRADER
def grader():
    c = C_GRADE
    gx0, gx1, gy, gz = 11.0, 20.0, 0.6, 1.1      # roller bed (top at gz), flow toward -X
    w = 1.3
    # frame legs + longitudinal rails
    for x in (gx0 + 0.2, (gx0 + gx1) / 2, gx1 - 0.2):
        for s in (-1, 1):
            box('gr_leg_%.1f_%d' % (x, s), (x, gy + s * (w / 2 + 0.05), (gz - 0.15) / 2), (0.08, 0.08, gz - 0.15), M['ss'], c, bev=0.008)
            box('gr_foot_%.1f_%d' % (x, s), (x, gy + s * (w / 2 + 0.05), 0.01), (0.14, 0.14, 0.02), M['ss'], c, bev=0.004)
    for s in (-1, 1):
        box('gr_side_%d' % s, ((gx0 + gx1) / 2, gy + s * (w / 2 + 0.05), gz - 0.07), (gx1 - gx0, 0.05, 0.26), M['ss'], c, bev=0.01)
    box('gr_trough', ((gx0 + gx1) / 2, gy, gz - 0.3), (gx1 - gx0, w, 0.04), M['ss'], c, bev=0.006)
    # rollers: 9 pairs across, diverging gap; animated spin
    n_r = 9
    for i in range(n_r):
        y = gy - w / 2 + 0.07 + i * (w - 0.14) / (n_r - 1)
        o = mk('gr_roller_%d' % i, lambda bm: _bm_cyl(bm, Vector((0, 0, 0)), 0.045, gx1 - gx0 - 0.1, 'X', 20), [M['ss']], c,
               loc=((gx0 + gx1) / 2, y, gz - 0.05), bev=0)
        o.data.shade_smooth()
        d = o.driver_add('rotation_euler', 0).driver
        d.type, d.expression = 'SCRIPTED', 'frame * %.3f' % (0.5 * (1 if i % 2 else -1))
    # motor + gearbox housing at the downstream end, guards
    box('gr_motor', (gx0 - 0.15, gy - 0.4, gz - 0.35), (0.4, 0.35, 0.35), M['grey_pl'], c, bev=0.02)
    box('gr_gearbox', (gx0 - 0.1, gy + 0.2, gz - 0.2), (0.25, 0.45, 0.3), M['ss'], c, bev=0.015)
    # hopper at the upstream end (tapered)
    hx = gx1 + 0.75

    def hop(bm):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r['verts']:
            top = v.co.z > 0
            v.co.x *= 1.3 if top else 0.6
            v.co.y *= 1.4 if top else 0.9
            v.co.z = 0.85 if top else 0
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES_ONLY')
    hp = mk('gr_hopper', hop, [M['ss']], c, loc=(hx, gy, gz + 0.35), bev=0)
    hp.modifiers.new('sol', 'SOLIDIFY').thickness = 0.004
    sklib.bevel(hp, 0.006, 2, 40)
    for x in (hx - 0.55, hx + 0.55):
        for s in (-1, 1):
            box('gr_hleg_%.1f_%d' % (x, s), (x, gy + s * 0.6, (gz + 0.35) / 2), (0.07, 0.07, gz + 0.35), M['ss'], c, bev=0.006)
    box('gr_platform', (hx + 1.3, gy, 1.075), (1.2, 1.6, 0.05), M['grate'], c, bev=0.004)
    for x in (hx + 0.75, hx + 1.85):
        for s in (-1, 1):
            box('gr_pleg_%.1f_%d' % (x, s), (x, gy + s * 0.75, 0.53), (0.06, 0.06, 1.06), M['ss'], c, bev=0.005)
    rng = random.Random(77)
    # shrimp: on rollers (moving -X), heap in hopper
    items = []
    for i in range(520):
        x, y = rng.uniform(gx0 + 0.1, gx1), gy + rng.uniform(-w / 2 + 0.08, w / 2 - 0.08)
        items.append(lying(x, y, gz - 0.005, 0, rng, yaw=rng.choice((0, math.pi))))
    root = sklib.new_obj('gr_shrimp_root', None, c)
    root.keyframe_insert('location', frame=1)
    root.location = (-0.9, 0, 0)
    root.keyframe_insert('location', frame=F_END)
    for fc in sklib._fcurves(root):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    scatter('gr_shrimp_rollers', items, c, parent=root)
    scatter('gr_shrimp_hopper', heap(hx, gy, gz + 0.95, 0.85, 0.95, 380, (1, 0, 0), rng, layers=4), c)
    # 4 chutes to the south side + crates of ice under them (sizes)
    chutes = []
    for k, x in enumerate((12.4, 14.4, 16.4, 18.4)):
        y0, y1 = gy - w / 2 - 0.05, gy - w / 2 - 0.75
        z0, z1 = gz - 0.32, 0.62

        def ch(bm, y0=y0, y1=y1, z0=z0, z1=z1):
            pts = [(-0.2, y0, z0), (0.2, y0, z0), (0.2, y1, z1), (-0.2, y1, z1)]
            vs = [bm.verts.new(p) for p in pts]
            bm.faces.new(vs)
            for sx in (-0.2, 0.2):      # side walls
                a = [bm.verts.new(p) for p in ((sx, y0, z0), (sx, y1, z1), (sx, y1, z1 + 0.09), (sx, y0, z0 + 0.09))]
                bm.faces.new(a)
        o = mk('gr_chute_%d' % k, ch, [M['ss']], c, loc=(x, 0, 0), bev=0)
        o.modifiers.new('sol', 'SOLIDIFY').thickness = 0.003
        sklib.bevel(o, 0.004, 2, 40)
        chutes.append((x, y1, z1))
    return chutes, rng


def crate_full(name, color, rng, stage_w=(1, 0, 0), n=55, coll=None, hi=False):
    """Unlinked collection: crate + crushed ice + shrimp nested in the ice (origin at crate base centre)."""
    cc = sklib.collection(name, False)
    cr = sklib.crate(color, name + '_crate', cc, wear=0.25)
    ice = sklib.crushed_ice_fill(cr, density=1.0, name=name + '_ice', coll=cc, seed=rng.randrange(999), depth=0.08)
    top = 0.25 - 0.035 + 0.01
    sh = scatter(name + '_shrimp', heap(0, 0, top + 0.004, 0.24, 0.14, n, stage_w, rng, layers=2), cc, hi=hi)
    cap = sklib.crushed_ice_fill((-0.24, 0.24, -0.15, 0.15, top, top + 0.02), density=0.12, name=name + '_ice2',
                                 coll=cc, seed=rng.randrange(999), chunk=0.016, mound=0.0)
    return cc


CRATE_COLS = [(0.05, 0.22, 0.55), (0.55, 0.06, 0.05), (0.06, 0.32, 0.18), (0.06, 0.25, 0.58)]


def grade_crates(chutes, rng):
    cs = [crate_full('A-CRATE-SHRIMP_%d' % i, CRATE_COLS[i % 4], random.Random(10 + i)) for i in range(4)]
    for k, (x, y1, z1) in enumerate(chutes):
        # low stainless stand + crate under each chute lip
        box('gr_stand_%d' % k, (x, y1 - 0.18, 0.15), (0.66, 0.46, 0.3), M['ss'], C_GRADE, bev=0.01)
        sklib.instance(cs[k], (x, y1 - 0.18, 0.3), 0.0, 'I_crate_grade_%d' % k, C_GRADE)
        # falling shrimp: chute lip -> crate, looping (keyed + Cycles), 3 per chute, staggered
        for j in range(3):
            pid = rng.randrange(2)
            o = bpy.data.objects.new('gr_fall_%d_%d' % (k, j), PROTOS[pid][0].data)
            C_GRADE.objects.link(o)
            per = 16
            off = j * per / 3 + k * 2.7
            for t in range(0, per + 1, 2):
                u = t / per
                o.location = (x + rng.uniform(-0.1, 0.1) * 0.3, y1 - 0.05 - 0.18 * u, z1 + 0.02 - 0.35 * u * u)
                o.rotation_euler = (math.pi / 2 + u * 2.4, 0.3 * u, rng.uniform(-0.3, 0.3))
                o.keyframe_insert('location', frame=1 + off + t)
                o.keyframe_insert('rotation_euler', frame=1 + off + t)
            for fc in sklib._fcurves(o):
                fc.modifiers.new('CYCLES')
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'
    # extra crates: stacks waiting near the line
    for i, (x, y, n) in enumerate(((12.5, -2.9, 3), (13.2, -2.9, 2), (21.0, -1.6, 3), (22.5, 2.6, 2))):
        for z in range(n):
            sklib.instance(cs[(i + z) % 4], (x, y, z * 0.25), 0.05 * ((i + z) % 3 - 1), 'I_crate_stack_%d_%d' % (i, z), C_GRADE)
    return cs


def sorting_table(rng):
    c = C_GRADE
    tx0, tx1, ty, tz = 12.0, 18.6, 2.5, 0.9
    box('sort_top', ((tx0 + tx1) / 2, ty, tz - 0.02), (tx1 - tx0, 0.9, 0.04), M['ss'], c, bev=0.008)
    for s in (-1, 1):
        box('sort_lip_%d' % s, ((tx0 + tx1) / 2, ty + s * 0.44, tz + 0.02), (tx1 - tx0, 0.02, 0.05), M['ss'], c, bev=0.004)
    for x in (tx0 + 0.15, (tx0 + tx1) / 2, tx1 - 0.15):
        for s in (-1, 1):
            box('sort_leg_%.1f_%d' % (x, s), (x, ty + s * 0.38, tz / 2 - 0.02), (0.05, 0.05, tz - 0.04), M['ss'], c, bev=0.005)
    box('sort_shelf', ((tx0 + tx1) / 2, ty, 0.2), (tx1 - tx0 - 0.1, 0.8, 0.02), M['ss'], c, bev=0.004)
    scatter('sort_shrimp', heap(15.3, ty - 0.1, tz, 3.0, 0.24, 420, (1, 0, 0), rng, layers=1), c)
    for i, x in enumerate((12.8, 14.6, 16.4, 18.0)):
        t = tray('sort_tray_%d' % i, c, loc=(x, ty + 0.25, tz))
        scatter('sort_tray_shrimp_%d' % i, heap(x, ty + 0.25, tz + 0.006, 0.14, 0.09, 22, (1, 0, 0), rng, layers=1), c)


# ============================================================================================ PEELING HALL
def peel_tables(rng):
    c = C_PEEL
    tx0, tx1, tz, tw = 26.0, 40.0, 0.86, 0.9
    seg_c = sklib.collection('A-PEEL-ICEBED', False)
    # one 2 m ice-bed segment (crushed ice + shrimp heaps), instanced 7x per table
    sklib.crushed_ice_fill((-0.98, 0.98, -0.16, 0.16, tz + 0.005, tz + 0.05), density=1.2, name='icebed_ice', coll=seg_c,
                           seed=3, chunk=0.02, mound=0.03, max_chunks=2500)
    scatter('icebed_shrimp', heap(0, 0, tz + 0.045, 0.95, 0.12, 170, (1, 0, 0), random.Random(4), layers=2), seg_c)
    trays = []
    for ti, ty in enumerate((-2.4, 2.4)):
        box('peel_top_%d' % ti, ((tx0 + tx1) / 2, ty, tz - 0.02), (tx1 - tx0, tw, 0.04), M['ss'], c, bev=0.008)
        for s in (-1, 1):
            box('peel_lip_%d_%d' % (ti, s), ((tx0 + tx1) / 2, ty + s * (tw / 2 - 0.01), tz + 0.025), (tx1 - tx0, 0.02, 0.05), M['ss'], c, bev=0.004)
        box('peel_trough_%d' % ti, ((tx0 + tx1) / 2, ty, tz + 0.005), (tx1 - tx0 - 0.1, 0.38, 0.02), M['ss'], c, bev=0.004)
        for x in [tx0 + 0.2 + i * (tx1 - tx0 - 0.4) / 6 for i in range(7)]:
            for s in (-1, 1):
                box('peel_leg_%d_%.1f_%d' % (ti, x, s), (x, ty + s * 0.36, tz / 2 - 0.02), (0.05, 0.05, tz - 0.04), M['ss'], c, bev=0.005)
            box('peel_rail_%d_%.1f' % (ti, x), (x, ty, 0.18), (0.04, 0.72, 0.04), M['ss'], c, bev=0.004)
        for k in range(7):
            sklib.instance(seg_c, (tx0 + 1.0 + k * 2.0, ty, 0), 0.0 if k % 2 else math.pi, 'I_icebed_%d_%d' % (ti, k), c)
        box('peel_shelf_%d' % ti, ((tx0 + tx1) / 2, ty, 0.25), (tx1 - tx0 - 0.1, tw - 0.1, 0.02), M['ss'], c, bev=0.004)
        # water spray bar over the table
        o = mk('peel_spraybar_%d' % ti, lambda bm: _bm_cyl(bm, Vector((0, 0, 0)), 0.018, tx1 - tx0, 'X', 12), [M['ss']], c,
               loc=((tx0 + tx1) / 2, ty, 1.95), bev=0)
        o.data.shade_smooth()
    return tx0, tx1, tz


def worker_trays(rng, x, ty, side, tz, i):
    """Per-worker trays at the table edge: tray of head-on (in), tray of the worker's output (headless or peeled),
    small bowl for heads/shells. side = +1 worker on +y side of the table."""
    c = C_PEEL
    ey = ty + side * 0.27
    stage = (1, 2, 2, 1)[i % 4]
    items = []
    t1 = tray('ptray_in_%d' % i, c, loc=(x - 0.2, ey, tz), size=(0.3, 0.22, 0.045), mat=M['ss'])
    items += heap(x - 0.2, ey, tz + 0.006, 0.11, 0.07, 14, (1, 0, 0), rng, layers=1)
    t2 = tray('ptray_out_%d' % i, c, loc=(x + 0.22, ey, tz), size=(0.3, 0.22, 0.045), mat=M['tray'])
    items += heap(x + 0.22, ey, tz + 0.006, 0.11, 0.07, 13, [(0, 1, 0), (0, 0, 1)][stage - 1], rng, layers=1)
    bowl = mk('pbowl_%d' % i, lambda bm: tray_bm(bm, 0.16, 0.16, 0.06, round_=True), [M['tray']], c, loc=(x + 0.5, ey, tz), bev=0)
    bowl.modifiers.new('sol', 'SOLIDIFY').thickness = 0.003
    bowl.data.shade_smooth()
    return items


# ============================================================================================ RECEIVING / WASH
def wash(rng):
    c = C_WASH
    # tiled wall (north side of the bay) + partition to the peeling hall with a wide opening
    box('rec_tile_wall', (50.5, 4.55, H / 2), (15.0, 0.1, H), M['tile'], c, bev=0.003)
    panel_wall('rec_partition', (43.0, Y0), (43.0, Y1), 0, H, M['wall'], c, holes=[(5.8, 10.2, 0, 4.4)], t=0.1)
    # wash tank: 3.5 x 1.4 x 0.75, stainless, water at 0.66
    tx0, tx1, ty0, ty1, th = 50.5, 54.0, 0.8, 2.2, 0.75

    def tank(bm):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r['verts']:
            v.co.x = tx0 if v.co.x < 0 else tx1
            v.co.y = ty0 if v.co.y < 0 else ty1
            v.co.z = th if v.co.z > 0 else 0.12
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES_ONLY')
    o = mk('wash_tank', tank, [M['ss']], c, bev=0)
    so = o.modifiers.new('sol', 'SOLIDIFY')
    so.thickness, so.offset = 0.025, 1.0
    sklib.bevel(o, 0.006, 2, 40)
    box('wash_rim', ((tx0 + tx1) / 2, ty0 - 0.02, th + 0.01), (tx1 - tx0 + 0.05, 0.06, 0.02), M['ss'], c, bev=0.006)
    for x in (tx0 + 0.1, (tx0 + tx1) / 2, tx1 - 0.1):
        for y in (ty0 + 0.05, ty1 - 0.05):
            box('wash_leg_%.1f_%.1f' % (x, y), (x, y, 0.06), (0.08, 0.08, 0.12), M['ss'], c, bev=0.006)
    wz = 0.66
    wt = box('wash_water', ((tx0 + tx1) / 2, (ty0 + ty1) / 2, wz - 0.25), (tx1 - tx0 - 0.03, ty1 - ty0 - 0.03, 0.5), M['water'], c, bev=0)
    # perforated basket floor + submerged shrimp
    box('wash_basket', ((tx0 + tx1) / 2, (ty0 + ty1) / 2, 0.3), (tx1 - tx0 - 0.1, ty1 - ty0 - 0.1, 0.01), M['grate'], c, bev=0)
    sub = heap((tx0 + tx1) / 2, (ty0 + ty1) / 2, 0.31, 1.6, 0.6, 600, (1, 0, 0), rng, layers=6)
    sub += [(x, y, rng.uniform(0.45, wz - 0.03), rx, ry, rz, s, p) for (x, y, z, rx, ry, rz, s, p) in
            heap((tx0 + tx1) / 2, (ty0 + ty1) / 2, 0.3, 1.6, 0.6, 140, (1, 0, 0), rng)]
    scatter('wash_shrimp', sub, c)
    # inflow pipe from the tiled wall + falling stream into the tank (stays inside)
    px, py = 53.6, 1.75
    pipe = mk('wash_pipe', lambda bm: (_bm_cyl(bm, Vector((0, 0, 0.6)), 0.03, 1.2, 'Z', 16),
                                       _bm_cyl(bm, Vector((0, 0, 1.2)), 0.03, 0.12, 'Y', 16)), [M['ss']], c,
              loc=(px, 4.45, 0.2), bev=0)
    pipe.data.shade_smooth()
    mk('wash_pipe_arm', lambda bm: _bm_cyl(bm, Vector((0, 0, 0)), 0.03, 4.45 - py, 'Y', 16), [M['ss']], c,
       loc=(px, (4.45 + py) / 2, 1.4), bev=0).data.shade_smooth()
    mk('wash_spout', lambda bm: _bm_cyl(bm, Vector((0, 0, 0)), 0.032, 0.14, 'Z', 16), [M['ss']], c,
       loc=(px, py, 1.34), bev=0).data.shade_smooth()
    st = mk('wash_stream', lambda bm: _bm_cyl(bm, Vector((0, 0, 0)), 0.024, 1.27 - wz, 'Z', 16, r2=0.016), [M['water']], c,
            loc=(px, py, (1.27 + wz) / 2), bev=0)
    st.data.shade_smooth()
    # splash ring (foam/bubbles) where the stream hits the surface
    foam = sklib.flat('foam_bubbles', (0.9, 0.93, 0.94), rough=0.4, var=0.25, scale=180, bump=0.4, **{'Alpha': 0.75})
    foam.surface_render_method = 'DITHERED'
    mk('wash_splash', lambda bm: _bm_cyl(bm, Vector((0, 0, 0)), 0.16, 0.012, 'Z', 24), [foam], c, loc=(px, py, wz + 0.004), bev=0)
    # overflow weir on the south wall -> thin sheet down into the floor gutter
    ox = 51.1
    mk('wash_weir', lambda bm: _bm_box(bm, Vector((0, 0, 0)), (0.5, 0.06, 0.03)), [M['ss']], c, loc=(ox, ty0 - 0.03, wz - 0.01), bev=0.004)

    def sheet(bm):
        pts = []
        for i in range(9):
            u = i / 8
            pts.append((ty0 - 0.06 - 0.12 * u * u, wz - 0.02 - (wz - 0.02) * u))
        prev = None
        for (y, z) in pts:
            a, b = bm.verts.new((-0.22, y, z)), bm.verts.new((0.22, y, z))
            if prev:
                bm.faces.new((prev[0], prev[1], b, a))
            prev = (a, b)
    mk('wash_overflow_sheet', sheet, [M['water']], c, loc=(ox, 0, 0), bev=0)
    box('wash_gutter', (52.3, ty0 - 0.3, -0.005), (4.4, 0.25, 0.012), M['grate'], c, bev=0.002)
    for i in range(3):
        box('wet_floor_%d' % i, (50.7 + i * 1.6, 0.1 + 0.3 * (i % 2), 0.0015), (1.8, 1.5, 0.001), M['wet'], c, bev=0)
    # receiving platform scale with indicator (blank dim display), crates on it
    sx, sy = 55.0, -3.3
    box('scale_plat', (sx, sy, 0.05), (1.0, 1.0, 0.1), M['ss'], c, bev=0.01)
    box('scale_base', (sx, sy, 0.02), (1.06, 1.06, 0.04), M['grey_pl'], c, bev=0.006)
    box('scale_col', (sx + 0.62, sy + 0.42, 0.55), (0.05, 0.05, 1.1), M['ss'], c, bev=0.004)
    box('scale_head', (sx + 0.62, sy + 0.42, 1.18), (0.3, 0.1, 0.2), M['ss'], c, bev=0.012)
    box('scale_screen', (sx + 0.62, sy + 0.366, 1.2), (0.2, 0.004, 0.07), M['screen'], c, bev=0)
    return (tx0, tx1, ty0, ty1, th, wz), (sx, sy)


def wash_crates(rng, scale_xy):
    cs = [crate_full('A-CRATE-SHRIMP_W%d' % i, CRATE_COLS[i % 4], random.Random(40 + i)) for i in range(4)]
    k = 0
    spots = [(scale_xy[0], scale_xy[1], 0.1, 2)]   # on the scale: 2 high
    spots += [(56.6, -3.2, 0, 3), (56.6, -3.85, 0, 3), (57.3, -3.2, 0, 2), (57.3, -3.85, 0, 3), (53.6, -4.2, 0, 1),
              (49.5, -2.4, 0, 1), (56.9, -5.3, 0, 2), (49.6, 0.3, 0, 2), (50.2, 0.25, 0, 1)]
    for (x, y, z0, n) in spots:
        for z in range(n):
            sklib.instance(cs[k % 4], (x, y, z0 + z * 0.25), rng.uniform(-0.06, 0.06) + (math.pi / 2 if k % 3 == 0 else 0),
                           'I_crate_wash_%d' % k, C_WASH)
            k += 1
    # ice flakes spilled on the floor around crates and the tank
    proto = sklib.collection('ICE_FLAKE', False)
    if not proto.objects:
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.012)
        bmesh.ops.scale(bm, vec=(1.2, 1.0, 0.35), verts=bm.verts[:])
        me = bpy.data.meshes.new('ice_flake')
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new('IF0_flake', me)
        proto.objects.link(o)
        sklib.mat_to(o, sklib._ice_chunk_mat(), uv=False)
    ng = scatter_group(proto)
    items = []
    for cx, cy, r in ((56.8, -3.6, 1.0), (52.3, 0.3, 1.6), (55.0, -3.3, 0.9), (49.8, 0.0, 0.6)):
        for i in range(90):
            a, d = rng.uniform(0, 6.28), r * math.sqrt(rng.random())
            items.append((cx + math.cos(a) * d * 1.3, cy + math.sin(a) * d * 0.8, 0.004, 0, 0, rng.uniform(0, 6.28),
                          rng.uniform(0.6, 1.4), 0))
    me = bpy.data.meshes.new('ice_flakes')
    me.vertices.add(len(items))
    me.vertices.foreach_set('co', [c for it in items for c in it[:3]])
    for nm, t, key, vals in (('rot', 'FLOAT_VECTOR', 'vector', [c for it in items for c in it[3:6]]),
                             ('scl', 'FLOAT', 'value', [it[6] for it in items]), ('pid', 'INT', 'value', [0] * len(items))):
        me.attributes.new(nm, t, 'POINT').data.foreach_set(key, vals)
    o = sklib.new_obj('ice_flakes', me, C_WASH)
    o.modifiers.new('sc', 'NODES').node_group = ng
    return cs


# ============================================================================================ DOCK + TRUCK + YARD
def dock(rng):
    c = C_DOCK
    # opening frame, raised roll-up door (drum + guides), dock seal pads, leveller, bumpers
    box('dock_drum', (57.7, 0, 3.55), (0.5, 3.6, 0.5), M['galv'], c, bev=0.02)
    for s in (-1, 1):
        box('dock_guide_%d' % s, (57.85, s * 1.68, 1.6), (0.1, 0.12, 3.2), M['galv'], c, bev=0.006)
        box('dock_seal_%d' % s, (58.35, s * 1.75, 1.1), (0.4, 0.3, 2.6), M['rubber'], c, bev=0.03)
        box('dock_bumper_%d' % s, (58.12, s * 1.1, -0.25), (0.14, 0.3, 0.45), M['rubber'], c, bev=0.02)
    box('dock_seal_top', (58.35, 0, 2.95), (0.4, 3.8, 0.5), M['rubber'], c, bev=0.03)
    box('dock_leveller', (57.4, 0, -0.01), (1.2, 2.2, 0.03), M['galv'], c, bev=0.006)
    box('dock_lip', (58.15, 0, -0.03), (0.3, 2.2, 0.02), M['galv'], c, bev=0.004)
    for s in (-1, 1):       # yellow safety edges
        box('dock_edge_%d' % s, (57.4, s * 1.12, 0.002), (1.2, 0.05, 0.004), M['yellow'], c, bev=0)
    # outside: building plinth below the dock, yard slab (z -1.2), compound wall
    box('dock_plinth', (58.3, 0, -0.6), (0.6, 16.0, 1.2), M['concrete'], c, bev=0.02)
    box('yard', (110, 0, -1.25), (104, 140, 0.1), M['concrete'], c, bev=0)
    box('yard_wall', (96, 0, 0.0), (0.25, 120, 2.5), M['plaster'], c, bev=0.01)
    for i, y in enumerate(range(-50, 51, 6)):
        box('yard_pier_%d' % i, (95.8, y, 0.15), (0.45, 0.45, 2.8), M['plaster'], c, bev=0.01)
    box('yard_cabin', (90, -14, 0.25), (3.0, 3.0, 3.0), M['plaster'], c, bev=0.02)
    box('yard_cabin_roof', (90, -14, 1.85), (3.6, 3.6, 0.15), M['galv'], c, bev=0.01)
    # reefer truck body backed in toward the dock, rear doors open
    truck(c, rng)


def truck(c, rng):
    rx = 60.0                 # rear face of the body
    L, W, Hb, fz = 6.6, 2.5, 2.55, -0.02        # body floor ~ dock level
    x0, x1 = rx, rx + L

    def body(bm):
        t = 0.08
        _bm_box(bm, Vector(((x0 + x1) / 2, 0, fz - 0.06)), (L, W, 0.12))              # floor
        _bm_box(bm, Vector(((x0 + x1) / 2, 0, fz + Hb)), (L, W, t))                    # roof
        for s in (-1, 1):
            _bm_box(bm, Vector(((x0 + x1) / 2, s * (W / 2 - t / 2), fz + Hb / 2)), (L, t, Hb))
        _bm_box(bm, Vector((x1 - t / 2, 0, fz + Hb / 2)), (t, W, Hb))                  # front bulkhead
        # rear frame (posts, header, sill)
        for s in (-1, 1):
            _bm_box(bm, Vector((x0 + 0.06, s * (W / 2 - 0.06), fz + Hb / 2)), (0.12, 0.12, Hb + 0.05))
        _bm_box(bm, Vector((x0 + 0.06, 0, fz + Hb - 0.05)), (0.12, W, 0.16))
        _bm_box(bm, Vector((x0 + 0.06, 0, fz - 0.08)), (0.12, W, 0.16))
        # side ribs
        for x in [x0 + 0.5 + i * 0.6 for i in range(10)]:
            for s in (-1, 1):
                _bm_box(bm, Vector((x, s * (W / 2 + 0.01), fz + Hb / 2)), (0.05, 0.02, Hb - 0.1))
    o = mk('truck_body', body, [M['truck']], c, bev=0.01)
    box('truck_floor_plate', ((x0 + x1) / 2, 0, fz + 0.003), (L - 0.2, W - 0.18, 0.006), M['alu'], c, bev=0)
    # doors swung ~260 deg flat against the sides
    for s in (-1, 1):
        d = box('truck_door_%d' % s, (x0 + 0.62, s * (W / 2 + 0.06), fz + Hb / 2), (1.2, 0.05, Hb - 0.1), M['truck'], c, bev=0.012)
        box('truck_door_gasket_%d' % s, (x0 + 0.62, s * (W / 2 + 0.035), fz + Hb / 2), (1.16, 0.01, Hb - 0.14), M['rubber'], c, bev=0)
        for f in (0.3, 0.8):
            box('truck_bar_%d_%.1f' % (s, f), (x0 + 0.1 + 1.1 * f, s * (W / 2 + 0.1), fz + Hb / 2), (0.03, 0.03, Hb - 0.2), M['galv'], c, bev=0.004)
    # chassis, dual rear wheels, bumper (underride bar), lamps, blank plate
    box('truck_chassis', ((x0 + x1) / 2 + 0.4, 0, fz - 0.35), (L + 1.0, 0.9, 0.22), M['rubber'], c, bev=0.01)
    for wx in (x0 + 1.6, x0 + 2.75):
        for s in (-1, 1):
            w = mk('truck_wheel_%.1f_%d' % (wx, s), lambda bm: (_bm_cyl(bm, Vector((0, 0, 0)), 0.5, 0.5, 'Y', 32),),
                   [M['rubber']], c, loc=(wx, s * 0.92, -0.7), bev=0.03)
            w.data.shade_smooth()
            mk('truck_hub_%.1f_%d' % (wx, s), lambda bm: (_bm_cyl(bm, Vector((0, 0, 0)), 0.28, 0.52, 'Y', 24),),
               [M['galv']], c, loc=(wx, s * 0.92, -0.7), bev=0.01)
    box('truck_underride', (x0 + 0.15, 0, -0.75), (0.12, 2.2, 0.14), M['yellow'], c, bev=0.01)
    for s in (-1, 1):
        box('truck_lamp_%d' % s, (x0 + 0.02, s * 0.95, -0.55), (0.04, 0.22, 0.1), M['red_lens'], c, bev=0.006)
        box('truck_mudflap_%d' % s, (x0 + 0.5, s * 0.92, -0.95), (0.02, 0.5, 0.5), M['rubber'], c, bev=0.004)
    box('truck_plate_blank', (x0 + 0.02, 0, -0.45), (0.02, 0.5, 0.12), M['tray'], c, bev=0.004)
    box('truck_ground_shadow_catch', (x0 + L / 2, 0, -1.198), (L, W, 0.002), M['concrete'], c, bev=0)
    # crates of iced shrimp inside the body (being unloaded)
    cs = [bpy.data.collections.get('A-CRATE-SHRIMP_W%d' % i) for i in range(4)]
    k = 0
    for xi in range(5):
        for yi in range(3):
            n = 4 if xi > 0 else 2
            for z in range(n):
                sklib.instance(cs[k % 4], (x0 + 0.9 + xi * 0.66, (yi - 1) * 0.72, fz + z * 0.25), (k % 2) * 0.03,
                               'I_crate_truck_%d' % k, c)
                k += 1


# ============================================================================================ PEOPLE
def person(name, seed, outfit, pose, loc, rotz, lod='L0', coll=C_PEOPLE, vis=None, work_phase=None, sex=None, tone=None):
    rng = random.Random(seed)
    sex = sex or ('female' if rng.random() < 0.45 else 'male')
    r = people.make_person(name, sex=sex, age=rng.uniform(0.1, 0.6),
                           body=dict(weight=rng.uniform(0.3, 0.7), muscle=rng.uniform(0.35, 0.65), height=rng.uniform(0.3, 0.7)),
                           skin_tone=tone if tone is not None else rng.uniform(0.35, 0.9), outfit=outfit, pose=pose,
                           location=loc, rotation_z=rotz, seed=seed, lod=lod)
    for o in [r] + list(r.children):
        if outfit == 'lab_coat' and o.type == 'MESH' and o.name.split('.', 1)[-1].startswith(('short', 'braid', 'ponytail', 'bob')):
            bpy.data.objects.remove(o)
            continue
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        coll.objects.link(o)
    for o in r.children:
        for sl in getattr(o, 'material_slots', []):
            m = sl.material
            if m and any(k in m.name for k in ('coat', 'lab_coat', 'hairnet', 'apron')) and not m.get('sk_toned'):
                for n in m.node_tree.nodes:
                    if n.type == 'RGB':
                        c0 = n.outputs[0].default_value
                        n.outputs[0].default_value = (c0[0] * 0.86, c0[1] * 0.87, c0[2] * 0.88, 1)
                m['sk_toned'] = 1
    if work_phase is not None:
        people.animate_cycle(r, 'work', 1, F_END, phase=work_phase, amount=rng.uniform(0.8, 1.15))
    if vis:
        frame_vis([o for o in r.children if o.type == 'MESH'], *vis)
    return r


def pose_quats(rig, pose, rng_seed):
    people.apply_pose(rig, pose, random.Random(rng_seed))
    return {pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones}


def key_quats(rig, q, f):
    for pb in rig.pose.bones:
        pb.rotation_quaternion = q[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f)


def walk_quats(rig, base, phase):
    """carry pose + leg stride (phase 0: left fwd, 1: pass, 2: right fwd, 3: pass)."""
    for pb in rig.pose.bones:
        pb.rotation_quaternion = base[pb.name]
    st = {0: ((-20, 6), (14, 22)), 1: ((-3, 18), (2, 4)), 2: ((14, 22), (-20, 6)), 3: ((2, 4), (-3, 18))}[phase]
    for s, (th, ca) in zip(('l', 'r'), st):
        people._set_rot(rig, 'thigh_' + s, th, 0, 0)
        people._set_rot(rig, 'calf_' + s, ca, 0, 0)
        people._set_rot(rig, 'foot_' + s, -(th + ca) + (-14 if ca > 15 else 0), 0, 0)
    bpy.context.view_layer.update()
    return {pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones}


def palms(rig):
    bpy.context.view_layer.update()
    mw = rig.matrix_world
    p = {}
    for s in ('l', 'r'):
        pb = rig.pose.bones['hand_' + s]
        p[s] = mw @ ((pb.head + pb.tail) / 2 + (pb.tail - pb.head) * 1.2)
    return p


def technician(bench_y, bz):
    """P-LAB-1: lifts a sample tray at the QC shelf (f1-50), turns, walks it into the lab (f56-135), sets it on the
    balance (f135-150) and probes a shrimp under the lamp (f150-192)."""
    qc = Vector((2.6, -1.46, 0))
    door = Vector((4.2, -3.0, 0))
    bench = Vector((5.25, bench_y + 0.07 + 0.42, 0))
    rig = person('P-LAB-1', 11, 'lab_coat', 'work_table', tuple(qc), math.pi, 'L0', C_PEOPLE, vis=(1, 250), sex='male', tone=0.55)
    q_work = pose_quats(rig, 'work_table', 3)
    q_carry = pose_quats(rig, 'carry', 3)
    walk = [walk_quats(rig, q_carry, i) for i in range(4)]
    # body path (location + facing)
    def face(v):          # rot_z so that the person (faces -Y at 0) faces direction v
        return math.atan2(v.x, -v.y)
    path = [(1, qc, math.pi), (50, qc, math.pi), (58, qc + (door - qc) * 0.08, face(door - qc)),
            (96, door, face(bench - door)), (130, bench + Vector((0, 0.03, 0)), 0.0), (192, bench, 0.0)]
    for f, p, rz in path:
        rig.location = (p.x, p.y, rig.location.z)
        rig.rotation_euler = (0, 0, rz)
        rig.keyframe_insert('location', frame=f)
        rig.keyframe_insert('rotation_euler', frame=f)
    sklib.ease_keys(rig)
    # pose keys
    key_quats(rig, q_work, 1)
    key_quats(rig, q_work, 30)
    key_quats(rig, q_carry, 46)
    f, i = 58, 0
    while f < 128:
        key_quats(rig, walk[i % 4], f)
        f += 7
        i += 1
    key_quats(rig, q_carry, 132)
    key_quats(rig, q_carry, 136)
    key_quats(rig, q_work, 150)
    key_quats(rig, q_work, 192)
    # tray follows the palms' midpoint until set down on the balance
    t = tray('qc_sample_tray', C_LAB, size=(0.34, 0.24, 0.045))
    rng = random.Random(9)
    items = heap(0, 0, 0.006, 0.12, 0.07, 9, (1, 0, 0), rng, layers=1)
    tip_item = items[0]
    scatter('qc_sample_shrimp', items, C_LAB, hi=True, parent=t)
    set_f = 147
    for f in range(1, 193):
        scene.frame_set(f)
        p = palms(rig)
        mid = (p['l'] + p['r']) / 2
        if f <= set_f:
            t.location = (mid.x, mid.y, QC_Z if f <= 30 else max(QC_Z, mid.z - 0.03))
            t.rotation_euler = (0, 0, rig.rotation_euler.z)
        t.keyframe_insert('location', frame=f)
        t.keyframe_insert('rotation_euler', frame=f)
    # balance + lamp at the set-down spot; tray lands on the pan
    scene.frame_set(170)
    p = palms(rig)
    mid = (p['l'] + p['r']) / 2
    pan = balance(C_LAB, (mid.x, mid.y - 0.03, bz))
    for f in range(set_f, 193):
        t.location = (mid.x, mid.y, pan + 0.001)
        t.rotation_euler = (0, 0, 0)
        t.keyframe_insert('location', frame=f)
        t.keyframe_insert('rotation_euler', frame=f)
    lamp(C_LAB, (mid.x + 0.45, bench_y - 0.25 + 0.5, bz), (mid.x, mid.y, pan))
    # probe thermometer: lies on the bench, then in the right hand pointing into a shrimp (f150+)
    def probe_obj(nm):
        def b(bm):
            _bm_box(bm, Vector((0, 0, 0.055)), (0.035, 0.022, 0.11))
            _bm_cyl(bm, Vector((0, 0, -0.06)), 0.002, 0.12, 'Z', 8)
        o = mk(nm, b, [M['tray']], C_LAB, bev=0.004)
        mk(nm + '_screen', lambda bm: _bm_box(bm, Vector((0, -0.0115, 0.075)), (0.024, 0.002, 0.03)), [M['screen']], C_LAB, bev=0).parent = o
        return o
    pr_bench = probe_obj('probe_bench')
    pr_bench.location = (mid.x - 0.35, bench_y + 0.1, bz + 0.012)
    pr_bench.rotation_euler = (math.pi / 2, 0, 0.4)
    pr = probe_obj('probe_hand')
    tip_w = Vector((mid.x + tip_item[0], mid.y + tip_item[1], pan + 0.02))
    for f in range(1, 193):
        scene.frame_set(f)
        hr = palms(rig)['r']
        d = (hr - tip_w)
        pr.location = hr - d.normalized() * 0.02
        pr.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        pr.keyframe_insert('location', frame=f)
        pr.keyframe_insert('rotation_euler', frame=f)
    frame_vis([pr] + list(pr.children), 150, 260)
    frame_vis([pr_bench] + list(pr_bench.children), 1, 149)
    scene.frame_set(1)
    return rig


def hold_shrimp(rig, rng, sides=('r', 'l')):
    """A shrimp in each working hand (bone-parented -> follows the work cycle; hands make contact)."""
    p = palms(rig)
    for s in sides:
        o = bpy.data.objects.new(rig.name + '_held_' + s, PROTOS[rng.choice((0, 1, 2, 3))][1].data)
        C_PEOPLE.objects.link(o)
        o.parent, o.parent_type, o.parent_bone = rig, 'BONE', 'hand_' + s
        o.matrix_world = Matrix.Translation(p[s] - Vector((0, 0, 0.022))) @ \
            Euler((math.pi / 2, 0, rig.rotation_euler.z + math.pi / 2 + rng.uniform(-0.5, 0.5))).to_matrix().to_4x4()
        o['vis_of'] = rig.name


def carry_crate(rig, cc):
    """Crate held at the middle of its long walls, rim at the palms (person 'carry' pose, static)."""
    p = palms(rig)
    mid = (p['l'] + p['r']) / 2
    r = rig.rotation_euler.z
    fwd = Vector((math.sin(r), -math.cos(r), 0))
    i = sklib.instance(cc, tuple(mid + fwd * 0.06 - Vector((0, 0, 0.245))), r + math.pi / 2, 'I_crate_carry_' + rig.name, C_PEOPLE)
    return i


def staff(chutes):
    if FAST:
        return
    cs = [bpy.data.collections.get('A-CRATE-SHRIMP_%d' % i) for i in range(4)]
    ph = random.Random(2)
    # grading: 4 at the sorting table (north, facing -Y, faces >= 4 m from the camera), hopper feeder, crate hand
    vis = (150, 470)
    for i, x in enumerate((13.0, 14.6, 16.2, 17.8)):
        r = person('P-GRADE-%d' % i, 100 + i, 'ppe_plant', 'work_table', (x + ph.uniform(-0.1, 0.1), 2.5 + 0.72, 0),
                   ph.uniform(-0.1, 0.1), 'L0', vis=vis, work_phase=ph.random())
        hold_shrimp(r, ph)
    r = person('P-GRADE-4', 110, 'ppe_plant', 'carry', (22.0, 0.6, 1.1), -math.pi / 2, 'L0', vis=vis)
    vis_objs = [carry_crate(r, cs[1])]
    r = person('P-GRADE-5', 111, 'ppe_plant', 'carry', (19.8, -2.3, 0), math.pi / 2, 'L0', vis=vis)
    vis_objs.append(carry_crate(r, cs[2]))
    # peeling: 2 tables x 2 sides x 6 = 24; aisle-side rows L0, outer rows L1; every one unique, phases differ
    k = 0
    rng = random.Random(31)
    items = []
    vis = (340, 650)
    for ti, ty in enumerate((-2.4, 2.4)):
        for side in (-1, 1):
            inner = (side == -1 and ty > 0) or (side == 1 and ty < 0)
            for j in range(6):
                x = 27.2 + j * 2.2 + rng.uniform(-0.2, 0.2) + (0.5 if side > 0 else 0)
                py = ty + side * 0.72
                rz = (0.0 if side > 0 else math.pi) + rng.uniform(-0.1, 0.1)
                r = person('P-PEEL-%02d' % k, 200 + k, 'ppe_plant', 'work_table', (x, py, 0), rz, 'L0' if inner else 'L1',
                           vis=vis, work_phase=rng.random())
                hold_shrimp(r, rng)
                items += worker_trays(rng, x, ty, side, 0.86, k)
                k += 1
    scatter('peel_tray_shrimp', items, C_PEEL)
    # receiving: crate tipper (north of the tank), basket hand (west end), crate stacker by the dock
    vis = (540, 765)
    person('P-WASH-0', 300, 'ppe_plant', 'carry', (52.1, 2.62, 0), 0.0, 'L0', vis=vis)
    r = person('P-WASH-1', 301, 'ppe_plant', 'work_table', (50.0, 1.5, 0), math.pi / 2, 'L0', vis=vis, work_phase=0.4)
    r = person('P-WASH-2', 302, 'ppe_plant', 'carry', (56.6, -4.62, 0), math.pi, 'L0', vis=vis)
    vis_objs.append(carry_crate(r, bpy.data.collections.get('A-CRATE-SHRIMP_W2')))
    for o in C_PEOPLE.objects:
        if 'vis_of' in o:
            rig = bpy.data.objects[o['vis_of']]
            frame_vis([o], *((150, 470) if 'GRADE' in rig.name else (340, 650)))


def tipping_crate(tank):
    """Crate held by P-WASH-0 tilting over the tank, shrimp sliding out into the water (loop)."""
    rig = bpy.data.objects.get('P-WASH-0')
    rng = random.Random(55)
    cc = bpy.data.collections.get('A-CRATE-SHRIMP_W1')
    pivot = sklib.new_obj('tip_pivot', None, C_WASH)
    if rig:
        p = palms(rig)
        mid = (p['l'] + p['r']) / 2
    else:
        mid = Vector((52.1, 2.23, 0.98))
    pivot.location = mid
    for f, a in ((540, 0.45), (640, 0.75), (700, 0.62), (765, 0.8)):
        pivot.rotation_euler = (a, 0, 0)
        pivot.keyframe_insert('rotation_euler', frame=f)
    sklib.ease_keys(pivot)
    i = sklib.instance(cc, (0, -0.3 + 0.02, -0.25), 0.0, 'I_crate_tipping', C_WASH)
    i.rotation_euler.z = math.pi / 2
    i.parent = pivot
    # falling shrimp from the crate lip into the water
    tx0, tx1, ty0, ty1, th, wz = tank
    for j in range(6):
        o = bpy.data.objects.new('tip_fall_%d' % j, PROTOS[rng.randrange(2)][0].data)
        C_WASH.objects.link(o)
        per = 18
        x0 = mid.x + rng.uniform(-0.15, 0.15)
        for t in range(0, per + 1, 2):
            u = t / per
            o.location = (x0, mid.y - 0.55 - 0.15 * u, mid.z - 0.2 - (mid.z - 0.2 - wz) * u * u)
            o.rotation_euler = (1.4 + u * 2.0, 0.2, rng.uniform(-0.4, 0.4))
            o.keyframe_insert('location', frame=1 + j * 3 + t)
            o.keyframe_insert('rotation_euler', frame=1 + j * 3 + t)
        for fc in sklib._fcurves(o):
            fc.modifiers.new('CYCLES')
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
        frame_vis([o], 540, 765)


# ============================================================================================ CAMERA
def cam_path():
    cam = sklib.camera('CAM', 35.0, (0, 0, 1.9), (0, 0, 0))
    # (frame, location, look-at or Euler, lens, f-stop)
    keys = [
        (1, (0.0, 0.0, 1.90), Euler((0, 0, -math.pi / 2)), 35),                    # BRIDGE_BELT: top-down 1.0 m over the belt
        (22, (0.25, 0.25, 2.05), (0.8, -0.35, 0.9), 35),
        (55, (1.05, 1.15, 1.85), (2.65, -1.05, 1.0), 32),                           # QC station: tech lifts the sample tray
        (100, (2.9, -0.9, 1.92), (4.4, -3.6, 1.0), 30),                             # following the tray to the lab door
        (150, (4.3, -2.8, 1.8), (5.25, -4.95, 0.98), 30),                           # through the door
        (172, (6.25, -3.5, 1.7), (5.2, -5.05, 0.98), 32),
        (192, (6.4, -3.6, 1.68), (5.25, -5.05, 0.98), 32),                          # bench: balance, probe, lamp
        (240, (9.55, -4.2, 1.8), (13.5, -0.9, 1.0), 28),                            # out of the lab into grading
        (300, (13.4, -3.15, 1.75), (17.0, -0.2, 1.05), 28),                         # along the chutes/crates
        (383, (16.0, -2.9, 5.3), (21.0, 0.6, 0.6), 24),                             # overhead reveal
        (440, (24.6, 0.0, 1.55), (31.0, 0.0, 1.2), 28),                             # peeling hall aisle, shoulder height
        (520, (30.2, 0.0, 1.55), (37.0, 0.0, 1.1), 28),
        (574, (32.0, -0.4, 5.0), (40.0, 0.0, 0.8), 24),                             # high wide of the hall
        (625, (45.2, -1.4, 2.3), (51.8, 1.3, 0.7), 26),                             # receiving: the wash tank
        (700, (51.4, -1.5, 1.75), (57.0, 0.4, 1.3), 28),
        (765, (55.0, 0.0, 1.50), (61.0, 0.0, 1.50), 28),                            # BRIDGE_DOCK
    ]
    prev = None
    for f, loc, aim, lens in keys:
        loc = Vector(loc)
        if isinstance(aim, Euler):
            e = aim.copy()
            dist = 1.0
        else:
            d = Vector(aim) - loc
            e = d.to_track_quat('-Z', 'Y').to_euler()
            dist = d.length
        if prev is not None:
            e.make_compatible(prev)
        prev = e
        cam.location = loc
        cam.rotation_euler = e
        cam.data.lens = lens
        cam.data.dof.focus_distance = dist
        cam.keyframe_insert('location', frame=f)
        cam.keyframe_insert('rotation_euler', frame=f)
        cam.data.keyframe_insert('lens', frame=f)
        cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    sklib.ease_keys(cam, cam.data)
    # exposure: 0 inside, -0.3 at the dock bridge (daylight exposure-matched)
    vs = scene.view_settings
    for f, ev in ((1, 0.0), (690, 0.0), (765, -0.3)):
        vs.exposure = ev
        vs.keyframe_insert('exposure', frame=f)
    sklib.ease_keys(scene)
    return cam



def world_ground():
    """The physical sky is black below the horizon -> metal facing down reflected black. Below-horizon = warm grey ground."""
    w = scene.world
    nt = w.node_tree
    sky = [n for n in nt.nodes if n.type == 'TEX_SKY'][0]
    bg = [n for n in nt.nodes if n.type == 'BACKGROUND'][0]
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange')
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = -0.04, 0.02
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    nt.links.new(mr.outputs[0], mix.inputs['Factor'])
    mix.inputs['A'].default_value = (1.6, 1.5, 1.35, 1)
    nt.links.new(sky.outputs[0], mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], bg.inputs['Color'])


def probes():
    """Sphere reflection probes per zone (captured at render) so stainless reflects the white hall, not the sky."""
    for nm, loc, r in (('PR_belt', (1, 0, 2.2), 7), ('PR_lab', (5.7, -4.2, 1.6), 3.5), ('PR_grade', (16, 0, 2.5), 8),
                       ('PR_peel', (33, 0, 2.5), 9), ('PR_wash', (51, 0, 2.2), 8)):
        P = bpy.data.lightprobes.new(nm, 'SPHERE')
        P.influence_distance = r
        P.falloff = 0.3
        sklib.new_obj(nm, P, C_LIGHT, loc=loc)
    e = scene.eevee
    e.shadow_pool_size = '1024'
    e.shadow_resolution_scale = 0.5
    for o in C_LIGHT.objects:
        if o.type == 'LIGHT' and o.name.startswith('L_hall'):
            o.data.shadow_maximum_resolution = 0.02
            o.data.use_shadow_jitter = False
            o.data.use_shadow = o.location.y < 0      # half the battens cast shadows (budget)


# ============================================================================================ BUILD
sklib.sky_world(sun_elev_deg=20, sun_az_deg=100)
world_ground()
shell()
lights()
probes()
belt()
bench_y, bz = lab()
chutes, rng_g = grader()
grade_crates(chutes, rng_g)
sorting_table(random.Random(12))
peel_tables(random.Random(13))
tank, scale_xy = wash(random.Random(14))
wash_crates(random.Random(15), scale_xy)
dock(random.Random(16))
if not FAST:
    technician(bench_y, bz)
staff(chutes)
tipping_crate(tank)
cam = cam_path()
scene.frame_set(1)
path = sklib.finish('plant-line', 'int')
for f in STILLS:
    sklib.render_still(STILL_DIR + 'pl_%s_f%03d.png' % (TAG, f), f, (960, 540))
