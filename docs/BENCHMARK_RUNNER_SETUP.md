# TGF dedicated benchmark runner setup

See the [operator runbook](https://github.com/tasimas-com/tgf/blob/main/docs/BENCHMARK_RUNNER_SETUP.md)
for hardware requirements, CPU-frequency configuration, fail-closed preflight, runner registration,
security isolation, repository Actions-variable gating, and benchmark artifact review.

The workflow must remain gated until a dedicated physical Linux x86-64 host is registered with
labels `self-hosted`, `linux`, `x64`, `tgf-benchmark-pinned` and passes
`python3 tools/check_benchmark_host.py`.
