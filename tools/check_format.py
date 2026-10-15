#!/usr/bin/env python3
"""Check or apply the repository's clang-format style to tracked source areas."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SOURCE_ROOTS = ("core", "platform", "rhi", "render", "text", "ui", "widgets", "pro", "host", "c", "bindings", "samples", "tests", "tools")
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
EXCLUDED_PARTS = {"build", "out", "_build", "generated", "third_party"}


def fail(message: str, code: int = 1) -> int:
    print(f"clang-format: {message}", file=sys.stderr)
    return code


def discover_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for directory in SOURCE_ROOTS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES:
                if not any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts):
                    found.append(path)
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang-format", required=True, help="path to clang-format executable")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--fix", action="store_true", help="rewrite files instead of checking them")
    args = parser.parse_args()

    root = args.root.resolve()
    tool = args.clang_format
    try:
        version = subprocess.run([tool, "--version"], check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return fail(f"cannot execute {tool!r}: {exc}", 2)
    match = re.search(r"version\s+(\d+)", version, re.IGNORECASE)
    if not match or int(match.group(1)) not in {22, 23}:
        return fail(f"expected clang-format major 22 or 23, found: {version or 'unknown'}", 2)

    files = discover_files(root)
    if not files:
        return fail("no C/C++ source files found")

    failures: list[str] = []
    for path in files:
        command = [tool, "--style=file"]
        command.append("-i" if args.fix else "--dry-run")
        if not args.fix:
            command.append("--Werror")
        command.append(str(path))
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
        except OSError as exc:
            return fail(f"failed to start formatter: {exc}", 2)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            failures.append(f"{path.relative_to(root)}: {detail}")

    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return fail(f"{len(failures)} file(s) need formatting")

    action = "formatted" if args.fix else "passed"
    print(f"clang-format {action}: {len(files)} file(s) checked using {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
