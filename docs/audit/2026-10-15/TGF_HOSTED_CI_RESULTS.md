# TGF hosted CI results — Revision 17

**Date:** 2026-10-15  
**Repository:** https://github.com/tasimas-com/tgf  
**Workflow:** TGF CI  
**Run:** [#13](https://github.com/tasimas-com/tgf/actions/runs/38730051352)  
**Commit:** `c73987167e7bf761ba6fe9ca558cf85b9b0b5780`  
**Conclusion:** success

## Matrix results

| Job | Compiler version from hosted log | CTest | Conclusion |
|---|---|---:|---|
| GCC 15 / Debug / ubuntu-26.04 | GCC 15.2.0 | 7/7 | success |
| GCC 15 / Release / ubuntu-26.04 | GCC 15.2.0 | 7/7 | success |
| LLVM Clang 22 / Debug / ubuntu-26.04 | Ubuntu clang 22.1.2 | 7/7 | success |
| LLVM Clang 22 / Release / ubuntu-26.04 | Ubuntu clang 22.1.2 | 7/7 | success |
| MSVC / Debug / windows-2025 | MSVC 19.51.36260.0; toolset 14.51.36231 | 7/7 | success |
| MSVC / Release / windows-2025 | MSVC 19.51.36260.0; toolset 14.51.36231 | 7/7 | success |
| AppleClang / Debug / macos-15 | Apple clang 17.0.0 (clang-1700.0.13.5) | 7/7 | success |
| AppleClang / Release / macos-15 | Apple clang 17.0.0 (clang-1700.0.13.5) | 7/7 | success |

The eight jobs therefore executed 56 individual CTest test cases successfully.
The seven registered test names were:

1. `showcase_checks`
2. `dependency_dag`
3. `dependency_dag_bindings_rule`
4. `cmake_preset_matrix`
5. `ci_workflow_contract`
6. `benchmark_host_policy`
7. `compiler_policy`

## Artifact inspection

All eight artifacts were downloaded using the GitHub Actions artifact endpoint. Each ZIP passed
`unzip -t`, contained `LastTest.log`, and its test log reported
`100% tests passed, 0 tests failed out of 7`.

| Artifact name | Artifact ID |
|---|---:|
| `ctest-gcc-15-debug-Linux` | 11969543684 |
| `ctest-clang-22-debug-Linux` | 11969513753 |
| `ctest-msvc-vs2022-debug-Windows` | 11969448906 |
| `ctest-appleclang-debug-macOS` | 11969353813 |
| `ctest-appleclang-release-macOS` | 11969328839 |
| `ctest-msvc-vs2022-release-Windows` | 11968944064 |
| `ctest-gcc-15-release-Linux` | 11968903986 |
| `ctest-clang-22-release-Linux` | 11968869037 |

## Accuracy corrections

The Windows compiler path in the hosted logs is under
`C:\\Program Files\\Microsoft Visual Studio\\18\\Enterprise\\VC\\Tools\\MSVC\\14.51.36231`,
and `cl /Bv` reports version `19.51.36260.0`. The workflow's old display label said
"Visual Studio 2022", which does not match that observed installation. The workflow label and
contract test have been corrected to name MSVC 14.51 on the Windows hosted image.

The current workflow uses `actions/cache@v4` to cache CMake build directories. It does not use
sccache as its compiler launcher. The TODO and CI documentation now describe the actual
incremental build-cache behavior.

## Remaining limits

This successful run is a first cross-platform baseline, not the complete compiler support matrix.
GCC 16, Clang 23, and MSVC 14.50 remain unverified. AppleClang 17 is the macOS native compatibility
lane; it does not replace the separate Clang 22/23 Linux compiler target.

The dedicated pinned-frequency benchmark runner has not been provisioned. The nightly benchmark
workflow remains safely gated and no benchmark pass is claimed.

Earlier workflow iterations included failures and cancellations while the Windows PDB handling,
matrix definition, and build cache were being corrected. Run #13 is the final successful run
reviewed for this report.
