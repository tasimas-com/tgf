# TGF GitHub repository — initial publication and CI verification

**Repository:** <https://github.com/tasimas-com/tgf>  
**Owner:** `tasimas-com`  
**Repository name:** `tgf`  
**Default branch:** `main`

## Repository state

The user created this dedicated repository on 2026-10-15 and connected the GitHub account.
The connected account `tasimas-com` has administrator and push permission. The repository is
public, has default branch `main`, and was empty (size 0) when inspected before initial publication.
The separate `tasimas-com/tasimas-com` website/profile repository is not used for TGF source.

## Initial publication contract

Publish the *contents* of this project directory at the repository root. In particular, `TODO.md`
must be at `https://github.com/tasimas-com/tgf/blob/main/TODO.md`; it is the authoritative
master checklist. Include `.github/workflows/ci.yml`, `.github/workflows/nightly-benchmarks.yml`,
all CMake files, source, tests, tools, samples, docs, ADRs, and audit evidence. Do not add local
build directories, CMake caches, Python bytecode, or IDE state.

The repository must not receive a synthetic README, license, or gitignore that conflicts with the
project copy. Keep `.gitignore` and `.gitattributes` from this project snapshot.

## Verify the first hosted CI run

A push to `main` triggers `.github/workflows/ci.yml`. Review all eight jobs:

- Ubuntu 26.04 / GCC 15 / Debug and Release
- Ubuntu 26.04 / Clang 22 / Debug and Release
- Windows Server 2025 / MSVC 2022 via Ninja / Debug and Release
- macOS 15 / AppleClang / Debug and Release

For every job, record the exact compiler version and conclusion, and inspect its uploaded CTest log
artifact. Update P0.1.4.e.7 in the root `TODO.md` only after all eight jobs finish successfully
and the logs/artifacts have been inspected. A green local CTest run is not a substitute for hosted
Windows/macOS results.

## Nightly benchmark runner is a separate setup

Do not set repository variable `TGF_BENCHMARK_RUNNER_READY=true` yet. First provision the dedicated
pinned-frequency Linux runner with labels `self-hosted`, `linux`, `x64`, and
`tgf-benchmark-pinned`; run `python3 tools/check_benchmark_host.py`; inspect its CPU-frequency
policies; and only then enable the repository variable. A skipped nightly workflow is not a
benchmark pass.
