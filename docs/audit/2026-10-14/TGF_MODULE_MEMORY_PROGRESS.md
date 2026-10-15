# TGF Revision 9 — P1.2.5 module memory progress

**Date:** 14 October 2026  
**Status:** Partial implementation, Linux/GCC and Linux/Clang verification passed. Revision 9 adds registry stress/capacity verification and reruns all available Linux configurations.

## What a beginner should understand

Cross-module memory ownership is like borrowing a tool from one workshop: the tool must be returned to the workshop that issued it, not destroyed by a different workshop. A mapped file is like a window into a very large book: the program can address the file's bytes without first copying the entire file into another buffer.

## Implemented: cross-module allocator registry

New public header: `core/include/tgf/core/module_allocator.hpp`.

- `ModuleAllocatorDesc` has a structure-size field, ABI version, opaque context, and paired `noexcept` callbacks.
- `register_module_allocator()` returns an 8-byte generational `ModuleAllocatorHandle` from a fixed 64-slot registry.
- `module_alloc_bytes()` adapts module allocations into the existing TGF tracking/budget system.
- `aligned_free_bytes()` calls the exact registered module deallocator.
- `unregister_module_allocator()` returns `Error::Busy` while outstanding allocations exist. The host must drain allocations before unloading the module. Stale handles are rejected after generation advances.
- Registry and lifetime transitions are mutex-protected. Callbacks may run concurrently and must be thread-safe; the APIs are not realtime-safe. Four threads completed 1,024 allocation/free pairs with exact callback pairing and zero outstanding blocks under ThreadSanitizer. All 64 slots can be occupied; a 65th registration is rejected with `CapacityExceeded`.

## Implemented: mapped files

New public header: `core/include/tgf/core/mapped_file.hpp`.

- UTF-8 path input, read-only and read-write whole-file mappings.
- `flush()` requests persistence for writable mappings.
- Move-only ownership; close/destruction releases the view and OS handles. Move construction and move assignment are both covered by regression tests.
- Empty files are valid and expose a null data pointer with size zero.
- Linux/POSIX implementation uses `open`, `fstat`, `mmap`, `msync`, and `munmap`. Windows implementation uses UTF-8-to-wide conversion and the native file-mapping APIs, but has not been built on Windows in this environment.

## Verification

- GCC 14.2 Release/static: build passed; CTest 3/3; showcase 26/26.
- GCC 14.2 Debug/static: build passed; CTest 3/3.
- GCC 14.2 ASan+UBSan: build passed; CTest 3/3.
- GCC 14.2 TSan: build passed; CTest 3/3.
- GCC 14.2 Release/shared: build passed with LTO disabled for this validation run; CTest 3/3.
- Clang 17 Release/static: build passed with LTO disabled; CTest 3/3.

New tests cover premature-unload rejection (`Error::Busy`), freeing through the exact registered backend, stale generation rejection, 64-slot capacity and overflow rejection, concurrent allocation/free from four threads (1,024 pairs), file read/write/flush persistence, read-only protection, move construction/assignment, and empty-file behavior.

## Remaining work

- Native Windows/MSVC compile and runtime test of `MappedFile` and registry APIs.
- Native macOS build/runtime verification of the POSIX implementation.
- True shared-library plugin load/unload integration test, including forced-unload policy and host coordination.
- Cross-toolchain plugin ABI must use a versioned C ABI or an explicitly supported compiler ABI; the current function-pointer descriptor is a same-process C++ contract only.
- Consider file mapping range/window support, concurrent truncation behavior, and large-file stress tests.

Accordingly, P1.2.5 remains `[p]`; its implementation slices are tracked individually in `TODO.md`. The concurrency/capacity subtask is complete, but native Windows/macOS and actual plugin ABI/load/unload evidence remain open.
