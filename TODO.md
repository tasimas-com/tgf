# TGF — TASIMAS GUI Framework
## Master Plan & Complete TODO  (Revision 22 — normative coding standard delivered)

> Goal: the fastest, leanest GUI framework for **large professional software and games** — Photoshop, Blender, After Effects, Cubase, Dorico, FL Studio, Cinema 4D, Unreal/Unity-class editors, and in-game UI for 2D/3D games — written in C++, minimal CPU / GPU / RAM / disk, with an architecture future engineers can extend for decades.
> License intent: free and open source (TASIMAS policy).
> Final deliverable of this plan: **TGF 1.0.0**, a professional, API-stable, documented, accessible, cross-platform release (criteria in §10).

Legend: `★` marks a task, decision or section added or materially changed during the audit. Revision 3 added the project-specific implementation contract; Revision 5 recorded core-safety remediation; Revision 6 records tagged memory diagnostics; Revisions 7–9 record lifecycle diagnostics, module allocator ownership, and mapped-file verification; Revision 10 completes the Phase 0 CMake preset matrix; Revision 11 adds the compiler-support policy, warnings-as-errors verification, and optional quality-tool workflows; Revision 12 adds cross-platform CI workflows, compiler caching, and a gated pinned-frequency benchmark job; Revision 13 hardens the hosted workflow and makes the MSVC sccache path effective through Ninja; Revision 14 records the connected GitHub account check and confirms that no TGF repository currently exists under that account; Revision 15 records the repository-creation blocker and initial-repository runbook. Revision 16 records creation of `tasimas-com/tgf`; Revision 17 records the published source and first hosted eight-job baseline; Revision 18 records the second successful eight-job run after the workflow-label/cache documentation corrections. Revision 21 records the project-owner-approved waiver of physical benchmark-host provisioning and runner registration; the workflow remains gated and no physical benchmark evidence is claimed. Revision 22 establishes the normative TGF coding standard and its CTest regression guard. Existing P0–P13 task IDs and ADR-0001–ADR-0027 are preserved wherever possible. Original task IDs are preserved so existing commits/issues still resolve; new tasks use new IDs.

 

## Project identity and implementation contract (TGF-specific)

This section is the canonical project profile. It resolves the difference between TGF as a general architectural idea and the actual TASIMAS project that will be implemented.

### Project identity

| Item | Decision |
|---|---|
| Full name | **TASIMAS GUI Framework** |
| Short name | **TGF** |
| Organization | **TASIMAS** |
| Public C++ namespace | `tgf` (sub-namespaces such as `tgf::core`, `tgf::ui`, `tgf::widgets`, `tgf::render`, `tgf::pro`) |
| Internal identifier prefix | `tgf` — do not use `tasimas` as the prefix for internal types, functions, macros, targets, or file names |
| Primary implementation language | **C++20** |
| Build system | **CMake 3.25+** with CMake Presets; Ninja is the preferred generator where available |
| Primary development environment | Visual Studio Community 2022 on Windows 11; this is a developer convenience, not a platform limitation |
| Product type | Modular, retained-mode, cross-platform GUI framework and UI renderer |
| License intent | Apache-2.0 for TGF, subject to the third-party license audit in ADR-0016 |
| First public major release | `1.0.0` |

TGF is a C++ framework, not a language-neutral specification and not a Rust/C#/Java framework. Bindings may be built on top of the stable C surface after the core API is established; they do not change the implementation language or the architectural ownership model.

### Product boundary: what TGF owns

TGF owns the machinery required to display and operate complex interfaces:

- Native windows and platform input integration when running in standalone mode.
- A retained widget tree, widget lifetime, stable handles, layout, styling, focus, input routing, animation, accessibility metadata, and UI automation IDs.
- Text shaping, text measurement, glyph rasterization support, and reusable text editing primitives.
- 2D UI rendering, batching, clipping, caching, compositing, and GPU resource management for TGF-owned UI resources.
- Optional application-level UI glue such as preferences scaffolding, workspace persistence, and command/undo infrastructure.
- Professional UI components: docking, timeline presentation/editing interactions, node-graph presentation/editing interactions, mixer controls, piano-roll presentation, property inspectors, profiler views, and large image-canvas presentation.
- Integration adapters that let an application provide its own window, event loop, GPU device, queue, render pass, swapchain, texture, or plugin-host surface.

### Product boundary: what the host application owns

TGF is **not** Photoshop, Blender, After Effects, Cubase, Dorico, Unreal, Unity, a game engine, a media engine, or an audio engine. The host application remains responsible for:

- The authoritative document, scene, project, asset, and data models.
- File formats and domain-specific serialization for its actual project files.
- Image processing, brush engines, layer compositing semantics, filters, color grading, and image export beyond the UI presentation/export facilities explicitly provided by TGF.
- 3D rendering, scene evaluation, physics, simulation, animation evaluation, shader compilation for the host's 3D engine, and viewport scene contents.
- Audio processing, DSP, transport clock, sample generation, plugin processing, and audio-thread scheduling.
- Video decoding/encoding, waveform analysis, thumbnail generation, and media processing.
- Node-graph execution semantics, visual-programming compilers, build systems, scripting runtimes, and application plugins.
- Business logic, networking, cloud synchronization, databases, licensing, updates, telemetry, and application-specific security policy.

TGF may provide reusable UI controls, adapters, drawing primitives, scheduling hooks, and data-binding contracts for those systems. It must not quietly absorb the host's domain responsibilities. For example, `Timeline` is a UI component and interaction model; the application owns the authoritative timeline data and playback engine. `ImageCanvas` presents and manipulates a host-provided tiled image source; the application owns the image document and brush/filter engine. `ViewportSurface` composites a host-rendered surface; TGF does not become the 3D renderer.

### Supported integration modes

All three modes are first-class architectural requirements, not optional late integrations:

1. **Standalone:** TGF creates and owns the native window, graphics device, event loop, and presentation lifecycle.
2. **Embedded surface / host-owned device:** the host owns its window and/or graphics device; TGF creates UI resources against an explicitly supplied device/queue and renders into a host-supplied target.
3. **Plugin GUI / host-pumped:** TGF is embedded as a child surface/window inside a DAW or another host application, and the host controls lifecycle, resize, DPI changes, and idle/frame pumping.

The RHI and platform interfaces must never assume that TGF owns `main()`, the native top-level window, the graphics device, the swapchain, or the main loop. Integration contracts must state resource ownership, synchronization, threading, device-loss handling, state restoration, resize behavior, DPI propagation, and shutdown order.

### Public API and naming contract

- Public C++ headers live under `include/tgf/`; implementation details live under `src/` or module-private directories.
- Public types/functions use the `tgf` namespace and consistent lower-case module naming. Macros use the `TGF_` prefix. Exported C symbols use `tgf_`.
- CMake consumers receive namespaced targets such as `TGF::Core`, `TGF::Platform`, `TGF::RHI`, `TGF::Render`, `TGF::Text`, `TGF::UI`, `TGF::Widgets`, and `TGF::Pro` (exact target set finalized in P0.1).
- No public header may require ImGui, GLFW, a platform SDK header, a graphics API header, or an implementation-only third-party header unless that dependency is explicitly part of the documented public integration surface.
- Do not expose STL types, C++ exceptions, compiler-specific RTTI, or implicit allocator ownership through the stable C ABI.
- The C++ API is source-compatible according to the documented semantic-versioning policy. A cross-compiler, cross-standard-library C++ binary ABI is **not** promised. The C ABI is the supported binary boundary for independently built plugins and language bindings.
- Handles are opaque/generational where lifetime can cross API boundaries. Borrowed pointers/references have explicit validity and thread-affinity rules.
- Every public API must state ownership, lifetime, thread safety, error behavior, and whether calls can allocate or block.

### Existing prototype and migration rule

The current TGF work has included CMake/C++ development, GLFW-based platform bring-up, and an ImGui-derived prototype/fork. Phase 0 must inventory the real repository before deciding what survives. The default is a clean retained/data-oriented TGF core. Existing ImGui code may remain in a separate reference or migration target, but:

- ImGui types and semantics must not leak into TGF public headers or ABI.
- TGF must not require an ImGui context or per-frame full-tree submission to operate.
- GLFW/SDL may be used for an early bring-up backend or sample, but native platform backends remain the production path required by the goals in §1.
- Existing working code is retained only when its ownership, threading, performance, portability, and license constraints pass the Phase 0 audit.

### 1.0 scope interpretation

The product matrix in §1.4 defines the classes of application TGF must serve. It does **not** mean that TGF 1.0 implements the domain engines or every feature of those products. The 1.0 deliverable is a reusable UI framework, a documented set of professional UI components, three integration modes, and representative reference applications/demos that prove those interfaces.

A feature is not considered complete merely because a widget can be drawn. For every 1.0 component, completion includes interaction semantics, keyboard/gamepad behavior where applicable, accessibility representation, localization/RTL behavior, high-DPI correctness, virtualization/stress behavior, state persistence where applicable, tests, documentation, and a measurable performance baseline.

If resources force a narrower 1.0, use the explicit scope-control levers in §6.2 and record the cut in an ADR/RFC. Never silently mark a post-1.0 item as complete or weaken a release gate to preserve the version number.

### Developer workstation notes (non-normative)

The Windows development setup may use Visual Studio 2022, CMake, Ninja, and a common local dependency directory such as `C:\Libraries`. This must remain a local developer choice. Repository files, public headers, build scripts, and installed packages must not contain absolute paths tied to one developer's machine. CI must prove a clean checkout builds without those local paths.

---

## 0. How to read and use this document

**Status legend:** `[ ]` not started / not delivered · `[p]` partially implemented but incomplete · `[x]` done · `[!]` blocked · `[?]` needs decision

**ID scheme:** `P<phase>.<section>.<task>` (e.g. `P3.2.4`). Every task has an ID so commits, issues and benchmarks can reference it. ADRs are `ADR-NNNN`. Audit findings are `F-NN` (Appendix A).

**Definition of Done (applies to every task):**
1. Code compiles warning-free on all tier-1 platforms and compilers.
2. Unit tests exist and pass (fuzz / property tests where input is untrusted or complex).
3. Benchmarks exist for anything on a hot path; no regression versus the stored baseline.
4. ★ No heap allocation in the **steady-state** per-frame hot path (verified by an allocation-counting test). *Steady state* = after warm-up; pools/arenas/caches may grow only at frame boundaries or on worker threads, never inside paint/layout/event loops, and every growth event is counted and visible in the profiler.
5. Public API documented with a usage example; ADR written if a design decision was made.
6. Reviewed by one other person (while solo: a written self-review checklist, plus the CI gates, plus an external review before each milestone M3 and later).
7. ★ Accessibility, localization/RTL, and high-DPI behavior of the feature are specified and tested (or explicitly marked N/A with a reason). These are not "later phases" (see F-05).
8. ★ Third-party code added by the task has a recorded license, version pin, and entry in the SBOM.

**Golden rule:** *Measure first, optimize second, but design for performance from day one.* Architecture decisions that cannot be changed later (memory model, data layout, threading model, numeric model, accessibility model, ABI, host-integration model) are decided in Phase 0 and written as ADRs.

**Relationship to the existing TGF work:** an earlier scaffold and a seven-phase plan exist (layered RHI over Vulkan/OpenGL/Metal), and there is also an ImGui-derived fork. Phase 0 includes an explicit audit to decide what is kept, rewritten or discarded. Map the old seven phases onto Phases 1–7 below.

---

## 1. Vision, goals, non-goals

### 1.1 Goals
1. **Speed:** 120/144 Hz capable; idle cost ≈ zero; interaction latency (input → pixels) as low as the OS allows.
2. **Lean:** small binary, small RSS, small VRAM, tiny startup time.
3. **Scale:** UIs with 100k+ logical items (timelines, outliners, node graphs, sample browsers) stay smooth through virtualization and incremental work.
4. **Pro-app widgets built in:** docking, timeline, node editor, curve editor, piano roll, mixer, knobs, color pickers, viewports, ★ image/paint canvas, ★ editor panels (details/outliner/console/profiler).
5. **Embeddability (both directions):** host 3D viewports, video, audio plugin GUIs (foreign windows) without hacks; ★ **and** be hosted — inside a game engine's render loop, inside an existing swapchain/device, or as a plugin GUI inside a DAW.
6. **Maintainable architecture:** strict layering, small modules, enforced dependency rules, excellent docs and tests.
7. **Cross-platform:** Windows, Linux (X11 + Wayland), macOS first-class. ★ Mobile/console are **architecture-preserved** (the platform and RHI interfaces must not preclude them; see ADR-0021) and delivered after 1.0 unless a funded need appears.
8. ★ **Games:** shippable in-game UI (small footprint, gamepad/keyboard navigation, safe areas, world-space UI, render-to-texture, localization) and game-editor UI from the same core.
9. ★ **Real-time safety:** the UI must never starve or block audio/render/simulation threads of the host app (no shared locks with real-time threads, bounded work per frame, adjustable priorities).

### 1.2 Non-goals (decided early to protect focus)
- Not a general application framework (no networking, database, XML, multimedia stack like Qt). TGF is UI only; integrate with other libraries.
- No native-look-and-feel widgets (not wxWidgets). TGF draws its own widgets for consistency and speed; it *does* integrate with native windows, menus (optional), dialogs, IME and accessibility APIs.
- No web view / browser engine inside the core.
- No built-in scripting language in the core (bindings come later, outside the core).
- ★ No exceptions, no RTTI, no `std::function` in hot paths, no global mutable state **inside the library implementation**. ★ Public headers must remain usable from user code compiled *with* exceptions and RTTI enabled (see ADR-0001).
- ★ Not a 3D engine or audio engine: TGF draws UI and composites host-provided surfaces; it does not own the app's scene, audio graph or document model.

### 1.3 Honest note on "beat everyone"
"Best" must be *provable*. Phase 0 builds a **public benchmark suite** and runs identical scenarios on a **tiered** competitor list (§P0.3.4): Dear ImGui, Qt Quick, Qt Widgets, Slint, egui, JUCE (the audio-industry baseline ★), Skia-based UIs, plus reference-only analysis of Unreal Slate, Unity UI Toolkit, Blender's UI and Flutter. TGF wins where it measurably wins, and the numbers are published. Differences by design: Dear ImGui is immediate-mode (re-submits everything every frame, great for tools, costly at scale); Qt is feature-rich (heavy); TGF targets the gap: **retained, data-oriented, damage-driven, GPU-batched**.

### 1.4 ★ Reference-product requirement matrix
Every product class below drives concrete requirements. A feature is "in scope for 1.0" if it is marked `1.0` in at least one row; otherwise it is `post-1.0`.

| Product class | Distinctive UI requirements | Where in plan |
|---|---|---|
| Photoshop / Krita / Substance | Gigapixel tiled canvas, color-managed display (ICC/OCIO), wide-gamut/HDR, low-latency pen strokes with prediction, huge layer panels, non-destructive filter UIs | P7.10 ★, P3.2.9, P2.3.2 |
| Blender / Cinema 4D / Houdini | Node editors, 3D viewport + gizmos, outliner 1M items, property grids with animated-property indicators, multi-window, custom keymaps | P7.2, P7.4, P7.6 |
| After Effects / Premiere / DaVinci | Timeline with 100k clips, keyframe/graph editor, video thumbnail strips, scopes, timecode, GPU-shared viewport | P7.3, P7.7 |
| Cubase / FL Studio / Ableton | Mixer, piano roll, meters at display rate, plugin GUI hosting, audio-thread-safe feeds, hours-long sample-accurate timelines | P7.3, P7.5, ADR-0022 |
| Dorico / Sibelius | SMuFL glyphs, page-based canvas, extreme zoom, 100k+ glyph pages, print/PDF export | P4.8, P7.5.5, P3.2.13 ★ |
| Unreal / Unity editors | Details/inspector panels via reflection, scene outliner, content browser, play-in-editor viewport, console/log, profiler flame graphs, material/blueprint graphs | P7.9 ★, P7.4, P7.6 |
| Shipped 2D/3D games | Tiny runtime, gamepad focus navigation, world-space UI, render-to-texture, host-owned device, safe areas, localization incl. CJK, 0 per-frame allocs | P8.5 ★, ADR-0020 |

---

## 2. Performance budgets (targets, verified by CI benchmarks)

These are targets to be validated in Phase 0 on reference hardware (define a low-end laptop, a mid desktop, an integrated-GPU machine, and ★ a 4K / 144 Hz / mixed-DPI multi-monitor rig). ★ **Every budget states its measurement condition** (resolution, DPI, backend, driver-memory accounting) — otherwise it is not a budget (F-03).

| Metric | Target | Measurement condition ★ |
|---|---|---|
| Idle CPU (static UI, window visible) | ~0% (no timer wakeups; event-driven) | 10-minute capture; ≤ 1 wakeup/s attributable to TGF when nothing animates |
| Idle GPU | 0 submissions when nothing is dirty | GPU queue capture |
| Input-to-photon latency | ≤ 1 display refresh + OS compositor latency, with a **latency mode** (UI + render on one thread, late input sampling) for pen/viewport interaction ★ | Hardware photodiode/camera method (P0.3.3) |
| Frame budget (typical interaction) | ≤ 2 ms CPU UI work at 100k-node *logical* tree (virtualized) | 1080p and 4K; mid desktop |
| ★ GPU frame cost | ≤ 0.5 ms GPU for a typical pro-app screen at 4K on mid desktop; ≤ 2 ms on reference iGPU | GPU timestamps |
| Cold start of "hello window" | < 30 ms to first frame **excluding** driver/device init; driver init reported separately ★ | Warm disk cache; per backend |
| Hello-window RSS | < 20 MB TGF-attributable private memory (stretch < 10 MB); total process incl. GPU driver reported separately because Vulkan/D3D12 drivers alone may use 50–150 MB ★ | Per backend |
| Core binary size | ★ ui + render + one backend, no complex-script shaping: < 1.5 MB stripped. With HarfBuzz + FreeType: < 3 MB. Documented per configuration | Release, LTO, stripped |
| ★ Per-node hot data | ≤ 64 bytes in the core node hot table (ADR-0003); kind-specific data in separate tables; **average total ≤ 256 bytes per typical widget** including kind data | Measured with allocation tags |
| Per-frame heap allocations | 0 in steady state (see DoD #4) | Allocation-counting test |
| Draw calls for a typical pro-app screen | < 50 (batched), ideally < 20 | Frame capture |
| Layout cost | O(changed subtree), never O(whole tree) for local changes | Counter test |
| Text: 10k visible glyphs | < 0.3 ms CPU to generate geometry (cache-hit path) | Latin + CJK sets |
| Scroll 1M-row virtual list | constant frame time | S3 |
| ★ Hours-long timeline | sample-accurate positions correct and jitter-free for ≥ 100 hours at 192 kHz | ADR-0017 numeric test |
| ★ Real-time safety | UI thread never takes a lock that an audio/render thread of the host may hold; worst-case UI frame work bounded and configurable | TSan + priority-inversion test |

**Rule:** any change that worsens a tracked metric by > 3% **(on a median of ≥ 30 runs, with noise floor measured in P0.3)** fails CI unless explicitly waived with an ADR. ★ A 3% gate on a noisy machine is meaningless, so CI uses dedicated, pinned-frequency benchmark runners and statistical comparison (e.g., Mann–Whitney), not single-run diffs.

---

## 3. Core architectural decisions (ADR index)

Each becomes a file `docs/adr/NNNN-title.md` in Phase 0. Recommended decision and rationale:

| ADR | Decision | Why |
|---|---|---|
| 0001 ★ | **C++20**, no exceptions, no RTTI **inside the library** (`-fno-exceptions -fno-rtti` for core). **Public headers compile and behave correctly in user TUs built with exceptions and RTTI on.** Allocation failure policy: core allocators return `Result`/null; UI-level OOM → documented degrade path then controlled abort with crash dump, never UB. Public C++ API: no STL types across the DLL boundary (see 0012). | Predictable perf, small binary; avoids the classic trap where `-fno-rtti` headers break user code. |
| 0002 ★ | **Retained-mode widget tree** with an **immediate-style authoring layer** on top. The sugar re-runs a builder **only when its inputs/state are dirty** (never every frame), diffing into the retained tree by stable IDs | Retained = damage tracking, incremental layout, GPU caching, accessibility tree, virtualization. Clarified so the sugar cannot reintroduce per-frame cost. |
| 0003 ★ | **Data-oriented storage** (SoA / handle-based arena, generational handles, no per-node `new`). Hot node table ≤ 64 B/node; kind data in per-kind tables | Cache locality, 0 allocs per frame, safe handles, cheap snapshots. Budget made consistent with the field list (F-04). |
| 0004 | **Dirty-flag + damage-rect invalidation** (style, layout, paint, composite separately) | Only changed regions are recomputed and redrawn; idle = nothing. |
| 0005 ★ | **GPU-first renderer** via a thin **RHI**. **Tier-1 backends: Vulkan, D3D12, Metal.** Tier-2 (compat, post-M4): D3D11, OpenGL 4.3/ES 3.x. **Software (CPU) renderer for tests, screenshots, and broken-driver fallback.** WebGPU post-1.0. P0.4.9 evaluates adopting an existing RHI (Dawn/wgpu-native/bgfx/NVRHI/SDL_GPU) vs own; the decision is recorded here | Six hand-written backends is multi-person-years of maintenance (F-06). Fewer, thinner backends + a decision spike. |
| 0006 ★ | **Text: HarfBuzz shaping + FreeType (or stb_truetype subset) rasterization.** Rendering strategy is **hybrid by size**: hinted coverage-bitmap atlas for small UI sizes (best quality), SDF/MSDF (or GPU glyph-path rendering — verify patent/license status) for large/zoomed text; CPU glyph cache; subpixel positioning options | MSDF alone blurs small text; one strategy cannot serve both UI labels and 400% zoomed scores (F-07). |
| 0007 | **Own layout engine**: flexbox-like + grid + absolute + "pro" constraints (anchors, splitters, docking) with incremental relayout | Predictable, fast, fully controllable; avoid importing a heavyweight CSS engine. P0.4.2 compares against Yoga/Taffy first. |
| 0008 ★ | **Threading model:** UI tree owned by one UI thread; **render thread** consumes immutable *frame packets*; worker job system for text shaping, image decode, layout of independent subtrees. Cross-thread access only via message queues / handles. **Latency mode:** UI and render may run on one thread to remove the extra frame of pipelining. Thread priorities and job-system worker count are configurable so the host's audio/render threads are never starved | The pipelined model adds ≥ 1 frame of latency, contradicting the latency budget unless an escape hatch exists (F-08). |
| 0009 | **Memory:** custom allocators (frame/linear arena, pool per type, small-block), all allocations tagged and tracked | Zero hot-path malloc, leak detection, budgets. |
| 0010 | **Event system:** no virtual-call-per-widget soup; typed event queue + sparse handler tables; command-based actions | Speed, undo/redo, scripting, and testability. |
| 0011 | **Styling:** compiled style sheets → flat style tables (no string lookups at runtime); themes are data; design tokens | No hash-map style lookups per draw. |
| 0012 ★ | **ABI:** C++ API for engineers + **stable C ABI** (`tgf_c.h`) for bindings and plugins. Rules: no allocator/ownership crossing a module boundary without explicit allocator hooks; no STL in the stable ABI; structs versioned with size fields | DLL boundaries without name-mangling or CRT-mismatch crashes. |
| 0013 | **Modular static libraries** with enforced dependency DAG (CMake targets + CI script that rejects illegal includes) | Future engineers can't create spaghetti. |
| 0014 | **Pro-app extensibility:** custom widgets are first-class (same API as built-ins); viewports can be GPU-shared textures or native child surfaces | Needed for 3D viewports, video, plugin editors. |
| 0015 | **Build:** CMake ≥ 3.25 + presets, vcpkg/Conan-optional, zero required third-party runtime deps except vendored/optional ones. ★ Compile-time budget: full clean build and incremental build times tracked in CI; public headers are minimal and self-contained | Easy adoption; large codebases die by build time. |
| 0016 ★ | **License: Apache-2.0** (explicit patent grant; compatible with MIT-style third-party code). Third-party audit gate: HarfBuzz (MIT), FreeType (choose FTL, not GPL), VMA (MIT), zstd (BSD/GPL dual → BSD), ICU/Unicode data (Unicode license). Bundled fonts must be OFL/Apache (e.g., Bravura, Leland) | Resolves open question 5; patent clause matters for a rendering/text library (F-17). |
| 0017 ★ | **Coordinate/numeric model:** device-independent pixels (DIP), `float` layout for UI chrome, snapped to device pixels at paint; per-monitor DPI. **Large-domain coordinates (timeline time, infinite canvas, score pages, gigapixel images) use `double`/`int64` in the domain model and a camera-/origin-relative transform to `float` for layout and GPU.** Sample-accurate time is `int64` samples + rational rate, never `float` | `float` has 24 bits of mantissa: 10 h at 192 kHz is ~6.9 billion samples and zoom ranges of 10^6 cannot be float (F-02). |
| 0018 | Result of the existing-asset audit (P0.2.2): keep / rewrite / delete table | Resolves the old-fork question with evidence. |
| 0019 ★ | **Accessibility-by-design:** every widget kind declares its role/states/actions in its behavior table from the first widget; the a11y tree is built from the UI tree with dirty updates; platform bridges follow in Phase 9, but the data model is fixed in Phase 5 | Retrofitting a11y into a finished tree is the usual failure (F-05). |
| 0020 ★ | **Host-integration model:** TGF can (a) own window + device + loop, (b) own window but use a host's device, (c) render into a host-provided swapchain/render pass/texture and be pumped by the host's loop (engine and DAW-plugin mode). The RHI supports **adopting external device/queue/command buffers**; platform layer supports **no-window / embedded-surface** operation | Unreal/Unity-class engines, game overlays, plugin GUIs all require (b)/(c); without it TGF cannot be used in half the target software (F-09). |
| 0021 ★ | **Platform tiering:** Tier-1 Windows/Linux(X11+Wayland)/macOS. The platform and RHI interfaces must be implementable by private (NDA) console backends and by iOS/Android without changing upper layers; touch, gamepad and on-screen-keyboard are in the core event model from day one | Keeps games/mobile possible post-1.0 without redesign (F-10). |
| 0022 ★ | **Real-time-thread contract:** audio/render threads communicate with UI through bounded SPSC/latest-value structures; target atomics must be always-lock-free. UI must not block the realtime side. Formal wait-free/page-fault-free guarantees require target-specific proof and pre-touch/host-callback validation; do not infer them from `is_always_lock_free` alone. | DAW/plugin hosting correctness (F-14). |
| 0023 ★ | **Internationalization model:** UTF-8 everywhere, ICU-class data for segmentation/bidi/collation (vendored subset), logical (start/end) rather than left/right in layout and styles, text direction a property of every container from the first layout implementation | RTL/bidi cannot be bolted onto left/right-based layout (F-05). |
| 0024 ★ | **Trust/security boundary:** all file formats TGF parses (themes, markup, images, fonts, workspaces, clipboard, DnD) are treated as untrusted; parsers are bounds-checked, fuzzed, and have size/recursion limits | Pro apps open files from the internet (F-15). |
| 0025 ★ | **Undo/Document boundary:** TGF provides the command/undo *framework* and transactions; the **document model belongs to the app**. UI-state undo (layout, selection) is separate from document undo | Prevents TGF from becoming an app framework (non-goal) while still serving pro apps. |
| 0026 ★ | **Reflection/inspection hook:** property grids bind through a minimal, optional, user-supplied property-descriptor interface (no mandatory macro reflection, no RTTI); a code-generator for descriptors is provided in tools | Needed for Unreal/Unity-style details panels without forcing RTTI (F-11). |
| 0027 ★ | **Frame-pacing & present policy:** documented per platform (flip-model/mailbox/FIFO/relaxed, Wayland presentation-time, Metal display link), adaptive to VRR; the app can request fixed-rate, vsync-driven, or on-demand frames | Smoothness and idle behavior depend on it. |

> `[?]` Decide in Phase 0: keep ImGui-derived code as a *prototype / migration shim* or start clean. Recommendation: **start clean for the core, keep the fork only as a reference and a compatibility test bed** — an ImGui-derived design fundamentally re-submits and re-hashes everything every frame, which conflicts with ADR-0002/0004.

---

## 4. Architecture overview

```
┌──────────────────────────────────────────────────────────────┐
│ Applications  (samples, reference pro apps, user software)    │
├──────────────────────────────────────────────────────────────┤
│ tgf::pro      Docking · Timeline · NodeGraph · PianoRoll ·    │
│               Mixer · CurveEditor · Viewport · PropertyGrid · │
│               ImageCanvas ★ · EditorPanels ★                  │
├──────────────────────────────────────────────────────────────┤
│ tgf::widgets  Button · Text · Input · List · Tree · Table ·   │
│               Menu · Tabs · Slider · ColorPicker · Dialogs    │
├──────────────────────────────────────────────────────────────┤
│ tgf::ui       Tree store · Layout · Style · Input routing ·   │
│               Focus · Animation · Commands/Undo · A11y tree   │
├───────────────┬───────────────────────┬──────────────────────┤
│ tgf::text     │ tgf::render           │ tgf::platform        │
│ shaping·bidi· │ Display lists → batch │ Windows·Input·DPI·   │
│ fonts·layout  │ → Frame graph → RHI   │ IME·Clipboard·DnD    │
│ (CPU only)    │ (owns glyph atlases)  │ (no GPU, no ui)      │
├───────────────┴───────────────────────┴──────────────────────┤
│ tgf::rhi   Vulkan · D3D12 · Metal · (D3D11/GL tier-2) · SW    │
├──────────────────────────────────────────────────────────────┤
│ tgf::core  Memory · Containers · Math · Jobs · Log · Profiler │
└──────────────────────────────────────────────────────────────┘
          Side modules: tgf::tools (inspector, profiler UI, hot reload),
                        tgf::c (C ABI), tgf::bindings, tgf::test,
                        tgf::host ★ (engine/DAW integration adapters)
```

**★ Explicit dependency table (enforced by CI; fixes the ambiguity of the original diagram, F-12):**

| Module | May depend on |
|---|---|
| core | std only |
| platform | core (surfaces are exposed as *opaque native handles*; platform never includes rhi/render/ui) |
| rhi | core (consumes opaque native handles from platform via a tiny `NativeSurface` struct defined in core) |
| text | core (CPU-only: fonts, shaping, bidi, line breaking, paragraph layout, glyph rasterization to CPU bitmaps) |
| render | core, rhi, text (owns GPU glyph atlases and uploads text rasterization results) |
| ui | core, text, render (display-list API only), platform (event types only, via core-defined event structs) |
| widgets | ui (public API only) |
| pro | widgets, ui (public API only) |
| tools, host, c | any of the above through public headers |

**Dependency rules:**
- A layer may depend only on layers it is allowed in the table above.
- `core` depends on nothing but the standard library.
- `rhi` backends never include each other; platform code never includes `ui`.
- `widgets` and `pro` use only the public `ui` API (same API as user widgets — "eat your own dog food").

**Frame pipeline:**
`OS events → input queue → event routing → state update/animation → style resolve (dirty only) → layout (dirty only) → paint (generate display list, dirty only) → batch & sort → frame packet → render thread (or same thread in latency mode) → RHI submit → present (damage rects)`.

---

## 5. Phases

---

### PHASE 0 — Foundations, decisions, benchmarks (do this before writing the framework)

**Purpose:** remove risk, define "best" with numbers, lock the irreversible decisions.

**P0.1 Repository and tooling**
- [x] P0.1.1 Monorepo layout: `/core /platform /rhi /render /text /ui /widgets /pro /tools /host /c /bindings /samples /benchmarks /tests /docs /third_party /cmake`
- [x] P0.1.2 CMake presets (debug, release, relwithdebinfo, asan, ubsan, tsan, msan, profiling)
  - Evidence: configure/build/test presets are connected for Debug, Release, RelWithDebInfo, profiling, ASan, UBSan, TSan, and MSan; `release-shared` and the legacy combined `asan-ubsan` remain available.
  - Compiler-aware sanitizer flags are centralized through `TGF_SANITIZER`; unsupported compiler/sanitizer combinations fail with an explicit configuration error instead of silently accepting GNU flags.
  - `tools/check_presets.py` validates preset uniqueness, required modes, sanitizer selection, and configure/build/test references; CTest registers it as `cmake_preset_matrix`.
  - Evidence: GCC 14.2 Linux builds and CTest passed for Debug, Release, shared Release, RelWithDebInfo, profiling, ASan, UBSan, TSan, and combined ASan+UBSan; Clang 17 MSan also passed. MSan does not install TGF's global `new` override because MSan owns those interceptors; the global-new accounting assertion and the separate warm-up test that depends on that hook are excluded, while explicit TGF allocation checks remain active. The Visual Studio 2022 presets are defined but require a Windows host for native execution.
- [x] P0.1.3 Compilers: MSVC (latest 2), Clang, GCC; warnings-as-errors; `clang-tidy`, `clang-format`, `include-what-you-use`
  - [x] P0.1.3.a Document the Tier-1 compiler generations and C++20 baseline in `docs/COMPILER_SUPPORT.md` and `cmake/compiler-support.json` (MSVC 14.51/14.50, Clang 23/22, GCC 16/15; reviewed 2026-10-15).
  - [x] P0.1.3.b Make warnings-as-errors the default and add a regression check for MSVC `/W4` + `/WX` and GCC/Clang warning flags + `-Werror`.
  - [x] P0.1.3.c Add `.clang-format` enforcement workflow (`format-check` / `format-fix`) and a portable source-file checker; hosted enforcement passed on LLVM 22.1.8 and 23.1.4, checking all 29 repository C/C++ source files.
  - [x] P0.1.3.d Add `.clang-tidy` policy and opt-in CMake integration (`TGF_ENABLE_CLANG_TIDY`); complete TGF Debug builds passed clang-tidy with warnings-as-errors on LLVM 22.1.8 and 23.1.4.
  - [x] P0.1.3.e Add opt-in Include-What-You-Use integration (`TGF_ENABLE_IWYU`) with explicit missing-tool and MSVC configuration errors; strict IWYU builds passed on IWYU 0.26/LLVM 22 and IWYU 0.27/LLVM 23. The generated duplicate-include header self-containment harness is narrowly excluded because its unused includes are the test itself; all implementation and showcase translation units remain checked.
  - [x] P0.1.3.f Export `compile_commands.json` for Ninja presets and add compiler-policy regression coverage to CTest.
  - [x] P0.1.3.g Execute the Tier-1 compiler matrix (MSVC 14.51/14.50, Clang 23/22, GCC 16/15) with warnings-as-errors.
    - Latest evidence: GitHub Actions [run #193](https://github.com/tasimas-com/tgf/actions/runs/39056856383), commit `f9674c393c8ff09ed46625b4b4334350b413b6c2`, passed **14/14 jobs** (MSVC 14.50/14.51, Clang 22/23, GCC 15/16, AppleClang; Debug and Release). All 14 CTest ZIP artifacts were downloaded, ZIP-integrity checked, and inspected: each contains **11/11 passing CTest cases** and the showcase reports **26 checks, 0 failed**; **154/154 CTest executions passed**.
    - Source-quality evidence: GitHub Actions [run #119](https://github.com/tasimas-com/tgf/actions/runs/39056856378) passed both LLVM jobs: clang-format checked 29 files; complete clang-tidy and strict IWYU builds passed with warnings-as-errors. Exact tool pairing: LLVM 22.1.8 + IWYU 0.26; LLVM 23.1.4 + IWYU 0.27.
    - Evidence: GitHub Actions [PR run #30](https://github.com/tasimas-com/tgf/actions/runs/38745686719), commit `a4169289e8ea031b005aefba7a89d9e13a4075c2`, passed **14/14 jobs** (seven compiler targets × Debug/Release). Verified compiler versions: GCC 16.0.1 and 15.2.0; LLVM Clang 23.1.4 and 22.1.2; MSVC 19.50.35739.0/toolset 14.50.35717 and 19.51.36260.0/toolset 14.51.36231. Every configuration explicitly enabled `TGF_WARNINGS_AS_ERRORS=ON`.
    - Evidence: all 14 uploaded CTest ZIP artifacts were downloaded, ZIP-integrity checked, and inspected. Each contains seven passing CTest entries and a showcase result of 26 checks with zero failures: **98/98 CTest executions passed**. AppleClang 17.0.0 Debug/Release remains the additional native macOS compatibility lane.
- [p] P0.1.4 CI matrix: Windows / Linux / macOS × compilers × configs; artifact caching; nightly benchmark job ★ on dedicated pinned-frequency runners
  - [x] P0.1.4.a Add push/PR/manual cross-platform build-and-test workflow for Windows, Linux, and macOS in Debug and Release.
  - [x] P0.1.4.b Add GitHub Actions build-directory caching with `actions/cache@v4` and upload one CTest log artifact per matrix job; the hosted baseline confirmed all eight artifacts.
  - [x] P0.1.4.c Add scheduled/manual nightly benchmark workflow, explicit dedicated-runner label, and repository-variable safety gate.
  - [x] P0.1.4.d Add a fail-closed CPU-frequency preflight plus unit tests and CTest workflow-contract checks.
  - [x] P0.1.4.e Execute and review the hosted GitHub Actions matrix on `tasimas-com/tgf`; run #13 passed all eight jobs, compiler versions were recorded, and all eight downloaded CTest ZIP artifacts were inspected.
    - [x] P0.1.4.e.1 Re-run the local workflow contract, YAML parser, preset graph, and existing GCC/Clang CTest builds; all available local checks pass.
    - [x] P0.1.4.e.2 Use the MSVC developer environment with Ninja (not the Visual Studio project generator), add Windows MSVC/Ninja presets, and serialize native PDB writes with /FS; the hosted workflow uses GitHub Actions build-directory caching, not an MSVC sccache compiler launcher.
    - [x] P0.1.4.e.3 Refresh checkout and artifact actions to their current v7 major releases and document the Node.js 24 runner prerequisite for the dedicated self-hosted host.
    - [x] P0.1.4.e.4 Execute the hosted matrix on `main`; run [#13](https://github.com/tasimas-com/tgf/actions/runs/38730051352) passed 8/8 jobs, and run [#14](https://github.com/tasimas-com/tgf/actions/runs/38738723466) passed 8/8 again after the workflow-label and documentation corrections.
    - [x] P0.1.4.e.5 Complete the initial account/repository discovery before creation; the earlier check found no TGF repository, and the user subsequently created the dedicated `tasimas-com/tgf` repository (recorded in .e.6).
  - [x] P0.1.4.e.6 Create the dedicated repository `tasimas-com/tgf`; verified through the connected GitHub account on 2026-10-15. Repository ID `1420440551`, default branch `main`, public visibility, and admin/push permissions were returned by GitHub. The repository was empty at verification time (size 0); no existing content was overwritten.
  - [x] P0.1.4.e.7 Publish the full project at the `main` root, execute all eight hosted jobs, inspect compiler versions and CTest artifacts, and record the successful run.
    - [x] P0.1.4.e.7.d Repeat the eight-job matrix after workflow-label and CI contract corrections in run [#14](https://github.com/tasimas-com/tgf/actions/runs/38738723466); all eight jobs passed and all eight new CTest artifacts were verified to contain seven passing tests.
    - [x] P0.1.4.e.7.a Publish the full project root, including the authoritative root `TODO.md`, source, tests, workflows, and documentation.
    - [x] P0.1.4.e.7.b Inspect all eight hosted jobs and record exact compilers: GCC 15.2.0, LLVM Clang 22.1.2, MSVC 19.51.36260.0/toolset 14.51.36231, and AppleClang 17.0.0; each Debug/Release job passed 7/7 CTest tests.
    - [x] P0.1.4.e.7.c Download and inspect all eight uploaded artifact ZIPs; each archive is valid and contains `LastTest.log` reporting 100% (7/7) passing tests.
  - [x] P0.1.4.f Deliver the dedicated benchmark-runner workflow, acceptance tooling, and operator runbook. **Owner-approved scope waiver (2026-10-17):** physical host provisioning and live runner operation are waived for this project stage; the nightly workflow remains safely gated and is not represented as operational.
    - [x] P0.1.4.f.1 Write `docs/BENCHMARK_RUNNER_SETUP.md` covering hardware, CPU-frequency policy, runner registration, security isolation, repository-variable gating, and artifact review.
    - [x] P0.1.4.f.2 Validate the fail-closed host preflight; its expanded ten-case unit suite covers pinned-frequency and bare-metal/VM checks. This environment correctly fails the real-host check because it exposes no CPU frequency policy and is virtualized. The separate inventory collector has five unit tests.
    - [x] P0.1.4.f.3 Complete the repository-side host acceptance and inventory tooling. **Physical-host acceptance waived by project owner (2026-10-17):** no dedicated bare-metal host, pinned-frequency configuration, or sustained thermal validation is claimed.
      - [x] Add a read-only JSON inventory collector for CPU topology/model/microcode, memory, DMI firmware, every exposed CPU-frequency policy, thermal zones/hwmon sensors, OS/kernel, compiler/build-tool versions, and allowlisted GitHub runner metadata.
      - [x] Extend the nightly preflight with a fail-closed x86-64/bare-metal check; VM detection must positively report no VM, in addition to the existing requirement that every frequency policy uses the performance governor and identical positive min/max limits.
      - [x] Register inventory regression tests in CTest, enforce the nightly inventory step in the CI contract checker, and upload the host-inventory.json report with the benchmark artifact.
      - [x] Replace the circular setup stub with an operator runbook covering physical acceptance, CPU-frequency pinning, thermal validation, inventory review, runner isolation/registration, and the readiness gate.
      - [x] Owner-approved waiver recorded: dedicated physical host procurement/provisioning, frequency pinning, and thermal validation are intentionally deferred. The inventory collector, fail-closed preflight, regression tests, CI contract, artifact capture, and operator runbook remain delivered.
    - [x] P0.1.4.f.4 **Runner registration and first-run acceptance waived by project owner (2026-10-17).** No self-hosted runner is registered, `TGF_BENCHMARK_RUNNER_READY` remains unset, and no dedicated-host nightly benchmark artifact is claimed. Keep the workflow disabled until the owner reverses this waiver and the complete physical-host acceptance procedure is performed.
  - [x] P0.1.4.g Complete and execute the full two-generation Tier-1 compiler matrix and add native Windows/macOS results. Satisfied by the 14/14-job hosted matrix recorded under P0.1.3.g: [run #30](https://github.com/tasimas-com/tgf/actions/runs/38745686719), including native Windows MSVC 14.50/14.51 and macOS AppleClang 17 Debug/Release.
- [x] P0.1.5 Coding standard document (naming, ownership, error handling, API stability levels). Delivered in `docs/CODING_STANDARD.md`, linked from the README, and guarded by `coding_standard_policy` CTest.
  - [x] Define repository naming, layout, include, and formatting rules consistently with the actual `.clang-format` and module namespace contract.
  - [x] Document ownership, lifetime, handle, allocator-boundary, and plugin-unload requirements from the architecture and ADR-0012.
  - [x] Specify exception-free error reporting, `Result<T>`/`Status`, `[[nodiscard]]`, and the assert/check distinction.
  - [x] Define private, experimental public C++, supported 1.x C++, and planned stable C ABI levels without claiming an unreleased ABI exists.
  - [x] Add a regression check for required policy sections and register it in CTest; document the check and link the policy from the README.
- [p] P0.1.6 Dependency-DAG checker script (fails CI on illegal includes, using the §4 table)
- [ ] P0.1.7 Contribution guide, code of conduct, issue/PR templates, ADR template
- [ ] ★ P0.1.8 License/SBOM tooling and third-party policy file (ADR-0016)
- [p] ★ P0.1.9 Build-time and header-hygiene tracking (clean + incremental build time budgets, per-header cost report)

**P0.2 Audit of existing TGF assets**
- [ ] P0.2.1 Inventory the existing scaffold and the ImGui-derived fork: what is reusable (platform glue, RHI sketches, shaders, tests)?
- [ ] P0.2.2 Decide per module: keep / rewrite / delete; record in ADR-0018
- [ ] P0.2.3 Preserve lessons learned (e.g., bypass style hash lookups, alpha-skip draws, integer-aligned rounding, flag-bit hygiene) in `docs/lessons.md`

**P0.3 Benchmark and comparison harness (the heart of "beat the competition")**
- [p] P0.3.1 Define reference hardware tiers and OS versions (★ include a 4K/144 Hz/mixed-DPI rig and a Wayland machine)
- [p] P0.3.2 Define scenarios (identical visuals in each framework):
  - S1 Hello window (startup time, RSS, binary size)
  - S2 10k buttons static (idle cost), then hover/animate one
  - S3 Scrolling 1M-row list/table
  - S4 Text-heavy: 100k visible glyphs, live editing, selection
  - S5 Timeline: 5,000 clips, zoom/pan, scrub
  - S6 Node graph: 2,000 nodes / 5,000 links, pan/zoom/drag
  - S7 Mixer: 128 channels × (meter + fader + knobs), 60–144 Hz meters
  - S8 Docking: resize/split/undock with 40 panels
  - S9 Resize storm (continuous window resizing)
  - S10 Embedded viewport (GPU-shared texture at 4K)
  - S11 Multi-monitor mixed-DPI move
  - ★ S12 Gigapixel image canvas: pan/zoom 1:1 to 3200%, pen strokes with latency measurement
  - ★ S13 Flame graph / profiler view with 5M events
  - ★ S14 In-game overlay: UI drawn into a host render pass with a 144 Hz game loop, steady-state allocations measured
  - ★ S15 Hours-long timeline numeric precision (ADR-0017 verification)
- [ ] P0.3.3 Metrics: frame time distribution (p50/p95/p99/max), CPU time, GPU time, RSS, VRAM, disk size, startup time, input latency (hardware camera/photodiode method documented), power draw where measurable; ★ benchmark noise floor and statistical comparison method
- [p] P0.3.4 ★ **Tiered baselines** (a 9-framework × 11-scenario matrix is ~100 implementations and would consume the project — F-13):
  - **Tier A (full suite, before M1):** Dear ImGui, Qt Quick, Slint, JUCE (S1, S2, S3, S4, S7, S9)
  - **Tier B (key scenarios, before M3):** Qt Widgets, egui, a Skia-based sample, Flutter (S1–S6, S9)
  - **Tier C (reference analysis only, no port):** Unreal Slate, Unity UI Toolkit, Blender UI, wxWidgets, GTK, SFML-custom — study architecture and published numbers
- [p] P0.3.5 Automated result store (JSON) + dashboard + regression gating
- [ ] P0.3.6 Publish baseline report: where each competitor is strong; set TGF numeric targets from it; ★ fairness statement (equal visuals, equal DPI, equal presentation mode, release builds)

**P0.4 Research spikes (time-boxed, 1–2 weeks each, throwaway code allowed)**
- [ ] P0.4.1 Retained tree storage layout (SoA vs AoS vs hybrid) micro-benchmark
- [ ] P0.4.2 Layout algorithm prototype (flex + incremental) vs Yoga/Taffy comparison
- [ ] P0.4.3 Vector path rendering approach: tessellation vs analytic coverage (SDF) vs compute rasterization; choose for rounded rects, strokes, curves, shadows
- [ ] P0.4.4 Text pipeline spike: HarfBuzz + hinted bitmap atlas vs SDF/MSDF vs GPU glyph-path rendering; subpixel positioning and quality at 9–14 px and at 400% zoom
- [ ] P0.4.5 Present-latency spike per platform (flip model, mailbox, waitable swapchain)
- [ ] P0.4.6 Damage-rect presentation spike (partial present support per API: `VK_KHR_incremental_present`, `Present1` dirty rects, Metal/Wayland/X11 behavior) ★ including whether compositors make damage rects worthwhile
- [ ] P0.4.7 Threading spike: UI thread + render thread with frame packets ★ vs latency mode; measure the added frame of latency
- [ ] P0.4.8 Embedded viewport spike: shared textures across Vulkan/D3D/Metal and native child surfaces
- [ ] ★ P0.4.9 **RHI build-vs-adopt spike:** evaluate Dawn / wgpu-native / bgfx / NVRHI / SDL_GPU against a hand-written thin RHI on: external-device adoption (ADR-0020), shared-texture interop, binary size, shader pipeline, maintenance cost. Output: ADR-0005 final
- [ ] ★ P0.4.10 **Host-integration spike:** render TGF into (a) a Vulkan engine render pass, (b) a D3D12 engine's command list, (c) a DAW plugin window (VST3/CLAP) — validates ADR-0020 before the RHI is frozen
- [p] ★ P0.4.11 **Numeric-domain spike:** prove float-GPU + double-domain camera-relative rendering for timeline (100 h @ 192 kHz), node canvas (zoom 10^6), gigapixel canvas; no jitter or precision seams
- [ ] ★ P0.4.12 **Accessibility data-model spike:** minimal widget set exposed to UI Automation + NSAccessibility + AT-SPI from a retained tree with dirty updates, including virtualized lists
- [ ] ★ P0.4.13 **Real-time-safety spike:** meters/playhead fed from a real audio callback; verify no blocking, no priority inversion, no page faults on the audio side

- [p] **P0.5 Write ADRs 0001–0027, finalize Phase 1–13 estimates (see §6.2), choose the first reference app (§9)**

**Exit criteria:** benchmark harness green with Tier-A competitors; ADRs accepted; spike results documented; repo + CI running.

---

### PHASE 1 — `tgf::core` (runtime foundation)

**Purpose:** the substrate everything depends on. Must be tiny, fast and bulletproof.

**P1.1 Platform/compiler abstraction**
- [p] P1.1.1 Macros/attributes: export, inline control, likely/unlikely, prefetch, restrict, cache-line size
- [p] P1.1.2 Fixed-width types, strong typedefs (`Dip`, `Px`, `Seconds`, ★ `SampleTime`, `DomainCoord`), `Handle<T>` (index + generation)
- [p] P1.1.3 Assert/contract system (debug-break, release-log, compile-out levels), `TGF_UNREACHABLE`
- [p] P1.1.4 Error model without exceptions: `Result<T,E>` / `Expected`, error codes, `[[nodiscard]]`; ★ allocation-failure policy (ADR-0001)
- [p] ★ P1.1.5 Header-compatibility tests: public headers compile and link in TUs with exceptions+RTTI on and off, and under /std:c++20 and c++23

**P1.2 Memory**
- [p] P1.2.1 Allocator interface; linear/frame arena (reset per frame), pool allocator, small-block allocator, page allocator
- [x] P1.2.2 Allocation tagging + budgets + tracking (debug and release stats): fixed subsystem tags, scoped tag propagation, per-tag live/cumulative/peak counters, enforced byte budgets, and allocation-free snapshots are implemented for TGF-routed allocations.
- [x] P1.2.3 Leak detection and "allocation in hot path" detector: thread-local `ScopedAllocationCheck::assert_no_allocations()`, per-tag snapshot leak deltas, `tracked_external_alloc_bytes()` paired host-allocator adapter, `ScopedMemoryLeakReport` lifecycle callback, and warm-up/steady-state allocation-boundary integration checks are implemented. Host allocators must opt into the adapter; uninstrumented allocations outside TGF remain intentionally invisible.
  - [x] P1.2.3.a Tracked external allocator adapter: backend callbacks are paired, TGF enforces payload alignment and per-tag budgets, tracks live/cumulative/peak bytes, and calls the matching backend deallocator through `aligned_free_bytes()`.
  - [x] P1.2.3.b Scoped shutdown leak reporting: report outstanding per-tag live deltas from a lifecycle-scoped callback; avoid a process-global `atexit` pointer that could outlive an unloadable plugin.
  - [x] P1.2.3.c Warm-up/steady-state boundary test: warm-up growth is separated from a 1,000-iteration steady-state loop (zero allocations); deliberate frame-boundary growth is measured and counted.
- [ ] P1.2.4 Optional mimalloc/rpmalloc integration behind the allocator interface
- [p] ★ P1.2.5 Cross-module allocator hooks (ADR-0012) and memory-mapped file utilities: versioned module allocator registration, generation handles, outstanding-allocation unload guard, and move-only mapped-file API are implemented. POSIX mappings are verified; native Windows/macOS validation and a true dynamically loaded plugin unload test remain open.
  - [x] P1.2.5.a Versioned module allocator descriptor and generational registration handle (fixed 64-slot registry; no registry heap allocation).
  - [x] P1.2.5.b Cross-module allocation/free pairing and unload guard (`Error::Busy` while blocks are outstanding; stale generations rejected).
  - [x] P1.2.5.c POSIX whole-file mapping, read-only/read-write access, flush, zero-length handling, and move ownership; showcase integration tests pass.
  - [p] P1.2.5.d Windows UTF-8 path / file mapping implementation and macOS POSIX compatibility are written but await native CI verification.
  - [p] P1.2.5.e Actual plugin load/unload integration test and cross-compiler stable C ABI adapter remain open; current C++ callback descriptor is a same-process ABI contract.
  - [x] P1.2.5.f Registry concurrency and capacity verification: four threads completed 1,024 paired allocations/frees; callback pairing, zero outstanding blocks, 64-slot capacity, and rejection of the 65th registration are tested. ThreadSanitizer passed.

**P1.3 Containers (own, minimal, allocator-aware)**
- [ ] P1.3.1 `Vector`, `SmallVector<N>`, `Span`, `Array`, `StaticVector`
- [ ] P1.3.2 Flat hash map/set (open addressing, SIMD-friendly probing), perfect hash for compile-time keys
- [p] P1.3.3 Slot map / generational arena, sparse set, bitset, ring buffer, intrusive list
- [p] P1.3.4 `StringView`, small-string-optimized `String`, UTF-8/16/32 utilities, interned strings (`Atom`) with hash
- [ ] P1.3.5 `InlineFunction<Sig, N>` (no heap) and `FunctionRef` for callbacks
- [ ] P1.3.6 Benchmarks vs `std::` and `absl`/`robin_hood` to justify each custom container (if not clearly better, use std)

**P1.4 Math**
- [p] P1.4.1 `Vec2/3/4`, `Mat3/4`, `Rect`, `Color` (sRGB/linear, premultiplied alpha), `Transform2D`; ★ double-precision variants (`Vec2d`, `Rectd`, `Transform2Dd`) and origin-relative conversion helpers (ADR-0017)
- [ ] P1.4.2 SIMD abstraction (SSE2/AVX2/NEON), scalar fallback; runtime dispatch where useful
- [p] P1.4.3 Bezier, easing curves, spring solvers, interpolation, color-space conversion (sRGB, linear, Oklab, HDR transfer functions)
- [ ] P1.4.4 Geometry utilities: rect packing (shelf/skyline/guillotine), hit-testing of paths, polygon clipping
- [p] ★ P1.4.5 Rational time/`SampleTime` arithmetic (exact, overflow-checked) for timelines

**P1.5 Concurrency**
- [p] P1.5.1 Atomics wrappers, spinlock/mutex/RW lock, lock-free SPSC/MPSC/MPMC queues
- [ ] P1.5.2 Job system: work-stealing, fibers or task graph, priorities, affinity; parallel-for with grain control; ★ configurable worker count and priority so host real-time threads are not starved
- [ ] P1.5.3 Thread-role annotations (UI, render, worker, ★ realtime) with debug checks; ★ realtime-role code may not allocate, lock, or call into the OS
- [p] P1.5.4 Triple-buffered `FramePacket` exchange primitive
- [p] ★ P1.5.5 Latest-value and SPSC primitives for audio-thread feeds (always-lock-free atomics are required and tested; formal target-specific wait-free guarantees remain unclaimed), with TSan and stress tests

**P1.6 Diagnostics**
- [p] P1.6.1 Logging (compile-time levels, ring buffer, sinks, zero-cost when disabled)
- [p] P1.6.2 Instrumented profiler (scoped zones, GPU timestamps hook, Tracy/Perfetto export)
- [ ] P1.6.3 Counters/metrics registry feeding the in-app inspector

- [p] **P1.7 Utilities:** time (monotonic high-resolution), file I/O (async-capable), path handling (UTF-8 everywhere), CLI parsing for samples, serialization primitives (binary + text), hashing (xxhash-class), UUIDs.

**Tests:** unit + property tests + fuzzing of string/UTF/containers; ASan/UBSan/TSan clean.
**Exit criteria:** all containers benchmarked; zero-allocation guard works; job system scales near-linearly to 8+ cores; ★ realtime-role checks verified by a test.

---

### PHASE 2 — `tgf::platform` (windows, input, OS integration)

**Purpose:** native, correct, low-latency windowing on Windows, Linux (X11 + Wayland), macOS. Not GLFW: we need control of present timing, IME, DPI, multi-window, and embedding. (GLFW/SDL can remain as an optional "bring-up" backend for rapid prototyping.)

**P2.1 Abstraction**
- [ ] P2.1.1 `Window`, `Monitor`, `Surface`, `EventSource`, `Clipboard`, `Cursor`, `Dialog` interfaces
- [ ] P2.1.2 Event loop models: blocking wait (idle = sleep), animation-driven (vsync), external pump (embed into host app loop) ★ and **no-window mode** (render into host-provided surface; ADR-0020)
- [ ] P2.1.3 Timers, wake-up from other threads, high-resolution frame pacing (ADR-0027)
- [ ] ★ P2.1.4 Platform interface is implementable by out-of-tree (console/mobile) backends: documented contract + contract tests (ADR-0021)

**P2.2 Backends**
- [ ] P2.2.1 **Windows:** Win32 + raw input, DirectComposition/DXGI flip-model swapchain, per-monitor-v2 DPI, WM_POINTER (touch/pen), Windows Ink, borderless/custom title bar with snap layouts, dark mode, IME (TSF), accessibility (UI Automation) hooks
- [ ] P2.2.2 **macOS:** Cocoa/AppKit (Objective-C++ isolated), CAMetalLayer/CVDisplayLink, trackpad gestures, Retina, native fullscreen, NSTextInputClient, NSAccessibility
- [ ] P2.2.3 **Linux X11:** XCB, XInput2 (high-res scroll/tablet), XSync frame pacing, XRandR, IBus/Fcitx via XIM/text-input, AT-SPI
- [ ] P2.2.4 **Linux Wayland:** xdg-shell, fractional-scale, text-input-v3, presentation-time, client-side decorations (libdecor), pointer constraints, clipboard/DnD. ★ Wayland cannot position windows globally: docking tear-off, tool windows and tooltips must use xdg-popup/transient rules and **degrade gracefully** (documented behavior matrix)
- [ ] P2.2.5 Optional: GLFW/SDL3 bring-up backend for early development

**P2.3 Input**
- [ ] P2.3.1 Unified event model: pointer (mouse/touch/pen with pressure/tilt), keyboard (physical key + layout-aware key + text), ★ **gamepad (core, not optional — needed for games and focus navigation)**, scroll/gesture (pinch, smooth scroll)
- [ ] P2.3.2 High-frequency input coalescing (e.g., 1000 Hz mice, pen at 200+ Hz) with predicted positions for low latency; ★ raw un-coalesced samples are also delivered to apps that need them (brush engines)
- [ ] P2.3.3 Dead keys, compose, IME composition events (pre-edit with attributes), RTL input
- [ ] P2.3.4 Key mapping tables, modifier handling, global shortcuts opt-in

**P2.4 OS services**
- [ ] P2.4.1 Clipboard (text, rich text, images, custom formats), drag & drop (in/out, file/URL/custom, with preview images)
- [ ] P2.4.2 Native file/folder dialogs, message boxes, notifications (optional), tray icon (optional), native menus (optional bridge)
- [ ] P2.4.3 Multi-window management: tool windows, popups, tooltips, modal stacks, window-level z-order, per-window DPI
- [ ] P2.4.4 Foreign window embedding: parent/child native handles (for plugin GUIs: VST3, CLAP, AU), and exposing TGF as a child of a host window (TGF-as-plugin-GUI); ★ resize negotiation and DPI propagation per plugin format
- [ ] P2.4.5 Cursor system (named + custom bitmap + hide/lock/confine for viewport navigation)
- [ ] P2.4.6 Power/GPU preferences (discrete vs integrated), VRR, HDR monitor detection
- [ ] ★ P2.4.7 Printing/PDF page-setup bridge (for Dorico-class apps; renders through P3.2.13)
- [ ] ★ P2.4.8 Safe-area / fullscreen-exclusive / borderless-fullscreen handling for games

**Tests:** headless "mock platform" for deterministic automated UI tests; per-OS integration tests (CI VMs + a few physical devices).
**Exit criteria:** sample app with multi-window, DnD, IME, mixed-DPI works on all 3 OSes; idle CPU ≈ 0; ★ plugin-GUI embedding demo and no-window host mode demo.

---

### PHASE 3 — `tgf::rhi` + `tgf::render` (GPU backend and 2D renderer)

**Purpose:** an extremely fast, batched 2D renderer with minimal overdraw, plus a thin RHI that makes backends cheap to maintain.

**P3.1 RHI (thin, explicit, modern)**
- [ ] P3.1.1 Core objects: Device, Queue, SwapChain, Buffer, Texture, Sampler, Shader, Pipeline, BindGroup, CommandBuffer, Fence/Semaphore
- [ ] P3.1.2 Backends in order (subject to ADR-0005 / P0.4.9): **Vulkan → D3D12 → Metal**; tier-2 after M4: D3D11, OpenGL 4.3/ES 3.x; **Software (CPU) for tests/fallback**
- [ ] P3.1.3 Memory: sub-allocation (VMA-style), staging ring buffers, persistently mapped upload heaps, bindless textures where available, texture-array atlas fallback
- [ ] P3.1.4 Shader pipeline: author once (Slang/HLSL or GLSL) → SPIR-V / DXIL / MSL via offline compile; pipeline cache on disk; hot-reload in dev
- [ ] P3.1.5 Frames in flight (2–3), GPU timestamps, validation layers toggle, device-lost recovery
- [ ] P3.1.6 Interop: import/export shared textures (DXGI shared handles, `VK_KHR_external_memory`, IOSurface), so app 3D renderers (Vulkan/GL/D3D) can feed TGF viewports with zero copies
- [ ] ★ P3.1.7 **External device adoption:** construct the RHI on a host-owned device/queue/command buffer/render pass (ADR-0020), with explicit synchronization contract and state-restoration rules
- [ ] ★ P3.1.8 Multi-GPU / adapter selection and per-window adapter handling (laptop hybrid graphics, eGPU)

**P3.2 2D renderer**
- [ ] P3.2.1 Display list format: compact, SoA, POD commands (rect, rrect, path fill/stroke, image, text run, gradient, shadow, clip push/pop, layer push/pop, custom callback)
- [ ] P3.2.2 Retained **layer cache**: static subtrees rasterized to textures and recomposited (invalidate on change); ★ VRAM-budgeted with eviction
- [ ] P3.2.3 Batcher: sort by pipeline/texture/clip with z-preserving merge; target < 20 draw calls typical; instanced quads for rects/rounded rects/borders drawn by SDF in the fragment shader (no tessellation for common shapes)
- [ ] P3.2.4 Vector paths: GPU-friendly strategy chosen in P0.4.3 (e.g., tessellation for simple, analytic-coverage / compute for complex); stroker with joins/caps/dashes; anti-aliasing without MSAA cost (analytic edge AA)
- [ ] P3.2.5 Effects: drop shadows, blur (separable/Kawase, downsampled), backdrop blur, glow, masks, blend modes, color transforms; all with budget awareness (auto-disable on weak GPUs)
- [ ] P3.2.6 Clipping: scissor for axis-aligned, stencil/SDF clip for rounded, hierarchical clip caching
- [ ] P3.2.7 Images: atlas manager, mip-mapped, compressed texture formats (BC7/ASTC), async decode (PNG/JPEG/WebP/AVIF/SVG via jobs), nine-patch, icon fonts/SVG-to-atlas
- [ ] P3.2.8 **Damage-driven redraw:** per-window dirty region tracking, scissored rendering, partial present where supported, full redraw fallback
- [ ] P3.2.9 Color management: linear-light blending option, wide-gamut/HDR output paths, per-window color space; ★ ICC + OCIO-style display transform stage (3D LUT) for color-critical apps
- [ ] P3.2.10 Frame graph for render passes (UI layers, blur chains, viewport composition) with automatic resource aliasing
- [ ] P3.2.11 Render thread + frame packet consumption; CPU fallback renderer (tile-based, SIMD) for headless/screenshot tests and driver-bug machines
- [ ] P3.2.12 Debug visualizers: overdraw heatmap, batch coloring, dirty-rect overlay, atlas viewer
- [ ] ★ P3.2.13 **Vector export backends:** display list → PDF / SVG / print (resolution-independent output for scores and layouts)
- [ ] ★ P3.2.14 **Tiled/virtual texture surfaces** (sparse residency, tile streaming, LRU) as a first-class resource for image canvases and huge layer caches
- [ ] ★ P3.2.15 **Render-to-texture and world-space UI:** UI trees rendered to textures or placed in 3D with a camera transform; correct hit-testing via ray/plane mapping (games)
- [ ] ★ P3.2.16 Transform-aware rendering for extreme zoom: camera-relative double→float pipeline (ADR-0017) so strokes/text do not shimmer at 10^6 zoom

**Tests:** golden-image tests per backend with perceptual diff thresholds (★ per-vendor baselines because GPUs differ legitimately); GPU-validation-layer-clean runs; benchmark S2/S9/S10/S12/S14.
**Exit criteria:** 10k rounded-rect widgets at 144 Hz on integrated GPU; idle frame = zero GPU work; viewport interop demo; ★ host-device adoption demo; ★ gigapixel tile demo.

---

### PHASE 4 — `tgf::text` (fonts, shaping, editing)

**Purpose:** pro-quality, fast, internationalized text — the most underestimated part of any GUI framework.

- [ ] P4.1 Font loading: TTF/OTF/WOFF2/variable fonts, system font enumeration + fallback chains, color fonts (COLR/CBDT/SBIX), font cache and memory-mapped fonts
- [ ] P4.2 Shaping: HarfBuzz integration (optional minimal fallback for Latin), ligatures, kerning, complex scripts (Arabic, Indic, Thai, CJK), vertical text (CJK)
- [ ] P4.3 Unicode: normalization, grapheme/word/line breaking (UAX #29, #14), bidi (UAX #9), script itemization, emoji sequences ★ (ICU-class vendored subset, ADR-0023)
- [ ] P4.4 Rasterization & atlas: ★ **hybrid by size (ADR-0006):** hinted coverage bitmaps for small UI sizes, SDF/MSDF or glyph-path rendering for large/zoomed text; subpixel positioning, gamma-correct blending, LCD optional, atlas eviction (LRU), multi-atlas pages. (CPU rasterization lives in `text`; GPU atlas upload lives in `render`.)
- [ ] P4.5 **Shaped-run cache** keyed by (text hash, font, size, features) → geometry reuse; incremental re-shaping on edits
- [ ] P4.6 Layout: paragraph layout (wrap, justify, ellipsis, tab stops, line-height), rich text spans (style runs), inline widgets/icons
- [ ] P4.7 Text editing engine (shared by all text widgets): rope or gap/piece-table buffer, multi-cursor, selection model, undo/redo grouping, IME pre-edit, bidi cursor movement, find/replace hooks, huge-document mode (100 MB+ with lazy layout)
- [ ] P4.8 Music/specialty glyphs: SMuFL (Bravura/Leland) support for score rendering (Dorico-class), icon fonts, custom glyph providers
- [ ] P4.9 Text measurement API with caching (layout depends on it; must be fast and allocation-free in steady state)
- [ ] P4.10 Accessibility text exposure (text ranges, caret, attributes) feeding Phase 9 (★ data model fixed in Phase 5, ADR-0019)
- [ ] ★ P4.11 Syntax-highlighting and token-span hooks for code-editor use (Unreal/Unity script and shader editors) — spans supplied by the app, not a built-in parser
- [ ] ★ P4.12 Font licensing: bundled default fonts (OFL) and a font-fallback policy that guarantees no tofu for supported scripts on all 3 OSes

**Tests:** Unicode conformance suites, shaping golden files, fuzzing of text input; benchmark S4.
**Exit criteria:** 100k visible glyphs scroll smoothly; correct Arabic/Devanagari/CJK + emoji; IME works on 3 OSes; ★ legible 9–11 px text vs OS-native rendering in side-by-side review.

---

### PHASE 5 — `tgf::ui` (the retained UI core)

**Purpose:** the engine room — widget tree, layout, style, events, focus, animation. This is where "best architecture" is won or lost.

**P5.1 Tree storage**
- [ ] P5.1.1 Node store: generational handles, contiguous hot arrays (`parent, first_child, next_sibling, flags, rect, style_id, layout_data` — ★ ≤ 64 B/node total, ADR-0003), cold data in side tables
- [ ] P5.1.2 Component model: widgets are *data + behavior tables* (not deep inheritance); custom widgets register behavior (measure/layout/paint/event/★ **a11y role/state/actions**) via a small trait struct; optional C++ class sugar over it
- [ ] P5.1.3 Tree mutation batching (apply at frame boundary), deterministic ordering, cheap subtree move/reparent, widget pooling and recycling (for virtualization)
- [ ] P5.1.4 Serialization/snapshot of the tree (debugging, tests, hot reload, state restoration)

**P5.2 Invalidation (the secret sauce)**
- [ ] P5.2.1 Separate dirty bits: `STYLE`, `LAYOUT_SELF`, `LAYOUT_CHILDREN`, `PAINT`, `COMPOSITE`, `A11Y`
- [ ] P5.2.2 Upward/downward propagation rules; **layout boundaries** (fixed-size nodes stop propagation)
- [ ] P5.2.3 Per-node paint caching and layer promotion heuristics (animated subtree → own layer)
- [ ] P5.2.4 Damage rect accumulation per window; zero work when no dirty bits are set
- [ ] P5.2.5 Frame scheduler: coalesce input, request-next-frame only on animation/dirty; vsync alignment; ★ per-frame work budget with deferral of low-priority work (real-time safety, goal 9)

**P5.3 Layout engine**
- [ ] P5.3.1 Box model, flex (row/column, wrap, grow/shrink/basis, gaps), grid (tracks, auto-placement, spans), stack/overlay, absolute/anchored, scroll containers; ★ all expressed in **logical start/end** terms, not left/right (ADR-0023)
- [ ] P5.3.2 "Pro" layouts: splitters with min/max/priority, dock layouts, toolbar overflow, timeline/track layouts (fixed row height, huge counts), ruler-aligned layouts
- [ ] P5.3.3 Intrinsic sizing (min/max/preferred) with caching; text-dependent measurement cached
- [ ] P5.3.4 Incremental, parallelizable layout of independent subtrees (job system)
- [ ] P5.3.5 Constraint solver option for complex panels (Cassowary-style, opt-in)
- [ ] P5.3.6 RTL mirroring, DPI-aware snapping, subpixel layout with pixel-snapped paint
- [ ] ★ P5.3.7 Layout determinism contract: identical input → bit-identical layout across platforms/compilers (needed for golden tests and for networked/collaborative UIs)

**P5.4 Style & theming**
- [ ] P5.4.1 Style model: design tokens (color, spacing, radius, typography, motion) → compiled style tables
- [ ] P5.4.2 Selectors/state variants (hover, pressed, focused, disabled, checked, custom states) resolved to flat indices at build time
- [ ] P5.4.3 Theme files (text format with hot reload; binary compiled for release), light/dark/high-contrast, user themes, per-widget overrides
- [ ] P5.4.4 Style transitions integrated with animation (no per-frame string/hash lookups)

**P5.5 Events & input routing**
- [ ] P5.5.1 Hit-testing with spatial acceleration (per-layer rect trees / grids), custom hit shapes, pointer capture, hover tracking; ★ ray-based hit testing for world-space UI (P3.2.15)
- [ ] P5.5.2 Capture/target/bubble phases without per-widget virtual dispatch cost; event handler tables per node-kind
- [ ] P5.5.3 Gesture recognizers: click, double/triple click, drag (threshold), long-press, pinch, pan, fling, pen hover/pressure
- [ ] P5.5.4 Keyboard focus management: focus scopes, tab order, roving focus, focus-visible rules, accelerator routing; ★ **spatial (directional) focus navigation for gamepad/D-pad and TV-style input**
- [ ] P5.5.5 Drag & drop (internal + OS): drag sources/targets, previews, auto-scroll, type negotiation
- [ ] P5.5.6 Modal/popup/tooltip management (z-layers, light-dismiss, anchoring and flipping)

**P5.6 Animation**
- [ ] P5.6.1 Animation system: tweens, springs, keyframes, sequences, interruptible/retargetable; runs on the UI thread, optionally compositor-driven (transform/opacity on render thread)
- [ ] P5.6.2 Frame-time based, vsync aligned; reduced-motion setting respected
- [ ] P5.6.3 Layout animation (FLIP-style) without re-layout every frame

**P5.7 State & data binding**
- [ ] P5.7.1 Reactive primitives (signals/observables) — optional, allocation-free subscription lists
- [ ] P5.7.2 Model/view interfaces for large data (list/tree/table models with change notifications and **virtualization** hooks)
- [ ] P5.7.3 Declarative authoring API (builder/DSL) + immediate-style sugar (ADR-0002) that diffs into retained tree with stable IDs, ★ re-running only on dirty inputs
- [ ] P5.7.4 Optional markup format (`.tgfui`) compiled to C++ or loaded at runtime for tooling/designer
- [ ] ★ P5.7.5 Property-descriptor binding (ADR-0026): generate editors for app-defined structs without RTTI

**P5.8 Commands, actions, undo**
- [ ] P5.8.1 Command/action registry (id, label, icon, shortcut, enabled-state predicate), contexts, command palette backend
- [ ] P5.8.2 Undo/redo framework (command pattern, transactions, merge rules, memory budget, history browser) — ★ document model stays app-owned (ADR-0025)
- [ ] P5.8.3 Shortcut system with user remapping, chords, conflicts detection, per-context scopes, import/export

**★ P5.9 Accessibility core (data model; platform bridges in Phase 9)**
- [ ] ★ P5.9.1 A11y node model (role, name, value, state, actions, relations, text range) as part of the node/behavior tables; dirty-driven updates
- [ ] ★ P5.9.2 Virtualized-collection a11y (expose only realized items plus accurate count/position; scroll-into-view on focus)
- [ ] ★ P5.9.3 Automation/introspection API (stable IDs, query by path/role) shared by a11y and UI testing (P10.5)

**Tests:** headless deterministic UI tests (simulated input + golden tree/pixel snapshots); property tests for layout (no overlap, determinism); benchmark S2/S3/S8/S9.
**Exit criteria:** 100k-node logical tree with 2k live widgets virtualized; single-widget change costs microseconds; idle = zero CPU; ★ every built-in widget exposes a valid a11y node; ★ RTL mirrored demo passes.

---

### PHASE 6 — `tgf::widgets` (standard widget library)

**Purpose:** complete, polished, accessible, themeable widgets built only on the public `ui` API.

- [ ] **P6.1 Basics:** Label, RichText, Icon, Image, Separator, Spacer, Panel/Card, ScrollView (inertia, overscroll, scrollbars with auto-hide), Tooltip, Badge, ProgressBar/Spinner
- [ ] **P6.2 Buttons & toggles:** Button (primary/secondary/ghost/icon), ToggleButton, CheckBox, RadioGroup, Switch, SplitButton, DropdownButton, ButtonGroup
- [ ] **P6.3 Inputs:** TextField, TextArea (code-editor capable), NumberField (drag-to-scrub, units, expression input like `2*3+1`), Slider, RangeSlider, SpinBox, ComboBox/Dropdown, SearchBox with suggestions, DatePicker/TimePicker, MaskedInput
- [ ] **P6.4 Collections:** ListView, TreeView, TableView/DataGrid (column resize/reorder/sort/filter, frozen columns, cell editors), GridView/Thumbnails — all virtualized via the model/view system
- [ ] **P6.5 Navigation:** TabBar (closable, reorderable, tear-off), Menu/MenuBar/ContextMenu (nested, icons, shortcuts, search), Toolbar (overflow), Breadcrumb, StatusBar, Sidebar, Accordion, Stepper
- [ ] **P6.6 Dialogs/overlays:** Modal dialog, Popover, Toast/Notification, Command palette, Color/Font/File pickers (custom + native bridge)
- [ ] **P6.7 Visualization basics:** Line/area/bar chart widget (GPU-batched), sparklines, level meter, gauge
- [ ] **P6.8 Quality bar for each widget:** keyboard operable, screen-reader roles/states, RTL, DPI, high-contrast, touch targets, ★ gamepad navigable, localization, theming tokens, animations respecting reduced motion, unit + golden + a11y tests, benchmark if it can scale
- [ ] **★ P6.9 Game-UI widgets:** gamepad-navigable menus, radial menu, hold-to-confirm button, input-prompt glyph icons (per-device), focus-ring styles for controllers, safe-area container

**Exit criteria:** "widget gallery" sample with every widget in light/dark/high-contrast and ★ LTR/RTL; all pass a11y checker; per-widget memory within budget.

---

### PHASE 7 — `tgf::pro` (professional-application components)

**Purpose:** the differentiator. Make building After Effects/Blender/DAW/Photoshop/engine-editor-class UIs *easy and fast*. Each component is an independent module with its own benchmark and sample.

**P7.1 Docking & workspace system**
- [ ] P7.1.1 Dock tree (split/tabs/floating), drag-to-dock with live preview, tear-off windows across monitors ★ (with Wayland fallback behavior, P2.2.4), auto-hide panels
- [ ] P7.1.2 Workspace save/restore/versioning (JSON + binary), per-user and per-project layouts, resets, presets (Edit, Animate, Mix, Compose…); ★ forward/backward-compatible layout migration when panels are added/removed
- [ ] P7.1.3 Panel API: lifecycle, titles, icons, min sizes, serialization hooks, multi-instance panels
- [ ] P7.1.4 Maximize/fullscreen panel, layout-lock, keyboard panel navigation, tab overflow

**P7.2 Viewport widget (3D/video/canvas embedding)**
- [ ] P7.2.1 `ViewportSurface`: app renders to a texture/native surface; TGF composites (zero-copy via RHI interop)
- [ ] P7.2.2 Input forwarding with capture (mouse lock/wrap for orbit/pan), high-rate pointer events, pen/tablet pressure
- [ ] P7.2.3 Overlay layer API (gizmos, rulers, safe areas, HUD) drawn by TGF above the viewport
- [ ] P7.2.4 Resize without flicker, frame-pacing contract with the app's render loop, HDR/color space tagging
- [ ] ★ P7.2.5 Multi-viewport (quad view, linked cameras) with independent frame pacing and a shared GPU budget
- [ ] ★ P7.2.6 Play-in-editor viewport mode: focus/capture handoff between editor UI and running game input, safe escape chord

**P7.3 Timeline & sequencer (After Effects / Premiere / Cubase / FL Studio)**
- [ ] P7.3.1 Time ruler (timecode/frames/bars-beats/seconds), zoom/pan with smooth inertia, snapping, markers, regions, loop range
- [ ] P7.3.2 Track/clip model: 100k+ clips with virtualization, clip rendering (waveforms/thumbnails/automation) via cached GPU layers; ★ positions stored as `SampleTime`/rational (ADR-0017)
- [ ] P7.3.3 Interaction: drag/trim/slip/slide/ripple, multi-select/box-select, razor, lanes, folders/groups, track heights, solo/mute/arm controls
- [ ] P7.3.4 Keyframe/automation lanes with Bezier handles, curve editing, per-property tracks (After Effects layer-property style)
- [ ] P7.3.5 Playhead with sample-accurate scrubbing and external clock sync (audio-thread-safe lock-free reads, ADR-0022)
- [ ] P7.3.6 Waveform renderer (multi-resolution peaks mipmaps, streaming load), video thumbnail strips (async)
- [ ] ★ P7.3.7 Tempo-map / time-signature aware ruler (non-linear time ↔ position mapping) and timecode drop-frame support

**P7.4 Node graph editor (Blender / Cinema 4D / Houdini / Nuke / Unreal Blueprint / Material graph style)**
- [ ] P7.4.1 Nodes, sockets, typed links, groups/frames/reroutes, minimap, auto-layout, zoom to 5–6 orders of magnitude (★ double-domain coordinates, ADR-0017), LOD (hide detail when small)
- [ ] P7.4.2 GPU-instanced node and link rendering (curves/splines/orthogonal), link hover/cut/insert, snapping, 10k+ nodes fluid
- [ ] P7.4.3 Embeddable widgets inside nodes (sliders, color, previews) with virtualization when off-screen
- [ ] P7.4.4 Selection, copy/paste with link retention, undo integration, search-to-add menu
- [ ] ★ P7.4.5 Execution-flow visualization (animated wires, breakpoints, per-node timing badges) for blueprint/shader/compositing graphs

**P7.5 Music/audio widgets (Cubase / FL Studio / Dorico)**
- [ ] P7.5.1 Piano roll (note editing, velocity lane, scale highlighting, ghost notes, quantize UI, 100k notes)
- [ ] P7.5.2 Mixer strips: faders (log/dB mapping), pan, meters (peak/RMS/LUFS with ballistics; lock-free audio-thread feeds), send slots, insert racks, channel routing views
- [ ] P7.5.3 Knobs, XY pads, step sequencer, envelope/ADSR editor, EQ curve display (FFT spectrum overlay, draggable bands), spectrogram, oscilloscope, tuner
- [ ] P7.5.4 Plugin editor host panel (embed VST3/CLAP/AU native windows; resize negotiation)
- [ ] P7.5.5 **Music notation engine hooks** (Dorico-class): SMuFL glyph rendering, staff/score canvas with large-scale zoom, symbol placement APIs, page-based layout viewport (the engraving logic itself is app domain; TGF supplies fast canvas, text, glyph and hit-testing primitives), ★ print/PDF export via P3.2.13
- [ ] ★ P7.5.6 Parameter-automation UX primitives: touch/latch/write modes, parameter-gesture begin/end events for host undo, MIDI-learn hooks

**P7.6 Property & outliner systems**
- [ ] P7.6.1 Property grid / inspector (reflected via ADR-0026 descriptors or manual properties, multi-edit, mixed values, units, reset, animated-property indicators/keyframe buttons)
- [ ] P7.6.2 Outliner/hierarchy tree (drag-reorder, visibility/lock columns, filtering, 1M items virtualized)
- [ ] P7.6.3 Asset browser (thumbnail grid with async loading, tags, search, preview scrubbing)

- [ ] **P7.7 Graph/curve/color tools:** curve editor (Bezier/spline/graph editor with tangent handles), gradient editor, color picker suite (HSV/HSL/Oklab/ICC-aware, eyedropper, palettes, HDR), LUT/histogram/vectorscope widgets, ruler/guide/grid canvas, infinite 2D canvas (pan/zoom, rulers, snapping)

- [ ] **P7.8 Pro-interaction polish:** scrub-number fields everywhere, modifier-key behaviors, tablet/pen support, precision mode (Shift = fine), cursor wrap during drags, tooltips with shortcuts, status-bar hints, full keyboard-only operation, customizable UI scale and density

**★ P7.9 Game/DCC editor components (Unreal / Unity class)**
- [ ] ★ P7.9.1 Details panel generator (ADR-0026) with categories, search, per-property override/reset, array/map/struct editors, asset/object reference pickers
- [ ] ★ P7.9.2 Scene/world outliner (hierarchy + filters + multi-selection + drag/drop reparent) built on P7.6.2
- [ ] ★ P7.9.3 Content browser (virtualized thumbnails, folders, collections, async previews, drag to viewport)
- [ ] ★ P7.9.4 Console/log panel (millions of lines, filters, severity colors, command input with completion, virtualized)
- [ ] ★ P7.9.5 **Profiler flame graph / timeline widget** (5M+ events, zoom to nanoseconds, aggregation LOD, GPU/CPU tracks) — also reused by P10.2
- [ ] ★ P7.9.6 Curve/animation sequencer reuse (cinematic tracks, animation state-machine graph via P7.4)
- [ ] ★ P7.9.7 Hot-reload-friendly panels (survive app-side DLL reload; ADR-0012 allocator rules)

**★ P7.10 Image/paint canvas (Photoshop / Krita class)**
- [ ] ★ P7.10.1 `ImageCanvas`: tiled/sparse gigapixel display (P3.2.14), pan/zoom 1:1 → 3200%, pixel grid, rulers, guides, nearest/bicubic resampling, rotation
- [ ] ★ P7.10.2 Color-managed display path (P3.2.9), soft-proof overlay, HDR/wide-gamut preview, per-document color space
- [ ] ★ P7.10.3 Stroke input pipeline: un-coalesced pen samples, prediction, pressure/tilt/rotation curves, latency-mode rendering of the in-progress stroke overlay (app owns the brush engine)
- [ ] ★ P7.10.4 Layer panel (10k layers virtualized, thumbnails, blend-mode UI, groups, masks, drag reorder), history panel, navigator, histogram/info panels
- [ ] ★ P7.10.5 Selection/transform overlays (marching ants, transform handles, lasso/path editing) drawn by TGF over the canvas

**Tests:** each component has stress tests (S5, S6, S7, S8, S12, S13) and golden interaction scripts.
**Exit criteria:** reference demos — *"Mini After Effects timeline"*, *"Mini Blender node editor + viewport"*, *"Mini DAW (arrange + mixer + piano roll)"*, ★ *"Mini Photoshop (gigapixel canvas + layers + pen)"*, ★ *"Mini engine editor (outliner + details + console + profiler + play viewport)"* — all running at display refresh rate with budgets met.

---

### PHASE 8 — Application framework glue (small, optional)

- [ ] P8.1 `tgf::app`: app lifecycle, window manager, settings persistence (preferences, window state), recent files, single-instance, crash-safe autosave hooks
- [ ] P8.2 Resource system: asset packing (fonts, icons, shaders, themes) into one memory-mappable archive, compression (zstd/LZ4), embed or load from disk, hot reload in dev
- [ ] P8.3 Localization: message catalogs (ICU MessageFormat-like plural/gender), runtime language switch, pseudo-localization test mode, number/date/unit formatting
- [ ] P8.4 Standard "Preferences" UI scaffolding, keymap editor, theme editor
- [ ] ★ P8.5 **Runtime / in-game mode:** `tgf::host` adapters for engines (render-pass integration, input routing from engine, asset loading through engine VFS), stripped runtime build profile (no inspector/tools, minimal binary), console/mobile-ready platform contract (ADR-0021), safe-area and per-device input prompts
- [ ] ★ P8.6 `tgf::host` plugin-GUI adapters: VST3, CLAP, AU (editor lifecycle, resize, host-driven idle, DPI)
- [ ] ★ P8.7 Update/crash/telemetry **hooks only** (opt-in, privacy-preserving); no mandatory network code in the framework

---

### PHASE 9 — Accessibility, internationalization, color, quality of experience

- [ ] P9.1 Accessibility **platform bridges** on the P5.9 model: **UI Automation (Win), NSAccessibility (macOS), AT-SPI (Linux)**
- [ ] P9.2 Screen-reader, keyboard-only, high-contrast, large-text, reduced-motion modes; automated a11y audits in CI; ★ manual testing with NVDA, JAWS, VoiceOver, Orca recorded per release
- [ ] P9.3 Full i18n: RTL layout mirroring, bidi in all widgets, CJK input and line breaking, locale-aware sorting/formatting (★ verification of ADR-0023, not first implementation)
- [ ] P9.4 Color management and HDR: per-monitor ICC awareness for color-critical tools (video/graphics), HDR UI composition rules, wide-gamut color pickers
- [ ] P9.5 Touch & pen UI mode: larger hit targets, gestures, on-screen keyboard integration
- [ ] P9.6 Resilience: GPU device-lost recovery, graceful fallback chain (preferred API → alternate API → software), safe-mode launch, crash reports with UI-state dump
- [ ] ★ P9.7 Accessibility for custom pro canvases: timeline/node-graph/piano-roll expose an alternative semantic tree (tracks, clips, nodes, notes) and keyboard-only editing paths

---

### PHASE 10 — Developer tooling (what makes engineers love TGF)

- [ ] P10.1 **Inspector** (in-app overlay): tree view, live property edit, layout bounds, dirty-rect visualization, event log, style resolution trace
- [ ] P10.2 **Profiler UI**: frame timeline (CPU zones + GPU timestamps), allocation counters, batch/draw-call stats, memory by tag, regression compare against saved capture (★ reuses P7.9.5)
- [ ] P10.3 **Hot reload**: themes, layouts/markup, shaders, and (opt-in) widget code via plugin DLL reload
- [ ] P10.4 **Visual designer** (stretch): drag/drop layout editor producing `.tgfui`
- [ ] P10.5 **Test tooling:** headless runner, input record/replay, golden image management with review UI, deterministic time/clock, fuzz harnesses; ★ out-of-process automation protocol (built on P5.9.3) for end-to-end tests of shipped apps
- [ ] P10.6 Debug assertions with actionable messages (e.g., "layout cycle at node X; path: …"), thread-role violations, hot-path allocation reports
- [ ] P10.7 IDE support: natvis/lldb pretty-printers, clangd-friendly build, project templates (`tgf-new`) and CLI scaffolding tool
- [ ] ★ P10.8 Remote inspector/profiler (attach to a running app or a game on another machine/device)

---

### PHASE 11 — Bindings, ABI, plugin ecosystem

- [ ] P11.1 Stable **C API** (`tgf_c.h`): opaque handles, versioned structs, explicit allocator hooks; ABI-compat tests across versions
- [ ] P11.2 Bindings (community-friendly generation from a single IDL): Python, Rust, C#, Lua/JS (for scripting UIs) — optional and outside core; ★ C# binding is prioritized for Unity-style tooling
- [ ] P11.3 Plugin system for TGF itself: custom widgets/backends/themes as shared libraries with versioned interface negotiation
- [ ] P11.4 Hosting: guidelines + samples for being embedded inside DAW hosts (as plugin GUI) and for embedding other plugin GUIs
- [ ] P11.5 WebGPU/WASM backend (stretch, post-1.0) for web demos and docs playground
- [ ] P11.6 Mobile/tablet (iOS/Android) and console feasibility study (stretch, post-1.0; architecture preserved by ADR-0021)

---

### PHASE 12 — Hardening, performance engineering, security  *(runs continuously from Phase 1; gates tighten each phase)*

- [ ] P12.1 CI gates: unit, integration, golden, a11y, benchmark regression (statistical, ★ see §2), binary-size budget, memory budget, startup budget, ★ build-time budget
- [ ] P12.2 Sanitizers (ASan/UBSan/TSan/MSan), static analysis (clang-tidy, MSVC /analyze, CodeQL), fuzzing (OSS-Fuzz) on text, markup, image decoders, clipboard/DnD parsers, ★ theme/workspace/font parsers (ADR-0024)
- [ ] P12.3 Driver matrix testing (NVIDIA, AMD, Intel, Apple, Mesa; old and new); workaround database with capability flags
- [ ] P12.4 Long-run soak tests (24–72 h, leak/fragmentation/handle exhaustion)
- [ ] P12.5 Performance passes: false-sharing audit, cache-miss profiling (perf/VTune/Instruments), PGO/LTO builds, SIMD kernels for hot loops, data-layout tuning, shader optimization, startup trimming (lazy init, mmap resources)
- [ ] P12.6 Security: sandbox-safe parsing, bounds-checked data paths, supply-chain (SBOM, pinned deps, reproducible builds, signed releases)
- [ ] P12.7 API stability policy (semver, deprecation windows), ABI checks for the C layer
- [ ] ★ P12.8 Real-time-safety audit: automated detection of allocations/locks on realtime-role threads, priority-inversion tests with a real audio callback
- [ ] ★ P12.9 Numeric robustness tests: extreme zoom/scroll/time values, NaN/Inf propagation guards, overflow checks on `SampleTime`
- [ ] ★ P12.10 Accessibility regression suite on real screen readers (scheduled)

---

### PHASE 13 — Documentation, samples, community, release

- [ ] P13.1 Docs site: concepts (architecture, frame pipeline, invalidation, threading), tutorials, API reference (generated), cookbook, performance guide, migration guides (from Qt, ImGui, wxWidgets, ★ JUCE)
- [ ] P13.2 **Architecture handbook for future engineers:** module map, dependency rules, "how to add a backend / widget / layout / effect" step-by-step, ADR index, glossary
- [ ] P13.3 Samples: hello window, widget gallery, text editor, file browser, node editor, timeline, mini DAW, mini 3D tool, plugin-hosted GUI, ★ mini Photoshop, ★ engine-editor, ★ in-game UI demo with gamepad
- [ ] P13.4 Public benchmark site (reproducible, scripts included) comparing TGF vs competitors — updated each release
- [ ] P13.5 Governance: roadmap process (RFCs), maintainers, release cadence (e.g., quarterly), LTS policy, security disclosure policy
- [ ] P13.6 ★ Releases (aligned with §6, resolves the original alpha/beta/milestone mismatch): **alpha = M3** (after Phase 5 + core Phase 6), **beta = M4** (after Phase 7), **RC = M5** (Phases 8–12 gates green), **1.0.0 = M6** (Phase 13 complete and §10 criteria met)
- [ ] P13.7 Showcase: ship a real TASIMAS application built on TGF (dogfooding), publish a case study
- [ ] ★ P13.8 Release engineering: signed binaries/packages (vcpkg/Conan/system packages), reproducible builds, versioned docs, migration notes, changelog automation
- [ ] ★ P13.9 External review before 1.0: independent API review by at least two pro-app developers outside the core team; independent security and accessibility reviews

---

## 6. Milestones, dependency order, schedule

### 6.1 Dependency order

```
P0 ─► P1 ─► P2 ─┬─► P3 ─► P4 ─► P5 ─► P6 ─► P7 ─► P13 (1.0)
                │                │       │       │
                └── (mock platform│       │       └► P11
                     for early UI │       ├► P8
                     tests)       │       ├► P9   (data model P5.9 earlier ★)
                                  │       └► P10  (starts in P5, grows continuously)
                                  └► P5.9 accessibility data model ★
P12 runs continuously from P1 onward; its gates tighten each phase.
```

★ Parallel tracks (to avoid a strictly serial multi-year chain, F-16): Track A core/platform/rhi, Track B text (can start with CPU-only work during P1/P2 since `text` depends only on `core`), Track C tooling/benchmarks/CI, Track D docs. P4 (CPU text) overlaps P2/P3; only the GPU atlas upload waits for P3.

| Milestone | Contents | Proof |
|---|---|---|
| M0 "Evidence" | P0 complete | Tier-A competitor benchmark report, spikes, ADRs |
| M1 "Window + Triangle" | P1 + P2 + minimal P3 | Multi-window, 144 Hz, idle ≈ 0% CPU, ★ host-device adoption proof |
| M2 "Pixels" | P3 + P4 | Fast text + rounded rect batching demo, ★ text-quality review |
| M3 "Alpha" | P5 + core P6 | Widget gallery, inspector, hot reload, ★ a11y data model, RTL demo |
| M4 "Pro Beta" | P7 | Mini-AE, Mini-Blender, Mini-DAW, ★ Mini-Photoshop, ★ Mini engine editor meet budgets |
| M5 "Release Candidate" | P8–P12 | All CI gates green, a11y audits pass on real screen readers |
| M6 "1.0.0" | P13 + §10 | Public benchmarks, docs, showcase app, external reviews |

### 6.2 ★ Effort estimates (the original plan had none; F-16)

These are **planning ranges in person-months for experienced engineers**, to be re-baselined at the end of Phase 0 (P0.5) using spike results. They show why scope control (§1.2, ADR-0005 tiering) matters.

| Phase | Person-months | Notes |
|---|---|---|
| P0 | 6–10 | Benchmark harness dominates |
| P1 | 8–12 | |
| P2 | 18–30 | Three OS backends + IME + embedding |
| P3 | 24–40 | Three RHI backends + renderer |
| P4 | 24–36 | Text + editing engine |
| P5 | 36–60 | Core of the product |
| P6 | 24–36 | |
| P7 | 48–90 | Largest; incl. P7.9, P7.10 |
| P8 | 8–14 | Incl. host adapters |
| P9 | 12–20 | Bridges + audits |
| P10 | 12–20 | |
| P11 | 8–14 | |
| P12 | 20+ | Continuous |
| P13 | 10–16 | |
| **Total** | **≈ 260–420** | ≈ 3–4 years for a team of 7–10; **not achievable solo** |

**Scope-control levers if resources are short (in order):** (1) ship fewer pro components in 1.0 (keep timeline, node graph, docking, viewport, property grid first); (2) tier-2 backends and mobile/console stay post-1.0; (3) Wayland polish after X11; (4) bindings other than C and C# post-1.0. Never cut: accessibility data model, i18n model, numeric model, host integration, tests/benchmarks.

---

## 7. Engineering rules (non-negotiable)

1. **No allocations in the steady-state frame loop.** Use frame arenas and pools; the guard asserts it (DoD #4).
2. ★ **No per-node dynamic dispatch in hot loops.** Dispatch by node *kind* in batches (table dispatch); an indirect call per kind-batch is fine, per node per frame is not. (The original wording banned all virtual calls while P5.1.2 itself uses behavior tables — reworded for consistency, F-04.)
3. **Data first:** hot data contiguous and small; cold data out of line; handles not pointers.
4. **Dirty-driven everything:** if nothing changed, nothing runs. Never poll.
5. **One owner per thread-affine object;** cross-thread communication only through queues/packets.
6. **Public API ≠ internal API:** `include/tgf/` is the only public surface; internals in `src/`, enforced by CI.
7. **Same API for built-in and custom widgets.**
8. **Every optimization has a benchmark; every benchmark has a baseline.**
9. **Prefer simple + measured to clever + assumed.** Custom containers only when they win in benchmarks.
10. **Every irreversible decision has an ADR.**
11. **Defaults are fast and accessible;** fancy effects are opt-in and budget-aware.
12. **Docs are part of the feature.**
13. ★ **Realtime threads are sacred:** UI never blocks them and they never block UI (ADR-0022); UI work per frame is bounded and deferrable.
14. ★ **Domain coordinates are never `float`** (ADR-0017); floats are for screen-space after the camera-relative transform.
15. ★ **Accessibility, RTL and DPI are part of "done"** for every widget, not a later pass (DoD #7).
16. ★ **Untrusted input everywhere** (ADR-0024): every parser has limits and a fuzz target.
17. ★ **Host-neutral:** no code may assume TGF owns the window, the device, the main loop, or `main()` (ADR-0020).

---

## 8. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Scope explosion (a framework this big can swallow years) | Never ships | Strict phases, vertical slices, reference demos as the success metric; ship alpha at M3; ★ scope-control levers (§6.2) |
| ★ Team capacity (≈ 260–420 person-months vs. solo/small team) | Stall | Honest estimates, open contribution model early, funding/sponsorship plan, prioritize reference app (§9) |
| Text/IME/bidi/a11y complexity | Poor international usability | Start text early (P4), use HarfBuzz/ICU-class libraries, conformance suites, a11y/i18n models fixed in Phase 5 |
| GPU driver inconsistencies | Rendering bugs | RHI thin and testable, software fallback, driver matrix, capability flags |
| ★ RHI maintenance cost (3 tier-1 backends) | Slows everything | P0.4.9 build-vs-adopt spike; tier-2 deferred |
| Premature custom everything | Wasted time | Benchmark-gate custom containers; use proven libs (HarfBuzz, FreeType, VMA) where they win |
| Retained-tree complexity vs. ease of use | Adoption friction | Immediate-style authoring sugar (ADR-0002), excellent samples |
| Cross-platform divergence (Wayland/X11/macOS quirks) | Platform bugs | Platform abstraction contract tests, mock platform, CI on real OSes, documented Wayland degrade matrix |
| Solo-maintainer bus factor | Project stall | Architecture handbook, ADRs, tests, open contribution model early |
| "Fastest" claim not demonstrated | Credibility | Public reproducible benchmarks from Phase 0 onward; fairness statement |
| ★ Float-precision failures in huge domains | Jitter, wrong sample positions | ADR-0017, P0.4.11 spike, S15, P12.9 |
| ★ Pipelining adds a frame of latency | Pen/viewport feels laggy | Latency mode (ADR-0008), P0.4.7 measurement |
| ★ Host-integration impossible after RHI freeze | Unusable in engines/DAWs | ADR-0020, P0.4.10 spike before RHI freeze, P3.1.7 |
| ★ Accessibility/i18n retrofitted late | Rewrite of widget API | ADR-0019/0023, P5.9, DoD #7 |
| ★ Third-party license conflicts (FreeType GPL option, fonts, codecs) | Legal risk to "free/open" goal | ADR-0016, SBOM gate P0.1.8, DoD #8 |
| ★ CI noise hides regressions / false alarms | Gate ignored | Dedicated runners, statistics, noise floor in P0.3 |
| ★ Build times balloon | Dev velocity dies | ADR-0015 budget, P0.1.9 |
| ★ Console/mobile NDAs prevent public backends | Fragmented codebase | ADR-0021 out-of-tree backend contract |

---

## 9. ★ Decisions (the original "open questions" resolved with defaults; revisit only via ADR)

Each has a **default** so Phase 0 is not blocked; the owner may override before ADR acceptance.

1. **ImGui-derived fork:** clean-room core; fork kept only as reference and compatibility test bed. *(default accepted)*
2. **Backend order:** Vulkan first on all desktop OSes (fastest path to M1 across platforms), then D3D12 on Windows, then Metal on macOS, unless P0.4.9 selects an adopted RHI.
3. **Minimum baseline:** Windows 10 22H2+, macOS 12+, Linux with Vulkan 1.1+ (Mesa 22+), D3D12 FL11_0 (Windows), Metal 2. OpenGL 4.3 is tier-2.
4. **Third-party policy:** HarfBuzz, FreeType (FTL), VMA, zstd allowed as required deps, **vendored and wrapped behind interfaces**, pinned and in the SBOM.
5. **License:** Apache-2.0 (ADR-0016).
6. **First reference app that drives priorities:** a **timeline** (shared by video, animation and DAW use) followed by the **node editor**; the DAW mixer/piano roll and the image canvas follow. Rationale: timeline + docking + property grid exercises the largest number of shared subsystems.
7. **Mobile/web/console:** explicitly out of scope for 1.0 *delivery*; architecture-preserved (ADR-0021).
8. **Governance:** solo-led with RFCs now; open the core team and move to maintainer-based governance at M1 (when the architecture is demonstrable).

---

## 10. ★ TGF 1.0.0 release criteria (the definition of "professional 1.0")

TGF is released as **1.0.0** only when **all** of the following are true:

**Product**
1. Tier-1 platforms (Windows, Linux X11+Wayland, macOS) pass the full CI matrix and the real-hardware test list.
2. Tier-1 renderer backends (Vulkan, D3D12, Metal, per ADR-0005) plus the software renderer pass golden tests; driver matrix (P12.3) has no open blocker.
3. All five reference demos (timeline, node editor+viewport, DAW, image canvas, engine editor) run at display refresh rate within the §2 budgets.
4. Host-integration modes (a)/(b)/(c) of ADR-0020 are demonstrated: standalone, engine-hosted, plugin-GUI-hosted.
5. In-game runtime profile ships with gamepad navigation and world-space UI.

**Quality**
6. Zero known crash/memory-safety bugs; sanitizer, static-analysis and fuzz gates green; ≥ 72 h soak passes.
7. Accessibility verified on NVDA/JAWS, VoiceOver, Orca; RTL, CJK IME and mixed-DPI verified.
8. Performance budgets in §2 are met and published with reproducible scripts; no tracked metric regressed > 3% (statistical) since RC.

**API & ecosystem**
9. Public C++ API and C ABI reviewed externally (P13.9) and frozen under semver; deprecation policy active.
10. Docs, architecture handbook, migration guides and samples complete; all public APIs have examples.
11. Signed, reproducible release artifacts with SBOM and license audit clean.
12. A real TASIMAS application built on TGF is shipped (dogfooding) with a published case study.

---


## 11. Implementation governance and change control

### 11.1 Task status rules

Use `[x]` only when the task's Definition of Done is met and evidence is linked from its issue/commit or relevant test report. Use `[p]` when some implementation or deliverable exists but the full task or its Definition of Done remains incomplete. Use `[ ]` when no implementation evidence exists or a required deliverable has not been produced. These markers describe completion, not whether someone is actively working on the task; ownership and active work belong in the issue/PR tracker.

A task is not done because:

- The code compiles on one machine.
- A screenshot shows a widget rendering.
- A backend works only on one GPU/driver.
- A test is written but not run in CI.
- A benchmark result has no reproducible scenario, hardware profile, or baseline.
- A feature works in standalone mode but fails in host-owned-device or host-pumped mode where that mode applies.

Use `[!]` for a real blocker, and include the blocker and unblock condition. Use `[?]` for an unresolved decision and link the ADR/RFC that will resolve it.

### 11.2 Change-control rules

1. Changes to ADR decisions require a new ADR revision or superseding ADR. Do not silently edit a decision after dependent code has shipped.
2. Changes to module dependencies require updating the dependency table, CMake target graph, and CI dependency checker together.
3. Changes to public APIs require API review, migration notes, and tests proving ownership/threading contracts.
4. Changes to performance targets require benchmark evidence and an explicit explanation; targets must not be weakened only to make CI green.
5. Moving a feature between 1.0 and post-1.0 requires an RFC/ADR and an update to the product matrix, milestone table, demo plan, and release criteria.
6. Adding a third-party library requires license review, version pin, security review, build impact measurement, and SBOM update before merge.
7. Platform-specific workarounds must be capability-gated and documented; do not scatter OS or driver checks throughout widgets.

### 11.3 Task completion record

Use this compact record in the issue/PR that closes a major task:

```text
Task ID:
Owner:
Scope:
Public API changed: yes/no (link)
ADR/RFC: none or ID
Tests: unit / integration / golden / accessibility / fuzz / sanitizer
Platforms and compiler versions tested:
Backends and GPU/driver versions tested:
Performance baseline and result:
Allocation/blocking/thread-affinity verification:
Accessibility / RTL / DPI / input-mode verification:
Third-party license/SBOM impact:
Known limitations:
Documentation and sample:
Reviewer / self-review evidence:
```

### 11.4 Release-blocker classification

- **Blocker:** data loss, exploitable memory safety issue, reproducible crash in a supported configuration, broken ABI/API promise, deadlock or audio/render real-time interference, inaccessible core workflow, or a release criterion failure.
- **Critical:** major feature unusable on a tier-1 platform/backend, severe performance regression, serious input/text/layout correctness issue, or missing host integration needed for a reference demo.
- **Major:** important feature incomplete with a viable workaround; significant but bounded UI, accessibility, or platform defect.
- **Minor:** cosmetic or low-impact issue that does not undermine a core workflow.

No open blocker is allowed at 1.0. Critical issues require a documented disposition and must be closed or explicitly excluded by a scope decision before RC.

---

## 12. Final artifact checklist

The 1.0 release is a source-and-binary deliverable, not just a successful local build. The release candidate must contain:

- [p] Source repository with reproducible CMake configuration and all required source/dependency license notices.
- [p] Public C++ headers and stable C ABI headers, with API/ABI compatibility reports.
- [ ] Built libraries for the supported configuration matrix, with debug symbols separated where appropriate.
- [p] CMake package config and exported namespaced targets for downstream projects.
- [ ] Runtime assets required by TGF (fonts, shader blobs, icons, theme defaults) with license metadata.
- [ ] Platform backend artifacts and a capability/support matrix.
- [ ] Software renderer/test backend where required by the configured build profile.
- [p] Samples and reference applications proving standalone, embedded, host-pumped, and game-runtime modes.
- [p] Unit, integration, accessibility, golden-image, fuzz, sanitizer, soak, and benchmark reports.
- [p] API reference, architecture handbook, tutorials, cookbooks, migration notes, changelog, and release notes.
- [ ] SBOM, third-party notices, security disclosure contact, reproducible-build instructions, and signed release artifacts.
- [ ] Known-issues document and supported-platform/backend matrix for the exact `1.0.0` tag.

---

## Appendix A — Audit log of this revision (issues found and where they were fixed)

| ID | Issue found in the original plan | Fix |
|---|---|---|
| F-01 | No explicit "1.0.0 done" definition; milestone and release names disagreed (alpha after P5 vs M3 "core P6"; 1.0 after P12 vs M6 P13) | §10 criteria; P13.6 aligned to M3–M6 |
| F-02 | ADR 0017 used `float` for layout/coordinates: breaks timelines (10 h @ 192 kHz > 2^24 samples), 10^6 zoom canvases, gigapixel images | ADR-0017 rewritten (double/int64 domain + camera-relative float), P0.4.11, P1.4.1/1.4.5, P3.2.16, S15, P12.9 |
| F-03 | Budgets lacked measurement conditions; RSS/binary targets ignored GPU driver memory and HarfBuzz/FreeType size | §2 rewritten with conditions, separate driver accounting, per-configuration binary size; statistical CI gating |
| F-04 | Internal inconsistencies: 64 B/widget vs. node field list; "no virtual calls" vs. behavior-table dispatch; "0 allocs" vs. caches/pools | Per-node hot budget split (ADR-0003); rule 2 reworded; steady-state definition (DoD #4) |
| F-05 | Accessibility, i18n/RTL and DPI were late phases (P9) though they dictate widget and layout APIs; layout used left/right | ADR-0019/0023, P5.9, logical start/end layout (P5.3.1), DoD #7, P9 reframed as bridges/verification |
| F-06 | Six RHI backends (Vulkan, D3D12, D3D11, Metal, GL, software) is unsustainable | ADR-0005 tiering; P0.4.9 build-vs-adopt spike; P3.1.2 reordered |
| F-07 | Text rendering via SDF/MSDF only: poor small-text quality | ADR-0006 hybrid by size; P0.4.4, P4.4 updated |
| F-08 | Render-thread pipeline contradicts the ≤ 1 frame latency target | Latency mode in ADR-0008, §2 latency row, P0.4.7 |
| F-09 | No way to run inside Unreal/Unity-style engines, game overlays, or plugin GUIs (host owns device/loop) | ADR-0020, P0.4.10, P2.1.2 no-window mode, P3.1.7, P8.5/8.6, `tgf::host` |
| F-10 | Games, mobile, consoles, gamepads excluded or optional although targets include games | Goal 8, ADR-0021, gamepad in core (P2.3.1), directional focus (P5.5.4), world-space UI (P3.2.15), P6.9, P8.5 |
| F-11 | Missing Unreal/Unity-class editor components (details panel, content browser, console, flame graph, play-in-editor) | P7.9, P7.2.5/7.2.6, ADR-0026 |
| F-12 | Layer diagram ambiguous (text vs render atlases; rhi vs platform surfaces) | Explicit dependency table (§4), P0.1.6 uses it |
| F-13 | Benchmark matrix (9 frameworks × 11 scenarios) impractical; JUCE (audio baseline) absent; no fairness rules | Tiered baselines (P0.3.4), JUCE added, fairness statement P0.3.6 |
| F-14 | Audio/real-time threading only implied | ADR-0022, goal 9, P1.5.3/1.5.5, P0.4.13, P12.8, rule 13 |
| F-15 | Untrusted-input handling scattered | ADR-0024, P12.2 extended, rule 16 |
| F-16 | No effort estimates, staffing, parallel tracks or scope levers | §6.2, §6.1 parallel tracks, risk "team capacity" |
| F-17 | Open questions left undecided (license, backends, baseline, first app) | §9 defaults; ADR-0016 Apache-2.0 |
| F-18 | Missing Photoshop-class needs (gigapixel tiled canvas, color-managed display, pen latency/prediction) | P7.10, P3.2.14, P3.2.9, P2.3.2, S12 |
| F-19 | Missing print/PDF/SVG export (Dorico-class) | P3.2.13, P2.4.7, P7.5.5 |
| F-20 | ADR-0001 `-fno-rtti/-fno-exceptions` risked breaking user code and left OOM undefined | ADR-0001 rewritten, P1.1.5, P1.1.4 |
| F-21 | Cross-DLL allocator/ownership hazards for plugins and hot reload | ADR-0012 rules, P1.2.5, P7.9.7 |
| F-22 | Wayland limits (no global window positioning) not reflected in docking/tear-off | P2.2.4, P7.1.1 |
| F-23 | Tempo-map/non-linear time, parameter-gesture undo, execution-flow visualization missing for DAW/node tools | P7.3.7, P7.5.6, P7.4.5 |
| F-24 | CI, build time and licensing hygiene (SBOM, FreeType license choice, fonts) not enforced | P0.1.8, P0.1.9, ADR-0015/0016, DoD #8, P4.12 |
| F-25 | No external validation before declaring 1.0 | P13.9, §10 criteria 9 |

*End of original architecture and implementation plan. Update status markers as work proceeds; amend phases only via an ADR or RFC.*

---

## Revision 10 notes — Phase 0 tooling

P0.1.2 is complete. `CMakePresets.json` includes the requested standard, profiling, and sanitizer configurations; sanitizer flags are selected through the compiler-aware `TGF_SANITIZER` setting. `docs/BUILDING.md` documents availability and caveats. `tools/check_presets.py` is registered with CTest to prevent disconnected or missing build/test presets.

## Revision 11 notes — compiler policy and quality tooling

P0.1.3 is partially complete. The current Tier-1 matrix is documented in `docs/COMPILER_SUPPORT.md` and `cmake/compiler-support.json`: MSVC 14.51/14.50, Clang 23/22, and GCC 16/15. `TGF_WARNINGS_AS_ERRORS` remains ON by default, with the MSVC `/W4` + `/WX` policy and the GCC/Clang warning set + `-Werror` checked by `tools/check_compiler_policy.py`. Ninja presets export `compile_commands.json`. Added `.clang-tidy`, optional CMake integration for clang-tidy and IWYU, plus `tools/check_format.py` and conditional `format-check`/`format-fix` targets. The compiler-policy check is registered in CTest. GCC 14.2 Release, Debug, and shared Release, plus Clang 17 Release, each pass 5/5 tests with warnings-as-errors. Actual current Tier-1 compiler runs and actual formatter/tidy/IWYU runs remain pending; the environment had none of those latest tool versions installed. P0.1.3 remains partial until the matrix and tools are executed in CI or on native toolchains.

## Appendix B — Core audit remediation backlog (updated 2026-10-14, Revision 10)

These follow-up tasks come from the code-level review of the supplied project snapshot. They are separate from the original 272-task baseline. Each completed item has targeted regression coverage and a documented contract; passing the original showcase alone was not sufficient evidence.

- [x] **AUD-CORE-001 — Allocation input validation:** `aligned_alloc_bytes()` rejects zero/non-power-of-two alignment and zero sizes, normalizes valid small alignments, and checks size-rounding overflow before allocation. Invalid/overflow cases have regression tests.
- [x] **AUD-CORE-002 — LinearArena release safety:** unsupported alignment, zero-size requests, uninitialized arenas, capacity exhaustion, and alignment-rounding overflow fail deterministically in Debug and Release; failures are counted.
- [x] **AUD-CORE-003 — Pool lifetime safety:** pool nodes track live objects; `destroy()` rejects foreign pointers and immediate double destruction; `release()`/re-init destroys all live objects. A raw pointer must be discarded after destruction because address reuse cannot distinguish a stale pointer from a new object.
- [x] **AUD-CORE-004 — Exception contract correctness:** `Pool<T>::create()` is conditionally `noexcept` and preserves the free list if construction throws; pool destruction requires a nothrow destructor. `SlotMap<T>` explicitly requires nothrow move construction, move assignment, and destruction before using its `noexcept` relocation/erase operations.
- [x] **AUD-CORE-005 — SampleTime zero-rate behavior:** `to_seconds()` now returns `Result<f64>` and reports `Error::InvalidArgument` for a zero sample rate; success and error paths are tested.
- [p] **AUD-CORE-006 — Realtime atomic guarantees:** SPSC/triple-buffer templates require always-lock-free atomic types at compile time and expose runtime checks. Tests cover lock-free status, bounded queue full/empty behavior, `noexcept` data-path calls, and zero allocations. Documentation explicitly does not equate C++ lock-free atomics with a portable formal wait-free/hard-realtime guarantee.
- [x] **AUD-CORE-007 — Allocation diagnostics accuracy:** `ScopedAllocationCheck` observes the calling thread; tracked external allocator adapters provide paired live/budget/leak accounting; `ScopedMemoryLeakReport` reports per-tag deltas at an explicit application/plugin shutdown boundary; and a warmed 1,000-iteration steady-state test verifies zero allocations while separately observing deliberate boundary growth. Hosts must route allocations through TGF or its adapter for them to be tracked.
- [x] **AUD-CORE-008 — Bindings dependency enforcement:** restrict `bindings` to `c` module headers in `tools/check_deps.py`; add a regression test proving C ABI includes pass and direct core includes fail.

- [x] **AUD-CORE-009 — Shared-library export for memory-tag scope:** exported `ScopedMemoryTag`'s out-of-line constructor/destructor and verified the public memory API in the shared-library showcase.
- [x] **AUD-CORE-010 — External allocator tracking:** added `ExternalAllocator` and `tracked_external_alloc_bytes()` so host allocator blocks receive TGF tags, budgets, live counters, leak deltas, aligned payloads, and paired deallocation.
- [x] **AUD-CORE-011 — Lifecycle leak reports:** added `ScopedMemoryLeakReport`; callbacks receive only positive per-tag live deltas at controlled application/plugin shutdown, without unsafe global `atexit` registration.
- [x] **AUD-CORE-012 — Warm-up/steady-state boundary:** added a regression test proving a warmed 1,000-iteration steady-state workload allocates zero times and deliberate boundary growth is detected.
- [x] **AUD-CORE-013 — Module allocator unload safety:** versioned registrations use generational handles; outstanding allocations pin callback ownership, premature unregister returns `Error::Busy`, and stale handles are rejected after unregister. A four-thread test completed 1,024 alloc/free operations with exact callback pairing; the 64-slot limit and 65th-registration rejection are verified.
- [p] **AUD-CORE-014 — Mapped-file portability:** move-only UTF-8 `MappedFile` supports read-only/read-write whole-file maps, flush, and zero-length files. Linux POSIX behavior is tested; Windows/macOS native builds remain unverified.
- [x] **AUD-CORE-015 — Module allocator concurrency and registry capacity:** descriptor publication and lifetime transitions are mutex-protected; four threads completed 1,024 allocation/free pairs under ThreadSanitizer, with exact allocator/deallocator pairing and no outstanding blocks. The fixed 64-slot registry accepts 64 active registrations and rejects the 65th with `CapacityExceeded`.

**Remediation result (Revision 10):** AUD-CORE-001 through AUD-CORE-005, AUD-CORE-007 through AUD-CORE-013, and AUD-CORE-015 are closed with regression coverage. AUD-CORE-006 and AUD-CORE-014 remain partial because formal hard-realtime/wait-free guarantees and native mapped-file verification are not yet established. P1.2.2 and P1.2.3 are complete for allocations routed through TGF or the tracked external allocator adapter; uninstrumented host allocations remain outside TGF's visibility by design. P1.2.5 is partial pending native platform and dynamic-plugin lifecycle verification. The dependency checker change still does not complete P0.1.6 as a whole: CI integration and the remaining Phase 0 requirements are outstanding.

**API notes:** `to_seconds()` is now a `Result<f64>`; callers must check `.ok()` before `.value()`. `Pool::destroy()` returns `bool`; `Pool<T>` requires a nothrow destructor. `SlotMap<T>` requires nothrow move construction/assignment and destruction. SPSC/triple-buffer use is restricted to targets with always-lock-free underlying atomics.


## Revision 12 notes — P0.1.4 continuous integration foundation

P0.1.4 is **partially implemented**, not complete. Added `.github/workflows/ci.yml` for Debug
and Release build/CTest jobs on Ubuntu 26.04 (GCC 15 and LLVM Clang 22), Windows Server 2025
(Visual Studio 2022/MSVC), and macOS 15 (AppleClang). The workflow enables the sccache GitHub
Actions cache, retains CTest logs as artifacts, and keeps optional LTO disabled in the common
matrix so a missing linker plugin does not masquerade as a compiler failure. Added a separate
nightly benchmark workflow guarded by `TGF_BENCHMARK_RUNNER_READY=true` and a required
self-hosted `tgf-benchmark-pinned` runner label. Its host preflight requires the Linux
`performance` governor and equal minimum/maximum CPU frequency for every exposed policy.

**Local evidence (Revision 12):** GCC 14.2 Release and Debug and Clang 17 Release (LTO disabled)
each build with warnings-as-errors and pass 7/7 CTest tests. These local results do not execute
GitHub-hosted Windows/macOS/Linux jobs or produce a nightly benchmark artifact.

## Revision 13 notes — hosted CI execution preparation

P0.1.4 remains **partially complete**. The extracted source has no `.git` directory or Git
remote, so the hosted workflow could not be launched directly from the archive. GitHub Actions
workflow files were hardened: Windows enters the MSVC 2022 developer environment and builds
through Ninja with `cl.exe`, making CMake's compiler-launcher feature effective for `sccache`.
Dedicated Windows MSVC/Ninja Debug and Release configure/build/test presets were added while
retaining the Visual Studio IDE presets. Workflow actions were refreshed to checkout v7 and
upload-artifact v7.

**Local evidence (Revision 13):** workflow YAML parsing and `tools/check_ci_workflows.py` pass;
`tools/check_presets.py` passes the expanded Windows MSVC/Ninja preset graph; GCC 14.2 Release,
GCC 14.2 Debug, and Clang 17 Release each pass **7/7 CTest tests**. This does not validate native
Windows/macOS or hosted workflow execution.

## Revision 14 notes — GitHub account and repository discovery

The GitHub integration is now connected. The authenticated account is `tasimas-com`. Its owned
repositories are `tasimas-com/tasimas-com`, `tasimas-com/tbhs`, and `tasimas-com/tjsonp`. A direct
lookup for `tasimas-com/TGF` returned HTTP 404. The public `tasimas-com/tasimas-com` README lists
TGF as “Coming soon”; it is a separate TASIMAS website/profile repository, not the TGF source
repository, so it must not be overwritten with framework files.

The repository-discovery subtask P0.1.4.e.5 is complete with this evidence. Actual hosted execution
(P0.1.4.e.4) remains blocked until a dedicated `tgf` GitHub repository exists. The eight hosted
matrix jobs, artifact upload, and nightly benchmark runner have therefore **not** been run.

## Revision 15 notes — dedicated repository setup

The user selected the repository name `tasimas-com/tgf`. The authenticated GitHub account was
confirmed as `tasimas-com`; the owned repositories were inspected and `tasimas-com/tgf` was not
present. The available connected GitHub operations include repository reads and existing-repository
Git-data/content writes, but do not expose the GitHub `Create a repository` operation. No unrelated
repository was modified and no repository was falsely reported as created.

Added `docs/GITHUB_REPOSITORY_SETUP.md` with the exact creation settings and initial-push runbook.
Updated `.gitignore`, added `.gitattributes`, removed an accidental Python bytecode cache from the
source archive, and preserved `TGF/TODO.md` as the canonical checklist at the project root.

**Current blocker:** the repository owner must create `https://github.com/tasimas-com/tgf` through
GitHub's New repository page (owner `tasimas-com`, name `tgf`, no README/license/gitignore
initialization). After that, the source can be published and hosted Actions can run. P0.1.4.e.6
remains partial and P0.1.4.e.7 remains not started; do not mark hosted CI complete until an actual
run URL, all eight job results, CTest artifacts, and recorded compiler versions are reviewed.
The dedicated benchmark runner and its repository variable remain disabled.

## Revision 16 notes — dedicated repository created; initial publication in progress

The user created `https://github.com/tasimas-com/tgf` and connected the GitHub account. The
connected identity `tasimas-com` has admin/push permission. GitHub repository metadata confirms:
repository ID `1420440551`, default branch `main`, public visibility, and an empty repository
(size 0) before this initial publication. The website/profile repository was not modified.

The current Revision 15 source archive is being prepared for publication with its project contents
at the repository root, including the authoritative root `TODO.md`. P0.1.4.e.6 is complete.
P0.1.4.e.7 remains partial until the initial commit is visible and all eight hosted CI jobs finish;
job logs and CTest artifacts must be inspected before any hosted-platform checkbox is closed.
The dedicated pinned-frequency nightly benchmark runner remains separately unconfigured.


## Revision 17 notes — first successful hosted cross-platform CI baseline

The dedicated public repository is live at https://github.com/tasimas-com/tgf (repository ID
1420440551, default branch `main`). The full project is published at the repository root and
the authoritative checklist is `TODO.md`.

**Hosted evidence:** TGF CI run [#13](https://github.com/tasimas-com/tgf/actions/runs/38730051352)
on 2026-10-15, commit `c73987167e7bf761ba6fe9ca558cf85b9b0b5780`, completed successfully.
All eight matrix jobs passed: GCC 15.2.0 Debug/Release, LLVM Clang 22.1.2 Debug/Release,
MSVC 19.51.36260.0 (toolset 14.51.36231) Debug/Release, and AppleClang 17.0.0 Debug/Release.
The Windows runner log path identifies a Visual Studio 18 Enterprise installation; the compiler
is therefore recorded by its actual version/toolset, not mislabeled as Visual Studio 2022.

Each job passed all seven CTest tests (56/56 individual test executions overall). All eight
CTest artifacts were downloaded, ZIP integrity checked, and their `LastTest.log` files inspected;
each reported 100% tests passed. Artifact IDs: 11968903986, 11968869037, 11969543684,
11969513753, 11968944064, 11969448906, 11969353813, and 11969328839.

**Caching correction:** the hosted workflow uses `actions/cache@v4` to preserve CMake build
directories for incremental builds. It does not currently use sccache as a compiler launcher;
the CI documentation and P0.1.4.b wording have been corrected to describe the actual behavior.

**Still open:** P0.1.4.f (dedicated pinned-frequency benchmark runner) and P0.1.4.g (the full
two-generation compiler matrix). The run verifies GCC 15, Clang 22, MSVC toolset 14.51, and
AppleClang 17; it does not establish GCC 16, Clang 23, MSVC 14.50, or a dedicated benchmark pass.
P0.1.3.g also remains partial. Phase 0 is not complete, and Phase 1 remains gated by the
documented Phase 0 exit criteria.


## Revision 18 notes — hosted CI verification repeated after corrections

The corrected workflow and its regression checker were committed as
`8a2cfff31e4502ba142e444a01c0308a489dfac0`. GitHub Actions run
[#14](https://github.com/tasimas-com/tgf/actions/runs/38738723466) completed successfully.
All eight jobs passed again: GCC 15.2.0 Debug/Release; LLVM Clang 22.1.2 Debug/Release;
MSVC 19.51.36260.0/toolset 14.51.36231 Debug/Release; AppleClang 17.0.0 Debug/Release.
Every job passed 7/7 CTest tests (56 successful test executions). All eight new artifact ZIPs
were downloaded, passed ZIP integrity checks, and each contained a `LastTest.log` with seven
`Test Passed.` entries. Artifact IDs: 11975135189, 11975130127, 11974769084, 11974489507,
11973969685, 11973939741, 11973764489, and 11973644936.

The hosted baseline does not complete the full compiler generations in P0.1.3.g/P0.1.4.g:
GCC 16, Clang 23, and MSVC 14.50 remain unverified. AppleClang 17 verifies the native macOS
compatibility lane. The dedicated pinned-frequency benchmark runner in P0.1.4.f remains
unprovisioned and the nightly workflow remains safely gated. Phase 0 is not complete; Phase 1
remains gated by the documented Phase 0 exit criteria.


## Revision 19 notes — dedicated benchmark runner preparation

Added `docs/BENCHMARK_RUNNER_SETUP.md`, a complete operator runbook for the dedicated Linux
x86-64 benchmark host: hardware/thermal inventory, CPU governor and fixed min/max policy, real-host
preflight, repository-scoped runner registration, security isolation, Actions-variable gate, and
manual/nightly artifact review. `docs/CI.md` now links to the runbook.

The five unit-test scenarios in `tools/test_check_benchmark_host.py` pass. The real preflight was
executed in the current environment and correctly failed closed with `No CPU frequency policy found
under /sys/devices/system/cpu`; this environment cannot serve as the pinned-frequency runner.
No self-hosted runner or Actions repository variable has been enabled, and no benchmark success is
claimed. P0.1.4.f.1 and .f.2 are done; .f.3 and .f.4 remain partial. Keep the nightly workflow safely
gated until a dedicated physical host passes the preflight. Phase 0 remains incomplete.

*End of TGF master TODO (Revision 19 — benchmark runner runbook and preflight verification complete; physical runner provisioning remains open, 2026-10-15).*


## Revision 20 — benchmark-host acceptance tooling

The dedicated runner path now has a read-only JSON inventory collector, registered inventory tests, and a stricter nightly preflight that requires x86-64 plus positive systemd evidence that no VM is detected. The CI contract checks that the workflow captures benchmark-artifacts/host-inventory.json. The circular runner-guide stub was replaced by an operator runbook covering bare-metal acceptance, CPU-frequency pinning, thermal validation, inventory review, runner isolation/registration, and the repository readiness gate.

This revision does **not** claim that a qualifying physical host has been provisioned. The available execution container exposes a hypervisor flag and no CPU-frequency policy or thermal sysfs sensors, so the real-host check correctly rejects it. P0.1.4.f.3 remains partial until a dedicated bare-metal Linux x86-64 host is supplied, configured, measured, and its inventory is reviewed; P0.1.4.f.4 remains blocked on that host.

## Revision 21 — owner-approved benchmark-host scope waiver (2026-10-17)

The project owner explicitly approved waiving the physical-host provisioning and runner-registration requirements for P0.1.4.f.3 and P0.1.4.f.4. These items are closed for the current project scope by an administrative scope decision, not by physical execution. No dedicated bare-metal Linux x86-64 host has been provisioned, no CPU-frequency pinning or sustained thermal validation has been performed on such a host, no self-hosted runner is registered, and no dedicated-host benchmark result is claimed. The repository-side inventory collector, fail-closed preflight, automated tests, CI contract, artifact capture, and operator runbook remain in place. `TGF_BENCHMARK_RUNNER_READY` must remain unset and the nightly benchmark workflow must remain gated. Reversing this waiver requires completing the documented host acceptance and runner-registration procedure before enabling the workflow. This waiver closes only P0.1.4.f; it does not declare the entirety of Phase 0 complete or authorize starting Phase 1.


## Revision 22 — normative coding standard (2026-10-17)

P0.1.5 is delivered by `docs/CODING_STANDARD.md`. The standard consolidates the existing project contract, naming and formatting rules, module boundaries, ownership/lifetime and allocator rules, error handling, thread/real-time constraints, public API documentation requirements, and explicit compatibility levels. It distinguishes the pre-1.0 experimental C++ surface from the intended supported 1.x source API and the future stable C ABI; it does not claim that the C ABI has already been implemented. A focused policy regression script is registered as `coding_standard_policy` in CTest, and the standard is linked from the repository README and CI documentation. This task adds policy documentation and a documentation-contract check; it does not implement P12.7 versioning automation or P11.1 C ABI compatibility tooling.
