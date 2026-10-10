"""Turntable stills of a product GLB under a neutral studio HDRI (G-PROD-4).
  Blender --factory-startup -b --python product_turntable.py -- <in.glb> <out_prefix> [angles=0,90,180,270] [--raw] [--elev 12] [--zoom 1.0] [--res 960x540]
Writes <out_prefix>-<angle>.jpg (JPEG q80). --raw: join/flatten Sketchfab hierarchy, auto-fit (for looking at raw scans)."""
import math, sys
import bpy
from mathutils import Vector
sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import sklib

a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]
angles = [float(x) for x in a[2].split(',')] if len(a) > 2 and not a[2].startswith('--') else [0, 90, 180, 270]
opt = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
elev, zoom = opt('--elev', 12.0), opt('--zoom', 1.0)
rx, ry = (int(v) for v in opt('--res', '960x540').split('x'))
pitch_view = opt('--view', 'side')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
s = bpy.context.scene
meshes = [o for o in s.objects if o.type == 'MESH']
pivot = bpy.data.objects.new('PIVOT', None); s.collection.objects.link(pivot)
for o in s.objects:
    if o.parent is None and o is not pivot:
        o.parent = pivot
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
ctr = (lo + hi) / 2; size = hi - lo
print('BBOX', tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
L = max(size)
pivot.location = (-ctr.x, -ctr.y, 0)          # turn around the model's vertical centre line
pv = bpy.data.objects.new('TURN', None); s.collection.objects.link(pv); pivot.parent = pv

sklib.hdri('studio_small_09', res='2k', strength=1.0)
# floor: soft neutral grey so contact reads, but no busy texture
bpy.ops.mesh.primitive_plane_add(size=L * 30, location=(0, 0, lo.z))
fl = s.objects[-1] if s.objects[-1].type == 'MESH' else bpy.context.active_object
m = bpy.data.materials.new('floor'); m.use_nodes = True
bs = m.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = (0.42, 0.42, 0.43, 1); bs.inputs['Roughness'].default_value = 0.6
bpy.context.active_object.data.materials.append(m)

cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 85
cam = bpy.data.objects.new('cam', cam_d); s.collection.objects.link(cam); s.camera = cam
fov = 2 * math.atan(36 / 2 / 85)
dist = (L * 0.5 / math.tan(fov / 2)) * 1.12 / zoom
h = ctr.z
if pitch_view == 'top':
    cam.location = (0, 0, h + dist * 1.0); cam.rotation_euler = (0, 0, 0)
else:
    e = math.radians(elev)
    cam.location = (0, -dist * math.cos(e), h + dist * math.sin(e))
    d = Vector((0, 0, h)) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sklib.render_settings('ext', s)
s.render.use_motion_blur = False
s.view_settings.look = 'AgX - Base Contrast' if 'AgX - Base Contrast' else 'None'
im = s.render.image_settings; im.file_format = 'JPEG'; im.quality = 80; im.color_mode = 'RGB'
for ang in angles:
    pv.rotation_euler = (0, 0, math.radians(ang))
    sklib.render_still('%s-%d.jpg' % (out, int(ang)), res=(rx, ry), samples=48)
