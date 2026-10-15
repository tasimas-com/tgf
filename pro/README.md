# tgf::pro

**Job:** Professional-app widgets: docking, timeline, node graph, piano roll, mixer, curve editor, viewport, property grid, image canvas.

**May depend on:** widgets, ui, core  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 7. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/pro/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
