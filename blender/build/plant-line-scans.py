"""Low-poly instancing copies of the CC0 shrimp scans for plant-line.blend.
  Blender -b --factory-startup --python plant-line-scans.py -- <in.glb> <out.glb> [--tris 6000]
Same idea as REPO/blender/clean_scan.py, but WELDS the glTF split vertices first: without the weld every UV seam
splits the scan into ~74k 'islands' and the small-island filter deletes most of the shrimp (shredded result)."""
import sys

import bmesh
import bpy
import numpy as np

a = sys.argv[sys.argv.index('--') + 1:]
src, dst = a[0], a[1]
tris = int(a[a.index('--tris') + 1]) if '--tris' in a else 6000
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in bpy.context.scene.objects:
    o.select_set(o.type == 'MESH')
bpy.context.view_layer.objects.active = ms[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(ms) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
for o in list(bpy.context.scene.objects):
    if o is not ob:
        bpy.data.objects.remove(o)
me = ob.data
bm = bmesh.new()
bm.from_mesh(me)
size = max(ob.dimensions)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=size * 2e-5)
# islands (welded)
bm.verts.ensure_lookup_table()
lab = [-1] * len(bm.verts)
isl = []
for v in bm.verts:
    if lab[v.index] >= 0:
        continue
    k = len(isl)
    st, n = [v], 0
    lab[v.index] = k
    pts = []
    while st:
        w = st.pop()
        n += 1
        pts.append(w.co.copy())
        for e in w.link_edges:
            o2 = e.other_vert(w)
            if lab[o2.index] < 0:
                lab[o2.index] = k
                st.append(o2)
    p = np.array(pts)
    isl.append((n, p.min(0), p.max(0)))
main = max(range(len(isl)), key=lambda i: isl[i][0])
mn, mx = isl[main][1], isl[main][2]
pad = (mx - mn) * 0.05
kill = set()
for i, (n, a0, a1) in enumerate(isl):
    if i == main:
        continue
    if np.any(a0 > mx + pad) or np.any(a1 < mn - pad) or n < 0.002 * len(bm.verts):
        kill.add(i)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if lab[v.index] in kill], context='VERTS')
bm.to_mesh(me)
bm.free()
t0 = sum(len(p.vertices) - 2 for p in me.polygons)
if t0 > tris:
    d = ob.modifiers.new('dec', 'DECIMATE')
    d.ratio = tris / t0
    bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
ob.location = (0, 0, 0)
bpy.ops.object.transform_apply(location=True)
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_apply=True)
print('PL_SCAN', dst, 'islands', len(isl), 'killed', len(kill), 'tris', t0, '->',
      sum(len(p.vertices) - 2 for p in me.polygons), 'dims', tuple(round(x, 3) for x in ob.dimensions))
