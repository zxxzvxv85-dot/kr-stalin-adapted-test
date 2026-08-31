from __future__ import annotations

from pathlib import Path

from PIL import Image

from build_bolshevik_large_canvas_v8 import CANVAS_SIZE, ICON_SIZE, NODES


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_exact_100px_v8.png"
NORMALIZED = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_normalized_2048x1152_v8.png"
OUTPUT_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_normalized_100px_v8"
CONTACT = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_normalized_100px_v8.png"

FILENAMES = [
    "RUS_kamenev_bol_register_returning_members.png",
    "RUS_kamenev_bol_restore_pravda.png",
    "RUS_kamenev_bol_restore_central_bureau.png",
    "RUS_kamenev_bol_unify_planning_apparatus.png",
    "RUS_kamenev_bol_rebuild_factory_cells.png",
    "RUS_kamenev_bol_railway_telegraph_bureau.png",
    "RUS_kamenev_bol_win_vst_majority.png",
    "RUS_kamenev_bol_undissolved_central_committee.png",
]


def main() -> None:
    source = Image.open(SOURCE).convert("RGBA")
    normalized = source.resize(CANVAS_SIZE, Image.Resampling.LANCZOS)
    normalized.save(NORMALIZED)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    contact = Image.new("RGBA", (ICON_SIZE * 4, ICON_SIZE * 2), (0, 0, 0, 0))
    for index, ((_, left, top), filename) in enumerate(zip(NODES, FILENAMES, strict=True)):
        crop = normalized.crop((left, top, left + ICON_SIZE, top + ICON_SIZE))
        crop.save(OUTPUT_DIR / filename)
        contact.alpha_composite(crop, ((index % 4) * ICON_SIZE, (index // 4) * ICON_SIZE))
    contact.save(CONTACT)

    print(f"source_size={source.width}x{source.height}")
    print(f"normalized_size={normalized.width}x{normalized.height}")
    print(f"icon_count={len(FILENAMES)}")
    print(f"icon_size={ICON_SIZE}x{ICON_SIZE}")
    print(f"contact_size={contact.width}x{contact.height}")


if __name__ == "__main__":
    main()
