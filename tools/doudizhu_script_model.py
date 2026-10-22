"""Fail-closed interpreter for the small HOI4 effect subset used by card gameplay.

Tests execute generated engine scripts, not a second implementation of game rules.
Not an engine emulator: GUI rendering and actual random-list/scoping integration
still require HOI4. Unsupported effects/triggers fail rather than being ignored.
"""
from __future__ import annotations

import math
import random
from hoi4_politics_blocks import parse


class ScriptModel:
    def __init__(self, effects, seed=1):
        self.effects = effects
        self.vars = {}
        self.temp = {}
        self.flags = set()
        self.rng = random.Random(seed)
        self.steps = 0
        self.calls = {}

    def number(self, value):
        if isinstance(value, (int, float)):
            return value
        try:
            return float(value)
        except ValueError:
            return self.temp.get(value, self.vars.get(value, 0))

    def check(self, nodes):
        if hasattr(nodes, "v"):
            nodes = nodes.v
        for node in nodes:
            key, value = node.k, node.v
            if key in ("AND", "hidden_trigger"):
                passed = self.check(value)
            elif key == "OR":
                passed = any(self.check([child]) for child in value)
            elif key == "NOT":
                passed = not any(self.check([child]) for child in value)
            elif key == "always":
                passed = value == "yes"
            elif key == "check_variable":
                if node.one("var"):
                    left, right = self.number(node.value("var")), self.number(node.value("value"))
                    op = node.value("compare", "equals")
                else:
                    child = value[0]
                    left, right, op = self.number(child.k), self.number(child.v), child.op
                passed = self.compare(left, right, op)
            elif key == "has_country_flag":
                passed = value in self.flags
            elif key == "has_variable":
                passed = value in self.vars
            elif key in ("tag", "original_tag"):
                passed = value == "RUS"
            elif key == "is_ai":
                passed = value == "no"
            else:
                raise AssertionError(("Unsupported trigger", node.raw()))
            if not passed:
                return False
        return True

    @staticmethod
    def compare(a, b, op):
        if op in ("=", "equals"):
            return math.isclose(a, b, abs_tol=0.00001)
        if op in (">", "greater_than"):
            return a > b
        if op in ("<", "less_than"):
            return a < b
        if op in (">=", "greater_than_or_equals"):
            return a >= b
        if op in ("<=", "less_than_or_equals"):
            return a <= b
        raise AssertionError(("Unsupported comparison", op))

    def call(self, name):
        self.calls[name] = self.calls.get(name, 0) + 1
        if name == "RUS_ddz_pick_people":
            # Lifecycle fixture supplies roster candidates; roster has separate checks.
            eligible = self.vars.get("fixture_candidates", 5)
            self.vars["RUS_ddz_people_count"] = eligible
            self.vars["RUS_ddz_people_ready"] = int(eligible >= 3)
            if eligible >= 3:
                for seat, person in enumerate(self.rng.sample(range(1, eligible + 1), 3), 1):
                    self.vars[f"RUS_ddz_person_{seat}"] = person
            return
        self.run(self.effects[name].v)

    def run(self, nodes):
        taken = None
        for node in nodes:
            self.steps += 1
            if self.steps > 50_000_000:
                raise AssertionError("Runaway gameplay script")
            key, value = node.k, node.v
            if key == "if":
                taken = self.check(node.one("limit"))
                if taken:
                    self.run([x for x in value if x.k != "limit"])
                continue
            if key == "else_if":
                assert taken is not None, "orphan else_if"
                if not taken and self.check(node.one("limit")):
                    self.run([x for x in value if x.k != "limit"])
                    taken = True
                continue
            if key == "else":
                assert taken is not None, "orphan else"
                if not taken:
                    self.run(value)
                taken = None
                continue
            taken = None
            if key in ("hidden_effect",):
                self.run(value)
            elif key in ("set_country_flag", "clr_country_flag"):
                self.flags.add(value) if key.startswith("set") else self.flags.discard(value)
            elif key.endswith("variable") and key.startswith(("set_", "add_to_", "subtract_from_", "multiply_", "divide_", "modulo_")):
                if node.one("var"):
                    name, amount = node.value("var"), self.number(node.value("value"))
                else:
                    name, amount = value[0].k, self.number(value[0].v)
                target = self.temp if "temp_variable" in key else self.vars
                old = target.get(name, 0)
                if key.startswith("set_"):
                    target[name] = amount
                elif key.startswith("add_to_"):
                    target[name] = old + amount
                elif key.startswith("subtract_from_"):
                    target[name] = old - amount
                elif key.startswith("multiply_"):
                    target[name] = old * amount
                elif key.startswith("divide_"):
                    target[name] = old / amount
                elif key.startswith("modulo_"):
                    target[name] = old % amount
            elif key in ("round_variable", "round_temp_variable"):
                target = self.temp if "temp" in key else self.vars
                target[value] = round(target.get(value, 0))
            elif key in ("clear_variable", "clear_temp_variable"):
                (self.temp if "temp" in key else self.vars).pop(value, None)
            elif key == "for_loop_effect":
                index = node.value("value", "v")
                stop = node.value("break", "break")
                at = self.number(node.value("start", "0"))
                end = self.number(node.value("end", "0"))
                delta = self.number(node.value("add", "1"))
                comparison = node.value("compare", "less_than")
                body = [x for x in value if x.k not in ("value", "break", "start", "end", "add", "compare")]
                assert delta != 0
                count = 0
                self.temp[stop] = 0
                while self.compare(at, end, comparison):
                    self.temp[index] = at
                    self.run(body)
                    count += 1
                    assert count < 1000, "Runaway loop"
                    if self.temp.get(stop, 0):
                        break
                    at += delta
            elif key == "random_list":
                choices = []
                for entry in value:
                    if entry.k in ("seed", "log"):
                        continue
                    weight = self.number(entry.k)
                    if entry.one("trigger") and not self.check(entry.one("trigger")):
                        continue
                    # Roster tests can use this too; conditional weights must be explicit.
                    for mod in entry.children("modifier"):
                        if self.check([x for x in mod.v if x.k not in ("factor", "add")]):
                            weight *= self.number(mod.value("factor", "1"))
                            weight += self.number(mod.value("add", "0"))
                    if weight > 0:
                        choices.append((entry, weight))
                assert choices, "Empty random list"
                entry = self.rng.choices([x[0] for x in choices], weights=[x[1] for x in choices])[0]
                self.run([x for x in entry.v if x.k not in ("trigger", "modifier")])
            elif key in self.effects or key == "RUS_ddz_pick_people":
                self.call(key)
            else:
                raise AssertionError(("Unsupported effect", node.raw()))


def load_effects(*texts):
    result = {}
    for text in texts:
        for node in parse(text):
            assert node.k not in result
            result[node.k] = node
    return result
