"""Test stills for table.blend (run under render-lock): $B --factory-startup -b table.blend --python table_stills.py -- tag f1,f2,.. [WxH] [samples]"""
import sys
import bpy
sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import sklib
a = sys.argv[sys.argv.index('--') + 1:]
tag, frames = a[0], [int(x) for x in a[1].split(',')]
res = tuple(int(v) for v in a[2].split('x')) if len(a) > 2 else (960, 540)
spp = int(a[3]) if len(a) > 3 else 32
out = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/stills/table/'
for f in frames:
    dt = sklib.render_still(out + '%s_f%03d.png' % (tag, f), f, res, spp)
    print('STILL f%d %.1fs' % (f, dt))
