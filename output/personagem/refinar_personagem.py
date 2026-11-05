import bpy, math
from mathutils import Vector, Matrix
from pathlib import Path

OUT=Path(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\personagem')
scene=bpy.data.scenes['Personagem • low poly.001']
bpy.context.window.scene=scene
scene['codex_character_id']='78ffdffe-lowpoly'
char=next(c for c in scene.collection.children if c.name.startswith('01 • PERSONAGEM'))
obs=list(char.objects)

def fy(x,z): return -1.30+.30*(abs(x)/1.68)**3+.041*(z-5.70)**2

# Bury the skin crown under the scalp instead of letting it protrude.
for ob in obs:
    if ob.name.startswith('Cabeça'):
        for v in ob.data.vertices:
            if v.co.z>7.10: v.co.z=7.10+(v.co.z-7.10)*.35
        if 'laterais' in ob.name:
            for f in ob.data.polygons: f.flip()
        for m in [m for m in bpy.data.materials if m.name.startswith('Barba • castanho quente')]:
            if m.name not in ob.data.materials: ob.data.materials.append(m)
        for f in ob.data.polygons:
            if f.center.z < (4.09 if 'laterais' in ob.name else 3.95):
                f.material_index=7

hair=next(o for o in obs if o.name.startswith('Cabelo • touca'))
for v in hair.data.vertices:
    if v.index<72 and v.co.y<-.05:
        v.co.y=min(v.co.y,fy(v.co.x,v.co.z)-.065)
# Remove the nonplanar internal cap across the hairline.
import bmesh
bm=bmesh.new()
bm.from_mesh(hair.data)
bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.faces[0]],context='FACES_ONLY')
bm.to_mesh(hair.data)
bm.free()

# Enlarge the eye opening vertically, together with the inserted eyes.
face=next(o for o in obs if o.name.startswith('Cabeça • rosto'))
for v in face.data.vertices:
    row,col=divmod(v.index,10)
    if col in (1,2,3,4,5,6,7,8):
        if row==5: v.co.z-=.045
        if row==7: v.co.z+=.045
for ob in obs:
    if ob.name.startswith('Olho '):
        for v in ob.data.vertices: v.co.z=5.435+(v.co.z-5.435)*1.12
        if 'esclera' in ob.name:
            for v in ob.data.vertices:
                if v.index<10: v.co.y-=.025
        if 'íris preta' in ob.name:
            cx=sum(v.co.x for v in ob.data.vertices)/len(ob.data.vertices)
            yy=min(v.co.y for v in ob.data.vertices)
            shape=[(-.22,.35),(.22,.35),(.315,.22),(.32,-.19),(.25,-.35),(-.25,-.35),(-.32,-.19),(-.315,.22)]
            me=bpy.data.meshes.new(ob.name+' • contorno octogonal')
            me.from_pydata([(cx+x,yy,5.435+z) for x,z in shape],[],[tuple(range(8))])
            me.materials.append(ob.data.materials[0])
            ob.data=me
    if ob.name.startswith('Orelha'):
        for v in ob.data.vertices: v.co.y+=.22

# One coherent head tilt, with the whole face and hair moving together.
headprefix=('Cabeça','Cabelo','Olho ','Sobrancelha','Nariz','Orelha','Barba','Bigode','Sorriso')
rot=Matrix.Rotation(math.radians(8.8),3,'Y')
pivot=Vector((0,0,5.60))
for ob in obs:
    if ob.type=='MESH' and ob.name.startswith(headprefix):
        for v in ob.data.vertices:
            co=v.co.copy()
            co.x*=1.085
            co.y*=1.035
            v.co=pivot+rot@(co-pivot)
        ob.data.update()

# Match the broad three-finger silhouette of the reference hand.
last=next(o for o in obs if o.name.startswith('Mão do positivo • dedo 4'))
bpy.data.objects.remove(last,do_unlink=True)
handpivot=Vector((-1.10,-1.40,2.70))
for ob in list(char.objects):
    if ob.name.startswith('Mão do positivo'):
        mw=ob.matrix_world.copy()
        inv=mw.inverted()
        for v in ob.data.vertices:
            co=mw@v.co
            co=handpivot+Vector(((co.x-handpivot.x)*1.14,(co.y-handpivot.y)*1.12,(co.z-handpivot.z)*1.08))
            co.x-=.08
            co.y-=.08
            v.co=inv@co

# Matte materials avoid a washed-out sheen on the flat facets.
for m in {m for o in char.objects for m in o.data.materials if o.type in ('MESH','CURVE')}:
    p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if p:
        p.inputs['Specular IOR Level'].default_value=.14
        if m.name.startswith(('Cabelo','Barba')): p.inputs['Roughness'].default_value=1
scene.camera.location=(-12.2,-20,8.8)
scene.camera.rotation_euler=(Vector((0,0,3.79))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.ortho_scale=8.07
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.view_settings.exposure=-.15
scene.render.filepath=str(OUT/'previa_v2.png')
scene.render.resolution_percentage=50
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'personagem_low_poly.blend'))
result={'scene':scene.name,'preview':scene.render.filepath,'faces':sum(len(o.data.polygons) for o in char.objects if o.type=='MESH')}
