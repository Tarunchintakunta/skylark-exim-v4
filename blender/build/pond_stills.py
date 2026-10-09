"""Test stills for pond.blend: Blender --factory-startup -b pond.blend --python pond_stills.py -- TAG f1 f2 ... [--full]"""
import sys
import bpy
sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import sklib  # noqa
a = sys.argv[sys.argv.index('--') + 1:]
full = '--full' in a
a = [x for x in a if x != '--full']
tag, frames = a[0], [int(x) for x in a[1:]]
out = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/stills/pond/'
for f in frames:
    res = (1920, 1080) if full else (960, 540)
    dt = sklib.render_still(out + '%s_f%03d%s.png' % (tag, f, '_full' if full else ''), f, res, 64 if full else 32)
    print('STILL f%d %.1fs' % (f, dt))
