# TGF CI remote-execution preparation — Revision 13

**Date:** 2026-10-15  
**Parent task:** P0.1.4.e — execute and review hosted GitHub Actions matrix  
**Status:** Local preparation complete; remote execution blocked on repository connection.

## What was inspected

The Revision 12 source archive contained `.github/workflows/ci.yml` and
`.github/workflows/nightly-benchmarks.yml`, but did not contain `.git` or a Git remote. At the time
of Revision 13, no authenticated GitHub context was available. In Revision 14 the GitHub
integration became connected and repository discovery was performed: the authenticated account
is `tasimas-com`, which owns `tasimas-com/tasimas-com`, `tasimas-com/tbhs`, and `tasimas-com/tjsonp`.
A direct lookup of `tasimas-com/TGF` returned 404. The profile/website repository README describes
TGF as “Coming soon”; it is not the TGF source repository. No remote files were changed.

## Local verification

Fresh CTest runs against the available build directories produced:

| Build directory | Compiler | Tests | Result |
|---|---|---:|---|
| `build/release` | GCC 14.2 | 7/7 | Pass |
| `build/debug` | GCC 14.2 | 7/7 | Pass |
| `build/clang-release` | Clang 17 | 7/7 | Pass |

Additional checks passed:

- `tools/check_ci_workflows.py`: workflow structural contract and PyYAML syntax parsing.
- `tools/check_presets.py`: configure/build/test preset references, including the new Windows
  MSVC/Ninja presets.
- `tools/test_check_benchmark_host.py`: all five benchmark-host policy fixtures.
- `cmake --list-presets`: preset file parses on the available Linux host; Windows-only presets
  are correctly hidden by their host condition.

These are local checks, not GitHub Actions results.

## Workflow correction

CMake documents that `CXX_COMPILER_LAUNCHER` is implemented for Makefile and Ninja generators.
The earlier Windows job used the Visual Studio generator, so its `CMAKE_CXX_COMPILER_LAUNCHER=sccache`
argument did not guarantee that MSVC compilations passed through sccache. Revision 13 changes the
Windows CI path to:

1. Set up the Visual Studio 2022 developer environment with `ilammy/msvc-dev-cmd@v1.13.0`.
2. Configure the Windows-only `msvc-ninja-debug` or `msvc-ninja-release` preset, explicitly
   selecting `cl.exe`.
3. Build/test through Ninja in PowerShell, with sccache configured as the compiler launcher.
   PowerShell avoids the documented Git Bash `link.exe` PATH shadowing issue.

The normal `vs2022` multi-configuration presets remain available for interactive Visual Studio
development.

The workflows were also updated to `actions/checkout@v7` and `actions/upload-artifact@v7`; the
nightly self-hosted runner instructions specify a Node.js 24-capable runner version.

## Remote actions still required

1. Create a dedicated repository named `TGF` under `tasimas-com`, or provide the correct
   existing owner/repository name.
2. Push this Revision 14 project so GitHub sees the workflow files.
3. Run `TGF CI` and verify all eight combinations: GCC 15, Clang 22, MSVC 2022, AppleClang ×
   Debug/Release.
4. Inspect exact compiler versions and every uploaded CTest log; fix any platform-specific errors.
5. Keep the dedicated nightly benchmark workflow disabled until its self-hosted pinned-frequency
   runner has been provisioned and validated.

P0.1.4.e.5 (repository discovery) is complete. P0.1.4.e.4 (hosted execution), P0.1.4.f, and
P0.1.4.g remain partial. P0.1.4 is not complete.
