from __future__ import annotations

from collections import deque
from math import pow
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output/imagegen"
SOURCE = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_generated_1680x944_v17.png"
DEST_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_fitted_100px_v17"
CONTACT = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_fitted_100px_contact_v17.png"
WHITE_CONTACT = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_fitted_100px_white_v17.png"

# Tight full-badge source rectangles measured on the unscaled 1672x941 API output.
SOURCE_BADGES = {
    "fist": (774, 51, 906, 166),
    "press": (555, 207, 682, 321),
    "books": (1003, 207, 1123, 321),
    "cards": (322, 362, 452, 475),
    "train": (779, 364, 902, 479),
    "worker": (555, 524, 682, 639),
    "handshake": (1001, 523, 1132, 639),
    "flag": (777, 686, 904, 800),
}

# Reorder the two pairs that the model placed in the wrong tree nodes.
TARGETS = [
    ("RUS_kamenev_bol_win_vst_majority", "一切权力归苏维埃", "fist"),
    ("RUS_kamenev_bol_restore_pravda", "《真理报》重返俄罗斯", "press"),
    ("RUS_kamenev_bol_undissolved_central_committee", "两张党证", "cards"),
    ("RUS_kamenev_bol_register_returning_members", "开设党校", "books"),
    ("RUS_kamenev_bol_rebuild_factory_cells", "车间里的党小组", "worker"),
    ("RUS_kamenev_bol_railway_telegraph_bureau", "铁路与电报联络局", "train"),
    ("RUS_kamenev_bol_unify_planning_apparatus", "设立最高纲领派联络处", "handshake"),
    ("RUS_kamenev_bol_raise_red_flag", "高举红旗", "flag"),
]


def font(size: int) -> ImageFont.ImageFont:
    for path in (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf")):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def exterior_background_alpha(crop: Image.Image) -> Image.Image:
    """Remove the edge-connected dark tree background while retaining badge interiors."""
    rgb = crop.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()

    # The generated focus-tree background is very dark and low-chroma.
    passable = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y]
            luminance = red * 0.2126 + green * 0.7152 + blue * 0.0722
            chroma = max(red, green, blue) - min(red, green, blue)
            passable[y][x] = luminance < 52 and chroma < 48

    exterior = [[False] * width for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        if passable[0][x]:
            exterior[0][x] = True
            queue.append((x, 0))
        if passable[height - 1][x]:
            exterior[height - 1][x] = True
            queue.append((x, height - 1))
    for y in range(height):
        if passable[y][0] and not exterior[y][0]:
            exterior[y][0] = True
            queue.append((0, y))
        if passable[y][width - 1] and not exterior[y][width - 1]:
            exterior[y][width - 1] = True
            queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height and passable[ny][nx] and not exterior[ny][nx]:
                exterior[ny][nx] = True
                queue.append((nx, ny))

    # Remove corner UI fragments without cutting the rounded badge silhouette.
    cx = (width - 1) / 2
    cy = (height - 1) / 2
    inner = [[False] * width for _ in range(height)]
    candidate = [[False] * width for _ in range(height)]
    retained = [[False] * width for _ in range(height)]
    queue.clear()

    for y in range(height):
        for x in range(width):
            outer_distance = pow((x - cx) / (width * 0.50), 2) + pow((y - cy) / (height * 0.51), 2)
            inner_distance = pow((x - cx) / (width * 0.40), 2) + pow((y - cy) / (height * 0.41), 2)
            inner[y][x] = inner_distance <= 1
            candidate[y][x] = not exterior[y][x] and outer_distance <= 1
            if inner[y][x]:
                retained[y][x] = True
                queue.append((x, y))

    # Keep outer-frame pixels only when they are connected to the solid badge core.
    # This discards isolated focus-tree rulers, guide ticks, and background specks.
    while queue:
        x, y = queue.popleft()
        for nx, ny in (
            (x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
            (x - 1, y),                     (x + 1, y),
            (x - 1, y + 1), (x, y + 1), (x + 1, y + 1),
        ):
            if 0 <= nx < width and 0 <= ny < height and candidate[ny][nx] and not retained[ny][nx]:
                retained[ny][nx] = True
                queue.append((nx, ny))

    alpha = Image.new("L", (width, height), 0)
    alpha_pixels = alpha.load()
    for y in range(height):
        for x in range(width):
            if retained[y][x]:
                alpha_pixels[x, y] = 255

    rgba = crop.convert("RGBA")
    rgba.putalpha(alpha)
    return rgba


def fit_badge(badge: Image.Image) -> Image.Image:
    alpha = badge.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("Badge extraction produced an empty alpha mask")
    badge = badge.crop(bbox)
    scale = min(94 / badge.width, 92 / badge.height)
    size = (max(1, round(badge.width * scale)), max(1, round(badge.height * scale)))
    badge = badge.resize(size, Image.Resampling.LANCZOS)

    result = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    result.alpha_composite(badge, ((100 - badge.width) // 2, (100 - badge.height) // 2))
    return result


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGB")

    fitted: list[tuple[str, Image.Image]] = []
    for focus_id, label, source_key in TARGETS:
        crop = source.crop(SOURCE_BADGES[source_key])
        badge = fit_badge(exterior_background_alpha(crop))
        badge.save(DEST_DIR / f"{focus_id}.png")
        fitted.append((label, badge))

    contact = Image.new("RGBA", (500, 300), (7, 20, 24, 255))
    white_contact = Image.new("RGBA", contact.size, (238, 238, 232, 255))
    label_font = font(12)
    for index, (label, badge) in enumerate(fitted):
        column = index % 4
        row = index // 4
        x = 10 + column * 120
        y = 10 + row * 140
        contact.alpha_composite(badge, (x, y))
        white_contact.alpha_composite(badge, (x, y))
        for sheet, text_fill in ((contact, (235, 235, 225, 255)), (white_contact, (20, 20, 20, 255))):
            draw = ImageDraw.Draw(sheet)
            draw.rectangle((x - 1, y - 1, x + 100, y + 100), outline=(160, 165, 160, 255), width=1)
            box = draw.textbbox((0, 0), label, font=label_font)
            text_width = box[2] - box[0]
            draw.text((x + 50 - text_width // 2, y + 106), label, font=label_font, fill=text_fill)

    contact.convert("RGB").save(CONTACT)
    white_contact.convert("RGB").save(WHITE_CONTACT)
    print(f"fitted icons: {DEST_DIR}")
    print(f"dark preview: {CONTACT}")
    print(f"white preview: {WHITE_CONTACT}")


if __name__ == "__main__":
    main()
