"""Exercise mission recipients, targeted volunteers, easy-mode changes and expiry.

The fixture runs shipped script blocks; it does not emulate HOI4 combat or UI.
"""
from copy import deepcopy
from itertools import product
import math

from hoi4_politics_blocks import R, load


OFFICERS = 'RUS_russian_officer_mission'
AID = 'RUS_aiding_chinese_comrades'
EASY = 'RUS_easy_mode_enabled'
BASE_REL = 'RUS_china_mission_volunteers'
EXTRA_REL = BASE_REL + '_easy'
BONUS = 'RUS_easy_mode_ideas_bonus'
IDEAS = {n.k: n for name in ('RUS_china_military_mission_ideas.txt', 'RUS_subcontinental_dawn_ideas.txt')
         for root in load(R / 'common/ideas' / name) for cat in root.v for n in cat.v}
EFFECTS = {n.k: n for name in ('RUS_china_military_mission_effects.txt', 'RUS_easy_mode_ideas_effects.txt')
           for n in load(R / 'common/scripted_effects' / name)}
DYNAMIC = next(n for n in load(R / 'common/dynamic_modifiers/RUS_easy_mode_ideas_bonus.txt') if n.k == BONUS)
RELATIONS = {n.k: n for n in load(R / 'common/modifiers/RUS_china_military_mission_modifiers.txt')}
FOCUS = next(n for n in load(R / 'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt')
             if n.value('id') == 'RUS_future_foreign_039')
DAILY = load(R / 'common/on_actions/RUS_china_military_mission_on_actions.txt')[0].one('on_daily').one('effect').v


def country(ai, easy):
    return dict(ai=ai, exists=True, flags={EASY} if easy else set(), ideas={}, variables={}, dynamic=set(), relations=set())


def check(nodes, world, current):
    c = world[current]
    def one(n):
        k, v = n.k, n.v
        if k in {'AND', 'hidden_trigger'}: return all(one(x) for x in v)
        if k == 'OR': return any(one(x) for x in v)
        if k == 'NOT': return not all(one(x) for x in v)
        if k == 'has_idea': return v in c['ideas']
        if k == 'has_country_flag': return v in c['flags']
        if k == 'is_ai': return c['ai'] == (v == 'yes')
        if k == 'country_exists': return world[v]['exists']
        if k == 'has_dynamic_modifier': return n.value('modifier') in c['dynamic']
        if k == 'has_relation_modifier': return (n.value('target'), n.value('modifier')) in c['relations']
        if k == 'check_variable':
            assert all(x.op == '>' for x in v)
            return all(c['variables'].get(x.k, 0) > float(x.v) for x in v)
        raise AssertionError(('Unsupported trigger', k))
    return all(one(n) for n in nodes)


def run(nodes, world, current='RUS'):
    matched = False
    for n in nodes:
        k, v = n.k, n.v
        if k in {'if', 'else'}:
            if k == 'if': matched = False
            if not matched and (k == 'else' or check(n.one('limit').v, world, current)):
                run([x for x in v if x.k != 'limit'], world, current)
                matched = True
            continue
        matched = False
        c = world[current]
        if k in world:
            if world[k]['exists']: run(v, world, k)
        elif k in EFFECTS: run(EFFECTS[k].v, world, current)
        elif k == 'hidden_effect': run(v, world, current)
        elif k in {'effect_tooltip', 'force_update_dynamic_modifier'}: pass
        elif k in {'add_ideas', 'add_timed_idea'}:
            idea = v if k == 'add_ideas' else n.value('idea')
            c['ideas'][idea] = None if k == 'add_ideas' else int(n.value('days'))
            callback = IDEAS[idea].one('on_add')
            if callback: run(callback.v, world, current)
        elif k == 'set_country_flag': c['flags'].add(v)
        elif k == 'clr_country_flag': c['flags'].discard(v)
        elif k == 'set_variable':
            for x in v: c['variables'][x.k] = float(x.v)
        elif k == 'add_to_variable':
            for x in v: c['variables'][x.k] = c['variables'].get(x.k, 0) + float(x.v)
        elif k == 'add_dynamic_modifier': c['dynamic'].add(n.value('modifier'))
        elif k == 'remove_dynamic_modifier': c['dynamic'].discard(n.value('modifier'))
        elif k == 'add_relation_modifier': c['relations'].add((n.value('target'), n.value('modifier')))
        elif k == 'remove_relation_modifier': c['relations'].discard((n.value('target'), n.value('modifier')))
        else: raise AssertionError(('Unsupported effect', k))


def total(c, key):
    result = sum(float(IDEAS[name].one('modifier').value(key, 0)) for name in c['ideas'])
    if BONUS in c['dynamic']: result += c['variables'].get(DYNAMIC.value(key), 0)
    return result


def cap(c, target):
    return sum(float(RELATIONS[name].value('send_volunteer_size')) for tag, name in c['relations'] if tag == target and name in RELATIONS)


def refresh(world):
    for tag, c in world.items():
        if EASY in c['flags'] and not c['ai']:
            run(EFFECTS['RUS_easy_mode_refresh_ideas'].v, world, tag)
            run(EFFECTS['RUS_china_mission_refresh_volunteers'].v, world, tag)
        run(DAILY, world, tag)


def assert_active(world):
    rus, chi = world['RUS'], world['CHI']
    rf = 2 if EASY in rus['flags'] and not rus['ai'] else 1
    cf = 2 if EASY in chi['flags'] and not chi['ai'] else 1
    for key, amount in {'experience_gain_army_factor': .10, 'army_strength_factor': .05,
                        'army_infantry_attack_factor': .05, 'mass_assault_mastery_gain_factor': .05}.items():
        assert math.isclose(total(chi, key), amount * cf), (key, chi)
    assert math.isclose(total(rus, 'experience_gain_army'), -.05), 'Easy mode must not double the daily expense'
    assert math.isclose(total(rus, 'experience_gain_factor'), .05 * rf)
    assert cap(rus, 'CHI') == rf and cap(rus, 'FNG') == cap(chi, 'RUS') == 0


cases = 0
for rus_ai, rus_easy, chi_ai, chi_easy, remove_before_callback in product((False, True), repeat=5):
    w = {'RUS': country(rus_ai, rus_easy), 'CHI': country(chi_ai, chi_easy), 'FNG': country(True, False)}
    rus, chi = w['RUS'], w['CHI']
    rus['ideas']['RUS_subcontinental_military_aid'] = None  # An unrelated bonus must survive expiry.
    rus['relations'].add(('CHI', 'volunteer_limit_plus_one'))  # A pre-existing KR agreement must survive.
    assert check(FOCUS.one('available').v, w, 'RUS')
    run(FOCUS.one('completion_reward').v, w)
    assert OFFICERS in chi['ideas'] and chi['ideas'][OFFICERS] is None
    assert rus['ideas'][AID] == 360 and OFFICERS not in rus['ideas'] and AID not in chi['ideas']
    assert not w['FNG']['ideas'] and not w['FNG']['relations']
    assert_active(w)
    snapshot = deepcopy((rus['relations'], rus['ideas'], chi['ideas']))
    for _ in range(25): refresh(w)
    assert (rus['relations'], rus['ideas'], chi['ideas']) == snapshot, 'Refresh must not stack slots or renew duration'
    assert_active(w)
    for c in (rus, chi): c['flags'].add(EASY)
    refresh(w)  # Activating easy mode after completing the focus.
    assert_active(w)
    rus['ai'] = chi['ai'] = True
    refresh(w)
    assert_active(w)  # Losing player control removes the additional benefits.
    rus['ai'] = chi['ai'] = False
    refresh(w)
    rus['ideas'][AID] = 1  # Last day: costs and benefits still apply.
    assert_active(w)
    if remove_before_callback: del rus['ideas'][AID]
    run(IDEAS[AID].one('on_remove').v, w)
    rus['ideas'].pop(AID, None)
    assert cap(rus, 'CHI') == 0
    assert ('CHI', 'volunteer_limit_plus_one') in rus['relations']
    assert total(rus, 'experience_gain_army') == total(rus, 'experience_gain_factor') == 0
    assert math.isclose(total(rus, 'army_org_factor'), .10), 'Preserve unrelated easy-mode benefits'
    assert 'RUS_china_mission_removing' not in rus['flags']
    assert math.isclose(total(chi, 'mass_assault_mastery_gain_factor'), .10), 'Officer mission remains after 360 days'
    refresh(w)
    assert cap(rus, 'CHI') == 0, 'Daily refresh must not recreate expired aid'
    w['CHI']['exists'] = False
    assert not check(FOCUS.one('available').v, w, 'RUS')
    cases += 1

assert FOCUS.one('select_effect') is None
assert FOCUS.one('prerequisite').value('focus') == 'RUS_future_foreign_025'
assert 'RUS_china_mission_refresh_volunteers = yes' in (R / 'common/scripted_effects/RUS_easy_mode_effects.txt').read_text()
assert all(IDEAS[name].one('modifier').one('send_volunteer_size') is None for name in (AID, OFFICERS))
for language in ('simp_chinese', 'english', 'russian'):
    p = R / f'localisation/{language}/RUS_china_military_mission_l_{language}.yml'
    assert p.read_bytes().startswith(b'\xef\xbb\xbf')
    text = p.read_text(encoding='utf-8-sig')
    assert '[GetRUSChinaMissionVolunteerBonus]' in text
    for key in (OFFICERS, AID, BASE_REL, EXTRA_REL): assert text.count(' ' + key + ':') == 1
print(f'PASS: {cases} military mission lifecycles; native rewards, CHI-only slots, easy-mode activation/AI switch and both expiry callback orders.')
