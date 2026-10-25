"""Source-owned seven-day flavour event and native-size photograph; no import writes."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'tools/design/RUS_football_20261025.json'
EVENT = Path('events/RUS_football_events.txt')
GFX = Path('interface/RUS_football_event.gfx')


def content():
    return json.loads(SPEC.read_text(encoding='utf-8'))


def focus_reward():
    """Append to the existing preview focus without opening it or changing its cost."""
    return ['hidden_effect = {',
            '\tif = {',
            '\t\tlimit = { tag = RUS NOT = { has_country_flag = RUS_football_scheduled } }',
            '\t\tset_country_flag = RUS_football_scheduled',
            '\t\tcountry_event = { id = RUS_football.0 days = 7 }',
            '\t}', '}']


def outputs():
    spec = content()
    assert spec['delay_days'] == 7 and spec['focus'] == 'RUS_future_domestic_151'
    eligible = ('tag = RUS has_completed_focus = RUS_future_domestic_151 '
                'has_country_flag = RUS_football_scheduled '
                'NOT = { has_country_flag = RUS_football_done }')
    # Explicit event delivery may bypass trigger filters; recheck in executable
    # effects before showing the report, as in the MIO report dispatcher.
    events = ['add_namespace = RUS_football\n', f'''country_event = {{
 id = RUS_football.0
 hidden = yes
 is_triggered_only = yes
 fire_only_once = yes
 immediate = {{
  if = {{
   limit = {{ {eligible} NOT = {{ has_country_flag = RUS_football_started }} }}
   set_country_flag = RUS_football_started
   country_event = {{ id = RUS_football.1 }}
  }}
 }}
}}
''']
    guard = eligible + ' has_country_flag = RUS_football_started'
    events.append(f'''country_event = {{
 id = RUS_football.1
 title = RUS_football.1.t
 desc = RUS_football.1.d
 picture = {spec['picture']}
 is_triggered_only = yes
 fire_only_once = yes
 trigger = {{ {guard} }}
 option = {{
  name = RUS_football.1.a
  hidden_effect = {{ if = {{ limit = {{ {guard} }} set_country_flag = RUS_football_done }} }}
 }}
}}
''')
    loc = {'RUS_football.1.t': spec['title'],
           'RUS_football.1.d': '\n\n'.join(spec['paragraphs']),
           'RUS_football.1.a': spec['option']}
    result = {EVENT: '\n'.join(events).encode('utf-8'),
              GFX: ('spriteTypes = {\n spriteType = {\n  name = "'+spec['picture']+'"\n'
                    '  texturefile = "'+spec['picture_path']+'"\n }\n}\n').encode('utf-8')}
    for lang in ('simp_chinese', 'english', 'russian'):
        # Preserve the user's prose on other language UIs until translated.
        text = 'l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v, ensure_ascii=False)+'\n' for k,v in loc.items())
        result[Path(f'localisation/{lang}/RUS_football_l_{lang}.yml')] = text.encode('utf-8-sig')
    return result


def picture():
    from PIL import Image, ImageOps
    from build_bryukhanov_sketch_event_picture import build_card, compose
    spec = content()
    source = ROOT / spec['source_picture']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == spec['source']['image_sha256']
    with Image.open(source) as image:
        photo = ImageOps.fit(image.convert('RGB'), (184, 138), Image.Resampling.LANCZOS,
                             centering=tuple(spec['picture_processing']['crop_center']))
    return compose(build_card(photo))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for relative, data in outputs().items():
        path = ROOT / relative
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        elif not path.is_file() or path.read_bytes() != data:
            stale.append(str(relative))
    spec = content()
    path = ROOT / spec['picture_path']
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        picture().save(path, format='PNG', optimize=True)
    # A read-only check never repaints an asset.
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != spec['picture_sha256']:
        stale.append(spec['picture_path'])
    if stale:
        raise SystemExit('Stale football event outputs: '+', '.join(stale))
    print('PASS: seven-day football event, single full-text report, localisation and 210x176 photograph current.')


if __name__ == '__main__':
    main()
