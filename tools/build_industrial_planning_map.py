"""Package fixed atlas artwork registered to installed KR state geometry.

KR data determines regions, centres and transport topology. ImageGen supplies
only the print finish; ordinary checks never redraw or regenerate artwork.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter, deque
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
KR = Path(os.environ.get('HOI4_KR_ROOT', ROOT.parent / '1521695605'))
DATA = 'tools/data/industrial_planning_map.json'
ASSETS = 'gfx/interface/RUS_industrial_planning'
ART = 'tools/assets/industrial_planning'
MAP_W, MAP_H = 1168, 432
MARKER_W = MARKER_H = 26
# Keep the existing network's sampling independent from the display resolution.
TOPOLOGY_W, TOPOLOGY_H = 816, 432
# Economic catchments follow existing KR state boundaries. Dense western areas
# are grouped around industrial centres; the sparsely settled east uses larger
# river/transport catchments. Never partition the country into equal squares.
DISTRICTS = [
    (213,[213,722]), (215,[215,216]), (195,[195,208,209,210,263,264]),
    (214,[214,351,397,262]), (242,[242,243,246,755,880]),
    (219,[219,205,223,224,247,248,253,254]), (260,[220,222,240,257,258,260]),
    (252,[244,252]), (249,[249,250,256]), (239,[239,255,401,265]),
    (251,[251,652]), (217,[217,236,237]), (218,[218,245,238]),
    (234,[1006,234,235]), (233,[232,233,787,961]),
    (653,[398,399,400,653]), (572,[572,573,651,582]),
    (403,[403,580]), (571,[571,583]), (570,[570,578]),
    (569,[569,40,654]), (568,[568,576,516]), (811,[811,329]),
    (566,[566,567,575,565]), (563,[563,564]), (574,[574,644]),
    (657,[657,561]), (562,[562,560]), (637,[637]),
    (409,[409]), (408,[408]), (577,[577]),
    (581,[581,406,587]), (402,[402]), (404,[404,590,588,810]), (589,[589]),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    states, palette, dependencies = {}, {}, {}
    for path in sorted((KR / 'history/states').glob('*.txt')):
        text = path.read_text(encoding='utf-8-sig')
        owner = re.search(r'\bowner\s*=\s*(\w+)', text)
        if not owner or owner[1] not in ('RUS', 'TRM'):
            continue
        sid = int(re.search(r'\bid\s*=\s*(\d+)', text)[1])
        province_ids = list(map(int, re.findall(r'\d+', re.search(r'\bprovinces\s*=\s*\{([^}]+)', text)[1])))
        resources = re.search(r'\bresources\s*=\s*\{([^}]+)', text)
        resources = dict(re.findall(r'(\w+)\s*=\s*([\d.]+)', resources[1])) if resources else {}
        states[sid] = dict(provinces=province_ids, owner=owner[1], coal=float(resources.get('coal', 0)), iron=float(resources.get('steel', 0)))
        dependencies[path.relative_to(KR).as_posix()] = digest(path)
    province_state = {p: s for s, values in states.items() for p in values['provinces']}
    definition = KR / 'map/definition.csv'
    for row in csv.reader(definition.read_text(encoding='utf-8-sig').splitlines(), delimiter=';'):
        if len(row) >= 4 and row[0].isdigit() and int(row[0]) in province_state:
            palette[tuple(map(int, row[1:4]))] = province_state[int(row[0])]
    source = KR / 'map/provinces.bmp'
    image = Image.open(source).convert('RGB').resize((2816, 1024), Image.Resampling.NEAREST)
    state_map = Image.new('I', image.size)
    state_map.putdata([palette.get(pixel, 0) for pixel in image.getdata()])
    mask = Image.new('L', state_map.size)
    mask.putdata([255 if value else 0 for value in state_map.getdata()])
    occupied = [mask.crop((x,0,x+1,mask.height)).getbbox() is not None for x in range(mask.width)]
    best = length = 0
    cut = 0
    for x, present in enumerate(occupied + occupied):
        length = 0 if present else length + 1
        if length > best:
            best, cut = length, (x+1) % mask.width
    # KR puts a small part of Chukotka across the horizontal map seam.
    # Unwrap at the largest empty longitude interval before taking the crop.
    for target in (state_map, mask):
        shifted = Image.new(target.mode, target.size)
        shifted.paste(target.crop((cut,0,target.width,target.height)),(0,0))
        shifted.paste(target.crop((0,0,cut,target.height)),(target.width-cut,0))
        target.paste(shifted)
    bbox = mask.getbbox()
    # Map geometry keeps its native aspect ratio. Padding is outside the country.
    cropped = state_map.crop(bbox)
    def fit(width, height):
        scale = min((width - 20) / cropped.width, (height - 20) / cropped.height)
        fitted = cropped.resize((round(cropped.width * scale), round(cropped.height * scale)), Image.Resampling.NEAREST)
        result = Image.new('I', (width, height))
        result.paste(fitted, ((width-fitted.width)//2, (height-fitted.height)//2))
        return result
    map_states = fit(MAP_W, MAP_H)
    assigned=[sid for _,group in DISTRICTS for sid in group]
    assert len(assigned)==len(set(assigned)) and set(assigned)==set(states), 'Review district definitions after KR changes'
    group_of={sid:i for i,(_,group) in enumerate(DISTRICTS) for sid in group}
    pixels=list(map_states.getdata())
    groups=[group_of.get(s,-1) for s in pixels]
    cells=[];edges=set();masks=[]
    for i,(centre,group) in enumerate(DISTRICTS):
        hits=[(index%MAP_W,index//MAP_W) for index,sid in enumerate(pixels) if sid==centre]
        cx=sum(x for x,y in hits)/len(hits);cy=sum(y for x,y in hits)/len(hits)
        m=Image.new('L',(MAP_W,MAP_H));m.putdata([255 if g==i else 0 for g in groups]);masks.append(m)
        cells.append(dict(id=i,state=centre,states=group,x=round(cx),y=round(cy),geo_x=round(cx),geo_y=round(cy),
                          coal=int(any(states[s]['coal']>0 for s in group)),iron=int(any(states[s]['iron']>0 for s in group)),bbox=m.getbbox()))
    network_groups=[group_of.get(s,-1) for s in fit(TOPOLOGY_W,TOPOLOGY_H).getdata()]
    for index,g in enumerate(network_groups):
        if g<0:continue
        for other in ([index+1] if index%TOPOLOGY_W<TOPOLOGY_W-1 else [])+([index+TOPOLOGY_W] if index//TOPOLOGY_W<TOPOLOGY_H-1 else []):
            if network_groups[other]>=0 and network_groups[other]!=g:edges.add(tuple(sorted((g,network_groups[other]))))
    # Two explicit maritime connections, rendered differently from land routes.
    by_state={c['state']:c['id'] for c in cells}
    sea_edges={tuple(sorted((by_state[a],by_state[b]))) for a,b in [(562,637),(409,577)]}
    edges|=sea_edges
    hub=by_state[219]
    for c in cells:c['neighbors']=sorted(b if a==c['id'] else a for a,b in edges if c['id'] in (a,b))
    # Marker callouts can move slightly to remain readable; borders never move.
    for _ in range(120):
        for i,a in enumerate(cells):
            for b in cells[i+1:]:
                dx,dy=b['x']-a['x'],b['y']-a['y']
                if abs(dx)<MARKER_W+6 and abs(dy)<MARKER_H+6:
                    if abs(dx)>abs(dy):
                        shift=(MARKER_W+6-abs(dx))/2+0.1;sign=1 if dx>=0 else -1
                        a['x']-=sign*shift;b['x']+=sign*shift
                    else:
                        shift=(MARKER_H+6-abs(dy))/2+0.1;sign=1 if dy>=0 else -1
                        a['y']-=sign*shift;b['y']+=sign*shift
            a['x']=max(22,min(MAP_W-22,a['x']));a['y']=max(22,min(MAP_H-22,a['y']))
    for c in cells:c['x']=round(c['x']);c['y']=round(c['y'])
    paths = {hub:[hub]};queue = deque([hub])
    while queue:
        i = queue.popleft()
        for j in cells[i]['neighbors']:
            if j not in paths:paths[j]=paths[i]+[j];queue.append(j)
    assert len(paths)==len(cells), 'Economic network has unreachable districts: '+str(set(range(len(cells)))-set(paths))
    dependencies['map/definition.csv'] = digest(definition)
    dependencies['map/provinces.bmp'] = digest(source)
    data = dict(schema=3, width=MAP_W, height=MAP_H, marker_width=MARKER_W, marker_height=MARKER_H,
                topology_size=[TOPOLOGY_W,TOPOLOGY_H],
                hub=hub, cells=cells,
                kr_dependencies=dependencies, source_crop=bbox, longitude_cut=cut,
                sea_edges=sorted(sea_edges),edges=sorted(edges),
                note='Economic districts follow KR states. Work is delivered to the named centre; mine eligibility follows deposits in the catchment. Real rail connection to Moscow and real state conditions are read at runtime.')
    land = Image.new('L', map_states.size)
    land.putdata([255 if value else 0 for value in map_states.getdata()])
    board = Image.new('RGBA', (MAP_W, MAP_H), '#17262c')
    draw = ImageDraw.Draw(board)
    for x in range(0,MAP_W,22):draw.line((x,0,x,MAP_H),fill='#1c3036')
    for y in range(0,MAP_H,22):draw.line((0,y,MAP_W,y),fill='#1c3036')
    board.paste('#52615a',mask=land)
    # Coastline first, grid district tint second. Six bands help orient the reader.
    outline = ImageChops.subtract(land.filter(ImageFilter.MaxFilter(3)),land)
    board.paste('#cbbf9b',mask=outline)
    for c,m in zip(cells,masks):
        tint=['#626d5a','#6d6b54','#646e68','#5e706d','#5b6873','#666178'][c['id']%6]
        board.paste(tint,mask=m)
        edge=ImageChops.subtract(m,m.filter(ImageFilter.MinFilter(3)))
        board.paste('#c1b48b',mask=edge)
        draw.line((c['geo_x'],c['geo_y'],c['x'],c['y']),fill='#d6ceb7',width=1)
    # KR's province raster stops at its northern edge. The padding above that
    # cut is outside the game map, not an invented strip of Arctic sea.
    if bbox[1] == 0:
        limit_y=land.getbbox()[1]
        data['northern_map_limit_y']=limit_y
        draw.rectangle((0,0,MAP_W-1,limit_y-1),fill='#252d30')
        for x in range(-limit_y,MAP_W,16):
            draw.line((x,limit_y-1,x+limit_y-1,0),fill='#333c3e',width=1)
        draw.line((0,limit_y-1,MAP_W-1,limit_y-1),fill='#817760',width=1)
    # A changed KR layout needs a newly registered reference, never silent reuse
    # of art prepared for another projection or a real-world country outline.
    reference=Image.open(ROOT/ART/'geography_reference.png').convert('RGBA')
    assert board.size==reference.size and board.tobytes()==reference.tobytes(), \
        'KR atlas geometry changed; review and replace its registered reference/art'
    source_art=Image.open(ROOT/ART/'atlas_source.png').convert('RGBA')
    assert abs(source_art.width/source_art.height-MAP_W/MAP_H)<0.002, 'Atlas aspect ratio mismatch'
    board=source_art.resize((MAP_W,MAP_H),Image.Resampling.LANCZOS)
    data['artwork']=dict(tool='built-in image_gen',model=None,
                         source=ART+'/atlas_source.png',source_size=list(source_art.size),
                         reference=ART+'/geography_reference.png',prompt=ART+'/prompt.txt',
                         note='Printed finish only. All regions and coordinates come from installed KR; northern padding denotes the game-map limit, not sea.')
    data['art_dependencies']={ART+'/'+name:digest(ROOT/ART/name)
                              for name in ('atlas_source.png','geography_reference.png','prompt.txt')}
    images={'map.png':board}
    # UI diagrams are deterministic vector primitives, with button states in a strip.
    for name, color in [('selected','#dfba62'),('offline','#bc594e'),('connected','#9cae80')]:
        img=Image.new('RGBA',(MARKER_W,MARKER_H));d=ImageDraw.Draw(img)
        d.ellipse((0,0,MARKER_W-1,MARKER_H-1),outline=color,width=2 if name=='selected' else 1)
        images[name+'.png']=img
    hit=Image.new('RGBA',(MARKER_W*3,MARKER_H))
    d=ImageDraw.Draw(hit)
    for frame,color in enumerate([(28,37,40,170),(69,76,67,220),(113,96,64,230)]):
        d.ellipse((frame*MARKER_W,0,frame*MARKER_W+MARKER_W-1,MARKER_H-1),fill=color,outline='#aca27f',width=1)
    images['cell_button.png']=hit
    progress=Image.new('RGBA',(280*21,12))
    d=ImageDraw.Draw(progress)
    for frame in range(21):
        left=280*frame
        d.rectangle((left,0,left+279,11),fill='#171f20',outline='#847b61')
        if frame: d.rectangle((left+2,2,left+2+round(275*frame/20),9),fill='#acb778')
    images['progress.png']=progress
    for c,m in zip(cells,masks):
        edge=ImageChops.subtract(m.filter(ImageFilter.MaxFilter(5)),m.filter(ImageFilter.MinFilter(3)))
        img=Image.new('RGBA',m.size);img.paste('#f1ce79',mask=edge)
        images[f'region_{c["id"]}.png']=img.crop(c['bbox'])
    data['edge_sprites']=[]
    for a,b in sorted(edges):
        x0,y0=cells[a]['x'],cells[a]['y'];x1,y1=cells[b]['x'],cells[b]['y']
        left,top=min(x0,x1)-2,min(y0,y1)-2;w,h=abs(x1-x0)+5,abs(y1-y0)+5
        img=Image.new('RGBA',(w,h));d=ImageDraw.Draw(img)
        if (a,b) in sea_edges:
            for segment in range(0,20,2):
                t,u=segment/20,(segment+1)/20
                d.line((x0+(x1-x0)*t-left,y0+(y1-y0)*t-top,x0+(x1-x0)*u-left,y0+(y1-y0)*u-top),fill='#87c5d2',width=2)
        else:d.line((x0-left,y0-top,x1-left,y1-top),fill='#e5ce8f',width=2)
        images[f'link_{a}_{b}.png']=img
        data['edge_sprites'].append(dict(a=a,b=b,x=left,y=top,width=w,height=h,sea=(a,b) in sea_edges))
    return data,images


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    parser.add_argument('--output-root',type=Path)
    args=parser.parse_args()
    if args.check and args.output_root:parser.error('--check cannot write --output-root')
    out=args.output_root or ROOT
    if not args.write and not args.output_root:
        data=json.loads((ROOT/DATA).read_text(encoding='utf-8'))
        bad=[p for p,h in data['kr_dependencies'].items() if not (KR/p).is_file() or digest(KR/p)!=h]
        assert not bad, 'KR map dependencies changed; review before rebuilding: '+str(bad)
        for p,h in data['art_dependencies'].items():
            assert (ROOT/p).is_file() and digest(ROOT/p)==h, 'Atlas source changed: '+p
        for p,h in data['asset_hashes'].items():assert digest(ROOT/ASSETS/p)==h,p
        print(f"PASS KR map/art dependencies and {len(data['asset_hashes'])} asset hashes; {len(data['cells'])} districts")
        return
    data,images=build();folder=out/ASSETS;folder.mkdir(parents=True,exist_ok=True)
    for name,img in images.items():img.save(folder/name)
    data['asset_hashes']={name:digest(folder/name) for name in images}
    p=out/DATA;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"Built {len(data['cells'])} districts, hub {data['hub']}; {folder}")


if __name__=='__main__':main()
