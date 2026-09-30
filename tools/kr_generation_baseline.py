"""Pin the upstream inputs that determine which advisor/idea effects we own.

KR itself is always read-only. Updating this local manifest is a deliberate
maintenance action after reviewing an upstream update, never part of generation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def kr_root(root: Path = ROOT) -> Path:
    return Path(os.environ.get("HOI4_KR_ROOT", str(root.parent / "1521695605"))).resolve()


def inputs(root: Path) -> dict[str, str | None]:
    upstream = kr_root(root)
    if not (upstream / "descriptor.mod").is_file():
        raise ValueError(f"KR descriptor missing: {upstream}")
    paths = {"descriptor.mod"}
    paths.update(p.relative_to(upstream).as_posix() for p in (upstream / "common/country_leader").glob("*.txt"))
    paths.update(p.relative_to(root).as_posix() for p in (root / "common/ideas").glob("*.txt"))
    return {p: hashlib.sha256((upstream / p).read_bytes()).hexdigest()
            if (upstream / p).is_file() else None for p in sorted(paths)}


def verify(root: Path = ROOT) -> None:
    manifest = root / "tools/kr_generation_baseline.json"
    if not manifest.exists():
        raise ValueError("Missing KR baseline; review dependencies and explicitly record it")
    expected = json.loads(manifest.read_text(encoding="utf-8"))["files"]
    actual = inputs(root)
    changed = sorted(p for p in expected.keys() | actual.keys() if p not in expected or p not in actual or expected[p] != actual[p])
    if changed:
        raise ValueError("KR inputs changed; review before --record: " + ", ".join(changed))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true", help="Explicitly accept reviewed upstream inputs")
    parser.add_argument("--kr-root", type=Path)
    args = parser.parse_args()
    if args.kr_root:
        os.environ["HOI4_KR_ROOT"] = str(args.kr_root.resolve())
    if args.record:
        data = {"purpose": "KR comparison inputs for easy-mode advisors and ideas", "files": inputs(ROOT)}
        (ROOT / "tools/kr_generation_baseline.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"Recorded {len(data['files'])} KR inputs")
    else:
        verify()
        print("KR generation baseline unchanged")


if __name__ == "__main__":
    main()
