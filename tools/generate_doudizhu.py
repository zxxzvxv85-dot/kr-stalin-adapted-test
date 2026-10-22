"""Generate the development-only government Dou Dizhu minigame (default: read-only)."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def outputs():
    import doudizhu_game
    import doudizhu_gui
    import doudizhu_roster
    import doudizhu_rules
    result = {}
    for module in (doudizhu_game, doudizhu_gui, doudizhu_roster, doudizhu_rules):
        for path, content in module.outputs().items():
            if path in result:
                raise ValueError(f"Duplicate generated path: {path}")
            if isinstance(content, str):
                content = content.removeprefix("\ufeff").replace("\r\n", "\n")
                content = content.encode("utf-8-sig" if path.startswith("localisation/") else "utf-8")
            result[path] = content
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--assets", action="store_true", help="Explicitly rebuild procedural UI glyphs; requires --write")
    args = parser.parse_args()
    if args.assets and not args.write:
        parser.error("--assets requires --write")
    import doudizhu_gui
    import doudizhu_roster
    if args.assets:
        doudizhu_gui.build_assets(ROOT)
    asset_errors = doudizhu_gui.validate_assets(ROOT)
    if asset_errors:
        raise SystemExit("\n".join(asset_errors))
    doudizhu_roster.check()
    mismatches = []
    rendered = outputs()
    for relative, content in rendered.items():
        path = ROOT / relative
        # Git on this workspace checks text out as CRLF. Preserve BOM checks,
        # but compare equivalent line endings without rewriting on --check.
        actual = path.read_bytes().replace(b"\r\n", b"\n") if path.is_file() else None
        if actual != content:
            mismatches.append(relative)
            if args.write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
    if mismatches and not args.write:
        raise SystemExit("Generated files differ:\n" + "\n".join(mismatches))
    print(f"Dou Dizhu: {len(rendered)} generated files consistent" if not args.write else f"Dou Dizhu: updated {len(mismatches)} generated files")


if __name__ == "__main__":
    main()
