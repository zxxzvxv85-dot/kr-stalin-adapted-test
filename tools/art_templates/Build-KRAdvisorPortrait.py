import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


WORK_SIZE = (260, 268)
FINAL_SIZE = (65, 67)
CARD_QUAD = ((18, 30), (171, 17), (187, 226), (31, 239))


def parse_crop(value):
    parts = tuple(int(part.strip()) for part in value.split(","))
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("crop must be left,top,right,bottom")
    return parts


def perspective_coefficients(source, destination):
    rows = []
    values = []
    for (sx, sy), (dx, dy) in zip(source, destination):
        rows.append([sx, sy, 1, 0, 0, 0, -dx * sx, -dx * sy])
        rows.append([0, 0, 0, sx, sy, 1, -dy * sx, -dy * sy])
        values.extend([dx, dy])
    matrix = np.linalg.solve(np.asarray(rows, dtype=float), np.asarray(values, dtype=float))
    return tuple(matrix)


def prepare_portrait(image, crop):
    image = image.crop(crop).convert("RGB")
    image = ImageOps.fit(image, (168, 224), method=Image.Resampling.LANCZOS)
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image, cutoff=(1, 1))
    image = ImageEnhance.Contrast(image).enhance(0.96)
    image = ImageEnhance.Brightness(image).enhance(0.94)
    image = image.filter(ImageFilter.UnsharpMask(radius=0.8, percent=75, threshold=4))

    values = np.asarray(image, dtype=np.float32)
    y, x = np.indices(values.shape)
    cx = values.shape[1] * 0.53
    cy = values.shape[0] * 0.45
    distance = ((x - cx) / values.shape[1]) ** 2 + ((y - cy) / values.shape[0]) ** 2
    values = 18.0 + values * 0.84
    values *= np.clip(1.03 - distance * 0.38, 0.78, 1.0)
    rng = np.random.default_rng(1917)
    values += rng.normal(0, 1.2, values.shape)
    values = np.clip(values, 0, 255).astype(np.uint8)

    image = Image.fromarray(values, mode="L")
    image = ImageOps.colorize(image, black="#151817", white="#d6d5cd")
    return image.convert("RGBA")


def warp_to_card(image):
    source = ((0, 0), (image.width - 1, 0), (image.width - 1, image.height - 1), (0, image.height - 1))
    inverse = perspective_coefficients(CARD_QUAD, source)
    return image.transform(
        WORK_SIZE,
        Image.Transform.PERSPECTIVE,
        inverse,
        resample=Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )


def make_preview(final_image, frame, path):
    scale = 8
    tile_size = (FINAL_SIZE[0] * scale, FINAL_SIZE[1] * scale)
    canvas = Image.new("RGB", (tile_size[0] * 2, tile_size[1]), (174, 174, 174))
    for index, item in enumerate((final_image, frame.resize(FINAL_SIZE, Image.Resampling.LANCZOS))):
        tile = Image.new("RGBA", FINAL_SIZE, (174, 174, 174, 255))
        tile.alpha_composite(item)
        tile = tile.convert("RGB").resize(tile_size, Image.Resampling.NEAREST)
        canvas.paste(tile, (tile_size[0] * index, 0))
    canvas.save(path)


def main():
    parser = argparse.ArgumentParser(description="Build a KR-style 65x67 advisor portrait using the reusable Bukharin frame.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--frame", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--crop", required=True, type=parse_crop)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()

    portrait = prepare_portrait(Image.open(args.input), args.crop)
    card = warp_to_card(portrait)
    frame = Image.open(args.frame).convert("RGBA")
    if frame.size == FINAL_SIZE:
        frame = frame.resize(WORK_SIZE, Image.Resampling.LANCZOS)
    elif frame.size != WORK_SIZE:
        raise ValueError(
            f"frame must be {FINAL_SIZE[0]}x{FINAL_SIZE[1]} or {WORK_SIZE[0]}x{WORK_SIZE[1]}"
        )

    card.alpha_composite(frame)
    final_image = card.resize(FINAL_SIZE, Image.Resampling.LANCZOS)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    final_image.save(args.output)

    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        make_preview(final_image, frame, args.preview)


if __name__ == "__main__":
    main()
