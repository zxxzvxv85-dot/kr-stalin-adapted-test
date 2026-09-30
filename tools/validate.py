"""Run the explicitly registered read-only checks from any working directory."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("validation_checks.json")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", nargs="+", action="append", help="One or more groups; repeated groups are deduplicated")
    parser.add_argument("--list", action="store_true", help="List selected checks without running them")
    parser.add_argument("--game-root", type=Path, default=Path(os.environ.get("HOI4_GAME_ROOT", ROOT.parents[3] / "common/Hearts of Iron IV")))
    parser.add_argument("--kr-root", type=Path, default=Path(os.environ.get("HOI4_KR_ROOT", ROOT.parent / "1521695605")))
    args = parser.parse_args()
    checks = json.loads(MANIFEST.read_text(encoding="utf-8"))
    groups = {group for check in checks for group in check["groups"]}
    chosen = {value for row in args.group or [] for value in row} or {"all"}
    unknown = chosen - groups - {"all"}
    if unknown:
        parser.error("Unknown groups: " + ", ".join(sorted(unknown)) + "; available: " + ", ".join(sorted(groups)))
    selected = [check for check in checks if "all" in chosen or chosen.intersection(check["groups"])]
    if args.list:
        for check in selected:
            print(f"{check['id']}: {', '.join(check['groups'])} [{check['path']}]")
        print(f"{len(selected)} checks; groups: {', '.join(sorted(groups))}")
        return 0
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "HOI4_GAME_ROOT": str(args.game_root.resolve()), "HOI4_KR_ROOT": str(args.kr_root.resolve())}
    failed = 0
    started = time.monotonic()
    for check in selected:
        source = ROOT / check["path"]
        executable = sys.executable if source.suffix == ".py" else shutil.which("node")
        dependencies = {
            "game": args.game_root,
            "kr": args.kr_root,
            "fonts": args.game_root / "gfx/fonts",
            "technology_extension_1": ROOT.parent / "3105210203",
            "technology_extension_2": ROOT.parent / "3555444820",
        }
        missing = [f"{key}={dependencies[key]}" for key in check.get("requires", []) if not dependencies[key].is_dir()]
        if not source.is_file(): missing.append(str(source))
        if not executable: missing.append("Node.js executable on PATH")
        if missing:
            failed += 1
            print(f"MISSING {check['id']}: " + "; ".join(missing), flush=True)
            continue
        arguments = [str(args.game_root / "gfx/fonts") if value == "{fonts}" else value for value in check.get("args", [])]
        try:
            result = subprocess.run([executable, str(source), *arguments], cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        except (OSError, subprocess.TimeoutExpired) as error:
            failed += 1
            print(f"ERROR {check['id']}: {error}", flush=True)
            continue
        if result.returncode:
            failed += 1
            print(f"FAIL {check['id']} (exit {result.returncode})", flush=True)
            print((result.stdout + result.stderr).rstrip(), flush=True)
        else:
            print(f"PASS {check['id']}", flush=True)
    print(f"{len(selected) - failed}/{len(selected)} passed; {failed} failed or missing dependencies; {time.monotonic() - started:.1f}s. These are static/fixture checks, not HOI4 runtime validation.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
