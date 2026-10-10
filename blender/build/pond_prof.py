"""Perf probe (render-lock only): times f172 full-res under toggles."""
import bpy, time
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1920, 1080, 100
s.frame_set(172)
out = '/tmp/claude-501/pond_prof.png'
def r(label):
    s.render.filepath = out
    t = time.time(); bpy.ops.render.render(write_still=True); print('PROF', label, round(time.time() - t, 1), flush=True)
r('warmup')
r('baseline')
vis = {}
def hide(names, label):
    for o in s.objects:
        if any(o.name.startswith(n) for n in names):
            vis[o.name] = o.hide_render; o.hide_render = True
    r(label)
s.eevee.use_volumetric_shadows = False
w = bpy.data.objects['A-POND-WATER']; m = w.data.materials[0]
out_n = [n for n in m.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
for l in list(out_n.inputs['Volume'].links): m.node_tree.links.remove(l)
r('no volume')
s.eevee.use_raytracing = False; r('no raytrace')
hide(['grove', 'clump', 'scrub'], 'no far veg')
md = bpy.data.objects['A-ENV-PONDS'].modifiers.get('grass_scatter'); md.show_render = False; r('no grass')
hide(['palm_', 'tree_', 'shrub_'], 'no near veg')
s.eevee.use_shadows = False; r('no shadows')
