"""Exercise shipped India branches and recipient scopes; not an HOI4 engine test."""
from __future__ import annotations

from copy import deepcopy
from itertools import product

from hoi4_politics_blocks import R, load


FOCUS = next(n for n in load(R / 'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt')
             if n.value('id') == 'RUS_future_foreign_038')
EFFECTS = {n.k: n for rel in ('common/scripted_effects/RUS_subcontinental_dawn_effects.txt',
                             'common/scripted_effects/RUS_easy_mode_ideas_effects.txt')
           for n in load(R / rel)}
IDEAS = load(R / 'common/ideas/RUS_subcontinental_dawn_ideas.txt')[0].one('country')
ECONOMIC = 'RUS_subcontinental_economic_aid'
MILITARY = 'RUS_subcontinental_military_aid'
BONUS = 'RUS_easy_mode_ideas_bonus'
EASY = 'RUS_easy_mode_enabled'
EXPECTED = {
    ECONOMIC: {'trade_opinion_factor': .25, 'stability_factor': .05,
               'resource_trade_cost_bonus_per_factory': 2, 'min_export': .10},
    MILITARY: {'army_org_factor': .05, 'attrition': -.10,
               'army_org_regain': .10, 'terrain_penalty_reduction': .15},
}


def country(tag, *, socialist=False, ai=True, easy=False):
    return dict(tag=tag, socialist=socialist, ai=ai, flags={EASY} if easy else set(),
                ideas=set(), vars={}, dynamic=set())


def world(unified=False):
    return dict(countries={'RUS': country('RUS', socialist=True, ai=False),
                           'GER': country('GER')},
                flags={'india_united'} if unified else set(), pacts=set(), wargoals=[])


def scope(name, current, root, previous):
    return {'ROOT': root, 'PREV': previous, 'THIS': current}.get(name, name)


def check(nodes, w, current, root, previous):
    c = w['countries'][current]
    def one(n):
        k, v = n.k, n.v
        if k == 'OR': return any(one(x) for x in v)
        if k == 'NOT': return not all(one(x) for x in v)
        if k in ('AND', 'hidden_trigger'): return all(one(x) for x in v)
        if k == 'tag': return current == scope(v, current, root, previous)
        if k == 'has_global_flag': return v in w['flags']
        if k == 'has_country_flag': return v in c['flags']
        if k == 'has_socialist_government': return c['socialist'] == (v == 'yes')
        if k == 'is_ai': return c['ai'] == (v == 'yes')
        if k == 'has_idea': return v in c['ideas']
        if k == 'has_dynamic_modifier': return n.value('modifier') in c['dynamic']
        if k == 'check_variable':
            return all(x.op == '>' and c['vars'].get(x.k, 0) > float(x.v) for x in v)
        raise AssertionError(('Unsupported trigger', k))
    return all(one(n) for n in nodes)


def run(nodes, w, current='RUS', root='RUS', previous=None):
    matched = False
    for n in nodes:
        k, v = n.k, n.v
        if k in ('if', 'else_if', 'else'):
            if k == 'if': matched = False
            if not matched and (k == 'else' or check(n.one('limit').v, w, current, root, previous)):
                run([x for x in v if x.k != 'limit'], w, current, root, previous)
                matched = True
            continue
        matched = False
        c = w['countries'][current]
        if k in EFFECTS:
            run(EFFECTS[k].v, w, current, root, previous)
        elif k == 'hidden_effect':
            run(v, w, current, root, previous)
        elif k == 'ROOT':
            run(v, w, root, root, current)
        elif k == 'every_other_country':
            for tag in list(w['countries']):
                if tag != current and check(n.one('limit').v, w, tag, root, current):
                    run([x for x in v if x.k != 'limit'], w, tag, root, current)
        elif k == 'add_ideas':
            assert v in EXPECTED
            c['ideas'].add(v)
        elif k == 'diplomatic_relation':
            assert n.value('relation') == 'non_aggression_pact'
            other = scope(n.value('country'), current, root, previous)
            assert other != current and other in w['countries']
            w['pacts'].add(frozenset((current, other)))
        elif k == 'create_wargoal':
            assert n.value('type') == 'annex_everything'
            other = scope(n.value('target'), current, root, previous)
            assert other != current and other in w['countries']
            w['wargoals'].append((current, other))
        elif k in ('set_variable', 'add_to_variable'):
            for x in v:
                c['vars'][x.k] = (c['vars'].get(x.k, 0) if k == 'add_to_variable' else 0) + float(x.v)
        elif k == 'add_dynamic_modifier': c['dynamic'].add(n.value('modifier'))
        elif k == 'remove_dynamic_modifier': c['dynamic'].discard(n.value('modifier'))
        elif k == 'force_update_dynamic_modifier': pass  # The engine updates display/effective modifiers.
        else: raise AssertionError(('Unsupported effect', k))


def values(c):
    result = {}
    for idea in c['ideas']:
        for k, v in EXPECTED[idea].items(): result[k] = result.get(k, 0) + v
    if BONUS in c['dynamic']:
        for k in result: result[k] += c['vars'].get('RUS_easy_mode_idea_' + k, 0)
    return result


for idea in IDEAS.v:
    assert {n.k: float(n.v) for n in idea.one('modifier').v} == EXPECTED[idea.k]
    assert idea.value('removal_cost') == '-1'
    assert not idea.children('cancel') and not idea.children('do_effect')

cases = 0
# HOI4 builds the displayed recipient list from the iterator limit, not inner ifs.
# Filtering only inside the country block can show all three Indian regimes.
branches = EFFECTS['RUS_subcontinental_dawn_effect']
peace = branches.one('if').children('every_other_country')
assert [n.one('limit').value('has_socialist_government') for n in peace] == ['yes', 'no']
military_recipients = branches.one('else').one('every_other_country')
assert military_recipients.one('limit').value('has_socialist_government') == 'yes'
assert military_recipients.value('add_ideas') == MILITARY

for tag, socialist, easy in product(('HND', 'RAJ', 'PRF'), (False, True), (False, True)):
    w = world(unified=True)
    w['countries'][tag] = country(tag, socialist=socialist)
    if easy: w['countries']['RUS']['flags'].add(EASY)
    run(FOCUS.one('completion_reward').v, w)
    rus, india = w['countries']['RUS'], w['countries'][tag]
    if socialist:
        assert rus['ideas'] == india['ideas'] == {ECONOMIC}
        assert values(india) == EXPECTED[ECONOMIC], 'AI India must not inherit the Russian easy bonus'
        assert values(rus) == {k: v * (2 if easy else 1) for k, v in EXPECTED[ECONOMIC].items()}
        assert w['pacts'] == {frozenset(('RUS', tag))} and not w['wargoals']
        # Recomputing, or enabling easy mode after the reward, never replays diplomacy/rewards.
        diplomacy = deepcopy((w['pacts'], w['wargoals']))
        rus['flags'].add(EASY)
        for _ in range(2): run(EFFECTS['RUS_easy_mode_refresh_ideas'].v, w)
        assert values(rus) == {k: v * 2 for k, v in EXPECTED[ECONOMIC].items()}
        assert diplomacy == (w['pacts'], w['wargoals']) and rus['ideas'] == {ECONOMIC}
    else:
        assert w['wargoals'] == [('RUS', tag)] and not w['pacts']
        assert not rus['ideas'] and not india['ideas']
    assert not w['countries']['GER']['ideas']
    cases += 1

# Fragmented India: rotate the socialist recipient to catch a hard-coded HND scope.
for socialist_tag, ai, easy in product(('HND', 'RAJ', 'PRF'), (False, True), (False, True)):
    w = world()
    w['countries']['RUS']['flags'].add(EASY)
    for tag in ('HND', 'RAJ', 'PRF'):
        w['countries'][tag] = country(tag, socialist=(tag == socialist_tag), ai=ai, easy=easy)
    run(FOCUS.one('completion_reward').v, w)
    assert not w['pacts'] and not w['wargoals']
    for tag, c in w['countries'].items():
        assert c['ideas'] == ({MILITARY} if tag == socialist_tag else set())
    target = w['countries'][socialist_tag]
    assert values(target) == {k: v * (2 if easy and not ai else 1) for k, v in EXPECTED[MILITARY].items()}
    # The national spirit is permanent: later unification does not replay the focus.
    w['flags'].add('india_united')
    run(EFFECTS['RUS_easy_mode_refresh_ideas'].v, w, socialist_tag, socialist_tag)
    assert target['ideas'] == {MILITARY} and not w['pacts'] and not w['wargoals']
    cases += 1

for unified in (False, True):
    w = world(unified)
    run(FOCUS.one('completion_reward').v, w)
    assert not w['pacts'] and not w['wargoals'] and not any(c['ideas'] for c in w['countries'].values())
    cases += 1

w = world()
for tag in ('HND', 'RAJ', 'PRF'): w['countries'][tag] = country(tag)
run(FOCUS.one('completion_reward').v, w)
assert not w['pacts'] and not w['wargoals'] and not any(c['ideas'] for c in w['countries'].values())
cases += 1

for language in ('simp_chinese', 'english', 'russian'):
    p = R / f'localisation/{language}/RUS_subcontinental_dawn_l_{language}.yml'
    assert p.read_bytes().startswith(b'\xef\xbb\xbf')
    text = p.read_text(encoding='utf-8-sig')
    assert text.startswith(f'l_{language}:')
    for key in EXPECTED:
        assert text.count(f' {key}:') == 1 and text.count(f' {key}_desc:') == 1

assert not FOCUS.one('select_effect'), 'Rewards must wait for focus completion'
print(f'PASS: {cases} India scenarios, bilateral scope, native values, easy-mode recipient isolation, refresh and three languages.')
