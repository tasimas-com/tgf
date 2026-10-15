# ADR-0028: Library linkage and build artifacts

Status: Accepted (Phase 0 default; revisit only via superseding ADR)

## Context
TGF must produce `.lib`/`.dll` outputs plus an executable that demonstrates the result.
The project goal is maximum runtime speed and minimum size/RAM/startup. The TODO already
mandates modular static libraries with an enforced dependency DAG (ADR-0013) and a stable
C ABI as the only binary boundary (ADR-0012).

## Decision
1. **Default: static libraries** (`tgf_core.lib` / `libtgf_core.a`, one per module).
2. **Optional: shared** via `-DTGF_BUILD_SHARED=ON` (`tgf_core.dll` + import lib / `.so` / `.dylib`).
   `TGF_API` expands to `dllexport`/`dllimport`/`visibility("default")` only in that mode.
   Everything is hidden by default (`-fvisibility=hidden`), so a shared build exports only
   what is marked `TGF_API`.
3. The **C++ API is only supported across the same compiler + standard library + CRT**
   in both modes. A DLL is not a way to get a stable C++ ABI. The stable binary boundary is
   the future `tgf_c.h` C ABI, which is what plugins and language bindings use.
4. Consumers use namespaced targets (`TGF::Core`, later `TGF::UI`, ...) and are insulated from
   the choice: `find_package(TGF)` + `target_link_libraries(app PRIVATE TGF::Core)` works for both.
5. The showcase executable links the same target, so *the same sources* are verified in
   either mode; `build_info()` reports the actual linkage at runtime.

## Why static is the default
* Whole-program/LTO inlining across the library boundary: handles, slot-map lookups, the
  arena fast path and the SPSC queue are tiny functions or templates; a DLL boundary would
  block inlining and add an indirection per call.
* No loader cost at startup (budget: <30 ms to first frame) and linker dead-stripping
  (`--gc-sections`, `/OPT:REF`) removes unused widgets, shrinking the final binary
  (budget: <1.5 MB core).
* No CRT/allocator mismatch across modules: with one image there is one heap and one
  set of statics (profiler TLS, log sink, allocation counters).
* Matches ADR-0013: modular static libraries combined by the final link.

## Why shared stays supported
* Hot-reload of editor panels and plugin-hosted GUIs (ADR-0012, P7.9.7, P8.6).
* Large suites of apps that want to share one TGF image.
* Verified now: the shared build already caught two missing exports (`LinearArena`,
  `ScopedZone`) that a static-only build would never have shown.

## Consequences
* Every public class with out-of-line members must be `TGF_API`; the CI matrix builds and
  runs the showcase in both linkage modes to catch missing exports.
* When many modules exist, the shared build will bundle them into one `tgf` DLL (to avoid
  cross-DLL allocator and TLS issues); the static build keeps one `.lib` per module plus
  an interface target `TGF::TGF` that links all of them.
