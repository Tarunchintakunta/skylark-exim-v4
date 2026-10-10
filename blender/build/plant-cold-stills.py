"""Test stills from the SAVED plant-cold.blend (build outside the lock, render inside it):
   assets-src/tools/render-lock-wd.sh $B --factory-startup -b assets-src/blender/plant-cold.blend \
       --python assets-src/blender/build/plant-cold-stills.py -- r2 1 120 300 574     (<= 4 frames per call)
   ... -- full 300     (one timed 1920x1080 64-sample frame)
"""
import sys

sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import sklib  # noqa: E402

a = sys.argv[sys.argv.index('--') + 1:]
out = sklib.SRC + '/blender/stills/plant-cold/'
tag, frames = a[0], [int(f) for f in a[1:]]
if tag.startswith('prev'):        # preview settings (render-scene.sh preview): 16 spp, no motion blur
    sc = sklib.bpy.context.scene
    sc.eevee.taa_render_samples, sc.render.use_motion_blur = 16, False
    sc.eevee.volumetric_samples, sc.eevee.volumetric_tile_size = 16, '8'
for f in frames:
    if tag == 'full':
        print('FULLFRAME %d %.1fs' % (f, sklib.render_still(out + 'full_f%04d.png' % f, f, res=(1920, 1080))))
    else:
        sklib.render_still(out + '%s_f%04d.png' % (tag, f), f, samples=16 if tag.startswith('prev') else None)
