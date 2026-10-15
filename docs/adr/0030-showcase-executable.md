# ADR-0030: One showcase executable that grows with every phase

Status: Accepted

## Decision
`samples/showcase` builds `tgf_showcase`, the single executable that demonstrates and
verifies *everything implemented so far*. It is a gate: exit code 0 only if every check
passes; CTest runs it (`--checks-only`) in every configuration.

* **Now (Phase 1 slice):** console harness — checks with human-readable evidence, micro
  benchmarks, `--json` result export, a global `operator new` hook that makes
  "0 allocations in steady state" (DoD #4) an observed fact. Console is the honest UI for a
  library that has no window yet.
* **M1 (Phase 2 + minimal Phase 3):** same executable opens a window (GLFW/SDL bring-up
  backend first per P2.2.5, native backend after), clears/draws a triangle, shows idle CPU
  and frame-time overlay. Checks keep running headless against the mock platform.
* **M2:** rounded-rect batching stress (10k widgets), text rendering page.
* **M3:** widget gallery (light/dark/high-contrast, LTR/RTL), inspector overlay.
* **M4+:** the five reference demos (timeline, node editor + viewport, DAW, image canvas,
  engine editor) become tabs of the same executable.

Rule: a phase is not "done" until its section of the showcase is green on every tier-1
platform. New modules add `checks_<module>.cpp` / `bench_<module>.cpp` and register them in
`main.cpp`; nothing else changes.
