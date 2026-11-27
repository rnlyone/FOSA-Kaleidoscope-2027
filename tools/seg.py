import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
im=np.asarray(Image.open('src/ppt/media/image1.png').convert('RGB')).astype(float)
bgc=np.load('bgc.npy'); d=np.abs(im-bgc).max(2); H,W=d.shape
CX,CY=514.0,675.5
seedm=ndi.binary_erosion(d>22,iterations=1)
lab,n=ndi.label(seedm)
sizes=ndi.sum(seedm,lab,range(1,n+1))
keep=np.zeros(n+1,bool); keep[1:]=sizes>=25
lab[~keep[lab]]=0
# grow seeds into full mask
full=d>7
dist,(iy,ix)=ndi.distance_transform_edt(lab==0,return_indices=True)
grown=lab[iy,ix]; grown[(dist>7)|(~full)]=0
# keep seed pixels too
grown[lab>0]=lab[lab>0]
ramp=np.clip((d-2)/18,0,1)
pieces=[]; used=np.zeros((H,W),bool)
ids=np.unique(grown); ids=ids[ids>0]
objs=ndi.find_objects(grown)
k=0
for i in ids:
    sl=objs[i-1]
    if sl is None: continue
    y0,y1=max(sl[0].start-2,0),min(sl[0].stop+2,H); x0,x1=max(sl[1].start-2,0),min(sl[1].stop+2,W)
    reg=grown[y0:y1,x0:x1]==i
    filled=ndi.binary_fill_holes(reg)
    core=ndi.binary_erosion(filled,iterations=1)
    zone=ndi.binary_dilation(filled,iterations=1)
    a=np.where(core,1.0,ramp[y0:y1,x0:x1])*zone
    # don't steal other pieces' pixels
    other=(grown[y0:y1,x0:x1]>0)&(~reg)
    a[other]=0
    rgb=im[y0:y1,x0:x1]
    safe=np.maximum(a,1e-3)[...,None]
    un=np.clip((rgb-(1-a[...,None])*bgc)/safe,0,255)
    out=np.dstack([un,a*255]).astype('uint8')
    area=float(a.sum())
    if area<20: continue
    used[y0:y1,x0:x1]|=a>0
    ys,xs=np.nonzero(a>0.5)
    if len(ys)==0: continue
    gx,gy=xs.mean()+x0,ys.mean()+y0
    # elongation via PCA
    cov=np.cov(np.vstack([xs,ys])) if len(xs)>2 else np.eye(2)
    ev,evec=np.linalg.eigh(cov); elong=float(np.sqrt(max(ev[1],1e-6)/max(ev[0],1e-6)))
    mcol=(un[a>0.5]).mean(0)
    name=f'b{k:03d}.webp'; k+=1
    Image.fromarray(out,'RGBA').save('site/a/'+name,quality=90,method=6)
    r=float(np.hypot(gx-CX,gy-CY))
    gold = mcol[0]>mcol[2]+15
    dark = mcol.mean()<90
    pieces.append(dict(f=name,x=x0/W,y=y0/H,w=(x1-x0)/W,h=(y1-y0)/H,gx=gx/W,gy=gy/H,r=r,area=area,el=elong,gold=bool(gold),dark=bool(dark),
                       ang=float(np.degrees(np.arctan2(evec[1,1],evec[0,1])))))
# residual dust
res_a=np.clip((d-2)/18,0,1); res_a[used]=0
safe=np.maximum(res_a,1e-3)[...,None]
un=np.clip((im-(1-res_a[...,None])*bgc)/safe,0,255)
Image.fromarray(np.dstack([un,res_a*255]).astype('uint8'),'RGBA').save('site/a/dust.webp',quality=85,method=6)
print('pieces',len(pieces),'residual frac',(res_a>0.3).mean())
json.dump(dict(pieces=pieces,cx=CX/W,cy=CY/H,bg=[int(round(v)) for v in bgc]),open('bgpieces.json','w'))
import collections
print(sorted([round(p['r']) for p in pieces])[:20])
print('gold',sum(p['gold'] for p in pieces),'dark',sum(p['dark'] for p in pieces),'elong>6',sum(p['el']>6 for p in pieces))
