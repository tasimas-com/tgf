# TGF — TASIMAS GUI Framework

Repository: <https://github.com/tasimas-com/tgf> · Master checklist: [`TODO.md`](TODO.md)

Retained-mode, data-oriented, damage-driven C++20 GUI framework for large professional
applications and games. TGF is licensed under [Apache-2.0](LICENSE); third-party intake is governed by [the dependency policy](third_party/POLICY.md), and the repository SBOM is generated in SPDX 2.3 format.

* License: [`LICENSE`](LICENSE) · Notices: [`NOTICE`](NOTICE) · Third-party policy and dependency inventory: [`third_party/POLICY.md`](third_party/POLICY.md) · SBOM generation: [`docs/THIRD_PARTY.md`](docs/THIRD_PARTY.md)
* Contributing: [`CONTRIBUTING.md`](CONTRIBUTING.md) · Code of conduct: [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · Build matrix and commands: [`docs/BUILDING.md`](docs/BUILDING.md) · Coding standard: [`docs/CODING_STANDARD.md`](docs/CODING_STANDARD.md) · Master plan: [`TODO.md`](TODO.md) · Design baseline: [`docs/DESIGN.md`](docs/DESIGN.md) ·
  Status ledger: [`docs/STATUS.md`](docs/STATUS.md) · CI policy: [`docs/CI.md`](docs/CI.md) · Compiler policy: [`docs/COMPILER_SUPPORT.md`](docs/COMPILER_SUPPORT.md) · ADRs: [`docs/adr/`](docs/adr/)
* Build performance and header costs: [docs/BUILD_PERFORMANCE.md](docs/BUILD_PERFORMANCE.md) · Latest Phase 0 reassessment (2026-11-18): [audit report](docs/audit/2026-11-18/PHASE_0_REASSESSMENT.md) · The current implementation is an early `tgf::core` foundation, not yet a GUI framework 1.0.0.

## Current implementation slice

The current executable verifies the `tgf::core` foundation; it is not yet a graphical UI
framework. Core memory diagnostics include subsystem tags, per-tag budgets, live/peak
accounting and snapshot leak deltas for allocations routed through TGF. The Phase 0
infrastructure now includes CMake preset and dependency-DAG gates, contributor governance,
Apache-2.0 licensing, third-party provenance/SBOM generation, and clean/incremental build and
public-header cost tracking. On 2026-11-17, the configured hosted matrix passed 14/14 jobs,
source quality passed 2/2 LLVM jobs, build-performance passed, and SPDX SBOM generation
passed. The required stable MSVC pair is 14.52 and 14.51. Microsoft announced 14.52 as generally
available and an LTS release on 2026-11-16; the refreshed compiler matrix is being verified. Phase 0 remains
open; the asset inventory, competitor benchmark suite, research spikes, and ADR set are not
complete. Phase 1 is still gated. See
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
