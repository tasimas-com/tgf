#!/usr/bin/env python3
"""Fail-closed regression checks for TGF's compiler and quality-tool policy."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

EXPECTED_COMPILERS = {
    "msvc": ["14.52", "14.51"],
    "clang": ["23", "22"],
    "gcc": ["16", "15"],
}
EXPECTED_TARGETS = {
    "gcc-16": {"compiler": "GCC 16", "os": "ubuntu-26.04", "cc": "gcc-16", "cxx": "g++-16", "compiler-major": "16"},
    "gcc-15": {"compiler": "GCC 15", "os": "ubuntu-26.04", "cc": "gcc-15", "cxx": "g++-15", "compiler-major": "15"},
    "clang-23": {"compiler": "LLVM Clang 23", "os": "ubuntu-26.04", "cc": "clang-23", "cxx": "clang++-23", "compiler-major": "23"},
    "clang-22": {"compiler": "LLVM Clang 22", "os": "ubuntu-26.04", "cc": "clang-22", "cxx": "clang++-22", "compiler-major": "22"},
    "msvc-14.52": {"compiler": "MSVC 14.52", "os": "windows-2025", "toolset": "14.52", "compiler-minor": "52", "preset-prefix": "msvc-ninja-"},
    "msvc-14.51": {"compiler": "MSVC 14.51", "os": "windows-2025", "toolset": "14.51", "compiler-minor": "51", "preset-prefix": "msvc-ninja-"},
    "appleclang": {"compiler": "AppleClang (Xcode)", "os": "macos-15", "cc": "clang", "cxx": "clang++", "compiler-major": ""},
}


def read_text(root: Path, relative: str) -> tuple[str | None, str | None]:
    try:
        return (root / relative).read_text(encoding="utf-8"), None
    except OSError as exc:
        return None, f"cannot read {relative}: {exc}"


def parse_ci_target_matrix(source: str) -> list[dict[str, str]]:
    """Read the matrix target-list subset of ci.yml without requiring PyYAML."""
    match = re.search(r"(?ms)^        target:\s*\n(?P<body>.*?)(?=^    steps:)", source)
    if match is None:
        raise ValueError("ci.yml: cannot locate the compiler target matrix")
    blocks = re.split(r"(?m)^          - os:\s*", match.group("body"))
    targets: list[dict[str, str]] = []
    for block in blocks[1:]:
        lines = block.splitlines()
        if not lines:
            continue
        target: dict[str, str] = {"os": lines[0].strip()}
        for line in lines[1:]:
            field = re.match(r"^            ([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
            if field is None:
                continue
            value = field.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            target[field.group(1)] = value
        targets.append(target)
    return targets


def check_repository(root: Path) -> list[str]:
    errors: list[str] = []

    policy_text, error = read_text(root, "cmake/compiler-support.json")
    if error:
        return [error]
    try:
        policy: dict[str, Any] = json.loads(policy_text or "")
    except json.JSONDecodeError as exc:
        return [f"invalid compiler-support.json: {exc}"]

    policy_date = policy.get("policy_date")
    try:
        if not isinstance(policy_date, str):
            raise ValueError("policy_date must be a string")
        reviewed_on = date.fromisoformat(policy_date)
        if reviewed_on > date.today():
            errors.append("compiler-support.json policy_date must not be in the future")
    except ValueError:
        errors.append("compiler-support.json policy_date must be a valid ISO-8601 date (YYYY-MM-DD)")

    if policy.get("tier_one_compilers") != EXPECTED_COMPILERS:
        errors.append("Tier-1 policy must declare MSVC 14.52/14.51, Clang 23/22, and GCC 16/15")
    if policy.get("language_standard") != "C++20":
        errors.append("TGF's language standard must remain C++20")
    if policy.get("warnings_as_errors_default") is not True:
        errors.append("warnings-as-errors must remain enabled by default")

    ci, error = read_text(root, ".github/workflows/ci.yml")
    if error:
        return errors + [error]
    try:
        targets = parse_ci_target_matrix(ci or "")
    except ValueError as exc:
        return errors + [str(exc)]

    by_key = {target.get("compiler-key", ""): target for target in targets}
    if len(targets) != len(EXPECTED_TARGETS) or set(by_key) != set(EXPECTED_TARGETS):
        errors.append("ci.yml must define exactly seven unique targets: GCC 15/16, Clang 22/23, MSVC 14.52/14.51, and AppleClang")
    for key, expected in EXPECTED_TARGETS.items():
        actual = by_key.get(key)
        if actual is None:
            errors.append(f"ci.yml: missing compiler target {key}")
            continue
        for field, required in expected.items():
            if actual.get(field) != required:
                errors.append(f"ci.yml: {key} must set {field}={required!r}, found {actual.get(field)!r}")

    if "configuration: [debug, release]" not in (ci or ""):
        errors.append("ci.yml must build and test Debug and Release")
    if not re.search(r'(?m)^  TGF_WARNINGS_AS_ERRORS:\s*"ON"\s*$', ci or ""):
        errors.append("ci.yml must set TGF_WARNINGS_AS_ERRORS=ON for every matrix job")
    if "DTGF_WARNINGS_AS_ERRORS=ON" not in (ci or ""):
        errors.append("ci.yml CMake configure commands must pass TGF_WARNINGS_AS_ERRORS=ON")

    # Each Windows matrix lane calls the same fail-closed installer, pinned to the
    # Visual Studio 2026 LTSC 18.11 channel used by windows-2025.
    for version, key, component in (
        ("14.52", "msvc-14.52", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"),
        ("14.51", "msvc-14.51", "Microsoft.VisualStudio.Component.VC.14.51.18.0.x86.x64"),
    ):
        step_name = f"Install MSVC {version} if missing"
        if step_name not in (ci or ""):
            errors.append(f"ci.yml must define {step_name}")
        if f"matrix.target.compiler-key == '{key}'" not in (ci or ""):
            errors.append(f"ci.yml: {version} installer must be scoped to {key}")
        if "-ToolsetVersion" not in (ci or "") or f'"{version}"' not in (ci or ""):
            errors.append(f"ci.yml: {version} install step must pass its exact toolset version")
        if component not in (ci or ""):
            errors.append(f"ci.yml: {version} install step must use component {component}")
    if ci.count("tools/install_msvc_toolset.ps1") != 2:
        errors.append("ci.yml must invoke the shared MSVC installer helper for both Windows targets")

    installer, error = read_text(root, "tools/install_msvc_toolset.ps1")
    if error:
        return errors + [error]
    for marker in (
        "[Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFilesX86)",
        "VisualStudio.18.Release.LTSC.18.11",
        "'modify --installPath \"{0}\" --channelId \"{1}\" --add \"{2}\" --quiet --norestart --wait'",
        "Start-Process -FilePath $bootstrapper -ArgumentList $installerArguments -Wait -PassThru",
        "Get-AuthenticodeSignature",
        '$signature.Status -ne "Valid"',
        "Microsoft Corporation",
        'Where-Object { $_.Name -like \"$ToolsetVersion.*\" }',
        "$installExitCode -notin @(0, 3010)",
        "Get-Content -LiteralPath $log.FullName -Tail 100",
        "refusing to fall back to another compiler",
    ):
        if marker not in installer:
            errors.append(f"tools/install_msvc_toolset.ps1 is missing required safety/verification contract: {marker}")

    if "toolset: $" + "{{ matrix.target.toolset }}" not in (ci or ""):
        errors.append("ci.yml must pass each matrix toolset to the MSVC developer environment")
    if "VCToolsVersion" not in (ci or "") or r"cl\.exe:\s+Version\s+19\." not in (ci or "") or "$expectedMinor" not in (ci or ""):
        errors.append("ci.yml must assert both the actual cl.exe and VCToolsVersion")
    if "Expected compiler major" not in (ci or ""):
        errors.append("ci.yml must verify GCC/Clang compiler majors")

    cmake, error = read_text(root, "CMakeLists.txt")
    if error:
        return errors + [error]
    compile_options, error = read_text(root, "cmake/TgfCompileOptions.cmake")
    if error:
        return errors + [error]
    quality_tools, error = read_text(root, "cmake/TgfQualityTools.cmake")
    if error:
        return errors + [error]
    presets, error = read_text(root, "CMakePresets.json")
    if error:
        return errors + [error]

    if not re.search(r'option\(TGF_WARNINGS_AS_ERRORS\s+"[^"]*"\s+ON\)', cmake or ""):
        errors.append("CMake must default TGF_WARNINGS_AS_ERRORS to ON")
    for required_flag in ("/W4", "/WX", "-Wall", "-Wextra", "-Wpedantic", "-Werror"):
        if required_flag not in (compile_options or ""):
            errors.append(f"compiler warning policy is missing {required_flag}")
    for marker in ("TGF_ENABLE_CLANG_TIDY", "TGF_ENABLE_IWYU", "CXX_CLANG_TIDY", "CXX_INCLUDE_WHAT_YOU_USE"):
        if marker not in (quality_tools or ""):
            errors.append(f"quality tool integration is missing {marker}")
    if "CMAKE_EXPORT_COMPILE_COMMANDS" not in (presets or ""):
        errors.append("Ninja developer presets must export compile_commands.json")

    for relative in (".clang-format", ".clang-tidy", "docs/COMPILER_SUPPORT.md", "tools/check_format.py"):
        if not (root / relative).is_file():
            errors.append(f"required compiler/quality policy file is missing: {relative}")

    quality_workflow, error = read_text(root, ".github/workflows/source-quality.yml")
    if error:
        return errors + [error]
    for marker in (
        'llvm-version: "22"', 'llvm-version: "23"',
        'iwyu-version: "0.26"', 'iwyu-version: "0.27"',
        "TGF_ENABLE_CLANG_TIDY=ON", "TGF_ENABLE_IWYU=ON",
        "TGF_WARNINGS_AS_ERRORS=ON", "tools/check_format.py",
    ):
        if marker not in (quality_workflow or ""):
            errors.append(f"source-quality.yml is missing required LLVM/quality contract: {marker}")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_compiler_policy.py <repository-root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    errors = check_repository(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: C++20; manifest and exact CI matrix agree (MSVC 14.52/14.51, "
        "Clang 23/22, GCC 16/15, AppleClang); warnings-as-errors; clang-format, "
        "clang-tidy, and version-matched IWYU"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
