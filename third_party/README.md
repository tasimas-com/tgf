# third_party

**Job:** Vendored third-party code. Every entry needs a licence check and a line in the third-party policy file (ADR-0016). Nothing is vendored yet.

**May depend on:** n/a  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in P0.1.8. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/third_party/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
