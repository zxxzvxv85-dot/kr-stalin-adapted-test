from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / "tmp/imagegen"
OUTPUT_DIR = ROOT / "output/imagegen"

SOURCE = TMP_DIR / "RUS_kamenev_bolshevik_chroma_grid_transparent_v18.png"
DEST_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_chroma_grid_100px_v18"
CONTACT_DARK = OUTPUT_DIR / "RUS_kamenev_bolshevik_chroma_grid_100px_dark_v18.png"
CONTACT_WHITE = OUTPUT_DIR / "RUS_kamenev_bolshevik_chroma_grid_100px_white_v18.png"

# Non-overlapping regions around the generated 4x2 grid. The API returned the
# input dimensions (1672x941), so these coordinates are in that native output.
X_BOUNDS = (80, 457, 831, 1205, 1592)
Y_BOUNDS = (35, 460, 900)

TARGETS = [
    ("RUS_kamenev_bol_win_vst_majority", "一切权力归苏维埃"),
    ("RUS_kamenev_bol_restore_pravda", "《真理报》重返俄罗斯"),
    ("RUS_kamenev_bol_undissolved_central_committee", "两张党证"),
    ("RUS_kamenev_bol_register_returning_members", "开设党校"),
    ("RUS_kamenev_bol_rebuild_factory_cells", "车间里的党小组"),
    ("RUS_kamenev_bol_railway_telegraph_bureau", "铁路与电报联络局"),
    ("RUS_kamenev_bol_unify_planning_apparatus", "设立最高纲领派联络处"),
    ("RUS_kamenev_bol_raise_red_flag", "高举红旗"),
]


def font(size: int) -> ImageFont.ImageFont:
    for path in (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf")):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def fit_complete_badge(region: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    alpha = region.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("Grid region contains no non-transparent badge pixels")

    badge = region.crop(bbox)
    scale = min(96 / badge.width, 96 / badge.height)
    target_size = (
        max(1, round(badge.width * scale)),
        max(1, round(badge.height * scale)),
    )
    badge = badge.resize(target_size, Image.Resampling.LANCZOS)

    result = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    result.alpha_composite(badge, ((100 - badge.width) // 2, (100 - badge.height) // 2))
    return result, bbox


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(SOURCE).convert("RGBA")

    results: list[tuple[str, Image.Image]] = []
    for index, (focus_id, label) in enumerate(TARGETS):
        row = index // 4
        column = index % 4
        region_box = (
            X_BOUNDS[column],
            Y_BOUNDS[row],
            X_BOUNDS[column + 1],
            Y_BOUNDS[row + 1],
        )
        region = sheet.crop(region_box)
        icon, local_bbox = fit_complete_badge(region)
        icon_path = DEST_DIR / f"{focus_id}.png"
        icon.save(icon_path)
        results.append((label, icon))

        global_bbox = (
            region_box[0] + local_bbox[0],
            region_box[1] + local_bbox[1],
            region_box[0] + local_bbox[2],
            region_box[1] + local_bbox[3],
        )
        alpha_bbox = icon.getchannel("A").getbbox()
        print(f"{focus_id}: source_bbox={global_bbox}, final_alpha_bbox={alpha_bbox}")

    dark = Image.new("RGBA", (500, 300), (7, 20, 24, 255))
    white = Image.new("RGBA", dark.size, (242, 242, 238, 255))
    label_font = font(12)
    for index, (label, icon) in enumerate(results):
        column = index % 4
        row = index // 4
        x = 10 + column * 120
        y = 10 + row * 140
        for canvas, text_color in ((dark, (235, 235, 225, 255)), (white, (18, 18, 18, 255))):
            canvas.alpha_composite(icon, (x, y))
            draw = ImageDraw.Draw(canvas)
            draw.rectangle((x - 1, y - 1, x + 100, y + 100), outline=(150, 155, 150, 255), width=1)
            text_box = draw.textbbox((0, 0), label, font=label_font)
            text_width = text_box[2] - text_box[0]
            draw.text((x + 50 - text_width // 2, y + 106), label, font=label_font, fill=text_color)

    dark.convert("RGB").save(CONTACT_DARK)
    white.convert("RGB").save(CONTACT_WHITE)
    print(f"icons: {DEST_DIR}")
    print(f"dark preview: {CONTACT_DARK}")
    print(f"white preview: {CONTACT_WHITE}")


if __name__ == "__main__":
    main()
