"""Animation packaging for ImageGen sector parts. No writes on import.

Frame atlases use native frameAnimatedSpriteType; only visual state is read.
Generated artwork remains untouched in sectors_v3. Transforms implement motion.
"""
from functools import lru_cache
import math
from PIL import Image, ImageDraw, ImageFilter
from national_plan_catalog import ROOT

SOURCE=ROOT/'tools/design/constructivist_dashboard_20261112'
PARTS=SOURCE/'sectors_v3'
FRAMES=64
# x, y, width, height, fps. Keep every horizontal atlas below 16384 pixels.
MOTIONS={
 'power_flow':(24,100,230,132,16),
 'rollers':(304,108,155,90,8),
 'freight':(6,360,248,120,16),
 'harvest':(352,390,92,92,8),
}

@lru_cache(None)
def part(name):
    with Image.open(PARTS/(name+'.png')) as im:img=im.convert('RGBA')
    assert img.getchannel('A').getextrema()[0]==0,name
    return img.crop(img.getchannel('A').getbbox())

@lru_cache(None)
def clean_background():
    """Only adopt the generated empty-track patch; preserve every other pixel."""
    original=Image.open(SOURCE/'backplate.png').convert('RGBA')
    clean=Image.open(PARTS/'clean_track.png').convert('RGBA').resize(original.size,Image.Resampling.LANCZOS)
    mask=Image.new('L',original.size)
    d=ImageDraw.Draw(mask)
    d.rectangle((20,910,518,1088),fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(5))
    # Labels and all artwork outside the train strip stay original.
    merged=Image.composite(clean,original,mask)
    return merged.resize((492,615),Image.Resampling.LANCZOS)

@lru_cache(None)
def freight_source():
    sprite=part('wagon').rotate(5,resample=Image.Resampling.BICUBIC,expand=True)
    return sprite.crop(sprite.getchannel('A').getbbox())

def motion(name,frame):
    x,y,w,h,_=MOTIONS[name]
    t=(frame%FRAMES)/FRAMES
    if name=='harvest':
        # Rotate in the full-size artwork before resampling; no jagged pixel spin.
        base=part('harvester').resize((352,352),Image.Resampling.LANCZOS)
        layer=Image.new('RGBA',(368,368));layer.alpha_composite(base,(8,8))
        return layer.rotate(-360*t,resample=Image.Resampling.BICUBIC).resize((w,h),Image.Resampling.LANCZOS)
    im=Image.new('RGBA',(w,h))
    if name=='rollers':
        base=part('drum').resize((192,192),Image.Resampling.LANCZOS)
        for cx,cy,ww,hh,phase in [(331,134,33,40,0),(388,161,24,29,.25),(441,179,17,21,.5)]:
            rotated=base.rotate(-360*(t+phase),resample=Image.Resampling.BICUBIC)
            cap=rotated.resize((ww*3,hh*3),Image.Resampling.LANCZOS).rotate(18,resample=Image.Resampling.BICUBIC,expand=True)
            cap=cap.resize((round(cap.width/3),round(cap.height/3)),Image.Resampling.LANCZOS)
            im.alpha_composite(cap,(round(cx-x-cap.width/2),round(cy-y-cap.height/2)))
    elif name=='freight':
        sprite=freight_source()
        # Geometric spacing gives a continuous perspective train, one wagon
        # replaces its predecessor per loop; offscreen entry/exit, no teleport.
        for n in range(9,-3,-1):
            scale=.62**(n-t)
            width=round(145*scale)
            if width<3 or width>650:continue
            height=round(width*sprite.height/sprite.width)
            car=sprite.resize((width,height),Image.Resampling.LANCZOS)
            cx=254-185*scale;bottom=406+72*scale
            im.alpha_composite(car,(round(cx-width/2)-x,round(bottom-height)-y))
    elif name=='power_flow':
        # Restrained highlights follow the printed wires, never neon globes.
        layer=Image.new('RGBA',(w*3,h*3));d=ImageDraw.Draw(layer)
        points=[(38,101),(102,160),(153,193),(212,211),(247,208)]
        for wire in range(3):
            pos=((t+wire*.19)%1)*4
            for k in range(12):
                u=pos-k*.022
                if not 0<=u<4:continue
                seg=int(u);f=u-seg;a,b=points[seg:seg+2]
                px=a[0]+(b[0]-a[0])*f-x;py=a[1]+(b[1]-a[1])*f+wire*4-y
                d.ellipse((px*3-1,py*3-1,px*3+2,py*3+2),fill=(242,211,161,round(205*(1-k/12))))
        im=layer.resize((w,h),Image.Resampling.LANCZOS)
    return im

def export():
    out={}
    for name,(_,_,w,h,_) in MOTIONS.items():
        assert w*FRAMES<=16384
        atlas=Image.new('RGBA',(w*FRAMES,h))
        for f in range(FRAMES):atlas.paste(motion(name,f),(f*w,0))
        out['sector_'+name]=atlas
        out['sector_'+name+'_idle']=motion(name,0) if name!='power_flow' else Image.new('RGBA',(w,h))
    return out
