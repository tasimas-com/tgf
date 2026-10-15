#!/usr/bin/env python3
"""Static and structural contract checks for TGF GitHub Actions workflows.

This is intentionally stdlib-only: a missing YAML parser must not weaken the
required compiler-matrix checks. If PyYAML is available, the expanded matrix
and its version-pinning inputs are also inspected structurally.
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
                "GCC 16",
                "GCC 15",
                "LLVM Clang 23",
                "LLVM Clang 22",
                "MSVC 14.51 (Windows hosted image)",
                "MSVC 14.50",
                "AppleClang",
                "configuration: [debug, release]",
                "actions/checkout@v7",
                "actions/cache@v4",
                "ilammy/msvc-dev-cmd@v1.13.0",
                "Install GCC 16 on Ubuntu 26.04",
                "sudo apt-get install --yes gcc-16 g++-16",
                "Install LLVM Clang 23 on Ubuntu 26.04",
                "https://apt.llvm.org/llvm.sh",
                "sudo ./llvm.sh 23",
                "Install MSVC 14.50 if missing",
                "Microsoft.VisualStudio.Component.VC.14.50.18.0.x86.x64",
                "toolset: ${{ matrix.target.toolset }}",
                "EXPECTED_COMPILER_MAJOR",
                "actual_major",
                "compiler-minor",
                "VCToolsVersion",
                "cl.exe",
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
            expected_compilers = {
                "GCC 16",
                "GCC 15",
                "LLVM Clang 23",
                "LLVM Clang 22",
                "MSVC 14.51 (Windows hosted image)",
                "MSVC 14.50",
                "AppleClang (Xcode)",
            }
            if configurations != ["debug", "release"]:
                errors.append("ci.yml: build matrix must cover Debug and Release")
            if (
                len(targets) != 7
                or actual_os != expected_os
                or actual_compilers != expected_compilers
            ):
                errors.append(
                    "ci.yml: target matrix must contain both GCC and Clang generations, "
                    "both MSVC toolsets, and the AppleClang compatibility lane"
                )

            target_by_compiler = {
                entry.get("compiler"): entry for entry in targets if isinstance(entry, dict)
            }
            expected_targets = {
                "GCC 16": ("gcc-16", "g++-16", "16", "ubuntu-26.04"),
                "GCC 15": ("gcc-15", "g++-15", "15", "ubuntu-26.04"),
                "LLVM Clang 23": ("clang-23", "clang++-23", "23", "ubuntu-26.04"),
                "LLVM Clang 22": ("clang-22", "clang++-22", "22", "ubuntu-26.04"),
            }
            for compiler, expected in expected_targets.items():
                target = target_by_compiler.get(compiler, {})
                actual = (
                    target.get("cc"),
                    target.get("cxx"),
                    target.get("compiler-major"),
                    target.get("os"),
                )
                if actual != expected:
                    errors.append(f"ci.yml: {compiler} must select the exact compiler binaries and major version")

            for compiler, toolset, minor in (
                ("MSVC 14.51 (Windows hosted image)", "14.51", "51"),
                ("MSVC 14.50", "14.50", "50"),
            ):
                target = target_by_compiler.get(compiler, {})
                if (
                    target.get("os") != "windows-2025"
                    or target.get("toolset") != toolset
                    or target.get("compiler-minor") != minor
                    or target.get("preset-prefix") != "msvc-ninja-"
                ):
                    errors.append(f"ci.yml: {compiler} must pin its matching toolset and MSVC/Ninja presets")

            apple = target_by_compiler.get("AppleClang (Xcode)", {})
            if apple.get("os") != "macos-15" or apple.get("compiler-major") != "":
                errors.append("ci.yml: AppleClang must remain a separate macOS compatibility lane")

            steps = job.get("steps", [])
            steps_by_name = {step.get("name"): step for step in steps if isinstance(step, dict)}
            gcc_install = steps_by_name.get("Install GCC 16 on Ubuntu 26.04", {})
            if gcc_install.get("if") != "matrix.target.compiler-key == 'gcc-16'":
                errors.append("ci.yml: GCC 16 installation must be scoped to the GCC 16 target")
            clang_install = steps_by_name.get("Install LLVM Clang 23 on Ubuntu 26.04", {})
            if clang_install.get("if") != "matrix.target.compiler-key == 'clang-23'":
                errors.append("ci.yml: Clang 23 installation must be scoped to the Clang 23 target")
            msvc_install = steps_by_name.get("Install MSVC 14.50 if missing", {})
            if msvc_install.get("if") != "matrix.target.compiler-key == 'msvc-14.50'":
                errors.append("ci.yml: MSVC 14.50 installation must be scoped to the MSVC 14.50 target")

            msvc_setup = steps_by_name.get("Set up MSVC developer environment", {})
            if msvc_setup.get("uses") != "ilammy/msvc-dev-cmd@v1.13.0":
                errors.append("ci.yml: Windows job must initialize the MSVC developer environment")
            if msvc_setup.get("with", {}).get("toolset") != "${{ matrix.target.toolset }}":
                errors.append("ci.yml: Windows jobs must pass their pinned MSVC toolset to vcvarsall")
            for step_name in ("Build (MSVC)", "Run CTest (MSVC)"):
                step = steps_by_name.get(step_name, {})
                if step.get("shell") != "pwsh" or step.get("if") != "runner.os == 'Windows'":
                    errors.append(f"ci.yml: {step_name} must run in PowerShell on Windows")
            msvc_probe = steps_by_name.get("Show compiler version (MSVC)", {})
            if "compiler-minor" not in msvc_probe.get("run", "") or "VCToolsVersion" not in msvc_probe.get("run", ""):
                errors.append("ci.yml: Windows job must verify the selected MSVC compiler and toolset versions")

            unix_probe = steps_by_name.get("Show compiler version (GCC / Clang)", {})
            if "EXPECTED_COMPILER_MAJOR" not in unix_probe.get("env", {}) or "-dumpversion" not in unix_probe.get("run", ""):
                errors.append("ci.yml: GCC/Clang jobs must assert the selected compiler major version")

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

    print("PASS: CI matrix defines the complete two-generation MSVC, Clang, and GCC Tier-1 matrix plus AppleClang compatibility")
    print("PASS: older MSVC is explicitly installed when absent; GCC/Clang/MSVC compiler versions are asserted")
    print("PASS: all compiler targets run Debug and Release with warnings-as-errors, incremental caching, and CTest artifacts")
    if yaml is not None:
        print("PASS: YAML structure, seven compiler targets, pinned toolsets, and installation conditions verified")
    else:
        print("INFO: PyYAML unavailable; structural checks skipped, required matrix/install/version contracts verified textually")
    print("PASS: nightly workflow requires a dedicated pinned-frequency runner and publishes benchmark artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
