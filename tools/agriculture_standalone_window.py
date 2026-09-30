"""Attach the agricultural cards and existing decision actions to a player window.

Called by build_agriculture_card_gui; this module never writes files. Decision
definitions remain the canonical action data, but their category is hidden.
Costs and execution guards are added here because GUI clicks bypass decisions.
"""
from pathlib import Path
import re

from hoi4_politics_blocks import parse

GUI = 'interface/RUS_national_agriculture.gui'
SCRIPT = 'common/scripted_guis/RUS_national_agriculture.txt'
CATEGORY = 'common/decisions/categories/RUS_agricultural_quarterly_management_categories.txt'
ACTIVE = 'RUS_nat_window_available = yes'
OPEN = 'has_country_flag = RUS_nat_window_open'
LANGS = ['simp_chinese', 'english', 'russian']


def inner(node, key):
    child = node.one(key)
    return child.inner().strip() if child else ''


def insert_into_block(source, key, content):
    match = re.search(r'\b' + re.escape(key) + r'\s*=\s*\{', source)
    assert match, key
    return source[:match.end()] + '\n' + content + '\n' + source[match.end():]


def render_window(outputs, base, root: Path):
    """Keep all card coordinates/actions; add a window shell and administration."""
    result = dict(outputs)
    local = {}

    def loc(name, values):
        key = 'RUS_agri_window_' + name
        local[key] = values if isinstance(values, list) else [values] * 3
        return key

    loc('open', ['国家农业系统', 'National agricultural system', 'Система сельского хозяйства'])
    loc('open_desc', ['点击打开农业生产、农机生产、贸易与农业建设界面。',
        'Click to open agricultural production, machinery production, trade and development.',
        'Нажмите, чтобы открыть производство сельхозпродукции и техники, торговлю и развитие.'])
    loc('open_tt', [f'§Y{title}§!\\n{desc}' for title, desc in zip(
        local['RUS_agri_window_open'], local['RUS_agri_window_open_desc'])])
    loc('support', ['季度援助', 'Quarterly support', 'Поддержка'])
    loc('development', ['农业建设', 'Development', 'Развитие'])
    loc('support_status', ['本季已用支援：§Y[?RUS_nat_support_count|0] / 4§!',
        'Support used this quarter: §Y[?RUS_nat_support_count|0] / 4§!',
        'Поддержка за квартал: §Y[?RUS_nat_support_count|0] / 4§!'])
    loc('development_status', ['可用土改分数：§Y[?RUS_agri_spendable_score|0]§!\\n国内限时项目：§Y[?RUS_agri_domestic_active_count|0] / 2§!',
        'Available reform score: §Y[?RUS_agri_spendable_score|0]§!\\nActive domestic projects: §Y[?RUS_agri_domestic_active_count|0] / 2§!',
        'Очки реформы: §Y[?RUS_agri_spendable_score|0]§!\\nВременные проекты: §Y[?RUS_agri_domestic_active_count|0] / 2§!'])
    loc('development_locked', ['成功完成土地改革后，可在此开展农业建设。',
        'Agricultural development becomes available after land reform succeeds.',
        'Развитие сельского хозяйства доступно после успешной земельной реформы.'])
    loc('guide_label', ['经营指南', 'Management guide', 'Руководство'])
    loc('shutdown_label', ['关闭国家农业系统', 'End agricultural management', 'Завершить управление'])
    loc('shutdown_desc', ['土地改革的目标已超额完成，可将日常生产交由常设机构负责。此决定不可撤销。',
        'Land reform has exceeded its goals. Permanent institutions can take over everyday production. This decision is irreversible.',
        'Цели земельной реформы перевыполнены. Повседневное производство можно передать постоянным органам. Решение необратимо.'])
    shutdown_tip = loc('shutdown_effect', [
        '永久停止国家农业系统的每日运行、季度结算与提醒，并关闭经营面板；释放系统占用的民用工厂，移除季度经营产生的年度临时修正。已取得的土地改革阶段成果和其他独立奖励保留。',
        'Permanently ends daily agricultural management, quarterly settlement and reminders, and closes this window. Releases assigned civilian factories and removes annual temporary agricultural modifiers. Land reform milestones and other independent rewards are retained.',
        'Навсегда прекращает ежедневное управление, квартальные расчёты и напоминания, закрывает окно. Освобождает выделенные фабрики и снимает временные годовые аграрные модификаторы. Этапы земельной реформы и независимые награды сохраняются.'
    ])

    # The native-size card content is nested under the same scripted-GUI root.
    original = parse(result[GUI])[0]
    content = original.v[0]
    widgets = '\n'.join(n.raw() for n in content.v if n.k not in {'name', 'position', 'size', 'clipping'})
    entries = '\n'.join(n.raw() for n in original.v[1:])
    shell = ['''guiTypes = {
	containerWindowType = {
		name = "RUS_national_agriculture_window"
		position = { x = -470 y = -346 }
		size = { width = 940 height = 692 }
		orientation = center
		moveable = yes
		click_to_front = yes
		show_sound = menu_open_window
		hide_sound = menu_close_window
		background = { name = "agriculture_frame" quadTextureSprite = "GFX_tiled_plain_bg" }
		instantTextBoxType = { name = "agriculture_title" position = { x = 20 y = 8 } text = "RUS_nat_title" font = "hoi_24header" maxWidth = 850 maxHeight = 30 format = center alwaystransparent = yes }
		buttonType = { name = "nat_window_close" position = { x = 896 y = 7 } spriteType = "GFX_closebutton" pdx_tooltip = "CLOSE" shortcut = "ESCAPE" clicksound = click_close }
		containerWindowType = {
			name = "RUS_national_agriculture_content"
			position = { x = 16 y = 48 }
			size = { width = 502 height = 625 }
			clipping = yes
''', widgets, '\n}\n', '''
		containerWindowType = {
			name = "nat_administration_background"
			position = { x = 532 y = 48 }
			size = { width = 392 height = 625 }
			background = { name = "Background" quadTextureSprite = "GFX_tiled_research_bg" }
		}
''']
    triggers = []
    actions = ['nat_window_close_click = { hidden_effect = { RUS_nat_window_close_effect = yes } }']

    def button(name, x, y, label, tooltip='', sprite='GFX_button_359x34'):
        shell.append(f'buttonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} quadTextureSprite = "{sprite}" buttonText = "{label}" buttonFont = "hoi_16mbs" pdx_tooltip = "{tooltip}" clicksound = click_default }}')

    def text(name, label, x, y, width=359, height=44):
        shell.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} text = "{label}" font = "hoi_16mbs" maxWidth = {width} maxHeight = {height} format = center fixedsize = yes alwaystransparent = yes }}')

    for page, label in enumerate(['support', 'development']):
        button('nat_admin_tab_' + str(page), 574 + 170 * page, 68, 'RUS_agri_window_' + label,
               'RUS_agri_window_' + label, 'GFX_button_123x34')
        actions.append(f'nat_admin_tab_{page}_click = {{ hidden_effect = {{ if = {{ limit = {{ {ACTIVE} {OPEN} }} set_variable = {{ RUS_nat_admin_page = {page} }} RUS_agri_refresh_gui = yes }} }} }}')
        text('nat_admin_status_' + str(page), 'RUS_agri_window_' + label + '_status', 548, 121)
        triggers.append(f'nat_admin_status_{page}_visible = {{ check_variable = {{ RUS_nat_admin_page {"< 1" if page == 0 else "= 1"} }} }}')
    text('nat_admin_locked', 'RUS_agri_window_development_locked', 562, 240, 331, 92)
    triggers.append('nat_admin_locked_visible = { check_variable = { RUS_nat_admin_page = 1 } NOT = { RUS_agri_exchange_unlocked = yes } }')

    specs = []
    for source in ['common/decisions/RUS_national_agriculture_decisions.txt',
                   'common/decisions/RUS_agri_development_decisions.txt',
                   'common/decisions/RUS_national_agriculture_shutdown_decision.txt']:
        source_text = base.get(source, (root / source).read_text(encoding='utf-8-sig'))
        specs.extend(parse(source_text)[0].v)
    assert len(specs) == 15, 'Review the window when agricultural decisions are added or removed.'

    # Read translated source text directly so GUI tooltips need no nested $...$ expansion.
    translations = []
    for lang in LANGS:
        catalog = {}
        for p in sorted((root / 'localisation' / lang).glob('*.yml')):
            text_source = base.get(p.relative_to(root).as_posix(), p.read_text(encoding='utf-8-sig'))
            catalog.update(re.findall(r'^\s*([\w.]+):(?:\d+)?\s*"(.*)"$', text_source, re.M))
        translations.append(catalog)

    support_row = development_row = 0
    for spec in specs:
        key = spec.k
        name = 'nat_action_' + key
        visible = inner(spec, 'visible')
        available = inner(spec, 'available')
        custom_cost = inner(spec, 'custom_cost_trigger')
        cost = int(spec.value('cost', '0'))
        assert cost >= 0 and not spec.one('days_remove') and not spec.one('days_re_enable'), key
        cost_guard = f'NOT = {{ check_variable = {{ political_power < {cost} }} }}' if cost else ''
        eligibility = f'hidden_trigger = {{ {ACTIVE} {OPEN} {visible} }}\n{available}\n{custom_cost}\n{cost_guard}'
        body = inner(spec, 'complete_effect')
        assert body, key
        if key == 'RUS_nat_close_system':
            body = body.replace('RUS_nat_close_system_tt', shutdown_tip)
        payment = f'add_political_power = -{cost}\n' if cost else ''
        # The original completion effect remains the sole reward definition.
        # Tooltip and hidden execution each consume this same source block.
        execution = payment + body
        ending = 'RUS_nat_window_close_effect = yes' if key == 'RUS_nat_close_system' else 'RUS_agri_refresh_gui = yes'
        actions.append(f'{name}_click = {{\n effect_tooltip = {{ {execution} }}\n hidden_effect = {{ if = {{ limit = {{ {eligibility} }} {execution}\n {ending} }} }}\n}}')
        triggers.append(f'{name}_click_enabled = {{ {eligibility} }}')
        if key.startswith('RUS_nat_support_'):
            y = 174 + support_row * 50
            support_row += 1
            display = 'check_variable = { RUS_nat_admin_page < 1 }'
        elif key.startswith('RUS_agri_exchange_'):
            y = 174 + development_row * 50
            development_row += 1
            display = 'check_variable = { RUS_nat_admin_page = 1 }'
        else:
            y = 623 if key == 'RUS_nat_guide_decision' else 581
            display = ''
        triggers.append(f'{name}_visible = {{ {visible} {display} }}')
        labels, tips = [], []
        for i, catalog in enumerate(translations):
            label_key = 'RUS_agri_window_' + ('shutdown_label' if key == 'RUS_nat_close_system' else 'guide_label')
            label = local[label_key][i] if key in {'RUS_nat_close_system', 'RUS_nat_guide_decision'} else catalog[key]
            desc = local['RUS_agri_window_shutdown_desc'][i] if key == 'RUS_nat_close_system' else catalog.get(key + '_desc', '')
            costs = catalog.get(spec.value('custom_cost_text'), '')
            labels.append(label)
            tips.append(f'§Y{label}§!\\n{desc}\\n\\n' + (costs + '\\n' if costs else '') + f'[!{name}_click_enabled]\\n[!{name}_click]')
        button(name, 548, y, loc(key + '_label', labels), loc(key + '_tt', tips))
    shell.extend(['}\n', entries, '\n}\n'])
    result[GUI] = '\n'.join(shell)

    script = result[SCRIPT].replace('context_type = decision_category', 'context_type = player_context', 1)
    script, count = re.subn(r'visible = \{ has_country_flag = RUS_nat_enabled \}',
                           f'visible = {{ {ACTIVE} {OPEN} }}', script, count=1)
    assert count == 1
    script = insert_into_block(script, 'triggers', '\n'.join(triggers))
    result[SCRIPT] = insert_into_block(script, 'effects', '\n'.join(actions))

    result['common/scripted_triggers/RUS_national_agriculture_window_triggers.txt'] = '''# Player-window eligibility; no production or quarterly state is changed here.
RUS_nat_window_available = {
	original_tag = RUS
	is_ai = no
	has_country_flag = RUS_agri_management_unlocked
	has_country_flag = RUS_nat_enabled
	NOT = { has_country_flag = RUS_nat_system_closed }
}
'''
    result['common/scripted_effects/RUS_national_agriculture_window_effects.txt'] = '''# Opening and closing only affect UI state. Plans, orders and timers are preserved.
RUS_nat_window_open_effect = {
	if = {
		limit = { RUS_nat_window_available = yes }
		set_country_flag = RUS_nat_window_open
		RUS_nat_refresh = yes
		RUS_agri_refresh_gui = yes
	}
}
RUS_nat_window_close_effect = {
	clr_country_flag = RUS_nat_window_open
	RUS_agri_refresh_gui = yes
}
'''
    # The raid-filter header starts at y=-38. Align to its right-hand column
    # and leave 6px above it, or above KR's 77px Mitteleuropa shortcut at -115.
    # Mutually exclusive roots avoid cached layout variables and out-of-bounds
    # child hitboxes. Both buttons call the same existing open/close effects.
    launcher_script = '''	RUS_national_agriculture_launcher@SUFFIX@ = {
		context_type = player_context
		parent_window_name = raid_filter
		window_name = "RUS_national_agriculture_launcher_window@SUFFIX@"
		ai_enabled = { always = no }
		visible = {
			RUS_nat_window_available = yes
			@MIT_VISIBILITY@
		}
		effects = {
			nat_window_open_click = {
				hidden_effect = {
					if = {
						limit = { has_country_flag = RUS_nat_window_open }
						RUS_nat_window_close_effect = yes
					}
					else = { RUS_nat_window_open_effect = yes }
				}
			}
		}
	}
'''
    launcher_gui = '''	containerWindowType = {
		name = "RUS_national_agriculture_launcher_window@SUFFIX@"
		position = { x = 0 y = @Y@ }
		size = { width = 77 height = 77 }
		background = { name = "Background" quadTextureSprite = "GFX_equipment_role_selector_tiled_window" }
		background = { name = "Background" quadTextureSprite = "GFX_tiled_research_bg" }
		buttonType = { name = "nat_window_open" position = { x = 9 y = 7 } scale = 1.8 quadTextureSprite = "GFX_decision_generic_agriculture" clicksound = click_ok oversound = ui_menu_over pdx_tooltip = "RUS_agri_window_open_tt" }
	}
'''
    launcher_scripts, launcher_guis = [], []
    for suffix, y, condition in [
        ('', -121, 'NOT = { GER_is_in_mitteleuropa = yes }'),
        ('_above_mitteleuropa', -198, 'GER_is_in_mitteleuropa = yes'),
    ]:
        launcher_scripts.append(launcher_script.replace('@SUFFIX@', suffix).replace('@MIT_VISIBILITY@', condition))
        launcher_guis.append(launcher_gui.replace('@SUFFIX@', suffix).replace('@Y@', str(y)))
    # No dirty cache: membership may change independently of agricultural UI state.
    result['common/scripted_guis/RUS_national_agriculture_launcher.txt'] = (
        '# Right-aligned map shortcut; use the upper slot only while KR displays Mitteleuropa.\n'
        'scripted_gui = {\n' + ''.join(launcher_scripts) + '}\n'
    )
    result['interface/RUS_national_agriculture_launcher.gui'] = 'guiTypes = {\n' + ''.join(launcher_guis) + '}\n'
    # Keep source decision IDs for maintenance; the full player workflow lives in the window.
    category = (root / CATEGORY).read_text(encoding='utf-8-sig')
    node = next(n for n in parse(category) if n.k == 'RUS_agricultural_quarterly_management_category')
    fields = [n.raw() for n in node.v if n.k not in {'visible', 'scripted_gui', 'visible_when_empty'}]
    replacement = node.k + ' = {\n\t# Operations are exposed through the independent agriculture window.\n\t' + '\n\t'.join(fields) + '\n\tvisible = { always = no }\n}'
    result[CATEGORY] = category[:node.a] + replacement + category[node.b:]
    for i, lang in enumerate(LANGS):
        result[f'localisation/{lang}/RUS_agriculture_window_l_{lang}.yml'] = '\ufeff' + f'l_{lang}:\n' + ''.join(f' {key}:0 "{values[i]}"\n' for key, values in local.items())
    return result
