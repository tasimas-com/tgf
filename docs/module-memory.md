# Module allocator ownership and mapped files (P1.2.5)

## Cross-module allocator registration

Each DLL/shared library/plugin that owns allocations registers a versioned
`ModuleAllocatorDesc`. The default constructor initializes `struct_size` to
`sizeof(ModuleAllocatorDesc)`; callers should preserve that value when preparing
the descriptor. It contains its ABI version, opaque context, and paired
`noexcept` allocate/deallocate callbacks. TGF stores
the descriptor in a fixed-capacity registry and returns a generational
`ModuleAllocatorHandle`.

A module allocates through `module_alloc_bytes(handle, size, alignment, tag)`
and releases the returned pointer only through `aligned_free_bytes()`. The
tracked header retains the TGF-side adapter and stable registry-slot context;
the actual module callback remains in the registered slot.

Before a module unloads, it must call `unregister_module_allocator(handle)`.
TGF returns `Error::Busy` while any allocations from that module remain live.
The host must stop new work, release all dependent objects/allocations, retry
unregistration, and only then unload the module. A successful unregister
invalidates the handle generation. This protects against use-after-unload of
allocator callbacks, but cannot stop a host from forcibly unloading a module
without following the protocol.

Callbacks may run concurrently and therefore must be thread-safe. They must
not throw, must use a matching allocator family, and their context must remain
valid until unregister succeeds. The registry uses a mutex for registration, unregistration, and outstanding-count
transitions; these APIs are not intended for realtime/audio callbacks. Regression
tests exercise 1,024 allocation/free pairs across four threads under ThreadSanitizer,
and verify the 64-slot limit plus rejection of a 65th active registration.

The descriptor is versioned but it is still a C++ function-pointer ABI. For
plugins built with unrelated compilers or CRTs, prefer a future versioned C ABI
with fixed-width fields and explicit calling convention. This work prevents
allocator mismatch only when the host obeys the registration/lifetime contract.

## Memory-mapped files

`MappedFile` maps a whole existing file with read-only or read-write access. The
public path is UTF-8. The OS backs the virtual address range and pages become
resident on demand; mapping a large file does not mean all bytes are resident
in RAM. Read-write mappings use shared mapping semantics. Call `flush()` when
the application needs to request persistence of modified mapped pages.

The object is move-only and releases the view, mapping object, and file handle
on `close()`/destruction. Empty files open successfully with a null view and
zero size. The mapping does not prevent another process from truncating the
file; applications must coordinate external mutation and keep the file stable
while accessing its mapped bytes. It is not currently a ranged/windowed
mapping API, and it does not provide async I/O or a file-growth protocol.
