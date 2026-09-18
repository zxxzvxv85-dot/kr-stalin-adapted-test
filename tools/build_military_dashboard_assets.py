"""Compose measured cards from existing KR textures/icons; no image generation.
Preview is an offline layout proof, never a claimed HOI4 screenshot.
"""
from pathlib import Path
import json,re
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
R=Path(__file__).resolve().parents[1]
KR=R.parent/'1521695605'
DEST=R/'gfx/interface/rus_fr_dashboard/cards'
OUT=R/'output/military-dashboard'
DEST.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
source=Image.open(KR/'gfx/interface/unit_limits_entry.png').convert('RGBA')
def panel(w,h):
    # Refit the measured native metal frame with preserved 10px corners.
    result=Image.new('RGBA',(w,h))
    sw,sh=source.size
    xs=[0,10,sw-10,sw];ys=[0,10,sh-10,sh]
    dx=[0,10,w-10,w];dy=[0,10,h-10,h]
    for i in range(3):
        for j in range(3):
            piece=source.crop((xs[i],ys[j],xs[i+1],ys[j+1]))
            width,height=dx[i+1]-dx[i],dy[j+1]-dy[j]
            if i==1 and j==1:
                # Tile metal grain rather than stretching a 34px strip vertically.
                texture=Image.new('RGBA',(width,height))
                for yy in range(0,height,piece.height):
                    for xx in range(0,width,piece.width):texture.alpha_composite(piece,(xx,yy))
                result.alpha_composite(texture,(dx[i],dy[j]))
            else:result.alpha_composite(piece.resize((width,height),Image.Resampling.LANCZOS),(dx[i],dy[j]))
    return result
console=panel(498,490)
shade=Image.new('RGBA',console.size);d=ImageDraw.Draw(shade)
d.rectangle((8,8,489,481),fill=(10,11,12,165))
d.rectangle((9,7,488,54),fill=(91,24,26,170))
d.line((12,56,485,56),fill='#a48a59',width=1)
d.rectangle((18,65,179,80),fill=(0,0,0,160),outline='#6f6553')
d.line((12,397,485,397),fill='#867450');d.line((249,411,249,478),fill='#554a3b')
console.alpha_composite(shade);console.save(DEST/'console.png')
for idx in range(1,5):
    base=panel(234,141)
    overlay=Image.new('RGBA',base.size);d=ImageDraw.Draw(overlay)
    d.rectangle((7,7,226,133),fill=(17,18,19,95))
    d.rectangle((7,7,226,31),fill=(92,30,30,200))
    d.line((8,32,225,32),fill='#a48b60')
    d.rectangle((7,113,226,132),fill=(6,8,9,200))
    d.line((8,112,225,112),fill='#64533c')
    base.alpha_composite(overlay)
    frames=[base,ImageEnhance.Brightness(base).enhance(1.2),ImageEnhance.Brightness(base).enhance(.78)]
    strip=Image.new('RGBA',(702,141))
    for frame,im in enumerate(frames):strip.alpha_composite(im,(234*frame,0))
    strip.save(DEST/f'card_{idx}.png')
for state,color in [('active','#c44b38'),('ready','#dfba6b'),('done','#718c68')]:
    im=Image.new('RGBA',(234,141));d=ImageDraw.Draw(im)
    d.rectangle((3,3,230,137),outline=color,width=2)
    for x,y,sx,sy in [(4,4,1,1),(229,4,-1,1),(4,136,1,-1),(229,136,-1,-1)]:
        d.line((x,y,x+14*sx,y),fill=color,width=3);d.line((x,y,x,y+11*sy),fill=color,width=3)
    im.save(DEST/f'{state}.png')
icons=['revolutionary_military_council.dds','military_political_system.dds','red_commander_system.png','experimental_formations.dds']
for i,name in enumerate(icons,1):
    src=Image.open(R/'gfx/interface/goals/RUS_fr_military_reform'/name).convert('RGBA')
    src=src.crop(src.getbbox());src.thumbnail((82,73),Image.Resampling.LANCZOS)
    im=Image.new('RGBA',(86,77));im.alpha_composite(src,((86-src.width)//2,(77-src.height)//2));im.save(DEST/f'emblem_{i}.png')
layout=json.loads((OUT/'layout.json').read_text())
loc={}
for f in (R/'localisation/simp_chinese').glob('RUS_fr_military_reform*_l_simp_chinese.yml'):
    for k,v in re.findall(r'^\s*([\w.]+):\s*\d*\s*"(.*)"',f.read_text(encoding='utf-8-sig'),re.M):loc[k]=v.replace('\\n','\n')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
titlefont=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',19)
def render(name,states,progress):
    canvas=Image.new('RGBA',(498,490))
    for w in layout:
        ident=w['id'];state=None
        match=re.search(r'stage_(\d)_(?:status_(\w+)|(ready|active|done)_frame)',ident)
        if match:
            state=match[2] or match[3]
            if states[int(match[1])-1]!=state:continue
        if 'reform_progress_' in ident and not ident.endswith(progress):continue
        brief='stage_4' if progress=='complete' else 'stage_1' if progress=='stage_2' else 'stage_0'
        if re.search(r'(obstacles|achievements)_',ident) and not ident.endswith(('header',brief)):continue
        if w['kind']!='text':
            key=w['sprite'].replace('GFX_RUS_fr_','')
            if key in ['card_ready','card_active','card_done']:key=key[5:]
            im=Image.open(DEST/(key+'.png')).convert('RGBA')
            if w['kind']=='button':im=im.crop((0,0,234,141))
            canvas.alpha_composite(im,(w['x'],w['y']))
        else:
            value=loc[w['key']]
            value=re.sub(r'\[\?RUS_fr_xp_cost_100\|0\]','100',value)
            value=re.sub(r'\[\?RUS_fr_dashboard_reform_days_remaining\|0\]','76',value)
            color='#e4dbc7'
            if '§G' in value:color='#90b47d'
            if '§Y' in value:color='#e3bd6b'
            if '§L' in value:color='#a09c93'
            value=re.sub(r'§.','',value)
            ft=titlefont if w['font']=='hoi_20b' else font
            dr=ImageDraw.Draw(canvas)
            for j,line in enumerate(value.splitlines()):
                tw=dr.textlength(line,font=ft)
                assert tw<=w['w'],(name,w['key'],tw,w['w'])
                assert (j+1)*18<=w['h']+3,(w['key'],'height')
                dr.text((w['x']+(w['w']-tw)/2,w['y']+j*18),line,font=ft,fill=color)
    dr=ImageDraw.Draw(canvas)
    if progress=='stage_2':dr.rectangle((21,68,78,76),fill='#9b463b')
    if progress=='complete':dr.rectangle((21,68,177,76),fill='#718c68')
    canvas.save(OUT/(name+'.png'))
render('initial',['locked']*4,'idle')
render('active',['done','active','locked','locked'],'stage_2')
render('ready',['ready','locked','locked','locked'],'idle')
render('waiting',['waiting','locked','locked','locked'],'idle')
render('complete',['done']*4,'complete')
print('Native KR metal frame + 4 existing emblems. 498x490 offline previews created.')
