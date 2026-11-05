"""Character sculpted from the supplied single-view low-poly reference.
Run inside Blender. All geometry is editable; the source scene is preserved.
"""
import bpy
import math
import random
from pathlib import Path
from mathutils import Vector

OUT = Path(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\personagem')
REF = r'C:\Users\luisf\AppData\Local\Temp\codex-clipboard-78ffdffe-2512-42af-abbc-bc21782b9096.png'
OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(63)

scene = bpy.data.scenes.new('Personagem • low poly')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
char = bpy.data.collections.new('01 • PERSONAGEM')
stage = bpy.data.collections.new('02 • ESTÚDIO')
refs = bpy.data.collections.new('03 • REFERÊNCIA')
scene.collection.children.link(char)
scene.collection.children.link(stage)
scene.collection.children.link(refs)

def linear(v):
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4

def material(name, color, roughness=.85, metallic=0):
    color = color.lstrip('#')
    rgb = tuple(linear(int(color[i:i+2], 16) / 255) for i in (0, 2, 4))
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if p is None:
        p = m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        output = m.node_tree.nodes.new('ShaderNodeOutputMaterial')
        m.node_tree.links.new(p.outputs['BSDF'], output.inputs['Surface'])
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m

def palette(name, colors):
    return [material(name + ' / ' + str(i + 1), c) for i, c in enumerate(colors)]

skin = palette('Pele • âmbar', ['E99860','ED9B63','E5955D','E19057','F0A16B','D98850','E99A65'])
ear_inner = material('Orelhas • cavidade', 'BF703F')
hair = palette('Cabelo • castanho', ['3A231B','442A20','4A2D22','38231C','533227','40261D'])
beard = palette('Barba • castanho quente', ['422719','482A1B','3A2318','4F2E1D','45271A'])
white = palette('Olhos • marfim', ['CFAD8B','D6B693','DDBE9B'])
eye_black = material('Olhos • café escuro', '24180F', .53)
eye_glint = material('Olhos • reflexos quadrados', 'FFF0DD', .4)
mouth_dark = material('Sorriso • interior', '522619')
teeth = material('Sorriso • dentes marfim', 'F4E4CE', .75)
lip = material('Sorriso • lábio inferior', 'CD7848')
shirt = palette('Camisa • verde oliva', ['66602D','6A6330','605B2A','716A35','5A5427','625C2A'])
collar = palette('Gola • oliva', ['5B5525','756D35','4D4921'])
pants = palette('Calça • azul ardósia', ['343246','3A384E','302F41','414057','363448'])
shoe = palette('Tênis • carvão', ['272426','211F22','302A2A','312B2B'])
sole = palette('Tênis • sola marfim', ['DED0BE','EADCCB','CDBEAD'])
cord = material('Colar • cordão preto', '201C18', .9)
gold = material('Colar • ouro', 'E9B522', .38, .60)
gold_side = material('Colar • ouro lateral', 'A96F0B', .4, .6)
base_mat = palette('Base • grafite', ['353039','49434F','302C32'])
floor_mat = material('Fundo • berinjela', '2D2732')

def mesh(name, verts, faces, mats, collection=char, variation=False):
    me = bpy.data.meshes.new(name + ' • malha')
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    for f in me.polygons:
        f.use_smooth = False
        if variation:
            f.material_index = rng.choices(range(len(mats)), [7] + [1] * (len(mats)-1))[0]
    return ob

def relocate(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)

def rect(hx, hy, b):
    return [(-hx+b,-hy), (hx-b,-hy), (hx,-hy+b), (hx,hy-b),
            (hx-b,hy), (-hx+b,hy), (-hx,hy-b), (-hx,-hy+b)]

def loft(name, rings, mats, triangulate=False, coll=char):
    n = len(rings[0])
    verts = [v for ring in rings for v in ring]
    faces = [tuple(reversed(range(n)))]
    for j in range(len(rings)-1):
        for i in range(n):
            a,b,c,d = j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i
            if triangulate and (i+j)%3 != 1:
                faces.extend([(a,b,d), (b,c,d)])
            else:
                faces.append((a,b,c,d))
    faces.append(tuple((len(rings)-1)*n+i for i in range(n)))
    return mesh(name, verts, faces, mats, coll, True)

def box(name, center, dims, bevel, mats, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center, rotation=rotation)
    ob = bpy.context.object
    ob.name = name
    relocate(ob, char)
    ob.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = ob.modifiers.new('Cantos de um único plano', 'BEVEL')
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for m in mats:
        ob.data.materials.append(m)
    for f in ob.data.polygons:
        f.use_smooth = False
        f.material_index = rng.choices(range(len(mats)), [8]+[1]*(len(mats)-1))[0]
    return ob

def tube(name, path, radii, mats, sides=8, phase=math.pi/8):
    rings = []
    for j, p in enumerate(path):
        p = Vector(p)
        tangent = Vector(path[min(j+1,len(path)-1)]) - Vector(path[max(0,j-1)])
        tangent.normalize()
        u = tangent.cross(Vector((0,1,0)))
        if u.length < .01:
            u = tangent.cross(Vector((1,0,0)))
        u.normalize()
        v = tangent.cross(u).normalized()
        r = radii[j]
        if isinstance(r,(float,int)):
            r = (r,r)
        rings.append([tuple(p + u*(math.cos(2*math.pi*i/sides+phase)*r[0]) + v*(math.sin(2*math.pi*i/sides+phase)*r[1])) for i in range(sides)])
    return loft(name, rings, mats)

def front_y(x,z):
    return -1.30 + .30*(abs(x)/1.68)**3 + .041*(z-5.70)**2

def plaque(name, outline, mats, depth=.055, offset=.06, yfun=front_y):
    n=len(outline)
    verts=[(x,yfun(x,z)-offset,z) for x,z in outline]
    verts += [(x,yfun(x,z)-offset+depth,z) for x,z in outline]
    faces=[tuple(range(n)), tuple(reversed(range(n,2*n)))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name, verts, faces, mats, variation=True)

# Sculpted skin shell: broad planes, real openings around both eyes.
columns=[-1,-.77,-.63,-.29,-.105,.105,.29,.63,.77,1]
rows=[(3.57,.62),(3.76,1.10),(4.04,1.42),(4.38,1.56),(4.78,1.64),
      (5.15,1.66),(5.45,1.68),(5.75,1.65),(6.13,1.63),(6.65,1.54),
      (7.10,1.28),(7.37,.76),(7.45,.15)]
verts=[]
for j,(z,w) in enumerate(rows):
    for i,u in enumerate(columns):
        x=u*w
        zz=z
        if j==5 and i in (1,4,5,8): zz+=.045
        if j==7:
            if i in (1,8): zz=5.60
            elif i in (4,5): zz=5.61
            elif i in (2,3,6,7): zz=5.78
        verts.append((x,front_y(x,zz),zz))
faces=[]
for j in range(len(rows)-1):
    for i in range(9):
        if j in (5,6) and i in (1,2,3,5,6,7): continue
        a=j*10+i; b=a+1; c=a+11; d=a+10
        if j not in (5,6) and (i+2*j)%3==0:
            faces.extend([(a,b,c),(a,c,d)])
        else:
            faces.append((a,b,c,d))
face=mesh('Cabeça • rosto com órbitas modeladas',verts,faces,skin,variation=True)
side_rings=[]
for z,w in rows:
    depth_scale=max(.20,min(1,(w/1.60)**.55))
    side_rings.append([(-w,front_y(w,z),z),(-w-.13*depth_scale,-.22,z),
                       (-w-.07*depth_scale,.55*depth_scale,z),(-w*.7,1.05*depth_scale,z),
                       (0,1.27*depth_scale,z),(w*.7,1.05*depth_scale,z),
                       (w+.07*depth_scale,.55*depth_scale,z),(w+.13*depth_scale,-.22,z),
                       (w,front_y(w,z),z)])
sideverts=[v for ring in side_rings for v in ring]
sidefaces=[]
for j in range(len(side_rings)-1):
    for i in range(8):
        a=j*9+i; b=a+1; c=a+10; d=a+9
        if (i+j)%2: sidefaces.extend([(a,b,c),(a,c,d)])
        else: sidefaces.append((a,b,c,d))
mesh('Cabeça • laterais e nuca',sideverts,sidefaces,skin,variation=True)

# Recessed, faceted almond-shaped eyes, espresso irises and square highlights.
for side, start in [('direito',1),('esquerdo',5)]:
    idx=[5*10+start+k for k in range(4)]
    idx += [6*10+start+3,7*10+start+3,7*10+start+2,7*10+start+1,7*10+start,6*10+start]
    loop=[verts[k] for k in idx]
    cx=(loop[0][0]+loop[3][0])/2
    cz=5.435
    ev=[(x,y+.025,z) for x,y,z in loop]
    ev += [(cx+(x-cx)*.82,front_y(cx,cz)-.04,cz+(z-cz)*.86) for x,y,z in loop]
    ev.append((cx,front_y(cx,cz)-.09,cz))
    ef=[]
    for i in range(10):
        ef.append((i,(i+1)%10,(i+1)%10+10,i+10))
        ef.append((i+10,(i+1)%10+10,20))
    mesh('Olho '+side+' • esclera inserida',ev,ef,white,variation=True)
    iris_y=front_y(cx,cz)-.108
    iv=[]
    for i in range(10):
        t=2*math.pi*i/10
        iv.append((cx+.303*math.cos(t),iris_y+.024*abs(math.cos(t)),cz+.351*math.sin(t)))
    mesh('Olho '+side+' • íris preta',iv,[tuple(range(10))],[eye_black])
    hw=.145
    hx=cx-.09
    hz=cz+.155
    mesh('Olho '+side+' • brilho quadrado',[(hx-hw/2,iris_y-.01,hz-hw/2),(hx+hw/2,iris_y-.01,hz-hw/2),
         (hx+hw/2,iris_y-.01,hz+hw/2),(hx-hw/2,iris_y-.01,hz+hw/2)],[(0,1,2,3)],[eye_glint])
    top=[(loop[k][0],loop[k][2]) for k in (8,7,6,5)]
    outline=top+[(x,z+.055) for x,z in reversed(top)]
    plaque('Olho '+side+' • pálpebra superior',outline,beard,.035,.025)

# Strong eyebrows with a gently arched upper edge.
brow=[(-1.29,5.90),(-1.14,6.12),(-.64,6.16),(-.23,6.06),(-.19,5.86),(-.66,5.95),(-1.03,5.94)]
plaque('Sobrancelha direita',brow,beard,.11,.11)
plaque('Sobrancelha esquerda',[(-x,z-.015) for x,z in reversed(brow)],beard,.11,.11)

# Angular bridge, tip and undersurface of the nose.
nv=[(-.16,-1.285,5.68),(.16,-1.285,5.68),(-.18,-1.49,5.28),(.18,-1.49,5.28),
    (-.39,-1.78,4.99),(.39,-1.78,4.99),(-.28,-1.64,4.88),(.28,-1.64,4.88),
    (0,-1.84,5.04),(0,-1.57,5.34),(-.27,-1.24,5.18),(.27,-1.24,5.18)]
nf=[(0,1,3,2),(2,3,9),(2,9,8,4),(9,3,5,8),(4,8,5,7,6),
    (0,2,4,10),(1,11,5,3),(10,4,6),(11,7,5),(6,7,11,10)]
nose=mesh('Nariz • ponte e ponta facetadas',nv,nf,skin)
for f,mi in zip(nose.data.polygons,[1,0,4,0,5,0,1,5,2,5]): f.material_index=mi

# Polygonal ears, with recessed inner bowls rather than a painted oval.
earshape=[(-.21,.46),(.13,.48),(.29,.30),(.29,-.35),(.12,-.52),(-.20,-.49),(-.33,-.27),(-.33,.25)]
for sign,label in [(-1,'direita'),(1,'esquerda')]:
    center=Vector((sign*1.73,-.22,4.83))
    er=[]
    for factor,yy in [(1,-.39),(.72,-.47),(.57,-.25)]:
        er += [(center.x+sign*x*factor,center.y+yy,center.z+z*factor) for x,z in earshape]
    er += [(center.x+sign*x,center.y+.05,center.z+z) for x,z in earshape]
    ef=[]
    for i in range(8):
        ni=(i+1)%8
        ef.extend([(i,ni,ni+8,i+8),(i+8,ni+8,ni+16,i+16),(i+24,ni+24,ni,i)])
    ef.append(tuple(16+i for i in range(8)))
    ear=mesh('Orelha '+label+' • contorno e cavidade',er,ef,skin+[ear_inner])
    for j,f in enumerate(ear.data.polygons):
        f.material_index=7 if j%3==1 or j==24 else (j%5)

# Low-poly scalp shell. Boundary drops at the temples, sideburns and nape.
n=24
hairline=[7.18,7.20,7.05,6.82,6.20,4.65,4.12,4.03,3.95,3.92,3.91,3.92,
          3.93,3.91,3.90,3.94,3.98,4.04,4.15,4.90,6.34,6.92,7.20,7.26]
hr=[]
for layer in range(5):
    ring=[]
    for i in range(n):
        t=2*math.pi*i/n
        sx=math.copysign(abs(math.sin(t))**.70,math.sin(t))
        cy=math.copysign(abs(math.cos(t))**.70,math.cos(t))
        low=hairline[i]
        if layer==0: z=low; scale=1.00
        elif layer==1: z=low*.56+7.30*.44; scale=1.025
        elif layer==2: z=low*.19+7.51*.81; scale=.95
        elif layer==3: z=7.55+.035*math.cos(t+.7); scale=.65
        else: z=7.65+.02*math.cos(t); scale=.20
        width=1.76
        # Follow the tapered jaw at the low ends of the hair.
        if z<4.3: width*=.87
        elif z>7.15: width*=1-(z-7.15)*.13
        x=sx*width*scale
        y=-cy*(1.17 if cy>0 else 1.34)*scale+.06
        ring.append((x,y,z))
    hr.append(ring)
hair_ob=loft('Cabelo • touca esculpida e costeletas',hr,hair,True)
for f in hair_ob.data.polygons:
    if f.center.z>7: f.material_index=rng.choice([1,2,4])

# Beard ring around a real skin opening at the smile.
outer=[(0,4.76),(.48,4.78),(.82,4.65),(.90,4.33),(1.48,4.28),(1.48,4.02),(1.10,3.74),(.58,3.56),
       (0,3.51),(-.58,3.56),(-1.10,3.74),(-1.48,4.02),(-1.48,4.28),(-.90,4.33),(-.82,4.65),(-.48,4.78)]
inner=[(0,4.48),(.39,4.50),(.72,4.49),(.80,4.36),(.78,4.15),(.59,3.99),(.25,3.96),(.24,4.05),
       (0,4.05),(-.24,4.05),(-.25,3.96),(-.59,3.99),(-.78,4.15),(-.80,4.36),(-.72,4.49),(-.39,4.50)]
bv=[]
for loop,off in [(outer,.105),(inner,.125)]:
    bv.extend((x,front_y(x,z)-off,z) for x,z in loop)
bf=[]
for i in range(16):
    j=(i+1)%16
    bf.append((i,j,j+16,i+16))
mesh('Barba • mandíbula e cavanhaque',bv,bf,beard,variation=True)
for sign,label in [(-1,'direita'),(1,'esquerda')]:
    sv=[(sign*1.49,-.91,5.55),(sign*1.66,-.35,5.55),(sign*1.66,-.32,4.16),
        (sign*1.37,-.89,3.94),(sign*1.10,front_y(1.10,3.74)-.105,3.74),
        (sign*1.48,front_y(1.48,4.28)-.105,4.28)]
    mesh('Barba • costeleta '+label,sv,[(0,1,2,5),(2,3,4,5)],beard,variation=True)

must=[(.035,4.58),(.06,4.80),(.36,4.85),(.69,4.75),(.82,4.61),(.70,4.51),(.33,4.55)]
plaque('Bigode • lado esquerdo',must,beard,.12,.17)
plaque('Bigode • lado direito',[(-x,z) for x,z in reversed(must)],beard,.12,.17)
smile=[(-.72,4.47),(-.51,4.44),(0,4.40),(.51,4.44),(.72,4.47),(.61,4.23),(.39,4.10),(0,4.07),(-.39,4.10),(-.61,4.23)]
plaque('Sorriso • abertura',smile,[mouth_dark],.035,.085)
dent=[(-.60,4.425),(0,4.365),(.60,4.425),(.47,4.23),(.30,4.18),(0,4.16),(-.30,4.18),(-.47,4.23)]
plaque('Sorriso • dentes em peça única',dent,[teeth],.022,.108)
plaque('Sorriso • lábio inferior',[(-.44,4.09),(0,4.055),(.44,4.09),(.30,4.04),(0,4.02),(-.30,4.04)],[lip],.01,.095)

# Neck and torso.
tube('Pescoço • oito planos',[(0,.06,3.08),(0,.05,3.76)],[.43,.48],skin,8)
torso_rings=[]
for z,wx,dy,cy in [(1.52,1.04,.56,.02),(1.72,1.06,.56,.02),(2.55,1.02,.57,.02),(3.10,.90,.52,.05),(3.35,.51,.39,.06)]:
    torso_rings.append([(x,y+cy,z) for x,y in rect(wx,dy,.19)])
loft('Camisa • corpo e barra facetados',torso_rings,shirt,True)
skin_v=[(-.46,-.525,3.42),(.46,-.525,3.42),(0,-.605,2.70)]
mesh('Decote • pele',skin_v,[(0,1,2)],skin)
mesh('Gola • dobra direita',[(-.50,-.56,3.40),(-.79,-.58,3.10),(-.66,-.65,2.97),(-.31,-.68,3.02),
     (0,-.65,2.64),(-.05,-.67,2.88)],[(0,1,2,3),(0,3,5),(3,4,5)],collar,variation=True)
mesh('Gola • dobra esquerda',[(.50,-.56,3.40),(.79,-.58,3.10),(.66,-.65,2.97),(.31,-.68,3.02),
     (0,-.65,2.64),(.05,-.67,2.88)],[(0,3,2,1),(0,5,3),(3,5,4)],collar,variation=True)

# Short sleeves and posed arms. The right hand is in the foreground giving a thumbs-up.
tube('Manga direita • braço levantado',[(-.80,.015,3.12),(-1.17,-.06,2.64)],[.37,.38],shirt,7)
tube('Manga esquerda • braço solto',[(.79,.06,3.11),(1.18,.06,2.61)],[.37,.36],shirt,7)
tube('Braço esquerdo • cotovelo e punho',[(1.18,.05,2.67),(1.35,-.01,2.16),(1.37,-.11,1.78)],[.27,.26,.22],skin,7)
box('Mão esquerda • dedos fechados',(1.37,-.16,1.55),(.50,.47,.70),.12,skin,rotation=(0,.035,-.05))
box('Mão esquerda • polegar',(1.14,-.34,1.64),(.20,.25,.43),.065,skin,rotation=(0,-.18,0))
for x in (1.28,1.43):
    box('Mão esquerda • dobra dos dedos',(x,-.403,1.43),(.013,.010,.22),.002,[skin[5]])
tube('Braço direito • cotovelo dobrado',[(-1.12,.0,2.68),(-1.25,-.43,2.37),(-1.21,-1.06,2.39)],[.27,.30,.29],skin,8)
box('Mão do positivo • palma',(-1.15,-1.32,2.47),(.82,.65,.83),.17,skin,rotation=(0,0,-.035))
for i,(zz,xx,ww) in enumerate([(2.82,-.78,.59),(2.57,-.76,.62),(2.32,-.80,.58),(2.13,-.91,.43)]):
    box('Mão do positivo • dedo '+str(i+1),(xx,-1.57,zz),(ww,.52,.235 if i<3 else .19),.055,skin)
tube('Mão do positivo • polegar erguido',[(-1.16,-1.29,2.78),(-.96,-1.39,3.10),(-.89,-1.38,3.39),(-.94,-1.35,3.56)],
     [(.22,.23),(.20,.215),(.18,.19),(.145,.16)],skin,7)

# Necklace and thick gold cross.
cu=bpy.data.curves.new('Colar • curva do cordão','CURVE')
cu.dimensions='3D'
cu.resolution_u=1
cu.bevel_depth=.025
cu.bevel_resolution=0
sp=cu.splines.new('POLY')
neckline=[(-.43,-.53,3.43),(-.30,-.65,3.17),(-.03,-.72,2.94),(.08,-.72,2.91),(.30,-.65,3.17),(.43,-.53,3.43)]
sp.points.add(len(neckline)-1)
for p,co in zip(sp.points,neckline): p.co=(*co,1)
co=bpy.data.objects.new('Colar • cordão preto',cu)
char.objects.link(co)
cu.materials.append(cord)
cross_outline=[(-.043,2.94),(.043,2.94),(.043,2.81),(.135,2.81),(.135,2.74),(.043,2.74),
               (.043,2.54),(-.043,2.54),(-.043,2.74),(-.135,2.74),(-.135,2.81),(-.043,2.81)]
plaque('Colar • crucifixo dourado',cross_outline,[gold,gold_side],.058,0,lambda x,z:-.80)
box('Colar • passador',(.0,-.778,2.925),(.062,.052,.09),.01,[gold])

# Trousers: broad beveled folds and a separated silhouette at the crotch.
box('Calça • cintura',(0,.035,1.44),(1.80,.91,.47),.14,pants)
for sign,label in [(-1,'direita'),(1,'esquerda')]:
    rr=[]
    for z,xc,wx,dy,cy in [(1.53,.48,.45,.45,.05),(1.12,.55,.47,.45,.04),(.71,.62,.45,.43,-.01),(.59,.61,.38,.37,-.01)]:
        rr.append([(sign*xc+x,y+cy,z) for x,y in rect(wx,dy,.12)])
    loft('Calça • perna '+label,rr,pants,True)
    footx=sign*.65
    sole_r=[]
    for z,wx,dy,b in [(.22,.50,.64,.10),(.38,.50,.64,.10),(.40,.47,.61,.10)]:
        sole_r.append([(x+footx,y-.16,z) for x,y in rect(wx,dy,b)])
    loft('Tênis '+label+' • sola branca',sole_r,sole)
    shoe_r=[]
    for z,wx,dy,b in [(.39,.475,.61,.10),(.56,.46,.58,.12),(.68,.34,.44,.11)]:
        shoe_r.append([(x+footx,y-.13,z) for x,y in rect(wx,dy,b)])
    loft('Tênis '+label+' • cabedal preto',shoe_r,shoe)

# Faceted circular display base.
base_r=[]
for z,r in [(-.08,1.98),(-.015,2.02),(.20,1.94),(.24,1.83)]:
    base_r.append([(r*math.cos(2*math.pi*i/16),r*math.sin(2*math.pi*i/16),z) for i in range(16)])
base=loft('Base • pedestal de dezesseis lados',base_r,base_mat,coll=stage)
for p in base.data.polygons:
    p.material_index=1 if p.normal.z>.8 else 0
mesh('Fundo • chão',[(-200,-200,-.09),(200,-200,-.09),(200,200,-.09),(-200,200,-.09)],[(0,1,2,3)],[floor_mat],stage)

def aim(ob,pt):
    ob.rotation_euler=(Vector(pt)-ob.location).to_track_quat('-Z','Y').to_euler()

cam_data=bpy.data.cameras.new('Câmera • referência 3/4')
cam=bpy.data.objects.new('Câmera • referência 3/4',cam_data)
stage.objects.link(cam)
cam.location=(-8,-22,9.0)
aim(cam,(0,0,3.80))
cam_data.type='ORTHO'
cam_data.ortho_scale=8.25
cam_data.lens=70
scene.camera=cam

def area(name,pos,power,size,color,target):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    data.color=color
    ob=bpy.data.objects.new(name,data)
    stage.objects.link(ob)
    ob.location=pos
    aim(ob,target)
    return ob

area('Luz • principal suave',(-4.5,-7.5,11),1150,5.0,(1.0,.84,.71),(0,0,4.4))
area('Luz • preenchimento',(5,-5,7),650,5.0,(1.0,.91,.82),(0,0,4.6))
area('Luz • recorte de cabelo',(-3,4,10),1050,4.0,(.79,.81,1.0),(0,0,5))
world=bpy.data.worlds.new('Mundo • estúdio cinza quente')
world.use_nodes=True
bg=next((n for n in world.node_tree.nodes if n.type=='BACKGROUND'),None)
if bg is None:
    bg=world.node_tree.nodes.new('ShaderNodeBackground')
    wo=world.node_tree.nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface'])
bg.inputs['Color'].default_value=(.32,.28,.34,1)
bg.inputs['Strength'].default_value=.40
scene.world=world

scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1200
scene.render.resolution_y=1312
scene.render.resolution_percentage=50
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.55
scene.render.filepath=str(OUT/'previa_v1.png')

# Pack the original reference in the editable .blend (not used as rendered geometry).
im=bpy.data.images.load(REF,check_existing=True)
im.name='Referência original • personagem low poly'
im.pack()
refob=bpy.data.objects.new('Referência original • oculta no render',None)
refs.objects.link(refob)
refob.empty_display_type='IMAGE'
refob.data=im
refob.empty_display_size=7
refob.location=(-6,2,3.8)
refob.rotation_euler=(math.pi/2,0,0)
refob.hide_render=True
refob.hide_viewport=True
scene['referencia']='Imagem fornecida pelo usuário; reconstrução manual em malhas tridimensionais de planos baixos.'
scene['observacao']='A vista posterior é interpretada a partir de uma única imagem de referência.'

bpy.ops.object.select_all(action='DESELECT')
for ob in char.objects: ob.select_set(True)
bpy.context.view_layer.objects.active=face
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_perspective='CAMERA'
            ar.spaces.active.shading.type='MATERIAL'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'personagem_low_poly.blend'))
result={'scene':scene.name,'objects':len(char.objects),'mesh_faces':sum(len(o.data.polygons) for o in char.objects if o.type=='MESH'),
        'blend':str(OUT/'personagem_low_poly.blend'),'preview':scene.render.filepath}
