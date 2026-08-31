from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
KR_GOALS = WORKSHOP_ROOT / "1521695605/gfx/interface/goals"
OUTPUT_DIR = ROOT / "output/imagegen"

SOURCE = OUTPUT_DIR / "RUS_kamenev_bolshevik_web_source_1669x942_v28.png"
DEST_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_web_final_100px_v28"
PREVIEW_DARK = OUTPUT_DIR / "RUS_kamenev_bolshevik_web_final_dark_v28.png"
PREVIEW_WHITE = OUTPUT_DIR / "RUS_kamenev_bolshevik_web_final_white_v28.png"
COMPARISON = OUTPUT_DIR / "RUS_kamenev_bolshevik_web_final_vs_current_vs_official_v28.png"

CURRENT_DIR = ROOT / "gfx/interface/goals/RUS_kamenev_politics"
ROUGH_RADIUS = 88
TARGET_CONTENT_SIZE = 88
RESAMPLING = Image.Resampling.BICUBIC
SHARPEN_RADIUS = 0.5
SHARPEN_PERCENT = 0
SHARPEN_THRESHOLD = 2
VERSION_LABEL = "网页版后期 V28"

TARGETS = [
    ("RUS_kamenev_bol_register_returning_members", "一切权力归苏维埃", (254, 248), "RUS_union_of_peasants_and_workers.png"),
    ("RUS_kamenev_bol_restore_pravda", "《真理报》重返俄罗斯", (638, 248), "generic_seize_press.png"),
    ("RUS_kamenev_bol_restore_central_bureau", "恢复中央局", (1013, 248), "CHI_the_party_state.png"),
    ("RUS_kamenev_bol_unify_planning_apparatus", "开设党校", (1407, 248), "ANQ_northern_school.png"),
    ("RUS_kamenev_bol_rebuild_factory_cells", "车间里的党小组", (254, 678), "generic_syndicalist_workers.png"),
    ("RUS_kamenev_bol_railway_telegraph_bureau", "铁路与电报联络局", (638, 678), "generic_seize_railway.png"),
    ("RUS_kamenev_bol_win_vst_majority", "最高纲领派联络处", (1013, 678), "generic_workers_democracy.png"),
    ("RUS_kamenev_bol_undissolved_central_committee", "高举红旗", (1407, 678), "RUS_soldier_with_flag.png"),
]


def font(size: int) -> ImageFont.ImageFont:
    for path in (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf")):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def chroma_key(cell: Image.Image) -> Image.Image:
    source = cell.convert("RGB")
    result = Image.new("RGBA", source.size, (0, 0, 0, 0))
    output: list[tuple[int, int, int, int]] = []

    for red, green, blue in source.get_flattened_data():
        green_excess = green - max(red, blue)
        if green >= 135 and green_excess >= 100:
            alpha = 0
        elif green >= 90 and green_excess >= 25:
            alpha = round(255 * (100 - green_excess) / 75)
        else:
            alpha = 255

        alpha = max(0, min(255, alpha))
        if alpha < 20:
            alpha = 0

        if alpha:
            spill = max(0, green - max(red, blue) - 4)
            edge_strength = 0.9 + 0.1 * (1 - alpha / 255)
            green = max(0, round(green - spill * edge_strength))
        output.append((red, green, blue, alpha))

    result.putdata(output)
    return result


def extract_icon(sheet: Image.Image, center: tuple[int, int]) -> Image.Image:
    center_x, center_y = center
    cell = sheet.crop(
        (
            center_x - ROUGH_RADIUS,
            center_y - ROUGH_RADIUS,
            center_x + ROUGH_RADIUS,
            center_y + ROUGH_RADIUS,
        )
    )
    keyed = chroma_key(cell)
    bbox = keyed.getchannel("A").point(lambda value: 255 if value >= 20 else 0).getbbox()
    if bbox is None:
        raise ValueError(f"No icon found near {center}")
    return keyed.crop(bbox)


def tone_icon(icon: Image.Image) -> Image.Image:
    source = icon.convert("RGBA")
    width, height = source.size
    corrected: list[tuple[int, int, int, int]] = []

    for index, (red, green, blue, alpha) in enumerate(source.get_flattened_data()):
        if alpha == 0:
            corrected.append((0, 0, 0, 0))
            continue

        x = index % width
        y = index // width
        luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        contrast_luminance = (luminance - 92) * 1.08 + 92
        direction = 1.075 - 0.055 * (x / max(1, width - 1)) - 0.055 * (y / max(1, height - 1))
        target_luminance = max(0, min(255, contrast_luminance * 1.055 * direction))
        ratio = target_luminance / max(1, luminance)
        ratio = max(0.78, min(1.24, ratio))

        red = max(0, min(255, round(red * ratio)))
        green = max(0, min(255, round(green * ratio)))
        blue = max(0, min(255, round(blue * ratio)))

        neutral = round(0.2126 * red + 0.7152 * green + 0.0722 * blue)
        red = round(red * 0.96 + neutral * 0.04)
        green = round(green * 0.96 + neutral * 0.04)
        blue = round(blue * 0.96 + neutral * 0.04)
        corrected.append((red, green, blue, alpha))

    source.putdata(corrected)
    return source


def fit_to_canvas(icon: Image.Image) -> Image.Image:
    scale = min(TARGET_CONTENT_SIZE / icon.width, TARGET_CONTENT_SIZE / icon.height)
    fitted = icon.resize(
        (max(1, round(icon.width * scale)), max(1, round(icon.height * scale))),
        RESAMPLING,
    )
    if SHARPEN_PERCENT > 0:
        alpha = fitted.getchannel("A")
        sharpened = fitted.convert("RGB").filter(
            ImageFilter.UnsharpMask(
                radius=SHARPEN_RADIUS,
                percent=SHARPEN_PERCENT,
                threshold=SHARPEN_THRESHOLD,
            )
        )
        fitted = Image.merge("RGBA", (*sharpened.split(), alpha))
    result = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    result.alpha_composite(fitted, ((100 - fitted.width) // 2, (100 - fitted.height) // 2))
    return result


def padded_reference(path: Path) -> Image.Image:
    source = Image.open(path).convert("RGBA")
    if source.width > 100 or source.height > 100:
        scale = min(100 / source.width, 100 / source.height)
        source = source.resize(
            (round(source.width * scale), round(source.height * scale)),
            Image.Resampling.LANCZOS,
        )
    result = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    result.alpha_composite(source, ((100 - source.width) // 2, (100 - source.height) // 2))
    return result


def luma_summary(icon: Image.Image) -> tuple[float, int, int, int]:
    values: list[int] = []
    for red, green, blue, alpha in icon.convert("RGBA").get_flattened_data():
        if alpha >= 128:
            values.append(round(0.2126 * red + 0.7152 * green + 0.0722 * blue))
    values.sort()
    if not values:
        return (0.0, 0, 0, 0)
    return (
        sum(values) / len(values),
        values[len(values) // 10],
        values[len(values) // 2],
        values[min(len(values) - 1, len(values) * 9 // 10)],
    )


def make_preview(icons: list[Image.Image], background: tuple[int, int, int, int], path: Path) -> None:
    canvas = Image.new("RGBA", (500, 280), background)
    draw = ImageDraw.Draw(canvas)
    label_font = font(12)
    text_color = (235, 235, 225, 255) if sum(background[:3]) < 300 else (18, 18, 18, 255)

    for index, icon in enumerate(icons):
        column = index % 4
        row = index // 4
        x = 10 + column * 122
        y = 10 + row * 135
        canvas.alpha_composite(icon, (x, y))
        label = TARGETS[index][1]
        text_box = draw.textbbox((0, 0), label, font=label_font)
        text_width = text_box[2] - text_box[0]
        draw.text((x + 50 - text_width // 2, y + 104), label, font=label_font, fill=text_color)
    canvas.convert("RGB").save(path)


def make_comparison(finals: list[Image.Image]) -> None:
    current = [padded_reference(CURRENT_DIR / f"{focus_id}.png") for focus_id, *_ in TARGETS]
    official = [padded_reference(KR_GOALS / reference) for *_, reference in TARGETS]
    canvas = Image.new("RGBA", (890, 350), (7, 20, 24, 255))
    draw = ImageDraw.Draw(canvas)
    title_font = font(13)
    rows = [("当前测试版", current), (VERSION_LABEL, finals), ("官方 KR 参考", official)]

    for row, (title, icons) in enumerate(rows):
        y = 10 + row * 110
        draw.text((8, y + 40), title, font=title_font, fill=(235, 235, 225, 255))
        for column, icon in enumerate(icons):
            canvas.alpha_composite(icon, (90 + column * 100, y))
    canvas.convert("RGB").save(COMPARISON)


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(SOURCE).convert("RGB")
    finals: list[Image.Image] = []

    for focus_id, _, center, reference_name in TARGETS:
        extracted = extract_icon(sheet, center)
        toned = tone_icon(extracted)
        final = fit_to_canvas(toned)
        final.save(DEST_DIR / f"{focus_id}.png")
        finals.append(final)

        official = padded_reference(KR_GOALS / reference_name)
        source_stats = luma_summary(extracted)
        final_stats = luma_summary(final)
        official_stats = luma_summary(official)
        print(
            f"{focus_id}: source={extracted.size} final_bbox={final.getchannel('A').getbbox()} "
            f"luma source/final/official={source_stats}/{final_stats}/{official_stats}"
        )

    make_preview(finals, (7, 20, 24, 255), PREVIEW_DARK)
    make_preview(finals, (242, 242, 238, 255), PREVIEW_WHITE)
    make_comparison(finals)
    print(f"icons: {DEST_DIR}")
    print(f"dark preview: {PREVIEW_DARK}")
    print(f"white preview: {PREVIEW_WHITE}")
    print(f"comparison: {COMPARISON}")


if __name__ == "__main__":
    main()
