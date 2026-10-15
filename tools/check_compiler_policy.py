#!/usr/bin/env python3
"""Regression checks for TGF's compiler-support and quality-tool policy."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def fail(message: str) -> int:
    print(f"compiler policy check failed: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: check_compiler_policy.py <repository-root>")
    root = Path(sys.argv[1]).resolve()
    try:
        policy = json.loads((root / "cmake/compiler-support.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"cannot load compiler-support.json: {exc}")

    expected = {"msvc": ["14.51", "14.50"], "clang": ["23", "22"], "gcc": ["16", "15"]}
    if policy.get("tier_one_compilers") != expected:
        return fail("Tier-1 compiler matrix must list the two current generations for MSVC, Clang, and GCC")
    if policy.get("language_standard") != "C++20":
        return fail("TGF's language standard must remain C++20")
    if policy.get("warnings_as_errors_default") is not True:
        return fail("warnings-as-errors must remain enabled by default")

    cmake = (root / "CMakeLists.txt").read_text(encoding="utf-8")
    compile_options = (root / "cmake/TgfCompileOptions.cmake").read_text(encoding="utf-8")
    quality_tools = (root / "cmake/TgfQualityTools.cmake").read_text(encoding="utf-8")
    if not re.search(r'option\(TGF_WARNINGS_AS_ERRORS\s+[^\n]*\sON\)', cmake):
        return fail("CMake must default TGF_WARNINGS_AS_ERRORS to ON")
    for required_flag in ("/W4", "/WX", "-Wall", "-Wextra", "-Wpedantic", "-Werror"):
        if required_flag not in compile_options:
            return fail(f"compiler warning policy is missing {required_flag}")
    for marker in ("TGF_ENABLE_CLANG_TIDY", "TGF_ENABLE_IWYU", "CXX_CLANG_TIDY", "CXX_INCLUDE_WHAT_YOU_USE"):
        if marker not in quality_tools:
            return fail(f"quality tool integration is missing {marker}")
    for required in (".clang-format", ".clang-tidy", "docs/COMPILER_SUPPORT.md", "tools/check_format.py"):
        if not (root / required).is_file():
            return fail(f"required compiler/quality policy file is missing: {required}")

    print("compiler policy OK: C++20, MSVC/Clang/GCC matrix, warnings-as-errors, formatter, tidy, and IWYU wiring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
