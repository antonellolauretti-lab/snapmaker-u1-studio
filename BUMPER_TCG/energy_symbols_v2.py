from pathlib import Path
root=Path(__file__).resolve().parent
text=(root/'energy_bumpers.py').read_text(encoding='utf-8')
# Reuse geometric helper definitions without running the previous exporter.
header=text.split('decorations=[]')[0].replace("BUMPER TCG ENERGIE 6mm'","BUMPER TCG ENERGIE SIMBOLI GRANDI'")
exec(compile(header,str(root/'energy_bumpers.py'),'exec'))
import hashlib
previous=root.parent/'PROGETTI DEFINITIVI/BUMPER TCG ENERGIE 6mm/4 BUMPER TCG ENERGIE 6mm - QUALITA 0.12.3mf'
previous_hash=hashlib.sha256(previous.read_bytes()).hexdigest()
quality=previous

def bezier(start,segments):
 pts=[start]; p=np.array(start,dtype=float)
 for c1,c2,end in segments:
  a,b,q=map(lambda x:np.array(x,dtype=float),(c1,c2,end))
  for t in np.linspace(0,1,14)[1:]: pts.append(((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*q).tolist())
  p=q
 return pts
flame_big=bezier((0,-6.25),[
 ((-4.8,-6),(-5.4,-2.1),(-3.2,.8)),
 ((-3.6,-1),(-1.8,-1.2),(-1.1,.5)),
 ((.1,2.2),(-.6,4.2),(-.3,6.25)),
 ((2.4,4.8),(3.2,2.7),(2.5,.3)),
 ((3.1,.5),(3.9,1.2),(3.7,2)),
 ((6,-.3),(5,-5.9),(0,-6.25))])
drop_big=bezier((0,6.25),[
 ((-1.1,3.3),(-4.7,.6),(-4.6,-2.2)),
 ((-4.6,-7.6),(4.6,-7.6),(4.6,-2.2)),
 ((4.7,.6),(1.1,3.3),(0,6.25))])
leaf_big=bezier((-3.9,-5.8),[
 ((-6,-.6),(-2.9,4.5),(4.4,6.25)),
 ((5.6,1.8),(3.9,-4.3),(-3.9,-5.8))])
bolt_big=[(1.8,6.25),(-4.4,-1),(-.65,-.55),(-2,-6.25),(4.4,1.35),(.65,.85)]
# A 12.5 mm silhouette, attached across the lower rim, extending outward only.
CY=-74.75
icons=[]
for points in [flame_big,bolt_big,drop_big,leaf_big]:
 p=np.array(points); p[:,1]=(p[:,1]-p[:,1].min())/(p[:,1].max()-p[:,1].min())*12.5-6.25
 cs=m.CrossSection([p if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))>0 else p[::-1]])
 # The actual symbol outline reaches the bed: no rectangular backing or unsupported shelf.
 icon=cs.extrude(8.7)+cs.extrude(.6,scale_top=(.9,.9)).translate([0,0,8.7])
 icons.append(icon.translate([0,CY,0]))
# Engraved veins and inner flame detail, confined to the raised icon face.
veins=[stroke([(-2.6,CY-3.9),(0,CY),(2.8,CY+4.1)],.9,8.85,.7)]
for yy in [-1.4,.5,2.3]:
 xx=yy*.62
 veins.append(stroke([(xx,CY+yy),(xx-1.65,CY+yy+.4)],.75,8.85,.7))
 veins.append(stroke([(xx,CY+yy),(xx+1.3,CY+yy-.45)],.75,8.85,.7))
icons[3]=icons[3]-union(veins)
icons[0]=icons[0]-stroke([(-.1,CY-3.8),(-1.15,CY-2.4),(-.3,CY-.6),(.6,CY+1.2)],1.0,8.88,.6)

# Keep side decoration, remove the previous tiny bottom symbols and repeated bottom motifs.
side_decs=[]
for i in range(4):
 ss=[]
 for side in [-1,1]:
  if i==0:
   ss.append(stroke([(side*(42.6+.65*np.sin(v*.17)),v) for v in np.linspace(-56,55,115)],1.05,7.4,.7))
   for cy in [-43,-21,1,23,45]:ss.append(motif(flame,side*43.2,cy,sx=.85,sy=2.5,h=.72))
  elif i==1:
   for cy in np.arange(-52,53,15):ss.append(motif(bolt,side*42.95,cy,sx=1.1,sy=2.3,h=.72))
  elif i==2:
   for shift in [-.8,.8]:ss.append(stroke([(side*(43+shift+.55*np.sin(v*.16)),v) for v in np.linspace(-59,59,130)],.95,7.4,.7))
  else:
   ss.append(stroke([(side*(42.9+.4*np.sin(v*.15)),v) for v in np.linspace(-57,57,120)],.95,7.4,.7))
   for j,cy in enumerate(np.arange(-51,52,11)):ss.append(motif(leaf,side*(42.9+(.4 if j%2 else -.4)),cy,sx=.70 if j%2 else -.70,sy=1.45,h=.72))
 side_decs.append(union(ss))

designs=[];reports=[]
def hole(s,z):
 ps=s.slice(z).to_polygons()
 return m.CrossSection([p[::-1] for p in ps if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))<-2000])
for name,icon,dec in zip(names,icons,side_decs):
 assert (icon^protected).volume()<1e-7,(name,'opening interference')
 s=(base+icon+dec).simplify(.000001)
 mesh=as_mesh(s);mesh.merge_vertices(digits_vertex=7);mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
 assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1,name
 s=as_solid(mesh); a=original^protected;b=s^protected
 error=(a-b).volume()+(b-a).volume();assert error<1e-6
 maxerr=0
 for z in np.linspace(.0001,7.4999,151):
  a,b=hole(original,z),hole(s,z);maxerr=max(maxerr,(a-b).area()+(b-a).area())
 assert maxerr<1e-6
 # All geometry beyond the lower edge comes from the icon, not an enlarged frame.
 below=m.Manifold.cube([150,30,15]).translate([-75,-103.6,0])
 assert ((s^below)-(icon^below)).volume()<1e-6
 designs.append(s)
 reports.append({'name':name,'internal_volume_difference_mm3':error,'hole_section_error_mm2':maxerr,'symbol_height_mm':12.5,'symbol_outward_extension_mm':7.4,'maximum_height_mm':9.3,'watertight':True,'connected_solids':1,'magnet_seats':0})
 print('VERIFIED',name,flush=True)

# Reuse the exporter with new names and outward-facing badges on the plate.
tail=text.split('fig=plt.figure(figsize=(10,13)')[1]
tail='fig=plt.figure(figsize=(10,13)'+tail
tail=tail.replace("positions=[(59.4,182.95,0),(182.95,210.6,90),(210.6,87.05,0),(87.05,59.4,90)]","positions=[(59.4,182.95,180),(182.95,210.6,90),(210.6,87.05,0),(87.05,59.4,270)]")
tail=tail.replace("('0 1 0 -1 0 0 0 0 1' if angle else '1 0 0 0 1 0 0 0 1')","{0:'1 0 0 0 1 0 0 0 1',90:'0 1 0 -1 0 0 0 0 1',180:'-1 0 0 0 -1 0 0 0 1',270:'0 -1 0 1 0 0 0 0 1'}[angle]")
tail=tail.replace("render([s],[i+1],palette,as_mesh)","render([s],[i+1],palette,as_mesh,relief=True)")
tail=tail.replace('4 BUMPER TCG ENERGIE 6mm - QUALITA 0.12.3mf','4 BUMPER ENERGIE SIMBOLI GRANDI - QUALITA 0.12.3mf')
tail=tail.replace("'maximum_relief_mm':.84,'max_height_mm':8.34","'maximum_relief_mm':1.8,'max_height_mm':9.3")
tail=tail.replace("BUMPER TCG | ENERGIE | BORDO 6 mm","BUMPER TCG | SIMBOLI CENTRALI GRANDI")
exec(compile(tail,str(root/'energy_bumpers.py'),'exec'))
assert hashlib.sha256(previous.read_bytes()).hexdigest()==previous_hash
print('SOURCE UNCHANGED',previous_hash)
