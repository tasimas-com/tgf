#!/usr/bin/env python3
"""Regression tests for complete and exclusion-safe C/C++ format-file discovery."""
from __future__ import annotations

import tempfile
from pathlib import Path

from check_format import discover_files


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tgf-format-discovery-") as tmp:
        root = Path(tmp)
        expected = (
            root / "core" / "src" / "main.cpp",
            root / "future-module" / "nested" / "new_api.hpp",
            root / "plugin_api.h",
        )
        for path in expected:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("// test source\n", encoding="utf-8")

        excluded = (
            root / ".git" / "objects" / "ignored.cpp",
            root / "build" / "generated" / "ignored.cpp",
            root / "third_party" / "vendor.cpp",
            root / "vendor" / "generated.cpp",
            root / "module" / "cmake-build-debug" / "generated.cpp",
        )
        for path in excluded:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("// excluded source\n", encoding="utf-8")

        actual = discover_files(root)
        if actual != sorted(expected):
            print("FAIL: source discovery missed new roots or included excluded files")
            print("Expected:", *(str(path.relative_to(root)) for path in sorted(expected)), sep="\n  ")
            print("Actual:", *(str(path.relative_to(root)) for path in actual), sep="\n  ")
            return 1

    print("PASS: formatter discovers nested and future module sources, excludes generated/vendor trees")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
