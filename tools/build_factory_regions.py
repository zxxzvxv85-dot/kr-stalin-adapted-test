"""Quantise installed KR province data into six code-native factory footprints.

Only JSON is emitted. This does not paint, edit or replace a map image. The
outlines are small, connected abstractions of KR catchments, at different scales.
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
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
KR=Path(os.environ.get('HOI4_KR_ROOT',ROOT.parent/'1521695605'))
DATA=ROOT/'tools/data/industrial_planning_factory_regions.json'
# Names, state catchments, maximum grid extents, gameplay coal/iron/rock quotas.
# KR's steel resource is the reference for the sandbox's iron deposits.
SPECS=[
    ('moscow','莫斯科','Moscow',[219,205,223,224,247,248,253,254],(16,13),(16,20,10)),
    ('petrograd','彼得格勒','Petrograd',[195,208,209,210,263,264],(17,12),(10,12,8)),
    ('tsaritsyn','察里津','Tsaritsyn',[217,218,232,233,234,235,236,237,238,245,787,961,1006],(23,17),(20,28,16)),
    ('west_siberia','西西伯利亚','West Siberia',[572,573,651,582,403,580,571,583,570,578],(20,17),(28,36,16)),
    ('central_siberia','中西伯利亚','Central Siberia',[569,40,654,568,576,516,811,329,566,567,575,565],(23,17),(36,36,20)),
    ('far_east','远东','Far East',[563,564,574,644,657,561,562,560,637,409,408,577],(23,17),(16,32,20)),
]

def neighbours(p,points):
    x,y=p
    return sorted(q for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)) if q in points)

def component(start,points):
    seen={start};queue=deque([start])
    while queue:
        for q in neighbours(queue.popleft(),points):
            if q not in seen:seen.add(q);queue.append(q)
    return seen

def build():
    dependencies={};states={};province_state={}
    needed={s for spec in SPECS for s in spec[3]}
    for path in sorted((KR/'history/states').glob('*.txt')):
        source=path.read_text(encoding='utf-8-sig')
        sid=int(re.search(r'\bid\s*=\s*(\d+)',source)[1])
        if sid not in needed:continue
        deps=re.findall(r'\d+',re.search(r'\bprovinces\s*=\s*\{([^}]+)',source)[1])
        province_state.update((int(p),sid) for p in deps)
        resources=re.search(r'\bresources\s*=\s*\{([^}]+)',source)
        resources=dict(re.findall(r'(\w+)\s*=\s*([\d.]+)',resources[1])) if resources else {}
        states[sid]={k:float(resources.get(k,0)) for k in ('coal','steel','aluminium','chromium','tungsten','oil')}
        dependencies[path.relative_to(KR).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    assert set(states)==needed
    palette={}
    for row in csv.reader((KR/'map/definition.csv').read_text(encoding='utf-8-sig').splitlines(),delimiter=';'):
        if len(row)>3 and row[0].isdigit() and int(row[0]) in province_state:
            palette[tuple(map(int,row[1:4]))]=province_state[int(row[0])]
    # Sample the province raster as a table of state IDs; no new artwork.
    image=Image.open(KR/'map/provinces.bmp').convert('RGB').resize((2816,1024),Image.Resampling.NEAREST)
    hits={s:[] for s in needed}
    for index,pixel in enumerate(image.get_flattened_data()):
        if pixel in palette:hits[palette[pixel]].append((index%2816,index//2816))
    occupied={x for pixels in hits.values() for x,y in pixels};best=length=cut=0
    for x in range(2816*2):
        length=0 if x%2816 in occupied else length+1
        if length>best:best,cut=length,(x+1)%2816
    hits={sid:[((x-cut)%2816,y) for x,y in pixels] for sid,pixels in hits.items()}
    regions=[]
    for rid,(key,zh,en,group,(mw,mh),quotas) in enumerate(SPECS):
        pixels=[p for sid in group for p in hits[sid]]
        left=min(x for x,y in pixels);top=min(y for x,y in pixels)
        sw=max(x for x,y in pixels)-left+1;sh=max(y for x,y in pixels)-top+1
        scale=min(mw/sw,mh/sh)
        w=max(1,round(sw*scale));h=max(1,round(sh*scale))
        buckets=Counter((min(w-1,int((x-left)*w/sw)),min(h-1,int((y-top)*h/sh))) for x,y in pixels)
        points={p for p,n in buckets.items() if n>=.30*sw*sh/(w*h)}
        groups=[];remaining=set(points)
        while remaining:
            connected=component(min(remaining),remaining);groups.append(connected);remaining-=connected
        points=max(groups,key=len)
        # Grid abstraction uses the contiguous mainland; isolated offshore
        # fragments are not connected with invented land or maritime routes.
        omitted=sum(len(g) for g in groups)-len(points)
        minx=min(x for x,y in points);miny=min(y for x,y in points)
        points={(x-minx,y-miny) for x,y in points}
        w=max(x for x,y in points)+1;h=max(y for x,y in points)+1
        centre=(sum(x for x,y in points)/len(points),sum(y for x,y in points)/len(points))
        hub=min(points,key=lambda p:(-len(neighbours(p,points)),(p[0]-centre[0])**2+(p[1]-centre[1])**2,p))
        queue=deque([hub]);seen={hub};starter=[]
        while queue and len(starter)<12:
            p=queue.popleft();starter.append(p)
            for q in neighbours(p,points):
                if q not in seen:seen.add(q);queue.append(q)
        assert len(starter)==12
        # A connected dominating backbone: every unprotected tile touches the
        # protected network. Random rocks can therefore never trap a deposit.
        protected=set(starter)
        covered=protected|{q for p in protected for q in neighbours(p,points)}
        while covered!=points:
            candidates={q for p in protected for q in neighbours(p,points)}-protected
            p=min(candidates,key=lambda p:(-len(set(neighbours(p,points))-covered),p))
            protected.add(p);covered|={p,*neighbours(p,points)}
        assert len(points-protected)>=quotas[2]
        assert len(points-set(starter))>=sum(quotas)-2
        rows=[''.join('#' if (x,y) in points else '.' for x in range(w)) for y in range(h)]
        regions.append(dict(id=rid,key=key,zh=zh,en=en,states=group,width=w,height=h,rows=rows,
            hub=hub,starter=starter,protected=sorted(protected),coal=quotas[0],iron=quotas[1],rocks=quotas[2],
            kr_resources={k:sum(states[s][k] for s in group) for k in ('coal','steel','aluminium','chromium','tungsten','oil')},omitted_offshore_cells=omitted))
    for rel in ('map/definition.csv','map/provinces.bmp'):
        dependencies[rel]=hashlib.sha256((KR/rel).read_bytes()).hexdigest()
    return dict(schema=1,cell_size=40,cell_step=42,regions=regions,kr_dependencies=dependencies,
        note='KR catchment mainland outlines quantised at independent scales. Coal/iron counts are fixed gameplay quotas; positions and rocks are random per plan. Minimum city deposits are sandbox starting reserves, not claims about native KR resources.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    content=json.dumps(build(),ensure_ascii=False,indent=2)+'\n'
    if args.write:DATA.write_text(content,encoding='utf-8')
    else:assert DATA.read_text(encoding='utf-8')==content,'Factory footprint reference is out of date'
    data=json.loads(content)
    for r in data['regions']:print(f'{r["zh"]}: {r["width"]}x{r["height"]}, {sum(row.count("#") for row in r["rows"])} tiles; coal {r["coal"]}, iron {r["iron"]}, rocks {r["rocks"]}')

if __name__=='__main__':main()
