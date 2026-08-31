from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "tmp/imagegen"
GUIDE = OUTPUT_DIR / "RUS_kamenev_bolshevik_eight_icon_strict_guide_v3.png"
MASK = OUTPUT_DIR / "RUS_kamenev_bolshevik_eight_icon_strict_mask_v3.png"

# The configured provider returns 1254x1254 images even when 1024x1024 is
# requested. Matching its native output avoids resampling the 100px slots.
CANVAS_SIZE = (1254, 1254)
SLOT_SIZE = 100
SLOTS = [
    (127, 427),
    (427, 427),
    (727, 427),
    (1027, 427),
    (127, 727),
    (427, 727),
    (727, 727),
    (1027, 727),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    guide = Image.new("RGBA", CANVAS_SIZE, (18, 17, 16, 255))
    guide_draw = ImageDraw.Draw(guide)
    mask = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
    mask_draw = ImageDraw.Draw(mask)

    for left, top in SLOTS:
        guide_draw.rectangle(
            (left - 1, top - 1, left + SLOT_SIZE, top + SLOT_SIZE),
            fill=(60, 55, 48, 255),
        )
        guide_draw.rectangle(
            (left, top, left + SLOT_SIZE - 1, top + SLOT_SIZE - 1),
            fill=(31, 28, 24, 255),
        )
        mask_draw.rectangle(
            (left, top, left + SLOT_SIZE - 1, top + SLOT_SIZE - 1),
            fill=(255, 255, 255, 0),
        )

    guide.save(GUIDE)
    mask.save(MASK)


if __name__ == "__main__":
    main()
