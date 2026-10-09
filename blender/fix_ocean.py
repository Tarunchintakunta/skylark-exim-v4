"""Make Ocean modifiers affordable (measured: a 2 km Ocean = 40×40 repeated 50 m tiles cost ~70 s of a 74 s preview frame).
Keeps the displaced ocean at <= MAX×MAX tiles of 100 m around its old centre and adds a flat far plane with the same
water material out to the old extent (slightly below, no shadow), so the horizon stays continuous.
  Blender --factory-startup -b <file.blend> --python blender/fix_ocean.py -- [MAX=8] [RES=10]   (saves in place)
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MAX = int(argv[0]) if argv else 6
RES = int(argv[1]) if len(argv) > 1 else 10
for ob in list(bpy.data.objects):
    for m in ob.modifiers:
        if m.type != 'OCEAN' or (m.repeat_x <= MAX and m.resolution <= RES):
            continue
        old = (m.repeat_x * m.spatial_size, m.repeat_y * m.spatial_size)
        cx, cy = ob.location.x + old[0] / 2, ob.location.y + old[1] / 2
        m.spatial_size = tile = 100
        m.repeat_x, m.repeat_y = min(max(1, round(old[0] / tile)), MAX), min(max(1, round(old[1] / tile)), MAX)
        if m.use_foam:
            m.foam_coverage = -0.3
        m.resolution = min(m.resolution, RES)
        ob.location.x, ob.location.y = cx - m.repeat_x * tile / 2, cy - m.repeat_y * tile / 2
        far_name = ob.name + '_far'
        if far_name not in bpy.data.objects and max(old) > m.repeat_x * tile:
            bpy.ops.mesh.primitive_plane_add(size=max(old) * 1.5, location=(cx, cy, ob.location.z - 0.15))
            far = bpy.context.active_object
            far.name = far_name
            for c in far.users_collection:
                c.objects.unlink(far)
            for c in ob.users_collection:
                c.objects.link(far)
            far.data.materials.append(ob.active_material)
            far.visible_shadow = False
        print('fix_ocean', ob.name, 'tiles', m.repeat_x, 'res', m.resolution, 'old extent', old)
bpy.ops.wm.save_mainfile()
