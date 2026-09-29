"""Render the independent local factory sandbox. Read-only unless --write.

The previous Russia-map economy is not imported or run. Production is daily,
with no native economy changes and no connection to the old Five-Year Plan.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from industrial_planning_factory_ui import render_outputs
from industrial_planning_factory_assets import render_assets

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--check',action='store_true');mode.add_argument('--write',action='store_true')
    parser.add_argument('--output-root',type=Path);args=parser.parse_args()
    if args.check and args.output_root: parser.error('--check cannot write --output-root')
    out=(args.output_root or ROOT).resolve();text_outputs=render_outputs();assets=render_assets()
    assert text_outputs==render_outputs() and assets==render_assets(),'Non-deterministic output'
    outputs={**{rel:content.encode('utf-8-sig' if rel.endswith('.yml') else 'utf-8') for rel,content in text_outputs.items()},**assets}
    differences=[]
    for rel,encoded in outputs.items():
        target=(out/rel).resolve();assert target.is_relative_to(out)
        actual=target.read_bytes() if target.is_file() else None
        if actual is not None and rel in text_outputs:actual=actual.replace(b'\r\n',b'\n')
        if encoded!=actual:
            differences.append(rel)
            if args.write or args.output_root: target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(encoded)
    print(f'{"Generated" if args.write or args.output_root else "Checked"} {len(text_outputs)} text files + {len(assets)} textures; {len(differences)} differences.')
    if differences and not (args.write or args.output_root): raise SystemExit('\n'.join(differences))


if __name__=='__main__': main()
