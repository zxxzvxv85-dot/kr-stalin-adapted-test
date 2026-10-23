"""Execute generated display effects and check seat geometry, entry wiring and assets.

Uses the existing fail-closed script fixture with only native while-loop/array extensions.
This is not a substitute for the engine's GUI renderer.
"""
from collections import Counter
from io import BytesIO
import json
import math
import re

from PIL import Image
from doudizhu_script_model import ScriptModel
from hoi4_politics_blocks import load
from generate_soviet_congress import ROOT, PARTIES, CHILDREN, ALL_PARTIES, FRAMES, LEADERS, TOTAL, WIDTH, HEIGHT, outputs, seats, leader_portraits


class CongressModel(ScriptModel):
    def __init__(self, effects):
        super().__init__(effects); self.arrays={}

    def run(self, nodes):
        for node in nodes:
            if node.k=='clear_array':
                self.arrays[node.v]=[]
            elif node.k=='add_to_array':
                self.arrays.setdefault(node.v[0].k,[]).append(self.number(node.v[0].v))
            elif node.k=='while_loop_effect':
                iterations=0
                while self.check(node.one('limit')):
                    self.run([n for n in node.v if n.k!='limit'])
                    iterations+=1; assert iterations<=800
            elif node.k=='if':
                # This feature has no else branches; base-model recursion calls us.
                if self.check(node.one('limit')):
                    self.run([n for n in node.v if n.k!='limit'])
            else:
                super().run([node])


def check_partition(model, distribution, expanded=False):
    for (key,*_),n in zip(PARTIES,distribution): model.vars['RUS_congress_'+key+'_seats']=n
    for parent,children in CHILDREN.items():
        count=model.vars['RUS_congress_'+parent+'_seats']
        quotient,remainder=divmod(count,len(children))
        for i,(key,*_) in enumerate(children): model.vars['RUS_congress_'+key+'_seats']=quotient+int(i<remainder)
    if expanded: model.flags.add('RUS_congress_show_children')
    else: model.flags.discard('RUS_congress_show_children')
    model.call('RUS_congress_refresh_display')
    array=model.arrays['RUS_congress_seats']
    assert len(array)==800
    rows=[row for row in PARTIES for row in (CHILDREN.get(row[0],[row]) if expanded else [row])]
    expected=[FRAMES[row[0]] for row in rows for _ in range(int(model.vars['RUS_congress_'+row[0]+'_seats']))]
    assert array==expected, 'Party seats must form continuous sectors, preserving parent totals'
    assert math.isclose(sum(model.vars['RUS_congress_'+key+'_percent'] for key,*_ in PARTIES),100)


def main():
    generated=outputs()
    assert all((ROOT/p).read_bytes()==data for p,data in generated.items())
    effects={n.k:n for n in load(ROOT/'common/scripted_effects/RUS_soviet_congress.txt')}
    model=CongressModel(effects); model.call('RUS_congress_prepare_demo')
    assert 'RUS_congress_demo_initialized' in model.flags
    default=[p[3] for p in PARTIES]; assert default==[240,160,120,200,80]
    check_partition(model,default)
    for distribution in [[800,0,0,0,0],[0,0,0,0,800],[160]*5,[1,399,0,1,399],[0,0,800,0,0]]:
        for expanded in [False,True]: check_partition(model,distribution,expanded)
        before=(dict(model.vars),list(model.arrays['RUS_congress_seats']))
        model.call('RUS_congress_prepare_demo')
        assert before==(model.vars,model.arrays['RUS_congress_seats']), 'Reopening must not reset saved seats'
    before=(dict(model.vars),list(model.arrays['RUS_congress_seats']))
    model.vars['RUS_congress_bolsheviks_seats']=-1
    model.vars['RUS_congress_labour_seats']=801
    model.call('RUS_congress_refresh_display')
    assert before[1]==model.arrays['RUS_congress_seats']
    assert before[0]['RUS_congress_revision']==model.vars['RUS_congress_revision']
    model.vars['RUS_congress_bolsheviks_seats']=0
    model.call('RUS_congress_refresh_display')
    assert before[1]==model.arrays['RUS_congress_seats'], 'Invalid total must not publish partial display'
    # No country modifiers, campaign currencies, event hooks or daily pulses.
    allowed={'RUS_congress_refresh_display','RUS_congress_prepare_demo'}
    assert set(effects)==allowed
    points=seats(); assert len(points)==len(set(points))==TOTAL
    for x,y in points:
        assert 20<=x<WIDTH-20 and 212<=y<416
    assert min(math.dist(a,b) for i,a in enumerate(points) for b in points[i+1:])>=6
    gui=load(ROOT/'interface/RUS_soviet_congress.gui')[0].v[0]
    icons=gui.children('iconType'); by_name={n.value('name').strip('"'):n for n in icons}
    sg=load(ROOT/'common/scripted_guis/RUS_soviet_congress.txt')[0].v[0]
    assert sg.value('context_type')=='decision_category' and sg.value('dirty')=='RUS_congress_revision'
    assert sg.value('window_name').strip('"')==gui.value('name').strip('"')
    props=sg.one('properties').v; assert len(props)==800
    for i,node in enumerate(props):
        assert node.k=='RUS_congress_seat_'+str(i)
        assert node.k in by_name and node.value('frame')==f'RUS_congress_seats^{i}'
        pos=by_name[node.k].one('position'); assert (int(pos.value('x')),int(pos.value('y')))==points[i]
    category=load(ROOT/'common/decisions/categories/RUS_soviet_congress.txt')[0]
    assert category.value('scripted_gui')==sg.k
    assert category.value('visible_when_empty')=='yes'
    assert category.one('allowed').value('original_tag')=='RUS' and category.one('visible').value('is_ai')=='no'
    decision=load(ROOT/'common/decisions/RUS_soviet_congress.txt')[0].v[0]
    assert decision.value('cost')=='0'
    assert decision.one('complete_effect').one('hidden_effect').value('RUS_congress_prepare_demo')=='yes'
    # Execute the actual two buttons, preserving all parent/child seat variables.
    check_partition(model,default,False)
    saved={k:v for k,v in model.vars.items() if k.endswith('_seats')}
    for _ in range(3):
        model.run(sg.one('effects').one('RUS_congress_expand_click').v)
        assert 'RUS_congress_show_children' in model.flags and len(model.arrays['RUS_congress_seats'])==800
        assert any(frame>5 for frame in model.arrays['RUS_congress_seats'])
        model.run(sg.one('effects').one('RUS_congress_collapse_click').v)
        assert 'RUS_congress_show_children' not in model.flags
        assert all(frame<=5 for frame in model.arrays['RUS_congress_seats'])
    assert saved=={k:v for k,v in model.vars.items() if k.endswith('_seats')}
    triggers=sg.one('triggers')
    assert model.check(triggers.one('RUS_congress_legend_main_visible'))
    assert not model.check(triggers.one('RUS_congress_legend_children_visible'))
    # Both modes retain five parent totals. Children are a separate contained breakdown.
    legends={n.value('name').strip('"'):n for n in gui.children('containerWindowType')}
    assert len(legends['RUS_congress_legend_main'].children('instantTextBoxType'))==10
    assert len(legends['RUS_congress_legend_children'].children('instantTextBoxType'))==24
    for legend in legends.values():
        for node in legend.children('instantTextBoxType'):
            if '_value_' in node.value('name'):
                assert node.value('alwaystransparent')=='no'
                assert node.value('pdx_tooltip').strip('"').startswith('RUS_congress_leaders_')
    portraits=leader_portraits()
    assert LEADERS['unions']==['RUS_mikhail_tomsky']
    assert LEADERS['bolsheviks']==['RUS_yakov_sverdlov']
    assert LEADERS['new_theory']==['RUS_daniil_sulimov','RUS_vladimir_levitsky']
    assert set(portraits)=={c for cs in LEADERS.values() for c in cs}
    registry=json.loads((ROOT/'tools/design/RUS_future_domestic_ids.json').read_text(encoding='utf-8'))
    names={n['suffix']:n['name'] for n in registry.values()}
    assert all(names[suffix]==name for _,name,suffix,_,_ in PARTIES)
    for path,data in generated.items():
        if path.suffix=='.png':
            im=Image.open(BytesIO(data)); assert im.mode=='RGBA'
            assert im.size==((60,6) if path.stem=='seats' else (WIDTH,HEIGHT))
        if path.suffix=='.yml':
            assert data.startswith(b'\xef\xbb\xbf')
            keys=re.findall(r'^\s+([^ :]+):0 ',data.decode('utf-8-sig'),re.M)
            assert len(keys)==len(set(keys))
            values={k:json.loads(v) for k,v in re.findall(r'^\s+([^ :]+):0 (".*")$',data.decode('utf-8-sig'),re.M)}
            for key,chars in LEADERS.items():
                tip=values['RUS_congress_leaders_'+key+'_tt']
                for char in chars:
                    assert '$'+char+'$' in tip
                    assert '£'+portraits[char].removeprefix('GFX_') in tip
    print('PASS: 800 seats; five parent parties and five contained subfactions; both display modes; all distributions/percentages; repeated entry/toggle preserves state; invalid totals rejected; leader/portrait tooltip bindings; geometry/decision/GUI/BOM/assets/generator parity.')


if __name__=='__main__':
    main()
