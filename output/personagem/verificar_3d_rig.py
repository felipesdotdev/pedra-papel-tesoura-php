import bpy, math, json
from pathlib import Path
from mathutils import Vector

OUT=Path(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\personagem')
s=max((sc for sc in bpy.data.scenes if sc.get('asset_id')=='personagem-volumetrico-rig-v1' and any(o.type=='ARMATURE' for o in sc.objects)),key=lambda sc:sc.name)
bpy.context.window.scene=s
rig=next(o for o in s.objects if o.type=='ARMATURE')
meshes=[o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
materials={m for ob in meshes for m in ob.data.materials}
missing=[]; unweighted=0
for ob in meshes:
    valid={g.index for g in ob.vertex_groups if g.name in rig.data.bones}
    missing.extend(g.name for g in ob.vertex_groups if g.name not in rig.data.bones)
    unweighted+=sum(not any(g.group in valid and g.weight>0 for g in v.groups) for v in ob.data.vertices)

def coords(ob):
    bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=ev.to_mesh()
    points=[ev.matrix_world@v.co for v in me.vertices]
    ev.to_mesh_clear()
    return points

targets={p:next(o for o in meshes if o.name.startswith(p)) for p in ['Cabeça • volume','Mão.R • palma','Dedo.R • index','Calça.L • joelho']}
before={p:coords(o) for p,o in targets.items()}
for name,rot in {'head':(.04,.04,.16),'forearm.R':(.25,0,.08),'index.01.R':(.22,0,0),'thigh.L':(.16,0,0),'shin.L':(-.18,0,0)}.items():
    rig.pose.bones[name].rotation_euler=rot
rig['piscar_R']=1.0; rig['piscar_L']=1.0; rig.update_tag()
s.frame_set(1); bpy.context.view_layer.update()
movement={p:max((a-b).length for a,b in zip(before[p],coords(o))) for p,o in targets.items()}
blink_values={o.name:o.data.shape_keys.key_blocks['Fechar'].value for o in meshes if o.name.startswith('Piscar.')}
main=s.camera
s.cycles.samples=24; s.render.resolution_percentage=50
s.render.filepath=str(OUT/'teste_pose_rig.png')
bpy.ops.render.render(scene=s.name,write_still=True)
for pb in rig.pose.bones: pb.rotation_euler=(0,0,0)
rig['piscar_R']=0.0; rig['piscar_L']=0.0; rig.update_tag()
s.frame_set(1); bpy.context.view_layer.update()

views=[]
target=Vector((0,0,3.82)); elev=math.radians(8)
stage=next(c for c in s.collection.children if c.name.startswith('03 • ESTÚDIO'))
for label,deg,filename in [('Referencia',None,'vista_referencia_3d.png'),('Frente',0,'vista_frente_3d.png'),('Perfil',90,'vista_perfil_3d.png'),('Costas',180,'vista_costas_3d.png')]:
    if deg is None:
        cam=main
    else:
        data=main.data.copy(); data.ortho_scale=8.20
        cam=bpy.data.objects.new('Inspeção • '+label,data); stage.objects.link(cam)
        phi=math.radians(deg)
        cam.location=target+Vector((math.sin(phi)*math.cos(elev),-math.cos(phi)*math.cos(elev),math.sin(elev)))*24
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    s.camera=cam; s.render.filepath=str(OUT/filename)
    bpy.ops.render.render(scene=s.name,write_still=True)
    views.append({'label':label,'path':s.render.filepath})
s.camera=main; s.cycles.samples=64; s.render.resolution_percentage=100
s.render.filepath=str(OUT/'personagem_3d_sem_textura.png')
report={'scene':s.name,'armature':rig.name,'bones':len(rig.data.bones),'meshes':len(meshes),
        'polygons':sum(len(o.data.polygons) for o in meshes),
        'image_texture_nodes':sum(n.type=='TEX_IMAGE' for m in materials for n in m.node_tree.nodes),
        'unweighted_vertices':unweighted,'missing_bones':sorted(set(missing)),
        'pose_displacement_units':movement,'blink_values_at_closed':blink_values,'views':views,
        'rest_pose_restored':all(abs(v)<.000001 for pb in rig.pose.bones for v in pb.rotation_euler)}
assert report['image_texture_nodes']==0
assert unweighted==0 and not missing
assert all(value>.01 for value in movement.values())
assert all(value>.99 for value in blink_values.values())
assert report['rest_pose_restored']
(OUT/'validacao_3d_rig.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'personagem_3d_rig_trabalho.blend'))
result=report
