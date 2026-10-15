# tgf::host

**Job:** Adapters that embed TGF inside other programs (game engines, DAW/plugin hosts).

**May depend on:** any module's public headers  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 7-8. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/host/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
