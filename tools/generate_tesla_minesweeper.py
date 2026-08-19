from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CELL = 34
BOARD_SIZE = 8
MINE_COUNT = 10
LAYOUT_COUNT = 48
PREFIX = "RUS_tesla_minesweeper"


def cell_id(index: int) -> str:
    return f"{index:02d}"


def neighbors(index: int) -> list[int]:
    row, column = divmod(index, BOARD_SIZE)
    result: list[int] = []
    for row_offset in (-1, 0, 1):
        for column_offset in (-1, 0, 1):
            if row_offset == 0 and column_offset == 0:
                continue
            other_row = row + row_offset
            other_column = column + column_offset
            if 0 <= other_row < BOARD_SIZE and 0 <= other_column < BOARD_SIZE:
                result.append(other_row * BOARD_SIZE + other_column)
    return result


def write_text(path: Path, content: str, bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8-sig" if bom else "utf-8")


def make_layouts() -> list[tuple[int, ...]]:
    rng = random.Random(19360710)
    layouts: set[tuple[int, ...]] = set()
    while len(layouts) < LAYOUT_COUNT:
        layouts.add(tuple(sorted(rng.sample(range(BOARD_SIZE * BOARD_SIZE), MINE_COUNT))))
    result = sorted(layouts)
    for index in range(BOARD_SIZE * BOARD_SIZE):
        safe_layouts = sum(index not in layout for layout in result)
        if safe_layouts < 24:
            raise RuntimeError(f"Cell {index} has too few first-click-safe layouts: {safe_layouts}")
    return result


def draw_assets() -> None:
    output = ROOT / "gfx/interface/tesla_minesweeper"
    output.mkdir(parents=True, exist_ok=True)
    font_path = Path("C:/Windows/Fonts/arialbd.ttf")
    number_font = ImageFont.truetype(str(font_path), 21)

    button_strip = Image.new("RGBA", (CELL * 4, CELL), (0, 0, 0, 0))
    palettes = [
        ((63, 69, 70), (173, 128, 58)),
        ((78, 85, 84), (225, 175, 76)),
        ((48, 53, 54), (119, 87, 43)),
        ((39, 42, 42), (75, 70, 61)),
    ]
    for frame, (fill, edge) in enumerate(palettes):
        draw = ImageDraw.Draw(button_strip)
        x = frame * CELL
        draw.rectangle((x, 0, x + CELL - 1, CELL - 1), fill=fill, outline=(20, 22, 22))
        draw.rectangle((x + 2, 2, x + CELL - 3, CELL - 3), outline=edge)
        draw.line((x + 3, 3, x + CELL - 4, 3), fill=(205, 205, 186))
        draw.line((x + 3, 4, x + 3, CELL - 4), fill=(135, 140, 132))
        draw.line((x + 4, CELL - 4, x + CELL - 4, CELL - 4), fill=(20, 23, 23))
    button_strip.save(output / f"{PREFIX}_cell_button.png")

    number_colours = [
        (210, 205, 181),
        (75, 150, 225),
        (75, 180, 105),
        (220, 78, 68),
        (178, 98, 210),
        (230, 151, 54),
        (73, 196, 188),
        (225, 225, 225),
        (235, 89, 126),
    ]
    revealed_strip = Image.new("RGBA", (CELL * 9, CELL), (0, 0, 0, 0))
    draw = ImageDraw.Draw(revealed_strip)
    for frame in range(9):
        x = frame * CELL
        draw.rectangle((x, 0, x + CELL - 1, CELL - 1), fill=(39, 43, 43), outline=(15, 16, 16))
        draw.rectangle((x + 1, 1, x + CELL - 2, CELL - 2), outline=(91, 87, 73))
        if frame:
            text = str(frame)
            box = draw.textbbox((0, 0), text, font=number_font)
            width = box[2] - box[0]
            height = box[3] - box[1]
            draw.text((x + (CELL - width) / 2, (CELL - height) / 2 - 2), text, font=number_font, fill=number_colours[frame])
    revealed_strip.save(output / f"{PREFIX}_cell_revealed.png")

    mine = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    draw = ImageDraw.Draw(mine)
    draw.rectangle((0, 0, CELL - 1, CELL - 1), fill=(49, 35, 32), outline=(15, 16, 16))
    for angle_line in [((5, 17), (29, 17)), ((17, 5), (17, 29)), ((8, 8), (26, 26)), ((26, 8), (8, 26))]:
        draw.line(angle_line, fill=(218, 91, 56), width=2)
    draw.ellipse((10, 10, 24, 24), fill=(30, 31, 30), outline=(234, 177, 69), width=2)
    draw.ellipse((15, 15, 19, 19), fill=(225, 230, 218))
    mine.save(output / f"{PREFIX}_mine.png")

    flag = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    draw = ImageDraw.Draw(flag)
    draw.line((12, 7, 12, 27), fill=(220, 208, 174), width=2)
    draw.polygon(((13, 8), (27, 12), (13, 17)), fill=(221, 132, 50), outline=(80, 43, 29))
    draw.line((7, 27, 20, 27), fill=(171, 136, 69), width=2)
    flag.save(output / f"{PREFIX}_flag.png")

    source = Image.open(ROOT / "gfx/interface/ideas/RUS_tesla_electrical_industries_source.png").convert("RGBA")
    source.thumbnail((50, 50), Image.Resampling.LANCZOS)

    def entry_frame(fill: tuple[int, int, int], edge: tuple[int, int, int], icon: Image.Image) -> Image.Image:
        frame = Image.new("RGBA", (64, 64), (*fill, 255))
        frame_draw = ImageDraw.Draw(frame)
        frame_draw.rectangle((0, 0, 63, 63), outline=(17, 19, 19), width=2)
        frame_draw.rectangle((3, 3, 60, 60), outline=edge, width=2)
        frame_draw.line((8, 55, 56, 7), fill=(*edge, 145), width=2)
        frame.alpha_composite(icon, ((64 - icon.width) // 2, (64 - icon.height) // 2))
        return frame

    entry_frames = []
    for fill, edge, brightness in [
        ((42, 47, 47), (179, 125, 54), 1.0),
        ((53, 60, 59), (237, 181, 70), 1.12),
        ((32, 36, 36), (122, 88, 42), 0.82),
        ((35, 37, 37), (85, 80, 69), 0.72),
    ]:
        icon = ImageEnhance.Brightness(source).enhance(brightness)
        entry_frames.append(entry_frame(fill, edge, icon))
    entry_strip = Image.new("RGBA", (64 * 4, 64), (0, 0, 0, 0))
    for index, frame in enumerate(entry_frames):
        entry_strip.alpha_composite(frame, (index * 64, 0))
    entry_strip.save(output / f"{PREFIX}_entry_button.png")

    locked_icon = ImageEnhance.Color(source).enhance(0.0)
    locked_icon = ImageEnhance.Brightness(locked_icon).enhance(0.55)
    entry_frame((31, 34, 34), (78, 76, 69), locked_icon).save(output / f"{PREFIX}_entry_locked.png")


def build_gfx() -> str:
    return f'''spriteTypes = {{
\tspriteType = {{
\t\tname = "GFX_{PREFIX}_entry_button"
\t\ttexturefile = "gfx/interface/tesla_minesweeper/{PREFIX}_entry_button.png"
\t\tnoOfFrames = 4
\t\teffectFile = "gfx/FX/buttonstate.lua"
\t}}
\tspriteType = {{
\t\tname = "GFX_{PREFIX}_entry_locked"
\t\ttexturefile = "gfx/interface/tesla_minesweeper/{PREFIX}_entry_locked.png"
\t}}
\tspriteType = {{
\t\tname = "GFX_{PREFIX}_cell_button"
\t\ttexturefile = "gfx/interface/tesla_minesweeper/{PREFIX}_cell_button.png"
\t\tnoOfFrames = 4
\t\teffectFile = "gfx/FX/buttonstate.lua"
\t}}
\tspriteType = {{
\t\tname = "GFX_{PREFIX}_cell_revealed"
\t\ttexturefile = "gfx/interface/tesla_minesweeper/{PREFIX}_cell_revealed.png"
\t\tnoOfFrames = 9
\t}}
\tspriteType = {{
\t\tname = "GFX_{PREFIX}_mine"
\t\ttexturefile = "gfx/interface/tesla_minesweeper/{PREFIX}_mine.png"
\t}}
\tspriteType = {{
\t\tname = "GFX_{PREFIX}_flag"
\t\ttexturefile = "gfx/interface/tesla_minesweeper/{PREFIX}_flag.png"
\t}}
}}'''


def build_gui() -> str:
    lines = [
        "guiTypes = {",
        "\tcontainerWindowType = {",
        f'\t\tname = "{PREFIX}_entry_window"',
        "\t\tposition = { x = 422 y = 397 }",
        "\t\tsize = { width = 77 height = 77 }",
        "\t\tclipping = no",
        "\t\tbackground = { name = \"BackgroundSteel\" quadTextureSprite = \"GFX_equipment_role_selector_tiled_window\" }",
        "\t\tbackground = { name = \"BackgroundPaper\" quadTextureSprite = \"GFX_tiled_research_bg\" }",
        "\t\tbuttonType = {",
        f'\t\t\tname = "{PREFIX}_entry_locked"',
        "\t\t\tposition = { x = 7 y = 6 }",
        f'\t\t\tquadTextureSprite = "GFX_{PREFIX}_entry_locked"',
        f"\t\t\tpdx_tooltip = {PREFIX}_title",
        f"\t\t\tpdx_tooltip_delayed = {PREFIX}_locked_desc",
        "\t\t}",
        "\t\tbuttonType = {",
        f'\t\t\tname = "{PREFIX}_entry_button"',
        "\t\t\tposition = { x = 7 y = 6 }",
        f'\t\t\tquadTextureSprite = "GFX_{PREFIX}_entry_button"',
        "\t\t\tclicksound = click_ok",
        "\t\t\toversound = ui_menu_over",
        f"\t\t\tpdx_tooltip = {PREFIX}_title",
        f"\t\t\tpdx_tooltip_delayed = {PREFIX}_entry_desc",
        "\t\t}",
        "\t}",
        "",
        "\tcontainerWindowType = {",
        f'\t\tname = "{PREFIX}_window"',
        "\t\tposition = { x = 0 y = 0 }",
        "\t\tsize = { width = 540 height = 500 }",
        "\t\torientation = center",
        "\t\torigo = center",
        "\t\tclipping = no",
        "\t\tmoveable = yes",
        "\t\tclick_to_front = yes",
        "\t\tshow_sound = menu_open_window",
        "\t\thide_sound = menu_close_window",
        "\t\tbackground = { name = \"PanelSteel\" quadTextureSprite = \"GFX_equipment_role_selector_tiled_window\" }",
        "\t\tbackground = { name = \"PanelPaper\" quadTextureSprite = \"GFX_tiled_research_bg\" }",
        "\t\tbuttonType = {",
        f'\t\t\tname = "{PREFIX}_close"',
        "\t\t\tposition = { x = -42 y = 12 }",
        "\t\t\torientation = UPPER_RIGHT",
        "\t\t\tquadTextureSprite = \"GFX_closebutton\"",
        "\t\t\tclicksound = click_close",
        "\t\t\tshortcut = \"ESCAPE\"",
        "\t\t\tpdx_tooltip = \"CLOSE\"",
        "\t\t}",
        "\t\tinstantTextBoxType = {",
        f'\t\t\tname = "{PREFIX}_title_text"',
        "\t\t\tposition = { x = 0 y = 18 }",
        "\t\t\tfont = \"hoi_24header\"",
        f"\t\t\ttext = {PREFIX}_title",
        "\t\t\tformat = center",
        "\t\t\tmaxWidth = 540",
        "\t\t\tmaxHeight = 32",
        "\t\t\tfixedsize = yes",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "\t\ticonType = {",
        f'\t\t\tname = "{PREFIX}_tesla_mark"',
        "\t\t\tposition = { x = 62 y = 86 }",
        "\t\t\tspriteType = \"GFX_idea_RUS_tesla_electrical_industries\"",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
    ]

    status_items = [
        ("ready", f"NOT = {{ has_country_flag = {PREFIX}_active }} NOT = {{ has_country_flag = {PREFIX}_won }} NOT = {{ has_country_flag = {PREFIX}_lost }}"),
        ("active", f"has_country_flag = {PREFIX}_active"),
        ("won", f"has_country_flag = {PREFIX}_won"),
        ("won_no_reward", f"has_country_flag = {PREFIX}_won has_country_flag = {PREFIX}_no_reward"),
        ("lost", f"has_country_flag = {PREFIX}_lost"),
    ]
    for status, _ in status_items:
        lines.extend([
            "\t\tinstantTextBoxType = {",
            f'\t\t\tname = "{PREFIX}_status_{status}"',
            "\t\t\tposition = { x = 18 y = 176 }",
            "\t\t\tfont = \"hoi_18mbs\"",
            f"\t\t\ttext = {PREFIX}_status_{status}",
            "\t\t\tformat = center",
            "\t\t\tmaxWidth = 150",
            "\t\t\tmaxHeight = 48",
            "\t\t\tfixedsize = yes",
            "\t\t\talwaystransparent = yes",
            "\t\t}",
        ])
    lines.extend([
        "\t\tinstantTextBoxType = {",
        f'\t\t\tname = "{PREFIX}_reward_text"',
        "\t\t\tposition = { x = 18 y = 245 }",
        "\t\t\tfont = \"hoi_16mbs\"",
        f"\t\t\ttext = {PREFIX}_reward",
        "\t\t\tformat = center",
        "\t\t\tmaxWidth = 150",
        "\t\t\tmaxHeight = 92",
        "\t\t\tfixedsize = yes",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "\t\tinstantTextBoxType = {",
        f'\t\t\tname = "{PREFIX}_flags_text"',
        "\t\t\tposition = { x = 18 y = 350 }",
        "\t\t\tfont = \"hoi_18mbs\"",
        f"\t\t\ttext = {PREFIX}_flags",
        "\t\t\tformat = center",
        "\t\t\tmaxWidth = 150",
        "\t\t\tmaxHeight = 28",
        "\t\t\tfixedsize = yes",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "\t\tinstantTextBoxType = {",
        f'\t\t\tname = "{PREFIX}_cooldown_text"',
        "\t\t\tposition = { x = 18 y = 382 }",
        "\t\t\tfont = \"hoi_16mbs\"",
        f"\t\t\ttext = {PREFIX}_cooldown",
        "\t\t\tformat = center",
        "\t\t\tmaxWidth = 150",
        "\t\t\tmaxHeight = 24",
        "\t\t\tfixedsize = yes",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "\t\tbuttonType = {",
        f'\t\t\tname = "{PREFIX}_start"',
        "\t\t\tposition = { x = 20 y = 430 }",
        "\t\t\tquadTextureSprite = \"GFX_button_148x34\"",
        f"\t\t\tbuttonText = {PREFIX}_start",
        "\t\t\tbuttonFont = \"hoi_18mbs\"",
        "\t\t\tclicksound = click_ok",
        f"\t\t\tpdx_tooltip = {PREFIX}_start_tooltip",
        "\t\t}",
    ])

    board_x, board_y = 225, 92
    for index in range(BOARD_SIZE * BOARD_SIZE):
        row, column = divmod(index, BOARD_SIZE)
        x = board_x + column * CELL
        y = board_y + row * CELL
        ident = cell_id(index)
        lines.extend([
            "\t\tbuttonType = {",
            f'\t\t\tname = "{PREFIX}_cell_{ident}_hidden"',
            f"\t\t\tposition = {{ x = {x} y = {y} }}",
            f'\t\t\tquadTextureSprite = "GFX_{PREFIX}_cell_button"',
            "\t\t\tclicksound = click_ok",
            "\t\t\toversound = ui_menu_over",
            f"\t\t\tpdx_tooltip = {PREFIX}_cell_tooltip",
            "\t\t}",
            "\t\ticonType = {",
            f'\t\t\tname = "{PREFIX}_cell_{ident}_revealed"',
            f"\t\t\tposition = {{ x = {x} y = {y} }}",
            f'\t\t\tspriteType = "GFX_{PREFIX}_cell_revealed"',
            "\t\t\talwaystransparent = yes",
            "\t\t}",
            "\t\ticonType = {",
            f'\t\t\tname = "{PREFIX}_cell_{ident}_mine"',
            f"\t\t\tposition = {{ x = {x} y = {y} }}",
            f'\t\t\tspriteType = "GFX_{PREFIX}_mine"',
            "\t\t\talwaystransparent = yes",
            "\t\t}",
            "\t\ticonType = {",
            f'\t\t\tname = "{PREFIX}_cell_{ident}_flag"',
            f"\t\t\tposition = {{ x = {x} y = {y} }}",
            f'\t\t\tspriteType = "GFX_{PREFIX}_flag"',
            "\t\t\talwaystransparent = yes",
            "\t\t}",
        ])
    lines.extend(["\t}", "}"])
    return "\n".join(lines)


def build_scripted_gui() -> str:
    lines = [
        "scripted_gui = {",
        f"\t{PREFIX}_entry = {{",
        "\t\tcontext_type = player_context",
        "\t\tparent_window_token = politics_tab",
        f'\t\twindow_name = "{PREFIX}_entry_window"',
        "\t\tai_enabled = { always = no }",
        "\t\tvisible = { original_tag = RUS }",
        "\t\ttriggers = {",
        f"\t\t\t{PREFIX}_entry_button_visible = {{ RUS_tesla_minesweeper_is_unlocked = yes }}",
        f"\t\t\t{PREFIX}_entry_locked_visible = {{ NOT = {{ RUS_tesla_minesweeper_is_unlocked = yes }} }}",
        f"\t\t\t{PREFIX}_entry_button_click_enabled = {{ RUS_tesla_minesweeper_is_unlocked = yes }}",
        "\t\t}",
        "\t\teffects = {",
        f"\t\t\t{PREFIX}_entry_button_click = {{",
        f"\t\t\t\tif = {{ limit = {{ NOT = {{ has_country_flag = {PREFIX}_window_open }} }} RUS_tesla_minesweeper_open = yes }}",
        "\t\t\t\telse = { RUS_tesla_minesweeper_close = yes }",
        "\t\t\t}",
        "\t\t}",
        "\t}",
        "",
        f"\t{PREFIX}_game = {{",
        "\t\tcontext_type = player_context",
        f'\t\twindow_name = "{PREFIX}_window"',
        f"\t\tdirty = global.{PREFIX}_update",
        "\t\tai_enabled = { always = no }",
        f"\t\tvisible = {{ RUS_tesla_minesweeper_is_unlocked = yes has_country_flag = {PREFIX}_window_open }}",
        "\t\tproperties = {",
    ]
    for index in range(BOARD_SIZE * BOARD_SIZE):
        ident = cell_id(index)
        lines.extend([
            f"\t\t\t{PREFIX}_cell_{ident}_revealed = {{",
            f"\t\t\t\tframe = {PREFIX}_count_{ident}",
            "\t\t\t}",
        ])
    lines.extend(["\t\t}", "\t\ttriggers = {"])
    status_conditions = {
        "ready": f"NOT = {{ has_country_flag = {PREFIX}_active }} NOT = {{ has_country_flag = {PREFIX}_won }} NOT = {{ has_country_flag = {PREFIX}_lost }}",
        "active": f"has_country_flag = {PREFIX}_active",
        "won": f"has_country_flag = {PREFIX}_won NOT = {{ has_country_flag = {PREFIX}_no_reward }}",
        "won_no_reward": f"has_country_flag = {PREFIX}_won has_country_flag = {PREFIX}_no_reward",
        "lost": f"has_country_flag = {PREFIX}_lost",
    }
    for status, condition in status_conditions.items():
        lines.append(f"\t\t\t{PREFIX}_status_{status}_visible = {{ {condition} }}")
    lines.extend([
        f"\t\t\t{PREFIX}_cooldown_text_visible = {{ has_country_flag = {PREFIX}_cooldown }}",
        f"\t\t\t{PREFIX}_start_click_enabled = {{",
        f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_active }}",
        f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_cooldown }}",
        "\t\t\t}",
    ])
    for index in range(BOARD_SIZE * BOARD_SIZE):
        ident = cell_id(index)
        lines.extend([
            f"\t\t\t{PREFIX}_cell_{ident}_hidden_visible = {{",
            f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_revealed_{ident} }}",
            f"\t\t\t\tNOT = {{ AND = {{ has_country_flag = {PREFIX}_lost has_country_flag = {PREFIX}_mine_{ident} }} }}",
            "\t\t\t}",
            f"\t\t\t{PREFIX}_cell_{ident}_revealed_visible = {{ has_country_flag = {PREFIX}_revealed_{ident} }}",
            f"\t\t\t{PREFIX}_cell_{ident}_mine_visible = {{ has_country_flag = {PREFIX}_lost has_country_flag = {PREFIX}_mine_{ident} }}",
            f"\t\t\t{PREFIX}_cell_{ident}_flag_visible = {{",
            f"\t\t\t\thas_country_flag = {PREFIX}_marked_{ident}",
            f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_lost }}",
            "\t\t\t}",
            f"\t\t\t{PREFIX}_cell_{ident}_hidden_click_enabled = {{",
            f"\t\t\t\thas_country_flag = {PREFIX}_active",
            f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_revealed_{ident} }}",
            f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_marked_{ident} }}",
            "\t\t\t}",
            f"\t\t\t{PREFIX}_cell_{ident}_hidden_right_click_enabled = {{",
            f"\t\t\t\thas_country_flag = {PREFIX}_active",
            f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_revealed_{ident} }}",
            f"\t\t\t\tOR = {{ has_country_flag = {PREFIX}_marked_{ident} check_variable = {{ {PREFIX}_flags < 10 }} }}",
            "\t\t\t}",
        ])
    lines.extend(["\t\t}", "\t\teffects = {"])
    lines.extend([
        f"\t\t\t{PREFIX}_close_click = {{ RUS_tesla_minesweeper_close = yes }}",
        f"\t\t\t{PREFIX}_start_click = {{ RUS_tesla_minesweeper_start = yes }}",
    ])
    for index in range(BOARD_SIZE * BOARD_SIZE):
        ident = cell_id(index)
        lines.extend([
            f"\t\t\t{PREFIX}_cell_{ident}_hidden_click = {{ RUS_tesla_minesweeper_reveal_{ident} = yes }}",
            f"\t\t\t{PREFIX}_cell_{ident}_hidden_right_click = {{ RUS_tesla_minesweeper_mark_{ident} = yes }}",
        ])
    lines.extend(["\t\t}", "\t}", "}"])
    return "\n".join(lines)


def build_triggers() -> str:
    return '''RUS_tesla_minesweeper_is_unlocked = {
\tOR = {
\t\thas_idea = RUS_nikola_tesla_advisor
\t\thas_idea = RUS_tesla_electrical_industries
\t}
}'''


def build_events() -> str:
    return f'''add_namespace = RUS_tesla_minesweeper

country_event = {{
\tid = RUS_tesla_minesweeper.1
\thidden = yes
\tis_triggered_only = yes

\timmediate = {{
\t\tclr_country_flag = {PREFIX}_cooldown
\t\tRUS_tesla_minesweeper_refresh_gui = yes
\t}}
}}'''


def build_effects(layouts: list[tuple[int, ...]]) -> str:
    lines = [
        "RUS_tesla_minesweeper_refresh_gui = {",
        f"\tset_variable_to_random = global.{PREFIX}_update",
        "}",
        "",
        "RUS_tesla_minesweeper_open = {",
        f"\tset_country_flag = {PREFIX}_window_open",
        "\tRUS_tesla_minesweeper_refresh_gui = yes",
        "}",
        "",
        "RUS_tesla_minesweeper_close = {",
        f"\tclr_country_flag = {PREFIX}_window_open",
        "\tRUS_tesla_minesweeper_refresh_gui = yes",
        "}",
        "",
        "RUS_tesla_minesweeper_reset_board = {",
        f"\tclr_country_flag = {PREFIX}_active",
        f"\tclr_country_flag = {PREFIX}_initialised",
        f"\tclr_country_flag = {PREFIX}_won",
        f"\tclr_country_flag = {PREFIX}_lost",
        f"\tclr_country_flag = {PREFIX}_no_reward",
        f"\tset_variable = {{ {PREFIX}_flags = 0 }}",
        f"\tclear_variable = {PREFIX}_first_cell",
    ]
    for index in range(BOARD_SIZE * BOARD_SIZE):
        ident = cell_id(index)
        lines.extend([
            f"\tclr_country_flag = {PREFIX}_mine_{ident}",
            f"\tclr_country_flag = {PREFIX}_revealed_{ident}",
            f"\tclr_country_flag = {PREFIX}_marked_{ident}",
            f"\tset_variable = {{ {PREFIX}_count_{ident} = 0 }}",
        ])
    lines.extend([
        "}",
        "",
        "RUS_tesla_minesweeper_start = {",
        "\tRUS_tesla_minesweeper_reset_board = yes",
        f"\tset_country_flag = {PREFIX}_active",
        "\tRUS_tesla_minesweeper_refresh_gui = yes",
        "}",
        "",
        "RUS_tesla_minesweeper_generate_board = {",
        "\trandom_list = {",
    ])
    for layout in layouts:
        lines.extend([
            "\t\t10 = {",
            "\t\t\tmodifier = {",
            "\t\t\t\tfactor = 0",
            "\t\t\t\tOR = {",
        ])
        for mine in layout:
            lines.append(f"\t\t\t\t\tcheck_variable = {{ {PREFIX}_first_cell = {mine} }}")
        lines.extend(["\t\t\t\t}", "\t\t\t}"])
        for mine in layout:
            lines.append(f"\t\t\tset_country_flag = {PREFIX}_mine_{cell_id(mine)}")
        lines.append("\t\t}")
    lines.extend([
        "\t}",
        f"\tset_country_flag = {PREFIX}_initialised",
        "\tRUS_tesla_minesweeper_compute_counts = yes",
        "}",
        "",
        "RUS_tesla_minesweeper_compute_counts = {",
    ])
    for index in range(BOARD_SIZE * BOARD_SIZE):
        ident = cell_id(index)
        lines.append(f"\tset_variable = {{ {PREFIX}_count_{ident} = 0 }}")
        for neighbor in neighbors(index):
            lines.extend([
                "\tif = {",
                f"\t\tlimit = {{ has_country_flag = {PREFIX}_mine_{cell_id(neighbor)} }}",
                f"\t\tadd_to_variable = {{ {PREFIX}_count_{ident} = 1 }}",
                "\t}",
            ])
    lines.extend(["}", "", "RUS_tesla_minesweeper_expand_empty_cells = {", "\tfor_loop_effect = {", "\t\tend = 16"])
    for index in range(BOARD_SIZE * BOARD_SIZE):
        ident = cell_id(index)
        lines.extend([
            "\t\tif = {",
            "\t\t\tlimit = {",
            f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_mine_{ident} }}",
            f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_revealed_{ident} }}",
            f"\t\t\t\tNOT = {{ has_country_flag = {PREFIX}_marked_{ident} }}",
            "\t\t\t\tOR = {",
        ])
        for neighbor in neighbors(index):
            neighbor_id = cell_id(neighbor)
            lines.append(f"\t\t\t\t\tAND = {{ has_country_flag = {PREFIX}_revealed_{neighbor_id} check_variable = {{ {PREFIX}_count_{neighbor_id} = 0 }} }}")
        lines.extend([
            "\t\t\t\t}",
            "\t\t\t}",
            f"\t\t\tset_country_flag = {PREFIX}_revealed_{ident}",
            "\t\t}",
        ])
    lines.extend(["\t}", "}", "", "RUS_tesla_minesweeper_check_victory = {", "\tif = {", "\t\tlimit = {", "\t\t\tAND = {"])
    for index in range(BOARD_SIZE * BOARD_SIZE):
        ident = cell_id(index)
        lines.append(f"\t\t\t\tOR = {{ has_country_flag = {PREFIX}_mine_{ident} has_country_flag = {PREFIX}_revealed_{ident} }}")
    lines.extend(["\t\t\t}", "\t\t}", "\t\tRUS_tesla_minesweeper_finish_victory = yes", "\t}", "}", ""])

    lines.extend([
        "RUS_tesla_minesweeper_finish_victory = {",
        f"\tclr_country_flag = {PREFIX}_active",
        f"\tset_country_flag = {PREFIX}_won",
        f"\tset_country_flag = {PREFIX}_cooldown",
        "\tcountry_event = { id = RUS_tesla_minesweeper.1 days = 60 }",
        "\tif = {",
        "\t\tlimit = {",
        "\t\t\tany_owned_state = {",
        "\t\t\t\tis_controlled_by = ROOT",
        "\t\t\t\tis_core_of = ROOT",
        "\t\t\t\timpassable = no",
        "\t\t\t\tenergy_infrastructure < 1",
        "\t\t\t\tindustrial_infrastructure < 1",
        "\t\t\t}",
        "\t\t}",
        "\t\trandom_owned_controlled_state = {",
        "\t\t\tlimit = {",
        "\t\t\t\tis_core_of = ROOT",
        "\t\t\t\timpassable = no",
        "\t\t\t\tenergy_infrastructure < 1",
        "\t\t\t\tindustrial_infrastructure < 1",
        "\t\t\t}",
        "\t\t\tadd_extra_state_shared_building_slots = 1",
        "\t\t\tadd_building_construction = { type = energy_infrastructure level = 1 instant_build = yes }",
        "\t\t}",
        "\t\tRUS_tesla_refresh_power_grid_bonuses = yes",
        "\t}",
        "\telse = {",
        f"\t\tset_country_flag = {PREFIX}_no_reward",
        "\t}",
        "\tRUS_tesla_minesweeper_refresh_gui = yes",
        "}",
        "",
        "RUS_tesla_minesweeper_finish_defeat = {",
        f"\tclr_country_flag = {PREFIX}_active",
        f"\tset_country_flag = {PREFIX}_lost",
        f"\tset_country_flag = {PREFIX}_cooldown",
        "\tcountry_event = { id = RUS_tesla_minesweeper.1 days = 60 }",
        "\tRUS_tesla_minesweeper_refresh_gui = yes",
        "}",
        "",
    ])
    for index in range(BOARD_SIZE * BOARD_SIZE):
        ident = cell_id(index)
        lines.extend([
            f"RUS_tesla_minesweeper_reveal_{ident} = {{",
            "\tif = {",
            f"\t\tlimit = {{ has_country_flag = {PREFIX}_active NOT = {{ has_country_flag = {PREFIX}_marked_{ident} }} }}",
            "\t\tif = {",
            f"\t\t\tlimit = {{ NOT = {{ has_country_flag = {PREFIX}_initialised }} }}",
            f"\t\t\tset_variable = {{ {PREFIX}_first_cell = {index} }}",
            "\t\t\tRUS_tesla_minesweeper_generate_board = yes",
            "\t\t}",
            "\t\tif = {",
            f"\t\t\tlimit = {{ has_country_flag = {PREFIX}_mine_{ident} }}",
            "\t\t\tRUS_tesla_minesweeper_finish_defeat = yes",
            "\t\t}",
            "\t\telse = {",
            f"\t\t\tset_country_flag = {PREFIX}_revealed_{ident}",
            "\t\t\tif = {",
            f"\t\t\t\tlimit = {{ check_variable = {{ {PREFIX}_count_{ident} = 0 }} }}",
            "\t\t\t\tRUS_tesla_minesweeper_expand_empty_cells = yes",
            "\t\t\t}",
            "\t\t\tRUS_tesla_minesweeper_check_victory = yes",
            "\t\t}",
            "\t}",
            "\tRUS_tesla_minesweeper_refresh_gui = yes",
            "}",
            "",
            f"RUS_tesla_minesweeper_mark_{ident} = {{",
            "\tif = {",
            f"\t\tlimit = {{ has_country_flag = {PREFIX}_active NOT = {{ has_country_flag = {PREFIX}_revealed_{ident} }} }}",
            "\t\tif = {",
            f"\t\t\tlimit = {{ has_country_flag = {PREFIX}_marked_{ident} }}",
            f"\t\t\tclr_country_flag = {PREFIX}_marked_{ident}",
            f"\t\t\tadd_to_variable = {{ {PREFIX}_flags = -1 }}",
            "\t\t}",
            "\t\telse_if = {",
            f"\t\t\tlimit = {{ check_variable = {{ {PREFIX}_flags < 10 }} }}",
            f"\t\t\tset_country_flag = {PREFIX}_marked_{ident}",
            f"\t\t\tadd_to_variable = {{ {PREFIX}_flags = 1 }}",
            "\t\t}",
            "\t}",
            "\tRUS_tesla_minesweeper_refresh_gui = yes",
            "}",
            "",
        ])
    return "\n".join(lines)


LOCALISATIONS = {
    "simp_chinese": {
        "title": "全俄罗斯电网故障排查",
        "locked_desc": "§Y任命尼古拉·特斯拉为顾问§!或选择§Y特斯拉电气§!作为工业企业后解锁。",
        "entry_desc": "打开全俄罗斯电网故障排查。\n\n§L工程师们用一套布满故障节点的模拟电网训练线路排查与风险隔离。§!",
        "status_ready": "§Y演算台待命§!",
        "status_active": "§G电网演算进行中§!",
        "status_won": "§G演算成功§!",
        "status_won_no_reward": "§G演算成功§!\n§L合格地区均已覆盖强化电网。§!",
        "status_lost": "§R电网短路§!\n§L本局没有惩罚。§!",
        "reward": "§Y胜利奖励§!\n在随机一处合格的俄罗斯核心地区建成§G1座强化电网§!。",
        "flags": "线路标记：[?RUS_tesla_minesweeper_flags|0]/10",
        "cooldown": "§Y设备检修：60日冷却中§!",
        "start": "开始新一轮演算",
        "start_tooltip": "建立一张新的8×8模拟电网。每局结束后需检修60日。",
        "cell_tooltip": "§Y左键§!排查节点\n§Y右键§!标记或取消危险节点\n§L第一次排查必定安全。§!",
    },
    "english": {
        "title": "All-Russian Grid Fault Inspection",
        "locked_desc": "Unlocked by appointing §YNikola Tesla§! as an advisor or retaining §YTesla Electric§! as the industrial concern.",
        "entry_desc": "Open the All-Russian Grid Fault Inspection.\n\n§LEngineers train to isolate faults across a simulated electrical network.§!",
        "status_ready": "§YSimulator Standing By§!",
        "status_active": "§GGrid Simulation in Progress§!",
        "status_won": "§GSimulation Successful§!",
        "status_won_no_reward": "§GSimulation Successful§!\n§LEvery eligible state already has a Reinforced Electrical Grid.§!",
        "status_lost": "§RGrid Shorted§!\n§LThere is no penalty for defeat.§!",
        "reward": "§YVictory Reward§!\nConstruct §G1 Reinforced Electrical Grid§! in a random eligible Russian core state.",
        "flags": "Marked Nodes: [?RUS_tesla_minesweeper_flags|0]/10",
        "cooldown": "§YEquipment Maintenance: 60-day cooldown§!",
        "start": "Begin New Simulation",
        "start_tooltip": "Create a new 8x8 simulated grid. A 60-day maintenance period follows each game.",
        "cell_tooltip": "§YLeft-click§! to inspect a node\n§YRight-click§! to mark or unmark a dangerous node\n§LThe first inspection is always safe.§!",
    },
    "russian": {
        "title": "Всероссийская проверка электросети",
        "locked_desc": "Открывается после назначения §YНиколы Теслы§! советником или выбора §Y«Тесла Электрик»§! промышленным концерном.",
        "entry_desc": "Открыть всероссийскую проверку электросети.\n\n§LИнженеры учатся выявлять и изолировать аварийные узлы в имитационной электросети.§!",
        "status_ready": "§YСимулятор готов§!",
        "status_active": "§GМоделирование сети§!",
        "status_won": "§GМоделирование успешно§!",
        "status_won_no_reward": "§GМоделирование успешно§!\n§LВо всех подходящих областях уже есть усиленная энергосеть.§!",
        "status_lost": "§RКороткое замыкание§!\n§LПоражение не влечёт наказания.§!",
        "reward": "§YНаграда за победу§!\nПостроить §G1 усиленную энергосеть§! в случайной подходящей национальной области России.",
        "flags": "Отмечено узлов: [?RUS_tesla_minesweeper_flags|0]/10",
        "cooldown": "§YОбслуживание оборудования: 60 дней§!",
        "start": "Начать новое моделирование",
        "start_tooltip": "Создать новую имитационную сеть 8x8. После каждой партии оборудование обслуживается 60 дней.",
        "cell_tooltip": "§YЛевая кнопка§!: проверить узел\n§YПравая кнопка§!: отметить или снять отметку\n§LПервая проверка всегда безопасна.§!",
    },
}


def escape_localisation(text: str) -> str:
    return text.replace('"', '\\"').replace("\n", "\\n")


def build_localisation(language: str, values: dict[str, str]) -> str:
    lines = [f"l_{language}:"]
    for suffix, value in values.items():
        lines.append(f'  {PREFIX}_{suffix}: "{escape_localisation(value)}"')
    return "\n".join(lines)


def main() -> None:
    layouts = make_layouts()
    draw_assets()
    write_text(ROOT / f"interface/{PREFIX}.gfx", build_gfx())
    write_text(ROOT / f"interface/{PREFIX}.gui", build_gui())
    write_text(ROOT / f"common/scripted_guis/{PREFIX}.txt", build_scripted_gui())
    write_text(ROOT / f"common/scripted_triggers/{PREFIX}.txt", build_triggers())
    write_text(ROOT / f"common/scripted_effects/{PREFIX}.txt", build_effects(layouts))
    write_text(ROOT / "events/RUS_tesla_minesweeper_events.txt", build_events())
    for language, values in LOCALISATIONS.items():
        write_text(
            ROOT / f"localisation/{language}/{PREFIX}_l_{language}.yml",
            build_localisation(language, values),
            bom=True,
        )
    print(f"Generated Tesla Minesweeper with {len(layouts)} synchronized layouts.")


if __name__ == "__main__":
    main()
