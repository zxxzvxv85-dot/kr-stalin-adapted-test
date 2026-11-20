"""Approved economic rewards; these nodes retain their existing preview gates.

References: KR Russia relief_work, urban_housing_projects and
modernise_transsiberian. Keep recovery, construction research and state upgrades;
new managed project unlock displays are owned by national_plan_focuses.py.
"""


def focus_rewards():
    recovery = [
        'if = {',
        '\tlimit = { RUS_has_black_monday = yes }',
        '\tRUS_decrease_black_monday = yes',
        '}',
    ]
    recovery_hint = [
        'if = {',
        '\tlimit = { NOT = { has_country_flag = RUS_BM_solved } }',
        '\tcustom_effect_tooltip = tooltip_white_line',
        '\tcustom_effect_tooltip = RUS_BM_recovery_tt',
        '}',
    ]
    construction = [
        '# RUS_EASY_MODE_TECH_START',
        'if = {',
        '\tlimit = { hidden_trigger = { has_country_flag = RUS_easy_mode_enabled is_ai = no } }',
        '\tadd_tech_bonus = { name = RUS_future_domestic_621 bonus = 2 uses = 2 category = construction_tech }',
        '}',
        'else = { add_tech_bonus = { name = RUS_future_domestic_621 bonus = 1 uses = 2 category = construction_tech } }',
        '# RUS_EASY_MODE_TECH_END',
    ]
    return {
        '804': [
            'if = {',
            '\tlimit = { has_dlc_aat = yes }',
            '\teffect_tooltip = { mio:RUS_tesla_electrical_organisation = { add_mio_size = 1 } }',
            '\thidden_effect = {',
            '\t\tif = {',
            '\t\t\tlimit = { NOT = { has_country_flag = RUS_tesla_electrification_focus_reward_claimed } }',
            '\t\t\tset_country_flag = RUS_tesla_electrification_focus_reward_pending',
            '\t\t\tRUS_tesla_apply_electrification_focus_reward = yes',
            '\t\t}',
            '\t}',
            '}',
        ],
        '424': recovery + recovery_hint,
        '420': recovery + [
            f'{state} = {{ increase_state_category_by_one_level = yes }}'
            for state in (195, 242, 249, 263, 572, 651)
        ],
        '621': construction + recovery_hint,
    }
