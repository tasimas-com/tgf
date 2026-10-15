# tgf::widgets

**Job:** Button, text, input, list, tree, table, menu, tabs, slider, colour picker, dialogs.

**May depend on:** ui (public API only), core  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 6. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/widgets/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
