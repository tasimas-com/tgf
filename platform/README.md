# tgf::platform

**Job:** Windows, keyboard/mouse/touch input, DPI, IME, clipboard, drag-and-drop. Exposes surfaces only as opaque native handles. No GPU, no ui.

**May depend on:** core  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 2. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/platform/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
