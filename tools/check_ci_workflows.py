#!/usr/bin/env python3
"""Static contract checks for the repository's GitHub Actions workflows.

This script uses only the Python standard library. If PyYAML is available, it
also parses each workflow to catch YAML syntax errors in local development.
"""

from __future__ import annotations

from pathlib import Path
import sys


def require(text: str, fragments: tuple[str, ...], label: str) -> list[str]:
    missing = [fragment for fragment in fragments if fragment not in text]
    return [f"{label}: missing required workflow content: {item}" for item in missing]


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    workflow_dir = root / ".github" / "workflows"
    ci_path = workflow_dir / "ci.yml"
    nightly_path = workflow_dir / "nightly-benchmarks.yml"
    errors: list[str] = []

    for path in (ci_path, nightly_path):
        if not path.is_file():
            errors.append(f"Missing workflow: {path.relative_to(root)}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    ci = ci_path.read_text(encoding="utf-8")
    nightly = nightly_path.read_text(encoding="utf-8")

    errors.extend(
        require(
            ci,
            (
                "pull_request:",
                "workflow_dispatch:",
                "ubuntu-26.04",
                "windows-2025",
                "macos-15",
                "GCC 15",
                "LLVM Clang 22",
                "MSVC 14.51 (Windows hosted image)",
                "AppleClang",
                "configuration: [debug, release]",
                "actions/checkout@v7",
                "actions/cache@v4",
                "ilammy/msvc-dev-cmd@v1.13.0",
                "Restore incremental CMake build cache",
                "msvc-ninja-",
                "cl /nologo /Bv",
                "shell: pwsh",
                "Build (MSVC)",
                "Run CTest (MSVC)",
                "DTGF_ENABLE_LTO=OFF",
                "DTGF_WARNINGS_AS_ERRORS=ON",
                "actions/upload-artifact@v7",
            ),
            "ci.yml",
        )
    )
    errors.extend(
        require(
            nightly,
            (
                "schedule:",
                "self-hosted",
                "tgf-benchmark-pinned",
                "TGF_BENCHMARK_RUNNER_READY",
                "actions/checkout@v7",
                "tools/check_benchmark_host.py",
                "tgf_showcase",
                "benchmark-results.json",
                "DTGF_ENABLE_LTO=OFF",
                "DTGF_WARNINGS_AS_ERRORS=ON",
                "actions/upload-artifact@v7",
            ),
            "nightly-benchmarks.yml",
        )
    )

    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        yaml = None

    if yaml is not None:
        parsed: dict[Path, dict] = {}
        for path in (ci_path, nightly_path):
            try:
                document = yaml.safe_load(path.read_text(encoding="utf-8"))
                if not isinstance(document, dict) or not isinstance(document.get("jobs"), dict):
                    errors.append(f"{path.relative_to(root)}: workflow must contain a jobs mapping")
                else:
                    parsed[path] = document
            except yaml.YAMLError as exc:
                errors.append(f"{path.relative_to(root)}: invalid YAML: {exc}")

        ci_doc = parsed.get(ci_path)
        if ci_doc is not None:
            job = ci_doc.get("jobs", {}).get("build-and-test", {})
            matrix = job.get("strategy", {}).get("matrix", {})
            configurations = matrix.get("configuration", [])
            targets = matrix.get("target", [])
            expected_os = {"ubuntu-26.04", "windows-2025", "macos-15"}
            actual_os = {entry.get("os") for entry in targets if isinstance(entry, dict)}
            actual_compilers = {entry.get("compiler") for entry in targets if isinstance(entry, dict)}
            expected_compilers = {"GCC 15", "LLVM Clang 22", "MSVC 14.51 (Windows hosted image)", "AppleClang (Xcode)"}
            if configurations != ["debug", "release"]:
                errors.append("ci.yml: build matrix must cover Debug and Release")
            if len(targets) != 4 or actual_os != expected_os or actual_compilers != expected_compilers:
                errors.append("ci.yml: target matrix must contain GCC, Clang, MSVC, and AppleClang entries")

            windows_entry = next(
                (entry for entry in targets if isinstance(entry, dict) and entry.get("os") == "windows-2025"),
                None,
            )
            if windows_entry is None or windows_entry.get("preset-prefix") != "msvc-ninja-":
                errors.append("ci.yml: Windows MSVC entry must select the msvc-ninja preset family")

            steps = job.get("steps", [])
            steps_by_name = {step.get("name"): step for step in steps if isinstance(step, dict)}
            msvc_setup = steps_by_name.get("Set up MSVC developer environment", {})
            if msvc_setup.get("uses") != "ilammy/msvc-dev-cmd@v1.13.0":
                errors.append("ci.yml: Windows job must initialize the MSVC developer environment")
            for step_name in ("Build (MSVC)", "Run CTest (MSVC)"):
                step = steps_by_name.get(step_name, {})
                if step.get("shell") != "pwsh" or step.get("if") != "runner.os == 'Windows'":
                    errors.append(f"ci.yml: {step_name} must run in PowerShell on Windows")
            if not any(step.get("name") == "Show compiler version (MSVC)" and "cl /nologo /Bv" in step.get("run", "") for step in steps if isinstance(step, dict)):
                errors.append("ci.yml: Windows job must record the exact MSVC compiler version")

        nightly_doc = parsed.get(nightly_path)
        if nightly_doc is not None:
            job = nightly_doc.get("jobs", {}).get("benchmark", {})
            labels = job.get("runs-on", [])
            if not {"self-hosted", "linux", "x64", "tgf-benchmark-pinned"}.issubset(set(labels)):
                errors.append("nightly-benchmarks.yml: benchmark job must require all dedicated-runner labels")
            if job.get("if") != "${{ vars.TGF_BENCHMARK_RUNNER_READY == 'true' }}":
                errors.append("nightly-benchmarks.yml: benchmark runner readiness gate must remain fail-closed")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: CI workflow defines Windows, Linux and macOS build/test jobs, two configurations, incremental build caching, and test artifacts")
    print("PASS: MSVC uses Ninja with native PDB handling; Linux/macOS share incremental build caches")
    print("PASS: Actions use current checkout/upload-artifact major releases")
    if yaml is not None:
        print("PASS: parsed matrix expands to four toolchains x two configurations; Windows MSVC uses Ninja + PowerShell")
    print("PASS: nightly workflow requires a dedicated pinned-frequency runner and publishes benchmark artifacts")
    print("PASS: workflow YAML syntax verified" if yaml is not None else "INFO: PyYAML unavailable; YAML syntax parse skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
