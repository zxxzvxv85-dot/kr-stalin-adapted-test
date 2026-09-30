"""Render the shipped agriculture-window geometry and textures for offline review.

The card state comes from preview_national_agriculture.cjs. This is a layout
proof, not a game capture; engine fonts, hover effects and tooltips need HOI4 QA.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont
from hoi4_politics_blocks import load

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GAME = ROOT.parents[3] / 'common/Hearts of Iron IV'


def render(game, admin_page, card_page):
    out = ROOT / 'output/national-agriculture'
    subprocess.run(['node', str(ROOT / 'tools/preview_national_agriculture.cjs'), 'simp_chinese', '--completed-reform'], cwd=ROOT, check=True)
    sample = json.loads((out / 'layout-simp_chinese.json').read_text(encoding='utf-8'))
    cards = sample['pages'][card_page - 1]
    catalog = {}
    for stem in ['RUS_national_agriculture', 'RUS_agriculture_window']:
        catalog.update(re.findall(r'^\s*([\w.]+):0 "(.*)"$', (ROOT / f'localisation/simp_chinese/{stem}_l_simp_chinese.yml').read_text(encoding='utf-8-sig'), re.M))
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)
    title_font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 24)
    proof = Image.new('RGBA', (972, 734), '#243932')
    sprites = {}
    for base, file in [(game, 'interface/core.gfx'), (game, 'interface/countrytechtreeview.gfx'),
                       (game, 'interface/general_stuff.gfx'), (ROOT.parent / '1521695605', 'interface/core.gfx')]:
        for group in load(base / file):
            if not isinstance(group.v, list):
                continue
            for n in group.v:
                if not isinstance(n.v, list):
                    continue
                texture = n.value('texturefile') or n.value('textureFile')
                if texture:
                    relative = texture.strip('"')
                    p = base / relative
                    if not p.exists():
                        p = game / relative
                    border = n.one('borderSize')
                    sprites[n.value('name').strip('"')] = (p, int(n.value('noOfFrames', '1')), int(border.value('x')) if border else 0)

    def paste(image, x, y, clip=None):
        if clip:
            layer = Image.new('RGBA', proof.size)
            layer.alpha_composite(image, (round(x), round(y)))
            left, top, width, height = map(round, clip)
            proof.alpha_composite(layer.crop((left, top, left + width, top + height)), (left, top))
        else:
            proof.alpha_composite(image, (round(x), round(y)))

    def native(name, x, y, width=None, height=None):
        path, frames, border = sprites[name]
        im = Image.open(path).convert('RGBA')
        if frames > 1:
            im = im.crop((0, 0, im.width // frames, im.height))
        width, height = width or im.width, height or im.height
        if border:
            sw, sh = im.size
            for sx0, sx1, dx0, dx1 in [(0, border, 0, border), (border, sw-border, border, width-border), (sw-border, sw, width-border, width)]:
                for sy0, sy1, dy0, dy1 in [(0, border, 0, border), (border, sh-border, border, height-border), (sh-border, sh, height-border, height)]:
                    paste(im.crop((sx0, sy0, sx1, sy1)).resize((dx1-dx0, dy1-dy0)), x+dx0, y+dy0)
        else:
            paste(im.resize((round(width), round(height)), Image.Resampling.LANCZOS), x, y)
        return width, height

    def text(value, x, y, width, size=16, height=40, align='center', clip=None):
        value = re.sub(r'§.', '', value).replace('\\n', '\n')
        value = re.sub(r'\[\?([^|]+)\|(\d)\]', lambda m: f'{sample["variables"].get(m[1], 0):.{m[2]}f}', value)
        f = title_font if size == 24 else font
        layer = Image.new('RGBA', proof.size)
        d = ImageDraw.Draw(layer)
        for row, line in enumerate(value.split('\n')):
            tw = d.textlength(line, font=f)
            d.text((x + (width-tw)/2 if align == 'center' else x, y + row * 21), line, font=f, fill='#eee5d2')
        paste(layer, 0, 0, clip)

    ox, oy = 16, 12
    native('GFX_tiled_plain_bg', ox, oy, 940, 692)
    native('GFX_tiled_research_bg', ox+532, oy+48, 392, 625)
    for w in cards:
        x, y = ox + 16 + w['x'], oy + 48 + w['y']
        clip = [ox+16+w['clip'][0], oy+48+w['clip'][1], *w['clip'][2:]] if w['clip'] else None
        im = None
        if w.get('sprite'):
            im = Image.open(ROOT / w['sprite']).convert('RGBA')
            im = im.resize((round(im.width*w['scale']), round(im.height*w['scale'])), Image.Resampling.LANCZOS)
            paste(im, x, y, clip)
        if w['text']:
            width = im.width if im else w['width']
            height = im.height if im else w['height']
            text(w['text'], x, y + (7 if w['kind']=='buttonType' else 0), width,
                 24 if w.get('font')=='hoi_24header' else 16, height, w.get('format') or 'center', clip)
    panel = load(ROOT / 'interface/RUS_national_agriculture.gui')[0].v[0]
    for widget in panel.v:
        if widget.k not in {'instantTextBoxType', 'buttonType'}:
            continue
        name = widget.value('name').strip('"')
        if name == 'nat_admin_locked':
            continue
        if name.startswith('nat_admin_status_') and name != f'nat_admin_status_{admin_page}':
            continue
        if name.startswith('nat_action_RUS_nat_support_') and admin_page != 0:
            continue
        if name.startswith('nat_action_RUS_agri_exchange_') and admin_page != 1:
            continue
        pos = widget.one('position'); x, y = ox + int(pos.value('x')), oy + int(pos.value('y'))
        if widget.k == 'buttonType':
            sprite = (widget.value('quadTextureSprite') or widget.value('spriteType')).strip('"')
            width, height = native(sprite, x, y)
            value = catalog.get(widget.value('buttonText').strip('"'), '')
            if value:
                text(value, x, y+7, width)
        else:
            value = catalog[widget.value('text').strip('"')]
            text(value, x, y, int(widget.value('maxWidth')), 24 if '24header' in widget.value('font') else 16)
    ImageDraw.Draw(proof).text((28, 707), '离线布局预览 · 非游戏截图；实际字体、悬停和窗口行为以游戏内为准', font=font, fill='#e0ddcc')
    destination = out / f'window-admin-{admin_page}-cards-{card_page}.png'
    proof.convert('RGB').save(destination)
    print(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=DEFAULT_GAME)
    parser.add_argument('--admin-page', type=int, choices=[0, 1], default=0)
    parser.add_argument('--card-page', type=int, choices=[1, 2, 3, 4, 5], default=1)
    args = parser.parse_args()
    render(args.game_root, args.admin_page, args.card_page)
