"""Clean a photoreal ffish.asia / Objaverse scan for Skylark v4 and export a Blender-ready GLB.
  Blender -b --python blender/clean_scan.py -- <in.glb> <out.glb> [--tris 60000] [--keep-checker]
 1. import; clear parents keeping transforms; apply transforms
 2. join all chunks (scans are split at 65k vertices) and find connected islands (union-find)
 3. delete every island outside the largest island's bounding box + 5% (= the colour-checker cube every ffish.asia scan has)
    and every island with < 0.5% of the vertices (= specks, the "floating crumb" seen in v3 PR #143)
 4. decimate to --tris (60k default for renders; scripts/optimize-glb.sh makes the <= 500 KB web version)
 5. longest axis -> X, centred, sitting on Z=0; export GLB with the scan textures
Then fix ragged fins / blotches BY HAND (ASSET_LIBRARY.md A-PROD checklist). Large scans take a few minutes headless.
"""
import math
import sys
import bpy
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    raise SystemExit("usage: -- <in.glb> <out.glb> [--tris N] [--keep-checker]")
src, dst = argv[0], argv[1]
tris_target = int(argv[argv.index("--tris") + 1]) if "--tris" in argv else 60000
keep_checker = "--keep-checker" in argv

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    raise SystemExit("no meshes in " + src)
for o in bpy.context.scene.objects:
    o.select_set(o.type == "MESH")
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(meshes) > 1:
    bpy.ops.object.join()
fish = bpy.context.view_layer.objects.active
for o in list(bpy.context.scene.objects):
    if o is not fish:
        bpy.data.objects.remove(o, do_unlink=True)
fish.name = "SCAN_" + dst.rsplit("/", 1)[-1].rsplit(".", 1)[0]
me = fish.data


def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


before = tri_count(fish)
nv = len(me.vertices)
ev = np.empty(len(me.edges) * 2, dtype=np.int64)
me.edges.foreach_get("vertices", ev)
parent = list(range(nv))


def find(a):
    root = a
    while parent[root] != root:
        root = parent[root]
    while parent[a] != root:
        parent[a], a = root, parent[a]
    return root


for a, b in ev.reshape(-1, 2).tolist():
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb
labels = np.fromiter((find(i) for i in range(nv)), dtype=np.int64, count=nv)
co = np.empty(nv * 3)
me.vertices.foreach_get("co", co)
co = co.reshape(-1, 3)
uniq, inv, counts = np.unique(labels, return_inverse=True, return_counts=True)
main = int(np.argmax(counts))
mmin, mmax = co[inv == main].min(0), co[inv == main].max(0)
pad = (mmax - mmin) * 0.05
kill = np.zeros(len(uniq), dtype=bool)
checker = 0
for k in range(len(uniq)):
    if k == main:
        continue
    pts = co[inv == k]
    outside = np.any(pts.min(0) > mmax + pad) or np.any(pts.max(0) < mmin - pad)
    if outside and not keep_checker:
        kill[k] = True
        checker += 1
    elif counts[k] < 0.005 * nv:
        kill[k] = True
dead = np.nonzero(kill[inv])[0].tolist()
if dead:
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in dead], context="VERTS")
    bm.to_mesh(me)
    bm.free()

t = tri_count(fish)
if t > tris_target:
    mod = fish.modifiers.new("decimate", "DECIMATE")
    mod.ratio = tris_target / float(t)
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)

dims = list(fish.dimensions)
ax = dims.index(max(dims))
if ax == 1:
    fish.rotation_euler[2] = math.radians(90)
elif ax == 2:
    fish.rotation_euler[1] = math.radians(90)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
fish.location = (0, 0, 0)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
zmin = min(v.co.z for v in me.vertices)
fish.location.z = -zmin
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", use_selection=False, export_apply=True)
print("CLEAN_SCAN", src, "->", dst)
print("  islands: %d, deleted %d (outside fish bbox: %d)" % (len(uniq), int(kill.sum()), checker))
print("  tris: %d -> %d | size: %.3f x %.3f x %.3f" % (before, tri_count(fish), *fish.dimensions))
print("  NEXT: fix fins/blotches by hand (ASSET_LIBRARY A-PROD), then scripts/optimize-glb.sh")
