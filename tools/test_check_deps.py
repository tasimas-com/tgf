#!/usr/bin/env python3
"""Regression test for the TGF dependency checker, including bindings isolation."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

REQUIRED_DIRS = (
    "core", "platform", "rhi", "render", "text", "ui", "widgets", "pro",
    "tools", "host", "c", "bindings", "samples", "benchmarks", "tests",
    "docs", "third_party", "cmake",
)


def run_checker(checker: pathlib.Path, source: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="tgf-deps-test-") as tmp:
        root = pathlib.Path(tmp)
        for name in REQUIRED_DIRS:
            (root / name).mkdir(parents=True, exist_ok=True)
        binding_source = root / "bindings" / "binding.cpp"
        binding_source.write_text(source, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(checker), str(root)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: test_check_deps.py path/to/check_deps.py", file=sys.stderr)
        return 2
    checker = pathlib.Path(sys.argv[1]).resolve()

    allowed = run_checker(checker, "#include <tgf/c/api.h>\n")
    if allowed.returncode != 0:
        print("FAIL: C ABI dependency should be allowed")
        print(allowed.stdout)
        return 1

    forbidden = run_checker(checker, "#include <tgf/core/types.hpp>\n")
    expected = "module 'bindings' may not depend on 'core'"
    if forbidden.returncode == 0 or expected not in forbidden.stdout:
        print("FAIL: direct core dependency from bindings was not rejected")
        print(forbidden.stdout)
        return 1

    print("dependency checker bindings rule passed (C allowed, core rejected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
