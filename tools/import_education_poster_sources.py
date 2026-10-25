"""Verify/import requested posters from the supplied archive; default is read-only."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from PIL import Image, ImageDraw, ImageOps
from education_reform_content import ACTIVITIES

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'tools/design/education_system_20261024'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true')
    parser.add_argument('--archive',type=Path,default=Path('C:/Users/Administrator/Downloads/03_USSR.zip'))
    args=parser.parse_args()
    catalogue=json.loads((DATA/'poster_catalog.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest()==catalogue['sha256']
    by_code={p['code']:p for p in catalogue['posters']}
    manifest=json.loads((DATA/'poster_sources.json').read_text(encoding='utf-8'))
    existing={s['id']:s for s in manifest['sources']}
    pictures=[]
    with zipfile.ZipFile(args.archive) as z:
        for a in ACTIVITIES:
            assert re.fullmatch('[a-z_]+',a['id'])
            item=by_code[a['poster']];payload=z.read(item['file'])
            assert hashlib.sha256(payload).hexdigest()==item['sha256']
            dest=DATA/'posters'/(a['id']+'.jpg')
            image=Image.open(io.BytesIO(payload));image.load()
            previous=existing.get(a['id'])
            if previous is None or previous['poster']!=a['poster']:
                existing[a['id']]={'id':a['id'],'poster':a['poster'],'original':item['file'],
                    'archive':catalogue['archive'],'path':dest.relative_to(ROOT).as_posix(),
                    'sha256':item['sha256'],'size':list(image.size),
                    'slogan':'Chinese adaptation for the mod; not a literal translation'}
            if args.write:
                if not dest.exists():dest.write_bytes(payload)
                elif dest.read_bytes()!=payload:
                    assert previous and hashlib.sha256(dest.read_bytes()).hexdigest()==previous['sha256'],'Source edited outside the importer'
                    dest.write_bytes(payload)
                assert dest.read_bytes()==payload
            else:assert dest.is_file() and dest.read_bytes()==payload,dest
            if a.get('gate') or a['id'] in {r['id'] for r in ACTIVITIES[14:]}:
                pictures.append((a,image.convert('RGB')))
    for item in catalogue['posters']:
        ids=[a['id'] for a in ACTIVITIES if a['poster']==item['code']]
        item['activity']=ids[0] if ids else None
        item['activities']=ids
    manifest['additional_archives']=[{'archive':catalogue['archive'],'sha256':catalogue['sha256']}]
    manifest['sources']=[existing[a['id']] for a in ACTIVITIES]
    if args.write:
        for filename,data in [('poster_sources.json',manifest),('poster_catalog.json',catalogue)]:
            (DATA/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        out=ROOT/'output/education_system/new_posters';out.mkdir(parents=True,exist_ok=True)
        for start in range(0,len(pictures),12):
            sheet=Image.new('RGB',(800,810),'#202620');draw=ImageDraw.Draw(sheet)
            for n,(a,im) in enumerate(pictures[start:start+12]):
                x=(n%4)*200;y=(n//4)*270;fit=ImageOps.contain(im,(190,240))
                sheet.paste(fit,(x+(200-fit.width)//2,y+(240-fit.height)//2))
                draw.text((x+5,y+242),a['poster']+' '+a['id'],fill='white')
            sheet.save(out/f'sources_{start//12+1}.jpg')
    print(f'PASS: {len(ACTIVITIES)} campaigns, {len({a["poster"] for a in ACTIVITIES})} distinct source posters; source SHA verified.')

if __name__=='__main__':main()
