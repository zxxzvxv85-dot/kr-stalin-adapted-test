"""Roster regression tests against generated HOI4 AST, not a second roster list."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import random
import unittest

from doudizhu_roster import ROOT, FALLBACK_PORTRAIT, catalogue, check, outputs, portrait_fallbacks
from hoi4_politics_blocks import N, load, parse


@dataclass
class Government:
    recruited: set[str] = field(default_factory=set)
    leader: str = ""
    roles: dict[str, set[str]] = field(default_factory=dict)
    hired: dict[str, str] = field(default_factory=dict)
    dead: set[str] = field(default_factory=set)
    flags: set[str] = field(default_factory=set)
    focuses: set[str] = field(default_factory=set)
    socialist: bool = True


class RosterVM:
    """Only the small script subset reached by these government fixtures.

    The draw effect is executed verbatim, including generated variable weights
    and their clearing.  Unhandled script instructions fail the test.
    """

    def __init__(self, government: Government | None = None, seed: int = 0):
        self.government = government or Government()
        rendered = outputs()
        self.triggers = {n.k: n for n in parse(rendered["common/scripted_triggers/RUS_doudizhu_roster.txt"])}
        self.triggers.update({n.k: n for n in load(ROOT / "common/scripted_triggers/RUS_stalin_advisor_lock_triggers.txt")})
        self.effect = parse(rendered["common/scripted_effects/RUS_doudizhu_roster.txt"])[0]
        self.variables: dict[str, float] = {}
        self.random = random.Random(seed)
        self.eligible_override: set[str] | None = None

    def all(self, nodes: list[N], character: str = "") -> bool:
        return all(self.test(n, character) for n in nodes)

    def test(self, n: N, character: str = "") -> bool:
        g = self.government
        key, value = n.k, n.v
        if key == "AND" or key in ("hidden_trigger", "limit"):
            return self.all(value, character)
        if key == "OR":
            return any(self.test(x, character) for x in value)
        if key == "NOT":
            return not any(self.test(x, character) for x in value)
        if key == "custom_override_tooltip":
            return self.all([x for x in value if x.k != "tooltip"], character)
        if key.startswith("RUS_") and isinstance(value, list):
            return self.all(value, key)
        if key == "always":
            return value == "yes"
        if key == "has_character":
            return value in g.recruited
        if key == "has_country_leader":
            return n.value("character") == g.leader
        if key == "has_character_flag":
            assert value == "is_dead"
            return character in g.dead
        if key == "has_advisor_role":
            return value in g.roles.get(character, set())
        if key in ("is_political_advisor", "is_second_in_command", "is_country_leader"):
            actual = {
                "is_political_advisor": g.hired.get(character) == "political_advisor",
                "is_second_in_command": g.hired.get(character) == "second_in_command",
                "is_country_leader": character == g.leader,
            }[key]
            return actual == (value == "yes")
        if key == "has_country_flag":
            return value in g.flags
        if key == "has_completed_focus":
            return value in g.focuses
        if key == "has_socialist_government":
            return g.socialist == (value == "yes")
        if key == "original_tag":
            return value == "RUS"
        if key == "check_variable":
            item = value[0]
            left, right = self.variables.get(item.k, 0), float(item.v)
            return {"=": left == right, ">": left > right, "<": left < right,
                    ">=": left >= right, "<=": left <= right}[item.op]
        if self.eligible_override is not None and key.startswith("RUS_ddz_person_"):
            return (key in self.eligible_override) == (value == "yes")
        if key in self.triggers:
            return self.all(self.triggers[key].v, character) == (value == "yes")
        raise AssertionError(f"Unhandled trigger {key}: {value}")

    def execute(self, nodes: list[N]) -> None:
        for n in nodes:
            if n.k == "set_variable":
                self.variables[n.v[0].k] = float(n.v[0].v)
            elif n.k == "add_to_variable":
                self.variables[n.v[0].k] = self.variables.get(n.v[0].k, 0) + float(n.v[0].v)
            elif n.k == "clear_variable":
                self.variables.pop(n.v, None)
            elif n.k == "if":
                if self.all(n.one("limit").v):
                    self.execute([child for child in n.v if child.k != "limit"])
            elif n.k == "random_list":
                choices = [x for x in n.v if self.variables.get(x.k, 0) > 0]
                if not choices:
                    raise AssertionError("A draw attempted with no positive weight")
                choice = self.random.choices(choices, [self.variables[x.k] for x in choices])[0]
                self.execute(choice.v)
            else:
                raise AssertionError(f"Unhandled effect {n.k}")


class RosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.people = {p.character: p for p in catalogue()}

    def eligible(self, government: Government, character: str) -> bool:
        vm = RosterVM(government)
        return vm.all(vm.triggers[self.people[character].trigger].v)

    def kaganovich_government(self) -> Government:
        person = "RUS_lazar_kaganovich"
        return Government(
            recruited={person, "RUS_iosif_stalin"}, leader="RUS_iosif_stalin",
            roles={person: {"political_advisor"}},
            flags={"RUS_kamenev_post_election_advisors_unlocked"},
            focuses={"RUS_reverse_the_october_revolution"},
        )

    def test_unlocked_unappointed_is_eligible(self):
        self.assertTrue(self.eligible(self.kaganovich_government(), "RUS_lazar_kaganovich"))

    def test_lock_and_life_and_recruitment_and_role_are_respected(self):
        person = "RUS_lazar_kaganovich"
        for changed in ("focus", "route_lock", "unrecruited", "dead", "role_removed", "hidden"):
            with self.subTest(changed=changed):
                g = self.kaganovich_government()
                if changed == "focus":
                    g.focuses.clear()
                elif changed == "route_lock":
                    g.flags.add("RUS_stalin_psr_balance_collapse_done")
                elif changed == "unrecruited":
                    g.recruited.remove(person)
                elif changed == "dead":
                    g.dead.add(person)
                elif changed == "role_removed":
                    g.roles.clear()
                elif changed == "hidden":
                    g.socialist = False
                self.assertFalse(self.eligible(g, person))

    def test_army_members_do_not_enter_unless_current_ruler(self):
        person = "RUS_kliment_voroshilov"
        g = Government(recruited={person}, roles={person: {"army_chief"}}, hired={person: "army_chief"})
        self.assertFalse(self.eligible(g, person))
        g.leader = person
        self.assertTrue(self.eligible(g, person))

    def test_former_leader_without_unlocked_civilian_role_is_excluded(self):
        person = "RUS_iosif_stalin"
        g = Government(recruited={person}, leader="RUS_yakov_sverdlov")
        self.assertFalse(self.eligible(g, person))
        g.leader = person
        self.assertTrue(self.eligible(g, person))

    def test_runtime_cabinet_appointment_is_included(self):
        # stalin_form_sov adds this SIC role at runtime, absent from the initial
        # Sverdlov character.  Its removal must not leave a permanent invite.
        person = "RUS_yakov_sverdlov"
        g = Government(recruited={person}, roles={person: {"second_in_command"}},
                       hired={person: "second_in_command"}, socialist=False)
        self.assertTrue(self.eligible(g, person))
        g.hired.clear()
        g.roles.clear()
        self.assertFalse(self.eligible(g, person))

    def test_sampling_counts_and_no_duplicates(self):
        people = tuple(self.people.values())
        for count in (0, 1, 2, 3, 4, 20, len(people)):
            for seed in range(8):
                with self.subTest(count=count, seed=seed):
                    vm = RosterVM(seed=seed)
                    pool = people[:count]
                    vm.eligible_override = {p.trigger for p in pool}
                    vm.execute(vm.effect.v)
                    self.assertEqual(vm.variables["RUS_ddz_people_count"], count)
                    seats = [int(vm.variables[f"RUS_ddz_person_{i}"]) for i in (1, 2, 3)]
                    if count < 3:
                        self.assertEqual(seats, [0, 0, 0])
                        self.assertEqual(vm.variables["RUS_ddz_people_ready"], 0)
                    else:
                        self.assertEqual(len(set(seats)), 3)
                        self.assertTrue(set(seats) <= {p.number for p in pool})
                        self.assertEqual(vm.variables["RUS_ddz_people_ready"], 1)
                        for seat, number in enumerate(seats, 1):
                            person = next(p for p in pool if p.number == number)
                            self.assertEqual(vm.variables[f"RUS_ddz_portrait_small_{seat}"], int(person.small))
                    self.assertFalse(any(k.startswith("RUS_ddz_person_weight_") for k in vm.variables))

    def test_safe_ids_and_static_structure(self):
        self.assertEqual(check()["characters"], len(self.people))
        self.assertTrue(all(0 < p.number <= 524288 for p in self.people.values()))
        self.assertEqual(len({p.number for p in self.people.values()}), len(self.people))

    def test_uniform_adviser_portraits(self):
        for person in self.people.values():
            with self.subTest(character=person.character):
                self.assertTrue(person.small)
                ports = person.instances[0].one("portraits")
                existing = {r.value("small") for r in ports.v if r.value("small")}
                if existing:
                    self.assertIn(person.portrait, existing)
                else:
                    self.assertEqual(person.portrait, FALLBACK_PORTRAIT)
        self.assertNotIn("RUS_iosif_stalin", portrait_fallbacks())
        self.assertNotIn("RUS_yakov_sverdlov", portrait_fallbacks())
        self.assertNotIn("RUS_lev_kamenev", portrait_fallbacks())
        self.assertNotIn("RUS_grigory_zinovyev", portrait_fallbacks())


if __name__ == "__main__":
    unittest.main()
