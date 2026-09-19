"""Exercise shipped event branches; this is not an HOI4 runtime test."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ns = {"__file__": str(ROOT / "tools/test_regional_diplomacy.py")}
exec((ROOT / "tools/test_regional_diplomacy.py").read_text(encoding="utf-8-sig").split("def country(")[0], ns)
parse, get = ns["parse"], ns["get"]
focus_id = "RUS_future_foreign_062"
event_prefix = "RUS_future_foreign_policy_events."
events = {get(v, "id"): v for k, _, v in ns["read"]("events/RUS_future_foreign_policy_events.txt") if k == "country_event"}
focus_source = (ROOT / "common/national_focus/00_RUS_future_foreign_policy_skeleton.txt").read_text(encoding="utf-8-sig")
focus = next(parse(block)[0][2] for block in re.split(r"(?m)(?=^shared_focus =)", focus_source) if re.search(r"\bid = " + focus_id + r"\b", block))

def check(nodes, state):
    for k, op, v in nodes:
        if k == "NOT": ok = not check(v, state)
        elif k == "has_country_flag": ok = v in state["flags"]
        elif k == "is_focus_being_completed": ok = state["active"] == v
        elif k == "country_exists": ok = v in {"GER", "POL", "RUS"}
        elif k == "power_balance_value":
            _, operator, threshold = next(n for n in v if n[0] == "value")
            ok = state["balance"] < float(threshold) if operator == "<" else state["balance"] >= float(threshold)
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
        elif k == "GER": run(v, state, "GER")
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
        elif k in {"name", "custom_effect_tooltip"}: pass
        else: raise AssertionError("Unexpected effect on claims-only path: " + k)

def fixture(balance):
    return dict(balance=balance, flags=set(), active=focus_id, events=[], claims=set(), wargoals=[], joins=[], completed=False)

for balance in [-1, -.1, 0, .4999, .5, .5001, 1]:
    s = fixture(balance)
    run(get(focus, "select_effect"), s)
    assert s["events"] == [(event_prefix + "7", "14")]
    dispatch = events[event_prefix + "7"]
    assert check(get(dispatch, "trigger"), s)
    s["events"].clear()
    run(get(dispatch, "immediate"), s)
    branch = "5" if balance < .5 else "6"
    assert s["events"] == [(event_prefix + branch, None)]
    assert not check(get(dispatch, "trigger"), s)
    event = events[event_prefix + branch]
    assert check(get(event, "trigger"), s)
    # Readiness changing while the popup is open must not change button rewards.
    s["balance"] = -balance
    run(get(event, "option"), s)
    assert s["completed"] and s["claims"] == {"537", "555"}
    assert s["wargoals"] == ([("GER", "ROOT")] if branch == "5" else [])
    assert s["joins"] == ([("RUS", "POL")] if branch == "6" else [])

s = fixture(0)
s["active"] = None
assert not check(get(events[event_prefix + "7"], "trigger"), s)
high = get(events[event_prefix + "6"], "immediate")
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
print("PASS: 7 readiness boundaries, single 14-day dispatch, cancellation, duplicate guard, both claims-only buttons, German wargoal, faction direction and 3 localisation files")
