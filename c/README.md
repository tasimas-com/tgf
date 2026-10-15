# tgf::c

**Job:** The stable C ABI (tgf_c.h). The only binary-stable boundary: plugins and language bindings go through it.

**May depend on:** any module's public headers  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 8. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/c/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
