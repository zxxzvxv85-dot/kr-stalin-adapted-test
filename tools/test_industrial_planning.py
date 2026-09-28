"""Execute the shipped planning effects in a bounded native-command fixture.

This checks script semantics and geometry, not rendering or HOI4 runtime speed.
The shared parser is side-effect free; importing this module does not run tests.
"""
from __future__ import annotations

import copy
import json
import random
import re
from collections import deque
from pathlib import Path

from hoi4_politics_blocks import parse

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'tools/data/industrial_planning_map.json').read_text(encoding='utf-8'))
FX={n.k:n.v for n in parse((ROOT/'common/scripted_effects/RUS_industrial_planning_effects.txt').read_text(encoding='utf-8'))}
TR={n.k:n.v for n in parse((ROOT/'common/scripted_triggers/RUS_industrial_planning_triggers.txt').read_text(encoding='utf-8'))}


def fixture():
    return dict(tag='RUS',ai=False,vars={'RUS_first_five_year_plan_score':37,'political_power':200},flags=set(),
                owned={c['state'] for c in DATA['cells']},controlled={c['state'] for c in DATA['cells']},commands=0)


def value(s,v):
    try:return float(v)
    except ValueError:return s['vars'].get(v,0)


def compare(a,op,b):return {'=':a==b,'>':a>b,'<':a<b}[op]


def check(nodes,s):
    def one(n):
        k,v=n.k,n.v
        if k in TR:return check(TR[k],s)==(v=='yes')
        if k in ('AND','hidden_trigger'):return check(v,s)
        if k=='OR':return any(one(c) for c in v)
        if k=='NOT':return not check(v,s)
        if k=='always':return v=='yes'
        if k=='original_tag':return s['tag']==v
        if k=='is_ai':return s['ai']==(v=='yes')
        if k=='has_country_flag':return v in s['flags']
        if k=='owns_state':return int(v) in s['owned']
        if k=='controls_state':return int(v) in s['controlled']
        if k=='check_variable':return all(compare(value(s,c.k),c.op,value(s,c.v)) for c in v)
        raise AssertionError(('Unsupported trigger',k))
    return all(one(n) for n in nodes)


def run(nodes,s):
    matched=False
    for n in nodes:
        k,v=n.k,n.v;s['commands']+=1
        if k in ('if','else_if','else'):
            if k=='if':matched=False
            if not matched and (k=='else' or check(n.one('limit').v,s)):
                run([c for c in v if c.k!='limit'],s);matched=True
            continue
        matched=False
        if k in FX:run(FX[k],s)
        elif k=='while_loop_effect':
            turns=0
            while check(n.one('limit').v,s):
                turns+=1;assert turns<=1000, 'Unbounded script loop'
                run([c for c in v if c.k!='limit'],s)
        elif k=='hidden_effect':run(v,s)
        elif k=='set_country_flag':s['flags'].add(v)
        elif k=='clr_country_flag':s['flags'].discard(v)
        elif k in ('set_variable','add_to_variable','subtract_from_variable'):
            a=v[0];number=value(s,a.v)
            s['vars'][a.k]=number if k=='set_variable' else value(s,a.k)+number*(1 if k=='add_to_variable' else -1)
        else:raise AssertionError(('Unexpected external effect',k))


def call(s,name):run(FX['RUS_ip_'+name],s)
def v(s,name):return value(s,'RUS_ip_'+name)
def put(s,name,number):s['vars']['RUS_ip_'+name]=number
def select(s,i):put(s,'selected',i);call(s,'refresh')
def resources(s):return tuple(v(s,k) for k in ['budget','coal','iron','steel','machines','round','score'])


def reachable(s):
    hub=DATA['hub'];cells=DATA['cells']
    allowed={c['id'] for c in cells if c['state'] in s['owned']&s['controlled'] and v(s,f'n{c["id"]}_rail')>0}
    if hub not in allowed:return set()
    found={hub};queue=deque([hub])
    while queue:
        for j in cells[queue.popleft()]['neighbors']:
            if j in allowed and j not in found:found.add(j);queue.append(j)
    return found


def tests():
    scenarios=0
    s=fixture();call(s,'open_effect');initial=copy.deepcopy(s)
    assert v(s,'budget')==24 and v(s,'round')==1
    assert v(s,'machine_output')==2, 'Starting layout must produce the first target'
    assert v(s,'next_machines')==2
    before=resources(s);call(s,'refresh');call(s,'refresh');assert resources(s)==before
    call(s,'close_effect');call(s,'open_effect');assert resources(s)==before
    saved=json.dumps({**s,'flags':list(s['flags']),'owned':list(s['owned']),'controlled':list(s['controlled'])})
    loaded=json.loads(saved)
    for k in ['flags','owned','controlled']:loaded[k]=set(loaded[k])
    call(loaded,'refresh');assert resources(loaded)==before
    scenarios+=5
    for country,ai in [('FRA',False),('RUS',True)]:
        other=fixture();other['tag']=country;other['ai']=ai;call(other,'open_effect')
        assert 'RUS_ip_initialized' not in other['flags'];scenarios+=1
    rng=random.Random(219)
    for _ in range(60):
        q=copy.deepcopy(initial)
        for c in DATA['cells']:
            put(q,f'n{c["id"]}_rail',rng.randrange(4))
            if rng.random()<.18:q['controlled'].discard(c['state'])
        call(q,'refresh')
        got={c['id'] for c in DATA['cells'] if v(q,f'n{c["id"]}_connected')==1}
        assert got==reachable(q),(got,reachable(q))
        assert v(q,'iterations')<=len(DATA['cells'])
        for key in ['next_coal','next_iron','next_steel','next_machines','power_left','transport_left']:assert v(q,key)>=0
        scenarios+=1
    # Direct effect calls still recheck cash, ownership, facility type and level.
    for kind,cost in [(1,2),(2,2),(3,3),(4,4),(5,5)]:
        for condition in ['valid','cash','occupied','max','foreign','closed','finished']:
            q=copy.deepcopy(initial);put(q,'budget',24)
            i=next(c['id'] for c in DATA['cells'] if kind>2 or c['coal' if kind==1 else 'iron'])
            select(q,i);put(q,f'n{i}_type',0);put(q,f'n{i}_level',0);put(q,f'n{i}_paid',0)
            if condition=='cash':put(q,'budget',cost-1)
            if condition=='occupied':put(q,f'n{i}_type',5 if kind!=5 else 3);put(q,f'n{i}_level',1)
            if condition=='max':put(q,f'n{i}_type',kind);put(q,f'n{i}_level',3)
            if condition=='foreign':q['controlled'].discard(DATA['cells'][i]['state'])
            if condition=='closed':q['flags'].discard('RUS_ip_open')
            if condition=='finished':q['flags'].add('RUS_ip_finished')
            prior=resources(q);level=v(q,f'n{i}_level');call(q,f'build_{kind}')
            if condition=='valid':assert v(q,f'n{i}_level')==level+1 and v(q,'budget')==prior[0]-cost
            else:assert resources(q)==prior and v(q,f'n{i}_level')==level
            scenarios+=1
    for kind,key in [(1,'coal'),(2,'iron')]:
        q=copy.deepcopy(initial);i=next(c['id'] for c in DATA['cells'] if not c[key]);select(q,i)
        put(q,f'n{i}_type',0);put(q,f'n{i}_level',0);before=resources(q);call(q,f'build_{kind}');assert resources(q)==before;scenarios+=1
    # Removing starter property gives no free cash; only paid upgrades are refunded.
    q=copy.deepcopy(initial);i=DATA['hub'];select(q,i);before=v(q,'budget')
    call(q,'build_3');assert v(q,'budget')==before-3
    call(q,'remove');assert v(q,'budget')==before
    call(q,'remove');assert v(q,'budget')==before
    call(q,'rail');assert v(q,'budget')==before-2
    call(q,'remove_rail');assert v(q,'budget')==before
    call(q,'remove_rail');assert v(q,'budget')==before
    assert v(q,'connected_count')==0 and v(q,'machine_output')==0;scenarios+=5
    q=copy.deepcopy(initial)
    for round_number in range(1,6):
        call(q,'refresh');prediction={key:v(q,'next_'+key) for key in ['coal','iron','steel','machines']}
        score=v(q,'score');target=v(q,'target');call(q,'settle')
        assert all(v(q,key)==number for key,number in prediction.items())
        assert v(q,'score')==score+(20 if prediction['machines']>=target else 0)
        assert v(q,'round')==min(5,round_number+1)
        scenarios+=1
    assert 'RUS_ip_finished' in q['flags'];before=resources(q)
    call(q,'settle');call(q,'settle');assert resources(q)==before
    call(q,'confirm_restart');assert resources(q)==before
    call(q,'arm_restart');call(q,'confirm_restart');assert resources(q)==resources(initial)
    assert q['vars']['RUS_first_five_year_plan_score']==37 and q['vars']['political_power']==200
    scenarios+=4
    # A funded strategy must actually satisfy all five increasing targets.
    # Nodes are real neighbouring districts, including a new rail corridor to Tomsk.
    q=copy.deepcopy(initial)
    plans=[
        [(5,'build_3',2),(2,'build_4',2),(16,'build_1',1),(4,'build_2',1),(3,'build_5',1)],
        [(16,'build_1',1),(4,'build_2',1)],
        [(7,'rail',1),(7,'build_3',2),(1,'rail',1),(1,'build_4',2),(17,'rail',1),(19,'rail',1),(19,'build_1',2),(3,'build_5',1)],
        [(7,'build_3',1),(1,'build_4',1),(19,'build_1',1)],
        [(6,'rail',1),(6,'build_2',2),(9,'rail',1),(9,'build_4',1),(15,'rail',1),(15,'build_3',1),(8,'rail',1),(8,'build_5',1)],
    ]
    for actions in plans:
        for i,action,times in actions:
            select(q,i)
            for _ in range(times):
                before=v(q,'budget');call(q,action)
                assert 0<=v(q,'budget')<before,(i,action,before)
        assert v(q,'next_machines')>=v(q,'target')
        call(q,'settle');scenarios+=1
    assert v(q,'score')==100 and v(q,'machines')==25
    # Maximal connected layouts are bounded and never create negative stock.
    for kind in range(1,6):
        q=copy.deepcopy(initial)
        for c in DATA['cells']:
            i=c['id'];put(q,f'n{i}_rail',3);put(q,f'n{i}_type',kind);put(q,f'n{i}_level',3)
        call(q,'refresh');assert v(q,'connected_count')==len(DATA['cells'])
        assert all(v(q,k)>=0 for k in ['next_coal','next_iron','next_steel','power_left','transport_left']);scenarios+=1
    # The data follows real state borders and has a complete, symmetric network.
    members=[s for c in DATA['cells'] for s in c['states']]
    assert len(members)==len(set(members))==104
    assert len(DATA['cells'])==36 and all(c['state'] in c['states'] for c in DATA['cells'])
    for i,a in enumerate(DATA['cells']):
        for b in DATA['cells'][i+1:]:assert abs(a['x']-b['x'])>=40 or abs(a['y']-b['y'])>=38,('Overlapping markers',a['id'],b['id'])
        for j in a['neighbors']:assert i in DATA['cells'][j]['neighbors']
    assert {tuple(x) for x in DATA['sea_edges']}=={(27,28),(29,31)}
    for lang in ['simp_chinese','english','russian']:
        path=ROOT/f'localisation/{lang}/RUS_industrial_planning_l_{lang}.yml'
        assert path.read_bytes().startswith(b'\xef\xbb\xbf')
        keys=[]
        for line in path.read_text(encoding='utf-8-sig').splitlines()[1:]:
            match=re.fullmatch(r' ([\w.]+):0 "(?:[^"\\]|\\.)*"',line);assert match,(path,line)
            keys.append(match[1])
        assert len(keys)==len(set(keys))
    print(f'PASS: {scenarios} script scenarios; geographic districts, graph connectivity, costs/refunds, forecasting, five rounds, save state and country isolation. Not an HOI4 runtime test.')


if __name__=='__main__':tests()
