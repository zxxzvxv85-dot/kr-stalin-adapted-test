from __future__ import annotations

import colorsys
import csv
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT.parent
KR = WORKSHOP / "1521695605"
BASE_GAME = Path(r"D:\steam\steamapps\common\Hearts of Iron IV")
ASSET_DIR = ROOT / "gfx" / "interface" / "RUS_europe_intervention"
PREVIEW_DIR = WORKSHOP / "tmp" / "europe_gui"
GENERATED_MAP_SOURCE = ROOT / "output" / "imagegen" / "europe-intervention-soviet-map-v1.png"

MAP_WIDTH = 700
MAP_HEIGHT = 414
RENDER_SCALE = 4
RENDER_WIDTH = MAP_WIDTH * RENDER_SCALE
RENDER_HEIGHT = MAP_HEIGHT * RENDER_SCALE
MAP_X = 15
MAP_Y = 16
WINDOW_WIDTH = 740
WINDOW_HEIGHT = 526
TITLE_HEIGHT = 44
MAP_WINDOW_Y = TITLE_HEIGHT
PORTRAIT_X = 525
PORTRAIT_Y = 584
PORTRAIT_WIDTH = 180
PORTRAIT_HEIGHT = 202

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
    ("AZR", 47.5, 40.3), ("PER", 53.0, 32.0),
]


@dataclass(frozen=True)
class RegionSelector:
    key: str
    members: tuple[str, ...]
    parts: tuple[str, ...]
    color_tag: str


@dataclass(frozen=True)
class MapHotspot:
    key: str
    selector_key: str
    part_tag: str
    longitude: float
    latitude: float


GROUP_SELECTORS = (
    RegionSelector(
        "NORDICS",
        ("ICE", "NOR", "SWE", "FIN", "DEN"),
        ("ICE", "NOR", "SWE", "FIN", "DEN"),
        "SCA",
    ),
    RegionSelector(
        "CENTRAL_EUROPE",
        ("HOL", "BEL", "FLA", "WAL", "GER", "SWI", "PRE", "NGF", "RHI", "BAY"),
        ("HOL", "BEL", "GER", "SWI"),
        "GER",
    ),
    RegionSelector(
        "AUSTRIA_HUNGARY",
        ("AUS", "HUN", "CZE", "GAL", "CRO", "SLO", "BOS"),
        ("AUS", "HUN", "CZE", "GAL", "CRO"),
        "AUS",
    ),
    RegionSelector(
        "ITALY",
        ("ITA", "SRI", "SIC", "PAP", "SRD", "VNC", "LOM", "EMI", "TUS", "TRS"),
        ("ITA", "SRI", "SIC", "PAP", "SRD"),
        "SRI",
    ),
    RegionSelector(
        "BALKANS",
        ("SER", "ROM", "GRE", "ALB", "BUL"),
        ("SER", "ROM", "GRE", "ALB", "BUL"),
        "SER",
    ),
)


def build_selectors() -> tuple[RegionSelector, ...]:
    group_by_member = {
        member: selector
        for selector in GROUP_SELECTORS
        for member in selector.members
    }
    selectors: list[RegionSelector] = []
    added_groups: set[str] = set()
    for tag, _, _ in COUNTRIES:
        group = group_by_member.get(tag)
        if group is not None:
            if group.key not in added_groups:
                selectors.append(group)
                added_groups.add(group.key)
            continue
        selectors.append(RegionSelector(tag, (tag,), (tag,), tag))
    return tuple(selectors)


SELECTORS = build_selectors()
SELECTOR_BY_KEY = {selector.key: selector for selector in SELECTORS}
SELECTOR_BY_MEMBER = {
    member: selector
    for selector in SELECTORS
    for member in selector.members
}
COUNTRY_CENTRES = {tag: (longitude, latitude) for tag, longitude, latitude in COUNTRIES}
HOTSPOTS = tuple(
    MapHotspot(
        part if len(selector.parts) == 1 else f"{selector.key}_{part}",
        selector.key,
        part,
        *COUNTRY_CENTRES[part],
    )
    for selector in SELECTORS
    for part in selector.parts
)
HOTSPOT_BY_KEY = {hotspot.key: hotspot for hotspot in HOTSPOTS}


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


def muted_country_color(tag: str, colors: dict[str, tuple[int, int, int]]) -> tuple[int, int, int, int]:
    if tag in {"RUS", "SOV"}:
        return (154, 120, 105, 255)

    source = colors.get(tag)
    if source is None:
        rng = random.Random(sum(ord(char) for char in tag))
        source = (rng.randint(75, 175), rng.randint(70, 165), rng.randint(65, 155))

    hue, saturation, value = colorsys.rgb_to_hsv(*(channel / 255 for channel in source))
    saturation = max(0.07, min(0.18, saturation * 0.24))
    value = max(0.56, min(0.70, value * 0.55 + 0.24))
    restrained = tuple(round(channel * 255) for channel in colorsys.hsv_to_rgb(hue, saturation, value))
    paper = (166, 155, 126)
    mixed = tuple(round(channel * 0.32 + paper[index] * 0.68) for index, channel in enumerate(restrained))
    return (*mixed, 255)


def outline_mask(mask: Image.Image, width: int = 1) -> Image.Image:
    expanded = mask.filter(ImageFilter.MaxFilter(width * 2 + 1))
    return ImageChops.subtract(expanded, mask)


def build_category_icon() -> None:
    source = Image.open(
        KR / "gfx" / "interface" / "goals" / "goal_communist_world_revolution.png"
    ).convert("RGBA")
    fitted = ImageOps.contain(source, (35, 40), Image.Resampling.LANCZOS)
    icon = Image.new("RGBA", (51, 40), (0, 0, 0, 0))
    icon.alpha_composite(fitted, ((icon.width - fitted.width) // 2, 0))
    icon.save(ASSET_DIR / "category_icon.png")


def build_entry_button() -> None:
    background = Image.open(
        BASE_GAME
        / "gfx"
        / "interface"
        / "government_in_exile"
        / "countryview_government_in_exile_bg.dds"
    ).convert("RGBA")
    source = Image.open(
        KR / "gfx" / "interface" / "goals" / "goal_communist_world_revolution.png"
    ).convert("RGBA")
    fitted = ImageOps.contain(source, (55, 55), Image.Resampling.LANCZOS)
    width, height = background.size
    sheet = Image.new("RGBA", (width * 4, height), (0, 0, 0, 0))
    states = (
        (1.00, 1.00, 255, 0),
        (1.12, 1.12, 255, 0),
        (0.86, 1.06, 255, 1),
        (0.58, 0.20, 150, 0),
    )
    for frame_index, (brightness, colour, alpha, y_offset) in enumerate(states):
        frame = ImageEnhance.Brightness(background).enhance(brightness)
        artwork = ImageEnhance.Color(fitted).enhance(colour)
        artwork = ImageEnhance.Brightness(artwork).enhance(brightness)
        if alpha < 255:
            artwork.putalpha(artwork.getchannel("A").point(lambda value: value * alpha // 255))
        frame.alpha_composite(
            artwork,
            (4, (height - artwork.height) // 2 + y_offset),
        )
        draw = ImageDraw.Draw(frame)
        draw.line((61, 7, 61, height - 8), fill=(19, 18, 15, 235), width=2)
        draw.line((63, 8, 63, height - 9), fill=(113, 101, 72, 180), width=1)
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

    # KX-style layered map construction, recast as a Soviet 1930s planning
    # chart: one aged sheet, restrained printed washes, and fine ink rules.
    panel = Image.new("RGBA", (RENDER_WIDTH, RENDER_HEIGHT), (117, 128, 119, 255))
    ocean = ImageDraw.Draw(panel, "RGBA")
    for longitude in range(-20, 61, 10):
        x, _ = map_source_to_output(longitude, 50)
        x *= RENDER_SCALE
        ocean.line((x, 0, x, RENDER_HEIGHT), fill=(79, 86, 76, 24), width=2)
    for latitude in range(30, 71, 10):
        _, y = map_source_to_output(20, latitude)
        y *= RENDER_SCALE
        ocean.line((0, y, RENDER_WIDTH, y), fill=(79, 86, 76, 24), width=2)

    land_mask = mask_for_states(
        state_pixels, set(owner_by_state), RENDER_WIDTH, RENDER_HEIGHT
    )
    panel.paste((166, 155, 126, 255), (0, 0, RENDER_WIDTH, RENDER_HEIGHT), land_mask)

    for tag in sorted(owned_states):
        mask = mask_for_states(state_pixels, owned_states[tag], RENDER_WIDTH, RENDER_HEIGHT)
        if mask.getbbox():
            panel.paste(
                muted_country_color(tag, country_colors),
                (0, 0, RENDER_WIDTH, RENDER_HEIGHT),
                mask,
            )

    for selector in GROUP_SELECTORS:
        state_ids = set().union(*(owned_states.get(part, set()) for part in selector.parts))
        if state_ids:
            mask = mask_for_states(state_pixels, state_ids, RENDER_WIDTH, RENDER_HEIGHT)
            panel.paste(
                muted_country_color(selector.color_tag, country_colors),
                (0, 0, RENDER_WIDTH, RENDER_HEIGHT),
                mask,
            )

    display_region = {
        part: selector.key
        for selector in GROUP_SELECTORS
        for part in selector.parts
    }
    owner_pixels = [
        display_region.get(owner_by_state.get(state_id, ""), owner_by_state.get(state_id, ""))
        for state_id in state_pixels
    ]
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
    state_rule = state_border_mask.filter(ImageFilter.MaxFilter(3))
    country_rule = country_border_mask.filter(ImageFilter.MaxFilter(5))
    panel.alpha_composite(
        Image.composite(
            Image.new("RGBA", panel.size, (92, 82, 61, 68)),
            Image.new("RGBA", panel.size, (0, 0, 0, 0)),
            state_rule,
        )
    )
    panel.alpha_composite(
        Image.composite(
            Image.new("RGBA", panel.size, (57, 49, 37, 178)),
            Image.new("RGBA", panel.size, (0, 0, 0, 0)),
            country_rule,
        )
    )

    coastline = outline_mask(land_mask, 2).filter(ImageFilter.MaxFilter(3))
    panel.alpha_composite(
        Image.composite(
            Image.new("RGBA", panel.size, (55, 88, 88, 178)),
            Image.new("RGBA", panel.size, (0, 0, 0, 0)),
            coastline,
        )
    )

    panel = ImageEnhance.Color(panel).enhance(0.66)
    panel = ImageEnhance.Contrast(panel).enhance(1.08)

    rng = random.Random(19360305)
    fine_noise = Image.frombytes(
        "L",
        panel.size,
        rng.randbytes(RENDER_WIDTH * RENDER_HEIGHT),
    ).filter(ImageFilter.GaussianBlur(1.2))
    coarse_width = max(1, RENDER_WIDTH // 18)
    coarse_height = max(1, RENDER_HEIGHT // 18)
    coarse_noise = Image.frombytes(
        "L",
        (coarse_width, coarse_height),
        rng.randbytes(coarse_width * coarse_height),
    ).resize(panel.size, Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(8))
    noise = Image.blend(fine_noise, coarse_noise, 0.70)
    paper_light = Image.new("RGBA", panel.size, (218, 199, 151, 0))
    paper_light.putalpha(noise.point(lambda value: max(0, value - 158) // 5))
    panel = Image.alpha_composite(panel, paper_light)
    paper_dark = Image.new("RGBA", panel.size, (39, 35, 28, 0))
    paper_dark.putalpha(noise.point(lambda value: max(0, 100 - value) // 6))
    panel = Image.alpha_composite(panel, paper_dark)

    edge = Image.new("RGBA", panel.size, (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(edge, "RGBA")
    for inset, alpha in ((0, 150), (3, 90), (8, 38), (16, 18)):
        edge_draw.rectangle(
            (inset, inset, RENDER_WIDTH - 1 - inset, RENDER_HEIGHT - 1 - inset),
            outline=(33, 29, 24, alpha),
            width=max(1, RENDER_SCALE),
        )
    panel = Image.alpha_composite(panel, edge)

    if GENERATED_MAP_SOURCE.exists():
        panel = Image.open(GENERATED_MAP_SOURCE).convert("RGBA").resize(
            (MAP_WIDTH, MAP_HEIGHT),
            Image.Resampling.LANCZOS,
        )
    else:
        panel = panel.resize((MAP_WIDTH, MAP_HEIGHT), Image.Resampling.LANCZOS)
    panel.save(ASSET_DIR / "europe_map_panel.png")

    selector_boxes: dict[str, tuple[int, int, int, int]] = {}
    initial_tags = set(owned_states)
    ordered_hotspots = [hotspot for hotspot in HOTSPOTS if hotspot.part_tag in initial_tags]
    ordered_hotspots += [hotspot for hotspot in HOTSPOTS if hotspot.part_tag not in initial_tags]
    for hotspot in ordered_hotspots:
        state_ids = owned_states.get(hotspot.part_tag) or cores_by_tag.get(
            hotspot.part_tag, set()
        )
        if state_ids:
            high_mask = mask_for_states(
                state_pixels, set(state_ids), RENDER_WIDTH, RENDER_HEIGHT
            )
            display_mask = high_mask.resize(
                (MAP_WIDTH, MAP_HEIGHT), Image.Resampling.LANCZOS
            )
            mask = display_mask.point(lambda value: 255 if value >= 72 else 0)
        else:
            mask = Image.new("L", panel.size, 0)
            display_mask = mask.copy()
        if not mask.getbbox():
            mask = fallback_mask(hotspot.longitude, hotspot.latitude)
            display_mask = mask.copy()
        mask = mask.filter(ImageFilter.MaxFilter(3))
        bbox = mask.getbbox()
        if not bbox:
            raise RuntimeError(f"Unable to build a map region for {hotspot.key}")
        bbox = (
            max(0, bbox[0] - 2),
            max(0, bbox[1] - 2),
            min(MAP_WIDTH, bbox[2] + 2),
            min(MAP_HEIGHT, bbox[3] + 2),
        )
        cropped_mask = mask.crop(bbox)
        cropped_display_mask = display_mask.crop(bbox)
        width, height = cropped_mask.size
        display_edge_source = cropped_display_mask.point(
            lambda value: 255 if value >= 96 else 0
        )
        fine_edge = outline_mask(display_edge_source, 1).filter(
            ImageFilter.GaussianBlur(0.28)
        )

        normal = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        hover = Image.new("RGBA", (width, height), (165, 91, 73, 58))
        hover.putalpha(cropped_display_mask.point(lambda value: min(88, value // 3)))
        hover.alpha_composite(
            Image.composite(
                Image.new("RGBA", (width, height), (93, 63, 49, 215)),
                Image.new("RGBA", (width, height), (0, 0, 0, 0)),
                fine_edge,
            )
        )
        pressed = Image.new("RGBA", (width, height), (130, 39, 32, 135))
        pressed.putalpha(cropped_mask.point(lambda value: min(185, value * 3 // 4)))
        disabled = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        sheet = Image.new("RGBA", (width * 4, height), (0, 0, 0, 0))
        for frame_index, frame in enumerate((normal, hover, pressed, disabled)):
            sheet.alpha_composite(frame, (frame_index * width, 0))
        sheet.save(ASSET_DIR / f"{hotspot.key}_button.png")

        selected_rng = random.Random(1936 + sum(ord(char) for char in hotspot.key))
        texture_width = max(2, width // 5)
        texture_height = max(2, height // 5)
        selected_texture = Image.frombytes(
            "L",
            (texture_width, texture_height),
            selected_rng.randbytes(texture_width * texture_height),
        ).resize((width, height), Image.Resampling.BICUBIC)
        selected_alpha = ImageChops.multiply(
            cropped_display_mask,
            selected_texture.point(lambda value: 76 + value // 7),
        )
        selected = Image.new("RGBA", (width, height), (127, 59, 50, 0))
        selected.putalpha(selected_alpha)
        selected.alpha_composite(
            Image.composite(
                Image.new("RGBA", (width, height), (68, 49, 39, 232)),
                Image.new("RGBA", (width, height), (0, 0, 0, 0)),
                fine_edge,
            )
        )
        selected.save(ASSET_DIR / f"{hotspot.key}_selected.png")
        selector_boxes[hotspot.key] = bbox

    obsolete = ASSET_DIR / "selected_frame.png"
    if obsolete.exists():
        obsolete.unlink()
    return selector_boxes


def build_gfx(selector_boxes: dict[str, tuple[int, int, int, int]]) -> None:
    lines = [
        "spriteTypes = {",
        "\tspriteType = {",
        '\t\tname = "GFX_RUS_europe_intervention_category_icon"',
        '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/category_icon.png"',
        "\t}",
        "",
        "\tspriteType = {",
        '\t\tname = "GFX_RUS_europe_intervention_entry_button"',
        '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/entry_button.png"',
        "\t\tnoOfFrames = 4",
        '\t\teffectFile = "gfx/FX/buttonstate.lua"',
        "\t}",
        "",
        "\tspriteType = {",
        '\t\tname = "GFX_RUS_europe_intervention_map_panel"',
        '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/europe_map_panel.png"',
        "\t}",
        "",
        "\tspriteType = {",
        '\t\tname = "GFX_RUS_europe_intervention_decision_portrait"',
        '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/decision_portrait.png"',
        "\t}",
        "",
        "\tspriteType = {",
        '\t\tname = "GFX_RUS_europe_intervention_overview_button"',
        '\t\ttexturefile = "gfx/interface/RUS_europe_intervention/overview_button.png"',
        "\t\tnoOfFrames = 4",
        "\t}",
    ]
    for hotspot_key in selector_boxes:
        lines.extend([
            "",
            "\tspriteType = {",
            f'\t\tname = "GFX_RUS_europe_intervention_{hotspot_key}_button"',
            f'\t\ttexturefile = "gfx/interface/RUS_europe_intervention/{hotspot_key}_button.png"',
            "\t\tnoOfFrames = 4",
            "\t}",
            "",
            "\tspriteType = {",
            f'\t\tname = "GFX_RUS_europe_intervention_{hotspot_key}_selected"',
            f'\t\ttexturefile = "gfx/interface/RUS_europe_intervention/{hotspot_key}_selected.png"',
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
        "\t\tposition = { x = 0 y = 0 }",
        "\t\tsize = { width = 129 height = 57 }",
        "\t\tclipping = no",
        "",
        "\t\ticonType = {",
        '\t\t\tname = "RUS_europe_intervention_entry_icon"',
        "\t\t\tposition = { x = 0 y = 0 }",
        '\t\t\tspriteType = "GFX_RUS_europe_intervention_entry_button"',
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_entry_label_text"',
        "\t\t\tposition = { x = 63 y = 18 }",
        '\t\t\tfont = "hoi_16mbs"',
        '\t\t\ttext = "RUS_europe_intervention_entry_button"',
        "\t\t\tformat = center",
        "\t\t\tfixedsize = yes",
        "\t\t\tmaxWidth = 62",
        "\t\t\tmaxHeight = 20",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "\t}",
        "",
        "\tcontainerWindowType = {",
        '\t\tname = "RUS_europe_intervention_header_window"',
        "\t\tposition = { x = 0 y = 0 }",
        f"\t\tsize = {{ width = {WINDOW_WIDTH} height = {TITLE_HEIGHT} }}",
        "\t\tclipping = no",
        '\t\tbackground = { name = "Background" quadTextureSprite = "GFX_tiled_header_1" }',
        "",
        "\t\ticonType = {",
        '\t\t\tname = "RUS_europe_intervention_header_emblem"',
        "\t\t\tposition = { x = 9 y = 2 }",
        '\t\t\tspriteType = "GFX_RUS_europe_intervention_category_icon"',
        "\t\t\tscale = 0.9",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_header_title"',
        "\t\t\tposition = { x = 57 y = 8 }",
        '\t\t\tfont = "hoi_36header"',
        '\t\t\ttext = "RUS_europe_intervention_title"',
        "\t\t\tformat = left",
        f"\t\t\tmaxWidth = {WINDOW_WIDTH - 94}",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "\t}",
        "",
        "\tcontainerWindowType = {",
        '\t\tname = "RUS_europe_intervention_window"',
        f"\t\tposition = {{ x = 0 y = {MAP_WINDOW_Y} }}",
        f"\t\tsize = {{ width = {WINDOW_WIDTH} height = {WINDOW_HEIGHT} }}",
        "\t\tclipping = no",
        "\t\tmoveable = no",
        "",
        '\t\tbackground = { name = "Background" quadTextureSprite = "GFX_tiled_window2_1b_border" }',
        "",
        "\t\tcontainerWindowType = {",
        '\t\t\tname = "RUS_europe_intervention_map_mount"',
        f"\t\t\tposition = {{ x = {MAP_X - 7} y = {MAP_Y - 7} }}",
        f"\t\t\tsize = {{ width = {MAP_WIDTH + 14} height = {MAP_HEIGHT + 14} }}",
        "\t\t\tclipping = no",
        '\t\t\tbackground = { name = "Background" quadTextureSprite = "GFX_tiled_window2_1b_border" }',
        "\t\t}",
        "",
        "\t\ticonType = {",
        '\t\t\tname = "RUS_europe_intervention_map"',
        f"\t\t\tposition = {{ x = {MAP_X} y = {MAP_Y} }}",
        '\t\t\tspriteType = "GFX_RUS_europe_intervention_map_panel"',
        "\t\t\talwaystransparent = yes",
        "\t\t}",
    ]

    for hotspot_key, (left, top, _, _) in selector_boxes.items():
        hotspot = HOTSPOT_BY_KEY[hotspot_key]
        lines.extend([
            "",
            "\t\tbuttonType = {",
            f'\t\t\tname = "RUS_europe_intervention_{hotspot_key}_button"',
            f"\t\t\tposition = {{ x = {MAP_X + left} y = {MAP_Y + top} }}",
            f'\t\t\tquadTextureSprite = "GFX_RUS_europe_intervention_{hotspot_key}_button"',
            '\t\t\tclicksound = "click_default"',
            f'\t\t\tpdx_tooltip = "RUS_europe_intervention_{hotspot.selector_key}_tt"',
            "\t\t}",
            "",
            "\t\ticonType = {",
            f'\t\t\tname = "RUS_europe_intervention_{hotspot_key}_selected"',
            f"\t\t\tposition = {{ x = {MAP_X + left} y = {MAP_Y + top} }}",
            f'\t\t\tspriteType = "GFX_RUS_europe_intervention_{hotspot_key}_selected"',
            f'\t\t\tpdx_tooltip = "RUS_europe_intervention_{hotspot.selector_key}_tt"',
            "\t\t\talwaystransparent = yes",
            "\t\t}",
        ])

    lines.extend([
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_no_selection"',
        f"\t\t\tposition = {{ x = {MAP_X} y = {MAP_Y + MAP_HEIGHT + 18} }}",
        '\t\t\tfont = "hoi_18mbs"',
        '\t\t\ttext = "RUS_europe_intervention_no_selection"',
        "\t\t\tformat = left",
        "\t\t\tmaxWidth = 365",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
    ])
    for selector in SELECTORS:
        lines.extend([
            "",
            "\t\tinstantTextBoxType = {",
            f'\t\t\tname = "RUS_europe_intervention_{selector.key}_selected_name"',
            f"\t\t\tposition = {{ x = {MAP_X} y = {MAP_Y + MAP_HEIGHT + 18} }}",
            '\t\t\tfont = "hoi_18mbs"',
            f'\t\t\ttext = "RUS_europe_intervention_{selector.key}_selected_name"',
            "\t\t\tformat = left",
            "\t\t\tmaxWidth = 365",
            "\t\t\talwaystransparent = yes",
            "\t\t}",
        ])
    lines.extend([
        "",
        "\t\tbuttonType = {",
        '\t\t\tname = "RUS_europe_intervention_overview_button"',
        f"\t\t\tposition = {{ x = {WINDOW_WIDTH - 113} y = {MAP_Y + MAP_HEIGHT + 12} }}",
        '\t\t\tquadTextureSprite = "GFX_standard_button_88"',
        '\t\t\tbuttonText = "RUS_europe_intervention_overview_button"',
        '\t\t\tbuttonFont = "hoi_16mbs"',
        '\t\t\tpdx_tooltip = "RUS_europe_intervention_overview_tt"',
        "\t\t}",
        "",
        "\t\tinstantTextBoxType = {",
        '\t\t\tname = "RUS_europe_intervention_help"',
        f"\t\t\tposition = {{ x = {MAP_X} y = {MAP_Y + MAP_HEIGHT + 58} }}",
        '\t\t\tfont = "hoi_16mbs"',
        '\t\t\ttext = "RUS_europe_intervention_help"',
        "\t\t\tformat = left",
        f"\t\t\tmaxWidth = {WINDOW_WIDTH - 30}",
        "\t\t\talwaystransparent = yes",
        "\t\t}",
        "\t}",
        "",
        "\tcontainerWindowType = {",
        '\t\tname = "RUS_europe_intervention_portrait_window"',
        f"\t\tposition = {{ x = {PORTRAIT_X} y = {PORTRAIT_Y} }}",
        f"\t\tsize = {{ width = {PORTRAIT_WIDTH} height = {PORTRAIT_HEIGHT} }}",
        "\t\tclipping = yes",
        "",
        "\t\ticonType = {",
        '\t\t\tname = "RUS_europe_intervention_decision_portrait"',
        "\t\t\tposition = { x = 0 y = 0 }",
        '\t\t\tspriteType = "GFX_RUS_europe_intervention_decision_portrait"',
        '\t\t\tpdx_tooltip = "RUS_europe_intervention_dzerzhinsky_tt"',
        "\t\t}",
        "\t}",
        "}",
    ])
    category_block = lines[1:-1]
    lines = ["guiTypes = {", *category_block, "}"]
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
        "\t\tparent_window_name = power_balance_button",
        '\t\twindow_name = "RUS_europe_intervention_entry_window"',
        "\t\tai_enabled = { always = no }",
        "\t\ttriggers = {",
        "\t\t\tshow_power_balance_glow_visible = { always = no }",
        "\t\t\tpower_balance_percentage_visible = { always = no }",
        "\t\t\tpower_balance_levels_visible = { always = no }",
        "\t\t\tpower_balance_ICON_visible = { always = no }",
        "\t\t}",
        "\t\tvisible = {",
        *visible,
        "\t\t}",
        "\t}",
        "",
        "\tRUS_europe_intervention_header_gui = {",
        "\t\tcontext_type = player_context",
        "\t\tparent_window_name = powerbalanceview",
        '\t\twindow_name = "RUS_europe_intervention_header_window"',
        "\t\tai_enabled = { always = no }",
        "\t\tvisible = {",
        *visible,
        "\t\t}",
        "\t}",
        "",
        "\tRUS_europe_intervention_portrait_gui = {",
        "\t\tcontext_type = player_context",
        "\t\tparent_window_name = powerbalanceview",
        '\t\twindow_name = "RUS_europe_intervention_portrait_window"',
        "\t\tai_enabled = { always = no }",
        "\t\tvisible = {",
        *visible,
        "\t\t}",
        "\t}",
        "",
        "\tRUS_europe_intervention_gui = {",
        "\t\tcontext_type = player_context",
        "\t\tparent_window_name = powerbalanceview",
        '\t\twindow_name = "RUS_europe_intervention_window"',
        "\t\tai_enabled = { always = no }",
        "\t\tvisible = {",
        *visible,
        "\t\t}",
        "\t\ttriggers = {",
        "\t\t\tRUS_europe_intervention_no_selection_visible = { NOT = { has_country_flag = RUS_europe_intervention_filter_active } }",
        "\t\t\tRUS_europe_intervention_overview_button_click_enabled = { has_country_flag = RUS_europe_intervention_filter_active }",
    ]
    for hotspot in HOTSPOTS:
        selector = SELECTOR_BY_KEY[hotspot.selector_key]
        exists = "OR = { " + " ".join(
            f"{tag} = {{ exists = yes }}" for tag in selector.members
        ) + " }"
        lines.extend([
            f"\t\t\tRUS_europe_intervention_{hotspot.key}_button_visible = {{ {exists} }}",
            f"\t\t\tRUS_europe_intervention_{hotspot.key}_button_click_enabled = {{ {exists} }}",
            f"\t\t\tRUS_europe_intervention_{hotspot.key}_selected_visible = {{ has_country_flag = RUS_europe_intervention_selected_{selector.key} }}",
        ])
    for selector in SELECTORS:
        lines.append(
            f"\t\t\tRUS_europe_intervention_{selector.key}_selected_name_visible = {{ has_country_flag = RUS_europe_intervention_selected_{selector.key} }}"
        )
    lines.extend([
        "\t\t}",
        "\t\teffects = {",
        "\t\t\tRUS_europe_intervention_overview_button_click = { RUS_clear_europe_intervention_selection = yes }",
    ])
    for hotspot in HOTSPOTS:
        lines.extend([
            f"\t\t\tRUS_europe_intervention_{hotspot.key}_button_click = {{",
            "\t\t\t\tRUS_clear_europe_intervention_selection = yes",
            "\t\t\t\tset_country_flag = RUS_europe_intervention_filter_active",
            f"\t\t\t\tset_country_flag = RUS_europe_intervention_selected_{hotspot.selector_key}",
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
    selection_keys = {selector.key for selector in SELECTORS}
    selection_keys.update(tag for tag, _, _ in COUNTRIES)
    for key in sorted(selection_keys):
        effect_lines.append(f"\tclr_country_flag = RUS_europe_intervention_selected_{key}")
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
    for selector in SELECTORS:
        trigger_lines.extend([
            "\t\tAND = {",
            f"\t\t\thas_country_flag = RUS_europe_intervention_selected_{selector.key}",
            "\t\t\tFROM = {",
        ])
        if len(selector.members) == 1:
            trigger_lines.append(f"\t\t\t\ttag = {selector.members[0]}")
        else:
            trigger_lines.append("\t\t\t\tOR = {")
            trigger_lines.extend(
                f"\t\t\t\t\ttag = {tag}" for tag in selector.members
            )
            trigger_lines.append("\t\t\t\t}")
        trigger_lines.extend(["\t\t\t}", "\t\t}"])
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
        selector_keys = dict.fromkeys(SELECTOR_BY_MEMBER[tag].key for tag in tags)
        trigger_lines.extend(
            f"\t\thas_country_flag = RUS_europe_intervention_selected_{key}"
            for key in selector_keys
        )
        trigger_lines.extend(["\t}", "}", ""])
    (ROOT / "common" / "scripted_triggers" / "RUS_europe_intervention_triggers.txt").write_text(
        "\n".join(trigger_lines), encoding="utf-8"
    )


DZERZHINSKY_TOOLTIPS = {
    "simp_chinese": "§Y费利克斯·埃德蒙多维奇·捷尔任斯基§!\\n§Y生于：§! §L1877年9月11日；俄罗斯帝国属波兰、维尔诺省§!\\n§Y背景：§! §L费利克斯·埃德蒙多维奇·捷尔任斯基生于俄属波兰维尔诺省奥什米扬内县捷尔任诺沃庄园，一个波兰小地主贵族家庭。童年并未在庄园的安宁中度过太久——母亲早逝，父亲也在他十岁时离世，此后家道中落，少年时期的捷尔任斯基便已开始目睹阶级分化的残酷现实。1895年，他在维尔诺中学就读期间接触到马克思主义小组，次年便决心辍学，投身革命活动。1897年，他参与组织维尔诺社会民主工党，同年被捕，首次尝到牢狱滋味。\\n\\n1905年革命席卷波兰时，捷尔任斯基已是波兰王国和立陶宛社会民主工党的核心组织者之一。他在华沙和罗兹领导大规模罢工，参与武装斗争的准备，并负责地下刊物的编辑与分发。此后数年间，他辗转于维尔纽斯、华沙、基辅等地，先后五次被捕、三次流放，累计在监牢与流放地度过近十一年光阴——几乎占去他成年后将近一半的岁月。这段经历为他日后主持全俄肃反委员会的工作积累了深厚的地下斗争经验与心理承受力。\\n\\n1917年二月革命后，流放中的捷尔任斯基获释，随即奔赴彼得格勒。十月武装起义期间，他是军事革命委员会委员，负责斯莫尔尼宫的通讯与保卫工作，确保起义指挥中枢的畅通。起义成功后，根据列宁提议，他受命组建全俄肃反委员会，以应对白军与间谍活动的威胁。在内战最严峻的岁月里，他以极其严厉甚至冷酷的作风主持肃反工作——对叛徒与间谍从不留情，对组织内的动摇分子亦毫不姑息。白军和敌对势力闻之色变，党内同志则既敬畏又信赖，他因此赢得了“钢铁的费利克斯”的称号。\\n\\n然而，内战的走向最终未如革命者所愿。红色政权在多方围攻下倾覆，流亡成为唯一的出路。在撤离的混乱中，捷尔任斯基与中央失去联络。为掩人耳目，他销毁了一切能表明身份的文件，伪装成一名普通的波兰裔铁路工人，混入向西撤退的难民潮中——这一决定如此果断而彻底，以至于绝大多数同志都以为他已在白军的围剿中丧生——他的名字甚至一度出现在流亡者内部流传的牺牲者名单上。\\n\\n穿越战火与边境线的重重关卡后，捷尔任斯基辗转抵达华沙。在这座他年轻时便已熟悉的城市里，他以“海燕”为化名重新扎根。初期举步维艰——没有文件、没有联系人、没有资金，仅靠记忆中的几个旧地址和地下工作的本能，他开始逐一联络残存的波兰工党。凭借其惊人的记忆力与对地下工作的高度敏感，他很快在华沙、罗兹、克拉科夫等工业城市的工人社区中建立起可靠的情报节点。事到如今，这张以华沙为基地的网络已悄然延伸至东欧各国……§!",
    "english": "§YFelix Edmundovich Dzerzhinsky§!\\n§YBorn:§! §LSeptember 11th, 1877; Vilna Governorate, Russian Poland§!\\n§YBackground:§! §LA veteran Polish revolutionary and organiser of the All-Russian Extraordinary Commission, Dzerzhinsky vanished during the White victory and was presumed dead. Under the alias 'Petrel', he rebuilt an underground network from Warsaw that now reaches across Eastern Europe.§!",
    "russian": "§YФеликс Эдмундович Дзержинский§!\\n§YРодился:§! §L11 сентября 1877 года; Виленская губерния, Царство Польское, Российская империя§!\\n§YБиография:§! §LОпытный польский революционер и организатор Всероссийской чрезвычайной комиссии исчез во время победы белых и долго считался погибшим. Под псевдонимом «Буревестник» он восстановил в Варшаве подпольную сеть, которая теперь охватывает всю Восточную Европу.§!",
}


def build_localisation() -> None:
    languages = {
        "simp_chinese": {
            "title": "欧洲革命事务局",
            "entry": "传播革命",
            "entry_tt": "打开§Y欧洲革命事务局§!，选择需要处理的国家并直接执行相关决议。",
            "none": "§Y欧洲总览§!：显示当前全部可用的革命外交与干涉决议",
            "help": "点击国家领土选择目标；随后打开决议栏查看对应国家的事务。点击“总览”恢复全部决议。",
            "overview": "总览",
            "overview_tt": "取消国家筛选，恢复显示全部可用决议。",
            "selected": "§Y已选目标：§!",
            "selected_region": "§Y已选区域：§!",
            "tooltip": "点击该国领土，仅显示与该国对应的可用决议。",
            "group_names": {
                "NORDICS": "北欧",
                "CENTRAL_EUROPE": "中欧",
                "AUSTRIA_HUNGARY": "奥匈帝国",
                "ITALY": "意大利",
                "BALKANS": "巴尔干地区",
            },
            "group_tooltips": {
                "NORDICS": "点击该区域，显示冰岛、挪威、瑞典、芬兰和丹麦的相关决议。",
                "CENTRAL_EUROPE": "点击该区域，显示荷兰、比利时、德国和瑞士的相关决议。",
                "AUSTRIA_HUNGARY": "点击该区域，显示奥匈帝国各组成国的相关决议。",
                "ITALY": "点击该区域，显示意大利各政权的相关决议。",
                "BALKANS": "点击该区域，显示塞尔维亚、罗马尼亚、希腊、阿尔巴尼亚和保加利亚的相关决议。",
            },
        },
        "english": {
            "title": "Bureau of European Revolutionary Affairs",
            "entry": "Spread the Revolution",
            "entry_tt": "Open the §YBureau of European Revolutionary Affairs§!, select a country, and execute its matching decisions directly.",
            "none": "§YEuropean overview§!: show all currently available revolutionary and intervention decisions",
            "help": "Select a country, then open Decisions to see its matching actions. Overview restores the full list.",
            "overview": "Overview",
            "overview_tt": "Clear the country filter and show every available decision.",
            "selected": "§YSelected target:§!",
            "selected_region": "§YSelected region:§!",
            "tooltip": "Select this territory to show available decisions concerning the country.",
            "group_names": {
                "NORDICS": "Nordic Countries",
                "CENTRAL_EUROPE": "Central Europe",
                "AUSTRIA_HUNGARY": "Austria-Hungary",
                "ITALY": "Italy",
                "BALKANS": "The Balkans",
            },
            "group_tooltips": {
                "NORDICS": "Select this region to show decisions concerning Iceland, Norway, Sweden, Finland, and Denmark.",
                "CENTRAL_EUROPE": "Select this region to show decisions concerning the Netherlands, Belgium, Germany, and Switzerland.",
                "AUSTRIA_HUNGARY": "Select this region to show decisions concerning the constituent states of Austria-Hungary.",
                "ITALY": "Select this region to show decisions concerning the Italian states.",
                "BALKANS": "Select this region to show decisions concerning Serbia, Romania, Greece, Albania, and Bulgaria.",
            },
        },
        "russian": {
            "title": "Бюро европейских революционных дел",
            "entry": "Распространить революцию",
            "entry_tt": "Открыть §YБюро европейских революционных дел§!, выбрать страну и выполнить связанные с ней решения.",
            "none": "§YОбзор Европы§!: показать все доступные решения по революционной дипломатии и вмешательству",
            "help": "Выберите страну, затем откройте решения, чтобы увидеть соответствующие действия. «Обзор» вернёт полный список.",
            "overview": "Обзор",
            "overview_tt": "Снять фильтр страны и показать все доступные решения.",
            "selected": "§YВыбранная цель:§!",
            "selected_region": "§YВыбранный регион:§!",
            "tooltip": "Выбрать территорию и показать доступные решения по этой стране.",
            "group_names": {
                "NORDICS": "Северная Европа",
                "CENTRAL_EUROPE": "Центральная Европа",
                "AUSTRIA_HUNGARY": "Австро-Венгрия",
                "ITALY": "Италия",
                "BALKANS": "Балканы",
            },
            "group_tooltips": {
                "NORDICS": "Выбрать регион и показать решения по Исландии, Норвегии, Швеции, Финляндии и Дании.",
                "CENTRAL_EUROPE": "Выбрать регион и показать решения по Нидерландам, Бельгии, Германии и Швейцарии.",
                "AUSTRIA_HUNGARY": "Выбрать регион и показать решения по составным государствам Австро-Венгрии.",
                "ITALY": "Выбрать регион и показать решения по итальянским государствам.",
                "BALKANS": "Выбрать регион и показать решения по Сербии, Румынии, Греции, Албании и Болгарии.",
            },
        },
    }
    for language, loc in languages.items():
        lines = [
            f"l_{language}:",
            f' RUS_europe_intervention_title:0 "{loc["title"]}"',
            f' RUS_europe_intervention_entry_button:0 "{loc["entry"]}"',
            f' RUS_europe_intervention_entry_tt:0 "{loc["entry_tt"]}"',
            f' RUS_europe_intervention_dzerzhinsky_tt:0 "{DZERZHINSKY_TOOLTIPS[language]}"',
            ' RUS_europe_intervention_empty_tt:0 ""',
            f' RUS_europe_intervention_no_selection:0 "{loc["none"]}"',
            f' RUS_europe_intervention_help:0 "{loc["help"]}"',
            f' RUS_europe_intervention_overview_button:0 "{loc["overview"]}"',
            f' RUS_europe_intervention_overview_tt:0 "{loc["overview_tt"]}"',
        ]
        for selector in SELECTORS:
            if selector.key in loc["group_names"]:
                name = loc["group_names"][selector.key]
                lines.append(
                    f' RUS_europe_intervention_{selector.key}_selected_name:0 "{loc["selected_region"]} {name}"'
                )
                lines.append(
                    f' RUS_europe_intervention_{selector.key}_tt:0 "§Y{name}§!\\n{loc["group_tooltips"][selector.key]}"'
                )
            else:
                tag = selector.members[0]
                lines.append(
                    f' RUS_europe_intervention_{selector.key}_selected_name:0 "{loc["selected"]} [{tag}.GetNameWithFlag]"'
                )
                lines.append(
                    f' RUS_europe_intervention_{selector.key}_tt:0 "§Y[{tag}.GetName]§!\\n{loc["tooltip"]}"'
                )
        path = ROOT / "localisation" / language / f"RUS_europe_intervention_l_{language}.yml"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    build_category_icon()
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
