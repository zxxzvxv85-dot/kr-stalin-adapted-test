#!/usr/bin/env python3
"""Draw the 23x33 unit-leader trait icon for `RUS_fr_fragmented_officer_training`.

Unit leader traits are drawn by the game with the sprite `GFX_trait_<trait token>`,
so every visible trait needs its own icon. The mod defines the trait in
`common/unit_leader/RUS_fr_military_reform_traits.txt` and points the sprite at
`gfx/interface/traits/RUS_fr_fragmented_officer_training.png`.

Usage:
    python tools/build_fragmented_officer_training_icon.py
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

SIZE = (23, 33)
SCALE = 8  # supersample, then downscale for smooth edges
OUT = pathlib.Path(__file__).resolve().parents[1] / "gfx/interface/traits/RUS_fr_fragmented_officer_training.png"

BOARD = (58, 64, 78, 255)
BOARD_EDGE = (196, 162, 84, 255)
CHEVRON = (223, 188, 104, 255)
CRACK = (188, 52, 44, 255)


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline, width):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def chevron(draw: ImageDraw.ImageDraw, y: int, x0: int, x1: int, thickness: int, color):
    mid = (x0 + x1) // 2
    top = y
    bottom = y + thickness + 3
    draw.line([(x0, bottom), (mid, top)], fill=color, width=thickness)
    draw.line([(mid, top), (x1, bottom)], fill=color, width=thickness)


def main() -> None:
    w, h = SIZE[0] * SCALE, SIZE[1] * SCALE
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # officer shoulder board
    rounded(d, (4 * SCALE, 2 * SCALE, 18 * SCALE + SCALE, 30 * SCALE + SCALE),
            radius=3 * SCALE, fill=BOARD, outline=BOARD_EDGE, width=SCALE)

    # three rank chevrons
    for y in (7, 13, 19):
        chevron(d, y * SCALE, 6 * SCALE, 14 * SCALE, 2 * SCALE, CHEVRON)

    # red crack: broken training pipeline
    crack = [(17, 4), (14, 10), (17, 15), (12, 21), (10, 29)]
    d.line([(x * SCALE, y * SCALE) for x, y in crack], fill=CRACK, width=SCALE + SCALE // 2, joint="curve")
    d.line([(14 * SCALE, 10 * SCALE), (9 * SCALE, 12 * SCALE)], fill=CRACK, width=SCALE)
    d.line([(17 * SCALE, 15 * SCALE), (19 * SCALE, 18 * SCALE)], fill=CRACK, width=SCALE)

    img = img.resize(SIZE, Image.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"wrote {OUT} {img.size} {img.mode}")


if __name__ == "__main__":
    main()
