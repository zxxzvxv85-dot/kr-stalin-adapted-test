"""Check the easy-only VDV policy, generated combat totals and refresh lifecycle."""

from copy import deepcopy
from decimal import Decimal as D
from itertools import product
from pathlib import Path
import re

from hoi4_politics_blocks import load

ROOT = Path(__file__).resolve().parents[1]
UNIT = "air_assault_special_forces"
UNLOCK = "RUS_stalin_air_assault_special_forces_infantry"
BASE = "RUS_easy_mode_air_assault_base_bonus"
FLAG = "RUS_easy_mode_enabled"
NORMAL = "RUS_fr_air_assault_mobility_priority_idea"
EASY = "RUS_fr_air_assault_mobility_priority_easy_idea"
HIDDEN = "RUS_fr_hidden_air_assault_mobility_priority"
HIDDEN_EASY = "RUS_fr_hidden_air_assault_mobility_priority_easy"
BORROWED = "RUS_easy_mode_air_assault_inheritance"
FX = {
    n.k: n
    for filename in ("RUS_easy_mode_air_assault_effects.txt", "RUS_easy_mode_technologies_effects.txt")
    for n in load(ROOT / "common/scripted_effects" / filename)
}
TECHS = {
    n.k: n for filename in ("RUS_stalin_air_assault.txt", "RUS_easy_mode_bonus_technologies.txt")
    for root in load(ROOT / "common/technologies" / filename) for n in root.v
}


def country(easy=True, ai=False, ideas=(), techs=()):
    return {"flags": {FLAG} if easy else set(), "ai": ai, "ideas": set(ideas),
            "techs": set(techs), "vars": {}, "modifiers": {}, "dynamic": set()}


def condition(nodes, state):
    def one(node):
        if node.k in ("AND", "hidden_trigger"):
            return condition(node.v, state)
        if node.k == "OR":
            return any(one(child) for child in node.v)
        if node.k == "NOT":
            return not condition(node.v, state)
        if node.k == "has_country_flag":
            return node.v in state["flags"]
        if node.k == "has_idea":
            return node.v in state["ideas"]
        if node.k == "has_tech":
            return node.v in state["techs"]
        if node.k == "is_ai":
            return state["ai"] == (node.v == "yes")
        if node.k == "has_dynamic_modifier":
            return node.value("modifier") in state["dynamic"]
        raise AssertionError(node.raw())
    return all(one(node) for node in nodes)


def execute(nodes, state):
    matched = False
    for node in nodes:
        if node.k in ("if", "else_if", "else"):
            if node.k == "if":
                matched = False
            if not matched and (node.k == "else" or condition(node.one("limit").v, state)):
                execute([n for n in node.v if n.k != "limit"], state)
                matched = True
            continue
        matched = False
        if node.k in FX:
            execute(FX[node.k].v, state)
        elif node.k == "hidden_effect":
            execute(node.v, state)
        elif node.k in ("effect_tooltip", "custom_effect_tooltip"):
            continue
        elif node.k in ("add_ideas", "remove_ideas"):
            (state["ideas"].add if node.k == "add_ideas" else state["ideas"].discard)(node.v)
        elif node.k in ("set_country_flag", "clr_country_flag"):
            (state["flags"].add if node.k == "set_country_flag" else state["flags"].discard)(node.v)
        elif node.k == "set_technology":
            for tech in node.v:
                if tech.k != "popup":
                    assert tech.v == "1"
                    state["techs"].add(tech.k)
        elif node.k in ("add_dynamic_modifier", "remove_dynamic_modifier"):
            (state["dynamic"].add if node.k == "add_dynamic_modifier" else state["dynamic"].discard)(node.value("modifier"))
        elif node.k in ("set_variable", "add_to_variable"):
            for value in node.v:
                number = state["modifiers"].get(value.v.split("@", 1)[1], D(0)) if value.v.startswith("modifier@") else D(value.v)
                state["vars"][value.k] = number + (state["vars"].get(value.k, D(0)) if node.k == "add_to_variable" else 0)
        elif node.k == "force_update_dynamic_modifier":
            pass
        else:
            raise AssertionError(node.raw())


def test_totals():
    unit = load(ROOT / "common/units/RUS_stalin_air_assault.txt")[0].one(UNIT)
    extra = TECHS[BASE].one(UNIT)
    factors = ("soft_attack", "hard_attack", "defense", "breakthrough", "ap_attack", "air_attack", "armor_value", "maximum_speed")
    flat = ("max_strength", "max_organisation", "default_morale", "initiative")
    upgrades = ("RUS_fr_air_assault_mobility_priority_bonus",
                "RUS_stalin_air_assault_drivetrain_weight_reduction_bonus",
                "RUS_stalin_air_assault_bubble_canopy_bonus")
    for active in product((False, True), repeat=3):
        for key in (*factors, *flat):
            ordinary = D(unit.value(key, "0")) + (1 if key in factors else 0)
            added = D(extra.value(key, "0"))
            for present, tech in zip(active, upgrades):
                if present:
                    ordinary += D(TECHS[tech].one(UNIT).value(key, "0"))
                    added += D(TECHS[tech + "_easy_bonus"].one(UNIT).value(key, "0"))
            assert ordinary + added == ordinary * 10, (active, key, ordinary, added)
    assert D(unit.value("combat_width")) + D(extra.value("combat_width")) == 1
    assert D("12.5") * (1 + D(extra.value("maximum_speed"))) == D(125)
    assert D(unit.value("max_organisation")) + D(extra.value("max_organisation")) == 600
    assert D(unit.value("max_strength")) + D(extra.value("max_strength")) == 300
    for terrain in ("plains", "forest", "hills", "mountain", "jungle", "marsh", "desert", "urban"):
        for stat in ("attack", "defence", "movement"):
            assert D(unit.one(terrain).value(stat)) == D("0.5")
            assert D(unit.one(terrain).value(stat)) + D(extra.one(terrain).value(stat)) == D(5)
    assert not {n.k for n in extra.v} & {"manpower", "need", "supply_consumption", "fuel_consumption", "training_time", "weight"}
    assert unit.value("manpower") == "1300" and unit.value("supply_consumption") == "0.22"
    assert unit.one("need").value("helicopter_equipment") == "30"
    assert unit.one("need").value("infantry_equipment") == "60"


def test_enable_and_repeat():
    for easy, ai, unlocked in product((False, True), repeat=3):
        state = country(easy, ai, techs=[UNLOCK] if unlocked else [])
        execute(FX["RUS_easy_mode_refresh_technologies"].v, state)
        assert (BASE in state["techs"]) == (easy and not ai and unlocked)
        assert not ({UNIT, "RUS_fr_air_assault_mobility_priority_bonus"} & state["techs"])
        before = deepcopy(state)
        for _ in range(5):
            execute(FX["RUS_easy_mode_refresh_technologies"].v, state)
        assert state == before


def test_cost_order_and_consolidation():
    ideas = {idea.k: idea for filename in ("RUS_fr_military_reform_ideas.txt", "RUS_fr_military_reform_hidden_ideas.txt")
             for root in load(ROOT / "common/ideas" / filename) for cat in root.v for idea in cat.v}
    cost = lambda key: D(ideas[key].one("equipment_bonus").one("helicopter_equipment").value("build_cost_ic"))
    assert cost(NORMAL) == cost(HIDDEN) == 5
    assert cost(EASY) == cost(HIDDEN_EASY) == D("-0.5")
    event = next(n for n in load(ROOT / "events/RUS_fr_military_reform_events.txt") if n.value("id") == "RUS_fr_military_reform.10")
    mobility = next(n for n in event.children("option") if n.value("name") == "RUS_fr_military_reform.10.b")
    consolidate = next(n for n in load(ROOT / "common/scripted_effects/RUS_fr_military_reform_effects.txt") if n.k == "RUS_fr_consolidate_armaments_construction_results")
    # Execute the real two cost-conversion branches, excluding unrelated reform rewards.
    def find_cost_branches(nodes):
        found = []
        for n in nodes:
            if n.k == "if" and n.one("limit").value("has_idea") in (NORMAL, EASY):
                found.append(n)
            elif isinstance(n.v, list):
                found.extend(find_cost_branches(n.v))
        return found
    branches = find_cost_branches(consolidate.v)
    assert len(branches) == 2
    for easy_first, consolidate_first in product((False, True), repeat=2):
        state = country(easy_first)
        execute(mobility.one("hidden_effect").v, state)
        if consolidate_first:
            execute(branches, state)
        state["flags"].add(FLAG)
        execute(FX["RUS_easy_mode_refresh_air_assault_equipment"].v, state)
        if not consolidate_first:
            execute(branches, state)
        assert state["ideas"] == {HIDDEN_EASY}
        for _ in range(5):
            execute(FX["RUS_easy_mode_refresh_air_assault_equipment"].v, state)
            execute(branches, state)
        assert state["ideas"] == {HIDDEN_EASY}
        assert sum(cost(key) for key in state["ideas"]) == D("-0.5")
    for easy, ai in product((False, True), repeat=2):
        state = country(easy, ai)
        execute(mobility.one("hidden_effect").v, state)
        assert state["ideas"] == ({EASY} if easy and not ai else {NORMAL})
    empty = country()
    execute(FX["RUS_easy_mode_refresh_air_assault_equipment"].v, empty)
    assert not empty["ideas"], "Easy mode must not grant the unearned production policy"
    trigger = (ROOT / "common/scripted_triggers/RUS_fr_auto_focus_triggers.txt").read_text(encoding="utf-8")
    assert f"has_idea = {EASY}" in trigger


def test_borrowed_bonuses():
    state = country(techs=[UNLOCK])
    state["modifiers"] = {
        "army_infantry_attack_factor": D("0.1"), "army_armor_attack_factor": D("0.2"),
        "army_infantry_defence_factor": D("0.15"), "army_armor_defence_factor": D("0.25"),
        "mechanized_attack_factor": D("0.3"), "special_forces_attack_factor": D("0.4"),
    }
    effect = FX["RUS_easy_mode_refresh_air_assault_inheritance"]
    for _ in range(8):
        execute(effect.v, state)
        assert state["vars"]["RUS_easy_vdv_borrowed_attack"] == D("0.3")
        assert state["vars"]["RUS_easy_vdv_borrowed_defence"] == D("0.4")
        assert state["dynamic"] == {BORROWED}
    # Native mechanized and SF bonuses remain one copy each; the bridge borrows
    # infantry and armour only. Removing a policy must remove its cached bonus.
    assert state["vars"]["RUS_easy_vdv_borrowed_attack"] + D("0.3") + D("0.4") == D(1)
    state["modifiers"]["army_armor_attack_factor"] = D("-0.05")
    execute(effect.v, state)
    assert state["vars"]["RUS_easy_vdv_borrowed_attack"] == D("0.05")
    state["modifiers"] = {}
    execute(effect.v, state)
    assert not any(state["vars"].values())
    for disabled in ("normal", "ai", "locked"):
        blocked = country(easy=disabled != "normal", ai=disabled == "ai", techs=[] if disabled == "locked" else [UNLOCK])
        blocked["dynamic"].add(BORROWED)
        execute(effect.v, blocked)
        assert not blocked["dynamic"] and not any(blocked["vars"].values())
    unit = load(ROOT / "common/units/RUS_stalin_air_assault.txt")[0].one(UNIT)
    assert unit.value("special_forces") == "yes"
    assert [node.k for node in unit.one("type").v] == ["mechanized"]


def test_localisation_and_native_mio_preview():
    keys = {BASE, BORROWED, EASY, EASY + "_desc", HIDDEN_EASY,
            "RUS_stalin_air_assault_drivetrain_weight_reduction_bonus",
            "RUS_stalin_air_assault_bubble_canopy_bonus",
            "RUS_stalin_air_assault_drivetrain_weight_reduction_bonus_easy_bonus",
            "RUS_stalin_air_assault_bubble_canopy_bonus_easy_bonus"}
    for lang in ("simp_chinese", "english", "russian"):
        path = ROOT / f"localisation/{lang}/RUS_easy_mode_l_{lang}.yml"
        assert path.read_bytes().startswith(b"\xef\xbb\xbf")
        locs = re.findall(r"^\s+([\w.]+):", path.read_text(encoding="utf-8-sig"), re.M)
        assert len(locs) == len(set(locs)) and keys <= set(locs)
    mio = load(ROOT / "common/military_industrial_organization/organizations/RUS_stalin_kamov_helicopter_organization.txt")[0]
    for token in ("RUS_vdv_generic_mio_trait_drivetrain_weight_reduction", "RUS_vdv_generic_mio_trait_bubble_canopy"):
        trait = next(n for n in mio.children("trait") if n.value("token") == token)
        reward = trait.one("on_complete").one("FROM")
        assert reward.one("effect_tooltip").one("set_technology") is not None
        assert reward.one("if").one("effect_tooltip").one("set_technology") is not None
        assert "RUS_easy_mode_refresh_technologies = yes" in reward.one("hidden_effect").raw()


if __name__ == "__main__":
    test_totals()
    test_enable_and_repeat()
    test_cost_order_and_consolidation()
    test_borrowed_bonuses()
    test_localisation_and_native_mio_preview()
    print("Passed: VDV 10x combat/speed, width 1, eight 500% terrains, cost policy order, one-copy category inheritance and native MIO previews.")
