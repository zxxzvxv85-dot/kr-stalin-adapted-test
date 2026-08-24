from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT.parent
KR = WORKSHOP / "1521695605"
GEOJSON = WORKSHOP / "tmp" / "europe_gui" / "ne_110m_admin_0_countries.geojson"
ASSET_DIR = ROOT / "gfx" / "interface" / "RUS_europe_intervention"

MAP_WIDTH = 500
MAP_HEIGHT = 250
FLAG_WIDTH = 20
FLAG_HEIGHT = 13
LON_MIN, LON_MAX = -25.0, 52.0
LAT_MIN, LAT_MAX = 31.0, 72.0

# Main-map entries use geographic coordinates. Potential successor tags share the
# same area and are only shown when that tag actually exists.
COUNTRIES = [
    ("ICE", -18.0, 65.0), ("IRE", -8.0, 53.0), ("NIR", -6.0, 55.0),
    ("ENG", -2.0, 54.0), ("WLS", -4.0, 52.0), ("SCO", -4.0, 58.0),
    ("NOR", 8.0, 62.0), ("SWE", 16.0, 61.0), ("FIN", 25.0, 64.0),
    ("DEN", 10.0, 56.0), ("HOL", 5.4, 52.5), ("BEL", 4.2, 50.8),
    ("FLA", 4.3, 51.2), ("WAL", 4.8, 50.3), ("FRA", 2.0, 46.5),
    ("BRI", -3.0, 48.3), ("LIL", 2.7, 50.4), ("SWI", 8.2, 46.5),
    ("SPA", -3.5, 40.5), ("CAT", 2.0, 42.0), ("BAS", -2.2, 43.1),
    ("POR", -8.2, 39.5), ("GER", 10.5, 51.5), ("PRE", 17.0, 53.5),
    ("NGF", 9.5, 54.0), ("RHI", 7.0, 50.0), ("BAY", 12.0, 48.5),
    ("AUS", 14.0, 47.4), ("HUN", 19.0, 47.0), ("CZE", 15.2, 49.7),
    ("SLO", 14.8, 46.0), ("GAL", 23.0, 49.7), ("POL", 19.0, 52.0),
    ("BAT", 23.0, 57.3), ("LIT", 24.0, 55.3), ("LAT", 24.6, 57.0),
    ("EST", 25.5, 59.0), ("BLR", 28.0, 53.2), ("UKR", 32.0, 49.0),
    ("ROM", 25.0, 46.0), ("SER", 20.7, 44.0), ("CRO", 16.5, 45.2),
    ("BOS", 17.8, 44.1), ("MNT", 19.2, 42.7), ("ALB", 20.0, 41.3),
    ("BUL", 25.0, 42.8), ("GRE", 22.7, 39.0), ("MAC", 21.7, 41.3),
    ("TRS", 13.6, 45.8), ("ITA", 11.5, 43.8), ("SRI", 9.5, 44.8),
    ("SIC", 15.0, 38.0), ("PAP", 12.6, 42.0), ("SRD", 9.0, 40.0),
    ("VNC", 12.3, 45.4), ("LOM", 9.6, 46.4), ("EMI", 11.2, 44.5),
    ("TUS", 11.0, 43.1), ("MLT", 14.4, 35.9), ("CYP", 33.0, 35.2),
    ("TUR", 32.0, 39.3), ("GEO", 43.0, 42.2), ("ARM", 44.2, 40.2),
    ("AZR", 47.5, 40.3),
]


def project(lon: float, lat: float) -> tuple[int, int]:
    x = int(round((lon - LON_MIN) / (LON_MAX - LON_MIN) * (MAP_WIDTH - 24))) + 12
    mercator = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    mercator_min = math.log(math.tan(math.pi / 4 + math.radians(LAT_MIN) / 2))
    mercator_max = math.log(math.tan(math.pi / 4 + math.radians(LAT_MAX) / 2))
    y = int(round((mercator_max - mercator) / (mercator_max - mercator_min) * (MAP_HEIGHT - 22))) + 11
    return x, y


def draw_polygon(draw: ImageDraw.ImageDraw, coordinates, fill, outline) -> None:
    for polygon in coordinates:
        outer = [project(float(lon), float(lat)) for lon, lat in polygon[0]]
        if len(outer) >= 3:
            draw.polygon(outer, fill=fill, outline=outline, width=1)


def build_map_panel() -> None:
    random.seed(1936)
    image = Image.new("RGBA", (MAP_WIDTH, MAP_HEIGHT), (38, 43, 40, 255))
    pixels = image.load()
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            grain = random.randint(-7, 7)
            vignette = int(12 * (((x - MAP_WIDTH / 2) / (MAP_WIDTH / 2)) ** 2 + ((y - MAP_HEIGHT / 2) / (MAP_HEIGHT / 2)) ** 2))
            pixels[x, y] = (max(18, 48 + grain - vignette), max(20, 51 + grain - vignette), max(18, 46 + grain - vignette), 255)

    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(0, MAP_WIDTH, 32):
        draw.line((x, 0, x, MAP_HEIGHT), fill=(122, 113, 82, 18), width=1)
    for y in range(0, MAP_HEIGHT, 25):
        draw.line((0, y, MAP_WIDTH, y), fill=(122, 113, 82, 18), width=1)

    if GEOJSON.exists():
        data = json.loads(GEOJSON.read_text(encoding="utf-8"))
        for feature in data["features"]:
            geometry = feature.get("geometry") or {}
            props = feature.get("properties") or {}
            continent = props.get("CONTINENT")
            name = props.get("NAME")
            if continent != "Europe" and name not in {"Turkey", "Georgia", "Armenia", "Azerbaijan", "Cyprus"}:
                continue
            if geometry.get("type") == "Polygon":
                polygons = [geometry["coordinates"]]
            elif geometry.get("type") == "MultiPolygon":
                polygons = geometry["coordinates"]
            else:
                continue
            draw_polygon(draw, polygons, fill=(102, 107, 94, 210), outline=(188, 176, 130, 125))

    # KR-style survey-map framing and restrained socialist accents.
    draw.rectangle((1, 1, MAP_WIDTH - 2, MAP_HEIGHT - 2), outline=(24, 22, 17, 255), width=3)
    draw.rectangle((5, 5, MAP_WIDTH - 6, MAP_HEIGHT - 6), outline=(161, 140, 83, 210), width=1)
    draw.line((12, 31, 112, 31), fill=(145, 30, 27, 190), width=2)
    draw.line((388, 31, 488, 31), fill=(145, 30, 27, 190), width=2)
    image = image.filter(ImageFilter.GaussianBlur(0.25))
    image.save(ASSET_DIR / "europe_map_panel.png")


def build_flag_buttons() -> None:
    selected = Image.new("RGBA", (FLAG_WIDTH, FLAG_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(selected)
    draw.rectangle((0, 0, FLAG_WIDTH - 1, FLAG_HEIGHT - 1), outline=(239, 210, 112, 255), width=2)
    draw.rectangle((2, 2, FLAG_WIDTH - 3, FLAG_HEIGHT - 3), outline=(139, 28, 25, 245), width=1)
    selected.save(ASSET_DIR / "selected_frame.png")

    for tag, _, _ in COUNTRIES:
        source = KR / "gfx" / "flags" / "medium" / f"{tag}.tga"
        flag = Image.open(source).convert("RGBA")
        flag = ImageOps.fit(flag, (FLAG_WIDTH - 2, FLAG_HEIGHT - 2), method=Image.Resampling.LANCZOS)
        base = Image.new("RGBA", (FLAG_WIDTH, FLAG_HEIGHT), (19, 18, 15, 255))
        base.alpha_composite(flag, (1, 1))

        normal = ImageEnhance.Brightness(base).enhance(0.82)
        hover = ImageEnhance.Contrast(ImageEnhance.Brightness(base).enhance(1.12)).enhance(1.08)
        hover_draw = ImageDraw.Draw(hover)
        hover_draw.rectangle((0, 0, FLAG_WIDTH - 1, FLAG_HEIGHT - 1), outline=(211, 185, 102, 255), width=1)
        pressed = ImageEnhance.Brightness(base).enhance(0.62)
        pressed_overlay = Image.new("RGBA", pressed.size, (112, 20, 18, 55))
        pressed = Image.alpha_composite(pressed, pressed_overlay)
        disabled = ImageOps.grayscale(base).convert("RGBA")
        disabled = ImageEnhance.Brightness(disabled).enhance(0.45)
        sheet = Image.new("RGBA", (FLAG_WIDTH * 4, FLAG_HEIGHT), (0, 0, 0, 0))
        for index, frame in enumerate((normal, hover, pressed, disabled)):
            sheet.alpha_composite(frame, (index * FLAG_WIDTH, 0))
        sheet.save(ASSET_DIR / f"{tag}_button.png")

    button = Image.new("RGBA", (72 * 4, 24), (0, 0, 0, 0))
    colors = ((67, 68, 61), (91, 88, 68), (78, 42, 38), (43, 43, 40))
    borders = ((144, 132, 96), (220, 194, 112), (162, 64, 52), (82, 80, 70))
    for index, (fill, border) in enumerate(zip(colors, borders)):
        frame = Image.new("RGBA", (72, 24), (*fill, 255))
        frame_draw = ImageDraw.Draw(frame)
        frame_draw.rectangle((0, 0, 71, 23), outline=(22, 20, 16, 255), width=2)
        frame_draw.rectangle((2, 2, 69, 21), outline=(*border, 255), width=1)
        button.alpha_composite(frame, (index * 72, 0))
    button.save(ASSET_DIR / "overview_button.png")


def build_gfx() -> None:
    lines = ["spriteTypes = {", "\tspriteType = {", '\t\tname = "GFX_RUS_europe_intervention_map_panel"', '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/europe_map_panel.png"', "\t}", "", "\tspriteType = {", '\t\tname = "GFX_RUS_europe_intervention_selected_frame"', '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/selected_frame.png"', "\t}", "", "\tspriteType = {", '\t\tname = "GFX_RUS_europe_intervention_overview_button"', '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/overview_button.png"', "\t\tnoOfFrames = 4", "\t}"]
    for tag, _, _ in COUNTRIES:
        lines.extend(["", "\tspriteType = {", f'\t\tname = "GFX_RUS_europe_intervention_{tag}_button"', f'\t\ttexturefile = "gfx/interface/RUS_europe_intervention/{tag}_button.png"', "\t\tnoOfFrames = 4", "\t}"])
    lines.append("}")
    (ROOT / "interface" / "RUS_europe_intervention.gfx").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_gui() -> None:
    lines = [
        "guiTypes = {",
        "\tcontainerWindowType = {",
        '\t\tname = "RUS_europe_intervention_window"',
        "\t\tposition = { x = 0 y = 0 }",
        "\t\tsize = { width = 100% height = 316 }",
        "\t\tclipping = no",
        "",
        "\t\ticonType = {",
        '\t\t\tname = "RUS_europe_intervention_map"',
        "\t\t\tposition = { x = 0 y = 0 }",
        '\t\t\tspriteType = "GFX_RUS_europe_intervention_map_panel"',
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_title"',
        "\t\t\tposition = { x = 110 y = 8 }",
        '\t\t\tfont = "hoi_22header"',
        '\t\t\ttext = "RUS_europe_intervention_title"',
        "\t\t\tformat = center",
        "\t\t\tmaxWidth = 280",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
    ]
    for tag, lon, lat in COUNTRIES:
        x, y = project(lon, lat)
        x -= FLAG_WIDTH // 2
        y -= FLAG_HEIGHT // 2
        lines.extend([
            "",
            "\t\tbuttonType = {",
            f'\t\t\tname = "RUS_europe_intervention_{tag}_button"',
            f"\t\t\tposition = {{ x = {x} y = {y} }}",
            f'\t\t\tquadTextureSprite = "GFX_RUS_europe_intervention_{tag}_button"',
            '\t\t\tclicksound = "click_default"',
            f'\t\t\tpdx_tooltip = "RUS_europe_intervention_{tag}_tt"',
            "\t\t}",
            "",
            "\t\ticonType = {",
            f'\t\t\tname = "RUS_europe_intervention_{tag}_selected"',
            f"\t\t\tposition = {{ x = {x} y = {y} }}",
            '\t\t\tspriteType = "GFX_RUS_europe_intervention_selected_frame"',
            f'\t\t\tpdx_tooltip = "RUS_europe_intervention_{tag}_tt"',
            "\t\t\talwaystransparent = yes",
            "\t\t}",
        ])

    lines.extend([
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_no_selection"',
        "\t\t\tposition = { x = 14 y = 261 }",
        '\t\t\tfont = "hoi_18mbs"',
        '\t\t\ttext = "RUS_europe_intervention_no_selection"',
        "\t\t\tformat = left",
        "\t\t\tmaxWidth = 360",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
    ])
    for tag, _, _ in COUNTRIES:
        lines.extend([
            "",
            "\t\tinstantTextBoxType = {",
            f'\t\t\tname = "RUS_europe_intervention_{tag}_selected_name"',
            "\t\t\tposition = { x = 14 y = 258 }",
            '\t\t\tfont = "hoi_18mbs"',
            f'\t\t\ttext = "RUS_europe_intervention_{tag}_selected_name"',
            "\t\t\tformat = left",
            "\t\t\tmaxWidth = 360",
            "\t\t\talwaystransparent = yes",
            "\t\t}",
        ])
    lines.extend([
        "",
        "\t\tbuttonType = {",
        '\t\t\tname = "RUS_europe_intervention_overview_button"',
        "\t\t\tposition = { x = 414 y = 256 }",
        '\t\t\tquadTextureSprite = "GFX_RUS_europe_intervention_overview_button"',
        '\t\t\tbuttonText = "RUS_europe_intervention_overview_button"',
        '\t\t\tbuttonFont = "hoi_16mbs"',
        '\t\t\tpdx_tooltip = "RUS_europe_intervention_overview_tt"',
        "\t\t}",
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_help"',
        "\t\t\tposition = { x = 14 y = 285 }",
        '\t\t\tfont = "hoi_16mbs"',
        '\t\t\ttext = "RUS_europe_intervention_help"',
        "\t\t\tformat = left",
        "\t\t\tmaxWidth = 472",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "\t}",
        "}",
    ])
    (ROOT / "interface" / "RUS_europe_intervention.gui").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_scripted_gui() -> None:
    lines = [
        "scripted_gui = {",
        "\tRUS_europe_intervention_gui = {",
        "\t\tcontext_type = decision_category",
        '\t\twindow_name = "RUS_europe_intervention_window"',
        "\t\tai_enabled = { always = no }",
        "\t\tvisible = {",
        "\t\t\toriginal_tag = RUS",
        "\t\t\thas_socialist_government = yes",
        "\t\t\thas_completed_focus = RUS_self_determination",
        "\t\t}",
        "\t\ttriggers = {",
        "\t\t\tRUS_europe_intervention_no_selection_visible = { NOT = { has_country_flag = RUS_europe_intervention_filter_active } }",
        "\t\t\tRUS_europe_intervention_overview_button_click_enabled = { has_country_flag = RUS_europe_intervention_filter_active }",
    ]
    for tag, _, _ in COUNTRIES:
        lines.extend([
            f"\t\t\tRUS_europe_intervention_{tag}_button_visible = {{ {tag} = {{ exists = yes }} }}",
            f"\t\t\tRUS_europe_intervention_{tag}_button_click_enabled = {{ {tag} = {{ exists = yes }} }}",
            f"\t\t\tRUS_europe_intervention_{tag}_selected_visible = {{ has_country_flag = RUS_europe_intervention_selected_{tag} }}",
            f"\t\t\tRUS_europe_intervention_{tag}_selected_name_visible = {{ has_country_flag = RUS_europe_intervention_selected_{tag} }}",
        ])
    lines.extend(["\t\t}", "\t\teffects = {", "\t\t\tRUS_europe_intervention_overview_button_click = { RUS_clear_europe_intervention_selection = yes }"])
    for tag, _, _ in COUNTRIES:
        lines.extend([
            f"\t\t\tRUS_europe_intervention_{tag}_button_click = {{",
            "\t\t\t\tRUS_clear_europe_intervention_selection = yes",
            "\t\t\t\tset_country_flag = RUS_europe_intervention_filter_active",
            f"\t\t\t\tset_country_flag = RUS_europe_intervention_selected_{tag}",
            "\t\t\t}",
        ])
    lines.extend(["\t\t}", "\t}", "}"])
    (ROOT / "common" / "scripted_guis" / "RUS_europe_intervention.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_scripted_effect_and_trigger() -> None:
    effect_lines = ["RUS_clear_europe_intervention_selection = {", "\tclr_country_flag = RUS_europe_intervention_filter_active"]
    for tag, _, _ in COUNTRIES:
        effect_lines.append(f"\tclr_country_flag = RUS_europe_intervention_selected_{tag}")
    effect_lines.append("}")
    (ROOT / "common" / "scripted_effects" / "RUS_europe_intervention_effects.txt").write_text("\n".join(effect_lines) + "\n", encoding="utf-8")

    trigger_lines = [
        "RUS_europe_intervention_target_selected_or_overview = {",
        "\tOR = {",
        "\t\tNOT = { has_country_flag = RUS_europe_intervention_filter_active }",
        "\t\tNOT = { has_socialist_government = yes }",
        "\t\tNOT = { has_completed_focus = RUS_self_determination }",
    ]
    for tag, _, _ in COUNTRIES:
        trigger_lines.extend([
            "\t\tAND = {",
            f"\t\t\thas_country_flag = RUS_europe_intervention_selected_{tag}",
            f"\t\t\tFROM = {{ tag = {tag} }}",
            "\t\t}",
        ])
    trigger_lines.extend(["\t}", "}", ""])
    grouped = {
        "BLR": ["BLR"],
        "BALTICS": ["BAT", "EST", "LAT", "LIT"],
        "UKR": ["UKR"],
        "POL": ["POL"],
    }
    for name, tags in grouped.items():
        trigger_lines.extend([
            f"RUS_europe_intervention_{name}_selected_or_overview = {{",
            "\tOR = {",
            "\t\tNOT = { has_country_flag = RUS_europe_intervention_filter_active }",
            "\t\tNOT = { has_socialist_government = yes }",
            "\t\tNOT = { has_completed_focus = RUS_self_determination }",
        ])
        trigger_lines.extend(f"\t\thas_country_flag = RUS_europe_intervention_selected_{tag}" for tag in tags)
        trigger_lines.extend(["\t}", "}", ""])
    (ROOT / "common" / "scripted_triggers" / "RUS_europe_intervention_triggers.txt").write_text("\n".join(trigger_lines), encoding="utf-8")


def build_localisation() -> None:
    languages = {
        "simp_chinese": {
            "title": "欧洲革命事务局",
            "none": "§Y欧洲总览§!：显示当前全部可用的革命外交与干涉决议",
            "help": "点击地图上的国旗以筛选该国事务；再次选择“总览”即可恢复完整决议列表。",
            "overview": "总览",
            "overview_tt": "取消国家筛选，恢复显示全部可用决议。",
            "selected": "§Y已选目标：§!",
            "tooltip": "点击后仅显示与该国对应的可用决议。",
        },
        "english": {
            "title": "Bureau of European Revolutionary Affairs",
            "none": "§YEuropean overview§!: show all currently available revolutionary and intervention decisions",
            "help": "Select a flag to filter decisions for that country. Choose Overview to restore the full list.",
            "overview": "Overview",
            "overview_tt": "Clear the country filter and show every available decision.",
            "selected": "§YSelected target:§!",
            "tooltip": "Select to show available decisions concerning this country.",
        },
        "russian": {
            "title": "Бюро европейских революционных дел",
            "none": "§YОбзор Европы§!: показать все доступные решения по революционной дипломатии и вмешательству",
            "help": "Нажмите на флаг, чтобы отфильтровать решения по стране. «Обзор» вернёт полный список.",
            "overview": "Обзор",
            "overview_tt": "Снять фильтр страны и показать все доступные решения.",
            "selected": "§YВыбранная цель:§!",
            "tooltip": "Показать доступные решения, относящиеся к этой стране.",
        },
    }
    for language, loc in languages.items():
        lines = [f"l_{language}:", f' RUS_europe_intervention_title:0 "{loc["title"]}"', f' RUS_europe_intervention_no_selection:0 "{loc["none"]}"', f' RUS_europe_intervention_help:0 "{loc["help"]}"', f' RUS_europe_intervention_overview_button:0 "{loc["overview"]}"', f' RUS_europe_intervention_overview_tt:0 "{loc["overview_tt"]}"']
        for tag, _, _ in COUNTRIES:
            lines.append(f' RUS_europe_intervention_{tag}_selected_name:0 "{loc["selected"]} [{tag}.GetNameWithFlag]"')
            lines.append(f' RUS_europe_intervention_{tag}_tt:0 "§Y[{tag}.GetName]§!\\n{loc["tooltip"]}"')
        path = ROOT / "localisation" / language / f"RUS_europe_intervention_l_{language}.yml"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    build_map_panel()
    build_flag_buttons()
    build_gfx()
    build_gui()
    build_scripted_gui()
    build_scripted_effect_and_trigger()
    build_localisation()
    print(f"Generated {len(COUNTRIES)} country selectors in {ROOT}")


if __name__ == "__main__":
    main()
