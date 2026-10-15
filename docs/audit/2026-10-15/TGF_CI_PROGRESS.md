# TGF CI implementation progress — Revision 12

**Date:** 2026-10-15  
**Task:** P0.1.4 — Windows / Linux / macOS CI, compiler caching, nightly pinned-frequency benchmarks  
**Status:** Partially implemented; remote runner execution and dedicated benchmark-host provisioning remain open.

## Delivered

### Pull-request and push CI

Added `.github/workflows/ci.yml` with Debug and Release build/test jobs for:

- Ubuntu 26.04 with GCC 15 (`gcc-15` / `g++-15`)
- Ubuntu 26.04 with LLVM Clang 22 (`clang-22` / `clang++-22`)
- Windows Server 2025 with Visual Studio 2022 / MSVC
- macOS 15 with AppleClang from Xcode

Each job enables warnings-as-errors, uses `sccache` backed by GitHub Actions cache, builds the project, runs the CTest preset, emits cache statistics, and uploads its CTest log. Optional LTO is disabled in this common compiler/OS baseline because LTO availability and linker-plugin packaging differ by toolchain; Release optimization remains enabled.

The Windows job captures CMake's compiler-identification output so the actual compiler version can be reviewed in the Actions log. The job is intentionally labelled Visual Studio 2022/MSVC rather than asserting a toolset patch version based on the runtime redistributable alone.

### Dedicated benchmark workflow

Added `.github/workflows/nightly-benchmarks.yml`, scheduled daily at 03:37 UTC and manually dispatchable. It targets only:

```text
[self-hosted, linux, x64, tgf-benchmark-pinned]
```

It will remain skipped until repository variable `TGF_BENCHMARK_RUNNER_READY` is set to the exact value `true`. This prevents a scheduled benchmark from silently running on a shared hosted runner.

Before compilation or measurement, `tools/check_benchmark_host.py` requires every exposed Linux CPU frequency policy to report:

- `scaling_governor = performance`
- `scaling_min_freq = scaling_max_freq`

The workflow records `uname`, `lscpu`, CMake, and compiler information alongside the showcase JSON benchmark output. Benchmark artifacts are retained for 30 days.

### Regression coverage and documentation

- `tools/check_ci_workflows.py` checks the cross-platform workflow, two build configurations, cache, CTest artifacts, nightly schedule, runner guard, host check, and benchmark artifact contract. It parses YAML when PyYAML is installed, while requiring no third-party Python dependency for its structural checks.
- `tools/test_check_benchmark_host.py` covers a valid pinned host, wrong governor, frequency scaling, missing controls, and missing policies.
- Both checks are registered in CTest.
- `docs/CI.md` documents platform coverage, host provisioning, runner labels, repository variable, and local checks.
- `docs/BUILDING.md`, `README.md`, `docs/STATUS.md`, and `TODO.md` were updated.

## Local verification

| Toolchain/configuration | Build | CTest |
|---|---|---:|
| GCC 14.2 Release | Pass | 7/7 |
| GCC 14.2 Debug | Pass | 7/7 |
| Clang 17 Release, LTO disabled | Pass | 7/7 |
| CI workflow YAML parse (PyYAML) | Pass | — |
| Benchmark host-policy unit tests | Pass | 5/5 |
| Workflow contract script | Pass | — |

GCC 14.2 and Clang 17 are the installed audit-environment compilers, not a substitute for the advertised latest Tier-1 generations. Clang 17's installed Swift toolchain lacks the LLVMgold plugin, so local Clang verification explicitly disables optional LTO. The hosted workflow uses the runner-provided supported compilers and also disables optional LTO for consistency.

## Not claimed complete

No GitHub Actions run has been started or inspected from this archive-only working environment. Thus the hosted Windows, Linux, and macOS workflow jobs have not yet proven that they execute successfully on GitHub runners. The exact two-generation matrix from `docs/COMPILER_SUPPORT.md` is also not yet fully covered by the hosted baseline. No dedicated benchmark runner has been provisioned, its labels have not been registered, and no nightly benchmark artifact exists yet.

P0.1.4 remains partial until:

1. The project is pushed to GitHub and the hosted CI matrix runs successfully; compiler logs and artifacts are reviewed.
2. The remaining Tier-1 compiler generations and native platform validation are added and executed.
3. A dedicated Linux x64 machine is frequency-pinned, registered with the required labels, passes the preflight, and produces repeatable nightly benchmark artifacts.

## References

- GitHub-hosted runner labels: https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- Ubuntu 26.04 runner image: https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2604-Readme.md
- Windows Server 2025 runner image: https://github.com/actions/runner-images/blob/main/images/windows/Windows2025-Readme.md
- macOS 15 runner image: https://github.com/actions/runner-images/blob/main/images/macos/macos-15-Readme.md
- Self-hosted runners: https://docs.github.com/en/actions/concepts/runners/self-hosted-runners
- Scheduled workflows: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- sccache GitHub Actions integration: https://github.com/mozilla-actions/sccache-action
