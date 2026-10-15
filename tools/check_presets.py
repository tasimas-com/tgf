#!/usr/bin/env python3
"""Validate that required CMake configure/build/test presets remain connected."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_PRESETS = {
    "debug": ("Debug", "None"),
    "release": ("Release", "None"),
    "relwithdebinfo": ("RelWithDebInfo", "None"),
    "profiling": ("RelWithDebInfo", "None"),
    "asan": ("Debug", "Address"),
    "ubsan": ("Debug", "Undefined"),
    "tsan": ("RelWithDebInfo", "Thread"),
    "msan": ("Debug", "Memory"),
}


def fail(message: str) -> int:
    print(f"preset check failed: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: check_presets.py <CMakePresets.json>")

    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"cannot read {path}: {exc}")

    if data.get("version", 0) < 6:
        return fail("preset schema version must be at least 6 (CMake 3.25)")

    categories: dict[str, dict[str, dict]] = {}
    for category in ("configurePresets", "buildPresets", "testPresets"):
        entries = data.get(category)
        if not isinstance(entries, list):
            return fail(f"{category} must be an array")
        indexed: dict[str, dict] = {}
        for entry in entries:
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                return fail(f"{category} contains an entry without a name")
            if name in indexed:
                return fail(f"duplicate {category} name: {name}")
            indexed[name] = entry
        categories[category] = indexed

    configure = categories["configurePresets"]
    build = categories["buildPresets"]
    tests = categories["testPresets"]

    for name, (build_type, sanitizer) in REQUIRED_PRESETS.items():
        preset = configure.get(name)
        if preset is None:
            return fail(f"required configure preset missing: {name}")
        cache = preset.get("cacheVariables", {})
        if cache.get("CMAKE_BUILD_TYPE") != build_type:
            return fail(f"{name} must use CMAKE_BUILD_TYPE={build_type}")
        if cache.get("TGF_SANITIZER", "None") != sanitizer:
            return fail(f"{name} must select TGF_SANITIZER={sanitizer}")
        if name not in build:
            return fail(f"build preset missing: {name}")
        if name not in tests:
            return fail(f"test preset missing: {name}")

    for entry in build.values():
        ref = entry.get("configurePreset")
        if ref not in configure:
            return fail(f"build preset {entry['name']} references unknown configure preset {ref}")
    for entry in tests.values():
        ref = entry.get("configurePreset")
        if ref not in configure:
            return fail(f"test preset {entry['name']} references unknown configure preset {ref}")
        if not entry.get("output", {}).get("outputOnFailure", False):
            return fail(f"test preset {entry['name']} must enable outputOnFailure")

    msvc_base = configure.get("msvc-ninja-base")
    if msvc_base is None or msvc_base.get("generator") != "Ninja":
        return fail("msvc-ninja-base must use Ninja so compiler launchers are supported")
    if msvc_base.get("cacheVariables", {}).get("CMAKE_CXX_COMPILER") != "cl":
        return fail("msvc-ninja-base must explicitly select MSVC cl.exe")
    if msvc_base.get("condition", {}).get("rhs") != "Windows":
        return fail("msvc-ninja-base must be restricted to Windows hosts")

    for name, build_type in (("msvc-ninja-debug", "Debug"), ("msvc-ninja-release", "Release")):
        preset = configure.get(name)
        if preset is None:
            return fail(f"Windows MSVC/Ninja configure preset missing: {name}")
        if preset.get("inherits") != "msvc-ninja-base":
            return fail(f"{name} must inherit the MSVC/Ninja base preset")
        cache = preset.get("cacheVariables", {})
        if cache.get("CMAKE_BUILD_TYPE") != build_type:
            return fail(f"{name} must use CMAKE_BUILD_TYPE={build_type}")
        if name not in build or name not in tests:
            return fail(f"{name} must have matching build and test presets")

    if "vs2022" not in configure or "vs2022-asan" not in configure:
        return fail("Windows Visual Studio 2022 and ASan configure presets are required")
    if "vs2022-release" not in build or "vs2022-asan" not in build:
        return fail("Visual Studio Release and ASan build presets are required")
    if "vs2022-release" not in tests or "vs2022-asan" not in tests:
        return fail("Visual Studio Release and ASan test presets are required")

    print(
        f"preset matrix OK: {len(configure)} configure, {len(build)} build, "
        f"{len(tests)} test presets; required configurations are connected"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
