"""State-specific industrial construction modifiers; read-only unless --write.

References: native modifiers_documentation state_production_speed_<Building>;
aat_dynamic_modifiers.txt state industrial_complex factor; KR state-control
on_action ROOT=new controller, FROM=old controller, FROM.FROM=state.
"""
import json
from pathlib import Path
from generation_io import cli

ROOT=Path(__file__).resolve().parents[1]
MOD='RUS_local_industrial_structure'

def render_outputs():
    effects='''RUS_lis_refresh_state = {
    if = {
        limit = { controller = { tag = RUS } }
        set_variable = { RUS_lis_cached_civ = building_level@industrial_complex }
        set_variable = { RUS_lis_cached_mil = building_level@arms_factory }
        set_variable = { RUS_lis_civ_denominator = RUS_lis_cached_civ }
        add_to_variable = { RUS_lis_civ_denominator = 10 }
        set_variable = { RUS_lis_mil_denominator = RUS_lis_cached_mil }
        add_to_variable = { RUS_lis_mil_denominator = 20 }
        set_variable = { RUS_lis_civ_speed = RUS_lis_cached_civ }
        multiply_variable = { RUS_lis_civ_speed = 40 }
        divide_variable = { RUS_lis_civ_speed = RUS_lis_civ_denominator }
        set_variable = { RUS_lis_mil_pressure = RUS_lis_cached_mil }
        multiply_variable = { RUS_lis_mil_pressure = 60 }
        divide_variable = { RUS_lis_mil_pressure = RUS_lis_mil_denominator }
        subtract_from_variable = { RUS_lis_civ_speed = RUS_lis_mil_pressure }
        divide_variable = { RUS_lis_civ_speed = 100 }
        set_variable = { RUS_lis_mil_speed = RUS_lis_cached_mil }
        multiply_variable = { RUS_lis_mil_speed = -50 }
        divide_variable = { RUS_lis_mil_speed = RUS_lis_mil_denominator }
        divide_variable = { RUS_lis_mil_speed = 100 }
        if = {
            limit = { NOT = { has_dynamic_modifier = { modifier = RUS_local_industrial_structure } } }
            add_dynamic_modifier = { modifier = RUS_local_industrial_structure }
        }
        force_update_dynamic_modifier = yes
    }
    else = {
        if = {
            limit = { has_dynamic_modifier = { modifier = RUS_local_industrial_structure } }
            remove_dynamic_modifier = { modifier = RUS_local_industrial_structure }
        }
    }
}
RUS_lis_refresh_country = {
    if = {
        limit = { tag = RUS }
        every_controlled_state = {
            limit = {
                OR = {
                    NOT = { has_variable = RUS_lis_cached_civ }
                    NOT = { has_variable = RUS_lis_cached_mil }
                    NOT = { check_variable = { RUS_lis_cached_civ = building_level@industrial_complex } }
                    NOT = { check_variable = { RUS_lis_cached_mil = building_level@arms_factory } }
                    NOT = { has_dynamic_modifier = { modifier = RUS_local_industrial_structure } }
                }
            }
            RUS_lis_refresh_state = yes
        }
    }
}
'''
    actions='''on_actions = {
    on_startup = { effect = { RUS = { RUS_lis_refresh_country = yes } } }
    on_daily_RUS = { effect = { RUS_lis_refresh_country = yes } }
    on_state_control_changed = {
        effect = {
            if = {
                limit = { OR = { tag = RUS FROM = { tag = RUS } } }
                FROM.FROM = { RUS_lis_refresh_state = yes }
            }
        }
    }
}
'''
    modifier='''RUS_local_industrial_structure = {
    icon = GFX_modifiers_generic_construction
    enable = { controller = { tag = RUS } }
    state_production_speed_industrial_complex_factor = RUS_lis_civ_speed
    state_production_speed_arms_factory_factor = RUS_lis_mil_speed
}
'''
    loc={MOD:'地方工业结构',MOD+'_desc':''}
    outputs={'common/scripted_effects/RUS_local_industrial_structure.txt':effects,
             'common/on_actions/RUS_local_industrial_structure.txt':actions,
             'common/dynamic_modifiers/RUS_local_industrial_structure.txt':modifier}
    for lang in ('simp_chinese','english','russian'):
        outputs[f'localisation/{lang}/RUS_local_industrial_structure_l_{lang}.yml']='l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
    return outputs

if __name__=='__main__':cli(render_outputs,root=ROOT,description=__doc__)
