"""Skylark v4 product GLBs (B2 products): tuna, prawn, swordfish. Re-runnable from scratch.
  Blender --factory-startup -b --python assets-src/blender/build/products.py -- <tuna|prawn|swordfish>
Writes assets-src/models/<name>.glb (Z-up scene exported +Y up, metres, centred, longest axis X, resting on y=0);
then run scripts/optimize-glb.sh <name>.  Scan sources/licences: docs/ASSETS.md, assets-src/tex/LICENSES.tsv."""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

REPO = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4'
SCANS = REPO + '/assets-src/scans'
MODELS = REPO + '/assets-src/models'
WORK = '/tmp/claude-501/sk/prod'
os.makedirs(WORK, exist_ok=True)

SCAN = {  # file, real total length (m), rotation to put head at -X / back up
    'tuna': ('yellowfin-tuna.glb', 1.20),
    'prawn': ('green-tiger-prawn.glb', 0.25),
    'prawn_alt': ('tiger-prawn-aniljaco.glb', 0.25),
}


def bbox(ob):
    co = np.empty(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    return co.min(0), co.max(0)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load_scan(which, drop_checker=True):
    """Import a scan, drop the colour-checker cube (its own object, material 'Material.001'), join, apply transforms,
    scale to real length, longest axis X, centred on X/Y, belly on z=0."""
    fn, length = SCAN[which]
    reset()
    bpy.ops.import_scene.gltf(filepath=SCANS + '/' + fn)
    s = bpy.context.scene
    meshes = [o for o in s.objects if o.type == 'MESH']
    for o in meshes:
        if drop_checker and len(o.data.vertices) <= 24 and o.data.materials and o.data.materials[0].name.startswith('Material'):
            bpy.data.objects.remove(o)
    meshes = [o for o in s.objects if o.type == 'MESH']
    for o in s.objects:
        o.select_set(o.type == 'MESH')
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in list(s.objects):
        if o.type != 'MESH':
            bpy.data.objects.remove(o)
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = 'SCAN_' + which
    lo, hi = bbox(ob)
    d = hi - lo
    ax = int(np.argmax(d))
    if ax == 1:
        ob.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))
    elif ax == 2:
        ob.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Y'))
    lo, hi = bbox(ob)
    k = length / (hi - lo)[0]
    c = (lo + hi) / 2
    ob.data.transform(Matrix.Scale(k, 4) @ Matrix.Translation(Vector((-c[0], -c[1], -lo[2]))))
    ob.data.update()
    simple_scan_materials(ob)
    return ob


def simple_scan_materials(ob):
    """Scans may come unlit / with odd node trees: rebuild every slot as Principled(base colour = its image)."""
    for m in ob.data.materials:
        imgs = [n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
        bs.name = 'Principled BSDF'
        nt.links.new(bs.outputs[0], out.inputs[0])
        if imgs:
            t = nt.nodes.new('ShaderNodeTexImage')
            t.image = imgs[0]
            nt.links.new(t.outputs['Color'], bs.inputs['Base Color'])
            if len(imgs) > 1:
                print('  material %s: %d images, using %s' % (m.name, len(imgs), imgs[0].name))


# ------------------------------------------------------------------------------------------- 2-D raster helpers (numpy)
def _box(a, r, axis):
    if r < 1:
        return a
    c = np.cumsum(np.pad(a, [(r + 1, r) if i == axis else (0, 0) for i in range(a.ndim)], mode='edge'), axis=axis)
    hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
    lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
    return (hi - lo) / (2 * r + 1)


def blur(a, sigma_px):
    """~gaussian = 3 box passes per axis."""
    r = max(0, int(round(sigma_px * 0.85)))
    a = a.astype(np.float64)
    for _ in range(3):
        a = _box(_box(a, r, 0), r, 1)
    return a


def dilate(m, r):
    if r < 1:
        return m.copy()
    out = m.copy()
    H, W = m.shape
    p = np.pad(m, r)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= p[r + dy:r + dy + H, r + dx:r + dx + W]
    return out


def erode(m, r):
    return ~dilate(~m, r)


def fill_holes(m):
    """Flood the outside from the border; whatever is not reached and not in m is a hole."""
    H, W = m.shape
    out = np.zeros((H + 2, W + 2), bool)
    free = ~np.pad(m, 1)
    out[0, :] = out[-1, :] = True
    out[:, 0] = out[:, -1] = True
    out &= free
    while True:
        g = out.copy()
        g[1:, :] |= out[:-1, :]
        g[:-1, :] |= out[1:, :]
        g[:, 1:] |= out[:, :-1]
        g[:, :-1] |= out[:, 1:]
        g &= free
        if (g == out).all():
            break
        out = g
    return ~out[1:-1, 1:-1]


def label(m):
    """4-connected components -> int array (0 = background)."""
    lab = np.zeros(m.shape, np.int32)
    H, W = m.shape
    n = 0
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]:
            continue
        n += 1
        st = [(y0, x0)]
        lab[y0, x0] = n
        while st:
            y, x = st.pop()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    st.append((yy, xx))
    return lab, n


class Raster:
    """Axis-aligned 2-D grid over coordinates (a, b) with pixel size px."""

    def __init__(self, a, b, px, pad=0.02):
        self.px = px
        self.a0, self.b0 = a.min() - pad, b.min() - pad
        self.W = int((a.max() + pad - self.a0) / px) + 1
        self.H = int((b.max() + pad - self.b0) / px) + 1

    def ij(self, a, b):
        i = np.clip(((b - self.b0) / self.px).astype(int), 0, self.H - 1)
        j = np.clip(((a - self.a0) / self.px).astype(int), 0, self.W - 1)
        return i, j

    def minmax(self, a, b, c):
        i, j = self.ij(a, b)
        lo = np.full((self.H, self.W), np.inf)
        hi = np.full((self.H, self.W), -np.inf)
        np.minimum.at(lo, (i, j), c)
        np.maximum.at(hi, (i, j), c)
        return lo, hi

    def occ(self, a, b):
        m = np.zeros((self.H, self.W), bool)
        m[self.ij(a, b)] = True
        return m


def mesh_points(ob):
    """vertices + face centres (denser sampling for rasters)."""
    me = ob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    fc = np.empty(len(me.polygons) * 3)
    me.polygons.foreach_get('center', fc)
    return co, fc.reshape(-1, 3)


def flatten_edge(R, m, x0, x1, bottom=True):
    """Within columns x0..x1 (metres), replace the silhouette's bottom (or top) edge by the straight line between the
    edge heights just outside the range and clear what lies beyond it (removes paired fins that read as 'thick')."""
    j0, j1 = R.ij(np.array([x0, x1]), np.array([R.b0, R.b0]))[1]
    def edge(j):
        rows = np.nonzero(m[:, j])[0]
        return (rows.min() if bottom else rows.max()) if len(rows) else None
    e0, e1 = edge(j0), edge(j1)
    for j in range(j0, j1 + 1):
        e = e0 + (e1 - e0) * (j - j0) / max(1, j1 - j0)
        if bottom:
            m[:int(e), j] = False
        else:
            m[int(e) + 1:, j] = False
    return m


def body_masks(ob, px=0.0015, thick=0.012, flatten=()):
    """Side (x,z) and top (x,y) silhouettes of the fleshy body: pixels where the scan is thicker than `thick`
    across the view direction. Fins (thin sheets) fall outside both."""
    co, fc = mesh_points(ob)
    P = np.vstack([co, fc])
    out = {}
    for name, (a, b, c) in {'side': (0, 2, 1), 'top': (0, 1, 2)}.items():
        R = Raster(P[:, a], P[:, b], px)
        lo, hi = R.minmax(P[:, a], P[:, b], P[:, c])
        t = np.where(np.isfinite(lo), hi - lo, 0)
        m = t > thick
        m = erode(dilate(m, 3), 3)
        m = fill_holes(m)
        lab, n = label(m)
        if n > 1:
            sizes = np.bincount(lab.ravel())
            sizes[0] = 0
            m = lab == int(np.argmax(sizes))
        if name == 'side':
            for x0, x1, bottom in flatten:
                m = flatten_edge(R, m, x0, x1, bottom)
        m = blur(m, 2) > 0.5
        out[name] = (R, m, (a, b))
    return out


def in_body(masks, P, grow_px=1):
    ok = np.ones(len(P), bool)
    for name, (R, m, (a, b)) in masks.items():
        mm = dilate(m, grow_px) if grow_px else m
        ok &= mm[R.ij(P[:, a], P[:, b])]
    return ok


# --------------------------------------------------------------------------------------------------- debug previews
def preview(path, views=('side', 'q', 'top'), res=(960, 540), focus=None, span=None, samples=16):
    """Quick EEVEE stills of the current scene (call under assets-src/tools/render-lock.sh)."""
    sys.path.insert(0, REPO + '/assets-src/blender/lib')
    import sklib
    s = bpy.context.scene
    if not s.world or 'SK_HDRI' not in s.world.name:
        sklib.hdri('studio_small_09', res='2k')
    sklib.render_settings('ext', s)
    s.render.use_motion_blur = False
    pts = [o.matrix_world @ Vector(c) for o in s.objects if o.type == 'MESH' and not o.hide_render for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    ctr = Vector(focus) if focus else (lo + hi) / 2
    L = span or max(hi - lo) * 1.1
    cd = bpy.data.cameras.get('PV') or bpy.data.cameras.new('PV')
    cam = bpy.data.objects.get('PV') or bpy.data.objects.new('PV', cd)
    if cam.name not in s.collection.objects:
        s.collection.objects.link(cam)
    s.camera = cam
    cd.lens = 85
    cd.clip_start, cd.clip_end = 0.01, 100
    dist = L / 2 / math.tan(math.atan(18 / 85)) * 1.0
    dirs = {'side': (0, -1, 0.08), 'q': (0.6, -0.8, 0.45), 'top': (0, -0.02, 1), 'front': (-1, 0, 0.1),
            'back': (1, 0, 0.15), 'other': (0, 1, 0.1), 'qb': (-0.6, 0.8, 0.35), 'under': (0.2, -0.4, -1)}
    for v in views:
        d = Vector(dirs[v]).normalized()
        cam.location = ctr + d * dist
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sklib.render_still('%s-%s.png' % (path, v), res=res, samples=samples)


# ------------------------------------------------------------------------------------------------ body + fin rebuild
def keep_largest(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen = np.zeros(len(bm.verts), bool)
    best = []
    for v in bm.verts:
        if seen[v.index]:
            continue
        st, ids = [v], []
        seen[v.index] = True
        while st:
            x = st.pop()
            ids.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if not seen[y.index]:
                    seen[y.index] = True
                    st.append(y)
        if len(ids) > len(best):
            best = ids
    keep = np.zeros(len(bm.verts), bool)
    keep[best] = True
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()


def select_only(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def body_lowpoly(scan, keep_mask, voxel=0.0025, tris=20000, name='BODY'):
    """Voxel-remesh the fleshy part of the scan (fins removed) into one closed manifold skin, drop floating specks,
    decimate. Thin fins never survive this, so they are rebuilt separately (fin_sheet)."""
    ob = scan.copy()
    ob.data = scan.data.copy()
    ob.name = name
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(~keep_mask)[0]], context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    select_only(ob)
    ob.data.remesh_voxel_size = voxel
    ob.data.remesh_voxel_adaptivity = 0.0
    bpy.ops.object.voxel_remesh()
    keep_largest(ob)
    sm = ob.modifiers.new('smooth', 'CORRECTIVE_SMOOTH')
    sm.iterations, sm.factor, sm.use_only_smooth = 3, 0.5, True
    bpy.ops.object.modifier_apply(modifier=sm.name)
    n = len(ob.data.polygons)
    if n > tris:
        d = ob.modifiers.new('dec', 'DECIMATE')
        d.ratio = tris / n
        d.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=d.name)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def appendage_groups(co, body, px=0.002, min_pts=400, mid=0.015):
    """Cluster the non-body scan vertices (fins, specks) by their side-view footprint; split paired fins by side."""
    A = np.nonzero(~body)[0]
    R = Raster(co[A, 0], co[A, 2], px)
    occ = erode(dilate(R.occ(co[A, 0], co[A, 2]), 2), 1)
    lab, n = label(occ)
    li = lab[R.ij(co[A, 0], co[A, 2])]
    groups = []
    for k in range(1, n + 1):
        idx = A[li == k]
        if len(idx) < min_pts:
            continue
        y = co[idx, 1]
        if np.mean(np.abs(y)) > mid:
            for sgn in (-1, 1):
                sub = idx[np.sign(y) == sgn]
                if len(sub) >= min_pts:
                    groups.append(sub)
        else:
            groups.append(idx)
    return groups


def _bilinear(f, x, y):
    H, W = f.shape
    x = np.clip(x, 0, W - 1.001)
    y = np.clip(y, 0, H - 1.001)
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = x - x0, y - y0
    return (f[y0, x0] * (1 - fx) * (1 - fy) + f[y0, x0 + 1] * fx * (1 - fy) +
            f[y0 + 1, x0] * (1 - fx) * fy + f[y0 + 1, x0 + 1] * fx * fy)


def fin_sheet(name, pts, masks=None, px=0.0008, close=0.003, open_=0.002, sigma=0.0025, thr=0.5, base_ext=0.008,
              cell=0.003, tmax=0.0022, tmin=0.0005, normal=None):
    """A clean, solid fin rebuilt from the scan points of a ragged fin:
    plane fit -> 2-D occupancy -> close (bridge frayed rays) / fill / open (cut spikes) -> extend the base into the body
    -> gaussian field -> grid mesh whose rim is snapped onto the smooth iso-line. Stores the thickness weight in the
    'fin_w' attribute (1 at the root, 0 at the rim) for solidify_fins(). UV = planar (normalised later by packing)."""
    c = pts.mean(0)
    if normal is None:
        normal = np.linalg.svd(pts - c, full_matrices=False)[2][2]
    n = np.asarray(normal, float)
    n /= np.linalg.norm(n)
    X = np.array([1.0, 0, 0])
    u = X - n * n.dot(X)
    if np.linalg.norm(u) < 0.3:
        u = np.array([0, 0, 1.0]) - n * n[2]
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    a, b = (pts - c) @ u, (pts - c) @ v
    R = Raster(a, b, px, pad=base_ext + 0.012)
    r = lambda d: max(1, int(round(d / px)))
    m = R.occ(a, b)
    m = erode(dilate(m, r(close)), r(close))
    m = fill_holes(m)
    m = dilate(erode(m, r(open_)), r(open_))
    lab, k = label(m)
    if k > 1:
        sz = np.bincount(lab.ravel())
        sz[0] = 0
        m = lab == int(np.argmax(sz))
    if masks is not None and base_ext > 0:
        jj, ii = np.meshgrid(np.arange(R.W), np.arange(R.H))
        A = R.a0 + (jj.ravel() + 0.5) * px
        B = R.b0 + (ii.ravel() + 0.5) * px
        P3 = c + np.outer(A, u) + np.outer(B, v)
        inb = in_body(masks, P3, 0).reshape(R.H, R.W)
        m = m | (dilate(m, r(base_ext)) & inb)
    f = blur(m.astype(float), sigma / px)
    # grid mesh over the field
    step = cell / px
    gx = np.arange(0, R.W, step)
    gy = np.arange(0, R.H, step)
    GX, GY = np.meshgrid(gx, gy)
    FV = _bilinear(f, GX, GY)
    inside_c = _bilinear(f, GX[:-1, :-1] + step / 2, GY[:-1, :-1] + step / 2) > thr
    bm = bmesh.new()
    vid = -np.ones(GX.shape, int)
    verts = []
    for i, j in zip(*np.nonzero(inside_c)):
        for (yy, xx) in ((i, j), (i, j + 1), (i + 1, j), (i + 1, j + 1)):
            if vid[yy, xx] < 0:
                vid[yy, xx] = len(verts)
                verts.append(bm.verts.new((GX[yy, xx], GY[yy, xx], 0)))
    bm.verts.ensure_lookup_table()
    for i, j in zip(*np.nonzero(inside_c)):
        bm.faces.new([verts[vid[i, j]], verts[vid[i, j + 1]], verts[vid[i + 1, j + 1]], verts[vid[i + 1, j]]])
    # snap the rim onto the iso-line, then relax
    gyf, gxf = np.gradient(f)
    for it in range(12):
        rim = [vv for vv in bm.verts if vv.is_boundary]
        for vv in rim:
            x, y = vv.co.x, vv.co.y
            val = _bilinear(f, np.array([x]), np.array([y]))[0] - thr
            gx_, gy_ = _bilinear(gxf, np.array([x]), np.array([y]))[0], _bilinear(gyf, np.array([x]), np.array([y]))[0]
            g2 = gx_ * gx_ + gy_ * gy_ + 1e-9
            d = np.clip(-val * np.array([gx_, gy_]) / g2, -step * 0.6, step * 0.6)
            vv.co.x += d[0]
            vv.co.y += d[1]
        if it < 10:
            new = {}
            for vv in rim:
                nb = [e.other_vert(vv) for e in vv.link_edges if e.is_boundary]
                if len(nb) == 2:
                    new[vv] = (vv.co * 0.5 + (nb[0].co + nb[1].co) * 0.25)
            for vv, co_ in new.items():
                vv.co = co_
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=step * 0.25)
    bmesh.ops.dissolve_degenerate(bm, dist=step * 0.05, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    # thickness weight from the field, UV, 3-D placement
    fw = bm.verts.layers.float.new('fin_w')
    uvl = bm.loops.layers.uv.new('UVMap')
    for vv in bm.verts:
        val = _bilinear(f, np.array([vv.co.x]), np.array([vv.co.y]))[0]
        vv[fw] = float(np.clip((val - thr) / (1 - thr) * 2.2, 0, 1)) ** 0.6
    span = max(R.W, R.H)
    for fa in bm.faces:
        for lp in fa.loops:
            lp[uvl].uv = (lp.vert.co.x / span, lp.vert.co.y / span)
    for vv in bm.verts:
        A_ = R.a0 + (vv.co.x + 0.5) * px
        B_ = R.b0 + (vv.co.y + 0.5) * px
        vv.co = Vector(c + A_ * u + B_ * v)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob['tmax'], ob['tmin'] = tmax, tmin
    ob['normal'] = list(n)
    return ob


def solidify_fins(ob, part_attr='part'):
    """Give every fin face (part > 0) real thickness, tapered by 'fin_w': extrude the sheet along its normal,
    keep the original as the other side, close the rim."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    fw = bm.verts.layers.float.get('fin_w')
    pl = bm.faces.layers.int.get(part_attr)
    tmax = ob.get('fin_tmax', {})
    parts = sorted({f[pl] for f in bm.faces if f[pl] > 0})
    for k in parts:
        faces = [f for f in bm.faces if f[pl] == k]
        tx, tn = tmax.get(str(k), (0.002, 0.0005))
        nrm = Vector((0, 0, 0))
        for f in faces:
            nrm += f.normal * f.calc_area()
        nrm.normalize()
        orig = {v for f in faces for v in f.verts}
        ret = bmesh.ops.extrude_face_region(bm, geom=faces, use_keep_orig=True)
        newv = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        uvl = bm.loops.layers.uv.get('UVMap')
        if uvl is not None:     # detach the second side's UVs so it gets its own island (two-sided bake)
            for f in ret['geom']:
                if isinstance(f, bmesh.types.BMFace) and all(v in set(newv) for v in f.verts):
                    for lp in f.loops:
                        lp[uvl].uv.x += 1.5
        for v in newv:
            v.co += nrm * (tn + (tx - tn) * v[fw]) * 0.5
        for v in orig:
            v.co -= nrm * (tn + (tx - tn) * v[fw]) * 0.5
        bmesh.ops.reverse_faces(bm, faces=faces)
    bm.normal_update()
    bm.to_mesh(ob.data)
    bm.free()


def assign_groups(co, groups, seeds, radius=0.045):
    """Name each appendage group by the nearest seed (x, z) -> {'name': idx array}; unmatched groups are dropped
    (specks, the stringy first-dorsal spike)."""
    out = {}
    for g in groups:
        c = co[g].mean(0)
        best, bd = None, radius
        for name, (x, z) in seeds.items():
            d = math.hypot(c[0] - x, c[2] - z)
            if d < bd:
                best, bd = name, d
        if best is None:
            print('  drop group n=%d at %s' % (len(g), c.round(3)))
            continue
        key = best
        if best in ('pelvic', 'pectoral'):
            key = '%s_%s' % (best, 'L' if c[1] > 0 else 'R')
        out[key] = np.concatenate([out[key], g]) if key in out else g
    return out


# ------------------------------------------------------------------------------------------------------- baking
def _img(name, size, data=False, color=(0, 0, 0, 1)):
    im = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False, is_data=data)
    im.generated_color = color
    return im


def bake(src_objs, target, img, kind='DIFFUSE', extrusion=0.006, max_dist=0.02, margin=8):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = 1
    s.cycles.device = 'CPU'
    mat = target.data.materials[0]
    nt = mat.node_tree
    node = nt.nodes.get('BAKE_TARGET') or nt.nodes.new('ShaderNodeTexImage')
    node.name = 'BAKE_TARGET'
    node.image = img
    nt.nodes.active = node
    select_only(*src_objs, target)
    b = s.render.bake
    b.use_selected_to_active, b.cage_extrusion, b.max_ray_distance, b.margin = True, extrusion, max_dist, margin
    b.use_clear = True
    if kind == 'DIFFUSE':
        b.use_pass_direct = b.use_pass_indirect = False
        b.use_pass_color = True
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
    else:
        bpy.ops.object.bake(type=kind)
    return img


def img_np(img):
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def np_img(img, a):
    img.pixels.foreach_set(a.astype(np.float32).ravel())
    img.update()


def push_pull_fill(rgb, known):
    """Fill unknown pixels from known ones (pyramid push-pull, like texture dilation but smooth)."""
    if known.all() or not known.any():
        return rgb
    H, W = known.shape
    if min(H, W) <= 2:
        m = rgb[known].mean(0)
        out = rgb.copy()
        out[~known] = m
        return out
    w = known.astype(np.float64)
    h2, w2 = (H + 1) // 2, (W + 1) // 2
    pw = np.zeros((h2 * 2, w2 * 2))
    pc = np.zeros((h2 * 2, w2 * 2, rgb.shape[2]))
    pw[:H, :W] = w
    pc[:H, :W] = rgb * w[..., None]
    sw = pw.reshape(h2, 2, w2, 2).sum((1, 3))
    sc = pc.reshape(h2, 2, w2, 2, -1).sum((1, 3))
    small_known = sw > 0
    small = np.where(small_known[..., None], sc / np.maximum(sw, 1e-9)[..., None], 0)
    small = push_pull_fill(small, small_known)
    up = np.repeat(np.repeat(small, 2, 0), 2, 1)[:H, :W]
    up = blur_rgb(up, 1.0)
    out = rgb.copy()
    out[~known] = up[~known]
    return out


def blur_rgb(a, s):
    return np.stack([blur(a[..., i], s) for i in range(a.shape[2])], -1)


def join_parts(parts, name):
    """parts: list of (obj, part_id). Adds face attr 'part', vertex attr 'fin_w', joins into one object."""
    for ob, pid in parts:
        me = ob.data
        if 'part' not in me.attributes:
            me.attributes.new('part', 'INT', 'FACE')
        me.attributes['part'].data.foreach_set('value', np.full(len(me.polygons), pid, np.int32))
        if 'fin_w' not in me.attributes:
            me.attributes.new('fin_w', 'FLOAT', 'POINT')
        if 'UVMap' not in me.uv_layers:
            me.uv_layers.new(name='UVMap')
    select_only(*[o for o, _ in parts[1:]], parts[0][0])
    bpy.context.view_layer.objects.active = parts[0][0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    return ob


def smart_uv(ob, angle=60, margin=0.002):
    select_only(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')


def pack_uv(ob, margin=0.003):
    select_only(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(margin=margin, rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')


def product_material(name, albedo, normal=None, rough=0.38, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes['Principled BSDF']
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = 0.0
    if 'Specular IOR Level' in bs.inputs:
        bs.inputs['Specular IOR Level'].default_value = spec
    if albedo is not None:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = albedo
        t.location = (-500, 300)
        nt.links.new(t.outputs['Color'], bs.inputs['Base Color'])
    if normal is not None:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = normal
        t.image.colorspace_settings.name = 'Non-Color'
        t.location = (-700, -200)
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nm.location = (-300, -200)
        nt.links.new(t.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
    return m


def whiten(objs):
    """Scan materials -> plain white (used to bake a 'hit' mask)."""
    for o in objs:
        for m in o.data.materials:
            bs = m.node_tree.nodes.get('Principled BSDF')
            for l in list(bs.inputs['Base Color'].links):
                m.node_tree.links.remove(l)
            bs.inputs['Base Color'].default_value = (1, 1, 1, 1)


def bake_albedo(scan, target, size=2048, extrusion=0.006, max_dist=0.02):
    col = bake([scan], target, _img(target.name + '_albedo', size), 'DIFFUSE', extrusion, max_dist, margin=0)
    a = img_np(col).copy()
    whiten([scan])
    hit = bake([scan], target, _img(target.name + '_hit', size), 'DIFFUSE', extrusion, max_dist, margin=0)
    known = img_np(hit)[..., 0] > 0.5
    return col, a, known


def clean_fin_texels(rgb, known, finmask, sigma=6, tol=0.18):
    """Fin texels that differ strongly from their neighbourhood (frayed-ray gaps showing the far side, white scan
    fringes) are treated as unknown and refilled, so the rebuilt solid fin reads as one clean membrane."""
    lum = rgb @ np.array([0.3, 0.55, 0.15])
    w = (known & finmask).astype(float)
    loc = blur(lum * w, sigma) / np.maximum(blur(w, sigma), 1e-6)
    bad = finmask & (np.abs(lum - loc) > tol)
    return known & ~dilate(bad, 1), int(bad.sum())


def save_png(img, path):
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()


def remove_blotches(rgb, mask_region=None, sat=0.22, hue_w=0.06, grow=3):
    """Paint out red blood/bruise blotches: strongly red pixels (hue near 0, saturated) are replaced by the
    surrounding skin colour (push-pull fill)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    s = (mx - mn) / np.maximum(mx, 1e-6)
    red = (r == mx) & (s > sat) & (mx > 0.06) & ((g - b) / np.maximum(mx - mn, 1e-6) < hue_w * 6) & (r > g * 1.12)
    if mask_region is not None:
        red &= mask_region
    red = dilate(red, grow)
    out = push_pull_fill(rgb, ~red)
    soft = blur(red.astype(float), 2)[..., None]
    return rgb * (1 - soft) + out * soft, red


# ------------------------------------------------------------------------------------------------------------ tuna
TUNA_SEEDS = [('pelvic', -0.21, 0.04), ('tail', 0.51, 0.18), ('tail', 0.582, 0.025), ('anal', 0.136, 0.071),
              ('pectoral', -0.146, 0.21), ('dfinlets', 0.258, 0.233), ('dorsal2', 0.066, 0.331),
              ('body', -0.594, 0.167), ('body', 0.376, 0.18)]
#           close  open   sigma   cell   tmax    tmin    base_ext
TUNA_FINS = {
    'tail':       (0.004, 0.003, 0.0040, 0.004, 0.0045, 0.0007, 0.010),
    'pectoral':   (0.003, 0.002, 0.0030, 0.004, 0.0030, 0.0006, 0.010),
    'pelvic':     (0.002, 0.0015, 0.0020, 0.003, 0.0025, 0.0005, 0.008),
    'dorsal2':    (0.003, 0.002, 0.0025, 0.003, 0.0035, 0.0006, 0.010),
    'anal':       (0.002, 0.0012, 0.0016, 0.0025, 0.0030, 0.0006, 0.008),
    'dfinlets':   (0.0015, 0.0010, 0.0014, 0.0025, 0.0030, 0.0006, 0.008),
}


def seeds_dict(seeds):
    return seeds


def assign(co, groups, seeds, radius=0.045):
    out = {}
    for g in groups:
        c = co[g].mean(0)
        best, bd = None, radius
        for name, x, z in seeds:
            d = math.hypot(c[0] - x, c[2] - z)
            if d < bd:
                best, bd = name, d
        if best is None:
            print('  drop group n=%d at %s' % (len(g), c.round(3)))
            continue
        key = best
        if best in ('pelvic', 'pectoral'):
            key = '%s_%s' % (best, 'L' if c[1] > 0 else 'R')
        out[key] = np.concatenate([out[key], g]) if key in out else g
    return out


def build_tuna(stage='all'):
    t0 = __import__('time').time()
    scan = load_scan('tuna')
    masks = body_masks(scan, flatten=[(-0.33, -0.08, True)])
    co, _ = mesh_points(scan)
    body = in_body(masks, co, 1)
    named = assign(co, appendage_groups(co, body), TUNA_SEEDS)
    keep = body.copy()
    if 'body' in named:
        keep[named.pop('body')] = True
    print('groups:', {k: len(v) for k, v in named.items()})
    low = body_loft(co[keep], step=0.006, nth=44, name='TUNA_BODY')
    smart_uv(low)
    parts = [(low, 0)]
    tmax = {}
    for i, (name, idx) in enumerate(sorted(named.items())):
        base = name.split('_')[0]
        cl, op, sg, cell, tx, tn, be = TUNA_FINS[base]
        fin = fin_sheet('FIN_' + name, co[idx], masks, close=cl, open_=op, sigma=sg, cell=cell, base_ext=be)
        parts.append((fin, i + 1))
        tmax[str(i + 1)] = (tx, tn)
        print('  fin %-12s pts %6d -> %d tris' % (name, len(idx), len(fin.data.polygons)))
    ob = join_parts(parts, 'TUNA')
    ob['fin_tmax'] = tmax
    ob['fin_names'] = {str(i + 1): n for i, n in enumerate(sorted(named))}
    solidify_fins(ob)          # before UV packing: each fin side gets its own island and its own bake
    pack_uv(ob)
    mat = product_material('TUNA_SKIN', None, rough=0.33)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    print('geometry %.0fs' % (__import__('time').time() - t0))
    nrm = bake([scan], ob, _img('TUNA_normal', 2048, data=True, color=(0.5, 0.5, 1, 1)), 'NORMAL', 0.006, 0.02, margin=16)
    col, rgb, known = bake_albedo(scan, ob)
    part = bake_attr_maps(ob, 2048)['part'][..., 0] > 0.5
    known, nbad = clean_fin_texels(rgb[..., :3].astype(np.float64), known, part)
    print('fin outlier texels', nbad)
    rgb3 = push_pull_fill(rgb[..., :3].astype(np.float64), known)
    rgb3, red = remove_blotches(rgb3)
    print('blotch px', int(red.sum()), 'miss px', int((~known).sum()))
    out = np.concatenate([rgb3, np.ones(rgb3.shape[:2] + (1,))], -1)
    np_img(col, out)
    save_png(col, WORK + '/tuna_albedo.png')
    save_png(nrm, WORK + '/tuna_normal.png')
    nt = mat.node_tree
    nt.nodes.remove(nt.nodes['BAKE_TARGET'])
    bpy.data.materials.remove(mat)
    ob.data.materials.clear()
    ob.data.materials.append(product_material('TUNA_SKIN', col, nrm, rough=0.33))
    bpy.data.objects.remove(scan)
    print('baked %.0fs, tris %d' % (__import__('time').time() - t0, sum(len(p.vertices) - 2 for p in ob.data.polygons)))
    bpy.ops.wm.save_as_mainfile(filepath=WORK + '/tuna_build.blend')
    export_glb(ob, MODELS + '/tuna.glb')
    return ob


def body_loft(pts, step=0.005, nth=48, pct=92, name='BODY', end_taper=True):
    """Closed, clean body skin lofted through the scan: for every X slice, the outer radius of the scan points in
    each of `nth` angular sectors around the slice centre (star-shaped section). Works on 'soup' scans where
    voxel remeshing would give a double wall. Belly = theta 0."""
    x = pts[:, 0]
    x0, x1 = x.min() + 0.0008, x.max() - 0.0008
    xs = np.linspace(x0, x1, max(8, int((x1 - x0) / step)))
    R = np.full((len(xs), nth), np.nan)
    C = np.zeros((len(xs), 2))
    order = np.argsort(x)
    xsorted = x[order]
    hw = max(step * 0.6, 0.0012)
    for i, xi in enumerate(xs):
        a, b = np.searchsorted(xsorted, [xi - hw, xi + hw])
        p = pts[order[a:b]]
        if len(p) < 12:
            continue
        cy, cz = (p[:, 1].min() + p[:, 1].max()) / 2, (p[:, 2].min() + p[:, 2].max()) / 2
        C[i] = cy, cz
        dy, dz = p[:, 1] - cy, p[:, 2] - cz
        th = np.mod(np.arctan2(dy, -dz), 2 * np.pi)
        rr = np.hypot(dy, dz)
        k = (th / (2 * np.pi) * nth).astype(int) % nth
        for s in range(nth):
            sel = rr[k == s]
            if len(sel) >= 3:
                R[i, s] = np.percentile(sel, pct)
    # fill missing sectors / slices by interpolation
    for i in range(len(xs)):
        row = R[i]
        ok = np.isfinite(row)
        if ok.sum() >= 3 and not ok.all():
            idx = np.arange(nth)
            R[i] = np.interp(idx, np.concatenate([idx[ok] - nth, idx[ok], idx[ok] + nth]),
                             np.concatenate([row[ok]] * 3))
    good = np.isfinite(R).all(1)
    for s in range(nth):
        R[:, s] = np.interp(xs, xs[good], R[good, s])
    C[:, 0] = np.interp(xs, xs[good], C[good, 0])
    C[:, 1] = np.interp(xs, xs[good], C[good, 1])
    # light smoothing (x: ~1 slice, theta: wrap-around)
    Rp = np.concatenate([R[:, -3:], R, R[:, :3]], 1)
    Rp = blur(Rp, 1.4)
    R = Rp[:, 3:-3]
    C = np.stack([blur(C[:, :1], 1.0)[:, 0], blur(C[:, 1:], 1.0)[:, 0]], 1)
    bm = bmesh.new()
    ths = (np.arange(nth) + 0.5) / nth * 2 * np.pi
    rings = []
    for i, xi in enumerate(xs):
        rings.append([bm.verts.new((xi, C[i, 0] + R[i, s] * math.sin(ths[s]), C[i, 1] - R[i, s] * math.cos(ths[s])))
                      for s in range(nth)])
    for i in range(len(xs) - 1):
        for s in range(nth):
            bm.faces.new([rings[i][s], rings[i][(s + 1) % nth], rings[i + 1][(s + 1) % nth], rings[i + 1][s]])
    for ring, xe, cc in ((rings[0], x0 - step * 0.3, C[0]), (rings[-1], x1 + step * 0.3, C[-1])):
        pole = bm.verts.new((xe, cc[0], cc[1]))
        for s in range(nth):
            f = [ring[s], ring[(s + 1) % nth], pole]
            bm.faces.new(f if ring is rings[-1] else f[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def export_glb(ob, path):
    """Centre on X/Y, rest on z=0 (glTF y=0 after the +Y-up conversion), longest axis X; GLB with the baked maps."""
    lo, hi = bbox(ob)
    ob.data.transform(Matrix.Translation(Vector((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))))
    ob.location = (0, 0, 0)
    for o in list(bpy.context.scene.objects):
        if o is not ob:
            bpy.data.objects.remove(o)
    for a in [a.name for a in ob.data.attributes if a.name in ('fin_w', 'part')]:
        ob.data.attributes.remove(ob.data.attributes[a])
    select_only(ob)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=True, export_texcoords=True, export_normals=True, export_animations=False,
                              export_image_format='WEBP', export_image_quality=90, export_attributes=False)
    lo, hi = bbox(ob)
    print('EXPORT %s tris %d dims %s size %d KB' % (path, sum(len(p.vertices) - 2 for p in ob.data.polygons),
                                                   (hi - lo).round(3), os.path.getsize(path) // 1024))


# ------------------------------------------------------------------------------------------------- swordfish (modelled)
def _poly_points(poly, step=0.002):
    """Dense points filling a 2-D polygon (even-odd rule)."""
    P = np.asarray(poly, float)
    lo, hi = P.min(0), P.max(0)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0], step), np.arange(lo[1], hi[1], step))
    x, y = gx.ravel(), gy.ravel()
    inside = np.zeros(len(x), bool)
    for (x1, y1), (x2, y2) in zip(P, np.roll(P, -1, 0)):
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / np.where(y2 == y1, 1e-12, y2 - y1) + x1)
        inside ^= c
    return np.stack([x[inside], y[inside]], 1)


def _spline(pts, n=24):
    """Catmull-Rom through control points (closed)."""
    P = np.asarray(pts, float)
    out = []
    for i in range(len(P)):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % len(P)], P[(i + 2) % len(P)]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


# station: x, centre z, half-width, half-height, superellipse exponent (2 = ellipse)
SWORD_ST = [(-1.200, 0.205, 0.003, 0.0015, 2.0), (-1.05, 0.206, 0.012, 0.004, 2.3), (-0.85, 0.208, 0.024, 0.008, 2.4),
            (-0.65, 0.210, 0.034, 0.012, 2.4), (-0.52, 0.212, 0.042, 0.018, 2.3), (-0.46, 0.205, 0.050, 0.030, 2.2),
            (-0.42, 0.195, 0.060, 0.052, 2.1), (-0.36, 0.190, 0.080, 0.085, 2.05), (-0.28, 0.190, 0.105, 0.125, 2.0),
            (-0.18, 0.195, 0.128, 0.160, 2.0), (-0.05, 0.200, 0.140, 0.180, 2.0), (0.10, 0.200, 0.138, 0.178, 2.0),
            (0.30, 0.200, 0.122, 0.158, 2.0), (0.50, 0.200, 0.095, 0.122, 2.0), (0.68, 0.200, 0.066, 0.082, 2.0),
            (0.82, 0.200, 0.045, 0.048, 2.0), (0.90, 0.200, 0.040, 0.032, 2.0), (0.95, 0.200, 0.042, 0.026, 2.0),
            (0.985, 0.200, 0.030, 0.022, 2.0)]


def sword_body(nth=48, step=0.012):
    st = np.array(SWORD_ST)
    xs = np.arange(st[0, 0], st[-1, 0] + 1e-6, step)
    xs = np.unique(np.concatenate([xs, np.linspace(-1.2, -1.15, 6)]))
    cols = [np.interp(xs, st[:, 0], st[:, k]) for k in range(1, 5)]
    th = (np.arange(nth) + 0.5) / nth * 2 * np.pi
    bm = bmesh.new()
    rings = []
    for i, x in enumerate(xs):
        cz, a, b, e = (c[i] for c in cols)
        s, c = np.sin(th), -np.cos(th)
        r = (np.abs(s / a) ** e + np.abs(c / b) ** e) ** (-1 / e)
        # flatter belly, slightly keeled back on the body; bill: flat with sharp side edges
        zc = cz + (0.012 if x > -0.4 else 0) * np.clip((x + 0.4) / 0.4, 0, 1) * (1 - np.clip((x - 0.6) / 0.35, 0, 1))
        rings.append([bm.verts.new((x, r[k] * s[k], zc + r[k] * c[k])) for k in range(nth)])
    for i in range(len(xs) - 1):
        for k in range(nth):
            bm.faces.new([rings[i][k], rings[i][(k + 1) % nth], rings[i + 1][(k + 1) % nth], rings[i + 1][k]])
    for ring, xe in ((rings[0], xs[0] - 0.004), (rings[-1], xs[-1] + 0.006)):
        cz = np.interp(xe, st[:, 0], st[:, 1])
        pole = bm.verts.new((xe, 0, cz))
        for k in range(nth):
            f = [ring[k], ring[(k + 1) % nth], pole]
            bm.faces.new(f if ring is rings[-1] else f[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('SWORD_BODY')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('SWORD_BODY', me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


# fin outlines in their own plane: (a = along X, b = up the fin), plus plane placement
SWORD_FINS = {
    # name: (control points (x, z) in the side plane, thickness root)
    'dorsal1': ([(-0.30, 0.335), (-0.25, 0.48), (-0.20, 0.62), (-0.15, 0.70), (-0.10, 0.70), (-0.13, 0.62),
                 (-0.13, 0.52), (-0.10, 0.44), (-0.05, 0.39), (-0.02, 0.365), (-0.15, 0.33)], 0.006),
    'dorsal2': ([(0.80, 0.235), (0.83, 0.262), (0.86, 0.258), (0.855, 0.236), (0.83, 0.225)], 0.003),
    'anal1': ([(0.05, 0.06), (0.10, -0.03), (0.15, -0.075), (0.18, -0.08), (0.17, -0.04), (0.20, 0.0),
               (0.25, 0.03), (0.15, 0.06)], 0.005),
    'anal2': ([(0.78, 0.17), (0.81, 0.135), (0.84, 0.140), (0.835, 0.165), (0.81, 0.178)], 0.003),
    'tail': ([(0.90, 0.20), (0.97, 0.26), (1.04, 0.40), (1.12, 0.55), (1.18, 0.61), (1.15, 0.52), (1.08, 0.38),
              (1.05, 0.27), (1.04, 0.20), (1.05, 0.13), (1.08, 0.02), (1.15, -0.12), (1.18, -0.21), (1.12, -0.15),
              (1.04, -0.01), (0.97, 0.14)], 0.009),
}


def sword_fins():
    obs = []
    for name, (ctrl, t) in SWORD_FINS.items():
        outline = _spline(ctrl, 16)
        pts2 = _poly_points(outline, 0.0015)
        pts = np.stack([pts2[:, 0], np.zeros(len(pts2)), pts2[:, 1]], 1)
        f = fin_sheet('FIN_' + name, pts, None, px=0.0015, close=0.002, open_=0.002, sigma=0.002, base_ext=0,
                      cell=0.010 if name in ('tail', 'dorsal1') else 0.006, normal=(0, 1, 0))
        f['tmax'] = t
        obs.append((name, f, t))
    # pectorals: long sickles low on the flank, swept back and slightly down
    for side in (1, -1):
        ctrl = [(-0.30, 0.0), (-0.20, 0.035), (-0.05, 0.035), (0.12, 0.010), (0.20, -0.015), (0.08, -0.005),
                (-0.10, -0.015), (-0.25, -0.025)]
        outline = _spline(ctrl, 16)
        pts2 = _poly_points(outline, 0.0015)
        # plane tilted ~35 deg out from the body side, root at the flank
        ang = math.radians(35)
        root = np.array([0.0, side * 0.115, 0.115])
        out_dir = np.array([0, side * math.sin(ang), -math.cos(ang) * 0.35])
        out_dir /= np.linalg.norm(out_dir)
        pts = root + np.outer(pts2[:, 0], [1, 0, 0]) + np.outer(pts2[:, 1] + 0.03, out_dir)
        nrm = np.cross([1, 0, 0], out_dir)
        f = fin_sheet('FIN_pect_%s' % ('L' if side > 0 else 'R'), pts, None, px=0.0015, close=0.002, open_=0.002,
                      sigma=0.002, base_ext=0, cell=0.008, normal=nrm)
        obs.append(('pect', f, 0.005))
    return obs


def vnoise(P, scale, seed=0):
    """3-D value noise (trilinear, smoothstep) in [0,1] for points P (n,3)."""
    q = P * scale + seed * 17.13
    i = np.floor(q).astype(np.int64)
    f = q - i
    f = f * f * (3 - 2 * f)

    def h(ix, iy, iz):
        n = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * h(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz)
    return out


def fbm(P, scale, oct=4, seed=0):
    s, a, tot = 0, 1.0, 0
    for o in range(oct):
        s = s + a * vnoise(P, scale * 2 ** o, seed + o)
        tot += a
        a *= 0.5
    return s / tot


def bake_attr_maps(ob, size):
    """Bake object-space position and normal into float images (Emit bake) for numpy painting."""
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = 1
    m = bpy.data.materials.new('ATTR')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    nt.links.new(em.outputs[0], out.inputs[0])
    tex = nt.nodes.new('ShaderNodeTexImage')
    nt.nodes.active = tex
    old = list(ob.data.materials)
    ob.data.materials.clear()
    ob.data.materials.append(m)
    select_only(ob)
    s.render.bake.use_selected_to_active = False
    s.render.bake.margin = 4
    res = {}
    at = nt.nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'part'
    for key, sock in (('pos', 'Position'), ('nrm', 'Normal'), ('part', None)):
        img = bpy.data.images.new('A_' + key, size, size, float_buffer=True, is_data=True)
        tex.image = img
        nt.links.new(geo.outputs[sock] if sock else at.outputs['Fac'], em.inputs[0])
        bpy.ops.object.bake(type='EMIT')
        res[key] = img_np(img)[..., :3].copy()
    alpha_img = bpy.data.images.new('A_cov', size, size, float_buffer=True, is_data=True)
    tex.image = alpha_img
    for l in list(em.inputs[0].links):
        nt.links.remove(l)
    em.inputs[0].default_value = (1, 1, 1, 1)
    s.render.bake.margin = 0
    bpy.ops.object.bake(type='EMIT')
    res['cov'] = img_np(alpha_img)[..., 0] > 0.5
    ob.data.materials.clear()
    for o in old:
        ob.data.materials.append(o)
    return res


def paint_swordfish(maps):
    P, N, part, cov = maps['pos'], maps['nrm'], np.rint(maps['part'][..., 0]).astype(int), maps['cov']
    H, W = cov.shape
    p = P.reshape(-1, 3)
    n = N.reshape(-1, 3)
    pid = part.ravel()
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    st = np.array(SWORD_ST)
    cz = np.interp(x, st[:, 0], st[:, 1])
    hh = np.interp(x, st[:, 0], st[:, 3])
    t = np.clip((z - cz) / np.maximum(hh, 1e-3), -1, 1)          # -1 belly .. +1 back
    back = np.array([0.075, 0.068, 0.066])
    bronze = np.array([0.20, 0.145, 0.095])
    flank = np.array([0.42, 0.42, 0.44])
    belly = np.array([0.62, 0.61, 0.60])
    k = np.clip((t + 0.05) / 0.55, 0, 1)[:, None]                 # countershading line just above the midline
    k = k * k * (3 - 2 * k)
    base = flank * (1 - k) + back * k
    bz = np.exp(-((t - 0.25) / 0.22) ** 2)[:, None] * 0.55          # bronze sheen band
    base = base * (1 - bz) + bronze * bz
    bl = np.clip((-t - 0.45) / 0.4, 0, 1)[:, None]
    base = base * (1 - bl) + belly * bl
    n1 = fbm(p, 9.0, 4, 1)[:, None]
    n2 = fbm(p * np.array([0.35, 1, 1]), 40.0, 3, 2)[:, None]
    n3 = vnoise(p, 160.0, 3)[:, None]
    base = base * (0.82 + 0.36 * n1) * (0.9 + 0.2 * n2) * (0.95 + 0.1 * n3)
    # faint purple-blue iridescence on the upper flank
    ir = np.exp(-((t - 0.05) / 0.18) ** 2)[:, None] * (fbm(p, 6.0, 2, 7)[:, None] > 0.5) * 0.12
    base = base + ir * np.array([0.05, 0.03, 0.12])
    # bill: dark, smooth, lighter underside
    bill = np.clip((-0.47 - x) / 0.04, 0, 1)[:, None]
    billc = np.where((n[:, 2] > 0)[:, None], np.array([0.085, 0.075, 0.07]), np.array([0.22, 0.20, 0.19]))
    billc = billc * (0.9 + 0.2 * fbm(p * np.array([0.2, 1, 1]), 30.0, 3, 9)[:, None])
    base = base * (1 - bill) + billc * bill
    # eye: large, dark blue-black iris with a pale ring
    for s_ in (1, -1):
        e = np.array([-0.405, s_ * 0.050, 0.212])
        d = np.linalg.norm(p - e, axis=1)
        ring = np.clip(1 - np.abs(d - 0.030) / 0.004, 0, 1)[:, None]
        iris = np.clip((0.028 - d) / 0.002, 0, 1)[:, None]
        pupil = np.clip((0.016 - d) / 0.002, 0, 1)[:, None]
        base = base * (1 - ring) + np.array([0.55, 0.52, 0.45]) * ring
        base = base * (1 - iris) + np.array([0.06, 0.08, 0.10]) * iris
        base = base * (1 - pupil) + np.array([0.01, 0.012, 0.015]) * pupil
        hl = np.clip((0.006 - np.linalg.norm(p - (e + np.array([0.008, 0, 0.010])), axis=1)) / 0.002, 0, 1)[:, None]
        base = base * (1 - hl * 0.6) + 0.5 * hl * 0.6
    # gill cover edge + mouth line (thin dark arcs)
    gx = -0.30 + 0.05 * ((z - 0.19) / 0.15) ** 2
    gill = np.clip(1 - np.abs(x - gx) / 0.004, 0, 1) * (np.abs(z - 0.19) < 0.15) * (x > -0.4)
    mouth = np.clip(1 - np.abs(z - (0.180 + 0.12 * (x + 0.47))) / 0.003, 0, 1) * (x > -0.47) * (x < -0.37)
    dark = np.maximum(gill, mouth)[:, None]
    base = base * (1 - 0.65 * dark)
    # fins: dark grey-brown with ray streaks, lighter thin trailing edges
    fin = (pid > 0)[:, None]
    rays = vnoise(p * np.array([1, 1, 0.05]), 90.0, 5)[:, None]
    finc = np.array([0.085, 0.075, 0.072]) * (0.8 + 0.4 * rays) * (0.85 + 0.3 * n1)
    base = np.where(fin, finc, base)
    out = base.reshape(H, W, 3)
    out = push_pull_fill(out, cov)
    return np.clip(out, 0, 1)


def build_swordfish():
    reset()
    body = sword_body()
    smart_uv(body)
    parts = [(body, 0)]
    tmax = {}
    for i, (name, f, t) in enumerate(sword_fins()):
        parts.append((f, i + 1))
        tmax[str(i + 1)] = (t, 0.0008)
    ob = join_parts(parts, 'SWORDFISH')
    ob['fin_tmax'] = tmax
    solidify_fins(ob)
    pack_uv(ob)
    maps = bake_attr_maps(ob, 2048)
    rgb = paint_swordfish(maps)
    img = _img('SWORD_albedo', 2048)
    np_img(img, np.concatenate([rgb, np.ones(rgb.shape[:2] + (1,))], -1))
    save_png(img, WORK + '/sword_albedo.png')
    ob.data.materials.clear()
    ob.data.materials.append(product_material('SWORD_SKIN', img, None, rough=0.42))
    bpy.ops.wm.save_as_mainfile(filepath=WORK + '/sword_build.blend')
    export_glb(ob, WORK + '/swordfish-attempt.glb')   # not shipped: fails G-PROD-2 (see report)


# ------------------------------------------------------------------------------------------------------------ prawn
def keep_big(ob, min_frac=0.002):
    """Drop connected components smaller than min_frac of the vertices (floating specks)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen = np.zeros(len(bm.verts), bool)
    kill = []
    nv = len(bm.verts)
    for v in bm.verts:
        if seen[v.index]:
            continue
        st, ids = [v], []
        seen[v.index] = True
        while st:
            x = st.pop()
            ids.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if not seen[y.index]:
                    seen[y.index] = True
                    st.append(y)
        if len(ids) < min_frac * nv:
            kill += ids
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    return len(kill)


def antenna_paths(scan, skin, gap=0.0015, cell=0.001, min_len=0.025):
    """Centrelines of thin strands in the scan that the remeshed skin lost (antennae): scan vertices farther than
    `gap` from the skin -> 3-D cell components -> longest geodesic path in each long component."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(skin, dg)
    me = scan.data
    hige = {i for i, m in enumerate(me.materials) if m.name.startswith('Hige')}
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    bad = np.zeros(len(co), bool)
    for p in me.polygons:
        if p.material_index in hige:
            bad[list(p.vertices)] = True
    far = [i for i in np.nonzero(~bad)[0] if tree.find_nearest(Vector(co[i]))[3] > gap]
    cells = {}
    for i in far:
        cells.setdefault(tuple((co[i] / cell).astype(int)), []).append(i)
    nb = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]
    seen, paths = set(), []

    def bfs(start, comp):
        par, dist, q = {start: None}, {start: 0}, [start]
        for k in q:
            for d in nb:
                n = (k[0] + d[0], k[1] + d[1], k[2] + d[2])
                if n in comp and n not in par:
                    par[n] = k
                    dist[n] = dist[k] + 1
                    q.append(n)
        far_ = max(dist, key=dist.get)
        return far_, par
    for c0 in cells:
        if c0 in seen:
            continue
        comp, q = {c0}, [c0]
        seen.add(c0)
        for k in q:
            for d in nb:
                n = (k[0] + d[0], k[1] + d[1], k[2] + d[2])
                if n in cells and n not in seen:
                    seen.add(n)
                    comp.add(n)
                    q.append(n)
        pts = np.array([co[i] for k in comp for i in cells[k]])
        if np.linalg.norm(pts.max(0) - pts.min(0)) < min_len:
            continue
        a, _ = bfs(c0, comp)
        b, par = bfs(a, comp)
        path, k = [], b
        while k is not None:
            path.append(np.mean([co[i] for i in cells[k]], 0))
            k = par[k]
        P = np.array(path)
        if len(P) > 5:
            P = np.stack([np.convolve(np.pad(P[:, j], 3, mode='edge'), np.ones(7) / 7, 'valid') for j in range(3)], 1)
        # root = the end nearer the skin; make it start inside the skin
        d0 = tree.find_nearest(Vector(P[0]))[3]
        d1 = tree.find_nearest(Vector(P[-1]))[3]
        if d1 < d0:
            P = P[::-1]
        root = np.array(tree.find_nearest(Vector(P[0]))[0])
        P = np.vstack([root + (root - P[0]) * 0.3, P])
        paths.append(P)
        print('  antenna path: %d pts, %.1f cm' % (len(P), 100 * np.linalg.norm(np.diff(P, axis=0), axis=1).sum()))
    return paths


def add_antennae(ob, paths, color, r0=0.00035, r1=0.00012, sides=6):
    bm = bmesh.new()
    for P in paths:
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        rings = []
        for i, p in enumerate(P):
            t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
            t = Vector(t).normalized()
            u = t.orthogonal().normalized()
            v = t.cross(u)
            r = r0 + (r1 - r0) * L[i] / L[-1]
            rings.append([bm.verts.new(Vector(p) + (u * math.cos(a) + v * math.sin(a)) * r)
                          for a in np.linspace(0, 2 * math.pi, sides, endpoint=False)])
        for a, b in zip(rings[:-1], rings[1:]):
            for k in range(sides):
                bm.faces.new([a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]])
        bm.faces.new(rings[-1][::-1])
    me = bpy.data.meshes.new('ANT')
    bm.to_mesh(me)
    bm.free()
    ant = bpy.data.objects.new('ANT', me)
    bpy.context.scene.collection.objects.link(ant)
    m = product_material('PRAWN_ANTENNA', None, rough=0.4)
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*color, 1)
    me.materials.append(m)
    me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        p.use_smooth = True
    select_only(ant, ob)
    bpy.ops.object.join()


def build_prawn(which='prawn', voxel=0.0008, tris=30000, out='prawn'):
    t0 = __import__('time').time()
    scan = load_scan(which)
    low = scan.copy()
    low.data = scan.data.copy()
    low.name = 'PRAWN'
    bpy.context.scene.collection.objects.link(low)
    select_only(low)
    low.data.remesh_voxel_size = voxel
    low.data.remesh_voxel_adaptivity = 0.0
    bpy.ops.object.voxel_remesh()
    print('remesh faces', len(low.data.polygons), 'specks removed', keep_big(low))
    ants = antenna_paths(scan, low)
    sm = low.modifiers.new('smooth', 'CORRECTIVE_SMOOTH')
    sm.iterations, sm.factor, sm.use_only_smooth = 4, 0.5, True
    bpy.ops.object.modifier_apply(modifier=sm.name)
    d = low.modifiers.new('dec', 'DECIMATE')
    d.ratio = min(1.0, tris / max(1, sum(len(p.vertices) - 2 for p in low.data.polygons)))
    d.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=d.name)
    for p in low.data.polygons:
        p.use_smooth = True
    smart_uv(low, angle=78, margin=0.001)
    pack_uv(low, margin=0.0015)
    mat = product_material('PRAWN_SHELL', None, rough=0.3)
    low.data.materials.clear()
    low.data.materials.append(mat)
    ext = voxel * 3
    col, rgb, known = bake_albedo(scan, low, 2048, ext, ext * 3)
    rgb3 = push_pull_fill(rgb[..., :3].astype(np.float64), known)
    out_ = np.concatenate([rgb3, np.ones(rgb3.shape[:2] + (1,))], -1)
    np_img(col, out_)
    save_png(col, WORK + '/%s_albedo.png' % out)
    nt = mat.node_tree
    nt.nodes.remove(nt.nodes['BAKE_TARGET'])
    low.data.materials.clear()
    low.data.materials.append(product_material('PRAWN_SHELL', col, None, rough=0.3))  # baked normal was ~flat: skip
    # antennae: strands thinner than the voxel are lost by the remesh -> rebuild them as tapered tubes along the
    # scan's own antenna centrelines. (The 'Hige*' strips in the scan are loose 2 cm fragments = specks: dropped.)
    if ants:
        add_antennae(low, ants, (0.50, 0.33, 0.26))
    bpy.data.objects.remove(scan)
    print('prawn %.0fs tris %d miss %d' % (__import__('time').time() - t0, sum(len(p.vertices) - 2 for p in low.data.polygons),
                                         int((~known).sum())))
    bpy.ops.wm.save_as_mainfile(filepath=WORK + '/%s_build.blend' % out)
    export_glb(low, MODELS + '/%s.glb' % out)


def build_prawn_scan(which='prawn', tris=45000, out='prawn', weld=0.00005):
    """Keep the scan's own UVs/textures: weld the photogrammetry soup, drop floating specks far from the animal,
    collapse-decimate to the web budget (legs/antennae are thin strips - checked in the turntable stills)."""
    scan = load_scan(which)
    bm = bmesh.new()
    bm.from_mesh(scan.data)
    n0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
    bm.to_mesh(scan.data)
    bm.free()
    print('weld', n0, '->', len(scan.data.vertices))
    t = sum(len(p.vertices) - 2 for p in scan.data.polygons)
    if t > tris:
        select_only(scan)
        d = scan.modifiers.new('dec', 'DECIMATE')
        d.ratio = tris / t
        d.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=d.name)
    for p in scan.data.polygons:
        p.use_smooth = True
    scan.name = 'PRAWN'
    export_glb(scan, MODELS + '/%s.glb' % out)


if __name__ == '__main__' and '--' in sys.argv:
    what = sys.argv[sys.argv.index('--') + 1]
    {'tuna': build_tuna, 'swordfish': build_swordfish, 'prawn': build_prawn, 'prawn_scan': build_prawn_scan,
     'prawn_alt': lambda: build_prawn('prawn_alt', out='prawn-alt')}[what]()
