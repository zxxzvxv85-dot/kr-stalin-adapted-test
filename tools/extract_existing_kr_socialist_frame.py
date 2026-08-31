from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT.parent
KR_GOALS = WORKSHOP / "1521695605/gfx/interface/goals"

SOURCE_A = KR_GOALS / "RUS_radsocs.png"
SOURCE_B = KR_GOALS / "RUS_syndies.png"
OUTPUT = ROOT / "output/imagegen/RUS_socialist_shared_frame_extracted_from_KR.png"
PREVIEW = ROOT / "output/imagegen/RUS_socialist_shared_frame_extracted_from_KR_preview.png"

CANVAS_SIZE = (100, 100)
DIFF_THRESHOLD = 32
INNER_CUTOFF_RADIUS = 29.5


def extract_shared_frame(first: Image.Image, second: Image.Image) -> Image.Image:
    if first.size != second.size:
        raise RuntimeError(f"Source sizes differ: {first.size} != {second.size}")

    width, height = first.size
    centre_x = (width - 1) / 2
    centre_y = (height - 1) / 2
    extracted = Image.new("RGBA", first.size, (0, 0, 0, 0))

    first_pixels = first.load()
    second_pixels = second.load()
    output_pixels = extracted.load()

    for y in range(height):
        for x in range(width):
            radius = ((x - centre_x) ** 2 + (y - centre_y) ** 2) ** 0.5
            if radius < INNER_CUTOFF_RADIUS:
                continue

            pixel_a = first_pixels[x, y]
            pixel_b = second_pixels[x, y]
            if not pixel_a[3] or not pixel_b[3]:
                continue

            difference = max(abs(pixel_a[channel] - pixel_b[channel]) for channel in range(4))
            if difference > DIFF_THRESHOLD:
                continue

            output_pixels[x, y] = (
                (pixel_a[0] + pixel_b[0]) // 2,
                (pixel_a[1] + pixel_b[1]) // 2,
                (pixel_a[2] + pixel_b[2]) // 2,
                min(pixel_a[3], pixel_b[3]),
            )

    return extracted


def checkerboard(size: tuple[int, int], cell: int = 8) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    colours = ((68, 68, 68, 255), (104, 104, 104, 255))
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            draw.rectangle(
                (x, y, min(x + cell - 1, size[0] - 1), min(y + cell - 1, size[1] - 1)),
                fill=colours[(x // cell + y // cell) % 2],
            )
    return image


def main() -> None:
    source_a = Image.open(SOURCE_A).convert("RGBA")
    source_b = Image.open(SOURCE_B).convert("RGBA")
    frame = extract_shared_frame(source_a, source_b)

    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    offset = ((CANVAS_SIZE[0] - frame.width) // 2, (CANVAS_SIZE[1] - frame.height) // 2)
    canvas.alpha_composite(frame, offset)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT)

    backgrounds = [
        checkerboard(CANVAS_SIZE),
        Image.new("RGBA", CANVAS_SIZE, (8, 18, 22, 255)),
        Image.new("RGBA", CANVAS_SIZE, (236, 234, 224, 255)),
    ]
    preview = Image.new("RGBA", (CANVAS_SIZE[0] * 3, CANVAS_SIZE[1]), (0, 0, 0, 0))
    for index, background in enumerate(backgrounds):
        background.alpha_composite(canvas)
        preview.alpha_composite(background, (index * CANVAS_SIZE[0], 0))
    preview.resize((1200, 400), Image.Resampling.NEAREST).save(PREVIEW)

    alpha = canvas.getchannel("A")
    print(f"source_size={source_a.width}x{source_a.height}")
    print(f"output_size={canvas.width}x{canvas.height}")
    print(f"alpha_bbox={alpha.getbbox()}")
    print(f"nonzero_alpha_pixels={sum(alpha.histogram()[1:])}")
    print(f"output={OUTPUT.resolve()}")
    print(f"preview={PREVIEW.resolve()}")


if __name__ == "__main__":
    main()
