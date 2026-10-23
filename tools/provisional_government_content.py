"""Authored six-focus content and an idempotent revolution hook; no import writes."""
from pathlib import Path
import json

from hoi4_politics_blocks import parse

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / 'tools/design/RUS_provisional_government_20261023.json'


def content():
    return json.loads(SPEC_PATH.read_text(encoding='utf-8'))


def patch_revolution_event(raw):
    event = parse(raw)[0]
    assert event.value('id') == 'russia_events.924'
    option = event.one('option')
    assert len(event.children('option')) == 1
    # Replace only this module's two appended fields, preserving every original
    # event field and its order. Regeneration also normalizes our own indentation.
    owned = [n for n in option.v if
             (n.k == 'custom_effect_tooltip' and n.v == 'RUS_provisional_revolution_context_tt') or
             (n.k == 'hidden_effect' and n.one('RUS_opening_finish_phase'))]
    for node in sorted(owned, key=lambda n:n.a, reverse=True):
        start = raw.rfind('\n', 0, node.a) + 1
        end = raw.find('\n', node.b)
        raw = raw[:start] + raw[end+1:]
    option = parse(raw)[0].one('option')
    # set_politics above can synchronously hand the opening tree back. Explicitly
    # finish that existing handoff before completing a focus in Russia_Focus.
    extra = '\n'.join([
        '\t\tcustom_effect_tooltip = RUS_provisional_revolution_context_tt',
        '\t\thidden_effect = {',
        '\t\t\tRUS_opening_finish_phase = yes',
        '\t\t\tif = {',
        '\t\t\t\tlimit = { NOT = { has_completed_focus = RUS_future_domestic_154 } }',
        '\t\t\t\tcomplete_national_focus = RUS_future_domestic_154',
        '\t\t\t}',
        '\t\t}',
        '',
    ])
    closing_line = raw.rfind('\n', 0, option.ib) + 1
    return raw[:closing_line].rstrip() + '\n' + extra + '\t' + raw[option.ib:]


def localisation_outputs():
    spec = content()
    tips = {
        'simp_chinese': {
            'RUS_provisional_revolution_context_tt': spec['event']['tooltip'],
            'RUS_provisional_revolution_event_only_tt': '由“雾月革命”事件完成。',
            'RUS_provisional_pending_event_only_tt': '该国策将由后续剧情事件完成。',
        },
        'english': {
            'RUS_provisional_revolution_context_tt': 'The revolutionaries hold the capital but cannot yet govern the whole country. A new Congress of Soviets is urgently needed...',
            'RUS_provisional_revolution_event_only_tt': 'Completed by the revolutionary seizure of power event.',
            'RUS_provisional_pending_event_only_tt': 'This focus will be completed by a future story event.',
        },
        'russian': {
            'RUS_provisional_revolution_context_tt': 'Революционеры заняли столицу, но ещё не способны управлять всей страной. Необходимо срочно созвать новый съезд Советов...',
            'RUS_provisional_revolution_event_only_tt': 'Завершается событием о переходе власти к революционерам.',
            'RUS_provisional_pending_event_only_tt': 'Этот фокус будет завершён будущим сюжетным событием.',
        },
    }
    result = {}
    for lang, data in tips.items():
        if lang == 'simp_chinese':
            data.update({
                'russia_events.924.t': spec['event']['title'],
                'russia_events.924.d': spec['event']['description'],
                'russia_events.924.a': spec['event']['option'],
            })
        rows = ['l_' + lang + ':']
        rows += [' ' + key + ':0 ' + json.dumps(value, ensure_ascii=False) for key, value in data.items()]
        result[Path(f'localisation/replace/zzzz_RUS_provisional_government_l_{lang}.yml')] = ('\n'.join(rows) + '\n').encode('utf-8-sig')
    return result
