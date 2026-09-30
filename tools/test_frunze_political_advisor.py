"""Guard removal of Frunze's cabinet role while retaining his military career.

These checks inspect effective script and exercise the event's actual conditions.
They do not simulate HOI4 character transfer, promotion, UI or crash behaviour.
"""
from itertools import product
import re

from generate_relationship_advisor_tiers import ADVISORS, render_outputs
from hoi4_politics_blocks import KR, R, data, load, tokens

MILITARY = "RUS_mikhail_frunze"
POLITICAL = "RUS_mikhail_frunze_political"
CHIEF = "RUS_mikhail_frunze_army_chief"
RETIRED = re.compile(
    r"\b(?:RUS_mikhail_frunze_(?:political|advisor)|"
    r"RUS_relationship_(?:display|scaled)_frunze\w*|"
    r"RUS_frunze_(?:legacy\w*|ideological_crusader)|"
    r"KR_bolshevik_frunze_bop|RUS_migrate_frunze_political_advisor|"
    r"RUS_refresh_frunze_legacy_advisor_bonus)\b"
)


def descendants(nodes):
    for node in nodes:
        yield node
        if isinstance(node.v, list):
            yield from descendants(node.v)


def check_military_roles():
    characters = data(R / "common/characters/RUS characters.txt", "characters")
    assert characters.one(POLITICAL) is None
    frunze = characters.one(MILITARY)
    assert frunze is not None and frunze.one("corps_commander") is not None
    roles = frunze.children("advisor")
    assert len(roles) == 1 and roles[0].value("slot") == "army_chief"
    assert roles[0].value("idea_token") == CHIEF
    assert tokens(roles[0].one("traits")) == ["RUS_fr_army_leadership_frunze"]
    assert not any("relationship" in trait for trait in tokens(frunze.one("corps_commander").one("traits")))
    history = load(R / "history/countries/RUS - Russia.txt")
    assert sum(n.k == "recruit_character" and n.v == MILITARY for n in history) == 1
    assert next(n for n in history if n.k == MILITARY).value("set_nationality") == "FOP"


def check_faction_entry():
    inherited = data(KR / "common/scripted_effects/RUS effects (Russia).txt", "RUS_add_faction_traits")
    current = data(R / "common/scripted_effects/zz_RUS_frunze_faction_trait_effects.txt", "RUS_add_faction_traits")
    original = inherited.one("hidden_effect").v
    retired = [n for n in original if n.k == "add_trait" and n.value("character") == MILITARY]
    assert len(retired) == 1 and retired[0].value("slot") == "political_advisor"
    expected = [n.norm() for n in original if n not in retired]
    assert [n.norm() for n in current.one("hidden_effect").v] == expected
    # Compare against KR so another upstream write cannot silently recreate the role.
    assert MILITARY not in current.raw()


def check_no_cabinet_references():
    scanned = 0
    for folder in ("common", "events", "history", "localisation"):
        for path in (R / folder).rglob("*"):
            if not path.is_file() or path.suffix not in {".txt", ".yml"}:
                continue
            match = RETIRED.search(path.read_text(encoding="utf-8-sig"))
            assert match is None, (path.relative_to(R), match.group(0) if match else "")
            scanned += 1
    assert all(row["slug"] != "frunze" and row["character"] != MILITARY for row in ADVISORS)
    for relative, expected in render_outputs().items():
        assert RETIRED.search(expected) is None, relative
        assert (R / relative).read_text(encoding="utf-8-sig") == expected, relative
    return scanned


def check_selection_and_career():
    events = {n.value("id"): n for n in load(R / "events/RUS events (Russia).txt") if n.k == "country_event"}
    event = events["russia_socialist_events.132"]
    options = {n.value("name"): n for n in event.children("option")}
    maximalist = options["russia_socialist_events.132.b"]
    ordinary = options["russia_socialist_events.132.f"]
    for option in (maximalist, ordinary):
        assert option.value("activate_advisor") == CHIEF
        assert POLITICAL not in option.raw()
    triggers = {n.k: n for n in load(KR / "common/scripted_triggers/RUS triggers (Russia).txt")}
    triggers.update({n.k: n for n in load(R / "common/scripted_triggers/_government_scripted_triggers.txt")})

    def check(nodes, flags, characters):
        def one(node):
            key, value = node.k, node.v
            if key == "tooltip":
                return True
            if key in {"AND", "hidden_trigger", "custom_override_tooltip"}:
                return check(value, flags, characters)
            if key == "NOT":
                return not any(one(child) for child in value)
            if key == "OR":
                return any(one(child) for child in value)
            if key == "has_country_flag":
                return value in flags
            if key == "has_character":
                return value in characters
            if key in triggers:
                return check(triggers[key].v, flags, characters) == (value == "yes")
            raise AssertionError(("unmodelled event condition", key))
        return all(one(n) for n in nodes)

    cases = 0
    for socialist, maximalist_route, present in product((False, True), repeat=3):
        flags = {key for key, enabled in (("KR_is_socialist", socialist), ("RUS_maximalist_side", maximalist_route)) if enabled}
        characters = {MILITARY} if present else set()
        assert check(ordinary.one("trigger").v, flags, characters) == (socialist and not maximalist_route and present)
        assert check(maximalist.one("trigger").v, flags, characters) == maximalist_route
        cases += 1
    # No rank check was introduced, and returning/promotion still targets the military record.
    assert "is_field_marshal" not in maximalist.raw() + ordinary.raw()
    exiles = events["russia_socialist_events.30"].one("option")
    assert any(n.k == "RUS_restore_bolshevik_exiles" for n in descendants(exiles.v))
    restore = data(KR / "common/scripted_effects/RUS effects (Russia).txt", "RUS_restore_bolshevik_exiles")
    assert restore.one("RUS").one(MILITARY).value("promote_leader") == "yes"
    focuses = data(R / "common/national_focus/RUS focus (Russia).txt", "focus_tree").children("focus")
    reorganisation = next(n for n in focuses if n.value("id") == "RUS_fr_national_military_reform_program")
    assert any(n.k == MILITARY and n.value("promote_leader") == "yes" for n in descendants(reorganisation.v))
    balance = (R / "common/scripted_effects/RUS_stalin_kamenev_bop_effects.txt").read_text(encoding="utf-8-sig")
    assert f"has_idea = {CHIEF}" in balance, "army-chief balance influence must remain"
    easy = (R / "common/scripted_effects/RUS_easy_mode_advisor_effects.txt").read_text(encoding="utf-8-sig")
    assert f"has_idea = {CHIEF}" in easy, "army-chief easy-mode bonus must remain"
    return cases


def main():
    check_military_roles()
    check_faction_entry()
    files = check_no_cabinet_references()
    cases = check_selection_and_career()
    print(f"PASS: Frunze military-only roles; KR initialization parity; {files} files without retired cabinet references; generation parity; {cases} chief-selection conditions; military career, chief influence and easy bonus retained. Static checks only.")


if __name__ == "__main__":
    main()
