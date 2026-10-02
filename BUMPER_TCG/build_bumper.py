import sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'Verifica_Toothless/deps'))
import numpy as np, trimesh, manifold3d as m
parts=[]
for i,offset in [(1,[0,0,3.75]),(4,[0,0,6.9000001])]:
 a=np.load(root/f'object{i}.npz'); mesh=trimesh.Trimesh(a['v']+offset,a['f'],process=True)
 for s in mesh.split():
  if s.centroid[0]>-26.15 and s.centroid[1]>29.15:
   parts.append(s)
   print('PART',i,len(s.faces),s.bounds.tolist(),s.is_watertight)
whole=m.Manifold.batch_boolean([m.Manifold(m.Mesh(np.float32(s.vertices),np.uint32(s.faces))) for s in parts],m.OpType.Add)
out=whole.to_mesh(); mesh=trimesh.Trimesh(out.vert_properties[:,:3],out.tri_verts,process=True)
print('UNION',whole.status(),mesh.bounds.tolist(),mesh.is_watertight)
for z in [0.1,0.74,0.76,3,6.29,6.31,6.74,6.76,7.4]:
 sec=whole.slice(z)
 print('SECTION',z)
 for p in sec.to_polygons():
  print("bounds",p.min(0),p.max(0),"area", np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))/2)
mesh.export(root/'source_single.stl')
import json, zipfile, xml.etree.ElementTree as E, hashlib
center=np.array([47.8,75.45,0])
whole=whole.translate(-center)
# Preserve every original surface within a box enclosing the complete opening.
protected=m.Manifold.cube([136.4,81.1,9],True).translate([0,0,3.75])
def rounded(w,h,r):
 points=[]
 for cx,cy,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for t in np.linspace(a,a+90,49):
   points.append([cx+r*np.cos(np.radians(t)),cy+r*np.sin(np.radians(t))])
 return m.CrossSection([points])
outer=rounded(145.2,89.9,6).extrude(7.5)
result=(whole+(outer-protected))^outer
delta=((whole-protected)+(protected-whole)) # unused globally; compare restricted solids below
before=whole^protected; after=result^protected
diff=(before-after).volume()+(after-before).volume()
assert diff<1e-7, diff
rm=result.to_mesh(); final=trimesh.Trimesh(rm.vert_properties[:,:3],rm.tri_verts,process=True)
assert final.is_watertight and final.is_winding_consistent and len(final.split())==1
# Compare the actual hole contours at 151 heights, including both lips.
max_hole_error=0
def holes(s,z):
 ps=s.slice(z).to_polygons()
 return m.CrossSection([p[::-1] for p in ps if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))<0])
for height in np.linspace(.0001,7.4999,151):
 a,b=holes(whole,height),holes(result,height)
 err=(a-b).area()+(b-a).area(); max_hole_error=max(max_hole_error,err)
assert max_hole_error<1e-6,max_hole_error
final.export(root/'BUMPER_PSA_ARROTONDATO.stl')
source=root.parent/'PROGETTI DEFINITIVI/4 BUMPER TCG.3mf'
original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
zin=zipfile.ZipFile(source)
settings=zin.read('Metadata/project_settings.config')
CORE='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
E.register_namespace('',CORE)
def tag(n): return '{'+CORE+'}'+n
colors=['GIALLO','ROSSO','BIANCO','NERO']
hexes=['#F5D000','#E52B20','#F5F5F5','#111111']
dest=root.parent/'PROGETTI DEFINITIVI/BUMPER TCG ARROTONDATI'
dest.mkdir(exist_ok=True)
def save_project(indices,filename):
 model=E.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'it-IT'})
 E.SubElement(model,tag('metadata'),{'name':'Application'}).text='BambuStudio-2.3.6'
 res=E.SubElement(model,tag('resources')); build=E.SubElement(model,tag('build'))
 config=E.Element('config'); plate=E.SubElement(config,'plate')
 for k,v in [('plater_id','1'),('plater_name','Bumper PSA arrotondati'),('locked','false')]: E.SubElement(plate,'metadata',key=k,value=v)
 placements=[(182.8,210.45,0),(210.45,87.2,90),(87.2,59.55,0),(59.55,182.8,90)]
 for i in indices:
  oid=str(i+1); obj=E.SubElement(res,tag('object'),id=oid,type='model',name='BUMPER PSA '+colors[i])
  me=E.SubElement(obj,tag('mesh')); vs=E.SubElement(me,tag('vertices')); fs=E.SubElement(me,tag('triangles'))
  for v in final.vertices: E.SubElement(vs,tag('vertex'),{c:format(float(val),'.9g') for c,val in zip('xyz',v)})
  for f in final.faces: E.SubElement(fs,tag('triangle'),{c:str(int(val)) for c,val in zip(['v1','v2','v3'],f)})
  x,y,angle=placements[i] if len(indices)>1 else (135,135,0)
  transform=('0 1 0 -1 0 0 0 0 1' if angle else '1 0 0 0 1 0 0 0 1')+f' {x} {y} 0'
  E.SubElement(build,tag('item'),objectid=oid,transform=transform,printable='1')
  co=E.SubElement(config,'object',id=oid)
  for k,v in [('name','BUMPER PSA '+colors[i]),('extruder',str(i+1))]: E.SubElement(co,'metadata',key=k,value=v)
  part=E.SubElement(co,'part',id=oid,subtype='normal_part')
  for k,v in [('name','BUMPER PSA '+colors[i]),('extruder',str(i+1))]: E.SubElement(part,'metadata',key=k,value=v)
  E.SubElement(part,'mesh_stat',edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
  inst=E.SubElement(plate,'model_instance')
  for k,v in [('object_id',oid),('instance_id','0'),('identify_id',str(120+i))]: E.SubElement(inst,'metadata',key=k,value=v)
 with zipfile.ZipFile(dest/filename,'w',zipfile.ZIP_DEFLATED) as zo:
  zo.writestr('[Content_Types].xml',zin.read('[Content_Types].xml'))
  zo.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
  zo.writestr('3D/3dmodel.model',E.tostring(model,encoding='utf-8',xml_declaration=True))
  zo.writestr('Metadata/model_settings.config',E.tostring(config,encoding='utf-8',xml_declaration=True))
  zo.writestr('Metadata/project_settings.config',settings)
 return str(dest/filename)
files=[save_project([i],f'BUMPER PSA ARROTONDATO {colors[i]}.3mf') for i in range(4)]
files.append(save_project(list(range(4)),'4 BUMPER PSA ARROTONDATI.3mf'))
report={'outer_mm':[145.2,89.9,7.5],'outer_corner_radius_mm':6,'straight_border_mm':5,'original_opening_mm':[135.2,79.9],'protected_volume_difference_mm3':diff,'max_hole_difference_mm2_151_sections':max_hole_error,'watertight':bool(final.is_watertight),'winding_consistent':bool(final.is_winding_consistent),'components':len(final.split()),'original_sha256':original_hash,'files':files}
(dest/'VERIFICA_GEOMETRIA.json').write_text(json.dumps(report,indent=2))
assert original_hash==hashlib.sha256(source.read_bytes()).hexdigest()
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
fig,axs=plt.subplots(1,2,figsize=(12,5),facecolor='#f5f5f5')
for ax,solid,title in zip(axs,[whole,result],['Prima: angoli sporgenti','Dopo: bordo uniforme, raggio 6 mm']):
 ps=solid.slice(3).to_polygons()
 for p in ps:
  area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
  ax.add_patch(Polygon(p,facecolor='#f5d000' if area>0 else '#f5f5f5',edgecolor='#353535',lw=.7))
 ax.set_aspect('equal'); ax.set_xlim(-78,78); ax.set_ylim(-51,51); ax.axis('off'); ax.set_title(title,fontsize=13)
fig.suptitle('BUMPER PSA | apertura interna conservata',fontsize=16)
fig.tight_layout(); fig.savefig(dest/'CONFRONTO.png',dpi=180)
print('RESULT',json.dumps(report,indent=2))
for file in files:
 with zipfile.ZipFile(file) as check:
  assert check.testzip() is None
  assert check.read('Metadata/project_settings.config')==settings
  doc=E.fromstring(check.read('3D/3dmodel.model'))
  objects={o.get('id'):o for o in doc.findall('.//'+tag('object'))}
  boxes=[]
  for item in doc.find(tag('build')):
   ob=objects[item.get('objectid')]
   vv=np.array([[float(v.get(c)) for c in 'xyz'] for v in ob.findall('.//'+tag('vertex'))])
   ff=np.array([[int(f.get(c)) for c in ['v1','v2','v3']] for f in ob.findall('.//'+tag('triangle'))])
   saved=trimesh.Trimesh(vv,ff,process=True)
   assert saved.is_watertight and saved.is_winding_consistent
   tf=np.array(list(map(float,item.get('transform').split()))).reshape(4,3)
   placed=vv@tf[:3]+tf[3]; lo,hi=placed.min(0),placed.max(0)
   assert np.all(lo>=[.5,1,-.00001]) and np.all(hi<=[270.5,271,270])
   for b0,b1 in boxes:
    assert np.any(hi[:2]<b0[:2]) or np.any(b1[:2]<lo[:2])
   boxes.append((lo,hi))
print('SAVED FILES: valid meshes, original print settings, in-bed, no overlapping objects')
(dest/'LEGGIMI.txt').write_text('BUMPER PSA ARROTONDATI - prima versione\n\nBordo esterno uniforme: 5 mm sui lati; raggio angoli: 6 mm.\nIngombro: 145,2 x 89,9 x 7,5 mm.\nApertura originale: circa 135,2 x 79,9 mm, con i raccordi originali conservati.\nZona interna invariata: differenza volumetrica 0 mm3 e 151 sezioni senza differenze.\nBase ricavata da un bumper giallo completo, inclusi gli inserti neri del progetto originale.\nQuattro versioni monocolore: slot 1 giallo, 2 rosso, 3 bianco, 4 nero.\nIl progetto con quattro pezzi mantiene una disposizione a girandola sul piatto U1.\nProfili macchina e filamenti, layer 0,2 mm e altre impostazioni conservati dal file originale.\nMesh chiuse, orientate correttamente e verificate dopo la riapertura dei file salvati.\nQuesti sono progetti 3MF da aprire e affettare in Snapmaker Orca, non G-code gia verificato.\nLa prova fisica resta da fare: il bordo piu spesso puo modificare la flessibilita pur mantenendo le misure interne.\nIl file originale 4 BUMPER TCG.3mf non e stato modificato.\n',encoding='utf-8')
