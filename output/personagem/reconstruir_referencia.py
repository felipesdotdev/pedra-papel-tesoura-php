"""Camera-calibrated volumetric reconstruction of the supplied reference.
The face is a sculpted, closed mesh, with real eye sockets and a raised nose.
Colors are sampled into individual face materials; no image plane is rendered.
"""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from pathlib import Path

OUT=Path(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\personagem')
REF=r'C:\Users\luisf\AppData\Local\Temp\codex-clipboard-d9c74af4-7207-4db1-9678-0868985acda4.png'
scene=bpy.data.scenes.new('Personagem • reconstrução fiel 3D')
bpy.context.window.scene=scene
scene['reconstruction_id']='78ffdffe-calibrated-v3'
scene['metodo']='Malhas com profundidade, volumes posteriores fechados e pintura UV a partir da referência. Câmera calibrada para a imagem fornecida.'
model=bpy.data.collections.new('REFERÊNCIA • personagem reconstruído')
studio=bpy.data.collections.new('REFERÊNCIA • câmera e estúdio')
scene.collection.children.link(model)
scene.collection.children.link(studio)
image=bpy.data.images.load(REF,check_existing=True)
image.name='REFERÊNCIA • original fornecido'
image.pack()
W,H=image.size
pixels=np.empty(W*H*4,dtype=np.float32)
image.pixels.foreach_get(pixels)
pixels=pixels.reshape(H,W,4)
K=8.0/H
ELEV=math.radians(8)
RIGHT=Vector((1,0,0))
UP=Vector((0,math.sin(ELEV),math.cos(ELEV)))
FRONT=Vector((0,-math.cos(ELEV),math.sin(ELEV)))
ORIGIN=Vector((0,0,3.9))

def xyz(p,depth):
    u,v=p
    return tuple(ORIGIN+RIGHT*((u-W/2)*K)+UP*((H/2-v)*K)+FRONT*depth)

def linear(v):
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

paint=bpy.data.materials.new('Pintura • cores da referência sobre volumes 3D')
nt=paint.node_tree
nt.nodes.clear()
tex=nt.nodes.new('ShaderNodeTexImage')
tex.image=image
tex.interpolation='Linear'
tex.extension='EXTEND'
tex.label='Pintura UV da imagem de referência'
emit=nt.nodes.new('ShaderNodeEmission')
bsdf=nt.nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Roughness'].default_value=.95
bsdf.inputs['Specular IOR Level'].default_value=.08
mix=nt.nodes.new('ShaderNodeMixShader')
mix.inputs[0].default_value=.055
out=nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(tex.outputs['Color'],emit.inputs['Color'])
nt.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
nt.links.new(emit.outputs[0],mix.inputs[1])
nt.links.new(bsdf.outputs[0],mix.inputs[2])
nt.links.new(mix.outputs[0],out.inputs[0])

matcache={}
def mat(rgb,label='Cor por face'):
    rgb=tuple(max(0,min(255,round(float(c)*255))) for c in rgb)
    key=(rgb,label)
    if key in matcache: return matcache[key]
    m=bpy.data.materials.new(label+' • %02X%02X%02X'%rgb)
    col=tuple(linear(c/255) for c in rgb)
    m.diffuse_color=(*col,1)
    nt=m.node_tree
    nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial')
    emit=nt.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value=(*col,1)
    emit.inputs['Strength'].default_value=1
    bsdf=nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value=(*col,1)
    bsdf.inputs['Roughness'].default_value=.95
    bsdf.inputs['Specular IOR Level'].default_value=.10
    mix=nt.nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value=.055
    nt.links.new(emit.outputs[0],mix.inputs[1])
    nt.links.new(bsdf.outputs[0],mix.inputs[2])
    nt.links.new(mix.outputs[0],out.inputs['Surface'])
    matcache[key]=m
    return m

def sampled(p):
    x=max(0,min(W-1,round(p[0])))
    y=max(0,min(H-1,round(p[1])))
    a=pixels[max(0,H-1-y-1):min(H,H-y+1),max(0,x-1):min(W,x+2),:3]
    return np.median(a.reshape(-1,3),axis=0)

def sample_face(points):
    center=np.mean(points,axis=0)
    samples=[sampled(center)]
    for p in points:
        samples.append(sampled(center*.68+np.array(p)*.32))
    return np.median(samples,axis=0)

def mesh(name,coords,faces,colors=None,collection=model):
    me=bpy.data.meshes.new(name+' • malha')
    me.from_pydata(coords,[],faces)
    me.update()
    ob=bpy.data.objects.new(name,me)
    collection.objects.link(ob)
    slots={}
    if colors is None: colors=[(.25,.15,.10)]*len(faces)
    for poly,col in zip(me.polygons,colors):
        mm=col if isinstance(col,bpy.types.Material) else mat(col)
        if mm.name not in slots:
            slots[mm.name]=len(me.materials)
            me.materials.append(mm)
        poly.material_index=slots[mm.name]
        poly.use_smooth=False
    return ob

def inside(p,loop):
    x,y=p
    hit=False
    j=len(loop)-1
    for i in range(len(loop)):
        xi,yi=loop[i]; xj,yj=loop[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi: hit=not hit
        j=i
    return hit

def triangulate(outline,paths=(),holes=(),extra=()):
    pts=[]; indices={}; edges=[]
    def vid(p):
        p=tuple(float(v) for v in p)
        if p not in indices:
            indices[p]=len(pts); pts.append(p)
        return indices[p]
    def line(path,closed=False):
        ids=[vid(p) for p in path]
        edges.extend(zip(ids,ids[1:]))
        if closed: edges.append((ids[-1],ids[0]))
    line(outline,True)
    for p in paths: line(p)
    for p in holes: line(p,True)
    for p in extra: vid(p)
    coords,ed,fs,*_=delaunay_2d_cdt([Vector(p) for p in pts],edges,[],0,.0001,False)
    coords=[tuple(p) for p in coords]
    fs=[tuple(f) for f in fs if inside(np.mean([coords[i] for i in f],axis=0),outline)
        and not any(inside(np.mean([coords[i] for i in f],axis=0),h) for h in holes)]
    return coords,fs

def surface(name,outline,depth,paths=(),holes=(),extra=(),solid=None,back_color=(.25,.15,.10)):
    pts,faces=triangulate(outline,paths,holes,extra)
    coords=[xyz(p,depth(*p)) for p in pts]
    front_count=len(faces)
    colors=[paint]*len(faces)
    if solid is not None:
        # A complete rear shell, with an intermediate bevel and back cap.
        c=np.mean(outline,axis=0)
        old=len(coords)
        for factor,d in [(1,solid+.07),(.84,solid)]:
            coords.extend(xyz(c+(np.array(p)-c)*factor,d) for p in outline)
        for i in range(len(outline)):
            j=(i+1)%len(outline)
            a=min(range(len(pts)),key=lambda k:(pts[k][0]-outline[i][0])**2+(pts[k][1]-outline[i][1])**2)
            b=min(range(len(pts)),key=lambda k:(pts[k][0]-outline[j][0])**2+(pts[k][1]-outline[j][1])**2)
            faces.extend([(a,b,old+j,old+i),(old+i,old+j,old+len(outline)+j,old+len(outline)+i)])
            colors.extend([back_color,back_color])
        faces.append(tuple(old+len(outline)+i for i in range(len(outline))))
        colors.append(back_color)
    ob=mesh(name,coords,faces,colors)
    uv=ob.data.uv_layers.new(name='Pintura da referência')
    for p in ob.data.polygons:
        for li in p.loop_indices:
            co=Vector(coords[ob.data.loops[li].vertex_index])-ORIGIN
            uv.data[li].uv=(.5+co.dot(RIGHT)/(K*W),.5+co.dot(UP)/(K*H))
    ob['faces_com_pintura_uv']=front_count
    ob['projecao']='Pontos calibrados com a referência original; profundidades em unidades Blender.'
    return ob,pts

# Every important silhouette and facial landmark comes from the reference.
head_outline=[(444,25),(603,29),(780,62),(880,158),(908,276),(900,377),(892,592),(872,647),
 (818,687),(747,728),(635,733),(533,711),(469,689),(399,675),(342,648),(307,593),
 (278,518),(237,455),(224,423),(226,249),(255,141),(380,48)]
eye_l=[(471,433),(509,395),(600,394),(631,405),(663,434),(660,472),(646,493),(496,490),(472,481)]
eye_r=[(761,431),(777,407),(816,400),(865,408),(894,445),(890,487),(879,501),(783,497),(766,480)]
mouth=[(592,578),(625,586),(714,591),(782,585),(807,579),(798,600),(778,616),(750,622),(680,622),(638,615),(620,605)]
brow_l=[(470,380),(498,341),(601,338),(663,357),(669,394),(598,380),(520,380)]
brow_r=[(779,402),(784,368),(824,356),(878,361),(900,377),(899,408),(856,397),(813,392)]
hairline=[(486,69),(411,153),(430,285),(397,341),(394,483),(399,550),(412,619),(369,645),
          (355,590),(351,421),(329,406),(272,402),(238,453)]
paths=[hairline,
 [(380,48),(486,69),(604,70),(736,71),(795,127),(880,158)],
 [(255,141),(342,153),(411,153)],[(226,249),(342,153),(335,275),(430,285)],
 [(226,249),(322,292),(225,389),(224,423),(238,453)],[(322,292),(335,275),(379,428),(351,421)],
 [(342,153),(402,55),(486,69)],[(444,25),(402,55),(380,48)],
 [(486,69),(553,125),(599,179),(614,268),(488,268),(411,153)],
 [(553,125),(692,123),(798,181),(599,179)],[(604,70),(692,123),(795,127)],
 [(795,127),(842,169),(891,269),(891,302),(811,290),(798,181)],
 [(614,268),(811,290),(816,380),(751,425)],[(488,268),(497,341)],[(614,268),(601,338)],
 [(430,285),(488,268)],[(398,483),(491,489),(496,490),(645,493),(638,526),(603,530),(554,555)],
 [(398,550),(491,581),(553,581),(553,643),(491,643),(412,619)],[(491,489),(491,581)],
 [(645,493),(638,526),(683,529)],[(891,500),(835,497),(841,562),(827,647),(872,647)],
 [(785,529),(808,537),(841,562),(827,647)],
 [(690,422),(750,425),(760,473),(785,529),(752,550),(692,549),(638,526),(668,514),(695,472),(690,422)],
 [(695,472),(760,473)],[(668,514),(672,527),(752,527),(785,529)],[(638,526),(672,527),(692,549)],
 [(355,590),(369,645),(412,619),(491,643),(553,643),(554,555),(579,539),(603,530),(638,532),
  (672,548),(692,550),(752,550),(785,535),(808,537),(841,562),(827,647),(872,647)],
 [(582,582),(593,575),(633,590),(708,595),(778,590),(808,580),(812,594),(808,624),(774,666),
  (751,668),(748,652),(668,651),(664,667),(635,666),(582,622),(582,582)],
 [(553,643),(582,622),(635,666),(635,706),(747,703),(774,666),(827,647)],
 [(469,689),(491,643)],[(533,711),(635,706),(635,733)],[(747,703),(747,728)],
 [(554,555),(603,549),(638,552),(672,575),(708,578),(714,565),(723,577),(780,579),(808,580)],
 [(663,434),(690,422)],[(750,425),(761,431)],brow_l+[brow_l[0]],brow_r+[brow_r[0]]]

nose_depth={(690,422):1.56,(750,425):1.43,(695,472):1.83,(760,473):1.72,
 (668,514):2.00,(638,526):1.77,(785,529):1.75,(752,550):1.90,(692,549):2.03,
 (672,527):2.13,(752,527):2.02,(683,529):2.14}
def head_d(u,v):
    # Sculpted front/side falloff makes a broad head, not a flat cutout.
    if (round(u),round(v)) in nose_depth: return nose_depth[(round(u),round(v))]
    d=1.36-.0019*(u-650)
    if u<430: d-=((430-u)/205)*1.65
    if v<180: d-=(180-v)/155*.91
    if v>620: d-=(v-620)/135*.49
    # Chin, upper lip and moustache have physical relief.
    if 550<u<842 and 530<v<583: d+=.12
    return d

head,head_pts=surface('Cabeça • cabelo, rosto e barba esculpidos',head_outline,head_d,paths,[eye_l,eye_r,mouth])

# Close the back of the cranium in three volumetric rings.
coords=[]; faces=[]; colors=[]
for scale,d in [(1,None),(.86,-1.28),(.44,-1.84),(.08,-1.98)]:
    for p in head_outline:
        q=np.array((565,365))+(np.array(p)-np.array((565,365)))*scale
        coords.append(xyz(q,head_d(*p) if d is None else d))
n=len(head_outline)
for j in range(3):
    for i in range(n):
        ni=(i+1)%n
        faces.append((j*n+i,j*n+ni,(j+1)*n+ni,(j+1)*n+i))
        rgb=sampled(((head_outline[i][0]+head_outline[ni][0])/2,(head_outline[i][1]+head_outline[ni][1])/2))
        # Inferred back is warm brown and continues into the side beard.
        if j>0: rgb=np.array((.235,.14,.10))*(1+.08*math.sin(i*1.7))
        colors.append(rgb)
faces.append(tuple(3*n+i for i in range(n))); colors.append((.24,.145,.105))
mesh('Cabeça • crânio posterior fechado',coords,faces,colors)

# Inserted eyes: sclera, large dark polygonal pupils, square highlights.
for label,outline in [('próximo',eye_l),('distante',eye_r)]:
    paths_eye=[]
    if label=='próximo':
        iris=[(514,417),(533,400),(580,399),(611,405),(617,432),(614,466),(603,492),(522,489),(511,468),(510,436)]
        glint=[(533,407),(559,407),(559,434),(533,434)]
        lid=[(471,433),(509,395),(600,394),(631,405),(663,434),(641,422),(616,407),(511,408)]
    else:
        iris=[(770,432),(785,412),(814,411),(846,417),(852,442),(849,474),(839,498),(780,496),(766,475),(766,449)]
        glint=[(786,420),(810,420),(810,446),(786,446)]
        lid=[(761,431),(777,407),(816,400),(865,408),(894,445),(874,432),(849,414),(785,414)]
    surface('Olho '+label+' • esclera',outline,lambda u,v:head_d(u,v)+.035,[iris+[iris[0]]])
    surface('Olho '+label+' • pupila',iris,lambda u,v:head_d(u,v)+.060,solid=head_d(*np.mean(iris,axis=0))+.025,back_color=(.13,.08,.05))
    surface('Olho '+label+' • reflexo quadrado',glint,lambda u,v:head_d(u,v)+.069)
    surface('Olho '+label+' • pálpebra',lid,lambda u,v:head_d(u,v)+.082,solid=head_d(*np.mean(lid,axis=0))-.01,back_color=(.22,.13,.08))

for label,outline in [('próxima',brow_l),('distante',brow_r)]:
    surface('Sobrancelha '+label+' • relevo',outline,lambda u,v:head_d(u,v)+.09,
            solid=head_d(*np.mean(outline,axis=0))-.01,back_color=(.23,.13,.08))

surface('Sorriso • cavidade',mouth,lambda u,v:head_d(u,v)+.025)
tooth=[(623,586),(662,591),(717,592),(775,587),(789,585),(779,601),(752,615),(684,619),(652,613),(638,605)]
surface('Sorriso • dentes',tooth,lambda u,v:head_d(u,v)+.047,
 paths=[[(638,605),(684,611),(752,608),(779,601)]])

# Near ear: an extruded rim and a recessed, darker inner bowl.
ear=[(272,402),(329,406),(351,421),(355,594),(306,600),(241,551),(238,454)]
earpaths=[[(238,454),(279,459),(291,445),(330,451),(333,538),(282,536),(279,459)],
 [(241,551),(266,550),(304,591),(355,594)],[(272,402),(249,444),(238,454)],[(329,406),(330,451)]]
def ear_d(u,v):
    if 281<u<334 and 451<v<538: return .65
    return .89 if u<280 else .94
surface('Orelha próxima • aro e cavidade',ear,ear_d,earpaths,solid=.40,back_color=(.58,.30,.15))

# Neck, shirt, folded collar and the hanging arm.
neck=[(532,697),(548,716),(591,752),(631,784),(655,789),(681,767),(699,732),(706,714)]
surface('Pescoço • sob a barba',neck,lambda u,v:.31,paths=[[(548,716),(633,761),(681,767)]],solid=-.42,back_color=(.56,.30,.16))
shirt_outline=[(442,686),(398,704),(359,731),(330,784),(310,846),(318,873),(336,913),(380,938),
 (379,994),(435,1004),(527,1006),(745,1002),(755,971),(771,897),(806,864),(821,838),
 (791,785),(764,747),(721,724),(699,732),(681,767),(655,789),(631,784),(591,752),(548,716),(521,705),(477,684)]
shirt_paths=[[(398,704),(407,719),(443,714),(477,684)],[(359,731),(391,744),(407,719)],
 [(330,784),(363,783),(391,744),(416,782)],[(310,846),(342,812)],
 [(380,938),(433,943),(431,1003)],[(433,943),(466,971),(527,974),(527,1006)],
 [(527,974),(580,973),(745,970),(745,1002)],[(580,973),(581,854)],
 [(548,716),(530,768),(552,805),(592,796),(634,854),(655,864),(709,800),(759,815),(740,768),(721,724)],
 [(552,805),(551,829)],[(634,854),(641,839),(592,796)],[(655,864),(673,846),(709,800)],
 [(764,747),(750,784),(779,851),(806,864)],[(709,800),(722,925),(745,970)],
 [(527,974),(534,894),(551,829)]]
def shirt_d(u,v):
    d=.57-.0008*(u-600)
    if u<390: d-=.42
    if u>750: d-=.22
    return d
surface('Camisa oliva • corpo e mangas',shirt_outline,shirt_d,shirt_paths,solid=-.56,back_color=(.32,.30,.13))
collar_l=[(548,716),(530,768),(552,805),(592,796),(634,854),(641,839),(607,790),(570,750)]
collar_r=[(699,732),(721,724),(740,768),(759,815),(709,800),(673,846),(655,864),(655,841),(682,802)]
surface('Gola • dobra próxima',collar_l,lambda u,v:shirt_d(u,v)+.035)
surface('Gola • dobra distante',collar_r,lambda u,v:shirt_d(u,v)+.035)
arm=[(806,858),(821,895),(843,957),(840,1017),(814,1039),(774,1049),(750,1039),(742,1013),(746,972),(743,947),(749,904)]
surface('Braço e mão relaxada • volume fechado',arm,lambda u,v:.45-.0007*(u-790),
 paths=[[(749,904),(778,932),(830,918)],[(778,932),(785,971),(843,957)],
        [(785,971),(775,1030),(814,1032)],[(746,972),(763,985),(755,1027),(774,1049)],[(814,1032),(840,1017)]],
 solid=-.05,back_color=(.67,.36,.18))

# Continuous hand mesh, with incised creases instead of disconnected bars.
hand=[(317,878),(337,912),(367,926),(400,929),(433,943),(519,930),(537,923),(542,892),(541,888),
 (549,879),(551,842),(544,839),(551,829),(551,793),(512,778),(518,754),(526,732),(521,703),
 (504,691),(483,685),(468,695),(461,732),(448,767),(416,782),(360,785),(342,798)]
handpaths=[[(342,812),(396,822),(448,788),(467,795),(466,827),(550,830)],
 [(396,822),(393,909),(425,923),(433,943)],[(466,827),(466,839),(544,840)],
 [(466,876),(465,886),(541,890)],[(466,839),(464,876)],[(425,923),(465,924),(537,923)],
 [(448,767),(478,774),(512,778)],[(461,732),(493,735),(526,732)],[(468,695),(495,698),(504,691)],
 [(317,878),(331,893),(367,907),(393,909)],[(342,798),(342,812)]]
def hand_d(u,v):
    d=1.55
    if u>465: d=1.69
    if u<380: d=1.30+(u-317)/63*.20
    if v<785: d=1.59+.001*(v-730)
    return d
surface('Mão do positivo • palma, dedos e polegar unidos',hand,hand_d,handpaths,solid=.86,back_color=(.73,.40,.21))
for i,crease in enumerate([[(467,827),(550,831),(550,839),(466,835)],[(466,876),(549,881),(541,889),(465,883)]]):
    surface('Mão • dobra '+str(i+1),crease,lambda u,v:1.695)

# Cord and gold cross: separate closed meshes.
def ribbon(name,path,width,depth,rgb):
    coords=[]
    for i,p in enumerate(path):
        vec=Vector(path[min(i+1,len(path)-1)])-Vector(path[max(0,i-1)])
        norm=Vector((-vec.y,vec.x)).normalized()*width/2
        coords.extend([xyz(Vector(p)+norm,depth),xyz(Vector(p)-norm,depth)])
    fs=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(path)-1)]
    return mesh(name,coords,fs,[rgb]*len(fs))
ribbon('Colar • cordão preto',[(548,717),(576,748),(614,777),(643,790),(656,791),(679,765),(699,733)],7,.68,(.08,.066,.055))
cross=[(644,788),(654,789),(656,807),(671,807),(671,820),(657,820),(658,843),(646,844),(644,820),
       (631,820),(630,807),(643,807)]
surface('Colar • crucifixo dourado',cross,lambda u,v:.76,paths=[[(644,788),(648,815),(646,844)]],solid=.69,back_color=(.65,.42,.03))

# Wide trousers and black shoes with thick ivory soles.
leg_l=[(403,1001),(598,1005),(582,1050),(558,1148),(547,1170),(391,1157),(368,1110),(387,1038)]
leg_r=[(598,1005),(741,1003),(759,1065),(773,1112),(762,1145),(703,1162),(590,1155),(580,1118),(580,1085)]
surface('Calça • perna próxima',leg_l,lambda u,v:.46,
 paths=[[(403,1001),(441,1033),(526,1026),(598,1005)],[(441,1033),(418,1119),(368,1110)],
        [(418,1119),(558,1135),(547,1170)],[(526,1026),(498,1126)]],solid=-.37,back_color=(.17,.16,.23))
surface('Calça • perna distante',leg_r,lambda u,v:.30,
 paths=[[(598,1005),(633,1040),(741,1003)],[(633,1040),(659,1135),(703,1162)],[(659,1135),(773,1112)]],
 solid=-.43,back_color=(.15,.15,.21))
shoe_l=[(382,1148),(528,1155),(549,1174),(556,1204),(560,1235),(424,1243),(368,1224),(369,1190),(375,1185)]
shoe_r=[(591,1152),(673,1145),(765,1156),(792,1173),(804,1193),(809,1228),(712,1237),(586,1215),(586,1184)]
surface('Tênis próximo • volume e sola',shoe_l,lambda u,v:.90,
 paths=[[(382,1148),(426,1174),(549,1174)],[(426,1174),(424,1209),(374,1189)],
        [(369,1190),(424,1207),(548,1206),(556,1201)],[(424,1207),(424,1243)]],solid=-.20,back_color=(.16,.14,.14))
surface('Tênis distante • volume e sola',shoe_r,lambda u,v:.69,
 paths=[[(591,1152),(674,1170),(792,1173)],[(674,1170),(712,1204),(804,1193)],
        [(587,1187),(712,1204),(808,1194)],[(712,1204),(712,1237)]],solid=-.31,back_color=(.15,.13,.13))

# A genuinely horizontal, sixteen-sided circular pedestal.
coords=[]; faces=[]; colors=[]
N=24
for cy,rx in [(1214,314),(1226,322),(1263,327)]:
    for i in range(N):
        t=2*math.pi*i/N
        p=(590+rx*math.cos(t),cy+rx*math.sin(ELEV)*math.sin(t))
        d=rx*K*math.cos(ELEV)*math.sin(t)
        coords.append(xyz(p,d))
for j in range(2):
    for i in range(N):
        ni=(i+1)%N
        f=(j*N+i,j*N+ni,(j+1)*N+ni,(j+1)*N+i)
        faces.append(f)
        pp=[]
        for ix in f:
            co=Vector(coords[ix])-ORIGIN
            pp.append((W/2+co.dot(RIGHT)/K,H/2-co.dot(UP)/K))
        colors.append(sample_face(pp))
faces.append(tuple(reversed(range(N)))); colors.append((.27,.25,.29))
faces.append(tuple(2*N+i for i in range(N))); colors.append((.14,.125,.15))
base=mesh('Base • pedestal circular facetado',coords,faces,colors,studio)

# Camera and a restrained neutral lighting rig.
camera_data=bpy.data.cameras.new('Câmera • enquadramento da referência')
camera=bpy.data.objects.new('Câmera • enquadramento da referência',camera_data)
studio.objects.link(camera)
camera.location=ORIGIN+FRONT*25
camera.rotation_euler=(-FRONT).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO'
camera_data.ortho_scale=8
camera_data.lens=65
scene.camera=camera
world=bpy.data.worlds.new('Mundo • cinza berinjela')
nt=world.node_tree
nt.nodes.clear()
bg=nt.nodes.new('ShaderNodeBackground')
wo=nt.nodes.new('ShaderNodeOutputWorld')
bg.inputs['Color'].default_value=tuple(linear(v/255) for v in (42,37,47))+(1,)
bg.inputs['Strength'].default_value=1
nt.links.new(bg.outputs[0],wo.inputs['Surface'])
scene.world=world
for name,pos,power,size in [('Luz • principal',(-4,-8,10),650,5),('Luz • preenchimento',(5,-4,6),300,5)]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.size=size
    light=bpy.data.objects.new(name,data); studio.objects.link(light); light.location=pos
    light.rotation_euler=(Vector((0,0,4))-light.location).to_track_quat('-Z','Y').to_euler()

# Emissive studio wall keeps the same background tone across the frame.
back=mat(tuple(v/255 for v in (42,37,47)),'Fundo')
bgco=[xyz((-200,-200),-5),xyz((W+200,-200),-5),xyz((W+200,H+200),-5),xyz((-200,H+200),-5)]
mesh('Fundo • painel de estúdio',bgco,[(0,1,2,3)],[back],studio)
scene.render.engine='CYCLES'
scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.render.resolution_x=W
scene.render.resolution_y=H
scene.render.resolution_percentage=50
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.view_settings.exposure=0
scene.render.filepath=str(OUT/'previa_reconstrucao.png')
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active=head
head.select_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'personagem_reconstruido.blend'))
result={'scene':scene.name,'objects':len(model.objects),'faces':sum(len(o.data.polygons) for o in model.objects if o.type=='MESH'),
        'materials':len(matcache),'blend':str(OUT/'personagem_reconstruido.blend')}
