"""Shared, read-only-by-default interface for maintained text generators.

Renderers return relative paths and Unicode text. Only this module writes files;
YAML receives a UTF-8 BOM and Paradox scripts do not. Line endings are compared
as text so a checkout's CRLF policy does not cause false generation drift.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Callable


def encoded(path: str, content: str) -> bytes:
    content = content.removeprefix("\ufeff").replace("\r\n", "\n")
    return content.encode("utf-8-sig" if path.endswith(".yml") else "utf-8")


def process_outputs(outputs: dict[str, str], root: Path, *, write: bool) -> int:
    root = root.resolve()
    differences = []
    pending = []
    targets = set()
    for relative, content in sorted(outputs.items()):
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or Path(relative).is_absolute():
            raise ValueError(f"Output escapes root: {relative}")
        if target in targets:
            raise ValueError(f"Multiple output paths resolve to the same file: {relative}")
        if any(prior in target.parents or target in prior.parents for prior in targets):
            raise ValueError(f"Output paths overlap as a file and directory: {relative}")
        targets.add(target)
        if target.exists() and not target.is_file():
            raise ValueError(f"Output target is not a regular file: {relative}")
        for parent in target.parents:
            if parent == root.parent:
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"Output parent is not a directory: {relative}")
        expected = encoded(relative, content)
        actual = target.read_bytes().replace(b"\r\n", b"\n") if target.is_file() else None
        if actual == expected:
            continue
        differences.append(relative)
        pending.append((target, expected))
    # Complete path and encoding validation before replacing any generated file.
    if write:
        for target, expected in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected)
    for relative in differences:
        print(f"{'WROTE' if write else 'DRIFT'} {relative}")
    print(f"{'Generated' if write else 'Checked'} {len(outputs)} outputs; {len(differences)} differences.")
    return 0 if write or not differences else 1


def cli(render_outputs: Callable[[], dict[str, str]], *, root: Path,
        description: str = "Generate maintained mod text", kr_dependency: bool = False) -> None:
    parser = argparse.ArgumentParser(description=description)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Read-only comparison (default)")
    mode.add_argument("--write", action="store_true", help="Update generated files in the source tree")
    parser.add_argument("--output-root", type=Path, help="Render into a separate directory, leaving source untouched")
    parser.add_argument("--kr-root", type=Path, help="Override the installed KR comparison source")
    args = parser.parse_args()
    if args.check and args.output_root:
        parser.error("--check and --output-root are mutually exclusive")
    if args.kr_root:
        os.environ["HOI4_KR_ROOT"] = str(args.kr_root.resolve())
    if args.output_root and args.output_root.resolve().is_relative_to(root.resolve()) and not args.write:
        parser.error("Use --write to update a directory inside the source root")
    try:
        if kr_dependency:
            from kr_generation_baseline import verify
            verify(root)
        outputs = render_outputs()
        # Catch order-dependent accumulators before either checking or writing.
        if outputs != render_outputs():
            raise ValueError("Renderer is not deterministic within one process")
        result = process_outputs(outputs, args.output_root or root,
                                 write=args.write or args.output_root is not None)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Generation failed: {error}\n")
    raise SystemExit(result)
