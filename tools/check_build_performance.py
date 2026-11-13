#!/usr/bin/env python3
"""Guard the build-time budget and per-header report implementation contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_build import validate_configuration


def require(path: Path, fragments: tuple[str, ...], label: str) -> list[str]:
    if not path.is_file():
        return [f"{label}: required file is missing"]
    content = path.read_text(encoding="utf-8")
    return [f"{label}: missing required contract text: {item}" for item in fragments if item not in content]


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors: list[str] = []
    config_path = root / "cmake" / "build-performance-budgets.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        validate_configuration(data, root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid build-performance budget configuration: {exc}")

    errors.extend(
        require(
            root / "CMakeLists.txt",
            ('option(TGF_ENABLE_HEADER_TIME_TRACE',),
            "CMakeLists.txt",
        )
    )
    errors.extend(
        require(
            root / "tests" / "CMakeLists.txt",
            (
                "file(GLOB_RECURSE _module_headers",
                "header-check-manifest.tsv",
                "-ftime-trace",
                "build_measurement_tool",
                "header_cost_reporter",
                "build_performance_policy",
            ),
            "tests/CMakeLists.txt",
        )
    )
    errors.extend(
        require(
            root / ".github" / "workflows" / "build-performance.yml",
            (
                "pull_request:",
                "workflow_dispatch:",
                "ubuntu-26.04",
                "clang-23",
                "TGF_ENABLE_HEADER_TIME_TRACE=ON",
                "tools/measure_build.py",
                "tools/report_header_costs.py",
                "actions/upload-artifact@v7",
                "build-performance-reports",
            ),
            "build-performance.yml",
        )
    )
    errors.extend(
        require(
            root / "docs" / "BUILD_PERFORMANCE.md",
            (
                "Clean build budget",
                "Incremental rebuild budget",
                "180 seconds",
                "45 seconds",
                "Total ExecuteCompiler",
                "runtime benchmark suite",
            ),
            "BUILD_PERFORMANCE.md",
        )
    )
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("PASS: build-time budgets, incremental probe, Clang header tracing, CTest coverage, and CI artifact contract are connected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
