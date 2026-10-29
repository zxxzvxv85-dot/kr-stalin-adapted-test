"""Integrate completed military decisions into the current reform stage.

Default/--check is read-only. Numeric baselines are archived in the design JSON;
stage tracker ideas retain their original equipment effects and callbacks but
are hidden. Their country modifiers and decision results share one visible DM.
"""
from pathlib import Path
import json,re
from hoi4_politics_blocks import parse,load
from generate_easy_mode_ideas import is_beneficial,bonuses

ROOT=Path(__file__).resolve().parents[1]
SPEC=Path('tools/design/military_decision_integration_20261029.json')
IDEAS=Path('common/ideas/RUS_fr_military_reform_ideas.txt')
FX=Path('common/scripted_effects/RUS_fr_military_reform_effects.txt')
DEC=Path('common/decisions/RUS_fr_military_reform_decisions.txt')
NEWFX=Path('common/scripted_effects/RUS_fr_current_reform_effects.txt')
DM=Path('common/dynamic_modifiers/RUS_fr_current_reform_modifiers.txt')
LOC=Path('common/scripted_localisation/RUS_fr_current_reform_localisation.txt')
CURRENT='RUS_fr_current_army_reform'
REFRESH='RUS_fr_refresh_current_reform'
ACTIVE='RUS_fr_unified_army_reform_active'

def b(k,lines):return k+' = {\n'+''.join('\t'+line+'\n' for x in lines for line in x.splitlines())+'}\n'
def cond(c,lines):return b('if',['limit = { '+c+' }',*lines]).rstrip()
def op(k,v,x):return f'{k}_variable = {{ {v} = {x} }}'
def one(raw):return parse(raw)[0]
def fields(n):
    out={}
    def visit(nodes):
        for x in nodes:
            if x.k=='custom_modifier_tooltip':continue
            if isinstance(x.v,list):visit(x.v)
            else:out[x.k]=float(x.v)
    for block in n.children('modifier')+n.children('hidden_modifier'):visit(block.v)
    return out
def easy_fields(n):
    # Match the existing ideas easy-mode generator: nested hidden_modifier
    # fields were not doubled, so moving them must not introduce a new bonus.
    return {x.k:float(x.v) for block in n.children('modifier')+n.children('hidden_modifier') for x in block.v
            if not isinstance(x.v,list) and x.k!='custom_modifier_tooltip' and is_beneficial(x.k,float(x.v))}
def reward_key(k):return 'RUS_fr_integrate_'+k.removeprefix('RUS_fr_')
def flag(k):return 'RUS_fr_integrated_'+k.removeprefix('RUS_fr_')
def val(m,layer):return 'RUS_fr_result_'+layer+'_'+m
def current(m):return 'RUS_fr_current_'+m

def replace_nodes(text,edits):
    for a,z,value in sorted(edits,reverse=True):text=text[:a]+value+text[z:]
    return text

def render_outputs():
    spec=json.loads((ROOT/SPEC).read_text(encoding='utf-8'))
    stages={k:one(v) for k,v in spec['stages'].items()}
    rewards={k:one(v) for k,v in spec['rewards'].items()}
    allfields=sorted({m for n in [*stages.values(),*rewards.values()] for m in fields(n)})
    permanent=sorted({m for k,n in rewards.items() if not k.endswith('_correction') for m in fields(n)})
    original_dm=next(n for n in load(ROOT/'common/dynamic_modifiers/RUS_fr_military_reform_dynamic_modifiers.txt') if n.k=='RUS_fr_unified_army_reform')
    unified={n.k:n.v for n in original_dm.v if n.k not in ('icon','custom_modifier_tooltip')}
    assert set(permanent)<=unified.keys(),set(permanent)-unified.keys()
    # Retain the original hidden state IDs so all stage prerequisites and swaps
    # keep their exact logic. Only the visible carrier changes.
    text=(ROOT/IDEAS).read_text(encoding='utf-8-sig');edits=[]
    for root in parse(text):
        for cat in root.v:
            if isinstance(cat.v,list):
                for n in cat.v:
                    if n.k in stages or n.k in rewards:edits.append((n.a,n.b,''))
    text=replace_nodes(text,edits)
    text=text.replace('# Current-stage decision integration; generated from '+str(SPEC)+'.','')
    generated=[]
    stage_codes={k:i+1 for i,k in enumerate(stages)}
    for k,n in stages.items():
        code=stage_codes[k]
        parts=[x.raw() for x in n.v if x.k not in ('modifier','hidden_modifier','on_add','on_remove')]
        add=[x.raw() for c in n.children('on_add') for x in c.v]
        add += [op('set','RUS_fr_current_reform_stage',code),REFRESH+' = yes']
        remove=[cond(f'check_variable = {{ RUS_fr_current_reform_stage = {code} }}',[op('set','RUS_fr_current_reform_stage',0),REFRESH+' = yes'])]
        parts += [b('on_add',add).rstrip(),b('on_remove',remove).rstrip()]
        generated.append(b(k,parts))
    for k,n in rewards.items():
        generated.append(b(k,[x.raw() for x in n.v if x.k not in ('modifier','hidden_modifier')]))
    tree=parse(text)[0];hidden=tree.one('hidden_ideas')
    addition='\n# Current-stage decision integration; generated from '+str(SPEC)+'.\n'+''.join(generated)
    if hidden:text=text[:hidden.ia]+text[hidden.ia:hidden.ib].rstrip()+addition+text[hidden.ib:]
    else:text=text[:tree.ib]+b('hidden_ideas',[addition])+text[tree.ib:]
    # Empty gaps are presentation only; avoid growing blank lines on regeneration.
    text=re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+','\n\n',text)
    outputs={IDEAS:text}
    # New native delta tooltips use RIGHT, as KR's shared variable modifier
    # tooltips do. Labels are native modifier localisation references.
    aliases={'experience_gain_factor':'MODIFIER_XP_GAIN_FACTOR','experience_gain_army_factor':'MODIFIER_XP_GAIN_ARMY_FACTOR',
             'experience_gain_army_unit_factor':'MODIFIER_XP_GAIN_ARMY_UNIT_FACTOR','land_reinforce_rate':'MODIFIER_LAND_REINFORCE_RATE',
             'mobilization_speed':'MODIFIER_MOBILIZATION_SPEED','command_power_gain_mult':'MODIFIER_COMMAND_POWER_GAIN_MULT',
             'conscription':'MODIFIER_CONSCRIPTION_FACTOR','party_popularity_stability_factor':'MODIFIER_STABILITY_POPULARITY_FACTOR',
             'army_attack_factor':'MODIFIERS_ARMY_ATTACK_FACTOR','army_defence_factor':'MODIFIERS_ARMY_DEFENCE_FACTOR',
             'army_core_attack_factor':'MODIFIERS_ARMY_CORE_ATTACK_FACTOR','army_core_defence_factor':'MODIFIERS_ARMY_CORE_DEFENCE_FACTOR',
             'army_non_core_attack_factor':'MODIFIERS_ARMY_NON_CORE_ATTACK_FACTOR','army_non_core_defence_factor':'MODIFIERS_ARMY_NON_CORE_DEFENCE_FACTOR',
             'army_strength_factor':'MODIFIER_ARMY_STRENGTH','breakthrough_factor':'MODIFIER_BREAKTHROUGH'}
    loc={CURRENT:'[RUSFrCurrentReformTitle]',CURRENT+'_desc':'[RUSFrCurrentReformDescription]',
         'RUS_fr_current_reform_changed_tt':'§Y[RUSFrCurrentReformTitle]§!追加效果：',
         'RUS_fr_current_equipment_tt':'[RUSFrCurrentEquipmentEffects]',
         'RUS_fr_current_equipment_base_tt':'步兵装备、支援装备、装甲装备生产花费：§R+10.0%§!',
         'RUS_fr_current_equipment_infantry_tt':'装甲装备生产花费：§R+10.0%§!',
         'RUS_fr_current_equipment_armour_tt':'步兵装备、支援装备生产花费：§R+10.0%§!',
         'RUS_fr_current_officer_tt':'[RUSFrCurrentOfficerEffects]',
         'RUS_fr_current_katyusha_results_tt':'[RUSFrCurrentKatyushaEffects]',
         'RUS_fr_current_empty':'',
         'RUS_fr_current_katyusha_tt':'火箭炮、自行火箭炮：\n$STAT_ARMY_SOFT_ATTACK$§G+50.0%§!\n$STAT_COMMON_PIERCING$§G+200.0%§!\n$STAT_ARMY_HARD_ATTACK$§G+100.0%§!',
         'RUS_fr_current_equipment_standardisation_tt':'步兵装备、支援装备生产花费：§G-10.0%§!',
         'RUS_fr_current_armoured_production_tt':'装甲装备生产花费：§G-10.0%§!'}
    for m in allfields:
        label=aliases.get(m,'MODIFIER_'+m.upper())
        loc['RUS_fr_result_'+m+'_tt']='$'+label+'$: $RIGHT|'+('-' if not is_beneficial(m,1) else '+')+'=%2$'
        if m=='land_mastery_gain_factor':loc['RUS_fr_result_'+m+'_tt']='$land_mastery_gain_factor_tt$'
    effects=['# Generated by tools/generate_military_decision_integration.py --write\n']
    for k,n in rewards.items():
        correction=k.endswith('_correction');values=fields(n);body=[]
        preview=[op('add_to',val(m,'preview'),f'{v:g}')[:-2]+' tooltip = RUS_fr_result_'+m+'_tt }' for m,v in values.items()]
        if n.one('equipment_bonus'):
            preview.append('custom_effect_tooltip = RUS_fr_current_'+('katyusha_tt' if 'katyusha' in k else k.removeprefix('RUS_fr_').removesuffix('_correction')+'_tt'))
        if 'command_merit' in k:preview.append('custom_effect_tooltip = RUS_fr_officer_attack_growth_bonus_tt')
        body += ['custom_effect_tooltip = RUS_fr_current_reform_changed_tt',b('effect_tooltip',preview).rstrip()]
        changes=[]
        if correction:
            changes += [op('add_to',val(m,'correction'),f'{v:g}') for m,v in values.items()]
            changes += [op('add_to',val(m,'correction_easy'),f'{v:g}') for m,v in easy_fields(n).items()]
        else:
            if values:
                changes += [cond('has_country_flag = '+ACTIVE,[op('add_to',unified[m],f'{v:g}') for m,v in values.items()]),
                            b('else',[op('add_to',val(m,'permanent'),f'{v:g}') for m,v in values.items()]+[op('add_to',val(m,'permanent_easy'),f'{v:g}') for m,v in easy_fields(n).items()]).rstrip()]
        if n.one('equipment_bonus'):
            equipment_id='RUS_fr_hidden_katyusha_rocket_artillery' if 'katyusha' in k else k
            changes.append('add_ideas = '+equipment_id)
        changes += ['set_country_flag = '+flag(k),REFRESH+' = yes','RUS_easy_mode_refresh_military = yes']
        condition='NOT = { has_country_flag = '+flag(k)+' }'
        if correction:condition+=' NOT = { has_country_flag = '+ACTIVE+' }'
        body += [b('hidden_effect',changes).rstrip()]
        effects.append(b(reward_key(k),[cond('hidden_trigger = { '+condition+' }',body)]))
    lines=[]
    for m in allfields:
        lines += [op('set',current(m),0)]
        for layer in ('permanent','correction'):
            lines += [cond('has_variable = '+val(m,layer),[op('add_to',current(m),'var:'+val(m,layer))])]
            lines += [cond('has_country_flag = RUS_easy_mode_enabled is_ai = no has_variable = '+val(m,layer+'_easy'),[op('add_to',current(m),'var:'+val(m,layer+'_easy'))])]
    for k,n in stages.items():
        values=fields(n)
        add=[op('add_to',current(m),f'{v:g}') for m,v in values.items()]
        add += [cond('has_country_flag = RUS_easy_mode_enabled is_ai = no',[op('add_to',current(m),f'{v:g}') for m,v in easy_fields(n).items()])]
        lines += [cond(f'check_variable = {{ RUS_fr_current_reform_stage = {stage_codes[k]} }}',add)]
    lines += [cond(f'OR = {{ has_country_flag = {ACTIVE} NOT = {{ check_variable = {{ RUS_fr_current_reform_stage > 0 }} }} }} has_dynamic_modifier = {{ modifier = {CURRENT} }}',[f'remove_dynamic_modifier = {{ modifier = {CURRENT} }}']),
              cond(f'NOT = {{ has_country_flag = {ACTIVE} }} check_variable = {{ RUS_fr_current_reform_stage > 0 }} NOT = {{ has_dynamic_modifier = {{ modifier = {CURRENT} }} }}',[f'add_dynamic_modifier = {{ modifier = {CURRENT} }}']),
              'force_update_dynamic_modifier = yes']
    effects.append(b(REFRESH,lines));outputs[NEWFX]='\n'.join(effects)
    dm=['icon = GFX_idea_FOP_revolutionary_army']+[f'{m} = {current(m)}' for m in allfields]
    dm += ['custom_modifier_tooltip = RUS_fr_current_equipment_tt','custom_modifier_tooltip = RUS_fr_current_officer_tt','custom_modifier_tooltip = RUS_fr_current_katyusha_results_tt']
    outputs[DM]='# Generated by tools/generate_military_decision_integration.py --write\n'+b(CURRENT,dm)
    # Transfer only persistent decision awards. Specialist corrections disappear
    # with the old specialist penalties, exactly as in the original end-stage.
    text=(ROOT/FX).read_text(encoding='utf-8-sig');edits=[]
    for n in parse(text):
        if n.k in spec['apply']:
            old=one(spec['apply'][n.k]);idea=old.one('else').one('add_ideas').v
            complete=[x.raw() for x in old.v if x.k=='set_country_flag']
            edits.append((n.a,n.b,b(n.k,[reward_key(idea)+' = yes',*complete]).rstrip()))
        elif n.k=='RUS_fr_initialise_unified_army_reform':
            new=spec['initialise'];needle='set_country_flag = '+ACTIVE
            transfer='\n'.join(cond('has_variable = '+val(m,'permanent'),[op('add_to',unified[m],'var:'+val(m,'permanent'))]) for m in permanent)
            new=new.replace(needle,transfer+'\n\t\t'+needle,1)
            edits.append((n.a,n.b,new))
    outputs[FX]=replace_nodes(text,edits)
    # Replace only the old decision result branches, leaving costs, timers,
    # prerequisites, other rewards and cancellations byte-for-byte intact.
    text=(ROOT/DEC).read_text(encoding='utf-8-sig');edits=[]
    def grants(nodes):
        out=set()
        for n in nodes:
            if n.k=='add_ideas' and n.v in rewards:out.add(n.v)
            elif isinstance(n.v,list):out.update(grants(n.v))
        return out
    for cat in parse(text):
        for decision in cat.v:
            if not isinstance(decision.v,list):continue
            remove=decision.one('remove_effect')
            if not remove:continue
            nodes=remove.v;i=0
            while i<len(nodes):
                n=nodes[i];group=[n]
                if n.k=='if' and i+1<len(nodes) and nodes[i+1].k=='else':group.append(nodes[i+1])
                targets=grants(group)
                if targets:
                    assert len(targets)==1,(decision.k,targets)
                    edits.append((n.a,group[-1].b,reward_key(next(iter(targets)))+' = yes'));i+=len(group)
                else:i+=1
    text=replace_nodes(text,edits)
    for key,n in rewards.items():
        if not n.one('equipment_bonus'):
            text=re.sub(r'has_idea\s*=\s*'+re.escape(key)+r'\b','has_country_flag = '+flag(key),text)
    outputs[DEC]=text
    title=[b('text',['trigger = { has_dynamic_modifier = { modifier = RUS_fr_unified_army_reform_final } }','localization_key = RUS_fr_unified_army_reform_final']).rstrip(),b('text',['trigger = { has_country_flag = '+ACTIVE+' }','localization_key = RUS_fr_unified_army_reform']).rstrip()]
    desc=[]
    for k,code in stage_codes.items():
        title.append(b('text',[f'trigger = {{ check_variable = {{ RUS_fr_current_reform_stage = {code} }} }}','localization_key = '+k]).rstrip())
        desc.append(b('text',[f'trigger = {{ check_variable = {{ RUS_fr_current_reform_stage = {code} }} }}','localization_key = '+k+'_desc']).rstrip())
    title.append(b('text',['localization_key = RUS_fr_unified_army_reform']).rstrip())
    outputs[LOC]=b('defined_text',['name = RUSFrCurrentReformTitle',*title])+b('defined_text',['name = RUSFrCurrentReformDescription',*desc,b('text',['localization_key = RUS_fr_current_empty']).rstrip()])
    equipment=[]
    for inf,arm,key in [(True,True,'empty'),(True,False,'equipment_infantry_tt'),(False,True,'equipment_armour_tt'),(False,False,'equipment_base_tt')]:
        condition=('' if inf else 'NOT = { ')+'has_idea = RUS_fr_equipment_standardisation_correction'+('' if inf else ' }')+' '+('' if arm else 'NOT = { ')+'has_idea = RUS_fr_armoured_production_correction'+('' if arm else ' }')
        equipment.append(b('text',['trigger = { '+condition+' }','localization_key = RUS_fr_current_'+key]).rstrip())
    outputs[LOC]+=b('defined_text',['name = RUSFrCurrentEquipmentEffects',*equipment])
    outputs[LOC]+=b('defined_text',['name = RUSFrCurrentOfficerEffects',b('text',['trigger = { has_country_flag = RUS_fr_officer_training_penalty }','localization_key = RUS_fr_officer_attack_growth_penalty_tt']).rstrip(),b('text',['trigger = { has_country_flag = RUS_fr_officer_training_reformed }','localization_key = RUS_fr_officer_attack_growth_bonus_tt']).rstrip(),b('text',['localization_key = RUS_fr_current_empty']).rstrip()])
    outputs[LOC]+=b('defined_text',['name = RUSFrCurrentKatyushaEffects',b('text',['trigger = { has_idea = RUS_fr_hidden_katyusha_rocket_artillery }','localization_key = RUS_fr_current_katyusha_tt']).rstrip(),b('text',['localization_key = RUS_fr_current_empty']).rstrip()])
    path=Path('common/dynamic_modifiers/RUS_fr_military_reform_dynamic_modifiers.txt')
    text=(ROOT/path).read_text(encoding='utf-8-sig');edits=[]
    for n in parse(text):
        if n.k in ('RUS_fr_unified_army_reform','RUS_fr_unified_army_reform_final') and not any(x.v=='RUS_fr_current_katyusha_results_tt' for x in n.children('custom_modifier_tooltip')):
            edits.append((n.ib,n.ib,'\tcustom_modifier_tooltip = RUS_fr_current_katyusha_results_tt\n'))
    outputs[path]=replace_nodes(text,edits)
    # Remove retired scalar contributions from the existing generated easy-mode
    # aggregate without regenerating unrelated, previously stale definitions.
    path=Path('common/scripted_effects/RUS_easy_mode_ideas_effects.txt')
    text=(ROOT/path).read_text(encoding='utf-8-sig');edits=[]
    remaining={k:v for k,v in bonuses().items() if k not in stages and k not in rewards}
    remaining_fields={m for values in remaining.values() for m in values}
    for root in parse(text):
        for n in root.v:
            if n.k=='if' and n.one('limit'):
                limit=n.one('limit')
                if len(limit.v)==1 and limit.v[0].k=='has_idea' and limit.v[0].v in (stages.keys()|rewards.keys()):edits.append((n.a,n.b,''))
            elif n.k=='set_variable' and n.v[0].k.startswith('RUS_easy_mode_idea_') and n.v[0].k.removeprefix('RUS_easy_mode_idea_') not in remaining_fields:
                edits.append((n.a,n.b,''))
    cleaned=re.sub(r'(?m)^[ \t]+$','',replace_nodes(text,edits))
    outputs[path]=re.sub(r'\n\n\n+','\n\n',cleaned)
    path=Path('common/dynamic_modifiers/RUS_easy_mode_ideas_bonus.txt')
    text=(ROOT/path).read_text(encoding='utf-8-sig')
    edits=[(n.a,n.b,'') for root in parse(text) for n in root.v if n.k!='icon' and n.k not in remaining_fields]
    outputs[path]=re.sub(r'(?m)^[ \t]+\n','',replace_nodes(text,edits))
    for lang in ('simp_chinese','english','russian'):
        outputs[Path(f'localisation/{lang}/RUS_fr_current_reform_l_{lang}.yml')]='l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
    return {str(k).replace('\\','/'):v for k,v in outputs.items()}

if __name__=='__main__':
    from generation_io import cli
    cli(render_outputs,root=ROOT,description=__doc__,kr_dependency=False)
