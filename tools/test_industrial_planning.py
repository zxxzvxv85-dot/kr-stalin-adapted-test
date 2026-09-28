"""Execute shipped construction scripts in a stateful native-economy fixture.

The fixture models economy cache refresh explicitly. It is not the HOI4 engine;
actual resource reservation and rendering still require game verification.
"""
from __future__ import annotations
import copy
import json
import math
import random
import re
from pathlib import Path
from hoi4_politics_blocks import parse
from industrial_planning_economy import PROJECTS, CATEGORIES

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'tools/data/industrial_planning_map.json').read_text(encoding='utf-8'))
FX={n.k:n.v for n in parse((ROOT/'common/scripted_effects/RUS_industrial_planning_effects.txt').read_text(encoding='utf-8'))}
TR={n.k:n.v for n in parse((ROOT/'common/scripted_triggers/RUS_industrial_planning_triggers.txt').read_text(encoding='utf-8'))}


def fixture(unlocked=True):
    ids={c['state'] for c in DATA['cells']}
    all_ids={i for c in DATA['cells'] for i in c['states']}
    return dict(tag='RUS',ai=False,war=False,opening_funds=1000,vars={'RUS_first_five_year_plan_score':37,'political_power':200},flags={'RUS_ip_ui_unlocked'} if unlocked else set(),
                owned=set(ids),controlled=set(ids),connected=set(ids),convoys=20,energy=1,civs=40,steel=100,coal=100,
                applied={'civs':0,'steel':0,'coal':0},modifier=False,extraction_modifier=False,extraction=0,debt_modifier=False,debt_stability=0,debt_construction=0,rewards=[],commands=0,scope=None,
                states={i:dict(infrastructure=2,industrial_complex=2,arms_factory=1,energy_infrastructure=0,
                               naval_base=1,rail_way=1,category='five',slots=20,coal=8,steel=8,state_population_k=4800) for i in all_ids})


def value(s,v):
    try:return float(v)
    except (ValueError,TypeError):pass
    if v in s['vars']:return s['vars'][v]
    native={'num_of_civilian_factories_available_for_projects':s['civs']-s['applied']['civs'],
            'resource@steel':s['steel']*(1+s['extraction'])-s['applied']['steel'],'resource@coal':s['coal']*(1+s['extraction'])-s['applied']['coal'],
            'energy_ratio':s['energy']}
    if v in native:return native[v]
    if re.match(r'^\d+\.',v):
        sid,key=v.split('.',1);d=s['states'][int(sid)]
        result=d[{'infrastructure_level':'infrastructure','industrial_complex_level':'industrial_complex'}.get(key,key.split('@')[-1])]
        return result*(1+s['extraction']) if key.startswith('resource@') else result
    return 0


def compare(a,op,b):return {'=':a==b,'>':a>b,'<':a<b,'>=':a>=b,'<=':a<=b}[op]


def state_id(s,text):
    return int(value(s,text.removeprefix('var:ROOT.'))) if text.startswith('var:ROOT.') else int(text)


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
        if k=='has_war':return s['war']==(v=='yes')
        if k=='has_country_flag':return v in s['flags']
        if k=='has_dynamic_modifier':return s[{'RUS_ip_extraction_bottleneck':'extraction_modifier','RUS_ip_construction_commitment':'modifier','RUS_ip_plan_debt':'debt_modifier'}[n.value('modifier')]]
        if k=='has_state_category':return s['states'][s['scope']]['category']==v
        if k=='owns_state':return state_id(s,v) in s['owned']
        if k=='controls_state':return state_id(s,v) in s['controlled']
        if k=='num_of_convoys':return compare(s['convoys'],n.op,float(v))
        if k=='check_variable':return all(compare(value(s,c.k),c.op,value(s,c.v)) for c in v)
        if k.isdigit():
            prior=s['scope'];s['scope']=int(k);answer=check(v,s);s['scope']=prior;return answer
        if k=='free_building_slots':
            d=s['states'][s['scope']];building=n.value('building');number=float(n.value('size'))
            cap={'infrastructure':5,'energy_infrastructure':1}.get(building,100)
            free=cap-d[building]
            if building in ('industrial_complex','arms_factory','energy_infrastructure'):
                free=min(free,d['slots']-d['industrial_complex']-d['arms_factory']-d['energy_infrastructure'])
            return compare(free,n.one('size').op,number)
        if k=='has_railway_level':return s['states'][int(n.value('state'))]['rail_way']>=int(n.value('level'))
        if k in ('has_railway_connection','can_build_railway'):
            a,b=state_id(s,n.value('start_state')),state_id(s,n.value('target_state'))
            if k=='can_build_railway':return {a,b}<=s['owned']&s['controlled'] and tuple(sorted((a,b))) not in s.get('blocked_paths',set())
            return a==b or {a,b}<=s['connected']
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
            s['vars'][a.k]=result
        elif k=='clamp_variable':s['vars'][n.value('var')]=min(value(s,n.value('max')),max(value(s,n.value('min')),value(s,n.value('var'))))
        elif k=='round_variable':s['vars'][v]=math.floor(value(s,v)+.5)
        elif k=='remove_dynamic_modifier':
            if n.value('modifier')=='RUS_ip_extraction_bottleneck':s['extraction_modifier']=False;s['extraction']=0
            elif n.value('modifier')=='RUS_ip_plan_debt':s['debt_modifier']=False;s['debt_stability']=0;s['debt_construction']=0
            else:s['modifier']=False;s['applied']={r:0 for r in s['applied']}
        elif k=='add_dynamic_modifier':
            if n.value('modifier')=='RUS_ip_extraction_bottleneck':s['extraction_modifier']=True;s['extraction']=value(s,'RUS_ip_resource_penalty')
            elif n.value('modifier')=='RUS_ip_plan_debt':s['debt_modifier']=True;s['debt_stability']=value(s,'RUS_ip_debt_stability');s['debt_construction']=value(s,'RUS_ip_debt_construction')
            else:s['modifier']=True;s['applied']={r:value(s,'RUS_ip_reserved_'+r) for r in s['applied']}
        elif k=='force_update_dynamic_modifier':
            if s['modifier']:s['applied']={r:value(s,'RUS_ip_reserved_'+r) for r in s['applied']}
            if s['extraction_modifier']:s['extraction']=value(s,'RUS_ip_resource_penalty')
            if s['debt_modifier']:s['debt_stability']=value(s,'RUS_ip_debt_stability');s['debt_construction']=value(s,'RUS_ip_debt_construction')
        elif k.isdigit():
            prior=s['scope'];s['scope']=int(k);run(v,s);s['scope']=prior
        elif k=='add_resource':
            r=n.value('type');amount=float(n.value('amount'));s['states'][s['scope']][r]+=amount;s[r]+=amount
            s['rewards'].append((s['scope'],r,amount))
        elif k=='set_state_category':
            d=s['states'][s['scope']];before=d['category']
            d['slots']+=CATEGORIES.index(v)-CATEGORIES.index(before);d['category']=v
            s['rewards'].append((s['scope'],'category',v))
        elif k=='add_building_construction':
            building=n.value('type');amount=float(n.value('level'));s['states'][s['scope']][building]+=amount
            if building=='industrial_complex':s['civs']+=amount
            s['rewards'].append((s['scope'],building,amount))
        elif k=='build_railway':
            a,b=state_id(s,n.value('start_state')),state_id(s,n.value('target_state'));assert {a,b}<=s['owned']&s['controlled']
            level=int(n.value('level'))
            if {a,b}&s['connected']:s['connected'].update((a,b))
            for sid in (a,b):s['states'][sid]['rail_way']=max(level,s['states'][sid]['rail_way'])
            s.setdefault('rail_orders',[]).append((a,b,level));s['rewards'].append((b,'rail',level))
        else:raise AssertionError(('Unsupported effect',k))


def call(s,name):run(FX['RUS_ip_'+name],s)
def v(s,name):return value(s,'RUS_ip_'+name)
def put(s,name,number):s['vars']['RUS_ip_'+name]=number
def select(s,i):put(s,'selected',i);s['flags'].discard('RUS_ip_cancel_armed');call(s,'refresh')
def gui_click(s,name):
    panel=next(n for n in parse((ROOT/'common/scripted_guis/RUS_industrial_planning.txt').read_text(encoding='utf-8'))[0].v if n.k=='RUS_industrial_planning_gui')
    run(panel.one('effects').one(name+'_click').v,s)
def plan_rail(s,start,end,level=2):
    gui_click(s,'ip_rail_choose');put(s,'rail_level',level)
    gui_click(s,f'ip_cell_{start}');gui_click(s,f'ip_cell_{end}')
def supply_fixture(s):
    """Pre-stock older construction-only scenarios; real-start tests stay empty."""
    s['opening_funds']=10000;put(s,'funds',10000)
    for r in ('steel','coal'):
        for c in DATA['cells']:put(s,f'n{c["id"]}_stock_{r}',10)
        put(s,'produced_'+r,10*len(DATA['cells']))
    call(s,'refresh');return s
def started(supplied=True):
    s=fixture();call(s,'open_effect');call(s,'start')
    return supply_fixture(s) if supplied else s
def finish(s,i):
    put(s,f'n{i}_work',v(s,f'n{i}_required')-.01);call(s,'daily')
def invariant(s):
    for r in ('civs','steel','coal'):
        assert v(s,'free_'+r)>=-.0001
        assert abs(v(s,'reserved_'+r)-s['applied'][r])<.0001
        assert abs(v(s,'free_'+r)+v(s,'reserved_'+r)-v(s,'capacity_'+r))<.0001
    assert -.30001<=s['extraction']<=0
    assert s['vars']['RUS_first_five_year_plan_score']==37 and s['vars']['political_power']==200
    assert all(0<=v(s,f'n{c["id"]}_percent')<=100 for c in DATA['cells'])
    imported=exported=0
    for c in DATA['cells']:
        n=f'n{c["id"]}_'
        assert 0<=v(s,n+'development')<=100
        assert v(s,n+'surplus')>=-1e-7 and v(s,n+'spare_freight')>=-1e-7
        assert v(s,n+'power_export')<=max(0,v(s,n+'local_power')-v(s,n+'power_need'))+1e-7,'Re-exported borrowed power'
        imported+=v(s,n+'power_import');exported+=v(s,n+'power_export')
    assert math.isclose(imported,exported,abs_tol=1e-7),'Power created by transport'
    assert math.isfinite(v(s,'funds'))
    assert -.500001<=s['debt_stability']<=0 and -.750001<=s['debt_construction']<=0
    assert math.isclose(v(s,'funds'),s['opening_funds']-v(s,'funds_spent')+v(s,'funds_refunded')+v(s,'funds_settled'),abs_tol=1e-5),'Cash conservation'
    for r in ('steel','coal'):
        stored=sum(v(s,f'n{c["id"]}_{kind}_{r}') for c in DATA['cells'] for kind in ('stock','in','out'))
        assert all(v(s,f'n{c["id"]}_{kind}_{r}')>=-1e-7 for c in DATA['cells'] for kind in ('stock','in','out'))
        assert math.isclose(v(s,'produced_'+r),stored+v(s,'consumed_'+r)+v(s,'lost_'+r),abs_tol=1e-5),('Material conservation',r,v(s,'produced_'+r),stored,v(s,'consumed_'+r),v(s,'lost_'+r))


def regional_tests():
    scenarios=0
    # Seeded native geography differentiates mature and frontier districts.
    q=fixture();frontier=DATA['cells'][16]['state']
    q['states'][frontier].update(state_population_k=90,infrastructure=0,industrial_complex=0,arms_factory=0,rail_way=0)
    call(q,'open_effect');call(q,'start');supply_fixture(q);select(q,16)
    initial=v(q,'n16_development');assert initial<20<v(q,'n5_development')
    call(q,'build_5');assert v(q,'n16_project')==0
    call(q,'build_1');assert v(q,'n16_project')==1
    mine_time=v(q,'n16_eta');assert 0<mine_time<500
    finish(q,16);mine_gain=v(q,'n16_development')-initial
    call(q,'build_1');finish(q,16);assert math.isclose(v(q,'n16_development')-initial,1.5)
    call(q,'build_1');finish(q,16);assert v(q,'n16_development')<20
    before=v(q,'n16_development');call(q,'build_7');finish(q,16)
    assert v(q,'n16_development')-before>mine_gain*5 and v(q,'n16_urban')==1
    assert v(q,'n16_development')>=20
    for _ in range(3):call(q,'refresh');call(q,'open_effect')
    assert v(q,'n16_development')>before and v(q,'n16_urban')==1
    scenarios+=8
    # Paused/cancelled work grants neither development nor trained workers.
    q=started();select(q,5);dev=v(q,'n5_development');workers=v(q,'n5_workers')
    call(q,'build_8');call(q,'pause');call(q,'daily');assert v(q,'n5_development')==dev
    q['flags'].add('RUS_ip_cancel_armed');call(q,'cancel');assert v(q,'n5_workers')==workers
    previous_gain=None
    for _ in range(3):
        before=v(q,'n5_trained');call(q,'build_8');finish(q,5);increment=v(q,'n5_trained')-before
        if previous_gain is not None:assert increment<previous_gain
        previous_gain=increment
    call(q,'build_8');assert v(q,'n5_project')==0 and v(q,'n5_training')==3
    before=copy.deepcopy(q['vars']);call(q,'complete_5_8');assert q['vars']==before
    put(q,'n5_development',99.8);call(q,'build_7');finish(q,5);assert v(q,'n5_development')==100
    scenarios+=7
    # A shared neighbour is finite: two recipients cannot spend its surplus twice.
    q=started();a=5;neighbors=[j for j in DATA['cells'][a]['neighbors'] if j not in (28,31)][:2];assert len(neighbors)==2
    for c in DATA['cells']:
        q['states'][c['state']].update(industrial_complex=0,arms_factory=0,coal=0,steel=0,energy_infrastructure=0,infrastructure=4,rail_way=3)
        put(q,f'n{c["id"]}_development',40)
    q['states'][219]['energy_infrastructure']=1
    # Only the chosen three nodes are permitted to exchange.
    q['controlled']={219,*[DATA['cells'][j]['state'] for j in neighbors]}
    for j in neighbors:
        q['states'][DATA['cells'][j]['state']]['industrial_complex']=6
        select(q,j);call(q,'build_5')
    call(q,'refresh');invariant(q)
    total=sum(v(q,f'n{j}_power_import') for j in neighbors)
    assert total>0 and total<=v(q,'n5_local_power')+1e-7
    recipient=neighbors[0];before=v(q,f'n{recipient}_speed')
    q['controlled'].discard(219);call(q,'refresh')
    assert v(q,f'n{recipient}_power_import')==0 and v(q,f'n{recipient}_running')==0
    scenarios+=3
    # Forecast of an idle site equals the queued speed when no other queue changes.
    for kind in PROJECTS:
        q=started();i=next(c['id'] for c in DATA['cells'] if kind>2 or c['coal' if kind==1 else 'iron'])
        select(q,i)
        if kind==10:plan_rail(q,5 if i!=5 else 3,i)
        forecast=v(q,'rail_days' if kind==10 else f'forecast_{kind}_days');call(q,f'build_{kind}')
        assert math.isclose(forecast,v(q,f'n{i}_eta'),rel_tol=1e-8),(kind,forecast,v(q,f'n{i}_eta'))
        scenarios+=1
    # Placement matters; an electrified resource site outperforms a distant importer.
    q=started();select(q,5);q['states'][219].update(coal=0,steel=0,energy_infrastructure=0);call(q,'refresh')
    remote=v(q,'forecast_5_days')
    q['states'][219].update(coal=30,steel=30,energy_infrastructure=1);call(q,'refresh')
    assert v(q,'forecast_5_days')<remote and v(q,'forecast_5_bottleneck')==0
    # Supporting work remains viable under severe regional shortages.
    for kind in (3,6,7,8,9):
        q=started();select(q,5);q['states'][219].update(state_population_k=0,industrial_complex=12,arms_factory=20,infrastructure=0,slots=60)
        put(q,'n5_development',8);call(q,f'build_{kind}');assert v(q,'n5_speed')>.3
        scenarios+=1
    # Same native output and time budget, different investment order. With
    # constant inputs between completions, summing ceil(remaining / rate) is an
    # exact analytical duration; finish() only exercises each completion guard.
    def sequence_time(sequence):
        s=started();s['controlled']={219};select(s,5);days=0
        for kind in sequence:
            call(s,f'build_{kind}');assert v(s,'n5_project')==kind
            days+=math.ceil(v(s,'n5_eta'));finish(s,5)
        return days,s
    direct,a=sequence_time([5,5,5]);supported,b=sequence_time([3,5,5,5])
    assert a['states'][219]['arms_factory']==b['states'][219]['arms_factory']==4
    assert supported<direct*.75 and supported<1800,(direct,supported)
    # Labour can independently bind: training improves work when power and
    # freight are adequate. The same investment cannot substitute for rails.
    q=started();q['controlled']={219};q['states'][219].update(state_population_k=0,industrial_complex=0,arms_factory=6,
        infrastructure=4,rail_way=5,coal=100,steel=100,energy_infrastructure=1)
    select(q,5);before=v(q,'forecast_5_days');assert v(q,'forecast_5_bottleneck')==1
    call(q,'build_8');finish(q,5);assert v(q,'forecast_5_days')<before*.8
    # Sea transport never invents a cable; state loss cannot keep an old flow.
    q=started();q['states'][DATA['cells'][27]['state']]['energy_infrastructure']=1
    q['states'][DATA['cells'][28]['state']]['industrial_complex']=8
    call(q,'refresh');assert v(q,'edge_27_28_live')==1 and v(q,'edge_27_28_flow')==0
    q['controlled'].discard(DATA['cells'][27]['state']);call(q,'refresh');assert v(q,'edge_27_28_live')==0
    return scenarios+5


def gui_tests():
    """Check page isolation and native-tooltip binding, not screenshots."""
    def field(node,key):
        item=node.one(key)
        return item.v.strip('"') if item else ''
    roots=parse((ROOT/'interface/RUS_industrial_planning.gui').read_text(encoding='utf-8'))[0]
    window=next(n for n in roots.v if field(n,'name')=='RUS_industrial_planning_window')
    def elements(node):
        for child in node.v:
            if not isinstance(child.v,list):continue
            if child.one('name'):yield child
            if child.k=='containerWindowType':yield from elements(child)
    widgets={field(n,'name'):n for n in elements(window)}
    panel=next(n for n in parse((ROOT/'common/scripted_guis/RUS_industrial_planning.txt').read_text(encoding='utf-8'))[0].v if n.k=='RUS_industrial_planning_gui')
    triggers=panel.one('triggers');effects=panel.one('effects')
    cards={name:n for name,n in widgets.items() if name.startswith(('ip_metric_bg_','ip_supply_bg_'))}
    assert len(cards)==8 and all(n.k=='iconType' for n in cards.values()),'Child-window backgrounds do not follow page visibility in-game'
    assert all(n.k!='containerWindowType' or triggers.one(name+'_visible') is None for name,n in widgets.items())
    s=started();count=0
    for action,page in [(None,'board'),('toggle_supply','supply'),('toggle_supply','board'),('toggle_help','help'),('toggle_help','board')]:
        if action:call(s,action)
        shown={name for name in cards if check(triggers.one(name+'_visible').v,s)}
        expected={name for name in cards if name.startswith('ip_metric_bg_' if page=='board' else 'ip_supply_bg_')} if page!='help' else set()
        assert shown==expected,(page,shown)
        assert check(triggers.one('ip_map_visible').v,s)==(page=='board')
        count+=1
    viewport=widgets['ip_map_viewport'];map_icon=widgets['ip_map']
    assert field(viewport,'clipping')=='yes' and viewport.one('background') is None
    assert 'ip_map_northern_limit' not in widgets
    assert int(field(map_icon.one('position'),'y'))==-round(DATA['northern_map_limit_y']*1.25)
    count+=1
    for lang in ('simp_chinese','english','russian'):
        text=(ROOT/f'localisation/{lang}/RUS_industrial_planning_l_{lang}.yml').read_text(encoding='utf-8-sig')
        loc=dict(re.findall(r'^ (\w+):\d* "(.*)"$',text,re.M))
        for kind in PROJECTS:
            name=f'ip_build_{kind}';tooltip=field(widgets[name],'pdx_tooltip')
            assert loc[tooltip]==f'[!{name}_click]',(name,tooltip)
            effect=effects.one(name+'_click')
            assert all(n.v!=tooltip for n in effect.v if n.k=='custom_effect_tooltip'),'Recursive tooltip'
            assert (effect.one('effect_tooltip') is not None)==(kind<=6 or kind in (9,10))
            for prefix in (() if kind==10 else ('ip_build_icon_',) if kind==9 else ('ip_build_icon_','ip_build_label_','ip_build_estimate_','ip_build_cost_')):
                assert field(widgets[prefix+str(kind)],'alwaystransparent')=='yes'
        assert loc['RUS_ip_funds_hover']=='[!ip_funds_icon_click]'
        assert field(widgets['ip_funds'],'pdx_tooltip')=='RUS_ip_funds_hover'
        assert field(widgets['ip_build_9'],'buttonText')=='RUS_ip_build_9'
        count+=1
    for kind in PROJECTS:
        q=started();select(q,5);before=copy.deepcopy(q['states']);reward_count=len(q['rewards'])
        if kind==10:plan_rail(q,3,5)
        run(effects.one(f'ip_build_{kind}_click').v,q)
        assert v(q,'n5_project')==kind,(kind,'Button did not queue project')
        assert q['states']==before and len(q['rewards'])==reward_count,'Hover/click must not award completed assets'
        assert v(q,'completed')==0
        count+=1
    return count


def expansion_tests():
    count=0
    # Upgrade the actual central state by exactly one level. Fully occupied
    # building slots do not block expansion; neighbours must remain unchanged.
    for before,after in zip(CATEGORIES,CATEGORIES[1:]):
        q=started();select(q,5);d=q['states'][219]
        d.update(category=before,slots=3);call(q,'refresh')
        others={sid:copy.deepcopy(st) for sid,st in q['states'].items() if sid!=219}
        cash=v(q,'funds');cost=v(q,'forecast_9_cost');call(q,'build_9')
        assert v(q,'n5_project')==9 and v(q,'reserved_civs')==3
        assert math.isclose(cash-v(q,'funds'),cost) and d['category']==before
        finish(q,5)
        assert d['category']==after and d['slots']==4 and v(q,'reserved_civs')==0
        assert v(q,'consumed_steel')>0 and v(q,'consumed_coal')>0
        assert others=={sid:st for sid,st in q['states'].items() if sid!=219}
        rewards=copy.deepcopy(q['rewards']);call(q,'complete_5_9');call(q,'refresh')
        assert q['rewards']==rewards;invariant(q);count+=1
    for category in ('twelve','wasteland','major_port','port','minor_port','one_island','zero_island'):
        q=started();select(q,5);q['states'][219]['category']=category;call(q,'build_9')
        assert v(q,'n5_project')==0 and not q['rewards'];count+=1
    # External changes do not downgrade a state or silently grant bonus slots.
    q=started();select(q,5);call(q,'build_9');paid=v(q,'n5_paid')
    q['states'][219]['category']='twelve';call(q,'daily')
    assert v(q,'n5_work')==0 and v(q,'reserved_civs')==0
    q['flags'].add('RUS_ip_cancel_armed');call(q,'cancel')
    assert math.isclose(v(q,'funds_refunded'),paid*.75) and not q['rewards'];count+=1
    q=started();select(q,5);call(q,'build_9');q['states'][219]['category']='eight';finish(q,5)
    assert q['states'][219]['category']=='nine';count+=1
    # With no warehouse stock expansion waits rather than creating capacity.
    q=started(False);q['steel']=q['coal']=0;select(q,5);call(q,'build_9');call(q,'daily')
    assert v(q,'n5_work')==0 and q['states'][219]['category']=='five';count+=1
    return count


def tests():
    # The new testing decision is required; simply loading Russia exposes no GUI.
    gate=fixture(False);call(gate,'open_effect');call(gate,'start')
    assert 'RUS_ip_open' not in gate['flags'] and 'RUS_ip_active' not in gate['flags']
    call(gate,'enable_gui');assert 'RUS_ip_open' in gate['flags'] and 'RUS_ip_ui_unlocked' in gate['flags']
    assert 'RUS_ip_active' not in gate['flags'] and not gate['extraction_modifier'] and not gate['modifier']
    scenarios=0;s=fixture();call(s,'open_effect')
    assert not s['rewards'] and not s['modifier'];assert v(s,'days_left')==1800
    call(s,'build_5');assert v(s,'queued')==0
    call(s,'daily');assert v(s,'days_left')==1800
    call(s,'start');call(s,'start');assert v(s,'days_left')==1800
    assert s['extraction_modifier'] and s['extraction']==-.30 and v(s,'free_coal')==70
    scenarios+=4
    for tag,ai in [('FRA',False),('RUS',True)]:
        other=fixture();other['tag']=tag;other['ai']=ai;call(other,'open_effect');call(other,'start')
        assert 'RUS_ip_economy_initialized' not in other['flags'];assert not other['rewards'];scenarios+=1
    for kind in PROJECTS:
        for failure in ['none','civs','funds','control','owned','slots','closed','inactive','occupied']:
            if kind==10 and failure=='slots':continue  # Railway uses no shared building slot.
            q=started();i=next(c['id'] for c in DATA['cells'] if kind>2 or c['coal' if kind==1 else 'iron'])
            select(q,i);sid=DATA['cells'][i]['state']
            if kind==10:plan_rail(q,5 if i!=5 else 3,i)
            if failure=='civs':put(q,'capacity_civs',0)
            if failure=='funds':put(q,'funds',0);q['opening_funds']=0
            if failure=='control':q['controlled'].discard(sid)
            if failure=='owned':q['owned'].discard(sid)
            if failure=='slots':
                q['states'][sid].update(slots=0,infrastructure=5,energy_infrastructure=1,category='twelve');put(q,f'n{i}_mine_{kind}',3)
                put(q,f'n{i}_urban',3);put(q,f'n{i}_training',3)
            if failure=='closed':call(q,'close_effect')
            if failure=='inactive':q['flags'].discard('RUS_ip_active')
            if failure=='occupied':put(q,f'n{i}_project',3);put(q,f'n{i}_required',180)
            call(q,f'build_{kind}')
            if failure=='none':
                assert v(q,f'n{i}_project')==kind,(kind,failure)
                assert not q['rewards'];old=v(q,f'n{i}_required');call(q,'refresh');assert v(q,f'n{i}_work')==0
                finish(q,i);assert v(q,'completed')==1 and (q['rewards'] or kind in (7,8))
                rewards=copy.deepcopy(q['rewards']);call(q,'daily');call(q,'refresh');call(q,f'complete_{i}_{kind}')
                assert q['rewards']==rewards,'Duplicate completion';assert v(q,f'n{i}_project')==0
            elif failure!='occupied':assert v(q,f'n{i}_project')==0,(kind,failure)
            invariant(q);scenarios+=1
    # Insufficient deposits never allow mining. Three paid completions are final.
    for kind,potential in [(1,'coal'),(2,'iron')]:
        q=started();i=next(c['id'] for c in DATA['cells'] if not c[potential]);select(q,i);call(q,f'build_{kind}');assert v(q,'queued')==0
        i=next(c['id'] for c in DATA['cells'] if c[potential]);select(q,i)
        for _ in range(3):call(q,f'build_{kind}');finish(q,i)
        before=len(q['rewards']);call(q,f'build_{kind}');assert v(q,f'n{i}_project')==0 and len(q['rewards'])==before;scenarios+=2
    # A rapid burst of clicks must not reuse stale native available resources.
    q=started();put(q,'capacity_civs',5)
    select(q,0);call(q,'build_5');select(q,1);call(q,'build_5')
    assert v(q,'queued')==1 and v(q,'reserved_civs')==5 and v(q,'free_civs')==0;scenarios+=1
    # Pauses release all commitments, retain work, and cannot be used as a refund.
    q=started();select(q,5);call(q,'build_5');call(q,'daily');progress=v(q,'n5_work')
    call(q,'pause');assert v(q,'reserved_civs')==0;call(q,'daily');assert v(q,'n5_work')==progress
    call(q,'pause');call(q,'daily');assert v(q,'n5_work')>progress
    call(q,'cancel');assert v(q,'n5_project')==5
    q['flags'].add('RUS_ip_cancel_armed');call(q,'cancel');assert v(q,'queued')==0 and v(q,'reserved_civs')==0 and not q['rewards'];scenarios+=4
    # Ownership / slot loss / severed rail pause existing work and release it.
    for reason in ['territory','slots','rail','civs']:
        q=started();select(q,5);call(q,'build_4');call(q,'daily');progress=v(q,'n5_work');sid=219
        if reason=='territory':q['controlled'].discard(sid)
        if reason=='slots':q['states'][sid]['slots']=3
        if reason=='rail':q['controlled'].discard(219) # losing the Moscow hub breaks all industrial connections
        if reason in ('civs','steel','coal'):q[reason]=0
        call(q,'daily');assert v(q,'n5_work')==progress and v(q,'reserved_civs')==0,reason
        invariant(q);scenarios+=1
    # Local factors increase speed; power and freight shortages reduce it.
    q=started();select(q,5);call(q,'build_5');slow=v(q,'n5_speed')
    q['states'][219]['infrastructure']=4;call(q,'refresh');assert v(q,'n5_speed')>slow
    fast=v(q,'n5_speed');q['energy']=.2;call(q,'refresh');assert 0<v(q,'n5_speed')<fast;scenarios+=2
    q=started();select(q,16);q['connected'].discard(DATA['cells'][16]['state']);q['states'][DATA['cells'][16]['state']]['infrastructure']=0
    call(q,'build_1');assert 0<v(q,'n16_speed')<1;scenarios+=1
    # Railway origin is fixed at start: another neighbor cannot silently replace it.
    q=started();i=16;select(q,i);call(q,'build_6');anchor=int(v(q,'n16_anchor'))-1
    assert anchor>=0;q['controlled'].discard(DATA['cells'][anchor]['state']);call(q,'daily');assert v(q,'n16_work')==0;scenarios+=1
    # Maritime connections use existing ports and actual convoy availability.
    q=started();q['connected'].discard(DATA['cells'][28]['state']);call(q,'refresh');assert v(q,'n28_connected')==1
    q['convoys']=9;call(q,'refresh');assert v(q,'n28_connected')==0;scenarios+=2
    # No click, save reload, opening or help page may advance time / grant assets.
    q=started();select(q,5);call(q,'build_5');call(q,'daily');before=(v(q,'days_left'),v(q,'n5_work'))
    for _ in range(5):call(q,'refresh');call(q,'toggle_help');call(q,'close_effect');call(q,'open_effect')
    assert before==(v(q,'days_left'),v(q,'n5_work')) and not q['rewards']
    restored=copy.deepcopy(q);call(restored,'refresh');assert v(restored,'n5_work')==v(q,'n5_work')
    # Player switching away cannot strand reservations, but AI cannot queue work.
    q['ai']=True;call(q,'daily');assert v(q,'n5_work')>before[1];scenarios+=3
    # Last-day completion is awarded once, then all remaining queues are released.
    q=started();select(q,5);call(q,'build_5');select(q,2);call(q,'build_4');put(q,'n5_work',299.99);put(q,'days_left',1)
    call(q,'daily');assert v(q,'completed')==1 and v(q,'days_left')==0 and v(q,'queued')==0 and not q['modifier']
    before=copy.deepcopy(q['rewards']);call(q,'daily');call(q,'start');assert q['rewards']==before and v(q,'days_left')==0;scenarios+=2
    assert not q['extraction_modifier'] and s['extraction']<0
    # Mining repairs two percentage points once, never from queueing/refresh/cancel.
    q=started();coal_sites=[c['id'] for c in DATA['cells'] if c['coal']]
    assert len(coal_sites)>=5
    for number in range(15):
        i=coal_sites[number//3];select(q,i);call(q,'build_1')
        before=q['extraction'];call(q,'refresh');assert q['extraction']==before
        finish(q,i);assert math.isclose(q['extraction'],min(0,-.3+.02*(number+1)),abs_tol=1e-8)
        assert v(q,'mining_completed')==number+1;scenarios+=1
    assert not q['extraction_modifier']
    i=next(c['id'] for c in DATA['cells'] if c['iron']);select(q,i);call(q,'build_2');finish(q,i)
    assert v(q,'mining_completed')==15 and q['extraction']==0
    before=q['extraction'];call(q,'close_effect');call(q,'open_effect');call(q,'refresh');assert q['extraction']==before;scenarios+=2
    # Seeded interaction sequences cover allocator conservation and negative pools.
    rng=random.Random(219);q=started()
    for _ in range(140):
        select(q,rng.randrange(36));kind=rng.randrange(1,len(PROJECTS)+1);call(q,f'build_{kind}')
        if rng.random()<.3:call(q,'pause')
        if rng.random()<.2:q['flags'].add('RUS_ip_cancel_armed');call(q,'cancel')
        if rng.random()<.5:call(q,'daily')
        invariant(q);scenarios+=1
    # Geometry and localisation are checked independently of simulation outcomes.
    assert DATA['width']==1168 and DATA['marker_width']==26
    members=[sid for c in DATA['cells'] for sid in c['states']];assert len(members)==len(set(members))==104
    for i,a in enumerate(DATA['cells']):
        for b in DATA['cells'][i+1:]:assert abs(a['x']-b['x'])>=26 or abs(a['y']-b['y'])>=26
        for j in a['neighbors']:assert i in DATA['cells'][j]['neighbors']
    for lang in ('simp_chinese','english','russian'):
        p=ROOT/f'localisation/{lang}/RUS_industrial_planning_l_{lang}.yml';assert p.read_bytes().startswith(b'\xef\xbb\xbf')
        text=p.read_text(encoding='utf-8-sig');keys=re.findall(r'^ (\w+):',text,re.M);assert len(keys)==len(set(keys))
        assert '$STATE_' not in text and all(f'[{c["state"]}.GetName]' in text for c in DATA['cells'])
    all_runtime='\n'.join(p.read_text(encoding='utf-8-sig') for folder in ('common','interface','localisation') for p in (ROOT/folder).rglob('*industrial_planning*') if p.is_file())
    assert not re.search(r'RUS_first_five_year_plan_|RUS_stalin_first_five_year_plan_|activate_mission|add_political_power',all_runtime)
    assert not re.search(r'RUS_ip_(?:round|budget|settle|machines|score)\b',all_runtime)
    assert 'effect_tooltip' in all_runtime and 'country_resource_cost_coal = RUS_ip_reserved_coal' in all_runtime
    assert 'local_resources_factor = RUS_ip_resource_penalty' in all_runtime
    decision=(ROOT/'common/decisions/RUS_industrial_planning_decisions.txt').read_text(encoding='utf-8')
    assert 'fire_only_once = yes' in decision and 'cost = 0' in decision and 'RUS_ip_enable_gui = yes' in decision
    gui=parse((ROOT/'common/scripted_guis/RUS_industrial_planning.txt').read_text(encoding='utf-8'))[0]
    panel=next(n for n in gui.v if n.k=='RUS_industrial_planning_gui')
    q=started();select(q,5);before=len(q['rewards']);run(panel.one('effects').one('ip_build_5_click').v,q)
    assert len(q['rewards'])==before and v(q,'n5_project')==5,'Tooltip must not award buildings on click'
    def walk(nodes):
        for n in nodes:
            if isinstance(n.v,list):yield from walk(n.v)
            elif n.k.startswith('RUS_ip_') and n.v in ('yes','no'):yield n.k
    for folder in ('common/scripted_effects','common/scripted_triggers','common/scripted_guis','common/on_actions'):
        for p in (ROOT/folder).glob('*industrial_planning*'):
            assert set(walk(parse(p.read_text(encoding='utf-8')))) <= FX.keys() | TR.keys(),p
    scenarios+=regional_tests()
    scenarios+=expansion_tests()
    from test_industrial_planning_rail import rail_tests
    scenarios+=rail_tests()
    from test_industrial_planning_supply import supply_tests
    scenarios+=supply_tests()
    scenarios+=gui_tests()
    print(f'PASS: {scenarios} construction / finance / freight scenarios; aggregation, cash and material conservation, finite capacities, forecasts, daily progress, one-time completion, deadline and old-plan isolation. Not an HOI4 runtime test.')


if __name__=='__main__':tests()
