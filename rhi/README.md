# tgf::rhi

**Job:** Render Hardware Interface: one thin API over Vulkan, D3D12, Metal (D3D11/GL tier-2, software fallback). Consumes opaque native handles via a tiny NativeSurface struct from core.

**May depend on:** core  (table enforced by `tools/check_deps.py`)

**Status:** not started - arrives in Phase 3. This folder exists now so the repository layout matches
the master plan (P0.1.1). When work starts, copy the shape of `core/`:
`include/tgf/rhi/` for public headers, `src/` for private code, a `CMakeLists.txt`, and one CMake
target exported as `TGF::...`.
