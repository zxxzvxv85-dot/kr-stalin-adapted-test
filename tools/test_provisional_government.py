"""Focused checks for the approved six-focus effects and revolution handoff."""
from pathlib import Path
import hashlib
import json
import re

from hoi4_politics_blocks import load, parse
from provisional_government_content import content, patch_revolution_event, localisation_outputs

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'RUS_future_domestic_'


def walk(nodes):
    for node in nodes:
        yield node
        if isinstance(node.v, list):
            yield from walk(node.v)


def main():
    spec = content()
    assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest() == spec['source_sha256']
    focuses = {n.value('id'): n for n in load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt')}
    expected = {
        '154': ('0', ''),
        '133': ('1', 'add_political_power = -25\nadd_stability = 0.1\nset_temp_variable = { RUS_influence_cost_change_var = 20 }\nRUS_decrease_german_economic_influence_cost = yes\ncustom_effect_tooltip = RUS_socrus_reduce_influence_decisions'),
        '136': ('1', 'add_command_power = 75\nadd_political_power = -10\ncountry_event = russia_socialist_events.100\nRUS_abolish_hosts = yes\nadd_popularity = { ideology = national_populist popularity = -0.05 }\nadd_popularity = { ideology = paternal_autocrat popularity = -0.1 }'),
        '138': ('0', 'add_political_power = 10'),
        '140': ('5', ''),
        '142': ('0', 'add_political_power = 10'),
    }
    for suffix, (cost, rewards) in expected.items():
        node = focuses[PREFIX+suffix]
        assert node.value('cost') == cost
        assert [n.norm() for n in node.one('completion_reward').v] == [n.norm() for n in parse(rewards)]
        assert node.one('bypass') is None and node.one('select_effect') is None
    assert len([n for n in focuses.values() if n.one('available').one('hidden_trigger')]) == 3
    assert spec['focuses']['138']['name'] == '工人政党的联合'
    effects = {n.k:n for n in load(ROOT/'common/scripted_effects/RUS effects (Russia).txt')}
    abolition = effects['RUS_abolish_hosts']
    assert abolition.value('custom_effect_tooltip') == 'RUS_abolish_hosts_effect_tt'
    removal = abolition.one('hidden_effect').one('delete_unit_template_and_units')
    assert removal.value('division_template') == '"Kazachya diviziya"' and removal.value('disband') == 'yes'
    discount = effects['RUS_decrease_german_economic_influence_cost']
    reductions = discount.children('subtract_from_variable')
    assert {n.v[0].k for n in reductions} == {'RUS_influence_cost_low','RUS_influence_cost_normal','RUS_influence_cost_increased'}
    for reduction in reductions:
        value = reduction.v[0]
        assert value.value('value') == 'RUS_influence_cost_change_var'
        assert value.one('clamp').value('min') == '0'
        assert value.one('clamp').value('max') == value.k


    events = {n.value('id'): n for n in load(ROOT/'events/RUS events (Russia).txt') if n.value('id')}
    assert 'russia_socialist_events.100' in events
    event = events['russia_events.924']
    option = event.one('option')
    assert len(event.children('option')) == 1
    assert option.value('custom_effect_tooltip') == 'RUS_provisional_revolution_context_tt'
    # Preserve the revolution's existing gameplay. The new prose does not remove
    # government transition, costs, leader death or the next day's event.
    assert option.value('add_stability') == '-0.1' and option.value('add_war_support') == '-0.15'
    assert option.value('kill_country_leader') == 'yes'
    assert option.one('set_politics').value('ruling_party') == 'radical_socialist'
    assert option.value('activate_advisor') == 'RUS_boris_kamkov_sic'
    assert option.value('set_country_flag') == 'RUS_savinkov_socialist_uprising'
    assert any(n.k=='country_event' and isinstance(n.v,list) and n.value('id')=='russia_events.925'
               and n.value('days')=='1' for n in walk(option.v))
    hook = next(n for n in option.children('hidden_effect') if n.one('RUS_opening_finish_phase'))
    assert [n.k for n in hook.v] == ['RUS_opening_finish_phase','if']
    gate = hook.one('if')
    assert gate.one('limit').one('NOT').value('has_completed_focus') == PREFIX+'154'
    assert gate.value('complete_national_focus') == PREFIX+'154'
    assert option.one('set_politics').a < hook.a
    assert not any(n.k=='add_political_power' for n in walk(hook.v))
    assert patch_revolution_event(event.raw()) == event.raw(), 'Generator must not append a second hook'
    # The two future story events are deliberately not wired to existing events.
    completion_sites = {suffix:[] for suffix in ['154','138','142']}
    for folder in ['events','common/scripted_effects','common/on_actions','common/decisions']:
        for path in (ROOT/folder).rglob('*.txt'):
            for n in walk(load(path)):
                if n.k=='complete_national_focus' and isinstance(n.v,str) and n.v in {PREFIX+s for s in completion_sites}:
                    completion_sites[n.v.removeprefix(PREFIX)].append(str(path.relative_to(ROOT)))
    assert len(completion_sites['154']) == 1
    assert completion_sites['138'] == completion_sites['142'] == []
    # Native completion grants the focus's own rewards; no parallel event reward
    # is added. The root has no reward and the guarded hook is safe to replay.
    completed=set(); popups=[]
    for _ in range(3):
        if gate.one('limit').one('NOT').value('has_completed_focus') not in completed:
            completed.add(gate.value('complete_national_focus')); popups.append(gate.value('complete_national_focus'))
    assert popups == [PREFIX+'154'] and focuses[PREFIX+'154'].one('completion_reward').v == []

    path=ROOT/'localisation/simp_chinese/RUS_future_domestic_l_simp_chinese.yml'
    raw=path.read_bytes(); assert raw.startswith(b'\xef\xbb\xbf')
    values={k:json.loads(v) for k,v in re.findall(r'^\s+([^ :]+):0 (".*")$',raw.decode('utf-8-sig'),re.M)}
    assert {key for key,value in values.items() if key.endswith('_desc') and value} == {PREFIX+s+'_desc' for s in expected}
    for suffix in expected:
        assert values[PREFIX+suffix] == spec['focuses'][suffix]['name']
        assert values[PREFIX+suffix+'_desc'] == spec['focuses'][suffix]['description']
    for relative,data in localisation_outputs().items():
        actual=(ROOT/relative).read_bytes(); assert actual == data and actual.startswith(b'\xef\xbb\xbf')
        keys=re.findall(r'^\s+([^ :]+):0 ',actual.decode('utf-8-sig'),re.M)
        assert len(keys)==len(set(keys))
    assert '\n\n' in spec['event']['description'] and '[GetMonth]' not in spec['event']['title']
    print('PASS: six approved durations/rewards/descriptions; only three manual focuses; revolution gameplay retained; tree handoff before guarded completion; pending story focuses unbound; localisation/BOM and source hash.')


if __name__ == '__main__':
    main()
