"""Check the five-page RUS intro against KR's real selectors and click bounds."""
from __future__ import annotations

from pathlib import Path
import re

from hoi4_politics_blocks import KR, R, data, load


def read_loc(path: Path) -> dict[str, str]:
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), f"Missing localisation BOM: {path}"
    entries = re.findall(r'^\s*([^#\s:]+):(?:\d+)?\s*"(.*)"\s*$', raw.decode("utf-8-sig"), re.M)
    assert len(dict(entries)) == len(entries), f"Duplicate keys: {path}"
    return dict(entries)


def matches(trigger, country, variables):
    for condition in trigger.v:
        if condition.k == "tag":
            if country != condition.v:
                return False
        elif condition.k == "check_variable":
            for check in condition.v:
                left = variables.get(check.k, 0)
                right = variables[check.v] if check.v in variables else int(check.v)
                if not {"=": left == right, "<": left < right, ">": left > right}[check.op]:
                    return False
        else:
            raise AssertionError(f"Unsupported intro condition: {condition.k}")
    return True


def select(function, country, variables):
    for branch in function.children("text"):
        trigger = branch.one("trigger")
        if trigger is None or matches(trigger, country, variables):
            return branch.value("localization_key").strip('"')
    raise AssertionError("Missing selector fallback")


def check_intro_content():
    functions = {n.value("name"): n for n in load(R / "common/scripted_localisation/RUS_country_intro_scripted_loc.txt")}
    history = load(R / "history/countries/RUS - Russia.txt")
    counts = [n.value("country_intro_page_count") for n in history
              if n.k == "set_variable" and n.one("country_intro_page_count")]
    assert counts == ["4"], "RUS needs five pages; KR stores the last zero-based index"
    controls = data(R / "common/scripted_guis/00_intro_screen_gui.txt", "scripted_gui").one("kr_intro_screen_tab_1")
    triggers, effects = controls.one("triggers"), controls.one("effects")

    # Traverse using the actual KR button conditions and increments, including ends.
    variables = {"curr_page_country": 0, "country_intro_page_count": int(counts[0])}
    assert not matches(triggers.one("country_flip_back_click_enabled"), "RUS", variables)
    for kind in ("Header", "Content"):
        function = functions[f"RUSGetCountryIntro{kind}"]
        expected = [f"RUS_unfinished_october_intro_{kind.lower()}"]
        expected += [f"RUS_country_intro_{kind.lower()}" + (f"_{i}" if i else "") for i in range(4)]
        variables["curr_page_country"] = 0
        visited = [select(function, "RUS", variables)]
        while matches(triggers.one("country_flip_forward_click_enabled"), "RUS", variables):
            step = effects.one("country_flip_forward_click").one("add_to_variable")
            variables["curr_page_country"] += int(step.value("curr_page_country"))
            visited.append(select(function, "RUS", variables))
            assert len(visited) <= 5, "Unbounded pagination"
        assert visited == expected, (kind, visited)
        back = [visited[-1]]
        while matches(triggers.one("country_flip_back_click_enabled"), "RUS", variables):
            step = effects.one("country_flip_back_click").one("subtract_from_variable")
            variables["curr_page_country"] -= int(step.value("curr_page_country"))
            back.append(select(function, "RUS", variables))
            assert len(back) <= 5, "Unbounded reverse pagination"
        assert back == expected[::-1]
        assert select(function, "RUS", {}) == expected[0], "Unset current page must show the new introduction"
        # Preserve KR's special cases and country-culture lookup in every other tag.
        for country in ("CAN", "GBR", "CHI", "FRA", "GER"):
            for page in range(6):
                assert select(function, country, {"curr_page_country": page}) == f"[GetCountryIntro{kind}]"

    palette = data(KR / "interface/core.gfx", "bitmapfonts").one("textcolors")
    valid_colors = {n.k for n in palette.v}
    for language in ("simp_chinese", "english", "russian"):
        loc = read_loc(R / f"localisation/replace/RUS_country_intro_l_{language}.yml")
        for kind in ("Header", "Content"):
            assert loc[f"kr_intro_screen_tab_1_{kind.lower()}"] == f"[ROOT.RUSGetCountryIntro{kind}]"
        body = loc["RUS_unfinished_october_intro_content"]
        assert len(body.split(r"\n\n")) == 5
        active = None
        for code in re.findall(r"§(.)", body):
            if code == "!":
                assert active, "Unmatched colour reset"
                active = None
            else:
                assert code in valid_colors and active is None, "Unknown or nested colour"
                active = code
        assert active is None, "Colour leaked beyond the final span"
        assert len(set(re.findall(r"§([^!])", body))) >= 5
        assert not any(key.startswith("RUS_country_intro_") for key in loc), "Reuse, do not overwrite or duplicate KR's original pages"

    print("PASS: RUS intro pages 1-5 and reverse traversal; KR navigation endpoints; other-country delegation; three-language references and native colour pairs.")


if __name__ == "__main__":
    check_intro_content()
