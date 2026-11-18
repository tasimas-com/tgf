# benchmarks

**Job:** Statistically gated performance suite (pinned frequency, noise-floor measured). Fails CI on regressions.

**May depend on:** any module's public headers  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in P0.3. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/benchmarks/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.


## Independent status check — 2026-11-18

The P0.3 benchmark harness remains **not started**. The current `samples/showcase/bench_core.cpp`
contains eight console microbenchmarks, but its source comment explicitly describes them as
smoke-level numbers to be replaced by the statistically gated P0.3 suite. They are useful for
checking that benchmarkable code paths exist; they are not a reproducible cross-framework
comparison and do not establish TGF's performance claims.

No Tier-A competitor workload implementations, equal-visual equivalence fixtures, documented
noise-floor/statistical method, reference-hardware tier matrix, persistent comparative result
store, dashboard, regression gate, or published fairness-qualified baseline report currently
exists here. The build-time/header-cost workflow in `docs/BUILD_PERFORMANCE.md` measures compiler
work, not runtime GUI performance, and must not be counted as P0.3 completion evidence. See the
[Phase 0 reassessment](../docs/audit/2026-11-18/PHASE_0_REASSESSMENT.md).
