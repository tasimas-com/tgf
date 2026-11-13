# P0.1.4 CI and hosted-runner evidence

**Audit date:** 2026-11-13  
**Source revision:** `5db091777f8341550df5b5fba5f78922e7661f50`  
**Scope:** P0.1.4 (CI matrix, build cache, CTest artifacts, nightly benchmark workflow and approved scope waiver)

## 1. Full hosted matrix

GitHub Actions [TGF CI run #378](https://github.com/tasimas-com/tgf/actions/runs/43399403368) completed successfully on the source revision above. All **14/14 jobs passed**: seven targets, each in Debug and Release.

| Hosted image | Compiler lane | Debug | Release |
|---|---|---:|---:|
| `ubuntu-26.04` | GCC 15 | Pass | Pass |
| `ubuntu-26.04` | GCC 16 | Pass | Pass |
| `ubuntu-26.04` | LLVM Clang 22 | Pass | Pass |
| `ubuntu-26.04` | LLVM Clang 23 | Pass | Pass |
| `windows-2025` | MSVC 14.50 / toolset 14.50.35717 | Pass | Pass |
| `windows-2025` | MSVC 14.51 / toolset 14.51.36231 | Pass | Pass |
| `macos-15` | AppleClang 17.0.0 (native macOS compatibility lane) | Pass | Pass |

The workflow explicitly checks GCC/Clang major versions and MSVC's compiler binary version plus `VCToolsVersion`. The observed MSVC compiler binaries were 19.50.35739.0 and 19.51.36260.0. The AppleClang job reported 17.0.0 on `arm64-apple-darwin24.6.0`. All matrix configure steps use warnings-as-errors.

## 2. CTest results and artifact inspection

Every matrix job ran all 11 registered CTest tests and uploaded its own `LastTest.log` artifact. All 14 artifacts were downloaded and inspected on 2026-11-13.

For each ZIP:
- ZIP integrity validation passed.
- Exactly one `LastTest.log` was present.
- The log contained all 11 tests in sequence, 11 `Test Passed.` records, zero `Test Failed.` records, and the final test terminator.

Result: **14/14 valid ZIP artifacts; 11/11 tests per artifact; 154/154 successful CTest executions.**

| Artifact | Artifact ID |
|---|---:|
| `ctest-msvc-14.50-debug-Windows` | 14025505634 |
| `ctest-clang-22-debug-Linux` | 14025000078 |
| `ctest-gcc-15-release-Linux` | 14024682190 |
| `ctest-gcc-16-release-Linux` | 14024641317 |
| `ctest-appleclang-release-macOS` | 14024555949 |
| `ctest-msvc-14.51-debug-Windows` | 14024421700 |
| `ctest-appleclang-debug-macOS` | 14024331750 |
| `ctest-clang-23-release-Linux` | 14024311893 |
| `ctest-msvc-14.51-release-Windows` | 14024291882 |
| `ctest-clang-22-release-Linux` | 14024272052 |
| `ctest-gcc-16-debug-Linux` | 14024202035 |
| `ctest-msvc-14.50-release-Windows` | 14024043907 |
| `ctest-gcc-15-debug-Linux` | 14023558945 |
| `ctest-clang-23-debug-Linux` | 14023369582 |

The tests include the showcase, dependency DAG and its policy regressions, preset graph, CI workflow contract, benchmark-host preflight and inventory tests, compiler policy, coding-standard policy, source-quality workflow contract, and format-discovery regression.

## 3. Source-quality workflow

GitHub Actions [TGF Source Quality run #304](https://github.com/tasimas-com/tgf/actions/runs/43399402789) completed successfully: **2/2 LLVM jobs passed**.

- LLVM/Clang 22.1.8 with IWYU 0.26.
- LLVM/Clang 23.1.6 with IWYU 0.27.
- clang-format checked all 29 repository-owned C/C++ files in each lane.
- The complete TGF Debug builds passed clang-tidy with warnings-as-errors.
- Strict Include-What-You-Use builds passed using the matched IWYU releases.

## 4. Build caching and artifact publication

The CI workflow uses `actions/cache@v6` to cache CMake build directories by runner, compiler, configuration and relevant source/configuration hash. This is build-directory caching, not an sccache compiler launcher. Each matrix job uploads one CTest log through `actions/upload-artifact@v7`, with a 14-day retention period.

## 5. Dedicated benchmark runner: explicit scope boundary

The repository contains the scheduled/manual nightly benchmark workflow, dedicated self-hosted runner label contract, repository-variable readiness gate, read-only CPU-frequency/bare-metal preflight, JSON host inventory collector, regression tests, artifact capture, and an operator runbook.

The project owner approved a scope waiver on 2026-10-17 for physical benchmark-host provisioning/validation and runner registration/first-run acceptance (P0.1.4.f.3 and P0.1.4.f.4). This remains an administrative scope waiver, not hardware evidence.

Consequently:
- No dedicated physical Linux x86-64 benchmark host, pinned-frequency configuration, or sustained thermal validation is claimed.
- No self-hosted benchmark runner or first-run benchmark artifact is claimed.
- The scheduled run [#28](https://github.com/tasimas-com/tgf/actions/runs/43211725951) was skipped by the readiness gate.
- `TGF_BENCHMARK_RUNNER_READY` must remain unset; do not enable the nightly job until the owner reverses the waiver and the physical acceptance procedure in [BENCHMARK_RUNNER_SETUP.md](../../BENCHMARK_RUNNER_SETUP.md) is completed.

## 6. Completion decision

P0.1.4's repository implementation and hosted verification are complete. Its physical benchmark-host operation is **explicitly waived for the current project stage** under the recorded owner decision. Therefore P0.1.4 can be closed only with that limitation attached; it must not be described as having a live dedicated benchmark runner or measured dedicated-host baselines.

This decision closes P0.1.4 for the approved scope and does not satisfy the other Phase 0 exit criteria or authorize Phase 1.
