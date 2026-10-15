# TGF memory diagnostics — implementation record

**Date:** 14 October 2026  
**TODO revision:** 6  
**Scope:** P1.2.2 complete for allocations routed through TGF; P1.2.3 remains partial.

## What was added

`tgf::core::memory` now provides fixed subsystem tags:

- `Unspecified`, `Core`, `Platform`, `Renderer`, `Text`, `UI`, `Widgets`, `Host`, `Sample`.
- `ScopedMemoryTag` sets a thread-local current tag and restores the previous tag at scope exit. Tags are not inherited automatically by new worker threads; set a scope on each worker that should be classified.
- `aligned_alloc_bytes(size, alignment)` inherits the current tag; the overload taking a `MemoryTag` assigns one explicitly.
- `MemoryStats` reports event counts, cumulative allocated/freed bytes, live allocation count, live bytes, peak live bytes, the configured budget, and budget-rejection count.
- `set_memory_budget(tag, bytes)` enforces a per-tag live-byte limit. A budget of zero means unlimited. Lowering a budget below current live usage is allowed; new allocations are refused until usage falls below the limit.
- `MemorySnapshot` and `memory_leaks_since()` report positive outstanding-allocation deltas from a captured baseline.
- `ScopedAllocationCheck::assert_no_allocations()` provides an always-on check for allocations observed on the current thread.

The diagnostics use fixed arrays and atomics. They do not allocate memory while updating counters or taking snapshots.

## Allocation coverage contract

The per-tag live/peak/budget accounting is authoritative for allocations routed through `aligned_alloc_bytes()` and corresponding `aligned_free_bytes()` calls.

The showcase replaces global C++ `new`/`delete` so all of its ordinary C++ allocations are routed through the TGF allocator. A production host may use the same pattern or route its custom allocators through the TGF allocation API.

`heap_note_allocation()` remains an event-only hook for external allocators. Calling it without paired allocation ownership/deallocation integration updates cumulative/thread allocation events but cannot establish live bytes, enforce the tag budget, or report leaks. This is intentional: TGF must not guess the size or lifetime of memory owned by an unrelated allocator.

`MemorySnapshot` reads independent atomics and is therefore not a globally transactional snapshot during concurrent allocations/frees. Capture baseline and final snapshots when the subsystem being measured is quiescent. `memory_leaks_since()` reports only positive outstanding deltas for a tag; it does not report a negative delta when older allocations were freed.

## Simple usage example

```cpp
using namespace tgf::core;

set_memory_budget(MemoryTag::Renderer, 64u * 1024u * 1024u); // 64 MiB
const MemorySnapshot before = memory_snapshot();
{
    ScopedMemoryTag renderer_memory(MemoryTag::Renderer);
    void* pixels = aligned_alloc_bytes(4096, 64);
    // Use pixels ...
    aligned_free_bytes(pixels);
}
const MemoryLeakReport leaks = memory_leaks_since(before, MemoryTag::Renderer);
TGF_CHECK(leaks.live_allocations == 0 && leaks.live_bytes == 0,
          "renderer memory leaked across the operation");
```

For a no-allocation hot path:

```cpp
ScopedAllocationCheck no_heap_in_this_thread;
update_realtime_state();
no_heap_in_this_thread.assert_no_allocations();
```

The allocation guard covers allocations that are reported on the calling thread. To include ordinary global C++ heap allocations, the host must route global `new`/`delete` through TGF or use equivalent instrumentation.

## Regression coverage

The showcase's new memory-diagnostics check verifies:

1. Default, nested, and restored scoped tags.
2. Stable human-readable tag names.
3. Global `new`/`delete` routed through the TGF allocator.
4. Successful in-budget allocations and rejection beyond a configured budget.
5. Correct requested-byte alignment.
6. Live allocation and byte counters.
7. Budget and exceeded-budget counters.
8. Snapshot leak deltas before/after frees.
9. Return to the baseline live-byte count after deallocation.
10. Concurrent allocation attempts against one shared budget never reserve beyond the limit.

The showcase now has 21 core checks, all passing.

## Verification performed

GCC 14.2 on Linux x86-64:

| Configuration | Build | CTest |
|---|---|---:|
| Release/static | Passed | 3/3 |
| Debug/static | Passed | 3/3 |
| Release/shared | Passed | 3/3 |
| ASan + UBSan | Passed | 3/3 |
| TSan | Passed | 3/3 |
| Clang 17 Release/static | Passed (optional LTO unavailable) | 3/3 |
| Installed static downstream consumer | Passed | Passed |

The shared build initially exposed missing symbol export on `ScopedMemoryTag`; the class was marked `TGF_API`, and the shared configuration subsequently built and passed all tests.

## Still open

- Full custom host allocator integration with paired allocation/free events and ownership-safe cross-module hooks (P1.2.5).
- Automatic shutdown leak summary/report policy.
- Host-level warm-up, steady-state, and boundary-growth integration tests as required by DoD #4.
- MSVC/Windows, macOS, ARM, and other supported-target validation.

Do not treat these open items as completed merely because the current TGF-routed allocator passes the tests above.
