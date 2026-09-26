"""Exercise PER/AFG focus rewards, faction transfers and per-recipient easy rewards.

This interprets the shipped script in fixtures, not the HOI4 engine.
"""
from itertools import product

from hoi4_politics_blocks import R, load


FOCUSES = {n.value('id'): n for n in load(R / 'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt')
           if n.k == 'shared_focus'}
EASY = 'RUS_easy_mode_enabled'
INVASION = 'RUS_Socialist_Attack_Middle_East'


def country(tag, *, socialist=False, faction=None, leader=False, ai=True, easy=False, exists=True):
    return dict(tag=tag, socialist=socialist, faction=faction, leader=leader, ai=ai,
                flags={EASY} if easy else set(), exists=exists, pp=0)


def check(nodes, w, current='RUS'):
    c = w[current]
    for n in nodes:
        k, v = n.k, n.v
        if k in w: ok = check(v, w, k)
        elif k == 'hidden_trigger': ok = check(v, w, current)
        elif k == 'NOT': ok = not check(v, w, current)
        elif k == 'exists': ok = c['exists'] == (v == 'yes')
        elif k == 'has_socialist_government': ok = c['socialist'] == (v == 'yes')
        elif k == 'is_in_faction': ok = bool(c['faction']) == (v == 'yes')
        elif k == 'is_faction_leader': ok = c['leader'] == (v == 'yes')
        elif k == 'has_country_flag': ok = v in c['flags']
        elif k == 'is_ai': ok = c['ai'] == (v == 'yes')
        elif k == 'is_in_faction_with':
            other = w['RUS' if v == 'ROOT' else v]
            ok = bool(c['faction']) and c['faction'] == other['faction']
        else: raise AssertionError(('Unsupported trigger', k))
        if not ok: return False
    return True


def run(nodes, w, actions, current='RUS'):
    matched = False
    for n in nodes:
        k, v = n.k, n.v
        if k in ('if', 'else'):
            if k == 'if': matched = False
            if not matched and (k == 'else' or check(n.one('limit').v, w, current)):
                run([x for x in v if x.k != 'limit'], w, actions, current)
                matched = True
            continue
        matched = False
        c = w[current]
        if k in w: run(v, w, actions, k)
        elif k == 'add_political_power': c['pp'] += int(v)
        elif k == 'leave_faction':
            assert c['faction'] and not c['leader']
            actions.append((k, current))
            c['faction'] = None
        elif k == 'dismantle_faction':
            assert c['leader'] and c['faction']
            faction = c['faction']
            actions.append((k, current))
            for other in w.values():
                if other['faction'] == faction:
                    other['faction'], other['leader'] = None, False
        elif k == 'add_to_faction':
            assert current == 'RUS' and c['faction'] and c['leader']
            assert w[v]['exists'] and w[v]['faction'] is None, 'Leave the old faction before joining'
            actions.append((k, v))
            w[v]['faction'] = c['faction']
        elif k == 'activate_targeted_decision':
            actions.append((k, n.value('target'), n.value('decision')))
        else: raise AssertionError(('Unsupported effect', k))


cases = 0
for (focus, tag), socialist, faction, rus_easy, target_mode in product(
        (('RUS_future_foreign_052', 'PER'), ('RUS_future_foreign_053', 'AFG')),
        (False, True), ('none', 'russian', 'foreign_member', 'foreign_leader'),
        (False, True), ('normal_ai', 'flagged_ai', 'easy_player')):
    foreign = faction.startswith('foreign')
    w = {'RUS': country('RUS', socialist=True, faction='russian', leader=True, ai=False, easy=rus_easy),
         tag: country(tag, socialist=socialist,
                      faction='foreign' if foreign else 'russian' if faction == 'russian' else None,
                      leader=faction == 'foreign_leader', ai=target_mode != 'easy_player',
                      easy=target_mode != 'normal_ai'),
         'GER': country('GER', faction='foreign', leader=faction != 'foreign_leader')}
    actions = []
    run(FOCUSES[focus].one('completion_reward').v, w, actions)
    if socialist:
        assert w[tag]['faction'] == w['RUS']['faction'] == 'russian'
        assert w['RUS']['pp'] == (100 if rus_easy else 50)
        assert w[tag]['pp'] == (100 if target_mode == 'easy_player' else 50)
        expected = []
        if foreign: expected.append(('dismantle_faction' if faction == 'foreign_leader' else 'leave_faction', tag))
        if faction != 'russian': expected.append(('add_to_faction', tag))
        assert actions == expected, 'Same-faction recipients must not leave/rejoin or unlock an invasion'
    else:
        assert actions == [('activate_targeted_decision', tag, INVASION)]
        assert w['RUS']['pp'] == w[tag]['pp'] == 0
        assert w[tag]['faction'] == ('foreign' if foreign else 'russian' if faction == 'russian' else None)
    assert w['GER']['pp'] == 0 and w['GER']['faction'] != 'russian', 'Do not recruit or reward the old allies'
    cases += 1

# A nonexistent target must never enter the new alliance/reward branch.
for focus, tag in (('RUS_future_foreign_052', 'PER'), ('RUS_future_foreign_053', 'AFG')):
    w = {'RUS': country('RUS', faction='russian', leader=True),
         tag: country(tag, socialist=True, exists=False)}
    actions = []
    run(FOCUSES[focus].one('completion_reward').v, w, actions)
    assert w['RUS']['pp'] == w[tag]['pp'] == 0
    assert actions == [('activate_targeted_decision', tag, INVASION)]
    assert FOCUSES[focus].one('select_effect') is None
    cases += 1

decision = next(d for cat in load(R / 'common/decisions/RUS decisions (Russia).txt')
                if isinstance(cat.v, list) for d in cat.v if d.k == INVASION)
assert decision.value('name') == 'invade_country'
assert decision.one('target_trigger').one('FROM').value('has_socialist_government') == 'no'
assert {n.k for n in decision.one('targets').v} >= {'PER', 'AFG'}
assert 'has_socialist_government = no' not in decision.one('visible').raw()
print(f'PASS: {cases} PER/AFG scenarios; branch isolation, ordered faction transfer, bilateral PP, easy-mode scope and socialist invasion entry.')
