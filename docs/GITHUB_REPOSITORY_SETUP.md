# TGF GitHub repository — publication and hosted CI verification

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

## First hosted CI baseline — verified

GitHub Actions run [#13](https://github.com/tasimas-com/tgf/actions/runs/38730051352) completed
successfully on 2026-10-15:

- 8/8 matrix jobs passed (four toolchain environments × Debug/Release).
- GCC 15.2.0, Clang 22.1.2, MSVC 19.51.36260.0/toolset 14.51.36231, AppleClang 17.0.0.
- Every job passed 7/7 CTest tests (56 successful individual test executions).
- All eight uploaded CTest artifact ZIPs were downloaded and checked; each contains a valid
  `LastTest.log` reporting 100% tests passed.

The full run and artifact evidence is in
[`docs/audit/2026-10-15/TGF_HOSTED_CI_RESULTS.md`](audit/2026-10-15/TGF_HOSTED_CI_RESULTS.md).

## Still required

The dedicated pinned-frequency benchmark workflow remains gated. Do not set
`TGF_BENCHMARK_RUNNER_READY=true` until a dedicated Linux x86-64 runner with labels
`self-hosted`, `linux`, `x64`, `tgf-benchmark-pinned` is provisioned and
`python3 tools/check_benchmark_host.py` passes.

The hosted matrix is only a first compiler baseline. Complete the second supported generations
(GCC 16, Clang 23, and MSVC 14.50) before marking the full Tier-1 compiler matrix complete.
