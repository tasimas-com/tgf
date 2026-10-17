# TGF coding standard

**Status:** normative engineering policy for the TGF repository  
**Applies to:** C++20 implementation, public headers, C ABI work, CMake, tests, tools, and project documentation  
**Related policy:** ` [TODO.md](../TODO.md), [DESIGN.md](DESIGN.md), [COMPILER_SUPPORT.md](COMPILER_SUPPORT.md), [ADR index](adr/README.md)

This document turns the TGF architecture and implementation contract into repeatable coding rules. It is not permission to change an architecture decision. Where a rule here appears to conflict with an accepted ADR or an explicit requirement in ` of TODO.md, the ADR/TODO decision wins; update this document when the discrepancy is resolved.

## 1. Non-negotiable project profile

- Use C++20. Disable language extensions and keep code portable across the supported MSVC, Clang, GCC, and AppleClang configurations.
- Keep implementation code in the owning module. Public C++ headers live below that module's include/tgf/<module>/ directory; private implementation belongs in src/ or another clearly private directory.
- Use the tgf namespace, TGF_ macro prefix, and tgf_ exported C-symbol prefix. Do not create new TASIMAS-prefixed implementation identifiers.
- Keep public headers self-contained and usable by downstream translation units compiled with exceptions and RTTI enabled, even though the TGF library implementation is built without exceptions and RTTI (ADR-0001).
- Preserve module dependency direction, allocator ownership, thread-affinity, real-time, and zero-steady-state-allocation contracts. A local convenience never overrides one of these contracts.
- Do not make a performance, portability, thread-safety, accessibility, or API-stability claim that has not been demonstrated by code, tests, or a recorded decision.

## 2. Naming and source layout

The following table is the canonical naming scheme. Follow existing names only when they already conform; do not propagate a legacy inconsistency into new code.

| Element | Convention | Example |
|---|---|---|
| Namespace | lower snake case | `tgf::core`, `tgf::render` |
| Namespace segment / module directory | lower snake case | `core/`, `widgets/` |
| Class, struct, union, enum, concept, type alias | UpperCamelCase | `SlotMap`, `MemoryStats`, `LogLevel` |
| Function and member function | lower snake case | `memory_snapshot()`, `set_log_level()` |
| Local variable and parameter | lower snake case | `frame_count`, `new_capacity` |
| Non-static data member | lower snake case with trailing underscore | `capacity_`, `free_head_` |
| Static/global storage variable | Avoid where possible; private implementation state uses `g_` + lower snake case | `g_alloc_count` |
| Named compile-time constant | `k` + UpperCamelCase | `kMemoryTagCount` |
| Enumerator | UpperCamelCase | `Error::OutOfMemory` |
| Template parameter | short descriptive UpperCamelCase | `T`, `Tag`, `Allocator` |
| Macro | `TGF_` + upper snake case | `TGF_ASSERT`, `TGF_VERSION_MAJOR` |
| Exported C function | `tgf_` + lower snake case | `tgf_create_context` |
| File | lower snake case | `mapped_file.hpp`, `memory.cpp` |
| CMake target | `tgf_<module>` with public alias `TGF::<Module>` | `tgf_core`, `TGF::Core` |
| Test | name the behavior or contract under test | `slot_map_rejects_stale_handles` |

Additional rules:

1. Prefer precise names over abbreviations. Use established short type aliases such as `u32` or `usize` where the project already defines them; do not invent new ambiguous aliases.
2. Use verbs for operations that change state and nouns/adjectives for queries. Predicates should read as questions or properties and return bool.
3. Avoid Hungarian notation, type-encoded variable prefixes, leading underscores, reserved-identifier patterns, and unscoped global names.
4. Do not add convenience aliases that hide units, ownership, mutability, or thread affinity. Use strong types for distinct units and domains.
5. Give constants internal linkage or namespace scope as appropriate. Do not create mutable global state inside the library implementation.
6. Use comments to explain intent, constraints, invariants, or non-obvious trade-offs—not to narrate each line.

## 3. Formatting and file organization

### 3.1 Formatter is authoritative

The repository's `.clang-format` file is the formatting source of truth. Its current policy is Google-derived style, two-space indentation, a 120-column limit, left pointer alignment, and case-sensitive include sorting. Do not hand-edit around clang-format or introduce per-directory style files without an approved decision.

Run the check before submitting C/C++ changes:

~~~sh
cmake --build build/release --target format-check
~~~

To apply formatting:

~~~sh
cmake --build build/release --target format-fix
~~~

The repository wrapper supports clang-format major versions 22 and 23. Generated files, build output, and third-party source are excluded. Never reformat vendored code as part of an unrelated change.

### 3.2 Includes and headers

- Every public header must compile when included by itself. The repository header self-containment target is the regression gate.
- A .cpp file includes its own corresponding public header first, when one exists. Then include the other project headers, standard-library headers, and third-party/platform headers in clearly separated groups.
- Include only what the file uses. Prefer forward declarations in headers when they are sufficient and safe.
- Do not use `using namespace` in headers or at namespace scope in implementation files.
- Do not rely on a transitive include. Include the declaration that provides each used type or function.
- Use `#pragma once` consistently with the current public headers.
- Public headers must not expose implementation-only, platform, graphics, windowing, font-engine, or immediate-mode GUI headers. Any deliberate exception must be part of the documented public integration surface and approved by an ADR.
- Keep include paths rooted at `tgf/<module>/...`. Do not use machine-specific absolute paths.

### 3.3 Module boundaries

A module owns its implementation, state, and private helpers. Use the dependency graph in TODO.md `4 and the dependency-DAG checker; do not bypass a boundary with relative includes, copied private declarations, or hidden link dependencies. Cross-module interaction must use an explicit public contract.

## 4. Types, interfaces, and C++ usage

- Prefer value types and explicit data structures. Use the project fixed-width aliases from `tgf::` when they improve clarity; use `usize` for sizes and indices.
- Use `enum class` for closed sets of values. Specify an underlying integer type when its size or representation is part of a memory, serialization, or ABI contract.
- Use `constexpr` and `const` when they communicate immutability or enable compile-time work without making code harder to understand.
- Make conversions explicit when they can lose information, change units, or cross a semantic boundary. Check overflow before size arithmetic and allocation-size multiplication.
- Mark single-argument constructors `explicit` unless implicit conversion is part of the documented type contract.
- Mark polymorphic base destructors virtual. Prefer composition and data-oriented dispatch to unnecessary inheritance or per-object virtual calls in hot paths.
- Do not use exceptions or RTTI in the TGF implementation. Public headers must nevertheless parse and work when included by consumer code with exceptions and RTTI enabled.
- Use `noexcept` when the operation is guaranteed not to propagate an exception. Do not add unconditional `noexcept` to operations that invoke user-supplied code or type operations that may throw; express conditional noexcept when appropriate.
- Avoid undefined behavior, unchecked narrowing, aliasing violations, uninitialized reads, and reliance on compiler-specific behavior outside the explicit portability layer.
- Do not introduce compiler intrinsics or platform APIs directly into portable modules. Isolate them behind a module/platform abstraction and test the fallback path.

## 5. Ownership, lifetime, and resource management

Every resource has one clearly identifiable owner and a documented release path.

### 5.1 Default ownership rules

1. Prefer automatic storage and value ownership for small, self-contained objects.
2. Use RAII for acquired resources: construction establishes ownership, and destruction releases it. Destructors must not throw.
3. Make ownership transfer explicit through move operations or named adopt/release operations. After transfer, the old owner must be visibly empty or invalid.
4. Treat raw pointers and references as non-owning borrows unless a declaration explicitly documents otherwise. State whether null is permitted, which object owns the pointee, and how long the borrow remains valid.
5. Do not return a reference, pointer, span, iterator, or string view whose backing storage can expire while the result is in use. Document invalidation rules for views into mutable or relocatable storage.
6. Avoid shared ownership as the default. Use reference counting only when independent shared lifetime is required and its synchronization, allocation cost, cycle behavior, and destruction thread are understood.
7. Do not store a borrowed pointer beyond the documented lifetime of its owner. Do not capture stack references in asynchronous work that may outlive the stack frame.

### 5.2 Module and plugin boundaries

- Never allocate in one module/CRT and free in another without an explicit paired allocator contract.
- Any memory crossing a module boundary must carry an explicit allocator/deallocator or be represented by an opaque handle whose owning module performs destruction.
- Use the module allocator registration and generation-handle rules in ADR-0012. A module must not unregister or unload while outstanding blocks or callbacks can still refer to its code.
- Do not expose allocator internals, STL ownership, or implicit destruction rules through the future stable C ABI.
- Document who destroys each resource, which module performs destruction, which thread may destroy it, and what happens if shutdown is attempted while dependent resources remain.
- Do not assume that the host owns or transfers a window, device, queue, swapchain, render target, or event loop. State ownership and synchronization at every integration boundary.

### 5.3 Handles and containers

Use opaque or generational handles when object references can outlive a storage location, cross a thread boundary, or cross an API boundary. A stale handle must be detected before dereference. A raw pointer must not be treated as a stable identity when storage can move or be reused.

Container growth must be explicit and observable. Hot-path code must use pre-reserved or fixed-capacity storage; do not hide allocation in lookup, layout, paint, input dispatch, or frame submission. State the invalidation behavior of pointers, references, iterators, and handles when a container grows, erases, compacts, or resets.

## 6. Error handling and contracts

### 6.1 Recoverable failures

TGF's implementation is exception-free (ADR-0001). Report expected failures through the existing error model:

- Return `tgf::core::Result<T>` when the operation may fail and produces a value.
- Return `tgf::core::Status` when the operation may fail but produces no value.
- Use the established `tgf::core::Error` values. Add an error value only when it expresses a distinct, actionable failure; document its meaning and whether retrying can help.
- Mark result-bearing functions and result types `[[nodiscard]]`. Callers must inspect or explicitly discard a result; never silently ignore it.
- Return `nullptr` only when null is the documented result for that API, such as an explicitly nullable allocation function. Do not use magic values or invalid handles to hide a recoverable error.
- Use bool for a natural predicate or a simple success/failure contract only when no diagnostic distinction is needed. Do not replace a meaningful Error with bool.
- Do not use process abort, assertions, logging, or a default object as a substitute for reporting invalid caller input or ordinary resource exhaustion.

### 6.2 Invariants and fatal conditions

- Use `TGF_ASSERT(condition, message)` for internal assumptions that should be checked in Debug builds but may be compiled out in Release.
- Use `TGF_CHECK(condition, message)` only for always-on invariants whose violation makes continued execution unsafe (for example, a condition required to prevent memory corruption).
- Validate external input and public API arguments and return an appropriate error instead of asserting that callers behaved correctly.
- Use `TGF_UNREACHABLE()` only after a condition has been proven impossible by the surrounding program logic. It is not a default branch for malformed input.
- Log enough context to diagnose a failure, but do not log secrets, credentials, document contents, or unbounded user-controlled strings. Logging from hot or real-time paths must obey their no-allocation/non-blocking constraints.
- A fatal process termination requires a documented unrecoverable invariant or explicit application policy. It must never be an accidental consequence of an unchecked recoverable error.

### 6.3 Noexcept, callbacks, and construction

No exception may cross a TGF implementation boundary. Callback types must state whether they can be called from any thread, their reentrancy rules, and their noexcept requirement. A public function is not automatically safe to mark noexcept merely because the library is built with exceptions disabled: consumer-provided types and callbacks may still be compiled with exceptions. Use compile-time constraints or conditional noexcept where a template invokes user code.

Constructors should establish a valid object or an explicitly documented empty/error state. Operations that can fail after construction should return a status/result or expose a documented two-step create/initialize pattern; do not leave a partially initialized object usable.

## 7. Thread safety and real-time behavior

- Every public API must state its thread-affinity or thread-safety contract: UI-thread-only, render-thread-only, worker-safe, externally synchronized, or thread-safe.
- The retained UI tree is owned by one UI thread. The render thread consumes immutable frame packets. Cross-thread communication uses documented queues, handles, snapshots, or messages—not unsynchronized access to mutable UI objects.
- Never make the host's audio, render, or simulation real-time thread wait for UI work. Do not introduce shared locks between the UI and a real-time thread.
- Real-time-facing operations must have bounded work and avoid allocation, blocking, OS calls, logging, and unbounded retries unless a documented platform-specific proof permits them.
- A lock-free atomic is not automatically wait-free, page-fault-free, or hard-real-time safe. Do not claim those properties without target-specific evidence.
- Document callback thread, ordering, reentrancy, and shutdown synchronization. Prevent callbacks from reaching an unloaded module.

## 8. Performance and memory discipline

- Design for zero heap allocation in the warmed steady-state per-frame path. Warm-up and boundary growth must be explicit, counted, and observable.
- Do not add hidden allocation to getters, iterators, formatting, event dispatch, layout, paint, or frame submission.
- Use TGF allocator APIs and memory tags for TGF-owned allocations. Pair external allocator callbacks and deallocation exactly.
- Check size calculations for overflow before allocating or copying.
- Bound queues, work budgets, recursion, and user-controlled input. Define behavior when capacity is reached.
- Benchmark hot-path changes in the same scenario and conditions as the stored baseline. Report CPU/GPU work, allocations, memory, and relevant tail latency; do not optimize from intuition alone.
- Keep cold diagnostics and verbose logging off the hot path. Instrumentation must itself obey documented allocation and timing constraints.

## 9. Public API documentation requirements

Every public type and callable API must document, where applicable:

- Purpose and important preconditions.
- Ownership: owns, borrows, adopts, transfers, or releases.
- Lifetime and invalidation rules for returned references, pointers, views, iterators, and handles.
- Nullability and valid value ranges.
- Error results and recovery behavior.
- Thread affinity, synchronization, callback thread, and reentrancy.
- Whether the call can allocate, block, call the operating system, or perform unbounded work.
- Version/stability classification and any platform/backend restrictions.

Do not require consumers to inspect implementation source to discover whether a pointer is owned, whether a function allocates, or which thread may call it. Provide a minimal compileable usage example for non-obvious public APIs. Keep examples consistent with the actual signature and ensure they are included in a test or a documented validation path when practical.

## 10. API and ABI stability levels

The following levels describe compatibility promises. The presence of `TGF_API` controls symbol visibility for shared builds; it does **not** by itself make a declaration stable.

| Level | Name | Meaning and rules |
|---|---|---|
| 0 | Private / internal | Not a supported consumer contract. May be renamed, moved, or removed without migration guarantees. Keep it out of installed public headers and exported symbols. |
| 1 | Experimental public C++ | Publicly visible for early adopters, but may change incompatibly before 1.0. Mark experimental status in the declaration's documentation. Changes still require tests and an update to examples/docs. |
| 2 | Supported public C++ | The intended 1.x C++ source API. Within a major version, preserve source compatibility except for documented deprecations and explicitly approved breaking changes. This does not promise a cross-compiler or cross-standard-library C++ binary ABI. |
| 3 | Stable C ABI | Reserved for the C interface planned around `tgf_c.h`. This is the binary boundary for independently built plugins and language bindings. It requires opaque handles, versioned size-tagged structures, explicit allocator ownership, documented calling conventions, and ABI compatibility tests before it can be advertised as delivered. |

Current project status and application rules:

- TGF is currently pre-1.0. Public C++ APIs are evolving and must be treated as Experimental unless a specific declaration has an explicit, reviewed stronger contract. Do not imply that version 0.1.0 is a frozen API.
- The supported C++ source-compatibility commitment applies to the 1.x release line. The exact semantic-versioning, deprecation-window, and compatibility-report mechanics remain subject to P12.7.
- The stable C ABI is a planned contract, not an implemented or released API today. P11.1 must deliver the C surface and tests before any declaration can be called Stable C ABI.
- C++ binary compatibility across compilers, standard libraries, or CRTs is not promised. Do not pass STL objects, exceptions, RTTI-dependent objects, or implicit allocator ownership across a DLL/plugin boundary.
- A public header is not automatically stable because it is under include/ or has TGF_API. Record the intended stability level in API documentation and review any promotion.
- A compatibility-breaking change requires API review, migration notes, tests for ownership/threading behavior, and an ADR/RFC when it changes an architectural contract.

## 11. Tests, reviews, and change hygiene

- Add tests for new behavior and for each corrected failure mode. Test invalid inputs, capacity exhaustion, stale handles, failure paths, and boundary conditions—not only the happy path.
- Tests must be deterministic, isolated, and safe to run repeatedly. Do not depend on machine-specific absolute paths, network access, wall-clock timing, or unseeded randomness unless the test explicitly validates that external property.
- Use sanitizers and static-analysis configurations where they apply. An analysis tool that is not installed or was not run is not a passing result.
- Public headers must pass self-containment checks and compile with exceptions/RTTI enabled for consumer code.
- CI must pass with warnings as errors on every supported compiler/configuration required by the current matrix.
- Review changes for module layering, memory/ownership, thread safety, accessibility/localization implications, performance, and license/SBOM impact.
- Update documentation, examples, ADRs, and migration notes in the same change when their contract changes.
- Never mark a TODO item complete merely because a file exists; its stated acceptance criteria and evidence must be satisfied.

## 12. Pull request checklist

Before requesting review, confirm:

- [ ] Names, file layout, include order, and formatting follow this standard and clang-format.
- [ ] Public headers are self-contained and expose no forbidden implementation/platform dependencies.
- [ ] Ownership, lifetime, invalidation, thread-affinity, and allocation/blocking behavior are documented.
- [ ] All recoverable failures use a documented result/status/error contract and are checked by callers.
- [ ] No exception/RTTI, undefined behavior, unchecked narrowing, or hidden hot-path allocation was introduced.
- [ ] Tests cover normal, error, boundary, capacity, and relevant concurrency paths.
- [ ] CI passes with the required compilers and warnings-as-errors.
- [ ] API stability level is explicit; compatibility changes include review, migration notes, and tests.
- [ ] Documentation, examples, ADRs, and license/SBOM records are updated as applicable.

