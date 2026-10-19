"""Deterministic export of existing KR logos for the native 48px MIO trait canvas.

Default/--check reads the manifest and verifies bytes; no image rendering on check.
--write explicitly exports the five small textures and their private sprites.
"""
from pathlib import Path
import argparse,hashlib,json,os,struct

ROOT=Path(__file__).resolve().parents[1]
KR=Path(os.environ.get('HOI4_KR_ROOT',ROOT.parent/'1521695605'))
NAMES=('toz','vpoz','bmz','obukhov','imz')
MANIFEST=ROOT/'tools/design/ordnance_design_bureau/trait_icons.json'
GFX='interface/RUS_odb_trait_icons.gfx'

def digest(data):return hashlib.sha256(data).hexdigest()
def sprite_text():
    return 'spriteTypes = {\n'+''.join(f'\tspriteType = {{\n\t\tname = "GFX_RUS_odb_trait_{name}"\n\t\ttexturefile = "gfx/interface/military_industrial_organization/RUS_odb/{name}.png"\n\t\tlegacy_lazy_load = no\n\t}}\n' for name in NAMES)+'}\n'

def export():
    from PIL import Image
    rows=[]
    for name in NAMES:
        source=f'gfx/interface/companies/RUS/RUS_{name}.png'
        original=Image.open(KR/source).convert('RGBA')
        bounds=original.getbbox();assert bounds
        logo=original.crop(bounds)
        logo.thumbnail((32,32),Image.Resampling.LANCZOS)
        canvas=Image.new('RGBA',(48,48));canvas.alpha_composite(logo,((48-logo.width)//2,(48-logo.height)//2))
        target=f'gfx/interface/military_industrial_organization/RUS_odb/{name}.png'
        path=ROOT/target;path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path)
        rows.append(dict(name=name,source=source,source_sha256=digest((KR/source).read_bytes()),source_size=list(original.size),path=target,sha256=digest(path.read_bytes()),canvas=[48,48],logo_limit=[32,32],trait_icon_position=[-21,-32],frame_position=[-29,-40],frame_circle_center=[32,32]))
    (ROOT/GFX).write_text(sprite_text(),encoding='utf-8',newline='\n')
    MANIFEST.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def check():
    rows=json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert [row['name'] for row in rows]==list(NAMES)
    for row in rows:
        data=(ROOT/row['path']).read_bytes()
        assert digest(data)==row['sha256'],row['path']
        assert struct.unpack('>II',data[16:24])==(48,48) and row['canvas']==[48,48],row['path']
        # Native circle center: (-29,-40)+(32,32)=(3,-8).
        # Native icon center: (-21,-32)+(24,24)=(3,-8).
        assert [a+b//2 for a,b in zip(row['trait_icon_position'],row['canvas'])]==[a+b for a,b in zip(row['frame_position'],row['frame_circle_center'])]
        assert digest((KR/row['source']).read_bytes())==row['source_sha256'],row['source']
    assert (ROOT/GFX).read_text(encoding='utf-8')==sprite_text()

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.write:export()
    check();print('PASS: five private MIO trait textures/sprites match the export manifest'+(' (written)' if a.write else ' (read-only)'))
if __name__=='__main__':main()
