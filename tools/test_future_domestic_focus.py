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
    registry=json.loads((ROOT/'tools/design/RUS_future_domestic_ids.json').read_text(encoding='utf-8'))
    vertices = [c for c in source.iter('mxCell')
           if c.get('vertex')=='1' and c.get('value','').strip()
           and not c.get('style','').startswith('text;')]
    ids = {PREFIX+registry[c.get('id')]['suffix'] for c in vertices}
    assert len(ids)==170
    domestic_ids={PREFIX+s['suffix'] for s in registry.values() if s['phase']=='domestic'}
    plan_ids=ids-domestic_ids
    domestic=load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt')
    phase_file=load(ROOT/'common/national_focus/00_RUS_future_five_year_plan_skeleton.txt')
    plan=[n for n in phase_file if n.k=='shared_focus']
    assert len(domestic)==153 and all(n.k=='shared_focus' for n in domestic)
    assert all(n.one('allow_branch').one('NOT').value('has_government')=='national_populist' for n in domestic)
    assert len(plan)==17 and {n.value('id') for n in plan}==plan_ids
    new=domestic+plan
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
    for c in vertices:
        entry=registry[c.get('id')];n=by_id[PREFIX+entry['suffix']]
        group=[v for v in vertices if registry[v.get('id')]['phase']==entry['phase']]
        minx=min(float(v.find('mxGeometry').get('x')) for v in group)
        miny=min(float(v.find('mxGeometry').get('y')) for v in group)
        ox,oy=(90,45) if entry['phase']=='domestic' else (6,1)
        g=c.find('mxGeometry')
        assert int(n.value('x'))==ox+round((float(g.get('x'))-minx)/80)
        assert int(n.value('y'))==oy+round((float(g.get('y'))-miny)/120)
    tree = next(n for n in load(ROOT/TREE) if n.k=='focus_tree')
    refs = [n.v for n in tree.children('shared_focus') if n.v.startswith(PREFIX)]
    assert Counter(refs)==Counter(domestic_ids), 'Domestic integration missing, duplicated or still contains first-five-year-plan nodes'
    phase_tree=next(n for n in phase_file if n.k=='focus_tree')
    assert phase_tree.value('id')=='RUS_future_five_year_plan_tree'
    assert phase_tree.value('default')=='no' and phase_tree.one('country').value('factor')=='0'
    assert Counter(n.v for n in phase_tree.children('shared_focus'))==Counter(plan_ids)
    assert int(phase_tree.one('continuous_focus_position').value('y'))>max(int(n.value('y')) for n in plan)*130+128
    for folder in ['events','common/on_actions','common/decisions','common/scripted_effects']:
        assert all('RUS_future_five_year_plan_tree' not in p.read_text(encoding='utf-8-sig') for p in (ROOT/folder).rglob('*.txt')), 'Automatic switch was not requested'
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
    assert len(reused)==13  # 192 now uses the user's approved local KX icon.
    assert len(sprites)==2*(170-len(reused))
    mutual = set()
    or_merges = 0
    for key,n in by_id.items():
        assert n.one('completion_reward').v==[]
        assert n.one('select_effect') is None
        assert n.one('ai_will_do').value('factor')=='0'
        assert n.one('available').one('custom_trigger_tooltip').value('always')=='no'
        prereqs=n.children('prerequisite')
        assert len(prereqs)<=1, 'Unannotated AND prerequisite'
        for p in prereqs:
            assert all(v.v in ids for v in p.children('focus'))
            assert all((v.v in plan_ids)==(key in plan_ids) for v in p.children('focus')), 'Cross-stage prerequisite would be unreachable'
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
    assert len(mutual)==7 and or_merges>20
    # Three economic approaches must all exclude one another.
    assert all(tuple(sorted((PREFIX+a,PREFIX+b))) in mutual for a,b in [('163','166'),('166','169'),('163','169')])
    # Invisible gates are mandatory available checks, never drawable prerequisite links.
    for target,solid,hidden in [('375','349','323'),('424','151','428')]:
        n=by_id[PREFIX+target]
        assert [v.v for p in n.children('prerequisite') for v in p.children('focus')]==[PREFIX+solid]
        assert [v.v for v in n.one('available').children('has_completed_focus')]==[PREFIX+hidden]
        for a,b in product([False,True],repeat=2):
            done={PREFIX+s for s,on in [(solid,a),(hidden,b)] if on}
            unlocked=all(any(v.v in done for v in p.children('focus')) for p in n.children('prerequisite')) and all(v.v in done for v in n.one('available').children('has_completed_focus'))
            assert unlocked==(a and b)
    fyp=by_id[PREFIX+'638']
    assert not fyp.children('prerequisite') and not fyp.one('available').children('has_completed_focus')
    assert [v.v for p in by_id[PREFIX+'323'].children('prerequisite') for v in p.children('focus')]==[PREFIX+'473']
    assert not by_id[PREFIX+'323'].one('available').children('has_completed_focus')
    assert {v.v for p in by_id[PREFIX+'331'].children('prerequisite') for v in p.children('focus')}=={PREFIX+'257'}
    # The new social-democratic extension is represented by actual drawable prerequisites.
    for suffix,parents in {'800':{'302'},'801':{'293'},'802':{'800','801'},'803':{'802','469'}}.items():
        assert {v.v for p in by_id[PREFIX+suffix].children('prerequisite') for v in p.children('focus')}=={PREFIX+s for s in parents}
    assert by_id[PREFIX+'390'].value('icon')=='GFX_focus_CHL_union_of_hispanic_republics'
    # The new education chain replaces the former blank shortcut to "向左".
    expected={'218':{'210'},'221':{'210'},'224':{'218','221'},'226':{'218','221'},
              '229':{'224','226'},'231':{'224','226'},'233':{'229','231'}}
    for suffix,parents in expected.items():
        groups=by_id[PREFIX+suffix].children('prerequisite')
        assert len(groups)==1 and {v.v for v in groups[0].children('focus')}=={PREFIX+p for p in parents}
    assert all(tuple(sorted((PREFIX+a,PREFIX+b))) in mutual for a,b in [('218','221'),('224','226'),('229','231')])
    def can_take(suffix,done):
        n=by_id[PREFIX+suffix]
        return all(any(v.v in done for v in p.children('focus')) for p in n.children('prerequisite')) and not any(m.value('focus') in done for m in n.children('mutually_exclusive'))
    assert not can_take('233',{PREFIX+'210'}), 'Education choices must not be bypassed'
    for philosophy,publicity,endpoint in product(['218','221'],['224','226'],['229','231']):
        done={PREFIX+'210'}
        assert can_take(philosophy,done);done.add(PREFIX+philosophy)
        assert not can_take('221' if philosophy=='218' else '218',done)
        assert can_take(publicity,done);done.add(PREFIX+publicity)
        assert not can_take('226' if publicity=='224' else '224',done)
        assert can_take(endpoint,done);done.add(PREFIX+endpoint)
        assert not can_take('231' if endpoint=='229' else '229',done)
        assert can_take('233',done)
    # New art must not duplicate any of the other preview icons.
    for suffix in ['218','221','224','226','229','231','800','801','802','803']:
        candidate=Image.open(ROOT/provenance[PREFIX+suffix]['destination']).convert('RGBA').tobytes()
        assert sum(Image.open(ROOT/s['destination']).convert('RGBA').tobytes()==candidate for s in provenance.values())==1
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
    assert not adaptation.children('prerequisite'), 'The latest drawing makes adaptation an independent root'
    assert not any(v.value('focus')==PREFIX+'151' for v in adaptation.children('mutually_exclusive'))
    for language in ['simp_chinese','english','russian']:
        raw=(ROOT/f'localisation/{language}/RUS_future_domestic_l_{language}.yml').read_bytes()
        assert raw.startswith(b'\xef\xbb\xbf')
        keys=re.findall(r'^\s+([^ :]+):0 ',raw.decode('utf-8-sig'),re.M)
        assert len(keys)==len(set(keys))==341
        assert set(keys)==ids|{i+'_desc' for i in ids}|{'RUS_future_domestic_preview_only_tt'}
        assert '第一个五年计划（' not in raw.decode('utf-8-sig')
        assert '奠基经济发展（' not in raw.decode('utf-8-sig')
    b=manifest['existing_conservative_bounds']; n=manifest['new_bounds']
    assert n['min_x']-b['max_x']>=6 and n['min_y']-b['max_y']>=4
    assert len(manifest['recovered_free_end_edges'])==8
    assert manifest['phase_counts']=={'domestic':153,'five_year_plan':17}
    assert PREFIX+'214' not in ids
    assert not any(v.v==PREFIX+'189' for p in by_id[PREFIX+'189'].children('prerequisite') for v in p.children('focus'))
    assert not manifest['planned_stage_entry']['implemented']
    assert set(manifest['planned_stage_entry']['any_completed'])=={PREFIX+s for s in ['177','182','183']}
    assert manifest['planned_stage_entry']['all_completed']==[PREFIX+'237']
    print(f'PASS: 153 domestic + 17 hidden independent five-year-plan focuses; no automatic switching or cross-stage prerequisites; {or_merges} OR merges; education 8-route choices; unique icons; 2 hidden AND gates; 7 exclusions; revised geometry and three-language keys/BOM valid.')


if __name__=='__main__':
    main()
