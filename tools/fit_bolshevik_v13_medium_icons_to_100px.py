from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/imagegen/RUS_kamenev_bolshevik_circular_medium_simple_1672x941_v13.png"
GUIDE = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_large_canvas_guide_1672x941_v9.png"
OUTPUT_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_circular_medium_simple_100px_v13"
TREE_PREVIEW = ROOT / "output/imagegen/RUS_kamenev_bolshevik_circular_medium_simple_exact_100px_tree_v13.png"
CONTACT_SHEET = ROOT / "output/imagegen/RUS_kamenev_bolshevik_circular_medium_simple_100px_contact_v13.png"

ICON_SIZE = 100
CONTENT_SIZE = 96
BACKGROUND = (6, 19, 23)

ICONS = [
    ("RUS_kamenev_bol_register_returning_members", (731, 45, 940, 217), (795, 61)),
    ("RUS_kamenev_bol_restore_pravda", (429, 237, 640, 411), (571, 212)),
    ("RUS_kamenev_bol_restore_central_bureau", (1025, 235, 1236, 412), (1019, 212)),
    ("RUS_kamenev_bol_unify_planning_apparatus", (210, 434, 419, 614), (347, 372)),
    ("RUS_kamenev_bol_rebuild_factory_cells", (728, 430, 940, 615), (795, 372)),
    ("RUS_kamenev_bol_railway_telegraph_bureau", (429, 588, 642, 768), (571, 531)),
    ("RUS_kamenev_bol_win_vst_majority", (1023, 586, 1237, 769), (1019, 531)),
    ("RUS_kamenev_bol_undissolved_central_committee", (728, 706, 941, 889), (795, 694)),
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
