"""Add conditional copies of positive one-off rewards in mod-owned scripts.

Only files absent from the installed Kaiserreich source are considered. The
marker makes this script safe to rerun after later edits. The normal branch is
not changed, and costs/negative rewards are never copied.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from hoi4_politics_blocks import load, parse


ROOT = Path(__file__).resolve().parents[1]
KR = ROOT.parent / "1521695605"
SOURCE_DIRS = (ROOT / "common/decisions", ROOT / "common/national_focus", ROOT / "common/scripted_effects", ROOT / "common/on_actions", ROOT / "events")
REWARD_KEYS = {
    "add_political_power",
    "add_stability",
    "add_war_support",
    "add_manpower",
    "army_experience",
    "air_experience",
    "navy_experience",
    "add_command_power",
    "add_mio_funds_gain_factor",
    "add_mio_size",
    "add_extra_state_shared_building_slots",
}
BLOCK_REWARDS = {
    "add_equipment_to_stockpile": "amount",
    "add_building_construction": "level",
    "add_offsite_building": "level",
    "add_resource": "amount",
}
SKIP_ANCESTORS = {
    "limit", "trigger", "available", "visible", "modifier", "hidden_modifier",
    "ai_will_do", "ai_chance", "cost", "custom_cost_trigger", "cancel_trigger",
}
MARKER = "# RUS_EASY_MODE_REWARD"
INHERITED_SCRIPTS = {
    "common/national_focus/RUS focus (Russia).txt",
    "common/decisions/RUS decisions (Russia).txt",
    "events/RUS events (Russia).txt",
}


def collect(nodes, ancestors=()):
    for node in nodes:
        if node.k in REWARD_KEYS and not any(key in SKIP_ANCESTORS for key in ancestors):
            try:
                amount = float(node.v)
            except (TypeError, ValueError):
                amount = 0
            if amount > 0:
                yield node
        if node.k in BLOCK_REWARDS and isinstance(node.v, list) and not any(key in SKIP_ANCESTORS for key in ancestors):
            if node.k == "add_building_construction" and node.value("type") in {"land_facility", "air_facility", "dam"}:
                continue
            amount = node.value(BLOCK_REWARDS[node.k])
            try:
                if float(amount) > 0:
                    yield node
            except (TypeError, ValueError):
                pass
        if isinstance(node.v, list):
            yield from collect(node.v, ancestors + (node.k,))


def changed_effects(path: Path, current: list, original: list):
    relative = path.relative_to(ROOT).as_posix()
    if relative.startswith("common/national_focus/"):
        def focuses(nodes):
            return {focus.value("id"): focus for tree in nodes if tree.k == "focus_tree" for focus in tree.children("focus")}
        old = focuses(original)
        for key, focus in focuses(current).items():
            prior = old.get(key)
            for field in ("completion_reward", "select_effect"):
                before = prior.children(field) if prior else []
                for block in focus.children(field):
                    if not before or block.norm() != before[0].norm():
                        yield block
        return
    if relative.startswith("events/"):
        def events(nodes):
            return {event.value("id"): event for event in nodes if event.k in ("country_event", "news_event", "state_event")}
        old = events(original)
        for key, event in events(current).items():
            prior = old.get(key)
            for field in ("immediate", "after"):
                before = prior.children(field) if prior else []
                for block in event.children(field):
                    if not before or block.norm() != before[0].norm():
                        yield block
            old_options = {option.value("name", str(index)): option for index, option in enumerate(prior.children("option"))} if prior else {}
            for index, option in enumerate(event.children("option")):
                previous = old_options.get(option.value("name", str(index)))
                if previous is None or option.norm() != previous.norm():
                    yield option
        return
    if relative.startswith("common/decisions/"):
        def decisions(nodes):
            return {(category.k, decision.k): decision for category in nodes if isinstance(category.v, list) for decision in category.v if isinstance(decision.v, list)}
        old = decisions(original)
        for key, decision in decisions(current).items():
            prior = old.get(key)
            for field in ("complete_effect", "remove_effect", "cancel_effect", "effect"):
                before = prior.children(field) if prior else []
                for block in decision.children(field):
                    if not before or block.norm() != before[0].norm():
                        yield block


def patch_text(source: str, candidates=None) -> tuple[str, int]:
    insertions = []
    for node in collect(parse(source)) if candidates is None else (node for block in candidates for node in collect([block])):
        following = source[node.b:node.b + 2000]
        already_copied_block = isinstance(node.v, list) and re.match(
            r"\s*if\s*=\s*\{\s*limit\s*=\s*\{\s*hidden_trigger\s*=\s*\{",
            following,
        ) and "RUS_easy_mode_enabled" in following[:200] and MARKER in following
        if MARKER in source[node.b:node.b + 200] or already_copied_block:
            continue
        before = source[source.rfind("\n", 0, node.a) + 1:node.a]
        indent = re.match(r"\s*", before).group(0)
        suffix = "" if source[node.b:node.b + 1] in ("\n", "\r") else f"\n{indent}"
        if node.k in {"add_building_construction", "add_resource", "add_extra_state_shared_building_slots"}:
            trigger = "owner = { has_country_flag = RUS_easy_mode_enabled is_ai = no }"
        elif node.k in {"add_mio_funds_gain_factor", "add_mio_size"}:
            trigger = "ROOT = { has_country_flag = RUS_easy_mode_enabled is_ai = no }"
        else:
            trigger = "has_country_flag = RUS_easy_mode_enabled is_ai = no"
        effect = node.raw() if isinstance(node.v, list) else f"{node.k} = {node.v}"
        insertion = (
            f"\n{indent}if = {{ limit = {{ hidden_trigger = {{ {trigger} }} }} "
            f"{effect} }} {MARKER}{suffix}"
        )
        insertions.append((node.b, insertion))
    for position, insertion in reversed(insertions):
        source = source[:position] + insertion + source[position:]
    return source, len(insertions)


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
            candidates = None
            if upstream.exists():
                candidates = list(changed_effects(path, parse(source), load(upstream)))
            patched, count = patch_text(source, candidates)
            if count:
                print(f"{path.relative_to(ROOT)}: {count}")
                total += count
                if args.write:
                    path.write_text(patched, encoding="utf-8-sig" if source.startswith("\ufeff") else "utf-8", newline="\n")
    print(f"Total conditional reward copies: {total}")


if __name__ == "__main__":
    main()
