from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output/imagegen"

SOURCE = OUTPUT_DIR / "RUS_kamenev_bolshevik_exact_100px_grid_3344x1888_v27.png"
OVERLAY = OUTPUT_DIR / "RUS_kamenev_bolshevik_exact_100px_grid_validation_overlay_v27.png"
ACTUAL_CROPS = OUTPUT_DIR / "RUS_kamenev_bolshevik_actual_100px_center_crops_v27.png"

REQUESTED_CANVAS_SIZE = (3344, 1888)
PLATE_SIZE = 100
CENTERS = [
    (512, 512), (1280, 512), (2048, 512), (2816, 512),
    (512, 1376), (1280, 1376), (2048, 1376), (2816, 1376),
]


def expected_box(center_x: int, center_y: int) -> tuple[int, int, int, int]:
    radius = PLATE_SIZE // 2
    return (
        center_x - radius,
        center_y - radius,
        center_x + radius,
        center_y + radius,
    )


def runs(values: list[int], threshold: int, minimum_length: int) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(values + [0]):
        if value > threshold and start is None:
            start = index
        elif value <= threshold and start is not None:
            if index - start >= minimum_length:
                result.append((start, index))
            start = None
    return result


def main() -> None:
    source = Image.open(SOURCE).convert("RGBA")
    rgb = source.convert("RGB")
    green = Image.new("RGB", source.size, (0, 255, 0))
    difference = ImageChops.difference(rgb, green).convert("L")
    mask = difference.point(lambda value: 255 if value > 24 else 0)

    column_projection = list(mask.resize((source.width, 1), Image.Resampling.BOX).get_flattened_data())
    row_projection = list(mask.resize((1, source.height), Image.Resampling.BOX).get_flattened_data())
    x_runs = runs(column_projection, threshold=8, minimum_length=20)
    y_runs = runs(row_projection, threshold=8, minimum_length=20)

    detected: list[tuple[int, int, int, int]] = []
    for top, bottom in y_runs:
        for left, right in x_runs:
            local_bbox = mask.crop((left, top, right, bottom)).getbbox()
            if local_bbox is None:
                continue
            detected.append(
                (
                    left + local_bbox[0],
                    top + local_bbox[1],
                    left + local_bbox[2],
                    top + local_bbox[3],
                )
            )

    overlay = source.copy()
    draw = ImageDraw.Draw(overlay)
    for box in detected:
        draw.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), outline=(255, 205, 0, 255), width=5)
        center_x = (box[0] + box[2]) // 2
        center_y = (box[1] + box[3]) // 2
        actual_box = expected_box(center_x, center_y)
        draw.rectangle(
            (actual_box[0], actual_box[1], actual_box[2] - 1, actual_box[3] - 1),
            outline=(0, 255, 255, 255),
            width=3,
        )

    scale_x = source.width / REQUESTED_CANVAS_SIZE[0]
    scale_y = source.height / REQUESTED_CANVAS_SIZE[1]
    scaled_plate_size = round(PLATE_SIZE * min(scale_x, scale_y))
    scaled_radius = scaled_plate_size // 2
    for center_x, center_y in CENTERS:
        scaled_center_x = round(center_x * scale_x)
        scaled_center_y = round(center_y * scale_y)
        box = (
            scaled_center_x - scaled_radius,
            scaled_center_y - scaled_radius,
            scaled_center_x + scaled_radius,
            scaled_center_y + scaled_radius,
        )
        draw.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), outline=(255, 255, 255, 255), width=5)
    overlay.save(OVERLAY)

    contact = Image.new("RGBA", (460, 240), (7, 20, 24, 255))
    for index, box in enumerate(detected):
        center_x = (box[0] + box[2]) // 2
        center_y = (box[1] + box[3]) // 2
        crop = source.crop(expected_box(center_x, center_y))
        x = 10 + (index % 4) * 110
        y = 10 + (index // 4) * 110
        contact.alpha_composite(crop, (x, y))
        ImageDraw.Draw(contact).rectangle((x, y, x + 99, y + 99), outline=(255, 255, 255, 255))
    contact.save(ACTUAL_CROPS)

    print(f"requested dimensions: {REQUESTED_CANVAS_SIZE[0]}x{REQUESTED_CANVAS_SIZE[1]}")
    print(f"actual dimensions: {source.width}x{source.height}")
    print(f"requested slots: {len(CENTERS)} at {PLATE_SIZE}x{PLATE_SIZE}")
    print(f"template slots after service resize: approximately {scaled_plate_size}x{scaled_plate_size}")
    print(f"horizontal non-green runs: {x_runs}")
    print(f"vertical non-green runs: {y_runs}")
    for index, box in enumerate(detected, start=1):
        print(f"detected {index}: bbox={box}, size={box[2] - box[0]}x{box[3] - box[1]}")
    print(f"overlay: {OVERLAY}")
    print(f"actual 100px crops: {ACTUAL_CROPS}")


if __name__ == "__main__":
    main()
