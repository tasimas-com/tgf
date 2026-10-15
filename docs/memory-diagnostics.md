# TGF memory diagnostics contract

This document defines what TGF tracks and what an application must do to obtain
complete tracking for a subsystem.

## TGF-owned allocations

Use `aligned_alloc_bytes()` and `aligned_free_bytes()`, or TGF allocators built
on top of them. These allocations participate in subsystem tags, byte budgets,
live allocation/byte counts, peaks, snapshots, and `ScopedAllocationCheck`.
A `ScopedMemoryTag` supplies the default tag for the current thread; explicitly
set a tag on worker threads because tags do not automatically propagate across
thread creation.

## Host/custom allocator integration

A host that must use its own allocator can wrap it with `ExternalAllocator` and
allocate through `tracked_external_alloc_bytes()`. TGF places a private tracking
header in the backend block, enforces the requested payload alignment and the
TGF tag budget, then sends the block back through the matching deallocation
callback when `aligned_free_bytes()` is called.

The allocate/deallocate callbacks and their context must remain valid until all
returned blocks have been released. The callbacks must be `noexcept` and must
belong to the same allocator family. Never free an adapted block directly with
the backend; always call `aligned_free_bytes()`.

`heap_note_allocation()` is retained as an event-only compatibility hook. It
increments cumulative and thread-local allocation counters, but it does not
provide live-byte accounting, enforce a budget, or contribute to leak snapshots.
Do not use it as a substitute for paired tracked allocation and deallocation.

## Shutdown leak reporting

Create a `ScopedMemoryLeakReport` at the beginning of the application or plugin
lifetime and destroy it at the application's controlled shutdown boundary.
Its callback receives positive per-tag deltas for allocations still live since
the reporter was created. The callback is `noexcept` and should not allocate.
Destroy the reporter while TGF and the callback's code are still loaded. This
scoped design avoids registering an `atexit` callback into a shared library
that a host might unload before process exit.

Snapshots are deltas, not a tracing garbage collector: take the baseline at a
quiescent lifecycle boundary and avoid concurrent unrelated allocations when
interpreting the report. A positive delta reports outstanding tracked bytes;
a zero delta means no net increase in the tracked live counts at that boundary.

## Warm-up and steady-state policy

1. Perform one-time initialization, resource loading, cache population, and
   capacity reservation during startup/warm-up or an explicit frame boundary.
2. Start `ScopedAllocationCheck` only after warm-up has completed.
3. Run representative paint/layout/event/frame work under the guard. The
   steady-state contract is zero allocations on the guarded thread.
4. Any planned capacity growth must occur outside paint/layout/event work and
   must be measured and visible as an allocation/growth event.
5. Worker-thread activity is checked on that worker thread separately; a
   thread-local guard does not claim to observe allocations on other threads.

The showcase regression test reserves a vector during warm-up, runs 1,000
steady-state iterations with zero allocations, then deliberately grows it at a
boundary and verifies that the allocation counter observes that growth.
