from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/imagegen/RUS_kamenev_bolshevik_circular_framed_1672x941_v12.png"
GUIDE = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_large_canvas_guide_1672x941_v9.png"
OUTPUT_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_circular_framed_100px_v12"
TREE_PREVIEW = ROOT / "output/imagegen/RUS_kamenev_bolshevik_circular_framed_exact_100px_tree_v12.png"
CONTACT_SHEET = ROOT / "output/imagegen/RUS_kamenev_bolshevik_circular_framed_100px_contact_v12.png"

ICON_SIZE = 100
CONTENT_SIZE = 96
BACKGROUND = (6, 19, 23)

ICONS = [
    ("RUS_kamenev_bol_register_returning_members", (747, 48, 919, 195), (795, 61)),
    ("RUS_kamenev_bol_restore_pravda", (477, 226, 651, 379), (571, 212)),
    ("RUS_kamenev_bol_restore_central_bureau", (1018, 226, 1192, 379), (1019, 212)),
    ("RUS_kamenev_bol_unify_planning_apparatus", (270, 413, 447, 567), (347, 372)),
    ("RUS_kamenev_bol_rebuild_factory_cells", (746, 409, 921, 564), (795, 372)),
    ("RUS_kamenev_bol_railway_telegraph_bureau", (477, 565, 652, 711), (571, 531)),
    ("RUS_kamenev_bol_win_vst_majority", (1016, 562, 1193, 711), (1019, 531)),
    ("RUS_kamenev_bol_undissolved_central_committee", (746, 725, 921, 873), (795, 694)),
]


def fit_icon(source: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    crop = source.crop(box)
    crop.thumbnail((CONTENT_SIZE, CONTENT_SIZE), Image.Resampling.LANCZOS)
    result = Image.new("RGB", (ICON_SIZE, ICON_SIZE), BACKGROUND)
    result.paste(crop, ((ICON_SIZE - crop.width) // 2, (ICON_SIZE - crop.height) // 2))
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
