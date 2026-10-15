# TGF implementation status

**Status date:** 15 October 2026 — Revision 15  
**Audited input:** supplied `tgf-project.tar.gz`, subsequently updated through TODO Revision 10 on 14 October 2026  
**Canonical task checklist:** [`../TODO.md`](../TODO.md)  
**Full source-audit evidence:** [`audit/2026-10-14/`](audit/2026-10-14/)

## Executive status

TGF is an early engineering baseline, not yet a usable GUI framework and not ready for a
1.0.0 release. The current working implementation is concentrated in `tgf::core`, its
console showcase, CMake packaging for `TGF::Core`, and the dependency/hygiene checker.

The archive does **not** yet contain implementations of the native platform layer, RHI,
renderer, text system, retained UI, standard widgets, professional-app components, host/plugin
adapters, stable C ABI, language bindings, or release engineering. Those directories are
architecture placeholders with README files, not functioning modules.

## Task assessment of the supplied snapshot

The 272 original task entries comprise the checkbox tasks plus 13 task groups that were
previously written as bold prose. Those task groups are now represented in `TODO.md` with
explicit status markers. Final artifact entries are included in the counts below.

| Area | Done | Partial | Not started | Not delivered | Total |
|---|---:|---:|---:|---:|---:|
| P0 — foundations | 2 | 11 | 19 | 0 | 32 |
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

The TODO now contains fifteen separate audit-remediation entries beyond the 272-entry baseline:
thirteen are closed with regression evidence and two remain partial (formal realtime guarantees
and native mapped-file portability).


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

## Phase 0 progress — P0.1.3 compiler policy and quality tooling (Revision 11)

P0.1.3 is **partially complete**. `docs/COMPILER_SUPPORT.md` and
`cmake/compiler-support.json` define the current Tier-1 target generations: MSVC 14.51/14.50,
Clang 23/22, and GCC 16/15. `TGF_WARNINGS_AS_ERRORS` remains ON by default; MSVC uses `/W4`
and `/WX`, while GCC/Clang use the documented warning set and `-Werror`. Ninja presets now
export `compile_commands.json`.

Added `.clang-tidy`, optional `TGF_ENABLE_CLANG_TIDY` and `TGF_ENABLE_IWYU` CMake integration,
and the `tools/check_format.py` workflow with `format-check`/`format-fix` targets when a supported
clang-format executable is present. Missing optional tools cause explicit configure/command errors,
not silent success. `tools/check_compiler_policy.py` is registered as the CTest `compiler_policy`.

Revision 11 GCC 14.2 Release, Debug, and shared Release each built with warnings-as-errors and passed **5/5** CTest tests. Clang 17 Release also built with warnings-as-errors and passed **5/5** CTest tests. The actual Tier-1 compiler generations (GCC 15/16, Clang 22/23, MSVC 14.50/14.51) have not
been executed in this Linux environment. clang-format, clang-tidy, and IWYU are not installed
here, so source formatting and the analyzers have not yet been run. GCC 14.2 and Clang 17 are
legacy compatibility checks, not proof of the advertised Tier-1 matrix. Native MSVC remains
unverified. P0.1.3 therefore remains partial.

## What is implemented

- C++20 `tgf::core` static/shared library with foundational types/handles, `Result<T>`/`Status`,
  assertions, counted raw allocation, `LinearArena`, `Pool<T>`, `SlotMap<T>`, `SpscQueue`,
  `TripleBuffer`, basic 2D vectors/rectangles/colors, camera-relative double-to-float conversion,
  checked `SampleTime` arithmetic, FNV-1a hashing, logging, CPU scoped profiling, and build info.
- `tgf_showcase` console executable with 26 core checks, eight smoke benchmarks, and JSON output.
- Versioned cross-module allocator registry (`ModuleAllocatorDesc`, generation handles, and an
  outstanding-allocation unload guard) plus move-only `MappedFile` read-only/read-write APIs.
  POSIX mapping behavior is verified on Linux; Windows mapping code is present but not natively built.
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


**Not verified:** MSVC/Visual Studio, Windows, macOS, ARM, native Wayland/X11 windows, GPU APIs,
GPU drivers, or a cross-platform CI matrix in the original audited snapshot. GitHub Actions workflows were introduced in Revision 12 and hardened in Revision 13; they still require a real remote execution.

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
9. **Memory-mapped files — partially implemented:** Linux POSIX whole-file read/write mappings,
   flush, move ownership, and empty files pass regression tests. Windows/macOS native verification,
   file mutation coordination, and large-file platform tests remain open.

Details and exact verification are in `docs/audit/2026-10-14/TGF_CORE_REMEDIATION.md`.

## Recommended next sequence

1. Finish **P0.1.3**: run the complete supported MSVC/Clang/GCC generation matrix and execute clang-format, clang-tidy, and IWYU on supported toolchains.
2. Finish **P0.1.4**: execute/review the hosted Windows/Linux/macOS workflows, complete both Tier-1 compiler generations, and provision the dedicated pinned-frequency benchmark runner.
3. Continue P0.1.5–P0.1.9: coding standard, dependency-DAG CI enforcement, contribution policy, license/SBOM tooling, and build/header-hygiene tracking.
3. Complete P0.2: inventory existing assets, decide keep/rewrite/delete, and record the result in ADR-0018.
4. Complete P0.3: implement the benchmark harness and publish fair Tier-A baselines and measurable targets.
5. Complete P0.4 and P0.5: document research spikes, accept ADRs, and finalize estimates/reference application.
6. Only after Phase 0 exit criteria are met, resume remaining Phase 1 work (including native mapped-file/plugin lifecycle validation and formal realtime evidence) before implementing later phases.

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
