# tgf::render

**Job:** Display lists -> batching -> frame graph -> RHI. Owns the GPU glyph atlases and uploads text rasterization results.

**May depend on:** core, rhi, text  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 3-4. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/render/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
