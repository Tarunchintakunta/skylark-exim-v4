"""Skylark v4 art-direction helpers (docs/COLOR_SCRIPT.md, issue #75). Blender 5.2 (compositor = scene.compositing_node_group).

    import sys; sys.path.insert(0, REPO + '/assets-src/blender/lib'); import look
    look.apply(scene, 'v-sea')          # light colours are the scene builder's job; this sets world tint, fog, view look and grade
    look.grade(scene, lift='#0f3d4a', gain='#ffb070', sat=1.12)   # or call the parts directly

Rules: colour comes from light and world, never a full-frame tint (QUALITY_GATES G-SCENE-8); vignette <= 0.12; no baked grain
(the web layer adds grain). One grade per .blend so chained clips stay identical at their internal joins.
"""
import bpy


def hex_rgb(h, linear=True):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    if linear:
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return tuple(c)


def _tint(h, amount):
    """A colour-balance offset around neutral: 1 + amount * (normalised hue - 1)."""
    r, g, b = hex_rgb(h, linear=False)
    m = max(r, g, b) or 1
    v = [1 + amount * (x / m - 1) for x in (r, g, b)]
    lum = 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]  # keep luminance: hue shift only, no darkening
    return tuple(x / lum for x in v)


def view(scene, look_name='AgX - Punchy', exposure=0.0):
    vs = scene.view_settings
    vs.view_transform = 'AgX'
    try:
        vs.look = look_name
    except TypeError:
        vs.look = 'AgX - Medium High Contrast'
    vs.exposure = exposure


def light(obj_or_name, hex_colour, energy=None):
    """Colour an existing light (sun/area/point/spot) by hex; optionally set its energy."""
    o = bpy.data.objects[obj_or_name] if isinstance(obj_or_name, str) else obj_or_name
    o.data.color = hex_rgb(hex_colour)
    if energy is not None:
        o.data.energy = energy
    return o


def add_light(scene, name, kind, hex_colour, energy, location, rotation=(0, 0, 0), size=1.0, shadow=True):
    """Add a key / fill / rim light. kind: 'SUN' | 'AREA' | 'SPOT' | 'POINT'."""
    d = bpy.data.lights.new(name, kind)
    d.color = hex_rgb(hex_colour)
    d.energy = energy
    if kind == 'AREA':
        d.size = size
    if hasattr(d, 'use_shadow'):
        d.use_shadow = shadow
    o = bpy.data.objects.new(name, d)
    o.location, o.rotation_euler = location, rotation
    scene.collection.objects.link(o)
    return o


def fog(scene, hex_colour, density, anisotropy=0.2):
    """WARNING: world volume = absorbs the sky/sun everywhere (black exteriors). Interiors only, tiny densities.
    Light world volume for depth (EEVEE volumetrics). density ~0.0005 (exterior) .. 0.008 (cold vapour)."""
    w = scene.world
    w.use_nodes = True
    nt = w.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
    vol = nt.nodes.get('SK_FOG') or nt.nodes.new('ShaderNodeVolumePrincipled')
    vol.name = 'SK_FOG'
    vol.inputs['Color'].default_value = (*hex_rgb(hex_colour), 1)
    vol.inputs['Density'].default_value = density
    vol.inputs['Anisotropy'].default_value = anisotropy
    nt.links.new(vol.outputs['Volume'], out.inputs['Volume'])
    e = scene.eevee
    for a, v in (('volumetric_tile_size', '8'), ('volumetric_samples', 32), ('volumetric_end', 2000.0)):
        if hasattr(e, a):
            try:
                setattr(e, a, v)
            except Exception:
                pass


def grade(scene, lift='#202020', gain='#ffffff', sat=1.1, contrast=2.0, bloom=0.15, vignette=0.1, lift_amt=0.025, gain_amt=0.03):
    """Compositor grade: colour balance (lift into the dominant hue, gain toward the key) -> saturation -> contrast ->
    gentle bloom on highlights -> light vignette (<= 0.12). Replaces any previous SK grade on this scene."""
    vignette = min(vignette, 0.12)
    name = 'SK_GRADE_' + scene.name
    old = bpy.data.node_groups.get(name)
    if old:
        bpy.data.node_groups.remove(old)
    t = bpy.data.node_groups.new(name, 'CompositorNodeTree')
    t.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    N = t.nodes.new
    rl = N('CompositorNodeRLayers')
    rl.scene = scene
    cb = N('CompositorNodeColorBalance')
    lift_v, gain_v = _tint(lift, lift_amt * 10), _tint(gain, gain_amt * 10)
    # 5.x exposes Lift/Gamma/Gain as sockets (colour + float pairs); set the colour ones.
    for s in cb.inputs:
        if s.name == 'Lift' and s.type == 'RGBA':
            s.default_value = (*lift_v, 1)
        if s.name == 'Gain' and s.type == 'RGBA':
            s.default_value = (*gain_v, 1)
    hs = N('CompositorNodeHueSat')
    hs.inputs['Saturation'].default_value = sat
    bc = N('CompositorNodeBrightContrast')
    bc.inputs['Contrast'].default_value = contrast
    gl = N('CompositorNodeGlare')
    try:
        gl.inputs['Type'].default_value = 'Bloom'
    except Exception:
        pass
    gl.inputs['Threshold'].default_value = 1.5  # 1.0 + size 0.5 spread warm highlights into a full-frame wash (table r2)
    gl.inputs['Strength'].default_value = bloom
    if 'Size' in gl.inputs:
        try:
            gl.inputs['Size'].default_value = 0.15
        except Exception:
            pass
    em = N('CompositorNodeEllipseMask')
    em.inputs['Size'].default_value = (0.95, 0.95)
    em.inputs['Value'].default_value = 1.0
    bl = N('CompositorNodeBlur')
    bl.inputs['Size'].default_value = (420, 420)
    mx = N('ShaderNodeMix')
    mx.data_type = 'RGBA'
    mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = vignette
    out = N('NodeGroupOutput')
    L = t.links.new
    L(rl.outputs['Image'], cb.inputs['Image'])
    L(cb.outputs['Image'], hs.inputs['Image'])
    L(hs.outputs['Image'], bc.inputs['Image'])
    L(bc.outputs['Image'], gl.inputs['Image'])
    L(em.outputs['Mask'], bl.inputs['Image'])
    a = [s for s in mx.inputs if s.name == 'A' and s.type == 'RGBA'][0]
    b = [s for s in mx.inputs if s.name == 'B' and s.type == 'RGBA'][0]
    L(gl.outputs['Image'], a)
    L(bl.outputs['Image'], b)
    res = [s for s in mx.outputs if s.type == 'RGBA'][0]
    L(res, out.inputs[0])
    scene.compositing_node_group = t
    if hasattr(scene.render, 'use_compositing'):
        scene.render.use_compositing = True
    return t


# Per-clip presets from docs/COLOR_SCRIPT.md §1/§3 (lift = dominant, gain = key colour).
PRESETS = {
    'table':      dict(look='AgX - Medium High Contrast', lift='#3a1f14', gain='#ffb46b', sat=1.12, fog=('#ffcf9a', 0.002)),
    'reefer':     dict(look='AgX - Punchy', lift='#123a5a', gain='#ff9a5c', sat=1.10, fog=('#cfe6f2', 0.002)),
    'port':       dict(look='AgX - Punchy', lift='#2b2147', gain='#ff8c4a', sat=1.12, fog=('#c98a7a', 0.0006)),
    'plant-cold': dict(look='AgX - Medium High Contrast', lift='#1e2a4f', gain='#cfe0ff', sat=1.10, fog=('#b9c8ff', 0.004)),
    'plant-line': dict(look='AgX - Medium High Contrast', lift='#2a4a6e', gain='#ffd59a', sat=1.10, fog=('#d0e4f2', 0.0015)),
    'truck':      dict(look='AgX - Punchy', lift='#4f7f4a', gain='#ffc98a', sat=1.10, fog=('#e8d2b0', 0.0005)),
    'pond':       dict(look='AgX - Punchy', lift='#2f6e68', gain='#ffcf7a', sat=1.12, fog=('#f4e2c0', 0.002)),
    'sea':        dict(look='AgX - Punchy', lift='#0f3d4a', gain='#ffb070', sat=1.12, fog=('#f0c9a0', 0.0006)),
    'prod-tuna':  dict(look='AgX - Medium High Contrast', lift='#0f1d33', gain='#e6f2ff', sat=1.06, fog=None),
    'prod-prawn': dict(look='AgX - Medium High Contrast', lift='#0f1d33', gain='#e6f2ff', sat=1.06, fog=None),
}


def apply(scene, blend):
    """View look + grade only. World fog is NOT applied: a world volume makes EEVEE absorb the whole sky and sun
    (truck round 1 went black, luma 3-11). Get depth haze per material (distance mix toward the row's fog colour) or
    from a bounded volume object around the subject instead; use fog() only for small closed interiors."""
    p = PRESETS[blend]
    view(scene, p['look'])
    grade(scene, lift=p['lift'], gain=p['gain'], sat=p['sat'])
