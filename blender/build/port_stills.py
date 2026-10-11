"""Test stills of port.blend: $B --factory-startup -b assets-src/blender/port.blend --python port_stills.py -- TAG f1 f2 ... [full]
Writes assets-src/blender/stills/port/<TAG>_f<frame>.png (960x540, 64 spp) and prints seconds + mean luma."""
import sys
sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import bpy, numpy as np, sklib  # noqa
a = sys.argv[sys.argv.index('--') + 1:]
tag, full = a[0], 'full' in a
frames = [int(x) for x in a[1:] if x.isdigit()]
spp = int(([x[1:] for x in a[1:] if x[:1] == 's' and x[1:].isdigit()] or ['64'])[0])
for f in frames:
    p = '%s/blender/stills/port/%s_f%03d.png' % (sklib.SRC, tag, f)
    dt = sklib.render_still(p, f, (1920, 1080) if full else (960, 540), spp)
    im = bpy.data.images.load(p); px = np.array(im.pixels[:]).reshape(-1, 4)
    print('STILL f%d %.1fs luma %.1f %s' % (f, dt, 255 * float((px[:, :3] @ [0.2126, 0.7152, 0.0722]).mean()), p))
