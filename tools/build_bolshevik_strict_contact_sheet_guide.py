from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "tmp/imagegen"
GUIDE = OUTPUT_DIR / "RUS_kamenev_bolshevik_eight_icon_strict_guide.png"
MASK = OUTPUT_DIR / "RUS_kamenev_bolshevik_eight_icon_strict_mask.png"

CANVAS_SIZE = (1024, 1024)
SLOT_SIZE = 100
SLOTS = [
    (112, 337),
    (312, 337),
    (512, 337),
    (712, 337),
    (112, 587),
    (312, 587),
    (512, 587),
    (712, 587),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    guide = Image.new("RGBA", CANVAS_SIZE, (18, 17, 16, 255))
    guide_draw = ImageDraw.Draw(guide)
    for left, top in SLOTS:
        guide_draw.rectangle(
            (left - 1, top - 1, left + SLOT_SIZE, top + SLOT_SIZE),
            fill=(60, 55, 48, 255),
        )
        guide_draw.rectangle(
            (left, top, left + SLOT_SIZE - 1, top + SLOT_SIZE - 1),
            fill=(31, 28, 24, 255),
        )

    # Transparent mask pixels are editable; opaque pixels remain unchanged.
    mask = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
    mask_draw = ImageDraw.Draw(mask)
    for left, top in SLOTS:
        mask_draw.rectangle(
            (left, top, left + SLOT_SIZE - 1, top + SLOT_SIZE - 1),
            fill=(255, 255, 255, 0),
        )

    guide.save(GUIDE)
    mask.save(MASK)


if __name__ == "__main__":
    main()
