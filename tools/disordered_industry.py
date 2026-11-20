"""Socialist industrial recovery, generated alongside the economic focuses."""
from pathlib import Path
from decimal import Decimal

OLD = 'RUS_opening_disordered_industry'
PREFIX = 'RUS_disordered_industry'
REFRESH = PREFIX + '_refresh'
PREVIEW = PREFIX + '_preview'
DISCOUNT_IDEA = PREFIX + '_federal'
DISCOUNT = f'has_idea = {DISCOUNT_IDEA}'
COOPERATIVE_IDEA = PREFIX + '_cooperative'
TRUSTS_IDEA = PREFIX + '_trusts'
COOPERATIVE_MONTHLY_EDUCATION = 0.5
TRUSTS_DAILY_RESOURCES = 0.5
MONTHLY_EDUCATION = PREFIX + '_monthly_education'
ROUTE_BONUS_TOOLTIPS = {
    'cooperative': PREFIX + '_cooperative_education_tt',
    'trusts': PREFIX + '_trusts_resources_tt',
}
ROUTES = {'169': 'federal', '166': 'cooperative', '163': 'trusts'}
ROUTE_ORDER = tuple(ROUTES.values())
POLICIES = {'422': 'federal', '421': 'cooperative', '486': 'cooperative',
            '377': 'trusts', '487': 'trusts'}
CHOICE = PREFIX + '_first_policy'
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
                    custom_modifier_tooltip=PREFIX+'_discount_tt'),
    'cooperative': dict(production_cost_infrastructure_factor=-.25,
                        resource_trade_cost_bonus_per_factory=2, stability_factor=.05,
                        consumer_goods_expected_value=.025, global_building_slots_factor=.10,
                        monthly_population=.10, production_cost_arms_factory_factor=.10,
                        military_industrial_organization_funds_gain=-.20, research_speed_factor=-.05,
                        custom_modifier_tooltip=ROUTE_BONUS_TOOLTIPS['cooperative']),
    'trusts': dict(production_speed_buildings_factor=.10, industrial_capacity_factory=.03,
                   political_power_factor=-.10, stability_factor=-.05, war_support_factor=-.05,
                   military_industrial_organization_funds_gain=.10, resource_trade_cost_bonus_per_factory=1,
                   production_cost_industrial_complex_factor=-.10, production_cost_arms_factory_factor=-.05,
                   custom_modifier_tooltip=ROUTE_BONUS_TOOLTIPS['trusts']),
}


def economy_branch(edges):
    result = {'RUS_future_domestic_424'}
    while True:
        expanded = result | {target for source, target in edges if source in result}
        if expanded == result:
            return sorted(result)
        result = expanded


def focus_reward(focus, branch):
    effects = []
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
    return effects


def route_requirement(suffix):
    route = ROUTES[suffix]
    return (f'custom_trigger_tooltip = {{ tooltip = {PREFIX}_{route}_requires_tt '
            f'check_variable = {{ {CHOICE} = {ROUTE_ORDER.index(route)+1} }} }}')


def idea_previews(tiers):
    # The engine compares the actual idea definitions, including integer trade
    # thresholds and the final route's modifiers.
    def preview(name, swaps, fallback=None, bonus_tooltip=None):
        lines = [f'{name} = {{']
        for index, (before, after) in enumerate(swaps):
            lines.extend([
                f'\t{"else_if" if index else "if"} = {{',
                f'\t\tlimit = {{ hidden_trigger = {{ has_idea = {before} }} }}',
                f'\t\teffect_tooltip = {{ swap_ideas = {{ remove_idea = {before} add_idea = {after} }} }}',
            ])
            if bonus_tooltip:
                lines.append(f'\t\tcustom_effect_tooltip = {bonus_tooltip}')
            lines.append('\t}')
        if fallback:
            lines.append(f'\telse = {{ {fallback} = yes }}')
        return [*lines, '}', '']

    lines = preview(PREVIEW, zip(tiers, tiers[1:]))
    for route in ROUTE_ORDER:
        final = f'{PREFIX}_{route}'
        lines.extend(preview(f'{PREVIEW}_{route}',
                             [(tiers[9], final), (tiers[10], final)], PREVIEW,
                             ROUTE_BONUS_TOOLTIPS.get(route)))
    return lines


def outputs(branch):
    tiers = [f'{PREFIX}_{index}' for index in range(11)]
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
    definitions.update({f'{PREFIX}_{suffix}': mod for suffix,mod in FINALS.items()})
    ideas = ['ideas = {', '\tcountry = {']
    for idea, modifiers in definitions.items():
        ideas.extend([f'\t\t{idea} = {{', '\t\t\tpicture = POL_disjointed_industry',
                      '\t\t\tallowed = { original_tag = RUS }', '\t\t\tremoval_cost = -1',
                      '\t\t\tmodifier = {'])
        ideas.extend(f'\t\t\t\t{key} = {value}' for key, value in modifiers.items())
        ideas.extend(['\t\t\t}', '\t\t}'])
    ideas.extend(['\t}', '}'])

    # Recompute from completed IDs so a replay or save reload cannot add a layer twice.
    count = PREFIX + '_count'
    have = 'OR = { ' + ' '.join(f'has_idea = {idea}' for idea in [OLD,*definitions]) + ' }'
    effect = [f'{REFRESH} = {{', '\tif = {',
              f'\t\tlimit = {{ original_tag = RUS has_socialist_government = yes {have} }}',
              f'\t\tset_temp_variable = {{ {count} = 0 }}']
    for focus in branch:
        effect.append(f'\t\tif = {{ limit = {{ has_completed_focus = {focus} }} add_to_temp_variable = {{ {count} = 1 }} }}')
    cases = [(f'check_variable = {{ {count} > 9 }} has_completed_focus = RUS_future_domestic_{focus}',
              f'{PREFIX}_{route}') for focus, route in ROUTES.items()]
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
    effect.extend(['\t}', '}', ''])
    effect.extend(idea_previews(tiers))
    effect.extend(f'''{MONTHLY_EDUCATION} = {{
\tif = {{
\t\tlimit = {{
\t\t\thas_socialist_government = yes
\t\t\thas_country_flag = RUS_education_system_active
\t\t\thas_idea = {COOPERATIVE_IDEA}
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
        Path('common/ideas/RUS_disordered_industry.txt'): '\n'.join(ideas)+'\n',
        Path('common/scripted_effects/RUS_disordered_industry.txt'): '\n'.join(effect).rstrip()+'\n',
        Path('common/on_actions/RUS_disordered_industry.txt'): actions,
    }
    for lang, label, tooltip in (
        ('simp_chinese','混乱的工业','经济项目政治点数及建设资源花费：§G−20%§!'),
        ('english','Disordered Industry','Economic Project Political Power and Construction Resource Cost: §G−20%§!'),
        ('russian','Дезорганизованная промышленность','Стоимость экономических проектов в политической власти и строительных ресурсах: §G−20%§!'),
    ):
        lines = [f'l_{lang}:', f' {PREFIX}_discount_tt:0 "{tooltip}"']
        education_text, resources_text = {
            'simp_chinese': ('每月基础教育水平和高等教育水平各 §G+{education}§!（教育系统启用后）',
                             '每日建设资源收入 §G+{resources}§!（国家建设账本开启后）'),
            'english': ('Monthly Basic and Higher Education each §G+{education}§! while education reform is active',
                        'Daily Construction Resource Income §G+{resources}§! while the construction account is open'),
            'russian': ('Начальное и высшее образование ежемесячно §G+{education}§! каждое при действующей реформе образования',
                        'Ежедневный доход строительных ресурсов §G+{resources}§! при открытом строительном счёте'),
        }[lang]
        education_text = education_text.format(education=COOPERATIVE_MONTHLY_EDUCATION)
        resources_text = resources_text.format(resources=TRUSTS_DAILY_RESOURCES)
        lines.extend([f' {ROUTE_BONUS_TOOLTIPS["cooperative"]}:0 "{education_text}"',
                      f' {ROUTE_BONUS_TOOLTIPS["trusts"]}:0 "{resources_text}"'])
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
            lines.extend([f' {idea}:0 "{label}"', f' {idea}_desc:0 "${OLD}_desc$"'])
        result[Path(f'localisation/{lang}/RUS_disordered_industry_l_{lang}.yml')] = '\n'.join(lines)+'\n'
    return {path: text.encode('utf-8-sig' if path.suffix == '.yml' else 'utf-8')
            for path, text in result.items()}
