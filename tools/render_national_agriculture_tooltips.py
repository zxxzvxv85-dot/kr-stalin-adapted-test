"""Offline proof of generated Chinese tooltip text, colors and inline art."""
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)
colors = {'Y': '#ffd64c', '4': '#80c9e9', 'G': '#78d268', 'R': '#f27370', 'g': '#ababab', 'b': '#000000', '!': '#eeeade'}
text = (ROOT / 'localisation/simp_chinese/RUS_national_agriculture_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
loc = dict(re.findall(r'^\s*([\w.]+):0 "(.*)"$', text, re.M))
out = ROOT / 'output/national-agriculture'
out.mkdir(parents=True, exist_ok=True)
for key in [f'RUS_nat_tab_{i}_tt' for i in range(4)] + ['RUS_nat_reserve_1_tt'] + [f'RUS_national_agriculture.{i}.d' for i in [2, 6, 7]]:
    event = key.startswith('RUS_national_agriculture.')
    width_limit = 512 if event else 342
    canvas = Image.new('RGB', (width_limit + 28, 1800), '#e2decf' if event else '#20221f')
    draw = ImageDraw.Draw(canvas)
    normal = '#181818' if event else colors['!']
    x, y, color = 14, 12, normal
    for token in re.findall(r'§.|£[^£]+£|\\n|[+-]?\d+(?:\.\d+)?%?|.', loc[key]):
        if token.startswith('§'):
            color = normal if token[1] == '!' else colors[token[1]]
            continue
        if token == r'\n':
            x, y = 14, y+24
            continue
        is_icon = token.startswith('£')
        width = 20 if is_icon else draw.textlength(token, font=font)
        if x+width > width_limit + 14:
            x, y = 14, y+24
        if is_icon:
            name = token.strip('£').removeprefix('RUS_nat_text_')
            with Image.open(ROOT / f'gfx/interface/RUS_national_agriculture/text_{name}.png') as icon:
                assert icon.size == (20,20) and icon.mode == 'RGBA'
                assert icon.getchannel('A').getbbox()
                canvas.paste(icon, (round(x),y+2), icon)
        else:
            draw.text((x,y), token, font=font, fill=color)
        x += width
    assert y+32 < canvas.height
    result = canvas.crop((0,0,width_limit + 28,y+32))
    result.save(out / f'{key}.png')
    print(f'{key}: {result.width}x{result.height} (offline proof, not an in-game screenshot)')
