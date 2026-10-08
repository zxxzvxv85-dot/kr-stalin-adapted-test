"""Read-only retirement checks against the approved pre-move focus contents.

The frozen baseline preserves gameplay fields, not the new implementation.
Actual engine layout and old-save behaviour still require in-game inspection.
"""
import hashlib
import json
from hoi4_politics_blocks import R, load, parse
from migrate_foreign_policy import OLD_TO_NEW, walk, render_outputs


def content(nodes):
    return [[n.k, n.op, content(n.v) if isinstance(n.v, list) else n.v]
            for n in nodes if n.k not in
            ('x', 'y', 'relative_position_id', 'offset', 'uncomplete_national_focus')]


baseline = json.loads((R / 'tools/test_support/foreign_policy_baseline.json').read_text(encoding='utf-8'))['focuses']
focuses = {n.value('id'): n for n in load(R / 'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt') if n.k == 'shared_focus'}
assert focuses.keys() == baseline.keys()
for id, n in focuses.items():
    digest = hashlib.sha256(json.dumps(content(n.v), ensure_ascii=False).encode()).hexdigest()
    assert digest == baseline[id]['content_sha256'], 'Gameplay fields changed: ' + id
    if id == 'RUS_future_foreign_001':
        assert (n.value('relative_position_id'), n.value('x'), n.value('y')) == ('RUS_russian_congress', '20', '-2')
        offset = n.one('offset')
        assert (offset.value('x'), offset.value('y'), offset.one('trigger').value('RUS_PLSR')) == ('-10', '1', 'yes')
    else:
        assert n.value('relative_position_id') == 'RUS_future_foreign_001'
        assert (int(n.value('x')), int(n.value('y'))) == (baseline[id]['x'], baseline[id]['y'])

for folder in ('common', 'events'):
    for path in (R / folder).rglob('*.txt'):
        text = path.read_text(encoding='utf-8-sig')
        if not any(k in text for k in OLD_TO_NEW):
            continue
        for n, _ in walk(parse(text)):
            assert not (n.k == 'focus' and isinstance(n.v, list) and n.value('id') in OLD_TO_NEW), path
            assert not (n.k in ('focus', 'has_completed_focus', 'relative_position_id', 'complete_national_focus') and isinstance(n.v, str) and n.v in OLD_TO_NEW), (path, n.raw())
            assert not (n.k == 'complete_national_focus' and isinstance(n.v, list) and n.value('focus') in OLD_TO_NEW), path

decisions = {n.k: n for n, _ in walk(load(R / 'common/decisions/RUS decisions (Russia).txt')) if n.k in ('RUS_Socialist_Attack_Middle_East', 'RUS_Socialist_Attack_Far_East')}
def check(nodes, completed, target):
    def one(n):
        if n.k in ('AND', 'FROM'): return check(n.v, completed, target)
        if n.k == 'OR': return any(one(x) for x in n.v)
        if n.k == 'has_completed_focus': return n.v in completed
        if n.k == 'tag': return target == n.v
        if n.k == 'always': return n.v == 'yes'
        raise AssertionError(n.raw())
    return all(one(n) for n in nodes)

cases = 0
for done in (set(), {'RUS_future_foreign_038'}, {'RUS_future_foreign_052'}, {'RUS_future_foreign_053'}, {'RUS_future_foreign_052', 'RUS_future_foreign_053'}):
    for target in ('PER', 'AFG', 'TUR'):
        actual = check(decisions['RUS_Socialist_Attack_Middle_East'].one('target_root_trigger').v, done, target)
        expected = (target == 'PER' and 'RUS_future_foreign_052' in done) or (target == 'AFG' and 'RUS_future_foreign_053' in done)
        assert actual == expected, (done, target)
        cases += 1
for done in (set(), {'RUS_future_foreign_042'}):
    assert check(decisions['RUS_Socialist_Attack_Far_East'].one('target_root_trigger').v, done, 'JAP') == bool(done)
    cases += 1
assert not render_outputs(), 'Migration is not idempotent'
print(f'PASS: {len(focuses)} focus contents/layouts, 29 retired IDs and auto completions; {cases} target eligibility cases. Not an engine test.')
