"""Execute the shipped Ukraine script subset; this is not a HOI4 engine test."""
from pathlib import Path
import re,copy
ROOT=Path(__file__).resolve().parents[2]
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
FX=dict((k,v) for k,_,v in read('common/scripted_effects/RUS_ukr_underground_effects.txt'))
FX['RUS_rd_action_readiness']=get(read('common/scripted_effects/RUS_regional_diplomacy_effects.txt'),'RUS_rd_action_readiness')
TR=dict((k,v) for k,_,v in read('common/scripted_triggers/RUS_ukr_underground_triggers.txt'))
FX.update((k,v) for k,_,v in read('common/scripted_effects/RUS_diplomacy_cost_effects.txt'))
TR.update((k,v) for k,_,v in read('common/scripted_triggers/RUS_diplomacy_cost_triggers.txt'))
TR['RUS_europe_intervention_UKR_selected_or_overview']=parse('always = yes')
D=dict((k,v) for k,_,v in get(read('common/decisions/RUS_ukr_underground_decisions.txt'),'RUS_Spreading_the_Revolution_decisions'))
def country(tag):return dict(tag=tag,exists=True,cap=False,socialist=tag=='RUS',ai=False,subject=False,faction='GER' if tag!='RUS' else 'RUS',war=set(),focus=set(),flags={},vars={},ideas={},decisions={},pp=1000,equipment=10000,stability=.8,balance=0,events=[])
def world():
    w={t:country(t) for t in ['RUS','UKR','GER']}
    w['RUS']['focus']={'RUS_future_foreign_037','RUS_future_foreign_059'};w['UKR']['flags']['UKR_revolt_over']=None
    run(FX['RUS_ukr_init'],w['RUS'],w);return w
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
        if k=='country_exists':return v in w and w[v].get('exists',False)
        if k=='has_country_leader':return c.get('leader')==get(v,'character')
        if k=='has_dynamic_modifier':return get(v,'modifier') in c.get('dynamic',set())
        if k=='has_power_balance':return c.get('bop',False)
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
        if k=='has_equipment':return all(compare(c['equipment'],o,float(z)) for a,o,z in v)
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
        elif k in ['random_owned_controlled_state','every_owned_state']:
            states=[st for st in c.get('states',[]) if st['owner']==c['tag'] and (k=='every_owned_state' or st['controller']==c['tag']) and check(get(v,'limit',[]),st,w)]
            if k=='random_owned_controlled_state':states=[states[choice%len(states)]] if states else []
            for st in states:run([n for n in v if n[0]!='limit'],st,w,choice)
        elif k=='set_state_flag':c['flags'][v]=None
        elif k=='clr_state_flag':c['flags'].pop(v,None)
        elif k=='damage_building':
            kind=get(v,'type');assert c['buildings'].get(kind,0)>0
            c['damage'][kind]=min(c['buildings'][kind],c['damage'].get(kind,0)+float(get(v,'damage')))
        elif k=='hidden_effect':run(v,c,w,choice)
        elif k=='custom_effect_tooltip':pass
        elif k=='effect_tooltip':pass # Presentation-only: must never grant resources.
        elif k=='set_country_flag':
            if isinstance(v,list):c['flags'][get(v,'flag')]=int(get(v,'days'))
            else:c['flags'][v]=None
        elif k=='clr_country_flag':c['flags'].pop(v,None)
        elif k in ['set_variable','add_to_variable','subtract_from_variable']:
            a,_,z=v[0];z=val(z,c);current=c['vars'].get(a,0)
            c['vars'][a]=z if k=='set_variable' else current+z*(1 if k=='add_to_variable' else -1)
        elif k=='clamp_variable':
            a=get(v,'var');c['vars'][a]=max(float(get(v,'min')),min(float(get(v,'max')),c['vars'].get(a,0)))
        elif k=='add_political_power':c['pp']+=float(v)
        elif k=='add_equipment_to_stockpile':c['equipment']+=float(get(v,'amount'))
        elif k=='add_dynamic_modifier':c.setdefault('dynamic',set()).add(get(v,'modifier'))
        elif k=='add_ideas':c['ideas'][v]=None
        elif k=='remove_ideas':c['ideas'].pop(v,None)
        elif k=='add_timed_idea':c['ideas'][get(v,'idea')]=int(get(v,'days'))
        elif k=='add_stability':c['stability']+=float(v)
        elif k=='add_power_balance_value':c['balance']+=float(get(v,'value'))
        elif k=='set_power_balance':c['bop']=True
        elif k=='country_event':c['events'].append(get(v,'id'))
        elif k=='random_list':
            options=[]
            for weight,_,body in v:
                mod=get(body,'modifier',[])
                if mod and check([n for n in mod if n[0]!='factor'],c,w) and get(mod,'factor')=='0':continue
                options.append([n for n in body if n[0]!='modifier'])
            assert options;run(options[choice%len(options)],c,w,choice)
        else:raise AssertionError(('Unsupported effect',k))
def tick(w,days=1):
    for _ in range(days):
        for c in w.values():
            for field in ['flags','ideas']:
                for k,d in list(c[field].items()):
                    if d is not None:
                        if d<=1:del c[field][k]
                        else:c[field][k]=d-1
        run(FX['RUS_ukr_tick'],w['RUS'],w)
        c=w['RUS']
        for id,remaining in list(c['decisions'].items()):
            d=D[id]
            if check(get(d,'cancel_trigger'),c,w):
                run(get(d,'cancel_effect'),c,w)
                # Guard against engines invoking remove_effect after cancellation as well.
                run(get(d,'remove_effect'),c,w)
                del c['decisions'][id]
            elif remaining<=1:
                run(get(d,'remove_effect'),c,w);del c['decisions'][id]
            else:c['decisions'][id]=remaining-1
def allowed(n,w):
    d=D['RUS_ukr_'+n];c=w['RUS']
    return all(check(get(d,k,[]),c,w) for k in ['visible','available','custom_cost_trigger'])
def start(n,w):
    assert allowed(n,w),('not available',n)
    run(get(D['RUS_ukr_'+n],'complete_effect'),w['RUS'],w)
    w['RUS']['decisions']['RUS_ukr_'+n]=int(get(D['RUS_ukr_'+n],'days_remove'))
def consumer_burden(w):
    c=w['RUS'];native=sum(float(get(get(D[id],'modifier',[]),'consumer_goods_factor',0)) for id in c['decisions'])
    return native+(.04 if 'RUS_ukr_emergency_burden' in c['ideas'] else 0)
def nets(w,*names):
    for n in names:w['RUS']['flags']['RUS_ukr_'+n+'_network']=None
def strength(w,n):w['RUS']['vars']['RUS_ukr_strength']=n
def alert(w,n):w['RUS']['vars']['RUS_ukr_alert']=n
def war(w):w['RUS']['war'].add('UKR');w['UKR']['war'].add('RUS')
def peace(w):w['RUS']['war'].clear();w['UKR']['war'].clear()
