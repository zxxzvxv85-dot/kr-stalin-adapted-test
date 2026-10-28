"""Read-only inventory of research cards reachable from the 102-focus military branch.

Counts normal-mode reward definitions, not preview blocks or easy-mode alternatives.
Other conditional rewards are retained with their conditions; this is an inventory,
not a claim that mutually exclusive branches can all be completed in one campaign.
"""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from hoi4_politics_blocks import load

ROOT = Path(__file__).resolve().parents[1]
KR = ROOT.parent / '1521695605'


def inventory():
    foci = {n.value('id'): n for t in load(ROOT / 'common/national_focus/RUS focus (Russia).txt')
            for n in t.children('focus')}
    ids = {'RUS_fr_post_revolutionary_armed_forces'}
    while True:
        before = len(ids)
        ids.update(k for k, n in foci.items() if n.value('relative_position_id') in ids)
        if before == len(ids):
            break
    effects = {}
    for base in (KR, ROOT):
        for p in sorted((base / 'common/scripted_effects').glob('*.txt')):
            effects.update({n.k: n for n in load(p)})
    loc = {}
    for base in (KR, ROOT.parent / '2946487287', ROOT):
        for p in sorted((base / 'localisation/simp_chinese').rglob('*.yml')):
            loc.update(re.findall(r'^\s*(\S+):\d*\s*"(.*)"\s*$', p.read_text(encoding='utf-8-sig'), re.M))
    rows = []

    def visit(nodes, focus, conditions=(), stack=()):
        easy_else = False
        for n in nodes:
            if n.k == 'if':
                easy_else = 'has_country_flag = RUS_easy_mode_enabled' in n.one('limit').raw()
                if easy_else:
                    continue
            elif n.k == 'else' and easy_else:
                easy_else = False
                visit(n.v, focus, conditions, stack)
                continue
            else:
                easy_else = False
            if n.k in ('effect_tooltip', 'limit', 'custom_effect_tooltip', 'log'):
                continue
            if n.k in ('add_tech_bonus', 'add_doctrine_cost_reduction'):
                title = loc.get(focus, focus)
                if title == '[RUS_bomber_clique_name]':
                    title = loc['RUS_bomber_clique_normal'] + ' / ' + loc['RUS_bomber_clique_szrs']
                rows.append(dict(kind=n.k, focus=focus, title=title,
                                 name=n.value('name'), uses=int(n.value('uses', '1')),
                                 bonus=float(n.value('bonus', n.value('cost_reduction', '0'))) * 100,
                                 ahead=float(n.value('ahead_reduction', '0')),
                                 targets=' / '.join(x.v for x in n.v if x.k in ('category', 'technology')),
                                 conditions=' AND '.join(conditions), via=' > '.join(stack)))
            elif n.k in effects and n.v == 'yes':
                assert n.k not in stack, ('Recursive effect', stack, n.k)
                visit(effects[n.k].v, focus, conditions, (*stack, n.k))
            elif isinstance(n.v, list):
                cond = conditions
                if n.k in ('if', 'else_if'):
                    cond += (re.sub(r'\s+', ' ', n.one('limit').inner()).strip(),)
                elif n.k == 'else':
                    cond += ('ELSE (preceding condition not met)',)
                visit(n.v, focus, cond, stack)

    for k, n in foci.items():
        if k in ids and n.one('completion_reward'):
            visit(n.one('completion_reward').v, k)
    return ids, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, help='Explicit output path; default only prints JSON')
    args = parser.parse_args()
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    ids, rows = inventory()
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    counts = Counter()
    for row in rows:
        counts[f"{row['kind']} / {row['bonus']:g}% / ahead {row['ahead']:g}"] += row['uses']
    print(json.dumps(dict(focus_count=len(ids), reward_entries=len(rows),
                         reward_foci=len({r['focus'] for r in rows}),
                         tech_uses=sum(r['uses'] for r in rows if r['kind'] == 'add_tech_bonus'),
                         doctrine_uses=sum(r['uses'] for r in rows if r['kind'] == 'add_doctrine_cost_reduction'),
                         by_bonus=dict(counts), rows=rows),
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
