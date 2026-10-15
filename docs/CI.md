# Continuous integration and benchmark infrastructure

**Hosted baseline verified twice:** 15 October 2026 — GitHub Actions runs [#13](https://github.com/tasimas-com/tgf/actions/runs/38730051352) and [#14](https://github.com/tasimas-com/tgf/actions/runs/38738723466).

TGF uses two GitHub Actions workflows:

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) builds and runs CTest on pushes,
  pull requests, and manual dispatches.
- [`.github/workflows/nightly-benchmarks.yml`](../.github/workflows/nightly-benchmarks.yml)
  runs the core showcase benchmarks only on a dedicated Linux host after its CPU-frequency
  preflight passes.

## Actual hosted build-and-test matrix

Runs #13 and #14 each completed successfully with **8/8 jobs**. Each compiler target ran Debug and Release.

| Hosted runner | Compiler actually reported by the job | Debug | Release |
|---|---|---:|---:|
| `ubuntu-26.04` | GCC 15.2.0 | Pass | Pass |
| `ubuntu-26.04` | Ubuntu LLVM Clang 22.1.2 | Pass | Pass |
| `windows-2025` | MSVC 19.51.36260.0, toolset 14.51.36231 | Pass | Pass |
| `macos-15` | AppleClang 17.0.0 (Xcode) | Pass | Pass |

The Windows runner log identifies the installed compiler path under
`Microsoft Visual Studio/18/Enterprise/VC/Tools/MSVC/14.51.36231`. The job is therefore
described as **MSVC 14.51 on the Windows hosted image**. It must not be described as Visual Studio
2022 merely because an earlier workflow label used that name.

Every one of the eight jobs passed all seven CTest entries:

1. `showcase_checks`
2. `dependency_dag`
3. `dependency_dag_bindings_rule`
4. `cmake_preset_matrix`
5. `ci_workflow_contract`
6. `benchmark_host_policy`
7. `compiler_policy`

That is **56 successful test executions per run, 112 across both accepted runs**. Each job uploaded a `LastTest.log` artifact. All eight
artifact ZIPs were downloaded, checked for ZIP integrity, and inspected; every log reported
`100% tests passed, 0 tests failed out of 7`.

| Artifact | GitHub artifact ID |
|---|---:|
| `ctest-gcc-15-debug-Linux` | 11969543684 |
| `ctest-clang-22-debug-Linux` | 11969513753 |
| `ctest-msvc-vs2022-debug-Windows` | 11969448906 |
| `ctest-appleclang-debug-macOS` | 11969353813 |
| `ctest-appleclang-release-macOS` | 11969328839 |
| `ctest-msvc-vs2022-release-Windows` | 11968944064 |
| `ctest-gcc-15-release-Linux` | 11968903986 |
| `ctest-clang-22-release-Linux` | 11968869037 |

Run #13: <https://github.com/tasimas-com/tgf/actions/runs/38730051352> (commit `c73987167e7bf761ba6fe9ca558cf85b9b0b5780`).  
Run #14: <https://github.com/tasimas-com/tgf/actions/runs/38738723466> (commit `8a2cfff31e4502ba142e444a01c0308a489dfac0`).

## Caching and artifacts

The current workflow uses `actions/cache@v4` to cache the CMake build directory per runner,
compiler, configuration, and relevant source/configuration hash. This is **incremental build
caching**, not an sccache compiler cache. The CTest log is uploaded per job with
`actions/upload-artifact@v7` and retained for 14 days.

The CI contract test checks the explicit four-target/two-configuration matrix, Windows MSVC/Ninja
configuration, compiler-version probe, cache path, artifact upload, and nightly runner guard.

## What this run does not prove

This is a successful cross-platform baseline verified twice, not the full two-generation Tier-1 compiler matrix.
It verified GCC 15, Clang 22, and MSVC toolset 14.51; it did not verify GCC 16, Clang 23, or
MSVC 14.50. AppleClang 17 is the macOS native compatibility lane, not a substitute for the
separate Clang 22/23 requirement. P0.1.3.g and P0.1.4.g therefore remain partial.

## Second-run artifact evidence

Run #14 artifact IDs: `11975135189`, `11975130127`, `11974769084`, `11974489507`, `11973969685`, `11973939741`, `11973764489`, and `11973644936`. Each archive passed ZIP integrity checks and contained a LastTest.log with seven successful test entries.

## Dedicated nightly benchmark runner

See the step-by-step [dedicated benchmark runner setup guide](BENCHMARK_RUNNER_SETUP.md) before provisioning or enabling a host.


The nightly workflow remains intentionally gated. It requires a self-hosted Linux x64 runner with
all labels:

```text
self-hosted, linux, x64, tgf-benchmark-pinned
```

It also requires the repository Actions variable `TGF_BENCHMARK_RUNNER_READY=true`. That
variable must remain unset until a dedicated machine is provisioned and
`python3 tools/check_benchmark_host.py` passes. The machine must use the `performance` governor
and fixed minimum/maximum CPU frequency policies. No successful nightly benchmark run is claimed.

## Local workflow checks

These repository checks are registered in CTest whenever Python 3 is found:

- `ci_workflow_contract`: verifies the workflow matrix, toolchain labels, Windows MSVC/Ninja
  steps, build cache, artifact upload, and benchmark safety gate.
- `benchmark_host_policy`: tests the CPU-frequency policy checker using controlled fixtures.

## Official references

- [GitHub-hosted runner labels and hardware](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [CMake compiler launcher generator support](https://cmake.org/cmake/help/latest/prop_tgt/LANG_COMPILER_LAUNCHER.html)
- [MSVC Developer Command Prompt action](https://github.com/ilammy/msvc-dev-cmd)
- [Checkout action](https://github.com/actions/checkout)
- [Upload artifact action](https://github.com/actions/upload-artifact)
- [GitHub Actions cache](https://github.com/actions/cache)
- [GitHub Actions self-hosted runners](https://docs.github.com/en/actions/concepts/runners/self-hosted-runners)
