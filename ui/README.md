# tgf::ui

**Job:** Widget tree store, layout, style, input routing, focus, animation, commands/undo, accessibility tree.

**May depend on:** core, text, render (display-list API only), platform (event types only)  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 5. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/ui/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
