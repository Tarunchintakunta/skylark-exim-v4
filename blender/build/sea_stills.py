"""Test stills for sea.blend (run inside render-lock): Blender --factory-startup -b sea.blend --python sea_stills.py -- TAG f1,f2,.. [WxH] [samples]"""
import sys, bpy, time
sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import sklib
a = sys.argv[sys.argv.index('--') + 1:]
tag, frames = a[0], [int(x) for x in a[1].split(',')]
res = tuple(int(x) for x in a[2].split('x')) if len(a) > 2 else (960, 540)
spp = int(a[3]) if len(a) > 3 else 32
out = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/stills/sea/'
s = bpy.context.scene
for f in frames:
    dt = sklib.render_still('%s%s_f%03d.png' % (out, tag, f), f, res=res, samples=spp)
    print('STILL f%d %.1fs' % (f, dt))
