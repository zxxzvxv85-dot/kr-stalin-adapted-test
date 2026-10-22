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
        stem = "a" if name in ("choose_move", "choose_team_move") else "s"
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
        self.assertEqual(set(self.vm.effects), {rules.v(s) for s in (
            "compare", "classify", "ai_offer", "choose_move", "strategy_offer", "choose_strategy_move", "choose_team_move")})
        text = next(iter(rules.outputs().values()))
        self.assertNotIn("random", text)
        self.assertNotIn("every_country", text)
        self.assertNotIn("while", text)


class TeamMoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vm = ScriptVM()

    def team_move(self, hand, previous, *, turn=2, landlord=3, last_player=1,
                  remaining=(5, 7, 8), passes=0):
        self.vm.vars.update({rules.v(k): value for k, value in (
            ("turn", turn), ("landlord", landlord), ("last_player", last_player),
            ("passes", passes), *[(f"count_{s}", n) for s, n in enumerate(remaining, 1)])})
        expected = rules.choose_team_move(hand, previous, turn=turn, landlord=landlord,
                                         last_player=last_player, remaining=remaining, passes=passes)
        move = self.vm.evaluate("choose_team_move", hand, previous)
        self.assertEqual(self.vm.selected(), expected)
        self.assertEqual(move, rules.classify(expected))
        self.assertTrue(all(0 <= selected <= count for selected, count in zip(expected, hand)))
        self.assertEqual(bool(self.vm.vars[rules.v("beats")]), move.beats(previous))
        self.assertEqual(tuple(self.vm.vars[rules.v(f"a_{r}")] for r in range(1, 16)), hand)
        return expected

    def test_ordinary_teammate_lead_is_held_in_all_seats(self):
        hand = cards((4, 1), (8, 2), (13, 4), (14, 1), (15, 1))
        for turn, landlord, mate in itertools.permutations((1, 2, 3)):
            for previous in (rules.Move(1, 2, 1, 1), rules.Move(2, 5, 1, 2), rules.Move(13, 1, 1, 4)):
                self.assertTrue(any(rules.choose_move(hand, previous)))
                self.assertEqual(self.team_move(hand, previous, turn=turn, landlord=landlord,
                                               last_player=mate), cards())

    def test_landlord_and_farmer_answering_landlord_keep_normal_picker(self):
        hand = cards((5, 1), (7, 2), (12, 4), (14, 1), (15, 1))
        previous = rules.Move(2, 4, 1, 2)
        expected = rules.choose_move(hand, previous)
        self.assertEqual(self.team_move(hand, previous, landlord=2), expected)
        self.assertEqual(self.team_move(hand, previous, landlord=1), expected)

    def test_free_lead_and_invalid_context_keep_normal_picker(self):
        hand = cards((3, 1), (4, 3), (7, 2))
        self.assertEqual(self.team_move(hand, rules.Move()), rules.choose_move(hand))
        previous = rules.Move(1, 1, 1, 1)
        self.assertEqual(self.team_move(hand, previous, last_player=0), rules.choose_move(hand, previous))
        self.assertEqual(self.team_move(hand, previous, landlord=0), rules.choose_move(hand, previous))

    def test_finishing_hand_always_wins_including_bomb_and_rocket(self):
        previous = rules.Move(1, 3, 1, 1)
        for hand in (cards((8, 1)), cards((9, 4)), cards((14, 1), (15, 1))):
            self.assertEqual(self.team_move(hand, previous, remaining=(1, sum(hand), 1), passes=1), hand)

    def test_complex_whole_hand_finish_overrides_team_holds_and_feeding(self):
        for hand in (cards((8, 4), (11, 2)), cards((8, 3), (9, 3), (11, 1), (12, 1)),
                     cards(*[(r, 1) for r in range(8, 13)]), cards((8, 3), (9, 3), (11, 2), (12, 2))):
            whole = rules.classify(hand)
            previous = rules.Move(whole.kind, whole.power - 1, whole.length, whole.n)
            self.assertEqual(self.team_move(hand, previous, remaining=(1, sum(hand), 1), passes=1), hand)
            self.assertEqual(self.team_move(hand, rules.Move(), landlord=1,
                                           remaining=(5, sum(hand), 1)), hand)

    def test_next_landlord_single_blocks_with_highest_ordinary_card(self):
        hand = cards((4, 1), (9, 2), (12, 4), (13, 1), (14, 1), (15, 1))
        self.assertEqual(self.team_move(hand, rules.Move(1, 3, 1, 1), remaining=(5, sum(hand), 1)),
                         cards((13, 1)))

    def test_next_landlord_pair_blocks_high_without_splitting_bomb(self):
        hand = cards((8, 2), (10, 2), (11, 3), (13, 4), (14, 1), (15, 1))
        self.assertEqual(self.team_move(hand, rules.Move(2, 6, 1, 2), remaining=(5, sum(hand), 2)),
                         cards((11, 2)))

    def test_blocking_wraps_seat_three_to_one(self):
        hand = cards((4, 1), (11, 1), (13, 1))
        self.assertEqual(self.team_move(hand, rules.Move(1, 3, 1, 1), turn=3, landlord=1,
                                       last_player=2, remaining=(1, 5, sum(hand))), cards((13, 1)))

    def test_landlord_already_passed_does_not_trigger_takeover(self):
        hand = cards((4, 1), (13, 1), (14, 1), (15, 1))
        previous = rules.Move(1, 3, 1, 1)
        self.assertEqual(self.team_move(hand, previous, turn=3, landlord=2, last_player=1,
                                       remaining=(5, 1, sum(hand)), passes=1), cards())
        # Even an inconsistent hand-crafted save cannot use stale pass history
        # to claim the landlord still needs an emergency block.
        self.assertEqual(self.team_move(hand, previous, remaining=(5, sum(hand), 1), passes=1), cards())

    def test_preserves_almost_finished_teammate_strong_lead(self):
        hand = cards((4, 1), (13, 2), (15, 1))
        for kind in (1, 2):
            for left in (1, 2):
                self.assertEqual(self.team_move(hand, rules.Move(kind, 12, 1, kind),
                                               remaining=(left, sum(hand), kind)), cards())

    def test_emergency_does_not_waste_jokers_or_bombs(self):
        hand = cards((1, 1), (13, 4), (14, 1), (15, 1))
        for kind in (1, 2):
            self.assertEqual(self.team_move(hand, rules.Move(kind, 12, 1, kind),
                                           remaining=(5, sum(hand), kind)), cards())

    def test_near_finish_requires_matching_pattern_and_next_seat(self):
        hand = cards((3, 1), (7, 3), (13, 2))
        self.assertEqual(self.team_move(hand, rules.Move(1, 2, 1, 1), remaining=(5, sum(hand), 2)), cards())
        self.assertEqual(self.team_move(hand, rules.Move(2, 2, 1, 2), remaining=(5, sum(hand), 1)), cards())
        self.assertEqual(self.team_move(hand, rules.Move(3, 2, 1, 3), remaining=(5, sum(hand), 3)), cards())
        self.assertEqual(self.team_move(hand, rules.Move(1, 2, 1, 1), turn=3, landlord=2,
                                       last_player=1, remaining=(5, 1, sum(hand))), cards())

    def test_opponent_private_cards_never_affect_the_move(self):
        hand, previous = cards((3, 1), (8, 2), (13, 1)), rules.Move(1, 2, 1, 1)
        args = dict(remaining=(5, sum(hand), 1))
        expected = self.team_move(hand, previous, **args)
        for private in (0, 1, 3, 4, 99):
            self.vm.vars.update({rules.v(f"h_{s}_{r}"): private for s in (1, 3) for r in range(1, 16)})
            self.vm.vars.update({rules.v(f"owner_{c}"): private for c in range(1, 55)})
            self.assertEqual(self.team_move(hand, previous, **args), expected)
        # Check the generated call graph as well as fixtures: no path can read
        # hidden hand ranks/owners. Team policy's only new hand input is counts.
        generated = next(iter(rules.outputs().values()))
        self.assertNotRegex(generated, r"RUS_ddz_(?:h_[123]_\d+|owner_\d+)")


    def test_next_enemy_reports_one_prefers_non_single_lead(self):
        hand = cards((2, 1), (7, 2), (13, 1))
        selected = self.team_move(hand, rules.Move(), remaining=(5, sum(hand), 1))
        self.assertEqual(selected, cards((7, 2)))

    def test_only_singles_lead_high_against_next_enemy_one_card(self):
        hand = cards((2, 1), (7, 1), (13, 1))
        self.assertEqual(self.team_move(hand, rules.Move(), remaining=(5, sum(hand), 1)), cards((13, 1)))

    def test_next_enemy_reports_two_avoids_pair_lead(self):
        hand = cards((2, 2), (13, 1))
        selected = self.team_move(hand, rules.Move(), remaining=(5, sum(hand), 2))
        self.assertEqual(rules.classify(selected).kind, 1)

    def test_free_lead_feeds_next_farmer_with_one_card(self):
        hand = cards((1, 4), (5, 1), (7, 2), (14, 1), (15, 1))
        selected = self.team_move(hand, rules.Move(), turn=2, landlord=1, last_player=2,
                                  remaining=(5, sum(hand), 1))
        self.assertEqual(selected, cards((5, 1)))
        # A complete finishing combination takes priority over giving the lead.
        hand = cards((7, 3), (8, 2))
        self.assertEqual(self.team_move(hand, rules.Move(), turn=2, landlord=1,
                                       remaining=(5, 5, 1)), hand)

    def test_two_card_teammate_not_assumed_to_have_pair(self):
        hand = cards((1, 2), (4, 3), (7, 1))
        selected = self.team_move(hand, rules.Move(), turn=2, landlord=1, remaining=(5, 6, 2))
        self.assertEqual(rules.classify(selected).kind, 5)

    def test_follow_enemy_high_single_and_pair_for_urgent_next_seat(self):
        hand = cards((4, 1), (7, 2), (12, 3), (13, 4), (14, 1), (15, 1))
        for turn, landlord, last in ((2, 3, 3), (2, 2, 1)):
            for kind in (1, 2):
                selected = self.team_move(hand, rules.Move(kind, 3, 1, kind), turn=turn,
                                          landlord=landlord, last_player=last, remaining=(5, sum(hand), kind))
                self.assertEqual(selected, cards((12, kind)))

    def test_normal_response_prefers_intact_single_and_pair(self):
        hand = cards((4, 2), (7, 3), (10, 1), (11, 2), (13, 4), (14, 1), (15, 1))
        # Previous landlord is not the actor's immediate next seat here.
        self.assertEqual(self.team_move(hand, rules.Move(1, 3, 1, 1), landlord=1), cards((10, 1)))
        self.assertEqual(self.team_move(hand, rules.Move(2, 5, 1, 2), landlord=1), cards((11, 2)))

    def test_nonurgent_response_can_pass_to_preserve_bomb_and_rocket(self):
        hand = cards((1, 1), (10, 4), (14, 1), (15, 1))
        self.assertEqual(self.team_move(hand, rules.Move(1, 5, 1, 1), landlord=1), cards())
        # An enemy close to going out justifies committing a whole bomb;
        # even then no single/pair is split from it or from the rocket.
        selected = self.team_move(hand, rules.Move(1, 5, 1, 1), landlord=1, remaining=(1, sum(hand), 7))
        self.assertEqual(selected, cards((10, 4)))
        self.assertEqual(self.team_move(cards((10, 4)), rules.Move(1, 5, 1, 1), landlord=1), cards((10, 4)))

    def test_landlord_counts_both_farmer_enemies_for_bomb_urgency(self):
        hand = cards((1, 1), (10, 4), (14, 1), (15, 1))
        previous = rules.Move(1, 5, 1, 1)
        self.assertEqual(self.team_move(hand, previous, landlord=2, remaining=(5, sum(hand), 5)), cards())
        self.assertEqual(self.team_move(hand, previous, landlord=2, remaining=(1, sum(hand), 5)), cards((10, 4)))
        self.assertEqual(self.team_move(hand, previous, landlord=2, remaining=(5, sum(hand), 2)), cards((10, 4)))

    def test_team_context_does_not_leak_to_hint_picker(self):
        hand = cards((4, 2), (10, 1), (13, 4))
        previous = rules.Move(1, 3, 1, 1)
        self.team_move(hand, previous, landlord=1)
        self.vm.evaluate("choose_move", hand, previous)
        self.assertEqual(self.vm.selected(), rules.choose_move(hand, previous))
        self.assertEqual(self.vm.selected(), cards((4, 1)))

    def test_safe_single_wing_not_hidden_by_lower_complete_bomb(self):
        # 4444 + 777 + J can answer 555 + K with 777 + J, without
        # rejecting the whole core merely because 4 was the lowest accessory.
        hand = cards((2, 4), (5, 3), (9, 1))
        previous = rules.Move(4, 3, 1, 4)
        self.assertEqual(self.team_move(hand, previous, landlord=1, remaining=(7, 8, 6)),
                         cards((5, 3), (9, 1)))
        self.vm.evaluate("choose_move", hand, previous)
        self.assertEqual(self.vm.selected(), rules.choose_move(hand, previous))
        self.assertEqual(self.vm.selected(), cards((2, 1), (5, 3)))

    def test_safe_pair_wing_not_hidden_by_lower_complete_bomb(self):
        hand = cards((2, 4), (5, 3), (9, 2))
        self.assertEqual(self.team_move(hand, rules.Move(5, 3, 1, 5), landlord=1,
                                       remaining=(7, 9, 6)), cards((5, 3), (9, 2)))

    def test_wing_selection_never_splits_held_rocket(self):
        hand = cards((5, 3), (14, 1), (15, 1))
        # No safe single wing exists. The nonurgent AI must pass instead of
        # splitting the rocket, and ordinary bomb resource preservation applies.
        self.assertEqual(self.team_move(hand, rules.Move(4, 3, 1, 4), landlord=1,
                                       remaining=(7, 5, 6)), cards())

    def test_rocket_as_two_wings_retains_whole_hand_and_safe_variant(self):
        for hand in (cards((5, 4), (14, 1), (15, 1)),
                     cards((5, 3), (6, 3), (14, 1), (15, 1))):
            whole = rules.classify(hand)
            previous = rules.Move(whole.kind, whole.power - 1, whole.length, whole.n)
            self.assertEqual(self.team_move(hand, previous, remaining=(5, sum(hand), 7)), hand)
        # A smaller lone wing must not prevent choosing both jokers together
        # when the two-wing pattern has no other safe complete allocation.
        hand = cards((3, 1), (5, 3), (6, 3), (14, 1), (15, 1))
        self.assertEqual(self.team_move(hand, rules.Move(9, 4, 2, 8), landlord=1,
                                       remaining=(7, 9, 6)), cards((5, 3), (6, 3), (14, 1), (15, 1)))

    def test_full_team_games_with_public_state_and_card_conservation(self):
        rng = random.Random(20261022)
        deck = [r for r in range(13) for _ in range(4)] + [13, 14]
        voluntary_passes = 0
        for game in range(18):
            rng.shuffle(deck)
            hands = [[part.count(r) for r in range(15)] for part in (deck[:20], deck[20:37], deck[37:])]
            turn, previous, passes, last_player = 1, rules.Move(), 0, 0
            played = [0] * 15
            for step in range(163):
                hand = tuple(hands[turn - 1])
                selected = self.team_move(hand, previous, turn=turn, landlord=1, last_player=last_player,
                                          remaining=tuple(map(sum, hands)), passes=passes)
                move = rules.classify(selected)
                if move.kind:
                    self.assertTrue(move.beats(previous))
                    hands[turn - 1] = [h - c for h, c in zip(hand, selected)]
                    played = [p + c for p, c in zip(played, selected)]
                    self.assertEqual([played[r] + sum(h[r] for h in hands) for r in range(15)], [4] * 13 + [1, 1])
                    previous, last_player, passes = move, turn, 0
                    if not sum(hands[turn - 1]):
                        break
                else:
                    self.assertTrue(previous.kind, "A free lead always plays at least one card")
                    if any(rules.choose_move(hand, previous)):
                        voluntary_passes += 1
                    passes += 1
                    if passes == 2:
                        previous, last_player, passes = rules.Move(), 0, 0
                turn = turn % 3 + 1
            else:
                self.fail(f"Team game {game} did not finish within finite card/pass bound")
        self.assertGreater(voluntary_passes, 0)


if __name__ == "__main__":
    unittest.main()
