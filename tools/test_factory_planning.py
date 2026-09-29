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
from industrial_planning_factory import CELLS, REGIONS, HUBS, HUB, COST, P, WIDTH, HEIGHT, cell_id

ROOT=Path(__file__).resolve().parents[1]
FX={n.k:n.v for n in parse((ROOT/'common/scripted_effects/RUS_industrial_planning_effects.txt').read_text(encoding='utf-8'))}
TR={n.k:n.v for n in parse((ROOT/'common/scripted_triggers/RUS_industrial_planning_triggers.txt').read_text(encoding='utf-8'))}
GUI=next(n for n in parse((ROOT/'common/scripted_guis/RUS_industrial_planning.txt').read_text(encoding='utf-8'))[0].v if n.k=='RUS_industrial_planning_gui')


def fixture(unlocked=True,seed=47):
    return dict(tag='RUS',ai=False,vars={'RUS_first_five_year_plan_score':37,'political_power':200},
                flags={'RUS_ip_ui_unlocked'} if unlocked else set(),commands=0,rng=seed,draws=0)


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
        elif k=='random_list':
            options=[]
            for option in v:
                weight=float(option.k)
                for mod in option.v:
                    if mod.k=='modifier' and check([c for c in mod.v if c.k!='factor'],s):weight*=float(mod.value('factor'))
                if weight>0:options.append((weight,option))
            assert options,'A random quota ran out of eligible tiles'
            # Reproducible fixture RNG, not an emulation of HOI4's RNG stream.
            s['rng']=(1664525*s['rng']+1013904223)%(2**32);s['draws']+=1
            draw=s['rng']/(2**32)*sum(w for w,o in options)
            for weight,option in options:
                draw-=weight
                if draw<0:
                    run([c for c in option.v if c.k!='modifier'],s);break
        elif k=='while_loop_effect':
            iterations=0
            while check(n.one('limit').v,s):
                iterations+=1;assert iterations<=len(CELLS),'Network relaxation did not terminate'
                run([c for c in v if c.k!='limit'],s)
        elif k=='every_country':
            if check(n.one('limit').v,s):run([c for c in v if c.k!='limit'],s)
        else:raise AssertionError(('Unsupported effect',k))


def call(s,name):run(FX[P+name],s)
def v(s,name):return value(s,P+name)
def put(s,name,number):s['vars'][P+name]=number
def select(s,i):
    if v(s,'region')!=CELLS[i]['region']:call(s,f'select_region_{CELLS[i]["region"]}')
    gui_click(s,f'ip_cell_{i}')
def gui_click(s,name):run(GUI.one('effects').one(name+'_click').v,s)
def opened(seed=47):
    s=fixture(seed=seed);call(s,'open_effect');return s
def builds(s,i,kind,levels=1):
    select(s,i)
    for _ in range(levels):call(s,'rail' if kind=='rail' else f'build_{kind}')



def sites(s,rid=0):
    r=REGIONS[rid];starter=r['starter']
    return dict(coal=next(i for i in starter if v(s,f'n{i}_terrain')==1),
        iron=next(i for i in starter if v(s,f'n{i}_terrain')==2),
        power=starter[1],steel=starter[2],machine=starter[3],spare_power=starter[4],spare_steel=starter[5])


def starter(s=None,rid=0):
    """A real UI build sequence: 11 line tiles plus five plants costs 36."""
    s=s or opened();t=sites(s,rid)
    for i in REGIONS[rid]['starter'][1:]:builds(s,i,'rail')
    for key,kind in [('coal',1),('iron',2),('power',3),('steel',4),('machine',5)]:builds(s,t[key],kind)
    return s


def path_to(s,target):
    start=REGIONS[CELLS[target]['region']]['hub'];queue=[start];paths={start:[]}
    for i in queue:
        for j in CELLS[i]['neighbors']:
            if j not in paths and v(s,f'n{j}_terrain')!=3:
                paths[j]=paths[i]+[j];queue.append(j)
    return paths[target]


def expansion_orders(s,rid=0):
    t=sites(s,rid);rails={i:v(s,f'n{i}_rail') for i in REGIONS[rid]['cells']};orders=[]
    def upgrade(site,kind,rail_grade):
        for i in path_to(s,site):
            while rails[i]<rail_grade:orders.append((i,'rail'));rails[i]+=1
        orders.append((site,kind))
    upgrade(t['coal'],1,2);upgrade(t['iron'],2,2)
    upgrade(t['spare_power'],3,1);upgrade(t['spare_steel'],4,1)
    upgrade(t['coal'],1,3);upgrade(t['power'],3,2)
    upgrade(t['steel'],4,2);upgrade(t['machine'],5,2)
    other_coal=min((i for i in REGIONS[rid]['cells'] if i!=t['coal'] and v(s,f'n{i}_terrain')==1),key=lambda i:len(path_to(s,i)))
    upgrade(other_coal,1,1);upgrade(t['spare_power'],3,2)
    upgrade(t['spare_steel'],4,2);upgrade(t['iron'],2,3)
    return orders


def invariants(s):
    assert s['vars']['RUS_first_five_year_plan_score']==37 and s['vars']['political_power']==200
    assert v(s,'budget')>=-1e-8 and 0<=v(s,'score')<=100
    assert v(s,'days_left')+v(s,'elapsed')==1800
    assert math.isclose(v(s,'budget'),40+v(s,'earned')-v(s,'spent')+v(s,'refunded'),abs_tol=1e-7)
    assert math.isclose(v(s,'earned'),v(s,'machines'),abs_tol=1e-7)
    assert math.isclose(v(s,'machines'),sum(v(s,f'r{r["id"]}_machines') for r in REGIONS),abs_tol=1e-7)
    for r in REGIONS:
        for key in ('coal','iron','steel','machines'):assert v(s,f'r{r["id"]}_{key}')>=-1e-8
    for c in CELLS:
        i=c['id']
        assert 0<=v(s,f'n{i}_effective')<=v(s,f'n{i}_level')<=3
        assert 0<=v(s,f'n{i}_route')<=v(s,f'n{i}_rail')<=3


def graph_oracle(s):
    """Independent priority-queue widest paths, one root per region."""
    grades=[0]*len(CELLS);queue=[]
    for hub in HUBS:grades[hub]=3;heapq.heappush(queue,(-3,hub))
    while queue:
        negative,i=heapq.heappop(queue);g=-negative
        if g!=grades[i]:continue
        for j in CELLS[i]['neighbors']:
            if v(s,f'n{j}_terrain')==3:continue
            candidate=min(g,v(s,f'n{j}_rail'))
            if candidate>grades[j]:grades[j]=candidate;heapq.heappush(queue,(-candidate,j))
    return grades


def production_snapshot(s):
    keys=['budget','machines','days_left','elapsed','earned','spent','refunded']
    keys += [f'r{r["id"]}_{k}' for r in REGIONS for k in ('coal','iron','steel','machines')]
    keys += [f'n{c["id"]}_{k}' for c in CELLS for k in ('type','level','rail','paid','rail_paid','paused','terrain')]
    return {k:v(s,k) for k in keys}


def geology_snapshot(s):return tuple(v(s,f'n{c["id"]}_terrain') for c in CELLS)


def test_lifecycle():
    count=0;s=fixture(False);call(s,'open_effect');assert 'RUS_ip_factory_initialized' not in s['flags']
    call(s,'enable_gui');assert v(s,'budget')==40 and v(s,'days_left')==1800;count+=1
    before=production_snapshot(s);draws=s['draws']
    for key in ('open_effect','daily','refresh','forecast','enable_gui'):call(s,key)
    assert production_snapshot(s)==before and s['draws']==draws;count+=1
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
    payload=json.dumps({**s,'flags':sorted(s['flags'])});loaded=json.loads(payload);loaded['flags']=set(loaded['flags'])
    call(s,'daily');run(startup,loaded);call(loaded,'daily');assert production_snapshot(s)==production_snapshot(loaded);count+=1
    old=geology_snapshot(s);call(s,'confirm_restart');assert v(s,'elapsed')==2
    call(s,'arm_restart');call(s,'confirm_restart');assert v(s,'elapsed')==0 and v(s,'budget')==40
    assert old!=geology_snapshot(s) and 'RUS_ip_active' not in s['flags'];invariants(s);count+=1
    return count


def test_geology():
    count=0;layouts=[]
    assert len(REGIONS)==6 and len({tuple((r['width'],r['height'])) for r in REGIONS})>=5
    assert all(r['coal']>=5 and r['iron']>=6 for r in REGIONS),'Every map needs several basic mine sites'
    for seed in range(20):
        s=opened(seed);layouts.append(geology_snapshot(s))
        for r in REGIONS:
            terrain=[v(s,f'n{i}_terrain') for i in r['cells']]
            assert terrain.count(1)==r['coal'] and terrain.count(2)==r['iron'] and terrain.count(3)==r['rocks']
            assert terrain.count(4)==1 and v(s,f'n{r["hub"]}_terrain')==4
            for i in r['cells']:
                if v(s,f'n{i}_terrain')!=3:assert i==r['hub'] or path_to(s,i)
            for i in r['starter']:
                if i not in r['starter'][-2:] and i!=r['hub']:assert v(s,f'n{i}_terrain')==0
            count+=1
    assert len(set(layouts))==20
    for r in REGIONS:assert len({tuple(row[i] for i in r['cells']) for row in layouts})>1
    # Reopening, changing region and previewing cannot reroll or consume RNG.
    s=opened();before=geology_snapshot(s);draws=s['draws']
    for r in REGIONS:call(s,f'select_region_{r["id"]}');call(s,'close_effect');call(s,'open_effect')
    assert geology_snapshot(s)==before and s['draws']==draws;count+=1
    for r in REGIONS:
        s=starter(opened(13+r['id']),r['id'])
        assert v(s,'budget')==4
        call(s,'start');call(s,'daily')
        assert v(s,f'r{r["id"]}_machines')>0
        assert all(v(s,f'r{other["id"]}_machines')==0 for other in REGIONS if other!=r)
        invariants(s);count+=1
    return count+2


def test_building_rules():
    s=opened();t=sites(s);rock=next(c['id'] for c in CELLS if v(s,f'n{c["id"]}_terrain')==3);count=0
    invalid=[(HUB,3),(rock,3),(t['power'],1),(t['power'],2),(t['coal'],3),(t['iron'],5),(t['coal'],2),(t['iron'],1)]
    for i,k in invalid:builds(s,i,k);assert v(s,'budget')==40 and v(s,f'n{i}_type')==0;count+=1
    builds(s,t['coal'],1,5);assert v(s,f'n{t["coal"]}_level')==3 and v(s,'budget')==31;count+=1
    builds(s,t['coal'],'rail',5);assert v(s,f'n{t["coal"]}_rail')==3 and v(s,'budget')==28;count+=1
    builds(s,t['steel'],4);builds(s,t['steel'],5);assert v(s,f'n{t["steel"]}_type')==4 and v(s,'budget')==22;count+=1
    select(s,t['steel']);call(s,'remove');assert v(s,'budget')==28
    call(s,'remove');assert v(s,'budget')==28;count+=1
    select(s,t['coal']);call(s,'remove');assert v(s,f'n{t["coal"]}_rail')==3 and v(s,'budget')==37
    call(s,'remove_rail');assert v(s,'budget')==40
    call(s,'remove_rail');assert v(s,'budget')==40;invariants(s);count+=1
    for i in (HUB,rock):
        select(s,i)
        for action in ('rail','remove','remove_rail','switch'):call(s,action)
        assert v(s,'budget')==40 and v(s,f'n{HUB}_rail')==3;count+=1
    put(s,'budget',2.99);builds(s,t['coal'],1);assert v(s,f'n{t["coal"]}_level')==0;count+=1
    s=opened();select(s,t['coal']);call(s,'toggle_help');before=production_snapshot(s)
    gui_click(s,'ip_build_1');gui_click(s,f'ip_cell_{t["iron"]}');gui_click(s,'ip_region_5')
    assert production_snapshot(s)==before and v(s,'selected')==t['coal'] and v(s,'region')==0;count+=1
    call(s,'close_effect');call(s,'build_1');assert production_snapshot(s)==before;count+=1
    s=starter();select(s,t['steel']);call(s,'switch');assert v(s,'steel_capacity')==0 and v(s,f'n{t["machine"]}_route')==1
    call(s,'switch');assert v(s,'steel_capacity')==1;invariants(s);count+=1
    # Hidden map clicks and spoofed selection cannot spend money off-screen.
    other=sites(s,5)['coal'];before=production_snapshot(s);gui_click(s,f'ip_cell_{other}')
    assert production_snapshot(s)==before and v(s,'selected')==t['steel']
    put(s,'selected',other);call(s,'build_1');assert production_snapshot(s)==before;count+=1
    return count


def test_network():
    count=0;rng=random.Random(830)
    for case in range(40):
        s=opened(case)
        for c in CELLS:
            i=c['id']
            if i in HUBS or v(s,f'n{i}_terrain')==3:continue
            put(s,f'n{i}_rail',rng.choice([0,0,1,2,3]))
            put(s,f'n{i}_type',rng.randrange(6));put(s,f'n{i}_level',rng.randrange(1,4));put(s,f'n{i}_paused',rng.randrange(2))
        call(s,'refresh');expected=graph_oracle(s)
        assert [v(s,f'n{c["id"]}_route') for c in CELLS]==expected
        for c in CELLS:
            i=c['id'];effective=0 if v(s,f'n{i}_paused') or not v(s,f'n{i}_type') else min(v(s,f'n{i}_level'),expected[i])
            assert v(s,f'n{i}_effective')==effective
        count+=1
    # Isolated cycles stay disconnected; adding a graded path and then removing
    # one segment must recalculate instead of keeping stale route capacity.
    s=opened();target=REGIONS[0]['starter'][-1];path=path_to(s,target)
    for i in path:put(s,f'n{i}_rail',3)
    call(s,'refresh');assert v(s,f'n{target}_route')==3
    put(s,f'n{path[0]}_rail',1);call(s,'refresh');assert v(s,f'n{target}_route')==1
    put(s,f'n{path[0]}_rail',0);call(s,'refresh');assert v(s,f'n{target}_route')==0;count+=3
    return count


def test_production():
    count=0;rng=random.Random(74);s=opened()
    for case in range(40):
        for r in REGIONS:
            rp=f'r{r["id"]}_'
            for k in ('coal','iron','steel'):put(s,rp+k,rng.random()*3)
            for k in ('coal','iron','power','steel','machine'):put(s,rp+k+'_capacity',rng.randrange(8))
        before=production_snapshot(s);draws=s['draws'];call(s,'forecast')
        assert production_snapshot(s)==before and s['draws']==draws
        for r in REGIONS:
            rp=f'r{r["id"]}_';get=lambda k:v(s,rp+k)
            coal_in=get('coal_capacity')*.3;iron_in=get('iron_capacity')*.3
            fuel=min(get('power_capacity')*.1,get('coal')+coal_in)
            steel=min(get('steel_capacity')*.2,get('coal')+coal_in-fuel,get('iron')+iron_in,fuel*3)
            mach=min(get('machine_capacity')*.2,(get('steel')+steel)/2,max(0,fuel*6-steel*2))
            expected={'next_coal':get('coal')+coal_in-fuel-steel,'next_iron':get('iron')+iron_in-steel,
                'next_steel':get('steel')+steel-mach*2,'power_left':fuel*6-steel*2-mach,'machine_output':mach}
            for key,n in expected.items():assert math.isclose(get(key),n,abs_tol=1e-8),(key,get(key),n)
            assert math.isclose(get('investment_output'),mach,abs_tol=1e-8)
        assert math.isclose(v(s,'investment_output'),sum(v(s,f'r{r["id"]}_machine_output') for r in REGIONS),abs_tol=1e-8);count+=1
    # Two actual starter factories continue while an empty third region is open.
    s=starter();put(s,'budget',v(s,'budget')+36);starter(s,1);call(s,'start');call(s,'select_region_5')
    empty=tuple(v(s,'r5_'+k) for k in ('coal','iron','steel'));budget=v(s,'budget');call(s,'daily')
    assert v(s,'r0_machines')>0 and v(s,'r1_machines')>0 and v(s,'r5_machines')==0
    assert tuple(v(s,'r5_'+k) for k in ('coal','iron','steel'))==empty
    assert math.isclose(v(s,'budget')-budget,v(s,'machines'),abs_tol=1e-8);count+=1
    # A last daily tick produces exactly once; expiry blocks builds everywhere.
    s=starter();call(s,'start');put(s,'days_left',1);put(s,'elapsed',1799);call(s,'daily')
    assert v(s,'days_left')==0 and 'RUS_ip_finished' in s['flags'] and 'RUS_ip_active' not in s['flags']
    before=production_snapshot(s);call(s,'daily');builds(s,sites(s)['coal'],1);assert production_snapshot(s)==before
    invariants(s);count+=1
    return count


def test_full_campaign():
    """A legal single-city expansion, with no injected money or extra grants."""
    s=starter();call(s,'start');orders=expansion_orders(s);completed=[];draws=s['draws']
    for day in range(1800):
        while orders:
            i,k=orders[0];cost=1 if k=='rail' else COST[k]
            if v(s,'budget')<cost:break
            select(s,i);trigger='can_rail' if k=='rail' else f'can_build_{k}'
            assert check(TR[P+trigger],s),(day,i,k)
            call(s,'rail' if k=='rail' else f'build_{k}');completed.append((day,*orders.pop(0)))
        call(s,'daily')
        if day%300==0:invariants(s)
    invariants(s)
    assert v(s,'elapsed')==1800 and v(s,'days_left')==0 and s['draws']==draws
    assert v(s,'machines')>=500,(v(s,'machines'),v(s,'budget'),orders,completed)
    assert v(s,'score')==100
    print(f'Campaign: {v(s,"machines"):.1f} deliveries, {v(s,"budget"):.1f} investment left; {len(completed)} expansion actions.')
    before=production_snapshot(s);call(s,'daily');assert production_snapshot(s)==before
    return 2


def main():
    started=time.perf_counter()
    total=sum(test() for test in (test_lifecycle,test_geology,test_building_rules,test_network,test_production,test_full_campaign))
    print(f'{total} generated-script scenarios passed in {time.perf_counter()-started:.1f}s.')


if __name__=='__main__':main()
