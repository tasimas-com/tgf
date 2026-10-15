# TGF — TASIMAS GUI Framework

Repository: <https://github.com/tasimas-com/tgf> · Master checklist: [`TODO.md`](TODO.md)

Retained-mode, data-oriented, damage-driven C++20 GUI framework for large professional
applications and games. Free and open source (Apache-2.0 intended).

* Build matrix and commands: [`docs/BUILDING.md`](docs/BUILDING.md) · Master plan: [`TODO.md`](TODO.md) · Design baseline: [`docs/DESIGN.md`](docs/DESIGN.md) ·
  Status ledger: [`docs/STATUS.md`](docs/STATUS.md) · CI policy: [`docs/CI.md`](docs/CI.md) · Compiler policy: [`docs/COMPILER_SUPPORT.md`](docs/COMPILER_SUPPORT.md) · ADRs: [`docs/adr/`](docs/adr/)
* Snapshot audit (2026-10-14): [`docs/audit/`](docs/audit/) · The current implementation is an early `tgf::core` foundation, not yet a GUI framework 1.0.0.

## Current implementation slice

The current executable verifies the `tgf::core` foundation; it is not yet a graphical UI
framework. Core memory diagnostics now include subsystem tags, per-tag budgets, live/peak
accounting and snapshot leak deltas for allocations routed through TGF. Revision 9 strengthened P1.2.5 with allocator concurrency/capacity tests and mapped-file ownership tests; Revision 10 completed the Phase 0 CMake preset matrix; Revision 11 adds the compiler-support policy and optional formatting/static-analysis workflows; Revision 12 adds cross-platform GitHub Actions build/test workflows and a guarded nightly benchmark job. See
[`docs/memory-diagnostics.md`](docs/memory-diagnostics.md) and
[`docs/module-memory.md`](docs/module-memory.md) for their ownership contracts.

## Quick start
See [`docs/BUILDING.md`](docs/BUILDING.md) for the full Debug/Release/profiling/sanitizer matrix.

```sh
cmake --preset release
cmake --build --preset release --parallel
ctest --preset release
./build/release/bin/tgf_showcase          # add --json report.json for machine-readable output
```
Windows (Visual Studio 2022): `cmake --preset vs2022` then `cmake --build --preset vs2022-release`.
Shared library variant: `-DTGF_BUILD_SHARED=ON` (preset `release-shared`).

Consume from CMake: `find_package(TGF REQUIRED)` → `target_link_libraries(app PRIVATE TGF::Core)`.


## Memory diagnostics

See [`docs/memory-diagnostics.md`](docs/memory-diagnostics.md) for tracked host allocators, budgets, scoped shutdown leak reports, and the warm-up/steady-state allocation policy.
