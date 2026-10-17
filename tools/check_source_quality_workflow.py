#!/usr/bin/env python3
"""Regression guard for the required LLVM source-quality CI lane."""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    path = root / ".github" / "workflows" / "source-quality.yml"
    if not path.is_file():
        print("FAIL: .github/workflows/source-quality.yml is missing", file=sys.stderr)
        return 1

    workflow = path.read_text(encoding="utf-8")
    required = (
        "pull_request:",
        "push:",
        "workflow_dispatch:",
        "ubuntu-26.04",
        'llvm-version: "22"',
        'iwyu-version: "0.26"',
        'llvm-version: "23"',
        'iwyu-version: "0.27"',
        "clang-format-$LLVM_VERSION",
        "clang-tidy-$LLVM_VERSION",
        'grep -Eq "version ${LLVM_VERSION}([.[:space:]]|$)"',
        "llvm-$LLVM_VERSION-dev",
        "libclang-$LLVM_VERSION-dev",
        "tools/check_format.py",
        "Enforce clang-format",
        "Run clang-tidy on the complete TGF build",
        "Run Include-What-You-Use on the complete TGF build",
        "TGF_ENABLE_CLANG_TIDY=ON",
        "TGF_ENABLE_IWYU=ON",
        'TGF_WARNINGS_AS_ERRORS=ON',
        'cmake --build "$RUNNER_TEMP/iwyu-build" --target include-what-you-use',
        "https://github.com/include-what-you-use/include-what-you-use.git",
        'cmake --build "build/clang-tidy-$LLVM_VERSION"',
        'cmake --build "build/iwyu-$LLVM_VERSION"',
    )
    # The configured IWYU integration must be strict; a report-only invocation
    # is not accepted as a successful CI analysis.
    integration = (root / "cmake" / "TgfQualityTools.cmake").read_text(encoding="utf-8")
    errors = [item for item in required if item not in workflow]
    if "CMAKE_CXX_INCLUDE_WHAT_YOU_USE" not in integration or "-Xiwyu;--error" not in integration:
        errors.append("CMake IWYU integration must fail the build on include diagnostics")
    if "continue-on-error:" in workflow:
        errors.append("source-quality checks may not be allowed to fail")
    if errors:
        for item in errors:
            print(f"FAIL: {item}", file=sys.stderr)
        return 1

    print("PASS: LLVM 22/23 CI runs formatter, clang-tidy, and strict IWYU with warnings-as-errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
