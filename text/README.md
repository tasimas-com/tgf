# tgf::text

**Job:** CPU-only text: fonts, shaping, bidi, line breaking, paragraph layout, glyph rasterization to CPU bitmaps.

**May depend on:** core  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 4. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/text/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
