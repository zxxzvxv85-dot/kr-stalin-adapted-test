from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / "tmp/imagegen"
OUTPUT_DIR = ROOT / "output/imagegen"

GUIDE = TMP_DIR / "RUS_kamenev_bolshevik_large_canvas_guide_v8.png"
MASK = TMP_DIR / "RUS_kamenev_bolshevik_large_canvas_mask_v8.png"
PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_large_canvas_guide_v8.png"

CANVAS_SIZE = (2048, 1152)
ICON_SIZE = 100
NODES = [
    ("一切权力归苏维埃", 974, 75),
    ("《真理报》重返俄罗斯", 700, 260),
    ("两张党证", 1248, 260),
    ("开设党校", 426, 455),
    ("车间里的党小组", 974, 455),
    ("铁路与电报联络局", 700, 650),
    ("设立最高纲领派联络处", 1248, 650),
    ("高举红旗", 974, 850),
]
EDGES = [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 6), (4, 7), (5, 7)]


def font(size: int) -> ImageFont.ImageFont:
    for path in (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf")):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("RGBA", CANVAS_SIZE, (5, 18, 22, 255))
    draw = ImageDraw.Draw(canvas)
    for y in range(CANVAS_SIZE[1]):
        shade = 17 + y * 7 // CANVAS_SIZE[1]
        draw.line((0, y, CANVAS_SIZE[0], y), fill=(5, shade, shade + 5, 255))

    draw.rectangle((0, 0, CANVAS_SIZE[0] - 1, 52), fill=(30, 31, 30, 255))
    draw.line((0, 52, CANVAS_SIZE[0], 52), fill=(124, 127, 120, 255), width=2)
    draw.text((22, 13), "俄共（布）组织路线", font=font(20), fill=(231, 231, 222, 255))

    # The connecting tree establishes UI scale across the large canvas.
    for parent, child in EDGES:
        _, px, py = NODES[parent]
        _, cx, cy = NODES[child]
        start = (px + ICON_SIZE // 2, py + ICON_SIZE)
        end = (cx + ICON_SIZE // 2, cy)
        bend_y = (start[1] + end[1]) // 2
        draw.line((start[0], start[1], start[0], bend_y), fill=(164, 61, 57, 255), width=2)
        draw.line((start[0], bend_y, end[0], bend_y), fill=(164, 61, 57, 255), width=2)
        draw.line((end[0], bend_y, end[0], end[1]), fill=(164, 61, 57, 255), width=2)

    label_font = font(15)
    for label, left, top in NODES:
        # The editable icon region is exactly these 100x100 pixels. Its border
        # sits outside the mask and acts as a hard visual ruler.
        draw.rectangle(
            (left, top, left + ICON_SIZE - 1, top + ICON_SIZE - 1),
            fill=(9, 20, 23, 255),
        )
        draw.rectangle(
            (left - 2, top - 2, left + ICON_SIZE + 1, top + ICON_SIZE + 1),
            outline=(225, 226, 217, 255),
            width=2,
        )
        for offset in range(0, ICON_SIZE + 1, 10):
            tick = 4 if offset % 50 else 7
            draw.line((left + offset, top - 3, left + offset, top - 3 - tick), fill=(204, 76, 68, 255), width=1)
            draw.line((left - 3, top + offset, left - 3 - tick, top + offset), fill=(204, 76, 68, 255), width=1)

        box = draw.textbbox((0, 0), label, font=label_font)
        label_width = box[2] - box[0]
        label_left = left + ICON_SIZE // 2 - label_width // 2 - 10
        label_top = top + ICON_SIZE + 8
        draw.rectangle(
            (label_left, label_top, label_left + label_width + 20, label_top + 30),
            fill=(8, 17, 19, 255),
            outline=(198, 201, 193, 255),
            width=1,
        )
        draw.text((label_left + 10, label_top + 5), label, font=label_font, fill=(235, 235, 226, 255))

    canvas.save(GUIDE)
    canvas.save(PREVIEW)

    mask = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
    mask_draw = ImageDraw.Draw(mask)
    for _, left, top in NODES:
        mask_draw.rectangle(
            (left, top, left + ICON_SIZE - 1, top + ICON_SIZE - 1),
            fill=(255, 255, 255, 0),
        )
    mask.save(MASK)


if __name__ == "__main__":
    main()
