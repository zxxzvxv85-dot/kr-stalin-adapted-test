"""Render the independent local factory sandbox. Read-only unless --write.

The previous Russia-map economy is not imported or run. Production is daily,
with no native economy changes and no connection to the old Five-Year Plan.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from industrial_planning_factory_ui import render_outputs

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--check',action='store_true');mode.add_argument('--write',action='store_true')
    parser.add_argument('--output-root',type=Path);args=parser.parse_args()
    if args.check and args.output_root: parser.error('--check cannot write --output-root')
    out=(args.output_root or ROOT).resolve();outputs=render_outputs();assert outputs==render_outputs(),'Non-deterministic output'
    differences=[]
    for rel,content in outputs.items():
        target=(out/rel).resolve();assert target.is_relative_to(out)
        encoded=content.encode('utf-8-sig' if rel.endswith('.yml') else 'utf-8')
        actual=target.read_bytes().replace(b'\r\n',b'\n') if target.is_file() else None
        if encoded!=actual:
            differences.append(rel)
            if args.write or args.output_root: target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(encoded)
    print(f'{"Generated" if args.write or args.output_root else "Checked"} {len(outputs)} files; {len(differences)} differences.')
    if differences and not (args.write or args.output_root): raise SystemExit('\n'.join(differences))


if __name__=='__main__': main()
