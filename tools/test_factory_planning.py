"""Execute the generated factory scripts, including lifecycle and production.

This interpreter is a test fixture, not the game engine. The independent graph
oracle and conservation checks cover the risky network and accounting rules.
"""
from __future__ import annotations
import copy
import heapq
import json
import math
import random
import re
import time
from pathlib import Path
from hoi4_politics_blocks import parse
from industrial_planning_factory import CELLS, COAL, IRON, ROCKS, HUB, COST, P

ROOT=Path(__file__).resolve().parents[1]
FX={n.k:n.v for n in parse((ROOT/'common/scripted_effects/RUS_industrial_planning_effects.txt').read_text(encoding='utf-8'))}
TR={n.k:n.v for n in parse((ROOT/'common/scripted_triggers/RUS_industrial_planning_triggers.txt').read_text(encoding='utf-8'))}
GUI=next(n for n in parse((ROOT/'common/scripted_guis/RUS_industrial_planning.txt').read_text(encoding='utf-8'))[0].v if n.k=='RUS_industrial_planning_gui')


def fixture(unlocked=True):
    return dict(tag='RUS',ai=False,vars={'RUS_first_five_year_plan_score':37,'political_power':200},
                flags={'RUS_ip_ui_unlocked'} if unlocked else set(),commands=0)


def value(s,x):
    try:return float(x)
    except (ValueError,TypeError):return s['vars'].get(x,0)


def compare(a,op,b):return {'=':a==b,'>':a>b,'<':a<b,'>=':a>=b,'<=':a<=b}[op]


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
        elif k=='hidden_effect':run(v,s)
        elif k in ('effect_tooltip','custom_effect_tooltip'):pass
        elif k=='set_country_flag':s['flags'].add(v)
        elif k=='clr_country_flag':s['flags'].discard(v)
        elif k in ('set_variable','add_to_variable','subtract_from_variable','multiply_variable','divide_variable'):
            a=v[0];number=value(s,a.v);prior=value(s,a.k)
            if k=='set_variable':result=number
            elif k=='add_to_variable':result=prior+number
            elif k=='subtract_from_variable':result=prior-number
            elif k=='multiply_variable':result=prior*number
            else:assert number!=0;result=prior/number
            assert math.isfinite(result),(k,a.k,result)
            s['vars'][a.k]=result
        elif k=='clamp_variable':s['vars'][n.value('var')]=min(value(s,n.value('max')),max(value(s,n.value('min')),value(s,n.value('var'))))
        elif k=='while_loop_effect':
            iterations=0
            while check(n.one('limit').v,s):
                iterations+=1;assert iterations<=48,'Network relaxation did not terminate'
                run([c for c in v if c.k!='limit'],s)
        elif k=='every_country':
            if check(n.one('limit').v,s):run([c for c in v if c.k!='limit'],s)
        else:raise AssertionError(('Unsupported effect',k))


def call(s,name):run(FX[P+name],s)
def v(s,name):return value(s,P+name)
def put(s,name,number):s['vars'][P+name]=number
def select(s,i):put(s,'selected',i);call(s,'refresh')
def gui_click(s,name):run(GUI.one('effects').one(name+'_click').v,s)
def opened():
    s=fixture();call(s,'open_effect');return s
def builds(s,i,kind,levels=1):
    select(s,i)
    for _ in range(levels):call(s,'rail' if kind=='rail' else f'build_{kind}')


def starter(s=None):
    """A complete, affordable chain around the bottom two deposit sites."""
    s=s or opened()
    for i in (42,41,33,44,45,46,38):builds(s,i,'rail')
    for i,k in ((33,1),(38,2),(42,3),(44,4),(45,5)):builds(s,i,k)
    return s


def invariants(s):
    assert s['vars']['RUS_first_five_year_plan_score']==37 and s['vars']['political_power']==200
    assert all(v(s,k)>=-1e-8 for k in ('budget','coal','iron','steel','machines'))
    assert 0<=v(s,'days_left')<=1800 and 0<=v(s,'score')<=100
    assert math.isclose(v(s,'budget'),40+v(s,'earned')-v(s,'spent')+v(s,'refunded'),abs_tol=1e-7)
    assert math.isclose(v(s,'earned'),v(s,'machines'),abs_tol=1e-7)
    assert v(s,'days_left')+v(s,'elapsed')==1800
    for c in CELLS:
        i=c['id']
        assert 0<=v(s,f'n{i}_effective')<=v(s,f'n{i}_level')<=3
        assert 0<=v(s,f'n{i}_route')<=v(s,f'n{i}_rail')<=3


def graph_oracle(s):
    """Independent priority-queue widest path, instead of script relaxation."""
    grades=[0]*48;grades[HUB]=3;queue=[(-3,HUB)]
    while queue:
        negative,i=heapq.heappop(queue);g=-negative
        if g!=grades[i]:continue
        for j in CELLS[i]['neighbors']:
            if j in ROCKS:continue
            candidate=min(g,v(s,f'n{j}_rail'))
            if candidate>grades[j]:
                grades[j]=candidate;heapq.heappush(queue,(-candidate,j))
    return grades


def production_snapshot(s):
    keys=['budget','coal','iron','steel','machines','days_left','elapsed','earned','spent','refunded']
    keys += [f'n{c["id"]}_{k}' for c in CELLS for k in ('type','level','rail','paid','rail_paid','paused')]
    return {k:v(s,k) for k in keys}


def test_lifecycle():
    count=0
    s=fixture(False);call(s,'open_effect');assert 'RUS_ip_factory_initialized' not in s['flags']
    call(s,'enable_gui');assert v(s,'budget')==40 and v(s,'days_left')==1800;count+=1
    before=production_snapshot(s)
    for key in ('open_effect','daily','refresh','forecast','enable_gui'):call(s,key)
    assert production_snapshot(s)==before;count+=1
    for tag,ai in [('GER',False),('RUS',True)]:
        t=fixture(False);t['tag']=tag;t['ai']=ai;call(t,'enable_gui');assert not t['flags'];count+=1
    s=starter();before=production_snapshot(s)
    for _ in range(3):call(s,'refresh');call(s,'forecast');call(s,'daily')
    assert production_snapshot(s)==before;count+=1
    call(s,'start');call(s,'close_effect');call(s,'daily')
    assert v(s,'elapsed')==1 and v(s,'machines')>0;count+=1
    for field,newvalue in [('tag','GER'),('ai',True)]:
        t=copy.deepcopy(s);t[field]=newvalue;b=production_snapshot(t);call(t,'daily');assert production_snapshot(t)==b;count+=1
    t=copy.deepcopy(s);t['flags'].discard('RUS_ip_ui_unlocked');b=production_snapshot(t);call(t,'daily');assert production_snapshot(t)==b;count+=1
    call(s,'open_effect');call(s,'start');assert v(s,'elapsed')==1;count+=1
    startup=parse((ROOT/'common/on_actions/RUS_industrial_planning_on_actions.txt').read_text(encoding='utf-8'))[0].one('on_startup').one('effect').v
    before=production_snapshot(s);run(startup,s);assert production_snapshot(s)==before;count+=1
    # Serialize everything exactly as country variables and flags would persist.
    payload=json.dumps({**s,'flags':sorted(s['flags'])});loaded=json.loads(payload);loaded['flags']=set(loaded['flags'])
    call(s,'daily');run(startup,loaded);call(loaded,'daily');assert production_snapshot(s)==production_snapshot(loaded);count+=1
    call(s,'confirm_restart');assert v(s,'elapsed')==2
    call(s,'arm_restart');call(s,'confirm_restart');assert v(s,'elapsed')==0 and v(s,'budget')==40
    assert 'RUS_ip_active' not in s['flags'];invariants(s);count+=1
    return count


def test_building_rules():
    count=0
    for site,kind in [(HUB,3),(11,3),(0,1),(0,2),(33,3),(38,5),(33,2),(38,1)]:
        s=opened();builds(s,site,kind);assert v(s,'budget')==40 and v(s,f'n{site}_type')==0;count+=1
    s=opened();builds(s,33,1,5);assert v(s,'n33_level')==3 and v(s,'budget')==31;count+=1
    builds(s,33,'rail',5);assert v(s,'n33_rail')==3 and v(s,'budget')==28;count+=1
    builds(s,44,4);builds(s,44,5);assert v(s,'n44_type')==4 and v(s,'budget')==22;count+=1
    select(s,44);call(s,'remove');assert v(s,'budget')==28
    call(s,'remove');assert v(s,'budget')==28;count+=1
    select(s,33);call(s,'remove');assert v(s,'n33_rail')==3 and v(s,'budget')==37
    call(s,'remove_rail');assert v(s,'budget')==40
    call(s,'remove_rail');assert v(s,'budget')==40;invariants(s);count+=1
    for site in (HUB,*ROCKS):
        select(s,site)
        for action in ('rail','remove','remove_rail','switch'):call(s,action)
        assert v(s,'budget')==40 and v(s,f'n{HUB}_rail')==3;count+=1
    s=opened();put(s,'budget',2.99);builds(s,33,1);assert v(s,'n33_level')==0;count+=1
    # Hidden page widgets and a closed window cannot mutate the board.
    s=opened();select(s,33);call(s,'toggle_help');before=production_snapshot(s)
    gui_click(s,'ip_build_1');gui_click(s,'ip_cell_38');assert production_snapshot(s)==before and v(s,'selected')==33;count+=1
    call(s,'close_effect');call(s,'build_1');assert production_snapshot(s)==before;count+=1
    # Pausing suppresses production only, not transit connectivity.
    s=starter();select(s,44);call(s,'switch');assert v(s,'steel_capacity')==0 and v(s,'n45_route')==1
    call(s,'switch');assert v(s,'steel_capacity')==1;invariants(s);count+=1
    return count


def test_network():
    count=0;s=opened()
    for i in (0,1,8,9):put(s,f'n{i}_rail',3)
    call(s,'refresh');assert all(v(s,f'n{i}_route')==0 for i in (0,1,8,9));count+=1
    # A longer high-grade route must beat a short low-grade one.
    for i,g in [(44,1),(45,3),(35,3),(36,3),(37,3)]:put(s,f'n{i}_rail',g)
    put(s,'n45_type',5);put(s,'n45_level',3);call(s,'refresh')
    assert v(s,'n45_route')==3 and v(s,'n45_effective')==3;count+=1
    put(s,'n37_rail',0);call(s,'refresh');assert v(s,'n45_effective')==1;count+=1
    rng=random.Random(1764)
    for _ in range(80):
        s=opened()
        for c in CELLS:
            if c['id']!=HUB and not c['rock']:put(s,f'n{c["id"]}_rail',rng.choice((0,0,1,2,3)))
        call(s,'refresh');expected=graph_oracle(s)
        assert [v(s,f'n{i}_route') for i in range(48)]==expected
        assert v(s,'iterations')<=48;count+=1
    return count


def test_production():
    count=0;s=starter();assert v(s,'budget')==8
    assert math.isclose(v(s,'machine_output'),.2) # Initial steel buffer allows full machinery output.
    before=production_snapshot(s);call(s,'start');call(s,'daily')
    assert math.isclose(v(s,'coal'),before['coal']+.3-.1-.2)
    assert math.isclose(v(s,'iron'),before['iron']+.3-.2)
    assert math.isclose(v(s,'steel'),before['steel']+.2-.4)
    assert math.isclose(v(s,'machines'),.2);invariants(s);count+=1
    for _ in range(30):call(s,'daily')
    assert math.isclose(v(s,'machine_output'),.1,abs_tol=1e-8);invariants(s);count+=1
    # Refresh, help and repeated selection must not manufacture free output.
    before=production_snapshot(s)
    for _ in range(5):call(s,'refresh');call(s,'toggle_help');select(s,45)
    assert production_snapshot(s)==before;count+=1
    rng=random.Random(519)
    for _ in range(60):
        s=opened()
        for key in ('coal','iron','steel'):put(s,key,rng.choice([0,0,.05,.1,1,12]))
        for key in ('coal','iron','power','steel','machine'):put(s,key+'_capacity',rng.randrange(7))
        before=production_snapshot(s);call(s,'forecast');assert production_snapshot(s)==before
        coal_in=v(s,'coal_output');iron_in=v(s,'iron_output');fuel=v(s,'fuel');steel=v(s,'steel_output');mach=v(s,'machine_output')
        for key in ('fuel','steel_output','machine_output','power_left'):assert v(s,key)>=-1e-8
        assert math.isclose(v(s,'next_coal'),v(s,'coal')+coal_in-fuel-steel,abs_tol=1e-8)
        assert math.isclose(v(s,'next_iron'),v(s,'iron')+iron_in-steel,abs_tol=1e-8)
        assert math.isclose(v(s,'next_steel'),v(s,'steel')+steel-mach*2,abs_tol=1e-8)
        assert math.isclose(v(s,'power_left'),fuel*6-steel*2-mach,abs_tol=1e-8)
        assert mach<=v(s,'machine_rate')+1e-8 and steel<=v(s,'steel_rate')+1e-8
        assert math.isclose(v(s,'investment_output'),mach);count+=1
    s=starter();call(s,'start');put(s,'days_left',1);put(s,'elapsed',1799);call(s,'daily')
    assert v(s,'days_left')==0 and 'RUS_ip_finished' in s['flags'] and 'RUS_ip_active' not in s['flags']
    before=production_snapshot(s);call(s,'daily');builds(s,33,1);assert production_snapshot(s)==before;invariants(s);count+=1
    return count


def test_full_campaign():
    """Run a legal build/upgrade strategy for exactly 1800 real script ticks."""
    s=starter();call(s,'start')
    # A second steelworks balances one machine level. Then expand the mines,
    # power, steel and machinery using only delivery income (no injected funds).
    orders=[(33,'rail'),(41,'rail'),(42,'rail'),(33,1),(46,3),(41,4),
            (38,'rail'),(44,'rail'),(45,'rail'),(46,'rail'),(38,2),
            (33,'rail'),(41,'rail'),(42,'rail'),(33,1),(42,3),(44,4),(45,5),
            (25,'rail'),(17,'rail'),(17,1),(46,3),(41,4),
            (38,'rail'),(44,'rail'),(45,'rail'),(46,'rail'),(38,2)]
    completed=[]
    for day in range(1800):
        while orders:
            i,k=orders[0];select(s,i)
            trigger='can_rail' if k=='rail' else f'can_build_{k}'
            if not check(TR[P+trigger],s):break
            call(s,'rail' if k=='rail' else f'build_{k}');completed.append((day,*orders.pop(0)))
        call(s,'daily')
        if day%100==0:invariants(s)
    invariants(s)
    assert v(s,'elapsed')==1800 and v(s,'days_left')==0
    assert v(s,'machines')>=500, (v(s,'machines'),v(s,'budget'),orders,completed)
    assert v(s,'score')==100
    print(f'Campaign: {v(s,"machines"):.1f} deliveries, {v(s,"budget"):.1f} investment left; {len(completed)} expansion actions.')
    before=production_snapshot(s);call(s,'daily');assert production_snapshot(s)==before
    return 2


def main():
    started=time.perf_counter()
    total=sum(test() for test in (test_lifecycle,test_building_rules,test_network,test_production,test_full_campaign))
    print(f'{total} generated-script scenarios passed in {time.perf_counter()-started:.1f}s.')


if __name__=='__main__':main()
