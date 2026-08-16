import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


FINAL_SIZE = (65, 67)
WORK_SIZE = (260, 268)
INNER_QUAD = ((7.5, 10.0), (39.5, 7.5), (43.0, 53.0), (11.0, 56.0))


def make_hole_mask(size, feather):
    scale_x = size[0] / FINAL_SIZE[0]
    scale_y = size[1] / FINAL_SIZE[1]
    polygon = [(round(x * scale_x), round(y * scale_y)) for x, y in INNER_QUAD]
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(feather * max(scale_x, scale_y)))
    return mask


def extract_frame(reference, size, feather):
    reference = reference.convert("RGBA")
    if reference.size != size:
        reference = reference.resize(size, Image.Resampling.LANCZOS)

    alpha = reference.getchannel("A")
    hole = make_hole_mask(size, feather)
    alpha = Image.composite(Image.new("L", size, 0), alpha, hole)
    reference.putalpha(alpha)
    return reference


def main():
    parser = argparse.ArgumentParser(description="Extract a reusable transparent advisor frame from the KR Bukharin portrait.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-final", required=True, type=Path)
    parser.add_argument("--output-work", required=True, type=Path)
    parser.add_argument("--feather", type=float, default=0.45)
    args = parser.parse_args()

    reference = Image.open(args.input)
    final_frame = extract_frame(reference, FINAL_SIZE, args.feather)
    work_frame = extract_frame(reference, WORK_SIZE, args.feather)

    args.output_final.parent.mkdir(parents=True, exist_ok=True)
    args.output_work.parent.mkdir(parents=True, exist_ok=True)
    final_frame.save(args.output_final)
    work_frame.save(args.output_work)


if __name__ == "__main__":
    main()
