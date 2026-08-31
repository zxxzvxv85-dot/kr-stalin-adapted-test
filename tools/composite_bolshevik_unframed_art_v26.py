from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
KR_GOALS = WORKSHOP_ROOT / "1521695605/gfx/interface/goals"
TMP_DIR = ROOT / "tmp/imagegen"
OUTPUT_DIR = ROOT / "output/imagegen"

SOURCE = TMP_DIR / "RUS_kamenev_bolshevik_low_resolution_repaint_transparent_v26.png"
FRAME = OUTPUT_DIR / "RUS_socialist_shared_frame_extracted_from_KR.png"
DEST_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_fixed_KR_frame_100px_v26"
PREVIEW_DARK = OUTPUT_DIR / "RUS_kamenev_bolshevik_fixed_KR_frame_100px_dark_v26.png"
PREVIEW_WHITE = OUTPUT_DIR / "RUS_kamenev_bolshevik_fixed_KR_frame_100px_white_v26.png"
COMPARISON = OUTPUT_DIR / "RUS_kamenev_bolshevik_fixed_KR_frame_vs_official_v26.png"

X_BOUNDS = (70, 457, 831, 1205, 1602)
Y_BOUNDS = (25, 465, 900)
ART_SIZE = 78

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


def extract_art(region: Image.Image) -> Image.Image:
    bbox = region.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("Grid region contains no visible artwork")
    art = region.crop(bbox)

    # The source is deliberately simplified; this final low-pass prevents the
    # 300px plate from reintroducing crisp microdetail during reduction.
    art = art.filter(ImageFilter.GaussianBlur(1.0))
    art = art.resize((ART_SIZE, ART_SIZE), Image.Resampling.BICUBIC)
    return art


def compose_icon(art: Image.Image, frame: Image.Image) -> Image.Image:
    icon = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    icon.alpha_composite(art, ((100 - ART_SIZE) // 2, (100 - ART_SIZE) // 2))
    icon.alpha_composite(frame, (0, 0))
    return icon


def padded_reference(filename: str) -> Image.Image:
    source = Image.open(KR_GOALS / filename).convert("RGBA")
    result = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    result.alpha_composite(source, ((100 - source.width) // 2, (100 - source.height) // 2))
    return result


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(SOURCE).convert("RGBA")
    frame = Image.open(FRAME).convert("RGBA")
    results: list[Image.Image] = []
    references: list[Image.Image] = []

    for index, (focus_id, _, reference_name) in enumerate(TARGETS):
        row = index // 4
        column = index % 4
        region = sheet.crop(
            (
                X_BOUNDS[column],
                Y_BOUNDS[row],
                X_BOUNDS[column + 1],
                Y_BOUNDS[row + 1],
            )
        )
        art = extract_art(region)
        icon = compose_icon(art, frame)
        icon.save(DEST_DIR / f"{focus_id}.png")
        results.append(icon)
        references.append(padded_reference(reference_name))
        print(f"{focus_id}: final_alpha_bbox={icon.getchannel('A').getbbox()}")

    dark = Image.new("RGBA", (500, 300), (7, 20, 24, 255))
    white = Image.new("RGBA", dark.size, (242, 242, 238, 255))
    label_font = font(12)
    for index, (_, text, _) in enumerate(TARGETS):
        column = index % 4
        row = index // 4
        x = 10 + column * 120
        y = 10 + row * 140
        for canvas, text_color in ((dark, (235, 235, 225, 255)), (white, (18, 18, 18, 255))):
            canvas.alpha_composite(results[index], (x, y))
            draw = ImageDraw.Draw(canvas)
            draw.rectangle((x - 1, y - 1, x + 100, y + 100), outline=(150, 155, 150, 255))
            box = draw.textbbox((0, 0), text, font=label_font)
            draw.text((x + 50 - (box[2] - box[0]) // 2, y + 106), text, font=label_font, fill=text_color)
    dark.convert("RGB").save(PREVIEW_DARK)
    white.convert("RGB").save(PREVIEW_WHITE)

    comparison = Image.new("RGBA", (900, 265), (7, 20, 24, 255))
    draw = ImageDraw.Draw(comparison)
    row_font = font(14)
    for row, (title, icons) in enumerate((("V26 固定 KR 框", results), ("官方 KR 参考", references))):
        y = 10 + row * 125
        draw.text((10, y + 40), title, font=row_font, fill=(235, 235, 225, 255))
        for column, icon in enumerate(icons):
            comparison.alpha_composite(icon, (125 + column * 95, y))
    comparison.convert("RGB").save(COMPARISON)

    print(f"icons: {DEST_DIR}")
    print(f"dark preview: {PREVIEW_DARK}")
    print(f"white preview: {PREVIEW_WHITE}")
    print(f"comparison: {COMPARISON}")


if __name__ == "__main__":
    main()
