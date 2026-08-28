from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "gfx/event_pictures/Europe/Russia"
SOURCE = ASSET_DIR / "GFX_report_event_RUS_bryukhanov_sketch_source.jpg"
OUTPUT = ASSET_DIR / "GFX_report_event_RUS_bryukhanov_sketch.png"

CANVAS_SIZE = (210, 176)
PHOTO_SIZE = (184, 138)
PAPER_BORDER = 3
ROTATION_DEGREES = -3.0


def fit_source(image: Image.Image) -> Image.Image:
    # Remove the video-frame edge while preserving the full drawing.
    image = image.crop((8, 18, image.width - 8, image.height - 2)).convert("RGB")
    image = ImageOps.fit(
        image,
        PHOTO_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Sharpness(image).enhance(0.92)

    monochrome = ImageOps.colorize(
        ImageOps.grayscale(image),
        black="#171510",
        white="#e8e1d0",
    )
    return Image.blend(image, monochrome, 0.42)


def build_card(photo: Image.Image) -> Image.Image:
    card_size = (
        photo.width + PAPER_BORDER * 2,
        photo.height + PAPER_BORDER * 2,
    )
    card = Image.new("RGBA", card_size, (232, 225, 208, 255))
    card.paste(photo, (PAPER_BORDER, PAPER_BORDER))
    ImageDraw.Draw(card).rectangle(
        (0, 0, card.width - 1, card.height - 1),
        outline=(72, 68, 59, 255),
        width=1,
    )
    return card.rotate(
        ROTATION_DEGREES,
        resample=Image.Resampling.BICUBIC,
        expand=True,
    )


def compose(card: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    x = (canvas.width - card.width) // 2 - 1
    y = (canvas.height - card.height) // 2 - 1

    shadow_alpha = card.getchannel("A").filter(ImageFilter.GaussianBlur(3.2))
    shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    shadow.putalpha(shadow_alpha.point(lambda value: int(value * 0.46)))
    canvas.alpha_composite(shadow, (x + 4, y + 5))
    canvas.alpha_composite(card, (x, y))
    return canvas


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Missing source image: {SOURCE}")
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE) as source:
        output = compose(build_card(fit_source(source)))
    output.save(OUTPUT, format="PNG", optimize=True)
    print(f"Wrote {OUTPUT} ({output.width}x{output.height}, RGBA)")


if __name__ == "__main__":
    main()
