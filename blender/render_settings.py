"""Apply the standard Skylark v4 render settings to the open .blend (RENDER_PIPELINE.md §2), then save it.
Via Blender MCP: exec(open(REPO + '/blender/render_settings.py').read())   (uses the .blend's own name + frame range from scripts/scenes.sh)
Headless:       Blender -b assets-src/blender/<blend>.blend --python blender/render_settings.py -- <blend> [ext|int|cold|dawn]
EEVEE (Blender 4.2+ "EEVEE Next" / 5.x "EEVEE"), 1920x1080, 24 fps, AgX, motion blur on, PNG 8-bit, output //../render/<blend>/.
"""
import os
import re
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
name = argv[0] if argv else os.path.splitext(os.path.basename(bpy.data.filepath))[0]
kind = argv[1] if len(argv) > 1 else None


def _scenes_sh_range(blend):
    """Read first/last frame + light kind for this .blend from scripts/scenes.sh (single source of truth)."""
    here = os.path.dirname(bpy.data.filepath) or os.getcwd()
    for root in (os.path.join(here, "..", ".."), os.getcwd()):
        p = os.path.join(root, "scripts", "scenes.sh")
        if os.path.exists(p):
            lo, hi, k = None, None, None
            for line in open(p):
                m = re.match(r'\s*"([^|"]+)\|([^|"]+)\|(\d+)\|(\d+)\|([^|"]+)\|([^|"]+)"', line)
                if m and m.group(2) == blend:
                    f, l = int(m.group(3)), int(m.group(4))
                    lo = f if lo is None else min(lo, f)
                    hi = l if hi is None else max(hi, l)
                    k = m.group(6)
            if lo is not None:
                return lo, hi, k
    return None


s = bpy.context.scene
rng = _scenes_sh_range(name)
if rng:
    s.frame_start, s.frame_end = rng[0], rng[1]
    kind = kind or rng[2]
kind = kind or "ext"

engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
s.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"

r = s.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
r.fps, r.fps_base = 24, 1.0
r.use_motion_blur = True
if hasattr(r, "motion_blur_shutter"):
    r.motion_blur_shutter = 0.5
r.film_transparent = False
r.use_overwrite = False          # resume-safe: existing frames are skipped
r.use_placeholder = False
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGB"
r.image_settings.color_depth = "8"
r.image_settings.compression = 15
r.filepath = "//../render/%s/" % name

e = s.eevee
e.taa_render_samples = 64
for attr, val in (("use_raytracing", True), ("use_shadows", True), ("use_gtao", True),
                  ("use_bloom", False), ("use_volumetric_shadows", False)):
    if hasattr(e, attr):
        setattr(e, attr, val)
rto = getattr(e, "ray_tracing_options", None)
if rto is not None and hasattr(rto, "resolution_scale"):
    rto.resolution_scale = "2"   # half-res ray tracing: big speed win, invisible after encode
if hasattr(e, "shadow_ray_count"):
    e.shadow_ray_count = 1
if hasattr(e, "shadow_step_count"):
    e.shadow_step_count = 6
if hasattr(e, "use_fast_gi"):
    e.use_fast_gi = True

vs = s.view_settings
vs.view_transform = "AgX"
pref = {"ext": "AgX - Medium High Contrast", "int": "AgX - Base Contrast", "cold": "AgX - Base Contrast", "dawn": "AgX - Medium Low Contrast"}
# The look enum is context-dependent (empty when read from bl_rna in 5.x), so set it directly.
try:
    vs.look = pref.get(kind, "None")
except TypeError:
    vs.look = "None"
vs.exposure = 0.0
vs.gamma = 1.0
s.display_settings.display_device = "sRGB"
# No compositor overlays / colour washes: the v3 "dark blue overlay" is banned (QUALITY_GATES G-LIGHT-3).
if hasattr(s, "use_nodes"):
    s.use_nodes = False

try:
    bpy.ops.file.pack_all()
except Exception as exc:
    print("pack_all:", exc)

if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
print("render settings:", name, s.render.engine, s.frame_start, s.frame_end, kind, vs.look, "->", r.filepath)
