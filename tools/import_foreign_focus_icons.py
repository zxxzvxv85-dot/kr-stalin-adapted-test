"""Package approved complete icon previews into native HOI4 sprite textures."""
from pathlib import Path
import json
import re
from PIL import Image, ImageDraw, ImageOps, ImageChops, ImageFilter
from collections import deque

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'output/imagegen/foreign-described-focus-preview'
DEST = ROOT / 'gfx/interface/goals/RUS_future_foreign'

def package(source):
    im = Image.open(source).convert('RGB')
    # Remove only connected exterior charcoal, preserving enclosed dark details.
    mask = Image.new('L', im.size)
    mask.putdata([255 if 18 <= r <= 48 and 3 <= g-r <= 10 and 2 <= b-r <= 10 and abs(g-b) <= 3 else 0
                  for r,g,b in im.get_flattened_data()])
    for seed in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]:
        if mask.getpixel(seed)==255:
            ImageDraw.floodfill(mask, seed, 128, thresh=0)
    alpha = mask.point(lambda x: 0 if x==128 else 255)
    # Discard disconnected background speckles before determining content bounds.
    probe=alpha.copy(); probe.thumbnail((250,250))
    w,h=probe.size; values=list(probe.get_flattened_data()); seen=set(); keep=Image.new('L',(w,h)); pix=keep.load()
    for n,v in enumerate(values):
        if v<128 or n in seen: continue
        seen.add(n); q=deque([n]); component=[]
        while q:
            k=q.popleft(); component.append(k); x,y=k%w,k//w
            for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                j=yy*w+xx
                if 0<=xx<w and 0<=yy<h and j not in seen and values[j]>=128:
                    seen.add(j);q.append(j)
        if len(component)>=20:
            for k in component: pix[k%w,k//w]=255
    keep=keep.filter(ImageFilter.MaxFilter(3)).resize(im.size,Image.Resampling.NEAREST)
    alpha=ImageChops.multiply(alpha,keep)
    rgba=im.convert('RGBA'); rgba.putalpha(alpha)
    box=alpha.getbbox()
    if not box: raise ValueError('Empty icon')
    rgba=ImageOps.contain(rgba.crop(box),(90,90),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(100,100))
    canvas.alpha_composite(rgba,((100-rgba.width)//2,(100-rgba.height)//2))
    return canvas

def add_icons(text, ids):
    for focus in ids:
        pattern=r'(\bid\s*=\s*'+re.escape(focus)+r'\s*\n)'
        text,count=re.subn(pattern,lambda m:m[1]+'\ticon = GFX_goal_'+focus+'\n',text,count=1)
        if count!=1: raise ValueError(f'Missing focus {focus}')
    return text

def main():
    items=json.loads((WORK/'builtin-manifest.json').read_text(encoding='utf-8'))
    DEST.mkdir(parents=True,exist_ok=True)
    for x in items:
        package(x['saved_path']).save(DEST/(x['id']+'.png'))
    file=ROOT/'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt'
    text=file.read_text(encoding='utf-8-sig')
    ids=[x['id'] for x in items]
    if any('icon = GFX_goal_'+x in text for x in ids):
        raise ValueError('Icon registrations already exist; refusing duplicate insertions')
    file.write_bytes(add_icons(text,ids).encode('utf-8'))
    template=(ROOT/'interface/RUS_stalin_kamenev_focus_icons.gfx').read_text(encoding='utf-8-sig')
    start=template.index('\tSpriteType = {\n\t\tname = "GFX_goal_RUS_kamenev_bol_restore_pravda"')
    end=template.index('\tSpriteType = {\n\t\tname = "GFX_goal_RUS_kamenev_bol_restore_central_bureau"',start)
    block=template[start:end]
    gfx='spriteTypes = {\n'+''.join(block.replace('RUS_kamenev_bol_restore_pravda',x).replace('goals/RUS_kamenev_politics/','goals/RUS_future_foreign/') for x in ids)+'}\n'
    (ROOT/'interface/RUS_future_foreign_focus_icons.gfx').write_bytes(gfx.encode('utf-8'))
    print(f'Packaged {len(items)} RGBA textures and registered normal/shine sprites.')

if __name__=='__main__': main()
