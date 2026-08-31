from __future__ import annotations

import hashlib
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
KR_GOALS = WORKSHOP_ROOT / "1521695605/gfx/interface/goals"
OUTPUT_DIR = ROOT / "output/imagegen"

SOURCE_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_chroma_grid_100px_v18"
DEST_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_KR_texture_contrast_100px_v21"
PREVIEW_DARK = OUTPUT_DIR / "RUS_kamenev_bolshevik_KR_texture_contrast_100px_dark_v21.png"
PREVIEW_WHITE = OUTPUT_DIR / "RUS_kamenev_bolshevik_KR_texture_contrast_100px_white_v21.png"
COMPARISON = OUTPUT_DIR / "RUS_kamenev_bolshevik_v18_v21_KR_reference_compare.png"

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


def deterministic_rng(name: str) -> random.Random:
    digest = hashlib.sha256(name.encode("ascii")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def kr_texture_grade(icon: Image.Image, name: str) -> Image.Image:
    rng = deterministic_rng(name)

    # A controlled down/up resample breaks unnaturally perfect digital edges
    # while retaining the native-size silhouette and alpha geometry.
    softened = icon.convert("RGBA").resize((90, 90), Image.Resampling.LANCZOS)
    softened = softened.resize((100, 100), Image.Resampling.BICUBIC)
    alpha = softened.getchannel("A")
    rgb = softened.convert("RGB")

    rgb = ImageEnhance.Color(rgb).enhance(0.80)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.00)
    rgb = ImageEnhance.Sharpness(rgb).enhance(0.46)
    rgb = Image.blend(rgb, Image.new("RGB", rgb.size, (88, 76, 61)), 0.045)
    rgb = ImageEnhance.Brightness(rgb).enhance(1.04)

    # Low-frequency patina produces irregular paint and oxidised metal rather
    # than uniform noise. Fine grain is kept below thumbnail-detail strength.
    patina_small = Image.new("L", (12, 12))
    patina_small.putdata([rng.randint(105, 150) for _ in range(12 * 12)])
    patina = patina_small.resize((100, 100), Image.Resampling.BICUBIC)

    pixels = rgb.load()
    patina_pixels = patina.load()
    alpha_pixels = alpha.load()
    for y in range(100):
        for x in range(100):
            if alpha_pixels[x, y] == 0:
                continue
            red, green, blue = pixels[x, y]
            low_frequency = (patina_pixels[x, y] - 127.5) / 127.5
            fine_grain = rng.gauss(0.0, 2.0)
            factor = 1.0 + low_frequency * 0.07
            red = max(0, min(255, red * factor + fine_grain))
            green = max(0, min(255, green * factor + fine_grain * 0.85))
            blue = max(0, min(255, blue * factor + fine_grain * 0.65))

            luminance = red * 0.2126 + green * 0.7152 + blue * 0.0722
            target_luminance = 100 + (luminance - 100) * 1.22
            if luminance > 150:
                target_luminance += 3
            target_luminance = max(0, min(255, target_luminance))
            luminance_factor = target_luminance / max(luminance, 1)
            pixels[x, y] = (
                max(0, min(255, round(red * luminance_factor))),
                max(0, min(255, round(green * luminance_factor))),
                max(0, min(255, round(blue * luminance_factor))),
            )

    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


def place_icon(canvas: Image.Image, icon: Image.Image, x: int, y: int) -> None:
    canvas.alpha_composite(icon, (x, y))


def label(canvas: Image.Image, text: str, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(canvas)
    label_font = font(12)
    box = draw.textbbox((0, 0), text, font=label_font)
    draw.text((x + 50 - (box[2] - box[0]) // 2, y), text, font=label_font, fill=color)


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    originals: list[Image.Image] = []
    graded: list[Image.Image] = []
    references: list[Image.Image] = []

    for focus_id, _, reference_name in TARGETS:
        original = Image.open(SOURCE_DIR / f"{focus_id}.png").convert("RGBA")
        processed = kr_texture_grade(original, focus_id)
        processed.save(DEST_DIR / f"{focus_id}.png")

        reference_raw = Image.open(KR_GOALS / reference_name).convert("RGBA")
        reference = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        reference.alpha_composite(
            reference_raw,
            ((100 - reference_raw.width) // 2, (100 - reference_raw.height) // 2),
        )
        originals.append(original)
        graded.append(processed)
        references.append(reference)

    dark = Image.new("RGBA", (500, 300), (7, 20, 24, 255))
    white = Image.new("RGBA", dark.size, (242, 242, 238, 255))
    for index, (_, text, _) in enumerate(TARGETS):
        column = index % 4
        row = index // 4
        x = 10 + column * 120
        y = 10 + row * 140
        for canvas, color in ((dark, (235, 235, 225, 255)), (white, (18, 18, 18, 255))):
            place_icon(canvas, graded[index], x, y)
            ImageDraw.Draw(canvas).rectangle((x - 1, y - 1, x + 100, y + 100), outline=(150, 155, 150, 255))
            label(canvas, text, x, y + 106, color)
    dark.convert("RGB").save(PREVIEW_DARK)
    white.convert("RGB").save(PREVIEW_WHITE)

    comparison = Image.new("RGBA", (900, 390), (7, 20, 24, 255))
    draw = ImageDraw.Draw(comparison)
    row_font = font(14)
    row_titles = ("V18 清晰原图", "V21 KR 明暗分层", "官方 KR 参考")
    rows = (originals, graded, references)
    for row, (title, icons) in enumerate(zip(row_titles, rows)):
        y = 10 + row * 125
        draw.text((10, y + 40), title, font=row_font, fill=(235, 235, 225, 255))
        for column, icon in enumerate(icons):
            place_icon(comparison, icon, 125 + column * 95, y)
    comparison.convert("RGB").save(COMPARISON)

    print(f"graded icons: {DEST_DIR}")
    print(f"dark preview: {PREVIEW_DARK}")
    print(f"white preview: {PREVIEW_WHITE}")
    print(f"comparison: {COMPARISON}")


if __name__ == "__main__":
    main()
