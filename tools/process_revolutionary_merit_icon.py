from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
SOURCE = Path(
    "C:/Users/Administrator/AppData/Local/Temp/"
    "codex-clipboard-dfbf2394-1739-4721-9ccc-6ce3409949ff.png"
)
OUTPUT_DIR = ROOT / "output/imagegen/revolutionary_merit_competition"
STAGED = OUTPUT_DIR / "revolutionary_merit_competition.png"

TARGET_RELATIVE = Path(
    "gfx/interface/goals/RUS_fr_military_reform/"
    "revolutionary_merit_competition.png"
)
TARGETS = [
    ROOT / TARGET_RELATIVE,
    WORKSHOP_ROOT / "kr_stalin_adapted_test_upload" / TARGET_RELATIVE,
    WORKSHOP_ROOT / "kr_stalin_adapted_test_pending_upload" / TARGET_RELATIVE,
]

NEIGHBOURS = [
    "tempered_in_steel.png",
    "strict_training_red_flag.png",
    "mechanisation_wave.png",
    "military_system_finalised.png",
    "red_commander_system.png",
]

CANVAS_SIZE = (100, 88)
CONTENT_LIMIT = (87, 87)
SHARPEN_RADIUS = 0.50
SHARPEN_PERCENT = 50
SHARPEN_THRESHOLD = 2


def font(size: int) -> ImageFont.ImageFont:
    for path in (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def chroma_key(source: Image.Image) -> Image.Image:
    rgb = source.convert("RGB")
    output: list[tuple[int, int, int, int]] = []

    for red, green, blue in rgb.get_flattened_data():
        green_excess = green - max(red, blue)

        if green >= 120 and green_excess >= 105:
            alpha = 0
        elif green >= 55 and green_excess > 20:
            alpha = round(255 * (105 - green_excess) / 85)
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        if alpha < 12:
            output.append((0, 0, 0, 0))
            continue

        # Recover edge colour from the green-screen mix instead of merely
        # lowering green, which otherwise leaves a dark green thumbnail halo.
        opacity = max(alpha / 255, 0.08)
        edge_mix = 1 - opacity
        clean_red = round(red / opacity)
        clean_green = round((green - 255 * edge_mix) / opacity)
        clean_blue = round(blue / opacity)
        clean_red = max(0, min(255, clean_red))
        clean_green = max(0, min(255, clean_green))
        clean_blue = max(0, min(255, clean_blue))

        if alpha < 255:
            clean_green = min(clean_green, max(clean_red, clean_blue) + 3)
        output.append((clean_red, clean_green, clean_blue, alpha))

    result = Image.new("RGBA", rgb.size, (0, 0, 0, 0))
    result.putdata(output)
    return result


def crop_subject(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.point(lambda value: 255 if value >= 18 else 0).getbbox()
    if bbox is None:
        raise ValueError("No foreground subject found after chroma keying")
    return image.crop(bbox)


def tone_subject(image: Image.Image) -> Image.Image:
    source = image.convert("RGBA")
    width, height = source.size
    corrected: list[tuple[int, int, int, int]] = []

    for index, (red, green, blue, alpha) in enumerate(source.get_flattened_data()):
        if alpha == 0:
            corrected.append((0, 0, 0, 0))
            continue

        x = index % width
        y = index // width
        luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue

        # Open the dense source midtones while retaining genuinely dark recesses.
        # The directional multiplier establishes the KR-style upper-left key light.
        levelled = luminance * 1.34
        contrast = (levelled - 92) * 1.085 + 92
        direction = 1.08 - 0.06 * (x / max(1, width - 1)) - 0.05 * (
            y / max(1, height - 1)
        )
        target_luminance = max(0, min(255, contrast * direction))
        ratio = target_luminance / max(1, luminance)
        ratio = max(0.72, min(1.68, ratio))

        red = max(0, min(255, round(red * ratio)))
        green = max(0, min(255, round(green * ratio)))
        blue = max(0, min(255, round(blue * ratio)))
        corrected.append((red, green, blue, alpha))

    source.putdata(corrected)
    alpha = source.getchannel("A")
    coloured = ImageEnhance.Color(source.convert("RGB")).enhance(1.035)
    return Image.merge("RGBA", (*coloured.split(), alpha))


def resize_rgba(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    # Pillow's RGBa mode stores premultiplied alpha and prevents transparent
    # edge colours from bleeding into the final Lanczos thumbnail.
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def fit_to_canvas(subject: Image.Image) -> Image.Image:
    scale = min(
        CONTENT_LIMIT[0] / subject.width,
        CONTENT_LIMIT[1] / subject.height,
    )
    fitted_size = (
        max(1, round(subject.width * scale)),
        max(1, round(subject.height * scale)),
    )
    fitted = resize_rgba(subject, fitted_size)

    alpha = fitted.getchannel("A")
    sharpened = fitted.convert("RGB").filter(
        ImageFilter.UnsharpMask(
            radius=SHARPEN_RADIUS,
            percent=SHARPEN_PERCENT,
            threshold=SHARPEN_THRESHOLD,
        )
    )
    fitted = Image.merge("RGBA", (*sharpened.split(), alpha))

    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    x = (CANVAS_SIZE[0] - fitted.width) // 2
    y = (CANVAS_SIZE[1] - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))
    return canvas


def composite_background(icon: Image.Image, colour: tuple[int, int, int]) -> Image.Image:
    background = Image.new("RGBA", icon.size, (*colour, 255))
    background.alpha_composite(icon)
    return background.convert("RGB")


def padded_icon(path: Path) -> Image.Image:
    source = Image.open(path).convert("RGBA")
    if source.width > 100 or source.height > 88:
        scale = min(100 / source.width, 88 / source.height)
        source = resize_rgba(source, (round(source.width * scale), round(source.height * scale)))
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    canvas.alpha_composite(
        source,
        ((100 - source.width) // 2, (88 - source.height) // 2),
    )
    return canvas


def luma_summary(icon: Image.Image) -> tuple[float, int, int, int]:
    values: list[int] = []
    for red, green, blue, alpha in icon.get_flattened_data():
        if alpha >= 128:
            values.append(round(0.2126 * red + 0.7152 * green + 0.0722 * blue))
    values.sort()
    if not values:
        return (0.0, 0, 0, 0)
    return (
        round(sum(values) / len(values), 2),
        values[len(values) // 10],
        values[len(values) // 2],
        values[min(len(values) - 1, len(values) * 9 // 10)],
    )


def make_previews(before: Image.Image, final: Image.Image) -> None:
    dark = composite_background(final, (7, 18, 22))
    white = composite_background(final, (240, 240, 236))
    dark.save(OUTPUT_DIR / "preview_dark.png")
    white.save(OUTPUT_DIR / "preview_white.png")

    military_dir = TARGETS[0].parent
    icons = [before, final] + [padded_icon(military_dir / name) for name in NEIGHBOURS]
    labels = ["旧版", "新版", "淬火成钢", "严格训练", "机械化浪潮", "军制完成", "红色指挥员"]
    canvas = Image.new("RGB", (800, 255), (7, 18, 22))
    draw = ImageDraw.Draw(canvas)
    label_font = font(13)
    title_font = font(15)
    draw.text((10, 8), "革命功勋竞赛：实尺寸与相邻军改图标", font=title_font, fill=(238, 236, 224))
    for index, (icon, label) in enumerate(zip(icons, labels)):
        x = 10 + index * 112
        y = 42
        canvas.paste(composite_background(icon, (7, 18, 22)), (x, y))
        draw.text((x, 136), label, font=label_font, fill=(238, 236, 224))

        enlarged = composite_background(icon, (7, 18, 22)).resize(
            (200, 176), Image.Resampling.NEAREST
        )
        if index < 2:
            enlarged.save(OUTPUT_DIR / f"preview_{'before' if index == 0 else 'after'}_2x.png")
    canvas.save(OUTPUT_DIR / "comparison_actual_size.png")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    source_copy = OUTPUT_DIR / "source_original.png"
    shutil.copy2(SOURCE, source_copy)

    before_path = TARGETS[0]
    before = padded_icon(before_path)
    backup_path = OUTPUT_DIR / "revolutionary_merit_competition_before.png"
    if not backup_path.exists():
        shutil.copy2(before_path, backup_path)

    keyed = chroma_key(Image.open(SOURCE))
    subject = crop_subject(keyed)
    subject.save(OUTPUT_DIR / "subject_keyed_master.png")
    toned = tone_subject(subject)
    toned.save(OUTPUT_DIR / "subject_toned_master.png")
    final = fit_to_canvas(toned)
    final.save(STAGED)
    make_previews(before, final)

    alpha_bbox = final.getchannel("A").point(lambda value: 255 if value >= 8 else 0).getbbox()
    green_spill = sum(
        1
        for red, green, blue, alpha in final.get_flattened_data()
        if alpha >= 16 and green > max(red, blue) + 18
    )
    print(f"source={SOURCE} size={Image.open(SOURCE).size}")
    print(f"subject={subject.size}")
    print(f"final={STAGED} size={final.size} mode={final.mode} alpha_bbox={alpha_bbox}")
    print(f"luma_before={luma_summary(before)} luma_after={luma_summary(final)}")
    print(f"green_spill_pixels={green_spill}")
    print(f"staged_sha256={sha256(STAGED)}")


if __name__ == "__main__":
    main()
