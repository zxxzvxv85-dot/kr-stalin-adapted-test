#!/usr/bin/env python3
"""Rebuild a clean draw.io focus drawing from a hand-edited reference file.

The mod author rearranges the exported drawing by hand (moving cards, hooking the
navy and air lines into the military-reform line, deleting helper boxes). This
script takes that edited file, maps every card back to its focus token, snaps the
layout to the 120 px grid and rewrites the file with the house style so the
drawing stays machine readable (card id == focus token).

Usage:
    python tools/rebuild_drawio_from_reference.py \
        --reference "$HOME/Downloads/my_layout.drawio" \
        --page "1 军事改革线（本模组）" \
        --out tools/design/RUS_three_services_focus_lines.drawio
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_focus_tree_to_drawio as exporter  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO / "tools/design/RUS_military_navy_air_focus_lines.drawio"
DEFAULT_OUT = REPO / "tools/design/RUS_three_services_focus_lines.drawio"

MODEL_ATTRS = {
    "dx": "5891",
    "dy": "731",
    "grid": "1",
    "gridSize": "10",
    "guides": "1",
    "tooltips": "1",
    "connect": "1",
    "arrows": "1",
    "fold": "1",
    "page": "1",
    "pageScale": "1",
    "pageWidth": "827",
    "pageHeight": "1169",
    "math": "0",
    "shadow": "0",
}


def label_index(paths: list[Path]) -> dict[str, str]:
    """label -> focus token, taken from the previously exported drawings."""
    index: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            continue
        for diagram in ET.parse(path).getroot().findall("diagram"):
            for cell in diagram.findall(".//mxCell"):
                if cell.get("vertex") != "1":
                    continue
                value = html.unescape(cell.get("value") or "").strip()
                cell_id = cell.get("id") or ""
                if value and re.fullmatch(r"[A-Za-z0-9_]+", cell_id):
                    index.setdefault(value, cell_id)
    return index


def parse_page(path: Path, page_name: str | None) -> ET.Element:
    root = ET.parse(path).getroot()
    pages = root.findall("diagram")
    if page_name:
        for diagram in pages:
            if diagram.get("name") == page_name:
                return diagram
        raise SystemExit(f"page not found: {page_name} (have {[d.get('name') for d in pages]})")
    if len(pages) != 1:
        raise SystemExit(f"file has {len(pages)} pages, pass --page")
    return pages[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="previous export, used for label lookup")
    parser.add_argument("--page", default=None, help="page name inside the reference file")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--name", default=None, help="page name for the rebuilt file")
    args = parser.parse_args()

    focuses = exporter.parse_focuses(exporter.DEFAULT_FOCUS_FILE)
    by_label = label_index([args.source])
    page = parse_page(args.reference, args.page)
    page_name = args.name or page.get("name") or "焦点线"

    cells = page.findall(".//mxCell")
    vertices: dict[str, dict[str, object]] = {}
    edges: list[tuple[str, str]] = []
    unresolved: list[str] = []

    for cell in cells:
        if cell.get("vertex") == "1":
            label = html.unescape(cell.get("value") or "").strip()
            cell_id = cell.get("id") or ""
            focus_id = cell_id if cell_id in focuses else by_label.get(label)
            if not focus_id:
                unresolved.append(f"{cell_id}:{label}")
                continue
            geometry = cell.find("mxGeometry")
            vertices[cell_id] = {
                "focus_id": focus_id,
                "label": label,
                "x": float(geometry.get("x", "0")),
                "y": float(geometry.get("y", "0")),
            }
        elif cell.get("edge") == "1":
            source, target = cell.get("source"), cell.get("target")
            if source and target:
                edges.append((source, target))

    if unresolved:
        print("warning: dropped cards without a focus token:", unresolved)

    xs = [float(item["x"]) for item in vertices.values()]
    ys = [float(item["y"]) for item in vertices.values()]
    min_x, min_y = min(xs), min(ys)

    def snap(value: float, origin: float) -> float:
        steps = round((value - origin) / exporter.GRID)
        return exporter.ORIGIN + steps * exporter.GRID

    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device"})
    diagram = ET.SubElement(mxfile, "diagram", {"name": page_name, "id": "page-" + page_name.split()[0]})
    model = ET.SubElement(diagram, "mxGraphModel", MODEL_ATTRS)
    mx_root = ET.SubElement(model, "root")
    ET.SubElement(mx_root, "mxCell", {"id": "0"})
    ET.SubElement(mx_root, "mxCell", {"id": "1", "parent": "0"})

    id_map: dict[str, str] = {}
    used_ids: set[str] = set()
    for cell_id, item in vertices.items():
        focus_id = str(item["focus_id"])
        target_id = focus_id
        suffix = 2
        while target_id in used_ids:
            target_id = f"{focus_id}_{suffix}"
            suffix += 1
        used_ids.add(target_id)
        id_map[cell_id] = target_id

    targets_with_parent = {
        id_map[target_id] for _source_id, target_id in edges if target_id in id_map
    }

    placed: set[tuple[float, float]] = set()
    nudged: list[str] = []
    for cell_id, item in vertices.items():
        focus_id = str(item["focus_id"])
        target_id = id_map[cell_id]

        x = snap(float(item["x"]), min_x)
        y = snap(float(item["y"]), min_y)
        if (x, y) in placed:
            x, y = exporter.free_cell((x, y), placed)
            nudged.append(f"{focus_id} -> ({x:g},{y:g})")
        placed.add((x, y))

        style = exporter.CARD_STYLE if target_id in targets_with_parent else exporter.ROOT_STYLE
        cell = ET.SubElement(
            mx_root,
            "mxCell",
            {"id": target_id, "value": html.escape(str(item["label"])), "style": style, "vertex": "1", "parent": "1"},
        )
        ET.SubElement(
            cell,
            "mxGeometry",
            {
                "x": f"{x:g}",
                "y": f"{y:g}",
                "width": f"{exporter.CARD[0]:g}",
                "height": f"{exporter.CARD[1]:g}",
                "as": "geometry",
            },
        )

    seen: set[tuple[str, str]] = set()
    edge_count = 0
    for source_id, target_id in edges:
        source = id_map.get(source_id)
        target = id_map.get(target_id)
        if not source or not target or (source, target) in seen:
            continue
        seen.add((source, target))
        cell = ET.SubElement(
            mx_root,
            "mxCell",
            {
                "id": f"edge-{edge_count}",
                "value": "",
                "style": exporter.EDGE_STYLE,
                "edge": "1",
                "parent": "1",
                "source": source,
                "target": target,
            },
        )
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        edge_count += 1

    ET.indent(mxfile)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(mxfile).write(args.out, encoding="utf-8", xml_declaration=True)
    print(f"rebuilt {len(id_map)} cards / {edge_count} edges -> {args.out} ({args.out.stat().st_size} bytes)")
    if nudged:
        print("nudged:", nudged)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
