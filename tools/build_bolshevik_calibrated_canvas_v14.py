from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from build_bolshevik_large_canvas_v9 import ICON_SIZE, NODES, ROOT


SOURCE = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_large_canvas_guide_1672x941_v9.png"
GUIDE = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_calibrated_48px_guide_1672x941_v14.png"
PREVIEW = ROOT / "output/imagegen/RUS_kamenev_bolshevik_calibrated_48px_guide_1672x941_v14.png"
CALIBRATED_DIAMETER = 48


def main() -> None:
    canvas = Image.open(SOURCE).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    inset = (ICON_SIZE - CALIBRATED_DIAMETER) // 2
    for _, left, top in NODES:
        box = (
            left + inset,
            top + inset,
            left + inset + CALIBRATED_DIAMETER - 1,
            top + inset + CALIBRATED_DIAMETER - 1,
        )
        draw.ellipse(box, outline=(231, 211, 150, 255), width=1)
        cx = left + ICON_SIZE // 2
        cy = top + ICON_SIZE // 2
        draw.line((cx, box[1], cx, box[3]), fill=(92, 116, 112, 255), width=1)
        draw.line((box[0], cy, box[2], cy), fill=(92, 116, 112, 255), width=1)

    GUIDE.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(GUIDE)
    canvas.save(PREVIEW)


if __name__ == "__main__":
    main()
