# TGF — Design (implementation baseline, Rev 1)

This document records the current implementation baseline against the master plan (`TODO.md`).
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
tools/                                         dependency, compiler, license, SBOM, benchmark-host, build-cost and quality gates
docs/                                          design/status/policy/ADR and dated audit records
platform/ rhi/ render/ text/ ui/ widgets/ pro/ host/ c/ bindings/   architecture placeholders (README only) until their phase
benchmarks/                                     P0.3 harness not started; README only
third_party/                                   live policy and direct-dependency registry; no third-party source currently vendored
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
| Cache-friendly hot data | Dense value array + separate owner/slot arrays; queue indices on separate cache lines with cached remote index | Local console smoke measurements only; not validated competitor baselines |
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

* The current hosted matrix has built and tested native Linux, Windows, and macOS jobs. On
  2026-11-17, [CI run #412](https://github.com/tasimas-com/tgf/actions/runs/44089512975)
  passed 14/14 configured jobs across GCC 15/16, Clang 22/23, MSVC 14.50/14.51, and
  AppleClang 17 in Debug and Release. The MSVC pair is no longer the latest two: 14.52 became
  generally available on 2026-11-16 and remains absent from the checked-in matrix. See
  [COMPILER_SUPPORT.md](COMPILER_SUPPORT.md); that migration is open.
* Benchmarks are single-process smoke numbers, not the pinned-frequency statistical suite of P0.3.
* `ScopedZone` costs ~70 ns (two `steady_clock` reads); fine for coarse zones, not for inner loops.
  It is off in Release by default. A calibrated TSC/QPC clock is planned.
* `MemoryTag`, `ScopedMemoryTag`, per-tag budgets, live/peak/cumulative statistics, snapshot leak deltas, tracked external allocator callbacks, and scoped lifecycle leak reports are implemented (P1.2.2/P1.2.3). Hosts must use `tracked_external_alloc_bytes()` for custom allocator blocks; raw uninstrumented allocations cannot be introspected safely.
* P1.2.5 remains partial: the fixed-capacity module allocator registry pins callback ownership until all blocks are freed, and `MappedFile` provides move-only whole-file mappings. Its platform-specific code is built/tested in the hosted Windows/macOS/Linux matrix; actual plugin load/unload and foreign-toolchain ABI validation remain outstanding.
* No window, GPU or text exists yet: the showcase is console-only until M1.

## 8. Next work packages (in order)

1. **Re-establish the latest-two MSVC baseline** — update the support manifest, policy checker,
   and hosted matrix to MSVC 14.52/14.51, then pass the full native matrix with warnings-as-errors.
2. **Complete P0.2 asset inventory** — record keep/rewrite/delete decisions for the earlier
   scaffold and ImGui-derived prototype, with ADR-0018 and lessons learned.
3. **Implement P0.3 benchmarking** — deliver the Tier-A harness, reference hardware/scenario
   definitions, metrics/noise-floor method, repeatable results, and a fair baseline report.
4. **Complete P0.4/P0.5** — run and document the research spikes, deliver ADR-0001…0027 as
   accepted/rejected/superseded records, and finalize Phase 1–13 estimates and the first
   reference-application decision. Phase 1 remains gated until all Phase 0 exit criteria pass.

## 9. Decisions that need your input

* **First real window backend:** GLFW bring-up (fastest to M1) vs straight to native Win32. Default
  assumed: GLFW for bring-up only, native as the production path (matches the TODO).
* **RHI:** adopt (Dawn/wgpu/bgfx/NVRHI/SDL_GPU) vs own thin RHI — decided by spike P0.4.9, not by opinion.
* **Team capacity:** the TODO estimates 260–420 person-months. The scope levers in §6.2 of the TODO
  should be agreed early, because they change which reference demos gate 1.0.
