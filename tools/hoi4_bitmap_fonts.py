"""Read installed Chinese BMFont fallbacks for UI metrics and layout proofs.

No font files are copied into the mod. Coordinates and advance widths come from
the same font definitions used by HOI4; final engine shading is still not emulated.
"""
from functools import lru_cache
from pathlib import Path
import os
import re
from PIL import Image, ImageColor, ImageChops
from hoi4_politics_blocks import load

ROOT=Path(__file__).resolve().parents[1]
GAME=Path(os.environ.get('HOI4_GAME_ROOT',ROOT.parents[3]/'common/Hearts of Iron IV'))
CN=ROOT.parent/'2946487287'
KR=ROOT.parent/'1521695605'


@lru_cache(None)
def font_data(name):
    definitions={n.value('name').strip('"'):n for block in load(CN/'interface/core_chinese.gfx') for n in block.v}
    definition=definitions[name]; faces=[]
    for entry in definition.one('fontfiles').v:
        relative=entry.k.strip('"')
        path=next((r/(relative+'.fnt') for r in [ROOT,CN,KR,GAME] if (r/(relative+'.fnt')).is_file()),None)
        if path is None: continue
        glyphs={}; pages={}; common={}
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            values={k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)}
            if line.startswith('common '): common=values
            elif line.startswith('page '):
                page_name=re.search(r'file="([^"]+)"',line)
                if page_name: pages[values['id']]=path.parent/page_name[1]
            elif line.startswith('char '): glyphs[values['id']]=values
        if not pages: pages={0:path.with_suffix('.dds')}
        # Some installed single-page fonts retain an obsolete _0 page name in
        # their BMFont metadata; HOI4 loads the font-prefix .dds instead.
        if len(pages)==1 and not next(iter(pages.values())).exists() and path.with_suffix('.dds').exists():
            pages={next(iter(pages)):path.with_suffix('.dds')}
        assert glyphs and common
        faces.append({'glyphs':glyphs,'pages':pages,'base':common['base'],'height':common['lineHeight']})
    assert faces,('Font has no installed faces',name)
    return faces


def plain(text):
    return re.sub(r'§.', '',text)


def glyph(name,char):
    code=ord(char)
    for face in font_data(name):
        if code in face['glyphs']: return face,face['glyphs'][code]
    raise ValueError(f'{name}: missing glyph U+{code:04X} {char!r}')


def measure(name,text):
    return max((sum(glyph(name,c)[1]['xadvance'] for c in line) for line in plain(text).split('\n')),default=0)


@lru_cache(None)
def page_image(path):
    return Image.open(path).convert('RGBA')


def render(im,x,y,text,name,colour='#e3dfcf',align='left',width=None):
    """Draw the installed font atlas into a layout proof at one game pixel per pixel."""
    base=font_data(name)[0]['base']; line_height=max(f['height'] for f in font_data(name))
    for line_index,line in enumerate(plain(text).split('\n')):
        line_x=x
        if align=='center': line_x+=((width or 0)-measure(name,line))/2
        elif align=='right': line_x+=(width or 0)-measure(name,line)
        for char in line:
            face,g=glyph(name,char)
            if g['width'] and g['height']:
                page=page_image(str(face['pages'][g.get('page',0)]))
                tile=page.crop((g['x'],g['y'],g['x']+g['width'],g['y']+g['height']))
                # Atlas RGB contains the light glyph, while alpha also covers
                # its dark outline/shadow. Tinting alpha alone makes text blob.
                alpha=ImageChops.multiply(tile.getchannel('A'),tile.convert('L'))
                ink=Image.new('RGBA',tile.size,ImageColor.getrgb(colour)+(255,));ink.putalpha(alpha)
                im.alpha_composite(ink,(round(line_x+g.get('xoffset',0)),round(y+line_index*line_height+base-face['base']+g.get('yoffset',0))))
            line_x+=g['xadvance']
