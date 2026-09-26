"""Exercise the focus's actual conditions and native reward scopes in fixtures."""
from copy import deepcopy
from itertools import product
import math
import os
from pathlib import Path

from hoi4_politics_blocks import R, load


FOCUS = next(n for n in load(R / 'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt')
             if n.value('id') == 'RUS_future_foreign_025')
EASY = 'RUS_easy_mode_enabled'
WAR_OVER = 'LEP_league_war_over'
KR = Path(os.environ.get('HOI4_KR_ROOT', R.parent / '1521695605'))


def country(*, exists=True, ai=True, easy=False):
    return dict(exists=exists, ai=ai, flags={EASY} if easy else set(), factories=0, pp=0,
                equipment={}, stability=.4, radical_socialist=.2)


def check(nodes, world, flags, current='RUS'):
    c = world[current]
    for n in nodes:
        if n.k == 'hidden_trigger': ok = check(n.v, world, flags, current)
        elif n.k == 'has_global_flag': ok = n.v in flags
        elif n.k == 'country_exists': ok = world[n.v]['exists']
        elif n.k == 'has_country_flag': ok = n.v in c['flags']
        elif n.k == 'is_ai': ok = c['ai'] == (n.v == 'yes')
        else: raise AssertionError(('Unsupported trigger', n.k))
        if not ok: return False
    return True


def run(nodes, world, flags, current='RUS'):
    c = world[current]
    for n in nodes:
        if n.k in world:
            if world[n.k]['exists']: run(n.v, world, flags, n.k)
        elif n.k == 'if':
            if check(n.one('limit').v, world, flags, current):
                run([x for x in n.v if x.k != 'limit'], world, flags, current)
        elif n.k == 'add_offsite_building':
            assert n.value('type') == 'industrial_complex', 'Aid must be civilian industry'
            c['factories'] += int(n.value('level'))
        elif n.k == 'add_political_power': c['pp'] += int(n.v)
        elif n.k == 'add_equipment_to_stockpile':
            equipment = n.value('type')
            c['equipment'][equipment] = c['equipment'].get(equipment, 0) + int(n.value('amount'))
        elif n.k == 'add_stability': c['stability'] += float(n.v)
        elif n.k == 'add_popularity':
            assert n.value('ideology') == 'radical_socialist'
            c['radical_socialist'] += float(n.value('popularity'))
        else: raise AssertionError(('Unsupported effect', n.k))


cases = 0
for war_over, exists, ai, chi_easy, rus_easy in product((False, True), repeat=5):
    flags = {WAR_OVER} if war_over else set()
    world = {'RUS': country(ai=False, easy=rus_easy),
             'CHI': country(exists=exists, ai=ai, easy=chi_easy),
             'FNG': country(), 'ANQ': country()}
    before = deepcopy(world)
    allowed = check(FOCUS.one('available').v, world, flags)
    assert allowed == (war_over and exists), 'Both new requirements must be met'
    if allowed: run(FOCUS.one('completion_reward').v, world, flags)
    for tag in ('RUS', 'FNG', 'ANQ'): assert world[tag] == before[tag], 'Aid must only reach CHI'
    if allowed:
        factor = 2 if chi_easy and not ai else 1
        c = world['CHI']
        assert (c['factories'], c['pp']) == (factor, 50 * factor)
        assert c['equipment'] == {'infantry_equipment': 5000 * factor,
                                  'artillery_equipment': 250 * factor,
                                  'support_equipment': 500 * factor}
        assert math.isclose(c['stability'], .4 + .05 * factor)
        assert math.isclose(c['radical_socialist'], .2 + .05 * factor)
        world['CHI']['exists'] = False
        assert not check(FOCUS.one('available').v, world, flags), 'Loss of CHI must invalidate the focus'
    else: assert world == before
    cases += 1

assert FOCUS.one('prerequisite').value('focus') == 'RUS_future_foreign_010'
assert FOCUS.one('select_effect') is None, 'Do not award aid merely for starting the focus'
assert FOCUS.one('bypass') is None
# Validate the upstream condition contract, including its existing player-facing name.
kr_effects = (KR / 'common/scripted_effects/01_China effects.txt').read_text(encoding='utf-8-sig')
kr_loc = (KR / 'localisation/english/KR_common/03 China l_english.yml').read_text(encoding='utf-8-sig')
assert 'set_global_flag = ' + WAR_OVER in kr_effects
assert ' ' + WAR_OVER + ':' in kr_loc
print(f'PASS: {cases} Defend Red China scenarios; war/existence gates, CHI-only aid, equipment, stability and per-recipient easy mode.')
