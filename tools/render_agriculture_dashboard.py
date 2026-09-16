"""Offline proof: real GUI coordinates/art and simulated values, not an engine capture."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,re
R=Path(__file__).resolve().parents[1];OUT=R/'output/agri-gui'
data=json.loads((R/'output/national-agriculture/layout-simp_chinese.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
titlefont=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',21)
sheet=Image.new('RGB',(1060,1380),'#0a1213');d=ImageDraw.Draw(sheet)
d.text((24,15),'国家农业系统 · 调度台',font=titlefont,fill='#e4d4a7')
d.text((24,47),'离线布局预览 · 示例数值 · 游戏实际效果待验证',font=font,fill='#849b91')
names=['种植配额','农机生产','库存与贸易','季度报告']
for idx,widgets in enumerate(data['pages']):
 im=Image.new('RGBA',(502,625),'#142421');di=ImageDraw.Draw(im)
 for w in widgets:
  before=im.copy() if w.get('clip') else None
  x,y=round(w['x']),round(w['y'])
  font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
  if w['kind']=='iconType':
   a=Image.open(R/w['sprite']).convert('RGBA');a=a.resize((round(a.width*w['scale']),round(a.height*w['scale'])),Image.Resampling.LANCZOS);im.alpha_composite(a,(x,y))
  elif w['kind']=='buttonType':
   if w.get('sprite'):
    a=Image.open(R/w['sprite']).convert('RGBA');width=a.width;im.alpha_composite(a,(x,y));bw=width
   else:
    bw=33;di.rectangle((x+2,y+2,x+30,y+30),fill='#2d4439',outline='#7a7854')
   text=w['text'];di.text((x+(bw-max(di.textlength(line,font=font) for line in text.splitlines() or ['']))/2,y+6),text,font=font,fill='#eadcb7' if w['enabled'] else '#829184')
  else:
   text=w['text'];xx=x
   font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22 if w.get('font')=='hoi_24header' else 14)
   if w.get('format')=='center':xx+=(w['width']-max(di.textlength(line,font=font) for line in text.splitlines() or ['']))/2
   di.multiline_text((xx,y),text,font=font,fill='#eee8ce',spacing=5)
  if before is not None:
   cx,cy,cw,ch=map(round,w['clip']);before.paste(im.crop((cx,cy,cx+cw,cy+ch)),(cx,cy));im=before;di=ImageDraw.Draw(im)
 ox=20+520*(idx%2);oy=100+640*(idx//2)

 if idx<4:sheet.paste(im,(ox,oy));d.text((ox,oy-23),names[idx],font=font,fill='#c8af72')
 im.convert('RGB').save(OUT/f'page-{idx+1}-preview.png')
sheet.save(OUT/'dashboard-preview.png');print(OUT/'dashboard-preview.png')
