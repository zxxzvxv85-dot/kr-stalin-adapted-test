"""Finite, country-scoped Dou Dizhu rules and computer moves.

Public effect protocol (all variables have prefix RUS_ddz_):
  classify: s_1..s_15 -> valid, beats, kind, power, len, n.
  choose_move: a_1..a_15 and last_* -> s_*, then classify outputs.
Ranks are 3,4,5,6,7,8,9,10,J,Q,K,A,2,small joker,big joker.
last_kind=0 is a free lead. Inputs are never consumed by these effects.

House rules: no 2/jokers in chains; airplane cores contain exactly three
selected cards per rank; single wings can contain a pair, but no three/four
of one rank and no core cards; pair wings have distinct ranks. Four plus two
singles may use a pair. Both jokers may serve as two single wings. A rocket
is always the two jokers. There is no wild card, bidding or score code here.

The emitted AI considers fewer than 400 fixed core patterns, fills wings in
ascending rank order, and never reads opponents' hands. It plays a complete
hand immediately when possible, otherwise favors the largest non-bomb lead
and the cheapest matching response, then bombs, then the rocket. There is
no recursive search, dynamic variable name, on_action or time-dependent work.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PREFIX = "RUS_ddz_"
KIND_NAMES = {
    0: "无效牌型", 1: "单张", 2: "对子", 3: "三张", 4: "三带一",
    5: "三带二", 6: "顺子", 7: "连对", 8: "飞机", 9: "飞机带单张",
    10: "飞机带对子", 11: "四带二", 12: "四带两对", 13: "炸弹", 14: "王炸",
}


@dataclass(frozen=True)
class Move:
    kind: int = 0
    power: int = 0
    length: int = 0
    n: int = 0

    def beats(self, previous: "Move") -> bool:
        if not self.kind:
            return False
        if not previous.kind:
            return True
        if self.kind == 14:
            return previous.kind != 14
        if previous.kind == 14:
            return False
        if self.kind == 13 and previous.kind != 13:
            return True
        return (self.kind == previous.kind and self.length == previous.length
                and self.n == previous.n and self.power > previous.power)


def classify(counts: Iterable[int]) -> Move:
    """Independent reference classifier, including count/deck boundary checks."""
    c = tuple(counts)
    n = sum(c)
    if len(c) != 15 or not 1 <= n <= 20 or any(
        not isinstance(v, int) or v < 0 or v > (4 if r < 13 else 1)
        for r, v in enumerate(c)
    ):
        return Move(n=n)
    occupied = [r + 1 for r, v in enumerate(c) if v]
    hist = {v: sum(x == v for x in c) for v in (1, 2, 3, 4)}
    if n == 2 and c[13:] == (1, 1):
        return Move(14, 15, 1, 2)
    if len(occupied) == 1:
        return Move({1: 1, 2: 2, 3: 3, 4: 13}[n], occupied[0], 1, n)
    if n == 4 and hist[3] == hist[1] == 1:
        return Move(4, c.index(3) + 1, 1, n)
    if n == 5 and hist[3] == hist[2] == 1:
        return Move(5, c.index(3) + 1, 1, n)
    if n == 6 and hist[4] == 1:
        return Move(11, c.index(4) + 1, 1, n)
    if n == 8 and hist[4] == 1 and hist[2] == 2:
        return Move(12, c.index(4) + 1, 1, n)
    # Simple chains and airplane cores. Highest valid core wins ambiguities.
    found = Move(n=n)
    for kind, copies, minimum in ((6, 1, 5), (7, 2, 3), (8, 3, 2)):
        if n % copies:
            continue
        length = n // copies
        if minimum <= length <= 12 and len(occupied) == length:
            low, high = occupied[0], occupied[-1]
            if high <= 12 and high - low + 1 == length and all(c[r-1] == copies for r in occupied):
                found = Move(kind, high, length, n)
    for kind, cards_per_core in ((9, 4), (10, 5)):
        if n % cards_per_core:
            continue
        length = n // cards_per_core
        if length < 2:
            continue
        for low in range(1, 14 - length):
            high = low + length - 1
            if not all(c[r - 1] == 3 for r in range(low, high + 1)):
                continue
            outside = c[:low - 1] + c[high:]
            if ((kind == 9 and max(outside, default=0) <= 2)
                    or (kind == 10 and all(x in (0, 2) for x in outside))):
                found = Move(kind, high, length, n)
    return found


@dataclass(frozen=True)
class Pattern:
    kind: int
    low: int
    high: int
    copies: int
    wings: int = 0
    wing_copies: int = 0

    @property
    def length(self):
        return self.high - self.low + 1

    @property
    def n(self):
        return self.length * self.copies + self.wings * self.wing_copies


def patterns() -> tuple[Pattern, ...]:
    result = []
    for kind, copies, max_rank, wings, wing_copies in (
        (1, 1, 15, 0, 0), (2, 2, 13, 0, 0), (3, 3, 13, 0, 0),
        (4, 3, 13, 1, 1), (5, 3, 13, 1, 2),
        (11, 4, 13, 2, 1), (12, 4, 13, 2, 2), (13, 4, 13, 0, 0),
    ):
        result.extend(Pattern(kind, r, r, copies, wings, wing_copies) for r in range(1, max_rank + 1))
    for kind, copies, minimum, divisor, wing_copies in (
        (6, 1, 5, 1, 0), (7, 2, 3, 2, 0), (8, 3, 2, 3, 0),
        (9, 3, 2, 4, 1), (10, 3, 2, 5, 2),
    ):
        for length in range(minimum, min(12, 20 // divisor) + 1):
            for low in range(1, 14 - length):
                result.append(Pattern(kind, low, low + length - 1, copies,
                                      length if wing_copies else 0, wing_copies))
    return tuple(result)


PATTERNS = patterns()


def candidate(hand: tuple[int, ...], p: Pattern) -> tuple[int, ...] | None:
    if any(hand[r - 1] < p.copies for r in range(p.low, p.high + 1)):
        return None
    c = [0] * 15
    c[p.low - 1:p.high] = [p.copies] * p.length
    remaining = p.wings
    for r in range(1, 16):
        if p.low <= r <= p.high or not remaining:
            continue
        if p.wing_copies == 2 and hand[r - 1] >= 2:
            c[r - 1] = 2
            remaining -= 1
        elif p.wing_copies == 1:
            used = min(remaining, hand[r - 1], 2)
            c[r - 1] = used
            remaining -= used
    return tuple(c) if not remaining else None


def move_score(move: Move, hand_n: int, previous: Move) -> int:
    if not previous.kind:
        score = move.n * 100 - move.power
    else:
        score = 100 - move.power
    if move.kind == 13:
        score -= 10000
    if move.kind == 14:
        score -= 20000
    if move.n == hand_n:
        score += 100000
    return score


def choose_move(hand: Iterable[int], previous: Move = Move()) -> tuple[int, ...]:
    hand = tuple(hand)
    best, best_score = (0,) * 15, -1000000
    for p in PATTERNS:
        c = candidate(hand, p)
        if c is None:
            continue
        move = classify(c)
        if move.beats(previous):
            score = move_score(move, sum(hand), previous)
            if score > best_score:
                best, best_score = c, score
    if hand[13] and hand[14]:
        c = (0,) * 13 + (1, 1)
        move = classify(c)
        score = move_score(move, sum(hand), previous)
        if move.beats(previous) and score > best_score:
            best = c
    return best


def v(name):
    return PREFIX + name


def block(name, lines):
    if isinstance(lines, str):
        lines = [lines]
    return name + " = {\n" + "\n".join("\t" + x.replace("\n", "\n\t") for x in lines) + "\n}"


def setv(name, value):
    return f"set_variable = {{ {v(name)} = {v(value) if isinstance(value, str) else value} }}"


def op(action, name, value):
    return f"{action}_variable = {{ {v(name)} = {v(value) if isinstance(value, str) else value} }}"


def check(name, operator, value):
    return f"check_variable = {{ {v(name)} {operator} {v(value) if isinstance(value, str) else value} }}"


def iff(conditions, effects):
    if isinstance(conditions, str):
        conditions = [conditions]
    if isinstance(effects, str):
        effects = [effects]
    return block("if", [block("limit", conditions), *effects])


def assign_move(kind, power, length, n=None):
    rows = [setv("kind", kind), setv("power", power), setv("len", length)]
    if n is not None:
        rows.append(setv("n", n))
    return rows


def compare_effect():
    return block("RUS_ddz_compare", [
        setv("beats", 0),
        iff(check("kind", ">", 0), [
            iff(block("OR", [
                check("last_kind", "=", 0),
                block("AND", [check("kind", "=", 14), check("last_kind", "<", 14)]),
                block("AND", [check("kind", "=", 13), check("last_kind", "<", 13)]),
                block("AND", [check("kind", "<", 14), check("kind", "=", "last_kind"), check("len", "=", "last_len"),
                              check("n", "=", "last_n"), check("power", ">", "last_power")]),
            ]), setv("beats", 1)),
        ]),
    ])


def classify_effect():
    rows = [setv(x, 0) for x in ("kind", "power", "len", "n", "valid", "beats")]
    rows += [setv(f"hist_{i}", 0) for i in range(1, 5)]
    rows += [setv("bad_count", 0)]
    for r in range(1, 16):
        rows.append(op("add_to", "n", f"s_{r}"))
        rows.append(iff(block("OR", [check(f"s_{r}", "<", 0), check(f"s_{r}", ">", 4 if r <= 13 else 1)]), setv("bad_count", 1)))
        for copies in range(1, 5):
            rows.append(iff(check(f"s_{r}", "=", copies), [op("add_to", f"hist_{copies}", 1), setv(f"rank_{copies}", r)]))
    simple = []
    for kind, copies in ((1, 1), (2, 2), (3, 3), (13, 4)):
        simple.append(iff([check("n", "=", copies), check(f"hist_{copies}", "=", 1)], assign_move(kind, f"rank_{copies}", 1)))
    for kind, total, hist in ((4, 4, ((3, 1), (1, 1))), (5, 5, ((3, 1), (2, 1))),
                              (11, 6, ((4, 1),)), (12, 8, ((4, 1), (2, 2)))):
        simple.append(iff([check("n", "=", total), *[check(f"hist_{k}", "=", n) for k, n in hist]],
                          assign_move(kind, "rank_3" if kind in (4, 5) else "rank_4", 1)))
    for p in PATTERNS:
        if p.kind not in (6, 7, 8, 9, 10):
            continue
        conditions = [check("n", "=", p.n)]
        conditions += [check(f"s_{r}", "=", p.copies) for r in range(p.low, p.high + 1)]
        if p.kind == 9:
            conditions += [check(f"s_{r}", "<", 3) for r in range(1, 16) if not p.low <= r <= p.high]
        if p.kind == 10:
            conditions += [check("hist_2", "=", p.length)]
        simple.append(iff(conditions, assign_move(p.kind, p.high, p.length)))
    simple.append(iff([check("n", "=", 2), check("s_14", "=", 1), check("s_15", "=", 1)], assign_move(14, 15, 1)))
    rows.append(iff([check("bad_count", "=", 0), check("n", ">", 0), check("n", "<", 21)], simple))
    rows.append(iff(check("kind", ">", 0), setv("valid", 1)))
    rows.append("RUS_ddz_compare = yes")
    return block("RUS_ddz_classify", rows)


def offer_effect():
    """A candidate has guaranteed legality, so do not reclassify 350 times."""
    rows = ["RUS_ddz_compare = yes"]
    accept = [setv("score", 100), op("subtract_from", "score", "power")]
    accept += [iff(check("last_kind", "=", 0), [setv("score", "n"), op("multiply", "score", 100), op("subtract_from", "score", "power")])]
    accept += [iff(check("kind", "=", 13), op("subtract_from", "score", 10000)),
               iff(check("kind", "=", 14), op("subtract_from", "score", 20000)),
               iff(check("n", "=", "hand_n"), op("add_to", "score", 100000))]
    accept += [iff(check("score", ">", "best_score"), [setv("best_score", "score"), *[setv(f"s_{r}", f"c_{r}") for r in range(1, 16)]])]
    rows.append(iff(check("beats", "=", 1), accept))
    return block("RUS_ddz_ai_offer", rows)


def build_candidate(p: Pattern):
    conditions = [check(f"a_{r}", ">", p.copies - 1) for r in range(p.low, p.high + 1)]
    # Skip whole core candidates whose kind/size cannot answer the table.
    if p.kind < 13:
        conditions.append(block("OR", [check("last_kind", "=", 0), block("AND", [
            check("last_kind", "=", p.kind), check("last_len", "=", p.length),
            check("last_n", "=", p.n), check("last_power", "<", p.high),
        ])]))
    effects = [setv(f"c_{r}", p.copies if p.low <= r <= p.high else 0) for r in range(1, 16)]
    effects += assign_move(p.kind, p.high, p.length, p.n)
    if p.wings:
        effects.append(setv("wings_left", p.wings))
        for r in range(1, 16):
            if p.low <= r <= p.high:
                continue
            effects.append(iff([check("wings_left", ">", 0), check(f"a_{r}", ">", p.wing_copies - 1)],
                               [setv(f"c_{r}", p.wing_copies), op("subtract_from", "wings_left", 1)]))
            if p.wing_copies == 1:
                effects.append(iff([check("wings_left", ">", 0), check(f"a_{r}", ">", 1)],
                                   [setv(f"c_{r}", 2), op("subtract_from", "wings_left", 1)]))
        effects.append(iff(check("wings_left", "=", 0), "RUS_ddz_ai_offer = yes"))
    else:
        effects.append("RUS_ddz_ai_offer = yes")
    return iff(conditions, effects)


def choose_effect():
    rows = [setv(f"s_{r}", 0) for r in range(1, 16)]
    rows += [setv("best_score", -1000000), setv("hand_n", 0)]
    rows += [op("add_to", "hand_n", f"a_{r}") for r in range(1, 16)]
    rows += [build_candidate(p) for p in PATTERNS]
    rows.append(iff([check("a_14", ">", 0), check("a_15", ">", 0)], [
        *[setv(f"c_{r}", int(r >= 14)) for r in range(1, 16)],
        *assign_move(14, 15, 1, 2), "RUS_ddz_ai_offer = yes",
    ]))
    rows.append("RUS_ddz_classify = yes")
    return block("RUS_ddz_choose_move", rows)


def outputs() -> dict[str, str]:
    text = "# Generated by tools/doudizhu_rules.py; edit the source, then use the parent generator.\n"
    text += "# Rank IDs 1..15: 3..A, 2, small joker, big joker. See module docstring for wing rules.\n\n"
    text += "\n\n".join((compare_effect(), classify_effect(), offer_effect(), choose_effect())) + "\n"
    return {"common/scripted_effects/RUS_doudizhu_rules.txt": text}


if __name__ == "__main__":
    # Standalone invocation is inspection only. The parent generator owns writes.
    generated = next(iter(outputs().values()))
    print(f"{len(PATTERNS)} bounded AI core patterns; {len(generated.splitlines())} script lines; {len(generated.encode('utf-8'))} bytes")
