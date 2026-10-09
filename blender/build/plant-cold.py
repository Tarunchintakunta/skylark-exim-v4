"""S7 plant-cold.blend -> v-cold (1-192, cold) | v-pack (192-383, int) | v-freeze (383-574, cold).
One continuous camera flight through the Anandapuram plant: reefer/dock doors (BRIDGE_DOOR, f1) open into the cold
store, down the frosted high-bay aisle past an electric reach truck lowering the hero pallet, rise to a high view,
through a glazed sliding door into the packing hall (pallet build -> strapping -> label -> hero carton lid closed),
then upstream along the IQF spiral-freezer outfeed (glazed shrimp, glazing spray, vapour) to a top-down of the
raw-shrimp infeed belt (BRIDGE_BELT, f574).

   $B -b --factory-startup --python assets-src/blender/build/plant-cold.py                 (build + save)
   then test stills from the saved file (lock only the render): see build/plant-cold-stills.py

World layout (metres, Z up). Camera travels roughly along -X.
  cold store  x -30.0..0, y -1.8..13.7, ceiling 10.0 | dock doors in the x=0 wall at y=0 | main aisle y -1.8..1.6
  packing hall x -56..-30.15, y -4..8, ceiling 5.0  | glazed sliding door at x=-30.1, y=0 | line along y=1.2
  IQF spiral housing x -55.5..-49.5; outfeed mouth y=1.2, infeed mouth y=3.4 (belts top z=0.95)
BRIDGE_BELT: empty 'BRIDGE_BELT' at the infeed belt surface; camera at f574 = BRIDGE_BELT.matrix_world @ (0,0,1.0),
rotation = BRIDGE_BELT rotation (0,0,90deg: looking straight down, image up = belt travel = into the freezer).
"""
import math
import random
import sys
import time

sys.path.insert(0, '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4/assets-src/blender/lib')
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

import sklib  # noqa: E402

D2R = math.pi / 180
T0 = time.time()
S = sklib.reset()
S.frame_start, S.frame_end = 1, 574
RNG = random.Random(707)


# ------------------------------------------------------------------------------------------------------------ helpers
def coll(name, parent=None):
    return sklib.collection(name, parent)


def box(name, c, size, mat, bev=0.006, seg=2, col=None, parent=None, rot=None):
    bm = bmesh.new()
    sklib._bm_box(bm, Vector(c) if parent is None and rot is None else Vector((0, 0, 0)), size)
    ob = sklib._mesh_obj(name, bm, col)
    if parent is not None or rot is not None:
        ob.location = c
        if rot is not None:
            ob.rotation_euler = rot
        if parent is not None:
            ob.parent = parent
    sklib.mat_to(ob, *(mat if isinstance(mat, (list, tuple)) else [mat]))
    if bev:
        sklib.bevel(ob, bev, seg)
    return ob


def bm_obj(name, bm, mats, col=None, bev=0.0, seg=2, parent=None, apply=False):
    ob = sklib._mesh_obj(name, bm, col, parent)
    sklib.mat_to(ob, *(mats if isinstance(mats, (list, tuple)) else [mats]))
    if bev:
        sklib.bevel(ob, bev, seg)
        if apply:
            sklib.apply_mods(ob)
    return ob


def cyl(bm, c, r, h, axis='Z', seg=16, mi=0):
    return sklib._bm_cyl(bm, Vector(c), r, h, axis, seg, mi)


def bx(bm, c, size, mi=0):
    return sklib._bm_box(bm, Vector(c), size, mi)


def look_euler(loc, aim):
    return (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


def key(ob, path, frames_vals, index=-1):
    """frames_vals = [(frame, value), ...] -> keys (Bezier, auto-clamped)."""
    for f, v in frames_vals:
        if index >= 0:
            getattr(ob, path)[index] = v
        else:
            setattr(ob, path, v)
        ob.keyframe_insert(path, index=index, frame=f)


def driver(sock_owner, path, expr, index=-1):
    fc = sock_owner.driver_add(path, index) if index >= 0 else sock_owner.driver_add(path)
    fc.driver.type = 'SCRIPTED'
    fc.driver.expression = expr        # simple expression with 'frame' -> no Python needed at render time
    return fc


# --------------------------------------------------------------------------------------------------------- materials
def frostify(m, amount=0.6, up_bias=0.6, scale=5.0, name=None):
    """Copy of a material with frost crystals mixed in (noise patches, stronger on upward faces and edges)."""
    nm = name or (m.name + '_frost%02d' % int(amount * 99))
    f = bpy.data.materials.get(nm)
    if f:
        return f
    f = m.copy()
    f.name = nm
    nt = f.node_tree
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    src = out.inputs['Surface'].links[0].from_socket
    n = sklib._n
    tc = n(nt, 'ShaderNodeTexCoord', 1400, -600)
    geo = n(nt, 'ShaderNodeNewGeometry', 1400, -800)
    sep = n(nt, 'ShaderNodeSeparateXYZ', 1600, -800)
    sklib._l(nt, geo.outputs['Normal'], sep.inputs[0])
    up = sklib._maprange(nt, sep.outputs[2], -0.3, 1.0, 1.0 - up_bias, 1.0, 1800, -800)
    nz = sklib._noise(nt, tc.outputs['Object'], scale * 5.0, 10.0, 0.7, 1600, -600)     # fine crystalline patches
    pm = sklib._maprange(nt, nz.outputs['Fac'], 0.68 - 0.2 * amount, 0.76 - 0.15 * amount, 0.0, 1.0, 1800, -600)
    fac = sklib._math(nt, 'MULTIPLY', pm, up, True, 2200, -700)
    fac = sklib._math(nt, 'MULTIPLY', fac, min(1.0, amount * 1.4), True, 2400, -700)
    fr = n(nt, 'ShaderNodeBsdfPrincipled', 2400, -300)
    fr.inputs['Base Color'].default_value = (0.86, 0.9, 0.93, 1)
    fr.inputs['Roughness'].default_value = 0.72
    fr.inputs['Subsurface Weight'].default_value = 0.15
    fn = sklib._noise(nt, tc.outputs['Object'], 140.0, 4.0, 0.6, 2000, -1200)
    bp = n(nt, 'ShaderNodeBump', 2200, -1200)
    bp.inputs['Strength'].default_value = 0.5
    bp.inputs['Distance'].default_value = 0.002
    sklib._l(nt, fn.outputs['Fac'], bp.inputs['Height'])
    sklib._l(nt, bp.outputs[0], fr.inputs['Normal'])
    mx = n(nt, 'ShaderNodeMixShader', 2700, 0)
    sklib._l(nt, fac, mx.inputs[0])
    sklib._l(nt, src, mx.inputs[1])
    sklib._l(nt, fr.outputs[0], mx.inputs[2])
    sklib._l(nt, mx.outputs[0], out.inputs['Surface'])
    out.location = (2950, 0)
    return f


def frost_decal(name='frost_decal'):
    """Floor-edge / housing frost: white crystalline, alpha by noise x 'gradient' (UV-free, uses object Z/Y)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = sklib._n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = sklib._n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    sklib._l(nt, b.outputs[0], out.inputs['Surface'])
    tc = sklib._n(nt, 'ShaderNodeTexCoord', -800, 0)
    nz = sklib._noise(nt, tc.outputs['Object'], 9.0, 10.0, 0.66, -600, 0)
    ga = sklib._n(nt, 'ShaderNodeAttribute', -600, -300, attribute_name='grad')
    a = sklib._maprange(nt, nz.outputs['Fac'], 0.38, 0.6, 0.0, 1.0, -400, 0)
    a = sklib._math(nt, 'MULTIPLY', a, ga.outputs['Fac'], True, -200, 0)
    a = sklib._math(nt, 'POWER', a, 0.7, True, 0, 0)
    sklib._l(nt, a, b.inputs['Alpha'])
    b.inputs['Base Color'].default_value = (0.88, 0.91, 0.94, 1)
    b.inputs['Roughness'].default_value = 0.6
    b.inputs['Subsurface Weight'].default_value = 0.2
    fn = sklib._noise(nt, tc.outputs['Object'], 160.0, 4.0, 0.6, -400, -400)
    bp = sklib._n(nt, 'ShaderNodeBump', 300, -400)
    bp.inputs['Strength'].default_value = 0.6
    bp.inputs['Distance'].default_value = 0.002
    sklib._l(nt, fn.outputs['Fac'], bp.inputs['Height'])
    sklib._l(nt, bp.outputs[0], b.inputs['Normal'])
    return m


def glass(name='glass_door'):
    return sklib.flat(name, (0.82, 0.88, 0.9), rough=0.03, var=0.02, scale=5,
                      **{'Alpha': 0.14, 'Coat Weight': 1.0, 'Coat Roughness': 0.02})


def pvc_strip():
    m = sklib.flat('pvc_strip', (0.80, 0.86, 0.87), rough=0.06, var=0.04, scale=12, bump=0.03,
                   **{'Alpha': 0.16, 'Coat Weight': 0.8, 'Coat Roughness': 0.03})
    m.use_transparent_shadow = True
    return m


def emissive(name, k=5000, strength=12.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = sklib._n(nt, 'ShaderNodeOutputMaterial', 400, 0)
    b = sklib._n(nt, 'ShaderNodeBsdfPrincipled', 100, 0)
    b.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1)
    b.inputs['Emission Color'].default_value = sklib.kelvin_rgb(k) + (1,)
    b.inputs['Emission Strength'].default_value = strength
    b.inputs['Roughness'].default_value = 0.4
    sklib._l(nt, b.outputs[0], out.inputs['Surface'])
    return m


def water_film(name='wet_film'):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = sklib._n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = sklib._n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    sklib._l(nt, b.outputs[0], out.inputs['Surface'])
    tc = sklib._n(nt, 'ShaderNodeTexCoord', -800, 0)
    nz = sklib._noise(nt, tc.outputs['Object'], 0.9, 6.0, 0.6, -600, 0)
    a = sklib._maprange(nt, nz.outputs['Fac'], 0.42, 0.56, 0.0, 0.85, -300, 0)
    sklib._l(nt, a, b.inputs['Alpha'])
    b.inputs['Base Color'].default_value = (0.18, 0.2, 0.2, 1)
    b.inputs['Roughness'].default_value = 0.02
    b.inputs['Coat Weight'].default_value = 1.0
    rn = sklib._noise(nt, tc.outputs['Object'], 30.0, 3.0, 0.5, -400, -300)
    bp = sklib._n(nt, 'ShaderNodeBump', 300, -300)
    bp.inputs['Strength'].default_value = 0.08
    sklib._l(nt, rn.outputs['Fac'], bp.inputs['Height'])
    sklib._l(nt, bp.outputs[0], b.inputs['Normal'])
    return m


def mist_mat(name, density=0.25, scale=1.2, drift=(0.012, 0.0, 0.004)):
    """Principled Volume, noise-shaped density, drifting with the frame (driver, no Python at render)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = sklib._n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    pv = sklib._n(nt, 'ShaderNodeVolumePrincipled', 600, 0)
    pv.inputs['Color'].default_value = (0.92, 0.95, 0.97, 1)
    pv.inputs['Anisotropy'].default_value = 0.3
    sklib._l(nt, pv.outputs[0], out.inputs['Volume'])
    tc = sklib._n(nt, 'ShaderNodeTexCoord', -1000, 0)
    mp = sklib._n(nt, 'ShaderNodeMapping', -800, 0)
    sklib._l(nt, tc.outputs['Object'], mp.inputs['Vector'])
    for i, v in enumerate(drift):
        if v:
            driver(mp.inputs['Location'], 'default_value', '-frame*%g' % v, i)
    nz = sklib._noise(nt, mp.outputs[0], scale, 4.0, 0.55, -550, 0, dims='3D')
    d = sklib._maprange(nt, nz.outputs['Fac'], 0.45, 0.75, 0.0, density, -300, 0)
    # fade to zero at the box faces (object space -1..1 generated coords)
    gs = sklib._n(nt, 'ShaderNodeSeparateXYZ', -800, -300)
    sklib._l(nt, tc.outputs['Generated'], gs.inputs[0])
    fade = None
    for i in range(3):
        e = sklib._math(nt, 'MINIMUM', gs.outputs[i], sklib._math(nt, 'SUBTRACT', 1.0, gs.outputs[i], x=-600, y=-300 - 80 * i),
                        x=-450, y=-300 - 80 * i)
        e = sklib._maprange(nt, e, 0.0, 0.3, 0.0, 1.0, -300, -300 - 80 * i)
        fade = e if fade is None else sklib._math(nt, 'MULTIPLY', fade, e, x=-150, y=-300 - 80 * i)
    sklib._l(nt, sklib._math(nt, 'MULTIPLY', d, fade, x=100, y=0), pv.inputs['Density'])
    return m


def mist_box(name, c, size, mat, col):
    bm = bmesh.new()
    bx(bm, (0, 0, 0), size)
    ob = sklib._mesh_obj(name, bm, col)
    ob.location = c
    ob.data.materials.append(mat)
    return ob


# shared materials
PUF = sklib.painted_metal((0.80, 0.81, 0.80), wear=0.08, streaks=0.0, contrast=0.25)
PUF_FROST = frostify(PUF, 0.35, 0.3, 3.0)
STAINLESS = sklib.stainless(0.08)
BRUSHED = sklib.pbr('stainless_brushed', 'blue_metal_plate', tint=(0.66, 0.67, 0.68), rough=(0.32, 0.55), metal=1.0, nor=0.3,
                    wear=0.08, wear_color=(0.4, 0.38, 0.35), var=0.04, scale=0.5, contrast=0.3)
STAIN_FROST = frostify(BRUSHED, 0.6, 0.4, 4.0)
RUBBER = sklib.plastic((0.025, 0.025, 0.025), 0.2, name='rubber_black')
FLOOR_COLD = sklib.epoxy_floor((0.58, 0.60, 0.60), wear=0.25)
FLOOR_PACK = sklib.epoxy_floor((0.50, 0.57, 0.54), wear=0.18)
LINE_YEL = sklib.epoxy_floor((0.78, 0.56, 0.05), wear=0.4)
KERB = sklib.pbr('kerb_concrete', 'concrete_floor_02', tint=(0.62, 0.62, 0.6), wear=0.3, ao_dist=0.2)
GALV = sklib.galvanised(0.15)
FROST = frost_decal()


# --------------------------------------------------------------------------------------------------------- building
def puf_wall(name, axis, fixed, a0, a1, z0, z1, side, col, mat=PUF, openings=(), pw=1.15, th=0.15):
    """Insulated sandwich-panel wall: vertical panels pw wide (bevelled -> V seams), thickness th.
    axis 'X' = wall runs along X at y=fixed (inner face), side = +1/-1 direction of the wall body from the inner face.
    openings = [(o0, o1, oz1)] along the run, from the floor up to oz1."""
    bm = bmesh.new()
    n = max(1, int(round((a1 - a0) / pw)))
    w = (a1 - a0) / n
    for i in range(n):
        p0, p1 = a0 + i * w, a0 + (i + 1) * w
        pieces = [(p0, p1, z0, z1)]
        for o0, o1, oz1 in openings:
            nxt = []
            for q0, q1, qz0, qz1 in pieces:
                if q1 <= o0 or q0 >= o1:
                    nxt.append((q0, q1, qz0, qz1))
                    continue
                if q0 < o0:
                    nxt.append((q0, o0, qz0, qz1))
                if q1 > o1:
                    nxt.append((o1, q1, qz0, qz1))
                nxt.append((max(q0, o0), min(q1, o1), max(qz0, oz1), qz1))
            pieces = nxt
        for q0, q1, qz0, qz1 in pieces:
            if q1 - q0 < 0.01 or qz1 - qz0 < 0.01:
                continue
            c = (q0 + q1) / 2
            d = fixed + side * th / 2
            if axis == 'X':
                bx(bm, (c, d, (qz0 + qz1) / 2), (q1 - q0 - 0.004, th, qz1 - qz0))
            else:
                bx(bm, (d, c, (qz0 + qz1) / 2), (th, q1 - q0 - 0.004, qz1 - qz0))
    ob = bm_obj(name, bm, mat, col, bev=0.008, seg=2)
    return ob


def kerb_frost(name, axis, fixed, a0, a1, side, col, frost=True):
    """150 mm concrete kerb at the wall foot + frost creeping onto the floor edge (cold rooms only)."""
    bm = bmesh.new()
    if axis == 'X':
        bx(bm, ((a0 + a1) / 2, fixed - side * 0.06, 0.075), (a1 - a0, 0.12, 0.15))
    else:
        bx(bm, (fixed - side * 0.06, (a0 + a1) / 2, 0.075), (0.12, a1 - a0, 0.15))
    bm_obj(name + '_kerb', bm, frostify(KERB, 0.5, 0.5, 4.0) if frost else KERB, col, bev=0.01)
    if not frost:
        return
    # frost decal strip on the floor: grid with 'grad' attribute 1 at the kerb -> 0 at 0.6 m
    bm = bmesh.new()
    nseg = max(2, int((a1 - a0) / 0.25))
    wdt = 0.7
    lay = bm.verts.layers.float.new('grad')
    rows = []
    for j in range(5):
        t = j / 4
        row = []
        for i in range(nseg + 1):
            a = a0 + (a1 - a0) * i / nseg
            d = fixed - side * (0.12 + t * wdt)
            co = (a, d, 0.003) if axis == 'X' else (d, a, 0.003)
            v = bm.verts.new(co)
            v[lay] = (1 - t) ** 1.5
            row.append(v)
        rows.append(row)
    for j in range(4):
        for i in range(nseg):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    me = bpy.data.meshes.new(name + '_frost')
    bm.to_mesh(me)
    bm.free()
    attr = me.attributes.get('grad')
    ob = sklib.new_obj(name + '_frost', me, col)
    ob.data.materials.append(FROST)
    # the bmesh float layer becomes a point attribute named 'grad' (read by the Attribute node)
    return ob, attr


def ceiling(name, x0, x1, y0, y1, z, col, mat=PUF):
    bm = bmesh.new()
    n = max(1, int((x1 - x0) / 1.15))
    w = (x1 - x0) / n
    for i in range(n):
        bx(bm, (x0 + (i + 0.5) * w, (y0 + y1) / 2, z + 0.075), (w - 0.004, y1 - y0, 0.15))
    return bm_obj(name, bm, mat, col, bev=0.008)


# ======================================================================================================== COLD STORE
C_COLD = coll('COLD_STORE')
XW_DOCK, XW_FAR = 0.0, -30.0           # inner faces x: dock wall inner = -0.15, far wall inner = -30.0
Y_L, Y_R = -1.8, 13.7
H_COLD = 10.0
box('cold_floor', ((XW_FAR - 0.15) / 2, (Y_L + Y_R) / 2, -0.1), (abs(XW_FAR) + 0.3, Y_R - Y_L + 0.3, 0.2),
    FLOOR_COLD, 0.0, col=C_COLD)
ceiling('cold_ceiling', XW_FAR - 0.15, 0.0, Y_L - 0.15, Y_R + 0.15, H_COLD, C_COLD)
DOOR_W, DOOR_H = 2.438, 2.896
puf_wall('cold_wall_dock', 'Y', -0.15, Y_L - 0.15, Y_R + 0.15, 0, H_COLD, +1, C_COLD,
         openings=[(-DOOR_W / 2, DOOR_W / 2, DOOR_H)])
puf_wall('cold_wall_far', 'Y', XW_FAR, Y_L - 0.15, Y_R + 0.15, 0, H_COLD, -1, C_COLD, openings=[(-1.0, 1.0, 2.45)])
puf_wall('cold_wall_left', 'X', Y_L, XW_FAR, -0.15, 0, H_COLD, -1, C_COLD)
puf_wall('cold_wall_right', 'X', Y_R, XW_FAR, -0.15, 0, H_COLD, +1, C_COLD)
kerb_frost('cold_left', 'X', Y_L, XW_FAR, -0.15, -1, C_COLD)
kerb_frost('cold_right', 'X', Y_R, XW_FAR, -0.15, +1, C_COLD)
kerb_frost('cold_far_a', 'Y', XW_FAR, Y_L, -1.0, -1, C_COLD)
kerb_frost('cold_far_b', 'Y', XW_FAR, 1.0, Y_R, -1, C_COLD)
kerb_frost('cold_dock_a', 'Y', -0.15, Y_L, -DOOR_W / 2, +1, C_COLD)
kerb_frost('cold_dock_b', 'Y', -0.15, DOOR_W / 2, Y_R, +1, C_COLD)
# aisle floor markings (painted lines, worn)
for y in (Y_L + 0.35, 1.45):
    box('aisle_line_%.1f' % y, (-15.0, y, 0.0015), (25.0, 0.09, 0.003), LINE_YEL, 0.0, col=C_COLD)

# ---- exterior dock side (only the door end is ever in frame, plus a little apron)
C_EXT = coll('DOCK_EXTERIOR')
box('dock_apron', (6.0, 0.0, -0.1), (12.0, 16.0, 0.2), sklib.concrete_quay(0.35), 0.0, col=C_EXT)


# ---- BRIDGE_DOOR: the white reefer door end (exact sklib container_40 reefer geometry) as the dispatch dock doors
def reefer_door_end():
    C = coll('BRIDGE_DOOR')
    src = sklib.container_40('reefer', 'white', 0.3, 'tmp_reefer', C)
    L = 12.192
    me = src.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    # islands
    seen, islands = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        seen.add(v.index)
        while stack:
            a = stack.pop()
            isl.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index)
                    stack.append(b)
        islands.append(isl)
    dx = L / 2 - 0.07
    part = {}
    for isl in islands:
        cx = sum(v.co.x for v in isl) / len(isl)
        cy = sum(v.co.y for v in isl) / len(isl)
        cz = sum(v.co.z for v in isl) / len(isl)
        if cx < L / 2 - 0.2:
            k = None
        elif abs(cy) < 1.0 and ((0.2 < cz < DOOR_H - 0.2 and cx > dx - 0.02) or cx >= dx + 0.034):
            k = 'leaf_p' if cy >= 0 else 'leaf_n'
        else:
            k = 'frame'
        for v in isl:
            part[v.index] = k
    objs = {}
    mats = [s.material for s in src.material_slots]
    for k in ('frame', 'leaf_p', 'leaf_n'):
        b2 = bm.copy()
        b2.verts.ensure_lookup_table()
        bmesh.ops.delete(b2, geom=[v for v in b2.verts if part.get(v.index) != k], context='VERTS')
        m2 = bpy.data.meshes.new('MESH_DOOR_' + k)
        b2.to_mesh(m2)
        b2.free()
        for mt in mats:
            m2.materials.append(mt)
        ob = sklib.new_obj('BRIDGE_DOOR_' + k, m2, C)
        objs[k] = ob
    bm.free()
    bpy.data.objects.remove(src)
    # place: container local x -> world x = x - L/2 + 0.16 (castings' outer face at x=+0.16)
    off = -L / 2 + 0.16
    objs['frame'].location = (off, 0, 0)
    hinges = {}
    for k, s in (('leaf_p', 1), ('leaf_n', -1)):
        hy = s * (DOOR_W / 2 - 0.15)
        hx = dx + 0.03
        h = sklib.new_obj('BRIDGE_DOOR_hinge_' + k, None, C, loc=(hx + off, hy, 0))
        ob = objs[k]
        ob.parent = h
        ob.location = (-hx, -hy, 0)
        hinges[k] = (h, s)
    return objs, hinges, off + dx + 0.015     # world x of the leaf outer face


DOOR_OBJS, DOOR_HINGES, X_LEAF = reefer_door_end()
for h, s in DOOR_HINGES.values():           # swing open f1-30 (outward, toward the camera side), settle by f60
    key(h, 'rotation_euler', [(1, 0.0), (6, s * 2 * D2R), (30, s * 104 * D2R), (60, s * 112 * D2R)], 2)
    sklib.ease_keys(h)
# door light rig at the bridge: sun + sky behind camera-left (az 135, elev 40) -> sklib.sky_world below

# ---- strip curtain (A-CURTAIN): rail + overlapping PVC strips that part as the camera pushes through (f40-62)
C_CUR = coll('A-CURTAIN')
XC = -0.45
box('curtain_rail', (XC, 0, 2.93), (0.08, DOOR_W + 0.1, 0.06), STAIN_FROST, 0.004, col=C_CUR)
PVC = pvc_strip()
nstr = 14
for i in range(nstr):
    y = -1.13 + i * (2.26 / (nstr - 1))
    bm = bmesh.new()
    # ribbed 200 x 2 mm strip, 2.88 m long, hanging from its top (origin at the rail)
    prof = [(-0.1, 0), (-0.098, 0.0012), (-0.07, 0.0018), (-0.068, 0), (0.068, 0), (0.07, 0.0018), (0.098, 0.0012), (0.1, 0)]
    a = [bm.verts.new((d - 0.001, u, 0)) for u, d in prof]
    b = [bm.verts.new((d - 0.001, u, -2.9)) for u, d in prof]
    for j in range(len(prof) - 1):
        bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1], cuts=12)
    st = sklib._mesh_obj('A-CURTAIN.strip_%02d' % i, bm, C_CUR)
    st.location = (XC + (0.012 if i % 2 else 0.0), y, 2.9)
    sklib.mat_to(st, PVC)
    so = st.modifiers.new('solid', 'SOLIDIFY')
    so.thickness = 0.002
    bd = st.modifiers.new('sag', 'SIMPLE_DEFORM')        # strips bow a little as they are pushed
    bd.deform_method, bd.deform_axis = 'BEND', 'Y'
    side = 1 if y >= 0 else -1
    push = max(0.0, 1.0 - abs(y) / 1.25)
    # rotation about X = swing aside (y), about Y = pushed in travel direction (-x)
    rx = [(1, 0), (40, 0), (47, -side * 46 * D2R * push), (54, -side * 40 * D2R * push), (64, side * 8 * D2R * push),
          (74, -side * 3 * D2R * push), (86, 0)]
    ry = [(1, 0), (40, 0), (47, -24 * D2R * push), (55, -16 * D2R * push), (66, 6 * D2R * push), (80, 0)]
    key(st, 'rotation_euler', rx, 0)
    key(st, 'rotation_euler', ry, 1)
    bd.angle = 0.0
    bd.keyframe_insert('angle', frame=40)
    bd.angle = 0.35 * push
    bd.keyframe_insert('angle', frame=50)
    bd.angle = 0.0
    bd.keyframe_insert('angle', frame=70)
    sklib.ease_keys(st)

# ---- cold mist at the door (falls out low), plus a faint layer along the dock floor
mist_box('cold_mist_door', (0.4, 0, 0.55), (3.6, 2.8, 1.1), mist_mat('mist_door', 0.12, 1.4, (0.02, 0.0, 0.0)), C_CUR)


# ---- high-bay racking: 10 bays x 5 levels per row, 5 rows (instanced), frosted
BAY, NB = 2.4, 10
X_RACK0 = -3.5                         # first upright (dock side); bays run toward -X
LV = [0.0, 1.65, 3.30, 4.95, 6.60]     # level beam centres (0 = floor)
UPR_H = 8.0
RACK_DEPTH = 1.1


def rack_row():
    c = coll('A-RACK-ROW', False)
    blue = frostify(sklib.painted_metal((0.04, 0.13, 0.36), 0.25, 0.1, 0.5), 0.55, 0.6, 3.5)
    orange = frostify(sklib.painted_metal((0.78, 0.26, 0.03), 0.25, 0.1, 0.5), 0.55, 0.7, 3.5)
    yel = sklib.painted_metal((0.80, 0.60, 0.04), 0.5, 0.0, 0.5)
    bm = bmesh.new()
    L = NB * BAY
    for i in range(NB + 1):
        x = L / 2 - i * BAY
        for y in (-RACK_DEPTH / 2, RACK_DEPTH / 2):
            bx(bm, (x, y, UPR_H / 2), (0.09, 0.07, UPR_H), 0)
            bx(bm, (x, y, 0.005), (0.16, 0.14, 0.01), 0)          # base plate
        z = 0.3
        k = 0
        while z < UPR_H - 0.3:                                   # frame bracing: horizontals + diagonals
            bx(bm, (x, 0, z), (0.035, RACK_DEPTH - 0.07, 0.035), 0)
            z2 = min(z + 1.2, UPR_H - 0.3)
            dl = math.hypot(RACK_DEPTH - 0.07, z2 - z)
            ang = math.atan2(z2 - z, (RACK_DEPTH - 0.07) * (1 if k % 2 else -1))
            vs = bx(bm, (0, 0, 0), (0.03, dl, 0.03), 0)
            bmesh.ops.rotate(bm, verts=vs, cent=Vector((0, 0, 0)), matrix=Matrix.Rotation(ang - math.pi / 2 * 0 + 0, 3, 'X'))
            bmesh.ops.translate(bm, verts=vs, vec=Vector((x, 0, (z + z2) / 2)))
            z, k = z2, k + 1
        bx(bm, (x, 0, UPR_H - 0.3), (0.035, RACK_DEPTH - 0.07, 0.035), 0)
    for i in range(NB):
        xc = L / 2 - (i + 0.5) * BAY
        for z in LV[1:]:
            for y in (-RACK_DEPTH / 2, RACK_DEPTH / 2):
                bx(bm, (xc, y, z), (BAY - 0.09, 0.05, 0.12), 1)
            for sx in (-0.55, 0.55):                              # pallet support bars
                bx(bm, (xc + sx, 0, z + 0.075), (0.04, RACK_DEPTH - 0.02, 0.03), 1)
    for i in range(NB + 1):                                       # column protectors (aisle side)
        bx(bm, (L / 2 - i * BAY, -RACK_DEPTH / 2 - 0.09, 0.2), (0.2, 0.06, 0.4), 2)
    ob = sklib._mesh_obj('A-RACK-ROW', bm, c)
    sklib.mat_to(ob, blue, orange, yel)
    sklib.bevel(ob, 0.004, 1, 40)
    sklib.apply_mods(ob)
    return c


def lite_pallet():
    """Far-row LOD of A-CARTON-PALLET: same pallet + 5 layers of bevelled carton boxes + film (one mesh)."""
    c = bpy.data.collections.get('A-CARTON-PALLET-LITE')
    if c:
        return c
    c = coll('A-CARTON-PALLET-LITE', False)
    pal = sklib.pallet_mesh('A-CARTON-PALLET-LITE.pallet')
    c.objects.link(pal)
    kraft = sklib.cardboard_kraft()
    white = sklib.pbr('carton_white_print', 'acg:Cardboard004', tint=(0.86, 0.85, 0.82), wear=0.12,
                      wear_color=(0.45, 0.4, 0.33), rough=(0.6, 0.85), ao_dist=0.04, nor=0.35, var=0.03)
    bm = bmesh.new()
    z0 = 0.144
    for k in range(5):
        for i in range(3):
            for j in range(2):
                bx(bm, (-0.35 + i * 0.35, -0.25 + j * 0.5, z0 + k * 0.258 + 0.1285), (0.348, 0.498, 0.256), 0)
    ob = sklib._mesh_obj('A-CARTON-PALLET-LITE.cartons', bm, c)
    sklib.mat_to(ob, kraft)
    sklib.bevel(ob, 0.005, 1, 40)
    sklib.apply_mods(ob)
    bm = bmesh.new()
    for k in range(5):        # white print panels on the outward faces
        zc = z0 + k * 0.258 + 0.14
        for i in range(3):
            for s in (-1, 1):
                sklib._quad_on_face(bm, (-0.35 + i * 0.35, s * 0.5015, zc), 0.30, 0.11, 180 if s > 0 else 0)
    pn = sklib._mesh_obj('A-CARTON-PALLET-LITE.print', bm, c)
    sklib.mat_to(pn, white)
    top = z0 + 5 * 0.258
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, (z0 + 0.05 + top - 0.1) / 2)) @
                          Matrix.Diagonal((1.065, 1.015, top - 0.1 - z0 - 0.05, 1)))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.9], context='FACES_ONLY')
    wr = sklib._mesh_obj('A-CARTON-PALLET-LITE.wrap', bm, c)
    sklib.mat_to(wr, bpy.data.materials.get('stretch_film') or sklib.flat(
        'stretch_film', (0.9, 0.92, 0.93), rough=0.06, var=0.03, scale=8, bump=0.3, **{'Alpha': 0.16, 'Coat Weight': 1.0}))
    return c


RACK = rack_row()
PAL5 = sklib.carton_pallet('A-CARTON-PALLET5', layers=5)
PAL_LITE = lite_pallet()
for o in PAL5.objects:            # frost on the stored pallets' wrap + cartons is a light white bloom: frost the wrap
    if o.name.endswith('.wrap'):
        sklib.mat_to(o, frostify(o.material_slots[0].material, 0.25, 0.8, 6.0, 'stretch_film_frost'), uv=False)
C_RACKS = coll('A-PLANT-COLDSTORE')
ROWS = [(2.15, 0), (3.45, math.pi), (7.55, 0), (8.85, math.pi), (12.95, 0)]
X_ROWC = X_RACK0 - NB * BAY / 2
for r, (y, rz) in enumerate(ROWS):
    sklib.instance(RACK, (X_ROWC, y, 0), rz, 'A-RACK-ROW.%d' % r, C_RACKS)
TRUCK_SLOT = (4, 1, 2)        # bay 4, slot 1 (x=-14.75? see below), level 2 in row 0
npal = {'full': 0, 'lite': 0}
for r, (y, rz) in enumerate(ROWS):
    for i in range(NB):
        for s in range(2):
            x = X_RACK0 - i * BAY - (0.65 if s == 0 else 1.75)
            for lv, z in enumerate(LV):
                if r == 0 and (i, s) == TRUCK_SLOT[:2] and lv in (0, TRUCK_SLOT[2]):
                    continue
                if RNG.random() > 0.9:
                    continue
                zb = 0.0 if lv == 0 else z + 0.06
                src = PAL5 if r < 2 else PAL_LITE
                npal['full' if r < 2 else 'lite'] += 1
                sklib.instance(src, (x + RNG.uniform(-0.02, 0.02), y + RNG.uniform(-0.03, 0.03), zb),
                               math.pi / 2 + rz + RNG.uniform(-0.012, 0.012), 'PAL.%d.%d.%d.%d' % (r, i, s, lv), C_RACKS)
X_TRUCK = X_RACK0 - TRUCK_SLOT[0] * BAY - 1.75
print('pallets', npal, 'truck x', X_TRUCK)


# ---- evaporator unit coolers (far wall + left wall, high), frosted coil, fan guards
def evaporator(name, loc, rz, col):
    root = sklib.new_obj(name, None, col, loc=loc, rot=(0, 0, rz))
    housing = sklib.painted_metal((0.82, 0.83, 0.82), 0.12, 0.05, 0.3)
    bm = bmesh.new()
    bx(bm, (0, 0, 0), (0.9, 3.0, 0.95), 0)                 # casing, fans blow toward +x local
    bx(bm, (0.47, 0, 0), (0.04, 2.9, 0.85), 1)              # fan plate (dark)
    for k in (-1, 0, 1):
        cyl(bm, (0.49, k * 0.95, 0), 0.36, 0.02, 'X', 32, 2)   # guard rings
        for rr in (0.12, 0.22, 0.31):
            cyl(bm, (0.505, k * 0.95, 0), rr, 0.008, 'X', 28, 2)
        bx(bm, (0.51, k * 0.95, 0), (0.008, 0.7, 0.012), 2)
        bx(bm, (0.51, k * 0.95, 0), (0.008, 0.012, 0.7), 2)
    bx(bm, (-0.47, 0, 0), (0.04, 2.9, 0.85), 3)             # coil face (frosted fins) at the back
    for i in range(4):                                       # drain tray + hangers
        bx(bm, ((-0.3 + 0.2 * i), 0, 0.85), (0.04, 0.04, 0.8), 0)
    bx(bm, (0, 0, -0.52), (0.95, 3.05, 0.08), 0)
    ob = bm_obj(name + '.body', bm, [frostify(housing, 0.35, 0.8, 4.0), sklib.plastic((0.05, 0.05, 0.05), 0.2),
                                     frostify(GALV, 0.5, 0.3, 6.0), frostify(GALV, 1.0, 0.0, 9.0, 'coil_frost')],
                col, bev=0.006, parent=root)
    return root


C_EVAP = coll('EVAPORATORS', C_COLD)
for i, y in enumerate((4.5, 9.0)):
    evaporator('EVAP.far.%d' % i, (XW_FAR + 0.6, y, 9.0), 0.0, C_EVAP)
for i, x in enumerate((-9.0, -21.0)):
    evaporator('EVAP.left.%d' % i, (x, Y_L + 0.6, 9.2), math.pi / 2, C_EVAP)

# ---- cold store LED high-bay fixtures (emissive bodies) + area lights
LED = emissive('led_5000', 5000, 14.0)
C_LT = coll('LIGHTS')


def area(name, loc, size, power, k=5000, rot=(0, 0, 0), shadow=True, spread=180):
    # ponytail: only key lights cast shadows (EEVEE shadow buffer overflowed with ~40 shadowed area lights)
    L = bpy.data.lights.new(name, 'AREA')
    L.shape, L.size, L.size_y = 'RECTANGLE', size[0], size[1]
    L.energy, L.color = power, sklib.kelvin_rgb(k)
    L.use_shadow = shadow
    L.spread = spread * D2R
    return sklib.new_obj(name, L, C_LT, loc=loc, rot=rot)


for x in (-3.0, -8.5, -14.0, -19.5, -25.0):
    for y in (0.0, 5.5, 10.9):
        bm = bmesh.new()
        bx(bm, (0, 0, 0.04), (0.3, 3.0, 0.08), 0)
        bx(bm, (0, 0, -0.005), (0.26, 2.94, 0.01), 1)
        bm_obj('led_cold_%g_%g' % (x, y), bm, [STAINLESS, LED], C_LT, bev=0.004).location = (x, y, H_COLD - 0.2)
# ponytail: few big area lights (39 small ones cost ~3x per frame); emissive fixtures above stay as the visible LEDs
area('L_cold_main_a', (-8.0, 0.0, H_COLD - 0.3), (11.0, 1.2), 2250, shadow=True)
area('L_cold_main_b', (-19.5, 0.0, H_COLD - 0.3), (11.0, 1.2), 2250, shadow=True)
area('L_cold_aisle2', (-14.0, 5.5, H_COLD - 0.3), (22.0, 1.2), 4500, shadow=False)
area('L_cold_aisle3', (-14.0, 10.9, H_COLD - 0.3), (22.0, 1.2), 4500, shadow=False)


# ---- electric reach truck (A-FORKLIFT) with operator P-COLD-1, the hero pallet + hero carton on top
def reach_truck():
    C = coll('A-FORKLIFT')
    paint = sklib.painted_metal((0.74, 0.50, 0.05), 0.3, 0.1, 0.5)
    dark = sklib.painted_metal((0.07, 0.075, 0.08), 0.3, 0.0, 0.5)
    steel = sklib.galvanised(0.3)
    root = sklib.new_obj('A-FORKLIFT', None, C)
    # chassis (local +X = forks): battery/drive unit, operator platform, side panel, dashboard
    bm = bmesh.new()
    bx(bm, (-0.72, 0, 0.62), (0.56, 1.22, 1.04), 0)             # battery hood
    bx(bm, (-0.22, 0, 0.16), (0.48, 1.22, 0.22), 0)             # platform base
    bx(bm, (-0.22, -0.57, 0.62), (0.48, 0.08, 0.92), 0)         # side panel
    bx(bm, (-0.05, 0.47, 1.1), (0.2, 0.22, 0.3), 1)             # dashboard / joystick pod
    bx(bm, (0.05, 0, 0.45), (0.12, 1.22, 0.7), 0)               # mast mount face
    bx(bm, (-1.0, 0, 0.18), (0.04, 1.26, 0.3), 1)               # rear bumper
    ch = bm_obj('A-FORKLIFT.chassis', bm, [paint, dark], C, bev=0.03, seg=3, parent=root)
    bm = bmesh.new()
    bx(bm, (-0.22, 0, 0.275), (0.46, 1.1, 0.012), 0)            # rubber floor mat
    bx(bm, (-0.05, 0.44, 1.3), (0.04, 0.04, 0.12), 0)           # joystick
    bm_obj('A-FORKLIFT.mat', bm, RUBBER, C, bev=0.003, parent=root)
    # overhead guard: 4 posts + roof grid
    bm = bmesh.new()
    for x in (-0.96, 0.06):
        for y in (-0.57, 0.57):
            bx(bm, (x, y, 1.62), (0.06, 0.06, 1.2 if x < 0 else 2.0), 0)
    bx(bm, (-0.45, 0, 2.24), (1.12, 1.2, 0.05), 0)
    bm_obj('A-FORKLIFT.guard', bm, dark, C, bev=0.01, parent=root)
    bm = bmesh.new()
    for i in range(6):
        bx(bm, (-0.9 + i * 0.18, 0, 2.275), (0.03, 1.12, 0.02), 0)
    bm_obj('A-FORKLIFT.guardbars', bm, dark, C, bev=0.004, parent=root)
    # base legs + wheels
    bm = bmesh.new()
    for y in (-0.46, 0.46):
        bx(bm, (0.75, y, 0.13), (1.3, 0.14, 0.2), 0)
    bm_obj('A-FORKLIFT.legs', bm, paint, C, bev=0.015, parent=root)
    bm = bmesh.new()
    for y in (-0.46, 0.46):
        cyl(bm, (1.25, y, 0.09), 0.09, 0.1, 'Y', 20)
    cyl(bm, (-0.62, 0.25, 0.17), 0.17, 0.16, 'Y', 24)
    cyl(bm, (-0.62, -0.42, 0.12), 0.12, 0.1, 'Y', 20)
    bm_obj('A-FORKLIFT.wheels', bm, RUBBER, C, bev=0.01, parent=root)
    # reach carriage (moves along legs), outer mast, inner mast (telescopes), fork carriage
    reach = sklib.new_obj('A-FORKLIFT.reach', None, C, root, (0.0, 0, 0))
    bm = bmesh.new()
    for y in (-0.36, 0.36):
        bx(bm, (0.3, y, 1.65), (0.1, 0.12, 3.1), 0)
    bx(bm, (0.3, 0, 3.15), (0.1, 0.84, 0.1), 0)
    bx(bm, (0.3, 0, 0.18), (0.18, 0.84, 0.16), 0)
    cyl(bm, (0.26, 0, 1.2), 0.05, 2.0, 'Z', 16)
    bm_obj('A-FORKLIFT.mast_outer', bm, steel, C, bev=0.008, parent=reach)
    inner = sklib.new_obj('A-FORKLIFT.mast_inner', None, C, reach)
    bm = bmesh.new()
    for y in (-0.27, 0.27):
        bx(bm, (0.36, y, 1.7), (0.08, 0.1, 3.0), 0)
    bx(bm, (0.36, 0, 3.15), (0.08, 0.64, 0.08), 0)
    for y in (-0.15, 0.15):                                       # lift chains
        bx(bm, (0.42, y, 1.8), (0.015, 0.03, 2.6), 1)
    bm_obj('A-FORKLIFT.mast_inner_mesh', bm, [steel, dark], C, bev=0.006, parent=inner)
    carr = sklib.new_obj('A-FORKLIFT.carriage', None, C, reach)
    bm = bmesh.new()
    bx(bm, (0.45, 0, 0.3), (0.06, 1.0, 0.5), 0)                   # fork plate
    for i in range(7):                                            # load backrest grid
        bx(bm, (0.45, -0.45 + i * 0.15, 0.95), (0.03, 0.03, 0.8), 0)
    bx(bm, (0.45, 0, 1.35), (0.04, 1.0, 0.04), 0)
    for y in (-0.22, 0.22):                                       # forks
        bx(bm, (0.5, y, 0.32), (0.05, 0.12, 0.56), 1)
        bx(bm, (1.08, y, 0.055), (1.18, 0.12, 0.05), 1)
    bm_obj('A-FORKLIFT.forks', bm, [dark, steel], C, bev=0.006, parent=carr)
    # the hero pallet on the forks (pallet bottom 3 cm under the tines' underside) + hero carton on top
    pal = sklib.instance(sklib.carton_pallet('A-CARTON-PALLET4', layers=4), (1.08, 0, 0.0), 0.0, 'A-CARTON-PALLET.hero', C)
    pal.parent = carr
    hero = sklib.hero_carton(0.0, 'A-HERO-CARTON.cold', coll=C, interior=False,
                             loc=(1.08, 0.02, 0.144 + 4 * 0.258 + 0.002), rot_z=0.04)
    hero.parent = carr
    return root, reach, inner, carr


TRUCK, T_REACH, T_INNER, T_CARR = reach_truck()
_film = bpy.data.materials.get('stretch_film')
if _film:                      # ponytail: film shadows opaque-free (transparent shadows on ~450 wraps were costly)
    _film.use_transparent_shadow = False
    for o in list(PAL5.objects) + list(PAL_LITE.objects) + list(bpy.data.collections['A-CARTON-PALLET4'].objects):
        if o.name.endswith('.wrap'):
            o.visible_shadow = False
TRUCK.rotation_euler = (0, 0, math.pi / 2)             # forks -> +Y (toward rack row 0)
Y_RACK_FRONT = ROWS[0][0] - RACK_DEPTH / 2
pal_c_in = ROWS[0][0]                                  # pallet centre y when in the rack
# truck origin y so that (reach 0.55) the pallet sits in the slot; later it reverses 0.7 m into the aisle
y_in = pal_c_in - 1.08 - 0.55
key(TRUCK, 'location', [(1, (X_TRUCK, y_in, 0)), (78, (X_TRUCK, y_in, 0)), (104, (X_TRUCK, y_in - 0.75, 0)),
                         (192, (X_TRUCK, y_in - 0.75, 0))])
key(T_REACH, 'location', [(1, (0.55, 0, 0)), (66, (0.55, 0, 0)), (84, (0.0, 0, 0))])
zc_rack = LV[2] + 0.06                                # carriage height with the pallet resting on the beams
key(T_CARR, 'location', [(1, (0, 0, zc_rack)), (60, (0, 0, zc_rack)), (68, (0, 0, zc_rack + 0.06)),
                         (98, (0, 0, zc_rack + 0.06)), (150, (0, 0, 0.12)), (192, (0, 0, 0.12))])
key(T_INNER, 'location', [(1, (0, 0, zc_rack - 1.2)), (60, (0, 0, zc_rack - 1.2)), (68, (0, 0, zc_rack - 1.14)),
                          (98, (0, 0, zc_rack - 1.14)), (128, (0, 0, 0.6)), (150, (0, 0, 0.0)), (192, (0, 0, 0.0))])
sklib.ease_keys(TRUCK, T_REACH, T_CARR, T_INNER)

import people  # noqa: E402  (enables MPFB)

C_PPL = coll('PEOPLE')


def person(name, sex, age, outfit, pose, loc, rz, seed, skin=0.6, body=None, cycle='work', phase=0.0, f0=1, f1=574):
    for m in bpy.data.materials:      # MPFB purges orphans: keep not-yet-assigned scene materials alive
        m.use_fake_user = True
    p = people.make_person(name, sex=sex, age=age, outfit=outfit, pose=pose, location=loc, rotation_z=rz, seed=seed,
                           skin_tone=skin, body=body)
    for o in [p] + list(p.children_recursive):
        for c in o.users_collection:
            c.objects.unlink(o)
        C_PPL.objects.link(o)
    if cycle:
        people.animate_cycle(p, cycle, f0, f1, phase=phase)
    return p


bpy.context.view_layer.update()
OPER = person('P-COLD-1', 'male', 0.35, 'thermal_suit', 'work_table', (0, 0, 0), 0.0, 53, 0.7, cycle='work', f1=192)
gz = OPER.location.z
OPER.parent = TRUCK
OPER.matrix_parent_inverse = Matrix()
OPER.location = (-0.24, -0.12, 0.282 + gz)
OPER.rotation_euler = (0, 0, math.pi)                   # faces local +Y (sideways, toward the dashboard)

# ======================================================================================================= PACKING HALL
C_PACK = coll('PACKING_HALL')
PX0, PX1, PY0, PY1, PH = -56.0, -30.15, -4.0, 8.0, 5.0
box('pack_floor', ((PX0 + PX1) / 2, (PY0 + PY1) / 2, -0.1), (PX1 - PX0, PY1 - PY0, 0.2), FLOOR_PACK, 0.0, col=C_PACK)
ceiling('pack_ceiling', PX0, PX1, PY0 - 0.15, PY1 + 0.15, PH, C_PACK)
puf_wall('pack_wall_far', 'Y', PX0, PY0 - 0.15, PY1 + 0.15, 0, PH, -1, C_PACK)
puf_wall('pack_wall_left', 'X', PY0, PX0, PX1, 0, PH, -1, C_PACK)
puf_wall('pack_wall_right', 'X', PY1, PX0, PX1, 0, PH, +1, C_PACK)
for nm, ax, fx, a0, a1, sd in (('pack_l', 'X', PY0, PX0, PX1, -1), ('pack_r', 'X', PY1, PX0, PX1, +1),
                               ('pack_f', 'Y', PX0, PY0, PY1, -1)):
    kerb_frost(nm, ax, fx, a0, a1, sd, C_PACK, frost=False)
kerb_frost('pack_c1', 'Y', PX1, PY0, -1.0, +1, C_PACK, frost=False)
kerb_frost('pack_c2', 'Y', PX1, 1.0, PY1, +1, C_PACK, frost=False)
# trench drains (stainless gratings) along the line + near the IQF
GRATE = sklib.stainless(0.25)
for x0, x1, y in ((-49.0, -32.0, -0.55), (-55.0, -49.8, 0.0)):
    bm = bmesh.new()
    bx(bm, ((x0 + x1) / 2, y, -0.01), (x1 - x0, 0.22, 0.02), 1)
    n = int((x1 - x0) / 0.03)
    for i in range(n):
        bx(bm, (x0 + 0.015 + i * 0.03, y, 0.0005), (0.008, 0.2, 0.004), 0)
    bx(bm, ((x0 + x1) / 2, y - 0.105, 0.0005), (x1 - x0, 0.01, 0.004), 0)
    bx(bm, ((x0 + x1) / 2, y + 0.105, 0.0005), (x1 - x0, 0.01, 0.004), 0)
    bm_obj('drain_%g' % x0, bm, [GRATE, RUBBER], C_PACK)
# wet floor near the IQF only (packing stays dry)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=8, y_segments=8, size=1.0)
wet = bm_obj('wet_floor_iqf', bm, water_film(), C_PACK)
wet.location, wet.scale = (-47.6, 2.2, 0.002), (3.2, 3.6, 1)

# ceiling services: round ducts, hangers, cable tray, LED panels
for y in (-1.6, 5.2):
    bm = bmesh.new()
    cyl(bm, (-43.0, y, 4.35), 0.28, 25.6, 'X', 28)
    for x in range(-55, -31, 3):
        cyl(bm, (x + 0.5, y, 4.35), 0.295, 0.06, 'X', 28)        # duct joints
        bx(bm, (x + 0.5, y, 4.75), (0.02, 0.02, 0.5), 0)
    for x in range(-54, -31, 4):                                  # diffusers
        cyl(bm, (x, y, 4.0), 0.12, 0.16, 'Z', 20)
    bm_obj('duct_%g' % y, bm, GALV, C_PACK, bev=0.004)
bm = bmesh.new()
bx(bm, (-43.0, 2.0, 4.6), (25.0, 0.3, 0.02), 0)
for s in (-1, 1):
    bx(bm, (-43.0, 2.0 + s * 0.15, 4.64), (25.0, 0.01, 0.08), 0)
for x in range(-55, -31, 2):
    bx(bm, (x, 2.0, 4.8), (0.02, 0.02, 0.4), 0)
bm_obj('cable_tray', bm, GALV, C_PACK, bev=0.002)
for x in (-32.6, -36.8, -41.0, -45.2, -49.4, -53.6):
    for y in (-2.4, 1.2, 4.8):
        bm = bmesh.new()
        bx(bm, (0, 0, 0.02), (1.24, 0.64, 0.04), 0)
        bx(bm, (0, 0, -0.002), (1.18, 0.58, 0.004), 1)
        bm_obj('led_pack_%g_%g' % (x, y), bm, [sklib.aluminium(0.05), LED], C_LT, bev=0.004).location = (x, y, PH - 0.04)

area('L_pack_line_a', (-36.8, 1.2, PH - 0.1), (8.0, 1.4), 1560, shadow=True)
area('L_pack_line_b', (-45.2, 1.2, PH - 0.1), (8.0, 1.4), 1560, shadow=True)
area('L_pack_left', (-43.0, -2.4, PH - 0.1), (21.0, 1.0), 1560, shadow=False)
area('L_pack_right', (-43.0, 4.8, PH - 0.1), (21.0, 1.0), 1560, shadow=False)

# ---- glazed sliding door (cold store -> packing hall), opens f196-220
C_GD = coll('GLAZED_DOOR')
GL = glass()
bm = bmesh.new()
bx(bm, (-30.2, 0, 2.5), (0.12, 2.3, 0.12), 0)                       # header (operator box)
bx(bm, (-30.32, 0, 2.62), (0.22, 4.3, 0.24), 0)
for y in (-1.06, 1.06):
    bx(bm, (-30.08, y, 1.225), (0.2, 0.08, 2.45), 0)
bm_obj('glazed_door_frame', bm, STAINLESS, C_GD, bev=0.006)
for s in (-1, 1):
    leaf = sklib.new_obj('glazed_door_leaf_%d' % s, None, C_GD, loc=(-30.28, s * 0.5, 0))
    bm = bmesh.new()
    for c, sz in (((0, 0, 1.2), (0.05, 1.0, 0.07)), ((0, 0, 0.05), (0.05, 1.0, 0.1)), ((0, 0, 2.38), (0.05, 1.0, 0.07)),
                  ((0, -0.47, 1.2), (0.05, 0.06, 2.4)), ((0, 0.47, 1.2), (0.05, 0.06, 2.4))):
        bx(bm, c, sz, 0)
    bx(bm, (0, -s * 0.38, 1.05), (0.09, 0.03, 0.5), 0)               # pull handle
    bm_obj('glazed_door_leaf_frame_%d' % s, bm, STAINLESS, C_GD, bev=0.005, parent=leaf)
    bm = bmesh.new()
    bx(bm, (0, 0, 0.665), (0.012, 0.88, 1.03), 0)
    bx(bm, (0, 0, 1.79), (0.012, 0.88, 1.12), 0)
    bm_obj('glazed_door_glass_%d' % s, bm, GL, C_GD, parent=leaf)
    key(leaf, 'location', [(1, (-30.28, s * 0.5, 0)), (196, (-30.28, s * 0.5, 0)), (220, (-30.28, s * 1.45, 0)),
                           (262, (-30.28, s * 1.45, 0)), (300, (-30.28, s * 0.5, 0))])
    sklib.ease_keys(leaf)


# ---- packing line equipment
def table(name, c, size, col, top_z=0.9, legs=True):
    x, y = c
    w, d = size
    bm = bmesh.new()
    bx(bm, (x, y, top_z - 0.02), (w, d, 0.04), 0)
    bx(bm, (x, y, top_z - 0.06), (w - 0.06, d - 0.06, 0.04), 0)
    bx(bm, (x, y, 0.2), (w - 0.12, d - 0.12, 0.02), 0)                 # under shelf
    if legs:
        for sx in (-1, 1):
            for sy in (-1, 1):
                cyl(bm, (x + sx * (w / 2 - 0.06), y + sy * (d / 2 - 0.06), (top_z - 0.06) / 2), 0.022, top_z - 0.06, 'Z', 12)
                cyl(bm, (x + sx * (w / 2 - 0.06), y + sy * (d / 2 - 0.06), 0.02), 0.03, 0.04, 'Z', 12)
    return bm_obj(name, bm, STAINLESS, col, bev=0.006)


C_LINE = coll('A-PLANT-PACK')
CC = sklib.carton_closed()


def carton_at(name, loc, rz=0.0, col=C_LINE):
    return sklib.instance(CC, loc, rz, name, col)


# pallet being built (3 full layers + 2 cartons of the 4th) + two finished wrapped pallets + pallet jack
pb = sklib.pallet_mesh('A-PALLET.build')
C_LINE.objects.link(pb)
pb.location = (-33.4, 1.6, 0)
pb.rotation_euler.z = math.pi / 2
for k in range(4):
    for i in range(3):
        for j in range(2):
            if k == 3 and (i, j) not in ((0, 0), (0, 1)):
                continue
            carton_at('C.build.%d%d%d' % (k, i, j), (-33.4 - 0.25 + j * 0.5, 1.6 - 0.35 + i * 0.35,
                                                       0.144 + k * 0.258), 0.0)
sklib.instance(PAL5, (-32.2, 4.6, 0), 0.03, 'A-CARTON-PALLET.done1', C_LINE)
sklib.instance(PAL5, (-33.6, 4.6, 0), -0.02, 'A-CARTON-PALLET.done2', C_LINE)


def pallet_jack(name, loc, rz, col):
    root = sklib.new_obj(name, None, col, loc=loc, rot=(0, 0, rz))
    red = sklib.painted_metal((0.55, 0.06, 0.04), 0.35, 0.1, 0.5)
    bm = bmesh.new()
    for y in (-0.27, 0.27):
        bx(bm, (0.6, y, 0.05), (1.15, 0.16, 0.06), 0)
    bx(bm, (-0.05, 0, 0.2), (0.25, 0.7, 0.35), 0)
    cyl(bm, (-0.15, 0, 0.55), 0.03, 0.9, 'Z', 12)
    bx(bm, (-0.42, 0, 1.12), (0.04, 0.3, 0.04), 0)
    ob = bm_obj(name + '.body', bm, red, col, bev=0.01, parent=root)
    ob.rotation_euler = (0, 0, 0)
    bm = bmesh.new()
    cyl(bm, (-0.12, 0, 0.09), 0.09, 0.08, 'Y', 18)
    for y in (-0.27, 0.27):
        cyl(bm, (1.1, y, 0.04), 0.04, 0.08, 'Y', 14)
    bm_obj(name + '.wheels', bm, RUBBER, col, bev=0.004, parent=root)
    return root


pallet_jack('A-PALLETJACK', (-34.6, 4.0, 0), 0.4, C_LINE)

# roller conveyor (strapper -> pallet build)
bm = bmesh.new()
for y in (-0.33, 0.33):
    bx(bm, (-36.9, 1.2 + y, 0.74), (4.6, 0.05, 0.1), 0)
for i in range(46):
    cyl(bm, (-39.15 + i * 0.1, 1.2, 0.76), 0.024, 0.62, 'Y', 12, 1)
for x in (-39.0, -37.2, -35.4):
    for y in (-0.3, 0.3):
        bx(bm, (x, 1.2 + y, 0.36), (0.04, 0.04, 0.72), 0)
bm_obj('roller_conveyor', bm, [STAINLESS, sklib.aluminium(0.1)], C_LINE, bev=0.004)
carton_at('C.conv.1', (-35.7, 1.2, 0.785), math.pi / 2 + 0.02)
carton_at('C.conv.2', (-36.4, 1.2, 0.785), math.pi / 2 - 0.03)

# automatic arch strapping machine with a carton in the arch
bm = bmesh.new()
bx(bm, (-37.6, 1.2, 0.38), (0.95, 0.85, 0.72), 0)                  # cabinet
bx(bm, (-37.6, 1.2, 0.76), (0.95, 0.85, 0.04), 1)                  # table top
for y in (-0.48, 0.48):
    bx(bm, (-37.6, 1.2 + y, 1.25), (0.16, 0.1, 1.0), 0)            # arch legs
bx(bm, (-37.6, 1.2, 1.78), (0.16, 1.06, 0.1), 0)                   # arch top
bx(bm, (-37.6, 1.2 - 0.43, 0.45), (0.5, 0.012, 0.4), 2)            # door panel seam (dark)
bm_obj('A-STRAPPER', bm, [sklib.painted_metal((0.78, 0.79, 0.8), 0.2, 0.05, 0.35), STAINLESS, RUBBER], C_LINE, bev=0.01)
bm = bmesh.new()
bx(bm, (-37.6, 1.2, 0.95), (0.06, 0.95, 0.08), 0)                  # control box on the arch leg
bm_obj('A-STRAPPER.ctrl', bm, sklib.painted_metal((0.1, 0.1, 0.11), 0.2), C_LINE, bev=0.005).location = (0, -0.3, 0.5)
carton_at('C.strap', (-37.6, 1.2, 0.78), math.pi / 2)

# label station: table, label printer, carton with the applied label (only allowed text)
table('label_table', (-40.5, 1.2), (1.4, 0.8), C_LINE, 0.88)
bm = bmesh.new()
bx(bm, (-40.95, 1.35, 1.03), (0.32, 0.26, 0.3), 0)                 # printer body
cyl(bm, (-40.95, 1.35, 1.24), 0.07, 0.24, 'Y', 20, 1)              # label roll
bx(bm, (-40.8, 1.35, 0.96), (0.02, 0.2, 0.12), 2)                  # dark output slot
bm_obj('label_printer', bm, [sklib.painted_metal((0.22, 0.23, 0.25), 0.2, 0.0, 0.4),
                              sklib.flat('label_paper', (0.9, 0.9, 0.88), 0.55, var=0.03, scale=200),
                              sklib.plastic((0.02, 0.02, 0.02), 0.1)], C_LINE, bev=0.008)
lab_c = sklib.new_obj('C.label.root', None, C_LINE, loc=(-40.25, 1.12, 0.88), rot=(0, 0, 0.06))
carton_at('C.label', (0, 0, 0), 0.0, C_LINE).parent = lab_c
PAPER = sklib.flat('label_paper', (0.9, 0.9, 0.88), 0.55, var=0.03, scale=200)
INK = sklib.flat('carton_ink', (0.025, 0.05, 0.13), rough=0.55, var=0.12, scale=180)
bm = bmesh.new()
sklib._quad_on_face(bm, (0.10, -0.1765, 0.075), 0.17, 0.085, 0)
lbl = sklib._mesh_obj('C.label.sticker', bm, C_LINE, lab_c)
sklib.mat_to(lbl, PAPER)
sklib._text_mesh('C.label.txt1', 'SKYLARK EXIM · VISAKHAPATNAM · INDIA', 0.0072, INK, lab_c, (0.10, -0.1772, 0.098), 0, C_LINE)
sklib._text_mesh('C.label.txt2', 'VANNAMEI', 0.022, INK, lab_c, (0.10, -0.1772, 0.068), 0, C_LINE)
bm = bmesh.new()                                                   # a sheet of blank labels on the table
bx(bm, (-40.1, 1.45, 0.885), (0.21, 0.3, 0.002), 0)
bm_obj('label_sheet', bm, PAPER, C_LINE)

# packing table + hero carton (lid folded closed by the packer f330-372) + poly bags, tape dispenser
table('pack_table_1', (-43.8, 1.2), (2.0, 1.0), C_LINE, 0.7)     # low packing bench: hands work at the carton rim
HERO = sklib.hero_carton(1.0, 'A-HERO-CARTON', coll=C_LINE, interior=True, loc=(-43.95, 1.12, 0.7), rot_z=0.0)
sklib.carton_key_open(HERO, 330, 372, 1.0, 0.0)
sklib.ease_keys(HERO)
BAG = bpy.data.materials.get('poly_bag_frosted') or sklib._ice_mats()[2]
bm = bmesh.new()
for i in range(6):
    bx(bm, (-43.15 + RNG.uniform(-0.01, 0.01), 0.95 + RNG.uniform(-0.01, 0.01), 0.702 + i * 0.002), (0.55, 0.42, 0.0015), 0)
bm_obj('poly_bags_stack', bm, BAG, C_LINE)
bm = bmesh.new()
bx(bm, (-43.1, 1.5, 0.75), (0.22, 0.1, 0.1), 0)
cyl(bm, (-43.1, 1.5, 0.8), 0.05, 0.05, 'Y', 18, 1)
bm_obj('tape_dispenser', bm, [sklib.painted_metal((0.15, 0.15, 0.16), 0.3), sklib.flat('carton_tape', (0.42, 0.27, 0.12),
                                                                                     rough=0.12, var=0.06, scale=60)],
       C_LINE, bev=0.005)
# glazed blocks waiting on a tray next to the carton (same block geometry as inside the carton)
tray = box('block_tray', (-44.45, 1.15, 0.715), (0.5, 0.36, 0.03), STAINLESS, 0.006, col=C_LINE)
for i in range(2):
    sklib._shrimp_block('A-BLOCK.tray_%d' % i, (0.152, 0.152, 0.085), (-44.55 + i * 0.17, 1.15, 0.73), C_LINE, None,
                        random.Random(30 + i), False)

# second packing table (background) + carton erector with a magazine of flat blanks
table('pack_table_2', (-41.5, 4.1), (2.0, 1.0), C_LINE, 0.9)
for i, x in enumerate((-42.0, -41.0)):
    carton_at('C.t2.%d' % i, (x, 4.05, 0.9), 0.05 * (i - 0.5))
bm = bmesh.new()
bx(bm, (-37.5, 5.2, 0.8), (2.0, 1.2, 1.2), 0)
bx(bm, (-37.5, 5.2, 1.45), (2.0, 1.2, 0.1), 1)
bx(bm, (-36.2, 5.2, 0.75), (0.6, 0.6, 0.03), 1)
for x in (-38.3, -36.7):
    bx(bm, (x, 4.58, 0.95), (0.6, 0.01, 0.6), 2)                   # guard windows
bm_obj('A-CARTON-ERECTOR', bm, [sklib.painted_metal((0.8, 0.81, 0.82), 0.15, 0.0, 0.3), STAINLESS, GL], C_LINE, bev=0.01)
bm = bmesh.new()
for i in range(30):
    bx(bm, (-37.9 + RNG.uniform(-0.004, 0.004), 5.25, 1.505 + i * 0.008), (1.0, 0.8, 0.007), 0)
bm2 = bmesh.new()
bx(bm2, (-37.0, 4.57, 1.0), (0.4, 0.06, 0.3), 0)
bm_obj('A-CARTON-ERECTOR.panel', bm2, sklib.painted_metal((0.2, 0.21, 0.23), 0.2, 0.0, 0.4), C_LINE, bev=0.005)
bm_obj('carton_blanks', bm, sklib.cardboard_kraft(), C_LINE, bev=0.001)

# ======================================================================================================== IQF / GLAZE
C_IQF = coll('A-IQF')
HX0, HX1, HY0, HY1, HHZ = -55.5, -49.5, -1.6, 6.0, 4.2
BELT_Z = 0.95
Y_OUT, Y_IN, BELT_W = 1.2, 3.4, 1.2
bm = bmesh.new()
nx, ny = 4, 7
for j in range(ny):                       # front face panels (with the two mouths cut out)
    y0, y1 = HY0 + (HY1 - HY0) * j / ny, HY0 + (HY1 - HY0) * (j + 1) / ny
    for zz0, zz1 in ((0, BELT_Z - 0.12), (BELT_Z + 0.32, HHZ)):
        bx(bm, (HX1 - 0.04, (y0 + y1) / 2, (zz0 + zz1) / 2), (0.08, y1 - y0 - 0.006, zz1 - zz0 - 0.006), 0)
    for yc in (Y_OUT, Y_IN):
        if y1 <= yc - BELT_W / 2 - 0.1 or y0 >= yc + BELT_W / 2 + 0.1:
            continue
    mid_blocks = []
    a0 = y0
    for yc in (Y_OUT, Y_IN):
        m0, m1 = yc - BELT_W / 2 - 0.08, yc + BELT_W / 2 + 0.08
        if m1 <= y0 or m0 >= y1:
            continue
        if m0 > a0:
            mid_blocks.append((a0, m0))
        a0 = max(a0, m1)
    if a0 < y1:
        mid_blocks.append((a0, y1))
    for b0, b1 in mid_blocks:
        bx(bm, (HX1 - 0.04, (b0 + b1) / 2, BELT_Z + 0.1), (0.08, b1 - b0 - 0.006, 0.44), 0)
for i in range(nx):                       # side + top panels
    x0, x1 = HX0 + (HX1 - HX0) * i / nx, HX0 + (HX1 - HX0) * (i + 1) / nx
    for y in (HY0 + 0.04, HY1 - 0.04):
        bx(bm, ((x0 + x1) / 2, y, HHZ / 2), (x1 - x0 - 0.006, 0.08, HHZ - 0.006), 0)
    bx(bm, ((x0 + x1) / 2, (HY0 + HY1) / 2, HHZ - 0.04), (x1 - x0 - 0.006, HY1 - HY0, 0.08), 0)
for yc in (Y_OUT, Y_IN):                  # mouth frames + inner tunnel liner (dark, vapour inside)
    bx(bm, (HX1 + 0.02, yc, BELT_Z + 0.33), (0.1, BELT_W + 0.3, 0.06), 1)
    bx(bm, (HX1 + 0.02, yc, BELT_Z - 0.13), (0.1, BELT_W + 0.3, 0.06), 1)
    for s in (-1, 1):
        bx(bm, (HX1 + 0.02, yc + s * (BELT_W / 2 + 0.12), BELT_Z + 0.1), (0.1, 0.06, 0.52), 1)
    bx(bm, (HX1 - 0.6, yc, BELT_Z + 0.31), (1.1, BELT_W + 0.16, 0.02), 2)
    for s in (-1, 1):
        bx(bm, (HX1 - 0.6, yc + s * (BELT_W / 2 + 0.08), BELT_Z + 0.1), (1.1, 0.02, 0.44), 2)
bm_obj('A-IQF.housing', bm, [frostify(BRUSHED, 0.4, 0.4, 3.0, 'iqf_housing_frost'), STAIN_FROST,
                              sklib.flat('tunnel_dark', (0.12, 0.13, 0.14), 0.4, var=0.2, scale=20, bump=0.2)],
       C_IQF, bev=0.006)
# frost lips around the mouths (heavy) + refrigerant pipes on top + control cabinet with blank HMI
for yc in (Y_OUT, Y_IN):
    bm = bmesh.new()
    lay = bm.verts.layers.float.new('grad')
    for zz, hgt in ((BELT_Z + 0.33, 0.35), (BELT_Z - 0.13, -0.25)):
        g = bmesh.ops.create_grid(bm, x_segments=12, y_segments=4, size=0.5)
        for v in g['verts']:
            u, w = v.co.x, v.co.y
            v.co = Vector((HX1 + 0.071, yc + u * (BELT_W + 0.5), zz + (w + 0.5) * hgt))
            v[lay] = 1.0 - (w + 0.5)
    m = bpy.data.meshes.new('mouth_frost')
    bm.to_mesh(m)
    bm.free()
    fo = sklib.new_obj('A-IQF.mouth_frost_%g' % yc, m, C_IQF)
    fo.data.materials.append(FROST)
bm = bmesh.new()
for k, y in enumerate((-0.6, -0.2, 4.6, 5.2)):
    cyl(bm, ((HX0 + HX1) / 2, y, HHZ + 0.25), 0.11 if k % 2 else 0.07, HX1 - HX0 + 0.2, 'X', 20)
    for x in (HX0 + 0.5, HX1 - 0.5):
        bx(bm, (x, y, HHZ + 0.06), (0.06, 0.06, 0.12), 0)
bm_obj('A-IQF.pipes', bm, frostify(sklib.flat('pipe_insul', (0.78, 0.8, 0.8), 0.5, var=0.05, scale=30, bump=0.1), 0.6, 0.6, 5.0),
       C_IQF, bev=0.004)
bm = bmesh.new()
bx(bm, (-50.2, -2.6, 1.1), (0.5, 0.9, 2.2), 0)
bx(bm, (-49.94, -2.6, 1.55), (0.02, 0.36, 0.26), 1)
bm_obj('A-IQF.cabinet', bm, [STAINLESS, sklib.flat('hmi_glass', (0.03, 0.05, 0.06), 0.08, var=0.05, scale=10,
                                                   **{'Emission Color': (0.2, 0.35, 0.45, 1), 'Emission Strength': 0.6})],
       C_IQF, bev=0.01)


def belt_mat(name='mesh_belt'):
    """Stainless balanced-weave mesh belt: cross rods + spiral wires, holes cut by alpha; UV scroll by driver
    (offset 0 at f574 -> identical belt texture at BRIDGE_BELT)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt = sklib._new_mat(name)
    out = sklib._n(nt, 'ShaderNodeOutputMaterial', 1200, 0)
    b = sklib._n(nt, 'ShaderNodeBsdfPrincipled', 900, 0)
    sklib._l(nt, b.outputs[0], out.inputs['Surface'])
    tc = sklib._n(nt, 'ShaderNodeTexCoord', -1400, 0)
    mp = sklib._n(nt, 'ShaderNodeMapping', -1200, 0)
    sklib._l(nt, tc.outputs['UV'], mp.inputs['Vector'])
    m['scroll'] = mp.name
    sep = sklib._n(nt, 'ShaderNodeSeparateXYZ', -1000, 0)
    sklib._l(nt, mp.outputs[0], sep.inputs[0])
    u, v = sep.outputs[0], sep.outputs[1]          # u along the belt (world x), v across
    pitch, sp = 0.0127, 0.009
    rod = sklib._math(nt, 'SINE', sklib._math(nt, 'MULTIPLY', u, 2 * math.pi / pitch, x=-800, y=200), x=-650, y=200)
    rod = sklib._maprange(nt, sklib._math(nt, 'ABSOLUTE', rod, x=-500, y=200), 0.55, 0.85, 0.0, 1.0, -350, 200)
    dg = sklib._math(nt, 'ADD', sklib._math(nt, 'MULTIPLY', v, 1.0 / sp, x=-800, y=-100),
                     sklib._math(nt, 'MULTIPLY', u, 0.5 / pitch, x=-800, y=-250), x=-650, y=-150)
    wr = sklib._math(nt, 'SINE', sklib._math(nt, 'MULTIPLY', dg, 2 * math.pi, x=-500, y=-150), x=-400, y=-150)
    wr = sklib._maprange(nt, wr, 0.2, 0.75, 0.0, 1.0, -250, -150)
    solid = sklib._math(nt, 'MAXIMUM', rod, wr, True, -100, 0)
    sklib._l(nt, sklib._maprange(nt, solid, 0.25, 0.35, 0.0, 1.0, 100, 0), b.inputs['Alpha'])
    nz = sklib._noise(nt, tc.outputs['Object'], 40.0, 4.0, 0.5, -300, -400)
    sklib._l(nt, sklib._mix(nt, sklib._maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 0, 1, 100, -400), (0.62, 0.63, 0.64),
                            (0.72, 0.73, 0.74), 'MIX', 300, -300), b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.28
    bp = sklib._n(nt, 'ShaderNodeBump', 600, -300)
    bp.inputs['Strength'].default_value = 0.8
    bp.inputs['Distance'].default_value = 0.0015
    sklib._l(nt, solid, bp.inputs['Height'])
    sklib._l(nt, bp.outputs[0], b.inputs['Normal'])
    return m


BELT_V = 0.10      # m/s
BELT_MAT_OUT = belt_mat('mesh_belt_out')
BELT_MAT_IN = belt_mat('mesh_belt_in')
for m, sgn in ((BELT_MAT_OUT, -1), (BELT_MAT_IN, +1)):
    mp = m.node_tree.nodes[m['scroll']]
    # texture moves with the belt: outfeed -> +x (toward packing), infeed -> -x (into the freezer)
    driver(mp.inputs['Location'], 'default_value', '(frame-574)*%g' % (sgn * BELT_V / 24.0), 0)


def conveyor(name, x0, x1, yc, mat, col):
    bm = bmesh.new()
    xa, xb = min(x0, x1), max(x0, x1)
    for s in (-1, 1):
        bx(bm, ((xa + xb) / 2, yc + s * (BELT_W / 2 + 0.05), BELT_Z - 0.03), (xb - xa, 0.05, 0.16), 0)   # side frames
        bx(bm, ((xa + xb) / 2, yc + s * (BELT_W / 2 + 0.03), BELT_Z + 0.06), (xb - xa, 0.012, 0.1), 0)   # guides
    x = xa + 0.4
    while x < xb - 0.2:
        for s in (-1, 1):
            bx(bm, (x, yc + s * (BELT_W / 2 - 0.05), (BELT_Z - 0.1) / 2), (0.05, 0.05, BELT_Z - 0.1), 0)
            cyl(bm, (x, yc + s * (BELT_W / 2 - 0.05), 0.02), 0.04, 0.04, 'Z', 12)
        bx(bm, (x, yc, 0.25), (0.04, BELT_W - 0.1, 0.04), 0)
        x += 1.4
    bx(bm, ((xa + xb) / 2, yc, BELT_Z - 0.05), (xb - xa, BELT_W - 0.02, 0.01), 1)     # slider bed (dark)
    bx(bm, ((xa + xb) / 2, yc, BELT_Z - 0.22), (xb - xa, BELT_W - 0.02, 0.01), 1)     # return run
    fr = bm_obj(name + '.frame', bm, [STAINLESS, sklib.plastic((0.06, 0.07, 0.08), 0.3)], col, bev=0.004)
    bm = bmesh.new()
    g = bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=0.5)
    me = bpy.data.meshes.new(name + '.belt')
    bm.to_mesh(me)
    bm.free()
    bt = sklib.new_obj(name + '.belt', me, col, loc=((xa + xb) / 2, yc, BELT_Z))
    bt.scale = (xb - xa, BELT_W, 1)
    bpy.context.view_layer.update()
    sklib.mat_to(bt, mat)          # metric box UV: u = world x, v = world y
    return fr, bt


conveyor('A-IQF.outfeed', HX1 - 0.6, -46.0, Y_OUT, BELT_MAT_OUT, C_IQF)
conveyor('A-IQF.infeed', HX1 - 0.6, -43.6, Y_IN, BELT_MAT_IN, C_IQF)
# belt run inside the mouths (dark interior already) + end hopper at the outfeed
bm = bmesh.new()
bx(bm, (-45.6, Y_OUT, BELT_Z - 0.12), (0.8, 1.0, 0.04), 0)
for s in (-1, 1):
    bx(bm, (-45.6, Y_OUT + s * 0.52, BELT_Z + 0.02), (0.8, 0.04, 0.32), 0)
bx(bm, (-45.22, Y_OUT, BELT_Z + 0.02), (0.04, 1.08, 0.32), 0)
for sx in (-1, 1):
    for sy in (-1, 1):
        cyl(bm, (-45.6 + sx * 0.35, Y_OUT + sy * 0.45, (BELT_Z - 0.14) / 2), 0.022, BELT_Z - 0.14, 'Z', 12)
bm_obj('A-IQF.hopper', bm, STAINLESS, C_IQF, bev=0.005)
# infeed chute from the grading hall (upstream end)
bm = bmesh.new()
bx(bm, (-43.95, Y_IN, BELT_Z + 0.25), (0.8, BELT_W + 0.14, 0.04), 0)
for s in (-1, 1):
    bx(bm, (-43.95, Y_IN + s * (BELT_W / 2 + 0.07), BELT_Z + 0.12), (0.8, 0.04, 0.3), 0)
bx(bm, (-43.55, Y_IN, BELT_Z + 0.12), (0.04, BELT_W + 0.14, 0.3), 0)
bm_obj('A-IQF.infeed_hood', bm, STAINLESS, C_IQF, bev=0.004)

# glazing spray bar over the outfeed
X_SPRAY = -47.8
bm = bmesh.new()
cyl(bm, (X_SPRAY, Y_OUT, BELT_Z + 0.55), 0.024, BELT_W + 0.3, 'Y', 16)
for i in range(13):
    cyl(bm, (X_SPRAY, Y_OUT - 0.54 + i * 0.09, BELT_Z + 0.51), 0.008, 0.05, 'Z', 10)
for s in (-1, 1):
    bx(bm, (X_SPRAY, Y_OUT + s * (BELT_W / 2 + 0.1), BELT_Z + 0.3), (0.04, 0.04, 0.55), 0)
cyl(bm, (X_SPRAY, Y_OUT + BELT_W / 2 + 0.2, BELT_Z + 1.8), 0.02, 2.5, 'Z', 12)
bm_obj('A-IQF.spray_bar', bm, STAINLESS, C_IQF, bev=0.003)


# ---------------------------------------------------------------------------- shrimp scans (CC0) + GN instancing
def load_scan(fn, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=sklib.SRC + '/models/plant-cold/' + fn)
    obs = [o for o in bpy.data.objects if o not in before]
    ob = [o for o in obs if o.type == 'MESH'][0]
    for o in obs:
        if o is not ob:
            bpy.data.objects.remove(o)
    ob.name = name
    ob.parent = None
    img = [n.image for n in ob.material_slots[0].material.node_tree.nodes if n.type == 'TEX_IMAGE'][0]
    # lying on its side on the belt, 0.11 m long, origin at the centre bottom
    s = 0.11 / max(ob.dimensions)
    me = ob.data
    me.transform(Matrix.Rotation(math.pi / 2, 4, 'X') @ Matrix.Diagonal((s, s, s, 1)))
    zs = [v.co.z for v in me.vertices]
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    me.transform(Matrix.Translation((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs))))
    me.shade_smooth()
    for c in ob.users_collection:
        c.objects.unlink(ob)
    return ob, img


def shrimp_mat(name, img, kind):
    m, nt = sklib._new_mat(name)
    out = sklib._n(nt, 'ShaderNodeOutputMaterial', 900, 0)
    b = sklib._n(nt, 'ShaderNodeBsdfPrincipled', 600, 0)
    sklib._l(nt, b.outputs[0], out.inputs['Surface'])
    ti = sklib._n(nt, 'ShaderNodeTexImage', -600, 100)
    ti.image = img
    if kind == 'raw':          # grey-translucent raw shrimp, wet
        col = sklib._mix(nt, 0.3, ti.outputs['Color'], (0.55, 0.56, 0.55), 'MIX', -250, 100)
        b.inputs['Subsurface Weight'].default_value = 0.55
        b.inputs['Subsurface Radius'].default_value = (0.6, 0.5, 0.45)
        b.inputs['Subsurface Scale'].default_value = 0.004
        b.inputs['Roughness'].default_value = 0.3
        b.inputs['Coat Weight'].default_value = 0.6
        b.inputs['Coat Roughness'].default_value = 0.08
    else:                      # IQF frozen + glazed: paler, thin clear ice coat with frost speckle
        col = sklib._mix(nt, 0.15, ti.outputs['Color'], (0.75, 0.72, 0.7), 'MIX', -250, 100)
        b.inputs['Subsurface Weight'].default_value = 0.3
        b.inputs['Subsurface Scale'].default_value = 0.003
        b.inputs['Coat Weight'].default_value = 1.0
        b.inputs['Coat Roughness'].default_value = 0.04
        tc = sklib._n(nt, 'ShaderNodeTexCoord', -800, -300)
        nz = sklib._noise(nt, tc.outputs['Object'], 400.0, 3.0, 0.6, -600, -300)
        sklib._l(nt, sklib._maprange(nt, nz.outputs['Fac'], 0.4, 0.7, 0.25, 0.6, -300, -300), b.inputs['Roughness'])
    sklib._l(nt, col, b.inputs['Base Color'])
    return m


C_SCAN = coll('SHRIMP_SRC', False)
SCANS = []
for fn, nm in (('greasyback-shrimp-lo.glb', 'SCAN_greasyback'), ('green-tiger-prawn-lo.glb', 'SCAN_tiger')):
    ob, img = load_scan(fn, nm)
    SCANS.append((ob, img))
SRC_RAW = coll('SHRIMP_RAW', False)
SRC_GLZ = coll('SHRIMP_GLAZED', False)
for ob, img in SCANS:
    for kind, C in (('raw', SRC_RAW), ('glazed', SRC_GLZ)):
        o2 = bpy.data.objects.new(ob.name + '_' + kind, ob.data.copy())
        o2.data.materials.clear()
        o2.data.materials.append(shrimp_mat('shrimp_%s_%s' % (ob.name[5:], kind), img, kind))
        C.objects.link(o2)


def gn_flow(name, src_coll, speed_x, length, f_zero=574, wrap=True):
    """GN: points (mesh verts, attrs 'rot','scl','pick') -> instances of src_coll children, x scrolled by
    speed_x (m/s) relative to f_zero and wrapped in [0, length]."""
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes
    L = ng.links
    gi = N.new('NodeGroupInput')
    go = N.new('NodeGroupOutput')
    st = N.new('GeometryNodeInputSceneTime')
    pos = N.new('GeometryNodeInputPosition')
    sp = N.new('ShaderNodeSeparateXYZ')
    L.new(pos.outputs[0], sp.inputs[0])
    t = N.new('ShaderNodeMath')
    t.operation = 'SUBTRACT'
    L.new(st.outputs['Frame'], t.inputs[0])
    t.inputs[1].default_value = f_zero
    d = N.new('ShaderNodeMath')
    d.operation = 'MULTIPLY_ADD'
    L.new(t.outputs[0], d.inputs[0])
    d.inputs[1].default_value = speed_x / 24.0
    L.new(sp.outputs[0], d.inputs[2])
    w = N.new('ShaderNodeMath')
    w.operation = 'WRAP'
    L.new(d.outputs[0], w.inputs[0])
    w.inputs[1].default_value = length
    w.inputs[2].default_value = 0.0
    cb = N.new('ShaderNodeCombineXYZ')
    L.new(w.outputs[0] if wrap else d.outputs[0], cb.inputs[0])
    L.new(sp.outputs[1], cb.inputs[1])
    L.new(sp.outputs[2], cb.inputs[2])
    setp = N.new('GeometryNodeSetPosition')
    L.new(gi.outputs[0], setp.inputs['Geometry'])
    L.new(cb.outputs[0], setp.inputs['Position'])
    ci = N.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = src_coll
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    ci.transform_space = 'ORIGINAL'
    iop = N.new('GeometryNodeInstanceOnPoints')
    L.new(setp.outputs[0], iop.inputs['Points'])
    L.new(ci.outputs[0], iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    na = {}
    for an, tp in (('rot', 'FLOAT_VECTOR'), ('scl', 'FLOAT_VECTOR'), ('pick', 'INT')):
        a = N.new('GeometryNodeInputNamedAttribute')
        a.data_type = tp
        a.inputs['Name'].default_value = an
        na[an] = a
    e2r = N.new('FunctionNodeEulerToRotation')
    L.new(na['rot'].outputs['Attribute'], e2r.inputs[0])
    L.new(e2r.outputs[0], iop.inputs['Rotation'])
    L.new(na['scl'].outputs['Attribute'], iop.inputs['Scale'])
    L.new(na['pick'].outputs['Attribute'], iop.inputs['Instance Index'])
    L.new(iop.outputs[0], go.inputs[0])
    return ng


def point_cloud_obj(name, pts, col, ng, loc):
    """pts = [(co, rot, scl, pick)] -> mesh of loose verts with attributes + GN modifier."""
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(pts))
    me.vertices.foreach_set('co', [c for p in pts for c in p[0]])
    for an, tp, idx in (('rot', 'FLOAT_VECTOR', 1), ('scl', 'FLOAT_VECTOR', 2), ('pick', 'INT', 3)):
        at = me.attributes.new(an, tp, 'POINT')
        if tp == 'INT':
            at.data.foreach_set('value', [p[idx] for p in pts])
        else:
            at.data.foreach_set('vector', [c for p in pts for c in p[idx]])
    ob = sklib.new_obj(name, me, col, loc=loc)
    md = ob.modifiers.new('flow', 'NODES')
    md.node_group = ng
    return ob


# raw shrimp in graded rows on the infeed (moving -x into the freezer; at rest pose on f574 = BRIDGE_BELT)
L_IN = (-43.6) - (HX1 - 0.6)            # local length, starts 0.6 m inside the mouth
rng = random.Random(574)
pts = []
x = 0.03
while x < L_IN - 0.05:
    n = 9
    for k in range(n):
        y = -0.5 + k * (1.0 / (n - 1)) + rng.uniform(-0.012, 0.012)
        flip = rng.random() < 0.5
        pts.append(((x + rng.uniform(-0.008, 0.008), y, 0.0015),
                    (0, 0, (math.pi / 2 if flip else -math.pi / 2) + rng.uniform(-0.25, 0.25)),
                    (rng.uniform(0.92, 1.08),) * 3, 0 if rng.random() < 0.6 else 1))
    x += 0.12
NG_IN = gn_flow('GN_shrimp_infeed', SRC_RAW, -BELT_V, L_IN)
RAW = point_cloud_obj('SHRIMP.infeed_rows', pts, C_IQF, NG_IN, (HX1 - 0.6, Y_IN, BELT_Z))
# glazed IQF shrimp scattered on the outfeed (moving +x toward the hopper)
L_OUT = (-46.0) - (HX1 - 0.6)
pts = []
for i in range(int(L_OUT * 1.2 * 70)):
    pts.append(((rng.uniform(0, L_OUT), rng.uniform(-0.54, 0.54), 0.0015), (0, 0, rng.uniform(0, 6.283)),
                (rng.uniform(0.9, 1.1),) * 3, 0 if rng.random() < 0.55 else 1))
NG_OUT = gn_flow('GN_shrimp_outfeed', SRC_GLZ, BELT_V, L_OUT)
GLZ = point_cloud_obj('SHRIMP.outfeed_iqf', pts, C_IQF, NG_OUT, (HX1 - 0.6, Y_OUT, BELT_Z))

# glazing spray: droplets falling under gravity-speed, wrapped (closed form -> deterministic per frame)
drop = bpy.data.meshes.new('droplet')
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.0009)
for v in bm.verts:
    v.co.z *= 5.0
bm.to_mesh(drop)
bm.free()
C_DROP = coll('DROPLET_SRC', False)
dob = bpy.data.objects.new('DROPLET', drop)
C_DROP.objects.link(dob)
dob.data.materials.append(sklib.flat('water_drop', (0.85, 0.9, 0.92), 0.02, var=0.0,
                                     **{'Alpha': 0.55, 'Coat Weight': 1.0, 'IOR': 1.33}))
ng = bpy.data.node_groups.new('GN_spray', 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
N, Lk = ng.nodes, ng.links
gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
st, pos = N.new('GeometryNodeInputSceneTime'), N.new('GeometryNodeInputPosition')
sp = N.new('ShaderNodeSeparateXYZ')
Lk.new(pos.outputs[0], sp.inputs[0])
dd = N.new('ShaderNodeMath')
dd.operation = 'MULTIPLY_ADD'
Lk.new(st.outputs['Frame'], dd.inputs[0])
dd.inputs[1].default_value = -2.6 / 24.0
Lk.new(sp.outputs[2], dd.inputs[2])
ww = N.new('ShaderNodeMath')
ww.operation = 'WRAP'
Lk.new(dd.outputs[0], ww.inputs[0])
ww.inputs[1].default_value, ww.inputs[2].default_value = 0.0, -0.5
cb = N.new('ShaderNodeCombineXYZ')
Lk.new(sp.outputs[0], cb.inputs[0])
Lk.new(sp.outputs[1], cb.inputs[1])
Lk.new(ww.outputs[0], cb.inputs[2])
sp2 = N.new('GeometryNodeSetPosition')
Lk.new(gi.outputs[0], sp2.inputs['Geometry'])
Lk.new(cb.outputs[0], sp2.inputs['Position'])
oi = N.new('GeometryNodeObjectInfo')
oi.inputs['Object'].default_value = dob
iop = N.new('GeometryNodeInstanceOnPoints')
Lk.new(sp2.outputs[0], iop.inputs['Points'])
Lk.new(oi.outputs['Geometry'], iop.inputs['Instance'])
Lk.new(iop.outputs[0], go.inputs[0])
me = bpy.data.meshes.new('spray_pts')
co = []
for i in range(3500):
    yy = rng.uniform(-0.56, 0.56)
    xx = rng.gauss(0, 0.012 + 0.0)
    co += [xx, yy, rng.uniform(-0.5, 0.0)]
me.vertices.add(len(co) // 3)
me.vertices.foreach_set('co', co)
spray = sklib.new_obj('A-IQF.glaze_spray', me, C_IQF, loc=(X_SPRAY, Y_OUT, BELT_Z + 0.5))
spray.modifiers.new('spray', 'NODES').node_group = ng

# cold vapour: out of both mouths (rolling forward/down) + a thin haze over the outfeed
mist_box('iqf_vapour_out', (HX1 + 0.55, Y_OUT, BELT_Z + 0.25), (1.2, 1.5, 0.7), mist_mat('vapour_out', 0.3, 1.2, (-0.012, 0.0, 0.002)), C_IQF)
mist_box('iqf_vapour_in', (HX1 + 0.45, Y_IN, BELT_Z + 0.3), (1.0, 1.5, 0.7), mist_mat('vapour_in', 0.22, 1.2, (-0.01, 0.0, 0.002)), C_IQF)

# IQF zone lights (cool LED 5000 K)
area('L_iqf', (-47.6, (Y_OUT + Y_IN) / 2, PH - 0.1), (1.4, 3.2), 440, shadow=True)

# ---- BRIDGE_BELT marker: belt surface point under the f574 camera (raw rows; belt UV offset 0 at f574)
C_BB = coll('BRIDGE_BELT', C_IQF)
X_BB = -48.95
BB = sklib.new_obj('BRIDGE_BELT', None, C_BB, loc=(X_BB, Y_IN, BELT_Z), rot=(0, 0, math.pi / 2))
BB.empty_display_size = 0.5
BB_LIGHT = area('L_BRIDGE_BELT', (X_BB, Y_IN, BELT_Z + 2.4), (1.2, 1.2), 180, 5000)
C_LT.objects.unlink(BB_LIGHT)
C_BB.objects.link(BB_LIGHT)

# ---- packing + IQF staff (full PPE, masked, hairnets; varied bodies/skin/age)
STAFF = [  # name, sex, age, pose, loc, rz, seed, skin, body, cycle
    ('P-PLANT-1', 'male', 0.3, 'carry', (-33.4, 0.4), math.pi, 11, 0.7, {'height': 0.55}, 'work'),
    ('P-PLANT-2', 'female', 0.45, 'work_table', (-38.35, 2.05), 0.0, 12, 0.5, {'weight': 0.6}, 'work'),
    ('P-PLANT-3', 'female', 0.25, 'work_table', (-40.4, 1.98), 0.0, 13, 0.4, None, 'work'),
    ('P-PLANT-4', 'female', 0.35, 'work_table', (-43.92, 1.66), 0.0, 14, 0.62, {'height': 0.4}, 'work'),
    ('P-PLANT-5', 'male', 0.55, 'work_table', (-42.0, 4.95), 0.0, 15, 0.8, {'weight': 0.65}, 'work'),
    ('P-PLANT-6', 'female', 0.6, 'work_table', (-41.0, 4.95), 0.0, 16, 0.55, None, 'work'),
    ('P-PLANT-7', 'male', 0.4, 'work_table', (-37.0, 4.12), math.pi, 17, 0.65, {'muscle': 0.6}, 'work'),
    ('P-PLANT-8', 'male', 0.22, 'walk', (-36.0, -2.3), math.pi / 2, 18, 0.75, None, 'walk'),
    ('P-PLANT-9', 'female', 0.4, 'work_table', (-45.9, 2.3), -math.pi / 2, 19, 0.58, None, 'work'),
    ('P-PLANT-10', 'male', 0.5, 'stand', (-49.4, -2.6), -math.pi / 2, 20, 0.72, {'weight': 0.55}, 'work'),
]
for i, (nm, sx, age, pose, (x, y), rz, sd, sk, bd, cyc) in enumerate(STAFF):
    p = person(nm, sx, age, 'ppe_plant', pose, (x, y, 0), rz, sd, sk, bd, cyc, phase=(i * 0.37) % 1.0, f0=192)
    if cyc == 'walk':          # walks toward the cold-store door side (+x) at ~1.2 m/s, f192-383
        key(p, 'location', [(192, (-41.0, -2.3, p.location.z)), (383, (-31.5, -2.3, p.location.z))])
        for fc in sklib._fcurves(p):
            if fc.data_path == 'location':
                for k in fc.keyframe_points:
                    k.interpolation = 'LINEAR'
carton_at('C.carried', (-33.4, 0.80, 0.83), math.pi / 2)
# the IQF worker's tray of glazed shrimp (held at the hopper edge)
table('iqf_check_table', (-46.42, 2.3), (0.5, 0.5), C_IQF, 0.9)
tray2 = box('iqf_check_tray', (-46.38, 2.3, 0.915), (0.32, 0.44, 0.025), STAINLESS, 0.005, col=C_IQF)
pts = []
for i in range(26):
    pts.append(((rng.uniform(-0.1, 0.1), rng.uniform(-0.16, 0.16), 0.0), (0, 0, rng.uniform(0, 6.28)),
                (rng.uniform(0.9, 1.05),) * 3, rng.randint(0, 1)))
ng_static = gn_flow('GN_shrimp_static', SRC_GLZ, 0.0, 10.0, wrap=False)
point_cloud_obj('SHRIMP.tray', pts, C_IQF, ng_static, (-46.38, 2.3, 0.929))


# ============================================================================================================ WORLD
sklib.sky_world(sun_elev_deg=40, sun_az_deg=135, strength=1.0)
W = S.world
nt = W.node_tree
bg = [n for n in nt.nodes if n.type == 'BACKGROUND'][0]
outw = [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0]
bg2 = sklib._n(nt, 'ShaderNodeBackground', 0, -250)
bg2.inputs['Color'].default_value = (0.86, 0.9, 0.93, 1)
bg2.inputs['Strength'].default_value = 0.35
mx = sklib._n(nt, 'ShaderNodeMixShader', 250, -100)
sklib._l(nt, bg.outputs[0], mx.inputs[1])
sklib._l(nt, bg2.outputs[0], mx.inputs[2])
sklib._l(nt, mx.outputs[0], outw.inputs[0])
outw.location = (500, 0)
fac = mx.inputs[0]
for f, v in ((1, 0.0), (34, 0.0), (64, 1.0)):
    fac.default_value = v
    fac.keyframe_insert('default_value', frame=f)
SUN = bpy.data.objects['SK_Sun']
for f, v in ((1, SUN.data.energy), (80, SUN.data.energy), (110, 0.0)):
    SUN.data.energy = v
    SUN.data.keyframe_insert('energy', frame=f)

# ============================================================================================================ CAMERA
CAM = sklib.camera('CAM', 50.0, (X_LEAF + 1.2, 0, 1.45), (X_LEAF - 5, 0, 1.45))
CAM.data.clip_start = 0.03
KEYS = [  # frame, location, look-at (or Euler), lens
    (1, (X_LEAF + 1.2, 0.0, 1.45), (X_LEAF - 5, 0.0, 1.45), 50),
    (30, (X_LEAF + 0.95, 0.0, 1.47), (-5.0, 0.0, 1.45), 46),
    (52, (-0.6, 0.04, 1.62), (-8.0, 0.3, 1.7), 34),
    (70, (-3.6, 0.05, 1.85), (-12.0, 0.6, 1.9), 28),
    (110, (-8.4, -0.1, 2.1), (X_TRUCK, 0.9, 2.3), 28),
    (150, (-12.6, -0.5, 2.7), (X_TRUCK, 1.0, 1.4), 28),
    (192, (-21.5, -1.0, 8.4), (-30.0, 1.0, 0.8), 24),
    (230, (-30.5, 0.0, 1.75), (-37.0, 0.8, 1.3), 28),
    (262, (-34.4, -1.0, 1.8), (-38.5, 1.3, 1.0), 28),
    (300, (-39.0, -0.5, 1.8), (-42.0, 1.2, 0.95), 30),
    (340, (-42.3, -0.2, 1.7), (-43.9, 1.15, 0.8), 32),
    (383, (-43.25, 0.15, 1.5), (-43.95, 1.12, 0.82), 35),
    (440, (-45.4, 0.2, 1.55), (-48.0, Y_OUT, 0.97), 32),
    (500, (-47.3, 0.3, 1.5), (-49.5, 1.1, 1.05), 32),
    (540, (-48.55, 0.9, 1.62), (-49.6, 1.3, 1.05), 35),
    (574, (X_BB, Y_IN, BELT_Z + 1.0), Euler((0, 0, math.pi / 2)), 35),
]
prev = None
for f, loc, aim, lens in KEYS:
    e = aim.copy() if isinstance(aim, Euler) else look_euler(loc, aim)
    if prev is not None:
        e.make_compatible(prev)
    prev = e
    CAM.location, CAM.rotation_euler = loc, e
    CAM.keyframe_insert('location', frame=f)
    CAM.keyframe_insert('rotation_euler', frame=f)
    CAM.data.lens = lens
    CAM.data.keyframe_insert('lens', frame=f)
sklib.ease_keys(CAM, CAM.data)
FOCUS = sklib.new_obj('CAM_focus', None, coll('LIGHTS'))
for f, p in ((1, (X_LEAF, 0, 1.45)), (40, (-3.0, 0, 1.6)), (110, (X_TRUCK, 0.8, 2.0)), (150, (X_TRUCK, 0.9, 1.4)),
             (192, (-27.5, 0.5, 1.5)), (230, (-35.0, 1.0, 1.2)), (300, (-40.3, 1.12, 0.98)), (383, (-43.95, 1.12, 0.85)),
             (440, (-47.2, Y_OUT, 0.97)), (500, (-48.6, 1.1, 1.0)), (540, (-49.5, 1.2, 1.05)), (574, (X_BB, Y_IN, BELT_Z))):
    FOCUS.location = p
    FOCUS.keyframe_insert('location', frame=f)
sklib.ease_keys(FOCUS)
sklib.dof(CAM, FOCUS, 6.3)

# ---- render cost: hide whole areas while they cannot be seen (walls/doors closed or behind camera)
def hide_window(obs, f_hide, f_show=None):
    for o in obs:
        for f, h in ((1, False), (f_hide, True)) if f_show is None else ((1, True), (f_show, False)):
            o.hide_render = h
            o.keyframe_insert('hide_render', frame=f)
        o.hide_render = False


def coll_objs(*cs):
    out = []
    for c in cs:
        out += list(c.all_objects)
    return out


hide_window(coll_objs(C_RACKS, C_EVAP, C_CUR, coll('A-FORKLIFT')) + [OPER] + list(OPER.children_recursive), 245)
hide_window(coll_objs(C_LINE, C_IQF) + [o for o in C_PPL.all_objects if o not in set([OPER] + list(OPER.children_recursive))],
            None, 175)
SUN.hide_render = False
SUN.keyframe_insert('hide_render', frame=1)
SUN.hide_render = True
SUN.keyframe_insert('hide_render', frame=112)
SUN.hide_render = False

# ============================================================================================================ FINISH
e = S.eevee
e.volumetric_tile_size = '16'
e.volumetric_samples = 32
e.volumetric_end = 25.0
print('BUILD %.1fs' % (time.time() - T0))
sklib.finish('plant-cold', 'cold')
S.frame_set(1)

