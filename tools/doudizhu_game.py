"""Country-scoped Dou Dizhu lifecycle. Pure renderer; no files written on import.

Cards 1..52 are ranks 3..2, four suits each; 53/54 are the jokers.
Owner 0=deck, 1=human, 2/3=computer, 4=kitty, 9=played.
All gameplay advances on GUI clicks. No on_actions, country rewards or timers.
"""
from __future__ import annotations

P = "RUS_ddz_"


def v(name):
    return P + str(name)


def setv(name, value):
    return f"set_variable = {{ {v(name)} = {value} }}"


def add(name, value=1):
    return f"add_to_variable = {{ {v(name)} = {value} }}"


def sub(name, value=1):
    return f"subtract_from_variable = {{ {v(name)} = {value} }}"


def eq(name, value, op="="):
    if op in (">=", "<="):
        comparison = "greater_than_or_equals" if op == ">=" else "less_than_or_equals"
        return f"check_variable = {{ var = {v(name)} value = {value} compare = {comparison} }}"
    return f"check_variable = {{ {v(name)} {op} {value} }}"


def block(key, lines):
    if isinstance(lines, str):
        lines = [lines]
    return key + " = {\n" + "\n".join("\t" + line for text in lines for line in text.splitlines()) + "\n}"


def iff(condition, *lines):
    return block("if", [block("limit", condition), *lines])


def call(name):
    return f"{v(name)} = yes"


def rank(card):
    return (card - 1) // 4 + 1 if card <= 52 else card - 39


def effects():
    result = []

    def effect(name, *lines):
        result.append(block(v(name), list(lines)))

    public_positions = []
    for seat, center, columns, step in ((1, 500, 20, 27), (2, 355, 10, 22), (3, 645, 10, 22)):
        for row in range(20 // columns):
            public_positions += [setv("public_row_n", v(f"public_n_{seat}")),
                                 sub("public_row_n", row * columns),
                                 iff(eq("public_row_n", columns, ">"), setv("public_row_n", columns)),
                                 iff(eq("public_row_n", 0, "<"), setv("public_row_n", 0)),
                                 setv("public_x", v("public_row_n")), sub("public_x"),
                                 f"multiply_variable = {{ {v('public_x')} = {-step / 2} }}",
                                 add("public_x", center - 17)]
            for slot in range(row * columns + 1, (row + 1) * columns + 1):
                public_positions += [setv(f"public_x_{seat}_{slot}", v("public_x")), add("public_x", step)]

    effect("clear_flags", *[setv(f"sel_{c}", 0) for c in range(1, 55)],
           *[setv(f"s_{r}", 0) for r in range(1, 16)],
           setv("selected_count", 0), setv("selection_legal", 0))
    effect("recount", *[setv(f"count_{s}", 0) for s in range(1, 4)],
           *[setv(f"h_{s}_{r}", 0) for s in range(1, 4) for r in range(1, 16)],
           *[iff(eq(f"owner_{c}", s), add(f"count_{s}"), add(f"h_{s}_{rank(c)}"))
             for c in range(1, 55) for s in range(1, 4)])
    # Static IDs avoid dynamic variable-name indirection unsupported by the engine.
    effect("refresh", setv("hand_x", 20), sub("hand_x", v("count_1")),
           f"multiply_variable = {{ {v('hand_x')} = 19.5 }}", add("hand_x", 167),
           *[iff(eq(f"owner_{c}", 1), setv(f"x_{c}", v("hand_x")), add("hand_x", 39),
                 setv(f"y_{c}", 522), iff(eq(f"sel_{c}", 1), setv(f"y_{c}", 504)))
             for c in range(1, 55)],
           setv("table_x", v("table_n")), sub("table_x"),
           f"multiply_variable = {{ {v('table_x')} = -13.5 }}", add("table_x", 483),
           *[line for i in range(1, 21) for line in (setv(f"table_x_{i}", v("table_x")), add("table_x", 27))],
           *public_positions,
           add("dirty"))
    effect("read_selection", *[setv(f"s_{r}", 0) for r in range(1, 16)],
           *[iff([eq(f"owner_{c}", 1), eq(f"sel_{c}", 1)], add(f"s_{rank(c)}")) for c in range(1, 55)],
           call("classify"), setv("selected_count", v("n")), setv("selection_legal", v("beats")))
    effect("load_actor", *[iff(eq("turn", s), *[setv(f"a_{r}", v(f"h_{s}_{r}")) for r in range(1, 16)])
                            for s in range(1, 4)])
    effect("next_turn", add("turn"), iff(eq("turn", 3, ">"), setv("turn", 1)))
    effect("clear_table", setv("table_n", 0), *[setv(f"table_{i}", 0) for i in range(1, 21)])
    effect("open", "set_country_flag = RUS_ddz_open", call("refresh"))

    # 54 finite draws, with each card's weight removed after drawing it once.
    draw = []
    for c in range(1, 55):
        draw.append(block(v(f"deck_{c}"), [setv(f"deck_{c}", 0), setv(f"owner_{c}", v("deal_seat")),
                    *[iff(eq("deal_slot", i), setv(f"bottom_{i}", c)) for i in range(1, 4)]]))
    effect("draw_card", block("random_list", draw))
    effect("deal", *[setv(f"owner_{c}", 0) for c in range(1, 55)],
           *[setv(f"deck_{c}", 1) for c in range(1, 55)], setv("deal_slot", 0),
           block("for_loop_effect", ["start = 0", "end = 17", "value = RUS_ddz_deal_loop", "break = RUS_ddz_deal_break",
                 *[line for s in range(1, 4) for line in (setv("deal_seat", s), call("draw_card"))]]),
           setv("deal_seat", 4),
           *[line for i in range(1, 4) for line in (setv("deal_slot", i), call("draw_card"))],
           setv("deal_slot", 0), call("recount"))
    effect("new_game", iff("OR = { " + eq("phase", 0) + " " + eq("phase", 3) + " }",
           call("pick_people"), setv("message", 5),
           iff(eq("people_ready", 1),
               *[setv(name, 0) for name in ["message", "landlord", "bid", "bidder", "bids_taken", "winner",
                                           "last_kind", "last_power", "last_len", "last_n", "last_player", "passes",
                                           "trick", "trick_closed"]],
               *[setv(f"seat_bid_{s}", -1) for s in range(1, 4)],
               *[setv(f"action_{s}", 0) for s in range(1, 4)],
               *[setv(f"action_trick_{s}", 0) for s in range(1, 4)],
               *[setv(f"play_{s}_{r}", 0) for s in range(1, 4) for r in range(1, 16)],
               add("deal_bank"), iff(eq("deal_bank", 1, ">"), setv("deal_bank", 0)),
               *[setv(f"public_bank_{s}", 0) for s in range(1, 4)],
               *[setv(f"seen_{r}", 0) for r in range(1, 16)],
               *[setv(f"public_n_{s}", 0) for s in range(1, 4)],
               *[setv(f"public_trick_{s}", 0) for s in range(1, 4)],
               *[setv(f"public_card_{s}_{i}", 0) for s in range(1, 4) for i in range(1, 21)],
               call("clear_table"), call("clear_flags"), call("deal"), setv("phase", 1),
               block("random_list", [block("1", setv("turn", s)) for s in range(1, 4)]),
               call("process_ai")), call("refresh")))

    effect("finish_auction", iff(eq("bid", 0), setv("phase", 3), setv("message", 4)),
           iff(eq("bid", 0, ">"), setv("landlord", v("bidder")), setv("turn", v("landlord")),
               *[iff(eq(f"owner_{c}", 4), setv(f"owner_{c}", v("landlord"))) for c in range(1, 55)],
               setv("phase", 2), setv("message", 0), call("recount")))
    effect("commit_bid", *[iff(eq("turn", s), setv(f"seat_bid_{s}", v("bid_value"))) for s in range(1, 4)],
           iff(eq("bid_value", v("bid"), ">"), setv("bid", v("bid_value")), setv("bidder", v("turn"))),
           add("bids_taken"),
           iff("OR = { " + eq("bid", 3) + " " + eq("bids_taken", 3) + " }", call("finish_auction")),
           block("else", call("next_turn")))
    effect("ai_bid", call("load_actor"), setv("strength", 0),
           *[iff(eq(f"a_{r}", 4), add("strength", 3)) for r in range(1, 14)],
           add("strength", v("a_13")),
           iff(eq("a_14", 1), add("strength", 2)), iff(eq("a_15", 1), add("strength", 3)),
           setv("bid_value", 0),
           iff(eq("strength", 4, ">="), setv("bid_value", 1)),
           iff(eq("strength", 6, ">="), setv("bid_value", 2)),
           iff(eq("strength", 8, ">="), setv("bid_value", 3)),
           iff(eq("bid_value", v("bid"), "<="), setv("bid_value", 0)), call("commit_bid"))
    for b in range(4):
        effect(f"bid_{b}", iff([eq("phase", 1), eq("turn", 1), *([] if b == 0 else [eq("bid", b, "<")])],
               setv("message", 0), setv("bid_value", b), call("commit_bid"), call("process_ai"), call("refresh")))

    effect("record_card", add("table_n"),
           *[iff(eq("table_n", i), setv(f"table_{i}", v("played_card"))) for i in range(1, 21)])
    commit = []
    for c in range(1, 55):
        commit.append(iff([eq(f"owner_{c}", v("turn")),
                          "OR = { AND = { " + eq("turn", 1) + " " + eq(f"sel_{c}", 1) + " } "
                          + "AND = { " + eq("turn", 1, ">") + " " + eq(f"s_{rank(c)}", 0, ">") + " } }"],
                         setv(f"owner_{c}", 9), add(f"seen_{rank(c)}"), sub(f"s_{rank(c)}"), setv("played_card", c), call("record_card")))
    # Keep the completed trick visible until the next lead. Stamps prevent a
    # previous pass being displayed as an action in the new trick.
    effect("commit_play", iff(eq("last_kind", 0), add("trick"), setv("trick_closed", 0)),
           *[setv(f"last_{name}", v(name)) for name in ("kind", "power", "len", "n")],
           *[iff(eq("turn", s), setv(f"action_{s}", 1), setv(f"action_trick_{s}", v("trick")),
                 *[setv(f"play_{s}_{r}", v(f"s_{r}")) for r in range(1, 16)]) for s in range(1, 4)],
           setv("last_player", v("turn")), setv("passes", 0), call("clear_table"), *commit,
           # Snapshot physical cards only after a successful play. Passing and
           # clearing the comparison target never erase another seat's display.
           *[iff(eq("turn", s), add(f"public_bank_{s}"),
                 iff(eq(f"public_bank_{s}", 1, ">"), setv(f"public_bank_{s}", 0)),
                 setv(f"public_n_{s}", v("table_n")),
                 setv(f"public_trick_{s}", v("trick")),
                 *[setv(f"public_card_{s}_{i}", v(f"table_{i}")) for i in range(1, 21)])
             for s in range(1, 4)],
           call("clear_flags"), call("recount"),
           *[iff([eq("turn", s), eq(f"count_{s}", 0)], setv("winner", s), setv("phase", 3)) for s in range(1, 4)],
           iff(eq("phase", 2), call("next_turn")))
    effect("commit_pass", *[iff(eq("turn", s), setv(f"action_{s}", 2), setv(f"action_trick_{s}", v("trick"))) for s in range(1, 4)],
           add("passes"), iff(eq("passes", 2),
           *[setv(f"last_{name}", 0) for name in ("kind", "power", "len", "n", "player")],
           setv("passes", 0), setv("trick_closed", 1), call("clear_table")), call("clear_flags"), call("next_turn"))
    # At most two computer players before a human action; six also covers bidding -> play transition.
    effect("process_ai", block("for_loop_effect", ["start = 0", "end = 6", "value = RUS_ddz_ai_loop", "break = RUS_ddz_ai_break",
           iff([eq("phase", 1), eq("turn", 1, ">")], call("ai_bid")),
           iff([eq("phase", 2), eq("turn", 1, ">")], call("load_actor"), call("choose_team_move"),
               iff(eq("beats", 1), call("commit_play")), block("else", call("commit_pass"))) ]))
    for c in range(1, 55):
        effect(f"select_{c}", iff([eq("phase", 2), eq("turn", 1), eq(f"owner_{c}", 1)],
               iff(eq(f"sel_{c}", 1), setv(f"sel_{c}", 0)), block("else", setv(f"sel_{c}", 1)),
               setv("message", 0), call("read_selection"), call("refresh")))
    effect("clear_selection", iff([eq("phase", 2), eq("turn", 1)], call("clear_flags"),
                                  setv("message", 0), call("refresh")))
    effect("hint", iff([eq("phase", 2), eq("turn", 1)], call("clear_flags"), call("load_actor"), call("choose_move"),
           setv("message", 6), iff(eq("beats", 1), setv("message", 0),
           *[iff([eq(f"owner_{c}", 1), eq(f"s_{rank(c)}", 0, ">")], setv(f"sel_{c}", 1), sub(f"s_{rank(c)}")) for c in range(1, 55)]),
           call("read_selection"), call("refresh")))
    effect("player_play", iff([eq("phase", 2), eq("turn", 1)], setv("message", 0), call("read_selection"),
           iff(eq("valid", 0), setv("message", 1)),
           block("else_if", [block("limit", eq("beats", 0)), setv("message", 2)]),
           block("else", [call("commit_play"), call("process_ai")]), call("refresh")))
    effect("player_pass", iff([eq("phase", 2), eq("turn", 1)], setv("message", 0),
           iff(eq("last_kind", 0), setv("message", 3)),
           block("else", [call("commit_pass"), call("process_ai")]), call("refresh")))
    effect("abandon", iff("OR = { " + eq("phase", 1) + " " + eq("phase", 2) + " }",
           iff(eq("message", 7), setv("phase", 3), setv("winner", 0), setv("message", 8), call("clear_flags")),
           block("else", setv("message", 7)), call("refresh")))
    return "# Generated by tools/generate_doudizhu.py; edit tools/doudizhu_game.py.\n\n" + "\n\n".join(result) + "\n"


def outputs():
    return {
        "common/scripted_effects/RUS_doudizhu_game.txt": effects(),
        "common/decisions/categories/RUS_doudizhu_categories.txt": """# Test-development minigame, deliberately independent of national focus progression.
RUS_ddz_test_category = {
    icon = GFX_decision_category_generic_political_actions
    allowed = { original_tag = RUS }
    visible = { is_ai = no }
}
""",
        "common/decisions/RUS_doudizhu_decisions.txt": """# Native decision format follows KR political discourse decisions and the development GUI launcher.
RUS_ddz_test_category = {
    RUS_ddz_open_table = {
        icon = GFX_decision_generic_political_discourse
        cost = 0
        visible = { is_ai = no }
        available = { hidden_trigger = { original_tag = RUS is_ai = no } }
        complete_effect = {
            custom_effect_tooltip = RUS_ddz_open_table_tt
            hidden_effect = { RUS_ddz_open = yes }
        }
        ai_will_do = { base = 0 }
    }
}
""",
    }
