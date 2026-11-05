"""True volumetric low-poly character. No image textures, projection or UV paint.
The supplied picture is used only as a visual modeling reference.
Includes a deforming FK skeleton, articulated fingers, gaze and blink controls.
"""
import bpy, bmesh, math, random, json
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.geometry import delaunay_2d_cdt

OUT=Path(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\personagem')
OUT.mkdir(parents=True,exist_ok=True)
rng=random.Random(406)
s=bpy.data.scenes.new('Personagem 3D • materiais sólidos e rig')
bpy.context.window.scene=s
s['asset_id']='personagem-volumetrico-rig-v1'
s['textures']=False
s['descricao']='Geometria tridimensional bilateral. Materiais Principled sólidos. Rig FK de corpo, cabeça, olhos, sobrancelhas e dedos; controles de piscar.'
geo=bpy.data.collections.new('01 • MALHAS 3D')
rigcol=bpy.data.collections.new('02 • RIG E CONTROLES')
stage=bpy.data.collections.new('03 • ESTÚDIO')
for c in (geo,rigcol,stage): s.collection.children.link(c)
head_objs=[]
all_mesh=[]
bones={}
blink=[]

def srgb(c): return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def material(name,hexcol,rough=.88,metal=0):
    m=bpy.data.materials.new('3D • '+name)
    rgb=tuple(srgb(int(hexcol[i:i+2],16)/255) for i in (0,2,4))
    m.diffuse_color=(*rgb,1)
    nt=m.node_tree; nt.nodes.clear()
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=(*rgb,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal
    bs.inputs['Specular IOR Level'].default_value=.10
    out=nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(bs.outputs[0],out.inputs['Surface'])
    return m
def pal(name,cols): return [material(name+' '+str(i+1),c) for i,c in enumerate(cols)]
skin=pal('Pele',['E99A66','EC9D69','E39460','EBA16F'])
skin_inner=material('Orelha • cavidade','B86A39')
hair=pal('Cabelo castanho',['42291F','4B3024','56372A','3B251D'])
beard=pal('Barba castanha',['45291B','4C2E1E','3D2519'])
ivory=pal('Esclera quente',['CDB093','D8BBA0','C3A283'])
iris=material('Olhos • café escuro','25190F',.70)
glint=material('Olhos • reflexos quadrados','FFF0DD',.45)
oral=material('Boca • interior','542B20')
teeth=material('Dentes • marfim','EEDCC7')
lip=material('Lábio inferior','C77B4A')
olive=pal('Camisa oliva',['635D2D','676032','5C5728','6C6533'])
collar=pal('Gola oliva',['5C5628','6E6632','49451E'])
navy=pal('Calça azul ardósia',['39364C','3E3B52','333145','413E55'])
black=pal('Tênis carvão',['262326','302A2B','211F22'])
sole=pal('Solas marfim',['DED0BF','E8DACA','D3C3B1'])
cordmat=material('Cordão preto','211C18')
gold=material('Cruz dourada','E8AF16',.42,.55)
basemat=pal('Base grafite',['343039','45404B','2C2930'])
floormat=material('Chão berinjela','302B35')

def weights(ob,per_vertex):
    groups={}
    for i,dd in enumerate(per_vertex):
        total=sum(dd.values())
        if not total: continue
        for name,value in dd.items():
            if value<=0: continue
            if name not in groups:
                groups[name]=ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
            groups[name].add([i],value/total,'REPLACE')

def mesh(name,verts,faces,mats,bone='head',ws=None,head=False,collection=geo,variant=False):
    me=bpy.data.meshes.new(name+' • malha')
    me.from_pydata(verts,[],faces); me.update()
    # Consistent outward normals on closed solids (including curved plaques).
    bm=bmesh.new(); bm.from_mesh(me)
    if bm.edges and all(len(e.link_faces)==2 for e in bm.edges):
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(me)
    bm.free()
    ob=bpy.data.objects.new(name,me); collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    for p in me.polygons:
        p.use_smooth=False
        if variant and len(mats)>1: p.material_index=rng.choices(range(len(mats)),[12]+[1]*(len(mats)-1))[0]
    if collection==geo:
        all_mesh.append(ob)
        weights(ob,ws if ws is not None else [{bone:1} for _ in verts])
    if head: head_objs.append(ob)
    return ob

def rect(wx,dy,b):
    return [(-wx+b,-dy),(wx-b,-dy),(wx,-dy+b),(wx,dy-b),
            (wx-b,dy),(-wx+b,dy),(-wx,dy-b),(-wx,-dy+b)]

def loft(name,rings,mats,bone='head',ring_weights=None,head=False,tri=False,caps=True,collection=geo):
    n=len(rings[0]); verts=[tuple(p) for ring in rings for p in ring]
    fs=[]
    if caps: fs.append(tuple(reversed(range(n))))
    for j in range(len(rings)-1):
        for i in range(n):
            a=j*n+i; b=j*n+(i+1)%n; c=(j+1)*n+(i+1)%n; d=(j+1)*n+i
            if tri and (i+j)%3==0: fs.extend([(a,b,c),(a,c,d)])
            else: fs.append((a,b,c,d))
    if caps: fs.append(tuple((len(rings)-1)*n+i for i in range(n)))
    ws=None if ring_weights is None else [dd for dd in ring_weights for _ in range(n)]
    return mesh(name,verts,fs,mats,bone,ws,head,collection,True)

def box(name,center,dims,bev,mats,bone):
    # Beveled rectangular mesh, with real side and back surfaces.
    cx,cy,cz=center; wx,dy,hz=(v/2 for v in dims)
    rr=[]
    for z,k in [(cz-hz,1-bev/max(wx,dy)),(cz-hz+bev,1),(cz+hz-bev,1),(cz+hz,1-bev/max(wx,dy))]:
        rr.append([(cx+x,cy+y,z) for x,y in rect(wx*k,dy*k,min(bev,wx*k*.45,dy*k*.45))])
    return loft(name,rr,mats,bone)

def tube(name,points,radii,mats,bone,ring_weights=None,sides=8):
    rr=[]
    for j,p in enumerate(points):
        p=Vector(p)
        tangent=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)])).normalized()
        u=tangent.cross(Vector((0,1,0)))
        if u.length<.01: u=tangent.cross(Vector((1,0,0)))
        u.normalize(); v=tangent.cross(u).normalized()
        rad=radii[j]
        if isinstance(rad,(int,float)): rad=(rad,rad)
        rr.append([tuple(p+u*(math.cos(2*math.pi*i/sides+math.pi/8)*rad[0])+v*(math.sin(2*math.pi*i/sides+math.pi/8)*rad[1])) for i in range(sides)])
    return loft(name,rr,mats,bone,ring_weights)

def bone(name,a,b,parent=None,connect=False): bones[name]=(tuple(a),tuple(b),parent,connect)

def fy(x,z): return -1.30+.50*(abs(x)/1.80)**2.5+.022*(z-5.7)**2
def plaque(name,poly,mats,offset=.05,thickness=.04,bone='head',head=True):
    vv=[(x,fy(x,z)-offset,z) for x,z in poly]
    vv.extend((x,fy(x,z)-offset+thickness,z) for x,z in poly)
    n=len(poly); fs=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    fs.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return mesh(name,vv,fs,mats,bone,head=head)

# A complete, rounded-cube skull. Eye sockets continue into recessed cups.
cols=[-1,-.778,-.622,-.311,-.139,.139,.311,.622,.778,1]
rows=[(3.48,.68),(3.69,1.20),(3.95,1.54),(4.25,1.74),(4.65,1.80),
      (4.94,1.80),(5.20,1.80),(5.52,1.80),(5.85,1.79),(6.30,1.74),
      (6.85,1.50),(7.17,1.12),(7.37,.55)]
vv=[]
for j,(z,w) in enumerate(rows):
    for i,t in enumerate(cols):
        zz=z
        if j==5 and i in (1,4,5,8): zz=4.97
        if j==7:
            if i in (1,8): zz=5.30
            elif i in (4,5): zz=5.31
            elif i in (2,3,6,7): zz=5.54
        x=t*w
        # The skin crown stays underneath the independent hair volume.
        if zz>7.10: zz=7.10+(zz-7.10)*.26
        vv.append((x,fy(x,zz),zz))
ff=[]
for j in range(len(rows)-1):
    for i in range(9):
        if j in (5,6) and i in (1,2,3,5,6,7): continue
        a=j*10+i; b=a+1; c=a+11; d=a+10
        if j in (8,9,10) and (i+j)%3==0: ff.extend([(a,b,c),(a,c,d)])
        else: ff.append((a,b,c,d))
eye_loops=[]
for start in (1,5):
    idx=[50+start+k for k in range(4)]+[60+start+3,70+start+3,70+start+2,70+start+1,70+start,60+start]
    loop=[Vector(vv[i]) for i in idx]; eye_loops.append(loop)
    cx=(loop[0].x+loop[3].x)/2
    last=idx
    for factor,dep in [(.97,.08),(.65,.39)]:
        ids=[]
        for p in loop:
            q=Vector((cx+(p.x-cx)*factor,p.y+dep,5.20+(p.z-5.20)*factor))
            ids.append(len(vv)); vv.append(tuple(q))
        for i in range(10): ff.append((last[i],last[(i+1)%10],ids[(i+1)%10],ids[i]))
        last=ids
    ff.append(tuple(reversed(last)))
# Side/back rings share the front edge coordinates, forming a real skull.
side_ids=[]
for z,w in rows:
    if z>7.10: z=7.10+(z-7.10)*.26
    ds=max(.25,min(1,w/1.5))
    ring=[(-w,fy(w,z),z),(-w-.04,-.30,z),(-w-.04,1.22*ds,z),(-w+.21*ds,1.47*ds,z),
          (0,1.50*ds,z),(w-.21*ds,1.47*ds,z),(w+.04,1.22*ds,z),(w+.04,-.30,z),(w,fy(w,z),z)]
    ids=[]
    for p in ring: ids.append(len(vv)); vv.append(p)
    side_ids.append(ids)
for j in range(len(rows)-1):
    for i in range(8):
        a,b,c,d=side_ids[j][i],side_ids[j][i+1],side_ids[j+1][i+1],side_ids[j+1][i]
        ff.append((d,c,b,a))
ff.extend([tuple(reversed(side_ids[0]+list(range(9,-1,-1))))])
# Integrate the beard into the actual cheek and jaw topology. It is a region of
# the rounded skull surface, not a separate front-facing panel.
beard_region=[(0,4.72),(.46,4.75),(.87,4.65),(.97,4.48),(.97,4.18),(1.64,4.16),(1.74,4.25),
 (1.54,3.95),(1.20,3.69),(.68,3.48),(-.68,3.48),(-1.20,3.69),(-1.54,3.95),(-1.74,4.25),
 (-1.64,4.16),(-.97,4.18),(-.97,4.48),(-.87,4.65),(-.46,4.75)]
beard_skin=[(0,4.44),(.35,4.46),(.73,4.45),(.83,4.36),(.82,4.14),(.61,3.93),(.27,3.91),
 (.26,4.00),(-.26,4.00),(-.27,3.91),(-.61,3.93),(-.82,4.14),(-.83,4.36),(-.73,4.45),(-.35,4.46)]
def point_inside(p,poly):
    hit=False; x,z=p
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)]
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]: hit=not hit
    return hit
lower_outline=[(vv[i][0],vv[i][2]) for i in range(10)]
lower_outline += [(vv[j*10+9][0],vv[j*10+9][2]) for j in range(1,6)]
lower_outline += [(vv[50+i][0],vv[50+i][2]) for i in range(8,-1,-1)]
lower_outline += [(vv[j*10][0],vv[j*10][2]) for j in range(4,0,-1)]
cdtpts=[]; cdtmap={}; cdtedges=[]
for poly in [lower_outline,beard_region,beard_skin]:
    ids=[]
    for p in poly:
        if p not in cdtmap: cdtmap[p]=len(cdtpts); cdtpts.append(Vector(p))
        ids.append(cdtmap[p])
    cdtedges.extend((ids[i],ids[(i+1)%len(ids)]) for i in range(len(ids)))
cv,ce,cf,*_=delaunay_2d_cdt(cdtpts,cdtedges,[],0,.00001,False)
ff=[f for f in ff if max(f)>=60]
lower_start=len(ff); off=len(vv)
vv.extend((p.x,fy(p.x,p.y),p.y) for p in cv)
lower_brown=[]
for f in cf:
    cent=sum((cv[i] for i in f),Vector((0,0)))/len(f)
    if not point_inside(cent,lower_outline): continue
    ff.append(tuple(off+i for i in f))
    lower_brown.append(point_inside(cent,beard_region) and not point_inside(cent,beard_skin))
skull=mesh('Cabeça • volume e órbitas',vv,ff,skin+beard,head=True)
for p,brown in zip(list(skull.data.polygons)[lower_start:],lower_brown):
    p.material_index=4 if brown else 0
for p in skull.data.polygons:
    if p.center.z<3.91 or (p.center.y>-.25 and p.center.z<4.27): p.material_index=4
    if abs(p.center.x)>1.60 and -.85<p.center.y<.35 and p.center.z<5.4: p.material_index=4
# Weld shared edges, while keeping the eye-socket loops.
bm=bmesh.new(); bm.from_mesh(skull.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(skull.data); bm.free()

# Faceted lens-shaped eyeballs, curved pupils and separate physical reflections.
for side,loop in zip(('R','L'),eye_loops):
    cx=(loop[0].x+loop[3].x)/2; cz=5.20
    rr=[]
    for fac,depth in [(1,.005),(.72,-.065),(.25,-.105)]:
        rr.append([(cx+(p.x-cx)*fac,fy(cx+(p.x-cx)*fac,cz+(p.z-cz)*fac)+depth,cz+(p.z-cz)*fac) for p in loop])
    eye=loft('Olho.'+side+' • globo facetado',rr,ivory,'eye.'+side,head=True)
    # Seal the back of the lens with a hemisphere-like cup.
    backring=[(cx+(p.x-cx)*.65,p.y+.30,cz+(p.z-cz)*.65) for p in loop]
    loft('Olho.'+side+' • volume posterior',[[tuple(p) for p in loop],backring],ivory,'eye.'+side,head=True)
    irisshape=[(-.24,.30),(.24,.30),(.32,.18),(.33,-.16),(.25,-.26),(-.25,-.26),(-.33,-.16),(-.32,.18)]
    ip=[(cx+x,fy(cx+x,cz+z)-.14,cz+z) for x,z in irisshape]
    ip.append((cx,fy(cx,cz)-.155,cz))
    mesh('Pupila.'+side+' • contorno arredondado',ip,[(i,8,(i+1)%8) for i in range(8)],[iris],'eye.'+side,head=True)
    hx=cx-.09; hz=cz+.14; hw=.155
    gp=[(x,fy(x,z)-.18,z) for x,z in [(hx-hw/2,hz-hw/2),(hx+hw/2,hz-hw/2),(hx+hw/2,hz+hw/2),(hx-hw/2,hz+hw/2)]]
    mesh('Reflexo.'+side+' • quadrado',gp,[(0,1,2,3)],[glint],'eye.'+side,head=True)
    top=[loop[k] for k in (8,7,6,5)]
    lidpoly=[(p.x,p.z) for p in top]+[(p.x,p.z+.048) for p in reversed(top)]
    plaque('Pálpebra.'+side+' • bordo superior',lidpoly,beard,.025,.025)
    # Skin lid retracts into the brow at rest and closes with a shape key.
    lv=[(p.x,fy(p.x,p.z)-.045,p.z+.025) for p in top]
    lv += [(p.x,fy(p.x,p.z)-.05,p.z-.005) for p in top]
    lid=mesh('Piscar.'+side+' • pálpebra móvel',lv,[(0,1,5,4),(1,2,6,5),(2,3,7,6)],skin,head=True)
    lid.shape_key_add(name='Basis')
    close=lid.shape_key_add(name='Fechar')
    for i in range(4):
        close.data[i].co.y=fy(close.data[i].co.x,5.2)-.30
        close.data[i+4].co.z=4.91
        close.data[i+4].co.y=fy(close.data[i+4].co.x,5.2)-.31
    blink.append(lid)

browpoly=[(-1.40,5.63),(-1.24,5.87),(-.61,5.88),(-.22,5.77),(-.20,5.55),(-.62,5.66),(-1.08,5.66)]
plaque('Sobrancelha.R • esculpida',browpoly,beard,.085,.08,'brow.R')
plaque('Sobrancelha.L • esculpida',[(-x+.20,z-.05) for x,z in reversed(browpoly)],beard,.085,.08,'brow.L')

# Bridge, tip and undersurface form an actual projecting low-poly nose.
nv=[(-.16,-1.28,5.39),(.16,-1.28,5.39),(-.20,-1.48,5.05),(.20,-1.48,5.05),
    (-.34,-1.80,4.80),(.34,-1.80,4.80),(-.27,-1.65,4.65),(.27,-1.65,4.65),
    (-.49,-1.64,4.78),(.49,-1.64,4.78),(-.29,-1.25,4.95),(.29,-1.25,4.95)]
nf=[(0,1,3,2),(2,3,5,4),(4,5,7,6),(0,2,4,8,10),(1,11,9,5,3),
    (8,4,6),(9,7,5),(8,6,7,9),(6,10,11,7),(8,10,0),(9,1,11)]
nose=mesh('Nariz • ponte, ponta e asas',nv,nf,skin,head=True)
for p,i in zip(nose.data.polygons,[0,1,1,0,2,0,1,2,2,2]): p.material_index=i

# Both ears: rounded rectangular rims and inset bowls, oriented anatomically.
eshape=[(-.23,.50),(.19,.50),(.34,.30),(.34,-.34),(.16,-.54),(-.22,-.51),(-.35,-.27),(-.35,.25)]
for sign,side in [(-1,'R'),(1,'L')]:
    c=Vector((sign*1.92,.18,4.66)); T=Vector((.66,sign*.75,0)); N=Vector((sign*.75,-.66,0))
    rings=[]
    for factor,depth in [(1,.02),(.75,.17),(.59,.02)]:
        rings.append([tuple(c+T*(x*factor)+Vector((0,0,z*factor))+N*depth) for x,z in eshape])
    ear=loft('Orelha.'+side+' • aro e concha',rings,skin+[skin_inner],head=True)
    for p in ear.data.polygons:
        if p.index>=9: p.material_index=4
    back=[tuple(c+T*x+Vector((0,0,z))-N*.12) for x,z in eshape]
    loft('Orelha.'+side+' • volume posterior',[back,rings[0]],skin,head=True)

# Full scalp shell, fitted to the skull. All sides and the nape are modeled.
def headwidth(z):
    for j in range(len(rows)-1):
        if rows[j][0]<=z<=rows[j+1][0]:
            t=(z-rows[j][0])/(rows[j+1][0]-rows[j][0])
            return rows[j][1]*(1-t)+rows[j+1][1]*t
    return rows[0][1] if z<rows[0][0] else max(.15,rows[-1][1]-(z-7.37)*1.6)
def outline_at(deg,z):
    d=abs(deg); sign=1 if deg>=0 else -1; w=headwidth(z)+.075
    keys=[(0,(0,fy(0,z)-.065)),(65,(w,fy(w-.075,z)-.06)),(80,(w+.04,-.30)),
          (120,(w+.04,1.23)),(135,(w-.17,1.52)),(180,(0,1.55))]
    for j in range(len(keys)-1):
        if keys[j][0]<=d<=keys[j+1][0]:
            t=(d-keys[j][0])/(keys[j+1][0]-keys[j][0]); a=Vector(keys[j][1]); b=Vector(keys[j+1][1])
            p=a.lerp(b,t); return (sign*p.x,p.y)
def lineheight(deg):
    d=abs(deg)
    vals=[(0,7.13),(15,7.17),(30,7.07),(45,6.92),(60,6.35),(75,5.54),(90,4.63),(105,4.26),(120,4.07),(135,3.98),(180,3.97)]
    for j in range(len(vals)-1):
        if vals[j][0]<=d<=vals[j+1][0]:
            t=(d-vals[j][0])/(vals[j+1][0]-vals[j][0]); zz=vals[j][1]*(1-t)+vals[j+1][1]*t
            if deg<0 and 20<d<75: zz+=.17*math.sin((d-20)/55*math.pi)
            return min(7.17,zz)
angles=[-180+i*15 for i in range(24)]
hair_v=[]; hair_f=[]
# A scalp sampled at the skull's actual horizontal sections. Clipping a fitted
# surface avoids the long diagonal hair faces cutting through the temples.
zs=[3.88,4.25,4.65,5.20,5.85,6.30,6.85,7.17,7.37]
def scalp_vertex(deg,z):
    x,y=outline_at(deg,min(z,7.17))
    if z>7.17:
        fac=1-.40*(z-7.17)
        x*=fac
        if y<.1: y=(y-.1)*fac+.1
    # The offset also protects the centers of broad side planes.
    x*=1.025
    if y<0: y-=.025
    elif y>0: y+=.025
    return Vector((x,y,z))
def clipped(poly):
    out=[]
    for j,(p,val) in enumerate(poly):
        q,v2=poly[(j+1)%len(poly)]
        if val>=0: out.append(p)
        if (val>=0)!=(v2>=0): out.append(p.lerp(q,val/(val-v2)))
    return out
for j in range(len(zs)-1):
    for i,a in enumerate(angles):
        b=angles[(i+1)%24]
        poly=[(scalp_vertex(a,zs[j]),zs[j]-lineheight(a)),
              (scalp_vertex(b,zs[j]),zs[j]-lineheight(b)),
              (scalp_vertex(b,zs[j+1]),zs[j+1]-lineheight(b)),
              (scalp_vertex(a,zs[j+1]),zs[j+1]-lineheight(a))]
        out=clipped(poly)
        if len(out)>2:
            k=len(hair_v); hair_v.extend(tuple(p) for p in out)
            hair_f.append(tuple(range(k,k+len(out))))
# Crown transitions are fully above the skull.
crowns=[]
for level,z,scale in [(0,7.37,1),(1,7.57,.62),(2,7.68,.28)]:
    rr=[]
    for a in angles:
        if level==0: p=scalp_vertex(a,z)
        else:
            x,y=outline_at(a,7.17)
            x*=.70 if level==1 else .30
            y=(y-.1)*(.90 if level==1 else .30)+.1
            p=Vector((x,y,z))
        rr.append(tuple(p))
    crowns.append(rr)
k=len(hair_v)
hair_v.extend(p for rr in crowns for p in rr)
for j in range(2):
    for i in range(24):
        a=k+j*24+i; b=k+j*24+(i+1)%24; c=k+(j+1)*24+(i+1)%24; d=k+(j+1)*24+i
        hair_f.append((a,b,c,d))
hair_f.append(tuple(k+48+i for i in range(24)))
hair_ob=mesh('Cabelo • touca, têmporas e nuca',hair_v,hair_f,hair,head=True)
me=hair_ob.data; bm=bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free()
for p in me.polygons:
    if p.center.z>7.0: p.material_index=1 if p.normal.z<.5 else 2
    elif p.normal.y>0: p.material_index=0

# Sculpted beard and moustache; beard continues under the jaw and around the sides.
outer=[(0,4.72),(.46,4.75),(.87,4.65),(.97,4.48),(.97,4.18),(1.64,4.16),(1.61,3.98),(1.19,3.69),(.63,3.50),(0,3.44),
       (-.63,3.50),(-1.19,3.69),(-1.61,3.98),(-1.64,4.16),(-.97,4.18),(-.97,4.48),(-.87,4.65),(-.46,4.75)]
inner=[(0,4.44),(.35,4.46),(.73,4.45),(.83,4.36),(.82,4.14),(.61,3.93),(.27,3.91),(.26,4.00),(.13,4.00),(0,4.00),
       (-.13,4.00),(-.26,4.00),(-.27,3.91),(-.61,3.93),(-.82,4.14),(-.83,4.36),(-.73,4.45),(-.35,4.46)]
# Cheek beard, sideburns and goatee are integrated into Cabeça • volume e órbitas.
must=[(.025,4.45),(.055,4.64),(.35,4.68),(.69,4.60),(.82,4.46),(.68,4.39),(.30,4.42)]
plaque('Bigode • lobo direito',[(-x,z) for x,z in reversed(must)],beard,.155,.09)
plaque('Bigode • lobo esquerdo',must,beard,.155,.09)
mouthpoly=[(-.75,4.42),(-.48,4.36),(0,4.33),(.48,4.36),(.75,4.42),(.62,4.22),(.39,4.13),(0,4.10),(-.39,4.13),(-.62,4.22)]
plaque('Boca • abertura do sorriso',mouthpoly,[oral],.042,.025)
toothcols=[(-.60,4.36,4.28),(-.44,4.33,4.20),(0,4.30,4.17),(.44,4.33,4.20),(.60,4.36,4.28)]
tv=[]
for depth in (.115,.085):
    for x,top,bot in toothcols: tv.extend([(x,fy(x,top)-depth,top),(x,fy(x,bot)-depth,bot)])
tf=[]
for i in range(4):
    a=2*i; tf.extend([(a,a+2,a+3,a+1),(a+10,a+11,a+13,a+12),
                     (a,a+10,a+12,a+2),(a+1,a+3,a+13,a+11)])
tf.extend([(0,1,11,10),(8,18,19,9)])
mesh('Dentes • arco curvo',tv,tf,[teeth],head=True)
plaque('Lábio • plano inferior',[(-.44,4.12),(0,4.08),(.44,4.12),(.30,4.07),(0,4.045),(-.30,4.07)],[lip],.05,.015)

# Head tilt is a rigid 3D transform, common to every head component.
HEAD_ROT=Matrix.Rotation(math.radians(6),3,'Y'); HEAD_PIVOT=Vector((0,0,5.50))
def hp(p): return HEAD_PIVOT+HEAD_ROT@(Vector(p)-HEAD_PIVOT)
for ob in head_objs:
    if ob.data.shape_keys:
        for key in ob.data.shape_keys.key_blocks:
            for v in key.data: v.co=hp(v.co)
        for v,p in zip(ob.data.vertices,ob.data.shape_keys.key_blocks['Basis'].data): v.co=p.co
    else:
        for v in ob.data.vertices: v.co=hp(v.co)
    ob.data.update()

# Torso: deformation rings, true side and back panels.
torso_r=[]; torso_ws=[]
for z,wx,dy in [(1.67,1.02,.56),(1.83,1.04,.57),(2.13,1.04,.57),(2.49,1.00,.57),(2.84,.96,.54),(3.13,.89,.48),(3.40,.49,.36)]:
    torso_r.append([(x,y+.06,z) for x,y in rect(wx,dy,.18)])
    if z<1.85: dd={'pelvis':.85,'spine':.15}
    elif z<2.3: dd={'pelvis':.15,'spine':.85}
    elif z<2.7: dd={'spine':.55,'chest':.45}
    else: dd={'chest':1}
    torso_ws.append(dd)
loft('Camisa • tronco com anéis de deformação',torso_r,olive,'chest',torso_ws,tri=False)
neckpts=[(0,.02,3.05),(0,.02,3.30),(0,.02,3.60),(0,.02,3.82)]
tube('Pescoço • anéis de articulação',neckpts,[.40,.42,.45,.46],skin,'neck',
     [{'chest':.6,'neck':.4},{'neck':1},{'neck':.6,'head':.4},{'head':1}],8)
mesh('Decote • abertura em V',[(-.46,-.48,3.46),(.46,-.48,3.46),(0,-.535,2.96)],[(0,1,2)],skin,'chest')
for sign,side in [(-1,'R'),(1,'L')]:
    cv=[(sign*.48,-.50,3.45),(sign*.76,-.52,3.14),(sign*.66,-.61,3.00),(sign*.32,-.62,3.04),
        (sign*.04,-.60,2.72),(sign*.10,-.63,2.92)]
    mesh('Gola.'+side+' • dobra em relevo',cv,[(0,1,2,3),(0,3,5),(3,4,5)],collar,'chest')

# Complete arms with several loops around elbows and wrists.
arm_pts={
 'R':[(-.98,.01,3.20),(-1.16,.03,2.91),(-1.32,.04,2.61),(-1.37,.02,2.48),(-1.68,-.35,2.48),(-2.01,-.773,2.552)],
 'L':[(.98,.02,3.20),(1.12,.02,2.82),(1.24,.03,2.44),(1.27,.01,2.30),(1.32,-.02,2.10),(1.35,-.04,1.89)]}
for side,pts in arm_pts.items():
    ws=[{'upper_arm.'+side:1},{'upper_arm.'+side:1},{'upper_arm.'+side:.7,'forearm.'+side:.3},
        {'upper_arm.'+side:.35,'forearm.'+side:.65},{'forearm.'+side:1},{'forearm.'+side:.65,'hand.'+side:.35}]
    tube('Braço.'+side+' • cotovelo e punho',pts,[.30,.29,.275,.27,.24,.215],skin,'upper_arm.'+side,ws,8)
    p0=Vector(pts[0]); p1=Vector(pts[1]); p2=p0.lerp(Vector(pts[2]),.65)
    tube('Manga.'+side+' • curta e articulada',[p0,p1,p2],[.40,.39,.36],olive,'upper_arm.'+side,
         [{'chest':.40,'upper_arm.'+side:.60},{'upper_arm.'+side:1},{'upper_arm.'+side:1}],8)

# Articulated, genuinely curled fingers. Each phalanx has its own bone and weights.
CAM_PHI=math.radians(30)
R=Vector((math.cos(CAM_PHI),-math.sin(CAM_PHI),0)); D=Vector((math.sin(CAM_PHI),math.cos(CAM_PHI),0)); Z=Vector((0,0,1))
hand_centers={}
def make_hand(side,center,scale,X,Y,A):
    c=Vector(center); hand_centers[side]=c
    def pt(p): return c+(X*p[0]+Y*p[1]+A*p[2])*scale
    # The palm is a closed beveled solid in the local hand frame.
    prs=[]
    palm_sections=[(-.55,.16,.21),(-.40,.255,.40),(-.16,.28,.45),(.30,.255,.43),(.45,.19,.36)] if side=='R' else [(-.40,.20,.33),(-.28,.255,.43),(.20,.255,.43),(.34,.19,.36)]
    for xx,wy,wz in palm_sections:
        ring=[pt((xx,y,z-(.09 if z<0 and side=='R' else 0))) for y,z in rect(wy,wz,.065)]
        prs.append(ring)
    palm=loft('Mão.'+side+' • palma',prs,skin,'hand.'+side)
    for index,zz in enumerate((.30,.09,-.14,-.33)):
        name=('index','middle','ring','pinky')[index]
        length=(1.0,1.04,.97,.83)[index]
        off=.20 if side=='R' else 0
        path=[(.25+off,.115,zz),(.48*length+off,.065,zz),(.55*length+off,-.18,zz-.018),(.17+off,-.32,zz-.035)]
        world=[pt(p) for p in path]
        for j in range(3):
            bn=f'{name}.{j+1:02d}.{side}'
            parent='hand.'+side if j==0 else f'{name}.{j:02d}.{side}'
            bone(bn,world[j],world[j+1],parent,j>0)
        # Add intermediate loops so the bends are not a single sharp hinge.
        pp=[]; rads=[]; ww=[]
        for j in range(3):
            a=world[j]; b=world[j+1]
            for t in (0,.45):
                pp.append(a.lerp(b,t)); rads.append((.116 if index<3 else .10)*scale)
                bn=f'{name}.{j+1:02d}.{side}'
                ww.append({bn:1} if j==0 or t>.01 else {f'{name}.{j:02d}.{side}':.45,bn:.55})
        pp.append(world[-1]); rads.append((.10 if index<3 else .085)*scale); ww.append({f'{name}.03.{side}':1})
        tube('Dedo.'+side+' • '+name,pp,rads,skin,f'{name}.01.{side}',ww,6)
    # Thumb is raised on the near hand, and rests beside the distant palm.
    local=[(.27,.02,.36),(.46,-.03,.62),(.52,-.035,.88),(.48,-.015,1.05)]
    if side=='L': local=[(-.22,.00,.34),(.02,-.08,.49),(.27,-.12,.48),(.37,-.14,.36)]
    world=[pt(p) for p in local]
    for j in range(3): bone(f'thumb.{j+1:02d}.{side}',world[j],world[j+1],'hand.'+side if j==0 else f'thumb.{j:02d}.{side}',j>0)
    tube('Polegar.'+side+' • três falanges',world,[.18*scale,.17*scale,.15*scale,.12*scale],skin,'thumb.01.'+side,
         [{'hand.'+side:.35,'thumb.01.'+side:.65},{'thumb.01.'+side:.5,'thumb.02.'+side:.5},
          {'thumb.02.'+side:.5,'thumb.03.'+side:.5},{'thumb.03.'+side:1}],7)
make_hand('R',(-1.80,-.893,2.752),1.0,R,D,Z)
make_hand('L',(1.34,-.12,1.67),.64,-Z,D,R)

# Trousers follow a real pelvis and independent articulated legs.
box('Calça • cintura e quadril',(0,.10,1.68),(1.78,.94,.44),.10,navy,'pelvis')
for sign,side in [(-1,'R'),(1,'L')]:
    pp=[(sign*.53,.10,1.74),(sign*.60,.10,1.50),(sign*.67,.10,1.20),(sign*.70,.10,1.08),(sign*.75,.11,.95),(sign*.80,.12,.76)]
    wr=[{'pelvis':.50,'thigh.'+side:.50},{'thigh.'+side:1},{'thigh.'+side:.75,'shin.'+side:.25},
        {'thigh.'+side:.4,'shin.'+side:.6},{'shin.'+side:1},{'shin.'+side:1}]
    rings=[]
    for j,p in enumerate(pp):
        wx=[.44,.46,.47,.46,.44,.40][j]; dy=[.46,.46,.44,.44,.43,.39][j]
        rings.append([(p[0]+x,p[1]+y,p[2]) for x,y in rect(wx,dy,.12)])
    loft('Calça.'+side+' • joelho articulado',rings,navy,'thigh.'+side,wr)
    xc=sign*.82; cy=.10
    rr=[]
    for z,wx,dy in [(.31,.50,.65),(.49,.50,.65),(.51,.47,.62)]:
        rr.append([(xc+x,cy+y,z) for x,y in rect(wx,dy,.11)])
    loft('Tênis.'+side+' • sola branca',rr,sole,'foot.'+side)
    rr=[]
    for z,wx,dy in [(.50,.475,.615),(.65,.46,.59),(.80,.34,.43)]:
        rr.append([(xc+x,cy+y,z) for x,y in rect(wx,dy,.11)])
    loft('Tênis.'+side+' • cabedal',rr,black,'foot.'+side)

# Necklace is independent geometry, attached to the upper torso.
cu=bpy.data.curves.new('Cordão • geometria','CURVE'); cu.dimensions='3D'; cu.resolution_u=1; cu.bevel_depth=.023; cu.bevel_resolution=0
sp=cu.splines.new('POLY')
points=[(-.44,-.44,3.50),(-.33,-.53,3.28),(-.07,-.64,3.03),(.05,-.65,3.01),(.29,-.54,3.27),(.43,-.44,3.50)]
sp.points.add(len(points)-1)
for p,co in zip(sp.points,points): p.co=(*co,1)
cord=bpy.data.objects.new('Colar • cordão',cu); geo.objects.link(cord); cu.materials.append(cordmat)
bpy.ops.object.select_all(action='DESELECT'); cord.select_set(True); bpy.context.view_layer.objects.active=cord
bpy.ops.object.convert(target='MESH'); cord=bpy.context.object; all_mesh.append(cord)
weights(cord,[{'neck':max(0,min(.5,(v.co.z-3.20)*1.6)),'chest':1-max(0,min(.5,(v.co.z-3.20)*1.6))} for v in cord.data.vertices])
cross=[(-.045,3.03),(.045,3.03),(.045,2.90),(.135,2.90),(.135,2.82),(.045,2.82),(.045,2.65),
       (-.045,2.65),(-.045,2.82),(-.135,2.82),(-.135,2.90),(-.045,2.90)]
cv=[(x,-.71,z) for x,z in cross]+[(x,-.655,z) for x,z in cross]
n=len(cross); cf=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh('Colar • crucifixo sólido',cv,cf,[gold],'chest')

# Build a useful FK armature. The reference gesture is the neutral pose.
bone('root',(0,0,.31),(0,0,1.0))
bone('pelvis',(0,.10,1.60),(0,.08,2.03),'root')
bone('spine',(0,.08,2.03),(0,.04,2.62),'pelvis',True)
bone('chest',(0,.04,2.62),(0,.01,3.20),'spine',True)
bone('neck',(0,.01,3.20),(0,.01,3.59),'chest',True)
bone('head',(0,.01,3.59),hp((0,0,6.1)),'neck',True)
for side in ('R','L'):
    pts=arm_pts[side]
    bone('clavicle.'+side,(0,.01,3.20),pts[0],'chest')
    bone('upper_arm.'+side,pts[0],pts[3],'clavicle.'+side,True)
    bone('forearm.'+side,pts[3],pts[-1],'upper_arm.'+side,True)
    bone('hand.'+side,pts[-1],hand_centers[side],'forearm.'+side,True)
    sg=-1 if side=='R' else 1
    bone('thigh.'+side,(sg*.53,.10,1.74),(sg*.70,.10,1.08),'pelvis')
    bone('shin.'+side,(sg*.70,.10,1.08),(sg*.80,.12,.61),'thigh.'+side,True)
    bone('foot.'+side,(sg*.80,.12,.61),(sg*.82,-.52,.50),'shin.'+side,True)
    ex=sg*.825
    bone('eye.'+side,hp((ex,-.97,5.20)),hp((ex,-1.45,5.20)),'head')
    bone('brow.'+side,hp((sg*.80,-1.0,5.73)),hp((sg*.80,-1.35,5.73)),'head')
arm=bpy.data.armatures.new('Personagem • esqueleto FK')
rig=bpy.data.objects.new('RIG • Personagem',arm); rigcol.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
pending=dict(bones)
while pending:
    for name,(a,b,parent,connect) in list(pending.items()):
        if parent and parent not in arm.edit_bones: continue
        eb=arm.edit_bones.new(name); eb.head=a; eb.tail=b
        if (eb.tail-eb.head).length<.025: eb.tail.z+=.07
        if parent:
            eb.parent=arm.edit_bones[parent]
            eb.use_connect=connect and (eb.head-eb.parent.tail).length<.01
        del pending[name]
bpy.ops.object.mode_set(mode='OBJECT')
arm.display_type='STICK'; rig.show_in_front=False
rig['piscar_R']=0.0; rig['piscar_L']=0.0
for side in ('R','L'):
    rig.id_properties_ui('piscar_'+side).update(min=0,max=1,description='0 = aberto; 1 = fechado')
for lid,side in zip(blink,('R','L')):
    drv=lid.data.shape_keys.key_blocks['Fechar'].driver_add('value').driver
    var=drv.variables.new(); var.name='blink'; var.type='SINGLE_PROP'; var.targets[0].id=rig; var.targets[0].data_path='["piscar_'+side+'"]'
    drv.expression='blink'
for ob in all_mesh:
    ob.parent=rig
    mod=ob.modifiers.new('Deformação • rig FK','ARMATURE'); mod.object=rig; mod.use_deform_preserve_volume=True
for pb in rig.pose.bones: pb.rotation_mode='XYZ'
rig['guia']='Pose Mode: root move tudo; pelvis/spine/chest/neck/head; braços/pernas FK; 3 falanges por dedo; eye.R/L para olhar; brow.R/L para expressão. Piscar: propriedades personalizadas do rig.'
rig['pose_neutra']='Gesto de positivo da referência. Rest pose em gesto, sem chaves de animação impostas.'

# Faceted circular base and lighting studio, separate from the animated character.
rr=[]
for z,r in [(.04,1.99),(.10,2.02),(.27,1.96),(.30,1.86)]:
    rr.append([(r*math.cos(2*math.pi*i/20),r*math.sin(2*math.pi*i/20),z) for i in range(20)])
base=loft('Base • pedestal',rr,basemat,bone=None,collection=stage)
for p in base.data.polygons: p.material_index=1 if p.normal.z>.8 else 0
mesh('Chão',[(-200,-200,.035),(200,-200,.035),(200,200,.035),(-200,200,.035)],[(0,1,2,3)],[floormat],bone=None,collection=stage)
world=bpy.data.worlds.new('Mundo • estúdio neutro'); world.node_tree.nodes.clear()
bg=world.node_tree.nodes.new('ShaderNodeBackground'); wo=world.node_tree.nodes.new('ShaderNodeOutputWorld')
bg.inputs[0].default_value=(.19,.17,.21,1); bg.inputs[1].default_value=.50
world.node_tree.links.new(bg.outputs[0],wo.inputs[0]); s.world=world
def aim(ob,p): ob.rotation_euler=(Vector(p)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,p,energy,size,color=(1,1,1)):
    d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=size; d.color=color
    ob=bpy.data.objects.new(name,d); stage.objects.link(ob); ob.location=p; aim(ob,(0,0,4.5))
    return ob
area('Luz • principal',(-5,-8,10),1000,5,(1,.94,.88))
area('Luz • preenchimento',(5,-5,7),550,5,(1,.97,.93))
area('Luz • recorte',(-3,5,10),850,4,(.85,.88,1))
hand_light=area('Luz • preenchimento das mãos',(-4.2,-5,4.5),250,3,(1,.94,.88))
aim(hand_light,(-1.6,-.8,2.8))
# A solid-color studio floor, with a low emission floor under the lighting.
floor_bs=next(n for n in floormat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
floor_bs.inputs['Emission Color'].default_value=tuple(srgb(v/255)*1.40 for v in (42,37,47))+(1,)
floor_bs.inputs['Emission Strength'].default_value=1
phi=math.radians(30); elev=math.radians(8)
front=Vector((-math.sin(phi)*math.cos(elev),-math.cos(phi)*math.cos(elev),math.sin(elev)))
target=Vector((0,0,3.82))+R*.055
cd=bpy.data.cameras.new('Câmera • referência 3D'); cam=bpy.data.objects.new('Câmera • referência 3D',cd); stage.objects.link(cam)
cam.location=target+front*24; aim(cam,target); cd.type='ORTHO'; cd.ortho_scale=8.10; cd.lens=70; s.camera=cam
s.render.engine='CYCLES'; s.cycles.samples=40; s.cycles.use_denoising=True
s.render.resolution_x=1199; s.render.resolution_y=1312; s.render.resolution_percentage=50
s.render.image_settings.file_format='PNG'; s.render.filepath=str(OUT/'previa_3d_real.png')
s.view_settings.view_transform='Standard'; s.view_settings.look='None'; s.view_settings.exposure=-.65
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA'
            a.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT'); skull.select_set(True); bpy.context.view_layer.objects.active=skull
bpy.context.view_layer.update()
path=OUT/'personagem_3d_rig_trabalho.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
result={'scene':s.name,'meshes':len(all_mesh),'bones':len(arm.bones),'faces':sum(len(o.data.polygons) for o in all_mesh),
        'image_texture_nodes':sum(n.type=='TEX_IMAGE' for o in all_mesh for m in o.data.materials for n in m.node_tree.nodes),
        'blend':str(path),'preview':s.render.filepath}
