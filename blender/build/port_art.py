"""Art pass for port.blend (issue #75, docs/COLOR_SCRIPT.md row 02 v-port): dusk harbour, purple-orange.
Run at the end of port.py (after sklib.finish), or on a saved port.blend for test stills:
  $B --factory-startup -b assets-src/blender/port.blend --python assets-src/blender/build/port_art.py --python .../port_stills.py -- TAG 1 27
Key: sun elev 8 deg, az 260 deg, #ff8c4a (constant over the shot; f1 = BRIDGE_SEA dusk, f264 = BRIDGE_DOOR dusk).
Fill: sky #4b4a8c. Rim: low sun #ffb06b. World: dusk sky zenith #262457 -> horizon #f29a5e. Haze #c98a7a 0.0006.
Accent: sodium #ffd28a (light-tower + crane floodlights, lamp lenses). Grade: look.apply(scene, 'port').
"""
import math
import sys

sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import look  # noqa: E402
import sklib  # noqa: E402

S = bpy.context.scene
D2R = math.pi / 180
BOUNCE_E = 2.0
EL, AZ = 8.0, 260.0
QZ = 3.0
H = look.hex_rgb


def sun_dir(el, az):
    e, a = el * D2R, az * D2R
    return Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))   # towards the sun


def aim(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()


# ---- key + world = reefer.py dusk_world() exactly (BRIDGE_SEA: port f1 must match reefer f192): sky_world(8, 260),
# sun #ff8c4a at sklib's elevation energy, sky mixed 0.6 with an EASE gradient horizon #e8825a -> zenith #1b2a4a
SUN = bpy.data.objects['SK_Sun']
W = bpy.data.worlds['SK_Sky']
for idb in (SUN, SUN.data, W.node_tree):
    idb.animation_data_clear()
W, SUN = sklib.sky_world(sun_elev_deg=EL, sun_az_deg=AZ, sun_angle_deg=3.0)
look.light(SUN, '#ff8c4a', 6.0)   # reefer uses 2.24; top-down sea at f1 is emission + glossy, unaffected by the key
nt = W.node_tree
sky = next(n for n in nt.nodes if n.type == 'TEX_SKY')
bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
tc = sklib._n(nt, 'ShaderNodeTexCoord', -900, -300)
sep = sklib._n(nt, 'ShaderNodeSeparateXYZ', -700, -300)
sklib._l(nt, tc.outputs['Generated'], sep.inputs[0])
ramp = sklib._n(nt, 'ShaderNodeValToRGB', -500, -300)
sklib._l(nt, sklib._maprange(nt, sep.outputs['Z'], 0.0, 0.6, 0.0, 1.0, -600, -500), ramp.inputs['Fac'])
ramp.color_ramp.elements[0].color = (*H('#e8825a'), 1)
ramp.color_ramp.elements[1].color = (*H('#1b2a4a'), 1)
ramp.color_ramp.interpolation = 'EASE'
sklib._l(nt, sklib._mix(nt, 0.6, sky.outputs[0], ramp.outputs['Color'], 'MIX', -100, 0), bg.inputs[0])

# ---- sea = reefer.py (seed 41, t=8.0 at f1 already): deep dusk blue body, warm #ff8c4a glints, haze toward #c98a7a
wm = bpy.data.materials['A-ENV-SEA_water']
nt = wm.node_tree
em = next(n for n in nt.nodes if n.type == 'EMISSION')
body = em.inputs['Color'].links[0].from_node
ba, bb = [x for x in body.inputs if x.type == 'RGBA']
ba.default_value = (0.010, 0.036, 0.095, 1)
bb.default_value = (0.040, 0.140, 0.220, 1)
mo = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
last = mo.inputs['Surface'].links[0].from_socket
geo = sklib._n(nt, 'ShaderNodeNewGeometry', -300, -2500)
dp = sklib._n(nt, 'ShaderNodeVectorMath', -300, -2700, operation='DOT_PRODUCT')
sklib._l(nt, geo.outputs['Normal'], dp.inputs[0])
dp.inputs[1].default_value = tuple(sun_dir(EL, AZ))
gp = sklib._math(nt, 'POWER', sklib._math(nt, 'MAXIMUM', dp.outputs['Value'], 0.0), 4.0)
gtc = sklib._n(nt, 'ShaderNodeTexCoord', -500, -3000)
spk = sklib._noise(nt, gtc.outputs['Object'], 1.6, 8.0, 0.7, -300, -3000)
spk = sklib._maprange(nt, spk.outputs['Fac'], 0.52, 0.72, 0.0, 1.0)
gem = sklib._n(nt, 'ShaderNodeEmission', 300, -2700)
gem.inputs['Color'].default_value = (*H('#ff8c4a'), 1)
sklib._l(nt, sklib._math(nt, 'MULTIPLY', sklib._math(nt, 'MULTIPLY', gp, spk), 60.0), gem.inputs['Strength'])
gad = sklib._n(nt, 'ShaderNodeAddShader', 900, -600)
sklib._l(nt, last, gad.inputs[0])
sklib._l(nt, gem.outputs[0], gad.inputs[1])
cdn = sklib._n(nt, 'ShaderNodeCameraData', -1500, -1900)
hz = sklib._math(nt, 'SUBTRACT', 1.0, sklib._math(nt, 'EXPONENT', sklib._math(nt, 'MULTIPLY', cdn.outputs['View Distance'], -0.0008)))
hem = sklib._n(nt, 'ShaderNodeEmission', 600, -900)
hem.inputs['Color'].default_value = (*H('#c98a7a'), 1)
hem.inputs['Strength'].default_value = 0.35
hmx = sklib._n(nt, 'ShaderNodeMixShader', 1100, -300)
sklib._l(nt, hz, hmx.inputs[0])
sklib._l(nt, gad.outputs[0], hmx.inputs[1])
sklib._l(nt, hem.outputs[0], hmx.inputs[2])
sklib._l(nt, hmx.outputs[0], mo.inputs['Surface'])

# ---- fill (violet sky bounce, no shadow) + rim (low warm sun kick on crane / box edges)
FILL = look.add_light(S, 'SK_Fill', 'SUN', '#4b4a8c', 4.0, (0, 0, 0),
               sun_dir(35, AZ - 180).to_track_quat('Z', 'Y').to_euler(), shadow=False)
rim = look.add_light(S, 'SK_Rim', 'SUN', '#ffb06b', 2.5, (0, 0, 0),
                     sun_dir(14, AZ - 25).to_track_quat('Z', 'Y').to_euler(), shadow=True)
rim.data.angle = 4.0 * D2R

# ---- sodium practicals: light towers + crane floodlights; lamp lenses glow
lamp = bpy.data.materials['lamp_lens']
b = next(n for n in lamp.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
b.inputs['Emission Color'].default_value = (*H('#ffd28a'), 1)
b.inputs['Emission Strength'].default_value = 40.0
TOWERS = ((67, -95), (67, -5), (67, 125), (67, 235), (236, -60), (236, 60), (236, 180), (236, 300))
for k, (x, y) in enumerate(TOWERS):
    o = look.add_light(S, 'SK_Sodium.T%d' % k, 'SPOT', '#ffd28a', 60000, (x, y - 0.6, QZ + 34.6), shadow=False)
    o.data.spot_size, o.data.spot_blend = 120 * D2R, 0.8
    aim(o, (x - 6, y - 6, QZ))
for k, cy in enumerate((-52.8, 0.0, 39.6)):
    for j, (x, tx) in enumerate(((25.0, 25.0), (-30.0, -16.0))):
        o = look.add_light(S, 'SK_Sodium.C%d%d' % (k, j), 'SPOT', '#ffd28a', 25000, (x, cy + 4.0, 42.0), shadow=False)
        o.data.spot_size, o.data.spot_blend = 70 * D2R, 0.9
        aim(o, (tx, cy + 4.0, QZ))

# ---- BRIDGE_DOOR: warm #ff9a5c side light from camera-left (-Y) grazing the truck reefer doors (camera looks -X)
door = look.add_light(S, 'SK_DoorKey', 'AREA', '#ff9a5c', 3500, (52.3, 18.0 - 5.5, 6.6), size=1.5, shadow=True)
aim(door, (51.0, 18.0, 5.4))

# ---- aerial perspective: day-blue haze emission -> dusk haze (#c98a7a, ridge more violet), dimmer
for m in bpy.data.materials:
    if m.name.endswith('_haze') and m.node_tree:
        em = next((n for n in m.node_tree.nodes if n.type == 'EMISSION'), None)
        if em:
            ridge = m.name.startswith('hill_veg')
            em.inputs['Color'].default_value = (*H('#9a6f86' if ridge else '#c98a7a'), 1)
            em.inputs['Strength'].default_value = 0.55 if ridge else 0.6


# ---- material richness: large-scale hue/value drift over big surfaces (no flat grey slabs)
def vary(name, a, b, scale, amt=1.0):
    m = bpy.data.materials.get(name)
    if not m or not m.node_tree:
        return
    t = m.node_tree
    bs = next(n for n in t.nodes if n.type == 'BSDF_PRINCIPLED')
    inp = bs.inputs['Base Color']
    if not inp.links:
        return
    src = inp.links[0].from_socket
    co = t.nodes.new('ShaderNodeTexCoord')
    nz = t.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value, nz.inputs['Detail'].default_value = scale, 3.0
    t.links.new(co.outputs['Object'], nz.inputs['Vector'])
    rp = t.nodes.new('ShaderNodeValToRGB')
    rp.color_ramp.elements[0].position, rp.color_ramp.elements[0].color = 0.35, (*a, 1)
    rp.color_ramp.elements[1].position, rp.color_ramp.elements[1].color = 0.65, (*b, 1)
    t.links.new(nz.outputs['Fac'], rp.inputs['Fac'])
    mx = t.nodes.new('ShaderNodeMix')
    mx.data_type, mx.blend_type = 'RGBA', 'MULTIPLY'
    mx.inputs[0].default_value = amt
    ca, cb = [x for x in mx.inputs if x.type == 'RGBA']
    t.links.new(src, ca)
    t.links.new(rp.outputs['Color'], cb)
    t.links.new(next(x for x in mx.outputs if x.type == 'RGBA'), inp)


WARM, COOL = (1.08, 0.98, 0.88), (0.86, 0.90, 1.02)
for nm in ('concrete_quay', 'asphalt'):
    vary(nm, (0.80, 0.78, 0.76), (1.12, 1.02, 0.90), 0.04)          # ~25 m stains / sun-bleached patches
for nm in ('painted_metal_233542_w54_s94_c64', 'painted_metal_8e9393_w29_s44_c49', 'galvanised',
           'painted_metal_bcb7a8_w34_s29_c44', 'painted_metal_b2b2aa_w34_s49_c44', 'painted_metal_bfbfb7_w15_s07_c34',
           'painted_metal_bfbfb7_w20_s11_c59', 'painted_metal_bfbfb7_w33_s29_c34', 'painted_metal_bfbfb7_w47_s47_c59'):
    vary(nm, COOL, WARM, 0.25)                                       # ~4 m paint fade / chalking

# ---- grade (view look + harbour haze + colour balance / bloom / vignette)
look.apply(S, 'port')             # AgX Punchy + grade, no world fog
# grade identical to reefer.py (lead, BRIDGE_SEA match): complementary cool lift / warm gain, exposure +0.9
look.grade(S, lift='#3a5b8c', gain='#ff9a5c', sat=1.10, contrast=2.0, bloom=0.15, vignette=0.10, lift_amt=0.012, gain_amt=0.015)
S.view_settings.exposure = 0.9
# ---- lead fix (f132/f204 front faces crushed to navy): mid-shot lift only. Bridges keep the exact values above:
# f1-12 (BRIDGE_SEA, reefer match) and f256-264 (BRIDGE_DOOR, plant-cold match) are untouched.
# Sky bounce = a no-shadow sun parented to the camera, shining along the view: lights whatever faces the camera
# (a fixed area light cannot follow a 60 m -> 1 m camera move).
cam = S.camera
bounce = look.add_light(S, 'SK_SkyBounce', 'SUN', '#8a7fb0', 0.0, (0, 0, 0), shadow=False)
bounce.parent = cam
bounce.data.angle = 30 * D2R
MID_FILL, MID_BOUNCE, MID_EXP = 9.0, BOUNCE_E, 1.45
for f, fill_e, b_e, ex in ((12, 4.0, 0.0, 0.9), (30, MID_FILL, MID_BOUNCE, MID_EXP), (240, MID_FILL, MID_BOUNCE, MID_EXP),
                           (256, 4.0, 0.0, 0.9)):
    FILL.data.energy = fill_e
    FILL.data.keyframe_insert('energy', frame=f)
    bounce.data.energy = b_e
    bounce.data.keyframe_insert('energy', frame=f)
    S.view_settings.exposure = ex
    S.view_settings.keyframe_insert('exposure', frame=f)
S.frame_set(1)
print('port_art: dusk pass applied')
