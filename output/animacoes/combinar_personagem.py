"""Preserve the approved original face; borrow the new back volume, clothing and rig.
Creates a derivative scene without mutating either source version.
"""
import bpy,os,math,json,struct
from mathutils import Vector,Matrix
ROOT=r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php'
OUT=os.path.join(ROOT,'output','animacoes');WEB=os.path.join(ROOT,'assets','personagem','animacoes')
source=bpy.data.scenes['PACK v3 | Referencia multiangulo.003']
scene=bpy.data.scenes.new('PACK | Original combinado')
bpy.context.window.scene=scene
char=bpy.data.collections.new('COMBO | Personagem e animacoes');stage=bpy.data.collections.new('COMBO | Estudio')
scene.collection.children.link(char);scene.collection.children.link(stage)
oldrig=next(o for o in source.objects if o.type=='ARMATURE')
oldchar=oldrig.users_collection[0];mapping={}
for old in source.objects:
    if old not in list(oldchar.objects) and old.type not in ('MESH','CAMERA','LIGHT'):continue
    ob=old.copy();ob.data=old.data.copy() if old.data else None;ob.name='COMBO | '+old.name
    (char if old in list(oldchar.objects) else stage).objects.link(ob);mapping[old]=ob
rig=mapping[oldrig];rig.name='RPS_Rig_Combinado'
for old,ob in mapping.items():
    if old.parent in mapping:ob.parent=mapping[old.parent]
    for mod in ob.modifiers:
        if mod.type=='ARMATURE':mod.object=rig
    if ob.type=='ARMATURE':
        for pb in ob.pose.bones:
            for con in pb.constraints:
                if getattr(con,'target',None)==oldrig:con.target=rig
                if hasattr(con,'pole_target') and con.pole_target==oldrig:con.pole_target=rig
scene.camera=mapping[source.camera];scene.world=source.world.copy()
for ob in list(char.objects):
    if ob.type=='MESH' and any(g.name=='head' for g in ob.vertex_groups):bpy.data.objects.remove(ob,do_unlink=True)

def bind(ob):
    vg=ob.vertex_groups.new(name='head');vg.add(list(range(len(ob.data.vertices))),1,'REPLACE')
    ob.parent=rig;ob.matrix_parent_inverse=Matrix.Identity(4)
    m=ob.modifiers.new('Rig | cabeca original preservada','ARMATURE');m.object=rig
def mesh(name,vs,fs,mats,ids=None):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.validate()
    ob=bpy.data.objects.new('COMBO | '+name,me);char.objects.link(ob)
    for m in mats:me.materials.append(m)
    if ids:
        for p,i in zip(me.polygons,ids):p.material_index=i
    bind(ob);return ob
def project(ob):
    uv=ob.data.uv_layers.new(name='FaceUV')
    for p in ob.data.polygons:
        for li in p.loop_indices:
            v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/2.6+.5,(v.z-3.0)/3.4)

original=bpy.data.scenes.get('Personagem - referencia low poly.001')
if not original:
    with bpy.data.libraries.load(os.path.join(ROOT,'output','personagem','personagem.blend'),link=False) as (a,b):b.scenes=['Personagem - referencia low poly.001']
    original=b.scenes[0]
original_char=next(c for c in original.collection.children if any(o.name.startswith('Testa central') for o in c.objects))
body=('Solado','Tenis','Biqueira','Perna','Cintura','Braco','Mao','Tronco','Camiseta','Manga','Pescoco')
lower=('Maxilar','Queixo','Rosto plano','Tempora')
newhair=next(o for o in oldchar.objects if o.name.startswith('REF | Cabelo'))
hairmats=list(newhair.data.materials)
beard=next(o for o in oldchar.objects if o.name.startswith('REF | Rosto')).data.materials[0].copy()
beard.name='COMBO | Barba discreta sobre rosto antigo'
# The face keeps the exact source topology, eye construction, brow shapes and nose.
for old in original_char.objects:
    if old.type!='MESH' or old.name.startswith(body) or old.name in ('Cabeca volume','Cabelo volume posterior','Cabelo calota posterior'):continue
    ob=old.copy();ob.data=old.data.copy();ob.animation_data_clear();ob.name='COMBO | Original '+old.name
    char.objects.link(ob);ob.parent=None;ob.modifiers.clear();ob.vertex_groups.clear();ob.matrix_world=Matrix.Identity(4)
    for v in ob.data.vertices:
        v.co.x*=.90;v.co.z=3.12+(v.co.z-2.65)*.86
        v.co.y*=1.05
        if old.name.startswith(('Nariz','Aba nasal')):v.co.y*=1.06
        if old.name.startswith(('Labio','Boca')) and abs(v.co.x)>.23:v.co.z+=.012
    if old.name.startswith(lower):
        ob.data.materials.clear();ob.data.materials.append(beard);project(ob)
    bind(ob)

# A rounded rear cranium replaces the original extruded back wall, while the front is unchanged.
shape=[(366,181),(521,234),(602,234),(762,181),(832,258),(829,400),(840,706),(752,800),(625,830),(497,830),(371,802),(281,707),(291,399),(291,258)]
boundary=[Vector(((px-561)/200*.90,-.504,3.12+((1360-py)/200-2.65)*.86)) for px,py in shape]
center=Vector((0,0,4.80));rings=[]
for sx,sz,y in [(1,1,-.504),(1.045,.99,.23),(.84,.94,.92),(.37,.70,1.22)]:
    rings.append([(p.x*sx,y,center.z+(p.z-center.z)*sz) for p in boundary])
vs=[p for ring in rings for p in ring];n=len(shape);faces=[tuple(reversed(range(n)))];ids=[0]
skin=next(o for o in original_char.objects if o.name=='Cabeca volume').data.materials[0]
for j in range(3):
    for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i));ids.append(1 if j>0 else 0)
faces.append(tuple(3*n+i for i in range(n)));ids.append(1)
mesh('Cranio com volume arredondado',vs,faces,[skin,hairmats[3]],ids)

# Borrow only the back/side cap from the new version; keep the old frontal hairstyle.
vs=[];faces=[];ids=[]
for p in newhair.data.polygons:
    center=sum((newhair.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
    if center.y<.04:continue
    off=len(vs)
    for i in p.vertices:
        v=newhair.data.vertices[i].co.copy();v.x*=1.18;v.y*=1.08;v.z=3.12+(v.z-3.12)*1.08;vs.append(tuple(v))
    faces.append(tuple(off+i for i in range(len(p.vertices))));ids.append(p.material_index)
mesh('Cabelo nuca e laterais volumetricos',vs,faces,hairmats,ids)

# Retain the new eyeglasses at the original eyes' location; no new smile or eyebrow design.
for old in oldchar.objects:
    if old.type=='MESH' and old.name.startswith('REF | Oculos'):
        ob=old.copy();ob.data=old.data.copy();ob.animation_data_clear();ob.name='COMBO | '+old.name
        char.objects.link(ob);ob.parent=None;ob.modifiers.clear();ob.vertex_groups.clear();ob.matrix_world=Matrix.Identity(4)
        for v in ob.data.vertices:v.co.x*=1.10;v.co.z-=.015;v.co.y-=.035
        bind(ob)

actions={t.name:t.strips[0].action for t in rig.animation_data.nla_tracks}
for t in rig.animation_data.nla_tracks:t.mute=True
rig.animation_data.action=actions['Idle'];scene.frame_start=1;scene.frame_end=144;scene.frame_set(1)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.fps=30
scene.render.resolution_x=760;scene.render.resolution_y=900;scene.render.resolution_percentage=70;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=-.22
scene.camera.location=(0,-20,5.0);scene.camera.rotation_euler=(Vector((0,0,3.2))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=7.4
scene.render.filepath=os.path.join(OUT,'combinado_frente.png');bpy.ops.render.render(write_still=True)
bpy.data.libraries.write(os.path.join(OUT,'personagem_combinado_animado.blend'),{scene},fake_user=True,compress=True)
result={'scene':scene.name,'rig':rig.name,'objects':len(char.objects),'preview':scene.render.filepath}
