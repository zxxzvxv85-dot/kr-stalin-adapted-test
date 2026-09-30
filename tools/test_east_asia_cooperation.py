"""Execute East Asia focus/expiry/monthly scripts in a bounded stateful fixture.

This checks script branches and accounting, not HOI4's combat or UI engine.
Unknown commands fail rather than silently passing an incomplete interpreter.
"""
from copy import deepcopy
from itertools import product
from pathlib import Path
from random import Random
import json
import math

from hoi4_politics_blocks import R, KR, load


EASY = 'RUS_easy_mode_enabled'
BONUS = 'RUS_easy_mode_ideas_bonus'
NETWORK = 'RUS_northeast_anti_japanese_network'
RESISTANCE = 'RUS_active_northeast_resistance'
ANTI_WAR = 'RUS_japanese_antiwar_movement'
ECONOMY = 'RUS_transcontinental_economic_cooperation'
EXCHANGE = 'RUS_workers_peasants_military_exchange'
SPONSOR = 'RUS_project_156_sponsor'
RECIPIENT = 'RUS_project_156_recipient'
TREATY = 'RUS_sino_soviet_friendship_treaty'
EQUIPMENT = 'RUS_sino_soviet_treaty_easy_equipment'
REL = 'RUS_northeast_network_combat'

IDEAS = {n.k: n for root in load(R / 'common/ideas/RUS_east_asia_cooperation_ideas.txt')
         for cat in root.v for n in cat.v}
EFFECTS = {n.k: n for file in ('RUS_east_asia_cooperation_effects.txt', 'RUS_easy_mode_ideas_effects.txt')
           for n in load(R / 'common/scripted_effects' / file)}
INVITE = next(n for n in load(KR / 'common/scripted_effects/00_useful_scripted_effects.txt')
              if n.k == 'invite_country_to_faction')
EFFECTS[INVITE.k] = INVITE
TRIGGERS = {n.k: n for n in load(R / 'common/scripted_triggers/RUS_east_asia_cooperation_triggers.txt')}
RELATIONS = {n.k: n for n in load(R / 'common/modifiers/RUS_east_asia_cooperation_modifiers.txt')}
OPINIONS = {n.k: n for root in load(R / 'common/opinion_modifiers/RUS_east_asia_cooperation_opinions.txt') for n in root.v}
FOCUSES = {n.value('id')[-3:]: n for n in load(R / 'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt')
           if n.value('id').startswith('RUS_future_foreign_')}
HOOKS = load(R / 'common/on_actions/RUS_east_asia_cooperation_on_actions.txt')[0]
DYNAMIC = next(n for n in load(R / 'common/dynamic_modifiers/RUS_easy_mode_ideas_bonus.txt') if n.k == BONUS)


def country(ai=True, easy=False, socialist=True, faction=None):
    return dict(ai=ai, flags={EASY} if easy else set(), socialist=socialist, exists=True,
                faction=faction, wars=set(), ideas={}, relations=set(), variables={}, dynamic=set(),
                pp=0, xp=0, cic=0, factories={'industrial_complex': 0, 'arms_factory': 0},
                research=[], opinions={}, pacts=set())


def world(rus_ai=False, rus_easy=False, chi_ai=True, chi_easy=False, *, allied=False, seed=1):
    return dict(countries={
        'RUS': country(rus_ai, rus_easy, faction='rus'),
        'CHI': country(chi_ai, chi_easy, faction='rus' if allied else 'china'),
        'JAP': country(socialist=False, faction='japan'),
        'FNG': country(socialist=False),
        'OTHER': country(),
    }, states={}, events=[], declarations=[], japan_broke=False, rng=Random(seed), remove_before=False)


def scope_tag(value, current, root, prev):
    return {'ROOT': root, 'PREV': prev, 'THIS': current}.get(value, value)


def condition(nodes, w, current, root='RUS', prev=None):
    countries = w['countries']
    c = countries.get(current)
    def one(n):
        k, v = n.k, n.v
        if k in {'AND', 'hidden_trigger'}: return all(one(x) for x in v)
        if k == 'OR': return any(one(x) for x in v)
        if k == 'NOT': return not all(one(x) for x in v)
        if k in TRIGGERS:
            result = condition(TRIGGERS[k].v, w, current, root, prev)
            return result == (v == 'yes')
        if k in countries: return condition(v, w, k, root, current)
        if k == 'FNG_JAP_influence_active':
            result = (countries['FNG']['exists'] and countries['JAP']['exists'] and not w['japan_broke']
                      and 'FNG' not in countries['JAP']['wars'])
            return result == (v == 'yes')
        if k == 'country_exists': return countries[v]['exists']
        if k == 'exists': return c['exists'] == (v == 'yes')
        if k == 'has_idea': return v in c['ideas']
        if k == 'has_country_flag': return v in c['flags']
        if k == 'is_ai': return c['ai'] == (v == 'yes')
        if k == 'has_socialist_government': return c['socialist'] == (v == 'yes')
        if k == 'has_war_with': return scope_tag(v, current, root, prev) in c['wars']
        if k == 'is_in_faction': return bool(c['faction']) == (v == 'yes')
        if k == 'is_in_faction_with':
            target = countries[scope_tag(v, current, root, prev)]
            return bool(c['faction']) and c['faction'] == target['faction']
        if k == 'can_declare_war_on':
            target = countries[v]
            return target['exists'] and v not in c['wars'] and v not in c['pacts'] and c['faction'] != target['faction']
        if k == 'has_dynamic_modifier': return n.value('modifier') in c['dynamic']
        if k == 'has_relation_modifier': return (n.value('target'), n.value('modifier')) in c['relations']
        if k == 'check_variable':
            assert all(x.op == '>' for x in v)
            return all(c['variables'].get(x.k, 0) > float(x.v) for x in v)
        if k == 'is_core_of': return scope_tag(v, current, root, prev) in w['states'][current]['cores']
        if k == 'free_building_slots':
            assert n.value('building') == 'infrastructure' and n.one('size').op == '>'
            return 5 - w['states'][current]['level'] > int(n.value('size'))
        raise AssertionError(('Unsupported trigger', k))
    return all(one(n) for n in nodes)


def execute(nodes, w, current='RUS', root='RUS', prev=None):
    matched = False
    for n in nodes:
        k, v = n.k, n.v
        if k in {'if', 'else_if', 'else'}:
            if k == 'if': matched = False
            if not matched and (k == 'else' or condition(n.one('limit').v, w, current, root, prev)):
                execute([x for x in v if x.k != 'limit'], w, current, root, prev)
                matched = True
            continue
        matched = False
        c = w['countries'].get(current)
        if k in {'ROOT', 'PREV', 'THIS'} or k in w['countries']:
            target = scope_tag(k, current, root, prev)
            if w['countries'][target]['exists']: execute(v, w, target, root, current)
        elif k in EFFECTS: execute(EFFECTS[k].v, w, current, root, prev)
        elif k == 'hidden_effect': execute(v, w, current, root, prev)
        elif k in {'effect_tooltip', 'custom_effect_tooltip', 'force_update_dynamic_modifier'}: pass
        elif k in {'add_ideas', 'add_timed_idea'}:
            idea = v if k == 'add_ideas' else n.value('idea')
            assert idea in IDEAS
            c['ideas'][idea] = None if k == 'add_ideas' else int(n.value('days'))
            callback = IDEAS[idea].one('on_add')
            if callback: execute(callback.v, w, current, root, prev)
        elif k == 'remove_ideas': expire(w, current, v)
        elif k == 'set_country_flag': c['flags'].add(v)
        elif k == 'clr_country_flag': c['flags'].discard(v)
        elif k in {'set_variable', 'add_to_variable'}:
            for x in v:
                c['variables'][x.k] = (0 if k == 'set_variable' else c['variables'].get(x.k, 0)) + float(x.v)
        elif k == 'add_dynamic_modifier': c['dynamic'].add(n.value('modifier'))
        elif k == 'remove_dynamic_modifier': c['dynamic'].discard(n.value('modifier'))
        elif k == 'add_relation_modifier': c['relations'].add((n.value('target'), n.value('modifier')))
        elif k == 'remove_relation_modifier': c['relations'].discard((n.value('target'), n.value('modifier')))
        elif k == 'add_political_power': c['pp'] += float(v)
        elif k == 'army_experience': c['xp'] += float(v)
        elif k == 'add_cic': c['cic'] += float(v)
        elif k == 'add_offsite_building': c['factories'][n.value('type')] += int(n.value('level'))
        elif k == 'add_tech_bonus': c['research'].append((n.value('category'), float(n.value('bonus')), int(n.value('uses'))))
        elif k == 'add_opinion_modifier':
            target = scope_tag(n.value('target'), current, root, prev)
            c['opinions'][target] = float(OPINIONS[n.value('modifier')].value('value'))
        elif k == 'diplomatic_relation':
            assert n.value('relation') == 'non_aggression_pact'
            target = scope_tag(n.value('country'), current, root, prev)
            c['pacts'].add(target)
            w['countries'][target]['pacts'].add(current)
        elif k == 'country_event': w['events'].append((current, n.value('id'), root))
        elif k == 'declare_war_on':
            target = n.value('target')
            w['declarations'].append((current, target, n.value('type')))
            c['wars'].add(target)
            w['countries'][target]['wars'].add(current)
        elif k == 'random_owned_controlled_state':
            eligible = [sid for sid, state in w['states'].items()
                        if state['owner'] == state['controller'] == current
                        and condition(n.one('limit').v, w, sid, root, current)]
            if eligible:
                chosen = w['rng'].choice(eligible)
                execute([x for x in v if x.k != 'limit'], w, chosen, root, current)
        elif k == 'add_building_construction':
            assert n.value('type') == 'infrastructure' and n.value('instant_build') == 'yes'
            w['states'][current]['level'] += int(n.value('level'))
            assert w['states'][current]['level'] <= 5, 'Selection consumed an award in a full state'
        else: raise AssertionError(('Unsupported effect', k))


def expire(w, tag, idea):
    c = w['countries'][tag]
    if idea not in c['ideas']: return
    if w['remove_before']: del c['ideas'][idea]
    callback = IDEAS[idea].one('on_remove')
    if callback: execute(callback.v, w, tag, tag)
    c['ideas'].pop(idea, None)


def focus(w, number):
    execute(FOCUSES[number].one('completion_reward').v, w)


def daily(w):
    for tag in w['countries']:
        execute(HOOKS.one('on_daily').one('effect').v, w, tag, tag)


def monthly(w):
    for tag in w['countries']:
        execute(HOOKS.one('on_monthly').one('effect').v, w, tag, tag)


def factor(c):
    return 2 if EASY in c['flags'] and not c['ai'] else 1


def total(c, key):
    value = sum(float(IDEAS[name].one('modifier').value(key, 0))
                for name in c['ideas'] if IDEAS[name].one('modifier'))
    if BONUS in c['dynamic']: value += c['variables'].get(DYNAMIC.value(key), 0)
    return value


def equipment(c, category, key):
    return sum(float(IDEAS[name].one('equipment_bonus').one(category).value(key, 0))
               for name in c['ideas'] if IDEAS[name].one('equipment_bonus')
               and IDEAS[name].one('equipment_bonus').one(category))


def combat(c, tag):
    return sum(float(RELATIONS[mod].value('attack_bonus_against'))
               for target, mod in c['relations'] if target == tag and mod in RELATIONS)


def state(level, owner='CHI', controller='CHI', cores=('CHI',)):
    return dict(level=level, owner=owner, controller=controller, cores=set(cores))


cases = 0
for ra, re, ca, ce in product((False, True), repeat=4):
    w = world(ra, re, ca, ce, allied=True)
    rus, chi = w['countries']['RUS'], w['countries']['CHI']
    rf, cf = factor(rus), factor(chi)
    for number in ('026', '061', '060', '054', '063', '027'):
        assert condition(FOCUSES[number].one('available').v, w, 'RUS')
        focus(w, number)
    assert rus['factories'] == dict(industrial_complex=10*rf, arms_factory=10*rf)
    assert chi['factories'] == dict(industrial_complex=10*cf, arms_factory=10*cf)
    assert w['events'] == [('RUS', 'RUS_east_asia_flavour.1', 'RUS')], 'Already-allied branch must only show the friendship flavour event, never invite'
    assert rus['xp'] == 50*rf and chi['xp'] == 75*cf
    assert rus['opinions']['CHI'] == 75*rf and chi['opinions']['RUS'] == 75*cf
    assert 'CHI' in rus['pacts'] and 'RUS' in chi['pacts']
    assert rus['research'] == [('industry', .5*rf, 1), ('infantry_weapons', .5*rf, 1), ('artillery', .5*rf, 1)]
    assert chi['research'] == [('industry', .5*cf, 1), ('infantry_weapons', .5*cf, 1), ('artillery', .5*cf, 1)]
    assert rus['ideas'][SPONSOR] == chi['ideas'][RECIPIENT] == 1800
    assert rus['ideas'][ECONOMY] == rus['ideas'][EXCHANGE] == 720 and chi['ideas'][NETWORK] == 360
    assert rus['ideas'][TREATY] is chi['ideas'][TREATY] is None
    assert total(rus, 'consumer_goods_factor') == .20, 'Sponsor cost must stay unchanged'
    assert total(rus, 'industrial_capacity_factory') == -.10
    assert total(rus, 'production_speed_arms_factory_factor') == -.10
    assert math.isclose(total(chi, 'consumer_goods_factor'), -.20*cf)
    assert math.isclose(total(chi, 'production_cost_industrial_complex_factor'), -.15*cf)
    assert math.isclose(total(chi, 'production_cost_arms_factory_factor'), -.15*cf)
    assert math.isclose(total(chi, 'production_factory_max_efficiency_factor'), .15*cf)
    for c, f in ((rus, rf), (chi, cf)):
        for key, base in {'army_core_attack_factor': .10, 'army_core_defence_factor': .10,
                          'army_attack_factor': .05, 'send_volunteer_factor': .05,
                          'war_stability_factor': .50, 'party_popularity_stability_factor': .35,
                          'communist_drift': .05, 'global_building_slots_factor': .15,
                          'air_mission_efficiency': .05, 'ace_effectiveness_factor': .15,
                          'air_cas_efficiency': .10, 'air_range_factor': .10,
                          'production_speed_dockyard_factor': .25, 'screening_efficiency': .10,
                          'navy_capital_ship_attack_factor': .10}.items():
            assert math.isclose(total(c, key), base*f), (key, total(c, key), base*f)
        assert math.isclose(equipment(c, 'mio_cat_eq_all_small_plane', 'build_cost_ic'), -.10*f)
        assert math.isclose(equipment(c, 'mio_cat_eq_all_aircraft', 'air_superiority'), .15*f)
        assert equipment(c, 'mio_cat_eq_all_aircraft', 'build_cost_ic') == 0, 'Do not discount all aircraft'
    assert math.isclose(combat(chi, 'JAP'), .05*cf) and math.isclose(combat(chi, 'FNG'), .05*cf)
    assert not w['countries']['OTHER']['ideas'] and not w['countries']['OTHER']['relations']
    before = deepcopy((rus, chi))
    for _ in range(3): daily(w)
    assert (rus, chi) == before, 'Daily refresh must not pay, stack or reset timers'
    w['states'] = {1: state(0), 2: state(0), 3: state(5), 4: state(0, controller='JAP'),
                   5: state(0, cores=()), 6: state(0, owner='JAP', controller='JAP')}
    monthly(w)
    assert rus['cic'] == 7500*rf and chi['cic'] == 0
    assert w['states'][1]['level'] + w['states'][2]['level'] == 2*cf
    assert all(w['states'][i]['level'] == 0 for i in (4, 5, 6))
    assert w['states'][3]['level'] == 5
    for tag in ('RUS', 'CHI'):
        w['countries'][tag]['flags'].add(EASY)
        w['countries'][tag]['ai'] = False
    # Exactly the same path called when easy mode is enabled after receiving rewards.
    for tag in ('RUS', 'CHI'): execute(EFFECTS['RUS_east_asia_refresh_cooperation'].v, w, tag, tag)
    assert math.isclose(total(chi, 'production_cost_industrial_complex_factor'), -.30)
    assert math.isclose(equipment(rus, 'mio_cat_eq_all_small_plane', 'build_cost_ic'), -.20)
    rus['ai'] = chi['ai'] = True
    daily(w)
    assert math.isclose(total(chi, 'consumer_goods_factor'), -.20)
    assert math.isclose(combat(chi, 'JAP'), .05)
    assert math.isclose(equipment(rus, 'mio_cat_eq_all_small_plane', 'build_cost_ic'), -.10)
    assert EQUIPMENT not in rus['ideas'] and EQUIPMENT not in chi['ideas']
    cases += 1

# Invitation branch uses the actual installed KR helper. Accepting later cannot
# turn this completed focus into the mutually exclusive factory reward branch.
for same, faction in product((False, True), (None, 'china', 'other')):
    w = world(rus_easy=True, allied=same)
    if not same: w['countries']['CHI']['faction'] = faction
    focus(w, '054')
    if same:
        assert not w['events']
        assert w['countries']['RUS']['factories']['arms_factory'] == 20
    else:
        assert w['events'] == [('CHI', 'generic_events.18', 'RUS')]
        w['countries']['CHI']['faction'] = 'rus'  # KR acceptance, not another completion.
        daily(w); monthly(w)
        assert all(sum(c['factories'].values()) == 0 for c in w['countries'].values())
    cases += 1

# Both possible engine callback orders must remove timed bonuses immediately.
for before, easy in product((False, True), repeat=2):
    w = world(rus_easy=easy, chi_ai=False, chi_easy=easy)
    w['remove_before'] = before
    for number in ('026', '061', '060', '063', '027'): focus(w, number)
    rus, chi = w['countries']['RUS'], w['countries']['CHI']
    w['states'] = {1: state(0), 2: state(0)}
    # Last active day pays, but the following month after expiry pays nothing.
    rus['ideas'][SPONSOR] = chi['ideas'][RECIPIENT] = 1
    monthly(w)
    expire(w, 'RUS', SPONSOR); expire(w, 'CHI', RECIPIENT)
    assert total(chi, 'consumer_goods_factor') == 0
    assert total(chi, 'production_cost_industrial_complex_factor') == 0
    amounts = deepcopy((rus['cic'], w['states']))
    daily(w); monthly(w)
    assert (rus['cic'], w['states']) == amounts
    expire(w, 'CHI', NETWORK)
    assert combat(chi, 'JAP') == combat(chi, 'FNG') == 0
    assert total(chi, 'supply_consumption_factor') == 0
    expire(w, 'RUS', TREATY)
    assert EQUIPMENT not in rus['ideas']
    assert total(rus, 'army_core_attack_factor') == 0
    assert math.isclose(total(rus, 'max_planning'), .1*factor(rus)), 'Unrelated spirit lost during expiry'
    expire(w, 'RUS', ECONOMY); expire(w, 'RUS', EXCHANGE)
    assert BONUS not in rus['dynamic']
    assert not any(flag.endswith('_removing') for flag in rus['flags'] | chi['flags'])
    cases += 1

# Capacity is recalculated on every draw, including repeated selections, full
# territory, just one remaining slot, and losing control of every core state.
for easy, levels in product((False, True), ((0,), (4,), (5,), (4, 4), (3, 4))):
    w = world(chi_ai=False, chi_easy=easy)
    focus(w, '063')
    w['states'] = {i: state(level) for i, level in enumerate(levels)}
    available = sum(5-level for level in levels)
    monthly(w)
    assert sum(s['level'] for s in w['states'].values()) - sum(levels) == min(4 if easy else 2, available)
    for s in w['states'].values(): s['controller'] = 'JAP'
    snapshot = deepcopy(w['states'])
    monthly(w)
    assert snapshot == w['states']
    cases += 1

# Government and diplomatic changes gate both availability and actual execution.
for change in ('missing', 'nonsocialist', 'war'):
    w = world()
    if change == 'missing': w['countries']['CHI']['exists'] = False
    elif change == 'nonsocialist': w['countries']['CHI']['socialist'] = False
    else: w['countries']['CHI']['wars'].add('RUS')
    for number in ('026', '027', '054', '060', '061', '063'):
        assert not condition(FOCUSES[number].one('available').v, w, 'RUS')
        focus(w, number)
    assert all(not c['ideas'] for tag, c in w['countries'].items() if tag != 'FNG')
    assert all(not sum(c['factories'].values()) for c in w['countries'].values())
    cases += 1

for socialist, exists, at_war in product((False, True), repeat=3):
    w = world()
    jap = w['countries']['JAP']
    jap['socialist'], jap['exists'] = socialist, exists
    if at_war: w['countries']['RUS']['wars'].add('JAP')
    eligible = exists and not socialist and not at_war
    assert bool(condition(FOCUSES['055'].one('available').v, w, 'RUS')) == eligible
    focus(w, '055')
    assert w['declarations'] == ([('RUS', 'JAP', 'annex_everything')] if eligible else [])
    cases += 1
w = world()
assert condition(FOCUSES['055'].one('available').v, w, 'RUS')
w['countries']['JAP']['socialist'] = True  # Changes while the focus is in progress.
focus(w, '055')
assert not w['declarations']
assert FOCUSES['055'].value('cancel_if_invalid') == 'yes'

for socialist, easy in product((False, True), repeat=2):
    w = world(rus_easy=easy)
    jap = w['countries']['JAP']
    jap['socialist'] = socialist
    jap['flags'].add(EASY); jap['ai'] = False
    focus(w, '011')
    if socialist:
        assert not jap['ideas'] and jap['pp'] == 100
        assert w['countries']['RUS']['pp'] == 50*(2 if easy else 1)
    else:
        assert jap['ideas'][ANTI_WAR] == 180
        execute(EFFECTS['RUS_easy_mode_refresh_ideas'].v, w, 'JAP', 'JAP')
        assert total(jap, 'radical_socialist_drift') == .03, 'Hostile agitation must not become a player bonus'
        assert total(jap, 'war_support_factor') == total(jap, 'conscription_factor') == -.05
        assert w['countries']['RUS']['pp'] == 25*(2 if easy else 1)
    cases += 1

for change in ('break', 'war', 'fng_missing', 'fng_socialist', 'jap_socialist'):
    w = world(chi_ai=False, chi_easy=True)
    focus(w, '026')
    fng, chi = w['countries']['FNG'], w['countries']['CHI']
    assert fng['ideas'][RESISTANCE] == 180
    fng['flags'].add(EASY); fng['ai'] = False
    execute(EFFECTS['RUS_easy_mode_refresh_ideas'].v, w, 'FNG', 'FNG')
    for key, amount in {'stability_factor': -.05, 'industrial_capacity_factory': -.1,
                        'army_org_factor': -.15, 'army_attack_factor': -.075, 'attrition': .15}.items():
        assert math.isclose(total(fng, key), amount), 'Resistance penalties must never double'
    if change == 'break': w['japan_broke'] = True
    if change == 'war': w['countries']['JAP']['wars'].add('FNG')
    if change == 'fng_missing': fng['exists'] = False
    if change == 'fng_socialist': fng['socialist'] = True
    if change == 'jap_socialist': w['countries']['JAP']['socialist'] = True
    daily(w)
    assert RESISTANCE not in fng['ideas'] and combat(chi, 'FNG') == 0
    assert (combat(chi, 'JAP') == 0) == (change == 'jap_socialist')
    assert math.isclose(total(chi, 'supply_consumption_factor'), -.2)
    cases += 1

assert 'RUS_east_asia_refresh_cooperation = yes' in (R / 'common/scripted_effects/RUS_easy_mode_effects.txt').read_text()
assert len(IDEAS) == 9
for lang in ('simp_chinese', 'english', 'russian'):
    p = R / f'localisation/{lang}/RUS_east_asia_cooperation_l_{lang}.yml'
    assert p.read_bytes().startswith(b'\xef\xbb\xbf')
    text = p.read_text(encoding='utf-8-sig')
    for key in IDEAS: assert text.count(' '+key+':') == 1
    for key in OPINIONS: assert text.count(' '+key+':') == 1
print(f'PASS: {cases} East Asia scenarios: recipients, mutually exclusive rewards, war guards, monthly capacity, expiry, and easy-mode lifecycle.')
