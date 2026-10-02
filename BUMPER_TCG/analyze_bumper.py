import zipfile, xml.etree.ElementTree as E, collections, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parent
z=zipfile.ZipFile(root.parent/'PROGETTI DEFINITIVI/4 BUMPER TCG.3mf')
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
name=next(n for n in z.namelist() if n.startswith('3D/Objects/'))
doc=E.fromstring(z.read(name))
z.extract('Metadata/plate_1.png',root)
for obj in doc.findall('m:resources/m:object',ns):
 v=np.array([[float(p.get(c)) for c in 'xyz'] for p in obj.findall('.//m:vertex',ns)])
 f=np.array([[int(p.get(c)) for c in ('v1','v2','v3')] for p in obj.findall('.//m:triangle',ns)])
 np.savez(root/('object'+obj.get('id')+'.npz'),v=v,f=f)
 print(obj.get('id'),v.shape,f.shape,'bounds',v.min(0),v.max(0),'z',np.unique(v[:,2]).tolist())
 im=Image.new('RGB',(1100,1100),'white'); d=ImageDraw.Draw(im)
 for t in f:
  pts=[(float(v[i,0]*4+550),float(550-v[i,1]*4)) for i in t]
  d.polygon(pts,outline='black')
 im.save(root/('object'+obj.get('id')+'.png'))
