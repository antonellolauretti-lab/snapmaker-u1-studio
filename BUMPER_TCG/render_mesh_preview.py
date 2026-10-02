import numpy as np
from PIL import Image
import matplotlib.colors as colors

def render(parts,slots,palette,as_mesh,relief=False):
    w,h=760,1200
    canvas=np.full((h,w,3),233,dtype=np.uint8)
    depth=np.full((h,w),-np.inf)
    tilt=np.radians(12); c,s=np.cos(tilt),np.sin(tilt)
    scale=7.55
    light=np.array([-.45,.55,.70]); light/=np.linalg.norm(light)
    for solid,slot in zip(parts,slots):
        mesh=as_mesh(solid); v=mesh.vertices
        px=w/2+v[:,0]*scale
        py=h/2-(v[:,1]*c+v[:,2]*s)*scale
        pz=-v[:,1]*s+v[:,2]*c
        rgb=np.array(colors.to_rgb(palette[slot]))
        for f,n in zip(mesh.faces,mesh.face_normals):
            tri=np.column_stack([px[f],py[f],pz[f]])
            x0=max(0,int(np.floor(tri[:,0].min()))); x1=min(w-1,int(np.ceil(tri[:,0].max())))
            y0=max(0,int(np.floor(tri[:,1].min()))); y1=min(h-1,int(np.ceil(tri[:,1].max())))
            if x1<x0 or y1<y0: continue
            a,b,d=tri; den=(b[1]-d[1])*(a[0]-d[0])+(d[0]-b[0])*(a[1]-d[1])
            if abs(den)<1e-10: continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1]; xx=xx+.5; yy=yy+.5
            u=((b[1]-d[1])*(xx-d[0])+(d[0]-b[0])*(yy-d[1]))/den
            vv=((d[1]-a[1])*(xx-d[0])+(a[0]-d[0])*(yy-d[1]))/den
            q=1-u-vv; z=u*a[2]+vv*b[2]+q*d[2]
            mask=(u>=-1e-8)&(vv>=-1e-8)&(q>=-1e-8)&(z>depth[y0:y1+1,x0:x1+1])
            diffuse=max(0,float(n@light))
            color=np.clip(rgb*(.52+.48*diffuse)+.07*diffuse**8,0,1)
            depth[y0:y1+1,x0:x1+1][mask]=z[mask]
            canvas[y0:y1+1,x0:x1+1][mask]=np.uint8(color*255)
    if relief:
        # Screen-space contact shading makes shallow, same-color relief readable.
        valid=np.isfinite(depth); occ=np.zeros((h,w))
        for dx,dy in [(2,0),(-2,0),(0,2),(0,-2),(4,2),(-4,-2),(2,4),(-2,-4)]:
            near=np.roll(depth,(dy,dx),(0,1))
            with np.errstate(invalid='ignore'): mask=(near-depth)>.24
            occ+=mask & valid & np.isfinite(near)
        factor=1-.65*np.minimum(occ/4,1)
        canvas=np.uint8(canvas.astype(float)*factor[:,:,None])
    return Image.fromarray(canvas).resize((570,900),Image.Resampling.LANCZOS)
