from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from build_bolshevik_large_canvas_v9 import ICON_SIZE, NODES, ROOT


SOURCE = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_large_canvas_guide_1672x941_v9.png"
GUIDE = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_circular_canvas_guide_1672x941_v12.png"
PREVIEW = ROOT / "output/imagegen/RUS_kamenev_bolshevik_circular_canvas_guide_1672x941_v12.png"


def main() -> None:
    canvas = Image.open(SOURCE).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    for _, left, top in NODES:
        draw.ellipse(
            (left + 4, top + 4, left + ICON_SIZE - 5, top + ICON_SIZE - 5),
            outline=(231, 211, 150, 255),
            width=1,
        )
        draw.line(
            (left + ICON_SIZE // 2, top + 4, left + ICON_SIZE // 2, top + ICON_SIZE - 5),
            fill=(92, 116, 112, 255),
            width=1,
        )
        draw.line(
            (left + 4, top + ICON_SIZE // 2, left + ICON_SIZE - 5, top + ICON_SIZE // 2),
            fill=(92, 116, 112, 255),
            width=1,
        )

    GUIDE.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(GUIDE)
    canvas.save(PREVIEW)


if __name__ == "__main__":
    main()
