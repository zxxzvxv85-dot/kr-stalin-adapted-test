from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

from build_bolshevik_focus_tree_generation_template import CANVAS_SIZE, ICON_SIZE, NODES


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_frame_candidates_guide_v5.png"
MASK = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_frame_candidates_mask_v5.png"
OUTPUT = ROOT / "output/imagegen/RUS_kamenev_bolshevik_frame_candidates_v5.png"
CROP_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_frame_candidates_v5"
CONTACT_SHEET = ROOT / "output/imagegen/RUS_kamenev_bolshevik_frame_candidates_v5_actual_size.png"


def main() -> None:
    guide = Image.open(GUIDE).convert("RGBA")
    mask = Image.open(MASK).convert("RGBA")
    output = Image.open(OUTPUT).convert("RGBA")

    if guide.size != CANVAS_SIZE or mask.size != CANVAS_SIZE:
        raise RuntimeError(f"Invalid guide or mask size: {guide.size=}, {mask.size=}")
    if output.size != CANVAS_SIZE:
        raise RuntimeError(f"Provider changed canvas size: expected {CANVAS_SIZE}, got {output.size}")

    diff = ImageChops.difference(output, guide)
    outside_mask = mask.getchannel("A")
    changed = diff.convert("RGB").convert("L").point(lambda value: 255 if value else 0)
    changed_outside = ImageChops.multiply(changed, outside_mask)
    outside_changed_pixels = sum(1 for value in changed_outside.getdata() if value)

    CROP_DIR.mkdir(parents=True, exist_ok=True)
    contact = Image.new("RGBA", (ICON_SIZE * 4, ICON_SIZE * 2), (0, 0, 0, 0))
    for index, (_, left, top) in enumerate(NODES, start=1):
        crop = output.crop((left, top, left + ICON_SIZE, top + ICON_SIZE))
        crop.save(CROP_DIR / f"candidate_{index}.png")
        contact.alpha_composite(crop, (((index - 1) % 4) * ICON_SIZE, ((index - 1) // 4) * ICON_SIZE))
    contact.save(CONTACT_SHEET)

    print(f"output_size={output.width}x{output.height}")
    print(f"outside_mask_changed_pixels={outside_changed_pixels}")
    print(f"candidate_count={len(NODES)}")
    print(f"candidate_size={ICON_SIZE}x{ICON_SIZE}")
    print(f"contact_sheet_size={contact.width}x{contact.height}")


if __name__ == "__main__":
    main()
