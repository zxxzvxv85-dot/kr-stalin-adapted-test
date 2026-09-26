"""Intro skin regression: live controls, KR behaviour and stationary window fade.

These checks validate scripts/assets and animation geometry, not engine playback.
"""
from __future__ import annotations

from math import isclose
from pathlib import Path
import os
import subprocess
import sys

from PIL import Image
from hoi4_politics_blocks import KR, R, data
from test_intro_content import check_intro_content

SKIN = {
    "GFX_RUS_intro_underlay": "GFX_tiled_window_pol_goal",
    "GFX_RUS_intro_panel": "GFX_tiled_generic_bg_1",
    "GFX_RUS_intro_content": "GFX_tiled_generic_bg_1",
    "GFX_RUS_intro_content_border": "GFX_tiled_window_thin_border",
    "GFX_RUS_intro_tab": "GFX_strategic_air_sort",
    "GFX_RUS_intro_continue": "GFX_intro_screen_continue_button",
    "GFX_RUS_intro_portrait_back": "GFX_tiled_paper_bg2",
    "GFX_RUS_intro_checkbox": "GFX_generic_checkbox3",
    "GFX_RUS_intro_page": "GFX_unitlist_unitinfo_button",
    "GFX_RUS_intro_back": "GFX_browser_back",
    "GFX_RUS_intro_forward": "GFX_browser_forward",
    "GFX_RUS_intro_spoilers": "GFX_checkbox_button_264",
}


def norm(node):
    if isinstance(node.v, list):
        # The single printed plate replaces only these three cosmetic fills.
        bare = node.value("name").strip('"')
        no_fill = bare in {"splash_border", "content_bkgr_bottom_layer", "content_bkgr_top_layer"}
        value = tuple(norm(n) for n in node.v
                      if not (no_fill and n.k == "background")
                      and not (n.k == "iconType" and n.value("name") == '"RUS_intro_printed_plate"'))
    else:
        value = node.v
        if node.k in ("quadTextureSprite", "spriteType") and value:
            bare = value.strip('"')
            if bare in SKIN:
                old = SKIN[bare]
                value = f'"{old}"' if value.startswith('"') else old
    return node.k, node.op, value


def named(root):
    return {n.value("name").strip('"'): n for n in root.v}


def xy(node, field):
    return tuple(float(node.one(field).value(k)) for k in ("x", "y"))


def check_closing_tabs(original, current):
    """Exercise both real close actions; the hidden parent must retain just its last tab."""
    cache = "RUS_intro_fading_tab"
    active = "kr_intro_screen_variable"

    def condition(node, state):
        if node.k == "has_variable":
            return node.v in state
        if node.k == "check_variable":
            return all(state.get(n.k, 0) == int(n.v) for n in node.v)
        values = [condition(n, state) for n in node.v]
        if node.k == "OR":
            return any(values)
        if node.k == "NOT":
            return not all(values)
        assert node.k in {"visible", "limit", "AND"}, node.k
        return all(values)

    def execute(block, state):
        branch_taken = None
        for node in block.v:
            if node.k == "set_variable":
                for assignment in node.v:
                    value = assignment.v
                    state[assignment.k] = state[value] if value in state else int(value)
            elif node.k == "clear_variable":
                state.pop(node.v, None)
            elif node.k == "set_variable_to_random":
                state[node.v] = state.get(node.v, 0) + 1
            elif node.k == "if":
                branch_taken = condition(node.one("limit"), state)
                if branch_taken:
                    execute(node, state)
            elif node.k == "else":
                assert branch_taken is not None
                if not branch_taken:
                    execute(node, state)
            else:
                assert node.k == "limit", f"Unsupported close action: {node.k}"

    def selected(state):
        return [i for i in range(1, 5)
                if condition(current.one(f"kr_intro_screen_tab_{i}").one("visible"), state)]

    main = current.one("kr_intro_screen")
    toggle = current.one("kr_intro_screen_button").one("effects").one("kr_intro_screen_button_click")
    close = main.one("effects").one("mod_options_button_click")
    assert not condition(main.one("visible"), {}) and selected({}) == []
    for tab in range(1, 5):
        for action in (toggle, close):
            for stale_cache in range(1, 5):
                state = {active: tab, cache: stale_cache, "curr_page_country": 3,
                         "kr_intro_screen_spoilers_revealed": 1}
                assert selected(state) == [tab], "A stale cache must not show an extra open tab"
                execute(action, state)
                assert not condition(main.one("visible"), state), "Close must still hide the parent"
                assert selected(state) == [tab], "Text must survive the parent's fade without overlapping tabs"
                execute(toggle, state)
                assert condition(main.one("visible"), state) and selected(state) == [1]
                assert cache not in state, "Reopen must retire the closing-tab cache"
                for destination in range(1, 5):
                    execute(main.one("effects").one(f"tab_{destination}_click"), state)
                    assert selected(state) == [destination], "Tab switches must remain immediate and exclusive"
                assert state["curr_page_country"] == 3 and state["kr_intro_screen_spoilers_revealed"] == 1

    # Strip only the declared visual additions, then compare the complete upstream AST.
    # This catches changes to parent bindings, dirty refresh, conditions and click effects.
    def without_cache(node):
        if node.k == "set_variable" and node.one(cache):
            assert len(node.v) == 1 and node.value(cache) == active
            return None
        if node.k == "clear_variable" and node.v == cache:
            return None
        if isinstance(node.v, list):
            nodes = node.v
            if node.k == "visible" and node.one("OR"):
                branches = node.one("OR").v
                assert branches[0].k == "check_variable" and branches[0].one(active)
                nodes = branches[:1]
            value = tuple(result for child in nodes if (result := without_cache(child)) is not None)
        else:
            value = node.v
        return node.k, node.op, value

    assert without_cache(current) == original.norm(), "Unrelated KR intro behaviour changed"


def main():
    check_intro_content()
    original = named(data(KR / "interface/kaiserreich/intro_screen.gui", "guiTypes"))
    mod = named(data(R / "interface/kaiserreich/intro_screen.gui", "guiTypes"))
    assert set(mod) == set(original), "Do not introduce a scripted parent chain around KR's tabs"
    for name, node in original.items():
        if name != "kr_intro_screen_container":
            assert norm(node) == norm(mod[name]), f"Controls/text/layout changed: {name}"

    old = original["kr_intro_screen_container"]
    canvas = mod["kr_intro_screen_container"]
    # Functional panel subtree, including every click target, is unchanged.
    assert norm(old.one("containerWindowType")) == norm(canvas.one("containerWindowType"))
    assert canvas.value("clipping") == "no"
    assert xy(canvas, "position") == xy(old, "position"), "Fading must leave the whole window stationary"
    assert canvas.one("size").norm() == old.one("size").norm()
    assert canvas.value("orientation") == old.value("orientation")
    assert canvas.value("origo") == old.value("origo")
    assert canvas.value("fade_time") == "1200"
    assert canvas.value("fade_type") == "linear"
    for field in ("show_position", "hide_position", "show_animation_type", "hide_animation_type", "animation_time"):
        assert canvas.one(field) is None, f"Unexpected movement alongside opacity fade: {field}"
    width = int(canvas.one("size").value("width"))
    title = next(n for n in canvas.children("iconType") if n.value("name") == '"RUS_intro_title"')
    x, y = xy(title, "position")
    scale = float(title.value("scale"))
    source = R / "tools/art_sources/intro_header_v2_source.png"
    title_png = R / "gfx/interface/rus_intro_header/constructivist_title.png"
    assert source.read_bytes() == title_png.read_bytes(), "Approved title must remain byte-exact"
    w, h = Image.open(source).size
    assert isclose(x + w * scale / 2, width / 2, abs_tol=1)
    assert 356 < y + h * scale < 382, "Title tail should join the panel without reaching tabs"

    # Regression for the actual 2026-09-25 'Parent window ... is not found' error:
    # preserve KR's original registration, with every tab directly attached to its root.
    base_gui = data(KR / "common/scripted_guis/00_intro_screen_gui.txt", "scripted_gui")
    live_gui = data(R / "common/scripted_guis/00_intro_screen_gui.txt", "scripted_gui")
    check_closing_tabs(base_gui, live_gui)
    main_gui = live_gui.one("kr_intro_screen")
    assert main_gui.value("window_name") == '"kr_intro_screen_container"'
    assert main_gui.one("parent_window_name") is None
    for i in range(1, 5):
        tab = live_gui.one(f"kr_intro_screen_tab_{i}")
        assert tab.value("parent_window_name") == '"kr_intro_screen_container"'
        assert tab.value("window_name").strip('"') in mod
    backfill = canvas.one("containerWindowType")
    assert backfill.one("background").value("quadTextureSprite") == '"GFX_RUS_intro_underlay"'
    assert Image.open(R / "gfx/interface/rus_intro_theme/underlay.png").getchannel("A").getextrema() == (255, 255)

    # Match native texture dimensions and scripted frame counts, preserving hitboxes.
    game = Path(os.environ.get("HOI4_GAME_ROOT", R.parents[3] / "common/Hearts of Iron IV"))
    originals = {
        "tab": ("button_strategic_air_sort.dds", 2),
        "continue": ("play_button_ready.dds", 1),
        "checkbox": ("generic_checkbox3.dds", 2),
        "page": ("unitcontrol/unitlist_unitinfo_button.dds", 1),
        "back": ("browser_back.dds", 1), "forward": ("browser_forward.dds", 1),
        "spoilers": ("checkbox_button_264.dds", 2),
    }
    sprites = data(R / "interface/RUS_intro_theme.gfx", "spriteTypes")
    for sprite in sprites.v:
        texture = sprite.value("texturefile").strip('"')
        size = Image.open(R / texture).size
        assert max(size) < 4096
        short = sprite.value("name").strip('"').removeprefix("GFX_RUS_intro_")
        if short in originals:
            native, frames = originals[short]
            assert size == Image.open(game / "gfx/interface" / native).size, short
            assert int(sprite.value("noOfFrames", "1")) == frames
    subprocess.run([sys.executable, "-B", str(R / "tools/build_intro_theme.py"), "--check"], check=True)
    print("PASS: original KR parent bindings and controls; stationary parent fade; 32 close/reopen scenarios retain only the active tab; byte-exact art and native hitboxes. Engine playback still requires in-game verification.")


if __name__ == "__main__":
    main()
