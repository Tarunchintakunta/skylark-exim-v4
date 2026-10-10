"""Skylark Exim v4 -- believable, varied MPFB2 people for headless scene scripts.

    import sys; sys.path.insert(0, '<REPO>/assets-src/blender/lib'); import people
    p = people.make_person('w1', sex='male', age=0.4, outfit='ppe_plant', pose='work_table',
                           location=(0, 0, 0), rotation_z=0, seed=7)
    people.animate_cycle(p, 'work', 1, 240, phase=0.3)

Bodies, faces, skin, eyes, eyebrows, eyelashes, hair and the base clothes come from MPFB2 + the
MakeHuman CC0 system assets (installed in MPFB's user data dir). Items the pack lacks (coats, apron,
hairnet, mask, gloves, gumboots, lungi, hi-vis vest, helmet, thermal suit, sweater, towel, lanyard)
are modelled here as separate meshes derived from the person's own body surface (same topology ->
same skin weights -> they deform with the rig and never clip), smoothed so they do not read as
skin-tight, pushed out to a minimum gap over the body/underlayers, with displacement + shader folds.
Body skin hidden under opaque garments is masked out (vertex group 'sk_hide').

Conventions: person faces -Y at rotation_z=0; metres; feet (or shoes) touch z=0 at `location`.
"""
import math
import random
import zlib

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

if 'bl_ext.blender_org.mpfb' not in bpy.context.preferences.addons:  # e.g. --factory-startup
    bpy.ops.preferences.addon_enable(module='bl_ext.blender_org.mpfb')
from bl_ext.blender_org.mpfb.services.humanservice import HumanService  # noqa: E402

OUTFITS = ['ppe_plant', 'thermal_suit', 'hivis_helmet', 'formal_shirt_lanyard', 'tshirt_lungi',
           'tshirt_shorts', 'oilskins', 'cotton_shirt_lungi_towel', 'diner_shirt', 'diner_sweater',
           'lab_coat']
POSES = ['stand', 'walk', 'work_table', 'carry', 'pull_rope', 'wave', 'sit', 'crouch']

HAND = {'hand', 'index', 'middle', 'ring', 'pinky', 'thumb'}


def _h(text):
    """Stable string hash (Python's hash() is salted per process -> seeds would not reproduce)."""
    return zlib.crc32(text.encode())


def _part(bone):
    """'upperarm_l' -> 'upperarm'; 'index_02_r' -> 'hand'; 'spine_02' -> 'spine'."""
    b = bone.rsplit('_', 1)[0] if bone[-2:] in ('_l', '_r') else bone
    b = b.split('_')[0]
    return 'hand' if b in HAND else b


# ----------------------------------------------------------------------------------------------
# materials
# ----------------------------------------------------------------------------------------------

def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return nt, nt.nodes, nt.links


def fabric(name, color, rough=0.8, sheen=0.4, pattern='plain', color2=None, scale=1.0,
           fold=0.35, gloss=False, band=None, check=4.5, seam=False):
    """Procedural cloth on the 'rest' attribute (rest-pose position, so it sticks while posed).
    pattern: plain | knit | quilt | plaid | stripes | bands | net
    band=(z0, period, width) in rest metres for 'bands' (hi-vis tape, mundu border)."""
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    out = N.new('ShaderNodeOutputMaterial')
    bs = N.new('ShaderNodeBsdfPrincipled')
    L.new(bs.outputs[0], out.inputs['Surface'])
    bs.inputs['Roughness'].default_value = rough
    if 'Sheen Weight' in bs.inputs:
        bs.inputs['Sheen Weight'].default_value = sheen
    if gloss:
        bs.inputs['Coat Weight'].default_value = 0.4
        bs.inputs['Coat Roughness'].default_value = 0.25
    at = N.new('ShaderNodeAttribute'); at.attribute_name = 'rest'
    co = at.outputs['Vector']
    # large soft folds + fine weave
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9 * scale
    nz.inputs['Detail'].default_value = 3
    L.new(co, nz.inputs['Vector'])
    # vertical drape creases (stretched noise)
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (28 * scale, 28 * scale, 3 * scale)
    L.new(co, mp.inputs['Vector'])
    nz2 = N.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 1.0
    nz2.inputs['Detail'].default_value = 2
    L.new(mp.outputs[0], nz2.inputs['Vector'])
    weave = N.new('ShaderNodeTexNoise'); weave.inputs['Scale'].default_value = 900 * scale
    L.new(co, weave.inputs['Vector'])
    h = N.new('ShaderNodeMath'); h.operation = 'ADD'
    L.new(nz.outputs['Fac'], h.inputs[0]); L.new(nz2.outputs['Fac'], h.inputs[1])
    h2 = N.new('ShaderNodeMath'); h2.operation = 'MULTIPLY_ADD'
    L.new(weave.outputs['Fac'], h2.inputs[0]); h2.inputs[1].default_value = 0.08
    L.new(h.outputs[0], h2.inputs[2])
    height = h2.outputs[0]
    col = N.new('ShaderNodeRGB'); col.outputs[0].default_value = (*color, 1)
    base = col.outputs[0]
    if pattern in ('knit', 'quilt', 'net', 'stripes', 'plaid', 'bands'):
        sep = N.new('ShaderNodeSeparateXYZ'); L.new(co, sep.inputs[0])
    if pattern == 'knit':  # vertical ribs
        w = N.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'; w.bands_direction = 'X'
        w.inputs['Scale'].default_value = 60; L.new(co, w.inputs['Vector'])
        m = N.new('ShaderNodeMath'); m.operation = 'MULTIPLY_ADD'
        L.new(w.outputs['Fac'], m.inputs[0]); m.inputs[1].default_value = 0.5; L.new(height, m.inputs[2])
        height = m.outputs[0]
    if pattern == 'quilt':  # horizontal padded channels
        w = N.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'; w.bands_direction = 'Z'
        w.inputs['Scale'].default_value = 9; w.wave_profile = 'SIN'; L.new(co, w.inputs['Vector'])
        m = N.new('ShaderNodeMath'); m.operation = 'MULTIPLY_ADD'
        L.new(w.outputs['Fac'], m.inputs[0]); m.inputs[1].default_value = 0.35; L.new(height, m.inputs[2])
        height = m.outputs[0]
    if pattern == 'net':
        v = N.new('ShaderNodeTexVoronoi'); v.feature = 'DISTANCE_TO_EDGE'
        v.inputs['Scale'].default_value = 260; L.new(co, v.inputs['Vector'])
        m = N.new('ShaderNodeMath'); m.operation = 'MULTIPLY_ADD'
        L.new(v.outputs['Distance'], m.inputs[0]); m.inputs[1].default_value = 3.0; L.new(height, m.inputs[2])
        height = m.outputs[0]
    if pattern in ('stripes', 'plaid', 'bands') and color2 is not None:
        c2 = N.new('ShaderNodeRGB'); c2.outputs[0].default_value = (*color2, 1)
        mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'
        if pattern == 'bands':  # horizontal bands on rest z (hi-vis tape, mundu border)
            sub = N.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
            L.new(sep.outputs['Z'], sub.inputs[0]); sub.inputs[1].default_value = band[0]
            md = N.new('ShaderNodeMath'); md.operation = 'FLOORED_MODULO'
            L.new(sub.outputs[0], md.inputs[0]); md.inputs[1].default_value = band[1]
            lt = N.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
            L.new(md.outputs[0], lt.inputs[0]); lt.inputs[1].default_value = band[2]
            fac = lt.outputs[0]
        else:
            w = N.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'
            w.bands_direction = 'Z' if pattern == 'stripes' else 'X'
            w.wave_profile = 'SAW'; w.inputs['Scale'].default_value = check
            L.new(co, w.inputs['Vector'])
            gt = N.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'
            L.new(w.outputs['Fac'], gt.inputs[0]); gt.inputs[1].default_value = 0.72 if pattern == 'stripes' else 0.86
            fac = gt.outputs[0]
            if pattern == 'plaid':
                w2 = N.new('ShaderNodeTexWave'); w2.wave_type = 'BANDS'; w2.bands_direction = 'Z'
                w2.wave_profile = 'SAW'; w2.inputs['Scale'].default_value = check
                L.new(co, w2.inputs['Vector'])
                g2 = N.new('ShaderNodeMath'); g2.operation = 'GREATER_THAN'
                L.new(w2.outputs['Fac'], g2.inputs[0]); g2.inputs[1].default_value = 0.86
                mx = N.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
                L.new(fac, mx.inputs[0]); L.new(g2.outputs[0], mx.inputs[1])
                fac = mx.outputs[0]
        L.new(fac, mix.inputs['Factor'])
        L.new(base, mix.inputs['A']); L.new(c2.outputs[0], mix.inputs['B'])
        base = mix.outputs['Result']
        if pattern == 'bands' and band[1] < 1:  # retro-reflective tape is smoother
            r = N.new('ShaderNodeMath'); r.operation = 'MULTIPLY_ADD'
            L.new(fac, r.inputs[0]); r.inputs[1].default_value = -0.45; r.inputs[2].default_value = rough
            L.new(r.outputs[0], bs.inputs['Roughness'])
    if seam:  # front placket line (coats): darker crease at x~0 on the front
        sp = N.new('ShaderNodeSeparateXYZ'); L.new(co, sp.inputs[0])
        ax = N.new('ShaderNodeMath'); ax.operation = 'ABSOLUTE'; L.new(sp.outputs['X'], ax.inputs[0])
        lt = N.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; L.new(ax.outputs[0], lt.inputs[0])
        lt.inputs[1].default_value = 0.004
        fr = N.new('ShaderNodeMath'); fr.operation = 'LESS_THAN'; L.new(sp.outputs['Y'], fr.inputs[0])
        fr.inputs[1].default_value = -0.03
        both = N.new('ShaderNodeMath'); both.operation = 'MULTIPLY'
        L.new(lt.outputs[0], both.inputs[0]); L.new(fr.outputs[0], both.inputs[1])
        dm = N.new('ShaderNodeMix'); dm.data_type = 'RGBA'
        L.new(both.outputs[0], dm.inputs['Factor']); L.new(base, dm.inputs['A'])
        dm.inputs['B'].default_value = (color[0] * 0.55, color[1] * 0.55, color[2] * 0.55, 1)
        base = dm.outputs['Result']
        h3 = N.new('ShaderNodeMath'); h3.operation = 'MULTIPLY_ADD'
        L.new(both.outputs[0], h3.inputs[0]); h3.inputs[1].default_value = -0.6; L.new(height, h3.inputs[2])
        height = h3.outputs[0]
    # subtle value variation from the folds (occlusion-ish)
    dk = N.new('ShaderNodeMapRange'); L.new(nz.outputs['Fac'], dk.inputs['Value'])
    dk.inputs['To Min'].default_value = 0.82; dk.inputs['To Max'].default_value = 1.05
    mul = N.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    L.new(base, mul.inputs['A']); L.new(dk.outputs['Result'], mul.inputs['B'])
    L.new(mul.outputs['Result'], bs.inputs['Base Color'])
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = fold
    bump.inputs['Distance'].default_value = 0.01
    L.new(height, bump.inputs['Height']); L.new(bump.outputs[0], bs.inputs['Normal'])
    return mat


def _mpfb_mat(obj):
    if not obj.material_slots or not obj.material_slots[0].material:
        return None
    m = obj.material_slots[0].material.copy()
    obj.material_slots[0].material = m
    return m


def tint_mpfb(obj, color, mode='MULTIPLY', fac=1.0, plain=False, rough=None):
    """Recolour an MPFB MAKESKIN material. plain=True drops the diffuse texture (kills printed
    logos) and keeps the asset's AO + normal maps, so the fabric folds stay."""
    m = _mpfb_mat(obj)
    if m is None:
        return
    nt = m.node_tree
    di = nt.nodes.get('diffuseIntensity')
    if di is None:
        return
    if plain:
        for l in list(di.inputs['Color2'].links):
            nt.links.remove(l)
        di.blend_type = 'MIX'
        di.inputs['Fac'].default_value = 1.0
        di.inputs['Color2'].default_value = (*color, 1)
    else:
        di.blend_type = mode
        di.inputs['Fac'].default_value = fac
        di.inputs['Color1'].default_value = (*color, 1)
        # MixRGB: Color1 is A, texture is B -> swap so result = tex (op) color
        tex = di.inputs['Color2'].links[0].from_socket if di.inputs['Color2'].links else None
        if tex is not None:
            nt.links.new(tex, di.inputs['Color1'])
            for l in list(di.inputs['Color2'].links):
                nt.links.remove(l)
            di.inputs['Color2'].default_value = (*color, 1)
    if rough is not None:
        bs = next((n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
        if bs:
            bs.inputs['Roughness'].default_value = rough
            if rough < 0.4:
                bs.inputs['Coat Weight'].default_value = 0.5


def _skin(body, tone, rng):
    """tone 0 (light wheat-brown) .. 1 (deep brown). Shifts the MPFB enhanced skin group."""
    mat = body.material_slots[0].material
    g = next(n for n in mat.node_tree.nodes if n.bl_idname == 'ShaderNodeGroup')
    light = Vector((0.62, 0.40, 0.27)); dark = Vector((0.20, 0.11, 0.065))
    c = light.lerp(dark, tone)
    c = Vector([max(0, x * (1 + rng.uniform(-0.05, 0.05))) for x in c])
    g.inputs['colorMixIn'].default_value = (*c, 1)
    g.inputs['colorMixInStrength'].default_value = 0.5 - 0.25 * tone
    g.inputs['Roughness'].default_value = rng.uniform(0.42, 0.52)
    g.inputs['SSS strength'].default_value = 0.12


# ----------------------------------------------------------------------------------------------
# person context (rest-pose body data)
# ----------------------------------------------------------------------------------------------

class _Ctx:
    def __init__(self, rig, body):
        self.rig, self.body = rig, body
        mods = [(m, m.show_viewport) for m in body.modifiers]
        for m, _ in mods:
            m.show_viewport = False
        dg = bpy.context.evaluated_depsgraph_get()
        ev = body.evaluated_get(dg)
        me = ev.to_mesh()
        self.co = [v.co.copy() for v in me.vertices]
        self.no = [v.normal.copy() for v in me.vertices]
        ev.to_mesh_clear()
        for m, s in mods:
            m.show_viewport = s
        names = {g.index: g.name for g in body.vertex_groups}
        bones = set(rig.data.bones.keys())
        self.bones = bones
        n = len(self.co)
        self.w = [dict() for _ in range(n)]
        self.inbody = [False] * n
        self.groups = {}
        for v in body.data.vertices:
            for ge in v.groups:
                nm = names[ge.group]
                if nm in bones:
                    self.w[v.index][nm] = ge.weight
                elif nm == 'body':
                    self.inbody[v.index] = True
                self.groups.setdefault(nm, []).append(v.index)
        self.dom = [max(d, key=d.get) if d else '' for d in self.w]
        self.part = [_part(b) if b else '' for b in self.dom]
        self.side = [b[-1] if b.endswith(('_l', '_r')) else 'c' for b in self.dom]
        # landmarks from MPFB joint helper cubes
        self.lm = {}
        for g, idx in self.groups.items():
            if g.startswith('joint-'):
                self.lm[g[6:]] = sum((self.co[i] for i in idx), Vector()) / len(idx)
        self.under = []      # objects garments must clear (MPFB clothes in rest)
        self.garments = []   # opaque garments used to hide body skin
        tris = [p.vertices[:] for p in body.data.polygons if all(self.inbody[i] for i in p.vertices)]
        self.bvh_body = BVHTree.FromPolygons(self.co, tris)

    def bvh_under(self):
        trees = [self.bvh_body]
        for o in self.under:
            trees.append(BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices],
                                              [p.vertices[:] for p in o.data.polygons]))
        return trees


def _push_out(trees, co, gap):
    """Move co outward so it is at least `gap` above the nearest underlying surface."""
    best = None
    for t in trees:
        hit = t.find_nearest(co, 0.12)
        if hit[0] is not None and (best is None or hit[3] < best[3]):
            best = hit
    if best is None:
        return co
    loc, nrm, _, _ = best
    d = (co - loc).dot(nrm)
    if d < gap:
        return co + nrm * (gap - d)
    return co


def _finish_garment(P, obj, mat, solid=0.003, disp=0.004, disp_size=0.06, opaque=True):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    a = obj.data.attributes.get('rest') or obj.data.attributes.new('rest', 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', [c for v in obj.data.vertices for c in v.co])
    if disp > 0:
        tn = 'sk_cloth_folds_%d' % round(disp_size * 1000)
        tex = bpy.data.textures.get(tn) or bpy.data.textures.new(tn, 'CLOUDS')
        tex.noise_scale = disp_size
        d = obj.modifiers.new('folds', 'DISPLACE')
        d.texture = tex; d.texture_coords = 'LOCAL'; d.strength = disp; d.mid_level = 0.3
    if solid > 0:
        s = obj.modifiers.new('thick', 'SOLIDIFY'); s.thickness = solid; s.offset = 1.0
    am = obj.modifiers.new('Armature', 'ARMATURE'); am.object = P.rig
    obj.parent = P.rig
    if opaque:
        P.garments.append(obj)
    return obj


def _new_obj(P, name, me):
    obj = bpy.data.objects.new(name, me)
    for c in P.rig.users_collection:
        c.objects.link(obj)
    return obj


def shell(P, name, keep, offset, mat, smooth=6, gap=None, hang=None, solid=0.003, disp=0.004,
          opaque=True, post=None):
    """Garment from a region of the body surface (keeps body skin weights)."""
    me = P.body.data.copy()
    obj = _new_obj(P, P.rig.name + '.' + name, me)
    for g in P.body.vertex_groups:
        obj.vertex_groups.new(name=g.name)
    if me.shape_keys:
        obj.shape_key_clear()
    for i, v in enumerate(me.vertices):
        v.co = P.co[i]
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    kill = [v for v in bm.verts if not (P.inbody[v.index] and keep(v.index))]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    # drop slivers: faces whose verts all have <2 neighbours etc. -> remove loose verts
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * offset
    for _ in range(smooth):
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5, use_axis_x=True, use_axis_y=True,
                              use_axis_z=True)
    if hang:
        hang(bm)
    trees = P.bvh_under()
    g = offset if gap is None else gap
    for v in bm.verts:
        v.co = _push_out(trees, v.co, g)
    if post:
        post(bm)
    bm.to_mesh(me); bm.free()
    # drop vertex groups that are not bones (keeps file small)
    for vg in list(obj.vertex_groups):
        if vg.name not in P.bones:
            obj.vertex_groups.remove(vg)
    return _finish_garment(P, obj, mat, solid=solid, disp=disp, opaque=opaque)


def _weights_from_body(P, obj, pelvis_mix=0.0, k=10, parts=None):
    """Blend skin weights from the k nearest body verts (optionally restricted to body parts)."""
    kd_idx = [i for i in range(len(P.co)) if P.inbody[i] and P.dom[i]
              and (parts is None or P.part[i] in parts)]
    kd = KDTree(len(kd_idx))
    for j, i in enumerate(kd_idx):
        kd.insert(P.co[i], j)
    kd.balance()
    groups = {}
    for v in obj.data.vertices:
        acc = {}
        tot = 0
        for co, j, d in kd.find_n(v.co, k):
            wt = 1.0 / (d + 0.01)
            tot += wt
            for b, x in P.w[kd_idx[j]].items():
                acc[b] = acc.get(b, 0) + x * wt
        s = sum(acc.values()) or 1
        acc = {b: (1 - pelvis_mix) * x / s for b, x in acc.items()}
        if pelvis_mix:
            acc['pelvis'] = acc.get('pelvis', 0) + pelvis_mix
        for b, x in acc.items():
            if x > 0.01:
                if b not in groups:
                    groups[b] = obj.vertex_groups.new(name=b)
                groups[b].add([v.index], x, 'REPLACE')


def tube(P, name, z_top, z_bot, mat, margin=0.02, flare=0.06, folds=0.06, nfold=13, arc=None,
         pelvis_mix=0.45, solid=0.003, waist_margin=None, ring_step=0.03, M=56):
    """Hanging skirt-like tube (lungi, coat skirt, apron) lofted around the hips/legs."""
    pts = [P.co[i] for i in range(len(P.co))
           if P.inbody[i] and P.part[i] in ('pelvis', 'spine', 'thigh', 'calf', 'foot', 'ball')]
    top_pts = [p for p in pts if abs(p.z - z_top) < 0.03]
    cx = 0.0
    cy = sum(p.y for p in top_pts) / max(1, len(top_pts))
    nlev = max(2, int((z_top - z_bot) / ring_step) + 1)
    lev = [z_top - (z_top - z_bot) * k / (nlev - 1) for k in range(nlev)]
    prof_prev = None
    rings = []
    rr = random.Random(_h(name))
    ph = [rr.uniform(0, 6.28) for _ in range(3)]
    for k, h in enumerate(lev):
        sl = [p for p in pts if abs(p.z - h) < 0.025]
        prof = [0.0] * M
        for p in sl:
            a = math.atan2(p.y - cy, p.x - cx)
            b = int((a + math.pi) / (2 * math.pi) * M) % M
            prof[b] = max(prof[b], math.hypot(p.x - cx, p.y - cy))
        # fill gaps + circular smoothing
        for _ in range(M):
            if all(prof):
                break
            prof = [x if x else max(prof[(j - 1) % M], prof[(j + 1) % M]) for j, x in enumerate(prof)]
        for _ in range(4):
            prof = [(prof[(j - 1) % M] + 2 * prof[j] + prof[(j + 1) % M]) / 4 for j in range(M)]
        if prof_prev:
            prof = [max(a, b * 0.985) for a, b in zip(prof, prof_prev)]
        prof_prev = prof
        t = k / (nlev - 1)
        m = (waist_margin if waist_margin is not None else margin) * (1 - t) + margin * t
        ring = []
        for j in range(M):
            a = -math.pi + (j + 0.5) * 2 * math.pi / M
            r = prof[j] + m + flare * t
            r *= 1 + folds * t * (0.5 + 0.5 * math.sin(nfold * a + ph[0] + 2 * math.sin(2 * a + ph[1])))
            ring.append(Vector((cx + r * math.cos(a), cy + r * math.sin(a), h)))
        rings.append(ring)
    js = list(range(M))
    closed = arc is None
    if arc is not None:  # front arc only (front = -Y = angle -90deg)
        js = [j for j in range(M) if abs((-math.pi + (j + 0.5) * 2 * math.pi / M) + math.pi / 2) <= arc]
    verts = [rings[k][j] for k in range(nlev) for j in js]
    nj = len(js)
    faces = []
    for k in range(nlev - 1):
        for q in range(nj if closed else nj - 1):
            a, b = k * nj + q, k * nj + (q + 1) % nj
            faces.append((a, b, b + nj, a + nj))
    me = bpy.data.meshes.new(P.rig.name + '.' + name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = _new_obj(P, P.rig.name + '.' + name, me)
    trees = P.bvh_under()
    for v in me.vertices:
        v.co = _push_out(trees, v.co, margin * 0.6)
    _weights_from_body(P, obj, pelvis_mix=pelvis_mix,
                       parts={'pelvis', 'spine', 'thigh', 'calf', 'foot', 'ball'})
    return _finish_garment(P, obj, mat, solid=solid, disp=0.006, disp_size=0.08)


def _ribbon(P, name, pts, width, thick, mat, normal_hint=None):
    """Flat strap through points (lanyard)."""
    verts, faces = [], []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, -1, 0))).normalized()
        if abs(d.z) > 0.9:
            side = Vector((1, 0, 0))
        verts += [p - side * width / 2, p + side * width / 2]
        if i:
            faces.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    obj = _new_obj(P, P.rig.name + '.' + name, me)
    _weights_from_body(P, obj, k=6, parts={'spine', 'neck', 'clavicle'})
    return _finish_garment(P, obj, mat, solid=thick, disp=0, opaque=False)


def helmet(P, mat):
    sc = [P.co[i] for i in P.groups.get('scalp', []) ]
    hd = [P.co[i] for i in range(len(P.co)) if P.inbody[i] and P.dom[i] == 'head']
    zmax = max(p.z for p in hd)
    xs = [p.x for p in hd if p.z > zmax - 0.1]; ys = [p.y for p in hd if p.z > zmax - 0.1]
    c = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, zmax - 0.085))
    rx, ry = (max(xs) - min(xs)) / 2 + 0.03, (max(ys) - min(ys)) / 2 + 0.035
    rz = 0.085 + 0.035
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=1.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.02], context='VERTS')
    for v in bm.verts:
        v.co = Vector((c.x + v.co.x * rx, c.y + v.co.y * ry, c.z + v.co.z * rz))
    # brim: extrude bottom boundary outward, longer at the front (-Y)
    edges = [e for e in bm.edges if e.is_boundary]
    res = bmesh.ops.extrude_edge_only(bm, edges=edges)
    for v in [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]:
        d = Vector((v.co.x - c.x, v.co.y - c.y, 0))
        fr = max(0.0, -d.normalized().y)
        v.co += d.normalized() * (0.012 + 0.045 * fr ** 2)
        v.co.z -= 0.006
    # crown ridge
    for v in bm.verts:
        if abs(v.co.x - c.x) < 0.012 and v.co.z > c.z + 0.02:
            v.co.z += 0.006
    me = bpy.data.meshes.new('helmet'); bm.to_mesh(me); bm.free()
    obj = _new_obj(P, P.rig.name + '.helmet', me)
    obj.vertex_groups.new(name='head').add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    return _finish_garment(P, obj, mat, solid=0.004, disp=0)


# ----------------------------------------------------------------------------------------------
# outfits
# ----------------------------------------------------------------------------------------------

def _islands(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop(); isl.append(x.index)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index); stack.append(o)
        out.append(isl)
    bm.free()
    return out


def _delete_verts(obj, idx):
    idx = set(idx)
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index in idx], context='VERTS')
    bm.to_mesh(obj.data); bm.free()


def split_clothes(obj, z_cut, P=None, waist=None):
    """Split an MPFB 'suit' (shirt + trousers in one mesh) into (upper, lower) objects. Separate
    islands split by height; a connected (tucked-in) island splits per vertex by nearest body part."""
    lower = set()
    kd = None
    for isl in _islands(obj):
        zs = [obj.data.vertices[i].co.z for i in isl]
        if min(zs) >= z_cut:
            continue
        if P is None or max(zs) < waist + 0.06:
            lower.update(isl)
            continue
        if kd is None:
            idx = [i for i in range(len(P.co)) if P.inbody[i]]
            kd = KDTree(len(idx))
            for j, i in enumerate(idx):
                kd.insert(P.co[i], i)
            kd.balance()
        for i in isl:
            co = obj.data.vertices[i].co
            pt = P.part[kd.find(co)[1]]
            if pt in ('thigh', 'calf', 'foot', 'ball') or (pt == 'pelvis' and co.z < waist):
                lower.add(i)
    up = obj
    lo = obj.copy(); lo.data = obj.data.copy()
    for c in obj.users_collection:
        c.objects.link(lo)
    lo.name = obj.name + '.lower'
    _delete_verts(up, lower)
    _delete_verts(lo, set(range(len(lo.data.vertices))) - lower)
    for o in (up, lo):
        if o.material_slots:
            o.material_slots[0].material = o.material_slots[0].material.copy()
    if not lo.data.vertices:
        bpy.data.objects.remove(lo)
        lo = None
    if not up.data.vertices:
        bpy.data.objects.remove(up)
        up = None
    return up, lo


_TEE = [(0.85, 0.85, 0.82), (0.45, 0.08, 0.08), (0.12, 0.25, 0.18), (0.35, 0.36, 0.38),
        (0.1, 0.16, 0.32), (0.55, 0.42, 0.22), (0.62, 0.62, 0.6)]
_LUNGI = [((0.08, 0.14, 0.32), (0.55, 0.55, 0.6)), ((0.32, 0.06, 0.05), (0.1, 0.1, 0.12)),
          ((0.1, 0.28, 0.18), (0.75, 0.72, 0.6)), ((0.18, 0.2, 0.42), (0.04, 0.05, 0.1))]
_MUNDU = (0.82, 0.78, 0.66)


def _outfit(P, outfit, clothes, sex, rng):
    """clothes: dict MPFB item name -> object (already fitted + rigged). Returns (mpfb, modelled)."""
    L = P.lm
    knee = (L['l-knee'].z + L['r-knee'].z) / 2
    hip = L['pelvis'].z if 'pelvis' in L else knee + 0.45
    crotch = L['l-upper-leg'].z
    ankle = L['l-ankle'].z
    waist = crotch + 0.18
    shoulder = L['l-shoulder'].z
    neck = L['neck'].z
    eye = (L['l-eye'].z + L['r-eye'].z) / 2
    mouth = L['mouth']
    mpfb, modelled = [], []

    def suit(name, z=None):
        o = clothes.get(name)
        return split_clothes(o, knee if z is None else z, P, waist) if o else (None, None)

    def keep_any(o, label):
        if o:  # MPFB clothes hide skin with their own authored delete groups
            mpfb.append(label)
            P.under.append(o)

    tee = rng.choice(_TEE)
    co, part, dom = P.co, P.part, P.dom
    UPPER = {'spine', 'clavicle', 'upperarm', 'lowerarm', 'neck', 'pelvis'}

    def upper_body(i, arms=True, lower_arm=True, z0=None):
        p = part[i]
        if p == 'neck':
            return co[i].z < neck - 0.02
        if p == 'pelvis':
            return co[i].z > (z0 if z0 is not None else waist - 0.06)
        if p == 'upperarm':
            return arms
        if p == 'lowerarm':
            return arms and lower_arm
        return p in ('spine', 'clavicle')

    def hang_front(bm):  # coat/vest fronts hang straight from the chest instead of hugging the belly
        ych = min(v.co.y for v in bm.verts if abs(v.co.x) < 0.1 and shoulder - 0.25 < v.co.z < shoulder - 0.1)
        for v in bm.verts:
            if v.co.z < shoulder - 0.15 and abs(v.co.x) < 0.2 and v.co.y < 0:
                f = min(1.0, (shoulder - 0.15 - v.co.z) / 0.2)
                v.co.y = min(v.co.y, v.co.y * (1 - 0.8 * f) + (ych + 0.01) * 0.8 * f)

    def coat(colr, label, length=None, apron=False):
        m = fabric(P.rig.name + '.' + label, colr, rough=0.75, sheen=0.3, seam=True)
        vtop = shoulder - 0.02
        vbot = shoulder - (0.2 if apron else 0.3)

        def vneck(i):  # open front V (lapels) showing the shirt underneath; PPE coats are closed
            z = co[i].z
            return False  # ponytail: V-cut removed (read as a pinafore); placket seam in the shader instead
        shell(P, label, lambda i: (upper_body(i, z0=waist - 0.04) or (part[i] == 'neck' and co[i].z < neck - 0.03))
              and not vneck(i), 0.026, m, smooth=14, gap=0.022, hang=hang_front)
        tube(P, label + '_skirt', waist + 0.03, (knee - 0.06) if length is None else length, m,
             margin=0.03, waist_margin=0.016, flare=0.05, folds=0.05, nfold=11)
        modelled.append(label)

    def boots(colr, label='gumboots', top=None):
        m = fabric(P.rig.name + '.' + label, colr, rough=0.35, sheen=0, fold=0.15, gloss=True)
        zt = top if top is not None else ankle + 0.27

        def flat(bm):
            for v in bm.verts:
                v.co.z = max(v.co.z, -0.012)
        shell(P, label, lambda i: part[i] in ('foot', 'ball') or (part[i] == 'calf' and co[i].z < zt),
              0.012, m, smooth=10, gap=0.012, post=flat, disp=0.002)
        modelled.append(label)

    def gloves(colr):
        m = fabric(P.rig.name + '.gloves', colr, rough=0.45, sheen=0, fold=0.1)
        shell(P, 'gloves', lambda i: part[i] == 'hand' or (part[i] == 'lowerarm' and (co[i] - (L['l-hand'] if co[i].x > 0 else L['r-hand'])).length < 0.09),
              0.0035, m, smooth=1, gap=0.003, solid=0.0015, disp=0.0)
        modelled.append('gloves')

    def headcover(colr, label, pattern, off):
        m = fabric(P.rig.name + '.' + label, colr, rough=0.9, sheen=0.2, pattern=pattern)
        sc = set(P.groups.get('scalp', []))
        shell(P, label, lambda i: dom[i] == 'head' and (i in sc or (co[i].z > eye + 0.045 and co[i].y > mouth.y + 0.02)
                                                       or (co[i].y > mouth.y + 0.07 and co[i].z > mouth.z))
              , off, m, smooth=8, gap=off * 0.8, disp=0.006)
        modelled.append(label)

    def mask(colr):
        m = fabric(P.rig.name + '.mask', colr, rough=0.85, sheen=0.1, fold=0.1)
        nose_z = eye - 0.03
        shell(P, 'mask', lambda i: dom[i] == 'head' and mouth.z - 0.055 < co[i].z < nose_z and co[i].y < mouth.y + 0.035
              and abs(co[i].x) < 0.068 and P.no[i].y < -0.15, 0.008, m, smooth=10, gap=0.006, disp=0.0, solid=0.002)
        modelled.append('face_mask')

    if outfit == 'ppe_plant':
        up, lo = suit('male_casualsuit04' if sex == 'male' else 'female_casualsuit01')
        if up:
            tint_mpfb(up, (0.9, 0.9, 0.88), plain=True); keep_any(up, 'MPFB tee (recoloured)')
        if lo:
            tint_mpfb(lo, (0.82, 0.83, 0.84), plain=True); keep_any(lo, 'MPFB trousers (recoloured white)')
        boots((0.8, 0.8, 0.78), 'gumboots', top=knee - 0.1)
        coat((0.8, 0.8, 0.78), 'coat', length=knee - 0.02, apron=True)
        am = fabric(P.rig.name + '.apron', (0.74, 0.79, 0.83), rough=0.3, sheen=0, fold=0.2, gloss=True)
        shell(P, 'apron_bib', lambda i: part[i] in ('spine', 'pelvis') and co[i].y < -0.02 and abs(co[i].x) < 0.15
              and waist - 0.04 < co[i].z < shoulder - 0.09, 0.034, am, smooth=10, gap=0.03, hang=hang_front)
        tube(P, 'apron', waist + 0.0, knee - 0.12, am, margin=0.045, waist_margin=0.05, flare=0.06, folds=0.03,
             nfold=7, arc=math.radians(68))
        modelled.append('apron')
        gloves((0.25, 0.42, 0.75))
        headcover((0.82, 0.82, 0.82), 'hairnet', 'net', 0.018)
        mask((0.55, 0.7, 0.8) if rng.random() < 0.6 else (0.8, 0.8, 0.8))
        return mpfb, modelled

    if outfit == 'thermal_suit':
        navy = rng.choice([(0.05, 0.08, 0.16), (0.12, 0.13, 0.15), (0.03, 0.12, 0.2)])
        m = fabric(P.rig.name + '.thermal', navy, rough=0.55, sheen=0.25, pattern='quilt', fold=0.3)
        boots((0.05, 0.05, 0.05), 'boots', top=ankle + 0.2)
        shell(P, 'thermal_suit', lambda i: (part[i] in UPPER and (part[i] != 'neck' or co[i].z < neck - 0.0))
              or part[i] == 'thigh' or (part[i] == 'calf' and co[i].z > ankle + 0.1),
              0.045, m, smooth=14, gap=0.038, hang=hang_front, disp=0.008)
        modelled.append('padded thermal suit')
        gloves((0.06, 0.06, 0.06))
        headcover(navy, 'beanie', 'knit', 0.012)
        return mpfb, modelled

    if outfit == 'hivis_helmet':
        o = clothes.get('male_worksuit01')
        keep_any(o, 'MPFB male_worksuit01 (overalls + tee)')
        sh = clothes.get('shoes03'); keep_any(sh, 'MPFB shoes03')
        vc = rng.choice([(1.0, 0.32, 0.02), (0.75, 1.0, 0.05)])
        m = fabric(P.rig.name + '.vest', vc, rough=0.7, sheen=0.1, pattern='bands', color2=(0.75, 0.75, 0.72),
                   band=(waist + 0.06, 0.24, 0.05))
        shell(P, 'hivis_vest', lambda i: upper_body(i, arms=False, z0=waist - 0.02) and part[i] != 'neck'
              and not (part[i] == 'clavicle' and co[i].z > shoulder + 0.04),
              0.028, m, smooth=8, gap=0.024, hang=hang_front)
        modelled.append('hi-vis vest')
        hc = rng.choice([(0.95, 0.75, 0.05), (0.92, 0.92, 0.9), (0.95, 0.4, 0.05)])
        helmet(P, fabric(P.rig.name + '.helmet', hc, rough=0.3, sheen=0, fold=0.05, gloss=True))
        modelled.append('hard hat')
        return mpfb, modelled

    if outfit in ('formal_shirt_lanyard', 'lab_coat'):
        if sex == 'male':
            up, lo = suit('male_casualsuit01')
            if up and rng.random() < 0.6:
                tint_mpfb(up, rng.choice([(0.88, 0.88, 0.86), (0.62, 0.72, 0.85), (0.7, 0.66, 0.78)]), plain=True)
            keep_any(up, 'MPFB male_casualsuit01 shirt')
            if lo:
                tint_mpfb(lo, rng.choice([(0.12, 0.12, 0.13), (0.25, 0.22, 0.18), (0.16, 0.17, 0.2)]), plain=True)
                keep_any(lo, 'MPFB trousers (recoloured)')
        else:
            keep_any(clothes.get('female_elegantsuit01'), 'MPFB female_elegantsuit01')
        keep_any(clothes.get('shoes01') or clothes.get('shoes04'), 'MPFB shoes')
        if outfit == 'lab_coat':
            coat((0.82, 0.82, 0.8), 'lab_coat', length=knee + 0.02)
        else:
            # lanyard: ring around the neck base, down to a blank card on the chest
            nb = L['neck']; chest_z = shoulder - 0.2
            ring = [i for i in range(len(co)) if P.inbody[i] and abs(co[i].z - (nb.z - 0.04)) < 0.012
                    and part[i] in ('neck', 'spine', 'clavicle')]
            ys = [co[i].y for i in ring] or [0.0]
            xs = [abs(co[i].x) for i in ring] or [0.06]
            rx, ry0, ry1 = max(xs) + 0.012, min(ys) - 0.012, max(ys) + 0.012
            pts = []
            yc, ry = (ry0 + ry1) / 2, (ry1 - ry0) / 2
            for k in range(15):  # a measured from the back (+Y): left front -> back -> right front
                a = math.radians(125 - 250 * k / 14)
                pts.append(Vector((rx * math.sin(a), yc + ry * math.cos(a), nb.z - 0.045 - 0.03 * (1 - math.cos(a)) / 2)))
            front_y = min(co[i].y for i in range(len(co)) if P.inbody[i] and part[i] == 'spine' and abs(co[i].x) < 0.05 and abs(co[i].z - chest_z) < 0.03)
            card = Vector((0, front_y - 0.012, chest_z))
            pts = [card + Vector((0.012, 0, 0.01))] + [pts[0].lerp(card, 0.5) + Vector((0, -0.02, 0))] + pts + \
                  [pts[-1].lerp(card, 0.5) + Vector((0, -0.02, 0)), card + Vector((-0.012, 0, 0.01))]
            trees = P.bvh_under()
            pts = [_push_out(trees, p, 0.008) for p in pts]
            lc = rng.choice([(0.05, 0.15, 0.45), (0.5, 0.05, 0.05), (0.05, 0.05, 0.06)])
            _ribbon(P, 'lanyard', pts, 0.016, 0.0015, fabric(P.rig.name + '.lanyard', lc, rough=0.6, fold=0.05))
            bmc = bmesh.new()
            bmesh.ops.create_cube(bmc, size=1.0)
            for v in bmc.verts:
                v.co = Vector((v.co.x * 0.055, v.co.y * 0.004, v.co.z * 0.085)) + card + Vector((0, -0.004, -0.045))
            me = bpy.data.meshes.new('card'); bmc.to_mesh(me); bmc.free()
            cobj = _new_obj(P, P.rig.name + '.id_card', me)
            cobj.vertex_groups.new(name='spine_03').add(list(range(len(me.vertices))), 1.0, 'REPLACE')
            _finish_garment(P, cobj, fabric(P.rig.name + '.card', (0.9, 0.9, 0.88), rough=0.3, sheen=0, fold=0),
                            solid=0, disp=0, opaque=False)
            modelled.append('lanyard + blank ID card')
        return mpfb, modelled

    if outfit in ('tshirt_lungi', 'tshirt_shorts', 'cotton_shirt_lungi_towel'):
        if outfit == 'cotton_shirt_lungi_towel':
            nm = 'male_casualsuit01' if sex == 'male' else 'female_elegantsuit01'
            up, lo = suit(nm, z=crotch + 0.05 if sex == 'female' else knee)
            if up:
                if sex == 'male':
                    tint_mpfb(up, rng.choice([(0.86, 0.84, 0.78), (0.6, 0.68, 0.78), (0.78, 0.74, 0.62)]), plain=True)
                keep_any(up, 'MPFB %s cotton shirt (recoloured)' % nm)
        else:
            nm = 'male_casualsuit04' if sex == 'male' else ('female_casualsuit01' if outfit == 'tshirt_lungi'
                                                            else 'female_casualsuit02')
            up, lo = suit(nm, z=knee if sex == 'male' or outfit == 'tshirt_lungi' else crotch + 0.12)
            if up:
                tint_mpfb(up, tee, plain=True); keep_any(up, 'MPFB %s tee (recoloured, logo removed)' % nm)
        if outfit == 'tshirt_shorts':
            if lo:
                if sex == 'male':
                    _delete_verts(lo, [v.index for v in lo.data.vertices if v.co.z < knee + 0.07])
                    vg = P.body.vertex_groups.get('Delete.' + nm)
                    if vg:  # un-hide the shins the cut jeans no longer cover
                        vg.remove([i for i in range(len(co)) if co[i].z < knee + 0.07])
                    tint_mpfb(lo, rng.choice([(0.55, 0.5, 0.38), (0.2, 0.22, 0.25), (0.3, 0.33, 0.25)]), plain=True)
                keep_any(lo, 'MPFB jeans cut to shorts')
            sh = clothes.get('shoes05') or clothes.get('shoes02'); keep_any(sh, 'MPFB sneakers')
            return mpfb, modelled
        if lo:
            bpy.data.objects.remove(lo)
        if outfit == 'tshirt_lungi':
            c1, c2 = rng.choice(_LUNGI)
            lm = fabric(P.rig.name + '.lungi', c1, rough=0.85, pattern='plaid', color2=[a * 0.55 + b * 0.45 for a, b in zip(c1, c2)], check=9)
        else:
            lm = fabric(P.rig.name + '.mundu', _MUNDU, rough=0.85, pattern='bands', color2=(0.62, 0.45, 0.12),
                        band=(ankle + 0.09, 5.0, 0.025))
        tube(P, 'lungi', waist + 0.02, ankle + 0.04, lm, margin=0.025, waist_margin=0.012, flare=0.04,
             folds=0.07, nfold=12)
        modelled.append('lungi' if outfit == 'tshirt_lungi' else 'mundu (white lungi)')
        if outfit == 'cotton_shirt_lungi_towel':
            sx = 1 if rng.random() < 0.5 else -1
            tm = fabric(P.rig.name + '.towel', (0.85, 0.8, 0.68), rough=0.95, sheen=0.5, pattern='plaid',
                        color2=(0.55, 0.14, 0.1), check=7)
            shell(P, 'towel', lambda i: co[i].x * sx > 0.04 and co[i].x * sx < 0.2 and co[i].z > shoulder - 0.28
                  and part[i] in ('spine', 'clavicle', 'neck', 'upperarm') and (part[i] != 'upperarm' or co[i].z > shoulder - 0.04)
                  and co[i].z < neck - 0.0, 0.018, tm, smooth=8, gap=0.016, solid=0.005, disp=0.006)
            modelled.append('shoulder towel')
        return mpfb, modelled

    if outfit == 'oilskins':
        up, lo = None, None
        o = clothes.get('male_worksuit01')
        if o:
            up, lo = split_clothes(o, knee, P, waist)
        if up:
            tint_mpfb(up, tee, plain=True); keep_any(up, 'MPFB worksuit tee (recoloured)')
        if lo:
            tint_mpfb(lo, rng.choice([(0.95, 0.62, 0.02), (0.9, 0.3, 0.03), (0.95, 0.75, 0.05)]), plain=True, rough=0.25)
            keep_any(lo, 'MPFB worksuit bib overalls -> oilskin bib trousers')
        boots(rng.choice([(0.9, 0.9, 0.88), (0.05, 0.05, 0.05)]), 'gumboots', top=knee - 0.08)
        return mpfb, modelled

    if outfit in ('diner_shirt', 'diner_sweater'):
        if sex == 'male':
            nm = next(k for k in clothes if k.startswith('male_casualsuit'))
            o = clothes.get(nm)
            if outfit == 'diner_sweater':
                up, lo = suit(nm)
                if up:
                    tint_mpfb(up, (0.85, 0.85, 0.82), plain=True); keep_any(up, 'MPFB tee')
                keep_any(lo, 'MPFB jeans')
            else:
                keep_any(o, 'MPFB %s' % nm)
        else:
            if outfit == 'diner_shirt':
                keep_any(clothes.get('female_elegantsuit01'), 'MPFB female_elegantsuit01')
            else:
                up, lo = suit('female_casualsuit01')
                if up:
                    tint_mpfb(up, (0.85, 0.85, 0.82), plain=True); keep_any(up, 'MPFB tee')
                keep_any(lo, 'MPFB jeans')
        keep_any(clothes.get('shoes01') or clothes.get('shoes04') or clothes.get('shoes02'), 'MPFB shoes')
        if outfit == 'diner_sweater':
            sc = rng.choice([(0.35, 0.08, 0.1), (0.25, 0.27, 0.3), (0.1, 0.15, 0.28), (0.4, 0.33, 0.22)])
            m = fabric(P.rig.name + '.sweater', sc, rough=0.95, sheen=0.6, pattern='knit', fold=0.4)
            shell(P, 'sweater', lambda i: upper_body(i, z0=waist - 0.07) and not (part[i] == 'lowerarm' and
                  (co[i] - (L['l-hand'] if co[i].x > 0 else L['r-hand'])).length < 0.06),
                  0.014, m, smooth=6, gap=0.012, hang=hang_front, disp=0.004)
            modelled.append('knit sweater')
        return mpfb, modelled
    raise ValueError('unknown outfit %r' % outfit)


def _mpfb_items(outfit, sex, rng):
    m = sex == 'male'
    return {
        'ppe_plant': ['male_casualsuit04' if m else 'female_casualsuit01'],
        'thermal_suit': [],
        'hivis_helmet': ['male_worksuit01', 'shoes03'],
        'formal_shirt_lanyard': ['male_casualsuit01' if m else 'female_elegantsuit01', 'shoes01' if m else 'shoes04'],
        'lab_coat': ['male_casualsuit01' if m else 'female_elegantsuit01', 'shoes01' if m else 'shoes04'],
        'tshirt_lungi': ['male_casualsuit04' if m else 'female_casualsuit01'],
        'tshirt_shorts': ['male_casualsuit04' if m else 'female_casualsuit02', 'shoes05'],
        'cotton_shirt_lungi_towel': ['male_casualsuit01' if m else 'female_elegantsuit01'],
        'oilskins': ['male_worksuit01'],
        'diner_shirt': [rng.choice(['male_casualsuit01', 'male_casualsuit03']) if m else 'female_elegantsuit01',
                        'shoes01' if m else 'shoes04'],
        'diner_sweater': ['male_casualsuit04' if m else 'female_casualsuit01', 'shoes02' if m else 'shoes04'],
    }[outfit]


# ----------------------------------------------------------------------------------------------
# faces / body
# ----------------------------------------------------------------------------------------------

_FACE_T = [  # (target base, symmetric l/r?)  value range +-
    ('head-oval', 0), ('head-round', 0), ('head-square', 0), ('head-age-decr|head-age-incr', 0),
    ('head-scale-vert-decr|head-scale-vert-incr', 0), ('head-scale-horiz-decr|head-scale-horiz-incr', 0),
    ('nose-scale-horiz-decr|nose-scale-horiz-incr', 0), ('nose-scale-vert-decr|nose-scale-vert-incr', 0),
    ('nose-trans-up|nose-trans-down', 0), ('nose-width1-decr|nose-width1-incr', 0),
    ('nose-hump-decr|nose-hump-incr', 0), ('nose-nostrils-width-decr|nose-nostrils-width-incr', 0),
    ('nose-point-width-decr|nose-point-width-incr', 0), ('nose-base-up|nose-base-down', 0),
    ('mouth-scale-horiz-decr|mouth-scale-horiz-incr', 0), ('mouth-lowerlip-height-decr|mouth-lowerlip-height-incr', 0),
    ('mouth-upperlip-height-decr|mouth-upperlip-height-incr', 0), ('mouth-trans-up|mouth-trans-down', 0),
    ('chin-width-decr|chin-width-incr', 0), ('chin-prominent-decr|chin-prominent-incr', 0),
    ('chin-height-decr|chin-height-incr', 0), ('chin-jaw-drop-decr|chin-jaw-drop-incr', 0),
    ('cheek-bones-decr|cheek-bones-incr', 1), ('cheek-volume-decr|cheek-volume-incr', 1),
    ('eye-scale-decr|eye-scale-incr', 1), ('eye-trans-down|eye-trans-up', 1),
    ('eye-bag-decr|eye-bag-incr', 1), ('eye-height2-decr|eye-height2-incr', 1),
    ('ear-scale-decr|ear-scale-incr', 1), ('ear-flap-decr|ear-flap-incr', 1),
    ('forehead-trans-backward|forehead-trans-forward', 0), ('eyebrows-trans-down|eyebrows-trans-up', 0),
    ('neck-scale-horiz-decr|neck-scale-horiz-incr', 0),
]


def _face_targets(rng):
    out = []
    for base, sym in _FACE_T:
        opts = base.split('|')
        nm = rng.choice(opts)
        v = rng.uniform(0.05, 0.7) if len(opts) == 1 else rng.uniform(0.0, 0.8)
        if len(opts) == 1 and rng.random() < 0.5:
            continue
        if sym:
            for s in ('l-', 'r-'):
                out.append({'target': s + nm, 'value': v})
        else:
            out.append({'target': nm, 'value': v})
    return out


def _mpfb_age(age):
    years = 18 + age * 62
    if years <= 25:
        return 0.1875 + (years - 11) / 14 * 0.3125
    return min(1.0, 0.5 + (years - 25) / 65 * 0.5)


def _hide_under(P):
    """Mask body skin covered by the modelled opaque garments: a ray along the normal, started 1.5 cm
    inside the skin, hits a garment within ~7 cm. (MPFB clothes keep MPFB's own Delete.* masks.)"""
    trees = []
    for o in P.garments:
        trees.append(BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices],
                                          [p.vertices[:] for p in o.data.polygons]))
    hide = []
    for i, (c, n) in enumerate(zip(P.co, P.no)):
        if not P.inbody[i]:
            continue
        o = c - n * 0.015
        reach = 0.03 if P.part[i] in ('neck', 'head') else 0.085  # open collars stand off the neck
        for t in trees:
            hit = t.ray_cast(o, n, reach)
            if hit[0] is not None:
                hide.append(i)
                break
    body = P.body
    if not hide:
        return
    vg = body.vertex_groups.new(name='sk_hide')
    vg.add(hide, 1.0, 'REPLACE')
    mk = body.modifiers.new('sk_hide', 'MASK'); mk.vertex_group = 'sk_hide'; mk.invert_vertex_group = True


# ----------------------------------------------------------------------------------------------
# poses
# ----------------------------------------------------------------------------------------------

def _set_rot(rig, bone, rx=0.0, ry=0.0, rz=0.0, mirror=True):
    """Rotation in rest-armature axes (X = character's left, Y = back, Z = up), degrees,
    expressed in the parent's (posed) frame. *_l values mirror to *_r when mirror=True."""
    pb = rig.pose.bones.get(bone)
    if pb is None:
        return
    R = rig.data.bones[bone].matrix_local.to_3x3()
    q = Euler((math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ').to_matrix()
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = (R.inverted() @ q @ R).to_quaternion()


def _pose_dict(pose, rng):
    """Euler (spine/legs, rest-armature axes, see _set_rot) + arm specs per side:
    ('aim', upper_dir, fore_dir, hand_dir) or ('reach', wrist_target, pole_dir, hand_dir), armature space,
    left side; right side mirrors x unless given explicitly."""
    j = lambda a: a + rng.uniform(-3, 3)
    v = lambda *c: Vector(c)
    d = {}
    shift = rng.uniform(2, 5)
    d['pelvis'] = (0, shift, 0)
    d['spine_01'] = (j(1), -shift * 0.6, 0)
    d['spine_03'] = (j(2), -shift * 0.4, j(0))
    d['neck_01'] = (j(-2), 0, j(0))
    d['head'] = (j(4), j(0), j(0))
    d['thigh_l'] = (0, -shift, 0); d['thigh_r'] = (-6, -shift + 1, 4)
    d['calf_r'] = (12, 0, 0)
    eb = rng.uniform(0.25, 0.45)
    arms = {'l': ('aim', v(0.12, 0.04, -1), v(0.06, -eb, -1), v(0.03, -eb * 0.5, -1)),
            'r': ('aim', v(-0.12, 0.06, -1), v(-0.08, -eb - 0.08, -1), v(-0.03, -eb * 0.5, -1))}
    if pose == 'walk':
        d.update(thigh_l=(-20, 0, 0), calf_l=(6, 0, 0), thigh_r=(14, 0, 2), calf_r=(22, 0, 0),
                 pelvis=(0, 0, j(3)), spine_01=(4, 0, j(-3)))
        arms = {'l': ('aim', v(0.1, 0.32, -1), v(0.06, 0.05, -1), v(0.03, 0.0, -1)),
                'r': ('aim', v(-0.1, -0.3, -1), v(-0.06, -0.75, -1), v(-0.03, -0.5, -1))}
    elif pose == 'work_table':
        d['spine_01'] = (12, 0, 0); d['spine_02'] = (9, 0, 0); d['spine_03'] = (6, 0, j(0))
        d['neck_01'] = (6, 0, 0); d['head'] = (16, 0, j(0))
        dx = rng.uniform(-0.04, 0.04)
        arms = {'l': ('reach', v(0.17 + dx, -0.45, 0.95), v(0.7, 0.4, -0.3), v(0.0, -1, -0.9)),
                'r': ('reach', v(-0.15 + dx, -0.42, 0.95), v(-0.7, 0.4, -0.3), v(0.0, -1, -0.9))}
    elif pose == 'carry':
        d['spine_01'] = (-4, 0, 0); d['spine_03'] = (-3, 0, 0)
        arms = {'l': ('reach', v(0.2, -0.33, 0.98), v(0.6, 0.5, -0.3), v(-0.2, -1, 0.1)),
                'r': ('reach', v(-0.2, -0.33, 0.98), v(-0.6, 0.5, -0.3), v(0.2, -1, 0.1))}
    elif pose == 'pull_rope':
        d['pelvis'] = (-6, 0, 10)
        d['spine_01'] = (-8, 0, -6); d['spine_03'] = (-4, 0, -6); d['head'] = (8, 0, 0)
        d['thigh_l'] = (-28, 0, 0); d['calf_l'] = (24, 0, 0)
        d['thigh_r'] = (14, 0, 0); d['calf_r'] = (16, 0, 0)
        arms = {'l': ('reach', v(0.04, -0.58, 1.08), v(0.6, 0.2, -0.6), v(-0.1, -1, 0.0)),
                'r': ('reach', v(-0.0, -0.36, 1.03), v(-0.6, 0.3, -0.6), v(0.1, -1, 0.0))}
    elif pose == 'wave':
        d['spine_03'] = (0, 3, 0); d['head'] = (2, 0, 6)
        arms['r'] = ('aim', v(-0.8, -0.15, 0.25), v(-0.12, -0.25, 1), v(-0.05, -0.1, 1))
    elif pose == 'sit':
        d['pelvis'] = (0, 0, 0); d['spine_01'] = (6, 0, 0); d['spine_03'] = (4, 0, 0)
        d['thigh_l'] = (-82, 0, -4); d['thigh_r'] = (-86, 0, 6)
        d['calf_l'] = (80, 0, 0); d['calf_r'] = (90, 0, 0)
        arms = {'l': ('aim', v(0.08, -0.3, -1), v(0.0, -1, -0.3), v(0.0, -1, -0.4)),
                'r': ('aim', v(-0.08, -0.25, -1), v(-0.05, -1, -0.25), v(0.0, -1, -0.4))}
    elif pose == 'crouch':
        d['pelvis'] = (0, 0, 0)
        d['spine_01'] = (22, 0, 0); d['spine_02'] = (12, 0, 0); d['spine_03'] = (8, 0, 0); d['head'] = (-15, 0, 0)
        d['thigh_l'] = (-105, 0, -12); d['thigh_r'] = (-100, 0, 12)
        d['calf_l'] = (135, 0, 0); d['calf_r'] = (130, 0, 0)
        arms = {'l': ('aim', v(0.05, -0.55, -1), v(-0.25, -1, -0.15), v(-0.2, -1, -0.5)),
                'r': ('aim', v(-0.05, -0.55, -1), v(0.25, -1, -0.15), v(0.2, -1, -0.5))}
    elif pose != 'stand':
        raise ValueError('unknown pose %r' % pose)
    # feet flat on the ground
    for s in ('l', 'r'):
        t = d.get('thigh_' + s, (0, 0, 0))[0] + d.get('calf_' + s, (0, 0, 0))[0] + d.get('pelvis', (0, 0, 0))[0]
        if pose == 'walk' and s == 'r':
            t -= 18  # trailing heel lifts
        d['foot_' + s] = (-t, 0, 0)
    return d, arms


def _aim(rig, bone, direction):
    """Swing a posed bone so it points along `direction` (armature space)."""
    bpy.context.view_layer.update()
    pb = rig.pose.bones[bone]
    q = (pb.tail - pb.head).normalized().rotation_difference(Vector(direction).normalized())
    h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix


def _arm(rig, s, spec):
    up, lo, ha = 'upperarm_' + s, 'lowerarm_' + s, 'hand_' + s
    if spec[0] == 'aim':
        _aim(rig, up, spec[1]); _aim(rig, lo, spec[2]); _aim(rig, ha, spec[3])
        return
    _, T, pole, hand_dir = spec
    bpy.context.view_layer.update()
    S = rig.pose.bones[up].head.copy()
    a = rig.data.bones[up].length; b = rig.data.bones[lo].length
    dv = T - S
    dist = min(dv.length, 0.93 * (a + b))  # never a locked-straight arm
    u = dv.normalized()
    n = (pole - u * pole.dot(u)).normalized()
    x = (a * a - b * b + dist * dist) / (2 * dist)
    h = math.sqrt(max(0.0, a * a - x * x))
    E = S + u * x + n * h
    _aim(rig, up, E - S)
    _aim(rig, lo, S + u * dist - E)
    _aim(rig, ha, hand_dir)


def apply_pose(rig, pose, rng=None):
    rng = rng or random.Random(0)
    d, arms = _pose_dict(pose, rng)
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
    for b, r in d.items():
        _set_rot(rig, b, *r)
    for s in ('l', 'r'):
        _arm(rig, s, arms[s])
    # relaxed / gripping fingers
    for s in ('l', 'r'):
        curl = 16 if pose not in ('carry', 'pull_rope') else 45
        for f in ('index', 'middle', 'ring', 'pinky'):
            for k in ('01', '02', '03'):
                _set_rot(rig, '%s_%s_%s' % (f, k, s), -(curl + rng.uniform(-6, 6)), 0, 0)
    bpy.context.view_layer.update()
    rig['sk_pose'] = pose
    for pb in rig.pose.bones:
        pb['sk_base'] = list(pb.rotation_quaternion)


def _ground(rig):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    mz = None
    for o in rig.children:
        if o.type != 'MESH' or o.hide_render:
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        for v in me.vertices:
            z = (mw @ v.co).z
            if mz is None or z < mz:
                mz = z
        ev.to_mesh_clear()
    return mz or 0.0


# ----------------------------------------------------------------------------------------------
# public API
# ----------------------------------------------------------------------------------------------

def make_person(name, sex='male', age=0.4, body=None, skin_tone=0.6, outfit='tshirt_lungi', pose='stand',
                location=(0, 0, 0), rotation_z=0.0, seed=0, lod='L0'):
    """Build one rigged, dressed, posed MPFB person. Returns the armature (root) object.
    age 0..1 maps to 18..80 years; body dict weight/muscle/height 0..1 (0.5 average);
    skin_tone 0 light wheat-brown .. 1 deep brown; lod 'L0' full, 'L1' decimated for crowds."""
    assert outfit in OUTFITS, outfit
    assert pose in POSES, pose
    rng = random.Random(seed * 7919 + _h(name) % 1000)
    body = dict(body or {})
    female = sex == 'female'
    ph = {
        'gender': 0.0 if female else 1.0,
        'age': _mpfb_age(age),
        'muscle': min(1, max(0, body.get('muscle', 0.5) + rng.uniform(-0.08, 0.08))),
        'weight': min(1, max(0, body.get('weight', 0.5) + rng.uniform(-0.08, 0.08))),
        'height': min(1, max(0, body.get('height', 0.45 if female else 0.5) + rng.uniform(-0.1, 0.1))),
        'proportions': rng.uniform(0.4, 0.7),
        'cupsize': rng.uniform(0.4, 0.6), 'firmness': rng.uniform(0.4, 0.6),
    }
    af = rng.uniform(0.35, 0.55); asn = rng.uniform(0.03, 0.12)
    ph['race'] = {'african': af, 'asian': asn, 'caucasian': max(0.05, 1 - af - asn)}
    years = 18 + age * 62
    agegrp = 'young' if years < 33 else ('middleage' if years < 58 else 'old')
    skin_eth = 'african' if skin_tone > 0.2 else 'asian'
    hi = HumanService._create_default_human_info_dict()
    hi['phenotype'].update({k: v for k, v in ph.items()})
    hi['name'] = name
    hi['rig'] = 'game_engine'
    hi['eyes'] = 'low-poly.mhclo'
    hi['eyebrows'] = 'eyebrow%03d.mhclo' % rng.choice([1, 2, 3, 5, 6, 7, 9, 10, 11, 12] if not female else [3, 4, 8, 10, 12])
    hi['eyelashes'] = 'eyelashes0%d.mhclo' % rng.choice([1, 2, 3, 4])
    covered = outfit in ('ppe_plant', 'thermal_suit', 'hivis_helmet')
    if not covered:
        hi['hair'] = rng.choice(['short01', 'short02', 'short03', 'short04'] if not female else
                                ['braid01', 'ponytail01', 'braid01', 'bob02']) + '.mhclo'
    elif female and outfit == 'hivis_helmet':
        hi['hair'] = 'braid01.mhclo'
    hi['skin_mhmat'] = '%s_%s_%s.mhmat' % (agegrp, skin_eth, 'female' if female else 'male')
    hi['skin_material_type'] = 'ENHANCED_SSS'
    hi['eyes_material_type'] = 'MAKESKIN'
    hi['targets'] = _face_targets(rng)
    hi['clothes'] = [c + '.mhclo' for c in _mpfb_items(outfit, sex, rng)]
    ds = HumanService.get_default_deserialization_settings()
    ds['subdiv_levels'] = 0
    bm_ = HumanService.deserialize_from_dict(hi, ds)
    rig = bm_.parent
    rig.name = name
    kids = list(rig.children)
    bodyobj = bm_
    _skin(bodyobj, skin_tone, rng)
    clothes = {}
    for o in kids:
        if o is bodyobj or o.type != 'MESH':
            continue
        nm = o.name.split('.', 1)[-1].split('.')[0]
        if nm.startswith(('short', 'braid', 'ponytail', 'bob', 'long', 'afro')):
            g = rng.uniform(0.06, 0.16)
            tint_mpfb(o, (g, g * 0.9, g * 0.85)) if years < 60 else tint_mpfb(o, (0.5, 0.48, 0.46), 'MIX', 0.45)
        elif nm.startswith('eyebrow'):
            tint_mpfb(o, (0.15, 0.12, 0.1))
        elif nm.startswith(('male_', 'female_', 'shoes')):
            clothes[nm] = o
    if 'eyes' in hi:
        for o in kids:
            if 'low-poly' in o.name:
                tint_mpfb(o, (0.35, 0.22, 0.14), 'MULTIPLY', 0.8)
    P = _Ctx(rig, bodyobj)
    # unused MPFB items (e.g. jeans removed for lungi) are deleted inside _outfit
    mpfb_used, modelled = _outfit(P, outfit, clothes, sex, rng)
    _hide_under(P)
    rig['sk_outfit'] = outfit
    rig['sk_mpfb'] = ', '.join(mpfb_used)
    rig['sk_modelled'] = ', '.join(modelled)
    apply_pose(rig, pose, rng)
    if lod == 'L1':
        for o in rig.children:
            if o.type == 'MESH':
                if 'eyelashes' in o.name:
                    o.hide_render = o.hide_viewport = True
                    continue
                dm = o.modifiers.new('lod', 'DECIMATE'); dm.ratio = 0.35
    # place: feet on z=0 at location
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0)
    gz = _ground(rig)
    rig.location = Vector(location) + Vector((0, 0, -gz))
    rig.rotation_euler = (0, 0, rotation_z)
    rig['sk_seed'] = seed
    return rig


def tri_count(rig):
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in rig.children:
        if o.type == 'MESH' and not o.hide_render:
            ev = o.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles()
            n += len(me.loop_triangles); ev.to_mesh_clear()
    return n


# ----------------------------------------------------------------------------------------------
# animation
# ----------------------------------------------------------------------------------------------

_CYCLES = {  # kind: (period frames, {bone: [(axis, amplitude deg, harmonic, phase offset)]})
    'work': (44, {'spine_02': [(0, 1.5, 1, 0), (2, 2.5, 1, 0.25)], 'spine_03': [(2, 2, 1, 0.3)],
                  'head': [(0, 3, 1, 0.5), (2, 4, 1, 0.1)],
                  'upperarm_l': [(0, 6, 1, 0), (2, 4, 1, 0.25)], 'upperarm_r': [(0, 6, 1, 0.5), (2, 4, 1, 0.75)],
                  'lowerarm_l': [(0, 10, 1, 0.15)], 'lowerarm_r': [(0, 10, 1, 0.65)],
                  'hand_l': [(0, 8, 2, 0)], 'hand_r': [(0, 8, 2, 0.5)]}),
    'pull': (52, {'pelvis': [(0, 3, 1, 0)], 'spine_01': [(0, 8, 1, 0.05)], 'spine_03': [(0, 4, 1, 0.1)],
                  'upperarm_l': [(0, 14, 1, 0.1)], 'upperarm_r': [(0, 14, 1, 0.1)],
                  'lowerarm_l': [(0, 18, 1, 0.15)], 'lowerarm_r': [(0, 18, 1, 0.15)],
                  'thigh_l': [(0, 4, 1, 0)], 'calf_l': [(0, 5, 1, 0)]}),
    'wave': (18, {'lowerarm_r': [(2, 22, 1, 0)], 'hand_r': [(2, 10, 1, 0.1)], 'head': [(2, 3, 1, 0)],
                  'spine_03': [(2, 1.5, 1, 0)]}),
    'walk': (30, {'thigh_l': [(0, 22, 1, 0)], 'thigh_r': [(0, 22, 1, 0.5)],
                  'calf_l': [(0, 18, 1, 0.65)], 'calf_r': [(0, 18, 1, 0.15)],
                  'foot_l': [(0, 10, 1, 0.8)], 'foot_r': [(0, 10, 1, 0.3)],
                  'upperarm_l': [(0, 14, 1, 0.5)], 'upperarm_r': [(0, 14, 1, 0)],
                  'lowerarm_l': [(0, 8, 1, 0.55)], 'lowerarm_r': [(0, 8, 1, 0.05)],
                  'pelvis': [(2, 4, 1, 0), (1, 2, 1, 0.25)], 'spine_03': [(2, 5, 1, 0.5)]}),
}


def _fcurves(action):
    if hasattr(action, 'fcurves') and action.fcurves is not None and len(action.fcurves):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, 'layers', []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out += list(cb.fcurves)
    return out


def animate_cycle(person, kind='work', frame_start=1, frame_end=240, phase=0.0, amount=1.0):
    """Key a subtle looping motion on top of the person's pose (Cycles modifier -> loops through
    frame_end). phase 0..1 shifts the loop so neighbours never move in sync; the period is also
    jittered per person (seed)."""
    rig = person
    period, spec = _CYCLES[kind]
    rng = random.Random(int(rig.get('sk_seed', 0)) * 31 + _h(kind) % 97)
    period = int(round(period * rng.uniform(0.9, 1.12)))
    off = phase * period
    steps = 8
    for bone, chans in spec.items():
        pb = rig.pose.bones.get(bone)
        if pb is None:
            continue
        base = pb.get('sk_base')
        from mathutils import Quaternion
        qb = Quaternion(base) if base else pb.rotation_quaternion.copy()
        R = rig.data.bones[bone].matrix_local.to_3x3()
        sign = -1 if bone.endswith('_r') else 1
        for k in range(steps + 1):
            t = k / steps
            e = [0.0, 0.0, 0.0]
            for ax, amp, harm, ph in chans:
                a = amp * amount * math.sin(2 * math.pi * (harm * t + ph))
                e[ax] += a * (sign if ax != 0 else 1)
            q = Euler([math.radians(x) for x in e], 'XYZ').to_matrix()
            pb.rotation_quaternion = (R.inverted() @ q @ R).to_quaternion() @ qb
            pb.keyframe_insert('rotation_quaternion', frame=frame_start - off + t * period)
        pb.rotation_quaternion = qb
    act = rig.animation_data.action
    for fc in _fcurves(act):
        if not any(m.type == 'CYCLES' for m in fc.modifiers):
            fc.modifiers.new('CYCLES')
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
    return rig
