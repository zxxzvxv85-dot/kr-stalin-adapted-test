"""Package generated art into a moving wheel and stationary UI layers.

Only --write produces assets. ImageGen sources remain unmodified. Resizing,
alpha masks and rotation are runtime asset packaging, not source repainting.
"""
import argparse, math, json
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw
from national_plan_catalog import ROOT

SOURCE=ROOT/'tools/design/constructivist_dashboard_20261112/backplate.png'
WHEEL_SOURCE=SOURCE.parent/'motion_v2/rotor_source.png'
DEST=ROOT/'gfx/interface/RUS_national_plan_dashboard'
IVORY=(225,203,157,235);RED=(223,55,29,245);DARK=(20,20,18,250)
WHEEL_XY=(136,202)
WHEEL_SIZE=224
PREVIEW_FRAMES=192
ROTATION_SECONDS=24

@lru_cache(None)
def wheel():
    with Image.open(WHEEL_SOURCE) as source:im=source.convert('RGBA')
    bounds=im.getchannel('A').getbbox()
    assert bounds and im.getchannel('A').getextrema()[0]==0,'Wheel needs real transparency'
    im=im.crop(bounds).resize((216,216),Image.Resampling.LANCZOS)
    result=Image.new('RGBA',(WHEEL_SIZE,WHEEL_SIZE));result.paste(im,(4,4))
    return result

@lru_cache(None)
def foreground():
    """Stationary original score face and plaques above the rotating disk."""
    im=Image.new('RGBA',(504,620));im.alpha_composite(Image.open(SOURCE).convert('RGBA').resize((492,615),Image.Resampling.LANCZOS),(6,0))
    mask=Image.new('L',(504*4,620*4));d=ImageDraw.Draw(mask)
    d.ellipse(tuple(v*4 for v in (192,258,304,370)),fill=255)
    for rect in [(25,244,163,277),(344,244,482,277),(25,477,176,509),(328,477,482,509)]:
        d.rectangle(tuple(v*4 for v in rect),fill=255)
    im.putalpha(mask.resize((504,620),Image.Resampling.LANCZOS))
    return im

def indicator(name,f):
    assert name=='rotor'
    return wheel().rotate(-360*f/PREVIEW_FRAMES,resample=Image.Resampling.BICUBIC)

def export():
    result={'background':Image.open(SOURCE).convert('RGBA').resize((492,615),Image.Resampling.LANCZOS)}
    result['wheel']=wheel()
    result['wheel_empty']=Image.new('RGBA',(WHEEL_SIZE,WHEEL_SIZE))
    mask=Image.new('RGBA',(WHEEL_SIZE,WHEEL_SIZE),'white');mask.putalpha(wheel().getchannel('A'))
    result['wheel_mask']=mask
    result['foreground']=foreground()
    for name,(w,h) in {'header':(428,20),'sector':(134,32),'area':(158,166),'region':(136,24),'score':(92,100),'close':(136,23)}.items():
        im=Image.new('RGBA',(w*3,h));d=ImageDraw.Draw(im)
        d.rectangle((w,0,w*2-1,h-1),fill=(239,218,175,22),outline=(239,218,175,120))
        d.rectangle((w*2,0,w*3-1,h-1),fill=(212,57,27,65),outline=RED)
        if name=='area':
            im=Image.new('RGBA',(w*3,h));d=ImageDraw.Draw(im)
            d.rectangle((w,0,w*2-1,h-1),fill=(239,218,175,14))
            d.rectangle((w*2,0,w*3-1,h-1),fill=(212,57,27,24))
        if name=='score':
            # The invisible circular-face control must never expose a rectangle,
            # including native hover and pressed frames.
            im=Image.new('RGBA',(w*3,h))
        result['hit_'+name]=im
    for name,(w,h) in {'selected_sector':(112,2),'selected_region':(123,2),'stage_pip':(6,4)}.items():
        result[name]=Image.new('RGBA',(w,h),RED if name!='stage_pip' else IVORY)
    im=Image.new('RGBA',(432,419),(19,20,18,252));d=ImageDraw.Draw(im)
    d.rectangle((0,0,431,418),outline=IVORY,width=2)
    d.line((18,38,413,38),fill=RED,width=2)
    result['ledger']=im
    DEST.mkdir(parents=True,exist_ok=True)
    for name,im in result.items():im.save(DEST/(name+'.png'))
    print(json.dumps({k:list(v.size) for k,v in result.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
    if a.write:export()
    else:print('Read-only. Use --write to export assets.')
