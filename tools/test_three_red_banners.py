"""Run the shipped focus, KR China filter and gendarme refresh in fixtures."""
from copy import deepcopy
from itertools import product
import math
import operator

from hoi4_politics_blocks import R, KR, load


ID = 'RUS_future_foreign_010'
PREFIX = 'RUS_third_international_gendarme_'
SPIRIT = 'RUS_third_international_gendarme'
EASY = 'RUS_easy_mode_enabled'
FOCUS = next(n for n in load(R / 'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt')
             if n.value('id') == ID)
EFFECTS = {n.k: n for filename in ('RUS_future_foreign_policy_effects.txt',
                                  'RUS_gendarme_waiting_effects.txt',
                                  'RUS_easy_mode_other_dynamic_effects.txt')
           for n in load(R / 'common/scripted_effects' / filename)}
TRIGGERS = {n.k: n for n in load(KR / 'common/scripted_triggers/_renaming_scripted_triggers.txt')
            if n.k in {'is_chinese_tag', 'is_tag_in_china_area'}}
TRIGGERS.update({n.k: n for n in load(R / 'common/scripted_triggers/RUS_kamenev_politics_triggers.txt')
                 if n.k == 'RUS_uses_kamenev_politics'})


def country(tag, *, socialist=False, exists=True, ai=True, easy=False):
    return dict(tag=tag, socialist=socialist, exists=exists, ai=ai, flags={EASY} if easy else set(),
                vars={}, focuses=set(), dynamic=set(), tech=set(), ideas=set(), xp=0, factories=0,
                stability=.6, war_support=.6, radical_socialist=.1)


def value(text, c):
    try: return float(text)
    except ValueError: return c['vars'].get(text.removeprefix('var:'), 0)


def check(nodes, w, current='RUS'):
    c = w[current]
    def one(n):
        k, v = n.k, n.v
        if k in w: return check(v, w, k)
        if k in TRIGGERS: return check(TRIGGERS[k].v, w, current) == (v == 'yes')
        if k in {'tooltip', 'not_tooltip'}: return True
        if k in {'AND', 'hidden_trigger', 'custom_override_tooltip'}: return all(one(x) for x in v)
        if k == 'OR': return any(one(x) for x in v)
        if k == 'NOT': return not all(one(x) for x in v)
        if k == 'original_tag': return current == v
        if k == 'exists': return c['exists'] == (v == 'yes')
        if k == 'has_socialist_government': return c['socialist'] == (v == 'yes')
        if k == 'has_country_flag': return v in c['flags']
        if k == 'has_completed_focus': return v in c['focuses']
        if k == 'has_tech': return v in c['tech']
        if k == 'has_idea': return v in c['ideas']
        if k == 'has_dynamic_modifier': return n.value('modifier') in c['dynamic']
        if k == 'is_ai': return c['ai'] == (v == 'yes')
        if k == 'country_exists': return v in w and w[v]['exists']
        if k == 'check_variable':
            comparisons = {'>': operator.gt, '<': operator.lt, '=': operator.eq,
                           '>=': operator.ge, '<=': operator.le, '!=': operator.ne}
            return all(comparisons[x.op](value(x.k, c), value(x.v, c)) for x in v)
        raise AssertionError(('Unsupported trigger', k))
    return all(one(n) for n in nodes)


def run(nodes, w, current='RUS'):
    matched = False
    for n in nodes:
        k, v = n.k, n.v
        if k in {'if', 'else'}:
            if k == 'if': matched = False
            if not matched and (k == 'else' or check(n.one('limit').v, w, current)):
                run([x for x in v if x.k != 'limit'], w, current)
                matched = True
            continue
        matched = False
        c = w[current]
        if k in w:
            if w[k]['exists']: run(v, w, k)
        elif k in EFFECTS: run(EFFECTS[k].v, w, current)
        elif k == 'hidden_effect': run(v, w, current)
        elif k in {'custom_effect_tooltip', 'effect_tooltip', 'force_update_dynamic_modifier'}: pass
        elif k == 'every_other_country':
            for tag in w:
                if tag != current and w[tag]['exists'] and check(n.one('limit').v, w, tag):
                    run([x for x in v if x.k != 'limit'], w, tag)
        elif k in {'set_variable', 'set_temp_variable', 'add_to_variable', 'add_to_temp_variable',
                   'multiply_variable', 'multiply_temp_variable'}:
            for x in v:
                if x.k == 'tooltip': continue
                amount = value(x.v, c)
                if k.startswith('set_'): c['vars'][x.k] = amount
                elif k.startswith('add_'): c['vars'][x.k] = value(x.k, c) + amount
                else: c['vars'][x.k] = value(x.k, c) * amount
        elif k == 'add_dynamic_modifier': c['dynamic'].add(n.value('modifier'))
        elif k == 'remove_dynamic_modifier': c['dynamic'].discard(n.value('modifier'))
        elif k == 'set_technology': c['tech'].update(x.k for x in v if x.k != 'popup')
        elif k == 'army_experience': c['xp'] += int(v)
        elif k == 'add_offsite_building':
            assert n.value('type') == 'arms_factory'
            c['factories'] += int(n.value('level'))
        elif k == 'add_popularity':
            assert n.value('ideology') == 'radical_socialist'
            c['radical_socialist'] += float(n.value('popularity'))
        elif k == 'add_stability': c['stability'] += float(v)
        elif k == 'add_war_support': c['war_support'] += float(v)
        else: raise AssertionError(('Unsupported effect', k))


def modifiers(c):
    limit, xp = (c['vars'].get(PREFIX + k, 0) for k in ('volunteer_limit', 'volunteer_experience'))
    if SPIRIT + '_easy_bonus' in c['dynamic']:
        limit += c['vars']['RUS_easy_dyn_' + SPIRIT + '_send_volunteer_size']
        xp += c['vars']['RUS_easy_dyn_' + SPIRIT + '_army_experience_from_volunteers']
    return limit, xp


def awards(w):
    return {tag: (c['xp'], c['factories'], c['stability'], c['war_support'], c['radical_socialist'])
            for tag, c in w.items()}


cases = 0
for victories, rus_ai, rus_easy, chinese_easy, japan_exists in product((0, 3, 20), (False, True),
                                                                    (False, True), (False, True), (False, True)):
    w = {tag: country(tag, socialist=socialist, exists=exists) for tag, socialist, exists in (
        ('RUS', True, True), ('CHI', True, True), ('SIK', True, True), ('TIB', True, True),
        ('MON', False, True), ('FNG', False, True), ('SZC', True, False), ('HND', True, True),
        ('FRA', True, True), ('SER', False, False), ('ROM', False, False), ('GRE', False, False),
        ('ALB', False, False), ('BUL', False, False), ('JAP', False, japan_exists))}
    c = w['RUS']
    c.update(ai=rus_ai, flags={EASY} if rus_easy else set())
    c['focuses'].add('RUS_future_foreign_004')
    c['vars'][PREFIX + 'victories'] = victories
    w['CHI'].update(ai=False, flags={EASY} if chinese_easy else set())
    refresh = EFFECTS['RUS_future_foreign_refresh_third_international_gendarme'].v
    easy_refresh = EFFECTS['RUS_easy_mode_refresh_other_dynamic'].v
    run(refresh, w)
    run(easy_refresh, w)
    before = modifiers(c)
    c['focuses'].add(ID)
    run(FOCUS.one('completion_reward').v, w)
    factor = 2 if rus_easy and not rus_ai else 1
    after = modifiers(c)
    assert after[0] - before[0] == factor
    assert math.isclose(after[1] - before[1], .05 * factor)
    for tag, recipient in w.items():
        expected = 2 if tag == 'CHI' and chinese_easy else 1
        if tag in {'CHI', 'SIK', 'TIB'}:
            assert (recipient['xp'], recipient['factories']) == (25 * expected, expected)
        else: assert recipient['xp'] == recipient['factories'] == 0
    assert math.isclose(w['JAP']['radical_socialist'], .15 if japan_exists else .1)
    assert math.isclose(w['JAP']['stability'], .55 if japan_exists else .6)
    assert math.isclose(w['JAP']['war_support'], .55 if japan_exists else .6)
    settled = deepcopy(awards(w))
    for _ in range(25):
        run(refresh, w)
        run(easy_refresh, w)
    assert modifiers(c) == after, 'Weekly refresh must neither erase nor stack the focus bonus'
    assert awards(w) == settled, 'China/Japan one-off rewards must not repeat during refresh'
    assert c['vars'][PREFIX + 'volunteer_limit'] == min(1 + victories, 5) + 1
    assert math.isclose(c['vars'][PREFIX + 'volunteer_experience'], min(1 + victories, 10) * .05 + .05)
    cases += 1

reward = FOCUS.one('completion_reward')
recipients = reward.one('every_other_country').one('limit')
assert recipients.value('is_tag_in_china_area') == 'yes'
assert recipients.value('has_socialist_government') == 'yes', 'Tooltip recipient list must exclude non-socialists'
assert reward.one('custom_effect_tooltip').value('localization_key') == 'tooltip_modify_dynmod'
assert reward.one('custom_effect_tooltip').value('DYNMOD') == SPIRIT
assert FOCUS.one('select_effect') is None
normal = reward.one('else').children('add_to_variable')
preview = reward.one('if').one('effect_tooltip').children('add_to_variable')
for nodes, factor in ((normal, 1), (preview, 2)):
    assert float(nodes[0].value(PREFIX + 'volunteer_limit')) == factor
    assert float(nodes[1].value(PREFIX + 'volunteer_experience')) == .05 * factor
    for language in ('simp_chinese', 'english', 'russian'):
        p = R / f'localisation/{language}/RUS_three_red_banners_l_{language}.yml'
        assert p.read_bytes().startswith(b'\xef\xbb\xbf')
        text = p.read_text(encoding='utf-8-sig')
        for n in nodes: assert text.count(' ' + n.value('tooltip') + ':') == 1
        assert '$RIGHT|' in text and '$MODIFIER_' in text

print(f'PASS: {cases} Three Red Banners scenarios; KR recipient filter, aid/Japan scope, caps, 25 refreshes and easy-mode display.')
