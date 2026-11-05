"""Build an isolated, editable IK character rig and a portable RPS animation pack.
Run in Blender through MCP. Source meshes/scenes and the static web GLB are preserved.
Coordinates: +Z up, -Y forward. Authoring 30 fps, sampled glTF deformation.
"""
import bpy, bmesh, math, random, os, json, struct
from mathutils import Vector, Matrix, Quaternion, Euler
ROOT=r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php'
OUT=os.path.join(ROOT,'output','animacoes')
WEB=os.path.join(ROOT,'assets','personagem','animacoes')
os.makedirs(OUT,exist_ok=True);os.makedirs(WEB,exist_ok=True)
source=bpy.data.scenes.get('Personagem - referencia low poly.001')
if source is None:
    with bpy.data.libraries.load(os.path.join(ROOT,'output','personagem','personagem.blend'),link=False) as (src,dst):
        dst.scenes=['Personagem - referencia low poly.001']
    source=dst.scenes[0]
source_char=next(c for c in source.collection.children if any(o.name.startswith('Testa central') for o in c.objects))
scene=bpy.data.scenes.new('PACK | Pedra Papel Tesoura')
bpy.context.window.scene=scene
char=bpy.data.collections.new('PACK | Personagem e objetos')
stage=bpy.data.collections.new('PACK | Estudio')
scene.collection.children.link(char);scene.collection.children.link(stage)
objects={}
for old in source.objects:
    ob=old.copy();ob.data=old.data.copy() if old.data else None;ob.animation_data_clear()
    (char if old in list(source_char.objects) else stage).objects.link(ob)
    ob.name='PACK | '+old.name;objects[old.name]=ob
scene.camera=objects[source.camera.name];scene.world=source.world.copy()
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=720;scene.render.resolution_y=900;scene.render.resolution_percentage=60
scene.render.image_settings.file_format='PNG';scene.render.fps=30
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=-.35
cam=scene.camera;cam.location=(8,-21,8);cam.rotation_euler=(Vector((-.15,-.2,3.15))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=8.6

def material(name,rgb,rough=.85,metal=0):
    ma=bpy.data.materials.new('PACK | '+name);ma.use_nodes=True;ma.diffuse_color=(*rgb,1)
    p=next(n for n in ma.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Specular IOR Level'].default_value=.18
    return ma
skin=objects['Braco E'].data.materials[0]
cloth=objects['Tronco camiseta'].data.materials[0]
rockmats=[material('Pedra cinza',(.17,.19,.18)),material('Pedra plano claro',(.24,.265,.25)),material('Pedra plano escuro',(.115,.135,.125))]
papermats=[material('Papel branco',(.89,.88,.81)),material('Papel dobras',(.64,.68,.68)),material('Papel linha dobra',(.75,.78,.75))]
steel=material('Tesoura laminas de aco',(.51,.55,.57),.25,.7)
edge=material('Tesoura fio claro',(.77,.80,.79),.21,.75)
handle=material('Tesoura aros azul petroleo',(.025,.16,.19),.6)
pocketmat=material('Bolso costura grafite',(.075,.077,.08))

def mesh(name,verts,faces,mats,indices=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();me.validate()
    ob=bpy.data.objects.new(name,me);char.objects.link(ob)
    for m in mats:me.materials.append(m)
    if indices:
        for p,i in zip(me.polygons,indices):p.material_index=i
    return ob
def box(name,center,dims,ma,bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    ob=bpy.context.object;ob.name='PACK | '+name
    for c in list(ob.users_collection):c.objects.unlink(ob)
    char.objects.link(ob);ob.scale=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=ob.modifiers.new('Cantos facetados','BEVEL');mod.width=bevel;mod.segments=1
        bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.data.materials.append(ma)
    # Mesh coordinates in world space simplify weights and bind matrices.
    for v in ob.data.vertices:v.co=ob.matrix_world@v.co
    ob.matrix_world=Matrix.Identity(4)
    return ob
def segment(name,a,b,r,ma):
    a,b=Vector(a),Vector(b);t=(b-a).normalized();u=t.cross(Vector((0,1,0)))
    if u.length<.01:u=t.cross(Vector((1,0,0)))
    u.normalize();v=t.cross(u).normalized();verts=[]
    for center,radius in [(a,r*.92),(a.lerp(b,.18),r),(a.lerp(b,.82),r),(b,r*.88)]:
        verts.extend(tuple(center+radius*(u*math.cos(i*math.pi/3)+v*math.sin(i*math.pi/3))) for i in range(6))
    faces=[tuple(reversed(range(6)))]
    for j in range(3):
        faces.extend((j*6+i,j*6+(i+1)%6,(j+1)*6+(i+1)%6,(j+1)*6+i) for i in range(6))
    faces.append(tuple(18+i for i in range(6)))
    return mesh('PACK | '+name,verts,faces,[ma])
def merge(name,obs):
    vs=[];fs=[];mats=[];ids=[]
    for ob in obs:
        off=len(vs);vs.extend(tuple(ob.matrix_world@v.co) for v in ob.data.vertices)
        for p in ob.data.polygons:
            ma=ob.data.materials[p.material_index]
            if ma not in mats:mats.append(ma)
            fs.append(tuple(off+i for i in p.vertices));ids.append(mats.index(ma))
    result=mesh(name,vs,fs,mats,ids)
    for ob in obs:bpy.data.objects.remove(ob,do_unlink=True)
    return result
def slices(ob,zs):
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    for z in zs:
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,z),plane_no=(0,0,1),clear_inner=False,clear_outer=False)
    bm.to_mesh(ob.data);bm.free();ob.data.update()

# An actual hierarchy with independently articulated fingers and IK poles.
ad=bpy.data.armatures.new('RPS | Esqueleto');rig=bpy.data.objects.new('RPS_Rig',ad);char.objects.link(rig);rig.show_in_front=True
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
rest={}
def bone(name,a,b,parent=None,deform=True,connect=False):
    bo=ad.edit_bones.new(name);bo.head=a;bo.tail=b;bo.use_deform=deform
    if parent:bo.parent=ad.edit_bones[parent];bo.use_connect=connect
    rest[name]=(Vector(a),Vector(b));return bo
bone('root',(0,0,0),(0,0,.35),deform=False)
bone('pelvis',(0,.04,1.18),(0,.04,1.50),'root')
bone('spine',(0,.04,1.50),(0,.04,2.05),'pelvis',connect=True)
bone('chest',(0,.04,2.05),(0,.04,2.50),'spine',connect=True)
bone('neck',(0,.04,2.50),(0,.04,2.80),'chest',connect=True)
bone('head',(0,.04,2.80),(0,.04,4.7),'neck',connect=True)
for side,sgn in [('R',-1),('L',1)]:
    shoulder=(sgn*.73,.04,2.38);elbow=(sgn*.98,-.115,1.88);wrist=(sgn*1.07,-.03,1.43);palm=(sgn*1.07,-.075,1.18)
    bone('clavicle.'+side,(0,.04,2.38),shoulder,'chest')
    bone('upper_arm.'+side,shoulder,elbow,'clavicle.'+side)
    bone('forearm.'+side,elbow,wrist,'upper_arm.'+side,connect=True)
    bone('hand.'+side,wrist,palm,'forearm.'+side,connect=True)
    hip=(sgn*.42,.04,1.18);knee=(sgn*.50,-.085,.76);ankle=(sgn*.55,.025,.34);toe=(sgn*.55,-.46,.18)
    bone('thigh.'+side,hip,knee,'pelvis');bone('shin.'+side,knee,ankle,'thigh.'+side,connect=True)
    bone('foot.'+side,ankle,toe,'shin.'+side,connect=True);bone('toe.'+side,toe,(sgn*.55,-.65,.17),'foot.'+side,connect=True)
    bone('CTRL_hand.'+side,wrist,palm,'root',False)
    bone('CTRL_foot.'+side,ankle,toe,'root',False)
    for name,a,b,end in [('arm',shoulder,elbow,wrist),('leg',hip,knee,ankle)]:
        a,b,end=Vector(a),Vector(b),Vector(end);axis=(end-a).normalized();projection=a+axis*(b-a).dot(axis)
        pole=b+(b-projection).normalized()*1.4
        bone('POLE_'+name+'.'+side,pole,pole+Vector((0,0,.2)),'root',False)
    for i,finger in enumerate(('index','middle','ring','pinky')):
        x=sgn*1.07+(i-1.5)*.116
        points=[(x,-.22,1.20),(x,-.23,1.065),(x,-.235,.955),(x,-.24,.88)]
        if finger=='pinky':points=[(px,py,pz+.045*j/3) for j,(px,py,pz) in enumerate(points)]
        for j in range(3):bone(f'{finger}_{j+1}.{side}',points[j],points[j+1],'hand.'+side if j==0 else f'{finger}_{j}.{side}',connect=j>0)
    points=[(sgn*.86,-.07,1.36),(sgn*.79,-.19,1.23),(sgn*.81,-.31,1.14),(sgn*.90,-.36,1.13)]
    for j in range(3):bone(f'thumb_{j+1}.{side}',points[j],points[j+1],'hand.'+side if j==0 else f'thumb_{j}.{side}',connect=j>0)
for name in ('prop_rock','prop_plane','prop_scissors'):
    bone(name,(0,0,0),(0,0,.3),'root')
bone('scissor_A',(0,0,0),(0,0,.6),'prop_scissors')
bone('scissor_B',(0,0,0),(0,0,.6),'prop_scissors')
bpy.ops.object.mode_set(mode='OBJECT')
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
for name in ('pelvis','spine','chest','neck','head'):ad.bones[name].color.palette='THEME04'
for bo in ad.bones:
    if bo.name.startswith(('CTRL','POLE')):bo.color.palette='THEME03'
deform=ad.collections.new('Deformacao | corpo e dedos');controls=ad.collections.new('Controles IK');props=ad.collections.new('Objetos de cena')
for bo in ad.bones:(controls if bo.name.startswith(('CTRL','POLE')) else props if bo.name.startswith(('prop_','scissor')) else deform).assign(bo)
for side in ('R','L'):
    for limb,tip,ctrl in [('arm','forearm','hand'),('leg','shin','foot')]:
        pb=rig.pose.bones[tip+'.'+side];con=pb.constraints.new('IK');con.name='IK 2 segmentos | '+limb;con.target=rig;con.subtarget='CTRL_'+ctrl+'.'+side;con.chain_count=2;con.use_stretch=False
        con.pole_target=rig;con.pole_subtarget='POLE_'+limb+'.'+side
        # Calibrate pole twist against the measured neutral elbow/knee, avoiding a guessed roll.
        first='upper_arm' if limb=='arm' else 'thigh';target=rest[tip+'.'+side][0];best=(1e9,0)
        for k in range(48):
            con.pole_angle=-math.pi+2*math.pi*k/48;bpy.context.view_layer.update()
            error=(rig.pose.bones[tip+'.'+side].head-target).length
            if error<best[0]:best=(error,con.pole_angle)
        con.pole_angle=best[1]
        for k in range(-8,9):
            con.pole_angle=best[1]+k*.008;bpy.context.view_layer.update();error=(rig.pose.bones[tip+'.'+side].head-target).length
            if error<best[0]:best=(error,con.pole_angle)
        con.pole_angle=best[1]
    for which in ('hand','foot'):
        con=rig.pose.bones[which+'.'+side].constraints.new('COPY_ROTATION');con.name='Orientacao do controle IK';con.target=rig;con.subtarget='CTRL_'+which+'.'+side;con.target_space='WORLD';con.owner_space='WORLD'

def bind(ob,weights):
    groups={}
    for v in ob.data.vertices:
        pairs=weights(v.co) if callable(weights) else [(weights,1)]
        for name,w in pairs:
            if w<=1e-7:continue
            if name not in groups:groups[name]=ob.vertex_groups.new(name=name)
            groups[name].add([v.index],w,'REPLACE')
    mod=ob.modifiers.new('RPS | skinning normalizado','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
    ob.parent=rig;ob.matrix_parent_inverse=Matrix.Identity(4)
def smooth(v):v=max(0,min(1,v));return v*v*(3-2*v)
def torso_weights(v):
    if v.z<1.6:
        t=smooth((v.z-1.25)/.35);return [('pelvis',1-t),('spine',t)]
    t=smooth((v.z-1.78)/.55);return [('spine',1-t),('chest',t)]

# Rigid facial layers move together; bending happens at anatomically meaningful joints.
bodyprefix=('Solado','Tenis','Biqueira','Perna','Cintura','Braco','Mao','Tronco','Camiseta','Manga','Pescoco')
headobs=[ob for name,ob in objects.items() if ob.type=='MESH' and ob in list(char.objects) and not name.startswith(bodyprefix)]
head=merge('PACK | Cabeca unificada',headobs);bind(head,'head')
for name,ob in list(objects.items()):
    if not name.startswith(bodyprefix):continue
    if ob.type!='MESH' or name not in source_char.objects:continue
    if name.startswith('Mao'):
        bpy.data.objects.remove(ob,do_unlink=True);continue
    if name.startswith(('Tronco','Camiseta')):
        slices(ob,[1.42,1.65,1.90,2.13,2.36]);bind(ob,torso_weights)
    elif name=='Cintura':bind(ob,'pelvis')
    elif name=='Pescoco':
        bind(ob,lambda v:[('neck',1-smooth((v.z-2.64)/.14)),('head',smooth((v.z-2.64)/.14))])
    elif name.startswith('Manga'):
        side='R' if name.endswith('E') else 'L';slices(ob,[2.0,2.2,2.4])
        bind(ob,lambda v,side=side:[('chest',1-smooth((abs(v.x)-.55)/.46)),('upper_arm.'+side,smooth((abs(v.x)-.55)/.46))])
    elif name.startswith('Braco'):
        side='R' if name.endswith('E') else 'L';slices(ob,[1.42,1.56,1.7,1.82,1.94,2.06])
        bind(ob,lambda v,side=side:[('forearm.'+side,1-smooth((v.z-1.77)/.23)),('upper_arm.'+side,smooth((v.z-1.77)/.23))])
    elif name.startswith('Perna'):
        side='R' if name.endswith('E') else 'L';slices(ob,[.42,.54,.66,.78,.90,1.04,1.17])
        bind(ob,lambda v,side=side:[('shin.'+side,1-smooth((v.z-.65)/.23)),('thigh.'+side,smooth((v.z-.65)/.23))])
    elif name.startswith(('Solado','Tenis','Biqueira')):
        bind(ob,'foot.'+('R' if name.endswith('E') else 'L'))

# Segmented low-poly hands: a palm and fifteen independently weighted phalanges per hand.
for side,sign in [('R',-1),('L',1)]:
    palm=box('Palma '+side,(sign*1.07,-.01,1.30),(.47,.47,.39),skin,.065);bind(palm,'hand.'+side)
    for finger in ('index','middle','ring','pinky','thumb'):
        for j in range(1,4):
            bn=f'{finger}_{j}.{side}';a,b=rest[bn];ob=segment(bn,a,b,.060 if finger!='thumb' else .075,skin);bind(ob,bn)

# Pocket stitching remains on the pants when the body rotates.
for side,sign in [('R',-1),('L',1)]:
    seam=segment('Bolso abertura '+side,(sign*.71,-.263,1.17),(sign*.38,-.263,1.08),.012,pocketmat);bind(seam,'pelvis')

# Three distinct props; all are driven by bones inside the same exported clip.
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.205,location=(0,0,0))
rock=bpy.context.object;rock.name='PACK | Pedra facetada'
for c in list(rock.users_collection):c.objects.unlink(rock)
char.objects.link(rock)
for ma in rockmats:rock.data.materials.append(ma)
for p in rock.data.polygons:p.material_index=p.index%3
bind(rock,'prop_rock')
plane=mesh('PACK | Aviao dobrado',[(0,-.65,.015),(-.55,.28,0),(-.12,.17,.025),(0,.44,.11),(.12,.17,.025),(.55,.28,0),(0,-.48,.16),(-.105,.44,.018),(.105,.44,.018)],[(0,1,2,6),(0,6,4,5),(6,2,7,3),(6,3,8,4),(1,7,2),(4,8,5),(0,5,4,8,3,7,2,1)],papermats,[0,0,1,2,2,2,1]);bind(plane,'prop_plane')
def hoop(name,cx,cz,bone_name):
    vs=[];fs=[]
    for i in range(16):
        a=2*math.pi*i/16
        for j in range(6):
            b=2*math.pi*j/6
            vs.append((cx+(.14+.032*math.cos(b))*math.cos(a),.032*math.sin(b),cz+(.19+.032*math.cos(b))*math.sin(a)))
    for i in range(16):
        for j in range(6):fs.append((i*6+j,((i+1)%16)*6+j,((i+1)%16)*6+(j+1)%6,i*6+(j+1)%6))
    ob=mesh(name,vs,fs,[handle]);bind(ob,bone_name)
for label,sgn in [('A',-1),('B',1)]:
    bn='scissor_'+label
    outline=[(sgn*.02,0,-.10),(sgn*.075,0,.02),(sgn*.095,0,.49),(sgn*.035,0,.70),(-sgn*.02,0,.60),(-sgn*.025,0,.05)]
    vs=[(x,y+off,z) for off in (-.018,.018) for x,y,z in outline];n=len(outline)
    ob=mesh('PACK | Tesoura lamina '+label,vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],[steel,edge],[0,1]+[1]*n);bind(ob,bn)
    ob=segment('Tesoura haste '+label,(sgn*.02,0,.04),(sgn*.13,0,-.24),.035,steel);bind(ob,bn)
    hoop('PACK | Tesoura aro '+label,sgn*.12,-.32,bn)
hub=box('Tesoura parafuso',(0,-.027,.02),(.11,.07,.11),steel,.025);bind(hub,'prop_scissors')

# Constant-velocity continuous Hermite paths with gentle tangent damping.
def curve(keys,f):
    if f<=keys[0][0]:return keys[0][1]
    if f>=keys[-1][0]:return keys[-1][1]
    for i in range(len(keys)-1):
        fa,a=keys[i];fb,b=keys[i+1]
        if fa<=f<=fb:
            t=(f-fa)/(fb-fa);dt=fb-fa
            m0=0 if i==0 else .65*(b-keys[i-1][1])/(fb-keys[i-1][0])
            m1=0 if i+2==len(keys) else .65*(keys[i+2][1]-a)/(keys[i+2][0]-fa)
            return (2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*dt*m0+(-2*t**3+3*t*t)*b+(t**3-t*t)*dt*m1
def path(keys,f):return Vector([curve([(fr,p[i]) for fr,p in keys],f) for i in range(len(keys[0][1]))])
def q(degrees):return Euler(tuple(math.radians(v) for v in degrees),'XYZ').to_quaternion()
def key(pb,frame):
    pb.keyframe_insert('location',frame=frame,group=pb.name);pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name);pb.keyframe_insert('scale',frame=frame,group=pb.name)
def control(name,pos,rot=(0,0,0)):
    pb=rig.pose.bones[name];m=pb.bone.matrix_local.copy();m.translation=Vector((0,0,0))
    pb.matrix=Matrix.Translation(Vector(pos))@q(rot).to_matrix().to_4x4()@m
def prop(name,pos,rotation,scale=1):
    pb=rig.pose.bones[name];m=pb.bone.matrix_local.copy();m.translation=Vector((0,0,0))
    pb.matrix=Matrix.Translation(pos)@rotation.to_matrix().to_4x4()@m;pb.scale=(scale,)*3
neutralR=tuple(rest['hand.R'][0]);neutralL=tuple(rest['hand.L'][0])
phases={
 'Pedra':{'end':114,'release':63,'pull':(19,33),'wrist':[(1,neutralR),(19,(-.65,-.49,1.41)),(32,(-1.06,-.63,1.94)),(46,(-1.65,-.03,2.64)),(54,(-1.65,-.02,2.66)),(63,(-1.22,-.94,2.55)),(75,(-.64,-.85,1.94)),(91,(-1.20,-.28,1.57)),(114,neutralR)],'rotation':[(1,(0,0,0)),(24,(20,-12,15)),(46,(-38,-30,-5)),(54,(-40,-30,-5)),(63,(35,-18,25)),(77,(45,6,35)),(114,(0,0,0))], 'body':[(1,(0,0,0,0,0,0)),(20,(.10,-.06,7,9,-3,9)),(44,(.12,-.055,-3,21,-4,-4)),(54,(.14,-.07,-4,24,-5,-6)),(65,(-.10,-.09,12,-19,5,-4)),(78,(-.12,-.07,7,-14,3,-1)),(96,(.03,-.025,-2,4,-1,-2)),(114,(0,0,0,0,0,0))]},
 'Papel':{'end':126,'release':67,'pull':(18,34),'wrist':[(1,neutralR),(18,(-.68,-.46,1.42)),(34,(-1.05,-.65,2.08)),(50,(-1.48,-.30,2.56)),(57,(-1.52,-.30,2.57)),(67,(-1.23,-.99,2.59)),(81,(-1.04,-.86,2.18)),(102,(-1.22,-.24,1.61)),(126,neutralR)],'rotation':[(1,(0,0,0)),(34,(-35,-15,-4)),(54,(-40,-25,-5)),(67,(-18,-14,2)),(82,(5,10,20)),(126,(0,0,0))], 'body':[(1,(0,0,0,0,0,0)),(19,(.08,-.055,6,7,-2,8)),(42,(.11,-.04,-2,15,-3,-2)),(56,(.11,-.06,-3,17,-3,-5)),(69,(-.08,-.07,8,-13,3,-5)),(86,(-.09,-.04,4,-9,2,-4)),(109,(.02,-.018,-1,2,-1,-1)),(126,(0,0,0,0,0,0))]},
 'Tesoura':{'end':144,'release':999,'pull':(22,40),'wrist':[(1,neutralR),(22,(-.65,-.49,1.4)),(40,(-1.19,-.60,1.98)),(55,(-1.52,-.73,2.39)),(66,(-1.48,-.94,2.43)),(76,(-1.47,-.80,2.41)),(85,(-1.48,-.97,2.45)),(95,(-1.47,-.80,2.41)),(104,(-1.48,-.98,2.43)),(115,(-1.06,-.65,1.98)),(127,(-.65,-.47,1.4)),(144,neutralR)],'rotation':[(1,(0,0,0)),(24,(10,-8,5)),(44,(8,-10,-2)),(56,(2,-8,-8)),(104,(0,-12,-10)),(127,(10,-8,5)),(144,(0,0,0))], 'body':[(1,(0,0,0,0,0,0)),(22,(.09,-.06,6,9,-2,9)),(52,(-.065,-.05,3,-8,2,-6)),(66,(-.09,-.075,6,-12,3,-6)),(76,(-.065,-.045,3,-8,2,-5)),(85,(-.10,-.075,6,-12,3,-6)),(95,(-.065,-.045,3,-8,2,-5)),(104,(-.09,-.075,6,-12,3,-6)),(127,(.08,-.055,6,8,-2,8)),(144,(0,0,0,0,0,0))]}
}
actions={};clips=[]
all_names=list(rig.pose.bones.keys())
for clip in ('Idle','Pedra','Papel','Tesoura'):
    action=bpy.data.actions.new(clip);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action
    # The low-poly fingers stay softly closed in the neutral pose.
    end=90 if clip=='Idle' else phases[clip]['end'];release_matrix=None;release_pos=None
    for frame in range(1,end+1):
        scene.frame_set(frame)
        for pb in rig.pose.bones:pb.location=(0,0,0);pb.rotation_quaternion=Quaternion();pb.scale=(1,1,1)
        if clip=='Idle':
            t=(frame-1)/(end-1);breath=math.sin(2*math.pi*t)
            body=Vector((.008*math.sin(2*math.pi*t),-.008*(1-math.cos(2*math.pi*t)),.7*breath,.6*breath,.4*breath,-.5*breath))
            wristR=Vector(neutralR)+Vector((0,-.008*breath,.004*breath));rotR=Vector((0,0,0));wristL=Vector(neutralL)+Vector((0,.006*breath,.004*breath));activity=0
        else:
            cfg=phases[clip];body=path(cfg['body'],frame);wristR=path(cfg['wrist'],frame);rotR=path(cfg['rotation'],frame)
            activity=math.sin(math.pi*(frame-1)/(end-1))**2
            wristL=Vector(neutralL)+Vector((.25*activity,-.22*activity,.20*activity))
        rig.pose.bones['pelvis'].location=(body[0],body[1],0) # bone-local Y points up
        rig.pose.bones['pelvis'].rotation_quaternion=q((0,body[3]*.22,body[4]*.25))
        rig.pose.bones['spine'].rotation_quaternion=q((body[2]*.5,body[3]*.40,body[4]*.45))
        rig.pose.bones['chest'].rotation_quaternion=q((body[2]*.5,body[3]*.38,body[4]*.30))
        rig.pose.bones['neck'].rotation_quaternion=q((body[5]*.45,-body[3]*.18,0))
        rig.pose.bones['head'].rotation_quaternion=q((body[5]*.55,-body[3]*.22,-body[4]*.25))
        for side,wrist,rot in [('R',wristR,rotR),('L',wristL,Vector((4*activity,0,-8*activity)))]:
            control('CTRL_hand.'+side,wrist,rot)
            base=rest['foot.'+side][0].copy();heel=0
            if clip in ('Pedra','Papel'):
                heel=curve([(1,0),(43,.012),(56,.06),(69,.04),(88,0),(end,0)],frame) if side=='R' else 0
            base.z+=heel;control('CTRL_foot.'+side,base,(heel*120,0,0))
        grip=.80
        if clip in ('Pedra','Papel'):
            grip=curve([(1,.80),(18,.85),(36,1),(phases[clip]['release']-3,1),(phases[clip]['release']+4,.08),(phases[clip]['release']+15,.20),(end,.80)],frame)
        for side in ('R','L'):
            for i,finger in enumerate(('index','middle','ring','pinky')):
                g=grip if side=='R' else .72
                for j in range(1,4):rig.pose.bones[f'{finger}_{j}.{side}'].rotation_quaternion=q((-g*[0,45,62,42][j],0,(i-1.5)*(1-g)*3))
            for j in range(1,4):rig.pose.bones[f'thumb_{j}.{side}'].rotation_quaternion=q((-12*(grip if side=='R' else .7),0,-8*j*(grip if side=='R' else .7)))
        bpy.context.view_layer.update()
        hand=rig.pose.bones['hand.R'];D=hand.matrix@hand.bone.matrix_local.inverted();grippos=D@Vector((-1.07,-.30,1.22));handrot=D.to_quaternion()
        for name in ('prop_rock','prop_plane','prop_scissors'):prop(name,Vector((0,0,-.3)),Quaternion(),.00001)
        if clip!='Idle':
            cfg=phases[clip];a,b=cfg['pull'];visible=smooth((frame-a)/(b-a))
            if frame<a:visible=.00001
            if clip=='Pedra':
                if frame<=cfg['release']:
                    position=grippos;rotation=handrot
                    if frame==cfg['release']:release_pos=position.copy();release_matrix=rotation.copy()
                else:
                    dt=(frame-cfg['release'])/30;position=release_pos+Vector((-2.7,-4.4,3.1))*dt+Vector((0,0,-4.9))*dt*dt
                    rotation=release_matrix@q((dt*400,dt*310,dt*160));visible*=1-smooth((frame-92)/8)
                prop('prop_rock',position,rotation,max(.00001,visible))
            elif clip=='Papel':
                if frame<=cfg['release']:
                    # Folded plane remains horizontal while pinched by its keel.
                    position=grippos+Vector((0,0,.16));rotation=q((-7,0,-16))
                    if frame==cfg['release']:release_pos=position.copy();release_matrix=rotation.copy()
                else:
                    dt=(frame-cfg['release'])/30
                    position=release_pos+Vector((-1.8*dt,-3.0*dt,.50*dt-.25*dt*dt+.11*math.sin(dt*3)))
                    rotation=q((-6+dt*6,12*math.sin(dt*3),-25-5*dt));visible*=1-smooth((frame-109)/8)
                prop('prop_plane',position,rotation,max(.00001,visible))
            else:
                visible*=1-smooth((frame-118)/10)
                prop('prop_scissors',grippos+handrot@Vector((0,0,.36)),handrot,max(.00001,visible))
                angle=curve([(1,5),(43,9),(56,28),(66,2),(76,28),(85,2),(95,28),(104,2),(114,8),(end,5)],frame)
                rig.pose.bones['scissor_A'].rotation_quaternion=q((0,0,angle));rig.pose.bones['scissor_B'].rotation_quaternion=q((0,0,-angle))
        for name in all_names:key(rig.pose.bones[name],frame)
    # Linear sampled tracks preserve the authored smooth analytic paths and avoid Bezier overshoot.
    slot=rig.animation_data.action_slot
    for layer in action.layers:
        for strip in layer.strips:
            bag=strip.channelbag(slot)
            if bag:
                for fc in bag.fcurves:
                    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
    track=rig.animation_data.nla_tracks.new();track.name=clip
    strip=track.strips.new(clip,1,action);track.mute=True
    actions[clip]=action
    clips.append({'name':clip,'frames':end,'fps':30,'duration':(end-1)/30,'release_frame':phases[clip]['release'] if clip in ('Pedra','Papel') else None})

rig['instrucoes']='Selecione uma Action Idle/Pedra/Papel/Tesoura no Action Editor. Controles verdes: IK maos/pes e poles; corpo azul: pelvis/coluna/cabeca. Dedos articulados individualmente. 30 fps.'
rig['preservacao']='Cabeca rigida em um osso para preservar todas as camadas do rosto; bracos/pernas/camiseta subdivididos e pesos normalizados nas dobras.'
scene['pack']='Pedra: retirada do bolso e arremesso. Papel: aviao dobrado e voo. Tesoura: retirada do bolso e tres cortes. Todas as acoes com corpo inteiro.'
scene.frame_start=1;scene.frame_end=144
rig.animation_data.action=actions['Idle'];scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for ob in char.objects:ob.select_set(True)
bpy.context.view_layer.objects.active=rig
pathfile=os.path.join(WEB,'personagem-animado.glb')
bpy.ops.export_scene.gltf(filepath=pathfile,export_format='GLB',use_selection=True,use_active_scene=True,export_apply=False,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_cameras=False,export_lights=False,export_skins=True,export_def_bones=True)
bpy.data.libraries.write(os.path.join(OUT,'personagem_animado.blend'),{scene},fake_user=True,compress=True)
metadata={'fps':30,'rig':rig.name,'bones':len(ad.bones),'deform_bones':len([b for b in ad.bones if b.use_deform]),'clips':clips,'file':'personagem-animado.glb'}
with open(os.path.join(WEB,'pack.json'),'w',encoding='utf-8') as f:json.dump(metadata,f,ensure_ascii=False,indent=2)
with open(os.path.join(OUT,'pack.json'),'w',encoding='utf-8') as f:json.dump(metadata,f,ensure_ascii=False,indent=2)
with open(pathfile,'rb') as f:
    data=f.read();length,kind=struct.unpack_from('<II',data,12);gltf=json.loads(data[20:20+length])
result={'blend':os.path.join(OUT,'personagem_animado.blend'),'glb_bytes':len(data),'animations':[a.get('name') for a in gltf.get('animations',[])],'skins':len(gltf.get('skins',[])),'bones':len(ad.bones)}
