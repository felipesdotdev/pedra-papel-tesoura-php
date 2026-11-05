"""Rebuild volume from the supplied front/profile/back sheet; retain the animated IK rig.
All meshes use real geometry around the cranium, not stacked frontal plates.
"""
import bpy,bmesh,math,random,os,json,struct
from mathutils import Vector,Matrix,Euler
ROOT=r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php'
OUT=os.path.join(ROOT,'output','animacoes');WEB=os.path.join(ROOT,'assets','personagem','animacoes')
scene=bpy.data.scenes['PACK v2 | Corpo inteiro'];bpy.context.window.scene=scene
scene.name='PACK v3 | Referencia multiangulo'
char=next(c for c in scene.collection.children if any(o.type=='ARMATURE' for o in c.objects))
rig=next(o for o in char.objects if o.type=='ARMATURE')
actions={t.name:t.strips[0].action for t in rig.animation_data.nla_tracks}
rig.animation_data.action=None
for p in rig.pose.bones:p.location=(0,0,0);p.rotation_quaternion=(1,0,0,0);p.scale=(1,1,1)
SHIFT=.93*.47
def legz(z):return z if z<=.35 else .35+(z-.35)*1.47 if z<1.28 else z+SHIFT
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
rest_snapshot={b.name:(b.head.copy(),b.tail.copy(),b.use_connect) for b in rig.data.edit_bones}
for bo in rig.data.edit_bones:bo.use_connect=False
for bo in rig.data.edit_bones:
    a,b,connected=rest_snapshot[bo.name]
    if not bo.name.startswith(('prop_','scissor')) and bo.name!='root':
        for point in (a,b):point.z=legz(point.z) if bo.name.startswith(('thigh','shin','foot','toe','CTRL_foot','POLE_leg','pelvis')) else point.z+SHIFT
    bo.head=a;bo.tail=b
for bo in rig.data.edit_bones:bo.use_connect=rest_snapshot[bo.name][2]
bpy.ops.object.mode_set(mode='OBJECT')
for action in actions.values():
    slot=action.slots[0]
    for layer in action.layers:
        for strip in layer.strips:
            bag=strip.channelbag(slot)
            if bag:
                for fc in bag.fcurves:
                    if 'pose.bones["prop_' in fc.data_path and fc.data_path.endswith('.location') and fc.array_index==1:
                        for kp in fc.keyframe_points:kp.co.y+=SHIFT;kp.handle_left.y+=SHIFT;kp.handle_right.y+=SHIFT

keep=[]
for ob in list(char.objects):
    if ob.type!='MESH':continue
    groups=[g.name for g in ob.vertex_groups]
    if any(g.startswith(('prop_','scissor')) for g in groups):keep.append(ob)
    elif any(g.startswith(('hand.','thumb_','index_','middle_','ring_','pinky_')) for g in groups):
        for v in ob.data.vertices:v.co.z+=SHIFT
        keep.append(ob)
    else:bpy.data.objects.remove(ob,do_unlink=True)

rng=random.Random(206)
def colorhex(s):
    rgb=[int(s[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)
def mat(name,s,rough=.95,metal=0,alpha=1):
    ma=bpy.data.materials.new('REF | '+name);rgb=colorhex(s);ma.diffuse_color=(*rgb,alpha);ma.use_nodes=True
    bs=next(n for n in ma.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;bs.inputs['Alpha'].default_value=alpha;bs.inputs['Specular IOR Level'].default_value=.15
    return ma
skin=mat('Pele pessego','DF9367');skinlight=mat('Pele planos claros','E6996C');skinshade=mat('Pele planos laterais','D58960')
skinface=mat('Pele com barba curta','DF9367')
image=bpy.data.images.load(os.path.join(OUT,'pele_barba.png'),check_existing=True);image.pack()
tex=skinface.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
bs=next(n for n in skinface.node_tree.nodes if n.type=='BSDF_PRINCIPLED');skinface.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
hair=[mat('Cabelo castanho','34271F'),mat('Cabelo plano medio','403027'),mat('Cabelo plano claro','4B3A2D'),mat('Cabelo temporas grisalhas','79736B'),mat('Cabelo transicao grisalha','665E54')]
red=[mat('Camiseta vermelho','8F2720'),mat('Camiseta plano claro','9F3127'),mat('Camiseta costura','7C201B')]
navy=[mat('Calca azul ardósia','303D51'),mat('Calca plano claro','3B495E'),mat('Calca dobras','293548')]
shoe=[mat('Tenis preto','232222'),mat('Tenis biqueira','302D2A')];sole=mat('Solado marfim','E4D4C0')
iris=mat('Iris castanho escuro','39291E',.8);pupil=mat('Pupila','17120E');white=mat('Esclera marfim','E8D1B4');glint=mat('Reflexo olho','FFF4DF',.5)
mouth=mat('Sorriso interior','522A20');teeth=mat('Sorriso dentes','F5E4CD');lip=mat('Labio suave','B76B47');nosemat=mat('Nariz ponta','D9875E')
metal=mat('Oculos aros cinza','A39D8E',.32,.45);temple=mat('Oculos hastes pretas','34302B',.75);lens=mat('Oculos lentes claras','B9C0B6',.12,0,.045)

def mesh(name,vs,fs,mats,ids=None,uv=False):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.validate();ob=bpy.data.objects.new('REF | '+name,me);char.objects.link(ob)
    for ma in mats:me.materials.append(ma)
    if ids:
        for p,i in zip(me.polygons,ids):p.material_index=i
    if uv:
        layer=me.uv_layers.new(name='FaceUV')
        for p in me.polygons:
            for li in p.loop_indices:
                v=me.vertices[me.loops[li].vertex_index].co;layer.data[li].uv=(v.x/2.6+.5,(v.z-3.0)/3.4)
    return ob
def bind(ob,weights):
    groups={}
    for v in ob.data.vertices:
        for name,w in (weights(v.co) if callable(weights) else [(weights,1)]):
            if w<=1e-6:continue
            if name not in groups:groups[name]=ob.vertex_groups.new(name=name)
            groups[name].add([v.index],w,'REPLACE')
    mod=ob.modifiers.new('Rig | pesos normalizados','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True;ob.parent=rig;ob.matrix_parent_inverse=Matrix.Identity(4)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def torso(v):
    z=v.z-SHIFT
    if z<1.6:t=smooth((z-1.25)/.35);return [('pelvis',1-t),('spine',t)]
    t=smooth((z-1.78)/.55);return [('spine',1-t),('chest',t)]
def rect(x,y,b):return [(-x+b,-y),(x-b,-y),(x,-y+b),(x,y-b),(x-b,y),(-x+b,y),(-x,y-b),(-x,-y+b)]
def loft(name,rings,mats,weight,tri=False):
    n=len(rings[0]);vs=[v for ring in rings for v in ring];fs=[tuple(reversed(range(n)))];ids=[0]
    for j in range(len(rings)-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;c=(j+1)*n+(i+1)%n;d=(j+1)*n+i
            if tri and (i+j)%3==1:fs.extend([(a,b,d),(b,c,d)]);ids.extend([0,1 if len(mats)>1 else 0])
            else:fs.append((a,b,c,d));ids.append(1 if len(mats)>1 and i==3 else 0)
    fs.append(tuple((len(rings)-1)*n+i for i in range(n)));ids.append(0)
    ob=mesh(name,vs,fs,mats,ids);bind(ob,weight);return ob
def tube(name,path,radii,mats,weight,sides=8):
    rings=[]
    for j,p in enumerate(path):
        p=Vector(p);t=(Vector(path[min(len(path)-1,j+1)])-Vector(path[max(0,j-1)])).normalized();u=t.cross(Vector((0,1,0)))
        if u.length<.01:u=t.cross(Vector((1,0,0)))
        u.normalize();v=t.cross(u).normalized();r=radii[j] if isinstance(radii,(tuple,list)) else radii
        rings.append([tuple(p+r*(u*math.cos(i*2*math.pi/sides)+v*math.sin(i*2*math.pi/sides))) for i in range(sides)])
    return loft(name,rings,mats,weight)

# Continuous torso with shoulder topology and sleeves instead of floating face panels.
rings=[]
for z,w,d in [(1.225,.70,.34),(1.5,.70,.34),(1.9,.69,.35),(2.23,.66,.35),(2.47,.56,.32),(2.60,.33,.25)]:
    rings.append([(x,y+.035,z+SHIFT) for x,y in rect(w,d,.13)])
loft('Camiseta vermelha',rings,red,torso)
tube('Pescoco',[(0,.04,2.48+SHIFT),(0,.04,2.92+SHIFT)],[.30,.32],[skin],'neck',8)
for side,sgn in [('R',-1),('L',1)]:
    upper=rig.data.bones['upper_arm.'+side];fore=rig.data.bones['forearm.'+side]
    path=[upper.head_local.copy(),upper.head_local.lerp(upper.tail_local,.35),upper.tail_local.copy(),fore.head_local.lerp(fore.tail_local,.5),fore.tail_local.copy()]
    def armw(v,side=side):
        t=smooth((v.z-SHIFT-1.76)/.24);return [('forearm.'+side,1-t),('upper_arm.'+side,t)]
    tube('Braco '+side,path,[.205,.205,.20,.18,.17],[skin,skinlight],armw)
    a=upper.head_local;b=upper.head_local.lerp(upper.tail_local,.63)
    tube('Manga '+side,[a+Vector((-sgn*.05,0,.11)),a.lerp(b,.55),b],[.33,.33,.30],red,'upper_arm.'+side,8)
    # Longer blue trousers and level soles, matched to the front and side references.
    rr=[]
    for z,cx,w,d in [(1.72,.37,.32,.32),(1.49,.40,.33,.32),(1.18,.45,.32,.31),(.94,.49,.31,.31),(.69,.52,.30,.30),(.43,.53,.30,.29)]:
        rr.append([(x+sgn*cx,y+.04,z) for x,y in rect(w,d,.07)])
    def legw(v,side=side):t=smooth((v.z-legz(.65))/(legz(.88)-legz(.65)));return [('shin.'+side,1-t),('thigh.'+side,t)]
    loft('Calca '+side,rr,navy,legw,True)
    sr=[]
    for z,w,d in [(.005,.41,.53),(.20,.41,.53),(.23,.39,.51)]:sr.append([(x+sgn*.55,y-.13,z) for x,y in rect(w,d,.085)])
    loft('Solado '+side,sr,[sole],'foot.'+side)
    sr=[]
    for z,w,d in [(.225,.39,.51),(.37,.385,.49),(.52,.30,.37)]:sr.append([(x+sgn*.55,y-.11,z) for x,y in rect(w,d,.09)])
    loft('Tenis '+side,sr,shoe,'foot.'+side)
    tube('Bolso '+side,[(sgn*.69,-.294,1.61),(sgn*.40,-.299,1.50)],[.012,.012],[navy[2]],'pelvis',4)
for ob in keep:
    if any(g.name.startswith(('hand.','thumb_','index_','middle_','ring_','pinky_')) for g in ob.vertex_groups):
        ob.data.materials.clear();ob.data.materials.append(skin)

# Broad low-poly facial surface, anatomically shaped eye openings and true side/back volume.
rows=[(3.12,.40),(3.25,.66),(3.48,.90),(3.72,1.02),(3.95,1.08),(4.18,1.11),(4.40,1.13),(4.56,1.14),(4.72,1.13),(5.04,1.11),(5.38,1.06),(5.70,.99),(5.94,.77),(6.10,.40),(6.15,.10)]
cols=[-1,-.78,-.64,-.27,-.16,.16,.27,.64,.78,1]
def front(x,z):
    y=-.97+.30*(abs(x)/1.15)**3+.052*(z-4.50)**2
    return y*(1-.94*smooth((z-5.65)/.52))
vs=[]
for j,(z,w) in enumerate(rows):
    for i,u in enumerate(cols):
        zz=z
        if j==8:zz=4.63 if i in (1,4,5,8) else 4.72
        if j==6:zz=4.46 if i in (1,4,5,8) else 4.40
        x=u*w*(1-.25*smooth((zz-5.70)/.40));vs.append((x,front(x,zz),zz))
fs=[]
for j in range(len(rows)-1):
    for i in range(9):
        if j in (6,7) and i in (1,2,3,5,6,7):continue
        a=j*10+i;b=a+1;c=a+11;d=a+10
        if j not in (6,7) and (i+j)%4==1:fs.extend([(a,b,d),(b,c,d)])
        else:fs.append((a,b,c,d))
ob=mesh('Rosto orbitas abertas',vs,fs,[skinface],uv=True);bind(ob,'head')
sidevs=[]
for z,w in rows:
    k=min(1,w/.9)
    shrink=1-.25*smooth((z-5.70)/.40)
    sidevs.extend((x*shrink,y*shrink,z) for x,y,z in [(-w,front(w,z),z),(-w-.08*k,-.1,z),(-w*.94,.53*k,z),(-w*.64,.95*k,z),(0,1.10*k,z),(w*.64,.95*k,z),(w*.94,.53*k,z),(w+.08*k,-.1,z),(w,front(w,z),z)])
fs=[]
for j in range(len(rows)-1):
    for i in range(8):
        a=j*9+i;b=a+1;c=a+10;d=a+9
        if (i+j)%3==1:fs.extend([(a,b,c),(a,c,d)])
        else:fs.append((a,b,c,d))
ob=mesh('Laterais cranio e nuca',sidevs,fs,[skinface],uv=True);bind(ob,'head')

def plaque(name,outline,ma,offset=.025):
    ob=mesh(name,[(x,front(x,z)-offset,z) for x,z in outline],[tuple(range(len(outline)))],[ma],uv=ma==skinface);bind(ob,'head');return ob
for sign,start in [(-1,1),(1,5)]:
    idx=[6*10+start+k for k in range(4)]+[7*10+start+3,8*10+start+3,8*10+start+2,8*10+start+1,8*10+start,7*10+start]
    loop=[Vector(vs[i]) for i in idx];cx=(loop[0].x+loop[3].x)/2;cz=4.555
    inside=[(cx+(p.x-cx)*.81,front(cx,cz)-.020,cz+(p.z-cz)*.70) for p in loop]
    ev=[tuple(p) for p in loop]+inside
    ob=mesh('Orbita pele '+str(sign),ev,[(i,(i+1)%10,(i+1)%10+10,i+10) for i in range(10)],[skinface],uv=True);bind(ob,'head')
    ev=inside+[(cx,front(cx,cz)-.038,cz)]
    ob=mesh('Esclera '+str(sign),ev,[(i,(i+1)%10,10) for i in range(10)],[white]);bind(ob,'head')
    outline=[(cx+x,cz+z) for x,z in [(-.085,-.115),(.085,-.115),(.115,-.085),(.115,.085),(.085,.115),(-.085,.115),(-.115,.085),(-.115,-.085)]]
    plaque('Iris '+str(sign),outline,iris,.075)
    outline=[(cx+.064*math.cos(i*math.pi/4),cz+.084*math.sin(i*math.pi/4)) for i in range(8)]
    plaque('Pupila '+str(sign),outline,pupil,.082)
    plaque('Brilho '+str(sign),[(cx-.025,cz+.02),(cx+.014,cz+.02),(cx+.014,cz+.058),(cx-.025,cz+.058)],glint,.087)
    brow=[(-.91,4.91),(-.74,5.045),(-.43,5.00),(-.26,4.87),(-.56,4.91),(-.91,4.86)]
    if sign==1:brow=[(-x,z) for x,z in reversed(brow)]
    plaque('Sobrancelha '+str(sign),brow,hair[0],.07)
    upper=[(p[0],p[2]) for p in inside[5:9]]
    plaque('Palpebra '+str(sign),upper+[(x,z+.025) for x,z in reversed(upper)],hair[0],.052)

# Compact, broad-tipped nose; the silhouette reads in profile as well as in front.
nv=[(-.12,-.975,4.73),(.12,-.975,4.73),(-.135,-1.13,4.39),(.135,-1.13,4.39),(-.25,-1.32,4.17),(.25,-1.32,4.17),(-.20,-1.20,4.075),(.20,-1.20,4.075),(0,-1.37,4.18),(0,-1.16,4.40),(-.24,-.91,4.27),(.24,-.91,4.27)]
nf=[(0,1,3,2),(2,3,9),(2,9,8,4),(9,3,5,8),(4,8,5,7,6),(0,2,4,10),(1,11,5,3),(10,4,6),(11,7,5),(6,7,11,10)]
ob=mesh('Nariz ponte e ponta',nv,nf,[skin,nosemat,skinshade],[0,0,1,1,1,0,0,2,2,2]);bind(ob,'head')
smile=[(-.59,3.965),(-.40,3.91),(0,3.875),(.40,3.91),(.59,3.965),(.51,3.78),(.31,3.66),(0,3.63),(-.31,3.66),(-.51,3.78)]
plaque('Sorriso abertura',smile,mouth,.037)
dent=[(-.51,3.93),(-.30,3.89),(0,3.855),(.30,3.89),(.51,3.93),(.44,3.80),(.24,3.73),(0,3.715),(-.24,3.73),(-.44,3.80)]
plaque('Sorriso dentes',dent,teeth,.052)
plaque('Labio inferior',[(-.36,3.65),(0,3.61),(.36,3.65),(.25,3.62),(0,3.585),(-.25,3.62)],lip,.029)

# Ears with a recessed bowl and a small forward tragus.
shape=[(-.13,.34),(.13,.37),(.27,.21),(.27,-.09),(.11,-.35),(-.11,-.34),(-.23,-.14),(-.24,.20)]
for sign in (-1,1):
    ev=[]
    for scale,y in [(1,-.33),(.70,-.39),(.52,-.22),(1,.03)]:ev.extend((sign*(1.14+x*scale),y,4.46+z*scale) for x,z in shape)
    ef=[];ids=[]
    for i in range(8):j=(i+1)%8;ef.extend([(i,j,j+8,i+8),(i+8,j+8,j+16,i+16),(i+24,j+24,j,i)]);ids.extend([0,1,0])
    ef.append(tuple(16+i for i in range(8)));ids.append(1)
    ob=mesh('Orelha '+str(sign),ev,ef,[skin,skinshade],ids);bind(ob,'head')

# Thin beveled rectangular frames, metal bridge and dark side temples.
frame=[(.16,4.69),(.21,4.77),(.88,4.77),(1.00,4.69),(.97,4.37),(.88,4.31),(.26,4.32),(.18,4.40)]
for sign in (-1,1):
    p=[(sign*x,front(sign*x,z)-.14,z) for x,z in frame];p.append(p[0]);tube('Oculos aro '+str(sign),p,.017,[metal],'head',6)
    lensob=plaque('Oculos lente '+str(sign),[(sign*x,z) for x,z in frame],lens,.12);lensob.visible_shadow=False
    tube('Oculos haste '+str(sign),[(sign*.98,-.89,4.68),(sign*1.15,-.26,4.67),(sign*1.20,.19,4.57),(sign*1.16,.30,4.44)],.025,[temple],'head',6)
tube('Oculos ponte',[(-.17,-1.09,4.65),(-.10,-1.11,4.68),(0,-1.12,4.69),(.10,-1.11,4.68),(.17,-1.09,4.65)],.019,[metal],'head',6)

# A combed asymmetric cap, with a connected gray band around the nape.
N=28;hr=[]
def line(t):
    a=abs(math.degrees(t));a=360-a if a>180 else a
    keys=[(0,5.80),(15,5.84),(30,5.98),(47,5.57),(65,5.01),(90,4.55),(110,3.95),(145,3.55),(180,3.47)]
    for (a0,z0),(a1,z1) in zip(keys,keys[1:]):
        if a0<=a<=a1:return z0+(z1-z0)*(a-a0)/(a1-a0)-.055*math.sin(t)
    return 3.82
for layer in range(5):
    ring=[]
    for i in range(N):
        t=i*2*math.pi/N;blend=[0,.22,.57,.86,1][layer];sc=[1,1.035,.98,.69,.20][layer]
        z=line(t)*(1-blend)+(6.27+.05*math.cos(t+.8))*blend
        x=1.24*math.copysign(abs(math.sin(t))**.77,math.sin(t))*sc
        y=.10-math.copysign(abs(math.cos(t))**.74,math.cos(t))*(.95 if math.cos(t)>0 else 1.18)*sc
        ring.append((x,y,z))
    hr.append(ring)
hv=[p for r in hr for p in r];hf=[];ids=[]
for j in range(4):
    for i in range(N):
        a=j*N+i;b=j*N+(i+1)%N;c=(j+1)*N+(i+1)%N;d=(j+1)*N+i
        z=sum(hv[k][2] for k in (a,b,c,d))/4;t=(i+.5)*2*math.pi/N
        gray=(math.cos(t)<-.15 and z<4.75) or (abs(math.sin(t))>.86 and z<5.25)
        mi=(3 if (i+j)%3 else 4) if gray else ([0,0,1,1,2][(i+2*j)%5])
        if (i+j)%3==1:hf.extend([(a,b,d),(b,c,d)]);ids.extend([mi,mi])
        else:hf.append((a,b,c,d));ids.append(mi)
hf.append(tuple(4*N+i for i in range(N)));ids.append(1)
ob=mesh('Cabelo topo penteado temporas e nuca',hv,hf,hair,ids);bind(ob,'head')

# Preserve the IK preferred bend after extending the legs.
bpy.context.view_layer.update()
for side in ('R','L'):
    for tip in ('forearm','shin'):
        pb=rig.pose.bones[tip+'.'+side];con=next(c for c in pb.constraints if c.type=='IK');target=pb.bone.head_local.copy();best=(1e9,con.pole_angle)
        for k in range(48):
            con.pole_angle=-math.pi+2*math.pi*k/48;bpy.context.view_layer.update();error=(pb.head-target).length
            if error<best[0]:best=(error,con.pole_angle)
        con.pole_angle=best[1]

# Clear, artist-facing control shapes (not rendered/exported as model geometry).
visual=bpy.data.collections.new('Controles | formas');scene.collection.children.link(visual);visual.hide_render=True
for name,points in [('Mao',[(-.22,-.22,0),(.22,-.22,0),(.22,.22,0),(-.22,.22,0)]),('Pe',[(-.28,-.48,0),(.28,-.48,0),(.28,.25,0),(-.28,.25,0)]),('Pole',[(0,-.15,0),(.15,0,0),(0,.15,0),(-.15,0,0)])]:
    me=bpy.data.meshes.new('CTRL '+name);me.from_pydata(points,[(i,(i+1)%len(points)) for i in range(len(points))],[])
    ob=bpy.data.objects.new('CTRL shape '+name,me);visual.objects.link(ob);ob.hide_set(True)
    for pb in rig.pose.bones:
        if (name=='Mao' and pb.name.startswith('CTRL_hand')) or (name=='Pe' and pb.name.startswith('CTRL_foot')) or (name=='Pole' and pb.name.startswith('POLE')):
            pb.custom_shape=ob;pb.use_custom_shape_bone_size=False

for t in rig.animation_data.nla_tracks:t.mute=True
rig.animation_data.action=actions['Idle'];scene.frame_set(1);scene.frame_end=144
scene.camera.location=(7,-21,7);scene.camera.rotation_euler=(Vector((0,0,3.15))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=7.1
scene.render.resolution_x=760;scene.render.resolution_y=900;scene.render.resolution_percentage=60;scene.cycles.samples=16
scene['referencia']='Folha multiangulo anexada pelo usuario: frente, tres quartos, perfil e nuca.'
scene.render.filepath=os.path.join(OUT,'personagem_referencia.png')
bpy.data.libraries.write(os.path.join(OUT,'personagem_referencia_animado.blend'),{scene},fake_user=True,compress=True)
result={'scene':scene.name,'rig':rig.name,'meshes':len([o for o in char.objects if o.type=='MESH']),'actions':{k:v.name for k,v in actions.items()},'blend':os.path.join(OUT,'personagem_referencia_animado.blend')}
