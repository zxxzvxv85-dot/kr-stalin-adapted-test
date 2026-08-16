from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SIZE = 768
FINAL_SIZE = 64
RNG = random.Random(18560710)


def rgba() -> Image.Image:
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def mask() -> Image.Image:
    return Image.new("L", (SIZE, SIZE), 0)


def polygon_mask(points: list[tuple[int, int]]) -> Image.Image:
    result = mask()
    ImageDraw.Draw(result).polygon(points, fill=255)
    return result


def vertical_gradient(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    result = rgba()
    pixels = result.load()
    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(SIZE):
            pixels[x, y] = (*color, 255)
    return result


def clipped_gradient(
    target: Image.Image,
    shape: Image.Image,
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> None:
    target.alpha_composite(Image.composite(vertical_gradient(top, bottom), rgba(), shape))


def add_clipped_noise(target: Image.Image, shape: Image.Image, opacity: int = 20) -> None:
    noise = Image.new("L", (SIZE, SIZE), 0)
    data = [RNG.randrange(0, 256) for _ in range(SIZE * SIZE)]
    noise.putdata(data)
    noise = noise.filter(ImageFilter.GaussianBlur(0.7))
    alpha = ImageChops.multiply(shape, noise.point(lambda p: p * opacity // 255))
    texture = Image.new("RGBA", (SIZE, SIZE), (238, 220, 174, 0))
    texture.putalpha(alpha)
    target.alpha_composite(texture)


def add_shadow(target: Image.Image, shape: Image.Image, offset: tuple[int, int], blur: int, alpha: int) -> None:
    shifted = ImageChops.offset(shape, offset[0], offset[1])
    if offset[0] > 0:
        ImageDraw.Draw(shifted).rectangle((0, 0, offset[0], SIZE), fill=0)
    if offset[1] > 0:
        ImageDraw.Draw(shifted).rectangle((0, 0, SIZE, offset[1]), fill=0)
    shifted = shifted.filter(ImageFilter.GaussianBlur(blur)).point(lambda p: p * alpha // 255)
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    layer.putalpha(shifted)
    target.alpha_composite(layer)


def ellipse_layer(box: tuple[int, int, int, int], fill: tuple[int, int, int, int]) -> Image.Image:
    layer = rgba()
    ImageDraw.Draw(layer).ellipse(box, fill=fill)
    return layer


def rounded_layer(
    box: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int, int]
) -> Image.Image:
    layer = rgba()
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=radius, fill=fill)
    return layer


def draw_plaque(canvas: Image.Image) -> None:
    outer_points = [(174, 86), (594, 86), (654, 146), (654, 612), (594, 678), (174, 678), (114, 612), (114, 146)]
    outer = polygon_mask(outer_points)
    add_shadow(canvas, outer, (23, 28), 24, 200)
    clipped_gradient(canvas, outer, (126, 103, 62), (40, 30, 25))
    add_clipped_noise(canvas, outer, 26)

    inner_points = [(192, 112), (576, 112), (626, 162), (626, 592), (576, 646), (192, 646), (142, 592), (142, 162)]
    inner = polygon_mask(inner_points)
    clipped_gradient(canvas, inner, (114, 34, 38), (43, 17, 25))
    add_clipped_noise(canvas, inner, 18)

    bevel = rgba()
    d = ImageDraw.Draw(bevel)
    d.line(outer_points + [outer_points[0]], fill=(229, 205, 139, 190), width=9, joint="curve")
    d.line(inner_points + [inner_points[0]], fill=(36, 23, 22, 230), width=13, joint="curve")
    d.line(inner_points[:4], fill=(225, 156, 94, 95), width=5, joint="curve")
    canvas.alpha_composite(bevel)

    vignette = mask()
    vd = ImageDraw.Draw(vignette)
    vd.ellipse((128, 96, 640, 690), fill=170)
    vignette = ImageChops.subtract(inner, vignette.filter(ImageFilter.GaussianBlur(75)))
    shade = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    shade.putalpha(vignette.point(lambda p: p * 110 // 255))
    canvas.alpha_composite(shade)


def draw_bolts(canvas: Image.Image) -> None:
    for x, y in ((178, 166), (590, 166), (178, 590), (590, 590)):
        canvas.alpha_composite(ellipse_layer((x - 19, y - 19, x + 19, y + 19), (23, 18, 17, 210)))
        canvas.alpha_composite(ellipse_layer((x - 14, y - 14, x + 14, y + 14), (194, 151, 84, 255)))
        canvas.alpha_composite(ellipse_layer((x - 8, y - 9, x + 6, y + 5), (244, 213, 150, 190)))
        line = rgba()
        ImageDraw.Draw(line).line((x - 8, y + 6, x + 8, y - 6), fill=(55, 38, 27, 255), width=5)
        canvas.alpha_composite(line)


def draw_arcs(canvas: Image.Image) -> None:
    left = [(300, 227), (270, 202), (246, 223), (220, 188), (192, 216), (166, 186)]
    right = [(468, 227), (498, 201), (522, 224), (549, 187), (578, 216), (605, 180)]
    for points in (left, right):
        glow = rgba()
        gd = ImageDraw.Draw(glow)
        gd.line(points, fill=(80, 170, 255, 210), width=30, joint="curve")
        glow = glow.filter(ImageFilter.GaussianBlur(20))
        canvas.alpha_composite(glow)

        core = rgba()
        cd = ImageDraw.Draw(core)
        cd.line(points, fill=(72, 153, 238, 255), width=12, joint="curve")
        cd.line(points, fill=(209, 237, 255, 255), width=5, joint="curve")
        canvas.alpha_composite(core)

    terminals = rgba()
    td = ImageDraw.Draw(terminals)
    for x, y in ((165, 187), (606, 181)):
        td.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(197, 160, 103, 255))
        td.ellipse((x - 10, y - 11, x + 8, y + 7), fill=(243, 218, 163, 230))
    canvas.alpha_composite(terminals)


def draw_coil(canvas: Image.Image) -> None:
    shadow = mask()
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((283, 205, 485, 579), radius=48, fill=255)
    add_shadow(canvas, shadow, (18, 20), 18, 190)

    base = rgba()
    bd = ImageDraw.Draw(base)
    bd.rounded_rectangle((272, 535, 496, 590), radius=20, fill=(38, 31, 29, 255))
    bd.rounded_rectangle((290, 521, 478, 566), radius=17, fill=(151, 111, 62, 255))
    bd.rectangle((310, 511, 458, 543), fill=(71, 51, 37, 255))
    bd.line((300, 531, 468, 531), fill=(239, 194, 116, 190), width=5)
    canvas.alpha_composite(base)

    stem = rounded_layer((344, 238, 424, 528), 30, (38, 46, 51, 255))
    canvas.alpha_composite(stem)
    stem_hi = rgba()
    sh = ImageDraw.Draw(stem_hi)
    sh.rounded_rectangle((355, 247, 374, 516), radius=9, fill=(157, 183, 186, 100))
    sh.rounded_rectangle((400, 247, 414, 516), radius=8, fill=(3, 7, 9, 125))
    canvas.alpha_composite(stem_hi)

    coil = rgba()
    cd = ImageDraw.Draw(coil)
    for i in range(8):
        y = 310 + i * 25
        inset = round(abs(3.5 - i) * 4)
        box = (318 + inset, y, 450 - inset, y + 13)
        cd.rounded_rectangle(box, radius=6, fill=(48, 28, 23, 255))
        cd.line((box[0] + 4, y + 3, box[2] - 4, y + 3), fill=(247, 162, 76, 255), width=5)
        cd.line((box[0] + 6, y + 9, box[2] - 6, y + 9), fill=(118, 53, 29, 255), width=3)
    cd.line((342, 313, 342, 490), fill=(255, 205, 121, 125), width=5)
    cd.line((430, 313, 430, 489), fill=(35, 22, 19, 165), width=6)
    canvas.alpha_composite(coil)

    cap_shadow = ellipse_layer((251, 190, 517, 291), (0, 0, 0, 175)).filter(ImageFilter.GaussianBlur(12))
    canvas.alpha_composite(cap_shadow)
    canvas.alpha_composite(ellipse_layer((245, 172, 523, 270), (45, 48, 49, 255)))
    canvas.alpha_composite(ellipse_layer((255, 169, 513, 251), (180, 158, 113, 255)))
    canvas.alpha_composite(ellipse_layer((268, 177, 500, 237), (47, 53, 55, 255)))
    canvas.alpha_composite(ellipse_layer((286, 184, 482, 220), (221, 204, 157, 150)))
    canvas.alpha_composite(ellipse_layer((303, 195, 465, 217), (31, 37, 39, 255)))

    connector = rgba()
    con = ImageDraw.Draw(connector)
    con.rounded_rectangle((355, 224, 413, 300), radius=14, fill=(94, 70, 45, 255))
    con.rounded_rectangle((366, 228, 385, 293), radius=8, fill=(223, 179, 106, 170))
    canvas.alpha_composite(connector)


def draw_lower_emblem(canvas: Image.Image) -> None:
    gear = rgba()
    gd = ImageDraw.Draw(gear)
    gd.ellipse((319, 555, 449, 685), fill=(29, 28, 29, 235), outline=(201, 157, 85, 255), width=12)
    gd.ellipse((340, 576, 428, 664), fill=(99, 32, 31, 255), outline=(60, 42, 30, 255), width=7)
    # Three-phase rotor motif, kept broad for 64 px readability.
    gd.arc((352, 586, 417, 651), 195, 335, fill=(235, 196, 119, 255), width=13)
    gd.arc((352, 586, 417, 651), 315, 95, fill=(235, 196, 119, 255), width=13)
    gd.arc((352, 586, 417, 651), 75, 215, fill=(235, 196, 119, 255), width=13)
    gd.ellipse((375, 609, 393, 627), fill=(35, 29, 26, 255))
    canvas.alpha_composite(gear)


def render() -> Image.Image:
    canvas = rgba()
    draw_plaque(canvas)
    draw_bolts(canvas)
    draw_arcs(canvas)
    draw_coil(canvas)
    draw_lower_emblem(canvas)

    # A subtle overall warm highlight helps the icon match HOI4's painted UI art.
    highlight = Image.new("RGBA", (SIZE, SIZE), (255, 222, 168, 0))
    hm = mask()
    ImageDraw.Draw(hm).ellipse((170, 87, 585, 340), fill=40)
    highlight.putalpha(hm.filter(ImageFilter.GaussianBlur(42)))
    canvas.alpha_composite(highlight)
    return canvas


def main() -> None:
    source = render()
    final = source.resize((FINAL_SIZE, FINAL_SIZE), Image.Resampling.LANCZOS)

    source_path = ROOT / "tools/art_sources/RUS_tesla_electrical_industries_source.png"
    preview_path = ROOT / "tools/art_previews/RUS_tesla_electrical_industries_preview.png"
    final_path = ROOT / "gfx/interface/ideas/RUS_tesla_electrical_industries.png"
    for path in (source_path, preview_path, final_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    source.save(source_path)
    final.save(final_path)

    preview = Image.new("RGBA", (640, 360), (25, 27, 29, 255))
    large = final.resize((256, 256), Image.Resampling.NEAREST)
    preview.alpha_composite(large, (64, 52))
    preview.alpha_composite(source.resize((256, 256), Image.Resampling.LANCZOS), (360, 52))
    ImageDraw.Draw(preview).rectangle((63, 51, 320, 309), outline=(91, 91, 91, 255), width=1)
    ImageDraw.Draw(preview).rectangle((359, 51, 616, 309), outline=(91, 91, 91, 255), width=1)
    preview.save(preview_path)

    print(f"source={source_path}")
    print(f"preview={preview_path}")
    print(f"final={final_path}")


if __name__ == "__main__":
    main()
