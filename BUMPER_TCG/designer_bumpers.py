import sys, json, zipfile, hashlib, xml.etree.ElementTree as E
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'Verifica_Toothless/deps'))
import numpy as np, trimesh, manifold3d as m
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Polygon

dest=root.parent/'PROGETTI DEFINITIVI/BUMPER TCG DESIGN 6mm'
dest.mkdir(exist_ok=True)
source=root.parent/'PROGETTI DEFINITIVI/4 BUMPER TCG.3mf'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
def union(ss): return m.Manifold.batch_boolean(ss,m.OpType.Add)
def as_mesh(s):
 a=s.to_mesh64(); return trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=False)
def as_solid(s): return m.Manifold(m.Mesh64(np.float64(s.vertices),np.uint64(s.faces)))
ss=[]
for i,off in [(1,[0,0,3.75]),(4,[0,0,6.9000001])]:
 a=np.load(root/f'object{i}.npz')
 for s in trimesh.Trimesh(a['v']+off,a['f'],process=True).split():
  if s.centroid[0]>-26.15 and s.centroid[1]>29.15: ss.append(as_solid(s))
original=as_solid(trimesh.load_mesh(root/'source_single.stl',process=True)).translate([-47.8,-75.45,0]).rotate([0,0,90])
protected=m.Manifold.cube([81.1,136.4,10],True).translate([0,0,3.75])
def rr(w,h,r,n=36):
 p=[]
 for cx,cy,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for t in np.linspace(a,a+90,n+1): p.append([cx+r*np.cos(np.deg2rad(t)),cy+r*np.sin(np.deg2rad(t))])
 return m.CrossSection([p])
outline=rr(91.9,147.2,6)
outer=outline.extrude(7.1)+outline.extrude(.4,scale_top=(91.1/91.9,146.4/147.2)).translate([0,0,7.1])
base=(original+(outer-protected))^outer
flat_outer=outline.extrude(7.5)
flat_base=(original+(flat_outer-protected))^flat_outer

def poly(points,z,height):
 p=np.array(points)
 if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))<0: p=p[::-1]
 return m.CrossSection([p]).extrude(height).translate([0,0,z])
def stroke(points,width,z=6.7,height=.8):
 # Rounded endpoints and joins; every inlay has positive thickness.
 cs=[]
 for p in points: cs.append(m.CrossSection.circle(width/2,16).translate(p))
 for a,b in zip(points[:-1],points[1:]):
  a,b=np.array(a),np.array(b); n=np.array([-(b-a)[1],(b-a)[0]])/np.linalg.norm(b-a)*width/2
  cs.append(m.CrossSection([[a+n,a-n,b-n,b+n]]))
 c=m.CrossSection.batch_boolean(cs,m.OpType.Add)
 return c.extrude(height).translate([0,0,z])
def split_inlays(s,dec):
 dec=dec^s
 assert (dec^protected).volume()<1e-7
 return s-dec,dec

# A: a triangulated shallow relief with three concentric rows and alternating peaks.
def facet_loop(w,h,r):
 p=[]
 corners=[(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]
 for j,(cx,cy,a) in enumerate(corners):
  arc=[[cx+r*np.cos(np.deg2rad(t)),cy+r*np.sin(np.deg2rad(t))] for t in np.linspace(a,a+90,5)]
  p.extend(arc)
  nx,ny,na=corners[(j+1)%4]; nxt=np.array([nx+r*np.cos(np.deg2rad(na)),ny+r*np.sin(np.deg2rad(na))])
  end=np.array(arc[-1]); count=6 if j%2==0 else 11
  p.extend([(end+(nxt-end)*k/count).tolist() for k in range(1,count)])
 return np.array(p)
loops=[facet_loop(82.1,137.4,2.8),facet_loop(87.0,142.3,4.4),facet_loop(93.9,149.2,7)]
n=len(loops[0]); assert all(len(p)==n for p in loops)
lower=[]
for row,p in enumerate(loops):
 for j,(x,y) in enumerate(p):
  z=7.7 if row==0 else ([7.45,6.95,7.3,7.05][j%4] if row==1 else 6.65)
  lower.append([x,y,z])
verts=np.array(lower+[[x,y,9] for x,y,z in lower]); k=len(lower); faces=[]
for row in range(2):
 for j in range(n):
  a=row*n+j; b=row*n+(j+1)%n; c=(row+1)*n+j; d=(row+1)*n+(j+1)%n
  # These triangles point downward at the bottom of the cutter.
  for t in [(a,b,c),(b,d,c)]: faces.extend([t,tuple(v+k for v in t[::-1])])
for row in [0,2]:
 for j in range(n):
  a=row*n+j; b=row*n+(j+1)%n
  ts=[(a,a+k,b),(b,a+k,b+k)]
  if row==2: ts=[t[::-1] for t in ts]
  faces.extend(ts)
cutter_mesh=trimesh.Trimesh(verts,faces,process=True)
assert cutter_mesh.is_watertight and cutter_mesh.is_winding_consistent
if cutter_mesh.volume<0: cutter_mesh.invert()
diamond=flat_base-(as_solid(cutter_mesh)-protected)
gem=poly([(0,-69.0),(-2,-70.6),(0,-72.3),(2,-70.6)],6.3,1.3)
A=split_inlays(diamond,gem)

# B: contrasting lower stripes and recessed upper stripes.
stripes=[]; grooves=[]
for side in [-1,1]:
 for y in [-46,-51,-56]:
  stripes.append(poly([(side*x,yy) for x,yy in [(40.9,y-2),(44.7,y+1.2),(44.7,y+2.6),(40.9,y-.6)]],6.7,.8))
 for y in [35,40,45]:
  grooves.append(poly([(side*x,yy) for x,yy in [(41.2,y-2),(44.8,y+1),(44.8,y+2.2),(41.2,y-.8)]],7.0,1))
B=split_inlays(base-union(grooves),union(stripes))

# C: coarse, printable circuit tracks and square terminals.
tracks=[]
for side in [-1,1]:
 for path in [[(43,-50),(43,-25),(41.5,-19),(41.5,5)],[(43,50),(43,25),(41.5,19),(41.5,10)],[(44,-9),(44,9)]]:
  tracks.append(stroke([(side*x,y) for x,y in path],1.1))
 for y in [-50,50]:
  tracks.append(m.Manifold.cube([2.1,2.1,.8]).translate([side*43-1.05,y-1.05,6.7]))
C=split_inlays(base,union(tracks))

# D: shallow grip grooves and four rounded yellow corner accents.
grips=[]; accents=[]
for side in [-1,1]:
 for y in np.arange(-13,13.01,3.25):
  grips.append(m.Manifold.cube([5,1.25,1.2]).translate([42 if side==1 else -47,y-.625,6.95]))
for sx in [-1,1]:
 for sy in [-1,1]:
  path=[(sx*42.95,sy*64.4),(sx*42.95,sy*67.6)]
  path += [(sx*(39.95+3*np.cos(t)),sy*(67.6+3*np.sin(t))) for t in np.linspace(0,np.pi/2,25)[1:]]
  path += [(sx*36.75,sy*70.6)]
  accents.append(stroke(path,1.3))
D=split_inlays(base-union(grips),union(accents))
designs=[A,B,C,D]; names=['A DIAMOND','B SPEED','C CIRCUIT','D STEALTH']
for i,parts in enumerate(designs):
 clean=[]
 for p in parts:
  p=p.simplify(0.00001 if i==0 else 0.000001)
  raw=as_mesh(p)
  tested=raw.copy(); tested.merge_vertices(digits_vertex=7)
  tested.update_faces(tested.nondegenerate_faces()); tested.update_faces(tested.unique_faces()); tested.remove_unreferenced_vertices()
  print('CLEAN CHECK',names[i],tested.is_watertight,len(raw.faces),len(tested.faces),flush=True)
  assert tested.is_watertight and tested.is_winding_consistent
  clean.append(as_solid(tested))
 designs[i]=tuple(clean)
print('BASE STATUS',base.status(),base.volume(),outer.status(),outer.volume(),flush=True)
for label,pp in zip(names,designs): print('PART STATUS',label,[(p.status(),p.volume()) for p in pp],union(list(pp)).status(),flush=True)
slots=[(1,4),(2,3),(3,4),(4,1)]
palette={1:'#F5D000',2:'#E52B20',3:'#F5F5F5',4:'#111111'}
def hole(s,z):
 ps=s.slice(z).to_polygons()
 return m.CrossSection([p[::-1] for p in ps if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))<-2000])
reports=[]
for name,parts in zip(names,designs):
 s=union(list(parts)); before=original^protected; after=s^protected
 assert s.status()==m.Error.NoError and not s.is_empty(),name
 err=(before-after).volume()+(after-before).volume()
 assert err<1e-6,(name,'internal volume',err)
 section_error=0
 for z in np.linspace(.0001,7.4999,151):
  a,b=hole(original,z),hole(s,z); ee=(a-b).area()+(b-a).area()
  section_error=max(section_error,ee)
 assert section_error<1e-6,(name,section_error)
 for p in parts:
  mesh=as_mesh(p); assert p.status()==m.Error.NoError and mesh.is_watertight and mesh.is_winding_consistent,(name,p.status(),mesh.is_watertight,mesh.is_winding_consistent,len(mesh.vertices),len(mesh.faces))
 total=as_mesh(s); assert len(total.split())==1
 assert (parts[0]^parts[1]).volume()<1e-7
 reports.append({'design':name,'internal_difference_mm3':err,'hole_difference_mm2_151_sections':section_error,'closed_meshes':True,'assembled_components':1,'volume_mm3':s.volume(),'accent_volume_mm3':parts[1].volume()})
 print('VERIFIED',name,flush=True)

CORE='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'; BAM='http://schemas.bambulab.com/package/2021'
E.register_namespace('',CORE); E.register_namespace('BambuStudio',BAM)
def t(s): return '{'+CORE+'}'+s
def meta(parent,key,value): E.SubElement(parent,'metadata',key=key,value=str(value))
zin=zipfile.ZipFile(source); original_settings=json.loads(zin.read('Metadata/project_settings.config'))
settings=dict(original_settings)
# Preserve the successful fit-related settings. Ensure all pieces print layer by layer.
settings['print_sequence']='by layer'
positions=[(59.4,182.95,0),(182.95,210.6,90),(210.6,87.05,0),(87.05,59.4,90)]
def package():
 model=E.Element(t('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'it-IT','xmlns:BambuStudio':BAM})
 E.SubElement(model,t('metadata'),name='Application').text='BambuStudio-2.3.6'
 E.SubElement(model,t('metadata'),name='BambuStudio:3mfVersion').text='1'
 E.SubElement(model,t('metadata'),name='Title').text='4 BUMPER TCG DESIGN - bordo 6 mm'
 res=E.SubElement(model,t('resources')); build=E.SubElement(model,t('build'))
 cfg=E.Element('config'); plate=E.SubElement(cfg,'plate')
 for key,value in [('plater_id',1),('plater_name','4 DESIGN - BORDO 6 mm'),('locked','false'),('thumbnail_file','Metadata/plate_1.png'),('thumbnail_no_light_file','Metadata/plate_no_light_1.png'),('top_file','Metadata/top_1.png')]: meta(plate,key,value)
 boxes=[]
 for i,(name,parts,extruders) in enumerate(zip(names,designs,slots)):
  assembly_id=20+i
  co=E.SubElement(cfg,'object',id=str(assembly_id)); meta(co,'name',name+' - bordo 6mm'); meta(co,'extruder',extruders[0])
  ids=[]
  for j,(solid,slot) in enumerate(zip(parts,extruders)):
   oid=1+i*2+j; ids.append(oid); label=name+(' CORPO' if j==0 else ' INSERTI')
   obj=E.SubElement(res,t('object'),id=str(oid),type='model',name=label)
   me=E.SubElement(obj,t('mesh')); vs=E.SubElement(me,t('vertices')); fs=E.SubElement(me,t('triangles'))
   mesh=as_mesh(solid)
   for v in mesh.vertices: E.SubElement(vs,t('vertex'),{c:format(float(val),'.12g') for c,val in zip('xyz',v)})
   for f in mesh.faces: E.SubElement(fs,t('triangle'),{c:str(int(val)) for c,val in zip(['v1','v2','v3'],f)})
   part=E.SubElement(co,'part',id=str(oid),subtype='normal_part'); meta(part,'name',label); meta(part,'extruder',slot)
   meta(part,'matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
   E.SubElement(part,'mesh_stat',edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
  obj=E.SubElement(res,t('object'),id=str(assembly_id),type='model',name=name); comps=E.SubElement(obj,t('components'))
  for oid in ids: E.SubElement(comps,t('component'),objectid=str(oid),transform='1 0 0 0 1 0 0 0 1 0 0 0')
  x,y,angle=positions[i]; transform=('0 1 0 -1 0 0 0 0 1' if angle else '1 0 0 0 1 0 0 0 1')+f' {x} {y} 0'
  E.SubElement(build,t('item'),objectid=str(assembly_id),transform=transform,printable='1')
  inst=E.SubElement(plate,'model_instance')
  for key,value in [('object_id',assembly_id),('instance_id',0),('identify_id',150+i)]: meta(inst,key,value)
  vv=as_mesh(union(list(parts))).vertices
  tf=np.array(list(map(float,transform.split()))).reshape(4,3); placed=vv@tf[:3]+tf[3]; lo,hi=placed.min(0),placed.max(0)
  assert np.all(lo>=[.5,1,-1e-5]) and np.all(hi<=[270.5,271,270])
  for b0,b1 in boxes: assert np.any(hi[:2]<b0[:2]) or np.any(b1[:2]<lo[:2])
  boxes.append((lo,hi))
 out=dest/'4 BUMPER TCG DESIGN 6mm.3mf'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml',zin.read('[Content_Types].xml'))
  z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
  z.writestr('3D/3dmodel.model',E.tostring(model,encoding='utf-8',xml_declaration=True))
  z.writestr('Metadata/model_settings.config',E.tostring(cfg,encoding='utf-8',xml_declaration=True))
  z.writestr('Metadata/project_settings.config',json.dumps(settings,ensure_ascii=False))
  for name in ['plate_1.png','plate_no_light_1.png','top_1.png']: z.write(dest/'PIATTO.png','Metadata/'+name)
 return out

# Render the actual meshes, including faceting, rather than the AI concept image.
from render_mesh_preview import render
fig=plt.figure(figsize=(10,13),facecolor='#e9e9e9')
for i,(name,parts,extruders) in enumerate(zip(names,designs,slots)):
 ax=fig.add_subplot(2,2,i+1)
 ax.set_facecolor('#e9e9e9')
 ax.imshow(render(parts,extruders,palette,as_mesh))
 ax.axis('off'); ax.set_title(name,fontsize=16,pad=-6)
fig.suptitle('BUMPER TCG | 4 DESIGN | BORDO 6 mm',fontsize=19,y=.98)
fig.text(.5,.02,'Anteprima delle mesh 3MF · apertura interna originale conservata',ha='center',fontsize=11)
fig.subplots_adjust(left=0,right=1,bottom=.04,top=.94,wspace=0,hspace=.02)
fig.savefig(dest/'ANTEPRIMA_4_DESIGN.png',dpi=170); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,7)); ax.set_facecolor('#34383a')
for i,(parts,extruders) in enumerate(zip(designs,slots)):
 x,y,angle=positions[i]
 for j,(solid,slot) in enumerate(zip(parts,extruders)):
  # At the top, inlays are visible; rendering the projection also includes beveled edges.
  solid=solid.rotate([0,0,angle]).translate([x,y,0]); ps=solid.slice(3 if j==0 else 6.85).to_polygons()
  ps=sorted(ps,key=lambda p:-np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))
  for p in ps:
   signed=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
   ax.add_patch(Polygon(p,facecolor=palette[slot] if signed>0 else '#34383a',edgecolor='none'))
 ax.text(x,y,names[i],color='#bbbbbb',ha='center',fontsize=9)
ax.set_aspect('equal'); ax.set_xlim(0,271); ax.set_ylim(0,271); ax.set_xticks([]); ax.set_yticks([])
fig.tight_layout(pad=0); fig.savefig(dest/'PIATTO.png',dpi=100); plt.close(fig)
out=package()
with zipfile.ZipFile(out) as check:
 assert check.testzip() is None
 doc=E.fromstring(check.read('3D/3dmodel.model')); cfg=E.fromstring(check.read('Metadata/model_settings.config'))
 assert len(doc.find(t('build')))==4 and len(cfg.findall('object/part'))==8
 for obj in doc.find(t('resources')):
  me=obj.find(t('mesh'))
  if me is None: continue
  vv=np.array([[float(v.get(c)) for c in 'xyz'] for v in me.find(t('vertices'))]); ff=np.array([[int(f.get(c)) for c in ['v1','v2','v3']] for f in me.find(t('triangles'))])
  mesh=trimesh.Trimesh(vv,ff,process=True,validate=True); assert mesh.is_watertight and mesh.is_winding_consistent
  assert len(mesh.faces)==len(ff),'Degenerate faces after serialization'
report={'original_sha256':source_hash,'outer_dimensions_mm':[91.9,147.2,7.5],'border_mm':6,'outer_corner_radius_mm':6,'original_opening_mm':[79.9,135.2],'parts':reports,'slots':dict(zip(names,slots)),'bed_clearance_between_adjacent_bounds_mm':4,'saved_meshes_verified':True,'sliced':False}
(dest/'VERIFICA.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
(dest/'LEGGIMI.txt').write_text('BUMPER TCG - QUATTRO DESIGN, BORDO 6 mm\n\nA DIAMOND: giallo con facce geometriche e rombo nero.\nB SPEED: rosso con sei inserti bianchi e incisioni superiori.\nC CIRCUIT: bianco con piste e terminali neri.\nD STEALTH: nero con archi gialli e scanalature laterali.\n\nIngombro singolo: 91,9 x 147,2 x 7,5 mm. Bordo nominale 6 mm; raggio esterno 6 mm.\nIncastro interno ricavato dal bumper originale completo e mantenuto invariato.\nOgni design: differenza volumetrica interna zero e confronto di 151 sezioni senza differenze.\nDecorazioni incassate nella faccia superiore: nessun inserto da incollare.\nFilamenti: 1 giallo, 2 rosso, 3 bianco, 4 nero, come nel progetto originale.\nQuattro oggetti con due parti ciascuno: mantenere gli inserti associati al relativo corpo.\nImpostazioni originali U1 conservate; stampa per layer.\nAprire come progetto in Snapmaker Orca e affettare: non e un G-code.\nPrima della produzione ripetuta verificare fisicamente la flessibilita del bordo da 6 mm.\nANTEPRIMA_4_DESIGN.png mostra le geometrie effettive, adattate al bordo reale.\n',encoding='utf-8')
print('CREATED',out,flush=True)
