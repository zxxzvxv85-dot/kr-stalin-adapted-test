from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
KR_GOALS = WORKSHOP_ROOT / "1521695605/gfx/interface/goals"
TMP_DIR = ROOT / "tmp/imagegen"
OUTPUT_DIR = ROOT / "output/imagegen"

CANVAS_SIZE = (1672, 941)
CHROMA = (0, 255, 0, 255)
CELL_SIZE = 100
EDIT_SIZE = 220

ANCHOR_CANVAS = TMP_DIR / "RUS_kamenev_bolshevik_chroma_grid_1672x941_v18.png"
EDIT_MASK = TMP_DIR / "RUS_kamenev_bolshevik_chroma_grid_mask_1672x941_v18.png"
PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_chroma_grid_1672x941_v18.png"
MASK_PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_chroma_grid_mask_preview_v18.png"

# Row-major order is also the final focus order.
ANCHORS = [
    ("RUS_union_of_peasants_and_workers.png", 220, 190),
    ("generic_seize_press.png", 594, 190),
    ("CHI_the_party_state.png", 968, 190),
    ("ANQ_northern_school.png", 1342, 190),
    ("generic_syndicalist_workers.png", 220, 651),
    ("generic_seize_railway.png", 594, 651),
    ("generic_workers_democracy.png", 968, 651),
    ("RUS_soldier_with_flag.png", 1342, 651),
]


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("RGBA", CANVAS_SIZE, CHROMA)
    mask = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
    mask_draw = ImageDraw.Draw(mask)
    mask_preview = canvas.copy()
    preview_draw = ImageDraw.Draw(mask_preview)

    for filename, cell_left, cell_top in ANCHORS:
        icon = Image.open(KR_GOALS / filename).convert("RGBA")
        if icon.width > CELL_SIZE or icon.height > CELL_SIZE:
            raise ValueError(f"{filename} is larger than {CELL_SIZE}x{CELL_SIZE}: {icon.size}")

        icon_left = cell_left + (CELL_SIZE - icon.width) // 2
        icon_top = cell_top + (CELL_SIZE - icon.height) // 2
        canvas.alpha_composite(icon, (icon_left, icon_top))
        mask_preview.alpha_composite(icon, (icon_left, icon_top))

        center_x = cell_left + CELL_SIZE // 2
        center_y = cell_top + CELL_SIZE // 2
        edit_left = center_x - EDIT_SIZE // 2
        edit_top = center_y - EDIT_SIZE // 2
        edit_right = edit_left + EDIT_SIZE
        edit_bottom = edit_top + EDIT_SIZE
        mask_draw.rectangle(
            (edit_left, edit_top, edit_right - 1, edit_bottom - 1),
            fill=(255, 255, 255, 0),
        )
        preview_draw.rectangle(
            (edit_left, edit_top, edit_right - 1, edit_bottom - 1),
            outline=(255, 255, 255, 255),
            width=2,
        )
        print(
            f"{filename}: source={icon.width}x{icon.height}, "
            f"cell=({cell_left},{cell_top}), edit=({edit_left},{edit_top})-({edit_right - 1},{edit_bottom - 1})"
        )

    canvas.save(ANCHOR_CANVAS)
    canvas.save(PREVIEW)
    mask.save(EDIT_MASK)
    mask_preview.save(MASK_PREVIEW)

    print(f"anchor canvas: {ANCHOR_CANVAS}")
    print(f"edit mask: {EDIT_MASK}")
    print(f"preview: {PREVIEW}")
    print(f"mask preview: {MASK_PREVIEW}")


if __name__ == "__main__":
    main()
