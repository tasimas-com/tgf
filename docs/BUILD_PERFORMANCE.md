# Build-time and public-header performance tracking

This document defines P0.1.9's reproducible build-time guard and public-header cost report.
It is deliberately separate from TGF's runtime benchmark suite: it measures compiler/build
work, not frame time, input latency, or GPU performance.

## Hosted measurement environment

The required lane uses GitHub-hosted Ubuntu 26.04, Ninja, Clang 23, Release mode, LTO disabled,
and exactly two parallel build jobs. The workflow does not restore a build cache: the clean
measurement must start with generated build outputs removed.

The checked-in initial ceilings are:

| Measurement | Hard budget |
|---|---:|
| Clean build budget | **180 seconds** |
| Incremental rebuild budget | **45 seconds** |

These are intentionally conservative initial ceilings, not claims that the current build takes
that long or that this is a cross-machine benchmark. Actual observed times are written to each
workflow artifact. The limits apply only to the documented runner/compiler/configuration. Do
not compare their absolute values against Windows, macOS, a developer workstation, another
compiler generation, or a cached build.

## What is measured

1. CMake configuration and tool installation happen before timing and are excluded.
2. The clean timer starts after CMake's clean target and covers the complete default build
   (TGF core, showcase, and isolated public-header check target).
3. The incremental timer touches core/src/profiler.cpp, then rebuilds the default target.
   The tool verifies that the probe source appears in the compiler output and restores its
   original filesystem timestamp even if the build fails. It changes no source contents.
4. The workflow fails when either measurement exceeds its checked-in ceiling. The JSON and
   Markdown reports, command logs, and header-cost reports are uploaded even on a failed run
   whenever the files were produced.

The two-job limit controls parallelism, while the absence of a restored build cache makes the
clean measurement genuinely clean. The incremental case intentionally represents one changed
implementation translation unit plus its dependent relink, not a no-op build.

## Public-header hygiene and cost

tests/CMakeLists.txt discovers first-party headers under each top-level module's
include/tgf/ directory. Every header is compiled in its own generated translation unit,
included twice to check its include guard, and compiled with exceptions and RTTI enabled.
This remains part of the required CTest build on the full compiler matrix.

For the cost report, the dedicated Clang 23 lane adds -ftime-trace only to the
tgf_header_check target. Each generated translation unit contains one public header, so
its Total ExecuteCompiler trace duration provides an isolated per-header compile-cost proxy.
The report also records the matching Source event duration for the header itself when Clang
emits that event. Results are sorted from most expensive to least expensive and published as
both JSON and Markdown.

The isolated translation-unit value includes fixed compiler/front-end overhead and any
transitive includes. It is useful for comparing headers within the same run; it is not a pure
measurement of just the header's own tokens, and the per-header values must not be summed to
predict total build time. Compare reports only when compiler version, configuration, runner
class, and measurement method match.

## Local use

Normal builds do not enable time tracing. To produce the same header cost data locally with
Clang 23:

~~~sh
CC=clang-23 CXX=clang++-23 cmake -S . -B build/performance -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DTGF_ENABLE_LTO=OFF \
  -DTGF_WARNINGS_AS_ERRORS=ON \
  -DTGF_ENABLE_HEADER_TIME_TRACE=ON

python3 tools/measure_build.py \
  --build-dir build/performance \
  --budget-file cmake/build-performance-budgets.json \
  --report-dir build/performance-reports

python3 tools/report_header_costs.py \
  --build-dir build/performance \
  --manifest build/performance/tests/header-check-manifest.tsv \
  --output-dir build/performance-reports
~~~

The report directory contains build-performance.json, build-performance.md,
header-costs.json, header-costs.md, and the clean/incremental build logs.

The measurement contract is encoded in cmake/build-performance-budgets.json and guarded by
CTest. The master plan associates the build-time policy with ADR-0015; the standalone ADR
record is still part of P0.5's ADR-writing work. Material changes to the measurement method or
budgets should therefore be documented with the ADR-0015 decision when that record is written.
