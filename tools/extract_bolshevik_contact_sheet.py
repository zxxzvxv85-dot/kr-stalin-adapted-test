from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/imagegen/RUS_kamenev_bolshevik_eight_icon_contact_sheet_v1.png"
OUTPUT_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_eight_icon_contact_sheet_v1_crops"
PREVIEW = ROOT / "output/imagegen/RUS_kamenev_bolshevik_eight_icon_contact_sheet_v1_100px_preview.png"

ICONS = [
    ("RUS_kamenev_bol_register_returning_members", (192, 272)),
    ("RUS_kamenev_bol_restore_pravda", (576, 274)),
    ("RUS_kamenev_bol_restore_central_bureau", (960, 274)),
    ("RUS_kamenev_bol_unify_planning_apparatus", (1344, 270)),
    ("RUS_kamenev_bol_rebuild_factory_cells", (192, 735)),
    ("RUS_kamenev_bol_railway_telegraph_bureau", (576, 735)),
    ("RUS_kamenev_bol_win_vst_majority", (960, 725)),
    ("RUS_kamenev_bol_undissolved_central_committee", (1344, 725)),
]


def crop_with_padding(image: Image.Image, center: tuple[int, int], size: int) -> Image.Image:
    half = size // 2
    left, top = center[0] - half, center[1] - half
    result = Image.new("RGBA", (size, size), (20, 17, 14, 255))
    source_box = (
        max(0, left),
        max(0, top),
        min(image.width, left + size),
        min(image.height, top + size),
    )
    fragment = image.crop(source_box)
    result.alpha_composite(fragment, (source_box[0] - left, source_box[1] - top))
    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGBA")
    preview = Image.new("RGBA", (440, 220), (18, 18, 17, 255))
    draw = ImageDraw.Draw(preview)

    for index, (name, center) in enumerate(ICONS):
        crop = crop_with_padding(source, center, 430)
        crop.save(OUTPUT_DIR / f"{name}_artwork_v1.png")
        thumb = crop.resize((100, 100), Image.Resampling.LANCZOS)
        x = 10 + (index % 4) * 110
        y = 5 + (index // 4) * 110
        preview.alpha_composite(thumb, (x, y))
        draw.rectangle((x, y, x + 99, y + 99), outline=(91, 82, 67, 255), width=1)

    preview.save(PREVIEW)


if __name__ == "__main__":
    main()
