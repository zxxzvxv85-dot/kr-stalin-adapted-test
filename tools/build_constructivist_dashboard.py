"""Export generated backplate and code-native animated UI indicators.

Only --write produces assets. Original ImageGen art remains unmodified.
Geometric indicators are UI graphics; they never repaint the source artwork.
"""
import argparse, math, json
from pathlib import Path
from PIL import Image, ImageDraw
from national_plan_catalog import ROOT

SOURCE=ROOT/'tools/design/constructivist_dashboard_20261112/backplate.png'
DEST=ROOT/'gfx/interface/RUS_national_plan_dashboard'
IVORY=(225,203,157,235);RED=(223,55,29,245);DARK=(20,20,18,250)

def indicator(name,f):
    size=(120,120) if name=='rotor' else (64,48)
    im=Image.new('RGBA',size);d=ImageDraw.Draw(im)
    t=f/24
    if name=='rotor':
        # The text disk stays still; only this narrow segmented track turns.
        for j in range(16):
            a=(j*22.5+t*360)%360
            d.arc((3,3,117,117),a,a+13,fill=IVORY if j%4 else RED,width=3)
            if j%4==0:
                r=57;ang=math.radians(a)
                x,y=60+r*math.cos(ang),60+r*math.sin(ang)
                d.ellipse((x-2,y-2,x+2,y+2),fill=RED)
    elif name=='electric':
        for j in range(4):
            d.arc((-15+j*10,8,35+j*10,60),206,300,fill=(*IVORY[:3],55+int(170*((t+j/4)%1))),width=2)
    elif name=='furnace':
        for j in range(3):
            alpha=int(100+140*(.5+.5*math.sin(t*math.tau+j)))
            x=j*17
            d.polygon([(x,42),(x+7,19),(x+17,19),(x+22,42)],fill=(*RED[:3],alpha))
            d.line((x+8,14,x+8,5),fill=(*IVORY[:3],alpha),width=2)
    elif name=='transport':
        # Small repeated angular cars run on an existing diagonal corridor.
        for j in range(4):
            x=((j*22+t*22)%88)-22;y=36-x*.35
            d.polygon([(x,y),(x+12,y-4),(x+12,y-10),(x,y-6)],fill=IVORY)
            d.line((x+1,y+3,x+13,y-1),fill=RED,width=2)
    elif name=='farm':
        for j in range(8):
            a=math.tau*(j/8+t);c=(31,24)
            pts=[(c[0]+r*math.cos(a+o),c[1]+r*math.sin(a+o)) for r,o in [(8,0),(21,0),(21,.22),(8,.38)]]
            d.polygon(pts,fill=RED if j%2 else IVORY)
        d.ellipse((27,20,35,28),fill=DARK,outline=IVORY)
    return im

def export():
    result={'background':Image.open(SOURCE).convert('RGBA').resize((492,615),Image.Resampling.LANCZOS)}
    for name in ('rotor','electric','furnace','transport','farm'):
        first=indicator(name,0);w,h=first.size;sheet=Image.new('RGBA',(w*24,h))
        for f in range(24):sheet.paste(indicator(name,f),(f*w,0))
        result[name]=sheet
    for name,(w,h) in {'header':(428,20),'sector':(134,32),'area':(158,166),'region':(136,24),'score':(92,100),'close':(136,23)}.items():
        im=Image.new('RGBA',(w*3,h));d=ImageDraw.Draw(im)
        d.rectangle((w,0,w*2-1,h-1),fill=(239,218,175,22),outline=(239,218,175,120))
        d.rectangle((w*2,0,w*3-1,h-1),fill=(212,57,27,65),outline=RED)
        if name=='area':
            im=Image.new('RGBA',(w*3,h));d=ImageDraw.Draw(im)
            d.rectangle((w,0,w*2-1,h-1),fill=(239,218,175,14))
            d.rectangle((w*2,0,w*3-1,h-1),fill=(212,57,27,24))
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
