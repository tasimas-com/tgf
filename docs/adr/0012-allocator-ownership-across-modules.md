# ADR-0012 — Allocator ownership across modules

**Status:** Accepted for the current C++ core implementation; stable cross-toolchain C ABI remains future work.

## Context

TGF is intended to be embedded in large applications and plugins. Memory may be
allocated in one DLL/shared library and released in another. Different modules
may use different CRT heaps or custom allocators. Passing raw ownership across
that boundary without an explicit protocol can corrupt heaps or call code in a
module that has already been unloaded.

## Decision

1. A module registers a versioned `ModuleAllocatorDesc` containing callback
   pointers and an opaque context. Registration returns a generational handle.
2. TGF stores registrations in a fixed-capacity registry, avoiding registry
   allocations and stale-handle reuse.
3. `module_alloc_bytes()` wraps backend allocations in TGF tracking metadata,
   assigns a `MemoryTag`, enforces TGF's budget, and routes deallocation back to
   the exact allocator registration.
4. `unregister_module_allocator()` returns `Error::Busy` while any allocation
   owned by that registration remains live. The host must drain the module's
   allocations before unloading its code.
5. Callbacks are `noexcept`, thread-safe, paired, and their context must remain
   valid until unregister succeeds. These calls are not realtime-safe.
6. No STL container, exception object, or ownership-bearing C++ object crosses
   the stable plugin ABI. The current descriptor itself is a same-process C++
   callback contract; unrelated compiler/CRT plugins require a versioned C ABI.
7. File-backed large resources may use `MappedFile`, a move-only, UTF-8 path,
   read-only/read-write mapping abstraction with explicit flushing.

## Consequences

- TGF can account for and correctly route blocks from registered host allocators.
- An orderly module unload is blocked while the module still owns allocations.
- The host remains responsible for stopping work and retrying unregister after
  dependent objects have been destroyed. Forced unload bypasses the safety rule.
- The fixed registry has finite capacity (64 concurrent registrations).
- A mapping is virtual memory backed by a file, not a guarantee that the entire
  file is resident in physical RAM. External file truncation must be coordinated.

## Validation

Showcase tests verify generation invalidation, outstanding allocation counts,
`Busy` on premature unregister, callback pairing, read/write mapping, flush
persistence, move ownership, and empty files. GCC Release, Debug, ASan+UBSan,
TSan, Clang 17, and shared-library builds are required; Windows/MSVC and macOS
validation remain open until run in their native environments.
