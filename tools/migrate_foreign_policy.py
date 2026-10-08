"""Retire the legacy socialist diplomacy tree and anchor the implemented tree.

Default is a dry run. Existing implemented rewards are preserved. This migration
uses parsed field spans so spirit names, sprites and localisation keys are not
mistaken for focus references.
"""
from pathlib import Path
import argparse
import difflib
from hoi4_politics_blocks import R, load, parse

ROOT_FOCUS = 'RUS_future_foreign_001'
OLD_TO_NEW = {
    'RUS_self_determination': '001',
    'RUS_eastern_vanguard': '004',
    'RUS_defencism': '008',
    'RUS_each_according_ability': '047',
    'RUS_pool_armour_innovation': '032',
    'RUS_american_revolution': None,
    'RUS_comrades_abroad': '032',
    'RUS_liberate_central_asia': None,
    'RUS_prepare_march_of_liberation': '051',
    'RUS_anti_capitalist_warfare': None,
    'RUS_turn_east': None,
    'RUS_turn_south': None,
    'RUS_rival_west': '043',
    'RUS_abolish_war': '028',
    'RUS_heir_of_world_revolution': '064',
    'RUS_socrus_spies': None,
    'RUS_vision_for_union': '005',
    'RUS_develop_poorer_republics': None,
    'RUS_rebuilding_liberated_lands': None,
    'RUS_union_of_peoples': None,
    'RUS_expansion_of_union': '043',
    'RUS_increased_devolution': None,
    'RUS_peoples_union': None,
    'RUS_centralise_authority': '013',
    'RUS_coordinate_development': '045',
    'RUS_what_a_childish_fantasy': '014',
    'RUS_found_communist_international': '012',
    'RUS_help_allys_industry': '042',
    'RUS_found_sov_union': '045',
}


def walk(nodes, ancestors=()):
    for n in nodes:
        yield n, ancestors
        if isinstance(n.v, list):
            yield from walk(n.v, (*ancestors, n))


def apply_spans(text, edits):
    edits = sorted(set(edits), reverse=True)
    previous = len(text)
    for start, end, replacement in edits:
        if end > previous:
            raise ValueError('Overlapping edits')
        text = text[:start] + replacement + text[end:]
        previous = start
    parse(text)
    return text


def retire_nodes(text):
    nodes = parse(text)
    edits = []
    for n, ancestors in walk(nodes):
        if n.k == 'focus' and isinstance(n.v, list) and n.value('id') in OLD_TO_NEW:
            edits.append((n.a, n.b, ''))
        if n.k == 'complete_national_focus':
            target = n.value('focus') if isinstance(n.v, list) else n.v
            if target in OLD_TO_NEW:
                enclosing = next((p for p in reversed(ancestors) if p.k == 'if'), None)
                if enclosing is None:
                    raise ValueError('Review unguarded legacy completion: ' + target)
                edits.append((enclosing.a, enclosing.b, ''))
    # A removed focus owns all nested fields, so discard edits inside it.
    outer = [e for e in edits if not any(o[0] < e[0] and e[1] <= o[1] for o in edits)]
    return apply_spans(text, outer)


def rewrite_references(text, path):
    edits = []
    for n, ancestors in walk(parse(text)):
        if n.k == 'has_completed_focus' and n.v in OLD_TO_NEW:
            successor = OLD_TO_NEW[n.v]
            # Overseas Comrades' old military-disorganisation reward is retired,
            # rather than silently adding it to the new military-exchange focus.
            if path.name == 'RUS_fr_military_reform_effects.txt' and n.v == 'RUS_comrades_abroad':
                successor = None
            # The China adviser mission belongs to the new China military branch.
            if path.name == 'RUS decisions (Russia).txt' and n.v == 'RUS_comrades_abroad':
                successor = '060'
            replacement = ('has_completed_focus = RUS_future_foreign_' + successor
                           if successor else 'always = no')
            edits.append((n.a, n.b, replacement))
        elif n.k == 'focus' and isinstance(n.v, str) and n.v in OLD_TO_NEW:
            if any(p.k == 'uncomplete_national_focus' for p in ancestors):
                # The union/faction switches cannot uncomplete a removed node;
                # modern manual focuses retain their own completion state.
                parent = next(p for p in reversed(ancestors) if p.k == 'uncomplete_national_focus')
                edits.append((parent.a, parent.b, ''))
            else:
                raise ValueError('Review legacy graph reference: ' + n.raw())
        elif n.k == 'relative_position_id' and n.v in OLD_TO_NEW:
            raise ValueError('Unretired descendant: ' + n.raw())
    outer = [e for e in edits if not any(o[0] < e[0] and e[1] <= o[1] for o in edits)]
    return apply_spans(text, outer)


def anchor_layout(text):
    focuses = [n for n in parse(text) if n.k == 'shared_focus']
    root = next(n for n in focuses if n.value('id') == ROOT_FOCUS)
    if root.value('relative_position_id') == 'RUS_russian_congress':
        return text
    ox, oy = int(root.value('x')), int(root.value('y'))
    edits = []
    for n in focuses:
        x, y = int(n.value('x')), int(n.value('y'))
        if n is root:
            location = ('relative_position_id = RUS_russian_congress\n\tx = 20\n\ty = -2\n'
                        '\toffset = { x = -10 y = 1 trigger = { RUS_PLSR = yes } }')
        else:
            location = f'relative_position_id = {ROOT_FOCUS}\n\tx = {x - ox}\n\ty = {y - oy}'
        edits.append((n.one('x').a, n.one('y').b, location))
    return apply_spans(text, edits)


def middle_east_gate(text):
    # New Iran/Afghanistan focuses explicitly activate these targets. The India
    # focus does not unlock Middle East wars, nor does either focus unlock Turkey.
    gate = ('OR = {\n'
            '\t\t\t\tAND = { has_completed_focus = RUS_future_foreign_052 FROM = { tag = PER } }\n'
            '\t\t\t\tAND = { has_completed_focus = RUS_future_foreign_053 FROM = { tag = AFG } }\n'
            '\t\t\t}')
    for n, _ in walk(parse(text)):
        if n.k == 'RUS_Socialist_Attack_Middle_East' and isinstance(n.v, list):
            field = n.one('target_root_trigger')
            replacement = 'target_root_trigger = {\n\t\t\t' + gate + '\n\t\t}'
            return apply_spans(text, [(field.a, field.b, replacement)])
    return text


def render_outputs(root=R):
    outputs = {}
    for directory in ('common', 'events'):
        for path in sorted((root / directory).rglob('*.txt')):
            text = path.read_text(encoding='utf-8-sig')
            if not any(k in text for k in OLD_TO_NEW) and path.name not in ('00_RUS_future_foreign_policy_skeleton.txt', 'RUS decisions (Russia).txt'):
                continue
            updated = retire_nodes(text)
            updated = rewrite_references(updated, path)
            if path.name == 'RUS decisions (Russia).txt':
                updated = middle_east_gate(updated)
            if path.name == '00_RUS_future_foreign_policy_skeleton.txt':
                updated = anchor_layout(updated)
            if updated != text:
                outputs[path.relative_to(root).as_posix()] = updated
    return outputs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    outputs = render_outputs()
    for rel, text in outputs.items():
        print(('UPDATE ' if args.write else 'PENDING ') + rel)
        if args.write:
            path = R / rel
            raw = path.read_bytes()
            # Preserve each file's current encoding and newline convention.
            bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
            original = raw.decode('utf-8-sig').splitlines(keepends=True)
            updated = text.splitlines(keepends=True)
            before = [line.rstrip('\r\n') for line in original]
            after = [line.rstrip('\r\n') for line in updated]
            newline = '\r\n' if raw.count(b'\r\n') > raw.count(b'\n') / 2 else '\n'
            result = []
            for op, a, b, c, d in difflib.SequenceMatcher(a=before, b=after, autojunk=False).get_opcodes():
                if op == 'equal':
                    result.extend(original[a:b])
                else:
                    result.extend(line + newline for line in after[c:d])
            path.write_bytes(bom + ''.join(result).encode('utf-8'))
    if args.check and outputs:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
