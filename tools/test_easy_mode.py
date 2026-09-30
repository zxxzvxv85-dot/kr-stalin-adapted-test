from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from generate_easy_mode_advisors import render as render_advisors
from generate_easy_mode_dynamic import render as render_dynamic
from generate_easy_mode_ideas import render as render_ideas
from generate_easy_mode_military import render as render_military
from generate_easy_mode_technologies import render as render_technologies
from generate_relationship_advisor_tiers import ADVISORS, easy_modifier_value
from hoi4_politics_blocks import load


def check_generated(render, modifier_path: str, effect_path: str) -> None:
    modifiers, effects = render()
    assert (ROOT / modifier_path).read_text(encoding="utf-8") == modifiers
    assert (ROOT / effect_path).read_text(encoding="utf-8") == effects


check_generated(render_advisors, "common/dynamic_modifiers/RUS_easy_mode_advisor_bonus.txt", "common/scripted_effects/RUS_easy_mode_advisor_effects.txt")
check_generated(render_dynamic, "common/dynamic_modifiers/RUS_easy_mode_other_dynamic_bonus.txt", "common/scripted_effects/RUS_easy_mode_other_dynamic_effects.txt")
check_generated(render_ideas, "common/dynamic_modifiers/RUS_easy_mode_ideas_bonus.txt", "common/scripted_effects/RUS_easy_mode_ideas_effects.txt")
check_generated(render_military, "common/dynamic_modifiers/RUS_easy_mode_military_bonus.txt", "common/scripted_effects/RUS_easy_mode_military_effects.txt")
check_generated(render_technologies, "common/technologies/RUS_easy_mode_bonus_technologies.txt", "common/scripted_effects/RUS_easy_mode_technologies_effects.txt")

advisor = next(row for row in ADVISORS if row["slug"] == "ustinov")
stage = advisor["stage_effects"][2]
assert easy_modifier_value("consumer_goods_expected_value", stage["consumer_goods_expected_value"]) == 0.01
assert easy_modifier_value("production_speed_buildings_factor", stage["production_speed_buildings_factor"]) == 0.18
assert easy_modifier_value("production_cost_infrastructure_factor", stage["production_cost_infrastructure_factor"]) == -0.16
assert easy_modifier_value("stability_factor", stage["stability_factor"]) == -0.01
assert easy_modifier_value("civilian_intel_to_others", -7.5) == -15

decision = (ROOT / "common/decisions/RUS_easy_mode_decisions.txt").read_text(encoding="utf-8")
category = (ROOT / "common/decisions/categories/RUS_easy_mode_categories.txt").read_text(encoding="utf-8")
assert "fire_only_once = yes" in decision and "cost = 0" in decision
assert "is_ai = no" in decision and "RUS_easy_mode_refresh = yes" in decision
assert "RUS_stalin_refresh_easy_advisor_trait_tiers = yes" in decision
assert "allowed = { is_ai = no original_tag = RUS }" in category
technology = (ROOT / "common/technologies/RUS_easy_mode_bonus_technologies.txt").read_text(encoding="utf-8")
assert "RUS_fr_armour_priority_self_propelled_bonus_easy_bonus" in technology
assert "supply_consumption = -0.30" in technology
assert "soft_attack = 0.15" in technology
agriculture = (ROOT / "common/scripted_effects/RUS_national_agriculture_effects.txt").read_text(encoding="utf-8")
assert agriculture.count("= 1.10 } }\nelse = { multiply_variable = { RUS_nat_") == 10
assert "RUS_nat_preview_retention = 1.00" in agriculture
assert "RUS_nat_retention = 1.00" in agriculture

balance = (ROOT / "common/scripted_effects/RUS_stalin_kamenev_bop_effects.txt").read_text(encoding="utf-8")
start = balance.index("# The balance position and penalties are unchanged")
end = balance.index("\n\tif = {", balance.index("RUS_kamenev_balance_conscription_factor = 2", start))
easy_balance = balance[start:end]
assert "RUS_kamenev_balance_stability_factor > 0" in easy_balance
assert "RUS_kamenev_balance_pp_gain > 0" in easy_balance
assert "RUS_kamenev_party_balance = 2" not in easy_balance

for path in (ROOT / "common").rglob("RUS_easy_mode*.txt"):
    load(path)
for path in (ROOT / "common/decisions/RUS_easy_mode_decisions.txt", ROOT / "common/scripted_effects/RUS_stalin_kamenev_bop_effects.txt"):
    load(path)

for language in ("simp_chinese", "english", "russian"):
    path = ROOT / f"localisation/{language}/RUS_easy_mode_l_{language}.yml"
    text = path.read_text(encoding="utf-8-sig")
    assert text.startswith(f"l_{language}:")
    assert "RUS_enable_easy_mode" in text and "RUS_easy_mode_ideas_bonus" in text
    advisor_text = (ROOT / f"localisation/{language}/RUS_stalin_relationship_scaled_advisor_tiers_l_{language}.yml").read_text(encoding="utf-8-sig")
    assert "RUS_maximalist_advisor_kolegayev_national_easy_tt" in advisor_text

print("Passed: easy-mode generators, beneficial/penalty signs, toggle, balance, script parsing and localisation.")
