"""Read-only border-event regressions using shipped scripts, not the HOI4 engine.

The small fixture counts native focus-completion calls and models the current
political-power rewards; regional initialisation is an explicit external boundary.
"""
from copy import deepcopy
from itertools import product
from pathlib import Path
import re

from test_support.regional_diplomacy import get, parse


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "RUS_future_foreign_policy_events."
FOCUS_PATH = "common/national_focus/00_RUS_future_foreign_policy_skeleton.txt"
EVENT_PATH = "events/RUS_future_foreign_policy_events.txt"
RUSSIA_PATH = "events/RUS events (Russia).txt"
TARGETS = {
    PREFIX + "13": "RUS_future_foreign_020",
    PREFIX + "14": "RUS_future_foreign_036",
    "russia_socialist_events.183": "RUS_future_foreign_037",
}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def definition(source, kind, wanted):
    # Parse only the requested top-level block; inherited files contain bare
    # lists outside this fixture's grammar, and duplicate IDs must not be hidden.
    blocks = re.split(r"(?m)(?=^" + kind + r"\s*=)", source)
    candidates = [b for b in blocks
                  if (match := re.search(r"\bid\s*=\s*([^\s{}]+)", b)) and match[1] == wanted]
    assert len(candidates) == 1, (kind, wanted, len(candidates))
    node = parse(candidates[0])[0]
    assert node[0] == kind and get(node[2], "id") == wanted
    return node[2]


def walk(nodes, path=()):
    for key, op, value in nodes:
        yield path, key, op, value
        if isinstance(value, list):
            yield from walk(value, path + (key,))


def values(nodes, key):
    return [value for found, _, value in nodes if found == key]


def check(nodes, state, scope="RUS"):
    for key, op, value in nodes:
        assert op == "=", (key, op)
        if key in {"AND", "hidden_trigger"}:
            ok = check(value, state, scope)
        elif key == "NOT":
            ok = not check(value, state, scope)
        elif key == "GER":
            ok = check(value, state, "GER")
        elif key == "has_completed_focus":
            assert scope == "RUS"
            ok = value in state["completed"]
        elif key == "has_country_flag":
            ok = value in state["flags"]
        elif key == "is_ai":
            ok = state["ai"] == (value == "yes")
        elif key == "has_socialist_government":
            ok = state["socialist"] == (value == "yes")
        elif key == "has_war_with":
            ok = value in state["wars"]
        elif key == "is_faction_leader":
            assert scope == "GER"
            ok = state["ger_leader"] == (value == "yes")
        else:
            raise AssertionError(("Unsupported fixture condition", key))
        if not ok:
            return False
    return True


def run(nodes, state):
    for key, _, value in nodes:
        if key == "if":
            if check(get(value, "limit"), state):
                run([node for node in value if node[0] != "limit"], state)
        elif key == "hidden_effect":
            run(value, state)
        elif key == "complete_national_focus":
            # Deliberately do not emulate engine duplicate suppression: the
            # option's own guard must prevent a second reward invocation.
            state["completion_calls"].append(value)
            state["completed"].add(value)
            run(get(focuses[value], "completion_reward"), state)
        elif key == "add_political_power":
            state["pp"] += float(value)
        elif key in {"RUS_rd_BAT_init", "RUS_rd_LIT_init", "RUS_rd_BLR_init", "RUS_ukr_init"}:
            assert value == "yes"
            state["initialisation_calls"].append(key)
        elif key in {"name", "log", "unlock_decision_tooltip"}:
            pass
        else:
            raise AssertionError(("Unexpected event/focus effect", key))


focus_source = read(FOCUS_PATH)
entry = definition(focus_source, "shared_focus", "RUS_future_foreign_008")
focuses = {focus: definition(focus_source, "shared_focus", focus) for focus in TARGETS.values()}
event_source = read(EVENT_PATH)
russia_source = read(RUSSIA_PATH)
events = {
    event: definition(russia_source if event.startswith("russia_") else event_source, "country_event", event)
    for event in TARGETS
}

# Only focus completion queues the two independent reports, in RUS scope with
# fixed delays. This rejects accidental selection-time, random or gated queues.
queued = [(path, value) for path, key, _, value in walk(entry)
          if key == "country_event" and get(value, "id") in TARGETS]
assert queued == [
    (("completion_reward", "hidden_effect"), [("id", "=", PREFIX + "13"), ("days", "=", "56")]),
    (("completion_reward", "hidden_effect"), [("id", "=", PREFIX + "14"), ("days", "=", "108")]),
], queued
for event in (PREFIX + "13", PREFIX + "14"):
    # A second call site elsewhere could create a second queued report.
    assert len(re.findall(r"\bid\s*=\s*" + re.escape(event) + r"\b", focus_source)) == 1
    assert len(re.findall(r"\bid\s*=\s*" + re.escape(event) + r"\b", event_source)) == 1

# The preceding Karelin-Shumskyi meeting is a different event. Preserve its
# leader eligibility, random timing, two popularity rewards and Kharkiv queue.
old_queue = [(path, value) for path, key, _, value in walk(entry)
             if key == "country_event" and get(value, "id") == "russia_socialist_events.182"]
assert old_queue == [(("completion_reward", "hidden_effect", "if"), parse("""
    id = russia_socialist_events.182 days = 20 random_days = 20
"""))]
meeting_branch = next(value for _, key, _, value in walk(entry)
                      if key == "if" and get(get(value, "country_event", []), "id") == "russia_socialist_events.182")
assert get(meeting_branch, "limit") == parse("""
    UKR = { NOT = { has_country_leader = { character = UKR_volodymyr_vynnychenko } } }
""")
meeting = definition(russia_source, "country_event", "russia_socialist_events.182")
assert meeting == parse('''
    id = russia_socialist_events.182
    title = russia_socialist_events.182.t
    desc = russia_socialist_events.182.d
    is_triggered_only = yes
    picture = GFX_report_event_RUS_karelin
    trigger = {
        has_socialist_government = yes
        NOT = { has_war_with = GER }
        GER = { is_faction_leader = yes }
    }
    option = {
        log = "[GetLogInfo]: event russia_socialist_events.182 option russia_socialist_events.182.a"
        name = russia_socialist_events.182.a
        hidden_effect = { country_event = { id = russia_socialist_events.183 days = 60 random_days = 60 } }
        add_popularity = { ideology = syndicalist popularity = 0.02 }
        add_popularity = { ideology = radical_socialist popularity = 0.02 }
    }
'''), "The existing meeting event/Kharkiv timing changed"

kharkiv = events["russia_socialist_events.183"]
assert get(kharkiv, "trigger") == get(meeting, "trigger")
assert get(kharkiv, "picture") == "GFX_report_event_generic_rally"
for socialist, war, leader in product((False, True), repeat=3):
    state = dict(socialist=socialist, wars={"GER"} if war else set(), ger_leader=leader)
    assert check(get(kharkiv, "trigger"), state) == (socialist and not war and leader)

expected_init = {
    "RUS_future_foreign_020": ["RUS_rd_BAT_init", "RUS_rd_LIT_init"],
    "RUS_future_foreign_036": ["RUS_rd_BLR_init"],
    "RUS_future_foreign_037": ["RUS_ukr_init"],
}
scenarios = 0
for event_id, focus_id in TARGETS.items():
    event = events[event_id]
    assert get(event, "is_triggered_only") == get(event, "fire_only_once") == "yes"
    assert get(event, "hidden") is None and get(event, "immediate") is None
    assert get(event, "title") == event_id + ".t" and get(event, "desc") == event_id + ".d"
    if event_id.startswith(PREFIX):
        assert get(event, "trigger") is None, "Already-completed focuses must not suppress the report"
    options = values(event, "option")
    assert len(options) == 1 and get(options[0], "name") == event_id + ".a"
    option = options[0]
    # The sole native completion command remains visible; only its redundant
    # completed-focus condition is hidden from the button's tooltip.
    guards = values(option, "if")
    assert len(guards) == 1
    assert get(guards[0], "limit") == parse(f"hidden_trigger = {{ NOT = {{ has_completed_focus = {focus_id} }} }}")
    assert get(guards[0], "complete_national_focus") == focus_id
    for already, easy, ai in product((False, True), repeat=3):
        state = dict(completed={focus_id} if already else set(),
                     flags={"RUS_easy_mode_enabled"} if easy else set(), ai=ai,
                     pp=0, completion_calls=[], initialisation_calls=[])
        before = deepcopy(state)
        run(option, state)
        if already:
            assert state == before, (event_id, "already completed", easy, ai)
        else:
            assert state["completion_calls"] == [focus_id]
            assert state["completed"] == {focus_id}
            assert state["pp"] == (100 if easy and not ai else 50)
            assert state["initialisation_calls"] == expected_init[focus_id]
        after = deepcopy(state)
        run(option, state)
        assert state == after, (event_id, "duplicate button execution")
        scenarios += 1

# Replacement localisation is required for the inherited Kharkiv keys. Check
# all three languages independently: an upstream normal-folder definition is
# intentional, but a second replace-folder override in one language is not.
expected_keys = {event + "." + suffix for event in TARGETS for suffix in ("t", "d", "a")}
for language in ("simp_chinese", "english", "russian"):
    path = ROOT / f"localisation/replace/RUS_border_revolution_events_l_{language}.yml"
    assert path.read_bytes().startswith(b"\xef\xbb\xbf"), (path, "Missing UTF-8 BOM")
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    assert lines[0] == "l_" + language + ":", (path, "Wrong language header")
    loc = {}
    for line in lines[1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r'\s+([^\s:]+):\d*\s+"((?:\\.|[^"\\])*)"\s*', line)
        assert match, (path, line)
        assert match[1] not in loc, (path, "Duplicate key", match[1])
        assert match[2].strip(), (path, "Empty value", match[1])
        loc[match[1]] = match[2]
    assert set(loc) == expected_keys, (path, set(loc) ^ expected_keys)
    counts = dict.fromkeys(expected_keys, 0)
    for other in (ROOT / "localisation/replace").rglob("*.yml"):
        text = other.read_text(encoding="utf-8-sig")
        if not re.search(r"(?m)^\s*l_" + language + r":\s*$", text):
            continue
        for key in re.findall(r"(?m)^\s+([^\s:]+):\d*\s", text):
            if key in counts:
                counts[key] += 1
    assert all(count == 1 for count in counts.values()), (language, counts)

print(f"PASS: 56/108-day completion queues; preserved meeting/Kharkiv chain; 8 trigger boundaries; {scenarios} reward/duplicate fixtures; three-language replacement keys and BOM. Static/fixture validation only.")
