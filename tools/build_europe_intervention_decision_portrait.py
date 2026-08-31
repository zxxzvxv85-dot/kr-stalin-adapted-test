from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "gfx" / "interface" / "RUS_europe_intervention"
SOURCE = ASSET_DIR / "decision_portrait_source.png"
OUTPUT = ASSET_DIR / "decision_portrait.png"
SCALE = 4
FINAL_SIZE = (180, 202)


def scaled_polygon(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return [(x * SCALE, y * SCALE) for x, y in points]


def polygon_mask(size: tuple[int, int], points: list[tuple[int, int]]) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(scaled_polygon(points), fill=255)
    return mask


def build_portrait() -> Image.Image:
    work_size = (FINAL_SIZE[0] * SCALE, FINAL_SIZE[1] * SCALE)
    outer = [(10, 6), (157, 1), (171, 188), (24, 201)]
    metal = [(14, 9), (154, 4), (167, 185), (28, 197)]
    recess = [(18, 13), (152, 8), (163, 181), (32, 193)]
    picture = [(22, 17), (149, 12), (160, 177), (36, 188)]

    result = Image.new("RGBA", work_size, (0, 0, 0, 0))

    shadow_mask = polygon_mask(work_size, [(15, 10), (162, 5), (176, 192), (29, 205)])
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(4 * SCALE))
    shadow = Image.new("RGBA", work_size, (0, 0, 0, 0))
    shadow.putalpha(shadow_mask.point(lambda value: value * 3 // 5))
    result.alpha_composite(shadow)

    outer_mask = polygon_mask(work_size, outer)
    metal_mask = polygon_mask(work_size, metal)
    picture_mask = polygon_mask(work_size, picture)

    draw = ImageDraw.Draw(result)
    draw.polygon(scaled_polygon(outer), fill=(20, 22, 21, 255))
    draw.polygon(scaled_polygon(metal), fill=(128, 132, 126, 255))

    rng = random.Random(1936)
    noise = Image.frombytes(
        "L",
        work_size,
        bytes(rng.randrange(90, 166) for _ in range(work_size[0] * work_size[1])),
    )
    vertical_light = Image.new("L", work_size)
    vertical_light.putdata(
        [
            max(58, min(205, 184 - y * 112 // work_size[1]))
            for y in range(work_size[1])
            for _ in range(work_size[0])
        ]
    )
    metal_texture = ImageChops.blend(vertical_light, noise, 0.18)
    textured_metal = Image.merge("RGBA", (metal_texture, metal_texture, metal_texture, metal_mask))
    result.alpha_composite(textured_metal)

    draw = ImageDraw.Draw(result)
    draw.polygon(scaled_polygon(recess), fill=(34, 36, 34, 255))

    with Image.open(SOURCE) as image:
        source = ImageOps.fit(
            image.convert("RGB"),
            (127 * SCALE, 171 * SCALE),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.05),
        ).convert("RGBA")

    shear = 13 / 171
    x0 = 22 * SCALE
    y0 = 17 * SCALE
    transformed = source.transform(
        work_size,
        Image.Transform.AFFINE,
        (1, -shear, -x0 + shear * y0, 0, 1, -y0),
        resample=Image.Resampling.BICUBIC,
    )
    transformed.putalpha(ImageChops.multiply(transformed.getchannel("A"), picture_mask))
    result.alpha_composite(transformed)

    draw = ImageDraw.Draw(result)
    line = SCALE
    draw.line(scaled_polygon([outer[0], outer[1], outer[2]]), fill=(174, 179, 170, 255), width=line)
    draw.line(scaled_polygon([outer[2], outer[3], outer[0]]), fill=(7, 8, 8, 255), width=2 * line)
    draw.line(scaled_polygon([metal[0], metal[1], metal[2]]), fill=(207, 211, 198, 255), width=line)
    draw.line(scaled_polygon([metal[2], metal[3], metal[0]]), fill=(45, 47, 45, 255), width=2 * line)
    draw.line(scaled_polygon([picture[0], picture[1], picture[2]]), fill=(77, 80, 75, 255), width=line)
    draw.line(scaled_polygon([picture[2], picture[3], picture[0]]), fill=(10, 11, 10, 255), width=2 * line)

    result.putalpha(ImageChops.lighter(result.getchannel("A"), outer_mask))
    return result.resize(FINAL_SIZE, Image.Resampling.LANCZOS)


if __name__ == "__main__":
    final = build_portrait()
    final.save(OUTPUT, optimize=True)
    print(f"Wrote {OUTPUT} ({final.width}x{final.height}, {final.mode})")
