from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_framed_normalized_1672x941_v9.png"
GUIDE = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_large_canvas_guide_1672x941_v9.png"
OUTPUT_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_framed_100px_v9"
TREE_PREVIEW = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_framed_exact_100px_v9.png"
CONTACT_SHEET = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_framed_100px_contact_v9.png"

ICON_SIZE = 100
CONTENT_SIZE = 96
BACKGROUND = (6, 19, 23)

# Full, unclipped generated badge extents on the normalized V9 canvas.
ICONS = [
    ("RUS_kamenev_bol_register_returning_members", (765, 46, 903, 163), (795, 61)),
    ("RUS_kamenev_bol_restore_pravda", (525, 191, 665, 319), (571, 212)),
    ("RUS_kamenev_bol_restore_central_bureau", (1000, 191, 1133, 319), (1019, 212)),
    ("RUS_kamenev_bol_unify_planning_apparatus", (303, 358, 434, 487), (347, 372)),
    ("RUS_kamenev_bol_rebuild_factory_cells", (769, 358, 901, 487), (795, 372)),
    ("RUS_kamenev_bol_railway_telegraph_bureau", (525, 519, 666, 654), (571, 531)),
    ("RUS_kamenev_bol_win_vst_majority", (995, 520, 1136, 650), (1019, 531)),
    ("RUS_kamenev_bol_undissolved_central_committee", (768, 695, 902, 828), (795, 694)),
]


def fit_icon(source: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    crop = source.crop(box)
    crop.thumbnail((CONTENT_SIZE, CONTENT_SIZE), Image.Resampling.LANCZOS)
    result = Image.new("RGB", (ICON_SIZE, ICON_SIZE), BACKGROUND)
    left = (ICON_SIZE - crop.width) // 2
    top = (ICON_SIZE - crop.height) // 2
    result.paste(crop, (left, top))
    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGB")
    tree = Image.open(GUIDE).convert("RGB")
    contact = Image.new("RGB", (400, 200), BACKGROUND)

    for index, (name, source_box, target_xy) in enumerate(ICONS):
        icon = fit_icon(source, source_box)
        icon.save(OUTPUT_DIR / f"{name}.png", optimize=True)
        tree.paste(icon, target_xy)
        contact.paste(icon, ((index % 4) * ICON_SIZE, (index // 4) * ICON_SIZE))

    tree.save(TREE_PREVIEW, optimize=True)
    contact.save(CONTACT_SHEET, optimize=True)


if __name__ == "__main__":
    main()
