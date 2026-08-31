from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOCUS_PATH = ROOT / "common" / "national_focus" / "RUS focus (Russia).txt"

SECTION_START = "\t### Federal Armaments and Defence Industry Commission ###"
SECTION_END = "\t### Kamenev Route Mirrors of Original VST Foci ###"

ROUTE_REQUIREMENTS = {
    "RUS_fr_soldier_load_lightening_program": "RUS_fr_infantry_lightweight_route",
    "RUS_fr_divisional_artillery_support_standard": "RUS_fr_infantry_artillery_route",
    "RUS_fr_vehicle_manufacturing_integration": "RUS_fr_vehicle_manufacturing_route",
    "RUS_fr_mechanised_logistics_regulations": "RUS_fr_mechanised_logistics_route",
    "RUS_fr_helicopter_pilot_program": "RUS_fr_helicopter_air_assault_route",
    "RUS_fr_self_propelled_direct_fire_system": "RUS_fr_self_propelled_fire_route",
    "RUS_fr_hull_structural_durability_trials": "RUS_fr_structural_durability_route",
}


def focus_blocks(section: str) -> list[tuple[int, int, str]]:
    blocks: list[tuple[int, int, str]] = []
    position = 0
    while True:
        start = section.find("\tfocus = {", position)
        if start < 0:
            return blocks
        brace = section.find("{", start)
        depth = 0
        end = brace
        while end < len(section):
            depth += (section[end] == "{") - (section[end] == "}")
            if depth == 0:
                end += 1
                break
            end += 1
        blocks.append((start, end, section[start:end]))
        position = end


def rewrite_focus(block: str) -> tuple[str, str, int]:
    focus_match = re.search(r"^\s*id\s*=\s*(RUS_fr_[A-Za-z0-9_]+)\s*$", block, re.M)
    cost_match = re.search(r"^(\s*)cost\s*=\s*([0-9.]+)\s*$", block, re.M)
    if not focus_match or not cost_match:
        raise RuntimeError("Armaments focus is missing an id or cost")

    focus_id = focus_match.group(1)
    days = round(float(cost_match.group(2)) * 7)
    threshold = days - 0.1

    block = re.sub(
        r"^\s*custom_override_tooltip\s*=\s*\{\s*tooltip\s*=\s*RUS_fr_automatic_focus_tt\s+always\s*=\s*no\s*\}\s*\n",
        "",
        block,
        flags=re.M,
    )
    block = re.sub(
        r"^\s*RUS_fr_requires_\d+_military_reform_materials\s*=\s*yes\s*\n",
        "",
        block,
        flags=re.M,
    )
    block = re.sub(
        r"^\s*select_effect\s*=\s*\{\s*add_to_variable\s*=\s*\{\s*RUS_fr_military_reform_materials\s*=\s*-10\s*\}\s*\}\s*\n",
        "",
        block,
        flags=re.M,
    )
    block = re.sub(
        r"^\s*add_to_variable\s*=\s*\{\s*RUS_fr_military_reform_materials\s*=\s*30\s+tooltip\s*=\s*RUS_fr_military_reform_materials_change_tt\s*\}\s*\n",
        "",
        block,
        flags=re.M,
    )

    route_requirement = ROUTE_REQUIREMENTS.get(focus_id)
    if route_requirement:
        available_match = re.search(r"^(\s*)available\s*=\s*\{\s*\n", block, re.M)
        if not available_match:
            raise RuntimeError(f"{focus_id} has no available block for its route lock")
        insertion = available_match.end()
        block = block[:insertion] + f"{available_match.group(1)}\t{route_requirement} = yes\n" + block[insertion:]

    block = re.sub(r"^\s*available\s*=\s*\{\s*\}\s*\n", "", block, flags=re.M)

    cost_match = re.search(r"^(\s*)cost\s*=\s*([0-9.]+)\s*$", block, re.M)
    assert cost_match is not None
    indent = cost_match.group(1)
    select_effect = (
        f"{cost_match.group(0)}\n"
        f"{indent}cancelable = no\n"
        f"{indent}select_effect = {{\n"
        f"{indent}\tif = {{\n"
        f"{indent}\t\tlimit = {{ check_variable = {{ RUS_fr_military_reform_materials > {threshold:.1f} }} }}\n"
        f"{indent}\t\tadd_to_variable = {{ RUS_fr_military_reform_materials = -{days} }}\n"
        f"{indent}\t\tcomplete_national_focus = {focus_id}\n"
        f"{indent}\t}}\n"
        f"{indent}}}"
    )
    block = block[: cost_match.start()] + select_effect + block[cost_match.end() :]

    reward_match = re.search(r"^(\s*)completion_reward\s*=\s*\{\s*\n", block, re.M)
    if not reward_match:
        raise RuntimeError(f"{focus_id} has no completion_reward")
    reward_insertion = reward_match.end()
    block = (
        block[:reward_insertion]
        + f"{reward_match.group(1)}\tcustom_effect_tooltip = RUS_fr_focus_materials_instant_completion_tt\n"
        + block[reward_insertion:]
    )
    return block, focus_id, days


def main() -> None:
    text = FOCUS_PATH.read_text(encoding="utf-8-sig")
    start = text.index(SECTION_START)
    end = text.index(SECTION_END, start)
    section = text[start:end]
    blocks = focus_blocks(section)
    if len(blocks) != 31:
        raise RuntimeError(f"Expected 31 armaments focuses, found {len(blocks)}")

    rewritten: list[str] = []
    cursor = 0
    report: list[tuple[str, int]] = []
    for block_start, block_end, block in blocks:
        new_block, focus_id, days = rewrite_focus(block)
        rewritten.append(section[cursor:block_start])
        rewritten.append(new_block)
        cursor = block_end
        report.append((focus_id, days))
    rewritten.append(section[cursor:])

    updated = text[:start] + "".join(rewritten) + text[end:]
    FOCUS_PATH.write_text(updated, encoding="utf-8-sig", newline="")
    print(f"Updated {len(report)} focuses in {FOCUS_PATH}")
    for focus_id, days in report:
        print(f"{focus_id}: {days} materials")


if __name__ == "__main__":
    main()
