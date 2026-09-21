"""Apply the grid layout of one draw.io page onto the matching HOI4 focuses.

The draw.io design file places every focus on a 120x120 pixel lattice. This
tool converts those pixel positions into the focus tree grid (x right, y down,
one unit per cell) relative to one reference focus, then rewrites the ``x`` and
``y`` lines of the matching focus blocks in the focus file.

Only the focus blocks between ``--start-marker`` and ``--end-marker`` are
touched, so a single page that covers several branches can be applied branch by
branch. Run without ``--apply`` for a dry-run table.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CELL = 120


def parse_page(path: Path, page_prefix: str) -> dict[str, tuple[str, float, float]]:
    root = ET.parse(path).getroot()
    pages = [page for page in root.iter("diagram") if (page.get("name") or "").startswith(page_prefix)]
    if len(pages) != 1:
        raise SystemExit(f"expected exactly one page starting with {page_prefix!r}, found {len(pages)}")
    nodes: dict[str, tuple[str, float, float]] = {}
    for cell in pages[0].iter("mxCell"):
        if cell.get("vertex") != "1":
            continue
        geometry = cell.find("mxGeometry")
        if geometry is None:
            continue
        nodes[cell.get("id")] = (
            cell.get("value") or "",
            float(geometry.get("x")),
            float(geometry.get("y")),
        )
    return nodes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drawio", required=True, type=Path)
    parser.add_argument("--page", required=True, help="page name prefix, e.g. '1 '")
    parser.add_argument("--root", required=True, help="focus id whose draw.io pixel is the grid origin")
    parser.add_argument("--focus-file", required=True, type=Path)
    parser.add_argument("--start-marker", required=True)
    parser.add_argument("--end-marker", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    nodes = parse_page(args.drawio, args.page)
    if args.root not in nodes:
        raise SystemExit(f"reference focus {args.root} is not on this page")
    origin_x, origin_y = nodes[args.root][1], nodes[args.root][2]

    raw = args.focus_file.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    start = text.index(args.start_marker)
    end = text.index(args.end_marker, start)
    head, section, tail = text[:start], text[start:end], text[end:]

    changed = 0
    rows: list[str] = []
    for block in re.finditer(r"focus\s*=\s*\{.*?\n\t\}", section, re.S):
        block_text = block.group(0)
        focus_id = re.search(r"^\s*id\s*=\s*(\w+)", block_text, re.M)
        if not focus_id:
            continue
        focus_id = focus_id.group(1)
        if focus_id == args.root:
            rows.append(f"{focus_id:52} kept (grid origin)")
            continue
        relative = re.search(r"^\s*relative_position_id\s*=\s*(\w+)", block_text, re.M)
        if not relative or relative.group(1) != args.root:
            rows.append(
                f"{focus_id:52} skipped (relative_position_id = {relative.group(1) if relative else 'none'})"
            )
            continue
        if focus_id not in nodes:
            rows.append(f"{focus_id:52} skipped (not on the draw.io page)")
            continue
        pixel_x, pixel_y = nodes[focus_id][1], nodes[focus_id][2]
        target_x = int(round((pixel_x - origin_x) / CELL))
        target_y = int(round((pixel_y - origin_y) / CELL))
        current_x = re.search(r"^\s*x\s*=\s*(-?\d+)", block_text, re.M)
        current_y = re.search(r"^\s*y\s*=\s*(-?\d+)", block_text, re.M)
        current = (int(current_x.group(1)), int(current_y.group(1))) if current_x and current_y else None
        target = (target_x, target_y)
        flag = "" if current == target else "  <-- change"
        rows.append(f"{focus_id:52} {str(current):>10} -> {str(target):>10}{flag}")
        if current == target:
            continue
        updated = re.sub(r"^(\s*x\s*=\s*)-?\d+", rf"\g<1>{target_x}", block_text, count=1, flags=re.M)
        updated = re.sub(r"^(\s*y\s*=\s*-?)\d+", rf"\g<1>{target_y}", updated, count=1, flags=re.M)
        section = section.replace(block_text, updated, 1)
        changed += 1

    print("\n".join(rows))
    print(f"\n{changed} focus block(s) differ from the drawing")
    if not args.apply:
        return 0
    if changed == 0:
        print("nothing to write")
        return 0
    payload = (head + section + tail).encode("utf-8")
    args.focus_file.write_bytes((b"\xef\xbb\xbf" if has_bom else b"") + payload)
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
