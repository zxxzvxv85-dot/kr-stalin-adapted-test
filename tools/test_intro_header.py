"""Intro skin regression: live controls, KR behaviour and whole-window reveal.

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

SKIN = {
    "GFX_RUS_intro_frame": "GFX_tiled_window_pol_goal",
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
        value = tuple(norm(n) for n in node.v)
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


def main():
    original = named(data(KR / "interface/kaiserreich/intro_screen.gui", "guiTypes"))
    mod = named(data(R / "interface/kaiserreich/intro_screen.gui", "guiTypes"))
    assert set(mod) == set(original) | {"RUS_intro_canvas"}
    for name, node in original.items():
        if name != "kr_intro_screen_container":
            assert norm(node) == norm(mod[name]), f"Controls/text/layout changed: {name}"

    old = original["kr_intro_screen_container"]
    canvas = mod["RUS_intro_canvas"]
    # Functional panel subtree, including every click target, is unchanged.
    assert norm(old.one("containerWindowType")) == norm(canvas.one("containerWindowType"))
    wrapper = mod["kr_intro_screen_container"]
    assert wrapper.value("clipping") == "yes"
    assert canvas.value("clipping") == "no"
    assert xy(wrapper, "position") == (-800, -20)
    assert xy(wrapper, "show_position") == (0, -20)
    assert xy(canvas, "position") == (840, 20)
    assert xy(canvas, "show_position") == (40, 20)
    for n in (wrapper, canvas):
        assert n.value("animation_time") == "1200"
        assert n.value("show_animation_type") == "decelerated"
        assert n.value("hide_animation_type") == "accelerated"
    width = int(wrapper.one("size").value("width"))
    height = int(wrapper.one("size").value("height"))
    # Sum stays fixed for any equal easing fraction, not just a chosen curve.
    for step in range(101):
        t = step / 100
        viewport_x = -800 * (1 - t)
        canvas_x = 840 - 800 * t
        assert isclose(viewport_x + canvas_x, 40, abs_tol=1e-10)
        assert isclose(viewport_x + width, 800 * t, abs_tol=1e-10)
    assert 40 - width / 2 == -360
    assert 20 - height / 2 == -420
    assert 20 + 852 < height, "Do not clip the bottom of the live Continue button"
    title = next(n for n in canvas.children("iconType") if n.value("name") == '"RUS_intro_title"')
    x, y = xy(title, "position")
    scale = float(title.value("scale"))
    source = R / "tools/art_sources/intro_header_v2_source.png"
    title_png = R / "gfx/interface/rus_intro_header/constructivist_title.png"
    assert source.read_bytes() == title_png.read_bytes(), "Approved title must remain byte-exact"
    w, h = Image.open(source).size
    assert 0 <= 40 + x and 40 + x + w * scale < width
    assert 356 < y + h * scale < 382, "Title tail should join the panel without reaching tabs"

    # Window hierarchy alone changes. All KR conditions, effects, properties,
    # texts, page counters and option flags must stay exactly as installed.
    base_gui = data(KR / "common/scripted_guis/00_intro_screen_gui.txt", "scripted_gui")
    theme_gui = data(R / "common/scripted_guis/00_intro_screen_gui.txt", "scripted_gui")
    assert len(theme_gui.v) == len(base_gui.v) + 1
    reveal = theme_gui.one("RUS_intro_reveal")
    assert reveal.one("effects") is None
    assert reveal.value("window_name") == '"kr_intro_screen_container"'
    for orig in base_gui.v:
        current = theme_gui.one(orig.k)
        assert current is not None
        if orig.k == "kr_intro_screen":
            assert current.value("window_name") == '"RUS_intro_canvas"'
            assert current.value("parent_window_name") == '"kr_intro_screen_container"'
            omit = {"window_name", "parent_window_name"}
            assert reveal.one("visible").norm() == current.one("visible").norm()
            assert reveal.value("dirty") == current.value("dirty")
        elif orig.k.startswith("kr_intro_screen_tab_"):
            assert current.value("parent_window_name") == '"RUS_intro_canvas"'
            omit = {"parent_window_name"}
        else:
            omit = set()
        assert [n.norm() for n in orig.v if n.k not in omit] == [n.norm() for n in current.v if n.k not in omit], orig.k

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
    print("PASS: KR behaviour/control parity, byte-exact title, native hitbox/frame sizes, stationary content and 1.2s whole-window reveal geometry. Engine playback still requires in-game verification.")


if __name__ == "__main__":
    main()
