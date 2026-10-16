"""Integration checks for the draw.io preview: no playable rewards or old-tree edits."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from PIL import Image
from hoi4_politics_blocks import load

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'RUS_future_domestic_'
TREE = 'common/national_focus/RUS focus (Russia).txt'


def main():
    source = ET.parse(ROOT/'tools/design/RUS_future_domestic_layout.drawio')
    ids = {PREFIX+c.get('id').rsplit('-',1)[-1] for c in source.iter('mxCell')
           if c.get('vertex')=='1' and c.get('value','').strip()
           and not c.get('style','').startswith('text;')}
    assert len(ids)==141
    new = load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt')
    assert len(new)==141 and all(n.k=='shared_focus' for n in new)
    by_id = {n.value('id'):n for n in new}
    assert set(by_id)==ids
    # User-specified spacing: nearest same-row neighbors must be two x units.
    # Check distinct branches, not only the global no-overlap envelope.
    for left,right in [('133','136'),('138','140'),('140','142'),
                       ('169','166'),('166','163'),('357','351')]:
        a,b=by_id[PREFIX+left],by_id[PREFIX+right]
        assert a.value('y')==b.value('y')
        assert abs(int(a.value('x'))-int(b.value('x')))==2, f'Incorrect spacing: {left}/{right}'
    same_row_gaps=[abs(int(a.value('x'))-int(b.value('x'))) for i,a in enumerate(new)
                   for b in new[i+1:] if a.value('y')==b.value('y')]
    assert min(same_row_gaps)==2, 'Minimum horizontal spacing must be two units'
    # Explicit user anchor: technician training is (0,0), with positive y UP.
    # HOI4 uses positive y DOWN, so only that sign changes on conversion.
    anchor=by_id[PREFIX+'181']
    for suffix,expected in [('163',(0,1)),('190',(2,1)),('192',(3,0))]:
        node=by_id[PREFIX+suffix]
        actual=(int(node.value('x'))-int(anchor.value('x')),
                int(anchor.value('y'))-int(node.value('y')))
        assert actual==expected, f'User reference coordinates differ: {suffix}: {actual} != {expected}'
    tree = next(n for n in load(ROOT/TREE) if n.k=='focus_tree')
    refs = [n.v for n in tree.children('shared_focus') if n.v.startswith(PREFIX)]
    assert Counter(refs)==Counter(ids), 'New shared-focus integration missing or duplicated'
    # This branch augments Russia's existing tree rather than replacing its selector.
    assert len(tree.children('focus'))>500
    assert tree.one('continuous_focus_position') is not None
    all_focus_ids = []
    for path in (ROOT/'common/national_focus').glob('*.txt'):
        for n in load(path):
            if n.k=='shared_focus': all_focus_ids.append(n.value('id'))
            if n.k=='focus_tree': all_focus_ids.extend(f.value('id') for f in n.children('focus'))
    assert all(Counter(all_focus_ids)[key]==1 for key in ids), 'Focus ID collision'
    sprite_nodes = load(ROOT/'interface/RUS_future_domestic_icons.gfx')[0].children('SpriteType')
    sprites = {s.value('name').strip('"'):s for s in sprite_nodes}
    assert len(sprites)==282
    pixels = set()
    mutual = set()
    or_merges = 0
    for key,n in by_id.items():
        assert n.one('completion_reward').v==[]
        assert n.one('select_effect') is None
        assert n.one('ai_will_do').value('factor')=='0'
        assert n.one('available').one('custom_trigger_tooltip').value('always')=='no'
        prereqs=n.children('prerequisite')
        assert len(prereqs)<=1, 'AND prerequisite introduced'
        for p in prereqs:
            assert all(v.v in ids for v in p.children('focus'))
            or_merges+=len(p.children('focus'))>1
        for m in n.children('mutually_exclusive'):
            other=m.value('focus'); assert other in ids
            assert any(x.value('focus')==key for x in by_id[other].children('mutually_exclusive'))
            mutual.add(tuple(sorted((key,other))))
        icon=n.value('icon')
        assert icon=='GFX_goal_'+key
        assert icon in sprites and icon+'_shine' in sprites
        texture=sprites[icon].value('texturefile').strip('"')
        assert sprites[icon+'_shine'].value('texturefile').strip('"')==texture
        image=Image.open(ROOT/texture)
        assert image.size==(100,100) and image.mode=='RGBA'
        assert image.getchannel('A').getextrema()==(0,255)
        digest=hashlib.sha256(image.tobytes()).hexdigest()
        assert digest not in pixels, 'Duplicate visible icon artwork'
        pixels.add(digest)
    assert len(mutual)==3 and or_merges>20
    adaptation=by_id[PREFIX+'249']
    assert [v.v for v in adaptation.one('prerequisite').children('focus')]==[PREFIX+'151']
    assert not any(v.value('focus')==PREFIX+'151' for v in adaptation.children('mutually_exclusive'))
    for language in ['simp_chinese','english','russian']:
        raw=(ROOT/f'localisation/{language}/RUS_future_domestic_l_{language}.yml').read_bytes()
        assert raw.startswith(b'\xef\xbb\xbf')
        keys=re.findall(r'^\s+([^ :]+):0 ',raw.decode('utf-8-sig'),re.M)
        assert len(keys)==len(set(keys))==283
        assert set(keys)==ids|{i+'_desc' for i in ids}|{'RUS_future_domestic_preview_only_tt'}
    manifest=json.loads((ROOT/'tools/design/RUS_future_domestic_sources.json').read_text(encoding='utf-8'))
    b=manifest['existing_conservative_bounds']; n=manifest['new_bounds']
    assert n['min_x']-b['max_x']>=6 and n['min_y']-b['max_y']>=4
    assert len(manifest['recovered_free_end_edges'])==2
    print(f'PASS: 141 focuses/282 sprites/141 distinct RGBA icons; {or_merges} OR merges; 3 symmetric exclusions; revolutionary entry linked; existing tree retained; three-language keys/BOM valid.')


if __name__=='__main__':
    main()
