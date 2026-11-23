"""Socialist industrial recovery, generated alongside the economic focuses."""
from pathlib import Path
from decimal import Decimal

OLD = 'RUS_opening_disordered_industry'
PREFIX = 'RUS_disordered_industry'
REFRESH = PREFIX + '_refresh'
PREVIEW = PREFIX + '_preview'
DISCOUNT_IDEA = PREFIX + '_federal'
FEDERAL_PICTURE = DISCOUNT_IDEA
FEDERAL_TEXTURE = 'gfx/interface/ideas/RUS_disordered_industry_federal.png'
DISCOUNT = f'has_idea = {DISCOUNT_IDEA}'
COOPERATIVE_IDEA = PREFIX + '_cooperative'
COOPERATIVE_TEXTURE = 'gfx/interface/ideas/RUS_disordered_industry_cooperative.png'
COOPERATIVE_PLAN_IDEA = COOPERATIVE_IDEA + '_planned'
COOPERATIVE_FOCUS = 'RUS_future_domestic_166'
COOPERATIVE_PRODUCTION_FOCUS = 'RUS_future_domestic_629'
LABOR_OVERSIGHT_FOCUS = 'RUS_future_domestic_179'
LABOR_OVERSIGHT_SCORE = 2
DEMOCRATIC_EFFICIENCY_FOCUS = 'RUS_future_domestic_177'
PRODUCERS_PLAN_FOCUS = 'RUS_future_domestic_631'
PRODUCERS_PLAN_IDEA = 'RUS_producers_common_plan'
PRODUCERS_EDUCATION_COST_FACTOR = .9
COOPERATIVE_EFFECTS = {
    COOPERATIVE_PRODUCTION_FOCUS: 'crop_bonus',
    LABOR_OVERSIGHT_FOCUS: 'agriculture_score',
    DEMOCRATIC_EFFICIENCY_FOCUS: 'machine_wear',
}
TRUSTS_IDEA = PREFIX + '_trusts'
COOPERATIVE_MONTHLY_EDUCATION = 0.5
TRUSTS_DAILY_RESOURCES = 0.5
MONTHLY_EDUCATION = PREFIX + '_monthly_education'
ROUTE_BONUS_TOOLTIPS = {
    'federal': PREFIX + '_discount_tt',
    'cooperative': PREFIX + '_cooperative_education_tt',
    'trusts': PREFIX + '_trusts_resources_tt',
}
ROUTES = {'169': 'federal', '166': 'cooperative', '163': 'trusts'}
ROUTE_ORDER = tuple(ROUTES.values())
POLICIES = {'422': 'federal', '421': 'cooperative', '486': 'cooperative',
            '377': 'trusts', '487': 'trusts'}
CHOICE = PREFIX + '_first_policy'
RESEARCH_FOCUS = 'RUS_future_domestic_176'
FEDERAL_FOCUS = 'RUS_future_domestic_169'
RESEARCH_FACTOR = PREFIX + '_research_factor'
RESEARCH_REDUCTION = PREFIX + '_research_reduction'
RESEARCH_STEP = .002
RESEARCH_TOOLTIP = PREFIX + '_research_tt'
ACCOUNTING_FOCUS = 'RUS_future_domestic_625'
COORDINATION_FOCUS = 'RUS_future_domestic_626'
LONG_RANGE_FOCUS = 'RUS_future_domestic_182'
PROJECTS_REQUIRED = 30
GOAL_REFUND = .50
REGIONAL_DURATION_FACTOR = .90
LONG_RANGE_SCORE = 1
FEDERAL_POLICIES = {
    ACCOUNTING_FOCUS: 'accounting',
    COORDINATION_FOCUS: 'coordination',
    LONG_RANGE_FOCUS: 'long_range',
}
PENALTIES = {
    'stability_factor': '-.10',
    'production_speed_buildings_factor': '-.10',
    'consumer_goods_factor': '.10',
    # The engine exposes conversion cost. Double base cost halves base speed.
    'conversion_cost_civ_to_mil_factor': '1',
    'production_cost_industrial_complex_factor': '.025',
    'production_cost_arms_factory_factor': '.50',
    'production_cost_infrastructure_factor': '.025',
}
FINALS = {
    'federal': dict(production_speed_buildings_factor=.05,
                    production_factory_efficiency_gain_factor=-.20,
                    industrial_capacity_factory=-.05, consumer_goods_expected_value=-.025,
                    production_cost_industrial_complex_factor=-.10, political_power_factor=-.05,
                    production_cost_infrastructure_factor=-.10,
                    custom_modifier_tooltip=ROUTE_BONUS_TOOLTIPS['federal']),
    'cooperative': dict(production_cost_infrastructure_factor=-.25,
                        resource_trade_cost_bonus_per_factory=2, stability_factor=.05,
                        consumer_goods_expected_value=.05, global_building_slots_factor=.10,
                        monthly_population=.10, production_cost_arms_factory_factor=.10,
                        military_industrial_organization_funds_gain=-.20, research_speed_factor=-.05,
                        custom_modifier_tooltip=ROUTE_BONUS_TOOLTIPS['cooperative']),
    'trusts': dict(production_speed_buildings_factor=.10, industrial_capacity_factory=.03,
                   political_power_factor=-.10, stability_factor=-.05, war_support_factor=-.05,
                   military_industrial_organization_funds_gain=.10, resource_trade_cost_bonus_per_factory=1,
                   production_cost_industrial_complex_factor=-.10, production_cost_arms_factory_factor=-.05,
                   custom_modifier_tooltip=ROUTE_BONUS_TOOLTIPS['trusts']),
}

# Use the modifier labels and any icons already supplied by vanilla and KR. The three
# building-cost labels are supplied by this mod.
PREVIEW_ROWS = {
    'monthly_population': 'MODIFIER_GLOBAL_MONTHLY_POPULATION',
    'political_power_factor': 'MODIFIER_POLITICAL_POWER_FACTOR',
    'consumer_goods_factor': 'MODIFIER_CONSUMER_GOODS_FACTOR',
    'consumer_goods_expected_value': 'MODIFIER_CONSUMER_GOODS_EXPECTED_VALUE',
    'stability_factor': 'MODIFIER_STABILITY_FACTOR',
    'war_support_factor': 'MODIFIER_WAR_SUPPORT_FACTOR',
    'conversion_cost_civ_to_mil_factor': 'MODIFIER_CONVERSION_COST_CIV_TO_MIL_FACTOR',
    'global_building_slots': 'MODIFIER_GLOBAL_BUILDING_SLOTS',
    'global_building_slots_factor': 'MODIFIER_GLOBAL_BUILDING_SLOTS_FACTOR',
    'production_speed_buildings_factor': 'MODIFIER_PRODUCTION_SPEED_BUILDINGS_FACTOR',
    'production_factory_efficiency_gain_factor': 'MODIFIER_PRODUCTION_FACTORY_EFFICIENCY_GAIN_FACTOR',
    'research_speed_factor': 'MODIFIER_RESEARCH_SPEED_FACTOR',
    'industrial_capacity_factory': 'MODIFIER_INDUSTRIAL_CAPACITY_FACTOR',
    'resource_trade_cost_bonus_per_factory': 'MODIFIER_RESOURCE_TRADE_COST_BONUS_PER_FACTORY',
    'military_industrial_organization_funds_gain': 'MODIFIER_MIO_FUNDS_GAIN',
    'production_cost_infrastructure_factor': 'modifier_production_cost_infrastructure_factor',
    'production_cost_arms_factory_factor': 'modifier_production_cost_arms_factory_factor',
    'production_cost_industrial_complex_factor': 'modifier_production_cost_industrial_complex_factor',
    'production_speed_rail_way_factor': 'modifier_production_speed_rail_way_factor',
}
INTEGER_ROWS = {'global_building_slots', 'resource_trade_cost_bonus_per_factory'}
NEUTRAL_ROWS = {'consumer_goods_factor', 'consumer_goods_expected_value'}
COST_ROWS = {'conversion_cost_civ_to_mil_factor', 'production_cost_infrastructure_factor',
             'production_cost_arms_factory_factor', 'production_cost_industrial_complex_factor'}


def route_preview_key(route, tier):
    return f'{PREVIEW}_{route}_{tier}_tt'


def route_preview_text(before, after, heading, bonus):
    """Join modifier deltas and the bonus in a single contiguous tooltip."""
    assert (before.keys() | after.keys()) - {'custom_modifier_tooltip'} <= PREVIEW_ROWS.keys()
    rows = [f'§Y${OLD}$§!{heading}']
    for modifier, label in PREVIEW_ROWS.items():
        delta = Decimal(str(after.get(modifier, 0))) - Decimal(str(before.get(modifier, 0)))
        if not delta:
            continue
        color = 'Y' if modifier in NEUTRAL_ROWS else (
            'G' if (delta < 0 if modifier in COST_ROWS else delta > 0) else 'R')
        amount = f'{int(delta):+d}' if modifier in INTEGER_ROWS else f'{delta*100:+.2f}%'
        rows.append(f'${label}$: §{color}{amount}§!')
    rows.append(f'${bonus}$')
    return '\\n'.join(rows)


def economy_branch(edges):
    result = {'RUS_future_domestic_424'}
    while True:
        expanded = result | {target for source, target in edges if source in result}
        if expanded == result:
            return sorted(result)
        result = expanded


def focus_reward(focus, branch):
    effects = []
    if focus == PRODUCERS_PLAN_FOCUS:
        effects.append(f'effect_tooltip = {{ swap_ideas = {{ remove_idea = {COOPERATIVE_IDEA} add_idea = {COOPERATIVE_PLAN_IDEA} }} }}')
    suffix = focus.rsplit('_', 1)[-1]
    policy = POLICIES.get(suffix)
    if policy:
        effects.append(
            f'if = {{ limit = {{ hidden_trigger = {{ NOT = {{ has_variable = {CHOICE} }} }} }} '
            f'custom_effect_tooltip = {PREFIX}_{policy}_first_tt '
            f'hidden_effect = {{ set_variable = {{ {CHOICE} = {ROUTE_ORDER.index(policy)+1} }} }} }}')
    if focus in branch:
        preview = f'{PREVIEW}_{ROUTES[suffix]}' if suffix in ROUTES else PREVIEW
        effects.append(f'{preview} = yes')
        effects.append(f'hidden_effect = {{ {REFRESH} = yes }}')
    if focus == RESEARCH_FOCUS:
        effects.extend([
            f'custom_effect_tooltip = {RESEARCH_TOOLTIP}',
            f'hidden_effect = {{ RUS_np_refresh = yes }}',
        ])
    if focus in FEDERAL_POLICIES:
        effects.append(f'custom_effect_tooltip = {PREFIX}_{FEDERAL_POLICIES[focus]}_tt')
    if focus == COORDINATION_FOCUS:
        effects.append('hidden_effect = { RUS_np_refresh = yes }')
    if focus in COOPERATIVE_EFFECTS:
        effects.append(f'custom_effect_tooltip = {PREFIX}_{COOPERATIVE_EFFECTS[focus]}_tt')
    if focus == DEMOCRATIC_EFFICIENCY_FOCUS:
        effects.append('hidden_effect = { if = { limit = { has_country_flag = RUS_nat_enabled } RUS_nat_refresh = yes } }')
    if focus == PRODUCERS_PLAN_FOCUS:
        effects.append('hidden_effect = { if = { limit = { has_country_flag = RUS_education_system_active } RUS_education_refresh = yes } }')
    return effects


def route_requirement(suffix):
    route = ROUTES[suffix]
    return (f'custom_trigger_tooltip = {{ tooltip = {PREFIX}_{route}_requires_tt '
            f'check_variable = {{ {CHOICE} = {ROUTE_ORDER.index(route)+1} }} }}')


def idea_previews(tiers, route_tiers):
    # Generic recovery can use the engine's idea diff. The final previews
    # join deltas and scripted bonuses so the engine cannot split the blocks.
    def preview(name, swaps, fallback=None, route=None):
        lines = [f'{name} = {{']
        for index, (before, after) in enumerate(swaps):
            swap = f'swap_ideas = {{ remove_idea = {before} add_idea = {after} }}'
            lines.extend([
                f'\t{"else_if" if index else "if"} = {{',
                f'\t\tlimit = {{ hidden_trigger = {{ has_idea = {before} }} }}',
            ])
            if route:
                tier = before.rsplit('_', 1)[-1]
                lines.append(f'\t\tcustom_effect_tooltip = {route_preview_key(route, tier)}')
            else:
                lines.append(f'\t\teffect_tooltip = {{ {swap} }}')
            lines.append('\t}')
        if fallback:
            lines.append(f'\telse = {{ {fallback} = yes }}')
        return [*lines, '}', '']

    swaps = list(zip(tiers, tiers[1:]))
    for route, variants in route_tiers.items():
        swaps.extend(zip(variants, [*variants[1:], f'{PREFIX}_{route}']))
    lines = preview(PREVIEW, swaps)
    for route in ROUTE_ORDER:
        final = f'{PREFIX}_{route}'
        fallback = PREVIEW
        if route in route_tiers:
            fallback = f'{PREVIEW}_{route}_transition'
            lines.extend(preview(fallback, zip(tiers[:9], route_tiers[route][1:]), PREVIEW))
        lines.extend(preview(f'{PREVIEW}_{route}',
                             [(tiers[9], final), (tiers[10], final)],
                             fallback, route))
    return lines


def outputs(branch):
    tiers = [f'{PREFIX}_{index}' for index in range(11)]
    route_tiers = {route: [f'{PREFIX}_{route}_{index}' for index in range(10)]
                   for route in ('federal', 'cooperative')}
    federal_tiers = route_tiers['federal']
    cooperative_tiers = route_tiers['cooperative']
    definitions = {}
    for index, idea in enumerate(tiers):
        remaining = Decimal(10-index)/10
        definitions[idea] = {
            key: format(Decimal(initial)*remaining, 'f')
            for key, initial in PENALTIES.items() if remaining
        }
        trade = -((10-index+2)//5)
        if trade:
            definitions[idea]['resource_trade_cost_bonus_per_factory'] = trade
        definitions[idea].update(production_speed_rail_way_factor=.025, global_building_slots=1)
    for variants in route_tiers.values():
        definitions.update({variant: definitions[base] for base, variant in zip(tiers, variants)})
    definitions.update({f'{PREFIX}_{suffix}': mod for suffix,mod in FINALS.items()})
    definitions[COOPERATIVE_PLAN_IDEA] = dict(FINALS['cooperative'], stability_weekly=.0025,
                                              political_power_factor=.05)
    ideas = ['ideas = {', '\tcountry = {']
    for idea, modifiers in definitions.items():
        federal = idea in federal_tiers or idea == DISCOUNT_IDEA
        cooperative = idea in [COOPERATIVE_IDEA, COOPERATIVE_PLAN_IDEA, *cooperative_tiers]
        picture = (FEDERAL_PICTURE if federal else COOPERATIVE_IDEA if cooperative
                   else 'POL_disjointed_industry')
        ideas.extend([f'\t\t{idea} = {{', f'\t\t\tpicture = {picture}',
                      '\t\t\tallowed = { original_tag = RUS }', '\t\t\tremoval_cost = -1',
                      '\t\t\tmodifier = {'])
        ideas.extend(f'\t\t\t\t{key} = {value}' for key, value in modifiers.items()
                     if not cooperative or key != 'custom_modifier_tooltip')
        if not cooperative:
            ideas.append(f'\t\t\t\tcustom_modifier_tooltip = {PREFIX}_research_active_tt')
        if idea in tiers or federal:
            ideas.extend(f'\t\t\t\tcustom_modifier_tooltip = {PREFIX}_{policy}_active_tt'
                         for policy in FEDERAL_POLICIES.values())
        if cooperative:
            ideas.append(f'\t\t\t\tcustom_modifier_tooltip = {idea}_effects_tt')
        ideas.extend(['\t\t\t}', '\t\t}'])
    # Keep the old ID resolvable until existing saves migrate on refresh.
    ideas.extend(['\t}', '\thidden_ideas = {',
                  f'\t\t{PRODUCERS_PLAN_IDEA} = {{ allowed = {{ always = no }} }}', '\t}', '}'])

    # Recompute from completed IDs so a replay or save reload cannot add a layer twice.
    count = PREFIX + '_count'
    have = 'OR = { ' + ' '.join(f'has_idea = {idea}' for idea in [OLD,*definitions]) + ' }'
    effect = [f'{REFRESH} = {{', '\tif = {',
              f'\t\tlimit = {{ original_tag = RUS has_socialist_government = yes {have} }}',
              f'\t\tset_temp_variable = {{ {count} = 0 }}']
    for focus in branch:
        effect.append(f'\t\tif = {{ limit = {{ has_completed_focus = {focus} }} add_to_temp_variable = {{ {count} = 1 }} }}')
    cases = []
    for focus, route in ROUTES.items():
        condition = f'check_variable = {{ {count} > 9 }} has_completed_focus = RUS_future_domestic_{focus}'
        if route == 'cooperative':
            cases.append((f'{condition} has_completed_focus = {PRODUCERS_PLAN_FOCUS}', COOPERATIVE_PLAN_IDEA))
        cases.append((condition, f'{PREFIX}_{route}'))
    for focus, route in ((FEDERAL_FOCUS, 'federal'), (COOPERATIVE_FOCUS, 'cooperative')):
        cases.extend((f'has_completed_focus = {focus} check_variable = {{ {count} = {index} }}', idea)
                     for index, idea in enumerate(route_tiers[route]))
    cases.extend([(f'check_variable = {{ {count} > 9 }}',tiers[10]),
                  *((f'check_variable = {{ {count} = {index} }}',tiers[index]) for index in range(10))])
    for index, (condition, idea) in enumerate(cases):
        others = ' '.join(other for other in [OLD,*definitions] if other != idea)
        effect.extend([f'\t\t{"else_if" if index else "if"} = {{',
                       f'\t\t\tlimit = {{ {condition} }}',
                       f'\t\t\tif = {{ limit = {{ NOT = {{ has_idea = {idea} }} }}',
                       f'\t\t\t\tremove_ideas = {{ {others} }}',
                       f'\t\t\t\tadd_ideas = {idea}',
                       '\t\t\t\tRUS_np_refresh_prices = yes',
                       '\t\t\t}', '\t\t}'])
    effect.extend(['\t}',
                   f'\tif = {{ limit = {{ has_idea = {PRODUCERS_PLAN_IDEA} }}',
                   f'\t\tremove_ideas = {{ {PRODUCERS_PLAN_IDEA} }}',
                   '\t}', '}', ''])
    effect.extend(idea_previews(tiers, route_tiers))
    effect.extend(f'''{MONTHLY_EDUCATION} = {{
\tif = {{
\t\tlimit = {{
\t\t\thas_socialist_government = yes
\t\t\thas_country_flag = RUS_education_system_active
\t\t\tOR = {{ has_idea = {COOPERATIVE_IDEA} has_idea = {COOPERATIVE_PLAN_IDEA} }}
\t\t}}
\t\tadd_to_variable = {{ RUS_basic_education_level = {COOPERATIVE_MONTHLY_EDUCATION} }}
\t\tadd_to_variable = {{ RUS_higher_education_level = {COOPERATIVE_MONTHLY_EDUCATION} }}
\t\tRUS_education_refresh = yes
\t}}
}}'''.splitlines())
    actions = f'''on_actions = {{
\ton_ruling_party_change_immediate = {{ effect = {{ {REFRESH} = yes }} }}
\ton_daily_RUS = {{ effect = {{ {REFRESH} = yes }} }}
\ton_monthly_RUS = {{ effect = {{ {MONTHLY_EDUCATION} = yes }} }}
}}
'''
    result = {
        Path('common/dynamic_modifiers/RUS_disordered_industry.txt'): f'''{PREFIX}_democratic_consumer = {{
	enable = {{
		has_country_flag = RUS_nat_enabled
		has_completed_focus = {DEMOCRATIC_EFFICIENCY_FOCUS}
	}}
	consumer_goods_expected_value = RUS_nat_democratic_consumer
}}
''',
        Path('interface/RUS_disordered_industry.gfx'): f'''spriteTypes = {{
	spriteType = {{
		name = "GFX_idea_{FEDERAL_PICTURE}"
		texturefile = "{FEDERAL_TEXTURE}"
	}}
	spriteType = {{
		name = "GFX_idea_{COOPERATIVE_IDEA}"
		texturefile = "{COOPERATIVE_TEXTURE}"
	}}
}}
''',
        Path('common/ideas/RUS_disordered_industry.txt'): '\n'.join(ideas)+'\n',
        Path('common/scripted_effects/RUS_disordered_industry.txt'): '\n'.join(effect).rstrip()+'\n',
        Path('common/on_actions/RUS_disordered_industry.txt'): actions,
        Path('common/scripted_localisation/RUS_disordered_industry_loc.txt'): f'''defined_text = {{
	name = RUSIndustrialSituationName
	text = {{
		trigger = {{ has_completed_focus = {FEDERAL_FOCUS} }}
		localization_key = {PREFIX}_federal_name
	}}
	text = {{
		trigger = {{ has_completed_focus = {COOPERATIVE_FOCUS} }}
		localization_key = {PREFIX}_cooperative_name
	}}
	text = {{ localization_key = {OLD} }}
}}

defined_text = {{
	name = RUSIndustrialResearchTooltip
	text = {{
		trigger = {{ has_completed_focus = {RESEARCH_FOCUS} }}
		localization_key = {PREFIX}_research_progress_tt
	}}
	text = {{ localization_key = {PREFIX}_research_blank_tt }}
}}
''',
    }
    policy_loc = Path('common/scripted_localisation/RUS_disordered_industry_loc.txt')
    policy_tooltips = FEDERAL_POLICIES | COOPERATIVE_EFFECTS
    for focus, policy in policy_tooltips.items():
        tooltip = f'{policy}_tt' if focus in FEDERAL_POLICIES else f'{policy}_row_tt'
        result[policy_loc] += f'''
defined_text = {{
	name = RUSIndustrialPolicy_{policy}
	text = {{
		trigger = {{ has_completed_focus = {focus} }}
		localization_key = {PREFIX}_{tooltip}
	}}
	text = {{ localization_key = {PREFIX}_research_blank_tt }}
}}
'''
    reform_trigger = ' '.join(f'has_completed_focus = {focus}' for focus in COOPERATIVE_EFFECTS)
    for name, key in (('RUSCooperativeReform', 'reform_group'),
                      ('RUSCooperativeReformAfterEducation', 'reform_group_after_education')):
        result[policy_loc] += f'''
defined_text = {{
	name = {name}
	text = {{
		trigger = {{ OR = {{ {reform_trigger} }} }}
		localization_key = {PREFIX}_{key}_tt
	}}
	text = {{ localization_key = {PREFIX}_research_blank_tt }}
}}
'''
    for lang, label, pp_cost, resource_cost in (
        ('simp_chinese', '混乱的工业', '工业决议政治点数花费', '工业决议§C建设资源§!花费'),
        ('english', 'Disordered Industry', 'Industrial Decision Political Power Cost',
         'Industrial Decision §CConstruction Resource§! Cost'),
        ('russian', 'Дезорганизованная промышленность', 'Затраты политической власти на промышленные решения',
         'Затраты §Cстроительных ресурсов§! на промышленные решения'),
    ):
        discount_text = (f'£pol_power£ {pp_cost}: §G-20%§!\\n'
                         f'£RUS_np_resources_texticon£ {resource_cost}: §G-20%§!')
        lines = [f'l_{lang}:', f' {ROUTE_BONUS_TOOLTIPS["federal"]}:0 "{discount_text}"']
        federal_name, research_condition, duration_label, total_label = {
            'simp_chinese': ('工业现状：联邦计划委员会', '每项已完成的科技',
                             '工业决议所需时间', '科技累计减免'),
            'english': ('State of Industry: Federal Planning Commission', 'Per researched technology',
                        'Industrial Decision Duration', 'Cumulative Research Reduction'),
            'russian': ('Состояние промышленности: Федеральная плановая комиссия',
                        'За каждую изученную технологию',
                        'Срок выполнения промышленных решений', 'Суммарное снижение за технологии'),
        }[lang]
        per_tech = f'§G-{RESEARCH_STEP*100:g}%§!'
        research_text = '\\n'.join([
            f'£research_speed_icon §g{research_condition}§!',
            f'£clock_texticon {duration_label}: {per_tech}',
            f'£pol_power£ {pp_cost}: {per_tech}',
            f'£RUS_np_resources_texticon£ {resource_cost}: {per_tech}',
        ])
        lines.extend([
            f' {PREFIX}_federal_name:0 "{federal_name}"',
            f' {RESEARCH_TOOLTIP}:0 "{research_text}"',
            f' {PREFIX}_research_active_tt:0 "[RUSIndustrialResearchTooltip]"',
            f' {PREFIX}_research_blank_tt:0 ""',
            f' {PREFIX}_research_progress_tt:0 "${RESEARCH_TOOLTIP}$\\n{total_label}: §G[?{RESEARCH_REDUCTION}|=1%]§!"',
        ])
        refund, refund_condition, duration, duration_condition, score, requirement = {
            'simp_chinese': ('正常竣工时返还的§C建设资源§!比例',
                             '若两项追加目标均已达成',
                             '工业与资源类决议所需时间',
                             '若所在工业区已有公路或铁路工程竣工',
                             '工业决议竣工获得的§Y一五计划分数§!',
                             '至少完成 {required} 项不同的工业决议（当前：§Y[?RUS_np_completed_projects|0]§!）'),
            'english': ('§CConstruction Resource§! Refund on Completion',
                        'If both additional objectives are met',
                        'Industry and Resource Decision Duration',
                        'If a road or railway project has been completed in the industrial region',
                        '§YFirst Five-Year Plan Score§! per Completed Industrial Decision',
                        'Complete at least {required} distinct industrial decisions (current: §Y[?RUS_np_completed_projects|0]§!)'),
            'russian': ('Возврат §Cстроительных ресурсов§! при завершении проекта',
                        'Если выполнены обе дополнительные задачи',
                        'Срок выполнения промышленных и ресурсных решений',
                        'Если в промышленном районе завершён дорожный или железнодорожный проект',
                        '§YОчки первой пятилетки§! за завершённое промышленное решение',
                        'Завершено не менее {required} разных промышленных решений (сейчас: §Y[?RUS_np_completed_projects|0]§!)'),
        }[lang]
        policy_text = {
            'accounting': f'§g{refund_condition}§!\\n£RUS_np_resources_texticon£ {refund}: §G{GOAL_REFUND:.0%}§!',
            'coordination': f'§g{duration_condition}§!\\n£clock_texticon {duration}: §G-{1-REGIONAL_DURATION_FACTOR:.0%}§!',
            'long_range': f'£decision_icon_small£ {score}: §G+{LONG_RANGE_SCORE}§!',
        }
        for policy, value in policy_text.items():
            lines.append(f' {PREFIX}_{policy}_tt:0 "{value}"')
        for policy in FEDERAL_POLICIES.values():
            lines.append(f' {PREFIX}_{policy}_active_tt:0 "[RUSIndustrialPolicy_{policy}]"')
        lines.append(f' {PREFIX}_long_range_requires_tt:0 "{requirement.format(required=PROJECTS_REQUIRED)}"')
        basic_text, higher_text, education_condition, resources_text, resources_condition, heading = {
            'simp_chinese': ('每月§C基础教育水平§!', '每月§Y高等教育水平§!', '教育系统启用后',
                             '每日§C建设资源§!收入 §G+{resources}§!', '国家建设账本开启后', '追加效果：'),
            'english': ('Monthly §CBasic Education§!', 'Monthly §YHigher Education§!', 'While education reform is active',
                        'Daily §CConstruction Resource§! Income §G+{resources}§!',
                        'While the construction account is open', ' is modified by'),
            'russian': ('Ежемесячный прирост §Cначального образования§!', 'Ежемесячный прирост §Yвысшего образования§!',
                        'При действующей реформе образования',
                        'Ежедневный доход §Cстроительных ресурсов§! §G+{resources}§!',
                        'При открытом строительном счёте', ' — изменение эффектов:'),
        }[lang]
        gain = f'§G+{COOPERATIVE_MONTHLY_EDUCATION}§!'
        education_text = (f'§g{education_condition}§!\\n'
                          f'£RUS_edu_basic_texticon£ {basic_text}: {gain}\\n'
                          f'£RUS_edu_higher_texticon£ {higher_text}: {gain}')
        cooperative_name, reform, crop_label, crop_names, score_label = {
            'simp_chinese': ('工业现状：建立合作社', '土改启用后', '季度{crop}产量', ('小麦', '黑麦', '甜菜'), '农业配套工业决议竣工获得的§Y土改分数§!'),
            'english': ('State of Industry: Establish Cooperatives', 'After land reform is enabled', 'Quarterly {crop} Yield', ('Wheat', 'Rye', 'Beet'), '§YLand Reform Score§! per Completed Agricultural Support Project'),
            'russian': ('Состояние промышленности: Создание кооперативов', 'После запуска земельной реформы', 'Квартальная урожайность: {crop}', ('Пшеница', 'Рожь', 'Свёкла'), '§YОчки земельной реформы§! за завершение аграрного проекта'),
        }[lang]
        crops = '\\n'.join(f'{crop_label.format(crop=crop)}: §G+{gain}§!'
                          for crop, gain in zip(crop_names, ('0.2', '0.2', '0.3')))
        wear = {
            'simp_chinese': '季度农机损耗率',
            'english': 'Quarterly Machinery Wear',
            'russian': 'Квартальный износ сельхозтехники',
        }[lang]
        factory, wheat, requirement = {
            'simp_chinese': ('每座民用工厂', '季度小麦产量', '土改分数大于 §Y100§!（当前：§Y[?RUS_agri_display_score|2]§!）'),
            'english': ('per Civilian Factory', 'Quarterly Wheat Yield', 'Land reform score above §Y100§! (current: §Y[?RUS_agri_display_score|2]§!)'),
            'russian': ('за каждую гражданскую фабрику', 'Квартальный урожай пшеницы', 'Очки земельной реформы выше §Y100§! (сейчас: §Y[?RUS_agri_display_score|2]§!)'),
        }[lang]
        def factory_effect(icon, label, amount, color='G'):
            name = f'{factory}{label}' if lang == 'simp_chinese' else f'{label} {factory}'
            return f'{icon} {name}: §{color}{amount}§!'
        democratic_effects = '\\n'.join([
            f'£RUS_nat_text_machinery£ {wear}: §G-5%§!',
            factory_effect('£RUS_nat_text_food£', wheat, '+0.05'),
            factory_effect('£consumer_goods_texticon£', '$MODIFIER_CONSUMER_GOODS_EXPECTED_VALUE$', '-0.02%', color='Y'),
        ])
        lines.extend([
            f' {PREFIX}_cooperative_name:0 "{cooperative_name}"',
            f' {PREFIX}_democratic_efficiency_requires_tt:0 "{requirement}"',
            f' {PREFIX}_democratic_consumer:0 "${PREFIX}_cooperative_name$"',
            f' {PREFIX}_reform_group_tt:0 "§g{reform}§![RUSIndustrialPolicy_crop_bonus][RUSIndustrialPolicy_agriculture_score][RUSIndustrialPolicy_machine_wear]"',
            f' {PREFIX}_reform_group_after_education_tt:0 "\\n${PREFIX}_reform_group_tt$"',
        ])
        reform_rows = {
            'crop_bonus': crops,
            'agriculture_score': f'£decision_icon_small£ {score_label}: §G+{LABOR_OVERSIGHT_SCORE}§!',
            'machine_wear': democratic_effects,
        }
        for policy, row in reform_rows.items():
            lines.extend([f' {PREFIX}_{policy}_tt:0 "§g{reform}§!\\n{row}"',
                          f' {PREFIX}_{policy}_row_tt:0 "\\n{row}"'])
        for idea in cooperative_tiers:
            lines.append(f' {idea}_effects_tt:0 "[RUSCooperativeReform]"')
        education_block = '$' + ROUTE_BONUS_TOOLTIPS['cooperative'] + '$'
        reform_block = '[RUSCooperativeReformAfterEducation]'
        lines.extend([
            f' {COOPERATIVE_IDEA}_effects_tt:0 "{education_block}{reform_block}"',
            f' {COOPERATIVE_PLAN_IDEA}_effects_tt:0 "{education_block}\\n${PRODUCERS_PLAN_IDEA}_education_cost_tt${reform_block}"',
        ])
        education_cost = {
            'simp_chinese': '教育改革决议政治点数花费',
            'english': 'Education Reform Decision Political Power Cost',
            'russian': 'Затраты политической власти на решения по реформе образования',
        }[lang]
        lines.extend([
            f' {PRODUCERS_PLAN_IDEA}:0 "$' + PRODUCERS_PLAN_FOCUS + '$"',
            f' {PRODUCERS_PLAN_IDEA}_education_cost_tt:0 "£pol_power£ {education_cost}: §G-{1-PRODUCERS_EDUCATION_COST_FACTOR:.0%}§!"',
        ])
        resources_text = ('£RUS_np_resources_texticon£ ' + resources_text.format(resources=TRUSTS_DAILY_RESOURCES)
                          + f'\\n§g{resources_condition}§!')
        lines.extend([f' {ROUTE_BONUS_TOOLTIPS["cooperative"]}:0 "{education_text}"',
                      f' {ROUTE_BONUS_TOOLTIPS["trusts"]}:0 "{resources_text}"'])
        for route, bonus in ROUTE_BONUS_TOOLTIPS.items():
            for tier in (9, 10):
                preview_text = route_preview_text(definitions[tiers[tier]], FINALS[route], heading, bonus)
                lines.append(f' {route_preview_key(route, tier)}:0 "{preview_text}"')
        infrastructure = {'simp_chinese':'§Y基础设施§!建造花费',
                          'english':'§YInfrastructure§! construction cost',
                          'russian':'Стоимость строительства §Yинфраструктуры§!'}[lang]
        lines.append(f' modifier_production_cost_infrastructure_factor:0 "{infrastructure}"')
        first = {'simp_chinese':'若率先完成本国策，将锁定「{focus}」路线。',
                 'english':'Completing this policy first commits Russia to {focus}.',
                 'russian':'Если выполнить эту меру первой, откроется путь «{focus}».'}[lang]
        for suffix,route in ROUTES.items():
            key = f'RUS_future_domestic_{suffix}'
            lines.append(f' {PREFIX}_{route}_first_tt:0 "{first.format(focus=("$"+key+"$"))}"')
            policies = [f'$RUS_future_domestic_{p}$' for p,r in POLICIES.items() if r == route]
            if lang == 'simp_chinese':
                requirement = '五项政策中最先完成的是' + '或'.join(f'「{p}」' for p in policies)
            elif lang == 'english':
                requirement = 'The first completed policy was ' + ' or '.join(policies)
            else:
                requirement = 'Первая выполненная мера: ' + ' или '.join(policies)
            lines.append(f' {PREFIX}_{route}_requires_tt:0 "{requirement}"')
        for idea in definitions:
            name = (f'${PREFIX}_federal_name$' if idea == DISCOUNT_IDEA or idea in federal_tiers else
                    f'${PREFIX}_cooperative_name$' if idea in [COOPERATIVE_IDEA, COOPERATIVE_PLAN_IDEA, *cooperative_tiers] else
                    '[RUSIndustrialSituationName]' if idea in tiers else label)
            lines.extend([f' {idea}:0 "{name}"', f' {idea}_desc:0 "${OLD}_desc$"'])
        result[Path(f'localisation/{lang}/RUS_disordered_industry_l_{lang}.yml')] = '\n'.join(lines)+'\n'
    return {path: text.encode('utf-8-sig' if path.suffix == '.yml' else 'utf-8')
            for path, text in result.items()}
