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
    'federal': PREFIX + '_discount_tt',
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
                    custom_modifier_tooltip=ROUTE_BONUS_TOOLTIPS['federal']),
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

# Modifier labels and sprites are supplied by vanilla and KR. The three
# building-cost labels are supplied by this mod.
PREVIEW_ROWS = {
    'monthly_population': ('MODIFIER_GLOBAL_MONTHLY_POPULATION', 'population_texticon'),
    'political_power_factor': ('MODIFIER_POLITICAL_POWER_FACTOR', 'pol_power'),
    'consumer_goods_factor': ('MODIFIER_CONSUMER_GOODS_FACTOR', 'consumer_goods_texticon'),
    'consumer_goods_expected_value': ('MODIFIER_CONSUMER_GOODS_EXPECTED_VALUE', 'consumer_goods_texticon'),
    'stability_factor': ('MODIFIER_STABILITY_FACTOR', 'stability_texticon'),
    'war_support_factor': ('MODIFIER_WAR_SUPPORT_FACTOR', 'war_support_texticon'),
    'conversion_cost_civ_to_mil_factor': ('MODIFIER_CONVERSION_COST_CIV_TO_MIL_FACTOR', 'mil_factory'),
    'global_building_slots': ('MODIFIER_GLOBAL_BUILDING_SLOTS', 'state'),
    'global_building_slots_factor': ('MODIFIER_GLOBAL_BUILDING_SLOTS_FACTOR', 'state'),
    'production_speed_buildings_factor': ('MODIFIER_PRODUCTION_SPEED_BUILDINGS_FACTOR', 'build_cost_ic_texticon'),
    'production_factory_efficiency_gain_factor': ('MODIFIER_PRODUCTION_FACTORY_EFFICIENCY_GAIN_FACTOR', ''),
    'research_speed_factor': ('MODIFIER_RESEARCH_SPEED_FACTOR', 'research_speed_icon'),
    'industrial_capacity_factory': ('MODIFIER_INDUSTRIAL_CAPACITY_FACTOR', 'mil_factory'),
    'resource_trade_cost_bonus_per_factory': ('MODIFIER_RESOURCE_TRADE_COST_BONUS_PER_FACTORY', 'resources_to_market_icon'),
    'military_industrial_organization_funds_gain': ('MODIFIER_MIO_FUNDS_GAIN', 'RUS_np_resources_texticon'),
    'production_cost_infrastructure_factor': ('modifier_production_cost_infrastructure_factor', ''),
    'production_cost_arms_factory_factor': ('modifier_production_cost_arms_factory_factor', ''),
    'production_cost_industrial_complex_factor': ('modifier_production_cost_industrial_complex_factor', ''),
    'production_speed_rail_way_factor': ('modifier_production_speed_rail_way_factor', 'railways_texticon'),
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
    for modifier, (label, icon) in PREVIEW_ROWS.items():
        delta = Decimal(str(after.get(modifier, 0))) - Decimal(str(before.get(modifier, 0)))
        if not delta:
            continue
        color = 'Y' if modifier in NEUTRAL_ROWS else (
            'G' if (delta < 0 if modifier in COST_ROWS else delta > 0) else 'R')
        amount = f'{int(delta):+d}' if modifier in INTEGER_ROWS else f'{delta*100:+.2f}%'
        icon_text = f'£{icon}£ ' if icon else ''
        rows.append(f'{icon_text}${label}$: §{color}{amount}§!')
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

    lines = preview(PREVIEW, zip(tiers, tiers[1:]))
    for route in ROUTE_ORDER:
        final = f'{PREFIX}_{route}'
        lines.extend(preview(f'{PREVIEW}_{route}',
                             [(tiers[9], final), (tiers[10], final)], PREVIEW,
                             route))
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
        education_text = (f'£RUS_edu_basic_texticon£ {basic_text}: {gain}\\n'
                          f'£RUS_edu_higher_texticon£ {higher_text}: {gain}\\n'
                          f'§g{education_condition}§!')
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
            lines.extend([f' {idea}:0 "{label}"', f' {idea}_desc:0 "${OLD}_desc$"'])
        result[Path(f'localisation/{lang}/RUS_disordered_industry_l_{lang}.yml')] = '\n'.join(lines)+'\n'
    return {path: text.encode('utf-8-sig' if path.suffix == '.yml' else 'utf-8')
            for path, text in result.items()}
