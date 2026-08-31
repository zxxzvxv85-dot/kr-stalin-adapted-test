from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
KR_GOALS = WORKSHOP_ROOT / "1521695605/gfx/interface/goals"
TMP_DIR = ROOT / "tmp/imagegen"
OUTPUT_DIR = ROOT / "output/imagegen"

BASE_GUIDE = TMP_DIR / "RUS_kamenev_bolshevik_large_canvas_guide_1672x941_v9.png"
ANCHOR_CANVAS = TMP_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_1672x941_v17.png"
EDIT_MASK = TMP_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_mask_1672x941_v17.png"
PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_1672x941_v17.png"
MASK_PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_mask_preview_v17.png"

NODE_SIZE = 100
ANCHORS = [
    ("RUS_union_of_peasants_and_workers.png", 795, 61),
    ("generic_seize_press.png", 571, 212),
    ("CHI_the_party_state.png", 1019, 212),
    ("ANQ_northern_school.png", 347, 372),
    ("generic_syndicalist_workers.png", 795, 372),
    ("generic_seize_railway.png", 571, 531),
    ("generic_workers_democracy.png", 1019, 531),
    ("RUS_soldier_with_flag.png", 795, 694),
]


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    canvas = Image.open(BASE_GUIDE).convert("RGBA")
    mask = Image.new("RGBA", canvas.size, (255, 255, 255, 255))
    mask_draw = ImageDraw.Draw(mask)

    preview = canvas.copy()
    preview_draw = ImageDraw.Draw(preview)

    for filename, node_left, node_top in ANCHORS:
        icon_path = KR_GOALS / filename
        icon = Image.open(icon_path).convert("RGBA")
        if icon.width > NODE_SIZE or icon.height > NODE_SIZE:
            raise ValueError(f"{filename} is larger than its 100x100 node: {icon.size}")

        left = node_left + (NODE_SIZE - icon.width) // 2
        top = node_top + (NODE_SIZE - icon.height) // 2
        right = left + icon.width
        bottom = top + icon.height

        canvas.alpha_composite(icon, (left, top))
        preview.alpha_composite(icon, (left, top))

        # Only this exact native-size rectangle can be changed by the edit call.
        mask_draw.rectangle((left, top, right - 1, bottom - 1), fill=(255, 255, 255, 0))
        preview_draw.rectangle((left, top, right - 1, bottom - 1), outline=(255, 220, 70, 255), width=1)

        print(f"{filename}: {icon.width}x{icon.height} at ({left},{top})-({right - 1},{bottom - 1})")

    canvas.save(ANCHOR_CANVAS)
    canvas.save(PREVIEW)
    mask.save(EDIT_MASK)

    # Human-readable mask preview: editable rectangles in red, locked area dimmed.
    mask_preview = canvas.convert("RGB")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 150))
    mask_preview = Image.alpha_composite(mask_preview.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(mask_preview)
    for filename, node_left, node_top in ANCHORS:
        with Image.open(KR_GOALS / filename) as icon:
            left = node_left + (NODE_SIZE - icon.width) // 2
            top = node_top + (NODE_SIZE - icon.height) // 2
            draw.rectangle(
                (left, top, left + icon.width - 1, top + icon.height - 1),
                outline=(255, 62, 55, 255),
                width=2,
            )
    mask_preview.save(MASK_PREVIEW)

    print(f"anchor canvas: {ANCHOR_CANVAS}")
    print(f"edit mask: {EDIT_MASK}")
    print(f"preview: {PREVIEW}")
    print(f"mask preview: {MASK_PREVIEW}")


if __name__ == "__main__":
    main()
