"""Keep Europe's overview navigation in the fixed header, outside map clipping.

Native references: KR scripted GUI button events are owned by the GUI whose
window contains the button. Only the two named navigation nodes are moved.
Default mode is read-only; this helper is also used by the test GUI generator.
"""
from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parents[1]
GUI = 'interface/RUS_europe_intervention.gui'
SCRIPT = 'common/scripted_guis/RUS_europe_intervention.txt'
BUTTON = 'RUS_europe_intervention_overview_button'


def replace_one(pattern, replacement, text, flags=0):
    result, count = re.subn(pattern, replacement, text, flags=flags)
    if count != 1:
        raise ValueError(f'Expected one navigation node, got {count}: {pattern}')
    return result


def repair_gui(text):
    pattern = r'\n\n\t\tbuttonType = \{\n\t\t\tname = "'+BUTTON+r'"[^\n]*(?:\n.*?)*?\n\t\t\}'
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise ValueError('Expected exactly one existing overview button')
    button = matches[0].group()
    button = replace_one(r'position = \{ x = \d+ y = \d+ \}',
                         'position = { x = 627 y = 6 }', button)
    text = text[:matches[0].start()]+text[matches[0].end():]
    start = text.index('name = "RUS_europe_intervention_header_window"')
    end = text.index('\n\t}', start)
    header = text[start:end]
    header = replace_one(r'(name = "RUS_europe_intervention_header_title".*?maxWidth = )\d+',
                         r'\g<1>525', header, re.S)
    return text[:start]+header+button+text[end:]


def repair_scripted_gui(text):
    # Removing before inserting makes this transformation idempotent.
    for suffix in ('_click_enabled', '_click'):
        text = replace_one(r'\n[ \t]*'+BUTTON+suffix+r' = \{[^\n]*\}', '', text)
    start = text.index('\tRUS_europe_intervention_header_gui = {')
    end = text.index('\n\t}', start)
    header = text[start:end]
    header = re.sub(r'\n\t\t(?:triggers|effects) = \{\n\t\t\}', '', header)
    header += ('\n\t\ttriggers = {\n\t\t\t'+BUTTON+'_click_enabled = { has_country_flag = RUS_europe_intervention_filter_active }\n\t\t}'
               '\n\t\teffects = {\n\t\t\t'+BUTTON+'_click = { RUS_clear_europe_intervention_selection = yes }\n\t\t}')
    return text[:start]+header+text[end:]


def render(root=ROOT):
    return {GUI: repair_gui((root/GUI).read_text(encoding='utf-8-sig')),
            SCRIPT: repair_scripted_gui((root/SCRIPT).read_text(encoding='utf-8-sig'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--write', action='store_true')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    outputs = render(args.root)
    different = []
    for path, text in outputs.items():
        target = args.root/path
        if target.read_text(encoding='utf-8-sig') != text:
            different.append(path)
            if args.write:
                target.write_bytes(text.encode('utf-8'))
    print(('Updated' if args.write else 'Checked')+f' overview navigation: {len(different)} differences')
    raise SystemExit(0 if args.write or not different else 1)


if __name__ == '__main__':
    main()
