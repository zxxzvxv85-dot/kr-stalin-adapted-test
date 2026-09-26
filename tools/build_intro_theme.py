"""Fit the printed intro plate and build its controls; default only checks hashes.

The approved title is copied byte-for-byte. The ImageGen plate is fitted to its
native GUI rectangle without cropping; controls remain code-native live UI.
Use --write to rebuild, or --output-root to render a separate review copy.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "tools/art_sources/intro_header_v2_source.png"
FRAME_SOURCE = "tools/art_sources/intro_frame_v2_source.png"
MANIFEST = "tools/art_sources/intro_theme_manifest.json"
FOLDER = "gfx/interface/rus_intro_theme/"
TITLE = "gfx/interface/rus_intro_header/constructivist_title.png"
INK = "#161713"
PAPER = "#e4d2ad"
RED = "#862b1f"
LINE = "#6b604e"
BODY = "#101210"


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def inputs() -> dict[str, str]:
    return {
        SOURCE: digest((ROOT / SOURCE).read_bytes()),
        FRAME_SOURCE: digest((ROOT / FRAME_SOURCE).read_bytes()),
        "tools/build_intro_theme.py": digest(Path(__file__).read_bytes().replace(b"\r\n", b"\n")),
    }


def render_outputs() -> dict[str, bytes]:
    # Import and draw only during an explicit build, never for ordinary checks.
    from PIL import Image, ImageDraw

    output = {TITLE: (ROOT / SOURCE).read_bytes()}

    def canvas(name, size, fill=(0, 0, 0, 0)):
        im = Image.new("RGBA", size, fill)
        return im, ImageDraw.Draw(im)

    def save(name, im):
        stream = io.BytesIO()
        im.save(stream, format="PNG", optimize=False)
        output[FOLDER + name + ".png"] = stream.getvalue()

    def print_grain(im):
        # Repeatable ink variation for code-drawn controls, never the source artwork.
        pixels = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = pixels[x, y]
                if not a:
                    continue
                h = ((x + 71) * 374761393 + (y + 19) * 668265263) & 0xffffffff
                h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
                noise = (h % 9) - 4
                if h % 103 == 0:
                    noise = 16
                pixels[x, y] = tuple(max(0, min(255, c + noise)) for c in (r, g, b)) + (a,)

    # Technical fit only. Alpha stays intact; a separate opaque GUI underlay
    # stops the source's worn ink from letting map labels show through the text.
    with Image.open(ROOT / FRAME_SOURCE) as plate:
        save("frame", plate.convert("RGBA").resize((728, 488), Image.Resampling.LANCZOS))
    im, d = canvas("underlay", (728, 488), BODY)
    save("underlay", im)

    im, d = canvas("bridge", (728, 36))
    d.polygon([(0, 36), (0, 31), (107, 8), (513, 20), (671, 8), (728, 31), (728, 36)], fill=INK)
    d.polygon([(0, 32), (105, 9), (149, 10), (24, 36)], fill=RED)
    d.line([(7, 33), (111, 11)], fill="#b7a27e", width=1)
    print_grain(im)
    save("bridge", im)

    for name, size, fill, border in [
        ("portrait_back", (172, 392), BODY, LINE),
        ("page", (76, 31), INK, LINE),
    ]:
        im, d = canvas(name, size, fill)
        if border:
            d.rectangle((0, 0, size[0] - 1, size[1] - 1), outline=border)
        d.line([(2, 1), (size[0] - 3, 1)], fill="#9c8a69")
        print_grain(im)
        save(name, im)

    # Original logical frame sizes: 123x34 tabs, 241x60 continue, 41x45 arrows.
    # Frame counts for script-controlled checkboxes match KR exactly.
    for name, w, h, frames in [
        ("tab", 123, 34, 2), ("continue", 241, 60, 1),
        ("back", 41, 45, 1), ("forward", 41, 45, 1),
        ("checkbox", 28, 23, 2), ("spoilers", 264, 35, 2),
    ]:
        im, d = canvas(name, (w * frames, h))
        for frame in range(frames):
            x = w * frame
            if name == "checkbox":
                d.rectangle((x + 3, 3, x + 21, 21), fill=INK, outline=LINE)
                d.line([(x + 4, 4), (x + 20, 4)], fill="#988663")
                if frame:
                    d.rectangle((x + 5, 5, x + 19, 19), fill=RED)
                    d.line([(x + 6, 12), (x + 10, 16), (x + 19, 7)], fill="#e3d1ae", width=2)
            elif name == "continue":
                # Smaller printed plaque inside the original 241x60 hitbox.
                d.polygon([(8, 10), (14, 5), (227, 5), (233, 10), (233, 50), (227, 55), (14, 55), (8, 50)], fill="#13130f", outline="#b7a382")
                d.rectangle((12, 9, 229, 51), fill="#72251c", outline="#4a2018")
                d.line([(15, 10), (226, 10)], fill="#b48461")
                d.line([(15, 49), (226, 49)], fill="#ac9271")
                d.line([(17, 46), (224, 46)], fill="#491912")
                for origin in (24, 211):
                    d.polygon([(origin, 24), (origin + 5, 30), (origin, 36), (origin - 5, 30)], fill="#c6ae86")
            elif name in ("back", "forward"):
                d.polygon([(5, 6), (35, 6), (38, 9), (38, 36), (35, 39), (5, 39), (2, 36), (2, 9)], fill="#222018", outline=LINE)
                d.line([(6, 8), (34, 8)], fill="#a4906c")
                d.line([(6, 37), (34, 37)], fill="#862b1f")
                tip = 13 if name == "back" else 28
                tail = 25 if name == "back" else 16
                d.polygon([(tip, 22), (tail, 14), (tail, 30)], fill="#cfbd98")
            else:
                fill = "#733025" if frame else "#29281f"
                d.polygon([(x + 4, 2), (x + w - 5, 2), (x + w - 2, 5), (x + w - 2, h - 6), (x + w - 5, h - 3), (x + 4, h - 3), (x + 1, h - 6), (x + 1, 5)], fill=fill, outline="#8f7e5e")
                d.line([(x + 6, 4), (x + w - 7, 4)], fill="#b09b77" if frame else "#6e6650")
                d.line([(x + 6, h - 6), (x + w - 7, h - 6)], fill="#221913")
                d.line([(x + 6, h - 4), (x + w - 7, h - 4)], fill="#a3442a")
                if name == "spoilers":
                    d.rectangle((x + 8, 9, x + 23, 24), outline=PAPER)
                    if frame:
                        d.line([(x + 10, 17), (x + 15, 22), (x + 23, 11)], fill=PAPER, width=2)
        print_grain(im)
        save(name, im)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--write", action="store_true")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    if args.check and args.output_root:
        parser.error("--check cannot write to --output-root")
    if args.output_root and args.output_root.resolve().is_relative_to(ROOT) and not args.write:
        parser.error("Use --write to replace source assets")
    if args.write or args.output_root:
        target = (args.output_root or ROOT).resolve()
        outputs = render_outputs()
        if outputs != render_outputs():
            raise ValueError("Intro asset renderer is not deterministic")
        manifest = {"inputs": inputs(), "outputs": {p: digest(b) for p, b in outputs.items()}}
        outputs[MANIFEST] = (json.dumps(manifest, indent=2) + "\n").encode()
        for relative, content in outputs.items():
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        print(f"Built {len(outputs) - 1} intro textures and their manifest.")
    else:
        manifest = json.loads((ROOT / MANIFEST).read_text())
        assert inputs() == manifest["inputs"], "Source changed; rebuild explicitly with --write"
        for relative, expected in manifest["outputs"].items():
            assert digest((ROOT / relative).read_bytes()) == expected, f"Asset drift: {relative}"
        print(f"PASS: {len(manifest['outputs'])} intro textures match source manifest (no drawing).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
