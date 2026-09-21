#!/usr/bin/env python3
"""Export focus-tree branches to a draw.io file.

The layout follows the conventions of the foreign-policy skeleton drawing the
team already uses (`tools/import_drawio_focus_skeleton.py` reverses this):

* one card per focus, 120x60 px, one grid step of 120 px between focuses
* card text is the Chinese focus name
* prerequisites are drawn as orthogonal bottom-to-top arrows (parent -> child)
* a focus with several prerequisites in one group becomes several arrows (OR)

Coordinates come from the focus file itself (x/y plus `relative_position_id`
chains), so the drawing matches the in-game layout. Conditional `offset`
blocks are ignored.

Usage:
    python tools/export_focus_tree_to_drawio.py \
        --out tools/design/RUS_military_navy_air_focus_lines.drawio
"""

from __future__ import annotations

import argparse
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_FOCUS_FILE = REPO / "common/national_focus/RUS focus (Russia).txt"
DEFAULT_OUT = REPO / "tools/design/RUS_military_navy_air_focus_lines.drawio"
LOCALISATION_ROOTS = (
    REPO,
    Path(r"D:\steam\steamapps\workshop\content\394360\2946487287"),
)
SCRIPTED_LOC_ROOTS = (
    REPO,
    Path(r"D:\steam\steamapps\workshop\content\394360\1521695605"),
)

GRID = 120.0
ORIGIN = 40.0
CARD = (120.0, 60.0)
CARD_STYLE = "whiteSpace=wrap;html=1;"
ROOT_STYLE = "rounded=0;whiteSpace=wrap;html=1;"
EXTERNAL_STYLE = "dashed=1;whiteSpace=wrap;html=1;fontColor=#666666;strokeColor=#999999;"
EDGE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
    "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
)
EXTERNAL_EDGE_STYLE = EDGE_STYLE + "dashed=1;strokeColor=#999999;"

# line name -> branch roots
LINES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("1 军事改革线（本模组）", ("RUS_fr_post_revolutionary_armed_forces",)),
    ("2 陆军线", ("RUS_address_the_army",)),
    ("3 海军线", ("RUS_inspect_VMFR",)),
    ("4 空军线", ("RUS_evaluate_VVFR",)),
)


@dataclass
class Focus:
    id: str
    x: int | None = None
    y: int | None = None
    relative_to: str | None = None
    prerequisites: list[list[str]] = field(default_factory=list)


def split_focus_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    for match in re.finditer(r"^\s*focus\s*=\s*\{", text, re.M):
        start = match.end() - 1
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(text[start : index + 1])
                    break
    return blocks


def parse_focuses(path: Path) -> dict[str, Focus]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    focuses: dict[str, Focus] = {}
    for block in split_focus_blocks(text):
        focus_id = re.search(r"^\s*id\s*=\s*([A-Za-z0-9_]+)", block, re.M)
        if not focus_id:
            continue

        def number(key: str) -> int | None:
            match = re.search(r"^\s*" + key + r"\s*=\s*(-?\d+)", block, re.M)
            return int(match.group(1)) if match else None

        relative = re.search(r"^\s*relative_position_id\s*=\s*([A-Za-z0-9_]+)", block, re.M)
        groups = [
            re.findall(r"focus\s*=\s*([A-Za-z0-9_]+)", group)
            for group in re.findall(r"prerequisite\s*=\s*\{([^}]*)\}", block)
        ]
        focuses[focus_id.group(1)] = Focus(
            id=focus_id.group(1),
            x=number("x"),
            y=number("y"),
            relative_to=relative.group(1) if relative else None,
            prerequisites=[group for group in groups if group],
        )
    return focuses


def absolute_position(focuses: dict[str, Focus], focus_id: str, seen: frozenset[str] = frozenset()) -> tuple[int, int]:
    focus = focuses[focus_id]
    if focus_id in seen:
        return (0, 0)
    x = focus.x or 0
    y = focus.y or 0
    if focus.relative_to and focus.relative_to in focuses:
        parent_x, parent_y = absolute_position(focuses, focus.relative_to, seen | {focus_id})
        return (parent_x + x, parent_y + y)
    return (x, y)


def load_localisation(roots: tuple[Path, ...], language: str = "simp_chinese") -> dict[str, str]:
    names: dict[str, str] = {}
    for root in roots:
        folder = root / "localisation" / language
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*.yml")):
            for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                match = re.match(r'\s*([A-Za-z0-9_.]+):\d*\s+"(.*)"\s*$', line)
                if match:
                    names.setdefault(match.group(1), match.group(2))
    return names


def load_scripted_loc_defaults(roots: tuple[Path, ...]) -> dict[str, str]:
    """defined_text name -> localisation key of its default (last) variant."""
    defaults: dict[str, str] = {}
    for root in roots:
        folder = root / "common/scripted_localisation"
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*.txt")):
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            for block in re.finditer(r"defined_text\s*=\s*\{", text):
                start = block.end() - 1
                depth = 0
                for index in range(start, len(text)):
                    if text[index] == "{":
                        depth += 1
                    elif text[index] == "}":
                        depth -= 1
                        if depth == 0:
                            body = text[start : index + 1]
                            break
                else:
                    continue
                name = re.search(r"name\s*=\s*([A-Za-z0-9_]+)", body)
                keys = re.findall(r"localization_key\s*=\s*([A-Za-z0-9_]+)", body)
                if name and keys:
                    defaults.setdefault(name.group(1), keys[-1])
    return defaults


def resolve_label(
    focus_id: str,
    names: dict[str, str],
    fallback_names: dict[str, str],
    scripted: dict[str, str],
) -> str:
    """Turn the localisation value into a readable card label."""
    value = names.get(focus_id, focus_id)

    def lookup(key: str) -> str | None:
        return names.get(key) or fallback_names.get(key)

    for _ in range(4):
        match = re.search(r"[\[$]([A-Za-z0-9_.]+)[\]$]", value)
        if not match:
            break
        key = match.group(1)
        replacement = lookup(key) or lookup(scripted.get(key, "")) or fallback_names.get(key)
        if not replacement or replacement == value:
            return focus_id
        value = value[: match.start()] + replacement + value[match.end() :]
    if re.search(r"[\[$£§]", value):
        return focus_id
    return value.strip() or focus_id


def branch_focuses(focuses: dict[str, Focus], roots: tuple[str, ...]) -> set[str]:
    children: dict[str, set[str]] = {}
    for focus in focuses.values():
        for group in focus.prerequisites:
            for parent in group:
                if parent in focuses:
                    children.setdefault(parent, set()).add(focus.id)

    selected: set[str] = set()
    queue = [root for root in roots if root in focuses]
    while queue:
        node = queue.pop()
        if node in selected:
            continue
        selected.add(node)
        queue.extend(children.get(node, ()))
    return selected


def external_parents(focuses: dict[str, Focus], selected: set[str]) -> dict[str, set[str]]:
    """focus id -> prerequisite focuses that live outside the drawn branch."""
    found: dict[str, set[str]] = {}
    for focus_id in selected:
        for group in focuses[focus_id].prerequisites:
            for parent in group:
                if parent in focuses and parent not in selected:
                    found.setdefault(focus_id, set()).add(parent)
    return found


def cell(box_x: float, box_y: float) -> tuple[float, float]:
    return (ORIGIN + box_x * GRID, ORIGIN + box_y * GRID)


def free_cell(preferred: tuple[float, float], occupied: set[tuple[float, float]]) -> tuple[float, float]:
    """Conditional focuses can share a grid cell in the focus file; nudge them apart."""
    if preferred not in occupied:
        return preferred
    for radius in range(1, 12):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            candidate = (preferred[0] + dx * radius, preferred[1] + dy * radius)
            if candidate not in occupied:
                return candidate
    return preferred


def tidy_positions(
    focuses: dict[str, Focus],
    selected: set[str],
) -> dict[str, tuple[float, float]]:
    """Absolute focus positions, with children pushed below their prerequisites.

    A few KR focuses hang off a `relative_position_id` that lives in another part
    of the tree, which would draw them above their own prerequisite. Those are
    re-anchored one row below the parents and empty rows/columns are dropped so
    the branch reads as one grid, like the hand-drawn skeleton layouts.
    """
    raw = {focus_id: absolute_position(focuses, focus_id) for focus_id in selected}
    positions = dict(raw)

    order = sorted(selected, key=lambda item: (raw[item][1], raw[item][0], item))
    for focus_id in order:
        parents = [
            parent
            for group in focuses[focus_id].prerequisites
            for parent in group
            if parent in selected and parent in positions
        ]
        if not parents:
            continue
        lowest_parent = max(positions[parent][1] for parent in parents)
        if positions[focus_id][1] > lowest_parent:
            continue
        positions[focus_id] = (positions[focus_id][0], lowest_parent + 1)

    occupied: set[tuple[float, float]] = set()
    for focus_id in order:
        placed = free_cell(positions[focus_id], occupied)
        positions[focus_id] = placed
        occupied.add(placed)

    # drop empty rows/columns so the drawing does not carry the whole tree's gaps
    columns = sorted({position[0] for position in positions.values()})
    rows = sorted({position[1] for position in positions.values()})
    column_index = {value: index for index, value in enumerate(columns)}
    row_index = {value: index for index, value in enumerate(rows)}
    return {focus_id: (column_index[x], row_index[y]) for focus_id, (x, y) in positions.items()}


def build_page(
    name: str,
    focuses: dict[str, Focus],
    selected: set[str],
    roots: tuple[str, ...],
    names: dict[str, str],
    fallback_names: dict[str, str],
    scripted: dict[str, str],
) -> ET.Element:
    externals = external_parents(focuses, selected)
    positions = tidy_positions(focuses, selected)

    # external prerequisites are drawn on a virtual row above their first child
    external_children: dict[str, list[str]] = {}
    for focus_id, parents in externals.items():
        for parent in parents:
            external_children.setdefault(parent, []).append(focus_id)
    external_positions: dict[str, tuple[float, float]] = {}
    for parent, children in external_children.items():
        anchor = min((positions[child] for child in children), key=lambda value: (value[1], value[0]))
        external_positions[parent] = (anchor[0], anchor[1] - 1)

    occupied: set[tuple[float, float]] = set(positions.values())
    for parent in sorted(external_positions):
        external_positions[parent] = free_cell(external_positions[parent], occupied)
        occupied.add(external_positions[parent])

    all_x = [value[0] for value in positions.values()] + [value[0] for value in external_positions.values()]
    all_y = [value[1] for value in positions.values()] + [value[1] for value in external_positions.values()]
    min_x, min_y = min(all_x), min(all_y)

    diagram = ET.Element("diagram", {"name": name, "id": "page-" + name.split()[0]})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
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
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    def add_vertex(cell_id: str, label: str, gx: float, gy: float, style: str) -> None:
        cell_element = ET.SubElement(
            root, "mxCell", {"id": cell_id, "value": html.escape(label), "style": style, "vertex": "1", "parent": "1"}
        )
        x, y = cell(gx - min_x, gy - min_y)
        ET.SubElement(
            cell_element,
            "mxGeometry",
            {"x": f"{x:g}", "y": f"{y:g}", "width": f"{CARD[0]:g}", "height": f"{CARD[1]:g}", "as": "geometry"},
        )

    def add_edge(edge_id: str, source: str, target: str, style: str) -> None:
        element = ET.SubElement(
            root,
            "mxCell",
            {"id": edge_id, "value": "", "style": style, "edge": "1", "parent": "1", "source": source, "target": target},
        )
        ET.SubElement(element, "mxGeometry", {"relative": "1", "as": "geometry"})

    for focus_id in sorted(selected):
        gx, gy = positions[focus_id]
        style = ROOT_STYLE if focus_id in roots else CARD_STYLE
        add_vertex(focus_id, resolve_label(focus_id, names, fallback_names, scripted), gx, gy, style)

    external_ids: dict[str, str] = {}
    for index, (parent, (gx, gy)) in enumerate(sorted(external_positions.items())):
        external_ids[parent] = f"external-{index}"
        add_vertex(
            external_ids[parent],
            f"（前置）{resolve_label(parent, names, fallback_names, scripted)}",
            gx,
            gy,
            EXTERNAL_STYLE,
        )

    edge_index = 0
    for focus_id in sorted(selected):
        for group in focuses[focus_id].prerequisites:
            for parent in group:
                if parent in selected:
                    add_edge(f"edge-{edge_index}", parent, focus_id, EDGE_STYLE)
                    edge_index += 1
                elif parent in external_positions:
                    add_edge(f"edge-{edge_index}", external_ids[parent], focus_id, EXTERNAL_EDGE_STYLE)
                    edge_index += 1

    print(
        f"{name}: focuses={len(selected)} edges={edge_index} externals={len(external_positions)} "
        f"grid={int(max(all_x) - min_x) + 1}x{int(max(all_y) - min_y) + 1}"
    )
    return diagram


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--focus-file", type=Path, default=DEFAULT_FOCUS_FILE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    focuses = parse_focuses(args.focus_file)
    names = load_localisation(LOCALISATION_ROOTS)
    english = load_localisation(LOCALISATION_ROOTS, "english")
    scripted = load_scripted_loc_defaults(SCRIPTED_LOC_ROOTS)
    print(
        f"parsed {len(focuses)} focuses, {len(names)} zh keys, {len(english)} en keys, "
        f"{len(scripted)} scripted-loc names"
    )

    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device"})
    for name, roots in LINES:
        selected = branch_focuses(focuses, roots)
        if not selected:
            print(f"!! {name}: no focuses found, skipped")
            continue
        mxfile.append(build_page(name, focuses, selected, roots, names, english, scripted))

    ET.indent(mxfile)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(mxfile)
    tree.write(args.out, encoding="utf-8", xml_declaration=True)
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
