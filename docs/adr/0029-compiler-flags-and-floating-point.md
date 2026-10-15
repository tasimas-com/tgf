# ADR-0029: Compiler policy, optimisation flags and floating-point determinism

Status: Accepted

## Decision
* Library implementation: `-fno-exceptions -fno-rtti` (`/EHs-c- /GR-`, `_HAS_EXCEPTIONS=0`).
  Public headers contain no `throw`, `dynamic_cast` or `typeid`, so user code compiled *with*
  exceptions/RTTI works (ADR-0001). Verified two ways: `build_info()` reports the library
  flags, and the showcase (an ordinary user TU with exceptions on) throws/catches and runs
  every check; every public header is also compiled standalone with exceptions/RTTI on.
* Warnings: `/W4 /permissive-` and `-Wall -Wextra -Wpedantic -Wshadow -Wconversion
  -Wsign-conversion -Wold-style-cast ...`, all as errors by default.
* Release: `-O2` as the starting point (not yet compared against `-O3`; the P0.3 benchmark
  suite decides), `-ffunction-sections -fdata-sections` + linker GC, LTO when
  the toolchain supports it, `/GL /LTCG /Gy /Gw /OPT:REF /OPT:ICF` on MSVC.
* **No `-ffast-math` / `/fp:fast`, and `-ffp-contract=off` / `/fp:precise`.** Layout must be
  bit-identical across compilers and platforms (P5.3.7) so golden tests and any networked or
  collaborative UI are reproducible. FMA contraction is a classic source of cross-compiler
  divergence. SIMD kernels may opt in locally where a benchmark proves a win and the result
  is not layout-affecting.
* `-march=native` is an opt-in developer option only (`TGF_NATIVE_ARCH`); distributed
  binaries target the baseline ISA with runtime dispatch (P1.4.2).
* Profiler zones compile out in Release unless `TGF_PROFILE=ON`; the current implementation
  uses `steady_clock` (~70 ns per zone). A calibrated TSC/QPC clock is planned (P1.6.2).
