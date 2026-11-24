# TGF GitHub repository — publication and hosted CI verification

> This runbook retains the initial-publication history. Its first/second-matrix sections are historical; see the current status below before relying on compiler-version claims.

**Repository:** https://github.com/tasimas-com/tgf  
**Owner:** `tasimas-com`  
**Default branch:** `main`  
**Visibility:** Public  
**Repository ID:** `1420440551`

## Publication state

The dedicated repository is created and populated. The complete TGF project is published at the
repository root. The authoritative master checklist is
[`TODO.md`](https://github.com/tasimas-com/tgf/blob/main/TODO.md).

The separate `tasimas-com/tasimas-com` website/profile repository was not modified.

## First hosted CI baseline — historical

GitHub Actions run [#13](https://github.com/tasimas-com/tgf/actions/runs/38730051352) completed
successfully on 2026-10-15:

- 8/8 matrix jobs passed (four toolchain environments × Debug/Release).
- GCC 15.2.0, Clang 22.1.2, MSVC 19.51.36260.0/toolset 14.51.36231, AppleClang 17.0.0.
- Every job passed 7/7 CTest tests (56 successful individual test executions).
- All eight uploaded CTest artifact ZIPs were downloaded and checked; each contains a valid
  `LastTest.log` reporting 100% tests passed.

The full run and artifact evidence is in
[`docs/audit/2026-10-15/TGF_HOSTED_CI_RESULTS.md`](audit/2026-10-15/TGF_HOSTED_CI_RESULTS.md).

## Current status — 2026-11-18

The current `main` commit is `7e9dad1581be59e1df6adf9caa7572a1129d518e`.
[TGF CI run #412](https://github.com/tasimas-com/tgf/actions/runs/44089512975) passed
14/14 configured jobs on 2026-11-17; [Source Quality run #338](https://github.com/tasimas-com/tgf/actions/runs/44089512797),
[Build Performance run #18](https://github.com/tasimas-com/tgf/actions/runs/44089512759), and
[SBOM run #13](https://github.com/tasimas-com/tgf/actions/runs/44089512739) also passed.
The configured matrix covers GCC 15/16, Clang 22/23, MSVC 14.50/14.51, and AppleClang 17.
Microsoft announced MSVC 14.52 as generally available and an LTS release on 2026-11-16.
The current two-generation MSVC matrix must therefore cover 14.52 and 14.51; run #412 is
historical evidence for the preceding 14.50/14.51 pair.

The dedicated pinned-frequency benchmark workflow remains gated. Do not set
`TGF_BENCHMARK_RUNNER_READY=true` until a dedicated Linux x86-64 runner with labels
`self-hosted`, `linux`, `x64`, `tgf-benchmark-pinned` is provisioned and
`python3 tools/check_benchmark_host.py` passes.

The historical matrix already added GCC 16 and Clang 23. Its MSVC pair has now been refreshed
to 14.52 and 14.51. Both Windows jobs use the Visual Studio 2026 LTSC 18.11 channel and verify
the selected compiler/toolset versions before configuring CMake.


## Hosted execution verified twice

- [Run #13](https://github.com/tasimas-com/tgf/actions/runs/38730051352): 8/8 jobs passed.
- [Run #14](https://github.com/tasimas-com/tgf/actions/runs/38738723466): 8/8 jobs passed after workflow-label corrections.
- Compilers: GCC 15.2.0, LLVM Clang 22.1.2, MSVC 19.51.36260.0/toolset 14.51.36231, AppleClang 17.0.0.
- All jobs passed 7/7 CTest tests. All sixteen CTest artifact ZIPs across both runs were downloaded and inspected.

The full run-#14 evidence and artifact IDs are recorded in `docs/CI.md` and the root `TODO.md`.
The pinned-frequency benchmark runner remains owner-waived. The current MSVC latest-two requirement is 14.52/14.51. The full Debug/Release matrix must pass
before the compiler-policy task can be closed.
