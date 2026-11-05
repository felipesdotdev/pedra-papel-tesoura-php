import bpy, json, re
from pathlib import Path

OUT=Path(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\personagem')
s=next(sc for sc in bpy.data.scenes if sc.get('calvicie_revisada'))
bpy.context.window.scene=s
for sc in list(bpy.data.scenes):
    if sc!=s: bpy.data.scenes.remove(sc)
owned=set(s.objects)
for ob in list(bpy.data.objects):
    if ob not in owned: bpy.data.objects.remove(ob,do_unlink=True)
used={m for ob in owned if ob.type=='MESH' for m in ob.data.materials}
for m in list(bpy.data.materials):
    if m not in used: bpy.data.materials.remove(m)
for w in list(bpy.data.worlds):
    if w!=s.world: bpy.data.worlds.remove(w)
for im in list(bpy.data.images):
    if im.source=='FILE': bpy.data.images.remove(im)
for ob in owned:
    for key in ('cabelo_original','cabeca_original'):
        if key in ob: del ob[key]
owned_mesh_data={ob.data for ob in owned if ob.type=='MESH'}
for me in list(bpy.data.meshes):
    if me.name.startswith('BASE APROVADA') and me not in owned_mesh_data: bpy.data.meshes.remove(me)
for t in list(bpy.data.texts):
    if t.name.startswith('LEIA-ME • Personagem 3D e rig'):
        t.use_fake_user=True
        t.write('\nCALVÍCIE REVISADA\nEntradas e menor densidade no topo ajustadas pela foto real.\nO couro cabeludo é uma extensão contínua da cabeça. Os fios curtos são geometria, sem textura fotográfica. O rosto abaixo da testa, o restante do corpo e o rig foram preservados.\n')
    else: bpy.data.texts.remove(t)
bpy.ops.outliner.orphans_purge(do_recursive=True)
owned=set(s.objects)
for ob in owned:
    ob.name=re.sub(r'\.\d{3}$','',ob.name)
    if ob.data: ob.data.name=re.sub(r'\.\d{3}$','',ob.data.name)
    if ob.name.startswith('Cabeça • volume'): ob.data.name='Cabeça • volume e couro cabeludo'
for col in s.collection.children: col.name=re.sub(r'\.\d{3}$','',col.name)
s.name='Personagem 3D • calvície ajustada'
s.render.filepath='//personagem_3d_calvicie.png'
rig=next(o for o in s.objects if o.type=='ARMATURE')
meshes=[o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
assert len(rig.data.bones)==54
assert all(mod.object==rig for ob in meshes for mod in ob.modifiers if mod.type=='ARMATURE')
assert all(abs(sum(g.weight for g in v.groups)-1)<.0001 for ob in meshes for v in ob.data.vertices)
texture_count=sum(n.type=='TEX_IMAGE' for m in used for n in m.node_tree.nodes)
assert texture_count==0
path=OUT/'personagem_3d_calvicie.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
report={'blend':str(path),'bytes':path.stat().st_size,'bones':len(rig.data.bones),
        'character_meshes':len(meshes),'polygons':sum(len(o.data.polygons) for o in meshes),
        'image_textures':texture_count,'external_images':sum(i.source=='FILE' for i in bpy.data.images)}
(OUT/'arquivo_calvicie_final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
