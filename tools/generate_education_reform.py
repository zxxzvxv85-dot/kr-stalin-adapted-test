"""Education system source. Default/--check are read-only; --write is explicit.

Reference: vanilla sov_propaganda_campaigns_scripted_gui(.gui/.txt), KR Russia
dynamic modifiers and decision effect_tooltip usage. No new event is created.
"""
from __future__ import annotations
import argparse
import io
import json
import hashlib
from pathlib import Path
from education_reform_content import (ACTIVITIES, CONTROLS, BODY, POOL_CAPS, KINDS, POSTER_CATEGORIES,
    HEAT_ECONOMIC_MODIFIERS, HEAT_WEEKLY_STABILITY_THRESHOLD, HEAT_WEEKLY_STABILITY_MAX_LOSS,EDUCATION_GAIN_CAPS,
    HEAT_QUALITY_CURVATURE,HEAT_STABILITY_PRESSURE,HEAT_POLITICAL_PRESSURE)
from education_poster_expansion import (MILITARY_GATE, AGRICULTURE_GATE, STATE_REWARDS, CATEGORY_ICONS)

ROOT = Path(__file__).resolve().parents[1]
DESIGN = Path('tools/design/education_system_20261024')
FX = Path('common/scripted_effects/RUS_stalin_education_reform_effects.txt')
DEC = Path('common/decisions/RUS stalin education reform decisions.txt')
DM = Path('common/dynamic_modifiers/RUS_education_continuous_modifiers.txt')
GUI = Path('interface/RUS_education_dashboard.gui')
SGUI = Path('common/scripted_guis/RUS_education_dashboard.txt')
GFX = Path('interface/RUS_education_dashboard.gfx')
ART = Path('gfx/interface/RUS_education')
VARS = {'basic':'RUS_basic_education_level','higher':'RUS_higher_education_level','heat':'RUS_education_enthusiasm'}

def block(key, lines):
    return key+' = {\n'+''.join('\t'+line+'\n' for line in lines)+'}\n\n'

def op(kind,var,val,temp=False):
    return f'{kind}_{"temp_" if temp else ""}variable = {{ {var} = {val} }}'

def setv(var,val): return op('set',var,val)
def add(var,val): return op('add_to',var,val)
def mul(var,val): return op('multiply',var,val)
def clamp(var,low,high):
    return [f'if = {{ limit = {{ check_variable = {{ {var} < {low} }} }} {setv(var,low)} }}',
            f'if = {{ limit = {{ check_variable = {{ {var} > {high} }} }} {setv(var,high)} }}']
def cond(condition,lines): return ['if = {','\tlimit = { '+condition+' }']+['\t'+s for s in lines]+['}']
def pv(mod): return 'RUS_edu_permanent_'+mod
def bv(mod): return 'RUS_edu_body_'+mod
def delta(a,mod): return 'RUS_edu_reward_'+a['id']+'_'+mod
def active(a): return 'RUS_edu_running_'+a['id']
def remain(a): return 'RUS_edu_days_'+a['id']

def repeated(a): return 'RUS_edu_repeated_'+a['id']

def repeat_condition(a):
    return 'has_country_flag = RUS_edu_central has_country_flag = RUS_edu_completed_'+a['id']

def category_requirements(a):
    # The drawing opens social/life posters at entry and economic posters with
    # professional training. Retain earlier cultural access as an alternative.
    if a['category']==2:
        if a['kind']=='culture':
            return ['OR = { has_country_flag = RUS_edu_technical_open has_country_flag = RUS_edu_culture_open }']
        return ['has_country_flag = RUS_edu_technical_open']
    if a['category'] in (3,5):return []
    if a['kind'] in ('higher','culture'):return ['has_country_flag = RUS_edu_culture_open']
    if a['kind']=='technical':return ['has_country_flag = RUS_edu_technical_open']
    return []

def access_requirements(a):
    rows=category_requirements(a)
    if a['kind']=='higher':rows.append('NOT = { check_variable = { RUS_basic_education_level < 35 } }')
    if a.get('gate'):rows.append(a['gate'])
    if a.get('wartime'):rows.append('has_war = yes')
    if a.get('state_reward'):
        state=a['state_reward']['state'];rows.extend([f'owns_state = {state}',f'controls_state = {state}'])
    return rows

def state_reward_effects(a):
    reward=a.get('state_reward')
    if not reward:return []
    state=reward['state'];modifier='RUS_edu_state_'+reward['preset']
    return cond(f'owns_state = {state} controls_state = {state}',[
        f'{state} = {{ add_dynamic_modifier = {{ modifier = {modifier} days = {reward["days"]} }} }}'])

def timed_reward_effects(a):
    reward=a.get('timed_reward')
    return [f'add_timed_idea = {{ idea = {reward["idea"]} days = {reward["days"]} }}'] if reward else []

def agriculture_reward_effects(a):
    reward=a.get('agriculture_reward')
    if not reward:return []
    if reward in ('wheat','rye'):
        body=[add('RUS_nat_'+reward+'_stock',4 if reward=='wheat' else 3)]+clamp('RUS_nat_'+reward+'_stock',0,12)
    elif reward=='technical':body=[setv('RUS_nat_technical_support',1)]
    else:body=cond('check_variable = { RUS_nat_repair_support < 0.05 }',[setv('RUS_nat_repair_support',.05)])
    return cond(AGRICULTURE_GATE,body+['RUS_nat_refresh = yes'])

def decision_icon(a):
    if a['kind']=='control':return 'GFX_decision_generic_political_discourse' if a['id']=='listen' else 'GFX_decision_generic_police_action'
    if a.get('agriculture_reward') or a['id']=='agriculture':return 'GFX_decision_generic_agriculture'
    if a['id']=='lenin_electrification':return 'GFX_decision_generic_electricity'
    if a['kind']=='higher':return 'GFX_decision_SOV_academy_of_sciences'
    return CATEGORY_ICONS[a['category']]

def effects():
    out=['# Generated by tools/generate_education_reform.py --write\n']
    init=['set_country_flag = RUS_education_system_active','set_country_flag = RUS_education_reform_started',
          'remove_ideas = RUS_malformed_education_system',setv(VARS['basic'],46),setv(VARS['higher'],7),setv(VARS['heat'],32),
          setv('RUS_education_completed_activities',0),setv('RUS_edu_active_count',0),setv('RUS_edu_slots',2),
          setv('RUS_education_overheat_days',0),setv('RUS_edu_category',4),
          setv('RUS_edu_mass_phase',0),setv('RUS_edu_mass_days',0)]
    for m in POOL_CAPS: init.append(setv(pv(m),0))
    # Explicit public interfaces: additive education/enthusiasm and reserved political pressure.
    for v in ['RUS_edu_external_basic_gain','RUS_edu_external_higher_gain','RUS_edu_external_heat_change','RUS_edu_external_pressure']:
        init.append(setv(v,0))
    for i in range(1,4): init += [setv(f'RUS_edu_slot_{i}',0),setv(f'RUS_edu_slot_{i}_frame',2)]
    init += ['RUS_education_refresh = yes','add_dynamic_modifier = { modifier = RUS_education_social_capacity }']
    out.append(block('RUS_education_initialize',cond('NOT = { has_country_flag = RUS_education_system_active }',init)))
    # Old upstream focuses may still call this, but cannot open the new system early.
    out.append(block('RUS_education_reform_start',cond('has_completed_focus = RUS_future_domestic_205',['RUS_education_initialize = yes'])))
    out.append(block('RUS_education_start_mass_campaign',cond('NOT = { has_country_flag = RUS_edu_mass_campaign_started }',[
        'set_country_flag = RUS_edu_mass_campaign_started',setv('RUS_edu_mass_phase',1),setv('RUS_edu_mass_days',180),
        'add_timed_idea = { idea = RUS_education_mass_hesitation days = 180 }','RUS_education_refresh = yes'])))
    # One branch per day: 180 hesitation pulses, then 180 enthusiasm pulses.
    mass=cond('check_variable = { RUS_edu_mass_phase = 1 }',[
        add(VARS['heat'],-.15),op('subtract_from','RUS_edu_mass_days',1),
        *cond('NOT = { check_variable = { RUS_edu_mass_days > 0 } }',[
            'remove_ideas = RUS_education_mass_hesitation',setv('RUS_edu_mass_phase',2),setv('RUS_edu_mass_days',180),
            'add_timed_idea = { idea = RUS_education_mass_enthusiasm days = 180 }'])])
    mass+=['else_if = {','\tlimit = { check_variable = { RUS_edu_mass_phase = 2 } }',
        '\t'+add(VARS['heat'],.05),'\t'+op('subtract_from','RUS_edu_mass_days',1),
        *['\t'+s for s in cond('NOT = { check_variable = { RUS_edu_mass_days > 0 } }',[
            'remove_ideas = RUS_education_mass_enthusiasm',setv('RUS_edu_mass_phase',0),setv('RUS_edu_mass_days',0)])],'}']
    out.append(block('RUS_education_mass_daily',mass))
    out.append(block('RUS_education_refresh',refresh_lines()))
    daily=['RUS_education_refresh = yes',add(VARS['heat'],-.1),'RUS_education_mass_daily = yes']
    for a in ACTIVITIES: daily += cond('has_country_flag = '+active(a),['RUS_education_tick_'+a['id']+' = yes'])
    for a in CONTROLS:
        daily += cond('has_country_flag = '+active(a),[op('subtract_from',remain(a),1)]+clamp(remain(a),0,a['days']))
    daily += [add(VARS['basic'],'RUS_edu_external_basic_gain'),add(VARS['higher'],'RUS_edu_external_higher_gain'),
              add(VARS['heat'],'RUS_edu_external_heat_change')]
    daily += cond(f'check_variable = {{ RUS_education_enthusiasm > {HEAT_WEEKLY_STABILITY_THRESHOLD} }}',[add('RUS_education_overheat_days',1)])
    daily += ['else = { '+setv('RUS_education_overheat_days',0)+' }','RUS_education_refresh = yes']
    out.append(block('RUS_education_daily',daily))
    for index,a in enumerate(ACTIVITIES+CONTROLS,1):
        regular=a['kind']!='control'; code=index+2
        req=f'has_country_flag = RUS_education_system_active NOT = {{ has_country_flag = {active(a)} }} NOT = {{ has_country_flag = RUS_edu_cooldown_{a["id"]} }}'
        if regular:
            req+=f' check_variable = {{ RUS_edu_active_count < RUS_edu_slots }} NOT = {{ has_country_flag = RUS_edu_busy_{a["kind"]} }}'
            req+=' '+' '.join(access_requirements(a))
        else: req+=' NOT = { has_country_flag = RUS_edu_control_busy }'
        begin=['set_country_flag = '+active(a),setv(remain(a),a['days'])]
        if regular:
            begin += cond(repeat_condition(a),['set_country_flag = '+repeated(a),
                f'add_dynamic_modifier = {{ modifier = RUS_edu_repeat_{a["id"]} days = {a["days"]} }}'])
            begin += ['set_country_flag = RUS_edu_busy_'+a['kind'],add('RUS_edu_active_count',1)]
            for i in range(1,4):
                begin += [('if' if i==1 else 'else_if')+' = {',f'\tlimit = {{ check_variable = {{ RUS_edu_slot_{i} = 0 }} }}',
                          '\t'+setv(f'RUS_edu_slot_{i}',code),'}']
        else: begin+=['set_country_flag = RUS_edu_control_busy']
        begin+=['RUS_education_refresh = yes']
        out.append(block('RUS_education_begin_'+a['id'],cond(req,begin)))
        if regular:
            tick=[]
            for kind in ('basic','higher'):
                if a[kind]:
                    tick += [setv('RUS_edu_gain',f'{a[kind]/a["days"]:.12g}'),mul('RUS_edu_gain','RUS_edu_quality'),
                             mul('RUS_edu_gain','RUS_edu_'+kind+'_multiplier')]
                    tick += mul_if('RUS_edu_gain',repeated(a),1.5)
                    # Limit after every multiplier. At most `days` daily pulses
                    # can execute, including the guarded final-day top-up.
                    tick += clamp('RUS_edu_gain',0,f'{EDUCATION_GAIN_CAPS[kind]/a["days"]:.12g}')
                    tick += [add(VARS[kind],'RUS_edu_gain')]
            if a['heat']:
                tick += [setv('RUS_edu_heat_gain',f'{a["heat"]/30:.12g}')]
                if a['heat']>0:
                    tick += mul_if('RUS_edu_heat_gain','RUS_edu_central',1.25)
                    if a['kind']=='culture': tick+=mul_if('RUS_edu_heat_gain','RUS_edu_amateur',.75)
                tick += mul_if('RUS_edu_heat_gain',repeated(a),1.5)
                tick += [add(VARS['heat'],'RUS_edu_heat_gain')]
            tick += [op('subtract_from',remain(a),1)]
            out.append(block('RUS_education_tick_'+a['id'],cond('has_country_flag = '+active(a)+' check_variable = { '+remain(a)+' > 0 }',tick)))
        release=['clr_country_flag = '+active(a)]
        if regular:
            release += ['clr_country_flag = '+repeated(a),
                        f'remove_dynamic_modifier = {{ modifier = RUS_edu_repeat_{a["id"]} }}']
            release += ['clr_country_flag = RUS_edu_busy_'+a['kind'],op('subtract_from','RUS_edu_active_count',1)]
            for i in range(1,4): release+=cond(f'check_variable = {{ RUS_edu_slot_{i} = {code} }}',[setv(f'RUS_edu_slot_{i}',0)])
        else: release+=['clr_country_flag = RUS_edu_control_busy']
        release += [setv(remain(a),0),f'set_country_flag = {{ flag = RUS_edu_cooldown_{a["id"]} days = {90 if regular else 60} }}',
                    'RUS_education_refresh = yes']
        out.append(block('RUS_education_cancel_'+a['id'],cond('has_country_flag = '+active(a),release)))
        finish=[]
        if regular:
            # An expiry callback may precede the last daily pulse. Top up only one day.
            finish += ['RUS_education_tick_'+a['id']+' = yes',add('RUS_education_completed_activities',1),
                       'set_country_flag = RUS_edu_completed_'+a['id']]
        else: finish += [add(VARS['heat'],a['heat'])]
        for m,v in a['permanent_modifiers'].items():finish.append(add(pv(m),f'{v:.12g}'))
        finish+=state_reward_effects(a)+timed_reward_effects(a)+agriculture_reward_effects(a)
        finish += ['RUS_education_cancel_'+a['id']+' = yes']
        out.append(block('RUS_education_finish_'+a['id'],cond('has_country_flag = '+active(a),finish)))
    # Existing culture events keep their public entry points, award bounded education gains,
    # and cannot start education or grant infinite old fixed bonuses before the entrance.
    for name,b,h,t in [('new_culture_popularisation',2,0,3),('new_culture_elite_art',0,2,-2),('revolutionary_realism',1,1,1),('revolutionary_romanticism',0,3,2)]:
        out.append(block('RUS_education_reform_effect_'+name,[f'custom_effect_tooltip = RUS_edu_legacy_{name}_tt',
            'hidden_effect = {']+['\t'+s for s in cond('has_country_flag = RUS_education_system_active',[add(VARS['basic'],b),add(VARS['higher'],h),add(VARS['heat'],t),'RUS_education_refresh = yes'])]+['}']))
    return '\n'.join(out).rstrip()+'\n'

def mul_if(v,flag,n): return cond('has_country_flag = '+flag,[mul(v,n)])

def refresh_lines():
    lines=[]
    for v in VARS.values(): lines+=clamp(v,0,100)
    for m,cap in POOL_CAPS.items(): lines+=clamp(pv(m),min(0,cap),max(0,cap))
    # Curves are continuous at 55; state variables are never rounded for gameplay.
    lines += [setv('RUS_edu_deviation',VARS['heat']),op('subtract_from','RUS_edu_deviation',55),
        'if = { limit = { check_variable = { RUS_education_enthusiasm > 55 } } divide_variable = { RUS_edu_deviation = 45 } }',
        'else = { divide_variable = { RUS_edu_deviation = 55 } }',setv('RUS_edu_heat_square','RUS_edu_deviation'),mul('RUS_edu_heat_square','RUS_edu_deviation'),
        setv('RUS_edu_quality_denominator','RUS_edu_heat_square'),mul('RUS_edu_quality_denominator',HEAT_QUALITY_CURVATURE),
        add('RUS_edu_quality_denominator',1),setv('RUS_edu_quality',1),op('divide','RUS_edu_quality','RUS_edu_quality_denominator'),
        setv('RUS_edu_quality_penalty',1),op('subtract_from','RUS_edu_quality_penalty','RUS_edu_quality'),
        setv('RUS_edu_overheat',0)]
    lines+=cond('check_variable = { RUS_education_enthusiasm > 55 }',[setv('RUS_edu_overheat','RUS_edu_heat_square')])
    for kind,initial,span in [('basic',20,80),('higher',5,95)]:
        n='RUS_edu_progress_'+kind
        lines += [setv(n,VARS[kind]),op('subtract_from',n,initial),op('divide',n,span)]+clamp(n,0,1)
        lines += [setv('RUS_edu_'+kind+'_multiplier',1)]
        if kind=='basic': lines+=mul_if('RUS_edu_basic_multiplier','RUS_edu_practice',1.2)
        else:
            lines+=mul_if('RUS_edu_higher_multiplier','RUS_edu_theory',1.2)
            lines+=mul_if('RUS_edu_higher_multiplier','RUS_edu_future',1.2)
        lines += mul_if('RUS_edu_'+kind+'_multiplier','RUS_edu_amateur',1.1)
        lines += cond('has_idea = RUS_mikhail_kalinin_advisor',[mul('RUS_edu_'+kind+'_multiplier',1.2)])
    # Only the two positive efficiency bonuses follow mobilisation. Education
    # deficits do not become bonuses through enthusiasm alone; upper caps stay fixed.
    lines += [setv('RUS_edu_economic_mobilisation',VARS['heat']),mul('RUS_edu_economic_mobilisation',.005),add('RUS_edu_economic_mobilisation',.5)]
    for m,(lo,hi,w) in BODY.items():
        lines += [setv('RUS_edu_weighted','RUS_edu_progress_basic'),mul('RUS_edu_weighted',w),
                  setv('RUS_edu_other','RUS_edu_progress_higher'),mul('RUS_edu_other',f'{1-w:.12g}'),add('RUS_edu_weighted','RUS_edu_other'),setv(bv(m),'RUS_edu_weighted')]
        if m not in HEAT_ECONOMIC_MODIFIERS:lines += [mul(bv(m),'RUS_edu_quality')]
        lines += [mul(bv(m),f'{hi-lo:.12g}'),add(bv(m),lo)]
        if m in HEAT_ECONOMIC_MODIFIERS:
            lines += cond(f'check_variable = {{ {bv(m)} > 0 }}',[mul(bv(m),'RUS_edu_economic_mobilisation')])
        # Positive civic participation grows with education, preserving the -10% floor at zero progress.
        if m=='political_power_factor':
            lines += [setv('RUS_edu_other','RUS_edu_quality_penalty'),mul('RUS_edu_other',-HEAT_POLITICAL_PRESSURE),add('RUS_edu_other',.05),
                      mul('RUS_edu_other','RUS_edu_weighted'),add(bv(m),'RUS_edu_other')]
    lines += [setv(bv('stability_factor'),'RUS_edu_quality_penalty'),mul(bv('stability_factor'),-HEAT_STABILITY_PRESSURE),
              setv(bv('industrial_capacity_factory'),VARS['heat']),mul(bv('industrial_capacity_factory'),.0005),
              setv(bv('stability_weekly'),0),
              setv('RUS_edu_quality_percent','RUS_edu_quality'),mul('RUS_edu_quality_percent',100),
              setv('RUS_edu_slots',2)]
    lines += cond(f'check_variable = {{ {VARS["heat"]} > {HEAT_WEEKLY_STABILITY_THRESHOLD} }}',[
        setv('RUS_edu_weekly_pressure',VARS['heat']),op('subtract_from','RUS_edu_weekly_pressure',HEAT_WEEKLY_STABILITY_THRESHOLD),
        op('divide','RUS_edu_weekly_pressure',100-HEAT_WEEKLY_STABILITY_THRESHOLD),
        setv(bv('stability_weekly'),'RUS_edu_weekly_pressure'),mul(bv('stability_weekly'),'RUS_edu_weekly_pressure'),
        mul(bv('stability_weekly'),-HEAT_WEEKLY_STABILITY_MAX_LOSS)])
    # Recompute the body first, then add the bounded persistent contributions.
    # Never add onto yesterday's combined values, or repeated refreshes would stack.
    lines += [setv(bv('political_power_cost'),0)]
    for m in POOL_CAPS:lines += [add(bv(m),pv(m))]
    lines += cond('has_dynamic_modifier = { modifier = RUS_education_permanent_results }',
                  ['remove_dynamic_modifier = { modifier = RUS_education_permanent_results }'])
    lines+=cond('has_country_flag = RUS_edu_culture_open',[setv('RUS_edu_slots',3)])
    for a in ACTIVITIES+CONTROLS:
        v='RUS_edu_cost_'+a['id']; lines+=[setv(v,a['cost'])]
        if a['kind']!='control':
            lines+=mul_if(v,'RUS_edu_central',.8)
            lines+=mul_if(v,'RUS_edu_amateur',.5)
            lines+=mul_if(v,'RUS_edu_era',.75)
            lines+=cond(repeat_condition(a),[mul(v,1.5)])
        for m,award in a['permanent_modifiers'].items():
            v=delta(a,m)
            lines += [setv(v,POOL_CAPS[m]),op('subtract_from',v,pv(m))]+clamp(v,min(0,award),max(0,award))
    for kind in VARS:
        v='RUS_edu_bar_'+kind
        lines += [setv(v,VARS[kind]),f'round_variable = {v}',add(v,1)]
    for i in range(1,4):
        lines += [setv(f'RUS_edu_slot_{i}_frame',2),setv(f'RUS_edu_slot_{i}_days',0),setv(f'RUS_edu_slot_{i}_progress',1)]
        if i==3: lines+=cond('check_variable = { RUS_edu_slots < 3 }',[setv(f'RUS_edu_slot_{i}_frame',1)])
        for code,a in enumerate(ACTIVITIES,3):
            lines += cond(f'check_variable = {{ RUS_edu_slot_{i} = {code} }}',[
                setv(f'RUS_edu_slot_{i}_frame',code),setv(f'RUS_edu_slot_{i}_days',remain(a)),
                setv(f'RUS_edu_slot_{i}_progress',a['days']),op('subtract_from',f'RUS_edu_slot_{i}_progress',remain(a)),
                mul(f'RUS_edu_slot_{i}_progress',f'{100/a["days"]:.12g}'),f'round_variable = RUS_edu_slot_{i}_progress',add(f'RUS_edu_slot_{i}_progress',1)])
    lines += catalog_lines()
    return lines+['force_update_dynamic_modifier = yes']

def catalog_lines():
    # The board shows campaigns actually in progress, not available posters.
    # Category selection only filters this view and the decision list.
    lines=clamp('RUS_edu_category',1,6)+[setv('RUS_edu_catalog_count',0)]
    for category in POSTER_CATEGORIES:
        entries=[(code,a) for code,a in enumerate(ACTIVITIES,3) if a['category']==category]
        lines+=cond(f'check_variable = {{ RUS_edu_category = {category} }}',[
            setv('RUS_edu_catalog_count',len(entries))])
    for i in range(1,4):
        for suffix,value in [('activity',0),('frame',2),('running',0),('days',0),('progress',1)]:
            lines.append(setv(f'RUS_edu_catalog_{i}_{suffix}',value))
    lines+=cond('check_variable = { RUS_edu_slots < 3 }',[setv('RUS_edu_catalog_3_frame',1)])
    for code,a in enumerate(ACTIVITIES,3):
        slots=[]
        for i in range(1,4):
            prefix=f'RUS_edu_catalog_{i}_'
            # Only the first free display slot receives this active campaign.
            updates=[setv(prefix+'activity',code),setv(prefix+'frame',code),
                setv(prefix+'running',1),setv(prefix+'days',remain(a)),
                setv(prefix+'progress',a['days']),op('subtract_from',prefix+'progress',remain(a)),
                mul(prefix+'progress',f'{100/a["days"]:.12g}'),f'round_variable = {prefix}progress',add(prefix+'progress',1)]
            slots += [('if' if i==1 else 'else_if')+' = {',
                f'\tlimit = {{ check_variable = {{ {prefix}activity = 0 }} check_variable = {{ RUS_edu_slots > {i-1} }} }}',
                *['\t'+line for line in updates],'}']
        lines+=cond(f'check_variable = {{ RUS_edu_category = {a["category"]} }} has_country_flag = {active(a)}',slots)
    return lines

def decisions():
    lines=['# Generated by tools/generate_education_reform.py --write','RUS_education_reform_category = {']
    for a in ACTIVITIES+CONTROLS:
        regular=a['kind']!='control'
        avail=['hidden_trigger = { has_country_flag = RUS_education_system_active has_socialist_government = yes }']
        if regular:
            avail += ['custom_trigger_tooltip = { tooltip = RUS_edu_free_slot_tt check_variable = { RUS_edu_active_count < RUS_edu_slots } }',
                      f'custom_trigger_tooltip = {{ tooltip = RUS_edu_{a["kind"]}_free_tt NOT = {{ has_country_flag = RUS_edu_busy_{a["kind"]} }} }}']
            for requirement in access_requirements(a):
                if requirement==MILITARY_GATE:
                    requirement='custom_trigger_tooltip = { tooltip = RUS_fr_basic_reform_completed_tt '+requirement+' }'
                elif requirement.startswith('has_country_flag = RUS_edu_'):continue
                avail.append(requirement)
        else:
            avail += ['custom_trigger_tooltip = { tooltip = RUS_edu_control_free_tt NOT = { has_country_flag = RUS_edu_control_busy } }',
                      'check_variable = { RUS_education_enthusiasm < 35 }' if a['id']=='listen' else 'NOT = { check_variable = { RUS_education_enthusiasm < 70 } }']
        avail += [f'custom_trigger_tooltip = {{ tooltip = RUS_edu_cooldown_tt NOT = {{ has_country_flag = RUS_edu_cooldown_{a["id"]} }} }}']
        visible=['has_country_flag = RUS_education_system_active']
        if regular: visible+=[f'check_variable = {{ RUS_edu_category = {a["category"]} }}']
        if regular:visible+=category_requirements(a)
        if a.get('gate'):visible.append(a['gate'])
        cancel_conditions='NOT = { has_country_flag = RUS_education_system_active } NOT = { has_socialist_government = yes }'
        if a.get('wartime'):cancel_conditions+=' has_war = no'
        finish_preview=[f'custom_effect_tooltip = RUS_edu_{a["id"]}_finish_tt']
        if a['permanent_modifiers']:
            finish_preview.append(f'effect_tooltip = {{ add_dynamic_modifier = {{ modifier = RUS_edu_result_{a["id"]} }} }}')
        if a.get('state_reward'):finish_preview.append(block('effect_tooltip',state_reward_effects(a)).strip())
        if a.get('timed_reward'):finish_preview.append(block('effect_tooltip',timed_reward_effects(a)).strip())
        if a.get('agriculture_reward'):
            finish_preview+=cond(AGRICULTURE_GATE,[f'custom_effect_tooltip = RUS_edu_agriculture_{a["agriculture_reward"]}_tt'])
        finish_preview.append(f'hidden_effect = {{ RUS_education_finish_{a["id"]} = yes }}')
        start_preview=[f'custom_effect_tooltip = RUS_edu_{a["id"]}_progress_tt']
        if regular:
            start_preview+=cond('hidden_trigger = { '+repeat_condition(a)+' }',[
                f'effect_tooltip = {{ add_dynamic_modifier = {{ modifier = RUS_edu_repeat_{a["id"]} days = {a["days"]} }} }}'])
        start_preview.append(f'hidden_effect = {{ RUS_education_begin_{a["id"]} = yes }}')
        body=[f'icon = {decision_icon(a)}','fire_only_once = no',f'cost = RUS_edu_cost_{a["id"]}?{a["cost"]}',
              f'days_remove = {a["days"]}',f'days_re_enable = {90 if regular else 60}',
              block('visible',visible).strip(),block('available',avail).strip(),
              'cancel_trigger = { hidden_trigger = { OR = { '+cancel_conditions+' } } }',
              block('modifier',[f'{m} = {v:g}' for m,v in a['modifiers'].items()]).strip(),
              block('complete_effect',start_preview).strip(),
              f'cancel_effect = {{ hidden_effect = {{ RUS_education_cancel_{a["id"]} = yes }} }}',
              block('remove_effect',finish_preview).strip(),
              'ai_will_do = { base = 1 }']
        lines += ['\t'+s for s in block('RUS_education_'+a['id'],body).rstrip().splitlines()]
    return '\n'.join(lines)+'\n}\n'

def modifiers():
    lines=['# Generated by tools/generate_education_reform.py --write\n']
    fields=list(BODY)+['stability_factor','stability_weekly','industrial_capacity_factory','political_power_cost']
    lines += [block('RUS_education_social_capacity',['icon = GFX_idea_generic_high_literacy']+[f'{m} = {bv(m)}' for m in fields]),
              '# Retired attachment handle: never added; refresh removes it while preserving pooled variables.\n',
              block('RUS_education_permanent_results',['icon = GFX_idea_generic_high_literacy']+[f'{m} = {pv(m)}' for m in POOL_CAPS])]
    for a in ACTIVITIES+CONTROLS:
        if a['permanent_modifiers']:
            lines.append(block('RUS_edu_result_'+a['id'],['icon = GFX_idea_generic_high_literacy']+
                [f'{m} = {delta(a,m)}' for m in a['permanent_modifiers']]))
        if a['kind']!='control':
            lines.append(block('RUS_edu_repeat_'+a['id'],['icon = GFX_idea_generic_high_literacy']+
                [f'{m} = {v*.5:g}' for m,v in a['modifiers'].items()]))
    for preset,(name,values) in STATE_REWARDS.items():
        lines.append(block('RUS_edu_state_'+preset,[
            'icon = GFX_decision_generic_industry',
            'enable = { owner = { original_tag = RUS has_socialist_government = yes } controller = { original_tag = RUS } }',
            *[f'{m} = {v:g}' for m,v in values.items()]]))
    return ''.join(lines).rstrip()+'\n'

def gui_outputs():
    # Keep the upper controls fixed; inset the entire noticeboard group by 6px
    # from its old origin so the wood clears the decision-category left border.
    board_offset=6
    canvas_width=498+board_offset
    ui=[]
    def text(name,key,x,y,w,font='hoi_16mbs',tip=None):
        ui.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} font = "{font}" text = "{key}" maxWidth = {w} maxHeight = 42 format = center'+(f' pdx_tooltip = {tip}' if tip else '')+' }')
    def icon(name,sprite,x,y,tip=None):
        ui.append(f'iconType = {{ name = "{name}" spriteType = "{sprite}" position = {{ x = {x} y = {y} }}'+(f' pdx_tooltip = {tip}' if tip else '')+' }')
    text('edu_title','RUS_edu_dashboard_title',4,4,486,'hoi_18mbs')
    for x,kind in zip((6,168,330),('basic','higher','heat')):
        icon(kind+'_panel','GFX_RUS_education_metric_panel',x,30)
        icon(kind+'_name_panel','GFX_RUS_education_metric_name_panel',x+5,33)
        text(kind+'_label','RUS_edu_'+kind+'_label',x+5,37,150,tip='RUS_edu_'+kind+'_tooltip')
        icon(kind+'_value_panel','GFX_RUS_education_metric_value_panel',x+32,62)
        text(kind+'_value','RUS_edu_'+kind+'_value',x+32,64,96,tip='RUS_edu_'+kind+'_tooltip')
        icon(kind+'_bar','GFX_RUS_edu_'+kind+'_bar',x+21,86,'RUS_edu_'+kind+'_tooltip')
    text('edu_rates','RUS_edu_rates',6,118,484)
    text('edu_gates','RUS_edu_gates',6,143,484,tip='RUS_edu_gates_tooltip')
    def button(name,key,x,y):
        ui.append(f'buttonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} quadTextureSprite = "GFX_button_123x34" buttonText = "{key}" buttonFont = "hoi_16mbs" clicksound = click_default }}')
    for category in POSTER_CATEGORIES:
        button(f'edu_category_{category}',f'RUS_edu_category_{category}',24+162*((category-1)%3),168+36*((category-1)//3))
    text('edu_catalog_heading','RUS_edu_catalog_heading',6,245,484)
    props=[]
    for kind in VARS: props.append(f'{kind}_bar = {{ frame = RUS_edu_bar_{kind} }}')
    icon('education_noticeboard','GFX_RUS_education_noticeboard',board_offset,274)
    guard='has_country_flag = RUS_education_system_active'
    triggers=[]
    click_effects=[]
    for category in POSTER_CATEGORIES:
        click_effects.append(block(f'edu_category_{category}_click',['hidden_effect = { '+f'if = {{ limit = {{ {guard} }} '+setv('RUS_edu_category',category)+' RUS_education_refresh = yes } }']).strip())
    for i,x in enumerate((6,168,330),1):
        x+=board_offset
        icon(f'poster_{i}','GFX_RUS_education_posters',x,275,'RUS_edu_slot_'+str(i)+'_tooltip')
        icon(f'activity_progress_{i}','GFX_RUS_edu_activity_bar',x+21,490)
        text(f'activity_name_{i}','RUS_edu_slot_'+str(i)+'_name',x+1,513,158)
        text(f'activity_days_{i}','RUS_edu_slot_'+str(i)+'_text',x+1,558,158)
        triggers += [f'activity_progress_{i}_visible = {{ check_variable = {{ RUS_edu_catalog_{i}_running = 1 }} }}',
                     f'activity_days_{i}_visible = {{ check_variable = {{ RUS_edu_catalog_{i}_running = 1 }} }}']
        props += [f'poster_{i} = {{ frame = RUS_edu_catalog_{i}_frame }}',f'activity_progress_{i} = {{ frame = RUS_edu_catalog_{i}_progress }}']
    # The category's custom-GUI anchor precedes its inner border in the user's
    # runtime screenshot. Correct the entire canvas, keeping the board and cards aligned.
    gui='guiTypes = {\n'+block('containerWindowType',['name = "RUS_education_dashboard_window"','position = { x = 8 y = 0 }',f'size = {{ width = {canvas_width} height = 601 }}']+ui)+'}\n'
    sgui='scripted_gui = {\n'+block('RUS_education_dashboard',['context_type = decision_category','window_name = "RUS_education_dashboard_window"',block('properties',props).strip(),block('triggers',triggers).strip(),block('effects',click_effects).strip()])+'}\n'
    sprites=[]
    for kind in ('basic','higher','heat','activity'):
        sprites.append(block('spriteType',[f'name = "GFX_RUS_edu_{kind}_bar"',f'texturefile = "{ART.as_posix()}/{kind}_bar.dds"','noOfFrames = 101']))
    sprites.append(block('spriteType',['name = "GFX_RUS_education_posters"',f'texturefile = "{ART.as_posix()}/posters.dds"',f'noOfFrames = {len(ACTIVITIES)+2}']))
    sprites.append(block('spriteType',['name = "GFX_RUS_education_noticeboard"','texturefile = "gfx/interface/propaganda/propaganda_bg.dds"','legacy_lazy_load = no']))
    for name in ('metric_panel','metric_name_panel','metric_value_panel'):
        sprites.append(block('spriteType',[f'name = "GFX_RUS_education_{name}"',f'texturefile = "{ART.as_posix()}/{name}.dds"']))
    for kind,texture in [('basic',f'{ART.as_posix()}/basic_texticon.dds'),('higher',f'{ART.as_posix()}/higher_texticon.dds'),('heat','gfx/texticons/SOV_propaganda_text_icon.dds')]:
        sprites.append(block('spriteType',[f'name = "GFX_RUS_edu_{kind}_texticon"',f'texturefile = "{texture}"','legacy_lazy_load = no']))
    return {GUI:gui,SGUI:sgui,GFX:'spriteTypes = {\n'+''.join(sprites)+'}\n'}

def localisations():
    l={
      'RUS_education_reform_category':'教育与文化建设',
      'RUS_education_reform_category_desc':'',
      'RUS_education_social_capacity':'教育改革',
      'RUS_education_social_capacity_desc':'',
      'RUS_education_permanent_results':'教育改革',
      'RUS_education_permanent_results_desc':'',
      'RUS_education_present_drive':'教育成果投入生产',
      'RUS_education_present_drive_desc':'',
      'RUS_edu_dashboard_title':'教育与文化建设',
      'RUS_edu_basic_label':'§C基础教育§!',
      'RUS_edu_higher_label':'§Y高等教育§!',
      'RUS_edu_heat_label':'§O民众热情§!',
      'RUS_edu_basic_value':'§C[?RUS_basic_education_level|2]%§!',
      'RUS_edu_higher_value':'§Y[?RUS_higher_education_level|2]%§!',
      'RUS_edu_heat_value':'§O[?RUS_education_enthusiasm|2]%§!',
      'RUS_basic_education_level':'§C基础教育水平§!',
      'RUS_higher_education_level':'§Y高等教育水平§!',
      'RUS_education_enthusiasm':'§O民众热情§!',
      'RUS_education_completed_activities':'已完成宣传次数',
      'RUS_edu_rates':'教育收益倍率：§Y[?RUS_edu_quality_percent|2]%§!   在办活动：[?RUS_edu_active_count|0]/[?RUS_edu_slots|0]',
      'RUS_edu_gates':'已完成宣传：§Y[?RUS_education_completed_activities|0]§! 次',
      'RUS_edu_gates_tooltip':'[RUSEducationNextGate]\\n仅正常完成宣传活动计数；开始、取消和调节热情不计数。',
      'RUS_edu_basic_tooltip':'§C基础教育水平§!：[?RUS_basic_education_level|2]%\\n反映民众的识字程度与基本知识，有助于生产、建设和人员培养。\\n可通过扫盲、学校与夜校提升。',
      'RUS_edu_higher_tooltip':'§Y高等教育水平§!：[?RUS_higher_education_level|2]%\\n反映专业人才培养与科学研究水平，有助于科研和技术发展。\\n可通过大学、科研与师资培养提升。',
      'RUS_edu_heat_tooltip':'§O民众热情§!：[?RUS_education_enthusiasm|2]%\\n反映民众参与教育与社会活动的积极性，会随时间减退，需要宣传维持。\\n热情提高可增强工厂产出与生产效率收益；过高会降低教育成效，并持续损害稳定度。',
      'RUS_edu_free_slot_tt':'有空余宣传栏位',
      'RUS_edu_control_free_tt':'没有正在进行的热情调节活动',
      'RUS_edu_cooldown_tt':'此活动已结束冷却',
      'RUS_edu_unlock_basic_tt':'开启教育与文化建设：2个宣传栏位。\\n解锁基础教育、社会与群体、国家与生活类海报。',
      'RUS_edu_unlock_culture_tt':'增加1个宣传栏位。\\n解锁文教与思想类海报。\\n基础教育达到35%后，可开展高等教育类活动。',
      'RUS_edu_unlock_technical_tt':'解锁经济与生产类海报及职业技术活动。',
      'RUS_edu_theory_tt':'§Y高等教育增量§!：§G+20%§!。',
      'RUS_edu_practice_tt':'§C基础教育增量§!：§G+20%§!。',
      'RUS_edu_central_tt':'宣传活动政治点花费：§G−20%§!。\\n宣传活动正热情增量：§Y+25%§!。',
      'RUS_edu_amateur_tt':'活动教育增量：§G+10%§!。\\n文化活动正热情增量：§Y−25%§!。',
      'RUS_edu_now_tt':'§C基础教育§!：§G+8§!；§Y高等教育§!：§G+3§!；§O民众热情§!：§Y+10§!。',
      'RUS_edu_future_tt':'§Y高等教育增量§!：§G+20%§!。',
      'RUS_edu_repeat_campaign_tt':'重复开展已完成的海报：花费、临时修正、教育及热情增量§Y×1.5§!。',
      'RUS_edu_half_cost_tt':'所有海报政治点花费：§G−50%§!。',
      'RUS_edu_era_cost_tt':'所有海报政治点花费：§G−25%§!。',
      'RUS_edu_mass_transition_tt':'180天后获得：',
      'RUS_education_mass_hesitation':'群众犹豫不决',
      'RUS_education_mass_enthusiasm':'群众热情澎湃',
      'RUS_edu_mass_hesitation_daily_tt':'每日§O民众热情§!：§Y−0.15§!',
      'RUS_edu_mass_enthusiasm_daily_tt':'每日§O民众热情§!：§Y+0.05§!',
      'RUS_edu_kalinin_tt':'教育活动的教育增量：§G+20%§!。',
      'RUS_edu_gate_first':'下一组：宣传3次／基础30%',
      'RUS_edu_gate_second':'下一组：6次／基础45%／高等15%',
      'RUS_edu_gate_third':'下一组：9次／基础60%／高等25%',
      'RUS_edu_gate_done':'教育路线已确定',
      'RUS_edu_empty':'空闲栏位',
      'RUS_edu_catalog_heading':'§Y[RUSEducationPosterCategory]§!',
      'RUS_edu_locked':'完成“对文化革命”后开放',
      'RUS_edu_blank':'',
    }
    for category,(name,folders) in POSTER_CATEGORIES.items(): l[f'RUS_edu_category_{category}']=name
    for preset,(name,values) in STATE_REWARDS.items():l['RUS_edu_state_'+preset]=name
    l.update({'RUS_edu_agriculture_wheat_tt':'小麦库存：§G+4§!单位',
              'RUS_edu_agriculture_rye_tt':'黑麦库存：§G+3§!单位',
              'RUS_edu_agriculture_technical_tt':'本季作物产量：§G+5%§!',
              'RUS_edu_agriculture_repair_tt':'本季农机损耗率：§G−5§!个百分点'})
    for kind,name in KINDS.items(): l['RUS_edu_'+kind+'_free_tt']=name+'类没有其他在办活动'
    for a in ACTIVITIES+CONTROLS:
        aid=a['id']; regular=a['kind']!='control'; key='RUS_education_'+aid
        l[key]=a['name']
        if a['permanent_modifiers']:l['RUS_edu_result_'+aid]='教育改革'
        if regular:l['RUS_edu_repeat_'+aid]='重复宣传：'+a['name']
        if a.get('timed_reward'):l[a['timed_reward']['idea']]=a['timed_reward']['name']
        l[key+'_desc']='【'+KINDS.get(a['kind'],'热情调节')+'】'
        if regular:
            gains=[]
            if a['basic']:gains.append(f'基础教育水平：§G+{a["basic"]:g}§!')
            if a['higher']:gains.append(f'高等教育水平：§G+{a["higher"]:g}§!')
            progress='教育提升：\\n'+'\\n'.join(gains) if gains else ''
            if a['heat']: progress+=f'\\n民众热情：每30天 §Y{a["heat"]:+g}§!'
            finish='完成宣传次数：§G+1§!。'
        else:
            progress='不占宣传栏位；不计入宣传次数。'
            finish=f'民众热情：§Y{a["heat"]:+g}§!'
        l['RUS_edu_'+aid+'_progress_tt']=progress
        l['RUS_edu_'+aid+'_finish_tt']=finish
        l['RUS_edu_activity_'+aid]=a['name']
    for i in range(1,4):
        l[f'RUS_edu_slot_{i}_name']=f'[RUSEducationSlot{i}]'
        l[f'RUS_edu_slot_{i}_text']=f'[RUSEducationSlot{i}Days]'
        l[f'RUS_edu_slot_{i}_countdown']=f'剩余 [?RUS_edu_catalog_{i}_days|0] 天'
        l[f'RUS_edu_slot_{i}_tooltip']=f'[RUSEducationSlot{i}]\\n[RUSEducationSlot{i}Days]'
    for name,b,h,t in [('new_culture_popularisation',2,0,3),('new_culture_elite_art',0,2,-2),('revolutionary_realism',1,1,1),('revolutionary_romanticism',0,3,2)]:
        l['RUS_edu_legacy_'+name+'_tt']=f'教育改革开启后：基础教育§C+{b}§!，高等教育§Y+{h}§!，热情§O{t:+g}§!。'
    # Inline texticons use the same sprite aliases everywhere, including native
    # check_variable names. Do not turn modifier effects into hand-written text.
    import re
    for key,value in list(l.items()):
        for kind,term,colour in [('basic','基础教育','C'),('higher','高等教育','Y'),('heat','民众热情','O')]:
            value=re.sub('§[A-Z]('+term+'(?:水平)?)§!',r'\1',value)
            value=re.sub(term+'(?:水平)?(?![类])',lambda _:f'£RUS_edu_{kind}_texticon£ §{colour}'+term+('水平' if kind!='heat' else '')+'§!',value)
        l[key]=value
    # Existing names have one owner in older localisation; put replacements in replace/.
    existing={'RUS_education_reform_category','RUS_education_reform_category_desc'}
    outputs={}
    for lang in ('simp_chinese','english','russian'):
        for replace in (False,True):
            values={k:v for k,v in l.items() if (k in existing)==replace}
            p=Path('localisation')/('replace' if replace else lang)/f'RUS_education_dashboard_l_{lang}.yml'
            outputs[p]=('l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v.replace('\\n','\n'),ensure_ascii=False)+'\n' for k,v in values.items())).encode('utf-8-sig')
    return outputs

def scripted_loc():
    chunks=[]
    choices=[('RUS_edu_gate_done','OR = { has_country_flag = RUS_edu_future has_completed_focus = RUS_future_domestic_229 }'),
             ('RUS_edu_gate_third','OR = { has_country_flag = RUS_edu_amateur has_country_flag = RUS_edu_central }'),
             ('RUS_edu_gate_second','OR = { has_country_flag = RUS_edu_theory has_country_flag = RUS_edu_practice }')]
    chunks.append(block('defined_text',['name = RUSEducationNextGate']+[block('text',['trigger = { '+c+' }','localization_key = '+key]).strip() for key,c in choices]+['text = { localization_key = RUS_edu_gate_first }']))
    chunks.append(block('defined_text',['name = RUSEducationPosterCategory']+[
        f'text = {{ trigger = {{ check_variable = {{ RUS_edu_category = {category} }} }} localization_key = RUS_edu_category_{category} }}' for category in POSTER_CATEGORIES]))
    for i in range(1,4):
        body=[f'name = RUSEducationSlot{i}',f'text = {{ trigger = {{ check_variable = {{ RUS_edu_catalog_{i}_frame = 1 }} }} localization_key = RUS_edu_locked }}']
        for code,a in enumerate(ACTIVITIES,3): body.append(f'text = {{ trigger = {{ check_variable = {{ RUS_edu_catalog_{i}_activity = {code} }} }} localization_key = RUS_edu_activity_{a["id"]} }}')
        body+=['text = { localization_key = RUS_edu_empty }']; chunks.append(block('defined_text',body))
        chunks.append(block('defined_text',[f'name = RUSEducationSlot{i}Days',
            f'text = {{ trigger = {{ check_variable = {{ RUS_edu_catalog_{i}_running = 1 }} }} localization_key = RUS_edu_slot_{i}_countdown }}',
            'text = { localization_key = RUS_edu_blank }']))
    return ''.join(chunks).rstrip()+'\n'

def render_outputs():
    outputs={FX:effects(),DEC:decisions(),DM:modifiers(),
        Path('common/scripted_localisation/RUS_education_dashboard.txt'):scripted_loc(),
        Path('common/on_actions/RUS_education_continuous_on_actions.txt'):'on_actions = {\n'+block('on_daily_RUS',['effect = {']+['\t'+s for s in
          cond('original_tag = RUS has_socialist_government = yes NOT = { has_country_flag = RUS_education_system_active } NOT = { has_idea = RUS_malformed_education_system }',['add_ideas = RUS_malformed_education_system'])+
          cond('has_country_flag = RUS_education_system_active',['RUS_education_daily = yes'])]+['}'])+'}\n',
    }
    outputs.update(gui_outputs())
    outputs.update(integration_outputs())
    outputs={p:s.encode('utf-8') for p,s in outputs.items()}; outputs.update(localisations()); return outputs

def integration_outputs():
    """Idempotent replacements of explicitly owned blocks; preserve all other scripts."""
    from hoi4_politics_blocks import parse
    outputs={}
    path=Path('common/decisions/categories/RUS decision_cats (Russia).txt')
    text=(ROOT/path).read_bytes().decode('utf-8-sig')
    node=next(n for n in parse(text) if n.k=='RUS_education_reform_category')
    replacement=block(node.k,['icon = generic_research','priority = 82','allowed = { original_tag = RUS }',
        'visible = { has_country_flag = RUS_education_system_active }','visible_when_empty = yes','scripted_gui = RUS_education_dashboard']).rstrip()
    outputs[path]=text[:node.a]+replacement+text[node.b:]
    path=Path('common/dynamic_modifiers/RUS stalin dynamic_modifiers.txt')
    text=(ROOT/path).read_bytes().decode('utf-8-sig')
    for n in reversed(parse(text)):
        if n.k in ('RUS_reforming_education_system','RUS_completed_education_reform'):text=text[:n.a]+text[n.b:]
    outputs[path]=text
    path=Path('common/on_actions/on_actions_Russia.txt');text=(ROOT/path).read_bytes().decode('utf-8-sig')
    def walk(nodes):
        for n in nodes:
            if isinstance(n.v,list):
                if n.k=='if' and n.one('limit') and 'RUS_education_' in n.one('limit').raw(): yield n
                else:yield from walk(n.v)
    matches=list(walk(parse(text)))
    assert len(matches) in (0,3),len(matches)
    for n in reversed(matches):text=text[:n.a]+text[n.b:]
    outputs[path]=text
    path=Path('common/scripted_effects/RUS_stalin_advisor_relationship_effects.txt');text=(ROOT/path).read_bytes().decode('utf-8-sig')
    n=next(n for n in parse(text) if n.k=='RUS_stalin_refresh_kalinin_education_effects')
    replacement=block(n.k,cond('has_country_flag = RUS_education_system_active',['RUS_education_refresh = yes'])).rstrip()
    outputs[path]=text[:n.a]+replacement+text[n.b:]
    path=Path('common/country_leader/stalin_form_sov_traits.txt');text=(ROOT/path).read_bytes().decode('utf-8-sig')
    n=next(t for root in parse(text) for t in root.children('RUS_kalinin_engineer_of_human_souls'))
    body=n.raw()
    import re
    body=re.sub(r'custom_modifier_tooltip = RUS_kalinin_education_(?:time|repeat|penalty)_tt', '',body)
    if 'RUS_edu_kalinin_tt' not in body:body=body[:-1]+'\tcustom_modifier_tooltip = RUS_edu_kalinin_tt\n\t}'
    outputs[path]=text[:n.a]+body+text[n.b:]
    path=Path('common/ideas/RUS stalin education reform ideas.txt')
    timed_ideas=[]
    for a in ACTIVITIES:
        if a.get('timed_reward'):
            r=a['timed_reward']
            timed_ideas.append(block(r['idea'],['picture = CZE_planning_bonus','allowed = { always = no }','removal_cost = -1',
                f'targeted_modifier = {{ tag = {r["target"]} attack_bonus_against_cores = {r["attack"]:g} }}']).strip())
    outputs[path]='ideas = {\n'+block('country',[block('RUS_malformed_education_system',['picture = SOV_opiate_of_the_masses',
        block('modifier',[f'{m} = {lo:g}' for m,(lo,hi,w) in BODY.items()]).strip()]).strip(),
        'RUS_education_present_drive = { picture = generic_high_literacy modifier = { industrial_capacity_factory = 0.05 } }',
        *[block('RUS_education_mass_'+phase,['picture = generic_high_literacy','allowed = { always = no }','removal_cost = -1',
            'modifier = { custom_modifier_tooltip = RUS_edu_mass_'+phase+'_daily_tt }']).strip()
          for phase in ('hesitation','enthusiasm')],*timed_ideas])+'}\n'
    return outputs

def render_assets():
    from PIL import Image,ImageOps
    result={}
    for kind in ('basic','higher'):
        source=Image.open(ROOT/DESIGN/'icons'/(kind+'.source.png')).convert('RGBA')
        alpha=source.getchannel('A');assert alpha.getextrema()==(0,255)
        # Packaging only: preserve the complete AI-created silhouette and alpha.
        source=source.crop(alpha.getbbox())
        fit=ImageOps.contain(source,(22,22),Image.Resampling.LANCZOS)
        icon=Image.new('RGBA',(24,24));icon.alpha_composite(fit,((24-fit.width)//2,(24-fit.height)//2))
        b=io.BytesIO();icon.save(b,format='DDS');result[ART/(kind+'_texticon.dds')]=b.getvalue()
    game=ROOT.parents[3]/'common/Hearts of Iron IV'
    # Native small-window border, nine-sliced without repainting its corners.
    source=Image.open(game/'gfx/interface/tiles/tiled_window_small.dds').convert('RGBA')
    for name,width,height,border in [('metric_panel',160,82,32),('metric_name_panel',150,28,6),('metric_value_panel',96,22,6)]:
        panel=Image.new('RGBA',(width,height))
        sx=[0,border,source.width-border,source.width];sy=[0,border,source.height-border,source.height]
        tx=[0,border,width-border,width];ty=[0,border,height-border,height]
        for row in range(3):
            for col in range(3):
                piece=source.crop((sx[col],sy[row],sx[col+1],sy[row+1]))
                # Repeat edges/centre exactly as the native tiling sprite does.
                for y in range(ty[row],ty[row+1],piece.height):
                    for x in range(tx[col],tx[col+1],piece.width):
                        panel.alpha_composite(piece.crop((0,0,min(piece.width,tx[col+1]-x),min(piece.height,ty[row+1]-y))),(x,y))
        b=io.BytesIO();panel.save(b,format='DDS');result[ART/(name+'.dds')]=b.getvalue()
    # Production's actual 118x21 artwork, unscaled and untinted. Its middle
    # 21px band is the fill; the other two bands are shader start/end cap layers.
    # Pack progress frames for scripted-GUI frame binding, keeping the native look.
    for kind,filename in [('basic','prod_progress_bar2.dds'),('higher','prod_progress_bar2_yellow.dds'),('heat','prod_progress_bar2_red.dds'),('activity','prod_progress_bar2.dds')]:
        background=Image.open(game/'gfx/interface/prod_progress_bar2_bg.dds').convert('RGBA')
        fill=Image.open(game/'gfx/interface'/filename).convert('RGBA').crop((0,21,118,42))
        assert background.size==(118,21)
        strip=Image.new('RGBA',(118*101,21))
        for value in range(101):
            im=background.copy();right=round(118*value/100)
            if right: im.alpha_composite(fill.crop((0,0,right,21)),(0,0))
            strip.paste(im,(value*118,0))
        b=io.BytesIO();strip.save(b,format='DDS');result[ART/(kind+'_bar.dds')]=b.getvalue()
    strip=Image.new('RGBA',(160*(len(ACTIVITIES)+2),205),'#d8cfae')
    vanilla=Image.open(ROOT.parents[3]/'common/Hearts of Iron IV/gfx/interface/propaganda/SOV/SOV_propaganda_strip.dds').convert('RGBA')
    strip.paste(vanilla.crop((0,0,320,205)),(0,0))
    for index,a in enumerate(ACTIVITIES,2):
        source=Image.open(ROOT/DESIGN/'posters'/(a['id']+'.jpg')).convert('RGB')
        fit=ImageOps.contain(source,(156,201),Image.Resampling.LANCZOS)
        paper=Image.new('RGBA',(160,205),'#e1d9ba');paper.paste(fit,((160-fit.width)//2,(205-fit.height)//2))
        strip.paste(paper,(index*160,0))
    b=io.BytesIO();strip.save(b,format='DDS');result[ART/'posters.dds']=b.getvalue()
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--assets',action='store_true');args=p.parse_args()
    outputs=render_outputs()
    if args.assets:
        if not args.write: p.error('--assets requires --write; checking never redraws')
        outputs.update(render_assets())
    if args.write:
        for path,data in outputs.items():
            target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True)
            if not target.is_file() or target.read_bytes()!=data: target.write_bytes(data)
        print('Wrote',len(outputs),'education files.');return 0
    stale=[str(p) for p,b in outputs.items() if not (ROOT/p).is_file() or (ROOT/p).read_bytes()!=b]
    if stale: print('STALE:',', '.join(stale));return 1
    manifest=json.loads((ROOT/DESIGN/'asset_manifest.json').read_text(encoding='utf-8'))
    for item in manifest['outputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item
    print('PASS: education text outputs and packaged assets current (read-only).');return 0

if __name__=='__main__':raise SystemExit(main())
