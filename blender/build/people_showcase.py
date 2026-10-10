"""People showcase: lineup of all outfits + close-ish shot of 2 PPE plant workers at a steel table.
Run: render-lock.sh Blender -b --python people_showcase.py [-- round_tag]"""
import math
import os
import sys
import time

import bpy

REPO = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4'
sys.path.insert(0, REPO + '/assets-src/blender/lib')
bpy.ops.wm.read_factory_settings(use_empty=True)
import people  # noqa: E402

OUT = REPO + '/assets-src/blender/stills/people/'
TAG = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'r1'
TEX = REPO + '/assets-src/tex/concrete_floor_02/concrete_floor_02_'
s = bpy.context.scene


def concrete():
    m = bpy.data.materials.new('concrete'); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    bs = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.4, 0.4, 0.4)
    L.new(tc.outputs['Object'], mp.inputs[0])

    def img(suf, col):
        t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(TEX + suf)
        if not col:
            t.image.colorspace_settings.name = 'Non-Color'
        L.new(mp.outputs[0], t.inputs[0]); return t
    L.new(img('diff_1k.jpg', True).outputs[0], bs.inputs['Base Color'])
    L.new(img('rough_1k.jpg', False).outputs[0], bs.inputs['Roughness'])
    nm = N.new('ShaderNodeNormalMap'); L.new(img('nor_gl_1k.jpg', False).outputs[0], nm.inputs['Color'])
    L.new(nm.outputs[0], bs.inputs['Normal'])
    return m


def steel():
    m = bpy.data.materials.new('steel'); m.use_nodes = True
    bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (0.72, 0.72, 0.72, 1); bs.inputs['Metallic'].default_value = 1
    bs.inputs['Roughness'].default_value = 0.28
    N, L = m.node_tree.nodes, m.node_tree.links
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 300
    mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.2; mr.inputs['To Max'].default_value = 0.38
    L.new(nz.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs['Result'], bs.inputs['Roughness'])
    return m


def box(name, loc, size, mat, bevel=0.004):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = 2
    o.data.materials.append(mat)
    return o


# --- environment: neutral daylit hall-ish space -------------------------------------------------
s.render.engine = 'BLENDER_EEVEE'
s.render.resolution_x, s.render.resolution_y = 960, 540
s.eevee.taa_render_samples = 48
s.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.55, 0.62, 0.72, 1); bg.inputs[1].default_value = 0.9
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(52), math.radians(8), math.radians(-35)))
sun = bpy.context.object; sun.data.energy = 3.2; sun.data.angle = math.radians(3)
bpy.ops.mesh.primitive_plane_add(size=60)
bpy.context.object.data.materials.append(concrete())
wall = box('wall', (0, 8, 3), (60, 0.3, 6), bpy.data.materials.new('wallm'))
wall.data.materials[0].diffuse_color = (0.6, 0.6, 0.58, 1)
wall.data.materials[0].use_nodes = True
wall.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.55, 0.52, 1)

# --- lineup ------------------------------------------------------------------------------------
cast = [  # name, sex, age, body, tone, outfit, pose
    ('a', 'male', 0.25, dict(weight=0.4, muscle=0.6, height=0.5), 0.7, 'tshirt_lungi', 'stand'),
    ('b', 'male', 0.6, dict(weight=0.65, muscle=0.5, height=0.45), 0.55, 'cotton_shirt_lungi_towel', 'wave'),
    ('c', 'female', 0.3, dict(weight=0.5, muscle=0.4, height=0.4), 0.45, 'formal_shirt_lanyard', 'stand'),
    ('d', 'male', 0.35, dict(weight=0.55, muscle=0.6, height=0.6), 0.8, 'hivis_helmet', 'carry'),
    ('e', 'male', 0.45, dict(weight=0.6, muscle=0.6, height=0.5), 0.65, 'oilskins', 'pull_rope'),
    ('f', 'male', 0.3, dict(weight=0.5, muscle=0.5, height=0.55), 0.35, 'thermal_suit', 'walk'),
    ('g', 'male', 0.2, dict(weight=0.35, muscle=0.5, height=0.5), 0.9, 'tshirt_shorts', 'crouch'),
    ('h', 'female', 0.5, dict(weight=0.6, muscle=0.4, height=0.4), 0.5, 'lab_coat', 'stand'),
    ('i', 'male', 0.7, dict(weight=0.5, muscle=0.4, height=0.45), 0.6, 'diner_shirt', 'sit'),
    ('j', 'female', 0.4, dict(weight=0.55, muscle=0.4, height=0.45), 0.3, 'diner_sweater', 'stand'),
]
if os.environ.get('SK_ONLY'):
    cast = [c for c in cast if c[0] in os.environ['SK_ONLY']]
stats = []
x0 = -(len(cast) - 1) * 1.15 / 2
for k, (n, sex, age, body, tone, outfit, pose) in enumerate(cast):
    t = time.time()
    p = people.make_person('P_' + n, sex=sex, age=age, body=body, skin_tone=tone, outfit=outfit, pose=pose,
                           location=(x0 + k * 1.15, 0, 0), rotation_z=math.radians((k % 3 - 1) * 12), seed=k + 3)
    dt = time.time() - t
    if pose == 'sit':
        box('stool', (p.location.x, p.location.y + 0.08, 0.22), (0.38, 0.38, 0.44), steel(), 0.01)
    stats.append((n, outfit, pose, round(dt, 2), people.tri_count(p), p['sk_mpfb'], p['sk_modelled']))
    print('PERSON', stats[-1], flush=True)

# --- PPE pair at a stainless table (placed off to the side) -----------------------------------
TX = 20.0
st = steel()
box('table_top', (TX, 0, 0.885), (1.6, 0.8, 0.03), st)
for dx in (-0.75, 0.75):
    for dy in (-0.35, 0.35):
        box('leg', (TX + dx, dy, 0.44), (0.04, 0.04, 0.87), st)
box('shelf', (TX, 0, 0.18), (1.5, 0.7, 0.02), st)
ppe = []
for k, (sx, sex, tone, age) in enumerate([(-0.38, 'male', 0.7, 0.3), (0.42, 'female', 0.5, 0.45)]):
    t = time.time()
    p = people.make_person('W_%d' % k, sex=sex, age=age, body=dict(weight=0.5 + 0.1 * k, height=0.5 - 0.05 * k),
                           skin_tone=tone, outfit='ppe_plant', pose='work_table',
                           location=(TX + sx, -0.78, 0), rotation_z=math.pi + math.radians(-6 + 10 * k), seed=40 + k)
    people.animate_cycle(p, 'work', 1, 120, phase=0.37 * k)
    ppe.append(p)
    stats.append(('W%d' % k, 'ppe_plant', 'work_table', round(time.time() - t, 2), people.tri_count(p),
                  p['sk_mpfb'], p['sk_modelled']))
    print('PERSON', stats[-1], flush=True)
for nm, kind, ph in (('P_b', 'wave', 0.0), ('P_e', 'pull', 0.3), ('P_f', 'walk', 0.6), ('P_d', 'work', 0.1)):
    if nm in bpy.data.objects:
        people.animate_cycle(bpy.data.objects[nm], kind, 1, 120, phase=ph)
t = time.time()
l1 = people.make_person('L1', sex='male', age=0.5, outfit='hivis_helmet', pose='walk', location=(40, 0, 0), seed=99, lod='L1')
print('L1', round(time.time() - t, 2), people.tri_count(l1), flush=True)
s.frame_set(30)


def cam(name, loc, look, lens):
    from mathutils import Vector
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.object; c.name = name; c.data.lens = lens
    d = Vector(look) - Vector(loc)
    c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return c


shots = [
    ('lineup_wide', (0, -10.5, 1.6), (0, 0, 0.95), 35),
    ('lineup_left', (x0 + 2 * 1.15, -5.2, 1.5), (x0 + 2 * 1.15, 0, 1.0), 40),
    ('lineup_right', (x0 + 7 * 1.15, -5.2, 1.5), (x0 + 7 * 1.15, 0, 1.0), 40),
    ('ppe_table', (TX + 0.9, 2.9, 1.7), (TX, -0.6, 1.1), 45),
    ('faces_2m', (x0 + 1.6, -2.0, 1.55), (x0 + 1.6, 0, 1.45), 50),
]
if os.environ.get('SK_ONLY'):
    shots = [('only', (0, -4.5, 1.4), (0, 0, 0.95), 35)]
for nm, loc, look, lens in shots:
    s.camera = cam(nm, loc, look, lens)
    s.render.filepath = OUT + '%s_%s.png' % (nm, TAG)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print('RENDER', nm, round(time.time() - t, 2), flush=True)
for r in stats:
    print('STAT', r)
bpy.ops.wm.save_as_mainfile(filepath='/tmp/claude-501/sk/people/showcase.blend')
