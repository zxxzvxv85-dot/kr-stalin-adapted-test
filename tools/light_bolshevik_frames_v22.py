from __future__ import annotations

from math import sqrt
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
KR_GOALS = WORKSHOP_ROOT / "1521695605/gfx/interface/goals"
OUTPUT_DIR = ROOT / "output/imagegen"

SOURCE_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_KR_texture_contrast_100px_v21"
DEST_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_KR_lit_frames_100px_v24"
PREVIEW_DARK = OUTPUT_DIR / "RUS_kamenev_bolshevik_KR_lit_frames_100px_dark_v24.png"
PREVIEW_WHITE = OUTPUT_DIR / "RUS_kamenev_bolshevik_KR_lit_frames_100px_white_v24.png"
COMPARISON = OUTPUT_DIR / "RUS_kamenev_bolshevik_v21_v24_KR_reference_compare.png"

TARGETS = [
    ("RUS_kamenev_bol_win_vst_majority", "一切权力归苏维埃", "RUS_union_of_peasants_and_workers.png"),
    ("RUS_kamenev_bol_restore_pravda", "《真理报》重返俄罗斯", "generic_seize_press.png"),
    ("RUS_kamenev_bol_undissolved_central_committee", "两张党证", "CHI_the_party_state.png"),
    ("RUS_kamenev_bol_register_returning_members", "开设党校", "ANQ_northern_school.png"),
    ("RUS_kamenev_bol_rebuild_factory_cells", "车间里的党小组", "generic_syndicalist_workers.png"),
    ("RUS_kamenev_bol_railway_telegraph_bureau", "铁路与电报联络局", "generic_seize_railway.png"),
    ("RUS_kamenev_bol_unify_planning_apparatus", "设立最高纲领派联络处", "generic_workers_democracy.png"),
    ("RUS_kamenev_bol_raise_red_flag", "高举红旗", "RUS_soldier_with_flag.png"),
]


def font(size: int) -> ImageFont.ImageFont:
    for path in (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf")):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def light_frame(icon: Image.Image) -> Image.Image:
    result = icon.convert("RGBA").copy()
    alpha = result.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("Icon has no visible alpha pixels")

    center_x = (bbox[0] + bbox[2] - 1) / 2
    center_y = (bbox[1] + bbox[3] - 1) / 2
    radius_x = max(1.0, (bbox[2] - bbox[0]) / 2)
    radius_y = max(1.0, (bbox[3] - bbox[1]) / 2)
    pixels = result.load()
    alpha_pixels = alpha.load()

    for y in range(result.height):
        for x in range(result.width):
            if alpha_pixels[x, y] == 0:
                continue

            norm_x = (x - center_x) / radius_x
            norm_y = (y - center_y) / radius_y
            radial = sqrt(norm_x * norm_x + norm_y * norm_y)
            frame_weight = smoothstep((radial - 0.52) / 0.34)
            if frame_weight <= 0:
                continue

            red, green, blue, pixel_alpha = pixels[x, y]
            chroma = max(red, green, blue) - min(red, green, blue)
            if red == max(red, green, blue) and chroma > 62:
                frame_weight *= 0.48

            luminance = red * 0.2126 + green * 0.7152 + blue * 0.0722
            direction = max(-1.0, min(1.0, (-norm_x - norm_y) / 1.45))
            directional_lift = 28.0 + 28.0 * max(0.0, direction) - 3.0 * max(0.0, -direction)
            target_luminance = 100.0 + (luminance - 100.0) * 1.15 + directional_lift
            target_luminance = luminance + (target_luminance - luminance) * frame_weight
            target_luminance = max(0.0, min(255.0, target_luminance))
            factor = target_luminance / max(luminance, 1.0)

            cool_highlight = max(0.0, direction) * frame_weight
            pixels[x, y] = (
                max(0, min(255, round(red * factor + 2.0 * cool_highlight))),
                max(0, min(255, round(green * factor + 6.0 * cool_highlight))),
                max(0, min(255, round(blue * factor + 10.0 * cool_highlight))),
                pixel_alpha,
            )

    return result


def padded_reference(filename: str) -> Image.Image:
    source = Image.open(KR_GOALS / filename).convert("RGBA")
    result = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    result.alpha_composite(source, ((100 - source.width) // 2, (100 - source.height) // 2))
    return result


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    before: list[Image.Image] = []
    after: list[Image.Image] = []
    references: list[Image.Image] = []

    for focus_id, _, reference_name in TARGETS:
        source = Image.open(SOURCE_DIR / f"{focus_id}.png").convert("RGBA")
        processed = light_frame(source)
        processed.save(DEST_DIR / f"{focus_id}.png")
        before.append(source)
        after.append(processed)
        references.append(padded_reference(reference_name))

    dark = Image.new("RGBA", (500, 300), (7, 20, 24, 255))
    white = Image.new("RGBA", dark.size, (242, 242, 238, 255))
    label_font = font(12)
    for index, (_, text, _) in enumerate(TARGETS):
        column = index % 4
        row = index // 4
        x = 10 + column * 120
        y = 10 + row * 140
        for canvas, text_color in ((dark, (235, 235, 225, 255)), (white, (18, 18, 18, 255))):
            canvas.alpha_composite(after[index], (x, y))
            draw = ImageDraw.Draw(canvas)
            draw.rectangle((x - 1, y - 1, x + 100, y + 100), outline=(150, 155, 150, 255))
            box = draw.textbbox((0, 0), text, font=label_font)
            draw.text((x + 50 - (box[2] - box[0]) // 2, y + 106), text, font=label_font, fill=text_color)
    dark.convert("RGB").save(PREVIEW_DARK)
    white.convert("RGB").save(PREVIEW_WHITE)

    comparison = Image.new("RGBA", (900, 390), (7, 20, 24, 255))
    draw = ImageDraw.Draw(comparison)
    row_font = font(14)
    row_titles = ("V21 边框偏暗", "V24 校准金属边框", "官方 KR 参考")
    for row, (title, icons) in enumerate(zip(row_titles, (before, after, references))):
        y = 10 + row * 125
        draw.text((10, y + 40), title, font=row_font, fill=(235, 235, 225, 255))
        for column, icon in enumerate(icons):
            comparison.alpha_composite(icon, (125 + column * 95, y))
    comparison.convert("RGB").save(COMPARISON)

    print(f"lit icons: {DEST_DIR}")
    print(f"dark preview: {PREVIEW_DARK}")
    print(f"white preview: {PREVIEW_WHITE}")
    print(f"comparison: {COMPARISON}")


if __name__ == "__main__":
    main()
