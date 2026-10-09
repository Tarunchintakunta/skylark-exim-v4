"""S9 map.blend -> B4 markets backdrop still.

Projection contract (the site overlays SVG routes on this image):
  plain equirectangular, lon -20..150 -> x 0..W, lat 65..-10 -> y 0..H, W:H = 170:75.
Plane spans x=-20..150, y=-10..65 (1 unit = 1 degree), ortho camera, ortho_scale 170, centred (65, 27.5).
Shading is flat emission (Standard view transform) so sea is exactly ink #0E1417 and flat land exactly glaze #BFD3D6;
relief = Bump node on ETOPO elevation, lit by a fixed top-left light vector in the shader (no scene lights).

Data (public domain, see assets-src/tex/LICENSES.tsv), downloaded to /tmp/claude-501/sk/mapdata/:
  ne_50m_land.geojson  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_land.geojson
  etopo.asc            https://coastwatch.pfeg.noaa.gov/erddap/griddap/etopo180.esriAscii?altitude[(-10):3:(65)][(-20):3:(150)]
Run: Blender --factory-startup -b --python map.py
"""
import bpy, json, struct, zlib, os, sys
import numpy as np

REPO = '/Users/tarunchintakunta/Desktop/2.0/skylark-exim-v4'
DATA = '/tmp/claude-501/sk/mapdata'
GEN = REPO + '/assets-src/tex/gen'
LON0, LON1, LAT0, LAT1 = -20.0, 150.0, -10.0, 65.0
W, H = 1920, 847
TEX_W = 3840                                    # land mask texture: 2 texels per output px
SS = 2                                          # extra supersampling for the mask edge
SUN = np.array([-1.0, 1.0, 1.25])               # top-left (north-west) light, ~41 deg high
RELIEF = 0.85                                   # how much the bump shading modulates the land
BUMP_DIST = 0.16                                # degrees of plane per km of elevation (exaggeration)


def srgb_to_lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def write_png16(path, a):
    """a: 2-D float array 0..1 -> 16-bit greyscale PNG (stdlib only)."""
    a = (np.clip(a, 0, 1) * 65535 + 0.5).astype('>u2')
    raw = b''.join(b'\0' + row.tobytes() for row in a)
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', a.shape[1], a.shape[0], 16, 0, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def land_mask(tw, th):
    """Even-odd scanline fill of every Natural Earth land ring, pixel centres, same lon/lat contract."""
    gj = json.load(open(DATA + '/ne_50m_land.geojson'))
    rings = []
    for ft in gj['features']:
        g = ft['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for p in polys:
            rings += [np.asarray(r, float) for r in p]
    T = np.zeros((th, tw + 1), np.uint16)
    for r in rings:
        x = (r[:, 0] - LON0) / (LON1 - LON0) * tw
        y = (LAT1 - r[:, 1]) / (LAT1 - LAT0) * th
        x0, y0, x1, y1 = x[:-1], y[:-1], x[1:], y[1:]
        lo, hi = np.minimum(y0, y1), np.maximum(y0, y1)
        a = np.ceil(lo - 0.5).astype(int)        # first row whose centre (j+0.5) >= lo
        b = np.ceil(hi - 0.5).astype(int)        # rows [a, b) are crossed (half-open: no double count at vertices)
        n = np.clip(b, 0, th) - np.clip(a, 0, th)
        keep = n > 0
        if not keep.any():
            continue
        a, n = np.clip(a, 0, th)[keep], n[keep]
        x0, y0, x1, y1 = x0[keep], y0[keep], x1[keep], y1[keep]
        idx = np.repeat(np.arange(len(n)), n)
        rows = a[idx] + (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n))
        yc = rows + 0.5
        xc = x0[idx] + (yc - y0[idx]) * (x1[idx] - x0[idx]) / (y1[idx] - y0[idx])
        col = np.clip(np.ceil(xc - 0.5).astype(int), 0, tw)
        np.add.at(T, (rows, col), 1)
    return (np.cumsum(T, axis=1)[:, :tw] & 1).astype(np.float32)


def blur(a, s):
    k = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2)
    k /= k.sum()
    for ax in (0, 1):
        a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, 3 * s, mode='edge'), k, 'valid'), ax, a)
    return a


def build_textures():
    os.makedirs(GEN, exist_ok=True)
    th = round(TEX_W * 75 / 170)
    m = land_mask(TEX_W * SS, th * SS).reshape(th, SS, TEX_W, SS).mean(axis=(1, 3))
    write_png16(GEN + '/map_land_mask.png', m)
    # ETOPO 3' grid, row 0 = lat 65 (north). Elevation in km, land only, softened; 0..1 over 0..8 km.
    hdr = {}
    with open(DATA + '/etopo.asc') as f:
        for _ in range(6):
            k, v = f.readline().split()
            hdr[k] = float(v)
        z = np.loadtxt(f, dtype=np.float32)
    z = np.clip(z, 0, None) / 1000.0
    z = blur(z, 3) ** 0.75                       # soften + lift lowland texture
    write_png16(GEN + "/map_height.png", z / 8.0 ** 0.75)
    print('map textures', m.shape, z.shape, 'land frac %.3f' % m.mean())


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    sea, land = srgb_to_lin('#0E1417'), srgb_to_lin('#BFD3D6')

    me = bpy.data.meshes.new('A-MAP')
    me.from_pydata([(LON0, LAT0, 0), (LON1, LAT0, 0), (LON1, LAT1, 0), (LON0, LAT1, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap')
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = c
    ob = bpy.data.objects.new('A-MAP', me)
    s.collection.objects.link(ob)

    mat = bpy.data.materials.new('map_relief')
    mat.use_nodes = True
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    def node(t, **kw):
        n = N.new(t)
        for k, v in kw.items():
            setattr(n, k, v)
        return n
    def img(name, interp):
        i = bpy.data.images.load(GEN + '/' + name, check_existing=True)
        i.colorspace_settings.name = 'Non-Color'
        return node('ShaderNodeTexImage', image=i, interpolation=interp, extension='EXTEND')
    tm, th_ = img('map_land_mask.png', 'Linear'), img('map_height.png', 'Cubic')
    hk = node('ShaderNodeMath', operation='MULTIPLY'); hk.inputs[1].default_value = 8.0      # -> km
    L.new(th_.outputs['Color'], hk.inputs[0])
    bump = node('ShaderNodeBump'); bump.inputs['Strength'].default_value = 1.0
    bump.inputs['Distance'].default_value = BUMP_DIST
    L.new(hk.outputs[0], bump.inputs['Height'])
    sun = SUN / np.linalg.norm(SUN)
    dot = node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
    dot.inputs[1].default_value = tuple(sun)
    L.new(bump.outputs['Normal'], dot.inputs[0])
    # shade = dot / sun.z (flat ground = 1.0); relief = 1 + RELIEF*(shade-1), clamped soft
    sh = node('ShaderNodeMapRange', clamp=False)   # unclamped: lit slopes may brighten a little above flat
    sh.inputs['From Min'].default_value, sh.inputs['From Max'].default_value = 0.0, sun[2]
    sh.inputs['To Min'].default_value, sh.inputs['To Max'].default_value = 1 - RELIEF, 1.0
    L.new(dot.outputs['Value'], sh.inputs['Value'])
    cl = node('ShaderNodeClamp'); cl.inputs['Min'].default_value, cl.inputs['Max'].default_value = 0.35, 1.18
    L.new(sh.outputs[0], cl.inputs['Value'])
    lc = node('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    lc.inputs['Factor'].default_value = 1.0
    lc.inputs[6].default_value = (*land, 1)
    L.new(cl.outputs[0], lc.inputs[7])
    mix = node('ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*sea, 1)
    L.new(tm.outputs['Color'], mix.inputs['Factor'])
    L.new(lc.outputs[2], mix.inputs[7])
    em = node('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0
    L.new(mix.outputs[2], em.inputs['Color'])
    out = node('ShaderNodeOutputMaterial')
    L.new(em.outputs[0], out.inputs['Surface'])
    me.materials.append(mat)

    w = bpy.data.worlds.new('ink'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (*sea, 1)
    s.world = w

    cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = LON1 - LON0
    cd.clip_start, cd.clip_end = 1, 1000
    cam = bpy.data.objects.new('cam', cd); cam.location = ((LON0 + LON1) / 2, (LAT0 + LAT1) / 2, 100)
    s.collection.objects.link(cam); s.camera = cam

    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = W, H, 100
    s.render.filter_size = 1.0
    s.eevee.taa_render_samples = 64
    s.view_settings.view_transform, s.view_settings.look = 'Standard', 'None'
    s.view_settings.exposure, s.view_settings.gamma = 0.0, 1.0
    s.render.image_settings.file_format, s.render.image_settings.color_mode = 'PNG', 'RGB'
    s.frame_start = s.frame_end = 1
    s.render.filepath = '//../render/markets-map/markets-map'
    path = REPO + '/assets-src/blender/map.blend'
    bpy.ops.wm.save_as_mainfile(filepath=path, relative_remap=True, compress=True)
    print('saved', path)


if '--no-tex' not in sys.argv:
    build_textures()
build_scene()
