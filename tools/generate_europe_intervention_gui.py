from __future__ import annotations

import csv
import random
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT.parent
KR = WORKSHOP / "1521695605"
BASE_GAME = Path(r"D:\steam\steamapps\common\Hearts of Iron IV")
ASSET_DIR = ROOT / "gfx" / "interface" / "RUS_europe_intervention"
PREVIEW_DIR = WORKSHOP / "tmp" / "europe_gui"

MAP_WIDTH = 880
MAP_HEIGHT = 520
RENDER_SCALE = 2
RENDER_WIDTH = MAP_WIDTH * RENDER_SCALE
RENDER_HEIGHT = MAP_HEIGHT * RENDER_SCALE
MAP_X = 20
MAP_Y = 55
WINDOW_WIDTH = 920
WINDOW_HEIGHT = 660

# The game map is 5632x2048. This crop covers Iceland through the Caucasus and
# northern Scandinavia through the Mediterranean without flattening Europe.
SOURCE_CROP = (2290, 80, 3800, 870)

# Potential successor tags remain available when they appear later. Their
# clickable silhouettes use core states if they own no territory in 1936.
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


def parse_states() -> tuple[dict[int, int], dict[int, str], dict[str, set[int]]]:
    province_to_state: dict[int, int] = {}
    owner_by_state: dict[int, str] = {}
    cores_by_tag: dict[str, set[int]] = defaultdict(set)

    for path in sorted((KR / "history" / "states").glob("*.txt")):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        state_match = re.search(r"\bid\s*=\s*(\d+)", text)
        provinces_match = re.search(r"\bprovinces\s*=\s*\{([^}]*)\}", text, re.S)
        if not state_match or not provinces_match:
            continue
        state_id = int(state_match.group(1))
        for province_id in map(int, re.findall(r"\d+", provinces_match.group(1))):
            province_to_state[province_id] = state_id

        history_match = re.search(r"\bhistory\s*=\s*\{", text)
        history_text = text[history_match.end():] if history_match else text
        owner_match = re.search(r"\bowner\s*=\s*([A-Z0-9]{3})", history_text)
        if owner_match:
            owner_by_state[state_id] = owner_match.group(1)
        for tag in re.findall(r"\badd_core_of\s*=\s*([A-Z0-9]{3})", history_text):
            cores_by_tag[tag].add(state_id)

    return province_to_state, owner_by_state, cores_by_tag


def parse_definition(province_to_state: dict[int, int]) -> dict[tuple[int, int, int], int]:
    color_to_state: dict[tuple[int, int, int], int] = {}
    definition = KR / "map" / "definition.csv"
    with definition.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.reader(stream, delimiter=";"):
            if len(row) < 4 or not row[0].isdigit():
                continue
            province_id = int(row[0])
            state_id = province_to_state.get(province_id)
            if state_id is None:
                continue
            color_to_state[(int(row[1]), int(row[2]), int(row[3]))] = state_id
    return color_to_state


def parse_country_colors() -> dict[str, tuple[int, int, int]]:
    text = (KR / "common" / "countries" / "colors.txt").read_text(
        encoding="utf-8-sig", errors="replace"
    )
    colors: dict[str, tuple[int, int, int]] = {}
    for block_match in re.finditer(
        r"(?ms)^([A-Z0-9]{3})\s*=\s*\{(.*?)(?=^\})", text
    ):
        color_match = re.search(
            r"\bcolor\s*=\s*(?:rgb\s*)?\{\s*(\d+)\s+(\d+)\s+(\d+)",
            block_match.group(2),
            re.I,
        )
        if color_match:
            colors[block_match.group(1)] = tuple(map(int, color_match.groups()))
    return colors


def load_flag(tag: str) -> Image.Image | None:
    candidates = [
        KR / "gfx" / "flags" / f"{tag}.tga",
        BASE_GAME / "gfx" / "flags" / f"{tag}.tga",
        KR / "gfx" / "flags" / "medium" / f"{tag}.tga",
        BASE_GAME / "gfx" / "flags" / "medium" / f"{tag}.tga",
    ]
    for path in candidates:
        if path.exists():
            return Image.open(path).convert("RGBA")
    return None


def map_source_to_output(lon: float, lat: float) -> tuple[int, int]:
    source_width, source_height = 5632, 2048
    source_x = (lon + 180.0) / 360.0 * source_width
    source_y = (90.0 - lat) / 180.0 * source_height
    left, top, right, bottom = SOURCE_CROP
    x = round((source_x - left) / (right - left) * MAP_WIDTH)
    y = round((source_y - top) / (bottom - top) * MAP_HEIGHT)
    return max(7, min(MAP_WIDTH - 8, x)), max(7, min(MAP_HEIGHT - 8, y))


def build_state_pixels(
    color_to_state: dict[tuple[int, int, int], int],
    width: int,
    height: int,
) -> list[int]:
    provinces = Image.open(KR / "map" / "provinces.bmp").convert("RGB")
    sampled = provinces.crop(SOURCE_CROP).resize(
        (width, height), Image.Resampling.NEAREST
    )
    return [color_to_state.get(rgb, 0) for rgb in sampled.get_flattened_data()]


def mask_for_states(
    state_pixels: list[int], state_ids: set[int], width: int, height: int
) -> Image.Image:
    mask = bytearray(width * height)
    for index, state_id in enumerate(state_pixels):
        if state_id in state_ids:
            mask[index] = 255
    return Image.frombytes("L", (width, height), bytes(mask))


def fallback_mask(lon: float, lat: float) -> Image.Image:
    x, y = map_source_to_output(lon, lat)
    mask = Image.new("L", (MAP_WIDTH, MAP_HEIGHT), 0)
    ImageDraw.Draw(mask).ellipse((x - 7, y - 7, x + 7, y + 7), fill=255)
    return mask


def largest_component_point(mask: Image.Image) -> tuple[int, int]:
    width, height = mask.size
    pixels = mask.load()
    visited = bytearray(width * height)
    largest: list[tuple[int, int]] = []
    bbox = mask.getbbox()
    if not bbox:
        return width // 2, height // 2
    for start_y in range(bbox[1], bbox[3]):
        for start_x in range(bbox[0], bbox[2]):
            start_index = start_y * width + start_x
            if visited[start_index] or pixels[start_x, start_y] < 128:
                continue
            visited[start_index] = 1
            stack = [(start_x, start_y)]
            component: list[tuple[int, int]] = []
            while stack:
                x, y = stack.pop()
                component.append((x, y))
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    index = ny * width + nx
                    if visited[index] or pixels[nx, ny] < 128:
                        continue
                    visited[index] = 1
                    stack.append((nx, ny))
            if len(component) > len(largest):
                largest = component
    if not largest:
        return (bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2
    centre_x = round(sum(point[0] for point in largest) / len(largest))
    centre_y = round(sum(point[1] for point in largest) / len(largest))
    return min(
        largest,
        key=lambda point: (point[0] - centre_x) ** 2 + (point[1] - centre_y) ** 2,
    )


def muted_country_color(tag: str, colors: dict[str, tuple[int, int, int]]) -> tuple[int, int, int, int]:
    source = colors.get(tag)
    if source is None:
        rng = random.Random(sum(ord(char) for char in tag))
        source = (rng.randint(75, 175), rng.randint(70, 165), rng.randint(65, 155))
    paper = (104, 100, 83)
    mixed = tuple(round(channel * 0.68 + paper[index] * 0.32) for index, channel in enumerate(source))
    return (*mixed, 255)


def paste_flag_marker(panel: Image.Image, tag: str, mask: Image.Image) -> None:
    bbox = mask.getbbox()
    flag = load_flag(tag)
    if not bbox or flag is None:
        return
    territory_width = bbox[2] - bbox[0]
    territory_height = bbox[3] - bbox[1]
    if territory_width < 14 or territory_height < 10:
        return
    marker_width = max(16, min(30, territory_width // 3))
    marker_height = max(10, round(marker_width * 0.62))
    marker_width *= RENDER_SCALE
    marker_height *= RENDER_SCALE
    target_x, target_y = largest_component_point(mask)
    centre_x = target_x * RENDER_SCALE
    centre_y = target_y * RENDER_SCALE
    marker = Image.new("RGBA", (marker_width + 4, marker_height + 4), (23, 22, 18, 245))
    fitted = ImageOps.fit(flag, (marker_width, marker_height), method=Image.Resampling.LANCZOS)
    marker.alpha_composite(fitted, (2, 2))
    draw = ImageDraw.Draw(marker)
    draw.rectangle((0, 0, marker.width - 1, marker.height - 1), outline=(24, 21, 15, 255), width=2)
    draw.rectangle((2, 2, marker.width - 3, marker.height - 3), outline=(192, 165, 96, 235), width=1)
    panel.alpha_composite(marker, (centre_x - marker.width // 2, centre_y - marker.height // 2))


def outline_mask(mask: Image.Image, width: int = 1) -> Image.Image:
    expanded = mask.filter(ImageFilter.MaxFilter(width * 2 + 1))
    return ImageChops.subtract(expanded, mask)


def build_entry_button() -> None:
    width, height = 168, 48
    sheet = Image.new("RGBA", (width * 4, height), (0, 0, 0, 0))
    fills = ((45, 51, 45), (66, 67, 51), (65, 36, 34), (34, 36, 34))
    borders = ((142, 125, 81), (220, 190, 102), (177, 67, 55), (74, 72, 61))
    for frame_index, (fill, border) in enumerate(zip(fills, borders)):
        frame = Image.new("RGBA", (width, height), (*fill, 255))
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, 0, width - 1, height - 1), outline=(17, 17, 14, 255), width=2)
        draw.rectangle((3, 3, width - 4, height - 4), outline=(*border, 255), width=1)
        draw.ellipse((9, 8, 39, 38), fill=(32, 31, 27, 255), outline=(*border, 255), width=1)
        draw.ellipse((17, 14, 31, 30), outline=(181, 42, 35, 255), width=2)
        draw.line((24, 11, 24, 34), fill=(214, 192, 116, 255), width=1)
        draw.line((13, 23, 35, 23), fill=(214, 192, 116, 255), width=1)
        sheet.alpha_composite(frame, (frame_index * width, 0))
    sheet.save(ASSET_DIR / "entry_button.png")


def build_overview_button() -> None:
    width, height = 96, 28
    sheet = Image.new("RGBA", (width * 4, height), (0, 0, 0, 0))
    fills = ((58, 61, 54), (82, 81, 62), (76, 40, 37), (40, 41, 38))
    borders = ((143, 129, 89), (221, 194, 107), (168, 61, 52), (77, 75, 66))
    for frame_index, (fill, border) in enumerate(zip(fills, borders)):
        frame = Image.new("RGBA", (width, height), (*fill, 255))
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, 0, width - 1, height - 1), outline=(19, 18, 15, 255), width=2)
        draw.rectangle((3, 3, width - 4, height - 4), outline=(*border, 255), width=1)
        sheet.alpha_composite(frame, (frame_index * width, 0))
    sheet.save(ASSET_DIR / "overview_button.png")


def build_map_assets() -> dict[str, tuple[int, int, int, int]]:
    province_to_state, owner_by_state, cores_by_tag = parse_states()
    color_to_state = parse_definition(province_to_state)
    country_colors = parse_country_colors()
    state_pixels = build_state_pixels(color_to_state, RENDER_WIDTH, RENDER_HEIGHT)

    owned_states: dict[str, set[int]] = defaultdict(set)
    for state_id, tag in owner_by_state.items():
        owned_states[tag].add(state_id)

    panel = Image.new("RGBA", (RENDER_WIDTH, RENDER_HEIGHT), (31, 45, 47, 255))
    ocean = ImageDraw.Draw(panel, "RGBA")
    for y in range(0, RENDER_HEIGHT, 42):
        ocean.line((0, y, RENDER_WIDTH, y), fill=(112, 119, 109, 18), width=1)
    for x in range(0, RENDER_WIDTH, 74):
        ocean.line((x, 0, x, RENDER_HEIGHT), fill=(95, 102, 96, 10), width=1)

    land_mask = mask_for_states(
        state_pixels, set(owner_by_state), RENDER_WIDTH, RENDER_HEIGHT
    )
    panel.paste((91, 88, 73, 255), (0, 0, RENDER_WIDTH, RENDER_HEIGHT), land_mask)

    for tag in sorted(owned_states):
        mask = mask_for_states(
            state_pixels, owned_states[tag], RENDER_WIDTH, RENDER_HEIGHT
        )
        if mask.getbbox():
            panel.paste(
                muted_country_color(tag, country_colors),
                (0, 0, RENDER_WIDTH, RENDER_HEIGHT),
                mask,
            )

    owner_pixels = [owner_by_state.get(state_id, "") for state_id in state_pixels]
    country_border = bytearray(RENDER_WIDTH * RENDER_HEIGHT)
    state_border = bytearray(RENDER_WIDTH * RENDER_HEIGHT)
    for y in range(RENDER_HEIGHT):
        row = y * RENDER_WIDTH
        for x in range(RENDER_WIDTH):
            index = row + x
            owner = owner_pixels[index]
            if not owner:
                continue
            neighbours = []
            if x + 1 < RENDER_WIDTH:
                neighbours.append(index + 1)
            if y + 1 < RENDER_HEIGHT:
                neighbours.append(index + RENDER_WIDTH)
            for neighbour in neighbours:
                other_owner = owner_pixels[neighbour]
                # Only borders shared by two countries are political borders.
                # Treating sea and lake pixels as countries produced heavy
                # coastlines and conspicuous black rings around inland lakes.
                if other_owner and other_owner != owner:
                    country_border[index] = 255
                elif (
                    other_owner == owner
                    and state_pixels[neighbour]
                    and state_pixels[neighbour] != state_pixels[index]
                ):
                    state_border[index] = 110

    state_border_mask = Image.frombytes(
        "L", (RENDER_WIDTH, RENDER_HEIGHT), bytes(state_border)
    )
    country_border_mask = Image.frombytes(
        "L", (RENDER_WIDTH, RENDER_HEIGHT), bytes(country_border)
    )
    panel.alpha_composite(
        Image.composite(
            Image.new("RGBA", panel.size, (48, 43, 33, 120)),
            Image.new("RGBA", panel.size, (0, 0, 0, 0)),
            state_border_mask,
        )
    )
    panel.alpha_composite(
        Image.composite(
            Image.new("RGBA", panel.size, (55, 49, 39, 185)),
            Image.new("RGBA", panel.size, (0, 0, 0, 0)),
            country_border_mask,
        )
    )

    # Flags are KR's own assets and serve only as restrained map labels. The
    # complete territory silhouette remains the actual button and hit target.
    selector_tags = {tag for tag, _, _ in COUNTRIES}
    for tag in sorted(selector_tags.intersection(owned_states)):
        state_ids = owned_states[tag]
        high_mask = mask_for_states(
            state_pixels, state_ids, RENDER_WIDTH, RENDER_HEIGHT
        )
        final_mask = high_mask.resize((MAP_WIDTH, MAP_HEIGHT), Image.Resampling.LANCZOS)
        paste_flag_marker(panel, tag, final_mask)

    panel = ImageEnhance.Color(panel).enhance(0.82)
    panel = ImageEnhance.Contrast(panel).enhance(1.06)
    grain = Image.new("RGBA", panel.size, (0, 0, 0, 0))
    grain_pixels = grain.load()
    rng = random.Random(19360101)
    for y in range(RENDER_HEIGHT):
        for x in range(RENDER_WIDTH):
            value = rng.randint(-5, 5)
            grain_pixels[x, y] = (120 if value > 0 else 20, 100, 70, abs(value))
    panel = Image.alpha_composite(panel, grain)

    panel = panel.resize((MAP_WIDTH, MAP_HEIGHT), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(panel)
    draw.rectangle((1, 1, MAP_WIDTH - 2, MAP_HEIGHT - 2), outline=(15, 14, 12, 255), width=4)
    draw.rectangle((6, 6, MAP_WIDTH - 7, MAP_HEIGHT - 7), outline=(181, 154, 91, 235), width=1)
    draw.rectangle((9, 9, MAP_WIDTH - 10, MAP_HEIGHT - 10), outline=(73, 67, 50, 190), width=1)
    corner = 26
    brass = (210, 181, 103, 235)
    for x_sign, y_sign in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        x0 = 10 if x_sign > 0 else MAP_WIDTH - 11
        y0 = 10 if y_sign > 0 else MAP_HEIGHT - 11
        draw.line((x0, y0, x0 + x_sign * corner, y0), fill=brass, width=2)
        draw.line((x0, y0, x0, y0 + y_sign * corner), fill=brass, width=2)
    panel.save(ASSET_DIR / "europe_map_panel.png")
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    panel.save(PREVIEW_DIR / "preview_kr_1936.png")

    selector_boxes: dict[str, tuple[int, int, int, int]] = {}
    country_centres = {tag: (lon, lat) for tag, lon, lat in COUNTRIES}
    initial_tags = set(owned_states)
    ordered_tags = [tag for tag, _, _ in COUNTRIES if tag in initial_tags]
    ordered_tags += [tag for tag, _, _ in COUNTRIES if tag not in initial_tags]

    for tag in ordered_tags:
        state_ids = owned_states.get(tag) or cores_by_tag.get(tag, set())
        if state_ids:
            high_mask = mask_for_states(
                state_pixels, set(state_ids), RENDER_WIDTH, RENDER_HEIGHT
            )
            mask = high_mask.resize((MAP_WIDTH, MAP_HEIGHT), Image.Resampling.LANCZOS)
            mask = mask.point(lambda value: 255 if value >= 72 else 0)
        else:
            mask = Image.new("L", panel.size, 0)
        if not mask.getbbox():
            mask = fallback_mask(*country_centres[tag])
        mask = mask.filter(ImageFilter.MaxFilter(3))
        bbox = mask.getbbox()
        if not bbox:
            raise RuntimeError(f"Unable to build a map region for {tag}")
        bbox = (
            max(0, bbox[0] - 2), max(0, bbox[1] - 2),
            min(MAP_WIDTH, bbox[2] + 2), min(MAP_HEIGHT, bbox[3] + 2),
        )
        cropped_mask = mask.crop(bbox)
        width, height = cropped_mask.size

        normal = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        hover = Image.new("RGBA", (width, height), (222, 190, 92, 68))
        hover.putalpha(cropped_mask.point(lambda value: min(145, value // 2)))
        hover.alpha_composite(
            Image.composite(
                Image.new("RGBA", (width, height), (244, 215, 125, 255)),
                Image.new("RGBA", (width, height), (0, 0, 0, 0)),
                outline_mask(cropped_mask, 1),
            )
        )
        pressed = Image.new("RGBA", (width, height), (139, 31, 27, 125))
        pressed.putalpha(cropped_mask.point(lambda value: min(185, value * 3 // 4)))
        disabled = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        sheet = Image.new("RGBA", (width * 4, height), (0, 0, 0, 0))
        for frame_index, frame in enumerate((normal, hover, pressed, disabled)):
            sheet.alpha_composite(frame, (frame_index * width, 0))
        sheet.save(ASSET_DIR / f"{tag}_button.png")

        selected = Image.new("RGBA", (width, height), (151, 34, 29, 78))
        selected.putalpha(cropped_mask.point(lambda value: min(128, value // 2)))
        selected.alpha_composite(
            Image.composite(
                Image.new("RGBA", (width, height), (237, 204, 108, 255)),
                Image.new("RGBA", (width, height), (0, 0, 0, 0)),
                outline_mask(cropped_mask, 2),
            )
        )
        selected.save(ASSET_DIR / f"{tag}_selected.png")
        selector_boxes[tag] = bbox

    obsolete = ASSET_DIR / "selected_frame.png"
    if obsolete.exists():
        obsolete.unlink()
    return selector_boxes


def build_gfx(selector_boxes: dict[str, tuple[int, int, int, int]]) -> None:
    lines = [
        "spriteTypes = {",
        "\tspriteType = {",
        '\t\tname = "GFX_RUS_europe_intervention_map_panel"',
        '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/europe_map_panel.png"',
        "\t}",
        "",
        "\tspriteType = {",
        '\t\tname = "GFX_RUS_europe_intervention_entry_button"',
        '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/entry_button.png"',
        "\t\tnoOfFrames = 4",
        "\t}",
        "",
        "\tspriteType = {",
        '\t\tname = "GFX_RUS_europe_intervention_overview_button"',
        '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/overview_button.png"',
        "\t\tnoOfFrames = 4",
        "\t}",
    ]
    for tag, _, _ in COUNTRIES:
        lines.extend([
            "",
            "\tspriteType = {",
            f'\t\tname = "GFX_RUS_europe_intervention_{tag}_button"',
            f'\t\ttexturefile = "gfx/interface/RUS_europe_intervention/{tag}_button.png"',
            "\t\tnoOfFrames = 4",
            "\t}",
            "",
            "\tspriteType = {",
            f'\t\tname = "GFX_RUS_europe_intervention_{tag}_selected"',
            f'\t\ttexturefile = "gfx/interface/RUS_europe_intervention/{tag}_selected.png"',
            "\t}",
        ])
    lines.append("}")
    (ROOT / "interface" / "RUS_europe_intervention.gfx").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def build_gui(selector_boxes: dict[str, tuple[int, int, int, int]]) -> None:
    lines = [
        "guiTypes = {",
        "\tcontainerWindowType = {",
        '\t\tname = "RUS_europe_intervention_entry_window"',
        "\t\tposition = { x = 367 y = 432 }",
        "\t\tsize = { width = 168 height = 48 }",
        "\t\tclipping = no",
        "",
        "\t\tbuttonType = {",
        '\t\t\tname = "RUS_europe_intervention_open_button"',
        "\t\t\tposition = { x = 0 y = 0 }",
        '\t\t\tquadTextureSprite = "GFX_RUS_europe_intervention_entry_button"',
        '\t\t\tbuttonText = "RUS_europe_intervention_entry_button"',
        '\t\t\tbuttonFont = "hoi_16mbs"',
        '\t\t\tpdx_tooltip = "RUS_europe_intervention_entry_tt"',
        '\t\t\tclicksound = "menu_open_window"',
        "\t\t}",
        "\t}",
        "",
        "\tcontainerWindowType = {",
        '\t\tname = "RUS_europe_intervention_window"',
        "\t\tposition = { x = 550 y = 0 }",
        f"\t\tsize = {{ width = {WINDOW_WIDTH} height = {WINDOW_HEIGHT} }}",
        "\t\tclipping = no",
        "",
        "\t\tbackground = {",
        '\t\t\tname = "Background"',
        '\t\t\tquadTextureSprite = "GFX_tiled_plain_bg"',
        "\t\t}",
        "",
        "\t\ticonType = {",
        '\t\t\tname = "RUS_europe_intervention_header"',
        "\t\t\tposition = { x = 5 y = 4 }",
        '\t\t\tspriteType = "GFX_header_bg"',
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_title"',
        "\t\t\tposition = { x = 100 y = 10 }",
        '\t\t\tfont = "hoi_28header"',
        '\t\t\ttext = "RUS_europe_intervention_title"',
        "\t\t\tformat = center",
        "\t\t\tmaxWidth = 720",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "",
        "\t\tbuttonType = {",
        '\t\t\tname = "RUS_europe_intervention_close_button"',
        "\t\t\tposition = { x = -42 y = 8 }",
        '\t\t\tquadTextureSprite = "GFX_closebutton"',
        '\t\t\tOrientation = "UPPER_RIGHT"',
        '\t\t\tclicksound = "click_close"',
        '\t\t\tpdx_tooltip = "CLOSE"',
        "\t\t}",
        "",
        "\t\ticonType = {",
        '\t\t\tname = "RUS_europe_intervention_map"',
        f"\t\t\tposition = {{ x = {MAP_X} y = {MAP_Y} }}",
        '\t\t\tspriteType = "GFX_RUS_europe_intervention_map_panel"',
        "\t\t\talwaystransparent = yes",
        "\t\t}",
    ]

    _, owner_by_state, _ = parse_states()
    initial_tags = set(owner_by_state.values())
    ordered_tags = [tag for tag, _, _ in COUNTRIES if tag in initial_tags]
    ordered_tags += [tag for tag, _, _ in COUNTRIES if tag not in initial_tags]
    for tag in ordered_tags:
        left, top, _, _ = selector_boxes[tag]
        lines.extend([
            "",
            "\t\tbuttonType = {",
            f'\t\t\tname = "RUS_europe_intervention_{tag}_button"',
            f"\t\t\tposition = {{ x = {MAP_X + left} y = {MAP_Y + top} }}",
            f'\t\t\tquadTextureSprite = "GFX_RUS_europe_intervention_{tag}_button"',
            '\t\t\tclicksound = "click_default"',
            f'\t\t\tpdx_tooltip = "RUS_europe_intervention_{tag}_tt"',
            "\t\t}",
            "",
            "\t\ticonType = {",
            f'\t\t\tname = "RUS_europe_intervention_{tag}_selected"',
            f"\t\t\tposition = {{ x = {MAP_X + left} y = {MAP_Y + top} }}",
            f'\t\t\tspriteType = "GFX_RUS_europe_intervention_{tag}_selected"',
            f'\t\t\tpdx_tooltip = "RUS_europe_intervention_{tag}_tt"',
            "\t\t\talwaystransparent = yes",
            "\t\t}",
        ])

    lines.extend([
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_no_selection"',
        "\t\t\tposition = { x = 20 y = 586 }",
        '\t\t\tfont = "hoi_18mbs"',
        '\t\t\ttext = "RUS_europe_intervention_no_selection"',
        "\t\t\tformat = left",
        "\t\t\tmaxWidth = 740",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
    ])
    for tag, _, _ in COUNTRIES:
        lines.extend([
            "",
            "\t\tinstantTextBoxType = {",
            f'\t\t\tname = "RUS_europe_intervention_{tag}_selected_name"',
            "\t\t\tposition = { x = 20 y = 586 }",
            '\t\t\tfont = "hoi_18mbs"',
            f'\t\t\ttext = "RUS_europe_intervention_{tag}_selected_name"',
            "\t\t\tformat = left",
            "\t\t\tmaxWidth = 740",
            "\t\t\talwaystransparent = yes",
            "\t\t}",
        ])
    lines.extend([
        "",
        "\t\tbuttonType = {",
        '\t\t\tname = "RUS_europe_intervention_overview_button"',
        "\t\t\tposition = { x = 804 y = 580 }",
        '\t\t\tquadTextureSprite = "GFX_RUS_europe_intervention_overview_button"',
        '\t\t\tbuttonText = "RUS_europe_intervention_overview_button"',
        '\t\t\tbuttonFont = "hoi_16mbs"',
        '\t\t\tpdx_tooltip = "RUS_europe_intervention_overview_tt"',
        "\t\t}",
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_help"',
        "\t\t\tposition = { x = 20 y = 626 }",
        '\t\t\tfont = "hoi_16mbs"',
        '\t\t\ttext = "RUS_europe_intervention_help"',
        "\t\t\tformat = left",
        "\t\t\tmaxWidth = 878",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "\t}",
        "}",
    ])
    (ROOT / "interface" / "RUS_europe_intervention.gui").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def build_scripted_gui() -> None:
    visible = [
        "\t\t\toriginal_tag = RUS",
        "\t\t\thas_socialist_government = yes",
        "\t\t\thas_completed_focus = RUS_self_determination",
    ]
    lines = [
        "scripted_gui = {",
        "\tRUS_europe_intervention_entry_gui = {",
        "\t\tcontext_type = player_context",
        '\t\tparent_window_name = "countrypoliticsview"',
        '\t\twindow_name = "RUS_europe_intervention_entry_window"',
        "\t\tai_enabled = { always = no }",
        "\t\tvisible = {",
        *visible,
        "\t\t}",
        "\t\ttriggers = {",
        "\t\t\tRUS_europe_intervention_open_button_click_enabled = { always = yes }",
        "\t\t}",
        "\t\teffects = {",
        "\t\t\tRUS_europe_intervention_open_button_click = {",
        "\t\t\t\tif = {",
        "\t\t\t\t\tlimit = { has_country_flag = RUS_europe_intervention_window_open }",
        "\t\t\t\t\tclr_country_flag = RUS_europe_intervention_window_open",
        "\t\t\t\t}",
        "\t\t\t\telse = { set_country_flag = RUS_europe_intervention_window_open }",
        "\t\t\t}",
        "\t\t}",
        "\t}",
        "",
        "\tRUS_europe_intervention_gui = {",
        "\t\tcontext_type = player_context",
        '\t\tparent_window_name = "countrypoliticsview"',
        '\t\twindow_name = "RUS_europe_intervention_window"',
        "\t\tai_enabled = { always = no }",
        "\t\tvisible = {",
        *visible,
        "\t\t\thas_country_flag = RUS_europe_intervention_window_open",
        "\t\t}",
        "\t\ttriggers = {",
        "\t\t\tRUS_europe_intervention_close_button_click_enabled = { always = yes }",
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
    lines.extend([
        "\t\t}",
        "\t\teffects = {",
        "\t\t\tRUS_europe_intervention_close_button_click = { clr_country_flag = RUS_europe_intervention_window_open }",
        "\t\t\tRUS_europe_intervention_overview_button_click = { RUS_clear_europe_intervention_selection = yes }",
    ])
    for tag, _, _ in COUNTRIES:
        lines.extend([
            f"\t\t\tRUS_europe_intervention_{tag}_button_click = {{",
            "\t\t\t\tRUS_clear_europe_intervention_selection = yes",
            "\t\t\t\tset_country_flag = RUS_europe_intervention_filter_active",
            f"\t\t\t\tset_country_flag = RUS_europe_intervention_selected_{tag}",
            "\t\t\t}",
        ])
    lines.extend(["\t\t}", "\t}", "}"])
    (ROOT / "common" / "scripted_guis" / "RUS_europe_intervention.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def build_scripted_effect_and_trigger() -> None:
    effect_lines = [
        "RUS_clear_europe_intervention_selection = {",
        "\tclr_country_flag = RUS_europe_intervention_filter_active",
    ]
    for tag, _, _ in COUNTRIES:
        effect_lines.append(f"\tclr_country_flag = RUS_europe_intervention_selected_{tag}")
    effect_lines.append("}")
    (ROOT / "common" / "scripted_effects" / "RUS_europe_intervention_effects.txt").write_text(
        "\n".join(effect_lines) + "\n", encoding="utf-8"
    )

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
        trigger_lines.extend(
            f"\t\thas_country_flag = RUS_europe_intervention_selected_{tag}" for tag in tags
        )
        trigger_lines.extend(["\t}", "}", ""])
    (ROOT / "common" / "scripted_triggers" / "RUS_europe_intervention_triggers.txt").write_text(
        "\n".join(trigger_lines), encoding="utf-8"
    )


def build_localisation() -> None:
    languages = {
        "simp_chinese": {
            "title": "欧洲革命事务局",
            "entry": "欧洲革命事务",
            "entry_tt": "打开§Y欧洲革命事务局§!地图，选择需要处理的国家。",
            "none": "§Y欧洲总览§!：显示当前全部可用的革命外交与干涉决议",
            "help": "点击地图中的国家领土以筛选该国事务；随后打开决议栏查看对应决议。“总览”将恢复完整列表。",
            "overview": "总览",
            "overview_tt": "取消国家筛选，恢复显示全部可用决议。",
            "selected": "§Y已选目标：§!",
            "tooltip": "点击该国领土，仅显示与该国对应的可用决议。",
        },
        "english": {
            "title": "Bureau of European Revolutionary Affairs",
            "entry": "European Affairs",
            "entry_tt": "Open the §YBureau of European Revolutionary Affairs§! and select a country.",
            "none": "§YEuropean overview§!: show all currently available revolutionary and intervention decisions",
            "help": "Select a country's territory, then open Decisions to see the matching actions. Overview restores the full list.",
            "overview": "Overview",
            "overview_tt": "Clear the country filter and show every available decision.",
            "selected": "§YSelected target:§!",
            "tooltip": "Select this territory to show available decisions concerning the country.",
        },
        "russian": {
            "title": "Бюро европейских революционных дел",
            "entry": "Дела Европы",
            "entry_tt": "Открыть §YБюро европейских революционных дел§! и выбрать страну.",
            "none": "§YОбзор Европы§!: показать все доступные решения по революционной дипломатии и вмешательству",
            "help": "Выберите территорию страны, затем откройте решения. «Обзор» вернёт полный список.",
            "overview": "Обзор",
            "overview_tt": "Снять фильтр страны и показать все доступные решения.",
            "selected": "§YВыбранная цель:§!",
            "tooltip": "Выбрать территорию и показать доступные решения по этой стране.",
        },
    }
    for language, loc in languages.items():
        lines = [
            f"l_{language}:",
            f' RUS_europe_intervention_title:0 "{loc["title"]}"',
            f' RUS_europe_intervention_entry_button:0 "{loc["entry"]}"',
            f' RUS_europe_intervention_entry_tt:0 "{loc["entry_tt"]}"',
            f' RUS_europe_intervention_no_selection:0 "{loc["none"]}"',
            f' RUS_europe_intervention_help:0 "{loc["help"]}"',
            f' RUS_europe_intervention_overview_button:0 "{loc["overview"]}"',
            f' RUS_europe_intervention_overview_tt:0 "{loc["overview_tt"]}"',
        ]
        for tag, _, _ in COUNTRIES:
            lines.append(
                f' RUS_europe_intervention_{tag}_selected_name:0 "{loc["selected"]} [{tag}.GetNameWithFlag]"'
            )
            lines.append(
                f' RUS_europe_intervention_{tag}_tt:0 "§Y[{tag}.GetName]§!\\n{loc["tooltip"]}"'
            )
        path = ROOT / "localisation" / language / f"RUS_europe_intervention_l_{language}.yml"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    build_entry_button()
    build_overview_button()
    selector_boxes = build_map_assets()
    build_gfx(selector_boxes)
    build_gui(selector_boxes)
    build_scripted_gui()
    build_scripted_effect_and_trigger()
    build_localisation()
    print(
        f"Generated KR 1936 Europe map ({MAP_WIDTH}x{MAP_HEIGHT}) and "
        f"{len(selector_boxes)} territory selectors in {ROOT}"
    )


if __name__ == "__main__":
    main()
