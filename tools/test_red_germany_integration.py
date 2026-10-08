"""Execute GRU release/reconstruction scripts in a bounded country/event model.

This verifies scope, scheduling, costs and one-time rewards, not the HOI4 engine.
Trigger names are also checked against the installed engine documentation so
the model cannot silently accept a made-up trigger. External helpers are opaque.
"""
from copy import deepcopy
from itertools import product
from pathlib import Path
from random import Random
import hashlib
import heapq
import json
import os
import re
import struct
import unittest

from hoi4_politics_blocks import R, KR, load, parse


GAME = Path(os.environ.get('HOI4_GAME_ROOT', R.parents[3] / 'common/Hearts of Iron IV'))
IMPORTED_SCRIPTS = [*(R / 'common').rglob('GRU_*.txt'), R / 'events/GRU_reconstruction_events.txt']
TRIGGERS = {n.k: n for f in (R / 'common/scripted_triggers').glob('GRU_*.txt') for n in load(f)}
EFFECTS = {n.k: n for f in (R / 'common/scripted_effects').glob('GRU_*.txt') for n in load(f)}
for n in load(R / 'common/scripted_effects/RUS_stalin_communist_effects.txt'):
    if n.k in {'RUS_stalin_set_country_radical_socialist_for_subject_release',
               'RUS_stalin_set_subject_radical_socialist_if_communist_path',
               'RUS_stalin_set_released_country_radical_socialist_if_from_communist_russia'}:
        EFFECTS[n.k] = n
EVENTS = {n.value('id'): n for n in load(R / 'events/GRU_reconstruction_events.txt') if n.k == 'country_event'}
EVENTS['stalin_form_sov.20'] = next(n for n in load(R / 'events/stalin_form_sov.txt') if n.value('id') == 'stalin_form_sov.20')
DECISIONS = {n.k: n for n in load(R / 'common/decisions/GRU_reconstruction_decisions.txt')[0].v}
TREE = load(R / 'common/national_focus/GRU_red_germany_focus.txt')[0]
FOCUSES = {n.value('id'): n for n in TREE.children('focus')}
FOLLOWUP_TREE = load(R / 'common/national_focus/GRU_hitler_focus.txt')[0]
FOLLOWUP_FOCUSES = {n.value('id'): n for n in FOLLOWUP_TREE.children('focus')}
IDEOLOGY_GROUPS = {subtype.k: ideology.k for ideology in load(R / 'common/ideologies/00_ideologies.txt')[0].v
                   for subtype in ideology.one('types').v}
HOOKS = load(R / 'common/on_actions/GRU_red_germany_on_actions.txt')[0]
BARS = ['GRU_bar_' + x for x in ('economy', 'security', 'livelihood')]
INF = ['GRU_inf_' + x for x in ('anarchist', 'nationalist', 'royalist')]
HITLER_LEADER = dict(name='GRU_adolf_hitler', desc='GRU_adolf_hitler_leader_desc',
                    picture='GFX_portrait_GRU_adolf_hitler', ideology='marxism_leninism_subtype')


def country(original, government='radical_socialist', overlord=None):
    return dict(original=original, government=government, overlord=overlord,
                flags=set(), variables={}, ideas={'GRU_occupation_government', 'GRU_no_standing_army'},
                pp=500., stability=.3, war_support=.1, popularities={}, war=False, ai=False,
                leader='KR occupation leader', leader_ideology='radical_socialist_subtype',
                characters=set(), leader_creations=[], leader_desc=None, leader_picture=None,
                tree='German_Puppet_focus', loaded=0, focuses=set(), party_names={},
                opaque=[], decisions={}, civil_wars=0, research_slots=3, army_experience=0.)


def world(tag='GRU', **kwargs):
    c = country('GRU', overlord='RUS')
    c.update(kwargs)
    return dict(countries={'RUS': country('RUS', 'communist'),
                           'FRA': country('FRA', 'syndicalist'), tag: c},
                tag=tag, time=0, sequence=0, queue=[], opened=[], rng=Random(4))


def cmp(a, op, b):
    return {'=': a == b, '>': a > b, '<': a < b}[op]


def walk(nodes):
    for n in nodes:
        yield n
        if isinstance(n.v, list):
            yield from walk(n.v)


def validate_condition_names(nodes, native_names):
    """Validate trigger roots; native parameter blocks are not nested triggers."""
    for n in nodes:
        if n.k in ('AND', 'OR', 'NOT', 'hidden_trigger', 'overlord', 'FROM'):
            validate_condition_names(n.v, native_names)
        elif n.k == 'custom_override_tooltip':
            validate_condition_names([x for x in n.v if x.k != 'tooltip'], native_names)
        elif n.k not in native_names and n.k not in TRIGGERS:
            raise AssertionError(('Unknown engine/scripted trigger', n.raw()))


def condition(nodes, w, tag, source=None):
    c = w['countries'].get(tag)
    if c is None:
        return False
    def one(n):
        k, v = n.k, n.v
        if k in ('AND', 'hidden_trigger'): return condition(v, w, tag, source)
        if k == 'OR': return any(one(x) for x in v)
        if k == 'NOT': return not condition(v, w, tag, source)
        if k == 'custom_override_tooltip': return condition([x for x in v if x.k != 'tooltip'], w, tag, source)
        if k in TRIGGERS: return condition(TRIGGERS[k].v, w, tag, source) == (v == 'yes')
        if k == 'overlord': return condition(v, w, c['overlord'], source)
        if k == 'FROM': return condition(v, w, source, source)
        if k in w['countries']: return condition(v, w, k, source)
        if k == 'original_tag': return c['original'] == v
        if k == 'tag': return tag == v
        if k == 'has_government': return c['government'] == v
        if k == 'has_character': return v in c['characters']
        if k == 'has_country_leader':
            assert n.value('ruling_only', 'yes') == 'yes', ('Only ruling leaders are modeled', n.raw())
            assert n.value('name'), ('Only leader name checks are modeled', n.raw())
            return c['leader'] == n.value('name')
        if k == 'has_country_flag': return v in c['flags']
        if k == 'has_war': return c['war'] == (v == 'yes')
        if k == 'is_ai': return c['ai'] == (v == 'yes')
        if k == 'is_subject': return bool(c['overlord']) == (v == 'yes')
        if k == 'has_political_power': return cmp(c['pp'], n.op, float(v))
        if k == 'check_variable': return all(cmp(c['variables'].get(x.k, 0), x.op, float(x.v)) for x in v)
        if k == 'always': return v == 'yes'
        raise AssertionError(('Unsupported condition', n.raw()))
    return all(one(n) for n in nodes)


def execute(nodes, w, tag, source=None):
    matched = False
    for n in nodes:
        k, v = n.k, n.v
        if k in ('if', 'else_if', 'else'):
            if k == 'if': matched = False
            if not matched and (k == 'else' or condition(n.one('limit').v, w, tag, source)):
                execute([x for x in v if x.k != 'limit'], w, tag, source)
                matched = True
            continue
        matched = False
        c = w['countries'][tag]
        if k in EFFECTS: execute(EFFECTS[k].v, w, tag, source)
        elif k == 'hidden_effect': execute(v, w, tag, source)
        elif k in ('effect_tooltip', 'custom_effect_tooltip', 'mark_focus_tree_layout_dirty'): pass
        elif k == 'set_country_flag': c['flags'].add(v)
        elif k == 'clr_country_flag': c['flags'].discard(v)
        elif k == 'set_country_leader_ideology': c['leader_ideology'] = v
        elif k == 'recruit_character':
            # The engine rejects runtime recruitment outside game/history.
            # A definition on disk is not an instantiated/recruitable character.
            raise AssertionError(('recruit_character is history-only in this runtime model', n.raw()))
        elif k == 'create_country_leader':
            # Native effect creates a country-local leader without a template;
            # an existing character with the same name receives the leader role.
            # Dormant party heads are outside this bounded model, so require the
            # intended party to rule before this effect executes.
            leader = {field: n.value(field) for field in ('name', 'desc', 'picture', 'ideology')}
            assert all(leader.values()), ('Incomplete runtime leader', n.raw())
            assert IDEOLOGY_GROUPS[leader['ideology']] == c['government'], ('Non-ruling party leader is outside this model', n.raw())
            c['characters'].add(leader['name'])
            c['leader'], c['leader_ideology'] = leader['name'], leader['ideology']
            c['leader_desc'], c['leader_picture'] = leader['desc'], leader['picture']
            # Record every execution: a set alone would hide duplicate creation.
            c['leader_creations'].append(leader)
        elif k == 'set_cosmetic_tag': c['cosmetic'] = v
        elif k == 'set_politics':
            c['government'] = n.value('ruling_party')
            # Model the reentrant government hook while establishing the country.
            execute(HOOKS.one('on_ruling_party_change').one('effect').v, w, tag, source)
        elif k == 'set_popularities': c['popularities'] = {x.k: float(x.v) for x in v}
        elif k == 'set_political_party': c['popularities'][n.value('ideology')] = float(n.value('popularity'))
        elif k == 'set_party_name': c['party_names'][n.value('ideology')] = n.value('name')
        elif k == 'load_focus_tree':
            c['tree'] = n.value('tree')
            c['loaded'] += 1
            if n.value('keep_completed') == 'no': c['focuses'].clear()
        elif k == 'add_ideas': c['ideas'].add(v)
        elif k == 'remove_ideas': c['ideas'].discard(v)
        elif k in ('add_political_power', 'add_stability', 'add_war_support'):
            c[{'add_political_power': 'pp', 'add_stability': 'stability', 'add_war_support': 'war_support'}[k]] += float(v)
        elif k == 'add_research_slot': c['research_slots'] += int(v)
        elif k == 'army_experience': c['army_experience'] += float(v)
        elif k == 'add_popularity':
            ideology = n.value('ideology')
            c['popularities'][ideology] = c['popularities'].get(ideology, 0) + 100 * float(n.value('popularity'))
        elif k in ('set_variable', 'add_to_variable', 'subtract_from_variable'):
            key, value = n.value('var'), n.value('value')
            value = c['variables'][value] if value in c['variables'] else float(value)
            c['variables'][key] = (0 if k == 'set_variable' else c['variables'].get(key, 0)) + (-value if k == 'subtract_from_variable' else value)
        elif k == 'clamp_variable':
            key = n.value('var')
            c['variables'][key] = min(float(n.value('max')), max(float(n.value('min')), c['variables'][key]))
        elif k == 'randomize_variable':
            assert n.value('distribution') == 'uniform'
            c['variables'][n.value('var')] = w['rng'].uniform(float(n.value('min')), float(n.value('max')))
        elif k == 'round_variable': c['variables'][v] = round(c['variables'][v])
        elif k == 'random_list': execute(w['rng'].choice(v).v, w, tag, source)
        elif k == 'country_event':
            delay = float(n.value('days', 0)) * 24 + float(n.value('hours', 0))
            w['sequence'] += 1
            heapq.heappush(w['queue'], (w['time'] + delay, w['sequence'], tag, n.value('id'), source))
        elif k == 'start_civil_war':
            c['civil_wars'] += 1
            c['war'] = True
            if n.value('ruling_party'): c['government'] = n.value('ruling_party')
            rebels = deepcopy(c)
            rebels.update(government=n.value('ideology'), overlord=None)
            w['countries']['REB'] = rebels
            execute([x for x in v if x.k not in ('ideology', 'ruling_party', 'size')], w, 'REB', tag)
        elif k in ('set_government_flags', 'RUS_stalin_setup_gxc_peng_pai_subject'):
            c['opaque'].append(k)  # unchanged external helper, not a scripted no-op
        else: raise AssertionError(('Unsupported effect', n.raw()))


def effect(w, name, tag=None, source=None):
    execute(EFFECTS[name].v, w, tag or w['tag'], source)


def fire(w, event_id, tag=None, source=None):
    tag = tag or w['tag']
    e = EVENTS[event_id]
    if e.one('trigger') and not condition(e.one('trigger').v, w, tag, source): return False
    if e.one('immediate'): execute(e.one('immediate').v, w, tag, source)
    if e.children('option'): w['opened'].append((tag, event_id))
    return True


def advance(w, days):
    stop = w['time'] + days * 24
    while w['queue'] and w['queue'][0][0] <= stop:
        when, _, tag, eid, source = heapq.heappop(w['queue'])
        w['time'] = when
        fire(w, eid, tag, source)
    w['time'] = stop


def choose(w, eid, index=0):
    option = EVENTS[eid].children('option')[index]
    if option.one('trigger') and not condition(option.one('trigger').v, w, w['tag']):
        return False
    execute([n for n in option.v if n.k not in ('name', 'trigger', 'ai_chance')], w, w['tag'])
    return True


def decision(w, key):
    d, tag = DECISIONS[key], w['tag']
    c = w['countries'][tag]
    if not condition(d.one('visible').v, w, tag) or not condition(d.one('available').v, w, tag): return False
    if c['decisions'].get(key, -1) > w['time']: return False
    cost = float(d.value('cost', 0))
    if c['pp'] < cost: return False
    c['pp'] -= cost
    execute(d.one('complete_effect').v, w, tag)
    c['decisions'][key] = float('inf') if d.value('fire_only_once') == 'yes' else w['time'] + 24 * float(d.value('days_re_enable', 0))
    return True


def established(tag='GRU'):
    w = world(tag)
    effect(w, 'GRU_establish_red_germany')
    return w, w['countries'][tag]


class ReleaseTests(unittest.TestCase):
    def test_eligibility_matrix(self):
        for original, overlord, government, war in product(('GRU', 'GER', 'AUS'), ('RUS', 'FRA', None), ('communist', 'radical_socialist', 'social_democrat'), (False, True)):
            w = world('D03', original=original, overlord=overlord, government=government, war=war)
            eligible = original == 'GRU' and overlord == 'RUS' and government != 'social_democrat' and not war
            self.assertEqual(condition(TRIGGERS['GRU_can_become_red_germany'].v, w, 'D03'), eligible)

    def test_russia_route_flag_and_other_socialist_overlords(self):
        w = world()
        rus = w['countries']['RUS']
        rus['government'] = 'social_democrat'
        self.assertFalse(condition(TRIGGERS['GRU_can_become_red_germany'].v, w, 'GRU'))
        rus['flags'].add('RUS_stalin_communist_path')
        self.assertTrue(condition(TRIGGERS['GRU_can_become_red_germany'].v, w, 'GRU'))
        w['countries']['GRU']['overlord'] = 'FRA'
        w['countries']['FRA']['government'] = 'communist'
        self.assertFalse(condition(TRIGGERS['GRU_can_become_red_germany'].v, w, 'GRU'))

    def test_deferred_release_handover_and_duplicate_callbacks(self):
        for tag in ('GRU', 'D03'):
            w = world(tag)
            c = w['countries'][tag]
            for hook in HOOKS.v: execute(hook.one('effect').v, w, tag, 'RUS')
            self.assertEqual(len(w['queue']), 1)
            self.assertEqual(c['tree'], 'German_Puppet_focus')
            # KR completes its reset after release hooks, before our next-day event.
            c['government'] = 'radical_socialist'
            c['popularities'] = {'radical_socialist': 27}
            advance(w, 1)
            self.assertEqual(c['tree'], 'GRU_red_germany_focus')
            self.assertEqual(c['government'], 'communist')
            self.assertEqual(c['popularities']['communist'], 55)
            self.assertEqual(c['popularities']['radical_socialist'], 0)
            self.assertEqual(sum(c['popularities'].values()), 100)
            self.assertEqual(c['leader'], 'KR occupation leader')
            self.assertEqual(c['leader_ideology'], 'marxism_leninism_subtype')
            self.assertNotIn('GRU_occupation_government', c['ideas'])
            self.assertIn('GRU_no_standing_army', c['ideas'])
            self.assertIn('GRU_collapsed_germany', c['ideas'])
            self.assertEqual(c['loaded'], 1)
            self.assertEqual([(e[3], e[0]) for e in w['queue']], [('GRU_reconstruction.1', 21 * 24)])

    def test_wartime_release_waits_for_peace(self):
        w = world(war=True)
        effect(w, 'GRU_queue_red_germany_setup')
        self.assertFalse(w['queue'])
        w['countries']['GRU']['war'] = False
        effect(w, 'GRU_queue_red_germany_setup')
        advance(w, 1)
        self.assertEqual(w['countries']['GRU']['government'], 'communist')

    def test_loss_of_eligibility_clears_pending_and_can_retry(self):
        for field, value in (('war', True), ('overlord', 'FRA'), ('government', 'social_democrat')):
            w = world()
            c = w['countries']['GRU']
            effect(w, 'GRU_queue_red_germany_setup')
            before = c[field]
            c[field] = value
            advance(w, 1)
            self.assertNotIn('GRU_red_germany_established', c['flags'])
            self.assertNotIn('GRU_red_germany_setup_pending', c['flags'])
            c[field] = before
            effect(w, 'GRU_queue_red_germany_setup')
            advance(w, 1)
            self.assertEqual(c['loaded'], 1)

    def test_old_conversion_entry_points_leave_managed_gru_alone(self):
        for tag in ('GRU', 'D03'):
            w, c = established(tag)
            c['government'] = 'syndicalist'  # a later choice must not be overwritten
            c['variables'][BARS[0]] = 74
            c['focuses'].add('GRU_new_german_government')
            before = deepcopy(c)
            for name in EFFECTS:
                if name.startswith('RUS_stalin_set_'): effect(w, name, source='RUS')
            self.assertFalse(fire(w, 'stalin_form_sov.20'))
            effect(w, 'GRU_establish_red_germany')
            effect(w, 'GRU_init_reconstruction')
            self.assertEqual(c, before)

    def test_other_puppets_keep_original_behavior(self):
        for tag in ('KOR', 'GXC', 'POL'):
            w = world(tag, original=tag, government='communist')
            effect(w, 'RUS_stalin_set_released_country_radical_socialist_if_from_communist_russia', source='RUS')
            c = w['countries'][tag]
            self.assertEqual(c['government'], 'radical_socialist')
            self.assertEqual(c['popularities']['radical_socialist'], 55)
            self.assertEqual([x[3] for x in w['queue']], ['stalin_form_sov.20'])
            self.assertEqual('RUS_stalin_setup_gxc_peng_pai_subject' in c['opaque'], tag == 'GXC')

    def test_debug_does_not_replace_russian_or_german_imperial_tree(self):
        for original in ('RUS', 'GER'):
            w = world('OTHER', original=original)
            effect(w, 'GRU_establish_red_germany')
            self.assertFalse(fire(w, 'GRU_reconstruction.99'))
            self.assertEqual(w['countries']['OTHER']['loaded'], 0)


class ReconstructionTests(unittest.TestCase):
    def assert_hitler_leads(self, c):
        self.assertEqual(c['leader'], 'GRU_adolf_hitler')
        self.assertEqual(c['leader_ideology'], 'marxism_leninism_subtype')
        self.assertEqual(c['government'], 'communist')
        self.assertIn('GRU_adolf_hitler', c['characters'])
        self.assertEqual(c['leader_desc'], 'GRU_adolf_hitler_leader_desc')
        self.assertEqual(c['leader_picture'], 'GFX_portrait_GRU_adolf_hitler')
        self.assertEqual(c['leader_creations'], [HITLER_LEADER])
        self.assertEqual(c['party_names']['communist'], 'GRU_hitler_communist_party')

    def test_exact_thresholds(self):
        for values in product((0, 80, 81, 99, 100), repeat=3):
            w, c = established()
            c['variables'].update(zip(BARS, values))
            c['variables'].update(zip(INF, values))
            self.assertEqual(condition(TRIGGERS['GRU_two_bars_full'].v, w, 'GRU'), sum(x == 100 for x in values) >= 2)
            self.assertEqual(condition(TRIGGERS['GRU_saboteurs_collapse'].v, w, 'GRU'), sum(x == 100 for x in values) >= 2)
            self.assertEqual(condition(TRIGGERS['GRU_any_saboteur_strong'].v, w, 'GRU'), max(values) > 80)

    def test_decision_costs_cooldowns_and_clamps(self):
        for suffix, var in zip(('economy', 'security', 'livelihood'), BARS):
            w, c = established()
            c['variables'][var] = 98
            self.assertTrue(decision(w, 'GRU_invest_' + suffix))
            self.assertEqual(c['pp'], 450)
            self.assertAlmostEqual(c['stability'], .31)
            self.assertEqual(c['variables'][var], 100)
            self.assertFalse(decision(w, 'GRU_invest_' + suffix))
        for suffix, var in zip(('anarchist', 'nationalist', 'royalist'), INF):
            w, c = established()
            c['variables'][var] = 8
            self.assertTrue(decision(w, 'GRU_suppress_' + suffix))
            self.assertEqual(c['variables'][var], 0)
            self.assertEqual(c['pp'], 450)
            self.assertAlmostEqual(c['war_support'], .11)
            c['variables'][var] = 20
            self.assertFalse(decision(w, 'GRU_suppress_' + suffix))
            w['time'] = 90 * 24
            self.assertTrue(decision(w, 'GRU_suppress_' + suffix))
            self.assertEqual(c['variables'][var], 10)

    def test_twenty_day_pulse_and_shutdown(self):
        w, c = established()
        advance(w, 19)
        self.assertFalse(w['opened'])
        advance(w, 1)
        self.assertEqual(len(w['opened']), 1)
        advance(w, 20)
        self.assertEqual(len(w['opened']), 2)
        c['flags'].discard('GRU_reconstruction_ongoing')
        advance(w, 100)
        self.assertEqual(len(w['opened']), 2)
        self.assertFalse(w['queue'])

    def test_sabotage_costs_random_ranges_and_stale_windows(self):
        for i, inf, bar in zip((2, 3, 4), INF, (BARS[1], BARS[2], BARS[0])):
            w, c = established()
            c['variables'][bar] = 50
            choose(w, f'GRU_reconstruction.{i}', 0)
            self.assertEqual(c['pp'], 485)
            self.assertEqual(c['variables'][bar], 50)
            self.assertEqual(c['variables'][inf], 2)
            choose(w, f'GRU_reconstruction.{i}', 1)
            self.assertTrue(40 <= c['variables'][bar] <= 49)
            self.assertTrue(6 <= c['variables'][inf] <= 10)
            c['flags'].discard('GRU_reconstruction_ongoing')
            before = deepcopy(c)
            choose(w, f'GRU_reconstruction.{i}', 0)
            choose(w, f'GRU_reconstruction.{i}', 1)
            self.assertEqual(c, before)

    def test_suppression_option_requires_exact_political_power_cost(self):
        for i, pp in product((2, 3, 4), (-1, 0, 14.99, 15, 15.01)):
            with self.subTest(event=i, political_power=pp):
                w, c = established()
                c['pp'] = pp
                before = deepcopy(c)
                chosen = choose(w, f'GRU_reconstruction.{i}', 0)
                self.assertEqual(chosen, pp >= 15)
                if chosen:
                    self.assertAlmostEqual(c['pp'], pp - 15)
                    self.assertEqual(c['variables'][INF[i - 2]], 2)
                else:
                    self.assertEqual(c, before)
                    # The free alternative remains available below the cost.
                    self.assertTrue(choose(w, f'GRU_reconstruction.{i}', 1))
                    self.assertEqual(c['pp'], pp)

    def test_election_outcomes_visible_rewards_once(self):
        # Explicit cases cover the strict >80 boundary and nationalist priority
        # when several factions are strong, without triggering the two-100 war.
        cases = (((80, 80, 80), 6), ((80.01, 80, 0), 7), ((0, 80, 81), 7),
                 ((0, 80.01, 0), 8), ((81, 81, 81), 8), ((0, 100, 0), 8))
        for (influence, outcome), prepared, ai, tag in product(cases, (False, True), (False, True), ('GRU', 'D03')):
            with self.subTest(influence=influence, prepared=prepared, ai=ai, tag=tag):
                w, c = established(tag)
                c['ai'] = ai
                c['variables'].update(zip(BARS, (100, 100, 0)))
                c['variables'].update(zip(INF, influence))
                c['focuses'].add('GRU_new_german_government')
                if prepared: c['flags'].add('GRU_first_election_prepared')
                self.assertTrue(decision(w, 'GRU_hold_first_election'))
                self.assertFalse(decision(w, 'GRU_hold_first_election'))
                advance(w, 6)
                self.assertFalse(w['opened'])
                advance(w, 1)
                eid = f'GRU_reconstruction.{outcome}'
                self.assertEqual(w['opened'], [(tag, eid)])
                # An open window cannot settle early or open a competing result.
                self.assertEqual((c['pp'], c['stability'], c['war_support']), (500, .3, .1))
                self.assertEqual(c['loaded'], 1)
                self.assertEqual(c['leader'], 'KR occupation leader')
                self.assertFalse(c['characters'])
                self.assertIn('GRU_collapsed_germany', c['ideas'])
                for i in (5, 6, 7, 8): self.assertFalse(fire(w, f'GRU_reconstruction.{i}'))
                # All results have one option; AI and human scopes can both use
                # it. This exercises script conditions, not engine AI timing.
                self.assertEqual(len(EVENTS[eid].children('option')), 1)
                self.assertTrue(choose(w, eid))
                self.assertNotIn('GRU_collapsed_germany', c['ideas'])
                self.assertEqual(c['popularities']['communist'], 65)
                self.assertEqual(c['popularities']['radical_socialist'], 0)
                rewards = {6: (600 + 50 * prepared, .5 + .05 * prepared, .1),
                           7: (625, .3 + .05 * prepared, .05),
                           8: (600 + 50 * prepared, .4, .2)}
                for key, value in zip(('pp', 'stability', 'war_support'), rewards[outcome]):
                    self.assertAlmostEqual(c[key], value)
                self.assertEqual(c['tree'], 'GRU_hitler_focus' if outcome == 8 else 'GRU_red_germany_focus')
                self.assertEqual(c['loaded'], 2 if outcome == 8 else 1)
                self.assertEqual(c['focuses'], set() if outcome == 8 else {'GRU_new_german_government'})
                self.assertEqual('GRU_hitler_path' in c['flags'], outcome == 8)
                self.assertEqual('GRU_sabotaged_election' in c['flags'], outcome == 7)
                self.assertEqual(c['government'], 'communist')
                if outcome == 8:
                    self.assert_hitler_leads(c)
                else:
                    self.assertEqual(c['leader'], 'KR occupation leader')
                    self.assertFalse(c['characters'])
                before = deepcopy(c)
                choose(w, eid)
                effect(w, 'GRU_finish_reconstruction')
                effect(w, 'GRU_enter_hitler_path')
                self.assertFalse(fire(w, eid))
                self.assertEqual(c, before)
                advance(w, 100)
                self.assertFalse(w['queue'])

    def test_collapse_cancels_pending_or_open_election(self):
        for (outcome, influence), open_first in product(((6, (0, 0, 0)), (7, (81, 0, 0)), (8, (0, 81, 0))), (False, True)):
            w, c = established()
            c['variables'].update(zip(BARS, (100, 100, 0)))
            c['variables'].update(zip(INF, influence))
            decision(w, 'GRU_hold_first_election')
            if open_first: advance(w, 7)
            c['variables'].update(zip(INF, (100, 0, 100)))
            before_pp = c['pp']
            effect(w, 'GRU_check_saboteur_collapse')
            effect(w, 'GRU_check_saboteur_collapse')
            advance(w, 7)
            before = deepcopy(c)
            choose(w, f'GRU_reconstruction.{outcome}')  # stale window must not award anything
            effect(w, 'GRU_enter_hitler_path')
            self.assertFalse(fire(w, 'GRU_reconstruction.97'))
            self.assertFalse(fire(w, 'GRU_reconstruction.8'))
            self.assertEqual(c, before)
            self.assertNotIn('GRU_first_election_held', c['flags'])
            self.assertNotIn('GRU_hitler_path', c['flags'])
            self.assertEqual(c['pp'], before_pp)
            self.assertEqual(c['civil_wars'], 1)
            self.assertFalse(fire(w, 'GRU_reconstruction.10'))
            self.assertEqual(c['government'], 'communist')
            rebel = w['countries']['REB']
            self.assertEqual(rebel['government'], 'paternal_autocrat')
            self.assertEqual(rebel['tree'], 'German_Puppet_focus')
            self.assertNotIn('GRU_red_germany_established', rebel['flags'])
            self.assertFalse(condition(TRIGGERS['GRU_reconstruction_active'].v, w, 'REB'))
            self.assertFalse(condition(TRIGGERS['GRU_can_become_red_germany'].v, w, 'REB'))

    def test_followup_queue_deduplicates_and_respects_collapse(self):
        w, c = established()
        c['flags'].add('GRU_first_election_scheduled')
        c['variables'][INF[1]] = 81
        # Dispatch twice before the zero-delay result is consumed. Its own guard
        # must allow only one window, even if duplicate dispatches were queued.
        self.assertTrue(fire(w, 'GRU_reconstruction.5'))
        self.assertTrue(fire(w, 'GRU_reconstruction.5'))
        advance(w, 0)
        self.assertEqual(w['opened'], [('GRU', 'GRU_reconstruction.8')])
        w, c = established()
        c['flags'].add('GRU_first_election_scheduled')
        c['variables'][INF[1]] = 81
        self.assertTrue(fire(w, 'GRU_reconstruction.5'))
        c['variables'].update(zip(INF, (100, 100, 0)))
        effect(w, 'GRU_check_saboteur_collapse')
        advance(w, 0)
        self.assertFalse(w['opened'])
        self.assertEqual(c['loaded'], 1)
        self.assertEqual(c['pp'], 500)

    def test_followup_debug_has_only_base_settlement_and_is_repeat_safe(self):
        for tag, prepared in product(('GRU', 'D03'), (False, True)):
            # Debug intentionally bypasses the normal Russian-overlord/peace
            # qualification but must still respect original_tag and civil war.
            w = world(tag, overlord=None, government='social_democrat', war=True)
            c = w['countries'][tag]
            if prepared: c['flags'].add('GRU_first_election_prepared')
            self.assertFalse(c['characters'])  # no history-instantiated leader
            self.assertFalse(c['leader_creations'])
            self.assertTrue(fire(w, 'GRU_reconstruction.97'))
            self.assertEqual(c['tree'], 'GRU_hitler_focus')
            self.assertEqual(c['loaded'], 2)
            self.assertEqual(c['pp'], 600)  # no .8 prepared/war-support reward
            self.assertAlmostEqual(c['stability'], .45)
            self.assertAlmostEqual(c['war_support'], .1)
            self.assertEqual(c['popularities']['communist'], 65)
            self.assertIn('GRU_hitler_path', c['flags'])
            self.assert_hitler_leads(c)
            c['focuses'].add('GRU_national_revolution')
            c['variables'][BARS[0]] = 74
            before, queue = deepcopy(c), list(w['queue'])
            self.assertTrue(fire(w, 'GRU_reconstruction.97'))
            self.assertTrue(fire(w, 'GRU_reconstruction.99'))
            self.assertFalse(fire(w, 'GRU_reconstruction.8'))
            choose(w, 'GRU_reconstruction.8')
            effect(w, 'GRU_enter_hitler_path')
            effect(w, 'GRU_load_hitler_focus_tree')
            self.assertEqual(c, before)
            self.assertEqual(w['queue'], queue)

    def test_followup_debug_after_normal_election_preserves_settled_rewards(self):
        for outcome, prepared, tag in product((6, 7), (False, True), ('GRU', 'D03')):
            with self.subTest(outcome=outcome, prepared=prepared, tag=tag):
                w, c = established(tag)
                c['variables'].update(zip(BARS, (100, 100, 0)))
                if outcome == 7: c['variables'][INF[0]] = 81
                if prepared: c['flags'].add('GRU_first_election_prepared')
                c['focuses'].add('GRU_new_german_government')
                self.assertTrue(decision(w, 'GRU_hold_first_election'))
                advance(w, 7)
                eid = f'GRU_reconstruction.{outcome}'
                self.assertEqual(w['opened'], [(tag, eid)])
                self.assertTrue(choose(w, eid))
                self.assertIn('GRU_first_election_held', c['flags'])
                self.assertEqual(c['tree'], 'GRU_red_germany_focus')
                expected = deepcopy(c)
                # The debug preview changes the tree and appoints the new leader.
                # PP, stability, support and popularity retain the .6/.7 result.
                expected['flags'].add('GRU_hitler_path')
                expected.update(tree='GRU_hitler_focus', loaded=c['loaded'] + 1, focuses=set())
                expected.update(leader='GRU_adolf_hitler', characters={'GRU_adolf_hitler'},
                                leader_desc='GRU_adolf_hitler_leader_desc',
                                leader_picture='GFX_portrait_GRU_adolf_hitler',
                                leader_creations=[HITLER_LEADER])
                expected['party_names']['communist'] = 'GRU_hitler_communist_party'
                self.assertTrue(fire(w, 'GRU_reconstruction.97'))
                self.assertTrue(choose(w, 'GRU_reconstruction.97'))
                self.assertEqual(c, expected)
                self.assert_hitler_leads(c)
                c['focuses'].add('GRU_national_revolution')
                before = deepcopy(c)
                self.assertTrue(fire(w, 'GRU_reconstruction.97'))
                self.assertTrue(choose(w, 'GRU_reconstruction.97'))
                effect(w, 'GRU_load_hitler_focus_tree')
                effect(w, 'GRU_enter_hitler_path')
                effect(w, 'GRU_finish_reconstruction')
                for i in (5, 6, 7, 8): self.assertFalse(fire(w, f'GRU_reconstruction.{i}'))
                for i in (6, 7, 8): choose(w, f'GRU_reconstruction.{i}')
                advance(w, 100)
                self.assertFalse(w['queue'])
                self.assertEqual(c, before)

    def test_debug_repairs_leader_on_existing_path_without_reset_or_rewards(self):
        for tag, existing_character, government in product(('GRU', 'D03'), (False, True), ('communist', 'syndicalist')):
            with self.subTest(tag=tag, existing_character=existing_character, government=government):
                w, c = established(tag)
                c['flags'].add('GRU_first_election_scheduled')
                effect(w, 'GRU_finish_reconstruction')
                # Reproduce an existing follow-up save with a random leader:
                # failed runtime recruitment left no Hitler instance. Also cover
                # an existing same-name character that lacks the ruling role.
                c['flags'].add('GRU_hitler_path')
                c.update(tree='GRU_hitler_focus', loaded=2, government=government,
                         leader='Random generated leader', leader_desc='Random leader biography',
                         leader_picture='GFX_random_leader')
                c['focuses'].add('GRU_national_revolution')
                if existing_character: c['characters'].add('GRU_adolf_hitler')
                self.assertEqual(bool(c['characters']), existing_character)
                self.assertFalse(c['leader_creations'])
                expected, queue = deepcopy(c), list(w['queue'])
                expected.update(government='communist', leader='GRU_adolf_hitler',
                                characters={'GRU_adolf_hitler'},
                                leader_desc='GRU_adolf_hitler_leader_desc',
                                leader_picture='GFX_portrait_GRU_adolf_hitler',
                                leader_creations=[HITLER_LEADER])
                expected['party_names']['communist'] = 'GRU_hitler_communist_party'
                if government != 'communist': expected['opaque'].append('set_government_flags')
                self.assertTrue(fire(w, 'GRU_reconstruction.97'))
                self.assertEqual(c, expected)
                self.assertEqual(w['queue'], queue)
                self.assert_hitler_leads(c)
                c['party_names']['communist'] = 'GRU_red_communist_party'
                self.assertTrue(fire(w, 'GRU_reconstruction.97'))
                effect(w, 'GRU_load_hitler_focus_tree')
                effect(w, 'GRU_appoint_hitler_leader')
                self.assertEqual(c, expected)
                self.assertEqual(w['queue'], queue)

    def test_leader_appointment_rejects_ineligible_countries_and_stages(self):
        for state in ('wrong_original', 'unestablished', 'unsettled', 'no_path', 'rebel', 'civil_war'):
            with self.subTest(state=state):
                w, c = established('D03')
                c['flags'].update(('GRU_first_election_held', 'GRU_hitler_path'))
                if state == 'wrong_original': c['original'] = 'GER'
                if state == 'unestablished': c['flags'].discard('GRU_red_germany_established')
                if state == 'unsettled': c['flags'].discard('GRU_first_election_held')
                if state == 'no_path': c['flags'].discard('GRU_hitler_path')
                if state == 'rebel': c['flags'].add('GRU_reconstruction_rebel')
                if state == 'civil_war': c['flags'].add('GRU_civil_war_started')
                before = deepcopy(c)
                effect(w, 'GRU_appoint_hitler_leader')
                self.assertEqual(c, before)

    def test_followup_entry_rejects_wrong_scope_and_inactive_reconstruction(self):
        for original in ('RUS', 'GER', 'AUS'):
            w = world('D03', original=original)
            c = w['countries']['D03']
            # Even copied flags do not make an unrelated dynamic tag eligible.
            c['flags'].update(('GRU_red_germany_established', 'GRU_reconstruction_ongoing', 'GRU_first_election_scheduled', 'GRU_first_election_held'))
            before = deepcopy(c)
            self.assertFalse(fire(w, 'GRU_reconstruction.97'))
            self.assertFalse(fire(w, 'GRU_reconstruction.8'))
            effect(w, 'GRU_enter_hitler_path')
            effect(w, 'GRU_load_hitler_focus_tree')
            self.assertEqual(c, before)
        for state in ('unscheduled', 'already_entered', 'civil_war', 'rebel'):
            w, c = established()
            if state != 'unscheduled': c['flags'].add('GRU_first_election_scheduled')
            if state == 'already_entered': c['flags'].add('GRU_hitler_path')
            if state == 'civil_war': c['flags'].add('GRU_civil_war_started')
            if state == 'rebel': effect(w, 'GRU_setup_reconstruction_rebels')
            before = deepcopy(c)
            effect(w, 'GRU_enter_hitler_path')
            self.assertEqual(c, before)
            if state != 'unscheduled':
                effect(w, 'GRU_load_hitler_focus_tree')
                self.assertEqual(c, before)
            if state in ('civil_war', 'rebel'):
                self.assertFalse(fire(w, 'GRU_reconstruction.97'))
                self.assertFalse(fire(w, 'GRU_reconstruction.8'))

    def test_followup_tree_loader_requires_settlement_and_safe_scope(self):
        w = world()
        c = w['countries']['GRU']
        c['flags'].add('GRU_first_election_held')
        before = deepcopy(c)
        effect(w, 'GRU_load_hitler_focus_tree')
        self.assertEqual(c, before)  # original GRU alone is not an established red Germany
        c['flags'].clear()
        effect(w, 'GRU_establish_red_germany')
        before = deepcopy(c)
        effect(w, 'GRU_load_hitler_focus_tree')
        self.assertEqual(c, before)  # switching trees must not skip settlement
        c['flags'].add('GRU_first_election_scheduled')
        effect(w, 'GRU_finish_reconstruction')
        for flag in ('GRU_reconstruction_rebel', 'GRU_civil_war_started'):
            c['flags'].add(flag)
            before = deepcopy(c)
            effect(w, 'GRU_load_hitler_focus_tree')
            self.assertEqual(c, before, flag)
            c['flags'].discard(flag)
        expected = deepcopy(c)
        expected['flags'].add('GRU_hitler_path')
        expected.update(tree='GRU_hitler_focus', loaded=c['loaded'] + 1, focuses=set())
        expected.update(leader='GRU_adolf_hitler', characters={'GRU_adolf_hitler'},
                        leader_desc='GRU_adolf_hitler_leader_desc',
                        leader_picture='GFX_portrait_GRU_adolf_hitler',
                        leader_creations=[HITLER_LEADER])
        expected['party_names']['communist'] = 'GRU_hitler_communist_party'
        effect(w, 'GRU_load_hitler_focus_tree')
        self.assertEqual(c, expected)

    def test_all_focus_rewards_execute_and_clamp(self):
        for focus in FOCUSES.values():
            w, c = established()
            c['variables'].update({x: 99 for x in BARS})
            execute(focus.one('completion_reward').v, w, 'GRU')
            self.assertTrue(all(0 <= c['variables'][x] <= 100 for x in BARS))

    def test_followup_focus_rewards_execute_without_changing_government_or_leader(self):
        w, c = established()
        for focus in FOLLOWUP_FOCUSES.values():
            execute(focus.one('completion_reward').v, w, 'GRU')
        self.assertEqual(c['pp'], 2025)
        self.assertAlmostEqual(c['stability'], .3)
        self.assertAlmostEqual(c['war_support'], .95)
        self.assertEqual(c['government'], 'communist')
        self.assertEqual(c['leader'], 'KR occupation leader')
        self.assertEqual(c['leader_ideology'], 'marxism_leninism_subtype')
        self.assertTrue({'GRU_revolutionary_chancellor', 'GRU_aristocracy_broken',
                         'GRU_class_enemies_exposed', 'GRU_fuhrer_principle',
                         'GRU_hitler_father', 'GRU_hitler_stalin_pact',
                         'GRU_two_hails', 'GRU_hitler_augustus'} <= c['flags'])

    def test_civil_war_preserves_original_government_for_both_legal_rebels(self):
        for influence, expected in (((100, 100, 0), 'national_populist'), ((0, 100, 100), 'paternal_autocrat')):
            w, c = established()
            c['variables'].update(zip(INF, influence))
            effect(w, 'GRU_check_saboteur_collapse')
            advance(w, 1)
            self.assertEqual(w['countries']['REB']['government'], expected)
            self.assertEqual(c['government'], 'communist')
            # Even a subsequently re-puppeted, peaceful socialist rebel country
            # must not start a second copy of the reconstruction campaign.
            rebel = w['countries']['REB']
            rebel.update(overlord='RUS', government='communist', war=False)
            self.assertFalse(condition(TRIGGERS['GRU_can_become_red_germany'].v, w, 'REB'))


class ContentTests(unittest.TestCase):
    def test_followup_runtime_leader_has_description_and_no_unrequested_traits(self):
        creations = [n for n in walk(EFFECTS['GRU_appoint_hitler_leader'].v) if n.k == 'create_country_leader']
        self.assertEqual(len(creations), 1)
        creation = creations[0]
        self.assertEqual(len(creation.v), len(HITLER_LEADER))
        self.assertEqual({n.k: n.v for n in creation.v}, HITLER_LEADER)
        self.assertEqual(IDEOLOGY_GROUPS[creation.value('ideology')], 'communist')
        guards = [n for n in walk(EFFECTS['GRU_appoint_hitler_leader'].v) if n.k == 'has_country_leader']
        self.assertEqual(len(guards), 2)  # creation guard and existing-save party rename
        for guard in guards:
            self.assertEqual({n.k: n.v for n in guard.v}, {'name': 'GRU_adolf_hitler', 'ruling_only': 'yes'})
        portrait = creation.value('picture')
        sprites = [n for n in walk(load(R / 'interface/GRU_red_germany_portraits.gfx'))
                   if n.k == 'spriteType' and n.value('name').strip('"') == portrait]
        self.assertEqual(len(sprites), 1)
        texture = sprites[0].value('texturefile').strip('"')
        self.assertEqual(texture, 'gfx/leaders/GRU/GRU_adolf_hitler.png')
        png = (R / texture).read_bytes()
        self.assertTrue(png.startswith(b'\x89PNG\r\n\x1a\n'))
        width, height, depth, colour, _, _, _ = struct.unpack('>IIBBBBB', png[16:29])
        self.assertEqual((width, height, depth, colour), (156, 210, 8, 2))  # opaque RGB

    def test_gru_runtime_scripts_do_not_use_history_only_recruitment(self):
        # Inspect every GRU event/effect, including branches no fixture reaches.
        # History-only recruitment must not pass merely because a definition
        # exists in common/characters or a fixture pre-instantiated a character.
        paths = set(IMPORTED_SCRIPTS) | set((R / 'events').glob('GRU_*.txt'))
        for path in paths:
            for n in walk(load(path)):
                self.assertNotEqual(n.k, 'recruit_character', (path.name, n.raw()))

    def test_runtime_model_rejects_recruitment_even_with_existing_character(self):
        for existing in (False, True):
            with self.subTest(existing_character=existing):
                w = world()
                c = w['countries']['GRU']
                if existing: c['characters'].add('GRU_adolf_hitler')
                before = deepcopy(c)
                with self.assertRaisesRegex(AssertionError, 'recruit_character is history-only'):
                    execute(parse('recruit_character = GRU_adolf_hitler'), w, 'GRU')
                self.assertEqual(c, before)

    def test_runtime_creation_uses_effect_fields_without_character_template(self):
        # Keep the model generic: supplied fields, not a name-specific template,
        # determine the runtime leader. No character registry is loaded.
        w = world(government='communist')
        c = w['countries']['GRU']
        self.assertFalse(c['characters'])
        execute(parse('''create_country_leader = {
            name = test_runtime_leader desc = test_runtime_biography
            picture = GFX_test_runtime_portrait ideology = marxism_leninism_subtype
        }'''), w, 'GRU')
        self.assertEqual(c['leader'], 'test_runtime_leader')
        self.assertEqual(c['leader_desc'], 'test_runtime_biography')
        self.assertEqual(c['leader_picture'], 'GFX_test_runtime_portrait')
        self.assertEqual(c['characters'], {'test_runtime_leader'})
        self.assertTrue(condition(parse('has_country_leader = { name = test_runtime_leader ruling_only = yes }'), w, 'GRU'))
        self.assertFalse(condition(parse('has_country_leader = { name = another_leader ruling_only = yes }'), w, 'GRU'))

    def test_imported_scripts_use_supported_comparison_operators(self):
        # Our general parser can tokenize >=, <= and !=, unlike the HOI4 script
        # parser. Do not let its permissiveness hide a file-breaking operator.
        for path in IMPORTED_SCRIPTS:
            for n in walk(load(path)):
                self.assertIn(n.op, (None, '=', '<', '>'), (path.name, n.raw()))

    def test_condition_names_match_engine_documentation(self):
        doc = (GAME / 'documentation/triggers_documentation.md').read_text(encoding='utf-8-sig')
        native_names = set(re.findall(r'^## (\w+)\s*$', doc, re.M))
        self.assertIn('has_political_power', native_names)
        self.assertNotIn('political_power', native_names)
        # Check every option trigger even when no fixture selects that option.
        for path in IMPORTED_SCRIPTS:
            for n in walk(load(path)):
                if n.k in ('trigger', 'limit', 'available', 'visible', 'allowed'):
                    with self.subTest(path=path.name, condition=n.raw()):
                        validate_condition_names(n.v, native_names)
        for n in TRIGGERS.values():
            validate_condition_names(n.v, native_names)
        with self.assertRaisesRegex(AssertionError, 'Unknown engine/scripted trigger'):
            validate_condition_names(parse('political_power > 14'), native_names)

    def test_tree_references_and_branch_reachability(self):
        self.assertFalse(FOCUSES.keys() & FOLLOWUP_FOCUSES.keys())
        for tree, focuses, count in ((TREE, FOCUSES, 59), (FOLLOWUP_TREE, FOLLOWUP_FOCUSES, 42)):
            with self.subTest(tree=tree.value('id')):
                self.assertEqual(len(focuses), count)
                self.assertEqual(len(tree.children('focus')), count)
                self.assertEqual(tree.one('country').value('factor'), '0')
                self.assertEqual(tree.value('default'), 'no')
                self.assertEqual(tree.value('reset_on_civilwar'), 'no')
                self.assertIsNone(tree.one('reset_on_civil_war'))
                positions = [(int(f.value('x')), int(f.value('y'))) for f in focuses.values()]
                self.assertEqual(len(set(positions)), len(positions))
                # KR uses a 96px column step and a 164px name panel: distinct
                # coordinates alone do not prevent neighboring titles overlap.
                for y in {y for _, y in positions}:
                    xs = sorted(x for x, row in positions if row == y)
                    self.assertTrue(all(b - a >= 2 for a, b in zip(xs, xs[1:])), (tree.value('id'), y, xs))
                prereqs = {k: [set(x.v for x in n.v) for n in f.children('prerequisite')] for k, f in focuses.items()}
                mutex = {k: set(x.v for n in f.children('mutually_exclusive') for x in n.v) for k, f in focuses.items()}
                for k in focuses:
                    for refs in [*prereqs[k], mutex[k]]: self.assertFalse(refs - focuses.keys())
                for shortcut in tree.children('shortcut'):
                    self.assertIn(shortcut.value('target'), focuses)
                # Enumerate maximal legal paths at each mutually exclusive
                # choice; requiring both sides of a fork must fail reachability.
                pairs = {tuple(sorted((k, x))) for k in focuses for x in mutex[k]}
                reached = set()
                for choices in product((0, 1), repeat=len(pairs)):
                    excluded = {pair[choice] for pair, choice in zip(sorted(pairs), choices)}
                    done = set()
                    while True:
                        ready = {k for k in focuses if k not in done | excluded and not mutex[k] & done and all(g & done for g in prereqs[k])}
                        if not ready: break
                        done |= ready
                    reached |= done
                self.assertEqual(reached, focuses.keys())

    def test_followup_focus_gameplay_matches_supplied_package(self):
        # Baseline from hongde/common/national_focus/GRU_hitler_focus.txt in the
        # user-supplied 2026-10-07 package. Keep its rewards, costs, AND-prerequisite
        # groups and other gameplay fields; only artwork and coordinates change.
        # Store the signature so regression checks do not require the local ZIP.
        signature = {k: [n.norm() for n in f.v if n.k not in ('icon', 'x', 'y')]
                     for k, f in FOLLOWUP_FOCUSES.items()}
        digest = hashlib.sha256(json.dumps(signature, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        self.assertEqual(digest, '4176c74ae37e55b391f0a98180c9fac1d9cf97f7e2c0f19fe08358ff5be273ac')

    def test_chinese_localization_and_custom_effect_references(self):
        p = R / 'localisation/simp_chinese/GRU_red_germany_l_simp_chinese.yml'
        b = p.read_bytes()
        self.assertTrue(b.startswith(b'\xef\xbb\xbf'))
        s = b.decode('utf-8-sig')
        entries = re.findall(r'^\s+([\w.]+):(?:\d+)?\s+"(.*)"\s*$', s, re.M)
        loc = dict(entries)
        self.assertEqual(len(loc), len(entries))
        self.assertNotIn('\ufffd', s)
        for focus in FOCUSES.keys() | FOLLOWUP_FOCUSES.keys(): self.assertIn(focus, loc); self.assertIn(focus + '_desc', loc)
        for decision_id in DECISIONS: self.assertIn(decision_id, loc); self.assertIn(decision_id + '_desc', loc)
        def walk(nodes):
            for n in nodes:
                if n.k in ('custom_effect_tooltip', 'tooltip', 'name', 'title', 'desc') and isinstance(n.v, str) and n.v.startswith('GRU_'):
                    self.assertIn(n.v, loc)
                if isinstance(n.v, list): walk(n.v)
        for f in [*(R / 'common').rglob('GRU_*.txt'), R / 'events/GRU_reconstruction_events.txt']:
            walk(load(f))
        self.assertIn('GRU_reconstruction_work_desc', loc)
        self.assertNotIn('德国社会主义党执政', s)

    def test_native_spirit_and_cosmetic_flag_assets(self):
        idea = load(R / 'common/ideas/GRU_red_germany_ideas.txt')[0].one('country').one('GRU_collapsed_germany')
        self.assertEqual(idea.value('picture'), 'generic_crippled_industry')
        expected = {'consumer_goods_factor': .2, 'industrial_capacity_factory': -.15,
                    'production_speed_buildings_factor': -.15, 'stability_factor': -.2,
                    'war_support_factor': -.15, 'research_speed_factor': -.1,
                    'recruitable_population_factor': -.05}
        self.assertEqual({n.k: float(n.v) for n in idea.one('modifier').v}, expected)
        for folder in ('', 'medium', 'small'):
            self.assertEqual((R / 'gfx/flags' / folder / 'GRU_red_germany.tga').read_bytes(),
                             (KR / 'gfx/flags' / folder / 'GRU_radical_socialist.tga').read_bytes())

    def test_all_imported_graphics_resolve_in_game_or_kr(self):
        game = Path(os.environ.get('HOI4_GAME_ROOT', R.parents[3] / 'common/Hearts of Iron IV'))
        sprites = set()
        for root in (R, KR, game):
            for f in (root / 'interface').rglob('*.gfx'):
                sprites.update(re.findall(r'\bname\s*=\s*"?(GFX_[\w.-]+)', f.read_text(encoding='utf-8-sig', errors='replace')))
        required = {'GFX_idea_generic_crippled_industry'}
        for f in [*(R / 'common').rglob('GRU_*.txt'), R / 'events/GRU_reconstruction_events.txt']:
            required.update(re.findall(r'\bGFX_\w+', f.read_text(encoding='utf-8-sig')))
        self.assertFalse(required - sprites, required - sprites)

    def test_upstream_namespace_and_top_level_event_ids(self):
        # New identifiers must not replace KR focuses or scripted helpers. Event
        # calls are references; count only top-level event declarations locally.
        own_events = [n.value('id') for n in load(R / 'events/GRU_reconstruction_events.txt') if n.k == 'country_event']
        self.assertEqual(len(set(own_events)), len(own_events))
        additions = set(FOCUSES) | set(FOLLOWUP_FOCUSES) | {k for k in EFFECTS if k.startswith('GRU_')} | set(TRIGGERS)
        pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted(additions))) + r')\b')
        collisions = []
        for folder in ('common/national_focus', 'common/scripted_effects', 'common/scripted_triggers', 'events'):
            for f in (KR / folder).glob('*.txt'):
                match = pattern.search(f.read_text(encoding='utf-8-sig', errors='replace'))
                if match: collisions.append((str(f.relative_to(KR)), match[0]))
        self.assertFalse(collisions, collisions)


if __name__ == '__main__':
    unittest.main(verbosity=2)
