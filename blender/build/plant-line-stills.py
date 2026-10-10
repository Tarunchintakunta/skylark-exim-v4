"""Render test stills from the saved plant-line.blend (use inside render-lock, <= 4 frames per call).
Blender -b --factory-startup assets-src/blender/plant-line.blend --python plant-line-stills.py -- TAG f1,f2 [W H SAMPLES]"""
import sys, time, bpy
a = sys.argv[sys.argv.index('--') + 1:]
tag, frames = a[0], [int(x) for x in a[1].split(',')]
w, h, spp = (int(a[2]), int(a[3]), int(a[4])) if len(a) > 4 else (960, 540, 64)
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = w, h, 100
s.eevee.taa_render_samples = spp
for f in frames:
    s.frame_set(f)
    s.render.filepath = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/stills/plant-line/pl_%s_f%03d.png' % (tag, f)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print('PL_STILL f%d %dx%d %.1fs' % (f, w, h, time.time() - t), flush=True)
