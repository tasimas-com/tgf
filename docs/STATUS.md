# TGF implementation status

**Status date:** 18 November 2026 — Revision 27  
**Audited input:** `tasimas-com/tgf` on GitHub; task completion and current CI evidence are maintained in the root `TODO.md`  
**Canonical task checklist:** [`../TODO.md`](../TODO.md)  
**Latest Phase 0 reassessment:** [`audit/2026-11-18/PHASE_0_REASSESSMENT.md`](audit/2026-11-18/PHASE_0_REASSESSMENT.md)  
**Original source-audit evidence:** [`audit/2026-10-14/`](audit/2026-10-14/)

## Executive status

TGF is an early engineering baseline, not yet a usable GUI framework and not ready for a
1.0.0 release. The current working implementation is concentrated in `tgf::core`, its
console showcase, CMake packaging for `TGF::Core`, and the repository's build, dependency,
compiler, licensing/SBOM, source-quality, and measurement policy tooling. Phase 0 is not
complete: the asset audit and competitor benchmark suite are not delivered, and most research
spikes and ADRs remain open. The MSVC stable Tier-1 pair is 14.52/14.51; Microsoft announced 14.52 GA/LTS on 16 November 2026.

The current repository does **not** yet contain implementations of the native platform layer, RHI,
renderer, text system, retained UI, standard widgets, professional-app components, host/plugin
adapters, stable C ABI, language bindings, or release engineering. Those directories are
architecture placeholders with README files, not functioning modules.

## Task assessment of the supplied snapshot

The 272 original task entries comprise the checkbox tasks plus 13 task groups that were
previously written as bold prose. Those task groups are now represented in `TODO.md` with
explicit status markers. Final artifact entries are included in the counts below.

| Area | Done | Partial | Not started | Not delivered | Total |
|---|---:|---:|---:|---:|---:|
| P0 — foundations | 8 | 6 | 18 | 0 | 32 |
| P1 — core | 1 | 18 | 11 | 0 | 30 |
| P2 — platform | 0 | 0 | 21 | 0 | 21 |
| P3 — RHI and renderer | 0 | 0 | 24 | 0 | 24 |
| P4 — text | 0 | 0 | 12 | 0 | 12 |
| P5 — retained UI | 0 | 0 | 40 | 0 | 40 |
| P6 — widgets | 0 | 0 | 9 | 0 | 9 |
| P7 — professional components | 0 | 0 | 45 | 0 | 45 |
| P8 — app/host integration | 0 | 0 | 7 | 0 | 7 |
| P9 — accessibility/i18n/resilience | 0 | 0 | 7 | 0 | 7 |
| P10 — developer tools | 0 | 0 | 8 | 0 | 8 |
| P11 — documentation/ecosystem | 0 | 0 | 6 | 0 | 6 |
| P12 — security/reliability | 0 | 0 | 10 | 0 | 10 |
| P13 — governance/release | 0 | 0 | 9 | 0 | 9 |
| Final artifacts | 0 | 6 | 0 | 6 | 12 |
| **Original task baseline** | **3** | **34** | **229** | **6** | **272** |

“Partial” means there is some implementation or deliverable, but the task is not complete.
“Not delivered” is used for final release artifacts that are absent from the supplied archive.
The checklist uses `[p]` for partial, `[x]` for done, and `[ ]` for not started/not delivered.
A `[x]` is not awarded merely because a local build passes. P0.1.2 is now complete with documented presets and an automated preset-graph test.

The original 14 October audit added fifteen remediation entries beyond its 272-task baseline.
Thirteen were closed with regression evidence and two remained partial at that historical review.
The current follow-up still keeps formal real-time guarantees and dynamically loaded plugin/
foreign-compiler ABI validation partial; native Windows/macOS mapped-file build/test coverage
has since been exercised in the hosted matrix.


## Phase 0 progress — P0.1.2 CMake preset matrix (Revision 10)

P0.1.2 is complete. The repository provides configure/build/test presets for Debug, Release,
RelWithDebInfo, profiling, AddressSanitizer, UndefinedBehaviorSanitizer, ThreadSanitizer, and
MemorySanitizer. It also retains shared Release, a combined ASan+UBSan compatibility preset,
and Visual Studio 2022 Release/Debug/ASan presets. `TGF_SANITIZER` centralizes compiler-aware
flags and rejects unsupported compiler/sanitizer combinations. `docs/BUILDING.md` explains
how to invoke each configuration. `tools/check_presets.py` validates required names, settings,
and preset references; CTest runs it as `cmake_preset_matrix`.

Fresh Linux verification (GCC 14.2 unless noted): Debug, Release, shared Release, RelWithDebInfo,
profiling, ASan, UBSan, TSan, and combined ASan+UBSan each built and passed all **4/4** CTest tests.
Clang 17 MSan built and passed **4/4** CTest tests; its showcase does not replace global
`new`/`delete` because MSan supplies those interceptors, so the global-new accounting assertion
and separate warm-up test that depends on the process-wide hook are excluded. Direct TGF
allocator, mapping, container and concurrency checks remain active. Preset graph validation
passed. Visual Studio presets are defined but were not
executed because this verification host is Linux; native MSVC validation belongs to the compiler
and CI matrix tasks P0.1.3/P0.1.4.

## Historical Phase 0 evidence — P0.1.3 compiler policy baseline (17 October 2026; MSVC pair reopened 18 November)

The 17 October implementation and verification completed the compiler-policy and source-quality
work against the then-current matrix. It targeted MSVC 14.51/14.50, Clang 23/22, and GCC 16/15.
This is a historical completion record. A later compiler-version reassessment on 23 November
the 23 November correction was based on a stale Microsoft Learn table. Microsoft's 16 November
2026 C++ Team Blog announcement confirms MSVC 14.52 is GA/LTS. The stable/in-support Tier-1
pair is 14.52/14.51, and the current policy, manifest and CI matrix have been restored to it.
`TGF_WARNINGS_AS_ERRORS` is ON by default; MSVC uses `/W4` + `/WX`, while GCC/Clang use
the documented warning set + `-Werror`. Ninja presets export `compile_commands.json`, and
the compiler-policy regression check is registered in CTest.

The required source-quality workflow [run #119](https://github.com/tasimas-com/tgf/actions/runs/39056856378)
passed both LLVM jobs: clang-format checked all 29 repository-owned C/C++ files; complete TGF
Debug builds passed clang-tidy with warnings-as-errors; strict IWYU passed using the matched
pairs LLVM 22.1.8/IWYU 0.26 and LLVM 23.1.4/IWYU 0.27. The generated duplicate-include
self-containment harness is narrowly excluded from IWYU because its deliberately unused includes
are the test itself; all implementation and showcase translation units remain checked.

The full Tier-1 hosted matrix [run #193](https://github.com/tasimas-com/tgf/actions/runs/39056856383)
passed 14/14 jobs across MSVC 14.50/14.51, Clang 22/23, GCC 15/16, and AppleClang 17 in Debug
and Release, with warnings-as-errors enabled. All 14 CTest artifacts were downloaded, ZIP
integrity checked, and inspected; each contained 11/11 passing CTest cases and the showcase
reported 26 checks with zero failures (154/154 CTest executions).

PR [#4](https://github.com/tasimas-com/tgf/pull/4) merged the original enforcement implementation into
`main`. The source-quality tooling and GCC/Clang lanes remain verified; P0.1.3.a and P0.1.3.g
are now being revalidated against the corrected 14.52/14.51 GA/LTS policy.
This does **not** satisfy the overall Phase 0 exit criteria: the separate benchmark/Tier-A,
research-spike, and ADR work remains. Phase 1 remains gated.

## What is implemented

- C++20 `tgf::core` static/shared library with foundational types/handles, `Result<T>`/`Status`,
  assertions, counted raw allocation, `LinearArena`, `Pool<T>`, `SlotMap<T>`, `SpscQueue`,
  `TripleBuffer`, basic 2D vectors/rectangles/colors, camera-relative double-to-float conversion,
  checked `SampleTime` arithmetic, FNV-1a hashing, logging, CPU scoped profiling, and build info.
- `tgf_showcase` console executable with 26 core checks, eight smoke benchmarks, and JSON output.
- Versioned cross-module allocator registry (`ModuleAllocatorDesc`, generation handles, and an
  outstanding-allocation unload guard) plus move-only `MappedFile` read-only/read-write APIs.
  POSIX and Windows mapping implementations are exercised by the hosted native Linux/Windows/macOS
build-and-test matrix; actual dynamic-plugin load/unload and foreign-toolchain stable C ABI
validation remain outstanding.
- CMake install/export package for the `TGF::Core` target, verified with a separate consumer.
- Repository layout and dependency checker. The bindings dependency rule identified in the audit
  has been corrected to permit only `tgf/c/...` dependencies and now has a positive/negative
  regression test.

## Verification evidence

The source audit was performed on Linux x86-64. Revision 10 verification was rerun after the final public descriptor-header change; Revision 11 additionally validates the compiler-policy wiring with GCC 14.2 Release and Clang 17 Release; all listed build configurations passed their registered tests. The following were verified against the input
snapshot:

- GCC 14.2: Debug, Release/static, Release/shared builds; CTest passed.
- GCC 14.2: combined AddressSanitizer + UndefinedBehaviorSanitizer build and tests passed.
- GCC 14.2: ThreadSanitizer build and tests passed, including the recorded SPSC and triple-buffer
  stress checks.
- Clang 17: Release/static build with warnings-as-errors and tests passed.
- Manual standalone public-header syntax checks passed under GCC C++20 and C++23, with exceptions
  and RTTI both enabled and disabled. These are audit-time manual checks, not yet a committed full
  compiler/standard matrix.
- Static install and a separate downstream CMake `find_package(TGF REQUIRED)` consumer passed.

Historical Revision 9 core verification (before the Revision 10 Phase 0 tooling work):

- GCC 14.2 Release/static: build passed; CTest **3/3** passed; showcase **26/26** checks passed.
- GCC 14.2 Debug/static: build passed; CTest **3/3** passed.
- GCC 14.2 ASan+UBSan: build passed; CTest **3/3** passed.
- GCC 14.2 TSan: build passed; CTest **3/3** passed.
- GCC 14.2 Release/shared: build passed with LTO disabled for this validation run; CTest **3/3** passed.
- Clang 17 Release/static: build passed with LTO disabled because this environment lacks LLVMgold; CTest **3/3** passed.
- New module allocator tests verify generation invalidation, rejection of premature unregister (`Error::Busy`), allocator callback pairing, and clearing the outstanding-allocation pin after free. A four-thread stress test completed 1,024 allocations/frees with exact callback pairing under ThreadSanitizer; all 64 registry slots are accepted and the 65th is rejected.
- New descriptor publication/lifetime tests validate concurrent register/use/unregister ordering. The test suite also checks mapped-file move assignment in addition to move construction.
- New mapped-file tests verify UTF-8 paths, read-only/read-write views, flush persistence, move ownership, and zero-length files on Linux/POSIX.
- Revision 7 tests continue to verify external allocator tracking, scoped shutdown reports, and 1,000 warmed steady-state iterations with zero allocations.


**Not verified in the current project state:** successful full hosted execution of the current MSVC 14.52/14.51 matrix, ARM,
native Wayland/X11 windows, real GPU APIs/drivers, and a dedicated physical pinned-frequency
benchmark host. Native Windows and macOS compiler/build/test lanes are verified for the currently
configured MSVC 14.50/14.51 and AppleClang 17 matrix; see the dated current evidence below. GitHub Actions workflows were introduced in Revision 12 and hardened in Revision 13; the current remote matrix and related policy workflows have since executed successfully (CI run #412, Source Quality run #338, Build Performance run #18, and SBOM run #13).

## Original core audit findings and current resolution

The initial source audit identified seven core risks. Allocation, arena, pool, exception-contract,
and zero-rate time issues are closed with regression tests. Realtime atomic guarantees remain
partial; allocation diagnostics now cover TGF-routed and explicitly adapted host allocations:

1. **Allocation validation — addressed:** invalid alignments and rounding overflow are rejected.
2. **LinearArena Release safety — addressed:** invalid requests fail deterministically in all builds.
3. **Pool lifetime — addressed with a raw-pointer caveat:** ownership and immediate double destroy
   are checked, and release destroys live objects. A raw pointer must be discarded after destroy;
   only a generational handle can distinguish a stale identity after storage reuse.
4. **Exception contracts — addressed:** Pool construction is exception-safe and SlotMap type
   requirements match its `noexcept` relocation/erase implementation.
5. **SampleTime zero rate — addressed:** `to_seconds()` returns `InvalidArgument` for rate zero.
6. **Realtime channels — partially addressed:** always-lock-free atomics are enforced and basic
   data-path checks exist. Callback integration, supported-target matrix, and formal wait-free/
   hard-realtime evidence still need per-target verification.
7. **Allocation diagnostics — implemented for instrumented allocations:** `MemoryTag` and
   `ScopedMemoryTag` classify TGF-routed allocations; `tracked_external_alloc_bytes()` adapts
   paired host allocator callbacks; `MemoryStats` exposes live/cumulative/peak counts and budgets;
   `MemorySnapshot`/`memory_leaks_since()` expose outstanding deltas; `ScopedMemoryLeakReport`
   reports per-tag deltas at controlled shutdown; and `ScopedAllocationCheck` verifies warmed
   steady-state operations. Allocations not routed through TGF or its adapter remain invisible.
8. **Cross-module memory ownership — partially implemented:** the module allocator registry blocks
   orderly unregister while blocks are still live and pairs frees with the registering callbacks.
   Native plugin load/unload and foreign-compiler C ABI validation remain open.
9. **Memory-mapped files — partially implemented:** Linux/POSIX and Windows/macOS native build/test
   paths for whole-file read/write mappings, flush, move ownership, and empty files are exercised
   by the hosted matrix. File mutation coordination, explicit large-file edge coverage, and
   dynamic plugin lifecycle validation remain open.

Details and exact verification are in `docs/audit/2026-10-14/TGF_CORE_REMEDIATION.md`.

## Recommended next sequence

1. Re-run the stable compiler matrix and policy regressions for P0.1.3/P0.1.4.g (MSVC 14.52/14.51, GCC 16/15, Clang 23/22, AppleClang); GCC/Clang and LLVM quality lanes have already passed on the preceding revision.
2. P0.1.8 is now complete: Apache-2.0 LICENSE/NOTICE, ADR-0016, direct dependency registry, policy checker, SPDX 2.3 generator, CTest gates, and SBOM artifact workflow are delivered.
3. Complete P0.2: inventory existing assets, decide keep/rewrite/delete, and record the result in ADR-0018; preserve lessons in docs/lessons.md.
4. Complete P0.3: implement the real cross-framework benchmark harness, statistical methodology, stored results, and fair Tier-A baselines.
5. Complete P0.4 and P0.5: document research spikes, deliver ADR-0001–0027 as decision records, and finalize estimates/reference application.
6. Keep Phase 1 blocked until the complete Phase 0 exit criteria are met.

## Revision 12 — CI workflow foundation

Implementation record: [`audit/2026-10-15/TGF_CI_PROGRESS.md`](audit/2026-10-15/TGF_CI_PROGRESS.md).

P0.1.4 is partially implemented. `.github/workflows/ci.yml` defines Debug and Release build/CTest
jobs for Ubuntu 26.04 with GCC 15 and Clang 22, Windows Server 2025 with Visual Studio 2022/MSVC,
and macOS 15 with AppleClang. It enables sccache-backed compiler caching and uploads CTest logs.
Optional LTO is disabled in the common CI baseline to avoid toolchain-specific linker-plugin
requirements; warnings-as-errors stays explicitly enabled. `.github/workflows/nightly-benchmarks.yml`
contains a scheduled/manual benchmark job that only runs on a self-hosted Linux x64 runner labelled
`tgf-benchmark-pinned` after repository variable `TGF_BENCHMARK_RUNNER_READY=true`.

The `tools/check_benchmark_host.py` preflight requires all exposed CPU frequency policies to use
the `performance` governor with equal minimum and maximum frequencies. Five unit tests exercise
valid and invalid host configurations. `tools/check_ci_workflows.py` verifies the workflow contract
and parses YAML when PyYAML is available; both checks are registered in CTest. GCC 14.2 Release
and Debug each pass 7/7 CTest tests locally. Clang 17 Release is verified with LTO disabled.
Remote workflow execution, full Tier-1 compiler-version coverage, and pinned benchmark-host
provisioning remain pending; none is claimed complete.


## Revision 13 — hosted CI execution preparation

Implementation record: [`audit/2026-10-15/TGF_CI_REMOTE_EXECUTION_PREP.md`](audit/2026-10-15/TGF_CI_REMOTE_EXECUTION_PREP.md).

The Windows CI leg now activates the Visual Studio 2022 developer environment and uses Ninja
with `cl.exe`, rather than the Visual Studio project generator. This matters because CMake's
compiler-launcher target property is implemented for Makefile and Ninja generators; this makes
`sccache` effective on the MSVC path. Added Windows-only `msvc-ninja-debug` and
`msvc-ninja-release` configure/build/test presets while retaining the Visual Studio IDE presets.
The workflow uses `actions/checkout@v7`, `actions/upload-artifact@v7`, and
`ilammy/msvc-dev-cmd@v1.13.0`. The nightly self-hosted runner documentation now requires a
Node.js 24-compatible Actions runner.

Local verification: GCC 14.2 Release, GCC 14.2 Debug, and Clang 17 Release each passed all 7/7
CTest tests. Workflow YAML parses, the CI contract checker passes, and the expanded CMake preset
graph checker passes. No Git remote, `.git` directory, GitHub CLI, or connected repository was
available in the extracted project environment. Therefore no hosted Actions run or Windows/macOS
result is claimed; P0.1.4.e remains partial pending connection to the actual GitHub repository.


## Revision 14 — GitHub repository discovery

The GitHub integration is connected to account `tasimas-com`. The account's owned repositories
are `tasimas-com/tasimas-com`, `tasimas-com/tbhs`, and `tasimas-com/tjsonp`; a direct lookup of
`tasimas-com/TGF` returned 404. The website/profile repository describes TGF as “Coming soon”
and is not the framework source repository. No remote files were changed. The local workflow is
ready for a dedicated TGF repository, but hosted CI cannot be run until that repository exists
or the correct repository name is supplied. See
[`audit/2026-10-15/TGF_GITHUB_REPOSITORY_DISCOVERY.md`](audit/2026-10-15/TGF_GITHUB_REPOSITORY_DISCOVERY.md).


## Revision 15 — dedicated GitHub repository setup

The dedicated destination is `tasimas-com/tgf`. GitHub identity and repository ownership were
verified, but no create-repository operation is exposed by the connected GitHub toolset, so no new
repository was created and no existing repository was modified. The creation and first-push
runbook is [`GITHUB_REPOSITORY_SETUP.md`](GITHUB_REPOSITORY_SETUP.md). The canonical master
checklist remains the root [`TODO.md`](../TODO.md), included in the project ZIP. Hosted CI remains
unverified until the repository exists and all eight Actions jobs have run.


## Revision 16 — dedicated GitHub repository created

The user created `tasimas-com/tgf` and connected the account. GitHub confirms repository ID
`1420440551`, default branch `main`, public visibility, and administrator/push access for
`tasimas-com`; the repository was empty before the first project publication. The initial source
snapshot is being published with `TODO.md` at the repository root. P0.1.4.e.6 is complete;
P0.1.4.e.7 remains open until the first commit is verified, all eight hosted jobs complete, and
the compiler versions and CTest artifacts are inspected. The nightly benchmark runner remains
separate and unconfigured. See [`GITHUB_REPOSITORY_SETUP.md`](GITHUB_REPOSITORY_SETUP.md).


## Revision 17 — hosted cross-platform CI baseline

The dedicated public repository is `tasimas-com/tgf`, default branch `main`. GitHub Actions
run [#13](https://github.com/tasimas-com/tgf/actions/runs/38730051352) passed 8/8 jobs on
2026-10-15. Each job ran seven CTest tests and uploaded a log artifact; all eight ZIP artifacts
were downloaded and inspected. Exact compiler versions and artifact IDs are recorded in
[`audit/2026-10-15/TGF_HOSTED_CI_RESULTS.md`](audit/2026-10-15/TGF_HOSTED_CI_RESULTS.md).

The Windows job is identified by its actual MSVC 14.51 toolset and compiler version, not by the
earlier inaccurate Visual Studio 2022 job label. The CI cache is GitHub Actions build-directory
caching (`actions/cache@v4`), not sccache.

P0.1.4.e (hosted matrix publication and review) is complete. P0.1.4.f (dedicated pinned-frequency
benchmark runner) and P0.1.4.g (full two-generation compiler matrix) remain partial. Phase 0 is
not complete.


## Revision 18 — hosted CI matrix verified twice

GitHub Actions runs [#13](https://github.com/tasimas-com/tgf/actions/runs/38730051352) and
[#14](https://github.com/tasimas-com/tgf/actions/runs/38738723466) each passed all eight
Windows/Linux/macOS × compiler × Debug/Release jobs. Exact compiler versions: GCC 15.2.0,
LLVM Clang 22.1.2, MSVC 19.51.36260.0/toolset 14.51.36231, and AppleClang 17.0.0.
All sixteen CTest artifacts across both runs were downloaded and inspected; every job passed
7/7 CTest tests. See `audit/2026-10-15/TGF_HOSTED_CI_RESULTS.md`.

The verified matrix is a first baseline. GCC 16, Clang 23, and MSVC 14.50 remain unverified,
and the dedicated pinned-frequency benchmark runner remains unprovisioned. P0.1.4.e is complete;
P0.1.4.f, P0.1.4.g, and P0.1.3.g remain partial. Phase 0 is not complete.


## Revision 19 — dedicated nightly benchmark runner preparation

Added `docs/BENCHMARK_RUNNER_SETUP.md` with hardware, CPU-frequency, runner registration,
security, Actions-variable, and artifact-review instructions. The five preflight unit tests pass.
The real-host preflight was executed in this environment and failed closed because no CPU
frequency policy is exposed; this is not a qualifying benchmark runner. No self-hosted runner or
`TGF_BENCHMARK_RUNNER_READY` variable is claimed as configured. P0.1.4.f remains partial until
the dedicated machine is physically provisioned, registered, and produces an inspected benchmark
artifact.


## Revision 20 — P0.1.3 compiler and source-quality gates completed (2026-10-17)

The former Revision 11 assessment above has been superseded by the completed evidence recorded
in this section and in the root `TODO.md`. P0.1.3 is no longer partial: PR #4 is merged,
the two-version source-quality workflow passed, and the full 14-job Tier-1 compiler matrix and
all 154 CTest executions passed. P0.1.3 closure does not change the separate benchmark-host
waiver or satisfy the overall Phase 0 exit criteria.


## Revision 21 — P0.1.4 hosted CI closure for the approved scope (2026-11-13)

P0.1.4 is closed for the current owner-approved project scope. The current hosted CI run [#378](https://github.com/tasimas-com/tgf/actions/runs/43399403368) completed 14/14 jobs across GCC 15/16, Clang 22/23, MSVC 14.50/14.51, and AppleClang 17, each in Debug and Release. All 14 CTest artifacts were downloaded and inspected: each ZIP passed integrity validation and each `LastTest.log` contained 11/11 passing tests (154/154 successful CTest executions). The paired source-quality run [#304](https://github.com/tasimas-com/tgf/actions/runs/43399402789) passed both LLVM jobs.

The dedicated nightly benchmark workflow, fail-closed preflight, inventory collector, acceptance tests, artifact capture, and operator runbook are delivered. **The 2026-10-17 project-owner waiver for physical benchmark-host provisioning and self-hosted runner registration/first-run acceptance remains active.** No physical pinned-frequency host, thermal validation, registered runner, first benchmark artifact, or dedicated-host performance result is claimed. Scheduled nightly run [#28](https://github.com/tasimas-com/tgf/actions/runs/43211725951) was skipped by the readiness gate; keep `TGF_BENCHMARK_RUNNER_READY` unset.

Exact compiler/job evidence and all 14 artifact IDs are recorded in [`audit/2026-11-13/P0_1_4_CI_EVIDENCE.md`](audit/2026-11-13/P0_1_4_CI_EVIDENCE.md). This closes P0.1.4 only within the approved scope and does not change the overall Phase 0 gate. Phase 1 remains blocked.


## Revision 22 — P0.1.4 re-verification after container-detection hardening (2026-11-13)

Follow-up commit `f49fd53a673be7c4589e24b7adfb9a01f327da06` corrected the benchmark-host preflight and inventory collector to use the default `systemd-detect-virt` mode, ensuring container virtualization (Docker/Podman/LXC/systemd-nspawn) is rejected as well as VM virtualization. Added explicit Docker-negative tests; the preflight suite now has 11 cases and inventory suite has 6.

The final code revision passed [TGF CI run #383](https://github.com/tasimas-com/tgf/actions/runs/43413133994) with 14/14 successful jobs. All 14 ZIP artifacts were inspected and passed integrity; each contains 11/11 passing CTest tests (154/154 executions) and the 11-/6-case Python suites. [Source Quality run #309](https://github.com/tasimas-com/tgf/actions/runs/43413133983) passed 2/2 jobs. The detailed per-artifact IDs and toolchain results are in `docs/audit/2026-11-13/P0_1_4_CI_EVIDENCE.md`.

The existing owner-approved physical benchmark-host waiver is unchanged: no dedicated physical host or registered runner is claimed, and `TGF_BENCHMARK_RUNNER_READY` remains unset. P0.1.4 is closed for that approved scope only. Phase 0 remains open overall and Phase 1 remains blocked.


## Revision 23 — P0.1.6 dependency-DAG enforcement completed (2026-11-13)

P0.1.6 is now complete. The dependency checker is kept in lockstep with the normative §4
module-dependency table and its mandatory CTest coverage includes all 38 permitted and 94
forbidden directed module edges, positive/negative include-path cases, ordinary
string/character-literal lookalikes, and symlink-boundary fixtures. Safe source-file links
within one module/consumer are accepted; source-file links crossing the repository or owning
module/consumer boundary are rejected; directory symlinks and symlinked top-level scan roots
are rejected. Unresolvable source links fail closed.

The verified code commit is `597887791105638b7b7202ace314bf1af0141596`.
[TGF CI run #388](https://github.com/tasimas-com/tgf/actions/runs/43416718257) passed 14/14
jobs across GCC 15/16, Clang 22/23, MSVC 14.50/14.51, and AppleClang in Debug and Release.
All 14 CTest artifacts were integrity-checked and inspected: 11/11 tests passed in each,
for 154/154 successful executions. [Source Quality run #314](https://github.com/tasimas-com/tgf/actions/runs/43416718274) passed 2/2 jobs. Detailed artifact IDs and the fixture-by-fixture evidence are recorded in
[`audit/2026-11-13/P0_1_6_DEPENDENCY_DAG_EVIDENCE.md`](audit/2026-11-13/P0_1_6_DEPENDENCY_DAG_EVIDENCE.md).

This task closure does not close the remaining Phase 0 research, ADR, benchmark, or release
criteria. Phase 0 remains open and Phase 1 remains blocked.


## Revision 24 — P0.1.7 contributor and governance workflow completed (2026-11-13)

P0.1.7 is complete. The repository now has a contributor guide, Code of Conduct, bug and
feature issue forms, PR template, ADR template and updated ADR index, README policy links,
and a mandatory `community_governance_policy` CTest guard. The guard checks required
policy sections and project-specific contracts, including honest license status, report
routes, issue-form types/IDs, PR review evidence, and ADR lifecycle/allocation. Issue-form
YAML was independently parsed with PyYAML 6.0.3.

On implementation commit `852d724fae3e74f33b78e05ab20cc72de19e0f53`, [TGF CI run #392]
(https://github.com/tasimas-com/tgf/actions/runs/43429879957) passed 14/14 matrix jobs.
All 14 CTest artifacts were integrity-checked and inspected: each had 12/12 passing tests,
including `community_governance_policy`, for 168/168 successful executions. [Source Quality
run #318](https://github.com/tasimas-com/tgf/actions/runs/43429879999) passed 2/2 LLVM jobs.
See [the P0.1.7 evidence report](audit/2026-11-13/P0_1_7_COMMUNITY_GOVERNANCE_EVIDENCE.md)
for artifact IDs and the verification register.

P0.1.7 closure does not complete the license/SBOM work in P0.1.8 or the remaining Phase 0
research, ADR, benchmark, and release criteria. Phase 0 remains open; Phase 1 remains blocked.


## Historical Revision 25 — Phase 0 next-task sequence (2026-11-13; superseded by Revision 27)

Updated the recommended sequence to reflect the verified closures of P0.1.6 and P0.1.7.
The next foundation task is P0.1.8 (license/SBOM/third-party policy), followed by P0.1.9
(build-time and header-hygiene budgets). This is a documentation correction only; it does
not change task status or authorize Phase 1.


## Historical Revision 26 — P0.1.9 build-time and header-cost tracking completed (2026-11-13; P0.1.8 status superseded by Revision 27)

P0.1.9 is complete. A standardised no-cache Clang 23.1.6 / Ninja / Release workflow now measures
clean and one-source incremental builds against checked-in hard ceilings (180 s and 45 s) and
publishes JSON/Markdown timing plus per-public-header cost reports. The final hosted run measured
3.441 s clean and 1.194 s incremental, and reported all 15 public headers. The isolated
translation-unit metric includes fixed compiler/front-end overhead and transitive includes;
it is a comparison proxy, not pure header-only CPU time.

[TGF CI run #398](https://github.com/tasimas-com/tgf/actions/runs/43458777497) passed 14/14
compiler/platform/configuration jobs. All 14 CTest artifacts were ZIP-integrity checked and
inspected; each contained 15/15 passing tests, including the three new build-measurement,
header-reporting, and performance-policy checks (210/210 executions). [Source Quality run
#324](https://github.com/tasimas-com/tgf/actions/runs/43458777647) passed 2/2 jobs.
[Build Performance run #4](https://github.com/tasimas-com/tgf/actions/runs/43458777543) passed;
its report artifact is [available here](https://github.com/tasimas-com/tgf/actions/runs/43458777543/artifacts/14055341519).
Per-artifact CTest IDs and the full evidence register are in
[audit/2026-11-13/P0_1_9_BUILD_PERFORMANCE_EVIDENCE.md](audit/2026-11-13/P0_1_9_BUILD_PERFORMANCE_EVIDENCE.md).

P0.1.8 (license/SBOM/third-party policy) remains the next unclosed foundation task. P0.1.9
closure does not authorize Phase 1; Phase 0 remains open and Phase 1 remains blocked.

## Revision 27 — independent Phase 0 reassessment (2026-11-18)

The current repository tree, C++ implementation, CMake configuration, test harnesses, policy/checker scripts, workflows, ADRs, and Markdown status pages were re-read against the Phase 0 acceptance criteria. Existing checkbox states were not treated as evidence. The current main code baseline at audit start was `7e9dad1581be59e1df6adf9caa7572a1129d518e`; documentation updates are recorded in the commits following this baseline. The task-by-task findings and exact scope limits are in [the 18 November reassessment](audit/2026-11-18/PHASE_0_REASSESSMENT.md).

**Current hosted evidence (17 November):** [TGF CI run #412](https://github.com/tasimas-com/tgf/actions/runs/44089512975) passed 14/14 configured jobs; [Source Quality run #338](https://github.com/tasimas-com/tgf/actions/runs/44089512797) passed 2/2 jobs; [Build Performance run #18](https://github.com/tasimas-com/tgf/actions/runs/44089512759) passed; and [SBOM run #13](https://github.com/tasimas-com/tgf/actions/runs/44089512739) passed and uploaded its SPDX 2.3 artifact. The passing compiler matrix includes GCC 15/16, Clang 22/23, MSVC 14.50/14.51, and AppleClang 17 in Debug/Release.

**Verified complete for the currently delivered scope:** P0.1.1, P0.1.2, P0.1.5, P0.1.6, P0.1.7, P0.1.8, and P0.1.9. The dependency policy has positive/negative edge and symlink tests; community governance and coding-standard policies are CTest gates; and P0.1.8 now has an accepted ADR, LICENSE/NOTICE, immutable dependency registry, fail-closed policy, SPDX 2.3 generator, tests, and uploaded artifact.

**MSVC policy correction (24 November 2026):** the 23 November conclusion relied on a stale Microsoft Learn table. Microsoft's 16 November announcement confirms MSVC 14.52 is generally available and an LTS release in Visual Studio 2026 18.12 Stable and 18.11 LTSC. The latest stable/in-support MSVC pair is 14.52/14.51. The manifest, checker, CI matrix and documents now use that pair. P0.1.3.a is complete; P0.1.3.g and P0.1.4.g remain open until the current 14-job hosted matrix and policy regressions pass. P0.1.4's physical pinned-frequency host and self-hosted runner provisioning remain explicitly owner-waived; no physical-host result is claimed.

**Remaining partial/not complete:** P0.2.1–P0.2.3 have no current asset keep/rewrite/delete inventory, ADR-0018, or docs/lessons.md. P0.3 has only reference/scenario/tier planning and the console's eight smoke benchmarks: no executable competitor comparison, measured Tier-A baseline, full metric/noise-floor specification, persistent comparative result store, dashboard, regression gate, or fair baseline report. P0.4.11 has a useful 100-hour/192-kHz integer/camera-relative precision check but not GPU, 10^6-zoom node-canvas, or gigapixel-canvas validation. P0.5 still lacks the majority of ADR-0001–0027 as standalone records, and the phase estimates/first reference app are not finalized.

**Not started:** P0.4.1–P0.4.10 and P0.4.12–P0.4.13 research spikes. A scenario name, architecture sketch, or existing core unit test is not a completed research spike.

The Phase 0 exit criteria are not met: the benchmark harness is not green with Tier-A competitors, the ADR set is not accepted, and the research spikes are not documented. Phase 1 remains blocked.



## Revision 28 — superseded MSVC policy note (2026-11-23)

This revision incorrectly classified MSVC Build Tools 14.52 as Preview by relying on a Microsoft Learn version table that had not been refreshed after the 16 November 2026 GA announcement. It is superseded by Revision 29 below; the required pair is 14.52/14.51.


## Revision 29 — MSVC 14.52 GA/LTS and CI policy restoration (2026-11-24)

Microsoft's [16 November 2026 announcement](https://devblogs.microsoft.com/cppblog/msvc-build-tools-version-14-52-now-generally-available/) confirms MSVC 14.52 is generally available as an LTS release in Visual Studio 2026 18.12 Stable and 18.11 LTSC. The stable/in-support Tier-1 pair is 14.52/14.51. The repository manifest, CI workflow, policy checker, shared channel-aware installer, regression tests and current documentation have been restored to this pair. P0.1.3.g/P0.1.4.g remain open until the refreshed full 14-job matrix passes; P0.1.4's separate physical benchmark-host waiver is unchanged.
