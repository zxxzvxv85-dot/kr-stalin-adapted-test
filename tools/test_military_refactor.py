"""Exercise the retained military controllers without claiming game-runtime coverage."""

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
import re

from hoi4_politics_blocks import load


ROOT = Path(__file__).resolve().parents[1]
EVENT_PATH = ROOT / "events/RUS_fr_military_reform_events.txt"
FOCUS_PATH = ROOT / "common/national_focus/RUS focus (Russia).txt"
EVENTS = {node.value("id"): node for node in load(EVENT_PATH) if node.k == "country_event"}
EFFECTS = {node.k: node for node in load(ROOT / "common/scripted_effects/RUS_fr_auto_focus_effects.txt")}
TRIGGERS = {node.k: node for node in load(ROOT / "common/scripted_triggers/RUS_fr_auto_focus_triggers.txt")}
FOCI = {node.value("id"): node for tree in load(FOCUS_PATH) for node in tree.children("focus")}
MATERIALS = "RUS_fr_military_reform_materials"
ACTIVE = "RUS_fr_rectification_auto_project_active"
FINISHED = "RUS_fr_rectification_line_finished"
DISPATCHER = "RUS_fr_military_reform.102"
COMPLETION = "RUS_fr_military_reform.103"
COUNCIL = "RUS_fr_rebuild_revolutionary_military_council"


def descendants(nodes):
    for node in nodes:
        yield node
        if isinstance(node.v, list):
            yield from descendants(node.v)


@dataclass
class State:
    flags: set = field(default_factory=set)
    completed: set = field(default_factory=set)
    variables: dict = field(default_factory=dict)
    queued: list = field(default_factory=list)
    completions: Counter = field(default_factory=Counter)


def check(nodes, state):
    def one(node):
        if node.k in TRIGGERS:
            return check(TRIGGERS[node.k].v, state)
        if node.k == "NOT":
            return not check(node.v, state)
        if node.k == "OR":
            return any(one(child) for child in node.v)
        if node.k == "has_country_flag":
            return node.v in state.flags
        if node.k == "has_completed_focus":
            return node.v in state.completed
        if node.k == "check_variable":
            for comparison in node.v:
                assert comparison.op == ">", comparison.raw()
                if state.variables.get(comparison.k, 0) <= float(comparison.v):
                    return False
            return True
        raise AssertionError(f"Unsupported fixture trigger: {node.raw()}")

    return all(one(node) for node in nodes)


def run(nodes, state):
    matched = False
    for node in nodes:
        if node.k in ("if", "else_if", "else"):
            if node.k == "if":
                matched = False
            if not matched and (node.k == "else" or check(node.one("limit").v, state)):
                run([child for child in node.v if child.k != "limit"], state)
                matched = True
            continue
        matched = False
        if node.k in EFFECTS:
            run(EFFECTS[node.k].v, state)
        elif node.k == "set_country_flag":
            state.flags.add(node.v)
        elif node.k == "clr_country_flag":
            state.flags.discard(node.v)
        elif node.k == "country_event":
            state.queued.append((node.value("id"), int(node.value("days", "0"))))
        elif node.k == "complete_national_focus":
            focus = node.value("focus") if isinstance(node.v, list) else node.v
            state.completed.add(focus)
            state.completions[focus] += 1
        elif node.k == "add_to_variable":
            for value in node.v:
                state.variables[value.k] = state.variables.get(value.k, 0) + float(value.v)
        elif node.k == "activate_shine_on_focus":
            pass  # Presentation only; it does not affect controller eligibility.
        elif node.k == "random_list":
            eligible = []
            for branch in node.v:
                disabled = any(
                    modifier.value("factor") == "0"
                    and check([child for child in modifier.v if child.k != "factor"], state)
                    for modifier in branch.children("modifier")
                )
                if not disabled:
                    eligible.append(branch)
            if eligible:
                # A deterministic eligible choice lets the fixture test sequencing.
                run([child for child in eligible[0].v if child.k != "modifier"], state)
        else:
            raise AssertionError(f"Unsupported fixture effect: {node.raw()}")


def fire(event_id, state):
    event = EVENTS[event_id]
    trigger = event.one("trigger")
    if trigger is None or check(trigger.v, state):
        run(event.one("immediate").v, state)


def test_armaments_material_boundaries():
    text = FOCUS_PATH.read_text(encoding="utf-8-sig")
    start = text.index("### Federal Armaments and Defence Industry Commission ###")
    end = text.index("### Kamenev Route Mirrors of Original VST Foci ###", start)
    ids = [focus_id for focus_id, focus in FOCI.items() if start < focus.a < end]
    assert len(ids) == 31
    for focus_id in ids:
        focus = FOCI[focus_id]
        days = round(float(focus.value("cost")) * 7)
        for available in (0, days - 1, days, days + 10):
            state = State(variables={MATERIALS: available})
            run(focus.one("select_effect").v, state)
            if available >= days:
                assert state.variables[MATERIALS] == available - days
                assert state.completions == Counter({focus_id: 1})
            else:
                assert state.variables[MATERIALS] == available
                assert not state.completions
            assert not state.queued, "Armaments must not enter the retired automatic queue"


def test_rectification_wait_and_resume():
    state = State(completed={COUNCIL})
    opening = FOCI[COUNCIL].one("completion_reward")
    # Execute only the opening controller commands; unrelated rewards are outside this fixture.
    start = [node for node in descendants(opening.v) if (
        node.k == "set_country_flag" and node.v.startswith("RUS_fr_rectification_")
    ) or (node.k == "country_event" and isinstance(node.v, list) and node.value("id") == DISPATCHER)]
    run(start, state)
    assert state.queued.pop() == (DISPATCHER, 7)

    def next_project(delay):
        fire(DISPATCHER, state)
        assert ACTIVE in state.flags
        assert state.queued.pop() == (COMPLETION, delay)
        before = (state.flags.copy(), state.queued.copy())
        fire(DISPATCHER, state)
        assert (state.flags, state.queued) == before, "A second project started while one was active"
        fire(COMPLETION, state)
        assert ACTIVE not in state.flags
        assert state.queued.pop() == (DISPATCHER, 7)

    for _ in range(4):
        next_project(14)
    assert len(state.completions) == 4
    fire(DISPATCHER, state)
    assert ACTIVE not in state.flags
    assert state.queued.pop() == (DISPATCHER, 7), "Missing decision gates must cause a retry"
    assert len(state.completions) == 4
    state.flags.update({"RUS_fr_military_democracy_decision_complete", "RUS_fr_political_work_decision_complete"})
    next_project(14)
    fire(DISPATCHER, state)
    assert ACTIVE not in state.flags
    assert state.queued.pop() == (DISPATCHER, 7)
    state.flags.add("RUS_fr_soldiers_committees_decision_complete")
    next_project(21)
    fire(DISPATCHER, state)
    assert FINISHED in state.flags and not state.queued
    assert len(state.completions) == 6 and set(state.completions.values()) == {1}
    fire(DISPATCHER, state)
    assert not state.queued


def test_retired_interfaces_and_active_hooks():
    retired = re.compile(r"\bRUS_fr_military_reform\.(?:100|101|400|401|402)\b|\bRUS_fr_requires_\d+_military_reform_materials\b|\bRUS_fr_auto_(?:project_active|project_selected|project_waiting|dispatch_scheduled)\b")
    for folder in ("common", "events", "history", "interface"):
        for path in (ROOT / folder).rglob("*.txt"):
            assert not retired.search(path.read_text(encoding="utf-8-sig")), path
    assert {DISPATCHER, COMPLETION, "RUS_fr_military_reform.900", *[f"RUS_fr_military_reform.{i}" for i in range(910, 914)]} <= EVENTS.keys()
    hooks = load(ROOT / "common/on_actions/RUS_fr_military_reform_on_actions.txt")[0]
    for name in ("on_startup", "on_weekly"):
        assert any(node.k == "country_event" and node.value("id") == "RUS_fr_military_reform.900" for node in descendants(hooks.one(name).v))
    recovery = EVENTS["RUS_fr_military_reform.900"].one("immediate")
    assert any(node.k == "RUS_fr_consolidate_armaments_construction_results" for node in descendants(recovery.v))
    assert any(node.k == "country_event" and node.value("id") == DISPATCHER for node in descendants(recovery.v))
    for lang, filename in (("simp_chinese", "RUS_fr_military_reform_l_simp_chinese.yml"), ("english", "RUS_test_missing_l_english.yml"), ("russian", "RUS_test_missing_l_russian.yml")):
        path = ROOT / "localisation" / lang / filename
        assert path.read_bytes().startswith(b"\xef\xbb\xbf"), path
        text = path.read_text(encoding="utf-8-sig")
        assert not re.search(r"RUS_fr_requires_\d+_military_reform_materials_tt:|RUS_fr_military_reform\.402\.[tda]:", text)


if __name__ == "__main__":
    test_armaments_material_boundaries()
    test_rectification_wait_and_resume()
    test_retired_interfaces_and_active_hooks()
    print("PASS: 31 armaments focuses at four material boundaries; six rectification timers, active-project exclusion, decision-gated retry/resume, no duplicate completion; retired interfaces removed and recovery hooks retained")
