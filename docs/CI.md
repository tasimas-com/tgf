# Continuous integration and benchmark infrastructure

**Introduced: Revision 12; CI hardening: Revision 13 (2026-10-15)**

TGF uses two GitHub Actions workflows:

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) builds and runs CTest on pushes,
  pull requests, and manual dispatches.
- [`.github/workflows/nightly-benchmarks.yml`](../.github/workflows/nightly-benchmarks.yml)
  runs the core showcase benchmarks on a dedicated Linux host whose CPU frequency controls
  pass an explicit preflight check.

## Build and test matrix

The hosted CI workflow requests these runner/toolchain combinations in both Debug and Release:

| Runner | Compiler | CMake generator | Purpose |
|---|---|---|---|
| `ubuntu-26.04` | GCC 15 (`gcc-15`, `g++-15`) | Ninja | GNU Linux toolchain |
| `ubuntu-26.04` | LLVM Clang 22 (`clang-22`, `clang++-22`) | Ninja | LLVM Linux toolchain |
| `windows-2025` | Visual Studio 2022 / MSVC | Ninja + `cl.exe` | Native Windows toolchain |
| `macos-15` | AppleClang from Xcode | Ninja | Native macOS toolchain |

On Windows, CI invokes `ilammy/msvc-dev-cmd` to establish the Visual Studio 2022 compiler
environment, then uses the Ninja generator with `cl.exe`. This is deliberate: CMake's
`CXX_COMPILER_LAUNCHER` property is implemented for Makefile and Ninja generators, not the
Visual Studio project generator. Using Ninja therefore makes the `sccache` launcher genuinely
active for the MSVC build. The regular `vs2022` multi-config presets remain available for local
Visual Studio IDE workflows.

The workflow records the actual compiler version from every job. The Ubuntu 26.04 runner image
documents GCC 15 and LLVM Clang 22; Windows 2025 provides Visual Studio 2022; macOS 15 provides
AppleClang and Ninja. These are runner-image capabilities, not proof of successful TGF Actions
runs. The exact compiler/toolset version printed by each remote run must be reviewed before
claiming support.

Every matrix entry builds and tests Debug and Release with warnings-as-errors enabled and
`sccache` as the C++ compiler launcher. The compiler cache uses GitHub Actions cache storage.
CTest logs are uploaded for 14 days, including after failures. The workflows currently use
`actions/checkout@v7`, `actions/upload-artifact@v7`, and `mozilla-actions/sccache-action@v0.0.11`.
The Windows developer environment is prepared with `ilammy/msvc-dev-cmd@v1.13.0`.

The hosted matrix is a first cross-platform baseline, not the full Tier-1 compiler-generation
matrix in [`COMPILER_SUPPORT.md`](COMPILER_SUPPORT.md). It does not yet prove GCC 16, Clang 23,
the previous GCC/Clang generations, or both supported MSVC toolsets. The exact versions printed
by remote jobs must be attached to the compiler support record before P0.1.3/P0.1.4 can close.

## Dedicated nightly benchmark runner

Ordinary shared hosted runners are not suitable for performance release gates. The nightly
workflow therefore targets only a self-hosted runner with all of these labels:

```text
self-hosted, linux, x64, tgf-benchmark-pinned
```

Before enabling it:

1. Provision a dedicated Linux x86-64 machine. Do not share it with interactive workloads or
   unrelated CI jobs while benchmarks run.
2. Configure every CPU frequency policy with the `performance` governor and set
   `scaling_min_freq` equal to `scaling_max_freq` for every policy. Keep the chosen frequency
   stable across reboots and record CPU model, microcode, kernel, BIOS/firmware, memory, and
   cooling configuration.
3. Install Git, CMake 3.25+, Ninja, Python 3, a supported C++ compiler, and the GitHub Actions
   runner. Register the four labels shown above. Keep the self-hosted runner updated to a
   release that supports the Node.js 24 runtime used by current artifact actions (2.327.1 or
   newer).
4. Verify the machine locally:

   ```sh
   python3 tools/check_benchmark_host.py
   ```

   The check fails closed if a frequency policy is missing, the governor is not `performance`,
   or minimum and maximum frequencies differ.
5. After the runner is online and preflight succeeds, set the repository Actions variable
   `TGF_BENCHMARK_RUNNER_READY` to the exact string `true`.

The workflow runs nightly at 03:37 UTC and can also be started manually. It builds the Release
showcase, runs its nine-sample-median core benchmark suite, and uploads `host.txt` plus
`benchmark-results.json` for 30 days. A skipped workflow means the repository variable is not
enabled; it does not mean a benchmark passed. A failed host preflight must be fixed before
performance results are considered usable.

## First GitHub run runbook

The dedicated repository is `tasimas-com/tgf`. Its creation must be completed through
<https://github.com/new> because the currently connected GitHub integration does not expose a
repository-creation operation. The exact owner/name/settings and initial push commands are in
[`GITHUB_REPOSITORY_SETUP.md`](GITHUB_REPOSITORY_SETUP.md).

After the empty repository exists, push the contents of the extracted `TGF/` directory to `main`.
The push triggers `TGF CI`. Review all eight platform/compiler/configuration jobs, inspect each
uploaded CTest log, and record exact compiler versions and the run URL. Do not set
`TGF_BENCHMARK_RUNNER_READY=true` until the dedicated pinned-frequency runner has been provisioned
and passed its own preflight.

## Local workflow checks

These repository checks are part of CTest whenever Python 3 is found:

- `ci_workflow_contract` checks the cross-platform matrix, current action versions, cache,
  Windows MSVC/Ninja compiler-launcher path, artifacts, and nightly runner guard. If PyYAML is
  installed it also parses both workflow files.
- `benchmark_host_policy` exercises the pinned-frequency check with controlled test fixtures.

The local project cannot emulate GitHub-hosted Windows/macOS machines or an administrator-
configured fixed-frequency benchmark host. Those require actual remote runners.

## Official references

- [GitHub-hosted runner labels and hardware](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [CMake compiler launcher generator support](https://cmake.org/cmake/help/latest/prop_tgt/LANG_COMPILER_LAUNCHER.html)
- [MSVC Developer Command Prompt action](https://github.com/ilammy/msvc-dev-cmd)
- [Checkout action](https://github.com/actions/checkout)
- [Upload artifact action](https://github.com/actions/upload-artifact)
- [sccache GitHub Actions integration](https://github.com/mozilla-actions/sccache-action)
- [GitHub Actions self-hosted runners](https://docs.github.com/en/actions/concepts/runners/self-hosted-runners)
