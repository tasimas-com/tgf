# Continuous integration and benchmark infrastructure

**P0.1.3 verified complete:** 17 October 2026 — the latest Tier-1 compiler matrix [run #193](https://github.com/tasimas-com/tgf/actions/runs/39056856383) passed 14/14 jobs and the required source-quality [run #119](https://github.com/tasimas-com/tgf/actions/runs/39056856378) passed both LLVM 22/23 analysis jobs. See the evidence below.

TGF uses three GitHub Actions workflows:

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) builds and runs CTest on pushes,
  pull requests, and manual dispatches.
- [`.github/workflows/source-quality.yml`](../.github/workflows/source-quality.yml) runs the required source-quality checks with LLVM/Clang 22 and 23: clang-format, clang-tidy, and Include-What-You-Use.
- [`.github/workflows/nightly-benchmarks.yml`](../.github/workflows/nightly-benchmarks.yml)
  runs the core showcase benchmarks only on a dedicated Linux host after its CPU-frequency
  preflight passes.

## Earlier hosted Tier-1 matrix baseline (run #30)

Run #30 completed successfully with **14/14 jobs**: seven compiler targets, each built and tested in Debug and Release. The compiler-version probes assert GCC/Clang major versions and both the MSVC compiler version and selected `VCToolsVersion`; no job may silently substitute another toolset. All configure steps explicitly set `TGF_WARNINGS_AS_ERRORS=ON`.

| Hosted runner | Compiler actually reported by the job | Debug | Release |
|---|---|---:|---:|
| `ubuntu-26.04` | GCC 16.0.1 | Pass | Pass |
| `ubuntu-26.04` | GCC 15.2.0 | Pass | Pass |
| `ubuntu-26.04` | Ubuntu LLVM Clang 23.1.4 | Pass | Pass |
| `ubuntu-26.04` | Ubuntu LLVM Clang 22.1.2 | Pass | Pass |
| `windows-2025` | MSVC 19.51.36260.0, toolset 14.51.36231 | Pass | Pass |
| `windows-2025` | MSVC 19.50.35739.0, toolset 14.50.35717 | Pass | Pass |
| `macos-15` | AppleClang 17.0.0 (Xcode compatibility lane) | Pass | Pass |

The MSVC 14.50 lane installs the exact Visual Studio component when absent, then checks
`cl /Bv` and `VCToolsVersion` before configuring. Its selected path was
`Microsoft Visual Studio/18/Enterprise/VC/Tools/MSVC/14.50.35717`; the 14.51 path was
`Microsoft Visual Studio/18/Enterprise/VC/Tools/MSVC/14.51.36231`.

Every job passed all seven CTest entries: `showcase_checks`, `dependency_dag`,
`dependency_dag_bindings_rule`, `cmake_preset_matrix`, `ci_workflow_contract`,
`benchmark_host_policy`, and `compiler_policy`. All 14 uploaded artifacts were downloaded
and inspected: each ZIP passed its integrity check and contained a `LastTest.log` with seven
passing tests. That is **98/98 successful CTest executions**. Every showcase log also reported
**26 checks, 0 failed**.

| Artifact | GitHub artifact ID |
|---|---:|
| `ctest-msvc-14.50-release-Windows` | 11980290689 |
| `ctest-msvc-14.51-release-Windows` | 11979055145 |
| `ctest-appleclang-debug-macOS` | 11978820974 |
| `ctest-gcc-15-release-Linux` | 11978656249 |
| `ctest-msvc-14.51-debug-Windows` | 11978606404 |
| `ctest-msvc-14.50-debug-Windows` | 11978577365 |
| `ctest-clang-23-release-Linux` | 11978356521 |
| `ctest-clang-22-debug-Linux` | 11978311464 |
| `ctest-clang-22-release-Linux` | 11978217757 |
| `ctest-gcc-16-release-Linux` | 11977538647 |
| `ctest-clang-23-debug-Linux` | 11977389139 |
| `ctest-appleclang-release-macOS` | 11977284004 |
| `ctest-gcc-15-debug-Linux` | 11977063741 |
| `ctest-gcc-16-debug-Linux` | 11976839382 |

Run #30: <https://github.com/tasimas-com/tgf/actions/runs/38745686719>
(commit `a4169289e8ea031b005aefba7a89d9e13a4075c2`). The run was triggered by the pull request
and validates the exact PR head.

## Historical initial hosted baseline (runs #13 and #14)

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

The CI contract test checks the explicit seven-target/two-configuration matrix, exact compiler binaries/toolsets and version probes, Windows MSVC/Ninja configuration, cache path, artifact upload, and nightly runner guard.

## Module dependency enforcement (P0.1.6)

`tools/check_deps.py` enforces the dependency matrix in the root `TODO.md` §4. It rejects
undeclared TGF module edges, non-canonical cross-module includes, include-path traversal,
macro-based include directives that cannot be validated, unknown module names, and includes
that bypass another module's public header tree. `widgets` can depend only on `ui`;
`pro` can depend only on `widgets` and `ui`; `tools`, `host`, and `c` can consume any
architectural layer through public headers; and `bindings` can consume only the public C ABI.
RHI backend implementations are isolated from one another, and public headers cannot expose
the platform/graphics SDK and implementation-only third-party headers covered by the policy.
The checker also retains repository-layout and machine-specific absolute-path checks.

The checker parses the normative table and fails when its executable policy drifts from
`TODO.md`. Its black-box regression suite exercises all **38 allowed** and **94 forbidden**
directed module edges, along with relative-include bypasses, private/missing public headers,
SDK leaks, RHI cross-backend includes, uppercase/unknown module names, path traversal,
non-literal includes, policy drift, and path hygiene.

When `TGF_BUILD_TESTS=ON`, CMake now requires a Python interpreter instead of silently
omitting policy tests. CTest runs both `dependency_dag` (the real repository) and
`dependency_dag_policy_regressions` (the positive/negative fixture suite). Every hosted
compiler/OS matrix job explicitly installs Python 3.13 with `actions/setup-python@v7`
before configure/build/test, so the dependency gate cannot disappear on a runner missing
a system Python installation.

## Source-quality enforcement (P0.1.3.c–e)

The dedicated source-quality workflow runs on pushes, pull requests, and manual dispatches for both supported LLVM generations. It installs version-matched clang-format and clang-tidy packages, checks every repository-owned C/C++ source file, and builds IWYU from its matching release tag (0.26 for LLVM 22; 0.27 for LLVM 23). It then builds TGF with `TGF_ENABLE_CLANG_TIDY=ON` and `TGF_ENABLE_IWYU=ON`, keeping warnings-as-errors enabled. These jobs are required CI checks: missing tools, unsupported versions, format drift, analyzer diagnostics, or IWYU include violations fail the workflow. The local CMake switches remain opt-in so ordinary developers are not forced to install LLVM analysis tools.

`source_quality_workflow` CTest protects the presence of this CI lane, its LLVM/IWYU compatibility pairs, and strict analyzer configuration. `format_checker_discovery` verifies that the formatter discovers source files in future module directories while excluding generated and vendored trees.

## Latest completion evidence (P0.1.3)

The full Tier-1 matrix [run #193](https://github.com/tasimas-com/tgf/actions/runs/39056856383) passed all 14 compiler/configuration jobs across MSVC 14.50/14.51, Clang 22/23, GCC 15/16, and AppleClang 17 in Debug and Release. All 14 CTest artifacts were downloaded, ZIP-integrity checked, and inspected: each contained 11/11 passing CTest cases and the showcase reported 26 checks with zero failures (154/154 CTest executions).

The dedicated source-quality workflow [run #119](https://github.com/tasimas-com/tgf/actions/runs/39056856378) passed both LLVM jobs. clang-format checked all 29 repository-owned C/C++ source files; complete TGF Debug builds passed clang-tidy with warnings-as-errors; strict IWYU passed on LLVM 22.1.8/IWYU 0.26 and LLVM 23.1.4/IWYU 0.27. The generated duplicate-include header self-containment harness is intentionally excluded from IWYU only; implementation and showcase translation units remain checked.

Together these runs satisfy P0.1.3. They do not provision or enable the dedicated pinned-frequency benchmark runner, prove Tier-A competitor benchmarks, close the remaining ADR/research-spike work, or satisfy the overall Phase 0 exit criteria. The earlier run #30 evidence and artifact inventory above are retained as historical baseline records.

## Second-run artifact evidence

Run #14 artifact IDs: `11975135189`, `11975130127`, `11974769084`, `11974489507`, `11973969685`, `11973939741`, `11973764489`, and `11973644936`. Each archive passed ZIP integrity checks and contained a LastTest.log with seven successful test entries.

## Dedicated nightly benchmark runner

See the step-by-step [dedicated benchmark runner setup guide](BENCHMARK_RUNNER_SETUP.md) before provisioning or enabling a host.


The nightly workflow now also runs tools/check_benchmark_host.py --require-bare-metal
to require x86-64 and positive no-VM evidence, then captures
benchmark-artifacts/host-inventory.json with tools/collect_benchmark_host_inventory.py.
The inventory contains CPU topology/microcode, memory, non-serial DMI/firmware fields, every
CPUFreq policy, thermal-zone/hwmon readings, OS/kernel and selected build-tool versions, and
allowlisted runner metadata. It is uploaded with the benchmark report. The collector is
read-only; host frequency changes remain an administrator-controlled provisioning step.

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
- `benchmark_host_policy`: ten controlled scenarios cover CPU-frequency policy validation and fail-closed x86-64/bare-metal detection.
- `benchmark_host_inventory`: five controlled scenarios validate CPU/memory/OS/frequency/thermal/DMI collection, virtualization metadata, and runner-metadata allowlisting.

## Official references

- [GitHub-hosted runner labels and hardware](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [CMake compiler launcher generator support](https://cmake.org/cmake/help/latest/prop_tgt/LANG_COMPILER_LAUNCHER.html)
- [MSVC Developer Command Prompt action](https://github.com/ilammy/msvc-dev-cmd)
- [Checkout action](https://github.com/actions/checkout)
- [Upload artifact action](https://github.com/actions/upload-artifact)
- [GitHub Actions cache](https://github.com/actions/cache)
- [GitHub Actions self-hosted runners](https://docs.github.com/en/actions/concepts/runners/self-hosted-runners)


## Coding standard policy (P0.1.5)

The normative coding rules are in [CODING_STANDARD.md](CODING_STANDARD.md). They define
naming, includes, ownership/lifetime, error handling, thread-safety, real-time and memory
discipline, public API documentation, and the pre-1.0 / 1.x / planned C ABI stability levels.
The style values are sourced from `.clang-format`, while `.clang-tidy` points back to the
same normative document.

The `coding_standard_policy` CTest entry runs
`tools/check_coding_standard.py`. It protects the required policy sections and key
architectural commitments from accidental deletion or drift. It is a documentation-contract
check, not a substitute for code review, clang-format, clang-tidy, or ABI analysis.
