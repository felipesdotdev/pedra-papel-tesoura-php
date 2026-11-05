import bpy,os,json,struct
from mathutils import Matrix,Vector
ROOT=r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php'
OUT=os.path.join(ROOT,'output','animacoes');WEB=os.path.join(ROOT,'assets','personagem','animacoes')
s=bpy.data.scenes['PACK | Original combinado'];bpy.context.window.scene=s
r=next(o for o in s.objects if o.type=='ARMATURE');c=r.users_collection[0]
# Keep unanimated prop bounds inside the body. This prevents a web viewer from
# placing its shadow plane below the character because of scissors at the origin.
if not r.get('web_prop_origin_raised'):
    r.animation_data.action=None
    for track in r.animation_data.nla_tracks:
        track.strips[0].action=track.strips[0].action.copy()
    for ob in c.objects:
        if ob.type=='MESH' and any(g.name.startswith(('prop_','scissor')) for g in ob.vertex_groups):
            for v in ob.data.vertices:v.co.z+=2
    bpy.ops.object.select_all(action='DESELECT');r.select_set(True);bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
    rest={b.name:(b.head.copy(),b.tail.copy()) for b in r.data.edit_bones if b.name.startswith(('prop_','scissor'))}
    for name,(a,b) in rest.items():a.z+=2;b.z+=2;r.data.edit_bones[name].head=a;r.data.edit_bones[name].tail=b
    bpy.ops.object.mode_set(mode='OBJECT')
    for track in r.animation_data.nla_tracks:
        action=track.strips[0].action;slot=action.slots[0]
        for layer in action.layers:
            for strip in layer.strips:
                bag=strip.channelbag(slot)
                if bag:
                    for fc in bag.fcurves:
                        if 'pose.bones["prop_' in fc.data_path and fc.data_path.endswith('.location') and fc.array_index==1:
                            for kp in fc.keyframe_points:kp.co.y-=2;kp.handle_left.y-=2;kp.handle_right.y-=2
    r['web_prop_origin_raised']=True
# Local curvature refinement only: the approved eyes, nose, jaw and haircut stay unchanged.
old=[o for o in c.objects if 'Original Testa ' in o.name]
if old:
    ma=old[0].data.materials[0]
    for o in old:bpy.data.objects.remove(o,do_unlink=True)
    rows=[([(366,181),(425,226),(521,234),(602,234),(705,226),(762,181)],[-.50,-.78,-.83,-.83,-.78,-.50]),
          ([(367,286),(445,286),(520,286),(602,286),(680,286),(758,286)],[-.86,-.94,-.985,-.985,-.94,-.86]),
          ([(340,400),(410,404),(496,408),(630,408),(704,404),(783,400)],[-.90,-.97,-1.0,-1.0,-.97,-.90])]
    vs=[]
    for points,ds in rows:
        vs.extend(((x-561)/200*.90,d*1.05,3.12+((1360-y)/200-2.65)*.86) for (x,y),d in zip(points,ds))
    faces=[(j*6+i,j*6+i+1,(j+1)*6+i+1,(j+1)*6+i) for j in range(2) for i in range(5)]
    me=bpy.data.meshes.new('Testa curvatura local');me.from_pydata(vs,[],faces);me.materials.append(ma)
    ob=bpy.data.objects.new('COMBO | Testa com curvatura',me);c.objects.link(ob)
    group=ob.vertex_groups.new(name='head');group.add(list(range(len(vs))),1,'REPLACE');ob.parent=r
    mod=ob.modifiers.new('Rig','ARMATURE');mod.object=r
    boundary={(round(x,5),round(z,5)):y for x,y,z in vs}
    for ob in c.objects:
        if ob.type=='MESH' and 'Original ' in ob.name and len(ob.data.polygons)==1:
            for v in ob.data.vertices:
                k=(round(v.co.x,5),round(v.co.z,5))
                if k in boundary:v.co.y=boundary[k]

# Export one skinned mesh with material primitives, keeping the artist's separate parts in Blender.
vs=[];faces=[];ids=[];uvs=[];materials=[];weights=[];smooth=[]
for ob in list(c.objects):
    if ob.type!='MESH':continue
    offset=len(vs)
    for v in ob.data.vertices:
        vs.append(tuple(ob.matrix_world@v.co));weights.append([(ob.vertex_groups[g.group].name,g.weight) for g in v.groups])
    layer=ob.data.uv_layers.active
    for p in ob.data.polygons:
        ma=ob.data.materials[p.material_index]
        if ma not in materials:materials.append(ma)
        faces.append(tuple(offset+i for i in p.vertices));ids.append(materials.index(ma));smooth.append(p.use_smooth)
        uvs.extend(tuple(layer.data[li].uv) if layer else (0,0) for li in p.loop_indices)
me=bpy.data.meshes.new('Export skinned mesh');me.from_pydata(vs,[],faces);me.update()
for ma in materials:me.materials.append(ma)
uv=me.uv_layers.new(name='UVMap')
for i,coord in enumerate(uvs):uv.data[i].uv=coord
for p,i,sm in zip(me.polygons,ids,smooth):p.material_index=i;p.use_smooth=sm
ob=bpy.data.objects.new('Character',me);c.objects.link(ob);ob.parent=r
groups={}
for i,w in enumerate(weights):
    for name,value in w:
        if name not in groups:groups[name]=ob.vertex_groups.new(name=name)
        groups[name].add([i],value,'REPLACE')
mod=ob.modifiers.new('Rig','ARMATURE');mod.object=r
acts={t.name:t.strips[0].action for t in r.animation_data.nla_tracks}
r.animation_data.action=None
for t in r.animation_data.nla_tracks:t.mute=False
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);r.select_set(True);bpy.context.view_layer.objects.active=r
path=os.path.join(WEB,'personagem-combinado.glb')
bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,use_active_scene=True,export_animation_mode='NLA_TRACKS',export_animations=True,export_force_sampling=True,export_frame_range=False,export_cameras=False,export_lights=False,export_skins=True,export_def_bones=True)
bpy.data.objects.remove(ob,do_unlink=True)
for t in r.animation_data.nla_tracks:t.mute=True
r.animation_data.action=acts['Idle'];s.frame_set(1)
s.camera.location=(0,-20,5.0);s.camera.rotation_euler=(Vector((0,0,3.2))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=7.4
s.render.filepath=os.path.join(WEB,'poster-combinado.png');bpy.ops.render.render(write_still=True)
bpy.data.libraries.write(os.path.join(OUT,'personagem_combinado_animado.blend'),{s},fake_user=True,compress=True)
raw=open(path,'rb').read();n,_=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+n])
meta={'fps':30,'bones':len(r.data.bones),'deform_bones':56,'rig':r.name,'file':'personagem-combinado.glb','clips':[{'name':name,'duration':(frames-1)/30,'frames':frames,'release_frame':release} for name,frames,release in [('Idle',90,None),('Pedra',114,63),('Papel',126,67),('Tesoura',144,None)]]}
for base in (OUT,WEB):
    with open(os.path.join(base,'pack.json'),'w',encoding='utf-8') as f:json.dump(meta,f,ensure_ascii=False,indent=2)
result={'animations':[a['name'] for a in g['animations']],'bytes':len(raw),'meshes':len(g['meshes']),'materials':len(g['materials']),'bones':len(r.data.bones)}
