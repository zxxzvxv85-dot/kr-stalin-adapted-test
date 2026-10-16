"""Integration checks for the draw.io preview: no playable rewards or old-tree edits."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from itertools import product

from PIL import Image
from hoi4_politics_blocks import load

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'RUS_future_domestic_'
TREE = 'common/national_focus/RUS focus (Russia).txt'


def main():
    source = ET.parse(ROOT/'tools/design/RUS_future_domestic_layout.drawio')
    remap=dict(zip('620 623 624 627 628 630 632 633 635 637 647 650 651 655 699'.split(),
                   '160 169 176 182 166 179 177 163 181 183 190 192 194 200 305'.split()))
    vertices = [c for c in source.iter('mxCell')
           if c.get('vertex')=='1' and c.get('value','').strip()
           and not c.get('style','').startswith('text;')]
    ids = {PREFIX+remap.get(c.get('id').rsplit('-',1)[-1],c.get('id').rsplit('-',1)[-1]) for c in vertices}
    assert len(ids)==161
    new = load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt')
    assert len(new)==161 and all(n.k=='shared_focus' for n in new)
    by_id = {n.value('id'):n for n in new}
    assert set(by_id)==ids
    # User-specified spacing: nearest same-row neighbors must be two x units.
    # Check distinct branches, not only the global no-overlap envelope.
    for left,right in [('133','136'),('138','140'),('140','142')]:
        a,b=by_id[PREFIX+left],by_id[PREFIX+right]
        assert a.value('y')==b.value('y')
        assert abs(int(a.value('x'))-int(b.value('x')))==2, f'Incorrect spacing: {left}/{right}'
    same_row_gaps=[abs(int(a.value('x'))-int(b.value('x'))) for i,a in enumerate(new)
                   for b in new[i+1:] if a.value('y')==b.value('y')]
    assert min(same_row_gaps)==2, 'Minimum horizontal spacing must be two units'
    # The new drawing supersedes old industry positions, but keeps the 80/120 scale.
    minx=min(float(c.find('mxGeometry').get('x')) for c in vertices)
    miny=min(float(c.find('mxGeometry').get('y')) for c in vertices)
    for c in vertices:
        suffix=c.get('id').rsplit('-',1)[-1];n=by_id[PREFIX+remap.get(suffix,suffix)]
        g=c.find('mxGeometry')
        assert int(n.value('x'))==90+round((float(g.get('x'))-minx)/80)
        assert int(n.value('y'))==45+round((float(g.get('y'))-miny)/120)
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
    manifest=json.loads((ROOT/'tools/design/RUS_future_domestic_sources.json').read_text(encoding='utf-8'))
    provenance={s['id']:s for s in manifest['sources']}
    reused={k:s for k,s in provenance.items() if s['original_kr_focus']}
    assert len(reused)==14
    assert len(sprites)==2*(161-len(reused))
    mutual = set()
    or_merges = 0
    for key,n in by_id.items():
        assert n.one('completion_reward').v==[]
        assert n.one('select_effect') is None
        assert n.one('ai_will_do').value('factor')=='0'
        assert n.one('available').one('custom_trigger_tooltip').value('always')=='no'
        prereqs=n.children('prerequisite')
        assert len(prereqs)<=(2 if key==PREFIX+'638' else 1), 'Unannotated AND prerequisite'
        for p in prereqs:
            assert all(v.v in ids for v in p.children('focus'))
            or_merges+=len(p.children('focus'))>1
        for m in n.children('mutually_exclusive'):
            other=m.value('focus'); assert other in ids
            assert any(x.value('focus')==key for x in by_id[other].children('mutually_exclusive'))
            mutual.add(tuple(sorted((key,other))))
        icon=n.value('icon')
        assert icon==provenance[key]['sprite']
        texture=provenance[key]['destination']
        if key not in reused:
            assert icon=='GFX_goal_'+key
            assert icon in sprites and icon+'_shine' in sprites
            assert sprites[icon].value('texturefile').strip('"')==texture
            assert sprites[icon+'_shine'].value('texturefile').strip('"')==texture
        image=Image.open(ROOT/texture)
        assert image.size==(100,100) and image.mode=='RGBA'
        assert image.getchannel('A').getextrema()==(0,255)
    assert len(mutual)==4 and or_merges>20
    # Three economic approaches must all exclude one another.
    assert all(tuple(sorted((PREFIX+a,PREFIX+b))) in mutual for a,b in [('163','166'),('166','169'),('163','169')])
    # Invisible gates are mandatory available checks, never drawable prerequisite links.
    for target,solid,hidden in [('323','473','257'),('375','349','323')]:
        n=by_id[PREFIX+target]
        assert [v.v for p in n.children('prerequisite') for v in p.children('focus')]==[PREFIX+solid]
        assert [v.v for v in n.one('available').children('has_completed_focus')]==[PREFIX+hidden]
        for a,b in product([False,True],repeat=2):
            done={PREFIX+s for s,on in [(solid,a),(hidden,b)] if on}
            unlocked=all(any(v.v in done for v in p.children('focus')) for p in n.children('prerequisite')) and all(v.v in done for v in n.one('available').children('has_completed_focus'))
            assert unlocked==(a and b)
    fyp=by_id[PREFIX+'638']
    groups=[{v.v for v in p.children('focus')} for p in fyp.children('prerequisite')]
    assert groups==[{PREFIX+s for s in ['177','182','183']},{PREFIX+'237'}]
    for a,b,c,d in product([False,True],repeat=4):
        done={PREFIX+s for s,on in zip(['177','182','183','237'],[a,b,c,d]) if on}
        assert all(bool(g & done) for g in groups)==((a or b or c) and d)
    assert by_id[PREFIX+'390'].value('icon')=='GFX_focus_CHL_union_of_hispanic_republics'
    # Confirm every direct reuse against installed KR's actual focus and sprite definitions.
    originals={f.value('id'):f for p in (ROOT.parent/'1521695605/common/national_focus').glob('*.txt') for t in load(p) for f in ([t] if t.k=='shared_focus' else t.children('focus'))}
    registry={}
    for root in [ROOT.parents[3]/'common/Hearts of Iron IV',ROOT.parent/'1521695605']:
        for p in (root/'interface').rglob('*.gfx'):
            for name,texture in re.findall(r'name\s*=\s*"([^"]+)"\s+texturefile\s*=\s*"([^"]+)"',p.read_text(encoding='utf-8-sig',errors='replace')):
                if name in {s['sprite']+suffix for s in reused.values() for suffix in ['', '_shine']}:registry[name]=texture
    for k,s in reused.items():
        assert originals[s['original_kr_focus']].value('icon')==s['sprite']
        assert registry[s['sprite']]==registry[s['sprite']+'_shine']
        assert registry[s['sprite']].replace('\\','/').endswith(Path(s['source']).name)
    adaptation=by_id[PREFIX+'249']
    assert [v.v for v in adaptation.one('prerequisite').children('focus')]==[PREFIX+'151']
    assert not any(v.value('focus')==PREFIX+'151' for v in adaptation.children('mutually_exclusive'))
    for language in ['simp_chinese','english','russian']:
        raw=(ROOT/f'localisation/{language}/RUS_future_domestic_l_{language}.yml').read_bytes()
        assert raw.startswith(b'\xef\xbb\xbf')
        keys=re.findall(r'^\s+([^ :]+):0 ',raw.decode('utf-8-sig'),re.M)
        assert len(keys)==len(set(keys))==323
        assert set(keys)==ids|{i+'_desc' for i in ids}|{'RUS_future_domestic_preview_only_tt'}
        assert '第一个五年计划（' not in raw.decode('utf-8-sig')
    b=manifest['existing_conservative_bounds']; n=manifest['new_bounds']
    assert n['min_x']-b['max_x']>=6 and n['min_y']-b['max_y']>=4
    assert len(manifest['recovered_free_end_edges'])==10
    print(f'PASS: 161 focuses/14 original KR sprite reuses; {or_merges} ordinary OR merges; 2 hidden AND gates; five-year-plan 16-case gate; 4 symmetric exclusions; revised drawing geometry; three-language keys/BOM valid.')


if __name__=='__main__':
    main()
