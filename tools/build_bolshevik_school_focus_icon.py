from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "gfx/interface/goals/RUS_kamenev_politics"
FRAME_DIR = ROOT / "gfx/interface/goals/frames"
OUTPUT_DIR = ROOT / "output/imagegen"
NAME = "RUS_kamenev_bol_unify_planning_apparatus"
WORK_SIZE = 800
MASTER_SIZE = 400
FINAL_SIZE = 100


def regular_polygon(cx: float, cy: float, radii: list[float], start: float = -90) -> list[tuple[float, float]]:
    step = 360 / len(radii)
    return [
        (
            cx + radius * math.cos(math.radians(start + index * step)),
            cy + radius * math.sin(math.radians(start + index * step)),
        )
        for index, radius in enumerate(radii)
    ]


def star_points(cx: float, cy: float, outer: float, inner: float) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for index in range(10):
        radius = outer if index % 2 == 0 else inner
        angle = math.radians(-90 + index * 36)
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def masked_gradient(mask: Image.Image, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    width, height = mask.size
    image = Image.new("RGBA", mask.size)
    pixels = image.load()
    for y in range(height):
        t = y / max(1, height - 1)
        directional = max(0.0, 1.0 - (y / height) * 0.75)
        for x in range(width):
            left_light = max(0.0, 1.0 - (x + y * 0.38) / (width * 0.9))
            lift = int(20 * left_light * directional)
            pixels[x, y] = (
                min(255, int(top[0] * (1 - t) + bottom[0] * t) + lift),
                min(255, int(top[1] * (1 - t) + bottom[1] * t) + lift),
                min(255, int(top[2] * (1 - t) + bottom[2] * t) + lift),
                mask.getpixel((x, y)),
            )
    return image


def texture_overlay(size: tuple[int, int], seed: int, strength: int) -> Image.Image:
    rng = random.Random(seed)
    noise = Image.new("L", size)
    noise.putdata([128 + rng.randint(-strength, strength) for _ in range(size[0] * size[1])])
    noise = noise.filter(ImageFilter.GaussianBlur(0.45))
    rgba = Image.new("RGBA", size, (96, 74, 50, 0))
    rgba.putalpha(ImageEnhance.Contrast(noise).enhance(1.3).point(lambda value: abs(value - 128) * 2))
    return rgba


def build_art() -> Image.Image:
    size = WORK_SIZE
    art = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    circle_mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(circle_mask).ellipse((112, 112, 688, 688), fill=255)

    backdrop = Image.new("RGBA", (size, size), (20, 34, 30, 255))
    draw = ImageDraw.Draw(backdrop)
    for y in range(120, 690):
        t = (y - 120) / 570
        color = (
            int(39 * (1 - t) + 16 * t),
            int(60 * (1 - t) + 30 * t),
            int(49 * (1 - t) + 27 * t),
            255,
        )
        draw.line((105, y, 695, y), fill=color, width=1)

    # Chalkboard surround and simple organisational diagram.
    draw.rounded_rectangle((150, 145, 650, 492), radius=16, fill=(25, 50, 42, 255), outline=(100, 86, 62, 255), width=13)
    draw.line((400, 205, 400, 278), fill=(154, 158, 130, 145), width=8)
    draw.line((275, 278, 525, 278), fill=(154, 158, 130, 145), width=8)
    draw.line((275, 278, 275, 342), fill=(154, 158, 130, 145), width=8)
    draw.line((525, 278, 525, 342), fill=(154, 158, 130, 145), width=8)
    for box in ((353, 167, 447, 225), (230, 327, 320, 382), (480, 327, 570, 382)):
        draw.rounded_rectangle(box, radius=10, outline=(171, 174, 144, 150), width=8)

    # Warm upper-left classroom light, kept behind the book.
    light_mask = Image.new("L", (size, size), 0)
    light_draw = ImageDraw.Draw(light_mask)
    light_draw.polygon([(90, 70), (355, 70), (610, 650), (210, 650)], fill=100)
    light_mask = light_mask.filter(ImageFilter.GaussianBlur(45))
    warm = Image.new("RGBA", (size, size), (240, 186, 95, 0))
    warm.putalpha(light_mask)
    backdrop = Image.alpha_composite(backdrop, warm)
    draw = ImageDraw.Draw(backdrop)

    # Solid wooden lectern.
    draw.polygon([(250, 515), (550, 515), (610, 680), (190, 680)], fill=(67, 36, 25, 255), outline=(31, 21, 19, 255), width=14)
    draw.polygon([(225, 506), (575, 506), (550, 555), (250, 555)], fill=(125, 71, 40, 255), outline=(43, 27, 22, 255), width=10)
    draw.line((280, 575, 244, 664), fill=(151, 88, 45, 170), width=10)
    draw.line((520, 575, 556, 664), fill=(31, 21, 20, 210), width=10)

    # Open book: broad silhouette, warm pages, no lettering.
    left_page = [(174, 425), (381, 452), (398, 611), (207, 573), (154, 509)]
    right_page = [(626, 425), (419, 452), (402, 611), (593, 573), (646, 509)]
    draw.polygon(left_page, fill=(225, 205, 157, 255), outline=(61, 39, 28, 255), width=13)
    draw.polygon(right_page, fill=(237, 218, 172, 255), outline=(61, 39, 28, 255), width=13)
    draw.line((400, 458, 400, 612), fill=(88, 53, 34, 255), width=12)
    draw.line((386, 461, 398, 607), fill=(255, 238, 191, 190), width=5)
    draw.arc((177, 448, 388, 599), 205, 328, fill=(116, 82, 53, 155), width=6)
    draw.arc((412, 448, 623, 599), 212, 335, fill=(116, 82, 53, 155), width=6)
    for offset in (0, 28, 56):
        draw.line((228, 495 + offset, 345, 510 + offset), fill=(119, 98, 67, 120), width=6)
        draw.line((455, 510 + offset, 572, 495 + offset), fill=(119, 98, 67, 120), width=6)

    # Restrained aged print texture, clipped to the artwork plate.
    grain = texture_overlay((size, size), seed=1937, strength=18)
    grain.putalpha(ImageChops.multiply(grain.getchannel("A"), circle_mask.point(lambda value: value // 4)))
    backdrop = Image.alpha_composite(backdrop, grain)
    art.paste(backdrop, (0, 0), circle_mask)
    return art


def build_frame() -> Image.Image:
    size = WORK_SIZE
    center = size / 2
    frame = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Six points per tooth produce a hard-edged Bolshevik gear silhouette.
    radii: list[float] = []
    for _ in range(16):
        radii.extend((344, 344, 382, 382, 344, 344))
    gear_mask = Image.new("L", (size, size), 0)
    gear_draw = ImageDraw.Draw(gear_mask)
    gear_draw.polygon(regular_polygon(center, center, radii), fill=255)
    gear_draw.ellipse((126, 126, 674, 674), fill=0)
    gear = masked_gradient(gear_mask, (106, 113, 112), (35, 40, 43))
    frame = Image.alpha_composite(frame, gear)

    draw = ImageDraw.Draw(frame)
    # Angular bevels and inner steel ring.
    draw.ellipse((105, 105, 695, 695), outline=(28, 30, 31, 255), width=25)
    draw.ellipse((120, 120, 680, 680), outline=(180, 184, 171, 255), width=8)
    draw.ellipse((133, 133, 667, 667), outline=(49, 53, 54, 255), width=17)
    draw.arc((112, 112, 688, 688), 205, 315, fill=(205, 211, 195, 210), width=6)
    draw.arc((112, 112, 688, 688), 15, 135, fill=(18, 20, 22, 230), width=8)

    # Straight enamel inserts identify the political frame without wreaths.
    inserts = [
        [(92, 493), (149, 466), (190, 600), (131, 630)],
        [(708, 493), (651, 466), (610, 600), (669, 630)],
    ]
    for polygon in inserts:
        draw.polygon(polygon, fill=(55, 22, 22, 255), outline=(21, 22, 23, 255), width=14)
        inset = [(x + (4 if x < center else -4), y - 3) for x, y in polygon]
        draw.polygon(inset, fill=(112, 28, 29, 255), outline=(169, 90, 70, 255), width=5)

    # Small steel rivets reinforce the urban-industrial frame language.
    for angle in (42, 138, 222, 318):
        x = center + 309 * math.cos(math.radians(angle))
        y = center + 309 * math.sin(math.radians(angle))
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(116, 122, 119, 255), outline=(22, 24, 25, 255), width=5)
        draw.ellipse((x - 4, y - 5, x + 3, y + 2), fill=(218, 214, 190, 180))

    # Compact red star at the crown, with steel-gold edging.
    outer_star = star_points(center, 112, 80, 34)
    inner_star = star_points(center, 112, 61, 26)
    draw.polygon(outer_star, fill=(45, 43, 40, 255), outline=(17, 18, 19, 255), width=8)
    draw.polygon(star_points(center, 112, 72, 31), fill=(190, 165, 104, 255))
    draw.polygon(inner_star, fill=(139, 26, 27, 255), outline=(64, 15, 18, 255), width=5)
    draw.line((400, 54, 400, 142), fill=(233, 108, 78, 180), width=4)
    draw.line((346, 129, 400, 112), fill=(237, 116, 82, 150), width=4)

    # Surface wear is subtle and remains clipped to the frame alpha.
    rng = random.Random(1917)
    for _ in range(420):
        x = rng.randrange(65, 735)
        y = rng.randrange(65, 735)
        if frame.getpixel((x, y))[3] > 20:
            tone = rng.choice(((220, 213, 182, 28), (8, 10, 11, 35), (132, 61, 42, 25)))
            radius = rng.choice((1, 1, 2, 3))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=tone)
    return frame


def save_outputs() -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    art = build_art()
    frame = build_frame()
    composite = Image.alpha_composite(art, frame)

    resample = Image.Resampling.LANCZOS
    art_master = art.resize((MASTER_SIZE, MASTER_SIZE), resample)
    frame_master = frame.resize((MASTER_SIZE, MASTER_SIZE), resample)
    composite_master = composite.resize((MASTER_SIZE, MASTER_SIZE), resample)
    final = composite.resize((FINAL_SIZE, FINAL_SIZE), resample)

    art_master.save(ICON_DIR / f"{NAME}_artwork.png")
    frame_master.save(FRAME_DIR / "RUS_bolshevik_political_focus_frame_standard.png")
    composite_master.save(ICON_DIR / f"{NAME}_source.png")
    final.save(ICON_DIR / f"{NAME}.png")

    neighbors = [
        "RUS_kamenev_bol_restore_pravda.png",
        "RUS_kamenev_bol_rebuild_factory_cells.png",
        f"{NAME}.png",
        "RUS_kamenev_bol_railway_telegraph_bureau.png",
        "RUS_kamenev_bol_restore_central_bureau.png",
    ]
    preview = Image.new("RGBA", (600, 120), (19, 19, 18, 255))
    for index, filename in enumerate(neighbors):
        icon = Image.open(ICON_DIR / filename).convert("RGBA").resize((100, 100), resample)
        preview.alpha_composite(icon, (10 + index * 120, 10))
    preview.save(OUTPUT_DIR / f"{NAME}_neighbor_preview.png")


if __name__ == "__main__":
    save_outputs()
