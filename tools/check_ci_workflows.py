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
                "MSVC 14.52",
                "MSVC 14.51",
                "AppleClang",
                "configuration: [debug, release]",
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7",
                "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7",
                "Set up Python 3.13",
                'python-version: "3.13"',
                "actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6",
                "ilammy/msvc-dev-cmd@0b201ec74fa43914dc39ae48a89fd1d8cb592756 # v1.13.0",
                "Install GCC 16 on Ubuntu 26.04",
                "sudo apt-get install --yes gcc-16 g++-16",
                "Install LLVM Clang 23 on Ubuntu 26.04",
                "https://apt.llvm.org/llvm-snapshot.gpg.key",
                'expected_fingerprint="6084F3CF814B57C1CF12EFD515CF4D18AF4F7421"',
                "signed-by=/usr/share/keyrings/apt.llvm.org.asc",
                "sudo apt-get install --yes clang-23",
                "Install MSVC 14.52 if missing",
                "Install MSVC 14.51 if missing",
                "https://download.visualstudio.microsoft.com/download/pr/2d4073f5-2775-4a70-8c1d-b50ae62795a7/d95f7e7eb4ede7b559d3bff79b496d1797d989cae5b96d494beb6b9ebffe61d0/vs_Enterprise.exe",
                "VisualStudio.18.Release.LTSC.18.11",
                "--wait",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "Microsoft.VisualStudio.Component.VC.14.51.18.0.x86.x64",
                                "Start-Process -FilePath $setup -ArgumentList $installerArguments -Wait -PassThru",
                "Start-Sleep -Seconds 5",
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
                "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7",
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
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7",
                "tools/check_benchmark_host.py --require-bare-metal",
                "tools/collect_benchmark_host_inventory.py",
                "benchmark-artifacts/host-inventory.json",
                "Capture hardware, thermal, and software inventory",
                "tgf_showcase",
                "benchmark-results.json",
                "DTGF_ENABLE_LTO=OFF",
                "DTGF_WARNINGS_AS_ERRORS=ON",
                "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7",
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
                "MSVC 14.52",
                "MSVC 14.51",
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
                ("MSVC 14.52", "14.52", "52"),
                ("MSVC 14.51", "14.51", "51"),
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
            python_setup = steps_by_name.get("Set up Python 3.13", {})
            if (
                python_setup.get("uses") != "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0"
                or python_setup.get("with", {}).get("python-version") != "3.13"
            ):
                errors.append("ci.yml: Python 3.13 must be explicitly installed for required policy tests")
            gcc_install = steps_by_name.get("Install GCC 16 on Ubuntu 26.04", {})
            if gcc_install.get("if") != "matrix.target.compiler-key == 'gcc-16'":
                errors.append("ci.yml: GCC 16 installation must be scoped to the GCC 16 target")
            clang_install = steps_by_name.get("Install LLVM Clang 23 on Ubuntu 26.04", {})
            if clang_install.get("if") != "matrix.target.compiler-key == 'clang-23'":
                errors.append("ci.yml: Clang 23 installation must be scoped to the Clang 23 target")
            msvc_install = steps_by_name.get("Install MSVC 14.52 if missing", {})
            if msvc_install.get("if") != "matrix.target.compiler-key == 'msvc-14.52'":
                errors.append("ci.yml: MSVC 14.52 installation must be scoped to the MSVC 14.52 target")
            msvc_install_script = msvc_install.get("run", "")
            if "setup.exe" in msvc_install_script:
                errors.append("ci.yml: use the Visual Studio bootstrapper, not setup.exe, for the MSVC 14.52 modify operation")
            if "VisualStudio.18.Release.LTSC.18.11" not in msvc_install_script:
                errors.append("ci.yml: MSVC 14.52 modify operation must specify the LTSC 18.11 channel ID")
            if "--wait" not in msvc_install_script:
                errors.append("ci.yml: MSVC 14.52 bootstrapper must wait for servicing to complete")
            if "Get-AuthenticodeSignature" not in msvc_install_script:
                errors.append("ci.yml: downloaded MSVC bootstrapper must have its Microsoft signature verified")
            if "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" not in msvc_install.get("run", ""):
                errors.append("ci.yml: MSVC 14.52 must use its versioned Visual Studio 18.11 x64/x86 component")
            if "--channelId VisualStudio.18.Stable" in msvc_install.get("run", ""):
                errors.append("ci.yml: MSVC 14.52 must use its LTSC channel rather than the Stable channel")
            if 'Where-Object { $_.Name -like "14.52.*" }' not in msvc_install.get("run", ""):
                errors.append("ci.yml: MSVC 14.52 installer must verify the exact GA toolset directory")
            previous_msvc_install = steps_by_name.get("Install MSVC 14.51 if missing", {})
            if previous_msvc_install.get("if") != "matrix.target.compiler-key == 'msvc-14.51'":
                errors.append("ci.yml: MSVC 14.51 installation must be scoped to the MSVC 14.51 target")
            if "Microsoft.VisualStudio.Component.VC.14.51.18.0.x86.x64" not in previous_msvc_install.get("run", ""):
                errors.append("ci.yml: MSVC 14.51 must use its version-specific x64/x86 component")
            if 'Where-Object { $_.Name -like "14.51.*" }' not in previous_msvc_install.get("run", ""):
                errors.append("ci.yml: MSVC 14.51 installer must verify the exact toolset directory")

            msvc_setup = steps_by_name.get("Set up MSVC developer environment", {})
            if msvc_setup.get("uses") != "ilammy/msvc-dev-cmd@0b201ec74fa43914dc39ae48a89fd1d8cb592756":
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
            steps = job.get("steps", [])
            steps_by_name = {step.get("name"): step for step in steps if isinstance(step, dict)}
            preflight = steps_by_name.get("Verify pinned CPU frequency and bare-metal host", {})
            if preflight.get("run") != "python3 tools/check_benchmark_host.py --require-bare-metal":
                errors.append("nightly-benchmarks.yml: benchmark preflight must verify pinned frequency and bare-metal x86-64")
            inventory = steps_by_name.get("Capture hardware, thermal, and software inventory", {})
            if "tools/collect_benchmark_host_inventory.py" not in inventory.get("run", "") or "host-inventory.json" not in inventory.get("run", ""):
                errors.append("nightly-benchmarks.yml: benchmark run must capture a machine-readable host inventory")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: CI matrix defines the complete two-generation MSVC, Clang, and GCC Tier-1 matrix plus AppleClang compatibility")
    print("PASS: MSVC 14.52 is explicitly installed when absent; GCC/Clang/MSVC compiler versions are asserted")
    print("PASS: all compiler targets run Debug and Release with warnings-as-errors, incremental caching, and CTest artifacts")
    if yaml is not None:
        print("PASS: YAML structure, seven compiler targets, pinned toolsets, and installation conditions verified")
    else:
        print("INFO: PyYAML unavailable; structural checks skipped, required matrix/install/version contracts verified textually")
    print("PASS: nightly workflow requires a dedicated pinned-frequency runner and publishes benchmark artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
