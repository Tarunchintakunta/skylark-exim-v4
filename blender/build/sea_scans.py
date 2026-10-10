"""Prep the CC0 ffish.asia scans for sea.blend -> assets-src/models/sea-scans.blend (objects SCAN_<name>).
Weld (scans are unwelded glTF triangles), drop the colour-checker cube + specks (largest island kept),
decimate, length along +X (head toward +X unknown), centred, z min = 0, scaled to a real length.
Run: Blender --factory-startup -b --python sea_scans.py"""
import bpy, bmesh, math, numpy as np
REPO = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4'
SCANS = [('skipjack', 6000, 0.52), ('yellowfin-tuna', 9000, 0.85), ('green-tiger-prawn', 1500, 0.17),
         ('greasyback-shrimp', 900, 0.11)]
bpy.ops.wm.read_factory_settings(use_empty=True)
keep = []
for name, tris, length in SCANS:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath='%s/assets-src/scans/%s.glb' % (REPO, name))
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']
    newn = [o.name for o in new]
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(ms) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    for n in newn:
        o = bpy.data.objects.get(n)
        if o and o != ob:
            bpy.data.objects.remove(o, do_unlink=True)
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    ext = max(ob.dimensions)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=ext * 2e-4)
    # islands
    bm.verts.ensure_lookup_table()
    seen, isl = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        st, comp = [v], []
        seen.add(v.index)
        while st:
            a = st.pop(); comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index); st.append(b)
        isl.append(comp)
    isl.sort(key=len, reverse=True)
    main = isl[0]
    co = np.array([v.co[:] for v in main]); lo, hi = co.min(0), co.max(0); pad = (hi - lo) * 0.03
    dead = []
    for comp in isl[1:]:
        c = np.array([v.co[:] for v in comp])
        inside = np.all(c.min(0) >= lo - pad) and np.all(c.max(0) <= hi + pad)
        if not inside or len(comp) < 0.002 * len(bm.verts):
            dead += comp
    bmesh.ops.delete(bm, geom=dead, context='VERTS')
    bm.to_mesh(me); bm.free()
    from mathutils import Matrix
    for _ in range(4):
        t = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        if t <= tris * 1.15:
            break
        d = ob.modifiers.new('dec', 'DECIMATE'); d.ratio = max(0.05, tris / t)
        d.use_collapse_triangulate = True; bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        nm = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.remove(d)
        old = ob.data; ob.data = nm; bpy.data.meshes.remove(old)
    me = ob.data
    me.transform(ob.matrix_world); ob.matrix_world = Matrix()
    dims = list(ob.dimensions); ax = dims.index(max(dims))
    if ax == 1:
        me.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))
    elif ax == 2:
        me.transform(Matrix.Rotation(math.pi / 2, 4, 'Y'))
    me.update()
    co = np.array([v.co[:] for v in me.vertices]); lo, hi = co.min(0), co.max(0)
    s_ = length / (hi[0] - lo[0])
    me.transform(Matrix.Diagonal((s_, s_, s_, 1)) @ Matrix.Translation(-(lo + hi) / 2))
    co = np.array([v.co[:] for v in me.vertices])
    if True:          # scans stand upright (dorsal +Z) -> lay them on their side
        me.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    co = np.array([v.co[:] for v in me.vertices])
    me.transform(Matrix.Translation((0, 0, -co[:, 2].min())))
    me.update()
    ob.name = me.name = 'SCAN_' + name
    me.shade_smooth()
    print('SCAN', name, len(isl), 'islands; tris', sum(len(p.vertices) - 2 for p in me.polygons), 'dims', tuple(round(x, 3) for x in ob.dimensions))
    keep.append(ob)
for im in bpy.data.images:
    im.pack()
bpy.ops.wm.save_as_mainfile(filepath=REPO + '/assets-src/models/sea-scans.blend', compress=True)
