from pathlib import Path
root=Path(__file__).resolve().parent
# Reuse the verified opening, rounded outer shell, and geometric helpers only.
code=(root/'designer_bumpers.py').read_text().split('# A:')[0]
code=code.replace("BUMPER TCG DESIGN 6mm'","BUMPER TCG ENERGIE 6mm'")
exec(compile(code,str(root/'designer_bumpers.py'),'exec'))
from render_mesh_preview import render
quality=root.parent/'PROGETTI DEFINITIVI/BUMPER TCG DESIGN 6mm/4 BUMPER TCG DESIGN 6mm - QUALITA 0.12.3mf'
names=['FUOCO','LAMPO','ACQUA','ERBA']
palette={1:'#E52B20',2:'#F5D000',3:'#1686D9',4:'#62BB28'}
def raised(points,h=.72): return poly(points,7.4,h+.1)
def motif(points,cx,cy,sx=1,sy=1,h=.72): return raised([(cx+sx*x,cy+sy*y) for x,y in points],h)
flame=[(0,-2.2),(-1.3,-1.5),(-1.55,-.5),(-1.0,.5),(-.7,-.1),(-.15,1.1),(.1,2.2),(.9,1.2),(1.2,.25),(1.05,-.2),(1.5,.2),(1.4,-1.05),(.8,-1.9)]
bolt=[(.7,2.2),(-1.45,-.45),(-.15,-.3),(-.65,-2.2),(1.5,.5),(.2,.3)]
drop=[(0,2.2),(-.55,1.2),(-1.3,-.15),(-1.5,-.8),(-1.3,-1.55),(-.7,-2.05),(0,-2.2),(.7,-2.05),(1.3,-1.55),(1.5,-.8),(1.3,-.15),(.55,1.2)]
leaf=[(-1.25,-1.8),(-1.4,-.3),(-.9,1),(.25,1.85),(1.3,2.15),(1.35,.65),(.9,-.75),(-.2,-1.7)]
decorations=[]
# Broad flame ribbons and attached tongues of fire.
ss=[motif(flame,0,-70.8,h=.84)]
for side in [-1,1]:
 y=np.linspace(-58,55,115)
 ss.append(stroke([(side*(42.6+.65*np.sin(v*.17)),v) for v in y],1.05,7.4,.70))
 for cy in [-45,-23,-1,21,43]: ss.append(motif(flame,side*43.2,cy,sx=.85,sy=2.5,h=.72))
 for x in [-28,-18,18,28]: ss.append(motif(flame,x,-70.75,sx=1.25,sy=.8,h=.6))
decorations.append(union(ss))
# Repeated lightning bolts with a larger bottom icon, all attached to the face.
ss=[motif(bolt,0,-70.8,h=.84)]
for side in [-1,1]:
 for cy in np.arange(-52,53,15): ss.append(motif(bolt,side*42.95,cy,sx=1.1,sy=2.3,h=.72))
for x in [-29,-18,18,29]: ss.append(motif(bolt,x,-70.8,sx=1.3,sy=.72,h=.6))
decorations.append(union(ss))
# Two smooth raised wave traces, plus a droplet emblem.
ss=[motif(drop,0,-70.8,h=.84)]
for side in [-1,1]:
 for shift in [-.8,.8]:
  ss.append(stroke([(side*(43+shift+.55*np.sin(v*.16)),v) for v in np.linspace(-59,59,130)],.95,7.4,.70))
 for cy in [-62,62]:
  ss.append(stroke([(side*(42.6+1.1*np.cos(t)),cy+1.4*np.sin(t)) for t in np.linspace(0,1.65*np.pi,40)],.9,7.4,.7))
for start,end in [(-34,-8),(8,34)]:
 ss.append(stroke([(x,-70.8+.65*np.sin(x*.34)) for x in np.linspace(start,end,45)],1,7.4,.7))
decorations.append(union(ss))
# Raised vines with broad leaves; no free-standing stems or undercuts.
ss=[motif(leaf,0,-70.8,h=.84)]
for side in [-1,1]:
 ss.append(stroke([(side*(42.9+.4*np.sin(v*.15)),v) for v in np.linspace(-59,59,120)],.95,7.4,.7))
 for j,cy in enumerate(np.arange(-53,54,11)):
  ss.append(motif(leaf,side*(42.9+(.4 if j%2 else -.4)),cy,sx=.70 if j%2 else -.70,sy=1.45,h=.72))
for x in [-28,-17,17,28]: ss.append(motif(leaf,x,-70.8,sx=1.1,sy=.8,h=.6))
decorations.append(union(ss))
designs=[]; reports=[]
def hole(s,z):
 ps=s.slice(z).to_polygons()
 return m.CrossSection([p[::-1] for p in ps if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))<-2000])
for name,d in zip(names,decorations):
 assert d.status()==m.Error.NoError and not d.is_empty()
 assert (d^protected).volume()<1e-7,(name,'Relief intrudes on protected opening')
 assert (d-flat_outer.translate([0,0,.84])).volume()<1e-6,(name,'Relief outside footprint')
 s=(base+d).simplify(.000001)
 mesh=as_mesh(s); mesh.merge_vertices(digits_vertex=7); mesh.update_faces(mesh.nondegenerate_faces()); mesh.update_faces(mesh.unique_faces()); mesh.remove_unreferenced_vertices()
 assert mesh.is_watertight and mesh.is_winding_consistent
 assert len(mesh.split())==1,name
 s=as_solid(mesh); a=original^protected; b=s^protected
 err=(a-b).volume()+(b-a).volume(); assert err<1e-6,(name,err)
 maxerr=0
 for z in np.linspace(.0001,7.4999,151):
  a,b=hole(original,z),hole(s,z); maxerr=max(maxerr,(a-b).area()+(b-a).area())
 assert maxerr<1e-6,(name,maxerr)
 # No magnets are used: the model is the preserved frame plus positive surface relief.
 assert (base-s).volume()<1e-6
 designs.append(s)
 reports.append({'name':name,'watertight':True,'connected_solids':1,'internal_volume_difference_mm3':err,'max_hole_difference_mm2_151_sections':maxerr,'bounds_mm':mesh.bounds.tolist(),'volume_mm3':s.volume(),'magnet_seats':0,'support_required_for_relief':False})
 print('VERIFIED',name,len(mesh.faces),'faces',flush=True)

fig=plt.figure(figsize=(10,13),facecolor='#e9e9e9')
for i,(name,s) in enumerate(zip(names,designs)):
 ax=fig.add_subplot(2,2,i+1); ax.imshow(render([s],[i+1],palette,as_mesh)); ax.axis('off'); ax.set_title(name,fontsize=17,pad=-5)
fig.suptitle('BUMPER TCG | ENERGIE | BORDO 6 mm',fontsize=18,y=.985)
fig.text(.5,.018,'Geometrie effettive · simboli e decorazioni a rilievo · incastro originale',ha='center',fontsize=10)
fig.subplots_adjust(left=0,right=1,bottom=.035,top=.94,wspace=0,hspace=.04)
fig.savefig(dest/'ANTEPRIMA_ENERGIE.png',dpi=160); plt.close(fig)

positions=[(59.4,182.95,0),(182.95,210.6,90),(210.6,87.05,0),(87.05,59.4,90)]
fig,ax=plt.subplots(figsize=(7,7)); ax.set_facecolor('#34383a'); boxes=[]
for i,(s,(x,y,angle)) in enumerate(zip(designs,positions)):
 p=s.rotate([0,0,angle]).translate([x,y,0]); mesh=as_mesh(p); lo,hi=mesh.bounds
 assert np.all(lo>=[.5,1,-1e-5]) and np.all(hi<=[270.5,271,270])
 for b0,b1 in boxes: assert np.any(hi[:2]<b0[:2]) or np.any(b1[:2]<lo[:2])
 boxes.append((lo,hi))
 ps=p.slice(3).to_polygons(); ps=sorted(ps,key=lambda q:-np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1)))
 for q in ps:
  area=np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1))
  ax.add_patch(Polygon(q,facecolor=palette[i+1] if area>0 else '#34383a',edgecolor='none'))
 ax.text(x,y,names[i],ha='center',color='#bbbbbb',fontsize=10)
ax.set_xlim(0,271); ax.set_ylim(0,271); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([]); fig.tight_layout(pad=0)
fig.savefig(dest/'PIATTO.png',dpi=100); plt.close(fig)

CORE='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'; BAM='http://schemas.bambulab.com/package/2021'
E.register_namespace('',CORE)
def t(s): return '{'+CORE+'}'+s
def meta(parent,key,value): E.SubElement(parent,'metadata',key=key,value=str(value))
qzip=zipfile.ZipFile(quality); settings=json.loads(qzip.read('Metadata/project_settings.config'))
settings['filament_colour']=list(palette.values()); settings['extruder_colour']=list(palette.values())
settings['print_settings_id']='BUMPER ENERGIE - Qualita 0.12 @Snapmaker U1 (0.4 nozzle)'
# Carry forward all print parameters and material behavior from the approved quality project.
expected={'layer_height':'0.12','initial_layer_print_height':'0.25','outer_wall_speed':'60','top_surface_speed':'40','top_shell_thickness':'1','bottom_shell_thickness':'0.6','xy_contour_compensation':'0','xy_hole_compensation':'0'}
assert all(settings[k]==v for k,v in expected.items())
model=E.Element(t('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'it-IT','xmlns:BambuStudio':BAM})
E.SubElement(model,t('metadata'),name='Application').text='BambuStudio-2.3.6'
E.SubElement(model,t('metadata'),name='BambuStudio:3mfVersion').text='1'
res=E.SubElement(model,t('resources')); build=E.SubElement(model,t('build'))
config=E.Element('config'); plate=E.SubElement(config,'plate')
for k,v in [('plater_id',1),('plater_name','ENERGIE - QUALITA 0.12'),('locked','false'),('thumbnail_file','Metadata/plate_1.png'),('thumbnail_no_light_file','Metadata/plate_no_light_1.png'),('top_file','Metadata/top_1.png')]: meta(plate,k,v)
for i,(s,name,(x,y,angle)) in enumerate(zip(designs,names,positions)):
 oid=str(i+1); obj=E.SubElement(res,t('object'),id=oid,type='model',name='ENERGIA '+name); me=E.SubElement(obj,t('mesh')); vs=E.SubElement(me,t('vertices')); fs=E.SubElement(me,t('triangles'))
 mesh=as_mesh(s)
 for v in mesh.vertices: E.SubElement(vs,t('vertex'),{c:format(float(val),'.12g') for c,val in zip('xyz',v)})
 for f in mesh.faces: E.SubElement(fs,t('triangle'),{c:str(int(val)) for c,val in zip(['v1','v2','v3'],f)})
 transform=('0 1 0 -1 0 0 0 0 1' if angle else '1 0 0 0 1 0 0 0 1')+f' {x} {y} 0'
 E.SubElement(build,t('item'),objectid=oid,transform=transform,printable='1')
 co=E.SubElement(config,'object',id=oid); meta(co,'name','ENERGIA '+name); meta(co,'extruder',i+1)
 part=E.SubElement(co,'part',id=oid,subtype='normal_part'); meta(part,'name','ENERGIA '+name); meta(part,'extruder',i+1)
 E.SubElement(part,'mesh_stat',edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
 inst=E.SubElement(plate,'model_instance')
 for k,v in [('object_id',oid),('instance_id',0),('identify_id',180+i)]: meta(inst,k,v)
out=dest/'4 BUMPER TCG ENERGIE 6mm - QUALITA 0.12.3mf'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('[Content_Types].xml',qzip.read('[Content_Types].xml'))
 z.writestr('_rels/.rels',qzip.read('_rels/.rels'))
 z.writestr('3D/3dmodel.model',E.tostring(model,encoding='utf-8',xml_declaration=True))
 z.writestr('Metadata/model_settings.config',E.tostring(config,encoding='utf-8',xml_declaration=True))
 z.writestr('Metadata/project_settings.config',json.dumps(settings,ensure_ascii=False,indent=2))
 for n in ['plate_1.png','plate_no_light_1.png','top_1.png']: z.write(dest/'PIATTO.png','Metadata/'+n)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 r=E.fromstring(z.read('3D/3dmodel.model'))
 for obj in r.find(t('resources')):
  v=np.array([[float(p.get(c)) for c in 'xyz'] for p in obj.findall('.//'+t('vertex'))]); f=np.array([[int(p.get(c)) for c in ['v1','v2','v3']] for p in obj.findall('.//'+t('triangle'))])
  mesh=trimesh.Trimesh(v,f,process=True,validate=True)
  assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.faces)==len(f)
report={'file':out.name,'designs':reports,'border_mm':6,'body_height_mm':7.5,'maximum_relief_mm':.84,'max_height_mm':8.34,'quality':expected,'colors':dict(zip(names,palette.values())),'plates':1,'adjacent_model_gap_mm':4,'magnet_seats':0,'source_quality_sha256':hashlib.sha256(quality.read_bytes()).hexdigest(),'slicing_verified':False}
(dest/'VERIFICA_ENERGIE.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CREATED',out,flush=True)
