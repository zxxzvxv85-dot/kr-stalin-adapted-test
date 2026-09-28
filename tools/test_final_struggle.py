"""Exercise shipped event branches; this is not an HOI4 runtime test."""
from pathlib import Path
from copy import deepcopy
import re

ROOT = Path(__file__).resolve().parents[1]
ns = {"__file__": str(ROOT / "tools/test_regional_diplomacy.py")}
exec((ROOT / "tools/test_regional_diplomacy.py").read_text(encoding="utf-8-sig").split("def country(")[0], ns)
parse, get = ns["parse"], ns["get"]
focus_id = "RUS_future_foreign_062"
event_prefix = "RUS_future_foreign_policy_events."
event_source = (ROOT / "events/RUS_future_foreign_policy_events.txt").read_text(encoding="utf-8-sig")
# The engine rejects >=/<= here even though the generic test parser accepts them.
assert not re.search(r"\bvalue\s*(?:>=|<=)", event_source), "Use NOT with a strict comparison for BOP thresholds"
events = {get(v, "id"): v for k, _, v in parse(event_source) if k == "country_event"}
focus_source = (ROOT / "common/national_focus/00_RUS_future_foreign_policy_skeleton.txt").read_text(encoding="utf-8-sig")
focus = next(parse(block)[0][2] for block in re.split(r"(?m)(?=^shared_focus =)", focus_source) if re.search(r"\bid = " + focus_id + r"\b", block))

def check(nodes, state):
    for k, op, v in nodes:
        if k == "NOT": ok = not check(v, state)
        elif k == "POL": ok = check(v, state)
        elif k == "is_subject_of": ok = state["pol_overlord"] == v
        elif k == "has_country_flag": ok = v in state["flags"]
        elif k == "focus_progress": ok = state["active"] == get(v, "focus") and not state["completed"]
        elif k == "has_completed_focus": ok = state["completed"]
        elif k == "country_exists": ok = v in state["countries"]
        elif k == "has_power_balance":
            assert get(v, "id") == "RUS_europe_intervention_power_balance"
            ok = state["has_bop"]
        elif k == "is_in_faction": ok = bool(state["pol_faction"]) == (v == "yes")
        elif k == "is_in_faction_with": ok = state["pol_faction"] == "RUS"
        elif k == "power_balance_value":
            _, operator, threshold = next(n for n in v if n[0] == "value")
            assert operator in {"<", ">"}, "Unsupported BOP comparison in fixture"
            ok = state["balance"] < float(threshold) if operator == "<" else state["balance"] > float(threshold)
        else: raise AssertionError((k, op, v))
        if not ok: return False
    return True

def run(nodes, state, scope="RUS"):
    matched = False
    for k, _, v in nodes:
        if k == "if":
            matched = check(get(v, "limit"), state)
            if matched: run([n for n in v if n[0] != "limit"], state, scope)
        elif k == "else":
            if not matched: run(v, state, scope)
        elif k == "hidden_effect": run(v, state, scope)
        elif k in {"GER", "POL"}: run(v, state, k)
        elif k == "leave_faction":
            assert scope == "POL"
            state["pol_faction"] = None
        elif k == "set_politics": state["politics"].append((scope, get(v, "ruling_party")))
        elif k == "give_guarantee": state["guarantees"].append((scope, v))
        elif k == "end_puppet":
            assert scope == state["pol_overlord"] and v == "POL"
            state["pol_overlord"] = None
        elif k == "declare_war_on":
            if get(v, "target") == "POL":
                assert state["pol_overlord"] is None and state["pol_faction"] != "GER", "Poland must be independent before war"
            state["wars"].append((scope, get(v, "target")))
        elif k == "set_country_flag": state["flags"].add(v)
        elif k == "country_event": state["events"].append((get(v, "id"), get(v, "days")))
        elif k == "complete_national_focus":
            assert v == focus_id
            state["active"] = None
            state["completed"] = True
            run(get(focus, "completion_reward"), state, scope)
        elif k == "add_state_claim": state["claims"].add(v)
        elif k == "create_wargoal": state["wargoals"].append((scope, get(v, "target")))
        elif k == "add_to_faction": state["joins"].append((scope, v))
        elif k in {"name", "custom_effect_tooltip", "scoped_play_song"}: pass  # Audio is an external engine boundary.
        else: raise AssertionError("Unexpected effect on claims-only path: " + k)

def fixture(balance):
    return dict(balance=balance, flags=set(), active=focus_id, events=[], claims=set(), wargoals=[], joins=[], completed=False, pol_faction="GER", pol_overlord="GER", politics=[], guarantees=[], wars=[], countries={"GER", "POL", "RUS"}, has_bop=True)

assert "is_focus_being_completed" not in event_source
for balance in [-1, -.75, -.5, 0, .5, .7499, .75, .7501, 1]:
    s = fixture(balance)
    run(get(focus, "select_effect"), s)
    assert s["events"] == [(event_prefix + "10", "7"), (event_prefix + "7", "14")]
    dispatch = events[event_prefix + "7"]
    assert check(get(dispatch, "trigger"), s)
    s["events"].clear()
    run(get(dispatch, "immediate"), s)
    branch = "5" if balance < .75 else "6"
    assert s["events"] == [(event_prefix + branch, None)]
    assert not check(get(dispatch, "trigger"), s)
    event = events[event_prefix + branch]
    assert check(get(event, "trigger"), s)
    assert get(event, "immediate") is None, "Visible events must wait for the button"
    assert not s["wars"] and not s["guarantees"] and not s["politics"] and not s["completed"]
    # Readiness changing while the popup is open must not change button rewards.
    s["balance"] = -balance
    run(get(event, "option"), s)
    assert s["completed"] and s["claims"] == {"537", "555"}
    assert s["wargoals"] == []
    assert s["joins"] == ([("RUS", "POL")] if branch == "6" else [])
    assert s["wars"] == [("GER", "POL" if branch == "6" else "RUS")]
    assert s["guarantees"] == ([("RUS", "POL")] if branch == "6" else [])
    assert s["politics"] == ([("POL", "radical_socialist")] if branch == "6" else [])
    assert s["pol_overlord"] == (None if branch == "6" else "GER")

# Day seven is a separate narrative: its threshold is strictly greater than 75,
# evaluated at delivery, and it must not pre-empt the existing day-fourteen logic.
uprising = events[event_prefix + "10"]
assert get(uprising, "is_triggered_only") == get(uprising, "fire_only_once") == "yes"
assert get(uprising, "immediate") is None
assert get(uprising, "picture") == "GFX_report_event_POL_revolution"
for start in (0, .75, 1):
    for day_seven in (-1, 0, .7499, .75, .7501, 1):
        s = fixture(start)
        run(get(focus, "select_effect"), s)
        assert s["events"] == [(event_prefix + "10", "7"), (event_prefix + "7", "14")]
        s["balance"] = day_seven
        assert check(get(uprising, "trigger"), s) == (day_seven > .75)
        snapshot = deepcopy(s)
        run(get(uprising, "option"), s)
        assert s == snapshot, "Narrative button must not change diplomacy, readiness, rewards or focus progress"
        assert check(get(events[event_prefix + "7"], "trigger"), s), "Day-seven report must not resolve day fourteen"
for missing in ("POL", "GER"):
    s = fixture(1); s["countries"].remove(missing)
    assert not check(get(uprising, "trigger"), s)
for changes in ({"active": None}, {"completed": True}, {"has_bop": False}):
    s = fixture(1); s.update(changes)
    assert not check(get(uprising, "trigger"), s)

s = fixture(0)
s["active"] = None
assert not check(get(events[event_prefix + "7"], "trigger"), s)
high = get(events[event_prefix + "6"], "option")
s = fixture(1)
s["pol_overlord"] = None
s["pol_faction"] = None
run(high, s)
assert s["wars"] == [("GER", "POL")] and s["pol_overlord"] is None
assert get(high, "give_guarantee") == "POL"
assert get(get(get(high, "GER"), "declare_war_on"), "target") == "POL"
assert get(get(get(high, "POL"), "set_politics"), "ruling_party") == "radical_socialist"
assert get(get(get(high, "POL"), "if"), "leave_faction") == "yes"

for lang in ["simp_chinese", "english", "russian"]:
    p = ROOT / f"localisation/{lang}/RUS_future_foreign_policy_mechanics_l_{lang}.yml"
    assert p.read_bytes().startswith(b"\xef\xbb\xbf")
    lines = p.read_text(encoding="utf-8-sig").splitlines()
    keys = []
    for line in lines[1:]:
        if not line.strip() or line.lstrip().startswith("#"): continue
        match = re.fullmatch(r'\s+([^\s:]+):\d*\s+"(?:\\.|[^"\\])*"\s*', line)
        assert match, (p, line)
        keys.append(match[1])
    assert len(keys) == len(set(keys)), p
    tooltip = next(line for line in lines if event_prefix + "5.a_tt:" in line)
    assert "\u00a7R" in tooltip and "\u00a7!" in tooltip
    p = ROOT / f"localisation/{lang}/RUS_warsaw_uprising_l_{lang}.yml"
    assert p.read_bytes().startswith(b"\xef\xbb\xbf")
    text = p.read_text(encoding="utf-8-sig")
    for suffix in ("t", "d", "a"): assert text.count(event_prefix+"10."+suffix+":") == 1
    assert "§b[POL.GetRUSWarsawHeadOfGovernment]§!" in text and "§b[POL.GetName]§!" in text
    assert text.count("\\n\\n") == 5
    if lang == "simp_chinese":
        assert "诺奇尼茨基" not in text and "波兰王国" not in text
        assert '"波兰人的枷锁终究由自己摘落"' in text

head_loc = parse((ROOT / "common/scripted_localisation/RUS_warsaw_uprising_loc.txt").read_text(encoding="utf-8"))[0][2]
assert get(head_loc, "name") == "GetRUSWarsawHeadOfGovernment"
head_branches = [v for k, _, v in head_loc if k == "text"]
assert get(get(get(head_branches[0], "trigger"), "any_character"), "is_second_in_command") == "yes"
assert get(head_branches[0], "localization_key").strip('"') == "[GetSecondInCommand]"
assert get(head_branches[1], "trigger") is None
assert get(head_branches[1], "localization_key").strip('"') == "[GetLeader]"
print("PASS: 9 day-fourteen BOP boundaries; 18 day-seven start/delivery pairs; strict >75, narrative-only option, target/cancel guards, black dynamic names and head-of-government fallback.")
