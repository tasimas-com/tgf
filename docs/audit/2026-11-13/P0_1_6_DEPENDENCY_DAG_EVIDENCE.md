# P0.1.6 — Dependency-DAG checker completion evidence

**Verification date:** 13 November 2026  
**Repository:** [tasimas-com/tgf](https://github.com/tasimas-com/tgf)  
**Verified code commit:** `597887791105638b7b7202ace314bf1af0141596`  
**Task:** P0.1.6 — Dependency-DAG checker script

## Implementation

`tools/check_deps.py` continues to derive its executable module policy from the normative
dependency table in the root `TODO.md` §4 and reports policy/document drift. Existing rules
remain in force: allowed/forbidden module edges, public-header-only consumer dependencies,
canonical cross-module include spelling, RHI backend isolation, include traversal rejection,
non-literal/macro include rejection, public SDK leak rejection, unknown module rejection,
machine-specific absolute-path detection, and repository-layout checks.

The symlink handling was strengthened:

- Each source-tree symlink is resolved strictly. Broken links and resolution loops produce
  diagnostics instead of being silently skipped.
- Source-file symlinks must resolve to a regular file within both the repository root and the
  owning module/consumer scan boundary.
- Directory symlinks inside scanned source trees are rejected. This prevents traversal into a
  different module, consumer root, or external directory.
- Required top-level scan directories must be real directories, not symlink aliases, even when
  an alias happens to point elsewhere inside the repository.

## Regression fixtures

`tools/test_check_deps.py` now explicitly tests:

| Fixture | Expected result |
|---|---|
| Source-file symlink to another file in the same module | Accept |
| Source-file symlink to another file in the same consumer root | Accept |
| Source-file symlink outside the repository | Reject |
| Source-file symlink into another module | Reject |
| Source-file symlink into another consumer root | Reject |
| Directory symlink outside the repository | Reject |
| Directory symlink into another module | Reject |
| Directory symlink into another consumer root | Reject |
| Top-level required directory symlinked to an in-repository directory | Reject |
| Top-level required directory symlinked outside the repository | Reject |
| Ordinary string/character literals containing include, import, Objective-C import, or comment-looking text | Ignore as non-directives |

In addition to these focused fixtures, the suite continues to exercise all **38 allowed** and
**94 forbidden** directed module edges, all consumer roots, public/private header boundaries,
relative-include bypasses, SDK leaks, RHI backend isolation, traversal and absolute paths,
unsupported named-module imports, comment/raw-string boundaries, malformed includes, policy
drift, and repository layout.

## Mandatory build/CI integration

With `TGF_BUILD_TESTS=ON`, CMake requires Python 3.10+ and registers both:

- `dependency_dag`: scans the actual repository tree.
- `dependency_dag_policy_regressions`: executes the positive/negative fixture suite.

The hosted CI workflow installs Python 3.13 before configure/build/test in every compiler/OS
matrix job. Thus the checker cannot be skipped merely because a runner lacks a system Python.

## Hosted verification

### Full compiler/OS/configuration matrix

[TGF CI run #388](https://github.com/tasimas-com/tgf/actions/runs/43416718257)  
Run ID: `43416718257`  
Commit: `597887791105638b7b7202ace314bf1af0141596`  
Result: **14/14 jobs passed**

The matrix covers GCC 15 and 16, LLVM Clang 22 and 23, MSVC 14.50 and 14.51, and AppleClang,
each in Debug and Release.

### Source quality

[Source Quality run #314](https://github.com/tasimas-com/tgf/actions/runs/43416718274)  
Run ID: `43416718274`  
Commit: `597887791105638b7b7202ace314bf1af0141596`  
Result: **2/2 LLVM jobs passed**

### CTest artifact register

All 14 artifacts were downloaded from run #388. Every ZIP passed integrity validation,
contained exactly one `LastTest.log`, and recorded 11/11 CTest tests passed with zero failures.
The dependency policy regression output in each log explicitly reports all 38 allowed and
94 forbidden edges and the new symlink/literal-lookalike test coverage.

| Artifact | GitHub artifact ID | CTest result |
|---|---:|---:|
| `ctest-msvc-14.50-debug-Windows` | 14032526879 | 11/11 passed |
| `ctest-msvc-14.50-release-Windows` | 14031678338 | 11/11 passed |
| `ctest-msvc-14.51-debug-Windows` | 14031713673 | 11/11 passed |
| `ctest-msvc-14.51-release-Windows` | 14032715600 | 11/11 passed |
| `ctest-gcc-15-debug-Linux` | 14031713590 | 11/11 passed |
| `ctest-gcc-15-release-Linux` | 14031379734 | 11/11 passed |
| `ctest-gcc-16-debug-Linux` | 14032251565 | 11/11 passed |
| `ctest-gcc-16-release-Linux` | 14031259570 | 11/11 passed |
| `ctest-clang-22-debug-Linux` | 14032191143 | 11/11 passed |
| `ctest-clang-22-release-Linux` | 14031009892 | 11/11 passed |
| `ctest-clang-23-debug-Linux` | 14031489505 | 11/11 passed |
| `ctest-clang-23-release-Linux` | 14031892718 | 11/11 passed |
| `ctest-appleclang-debug-macOS` | 14031109413 | 11/11 passed |
| `ctest-appleclang-release-macOS` | 14031841998 | 11/11 passed |

**Aggregate:** 154/154 CTest executions passed; zero failed. The matrix and artifact evidence
supports P0.1.6 completion. It does not imply that the remaining Phase 0 tasks are complete;
Phase 0 remains open and Phase 1 remains blocked.
