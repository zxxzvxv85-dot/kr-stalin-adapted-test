"""Static pixel-layout review only; this is not an in-game screenshot.

Run with an explicit output path. Uses the exact GUI coordinate constants and
existing portrait textures; it does not change any gameplay or generated file.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont
from doudizhu_gui import ASSET_DIR, HAND_X, HAND_Y, HAND_SELECTED_Y, HAND_STEP
from hoi4_politics_blocks import load

ROOT = Path(__file__).resolve().parents[1]


def preview(target: Path):
    base = Image.new('RGBA',(1000,710),'#292d2b')
    d = ImageDraw.Draw(base)
    font_path = 'C:/Windows/Fonts/msyh.ttc'

    def label(value, box, size=16, colour='#d8d9cd'):
        x,y,w,h = box
        font = ImageFont.truetype(font_path,size)
        lines=[]
        for part in value.split('\n'):
            current=''
            for c in part:
                if d.textlength(current+c,font=font)>w and current:
                    lines.append(current);current=''
                current+=c
            lines.append(current)
        for i,line in enumerate(lines):
            tw=d.textlength(line,font=font)
            d.text((x+(w-tw)/2,y+i*(size+2)),line,font=font,fill=colour)

    def paste(filename, x, y, size=None):
        im=Image.open(ROOT/ASSET_DIR/filename).convert('RGBA')
        if size:im=im.resize(size,Image.Resampling.LANCZOS)
        base.alpha_composite(im,(x,y))

    def portrait(sprite,x,y,small=False):
        roots=[ROOT,ROOT.parent/'1521695605',Path('D:/steam/steamapps/common/Hearts of Iron IV')]
        match=None
        for root in roots:
            if match:break
            for path in (root/'interface').rglob('*.gfx'):
                source=path.read_text(encoding='utf-8-sig',errors='replace')
                if sprite not in source:continue
                for node in load(path):
                    for entry in node.v if isinstance(node.v,list) else []:
                        if entry.value('name').strip('"')==sprite:
                            match=(entry.value('texturefile') or entry.value('textureFile')).strip('"')
                            break
                if match:break
        if not match:raise ValueError(sprite)
        path=next(r/match for r in roots if (r/match).is_file())
        im=Image.open(path).convert('RGBA')
        im=im.resize((65,67) if small else (66,88),Image.Resampling.LANCZOS)
        base.alpha_composite(im,(x,y+11 if small else y))

    d.rectangle((1,1,998,678),outline='#93937a',width=2)
    d.line((14,82,985,82),fill='#716e56')
    paste('felt.png',12,92)
    label('休息室 · 斗地主',(38,17,924,32),24,'#e7d6a7')
    label('三位牌友，一副好牌。',(235,54,530,26))
    label('×',(964,10,28,28),22)
    label('三张底牌',(420,93,160,26))
    for index,card in enumerate([26,43,54]):paste(f'card_{card:02d}.png',438+42*index,121,(36,53))
    for seat,(sprite,name,x,y,px,py,pw,small) in enumerate([
        ('GFX_portrait_RUS_iosif_stalin_civilian_small','约瑟夫·斯大林',48,492,20,476,140,True),
        ('GFX_portrait_RUS_lazar_kaganovich_civilian_small','拉扎尔·卡冈诺维奇',84,151,25,141,184,True),
        ('GFX_portrait_RUS_mikhail_kalinin_civilian_small','米哈伊尔·加里宁',850,151,791,141,184,True),
    ],1):
        paste('portrait_frame.png',x-3,y+8)
        portrait(sprite,x,y,small)
        label(name,(px,584 if seat==1 else 248,pw,42))
        label('地主' if seat==1 else '农民',(px,651 if seat==1 else 295,pw,24),16,'#e3c56c')
        label('手牌 '+str({1:20,2:15,3:17}[seat])+' 张',(px,627 if seat==1 else 324,pw,24))
    label('你的座位',(20,465,140,24),16,'#e3c56c')
    label('上一手：拉扎尔·卡冈诺维奇',(215,246,570,26))
    table=Image.open(ROOT/ASSET_DIR/'table_faces.png')
    for index,card in enumerate([29,31]):
        base.alpha_composite(table.crop(((card-1)*34,0,card*34,50)),(round(500-27/2-17+index*27),282))
    label('轮到你出牌  ·  点击手牌选中，再点击“出牌”',(225,378,550,92),20,'#e7d6a7')
    label('已选 2 张',(425,476,300,24))
    for index,card in enumerate([1,2,4,7,9,10,13,16,18,21,22,25,30,33,37,42,44,47,49,54]):
        paste(f'card_{card:02d}.png',HAND_X+index*HAND_STEP,HAND_SELECTED_Y if card in [42,44] else HAND_Y)
    for x,value in [(242,'出牌'),(377,'不出'),(512,'提示'),(647,'取消选择'),(846,'结束本局')]:
        d.rounded_rectangle((x,614,x+122,647),radius=2,fill='#494b3a',outline='#a29d75')
        label(value,(x,619,123,28))
    label('玩法说明',(821,653,150,24))
    label('静态布局检查 · 原生界面坐标与实际纹理 · 非游戏截图',(0,685,1000,24),13,'#a3a79e')
    target.parent.mkdir(parents=True,exist_ok=True)
    base.convert('RGB').save(target)
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    print(preview(args.output.resolve()))
