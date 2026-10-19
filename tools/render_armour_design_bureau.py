"""Render the actual live specification at native grid, frame and texture sizes.

Review annotations are outside the entry frames. This is not a game screenshot.
"""
from pathlib import Path
import json,sys,textwrap
from PIL import Image,ImageDraw,ImageFont
from hoi4_politics_blocks import load
from generate_armour_design_bureau import ROOT,SPEC_PATH

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    game=ROOT.parents[3]/'common/Hearts of Iron IV';kr=ROOT.parent/'1521695605'
    spec=json.loads(SPEC_PATH.read_text(encoding='utf-8'));sprites={}
    for base in [game,kr,ROOT]:
        for p in (base/'interface').rglob('*.gfx'):
            try:ns=load(p)
            except (AssertionError,IndexError,UnicodeError):continue
            for root in ns:
                for n in root.v if isinstance(root.v,list) else []:
                    if n.k.lower()=='spritetype':
                        path=n.value('texturefile',n.value('textureFile')).strip('"')
                        if path:sprites[n.value('name').strip('"')]=(path,int(n.value('noOfFrames',1)))
    def icon(name):
        texture,frames=sprites[name];p=next(b/texture for b in [ROOT,kr,game] if (b/texture).exists());im=Image.open(p).convert('RGBA')
        if frames>1:im=im.crop((0,0,im.width//frames,im.height))
        assert im.size==(48,48),(name,im.size)
        return im
    im=Image.new('RGBA',(1280,720),'#1c211e');d=ImageDraw.Draw(im)
    def font(n):return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
    def text(x,y,s,size=13,color='#e3dfcc',anchor=None):d.text((x,y),s,font=font(size),fill=color,anchor=anchor)
    text(24,17,'陆军装甲设计总局',24,'#dbc48f')
    text(1253,25,'脚本布局预览 · 非实机截图',13,'#a1a99e','ra')
    d.rectangle((20,62,319,700),fill='#242b25',outline='#858168',width=2)
    art=Image.open(ROOT/'tools/design/armour_design_bureau/armour_bureau_master.png').convert('RGBA');art.thumbnail((205,205),Image.Resampling.LANCZOS);im.alpha_composite(art,(68,82));d=ImageDraw.Draw(im)
    text(38,310,'指导作战',20,'#dec48b');text(38,352,'需要：');text(48,380,'扩大武器设计交流');text(48,407,'联合设计生产');text(48,434,'经费大于 1000',13,'#d7c175')
    text(38,479,'完成时：');text(48,507,'经费：−1000',13,'#dc7b70');text(48,534,'装甲生产花费：+2%',13,'#dc7b70');text(48,561,'生活消费品期望：+1%',13,'#dc7b70');text(48,588,'装甲营战斗宽度：−0.05',13,'#80d188');text(48,615,'升级规模需求：+10%',13,'#dc7b70');text(38,659,'这项特质还可以培养9次。',13,'#87bdc3')
    d.rectangle((340,62,1245,702),fill='#242b26',outline='#858168',width=2)
    byid={n['id']:n for n in spec['nodes']}
    # Include the entire native 87x117 entry in the available 885x620 area.
    def position(n):return (445+n['x']*87,76+n['y']*117)
    def center(n):x,y=position(n);return x+43,y+40
    for n in spec['nodes']:
        assert 0<=n['x']*87 and n['x']*87+87<=885 and 10+n['y']*117+117<=620
        x,y=center(n)
        for i,p in enumerate(n.get('parents',[])):
            sx,sy=center(byid[p]);mid=sy+45+(y-sy-80)*(.35+.1*i)
            d.line([(sx+3,sy+40),(sx+3,mid),(x+3,mid),(x+3,y-28)],fill='#91aaa4',width=1)
    frame=Image.open(game/'gfx/interface/military_industrial_organization/mio_department_trait.dds').convert('RGBA').crop((128,0,192,80))
    for n in spec['nodes']:
        x,y=center(n);im.alpha_composite(frame,(x-29,y-40));im.alpha_composite(icon(n['icon']),(x-21,y-32));d=ImageDraw.Draw(im)
        label=n['name']
        if n['id']=='okmo':label='整合莫洛佐夫\n机械制造设计局'
        elif len(label)>12:label='\n'.join(textwrap.wrap(label,8))
        for i,line in enumerate(label.splitlines()):text(x+3,y+43+i*16,line,11,anchor='mt')
        if n.get('repeat'):text(x+32,y-34,'1/10',11,'#e4cc8d')
    path=ROOT/'output/armour_mio_drawio_20261019/陆军装甲设计总局_实现布局预览.png';path.parent.mkdir(parents=True,exist_ok=True);im.convert('RGB').save(path)
    print(path)
if __name__=='__main__':main()
