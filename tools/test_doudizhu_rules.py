"""Execute generated Clausewitz effects and compare against independent rules.

No HOI4 process is used. This validates emitted logic, not the engine GUI.
"""
from __future__ import annotations

import itertools
import random
import unittest

import doudizhu_rules as rules
from doudizhu_script_model import ScriptModel, load_effects


class ScriptVM(ScriptModel):
    """Use the same fail-closed effect executor as the full game tests."""

    def __init__(self, text=None):
        super().__init__(load_effects(text if text is not None else next(iter(rules.outputs().values()))))

    def evaluate(self, name, counts, previous=rules.Move()):
        stem = "a" if name == "choose_move" else "s"
        self.vars.update({rules.v(f"{stem}_{r}"): c for r, c in enumerate(counts, 1)})
        self.vars.update({rules.v("last_" + key): value for key, value in (
            ("kind", previous.kind), ("power", previous.power), ("len", previous.length), ("n", previous.n))})
        self.call(rules.v(name))
        return rules.Move(*(int(self.vars[rules.v(key)]) for key in ("kind", "power", "len", "n")))

    def selected(self):
        return tuple(int(self.vars[rules.v(f"s_{r}")]) for r in range(1, 16))


def cards(*pairs):
    result = [0] * 15
    for rank, count in pairs:
        result[rank - 1] = count
    return tuple(result)


class RulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vm = ScriptVM()

    def assert_rule(self, counts, expected_kind=None, previous=rules.Move()):
        expected = rules.classify(counts)
        if expected_kind is not None:
            self.assertEqual(expected.kind, expected_kind, counts)
        actual = self.vm.evaluate("classify", counts, previous)
        self.assertEqual(actual, expected, counts)
        self.assertEqual(self.vm.vars[rules.v("valid")], int(bool(expected.kind)), counts)
        self.assertEqual(self.vm.vars[rules.v("beats")], int(expected.beats(previous)), (counts, previous))

    def test_each_type_and_wing_boundaries(self):
        examples = {
            1: cards((15, 1)), 2: cards((13, 2)), 3: cards((12, 3)),
            4: cards((13, 3), (15, 1)), 5: cards((3, 3), (5, 2)),
            6: cards(*[(r, 1) for r in range(8, 13)]),
            7: cards((10, 2), (11, 2), (12, 2)),
            8: cards((11, 3), (12, 3)), 9: cards((1, 3), (2, 3), (13, 2)),
            10: cards((1, 3), (2, 3), (12, 2), (13, 2)),
            11: cards((1, 4), (13, 2)), 12: cards((1, 4), (12, 2), (13, 2)),
            13: cards((13, 4)), 14: cards((14, 1), (15, 1)),
        }
        for kind, c in examples.items():
            self.assert_rule(c, kind)
            for old in (rules.Move(), rules.Move(kind, 1, rules.classify(c).length, sum(c)),
                        rules.Move(13, 13, 1, 4), rules.Move(14, 15, 1, 2)):
                self.assert_rule(c, previous=old)
        invalid = [
            cards(), cards((14, 2)), cards((1, 5)), cards((1, -1)),
            cards(*[(r, 1) for r in range(9, 14)]),  # 2 cannot extend straight
            cards((12, 3), (13, 3)),  # 2 cannot extend airplane
            cards((1, 4), (2, 4)),  # core's fourth card cannot be a wing
            cards((1, 3), (2, 3), (3, 3), (13, 3)),  # triple wings excluded
            cards((1, 4), (2, 3), (3, 1)),  # one core rank has four selected
            cards((1, 4), (2, 4), (3, 2)),  # one four-rank cannot count as two pair wings
            cards((1, 1), (3, 1)), cards((1, 2), (2, 2)),
        ]
        for c in invalid:
            self.assert_rule(c, 0)
        self.assert_rule(cards((1, 3), (2, 3), (14, 1), (15, 1)), 9)
        self.assert_rule(cards((1, 4), (14, 1), (15, 1)), 11)

    def test_all_fixed_patterns_and_mutations(self):
        hand = (4,) * 13 + (1, 1)
        rng = random.Random(1929)
        for p in rules.PATTERNS:
            c = rules.candidate(hand, p)
            self.assertIsNotNone(c)
            self.assert_rule(c, p.kind)
            for _ in range(2):
                mutated = list(c)
                r = rng.randrange(15)
                mutated[r] = (mutated[r] + 1) % (5 if r < 13 else 2)
                self.assert_rule(tuple(mutated))

    def test_rank_multiset_exhaustion(self):
        # All multiplicities on four separated ranks plus both jokers.
        for counts in itertools.product(range(5), repeat=4):
            for jokers in ((0, 0), (0, 1), (1, 0), (1, 1)):
                self.assert_rule(cards(*zip((1, 3, 12, 13, 14, 15), (*counts, *jokers))))

    def test_random_selections(self):
        rng = random.Random(1945)
        deck = [r for r in range(13) for _ in range(4)] + [13, 14]
        for _ in range(300):
            sample = rng.sample(deck, rng.randrange(1, 21))
            c = tuple(sample.count(r) for r in range(15))
            self.assert_rule(c)

    def test_ai_responds_with_smallest_matching_move_before_bomb(self):
        hand = cards((1, 4), (6, 2), (7, 2), (14, 1), (15, 1))
        old = rules.Move(2, 4, 1, 2)
        move = self.vm.evaluate("choose_move", hand, old)
        self.assertEqual(move, rules.Move(2, 6, 1, 2))
        self.assertEqual(self.vm.selected(), rules.choose_move(hand, old))
        old = rules.Move(2, 13, 1, 2)
        self.assertEqual(self.vm.evaluate("choose_move", hand, old).kind, 13)
        self.assertEqual(self.vm.evaluate("choose_move", hand, rules.Move(13, 13, 1, 4)).kind, 14)
        self.assertEqual(self.vm.evaluate("choose_move", hand, rules.Move(14, 15, 1, 2)).kind, 0)

    def test_full_scripted_games(self):
        rng = random.Random(1936)
        deck = [r for r in range(13) for _ in range(4)] + [13, 14]
        for game in range(24):
            rng.shuffle(deck)
            hands = [[part.count(r) for r in range(15)] for part in (deck[:20], deck[20:37], deck[37:])]
            turn, previous, passes = 0, rules.Move(), 0
            played = [0] * 15
            for step in range(163):
                hand = tuple(hands[turn])
                move = self.vm.evaluate("choose_move", hand, previous)
                selected = self.vm.selected()
                self.assertEqual(selected, rules.choose_move(hand, previous), (game, step, previous, hand))
                self.assertEqual(move, rules.classify(selected))
                self.assertTrue(all(0 <= s <= h for s, h in zip(selected, hand)))
                if move.kind:
                    self.assertTrue(move.beats(previous), (game, step, move, previous))
                    self.assertTrue(self.vm.vars[rules.v("beats")])
                    hands[turn] = [h - s for h, s in zip(hand, selected)]
                    played = [p + s for p, s in zip(played, selected)]
                    previous, passes = move, 0
                    self.assertEqual([played[r] + sum(h[r] for h in hands) for r in range(15)], [4] * 13 + [1, 1])
                    if not sum(hands[turn]):
                        break
                else:
                    self.assertTrue(previous.kind, "AI must find a move on a free lead")
                    passes += 1
                    if passes == 2:
                        previous, passes = rules.Move(), 0
                turn = (turn + 1) % 3
            else:
                self.fail(f"Game {game} did not finish within finite card/pass bound")

    def test_generator_public_effects_and_names(self):
        self.assertLess(len(rules.PATTERNS), 400)
        self.assertEqual(set(self.vm.effects), {rules.v(s) for s in ("compare", "classify", "ai_offer", "choose_move")})
        text = next(iter(rules.outputs().values()))
        self.assertNotIn("random", text)
        self.assertNotIn("every_country", text)
        self.assertNotIn("while", text)


if __name__ == "__main__":
    unittest.main()
