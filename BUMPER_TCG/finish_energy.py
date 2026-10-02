import sys,json,re,collections,zipfile,xml.etree.ElementTree as E
from pathlib import Path
root=Path(__file__).resolve().parent; sys.path.insert(0,str(root.parent/'Verifica_Toothless/deps'))
import numpy as np,trimesh,manifold3d as m,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from render_mesh_preview import render
dest=root.parent/'PROGETTI DEFINITIVI/BUMPER TCG ENERGIE 6mm'
project=dest/'4 BUMPER TCG ENERGIE 6mm - QUALITA 0.12.3mf'
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
names=['FUOCO','LAMPO','ACQUA','ERBA']; palette={1:'#E52B20',2:'#F5D000',3:'#1686D9',4:'#62BB28'}
with zipfile.ZipFile(project) as z:
 doc=E.fromstring(z.read('3D/3dmodel.model')); cfg=json.loads(z.read('Metadata/project_settings.config'))
solids=[]; boxes=[]
for obj,item in zip(doc.findall('m:resources/m:object',ns),doc.findall('m:build/m:item',ns)):
 v=np.array([[float(p.get(c)) for c in 'xyz'] for p in obj.findall('.//m:vertex',ns)]); f=np.array([[int(p.get(c)) for c in ['v1','v2','v3']] for p in obj.findall('.//m:triangle',ns)])
 mesh=trimesh.Trimesh(v,f,process=True,validate=True); assert mesh.is_watertight and mesh.is_winding_consistent
 solids.append(m.Manifold(m.Mesh64(mesh.vertices,np.uint64(mesh.faces))))
 tf=np.array(list(map(float,item.get('transform').split()))).reshape(4,3); placed=v@tf[:3]+tf[3]; boxes.append((placed.min(0),placed.max(0)))
def as_mesh(s):
 a=s.to_mesh64();return trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=False)
fig=plt.figure(figsize=(10,13),facecolor='#e9e9e9')
for i,s in enumerate(solids):
 ax=fig.add_subplot(2,2,i+1); ax.imshow(render([s],[i+1],palette,as_mesh,relief=True)); ax.axis('off'); ax.set_title(names[i],fontsize=17,pad=-5)
fig.suptitle('BUMPER TCG | ENERGIE | BORDO 6 mm',fontsize=18,y=.985)
fig.text(.5,.016,'Mesh effettive · ombreggiatura dei rilievi accentuata per leggibilita',ha='center',fontsize=10)
fig.subplots_adjust(left=0,right=1,bottom=.035,top=.94,wspace=0,hspace=.04)
fig.savefig(dest/'ANTEPRIMA_ENERGIE.png',dpi=160);plt.close(fig)
g=(root/'energy_slice/plate_1.gcode').read_text(encoding='utf-8')
x=y=z=0.; tool=None;feature=''; tower=False; towerpoints=[]; counts=[collections.Counter() for _ in range(4)]; relief=[0]*4
feed=0; speeds=collections.defaultdict(float); unsupported=0
for line in g.splitlines():
 if line.startswith(';TYPE:'): feature=line[6:]
 if line.startswith('; WIPE_TOWER_START'): tower=True
 if line.startswith('; WIPE_TOWER_END'): tower=False
 mt=re.fullmatch(r'T(\d+)\s*',line)
 if mt: tool=int(mt[1])
 if not line.startswith(('G0 ','G1 ')): continue
 w={a:float(b) for a,b in re.findall(r'([XYZEF])(-?(?:\d+(?:\.\d*)?|\.\d+))',line)}
 x=w.get('X',x);y=w.get('Y',y);z=w.get('Z',z);feed=w.get('F',feed)
 if w.get('E',0)<=0 or not ('X' in w or 'Y' in w):continue
 if tower or feature=='Prime tower':towerpoints.append((x,y));continue
 if 'Support' in feature:unsupported+=1
 for i,(lo,hi) in enumerate(boxes):
  if lo[0]-.1<=x<=hi[0]+.1 and lo[1]-.1<=y<=hi[1]+.1:
   counts[i][tool]+=1
   if z>7.6:relief[i]+=1
   if feature in ['Outer wall','Top surface']:speeds[feature]=max(speeds[feature],feed/60)
assert all(set(c)=={i} for i,c in enumerate(counts)),counts
assert all(c>0 for c in relief),relief
assert unsupported==0
assert speeds['Outer wall']<=60.01 and speeds['Top surface']<=40.01,speeds
tp=np.array(towerpoints); assert len(tp)>0
lo,hi=tp.min(0)-.3,tp.max(0)+.3
for b0,b1 in boxes: assert np.any(hi<b0[:2]) or np.any(b1[:2]<lo),('Tower collision',lo,hi)
report=json.loads((dest/'VERIFICA_ENERGIE.json').read_text())
report.update({'material_profile':'Snapmaker PLA SnapSpeed @U1','bed':cfg['curr_bed_type'],'slicing_verified':True,'slicing_validator':'OrcaSlicer 2.4.2 portable; macros macchina sostituite soltanto nella copia di controllo','native_snapmaker_gcode_generated':False,'extrusion_tools_per_bumper':[dict(c) for c in counts],'relief_extrusion_moves':relief,'tower_xy_bounds_including_line_width':[lo.tolist(),hi.tolist()],'tower_clear_of_bumpers':True,'support_moves':unsupported,'actual_max_feature_speed_mm_s':dict(speeds)})
(dest/'VERIFICA_ENERGIE.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(dest/'LEGGIMI.txt').write_text('BUMPER TCG ENERGIE - QUALITA 0.12\n\nUn piatto: 1 FUOCO rosso, 2 LAMPO giallo, 3 ACQUA blu, 4 ERBA verde.\nCaricare le quattro bobine in questo ordine. Simboli e decorazioni a rilievo nello stesso colore del corpo.\nBordo nominale 6 mm, corpo 91,9 x 147,2 x 7,5 mm. Altezza massima con rilievi 8,34 mm.\nIncastro originale conservato; confronto volumetrico interno nullo e 151 sezioni controllate.\nNessun magnete o sede per magneti, nessuna pausa di inserimento richiesta.\nQualita: layer 0,12 mm, primo layer 0,25 mm; pareti esterne 60 mm/s, superficie superiore 40 mm/s; guscio sopra 1 mm e sotto 0,6 mm.\nPLA SnapSpeed @U1, PEI testurizzato, quattro ugelli 0,4 mm. Flusso massimo mantenuto a 12 mm3/s.\nVerifica slicing completata con OrcaSlicer 2.4.2 portable su copia di controllo: quattro colori corretti, rilievi presenti, torre senza collisioni, nessun supporto.\nLa copia di controllo usa macro macchina del validatore: il relativo G-code non viene fornito per stampare.\nAprire il 3MF definitivo come progetto in Snapmaker Orca e affettare con il profilo nativo prima di inviarlo alla stampante.\nControllare fisicamente il primo set prima della produzione ripetuta.\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['extrusion_tools_per_bumper','relief_extrusion_moves','tower_xy_bounds_including_line_width','actual_max_feature_speed_mm_s']},indent=2))
