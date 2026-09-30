"""Read-only structural checks across all runtime folders.

This checks syntax boundaries and definition collisions, not engine scope rules.
Repeated containers (on_actions, spriteType, option, modifier, etc.) are legal;
only namespaces with genuinely unique IDs are checked for duplicate definitions.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re

from hoi4_politics_blocks import load

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|[^\s"#{}]+|[{}]|"')


def main() -> int:
    errors = []
    scripts = []
    for folder in ("common", "events", "history", "interface", "music"):
        scripts.extend(p for p in (ROOT / folder).rglob("*") if p.suffix in (".txt", ".gui", ".gfx", ".asset"))
    for path in sorted(scripts):
        relative = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            errors.append(f"{relative}: unexpected script BOM")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            errors.append(f"{relative}: {error}")
            continue
        stack = []
        line = 1
        previous = 0
        for token in TOKEN.finditer(text):
            value = token[0]
            line += text.count("\n", previous, token.start())
            previous = token.start()
            if value == '"':
                errors.append(f"{relative}:{line}: unclosed quote")
            elif value == "{":
                stack.append(line)
            elif value == "}":
                if stack:
                    stack.pop()
                else:
                    errors.append(f"{relative}:{line}: unmatched closing brace")
        if stack:
            errors.append(f"{relative}: unclosed blocks at {stack}")

    definitions = defaultdict(list)
    for folder in ("scripted_effects", "scripted_triggers", "dynamic_modifiers", "country_leader"):
        for path in (ROOT / "common" / folder).glob("*.txt"):
            for node in load(path):
                entries = node.v if folder == "country_leader" and node.k == "leader_traits" else [node]
                for entry in entries:
                    definitions[(folder, entry.k)].append(path.relative_to(ROOT).as_posix())
    for path in (ROOT / "events").glob("*.txt"):
        for event in load(path):
            if event.k in ("country_event", "news_event") and event.one("id"):
                definitions[("event", event.value("id"))].append(path.relative_to(ROOT).as_posix())
    for path in (ROOT / "common/national_focus").glob("*.txt"):
        for tree in load(path):
            for focus in tree.children("focus"):
                definitions[("focus", focus.value("id"))].append(path.relative_to(ROOT).as_posix())
    for (namespace, name), paths in definitions.items():
        if len(paths) > 1:
            errors.append(f"Duplicate {namespace} {name}: {', '.join(paths)}")

    localisations = sorted((ROOT / "localisation").rglob("*.yml"))
    for path in localisations:
        raw = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        if not raw.startswith(b"\xef\xbb\xbf"):
            errors.append(f"{relative}: missing localisation BOM")
        text = raw.decode("utf-8-sig")
        keys = re.findall(r'^\s*([^#\s:]+):(?:\d+)?\s', text, re.M)
        duplicates = [key for key, count in Counter(keys).items() if count > 1]
        if duplicates:
            errors.append(f"{relative}: duplicate keys {duplicates}")
    for error in errors:
        print(error)
    print(f"Structure: {len(scripts)} scripts, {len(localisations)} localisation files, {len(errors)} errors.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
