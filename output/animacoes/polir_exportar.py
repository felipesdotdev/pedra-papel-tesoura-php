# Run once after reconstruir_referencia.py; uses the reviewed scene explicitly.
import bpy,math,os,json,struct
from mathutils import Vector
s=bpy.data.scenes['PACK v3 | Referencia multiangulo.003'];bpy.context.window.scene=s;r=next(o for o in s.objects if o.type=='ARMATURE');c=r.users_collection[0]
for ob in c.objects:
 if ob.type!='MESH':continue
 if ob.name.startswith('REF | Laterais'):
  for v in ob.data.vertices:
   if v.co.y>0:
    z=v.co.z;t=max(0,min(1,(z-4.9)/1.2));t=t*t*(3-2*t);low=max(.35,min(1,(z-3.10)/.85));v.co.y*=low*(1-.55*t)
 if ob.name.startswith('REF | Cabelo'):
  for v in ob.data.vertices:
   if v.co.z<4.8:
    t=max(0,min(1,(v.co.z-3.45)/1.35));t=t*t*(3-2*t);fac=.62+.38*t;v.co.x*=fac;v.co.y=.10+(v.co.y-.10)*fac
floor=bpy.data.materials.new('PACK | Fundo grafite');floor.use_nodes=True
bs=next(n for n in floor.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.025,.023,.025,1);bs.inputs['Roughness'].default_value=1
for o in s.objects:
 if o.type=='MESH' and any(k in o.name for k in ('Chao estudio','Ciclorama')):o.data.materials.clear();o.data.materials.append(floor)
background=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');background.inputs[0].default_value=(.045,.04,.045,1);background.inputs[1].default_value=.5
s.view_settings.exposure=-.22
acts={t.name:t.strips[0].action for t in r.animation_data.nla_tracks}
metrics=[]
for name,a in acts.items():
 r.animation_data.action=a;mh=0;mf=0
 end={'Idle':90,'Pedra':114,'Papel':126,'Tesoura':144}[name]
 for f in range(1,end+1,2):
  s.frame_set(f);bpy.context.view_layer.update()
  for side in ['R','L']:
   mh=max(mh,(r.pose.bones['hand.'+side].head-r.pose.bones['CTRL_hand.'+side].head).length)
   mf=max(mf,(r.pose.bones['foot.'+side].head-r.pose.bones['CTRL_foot.'+side].head).length)
 metrics.append({'clip':name,'hand_error':round(mh,4),'foot_error':round(mf,4)})
r.animation_data.action=None
for t in r.animation_data.nla_tracks:t.mute=False
bpy.ops.object.select_all(action='DESELECT')
for o in c.objects:o.select_set(True)
bpy.context.view_layer.objects.active=r
p=r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\assets\personagem\animacoes\personagem-referencia.glb'
bpy.ops.export_scene.gltf(filepath=p,export_format='GLB',use_selection=True,use_active_scene=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_frame_range=False,export_cameras=False,export_lights=False,export_skins=True,export_def_bones=True)
for t in r.animation_data.nla_tracks:t.mute=True
r.animation_data.action=acts['Idle'];s.frame_set(1)
data=open(p,'rb').read();n,t=struct.unpack_from('<II',data,12);g=json.loads(data[20:20+n])
bpy.data.libraries.write(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\animacoes\personagem_referencia_animado.blend',{s},fake_user=True,compress=True)
result={'metrics':metrics,'animations':[a.get('name') for a in g.get('animations',[])],'skins':len(g.get('skins',[])),'bytes':len(data)}

