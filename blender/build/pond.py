"""S5 pond.blend -> v-pond (1-216, dawn). Coastal Andhra shrimp farm at sunrise.
Run: Blender --factory-startup -b --python pond.py   (env POND_FAST=1 skips people + grass for quick layout tests)

World: metres, Z up, +X = east, sea level z=0. Pond water W=1.5, bund top 2.6, land 1.8. Coast runs NNE (sea to ESE).
f1 = BRIDGE_COAST (300 m, 24 mm, pitch -35, heading east), f216 = BRIDGE_HORIZON (3 m above sea, 35 mm, az 95,
horizon at 46 %, sun 4 deg in frame, sklib.ocean seed 41 calm).
"""
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

REPO = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4'
sys.path.insert(0, REPO + '/assets-src/blender/lib')
import sklib  # noqa: E402
import look  # noqa: E402
from sklib import _n, _l, _img, _mix, _maprange, _noise, _math, _new_mat, _vscale  # noqa: E402

FAST = os.environ.get('POND_FAST') == '1'
D2R = math.pi / 180
W, TOP, LAND = 1.5, 2.6, 1.8                 # pond water level, bund top, surrounding land (m above sea)
HX, HY = -3.9, -10.0                          # harvest bag (east bund of the SE pond)
CAM_END = Vector((9.4, -12.0, 3.0))

s = sklib.reset()
s.frame_start, s.frame_end = 1, 216
RNG = random.Random(5)


def C(name, parent=None):
    return sklib.collection(name, parent)


def obj(name, bm, coll, mats=(), uv=True, smooth=False):
    ob = sklib._mesh_obj(name, bm, coll)
    if mats:
        sklib.mat_to(ob, *mats, uv=uv)
    if smooth:
        ob.data.shade_smooth()
    return ob


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def drive(idb, path, expr, index=-1):
    d = idb.driver_add(path, index) if index >= 0 else idb.driver_add(path)
    d.driver.type, d.driver.expression = 'SCRIPTED', expr
    return d


# ======================================================================================================== sky + sun
world, SUN = sklib.sky_world(sun_elev_deg=15, sun_az_deg=90, strength=1.05)
nt = world.node_tree
sky = [n for n in nt.nodes if n.type == 'TEX_SKY'][0]
bg = [n for n in nt.nodes if n.type == 'BACKGROUND'][0]
sky_cam = nt.nodes.new('ShaderNodeTexSky')       # camera rays see the sun disc; lighting uses the disc-less sky
for a in ('sky_type', 'air_density', 'aerosol_density', 'ozone_density', 'sun_elevation', 'sun_rotation'):
    setattr(sky_cam, a, getattr(sky, a))
sky_cam.sun_disc = True
sky_cam.sun_size = 0.6 * D2R
lp = nt.nodes.new('ShaderNodeLightPath')
mx = nt.nodes.new('ShaderNodeMix')
mx.data_type = 'RGBA'
nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs['Factor'])
nt.links.new(sky.outputs[0], mx.inputs[6])
nt.links.new(sky_cam.outputs[0], mx.inputs[7])
nt.links.new(mx.outputs[2], bg.inputs[0])
world.sun_threshold = 1e6 if hasattr(world, 'sun_threshold') else 0


# art pass (COLOR_SCRIPT row 11): hue-only tints on the physical sky, horizon -> zenith by ray elevation.
# camera rays: sunrise horizon #ffd98f (f216 BRIDGE_HORIZON #ffbf7a) -> zenith #3f6f9a;
# lighting/reflections: same warm horizon (the sea and ponds mirror it) -> world colour #7fb6c8 overhead (cool fill).
def _hue(h, k):
    c = look.hex_rgb(h)
    lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    return tuple(1 + k * (x / lum - 1) for x in c) + (1,)


def _sea_tint(h, gain=1.0, mix=0.85):
    """sea.py's dawn tint (max-normalised, mix 0.85): f216 matches sea f1 (BRIDGE_HORIZON)."""
    c = look.hex_rgb(h)
    m = max(c)
    return tuple(1 - mix + mix * gain * x / m for x in c) + (1,)


def sky_tint(src, keys, x):
    """keys: (frame, horizon rgba, zenith rgba, gradient top in ray-Z)."""
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs['From Min'].default_value = 0.0
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    hz, zn = nt.nodes.new('ShaderNodeRGB'), nt.nodes.new('ShaderNodeRGB')
    hz.name, zn.name = 'SK_HORIZON_' + x, 'SK_ZENITH_' + x
    g = nt.nodes.new('ShaderNodeMix')
    g.data_type = 'RGBA'
    nt.links.new(mr.outputs[0], g.inputs['Factor'])
    nt.links.new(hz.outputs[0], g.inputs[6])
    nt.links.new(zn.outputs[0], g.inputs[7])
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type, mul.blend_type = 'RGBA', 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    nt.links.new(src, mul.inputs[6])
    nt.links.new(g.outputs[2], mul.inputs[7])
    for f_, h_, z_, top in keys:
        hz.outputs[0].default_value, zn.outputs[0].default_value = h_, z_
        mr.inputs['From Max'].default_value = top
        hz.outputs[0].keyframe_insert('default_value', frame=f_)
        zn.outputs[0].keyframe_insert('default_value', frame=f_)
        mr.inputs['From Max'].keyframe_insert('default_value', frame=f_)
    return mul.outputs[2]


# f1-150 row 11 tints; f216 = sea f1's gradient (horizon #ffbf7a -> zenith #24496b) on both camera and lighting rays
END_KEY = (216, _sea_tint('#ffbf7a'), _sea_tint('#24496b', 0.45), 0.24)
nt.links.new(sky_tint(sky.outputs[0], [(1, _hue('#ffd98f', 0.45), _hue('#7fb6c8', 0.45), 0.5),
                                        (150, _hue('#ffd98f', 0.45), _hue('#7fb6c8', 0.45), 0.5), END_KEY], 'L'), mx.inputs[6])
nt.links.new(sky_tint(sky_cam.outputs[0], [(1, _hue('#ffd98f', 0.45), _hue('#3f6f9a', 0.5), 0.5),
                                            (150, _hue('#ffd98f', 0.45), _hue('#3f6f9a', 0.5), 0.5), END_KEY], 'C'), mx.inputs[7])


def sun_at(f, el, az, hexc):
    for n in (sky, sky_cam):
        n.sun_elevation, n.sun_rotation = el * D2R, az * D2R
        n.keyframe_insert('sun_elevation', frame=f)
        n.keyframe_insert('sun_rotation', frame=f)
    e, a = el * D2R, az * D2R
    d = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    SUN.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    SUN.keyframe_insert('rotation_euler', frame=f)
    SUN.data.color = look.hex_rgb(hexc)
    SUN.data.energy = 6.0 * 1.25 * max(0.15, math.sin(e)) ** 0.5
    SUN.data.keyframe_insert('color', frame=f)
    SUN.data.keyframe_insert('energy', frame=f)


sun_at(1, 15, 90, '#ffcf7a')    # BRIDGE_COAST (truck #ffc98a, same hue family)
sun_at(216, 4, 95, '#ffb070')   # BRIDGE_HORIZON
sklib.ease_keys(SUN, SUN.data)
# cool fill from the west sky (behind camera for most of the shot) + warm low rim for palms / net / crew edges
FILL = look.add_light(s, 'SK_FILL', 'SUN', '#7fb6c8', 0.9, (0, 0, 50), (math.radians(55), 0, math.radians(-95)), shadow=False)
RIM = look.add_light(s, 'SK_RIM', 'SUN', '#ffe0a0', 1.6, (0, 0, 50), (math.radians(80), 0, math.radians(70)), shadow=False)
FILL.data.angle = RIM.data.angle = 0.2
FILL.data.specular_factor = RIM.data.specular_factor = 0.0   # no extra sun glints on the water


# ===================================================================================================== pond layout
def grid_ponds(x_east, y_south, cols, rows, wx, wy, gap=6.2):
    out = []
    for c in range(cols):
        for r in range(rows):
            x1 = x_east - (cols - 1 - c) * (wx + gap)
            y0 = y_south + r * (wy + gap)
            out.append((x1 - wx, x1, y0, y0 + wy))
    return out


NEAR = grid_ponds(-4.0, -20.0, 4, 4, 52.0, 38.0)          # 16 ponds; harvest = col 3 row 0 = NEAR[12]
DRY = {3}                                                   # col 0 row 3 drained (variety)
FAR = grid_ponds(-180.0, 205.0, 5, 3, 55.0, 40.0) + grid_ponds(30.0, 222.0, 3, 4, 48.0, 36.0) + \
    grid_ponds(-330.0, -150.0, 3, 3, 60.0, 45.0)
PONDS = NEAR + FAR


def coast_b(y):
    """0 at the farm (y -60..10: the end shot needs open sea right off the east bund), 1 away from it."""
    return ss(10.0, 170.0, y) + ss(-60.0, -160.0, y)


def shore_x(y):
    # full-r2: away from the farm the coast follows truck.blend's BRIDGE_COAST (x = 900 + 0.5 y there; the truck
    # f216 camera (260, -110) maps onto ours (-560, -60) -> x = 55 + 0.5 y here), with a sand beach + casuarina belt
    near = 7.0 + 0.2 * (y + 10) + 1.0 * np.sin(y / 37.0) + 0.6 * np.sin(y / 13.0 + 1.0)
    return near + (55.0 + 0.5 * y - near) * coast_b(y)


def axis(lo, hi, req, base, far_c, far_r):
    """Sorted coords: required lines + fill whose max spacing grows away from [far_c +- far_r]."""
    req = sorted(set(round(v, 3) for v in req if lo <= v <= hi) | {lo, hi})
    out = [req[0]]
    for a, b in zip(req, req[1:]):
        mid = (a + b) / 2
        sp = base + 0.06 * max(0.0, abs(mid - far_c) - far_r)
        sp = min(sp, 30.0)
        n = max(1, int(math.ceil((b - a) / sp)))
        out += [a + (b - a) * k / n for k in range(1, n + 1)]
    return np.array(out)


def build_terrain(coll):
    near_off = [-1.6, -1.2, -0.8, -0.4, 0, 0.3, 0.6, 0.9, 1.2, 1.6, 1.9, 2.3, 2.45, 2.6, 2.75, 2.9, 3.1, 3.3,
                3.6, 3.85, 4.0, 4.15, 4.4, 4.7, 5.0, 5.4, 5.8, 6.2, 6.6, 7.2]
    far_off = [-1.6, -0.8, 0, 0.8, 1.6, 3.1, 5.0, 6.6]
    rx, ry = [], []
    for i, (x0, x1, y0, y1) in enumerate(PONDS):
        offs = near_off if i < len(NEAR) else far_off
        for d in offs:
            rx += [x0 - d, x1 + d]
            ry += [y0 - d, y1 + d]
    rx += list(np.arange(-14.0, 14.0, 0.25))                # harvest close-up zone
    ry += list(np.arange(-24.0, 0.0, 0.25))
    xs = axis(-900.0, 640.0, rx, 1.6, -100.0, 140.0)
    ys = axis(-900.0, 900.0, ry, 1.6, 60.0, 120.0)
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    X32, Y32 = X.ravel().astype(np.float64), Y.ravel().astype(np.float64)
    n = X32.size
    print('terrain verts', len(xs), len(ys), n)
    best = np.full(n, 1e9)
    second = np.full(n, 1e9)
    who = np.full(n, -1)
    for i, (x0, x1, y0, y1) in enumerate(PONDS):
        dx = np.maximum(x0 - X32, X32 - x1)
        dy = np.maximum(y0 - Y32, Y32 - y1)
        d = np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) + np.minimum(np.maximum(dx, dy), 0)
        nb = d < best
        second = np.where(nb, best, np.minimum(second, d))
        who = np.where(nb, i, who)
        best = np.where(nb, d, best)
    d = best
    interior = second < 7.0
    t = np.clip(d / 1.6, -1, 1)
    z = np.where(d <= 1.6, W + 1.1 * np.tanh(1.5 * t) / np.tanh(1.5), TOP)
    z = np.where(d > 5.0, TOP - 0.8 * ss(5.0, 6.6, d), z)
    # undulation
    rr = np.random.RandomState(3)
    und = np.zeros(n)
    for k in range(7):
        f = 0.004 * 2.1 ** k
        a = rr.uniform(0, 6.28, 2)
        th = rr.uniform(0, 6.28)
        und += (0.5 ** k) * np.sin(f * (X32 * math.cos(th) + Y32 * math.sin(th)) + a[0]) * np.cos(
            f * 1.3 * (X32 * math.sin(th) - Y32 * math.cos(th)) + a[1])
    micro = np.sin(X32 * 1.7 + np.sin(Y32 * 0.9)) * np.sin(Y32 * 1.3 + np.sin(X32 * 0.7))
    onbund = (d > 1.4) & (d < 6.8)
    # r5: real relief away from the farms (gentle rises/hollows up to ~2 m; ponds + bunds stay level)
    relief = 0.12 + 1.3 * ss(12.0, 90.0, d)
    z = z + np.where(d > 6.6, relief * und, 0) + np.where(onbund, 0.025 * und + 0.012 * micro, 0)
    g = lambda v, w: np.exp(-(v / w) ** 2)
    outer = ~interior & (d > 1.6) & (d < 5.0)
    rut = np.where(outer, g(d - 2.75, 0.17) + g(d - 4.0, 0.17), 0.0)
    z -= 0.075 * rut
    z += np.where(onbund & (d < 5.0), 0.05 * g(d - 3.2, 0.9), 0)          # crowned top
    path = np.where(interior & (d > 1.6), g(d - 3.1, 0.38), 0.0) + np.where(outer, 0.35 * g(d - 3.4, 1.0), 0)
    # beach / sea
    sdist = (X32 - shore_x(Y32)) * 0.944
    zb = np.maximum(np.where(sdist < 0, -0.6 * sdist, -0.2 * sdist), -3.0)        # embankment, then shelving sea bed
    beach = ss(0.0, 0.35, z - zb) * (zb < z + 0.4)
    z = np.minimum(z, zb)
    # full-r2: wide sand beach (truck: 72 m) sloping to the waterline, only where coast_b > 0
    cb = coast_b(Y32)
    sd = (X32 - shore_x(Y32)) * 0.894
    sand = ss(-86.0, -74.0, sd) * cb
    z = np.where(sand > 0, np.minimum(z, z * (1 - sand) + sand * (0.25 + 0.019 * np.maximum(0.0, -sd))), z)
    beach = np.maximum(beach, sand)
    wet = np.where(d < 6.0, 1 - ss(0.05, 0.4, d), 0) * (d > -0.6)
    bed = ss(-0.15, -0.6, d)
    dry = np.isin(who, list(DRY)) & (d < 1.2)
    nearfarm = np.hypot(np.maximum(0, np.abs(X32 + 90) - 100), np.maximum(0, np.abs(Y32 + 8) - 30))
    grass = (1 - ss(10, 60, nearfarm)) * (1 - beach) * (1 - ss(0.15, 0.6, wet)) * (d > 0.5) * (1 - 0.8 * path)
    grass *= np.clip(1 - rut * 2, 0, 1)
    # ponytail: tufts only where the low camera can resolve them (path f90-216); texture carries the rest
    px, py = np.clip(X32, -95.0, 8.0), -5.0 - (np.clip(X32, -95.0, 8.0) + 95.0) * (7.0 / 103.0)
    near_path = np.hypot(X32 - px, Y32 - py)
    grass *= 0.03 + 0.97 * (1 - ss(12.0, 30.0, near_path))
    grass *= 1 - (np.abs(Y32 + 45.0) < 6.5) * (X32 < -22.0)          # full-r2: farm road corridor
    # mesh
    nx, ny = len(xs), len(ys)
    me = bpy.data.meshes.new('A-ENV-PONDS')
    me.vertices.add(n)
    me.vertices.foreach_set('co', np.stack([X32, Y32, z], 1).astype(np.float32).ravel())
    ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing='ij')
    a = (ii * ny + jj).ravel()
    quads = np.stack([a, a + ny, a + ny + 1, a + 1], 1)
    nq = len(quads)
    me.loops.add(nq * 4)
    me.loops.foreach_set('vertex_index', quads.astype(np.int32).ravel())
    me.polygons.add(nq)
    me.polygons.foreach_set('loop_start', np.arange(0, nq * 4, 4, dtype=np.int32))
    me.update()
    me.validate()
    field = ss(9.0, 22.0, d) * (1 - beach) * ss(6.0, 14.0, near_path)
    for nm, arr in (('path', path), ('rut', rut), ('beach', beach), ('wet', wet), ('bed', bed),
                    ('dry', dry.astype(float)), ('grass', grass), ('und', und), ('field', field)):
        at = me.attributes.new(nm, 'FLOAT', 'POINT')
        at.data.foreach_set('value', np.clip(arr, -5, 5).astype(np.float32))
    ob = sklib.new_obj('A-ENV-PONDS', me, coll)
    sklib.mat_to(ob, terrain_mat())
    me.shade_smooth()
    return ob


def height_at(x, y):
    """Terrain height at (x, y) from the evaluated mesh (ray cast down)."""
    ok, loc, nrm, idx = TERRAIN.ray_cast(Vector((x, y, 50.0)), Vector((0, 0, -1)))
    return loc.z if ok else LAND


# ======================================================================================================= materials
def tex_layer(nt, slug, size_m, uvnode, x, y, res='1k'):
    t = sklib.tex(slug, res)
    k = 1.0 / (t['size_m'] * size_m)
    uv = _vscale(nt, uvnode.outputs['UV'], k, k, k, x - 300, y)
    di = _img(nt, t['diff'], True, uv, x, y)
    ro = _img(nt, t['rough'], False, uv, x, y - 260)
    no = _img(nt, t['nor'], False, uv, x, y - 520)
    return [di.outputs['Color'], ro.outputs['Color'], no.outputs['Color']]


def mix3(nt, fac, a, b, x, y):
    out = []
    for i in range(3):
        out.append(_mix(nt, fac, a[i], b[i], 'MIX', x, y - i * 200))
    return out


def attr(nt, name, x, y):
    return _n(nt, 'ShaderNodeAttribute', x, y, attribute_name=name).outputs['Fac']


def terrain_mat():
    m, nt = _new_mat('pond_terrain')
    out = _n(nt, 'ShaderNodeOutputMaterial', 3200, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 2900, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -2400, 0)
    grass = tex_layer(nt, 'leafy_grass', 1.0, tc, -1800, 1600)
    mud = tex_layer(nt, 'brown_mud_03', 1.0, tc, -1800, 800)
    ruts = tex_layer(nt, 'muddy_tracks', 1.0, tc, -1800, 0)
    sand = tex_layer(nt, 'damp_sand', 1.0, tc, -1800, -800)
    cracked = tex_layer(nt, 'mud_cracked_dry_03', 1.0, tc, -1800, -1600)
    path = tex_layer(nt, 'grass_path_2', 1.0, tc, -1800, -2400)
    # macro field variation: fresh green / olive / dry straw patches
    nz = _noise(nt, tc.outputs['Object'], 0.012, 4.0, 0.55, -1500, 2400)
    nz2 = _noise(nt, tc.outputs['Object'], 0.05, 3.0, 0.6, -1500, 2100)
    macro = _mix(nt, _maprange(nt, nz.outputs['Fac'], 0.35, 0.65, 0, 1, -1200, 2400),
                 (0.55, 0.85, 0.42), (1.05, 0.95, 0.62), 'MIX', -1000, 2400)
    macro = _mix(nt, _maprange(nt, nz2.outputs['Fac'], 0.45, 0.7, 0, 0.5, -1200, 2100), macro, (0.85, 0.75, 0.5),
                 'MIX', -800, 2300)
    bw = _n(nt, 'ShaderNodeRGBToBW', -1300, 1900)
    _l(nt, grass[0], bw.inputs[0])
    green = _mix(nt, 1.0, bw.outputs[0], (0.42, 0.62, 0.2), 'MULTIPLY', -1100, 1900)
    green = _mix(nt, 0.3, green, grass[0], 'MIX', -950, 1900)
    # r5: rectangular field patchwork (paddy / pasture / straw / ploughed) with field bunds + farm tracks, away
    # from the pond farms only (attribute 'field'); replaces the polygon Voronoi patches that read as CG
    fmask = attr(nt, 'field', -1500, 3600)
    osep = _n(nt, 'ShaderNodeSeparateXYZ', -2100, 3600)
    _l(nt, tc.outputs['Object'], osep.inputs[0])
    ca, sa = math.cos(0.21), math.sin(0.21)
    U = _math(nt, 'MULTIPLY_ADD', osep.outputs['X'], ca, x=-1900, y=3700, c=_math(nt, 'MULTIPLY', osep.outputs['Y'], sa, x=-2000, y=3800))
    V = _math(nt, 'MULTIPLY_ADD', osep.outputs['Y'], ca, x=-1900, y=3500, c=_math(nt, 'MULTIPLY', osep.outputs['X'], -sa, x=-2000, y=3400))
    uq = _math(nt, 'DIVIDE', U, 28.0, x=-1750, y=3700)
    cu = _math(nt, 'FLOOR', uq, x=-1600, y=3700)
    vq = _math(nt, 'DIVIDE', _math(nt, 'MULTIPLY_ADD', cu, 23.0, x=-1600, y=3500, c=V), 40.0, x=-1450, y=3500)
    cv = _math(nt, 'FLOOR', vq, x=-1300, y=3500)
    cc = _n(nt, 'ShaderNodeCombineXYZ', -1150, 3600)
    _l(nt, cu, cc.inputs['X'])
    _l(nt, cv, cc.inputs['Y'])
    wn = _n(nt, 'ShaderNodeTexWhiteNoise', -1000, 3600, noise_dimensions='3D')
    _l(nt, cc.outputs[0], wn.inputs['Vector'])
    rsep = _n(nt, 'ShaderNodeSeparateColor', -850, 3700)
    _l(nt, wn.outputs['Color'], rsep.inputs[0])
    ramp = _n(nt, 'ShaderNodeValToRGB', -700, 3800)
    ramp.color_ramp.interpolation = 'CONSTANT'
    pal = [(0.0, (0.5, 1.12, 0.42)), (0.22, (0.66, 1.05, 0.45)), (0.4, (0.85, 1.0, 0.5)), (0.55, (1.0, 0.98, 0.55)),
           (0.7, (1.3, 1.08, 0.62)), (0.84, (0.58, 0.98, 0.5))]
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = pal[0][0], pal[0][1] + (1,)
    els[1].position, els[1].color = pal[1][0], pal[1][1] + (1,)
    for p_, c_ in pal[2:]:
        e_ = els.new(p_)
        e_.color = c_ + (1,)
    _l(nt, rsep.outputs[0], ramp.inputs['Fac'])
    # crop rows in about half the fields
    rows = _math(nt, 'SINE', _math(nt, 'MULTIPLY', V, 2 * math.pi / 1.1, x=-1000, y=3300), x=-850, y=3300)
    rows = _maprange(nt, rows, -1, 1, 0.82, 1.0, -700, 3300)
    rowsel = _maprange(nt, rsep.outputs[1], 0.48, 0.52, 0.0, 1.0, -700, 3150)
    rc = _n(nt, 'ShaderNodeCombineColor', -400, 3300)
    for ch in ('Red', 'Green', 'Blue'):
        _l(nt, rows, rc.inputs[ch])
    rowk = _mix(nt, rowsel, (1, 1, 1), rc.outputs[0], 'MIX', -250, 3300)
    ftint = _mix(nt, 1.0, ramp.outputs['Color'], rowk, 'MULTIPLY', -100, 3600)
    field = _mix(nt, fmask, (1, 1, 1), ftint, 'MIX', 50, 3600)
    macro = _mix(nt, 1.0, macro, field, 'MULTIPLY', -700, 2500)
    # bunds between fields (thin grassy ridges) + tracks along every third column line
    eu = _math(nt, 'MULTIPLY', _math(nt, 'MINIMUM', _math(nt, 'FRACT', uq, x=-1450, y=3950),
                                     _math(nt, 'SUBTRACT', 1.0, _math(nt, 'FRACT', uq, x=-1450, y=4050), x=-1300, y=4050),
                                     x=-1150, y=4000), 28.0, x=-1000, y=4000)
    ev = _math(nt, 'MULTIPLY', _math(nt, 'MINIMUM', _math(nt, 'FRACT', vq, x=-1450, y=4150),
                                     _math(nt, 'SUBTRACT', 1.0, _math(nt, 'FRACT', vq, x=-1450, y=4250), x=-1300, y=4250),
                                     x=-1150, y=4200), 40.0, x=-1000, y=4200)
    FBUND = _math(nt, 'MULTIPLY', _maprange(nt, _math(nt, 'MINIMUM', eu, ev, x=-850, y=4100), 0.3, 0.75, 1.0, 0.0, -700, 4100),
                  fmask, x=-550, y=4100)
    ru = _math(nt, 'FRACT', _math(nt, 'DIVIDE', U, 126.0, x=-1600, y=4400), x=-1450, y=4400)
    er = _math(nt, 'MULTIPLY', _math(nt, 'MINIMUM', ru, _math(nt, 'SUBTRACT', 1.0, ru, x=-1300, y=4450), x=-1150, y=4400),
               126.0, x=-1000, y=4400)
    FROAD = _math(nt, 'MULTIPLY', _maprange(nt, er, 1.5, 2.3, 1.0, 0.0, -850, 4400), fmask, x=-700, y=4400)
    FBARE = _math(nt, 'MULTIPLY', _maprange(nt, rsep.outputs[2], 0.3, 0.27, 0.0, 1.0, -700, 3950), fmask, x=-550, y=3950)
    gcol = _mix(nt, 1.0, green, macro, 'MULTIPLY', -700, 1700)
    grass = [_math(nt, 'MULTIPLY', gcol, 1.0, x=-600, y=1700) if False else gcol, grass[1], grass[2]]
    # slope -> bare earth on bund faces
    geo = _n(nt, 'ShaderNodeNewGeometry', -1500, 3000)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -1300, 3000)
    _l(nt, geo.outputs['Normal'], sep.inputs[0])
    nb = _noise(nt, tc.outputs['Object'], 0.6, 5.0, 0.65, -1300, 3300)
    steep = _maprange(nt, sep.outputs['Z'], 0.96, 0.7, 0.0, 1.0, -1100, 3000)
    steep = _math(nt, 'MULTIPLY', steep, _maprange(nt, nb.outputs['Fac'], 0.35, 0.6, 0.25, 1.0, -1100, 3300), True,
                  -900, 3000)
    L = mix3(nt, steep, grass, mud, -400, 1600)
    pa = _math(nt, 'MULTIPLY', attr(nt, 'path', -1100, 600),
               _maprange(nt, nb.outputs['Fac'], 0.3, 0.6, 0.6, 1.2, -1100, 450), True, -900, 600)
    L = mix3(nt, pa, L, path, -200, 1000)
    L = mix3(nt, FBARE, L, [_mix(nt, 0.6, mud[0], (0.3, 0.15, 0.09), 'MIX', -300, 900), mud[1], mud[2]], -100, 900)
    L = mix3(nt, FBUND, L, [_mix(nt, 1.0, green, (0.9, 1.0, 0.8), 'MULTIPLY', -300, 850), grass[1], grass[2]], -50, 850)
    L = mix3(nt, FROAD, L, path, 0, 800)
    L = mix3(nt, _math(nt, 'MULTIPLY', attr(nt, 'rut', -900, 200), 1.6, True, -700, 200), L, ruts, 0, 600)
    wet = attr(nt, 'wet', -900, -200)
    wetmud = [_mix(nt, 1.0, mud[0], (0.5, 0.44, 0.36), 'MULTIPLY', -500, -200), mud[1], mud[2]]
    L = mix3(nt, wet, L, wetmud, 200, 200)
    bed = attr(nt, 'bed', -900, -500)
    sludge = [_mix(nt, 1.0, mud[0], (0.22, 0.28, 0.14), 'MULTIPLY', -500, -500), mud[1], mud[2]]
    L = mix3(nt, bed, L, sludge, 400, -200)
    L = mix3(nt, _math(nt, 'MULTIPLY', bed, attr(nt, 'dry', -900, -800), True, -700, -800), L, cracked, 600, -600)
    sbw = _n(nt, 'ShaderNodeRGBToBW', 400, -900)
    _l(nt, sand[0], sbw.inputs[0])
    sand = [_mix(nt, 1.0, sbw.outputs[0], (1.85, 1.75, 1.55), 'MULTIPLY', 600, -900), sand[1], sand[2]]
    L = mix3(nt, attr(nt, 'beach', -900, -1100), L, sand, 800, -1000)
    vm = _n(nt, 'ShaderNodeVectorMath', 1300, 300, operation='SCALE')
    _l(nt, L[0], vm.inputs[0])
    vm.inputs['Scale'].default_value = 1.0
    _l(nt, vm.outputs[0], b.inputs['Base Color'])
    r = _maprange(nt, L[1], 0.0, 1.0, 0.45, 1.0, 1300, 0)
    r = _math(nt, 'MULTIPLY', r, _maprange(nt, wet, 0, 1, 1.0, 0.6, 1300, -150), True, 1500, 0)
    _l(nt, r, b.inputs['Roughness'])
    nm = _n(nt, 'ShaderNodeNormalMap', 1500, -400)
    nm.inputs['Strength'].default_value = 1.2
    _l(nt, L[2], nm.inputs['Color'])
    _l(nt, nm.outputs[0], b.inputs['Normal'])
    return m


def water_mat():
    m, nt = _new_mat('pond_water')
    out = _n(nt, 'ShaderNodeOutputMaterial', 1200, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 800, 200)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    # r5: shrimp-pond water = plankton-green / silt-brown and turbid, wind-rippled; only ~1/4 transmits (refracted
    # view of the submerged net + legs, which fade toward the murk colour with depth in their own materials)
    b.inputs['Transmission Weight'].default_value = 0.26
    b.inputs['IOR'].default_value = 1.333
    b.inputs['Specular IOR Level'].default_value = 0.22
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    mp = _n(nt, 'ShaderNodeMapping', -700, 0)
    _l(nt, tc.outputs['Object'], mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = (1, 1, 1)
    drive(mp.inputs['Location'], 'default_value', 'frame*0.02', 0)
    mp2 = _n(nt, 'ShaderNodeMapping', -700, -300)
    _l(nt, tc.outputs['Object'], mp2.inputs['Vector'])
    mp2.inputs['Rotation'].default_value = (0, 0, 0.7)
    drive(mp2.inputs['Location'], 'default_value', 'frame*-0.035', 1)
    murk = _noise(nt, tc.outputs['Object'], 0.05, 4.0, 0.6, -500, 600)
    _l(nt, _mix(nt, _maprange(nt, murk.outputs['Fac'], 0.32, 0.68, 0, 1, -250, 600), (0.035, 0.14, 0.12),
                (0.08, 0.16, 0.10), 'MIX', 0, 600), b.inputs['Base Color'])
    rn = _noise(nt, mp.outputs[0], 0.06, 3.0, 0.5, -500, 300)
    _l(nt, _maprange(nt, rn.outputs['Fac'], 0.35, 0.65, 0.09, 0.28, -250, 300), b.inputs['Roughness'])
    wv = _noise(nt, mp.outputs[0], 1.4, 7.0, 0.62, -500, -100)
    wv2 = _noise(nt, _vscale(nt, mp2.outputs[0], 0.35, 1.0, 1.0, -550, -350), 2.6, 4.0, 0.55, -350, -350)
    gust = _noise(nt, mp.outputs[0], 0.035, 2.0, 0.5, -500, -600)        # cat's-paw gust patches
    h = _math(nt, 'MULTIPLY_ADD', wv2.outputs['Fac'], _maprange(nt, gust.outputs['Fac'], 0.4, 0.62, 0.25, 1.4, -250, -600),
              x=-100, y=-300, c=wv.outputs['Fac'])
    bp = _n(nt, 'ShaderNodeBump', 300, -200)
    bp.inputs['Strength'].default_value = 0.55
    bp.inputs['Distance'].default_value = 0.06
    _l(nt, h, bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    m.use_raytrace_refraction = True
    if hasattr(m, 'thickness_mode'):
        m.thickness_mode = 'SLAB'
    return m


def far_water_mat():
    """Distant ponds: opaque murky green with sky reflection (no volume beyond volumetric range anyway)."""
    m, nt = _new_mat('pond_water_far')
    out = _n(nt, 'ShaderNodeOutputMaterial', 800, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 500, 0)
    _l(nt, b.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', -700, 0)
    nz = _noise(nt, tc.outputs['Object'], 0.03, 3.0, 0.5, -500, 200)
    # r5: each pond its own bloom colour (bright plankton green .. silty olive-brown)
    pv = _n(nt, 'ShaderNodeTexVoronoi', -500, 450)
    pv.inputs['Scale'].default_value = 0.012
    _l(nt, tc.outputs['Object'], pv.inputs['Vector'])
    psep = _n(nt, 'ShaderNodeSeparateColor', -300, 450)
    _l(nt, pv.outputs['Color'], psep.inputs[0])
    pc = _mix(nt, psep.outputs[0], (0.03, 0.15, 0.12), (0.09, 0.16, 0.09), 'MIX', -100, 450)
    _l(nt, _mix(nt, _maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 0, 0.35, -300, 200), pc,
                (0.05, 0.13, 0.10), 'MIX', 100, 200), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.34
    b.inputs['Specular IOR Level'].default_value = 0.25
    return m


def leaf_mat(name, c1, c2, dead=(0.32, 0.22, 0.10), transl=0.35):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = _new_mat(name)
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 300, 100)
    tr = _n(nt, 'ShaderNodeBsdfTranslucent', 300, -200)
    ms = _n(nt, 'ShaderNodeMixShader', 650, 0)
    ms.inputs[0].default_value = transl
    _l(nt, b.outputs[0], ms.inputs[1])
    _l(nt, tr.outputs[0], ms.inputs[2])
    _l(nt, ms.outputs[0], out.inputs['Surface'])
    var = attr(nt, 'leafvar', -700, 200)
    dd = attr(nt, 'dead', -700, 0)
    col = _mix(nt, var, c1, c2, 'MIX', -400, 200)
    col = _mix(nt, dd, col, dead, 'MIX', -200, 150)
    _l(nt, col, b.inputs['Base Color'])
    tcol = _mix(nt, 1.0, col, (1.4, 1.5, 0.7), 'MULTIPLY', 0, -200)
    _l(nt, tcol, tr.inputs['Color'])
    b.inputs['Roughness'].default_value = 0.5
    tc = _n(nt, 'ShaderNodeTexCoord', -700, -300)
    nzz = _noise(nt, tc.outputs['Object'], 40.0, 4.0, 0.6, -500, -300)
    bp = _n(nt, 'ShaderNodeBump', 0, -450)
    bp.inputs['Strength'].default_value = 0.15
    _l(nt, nzz.outputs['Fac'], bp.inputs['Height'])
    _l(nt, bp.outputs[0], b.inputs['Normal'])
    m.use_backface_culling = False
    return m


def set_attr(me, name, vals, domain='FACE'):
    at = me.attributes.get(name) or me.attributes.new(name, 'FLOAT', domain)
    at.data.foreach_set('value', np.asarray(vals, np.float32))


# ========================================================================================================= terrain
ENV = C('ENV')
TERRAIN = build_terrain(ENV)
bpy.context.view_layer.update()


def build_water(coll):
    bm = bmesh.new()
    bmf = bmesh.new()
    for i, (x0, x1, y0, y1) in enumerate(NEAR):
        if i in DRY:
            continue
        e = 1.4
        sklib._bm_box(bm, Vector(((x0 + x1) / 2, (y0 + y1) / 2, (W + 0.35) / 2)), (x1 - x0 + 2 * e, y1 - y0 + 2 * e, W - 0.35))
    for (x0, x1, y0, y1) in FAR:
        e = 1.0
        vs = [bmf.verts.new((x, y, W)) for x, y in ((x0 - e, y0 - e), (x1 + e, y0 - e), (x1 + e, y1 + e), (x0 - e, y1 + e))]
        bmf.faces.new(vs)
    w = obj('A-POND-WATER', bm, coll, (water_mat(),))
    wf = obj('A-POND-WATER-FAR', bmf, coll, (far_water_mat(),))
    for o in (w, wf):
        o.visible_shadow = False
    # puddles in the drained pond
    return w


build_water(ENV)


# ============================================================================================================== sea
def build_sea(coll):
    sea = sklib.ocean(size=50, seed=41, time=-9.0, choppy=0.6, wave_scale=0.35, wind=6.0, res=10, animate=True,
                      name='A-ENV-SEA', coll=coll)
    mat = sea.data.materials[0]
    cx, cy = CAM_END.x, CAM_END.y

    def geo(c, lo, hi):
        pts = [c]
        for sgn, lim in ((1, hi), (-1, lo)):
            step, v = 0.35, c
            while (v - lim) * sgn < 0:
                v += sgn * step
                step *= 1.035
                pts.append(v)
        return np.array(sorted(pts))

    xs, ys = geo(cx, -420.0, 9000.0), geo(cy, -9000.0, 9000.0)
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    nx, ny = len(xs), len(ys)
    me = bpy.data.meshes.new('A-ENV-SEA')
    me.vertices.add(nx * ny)
    me.vertices.foreach_set('co', np.stack([X.ravel(), Y.ravel(), np.zeros(nx * ny)], 1).astype(np.float32).ravel())
    ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing='ij')
    a = (ii * ny + jj).ravel()
    q = np.stack([a, a + ny, a + ny + 1, a + 1], 1)
    me.loops.add(len(q) * 4)
    me.loops.foreach_set('vertex_index', q.astype(np.int32).ravel())
    me.polygons.add(len(q))
    me.polygons.foreach_set('loop_start', np.arange(0, len(q) * 4, 4, dtype=np.int32))
    me.update()
    me.materials.append(mat)
    old = sea.data
    sea.data = me
    bpy.data.meshes.remove(old)
    sea.location = (0, 0, 0)
    sea.modifiers['Ocean'].geometry_mode = 'DISPLACE'
    me.shade_smooth()
    print('sea verts', nx * ny)
    return sea


SEA = build_sea(ENV)


def surf_lines(coll):
    """full-r2: broken surf foam bands parallel to the open beach (as in truck f216), only away from the farm."""
    m, nt = _new_mat('surf_foam')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 400, 200)
    b.inputs['Base Color'].default_value = (0.9, 0.92, 0.92, 1)
    b.inputs['Roughness'].default_value = 0.6
    tr = _n(nt, 'ShaderNodeBsdfTransparent', 400, -150)
    ms = _n(nt, 'ShaderNodeMixShader', 700, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -700, -200)
    _l(nt, tc.outputs['UV'], sep.inputs[0])
    nz = _noise(nt, _vscale(nt, tc.outputs['Object'], 0.25, 0.25, 1.0, -700, 100), 1.0, 5.0, 0.6, -500, 100)
    edge = _maprange(nt, _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', sep.outputs['Y'], 0.5, x=-500, y=-200), x=-350, y=-200),
                     0.15, 0.5, 1.0, 0.0, -200, -200)
    a = _math(nt, 'MULTIPLY', _maprange(nt, nz.outputs['Fac'], 0.42, 0.6, 0.0, 0.95, -250, 100), edge, x=100, y=0)
    _l(nt, a, ms.inputs[0])
    _l(nt, tr.outputs[0], ms.inputs[1])
    _l(nt, b.outputs[0], ms.inputs[2])
    _l(nt, ms.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    for d0, w in ((7.0, 3.5), (19.0, 2.5), (33.0, 2.0), (50.0, 1.6)):
        prev = None
        for yy in np.arange(-900.0, 900.0, 6.0):
            if float(coast_b(yy)) < 0.6:
                prev = None
                continue
            cx = float(shore_x(yy))
            pair = (bm.verts.new((cx + d0 / 0.894, yy, 0.32)), bm.verts.new((cx + (d0 + w) / 0.894, yy, 0.32)))
            if prev:
                f = bm.faces.new((prev[0], pair[0], pair[1], prev[1]))
                for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                    lp[uvl].uv = uv
            prev = pair
    o = obj('A-ENV-SURF', bm, coll, (m,), uv=False)
    o.visible_shadow = False
    return o


surf_lines(ENV)
# r5 perf: the ocean FFT at res 10 (+ motion-blur steps) cost ~5-10 s/frame; the sea is distant until the camera
# turns to it at ~f186, so simulate at res 8 before that (same seed/spectrum, finer ripples only) and the
# bridge resolution 10 from f186 on (BRIDGE_HORIZON f216 unchanged)
_oc = SEA.modifiers['Ocean']
_lo = SEA.modifiers.new('Ocean_lo', 'OCEAN')
for p_ in _oc.bl_rna.properties:
    if not p_.is_readonly and p_.identifier not in ('name', 'resolution', 'show_expanded'):
        try:
            setattr(_lo, p_.identifier, getattr(_oc, p_.identifier))
        except Exception:
            pass
_lo.resolution = 8
for d_ in SEA.animation_data.drivers if SEA.animation_data else []:
    if d_.data_path.startswith('modifiers["Ocean"]'):
        nd = _lo.driver_add(d_.data_path.split('.')[-1])
        nd.driver.type, nd.driver.expression = d_.driver.type, d_.driver.expression
for f_, lo_ in ((1, True), (186, False)):
    _lo.show_render, _oc.show_render = lo_, not lo_
    _lo.keyframe_insert('show_render', frame=f_)
    _oc.keyframe_insert('show_render', frame=f_)


# ======================================================================================================== aerators
def aerator_collection(name, speed, trail=28.0):
    co = C(name, False)
    plast = sklib.plastic((0.82, 0.83, 0.8), 0.35, name='aer_float')
    galv = sklib.galvanised(0.35)
    blue = sklib.painted_metal((0.06, 0.2, 0.42), 0.35, 0.2)
    yel = sklib.plastic(look.hex_rgb('#e2a03a'), 0.3, name='aer_paddle')
    bm = bmesh.new()
    for sy in (-1, 1):
        sklib._bm_cyl(bm, Vector((0, sy * 1.15, 0.0)), 0.17, 1.7, 'X', 16, 0)
        sklib._bm_cyl(bm, Vector((0.85, sy * 1.15, 0.0)), 0.17, 0.1, 'X', 16, 0, r2=0.05)
        sklib._bm_cyl(bm, Vector((-0.85, sy * 1.15, 0.0)), 0.17, 0.1, 'X', 16, 0, r2=0.05)
    body = obj(name + '_floats', bm, co, (plast,))
    sklib.bevel(body, 0.01, 2)
    bm = bmesh.new()
    for sx in (-0.42, 0.42):
        sklib._bm_box(bm, Vector((sx, 0, 0.42)), (0.05, 2.4, 0.05), 0)
        for sy in (-1, 1):
            sklib._bm_box(bm, Vector((sx, sy * 1.15, 0.27)), (0.05, 0.05, 0.3), 0)
    sklib._bm_box(bm, Vector((0, 0, 0.42)), (0.9, 0.06, 0.05), 0)
    sklib._bm_box(bm, Vector((0, 0, 0.55)), (0.32, 0.36, 0.26), 1)               # gearbox
    sklib._bm_cyl(bm, Vector((-0.38, 0, 0.6)), 0.12, 0.38, 'X', 16, 1)            # motor
    sklib._bm_cyl(bm, Vector((-0.6, 0, 0.6)), 0.1, 0.06, 'X', 16, 0)
    sklib._bm_cyl(bm, Vector((0, 0, 0.3)), 0.028, 2.1, 'Y', 10, 0)               # shaft
    frame = obj(name + '_frame', bm, co, (galv, blue))
    sklib.bevel(frame, 0.006, 2)
    wheels = []
    for sy in (-0.62, 0.62):
        bm = bmesh.new()
        sklib._bm_cyl(bm, Vector((0, 0, 0)), 0.12, 0.34, 'Y', 16, 0)
        for k in range(8):
            a = k * math.pi / 4
            M = Matrix.Rotation(a, 4, 'Y')
            vs = sklib._bm_box(bm, Vector((0, 0, 0)), (0.025, 0.34, 0.24), 1)
            for v in vs:
                v.co = M @ (v.co + Vector((0.02 * (v.co.z), 0, 0.24)))
        w = obj(name + '_wheel', bm, co, (galv, yel))
        w.location = (0, sy, 0.3)
        sklib.bevel(w, 0.004, 2)
        drive(w, 'rotation_euler', 'frame*%g' % speed, 1)
        wheels.append(w)
    # foam: churn at the wheels + trail downstream (+X), only on the water surface
    bm = bmesh.new()
    nxs, nys = 40, 10
    xs = np.linspace(-1.2, trail + 0.5, nxs)
    grid = [[bm.verts.new((x, (j / (nys - 1) - 0.5) * (2.6 + 0.2 * max(0, x)), 0.128)) for j in range(nys)] for x in xs]
    for i in range(nxs - 1):
        for j in range(nys - 1):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    foam = obj(name + '_foam', bm, co, (foam_mat(trail),), uv=False)
    foam.visible_shadow = False
    # churn: white-water curtains thrown up behind each paddle wheel (scrolling spray texture, no shadows)
    if speed:
        bm = bmesh.new()
        for sy in (-0.62, 0.62):
            for k, (x0_, h_, tilt) in enumerate(((0.25, 0.42, 0.5), (0.55, 0.3, 0.9))):
                c_ = Vector((x0_, sy, 0.13))
                dx = Vector((math.sin(tilt) * h_, 0, math.cos(tilt) * h_))
                vs = [bm.verts.new(c_ + Vector((0, -0.2, 0))), bm.verts.new(c_ + Vector((0, 0.2, 0))),
                      bm.verts.new(c_ + dx + Vector((0, 0.24, 0))), bm.verts.new(c_ + dx + Vector((0, -0.24, 0)))]
                bm.faces.new(vs)
        uvl = bm.loops.layers.uv.new('UVMap')
        for f in bm.faces:
            for i_, lp in enumerate(f.loops):
                lp[uvl].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[i_]
        spray = obj(name + '_spray', bm, co, (spray_mat(),), uv=False)
        spray.visible_shadow = False
    return co


def spray_mat():
    m = bpy.data.materials.get('aer_spray')
    if m:
        return m
    m, nt = _new_mat('aer_spray')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 400, 200)
    b.inputs['Base Color'].default_value = (0.9, 0.9, 0.86, 1)
    b.inputs['Roughness'].default_value = 0.4
    b.inputs['Subsurface Weight'].default_value = 0.0
    tr = _n(nt, 'ShaderNodeBsdfTransparent', 400, -150)
    ms = _n(nt, 'ShaderNodeMixShader', 700, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    mp = _n(nt, 'ShaderNodeMapping', -700, 0)
    _l(nt, tc.outputs['UV'], mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = (3.0, 1.0, 1.0)
    drive(mp.inputs['Location'], 'default_value', 'frame*-0.37', 1)
    nz = _noise(nt, mp.outputs[0], 4.0, 6.0, 0.7, -500, 100)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -700, -250)
    _l(nt, tc.outputs['UV'], sep.inputs[0])
    edge = _math(nt, 'MULTIPLY', _maprange(nt, sep.outputs['Y'], 1.0, 0.35, 0, 1, -500, -250),
                 _math(nt, 'MULTIPLY', _maprange(nt, sep.outputs['X'], 0.0, 0.2, 0, 1, -500, -400),
                       _maprange(nt, sep.outputs['X'], 1.0, 0.8, 0, 1, -500, -550), x=-300, y=-450), x=-150, y=-300)
    a = _math(nt, 'MULTIPLY', _maprange(nt, nz.outputs['Fac'], 0.42, 0.62, 0.0, 0.85, -300, 100), edge, x=100, y=0)
    _l(nt, a, ms.inputs[0])
    _l(nt, tr.outputs[0], ms.inputs[1])
    _l(nt, b.outputs[0], ms.inputs[2])
    _l(nt, ms.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'
    m.use_backface_culling = False
    return m


def foam_mat(trail=28.0):
    nm = 'aer_foam_%d' % int(trail)
    m = bpy.data.materials.get(nm)
    if m:
        return m
    m, nt = _new_mat(nm)
    out = _n(nt, 'ShaderNodeOutputMaterial', 1300, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 700, 200)
    b.inputs['Base Color'].default_value = (0.86, 0.87, 0.82, 1)
    b.inputs['Roughness'].default_value = 0.55
    tr = _n(nt, 'ShaderNodeBsdfTransparent', 700, -200)
    ms = _n(nt, 'ShaderNodeMixShader', 1000, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -1200, 0)
    oi = _n(nt, 'ShaderNodeObjectInfo', -1200, -400)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -1000, 0)
    _l(nt, tc.outputs['Object'], sep.inputs[0])
    X, Y = sep.outputs['X'], sep.outputs['Y']
    # scrolling streak coords (downstream drift ~1.2 m/s)
    xs_ = _math(nt, 'SUBTRACT', X, 0.0, x=-800, y=100)
    drive(xs_.node.inputs[1], 'default_value', 'frame*0.05')
    cmb = _n(nt, 'ShaderNodeCombineXYZ', -600, 0)
    _l(nt, _math(nt, 'MULTIPLY', xs_, 0.14, x=-700, y=150), cmb.inputs['X'])
    _l(nt, _math(nt, 'MULTIPLY', Y, 1.6, x=-700, y=0), cmb.inputs['Y'])
    _l(nt, _math(nt, 'MULTIPLY', oi.outputs['Random'], 50.0, x=-700, y=-150), cmb.inputs['Z'])
    n1 = _noise(nt, cmb.outputs[0], 2.2, 8.0, 0.68, -400, 100)
    vo = _n(nt, 'ShaderNodeTexVoronoi', -400, -200)
    vo.inputs['Scale'].default_value = 9.0
    _l(nt, cmb.outputs[0], vo.inputs['Vector'])
    pat = _maprange(nt, n1.outputs['Fac'], 0.36, 0.58, 0.0, 1.0, -200, 100)
    bub = _maprange(nt, vo.outputs['Distance'], 0.05, 0.3, 0.6, 0.0, -200, -200)
    pat = _math(nt, 'MAXIMUM', pat, bub, x=0, y=0)
    # fades: along the trail, across it, churn near the wheels
    along = _maprange(nt, X, 0.0, trail, 1.0, 0.0, -400, 400)
    along = _math(nt, 'POWER', along, 0.7, x=-300, y=450)
    along = _math(nt, 'MULTIPLY', along, _maprange(nt, X, -1.4, 0.4, 0.0, 1.0, -400, 550), True, -200, 400)
    halfw = _math(nt, 'MULTIPLY_ADD', _math(nt, 'MAXIMUM', X, 0.0, x=-600, y=700), 0.1, x=-400, y=700, c=1.3)
    across = _maprange(nt, _math(nt, 'DIVIDE', _math(nt, 'ABSOLUTE', Y, x=-600, y=850), halfw, x=-400, y=850),
                       0.35, 1.0, 1.0, 0.0, -200, 800)
    churn = _maprange(nt, X, 0.6, 5.5, 1.0, 0.0, -200, 650)
    a = _math(nt, 'MULTIPLY', pat, _math(nt, 'MULTIPLY', along, across, x=0, y=500), x=200, y=200)
    # boiling white water at the wheels: isotropic blobs, not a solid sheet
    bmp = _n(nt, 'ShaderNodeMapping', -600, 1000)
    _l(nt, tc.outputs['Object'], bmp.inputs['Vector'])
    drive(bmp.inputs['Location'], 'default_value', 'frame*0.06', 2)
    n2 = _noise(nt, bmp.outputs[0], 1.6, 6.0, 0.65, -400, 1000)
    boil = _maprange(nt, n2.outputs['Fac'], 0.42, 0.62, 0.0, 1.0, -200, 1000)
    soft = _maprange(nt, _math(nt, 'DIVIDE', _math(nt, 'ABSOLUTE', Y, x=-600, y=1150), halfw, x=-400, y=1150),
                     0.2, 1.0, 1.0, 0.0, -200, 1150)
    a = _math(nt, 'MAXIMUM', a, _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', churn, along, x=100, y=900),
                                      _math(nt, 'MULTIPLY', soft, boil, x=0, y=1100), x=400, y=700), x=500, y=300)
    a = _math(nt, 'MULTIPLY', a, 1.0, True, 800, 300)
    # churned plume under the foam: stirred-up silt makes the wake browner + rougher than the mirror-calm pond, so
    # the trail reads even at grazing angles where white foam alone vanishes into the bright sky reflection
    plume = _math(nt, 'MULTIPLY', _math(nt, 'POWER', along, 0.6, x=400, y=900),
                  _maprange(nt, across, 0.0, 0.4, 0.0, 1.0, 400, 1000), x=550, y=900)
    plume = _math(nt, 'MULTIPLY', plume, _maprange(nt, n1.outputs['Fac'], 0.25, 0.6, 0.8, 1.0, 400, 1100), True, 700, 900)
    mud = _n(nt, 'ShaderNodeBsdfPrincipled', 700, 700)
    mud.inputs['Base Color'].default_value = (0.085, 0.075, 0.04, 1)
    mud.inputs['Roughness'].default_value = 0.6
    mud.inputs['Specular IOR Level'].default_value = 0.1
    ms0 = _n(nt, 'ShaderNodeMixShader', 950, 600)
    _l(nt, plume, ms0.inputs[0])
    _l(nt, tr.outputs[0], ms0.inputs[1])
    _l(nt, mud.outputs[0], ms0.inputs[2])
    # foam: bubbly bump catches the low sun + a little bubble scatter
    bpf = _n(nt, 'ShaderNodeBump', 500, 100)
    bpf.inputs['Strength'].default_value = 0.8
    _l(nt, vo.outputs['Distance'], bpf.inputs['Height'])
    _l(nt, bpf.outputs[0], b.inputs['Normal'])
    b.inputs['Base Color'].default_value = (0.95, 0.95, 0.9, 1)
    b.inputs['Emission Color'].default_value = (1.0, 0.85, 0.7, 1)
    b.inputs['Emission Strength'].default_value = 0.6
    _l(nt, a, ms.inputs[0])
    _l(nt, ms0.outputs[0], ms.inputs[1])
    _l(nt, b.outputs[0], ms.inputs[2])
    _l(nt, ms.outputs[0], out.inputs['Surface'])
    # BLENDED: drawn after the ray-traced-refraction water layer, which otherwise paints over dithered surfaces
    # lying on it (trails vanished at grazing angles)
    m.surface_render_method = 'BLENDED'
    return m


AER = [aerator_collection('A-AERATOR-a', 0.42), aerator_collection('A-AERATOR-b', -0.0),
       aerator_collection('A-AERATOR-c', 0.42, 13.0)]       # c: short trail (harvest pond, ends mid-pond)
# b: one stopped unit (harvest pond is being drained); its foam hidden
for o in AER[1].objects:
    if o.name.endswith('_foam'):
        AER[1].objects.unlink(o)
    if 'wheel' in o.name:
        o.driver_remove('rotation_euler', 1)
AERS = C('AERATORS')
n_aer = 0
for i, (x0, x1, y0, y1) in enumerate(NEAR):
    if i in DRY:
        continue
    yc = (y0 + y1) / 2
    if i == 12:     # harvest pond: three running in the north half, trails end mid-pond
        for k, (ax, ay) in enumerate([(x0 + 6.0, y1 - 8.0), (x0 + 22.0, yc + 6.0), (x0 + 34.0, y1 - 6.0),
                                      (x0 + 26.0, y0 + 5.5)]):     # last: under the low pass (f120-135)
            sklib.instance(AER[2], (ax, ay, W - 0.12), random.Random(k).uniform(-0.08, 0.08), 'aer_%02d_%d' % (i, k), AERS)
            n_aer += 1
        continue
    if i in (8, 13):  # neighbours of the low pass: one near the camera side
        sklib.instance(AER[0], (x0 + 14.0, yc - 0.5, W - 0.12), 0.05, 'aer_%02d_c' % i, AERS)
        n_aer += 1
    r = random.Random(i)
    sklib.instance(AER[0], (x0 + 5.0 + r.uniform(0, 3), y0 + 7 + r.uniform(0, 3), W - 0.12), r.uniform(-0.1, 0.1),
                   'aer_%02d_a' % i, AERS)
    n_aer += 1
    if r.random() < 0.7:
        sklib.instance(AER[0], (x1 - 5.0 - r.uniform(0, 3), y1 - 7 - r.uniform(0, 3), W - 0.12),
                       math.pi + r.uniform(-0.1, 0.1), 'aer_%02d_b' % i, AERS)
        n_aer += 1
print('aerators', n_aer)


# ======================================================================================================== vegetation
def tube(bm, pts, radii, seg=8, mi=0, uvl=None):
    """Tapered tube along pts; returns ring verts. Writes metric UV if uvl given."""
    rings = []
    prev_n = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        q = t.to_track_quat('Z', 'Y')
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            ring.append(bm.verts.new(p + q @ Vector((math.cos(a) * radii[i], math.sin(a) * radii[i], 0))))
        rings.append(ring)
    faces = []
    for i in range(len(rings) - 1):
        for k in range(seg):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]))
            f.material_index = mi
            faces.append((f, i, k))
    if uvl is not None:
        acc = [0.0]
        for i in range(1, len(pts)):
            acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)
        for f, i, k in faces:
            circ = 2 * math.pi * radii[i]
            for lp in f.loops:
                vi = rings[i].index(lp.vert) if lp.vert in rings[i] else rings[i + 1].index(lp.vert)
                ii = i if lp.vert in rings[i] else i + 1
                kk = vi if not (vi == 0 and k == seg - 1) else seg
                lp[uvl].uv = (kk / seg * circ, acc[ii])
    return rings


def palm(name, seed, H, lean, lod=0):
    r = random.Random(seed)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    lv = bm.faces.layers.float.new('leafvar')
    dd = bm.faces.layers.float.new('dead')
    az = r.uniform(0, 6.28)
    dirv = Vector((math.cos(az), math.sin(az), 0))
    n = int(H / 0.35)
    pts, rad = [], []
    for i in range(n + 1):
        t = i / n
        off = H * math.sin(lean * D2R) * (t - 0.32 * t * t) + 0.15 * math.sin(t * 7 + seed)
        pts.append(dirv * off + Vector((0, 0, H * t)))
        rad.append(0.15 + 0.13 * math.exp(-t * 14) - 0.025 * t + 0.008 * math.sin(t * 40))
    tube(bm, pts, rad, 12, 0, uvl)
    top = pts[-1]
    up = (pts[-1] - pts[-3]).normalized()
    # leaf-base boots
    for k in range(10):
        a = k * 2.4
        b0 = top + Vector((math.cos(a) * 0.14, math.sin(a) * 0.14, -0.35 + 0.03 * k))
        tube(bm, [b0, b0 + Vector((math.cos(a) * 0.25, math.sin(a) * 0.25, 0.35))], [0.06, 0.03], 5, 1)
    nf = r.randint(26, 32)
    for i in range(nf):
        phi = i * 137.5 * D2R + r.uniform(-0.2, 0.2)
        age = i / nf
        el = (60 - 115 * age + r.uniform(-8, 8)) * D2R
        dead = 1.0 if (age > 0.93 and r.random() < 0.6) else 0.0
        if dead:
            el = -75 * D2R
        Lr = (3.2 + 1.6 * math.sin(math.pi * min(1, age + 0.25))) * r.uniform(0.9, 1.08)
        d0 = Vector((math.cos(el) * math.cos(phi), math.cos(el) * math.sin(phi), math.sin(el)))
        k = r.uniform(0.07, 0.12) * (1.4 if age > 0.6 else 1.0)
        base = top + up * 0.12 + d0 * 0.15
        ns = 14
        rp = [base + d0 * (Lr * j / ns) + Vector((0, 0, -k * (Lr * j / ns) ** 2)) for j in range(ns + 1)]
        tube(bm, rp, [0.035 * (1 - j / ns) + 0.008 for j in range(ns + 1)], 4, 1)
        var = r.random()
        nl = 50 if lod == 0 else 16
        for side in (-1, 1):
            for j in range(nl):
                s_ = 0.12 + 0.86 * j / nl
                idx = s_ * ns
                i0 = min(int(idx), ns - 1)
                p = rp[i0].lerp(rp[i0 + 1], idx - i0)
                tan = (rp[i0 + 1] - rp[i0]).normalized()
                side_v = tan.cross(Vector((0, 0, 1)))
                if side_v.length < 1e-3:
                    side_v = Vector((1, 0, 0))
                side_v.normalize()
                ll = (0.25 + 0.75 * math.sin(math.pi * min(1, s_ * 1.05)) ** 0.7) * 0.85 * r.uniform(0.85, 1.1)
                ang = r.uniform(28, 42) * D2R
                ldir = (side_v * side * math.cos(ang) + tan * math.sin(ang) + Vector((0, 0, -0.25 - 0.3 * s_))).normalized()
                wv = tan * (0.034 if lod == 0 else 0.09) * (1 - 0.3 * s_)
                prev = None
                nq = 4 if lod == 0 else 2
                for q in range(nq):
                    u = q / (nq - 1)
                    c = p + ldir * (ll * u) + Vector((0, 0, -0.12 * ll * u * u))
                    wd = wv * (1 - 0.85 * u)
                    pair = (bm.verts.new(c - wd), bm.verts.new(c + wd + Vector((0, 0, 0.012))))
                    if prev:
                        f = bm.faces.new((prev[0], pair[0], pair[1], prev[1]))
                        f.material_index = 2
                        f[lv] = min(1, max(0, var + r.uniform(-0.15, 0.15)))
                        f[dd] = dead if dead else (0.35 if age > 0.85 and r.random() < 0.3 else 0.0)
                    prev = pair
    # coconuts
    for k in range(r.randint(6, 12)):
        a = r.uniform(0, 6.28)
        c = top + Vector((math.cos(a) * 0.32, math.sin(a) * 0.32, r.uniform(-0.55, -0.2)))
        rr = r.uniform(0.1, 0.13)
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rr, matrix=Matrix.Translation(c))
        for v in res['verts']:
            v.co.z = c.z + (v.co.z - c.z) * 1.15
        for f in {f for v in res['verts'] for f in v.link_faces}:
            f.material_index = 3
            f[lv] = r.random()
    ob = sklib._mesh_obj(name, bm, False)
    bark = sklib.pbr('palm_bark', 'palm_tree_bark', wear=0.2)
    rach = leaf_mat('palm_rachis', (0.2, 0.22, 0.07), (0.3, 0.26, 0.09), transl=0.15)
    leaf = leaf_mat('palm_leaf', (0.07, 0.13, 0.025), (0.13, 0.17, 0.035), (0.30, 0.20, 0.08))
    nut = leaf_mat('coconut', (0.18, 0.2, 0.04), (0.28, 0.2, 0.06), transl=0.0)
    for mm in (bark, rach, leaf, nut):
        ob.data.materials.append(mm)
    ob.data.shade_smooth()
    return ob


def leaf_crown(bm, lv, centers, n_per, size, r, rad, droop=0.0, mi=1, shape='diamond'):
    for c in centers:
        var = r.random()
        for k in range(n_per):
            p = c + Vector((r.gauss(0, rad), r.gauss(0, rad), r.gauss(0, rad * 0.7)))
            nrm = (p - c).normalized() if (p - c).length > 1e-3 else Vector((0, 0, 1))
            e = Euler((r.uniform(0, 6.28), r.uniform(0, 6.28), r.uniform(0, 6.28))).to_matrix()
            a = e @ Vector((1, 0, 0))
            b = nrm.cross(a).normalized() if nrm.cross(a).length > 1e-3 else Vector((0, 1, 0))
            L = size * r.uniform(0.7, 1.2)
            if shape == 'strand':
                dvec = (Vector((0, 0, -1)) * droop + a * (1 - droop)).normalized()
                vs = [bm.verts.new(p), bm.verts.new(p + b * 0.012), bm.verts.new(p + dvec * L)]
            else:
                vs = [bm.verts.new(p), bm.verts.new(p + a * L * 0.5 + b * L * 0.22),
                      bm.verts.new(p + a * L), bm.verts.new(p + a * L * 0.5 - b * L * 0.22)]
            f = bm.faces.new(vs)
            f.material_index = mi
            f[lv] = min(1, max(0, var + r.uniform(-0.2, 0.2)))


def tree(name, seed, kind, lod=0):
    r = random.Random(seed)
    q_ = 0.22 if lod else 1.0
    z_ = 2.0 if lod else 1.0
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    lv = bm.faces.layers.float.new('leafvar')
    bm.faces.layers.float.new('dead')
    centers = []
    if kind == 'neem':
        H = r.uniform(3.0, 4.0)
        lean = Vector((r.uniform(-0.3, 0.3), r.uniform(-0.3, 0.3), 0))
        trunk = [Vector((0, 0, 0)) + lean * (t * t) + Vector((0, 0, H * t)) for t in np.linspace(0, 1, 8)]
        tube(bm, trunk, [0.28 - 0.12 * t + 0.08 * math.exp(-t * 10) for t in np.linspace(0, 1, 8)], 10, 0, uvl)
        top = trunk[-1]
        for b in range(r.randint(5, 7)):
            a = b * 2.4 + r.uniform(-0.3, 0.3)
            L = r.uniform(2.8, 4.2)
            d = Vector((math.cos(a) * 0.75, math.sin(a) * 0.75, r.uniform(0.6, 1.0))).normalized()
            pts = [top + d * (L * t) + Vector((0, 0, -0.3 * (L * t) ** 2 / L)) for t in np.linspace(0, 1, 6)]
            tube(bm, pts, [0.13 * (1 - 0.8 * t) for t in np.linspace(0, 1, 6)], 7, 0, uvl)
            for t in (0.55, 0.8, 1.0):
                centers.append(top + d * (L * t) + Vector((r.uniform(-0.6, 0.6), r.uniform(-0.6, 0.6), 0.5)))
        crown_c = top + Vector((0, 0, 2.5))
        for k in range(10):
            centers.append(crown_c + Vector((r.uniform(-2.8, 2.8), r.uniform(-2.8, 2.8), r.uniform(-0.5, 2.2))))
        leaf_crown(bm, lv, centers, int(230 * q_), 0.26 * z_, r, 0.75)
        mats = (sklib.pbr('bark_tree', 'bark_brown_02', wear=0.2),
                leaf_mat('neem_leaf', (0.06, 0.14, 0.03), (0.1, 0.17, 0.04)))
    elif kind == 'casuarina':
        H = r.uniform(11, 16)
        bend = Vector((r.uniform(-0.6, 0.6), r.uniform(-0.6, 0.6), 0))
        trunk = [bend * (t * t) + Vector((0, 0, H * t)) for t in np.linspace(0, 1, 12)]
        tube(bm, trunk, [0.16 * (1 - 0.85 * t) + 0.02 for t in np.linspace(0, 1, 12)], 8, 0, uvl)
        for k in range(26):
            t = r.uniform(0.3, 1.0)
            c = bend * (t * t) + Vector((0, 0, H * t))
            rad = 2.2 * (1.05 - t) + 0.3
            a = r.uniform(0, 6.28)
            p = c + Vector((math.cos(a) * rad * r.uniform(0.3, 1), math.sin(a) * rad * r.uniform(0.3, 1), 0))
            tube(bm, [c, p], [0.05 * (1.1 - t), 0.015], 5, 0)
            centers.append(p)
        leaf_crown(bm, lv, centers, int(420 * q_), 0.45 * z_, r, 0.55, droop=0.75, shape='strand')
        mats = (sklib.pbr('bark_tree', 'bark_brown_02', wear=0.2),
                leaf_mat('casuarina_needle', (0.07, 0.1, 0.04), (0.1, 0.12, 0.05), transl=0.2))
    else:   # shrub
        for k in range(r.randint(5, 9)):
            centers.append(Vector((r.uniform(-0.8, 0.8), r.uniform(-0.8, 0.8), r.uniform(0.4, 1.1))))
            tube(bm, [Vector((0, 0, 0)), centers[-1]], [0.04, 0.01], 5, 0)
        leaf_crown(bm, lv, centers, int(140 * q_), 0.18 * z_, r, 0.4)
        mats = (sklib.pbr('bark_tree', 'bark_brown_02', wear=0.2),
                leaf_mat('shrub_leaf', (0.08, 0.15, 0.03), (0.15, 0.17, 0.04)))
    ob = sklib._mesh_obj(name, bm, False)
    for mm in mats:
        ob.data.materials.append(mm)
    ob.data.shade_smooth()
    return ob


def tuft(name, seed):
    r = random.Random(seed)
    bm = bmesh.new()
    lv = bm.faces.layers.float.new('leafvar')
    dd = bm.faces.layers.float.new('dead')
    for k in range(22):
        a = r.uniform(0, 6.28)
        base = Vector((math.cos(a), math.sin(a), 0)) * r.uniform(0, 0.12)
        h = r.uniform(0.18, 0.55)
        lean = Vector((math.cos(a), math.sin(a), 0)) * r.uniform(0.05, 0.35) * h
        side = Vector((-math.sin(a), math.cos(a), 0)) * 0.006
        prev = None
        for q in range(4):
            u = q / 3
            c = base + lean * u * u + Vector((0, 0, h * u))
            w = side * (1 - u)
            pair = (bm.verts.new(c - w), bm.verts.new(c + w))
            if prev:
                f = bm.faces.new((prev[0], pair[0], pair[1], prev[1]))
                f[lv] = r.random()
                f[dd] = 1.0 if r.random() < 0.12 else 0.0
            prev = pair
    ob = sklib._mesh_obj(name, bm, False)
    ob.data.materials.append(leaf_mat('grass_blade', (0.1, 0.17, 0.04), (0.22, 0.24, 0.07), (0.45, 0.38, 0.2), 0.3))
    return ob


def lib_coll(name, obs):
    co = C(name, False)
    for o in obs:
        co.objects.link(o)
    return co


VEG = C('VEG')
PALMS = [lib_coll('A-VEG-PALM-%d' % i, [palm('palm_%d' % i, 11 + i * 7, H, lean)])
         for i, (H, lean) in enumerate([(8.5, 14), (10.5, 6), (12.0, 22), (13.5, 10), (15.5, 17), (17.5, 4)])]
TREES = [lib_coll('A-VEG-NEEM-%d' % i, [tree('neem_%d' % i, 40 + i, 'neem')]) for i in range(2)] + \
        [lib_coll('A-VEG-CASUARINA-%d' % i, [tree('casu_%d' % i, 60 + i, 'casuarina')]) for i in range(2)]
SHRUBS = [lib_coll('A-VEG-SHRUB-%d' % i, [tree('shrub_%d' % i, 80 + i, 'shrub')]) for i in range(2)]


def place(coll_list, pts, rng, scale=(0.85, 1.12), name='veg'):
    n = 0
    for p in pts:
        x, y = p
        z = height_at(x, y) - 0.05
        co = coll_list[rng.randrange(len(coll_list))]
        sklib.instance(co, (x, y, z), rng.uniform(0, 6.28), '%s_%03d' % (name, n), VEG, rng.uniform(*scale))
        n += 1
    return n


def free_spot(x, y, clear=7.5):
    """Not inside a pond or on a pond bund (ponds keep their banks clear)."""
    for (x0, x1, y0, y1) in PONDS:
        if x0 - clear < x < x1 + clear and y0 - clear < y < y1 + clear:
            return False
    return x < float(shore_x(y)) - 9.0


vr = random.Random(9)
palm_pts = []
# rows along the south perimeter track and the coast, west side clump, north edge, around the sheds
for x in np.arange(-232, -10, 9.0):
    palm_pts.append((x + vr.uniform(-2, 2), -30.5 + vr.uniform(-2.5, 1.5)))
for y in np.arange(30, 170, 11.0):
    palm_pts.append((float(shore_x(y)) - 12 - 85 * float(coast_b(y)) + vr.uniform(-2, 2), y + vr.uniform(-3, 3)))
for k in range(26):
    palm_pts.append((-250 + vr.uniform(-25, 8), vr.uniform(-30, 160)))
for k in range(18):
    palm_pts.append((vr.uniform(-230, -20), 163 + vr.uniform(0, 25)))
palm_pts = [p for p in palm_pts if free_spot(*p, 7.5)]
n_palm = place(PALMS, palm_pts, vr, name='palm')
# distant coconut groves (aerial)
grove = []
for k in range(260):
    cx, cy = vr.choice([(-420, 40), (-330, 460), (-80, 520), (-560, -220), (-200, -300), (-640, 260)])
    p = (cx + vr.gauss(0, 55), cy + vr.gauss(0, 45))
    if free_spot(*p, 4):
        grove.append(p)
PALMS_LO = [lib_coll('A-VEG-PALM-LO-%d' % i, [palm('palmlo_%d' % i, 11 + i * 7, H, lean, 1)])
            for i, (H, lean) in enumerate([(8.5, 14), (10.5, 6), (12.0, 22), (13.5, 10), (15.5, 17), (17.5, 4)])]
n_grove = place(PALMS_LO, grove, vr, (0.8, 1.15), 'grove')
tree_pts = [p for p in [(vr.uniform(-300, -240), vr.uniform(-40, 180)) for _ in range(12)] +
            [(vr.uniform(-230, -10), vr.uniform(-48, -36)) for _ in range(8)] +
            [(vr.uniform(-230, 0), vr.uniform(172, 200)) for _ in range(12)] if free_spot(*p, 6)]
n_tree = place(TREES, tree_pts, vr, (0.8, 1.2), 'tree')
shrub_pts = [p for p in [(vr.uniform(-245, 5), vr.choice([vr.uniform(-40, -27.5), vr.uniform(158, 175)]))
                         for _ in range(90)] + [(float(shore_x(y)) - 85 * float(coast_b(y)) - vr.uniform(8.5, 14), y) for y in np.arange(-60, 170, 6)]
             if free_spot(*p, 7.0)]
n_shrub = place(SHRUBS, shrub_pts, vr, (0.6, 1.4), 'shrub')
# scattered tree clumps + scrub across the open land (aerial read)
land = []
for k in range(130):
    cx, cy = vr.uniform(-800, 250), vr.uniform(-700, 850)
    for j in range(vr.randint(2, 6)):
        p = (cx + vr.gauss(0, 12), cy + vr.gauss(0, 12))
        if free_spot(*p, 6):
            land.append(p)
TREES_LO = [lib_coll('A-VEG-TREE-LO-%d' % i, [tree('treelo_%d' % i, 40 + i, k, 1)]) for i, k in enumerate(['neem', 'neem', 'casuarina'])]
SHRUBS_LO = [lib_coll('A-VEG-SHRUB-LO-%d' % i, [tree('shrublo_%d' % i, 80 + i, 'shrub', 1)]) for i in range(2)]
n_tree += place(TREES_LO, land, vr, (0.8, 1.25), 'clump')
scrub = [p for p in [(vr.uniform(-800, 250), vr.uniform(-700, 850)) for _ in range(500)] if free_spot(*p, 6)]
n_shrub += place(SHRUBS_LO, scrub, vr, (0.9, 1.8), 'scrub')
# r5: coconut rows along the farm tracks of the field patchwork (same rotation/spacing as terrain_mat)
ca_, sa_ = math.cos(0.21), math.sin(0.21)
rows_ = []
for kk in range(-8, 4):
    for vv in np.arange(-700.0, 850.0, 10.0):
        if vr.random() < 0.4:
            continue
        uu = kk * 252.0 + vr.choice((-4.0, 4.0)) + vr.uniform(-1, 1)
        x, y = uu * ca_ - vv * sa_, uu * sa_ + vv * ca_
        if -820 < x < 260 and -720 < y < 860 and free_spot(x, y, 22):
            rows_.append((x, y))
n_grove += place(PALMS_LO, rows_, vr, (0.85, 1.15), 'rowpalm')


# r5: hamlets of village houses (plaster walls in faded pastels, tin or tiled roofs) among the groves
def house_variant(i, w, d, h, tint, roof):
    r = random.Random(300 + i)
    bm = bmesh.new()
    sklib._bm_box(bm, Vector((0, 0, h / 2)), (w, d, h), 0)
    sklib._bm_box(bm, Vector((0, d / 2 + 0.01, 0.95)), (0.9, 0.04, 1.9), 2)            # door
    for sx in (-1, 1):
        sklib._bm_box(bm, Vector((sx * w * 0.3, d / 2 + 0.01, 1.5)), (0.7, 0.04, 0.8), 2)
    sklib._bm_box(bm, Vector((0, 0, 0.12)), (w + 0.4, d + 0.4, 0.24), 3)                 # plinth
    if roof == 'gable':
        rh, ex, ey = 1.1, w / 2 + 0.35, d / 2 + 0.45
        for sy in (-1, 1):
            vs = [bm.verts.new(c) for c in ((-ex, sy * ey, h - 0.12), (ex, sy * ey, h - 0.12), (ex, 0, h + rh), (-ex, 0, h + rh))]
            f = bm.faces.new(vs if sy < 0 else vs[::-1])
            f.material_index = 1
        for sx in (-1, 1):                                                                # gable end walls
            vs = [bm.verts.new(c) for c in ((sx * w / 2, -d / 2, h), (sx * w / 2, d / 2, h), (sx * w / 2, 0, h + rh - 0.05))]
            bm.faces.new(vs)
    else:
        sklib._bm_box(bm, Vector((0, 0, h + 0.1)), (w + 0.2, d + 0.2, 0.2), 0)          # RCC slab
        sklib._bm_box(bm, Vector((0, 0, h + 0.35)), (w + 0.2, 0.12, 0.3), 0)            # parapet
        sklib._bm_box(bm, Vector((0, 0, h + 0.35)), (0.12, d + 0.2, 0.3), 0)
    ob = sklib._mesh_obj('house_%d' % i, bm, False)
    wall = sklib.pbr('house_wall_%d' % i, 'painted_plaster_wall', tint=tint, wear=0.55, scale=0.5)
    roofm = bpy.data.materials.get('tin_roof') or sklib.pbr('tin_roof', 'corrugated_iron_02', wear=0.45, metal=0.5,
                                                            rough=(0.35, 0.85), streaks=0.6)
    dark = sklib.flat('house_opening', (0.04, 0.035, 0.03), rough=0.8, var=0.1, scale=20)
    plinth = sklib.concrete_quay(0.5)
    for mm in (wall, roofm, dark, plinth):
        ob.data.materials.append(mm)
    sklib.box_uv(ob, 1.0)
    sklib.bevel(ob, 0.02, 2)
    return ob


HOUSES = [lib_coll('A-HOUSE-%d' % i, [house_variant(i, w, d, h, t, rf)]) for i, (w, d, h, t, rf) in enumerate([
    (6.0, 4.5, 2.9, (0.45, 0.58, 0.6), 'gable'), (5.0, 4.0, 2.8, (0.68, 0.6, 0.4), 'gable'),
    (7.5, 5.0, 3.1, (0.62, 0.6, 0.55), 'flat'), (5.5, 4.2, 2.8, (0.5, 0.62, 0.46), 'flat'),
    (4.5, 3.6, 2.6, (0.66, 0.5, 0.44), 'gable')])]
hpts = []
for cx, cy, nh in ((-430, 70, 16), (-560, -200, 12), (-190, -300, 10), (-90, 470, 12), (120, -260, 8)):
    ang = vr.uniform(0, 6.28)
    for k in range(nh):
        # houses line a lane through the hamlet
        t_ = (k - nh / 2) * 11.0
        p = (cx + t_ * math.cos(ang) + vr.choice((-9, 9)) * -math.sin(ang) + vr.uniform(-2, 2),
             cy + t_ * math.sin(ang) + vr.choice((-9, 9)) * math.cos(ang) + vr.uniform(-2, 2))
        if free_spot(*p, 10):
            hpts.append(p)
n_house = 0
for p in hpts:
    co = HOUSES[vr.randrange(len(HOUSES))]
    sklib.instance(co, (p[0], p[1], height_at(*p) - 0.1), vr.uniform(0, 6.28), 'house_%03d' % n_house, VEG)
    n_house += 1
# full-r2 (match truck f216): casuarina shelter belt behind the beach, a coconut orchard south of the farm road,
# the farm road itself (asphalt, y = -45, ends at the farm's south-east corner)
def casuarina_cone(name, seed):
    """Shelter-belt casuarina seen from the air: straight trunk + narrow ragged dark cone (lumpy, low poly)."""
    r = random.Random(seed)
    bm = bmesh.new()
    lv = bm.faces.layers.float.new('leafvar')
    bm.faces.layers.float.new('dead')
    H = r.uniform(12, 16)
    tube(bm, [Vector((0, 0, 0)), Vector((0, 0, H * 0.45))], [0.16, 0.12], 6, 0)
    rings = []
    for i, t in enumerate(np.linspace(0.25, 1.0, 9)):
        rad = 2.3 * (1.0 - t) ** 0.85 + 0.05
        rings.append([bm.verts.new((math.cos(a) * rad * r.uniform(0.75, 1.25), math.sin(a) * rad * r.uniform(0.75, 1.25),
                                    H * t + r.uniform(-0.3, 0.3))) for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)])
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(10):
            f = bm.faces.new((a_[k], a_[(k + 1) % 10], b_[(k + 1) % 10], b_[k]))
            f.material_index = 1
            f[lv] = r.random()
    ob = sklib._mesh_obj(name, bm, False)
    for mm in (sklib.pbr('bark_tree', 'bark_brown_02', wear=0.2),
               leaf_mat('casuarina_needle', (0.07, 0.1, 0.04), (0.1, 0.12, 0.05), transl=0.2)):
        ob.data.materials.append(mm)
    bev = ob.modifiers.new('sub', 'SUBSURF')
    bev.levels = bev.render_levels = 1
    return ob


CASCONE = [lib_coll('A-VEG-CASUARINA-CONE-%d' % i, [casuarina_cone('casucone_%d' % i, 500 + i)]) for i in range(3)]
cr_ = random.Random(31)
n_cas = 0
for yy in np.arange(-900.0, 900.0, 6.0):
    if float(coast_b(yy)) < 0.6:
        continue
    for row in range(5):
        if cr_.random() < 0.12:
            continue
        y_ = yy + cr_.uniform(-3, 3)
        x_ = float(shore_x(y_)) + (-80.0 - row * 9.0 + cr_.uniform(-3, 3)) / 0.894
        if not -890 < x_ < 630 or any(x0 - 7 < x_ < x1 + 7 and y0 - 7 < y_ < y1 + 7 for (x0, x1, y0, y1) in PONDS):
            continue
        sklib.instance(CASCONE[cr_.randrange(3)], (x_, y_, height_at(x_, y_) - 0.05), cr_.uniform(0, 6.28), 'casua_%04d' % n_cas, VEG,
                       cr_.uniform(0.85, 1.25))
        n_cas += 1
n_orch = 0
for ix in range(18):
    for iy in range(14):
        x_, y_ = -362.0 + ix * 8.0 + cr_.uniform(-0.6, 0.6), -60.0 - iy * 8.0 + cr_.uniform(-0.6, 0.6)
        if cr_.random() < 0.06 or not free_spot(x_, y_, 4):
            continue
        sklib.instance(PALMS_LO[cr_.randrange(6)], (x_, y_, height_at(x_, y_) - 0.05), cr_.uniform(0, 6.28),
                       'orchard_%03d' % n_orch, VEG, cr_.uniform(0.75, 1.0))
        n_orch += 1
ROAD_Y = -45.0
for o in list(VEG.objects):        # clear the road corridor (deleting keeps every other placement unchanged)
    if abs(o.location.y - ROAD_Y) < 6.5 and o.location.x < -24:
        bpy.data.objects.remove(o)
print('palms', n_palm, 'grove', n_grove, 'trees', n_tree, 'shrubs', n_shrub, 'houses', n_house, 'casuarinas', n_cas,
      'orchard', n_orch)


def scatter(target, coll, attr_name, density, seed, scale=(0.7, 1.3), name='scatter'):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, Lk = ng.nodes, ng.links
    gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
    dist = N.new('GeometryNodeDistributePointsOnFaces')
    dist.distribute_method = 'RANDOM'
    dist.inputs['Density'].default_value = density
    dist.inputs['Seed'].default_value = seed
    Lk.new(gi.outputs[0], dist.inputs['Mesh'])
    na = N.new('GeometryNodeInputNamedAttribute')
    na.data_type = 'FLOAT'
    na.inputs['Name'].default_value = attr_name
    rv = N.new('FunctionNodeRandomValue')
    rv.data_type = 'FLOAT'
    rv.inputs['Seed'].default_value = seed + 1
    cmp = N.new('FunctionNodeCompare')
    cmp.data_type, cmp.operation = 'FLOAT', 'GREATER_THAN'
    Lk.new(_rvout(rv, 'FLOAT'), cmp.inputs[0])
    Lk.new(na.outputs['Attribute'], cmp.inputs[1])
    dele = N.new('GeometryNodeDeleteGeometry')
    Lk.new(dist.outputs['Points'], dele.inputs['Geometry'])
    Lk.new(cmp.outputs[0], dele.inputs['Selection'])
    ci = N.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = coll
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    iop = N.new('GeometryNodeInstanceOnPoints')
    Lk.new(dele.outputs[0], iop.inputs['Points'])
    Lk.new(ci.outputs[0], iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    ri = N.new('FunctionNodeRandomValue')
    ri.data_type = 'INT'
    [i for i in ri.inputs if i.enabled and i.type == 'INT' and i.name == 'Max'][0].default_value = 10
    ri.inputs['Seed'].default_value = seed + 2
    Lk.new(_rvout(ri, 'INT'), iop.inputs['Instance Index'])
    rr = N.new('FunctionNodeRandomValue')
    rr.data_type = 'FLOAT_VECTOR'
    vv = [i for i in rr.inputs if i.enabled and i.type == 'VECTOR']
    vv[0].default_value, vv[1].default_value = (-0.15, -0.15, 0), (0.15, 0.15, 6.28)
    Lk.new(_rvout(rr, 'FLOAT_VECTOR'), iop.inputs['Rotation'])
    rs = N.new('FunctionNodeRandomValue')
    rs.data_type = 'FLOAT'
    fl = [i for i in rs.inputs if i.enabled and i.type == 'VALUE' and i.name in ('Min', 'Max')]
    fl[0].default_value, fl[1].default_value = scale
    rs.inputs['Seed'].default_value = seed + 3
    Lk.new(_rvout(rs, 'FLOAT'), iop.inputs['Scale'])
    j = N.new('GeometryNodeJoinGeometry')
    Lk.new(iop.outputs[0], j.inputs[0])
    Lk.new(gi.outputs[0], j.inputs[0])
    Lk.new(j.outputs[0], go.inputs[0])
    md = target.modifiers.new(name, 'NODES')
    md.node_group = ng
    return md


def _rvout(node, dt):
    for o in node.outputs:
        if o.enabled and o.type == {'FLOAT': 'VALUE', 'INT': 'INT', 'FLOAT_VECTOR': 'VECTOR'}[dt]:
            return o
    return node.outputs[0]


TUFTS = lib_coll('A-VEG-GRASS', [tuft('tuft_%d' % i, 200 + i) for i in range(4)])
if not FAST:
    scatter(TERRAIN, TUFTS, 'grass', 2.2, 7, (0.6, 1.4), 'grass_scatter')


# ============================================================================================================ props
PROPS = C('PROPS')


def shed(name, loc, rot, w=6.0, d=4.2, h=2.6, sacks=0):
    root = sklib.new_obj(name, None, PROPS, loc=loc, rot=(0, 0, rot))
    bark = sklib.pbr('pole_bark', 'bark_brown_02', wear=0.3, scale=0.4)
    roofm = sklib.pbr('tin_roof', 'corrugated_iron_02', wear=0.45, metal=0.5, rough=(0.35, 0.85), streaks=0.6)
    brick = sklib.pbr('brick_wall', 'red_brick_03', wear=0.45)
    bm = bmesh.new()
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            hh = h + (0.35 if sy > 0 else 0)
            sklib._bm_cyl(bm, Vector((sx * w / 2, sy * d / 2, hh / 2)), 0.065, hh, 'Z', 8, 0)
    for sy in (-1, 1):
        hh = h + (0.35 if sy > 0 else 0)
        sklib._bm_box(bm, Vector((0, sy * d / 2, hh - 0.05)), (w + 0.3, 0.08, 0.1), 0)
    for sx in np.linspace(-w / 2, w / 2, 5):
        vs = sklib._bm_box(bm, Vector((sx, 0, h + 0.2)), (0.07, d + 0.5, 0.08), 0)
        for v in vs:
            v.co.z += 0.35 * (v.co.y / d)
    posts = obj(name + '_posts', bm, PROPS, (bark,))
    posts.parent = root
    sklib.bevel(posts, 0.01, 2)
    # corrugated roof sheet (sine profile) with sag + overhang
    bm = bmesh.new()
    nu, nv = int((w + 0.6) / 0.0381) + 1, 10
    grid = []
    for i in range(nu):
        x = -w / 2 - 0.3 + i * 0.0381
        row = []
        for j in range(nv):
            y = -d / 2 - 0.35 + (d + 0.7) * j / (nv - 1)
            z = h + 0.27 + 0.35 * (y / d) + 0.009 * math.sin(i * math.pi) + 0.015 * math.sin(x * 0.9) * math.sin(y)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for i in range(nu - 1):
        for j in range(nv - 1):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    roof = obj(name + '_roof', bm, PROPS, (roofm,))
    roof.parent = root
    so = roof.modifiers.new('Solidify', 'SOLIDIFY')
    so.thickness = 0.004
    roof.data.shade_smooth()
    bm = bmesh.new()
    sklib._bm_box(bm, Vector((0, d / 2 - 0.12, 0.6)), (w, 0.23, 1.2), 0)
    sklib._bm_box(bm, Vector((-w / 2 + 0.12, 0.3, 0.6)), (0.23, d - 1.0, 1.2), 0)
    wall = obj(name + '_wall', bm, PROPS, (brick,))
    wall.parent = root
    sklib.bevel(wall, 0.01, 2)
    return root


def sack_mesh():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=5, use_grid_fill=True)
    for v in bm.verts:
        x, y, z = v.co
        v.co = Vector((x * 0.9 * (1 + 0.12 * (0.25 - z * z)), y * 0.55 * (1 + 0.25 * (0.25 - z * z)),
                       z * 0.17 * (1 - 0.3 * x * x)))
        v.co.z += 0.085
    ob = sklib._mesh_obj('A-SACK-FEED', bm, False)
    sklib.mat_to(ob, sklib.pbr('sack_pp', 'rough_linen', tint=(0.82, 0.83, 0.8), wear=0.35, scale=3.0,
                               wear_color=(0.4, 0.36, 0.3)))
    sub = ob.modifiers.new('sub', 'SUBSURF')
    sub.levels = sub.render_levels = 1
    ob.data.shade_smooth()
    return ob


SACK = sack_mesh()
SHEDS = [shed('A-SHED-1', (-86.0, -36.0, height_at(-86, -36)), 0.05),
         shed('A-SHED-2', (-262.0, 40.0, height_at(-262, 40)), math.pi / 2 + 0.1),
         shed('A-SHED-3', (-126.0, 172.0, height_at(-126, 172)), math.pi - 0.04)]
sr = random.Random(4)
n_sack = 0
for k in range(12):      # stacked under shed 1, a few on the floor
    lay, idx = divmod(k, 4)
    x = -86.0 - 1.6 + (idx % 2) * 1.0 + sr.uniform(-0.05, 0.05)
    y = -36.0 + 0.6 + (idx // 2) * 0.62
    z = height_at(x, y) + lay * 0.16
    if lay == 2 and idx > 1:
        x, y, z = -86.0 + 1.3 + idx * 0.4, -36.0 - 0.9, height_at(-84.0, -36.9)
    o = sklib.new_obj('sack_%02d' % k, SACK.data, PROPS, loc=(x, y, z), rot=(0, 0, 0.05 + sr.uniform(-0.12, 0.12)))
    n_sack += 1
# blue drums by shed 1
drum_m = sklib.plastic((0.05, 0.2, 0.55), 0.35, name='drum_blue')
for k, (dx, dy) in enumerate([(2.2, 0.9), (2.75, 1.1), (2.5, 0.4)]):
    bm = bmesh.new()
    sklib._bm_cyl(bm, Vector((0, 0, 0.45)), 0.29, 0.9, 'Z', 24, 0)
    for zz in (0.3, 0.6):
        sklib._bm_cyl(bm, Vector((0, 0, zz)), 0.3, 0.03, 'Z', 24, 0)
    o = obj('drum_%d' % k, bm, PROPS, (drum_m,))
    o.location = (-86 + dx, -36 + dy, height_at(-86 + dx, -36 + dy))
    sklib.bevel(o, 0.01, 2)


def motorbike(loc, rot):
    root = sklib.new_obj('A-BIKE', None, PROPS, loc=loc, rot=(0, 0, rot))
    rub = sklib.flat('rubber_tyre', (0.03, 0.03, 0.03), rough=0.85, bump=0.3, scale=200)
    paint = sklib.painted_metal((0.45, 0.03, 0.03), 0.25, 0.0, contrast=0.4)
    blk = sklib.painted_metal((0.03, 0.03, 0.035), 0.3, 0.0, contrast=0.4)
    chrome = sklib.stainless(0.15)
    seat = sklib.pbr('bike_seat', 'fabric_leather_02', tint=(0.04, 0.04, 0.04), wear=0.2, scale=0.5)
    parts = []
    for wx in (-0.65, 0.62):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.3, radius2=0.3, depth=0.09,
                              matrix=Matrix.Translation((wx, 0, 0.3)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
        t = obj('bike_tyre', bm, PROPS, (rub,))
        t.parent = root
        sklib.bevel(t, 0.03, 3, 30)
        bm = bmesh.new()
        sklib._bm_cyl(bm, Vector((wx, 0, 0.3)), 0.21, 0.1, 'Y', 32, 0)
        sklib._bm_cyl(bm, Vector((wx, 0, 0.3)), 0.06, 0.16, 'Y', 16, 1)
        for k in range(18):
            a = k * math.pi / 9
            v = sklib._bm_cyl(bm, Vector((wx, 0, 0.3)), 0.003, 0.4, 'X', 4, 1)
            for vv in v:
                vv.co = Vector((wx, 0, 0.3)) + Matrix.Rotation(a, 3, 'Y') @ (vv.co - Vector((wx, 0, 0.3)))
        rim = obj('bike_rim', bm, PROPS, (blk, chrome))
        rim.parent = root
    bm = bmesh.new()
    sklib._bm_box(bm, Vector((0.25, 0, 0.82)), (0.48, 0.26, 0.2), 0)              # tank
    sklib._bm_box(bm, Vector((-0.3, 0, 0.8)), (0.62, 0.24, 0.09), 2)              # seat
    sklib._bm_box(bm, Vector((-0.2, 0, 0.62)), (0.42, 0.2, 0.18), 0)              # side panel
    sklib._bm_box(bm, Vector((0.08, 0, 0.42)), (0.34, 0.22, 0.26), 1)             # engine
    for k in range(5):
        sklib._bm_box(bm, Vector((0.2, 0, 0.36 + k * 0.04)), (0.14, 0.24, 0.012), 1)
    sklib._bm_cyl(bm, Vector((-0.35, 0.16, 0.35)), 0.045, 0.6, 'X', 12, 3)        # silencer
    sklib._bm_box(bm, Vector((-0.66, 0, 0.62)), (0.42, 0.14, 0.03), 0)            # rear mudguard
    sklib._bm_box(bm, Vector((0.62, 0, 0.62)), (0.36, 0.12, 0.03), 0)
    sklib._bm_box(bm, Vector((-0.86, 0, 0.58)), (0.02, 0.17, 0.11), 1)            # blank plate
    vs = sklib._bm_cyl(bm, Vector((0.5, 0, 0.62)), 0.02, 0.62, 'Z', 8, 3)          # fork
    for v in vs:
        v.co.x += 0.25 * (v.co.z - 0.62)
    sklib._bm_cyl(bm, Vector((0.6, 0, 1.0)), 0.012, 0.72, 'Y', 8, 1)               # handlebar
    sklib._bm_cyl(bm, Vector((0.68, 0, 0.88)), 0.085, 0.1, 'X', 16, 1)             # headlamp
    sklib._bm_cyl(bm, Vector((-0.1, 0, 0.5)), 0.03, 0.9, 'X', 8, 1)                # frame tube
    body = obj('bike_body', bm, PROPS, (paint, blk, seat, chrome))
    body.parent = root
    sklib.bevel(body, 0.012, 3, 30)
    root.rotation_euler.x = 0.0
    root.rotation_euler = (8 * D2R, 0, rot)      # leaning on its side stand
    return root


def power_line():
    """Concrete poles + two sagging conductors along the south perimeter track (aerator supply)."""
    conc = sklib.concrete_quay(0.5)
    bm = bmesh.new()
    xs = list(np.arange(-228.0, -6.0, 32.0))
    tops = []
    for x in xs:
        y = -25.4
        z0 = height_at(x, y)
        v = sklib._bm_box(bm, Vector((x, y, z0 + 4.0)), (0.16, 0.12, 8.6), 0)
        for vv in v:
            k = (vv.co.z - z0) / 8.6
            vv.co.x = x + (vv.co.x - x) * (1.25 - 0.5 * k)
            vv.co.y = y + (vv.co.y - y) * (1.25 - 0.5 * k)
        sklib._bm_box(bm, Vector((x, y, z0 + 7.9)), (0.08, 1.1, 0.1), 0)
        tops.append([Vector((x, y + sy * 0.45, z0 + 8.0)) for sy in (-1, 1)])
    poles = obj('A-POLES', bm, PROPS, (conc,))
    sklib.bevel(poles, 0.01, 2)
    wire = sklib.flat('wire_alu', (0.35, 0.35, 0.34), rough=0.4, metal=1.0)
    for w_ in range(2):
        cu = bpy.data.curves.new('wire%d' % w_, 'CURVE')
        cu.dimensions, cu.bevel_depth = '3D', 0.008
        sp = cu.splines.new('POLY')
        pts = []
        for a_, b_ in zip(tops, tops[1:]):
            A, B = a_[w_], b_[w_]
            for k in range(8):
                t = k / 8
                pts.append(A.lerp(B, t) - Vector((0, 0, 0.55 * 4 * t * (1 - t))))
        pts.append(tops[-1][w_])
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p.x, p.y, p.z, 1)
        o = sklib.new_obj('A-WIRE-%d' % w_, cu, PROPS)
        o.data.materials.append(wire)


power_line()


def farm_road(x0=-900.0, x1=-26.0, y=-45.0):
    """full-r2: the asphalt road of truck f216 (there at y -10, here moved south of the shed/bike to y -45), gravel
    shoulders, following the terrain; it ends at the farm's south-east corner."""
    xs_ = list(np.arange(x0, x1, 4.0)) + [x1]
    zs = [height_at(x_, y) for x_ in xs_]
    for name, half, dz, mat in (('A-ROAD-shoulder', 5.2, 0.03, sklib.pbr('road_gravel', 'gravel_road', wear=0.3)),
                                ('A-ROAD', 3.5, 0.06, sklib.asphalt(0.35))):
        bm = bmesh.new()
        rows = [[bm.verts.new((x_, y + sy * half + 0.25 * math.sin(x_ * 0.05 + sy), z_ + dz)) for sy in (-1, 1)]
                for x_, z_ in zip(xs_, zs)]
        for a_, b_ in zip(rows, rows[1:]):
            bm.faces.new((a_[0], b_[0], b_[1], a_[1]))
        o = obj(name, bm, PROPS, (mat,))
        o.visible_shadow = False


farm_road()
BIKE = motorbike((-82.2, -38.6, height_at(-82.2, -38.6) + 0.04), 0.3)


# ========================================================================================================= harvest
HAR = C('HARVEST')
pole_m = sklib.pbr('pole_bark', 'bark_brown_02', wear=0.3, scale=0.4)
rope_m = sklib.pbr('rope_coir', 'rough_linen', tint=(0.55, 0.45, 0.28), wear=0.3, scale=0.2)
APEX = Vector((HX + 0.25, HY, 6.3))
legs = [Vector((-1.0, HY + 1.3, height_at(-1.0, HY + 1.3))), Vector((-1.0, HY - 1.3, height_at(-1.0, HY - 1.3))),
        Vector((HX - 2.0, HY, height_at(HX - 2.0, HY)))]
bm = bmesh.new()
for lg in legs:
    p0 = lg - (APEX - lg).normalized() * 0.15
    p1 = APEX + (APEX - lg).normalized() * 0.35
    tube(bm, [p0, p0.lerp(p1, 0.5), p1], [0.07, 0.06, 0.05], 10)
TRIPOD = obj('A-TRIPOD', bm, HAR, (pole_m,))
TRIPOD.data.shade_smooth()
bm = bmesh.new()
sklib._bm_box(bm, APEX + Vector((0, 0, -0.18)), (0.08, 0.12, 0.22), 0)
sklib._bm_cyl(bm, APEX + Vector((0, 0, -0.2)), 0.07, 0.04, 'Y', 16, 0)
REDIRECT = legs[0].lerp(APEX, 0.36)
sklib._bm_box(bm, REDIRECT, (0.09, 0.1, 0.16), 0)
PULLEYS = obj('A-PULLEYS', bm, HAR, (sklib.galvanised(0.5),))
sklib.bevel(PULLEYS, 0.006, 2)

# --- net bag: tapered sack with nylon net + shrimp packed inside
net_m = None


def net_material():
    m, nt = _new_mat('net_nylon')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 400, 200)
    b.inputs['Base Color'].default_value = (0.06, 0.16, 0.12, 1)
    b.inputs['Roughness'].default_value = 0.3
    b.inputs['Coat Weight'].default_value = 0.5
    tr = _n(nt, 'ShaderNodeBsdfTransparent', 400, -150)
    ms = _n(nt, 'ShaderNodeMixShader', 700, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -700, 0)
    _l(nt, tc.outputs['UV'], sep.inputs[0])
    k = 2 * math.pi / 0.03      # 3 cm mesh, diamond
    u = _math(nt, 'ADD', sep.outputs[0], sep.outputs[1], x=-500, y=100)
    v = _math(nt, 'SUBTRACT', sep.outputs[0], sep.outputs[1], x=-500, y=-100)
    su = _math(nt, 'ABSOLUTE', _math(nt, 'SINE', _math(nt, 'MULTIPLY', u, k / 2, x=-350, y=100), x=-200, y=100), x=-50, y=100)
    sv = _math(nt, 'ABSOLUTE', _math(nt, 'SINE', _math(nt, 'MULTIPLY', v, k / 2, x=-350, y=-100), x=-200, y=-100), x=-50, y=-100)
    th = _math(nt, 'MAXIMUM', _maprange(nt, su, 0.0, 0.32, 1.0, 0.0, 100, 100), _maprange(nt, sv, 0.0, 0.32, 1.0, 0.0, 100, -100), x=300, y=0)
    _l(nt, th, ms.inputs[0])
    _l(nt, tr.outputs[0], ms.inputs[1])
    _l(nt, b.outputs[0], ms.inputs[2])
    _l(nt, ms.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'DITHERED'
    m.use_backface_culling = False
    return m


def bag_profile(t):          # t 0 top .. 1 bottom ; radius
    return 0.12 + 0.3 * math.sin(math.pi * min(1, t * 1.15)) ** 0.7


BAG = sklib.new_obj('A-NET-BAG', None, HAR)
bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UVMap')
rings = []
nz_, na_ = 18, 32
for i in range(nz_ + 1):
    t = i / nz_
    rr_ = bag_profile(t) + 0.015 * math.sin(i * 1.7)
    rings.append([bm.verts.new((rr_ * math.cos(2 * math.pi * k / na_) * (1 + 0.06 * math.sin(k * 0.9 + i)),
                                rr_ * math.sin(2 * math.pi * k / na_), -1.05 * t)) for k in range(na_)])
for i in range(nz_):
    for k in range(na_):
        k2 = (k + 1) % na_
        f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
        for lp in f.loops:
            ii = i if lp.vert in rings[i] else i + 1
            kk = rings[ii].index(lp.vert)
            if k2 == 0 and kk == 0:
                kk = na_
            lp[uvl].uv = (kk / na_ * 2.2, ii / nz_ * 1.1)
bmesh.ops.contextual_create(bm, geom=rings[-1])
netob = obj('A-NET-BAG-mesh', bm, HAR, (net_material(),), uv=False)
netob.parent = BAG
netob.data.shade_smooth()

# shrimp scan (CC0, ffish.asia greasyback, used as unlabelled filler)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=REPO + '/assets-src/models/plant-line/greasyback-shrimp-lo.glb')
sh = [o for o in set(bpy.data.objects) - before if o.type == 'MESH'][0]
for o in set(bpy.data.objects) - before:
    if o is not sh:
        bpy.data.objects.remove(o)
sh.parent = None
sc = 0.14 / max(sh.dimensions)
sh.data.transform(Matrix.Diagonal((sc, sc, sc, 1)))
sh.data.transform(Matrix.Translation(-Vector(sh.data.vertices[0].co) * 0))
sh.location = (0, 0, 0)
sh.rotation_euler = (0, 0, 0)
sh.scale = (1, 1, 1)
dm = sh.modifiers.new('dec', 'DECIMATE')
dm.ratio = 0.12
sklib.apply_mods(sh)
for c in list(sh.users_collection):
    c.objects.unlink(sh)
for mat in sh.data.materials:      # wet raw shrimp: glossier, a touch translucent
    if mat and mat.node_tree:
        for nd in mat.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED':
                nd.inputs['Roughness'].default_value = 0.22
                nd.inputs['Coat Weight'].default_value = 0.6
                nd.inputs['Subsurface Weight'].default_value = 0.2
SHRIMP_ME = sh.data
bpy.data.objects.remove(sh)
mr = random.Random(21)
for k in range(170):
    t = mr.uniform(0.12, 0.95)
    a = mr.uniform(0, 6.28)
    rr_ = bag_profile(t) * mr.uniform(0.55, 0.88)
    o = sklib.new_obj('bag_shrimp_%03d' % k, SHRIMP_ME, HAR, loc=(rr_ * math.cos(a), rr_ * math.sin(a), -1.05 * t),
                      rot=(mr.uniform(0, 6.28), mr.uniform(0, 6.28), mr.uniform(0, 6.28)))
    o.parent = BAG
    o.scale = (mr.uniform(0.85, 1.1),) * 3
# a dark inner mass so the packed bag never reads hollow
bm = bmesh.new()
res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
for v in bm.verts:
    t = min(1, max(0, -(v.co.z - 1) / 2))
    v.co = Vector((v.co.x * bag_profile(t) * 0.62, v.co.y * bag_profile(t) * 0.62, -0.55 + v.co.z * 0.45))
core = obj('bag_core', bm, HAR, (sklib.flat('shrimp_mass', (0.42, 0.38, 0.34), rough=0.25, var=0.35, scale=60, bump=0.5),))
core.parent = BAG
core.data.shade_smooth()

# bag keys: submerged (top just below the surface) -> lifted out f148-182 -> swung toward the crates f196-216
for f, p in ((1, (HX, HY, W - 0.05)), (138, (HX, HY, W - 0.05)), (176, (HX + 0.1, HY, W + 1.45)),
             (196, (HX + 0.2, HY, W + 1.5)), (216, (HX + 0.9, HY - 0.3, W + 1.55))):
    BAG.location = p
    BAG.keyframe_insert('location', frame=f)
for f, r_ in ((1, 0), (160, 0.0), (184, 0.05), (196, -0.04), (216, 0.03)):
    BAG.rotation_euler = (r_, r_ * 0.5, 0)
    BAG.keyframe_insert('rotation_euler', frame=f)
sklib.ease_keys(BAG)

# draining water: droplets from the bag bottom (particles, gravity, motion-blurred)
drop_m = bpy.data.materials.get('pond_water')
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.006)
DROP = obj('A-DROPLET', bm, False if False else HAR, (sklib.flat('droplet', (0.8, 0.85, 0.8), rough=0.02, **{'Transmission Weight': 1.0, 'IOR': 1.33}),), uv=False)
DROP.hide_render = DROP.hide_viewport = False
for c in list(DROP.users_collection):
    c.objects.unlink(DROP)
bm = bmesh.new()
for i in range(12):
    t = 0.45 + 0.55 * i / 12
    a = i * 2.4
    pass
res = bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=0.3)
emit = obj('A-BAG-DRIP-EMIT', bm, HAR, ())
emit.parent = BAG
emit.location = (0, 0, -0.75)
emit.hide_render = True
ps_mod = emit.modifiers.new('drip', 'PARTICLE_SYSTEM')
pset = ps_mod.particle_system.settings
pset.count = 2600
pset.frame_start, pset.frame_end = 142, 216
pset.lifetime, pset.lifetime_random = 16, 0.4
pset.emit_from = 'FACE'
pset.normal_factor = 0.0
pset.object_align_factor = (0, 0, -0.6)
pset.factor_random = 0.25
pset.render_type = 'OBJECT'
pset.instance_object = DROP
pset.particle_size, pset.size_random = 1.0, 0.6
pset.use_rotations = False
emit.show_instancer_for_render = False

# ropes: apex -> bag (hooked), apex -> redirect pulley -> pullers' hands -> slack tail
rope_curves = []


def rope(name, pts, hooks=()):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth, cu.bevel_resolution = 0.011, 2
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, p.z, 1)
    ob = sklib.new_obj(name, cu, HAR)
    ob.data.materials.append(rope_m)
    for i, (target, bone) in hooks:
        md = ob.modifiers.new('hook%d' % i, 'HOOK')
        md.object = target
        if bone:
            md.subtarget = bone
            pb = target.pose.bones[bone]
            M = target.matrix_world @ pb.matrix
        else:
            M = target.matrix_world.copy()
        md.matrix_inverse = M.inverted()
        md.vertex_indices_set([i])
    return ob


bpy.context.view_layer.update()
rope('rope_bag', [APEX + Vector((0, 0, -0.25)), BAG.matrix_world @ Vector((0, 0, 0.02))], [(1, (BAG, None))])

# r5: drag net (seine) IN the water: an arc around the crew from bank to bank, float line on the surface, the
# netting hanging down to the bed; below the surface it is seen refracted through the murky water and fades into it
def seine_material():
    m, nt = _new_mat('net_seine')
    out = _n(nt, 'ShaderNodeOutputMaterial', 1100, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 600, 200)
    b.inputs['Roughness'].default_value = 0.45
    tr = _n(nt, 'ShaderNodeBsdfTransparent', 600, -150)
    ms = _n(nt, 'ShaderNodeMixShader', 900, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    sep = _n(nt, 'ShaderNodeSeparateXYZ', -700, 0)
    _l(nt, tc.outputs['UV'], sep.inputs[0])
    k = 2 * math.pi / 0.04
    u = _math(nt, 'ADD', sep.outputs[0], sep.outputs[1], x=-500, y=100)
    v = _math(nt, 'SUBTRACT', sep.outputs[0], sep.outputs[1], x=-500, y=-100)
    su = _math(nt, 'ABSOLUTE', _math(nt, 'SINE', _math(nt, 'MULTIPLY', u, k / 2, x=-350, y=100), x=-200, y=100), x=-50, y=100)
    sv = _math(nt, 'ABSOLUTE', _math(nt, 'SINE', _math(nt, 'MULTIPLY', v, k / 2, x=-350, y=-100), x=-200, y=-100), x=-50, y=-100)
    th = _math(nt, 'MAXIMUM', _maprange(nt, su, 0.0, 0.26, 1.0, 0.0, 100, 100), _maprange(nt, sv, 0.0, 0.26, 1.0, 0.0, 100, -100), x=300, y=0)
    geo = _n(nt, 'ShaderNodeNewGeometry', -700, -400)
    gz = _n(nt, 'ShaderNodeSeparateXYZ', -500, -400)
    _l(nt, geo.outputs['Position'], gz.inputs[0])
    deep = _maprange(nt, gz.outputs['Z'], W, W - 0.9, 0.0, 1.0, -300, -400)
    _l(nt, _mix(nt, deep, (0.32, 0.5, 0.4), (0.14, 0.17, 0.08), 'MIX', 300, 300), b.inputs['Base Color'])
    _l(nt, _math(nt, 'MULTIPLY', th, _maprange(nt, deep, 0, 1, 1.0, 0.35, 300, -300), x=500, y=0), ms.inputs[0])
    _l(nt, tr.outputs[0], ms.inputs[1])
    _l(nt, b.outputs[0], ms.inputs[2])
    _l(nt, ms.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'DITHERED'
    m.use_backface_culling = False
    return m


SEINE_C, SEINE_R = Vector((HX + 0.2, HY - 0.3, 0)), 5.2
bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UVMap')
arc = [a * D2R for a in np.linspace(98, 262, 72)]
cols = []
fl_pts = []
for j, a in enumerate(arc):
    x = SEINE_C.x + SEINE_R * math.cos(a)
    y = SEINE_C.y + SEINE_R * math.sin(a) * 1.15
    bed_z = height_at(x, y)
    top = W + 0.07 + 0.015 * math.sin(j * 0.9)
    bot = max(bed_z + 0.03, W - 1.15)
    sag = 0.12 * math.sin(math.pi * j / (len(arc) - 1))
    cols.append([bm.verts.new((x + sag * math.cos(a) * (r_ / 7) ** 2, y, top + (bot - top) * r_ / 7)) for r_ in range(8)])
    fl_pts.append(Vector((x, y, top - 0.05)))
alen = [0.0]
for j in range(1, len(arc)):
    alen.append(alen[-1] + (fl_pts[j] - fl_pts[j - 1]).length)
for j in range(len(arc) - 1):
    for r_ in range(7):
        f = bm.faces.new((cols[j][r_], cols[j + 1][r_], cols[j + 1][r_ + 1], cols[j][r_ + 1]))
        for lp in f.loops:
            jj = j if lp.vert in cols[j] else j + 1
            lp[uvl].uv = (alen[jj], -(lp.vert.co.z - W))
SEINE = obj('A-NET-SEINE', bm, HAR, (seine_material(),), uv=False)
SEINE.visible_shadow = False
cu_ = bpy.data.curves.new('seine_headrope', 'CURVE')
cu_.dimensions, cu_.bevel_depth = '3D', 0.009
sp_ = cu_.splines.new('POLY')
sp_.points.add(len(fl_pts) - 1)
for i_, p_ in enumerate(fl_pts):
    sp_.points[i_].co = (p_.x, p_.y, p_.z, 1)
hr = sklib.new_obj('A-NET-SEINE-rope', cu_, HAR)
hr.data.materials.append(rope_m)
bm = bmesh.new()
for j in range(2, len(arc) - 2, 3):
    p_ = fl_pts[j]
    t_ = Vector((fl_pts[j + 1] - fl_pts[j - 1])).normalized()
    vs = sklib._bm_cyl(bm, Vector((0, 0, 0)), 0.045, 0.11, 'X', 12, 0)
    M = Matrix.Translation(p_ + Vector((0, 0, -0.01))) @ t_.to_track_quat('X', 'Z').to_matrix().to_4x4()
    for v_ in vs:
        v_.co = M @ v_.co
floats = obj('A-NET-SEINE-floats', bm, HAR, (sklib.plastic(look.hex_rgb('#e2a03a'), 0.4, name='seine_float'),))
sklib.bevel(floats, 0.008, 2)
bm = bmesh.new()
for j in (0, len(arc) - 1):
    p_ = fl_pts[j]
    b0 = Vector((p_.x, p_.y, height_at(p_.x, p_.y) - 0.3))
    tube(bm, [b0, b0 + Vector((0.03, 0, 0.75)), b0 + Vector((0.06, 0, 1.5))], [0.035, 0.03, 0.025], 8)
stakes = obj('A-NET-SEINE-stakes', bm, HAR, (pole_m,))

# crates of ice on the bund (A-CRATE-SHRIMP x6), shrimp already in four of them
CRATES = []
for k, (dx, dy, col) in enumerate([(0.1, -1.6, (0.55, 0.06, 0.04)), (0.75, -1.6, (0.05, 0.22, 0.55)),
                                    (0.1, -2.1, (0.05, 0.22, 0.55)), (0.75, -2.1, (0.55, 0.06, 0.04)),
                                    (1.4, -1.75, (0.55, 0.06, 0.04)), (0.45, -2.62, (0.05, 0.35, 0.18))]):
    x, y = -1.2 + dx, HY + dy
    cr = sklib.crate(col, 'A-CRATE-SHRIMP-%d' % k, HAR)
    cr.location = (x, y, height_at(x, y) - 0.005)
    cr.rotation_euler = (0, 0, random.Random(k).uniform(-0.12, 0.12))
    bpy.context.view_layer.update()
    sklib.crushed_ice_fill(cr, density=1.0, name='ice_%d' % k, coll=HAR, seed=k, depth=0.12)
    if k < 4:
        rr2 = random.Random(70 + k)
        for j in range(22):
            o = sklib.new_obj('crate%d_shrimp_%02d' % (k, j), SHRIMP_ME, HAR,
                              loc=(rr2.uniform(-0.22, 0.22), rr2.uniform(-0.13, 0.13), 0.215 + rr2.uniform(0, 0.03)),
                              rot=(rr2.uniform(-0.4, 0.4), rr2.uniform(-0.4, 0.4), rr2.uniform(0, 6.28)))
            o.parent = cr
    CRATES.append(cr)

# ============================================================================================================ people
PEOPLE = C('PEOPLE')
if not FAST:
    import people   # noqa: E402

    def person(name, outfit, pose, x, y, face_to, seed, age, tone, z=None, sex='male', body=None):
        zz = height_at(x, y) if z is None else z
        rz = math.atan2(face_to[0] - x, -(face_to[1] - y))
        p = people.make_person(name, sex=sex, age=age, skin_tone=tone, outfit=outfit, pose=pose,
                               location=(x, y, zz), rotation_z=rz, seed=seed, body=body)
        for o in [p] + list(p.children):
            for c in list(o.users_collection):
                c.objects.unlink(o)
            PEOPLE.objects.link(o)
        return p

    P1 = person('P-FARM-1', 'cotton_shirt_lungi_towel', 'pull_rope', -0.95, HY + 2.6, (-1.0, HY - 2), 1, 0.55, 0.7)
    P2 = person('P-FARM-2', 'cotton_shirt_lungi_towel', 'pull_rope', -0.85, HY + 4.1, (-1.0, HY - 2), 2, 0.3, 0.85,
                body={'weight': 0.35})
    P3 = person('P-FARM-3', 'tshirt_shorts', 'carry', HX - 0.6, HY + 0.2, (HX, HY), 3, 0.25, 0.8)
    P4 = person('P-FARM-4', 'tshirt_shorts', 'carry', HX - 0.55, HY - 0.8, (HX, HY), 4, 0.4, 0.95)
    P5 = person('P-FARM-5', 'cotton_shirt_lungi_towel', 'stand', 0.5, HY - 0.9, (HX, HY), 5, 0.7, 0.75)
    P6 = person('P-FARM-6', 'cotton_shirt_lungi_towel', 'walk', -118.0, 21.1, (-50, 21.1), 6, 0.45, 0.65)
    def recolor(p, part, color):
        for c in p.children:
            if c.type == 'MESH' and c.name.split('.', 1)[-1] == part:
                people.tint_mpfb(c, color, plain=True)
    recolor(P1, 'male_casualsuit01', (0.55, 0.64, 0.76))
    recolor(P2, 'male_casualsuit01', (0.74, 0.6, 0.46))
    recolor(P3, 'male_casualsuit04', (0.42, 0.12, 0.1))
    recolor(P4, 'male_casualsuit04', (0.16, 0.22, 0.3))
    recolor(P5, 'male_casualsuit01', (0.8, 0.77, 0.66))
    # r5: coloured checked lungis (all-white mundus read as robes at this distance)
    for p_, nm_, c1_, c2_ in ((P2, 'P2_lungi', (0.12, 0.2, 0.38), (0.55, 0.5, 0.42)),
                              (P1, 'P1_lungi', (0.1, 0.3, 0.16), (0.45, 0.42, 0.3)),
                              (P5, 'P5_lungi', (0.42, 0.1, 0.1), (0.5, 0.42, 0.3))):
        for c in p_.children:
            if c.name.endswith('.lungi'):
                c.data.materials[0] = people.fabric(nm_, c1_, pattern='plaid', color2=c2_)
    people.animate_cycle(P1, 'pull', 1, 216, 0.0)
    people.animate_cycle(P2, 'pull', 1, 216, 0.35)
    people.animate_cycle(P3, 'work', 1, 216, 0.2, 0.5)
    people.animate_cycle(P4, 'work', 1, 216, 0.7, 0.5)
    people.animate_cycle(P5, 'work', 1, 216, 0.5, 0.4)
    people.animate_cycle(P6, 'walk', 1, 216, 0.0)
    z6 = height_at(-118.0, 21.1)
    P6.location = (-118.0, 21.1, P6.location.z)
    P6.keyframe_insert('location', frame=1)
    P6.location = (-118.0 + 1.25 * 9.0, 21.1, P6.location.z)
    P6.keyframe_insert('location', frame=216)
    for fc in sklib._fcurves(P6):
        if fc.data_path == 'location':
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    bpy.context.view_layer.update()

    def hand(p, side):
        pb = p.pose.bones['hand_' + side]
        return p.matrix_world @ ((pb.head + pb.tail) / 2)
    pts = [APEX + Vector((0.05, 0, -0.2)), REDIRECT + Vector((0, -0.06, 0)), hand(P1, 'l'), hand(P1, 'r'),
           hand(P2, 'l'), hand(P2, 'r')]
    tail = hand(P2, 'r') + Vector((0.25, 0.9, -0.6))
    end = Vector((tail.x + 0.3, tail.y + 0.6, height_at(tail.x + 0.3, tail.y + 0.6) + 0.02))
    pts += [tail, end]
    rope('rope_haul', pts, [(2, (P1, 'hand_l')), (3, (P1, 'hand_r')), (4, (P2, 'hand_l')), (5, (P2, 'hand_r'))])


# ============================================================================================================ egrets
def egret_mesh(flying=False):
    bm = bmesh.new()
    white = sklib.flat('egret_feather', (0.86, 0.86, 0.83), rough=0.7, var=0.04, scale=80, bump=0.2,
                       **{'Subsurface Weight': 0.1})
    beak = sklib.flat('egret_beak', (0.75, 0.55, 0.08), rough=0.4)
    leg = sklib.flat('egret_leg', (0.04, 0.04, 0.03), rough=0.6)
    if flying:
        body = [Vector((x, 0, 0)) for x in np.linspace(-0.35, 0.3, 8)]
        rad = [0.02, 0.07, 0.09, 0.095, 0.09, 0.07, 0.05, 0.035]
        tube(bm, body, rad, 10, 0)
        tube(bm, [Vector((0.3, 0, 0)), Vector((0.36, 0, 0.03)), Vector((0.4, 0, 0.0))], [0.035, 0.03, 0.025], 8, 0)
        tube(bm, [Vector((0.4, 0, 0)), Vector((0.52, 0, -0.02))], [0.012, 0.002], 6, 1)
        for sy in (-1, 1):
            tube(bm, [Vector((-0.3, sy * 0.03, -0.02)), Vector((-0.75, sy * 0.04, -0.05))], [0.006, 0.004], 4, 2)
    else:
        body = [Vector((x, 0, 0.62 + 0.25 * x)) for x in np.linspace(-0.3, 0.2, 7)]
        tube(bm, body, [0.02, 0.07, 0.09, 0.09, 0.08, 0.06, 0.04], 10, 0)
        neck = [Vector((0.2 + 0.07 * math.sin(t * 3.1), 0, 0.68 + 0.36 * t)) for t in np.linspace(0, 1, 8)]
        tube(bm, neck, [0.035 - 0.015 * t for t in np.linspace(0, 1, 8)], 8, 0)
        h = neck[-1]
        tube(bm, [h - Vector((0.03, 0, 0)), h + Vector((0.04, 0, 0.01))], [0.028, 0.025], 8, 0)
        tube(bm, [h + Vector((0.04, 0, 0.0)), h + Vector((0.17, 0, -0.02))], [0.01, 0.002], 6, 1)
        for sy in (-1, 1):
            tube(bm, [Vector((0, sy * 0.04, 0.6)), Vector((0.02, sy * 0.05, 0.3)), Vector((0, sy * 0.05, 0.0))],
                 [0.009, 0.007, 0.006], 5, 2)
    ob = sklib._mesh_obj('egret_fly' if flying else 'egret_stand', bm, False)
    for mm in (white, beak, leg):
        ob.data.materials.append(mm)
    ob.data.shade_smooth()
    return ob


EGR = C('EGRETS')
eg_stand = egret_mesh(False)
for k, (x, y, rz) in enumerate([(-60.2, -6.0, 1.2), (-58.4, 2.0, 2.6), (-112.0, -21.6, 0.3), (-118.0, 40.0, 4.0)]):
    o = sklib.new_obj('A-FX-EGRET-%d' % k, eg_stand.data, EGR, loc=(x, y, height_at(x, y)), rot=(0, 0, rz))
eg_fly = egret_mesh(True)
wing_m = bpy.data.materials['egret_feather']
for k, (p0, p1, z0) in enumerate([((-120, -30), (-40, 30), 9.0), ((-60, 40), (-20, -40), 7.0)]):
    root = sklib.new_obj('A-FX-EGRET-F%d' % k, eg_fly.data, EGR)
    for f, p, z in ((90, p0, z0), (170, p1, z0 + 2)):
        root.location = (p[0], p[1], z)
        root.keyframe_insert('location', frame=f)
    d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0))
    root.rotation_euler = (0, 0, math.atan2(d.y, d.x))
    for fc in sklib._fcurves(root):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    for sy in (-1, 1):
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in ((-0.12, 0, 0), (0.12, 0, 0), (0.05, sy * 0.75, 0.0), (-0.12, sy * 0.72, 0))]
        bm.faces.new(vs if sy > 0 else vs[::-1])
        wgo = obj('egret_wing', bm, EGR, (wing_m,), uv=False)
        so = wgo.modifiers.new('s', 'SOLIDIFY')
        so.thickness = 0.015
        wgo.parent = root
        drive(wgo, 'rotation_euler', '%d*0.6*sin(frame*0.55+%d)' % (sy, k), 0)

# ============================================================================================================== mist
def mist_material():
    m, nt = _new_mat('dawn_mist')
    out = _n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', 400, 200)
    b.inputs['Base Color'].default_value = (0.95, 0.88, 0.8, 1)
    b.inputs['Roughness'].default_value = 1.0
    b.inputs['Emission Color'].default_value = (1.0, 0.82, 0.65, 1)
    b.inputs['Emission Strength'].default_value = 0.1
    tr = _n(nt, 'ShaderNodeBsdfTransparent', 400, -150)
    ms = _n(nt, 'ShaderNodeMixShader', 700, 0)
    tc = _n(nt, 'ShaderNodeTexCoord', -900, 0)
    mp = _n(nt, 'ShaderNodeMapping', -700, 100)
    _l(nt, tc.outputs['Object'], mp.inputs['Vector'])
    drive(mp.inputs['Location'], 'default_value', 'frame*0.03', 0)
    nz = _n(nt, 'ShaderNodeTexNoise', -500, 100)
    nz.noise_dimensions = '3D'
    nz.inputs['Scale'].default_value = 0.035
    nz.inputs['Detail'].default_value = 5.0
    nz.inputs['Roughness'].default_value = 0.6
    _l(nt, mp.outputs[0], nz.inputs['Vector'])
    gen = _n(nt, 'ShaderNodeSeparateXYZ', -700, -200)
    _l(nt, tc.outputs['Generated'], gen.inputs[0])
    ex = _math(nt, 'MULTIPLY', _maprange(nt, gen.outputs['X'], 0.0, 0.15, 0, 1, -500, -200),
               _maprange(nt, gen.outputs['X'], 1.0, 0.85, 0, 1, -500, -350), x=-300, y=-250)
    ey = _math(nt, 'MULTIPLY', _maprange(nt, gen.outputs['Y'], 0.0, 0.15, 0, 1, -500, -500),
               _maprange(nt, gen.outputs['Y'], 1.0, 0.85, 0, 1, -500, -650), x=-300, y=-550)
    a = _math(nt, 'MULTIPLY', _maprange(nt, nz.outputs['Fac'], 0.5, 0.75, 0.0, 0.13, -300, 100),
              _math(nt, 'MULTIPLY', ex, ey, x=-150, y=-400), x=100, y=0)
    # r5: from the aerial the mist sheets read as cloud blobs on the water -> fade out with view distance
    cd = _n(nt, 'ShaderNodeCameraData', -500, -800)
    a = _math(nt, 'MULTIPLY', a, _maprange(nt, cd.outputs['View Distance'], 60.0, 150.0, 1.0, 0.0, -300, -800), x=250, y=0)
    _l(nt, a, ms.inputs[0])
    _l(nt, tr.outputs[0], ms.inputs[1])
    _l(nt, b.outputs[0], ms.inputs[2])
    _l(nt, ms.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'
    return m


MIST = C('MIST')
mist_m = mist_material()
for i, (x0, x1, y0, y1) in enumerate(NEAR):
    if i in DRY:
        continue
    for h_ in (0.35, 1.1):
        bm = bmesh.new()
        vs = [bm.verts.new((x, y, W + h_)) for x, y in ((x0 - 1, y0 - 1), (x1 + 1, y0 - 1), (x1 + 1, y1 + 1), (x0 - 1, y1 + 1))]
        bm.faces.new(vs)
        mo = obj('mist_%02d_%d' % (i, int(h_ * 10)), bm, MIST, (mist_m,), uv=False)
        mo.visible_shadow = False
        if i == 12:   # keep the harvest pond clear around the bag/crew
            mo.hide_render = h_ > 1

def sun_disc():
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=6000 * math.tan(0.29 * D2R))
    m, nt = _new_mat('sun_disc')
    out = _n(nt, 'ShaderNodeOutputMaterial', 400, 0)
    em = _n(nt, 'ShaderNodeEmission', 100, 0)
    em.inputs['Color'].default_value = tuple(sklib.kelvin_rgb(3300)) + (1,)
    em.inputs['Strength'].default_value = 60.0
    _l(nt, em.outputs[0], out.inputs['Surface'])
    o = obj('SUN-DISC', bm, ENV, (m,), uv=False)
    o.visible_shadow = o.visible_diffuse = o.visible_glossy = False
    if hasattr(o, 'visible_volume_scatter'):
        o.visible_volume_scatter = False
    for f, el, az in ((1, 15, 90), (216, 4, 95)):
        e_, a_ = el * D2R, az * D2R
        dv = Vector((math.sin(a_) * math.cos(e_), math.cos(a_) * math.cos(e_), math.sin(e_)))
        o.location = CAM_END + dv * 6000
        o.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
        o.keyframe_insert('location', frame=f)
        o.keyframe_insert('rotation_euler', frame=f)
    return o


sun_disc()

def add_haze(mat, k=2600.0, amax=0.26, col=look.hex_rgb('#f4e2c0'), st=0.85):
    """Aerial perspective: blend toward the dawn horizon colour with view distance (no compositor)."""
    nt = mat.node_tree
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    lk = out.inputs['Surface'].links
    if not lk:
        return
    src = lk[0].from_socket
    cd = nt.nodes.new('ShaderNodeCameraData')
    f = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, _math(nt, 'EXPONENT', _math(nt, 'DIVIDE', cd.outputs['View Distance'], -k))), amax)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = col + (1,)
    em.inputs['Strength'].default_value = st
    ms = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(f, ms.inputs[0])
    nt.links.new(src, ms.inputs[1])
    nt.links.new(em.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs['Surface'])


for mn in ('pond_terrain', 'pond_water_far', 'palm_leaf', 'palm_rachis', 'coconut', 'palm_bark', 'neem_leaf',
           'casuarina_needle', 'shrub_leaf', 'bark_tree', 'grass_blade', 'tin_roof', 'brick_wall', 'pole_bark', 'asphalt',
           'road_gravel'):
    if bpy.data.materials.get(mn):
        add_haze(bpy.data.materials[mn])
for m_ in list(bpy.data.materials):
    if m_.name.startswith('house_wall') or m_.name in ('house_opening', 'tin_roof.001'):
        add_haze(m_)

# ============================================================================================================ camera
cam = sklib.camera('CAM', 24.0, (-560.0, -60.0, 300.0), (0, 0, 0))
cam.data.clip_start, cam.data.clip_end = 0.1, 12000
p_ = 35 * D2R
aim1 = Vector((-560.0, -60.0, 300.0)) + 428.0 * Vector((math.cos(p_), 0, -math.sin(p_)))
hz = 95 * D2R
pe = 1.33 * D2R
aim_end = CAM_END + 100.0 * Vector((math.sin(hz) * math.cos(pe), math.cos(hz) * math.cos(pe), math.sin(pe)))
KEYS = [
    (1, (-560.0, -60.0, 300.0), aim1, 24.0),
    (45, (-330.0, -30.0, 110.0), (-110.0, -8.0, 4.0), 24.0),
    (90, (-92.0, -4.0, 13.0), (-20.0, -8.0, 2.5), 24.0),
    (125, (-46.0, -9.0, 5.6), (-6.0, -10.0, 2.4), 26.0),
    (160, (-11.5, -18.5, 3.4), (HX + 0.4, HY, 2.7), 30.0),
    (188, (-6.4, -17.4, 3.3), (HX + 0.9, HY - 0.4, 3.0), 32.0),
    (216, tuple(CAM_END), aim_end, 35.0),
]
sklib.camera_path(cam, [(f, Vector(l), Vector(a), le) for f, l, a, le in KEYS])
d = sklib.dof(cam, 400.0, 5.6)
for f, fd in ((1, 520), (90, 75), (125, 45), (160, 11.0), (188, 8.5), (204, 40), (216, 400)):
    cam.data.dof.focus_distance = fd
    cam.data.dof.keyframe_insert('focus_distance', frame=f)
sklib.ease_keys(cam.data)

# ===================================================================================================== perf culling
# r5: things the camera can no longer see (all keys CONSTANT). After f112 the camera looks east over the harvest
# pond and the sea: the far groves, field palms, hamlets and far pond blocks are behind/outside the frustum.
def hide_ranges(ob, shown):
    """shown = list of (first, last) frame ranges where ob renders; hidden elsewhere."""
    keys = {1: True}
    for a, b in shown:
        keys[a] = False
        keys[b + 1] = True
    for f_, h_ in sorted(keys.items()):
        ob.hide_render = h_
        ob.keyframe_insert('hide_render', frame=f_)


FAR_PREFIX = ('grove_', 'clump_', 'scrub_', 'rowpalm_', 'house_', 'A-POND-WATER-FAR')
n_cull = 0
for o in list(bpy.data.objects):
    if o.name.startswith(FAR_PREFIX) and o.users_collection and o.users_collection[0].name in ('VEG', 'ENV'):
        hide_ranges(o, [(1, 112)])
        n_cull += 1
if not FAST:
    for o in list(PEOPLE.all_objects) + list(HAR.all_objects):     # crew/harvest are sub-pixel in the aerial
        if not o.hide_render:
            hide_ranges(o, [(50, 216)])
            n_cull += 1
    gs = TERRAIN.modifiers.get('grass_scatter')
    if gs:
        for f_, v_ in ((1, False), (60, True)):
            gs.show_render = v_
            gs.keyframe_insert('show_render', frame=f_)
print('culled', n_cull)
# end of the shot: the camera turns to the open sea -> each land object is hidden after the last frame (>= 170)
# in which any of its bounding-box corners (instances: a 6 m / 16 m tall proxy) is inside the (padded) frustum
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
cam_ = bpy.data.objects['CAM']


def _pts(o):
    if o.type == 'EMPTY' and o.instance_collection:
        c = o.matrix_world.translation
        return [c + Vector((dx, dy, dz)) for dx in (-6, 6) for dy in (-6, 6) for dz in (0, 16)]
    if o.type in ('MESH', 'CURVE'):
        return [o.matrix_world @ Vector(b) for b in o.bound_box]
    return []


late = [o for cn in ('VEG', 'PROPS', 'AERATORS', 'MIST', 'HARVEST', 'PEOPLE', 'EGRETS')
        for o in bpy.data.collections[cn].all_objects
        if not o.name.startswith(FAR_PREFIX) and (not o.hide_render or o.animation_data)]
last = {o.name: 169 for o in late}
for f_ in range(170, 217):
    s.frame_set(f_)
    for o in late:
        for p in _pts(o):
            v = world_to_camera_view(s, cam_, p)
            if v.z > 0 and -0.15 < v.x < 1.15 and -0.15 < v.y < 1.15:
                last[o.name] = f_
                break
n_late = 0
for o in late:
    if last[o.name] < 214:
        o.hide_render = False
        o.keyframe_insert('hide_render', frame=last[o.name] + 1)
        o.hide_render = True
        o.keyframe_insert('hide_render', frame=last[o.name] + 2)
        n_late += 1
s.frame_set(1)
print('late-culled', n_late, 'of', len(late))
# shadow casters that never matter: the sea, low scrub/clumps far out on the land
SEA.visible_shadow = False
for o in bpy.data.objects:
    if o.name.startswith(('scrub_', 'clump_')):
        o.visible_shadow = False
SUN.data.shadow_maximum_resolution = 0.008
s.eevee.shadow_resolution_scale = 0.5
s.eevee.ray_tracing_options.trace_max_roughness = 0.3

# ============================================================================================================ render
e = s.eevee
e.volumetric_end = 60.0
e.volumetric_tile_size = '16'
e.volumetric_samples = 32
s.frame_set(1)
sklib.finish('pond', 'dawn')
# r5 perf (after sklib's defaults): 32 spp + 4 shadow steps (checked for noise on the r8 stills)
e.taa_render_samples = 32
e.shadow_step_count = 4
# ============================================================================================ art pass (issue #75)
GRADE_C, GRADE_SAT, MIST_D, EXPO = 0.0, 1.08, 0.004, 0.35


def art_look(s):
    """COLOR_SCRIPT row 11 grade. World fog (look.fog) blocks the sun in EEVEE (world volumes are infinite), so the
    low pond mist is a mesh volume over the farm instead; it only renders inside the 60 m volumetric range."""
    p = look.PRESETS['pond']
    look.view(s, p['look'], exposure=EXPO)   # keep frames at least as bright as before the art pass
    # complementary (COLOR_SCRIPT §3): cool zenith-blue shadows against warm sunrise-yellow highlights
    look.grade(s, lift='#3f6f9a', gain=p['gain'], sat=GRADE_SAT, contrast=GRADE_C, bloom=0.15, vignette=0.1,
               lift_amt=0.02, gain_amt=0.03)
    m = bpy.data.materials.get('pond_mist_vol') or bpy.data.materials.new('pond_mist_vol')
    m.use_nodes = True
    t = m.node_tree
    t.nodes.clear()
    out = t.nodes.new('ShaderNodeOutputMaterial')
    v = t.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (*look.hex_rgb('#f4e2c0'), 1)
    v.inputs['Anisotropy'].default_value = 0.55
    geo = t.nodes.new('ShaderNodeNewGeometry')
    sep = t.nodes.new('ShaderNodeSeparateXYZ')
    t.links.new(geo.outputs['Position'], sep.inputs[0])
    mr = t.nodes.new('ShaderNodeMapRange')          # densest on the water, thinning out by 9 m
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = 1.5, 9.0
    mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = MIST_D, MIST_D * 0.15
    t.links.new(sep.outputs['Z'], mr.inputs['Value'])
    t.links.new(mr.outputs[0], v.inputs['Density'])
    t.links.new(v.outputs['Volume'], out.inputs['Volume'])
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    ob = bpy.data.objects.get('SK_POND_MIST')
    if ob is None:
        me = bpy.data.meshes.new('SK_POND_MIST')
        bm.to_mesh(me)
        ob = bpy.data.objects.new('SK_POND_MIST', me)
        s.collection.objects.link(ob)
        me.materials.append(m)
    bm.free()
    ob.location, ob.scale = (-60.0, -10.0, 5.0), (260.0, 220.0, 10.0)
    ob.visible_shadow = False
    e = s.eevee
    e.volumetric_end, e.volumetric_tile_size, e.volumetric_samples = 60.0, '16', 24


art_look(s)


def end_ramp(s):
    """Brighten into BRIDGE_HORIZON so f216 meets sea f1 (luma ~224): exposure EXPO at f180 -> 1.05 at f216."""
    vs = s.view_settings
    for f_, ex in ((180, EXPO), (216, 1.05)):
        vs.exposure = ex
        vs.keyframe_insert('exposure', frame=f_)
    vs.exposure = EXPO


end_ramp(s)
bpy.ops.wm.save_mainfile(compress=True)
