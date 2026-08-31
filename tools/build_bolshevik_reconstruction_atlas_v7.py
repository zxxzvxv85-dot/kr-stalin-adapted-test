from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_eight_complete_icons_v6"
TMP_DIR = ROOT / "tmp/imagegen"
OUTPUT_DIR = ROOT / "output/imagegen"

GUIDE = TMP_DIR / "RUS_kamenev_bolshevik_reconstruction_atlas_guide_v7.png"
MASK = TMP_DIR / "RUS_kamenev_bolshevik_reconstruction_atlas_mask_v7.png"
PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_reconstruction_atlas_guide_v7.png"

CANVAS_SIZE = (1254, 1254)
ICON_SIZE = 100
SLOTS = [
    (127, 427),
    (427, 427),
    (727, 427),
    (1027, 427),
    (127, 727),
    (427, 727),
    (727, 727),
    (1027, 727),
]

ICONS = [
    ("01  ALL POWER TO THE SOVIETS", "RUS_kamenev_bol_register_returning_members.png"),
    ("02  PRAVDA RETURNS", "RUS_kamenev_bol_restore_pravda.png"),
    ("03  TWO PARTY CARDS", "RUS_kamenev_bol_restore_central_bureau.png"),
    ("04  OPEN PARTY SCHOOLS", "RUS_kamenev_bol_unify_planning_apparatus.png"),
    ("05  FACTORY PARTY CELLS", "RUS_kamenev_bol_rebuild_factory_cells.png"),
    ("06  RAILWAY AND TELEGRAPH", "RUS_kamenev_bol_railway_telegraph_bureau.png"),
    ("07  MAXIMALIST LIAISON", "RUS_kamenev_bol_win_vst_majority.png"),
    ("08  RAISE THE RED FLAG", "RUS_kamenev_bol_undissolved_central_committee.png"),
]


def load_font(size: int) -> ImageFont.ImageFont:
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default()


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("RGBA", CANVAS_SIZE, (9, 15, 17, 255))
    draw = ImageDraw.Draw(canvas)
    font_title = load_font(22)
    font_label = load_font(13)

    draw.rectangle((0, 0, CANVAS_SIZE[0] - 1, 54), fill=(29, 30, 29, 255))
    draw.line((0, 54, CANVAS_SIZE[0], 54), fill=(135, 137, 130, 255), width=2)
    draw.text((24, 15), "BOLSHEVIK FOCUS ICON RECONSTRUCTION - EXACT 100 PX CELLS", font=font_title, fill=(230, 230, 220, 255))

    for (label, filename), (left, top) in zip(ICONS, SLOTS, strict=True):
        source = Image.open(SOURCE_DIR / filename).convert("RGBA")
        if source.size != (ICON_SIZE, ICON_SIZE):
            raise RuntimeError(f"Source is not 100x100: {filename} is {source.size}")

        # Paste without resizing: the source begins the reconstruction at its
        # exact current pixel size inside the hard cell boundary.
        canvas.alpha_composite(source, (left, top))

        draw.rectangle(
            (left - 3, top - 3, left + ICON_SIZE + 2, top + ICON_SIZE + 2),
            outline=(229, 229, 217, 255),
            width=2,
        )
        draw.rectangle(
            (left - 6, top - 6, left + ICON_SIZE + 5, top + ICON_SIZE + 5),
            outline=(92, 96, 92, 255),
            width=1,
        )
        draw.text((left - 6, top - 27), label, font=font_label, fill=(213, 213, 204, 255))

        # Visible coordinate ticks reinforce that no generated pixel may
        # cross the 100px boundary.
        for offset in (0, ICON_SIZE):
            draw.line((left + offset, top - 10, left + offset, top - 4), fill=(208, 82, 72, 255), width=1)
            draw.line((left + offset, top + ICON_SIZE + 3, left + offset, top + ICON_SIZE + 9), fill=(208, 82, 72, 255), width=1)
            draw.line((left - 10, top + offset, left - 4, top + offset), fill=(208, 82, 72, 255), width=1)
            draw.line((left + ICON_SIZE + 3, top + offset, left + ICON_SIZE + 9, top + offset), fill=(208, 82, 72, 255), width=1)

    canvas.save(GUIDE)
    canvas.save(PREVIEW)

    mask = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
    mask_draw = ImageDraw.Draw(mask)
    for left, top in SLOTS:
        mask_draw.rectangle(
            (left, top, left + ICON_SIZE - 1, top + ICON_SIZE - 1),
            fill=(255, 255, 255, 0),
        )
    mask.save(MASK)


if __name__ == "__main__":
    main()
