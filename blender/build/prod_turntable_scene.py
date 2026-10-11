"""S10 product turntable fallbacks: prod-tuna.blend / prod-prawn.blend (120 f, one linear 360 deg turn, loops).
  Blender --factory-startup -b --python prod_turntable_scene.py -- tuna|prawn|both [--stills <tag>]
Product = the live site GLB (assets-src/models/<name>.glb) on an ice-slab plinth (A-PROD-PLINTH) with crushed ice,
dark studio sweep (site B2 is a dark section), Poly Haven studio HDRI + softboxes. --stills renders f1/31/61/91
(0/90/180/270 deg) at 1920x1080 into assets-src/blender/stills/prod-<name>/<tag>-<deg>.png (run under render-lock-wd)."""
import math, random, sys
import bmesh, bpy
from mathutils import Vector, noise
sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import sklib
import look
from sklib import _n, _l, _maprange, _mix, _noise

A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['both']
WHICH = ['tuna', 'prawn'] if A[0] == 'both' else [A[0]]
TAG = A[A.index('--stills') + 1] if '--stills' in A else None


def bbox(obs):
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))


# ------------------------------------------------------------------------------------------------ A-PROD-PLINTH
def slab_mesh(L, W, H, seed):
    """Box (top at z=0) from uniform grids so chips get enough vertices; chipped edges = planar cuts near edges,
    hand-cut unevenness on the sides, top kept planar where the product rests."""
    rng = random.Random(seed)
    sp = L / 170
    bm = bmesh.new()
    faces = [((0, 0, 0), (L, W), (0, 0, 0)), ((0, 0, -H), (L, W), (math.pi, 0, 0)),
             ((0, -W / 2, -H / 2), (L, H), (math.pi / 2, 0, 0)), ((0, W / 2, -H / 2), (L, H), (-math.pi / 2, 0, 0)),
             ((L / 2, 0, -H / 2), (H, W), (0, math.pi / 2, 0)), ((-L / 2, 0, -H / 2), (H, W), (0, -math.pi / 2, 0))]
    from mathutils import Euler, Matrix
    for loc, (a, b), rot in faces:
        g = bmesh.new()
        bmesh.ops.create_grid(g, x_segments=max(2, round(a / sp)), y_segments=max(2, round(b / sp)), size=0.5)
        M = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
        ex = max(abs(v.co.x) for v in g.verts) * 2      # grid extent differs between Blender versions: normalise
        for v in g.verts:
            v.co = M @ Vector((v.co.x / ex * a, v.co.y / ex * b, 0))
        me = bpy.data.meshes.new('tmp'); g.to_mesh(me); g.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=sp * 0.2)
    # chips: planar cuts along the 12 edges (more on the top edges, the ones the camera sees)
    hx, hy = L / 2, W / 2
    edges = []
    for sy in (-1, 1):
        for sz in (0, -H):
            edges.append(((-hx, sy * hy, sz), (hx, sy * hy, sz), Vector((0, sy, 1 if sz == 0 else -1)), 3 if sz == 0 else 1))
    for sx in (-1, 1):
        for sz in (0, -H):
            edges.append(((sx * hx, -hy, sz), (sx * hx, hy, sz), Vector((sx, 0, 1 if sz == 0 else -1)), 3 if sz == 0 else 1))
        for sy in (-1, 1):
            edges.append(((sx * hx, sy * hy, 0), (sx * hx, sy * hy, -H), Vector((sx, sy, 0)), 1))
    cuts = []
    for a, b, n, w in edges:
        a, b = Vector(a), Vector(b)
        for _ in range(int(w * max(4, (b - a).length / H * 2.0))):
            c = a.lerp(b, rng.random())
            nn = (n.normalized() + Vector([rng.uniform(-0.35, 0.35) for _ in range(3)])).normalized()
            cuts.append((c - nn * H * rng.uniform(0.02, 0.08), nn, H * rng.uniform(0.15, 0.4)))
    for v in bm.verts:
        p = v.co
        for c, nn, r in cuts:
            if (p - c).length < r * 2.2:
                d = (p - c).dot(nn)
                if d > 0:
                    p = p - nn * d
        # hand-cut unevenness on sides/bottom; top stays flat inside (product contact), rolls off at the rim
        rim = min(hx - abs(p.x), hy - abs(p.y))
        amp = H * 0.035 * (1.0 if p.z < -0.02 * H else min(1.0, max(0.0, 1 - rim / (H * 0.5))))
        p = p + Vector((noise.noise(p * 9 / H + Vector((seed, 0, 0))) * amp,
                        noise.noise(p * 9 / H + Vector((0, seed, 3))) * amp,
                        noise.noise(p * 7 / H + Vector((5, 0, seed))) * amp * (1 if p.z < -0.02 * H else 0.3)))
        v.co = p
    return bm


def ice_slab_mat():
    m, nt = sklib._new_mat('ice_slab')
    out = _n(nt, 'ShaderNodeOutputMaterial', 1100, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 800, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    cloud = _noise(nt, tc.outputs['Object'], 2.2, 6.0, 0.62, -700, 200)            # milky cores / clear zones
    cm = _maprange(nt, cloud.outputs['Fac'], 0.4, 0.68, 0.0, 1.0, -450, 200)
    vo = _n(nt, 'ShaderNodeTexVoronoi', -700, -150)                                    # trapped air bubbles
    vo.inputs['Scale'].default_value = 60.0
    vo.inputs['Randomness'].default_value = 1.0
    _l(nt, tc.outputs['Object'], vo.inputs['Vector'])
    bub = _maprange(nt, vo.outputs['Distance'], 0.015, 0.045, 0.45, 0.0, -450, -150)
    sm = _n(nt, 'ShaderNodeMath', -200, 50, operation='MAXIMUM'); sm.use_clamp = True
    _l(nt, cm, sm.inputs[0]); _l(nt, bub, sm.inputs[1])
    _l(nt, _mix(nt, sm.outputs[0], (0.62, 0.82, 0.95), (0.88, 0.95, 1.0), 'MIX', 100, 250), b.inputs['Base Color'])
    _l(nt, _maprange(nt, sm.outputs[0], 0, 1, 0.85, 0.4, 100, 50), b.inputs['Transmission Weight'])
    fr = _noise(nt, tc.outputs['Object'], 14.0, 8.0, 0.7, -700, -450)                 # frost patches (matte)
    _l(nt, _maprange(nt, fr.outputs['Fac'], 0.55, 0.75, 0.03, 0.35, 100, -150), b.inputs['Roughness'])
    b.inputs['IOR'].default_value = 1.31
    b.inputs['Subsurface Weight'].default_value = 0.4
    b.inputs['Subsurface Radius'].default_value = (0.02, 0.03, 0.05)
    b.inputs['Subsurface Scale'].default_value = 0.02
    b.inputs['Coat Weight'].default_value = 1.0                                         # wet melt film
    b.inputs['Coat Roughness'].default_value = 0.02
    b.inputs['Coat IOR'].default_value = 1.33
    rip = _noise(nt, tc.outputs['Object'], 40.0, 4.0, 0.5, -700, -700)
    bp = _n(nt, 'ShaderNodeBump', 400, -400)
    bp.inputs['Strength'].default_value = 0.12
    _l(nt, rip.outputs['Fac'], bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    _l(nt, bp.outputs[0], b.inputs['Coat Normal'])
    for k, v in (('use_raytrace_refraction', True), ('surface_render_method', 'DITHERED'), ('thickness_mode', 'SLAB')):
        if hasattr(m, k):
            setattr(m, k, v)
    return m


def chunk_mat():
    """Crushed ice: clear, glossy, wet; whiter frosted cores in some chunks (object-space noise)."""
    m, nt = sklib._new_mat('ice_chunk_clear')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -700, 0)
    fr = _noise(nt, tc.outputs['Object'], 45.0, 6.0, 0.65, -500, 0)
    fm = _maprange(nt, fr.outputs['Fac'], 0.45, 0.7, 0.0, 1.0, -300, 0)
    _l(nt, _mix(nt, fm, (0.72, 0.88, 0.97), (0.92, 0.97, 1.0), 'MIX', -100, 250), b.inputs['Base Color'])
    _l(nt, _maprange(nt, fm, 0, 1, 0.6, 0.2, -100, 50), b.inputs['Transmission Weight'])
    _l(nt, _maprange(nt, fm, 0, 1, 0.04, 0.3, -100, -150), b.inputs['Roughness'])
    b.inputs['IOR'].default_value = 1.31
    b.inputs['Coat Weight'].default_value = 0.8
    b.inputs['Coat Roughness'].default_value = 0.02
    b.inputs['Subsurface Weight'].default_value = 0.5
    b.inputs['Subsurface Radius'].default_value = (0.4, 0.6, 1.0)
    b.inputs['Subsurface Scale'].default_value = 0.01
    for k, v in (('use_raytrace_refraction', True), ('surface_render_method', 'DITHERED')):
        if hasattr(m, k):
            setattr(m, k, v)
    return m



def plinth(L, W, H, chunk, prod, hmax, turn, seed=7):
    ob = sklib._mesh_obj('A-PROD-PLINTH', slab_mesh(L, W, H, seed), parent=turn)
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=35 * sklib.D2R)
    ob.data.materials.append(ice_slab_mat())
    ice_bed(L, W, chunk, prod, hmax, turn, seed)
    return ob


def ice_bed(L, W, chunk, prod, hmax, turn, seed):
    """Crushed-ice bed on the slab that rises to meet the product's underside (product rests on ice, never floats):
    height field T(x,y) = lowest product surface above (x,y) (ray cast up), capped at hmax, falling off around the
    footprint at the angle of repose; every chunk vertex is kept below the product surface above it (no clipping)."""
    from mathutils import Euler, Matrix
    from mathutils.bvhtree import BVHTree
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in prod:
        b2 = bmesh.new(); b2.from_object(o, dg); b2.transform(o.matrix_world)
        me = bpy.data.meshes.new('t'); b2.to_mesh(me); b2.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    tree = BVHTree.FromBMesh(bm); bm.free()
    up = Vector((0, 0, 1))

    def zf(x, y):
        h = tree.ray_cast(Vector((x, y, -1.0)), up)
        return h[0].z if h[0] else 1e9
    cell = chunk * 0.7
    nx, ny = int(L / cell) + 1, int(W / cell) + 1
    Z = np.array([[zf(-L / 2 + i * cell, -W / 2 + j * cell) for j in range(ny)] for i in range(nx)])
    T = np.where(Z < 1e8, np.minimum(Z, hmax), -1.0)
    slope = math.tan(38 * sklib.D2R) * cell
    for _ in range(int(hmax / slope) + 2):          # angle-of-repose falloff around the footprint
        P = np.pad(T, 1, constant_values=-1.0)
        T = np.maximum.reduce([T, P[:-2, 1:-1] - slope, P[2:, 1:-1] - slope, P[1:-1, :-2] - slope, P[1:-1, 2:] - slope])
    T = np.minimum(np.maximum(T, chunk * 0.6), Z)
    edge = chunk * 2.5
    rng = random.Random(seed)
    protos = []
    for k in range(8):
        b = bmesh.new()
        bmesh.ops.create_icosphere(b, subdivisions=1, radius=1.0)
        for v in b.verts:
            v.co *= rng.uniform(0.8, 1.12)
        bmesh.ops.scale(b, vec=(rng.uniform(0.9, 1.4), rng.uniform(0.7, 1.1), rng.uniform(0.45, 0.8)), verts=b.verts[:])
        protos.append(([v.co.copy() for v in b.verts], [[v.index for v in f.verts] for f in b.faces]))
        b.free()
    n = int((L - 2 * edge) * (W - 2 * edge) / (1.25 * chunk) ** 2 * 2.6)
    out = bmesh.new()
    for i in range(n):
        x, y = rng.uniform(-L / 2 + edge, L / 2 - edge), rng.uniform(-W / 2 + edge, W / 2 - edge)
        t = T[min(nx - 1, int(round((x + L / 2) / cell))), min(ny - 1, int(round((y + W / 2) / cell)))]
        sc = chunk * rng.uniform(0.5, 1.3)
        z = t - rng.uniform(0.0, min(t, 2.5 * chunk)) - sc * 0.35
        M = Matrix.Translation((x, y, z)) @ Euler([rng.uniform(0, 6.3) for _ in range(3)]).to_matrix().to_4x4() @ \
            Matrix.Diagonal((sc, sc, sc, 1))
        vs, fs = protos[i % len(protos)]
        pts = [M @ c for c in vs]
        over = max(p.z - (zf(p.x, p.y) - chunk * 0.04) for p in pts)
        if over > 0:
            pts = [p - Vector((0, 0, over)) for p in pts]
        nv = [out.verts.new(p) for p in pts]
        for f in fs:
            out.faces.new([nv[j] for j in f])
    ob = sklib._mesh_obj('A-ICE-CRUSHED', out, parent=turn)
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=45 * sklib.D2R)
    ob.data.materials.append(chunk_mat())
    return ob


# -------------------------------------------------------------------------------------------------- studio sweep
def sweep(S, floor_z, mat):
    """Seamless cyclorama: floor (toward camera) curving up into a back wall."""
    bm = bmesh.new()
    prof = [(-9 * S, 0.0)] + [(1.6 * S + 2.2 * S * math.sin(t * math.pi / 2 / 16), 2.2 * S * (1 - math.cos(t * math.pi / 2 / 16)))
                              for t in range(17)] + [(3.8 * S, 7 * S)]
    row = []
    for x in (-9 * S, 9 * S):
        row.append([bm.verts.new((x, y, floor_z + z)) for y, z in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((row[0][i], row[1][i], row[1][i + 1], row[0][i + 1]))
    ob = sklib._mesh_obj('STUDIO-SWEEP', bm)
    ob.data.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def area(name, loc, aim, size, power, color=(1, 1, 1), spread=180):
    d = bpy.data.lights.new(name, 'AREA'); d.shape, d.size, d.energy, d.color = 'DISK', size, power, color
    d.spread = spread * sklib.D2R
    o = sklib.new_obj(name, d, loc=loc)
    o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


# ----------------------------------------------------------------------------------------------- Zoi navy studio
def tint_world(w, hexc):
    """Keep the HDRI's reflections (silver skin needs them) but shift them to the row's world hue."""
    nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    env = bg.inputs['Color'].links[0].from_node
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = 1.0
    c = look.hex_rgb(hexc); m = max(c)
    a = [x for x in mx.inputs if x.name == 'A' and x.type == 'RGBA'][0]
    b = [x for x in mx.inputs if x.name == 'B' and x.type == 'RGBA'][0]
    nt.links.new(env.outputs[0], a)
    b.default_value = (*[1.0 * x / m for x in c], 1)          # hue of #0b1424 at a usable level
    nt.links.new([x for x in mx.outputs if x.type == 'RGBA'][0], bg.inputs['Color'])


def navy_mat(S):
    """Navy #0f1d33 sweep with large soft hue/value drift (deeper toward the edges, bluer patches) + fine paper noise."""
    m, nt = sklib._new_mat('studio_navy')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -800, 0)
    big = _noise(nt, tc.outputs['Object'], 0.35 / S, 2.0, 0.5, -600, 150)
    fine = _noise(nt, tc.outputs['Object'], 40.0 / S, 6.0, 0.6, -600, -150)
    nav = look.hex_rgb('#0f1d33'); deep = look.hex_rgb('#0b1424'); blu = look.hex_rgb('#1a3358')
    nav, deep, blu = [tuple(0.7 * x for x in c) for c in (nav, deep, blu)]   # lit floor reads as #0f1d33-ish
    c1 = _mix(nt, _maprange(nt, big.outputs['Fac'], 0.35, 0.65, 0, 1, -350, 150), deep, nav, 'MIX', -100, 200)
    c2 = _mix(nt, _maprange(nt, big.outputs['Fac'], 0.55, 0.75, 0, 0.6, -350, 0), (0, 0, 0), blu, 'MIX', -100, 0)
    mx = _n(nt, 'ShaderNodeMix', 150, 150); mx.data_type = 'RGBA'; mx.blend_type = 'ADD'
    mx.inputs[0].default_value = 1.0
    _l(nt, c1, [x for x in mx.inputs if x.name == 'A' and x.type == 'RGBA'][0])
    _l(nt, c2, [x for x in mx.inputs if x.name == 'B' and x.type == 'RGBA'][0])
    vm = _n(nt, 'ShaderNodeVectorMath', 350, 150, operation='SCALE')
    _l(nt, [x for x in mx.outputs if x.type == 'RGBA'][0], vm.inputs[0])
    _l(nt, _maprange(nt, fine.outputs['Fac'], 0.3, 0.7, 0.92, 1.08, 150, -150), vm.inputs['Scale'])
    _l(nt, vm.outputs[0], b.inputs['Base Color'])
    _l(nt, _maprange(nt, fine.outputs['Fac'], 0.3, 0.7, 0.72, 0.88, 350, -150), b.inputs['Roughness'])
    b.inputs['Specular IOR Level'].default_value = 0.25          # matte paper sweep: no bright grazing sheen
    return m


def glow_mat(name, hexc, strength, fz, fade):
    """Additive soft disc (out-of-focus light): transparent + emission with a smooth radial falloff."""
    m, nt = sklib._new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -700, 0)
    g = _n(nt, 'ShaderNodeTexGradient', -500, 0); g.gradient_type = 'SPHERICAL'
    _l(nt, tc.outputs['Object'], g.inputs['Vector'])
    f = _n(nt, 'ShaderNodeMath', -300, 0, operation='POWER'); f.inputs[1].default_value = 2.2
    _l(nt, g.outputs['Fac'], f.inputs[0])
    geo = _n(nt, 'ShaderNodeNewGeometry', -700, -300)       # fade out toward the floor: no hard line where the sweep cuts the disc
    sx = _n(nt, 'ShaderNodeSeparateXYZ', -500, -300)
    _l(nt, geo.outputs['Position'], sx.inputs[0])
    hf = _n(nt, 'ShaderNodeMapRange', -300, -300); hf.interpolation_type = 'SMOOTHERSTEP'
    hf.inputs['From Min'].default_value, hf.inputs['From Max'].default_value = fz, fz + fade
    _l(nt, sx.outputs['Z'], hf.inputs['Value'])
    fm = _n(nt, 'ShaderNodeMath', -150, -200, operation='MULTIPLY')
    _l(nt, f.outputs[0], fm.inputs[0]); _l(nt, hf.outputs['Result'], fm.inputs[1])
    f = fm
    e = _n(nt, 'ShaderNodeEmission', 0, 100)
    e.inputs['Color'].default_value = (*look.hex_rgb(hexc), 1)
    st = _n(nt, 'ShaderNodeMath', -100, -100, operation='MULTIPLY'); st.inputs[1].default_value = strength
    _l(nt, f.outputs[0], st.inputs[0]); _l(nt, st.outputs[0], e.inputs['Strength'])
    tr = _n(nt, 'ShaderNodeBsdfTransparent', 0, -100)
    ad = _n(nt, 'ShaderNodeAddShader', 400, 0)
    _l(nt, tr.outputs[0], ad.inputs[0]); _l(nt, e.outputs[0], ad.inputs[1]); _l(nt, ad.outputs[0], out.inputs['Surface'])
    for k, v in (('surface_render_method', 'BLENDED'), ('use_transparent_shadow', True)):
        if hasattr(m, k):
            setattr(m, k, v)
    return m


# (u, v) in [-1, 1] screen coords, radius as a fraction of frame half-height. Top-left third stays calm (type zone).
GLOWS = [(0.10, 0.30, 0.95, '#9fd8ff', 1.4), (0.62, 0.10, 0.65, '#3a5b8c', 2.0), (-0.55, 0.05, 0.60, '#3a5b8c', 1.6),
         (0.40, 0.42, 0.22, '#9fe3ff', 2.2), (-0.18, 0.38, 0.12, '#9fd8ff', 2.0), (0.82, 0.14, 0.16, '#e2a03a', 1.4),
         (0.70, 0.24, 0.06, '#e2a03a', 1.8)]


def glows(s, cam, near, fz, fade):
    """Soft discs just in front of the backdrop, placed through the camera so they sit behind the product in frame."""
    bpy.context.view_layer.update()
    M = cam.matrix_world; o = M.translation
    fwd, rt, up = -M.col[2].xyz, M.col[0].xyz, M.col[1].xyz
    tx = 18.0 / cam.data.lens; ty = tx * 9 / 16
    sw = bpy.data.objects['STUDIO-SWEEP']
    for i, (u, v, r, hexc, st) in enumerate(GLOWS):
        mi = sw.matrix_world.inverted()                      # hit the backdrop only, never the product
        d = (fwd + rt * u * tx + up * v * ty).normalized()
        h, lc, *_ = sw.ray_cast(mi @ o, (mi.to_3x3() @ d).normalized())
        depth = ((sw.matrix_world @ lc - o).length if h else 50.0) * 0.9
        depth = max(depth, near)                             # always behind the product
        p = o + d * depth
        me = bpy.data.meshes.new('GLOW'); bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=1.0); bm.to_mesh(me); bm.free()
        ob = sklib.new_obj('GLOW-%d' % i, me, loc=p)
        ob.rotation_euler = (o - p).to_track_quat('Z', 'Y').to_euler()
        ob.scale = [r * depth * ty * fwd.dot(d)] * 3
        ob.data.materials.append(glow_mat('glow_%d' % i, hexc, st, fz, fade))
        ob.visible_shadow = False
        for a in ('visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter'):
            if hasattr(ob, a):
                setattr(ob, a, False)


# ----------------------------------------------------------------------------------------------------------- build
def build(name):
    s = sklib.reset()
    bpy.ops.import_scene.gltf(filepath=sklib.SRC + '/models/%s.glb' % name)
    prod = [o for o in s.objects if o.type == 'MESH']
    bpy.context.view_layer.update()
    lo, hi = bbox(prod)
    Lp, Hp = hi.x - lo.x, hi.z - lo.z
    S = Lp / 1.19                                     # scene scale relative to the tuna
    turn = sklib.new_obj('TURN', None)
    for o in s.objects:
        if o.parent is None and o is not turn:
            o.parent = turn
            o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))   # rest exactly on the slab top z=0
    kx, ky = Lp / 2, (hi.y - lo.y) / 2
    L, W, H = Lp + 0.32 * S, 2 * ky + 0.26 * S, 0.13 * S
    plinth(L, W, H, 0.02 * S, prod, 0.45 * Hp, turn)

    # one linear 360 deg turn: f1 = 0 deg, f121 = 360 deg (= f1) -> 120 unique frames that loop
    turn.rotation_euler = (0, 0, 0); turn.keyframe_insert('rotation_euler', index=2, frame=1)
    turn.rotation_euler = (0, 0, 2 * math.pi); turn.keyframe_insert('rotation_euler', index=2, frame=121)
    for fc in sklib._fcurves(turn):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'

    # Zoi studio (COLOR_SCRIPT row P): navy field, 5600 K softbox key, #3a5b8c fill, #9fe3ff ice rim, world #0b1424
    w = sklib.hdri('studio_small_09', res='2k', strength=0.35, rot_deg=40)
    tint_world(w, '#0b1424')
    sweep(S, -H, navy_mat(S))
    k = S * S
    area('KEY', (-1.7 * S, -1.5 * S, 1.9 * S), (0, 0, Hp * 0.3), 1.6 * S, 300 * k, sklib.kelvin_rgb(5600), 55)
    area('FILL', (2.2 * S, -1.8 * S, 0.7 * S), (0, 0, Hp * 0.3), 2.0 * S, 90 * k, look.hex_rgb('#3a5b8c'))
    area('RIM', (1.0 * S, 1.6 * S, 1.4 * S), (0, 0, Hp * 0.4), 0.9 * S, 260 * k, look.hex_rgb('#9fe3ff'))
    area('RIM2', (-1.3 * S, 1.4 * S, 0.5 * S), (0, 0, 0), 0.7 * S, 200 * k, look.hex_rgb('#9fe3ff'), 70)  # low ice rim on the slab
    area('WASH', (0, 1.0 * S, 1.8 * S), (0, 3.6 * S, 0.9 * S), 2.0 * S, 110 * k, look.hex_rgb('#3a5b8c'), 90)

    # camera: product ~55 % of frame width, centred (mobile crop keeps the middle of the body), 14 deg down
    lens, el = 50.0, 16 * sklib.D2R
    dist = Lp / (0.55 * 36 / lens)
    tgt = Vector((0, 0, Hp * 0.42))
    cam = sklib.camera('CAM', lens, tgt + Vector((0, -dist * math.cos(el), dist * math.sin(el))), tgt)
    sklib.dof(cam, dist, 14.0 / S)
    glows(s, cam, dist + 0.6 * Lp, -H, 0.45 * S)
    sklib.finish('prod-' + name, 'ext')
    # product turntable: short shutter so the near end of the slab stays crisp at 3 deg/frame, then re-save
    s.render.motion_blur_shutter = 0.15
    look.apply(s, 'prod-' + name)
    look.grade(s, lift='#3a5b8c', gain='#ffe9d2', sat=1.10, lift_amt=0.012, gain_amt=0.025)   # §3 complementary: cool navy/fill lift, warm-neutral key gain (true product colour)
    bpy.ops.wm.save_mainfile(compress=True)
    return s


for nm in WHICH:
    sc = build(nm)
    if TAG:
        import os
        d = '%s/blender/stills/prod-%s' % (sklib.SRC, nm); os.makedirs(d, exist_ok=True)
        for f in (1, 12, 40, 60, 108, 120):
            sklib.render_still('%s/%s-%04d.png' % (d, TAG, f), frame=f, res=(1920, 1080))
