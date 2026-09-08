"""Render extracted GUI geometry, labels and real icons for offline inspection."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/national-agriculture'
for source in OUT.glob('layout-*.json'):
    data = json.loads(source.read_text(encoding='utf-8'))
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc' if data['locale']=='simp_chinese' else 'C:/Windows/Fonts/arial.ttf', 16)
    sheet = Image.new('RGB', (1044, 1320), '#171918')
    d = ImageDraw.Draw(sheet)
    d.text((14, 7), 'OFFLINE LAYOUT PROOF / NOT AN IN-GAME SCREENSHOT', font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16), fill='white')
    for p, widgets in enumerate(data['pages']):
        ox, oy = 10+(p%2)*522, 38+(p//2)*638
        d.rectangle((ox,oy,ox+502,oy+625), fill='#30332b', outline='#62675b')
        for w in widgets:
            x,y=ox+w['x'],oy+w['y']
            if w['kind']=='iconType':
                assert w['sprite'], w['name']
                with Image.open(ROOT/w['sprite']) as im:
                    icon=im.convert('RGBA')
                icon=icon.resize((round(icon.width*w['scale']),round(icon.height*w['scale'])),Image.Resampling.LANCZOS)
                assert x+icon.width<=ox+502 and y+icon.height<=oy+625
                sheet.paste(icon,(x,y),icon)
            elif w['kind']=='buttonType':
                width=26 if w['name'].endswith(('_minus','_plus')) else 123
                d.rectangle((x,y,x+width-1,y+33),fill='#41473a' if w['enabled'] else '#33362f',outline='#888979')
                tw=d.textlength(w['text'],font=font)
                d.text((x+(width-tw)/2,y+6),w['text'],font=font,fill='#e5e0c7' if w['enabled'] else '#85867a')
            else:
                d.text((x,y),w['text'],font=font,fill='#e4e3d7')
    destination=OUT/f"layout-{data['locale']}.png"
    sheet.save(destination)
    print(destination)
