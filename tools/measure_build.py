#!/usr/bin/env python3
"""Measure a clean TGF build and a one-translation-unit incremental rebuild."""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def validate_configuration(data: dict[str, Any], source_root: Path) -> tuple[Path, dict[str, float]]:
    if data.get("schema_version") != 1:
        raise ValueError("budget file schema_version must be 1")
    if data.get("generator") != "Ninja":
        raise ValueError("build-time tracking currently requires the Ninja generator")
    if data.get("compiler_id") != "Clang" or data.get("compiler_major") != 23:
        raise ValueError("the hosted baseline must use Clang 23")
    if data.get("configuration") != "Release":
        raise ValueError("the hosted baseline must use the Release configuration")

    parallel_jobs = data.get("parallel_jobs")
    if not isinstance(parallel_jobs, int) or isinstance(parallel_jobs, bool) or parallel_jobs < 1:
        raise ValueError("parallel_jobs must be a positive integer")

    budgets = data.get("budgets_seconds")
    if not isinstance(budgets, dict):
        raise ValueError("budgets_seconds must be an object")
    clean = budgets.get("clean")
    incremental = budgets.get("incremental")
    for label, value in (("clean", clean), ("incremental", incremental)):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{label} build budget must be a positive number")
    if incremental >= clean:
        raise ValueError("incremental build budget must be lower than the clean build budget")

    probe_text = data.get("incremental_probe")
    if not isinstance(probe_text, str) or not probe_text:
        raise ValueError("incremental_probe must be a repository-relative source path")
    probe_relative = Path(probe_text)
    if probe_relative.is_absolute():
        raise ValueError("incremental_probe must be repository-relative")
    probe = (source_root / probe_relative).resolve()
    try:
        probe.relative_to(source_root.resolve())
    except ValueError as exc:
        raise ValueError("incremental_probe must remain inside the source tree") from exc
    if not probe.is_file() or probe.suffix.lower() not in (".c", ".cc", ".cpp", ".cxx"):
        raise ValueError(f"incremental_probe is not an existing C/C++ source file: {probe_text}")

    return probe, {"clean": float(clean), "incremental": float(incremental)}


def run_timed_build(command: list[str], cwd: Path, log_path: Path) -> tuple[float, str]:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    elapsed = time.perf_counter() - started
    output = completed.stdout or ""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(
            f"build command failed with exit code {completed.returncode}; see {log_path}"
        )
    return elapsed, output


def run_incremental_build(
    probe: Path, command: list[str], cwd: Path, log_path: Path
) -> tuple[float, str]:
    """Touch one tracked source, rebuild it, then restore its original timestamp."""
    original = probe.stat()
    try:
        touched_ns = max(time.time_ns(), original.st_mtime_ns) + 1_000_000_000
        os.utime(probe, ns=(original.st_atime_ns, touched_ns))
        elapsed, output = run_timed_build(command, cwd, log_path)
    finally:
        os.utime(probe, ns=(original.st_atime_ns, original.st_mtime_ns))
    if probe.name not in output:
        raise RuntimeError(
            f"incremental build did not compile the probe source {probe.name}; "
            f"see {log_path}"
        )
    return elapsed, output


def read_cmake_cache(build_dir: Path) -> dict[str, str]:
    cache = build_dir / "CMakeCache.txt"
    if not cache.is_file():
        raise ValueError(f"no CMakeCache.txt found in build directory: {build_dir}")
    values: dict[str, str] = {}
    for line in cache.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"^([^:#]+):[^=]+=(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def read_compiler_identity(build_dir: Path) -> tuple[str, str]:
    """Read compiler identity from CMake's generated compiler metadata."""
    candidates = sorted((build_dir / "CMakeFiles").glob("*/CMakeCXXCompiler.cmake"))
    if not candidates:
        raise ValueError("CMake compiler metadata file was not found under CMakeFiles")
    for path in candidates:
        content = path.read_text(encoding="utf-8", errors="replace")
        compiler_id = re.search(r'^set\\(CMAKE_CXX_COMPILER_ID "([^"]+)"\\)', content, re.MULTILINE)
        compiler_version = re.search(r'^set\\(CMAKE_CXX_COMPILER_VERSION "([^"]+)"\\)', content, re.MULTILINE)
        if compiler_id and compiler_version:
            return compiler_id.group(1), compiler_version.group(1)
    raise ValueError("CMake compiler metadata does not contain compiler ID and version")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--budget-file", type=Path, default=None)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--cmake", default="cmake")
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    build_dir = args.build_dir.resolve()
    budget_file = args.budget_file or source_root / "cmake" / "build-performance-budgets.json"
    report_dir = args.report_dir.resolve()
    try:
        data = json.loads(budget_file.read_text(encoding="utf-8"))
        probe, budgets = validate_configuration(data, source_root)
        cache = read_cmake_cache(build_dir)
        if cache.get("CMAKE_GENERATOR") != data["generator"]:
            raise ValueError(
                f"expected generator {data['generator']}, found {cache.get('CMAKE_GENERATOR')}"
            )
        compiler_id, compiler_version = read_compiler_identity(build_dir)
        if compiler_id != data["compiler_id"]:
            raise ValueError(
                f"expected compiler {data['compiler_id']}, found {compiler_id}"
            )
        if not compiler_version.startswith(f'{data["compiler_major"]}.'):
            raise ValueError(
                f"expected compiler major {data['compiler_major']}, found {compiler_version or 'unknown'}"
            )
        if cache.get("CMAKE_BUILD_TYPE") != data["configuration"]:
            raise ValueError(
                f"expected {data['configuration']} configuration, found {cache.get('CMAKE_BUILD_TYPE')}"
            )

        report_dir.mkdir(parents=True, exist_ok=True)
        parallel = str(data["parallel_jobs"])
        command = [args.cmake, "--build", str(build_dir), "--parallel", parallel, "--verbose"]
        clean_log = report_dir / "clean-build.log"
        incremental_log = report_dir / "incremental-build.log"

        clean_result = subprocess.run(
            [args.cmake, "--build", str(build_dir), "--target", "clean"],
            cwd=source_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        (report_dir / "clean-target.log").write_text(
            clean_result.stdout or "", encoding="utf-8"
        )
        if clean_result.returncode != 0:
            raise RuntimeError(
                f"CMake clean target failed with exit code {clean_result.returncode}"
            )

        clean_seconds, clean_output = run_timed_build(command, source_root, clean_log)
        incremental_seconds, incremental_output = run_incremental_build(
            probe, command, source_root, incremental_log
        )
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"build performance measurement failed: {exc}", file=sys.stderr)
        return 1

    clean_passed = clean_seconds <= budgets["clean"]
    incremental_passed = incremental_seconds <= budgets["incremental"]
    report = {
        "schema_version": 1,
        "tool": "tools/measure_build.py",
        "runner": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        },
        "configuration": data["configuration"],
        "generator": data["generator"],
        "compiler": {
            "id": compiler_id,
            "version": compiler_version,
            "path": cache.get("CMAKE_CXX_COMPILER"),
        },
        "parallel_jobs": int(data["parallel_jobs"]),
        "incremental_probe": str(probe.relative_to(source_root)),
        "measurements": {
            "clean": {
                "seconds": round(clean_seconds, 3),
                "budget_seconds": budgets["clean"],
                "passed": clean_passed,
            },
            "incremental": {
                "seconds": round(incremental_seconds, 3),
                "budget_seconds": budgets["incremental"],
                "passed": incremental_passed,
                "recompiled_probe": probe.name in incremental_output,
            },
        },
    }
    json_path = report_dir / "build-performance.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown = [
        "# TGF build-time report",
        "",
        f"- Configuration: {data['configuration']} / {data['generator']}",
        f"- Compiler: {report['compiler']['id']} {report['compiler']['version']}",
        f"- Parallel build jobs: {data['parallel_jobs']}",
        f"- Incremental probe: {report['incremental_probe']}",
        "",
        "| Measurement | Elapsed | Budget | Result |",
        "|---|---:|---:|---|",
        f"| Clean build | {clean_seconds:.3f} s | {budgets['clean']:.1f} s | {'PASS' if clean_passed else 'FAIL'} |",
        f"| One-source incremental rebuild | {incremental_seconds:.3f} s | {budgets['incremental']:.1f} s | {'PASS' if incremental_passed else 'FAIL'} |",
        "",
        "The clean timer covers the default build after CMake's clean target; configuration and tool installation are excluded.",
        "The incremental timer covers a rebuild after touching the probe source; its original timestamp is restored.",
        "",
    ]
    (report_dir / "build-performance.md").write_text("\n".join(markdown), encoding="utf-8")
    print(f"Clean build: {clean_seconds:.3f}s / {budgets['clean']:.1f}s")
    print(f"Incremental rebuild: {incremental_seconds:.3f}s / {budgets['incremental']:.1f}s")
    print(f"Build report: {json_path}")
    return 0 if clean_passed and incremental_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
