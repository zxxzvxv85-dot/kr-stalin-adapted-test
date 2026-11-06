"""Compose native industrial decisions with a Stalin-stage national plan.

References: KR Central Asia decisions (civilian_factory_use), native
add_days_remove/remove_decision/get_supply_vehicles; state-scoped add_manpower.
"""
import json,re
from hoi4_politics_blocks import parse
from national_plan_catalog import ROOT,DATA,PROJECTS,REGIONS,CORRIDORS,MIO_TARGETS,MIO_REWARDS,CONSORTIUM_MIOS,FACTORY_GOALS,EXTRA_EDUCATION_PROJECTS,EXTRA_RESOURCE_PROJECTS,EXTRA_STRATEGIC_PROJECTS

CAT='RUS_first_five_year_plan_industrial_projects'
DEC='common/decisions/RUS decisions (Russia).txt'
FX='common/scripted_effects/RUS_national_plan_effects.txt'
DM='common/dynamic_modifiers/RUS_national_plan_modifiers.txt'
P='RUS_np_'
def b(key,body):return key+' = {\n'+''.join('\t'+s+'\n' for s in body)+'}\n'
def sv(v,x):return f'set_variable = {{ {v} = {x} }}'
def op(k,v,x):return f'{k}_variable = {{ {v} = {x} }}'
def add(v,x):return op('add_to',v,x)
def sub(v,x):return op('subtract_from',v,x)
def mul(v,x):return op('multiply',v,x)
def div(v,x):return op('divide',v,x)
def iff(c,lines):return b('if',['limit = { '+c+' }',*lines]).strip()
def ck(v,rel,x):return f'check_variable = {{ {v} {rel} {x} }}'
def clamp(v,lo,hi):return [iff(ck(v,'<',lo),[sv(v,lo)]),iff(ck(v,'>',hi),[sv(v,hi)])]
def var(p,s):return P+p['key']+'_'+s
def flag(p,s):return 'has_country_flag = '+var(p,s)
def call(p,s):return var(p,s)+' = yes'
def stock(n):return f'has_equipment = {{ train_equipment_1 > {n-1} }}'
def equip(x):return f'add_equipment_to_stockpile = {{ type = train_equipment_1 amount = {x} }}'
def scope(s,lines):return b(str(s),lines).strip()
def own(s):return f'{s} = {{ is_owned_and_controlled_by_ROOT_or_subject = yes }}'
def owned(p):return ' '.join(own(s) for s in p['states'])
def running(p):return flag(p,'running')
def repeatable(p):return p.get('original_id',p['id'])=='RUS_kamenev_all_russian_electrification'
def unfinished(p):
    return '' if repeatable(p) else 'NOT = { '+flag(p,'completed')+' }'+(' NOT = { has_country_flag = RUS_rc_finished_'+p['original_id']+' }' if p['legacy'] else '')
def remove_active(p):
    return f'remove_decision = {p["id"]}'
def ceil(v):return [add(v,.499),f'round_variable = {v}']
def restore(text):
    """Restore owned catalogue nodes before applying provisional GUI observers."""
    text=re.sub(r'(?ms)^\s*# RUS_NP_MANAGEMENT_BEGIN\n.*?^\s*# RUS_NP_MANAGEMENT_END\s*\n','\n',text)
    cat=next(n for n in parse(text) if n.k==CAT)
    old={p['id']:p['original'] for p in DATA['legacy']}
    edits=[(n.a,n.b,old[n.k]) for n in cat.v if n.k in old]
    for a,z,s in sorted(edits,reverse=True):text=text[:a]+s+text[z:]
    return text

def safe_build(state,kind,amount=1):
    cap={'infrastructure':5,'energy_infrastructure':5,'industrial_infrastructure':5}.get(kind,20)
    body=[]
    for _ in range(amount):
        body += [iff(f'{kind} < {cap}',([
            'add_extra_state_shared_building_slots = 1'] if kind in ('industrial_complex','arms_factory','dockyard') else [])+[
            f'add_building_construction = {{ type = {kind} level = 1 instant_build = yes }}']),
            b('else',['add_extra_state_shared_building_slots = 1']).strip()]
    return scope(state,body)

def develop(state):
    rows=['hidden_effect = { '+iff('NOT = { has_variable = RUS_np_development }',[sv('RUS_np_development',2)])+' }']
    for old in range(3):
        step=[]
        if old in (0,1):step += [f'remove_dynamic_modifier = {{ modifier = RUS_np_region_{old} }}']
        if old+1 in (1,3):step += [f'add_dynamic_modifier = {{ modifier = RUS_np_region_{old+1} }}']
        step += ['hidden_effect = { '+sv('RUS_np_development',old+1)+' }']
        # Descending order makes exactly one transition, including when the
        # state had no shortage before its first plan improvement.
        condition=('OR = { NOT = { has_variable = RUS_np_development } '+ck('RUS_np_development','=',2)+' }') if old==2 else 'has_variable = RUS_np_development '+ck('RUS_np_development','=',old)
        rows.insert(1,iff('hidden_trigger = { '+condition+' }',step))
    return scope(state,rows)

def farm_credit():return ['custom_effect_tooltip = RUS_np_farm_credit_tt','hidden_effect = { '+add(P+'farm_credit',100)+' }']

def base_reward(p):
    s=p['states'][0];r=p.get('reward');out=[]
    if r in ('factory','aluminium','wagons','fertilizer'):out.append(safe_build(s,'industrial_complex'))
    if r=='aluminium':out.append(scope(s,['add_resource = { type = aluminium amount = 8 }']))
    if r=='energy':out.append(safe_build(s,'energy_infrastructure'))
    if r in ('grid','metro','canal','hub'):out.append(safe_build(s,'infrastructure'))
    if r in ('metro','canal'):out += [scope(s,['add_manpower = 5000']),develop(s)]
    if r=='wagons':out += [equip(10)]
    if r=='fertilizer':out += ['custom_effect_tooltip = RUS_np_fertilizer_reward_tt','hidden_effect = { '+sv(P+'fertilizer',.03)+' }']
    if r=='hub':
        out += ['hidden_effect = { set_country_flag = '+var(p,'hub')+' }',develop(s)]
        for c in CORRIDORS:
            if c['project']==p['id']:
                out += ['build_railway = { level = '+str(c['level'])+' path = { '+' '.join(map(str,c['path']))+' } }','hidden_effect = { '+sv(P+'rail_'+c['key'],c['level'])+' }']
    if r=='rural':out += ['custom_effect_tooltip = RUS_np_rural_reward_tt','hidden_effect = { '+sv(var(p,'farm_rate'),2)+' }',develop(s)]
    return out

def goals(p):
    s=p['states'][0];k=p['kind']
    # Independent goal records; none is an extra hard prerequisite.
    first=(f'{s} = {{ NOT = {{ infrastructure < 3 }} }}','基础设施达到3级',[develop(s)])
    if p['key'] in ('bearing','uvz'):
        first=(f'{s} = {{ NOT = {{ infrastructure < 3 }} }} has_country_flag = RUS_education_system_active','基础设施达到3级，教育改革已启动',['RUS_np_award_education = yes'])
    if k=='resource':
        first=(f'{s} = {{ check_variable = {{ resource@steel > 19 }} }}','本地区钢产出至少20',[scope(s,['add_resource = { type = steel amount = 4 }'])])
        # Only augment a known existing raw resource, never fabricate a deposit.
        resource=next((n for n in ('oil','tungsten','aluminium','coal','steel') if p.get('original') and re.search(r'type\s*=\s*'+n+r'\b',p['original'])),None)
        if resource:first=(f'{s} = {{ check_variable = {{ resource@{resource} > 7 }} }}','本地区对应资源产出至少8',[scope(s,[f'add_resource = {{ type = {resource} amount = 4 }}'])])
        else:first=(f'{s} = {{ NOT = {{ infrastructure < 3 }} }}','基础设施达到3级',[scope(s,['add_extra_state_shared_building_slots = 1'])])
    if k=='agriculture':
        second=('has_country_flag = RUS_nat_enabled check_variable = { RUS_nat_machine_stock > 99 }','农业建设已启用且农机库存至少100',farm_credit())
        if p['key'] in ('tsaritsyn_rural','rostselmash'):
            second=('has_country_flag = RUS_nat_enabled has_country_flag = RUS_agri_management_unlocked NOT = { has_country_flag = RUS_maximalist_land_reform_failure } check_variable = { RUS_nat_machine_stock > 99 }','农业建设已启用、土改可推进且农机库存至少100',farm_credit()+['RUS_np_award_land_score = yes'])
    elif k=='city':
        second=(f'{s} = {{ NOT = {{ industrial_complex < 3 }} }}','本地区民用工厂达到3座',[scope(s,['add_manpower = 5000','add_extra_state_shared_building_slots = 1'])])
    else:
        second=(f'check_variable = {{ RUS_np_rail_region_{p["region"]} > 1.499 }}','本工业区计划干线平均等级达到1.50',[safe_build(s,'industrial_infrastructure')])
    rows=[first,second]
    if p['key'] in FACTORY_GOALS:
        index,kind,label,amount,offsite=FACTORY_GOALS[p['key']]
        _,_,reward=rows[index]
        condition=f'{s} = {{ NOT = {{ check_variable = {{ building_level@{kind} < ROOT.{var(p,"factory_target")} }} }} }}'
        rows[index]=(condition,f'施工期间在本地区额外建成{amount}座{label}',reward+([f'add_offsite_building = {{ type = {offsite} level = 1 }}'] if offsite else []))
    if p['key'] in MIO_REWARDS:
        key,index=MIO_REWARDS[p['key']];condition,name,reward=rows[index]
        rows[index]=(condition,name,reward+['RUS_np_award_mio_'+key+' = yes'])
    if p['key'] in EXTRA_EDUCATION_PROJECTS:
        rows.append((f'{s} = {{ NOT = {{ infrastructure < 3 }} }} has_country_flag = RUS_education_system_active',
                     '基础设施达到3级，教育改革已启动',['RUS_np_award_education = yes']))
    if p['key'] in EXTRA_RESOURCE_PROJECTS:
        rows.append((f'{s} = {{ NOT = {{ infrastructure < 3 }} }} check_variable = {{ RUS_np_rail_region_{p["region"]} > 1.499 }}',
                     '基础设施达到3级，计划干线平均等级达到1.50',['RUS_np_award_resources = yes']))
    if p['key'] in EXTRA_STRATEGIC_PROJECTS:
        resource,amount,label=EXTRA_STRATEGIC_PROJECTS[p['key']]
        rows.append((f'{s} = {{ NOT = {{ infrastructure < 3 }} check_variable = {{ resource@{resource} > 7 }} }}',
                     f'基础设施达到3级，本地区{label}产出至少8',
                     [scope(s,[f'add_resource = {{ type = {resource} amount = {amount} }}'])]))
    return rows

def mio_cases(key):
    primary,merged,successor,_=MIO_TARGETS[key]
    def eligible(token):return f'has_military_industrial_organization = {token} mio:{token} = {{ is_mio_available = yes }}'
    if merged:
        redirect='has_completed_focus = RUS_future_foreign_030 has_country_flag = '+merged+' '+eligible(successor)
        return [(redirect,successor),('NOT = { AND = { '+redirect+' } } '+eligible(primary),primary)]
    return [(eligible(primary),primary)]

def mio_preview(key):
    if key=='consortium':return [iff('has_dlc_aat = yes',['custom_effect_tooltip = RUS_np_mio_consortium_award_tt'])]
    primary,merged,_,_=MIO_TARGETS[key]
    if merged:
        condition,successor=mio_cases(key)[0]
        body=[iff('hidden_trigger = { '+condition+' }',[f'effect_tooltip = {{ mio:{successor} = {{ add_mio_size = 1 }} }}']),
              b('else',[f'effect_tooltip = {{ mio:{primary} = {{ add_mio_size = 1 }} }}']).strip()]
    else:body=[f'effect_tooltip = {{ mio:{primary} = {{ add_mio_size = 1 }} }}']
    return [iff('has_dlc_aat = yes',body)]

def consortium_ready():
    # Exact roster/eligibility used by native KR russia_events.440.
    return 'OR = { '+' '.join(f'mio:{token} = {{ is_mio_assigned_to_task = yes }}' for token in CONSORTIUM_MIOS)+' }'

def mio_effects():
    out=[]
    for key,(_,merged,successor,_) in MIO_TARGETS.items():
        primary=MIO_TARGETS[key][0];credit=P+'mio_'+key+'_credit'
        # Preview dispatch lives outside effect_tooltip in the decision. A
        # forced tooltip around the whole conditional can expose both branches.
        out.append(b(P+'award_mio_'+key,[iff('has_dlc_aat = yes',[
            'hidden_effect = { '+add(credit,1)+' '+P+'claim_mio_'+key+' = yes }'])]))
        cases=[]
        for i,(condition,token) in enumerate(mio_cases(key)):
            cases.append(b('if' if i==0 else 'else_if',['limit = { '+condition+' }',f'mio:{token} = {{ add_mio_size = 1 }}',sub(credit,1)]).strip())
        out.append(b(P+'claim_mio_'+key,[iff('has_dlc_aat = yes '+ck(credit,'>',0),cases)]))
    out.append(b(P+'award_mio_consortium',[iff('has_dlc_aat = yes',[
        'custom_effect_tooltip = RUS_np_mio_consortium_award_tt',
        'hidden_effect = { '+add(P+'mio_consortium_credit',1)+' }'])]))
    out.append(b(P+'claim_mio_consortium',[iff('has_dlc_aat = yes '+ck(P+'mio_consortium_credit','>',0)+' '+consortium_ready(),[
        sub(P+'mio_consortium_credit',1),'country_event = russia_events.440'])]))
    return ''.join(out)

def new_node(p):
    s=p['states'][0]
    return b(p['id'],[
        'icon = GFX_decision_generic_construction','allowed = { original_tag = RUS }','fire_only_once = yes',
        f'cost = {p["cost"]}',f'days_remove = {p["fallback"]}',
        'visible = { RUS_np_context = yes NOT = { '+flag(p,'completed')+' } }',
        'available = { '+owned(p)+' }',
        f'highlight_states = {{ highlight_state_targets = {{ state = {s} }} }}',
        'complete_effect = { }',b('remove_effect',base_reward(p)).strip(),
        'ai_will_do = { base = 0 }'])

def patch_node(node,p):
    text=node.raw();n=parse(text)[0];fields={}
    def field(key,body,append=False):
        e=n.one(key)
        value=b(key,([e.inner()] if append and e else [])+body).strip()
        fields[key]=value
    # New playtest entry: all 62 projects are directly listed without focuses.
    # Outside managed Russia, preserve original gates and PP prices.
    # allowed is cached by HOI4 at start; it must contain static country identity
    # only. Managed copies have their own IDs so original activated decisions
    # and their provisional availability are not changed.
    field('allowed',['original_tag = RUS'])
    fields['on_map_mode']='on_map_mode = decision_view_only'
    fields['days_remove']='days_remove = '+var(p,'initial_days')+'?'+str(p['fallback'])
    extra=''
    if p.get('original_id')=='RUS_create_tankograd':extra='has_country_flag = unlock_chtz'
    if p.get('original_id')=='RUS_convert_civilian_aviation_industry':extra='219 = { NOT = { industrial_complex < 3 } }'
    field('available',['hidden_trigger = { RUS_np_context = yes } RUS_np_ready_'+p['key']+' = yes num_of_civilian_factories_available_for_projects > '+str(p['civ']-1)+' '+extra])
    once=unfinished(p)
    field('visible',['RUS_np_context = yes OR = { check_variable = { RUS_np_filter = 0 } check_variable = { RUS_np_filter = '+str(p['region'])+' } } '+once])
    for c in CORRIDORS:
        if c['project']==p.get('original_id',p['id']):field('highlight_states',rail_highlight(c))
    start=n.one('complete_effect')
    field('complete_effect',([start.inner()] if start else [])+[
        iff('RUS_np_context = yes',[
            'custom_effect_tooltip = '+var(p,'cost_tt'),
            *([f'effect_tooltip = {{ add_dynamic_modifier = {{ modifier = {var(p,"cost")} }} }}'] if p['civ'] or p['consumer'] else []),
            *goal_tooltips(p),
            'hidden_effect = { '+call(p,'begin')+' }'])])
    original=node.one('remove_effect').inner()
    field('remove_effect',[
        b('effect_tooltip',[original]).strip(),*goal_tooltips(p),
        'hidden_effect = { '+call(p,'finish')+' }'])
    # The managed ledger never refunds PP (the old Central Asia cancellation
    # did). Its legacy UI flags are cleared by the common release handler.
    field('cancel_effect',['hidden_effect = { '+call(p,'cancel')+' }'])
    prior=n.one('cancel_trigger')
    field('cancel_trigger',['OR = { '+(prior.inner() if prior else '')+' AND = { '+running(p)+' OR = { RUS_np_context = no NOT = { '+owned(p)+' } } } }'])
    edits=[]
    for key,value in fields.items():
        e=n.one(key)
        edits.append((e.a,e.b,value) if e else (n.ib,n.ib,'\n'+value+'\n'))
    # Even state_target=no declares a targeted decision. With no targets or
    # target_trigger the engine enumerates every country, flooding the map.
    # These are plain decisions with fixed reward scopes, so omit targeting.
    for key in ('state_target','state_trigger','target_root_trigger','target_trigger','targets','target_array','cancel_if_not_visible'):
        e=n.one(key)
        if e:edits.append((e.a,e.b,''))
    for a,z,value in sorted(edits,reverse=True):text=text[:a]+value+text[z:]
    text=text.replace(n.k+' =',p['id']+' =',1)
    return text

def goal_tooltips(p):
    rows=[]
    for i,(condition,_,reward) in enumerate(goals(p),1):
        rows += ['custom_effect_tooltip = '+var(p,'goal_'+str(i)+'_tt')]
        ordinary=[line for line in reward if not line.startswith('RUS_np_award_mio_')]
        if ordinary:rows += [b('effect_tooltip',ordinary).strip()]
        for line in reward:
            if line.startswith('RUS_np_award_mio_'):rows += mio_preview(line.split(' =')[0].removeprefix('RUS_np_award_mio_'))
    return rows

def rail_highlight(c):
    # Native/KR Netherlands flooding decisions use explicit province lists.
    # Read the exact same path used by railway construction and registration.
    return ['highlight_provinces = { '+' '.join(map(str,c['path']))+' }','highlight_only_provinces = yes']

def refresh():
    out=[sv(P+'civ','num_of_available_civilian_factories'),*clamp(P+'civ',0,10000),sv(P+'education',0)]
    out += [iff('has_variable = RUS_basic_education_level',[sv(P+'education','RUS_basic_education_level'),mul(P+'education',.6),sv(P+'tmp','RUS_higher_education_level'),mul(P+'tmp',.4),add(P+'education',P+'tmp')])]
    out += clamp(P+'education',0,100)+[sv(P+'efficiency',P+'education'),mul(P+'efficiency',.005),add(P+'efficiency',.75),sv(P+'speed',1)]
    out += [iff('has_variable = RUS_education_enthusiasm',[sv(P+'speed','RUS_education_enthusiasm'),mul(P+'speed',.01),add(P+'speed',.5)])]+clamp(P+'speed',.5,1.5)
    out += [sv(P+'income',P+'civ'),mul(P+'income',.02),mul(P+'income',P+'efficiency'),sv(P+'grant',P+'civ'),mul(P+'grant',10),mul(P+'grant',P+'efficiency'),sv(P+'slots',2)]
    for v in ('civ','education'):
        for threshold in (25,50,75,100,125,150):
            if v=='education' and threshold>100:continue
            out.append(iff('NOT = { '+ck(P+v,'<',threshold)+' }',[add(P+'slots',1)]))
    out += clamp(P+'slots',2,8)+[sv(P+'active',0),sv(P+'trains',0),sv(P+'rail_average',0),sv(P+'rail_weight',0),sv(P+'farm_rate',0),sv(P+'repair',0)]
    for region in REGIONS:out += [sv(P+'rail_region_'+str(region),0),sv(P+'rail_weight_'+str(region),0)]
    for p in PROJECTS:
        value=var(p,'initial_days');base=p['base_days'].split('?')[0]
        out += [sv(value,p['fallback'])]
        if not base.isdigit():out += [iff('has_variable = '+base,[sv(value,base)])]
        out += clamp(value,1,3650)+[div(value,P+'speed'),*ceil(value),add(value,1)]
        out += [iff(running(p),[add(P+'active',1),add(P+'trains',var(p,'trains'))])]
        if p.get('reward')=='rural':out += [iff(flag(p,'completed'),[add(P+'farm_rate',var(p,'farm_rate')),add(P+'repair',.01)])]
    for c in CORRIDORS:
        level=P+'rail_'+c['key']
        connected='has_railway_connection = { path = { '+' '.join(map(str,c['path']))+' } }'
        out += [iff('has_variable = '+level+' '+' '.join(own(s) for s in c['states'])+' '+connected,[sv(P+'tmp',level),mul(P+'tmp',c.get('weight',1)),add(P+'rail_average',P+'tmp'),*[add(P+'rail_region_'+str(r),P+'tmp') for r in c['regions']]])]
        out += [add(P+'rail_weight',c.get('weight',1))]
        out += [add(P+'rail_weight_'+str(r),c['weight']) for r in c['regions']]
    out += [div(P+'rail_average',P+'rail_weight')]
    out += [sv(P+'rail_display',P+'rail_average')]
    for region in REGIONS:
        out += [div(P+'rail_region_'+str(region),P+'rail_weight_'+str(region)),iff(ck(P+'filter','=',region),[sv(P+'rail_display',P+'rail_region_'+str(region))])]
    for city in ('moscow','leningrad','tsaritsyn'):
        out += [add(P+'trains',P+city+'_dispatch')]
    out += ['RUS_np_refresh_rural = yes']
    return out

def native_base(p):
    n=parse(p['original'] if p['legacy'] else new_node(p))[0]
    return n.one('remove_effect').inner()

def project_effects(p):
    k=p['key'];s=p['states'][0];out=[]
    timer='days_decision_timeout@'+p['id']
    base=p['base_days'].split('?')[0]
    start=[sv(var(p,'total'),p['fallback'])]
    if not base.isdigit():start += [iff('has_variable = '+base,[sv(var(p,'total'),base)])]
    start += clamp(var(p,'total'),1,3650)+[
        'set_country_flag = '+var(p,'managed'),'set_country_flag = '+var(p,'running'),
        sv(var(p,'left'),var(p,'total')),sv(var(p,'paid'),p['budget']),sv(var(p,'trains'),p['trains']),sv(var(p,'last_day'),'global.num_days'),
        sub(P+'available',p['budget']),add(P+'frozen',p['budget']),equip(-p['trains'])]
    if k in FACTORY_GOALS:
        _,kind,_,amount,_=FACTORY_GOALS[k]
        start += [sv(var(p,'factory_target'),f'{s}.building_level@{kind}'),add(var(p,'factory_target'),amount)]
    if p['civ'] or p['consumer']:start += [f'add_dynamic_modifier = {{ modifier = {var(p,"cost")} }}']
    start += ['clr_country_flag = '+var(p,'goal_'+str(i)) for i in (1,2)]
    start += [call(p,'goals'),'RUS_np_refresh = yes',call(p,'timer')]
    out.append(b(var(p,'begin'),[iff('RUS_np_ready_'+k+' = yes',start)]))
    goal_lines=[]
    for i,(condition,_,_) in enumerate(goals(p),1):
        goal_lines += [iff('NOT = { '+flag(p,'goal_'+str(i))+' } '+owned(p)+' '+condition,['set_country_flag = '+var(p,'goal_'+str(i))])]
    out.append(b(var(p,'goals'),[iff(running(p)+' NOT = { '+flag(p,'completed')+' }',goal_lines)]))
    # One guard day keeps an engine expiry from racing a slow final pulse.
    # No progress is discarded: terminal processing tops up at most one pulse.
    # add_days_remove.days accepts a literal integer, not a variable token.
    # Decompose the signed integer delta into native constant-day adjustments.
    positive=[];negative=[]
    for power in range(13,-1,-1):
        step=2**power
        positive.append(iff('NOT = { '+ck(P+'adjust','<',step)+' }',[
            f'add_days_remove = {{ decision = {p["id"]} days = {step} }}',sub(P+'adjust',step)]))
        negative.append(iff('NOT = { '+ck(P+'adjust','>',-step)+' }',[
            f'add_days_remove = {{ decision = {p["id"]} days = {-step} }}',add(P+'adjust',step)]))
    out.append(b(var(p,'apply_timer_delta'),[f'round_variable = {P}adjust',
        iff(ck(P+'adjust','>',0),positive),b('else',negative).strip()]))
    timerlines=[sv(var(p,'display'),var(p,'left')),div(var(p,'display'),P+'speed'),*ceil(var(p,'display')),
        *clamp(var(p,'display'),1,7300),sv(P+'adjust',var(p,'display')),add(P+'adjust',1),sub(P+'adjust',timer),
        call(p,'apply_timer_delta')]
    out.append(b(var(p,'timer'),[iff(running(p),timerlines)]))
    pulse=[sv(var(p,'last_day'),'global.num_days'),call(p,'goals'),sub(var(p,'left'),P+'speed'),*clamp(var(p,'left'),0,var(p,'total'))]
    out.append(b(var(p,'tick'),[iff(running(p)+' '+ck(var(p,'last_day'),'<','global.num_days'),pulse)]))
    # Release is guarded by running; the durable managed flag prevents a
    # duplicate native callback from falling through to original rewards.
    release=[sub(P+'frozen',var(p,'paid')),add(P+'available',P+'refund'),add(P+'spent',P+'consumed'),
        sv(P+'return_trains',var(p,'trains')),
        iff('NOT = { '+owned(p)+' }',[mul(P+'return_trains',.75),op('subtract_from',P+'return_trains',.499),f'round_variable = {P}return_trains']),
        equip(P+'return_trains'),
        'clr_country_flag = '+var(p,'running'),
        *([f'remove_dynamic_modifier = {{ modifier = {var(p,"cost")} }}'] if p['civ'] or p['consumer'] else []),
        sv(var(p,'trains'),0),sv(var(p,'paid'),0),'RUS_np_refresh = yes']
    if p['legacy']:
        release += ['set_country_flag = RUS_rc_settled_'+p['original_id'],'clr_country_flag = RUS_rc_running_'+p['original_id']]
    out.append(b(var(p,'release'),[iff(running(p),release)]))
    cancel=[sv(P+'consumed',var(p,'total')),sub(P+'consumed',var(p,'left')),div(P+'consumed',var(p,'total')),mul(P+'consumed',.8),mul(P+'consumed',var(p,'paid')),
        sv(P+'refund',var(p,'paid')),sub(P+'refund',P+'consumed'),
        iff('NOT = { '+owned(p)+' }',[sv(P+'loss',P+'refund'),mul(P+'loss',.5),sub(P+'refund',P+'loss'),add(P+'consumed',P+'loss')]),call(p,'release')]
    out.append(b(var(p,'cancel'),[iff(running(p),cancel)]))
    # Rewards do not run if the project terminates after losing its territory.
    bonus=[]
    for i,(_,_,reward) in enumerate(goals(p),1):bonus += [iff(flag(p,'goal_'+str(i)),reward)]
    for c in CORRIDORS:
        if p['legacy'] and c['project']==p['original_id']:bonus += [sv(P+'rail_'+c['key'],c['level']),'build_railway = { level = '+str(c['level'])+' path = { '+' '.join(map(str,c['path']))+' } }']
    reward=[call(p,'goals'),native_base(p),iff('NOT = { '+flag(p,'completed')+' }',bonus),'set_country_flag = '+var(p,'completed'),
        sv(P+'consumed',var(p,'paid')),mul(P+'consumed',.8),sv(P+'refund',var(p,'paid')),sub(P+'refund',P+'consumed'),call(p,'release')]
    finish=[call(p,'tick'),iff(owned(p),reward),b('else',[call(p,'cancel')]).strip()]
    out.append(b(var(p,'finish'),[iff(running(p),finish)]))
    return ''.join(out)

def management():
    out=[]
    common=['allowed = { original_tag = RUS }','visible = { RUS_np_context = yes }','on_map_mode = decision_view_only','cost = 0','ai_will_do = { base = 0 }']
    out.append(b('RUS_np_open_account',[x for x in common if not x.startswith('visible =')]+['visible = { RUS_np_context = yes NOT = { has_country_flag = RUS_np_initialized } }','complete_effect = { hidden_effect = { RUS_np_initialize = yes } }']))
    for i in range(7):
        out.append(b(P+'filter_'+str(i),common+[f'complete_effect = {{ hidden_effect = {{ set_variable = {{ RUS_np_filter = {i} }} RUS_np_refresh = yes }} }}']))
    for key in MIO_TARGETS:
        credit=P+'mio_'+key+'_credit'
        eligibility='OR = { '+' '.join('AND = { '+condition+' }' for condition,_ in mio_cases(key))+' }'
        preview=mio_preview(key)
        out.append(b(P+'redeem_mio_'+key,[x for x in common if not x.startswith('visible =')]+[
            'visible = { RUS_np_context = yes has_dlc_aat = yes '+ck(credit,'>',0)+' }',
            'available = { '+eligibility+' }',b('complete_effect',preview+['hidden_effect = { '+P+'claim_mio_'+key+' = yes }']).strip()]))
    out.append(b(P+'redeem_mio_consortium',[x for x in common if not x.startswith('visible =')]+[
        'visible = { RUS_np_context = yes has_dlc_aat = yes '+ck(P+'mio_consortium_credit','>',0)+' }',
        'available = { '+consortium_ready()+' }',
        'complete_effect = { custom_effect_tooltip = RUS_aat_consortium_tt hidden_effect = { RUS_np_claim_mio_consortium = yes } }']))
    for p in PROJECTS:
        out.append(b(var(p,'terminate'),[x for x in common if not x.startswith('visible =')]+[
            'visible = { RUS_np_context = yes '+running(p)+' OR = { '+ck(P+'filter','=',0)+' '+ck(P+'filter','=',p['region'])+' } }',
            'available = { '+running(p)+' }',
            # Settle first so even a native removal callback cannot award
            # construction rewards for an intentionally terminated project.
            'complete_effect = { custom_effect_tooltip = RUS_np_terminate_tt hidden_effect = { '+call(p,'cancel')+' '+remove_active(p)+' } }']))
    for city,state in [('moscow',219),('leningrad',195),('tsaritsyn',217)]:
        hub=P+city+'_logistics_completed';v=P+city+'_dispatch'
        vis=[x for x in common if not x.startswith('visible =')]
        out.append(b(P+city+'_dispatch',vis+['visible = { RUS_np_context = yes has_country_flag = '+hub+' '+ck(v,'=',0)+' }',
            'available = { has_country_flag = '+hub+' '+own(state)+' '+stock(10)+' check_variable = { '+v+' = 0 } has_railway_connection = { start_state = 219 target_state = '+str(195 if state==219 else state)+' } }',
            'complete_effect = { effect_tooltip = { add_dynamic_modifier = { modifier = RUS_np_transport_network } } hidden_effect = { '+equip(-10)+' '+sv(v,10)+' RUS_np_refresh_transport = yes } }']))
        out.append(b(P+city+'_recall',vis+['visible = { RUS_np_context = yes '+ck(v,'>',0)+' }',
            'complete_effect = { hidden_effect = { '+equip(v)+' '+sv(v,0)+' RUS_np_refresh_transport = yes } }']))
    for c in CORRIDORS:
        v=P+'rail_'+c['key']
        path=' path = { '+' '.join(map(str,c['path']))+' } '
        out.append(b(P+'upgrade_'+c['key'],[x for x in common if not x.startswith('visible =')]+['visible = { RUS_np_context = yes has_variable = '+v+' '+ck(v,'<',3)+' }',
            'available = { has_variable = '+v+' '+ck(v,'<',3)+' '+' '.join(own(s) for s in c['states'])+' '+ck(P+'available','>',39)+' }','days_re_enable = 30',
            b('highlight_states',rail_highlight(c)).strip(),
            b('complete_effect',['custom_effect_tooltip = RUS_np_upgrade_rail_tt',
                b('effect_tooltip',['build_railway = { level = 3 '+path+' }']).strip(),
                'hidden_effect = { '+sub(P+'available',40)+' '+add(P+'spent',40)+' '+sv(v,3)+' build_railway = { level = 3 '+path+' } RUS_np_refresh = yes }']).strip()]))
    return ''.join(out)

def augment(out):
    text=out[DEC];cat=next(n for n in parse(text) if n.k==CAT);by={n.k:n for n in cat.v}
    edits=[]
    for p in PROJECTS:
        if p['legacy']:
            n=by[p['original_id']];e=n.one('visible')
            if e:edits.append((e.ia,e.ia,'\n NOT = { RUS_np_context = yes }\n'))
            else:edits.append((n.ib,n.ib,'\n visible = { RUS_np_context = no }\n'))
    appended='\n# RUS_NP_MANAGEMENT_BEGIN\n'+management()+''.join(patch_node(parse(p['original'])[0] if p['legacy'] else parse(new_node(p))[0],p)+'\n' for p in PROJECTS)+'# RUS_NP_MANAGEMENT_END\n'
    appended='\n'.join(line.rstrip() for line in appended.split('\n'))
    edits.append((cat.ib,cat.ib,appended))
    for a,z,s in sorted(edits,reverse=True):text=text[:a]+s+text[z:]
    out[DEC]=text
    triggers=[b('RUS_np_context',['original_tag = RUS','is_ai = no','has_socialist_government = yes','RUS_rc_stalin_phase = yes'])]
    triggers += [b('RUS_np_rural_candidate',[
        'is_core_of = RUS','is_owned_and_controlled_by = RUS',
        'NOT = { state = 219 } NOT = { state = 195 } NOT = { state = 217 }',
        'OR = { has_state_category = one has_state_category = two has_state_category = three has_state_category = four }',
        'infrastructure < 3','industrial_complex < 3','arms_factory < 3'])]
    for p in PROJECTS:
        condition=['RUS_np_context = yes','has_country_flag = RUS_np_initialized','NOT = { '+running(p)+' }',unfinished(p),owned(p),
            'custom_trigger_tooltip = { tooltip = RUS_np_budget_tt NOT = { '+ck(P+'available','<',p['budget'])+' } }',
            'custom_trigger_tooltip = { tooltip = RUS_np_slot_tt '+ck(P+'active','<',P+'slots')+' }',
            'custom_trigger_tooltip = { tooltip = RUS_np_trains_tt '+stock(p['trains'])+' }']
        triggers.append(b('RUS_np_ready_'+p['key'],condition))
    out['common/scripted_triggers/RUS_national_plan_triggers.txt']='\n'.join(line.rstrip() for line in ''.join(triggers).split('\n'))
    effects=[b('RUS_np_refresh',refresh())]
    effects.append(mio_effects())
    # One state pass at initialization, on score changes, or every 30 days for
    # newly acquired rural cores. No all-state scan from GUI visibility checks.
    rural=[sv(P+'rural_score',0),iff('has_variable = RUS_first_five_year_plan_score',[sv(P+'rural_score','RUS_first_five_year_plan_score')]),
        *clamp(P+'rural_score',0,150),sv(P+'rural_build_speed',P+'rural_score'),div(P+'rural_build_speed',150),mul(P+'rural_build_speed',.25),sub(P+'rural_build_speed',.2),
        sv(P+'rural_slots',P+'rural_score'),div(P+'rural_slots',150),mul(P+'rural_slots',.175),sub(P+'rural_slots',.15),
        sv(P+'rural_scan_age','global.num_days'),sub(P+'rural_scan_age',P+'rural_scan_day')]
    rural_state=['set_state_flag = RUS_np_rural_area',sv(P+'rural_build_speed','PREV.RUS_np_rural_build_speed'),
        sv(P+'rural_slots','PREV.RUS_np_rural_slots'),
        iff('NOT = { infrastructure < 5 }',[add(P+'rural_build_speed',.1),'set_state_flag = RUS_np_rural_infra_five']),
        b('else',['clr_state_flag = RUS_np_rural_infra_five']).strip(),
        iff('OR = { '+ck(P+'rural_build_speed','<',0)+' '+ck(P+'rural_slots','<',0)+' }',[
            iff('has_dynamic_modifier = { modifier = RUS_np_rural_infrastructure_improved }',['remove_dynamic_modifier = { modifier = RUS_np_rural_infrastructure_improved }']),
            iff('NOT = { has_dynamic_modifier = { modifier = RUS_np_rural_infrastructure } }',['add_dynamic_modifier = { modifier = RUS_np_rural_infrastructure }'])]),
        b('else',[
            iff('has_dynamic_modifier = { modifier = RUS_np_rural_infrastructure }',['remove_dynamic_modifier = { modifier = RUS_np_rural_infrastructure }']),
            iff('NOT = { has_dynamic_modifier = { modifier = RUS_np_rural_infrastructure_improved } }',['add_dynamic_modifier = { modifier = RUS_np_rural_infrastructure_improved }'])]).strip(),
        'force_update_dynamic_modifier = yes']
    rural += [iff('OR = { NOT = { has_variable = RUS_np_rural_cached_score } NOT = { '+ck(P+'rural_score','=',P+'rural_cached_score')+' } '+ck(P+'rural_scan_age','>',29)+' }',[
        sv(P+'rural_cached_score',P+'rural_score'),sv(P+'rural_scan_day','global.num_days'),
        b('every_owned_state',['limit = { OR = { has_state_flag = RUS_np_rural_area RUS_np_rural_candidate = yes } }','RUS_np_refresh_rural_state = yes']).strip()])]
    effects.append(b('RUS_np_refresh_rural_state',rural_state))
    effects.append(b('RUS_np_refresh_rural',[iff('original_tag = RUS has_country_flag = RUS_np_rural_enabled',rural)]))
    # Startup must not depend on whether player ownership is settled yet.
    effects.append(b('RUS_np_initialize_rural',[iff('tag = RUS NOT = { has_country_flag = RUS_np_rural_enabled }',[
        'set_country_flag = RUS_np_rural_enabled','RUS_np_refresh_rural = yes'])]))
    effects.append(b('RUS_np_rural_daily',['RUS_np_initialize_rural = yes','RUS_np_refresh_rural = yes',
        iff('has_country_flag = RUS_np_rural_enabled '+ck(P+'rural_infra_day','<','global.num_days'),[
            sv(P+'rural_infra_day','global.num_days'),b('every_owned_state',[
                'limit = { has_state_flag = RUS_np_rural_area OR = { AND = { NOT = { infrastructure < 5 } NOT = { has_state_flag = RUS_np_rural_infra_five } } AND = { infrastructure < 5 has_state_flag = RUS_np_rural_infra_five } } }',
                'RUS_np_refresh_rural_state = yes']).strip()])]))
    defaults=[iff('NOT = { has_variable = '+v+' }',[sv(v,x)]) for v,x in [('RUS_ic_cost_low',20),('RUS_ic_cost_med',40),('RUS_ic_cost_high',60),('RUS_ic_time_60',60),('RUS_ic_time_120',120)]]
    init=['RUS_np_initialize_rural = yes','set_country_flag = RUS_np_initialized',*defaults,sv(P+'available',0),sv(P+'frozen',0),sv(P+'spent',0),sv(P+'filter',0),sv(P+'year','year'),sv(P+'farm_credit',0),sv(P+'day','global.num_days'),sub(P+'day',1),'RUS_np_refresh = yes',
        sv(P+'fraction','global.num_days'),op('modulo',P+'fraction',365),mul(P+'fraction',-1),add(P+'fraction',365),div(P+'fraction',365),sv(P+'initial_grant',P+'grant'),mul(P+'initial_grant',P+'fraction'),add(P+'available',P+'initial_grant')]
    # The deficit is explicitly local. Three bounded improvements clear it and
    # establish the positive tier; initialization cannot reapply it later.
    for s in (219,195,217):init += [iff(own(s),[scope(s,[sv('RUS_np_development',0),'add_dynamic_modifier = { modifier = RUS_np_region_0 }'])])]
    effects.append(b('RUS_np_initialize',[iff('RUS_np_context = yes NOT = { has_country_flag = RUS_np_initialized }',init)]))
    daily=[sv(P+'day','global.num_days'),'RUS_np_refresh = yes',
        iff(ck(P+'year','<','year'),[sv(P+'year','year'),add(P+'available',P+'grant')]),add(P+'available',P+'income')]
    for p in PROJECTS:
        daily += [iff(running(p),[
            iff('NOT = { '+owned(p)+' }',[remove_active(p),call(p,'cancel')]),
            b('else',[call(p,'tick'),iff(ck(var(p,'left'),'<',.001),[sv(P+'adjust','days_decision_timeout@'+p['id']),mul(P+'adjust',-1),call(p,'apply_timer_delta')]),b('else',[call(p,'timer')]).strip()]).strip()])]
    daily += ['RUS_np_refresh_transport = yes','RUS_np_refresh = yes']
    effects.append(b('RUS_np_daily',[iff('RUS_np_context = yes',['RUS_np_initialize = yes',iff(ck(P+'day','<','global.num_days'),daily)]),b('else',[iff('has_country_flag = RUS_np_initialized',[
        iff(running(p),[remove_active(p),call(p,'cancel')]) for p in PROJECTS]+[
        equip(P+c+'_dispatch')+' '+sv(P+c+'_dispatch',0) for c in ('moscow','leningrad','tsaritsyn')]+['RUS_np_refresh_transport = yes'])]).strip()]))
    transport=[sv(P+'transport_bonus',0)]
    for city,state in [('moscow',219),('leningrad',195),('tsaritsyn',217)]:
        v=P+city+'_dispatch';end=195 if state==219 else state
        transport += [iff(ck(v,'>',0)+' '+own(state)+f' has_railway_connection = {{ start_state = 219 target_state = {end} }}',[add(P+'transport_bonus',.01)])]
    transport += [iff(ck(P+'transport_bonus','>',0),['add_dynamic_modifier = { modifier = RUS_np_transport_network }']),b('else',['remove_dynamic_modifier = { modifier = RUS_np_transport_network }']).strip(),'RUS_np_refresh = yes','force_update_dynamic_modifier = yes']
    effects.append(b('RUS_np_refresh_transport',transport))
    effects.extend(project_effects(p) for p in PROJECTS)
    agri=[sv(P+'delivery',P+'farm_rate'),add(P+'delivery',P+'farm_credit'),
        sv(P+'room','RUS_nat_target'),sub(P+'room','RUS_nat_installed'),add(P+'room',5000),sub(P+'room','RUS_nat_machine_stock'),*clamp(P+'room',0,1001000),
        *clamp(P+'delivery',0,P+'room'),sv(P+'credit_used',P+'delivery'),sub(P+'credit_used',P+'farm_rate'),*clamp(P+'credit_used',0,P+'farm_credit'),sub(P+'farm_credit',P+'credit_used'),
        add('RUS_nat_machine_stock',P+'delivery'),add('RUS_nat_produced',P+'delivery')]
    effects.append(b('RUS_np_agri_delivery',[iff('has_country_flag = RUS_np_initialized '+ck(P+'agri_day','<','global.num_days'),[sv(P+'agri_day','global.num_days'),*agri])]))
    effects.append(b('RUS_np_award_education',['custom_effect_tooltip = RUS_np_education_award_tt',b('hidden_effect',[
        iff('has_country_flag = RUS_education_system_active',[add('RUS_basic_education_level',1),add('RUS_higher_education_level',.5),'RUS_education_refresh = yes'])]).strip()]))
    effects.append(b('RUS_np_award_resources',['custom_effect_tooltip = RUS_np_resources_award_tt',
        'hidden_effect = { '+add(P+'available',15)+' '+add(P+'bonus_resources',15)+' }']))
    effects.append(b('RUS_np_award_land_score',['custom_effect_tooltip = RUS_np_land_award_tt',b('hidden_effect',[
        sv('RUS_agri_score_award',5),'RUS_agri_credit_score = yes','RUS_nat_refresh = yes']).strip()]))
    out[FX]='# Generated national plan. Legacy score/spirit functions are not modified.\n'+''.join(effects)
    out[FX]='\n'.join(line.rstrip() for line in out[FX].split('\n'))
    dm=[b('RUS_np_transport_network',['enable = { RUS_np_context = yes }','production_speed_buildings_factor = RUS_np_transport_bonus','industrial_capacity_factory = RUS_np_transport_bonus'])]
    for key in ('RUS_np_rural_infrastructure','RUS_np_rural_infrastructure_improved'):
        dm.append(b(key,['icon = GFX_modifiers_PRC_rural_development',
            'enable = { is_core_of = RUS owner = { tag = RUS has_country_flag = RUS_np_rural_enabled } controller = { tag = RUS } }',
            'state_production_speed_buildings_factor = RUS_np_rural_build_speed','local_building_slots_factor = RUS_np_rural_slots']))
    for i,mods in [(0,{'state_production_speed_buildings_factor':-.05,'local_building_slots_factor':-.05}),(1,{'state_production_speed_buildings_factor':-.025}),(3,{'state_production_speed_buildings_factor':.05,'local_building_slots_factor':.05})]:
        dm.append(b(P+'region_'+str(i),['enable = { owner = { original_tag = RUS } controller = { original_tag = RUS } }',*[f'{m} = {v}' for m,v in mods.items()]]))
    for p in PROJECTS:
        if not (p['civ'] or p['consumer']):continue
        fields=['enable = { '+running(p)+' }']
        if p['civ']:fields.append(f'civilian_factory_use = {p["civ"]}')
        if p['consumer']:fields.append(f'consumer_goods_factor = {p["consumer"]}')
        dm.append(b(var(p,'cost'),fields))
    out[DM]=''.join(dm)
    out['common/on_actions/RUS_national_plan_on_actions.txt']='on_actions = {\n on_startup = { effect = { RUS = { RUS_np_initialize_rural = yes } } }\n on_daily_RUS = { effect = { RUS_np_rural_daily = yes RUS_np_daily = yes } }\n}\n'
    out['common/synchronized_dynamic_tokens/RUS_national_plan_tokens.txt']='\n'.join(p['id'] for p in PROJECTS)+'\n'
    out.update(localisations())
    # Human-reviewable 62-row ledger generated from the same runtime catalogue.
    columns=['ID','原工程ID','地区分类','目标地区','基准工期','建设资源','征用普通列车','额外占用民工','额外消费品系数','追加目标1','追加目标2','一五计分','历史来源','军工机构追加奖励']
    rows=['\t'.join(columns)]
    for p in PROJECTS:
        values=[p['id'],p.get('original_id','新增'),REGIONS[p['region']],','.join(map(str,p['states'])),p['base_days'],p['budget'],p['trains'],p['civ'],p['consumer'],goals(p)[0][1],goals(p)[1][1],'原奖励原值' if p['legacy'] else '0',p.get('source','原版工程')]
        award=MIO_REWARDS.get(p['key']);values.append(('航空军工协作：选择在用机构，经费获取+25%' if award[0]=='consortium' else MIO_TARGETS[award[0]][3]+'：规模+1') if award else '无')
        rows.append('\t'.join(map(str,values)))
    out['tools/design/national_plan_20261104/projects.tsv']='\n'.join(rows)+'\n'
    return out

def localisations():
    l={'RUS_np_open_account':'建立国家建设账本','RUS_np_open_account_desc':'统筹国家建设资源，批准工业与交通工程。',
       'RUS_np_budget_tt':'§C建设资源§!充足','RUS_np_slot_tt':'存在空闲工程名额','RUS_np_trains_tt':'普通列车库存满足征用要求','RUS_np_stage_tt':'一五计划达到第一阶段',
       'RUS_np_bonus_summary':'追加目标在期限内达成后记录资格，随工程正常竣工结算。','RUS_np_upgrade_rail_tt':'消耗§C建设资源§!：§R40§!',
       'RUS_np_transport_network':'工业区运输网络','RUS_np_region_0':'工业区配套不足Ⅱ','RUS_np_region_1':'工业区配套不足Ⅰ','RUS_np_region_3':'工业区配套完善Ⅰ',
       'RUS_np_header':'§C建设资源：[?RUS_np_available|2]§!　冻结：§Y[?RUS_np_frozen|2]§!　§g已消耗：[?RUS_np_spent|2]§!\\n每日收入：§G+[?RUS_np_income|2]§!　工程名额：[?RUS_np_active|0]/[?RUS_np_slots|0]　征用列车：[?RUS_np_trains|0]\\n计划干线平均等级：§Y[?RUS_np_rail_display|2]§!',
       'RUS_np_header_old':'这些决议将§G促进§!我们的§C经济复苏§!。',
       'RUS_np_unlocked':'§G已达成§!','RUS_np_pending':'§Y未达成§!','RUS_np_claimed':'§g已领取§!'}
    l['RUS_np_terminate_tt']='终止工程，结算已用建设资源并返还余款及施工列车。政治点不返还，不获得竣工奖励。'
    l['RUS_np_rural_infrastructure']='落后的基础设施'
    l['RUS_np_rural_infrastructure_desc']=''
    l['RUS_np_rural_infrastructure_improved']='改善的基础设施'
    l['RUS_np_rural_infrastructure_improved_desc']=''
    l['RUS_np_mio_consortium_award_tt']='获得一次航空军工协作成果。可选择一个正在承担研究或生产任务的航空军工机构，经费获取增加§G25%§!。'
    l['RUS_np_redeem_mio_consortium']='分配航空工业协作成果'
    l['RUS_np_redeem_mio_consortium_desc']='$RUS_aat_consortium_tt$'
    for key,(_,_,_,name) in MIO_TARGETS.items():
        l[P+'redeem_mio_'+key]='兑现'+name+'扩建成果'
        l[P+'redeem_mio_'+key+'_desc']='对应军工机构可用后兑现扩建成果。已整合的企业由其设计总局承接。'
    l['RUS_np_education_award_tt']='£RUS_edu_basic_texticon£ §C基础教育水平§!：§G+1.00§!\\n£RUS_edu_higher_texticon£ §Y高等教育水平§!：§G+0.50§!'
    l['RUS_np_resources_award_tt']='§C建设资源§!：§G+15.00§!'
    l['RUS_np_land_award_tt']='土地改革分数：§G+5§!'
    l['RUS_np_farm_credit_tt']='农业建设获得§G100§!单位农机。'
    l['RUS_np_fertilizer_reward_tt']='小麦、黑麦与甜菜产量：§G+3.00%§!'
    l['RUS_np_rural_reward_tt']='每日农机供应：§G+2§!\\n农机损耗率：§G-1.00%§!'
    l['RUS_np_header']='当前分类：[RUSNPRegionName]\\n'+l['RUS_np_header']
    sloc=[b('defined_text',['name = RUSNationalPlanLedger',b('text',['trigger = { RUS_np_context = yes }','localization_key = RUS_np_header']).strip(),'text = { localization_key = RUS_np_header_old }'])]
    sloc.append(b('defined_text',['name = RUSNPRegionName',*[b('text',['trigger = { check_variable = { RUS_np_filter = '+str(i)+' } }','localization_key = RUS_np_region_name_'+str(i)]).strip() for i in range(1,7)],'text = { localization_key = RUS_np_region_name_0 }']))
    for i in range(7):l[P+'region_name_'+str(i)]=REGIONS.get(i,'全部地区')
    for i in range(7):l[P+'filter_'+str(i)]='查看：'+REGIONS.get(i,'全部地区')
    for c in CORRIDORS:l[P+'upgrade_'+c['key']]='升级计划干线：'+c['label']
    for city,name in [('moscow','莫斯科'),('leningrad','列宁格勒'),('tsaritsyn','察里津')]:
        l[P+city+'_dispatch']='加强'+name+'工业区运输';l[P+city+'_recall']='撤回'+name+'运输列车'
        l[P+city+'_dispatch_desc']='征用10列普通列车。铁路保持连通时，扩大工业区运输与工业协作收益。'
        l[P+city+'_recall_desc']='返还本工业区投入运输的列车，解除对应运输加成。'
    for p in PROJECTS:
        l[var(p,'cost')]='工程建设投入'
        l[var(p,'cost_tt')]=f'冻结§C建设资源§!：§Y{p["budget"]}§!'+(f'\\n征用普通列车：§Y{p["trains"]}§!' if p['trains'] else '')+'\\n正常竣工返还未使用的20%§C建设资源§!'+('及全部施工列车。' if p['trains'] else '。')
        l[p['id']]=('$'+p['original_id']+'$') if p['legacy'] else p['name']
        l[var(p,'terminate')]='终止工程：$'+p['id']+'$'
        l[var(p,'terminate')+'_desc']='$RUS_np_terminate_tt$'
        parts=([p['intro'],''] if p.get('intro') else [])+['$'+var(p,'cost_tt')+'$','追加目标：']
        for i,(_,name,_) in enumerate(goals(p),1):
            helper='RUSNPGoal_'+p['key']+'_'+str(i)
            parts.append(f'{name}：[{helper}]')
            l[var(p,'goal_'+str(i)+'_tt')]=f'追加目标：{name}（[{helper}]）'
            sloc.append(b('defined_text',['name = '+helper,b('text',['trigger = { '+flag(p,'completed')+' }','localization_key = RUS_np_claimed']).strip(),b('text',['trigger = { '+flag(p,'goal_'+str(i))+' }','localization_key = RUS_np_unlocked']).strip(),'text = { localization_key = RUS_np_pending }']))
        l[var(p,'description')]='\\n'.join(parts)
        l[p['id']+'_desc']='$'+var(p,'description')+'$'
    out={'common/scripted_localisation/RUS_national_plan_loc.txt':''.join(sloc)}
    for lang in ('simp_chinese','english','russian'):
        out[f'localisation/{lang}/RUS_national_plan_l_{lang}.yml']='l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v.replace('\\n','\n'),ensure_ascii=False)+'\n' for k,v in l.items())
    out['localisation/replace/RUS_national_plan_category_l_simp_chinese.yml']='l_simp_chinese:\n RUS_first_five_year_plan_industrial_projects_desc:0 "[RUSNationalPlanLedger]"\n'
    return out
