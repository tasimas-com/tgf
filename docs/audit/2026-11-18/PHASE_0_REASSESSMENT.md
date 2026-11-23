# TGF Phase 0 — independent reassessment

**Audit date:** 18 November 2026  
**Repository:** [tasimas-com/tgf](https://github.com/tasimas-com/tgf)  
**Branch:** `main`  
**Code snapshot reviewed:** `7e9dad1581be59e1df6adf9caa7572a1129d518e`  
**Current hosted verification at audit time:** `7e9dad1581be59e1df6adf9caa7572a1129d518e`  
**Task ledger:** [`TODO.md`](../../../TODO.md)

## 1. Method and scope

The Phase 0 checkboxes were deliberately ignored as evidence. The current recursive repository
tree was reviewed, including the C++ public headers and implementations, showcase code and
tests, CMake project files/modules/presets, compiler and dependency policies, Python checker
and regression-test scripts, GitHub Actions workflows, third-party inventory and license
material, ADRs, and project documentation. The source review focused on whether the acceptance
criteria are implemented, whether policy gates are fail-closed and connected to CTest/CI, and
whether hosted evidence actually covers the claimed scope.

The review included, among other areas:

- `core/include/tgf/core/` and `core/src/`, including memory, module allocator, mapping,
  profiler, result/error, math, time, containers and concurrency primitives;
- `samples/showcase/`, especially `checks_core.cpp`, `bench_core.cpp`, the harness and JSON
  reporting path;
- root/CMake module configuration, presets, compiler support, dependency policy, build-time
  measurement and header-cost report tooling;
- `tests/CMakeLists.txt`, every repository policy checker and its unit/fixture tests;
- all current GitHub Actions workflows and their latest run/job status;
- README, status, design, compiler/CI/build/dependency/benchmark/runner docs and ADRs relevant
  to Phase 0.

This is a repository/code/documentation audit plus review of hosted GitHub Actions evidence.
It is **not** a claim that a fresh local build was run in this audit environment, nor that every
physical target, GPU, runner, or competitor application was exercised. Existing test/CI results
are cited with their actual scope.

## 2. Executive result

**Phase 0 is not complete. Phase 1 remains blocked.**

The foundational repository and policy infrastructure is much stronger than the original
snapshot, and P0.1.8 is now genuinely complete. However, this report's MSVC release-status conclusion requires the 23 November erratum below;
the asset inventory is absent; the P0.3 comparative benchmark harness and measured competitor
baselines are absent; most research spikes and most individual ADRs have not been delivered.

## 3. Current hosted evidence

On 17 November 2026, the following workflows completed successfully on the current code
snapshot:

| Workflow | Run | Result | What it proves |
|---|---|---:|---|
| TGF CI | [#412](https://github.com/tasimas-com/tgf/actions/runs/44089512975) | 14/14 jobs passed | The **configured** seven-target × Debug/Release matrix passed: GCC 15/16, Clang 22/23, MSVC 14.50/14.51, AppleClang 17 |
| Source Quality | [#338](https://github.com/tasimas-com/tgf/actions/runs/44089512797) | 2/2 jobs passed | The current LLVM 22/23 formatting, clang-tidy and IWYU lanes passed |
| Build Performance | [#18](https://github.com/tasimas-com/tgf/actions/runs/44089512759) | Passed | The dedicated clean/incremental build-budget and public-header reporting workflow passed |
| SPDX SBOM | [#13](https://github.com/tasimas-com/tgf/actions/runs/44089512739) | Passed | Third-party policy validation and SPDX 2.3 generation/artifact publication passed |

The run #412 result verifies the matrix that is checked into the repository; it does not prove
that matrix is still current for every compiler family. Do not infer that every CTest ZIP was
downloaded and inspected in run #412: the current evidence cited here is the workflow's
reported job success. Earlier per-artifact inspection records remain available in the dated
13 November evidence reports.

## 4. Phase 0 task reassessment

### P0.1 — Repository and tooling

| Task | Reassessed status | Findings |
|---|---|---|
| P0.1.1 Repository layout | **Complete** | Required top-level module, tooling, sample, test, documentation, third-party and CMake layout exists. The future GUI modules remain README-only architecture placeholders; that is not a missing layout requirement. |
| P0.1.2 CMake presets | **Complete** | Configure/build/test presets cover Debug, Release, RelWithDebInfo, profiling and sanitizers; shared Release and compatibility presets remain. Compiler-aware sanitizer selection and `tools/check_presets.py` are connected to CTest. Existing Linux build/test evidence covers supported configurations; native Visual Studio presets are separately defined. |
| P0.1.3 Compiler policy and quality | **Partial — awaiting revalidation** | Warnings-as-errors, clang-format, clang-tidy, IWYU and GCC/Clang policy lanes are implemented and hosted. The 23 November correction confirms the stable MSVC pair is 14.51/14.50; the current revised manifest/checker/CI commit still needs its full matrix run. |
| P0.1.4 Hosted CI and benchmark runner | **Partial** | The workflows, matrix, artifacts, preflight, inventory collector, operator runbook and scope waiver are implemented. The physical benchmark host and self-hosted runner remain explicitly waived; its 14.51/14.50 stable matrix is being reverified after the policy-checker update. |
| P0.1.5 Coding standard | **Complete** | The normative standard, formatter/tidy alignment and CTest documentation-contract checker exist. This is a policy gate, not proof that every future code change is automatically semantically correct. |
| P0.1.6 Dependency DAG | **Complete** | The checker is tied to the normative table and has broad positive/negative edge tests, symlink-boundary tests, literal-lookalike tests, required CTest registration and hosted evidence. The 13 November P0.1.6 report records the complete fixture and artifact inspection. |
| P0.1.7 Contributor/governance files | **Complete** | Contributor guide, Code of Conduct, issue forms, PR template, ADR template/index and the community governance CTest guard exist. Server-side GitHub report-content configuration is correctly documented as external to repository files. |
| P0.1.8 License/SBOM/third-party policy | **Complete — 17 November** | Root Apache-2.0 LICENSE and scoped NOTICE, accepted ADR-0016, machine-readable dependency inventory, fail-closed dependency/action/CMake/vendored-file policy, SPDX 2.3 generator, CTest regression suite and dedicated SBOM workflow/artifact exist. The SBOM is direct repository-dependency scope, not a recursive inventory of upstream actions, runner images, OS packages or compiler/Python distributions. |
| P0.1.9 Build-time/header costs | **Complete** | Clean and incremental build timing budgets, incremental probe verification, per-header self-containment TUs, Clang time-trace parser/reports, CTest guards and dedicated hosted workflow exist. The historical run #4 report has concrete time and header-cost output. |

#### MSVC version policy — 23 November correction

This report's 18 November conclusion incorrectly treated MSVC Build Tools 14.52 as generally
available. Microsoft's current [MSVC compiler-version table](https://learn.microsoft.com/en-us/cpp/overview/compiler-versions)
marks 14.52 as **Preview**. The same table lists 14.51 as Standard support with EOL in
February 2027 and 14.50 as Long-Term support with EOL in November 2028. The stable,
supported Tier-1 pair is therefore **14.51/14.50**, not 14.52/14.51.

The CI matrix has been restored to the historically passing 14.51 hosted-image lane and the
14.50 side-by-side installer lane. The preview compiler is intentionally excluded from the
stable release gate. The 23 November policy update adds a stricter manifest-to-matrix checker
and negative regression cases; the corrected current commit must pass all 14 compiler/OS/
configuration jobs and the source-quality workflow before P0.1.3.g/P0.1.4.g are closed.

### P0.2 — Existing asset audit

| Task | Reassessed status | Findings |
|---|---|---|
| P0.2.1 Inventory existing scaffold and ImGui-derived fork | **Not started** | The repository contains no current asset inventory that identifies the earlier prototype's files, platform glue, RHI sketches, shaders or tests and assesses their provenance/reusability. |
| P0.2.2 Keep/rewrite/delete decisions and ADR-0018 | **Not started** | ADR-0018 is absent. A historical source audit is not a substitute for module-by-module dispositions. |
| P0.2.3 Lessons learned | **Not started** | `docs/lessons.md` is absent; required engineering lessons have not been assembled as the specified deliverable. |

The current tree's lack of vendored ImGui/source files does not answer what happened to the
earlier assets, nor provide a documented decision to retain, rewrite or discard them.

### P0.3 — Benchmark and comparison harness

| Task | Reassessed status | Findings |
|---|---|---|
| P0.3.1 Reference hardware/OS tiers | **Partial** | The dedicated runner runbook and build-measurement hosted environment specify useful constraints, but there is no reference-tier specification for the 4K/144 Hz/mixed-DPI rig and native Wayland system required by the plan. |
| P0.3.2 Identical scenarios | **Partial** | S1–S15 are documented scenario names. No cross-framework implementations or validated equal-visual/equal-DPI fixtures were found. |
| P0.3.3 Metrics/statistical method | **Not started** | The complete runtime metrics, noise-floor measurement and statistical comparison method are not delivered. Build-time compiler metrics do not satisfy this runtime GUI requirement. |
| P0.3.4 Tiered baselines | **Partial** | The Tier A/B/C strategy is documented, but no measured Tier-A competitor result set or comparable baseline was found. |
| P0.3.5 Result store/dashboard/regression gate | **Partial** | `tgf_showcase --json` exports local core-smoke data. There is no persistent comparative history, dashboard or statistically meaningful regression gate. |
| P0.3.6 Published baseline/fairness report | **Not started** | No report establishes where competitors are strong, sets measured TGF targets, or documents fairness across presentation mode, DPI, visuals and release configuration. |

The source comment in `samples/showcase/bench_core.cpp` itself calls its eight benchmarks
smoke-level and says the statistically gated P0.3 suite will replace them. They measure core
operations such as arena allocation, pool create/destroy, SlotMap, SPSC, hashing and profiler
zones. They do not implement the GUI scenarios or provide a cross-framework comparison.
`benchmarks/README.md` explicitly says the P0.3 harness is not started.

The build-time workflow in P0.1.9 measures compiler/build and public-header cost. It is a
separate engineering metric and must not be counted as the runtime competitor benchmark suite.

### P0.4 — Research spikes

| Task | Reassessed status | Findings |
|---|---|---|
| P0.4.1–P0.4.10 | **Not started** | No completed, measured spike reports were found for tree storage, layout, vector rendering, text, present latency, damage presentation, threading, embedded viewport, RHI build-vs-adopt, or host integration. |
| P0.4.11 Numeric-domain spike | **Partial** | Existing core checks cover adjacent-sample integer precision and camera-relative conversion at 100 hours / 192 kHz. They do not demonstrate float-GPU rendering, node-canvas zoom of 10^6, or gigapixel canvas tile/seam correctness. |
| P0.4.12 Accessibility data-model spike | **Not started** | No retained-tree UI Automation / NSAccessibility / AT-SPI dirty-update spike, including virtualized list validation, was found. |
| P0.4.13 Real-time safety spike | **Not started** | No real audio callback integration with blocking, priority inversion and page-fault measurements was found. |

In particular, the numeric-core check is useful and should remain, but a single CPU-side math
test must not be promoted to the full multi-domain/GPU acceptance requirement.

### P0.5 — ADRs, estimates and first reference application

**Partial.** There are five standalone ADR files in the current tree:
ADR-0012, ADR-0016 and ADR-0028–0030. ADR-0012 and ADR-0016 cover two records in the
0001–0027 range; most of the planned ADRs are not individual decision records. The phase
estimates and first reference-application decision also remain unfinished. An ADR template and
index are useful governance foundations, not completed decisions.

## 5. Phase 0 disposition

The only fully delivered P0.1 tasks at this audit are P0.1.1, P0.1.2, P0.1.5, P0.1.6,
P0.1.7, P0.1.8 and P0.1.9. P0.1.3 and P0.1.4 are partial because the current latest-two
MSVC pair has changed; the physical benchmark-host sub-items remain owner-waived as noted.

The root `TODO.md` has been updated to reflect these findings, including the reopened MSVC
subtasks and the P0.1.8 completion. The historical task-count table in `docs/STATUS.md`
continues to describe the original 14 October task snapshot and is not a current completion
count.

**Phase 0 exit criteria remain unmet:** the competitor benchmark harness/baselines are absent,
the majority of ADRs and the asset-audit decisions are absent, and the required research spikes
are undocumented. **Do not start Phase 1.**

## 6. Documentation consistency updates

The following Markdown files were reconciled with the re-audit:

- Root `TODO.md`: task status corrections, evidence notes, limitations and Revision 30.
- `README.md`: current Phase 0 summary and audit link.
- `docs/STATUS.md`: date/revision, current evidence and current-vs-historical task state.
- `docs/COMPILER_SUPPORT.md`: latest-two MSVC policy gap and current configured matrix.
- `docs/CI.md`: current hosted runs, build-performance/SBOM workflows, benchmark-host boundary.
- `docs/DESIGN.md`: current cross-platform verification and actual P0 next sequence.
- `docs/GITHUB_REPOSITORY_SETUP.md`: current hosted evidence; initial publication details retained as history.
- `docs/THIRD_PARTY.md` and ADR-0016: completed direct-dependency SBOM scope and evidence.
- ADR-0012: current native platform build/test evidence and remaining plugin/ABI limitations.
- `docs/BENCHMARK_RUNNER_SETUP.md`: explicit difference between the owner waiver and physical acceptance.
- `benchmarks/README.md`: explicit P0.3 not-started status and separation from core smoke benchmarks.
- `docs/audit/README.md`: links to this report and marks the original dependency note as historical.

No production C++ implementation or workflow matrix was changed as part of this status audit.
The MSVC 14.52 upgrade is deliberately left as an open task rather than being silently
implemented without a dedicated task/review.


## Erratum — 23 November 2026: MSVC 14.52 is Preview

The original report's statement that MSVC 14.52 became generally available on 16 November was incorrect. Microsoft's official compiler-version table (last updated 28 May 2026 and rechecked on 23 November) explicitly labels 14.52 as Preview and has no GA/EOL date for it. Microsoft lists 14.51 as Standard support (February 2027 EOL) and 14.50 as Long-Term support (November 2028 EOL). TGF's latest two stable/in-support MSVC generations are 14.51 and 14.50. All references in the main task ledger and active policy documentation have been corrected accordingly. The failed exploratory 14.52 installation attempts are not relevant to P0.1.3 acceptance and are not counted as failures of the stable MSVC matrix.
