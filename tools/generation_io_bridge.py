"""JSON transport for Node generators; all writes use generation_io.cli."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from generation_io import cli


def main() -> None:
    root = Path(sys.argv.pop(1))
    sys.stdin.reconfigure(encoding="utf-8")
    outputs = json.load(sys.stdin)
    cli(lambda: outputs, root=root)


if __name__ == "__main__":
    main()
