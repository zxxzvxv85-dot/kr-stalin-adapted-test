#!/usr/bin/env python3
"""Rebuild the KR frontend background (main menu cover).

The KR/vanilla ``frontend_background`` container is a 1920x1440 (4:3) box anchored
to the centre of the screen with ``preserve_aspect_ratio``, so a 16:9 display only
draws the middle 1920x1080 rows of the texture. The texture therefore has to be 4:3
while the artwork is 16:9, which is why KR ships 16:9 pictures inside a 4:3 canvas.

Two layout modes:
    crop       - centre-crop the source to 4:3 and scale it to 1920x1440, so the
                 texture is all picture with no filler.
    letterbox  - keep the whole 16:9 picture at native 1920x1080 in the middle and
                 leave the 180px bands fully transparent: nothing is cropped, nothing
                 is distorted and no filler colour is baked in.

Crop drops the sides of a 16:9 source (and, because only the middle band is drawn,
the visible result is also zoomed vertically); letterbox never loses any picture.

The runtime DDS is uncompressed without mipmaps: 24-bit RGB when the canvas is fully
opaque, 32-bit RGBA (same layout as gfx/interface/logo_game.dds) when the bands are
transparent.

Usage:
    python tools/build_main_menu_background.py <source image> [crop|letterbox]
"""
from __future__ import annotations

import pathlib
import struct
import sys

from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "gfx" / "loadingscreens"
TEXTURE = OUT_DIR / "RUS_stalin_main_menu.dds"

WIDTH, HEIGHT = 1920, 1440          # native KR frontend canvas (4:3)
BAND = (HEIGHT - WIDTH * 9 // 16) // 2  # 180px top/bottom bands a 16:9 screen hides
MODES = ("crop", "letterbox")
DEFAULT_MODE = "letterbox"


def build_canvas(source: pathlib.Path, mode: str) -> Image.Image:
    art = Image.open(source).convert("RGB")
    if mode == "crop":
        return _centre_crop(art, WIDTH / HEIGHT).resize((WIDTH, HEIGHT), Image.LANCZOS)
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    canvas.paste(art.resize((WIDTH, HEIGHT - 2 * BAND), Image.LANCZOS), (0, BAND))
    return canvas


def _centre_crop(image: Image.Image, ratio: float) -> Image.Image:
    if image.width / image.height > ratio:      # too wide: drop the sides
        width = round(image.height * ratio)
        left = (image.width - width) // 2
        return image.crop((left, 0, left + width, image.height))
    height = round(image.width / ratio)          # too tall: drop top and bottom
    top = (image.height - height) // 2
    return image.crop((0, top, image.width, top + height))


def write_dds(image: Image.Image, path: pathlib.Path) -> int:
    """Write an uncompressed DDS (legacy 128-byte header, no mipmaps).

    A fully opaque canvas stays 24-bit RGB like the previous menu background; a canvas
    with transparent bands needs the 32-bit RGBA layout the mod's logo already uses.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    opaque = image.getchannel("A").getextrema() == (255, 255)
    bpp = 3 if opaque else 4
    flags = 0x40 if opaque else 0x41  # DDPF_RGB [| DDPF_ALPHAPIXELS]
    alpha_mask = 0 if opaque else 0xFF000000
    masks = (0x00FF0000, 0x0000FF00, 0x000000FF, alpha_mask)
    header = b"".join(
        (
            b"DDS ",
            struct.pack(
                "<7I",
                124,             # dwSize
                0x0000100F,      # CAPS | HEIGHT | WIDTH | PITCH | PIXELFORMAT
                image.height,
                image.width,
                image.width * bpp,  # dwPitchOrLinearSize
                0,               # dwDepth
                0,               # dwMipMapCount
            ),
            b"\0" * 44,          # dwReserved1[11]
            struct.pack("<8I", 32, flags, 0, bpp * 8, *masks),
            struct.pack("<5I", 0x1000, 0, 0, 0, 0),  # caps: texture only
        )
    )
    assert len(header) == 128, len(header)
    # The masks put R (and A) in the third (and fourth) byte, so the data is stored
    # BGRA / BGR - the same order as logo_game.dds and the previous menu background.
    r, g, b, a = image.split()
    payload = (Image.merge("RGB", (b, g, r)) if opaque else Image.merge("RGBA", (b, g, r, a))).tobytes()
    path.write_bytes(header + payload)
    return len(header) + len(payload)


def main() -> int:
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] not in MODES):
        print(__doc__)
        return 2
    mode = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_MODE
    source = pathlib.Path(sys.argv[1])
    if not source.is_file():
        print(f"missing source image: {source}")
        return 2

    canvas = build_canvas(source, mode)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    size = write_dds(canvas, TEXTURE)
    canvas.save(OUT_DIR / "RUS_stalin_main_menu_source.png")
    canvas.save(OUT_DIR / "RUS_stalin_main_menu_preview.png")
    canvas.crop((0, BAND, WIDTH, HEIGHT - BAND)).save(OUT_DIR / "RUS_stalin_main_menu_16x9_preview.png")
    Image.open(source).save(OUT_DIR / "RUS_stalin_main_menu_source_raw.png")
    print(f"mode {mode}: canvas {canvas.size}, visible band {WIDTH}x{HEIGHT - 2 * BAND}, dds {size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
