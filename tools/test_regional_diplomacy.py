"""Interpret shipped regional scripts in a deterministic fixture, not the HOI4 engine.
Tests cover transactions, timed settlement, cancellation, isolation and fort scope.
"""
from pathlib import Path
import re, copy
ROOT=Path(__file__).resolve().parents[1]
def parse(text):
    tokens=re.findall(r'#[^\n]*|"(?:\\.|[^"\\])*"|[{}]|[<>!=]=?|[^\s{}=<>!#]+',text)
    tokens=[t for t in tokens if not t.startswith('#')];i=0
    def block(nested=False):
        nonlocal i
        nodes=[]
        while i<len(tokens) and tokens[i]!='}':
            k=tokens[i];i+=1
            assert tokens[i] in ['=','>','<','>=','<='],(k,tokens[i]);op=tokens[i];i+=1
            v=tokens[i];i+=1
            if v=='{':v=block(True)
            nodes.append((k,op,v))
        if nested:assert tokens[i]=='}';i+=1
        return nodes
    result=block();assert i==len(tokens);return result

def read(p):return parse((ROOT/p).read_text(encoding='utf-8-sig'))

def get(b,k,default=None):return next((v for x,_,v in b if x==k),default)

def country(tag):return dict(tag=tag,exists=True,cap=False,socialist=tag=='RUS',ai=False,subject=False,faction='GER' if tag!='RUS' else 'RUS',war=set(),focus=set(),flags={},vars={},ideas={},decisions={},pp=1000,equipment=10000,stability=.8,balance=0,events=[])

def val(x,c):
    try:return float(x)
    except ValueError:return c['vars'].get(x,0)

def compare(a,op,b):return {'=':lambda:a==b,'>':lambda:a>b,'<':lambda:a<b,'>=':lambda:a>=b,'<=':lambda:a<=b}[op]()

def check(b,c,w):
    def one(k,op,v):
        if k in w:return check(v,w[k],w)
        if k in TR:return check(TR[k],c,w)==(v=='yes')
        if k=='custom_trigger_tooltip':return check([n for n in v if n[0]!='tooltip'],c,w)
        if k in ['AND','hidden_trigger']:return check(v,c,w)
        if k=='NOT':return not check(v,c,w)
        if k=='OR':return any(one(*n) for n in v)
        if k=='always':return v=='yes'
        if k=='has_power_balance':return c.get('bop',False)
        if k=='has_idea':return v in c['ideas']
        if k=='controls_province':return w['_provinces'][int(val(v,c))]['controller']==c['tag']
        if k=='has_template':return v in c.get('templates',{})
        if k=='has_variable':return v in c['vars']
        if k=='any_owned_state':return any(check(v,s,w) for s in c.get('states',[]) if s['owner']==c['tag'])
        if k=='any_controlled_state':return any(check(v,s,w) for s in c.get('states',[]) if s['controller']==c['tag'])
        if k=='any_neighbor_state':return any(check(v,s,w) for s in c.get('neighbors',[]))
        if k=='is_controlled_by':return c['controller']==('RUS' if v=='ROOT' else v)
        if k=='impassable':return c.get('impassable',False)==(v=='yes')
        if k=='original_tag':return c['tag']==v
        if k in ['is_ai','exists','has_capitulated','is_subject','has_socialist_government']:
            return c[{'is_ai':'ai','exists':'exists','has_capitulated':'cap','is_subject':'subject','has_socialist_government':'socialist'}[k]]==(v=='yes')
        if k in ['has_country_flag','has_state_flag']:return v in c['flags']
        if k in ['rail_way','infrastructure']:return compare(c['buildings'].get(k,0),op,float(v))
        if k=='has_completed_focus':return v in c['focus']
        if k=='has_active_mission':return v in c.get('missions',set())
        if k=='has_war_with':return v in c['war']
        if k=='is_in_faction_with':return c['faction']==w[v]['faction'] and bool(c['faction'])
        if k=='has_political_power':return compare(c['pp'],op,float(v))
        if k=='check_variable':return all(compare(val(a,c),o,val(z,c)) for a,o,z in v)
        if k=='has_equipment':return all(compare(c['equipment'][a],o,float(z)) for a,o,z in v)
        raise AssertionError(('Unsupported trigger',k))
    return all(one(*n) for n in b)

def run(b,c,w,choice=0):
    matched=False
    for k,op,v in b:
        if k in ['if','else_if','else']:
            if k=='if':matched=False
            if not matched and (k=='else' or check(get(v,'limit',[]),c,w)):
                run([n for n in v if n[0]!='limit'],c,w,choice);matched=True
            continue
        matched=False
        if k in w:run(v,w[k],w,choice)
        elif k in FX:run(FX[k],c,w,choice)
        elif k=='random_controlled_state':
            states=[s for s in c.get('states',[]) if s['controller']==c['tag'] and check(get(v,'limit',[]),s,w)]
            if states:run([n for n in v if n[0]!='limit'],states[choice%len(states)],w,choice)
        elif k in ['random_owned_controlled_state','every_owned_state']:
            states=[st for st in c.get('states',[]) if st['owner']==c['tag'] and (k=='every_owned_state' or st['controller']==c['tag']) and check(get(v,'limit',[]),st,w)]
            if k=='random_owned_controlled_state':states=[states[choice%len(states)]] if states else []
            for st in states:run([n for n in v if n[0]!='limit'],st,w,choice)
        elif k=='set_state_flag':c['flags'][v]=None
        elif k=='clr_state_flag':c['flags'].pop(v,None)
        elif k=='damage_building':
            p=w['_provinces'][int(val(get(v,'province').removeprefix('var:'),c))]
            kind=get(v,'type');level=p['buildings'].get(kind,0)
            p['damage'][kind]=min(level,p['damage'].get(kind,0)+float(get(v,'damage')))
        elif k=='for_loop_effect':
            assert get(v,'end')=='global.province_controllers^num'
            for i in range(int(get(v,'start')),len(w['_provinces'])):
                c['vars'][get(v,'value')]=i
                run([n for n in v if n[0] not in ['start','end','value']],c,w,choice)
        elif k=='set_power_balance':c['bop']=True
        elif k=='division_template':c.setdefault('templates',{})[get(v,'name')]=v
        elif k=='create_unit':
            assert (get(v,'owner')=='PREV' and c['controller']=='RUS' and get(v,'allow_spawning_on_enemy_provs')=='no') or (get(v,'owner')=='ROOT' and c['controller'] in w['RUS']['war'] and get(v,'allow_spawning_on_enemy_provs')=='yes')
            w['RUS'].setdefault('units',[]).append(c['id'])
        elif k=='army_experience':c['xp']=c.get('xp',0)+float(v)
        elif k=='hidden_effect':run(v,c,w,choice)
        elif k=='custom_effect_tooltip':pass
        elif k=='effect_tooltip':pass # Presentation-only: must never grant resources.
        elif k=='set_country_flag':
            if isinstance(v,list):c['flags'][get(v,'flag')]=int(get(v,'days'))
            else:c['flags'][v]=None
        elif k=='clr_country_flag':c['flags'].pop(v,None)
        elif k in ['set_variable','set_temp_variable','add_to_variable','subtract_from_variable']:
            a,_,z=v[0];z=val(z,c);current=c['vars'].get(a,0)
            c['vars'][a]=z if k in ['set_variable','set_temp_variable'] else current+z*(1 if k=='add_to_variable' else -1)
        elif k=='clamp_variable':
            a=get(v,'var');c['vars'][a]=max(float(get(v,'min')),min(float(get(v,'max')),c['vars'].get(a,0)))
        elif k=='add_political_power':c['pp']+=float(v)
        elif k=='add_equipment_to_stockpile':c['equipment'][get(v,'type')]+=float(get(v,'amount'))
        elif k=='add_ideas':c['ideas'][v]=None
        elif k=='remove_ideas':c['ideas'].pop(v,None)
        elif k=='add_timed_idea':c['ideas'][get(v,'idea')]=int(get(v,'days'))
        elif k=='add_stability':c['stability']+=float(v)
        elif k=='add_power_balance_value':c['balance']+=float(get(v,'value'))
        elif k=='country_event':c['events'].append(get(v,'id'))
        elif k=='random_list':
            options=[]
            for weight,_,body in v:
                mod=get(body,'modifier',[])
                if mod and check([n for n in mod if n[0]!='factor'],c,w) and get(mod,'factor')=='0':continue
                options.append([n for n in body if n[0]!='modifier'])
            assert options;run(options[choice%len(options)],c,w,choice)
        else:raise AssertionError(('Unsupported effect',k))
FX={k:v for k,_,v in read('common/scripted_effects/RUS_regional_diplomacy_effects.txt')}
FX.update((k,v) for k,_,v in read('common/scripted_effects/RUS_regional_militia_effects.txt'))
FX.update((k,v) for k,_,v in read('common/scripted_effects/RUS_diplomacy_cost_effects.txt'))
TR={k:v for k,_,v in read('common/scripted_triggers/RUS_regional_diplomacy_triggers.txt')}
TR.update((k,v) for k,_,v in read('common/scripted_triggers/RUS_diplomacy_cost_triggers.txt'))
D={k:v for k,_,v in get(read('common/decisions/RUS_regional_diplomacy_decisions.txt'),'RUS_Spreading_the_Revolution_decisions')}
TAGS=['BAT','LIT','GEO','AZR','BLR','POL']
def world():
    w={t:country(t) for t in ['RUS','GER']+TAGS}
    for c in w.values():c['equipment']={'infantry_equipment':10000,'support_equipment':10000}
    c=w['RUS'];c['focus']={f'RUS_future_foreign_{n}' for n in ['020','021','022','036']};c['war']=set(TAGS)
    c['states']=[dict(id=t,owner='RUS',controller='RUS',neighbors=[dict(controller=t)]) for t in TAGS]
    for t in TAGS:w[t]['states']=[dict(id=t+'_enemy',owner=t,controller=t,neighbors=[dict(controller='RUS')])]
    w['_provinces']=[dict(controller=t,buildings={'bunker':level,'coastal_bunker':level,'rail_way':4},damage={}) for t,level in [('GER',0),('BLR',10),('BLR',3),('POL',7),('BLR',1)]]
    for t in TAGS:run(FX[f'RUS_rd_{t}_init'],c,w)
    return w
def start(id,w):
    c=w['RUS'];d=D[id]
    assert all(check(get(d,k,[]),c,w) for k in ['visible','available','custom_cost_trigger']),id
    run(get(d,'complete_effect'),c,w);c['decisions'][id]=int(get(d,'days_remove'))
def tick(w,days=1,choice=0):
    for _ in range(days):
        for c in (w[t] for t in ['RUS','GER']+TAGS):
            for field in ['flags','ideas']:
                for k,d in list(c[field].items()):
                    if d is not None:
                        if d<=1:del c[field][k]
                        else:c[field][k]=d-1
        c=w['RUS'];run(FX['RUS_rd_daily_tick'],c,w)
        for id,left in list(c['decisions'].items()):
            d=D[id]
            if check(get(d,'cancel_trigger'),c,w):
                run(get(d,'cancel_effect'),c,w,choice)
                run(get(d,'remove_effect'),c,w,choice)
                del c['decisions'][id]
            elif left<=1:
                run(get(d,'remove_effect'),c,w,choice);del c['decisions'][id]
            else:c['decisions'][id]=left-1
def ready(id,w):
    c=w['RUS'];t=id.split('_')[2];c['vars'][f'RUS_rd_{t}_stock']=2 if t in TAGS[:4] else 70
    if id.endswith('_fast'):c['flags']['RUS_rd_BLR_couriers_ready']=90
def snap(w):return copy.deepcopy(w)

actions=[k for k,v in D.items() if get(v,'complete_effect')]
assert len(actions)==19 and len(D)==25
for id in actions:
    t=id.split('_')[2];resource=f'RUS_rd_{t}_stock';cap=3 if t in TAGS[:4] else 100
    for discounted in [False,True]:
        w=world();ready(id,w);c=w['RUS'];d=D[id]
        if discounted:c['flags']['RUS_diplomacy_pp_discount']=None
        source=FX[id+'_start'];pay=next(int(k.rsplit('_',1)[1]) for k,_,_ in source if k.startswith('RUS_diplomacy_pay_'))*(.8 if discounted else 1)
        c['pp']=pay-.01;assert not check(get(d,'custom_cost_trigger'),c,w)
        c['pp']=pay;assert check(get(d,'custom_cost_trigger'),c,w)
        before=c['vars'][resource];start(id,w)
        assert abs(c['pp'])<1e-8 and c['balance']==.005
        assert c['vars'][resource]<=before and not w[t]['ideas']
        assert not check(get(d,'available'),c,w)
        tick(w,int(get(d,'days_remove'))-1)
        assert id in c['decisions'] and not w[t]['ideas']
        tick(w);assert id not in c['decisions'] and 0<=c['vars'][resource]<=cap
        assert c['balance']==.005 and c['vars'][f'RUS_rd_{t}_remaining']==0
        saved=snap(w);run(get(d,'remove_effect'),c,w);assert w==saved,'double settlement '+id
    # Cancellation and a later engine remove callback cannot grant a reward/refund.
    for invalid in ['cap','socialist','exists','faction']+(['peace'] if get(D[id],'days_remove') and 'has_war_with' in str(D[id]) else []):
        w=world();ready(id,w);c=w['RUS'];start(id,w)
        if invalid=='peace':c['war'].clear()
        else:w[t][invalid]={'cap':True,'socialist':True,'exists':False,'faction':'OTHER'}[invalid]
        pp=c['pp'];stock=c['vars'][resource];equipment=copy.deepcopy(c['equipment']);tick(w)
        assert id not in c['decisions'] and not w[t]['ideas'] and not c.get('units')
        assert c['pp']==pp and c['equipment']==equipment and c['vars'][resource]==stock
        assert c['balance']==.005 and all(not p['damage'] for p in w['_provinces'])
    # Force the exposure branch for actions with risk.
    if 'random_list' in str(FX[id+'_finish']):
        w=world();ready(id,w);c=w['RUS'];start(id,w);stock=c['vars'][resource]
        tick(w,int(get(D[id],'days_remove')),choice=1)
        assert c['flags'][f'RUS_rd_{t}_lock']==60 and not w[t]['ideas'] and not c.get('units')
        assert c['vars'][resource]==max(0,stock-(1 if cap==3 else 10))
        assert all(not p['damage'] for p in w['_provinces'])
        tick(w,60);assert f'RUS_rd_{t}_lock' not in c['flags'] and c['vars'][f'RUS_rd_{t}_lock_days']==0

# Country isolation, stock generation/caps and idempotent initialization.
w=world();c=w['RUS']
for id in ['RUS_rd_BAT_press','RUS_rd_LIT_press','RUS_rd_GEO_stations','RUS_rd_AZR_stations','RUS_rd_BLR_supplies','RUS_rd_POL_contact']:start(id,w)
tick(w,21)
assert [c['vars'][f'RUS_rd_{t}_stock'] for t in TAGS]==[1,1,1,1,25,35]
assert abs(c['balance']-.03)<1e-9
for t in TAGS:
    stock=c['vars'][f'RUS_rd_{t}_stock'];run(FX[f'RUS_rd_{t}_init'],c,w);assert c['vars'][f'RUS_rd_{t}_stock']==stock
for id in ['RUS_rd_BAT_press','RUS_rd_BLR_supplies','RUS_rd_POL_training']:
    w=world();c=w['RUS'];t=id.split('_')[2];cap=3 if t=='BAT' else 100
    c['vars'][f'RUS_rd_{t}_stock']=cap-1;start(id,w);tick(w,30)
    assert c['vars'][f'RUS_rd_{t}_stock']==cap

# Both raid variants hit every Belarus-controlled province, preserve foreign forts
# and leave non-fort infrastructure unchanged. Courier advantage is consumed once.
for id in ['RUS_rd_BLR_raids','RUS_rd_BLR_raids_fast']:
    w=world();ready(id,w);c=w['RUS'];start(id,w)
    assert 'RUS_rd_BLR_couriers_ready' not in c['flags']
    assert check(get(D[id],'visible'),c,w)
    tick(w,int(get(D[id],'days_remove')))
    for p in w['_provinces']:
        if p['controller']=='BLR':assert p['damage']=={k:p['buildings'][k] for k in ['bunker','coastal_bunker']}
        else:assert not p['damage']
        assert p['buildings']['rail_way']==4
    assert c['flags']['RUS_rd_BLR_raids_cooldown']==90

# Militia only appear on eligible Russian border states; cap is lifetime and
# separate per target. No common border cannot consume a spawn allowance.
for t,a in [('GEO','militias'),('AZR','militias'),('BLR','supplies'),('POL','training')]:
    id=f'RUS_rd_{t}_{a}';w=world();ready(id,w);c=w['RUS'];start(id,w);tick(w,30)
    assert c['units']==[t+'_enemy'] and c['vars'][f'RUS_rd_{t}_militia_raised']==1
    fx=FX[f'RUS_rd_{t}_form_militia']
    run(fx,c,w);run(fx,c,w);assert c['units']==[t+'_enemy',t+'_enemy']
    assert c['vars'][f'RUS_rd_{t}_militia_raised']==2
    template=next(iter(c['templates'].values()))
    assert len(get(template,'regiments'))==4 and all(k=='militia' for k,_,_ in get(template,'regiments'))
    for mode in ['no_border','enemy_controlled','impassable']:
        w=world();c=w['RUS'];c['war'].clear()
        for s in c['states']:
            if mode=='no_border':s['neighbors']=[]
            elif mode=='enemy_controlled':s['controller']='GER'
            else:s['impassable']=True
        run(fx,c,w);assert not c.get('units') and c['vars'].get(f'RUS_rd_{t}_militia_raised',0)==0
    w=world();c=w['RUS'];c['war'].clear();run(fx,c,w);assert c['units']==[t]
    w=world();c=w['RUS'];w[t]['states'][0]['neighbors']=[];run(fx,c,w);assert not c.get('units')

# Integration: ten existing Ukraine actions get the same start reward, never
# status entries. Focus rewards are separate from idempotent resource setup.
ukr=(ROOT/'common/decisions/RUS_ukr_underground_decisions.txt').read_text(encoding='utf-8-sig')
assert len(re.findall(r'\bcomplete_effect\s*=\s*{',ukr))==ukr.count('RUS_rd_action_readiness = yes')==10
focus=(ROOT/'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt').read_text(encoding='utf-8-sig')
for n in ['020','021','022','036']:
    body=focus.split('id = RUS_future_foreign_'+n,1)[1].split('\n\tfocus =',1)[0]
    assert 'add_political_power = 50' in body and 'RUS_rd_' in body
loc=(ROOT/'localisation/simp_chinese/RUS_regional_diplomacy_l_simp_chinese.yml').read_bytes()
assert loc.startswith(b'\xef\xbb\xbf')
keys=re.findall(r'^ ([A-Za-z0-9_]+):',loc.decode('utf-8-sig'),re.M)
assert len(keys)==len(set(keys))
for id in D:assert id in keys and id+'_desc' in keys
print('PASS: 19 action variants; transactions/discounts, readiness, cancellation, risk, timers, caps, country isolation, both fort-damage variants, border militia and integrations. Not a game-engine test.')
