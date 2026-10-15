# tgf::bindings

**Job:** Language bindings (C#, Python, Rust, ...) built on top of the C ABI only.

**May depend on:** c (the C ABI) only  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 8. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/bindings/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
