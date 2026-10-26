"""Native-size layout proof from generated GUI, textures and installed font atlases.

Not an engine screenshot. Writes only ignored output/education_system previews.
"""
from pathlib import Path
import re
from PIL import Image,ImageDraw
from hoi4_politics_blocks import load
from hoi4_bitmap_fonts import measure,render,font_data,plain
from generate_education_reform import ROOT,GUI,GFX,SGUI,VARS
from test_education_reform import initialized,unlock_all

COLOURS={'C':'#72c7de','Y':'#e4bf61','O':'#de7852','G':'#86bd87','R':'#ff3232','b':'#000000','!':'#e3dfcf'}
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
                key=t.value('localization_key')
                s=s.replace('['+name+']',loc.get(key,key));break
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
    loc=localisation();window=load(ROOT/GUI)[0].v[0];height=int(window.one('size').value('height'));width=int(window.one('size').value('width'));im=Image.new('RGBA',(width,height),'#222b27');d=ImageDraw.Draw(im)
    d.rectangle((1,1,width-2,height-2),outline='#a39464')
    scripted=load(ROOT/SGUI)[0].v[0];props=scripted.one('properties');triggers=scripted.one('triggers')
    sprites={n.value('name').strip('"'):n for root in load(ROOT/GFX) for n in root.v}
    warnings=[]
    for n in window.v:
        if n.k not in ('iconType','instantTextBoxType','buttonType'):continue
        name=n.value('name').strip('"');x=int(n.one('position').value('x'));y=int(n.one('position').value('y'))
        visibility=triggers.one(name+'_visible') if triggers else None
        if visibility and not m.check(visibility):continue
        if n.k=='buttonType':
            sprite=sprites.get(n.value('quadTextureSprite').strip('"'))
            path=ROOT/sprite.value('texturefile').strip('"') if sprite else GAME/'gfx/interface/button_123x34.dds'
            image=Image.open(path).convert('RGBA');im.alpha_composite(image,(x,y))
            if n.one('buttonText'):
                text=resolve(loc[n.value('buttonText').strip('"')],m,loc)
                render(im,x+(image.width-measure('hoi_16mbs',text))/2,y+9,text,'hoi_16mbs',COLOURS['!'])
            continue
        if n.k=='iconType':
            property=props.one(name) if props else None
            image_key=property.value('image') if property else None
            sprite=sprites[resolve(image_key.strip('"'),m,loc) if image_key else n.value('spriteType').strip('"')];relative=sprite.value('texturefile').strip('"')
            path=next(r/relative for r in (ROOT,GAME) if (r/relative).is_file())
            image=Image.open(path).convert('RGBA');frames=int(sprite.value('noOfFrames','1'));w=image.width//frames
            property=props.one(name);frame=round(m.vars.get(property.value('frame'),1)) if property else int(n.value('frame','1'))
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

def preview_category(m,dest):
    """Include native category heading/description above the unchanged GUI.

    Width/font come from countrydecisionview.gui; vertical flow is a layout
    proof, not an emulation of the engine's category-height calculation.
    """
    import json
    path=ROOT/'localisation/replace/RUS_education_dashboard_l_simp_chinese.yml'
    loc=localisation()|{k:json.loads(v) for k,v in re.findall(r'^ ([\w.]+):0 (".*")$',path.read_text(encoding='utf-8-sig'),re.M)}
    font='hoi_16mbs';description=resolve(loc['RUS_education_reform_category_desc'],m,loc)
    lines=wrap(description,font,470) if description else []
    line_height=max(f['height'] for f in font_data(font))
    dashboard=Image.open(preview(m,dest.with_name(dest.stem+'_GUI.png'))).convert('RGBA')
    offset=58+(6+len(lines)*line_height+12 if lines else 8)
    im=Image.new('RGBA',(520,offset+dashboard.height+8),'#222b27')
    d=ImageDraw.Draw(im);d.rectangle((1,1,518,im.height-2),outline='#a39464')
    title=loc['RUS_education_reform_category']
    render(im,(520-measure('hoi_20b',title))/2,20,title,'hoi_20b',COLOURS['!'])
    d.line((8,56,512,56),fill='#6f6b50')
    colour=COLOURS['!']
    for row,line in enumerate(lines):
        x=14
        for chunk in re.split(r'(§.)',line):
            if chunk.startswith('§'):colour=COLOURS.get(chunk[1],COLOURS['!']);continue
            render(im,x,64+row*line_height,chunk,font,colour);x+=measure(font,chunk)
        assert x<=14+470
    im.alpha_composite(dashboard,(8,offset))
    im.convert('RGB').save(dest)
    return str(dest)


def main():
    m=initialized();paths=[preview(m,ROOT/'output/education_system/教育面板_初始.png')]
    paths.append(preview_category(m,ROOT/'output/education_system/教育分类_介绍与面板.png'))
    opened=initialized();opened.flags.add('RUS_edu_intro_open')
    paths.append(preview_category(opened,ROOT/'output/education_system/教育分类_展开介绍.png'))
    assert m.start('literacy');paths.append(preview(m,ROOT/'output/education_system/教育面板_单项活动.png'))
    m=initialized()
    m.flags.update({'RUS_edu_culture_open','RUS_edu_technical_open'});m.vars.update({VARS['basic']:47.39,VARS['higher']:18.67,VARS['heat']:68.37,'RUS_education_completed_activities':6});m.call('RUS_education_refresh')
    from education_reform_content import ACTIVITIES
    for a,days in [('literacy',39),('university',75),('mentoring',42)]:
        m.vars['RUS_edu_category']=next(x['category'] for x in ACTIVITIES if x['id']==a)
        assert m.start(a);m.vars['RUS_edu_days_'+a]=days
    m.vars['RUS_edu_category']=4
    m.call('RUS_education_refresh');paths.append(preview(m,ROOT/'output/education_system/教育面板_活动示意.png'))
    for category in range(1,7):
        m.vars.update(RUS_edu_category=category);m.call('RUS_education_refresh')
        paths.append(preview(m,ROOT/f'output/education_system/海报分类_{category}.png'))
    for category in range(1,7):
        m=unlock_all(initialized());m.vars.update(RUS_edu_category=category)
        a=next(a for a in ACTIVITIES[14:] if a['category']==category)
        assert m.start(a['id']);paths.append(preview(m,ROOT/f'output/education_system/新增海报_{category}.png'))
    # All campaign names must fit the existing two-line label, including long slogans.
    for a in ACTIVITIES:
        assert len(wrap(a['name'],'hoi_16mbs',158))*max(f['height'] for f in font_data('hoi_16mbs'))<=42,a['id']
    print('PASS: installed font atlases, generated coordinates, bounded text and packaged art. Not engine screenshots.');print('\n'.join(paths))
if __name__=='__main__':main()
