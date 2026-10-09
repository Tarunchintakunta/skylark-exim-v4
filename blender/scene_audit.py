"""Scene audit for QUALITY_GATES G-SCENE-1/2/4 — run inside Blender (MCP: exec(open(REPO+'/blender/scene_audit.py').read())) or
   Blender -b assets-src/blender/<blend>.blend --python blender/scene_audit.py -- [--step 6] [--hero PREFIX,PREFIX]
Reports (and writes docs/reviews/<blend>-audit.txt):
 - FLAT: mesh objects visible to the camera whose material has no image texture and no procedural texture node (untextured = toy look)
 - NOMAT: meshes without any material
 - INTERSECT: BVH overlaps between hero objects (names starting with the hero prefixes) every --step frames
 - FLOAT: hero objects whose lowest point is > 2 cm above / < -2 cm below the object directly under them at frame start (ray cast down)
 - TRIS: total evaluated triangles (warn > 3,000,000)
Exit text ends with "AUDIT PASS" or "AUDIT FAIL n issues".
"""
import os
import sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
step = int(argv[argv.index("--step") + 1]) if "--step" in argv else 6
prefixes = tuple((argv[argv.index("--hero") + 1] if "--hero" in argv else
                  "A-CONT,A-VESSEL,A-TRUCK,A-FORKLIFT,A-CRATE,A-CARTON,A-HERO,P-,A-NET,A-PORT-SPREADER,A-CARTON-PALLET").split(","))
s = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
issues = []
TEX = {"TEX_IMAGE", "TEX_NOISE", "TEX_MUSGRAVE", "TEX_VORONOI", "TEX_WAVE", "TEX_BRICK", "TEX_GRADIENT", "TEX_MAGIC", "TEX_CHECKER"}


def textured(mat):
    if not mat or not mat.use_nodes or not mat.node_tree:
        return False
    stack = [mat.node_tree]
    while stack:
        nt = stack.pop()
        for n in nt.nodes:
            if n.type in TEX:
                return True
            if n.type == "GROUP" and n.node_tree:
                stack.append(n.node_tree)
    return False


for ob in s.objects:
    if ob.type != "MESH" or ob.hide_render:
        continue
    mats = [sl.material for sl in ob.material_slots if sl.material]
    if not mats:
        issues.append("NOMAT %s" % ob.name)
    elif not any(textured(m) for m in mats) and not ob.name.startswith(("BRIDGE", "FX_", "SKY")):
        issues.append("FLAT %s (%s)" % (ob.name, ", ".join(m.name for m in mats)))

tris = 0
for inst in dg.object_instances:
    o = inst.object
    if o.type == "MESH":
        try:
            m = o.data
            tris += sum(len(p.vertices) - 2 for p in m.polygons)
        except Exception:
            pass
if tris > 3_000_000:
    issues.append("TRIS %d evaluated triangles (> 3M: use instancing/LOD)" % tris)

heroes = [o for o in s.objects if o.type == "MESH" and o.name.startswith(prefixes) and not o.hide_render]


def bvh(o):
    oe = o.evaluated_get(dg)
    me = oe.to_mesh()
    me.transform(o.matrix_world)
    t = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    oe.to_mesh_clear()
    return t


def root(o):
    while o.parent:
        o = o.parent
    return o


for f in range(s.frame_start, s.frame_end + 1, step):
    s.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    trees = {o.name: bvh(o) for o in heroes}
    names = list(trees)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = s.objects[names[i]], s.objects[names[j]]
            if root(a) is root(b):
                continue
            if trees[names[i]].overlap(trees[names[j]]):
                issues.append("INTERSECT f%d %s x %s" % (f, a.name, b.name))

s.frame_set(s.frame_start)
for o in heroes:
    if o.name.startswith("P-") or o.parent:
        continue
    lo = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    centre = o.matrix_world.translation.copy()
    hit, loc, *_ = s.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((centre.x, centre.y, lo - 0.001)), Vector((0, 0, -1)))
    if hit and (lo - loc.z) > 0.02:
        issues.append("FLOAT %s %.2f m above support" % (o.name, lo - loc.z))

name = os.path.splitext(os.path.basename(bpy.data.filepath))[0] or "untitled"
out = "\n".join(issues + ["AUDIT PASS" if not issues else "AUDIT FAIL %d issues" % len(issues)])
print(out)
try:
    d = os.path.join(bpy.path.abspath("//"), "..", "..", "docs", "reviews")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name + "-audit.txt"), "w").write(out + "\n")
except Exception as exc:
    print("could not write audit file:", exc)
