"""Actual emitted-script lifecycle tests for the development card table."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import unittest

import doudizhu_game as game
import doudizhu_rules as rules
from doudizhu_script_model import ScriptModel, load_effects

ROOT = Path(__file__).resolve().parents[1]
EFFECTS = load_effects(game.effects(), next(iter(rules.outputs().values())))


def get(model, name):
    return int(model.vars.get(game.v(name), 0))


def setv(model, **values):
    model.vars.update({game.v(k): v for k, v in values.items()})


def call(model, name):
    model.call(game.v(name))


def audit(model):
    owners = [get(model, f"owner_{i}") for i in range(1, 55)]
    assert set(owners) <= {1, 2, 3, 4, 9}, Counter(owners)
    assert not any(get(model, f"deck_{i}") for i in range(1, 55))
    for seat in range(1, 4):
        cards = [c for c in range(1, 55) if owners[c-1] == seat]
        assert len(cards) == get(model, f"count_{seat}") <= 20
        counts = Counter(game.rank(c) for c in cards)
        assert all(counts[r] == get(model, f"h_{seat}_{r}") for r in range(1, 16))
    if get(model, "phase") == 2:
        assert 4 not in owners
    if get(model, "phase") in (1, 2):
        assert get(model, "turn") == 1, "Computer sequence failed to return to player"
    assert len({get(model, f"bottom_{s}") for s in range(1, 4)}) == 3
    for i in range(1, 21):
        card = get(model, f"table_{i}")
        if card:
            assert owners[card-1] == 9
    played_counts = Counter(game.rank(card) for card,owner in enumerate(owners,1) if owner==9)
    assert all(get(model,f"seen_{r}")==played_counts[r] for r in range(1,16))
    snapshots = []
    for seat in (1, 2, 3):
        cards = [get(model, f"public_card_{seat}_{i}") for i in range(1, 21)]
        count = get(model, f"public_n_{seat}")
        assert all(cards[:count]) and not any(cards[count:])
        assert all(owners[c-1] == 9 for c in cards if c)
        ranks = Counter(game.rank(c) for c in cards if c)
        assert all(ranks[r] == get(model, f"play_{seat}_{r}") for r in range(1, 16))
        snapshots += [c for c in cards if c]
    assert len(set(snapshots)) == len(snapshots)


class LifecycleTests(unittest.TestCase):
    def model(self, seed=1):
        return ScriptModel(EFFECTS, seed)

    def playable(self, seed=1):
        model = self.model(seed)
        call(model, "new_game")
        if get(model, "phase") == 1:
            call(model, "bid_3")
        self.assertEqual(get(model, "phase"), 2)
        audit(model)
        return model

    def test_animation_bank_restarts_only_for_new_game_or_successful_play(self):
        model=self.playable()
        self.assertEqual(get(model,'deal_bank'),1)
        before=[get(model,f'public_bank_{seat}') for seat in (1,2,3)]
        call(model,'hint')
        self.assertEqual([get(model,f'public_bank_{seat}') for seat in (1,2,3)],before)
        for seat in (1,2,3):
            # Legal single-card plays replace even equal-size public piles.
            for attempt in range(2):
                card=next(c for c in range(1,55) if get(model,f'owner_{c}')==seat)
                setv(model,turn=seat,last_kind=0,phase=2)
                call(model,'clear_flags')
                setv(model,**{f's_{game.rank(card)}':1,f'sel_{card}':1})
                call(model,'classify')
                previous=get(model,f'public_bank_{seat}')
                other={s:get(model,f'public_bank_{s}') for s in (1,2,3) if s!=seat}
                call(model,'commit_play')
                self.assertEqual(get(model,f'public_bank_{seat}'),1-previous)
                self.assertEqual({s:get(model,f'public_bank_{s}') for s in other},other)
                previous=get(model,f'public_bank_{seat}')
                call(model,'commit_pass')
                self.assertEqual(get(model,f'public_bank_{seat}'),previous)
        setv(model,phase=3)
        call(model,'new_game')
        self.assertEqual(get(model,'deal_bank'),0)
        audit(model)

    def test_deck_no_replacement_and_conservation(self):
        model = self.model()
        for seed in range(100):
            model.rng.seed(seed)
            call(model, "deal")
            self.assertEqual([get(model, f"count_{s}") for s in range(1, 4)], [17]*3)
            self.assertEqual(sum(get(model, f"owner_{i}") == 4 for i in range(1, 55)), 3)
            self.assertEqual(len({get(model, f"bottom_{s}") for s in range(1, 4)}), 3)

    def test_not_enough_people_and_active_new_game_guard(self):
        model = self.model()
        model.vars["fixture_candidates"] = 2
        call(model, "new_game")
        self.assertEqual(get(model, "phase"), 0)
        self.assertEqual(get(model, "message"), 5)
        self.assertNotIn(game.v("owner_1"), model.vars)
        model = self.playable()
        before = dict(model.vars)
        call(model, "new_game")
        self.assertEqual(before, model.vars)

    def test_distinct_people_each_round(self):
        model = self.model()
        seen = set()
        for _ in range(25):
            setv(model, phase=0)
            call(model, "new_game")
            people = tuple(get(model, f"person_{s}") for s in range(1, 4))
            self.assertEqual(len(set(people)), 3)
            seen.add(people)
        self.assertGreater(len(seen), 5)

    def test_open_and_close_do_not_redeal(self):
        model = self.playable()
        owners = [get(model, f"owner_{c}") for c in range(1, 55)]
        people = [get(model, f"person_{s}") for s in range(1, 4)]
        model.flags.discard("RUS_ddz_open")
        call(model, "open")
        self.assertIn("RUS_ddz_open", model.flags)
        self.assertEqual(owners, [get(model, f"owner_{c}") for c in range(1, 55)])
        self.assertEqual(people, [get(model, f"person_{s}") for s in range(1, 4)])

    def test_auction_all_pass_and_strict_higher_bid(self):
        model = self.model()
        call(model, "deal")
        setv(model, phase=1, turn=1, bid=0, bidder=0, bids_taken=0, bid_value=0)
        for _ in range(3):
            call(model, "commit_bid")
        self.assertEqual(get(model, "phase"), 3)
        self.assertEqual(get(model, "message"), 4)
        self.assertEqual(get(model, "winner"), 0)
        setv(model, phase=1, turn=1, bid=2, bidder=2, bids_taken=1)
        before = dict(model.vars)
        call(model, "bid_1")
        call(model, "bid_2")
        self.assertEqual(before, model.vars)
        setv(model, bid_value=3)
        call(model, "commit_bid")
        self.assertEqual(get(model, "landlord"), 1)
        self.assertEqual(get(model, "count_1"), 20)

    def test_two_passes_restore_lead_and_clear_target(self):
        model = self.playable()
        setv(model, turn=2, last_kind=1, last_power=7, last_n=1, last_len=1, last_player=1, passes=0)
        call(model, "commit_pass")
        self.assertEqual(get(model, "last_kind"), 1)
        self.assertEqual(get(model, "turn"), 3)
        call(model, "commit_pass")
        self.assertEqual(get(model, "last_kind"), 0)
        self.assertEqual(get(model, "turn"), 1)
        self.assertEqual(get(model, "passes"), 0)

    def test_round_action_stamps_survive_passes_but_not_new_lead(self):
        model = self.playable()
        setv(model, turn=1, last_kind=0, trick=5, trick_closed=1, passes=0)
        call(model, "clear_flags")
        card = min(c for c in range(1, 55) if get(model, f"owner_{c}") == 1)
        call(model, f"select_{card}")
        call(model, "read_selection")
        call(model, "commit_play")
        self.assertEqual(get(model, "trick"), 6)
        self.assertEqual(get(model, "trick_closed"), 0)
        self.assertEqual(get(model, "action_trick_1"), 6)
        call(model, "commit_pass")
        call(model, "commit_pass")
        self.assertEqual(get(model, "trick"), 6)
        self.assertEqual(get(model, "trick_closed"), 1)
        self.assertEqual([get(model, f"action_{s}") for s in (1, 2, 3)], [1, 2, 2])
        self.assertEqual([get(model, f"action_trick_{s}") for s in (1, 2, 3)], [6, 6, 6])
        card = min(c for c in range(1, 55) if get(model, f"owner_{c}") == 1)
        call(model, f"select_{card}")
        call(model, "read_selection")
        call(model, "commit_play")
        self.assertEqual(get(model, "trick"), 7)
        self.assertEqual(get(model, "trick_closed"), 0)
        self.assertEqual(get(model, "action_trick_1"), 7)
        self.assertEqual([get(model, f"action_trick_{s}") for s in (2, 3)], [6, 6])
        # Merely selecting or hinting must not count as a public action.
        setv(model, turn=1)
        before = [get(model, f"action_trick_{s}") for s in (1, 2, 3)]
        call(model, "hint")
        self.assertEqual(before, [get(model, f"action_trick_{s}") for s in (1, 2, 3)])

    def test_invalid_play_pass_and_hint_are_non_destructive(self):
        model = self.playable()
        setv(model, last_kind=0, last_n=0, last_player=0)
        call(model, "clear_flags")
        owners = [get(model, f"owner_{c}") for c in range(1, 55)]
        call(model, "player_play")
        self.assertEqual(get(model, "message"), 1)
        call(model, "player_pass")
        self.assertEqual(get(model, "message"), 3)
        call(model, "hint")
        self.assertGreater(get(model, "selected_count"), 0)
        self.assertEqual(get(model, "selection_legal"), 1)
        self.assertEqual(owners, [get(model, f"owner_{c}") for c in range(1, 55)])
        # Opponents' cards cannot be selected through directly invoked callbacks.
        for c in range(1, 55):
            if get(model, f"owner_{c}") != 1:
                call(model, f"select_{c}")
                self.assertEqual(get(model, f"sel_{c}"), 0)

    def test_each_seat_keeps_physical_play_until_its_next_successful_play(self):
        model = self.model()
        setv(model, phase=2, turn=1, landlord=1, trick=0)
        # Give each player distinct suits and several spare cards. The public
        # snapshots must preserve actual suits, not reconstruct them by rank.
        for c in range(1, 55):
            setv(model, **{f"owner_{c}": (c - 1) % 3 + 1})
        call(model, "recount")

        def play(seat, selected):
            setv(model, turn=seat)
            call(model, "clear_flags")
            for card in selected:
                if seat == 1:
                    call(model, f"select_{card}")
                else:
                    key = f"s_{game.rank(card)}"
                    setv(model, **{key: get(model, key) + 1})
            call(model, "read_selection" if seat == 1 else "classify")
            self.assertEqual(get(model, "beats"), 1)
            call(model, "commit_play")

        def snapshot(seat):
            return tuple(get(model, f"public_card_{seat}_{i}") for i in range(1, 21))

        play(1, [1, 4])  # pair of threes, different physical suits
        first = snapshot(1)
        self.assertEqual(first[:3], (1, 4, 0))
        call(model, "commit_pass")
        call(model, "commit_pass")
        self.assertEqual(get(model, "table_n"), 0)
        self.assertEqual(snapshot(1), first)
        self.assertEqual(get(model, "public_trick_1"), 1)
        play(1, [7])  # same player replaces a pair with a single; tail clears
        self.assertEqual(snapshot(1), (7,) + (0,) * 19)
        play(2, [11])
        play(3, [15])
        saved = [snapshot(s) for s in (1, 2, 3)]
        self.assertEqual([x[0] for x in saved], [7, 11, 15])
        call(model, "commit_pass")
        call(model, "commit_pass")
        self.assertEqual([snapshot(s) for s in (1, 2, 3)], saved)
        play(3, [18])
        self.assertEqual(snapshot(3), (18,) + (0,) * 19)
        self.assertEqual([snapshot(s) for s in (1, 2)], saved[:2])
        # Isolate new-game reset from automatic bidding/playing that could
        # legitimately populate a fresh snapshot during the same call.
        model.effects = {**model.effects, **load_effects("RUS_ddz_process_ai = { }")}
        setv(model, phase=3)
        call(model, "new_game")
        self.assertEqual([snapshot(s) for s in (1, 2, 3)], [(0,) * 20] * 3)
        self.assertEqual([get(model, f"public_n_{s}") for s in (1, 2, 3)], [0] * 3)

    def test_public_piles_center_each_visible_row_without_overlap(self):
        model = self.model()
        for count in range(1, 21):
            setv(model, **{f"public_n_{s}": count for s in (1, 2, 3)})
            call(model, "refresh")
            for seat, center, columns, step in ((1, 500, 20, 27), (2, 355, 10, 22), (3, 645, 10, 22)):
                for row in range((count - 1) // columns + 1):
                    row_count = min(columns, count - row * columns)
                    positions = [model.vars[game.v(f"public_x_{seat}_{row * columns + i}")]
                                 for i in range(1, row_count + 1)]
                    self.assertEqual((positions[0] + positions[-1] + 34) / 2, center)
                    self.assertTrue(all(b - a == step for a, b in zip(positions, positions[1:])))
                    self.assertGreaterEqual(positions[0], 220 if seat != 3 else 510)
                    self.assertLessEqual(positions[-1] + 34, 490 if seat == 2 else 780)

    def test_physical_selected_suit_is_removed(self):
        model = self.playable()
        call(model, "clear_flags")
        setv(model, last_kind=0, last_n=0, last_player=0)
        card = max(c for c in range(1, 55) if get(model, f"owner_{c}") == 1)
        call(model, f"select_{card}")
        call(model, "read_selection")
        self.assertEqual(get(model, "beats"), 1)
        call(model, "commit_play")
        self.assertEqual(get(model, f"owner_{card}"), 9)
        self.assertEqual(get(model, "table_1"), card)
        self.assertEqual(get(model, "action_1"), 1)
        self.assertEqual(get(model, f"play_1_{game.rank(card)}"), 1)
        self.assertEqual(sum(get(model, f"play_1_{r}") for r in range(1, 16)), 1)
        self.assertTrue(all(get(model, f"sel_{c}") == 0 for c in range(1, 55)))

    def test_abandon_requires_second_click_and_new_round_resets(self):
        model = self.playable()
        call(model, "abandon")
        self.assertEqual(get(model, "phase"), 2)
        self.assertEqual(get(model, "message"), 7)
        call(model, "abandon")
        self.assertEqual(get(model, "phase"), 3)
        self.assertEqual(get(model, "winner"), 0)
        call(model, "new_game")
        self.assertIn(get(model, "phase"), (1, 2))
        audit(model)

    def test_full_gui_click_lifecycle(self):
        total_turns = 0
        winners = set()
        for seed in range(24):
            model = self.playable(seed)
            turns = 0
            while get(model, "phase") == 2:
                audit(model)
                owners_before = Counter(get(model, f"owner_{c}") for c in range(1, 55))
                call(model, "hint")
                if get(model, "selected_count"):
                    self.assertEqual(get(model, "selection_legal"), 1)
                    call(model, "player_play")
                    owners_after = Counter(get(model, f"owner_{c}") for c in range(1, 55))
                    self.assertGreater(owners_after[9], owners_before[9])
                else:
                    self.assertGreater(get(model, "last_kind"), 0)
                    call(model, "player_pass")
                turns += 1
                self.assertLess(turns, 100)
            audit(model)
            winner = get(model, "winner")
            self.assertIn(winner, (1, 2, 3))
            self.assertEqual(get(model, f"count_{winner}"), 0)
            winners.add(winner)
            total_turns += turns
        self.assertEqual(winners, {1, 2, 3})
        print(f"Executed 24 complete GUI-action games, {total_turns} human turns; all seats won at least once.")

    def test_isolated_script_vocabulary(self):
        # Any added campaign-mutating effects must get explicit review.
        text = game.effects() + next(iter(rules.outputs().values()))
        forbidden = ("add_political_power", "add_stability", "country_event", "load_focus_tree", "add_ideas", "on_daily", "set_global_flag")
        for token in forbidden:
            self.assertNotIn(token, text)
        for name in re.findall(r"(?:set|add_to|subtract_from|multiply|divide)_variable\s*=\s*\{\s*(\w+)", text):
            self.assertTrue(name.startswith("RUS_ddz_"), name)

    def test_native_gui_callbacks_end_to_end(self):
        import doudizhu_gui
        from hoi4_politics_blocks import parse
        gui = parse(doudizhu_gui.outputs()["common/scripted_guis/RUS_doudizhu.txt"])[0].v[0]
        callbacks = {n.k: n for n in gui.one("effects").v}
        for seed in (3, 7, 15):
            model = self.model(seed)
            call(model, "open")
            model.run(callbacks["ddz_new_click"].v)
            if get(model, "phase") == 1:
                model.run(callbacks["ddz_bid_3_click"].v)
            self.assertEqual(get(model, "phase"), 2, "Native bid callback must allow current player")
            for _ in range(100):
                if get(model, "phase") == 3:
                    break
                model.run(callbacks["ddz_hint_click"].v)
                action = "ddz_play_click" if get(model, "selected_count") else "ddz_pass_click"
                model.run(callbacks[action].v)
                audit(model)
            self.assertEqual(get(model, "phase"), 3)
            self.assertGreater(get(model, "winner"), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
