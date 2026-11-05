"""Isolate the finished asset in a background copy, preserving the live file."""
import bpy, json, re
from pathlib import Path

OUT=Path(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\personagem')
s=max((sc for sc in bpy.data.scenes if sc.get('asset_id')=='personagem-volumetrico-rig-v1' and any(o.type=='ARMATURE' for o in sc.objects)),key=lambda sc:sc.name)
bpy.context.window.scene=s
for sc in list(bpy.data.scenes):
    if sc!=s: bpy.data.scenes.remove(sc)
owned=set(s.objects)
for ob in list(bpy.data.objects):
    if ob not in owned: bpy.data.objects.remove(ob,do_unlink=True)
used_materials={m for o in owned if o.type=='MESH' for m in o.data.materials}
for m in list(bpy.data.materials):
    if m not in used_materials: bpy.data.materials.remove(m)
for world in list(bpy.data.worlds):
    if world!=s.world: bpy.data.worlds.remove(world)
for text in list(bpy.data.texts):
    if text.name.startswith('LEIA-ME • Personagem 3D e rig'): text.use_fake_user=True
    else: bpy.data.texts.remove(text)
for im in list(bpy.data.images):
    if im.source=='FILE': bpy.data.images.remove(im)
bpy.ops.outliner.orphans_purge(do_recursive=True)
for ob in owned:
    ob.name=re.sub(r'\.\d{3}$','',ob.name)
    if ob.data: ob.data.name=re.sub(r'\.\d{3}$','',ob.data.name)
for col in s.collection.children: col.name=re.sub(r'\.\d{3}$','',col.name)
s.name='Personagem 3D • sem textura de imagem'
s.render.filepath='//personagem_3d_sem_textura.png'
rig=next(o for o in s.objects if o.type=='ARMATURE')
meshes=[o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
textures=sum(n.type=='TEX_IMAGE' for m in used_materials for n in m.node_tree.nodes)
assert textures==0
assert len(rig.data.bones)==54
assert all(mod.object==rig for ob in meshes for mod in ob.modifiers if mod.type=='ARMATURE')
assert all(g.name in rig.data.bones for ob in meshes for g in ob.vertex_groups)
assert all(d.targets[0].id==rig for ob in meshes if ob.data.shape_keys for fc in ob.data.shape_keys.animation_data.drivers for d in fc.driver.variables)
assert all(abs(v)<.000001 for p in rig.pose.bones for v in p.rotation_euler)
report={'scene':s.name,'character_meshes':len(meshes),'polygons':sum(len(o.data.polygons) for o in meshes),
        'bones':len(rig.data.bones),'image_texture_nodes':textures,
        'external_images':sum(im.source=='FILE' for im in bpy.data.images),
        'rig_modifiers_valid':True,'blink_drivers_valid':True,'neutral_pose':True}
path=OUT/'personagem_3d_sem_textura.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
report['blend']=str(path); report['bytes']=path.stat().st_size
(OUT/'arquivo_3d_final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
