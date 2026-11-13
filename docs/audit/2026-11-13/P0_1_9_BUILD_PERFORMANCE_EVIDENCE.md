# P0.1.9 — Build-time budgets and public-header cost evidence

**Date:** 2026-11-13  
**Verified implementation commit:** d444003c5c839294f1c31e79d6a4c7d5f95f5f18  
**Task:** Clean and incremental build-time budgets plus per-header compile-cost reporting.

## Delivered

- cmake/build-performance-budgets.json defines the canonical baseline: Ninja, Clang 23,
  Release, two parallel build jobs, with hard ceilings of 180 seconds (clean) and 45 seconds
  (one-source incremental).
- tools/measure_build.py validates the requested build directory's generator, compiler
  identity/version, and configuration. It removes generated build outputs with the CMake clean
  target, times the full default build, touches core/src/profiler.cpp for an incremental
  rebuild, verifies that the probe was actually recompiled, and restores the original source
  timestamp even if the build fails. It writes JSON/Markdown results and command logs.
- tools/report_header_costs.py consumes Clang time-trace JSON and the generated header
  manifest. It emits sorted JSON and Markdown costs for each isolated public-header translation
  unit.
- The public-header check discovers first-party headers below each module's include/tgf/
  directory, generates one translation unit per header, and includes each header twice. The
  check remains part of ordinary CTest builds; only the dedicated cost lane enables Clang time
  tracing on that target.
- Three mandatory CTest checks cover the measurement tool, the header report parser/writer, and
  the build-performance policy wiring. docs/BUILD_PERFORMANCE.md explains the baseline,
  commands, report semantics, and comparison limitations.

## Measurement contract

The hosted performance lane runs on GitHub-hosted Ubuntu 26.04 with Ninja, Clang 23.1.6,
Release configuration, LTO disabled, and two parallel jobs. It does not restore a build cache.
Tool installation and CMake configuration are excluded from the timers. The clean measurement
runs after the CMake clean target; the incremental measurement touches one implementation
translation unit, rebuilds, confirms the compiler command, and restores the original timestamp.

| Measurement | Result | Hard ceiling |
|---|---:|---:|
| Clean default build | **3.441 s** | 180 s |
| One-source incremental rebuild | **1.194 s** | 45 s |
| Public headers costed | **15** | all discovered |

The report ranks public headers by Clang's Total ExecuteCompiler duration for one isolated
translation unit containing that header twice. In this run the three highest values were:

| Public header | Isolated translation-unit duration |
|---|---:|
| tgf/core/hash.hpp | 118.198 ms |
| tgf/core/spsc.hpp | 86.975 ms |
| tgf/core/slot_map.hpp | 59.499 ms |

**Interpretation limit:** this duration includes compiler/front-end startup overhead and
transitive includes. It is a consistent relative proxy for comparing headers in this one
compiler/configuration/runner, not a pure measurement of the header's own tokens and not a
value that can be summed to predict total build time. The Clang trace did not emit matching
per-header Source spans in this run, so the report uses the isolated translation-unit
duration as its primary metric. Do not compare absolute values across compiler versions,
configurations, or runner classes.

## Full compiler-matrix verification

[TGF CI run #398](https://github.com/tasimas-com/tgf/actions/runs/43458777497) ran the final
implementation commit and passed all **14/14** jobs:

| Target / compiler | Configuration | Artifact ID | CTest result |
|---|---|---:|---:|
| GCC 15 | Debug | [14054847720](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14054847720) | 15/15 |
| GCC 15 | Release | [14056110479](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14056110479) | 15/15 |
| GCC 16 | Debug | [14055890717](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14055890717) | 15/15 |
| GCC 16 | Release | [14056095507](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14056095507) | 15/15 |
| LLVM Clang 22 | Debug | [14054124176](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14054124176) | 15/15 |
| LLVM Clang 22 | Release | [14054139130](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14054139130) | 15/15 |
| LLVM Clang 23 | Debug | [14054293827](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14054293827) | 15/15 |
| LLVM Clang 23 | Release | [14054408982](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14054408982) | 15/15 |
| MSVC 14.50 | Debug | [14054639321](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14054639321) | 15/15 |
| MSVC 14.50 | Release | [14055402091](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14055402091) | 15/15 |
| MSVC 14.51 | Debug | [14054478622](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14054478622) | 15/15 |
| MSVC 14.51 | Release | [14055337075](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14055337075) | 15/15 |
| AppleClang | Debug | [14055102476](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14055102476) | 15/15 |
| AppleClang | Release | [14055561789](https://github.com/tasimas-com/tgf/actions/runs/43458777497/artifacts/14055561789) | 15/15 |

All 14 ZIPs were downloaded and integrity-checked. Each contained exactly one LastTest.log;
the logs recorded 15 test starts, 15 Test Passed outcomes, and zero Test Failed outcomes.
The three new tests—build_measurement_tool, header_cost_reporter, and
build_performance_policy—were present and passed in every configuration. Total:
**210/210 CTest executions**.

[Source Quality run #324](https://github.com/tasimas-com/tgf/actions/runs/43458777647) passed
both LLVM 22/23 formatting, clang-tidy, and IWYU jobs.

[Build Performance run #4](https://github.com/tasimas-com/tgf/actions/runs/43458777543) passed.
Its [downloadable performance-report artifact](https://github.com/tasimas-com/tgf/actions/runs/43458777543/artifacts/14055341519)
contains build-performance.json, build-performance.md, header-costs.json,
header-costs.md, and the clean/incremental build logs.

## Closure boundary

P0.1.9 is complete. P0.1.8 (formal license, SBOM tooling, and third-party policy) remains
open; P0.2–P0.5 work and all other Phase 0 exit criteria remain open. Phase 0 is not complete,
and Phase 1 remains blocked.
