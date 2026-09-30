"""Conditionally double positive research bonuses in mod-owned effect blocks."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from apply_easy_mode_rewards import ROOT, KR, SOURCE_DIRS, INHERITED_SCRIPTS, changed_effects
from hoi4_politics_blocks import load, parse


START = "# RUS_EASY_MODE_TECH_START"
END = "# RUS_EASY_MODE_TECH_END"


def walk(nodes):
    for node in nodes:
        if node.k == "add_tech_bonus" and isinstance(node.v, list):
            bonus = node.value("bonus")
            try:
                if float(bonus) > 0:
                    yield node
            except (TypeError, ValueError):
                pass
        if isinstance(node.v, list):
            yield from walk(node.v)


def patch_text(source: str, candidates) -> tuple[str, int]:
    replacements = []
    for node in walk(candidates):
        prefix = source[:node.a]
        if prefix.rfind(START) > prefix.rfind(END):
            continue
        original = node.raw()
        amount = float(node.value("bonus"))
        doubled = f"{amount * 2:.6f}".rstrip("0").rstrip(".")
        boosted = re.sub(r"(?m)(\bbonus\s*=\s*)[0-9]+(?:\.[0-9]+)?", rf"\g<1>{doubled}", original, count=1)
        indent = re.match(r"\s*", source[source.rfind("\n", 0, node.a) + 1:node.a]).group(0)
        replacement = (
            f"\n{indent}{START}\n{indent}if = {{ limit = {{ hidden_trigger = {{ has_country_flag = RUS_easy_mode_enabled is_ai = no }} }} {boosted} }}\n"
            f"{indent}else = {{ {original} }}\n{indent}{END}\n{indent}"
        )
        replacements.append((node.a, node.b, replacement))
    for start, end, replacement in reversed(replacements):
        source = source[:start] + replacement + source[end:]
    return source, len(replacements)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    total = 0
    for folder in SOURCE_DIRS:
        for path in sorted(folder.glob("*.txt")):
            if path.name.startswith("RUS_easy_mode"):
                continue
            upstream = KR / path.relative_to(ROOT)
            if upstream.exists() and path.relative_to(ROOT).as_posix() not in INHERITED_SCRIPTS:
                continue
            source = path.read_text(encoding="utf-8-sig")
            nodes = parse(source)
            candidates = list(changed_effects(path, nodes, load(upstream))) if upstream.exists() else nodes
            patched, count = patch_text(source, candidates)
            if count:
                print(f"{path.relative_to(ROOT)}: {count}")
                total += count
                if args.write:
                    path.write_text(patched, encoding="utf-8", newline="\n")
    print(f"Total conditional research bonuses: {total}")


if __name__ == "__main__":
    main()
