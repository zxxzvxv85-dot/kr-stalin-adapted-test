from __future__ import annotations

import math
from collections import deque
from pathlib import Path
from statistics import median

from PIL import Image, ImageChops, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/imagegen/RUS_kamenev_bolshevik_eight_complete_icons_v6.png"
OUTPUT_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_eight_complete_icons_v6_scaled_100px"
CONTACT = ROOT / "output/imagegen/RUS_kamenev_bolshevik_eight_complete_icons_v6_scaled_100px.png"
WHITE_PREVIEW = ROOT / "output/imagegen/RUS_kamenev_bolshevik_eight_complete_icons_v6_scaled_100px_white.png"

FINAL_SIZE = 100
MAX_WIDTH = 94
MAX_HEIGHT = 90

# Complete visual bounds measured on the generated 1254x1254 focus-tree
# plate. These deliberately stop above each UI label and include the entire
# badge, unlike the earlier fixed-slot crops.
ICONS = [
    ("RUS_kamenev_bol_register_returning_members.png", (548, 62, 706, 193), None),
    ("RUS_kamenev_bol_restore_pravda.png", (343, 248, 512, 372), 431),
    ("RUS_kamenev_bol_restore_central_bureau.png", (745, 252, 907, 372), 822),
    ("RUS_kamenev_bol_unify_planning_apparatus.png", (168, 464, 312, 581), 237),
    ("RUS_kamenev_bol_rebuild_factory_cells.png", (545, 466, 710, 581), 627),
    ("RUS_kamenev_bol_railway_telegraph_bureau.png", (340, 665, 520, 794), 431),
    ("RUS_kamenev_bol_win_vst_majority.png", (740, 678, 910, 794), 822),
    ("RUS_kamenev_bol_undissolved_central_committee.png", (525, 890, 728, 1060), 627),
]


def median_background(crop: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    values: list[tuple[int, int, int]] = []
    for red, green, blue, _ in crop.crop(box).getdata():
        if red < 35 and green < 55 and blue < 65 and blue >= red + 5:
            values.append((red, green, blue))
    if not values:
        return (7, 22, 27)
    return tuple(int(median(channel)) for channel in zip(*values, strict=True))


def lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def build_alpha(crop: Image.Image) -> Image.Image:
    width, height = crop.size
    sample = max(6, min(width, height) // 12)
    corners = (
        median_background(crop, (0, 0, sample, sample)),
        median_background(crop, (width - sample, 0, width, sample)),
        median_background(crop, (0, height - sample, sample, height)),
        median_background(crop, (width - sample, height - sample, width, height)),
    )

    alpha = Image.new("L", crop.size, 0)
    alpha_pixels = alpha.load()
    source_pixels = crop.load()
    for y in range(height):
        fy = y / max(1, height - 1)
        for x in range(width):
            fx = x / max(1, width - 1)
            top = tuple(lerp(corners[0][index], corners[1][index], fx) for index in range(3))
            bottom = tuple(lerp(corners[2][index], corners[3][index], fx) for index in range(3))
            expected = tuple(lerp(top[index], bottom[index], fy) for index in range(3))
            red, green, blue, _ = source_pixels[x, y]
            distance = math.sqrt(
                (red - expected[0]) ** 2
                + (green - expected[1]) ** 2
                + (blue - expected[2]) ** 2
            )
            if distance <= 12:
                value = 0
            elif distance >= 36:
                value = 255
            else:
                value = int((distance - 12) * 255 / 24)
            alpha_pixels[x, y] = value

    # Remove background grain and the one-pixel focus-tree connectors before
    # restoring a narrow antialiased edge around the real badge silhouette.
    binary = alpha.point(lambda value: 255 if value >= 96 else 0)
    opened = binary.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    keep_large_components(opened)
    support = opened.filter(ImageFilter.MaxFilter(5))
    return ImageChops.multiply(alpha, support)


def keep_large_components(alpha: Image.Image) -> None:
    width, height = alpha.size
    pixels = alpha.load()
    visited = bytearray(width * height)

    components: list[list[tuple[int, int]]] = []
    for start_y in range(height):
        for start_x in range(width):
            offset = start_y * width + start_x
            if visited[offset] or pixels[start_x, start_y] <= 48:
                continue

            queue = deque([(start_x, start_y)])
            visited[offset] = 1
            component: list[tuple[int, int]] = []
            min_x = max_x = start_x
            min_y = max_y = start_y
            while queue:
                x, y = queue.popleft()
                component.append((x, y))
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                for next_x, next_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if not (0 <= next_x < width and 0 <= next_y < height):
                        continue
                    next_offset = next_y * width + next_x
                    if visited[next_offset] or pixels[next_x, next_y] <= 48:
                        continue
                    visited[next_offset] = 1
                    queue.append((next_x, next_y))

            components.append(component)

    if not components:
        return
    largest = max(len(component) for component in components)
    minimum = max(30, largest // 50)
    for component in components:
        if len(component) < minimum:
            for x, y in component:
                pixels[x, y] = 0


def premultiplied_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def remove_top_connector_stub(alpha: Image.Image, local_x: int) -> None:
    pixels = alpha.load()
    width, height = alpha.size
    started = False
    for y in range(min(height, 28)):
        active = sum(
            pixels[x, y] > 48
            for x in range(max(0, local_x - 5), min(width, local_x + 6))
        )
        if not started:
            if active == 0:
                continue
            started = True
        if active > 5:
            break
        for x in range(max(0, local_x - 2), min(width, local_x + 3)):
            pixels[x, y] = 0


def main() -> None:
    source = Image.open(SOURCE).convert("RGBA")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    contact = Image.new("RGBA", (FINAL_SIZE * 4, FINAL_SIZE * 2), (0, 0, 0, 0))

    for index, (filename, bounds, connector_x) in enumerate(ICONS):
        crop = source.crop(bounds)
        alpha = build_alpha(crop)
        if connector_x is not None:
            remove_top_connector_stub(alpha, connector_x - bounds[0])
        crop.putalpha(alpha)

        content_box = alpha.getbbox()
        if content_box is None:
            raise RuntimeError(f"No foreground found for {filename}")
        isolated = crop.crop(content_box)
        scale = min(MAX_WIDTH / isolated.width, MAX_HEIGHT / isolated.height)
        scaled_size = (
            max(1, round(isolated.width * scale)),
            max(1, round(isolated.height * scale)),
        )
        scaled = premultiplied_resize(isolated, scaled_size)

        final = Image.new("RGBA", (FINAL_SIZE, FINAL_SIZE), (0, 0, 0, 0))
        left = (FINAL_SIZE - scaled.width) // 2
        top = (FINAL_SIZE - scaled.height) // 2
        final.alpha_composite(scaled, (left, top))
        final.save(OUTPUT_DIR / filename)
        contact.alpha_composite(final, ((index % 4) * FINAL_SIZE, (index // 4) * FINAL_SIZE))

        final_box = final.getchannel("A").getbbox()
        print(f"{filename}: source={isolated.size}, scaled={scaled.size}, alpha_bbox={final_box}")

    contact.save(CONTACT)
    white = Image.new("RGBA", contact.size, (235, 235, 229, 255))
    white.alpha_composite(contact)
    white.save(WHITE_PREVIEW)


if __name__ == "__main__":
    main()
