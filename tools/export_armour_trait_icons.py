"""Reuse the verified native 48px canvas export; no image generation or check writes."""
import argparse,json
from pathlib import Path
import export_ordnance_trait_icons as base

ROOT=Path(__file__).resolve().parents[1]

def configure():
    base.NAMES=('okmo_kr','uztm','chtz','putilovets','amo','tstz','naz')
    base.MANIFEST=ROOT/'tools/design/armour_design_bureau/trait_icons.json'
    base.GFX='interface/RUS_adb_trait_icons.gfx'
    base.PREFIX='RUS_adb'

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args();configure()
    if a.write:
        base.export()
        from PIL import Image
        art=Image.open(ROOT/'tools/design/armour_design_bureau/armour_bureau_master.png').convert('RGBA')
        art.thumbnail((64,64),Image.Resampling.LANCZOS)
        canvas=Image.new('RGBA',(64,64));canvas.alpha_composite(art,((64-art.width)//2,(64-art.height)//2))
        canvas.save(ROOT/'gfx/interface/ideas/RUS_adb_organisation.png')
        record={"source":"tools/design/armour_design_bureau/armour_bureau_master.png","tool":"Built-in image_gen, reused approved no-compass artwork from 2026-10-19; no new generation","source_sha256":base.digest((ROOT/'tools/design/armour_design_bureau/armour_bureau_master.png').read_bytes()),"path":"gfx/interface/ideas/RUS_adb_organisation.png","size":[64,64],"sha256":base.digest((ROOT/'gfx/interface/ideas/RUS_adb_organisation.png').read_bytes())}
        (ROOT/'tools/design/armour_design_bureau/artwork.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    base.check()
    record=json.loads((ROOT/'tools/design/armour_design_bureau/artwork.json').read_text(encoding='utf-8'))
    for field,sha in [('source','source_sha256'),('path','sha256')]:assert base.digest((ROOT/record[field]).read_bytes())==record[sha]
    print('PASS: seven native-size armour trait logos and approved bureau artwork '+('written' if a.write else 'match (read-only)'))
if __name__=='__main__':main()
