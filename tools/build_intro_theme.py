"""Build the flat, geometric intro skin; default checks hashes without drawing.

The title is copied byte-for-byte from the approved ImageGen source. Everything
else is a blank UI surface drawn from geometry; text remains live HOI4 content.
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
MANIFEST = "tools/art_sources/intro_theme_manifest.json"
FOLDER = "gfx/interface/rus_intro_theme/"
TITLE = "gfx/interface/rus_intro_header/constructivist_title.png"
INK = "#181917"
PAPER = "#e4d2ad"
RED = "#ad251c"
LINE = "#746b58"
BODY = "#101210"


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def inputs() -> dict[str, str]:
    return {
        SOURCE: digest((ROOT / SOURCE).read_bytes()),
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

    im, d = canvas("frame", (728, 488), INK)
    d.rectangle((0, 0, 727, 487), outline=PAPER, width=2)
    d.rectangle((3, 3, 724, 484), outline=LINE, width=1)
    d.rectangle((4, 4, 723, 10), fill=RED)
    d.polygon([(5, 482), (191, 482), (178, 487), (0, 487)], fill=RED)
    for x in (645, 667, 689):
        d.polygon([(x, 487), (x + 15, 487), (x + 28, 472), (x + 13, 472)], fill=PAPER)
    save("frame", im)

    im, d = canvas("bridge", (728, 36))
    d.polygon([(0, 36), (0, 25), (71, 6), (533, 18), (672, 0), (728, 25), (728, 36)], fill=INK)
    d.polygon([(0, 25), (71, 6), (145, 8), (0, 34)], fill=RED)
    d.polygon([(576, 22), (672, 0), (714, 18), (614, 30)], fill=RED)
    d.line([(1, 32), (150, 9)], fill=PAPER, width=2)
    save("bridge", im)

    for name, size, fill, border in [
        ("panel", (720, 480), INK, None),
        ("content_border", (696, 400), BODY, LINE),
        ("content", (688, 392), BODY, None),
        ("portrait_back", (172, 392), BODY, LINE),
        ("page", (76, 31), INK, LINE),
    ]:
        im, d = canvas(name, size, fill)
        if border:
            d.rectangle((0, 0, size[0] - 1, size[1] - 1), outline=border)
        if name == "panel":
            d.rectangle((4, 3, 715, 6), fill=RED)
            d.line([(12, 65), (708, 65)], fill=LINE)
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
            fill = RED if name == "continue" or frame == 1 else INK
            box = (x + 1, 1, x + w - 2, h - 2)
            if name == "checkbox":
                d.rectangle((x + 2, 2, x + 22, 21), fill=INK, outline=LINE)
                if frame:
                    d.rectangle((x + 3, 3, x + 21, 20), fill=RED)
                    d.line([(x + 6, 12), (x + 10, 16), (x + 19, 7)], fill=PAPER, width=2)
            else:
                d.rectangle(box, fill=fill, outline=PAPER if frame or name == "continue" else LINE, width=1)
                d.rectangle((x + 1, h - 5, x + w - 2, h - 2), fill=PAPER if frame else RED)
                if name in ("back", "forward"):
                    tip = 12 if name == "back" else 29
                    tail = 28 if name == "back" else 13
                    d.polygon([(x + tip, 21), (x + tail, 11), (x + tail, 31)], fill=PAPER)
                elif name == "continue":
                    d.polygon([(17, 14), (29, 14), (40, 30), (29, 45), (17, 45), (28, 30)], fill=PAPER)
                    d.polygon([(206, 14), (218, 14), (229, 30), (218, 45), (206, 45), (217, 30)], fill=PAPER)
                elif name == "spoilers":
                    d.rectangle((x + 8, 9, x + 23, 24), outline=PAPER)
                    if frame:
                        d.line([(x + 10, 17), (x + 15, 22), (x + 23, 11)], fill=PAPER, width=2)
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
