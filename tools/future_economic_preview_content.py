"""Approved economic rewards; these nodes retain their existing preview gates.

References: KR Russia relief_work, urban_housing_projects and
modernise_transsiberian. Keep recovery, construction research and state upgrades;
new managed project unlock displays are owned by national_plan_focuses.py.
"""


PROJECT_RECOVERY_HINT = 'RUS_future_domestic_project_recovery_tt'
PROJECT_RECOVERY_TEXT = {
    'simp_chinese': '每竣工一项由此解锁的公路或铁路工程，§Y黑色星期一§!的负面效果降低§G一档§!。',
    'english': 'Each road or railway project unlocked here weakens §YBlack Monday§! by §Gone stage§! upon completion.',
    'russian': 'Каждый завершённый дорожный или железнодорожный проект, открытый этим фокусом, ослабляет эффект §YЧёрного понедельника§! на §Gодну ступень§!.',
}

RURAL_UPGRADE_COUNT = 5
RURAL_UPGRADE_HINT = 'RUS_future_domestic_rural_upgrade_tt'
RURAL_UPGRADE_TEXT = {
    'simp_chinese': f'随机选取至多§G{RURAL_UPGRADE_COUNT}§!个拥有并控制的核心乡村地区，地区等级各提高§G一级§!。',
    'english': f'Increase the state category by §Gone level§! in up to §G{RURAL_UPGRADE_COUNT}§! random owned and controlled rural core states.',
    'russian': f'Повышает категорию на §Gодин уровень§! в случайных сельских регионах (до §G{RURAL_UPGRADE_COUNT}§!), которыми мы владеем и которые контролируем и считаем национальными.',
}


def rural_upgrade_reward():
    # KR's FOP_AND_agricultiral_economy_reforms uses the same random scope
    # and native category upgrade. Mark draws to avoid hitting a state twice.
    selected = 'RUS_future_domestic_rural_upgrade_selected'
    draw = [
        '\trandom_owned_controlled_state = {',
        f'\t\tlimit = {{ is_core_of = ROOT NOT = {{ has_state_flag = {selected} }}',
        '\t\t\tOR = { has_state_category = two has_state_category = three has_state_category = four }',
        '\t\t}',
        f'\t\tset_state_flag = {selected}',
        '\t\tincrease_state_category_by_one_level = yes',
        '\t}',
    ]
    return [
        f'custom_effect_tooltip = {RURAL_UPGRADE_HINT}',
        'hidden_effect = {',
        *(draw * RURAL_UPGRADE_COUNT),
        f'\tevery_owned_state = {{ limit = {{ has_state_flag = {selected} }} clr_state_flag = {selected} }}',
        '}',
    ]


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
        f'\tcustom_effect_tooltip = {PROJECT_RECOVERY_HINT}',
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
        '486': rural_upgrade_reward(),
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
