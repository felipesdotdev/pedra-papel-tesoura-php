"""Revise only scalp and hair on the approved, rigged 3D character.
Receded temples and short, sparse geometric strands; no image texture.
"""
import bpy, bmesh, math, random, hashlib, struct, json
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT=Path(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\personagem')
s=bpy.data.scenes['Personagem 3D • materiais sólidos e rig.006']
bpy.context.window.scene=s
hair=next(o for o in s.objects if o.name.startswith('Cabelo • touca'))
head=next(o for o in s.objects if o.name.startswith('Cabeça • volume'))
rig=next(o for o in s.objects if o.type=='ARMATURE')
collection=next(c for c in s.collection.children if c.name.startswith('01 • MALHAS'))
ROT=Matrix.Rotation(math.radians(6),3,'Y')
PIV=Vector((0,0,5.50))
def local(p): return PIV+ROT.transposed()@(Vector(p)-PIV)
def world(p): return PIV+ROT@(Vector(p)-PIV)

def digest(ob):
    h=hashlib.sha256()
    if ob.type=='MESH':
        h.update(struct.pack('<%df'%(len(ob.data.vertices)*3),*(c for v in ob.data.vertices for c in v.co)))
        h.update(str([(tuple(p.vertices),p.material_index) for p in ob.data.polygons]).encode())
    h.update(str(tuple(tuple(r) for r in ob.matrix_world)).encode())
    return h.hexdigest()
unchanged={o.name:digest(o) for o in s.objects if o not in (hair,head) and not o.get('calvicie_gerado')}
rest_pose={b.name:tuple(b.rotation_euler) for b in rig.pose.bones}
if not head.get('cabeca_original'):
    backup_head=head.data.copy(); backup_head.name='BASE APROVADA • cabeça anterior'
    backup_head.use_fake_user=True; head['cabeca_original']=backup_head.name
head.data=bpy.data.meshes[head['cabeca_original']].copy()
head_group=head.vertex_groups.get('head') or head.vertex_groups.new(name='head')
head_group.add(list(range(len(head.data.vertices))),1,'REPLACE')
if not hair.get('cabelo_original'):
    backup=hair.data.copy(); backup.name='BASE APROVADA • cabelo anterior'
    backup.use_fake_user=True
    hair['cabelo_original']=backup.name
source=bpy.data.meshes[hair['cabelo_original']]
for ob in list(s.objects):
    if ob.get('calvicie_gerado'): bpy.data.objects.remove(ob,do_unlink=True)
source.update()
verts=[local(v.co) for v in source.vertices]
normals=[(ROT.transposed()@v.normal).normalized() for v in source.vertices]
faces=[tuple(p.vertices) for p in source.polygons]
tree=BVHTree.FromPolygons(verts,faces,all_triangles=False)
hairmats=list(source.materials)

def make_material(name,color):
    m=bpy.data.materials.new(name)
    rgb=tuple(int(color[i:i+2],16)/255 for i in (0,2,4))
    rgb=tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb)
    m.diffuse_color=(*rgb,1)
    nt=m.node_tree; nt.nodes.clear()
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=(*rgb,1)
    bs.inputs['Roughness'].default_value=.95
    bs.inputs['Specular IOR Level'].default_value=.08
    out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(bs.outputs[0],out.inputs[0])
    return m

def bind(ob):
    ob.parent=rig
    ob.matrix_parent_inverse=hair.matrix_parent_inverse.copy()
    ob.matrix_basis=hair.matrix_basis.copy()
    group=ob.vertex_groups.get('head') or ob.vertex_groups.new(name='head')
    group.add(list(range(len(ob.data.vertices))),1,'REPLACE')
    mod=ob.modifiers.new('Deformação • cabeça','ARMATURE')
    mod.object=rig; mod.use_deform_preserve_volume=True
    ob['calvicie_gerado']=True

def threshold(deg):
    # The central point stays slightly forward; the two temples recede deeply.
    d=abs(deg)
    keys=[(0,7.66),(15,7.64),(30,7.62),(45,7.53),(60,7.22),(70,6.45),
          (75,5.85),(90,4.70),(105,4.30),(120,4.08),(135,3.98),(180,3.97)]
    for j in range(len(keys)-1):
        if keys[j][0]<=d<=keys[j+1][0]:
            t=(d-keys[j][0])/(keys[j+1][0]-keys[j][0])
            return keys[j][1]*(1-t)+keys[j+1][1]*t
    return keys[-1][1]

def signed(p):
    a=math.degrees(math.atan2(p.x/1.8,-(p.y-.1)/1.45))
    line=p.z-threshold(a)
    # Diffuse thinning on the crown, with fuller sides and back.
    ellipse=(p.x/.75)**2+((p.y-.15)/.90)**2-1
    opening=ellipse*.22 if p.z>7.31 else 1
    return min(line,opening)

hv=[]; hf=[]; hm=[]
for poly in source.polygons:
    ring=[(verts[i],signed(verts[i])) for i in poly.vertices]
    cut=[]
    for j,(a,va) in enumerate(ring):
        b,vb=ring[(j+1)%len(ring)]
        if va>=0: cut.append(a)
        if (va>=0)!=(vb>=0): cut.append(a.lerp(b,va/(va-vb)))
    if len(cut)>=3:
        k=len(hv); hv.extend(tuple(world(p)) for p in cut)
        hf.append(tuple(range(k,k+len(cut)))); hm.append(poly.material_index)
me=bpy.data.meshes.new('Cabelo • entradas e coroa rala')
me.from_pydata(hv,[],hf); me.update()
for m in hairmats: me.materials.append(m)
for p,i in zip(me.polygons,hm): p.material_index=i
bm=bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free()
hair.data=me
hair_group=hair.vertex_groups.get('head') or hair.vertex_groups.new(name='head')
hair_group.add(list(range(len(me.vertices))),1,'REPLACE')
hair['calvicie']='Entradas frontotemporais profundas e menor densidade no topo, com fios curtos em geometria.'

# Rebuild the exposed upper scalp as a continuous extension of the approved
# skull. All existing face vertices below the forehead are retained exactly.
visible_vertices={i for p in head.data.polygons for i in p.vertices}
approved_lower={tuple(round(c,6) for c in v.co) for v in head.data.vertices if v.index in visible_vertices and local(v.co).z<6.299}
bm=bmesh.new(); bm.from_mesh(head.data)
remove=[f for f in bm.faces if any(local(v.co).z>6.301 for v in f.verts)]
bmesh.ops.delete(bm,geom=remove,context='FACES')
unused=[v for v in bm.verts if not v.link_faces]
if unused: bmesh.ops.delete(bm,geom=unused,context='VERTS')
boundary=[v for v in bm.verts if abs(local(v.co).z-6.30)<.0002]
assert len(boundary)==17, len(boundary)
boundary.sort(key=lambda v:math.atan2(local(v.co).x,-(local(v.co).y-.1)))
base=[local(v.co) for v in boundary]
last=boundary
profiles=[(6.85,1.50,-1.270,1.49),(7.02,1.35,-1.255,1.49),(7.17,1.12,-1.240,1.49),
          (7.37,1.06,-1.185,1.49),(7.57,.80,-1.075,1.35),(7.665,.33,-.290,.51)]
for z,w,front,back in profiles:
    ring=[]
    for p in base:
        sign=1 if p.x>=0 else -1
        original_front=-1.30+.50*(abs(p.x)/1.80)**2.5+.022*(6.30-5.7)**2
        if abs(p.y-original_front)<.002:
            u=p.x/1.74; x=u*w
            y=front+.50*(abs(x)/1.80)**2.5
        elif p.y<0:
            x=sign*(w+.025*w/1.5); y=front+.97*min(1,w/1.1)
        elif p.y<1.35:
            x=sign*(w+.025*w/1.5); y=back-.25*min(1,w/1.1)
        elif abs(p.x)>.10:
            x=sign*(w-.21*w/1.74); y=back-.03*w/1.74
        else: x=0; y=back
        ring.append(bm.verts.new(world((x,y,z))))
    for i in range(17):
        f=bm.faces.new((last[i],last[(i+1)%17],ring[(i+1)%17],ring[i]))
        f.material_index=0; f.smooth=False
    last=ring
tip=bm.verts.new(world((0,.15,7.68)))
for i in range(17):
    f=bm.faces.new((last[i],last[(i+1)%17],tip)); f.material_index=0; f.smooth=False
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(head.data); bm.free()
head_group=head.vertex_groups.get('head') or head.vertex_groups.new(name='head')
head_group.add(list(range(len(head.data.vertices))),1,'REPLACE')
new_lower={tuple(round(c,6) for c in v.co) for v in head.data.vertices if local(v.co).z<6.299}
assert approved_lower==new_lower
head.data.update()
tree=BVHTree.FromPolygons([local(v.co) for v in head.data.vertices],[tuple(p.vertices) for p in head.data.polygons],all_triangles=False)

# Discrete, short polygonal hairs leave the scalp visible on the crown.
rand=random.Random(91)
sv=[]; sf=[]
def scalp_point(x,y):
    hit,n,idx,dist=tree.ray_cast(Vector((x,y,9)),Vector((0,0,-1)))
    if hit is None: return None
    return hit+n*.018,n
for candidate in range(320):
    x=rand.uniform(-.73,.73); y=rand.uniform(-1.10,1.02)
    start=scalp_point(x,y)
    if start is None or signed(start[0])>-.005: continue
    length=rand.uniform(.08,.16); width=rand.uniform(.006,.011)
    end=scalp_point(x+rand.uniform(-.055,.065),y+length)
    if end is None: continue
    a,na=start; b,nb=end
    sideways=Vector((1,0,0))*width/2
    apex=(a+b)/2+(na+nb).normalized()*.005
    points=[a-sideways,a+sideways,b+sideways*.10,b-sideways*.10,apex]
    k=len(sv); sv.extend(tuple(world(p)) for p in points)
    sf.extend([(k,k+1,k+4),(k+1,k+2,k+4),(k+2,k+3,k+4),(k+3,k,k+4),(k+3,k+2,k+1,k)])
strands=bpy.data.meshes.new('Fios ralos • geometria curta')
strands.from_pydata(sv,[],sf); strands.update()
strands.materials.append(make_material('3D • Fios curtos castanhos','593B29'))
strandob=bpy.data.objects.new('Cabelo • fios curtos no topo',strands)
collection.objects.link(strandob); bind(strandob)

bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[name])==value for name,value in unchanged.items())
assert all(tuple(rig.pose.bones[name].rotation_euler)==value for name,value in rest_pose.items())
assert all(n.type!='TEX_IMAGE' for ob in (hair,head,strandob) for m in ob.data.materials for n in m.node_tree.nodes)
s['calvicie_revisada']=True
s['referencia_cabelo']='Foto real fornecida em 2026-11-05: entradas e rarefação superior; sem textura fotográfica.'
report={'scene':s.name,'changed_existing_objects':[hair.name,head.name+' (couro cabeludo)'],'unchanged_objects_verified':len(unchanged),
        'approved_face_vertices_preserved':len(approved_lower),'hair_faces':len(hair.data.polygons),'sparse_hairs':len(sf)//5,'rig_bones':len(rig.data.bones),'image_texture_nodes':0}
(OUT/'validacao_calvicie.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
s.render.resolution_percentage=50; s.cycles.samples=32
s.render.filepath=str(OUT/'calvicie_previa.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'personagem_3d_calvicie_trabalho.blend'))
bpy.ops.render.render(scene=s.name,write_still=True)
result=report
