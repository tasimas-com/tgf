# TGF — Design (implementation baseline, Rev 1)

This document turns the master plan (`TODO.md`, Revision 6) into concrete engineering
decisions and shows how each performance rule is enforced in code. Where this document and
the TODO disagree, the TODO's ADRs win until a superseding ADR is accepted.

## 1. Decisions made now

| Question | Decision | Where |
|---|---|---|
| `.lib` or `.dll`? | **Static by default**, shared optional (`-DTGF_BUILD_SHARED=ON`). Stable binary ABI only via the future C layer. | ADR-0028 |
| Demonstration executable | `tgf_showcase`, one binary that grows each phase; also the CI gate | ADR-0030 |
| Language / flags | C++20; library built without exceptions/RTTI; headers safe for user code with both | ADR-0001, 0029 |
| Floating point | No fast-math, no FMA contraction: bit-identical layout across compilers | ADR-0029 |
| Build | CMake ≥ 3.25 + presets; Ninja or VS 2022; namespaced targets `TGF::Core` ... | `CMakePresets.json` |
| Namespace / prefixes | `tgf::<module>`, `TGF_` macros, `tgf_` C symbols | TODO contract |
| First vertical slice | `tgf::core` (Phase 1 subset) + showcase + CI-style gates | this repo |

## 2. Repository layout

```
CMakeLists.txt, CMakePresets.json, cmake/     policy, options, install/export
core/                                          tgf::core  (include/tgf/core, src)
samples/showcase/                              tgf_showcase executable
tests/                                         header self-containment, CTest wiring
tools/check_deps.py                            dependency-DAG + hygiene checker
docs/                                          DESIGN.md, STATUS.md, adr/
platform/ rhi/ render/ text/ ui/ widgets/ pro/ host/ c/ bindings/   placeholders (README only) until their phase
benchmarks/ third_party/                       placeholders until P0.3 / P0.1.8
```
Each future module follows the same shape as `core/`: `include/tgf/<module>/` public headers,
`src/` private code, one CMake target `tgf_<module>` exported as `TGF::<Module>`.

## 3. Module graph (enforced, not advisory)

`core` ← `platform`, `rhi`, `text` ← `render` (core, rhi, text) ← `ui` (core, text, render,
platform) ← `widgets` ← `pro`; `tools`, `host`, `c` may use any public headers.
`tools/check_deps.py` encodes this table and runs in CTest (`dependency_dag`). It also rejects
third-party/platform/graphics headers in public headers and machine-specific absolute paths.
Adding a module = adding its row to the script and the CMake target in the same change.

## 4. How the performance rules become code

| Rule (TODO) | Mechanism in this repo | How it is verified |
|---|---|---|
| 0 heap allocations in steady state (DoD #4) | `ScopedAllocationCheck` measures the calling thread; TGF and `tracked_external_alloc_bytes()` record `MemoryTag`, live/cumulative/peak bytes, enforce per-tag budgets, and feed snapshot leak deltas. `ScopedMemoryLeakReport` emits per-tag outstanding deltas at a controlled host/plugin shutdown boundary. | Showcase verifies zero allocations for SlotMap, Arena, Pool, Profiler, SPSC and triple-buffer data paths, paired external allocator accounting, scoped shutdown reporting, and 1,000 warmed steady-state iterations with zero allocations. Hosts must route their own allocator through the adapter for visibility. |
| Growth only at boundaries, always visible | `SlotMap::reserve`, `GrowPolicy::Fixed`, `growth_events()`; arena/pool are fixed-capacity and report failure | Growth/Fixed-policy check |
| Handles, not pointers (rule 3) | `Handle<Tag>` = 8 B, generation 0 = invalid; `SlotMap` swap-removes into a dense array | Stale-handle, double-erase, reuse and growth-stability checks |
| Cache-friendly hot data | Dense value array + separate owner/slot arrays; queue indices on separate cache lines with cached remote index | Benchmarks (get 8–9 ns at 100k random, insert+erase ≈2 ns) |
| Real-time threads are sacred (ADR-0022) | `SpscQueue`, `TripleBuffer`: no allocation, no mutexes, trivially-copyable payloads, and compile-time always-lock-free atomic requirements. No portable formal wait-free or hard-deadline claim is made. | Bounded/full/empty checks, no-allocation checks, 2-thread stress, torn-read detector, and TSan on tested x86-64 target; each supported platform still needs its own timing/code-generation validation. |
| No float for domain coordinates (ADR-0017) | `SampleTime{i64}` with overflow-checked arithmetic; `to_camera_relative(Vec2d→Vec2f)` | Check shows naive f32 jitters (≈4.5 px) at 100 h @192 kHz vs 3e-6 px camera-relative |
| No exceptions inside the library (ADR-0001) | `Result<T>`/`Status`, `[[nodiscard]]`, `-fno-exceptions` for compiled core; template APIs use truthful conditional `noexcept` and explicit type constraints | `build_info()` flags + headers compiled standalone with exceptions on |
| Deterministic layout math (ADR-0029) | `-ffp-contract=off`, `/fp:precise`, no fast-math | (cross-compiler golden test arrives with P5.3.7) |
| Cheap diagnostics | Compile-time-stripped `TGF_LOG`/`TGF_ZONE`; zones in a per-thread ring, no locks | Profiler/log checks |

## 5. Build and run

```
# Linux / macOS (Ninja)
cmake --preset release            && cmake --build --preset release
ctest --preset release            # checks + dependency DAG
./build/release/bin/tgf_showcase  # full report incl. benchmarks
cmake --preset release-shared     && cmake --build --preset release-shared   # DLL/.so variant

# Windows, Visual Studio 2022 (no Ninja needed)
cmake --preset vs2022
cmake --build --preset vs2022-release
ctest --preset vs2022-release
build\vs2022\bin\Release\tgf_showcase.exe
```
Other presets: `debug`, `relwithdebinfo` (profiler on), `asan-ubsan`, `tsan` (non-Windows).
Outputs: static library in `build/<preset>/lib`, executable (and the shared library when
enabled) in `build/<preset>/bin`. `cmake --install` produces headers, the library and a
`find_package(TGF)` config; both linkage modes were tested with a minimal consumer project.

## 6. What the first slice contains (tgf::core)

`config`, `types` (fixed-width types, `Handle`, strong `Dip/Px/Seconds`), `assert`, `result`,
`log`, `memory` (counted alloc, `LinearArena`, `Pool`), `slot_map`, `spsc` (`SpscQueue`,
`TripleBuffer`), `math` (`Vec2/Rect/Color`, camera-relative), `time` (`SampleTime`), `hash`
(constexpr FNV-1a), `profiler`, `build_info`.

## 7. Known limits of this slice (be aware before relying on it)

* Verified on **Linux x86-64 with GCC 13 and Clang** in Release, Debug, ASan+UBSan, TSan, static
  and shared. **MSVC / Windows and macOS have not been built yet** — the code and presets are
  written for them (export macros, `_aligned_malloc`, `/W4` flags), but nothing counts as done
  on those platforms until the CI matrix runs (TODO §11.1).
* Benchmarks are single-process smoke numbers, not the pinned-frequency statistical suite of P0.3.
* `ScopedZone` costs ~70 ns (two `steady_clock` reads); fine for coarse zones, not for inner loops.
  It is off in Release by default. A calibrated TSC/QPC clock is planned.
* `MemoryTag`, `ScopedMemoryTag`, per-tag budgets, live/peak/cumulative statistics, snapshot leak deltas, tracked external allocator callbacks, and scoped lifecycle leak reports are implemented (P1.2.2/P1.2.3). Hosts must use `tracked_external_alloc_bytes()` for custom allocator blocks; raw uninstrumented allocations cannot be introspected safely.
* P1.2.5 is in progress: a fixed-capacity module allocator registry pins callback ownership until all blocks are freed, and `MappedFile` provides move-only whole-file mappings. Native Windows/macOS and actual plugin load/unload validation remain outstanding.
* No window, GPU or text exists yet: the showcase is console-only until M1.

## 8. Next work packages (in order)

1. **Finish Phase 1 core** — `Vector/SmallVector/Span`, flat hash map, `String`/`Atom`,
   `InlineFunction`, cross-module allocator ownership protocol, job system with thread roles, MPSC queue.
   Gate: containers must beat `std::` in benchmarks or be dropped (P1.3.6).
2. **Phase 0 evidence work in parallel** — CI matrix (Windows/Linux/macOS), benchmark noise-floor
   measurement, ADR-0001…0027 written as files, the RHI build-vs-adopt spike (P0.4.9) and the
   host-integration spike (P0.4.10), because they decide `rhi`/`platform` before any code is written.
3. **Phase 2 platform with mock backend first**, then a GLFW bring-up window so the showcase can show
   a real window at M1; native Win32 backend next (your primary environment).
4. **Phase 3 minimal RHI** (clear + rect batching) on the backend chosen in P0.4.9.

## 9. Decisions that need your input

* **First real window backend:** GLFW bring-up (fastest to M1) vs straight to native Win32. Default
  assumed: GLFW for bring-up only, native as the production path (matches the TODO).
* **RHI:** adopt (Dawn/wgpu/bgfx/NVRHI/SDL_GPU) vs own thin RHI — decided by spike P0.4.9, not by opinion.
* **Team capacity:** the TODO estimates 260–420 person-months. The scope levers in §6.2 of the TODO
  should be agreed early, because they change which reference demos gate 1.0.
