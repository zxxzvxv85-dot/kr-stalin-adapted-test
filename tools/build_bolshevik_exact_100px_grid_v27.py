from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / "tmp/imagegen"
OUTPUT_DIR = ROOT / "output/imagegen"

CANVAS_SIZE = (3344, 1888)
CHROMA = (0, 255, 0, 255)
PLATE_COLOR = (38, 35, 31, 255)
PLATE_SIZE = 100

CENTERS = [
    (512, 512), (1280, 512), (2048, 512), (2816, 512),
    (512, 1376), (1280, 1376), (2048, 1376), (2816, 1376),
]

EDIT_TARGET = TMP_DIR / "RUS_kamenev_bolshevik_exact_100px_grid_3344x1888_v27.png"
EDIT_MASK = TMP_DIR / "RUS_kamenev_bolshevik_exact_100px_grid_mask_3344x1888_v27.png"
TARGET_PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_exact_100px_grid_template_v27.png"
MASK_PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_exact_100px_grid_mask_preview_v27.png"
SUBJECT_SOURCE = OUTPUT_DIR / "RUS_kamenev_bolshevik_low_resolution_repaint_1680x944_v26.png"
STYLE_SOURCE = OUTPUT_DIR / "RUS_kamenev_bolshevik_official_KR_style_reference_1672x941_v25.png"
SUBJECT_REFERENCE = TMP_DIR / "RUS_kamenev_bolshevik_subject_reference_3344x1888_v27.png"
STYLE_REFERENCE = TMP_DIR / "RUS_kamenev_bolshevik_style_reference_3344x1888_v27.png"


def plate_box(center_x: int, center_y: int) -> tuple[int, int, int, int]:
    radius = PLATE_SIZE // 2
    return (
        center_x - radius,
        center_y - radius,
        center_x + radius - 1,
        center_y + radius - 1,
    )


def padded_reference(source_path: Path, fill: tuple[int, int, int, int]) -> Image.Image:
    source = Image.open(source_path).convert("RGBA")
    canvas = Image.new("RGBA", CANVAS_SIZE, fill)
    canvas.alpha_composite(
        source,
        ((CANVAS_SIZE[0] - source.width) // 2, (CANVAS_SIZE[1] - source.height) // 2),
    )
    return canvas


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    target = Image.new("RGBA", CANVAS_SIZE, CHROMA)
    target_draw = ImageDraw.Draw(target)
    mask = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
    mask_draw = ImageDraw.Draw(mask)
    mask_preview = target.copy()
    preview_draw = ImageDraw.Draw(mask_preview)

    for center_x, center_y in CENTERS:
        box = plate_box(center_x, center_y)
        target_draw.ellipse(box, fill=PLATE_COLOR)
        mask_draw.ellipse(box, fill=(255, 255, 255, 0))
        preview_draw.ellipse(box, fill=PLATE_COLOR, outline=(255, 255, 255, 255), width=1)

    target.save(EDIT_TARGET)
    target.save(TARGET_PREVIEW)
    mask.save(EDIT_MASK)
    mask_preview.save(MASK_PREVIEW)
    padded_reference(SUBJECT_SOURCE, CHROMA).save(SUBJECT_REFERENCE)
    padded_reference(STYLE_SOURCE, (7, 20, 24, 255)).save(STYLE_REFERENCE)

    print(f"canvas: {CANVAS_SIZE[0]}x{CANVAS_SIZE[1]}")
    print(f"plate diameter: {PLATE_SIZE}px")
    print(f"edit target: {EDIT_TARGET}")
    print(f"edit mask: {EDIT_MASK}")
    print(f"target preview: {TARGET_PREVIEW}")
    print(f"mask preview: {MASK_PREVIEW}")
    print(f"subject reference: {SUBJECT_REFERENCE}")
    print(f"style reference: {STYLE_REFERENCE}")


if __name__ == "__main__":
    main()
