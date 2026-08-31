from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

from build_bolshevik_large_canvas_v8 import CANVAS_SIZE, ICON_SIZE, NODES


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_large_canvas_guide_v8.png"
MASK = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_large_canvas_mask_v8.png"
OUTPUT = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_exact_100px_v8.png"
CROP_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_exact_100px_v8"
CONTACT = ROOT / "output/imagegen/RUS_kamenev_bolshevik_large_canvas_exact_100px_v8_actual_size.png"

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
    guide = Image.open(GUIDE).convert("RGBA")
    mask = Image.open(MASK).convert("RGBA")
    output = Image.open(OUTPUT).convert("RGBA")
    if output.size != CANVAS_SIZE:
        raise RuntimeError(f"Provider changed canvas size: expected {CANVAS_SIZE}, got {output.size}")

    diff = ImageChops.difference(output, guide)
    changed = diff.convert("RGB").convert("L").point(lambda value: 255 if value else 0)
    outside_changed = ImageChops.multiply(changed, mask.getchannel("A"))
    outside_changed_pixels = sum(1 for value in outside_changed.getdata() if value)

    CROP_DIR.mkdir(parents=True, exist_ok=True)
    contact = Image.new("RGBA", (ICON_SIZE * 4, ICON_SIZE * 2), (0, 0, 0, 0))
    for index, ((_, left, top), filename) in enumerate(zip(NODES, FILENAMES, strict=True)):
        crop = output.crop((left, top, left + ICON_SIZE, top + ICON_SIZE))
        crop.save(CROP_DIR / filename)
        contact.alpha_composite(crop, ((index % 4) * ICON_SIZE, (index // 4) * ICON_SIZE))
    contact.save(CONTACT)

    print(f"output_size={output.width}x{output.height}")
    print(f"outside_mask_changed_pixels={outside_changed_pixels}")
    print(f"icon_count={len(FILENAMES)}")
    print(f"icon_size={ICON_SIZE}x{ICON_SIZE}")
    print(f"contact_sheet_size={contact.width}x{contact.height}")


if __name__ == "__main__":
    main()
