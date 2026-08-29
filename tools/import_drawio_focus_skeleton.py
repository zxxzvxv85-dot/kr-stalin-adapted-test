#!/usr/bin/env python3
"""Import the named focus skeleton from a draw.io layout.

The importer keeps the source layout's named vertices and valid named edges,
then places the resulting placeholder branch safely to the right of the
existing Russia focus tree. Re-running it is idempotent.
"""

from __future__ import annotations

import argparse
import html
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path


REFERENCE_BEGIN = "\t# BEGIN RUS future foreign-policy skeleton"
REFERENCE_END = "\t# END RUS future foreign-policy skeleton"
EXPECTED_VERTEX_COUNT = 63
X_ORIGIN = 0
Y_ORIGIN = 17
DRAWIO_X_STEP = 120.0
DRAWIO_Y_STEP = 120.0


def clean_label(value: str | None) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("\xa0", " ").strip()


def round_grid(value: float) -> int:
    return math.floor(value + 0.5)


def parse_layout(path: Path) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    root = ET.parse(path).getroot()
    cells = root.findall(".//mxCell")
    vertices: list[dict[str, object]] = []
    by_cell_id: dict[str, dict[str, object]] = {}

    for cell in cells:
        if cell.get("vertex") != "1":
            continue
        label = clean_label(cell.get("value"))
        if not label:
            continue
        geometry = cell.find("mxGeometry")
        if geometry is None:
            raise RuntimeError(f"named vertex has no geometry: {label}")
        vertex = {
            "cell_id": cell.get("id", ""),
            "label": label,
            "raw_x": float(geometry.get("x", "0")),
            "raw_y": float(geometry.get("y", "0")),
        }
        vertices.append(vertex)
        by_cell_id[str(vertex["cell_id"])] = vertex

    if len(vertices) != EXPECTED_VERTEX_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_VERTEX_COUNT} named vertices, found {len(vertices)}"
        )
    labels = [str(vertex["label"]) for vertex in vertices]
    if len(labels) != len(set(labels)):
        raise RuntimeError("draw.io layout contains duplicate named vertices")

    min_x = min(float(vertex["raw_x"]) for vertex in vertices)
    min_y = min(float(vertex["raw_y"]) for vertex in vertices)
    for vertex in vertices:
        vertex["x"] = X_ORIGIN + round_grid(
            (float(vertex["raw_x"]) - min_x) / DRAWIO_X_STEP
        )
        vertex["y"] = Y_ORIGIN + round_grid(
            (float(vertex["raw_y"]) - min_y) / DRAWIO_Y_STEP
        )

    vertices.sort(key=lambda item: (int(item["y"]), int(item["x"]), str(item["label"])))
    for index, vertex in enumerate(vertices, start=1):
        vertex["focus_id"] = f"RUS_future_foreign_{index:03d}"

    incoming: list[tuple[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()
    for cell in cells:
        if cell.get("edge") != "1":
            continue
        source = by_cell_id.get(cell.get("source", ""))
        target = by_cell_id.get(cell.get("target", ""))
        if source is None or target is None or source is target:
            continue
        edge = (str(source["focus_id"]), str(target["focus_id"]))
        if edge not in seen_edges:
            seen_edges.add(edge)
            incoming.append(edge)

    positions: dict[tuple[int, int], str] = {}
    for vertex in vertices:
        position = (int(vertex["x"]), int(vertex["y"]))
        if position in positions:
            raise RuntimeError(
                f"focus position collision: {positions[position]} and {vertex['label']}"
            )
        positions[position] = str(vertex["label"])

    return vertices, incoming


def render_shared_focuses(
    vertices: list[dict[str, object]], edges: list[tuple[str, str]]
) -> str:
    prerequisites: dict[str, list[str]] = {
        str(vertex["focus_id"]): [] for vertex in vertices
    }
    for source, target in edges:
        prerequisites[target].append(source)

    lines = [
        "############################################################################################################",
        "# Future Socialist Foreign Policy - layout skeleton imported from draw.io",
        "# Placeholder focuses intentionally have no icon, description, or completion reward.",
        "############################################################################################################",
        "",
    ]
    for vertex in vertices:
        focus_id = str(vertex["focus_id"])
        lines.extend(
            [
                f"# {vertex['label']}",
                "shared_focus = {",
                f"\tid = {focus_id}",
                "\tcost = 7",
                "",
                f"\tx = {vertex['x']}",
                f"\ty = {vertex['y']}",
                "",
                "\tallow_branch = { has_socialist_government = yes }",
                "\tavailable = { always = no }",
            ]
        )
        for prerequisite in prerequisites[focus_id]:
            lines.append(f"\tprerequisite = {{ focus = {prerequisite} }}")
        lines.extend(["\tai_will_do = { factor = 0 }", "}", ""])
    return "\n".join(lines)


def render_references(vertices: list[dict[str, object]]) -> str:
    rows = [REFERENCE_BEGIN]
    rows.extend(f"\tshared_focus = {vertex['focus_id']}" for vertex in vertices)
    rows.append(REFERENCE_END)
    return "\n".join(rows)


def update_focus_tree(path: Path, references: str) -> None:
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    newline = "\r\n" if raw.count(b"\r\n") > raw.count(b"\n") / 2 else "\n"
    text = raw.decode("utf-8-sig")
    block_pattern = re.compile(
        rf"{re.escape(REFERENCE_BEGIN)}.*?{re.escape(REFERENCE_END)}",
        flags=re.DOTALL,
    )
    if block_pattern.search(text):
        updated = block_pattern.sub(references, text, count=1)
    else:
        marker = "\tdefault = no\n"
        if marker not in text:
            raise RuntimeError(f"focus tree insertion marker not found: {path}")
        updated = text.replace(marker, f"{marker}\n{references}\n", 1)
    normalised = updated.replace("\r\n", "\n").replace("\n", newline)
    encoded = normalised.encode("utf-8")
    path.write_bytes((b"\xef\xbb\xbf" if has_bom else b"") + encoded)


def write_chinese_localisation(path: Path, vertices: list[dict[str, object]]) -> None:
    lines = ["l_simp_chinese:"]
    for vertex in vertices:
        label = str(vertex["label"]).replace('"', '\\"')
        lines.append(f' {vertex["focus_id"]}:0 "{label}"')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("drawio", type=Path)
    parser.add_argument(
        "--mod-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()

    mod_root = args.mod_root.resolve()
    vertices, edges = parse_layout(args.drawio.resolve())
    shared_path = (
        mod_root
        / "common"
        / "national_focus"
        / "00_RUS_future_foreign_policy_skeleton.txt"
    )
    tree_path = mod_root / "common" / "national_focus" / "RUS focus (Russia).txt"
    loc_path = (
        mod_root
        / "localisation"
        / "simp_chinese"
        / "RUS_future_foreign_policy_skeleton_l_simp_chinese.yml"
    )

    shared_path.write_text(
        render_shared_focuses(vertices, edges), encoding="utf-8", newline="\n"
    )
    update_focus_tree(tree_path, render_references(vertices))
    write_chinese_localisation(loc_path, vertices)

    print(f"wrote {len(vertices)} placeholder focuses and {len(edges)} valid links")
    print(f"focus definitions: {shared_path}")
    print(f"focus references:  {tree_path}")
    print(f"localisation:      {loc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
