# TGF hosted CI results — Revision 18

**Repository:** https://github.com/tasimas-com/tgf  
**Run #13:** https://github.com/tasimas-com/tgf/actions/runs/38730051352  
**Run #14:** https://github.com/tasimas-com/tgf/actions/runs/38738723466  
**Date:** 2026-10-15

## Run #14 — second successful baseline

Commit: `8a2cfff31e4502ba142e444a01c0308a489dfac0`  
Conclusion: **success, 8/8 jobs**.

| Job | Compiler reported in log | CTest | Conclusion |
|---|---|---:|---|
| GCC 15 / Debug / ubuntu-26.04 | GCC 15.2.0 | 7/7 | success |
| GCC 15 / Release / ubuntu-26.04 | GCC 15.2.0 | 7/7 | success |
| LLVM Clang 22 / Debug / ubuntu-26.04 | Ubuntu Clang 22.1.2 | 7/7 | success |
| LLVM Clang 22 / Release / ubuntu-26.04 | Ubuntu Clang 22.1.2 | 7/7 | success |
| MSVC 14.51 / Debug / windows-2025 | MSVC 19.51.36260.0, toolset 14.51.36231 | 7/7 | success |
| MSVC 14.51 / Release / windows-2025 | MSVC 19.51.36260.0, toolset 14.51.36231 | 7/7 | success |
| AppleClang / Debug / macos-15 | Apple clang 17.0.0 | 7/7 | success |
| AppleClang / Release / macos-15 | Apple clang 17.0.0 | 7/7 | success |

The seven CTest entries are `showcase_checks`, `dependency_dag`, `dependency_dag_bindings_rule`, `cmake_preset_matrix`, `ci_workflow_contract`, `benchmark_host_policy`, and `compiler_policy`. This is 56 successful CTest executions in run #14.

All eight artifacts were downloaded and ZIP-integrity checked. Each contains `LastTest.log` with seven `Test Passed.` entries.

| Artifact | ID |
|---|---:|
| `ctest-gcc-15-debug-Linux` | 11973939741 |
| `ctest-gcc-15-release-Linux` | 11973764489 |
| `ctest-clang-22-debug-Linux` | 11973644936 |
| `ctest-clang-22-release-Linux` | 11974489507 |
| `ctest-appleclang-debug-macOS` | 11973969685 |
| `ctest-appleclang-release-macOS` | 11974769084 |
| `ctest-msvc-14.51-debug-Windows` | 11975130127 |
| `ctest-msvc-14.51-release-Windows` | 11975135189 |

## Run #13 — first successful baseline

Run #13 also completed 8/8 jobs and its eight artifacts were downloaded and inspected. Run URL: https://github.com/tasimas-com/tgf/actions/runs/38730051352.

## Accuracy corrections

The Windows runner's actual compiler is MSVC 19.51.36260.0 with toolset 14.51.36231, installed under a Visual Studio 18 Enterprise runner image. The workflow label and documentation use the actual compiler identity rather than the earlier inaccurate Visual Studio 2022 display label.

The workflow uses `actions/cache@v4` to cache CMake build directories. It does not use sccache as an MSVC compiler launcher. `/FS` serializes parallel PDB writes for the Ninja/MSVC build.

## Remaining limits

The matrix verifies GCC 15, Clang 22, MSVC 14.51, and AppleClang 17. It does not prove GCC 16, Clang 23, or MSVC 14.50. The dedicated pinned-frequency benchmark runner remains unprovisioned and safely gated. Phase 0 remains incomplete.
