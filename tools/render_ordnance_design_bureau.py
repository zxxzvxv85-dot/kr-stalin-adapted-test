"""Optional layout preview from the live specification; never used by --check."""
from pathlib import Path
import json,sys
from PIL import Image,ImageDraw,ImageFont
from hoi4_politics_blocks import load
from generate_ordnance_design_bureau import ROOT,SPEC_PATH

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    game=ROOT.parents[3]/'common/Hearts of Iron IV';kr=ROOT.parent/'1521695605'
    spec=json.loads(SPEC_PATH.read_text(encoding='utf-8'));sprites={}
    for base,paths in [(game,list((game/'interface').glob('*.gfx'))+list((game/'interface/military_industrial_organization').glob('*.gfx'))),(kr,list((kr/'interface/kaiserreich').rglob('*.gfx'))),(ROOT,list((ROOT/'interface').glob('*.gfx')))]:
        for p in paths:
            try:roots=load(p)
            except (AssertionError,IndexError,UnicodeError):
                if base==ROOT:raise
                continue
            for root in roots:
                for n in root.v if isinstance(root.v,list) else []:
                    if n.k.lower()!='spritetype':continue
                    texture=n.value('texturefile',n.value('textureFile')).strip('"')
                    if texture:sprites[n.value('name').strip('"')]=(texture,int(n.value('noOfFrames',1)))
    def icon(name):
        texture,frames=sprites[name]
        path=next(b/texture for b in [ROOT,kr,game] if (b/texture).exists())
        im=Image.open(path).convert('RGBA')
        if frames>1:im=im.crop((0,0,im.width//frames,im.height))
        im.thumbnail((42,42),Image.Resampling.LANCZOS);return im
    image=Image.new('RGBA',(1280,720),'#181b19');d=ImageDraw.Draw(image)
    def f(size):return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size)
    def t(x,y,s,size=14,color='#e0ddce',anchor=None):d.text((x,y),s,font=f(size),fill=color,anchor=anchor)
    t(26,15,'陆军兵器设计总局',24,'#dec48c')
    t(1250,22,'脚本布局预览 · 非实机截图',13,'#9ba59d','ra')
    d.rectangle((20,62,315,697),fill='#242923',outline='#7b775f',width=2)
    art=Image.open(ROOT/'tools/design/ordnance_design_bureau/ordnance_bureau_master.png').convert('RGBA');art.thumbnail((210,210),Image.Resampling.LANCZOS)
    image.alpha_composite(art,(63,89));d=ImageDraw.Draw(image)
    # Show one real trait's condition/effect format, rather than developer notes.
    t(36,315,'极端环境耐受性',20,'#dec48c')
    t(36,357,'需要：',14,'#e8e4d8')
    t(46,384,'✓ 扩大试验性装备测试',14,'#8cce8c')
    t(36,423,'完成时：',14,'#e8e4d8')
    t(36,452,'此后新授予的勋章将额外提供：',13,'#b0b6ac')
    for y,label in [(485,'陆军师攻击'),(513,'陆军师防御'),(541,'陆军组织度'),(569,'突破')]:
        t(46,y,label+'：',14);t(273,y,'+0.5%',14,'#72d978','ra')
    t(36,620,'这项特质还可以培养9次。',13,'#7dbfce')
    # Right-hand viewport matches the native 905x640 scroll area, including margins.
    d.rectangle((340,62,1245,702),fill='#202622',outline='#777460',width=2)
    byid={n['id']:n for n in spec['nodes']}
    def pos(n):return (470+n['x']*87,105+n['y']*117)
    for n in spec['nodes']:
        x,y=pos(n)
        for parent in n.get('parents',[]):
            px,py=pos(byid[parent]);mid=(py+y)//2+15
            d.line([(px,py+27),(px,mid),(x,mid),(x,y-28)],fill='#84958c',width=2)
    for n in spec['nodes']:
        if n.get('exclusive') and n['id']<n['exclusive']:
            a,b=sorted([pos(n),pos(byid[n['exclusive']])]);d.line((a[0]+30,a[1],b[0]-30,b[1]),fill='#b49b68',width=2)
            t((a[0]+b[0])/2,a[1]-9,'×',16,'#d6bc79','mm')
    for n in spec['nodes']:
        x,y=pos(n);border='#cbb06f' if n.get('source') else '#7e9287'
        d.rounded_rectangle((x-29,y-30,x+29,y+30),radius=8,fill='#303b34',outline=border,width=2)
        art=icon(n['icon']);image.alpha_composite(art,(int(x-art.width/2),int(y-art.height/2)));d=ImageDraw.Draw(image)
        s=n['name']
        import math
        count=max(1,math.ceil(f(12).getlength(s)/142));step=math.ceil(len(s)/count)
        lines=[s[i:i+step] for i in range(0,len(s),step)]
        for i,line in enumerate(lines):t(x,y+35+i*17,line,12,anchor='mt')
        if n.get('repeat'):t(x+35,y-28,f'1/{n["repeat"]}',12,'#ddc984')
    out=ROOT/'output/ordnance_mio_drawio_20261019/陆军兵器设计总局_实现布局预览.png'
    out.parent.mkdir(parents=True,exist_ok=True);image.convert('RGB').save(out)
    print(out)
if __name__=='__main__':main()
