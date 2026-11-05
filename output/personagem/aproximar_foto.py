"""Derive the web character from its original scene; preserve all existing scenes.
Run through Blender MCP. The new photo supplies visible appearance, not identity.
"""
import bpy, math, random, os, shutil
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php'
OUT=os.path.join(ROOT,'output','personagem')
ASSETS=os.path.join(ROOT,'assets','personagem')
source=bpy.data.scenes['Personagem - referencia low poly.001']
scene=bpy.data.scenes.new('Personagem | Foto com oculos e sorriso')
bpy.context.window.scene=scene
char=bpy.data.collections.new('FOTO | Personagem editavel')
studio=bpy.data.collections.new('FOTO | Estudio')
scene.collection.children.link(char);scene.collection.children.link(studio)
source_char=source.objects['Testa central'].users_collection[0]
objects={};materials={}
for old in source.objects:
    ob=old.copy()
    if old.data:ob.data=old.data.copy()
    (char if old in list(source_char.objects) else studio).objects.link(ob)
    ob.name='Foto | '+old.name;objects[old.name]=ob
    if ob.type=='MESH':
        for i,ma in enumerate(ob.data.materials):
            if ma not in materials:materials[ma]=ma.copy()
            ob.data.materials[i]=materials[ma]
scene.camera=objects[source.camera.name]
scene.world=source.world.copy()

def material(name,rgb,rough=.9,metal=0,alpha=1):
    ma=bpy.data.materials.new('Foto | '+name);ma.diffuse_color=(*rgb,alpha);ma.use_nodes=True
    p=next(n for n in ma.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal;p.inputs['Alpha'].default_value=alpha
    p.inputs['Specular IOR Level'].default_value=.2
    return ma
def recolor(ma,rgb):
    p=next(n for n in ma.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*rgb,1);ma.diffuse_color=(*rgb,1)

skin=objects['Rosto plano inferior'].data.materials[0]
skinlight=objects['Testa central'].data.materials[0]
skinshade=objects['Maxilar lateral E'].data.materials[0]
recolor(skin,(.53,.30,.22));recolor(skinlight,(.59,.345,.26));recolor(skinshade,(.445,.235,.173))
recolor(objects['Tronco camiseta'].data.materials[0],(.36,.025,.022))
recolor(objects['Camiseta peito facetado'].data.materials[0],(.41,.034,.027))
hair=material('Cabelo castanho escuro',(.025,.025,.021))
hairlit=material('Cabelo planos penteados',(.041,.042,.034))
hairgray=material('Cabelo grisalho nas temporas',(.14,.155,.14))
hairgraydark=material('Cabelo mistura grisalha',(.067,.078,.066))
browmat=material('Sobrancelhas suaves',(.078,.063,.047))
beardbase=material('Barba curta base misturada a pele',(.405,.282,.225))
beardedge=material('Barba transicao discreta',(.48,.288,.218))
stubbledark=material('Barba fios curtos escuros',(.105,.096,.083))
stubblegray=material('Barba fios grisalhos',(.47,.455,.415))
stubblelight=material('Barba fios brancos no queixo',(.62,.59,.535))
framemat=material('Oculos metal bronze cinza',(.125,.116,.088),.32,.65)
lensmat=material('Oculos lentes transparentes',(.66,.77,.70),.15,0,.055)
smilemat=material('Sorriso interior',(.115,.037,.026))
teethmat=material('Sorriso dentes marfim',(.87,.83,.71),.7)
lipmat=material('Sorriso labios naturais',(.42,.184,.145))
creasemat=material('Dobras de expressao',(.415,.23,.178))

def point(p,d):return ((p[0]-561)/200,d,(1360-p[1])/200)
def mesh(name,vs,fs,mats,ids=None):
    me=bpy.data.meshes.new('Foto | '+name);me.from_pydata(vs,[],fs);me.update()
    ob=bpy.data.objects.new('Foto | '+name,me);char.objects.link(ob)
    for ma in mats:me.materials.append(ma)
    if ids:
        for f,i in zip(me.polygons,ids):f.material_index=i
    return ob
def patch(name,ps,ds,ma):
    if isinstance(ds,(int,float)):ds=[ds]*len(ps)
    return mesh(name,[point(p,d) for p,d in zip(ps,ds)],[tuple(range(len(ps)))],[ma])
def remove(name):
    ob=objects.pop(name,None)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)
def mirror(ps):return [(1122-x,y) for x,y in ps]
def tube(name,path,radius,ma,sides=6):
    vs=[];fs=[]
    for j,p in enumerate(path):
        p=Vector(p);t=Vector(path[min(j+1,len(path)-1)])-Vector(path[max(0,j-1)])
        t.normalize();u=t.cross(Vector((0,1,0)))
        if u.length<.01:u=t.cross(Vector((1,0,0)))
        u.normalize();v=t.cross(u).normalized()
        for i in range(sides):vs.append(tuple(p+radius*(u*math.cos(i*2*math.pi/sides)+v*math.sin(i*2*math.pi/sides))))
    for j in range(len(path)-1):
        for i in range(sides):fs.append((j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i))
    fs += [tuple(reversed(range(sides))),tuple((len(path)-1)*sides+i for i in range(sides))]
    return mesh(name,vs,fs,[ma])

# Rebuild the haircut: short, swept to one side, with receding temples.
for name in list(objects):
    if name.startswith('Cabelo') or name.startswith('Sobrancelha') or name.startswith(('Labio','Boca linha')):remove(name)
patch('Testa ampliada nas entradas',[(300,380),(313,270),(360,183),(417,141),(504,135),(623,143),(741,174),(805,272),(820,400)],-.495,skin)
# Make the forehead a broad gentle plane, without a dark diagonal ridge.
for name in ('Testa central','Testa superior'):
    for v in objects[name].data.vertices:v.co.y=-.86
N=32;rings=[]
def hairline(t):
    # Interpolate the front M-shaped hairline and the short sides/nape.
    a=abs(math.degrees(t))
    if a>180:a=360-a
    keys=[(0,209),(22.5,181),(40,172),(55,243),(70,400),(90,555),(120,610),(180,620)]
    for (a0,p0),(a1,p1) in zip(keys,keys[1:]):
        if a0<=a<=a1:
            py=p0+(p1-p0)*(a-a0)/(a1-a0)
            if math.sin(t)>0 and a<60:py+=12*math.sin(t)
            return (1360-py)/200
    return 3.7
for layer in range(5):
    ring=[]
    for i in range(N):
        t=2*math.pi*i/N;low=hairline(t)
        fraction=[0,.38,.73,.94,1][layer];scale=[1,1.01,.94,.64,.20][layer]
        z=low*(1-fraction)+(6.43+.035*math.sin(t+.5))*fraction
        x=1.46*math.copysign(abs(math.sin(t))**.78,math.sin(t))*scale
        cy=math.copysign(abs(math.cos(t))**.7,math.cos(t))
        y=.10-cy*(.99 if cy>0 else 1.15)*scale
        ring.append((x,y,z))
    rings.append(ring)
vs=[v for ring in rings for v in ring];fs=[];ids=[]
for j in range(4):
    for i in range(N):
        a=j*N+i;b=j*N+(i+1)%N;c=(j+1)*N+(i+1)%N;d=(j+1)*N+i
        angle=abs(math.sin((i+.5)*2*math.pi/N))
        index=(2 if i%3==0 else 3) if angle>.89 and j<2 else (1 if (i+j)%4==0 else 0)
        fs.extend([(a,b,d),(b,c,d)]);ids.extend([index,index])
fs.append(tuple(4*N+i for i in range(N)));ids.append(0)
mesh('Cabelo curto com entradas e temporas grisalhas',vs,fs,[hair,hairlit,hairgray,hairgraydark],ids)

# Smile-softened eyes and finer, naturally arched eyebrows.
eye_names=('Esclera','Iris octogonal','Pupila','Reflexo quadrado','Linha palpebra')
for side in ('E','D'):
    old=objects['Esclera '+side]
    ps=[(v.co.x*200+561,1360-v.co.z*200) for v in old.data.vertices]
    patch('Pele sob palpebras '+side,ps,-.902,skin)
    cx=447 if side=='E' else 675
    for base in eye_names:
        ob=objects[base+' '+side]
        if base=='Linha palpebra':ob.data.materials[0]=browmat
        for v in ob.data.vertices:
            px=v.co.x*200+561;py=1360-v.co.z*200
            px=cx+(px-cx)*.93;py=501+(py-501)*.72
            v.co.x=(px-561)/200;v.co.z=(1360-py)/200
    ps=[(367,435),(399,422),(447,425),(491,439),(494,449),(446,437),(402,434),(369,443)]
    patch('Sobrancelha fina '+side,ps if side=='E' else mirror(ps),-.985,browmat)

# Front skin surface sampled for beard and expression details.
skin_objects=[o for o in char.objects if o.type=='MESH' and any(m in (skin,skinlight,skinshade) for m in o.data.materials)]
vskin=[];fskin=[]
for ob in skin_objects:
    offset=len(vskin);vskin.extend(tuple(ob.matrix_world@v.co) for v in ob.data.vertices)
    fskin.extend(tuple(offset+i for i in p.vertices) for p in ob.data.polygons)
bvh=BVHTree.FromPolygons(vskin,fskin)
def front(px,py,off=.012):
    x=(px-561)/200;z=(1360-py)/200
    hit=bvh.ray_cast(Vector((x,-5,z)),Vector((0,1,0)),7)
    return hit[0].y-off if hit[0] is not None else -.94-off

# Thin rectangular metal eyeglasses, complete rims, bridge and temple arms.
outline=[(346,478),(358,463),(404,458),(479,462),(511,477),(507,523),(491,545),(386,545),(353,529)]
for side in ('E','D'):
    ps=outline if side=='E' else mirror(outline)
    path=[point(p,-1.095) for p in ps];path.append(path[0])
    tube('Oculos aro retangular '+side,path,.018,framemat,6)
    lens=patch('Oculos lente clara '+side,ps,-1.077,lensmat)
    lens.visible_shadow=False
    arm=[(346,481),(321,474),(299,484),(290,520)]
    if side=='D':arm=mirror(arm)
    tube('Oculos haste '+side,[point(p,d) for p,d in zip(arm,[-1.09,-.73,-.17,.05])],.018,framemat)
tube('Oculos ponte sobre nariz',[point(p,d) for p,d in zip([(511,482),(529,475),(551,473),(571,473),(593,475),(611,482)],[-1.095,-1.10,-1.115,-1.115,-1.10,-1.095])],.016,framemat)

# A salt-and-pepper stubble field rather than a solid full beard.
outer=[(315,556),(346,581),(389,620),(470,650),(561,654),(652,650),(733,620),(776,581),(807,556),(812,700),(747,790),(626,823),(496,823),(375,790),(310,700)]
inner=[(420,663),(430,674),(444,684),(489,677),(561,675),(633,677),(678,684),(692,674),(702,663),(693,730),(648,766),(599,779),(523,779),(474,766),(429,730)]
loops=[outer,[(a[0]*.65+b[0]*.35,a[1]*.65+b[1]*.35) for a,b in zip(outer,inner)],inner]
vs=[]
for loop in loops:vs.extend(point(p,front(*p,.012)) for p in loop)
fs=[];ids=[];n=len(outer)
for layer in range(2):
    for i in range(n):
        j=(i+1)%n;fs.append((layer*n+i,layer*n+j,(layer+1)*n+j,(layer+1)*n+i));ids.append(layer)
beard=mesh('Barba curta transicao no maxilar',vs,fs,[beardedge,beardbase],ids)

# Sparse short strands with progressively more gray towards the chin.
rng=random.Random(153);vs=[];fs=[];ids=[]
def inside(p,poly):
    x,y=p;value=False;j=len(poly)-1
    for i,(xi,yi) in enumerate(poly):
        xj,yj=poly[j]
        if ((yi>y)!=(yj>y)) and x<(xj-xi)*(y-yi)/(yj-yi)+xi:value=not value
        j=i
    return value
for _ in range(1800):
    px=rng.uniform(305,817);py=rng.uniform(554,822)
    if not inside((px,py),outer) or inside((px,py),inner):continue
    width=rng.uniform(.65,1.45);height=rng.uniform(2.0,4.8)
    d=front(px,py,.017);offset=len(vs)
    vs.extend(point(p,d) for p in [(px-width,py-height/2),(px+width,py-height/2),(px+width*.35,py+height/2),(px-width*.35,py+height/2)])
    fs.append(tuple(offset+i for i in range(4)))
    chance=rng.random();ids.append(2 if py>749 and chance<.4 else 1 if chance<.57 else 0)
mesh('Barba fios curtos sal e pimenta',vs,fs,[stubbledark,stubblegray,stubblelight],ids)
for side in ('E','D'):
    ps=[(488,653),(510,646),(551,652),(557,666),(521,662),(494,674),(473,678)]
    if side=='D':ps=mirror(ps)
    patch('Bigode curto '+side,ps,[front(*p,.016) for p in ps],beardbase)

# Broad relaxed smile with one upper row of teeth and a subtle lower lip.
smile=[(437,684),(474,698),(518,704),(561,707),(604,704),(648,698),(685,684),(674,715),(648,741),(608,756),(561,762),(514,756),(474,741),(448,715)]
patch('Sorriso aberto',smile,-.981,smilemat)
teeth=[(448,691),(478,701),(520,709),(561,712),(602,709),(644,701),(674,691),(660,715),(632,730),(595,739),(561,742),(527,739),(490,730),(462,715)]
patch('Sorriso dentes superiores',teeth,-.990,teethmat)
patch('Sorriso labio inferior',[(466,738),(509,757),(561,764),(613,757),(656,738),(635,758),(597,771),(561,774),(525,771),(487,758)],-.992,lipmat)
for side in ('E','D'):
    ps=[(421,646),(410,659),(415,680),(435,697)]
    if side=='D':ps=mirror(ps)
    tube('Dobra suave do sorriso '+side,[point(p,front(*p,.009)) for p in ps],.006,creasemat,4)

# Narrow the jaw and keep the adult oval silhouette throughout every facial part.
body_prefix=('Solado','Tenis','Biqueira','Perna','Cintura','Braco','Mao','Tronco','Camiseta','Manga','Pescoco')
for ob in list(char.objects):
    if any(ob==objects.get(name) for name in objects if name.startswith(body_prefix)):continue
    for ve in ob.data.vertices:
        py=1360-ve.co.z*200
        taper=1-.12*max(0,min(1,(py-570)/260))
        ve.co.x*=.92*taper
    ob.data.update()

# Save a derivative project and export only the character, never the studio.
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1122;scene.render.resolution_y=1402;scene.render.resolution_percentage=65
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=-.35
scene.camera.location=(0,-18,3.65);scene.camera.rotation_euler=(Vector((0,0,3.35))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.ortho_scale=7.02
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,'personagem_foto.png')
image=bpy.data.images.load(r'C:\Users\luisf\AppData\Local\Temp\codex-clipboard-0b913fcb-0f27-45a9-9650-2f09dbb60a57.png',check_existing=True);image.pack()
scene['referencia_visual']='Foto fornecida: oculos retangulares, entradas, cabelo curto grisalho, barba curta, sorriso e camiseta vermelha.'
for fn in ('personagem.glb','poster.png'):
    original=os.path.join(ASSETS,fn);backup=os.path.join(OUT,'antes_foto_'+fn)
    if os.path.exists(original) and not os.path.exists(backup):shutil.copy2(original,backup)
bpy.ops.object.select_all(action='DESELECT')
for ob in char.objects:ob.select_set(True)
bpy.context.view_layer.objects.active=next(iter(char.objects))
bpy.ops.export_scene.gltf(filepath=os.path.join(ASSETS,'personagem.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'personagem_foto.blend'))
result={'scene':scene.name,'objects':len(char.objects),'glb_bytes':os.path.getsize(os.path.join(ASSETS,'personagem.glb')),'blend':os.path.join(OUT,'personagem_foto.blend')}
