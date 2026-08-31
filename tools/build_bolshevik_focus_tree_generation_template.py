from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output/imagegen"
TMP_DIR = ROOT / "tmp/imagegen"

FRAME_PREVIEW = OUTPUT_DIR / "RUS_bolshevik_political_frame_100px_preview.png"
TREE_PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_focus_tree_template_v4.png"
GUIDE = TMP_DIR / "RUS_kamenev_bolshevik_focus_tree_guide_v4.png"
MASK = TMP_DIR / "RUS_kamenev_bolshevik_focus_tree_mask_v4.png"
FRAME_CANDIDATE_GUIDE = TMP_DIR / "RUS_kamenev_bolshevik_frame_candidates_guide_v5.png"
FRAME_CANDIDATE_MASK = TMP_DIR / "RUS_kamenev_bolshevik_frame_candidates_mask_v5.png"

CANVAS_SIZE = (1254, 1254)
ICON_SIZE = 100
ART_RADIUS = 33

# These positions reproduce the branch shape in the actual focus file. Every
# icon remains exactly 100x100 on the provider-native canvas.
NODES = [
    ("一切权力归苏维埃", 577, 85),
    ("《真理报》重返俄罗斯", 382, 265),
    ("两张党证", 772, 265),
    ("开设党校", 187, 475),
    ("车间里的党小组", 577, 475),
    ("铁路与电报联络局", 382, 685),
    ("设立最高纲领派联络处", 772, 685),
    ("高举红旗", 577, 925),
]

# Edges use indexes into NODES and mirror the focus prerequisites.
EDGES = [
    (0, 1),
    (0, 2),
    (0, 4),
    (1, 3),
    (1, 5),
    (2, 6),
    (4, 7),
    (5, 7),
]


def radial_points(cx: float, cy: float, radii: list[float]) -> list[tuple[float, float]]:
    count = len(radii)
    return [
        (
            cx + radius * math.cos(-math.pi / 2 + 2 * math.pi * index / count),
            cy + radius * math.sin(-math.pi / 2 + 2 * math.pi * index / count),
        )
        for index, radius in enumerate(radii)
    ]


def star_points(cx: float, cy: float, outer: float, inner: float) -> list[tuple[float, float]]:
    radii = [outer if index % 2 == 0 else inner for index in range(10)]
    return radial_points(cx, cy, radii)


def build_frame() -> Image.Image:
    """Draw the reusable frame directly at its final 100x100 pixel size."""
    frame = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))

    # Hard gunmetal gear silhouette: 16 teeth, no agrarian wreath language.
    gear_mask = Image.new("L", frame.size, 0)
    mask_draw = ImageDraw.Draw(gear_mask)
    radii: list[float] = []
    for _ in range(16):
        radii.extend((43, 48, 48, 43))
    mask_draw.polygon(radial_points(50, 51, radii), fill=255)
    mask_draw.ellipse((17, 18, 83, 84), fill=0)

    steel = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    steel_pixels = steel.load()
    for y in range(ICON_SIZE):
        light = max(0, min(255, 112 - y * 3 // 4))
        for x in range(ICON_SIZE):
            if gear_mask.getpixel((x, y)):
                steel_pixels[x, y] = (light, light + 5, light + 5, 255)
    frame = Image.alpha_composite(frame, steel)

    draw = ImageDraw.Draw(frame)
    draw.ellipse((14, 15, 86, 87), outline=(24, 27, 29, 255), width=4)
    draw.ellipse((16, 17, 84, 85), outline=(176, 181, 174, 255), width=2)
    draw.ellipse((18, 19, 82, 83), outline=(47, 51, 53, 255), width=3)
    draw.arc((16, 17, 84, 85), 195, 300, fill=(214, 216, 199, 220), width=1)
    draw.arc((16, 17, 84, 85), 10, 130, fill=(15, 17, 19, 235), width=2)

    # Straight red enamel inserts distinguish the Bolshevik political family.
    for panel in (
        [(10, 62), (18, 58), (23, 76), (15, 80)],
        [(90, 62), (82, 58), (77, 76), (85, 80)],
    ):
        draw.polygon(panel, fill=(42, 23, 24, 255), outline=(18, 19, 20, 255))
        inset = [(x + (1 if x < 50 else -1), y) for x, y in panel]
        draw.polygon(inset, fill=(118, 31, 32, 255), outline=(171, 84, 67, 255))

    # Compact crown emblem; the inner art never needs to redraw this star.
    draw.polygon(star_points(50, 14, 11, 5), fill=(38, 38, 36, 255))
    draw.polygon(star_points(50, 14, 9, 4), fill=(179, 151, 85, 255))
    draw.polygon(star_points(50, 14, 7, 3), fill=(143, 27, 28, 255))
    draw.line((50, 7, 50, 19), fill=(232, 99, 74, 190), width=1)

    for angle in (42, 138, 222, 318):
        x = 50 + 39 * math.cos(math.radians(angle))
        y = 51 + 39 * math.sin(math.radians(angle))
        draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(203, 201, 183, 255))

    return frame


def load_font(size: int) -> ImageFont.ImageFont:
    for path in (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_tree_background(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    for y in range(CANVAS_SIZE[1]):
        shade = 16 + y * 7 // CANVAS_SIZE[1]
        draw.line((0, y, CANVAS_SIZE[0], y), fill=(5, shade, shade + 4, 255))

    draw.rectangle((0, 0, CANVAS_SIZE[0] - 1, 47), fill=(31, 32, 31, 255))
    draw.line((0, 47, CANVAS_SIZE[0], 47), fill=(94, 98, 93, 255), width=2)
    draw.text((18, 12), "俄共（布）组织路线", font=load_font(20), fill=(224, 224, 216, 255))


def draw_connections(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    for parent, child in EDGES:
        _, px, py = NODES[parent]
        _, cx, cy = NODES[child]
        start = (px + ICON_SIZE // 2, py + ICON_SIZE)
        end = (cx + ICON_SIZE // 2, cy)
        bend_y = (start[1] + end[1]) // 2
        draw.line((start[0], start[1], start[0], bend_y), fill=(156, 62, 58, 255), width=2)
        draw.line((start[0], bend_y, end[0], bend_y), fill=(156, 62, 58, 255), width=2)
        draw.line((end[0], bend_y, end[0], end[1]), fill=(156, 62, 58, 255), width=2)


def draw_node_labels(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    font = load_font(15)
    for label, left, top in NODES:
        box = draw.textbbox((0, 0), label, font=font)
        width = box[2] - box[0]
        label_left = left + ICON_SIZE // 2 - width // 2 - 10
        label_top = top + ICON_SIZE + 7
        label_right = label_left + width + 20
        draw.rectangle((label_left, label_top, label_right, label_top + 30), fill=(9, 18, 20, 255), outline=(195, 199, 190, 255), width=1)
        draw.text((label_left + 10, label_top + 5), label, font=font, fill=(236, 236, 227, 255))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    frame = build_frame()
    frame.save(FRAME_PREVIEW)

    guide = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 255))
    draw_tree_background(guide)
    draw_connections(guide)

    # Seed each aperture with a dark neutral field. The API mask exposes only
    # these exact final-size interiors and locks the reusable frame and UI.
    guide_draw = ImageDraw.Draw(guide)
    for _, left, top in NODES:
        cx = left + ICON_SIZE // 2
        cy = top + ICON_SIZE // 2 + 1
        guide_draw.ellipse(
            (cx - ART_RADIUS, cy - ART_RADIUS, cx + ART_RADIUS, cy + ART_RADIUS),
            fill=(27, 27, 25, 255),
        )
        guide.alpha_composite(frame, (left, top))

    draw_node_labels(guide)
    guide.save(GUIDE)
    guide.save(TREE_PREVIEW)

    mask = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
    mask_draw = ImageDraw.Draw(mask)
    for _, left, top in NODES:
        cx = left + ICON_SIZE // 2
        cy = top + ICON_SIZE // 2 + 1
        mask_draw.ellipse(
            (cx - ART_RADIUS, cy - ART_RADIUS, cx + ART_RADIUS, cy + ART_RADIUS),
            fill=(255, 255, 255, 0),
        )
    mask.save(MASK)

    # Separate guide for generating the frame family itself. Each editable
    # slot is exactly 100x100; the tree UI remains locked by the edit mask.
    frame_guide = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 255))
    draw_tree_background(frame_guide)
    draw_connections(frame_guide)
    frame_draw = ImageDraw.Draw(frame_guide)
    for _, left, top in NODES:
        frame_draw.rectangle(
            (left, top, left + ICON_SIZE - 1, top + ICON_SIZE - 1),
            fill=(7, 18, 20, 255),
            outline=(74, 79, 76, 255),
        )
    draw_node_labels(frame_guide)
    frame_guide.save(FRAME_CANDIDATE_GUIDE)

    frame_mask = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
    frame_mask_draw = ImageDraw.Draw(frame_mask)
    for _, left, top in NODES:
        frame_mask_draw.rectangle(
            (left, top, left + ICON_SIZE - 1, top + ICON_SIZE - 1),
            fill=(255, 255, 255, 0),
        )
    frame_mask.save(FRAME_CANDIDATE_MASK)


if __name__ == "__main__":
    main()
