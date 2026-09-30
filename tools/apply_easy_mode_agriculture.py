"""Check agricultural easy-mode effects against their canonical generator.

Kept as a compatible command name. The complete agriculture renderer now owns
these branches; no marker-based search-and-replace is performed on game files.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from generation_io import cli

ROOT = Path(__file__).resolve().parents[1]
TARGET = "common/scripted_effects/RUS_national_agriculture_effects.txt"


def render_outputs() -> dict[str, str]:
    generated = json.loads(subprocess.check_output(
        ["node", str(ROOT / "tools/generate_national_agriculture.cjs"), "--base-json"],
        cwd=ROOT, encoding="utf-8",
    ))
    return {TARGET: generated[TARGET]}


if __name__ == "__main__":
    cli(render_outputs, root=ROOT, description=__doc__)
