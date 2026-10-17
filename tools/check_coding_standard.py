#!/usr/bin/env python3
"""Regression check for the normative TGF coding standard (P0.1.5)."""
from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "## 2. Naming and source layout",
    "## 3. Formatting and file organization",
    "## 5. Ownership, lifetime, and resource management",
    "## 6. Error handling and contracts",
    "## 10. API and ABI stability levels",
    "## 12. Pull request checklist",
)

REQUIRED_CONTRACTS = (
    "TGF_",
    "tgf_",
    "lower snake case",
    "UpperCamelCase",
    "trailing underscore",
    "kMemoryTagCount",
    "clang-format",
    "Result<T>",
    "Status",
    "[[nodiscard]]",
    "TGF_ASSERT",
    "TGF_CHECK",
    "RAII",
    "generational handles",
    "does not promise a cross-compiler or cross-standard-library C++ binary ABI",
    "Stable C ABI",
)

# This test guards the standard's existence and critical architectural contracts.
# It intentionally does not attempt to parse or lint C++ source code.
def fail(message: str) -> int:
    print(f"coding standard check FAILED: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: check_coding_standard.py <repository-root>")

    root = Path(sys.argv[1]).resolve()
    standard_path = root / "docs" / "CODING_STANDARD.md"
    formatter_path = root / ".clang-format"
    tidy_path = root / ".clang-tidy"

    try:
        standard = standard_path.read_text(encoding="utf-8")
        formatter = formatter_path.read_text(encoding="utf-8")
        tidy = tidy_path.read_text(encoding="utf-8")
    except OSError as exc:
        return fail(f"cannot read required policy file: {exc}")

    for section in REQUIRED_SECTIONS:
        if section not in standard:
            return fail(f"missing required section: {section}")

    for contract in REQUIRED_CONTRACTS:
        if contract not in standard:
            return fail(f"missing required policy contract: {contract}")

    # Keep mechanical style values documented from the actual repository config.
    for setting in ("BasedOnStyle: Google", "ColumnLimit: 120", "IndentWidth: 2", "PointerAlignment: Left"):
        if setting not in formatter or setting not in standard:
            return fail(f"formatter policy and coding standard disagree on {setting!r}")

    if "docs/CODING_STANDARD.md" not in tidy:
        return fail(".clang-tidy must point contributors to the normative coding standard")
    if "-portability-avoid-pragma-once" not in tidy or "Use `#pragma once` consistently with the current public headers." not in standard:
        return fail("clang-tidy must preserve the documented #pragma once convention without disabling portability checks")

    print("coding standard OK: naming, formatting, ownership, errors, API stability, and review contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
