# benchmarks

**Job:** Statistically gated performance suite (pinned frequency, noise-floor measured). Fails CI on regressions.

**May depend on:** any module's public headers  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in P0.3. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/benchmarks/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
