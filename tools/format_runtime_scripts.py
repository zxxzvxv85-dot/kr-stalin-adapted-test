"""Expand long handwritten Paradox script lines without changing tokens or scope.

Default/--check is read-only and returns 1 if formatting is outstanding.
--list prints the candidate files without changing them. --write explicitly
applies only verified whitespace changes; generated and upstream files are excluded.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import os
import re

from hoi4_politics_blocks import parse


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = Path(os.environ.get("HOI4_KR_ROOT", ROOT.parent / "1521695605"))
FOLDERS = (
    "common/scripted_effects",
    "common/scripted_triggers",
    "common/on_actions",
    "common/decisions",
    "events",
)
MAX_LINE_LENGTH = 200
TOKEN = re.compile(r'#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}]|[<>!=]=?|[^\s{}=<>!#]+')
OPERATOR = {"=", "<", ">", "<=", ">=", "!=", "!"}
EXCLUDED_NAME = re.compile(r"RUS_national_agriculture|tesla|RUS_easy_mode|relationship.*tier", re.I)
GENERATED_HEADER = re.compile(r"(?im)^\s*#.*(?:auto.?generated|generated\b|do not edit|自动生成)")


def tokens(text: str) -> list[str]:
    """Keep comments as tokens, unlike the syntax parser used for the second check."""
    return [match[0] for match in TOKEN.finditer(text)]


def assert_equivalent(before: str, after: str) -> None:
    if tokens(before) != tokens(after):
        raise ValueError("Formatting changed the token/comment sequence")
    if [node.norm() for node in parse(before)] != [node.norm() for node in parse(after)]:
        raise ValueError("Formatting changed the parsed script structure")


def expand_line(parts: list[str], depth: int) -> list[str]:
    result: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            result.append("\t" * depth + " ".join(current))
            current.clear()

    for index, part in enumerate(parts):
        if part.startswith("#"):
            if current:
                current.append(part)
                flush()
            elif result:
                result[-1] += " " + part
            else:
                result.append("\t" * depth + part)
        elif part == "{":
            current.append(part)
            flush()
            depth += 1
        elif part == "}":
            flush()
            depth -= 1
            if depth < 0:
                raise ValueError("Unexpected closing brace")
            current.append(part)
            flush()
        else:
            # A key/operator pair starts a new statement, while lists of bare
            # identifiers stay together. Quoted strings always remain one token.
            if index + 1 < len(parts) and parts[index + 1] in OPERATOR and current:
                flush()
            current.append(part)
    flush()
    return result


def format_text(text: str, threshold: int = MAX_LINE_LENGTH) -> tuple[str, int]:
    newline = "\r\n" if "\r\n" in text else "\n"
    output: list[str] = []
    changed = 0
    depth = 0
    offset = 0
    # Do not touch a physical line intersecting a quoted multiline string.
    multiline = [(match.start(), match.end()) for match in TOKEN.finditer(text)
                 if match[0].startswith('"') and ("\n" in match[0] or "\r" in match[0])]
    for line in text.splitlines(keepends=True):
        ending = "\r\n" if line.endswith("\r\n") else line[-1:] if line.endswith(("\n", "\r")) else ""
        content = line[:-len(ending)] if ending else line
        intersects_string = any(start < offset + len(line) and end > offset for start, end in multiline)
        parts = tokens(content)
        code = [part for part in parts if not part.startswith("#")]
        if len(content) > threshold and "{" in code and "}" in code and not intersects_string:
            replacement = (ending or newline).join(expand_line(parts, depth)) + ending
            output.append(replacement)
            changed += replacement != line
        else:
            output.append(line)
        # Count full lexer tokens within the line, rather than braces in comments/strings.
        if intersects_string:
            code = [match[0] for match in TOKEN.finditer(text)
                    if offset <= match.start() < offset + len(line) and match[0] in ("{", "}")]
        depth += code.count("{") - code.count("}")
        offset += len(line)
    after = "".join(output)
    if changed:
        assert_equivalent(text, after)
    return after, changed


@dataclass
class Change:
    path: Path
    original: bytes
    formatted: bytes
    lines: int


def candidate_changes() -> list[Change]:
    if not UPSTREAM.is_dir():
        raise FileNotFoundError(f"KR source is required to exclude upstream overrides: {UPSTREAM}")
    changes: list[Change] = []
    for folder in FOLDERS:
        for path in sorted((ROOT / folder).rglob("*.txt")):
            if EXCLUDED_NAME.search(path.name) or (UPSTREAM / path.relative_to(ROOT)).exists():
                continue
            original = path.read_bytes()
            text = original.decode("utf-8-sig")
            if GENERATED_HEADER.search("\n".join(text.splitlines()[:30])):
                continue
            after, count = format_text(text)
            if count:
                bom = b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b""
                changes.append(Change(path, original, bom + after.encode("utf-8"), count))
    return changes


def self_test() -> None:
    # Braces, operators and '#' inside strings/comments must remain literal.
    source = '# Keep { this } comment\r\nroot = { if = { limit = { flag = yes } log = "a # { b } >= \\"quoted\\"" value = -1 } else = { flags = { a b c } } } # same comment\r\n'
    after, count = format_text(source, 30)
    assert count == 1 and after != source
    assert_equivalent(source, after)
    assert "\r\n" in after and after.endswith("# same comment\r\n")
    assert format_text(after, 30) == (after, 0), "Formatting must be idempotent"
    nested = 'outer = {\n\tinner = { if = { limit = { a = yes b = no } c = yes } }\n}\n'
    after, count = format_text(nested, 30)
    assert count == 1 and "\n\t\tif = {\n\t\t\tlimit = {" in after
    assert_equivalent(nested, after)
    multiline = 'root = { text = "first\n{ literal } second" }\n'
    assert format_text(multiline, 10) == (multiline, 0)
    no_ending = 'root = { if = { limit = { a = yes } b = 1 } }'
    after, count = format_text(no_ending, 20)
    assert count == 1 and not after.endswith("\n")
    assert_equivalent(no_ending, after)
    print("PASS: formatter preserves comments, escaped/brace-bearing strings, multiline strings, scope, mixed statements, line endings and idempotence")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Read-only check (the default)")
    mode.add_argument("--write", action="store_true", help="Apply verified whitespace changes")
    parser.add_argument("--list", action="store_true", help="Print candidates; never write")
    parser.add_argument("--self-test", action="store_true", help="Test formatter safeguards only")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    changes = candidate_changes()
    for change in changes:
        print(f"{change.path.relative_to(ROOT).as_posix()}: {change.lines} long lines")
    if args.list:
        print(f"Candidates: {len(changes)} files, {sum(change.lines for change in changes)} lines; token/comment and AST checks passed")
        return 0
    if args.write:
        # Validate the complete batch before any write, and reject concurrent edits.
        if any(change.path.read_bytes() != change.original for change in changes):
            raise RuntimeError("A candidate changed during formatting; rerun against current files")
        for change in changes:
            change.path.write_bytes(change.formatted)
        print(f"Formatted {len(changes)} files; token/comment sequence and AST unchanged")
        return 0
    print(f"CHECK: {len(changes)} files need long-line formatting" if changes else "PASS: no eligible handwritten long lines remain")
    return 1 if changes else 0


if __name__ == "__main__":
    raise SystemExit(main())
