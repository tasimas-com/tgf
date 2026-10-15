# TGF core safety remediation — 14 October 2026

This report records the first implementation pass against Appendix B of `TODO.md` Revision 5.
It supplements (does not overwrite) the source audit of the original supplied archive.

## Task results

| Task | Status | Evidence |
|---|---|---|
| AUD-CORE-001 | Done | `aligned_alloc_bytes()` validates alignment and size-rounding overflow; showcase tests valid/invalid allocations. |
| AUD-CORE-002 | Done | `LinearArena::allocate()` rejects invalid alignment, zero size, uninitialized use, and exhaustion in all build modes. |
| AUD-CORE-003 | Done | Pool node ownership/live state; foreign and immediate double destruction rejected; release destroys live objects. |
| AUD-CORE-004 | Done | Pool constructor exception safety + conditional `noexcept`; SlotMap nothrow type constraints. |
| AUD-CORE-005 | Done | `to_seconds()` returns `Result<f64>` and zero rate maps to `InvalidArgument`. |
| AUD-CORE-006 | Partial | always-lock-free atomic constraints, runtime checks, bounded failure tests, and no-allocation data-path checks; supported-target callback and timing evidence remain open. |
| AUD-CORE-007 | Partial | thread-local allocation scopes and successful allocation counting; tags/live bytes/leaks/budgets are still absent. |
| AUD-CORE-008 | Done | Existing bindings dependency rule fix and regression test retained. |

## API and behavioral details

### Allocation and arena

`aligned_alloc_bytes()` returns `nullptr` for zero size, zero alignment, non-power-of-two alignment, or a size whose rounding would overflow `usize`. Valid alignments below 16 are normalized to 16. Counts are incremented only after a successful allocation.

`LinearArena::allocate()` now treats invalid requests as ordinary allocation failures rather than relying on debug-only assertions. Failed requests increment `failed_allocations()`.

### Pool lifetime

Pool nodes hold explicit `live` state. `destroy()` returns `false` for null, foreign, or already-destroyed pointers; valid owned live pointers are destroyed and returned to the free list. `release()` destructs all live objects before freeing storage. `Pool<T>` requires a nothrow destructor. `create()` is conditionally `noexcept`; a throwing constructor leaves the free list unchanged.

A raw pointer cannot encode an object's generation. Callers must discard it after destroy; if the slot is reused, an old pointer has the same address as the new object. Use a generational `SlotMap` handle when stale identity must be detectable.

### SlotMap exception contract

SlotMap relocation/erase are `noexcept`. The template now statically requires `T` to be nothrow move-constructible, nothrow move-assignable, and nothrow destructible. This intentionally converts a runtime terminate hazard into a compile-time type requirement.

### Time conversion

`to_seconds(SampleTime, sample_rate)` now returns `Result<f64>`. A zero sample rate returns `Error::InvalidArgument`; consumers must check the result before reading its value.

### Realtime channels

SPSC and triple-buffer templates require `std::atomic<usize>` / `std::atomic<u32>` to be always lock-free on the target. Runtime checks are included. The C++ standard's lock-free property is not a formal wait-free or hard-realtime deadline guarantee, so TGF no longer makes that universal claim. The methods are `noexcept`, do not allocate, and use bounded algorithmic operations. Callback integration, target timing, generated code, and an explicit supported-platform matrix remain open; AUD-CORE-006 is therefore partial.

### Allocation diagnostics

`ScopedAllocationCheck` now records the current thread's counter, so unrelated worker-thread allocations do not affect a guarded hot path. The process-wide event and cumulative-byte counters remain cumulative traffic counters, not live-byte accounting. Tags, budgets, complete leak reporting, and host-wide allocation interception remain unfinished; AUD-CORE-007 is therefore partial.

## Regression coverage added/expanded

The showcase now verifies:

- invalid alignment and allocation-size overflow;
- arena invalid alignment, uninitialized use, exhaustion, and failure counting;
- pool ownership, immediate double-destroy rejection, live-object cleanup, and constructor-throw recovery;
- zero-sample-rate error behavior;
- lock-free atomic availability, SPSC empty/full behavior, `noexcept` data-path signatures, and zero-allocation queue/buffer data paths;
- scoped allocation isolation from an unrelated worker thread.

## Verification performed

Environment: GCC 14.2, Linux x86-64, CMake/Ninja, warnings-as-errors.

| Configuration | Build | CTest |
|---|---|---|
| Release | Passed | 3/3 passed |
| Debug | Passed | 3/3 passed |
| ASan + UBSan | Passed | 3/3 passed |
| TSan | Passed | 3/3 passed |

These results do not verify MSVC/Windows, macOS, ARM, or other platforms. Those remain open in the main TODO and platform/CI matrix. The SPSC/triple-buffer data-path checks are not a substitute for host audio-callback integration or per-target worst-case latency evidence.
