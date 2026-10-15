# TGF Revision 7 — P1.2.3 allocation diagnostics completion

**Date:** 14 October 2026  
**Scope:** external allocator tracking, lifecycle leak reports, and warm-up/steady-state allocation verification.

## Beginner explanation

A game or professional application may have its own memory manager. TGF cannot safely guess how that manager allocates or frees memory. The application must connect it deliberately. The new adapter wraps both sides of the allocator, so TGF can label the memory, enforce its budget, count what is still in use, and later return the original block to the same allocator.

A leak report is like checking which borrowed items are still missing when an application or plugin shuts down. A steady-state test first lets the application prepare and reserve what it needs, then checks that normal repeated work does not keep asking for more memory. Planned growth is measured separately at a safe boundary.

## Implemented changes

### 1. Tracked external allocator adapter

Public API additions in `core/include/tgf/core/memory.hpp`:

- `ExternalAllocator` callback table (`allocate`, `deallocate`, `context`).
- `tracked_external_alloc_bytes()` wraps a custom backend block with a TGF tracking header.
- Payload alignment, per-tag byte budget reservations, live allocation/byte counters, cumulative/peak accounting, and snapshot leak deltas are updated.
- `aligned_free_bytes()` invokes the exact paired external deallocation callback with the original backend block, requested backend size, and alignment.

Callbacks are required to be `noexcept`, paired from the same allocator family, and valid until all wrapped blocks are freed. A host must not call its raw deallocator directly for a wrapped pointer.

### 2. Scoped shutdown leak reports

`ScopedMemoryLeakReport` captures a baseline and reports positive outstanding per-tag deltas from its destructor. The host creates it at application/plugin startup and destroys it at a controlled shutdown boundary while TGF and the callback code are still loaded. This deliberately avoids registering a process-global `atexit` callback into an unloadable plugin. Callbacks should not allocate. Deltas are meaningful when measured at a quiescent boundary.

### 3. Warm-up / steady-state boundary test

The showcase reserves a vector during warm-up, then runs 1,000 repeated iterations under `ScopedAllocationCheck`. The test verifies zero allocations in steady state. It then deliberately expands capacity in a separate frame-boundary guard and verifies the growth is observed by the allocation counter.

### 4. Documentation and TODO

- `TODO.md`: Revision 7; P1.2.3 and AUD-CORE-007 are closed; AUD-CORE-010 through 012 are added and closed.
- `docs/memory-diagnostics.md`: complete integration contract and recommended lifecycle.
- `docs/DESIGN.md`, `docs/STATUS.md`, and `README.md`: synchronized to the implementation.

## Verification

- GCC 14.2 Release/static configure and build: passed.
- CTest: 3/3 passed (`showcase_checks`, `dependency_dag`, `dependency_dag_bindings_rule`).
- Showcase: 23 checks, 0 failed.
- The new external allocator regression verifies 256-byte payload alignment, per-tag budget rejection, exact backend deallocation pairing, live-byte restoration, and shutdown leak callback values.
- The steady-state regression verifies 1,000 warmed iterations with zero allocations and counts the deliberate boundary growth.

Debug, ASan+UBSan, TSan, shared-library, Windows/MSVC, macOS, and ARM reruns remain separate validation tasks for this Revision 7 delta. Previous Revision 6 verification is recorded in `docs/STATUS.md` but must not be misrepresented as re-running these new changes.

## Limits / next phase

This closes P1.2.3 as a TGF capability: the hooks and contracts are now present, and external hosts can opt into them. TGF cannot track allocations a host does not route through TGF or this adapter. P1.2.5 remains open and must define ownership/allocator compatibility across DLL/shared-library/plugin boundaries and implement memory-mapped file utilities. AUD-CORE-006 also remains partial because C++ lock-free atomics alone do not prove formal hard-realtime or wait-free behavior on every supported target.
