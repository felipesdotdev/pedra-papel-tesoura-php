import bpy
import json
from pathlib import Path

scene=bpy.data.scenes['Personagem • reconstrução fiel 3D']
bpy.context.window.scene=scene
for other in list(bpy.data.scenes):
    if other!=scene:
        bpy.data.scenes.remove(other)
owned=set(scene.objects)
for ob in list(bpy.data.objects):
    if ob not in owned:
        bpy.data.objects.remove(ob,do_unlink=True)
for collection in list(bpy.data.collections):
    if collection.users==0:
        bpy.data.collections.remove(collection)
bpy.ops.outliner.orphans_purge(do_recursive=True)
scene.name='Personagem • referência low poly'
scene.render.filepath='//personagem_final.png'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file:
        im.pack()
out=Path(r'C:\Users\luisf\Documents\ChatGPT\pedra-papel-tesoura-php\output\personagem')
path=out/'personagem_final.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
report={'file':str(path),'scenes':[s.name for s in bpy.data.scenes],
        'objects':len(scene.objects),'meshes':sum(o.type=='MESH' for o in scene.objects),
        'faces':sum(len(o.data.polygons) for o in scene.objects if o.type=='MESH'),
        'packed_images':[im.name for im in bpy.data.images if im.packed_file],
        'bytes':path.stat().st_size,'camera':scene.camera.name}
(out/'verificacao_final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
