from __future__ import annotations

import shutil
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "output/imagegen/KR_PSR_11_Focus_Icons_Web_Import_v1/sources"
OUTPUT_DIR = ROOT / "output/imagegen/KR_PSR_11_Focus_Icons_Web_Import_v1"
EXTRACTED_DIR = OUTPUT_DIR / "extracted_100px"
BACKUP_DIR = OUTPUT_DIR / "backup_previous_icons"
TARGET_DIR = ROOT / "gfx/interface/goals/RUS_kamenev_politics"

PSR_SHEET = SOURCE_DIR / "psr_11_web_sheet.png"
REPLACEMENT_SHEET = SOURCE_DIR / "replacement_web_sheet.png"

FILENAMES = [
    "RUS_kamenev_psr_rebuild_central_committee.png",
    "RUS_kamenev_psr_absorb_democratic_parties.png",
    "RUS_kamenev_psr_preserve_land_committees.png",
    "RUS_kamenev_psr_claim_internal_affairs.png",
    "RUS_kamenev_psr_defend_revolutionary_democracy.png",
    "RUS_kamenev_psr_land_socialisation_bill.png",
    "RUS_kamenev_psr_peasant_congress.png",
    "RUS_kamenev_psr_final_party_congress.png",
    "RUS_kamenev_psr_cooperatives_fair_grain_prices.png",
    "RUS_kamenev_psr_local_self_government.png",
    "RUS_kamenev_psr_agrarian_socialism.png",
]

# Bounds isolate each generated slot without relying on perfectly even placement.
PSR_CELLS = [
    (0, 20, 500, 320),
    (500, 20, 835, 320),
    (835, 20, 1168, 320),
    (1168, 20, 1669, 320),
    (0, 320, 500, 600),
    (500, 320, 835, 600),
    (835, 320, 1168, 600),
    (1168, 320, 1669, 600),
    (334, 590, 667, 942),
    (667, 590, 1000, 942),
    (1000, 590, 1335, 942),
]
REPLACEMENT_CELL = (1010, 580, 1500, 949)
FINAL_CONTENT_SIZE = 88
DETAIL_SMOOTH_BLEND = 0.85
STRONG_EDGE_THRESHOLD = 28


def is_chroma_green(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, _ = pixel
    return g > 120 and g - max(r, b) > 80


def largest_foreground_component(
    image: Image.Image, cell: tuple[int, int, int, int]
) -> set[tuple[int, int]]:
    x0, y0, x1, y1 = cell
    pixels = image.load()
    foreground = {
        (x, y)
        for y in range(y0, y1)
        for x in range(x0, x1)
        if not is_chroma_green(pixels[x, y])
    }
    largest: set[tuple[int, int]] = set()

    while foreground:
        seed = foreground.pop()
        component = {seed}
        queue = deque([seed])
        while queue:
            x, y = queue.popleft()
            for neighbor_y in (y - 1, y, y + 1):
                for neighbor_x in (x - 1, x, x + 1):
                    neighbor = (neighbor_x, neighbor_y)
                    if neighbor in foreground:
                        foreground.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
        if len(component) > len(largest):
            largest = component

    if not largest:
        raise RuntimeError(f"No foreground found in cell {cell}")
    return largest


def extract_icon(
    image: Image.Image,
    cell: tuple[int, int, int, int],
    background: tuple[int, int, int],
) -> Image.Image:
    component = largest_foreground_component(image, cell)
    xs = [point[0] for point in component]
    ys = [point[1] for point in component]
    padding = 6
    bounds = (
        max(0, min(xs) - padding),
        max(0, min(ys) - padding),
        min(image.width, max(xs) + 1 + padding),
        min(image.height, max(ys) + 1 + padding),
    )
    crop = image.crop(bounds).convert("RGBA")

    core = Image.new("L", crop.size, 0)
    core_pixels = core.load()
    for x, y in component:
        core_pixels[x - bounds[0], y - bounds[1]] = 255
    allowed = core.filter(ImageFilter.MaxFilter(13))

    source_pixels = crop.load()
    allowed_pixels = allowed.load()
    bg_r, bg_g, bg_b = background
    for y in range(crop.height):
        for x in range(crop.width):
            r, g, b, _ = source_pixels[x, y]
            if allowed_pixels[x, y] == 0:
                source_pixels[x, y] = (0, 0, 0, 0)
                continue

            green_dominance = g - max(r, b)
            if g < 100 or green_dominance <= 60:
                alpha = 255
            elif green_dominance >= 190:
                alpha = 0
            else:
                alpha = round(255 * (190 - green_dominance) / 130)

            if alpha < 12:
                source_pixels[x, y] = (0, 0, 0, 0)
                continue

            # Recover the foreground colour from pixels blended against the green sheet.
            opacity = alpha / 255
            out_r = round((r - (1 - opacity) * bg_r) / opacity)
            out_g = round((g - (1 - opacity) * bg_g) / opacity)
            out_b = round((b - (1 - opacity) * bg_b) / opacity)
            source_pixels[x, y] = (
                max(0, min(255, out_r)),
                max(0, min(255, out_g)),
                max(0, min(255, out_b)),
                alpha,
            )

    alpha_bounds = crop.getchannel("A").getbbox()
    if alpha_bounds is None:
        raise RuntimeError(f"Empty alpha after chroma removal in cell {cell}")
    crop = crop.crop(alpha_bounds)

    scale = min(FINAL_CONTENT_SIZE / crop.width, FINAL_CONTENT_SIZE / crop.height)
    resized = crop.resize(
        (max(1, round(crop.width * scale)), max(1, round(crop.height * scale))),
        Image.Resampling.LANCZOS,
    )
    resized_pixels = resized.load()
    for y in range(resized.height):
        for x in range(resized.width):
            r, g, b, alpha = resized_pixels[x, y]
            if alpha < 12:
                resized_pixels[x, y] = (0, 0, 0, 0)
            elif alpha < 245 and g > max(r, b) + 10:
                # Remove chroma spill only from antialiased outer pixels.
                resized_pixels[x, y] = (r, max(r, b) + 10, b, alpha)
    result = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    result.alpha_composite(
        resized,
        ((100 - resized.width) // 2, (100 - resized.height) // 2),
    )
    edge_test = result.getchannel("A").filter(ImageFilter.MinFilter(7))
    result_pixels = result.load()
    edge_pixels = edge_test.load()
    for y in range(result.height):
        for x in range(result.width):
            r, g, b, alpha = result_pixels[x, y]
            green_dominance = g - max(r, b)
            if edge_pixels[x, y] < 128 and g > 60 and green_dominance > 30:
                # Generated sheets include opaque dark-green drop-shadow remnants.
                result_pixels[x, y] = (0, 0, 0, 0)
            elif edge_pixels[x, y] < 128 and green_dominance > 10:
                result_pixels[x, y] = (r, max(r, b) + 10, b, alpha)

    # Suppress small generated texture, then restore strong subject and frame boundaries.
    original_alpha = result.getchannel("A")
    interior_mask = original_alpha.filter(ImageFilter.MinFilter(5)).point(
        lambda value: 235 if value >= 245 else 0
    )
    median_smoothed = result.filter(ImageFilter.MedianFilter(3))
    detail_smoothed = Image.blend(result, median_smoothed, DETAIL_SMOOTH_BLEND)

    edge_source = (
        result.convert("L")
        .filter(ImageFilter.GaussianBlur(0.65))
        .filter(ImageFilter.FIND_EDGES)
    )
    strong_edges = edge_source.point(
        lambda value: 255 if value >= STRONG_EDGE_THRESHOLD else 0
    ).filter(ImageFilter.MaxFilter(3))
    edge_protected = Image.composite(result, detail_smoothed, strong_edges)
    result = Image.composite(edge_protected, result, interior_mask)
    result.putalpha(original_alpha)
    return result


def build_preview(icons: list[Image.Image]) -> Image.Image:
    preview = Image.new("RGBA", (500, 380), (20, 24, 23, 255))
    draw = ImageDraw.Draw(preview)
    positions = [
        *((20 + column * 120, 20) for column in range(4)),
        *((20 + column * 120, 140) for column in range(4)),
        *((80 + column * 120, 260) for column in range(3)),
    ]
    for index, (icon, position) in enumerate(zip(icons, positions, strict=True), start=1):
        preview.alpha_composite(icon, position)
        draw.text((position[0] + 3, position[1] + 82), str(index), fill=(235, 230, 210, 255))
    return preview


def main() -> None:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    psr_sheet = Image.open(PSR_SHEET).convert("RGBA")
    replacement_sheet = Image.open(REPLACEMENT_SHEET).convert("RGBA")
    if psr_sheet.size != (1669, 942):
        raise ValueError(f"Unexpected PSR sheet size: {psr_sheet.size}")
    if replacement_sheet.size != (1658, 949):
        raise ValueError(f"Unexpected replacement sheet size: {replacement_sheet.size}")

    icons = [
        extract_icon(psr_sheet, cell, (8, 228, 12))
        for cell in PSR_CELLS[:10]
    ]
    icons.append(extract_icon(replacement_sheet, REPLACEMENT_CELL, (6, 231, 17)))

    for filename, icon in zip(FILENAMES, icons, strict=True):
        target = TARGET_DIR / filename
        backup = BACKUP_DIR / filename
        if target.exists() and not backup.exists():
            shutil.copy2(target, backup)
        icon.save(EXTRACTED_DIR / filename)
        icon.save(target)

    build_preview(icons).save(OUTPUT_DIR / "PSR_11_icons_actual_size_preview.png")

    for filename in FILENAMES:
        image = Image.open(TARGET_DIR / filename)
        if image.size != (100, 100) or image.mode != "RGBA":
            raise RuntimeError(f"Invalid imported icon: {filename} {image.size} {image.mode}")
        if image.getchannel("A").getbbox() is None:
            raise RuntimeError(f"Imported icon has empty alpha: {filename}")

    print(f"Imported {len(icons)} PSR icons into {TARGET_DIR}")
    print(f"Preview: {OUTPUT_DIR / 'PSR_11_icons_actual_size_preview.png'}")
    print("Slot 11 source: replacement sheet bottom-right PSR icon")


if __name__ == "__main__":
    main()
