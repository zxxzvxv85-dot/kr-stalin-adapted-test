from hoi4_politics_blocks import R, load

effect = load(R/'common/scripted_effects/RUS_gendarme_waiting_effects.txt')[0]
def check(node, completed, tech):
    for n in node.v:
        if n.k == 'has_completed_focus' and not completed: return False
        if n.k == 'has_tech' and not tech: return False
        if n.k == 'NOT' and check(n, completed, tech): return False
    return True
def run(node, state):
    for n in node.v:
        if n.k == 'limit': continue
        if n.k == 'if':
            if check(n.one('limit'), state['completed'], state['tech']): run(n, state)
        elif n.k == 'set_variable': state[n.v[0].k] = float(n.v[0].v)
        elif n.k == 'set_technology':
            state['tech'] = True
            state['grants'] += 1
        else: raise AssertionError(n.k)
for completed in [False, True]:
    state = dict(completed=completed, tech=False, speed=0, grants=0)
    for _ in range(100): run(effect, state)
    assert state['RUS_gendarme_waiting_attack_speed'] == (0.1 if completed else 0)
    assert state['RUS_gendarme_waiting_river_speed'] == (-0.25 if completed else 0)
    assert state['grants'] == int(completed)
tech = load(R/'common/technologies/RUS_gendarme_waiting_terrain.txt')[0].v[0]
army = tech.one('category_army')
assert army.one('river') is None
assert army.one('fort').value('attack') == '0.10'
modifier = load(R/'common/dynamic_modifiers/RUS_future_foreign_policy_dynamic_modifiers.txt')[0]
assert modifier.value('army_attack_speed_factor') == 'RUS_gendarme_waiting_attack_speed'
assert modifier.value('river_crossing_factor') == 'RUS_gendarme_waiting_river_speed'
for lang in ['simp_chinese', 'english', 'russian']:
    assert (R/f'localisation/{lang}/RUS_gendarme_waiting_l_{lang}.yml').read_bytes().startswith(b'\xef\xbb\xbf')
print('PASS: no bonus before focus; completed focus grants 10% speed and terrain technology once across 100 refreshes; river/fort values and localisation BOM verified.')
