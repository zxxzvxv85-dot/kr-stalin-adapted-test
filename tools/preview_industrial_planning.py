"""Render the actual prototype GUI layout with its initial scripted state.

This is a layout preview, not an HOI4 screenshot: Chinese font metrics and the
nine-sliced native background are approximated. Only output/ is written.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from hoi4_politics_blocks import parse
from test_industrial_planning import ROOT, fixture, call, check

GAME = Path(os.environ.get('HOI4_GAME_ROOT', ROOT.parents[3] / 'common/Hearts of Iron IV'))
KR = Path(os.environ.get('HOI4_KR_ROOT', ROOT.parent / '1521695605'))
CN = Path(os.environ.get('HOI4_KR_CN_ROOT', ROOT.parent / '2946487287'))
COLOURS = {'Y':'#e4cb76','G':'#96bd83','R':'#db7867','g':'#adb0aa','!':'#eee9da'}


def field(node, name, fallback=''):
    found = node.one(name)
    return found.v.strip('"') if found else fallback


def entries(path):
    return parse(path.read_text(encoding='utf-8-sig'))


def nine_slice(source, size, border):
    result = Image.new('RGBA', size)
    w,h=source.size;dw,dh=size
    sx=[0,border,w-border,w];sy=[0,border,h-border,h]
    dx=[0,border,dw-border,dw];dy=[0,border,dh-border,dh]
    for x in range(3):
        for y in range(3):
            piece=source.crop((sx[x],sy[y],sx[x+1],sy[y+1]))
            piece=piece.resize((dx[x+1]-dx[x],dy[y+1]-dy[y]))
            result.alpha_composite(piece,(dx[x],dy[y]))
    return result


def render(finished=False):
    state=fixture();call(state,'open_effect')
    if finished:
        for _ in range(5):call(state,'settle')
    loc={}
    for root in [CN/'localisation',ROOT/'localisation/simp_chinese']:
        for path in root.rglob('*.yml'):
            for match in re.finditer(r'^\s*(\w+):\d*\s+"(.*)"',path.read_text(encoding='utf-8-sig'),re.M):
                loc[match[1]]=match[2]
    definitions={field(n,'name'):n for n in entries(ROOT/'common/scripted_localisation/RUS_industrial_planning_loc.txt')}
    def resolve(key, depth=0):
        assert depth<12, key
        text=loc.get(key,key)
        text=re.sub(r'\$([^$]+)\$',lambda m:resolve(m[1],depth+1),text)
        text=re.sub(r'\[\?(\w+)\|0\]',lambda m:str(int(state['vars'].get(m[1],0))),text)
        def scripted(m):
            definition=definitions[m[1]]
            for item in definition.v:
                if item.k=='text':
                    trigger=item.one('trigger')
                    if not trigger or check(trigger.v,state):return resolve(field(item,'localization_key'),depth+1)
            raise AssertionError(m[1])
        return re.sub(r'\[(Get\w+)\]',scripted,text).replace('\\n','\n')
    gui_root=entries(ROOT/'interface/RUS_industrial_planning.gui')[0]
    window=next(n for n in gui_root.v if field(n,'name')=='RUS_industrial_planning_window')
    width=int(field(window.one('size'),'width'));height=int(field(window.one('size'),'height'))
    panel=next(n for n in entries(ROOT/'common/scripted_guis/RUS_industrial_planning.txt')[0].v if n.k=='RUS_industrial_planning_gui')
    triggers={n.k:n.v for n in panel.one('triggers').v}
    gfx={field(n,'name'):n for n in entries(ROOT/'interface/RUS_industrial_planning.gfx')[0].v}
    def asset(rel):
        return Image.open(next(root/rel for root in [ROOT,KR,GAME] if (root/rel).is_file())).convert('RGBA')
    canvas=nine_slice(asset('gfx/interface/tiles/tiled_plain_bg.dds'),(width,height),64)
    draw=ImageDraw.Draw(canvas);issues=[]
    def text_box(text,x,y,w,h,font_name='hoi_16mbs',centre=False,disabled=False):
        size=int(re.search(r'\d+',font_name)[0]);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size)
        line_height=size+2;lines=[[]];colour=COLOURS['!'];line_width=0
        tokens=re.findall(r'§.|[^§]',text,re.S)
        for token in tokens:
            if token.startswith('§'):
                colour=COLOURS.get(token[1],COLOURS['!']);continue
            measure=0 if token=='\n' else draw.textlength(token,font=font)
            if token=='\n' or line_width+measure>w:
                lines.append([]);line_width=0
                if token=='\n':continue
            lines[-1].append((token,colour));line_width+=measure
        used=len(lines)*line_height
        if used>h+2:issues.append({'text':text,'required':used,'height':h,'x':x,'y':y})
        for row,line in enumerate(lines):
            full=''.join(t for t,c in line)
            px=x+(w-draw.textlength(full,font=font))/2 if centre else x
            for char,c in line:
                draw.text((px,y+row*line_height),char,font=font,fill='#77776d' if disabled else c,anchor='lt',stroke_width=0)
                px+=draw.textlength(char,font=font)
    for widget in window.v:
        name=field(widget,'name') if isinstance(widget.v,list) else ''
        if name+'_visible' in triggers and not check(triggers[name+'_visible'],state):continue
        position=widget.one('position') if isinstance(widget.v,list) else None
        if position is None:continue
        x=int(field(position,'x'));y=int(field(position,'y'))
        if widget.k=='containerWindowType':
            size=widget.one('size');sz=(int(field(size,'width')),int(field(size,'height')))
            canvas.alpha_composite(nine_slice(asset('gfx/interface/tiles/tiled_research_bg.dds'),sz,32),(x,y))
        elif widget.k in ('iconType','buttonType'):
            sprite=field(widget,'spriteType',field(widget,'quadTextureSprite'))
            if sprite in gfx:
                meta=gfx[sprite];img=asset(field(meta,'texturefile',field(meta,'textureFile')))
                frames=int(field(meta,'noOfFrames','1'))
                if frames>1:img=img.crop((0,0,img.width//frames,img.height))
            elif sprite=='GFX_closebutton':img=asset('gfx/interface/closebutton.dds')
            elif sprite=='GFX_button_123x34':img=asset('gfx/interface/button_123x34.dds')
            else:raise AssertionError(sprite)
            assert 0<=x and x+img.width<=width and 0<=y and y+img.height<=height,(name,x,y,img.size)
            disabled=name+'_click_enabled' in triggers and not check(triggers[name+'_click_enabled'],state)
            if disabled:img=Image.blend(img,Image.new('RGBA',img.size,'#252824'),.4)
            canvas.alpha_composite(img,(x,y))
            label=field(widget,'buttonText')
            if label:text_box(resolve(label),x,y+7,img.width,img.height-7,centre=True,disabled=disabled)
        elif widget.k=='instantTextBoxType':
            w=int(field(widget,'maxWidth'));h=int(field(widget,'maxHeight'))
            assert x+w<=width and y+h<=height,(name,x,y,w,h)
            text_box(resolve(field(widget,'text')),x,y,w,h,field(widget,'font'),field(widget,'format')=='center')
    # Separate caption outside the game window, so it cannot be mistaken for a screenshot.
    result=Image.new('RGB',(width,height+32),'#101719');result.paste(canvas,(0,32),canvas)
    d=ImageDraw.Draw(result)
    d.text((15,5),'布局预览 · 根据实际 GUI 坐标与脚本初始状态绘制，非游戏截图',font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15),fill='#abbcaf')
    return result,issues


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--finished',action='store_true');args=parser.parse_args()
    image,issues=render(args.finished)
    folder=ROOT/'output/industrial_planning';folder.mkdir(parents=True,exist_ok=True)
    path=folder/('finished.png' if args.finished else 'preview.png');image.save(path)
    (folder/(path.stem+'-layout.json')).write_text(json.dumps(issues,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(str(path));print(f'Text height warnings (approximate font): {len(issues)}')


if __name__=='__main__':main()
