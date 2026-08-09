from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


WORK_SIZE = 400
OUTPUT_SIZE = 100
FINAL_ART_SCALE = 0.91
TRANSPARENT = (0, 0, 0, 0)

GOLD = (204, 163, 85, 255)
LIGHT_GOLD = (241, 213, 139, 255)
DARK_GOLD = (83, 57, 31, 255)
RED = (157, 27, 38, 255)
BRIGHT_RED = (210, 42, 48, 255)
DARK_RED = (71, 17, 24, 255)
GREEN = (49, 79, 56, 255)
DARK_GREEN = (24, 46, 35, 255)
STEEL = (150, 151, 143, 255)
LIGHT_STEEL = (216, 210, 186, 255)
DARK_STEEL = (50, 52, 51, 255)
PAPER = (217, 196, 146, 255)
DARK_PAPER = (108, 80, 49, 255)
INK = (43, 35, 29, 255)

BURGUNDY_PLATE = ((105, 42, 49), (34, 28, 34))
FOREST_PLATE = ((57, 84, 59), (31, 40, 36))
TEAL_PLATE = ((47, 78, 80), (30, 39, 44))
NAVY_PLATE = ((53, 63, 84), (29, 31, 42))
OCHRE_PLATE = ((111, 80, 45), (45, 37, 31))
PLUM_PLATE = ((84, 49, 72), (36, 29, 39))

ICON_PLATE_PALETTES = {
    "RUS_kamenev_national_economic_line": TEAL_PLATE,
    "RUS_kamenev_no_permanent_creditor": BURGUNDY_PLATE,
    "RUS_kamenev_one_party_card": NAVY_PLATE,
    "RUS_kamenev_majority_rule": OCHRE_PLATE,
    "RUS_kamenev_psr_rebuild_central_committee": FOREST_PLATE,
    "RUS_kamenev_psr_preserve_land_committees": OCHRE_PLATE,
    "RUS_kamenev_psr_claim_internal_affairs": TEAL_PLATE,
    "RUS_kamenev_psr_defend_revolutionary_democracy": FOREST_PLATE,
    "RUS_kamenev_psr_land_socialisation_bill": OCHRE_PLATE,
    "RUS_kamenev_psr_peasant_congress": NAVY_PLATE,
    "RUS_kamenev_psr_final_party_congress": PLUM_PLATE,
    "RUS_kamenev_psr_cooperatives_fair_grain_prices": TEAL_PLATE,
    "RUS_kamenev_psr_local_self_government": BURGUNDY_PLATE,
    "RUS_kamenev_psr_agrarian_socialism": FOREST_PLATE,
    "RUS_kamenev_bol_register_returning_members": BURGUNDY_PLATE,
    "RUS_kamenev_bol_restore_pravda": NAVY_PLATE,
    "RUS_kamenev_bol_restore_central_bureau": FOREST_PLATE,
    "RUS_kamenev_bol_unify_planning_apparatus": PLUM_PLATE,
    "RUS_kamenev_bol_rebuild_factory_cells": NAVY_PLATE,
    "RUS_kamenev_bol_railway_telegraph_bureau": OCHRE_PLATE,
    "RUS_kamenev_bol_win_vst_majority": FOREST_PLATE,
    "RUS_kamenev_bol_undissolved_central_committee": BURGUNDY_PLATE,
}


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["arialbd.ttf", "timesbd.ttf"] if bold else ["arial.ttf", "times.ttf"]
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def shift_mask(mask: Image.Image, dx: int, dy: int) -> Image.Image:
    shifted = Image.new("L", mask.size, 0)
    shifted.paste(mask, (dx, dy))
    return shifted


def gradient_image(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    ramp = Image.linear_gradient("L").resize((WORK_SIZE, WORK_SIZE))
    return ImageOps.colorize(ramp, top, bottom).convert("RGBA")


def add_bevelled_shape(
    canvas: Image.Image,
    mask: Image.Image,
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
    shadow: int = 9,
    edge: int = 3,
) -> None:
    side_colour = Image.new("RGBA", canvas.size, (45, 31, 24, 0))
    for depth in range(12, 0, -2):
        side_alpha = shift_mask(mask, depth // 2, depth)
        side_colour.putalpha(side_alpha.point(lambda value: value * 190 // 255))
        canvas.alpha_composite(side_colour)

    shadow_mask = shift_mask(mask.filter(ImageFilter.GaussianBlur(shadow)), 6, 8)
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_layer.putalpha(shadow_mask.point(lambda value: value * 145 // 255))
    canvas.alpha_composite(shadow_layer)

    fill = gradient_image(top, bottom)
    fill.putalpha(mask)
    canvas.alpha_composite(fill)

    highlight = ImageChops.subtract(mask, shift_mask(mask, edge, edge))
    lowlight = ImageChops.subtract(mask, shift_mask(mask, -edge, -edge))
    hi_layer = Image.new("RGBA", canvas.size, (255, 240, 196, 0))
    hi_layer.putalpha(highlight.point(lambda value: value * 125 // 255))
    lo_layer = Image.new("RGBA", canvas.size, (24, 15, 13, 0))
    lo_layer.putalpha(lowlight.point(lambda value: value * 145 // 255))
    canvas.alpha_composite(hi_layer)
    canvas.alpha_composite(lo_layer)


def add_shadowed_layer(canvas: Image.Image, layer: Image.Image, blur: int = 7, offset: tuple[int, int] = (5, 7)) -> None:
    alpha = layer.getchannel("A")
    shadow = shift_mask(alpha.filter(ImageFilter.GaussianBlur(blur)), offset[0], offset[1])
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_layer.putalpha(shadow.point(lambda value: value * 165 // 255))
    canvas.alpha_composite(shadow_layer)
    canvas.alpha_composite(layer)


def diagonal_light_ramp(size: tuple[int, int]) -> Image.Image:
    vertical = Image.linear_gradient("L").resize(size)
    horizontal = vertical.rotate(90, resample=Image.Resampling.BICUBIC, expand=False)
    return ImageChops.add(vertical, horizontal, scale=2.0)


def add_relief_layer(
    canvas: Image.Image,
    layer: Image.Image,
    *,
    depth: int = 8,
    shadow_blur: int = 6,
    shadow_offset: tuple[int, int] = (9, 12),
    shadow_opacity: int = 205,
    internal_relief: bool = True,
) -> None:
    alpha = layer.getchannel("A")
    if not alpha.getbbox():
        return

    shadow = shift_mask(alpha.filter(ImageFilter.GaussianBlur(shadow_blur)), *shadow_offset)
    shadow_layer = Image.new("RGBA", canvas.size, (12, 8, 8, 0))
    shadow_layer.putalpha(shadow.point(lambda value: value * shadow_opacity // 255))
    canvas.alpha_composite(shadow_layer)

    side_rgb = ImageOps.colorize(
        ImageOps.grayscale(layer),
        (22, 14, 13),
        (100, 68, 40),
    ).convert("RGBA")
    for step in range(depth, 0, -1):
        side = side_rgb.copy()
        side.putalpha(shift_mask(alpha, step, step).point(lambda value: value * 230 // 255))
        canvas.alpha_composite(side)

    face = layer.copy()
    ramp = diagonal_light_ramp(layer.size)
    face_high = ImageChops.multiply(alpha, ImageOps.invert(ramp))
    face_low = ImageChops.multiply(alpha, ramp)
    high_layer = Image.new("RGBA", layer.size, (248, 224, 166, 0))
    high_layer.putalpha(face_high.point(lambda value: value * 38 // 255))
    low_layer = Image.new("RGBA", layer.size, (24, 15, 14, 0))
    low_layer.putalpha(face_low.point(lambda value: value * 58 // 255))
    face.alpha_composite(low_layer)
    face.alpha_composite(high_layer)

    edge_high = ImageChops.subtract(alpha, shift_mask(alpha, 4, 4))
    edge_low = ImageChops.subtract(alpha, shift_mask(alpha, -4, -4))
    bevel_high = Image.new("RGBA", layer.size, (255, 232, 176, 0))
    bevel_high.putalpha(edge_high.point(lambda value: value * 165 // 255))
    bevel_low = Image.new("RGBA", layer.size, (20, 12, 12, 0))
    bevel_low.putalpha(edge_low.point(lambda value: value * 205 // 255))
    face.alpha_composite(bevel_low)
    face.alpha_composite(bevel_high)

    if internal_relief:
        luminance = ImageOps.grayscale(layer.convert("RGB")).filter(ImageFilter.FIND_EDGES)
        luminance = ImageOps.autocontrast(luminance).filter(ImageFilter.GaussianBlur(0.8))
        luminance = luminance.point(lambda value: 0 if value < 58 else min(255, (value - 58) * 2))
        luminance = ImageChops.multiply(luminance, alpha)
        internal_high = Image.new("RGBA", layer.size, (250, 226, 172, 0))
        internal_high.putalpha(shift_mask(luminance, -3, -3).point(lambda value: value * 82 // 255))
        internal_low = Image.new("RGBA", layer.size, (18, 12, 12, 0))
        internal_low.putalpha(shift_mask(luminance, 4, 4).point(lambda value: value * 120 // 255))
        face.alpha_composite(internal_low)
        face.alpha_composite(internal_high)

    canvas.alpha_composite(face)


def make_ellipse_mask(box: tuple[int, int, int, int]) -> Image.Image:
    mask = Image.new("L", (WORK_SIZE, WORK_SIZE), 0)
    ImageDraw.Draw(mask).ellipse(box, fill=255)
    return mask


def make_gear_mask(center: tuple[int, int], outer: int, inner: int, teeth: int = 18) -> Image.Image:
    cx, cy = center
    points: list[tuple[float, float]] = []
    for index in range(teeth * 4):
        angle = -math.pi / 2 + index * math.pi / (teeth * 2)
        phase = index % 4
        radius = outer if phase in (1, 2) else outer - 17
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    mask = Image.new("L", (WORK_SIZE, WORK_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(points, fill=255)
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), fill=0)
    return mask


def rotated_rounded_rect(
    size: tuple[int, int],
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    width: int,
    angle: float,
) -> Image.Image:
    image = Image.new("RGBA", size, TRANSPARENT)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((width, width, size[0] - width - 1, size[1] - width - 1), radius, fill, outline, width)
    return image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)


def paste_center(canvas: Image.Image, image: Image.Image, center: tuple[int, int]) -> None:
    canvas.alpha_composite(image, (int(center[0] - image.width / 2), int(center[1] - image.height / 2)))


def paste_relief_center(
    canvas: Image.Image,
    image: Image.Image,
    center: tuple[int, int],
    *,
    depth: int = 4,
) -> None:
    positioned = Image.new("RGBA", canvas.size, TRANSPARENT)
    positioned.alpha_composite(image, (int(center[0] - image.width / 2), int(center[1] - image.height / 2)))
    add_relief_layer(
        canvas,
        positioned,
        depth=depth,
        shadow_blur=3,
        shadow_offset=(4, 6),
        shadow_opacity=150,
        internal_relief=True,
    )


def draw_ribbon(canvas: Image.Image, color: tuple[int, int, int, int]) -> None:
    layer = Image.new("RGBA", canvas.size, TRANSPARENT)
    draw = ImageDraw.Draw(layer)
    draw.polygon([(38, 232), (107, 209), (116, 263), (55, 293)], fill=DARK_RED, outline=DARK_GOLD, width=6)
    draw.polygon([(362, 232), (293, 209), (284, 263), (345, 293)], fill=DARK_RED, outline=DARK_GOLD, width=6)
    draw.rounded_rectangle((82, 213, 318, 278), 18, fill=color, outline=DARK_GOLD, width=8)
    layer = layer.filter(ImageFilter.GaussianBlur(0.35))
    add_shadowed_layer(canvas, layer, blur=5, offset=(4, 6))


def add_rotated_leaf(canvas: Image.Image, center: tuple[int, int], angle: float, color: tuple[int, int, int, int]) -> None:
    leaf = Image.new("RGBA", (42, 22), TRANSPARENT)
    draw = ImageDraw.Draw(leaf)
    draw.ellipse((4, 3, 36, 18), fill=color, outline=DARK_GOLD, width=3)
    draw.line((7, 12, 34, 10), fill=LIGHT_GOLD, width=2)
    leaf = leaf.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    paste_center(canvas, leaf, center)


def draw_wreath(canvas: Image.Image, wheat: bool = False) -> None:
    layer = Image.new("RGBA", canvas.size, TRANSPARENT)
    draw = ImageDraw.Draw(layer)
    draw.arc((44, 68, 356, 370), 98, 160, fill=DARK_GOLD, width=10)
    draw.arc((44, 68, 356, 370), 20, 82, fill=DARK_GOLD, width=10)
    for side in (-1, 1):
        for index in range(10):
            progress = index / 9
            theta = math.radians(132 - progress * 70)
            x = 200 + side * (142 * math.cos(theta))
            y = 246 + 126 * math.sin(theta)
            angle = (48 - progress * 76) * side
            color = LIGHT_GOLD if index % 3 == 0 else GOLD
            add_rotated_leaf(layer, (int(x), int(y)), angle, color)
            if wheat and index in (2, 4, 6, 8):
                grain = Image.new("RGBA", (22, 34), TRANSPARENT)
                gd = ImageDraw.Draw(grain)
                gd.ellipse((5, 2, 16, 18), fill=LIGHT_GOLD, outline=DARK_GOLD, width=2)
                gd.ellipse((2, 12, 12, 29), fill=GOLD, outline=DARK_GOLD, width=2)
                gd.ellipse((10, 12, 20, 29), fill=GOLD, outline=DARK_GOLD, width=2)
                grain = grain.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
                paste_center(layer, grain, (int(x), int(y - 7)))
    add_shadowed_layer(canvas, layer, blur=4, offset=(3, 5))


def build_base(theme: str, icon_id: str) -> tuple[Image.Image, Image.Image]:
    canvas = Image.new("RGBA", (WORK_SIZE, WORK_SIZE), TRANSPARENT)
    plate_top, plate_bottom = ICON_PLATE_PALETTES.get(icon_id, BURGUNDY_PLATE)
    if theme == "bol":
        gear = make_gear_mask((200, 192), 169, 139)
        add_bevelled_shape(canvas, gear, (184, 163, 112), (64, 55, 43), shadow=8)
        draw_ribbon(canvas, RED)
        plate = make_ellipse_mask((68, 53, 332, 326))
        add_bevelled_shape(canvas, plate, plate_top, plate_bottom, shadow=10)
    elif theme == "psr":
        draw_ribbon(canvas, (109, 34, 44, 255))
        plate = make_ellipse_mask((67, 54, 333, 328))
        add_bevelled_shape(canvas, plate, plate_top, plate_bottom, shadow=10)
        ring = ImageChops.subtract(make_ellipse_mask((55, 42, 345, 340)), make_ellipse_mask((72, 59, 328, 322)))
        add_bevelled_shape(canvas, ring, (223, 192, 113), (91, 64, 35), shadow=5)
        draw_wreath(canvas, wheat=True)
    else:
        draw_ribbon(canvas, (122, 36, 43, 255))
        plate = make_ellipse_mask((67, 54, 333, 328))
        add_bevelled_shape(canvas, plate, plate_top, plate_bottom, shadow=10)
        ring = ImageChops.subtract(make_ellipse_mask((55, 42, 345, 340)), make_ellipse_mask((73, 61, 327, 320)))
        add_bevelled_shape(canvas, ring, (205, 170, 94), (76, 52, 30), shadow=5)
        draw_wreath(canvas)
    return canvas, plate


def add_source_motif(
    canvas: Image.Image,
    clip: Image.Image,
    source_dir: Path,
    filename: str,
    max_size: tuple[int, int] = (224, 206),
    center: tuple[int, int] = (200, 185),
    dark: tuple[int, int, int] = (45, 38, 34),
    light: tuple[int, int, int] = (202, 173, 112),
    opacity: int = 148,
) -> None:
    path = source_dir / filename
    if not path.exists():
        return
    source = Image.open(path).convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox:
        source = source.crop(bbox)
    scale = min(max_size[0] / source.width, max_size[1] / source.height)
    source = source.resize(
        (max(1, int(source.width * scale)), max(1, int(source.height * scale))),
        Image.Resampling.LANCZOS,
    )
    gray = ImageOps.grayscale(source)
    tinted = ImageOps.colorize(gray, dark, light).convert("RGBA")
    tinted_rgb = Image.blend(tinted.convert("RGB"), source.convert("RGB"), 0.28)
    tinted = tinted_rgb.convert("RGBA")
    alpha = source.getchannel("A").point(lambda value: value * opacity // 255)
    tinted.putalpha(alpha)
    layer = Image.new("RGBA", canvas.size, TRANSPARENT)
    layer.alpha_composite(tinted, (center[0] - tinted.width // 2, center[1] - tinted.height // 2))
    clipped_alpha = ImageChops.multiply(layer.getchannel("A"), clip)
    layer.putalpha(clipped_alpha)
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.25)))


def draw_star(layer: Image.Image, center: tuple[int, int], radius: int, fill=GOLD, outline=DARK_GOLD) -> None:
    cx, cy = center
    points: list[tuple[float, float]] = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        r = radius if index % 2 == 0 else radius * 0.42
        points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    draw = ImageDraw.Draw(layer)
    draw.polygon(points, fill=fill, outline=outline)
    draw.line(points + [points[0]], fill=outline, width=max(3, radius // 9), joint="curve")


def draw_rose(layer: Image.Image, center: tuple[int, int], radius: int) -> None:
    cx, cy = center
    for index in range(8):
        angle = index * 45
        petal = Image.new("RGBA", (radius * 2, radius), TRANSPARENT)
        pd = ImageDraw.Draw(petal)
        pd.ellipse((5, 4, radius * 2 - 6, radius - 5), fill=BRIGHT_RED, outline=DARK_RED, width=5)
        petal = petal.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        distance = radius * 0.42
        theta = math.radians(angle)
        paste_center(layer, petal, (int(cx + math.cos(theta) * distance), int(cy + math.sin(theta) * distance)))
    draw = ImageDraw.Draw(layer)
    draw.ellipse((cx - radius // 2, cy - radius // 2, cx + radius // 2, cy + radius // 2), fill=RED, outline=LIGHT_GOLD, width=5)


def draw_wheat_stalk(layer: Image.Image, base: tuple[int, int], length: int, angle: float, color=LIGHT_GOLD) -> None:
    stalk = Image.new("RGBA", (50, length + 20), TRANSPARENT)
    draw = ImageDraw.Draw(stalk)
    x = 25
    draw.line((x, length + 8, x, 18), fill=DARK_GOLD, width=5)
    for index in range(7):
        y = length - 12 - index * (length - 38) / 7
        draw.ellipse((x - 19, y - 10, x - 2, y + 12), fill=color, outline=DARK_GOLD, width=3)
        draw.ellipse((x + 2, y - 10, x + 19, y + 12), fill=color, outline=DARK_GOLD, width=3)
    draw.ellipse((x - 7, 5, x + 7, 30), fill=color, outline=DARK_GOLD, width=3)
    stalk = stalk.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    paste_relief_center(layer, stalk, base, depth=3)


def draw_handshake(
    layer: Image.Image,
    center: tuple[int, int],
    scale: float = 1.0,
    left_color: tuple[int, int, int, int] = RED,
    right_color: tuple[int, int, int, int] = GREEN,
) -> None:
    cx, cy = center
    object_layer = Image.new("RGBA", layer.size, TRANSPARENT)
    left = rotated_rounded_rect((int(150 * scale), int(50 * scale)), int(18 * scale), left_color, DARK_GOLD, max(3, int(5 * scale)), -20)
    right = rotated_rounded_rect((int(150 * scale), int(50 * scale)), int(18 * scale), right_color, DARK_GOLD, max(3, int(5 * scale)), 20)
    paste_center(object_layer, left, (int(cx - 55 * scale), int(cy + 5 * scale)))
    paste_center(object_layer, right, (int(cx + 55 * scale), int(cy + 5 * scale)))
    draw = ImageDraw.Draw(object_layer)
    hand = LIGHT_GOLD
    outline = DARK_GOLD
    draw.ellipse((cx - 43 * scale, cy - 22 * scale, cx + 15 * scale, cy + 28 * scale), fill=hand, outline=outline, width=max(3, int(5 * scale)))
    draw.ellipse((cx - 15 * scale, cy - 22 * scale, cx + 43 * scale, cy + 28 * scale), fill=hand, outline=outline, width=max(3, int(5 * scale)))
    draw.rounded_rectangle((cx - 28 * scale, cy - 7 * scale, cx + 28 * scale, cy + 19 * scale), int(10 * scale), fill=hand, outline=outline, width=max(3, int(4 * scale)))
    for index in range(3):
        y = cy - 6 * scale + index * 9 * scale
        draw.line((cx - 4 * scale, y, cx + 24 * scale, y + 3 * scale), fill=(120, 86, 43, 255), width=max(2, int(3 * scale)))
    add_relief_layer(
        layer,
        object_layer,
        depth=4,
        shadow_blur=3,
        shadow_offset=(4, 6),
        shadow_opacity=155,
    )


def draw_document(
    layer: Image.Image,
    box: tuple[int, int, int, int],
    angle: float = 0,
    seal: bool = True,
    line_color=INK,
) -> None:
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    doc = Image.new("RGBA", (width + 18, height + 18), TRANSPARENT)
    draw = ImageDraw.Draw(doc)
    draw.rounded_rectangle((8, 8, width + 6, height + 6), 13, fill=PAPER, outline=DARK_PAPER, width=6)
    draw.polygon([(width - 25, 8), (width + 6, 38), (width + 6, 8)], fill=(238, 219, 169, 255), outline=DARK_PAPER)
    for index, ratio in enumerate((0.25, 0.38, 0.51, 0.64)):
        line_width = width * (0.72 if index != 2 else 0.52)
        draw.line((27, height * ratio, 27 + line_width, height * ratio), fill=line_color, width=5)
    if seal:
        draw.ellipse((width * 0.58, height * 0.68, width * 0.81, height * 0.91), fill=RED, outline=DARK_RED, width=5)
        draw_star(doc, (int(width * 0.695), int(height * 0.795)), max(8, int(width * 0.07)), fill=LIGHT_GOLD)
    doc = doc.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    paste_relief_center(layer, doc, ((x1 + x2) // 2, (y1 + y2) // 2), depth=5)


def draw_card(
    layer: Image.Image,
    center: tuple[int, int],
    size: tuple[int, int],
    angle: float,
    color: tuple[int, int, int, int],
    emblem: str,
) -> None:
    card = rotated_rounded_rect(size, 14, color, DARK_GOLD, 6, 0)
    draw = ImageDraw.Draw(card)
    draw.line((20, size[1] - 28, size[0] - 20, size[1] - 28), fill=LIGHT_GOLD, width=5)
    if emblem == "star":
        draw_star(card, (size[0] // 2, size[1] // 2 - 8), min(size) // 5, fill=LIGHT_GOLD)
    elif emblem == "rose":
        draw_rose(card, (size[0] // 2, size[1] // 2 - 8), min(size) // 6)
    else:
        draw.ellipse((size[0] // 2 - 23, size[1] // 2 - 31, size[0] // 2 + 23, size[1] // 2 + 15), outline=LIGHT_GOLD, width=8)
        draw.line((size[0] // 2 - 34, size[1] // 2 - 8, size[0] // 2 + 34, size[1] // 2 - 8), fill=LIGHT_GOLD, width=7)
    card = card.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    paste_relief_center(layer, card, center, depth=5)


def draw_people(layer: Image.Image, centers: list[tuple[int, int]], colors: list[tuple[int, int, int, int]]) -> None:
    for (cx, cy), color in zip(centers, colors):
        person = Image.new("RGBA", layer.size, TRANSPARENT)
        draw = ImageDraw.Draw(person)
        draw.ellipse((cx - 22, cy - 54, cx + 22, cy - 10), fill=LIGHT_GOLD, outline=DARK_GOLD, width=5)
        draw.polygon([(cx - 44, cy + 52), (cx - 32, cy + 2), (cx, cy - 12), (cx + 32, cy + 2), (cx + 44, cy + 52)], fill=color, outline=DARK_GOLD)
        draw.line((cx - 44, cy + 52, cx + 44, cy + 52), fill=DARK_GOLD, width=6)
        add_relief_layer(
            layer,
            person,
            depth=4,
            shadow_blur=3,
            shadow_offset=(4, 6),
            shadow_opacity=155,
        )


def draw_rifle(layer: Image.Image, start: tuple[int, int], end: tuple[int, int]) -> None:
    object_layer = Image.new("RGBA", layer.size, TRANSPARENT)
    draw = ImageDraw.Draw(object_layer)
    draw.line((start, end), fill=LIGHT_STEEL, width=13)
    draw.line((start, end), fill=DARK_STEEL, width=5)
    sx, sy = start
    ex, ey = end
    draw.polygon([(sx - 18, sy + 8), (sx + 18, sy - 7), (sx + 52, sy + 30), (sx + 13, sy + 43)], fill=(122, 72, 42, 255), outline=DARK_GOLD)
    draw.line((ex - 12, ey + 8, ex + 24, ey - 17), fill=LIGHT_STEEL, width=7)
    add_relief_layer(layer, object_layer, depth=4, shadow_blur=3, shadow_offset=(4, 6), shadow_opacity=155)


def draw_house(layer: Image.Image, center: tuple[int, int], scale: float = 1.0) -> None:
    cx, cy = center
    object_layer = Image.new("RGBA", layer.size, TRANSPARENT)
    draw = ImageDraw.Draw(object_layer)
    w = 130 * scale
    h = 90 * scale
    draw.rectangle((cx - w / 2, cy - h / 4, cx + w / 2, cy + h / 2), fill=(118, 73, 48, 255), outline=DARK_GOLD, width=max(4, int(6 * scale)))
    draw.polygon([(cx - w * 0.62, cy - h / 4), (cx, cy - h * 0.82), (cx + w * 0.62, cy - h / 4)], fill=DARK_RED, outline=DARK_GOLD)
    draw.rectangle((cx - 17 * scale, cy + 5 * scale, cx + 17 * scale, cy + h / 2), fill=(43, 35, 29, 255), outline=LIGHT_GOLD, width=max(3, int(4 * scale)))
    draw.rectangle((cx - 48 * scale, cy - 4 * scale, cx - 23 * scale, cy + 22 * scale), fill=(173, 188, 177, 255), outline=DARK_GOLD, width=max(3, int(4 * scale)))
    draw.rectangle((cx + 23 * scale, cy - 4 * scale, cx + 48 * scale, cy + 22 * scale), fill=(173, 188, 177, 255), outline=DARK_GOLD, width=max(3, int(4 * scale)))
    add_relief_layer(layer, object_layer, depth=4, shadow_blur=3, shadow_offset=(4, 6), shadow_opacity=150)


def draw_factory(layer: Image.Image, base_y: int = 278, scale: float = 1.0) -> None:
    object_layer = Image.new("RGBA", layer.size, TRANSPARENT)
    draw = ImageDraw.Draw(object_layer)
    x1 = 78
    x2 = 322
    draw.rectangle((x1, base_y - 78 * scale, x2, base_y), fill=(84, 76, 68, 255), outline=DARK_STEEL, width=max(4, int(7 * scale)))
    saw = [(x1, base_y - 78 * scale)]
    for index in range(5):
        x = x1 + index * (x2 - x1) / 5
        saw.extend([(x + 25 * scale, base_y - 122 * scale), (x + 50 * scale, base_y - 78 * scale)])
    saw.append((x2, base_y))
    draw.line(saw, fill=LIGHT_STEEL, width=max(4, int(7 * scale)), joint="curve")
    for x in (118, 171, 224, 277):
        draw.rectangle((x - 13, base_y - 52 * scale, x + 13, base_y - 20 * scale), fill=(183, 167, 115, 255), outline=DARK_GOLD, width=4)
    draw.rectangle((274, base_y - 172 * scale, 304, base_y - 78 * scale), fill=(71, 66, 60, 255), outline=DARK_STEEL, width=6)
    add_relief_layer(layer, object_layer, depth=5, shadow_blur=3, shadow_offset=(4, 7), shadow_opacity=165)


def draw_book(layer: Image.Image, center: tuple[int, int], scale: float = 1.0) -> None:
    cx, cy = center
    object_layer = Image.new("RGBA", layer.size, TRANSPARENT)
    draw = ImageDraw.Draw(object_layer)
    w = 92 * scale
    h = 72 * scale
    left = [(cx, cy + h / 2), (cx - w, cy + h * 0.25), (cx - w * 0.88, cy - h / 2), (cx - 8, cy - h * 0.32)]
    right = [(cx, cy + h / 2), (cx + w, cy + h * 0.25), (cx + w * 0.88, cy - h / 2), (cx + 8, cy - h * 0.32)]
    draw.polygon(left, fill=PAPER, outline=DARK_PAPER)
    draw.polygon(right, fill=PAPER, outline=DARK_PAPER)
    draw.line((cx, cy - h * 0.3, cx, cy + h / 2), fill=DARK_PAPER, width=max(4, int(6 * scale)))
    for side in (-1, 1):
        for index in range(3):
            y = cy - h * 0.13 + index * h * 0.18
            draw.line((cx + side * 18 * scale, y, cx + side * 72 * scale, y + side * 2), fill=INK, width=max(3, int(4 * scale)))
    add_relief_layer(layer, object_layer, depth=4, shadow_blur=3, shadow_offset=(4, 6), shadow_opacity=150)


def draw_telegraph_and_tracks(layer: Image.Image) -> None:
    object_layer = Image.new("RGBA", layer.size, TRANSPARENT)
    draw = ImageDraw.Draw(object_layer)
    horizon = 138
    draw.line((167, 304, 193, horizon), fill=LIGHT_STEEL, width=9)
    draw.line((233, 304, 207, horizon), fill=LIGHT_STEEL, width=9)
    for index in range(8):
        t = index / 8
        y = int(298 - t * 148)
        half = int(38 * (1 - t) + 8)
        draw.line((200 - half, y, 200 + half, y), fill=(121, 79, 43, 255), width=max(3, int(9 * (1 - t) + 3)))
    for side, x in ((-1, 96), (1, 304)):
        draw.line((x, 302, x + side * 8, 118), fill=DARK_STEEL, width=8)
        for y in (155, 207, 259):
            pole_x = int(x + side * (302 - y) * 0.045)
            draw.line((pole_x - 25, y, pole_x + 25, y), fill=DARK_STEEL, width=7)
            draw.ellipse((pole_x - 30, y - 8, pole_x - 19, y + 3), fill=LIGHT_STEEL)
            draw.ellipse((pole_x + 19, y - 8, pole_x + 30, y + 3), fill=LIGHT_STEEL)
    draw.line((71, 148, 329, 148), fill=(63, 55, 47, 255), width=4)
    draw.line((68, 202, 332, 202), fill=(63, 55, 47, 255), width=4)
    add_relief_layer(layer, object_layer, depth=4, shadow_blur=3, shadow_offset=(4, 6), shadow_opacity=150)


def draw_flag_and_kremlin(layer: Image.Image) -> None:
    object_layer = Image.new("RGBA", layer.size, TRANSPARENT)
    draw = ImageDraw.Draw(object_layer)
    draw.rectangle((103, 207, 302, 294), fill=(75, 65, 57, 255), outline=DARK_STEEL, width=6)
    towers = [(121, 207, 38), (200, 190, 52), (278, 210, 36)]
    for x, y, width in towers:
        draw.rectangle((x - width / 2, y - 95, x + width / 2, 294), fill=(97, 79, 62, 255), outline=DARK_STEEL, width=6)
        draw.polygon([(x - width * 0.65, y - 95), (x, y - 145), (x + width * 0.65, y - 95)], fill=(70, 47, 43, 255), outline=DARK_GOLD)
        draw_star(object_layer, (x, int(y - 151)), 13, fill=LIGHT_GOLD)
    draw.line((120, 72, 120, 250), fill=LIGHT_STEEL, width=9)
    draw.polygon([(121, 76), (310, 99), (255, 166), (121, 139)], fill=BRIGHT_RED, outline=DARK_RED)
    draw_star(object_layer, (194, 116), 25, fill=LIGHT_GOLD)
    add_relief_layer(layer, object_layer, depth=5, shadow_blur=3, shadow_offset=(4, 7), shadow_opacity=165)


def icon_layer() -> Image.Image:
    return Image.new("RGBA", (WORK_SIZE, WORK_SIZE), TRANSPARENT)


def load_source_backplate(source_dir: Path, filename: str, theme: str, icon_id: str) -> Image.Image | None:
    path = source_dir / filename
    if not path.exists():
        return None

    source = Image.open(path).convert("RGBA").resize((WORK_SIZE, WORK_SIZE), Image.Resampling.LANCZOS)
    alpha = source.getchannel("A")
    rgb = source.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.18)
    rgb = ImageEnhance.Color(rgb).enhance(0.98)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.88)

    wash = ICON_PLATE_PALETTES.get(icon_id, BURGUNDY_PLATE)[0]
    wash_layer = Image.new("RGB", rgb.size, wash)
    rgb = Image.blend(rgb, ImageChops.multiply(rgb, wash_layer), 0.045)

    backplate = rgb.convert("RGBA")
    backplate.putalpha(alpha.point(lambda value: value * 238 // 255))
    return backplate


SOURCE_FOREGROUND_SPECS = {
    "RUS_kamenev_no_permanent_creditor": (
        "RUS_oppression.png",
        (17, 7, 82, 67),
        (242, 210),
        (200, 158),
    ),
    "RUS_kamenev_one_party_card": (
        "generic_political_purge.png",
        (22, 3, 68, 64),
        (210, 220),
        (200, 157),
    ),
    "RUS_kamenev_majority_rule": (
        "RUS_union_of_peasants_and_workers.png",
        (21, 16, 81, 64),
        (258, 206),
        (200, 150),
    ),
    "RUS_kamenev_psr_rebuild_central_committee": (
        "RUS_rebuild_eser_party.png",
        (23, 10, 78, 66),
        (220, 220),
        (200, 157),
    ),
    "RUS_kamenev_psr_preserve_land_committees": (
        "RUS_values_of_february.png",
        (20, 0, 88, 70),
        (220, 220),
        (200, 158),
    ),
    "RUS_kamenev_psr_claim_internal_affairs": (
        "integrate_workers_militia.png",
        (15, 0, 76, 63),
        (222, 218),
        (200, 157),
    ),
    "RUS_kamenev_psr_defend_revolutionary_democracy": (
        "card_tricks.png",
        (16, 5, 74, 62),
        (222, 216),
        (200, 155),
    ),
    "RUS_kamenev_psr_land_socialisation_bill": (
        "generic_land_reform.png",
        (20, 4, 76, 68),
        (210, 218),
        (200, 158),
    ),
    "RUS_kamenev_psr_peasant_congress": (
        "generic_council.png",
        (23, 15, 78, 59),
        (250, 196),
        (200, 148),
    ),
    "RUS_kamenev_psr_final_party_congress": (
        "RUS_maximalist.png",
        (19, 0, 81, 68),
        (210, 220),
        (200, 157),
    ),
    "RUS_kamenev_psr_cooperatives_fair_grain_prices": (
        "BEL_Cooperative.png",
        (21, 8, 75, 66),
        (208, 220),
        (200, 157),
    ),
    "RUS_kamenev_psr_local_self_government": (
        "generic_syndicalist_council.png",
        (20, 2, 80, 70),
        (210, 220),
        (200, 158),
    ),
    "RUS_kamenev_psr_agrarian_socialism": (
        "agrarian_socialism.png",
        (15, 1, 79, 71),
        (212, 220),
        (200, 158),
    ),
    "RUS_kamenev_bol_register_returning_members": (
        "NOR_passport_convention.png",
        (21, 10, 69, 62),
        (208, 220),
        (200, 158),
    ),
    "RUS_kamenev_bol_restore_pravda": (
        "generic_seize_press.png",
        (25, 0, 71, 72),
        (180, 224),
        (200, 159),
    ),
    "RUS_kamenev_bol_restore_central_bureau": (
        "generic_secret_documents.png",
        (19, 10, 81, 68),
        (226, 212),
        (200, 157),
    ),
    "RUS_kamenev_bol_unify_planning_apparatus": (
        "commune_politics.png",
        (23, 0, 71, 68),
        (180, 220),
        (200, 158),
    ),
    "RUS_kamenev_bol_rebuild_factory_cells": (
        "generic_farmer_and_worker.png",
        (18, 1, 82, 72),
        (216, 220),
        (200, 158),
    ),
    "RUS_kamenev_bol_railway_telegraph_bureau": (
        "generic_seize_railway.png",
        (14, 0, 85, 68),
        (230, 218),
        (200, 158),
    ),
    "RUS_kamenev_bol_win_vst_majority": (
        "generic_farmer.png",
        (21, 0, 73, 82),
        (180, 226),
        (200, 160),
    ),
    "RUS_kamenev_bol_undissolved_central_committee": (
        "RUS_red_flag_over_kremlin.png",
        (20, 7, 82, 78),
        (214, 220),
        (200, 158),
    ),
}

SOURCE_FOREGROUND_ON_TOP = set(SOURCE_FOREGROUND_SPECS) - {
    "RUS_kamenev_majority_rule",
    "RUS_kamenev_psr_peasant_congress",
}

PAINTER_OPACITY = {
    "RUS_kamenev_no_permanent_creditor": 165,
    "RUS_kamenev_one_party_card": 145,
    "RUS_kamenev_psr_rebuild_central_committee": 155,
    "RUS_kamenev_psr_preserve_land_committees": 150,
    "RUS_kamenev_psr_claim_internal_affairs": 155,
    "RUS_kamenev_psr_defend_revolutionary_democracy": 100,
    "RUS_kamenev_psr_land_socialisation_bill": 145,
    "RUS_kamenev_psr_final_party_congress": 145,
    "RUS_kamenev_psr_cooperatives_fair_grain_prices": 140,
    "RUS_kamenev_psr_local_self_government": 130,
    "RUS_kamenev_psr_agrarian_socialism": 110,
    "RUS_kamenev_bol_register_returning_members": 140,
    "RUS_kamenev_bol_restore_pravda": 95,
    "RUS_kamenev_bol_restore_central_bureau": 105,
    "RUS_kamenev_bol_unify_planning_apparatus": 145,
    "RUS_kamenev_bol_rebuild_factory_cells": 140,
    "RUS_kamenev_bol_railway_telegraph_bureau": 140,
    "RUS_kamenev_bol_win_vst_majority": 150,
    "RUS_kamenev_bol_undissolved_central_committee": 100,
}


def add_source_foreground(canvas: Image.Image, source_dir: Path, icon_id: str, clip: Image.Image) -> None:
    spec = SOURCE_FOREGROUND_SPECS.get(icon_id)
    if spec is None:
        return

    filename, crop_box, max_size, center = spec
    path = source_dir / filename
    if not path.exists():
        return

    source = Image.open(path).convert("RGBA").crop(crop_box)
    bbox = source.getchannel("A").getbbox()
    if bbox:
        source = source.crop(bbox)
    scale = min(max_size[0] / source.width, max_size[1] / source.height)
    source = source.resize(
        (max(1, int(source.width * scale)), max(1, int(source.height * scale))),
        Image.Resampling.LANCZOS,
    )
    feather = Image.new("L", source.size, 0)
    feather_draw = ImageDraw.Draw(feather)
    inset = 5
    feather_draw.rounded_rectangle(
        (inset, inset, source.width - inset - 1, source.height - inset - 1),
        radius=max(12, min(source.size) // 4),
        fill=255,
    )
    feather = feather.filter(ImageFilter.GaussianBlur(5))
    source.putalpha(ImageChops.multiply(source.getchannel("A"), feather))
    approved_subject = icon_id in {
        "RUS_kamenev_majority_rule",
        "RUS_kamenev_psr_peasant_congress",
    }
    rgb = ImageEnhance.Contrast(source.convert("RGB")).enhance(1.12 if approved_subject else 1.18)
    rgb = ImageEnhance.Color(rgb).enhance(0.9 if approved_subject else 1.12)
    if not approved_subject:
        rgb = ImageEnhance.Brightness(rgb).enhance(1.03)
    subject = rgb.convert("RGBA")
    subject.putalpha(source.getchannel("A"))

    positioned = Image.new("RGBA", canvas.size, TRANSPARENT)
    positioned.alpha_composite(subject, (center[0] - subject.width // 2, center[1] - subject.height // 2))
    positioned.putalpha(ImageChops.multiply(positioned.getchannel("A"), clip))
    add_relief_layer(
        canvas,
        positioned,
        depth=5,
        shadow_blur=3,
        shadow_offset=(5, 7),
        shadow_opacity=175,
        internal_relief=False,
    )


def apply_source_surface(canvas: Image.Image, source_dir: Path, filename: str) -> Image.Image:
    path = source_dir / filename
    if not path.exists():
        return canvas

    source = Image.open(path).convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox:
        source = source.crop(bbox)
    source = ImageOps.fit(source, canvas.size, method=Image.Resampling.LANCZOS)

    alpha = canvas.getchannel("A")
    base_rgb = canvas.convert("RGB")
    source_rgb = source.convert("RGB")
    source_gray = ImageOps.autocontrast(ImageOps.grayscale(source)).filter(ImageFilter.GaussianBlur(0.55))
    relief = ImageOps.colorize(source_gray, (102, 84, 64), (255, 239, 197))
    multiplied = ImageChops.multiply(base_rgb, relief)
    surfaced = Image.blend(base_rgb, multiplied, 0.12)
    surfaced = Image.blend(surfaced, source_rgb, 0.06)
    result = surfaced.convert("RGBA")
    result.putalpha(alpha)
    return result


def build_icon(icon_id: str, theme: str, source_dir: Path, source: str, painter) -> Image.Image:
    canvas = Image.new("RGBA", (WORK_SIZE, WORK_SIZE), TRANSPARENT)
    source_backplate = load_source_backplate(source_dir, source, theme, icon_id)
    if source_backplate is not None:
        add_relief_layer(
            canvas,
            source_backplate,
            depth=5,
            shadow_blur=6,
            shadow_offset=(8, 11),
            shadow_opacity=180,
            internal_relief=False,
        )

    medal, clip = build_base(theme, icon_id)
    canvas.alpha_composite(medal)
    add_source_motif(canvas, clip, source_dir, source)
    if icon_id not in SOURCE_FOREGROUND_ON_TOP:
        add_source_foreground(canvas, source_dir, icon_id, clip)
    layer = icon_layer()
    painter(layer)
    painter_opacity = PAINTER_OPACITY.get(icon_id, 255)
    if painter_opacity < 255:
        layer.putalpha(layer.getchannel("A").point(lambda value: value * painter_opacity // 255))
    add_relief_layer(
        canvas,
        layer,
        depth=9,
        shadow_blur=5,
        shadow_offset=(9, 12),
        shadow_opacity=220,
    )
    if icon_id in SOURCE_FOREGROUND_ON_TOP:
        add_source_foreground(canvas, source_dir, icon_id, clip)
    canvas = apply_source_surface(canvas, source_dir, source)
    return finish_icon(canvas, icon_id)


def finish_icon(canvas: Image.Image, seed_text: str) -> Image.Image:
    seed = sum((index + 1) * ord(char) for index, char in enumerate(seed_text))
    rng = random.Random(seed)
    alpha = canvas.getchannel("A")

    # Give the clean vector construction the uneven surface of a painted,
    # handled interwar medal before the final game-size downscale.
    coarse_noise = Image.effect_noise(canvas.size, 46).filter(ImageFilter.GaussianBlur(1.15))
    fine_noise = Image.effect_noise(canvas.size, 18).filter(ImageFilter.GaussianBlur(0.35))
    patina_mask = coarse_noise.point(lambda value: max(0, (112 - value) * 2))
    patina_mask = ImageChops.multiply(alpha, patina_mask)
    patina = Image.new("RGBA", canvas.size, (35, 52, 39, 0))
    patina.putalpha(patina_mask.point(lambda value: value * 38 // 255))
    canvas.alpha_composite(patina)

    dust_mask = fine_noise.point(lambda value: abs(value - 128))
    dust_mask = ImageChops.multiply(alpha, dust_mask)
    dust = Image.new("RGBA", canvas.size, (224, 194, 130, 0))
    dust.putalpha(dust_mask.point(lambda value: value * 28 // 255))
    canvas.alpha_composite(dust)

    # Directional relief lighting replaces the flat, evenly-lit badge look.
    light_ramp = Image.linear_gradient("L").resize(canvas.size)
    light_ramp = light_ramp.rotate(38, resample=Image.Resampling.BICUBIC, expand=False)
    highlight_alpha = ImageChops.multiply(alpha, light_ramp.point(lambda value: max(0, value - 118)))
    shadow_alpha = ImageChops.multiply(alpha, ImageOps.invert(light_ramp).point(lambda value: max(0, value - 105)))
    highlight = Image.new("RGBA", canvas.size, (246, 220, 162, 0))
    highlight.putalpha(highlight_alpha.point(lambda value: value * 50 // 255))
    shadow = Image.new("RGBA", canvas.size, (28, 19, 19, 0))
    shadow.putalpha(shadow_alpha.point(lambda value: value * 46 // 255))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(highlight)

    # Catch edges like worn brass while keeping the centre darker and painted.
    inner_alpha = alpha.filter(ImageFilter.MinFilter(9))
    worn_edge = ImageChops.subtract(alpha, inner_alpha)
    edge_light = Image.new("RGBA", canvas.size, (232, 199, 124, 0))
    edge_light.putalpha(worn_edge.point(lambda value: value * 94 // 255))
    canvas.alpha_composite(edge_light)

    scratches = Image.new("RGBA", canvas.size, TRANSPARENT)
    scratch_draw = ImageDraw.Draw(scratches)
    for _ in range(34):
        x = rng.randint(56, 344)
        y = rng.randint(54, 330)
        length = rng.randint(8, 34)
        rise = rng.randint(-5, 5)
        colour = (244, 220, 163, rng.randint(15, 34)) if rng.random() < 0.45 else (28, 23, 21, rng.randint(18, 42))
        scratch_draw.line((x, y, x + length, y + rise), fill=colour, width=rng.choice((1, 1, 2)))
    scratches.putalpha(ImageChops.multiply(scratches.getchannel("A"), alpha))
    canvas.alpha_composite(scratches.filter(ImageFilter.GaussianBlur(0.2)))

    # Internal colour boundaries receive offset light and shade, so the
    # figures, documents and emblems read as layered paint or metal relief.
    colour_edges = ImageOps.grayscale(canvas.convert("RGB")).filter(ImageFilter.FIND_EDGES)
    colour_edges = ImageOps.autocontrast(colour_edges).filter(ImageFilter.GaussianBlur(0.65))
    colour_edges = colour_edges.point(lambda value: 0 if value < 42 else min(255, (value - 42) * 2))
    edge_high = shift_mask(colour_edges, -3, -3)
    edge_low = shift_mask(colour_edges, 4, 4)
    edge_high = ImageChops.multiply(edge_high, alpha)
    edge_low = ImageChops.multiply(edge_low, alpha)
    relief_high = Image.new("RGBA", canvas.size, (248, 224, 170, 0))
    relief_high.putalpha(edge_high.point(lambda value: value * 58 // 255))
    relief_low = Image.new("RGBA", canvas.size, (20, 16, 16, 0))
    relief_low.putalpha(edge_low.point(lambda value: value * 92 // 255))
    canvas.alpha_composite(relief_low)
    canvas.alpha_composite(relief_high)

    rgb = Image.new("RGB", canvas.size, (0, 0, 0))
    rgb.paste(canvas.convert("RGB"), mask=alpha)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.19)
    rgb = ImageEnhance.Color(rgb).enhance(0.98)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.97)
    graded = rgb.convert("RGBA")
    graded.putalpha(alpha)
    graded = graded.filter(ImageFilter.GaussianBlur(0.18))
    graded = graded.filter(ImageFilter.UnsharpMask(radius=1.3, percent=48, threshold=4))
    final = graded.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)
    final = final.filter(ImageFilter.UnsharpMask(radius=0.6, percent=34, threshold=3))

    art_size = round(OUTPUT_SIZE * FINAL_ART_SCALE)
    scaled = final.resize((art_size, art_size), Image.Resampling.LANCZOS)
    output = Image.new("RGBA", (OUTPUT_SIZE, OUTPUT_SIZE), TRANSPARENT)
    inset = (OUTPUT_SIZE - art_size) // 2
    output.alpha_composite(scaled, (inset, inset))
    return output


def paint_national_economic_line(layer: Image.Image) -> None:
    draw_document(layer, (79, 72, 218, 247), angle=-10, seal=False)
    draw_factory(layer, base_y=292, scale=0.74)
    draw_star(layer, (252, 116), 34, fill=LIGHT_GOLD)
    draw = ImageDraw.Draw(layer)
    junctions = [(128, 246), (204, 258), (286, 240)]
    for endpoint in junctions:
        draw.line(((244, 143), endpoint), fill=DARK_GOLD, width=12)
        draw.line(((244, 143), endpoint), fill=LIGHT_GOLD, width=5)
        draw.ellipse(
            (endpoint[0] - 11, endpoint[1] - 11, endpoint[0] + 11, endpoint[1] + 11),
            fill=RED,
            outline=LIGHT_GOLD,
            width=4,
        )


def paint_maximalist_talks(layer: Image.Image) -> None:
    draw_document(layer, (94, 82, 219, 246), angle=-9)
    draw_wheat_stalk(layer, (279, 181), 137, 16)
    draw_handshake(layer, (205, 252), 0.88, RED, GREEN)


def paint_curb_srs(layer: Image.Image) -> None:
    draw_rose(layer, (199, 171), 53)
    chain = ImageDraw.Draw(layer)
    for index in range(5):
        x = 105 + index * 45
        chain.ellipse((x, 205 + (index % 2) * 7, x + 58, 238 + (index % 2) * 7), outline=LIGHT_STEEL, width=10)
    brace = rotated_rounded_rect((255, 34), 13, (105, 103, 96, 255), DARK_STEEL, 6, -35)
    paste_center(layer, brace, (205, 191))
    for point in ((135, 240), (274, 142)):
        ImageDraw.Draw(layer).ellipse((point[0] - 10, point[1] - 10, point[0] + 10, point[1] + 10), fill=LIGHT_GOLD, outline=DARK_GOLD, width=4)


def paint_purity(layer: Image.Image) -> None:
    draw_card(layer, (154, 188), (124, 168), -13, (81, 77, 72, 255), "gear")
    draw_card(layer, (248, 189), (124, 168), 13, (80, 74, 71, 255), "rose")
    draw_card(layer, (201, 177), (139, 187), 0, RED, "star")
    draw_star(layer, (201, 277), 31, fill=LIGHT_GOLD)


def paint_more_friends(layer: Image.Image) -> None:
    draw_handshake(layer, (201, 256), 0.78, RED, GREEN)


def paint_kamkov_talks(layer: Image.Image) -> None:
    draw_document(layer, (85, 105, 191, 246), angle=-12, seal=False)
    draw_document(layer, (209, 105, 315, 246), angle=12, seal=False)
    draw_rose(layer, (143, 174), 28)
    draw_star(layer, (257, 174), 31, fill=LIGHT_GOLD)
    draw_handshake(layer, (200, 261), 0.72, (113, 40, 47, 255), GREEN)


def paint_psr_rebuild(layer: Image.Image) -> None:
    draw_rose(layer, (200, 172), 59)
    draw = ImageDraw.Draw(layer)
    crack = [(190, 111), (210, 142), (188, 165), (211, 191), (190, 230)]
    draw.line(crack, fill=(35, 31, 29, 255), width=13, joint="curve")
    for y in (138, 174, 207):
        draw.line((177, y, 223, y - 5), fill=LIGHT_GOLD, width=8)
        draw.ellipse((171, y - 6, 184, y + 7), fill=DARK_GOLD)
        draw.ellipse((216, y - 11, 229, y + 2), fill=DARK_GOLD)
    draw_wheat_stalk(layer, (129, 240), 125, -18)
    draw_wheat_stalk(layer, (271, 240), 125, 18)


def paint_psr_right_union(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    draw.line((132, 89, 176, 251), fill=LIGHT_STEEL, width=9)
    draw.line((268, 89, 224, 251), fill=LIGHT_STEEL, width=9)
    draw.polygon([(136, 91), (222, 114), (171, 174), (145, 157)], fill=RED, outline=DARK_RED)
    draw.polygon([(264, 91), (178, 114), (229, 174), (255, 157)], fill=(116, 81, 62, 255), outline=DARK_GOLD)
    draw_handshake(layer, (201, 247), 0.78, RED, (116, 81, 62, 255))


def paint_psr_militia(layer: Image.Image) -> None:
    draw_wheat_stalk(layer, (138, 218), 152, -20)
    draw_wheat_stalk(layer, (263, 218), 152, 20)
    draw_rifle(layer, (103, 260), (292, 99))
    shield = Image.new("RGBA", (132, 148), TRANSPARENT)
    sd = ImageDraw.Draw(shield)
    sd.polygon([(66, 5), (123, 27), (111, 102), (66, 141), (21, 102), (9, 27)], fill=(69, 89, 61, 255), outline=DARK_GOLD)
    draw_star(shield, (66, 72), 31, fill=LIGHT_GOLD)
    paste_center(layer, shield, (201, 198))


def paint_psr_no_dual_cards(layer: Image.Image) -> None:
    draw_card(layer, (157, 181), (126, 169), -13, GREEN, "rose")
    draw_card(layer, (244, 181), (126, 169), 13, RED, "star")
    draw = ImageDraw.Draw(layer)
    draw.line((112, 275, 292, 88), fill=LIGHT_STEEL, width=18)
    draw.line((112, 275, 292, 88), fill=DARK_RED, width=8)


def paint_psr_land_bill(layer: Image.Image) -> None:
    draw_document(layer, (108, 76, 252, 249), angle=-8)
    draw_wheat_stalk(layer, (281, 191), 143, 13)
    draw = ImageDraw.Draw(layer)
    for index in range(5):
        y = 239 + index * 13
        draw.arc((80 - index * 7, y - 31, 323 + index * 7, y + 23), 188, 352, fill=(135, 101, 56, 255), width=6)


def paint_psr_peasant_rep(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    draw.polygon([(113, 219), (287, 219), (309, 290), (91, 290)], fill=(94, 72, 54, 255), outline=DARK_GOLD)
    draw_star(layer, (200, 254), 25, fill=LIGHT_GOLD)
    draw_wheat_stalk(layer, (100, 234), 108, -24)
    draw_wheat_stalk(layer, (300, 234), 108, 24)


def paint_psr_placate_maximalists(layer: Image.Image) -> None:
    draw_rose(layer, (132, 158), 40)
    draw_star(layer, (268, 158), 49, fill=LIGHT_GOLD)
    draw_handshake(layer, (200, 248), 0.78, GREEN, RED)
    draw = ImageDraw.Draw(layer)
    draw.arc((113, 112, 287, 282), 208, 332, fill=LIGHT_GOLD, width=8)


def paint_psr_coops(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    draw.ellipse((102, 112, 224, 234), fill=(112, 91, 59, 255), outline=DARK_GOLD, width=8)
    draw.ellipse((176, 111, 298, 233), fill=GREEN, outline=DARK_GOLD, width=8)
    draw.ellipse((156, 142, 244, 230), fill=(83, 58, 42, 255), outline=LIGHT_GOLD, width=7)
    draw_wheat_stalk(layer, (142, 241), 122, -14)
    draw_wheat_stalk(layer, (260, 241), 122, 14)
    draw.rounded_rectangle((127, 238, 273, 292), 17, fill=(130, 84, 49, 255), outline=DARK_GOLD, width=7)
    draw.line((148, 263, 252, 263), fill=LIGHT_GOLD, width=6)


def paint_psr_rural_charter(layer: Image.Image) -> None:
    draw_document(layer, (92, 81, 226, 252), angle=-10)
    draw_house(layer, (260, 206), 0.72)
    draw_star(layer, (260, 123), 28, fill=LIGHT_GOLD)


def paint_psr_agrarian(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    draw.ellipse((143, 112, 257, 226), fill=(204, 116, 44, 255), outline=DARK_GOLD, width=7)
    for angle in range(200, 341, 20):
        rad = math.radians(angle)
        draw.line((200, 169, 200 + math.cos(rad) * 112, 169 + math.sin(rad) * 112), fill=LIGHT_GOLD, width=6)
    draw.rectangle((75, 178, 325, 292), fill=(50, 72, 48, 255))
    for index in range(5):
        draw.arc((77 - index * 6, 188 + index * 14, 323 + index * 6, 294 + index * 14), 186, 354, fill=(161, 119, 58, 255), width=7)
    draw_wheat_stalk(layer, (118, 239), 150, -18)
    draw_wheat_stalk(layer, (282, 239), 150, 18)
    draw_star(layer, (200, 140), 28, fill=LIGHT_GOLD)


def paint_bol_registry(layer: Image.Image) -> None:
    draw_book(layer, (197, 205), 0.82)
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle((106, 98, 185, 174), 10, fill=(118, 45, 48, 255), outline=DARK_GOLD, width=6)
    draw.ellipse((126, 112, 164, 150), fill=LIGHT_GOLD, outline=DARK_GOLD, width=4)
    draw.line((230, 103, 295, 103), fill=LIGHT_STEEL, width=10)
    draw.polygon([(294, 103), (265, 83), (265, 123)], fill=LIGHT_STEEL, outline=DARK_STEEL)
    draw_star(layer, (201, 248), 24, fill=LIGHT_GOLD)


def paint_bol_pravda(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle((91, 88, 309, 277), 12, fill=PAPER, outline=DARK_PAPER, width=8)
    draw.rectangle((105, 102, 295, 151), fill=RED, outline=DARK_RED, width=5)
    title = "\u041f\u0420\u0410\u0412\u0414\u0410"
    font = get_font(30, bold=True)
    bbox = draw.textbbox((0, 0), title, font=font)
    draw.text((200 - (bbox[2] - bbox[0]) / 2, 108), title, font=font, fill=LIGHT_GOLD, stroke_width=1, stroke_fill=DARK_RED)
    draw.rectangle((112, 167, 189, 245), fill=(91, 74, 62, 255), outline=DARK_STEEL, width=5)
    draw_star(layer, (150, 205), 25, fill=LIGHT_GOLD)
    for y in (173, 191, 209, 227, 245):
        draw.line((205, y, 283, y), fill=INK, width=5)
    draw.line((213, 284, 302, 284), fill=LIGHT_STEEL, width=12)
    draw.ellipse((205, 267, 237, 300), fill=DARK_STEEL, outline=LIGHT_STEEL, width=5)
    draw.ellipse((276, 267, 308, 300), fill=DARK_STEEL, outline=LIGHT_STEEL, width=5)


def paint_bol_two_cards(layer: Image.Image) -> None:
    draw_card(layer, (155, 185), (138, 184), -14, (107, 37, 43, 255), "gear")
    draw_card(layer, (245, 185), (138, 184), 14, RED, "star")
    draw = ImageDraw.Draw(layer)
    draw.ellipse((176, 243, 224, 291), fill=LIGHT_GOLD, outline=DARK_GOLD, width=6)
    draw.line((185, 267, 215, 267), fill=DARK_RED, width=8)


def paint_bol_school(layer: Image.Image) -> None:
    draw_book(layer, (200, 233), 0.86)
    draw = ImageDraw.Draw(layer)
    draw.polygon([(190, 171), (211, 91), (232, 172)], fill=BRIGHT_RED, outline=DARK_RED)
    draw.ellipse((183, 156, 239, 213), fill=(214, 111, 39, 255), outline=DARK_GOLD, width=6)
    draw_star(layer, (211, 130), 23, fill=LIGHT_GOLD)


def paint_bol_factory_cells(layer: Image.Image) -> None:
    draw_factory(layer, base_y=282, scale=0.82)
    draw = ImageDraw.Draw(layer)
    nodes = [(118, 121), (199, 91), (282, 121), (151, 166), (247, 166)]
    for first, second in ((0, 1), (1, 2), (0, 3), (1, 3), (1, 4), (2, 4), (3, 4)):
        draw.line((nodes[first], nodes[second]), fill=LIGHT_GOLD, width=6)
    for x, y in nodes:
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=RED, outline=LIGHT_GOLD, width=5)


def paint_bol_rail_telegraph(layer: Image.Image) -> None:
    draw_telegraph_and_tracks(layer)
    draw = ImageDraw.Draw(layer)
    draw.ellipse((180, 109, 220, 149), fill=BRIGHT_RED, outline=DARK_GOLD, width=6)
    draw_star(layer, (200, 129), 15, fill=LIGHT_GOLD)


def paint_bol_maximalist_liaison(layer: Image.Image) -> None:
    draw_wheat_stalk(layer, (132, 191), 145, -13)
    draw_star(layer, (270, 151), 55, fill=LIGHT_GOLD)
    draw_handshake(layer, (204, 249), 0.73, (111, 74, 51, 255), RED)
    draw = ImageDraw.Draw(layer)
    draw.line((148, 105, 246, 105), fill=LIGHT_STEEL, width=6)
    for x in (148, 180, 213, 246):
        draw.ellipse((x - 8, 97, x + 8, 113), fill=RED, outline=DARK_GOLD, width=3)


def paint_bol_red_flag(layer: Image.Image) -> None:
    draw_flag_and_kremlin(layer)


ICON_SPECS = [
    ("RUS_kamenev_national_economic_line", "main", "state_economy.png", paint_national_economic_line),
    ("RUS_kamenev_no_permanent_creditor", "main", "RUS_oppression.png", paint_curb_srs),
    ("RUS_kamenev_one_party_card", "main", "generic_political_purge.png", paint_purity),
    ("RUS_kamenev_majority_rule", "main", "RUS_coalition_of_idealists.png", paint_more_friends),
    ("RUS_kamenev_psr_rebuild_central_committee", "psr", "RUS_rebuild_eser_party.png", paint_psr_rebuild),
    ("RUS_kamenev_psr_preserve_land_committees", "psr", "RUS_values_of_february.png", paint_psr_right_union),
    ("RUS_kamenev_psr_claim_internal_affairs", "psr", "integrate_workers_militia.png", paint_psr_militia),
    ("RUS_kamenev_psr_defend_revolutionary_democracy", "psr", "card_tricks.png", paint_psr_no_dual_cards),
    ("RUS_kamenev_psr_land_socialisation_bill", "psr", "generic_land_reform.png", paint_psr_land_bill),
    ("RUS_kamenev_psr_peasant_congress", "psr", "generic_council.png", paint_psr_peasant_rep),
    ("RUS_kamenev_psr_final_party_congress", "psr", "RUS_maximalist.png", paint_psr_placate_maximalists),
    ("RUS_kamenev_psr_cooperatives_fair_grain_prices", "psr", "BEL_Cooperative.png", paint_psr_coops),
    ("RUS_kamenev_psr_local_self_government", "psr", "generic_syndicalist_council.png", paint_psr_rural_charter),
    ("RUS_kamenev_psr_agrarian_socialism", "psr", "agrarian_socialism.png", paint_psr_agrarian),
    ("RUS_kamenev_bol_register_returning_members", "bol", "NOR_passport_convention.png", paint_bol_registry),
    ("RUS_kamenev_bol_restore_pravda", "bol", "generic_seize_press.png", paint_bol_pravda),
    ("RUS_kamenev_bol_restore_central_bureau", "bol", "generic_secret_documents.png", paint_bol_two_cards),
    ("RUS_kamenev_bol_unify_planning_apparatus", "bol", "commune_politics.png", paint_bol_school),
    ("RUS_kamenev_bol_rebuild_factory_cells", "bol", "generic_farmer_and_worker.png", paint_bol_factory_cells),
    ("RUS_kamenev_bol_railway_telegraph_bureau", "bol", "generic_seize_railway.png", paint_bol_rail_telegraph),
    ("RUS_kamenev_bol_win_vst_majority", "bol", "generic_farmer.png", paint_bol_maximalist_liaison),
    ("RUS_kamenev_bol_undissolved_central_committee", "bol", "RUS_red_flag_over_kremlin.png", paint_bol_red_flag),
]


def create_preview(images: list[tuple[str, Image.Image]], path: Path) -> None:
    columns = 5
    cell_width = 184
    cell_height = 142
    rows = math.ceil(len(images) / columns)
    preview = Image.new("RGB", (columns * cell_width, rows * cell_height), (38, 38, 38))
    draw = ImageDraw.Draw(preview)
    font = get_font(13)
    for index, (name, image) in enumerate(images):
        column = index % columns
        row = index // columns
        x = column * cell_width + 42
        y = row * cell_height + 4
        checker = Image.new("RGB", (100, 100), (224, 216, 192))
        preview.paste(checker, (x, y))
        preview.paste(image.convert("RGB"), (x, y), image.getchannel("A"))
        label = name.replace("RUS_kamenev_", "")
        if len(label) > 24:
            label = label[:23] + "..."
        draw.text((column * cell_width + 6, row * cell_height + 109), label, font=font, fill=(242, 242, 242))
    path.parent.mkdir(parents=True, exist_ok=True)
    preview.save(path)


def create_gfx_file(mod_root: Path) -> Path:
    lines = ["spriteTypes = {", ""]
    for icon_id, _, _, _ in ICON_SPECS:
        texture = f"gfx/interface/goals/RUS_kamenev_politics/{icon_id}.png"
        sprite = f"GFX_goal_{icon_id}"
        lines.extend(
            [
                "\tSpriteType = {",
                f'\t\tname = "{sprite}"',
                f'\t\ttexturefile = "{texture}"',
                "\t}",
                "",
                "\tSpriteType = {",
                f'\t\tname = "{sprite}_shine"',
                f'\t\ttexturefile = "{texture}"',
                '\t\teffectFile = "gfx/FX/buttonstate.lua"',
                "\t\tanimation = {",
                f'\t\t\tanimationmaskfile = "{texture}"',
                '\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"',
                "\t\t\tanimationrotation = -90.0",
                "\t\t\tanimationlooping = no",
                "\t\t\tanimationtime = 0.75",
                "\t\t\tanimationdelay = 0",
                '\t\t\tanimationblendmode = "add"',
                '\t\t\tanimationtype = "scrolling"',
                "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }",
                "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }",
                "\t\t}",
                "\t\tanimation = {",
                f'\t\t\tanimationmaskfile = "{texture}"',
                '\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"',
                "\t\t\tanimationrotation = 90.0",
                "\t\t\tanimationlooping = no",
                "\t\t\tanimationtime = 0.75",
                "\t\t\tanimationdelay = 0",
                '\t\t\tanimationblendmode = "add"',
                '\t\t\tanimationtype = "scrolling"',
                "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }",
                "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }",
                "\t\t}",
                "\t\tlegacy_lazy_load = no",
                "\t}",
                "",
            ]
        )
    lines.append("}")
    path = mod_root / "interface" / "RUS_stalin_kamenev_focus_icons.gfx"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate custom KR-style focus icons for the Kamenev political branch.")
    parser.add_argument("--kr-root", type=Path, required=True, help="Kaiserreich mod root containing gfx/interface/goals.")
    parser.add_argument("--preview", type=Path, help="Optional contact-sheet output path.")
    args = parser.parse_args()

    mod_root = Path(__file__).resolve().parents[1]
    source_dir = args.kr_root / "gfx" / "interface" / "goals"
    output_dir = mod_root / "gfx" / "interface" / "goals" / "RUS_kamenev_politics"
    output_dir.mkdir(parents=True, exist_ok=True)

    images: list[tuple[str, Image.Image]] = []
    for icon_id, theme, source, painter in ICON_SPECS:
        image = build_icon(icon_id, theme, source_dir, source, painter)
        image.save(output_dir / f"{icon_id}.png")
        images.append((icon_id, image))

    gfx_path = create_gfx_file(mod_root)
    if args.preview:
        create_preview(images, args.preview)

    print(f"Generated {len(images)} icons in {output_dir}")
    print(f"Wrote sprite definitions to {gfx_path}")


if __name__ == "__main__":
    main()
