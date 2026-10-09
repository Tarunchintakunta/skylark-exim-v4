"""sklib showcase / regression scene: open hero carton on a table, reefer + dry containers on a concrete quay,
fish crates with crushed ice, a pallet of cartons, sea strip behind, physical sky. Renders test stills.
   tools/render-lock.sh $B -b --python assets-src/blender/build/lib_showcase.py -- [shot ...]   (shots: wide carton crates)
"""
import sys
import time

sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import sklib  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
shots = argv or ['wide', 'carton', 'crates']
OUT = sklib.SRC + '/blender/stills/lib/'
t0 = time.time()
s = sklib.reset()
sklib.sky_world(sun_elev_deg=32, sun_az_deg=235, strength=1.0)


def box(name, c, size, mat, bev=0.004):
    bm = bmesh.new()
    sklib._bm_box(bm, Vector(c), size)
    ob = sklib._mesh_obj(name, bm)
    sklib.mat_to(ob, mat)
    if bev:
        sklib.bevel(ob, bev, 2)
    return ob


# quay slab (top at z=0) with its sea wall, water 1.6 m below
box('quay', (0, -5, -1.5), (120, 60, 3), sklib.concrete_quay(), 0.03)
sea = sklib.ocean(size=300, seed=41, choppy=1.0, wave_scale=0.6, wind=9)
sea.location = (-150, 25, -1.6)

# containers: dry 40 on the ground, reefer next to it, a second dry on top
sklib.container_40('dry', 'maroon', 0.45, 'A-CONT-40DRY.a').location = (-5, 13.5, 0)
sklib.container_40('reefer', 'white', 0.3, 'A-CONT-40RF.a').location = (-5, 10.6, 0)
sklib.container_40('dry', 'blue', 0.6, 'A-CONT-40DRY.b').location = (-5, 13.5, 2.591)
c20 = sklib.container_20('dry', 'green', 0.4, 'A-CONT-20DRY.a')
c20.location, c20.rotation_euler.z = (9, 15, 0), 0.25

# table + open carton
oak = sklib.oak_table()
box('table_top', (2.0, 0.0, 0.74), (1.6, 0.85, 0.04), oak, 0.006)
for x in (-0.72, 0.72):
    for y in (-0.36, 0.36):
        box('table_leg', (2.0 + x, y, 0.36), (0.06, 0.06, 0.72), oak, 0.004)
sklib.hero_carton(open_amount=1.0, loc=(2.05, 0.02, 0.76), rot_z=0.12)

# crates with ice on the quay
cr1 = sklib.crate((0.05, 0.22, 0.55), 'A-CRATE-FISH.1')
cr1.location = (0.35, -0.6, 0)
cr2 = sklib.crate((0.05, 0.22, 0.55), 'A-CRATE-FISH.2')
cr2.location = (0.35, -0.6, 0.25)
cr3 = sklib.crate((0.55, 0.08, 0.06), 'A-CRATE-FISH.3')
cr3.location, cr3.rotation_euler.z = (-0.35, -0.75, 0), 0.3
bpy.context.view_layer.update()
sklib.crushed_ice_fill(cr2, density=1.2, name='A-ICE-CRUSHED.2')
sklib.crushed_ice_fill(cr3, density=1.2, name='A-ICE-CRUSHED.3', seed=5)

# pallet of closed cartons
sklib.instance(sklib.carton_pallet(), (-2.2, 4.5, 0), 0.4, 'A-CARTON-PALLET.1')
sklib.instance(sklib.carton_pallet(), (-0.6, 5.2, 0), -0.1, 'A-CARTON-PALLET.2')

cam = sklib.camera('CAM', 30)
sklib.finish('lib_showcase', 'ext')
print('BUILD %.1fs' % (time.time() - t0))

SHOTS = {
    'wide': ((5.6, -5.2, 1.65), (-0.5, 6.0, 1.3), 28, None, 0),
    'carton': ((2.3, -0.42, 1.5), (2.05, 0.02, 0.93), 45, 'A-HERO-CARTON.block_11', 4.0),
    'crates': ((1.45, -2.35, 0.95), (0.0, -0.45, 0.32), 35, 'A-CRATE-FISH.2', 5.6),
    'label': ((2.75, -1.1, 1.05), (2.03, 0.0, 0.88), 40, 'A-HERO-CARTON', 5.6),
    'doors': ((5.5, 4.0, 1.7), (1.1, 12.0, 1.6), 30, None, 0),
    'reefer': ((-14.0, 5.5, 1.6), (-11.0, 10.6, 1.6), 30, None, 0),
}
for k in shots:
    loc, look, lens, foc, fst = SHOTS[k]
    sklib.camera('CAM', lens, loc, look)
    if foc:
        sklib.dof(cam, bpy.data.objects[foc], fst)
    else:
        cam.data.dof.use_dof = False
    sklib.render_still(OUT + 'lib_%s.png' % k)
