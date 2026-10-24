"""Native-size layout proof from generated GUI, textures and installed font atlases.

Not an engine screenshot. Writes only ignored output/education_system previews.
"""
from pathlib import Path
import re
from PIL import Image,ImageDraw
from hoi4_politics_blocks import load
from hoi4_bitmap_fonts import measure,render,font_data,plain
from generate_education_reform import ROOT,GUI,GFX,SGUI,VARS
from test_education_reform import initialized

COLOURS={'C':'#72c7de','Y':'#e4bf61','O':'#de7852','G':'#86bd87','!':'#e3dfcf'}
GAME=ROOT.parents[3]/'common/Hearts of Iron IV'

def inline_image(token):
    key='GFX_'+token.strip('£')
    sprite=next(n for root in load(ROOT/GFX) for n in root.v if n.value('name').strip('"')==key)
    relative=sprite.value('texturefile').strip('"')
    return Image.open(next(r/relative for r in (ROOT,GAME) if (r/relative).is_file())).convert('RGBA')

def rich_width(font,text):
    return sum(inline_image(t).width if t.startswith('£') else measure(font,t) for t in re.split(r'(£[^£]+£)',text))

def localisation():
    import json
    path=ROOT/'localisation/simp_chinese/RUS_education_dashboard_l_simp_chinese.yml'
    return {k:json.loads(v).replace('\\n','\n') for k,v in re.findall(r'^ ([\w.]+):0 (".*")$',path.read_text(encoding='utf-8-sig'),re.M)}

def resolve(s,m,loc):
    definitions=load(ROOT/'common/scripted_localisation/RUS_education_dashboard.txt')
    for n in definitions:
        name=n.value('name')
        for t in n.children('text'):
            if not t.one('trigger') or m.check(t.one('trigger')):
                s=s.replace('['+name+']',loc[t.value('localization_key')]);break
    return re.sub(r'\[\?([\w]+)\|(\d+)\]',lambda x:f'{m.vars.get(x[1],0):.{x[2]}f}',s)

def wrap(text,font,width):
    lines=[];line='';i=0
    for paragraph in text.split('\n'):
        line='';i=0
        while i<len(paragraph):
            if paragraph[i]=='§':line+=paragraph[i:i+2];i+=2;continue
            if paragraph[i]=='£':
                stop=paragraph.index('£',i+1);c=paragraph[i:stop+1];i=stop+1
            else:c=paragraph[i];i+=1
            if rich_width(font,line+c)>width and plain(line):lines.append(line);line=c
            else:line+=c
        lines.append(line)
    return lines

def preview(m,dest):
    loc=localisation();window=load(ROOT/GUI)[0].v[0];im=Image.new('RGBA',(498,509),'#222b27');d=ImageDraw.Draw(im)
    d.rectangle((1,1,496,507),outline='#a39464');d.line((8,29,488,29),fill='#6f6b50')
    props=load(ROOT/SGUI)[0].v[0].one('properties')
    sprites={n.value('name').strip('"'):n for root in load(ROOT/GFX) for n in root.v}
    warnings=[]
    for n in window.v:
        if n.k not in ('iconType','instantTextBoxType'):continue
        name=n.value('name').strip('"');x=int(n.one('position').value('x'));y=int(n.one('position').value('y'))
        if n.k=='iconType':
            sprite=sprites[n.value('spriteType').strip('"')];image=Image.open(ROOT/sprite.value('texturefile').strip('"')).convert('RGBA');frames=int(sprite.value('noOfFrames'));w=image.width//frames
            property=props.one(name);frame=round(m.vars.get(property.value('frame'),1)) if property else 1
            im.alpha_composite(image.crop(((frame-1)*w,0,frame*w,image.height)),(x,y));continue
        text=resolve(loc[n.value('text').strip('"')],m,loc);font=n.value('font').strip('"');width=int(n.value('maxWidth'));lines=wrap(text,font,width)
        height=max(f['height'] for f in font_data(font))
        if len(lines)*height>int(n.value('maxHeight')):warnings.append((name,'text height',len(lines)*height,n.value('maxHeight')))
        colour=COLOURS['!']
        for row,line in enumerate(lines):
            xx=x+(width-rich_width(font,line))/2
            for chunk in re.split(r'(§.|£[^£]+£)',line):
                if chunk.startswith('§'):colour=COLOURS.get(chunk[1],COLOURS['!']);continue
                if chunk.startswith('£'):
                    icon=inline_image(chunk);im.alpha_composite(icon,(round(xx),round(y+row*height+(height-icon.height)/2)));xx+=icon.width;continue
                render(im,xx,y+row*height,chunk,font,colour);xx+=measure(font,chunk)
    assert not warnings,warnings
    dest.parent.mkdir(parents=True,exist_ok=True);im.convert('RGB').save(dest);return str(dest)

def main():
    m=initialized();paths=[preview(m,ROOT/'output/education_system/教育面板_初始.png')]
    m.flags.update({'RUS_edu_culture_open','RUS_edu_technical_open'});m.vars.update({VARS['basic']:47.39,VARS['higher']:18.67,VARS['heat']:68.37,'RUS_education_completed_activities':6});m.call('RUS_education_refresh')
    for a,days in [('literacy',39),('university',75),('mentoring',42)]:assert m.start(a);m.vars['RUS_edu_days_'+a]=days
    m.call('RUS_education_refresh');paths.append(preview(m,ROOT/'output/education_system/教育面板_活动示意.png'))
    print('PASS: installed font atlases, generated coordinates, bounded text and packaged art. Not engine screenshots.');print('\n'.join(paths))
if __name__=='__main__':main()
